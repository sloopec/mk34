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

"""Kontinuitaets-Tool `check_consistency` (TASK-011, erweitert TASK-012).

Bewusst rein deterministisches Retrieval, keine LLM-Bewertung innerhalb des
Tools -- Akzeptanzkriterium "Kein Netzwerkaufruf im Retrieval-Pfad
(nachweisbar offline lauffaehig)" schliesst einen eingebetteten LLM-Aufruf
aus (der immer einen Netzwerkaufruf braeuchte). Die Task-Datei beschreibt
`check_consistency` als `dict mit {"conflicts": [...]}`; dieses Modul liefert
stattdessen die dafuer noetige Evidenz (`relevant_passages`,
`timeline_conflicts`, `character_states`) -- die eigentliche semantische
Konflikt-Beurteilung (erfordert Sprachverstaendnis, keine deterministische
Zeichenkettenanalyse) uebernimmt der Continuity Agent (LLM,
`app/agents/continuity_agent.py`), der dieses Tool aufruft und sein
Ergebnis gegen `new_text` abgleicht, bevor er selbst `{"conflicts": [...]}`
liefert (`output_schema=ContinuityReport`). Siehe TASK-011-Walkthrough fuer
die Begruendung dieser Abweichung von der woertlichen Tool-Signatur.

TASK-012 ergaenzt zwei weitere, ebenso deterministische Evidenzquellen:
`app/tools/timeline.py::validate_chronology` (Zeitspruenge/Parallelitaets-
Konflikte) und `app/tools/characters.py::get_knowledge_state` (kapitelweiser
Figuren-Zustand) -- der Continuity Agent nutzt damit beide in TASK-012
gebauten Quellen zusaetzlich zum FTS5-Retrieval aus TASK-011.
"""

from __future__ import annotations

from app.retrieval.query import query_relevant_passages
from app.tools.characters import get_knowledge_state
from app.tools.manuscript import characters_mentioned
from app.tools.timeline import validate_chronology


def check_consistency(
    new_text: str, context_refs: list[str], chapter: int | None = None
) -> dict:
    """Sucht Evidenz zu einer neuen Szene aus drei deterministischen
    Quellen: FTS5-Retrieval (Vorpassagen), Timeline (Zeitspruenge/
    Parallelitaets-Konflikte) und Figuren-Zustand (kapitelweises Wissen).

    Args:
        new_text: Der zu pruefende neue Szenentext.
        context_refs: Zusaetzliche Suchbegriffe (z. B. Figuren, Orte, Fakten
            aus dem Beat), die die Retrieval-Abfrage praezisieren.
        chapter: 1-basierte Kapitelnummer der zu pruefenden Szene, falls
            bekannt -- wird genutzt, um den Wissensstand der beteiligten
            Figuren zu diesem Zeitpunkt nachzuschlagen. Ohne `chapter` bleibt
            `character_states` leer (kein Fehler, nur weniger Kontext).

    Returns:
        `{"status": "success", "query_entities": list[str],
        "relevant_passages": [...], "timeline_conflicts": {"time_jumps":
        [...], "parallel_conflicts": [...]}, "character_states": {name:
        {"knowledge_state": str, "chapter_state": dict | None}}}`. Leere
        Listen/Dicts bedeuten "keine Vorpassage/kein Konflikt/kein bekannter
        Zustand gefunden" -- das ist kein Fehler.
    """
    entities = sorted(
        set(characters_mentioned(new_text)) | {r for r in context_refs if r}
    )
    search_terms = entities or [r for r in context_refs if r]
    passages = query_relevant_passages(
        entities=search_terms, k=5, characters=entities or None
    )

    timeline_check = validate_chronology()
    parallel_conflicts = [
        conflict
        for conflict in timeline_check["parallel_conflicts"]
        if conflict["character"] in entities
    ]

    character_states: dict = {}
    if chapter is not None:
        for name in entities:
            result = get_knowledge_state(name, chapter)
            if result.get("status") == "success":
                character_states[name] = {
                    "knowledge_state": result["knowledge_state"],
                    "chapter_state": result["chapter_state"],
                }

    return {
        "status": "success",
        "query_entities": entities,
        "relevant_passages": passages,
        "timeline_conflicts": {
            "time_jumps": timeline_check["time_jumps"],
            "parallel_conflicts": parallel_conflicts,
        },
        "character_states": character_states,
    }
