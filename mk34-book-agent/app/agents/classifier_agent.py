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

"""Content-Classifier: entscheidet lokal/Cloud fuer den Scene Agent (Plan 3,
TASK-004). `output_schema` liefert eine strukturierte `RouteDecision`
(`route`, `reason`, `confidence`) unter `state["route_decision"]` --
`output_schema` deaktiviert Tool-Calling (ADK-Cheatsheet), der Classifier
braucht ohnehin keine Tools, sein Input kommt vollstaendig aus dem State
(`{scene_context}`, `{scene_beat}`).

Modell: `model_for("classifier")` -> Start `gemini-3.5-flash-lite` (E6,
billige, haeufige Ja/Nein-Entscheidung), spaeter `anthropic/claude-haiku-4-5`.
"""

from __future__ import annotations

from google.adk.agents import Agent

from app.models.router import model_for
from app.prompts.classifier import CLASSIFIER_INSTRUCTION
from app.schemas import RouteDecision


def create_classifier_agent() -> Agent:
    """Factory -- **aufrufen** (`create_classifier_agent()`), nicht referenzieren."""
    return Agent(
        name="classifier_agent",
        model=model_for("classifier"),
        description=(
            "Entscheidet, ob die naechste Szene lokal (unzensiert) oder in der "
            "Cloud geschrieben wird -- schreibt selbst keinen Szenentext."
        ),
        instruction=CLASSIFIER_INSTRUCTION,
        output_schema=RouteDecision,
        output_key="route_decision",
    )
