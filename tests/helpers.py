import os


def auth_header():
    token = os.environ.get("API_TOKEN", "your-secret-token-here")
    return {"Authorization": f"Bearer {token}"}

