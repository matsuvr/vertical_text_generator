import main
from fastapi.testclient import TestClient


def auth_header():
    return {"Authorization": "Bearer your-secret-token-here"}


def test_batch_items_limit():
    client = TestClient(main.app)
    data = {"items": [{"text": "a"} for _ in range(51)]}
    response = client.post("/render/batch", json=data, headers=auth_header())
    assert response.status_code == 400
