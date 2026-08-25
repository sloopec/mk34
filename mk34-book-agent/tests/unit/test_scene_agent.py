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

"""Unit tests for `app/agents/scene_agent.py` (Plan 3, TASK-002/004).

Structure/logic only, no live LLM call -- see the TASK-002/003/004
walkthroughs for the live `InMemoryRunner`/`agents-cli run` smoke tests.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.agents.scene_agent import _log_refusal_if_detected, create_scene_agent
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


def test_create_scene_agent_has_no_before_model_callback() -> None:
    """Bewusste Projektentscheidung: keine Safety-Guardrails auf dem Scene
    Agent (Kern-Use-Case, unzensierte Szenen). `after_model_callback` ist
    gesetzt (`_log_refusal_if_detected`, TASK-004/E9), aber kein Guardrail --
    sie blockiert/veraendert nie eine Antwort, siehe eigener Test unten."""
    agent = create_scene_agent()
    assert agent.before_model_callback is None
    assert agent.after_model_callback is _log_refusal_if_detected


def test_create_scene_agent_calling_twice_avoids_shared_instances() -> None:
    assert create_scene_agent() is not create_scene_agent()


def test_create_scene_agent_name_and_description() -> None:
    agent = create_scene_agent()
    assert agent.name == "scene_agent"
    assert "Szene" in agent.description


# --- TASK-004: route-Parameter ------------------------------------------------


def test_create_scene_agent_accepts_route_none_defaults_to_cloud() -> None:
    agent = create_scene_agent(route=None)
    assert isinstance(agent.model, str)
    assert agent.model.startswith("gemini-")


def test_create_scene_agent_accepts_route_cloud_explicitly() -> None:
    agent = create_scene_agent(route="cloud")
    assert isinstance(agent.model, str)
    assert agent.model.startswith("gemini-")


# --- TASK-004: _log_refusal_if_detected (Entscheidung E9) ---------------------


class _FakeCallbackContext:
    def __init__(self, state: dict):
        self.state = state


@pytest.mark.asyncio
async def test_log_refusal_if_detected_returns_none_always() -> None:
    """Rein beobachtend -- niemals ein Guardrail, unabhaengig vom Ergebnis."""
    ctx = _FakeCallbackContext({"route": "cloud"})
    refusal_response = SimpleNamespace(finish_reason=SimpleNamespace(name="SAFETY"))
    normal_response = SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))

    assert await _log_refusal_if_detected(ctx, refusal_response) is None
    assert await _log_refusal_if_detected(ctx, normal_response) is None


@pytest.mark.asyncio
async def test_log_refusal_if_detected_logs_on_refusal(caplog) -> None:
    import logging

    ctx = _FakeCallbackContext(
        {"route": "cloud", "active_chapter": 2, "active_scene": 5}
    )
    refusal_response = SimpleNamespace(finish_reason=SimpleNamespace(name="SAFETY"))

    with caplog.at_level(logging.WARNING, logger="app.agents.scene_agent"):
        await _log_refusal_if_detected(ctx, refusal_response)

    assert "Cloud-Refusal erkannt" in caplog.text


@pytest.mark.asyncio
async def test_log_refusal_if_detected_silent_on_normal_response(caplog) -> None:
    import logging

    ctx = _FakeCallbackContext({"route": "cloud"})
    normal_response = SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))

    with caplog.at_level(logging.WARNING, logger="app.agents.scene_agent"):
        await _log_refusal_if_detected(ctx, normal_response)

    assert "Cloud-Refusal erkannt" not in caplog.text
