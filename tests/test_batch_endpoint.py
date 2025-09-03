import os

from fastapi.testclient import TestClient

import main


def auth_header():
    token = os.environ.get("API_TOKEN", "your-secret-token-here")
    return {"Authorization": f"Bearer {token}"}


def test_batch_items_limit():
    client = TestClient(main.app)
    data = {"items": [{"text": "a"} for _ in range(51)]}
    response = client.post("/render/batch", json=data, headers=auth_header())
    assert response.status_code == 400
