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

"""Schreib-Pipeline (TASK-008, Szenen-Schritt scharf geschaltet in Plan 3/
TASK-003): Kontext -> Beat -> Figuren-Brief -> Szene -> Kontinuitaetspruefung
-> Editor-Loop, als deterministischer `SequentialAgent` statt LLM-Delegation
-- die Reihenfolge ist fest und soll nicht vom Modell entschieden werden.

**POST-WRITE-HOOK (TASK-012, scharf geschaltet in Plan 3/TASK-003):** Nach
einer final gespeicherten Szene (`write_scene`, Grade "pass") schreibt
`_update_timeline_and_character_state` automatisch einen Timeline-Eintrag
(`app/tools/timeline.py::append_event`) und aktualisiert den kapitelweisen
Zustand der beteiligten Figuren (`app/tools/characters.py::update_character_state`).
Die Extraktion ist bewusst deterministisch (Regex/Stichworterkennung), nicht
LLM-gestuetzt -- haelt den Hook offline testbar. Ab diesem Task laeuft er auf
echten, vom Scene Agent generierten Szenen statt auf dem Plan-2-Fixture.

**SZENEN-SLOT (Plan 3, TASK-003):** `create_scene_agent()`
(`app/agents/scene_agent.py`, TASK-002) ersetzt das Plan-2-Fixture
`_SceneSlotFixture` an genau der dort dokumentierten Slot-Position
(Entscheidung E8) -- das Fixture und die zugehoerige Fixture-Datei-Referenz
sind entfernt.

**KONTINUITAETS-PRUEFUNG (Plan 2/TASK-011, in die Pipeline eingehaengt in
Plan 3/TASK-003):** `create_continuity_agent()` laeuft direkt als
SequentialAgent-Schritt (nicht als `AgentTool`, siehe Design-Entscheidung im
TASK-003-Walkthrough) nach dem Scene Agent -- er liest `{scene_draft}`,
`{scene_beat}`, `{character_brief}`, `{active_chapter}` bereits aus dem von
den vorherigen Schritten gesetzten State und schreibt sein Ergebnis nach
`state["continuity_report"]` (`output_schema=ContinuityReport`, also ein
`dict` mit `conflicts: [...]`). `_ContinuityGate` wertet das aus: findet sich
ein Konflikt mit `severity: "high"`, wird der (teure) Editor-Loop gar nicht
erst gestartet -- die Szene wird NICHT gespeichert, sondern als
Konflikt-Entwurf abgelegt, die Konfliktliste wird als Turn-Antwort
ausgegeben.

**AKTIVE SZENE AUS DER USER-NACHRICHT (Plan 3, TASK-003):** Der Orchestrator
delegiert bei "Schreibe Kapitel N, Szene M" den gesamten Turn an
`writing_pipeline` (Sub-Agent-Transfer, siehe `app/agent.py`) -- die
Kapitel-/Szenennummer muss danach aus der User-Nachricht selbst extrahiert
werden, bevor `context_loader_step` `{active_chapter}`/`{active_scene}`
liest. `_set_active_scene_from_user_message` (deterministischer Regex,
analog zu `extract_timestamp`/`_detect_infection_status`) uebernimmt das als
`before_agent_callback` der Pipeline; ohne Treffer bleiben die von
`app/callbacks.py::initialize_state` gesetzten Defaults (Kapitel/Szene 1)
unveraendert.
"""

from __future__ import annotations

import re
from collections.abc import AsyncGenerator

from google.adk.agents import Agent, BaseAgent, LoopAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.tools import AgentTool
from google.genai import types

from app.agents.character_agent import create_character_agent
from app.agents.continuity_agent import create_continuity_agent
from app.agents.editor_agent import create_editor_agent
from app.agents.quality_checker import QualityChecker
from app.agents.scene_agent import create_scene_agent
from app.models.router import model_for
from app.tools.characters import update_character_state
from app.tools.context_loader import load_scene_context
from app.tools.manuscript import characters_mentioned, write_scene, write_scene_draft
from app.tools.timeline import append_event, extract_timestamp

_MAX_EDITOR_ITERATIONS = 3
_HIGH_SEVERITY = "high"

