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

"""FTS5-Ingestion: baut den lokalen Retrieval-Index aus dem Manuskript auf
(Entscheidung E2, Stufe 1, TASK-011).

Chunk-Grenze ist die Szene (nicht eine feste Tokenzahl). Jeder Chunk traegt
`chapter`, `scene`, `pov_character`, `characters_present`, `location`,
`timestamp` als `UNINDEXED`-Spalten (fuer den Metadaten-Filter in
`query.py`) plus den Szenentext als FTS5-indizierte Spalte (Unicode61-
Tokenizer, geeignet fuer Deutsch). `pov_character`/`location` stammen, wenn
vorhanden, aus dem vom Plot Agent geschriebenen `scene_beats`-Feld in
`plot_outline.json` (TASK-004); `characters_present` faellt andernfalls auf
eine simple Namens-Erkennung im Szenentext zurueck (wie
`app/tools/manuscript.py::chapter_stats`). `timestamp` wird per Regex aus
Formulierungen wie "20:43 Uhr" (vgl. Szene E) extrahiert, best-effort.

Kein Netzwerkaufruf: reines `sqlite3` (Stdlib), der Index ist jederzeit aus
dem Manuskript reproduzierbar und deshalb gitignored
(`books/*/.index/`, siehe `.gitignore`).
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from app.config import get_settings
from app.tools._paths import REPO_ROOT, store_dir
from app.tools.manuscript import (
    characters_mentioned,
    list_chapters,
    parse_scene_markers,
    read_manuscript,
)

_TIMESTAMP_RE = re.compile(r"\b(\d{1,2}:\d{2})\s*Uhr\b")


def index_path() -> Path:
    """Absoluter Pfad zum FTS5-Index (`MK34_INDEX_PATH`, relativ zum Repo-Root)."""
    settings = get_settings()
    path = Path(settings.mk34_index_path)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(path)


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS scenes")
    conn.execute(
        """
        CREATE VIRTUAL TABLE scenes USING fts5(
            text,
            chapter UNINDEXED,
            scene UNINDEXED,
            pov_character UNINDEXED,
            characters_present UNINDEXED,
            location UNINDEXED,
            timestamp UNINDEXED,
            tokenize = 'unicode61'
        )
        """
    )


def _scene_beat_metadata() -> dict[tuple[int, int], dict]:
    """Liest `pov_character`/`location`/`characters_present` aus dem
    `scene_beats`-Feld in `plot_outline.json` (TASK-004), keyed nach
    `(chapter, scene)`. Liefert `{}`, solange das Feld noch nicht existiert."""
    path = store_dir() / "plot_outline.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {
        (beat["chapter"], beat["scene"]): beat
        for beat in data.get("scene_beats", [])
        if "chapter" in beat and "scene" in beat
    }


def _extract_timestamp(text: str) -> str:
    match = _TIMESTAMP_RE.search(text)
    return f"{match.group(1)} Uhr" if match else ""


def build_index() -> dict:
    """Baut den FTS5-Index vollstaendig neu aus dem aktuellen Manuskript auf.

    Idempotent (`DROP TABLE IF EXISTS` + Neuaufbau) und jederzeit
    reproduzierbar -- der Index ist reine Laufzeit-Ableitung des
    Manuskripts, kein eigener Wahrheitsspeicher.

    Returns:
        `{"status": "success", "chunks_indexed": int, "path": str}`.
    """
    beat_metadata = _scene_beat_metadata()
    path = index_path()
    conn = _connect(path)
    try:
        _create_schema(conn)
        chunks_indexed = 0
        for entry in list_chapters().get("chapters", []):
            chapter = entry["chapter"]
            result = read_manuscript(chapter)
            if result.get("status") != "success":
                continue
            for scene, scene_text in parse_scene_markers(result["text"]).items():
                beat = beat_metadata.get((chapter, scene), {})
                characters = beat.get("characters_present") or characters_mentioned(
                    scene_text
                )
                conn.execute(
                    "INSERT INTO scenes (text, chapter, scene, pov_character, "
                    "characters_present, location, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        scene_text,
                        chapter,
                        scene,
                        beat.get("pov_character", ""),
                        ",".join(characters),
                        beat.get("location", ""),
                        _extract_timestamp(scene_text),
                    ),
                )
                chunks_indexed += 1
        conn.commit()
    finally:
        conn.close()
    return {"status": "success", "chunks_indexed": chunks_indexed, "path": str(path)}
