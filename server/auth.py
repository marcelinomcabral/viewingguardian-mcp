"""
OAuth 2.1 + PKCE S256 authentication for Alexa+ MCP add-on.
Alexa+ requires: 401 without WWW-Authenticate header.
Discovery metadata MUST advertise S256.
"""
import os
from jose import jwt, JWTError
from fastmcp.server.middleware import Middleware, MiddlewareContext
from starlette.responses import JSONResponse


class AlexaAuthMiddleware(Middleware):
    """
    Validates Bearer tokens on every MCP request.
    Returns 401 WITHOUT WWW-Authenticate header (Alexa+ requirement).
    """

    async def on_request(self, context: MiddlewareContext, call_next):
        request = context.request

        # Allow discovery endpoints without auth
        path = request.url.path
        if path.startswith("/.well-known/"):
            return await call_next(context)

        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                {"error": "unauthorized", "error_description": "Missing Bearer token"},
                status_code=401,
                # NO WWW-Authenticate header — Alexa+ requirement
            )

        token = auth_header.removeprefix("Bearer ").strip()

        if not validate_token(token):
            return JSONResponse(
                {"error": "invalid_token", "error_description": "Token validation failed"},
                status_code=401,
            )

        return await call_next(context)


def validate_token(token: str) -> bool:
    """
    Validate JWT token. In production, verify signature against
    your OAuth provider's JWKS endpoint.
    """
    secret = os.getenv("OAUTH_JWT_SECRET")
    if not secret:
        return False
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=os.getenv("OAUTH_CLIENT_ID", "viewingguardian-client"),
        )
        return payload.get("iss") == os.getenv("OAUTH_ISSUER")
    except JWTError:
        return False