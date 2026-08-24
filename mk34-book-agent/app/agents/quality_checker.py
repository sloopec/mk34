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

"""`QualityChecker`: terminiert den Editor-`LoopAgent` bei `grade == "pass"`.

Grundlage fuer den `LoopAgent(editor_agent, quality_checker)` in TASK-008.
`output_schema` liefert den `editor_verdict`-State-Wert als reines `dict`
(ADK serialisiert `BaseModel.model_dump()`, siehe `_schema_utils.py`) --
`QualityChecker` liest also `state["editor_verdict"]["grade"]`, nicht ein
Pydantic-Objekt.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions


class QualityChecker(BaseAgent):
    """Eskaliert (stoppt den umgebenden `LoopAgent`), sobald der Editor
    `grade == "pass"` liefert."""

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        verdict = ctx.session.state.get("editor_verdict")
        if verdict and verdict.get("grade") == "pass":
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            yield Event(author=self.name)
