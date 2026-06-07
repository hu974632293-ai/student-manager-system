from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core import security
from app.dao.refresh_token import refresh_token_dao
from app.models.classes import Class
from app.models.class_teacher_link import class_teacher_link
from app.models.refresh_token import UserRefreshToken
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.token_service import TokenService
from app.views.schemas.auth import ChangePasswordRequest, LoginRequest, LogoutRequest, RefreshTokenRequest


def make_user(**overrides):
    data = {
        "id": 1,
        "username": "admin",
        "real_name": "System Admin",
        "role": "admin",
        "teacher_id": None,
        "student_id": None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_db():
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    User.__table__.create(engine)
    UserRefreshToken.__table__.create(engine)
    return TestingSession()


def make_scope_db():
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Teacher.__table__.create(engine)
    Class.__table__.create(engine)
    class_teacher_link.create(engine)
    Student.__table__.create(engine)
    return TestingSession()


def add_user(db, **overrides):
    data = {
        "username": "refresh_admin",
        "password_hash": security.hash_password("admin123"),
        "real_name": "Refresh Admin",
        "role": "admin",
        "is_active": True,
    }
    data.update(overrides)
    user = User(**data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_password_hash_roundtrip():
    password_hash = security.hash_password("admin123")

    assert password_hash.startswith("pbkdf2_sha256$")
    assert security.verify_password("admin123", password_hash) is True
    assert security.verify_password("wrong", password_hash) is False


def test_access_token_contains_user_identity():
    token = security.create_access_token(make_user())

    payload = security.decode_access_token(token)

    assert payload["sub"] == "admin"
    assert payload["uid"] == 1
    assert payload["role"] == "admin"
    assert payload["jti"]


def test_expired_access_token_returns_none():
    token = security.create_access_token(
        make_user(),
        expires_delta=timedelta(seconds=-1),
        now=datetime.now(timezone.utc),
    )

    assert security.decode_access_token(token) is None


def test_refresh_token_is_stored_as_hash():
    db = make_db()
    user = add_user(db)

    plain_token = TokenService.issue_refresh_token(db, user)
    stored_token = db.query(UserRefreshToken).filter(UserRefreshToken.user_id == user.id).one()

    assert stored_token.token_hash == security.hash_refresh_token(plain_token)
    assert stored_token.token_hash != plain_token
    assert stored_token.revoked_at is None


def test_refresh_token_rotation_revokes_old_token():
    db = make_db()
    user = add_user(db)
    old_plain = TokenService.issue_refresh_token(db, user)

    rotated = TokenService.rotate_refresh_token(db, old_plain)

    assert rotated is not None
    rotated_user, new_plain = rotated
    assert rotated_user.id == user.id
    assert new_plain != old_plain
    assert TokenService.rotate_refresh_token(db, old_plain) is None


def test_refresh_token_rotation_does_not_create_new_token_when_atomic_consume_fails(monkeypatch):
    db = make_db()
    user = add_user(db)
    old_plain = TokenService.issue_refresh_token(db, user)

    monkeypatch.setattr(refresh_token_dao, "consume_active", lambda *args, **kwargs: 0, raising=False)

    rotated = TokenService.rotate_refresh_token(db, old_plain)
    tokens = db.query(UserRefreshToken).filter(UserRefreshToken.user_id == user.id).all()

    assert rotated is None
    assert len(tokens) == 1
    assert tokens[0].token_hash == security.hash_refresh_token(old_plain)
    assert tokens[0].revoked_at is None


def test_login_returns_access_and_refresh_tokens():
    db = make_db()
    add_user(db, username="admin", real_name="System Admin")

    result = AuthService.login(db, LoginRequest(username=" admin ", password="admin123"))

    assert result["code"] == 1
    assert result["data"].access_token
    assert result["data"].refresh_token
    assert result["data"].token_type == "bearer"


def test_default_teacher_bindings_prefer_non_empty_scopes():
    db = make_scope_db()
    db.add_all(
        [
            Teacher(id=1, teacher_number="T001", name="空范围教师", is_deleted=False),
            Teacher(id=2, teacher_number="T002", name="授课教师", is_deleted=False),
            Teacher(id=3, teacher_number="T003", name="顾问教师", is_deleted=False),
            Class(id=1, class_id="C001", is_deleted=False),
            Student(student_id="S001", class_id=1, name="测试学生", consultant_id=3, is_deleted=False),
        ]
    )
    db.flush()
    db.execute(class_teacher_link.insert().values(class_id=1, teacher_id=2))
    db.commit()

    assert AuthService._first_teacher_with_classes_id(db) == 2
    assert AuthService._first_teacher_with_consultant_students_id(db) == 3
    assert AuthService._teacher_has_classes(db, 1) is False
    assert AuthService._teacher_has_classes(db, 2) is True
    assert AuthService._teacher_has_consultant_students(db, 1) is False
    assert AuthService._teacher_has_consultant_students(db, 3) is True


def test_refresh_rotates_token_and_rejects_old_token():
    db = make_db()
    add_user(db, username="admin", real_name="System Admin")
    login_result = AuthService.login(db, LoginRequest(username="admin", password="admin123"))
    old_refresh = login_result["data"].refresh_token

    refresh_result = AuthService.refresh(db, RefreshTokenRequest.model_validate({"refresh_token": old_refresh}))

    assert refresh_result["code"] == 1
    assert refresh_result["data"].refresh_token != old_refresh
    assert AuthService.refresh(db, RefreshTokenRequest.model_validate({"refresh_token": old_refresh}))["code"] == 0


def test_logout_revokes_refresh_token():
    db = make_db()
    add_user(db, username="admin", real_name="System Admin")
    login_result = AuthService.login(db, LoginRequest(username="admin", password="admin123"))
    refresh_token = login_result["data"].refresh_token

    logout_result = AuthService.logout(db, LogoutRequest.model_validate({"refresh_token": refresh_token}))

    assert logout_result["code"] == 1
    assert AuthService.refresh(db, RefreshTokenRequest.model_validate({"refresh_token": refresh_token}))["code"] == 0


def test_change_password_revokes_refresh_tokens_and_updates_password():
    db = make_db()
    user = add_user(db, username="admin", real_name="System Admin")
    login_result = AuthService.login(db, LoginRequest(username="admin", password="admin123"))
    refresh_token = login_result["data"].refresh_token

    change_result = AuthService.change_password(
        db,
        user,
        ChangePasswordRequest(old_password="admin123", new_password="newpass123"),
    )

    assert change_result["code"] == 1
    assert AuthService.refresh(db, RefreshTokenRequest.model_validate({"refresh_token": refresh_token}))["code"] == 0
    assert AuthService.login(db, LoginRequest(username="admin", password="newpass123"))["code"] == 1
