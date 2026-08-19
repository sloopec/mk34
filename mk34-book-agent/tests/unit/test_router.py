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

"""Unit tests for the mk34 model router: role -> tier -> model -> provider.

Only code-correctness is asserted here (role mapping, tier resolution,
provider dispatch) -- no LLM output is checked. See `mk34-book-agent/CLAUDE.md`
and `.claude/plans/01-fundament-und-kontext/tasks/TASK-002-model-router.md`.
"""

from __future__ import annotations

import pytest

from app.config import Settings
from app.models.router import ROLE_TIERS, model_for


def _settings(**overrides) -> Settings:
    """Builds a `Settings` instance isolated from the real `.env`/environ."""
    defaults = {
        "mk34_model_heavy": "gemini-3.1-pro-preview",
        "mk34_model_fast": "gemini-3.7-flash",
        "mk34_model_lite": "gemini-3.5-flash-lite",
        "mk34_model_scene": "gemini-3.1-pro-preview",
        "gemini_api_key": "test-key",
        "anthropic_api_key": None,
        "_env_file": None,  # do not read the project's real .env
    }
    defaults.update(overrides)
    return Settings(**defaults)


# --- Rollen-Mapping ---------------------------------------------------------

EXPECTED_ROLE_TIERS = {
    "orchestrator": "fast",
    "continuity": "fast",
    "research": "fast",
    "plot": "heavy",
    "character": "heavy",
    "editor": "heavy",
    "style": "heavy",
    "classifier": "lite",
    "scene": "scene",
}


def test_role_tiers_cover_all_nine_roles() -> None:
    assert ROLE_TIERS == EXPECTED_ROLE_TIERS


@pytest.mark.parametrize("role", sorted(EXPECTED_ROLE_TIERS))
def test_model_for_returns_bare_gemini_string_for_every_role(role: str) -> None:
    settings = _settings()
    result = model_for(role, settings=settings)
    assert isinstance(result, str)
    assert result.startswith("gemini-")


def test_model_for_unknown_role_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unbekannte Rolle"):
        model_for("narrator", settings=_settings())


# --- Tier-Aufloesung ---------------------------------------------------------


def test_model_for_tier_resolves_all_four_tiers() -> None:
    settings = _settings(
        mk34_model_heavy="gemini-heavy-x",
        mk34_model_fast="gemini-fast-x",
        mk34_model_lite="gemini-lite-x",
        mk34_model_scene="gemini-scene-x",
    )
    assert settings.model_for_tier("heavy") == "gemini-heavy-x"
    assert settings.model_for_tier("fast") == "gemini-fast-x"
    assert settings.model_for_tier("lite") == "gemini-lite-x"
    assert settings.model_for_tier("scene") == "gemini-scene-x"


def test_model_for_tier_unknown_tier_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unbekannter Modell-Tier"):
        _settings().model_for_tier("ultra")


def test_heavy_roles_resolve_through_heavy_tier() -> None:
    settings = _settings(mk34_model_heavy="gemini-heavy-marker")
    for role in ("plot", "character", "editor", "style"):
        assert model_for(role, settings=settings) == "gemini-heavy-marker"


def test_fast_roles_resolve_through_fast_tier() -> None:
    settings = _settings(mk34_model_fast="gemini-fast-marker")
    for role in ("orchestrator", "continuity", "research"):
        assert model_for(role, settings=settings) == "gemini-fast-marker"


def test_scene_role_uses_its_own_variable() -> None:
    settings = _settings(
        mk34_model_heavy="gemini-heavy-marker",
        mk34_model_scene="gemini-scene-marker",
    )
    assert model_for("scene", settings=settings) == "gemini-scene-marker"


# --- Provider-Erkennung ------------------------------------------------------


def test_gemini_provider_returns_bare_string_not_a_wrapper() -> None:
    settings = _settings(mk34_model_fast="gemini-3.7-flash")
    result = model_for("orchestrator", settings=settings)
    assert result == "gemini-3.7-flash"
    assert type(result) is str


def test_gemini_provider_missing_api_key_raises_runtime_error() -> None:
    settings = _settings(gemini_api_key=None)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        model_for("orchestrator", settings=settings)


def test_anthropic_provider_returns_lite_llm_instance_without_api_call() -> None:
    from google.adk.models.lite_llm import LiteLlm

    settings = _settings(mk34_model_fast="anthropic/claude-sonnet-5")
    result = model_for("orchestrator", settings=settings)
    assert isinstance(result, LiteLlm)
    assert result.model == "anthropic/claude-sonnet-5"


def test_local_provider_raises_not_implemented_with_plan_reference() -> None:
    settings = _settings(mk34_model_scene="local")
    with pytest.raises(NotImplementedError, match="03-szenen-und-lokales-llm"):
        model_for("scene", settings=settings)


def test_unknown_provider_prefix_raises_value_error() -> None:
    settings = _settings(mk34_model_fast="mystery-model-42")
    with pytest.raises(ValueError, match="Unbekannter Provider"):
        model_for("orchestrator", settings=settings)
