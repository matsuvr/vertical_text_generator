from fastapi.testclient import TestClient

import main
from tests.helpers import auth_header

client = TestClient(main.app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    j = r.json()
    assert "title" in j
    assert "/render" in j.get("endpoints", {})


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert j.get("status") == "healthy"


def test_debug_html_requires_auth():
    r = client.get("/debug/html")
    assert r.status_code == 401


def test_debug_html_with_auth():
    r = client.get("/debug/html", headers=auth_header())
    assert r.status_code == 200
    # HTML should contain the container class used by the generator
    assert "vertical-text-content" in r.text
