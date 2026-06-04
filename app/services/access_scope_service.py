from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.permissions import ROLE_ADMIN, ROLE_CONSULTANT, ROLE_STUDENT, ROLE_TEACHER
from app.models.classes import Class
from app.models.class_teacher_link import class_teacher_link
from app.models.student import Student
from app.models.user import User


class AccessScopeService:
    @staticmethod
    def is_admin(user: User) -> bool:
        return user.role == ROLE_ADMIN

    @staticmethod
    def teacher_class_ids(db: Session, user: User) -> list[int]:
        if user.role != ROLE_TEACHER or not user.teacher_id:
            return []
        rows = (
            db.query(Class.id)
            .join(class_teacher_link, Class.id == class_teacher_link.c.class_id)
            .filter(
                class_teacher_link.c.teacher_id == user.teacher_id,
                Class.is_deleted == False,
            )
            .all()
        )
        return [row[0] for row in rows]

    @staticmethod
    def teacher_class_names(db: Session, user: User) -> list[str]:
        if user.role != ROLE_TEACHER or not user.teacher_id:
            return []
        rows = (
            db.query(Class.class_id)
            .join(class_teacher_link, Class.id == class_teacher_link.c.class_id)
            .filter(
                class_teacher_link.c.teacher_id == user.teacher_id,
                Class.is_deleted == False,
            )
            .all()
        )
        return [row[0] for row in rows]

    @staticmethod
    def allowed_student_ids(db: Session, user: User) -> list[str] | None:
        if user.role == ROLE_ADMIN:
            return None
        if user.role == ROLE_STUDENT:
            return [user.student_id] if user.student_id else []
        if user.role == ROLE_TEACHER:
            class_ids = AccessScopeService.teacher_class_ids(db, user)
            if not class_ids:
                return []
            rows = (
                db.query(Student.student_id)
                .filter(Student.class_id.in_(class_ids), Student.is_deleted == False)
                .all()
            )
            return [row[0] for row in rows]
        if user.role == ROLE_CONSULTANT:
            if not user.teacher_id:
                return []
            rows = (
                db.query(Student.student_id)
                .filter(Student.consultant_id == user.teacher_id, Student.is_deleted == False)
                .all()
            )
            return [row[0] for row in rows]
        return []

    @staticmethod
    def can_access_student(db: Session, user: User, student_id: str) -> bool:
        allowed = AccessScopeService.allowed_student_ids(db, user)
        return allowed is None or student_id in allowed
