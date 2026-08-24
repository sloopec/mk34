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

"""Unit tests for `app/agents/character_agent.py` -- structure only, no live
LLM call (see TASK-005 walkthrough for the live `AgentTool` smoke test)."""

from __future__ import annotations

from app.agents.character_agent import create_character_agent


def test_create_character_agent_has_all_four_tools() -> None:
    agent = create_character_agent()
    tool_names = {getattr(t, "__name__", getattr(t, "name", None)) for t in agent.tools}
    assert tool_names == {
        "get_character",
        "get_character_arc",
        "get_knowledge_state",
        "update_character",
    }


def test_create_character_agent_uses_character_model() -> None:
    agent = create_character_agent()
    assert isinstance(agent.model, str)
    assert agent.model.startswith("gemini-")


def test_create_character_agent_calling_twice_avoids_shared_instances() -> None:
    first = create_character_agent()
    second = create_character_agent()
    assert first is not second
