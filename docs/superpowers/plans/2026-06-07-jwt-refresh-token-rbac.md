# JWT Refresh Token RBAC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有固定角色 RBAC 基础上补齐数据库 refresh token、JWT 生命周期接口和权限码依赖。

**Architecture:** 继续遵守 `controller -> service -> dao -> model`。`app/core/security.py` 承担密码哈希、JWT 编解码、随机 refresh token 与哈希；`TokenService` 编排 refresh token 业务规则；DAO 只做数据库读写；controller 只接收请求并调用 service。

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, MySQL runtime, SQLite in-memory tests.

---

## File Structure

- Create: `app/core/security.py`  
  密码哈希、JWT access token 创建/解析、refresh token 明文生成和哈希。
- Create: `app/models/refresh_token.py`  
  `user_refresh_tokens` ORM 模型。
- Create: `app/dao/refresh_token.py`  
  refresh token CRUD/query、撤销、按用户批量撤销。
- Create: `app/services/token_service.py`  
  生成、校验、轮换、撤销 refresh token。
- Modify: `app/services/auth_service.py`  
  调用 security/token service，增加 refresh/logout/change-password。
- Modify: `app/controllers/auth.py`  
  新增三个认证路由，新增 `require_permissions(...)`。
- Modify: `app/views/schemas/auth.py`  
  增加 refresh/logout/change-password 请求 schema，登录响应增加 `refresh_token`。
- Modify: `app/main.py`  
  导入 refresh token 模型，确保启动 `Base.metadata.create_all` 能创建表。
- Create: `tests/test_auth_tokens.py`  
  覆盖密码、access token、refresh token、登录、刷新、退出、改密。
- Create: `tests/test_auth_permissions.py`  
  覆盖权限码依赖。
- Modify: `README.md`  
  记录 JWT refresh token 与权限策略。

---

### Task 1: Security Core

**Files:**
- Create: `app/core/security.py`
- Modify: `app/services/auth_service.py`
- Test: `tests/test_auth_tokens.py`

- [ ] **Step 1: Write failing security tests**

Create `tests/test_auth_tokens.py`:

```python
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.core import security


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
```

- [ ] **Step 2: Run failing test**

Run:

```powershell
python -m pytest tests/test_auth_tokens.py -q
```

Expected: fails because `app.core.security` is missing.

- [ ] **Step 3: Create security module**

Create `app/core/security.py`:

```python
import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "wolinsms-dev-secret")
JWT_ACCESS_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "30"))
JWT_REFRESH_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), 120000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, salt, stored = password_hash.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), 120000)
    return hmac.compare_digest(digest.hex(), stored)


def create_access_token(user: Any, expires_delta: timedelta | None = None, now: datetime | None = None) -> str:
    issued_at = now or datetime.now(timezone.utc)
    payload = {
        "sub": user.username,
        "uid": user.id,
        "role": user.role,
        "name": user.real_name,
        "teacher_id": user.teacher_id,
        "student_id": user.student_id,
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + (expires_delta or timedelta(minutes=JWT_ACCESS_EXPIRE_MINUTES))).timestamp()),
        "jti": secrets.token_urlsafe(24),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = (
        f"{_b64url_encode(json.dumps(header, separators=(',', ':')).encode())}."
        f"{_b64url_encode(json.dumps(payload, separators=(',', ':')).encode())}"
    )
    signature = hmac.new(JWT_SECRET_KEY.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict | None:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}"
        expected = hmac.new(JWT_SECRET_KEY.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64url_encode(expected), signature_b64):
            return None
        payload = json.loads(_b64url_decode(payload_b64))
        if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
            return None
        return payload
    except Exception:
        return None


def create_refresh_token_plaintext() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
```

- [ ] **Step 4: Make `AuthService` delegate security helpers**

In `app/services/auth_service.py`, import:

```python
from app.core import security
```

Replace helper methods:

```python
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
```

