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
