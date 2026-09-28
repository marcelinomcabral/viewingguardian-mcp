"""
OAuth 2.1 discovery documents required by Alexa+.
Uses FastMCP's custom_route decorator.
"""
import os
from starlette.requests import Request
from starlette.responses import JSONResponse


def register_discovery_routes(mcp):
    """Register well-known OAuth discovery endpoints on the FastMCP server."""

    @mcp.custom_route("/.well-known/oauth-protected-resource", methods=["GET"])
    async def protected_resource_metadata(request: Request) -> JSONResponse:
        """RFC 9728 — Protected Resource Metadata."""
        issuer = os.getenv("OAUTH_ISSUER", "https://your-server.example.com")
        return JSONResponse({
            "resource": f"{issuer}/mcp",
            "authorization_servers": [issuer],
            "scopes_supported": [
                "playback:read",
                "playback:control",
                "profile:read",
                "profile:write",
            ],
            "bearer_methods_supported": ["header"],
        })

    @mcp.custom_route("/.well-known/oauth-authorization-server", methods=["GET"])
    async def authorization_server_metadata(request: Request) -> JSONResponse:
        """RFC 8414 — Authorization Server Metadata."""
        issuer = os.getenv("OAUTH_ISSUER", "https://your-server.example.com")
        return JSONResponse({
            "issuer": issuer,
            "authorization_endpoint": f"{issuer}/oauth/authorize",
            "token_endpoint": f"{issuer}/oauth/token",
            "registration_endpoint": f"{issuer}/oauth/register",
            "revocation_endpoint": f"{issuer}/oauth/revoke",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
            "revocation_endpoint_auth_methods_supported": ["none", "client_secret_post"],
            # CRITICAL — Alexa+ rejects if S256 is absent
            "code_challenge_methods_supported": ["S256"],
            "scopes_supported": [
                "playback:read",
                "playback:control",
                "profile:read",
                "profile:write",
            ],
        })