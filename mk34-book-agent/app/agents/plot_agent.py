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

"""Plot Agent: Szenen-Beats, Wendepunkte und Spannungsbogen (TASK-004).

Zweistufig, weil `output_schema` Tool-Calling und Delegation deaktiviert
(ADK-Cheatsheet): ein Agent mit Tools sammelt den Kontext
(`output_key="plot_raw"`), ein nachgelagerter Agent mit `output_schema`
formalisiert ihn (`output_key="plot_beats"`). Ein `after_agent_callback`
schreibt die formalisierten Beats deterministisch nach `plot_outline.json`
-- Persistenz haengt nie davon ab, dass ein Modell einen Tool-Call zum
Speichern "erinnert".
"""

from __future__ import annotations

from google.adk.agents import Agent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext

from app.models.router import model_for
from app.prompts.plot import PLOT_CONTEXT_INSTRUCTION, PLOT_FORMALIZER_INSTRUCTION
from app.schemas import SceneBeatList
from app.tools.context_loader import (
    load_plot_outline,
    read_chapter_summaries,
    update_plot_outline,
)


def _create_plot_context_agent() -> Agent:
    return Agent(
        name="plot_context_gatherer",
        model=model_for("plot"),
        description="Sammelt Kontext (Phase, bisherige Kapitel) fuer die Beat-Entwicklung.",
        instruction=PLOT_CONTEXT_INSTRUCTION,
        tools=[load_plot_outline, read_chapter_summaries],
        output_key="plot_raw",
    )


def _create_plot_formalizer_agent() -> Agent:
    return Agent(
        name="plot_formalizer",
        model=model_for("plot"),
        description="Formalisiert grobe Beat-Ideen in strukturierte SceneBeat-Objekte.",
        instruction=PLOT_FORMALIZER_INSTRUCTION,
        output_schema=SceneBeatList,
        output_key="plot_beats",
    )


async def _persist_plot_beats(callback_context: CallbackContext) -> None:
    """Schreibt die formalisierten Beats deterministisch nach `plot_outline.json`."""
    raw = callback_context.state.get("plot_beats")
    beats = raw.get("beats", []) if isinstance(raw, dict) else []
    for beat in beats:
        update_plot_outline(
            chapter=beat["chapter"],
            scene=beat["scene"],
            pov_character=beat["pov_character"],
            location=beat["location"],
            beat=beat["beat"],
            turning_point=beat["turning_point"],
            tension_level=beat["tension_level"],
            characters_present=beat["characters_present"],
        )


def create_plot_agent() -> SequentialAgent:
    """Factory -- **aufrufen** (`create_plot_agent()`), nicht referenzieren."""
    return SequentialAgent(
        name="plot_agent",
        description=(
            "Entwickelt detaillierte Szenen-Beats, Wendepunkte und Spannungsbogen "
            "fuer eine Akt-/Phasennummer aus basics.md."
        ),
        sub_agents=[_create_plot_context_agent(), _create_plot_formalizer_agent()],
        after_agent_callback=_persist_plot_beats,
    )
