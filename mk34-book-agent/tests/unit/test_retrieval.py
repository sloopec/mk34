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

"""Unit tests for `app/retrieval/index.py`, `query.py`, `app/tools/consistency.py`
(TASK-011). Fully offline -- stdlib `sqlite3` only, no network call anywhere
in the retrieval path."""

from __future__ import annotations

import json
import socket

import pytest

from app.retrieval import index as index_module
from app.retrieval import query as query_module
from app.tools import consistency, manuscript


@pytest.fixture
def book(tmp_path, monkeypatch):
    store_dir = tmp_path / "store"
    manuscript_dir = tmp_path / "manuscript"
    index_file = tmp_path / ".index" / "manuscript.db"
    store_dir.mkdir(parents=True)
    manuscript_dir.mkdir(parents=True)

    (store_dir / "characters.json").write_text(
        json.dumps(
            {
                "characters": [
                    {"name": "David"},
                    {"name": "Dr. Sarah Lin"},
                ]
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(manuscript, "manuscript_dir", lambda: manuscript_dir)
    monkeypatch.setattr(manuscript, "store_dir", lambda: store_dir)
    monkeypatch.setattr(index_module, "store_dir", lambda: store_dir)
    monkeypatch.setattr(index_module, "index_path", lambda: index_file)
    monkeypatch.setattr(query_module, "index_path", lambda: index_file)

    return {"store": store_dir, "manuscript": manuscript_dir, "index": index_file}


def _block_network(monkeypatch):
    """Fails the test if any code under test opens a network socket."""

    def _guard(*args, **kwargs):
        raise AssertionError("Netzwerkaufruf im Retrieval-Pfad entdeckt!")

    monkeypatch.setattr(socket.socket, "connect", _guard)


# --- build_index ---------------------------------------------------------------


def test_build_index_empty_manuscript_returns_zero_chunks(book) -> None:
    result = index_module.build_index()
    assert result == {
        "status": "success",
        "chunks_indexed": 0,
        "path": str(book["index"]),
    }
    assert book["index"].exists()


def test_build_index_chunks_by_scene(book) -> None:
    manuscript.write_scene(1, 1, "David traf David in einer Szene mit Sarah.")
    manuscript.write_scene(1, 2, "Eine zweite Szene ohne bekannte Figuren.")
    manuscript.write_scene(2, 1, "Kapitel zwei, Szene eins.")

    result = index_module.build_index()

    assert result["status"] == "success"
    assert result["chunks_indexed"] == 3


def test_build_index_extracts_timestamp(book) -> None:
    manuscript.write_scene(1, 1, "20:43 Uhr | Markus klopfte an die Tuer.")
    index_module.build_index()

    hits = query_module.query_relevant_passages(entities=["Markus"], k=5)
    assert hits
    assert hits[0]["timestamp"] == "20:43 Uhr"


def test_build_index_falls_back_to_character_mention_detection(book) -> None:
    manuscript.write_scene(1, 1, "David sprach mit Dr. Sarah Lin ueber die Naniten.")
    index_module.build_index()

    hits = query_module.query_relevant_passages(entities=["David"], k=5)
    assert hits
    assert set(hits[0]["characters_present"]) == {"David", "Dr. Sarah Lin"}


def test_build_index_is_idempotent(book) -> None:
    manuscript.write_scene(1, 1, "Text.")
    index_module.build_index()
    result = index_module.build_index()  # rebuild -- must not duplicate
    assert result["chunks_indexed"] == 1


def test_build_index_uses_scene_beat_metadata_when_present(book) -> None:
    manuscript.write_scene(3, 1, "David erreicht die Kommune.")
    (book["store"] / "plot_outline.json").write_text(
        json.dumps(
            {
                "scene_beats": [
                    {
                        "chapter": 3,
                        "scene": 1,
                        "pov_character": "David",
                        "location": "Kommune",
                        "characters_present": ["David", "Dr. Sarah Lin"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    index_module.build_index()

    hits = query_module.query_relevant_passages(entities=["David"], k=5)
    assert hits[0]["pov_character"] == "David"
    assert hits[0]["location"] == "Kommune"


# --- query_relevant_passages -----------------------------------------------------


def test_query_returns_empty_list_when_index_missing(book) -> None:
    assert query_module.query_relevant_passages(entities=["David"]) == []


def test_query_returns_empty_list_for_no_entities(book) -> None:
    manuscript.write_scene(1, 1, "Text.")
    index_module.build_index()
    assert query_module.query_relevant_passages(entities=[]) == []


def test_query_ranks_by_relevance(book) -> None:
    manuscript.write_scene(
        1, 1, "Elena spricht kein Wort, ihr Gesicht ist ausdruckslos."
    )
    manuscript.write_scene(1, 2, "David geht spazieren, unabhaengig von allem.")
    index_module.build_index()

    hits = query_module.query_relevant_passages(entities=["Elena"], k=5)

    assert len(hits) == 1
    assert hits[0]["scene"] == 1


def test_query_metadata_filter_by_character(book) -> None:
    manuscript.write_scene(1, 1, "Sarah erklaert Naniten.")
    manuscript.write_scene(1, 2, "David erklaert Naniten.")
    index_module.build_index()

    hits = query_module.query_relevant_passages(
        entities=["Naniten"], k=5, characters=["David"]
    )

    assert all("David" in hit["characters_present"] for hit in hits)


def test_query_sanitizes_fts5_special_characters(book) -> None:
    manuscript.write_scene(1, 1, "Text ueber die Firma OmniCorp*.")
    index_module.build_index()

    # Would raise sqlite3.OperationalError if unescaped -- '*' is an FTS5 prefix operator.
    result = query_module.query_relevant_passages(
        entities=['OmniCorp* OR "; DROP TABLE']
    )
    assert isinstance(result, list)


def test_retrieval_path_never_opens_a_network_socket(book, monkeypatch) -> None:
    _block_network(monkeypatch)
    manuscript.write_scene(1, 1, "David trifft Sarah.")
    index_module.build_index()
    query_module.query_relevant_passages(entities=["David"])
    consistency.check_consistency("David trifft Sarah erneut.", ["Sarah"])


# --- check_consistency -----------------------------------------------------------


def test_check_consistency_returns_relevant_passages(book) -> None:
    manuscript.write_scene(2, 1, "David erhaelt von Dr. Aris die Diagnose.")
    index_module.build_index()

    result = consistency.check_consistency(
        "David erzaehlt Sarah von der Diagnose.", ["David"]
    )

    assert result["status"] == "success"
    assert "David" in result["query_entities"]
    assert any(p["chapter"] == 2 for p in result["relevant_passages"])


def test_check_consistency_empty_index_returns_empty_passages(book) -> None:
    result = consistency.check_consistency("Ganz neuer Text.", ["Unbekannt"])
    assert result["status"] == "success"
    assert result["relevant_passages"] == []
