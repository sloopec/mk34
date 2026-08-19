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
Modell bleiben als konfigurierbare Alternativen im Design -- die
Provider-Erkennung unten ist bereits dafuer vorbereitet, auch wenn in
diesem Plan nur der Gemini-Zweig tatsaechlich benutzt wird.
"""

from __future__ import annotations

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


def model_for(role: str, settings: Settings | None = None) -> str | BaseLlm:
    """Resolves an agent role to a concrete model.

    Args:
        role: One of `ROLE_TIERS` (e.g. `"orchestrator"`, `"plot"`, `"scene"`).
        settings: Optional explicit `Settings` instance, mainly for tests.
            Defaults to the process-wide cached settings.

    Returns:
        A bare Gemini model-ID string for `gemini-*` models (ADK-native, no
        wrapper), or a `LiteLlm` instance for `anthropic/*` models.

    Raises:
        ValueError: Unknown role or unrecognized provider prefix.
        NotImplementedError: The role resolves to the local model, which is
            not wired up in this plan (see `03-szenen-und-lokales-llm/TASK-001`).
        RuntimeError: The resolved model is a Gemini model but `GEMINI_API_KEY`
            is not set -- no silent fallback to another provider/model.
    """
    if role not in ROLE_TIERS:
        raise ValueError(
            f"Unbekannte Rolle: {role!r}. Bekannte Rollen: {sorted(ROLE_TIERS)}"
        )
    tier = ROLE_TIERS[role]

    settings = settings or get_settings()
    model_id = settings.model_for_tier(tier)

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

    if model_id == "local":
        raise NotImplementedError(
            "Lokales LLM ist in diesem Plan nicht angebunden -- siehe "
            "03-szenen-und-lokales-llm/TASK-001 (erweitert diesen Router)."
        )

    raise ValueError(f"Unbekannter Provider fuer Modell-ID {model_id!r}")