Remove imports no longer used by `auth_service.py`: `base64`, `hashlib`, `hmac`, `json`, `os`, `secrets`, `timedelta`, `timezone`.

- [ ] **Step 5: Verify and commit**

Run:

```powershell
python -m pytest tests/test_auth_tokens.py -q
```

Expected: `3 passed`.

Commit:

```powershell
git add app/core/security.py app/services/auth_service.py tests/test_auth_tokens.py
git commit -m "抽取认证安全工具"
```

---

### Task 2: Refresh Token Persistence

**Files:**
- Create: `app/models/refresh_token.py`
- Create: `app/dao/refresh_token.py`
- Create: `app/services/token_service.py`
- Modify: `app/main.py`
- Test: `tests/test_auth_tokens.py`

- [ ] **Step 1: Add persistence tests**

Append to `tests/test_auth_tokens.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.refresh_token import UserRefreshToken
from app.models.user import User
from app.services.token_service import TokenService


def make_db():
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return TestingSession()


def add_user(db):
    user = User(
        username="admin",
        password_hash=security.hash_password("admin123"),
        real_name="System Admin",
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_refresh_token_is_stored_as_hash():
    db = make_db()
    try:
        user = add_user(db)

        plain = TokenService.issue_refresh_token(db, user)
        row = db.query(UserRefreshToken).one()

        assert plain
        assert row.token_hash == security.hash_refresh_token(plain)
        assert row.token_hash != plain
        assert row.revoked_at is None
    finally:
        db.close()


def test_refresh_token_rotation_revokes_old_token():
    db = make_db()
    try:
        user = add_user(db)
        old_plain = TokenService.issue_refresh_token(db, user)

        result = TokenService.rotate_refresh_token(db, old_plain)

        assert result is not None
        refreshed_user, new_plain = result
        assert refreshed_user.id == user.id
        assert new_plain != old_plain
        assert TokenService.rotate_refresh_token(db, old_plain) is None
    finally:
        db.close()
```

- [ ] **Step 2: Run failing test**

Run:

```powershell
python -m pytest tests/test_auth_tokens.py -q
```

Expected: fails because refresh token model/service is missing.

- [ ] **Step 3: Create refresh token model**

Create `app/models/refresh_token.py`:

```python
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from app.core.database import Base


class UserRefreshToken(Base):
    __tablename__ = "user_refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    jti = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    replaced_by_jti = Column(String(64), nullable=True)
    created_ip = Column(String(64), nullable=True)
    created_user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 4: Create refresh token DAO**

Create `app/dao/refresh_token.py`:

```python
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.refresh_token import UserRefreshToken


class RefreshTokenDAO:
    @staticmethod
    def create(db: Session, data: dict) -> UserRefreshToken:
        token = UserRefreshToken(**data)
        db.add(token)
        db.commit()
        db.refresh(token)
        return token

    @staticmethod
    def get_by_hash(db: Session, token_hash: str) -> UserRefreshToken | None:
        return db.query(UserRefreshToken).filter(UserRefreshToken.token_hash == token_hash).first()

    @staticmethod
    def revoke(db: Session, token: UserRefreshToken, revoked_at: datetime, replaced_by_jti: str | None = None) -> UserRefreshToken:
        token.revoked_at = revoked_at
        token.replaced_by_jti = replaced_by_jti
        db.commit()
        db.refresh(token)
        return token

    @staticmethod
    def revoke_all_for_user(db: Session, user_id: int, revoked_at: datetime) -> int:
        rows = (
            db.query(UserRefreshToken)
            .filter(UserRefreshToken.user_id == user_id, UserRefreshToken.revoked_at.is_(None))
            .all()
        )
        for row in rows:
            row.revoked_at = revoked_at
        db.commit()
        return len(rows)


refresh_token_dao = RefreshTokenDAO()
```

- [ ] **Step 5: Create token service**

Create `app/services/token_service.py`:

```python
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core import security
from app.dao.refresh_token import refresh_token_dao
from app.models.user import User


