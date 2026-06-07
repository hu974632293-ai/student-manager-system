import time

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core import security
from app.core.database import Base, engine, get_db
from app.core.permissions import get_modules_for_role, get_permissions_for_role
from app.core.response import fail, success
from app.core.schema_compat import ensure_user_identity_columns
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User
from app.services.token_service import TokenService
from app.views.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshTokenRequest,
    UserOut,
)


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return security.hash_password(password)

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        return security.verify_password(password, password_hash)

    @staticmethod
    def create_access_token(user: User) -> str:
        return security.create_access_token(user)

    @staticmethod
    def decode_access_token(token: str):
        return security.decode_access_token(token)

    @staticmethod
    def get_current_user(db: Session, authorization: str | None):
        if not authorization or not authorization.lower().startswith("bearer "):
            return None
        payload = AuthService.decode_access_token(authorization.split(" ", 1)[1])
        if not payload:
            return None
        return db.query(User).filter(User.username == payload["sub"], User.is_active == True).first()

    @staticmethod
    def ensure_default_users() -> None:
        for attempt in range(5):
            try:
                AuthService._ensure_default_users_once()
                return
            except OperationalError:
                if attempt == 4:
                    raise
                time.sleep(2)

    @staticmethod
    def _ensure_default_users_once() -> None:
        Base.metadata.create_all(bind=engine)
        ensure_user_identity_columns()
        db = next(get_db())
        try:
            demo_teacher = db.query(Teacher).filter(Teacher.is_deleted == False).order_by(Teacher.id).first()
            demo_student = db.query(Student).filter(Student.is_deleted == False).order_by(Student.id).first()
            demo_teacher_id = demo_teacher.id if demo_teacher else None
            demo_student_id = demo_student.student_id if demo_student else None
        finally:
            db.close()
        defaults = [
            ("admin", "admin123", "System Admin", "admin", None, None),
            ("teacher", "teacher123", "Demo Teacher", "teacher", demo_teacher_id, None),
            ("consultant", "consultant123", "Consultant", "consultant", demo_teacher_id, None),
            ("student", "student123", "Demo Student", "student", None, demo_student_id),
        ]
        db = next(get_db())
        try:
            for username, password, real_name, role, teacher_id, student_id in defaults:
                user = db.query(User).filter(User.username == username).first()
                if not user:
                    db.add(
                        User(
                            username=username,
                            password_hash=AuthService.hash_password(password),
                            real_name=real_name,
                            role=role,
                            teacher_id=teacher_id,
                            student_id=student_id,
                        )
                    )
                else:
                    if not AuthService.verify_password(password, user.password_hash):
                        user.password_hash = AuthService.hash_password(password)
                    if user.teacher_id is None and teacher_id is not None:
                        user.teacher_id = teacher_id
                    if user.student_id is None and student_id is not None:
                        user.student_id = student_id
            db.commit()
        finally:
            db.close()

    @staticmethod
    def user_out(user: User) -> UserOut:
        return UserOut(
            id=user.id,
            username=user.username,
            real_name=user.real_name,
            role=user.role,
            teacher_id=user.teacher_id,
            student_id=user.student_id,
            permissions=get_permissions_for_role(user.role),
            modules=get_modules_for_role(user.role),
        )

    @staticmethod
    def _login_response(user: User, refresh_token: str) -> LoginResponse:
        return LoginResponse.model_validate(
            {
                "access_token": AuthService.create_access_token(user),
                "refresh_token": refresh_token,
                "user": AuthService.user_out(user),
            }
        )

    @staticmethod
    def login(db: Session, payload: LoginRequest):
        username = payload.username.strip()
        user = db.query(User).filter(User.username == username, User.is_active == True).first()
        if not user or not AuthService.verify_password(payload.password, user.password_hash):
            return fail("账号或密码错误")
        refresh_token = TokenService.issue_refresh_token(db, user)
        return success(AuthService._login_response(user, refresh_token), "login success")

    @staticmethod
    def me(user: User):
        return success(AuthService.user_out(user), "current user")

    @staticmethod
    def refresh(db: Session, payload: RefreshTokenRequest):
        rotated = TokenService.rotate_refresh_token(db, payload.refresh_token)
        if rotated is None:
            return fail("refresh token invalid")
        user, refresh_token = rotated
        return success(AuthService._login_response(user, refresh_token), "refresh success")

    @staticmethod
    def logout(db: Session, payload: LogoutRequest):
        TokenService.revoke_refresh_token(db, payload.refresh_token)
        return success(None, "logout success")

    @staticmethod
    def change_password(db: Session, user: User, payload: ChangePasswordRequest):
        if not AuthService.verify_password(payload.old_password, user.password_hash):
            return fail("old password incorrect")
        if len(payload.new_password) < 6:
            return fail("new password too short")
        user.password_hash = AuthService.hash_password(payload.new_password)
        TokenService.revoke_all_for_user(db, user.id)
        return success(None, "password changed")
