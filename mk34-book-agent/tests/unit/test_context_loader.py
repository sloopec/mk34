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

"""Unit tests for `app/tools/context_loader.py` against a fixture store."""

from __future__ import annotations

import json

import pytest

from app.tools import context_loader


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Isolates every test against a throwaway store under tmp_path."""
    store_dir = tmp_path / "store"
    store_dir.mkdir(parents=True)

    (store_dir / "world_bible.md").write_text(
        "# World Bible\n\n1. Kein zentraler Server.\n", encoding="utf-8"
    )
    (store_dir / "style_guide.md").write_text(
        "# Style Guide\n\nDavid = Laie.\n", encoding="utf-8"
    )
    (store_dir / "characters.json").write_text(
        json.dumps(
            {
                "characters": [
                    {"name": "David", "language_register": "Laie"},
                    {"name": "Dr. Sarah Lin", "language_register": "wissenschaftlich"},
                ]
            }
        ),
        encoding="utf-8",
    )
    (store_dir / "plot_outline.json").write_text(
        json.dumps(
            {
                "phases": [
                    {
                        "id": 2,
                        "title": "Die Recherche",
                        "focus_characters": ["David", "Dr. Aris"],
                        "summary": "David erhaelt die Diagnose.",
                        "beats": ["Aris zeigt David das Blutbild."],
                        "example_scenes": ["C"],
                    }
                ],
                "scene_beats": [
                    {
                        "chapter": 3,
                        "scene": 1,
                        "pov_character": "David",
                        "beat": "David trifft Sarah zum ersten Mal in der Kommune.",
                        "characters_present": ["David", "Dr. Sarah Lin"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(context_loader, "store_dir", lambda: store_dir)
    return store_dir


class _FakeToolContext:
    def __init__(self):
        self.state = {}


# --- load_world_bible / load_style_guide ------------------------------------


def test_load_world_bible_returns_text(store) -> None:
    result = context_loader.load_world_bible()
    assert result["status"] == "success"
    assert "zentraler Server" in result["text"]


def test_load_world_bible_not_found(store) -> None:
    (store / "world_bible.md").unlink()
    assert context_loader.load_world_bible() == {"status": "not_found"}


def test_load_style_guide_returns_text(store) -> None:
    result = context_loader.load_style_guide()
    assert result["status"] == "success"
    assert "David = Laie." in result["text"]


# --- load_plot_outline -------------------------------------------------------


def test_load_plot_outline_returns_matching_phase(store) -> None:
    result = context_loader.load_plot_outline(2)
    assert result["status"] == "success"
    assert result["title"] == "Die Recherche"
    assert result["focus_characters"] == ["David", "Dr. Aris"]


def test_load_plot_outline_not_found(store) -> None:
    assert context_loader.load_plot_outline(99) == {"status": "not_found", "act": 99}


# --- load_scene_context -------------------------------------------------------


def test_load_scene_context_combines_beat_characters_and_world_rules(store) -> None:
    tool_context = _FakeToolContext()

    result = context_loader.load_scene_context(3, 1, tool_context)

    assert result["status"] == "success"
    assert result["beat"]["beat"] == "David trifft Sarah zum ersten Mal in der Kommune."
    names = {c["name"] for c in result["characters"]}
    assert names == {"David", "Dr. Sarah Lin"}
    assert "zentraler Server" in result["world_rules"]
    assert "David = Laie." in result["style_guide"]


def test_load_scene_context_writes_state_via_scene_context_key(store) -> None:
    tool_context = _FakeToolContext()

    result = context_loader.load_scene_context(3, 1, tool_context)

    assert tool_context.state["scene_context"] == result


def test_load_scene_context_beat_is_none_when_not_yet_written(store) -> None:
    tool_context = _FakeToolContext()

    result = context_loader.load_scene_context(9, 9, tool_context)

    assert result["status"] == "success"
    assert result["beat"] is None
    assert result["characters"] == []
