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

"""Shared path helpers for `app/tools/*` -- resolves `MK34_BOOK_ROOT` and
guards every filesystem access against path traversal.

Entscheidung E5 (`.claude/plans/README.md`): `books/life_link/` liegt im
Repo-Root, ausserhalb von `mk34-book-agent/`. Kapitel-/Szenennummern kommen
aus Modell-Output und werden deshalb nie direkt in einen Pfad
interpoliert, ohne durch `resolve_within` zu laufen (TASK-001,
Akzeptanzkriterium "Pfad-Traversal wird abgelehnt").
"""

from __future__ import annotations

from pathlib import Path

from app.config import Settings, get_settings

# app/tools/_paths.py -> app/tools -> app -> mk34-book-agent -> <repo root>
_AGENT_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = _AGENT_DIR.parent


def book_root(settings: Settings | None = None) -> Path:
    """Absolute, resolved path to the active book project (`MK34_BOOK_ROOT`)."""
    settings = settings or get_settings()
    return (REPO_ROOT / settings.mk34_book_root).resolve()


def manuscript_dir(settings: Settings | None = None) -> Path:
    """Absolute path to `<book_root>/manuscript/`, created if missing."""
    d = book_root(settings) / "manuscript"
    d.mkdir(parents=True, exist_ok=True)
    return d


def store_dir(settings: Settings | None = None) -> Path:
    """Absolute path to `<book_root>/store/` (read/write for context tools)."""
    return book_root(settings) / "store"


def resolve_within(base: Path, relative_name: str) -> Path:
    """Resolves `relative_name` under `base`, rejecting path traversal.

    Raises:
        ValueError: `relative_name` escapes `base` (e.g. via `..` or an
            absolute path).
    """
    if not relative_name or relative_name in (".", ".."):
        raise ValueError(f"Ungueltiger Dateiname: {relative_name!r}")
    base_resolved = base.resolve()
    candidate = (base_resolved / relative_name).resolve()
    if not candidate.is_relative_to(base_resolved):
        raise ValueError(
            f"Pfad-Traversal abgelehnt: {relative_name!r} liegt ausserhalb von {base_resolved}"
        )
    return candidate
