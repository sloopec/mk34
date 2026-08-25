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

"""`before_agent_callback`s, die den Session-State vorinitialisieren.

`initialize_state` verhindert `KeyError` beim ersten Turn, wenn eine
Instruction bereits `{book_slug}`, `{active_chapter}`, `{active_scene}` oder
`{scene_context}` referenziert, bevor der erste State-Schreibvorgang
(z. B. `load_scene_context`, TASK-002) stattgefunden hat.
"""

from __future__ import annotations

from google.adk.agents.callback_context import CallbackContext

from app.config import get_settings


async def initialize_state(callback_context: CallbackContext) -> None:
    """Setzt Default-Werte fuer `{state_key}`-Injections, falls noch unbesetzt."""
    state = callback_context.state
    settings = get_settings()

    if "book_slug" not in state:
        state["book_slug"] = settings.mk34_book_slug
    if "active_chapter" not in state:
        state["active_chapter"] = 1
    if "active_scene" not in state:
        state["active_scene"] = 1
    if "scene_context" not in state:
        state["scene_context"] = {}