class TokenService:
    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def issue_refresh_token(db: Session, user: User, created_ip: str | None = None, created_user_agent: str | None = None) -> str:
        plain = security.create_refresh_token_plaintext()
        refresh_token_dao.create(
            db,
            {
                "user_id": user.id,
                "token_hash": security.hash_refresh_token(plain),
                "jti": secrets.token_urlsafe(24),
                "expires_at": TokenService._now() + timedelta(days=security.JWT_REFRESH_EXPIRE_DAYS),
                "created_ip": created_ip,
                "created_user_agent": created_user_agent,
            },
        )
        return plain

    @staticmethod
    def rotate_refresh_token(db: Session, refresh_token: str) -> tuple[User, str] | None:
        now = TokenService._now()
        row = refresh_token_dao.get_by_hash(db, security.hash_refresh_token(refresh_token))
        if row is None or row.revoked_at is not None or row.expires_at <= now:
            return None
        user = db.query(User).filter(User.id == row.user_id, User.is_active == True).first()
        if user is None:
            return None
        new_plain = security.create_refresh_token_plaintext()
        new_jti = secrets.token_urlsafe(24)
        refresh_token_dao.revoke(db, row, now, replaced_by_jti=new_jti)
        refresh_token_dao.create(
            db,
            {
                "user_id": user.id,
                "token_hash": security.hash_refresh_token(new_plain),
                "jti": new_jti,
                "expires_at": now + timedelta(days=security.JWT_REFRESH_EXPIRE_DAYS),
            },
        )
        return user, new_plain

    @staticmethod
    def revoke_refresh_token(db: Session, refresh_token: str) -> bool:
        row = refresh_token_dao.get_by_hash(db, security.hash_refresh_token(refresh_token))
        if row is None or row.revoked_at is not None:
            return False
        refresh_token_dao.revoke(db, row, TokenService._now())
        return True

    @staticmethod
    def revoke_all_for_user(db: Session, user_id: int) -> int:
        return refresh_token_dao.revoke_all_for_user(db, user_id, TokenService._now())
```

- [ ] **Step 6: Import model at startup**

In `app/main.py`, add:

```python
from app.models.refresh_token import UserRefreshToken  # noqa: F401
```

- [ ] **Step 7: Verify and commit**

Run:

```powershell
python -m pytest tests/test_auth_tokens.py -q
```

Expected: `5 passed`.

Commit:

```powershell
git add app/models/refresh_token.py app/dao/refresh_token.py app/services/token_service.py app/main.py tests/test_auth_tokens.py
git commit -m "新增刷新令牌持久化"
```

---

### Task 3: Login, Refresh, Logout, Change Password

**Files:**
- Modify: `app/views/schemas/auth.py`
- Modify: `app/services/auth_service.py`
- Modify: `app/controllers/auth.py`
- Test: `tests/test_auth_tokens.py`

- [ ] **Step 1: Add auth lifecycle tests**

Append to `tests/test_auth_tokens.py`:

```python
from app.services.auth_service import AuthService
from app.views.schemas.auth import ChangePasswordRequest, LoginRequest, LogoutRequest, RefreshTokenRequest


def test_login_returns_access_and_refresh_tokens():
    db = make_db()
    try:
        add_user(db)

        response = AuthService.login(db, LoginRequest(username=" admin ", password="admin123"))

        assert response["code"] == 1
        assert response["data"].access_token
        assert response["data"].refresh_token
        assert response["data"].token_type == "bearer"
    finally:
        db.close()


def test_refresh_rotates_token_and_rejects_old_token():
    db = make_db()
    try:
        add_user(db)
        login_response = AuthService.login(db, LoginRequest(username="admin", password="admin123"))
        old_refresh = login_response["data"].refresh_token

        response = AuthService.refresh(db, RefreshTokenRequest.model_validate({"refresh_token": old_refresh}))

        assert response["code"] == 1
        assert response["data"].access_token
        assert response["data"].refresh_token != old_refresh
        assert AuthService.refresh(db, RefreshTokenRequest.model_validate({"refresh_token": old_refresh}))["code"] == 0
    finally:
        db.close()


