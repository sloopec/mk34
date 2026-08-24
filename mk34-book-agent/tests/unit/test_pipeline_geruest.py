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

"""Unit tests for `app/pipelines/writing.py` (TASK-008).

Structure, Szenen-Slot-Position and the persistence callback are asserted
directly; the live end-to-end run (Fixture -> Editor-Loop -> Persistenz) is
verified separately via `InMemoryRunner` against the real Gemini API --
siehe TASK-008-Walkthrough.
"""

from __future__ import annotations

import pytest
from google.adk.agents import LoopAgent

from app.agents.quality_checker import QualityChecker
from app.pipelines.writing import (
    _detect_infection_status,
    _persist_or_draft,
    _SceneSlotFixture,
    _update_timeline_and_character_state,
    create_writing_pipeline,
)


def test_pipeline_has_five_steps_in_order() -> None:
    pipeline = create_writing_pipeline()
    names = [a.name for a in pipeline.sub_agents]
    assert names == [
        "context_loader_step",
        "plot_beat_step",
        "character_brief_step",
        "scene_slot_fixture",
        "editing_loop",
    ]


def test_scene_slot_is_at_fixed_position_four() -> None:
    """Fixiert die Slot-Position, damit Plan 3/TASK-003 `_SceneSlotFixture`
    eindeutig durch `create_scene_agent()` ersetzen kann."""
    pipeline = create_writing_pipeline()
    slot = pipeline.sub_agents[3]
    assert isinstance(slot, _SceneSlotFixture)
    assert slot.name == "scene_slot_fixture"


def test_editing_loop_wraps_editor_and_quality_checker_with_max_three_iterations() -> (
    None
):
    pipeline = create_writing_pipeline()
    loop = pipeline.sub_agents[4]
    assert isinstance(loop, LoopAgent)
    assert loop.max_iterations == 3
    sub_names = [a.name for a in loop.sub_agents]
    assert sub_names == ["editor_agent", "quality_checker"]
    assert isinstance(loop.sub_agents[1], QualityChecker)


def test_context_loader_step_has_no_output_key() -> None:
    """load_scene_context schreibt seinen State-Eintrag bereits selbst
    (TASK-002) -- ein output_key hier wuerde ihn mit dem freien
    Bestaetigungstext des Agenten ueberschreiben."""
    pipeline = create_writing_pipeline()
    context_step = pipeline.sub_agents[0]
    assert context_step.output_key is None


def test_create_writing_pipeline_calling_twice_avoids_shared_instances() -> None:
    assert create_writing_pipeline() is not create_writing_pipeline()


# --- _persist_or_draft ----------------------------------------------------------


class _FakeCallbackContext:
    def __init__(self, state: dict):
        self.state = state


@pytest.mark.asyncio
async def test_persist_or_draft_writes_final_scene_on_pass(monkeypatch) -> None:
    written = []
    monkeypatch.setattr(
        "app.pipelines.writing.write_scene",
        lambda **kwargs: written.append(("final", kwargs)),
    )
    monkeypatch.setattr(
        "app.pipelines.writing.write_scene_draft",
        lambda **kwargs: written.append(("draft", kwargs)),
    )
    # TASK-012: the post-write hook must not touch the real store during
    # this structural test -- isolate it explicitly.
    monkeypatch.setattr("app.pipelines.writing.append_event", lambda **kwargs: None)
    monkeypatch.setattr(
        "app.pipelines.writing.update_character_state", lambda **kwargs: None
    )
    ctx = _FakeCallbackContext(
        {
            "active_chapter": 5,
            "active_scene": 1,
            "editor_verdict": {"grade": "pass", "revised_text": "Fertige Szene."},
        }
    )

    await _persist_or_draft(ctx)

    assert len(written) == 1
    kind, kwargs = written[0]
    assert kind == "final"
    assert kwargs["chapter"] == 5
    assert kwargs["text"] == "Fertige Szene."


@pytest.mark.asyncio
async def test_persist_or_draft_calls_post_write_hook_on_pass(monkeypatch) -> None:
    monkeypatch.setattr("app.pipelines.writing.write_scene", lambda **kwargs: None)
    hook_calls = []
    monkeypatch.setattr(
        "app.pipelines.writing._update_timeline_and_character_state",
        lambda ctx, text: hook_calls.append(text),
    )
    ctx = _FakeCallbackContext(
        {
            "active_chapter": 5,
            "active_scene": 1,
            "editor_verdict": {"grade": "pass", "revised_text": "Fertige Szene."},
        }
    )

    await _persist_or_draft(ctx)

    assert hook_calls == ["Fertige Szene."]


