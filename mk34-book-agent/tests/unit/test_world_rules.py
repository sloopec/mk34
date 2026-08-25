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

"""Unit tests for `app/tools/consistency.py::validate_world_rules` (TASK-013)."""

from __future__ import annotations

import json

import pytest

from app.tools import characters as characters_module
from app.tools import consistency


@pytest.fixture
def store(tmp_path, monkeypatch):
    store_dir = tmp_path / "store"
    store_dir.mkdir(parents=True)
    (store_dir / "characters.json").write_text(
        json.dumps(
            {
                "characters": [
                    {
                        "name": "Dr. Sarah Lin",
                        "language_register": (
                            "Praezise, wissenschaftlich -- 'Naniten', 'Assembler', "
                            "'Emergenz'. Korrigiert Davids Laienbegriffe aktiv."
                        ),
                    },
                    {
                        "name": "David",
                        "language_register": (
                            "Laie -- nutzt umgangssprachliche, technisch unpraezise "
                            "Begriffe wie 'Nanobots', 'Chips', 'Programmierung'."
                        ),
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(characters_module, "store_dir", lambda: store_dir)
    monkeypatch.setattr(consistency, "get_character", characters_module.get_character)
    return store_dir


# --- Regel 1: kein zentraler Server --------------------------------------------------


def test_detects_central_server_violation(store) -> None:
    result = consistency.validate_world_rules(
        "Die Naniten meldeten sich beim zentralen Server, der ihre naechsten Befehle "
        "festlegte."
    )
    rule_ids = {v["rule_id"] for v in result["violations"]}
    assert 1 in rule_ids


def test_no_central_server_violation_for_clean_text(store) -> None:
    result = consistency.validate_world_rules(
        "Die Naniten kommunizieren nur bei koerperlicher Naehe."
    )
    assert result == {"status": "success", "violations": []}


# --- Regel 5: keine mechanischen "Metallmaennchen" -----------------------------------


def test_detects_mechanical_robot_violation(store) -> None:
    result = consistency.validate_world_rules(
        "Winzige Metallmaennchen mit Zangen krabbelten durch seine Blutbahn."
    )
    rule_ids = {v["rule_id"] for v in result["violations"]}
    assert 5 in rule_ids


def test_detects_mechanical_robot_violation_with_umlaut_spelling(store) -> None:
    result = consistency.validate_world_rules(
        "Winzige Metallmännchen mit Zangen krabbelten durch seine Blutbahn."
    )
    rule_ids = {v["rule_id"] for v in result["violations"]}
    assert 5 in rule_ids


# --- Regel 6: Terminologie-Konsistenz, figurenbezogen --------------------------------


def test_detects_terminology_violation_for_scientist_using_laypeople_term(
    store,
) -> None:
    text = "Sarah sagte: 'Die Nanobots sind ausser Kontrolle.'"
    result = consistency.validate_world_rules(text, characters=["Dr. Sarah Lin"])
    rule_ids = {v["rule_id"] for v in result["violations"]}
    assert 6 in rule_ids


def test_no_terminology_violation_when_scientist_uses_correct_term(store) -> None:
    text = "Sarah sagte: 'Die Naniten sind ausser Kontrolle.'"
    result = consistency.validate_world_rules(text, characters=["Dr. Sarah Lin"])
    assert result["violations"] == []


def test_no_terminology_violation_for_layperson_using_laypeople_term(store) -> None:
    text = "David sagte: 'Meine Nanobots spinnen total.'"
    result = consistency.validate_world_rules(text, characters=["David"])
    assert result["violations"] == []


def test_terminology_check_falls_back_to_mentioned_characters(store) -> None:
    text = "Sarah erklaerte: 'Die Nanobots reagieren nicht mehr.'"
    result = consistency.validate_world_rules(text)
    rule_ids = {v["rule_id"] for v in result["violations"]}
    assert 6 in rule_ids


# --- Kombinierte Faelle ----------------------------------------------------------------


def test_multiple_violations_are_all_reported(store) -> None:
    text = (
        "Winzige Metallmaennchen meldeten sich beim zentralen Server. "
        "Sarah sagte: 'Die Nanobots gehorchen niemandem mehr.'"
    )
    result = consistency.validate_world_rules(text, characters=["Dr. Sarah Lin"])
    rule_ids = {v["rule_id"] for v in result["violations"]}
    assert rule_ids == {1, 5, 6}


def test_each_violation_has_evidence_and_explanation(store) -> None:
    result = consistency.validate_world_rules("Die Naniten meldeten sich beim Server.")
    assert result["violations"]
    for violation in result["violations"]:
        assert violation["evidence"]
        assert violation["explanation"]
        assert isinstance(violation["rule_id"], int)


# --- check_consistency traegt world_rule_violations mit -----------------------------


def test_check_consistency_includes_world_rule_violations(store, monkeypatch, tmp_path):
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir(parents=True)
    index_file = tmp_path / ".index" / "manuscript.db"

    from app.retrieval import index as index_module
    from app.retrieval import query as query_module
    from app.tools import manuscript as manuscript_module
    from app.tools import timeline as timeline_module

    monkeypatch.setattr(manuscript_module, "manuscript_dir", lambda: manuscript_dir)
    monkeypatch.setattr(manuscript_module, "store_dir", lambda: store)
    monkeypatch.setattr(index_module, "store_dir", lambda: store)
    monkeypatch.setattr(index_module, "index_path", lambda: index_file)
    monkeypatch.setattr(query_module, "index_path", lambda: index_file)
    monkeypatch.setattr(timeline_module, "store_dir", lambda: store)

    result = consistency.check_consistency(
        "Die Naniten meldeten sich beim zentralen Server.", []
    )

    assert "world_rule_violations" in result
    rule_ids = {v["rule_id"] for v in result["world_rule_violations"]}
    assert 1 in rule_ids


def test_check_consistency_empty_world_rule_violations_for_clean_text(
    store, monkeypatch, tmp_path
):
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir(parents=True)
    index_file = tmp_path / ".index" / "manuscript.db"

    from app.retrieval import index as index_module
    from app.retrieval import query as query_module
    from app.tools import manuscript as manuscript_module
    from app.tools import timeline as timeline_module

    monkeypatch.setattr(manuscript_module, "manuscript_dir", lambda: manuscript_dir)
    monkeypatch.setattr(manuscript_module, "store_dir", lambda: store)
    monkeypatch.setattr(index_module, "store_dir", lambda: store)
    monkeypatch.setattr(index_module, "index_path", lambda: index_file)
    monkeypatch.setattr(query_module, "index_path", lambda: index_file)
    monkeypatch.setattr(timeline_module, "store_dir", lambda: store)

    result = consistency.check_consistency("Ein voellig unauffaelliger Satz.", [])

    assert result["world_rule_violations"] == []
