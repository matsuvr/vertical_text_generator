from fastapi.testclient import TestClient

import main

from tests.helpers import auth_header


def test_batch_items_limit():
    client = TestClient(main.app)
    data = {"items": [{"text": "a"} for _ in range(51)]}
    response = client.post("/render/batch", json=data, headers=auth_header())
    assert response.status_code == 400
