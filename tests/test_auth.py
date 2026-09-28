"""Tests for OAuth middleware and discovery endpoints."""
import os
import pytest
from starlette.testclient import TestClient
from jose import jwt

os.environ["OAUTH_JWT_SECRET"] = "test_secret_that_is_long_enough_for_hs256"
os.environ["OAUTH_ISSUER"] = "https://test.example.com"
os.environ["OAUTH_CLIENT_ID"] = "test-client"

from server.main import mcp


def make_token():
    return jwt.encode(
        {"iss": "https://test.example.com", "aud": "test-client", "sub": "user1"},
        "test_secret_that_is_long_enough_for_hs256",
        algorithm="HS256",
    )


@pytest.fixture
def client():
    return TestClient(mcp.app)


def test_discovery_metadata_has_s256(client):
    """CRITICAL: Alexa+ requires S256 in code_challenge_methods_supported."""
    response = client.get("/.well-known/oauth-authorization-server")
    assert response.status_code == 200
    data = response.json()
    assert "S256" in data["code_challenge_methods_supported"]


def test_protected_resource_metadata(client):
    response = client.get("/.well-known/oauth-protected-resource")
    assert response.status_code == 200
    assert "resource" in response.json()


def test_unauthenticated_request_returns_401(client):
    response = client.post("/mcp", json={"jsonrpc": "2.0", "method": "tools/list", "id": 1})
    assert response.status_code == 401
    # MUST NOT have WWW-Authenticate header
    assert "www-authenticate" not in response.headers


def test_authenticated_request_succeeds(client):
    token = make_token()
    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200