"""Reglas del chat: con quién puede hablar cada rol, conversaciones, historial, no leídos y guardar mensajes.

Es código síncrono (SQLAlchemy). El WebSocket lo llama dentro de run_in_threadpool para no bloquear el servidor.
"""
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Set

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dto.response.chat import ChatConversationResponse, ChatMessageResponse, ChatUserResponse
from app.exception import ApiException, ForbiddenOperationException, InvalidRequestException, ResourceNotFoundException
from app.model import (
    ChatConversation, ChatConversationType, ChatMessage, ChatParticipant, Course, CourseSubject, Enrollment,
    EnrollmentStatus, Role, Student, Teacher, User,
)

GENERAL_NAME = "Sala general"
MAX_LENGTH = 2000
STAFF = {"ADMIN", "RECTOR", "COORDINATOR"}

ROLE_LABELS = {"ADMIN": "Administrador", "RECTOR": "Rector", "COORDINATOR": "Coordinador",
               "TEACHER": "Docente", "STUDENT": "Estudiante"}


ForbiddenChatException = ForbiddenOperationException  # 403: no puede escribirle o no participa


def ensure_general_room(db: Session) -> ChatConversation:
    room = db.query(ChatConversation).filter(ChatConversation.tipo == ChatConversationType.GENERAL.value).first()
    if room is None:
        room = ChatConversation(tipo=ChatConversationType.GENERAL.value, nombre=GENERAL_NAME)
        db.add(room)
        db.commit()
        db.refresh(room)
    return room


def clean_content(raw: object) -> str:
    """Texto plano, sin espacios sobrantes ni caracteres de control. Angular lo muestra como texto (no HTML)."""
    if not isinstance(raw, str):
        raise InvalidRequestException("The message must be text")
    text = "".join(ch for ch in raw if ch in "\n\t" or ch >= " ").strip()
    if not text:
        raise InvalidRequestException("The message is empty")
    if len(text) > MAX_LENGTH:
        raise InvalidRequestException(f"The message exceeds {MAX_LENGTH} characters")
    return text


