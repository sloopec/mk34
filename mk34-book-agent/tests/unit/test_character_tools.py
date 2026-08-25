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

"""Unit tests for `app/tools/characters.py` (TASK-005)."""

from __future__ import annotations

import json

import pytest

from app.tools import characters


@pytest.fixture
def store(tmp_path, monkeypatch):
    store_dir = tmp_path / "store"
    store_dir.mkdir(parents=True)
    (store_dir / "characters.json").write_text(
        json.dumps(
            {
                "characters": [
                    {
                        "name": "David",
                        "role": "Protagonist",
                        "language_register": "Laie",
                        "motivation": "Will verstehen, bevor er handelt.",
                        "arc": "Vom ahnungslosen Ehemann zum Mitstreiter.",
                        "knowledge_state": "Phase 1: ahnungslos.",
                        "first_appearance": "Phase 1",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(characters, "store_dir", lambda: store_dir)
    return store_dir


# --- get_character -----------------------------------------------------------


def test_get_character_returns_full_profile(store) -> None:
    result = characters.get_character("David")
    assert result["status"] == "success"
    assert result["role"] == "Protagonist"
    assert result["language_register"] == "Laie"


def test_get_character_not_found(store) -> None:
    assert characters.get_character("Unbekannt") == {
        "status": "not_found",
        "name": "Unbekannt",
    }


# --- update_character ----------------------------------------------------------


def test_update_character_appends_to_development_log(store) -> None:
    result = characters.update_character("David", "Erfaehrt von der Keimbahn-Mutation.")
    assert result == {"status": "success", "name": "David"}

    data = json.loads((store / "characters.json").read_text(encoding="utf-8"))
    assert data["characters"][0]["development_log"] == [
        "Erfaehrt von der Keimbahn-Mutation."
    ]
    # arc untouched
    assert data["characters"][0]["arc"] == "Vom ahnungslosen Ehemann zum Mitstreiter."


def test_update_character_is_idempotent(store) -> None:
    characters.update_character("David", "Gleiche Entwicklung.")
    characters.update_character("David", "Gleiche Entwicklung.")

    data = json.loads((store / "characters.json").read_text(encoding="utf-8"))
    assert data["characters"][0]["development_log"] == ["Gleiche Entwicklung."]


def test_update_character_not_found(store) -> None:
    assert characters.update_character("Unbekannt", "x") == {
        "status": "not_found",
        "name": "Unbekannt",
    }


# --- get_character_arc -------------------------------------------------------------


def test_get_character_arc_includes_development_log(store) -> None:
    characters.update_character("David", "Neue Erkenntnis.")

    result = characters.get_character_arc("David")

    assert result["status"] == "success"
    assert result["arc"] == "Vom ahnungslosen Ehemann zum Mitstreiter."
    assert result["development_log"] == ["Neue Erkenntnis."]


def test_get_character_arc_not_found(store) -> None:
    assert characters.get_character_arc("Unbekannt")["status"] == "not_found"


# --- get_knowledge_state ---------------------------------------------------------


def test_get_knowledge_state_returns_field(store) -> None:
    result = characters.get_knowledge_state("David", 3)
    assert result["status"] == "success"
    assert result["chapter"] == 3
    assert result["knowledge_state"] == "Phase 1: ahnungslos."


def test_get_knowledge_state_not_found(store) -> None:
    assert characters.get_knowledge_state("Unbekannt", 1)["status"] == "not_found"


def test_get_knowledge_state_chapter_state_is_none_without_entries(store) -> None:
    result = characters.get_knowledge_state("David", 5)
    assert result["chapter_state"] is None


# --- update_character_state / get_knowledge_state (TASK-012) -----------------------


def test_update_character_state_writes_chapter_entry(store) -> None:
    result = characters.update_character_state(
        "David",
        chapter=3,
        location="Kommune",
        knowledge="Kennt die Diagnose.",
        emotional_state="verunsichert",
        infection_status="nicht_optimiert",
    )
    assert result == {"status": "success", "name": "David", "chapter": 3}

    data = json.loads((store / "characters.json").read_text(encoding="utf-8"))
    assert data["characters"][0]["state_by_chapter"]["3"] == {
        "location": "Kommune",
        "knowledge": "Kennt die Diagnose.",
        "emotional_state": "verunsichert",
        "infection_status": "nicht_optimiert",
    }


def test_update_character_state_not_found(store) -> None:
    assert characters.update_character_state("Unbekannt", chapter=1) == {
        "status": "not_found",
        "name": "Unbekannt",
    }


def test_get_knowledge_state_falls_back_to_latest_earlier_chapter(store) -> None:
    characters.update_character_state("David", chapter=2, knowledge="Weiss von X.")
    characters.update_character_state("David", chapter=5, knowledge="Weiss von Y.")

    result = characters.get_knowledge_state("David", 4)

    assert result["chapter_state"]["chapter"] == 2
    assert result["chapter_state"]["knowledge"] == "Weiss von X."


def test_get_knowledge_state_uses_exact_chapter_when_available(store) -> None:
    characters.update_character_state("David", chapter=2, knowledge="Weiss von X.")
    characters.update_character_state("David", chapter=4, knowledge="Weiss von Y.")

    result = characters.get_knowledge_state("David", 4)

    assert result["chapter_state"]["chapter"] == 4
    assert result["chapter_state"]["knowledge"] == "Weiss von Y."


# --- check_knowledge_prerequisite ---------------------------------------------------


def test_check_knowledge_prerequisite_ok_when_knowledge_present(store) -> None:
    characters.update_character_state(
        "David", chapter=2, knowledge="Kennt die Diagnose."
    )

    result = characters.check_knowledge_prerequisite("David", 3, "Diagnose")

    assert result["status"] == "ok"


def test_check_knowledge_prerequisite_violation_when_knowledge_missing(store) -> None:
    characters.update_character_state(
        "David", chapter=2, knowledge="Kennt nur den Ausbruch."
    )

    result = characters.check_knowledge_prerequisite("David", 3, "Keimbahn-Mutation")

    assert result["status"] == "violation"


def test_check_knowledge_prerequisite_unknown_without_chapter_state(store) -> None:
    result = characters.check_knowledge_prerequisite("David", 1, "irgendwas")
    assert result["status"] == "unknown"


def test_check_knowledge_prerequisite_not_found(store) -> None:
    result = characters.check_knowledge_prerequisite("Unbekannt", 1, "x")
    assert result["status"] == "not_found"
