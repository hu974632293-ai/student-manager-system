from fastapi.testclient import TestClient

from app.main import app


def test_frontend_route_returns_index_for_browser_navigation():
    client = TestClient(app)

    response = client.get("/students", headers={"accept": "text/html"})

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert '<div id="app"></div>' in response.text


def test_api_route_still_requires_login_for_json_request():
    client = TestClient(app)

    response = client.get("/students", headers={"accept": "application/json"})

    assert response.status_code == 401
    assert response.json() == {"code": 0, "msg": "请先登录", "data": None}
