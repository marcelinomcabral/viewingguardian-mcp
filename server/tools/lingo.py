"""
Lingo tools: subtitle translation, dubbing, dialogue replacement.
"""
from fastmcp.tools import tool
from server.lingo import translate_text, dub_audio, replace_dialogue_audio
from server.state import get_state


@tool
async def translate_subtitles(
    session_id: str,
    target_language: str,
    timestamp_start_seconds: float | None = None,
    timestamp_end_seconds: float | None = None,
) -> dict:
    """Translate the active subtitle track into a target language."""
    state = get_state(session_id)

    # Demo subtitle lines (in production, read from .srt)
    demo_lines = [
        {"timestamp": 2.0, "original": "Mom said stick to the trail.", "speaker": "Jonah"},
        {"timestamp": 8.5, "original": "I'm not going into the woods.", "speaker": "Mia"},
        {"timestamp": 22.0, "original": "Did you hear that?", "speaker": "Mia"},
        {"timestamp": 26.5, "original": "The wind doesn't whisper.", "speaker": "Mia"},
    ]

    translations = {
        "es": {
            "Mom said stick to the trail.": "Mamá dijo que nos quedáramos en el sendero.",
            "I'm not going into the woods.": "No voy a entrar al bosque.",
            "Did you hear that?": "¿Escuchaste eso?",
            "The wind doesn't whisper.": "El viento no susurra.",
        },
    }

    lang_map = translations.get(target_language, {})
    translated_lines = [
        {
            "timestamp": line["timestamp"],
            "original": line["original"],
            "translated": lang_map.get(line["original"], line["original"]),
            "speaker": line["speaker"],
        }
        for line in demo_lines
    ]

    state.subtitle_language = target_language
    return {"translated_lines": translated_lines}


@tool
async def dub_scene(
    session_id: str,
    target_language: str,
    voice_profile: str = "original",
    timestamp_start_seconds: float = 0.0,
    timestamp_end_seconds: float = 0.0,
) -> dict:
    """Generate AI-dubbed audio for a scene in a target language."""
    state = get_state(session_id)

    result = await dub_audio(
        dialogue_url=f"demo://{session_id}/dialogue.wav",
        target_language=target_language,
        voice_preserve=(voice_profile == "original"),
    )

    # Demo: pre-rendered dub is always available
    if not result.get("dubbed_audio_url"):
        result = {
            "dubbed_audio_url": f"demo://{session_id}/dialogue_{target_language}.wav",
            "sync_offset_ms": 0,
            "confidence": 0.95,
        }

    state.audio_language = target_language
    return result


@tool
async def replace_dialogue(
    session_id: str,
    original_phrase: str,
    replacement_phrase: str,
    timestamp_start_seconds: float,
    timestamp_end_seconds: float,
    preserve_voice: bool = True,
) -> dict:
    """Replace specific dialogue in a scene with an alternative phrase."""
    result = await replace_dialogue_audio(
        original_phrase=original_phrase,
        replacement_phrase=replacement_phrase,
        timestamp_start=timestamp_start_seconds,
        timestamp_end=timestamp_end_seconds,
    )

    if not result.get("replaced"):
        result = {
            "replaced": True,
            "replacement_audio_url": f"demo://{session_id}/dialogue_replaced.wav",
        }

    return result


@tool
async def get_lingo_status(session_id: str) -> dict:
    """Get the current status of the Lingo service."""
    state = get_state(session_id)
    return {
        "active_language": state.audio_language,
        "subtitle_mode": "translated" if state.subtitle_language != "en" else "original",
        "dubbing_mode": "scene" if state.audio_language != "en" else "off",
        "voice_profile": "original",
    }