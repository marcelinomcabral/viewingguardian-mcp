"""
ASK-to-MCP shim.
Accepts traditional Alexa Skills Kit requests at /alexa and translates
them into calls against the guardian tools. This lets the Developer
Console simulator exercise the skill end-to-end.

This is a demo bridge — the production path is the MCP Toolkit.
"""
from starlette.requests import Request
from starlette.responses import JSONResponse
from server.tools import guardian


def _ssml(text: str) -> dict:
    return {"type": "SSML", "ssml": f"<speak>{text}</speak>"}


def _ask_response(speech: str, end_session: bool = False) -> JSONResponse:
    return JSONResponse({
        "version": "1.0",
        "response": {
            "outputSpeech": _ssml(speech),
            "shouldEndSession": end_session,
        },
    })


async def alexa_handler(request: Request) -> JSONResponse:
    """Entry point for ASK requests from the Developer Console simulator."""
    try:
        body = await request.json()
    except Exception:
        return _ask_response("I couldn't read the request.", end_session=True)

    # ── Handle standard lifecycle requests ─────────────────────────
    req_type = body.get("request", {}).get("type", "")

    if req_type == "LaunchRequest":
        return _ask_response(
            "Viewing Guardian is ready. Ask me what's playing, "
            "or whether a scene is okay for your child."
        )

    if req_type == "SessionEndedRequest":
        return _ask_response("Goodbye.", end_session=True)

    if req_type != "IntentRequest":
        return _ask_response("I'm not sure how to handle that.", end_session=True)

    # ── Handle the AnalyzeSceneIntent ──────────────────────────────
    intent = body["request"]["intent"]
    intent_name = intent.get("name", "")
    slots = intent.get("slots", {})
    child_slot = slots.get("child", {}).get("value") or "mia"

    # Normalize to a profile id
    profile_id = "mia" if child_slot.lower() in ("mia", "my daughter", "my son") else child_slot.lower()

    if intent_name == "AnalyzeSceneIntent":
        # 1. Get current context
        context = await guardian.get_current_context("demo-session-1")
        title = context.get("title", "this content")
        ts = context.get("timestamp_seconds", 0)

        # 2. Analyze for the child
        verdict = await guardian.analyze_scene_for_child(
            session_id="demo-session-1",
            profile_id=profile_id,
            timestamp_seconds=ts,
        )

        v = verdict.get("verdict", "safe")
        reason = verdict.get("reason", "")
        action = verdict.get("recommended_action", "none")
        skip = verdict.get("skip_seconds", 0)

        # 3. Build a spoken response
        if v == "skip":
            speech = (
                f"This is a flagged scene. {reason} "
                f"I recommend skipping forward {skip} seconds. "
                f"Say 'skip it' to proceed."
            )
        elif v == "flag":
            speech = (
                f"Caution. {reason} "
                f"I can skip {skip} seconds or pause. What would you like?"
            )
        elif v == "caution":
            speech = f"Caution advised. {reason}"
        else:
            speech = f"You're watching {title}. This scene looks safe. Enjoy."

        return _ask_response(speech, end_session=False)

    if intent_name == "AMAZON.HelpIntent":
        return _ask_response(
            "Ask me: what's playing. Or: is this okay for Mia."
        )

    if intent_name in ("AMAZON.StopIntent", "AMAZON.CancelIntent"):
        return _ask_response("Okay. Stopping.", end_session=True)

    return _ask_response("I don't recognize that intent yet.", end_session=True)