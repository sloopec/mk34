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

"""Unit tests for `app/agents/scene_agent.py` (Plan 3, TASK-002).

Structure/logic only, no live LLM call -- see the TASK-002 walkthrough for
the live `InMemoryRunner` smoke test.
"""

from __future__ import annotations

from app.agents.scene_agent import create_scene_agent
from app.tools.context_loader import load_scene_context
from app.tools.manuscript import read_manuscript, write_scene


def test_create_scene_agent_uses_scene_model() -> None:
    agent = create_scene_agent()
    assert isinstance(agent.model, str)
    assert agent.model.startswith("gemini-")


def test_create_scene_agent_has_expected_tools() -> None:
    agent = create_scene_agent()
    assert agent.tools == [read_manuscript, write_scene, load_scene_context]


def test_create_scene_agent_output_key_is_scene_draft() -> None:
    agent = create_scene_agent()
    assert agent.output_key == "scene_draft"


def test_create_scene_agent_has_no_safety_callbacks() -> None:
    """Bewusste Projektentscheidung: keine Safety-Guardrails auf dem Scene
    Agent (Kern-Use-Case, unzensierte Szenen)."""
    agent = create_scene_agent()
    assert agent.before_model_callback is None
    assert agent.after_model_callback is None


def test_create_scene_agent_calling_twice_avoids_shared_instances() -> None:
    assert create_scene_agent() is not create_scene_agent()


def test_create_scene_agent_name_and_description() -> None:
    agent = create_scene_agent()
    assert agent.name == "scene_agent"
    assert "Szene" in agent.description
