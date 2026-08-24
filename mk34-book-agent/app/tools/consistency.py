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

"""Kontinuitaets-Tool `check_consistency` (TASK-011).

Bewusst rein deterministisches Retrieval, keine LLM-Bewertung innerhalb des
Tools -- Akzeptanzkriterium "Kein Netzwerkaufruf im Retrieval-Pfad
(nachweisbar offline lauffaehig)" schliesst einen eingebetteten LLM-Aufruf
aus (der immer einen Netzwerkaufruf braeuchte). Die Task-Datei beschreibt
`check_consistency` als `dict mit {"conflicts": [...]}`; dieses Modul liefert
stattdessen die dafuer noetige Evidenz (`relevant_passages`) -- die
eigentliche semantische Konflikt-Beurteilung (erfordert Sprachverstaendnis,
keine deterministische Zeichenkettenanalyse) uebernimmt der Continuity Agent
(LLM, `app/agents/continuity_agent.py`), der dieses Tool aufruft und sein
Ergebnis gegen `new_text` abgleicht, bevor er selbst `{"conflicts": [...]}`
liefert (`output_schema=ContinuityReport`). Siehe TASK-011-Walkthrough fuer
die Begruendung dieser Abweichung von der woertlichen Tool-Signatur.
"""

from __future__ import annotations

from app.retrieval.query import query_relevant_passages
from app.tools.manuscript import characters_mentioned


def check_consistency(new_text: str, context_refs: list[str]) -> dict:
    """Sucht die relevantesten Vorpassagen zu einer neuen Szene als
    Grounding-Basis fuer die Kontinuitaetspruefung.

    Args:
        new_text: Der zu pruefende neue Szenentext.
        context_refs: Zusaetzliche Suchbegriffe (z. B. Figuren, Orte, Fakten
            aus dem Beat), die die Retrieval-Abfrage praezisieren.

    Returns:
        `{"status": "success", "query_entities": list[str],
        "relevant_passages": [{"chapter", "scene", "text", "pov_character",
        "characters_present", "location", "timestamp"}, ...]}`. Leere
        `relevant_passages`, wenn kein Index existiert oder nichts Relevantes
        gefunden wurde -- das ist kein Fehler, sondern bedeutet "keine
        Vorpassage widerspricht dem neuen Text" (oder: das Manuskript ist
        noch leer).
    """
    entities = sorted(
        set(characters_mentioned(new_text)) | {r for r in context_refs if r}
    )
    search_terms = entities or [r for r in context_refs if r]
    passages = query_relevant_passages(
        entities=search_terms, k=5, characters=entities or None
    )
    return {
        "status": "success",
        "query_entities": entities,
        "relevant_passages": passages,
    }
