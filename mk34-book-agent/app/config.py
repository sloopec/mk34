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

"""mk34 configuration: model tiers, book-project paths, judge models.

Values are read from the process environment / `.env` via `pydantic-settings`.
This module never opens or inspects `.env` itself -- `pydantic-settings`
loads it the same way `python-dotenv` does elsewhere in `app/`, so secrets
only ever flow into the process environment, never through this codebase's
own I/O (see `mk34-book-agent/CLAUDE.md` -> ".env Handling (STRICT)").

Startwerte siehe `.claude/plans/01-fundament-und-kontext/plan.md` ->
*Konfiguration* und `.claude/plans/README.md` -> *Model-Routing-Matrix*
(Stand 2026-08-17, E6/E7).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# mk34-book-agent/.env -- same file `app/fast_api_app.py`'s `load_dotenv()`
# targets. Loaded here too so `Settings()` also works for entrypoints that
# don't go through `fast_api_app.py` (e.g. `agents-cli run`, plain scripts).
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """mk34 configuration, provider-agnostic.

    Only the model *tier* variables (`MK34_MODEL_*`) are consumed by the
    router (`app/models/router.py`) today. The judge-model and book-path
    variables are already modeled here so later tasks (Plan 2 eval
    grundgeruest, TASK-003 Kontext-Store) can depend on this one Settings
    class instead of re-reading `.env` themselves.
    """

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Model-Router (TASK-002) --------------------------------------
    mk34_model_heavy: str = "gemini-3.1-pro-preview"
    mk34_model_fast: str = "gemini-3.7-flash"
    mk34_model_lite: str = "gemini-3.5-flash-lite"
    mk34_model_scene: str = "gemini-3.1-pro-preview"

    # --- Provider-Credentials -------------------------------------------
    # Nur Praesenz wird geprueft (Router), niemals der Wert geloggt/gelesen.
    gemini_api_key: str | None = None
    anthropic_api_key: str | None = None

    # --- Eval-Judges (Entscheidung E4, ab Plan 2/TASK-003) ---------------
    mk34_judge_model_fast: str = "gemini-3.7-flash"
    mk34_judge_model_craft: str = "gemini-3.1-pro-preview"

    # --- Aktives Buchprojekt (Entscheidung E5, TASK-003) ------------------
    mk34_book_slug: str = "life_link"
    mk34_book_root: str = "books/life_link"

    def model_for_tier(self, tier: str) -> str:
        """Resolves a tier name (`heavy`/`fast`/`lite`/`scene`) to a model ID."""
        field_name = f"mk34_model_{tier}"
        if field_name not in self.__class__.model_fields:
            raise ValueError(f"Unbekannter Modell-Tier: {tier!r}")
        return getattr(self, field_name)


@lru_cache
def get_settings() -> Settings:
    """Process-wide cached settings instance."""
    return Settings()
