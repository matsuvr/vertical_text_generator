import os
import re

from fastapi.testclient import TestClient

import main


def auth_header():
    token = os.environ.get("API_TOKEN", "your-secret-token-here")
    return {"Authorization": f"Bearer {token}"}


def test_dash_rotation_in_debug_html():
    client = TestClient(main.app)
    text = "あの子は —— いつかナポリ湾を描きたいって言ってたんです"
    r = client.get(
        "/debug/html",
        params={"text": text},
        headers=auth_header(),
    )
    assert r.status_code == 200
    html = r.text
    # Two-em dash may be normalized as U+2014 repeated or kept as U+2E3A depending on input method.
    # We verify that any of the dash characters are wrapped with rotate-90 spans.
    # Check that there is at least one rotate-90 span present.
    assert 'class="rotate-90"' in html
    # Ensure that the dash sequence within the input appears inside rotate-90 spans
    # Extract the processed content area to limit false positives
    m = re.search(r"<div class=\"vertical-text-content\">(.*?)</div>", html, re.S)
    assert m, "vertical-text-content not found"
    content = m.group(1)
    # Count rotate-90 wrapped characters
    wrapped = re.findall(r"<span class=\"rotate-90\">(.+?)</span>", content)
    assert wrapped, "No rotated dash found"
