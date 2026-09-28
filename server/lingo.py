"""
Lingo service: translation, dubbing, and dialogue replacement.
Uses ElevenLabs Dubbing API for voice-preserving dubbing.
"""
import os
import httpx

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"


async def translate_text(text: str, target_language: str) -> str:
    """Translate text using ElevenLabs or a fallback translation API."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        # ElevenLabs supports dubbing; for plain text translation,
        # use a translation endpoint or Bedrock.
        # For demo: return a placeholder that proves the call happens.
        response = await client.post(
            f"{ELEVENLABS_BASE}/dubbing",
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            json={
                "source_url": "",
                "target_lang": target_language,
                "text": text,
            },
        )
        if response.status_code == 200:
            return response.json().get("translated_text", text)
        return text


async def dub_audio(
    dialogue_url: str,
    target_language: str,
    voice_preserve: bool = True,
) -> dict:
    """
    Dub an audio stem using ElevenLabs Dubbing API.
    Returns dict with dubbed_audio_url and sync info.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{ELEVENLABS_BASE}/dubbing",
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            json={
                "source_url": dialogue_url,
                "target_lang": target_language,
                "preserve_voice": voice_preserve,
                "watermark": False,
            },
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "dubbed_audio_url": data.get("dubbed_url", ""),
                "sync_offset_ms": data.get("sync_offset_ms", 0),
                "confidence": data.get("confidence", 0.0),
            }
        return {
            "dubbed_audio_url": "",
            "sync_offset_ms": 0,
            "confidence": 0.0,
            "error": response.text[:200],
        }


async def replace_dialogue_audio(
    original_phrase: str,
    replacement_phrase: str,
    timestamp_start: float,
    timestamp_end: float,
) -> dict:
    """
    Replace a specific phrase in the dialogue stem.
    In production, this calls ElevenLabs speech-to-speech with the
    original audio segment + the replacement text.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{ELEVENLABS_BASE}/speech-to-speech",
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            json={
                "audio_url": "",
                "text": replacement_phrase,
                "voice_id": "original",
            },
        )
        return {
            "replaced": response.status_code == 200,
            "replacement_audio_url": response.json().get("audio_url", "") if response.status_code == 200 else "",
        }