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

"""Unit tests for the local-LLM anteil of the model router (Plan 3, TASK-001).

No real VM/tunnel is required -- `local_model_available` is exercised
against unreachable URLs (real network failure, no mock needed for the
"VM is down" case) and against a mocked `urllib.request.urlopen` for the
"VM is up" case, so the suite stays fast and offline.
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from app.config import Settings
from app.models.router import local_model_available, model_for


def _settings(**overrides) -> Settings:
    """Builds a `Settings` instance isolated from the real `.env`/environ."""
    defaults = {
        "mk34_model_heavy": "gemini-3.1-pro-preview",
        "mk34_model_fast": "gemini-3.7-flash",
        "mk34_model_lite": "gemini-3.5-flash-lite",
        "mk34_model_scene": "gemini-3.1-pro-preview",
        "gemini_api_key": "test-key",
        "anthropic_api_key": None,
        "mk34_local_model": "openai/supergemma4",
        "mk34_local_api_base": "http://localhost:8080/v1",
        "mk34_local_api_key": "not-needed",
        # unrouted port, unreachable without any real service listening --
        # deterministic "VM is down" without touching the network stack.
        "mk34_local_health_url": "http://127.0.0.1:1/health",
        "mk34_allow_cloud_fallback": False,
        "_env_file": None,  # do not read the project's real .env
    }
    defaults.update(overrides)
    return Settings(**defaults)


@contextmanager
def _mock_healthy_endpoint():
    response = MagicMock()
    response.status = 200
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    with patch("app.models.router.urllib.request.urlopen", return_value=response) as m:
        yield m


# --- local_model_available ---------------------------------------------------


def test_local_model_available_false_without_running_vm() -> None:
    settings = _settings()
    assert local_model_available(settings) is False


def test_local_model_available_true_when_health_endpoint_responds_ok() -> None:
    settings = _settings()
    with _mock_healthy_endpoint():
        assert local_model_available(settings) is True


def test_local_model_available_false_on_non_2xx_status() -> None:
    settings = _settings()
    response = MagicMock()
    response.status = 503
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    with patch("app.models.router.urllib.request.urlopen", return_value=response):
        assert local_model_available(settings) is False


def test_local_model_available_never_raises_on_malformed_url() -> None:
    settings = _settings(mk34_local_health_url="not-a-valid-url")
    assert local_model_available(settings) is False


# --- model_for("scene", route="local") ---------------------------------------


def test_scene_route_local_returns_lite_llm_when_vm_reachable() -> None:
    from google.adk.models.lite_llm import LiteLlm

    settings = _settings()
    with _mock_healthy_endpoint():
        result = model_for("scene", settings=settings, route="local")

    assert isinstance(result, LiteLlm)
    assert result.model == "openai/supergemma4"


def test_scene_route_cloud_returns_configured_gemini_model() -> None:
    settings = _settings(mk34_model_scene="gemini-3.1-pro-preview")
    result = model_for("scene", settings=settings, route="cloud")
    assert result == "gemini-3.1-pro-preview"


def test_scene_role_without_route_defaults_to_cloud() -> None:
    """Stufe A (TASK-002/003): ohne Classifier/Override bleibt scene auf Cloud."""
    settings = _settings(mk34_model_scene="gemini-3.1-pro-preview")
    result = model_for("scene", settings=settings)
    assert result == "gemini-3.1-pro-preview"


# --- Kein stiller Cloud-Fallback ----------------------------------------------


def test_local_route_unreachable_vm_raises_runtime_error_with_instructions() -> None:
    settings = _settings(mk34_allow_cloud_fallback=False)
    with pytest.raises(RuntimeError, match="VM starten"):
        model_for("scene", settings=settings, route="local")


def test_local_route_unreachable_vm_falls_back_to_cloud_only_with_explicit_opt_in() -> (
    None
):
    settings = _settings(
        mk34_allow_cloud_fallback=True, mk34_model_scene="gemini-3.1-pro-preview"
    )
    with pytest.warns(UserWarning, match="MK34_ALLOW_CLOUD_FALLBACK"):
        result = model_for("scene", settings=settings, route="local")
    assert result == "gemini-3.1-pro-preview"


def test_local_route_fallback_with_local_configured_as_cloud_model_raises() -> None:
    """MK34_MODEL_SCENE=local UND Fallback aktiv, aber kein Cloud-Modell
    konfiguriert -- muss klar scheitern statt ein ungueltiges Modell zu liefern."""
    settings = _settings(mk34_allow_cloud_fallback=True, mk34_model_scene="local")
    with pytest.warns(UserWarning):
        with pytest.raises(RuntimeError, match="Cloud-Fallback nicht moeglich"):
            model_for("scene", settings=settings, route="local")


# --- Rollen-Guard: lokale Route nur fuer "scene" ------------------------------


@pytest.mark.parametrize(
    "role",
    [
        "orchestrator",
        "continuity",
        "research",
        "plot",
        "character",
        "editor",
        "style",
        "classifier",
    ],
)
def test_non_scene_roles_reject_local_route(role: str) -> None:
    settings = _settings()
    with pytest.raises(ValueError, match="ausschliesslich fuer die Rolle"):
        model_for(role, settings=settings, route="local")


def test_scene_config_default_local_without_explicit_route_uses_local_resolution() -> (
    None
):
    """MK34_MODEL_SCENE=local (Config-Force) wirkt auch ohne explizites
    `route`-Argument, z. B. bevor der Classifier (TASK-004) existiert."""
    settings = _settings(mk34_model_scene="local")
    with pytest.raises(RuntimeError, match="Lokales Modell nicht erreichbar"):
        model_for("scene", settings=settings)


def test_scene_config_default_local_with_explicit_cloud_route_raises_clear_error() -> (
    None
):
    settings = _settings(mk34_model_scene="local")
    with pytest.raises(ValueError, match="kein separates Cloud-Modell"):
        model_for("scene", settings=settings, route="cloud")
