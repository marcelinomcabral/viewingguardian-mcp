"""
ViewingGuardian + Lingo MCP Server
Entry point. Alexa+ discovers tools via Streamable HTTP.
"""
import os
from dotenv import load_dotenv
from fastmcp import FastMCP
from server.tools import guardian, lingo
from server.auth import AlexaAuthMiddleware
from server.well_known import register_discovery_routes
from server.ask_shim import alexa_handler


load_dotenv()

# ─── Create MCP server ────────────────────────────────────────────────
mcp = FastMCP(
    name="viewingguardian",
    instructions=(
        "AI guardian and language layer for Fire TV playback. "
        "Use guardian tools to analyze scenes against child profiles and intervene. "
        "Use lingo tools to translate, dub, or replace dialogue."
    ),
)

# ─── Auth middleware (OAuth 2.1 + PKCE S256) ─────────────────────────
#mcp.add_middleware(AlexaAuthMiddleware())

# ─── Register Guardian tools ──────────────────────────────────────────
mcp.add_tool(guardian.get_current_context)
mcp.add_tool(guardian.analyze_scene_for_child)
mcp.add_tool(guardian.skip_scene)
mcp.add_tool(guardian.get_child_profile)
mcp.add_tool(guardian.log_decision)
mcp.add_tool(guardian.set_boundary)

# ─── Register Lingo tools ─────────────────────────────────────────────
mcp.add_tool(lingo.translate_subtitles)
mcp.add_tool(lingo.dub_scene)
mcp.add_tool(lingo.replace_dialogue)
mcp.add_tool(lingo.get_lingo_status)

# ─── Register OAuth discovery endpoints ───────────────────────────────
register_discovery_routes(mcp)

@mcp.custom_route("/alexa", methods=["POST"])
async def alexa_route(request):
    return await alexa_handler(request)

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host=os.getenv("SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVER_PORT", "8000")),
    )