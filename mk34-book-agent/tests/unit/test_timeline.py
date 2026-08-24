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

"""Unit tests for `app/tools/timeline.py` (TASK-012)."""

from __future__ import annotations

import json

import pytest

from app.tools import timeline


@pytest.fixture
def store(tmp_path, monkeypatch):
    store_dir = tmp_path / "store"
    store_dir.mkdir(parents=True)
    monkeypatch.setattr(timeline, "store_dir", lambda: store_dir)
    return store_dir


# --- extract_timestamp --------------------------------------------------------------


def test_extract_timestamp_finds_hh_mm_uhr() -> None:
    assert (
        timeline.extract_timestamp("20:43 Uhr | Markus klopfte an die Tuer.")
        == "20:43 Uhr"
    )


def test_extract_timestamp_empty_when_not_found() -> None:
    assert timeline.extract_timestamp("Kein Zeitstempel hier.") == ""


# --- append_event / read_timeline ----------------------------------------------------


def test_append_event_writes_and_reads_back(store) -> None:
    result = timeline.append_event(
        chapter=1,
        scene=1,
        timestamp="20:43 Uhr",
        location="Sophies Wohnung",
        description="Markus klopft an.",
        characters=["Markus", "Sophie"],
    )
    assert result == {"status": "success", "chapter": 1, "scene": 1, "event_count": 1}

    data = json.loads((store / "timeline.json").read_text(encoding="utf-8"))
    assert data["events"][0]["timestamp"] == "20:43 Uhr"
    assert data["events"][0]["characters"] == ["Markus", "Sophie"]


def test_append_event_is_idempotent_per_scene(store) -> None:
    timeline.append_event(1, 1, "20:00 Uhr", "Ort A", "Erste Fassung.", ["David"])
    timeline.append_event(
        1, 1, "20:05 Uhr", "Ort A", "Ueberschriebene Fassung.", ["David"]
    )

    result = timeline.read_timeline()
    assert len(result["events"]) == 1
    assert result["events"][0]["description"] == "Ueberschriebene Fassung."


def test_read_timeline_filters_by_chapter_range(store) -> None:
    timeline.append_event(1, 1, "", "", "Kapitel 1.", [])
    timeline.append_event(2, 1, "", "", "Kapitel 2.", [])
    timeline.append_event(3, 1, "", "", "Kapitel 3.", [])

    result = timeline.read_timeline(from_chapter=2, to_chapter=3)

    chapters = [e["chapter"] for e in result["events"]]
    assert chapters == [2, 3]


def test_read_timeline_sorted_by_chapter_and_scene(store) -> None:
    timeline.append_event(2, 1, "", "", "b", [])
    timeline.append_event(1, 2, "", "", "a2", [])
    timeline.append_event(1, 1, "", "", "a1", [])

    result = timeline.read_timeline()

    assert [(e["chapter"], e["scene"]) for e in result["events"]] == [
        (1, 1),
        (1, 2),
        (2, 1),
    ]


# --- validate_chronology: Zeitspruenge ------------------------------------------------


def test_validate_chronology_detects_artificial_time_jump(store) -> None:
    # Kuenstlich eingebauter Zeitsprung: Szene 2 folgt direkt auf Szene 1 (kein
    # Tageswechsel-Hinweis in der Beschreibung), aber die Uhrzeit laeuft zurueck.
    timeline.append_event(
        1, 1, "20:43 Uhr", "Sophies Wohnung", "Markus klopft an.", ["Markus"]
    )
    timeline.append_event(
        1, 2, "08:00 Uhr", "Sophies Wohnung", "Sie reden weiter.", ["Markus"]
    )

    result = timeline.validate_chronology()

    assert len(result["time_jumps"]) == 1
    jump = result["time_jumps"][0]
    assert jump["type"] == "Zeitsprung"
    assert jump["from"]["timestamp"] == "20:43 Uhr"
    assert jump["to"]["timestamp"] == "08:00 Uhr"


def test_validate_chronology_no_time_jump_with_day_change_hint(store) -> None:
    timeline.append_event(
        1, 1, "20:43 Uhr", "Sophies Wohnung", "Markus klopft an.", ["Markus"]
    )
    timeline.append_event(
        1,
        2,
        "08:00 Uhr",
        "Sophies Wohnung",
        "Am naechsten Tag wachen sie auf.",
        ["Markus"],
    )

    result = timeline.validate_chronology()

    assert result["time_jumps"] == []


def test_validate_chronology_no_jump_for_forward_moving_time(store) -> None:
    timeline.append_event(1, 1, "08:00 Uhr", "Ort A", "Start.", ["David"])
    timeline.append_event(1, 2, "08:30 Uhr", "Ort A", "Weiter.", ["David"])

    result = timeline.validate_chronology()

    assert result["time_jumps"] == []


# --- validate_chronology: Parallelitaets-Konflikte -------------------------------------


def test_validate_chronology_detects_parallel_location_conflict(store) -> None:
    # Kuenstlich eingebauter Parallelitaets-Konflikt: David ist laut Timeline zur
    # exakt selben Uhrzeit an zwei verschiedenen Orten.
    timeline.append_event(1, 1, "20:00 Uhr", "Kommune", "David bei Sarah.", ["David"])
    timeline.append_event(
        1, 2, "20:00 Uhr", "Davids Wohnung", "David zu Hause.", ["David"]
    )

    result = timeline.validate_chronology()

    assert len(result["parallel_conflicts"]) == 1
    conflict = result["parallel_conflicts"][0]
    assert conflict["type"] == "Parallelitaets-Konflikt"
    assert conflict["character"] == "David"
    assert conflict["timestamp"] == "20:00 Uhr"
    assert set(conflict["locations"]) == {"Kommune", "Davids Wohnung"}


def test_validate_chronology_no_conflict_same_location_same_time(store) -> None:
    timeline.append_event(
        1, 1, "20:00 Uhr", "Kommune", "David und Sarah reden.", ["David", "Sarah"]
    )

    result = timeline.validate_chronology()

    assert result["parallel_conflicts"] == []


def test_validate_chronology_empty_timeline_returns_no_conflicts(store) -> None:
    result = timeline.validate_chronology()
    assert result == {"status": "success", "time_jumps": [], "parallel_conflicts": []}
