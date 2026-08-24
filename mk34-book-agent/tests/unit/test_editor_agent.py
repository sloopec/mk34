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

"""Unit tests for `app/agents/editor_agent.py` and `quality_checker.py`.

Structure/logic only, no live LLM call (see TASK-006 walkthrough for the
live register-violation smoke test).
"""

from __future__ import annotations

import pytest

from app.agents.editor_agent import create_editor_agent
from app.agents.quality_checker import QualityChecker
from app.schemas import EditorVerdict

# --- editor_agent structure ---------------------------------------------------


def test_create_editor_agent_uses_output_schema_and_no_tools() -> None:
    agent = create_editor_agent()
    assert agent.output_schema is EditorVerdict
    assert agent.output_key == "editor_verdict"
    assert not agent.tools


def test_create_editor_agent_uses_editor_model() -> None:
    agent = create_editor_agent()
    assert isinstance(agent.model, str)
    assert agent.model.startswith("gemini-")


def test_create_editor_agent_calling_twice_avoids_shared_instances() -> None:
    assert create_editor_agent() is not create_editor_agent()


# --- QualityChecker escalation logic --------------------------------------------


class _FakeSession:
    def __init__(self, state: dict):
        self.state = state


class _FakeInvocationContext:
    def __init__(self, state: dict):
        self.session = _FakeSession(state)


@pytest.mark.asyncio
async def test_quality_checker_escalates_on_pass() -> None:
    checker = QualityChecker(name="quality_checker")
    ctx = _FakeInvocationContext({"editor_verdict": {"grade": "pass", "issues": []}})

    events = [event async for event in checker._run_async_impl(ctx)]

    assert len(events) == 1
    assert events[0].actions.escalate is True


@pytest.mark.asyncio
async def test_quality_checker_does_not_escalate_on_needs_revision() -> None:
    checker = QualityChecker(name="quality_checker")
    ctx = _FakeInvocationContext(
        {"editor_verdict": {"grade": "needs_revision", "issues": ["Registerbruch"]}}
    )

    events = [event async for event in checker._run_async_impl(ctx)]

    assert len(events) == 1
    assert not events[0].actions.escalate


@pytest.mark.asyncio
async def test_quality_checker_does_not_escalate_when_no_verdict_yet() -> None:
    checker = QualityChecker(name="quality_checker")
    ctx = _FakeInvocationContext({})

    events = [event async for event in checker._run_async_impl(ctx)]

    assert len(events) == 1
    assert not events[0].actions.escalate
