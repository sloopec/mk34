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

**Stufe A (TASK-002/003):** `model_for("scene")` ohne `route`-Argument liefert
immer die Cloud-Route (`MK34_MODEL_SCENE`, Start `gemini-3.1-pro-preview`,
Entscheidung E6) -- der Schreib-Workflow ist damit sofort ohne laufende VM
testbar. **Stufe B (Plan 3, TASK-004):** `create_scene_agent(route=...)`
nimmt jetzt einen optionalen `route`-Parameter (`"local"`/`"cloud"`/`None`)
entgegen und reicht ihn an `model_for("scene", route=route)` durch. Ein
Routing-Wrapper in `app/pipelines/writing.py`
(`_RoutedSceneStep`) ruft diese Factory pro Pipeline-Durchlauf mit dem
aktuellen `state["route"]` (gesetzt vom Classifier, TASK-004) frisch auf --
ADKs `Agent.model` wird sonst nur einmal bei der Konstruktion aufgeloest
(siehe `app/models/router.py`-Docstring), ein dynamischer Modellwechsel pro
Turn braucht deshalb eine frische Agent-Instanz statt eines mutierbaren
Felds.

Bewusst **keine** Safety-Callbacks/-Plugins auf diesem Agenten (Kern-Use-Case-
Entscheidung, gilt fuer Plan 3/4 unveraendert) -- ein Safety-Block auf einer
harmlosen Szene ist ein Bug im Prompt oder ein Fall fuer die lokale Route.
`_log_refusal_if_detected` (TASK-004, Entscheidung E9) ist bewusst rein
beobachtend: sie blockiert/veraendert nie eine Antwort (kein Guardrail,
`return None` immer), sie protokolliert nur, wenn ein Cloud-Refusal auftritt
-- Signal fuer die Klassifikationsregel-Nachschaerfung, siehe
`app/pipelines/writing.py`-Docstring.
"""

from __future__ import annotations

import logging

from google.adk.agents import Agent

from app.models.router import is_refusal, model_for
from app.prompts.scene import SCENE_INSTRUCTION
from app.tools.context_loader import load_scene_context
from app.tools.manuscript import read_manuscript, write_scene

_logger = logging.getLogger(__name__)


async def _log_refusal_if_detected(callback_context, llm_response):
    """`after_model_callback`: protokolliert eine erkannte Cloud-Refusal
    (Entscheidung E9), veraendert die Antwort NIE (kein Guardrail). Ist die
    Szene bereits auf `local` geroutet, ist eine Refusal ohnehin nicht zu
    erwarten -- das Signal ist primaer fuer die Cloud-Route relevant (eine
    Klassifikationsregel, die haette 'local' waehlen sollen)."""
    if is_refusal(llm_response):
        route = callback_context.state.get("route", "cloud")
        _logger.warning(
            "Scene Agent: Cloud-Refusal erkannt (route=%s, chapter=%s, scene=%s). "
            "Nachschaerfungs-Fall fuer tests/eval/datasets/uncensored-routing.json "
            "(Entscheidung E9).",
            route,
            callback_context.state.get("active_chapter"),
            callback_context.state.get("active_scene"),
        )
    return None


def create_scene_agent(route: str | None = None) -> Agent:
    """Factory -- **aufrufen** (`create_scene_agent()`), nicht referenzieren.

    Args:
        route: Optionale explizite Route (`"local"`/`"cloud"`), z. B.
            `state["route"]` (Classifier, TASK-004) oder ein manueller
            Override. `None` (Default) resolves ueber `model_for("scene")`
            immer auf die Cloud-Route (Stufe A, TASK-002/003).
    """
    return Agent(
        name="scene_agent",
        model=model_for("scene", route=route),
        description=(
            "Schreibt eine einzelne Szene aus Beat, Figuren-Brief und Weltregeln. "
            "Kreatives Schreibwerkzeug -- keine Safety-Guardrails (Kern-Use-Case)."
        ),
        instruction=SCENE_INSTRUCTION,
        tools=[read_manuscript, write_scene, load_scene_context],
        output_key="scene_draft",
        after_model_callback=_log_refusal_if_detected,
    )
