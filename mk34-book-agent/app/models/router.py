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

"""Central model router: agent role -> tier -> model string -> provider.

This is the *only* place in the codebase allowed to know about model
providers or hardcode model IDs (besides `app/config.py`'s defaults). No
agent module should ever write a raw model string.

Entscheidung E6 (Gemini-first, siehe `.claude/plans/01-fundament-und-kontext/
plan.md`): der Start erfolgt ausschliesslich mit Gemini, ADK-nativ als
Modell-String, ohne LiteLLM-Umweg. Claude (via LiteLLM) und das lokale
Modell bleiben als konfigurierbare Alternativen im Design.

**Lokales Modell (Plan 3, TASK-001):** einzig die Rolle `"scene"` darf auf
die lokale Route (`route="local"`) wechseln -- das unzensierte
`supergemma4-26b-abliterated` via llama.cpp/llama-server, angebunden ueber
SSH-Tunnel (`docs/LOCAL_MODEL_VM_SETUP.md`). `model_for()` selbst kennt
keine ADK-`InvocationContext`/Session-State -- ADKs `Agent.model` wird einmal
bei der Agent-Konstruktion aufgeloest (siehe `LlmAgent.canonical_model`,
kein Callable-Support), waehrend `state["route"]` erst zur Laufzeit vom
Classifier (Plan 3, TASK-004) gesetzt wird. Die Aufloesung von "welches
Modell fuer *diese* Anfrage" ist deshalb zweigeteilt:
- `model_for(role, route=...)` ist die reine, testbare Aufloesungsfunktion
  hier (Rolle + optionale explizite Route -> `str | BaseLlm`).
- Die eigentliche Pro-Turn-Neuaufloesung (State lesen, `model_for` erneut
  aufrufen, eine frische `Agent`-Instanz bauen) uebernimmt der Aufrufer zur
  Laufzeit -- ab TASK-004 ein dediziertes `BaseAgent`-Wrapper-Pattern in
  `app/pipelines/writing.py`, analog zu den bereits vorhandenen
  `BaseAgent`-Subklassen (`_SceneSlotFixture`, `QualityChecker`).

Ohne explizite `route` faellt `model_for("scene", ...)` auf die Cloud-Route
zurueck (`MK34_MODEL_SCENE`) -- das ist Stufe A (Plan 3, TASK-002/003): der
Schreib-Workflow ist ohne VM und ohne Classifier lauffaehig.
"""

from __future__ import annotations

import urllib.error
import urllib.request
import warnings
from typing import TYPE_CHECKING

from app.config import Settings, get_settings

if TYPE_CHECKING:
    from google.adk.models import BaseLlm

# Rolle -> Tier. Jede Rolle, die ein Agent-Modul spaeter braucht, muss hier
# eingetragen sein -- `model_for` lehnt unbekannte Rollen explizit ab statt
# still auf einen Default zurueckzufallen.
ROLE_TIERS: dict[str, str] = {
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

# Einzige Rolle, fuer die die lokale Route ueberhaupt angefordert werden darf
# (von Anfang an entschieden, siehe plan.md -> Ziele).
_LOCAL_ELIGIBLE_ROLE = "scene"

_HEALTH_CHECK_TIMEOUT_SECONDS = 2.0


def local_model_available(settings: Settings | None = None) -> bool:
    """Preflight-Health-Check gegen `MK34_LOCAL_HEALTH_URL`.

    Liefert **immer** `bool` -- niemals eine Exception, egal ob die VM/der
    SSH-Tunnel nicht laeuft, das Netzwerk nicht erreichbar ist oder die URL
    ungueltig konfiguriert ist (Akzeptanzkriterium TASK-001).

    Args:
        settings: Optionale explizite `Settings`-Instanz, primaer fuer Tests.

    Returns:
        `True`, wenn der Health-Endpoint mit einem 2xx-Status antwortet,
        sonst `False`.
    """
    settings = settings or get_settings()
    try:
        with urllib.request.urlopen(
            settings.mk34_local_health_url, timeout=_HEALTH_CHECK_TIMEOUT_SECONDS
        ) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, OSError, ValueError):
        return False


def _resolve_cloud_model(model_id: str, settings: Settings) -> str | BaseLlm:
    """Aufloesung eines Cloud-Modell-Strings (Gemini oder Anthropic)."""
    if model_id.startswith("gemini-"):
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY ist nicht gesetzt. mk34 ist Gemini-first "
                "(Entscheidung E6) -- kein stiller Fallback auf ein anderes "
                "Modell oder Provider. Bitte GEMINI_API_KEY in "
                "mk34-book-agent/.env setzen."
            )
        return model_id  # ADK-nativer Modell-String, kein Wrapper.

    if model_id.startswith("anthropic/"):
        from google.adk.models.lite_llm import LiteLlm

        return LiteLlm(model=model_id)

    raise ValueError(f"Unbekannter Provider fuer Modell-ID {model_id!r}")


