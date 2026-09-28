"""In-memory session state. Swap for DynamoDB in production."""
import json
from pathlib import Path
from server.models import PlaybackState, ChildProfile

_sessions: dict[str, PlaybackState] = {}
_profiles: dict[str, ChildProfile] = {}

DATA_DIR = Path(__file__).parent / "data"


def load_demo_data():
    """Load the mock film metadata and child profiles."""
    meta_path = DATA_DIR / "whispering_woods_metadata.json"
    profiles_path = DATA_DIR / "profiles.json"

    if meta_path.exists():
        raw = json.loads(meta_path.read_text())
        for session_id, data in raw.get("sessions", {}).items():
            _sessions[session_id] = PlaybackState(**data)

    if profiles_path.exists():
        raw = json.loads(profiles_path.read_text())
        for profile_id, data in raw.get("profiles", {}).items():
            _profiles[profile_id] = ChildProfile(**data)


def get_state(session_id: str) -> PlaybackState:
    if session_id not in _sessions:
        load_demo_data()
    return _sessions.get(session_id, PlaybackState(session_id=session_id))


def get_profile(profile_id: str) -> ChildProfile:
    if profile_id not in _profiles:
        load_demo_data()
    return _profiles.get(
        profile_id,
        ChildProfile(child_id=profile_id, name="Unknown", age=10),
    )


def log_intervention(session_id: str, child_id: str, scene_id: str,
                     timestamp: float, action: str, reason: str = ""):
    """Append to intervention log. In production, write to DynamoDB."""
    state = get_state(session_id)
    print(f"[INTERVENTION] session={session_id} child={child_id} "
          f"scene={scene_id} t={timestamp} action={action} reason={reason}")