# "Kapitel 3, Szene 2" / "kapitel 3 Szene 2" / "Kapitel3Szene2" -- tolerant
# gegenueber Gross-/Kleinschreibung und optionalem Komma, aber bewusst nicht
# ueber die gesamte Nachricht "greedy" (matcht die naechste Szenennummer nach
# der Kapitelnummer, nicht irgendeine spaetere Zahl im Text).
_ACTIVE_SCENE_RE = re.compile(r"[Kk]apitel\s*(\d+)\D{0,20}?[Ss]zene\s*(\d+)", re.DOTALL)


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


def _set_active_scene_from_user_message(callback_context: CallbackContext) -> None:
    """Extrahiert `"Kapitel N, Szene M"` deterministisch aus der User-Nachricht
    und setzt `state["active_chapter"]`/`state["active_scene"]` entsprechend
    (siehe Modul-Docstring). Ohne Treffer bleiben die von
    `app/callbacks.py::initialize_state` gesetzten Defaults unveraendert."""
    user_content = callback_context.user_content
    if not user_content or not user_content.parts:
        return
    text = " ".join(part.text for part in user_content.parts if part.text)
    match = _ACTIVE_SCENE_RE.search(text)
    if not match:
        return
    callback_context.state["active_chapter"] = int(match.group(1))
    callback_context.state["active_scene"] = int(match.group(2))


def _format_conflict(conflict: dict) -> str:
    severity = conflict.get("severity", "?")
    kind = conflict.get("type", "Konflikt")
    evidence = conflict.get("evidence", "")
    reference = conflict.get("reference", "?")
    return f"[{severity}] {kind}: {evidence} (siehe {reference})"


class _ContinuityGate(BaseAgent):
    """Umhuellt den Editor-`LoopAgent`: ein Kontinuitaets-Konflikt mit
    `severity: "high"` (`state["continuity_report"]`, gesetzt vom
    vorangehenden `continuity_agent`-Schritt) verhindert das Schreiben der
    Szene vollstaendig -- der Editor-Loop wird dafuer gar nicht erst
    gestartet (spart LLM-Aufrufe fuer eine Szene, die ohnehin nicht
    persistiert wird), die Szene landet stattdessen als Konflikt-Entwurf
    (`.draft.md`), die Konfliktliste wird als Turn-Antwort ausgegeben
    (TASK-003-Akzeptanzkriterium "Continuity-Konflikt verhindert das
    Schreiben; Konfliktliste wird ausgegeben").

    `ADK`s `SequentialAgent` honoriert `EventActions.escalate` NICHT (das ist
    ein reines `LoopAgent`-Signal) -- ein fruehzeitiger Abbruch der
    umgebenden Pipeline ist deshalb nicht moeglich. Diese Klasse loest das
    stattdessen durch Komposition: sie haelt den echten Editor-`LoopAgent`
    als einzigen Sub-Agenten und delegiert nur dann an ihn, wenn kein
    High-Severity-Konflikt vorliegt.
    """

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state
        report = state.get("continuity_report") or {}
        conflicts = report.get("conflicts", []) if isinstance(report, dict) else []
        high_severity = [c for c in conflicts if c.get("severity") == _HIGH_SEVERITY]

        if not high_severity:
            editing_loop = self.sub_agents[0]
            async for event in editing_loop.run_async(ctx):
                yield event
            return

        chapter = state.get("active_chapter", 1)
        scene = state.get("active_scene", 1)
        conflict_lines = [_format_conflict(c) for c in high_severity]
        write_scene_draft(
            chapter=chapter,
            scene=scene,
            text=state.get("scene_draft", ""),
            verdict={"grade": "continuity_conflict", "issues": conflict_lines},
        )
        summary = (
            "Szene wurde NICHT gespeichert -- Kontinuitaets-Konflikt(e) mit hoher "
            "Schwere gefunden:\n" + "\n".join(f"- {line}" for line in conflict_lines)
        )
        yield Event(
            author=self.name,
            content=types.Content(role="model", parts=[types.Part(text=summary)]),
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
    continuity_gate = _ContinuityGate(name="continuity_gate", sub_agents=[editing_loop])
    return SequentialAgent(
        name="writing_pipeline",
        description=(
            "Deterministische Schreib-Pipeline: Kontext laden, Beat bestaetigen, "
            "Figuren-Brief holen, Szene schreiben, Kontinuitaet pruefen, lektorieren."
        ),
        before_agent_callback=_set_active_scene_from_user_message,
        sub_agents=[
            _create_context_loader_step(),
            _create_plot_beat_step(),
            _create_character_brief_step(),
            create_scene_agent(),
            create_continuity_agent(),
            continuity_gate,
        ],
    )
