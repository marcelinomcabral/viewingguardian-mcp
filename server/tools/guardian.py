"""
Guardian tools: scene analysis, interventions, child profiles.
"""
from fastmcp.tools import tool
from server.state import get_state, get_profile, log_intervention
from server.analysis import analyze_scene_with_llm, get_cached_analysis, cache_analysis
from server.firetv import send_firetv_command

@tool
async def get_current_context(session_id: str) -> dict:
    """Get current playback state: title, timestamp, scene metadata."""
    state = get_state(session_id)
    scene = state.scene_at(state.current_timestamp)
    return {
        "title": state.title,
        "timestamp_seconds": state.current_timestamp,
        "scene_description": scene.description if scene else "",
        "scene_id": scene.scene_id if scene else "",
        "content_rating": state.content_rating,
        "audio_language": state.audio_language,
        "subtitle_language": state.subtitle_language,
    }


@tool
async def analyze_scene_for_child(
    session_id: str,
    profile_id: str,
    timestamp_seconds: float | None = None,
) -> dict:
    """Analyze the current scene for age-appropriateness against a child profile."""
    state = get_state(session_id)
    profile = get_profile(profile_id)
    ts = timestamp_seconds if timestamp_seconds is not None else state.current_timestamp
    scene = state.scene_at(ts)

    if not scene:
        return {
            "verdict": "safe",
            "reason": "No scene data at this timestamp.",
            "recommended_action": "none",
            "skip_seconds": 0,
        }

    # Check cache first
    cached = get_cached_analysis(scene.scene_id)
    if cached:
        return cached

        # ─── Fast-path: rule-based verdict from scene metadata ──────────
    if "jump_scare" in scene.flags or "pre_jump_scare" in scene.flags:
        verdict = {
            "verdict": "skip",
            "reason": f"Jump scare detected at {int(scene.start)}s. Not suitable for {profile.name} (age {profile.age}).",
            "recommended_action": "skip_forward",
            "skip_seconds": 12,
        }
    elif "peril" in scene.flags or "peak_moment" in scene.flags:
        verdict = {
            "verdict": "flag",
            "reason": f"Peril sequence detected. {profile.name} is sensitive to peril.",
            "recommended_action": "skip_forward",
            "skip_seconds": 8,
        }
    elif "mild_profanity" in scene.flags:
        verdict = {
            "verdict": "caution",
            "reason": "Mild profanity detected. Household rule: family-friendly language.",
            "recommended_action": "replace_dialogue",
            "skip_seconds": 0,
        }
    else:
        verdict = await analyze_scene_with_llm(
            scene_description=scene.description,
            intensity=scene.intensity,
            flags=scene.flags,
            profile=profile.model_dump(),
        )

    cache_analysis(scene.scene_id, verdict)
    return verdict


@tool
async def skip_scene(session_id: str, seconds: int) -> dict:
    """Skip forward N seconds on the active Fire TV playback."""
    result = await send_firetv_command(session_id, "skip", value=seconds)
    state = get_state(session_id)
    state.current_timestamp += seconds
    log_intervention(
        session_id=session_id,
        child_id="mia",
        scene_id="skip",
        timestamp=state.current_timestamp,
        action=f"skip_forward_{seconds}s",
        reason="Guardian intervention",
    )
    return {
        "success": result.get("success", False),
        "new_timestamp_seconds": state.current_timestamp,
    }


@tool
async def get_child_profile(child_id: str) -> dict:
    """Get a child's viewing profile: age, sensitivities, intervention history."""
    profile = get_profile(child_id)
    return {
        "name": profile.name,
        "age": profile.age,
        "sensitivities": profile.sensitivities,
        "household_rules": profile.household_rules,
        "interventions_this_week": 3,  # Demo value
    }


@tool
async def log_decision(
    session_id: str,
    child_id: str,
    scene_timestamp_seconds: float,
    action: str,
    reason: str = "",
) -> dict:
    """Log a guardian intervention for a child's viewing session."""
    log_intervention(
        session_id=session_id,
        child_id=child_id,
        scene_id="decision",
        timestamp=scene_timestamp_seconds,
        action=action,
        reason=reason,
    )
    return {"logged": True, "session_flag_count": 4}  # Demo value


@tool
async def set_boundary(
    child_id: str,
    rule_type: str,
    value: str,
    active_hours: str = "",
) -> dict:
    """Set a persistent viewing boundary for a child profile."""
    profile = get_profile(child_id)
    profile.household_rules[rule_type] = value
    if active_hours:
        profile.household_rules[f"{rule_type}_hours"] = active_hours
    return {"rule_id": f"{child_id}_{rule_type}", "confirmed": True}