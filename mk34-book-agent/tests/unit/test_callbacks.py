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

"""Unit tests for `app/callbacks.initialize_state`.

`initialize_state` only touches `callback_context.state` (a dict-like), so a
minimal fake stands in for `CallbackContext` -- no real `InvocationContext`
needed.
"""

from __future__ import annotations

import pytest

from app.callbacks import initialize_state


class _FakeCallbackContext:
    def __init__(self, state: dict | None = None):
        self.state = state if state is not None else {}


@pytest.mark.asyncio
async def test_initialize_state_sets_all_four_defaults() -> None:
    ctx = _FakeCallbackContext()

    await initialize_state(ctx)

    assert ctx.state["book_slug"] == "life_link"
    assert ctx.state["active_chapter"] == 1
    assert ctx.state["active_scene"] == 1
    assert ctx.state["scene_context"] == {}


@pytest.mark.asyncio
async def test_initialize_state_does_not_overwrite_existing_values() -> None:
    ctx = _FakeCallbackContext(
        state={"active_chapter": 5, "active_scene": 2, "scene_context": {"beat": "x"}}
    )

    await initialize_state(ctx)

    assert ctx.state["active_chapter"] == 5
    assert ctx.state["active_scene"] == 2
    assert ctx.state["scene_context"] == {"beat": "x"}
    assert ctx.state["book_slug"] == "life_link"  # still filled in
