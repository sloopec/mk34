# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for `app/agents/plot_agent.py` -- structure and the persistence
callback only. No live LLM call: agent *construction* (model/tools/schema
wiring) is asserted directly; live behavior is verified separately via
`uv run python` against a real Gemini call (see TASK-004 walkthrough) and
later end-to-end in TASK-009's smoke test once the orchestrator exists.
"""

from __future__ import annotations

import pytest

from app.agents.plot_agent import _persist_plot_beats, create_plot_agent
from app.schemas import SceneBeatList


def test_create_plot_agent_is_two_stage_sequential() -> None:
    agent = create_plot_agent()

    assert agent.name == "plot_agent"
    assert len(agent.sub_agents) == 2
    context_agent, formalizer_agent = agent.sub_agents
    assert context_agent.output_key == "plot_raw"
    assert formalizer_agent.output_key == "plot_beats"
    assert formalizer_agent.output_schema is SceneBeatList
    # output_schema disables tool calling -- the formalizer must carry none.
    assert not formalizer_agent.tools


def test_create_plot_agent_context_stage_has_context_tools() -> None:
    agent = create_plot_agent()
    context_agent = agent.sub_agents[0]
    tool_names = {
        getattr(t, "__name__", getattr(t, "name", None)) for t in context_agent.tools
    }
    assert "load_plot_outline" in tool_names
    assert "read_chapter_summaries" in tool_names


def test_create_plot_agent_calling_twice_avoids_shared_instances() -> None:
    """Factory-function convention (ADK): each call must build fresh sub-agent
    instances, or reusing the factory across a session raises "agent already
    has a parent"."""
    first = create_plot_agent()
    second = create_plot_agent()
    assert first is not second
    assert first.sub_agents[0] is not second.sub_agents[0]


class _FakeState(dict):
    pass


class _FakeCallbackContext:
    def __init__(self, state):
        self.state = state


@pytest.mark.asyncio
async def test_persist_plot_beats_writes_each_beat(monkeypatch) -> None:
    recorded = []
    monkeypatch.setattr(
        "app.agents.plot_agent.update_plot_outline",
        lambda **kwargs: recorded.append(kwargs) or {"status": "success"},
    )
    state = _FakeState(
        plot_beats={
            "beats": [
                {
                    "chapter": 3,
                    "scene": 1,
                    "pov_character": "David",
                    "location": "Kommune",
                    "beat": "David trifft Sarah.",
                    "turning_point": True,
                    "tension_level": 7,
                    "characters_present": ["David", "Dr. Sarah Lin"],
                }
            ]
        }
    )

    await _persist_plot_beats(_FakeCallbackContext(state))

    assert len(recorded) == 1
    assert recorded[0]["chapter"] == 3
    assert recorded[0]["pov_character"] == "David"


@pytest.mark.asyncio
async def test_persist_plot_beats_handles_missing_state_gracefully(monkeypatch) -> None:
    recorded = []
    monkeypatch.setattr(
        "app.agents.plot_agent.update_plot_outline",
        lambda **kwargs: recorded.append(kwargs),
    )

    await _persist_plot_beats(_FakeCallbackContext(_FakeState()))

    assert recorded == []
