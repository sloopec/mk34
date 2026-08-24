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

"""Unit tests for `app/models/router.py::is_refusal` (Plan 3, TASK-004,
Entscheidung E9) -- "Refusal als Routing-Signal" fuer beide Provider.

Alle Faelle mit gestubbten Responses (`SimpleNamespace`), kein echter
API-Aufruf noetig.
"""

from __future__ import annotations

from types import SimpleNamespace

from app.models.router import is_refusal


def test_is_refusal_false_for_normal_response() -> None:
    response = SimpleNamespace(finish_reason="STOP", candidates=[])
    assert is_refusal(response) is False


# --- Gemini: candidate finish_reason -------------------------------------------


def test_is_refusal_true_for_gemini_candidate_safety_finish_reason() -> None:
    candidate = SimpleNamespace(finish_reason=SimpleNamespace(name="SAFETY"))
    response = SimpleNamespace(candidates=[candidate])
    assert is_refusal(response) is True


def test_is_refusal_true_for_gemini_candidate_prohibited_content() -> None:
    candidate = SimpleNamespace(
        finish_reason=SimpleNamespace(name="PROHIBITED_CONTENT")
    )
    response = SimpleNamespace(candidates=[candidate])
    assert is_refusal(response) is True


def test_is_refusal_true_for_gemini_candidate_finish_reason_as_plain_string() -> None:
    """finish_reason kann auch als reiner String vorliegen (nicht nur als
    Enum mit `.name`), z. B. bei manchen SDK-Versionen/Stubs."""
    candidate = SimpleNamespace(finish_reason="SAFETY")
    response = SimpleNamespace(candidates=[candidate])
    assert is_refusal(response) is True


def test_is_refusal_false_for_gemini_candidate_stop_finish_reason() -> None:
    candidate = SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))
    response = SimpleNamespace(candidates=[candidate])
    assert is_refusal(response) is False


# --- Gemini: prompt-level block (leere Kandidaten) -----------------------------


def test_is_refusal_true_for_gemini_prompt_feedback_block_reason() -> None:
    response = SimpleNamespace(
        candidates=[],
        prompt_feedback=SimpleNamespace(block_reason="SAFETY"),
    )
    assert is_refusal(response) is True


def test_is_refusal_false_without_block_reason_and_no_candidates() -> None:
    response = SimpleNamespace(candidates=[], prompt_feedback=None)
    assert is_refusal(response) is False


# --- ADK-normalisiertes LlmResponse (finish_reason/error_code direkt) ---------


def test_is_refusal_true_for_adk_llm_response_finish_reason() -> None:
    """ADKs `LlmResponse` traegt `finish_reason` direkt auf dem Response-
    Objekt (nicht ueber `candidates`), siehe `google.adk.models.llm_response`."""
    response = SimpleNamespace(finish_reason=SimpleNamespace(name="SAFETY"))
    assert is_refusal(response) is True


def test_is_refusal_true_for_adk_llm_response_error_code() -> None:
    """ADK mappt `prompt_feedback.block_reason` in `LlmResponse.error_code`."""
    response = SimpleNamespace(finish_reason=None, error_code="SAFETY")
    assert is_refusal(response) is True


# --- Claude: stop_reason == "refusal" ------------------------------------------


def test_is_refusal_true_for_claude_stop_reason_refusal() -> None:
    response = SimpleNamespace(stop_reason="refusal")
    assert is_refusal(response) is True


def test_is_refusal_false_for_claude_stop_reason_end_turn() -> None:
    response = SimpleNamespace(stop_reason="end_turn")
    assert is_refusal(response) is False


def test_is_refusal_handles_response_without_any_known_attribute() -> None:
    assert is_refusal(SimpleNamespace()) is False
