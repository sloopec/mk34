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

"""Editor Agent: Lektorat -- prueft und ueberarbeitet Rohtext (TASK-006).

Laeuft in diesem Plan ueber **vorgelegten** Text (Fixture bzw. Autoren-Rohtext)
-- der Scene Agent existiert noch nicht (kommt in Plan 3). `output_schema`
deaktiviert Tool-Calling; der Editor braucht ohnehin keine Tools, sein Input
kommt vollstaendig aus dem State (`{scene_draft}`, `{scene_context}`,
optional `{continuity_report}`).
"""

from __future__ import annotations

from google.adk.agents import Agent

from app.models.router import model_for
from app.prompts.editor import EDITOR_INSTRUCTION
from app.schemas import EditorVerdict


def create_editor_agent() -> Agent:
    """Factory -- **aufrufen** (`create_editor_agent()`), nicht referenzieren."""
    return Agent(
        name="editor_agent",
        model=model_for("editor"),
        description=(
            "Lektoriert Szenentext: Stilkonsistenz, Sprachregister, Pacing, "
            "Show-dont-tell, ELI5-Qualitaet. Aendert nie Handlungsfakten."
        ),
        instruction=EDITOR_INSTRUCTION,
        output_schema=EditorVerdict,
        output_key="editor_verdict",
    )
