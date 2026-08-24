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

"""Schreib-Pipeline-Geruest (TASK-008): Kontext -> Beat -> Figuren-Brief ->
Editor-Loop, als deterministischer `SequentialAgent` statt LLM-Delegation --
die Reihenfolge ist fest und soll nicht vom Modell entschieden werden.

**POST-WRITE-HOOK (TASK-012):** Nach einer final gespeicherten Szene
(`write_scene`, Grade "pass") schreibt `_update_timeline_and_character_state`
automatisch einen Timeline-Eintrag (`app/tools/timeline.py::append_event`)
und aktualisiert den kapitelweisen Zustand der beteiligten Figuren
(`app/tools/characters.py::update_character_state`). Die Extraktion ist in
diesem Plan bewusst deterministisch (Regex/Stichworterkennung), nicht
LLM-gestuetzt -- haelt den Hook offline fixture-testbar; wird "scharf
geschaltet" (echte, generierte Szenen statt Fixture) mit dem Scene Agent in
Plan 3.

**SZENEN-SLOT (Entscheidung E8):** In diesem Plan gibt es noch keinen Scene
Agent (kommt in `03-szenen-und-lokales-llm/TASK-003`). Statt Text zu
generieren, setzt `_SceneSlotFixture` `state["scene_draft"]` auf das
eingecheckte Fixture Szene E ("Das Protokoll der Sehnsucht",
`tests/fixtures/szene_e_protokoll_der_sehnsucht.md`) -- die einzige
ausformulierte Szene aus `basics.md`, mit beiden Registern (klinische
KI-Analyse, erzaehlende Figurenperspektive), ideal um Register-Checks und
Editor-Verdikt realistisch zu treiben. Plan 3/TASK-003 ersetzt
`_SceneSlotFixture` durch `create_scene_agent()` an genau dieser Stelle und
entfernt das Fixture wieder.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

from google.adk.agents import Agent, BaseAgent, LoopAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.tools import AgentTool

from app.agents.character_agent import create_character_agent
from app.agents.editor_agent import create_editor_agent
from app.agents.quality_checker import QualityChecker
from app.models.router import model_for
from app.tools.characters import update_character_state
from app.tools.context_loader import load_scene_context
from app.tools.manuscript import characters_mentioned, write_scene, write_scene_draft
from app.tools.timeline import append_event, extract_timestamp

_FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "szene_e_protokoll_der_sehnsucht.md"
)

_MAX_EDITOR_ITERATIONS = 3


def _create_context_loader_step() -> Agent:
    return Agent(
        name="context_loader_step",
        model=model_for("orchestrator"),
        description="Laedt den Szenenkontext fuer die aktive Kapitel/Szenen-Kombination.",
        instruction=(
            "Aktuelles Kapitel: {active_chapter}, aktuelle Szene: {active_scene}.\n"
            "Rufe load_scene_context mit diesen Werten auf. Antworte danach nur mit "
            "'Kontext geladen.' -- das Tool schreibt sein Ergebnis bereits selbst unter "
            "dem State-Key `scene_context` (siehe app/tools/context_loader.py), ein "
            "zusaetzliches `output_key` auf diesem Schritt wuerde diesen strukturierten "
            "Wert mit dem freien Bestaetigungstext ueberschreiben."
        ),
        tools=[load_scene_context],
    )


def _create_plot_beat_step() -> Agent:
    return Agent(
        name="plot_beat_step",
        model=model_for("plot"),
        description="Fasst den Beat fuer die aktuelle Szene aus dem geladenen Kontext zusammen.",
        instruction=(
            "Geladener Szenenkontext:\n{scene_context}\n\n"
            "Fasse daraus den Beat fuer diese Szene in 2-3 Saetzen zusammen: POV-Figur, was "
            "passiert, ist es ein Wendepunkt, Spannungslevel. Ist im Kontext kein Beat "
            "vorhanden (`beat` ist `None`), sag das explizit -- erfinde keinen eigenen Beat."
        ),
        output_key="scene_beat",
    )


def _create_character_brief_step() -> Agent:
    return Agent(
        name="character_brief_step",
        model=model_for("orchestrator"),
        description="Holt einen Figuren-Brief fuer die POV-Figur der aktuellen Szene.",
        instruction=(
            "Beat der aktuellen Szene:\n{scene_beat}\n\n"
            "Ermittle die POV-Figur aus dem Beat und konsultiere das character_agent-Tool "
            "fuer einen Figuren-Brief zu dieser Figur im Kontext dieser Szene. Ist keine "
            "POV-Figur bekannt, sag das explizit, statt eine zu erfinden."
        ),
        tools=[AgentTool(create_character_agent())],
        output_key="character_brief",
    )


class _SceneSlotFixture(BaseAgent):
    """SZENEN-SLOT (Entscheidung E8) -- Platzhalter fuer `create_scene_agent()`.

    Legt `state["scene_draft"]` auf das eingecheckte Fixture Szene E fest,
    statt Text zu generieren. Wird 1:1 durch `create_scene_agent()` ersetzt,
    sobald der Scene Agent existiert (Plan 3/TASK-003) -- diese Klasse und
    das Fixture verschwinden dann wieder.
    """

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        text = _FIXTURE_PATH.read_text(encoding="utf-8")
        yield Event(
            author=self.name,
            actions=EventActions(state_delta={"scene_draft": text}),
        )


_INFECTION_KEYWORDS = (
    ("compliance", "voll_compliant"),
    ("voll compliant", "voll_compliant"),
    ("infiziert", "infiziert"),
    ("infektion", "infiziert"),
    ("nicht optimiert", "nicht_optimiert"),
    ("unoptimiert", "nicht_optimiert"),
)


def _detect_infection_status(text: str) -> str:
    """Best-effort Stichwort-Erkennung, kein semantisches Verstehen.

    Deterministischer Platzhalter fuer die in der Task-Beschreibung
    vorgesehene LLM-gestuetzte Extraktion (siehe Modul-Docstring/Walkthrough
    TASK-012) -- reicht fuer Fixture-Tests, wird mit dem Scene Agent in
    Plan 3 durch eine belastbarere Extraktion ersetzt.
    """
    lowered = text.lower()
    for keyword, status in _INFECTION_KEYWORDS:
        if keyword in lowered:
            return status
    return ""


def _update_timeline_and_character_state(
    callback_context: CallbackContext, text: str
) -> None:
    """Post-Write-Schritt (TASK-012): traegt die geschriebene Szene in die
    Timeline ein und aktualisiert den kapitelweisen Zustand der beteiligten
    Figuren.

    Deterministische Extraktion (Regex-Uhrzeit, bekannte Figurennamen,
    Stichwort-Erkennung fuer den Infektionsstatus) statt LLM-Aufruf -- haelt
    den Hook offline testbar (Akzeptanzkriterium "pytest deckt
    Timeline-Validierung mit Fixtures ab") und deterministisch (Task-
    Beschreibung: "das Schreiben deterministisch ueber Tools"). Wird mit dem
    Scene Agent in Plan 3 durch eine LLM-gestuetzte Extraktion ergaenzt/
    ersetzt, sobald generierter statt Fixture-Text vorliegt (siehe
    Walkthrough TASK-012).
    """
    state = callback_context.state
    chapter = state.get("active_chapter", 1)
    scene = state.get("active_scene", 1)
    beat = (state.get("scene_context") or {}).get("beat") or {}
    characters = beat.get("characters_present") or characters_mentioned(text)
    location = beat.get("location", "")
    description = beat.get("beat", "") or " ".join(text.split())[:150]
    timestamp = extract_timestamp(text)
    infection_status = _detect_infection_status(text)

    append_event(
        chapter=chapter,
        scene=scene,
        timestamp=timestamp,
        location=location,
        description=description,
        characters=characters,
    )
    for name in characters:
        update_character_state(
            name=name,
            chapter=chapter,
            location=location,
            knowledge=description,
            emotional_state="",
            infection_status=infection_status,
        )


async def _persist_or_draft(callback_context: CallbackContext) -> None:
    """Nach dem Editor-Loop: finale Fassung via `write_scene`, sonst
    `.draft.md` mit Verdikt-Frontmatter -- nie stillschweigend als fertig
    markieren (Persistenz-Konvention, TASK-008). Bei finaler Fassung
    zusaetzlich Post-Write-Schritt fuer Timeline/Character-State (TASK-012)."""
    state = callback_context.state
    verdict = state.get("editor_verdict")
    chapter = state.get("active_chapter", 1)
    scene = state.get("active_scene", 1)

    if verdict and verdict.get("grade") == "pass":
        final_text = verdict.get("revised_text", "")
        write_scene(chapter=chapter, scene=scene, text=final_text)
        _update_timeline_and_character_state(callback_context, final_text)
        return

    draft_text = (verdict or {}).get("revised_text") or state.get("scene_draft", "")
    write_scene_draft(
        chapter=chapter, scene=scene, text=draft_text, verdict=verdict or {}
    )


def create_writing_pipeline() -> SequentialAgent:
    """Factory -- **aufrufen** (`create_writing_pipeline()`), nicht referenzieren."""
    editing_loop = LoopAgent(
        name="editing_loop",
        sub_agents=[create_editor_agent(), QualityChecker(name="quality_checker")],
        max_iterations=_MAX_EDITOR_ITERATIONS,
        after_agent_callback=_persist_or_draft,
    )
    return SequentialAgent(
        name="writing_pipeline",
        description=(
            "Deterministische Schreib-Pipeline: Kontext laden, Beat bestaetigen, "
            "Figuren-Brief holen, Szene (Fixture-Slot) lektorieren."
        ),
        sub_agents=[
            _create_context_loader_step(),
            _create_plot_beat_step(),
            _create_character_brief_step(),
            _SceneSlotFixture(name="scene_slot_fixture"),
            editing_loop,
        ],
    )
