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

"""Continuity Agent: Faktencheck neuer Szenen gegen das bisherige Manuskript
(TASK-011), per lokalem FTS5-Retrieval statt "das gesamte Manuskript lesen"
(sprengt bei 30+ Kapiteln jedes Kontextfenster/Budget).

Zweistufig wie der Plot Agent (TASK-004): ein Agent mit `check_consistency`-
Tool sammelt Belege (`output_key="continuity_raw"`), ein nachgelagerter
Agent mit `output_schema=ContinuityReport` formalisiert sie
(`output_key="continuity_report"`) -- `output_schema` deaktiviert
Tool-Calling.

Einbindung als `AgentTool` (in Plan 3 in der Pipeline vor dem Editor-Loop,
siehe `app/pipelines/writing.py`, TASK-008 -- der Continuity-Schritt selbst
kommt erst mit Plan 3).
"""

from __future__ import annotations

from google.adk.agents import Agent, SequentialAgent

from app.models.router import model_for
from app.prompts.continuity import (
    CONTINUITY_CONTEXT_INSTRUCTION,
    CONTINUITY_FORMALIZER_INSTRUCTION,
)
from app.schemas import ContinuityReport
from app.tools.consistency import check_consistency, validate_world_rules


def _create_continuity_context_agent() -> Agent:
    return Agent(
        name="continuity_context_agent",
        model=model_for("continuity"),
        description="Sucht relevante Vorpassagen und identifiziert moegliche Konflikte.",
        instruction=CONTINUITY_CONTEXT_INSTRUCTION,
        tools=[check_consistency, validate_world_rules],
        output_key="continuity_raw",
    )


def _create_continuity_formalizer_agent() -> Agent:
    return Agent(
        name="continuity_formalizer",
        model=model_for("continuity"),
        description="Formalisiert gefundene Konflikte in ein strukturiertes Verdikt.",
        instruction=CONTINUITY_FORMALIZER_INSTRUCTION,
        output_schema=ContinuityReport,
        output_key="continuity_report",
    )


def create_continuity_agent() -> SequentialAgent:
    """Factory -- **aufrufen** (`create_continuity_agent()`), nicht referenzieren."""
    return SequentialAgent(
        name="continuity_agent",
        description=(
            "Prueft eine neue Szene auf Widersprueche zum bisherigen Manuskript "
            "(Wissen zu frueh, Zeitspruenge, Naniten-Regelverstoesse), per lokalem "
            "Retrieval belegt."
        ),
        sub_agents=[
            _create_continuity_context_agent(),
            _create_continuity_formalizer_agent(),
        ],
    )