@pytest.mark.asyncio
async def test_persist_or_draft_skips_post_write_hook_when_not_pass(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.pipelines.writing.write_scene_draft", lambda **kwargs: None
    )
    hook_calls = []
    monkeypatch.setattr(
        "app.pipelines.writing._update_timeline_and_character_state",
        lambda ctx, text: hook_calls.append(text),
    )
    ctx = _FakeCallbackContext(
        {
            "active_chapter": 5,
            "active_scene": 1,
            "editor_verdict": {"grade": "needs_revision", "revised_text": "Entwurf."},
        }
    )

    await _persist_or_draft(ctx)

    assert hook_calls == []


@pytest.mark.asyncio
async def test_persist_or_draft_writes_draft_when_not_pass(monkeypatch) -> None:
    written = []
    monkeypatch.setattr(
        "app.pipelines.writing.write_scene",
        lambda **kwargs: written.append(("final", kwargs)),
    )
    monkeypatch.setattr(
        "app.pipelines.writing.write_scene_draft",
        lambda **kwargs: written.append(("draft", kwargs)),
    )
    ctx = _FakeCallbackContext(
        {
            "active_chapter": 5,
            "active_scene": 1,
            "editor_verdict": {
                "grade": "needs_revision",
                "issues": ["Register"],
                "revised_text": "Noch nicht fertig.",
            },
        }
    )

    await _persist_or_draft(ctx)

    assert len(written) == 1
    kind, kwargs = written[0]
    assert kind == "draft"
    assert kwargs["verdict"]["grade"] == "needs_revision"


@pytest.mark.asyncio
async def test_persist_or_draft_writes_draft_when_no_verdict_yet(monkeypatch) -> None:
    written = []
    monkeypatch.setattr(
        "app.pipelines.writing.write_scene",
        lambda **kwargs: written.append(("final", kwargs)),
    )
    monkeypatch.setattr(
        "app.pipelines.writing.write_scene_draft",
        lambda **kwargs: written.append(("draft", kwargs)),
    )
    ctx = _FakeCallbackContext(
        {"active_chapter": 1, "active_scene": 1, "scene_draft": "Rohfassung."}
    )

    await _persist_or_draft(ctx)

    assert len(written) == 1
    kind, kwargs = written[0]
    assert kind == "draft"
    assert kwargs["text"] == "Rohfassung."


# --- _update_timeline_and_character_state / _detect_infection_status (TASK-012) --------


def test_detect_infection_status_finds_compliance() -> None:
    assert (
        _detect_infection_status("Volle Compliance trotz Ablehnung.")
        == "voll_compliant"
    )


def test_detect_infection_status_finds_infiziert() -> None:
    assert _detect_infection_status("Sie ist infiziert.") == "infiziert"


def test_detect_infection_status_finds_nicht_optimiert() -> None:
    assert _detect_infection_status("Er ist noch nicht optimiert.") == "nicht_optimiert"


def test_detect_infection_status_empty_when_no_keyword() -> None:
    assert _detect_infection_status("Ein ganz normaler Satz.") == ""


def test_update_timeline_and_character_state_uses_beat_metadata(monkeypatch) -> None:
    append_calls = []
    state_calls = []
    monkeypatch.setattr(
        "app.pipelines.writing.append_event",
        lambda **kwargs: append_calls.append(kwargs),
    )
    monkeypatch.setattr(
        "app.pipelines.writing.update_character_state",
        lambda **kwargs: state_calls.append(kwargs),
    )
    ctx = _FakeCallbackContext(
        {
            "active_chapter": 3,
            "active_scene": 1,
            "scene_context": {
                "beat": {
                    "pov_character": "David",
                    "location": "Kommune",
                    "characters_present": ["David", "Dr. Sarah Lin"],
                    "beat": "David erreicht die Kommune.",
                }
            },
        }
    )

    _update_timeline_and_character_state(ctx, "20:43 Uhr | David kommt an.")

    assert len(append_calls) == 1
    event = append_calls[0]
    assert event["chapter"] == 3
    assert event["scene"] == 1
    assert event["timestamp"] == "20:43 Uhr"
    assert event["location"] == "Kommune"
    assert event["characters"] == ["David", "Dr. Sarah Lin"]

    assert len(state_calls) == 2
    names = {call["name"] for call in state_calls}
    assert names == {"David", "Dr. Sarah Lin"}
    for call in state_calls:
        assert call["chapter"] == 3
        assert call["location"] == "Kommune"


def test_update_timeline_and_character_state_falls_back_without_beat(
    monkeypatch,
) -> None:
    append_calls = []
    monkeypatch.setattr(
        "app.pipelines.writing.append_event",
        lambda **kwargs: append_calls.append(kwargs),
    )
    monkeypatch.setattr(
        "app.pipelines.writing.update_character_state", lambda **kwargs: None
    )
    monkeypatch.setattr(
        "app.pipelines.writing.characters_mentioned", lambda text: ["David"]
    )
    ctx = _FakeCallbackContext({"active_chapter": 1, "active_scene": 1})

    _update_timeline_and_character_state(ctx, "Ein Text ohne Beat-Metadaten.")

    assert append_calls[0]["characters"] == ["David"]
    assert append_calls[0]["location"] == ""
