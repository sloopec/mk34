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

"""FTS5-Query: Metadaten-Filter + BM25-Volltext ueber Szenen-Chunks (TASK-011).

Query = Metadaten-Filter (beteiligte Figuren aus dem neuen Beat) plus
BM25-Volltext ueber die Entitaeten der neuen Szene, wie in der Task-Datei
spezifiziert. Kein Netzwerkaufruf.
"""

from __future__ import annotations

import sqlite3

from app.retrieval.index import index_path


def _sanitize_term(term: str) -> str | None:
    """Quotet jeden Suchbegriff, damit FTS5-Operatoren (`*`, `^`, `OR`, ...)
    in einem Modell-/User-gelieferten Entitaetsnamen nicht als Query-Syntax
    interpretiert werden."""
    term = term.strip()
    if not term:
        return None
    escaped = term.replace('"', '""')
    return f'"{escaped}"'


def query_relevant_passages(
    entities: list[str],
    k: int = 5,
    characters: list[str] | None = None,
) -> list[dict]:
    """Findet die `k` relevantesten Vorpassagen zu den Entitaeten einer neuen
    Szene.

    Args:
        entities: Namen/Begriffe der neuen Szene (Figuren, Orte, Fakten),
            gegen die die BM25-Volltextsuche laeuft.
        k: Anzahl der zurueckzugebenden Treffer.
        characters: Optionaler Metadaten-Filter -- schraenkt auf Passagen
            ein, in denen mindestens eine dieser Figuren als anwesend
            gefuehrt wird.

    Returns:
        Liste von `{"chapter", "scene", "text", "pov_character",
        "characters_present", "location", "timestamp"}`, nach BM25-Relevanz
        sortiert (relevanteste zuerst). Leere Liste, wenn der Index noch
        nicht existiert oder keine verwertbaren Entitaeten uebergeben wurden.
    """
    path = index_path()
    if not path.exists():
        return []

    terms = [t for t in (_sanitize_term(e) for e in entities) if t]
    if not terms:
        return []
    match_query = " OR ".join(terms)

    sql = (
        "SELECT chapter, scene, text, pov_character, characters_present, "
        "location, timestamp FROM scenes WHERE scenes MATCH ?"
    )
    params: list[object] = [match_query]
    if characters:
        clauses = " OR ".join("characters_present LIKE ?" for _ in characters)
        sql += f" AND ({clauses})"
        params.extend(f"%{c}%" for c in characters)
    sql += " ORDER BY bm25(scenes) LIMIT ?"
    params.append(k)

    conn = sqlite3.connect(path)
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()

    return [
        {
            "chapter": row[0],
            "scene": row[1],
            "text": row[2],
            "pov_character": row[3],
            "characters_present": row[4].split(",") if row[4] else [],
            "location": row[5],
            "timestamp": row[6],
        }
        for row in rows
    ]
