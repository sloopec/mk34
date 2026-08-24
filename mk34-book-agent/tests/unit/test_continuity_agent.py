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

"""Unit tests for `app/agents/continuity_agent.py` -- structure only, no live
LLM call (see TASK-011 walkthrough for the live verification)."""

from __future__ import annotations

from app.agents.continuity_agent import create_continuity_agent
from app.schemas import ContinuityReport


def test_create_continuity_agent_is_two_stage_sequential() -> None:
    agent = create_continuity_agent()

    assert agent.name == "continuity_agent"
    assert len(agent.sub_agents) == 2
    context_agent, formalizer_agent = agent.sub_agents
    assert context_agent.output_key == "continuity_raw"
    assert formalizer_agent.output_key == "continuity_report"
    assert formalizer_agent.output_schema is ContinuityReport
    assert not formalizer_agent.tools


def test_create_continuity_agent_context_stage_has_check_consistency_tool() -> None:
    agent = create_continuity_agent()
    context_agent = agent.sub_agents[0]
    tool_names = {
        getattr(t, "__name__", getattr(t, "name", None)) for t in context_agent.tools
    }
    assert tool_names == {"check_consistency", "validate_world_rules"}


def test_create_continuity_agent_uses_continuity_model() -> None:
    agent = create_continuity_agent()
    for sub_agent in agent.sub_agents:
        assert isinstance(sub_agent.model, str)
        assert sub_agent.model.startswith("gemini-")


def test_create_continuity_agent_calling_twice_avoids_shared_instances() -> None:
    first = create_continuity_agent()
    second = create_continuity_agent()
    assert first is not second
    assert first.sub_agents[0] is not second.sub_agents[0]
