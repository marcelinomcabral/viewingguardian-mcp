"""Latency tests. Alexa+ requires <500ms round-trip."""
import time
import pytest
from server.state import load_demo_data
from server.tools import guardian


@pytest.fixture(autouse=True)
def setup():
    load_demo_data()


@pytest.mark.asyncio
async def test_cached_analysis_latency():
    """Cached analysis must return in <50ms."""
    # Warm cache
    await guardian.analyze_scene_for_child("demo-session-1", "mia", 80.0)

    start = time.perf_counter()
    await guardian.analyze_scene_for_child("demo-session-1", "mia", 80.0)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 50, f"Cached analysis took {elapsed_ms:.0f}ms"


@pytest.mark.asyncio
async def test_get_context_latency():
    start = time.perf_counter()
    await guardian.get_current_context("demo-session-1")
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 50, f"get_current_context took {elapsed_ms:.0f}ms"