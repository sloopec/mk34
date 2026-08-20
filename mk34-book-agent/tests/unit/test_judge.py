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

"""Unit tests for `tests/eval/mk34_eval/judge.py`.

Verifies the provider-agnostic contract with stubbed clients -- no real API
calls, no `GEMINI_API_KEY`/`ANTHROPIC_API_KEY` needed. The call site
(`judge(...)`) is identical for both providers; only the resolved model
string (via `tier` -> `app.config.Settings`) determines which client gets
used.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_EVAL_DIR = Path(__file__).resolve().parent.parent / "eval"
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from mk34_eval import judge as judge_module  # noqa: E402

from app.config import Settings  # noqa: E402


@pytest.fixture
def rubrics_dir(tmp_path, monkeypatch):
    """Isolates rubric loading against a throwaway rubrics directory."""
    d = tmp_path / "rubrics"
    d.mkdir()
    (d / "fast_rubric.md").write_text(
        "---\ntier: fast\n---\n\nBewerte 1-5.\n", encoding="utf-8"
    )
    (d / "craft_rubric.md").write_text(
        "---\ntier: craft\n---\n\nBewerte 1-5, streng.\n", encoding="utf-8"
    )
    (d / "no_tier_rubric.md").write_text("Kein Frontmatter hier.\n", encoding="utf-8")
    monkeypatch.setattr(judge_module, "RUBRICS_DIR", d)
    judge_module.cost_log.reset()
    return d


def _settings(**overrides) -> Settings:
    defaults = {
        "mk34_judge_model_fast": "gemini-3.7-flash",
        "mk34_judge_model_craft": "gemini-3.1-pro-preview",
        "_env_file": None,
    }
    defaults.update(overrides)
    return Settings(**defaults)


# --- load_rubric --------------------------------------------------------------


def test_load_rubric_returns_tier_and_body(rubrics_dir) -> None:
    tier, body = judge_module.load_rubric("fast_rubric")
    assert tier == "fast"
    assert "Bewerte 1-5." in body


def test_load_rubric_missing_file_raises(rubrics_dir) -> None:
    with pytest.raises(FileNotFoundError):
        judge_module.load_rubric("does_not_exist")


def test_load_rubric_missing_frontmatter_raises(rubrics_dir) -> None:
    with pytest.raises(ValueError, match="Frontmatter"):
        judge_module.load_rubric("no_tier_rubric")


# --- judge() on Gemini (fast tier) --------------------------------------------


def test_judge_gemini_returns_schema_valid_verdict(rubrics_dir, monkeypatch) -> None:
    monkeypatch.setattr(
        judge_module, "_model_for_tier", lambda tier: "gemini-3.7-flash"
    )

    class _FakeParsed:
        score = 4
        explanation = "Trifft die Frage gut."

    class _FakeResponse:
        parsed = _FakeParsed()

    class _FakeModels:
        def generate_content(self, **kwargs):
            return _FakeResponse()

    class _FakeGenaiClient:
        models = _FakeModels()

    monkeypatch.setattr(judge_module, "_get_genai_client", lambda: _FakeGenaiClient())

    result = judge_module.judge("fast_rubric", "Frage?", "Antwort.")

    assert result == {"score": 4, "explanation": "Trifft die Frage gut."}
    assert judge_module.cost_log.snapshot()["fast"] == 1


def test_judge_gemini_clamps_out_of_range_score(rubrics_dir, monkeypatch) -> None:
    monkeypatch.setattr(
        judge_module, "_model_for_tier", lambda tier: "gemini-3.7-flash"
    )

    class _FakeParsed:
        score = 9  # out of the documented 1-5 range
        explanation = "Zu hoch."

    class _FakeResponse:
        parsed = _FakeParsed()

    class _FakeModels:
        def generate_content(self, **kwargs):
            return _FakeResponse()

    class _FakeGenaiClient:
        models = _FakeModels()

    monkeypatch.setattr(judge_module, "_get_genai_client", lambda: _FakeGenaiClient())

    result = judge_module.judge("fast_rubric", "Frage?", "Antwort.")

    assert result["score"] == 5


# --- judge() on Claude (craft tier), same call site, stubbed client ----------


def test_judge_claude_returns_schema_valid_verdict_same_call_site(
    rubrics_dir, monkeypatch
) -> None:
    """Acceptance criterion: identical `judge(...)` call site works on Claude
    too, once the resolved model string is `claude-*` -- only the stubbed
    client differs, no code change at the call site.
    """
    monkeypatch.setattr(judge_module, "_model_for_tier", lambda tier: "claude-opus-5")

    class _FakeTextBlock:
        type = "text"
        text = '{"score": 5, "explanation": "Durchgehend im Register."}'

    class _FakeAnthropicResponse:
        content = (_FakeTextBlock(),)

    class _FakeMessages:
        def create(self, **kwargs):
            return _FakeAnthropicResponse()

    class _FakeAnthropicClient:
        messages = _FakeMessages()

    monkeypatch.setattr(
        judge_module, "_get_anthropic_client", lambda: _FakeAnthropicClient()
    )

    result = judge_module.judge("craft_rubric", "Frage?", "Antwort.")

    assert result == {"score": 5, "explanation": "Durchgehend im Register."}
    assert judge_module.cost_log.snapshot()["craft"] == 1


def test_judge_claude_parses_json_wrapped_in_prose(rubrics_dir, monkeypatch) -> None:
    """Claude sometimes wraps JSON in explanatory prose; the extractor must
    still find and parse the embedded object."""
    monkeypatch.setattr(judge_module, "_model_for_tier", lambda tier: "claude-opus-5")

    class _FakeTextBlock:
        type = "text"
        text = 'Hier ist meine Bewertung:\n{"score": 3, "explanation": "Ok."}\nEnde.'

    class _FakeAnthropicResponse:
        content = (_FakeTextBlock(),)

    class _FakeMessages:
        def create(self, **kwargs):
            return _FakeAnthropicResponse()

    class _FakeAnthropicClient:
        messages = _FakeMessages()

    monkeypatch.setattr(
        judge_module, "_get_anthropic_client", lambda: _FakeAnthropicClient()
    )

    result = judge_module.judge("craft_rubric", "Frage?", "Antwort.")

    assert result == {"score": 3, "explanation": "Ok."}


# --- provider dispatch ---------------------------------------------------------


def test_provider_for_model_dispatches_gemini_and_claude() -> None:
    assert judge_module._provider_for_model("gemini-3.7-flash") == "google-genai"
    assert judge_module._provider_for_model("claude-opus-5") == "anthropic"


def test_provider_for_model_unknown_prefix_raises() -> None:
    with pytest.raises(ValueError, match="Unbekannter Judge-Provider"):
        judge_module._provider_for_model("mystery-model")


def test_model_for_tier_reads_from_settings(rubrics_dir, monkeypatch) -> None:
    settings = _settings(
        mk34_judge_model_fast="gemini-fast-marker",
        mk34_judge_model_craft="gemini-craft-marker",
    )
    monkeypatch.setattr(judge_module, "get_settings", lambda: settings)
    assert judge_module._model_for_tier("fast") == "gemini-fast-marker"
    assert judge_module._model_for_tier("craft") == "gemini-craft-marker"


# --- cost log -------------------------------------------------------------------


def test_cost_log_separates_fast_and_craft(rubrics_dir, monkeypatch) -> None:
    monkeypatch.setattr(
        judge_module, "_model_for_tier", lambda tier: "gemini-3.7-flash"
    )

    class _FakeParsed:
        score = 3
        explanation = "x"

    class _FakeResponse:
        parsed = _FakeParsed()

    class _FakeModels:
        def generate_content(self, **kwargs):
            return _FakeResponse()

    class _FakeGenaiClient:
        models = _FakeModels()

    monkeypatch.setattr(judge_module, "_get_genai_client", lambda: _FakeGenaiClient())

    judge_module.judge("fast_rubric", "a", "b")
    judge_module.judge("fast_rubric", "a", "b")

    snapshot = judge_module.cost_log.snapshot()
    assert snapshot["fast"] == 2
    assert snapshot["craft"] == 0
