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

"""Unit tests for `app/agents/classifier_agent.py` (Plan 3, TASK-004).

Structure/logic only, no live LLM call -- see the TASK-004 walkthrough for
the live `agents-cli run` smoke test.
"""

from __future__ import annotations

from app.agents.classifier_agent import create_classifier_agent
from app.schemas import RouteDecision


def test_create_classifier_agent_uses_lite_tier_model() -> None:
    agent = create_classifier_agent()
    assert isinstance(agent.model, str)
    assert agent.model.startswith("gemini-")


def test_create_classifier_agent_uses_output_schema_and_no_tools() -> None:
    agent = create_classifier_agent()
    assert agent.output_schema is RouteDecision
    assert agent.output_key == "route_decision"
    assert not agent.tools


def test_create_classifier_agent_calling_twice_avoids_shared_instances() -> None:
    assert create_classifier_agent() is not create_classifier_agent()


def test_create_classifier_agent_name_and_description() -> None:
    agent = create_classifier_agent()
    assert agent.name == "classifier_agent"
    assert "lokal" in agent.description.lower()
