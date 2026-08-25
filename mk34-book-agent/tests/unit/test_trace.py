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

"""Unit tests for `tests/eval/mk34_eval/trace.py::get_state_delta` (Plan 3,
TASK-005 Stufe B, ergaenzt fuer `correct_route_metric.py`).
"""

from __future__ import annotations

import sys
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parent.parent / "eval"
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from mk34_eval.trace import get_state_delta  # noqa: E402


def test_get_state_delta_returns_none_when_key_never_written() -> None:
    instance = {"agent_data": {"turns": [{"events": [{"actions": {}}]}]}}
    assert get_state_delta(instance, "route") is None


def test_get_state_delta_finds_value_in_state_delta() -> None:
    instance = {
        "agent_data": {
            "turns": [{"events": [{"actions": {"stateDelta": {"route": "local"}}}]}]
        }
    }
    assert get_state_delta(instance, "route") == "local"


def test_get_state_delta_returns_last_written_value() -> None:
    """Idempotent state Schreibvorgaenge: der letzte Event gewinnt."""
    instance = {
        "agent_data": {
            "turns": [
                {
                    "events": [
                        {"actions": {"stateDelta": {"route": "cloud"}}},
                        {"actions": {"stateDelta": {"route": "local"}}},
                    ]
                }
            ]
        }
    }
    assert get_state_delta(instance, "route") == "local"


def test_get_state_delta_handles_missing_agent_data() -> None:
    assert get_state_delta({}, "route") is None


def test_get_state_delta_handles_events_without_actions() -> None:
    instance = {"agent_data": {"turns": [{"events": [{"content": {}}]}]}}
    assert get_state_delta(instance, "route") is None


def test_get_state_delta_ignores_unrelated_keys() -> None:
    instance = {
        "agent_data": {
            "turns": [{"events": [{"actions": {"stateDelta": {"scene_draft": "x"}}}]}]
        }
    }
    assert get_state_delta(instance, "route") is None
