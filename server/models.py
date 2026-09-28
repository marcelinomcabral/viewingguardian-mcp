"""Pydantic models for state, profiles, and scene metadata."""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class SceneFlag(BaseModel):
    scene_id: str
    start: float
    end: float
    intensity: Literal["low", "medium", "high"]
    flags: list[str] = Field(default_factory=list)
    description: str = ""


class ChildProfile(BaseModel):
    child_id: str
    name: str
    age: int
    sensitivities: dict[str, str] = Field(default_factory=dict)
    household_rules: dict[str, str] = Field(default_factory=dict)


class InterventionLog(BaseModel):
    session_id: str
    child_id: str
    scene_id: str
    timestamp: float
    action: str
    reason: str = ""


class PlaybackState(BaseModel):
    session_id: str
    title: str = ""
    current_timestamp: float = 0.0
    content_rating: str = "PG"
    audio_language: str = "en"
    subtitle_language: str = "en"
    scenes: list[SceneFlag] = Field(default_factory=list)

    def scene_at(self, timestamp: float) -> Optional[SceneFlag]:
        for scene in self.scenes:
            if scene.start <= timestamp < scene.end:
                return scene
        return None