def test_logout_revokes_refresh_token():
    db = make_db()
    try:
        add_user(db)
        login_response = AuthService.login(db, LoginRequest(username="admin", password="admin123"))
        refresh_token = login_response["data"].refresh_token

        logout_response = AuthService.logout(db, LogoutRequest.model_validate({"refresh_token": refresh_token}))

        assert logout_response["code"] == 1
        assert AuthService.refresh(db, RefreshTokenRequest.model_validate({"refresh_token": refresh_token}))["code"] == 0
    finally:
        db.close()


def test_change_password_revokes_refresh_tokens_and_updates_password():
    db = make_db()
    try:
        user = add_user(db)
        login_response = AuthService.login(db, LoginRequest(username="admin", password="admin123"))
        refresh_token = login_response["data"].refresh_token

        response = AuthService.change_password(
            db,
            user,
            ChangePasswordRequest(old_password="admin123", new_password="newpass123"),
        )

        assert response["code"] == 1
        assert AuthService.refresh(db, RefreshTokenRequest.model_validate({"refresh_token": refresh_token}))["code"] == 0
        assert AuthService.login(db, LoginRequest(username="admin", password="newpass123"))["code"] == 1
    finally:
        db.close()
```

- [ ] **Step 2: Run failing tests**

Run:

```powershell
python -m pytest tests/test_auth_tokens.py -q
```

Expected: missing schemas or service methods.

- [ ] **Step 3: Extend auth schemas**

In `app/views/schemas/auth.py`, add request models and update response:

```python
class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut
```

- [ ] **Step 4: Add AuthService lifecycle methods**

In `app/services/auth_service.py`, import:

```python
from app.services.token_service import TokenService
from app.views.schemas.auth import ChangePasswordRequest, LoginRequest, LoginResponse, LogoutRequest, RefreshTokenRequest, UserOut
```

Replace `login` and add methods:

```python
@staticmethod
def login(db: Session, payload: LoginRequest):
    username = payload.username.strip()
    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    if not user or not AuthService.verify_password(payload.password, user.password_hash):
        return fail("账号或密码错误")
    return success(
        LoginResponse.model_validate(
            {
                "access_token": AuthService.create_access_token(user),
                "refresh_token": TokenService.issue_refresh_token(db, user),
                "user": AuthService.user_out(user),
            }
        ),
        "login success",
    )

@staticmethod
def refresh(db: Session, payload: RefreshTokenRequest):
    result = TokenService.rotate_refresh_token(db, payload.refresh_token)
    if result is None:
        return fail("refresh token invalid")
    user, refresh_token = result
    return success(
        LoginResponse.model_validate(
            {
                "access_token": AuthService.create_access_token(user),
                "refresh_token": refresh_token,
                "user": AuthService.user_out(user),
            }
        ),
        "token refreshed",
    )

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
    db.commit()
    TokenService.revoke_all_for_user(db, user.id)
    return success(None, "password changed")
```

- [ ] **Step 5: Add controller routes**

In `app/controllers/auth.py`, import:

```python
from app.views.schemas.auth import ChangePasswordRequest, LoginRequest, LogoutRequest, RefreshTokenRequest
```

Add routes:

```python
@auth_router.post("/refresh", summary="刷新访问令牌")
def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    return AuthService.refresh(db, payload)


@auth_router.post("/logout", summary="退出登录并撤销刷新令牌")
def logout(payload: LogoutRequest, db: Session = Depends(get_db)):
    return AuthService.logout(db, payload)


