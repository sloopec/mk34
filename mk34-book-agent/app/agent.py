# ruff: noqa
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

"""mk34 root_agent: der Orchestrator (Plan 2, TASK-007).

Ersetzt den TASK-003-Interims-Scaffold-Agenten vollstaendig (siehe dessen
Kommentar dort, der genau diesen Ersatz ankuendigte). Zwei Einbindungsarten
bewusst getrennt (siehe TASK-007-Task-Datei):
- `sub_agents` -- Agenten, die einen ganzen Turn uebernehmen duerfen (Plot,
  Editor; ab Plan 3 auch Scene/Pipeline).
- `AgentTool` -- Spezialisten, die innerhalb eines Turns konsultiert werden
  und antworten (Character; spaeter Continuity/Research).

Die Registrierung des Scene Agent als Sub-Agent und das Pipeline-Routing
("Schreibe 3.2 -> writing_pipeline") folgen in
`03-szenen-und-lokales-llm/TASK-003`; die Instruction wird dort erweitert,
nicht neu geschrieben.
"""

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import AgentTool
from google.genai import types

from app.agents.character_agent import create_character_agent
from app.agents.editor_agent import create_editor_agent
from app.agents.plot_agent import create_plot_agent
from app.callbacks import initialize_state
from app.models.router import model_for
from app.prompts.orchestrator import ORCHESTRATOR_INSTRUCTION
from app.tools.context_loader import load_plot_outline
from app.tools.manuscript import chapter_stats, list_chapters

# mk34 (Entscheidung E6, plan.md): Modell kommt aus dem zentralen Router statt
# hartcodiert zu sein. Bewusst beauftragte Modelländerung (Code-Preservation-
# Ausnahme) -- siehe .claude/plans/01-fundament-und-kontext/tasks/TASK-002-model-router.md.
MODEL = model_for("orchestrator")


def _wrap_model(model):
    # `model_for` returns a bare Gemini model-ID string today (Gemini-first,
    # Entscheidung E6); wrap it the same way the scaffold default was wrapped
    # (retry_options preserved). A future `.env` switch to `anthropic/*` would
    # make `model_for` return a `LiteLlm` instance instead, which ADK's `Agent`
    # accepts directly -- so only the string case needs the `Gemini(...)` wrapper.
    if isinstance(model, str):
        return Gemini(model=model, retry_options=types.HttpRetryOptions(attempts=3))
    return model


# mk34 (TASK-007): `load_plot_outline` ist zusaetzlich zum in der Task-Datei
# skizzierten Tool-Set aufgenommen -- rein faktische Plot-Nachfragen ("Fasse
# Phase 2 zusammen", TASK-003/basic-dataset.json) sollen als Nachschlagen
# beantwortet werden, nicht ueber eine Sub-Agent-Delegation an den Plot
# Agent, der als Nebenwirkung spekulative Beats nach plot_outline.json
# schreiben wuerde (siehe TASK-004: after_agent_callback persistiert
# deterministisch bei jedem Lauf).
root_agent = Agent(
    name="orchestrator",
    model=_wrap_model(MODEL),
    description="Koordiniert die Buch-Agenten fuer das Projekt Life Link.",
    instruction=ORCHESTRATOR_INSTRUCTION,
    sub_agents=[create_plot_agent(), create_editor_agent()],
    tools=[
        AgentTool(create_character_agent()),
        list_chapters,
        chapter_stats,
        load_plot_outline,
    ],
    before_agent_callback=initialize_state,
)

app = App(
    root_agent=root_agent,
    name="app",
)
