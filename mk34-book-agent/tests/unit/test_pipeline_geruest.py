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

"""Unit tests for `app/pipelines/writing.py` (TASK-008, Szenen-Schritt scharf
geschaltet in Plan 3/TASK-003, Content-Klassifikation/Routing in TASK-004).

Structure, Szenen-/Kontinuitaets-/Classifier-Slot-Position, die aktive-Szene-
und Override-Extraktion sowie der Persistenz-/Continuity-/Routing-Callback
sind direkt getestet; der volle End-to-End-Lauf (Classifier -> Scene Agent
-> Continuity -> Editor-Loop -> Persistenz) gegen die echte Gemini-API ist
separat per `agents-cli run`/`InMemoryRunner` verifiziert -- siehe
TASK-003/004-Walkthroughs.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from google.adk.agents import BaseAgent, LoopAgent
from pydantic import Field

from app.agents.quality_checker import QualityChecker
from app.pipelines.writing import (
    _apply_route_decision,
    _apply_route_override_from_user_message,
    _ContinuityGate,
    _detect_infection_status,
    _persist_or_draft,
    _RoutedSceneStep,
    _set_active_scene_from_user_message,
    _update_timeline_and_character_state,
    create_writing_pipeline,
)


def test_pipeline_has_seven_steps_in_order() -> None:
    pipeline = create_writing_pipeline()
    names = [a.name for a in pipeline.sub_agents]
    assert names == [
        "context_loader_step",
        "plot_beat_step",
        "character_brief_step",
        "classifier_agent",
        "scene_agent_step",
        "continuity_agent",
        "continuity_gate",
    ]


def test_classifier_step_is_at_fixed_position_three() -> None:
    pipeline = create_writing_pipeline()
    slot = pipeline.sub_agents[3]
    assert slot.name == "classifier_agent"
    assert slot.output_key == "route_decision"
    assert slot.after_agent_callback is _apply_route_decision


def test_scene_agent_step_is_a_routed_scene_step() -> None:
    """Fixiert die Slot-Position aus Entscheidung E8 (Plan 2/TASK-008) --
    `_RoutedSceneStep` ersetzt den statischen `create_scene_agent()`-Aufruf
    aus TASK-003, um `state["route"]` (TASK-004) pro Turn neu aufzuloesen."""
    pipeline = create_writing_pipeline()
    slot = pipeline.sub_agents[4]
    assert isinstance(slot, _RoutedSceneStep)
    assert slot.name == "scene_agent_step"


def test_continuity_agent_runs_before_the_continuity_gate() -> None:
    pipeline = create_writing_pipeline()
    assert pipeline.sub_agents[5].name == "continuity_agent"
    assert isinstance(pipeline.sub_agents[6], _ContinuityGate)


def test_continuity_gate_wraps_editing_loop() -> None:
    pipeline = create_writing_pipeline()
    gate = pipeline.sub_agents[6]
    assert isinstance(gate, _ContinuityGate)
    editing_loop = gate.sub_agents[0]
    assert isinstance(editing_loop, LoopAgent)
    assert editing_loop.max_iterations == 3
    sub_names = [a.name for a in editing_loop.sub_agents]
    assert sub_names == ["editor_agent", "quality_checker"]
    assert isinstance(editing_loop.sub_agents[1], QualityChecker)


def test_pipeline_has_active_scene_and_override_extraction_callbacks() -> None:
    pipeline = create_writing_pipeline()
    assert pipeline.before_agent_callback == [
        _set_active_scene_from_user_message,
        _apply_route_override_from_user_message,
    ]


def test_context_loader_step_has_no_output_key() -> None:
    """load_scene_context schreibt seinen State-Eintrag bereits selbst
    (TASK-002) -- ein output_key hier wuerde ihn mit dem freien
    Bestaetigungstext des Agenten ueberschreiben."""
    pipeline = create_writing_pipeline()
    context_step = pipeline.sub_agents[0]
    assert context_step.output_key is None


def test_create_writing_pipeline_calling_twice_avoids_shared_instances() -> None:
    assert create_writing_pipeline() is not create_writing_pipeline()


# --- _set_active_scene_from_user_message (TASK-003) -----------------------------


class _FakeUserContent:
    def __init__(self, text: str):
        self.parts = [SimpleNamespace(text=text)]


class _FakeCallbackContext:
    def __init__(self, state: dict, user_text: str | None = None):
        self.state = state
        self.user_content = _FakeUserContent(user_text) if user_text else None


def test_set_active_scene_extracts_chapter_and_scene() -> None:
    ctx = _FakeCallbackContext({}, user_text="Schreibe Kapitel 3, Szene 2.")
    _set_active_scene_from_user_message(ctx)
    assert ctx.state["active_chapter"] == 3
    assert ctx.state["active_scene"] == 2


def test_set_active_scene_is_case_insensitive_and_tolerates_missing_comma() -> None:
    ctx = _FakeCallbackContext({}, user_text="schreibe kapitel 12 szene 7 bitte")
    _set_active_scene_from_user_message(ctx)
    assert ctx.state["active_chapter"] == 12
    assert ctx.state["active_scene"] == 7


def test_set_active_scene_leaves_state_untouched_without_match() -> None:
    ctx = _FakeCallbackContext(
        {"active_chapter": 1, "active_scene": 1},
        user_text="Schreibe die naechste Szene.",
    )
    _set_active_scene_from_user_message(ctx)
    assert ctx.state == {"active_chapter": 1, "active_scene": 1}


def test_set_active_scene_handles_missing_user_content() -> None:
    ctx = _FakeCallbackContext({"active_chapter": 1, "active_scene": 1})
    _set_active_scene_from_user_message(ctx)  # must not raise
    assert ctx.state == {"active_chapter": 1, "active_scene": 1}


# --- _apply_route_override_from_user_message (TASK-004) -----------------------


def test_route_override_detects_flag_local() -> None:
    ctx = _FakeCallbackContext({}, user_text="Schreibe die Szene. --model local")
    _apply_route_override_from_user_message(ctx)
    assert ctx.state["route_override"] == "local"


def test_route_override_detects_flag_cloud() -> None:
    ctx = _FakeCallbackContext({}, user_text="Schreibe die Szene. --model cloud")
    _apply_route_override_from_user_message(ctx)
    assert ctx.state["route_override"] == "cloud"


def test_route_override_detects_natural_language_local() -> None:
    ctx = _FakeCallbackContext({}, user_text="Bitte schreibe das lokal.")
    _apply_route_override_from_user_message(ctx)
    assert ctx.state["route_override"] == "local"


def test_route_override_detects_natural_language_cloud() -> None:
    ctx = _FakeCallbackContext({}, user_text="Schreibe das in der Cloud.")
    _apply_route_override_from_user_message(ctx)
    assert ctx.state["route_override"] == "cloud"


def test_route_override_absent_without_match() -> None:
    ctx = _FakeCallbackContext({}, user_text="Schreibe Kapitel 3, Szene 2.")
    _apply_route_override_from_user_message(ctx)
    assert "route_override" not in ctx.state


def test_route_override_handles_missing_user_content() -> None:
    ctx = _FakeCallbackContext({})
    _apply_route_override_from_user_message(ctx)  # must not raise
    assert "route_override" not in ctx.state


# --- _apply_route_decision (TASK-004) ------------------------------------------


@pytest.mark.asyncio
async def test_apply_route_decision_uses_classifier_result_without_override() -> None:
    ctx = _FakeCallbackContext(
        {
            "route_decision": {
                "route": "local",
                "reason": "Koerperhorror",
                "confidence": 0.9,
            }
        }
    )
    await _apply_route_decision(ctx)
    assert ctx.state["route"] == "local"


@pytest.mark.asyncio
async def test_apply_route_decision_override_beats_classifier() -> None:
    ctx = _FakeCallbackContext(
        {
            "route_override": "local",
            "route_decision": {
                "route": "cloud",
                "reason": "Boardroom",
                "confidence": 0.8,
            },
        }
    )
    await _apply_route_decision(ctx)
    assert ctx.state["route"] == "local"


@pytest.mark.asyncio
async def test_apply_route_decision_defaults_to_cloud_without_decision() -> None:
    ctx = _FakeCallbackContext({})
    await _apply_route_decision(ctx)
    assert ctx.state["route"] == "cloud"


# --- _RoutedSceneStep (TASK-004) ------------------------------------------------


@pytest.mark.asyncio
async def test_routed_scene_step_builds_scene_agent_with_current_route(
    monkeypatch,
) -> None:
    captured_routes = []

    class _FakeSceneAgent:
        async def run_async(self, ctx):
            return
            yield  # pragma: no cover

    def _fake_create_scene_agent(route=None):
        captured_routes.append(route)
        return _FakeSceneAgent()

    monkeypatch.setattr(
        "app.pipelines.writing.create_scene_agent", _fake_create_scene_agent
    )
    step = _RoutedSceneStep(name="scene_agent_step")
    ctx = _FakeInvocationContext({"route": "local"})

    events = [event async for event in step._run_async_impl(ctx)]

    assert captured_routes == ["local"]
    assert events == []


@pytest.mark.asyncio
async def test_routed_scene_step_defaults_route_to_none_without_state(
    monkeypatch,
) -> None:
    captured_routes = []

    class _FakeSceneAgent:
        async def run_async(self, ctx):
            return
            yield  # pragma: no cover

    def _fake_create_scene_agent(route=None):
        captured_routes.append(route)
        return _FakeSceneAgent()

    monkeypatch.setattr(
        "app.pipelines.writing.create_scene_agent", _fake_create_scene_agent
    )
    step = _RoutedSceneStep(name="scene_agent_step")
    ctx = _FakeInvocationContext({})

    [event async for event in step._run_async_impl(ctx)]

    assert captured_routes == [None]


# --- _ContinuityGate (TASK-003) --------------------------------------------------


class _FakeSession:
    def __init__(self, state: dict):
        self.state = state


class _FakeInvocationContext:
    def __init__(self, state: dict):
        self.session = _FakeSession(state)


class _RecordingEditingLoop(BaseAgent):
    """Minimaler `BaseAgent`-Stand-in fuer den echten `LoopAgent` -- ein
    echter `BaseAgent`, damit `_ContinuityGate`s `sub_agents`-Feld (Pydantic,
    erwartet `BaseAgent`-Instanzen) ihn akzeptiert. `run_async` (die von
    `_ContinuityGate` tatsaechlich aufgerufene *public* Methode, nicht
    `_run_async_impl`) wird in jedem Test per `monkeypatch` durch einen
    zaehlenden Fake ersetzt -- die echte `run_async`-Implementierung baut
    intern einen vollen ADK-`InvocationContext` auf (`model_copy`, Branch-
    Handling), den in einem reinen Logik-Unit-Test nachzubilden unnoetigen
    Aufwand waere; das volle Zusammenspiel ist per `InMemoryRunner` verifiziert
    (siehe TASK-003-Walkthrough)."""

    run_count: int = Field(default=0)

    async def _run_async_impl(self, ctx):
        self.run_count += 1
        return
        yield  # pragma: no cover -- macht die Methode zu einem Async-Generator


def _patch_run_async_to_count(monkeypatch, agent: _RecordingEditingLoop) -> None:
    # Pydantic-Modelle (ADKs `BaseAgent`) verbieten das Ueberschreiben einer
    # geerbten Methode auf Instanzebene (`__setattr__` prueft deklarierte
    # Felder) -- deshalb hier auf Klassenebene patchen, `monkeypatch` macht
    # das test-lokal rueckgaengig.
    async def _fake_run_async(self, ctx):
        self.run_count += 1
        return
        yield  # pragma: no cover -- macht die Methode zu einem Async-Generator

    monkeypatch.setattr(_RecordingEditingLoop, "run_async", _fake_run_async)


@pytest.mark.asyncio
async def test_continuity_gate_delegates_to_editing_loop_without_high_severity(
    monkeypatch,
) -> None:
    fake_loop = _RecordingEditingLoop(name="fake_editing_loop")
    _patch_run_async_to_count(monkeypatch, fake_loop)
    gate = _ContinuityGate(name="continuity_gate", sub_agents=[fake_loop])
    ctx = _FakeInvocationContext(
        {"continuity_report": {"conflicts": [{"severity": "low"}]}}
    )

    events = [event async for event in gate._run_async_impl(ctx)]

    assert fake_loop.run_count == 1
    assert events == []


@pytest.mark.asyncio
async def test_continuity_gate_blocks_writing_on_high_severity_conflict(
    monkeypatch,
) -> None:
    fake_loop = _RecordingEditingLoop(name="fake_editing_loop")
    gate = _ContinuityGate(name="continuity_gate", sub_agents=[fake_loop])
    draft_calls = []
    monkeypatch.setattr(
        "app.pipelines.writing.write_scene_draft",
        lambda **kwargs: draft_calls.append(kwargs),
    )
    ctx = _FakeInvocationContext(
        {
            "active_chapter": 2,
            "active_scene": 5,
            "scene_draft": "Rohfassung mit Konflikt.",
            "continuity_report": {
                "conflicts": [
                    {
                        "type": "Wissen zu frueh",
                        "evidence": "David nennt die Keimbahn-Mutation.",
                        "reference": "Kapitel 4, Szene 1",
                        "severity": "high",
                    }
                ]
            },
        }
    )

    events = [event async for event in gate._run_async_impl(ctx)]

    assert fake_loop.run_count == 0  # Editor-Loop wurde NICHT gestartet
    assert len(draft_calls) == 1
    assert draft_calls[0]["chapter"] == 2
    assert draft_calls[0]["scene"] == 5
    assert draft_calls[0]["verdict"]["grade"] == "continuity_conflict"
    assert "Wissen zu frueh" in draft_calls[0]["verdict"]["issues"][0]

    assert len(events) == 1
    response_text = events[0].content.parts[0].text
    assert response_text is not None
    assert "NICHT gespeichert" in response_text
    assert "Kapitel 4, Szene 1" in response_text


@pytest.mark.asyncio
async def test_continuity_gate_ignores_low_and_medium_severity(monkeypatch) -> None:
    fake_loop = _RecordingEditingLoop(name="fake_editing_loop")
    _patch_run_async_to_count(monkeypatch, fake_loop)
    gate = _ContinuityGate(name="continuity_gate", sub_agents=[fake_loop])
    ctx = _FakeInvocationContext(
        {
            "continuity_report": {
                "conflicts": [{"severity": "low"}, {"severity": "medium"}]
            }
        }
    )

    events = [event async for event in gate._run_async_impl(ctx)]

    assert fake_loop.run_count == 1
    assert events == []


@pytest.mark.asyncio
async def test_continuity_gate_handles_missing_report(monkeypatch) -> None:
    fake_loop = _RecordingEditingLoop(name="fake_editing_loop")
    _patch_run_async_to_count(monkeypatch, fake_loop)
    gate = _ContinuityGate(name="continuity_gate", sub_agents=[fake_loop])
    ctx = _FakeInvocationContext({})

    events = [event async for event in gate._run_async_impl(ctx)]

    assert fake_loop.run_count == 1
    assert events == []


# --- _persist_or_draft ----------------------------------------------------------


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