@auth_router.post("/change-password", summary="修改当前用户密码")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return AuthService.change_password(db, user, payload)
```

- [ ] **Step 6: Verify and commit**

Run:

```powershell
python -m pytest tests/test_auth_tokens.py -q
```

Expected: all auth token tests pass.

Commit:

```powershell
git add app/views/schemas/auth.py app/services/auth_service.py app/controllers/auth.py tests/test_auth_tokens.py
git commit -m "补齐认证令牌生命周期"
```

---

### Task 4: Permission Dependency

**Files:**
- Modify: `app/controllers/auth.py`
- Test: `tests/test_auth_permissions.py`

- [ ] **Step 1: Write permission dependency tests**

Create `tests/test_auth_permissions.py`:

```python
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.controllers import auth as auth_api


class FakeUser:
    def __init__(self, username, role):
        self.username = username
        self.role = role


def make_client(fake_user):
    app = FastAPI()

    @app.get("/protected")
    def protected(user=Depends(auth_api.require_permissions("logs:read"))):
        return {"user": user.username}

    app.dependency_overrides[auth_api.get_current_user] = lambda: fake_user
    return TestClient(app)


def test_require_permissions_allows_role_with_permission():
    response = make_client(FakeUser("admin", "admin")).get("/protected")

    assert response.status_code == 200
    assert response.json() == {"user": "admin"}


def test_require_permissions_rejects_role_without_permission():
    response = make_client(FakeUser("student", "student")).get("/protected")

    assert response.status_code == 403
    assert response.json()["detail"] == "permission denied"
```

- [ ] **Step 2: Run failing test**

Run:

```powershell
python -m pytest tests/test_auth_permissions.py -q
```

Expected: `require_permissions` is missing.

- [ ] **Step 3: Implement permission dependency**

In `app/controllers/auth.py`, import:

```python
from app.core.permissions import get_permissions_for_role
```

Add below `require_roles`:

```python
def require_permissions(*permissions: str):
    def dependency(user=Depends(get_current_user)):
        user_permissions = set(get_permissions_for_role(user.role))
        if permissions and not set(permissions).issubset(user_permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="permission denied")
        return user

    return dependency
```

- [ ] **Step 4: Verify and commit**

Run:

```powershell
python -m pytest tests/test_auth_permissions.py -q
```

Expected: `2 passed`.

Commit:

```powershell
git add app/controllers/auth.py tests/test_auth_permissions.py
git commit -m "新增权限码依赖校验"
```

---

### Task 5: Final Verification And Documentation

**Files:**
- Modify: `README.md`
- Test: project verification

- [ ] **Step 1: Update README**

Add near the role permissions section:

```markdown
## Authentication

The backend uses JWT access tokens plus database-backed refresh tokens.

- `POST /auth/login` returns `access_token`, `refresh_token`, `token_type`, and user information.
- `POST /auth/refresh` rotates the refresh token and returns a new token pair.
- `POST /auth/logout` revokes the submitted refresh token.
- `POST /auth/change-password` changes the current user's password and revokes existing refresh tokens for that user.

Refresh tokens are stored only as hashes in `user_refresh_tokens`. Access tokens are verified from the `Authorization: Bearer <token>` header.
```

- [ ] **Step 2: Run AST verification**

Run:

```powershell
python -c "import ast, pathlib; [ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(p)) for p in pathlib.Path('app').rglob('*.py')]; print('AST OK')"
```

Expected:

```text
AST OK
```

- [ ] **Step 3: Run app import verification**

Run:

```powershell
python -c "import app.main; print('import app.main OK')"
```

Expected:

```text
import app.main OK
```

- [ ] **Step 4: Run pytest**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit documentation**

Run:

```powershell
git add README.md
git commit -m "补充认证刷新令牌说明"
```

---

## Self-Review

- Spec coverage: refresh token 入库、JWT access token、刷新、退出、改密、固定权限矩阵、`require_permissions(...)`、统一响应、中文 summary、验证命令均有任务覆盖。
- 占位扫描: 文档没有未完成标记或未定义占位函数。
- Scope check: 没有引入动态 RBAC 表、权限管理后台或无关重构。
- Type consistency: `RefreshTokenRequest`、`LogoutRequest`、`ChangePasswordRequest`、`LoginResponse.refresh_token`、`TokenService` 都先定义再使用。
