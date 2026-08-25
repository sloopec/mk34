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

"""Character Agent: Figurenkonsistenz und -entwicklung (TASK-005).

Wird als `AgentTool` in Orchestrator/Editor eingebunden (ab Plan 3 zusaetzlich
im Scene Agent) -- der aufrufende Agent behaelt die Kontrolle und bekommt
einen Figuren-Brief zurueck, statt den Turn abzugeben.
"""

from __future__ import annotations

from google.adk.agents import Agent

from app.models.router import model_for
from app.prompts.character import CHARACTER_INSTRUCTION
from app.tools.characters import (
    get_character,
    get_character_arc,
    get_knowledge_state,
    update_character,
)


def create_character_agent() -> Agent:
    """Factory -- **aufrufen** (`create_character_agent()`), nicht referenzieren."""
    return Agent(
        name="character_agent",
        model=model_for("character"),
        description=(
            "Spezialist fuer Figurenkonsistenz: liefert einen Figuren-Brief mit "
            "Sprachregister, Motivation, Wissensstand und Dialogvorschlaegen fuer eine "
            "benannte Figur in einem gegebenen Szenenkontext."
        ),
        instruction=CHARACTER_INSTRUCTION,
        tools=[get_character, get_character_arc, get_knowledge_state, update_character],
    )
