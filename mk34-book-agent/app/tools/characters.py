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

"""Figuren-Tools gegen `<MK34_BOOK_ROOT>/store/characters.json` (TASK-005).

`characters.json` traegt pro Figur `name`, `role`, `language_register`,
`motivation`, `arc`, `knowledge_state` (Fliesstext ueber die Phasen hinweg,
siehe Plan 1/TASK-003) und `first_appearance`. `update_character` haengt
Entwicklungen an ein separates `development_log`-Feld an, statt `arc`
destruktiv zu ueberschreiben.

Feingranulares, kapitelweises `knowledge_state`-Tracking (pro Figur *und*
Kapitel) kommt erst mit TASK-012 (Timeline-/Character-State-Tracking) --
`get_knowledge_state` liefert bis dahin das vorhandene Phasen-Fliesstext-Feld
plus Hinweis, bis zu welcher Phase es reicht.
"""

from __future__ import annotations

import json

from app.tools._paths import store_dir

_CHARACTERS_FILE = "characters.json"


def _characters_path():
    return store_dir() / _CHARACTERS_FILE


def _read_characters() -> dict:
    path = _characters_path()
    if not path.exists():
        return {"characters": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"characters": []}


def _write_characters(data: dict) -> None:
    path = _characters_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _find_character(data: dict, name: str) -> dict | None:
    for character in data.get("characters", []):
        if character.get("name") == name:
            return character
    return None


def get_character(name: str) -> dict:
    """Laedt das vollstaendige Figurenprofil einer Figur.

    Args:
        name: Exakter Figurenname, wie in `characters.json` gefuehrt (z. B.
            "Dr. Sarah Lin").

    Returns:
        Bei Erfolg `{"status": "success", **Figurenprofil}`. Ist die Figur
        nicht bekannt: `{"status": "not_found", "name": str}`.
    """
    character = _find_character(_read_characters(), name)
    if character is None:
        return {"status": "not_found", "name": name}
    return {"status": "success", **character}


def update_character(name: str, development: str) -> dict:
    """Haengt eine Entwicklung an das `development_log` einer Figur an.

    Idempotent: identische Eintraege werden nicht doppelt angehaengt. Das
    bestehende `arc`-Feld bleibt unveraendert -- Entwicklungen ergaenzen den
    Kanon, statt ihn zu ueberschreiben.

    Args:
        name: Exakter Figurenname.
        development: Kurzbeschreibung der neuen Entwicklung.

    Returns:
        Bei Erfolg `{"status": "success", "name": str}`. Ist die Figur nicht
        bekannt: `{"status": "not_found", "name": str}`.
    """
    data = _read_characters()
    character = _find_character(data, name)
    if character is None:
        return {"status": "not_found", "name": name}
    log = character.setdefault("development_log", [])
    if development not in log:
        log.append(development)
    _write_characters(data)
    return {"status": "success", "name": name}


def get_character_arc(name: str) -> dict:
    """Laedt den kanonischen Entwicklungsbogen einer Figur plus geloggte
    Entwicklungen aus `update_character`-Aufrufen.

    Args:
        name: Exakter Figurenname.

    Returns:
        Bei Erfolg `{"status": "success", "name": str, "arc": str,
        "development_log": list[str]}`. Ist die Figur nicht bekannt:
        `{"status": "not_found", "name": str}`.
    """
    character = _find_character(_read_characters(), name)
    if character is None:
        return {"status": "not_found", "name": name}
    return {
        "status": "success",
        "name": name,
        "arc": character.get("arc", ""),
        "development_log": character.get("development_log", []),
    }


def get_knowledge_state(name: str, chapter: int) -> dict:
    """Liefert, was eine Figur bis zu einem bestimmten Zeitpunkt weiss.

    Args:
        name: Exakter Figurenname.
        chapter: 1-basierte Kapitelnummer, fuer die der Wissensstand
            interessiert (dient hier nur der Nachvollziehbarkeit im
            Rueckgabewert -- die eigentliche Filterung nach Kapitel kommt
            erst mit TASK-012).

    Returns:
        Bei Erfolg `{"status": "success", "name": str, "chapter": int,
        "knowledge_state": str}`. Ist die Figur nicht bekannt:
        `{"status": "not_found", "name": str}`.
    """
    character = _find_character(_read_characters(), name)
    if character is None:
        return {"status": "not_found", "name": name}
    return {
        "status": "success",
        "name": name,
        "chapter": chapter,
        "knowledge_state": character.get("knowledge_state", ""),
    }
