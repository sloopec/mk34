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

"""Unit tests for `read_chapter_summaries` and `update_plot_outline`
(app/tools/context_loader.py, TASK-004)."""

from __future__ import annotations

import json

import pytest

from app.tools import context_loader, manuscript


@pytest.fixture
def store(tmp_path, monkeypatch):
    store_dir = tmp_path / "store"
    manuscript_dir = tmp_path / "manuscript"
    store_dir.mkdir(parents=True)
    manuscript_dir.mkdir(parents=True)
    (store_dir / "plot_outline.json").write_text(
        json.dumps({"phases": [{"id": 2, "title": "Die Recherche"}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(context_loader, "store_dir", lambda: store_dir)
    monkeypatch.setattr(manuscript, "manuscript_dir", lambda: manuscript_dir)
    return store_dir


# --- read_chapter_summaries -------------------------------------------------


def test_read_chapter_summaries_empty_manuscript(store) -> None:
    assert context_loader.read_chapter_summaries() == {
        "status": "success",
        "summaries": [],
    }


def test_read_chapter_summaries_returns_snippet_per_chapter(store) -> None:
    manuscript.write_scene(1, 1, "Ein " * 200)  # long text, snippet must be capped

    result = context_loader.read_chapter_summaries()

    assert result["status"] == "success"
    assert len(result["summaries"]) == 1
    entry = result["summaries"][0]
    assert entry["chapter"] == 1
    assert len(entry["summary"]) <= 300


# --- update_plot_outline -----------------------------------------------------


def _beat(**overrides) -> dict:
    base = {
        "chapter": 3,
        "scene": 1,
        "pov_character": "David",
        "location": "Kommune",
        "beat": "David trifft Sarah.",
        "turning_point": True,
        "tension_level": 7,
        "characters_present": ["David", "Dr. Sarah Lin"],
    }
    base.update(overrides)
    return base


def test_update_plot_outline_appends_without_destroying_phases(store) -> None:
    result = context_loader.update_plot_outline(**_beat())

    assert result == {"status": "success", "chapter": 3, "scene": 1}
    data = json.loads((store / "plot_outline.json").read_text(encoding="utf-8"))
    assert data["phases"] == [{"id": 2, "title": "Die Recherche"}]  # untouched
    assert len(data["scene_beats"]) == 1
    assert data["scene_beats"][0]["pov_character"] == "David"


def test_update_plot_outline_is_idempotent_for_same_chapter_scene(store) -> None:
    context_loader.update_plot_outline(**_beat(beat="Erste Fassung."))
    context_loader.update_plot_outline(**_beat(beat="Ueberarbeitete Fassung."))

    data = json.loads((store / "plot_outline.json").read_text(encoding="utf-8"))
    assert len(data["scene_beats"]) == 1
    assert data["scene_beats"][0]["beat"] == "Ueberarbeitete Fassung."


def test_update_plot_outline_appends_a_second_distinct_beat(store) -> None:
    context_loader.update_plot_outline(**_beat(scene=1))
    context_loader.update_plot_outline(**_beat(scene=2))

    data = json.loads((store / "plot_outline.json").read_text(encoding="utf-8"))
    assert len(data["scene_beats"]) == 2


def test_update_plot_outline_clamps_tension_level(store) -> None:
    context_loader.update_plot_outline(**_beat(tension_level=99))
    data = json.loads((store / "plot_outline.json").read_text(encoding="utf-8"))
    assert data["scene_beats"][0]["tension_level"] == 10

    context_loader.update_plot_outline(**_beat(tension_level=-5))
    data = json.loads((store / "plot_outline.json").read_text(encoding="utf-8"))
    assert data["scene_beats"][0]["tension_level"] == 1