def _resolve_local_scene_model(settings: Settings) -> BaseLlm:
    """Aufloesung der lokalen Route fuer die Rolle `scene`.

    Kein stiller Cloud-Fallback (TASK-001-Akzeptanzkriterium): ist die VM
    nicht erreichbar, bricht dieser Aufruf mit einer Handlungsanweisung ab,
    es sei denn `MK34_ALLOW_CLOUD_FALLBACK=true` ist explizit gesetzt -- dann
    wird auf die Cloud-Route (`MK34_MODEL_SCENE`) zurueckgefallen, mit einer
    unuebersehbaren Warnung.
    """
    if local_model_available(settings):
        from google.adk.models.lite_llm import LiteLlm

        return LiteLlm(
            model=settings.mk34_local_model,
            api_base=settings.mk34_local_api_base,
            api_key=settings.mk34_local_api_key,
        )

    if settings.mk34_allow_cloud_fallback:
        warnings.warn(
            "Lokales Modell nicht erreichbar (MK34_LOCAL_HEALTH_URL="
            f"{settings.mk34_local_health_url!r}). MK34_ALLOW_CLOUD_FALLBACK=true "
            "ist gesetzt -- falle auf die Cloud-Route (MK34_MODEL_SCENE) zurueck. "
            "Achtung: eine als 'local' klassifizierte (unzensierte) Szene auf "
            "einem Cloud-Modell endet moeglicherweise in einer Refusal oder "
            "abgeschwaechtem Text (siehe plan.md -> Stufe B).",
            stacklevel=2,
        )
        cloud_model_id = settings.mk34_model_scene
        if cloud_model_id == "local":
            raise RuntimeError(
                "Cloud-Fallback nicht moeglich: MK34_MODEL_SCENE ist selbst auf "
                "'local' gesetzt, es gibt also kein konfiguriertes Cloud-Modell "
                "fuer die Rolle 'scene'. Bitte MK34_MODEL_SCENE auf ein "
                "Cloud-Modell setzen oder die VM starten."
            )
        return _resolve_cloud_model(cloud_model_id, settings)

    raise RuntimeError(
        "Lokales Modell nicht erreichbar (MK34_LOCAL_HEALTH_URL="
        f"{settings.mk34_local_health_url!r}). Kein stiller Cloud-Fallback "
        "(MK34_ALLOW_CLOUD_FALLBACK=false, Default). Handlungsanweisung: VM "
        "starten -- siehe docs/LOCAL_MODEL_VM_SETUP.md "
        "(scripts/start_local_model.sh) bzw. den SSH-Tunnel "
        "'ssh -f -N mk34-vm-tunnel' oeffnen. Alternativ explizit "
        "MK34_ALLOW_CLOUD_FALLBACK=true setzen, um mit Warnung auf die "
        "Cloud-Route auszuweichen."
    )


def model_for(
    role: str, settings: Settings | None = None, route: str | None = None
) -> str | BaseLlm:
    """Resolves an agent role to a concrete model.

    Args:
        role: One of `ROLE_TIERS` (e.g. `"orchestrator"`, `"plot"`, `"scene"`).
        settings: Optional explicit `Settings` instance, mainly for tests.
            Defaults to the process-wide cached settings.
        route: Optional explicit route override (`"local"` or `"cloud"`),
            e.g. `state["route"]` as set by the content classifier (Plan 3,
            TASK-004) or a manual `--model local`/`--model cloud` override.
            Only meaningful for `role="scene"`. Without it, `role="scene"`
            resolves to the cloud tier (`MK34_MODEL_SCENE`), unless
            `MK34_MODEL_SCENE` is itself configured as the literal value
            `"local"` (config-level force, independent of any classifier).

    Returns:
        A bare Gemini model-ID string for `gemini-*` models (ADK-native, no
        wrapper), or a `LiteLlm` instance for `anthropic/*` models or the
        local model.

    Raises:
        ValueError: Unknown role, unrecognized provider prefix, or the local
            route was requested for a role other than `"scene"`.
        RuntimeError: The resolved model is a Gemini model but `GEMINI_API_KEY`
            is not set, or the local route was requested but the VM/tunnel is
            not reachable and no cloud fallback is permitted -- no silent
            fallback to another provider/model in either case.
    """
    if role not in ROLE_TIERS:
        raise ValueError(
            f"Unbekannte Rolle: {role!r}. Bekannte Rollen: {sorted(ROLE_TIERS)}"
        )
    tier = ROLE_TIERS[role]
    settings = settings or get_settings()
    model_id = settings.model_for_tier(tier)

    wants_local = route == "local" or (route is None and model_id == "local")

    if wants_local:
        if role != _LOCAL_ELIGIBLE_ROLE:
            raise ValueError(
                f"Rolle {role!r} darf die lokale Route nicht anfordern -- das "
                f"lokale Modell ist ausschliesslich fuer die Rolle "
                f"{_LOCAL_ELIGIBLE_ROLE!r} vorgesehen (siehe plan.md -> Ziele)."
            )
        return _resolve_local_scene_model(settings)

    if model_id == "local":
        # route wurde explizit auf "cloud" gesetzt, obwohl MK34_MODEL_SCENE
        # (Config-Default) "local" ist -- es gibt kein separates Cloud-Modell
        # fuer diesen Fall, also klarer Fehler statt stiller Annahme.
        raise ValueError(
            "MK34_MODEL_SCENE ist auf 'local' gesetzt, aber route='cloud' wurde "
            "angefordert -- kein separates Cloud-Modell fuer diesen Fall "
            "konfiguriert. Bitte MK34_MODEL_SCENE auf ein Cloud-Modell setzen."
        )

    return _resolve_cloud_model(model_id, settings)
