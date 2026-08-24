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

"""Scene Agent: schreibt eine einzelne Szene aus Beat, Figuren-Brief und
Weltregeln (Plan 3, TASK-002) -- der Agent, fuer den es dieses Projekt gibt.

**Stufe A (dieser Task):** `model_for("scene")` ohne `route`-Argument liefert
immer die Cloud-Route (`MK34_MODEL_SCENE`, Start `gemini-3.1-pro-preview`,
Entscheidung E6) -- der Schreib-Workflow ist damit sofort ohne laufende VM
testbar. **Stufe B (Plan 3, TASK-004):** ein Routing-Wrapper in
`app/pipelines/writing.py` ruft `model_for("scene", route=state["route"])`
pro Pipeline-Durchlauf erneut auf und baut bei Bedarf eine frische
`Agent`-Instanz mit dem lokalen Modell -- an dieser Factory-Funktion selbst
aendert sich dafuer nichts (siehe `app/models/router.py`-Docstring).

Bewusst **keine** Safety-Callbacks/-Plugins auf diesem Agenten (Kern-Use-Case-
Entscheidung, gilt fuer Plan 3/4 unveraendert) -- ein Safety-Block auf einer
harmlosen Szene ist ein Bug im Prompt oder ein Fall fuer die lokale Route.
"""

from __future__ import annotations

from google.adk.agents import Agent

from app.models.router import model_for
from app.prompts.scene import SCENE_INSTRUCTION
from app.tools.context_loader import load_scene_context
from app.tools.manuscript import read_manuscript, write_scene


def create_scene_agent() -> Agent:
    """Factory -- **aufrufen** (`create_scene_agent()`), nicht referenzieren."""
    return Agent(
        name="scene_agent",
        model=model_for("scene"),
        description=(
            "Schreibt eine einzelne Szene aus Beat, Figuren-Brief und Weltregeln. "
            "Kreatives Schreibwerkzeug -- keine Safety-Guardrails (Kern-Use-Case)."
        ),
        instruction=SCENE_INSTRUCTION,
        tools=[read_manuscript, write_scene, load_scene_context],
        output_key="scene_draft",
    )
