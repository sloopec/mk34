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

TASK-013 ergaenzt `validate_world_rules`: deterministische (Terminologie,
verbotene Begriffe) Pruefung der 10 nummerierten Naniten-Regeln aus
`books/life_link/store/world_bible.md` (Abschnitt 3). Die semantische Haelfte
("verhaelt sich die Technologie logisch konsistent?", Regeln ohne
eindeutiges Verbotswort, z. B. "keine Fernkommunikation ueber Distanz")
uebernimmt bewusst NICHT dieses Tool, sondern der Continuity Agent selbst
(LLM) -- er hat `world_bible.md` bereits ueber `scene_context` im Kontext
und wird per Instruktion ("Regelwidrige Naniten", `app/prompts/continuity.py`)
explizit zur semantischen Pruefung angehalten. Das entspricht der in der
Task-Datei geforderten Zweistufigkeit (Python fuer harte Verbotsmuster,
LLM-Judge fuer Semantik), ohne einen zusaetzlichen Live-LLM-Aufruf in dieses
Tool einzubetten (haelt `validate_world_rules` netzwerkfrei und offline
testbar wie `check_consistency`).
"""

from __future__ import annotations

import re

from app.retrieval.query import query_relevant_passages
from app.tools.characters import get_character, get_knowledge_state
from app.tools.manuscript import characters_mentioned
from app.tools.timeline import validate_chronology

# Regel-IDs verweisen auf die nummerierte Liste in
# books/life_link/store/world_bible.md, Abschnitt 3 ("Regeln der
# Schwarmintelligenz"). Nur Regeln mit eindeutigen Verbots-/Signalwoertern
# sind hier deterministisch pruefbar (Regeln 1, 5, 6); die uebrigen
# erfordern Sprachverstaendnis und bleiben LLM-Aufgabe (siehe Modul-Docstring).
_FORBIDDEN_PHRASES: list[tuple[int, str, str]] = [
    (
        1,
        "server",
        "Regel 1 (kein zentraler Server): Text erwaehnt einen 'Server' im "
        "Zusammenhang mit den Naniten -- es gibt keine zentrale "
        "Kontrollinstanz.",
    ),
    (
        1,
        "hauptcomputer",
        "Regel 1 (kein zentraler Server): Text erwaehnt einen zentralen Hauptcomputer.",
    ),
    (
        1,
        "mutterschiff",
        "Regel 1 (kein zentraler Server): Text erwaehnt ein zentrales Mutterschiff.",
    ),
    (
        1,
        "kontrollzentrum",
        "Regel 1 (kein zentraler Server): Text erwaehnt ein zentrales Kontrollzentrum.",
    ),
    (
        1,
        "kommandozentrale",
        "Regel 1 (kein zentraler Server): Text erwaehnt eine zentrale "
        "Kommandozentrale.",
    ),
    (
        5,
        "metallm",
        "Regel 5 (keine mechanischen 'Metallmaennchen'): Text beschreibt "
        "Naniten als mechanische Roboter statt molekularer Maschinen.",
    ),
    (
        5,
        "roboter",
        "Regel 5 (keine mechanischen 'Metallmaennchen'): Text beschreibt "
        "Naniten als Roboter statt molekularer Maschinen.",
    ),
    (
        5,
        "zahnr",
        "Regel 5 (keine mechanischen 'Metallmaennchen'): Text beschreibt "
        "Naniten mit mechanischen Bauteilen (Zahnraeder).",
    ),
]


def _split_sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _check_forbidden_phrases(text: str) -> list[dict]:
    violations = []
    for sentence in _split_sentences(text):
        lowered = sentence.lower()
        for rule_id, phrase, explanation in _FORBIDDEN_PHRASES:
            if phrase in lowered:
                violations.append(
                    {
                        "rule_id": rule_id,
                        "evidence": sentence.strip(),
                        "explanation": explanation,
                    }
                )
    return violations


def _classify_register(character: dict) -> str | None:
    """Grobe Zweiteilung des Sprachregisters aus `characters.json`
    (`language_register`-Freitext) in `"laie"` oder `"wissenschaftlich"`,
    fuer den figurenbezogenen Terminologie-Check (Regel 6).

    Prueft "wissenschaftlich" zuerst: Freitexte wie "...korrigiert Davids
    Laienbegriffe aktiv" enthalten sonst "laie" als Teilstring von
    "Laienbegriffe" und wuerden faelschlich als Laien-Register erkannt.
    """
    register = character.get("language_register", "").lower()
    if re.search(r"wissenschaftlich|\bpräzise\b|\bpraezise\b", register):
        return "wissenschaftlich"
    if re.search(r"\blaie\b|umgangssprachlich", register):
        return "laie"
    return None


def _check_terminology(text: str, characters_present: list[str]) -> list[dict]:
    """Regel 6 (Terminologie-Konsistenz), figurenbezogen: eine Figur mit
    wissenschaftlichem Register sollte "Nanobots" nicht in ihrem eigenen
    Sprechanteil verwenden (und umgekehrt eine Laien-Figur nicht "Naniten").
    Deterministisch ueber Naeherung (Figurenname + Begriff im selben Satz),
    keine echte Sprecherzuordnung."""
    violations = []
    sentences = _split_sentences(text)
    for name in characters_present:
        character = get_character(name)
        if character.get("status") != "success":
            continue
        register = _classify_register(character)
        if register is None:
            continue
        forbidden_term = "nanobots" if register == "wissenschaftlich" else "naniten"
        # Wie `characters_mentioned` (app/tools/manuscript.py): auch auf
        # einzelne Namensbestandteile matchen (z. B. "Sarah" fuer "Dr. Sarah
        # Lin"), damit reine Dialog-Attribuierungen erkannt werden.
        name_tokens = [name, *name.split()]
        for sentence in sentences:
            if (
                any(token and token in sentence for token in name_tokens)
                and forbidden_term in sentence.lower()
            ):
                violations.append(
                    {
                        "rule_id": 6,
                        "evidence": sentence.strip(),
                        "explanation": (
                            f"{name} (Sprachregister: {register}) verwendet "
                            f"'{forbidden_term.capitalize()}', was fuer dieses "
                            "Register untypisch ist (Regel 6, "
                            "Terminologie-Konsistenz)."
                        ),
                    }
                )
    return violations


def validate_world_rules(text: str, characters: list[str] | None = None) -> dict:
    """Prueft einen Szenentext deterministisch gegen die harten Naniten-
    Weltregeln aus `world_bible.md` (verbotene Begriffe fuer Regel 1/5,
    figurenbezogene Terminologie fuer Regel 6). Semantische Regeln
    (2, 3, 4, 7, 8, 9, 10) prueft der Continuity Agent selbst per LLM-
    Reasoning gegen `world_bible.md` (siehe Modul-Docstring).

    Args:
        text: Der zu pruefende Szenentext.
        characters: Namen der in der Szene anwesenden Figuren, fuer den
            Terminologie-Check (Regel 6). Ohne Angabe faellt der Check auf
            im Text erwaehnte, bekannte Figurennamen zurueck.

    Returns:
        `{"status": "success", "violations": [{"rule_id": int, "evidence":
        str, "explanation": str}, ...]}`. Leere Liste, wenn keine
        deterministisch pruefbare Regel verletzt wurde -- das schliesst
        Verstoesse gegen die rein semantischen Regeln NICHT aus.
    """
    characters_present = characters or characters_mentioned(text)
    violations = _check_forbidden_phrases(text)
    violations += _check_terminology(text, characters_present)
    return {"status": "success", "violations": violations}


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
        {"knowledge_state": str, "chapter_state": dict | None}},
        "world_rule_violations": [{"rule_id", "evidence", "explanation"},
        ...]}`. Leere Listen/Dicts bedeuten "keine Vorpassage/kein
        Konflikt/kein bekannter Zustand/keine deterministisch pruefbare
        Regelverletzung gefunden" -- das ist kein Fehler (TASK-013:
        `world_rule_violations` deckt nur die deterministisch pruefbaren
        Regeln 1/5/6 ab, siehe `validate_world_rules`).
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

    world_rule_violations = validate_world_rules(new_text, characters=entities or None)[
        "violations"
    ]

    return {
        "status": "success",
        "query_entities": entities,
        "relevant_passages": passages,
        "timeline_conflicts": {
            "time_jumps": timeline_check["time_jumps"],
            "parallel_conflicts": parallel_conflicts,
        },
        "character_states": character_states,
        "world_rule_violations": world_rule_violations,
    }
