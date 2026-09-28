"""Unit tests for Guardian and Lingo tools."""
import pytest
from server.state import load_demo_data
from server.tools import guardian, lingo


@pytest.fixture(autouse=True)
def setup():
    load_demo_data()


@pytest.mark.asyncio
async def test_get_current_context():
    result = await guardian.get_current_context("demo-session-1")
    assert result["title"] == "The Whispering Woods"
    assert result["timestamp_seconds"] == 70.0
    assert result["content_rating"] == "PG"


@pytest.mark.asyncio
async def test_analyze_scene_jump_scare():
    """At t=80, scene 2.2 (jump scare) should be flagged."""
    result = await guardian.analyze_scene_for_child(
        session_id="demo-session-1",
        profile_id="mia",
        timestamp_seconds=80.0,
    )
    assert result["verdict"] == "skip"
    assert result["recommended_action"] == "skip_forward"
    assert result["skip_seconds"] == 12


@pytest.mark.asyncio
async def test_analyze_scene_safe():
    """At t=10, scene 1.1 (safe) should not be flagged."""
    result = await guardian.analyze_scene_for_child(
        session_id="demo-session-1",
        profile_id="mia",
        timestamp_seconds=10.0,
    )
    assert result["verdict"] == "safe"


@pytest.mark.asyncio
async def test_analyze_scene_peril():
    """At t=160, scene 4.1 (peril) should be flagged."""
    result = await guardian.analyze_scene_for_child(
        session_id="demo-session-1",
        profile_id="mia",
        timestamp_seconds=160.0,
    )
    assert result["verdict"] == "flag"
    assert result["recommended_action"] == "skip_forward"


@pytest.mark.asyncio
async def test_translate_subtitles_spanish():
    result = await lingo.translate_subtitles(
        session_id="demo-session-1",
        target_language="es",
    )
    assert len(result["translated_lines"]) > 0
    assert result["translated_lines"][0]["translated"] != result["translated_lines"][0]["original"]


@pytest.mark.asyncio
async def test_dub_scene():
    result = await lingo.dub_scene(
        session_id="demo-session-1",
        target_language="es",
        voice_profile="original",
    )
    assert result["dubbed_audio_url"] != ""
    assert result["confidence"] > 0


@pytest.mark.asyncio
async def test_replace_dialogue():
    result = await lingo.replace_dialogue(
        session_id="demo-session-1",
        original_phrase="What the hell",
        replacement_phrase="What the heck",
        timestamp_start_seconds=126.0,
        timestamp_end_seconds=129.0,
    )
    assert result["replaced"] is True


@pytest.mark.asyncio
async def test_get_child_profile():
    result = await guardian.get_child_profile("mia")
    assert result["name"] == "Mia"
    assert result["age"] == 7
    assert result["sensitivities"]["jump_scares"] == "high"