class ChatService:

    def __init__(self, db: Session):
        self.db = db

    # ---------- usuarios ----------

    @staticmethod
    def user_dto(user: User, online: Iterable[int] = ()) -> ChatUserResponse:
        role = user.role_ref.nombre if user.role_ref else ""
        return ChatUserResponse(id=user.id, full_name=user.full_name, role=ROLE_LABELS.get(role, role),
                                online=user.id in set(online))

    def find_user(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id, User.estado.is_(True), User.enabled.is_(True)).first()

    def _role(self, user: User) -> str:
        return user.role_ref.nombre if user.role_ref else ""

    # ---------- con quién puede hablar ----------

    def contact_ids(self, user: User) -> Set[int]:
        """Directivos: con todos. Docente: personal + sus estudiantes. Estudiante: sus docentes y directivos
        (no con otros estudiantes en privado)."""
        role = self._role(user)
        active = self.db.query(User.id, Role.nombre).join(Role, Role.id == User.role_id).filter(
            User.estado.is_(True), User.enabled.is_(True), User.id != user.id)
        if role in STAFF:
            return {uid for uid, _ in active.all()}

        staff_ids = {uid for uid, r in active.all() if r in STAFF}
        if role == "TEACHER":
            teacher = self.db.query(Teacher).filter(Teacher.user_id == user.id, Teacher.estado.is_(True)).first()
            teacher_ids = {uid for uid, r in active.all() if r == "TEACHER"}
            if teacher is None:
                return staff_ids | teacher_ids
            course_ids = {cid for (cid,) in self.db.query(CourseSubject.course_id).filter(
                CourseSubject.teacher_id == teacher.id, CourseSubject.estado.is_(True))}
            course_ids |= {cid for (cid,) in self.db.query(Course.id).filter(
                Course.director_teacher_id == teacher.id, Course.estado.is_(True))}
            student_users = {uid for (uid,) in self.db.query(Student.user_id).join(
                Enrollment, Enrollment.student_id == Student.id).filter(
                Enrollment.course_id.in_(course_ids or [-1]), Enrollment.status == EnrollmentStatus.ACTIVE,
                Enrollment.estado.is_(True), Student.estado.is_(True))}
            return staff_ids | teacher_ids | student_users

        if role == "STUDENT":
            student = self.db.query(Student).filter(Student.user_id == user.id, Student.estado.is_(True)).first()
            if student is None:
                return staff_ids
            course_ids = [cid for (cid,) in self.db.query(Enrollment.course_id).filter(
                Enrollment.student_id == student.id, Enrollment.status == EnrollmentStatus.ACTIVE,
                Enrollment.estado.is_(True))]
            teacher_ids = {tid for (tid,) in self.db.query(CourseSubject.teacher_id).filter(
                CourseSubject.course_id.in_(course_ids or [-1]), CourseSubject.estado.is_(True))}
            teacher_ids |= {tid for (tid,) in self.db.query(Course.director_teacher_id).filter(
                Course.id.in_(course_ids or [-1])) if tid}
            teacher_users = {uid for (uid,) in self.db.query(Teacher.user_id).filter(Teacher.id.in_(teacher_ids or [-1]))}
            return staff_ids | teacher_users
        return staff_ids

    def contacts(self, user: User, online: Set[int], q: str = "") -> List[ChatUserResponse]:
        ids = self.contact_ids(user)
        query = self.db.query(User).filter(User.id.in_(ids or [-1]))
        if q.strip():
            query = query.filter(User.full_name.ilike(f"%{q.strip()}%"))
        users = query.all()
        users.sort(key=lambda u: (u.id not in online, u.full_name))
        return [self.user_dto(u, online) for u in users[:200]]

    # ---------- conversaciones ----------

    def _participant(self, conv: ChatConversation, user_id: int, create: bool = False) -> Optional[ChatParticipant]:
        p = next((x for x in conv.participants if x.user_id == user_id), None)
        if p is None and create:
            p = ChatParticipant(conversation_id=conv.id, user_id=user_id, ultimo_leido_id=0)
            self.db.add(p)
            self.db.flush()
            conv.participants.append(p)
        return p

    def get_conversation_for(self, user: User, conversation_id: int) -> ChatConversation:
        """La conversación si el usuario puede verla (la general: todos; la privada: sus dos participantes)."""
        conv = self.db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id, ChatConversation.estado.is_(True)).first()
        if conv is None:
            raise ResourceNotFoundException("Conversation not found")
        if conv.tipo == ChatConversationType.DIRECT.value and self._participant(conv, user.id) is None:
            raise ForbiddenChatException("You are not part of this conversation")
        return conv

    def open_direct(self, user: User, other_id: int, online: Set[int]) -> ChatConversationResponse:
        if other_id == user.id:
            raise InvalidRequestException("You cannot chat with yourself")
        other = self.find_user(other_id)
        if other is None:
            raise ResourceNotFoundException("User not found")
        if other_id not in self.contact_ids(user):
            raise ForbiddenChatException("You cannot start a chat with this user")
        key = f"{min(user.id, other_id)}:{max(user.id, other_id)}"
        conv = self.db.query(ChatConversation).filter(ChatConversation.clave_directa == key).first()
        if conv is None:
            conv = ChatConversation(tipo=ChatConversationType.DIRECT.value, clave_directa=key)
            self.db.add(conv)
            self.db.flush()
            self.db.add_all([ChatParticipant(conversation_id=conv.id, user_id=user.id, ultimo_leido_id=0),
                             ChatParticipant(conversation_id=conv.id, user_id=other_id, ultimo_leido_id=0)])
            self.db.commit()
            self.db.refresh(conv)
        return self.conversation_dto(conv, user, online)

    def conversation_dto(self, conv: ChatConversation, user: User, online: Set[int]) -> ChatConversationResponse:
        me = self._participant(conv, user.id)
        last_read = me.ultimo_leido_id if me else 0
        last = self.db.query(ChatMessage).filter(ChatMessage.conversation_id == conv.id,
                                                 ChatMessage.estado.is_(True)).order_by(ChatMessage.id.desc()).first()
        unread = self.db.query(func.count(ChatMessage.id)).filter(
            ChatMessage.conversation_id == conv.id, ChatMessage.id > last_read, ChatMessage.user_id != user.id,
            ChatMessage.estado.is_(True)).scalar() or 0
        dto = ChatConversationResponse(
            id=conv.id, type=conv.tipo, name=conv.nombre or GENERAL_NAME, unread=unread, last_read_id=last_read,
            last_message=self.message_dto(last, online) if last else None,
        )
        if conv.tipo == ChatConversationType.DIRECT.value:
            other_p = next((p for p in conv.participants if p.user_id != user.id), None)
            if other_p is not None:
                dto.other_user = self.user_dto(other_p.user, online)
                dto.name = other_p.user.full_name
                dto.other_last_read_id = other_p.ultimo_leido_id
        else:
            dto.online_count = len(online)
        return dto

    def conversations(self, user: User, online: Set[int]) -> List[ChatConversationResponse]:
        general = ensure_general_room(self.db)
        directs = self.db.query(ChatConversation).join(
            ChatParticipant, ChatParticipant.conversation_id == ChatConversation.id).filter(
            ChatParticipant.user_id == user.id, ChatConversation.tipo == ChatConversationType.DIRECT.value,
            ChatConversation.estado.is_(True)).all()
        result = [self.conversation_dto(general, user, online)]
        dtos = [self.conversation_dto(c, user, online) for c in directs]
        dtos.sort(key=lambda d: d.last_message.id if d.last_message else 0, reverse=True)
        return result + dtos

    def recipients(self, conv: ChatConversation) -> Optional[Set[int]]:
        """None = todos los conectados (sala general); si no, los ids de los participantes."""
        if conv.tipo == ChatConversationType.GENERAL.value:
            return None
        return {p.user_id for p in conv.participants}

    # ---------- mensajes ----------

    def message_dto(self, m: ChatMessage, online: Iterable[int] = ()) -> ChatMessageResponse:
        # Se guarda en UTC (sin zona) y se envía con zona: el navegador lo muestra en la hora local del usuario
        return ChatMessageResponse(id=m.id, conversation_id=m.conversation_id, sender=self.user_dto(m.user, online),
                                   content=m.contenido, created_at=m.creado.replace(tzinfo=timezone.utc))

    def history(self, user: User, conversation_id: int, before: Optional[int], limit: int,
                online: Set[int]) -> List[ChatMessageResponse]:
        conv = self.get_conversation_for(user, conversation_id)
        q = self.db.query(ChatMessage).filter(ChatMessage.conversation_id == conv.id, ChatMessage.estado.is_(True))
        if before:
            q = q.filter(ChatMessage.id < before)
        rows = q.order_by(ChatMessage.id.desc()).limit(max(1, min(limit, 100))).all()
        return [self.message_dto(m, online) for m in reversed(rows)]

    def send(self, user: User, conversation_id: int, raw_content: object) -> tuple[ChatMessage, ChatConversation]:
        conv = self.get_conversation_for(user, conversation_id)
        if conv.tipo == ChatConversationType.DIRECT.value:
            other = next((p.user_id for p in conv.participants if p.user_id != user.id), None)
            if other is None or self.find_user(other) is None:
                raise ForbiddenChatException("The other user is no longer active")
        now = datetime.now(timezone.utc).replace(tzinfo=None)   # UTC, igual en Neon (UTC) y en un PC local
        message = ChatMessage(conversation_id=conv.id, user_id=user.id, contenido=clean_content(raw_content), creado=now)
        self.db.add(message)
        conv.ultimo_mensaje_en = now
        self.db.flush()
        me = self._participant(conv, user.id, create=True)
        me.ultimo_leido_id = message.id     # lo propio cuenta como leído
        self.db.commit()
        self.db.refresh(message)
        return message, conv

    def mark_read(self, user: User, conversation_id: int, message_id: int) -> tuple[ChatConversation, int]:
        conv = self.get_conversation_for(user, conversation_id)
        last_id = self.db.query(func.max(ChatMessage.id)).filter(ChatMessage.conversation_id == conv.id).scalar() or 0
        me = self._participant(conv, user.id, create=True)
        me.ultimo_leido_id = max(me.ultimo_leido_id or 0, min(message_id, last_id))
        self.db.commit()
        return conv, me.ultimo_leido_id
