"""
Fire TV control via Home Assistant REST API.
Sends skip, pause, and resume commands to the Fire TV.
"""
import os
import httpx

HA_URL = os.getenv("HA_URL", "http://homeassistant.local:8123/api")
HA_TOKEN = os.getenv("HA_TOKEN", "")


async def send_firetv_command(session_id: str, command: str, value=None) -> dict:
    """
    Send a command to the Fire TV via Home Assistant.
    Commands: skip, pause, resume, set_volume
    """
    entity_id = f"media_player.firetv_{session_id}"

    service_map = {
        "skip": "media_next_track",
        "pause": "media_pause",
        "resume": "media_play",
    }

    service = service_map.get(command)
    if not service:
        return {"success": False, "error": f"Unknown command: {command}"}

    payload = {"entity_id": entity_id}
    if command == "skip" and value:
        # HA doesn't natively support skip-by-seconds.
        # Fire TV ADB or a companion app is needed for precise skips.
        # For demo, use media_next_track as a coarse skip.
        payload["seek_seconds"] = value

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{HA_URL}/services/media_player/{service}",
                headers={
                    "Authorization": f"Bearer {HA_TOKEN}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            return {"success": response.status_code in (200, 201)}
    except httpx.RequestError as e:
        return {"success": False, "error": str(e)}