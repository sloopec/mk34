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

"""Unit tests for `app/tools/manuscript.py` against a fixture manuscript.

Only code-correctness is asserted here (file I/O, marker parsing, path
safety) -- no LLM output is checked. See `mk34-book-agent/CLAUDE.md`.
"""

from __future__ import annotations

import json

import pytest

from app.tools import manuscript


@pytest.fixture
def book(tmp_path, monkeypatch):
    """Isolates every test against a throwaway book root under tmp_path."""
    book_dir = tmp_path / "books" / "test_book"
    (book_dir / "store").mkdir(parents=True)
    (book_dir / "manuscript").mkdir(parents=True)
    (book_dir / "store" / "characters.json").write_text(
        json.dumps(
            {
                "characters": [
                    {"name": "Dr. Sarah Lin"},
                    {"name": "David"},
                ]
            }
        ),
        encoding="utf-8",
    )

    # manuscript.py resolves paths via app.tools._paths, which anchors
    # MK34_BOOK_ROOT at the repo root two levels above mk34-book-agent/.
    # Simplest isolation: monkeypatch the resolved book_root directly.
    monkeypatch.setattr(manuscript, "manuscript_dir", lambda: book_dir / "manuscript")
    monkeypatch.setattr(manuscript, "store_dir", lambda: book_dir / "store")
    return book_dir


# --- read_manuscript ---------------------------------------------------------


def test_read_manuscript_not_found(book) -> None:
    result = manuscript.read_manuscript(1)
    assert result == {"status": "not_found", "chapter": 1}


def test_read_manuscript_returns_full_text_and_scene_count(book) -> None:
    manuscript.write_scene(1, 1, "Erste Szene.")
    manuscript.write_scene(1, 2, "Zweite Szene.")

    result = manuscript.read_manuscript(1)

    assert result["status"] == "success"
    assert result["scene_count"] == 2
    assert "Erste Szene." in result["text"]
    assert "Zweite Szene." in result["text"]


# --- write_scene --------------------------------------------------------------


def test_write_scene_creates_missing_chapter_file(book) -> None:
    result = manuscript.write_scene(2, 1, "Neuer Text.")

    assert result == {"status": "success", "chapter": 2, "scene": 1, "scene_count": 1}
    assert (book / "manuscript" / "chapter_02.md").exists()


def test_write_scene_replaces_existing_scene_idempotently(book) -> None:
    manuscript.write_scene(3, 1, "Version A.")
    manuscript.write_scene(3, 2, "Unveraendert.")

    result = manuscript.write_scene(3, 1, "Version B.")

    assert result["status"] == "success"
    assert result["scene_count"] == 2  # scene 2 preserved, not duplicated
    text = manuscript.read_manuscript(3)["text"]
    assert "Version A." not in text
    assert "Version B." in text
    assert "Unveraendert." in text


def test_write_scene_never_silently_overwrites_whole_chapter(book) -> None:
    manuscript.write_scene(4, 1, "Szene eins bleibt.")
    manuscript.write_scene(4, 3, "Szene drei ist neu.")

    result = manuscript.read_manuscript(4)

    assert result["scene_count"] == 2
    assert "Szene eins bleibt." in result["text"]
    assert "Szene drei ist neu." in result["text"]


def test_write_scene_rejects_empty_text(book) -> None:
    result = manuscript.write_scene(1, 1, "   ")
    assert result["status"] == "error"


# --- list_chapters -------------------------------------------------------------


def test_list_chapters_reports_scene_counts(book) -> None:
    manuscript.write_scene(1, 1, "A")
    manuscript.write_scene(2, 1, "B")
    manuscript.write_scene(2, 2, "C")

    result = manuscript.list_chapters()

    assert result["status"] == "success"
    assert result["chapters"] == [
        {"chapter": 1, "scene_count": 1},
        {"chapter": 2, "scene_count": 2},
    ]


def test_list_chapters_empty_manuscript(book) -> None:
    assert manuscript.list_chapters() == {"status": "success", "chapters": []}


# --- chapter_stats ---------------------------------------------------------------


def test_chapter_stats_reports_word_count_and_characters(book) -> None:
    manuscript.write_scene(
        1, 1, "Dr. Sarah Lin sprach mit David ueber die Naniten im Blut."
    )

    result = manuscript.chapter_stats(1)

    assert result["status"] == "success"
    assert result["scene_count"] == 1
    # word_count includes the auto-generated chapter header, so only assert
    # it covers at least the scene's own words (10), not an exact count.
    assert result["word_count"] >= 10
    assert set(result["characters_present"]) == {"Dr. Sarah Lin", "David"}


def test_chapter_stats_not_found(book) -> None:
    assert manuscript.chapter_stats(99) == {"status": "not_found", "chapter": 99}


# --- write_scene_draft (TASK-008) -----------------------------------------------


def test_write_scene_draft_creates_file_with_verdict_frontmatter(book) -> None:
    result = manuscript.write_scene_draft(
        chapter=5,
        scene=1,
        text="Unfertiger Text.",
        verdict={"grade": "needs_revision", "issues": ["Registerbruch"]},
    )

    assert result["status"] == "success"
    draft_path = book / "manuscript" / "kapitel_05.scene_1.draft.md"
    assert draft_path.exists()
    content = draft_path.read_text(encoding="utf-8")
    assert "status: draft" in content
    assert "grade: needs_revision" in content
    assert "Registerbruch" in content
    assert "Unfertiger Text." in content


def test_write_scene_draft_never_touches_the_final_chapter_file(book) -> None:
    manuscript.write_scene_draft(
        chapter=5, scene=1, text="Entwurf.", verdict={"grade": "needs_revision"}
    )
    assert not (book / "manuscript" / "chapter_05.md").exists()


def test_write_scene_draft_rejects_invalid_chapter(book) -> None:
    result = manuscript.write_scene_draft(
        chapter="../evil", scene=1, text="x", verdict={"grade": "needs_revision"}
    )
    assert result["status"] == "error"


# --- Path traversal ---------------------------------------------------------------


@pytest.mark.parametrize(
    "malicious_chapter",
    ["../../etc/passwd", "1/../../secrets", "/etc/passwd", "..", ""],
)
def test_read_manuscript_rejects_path_traversal(book, malicious_chapter) -> None:
    result = manuscript.read_manuscript(malicious_chapter)
    assert result["status"] == "error"


def test_write_scene_rejects_path_traversal(book) -> None:
    result = manuscript.write_scene("../../evil", 1, "text")
    assert result["status"] == "error"


def test_resolve_within_rejects_dot_dot(tmp_path) -> None:
    from app.tools._paths import resolve_within

    with pytest.raises(ValueError):
        resolve_within(base=tmp_path, relative_name="../evil.md")


def test_resolve_within_accepts_a_plain_filename(tmp_path) -> None:
    from app.tools._paths import resolve_within

    resolved = resolve_within(base=tmp_path, relative_name="chapter_01.md")
    assert resolved == (tmp_path / "chapter_01.md").resolve()
