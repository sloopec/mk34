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

Feingranulares, kapitelweises Zustandstracking (TASK-012) liegt im neuen
Feld `state_by_chapter` je Figur: `{"<chapter>": {"location", "knowledge",
"emotional_state", "infection_status"}}` -- Kapitelnummern als String-Keys
(JSON kennt keine int-Keys). `infection_status` ist LifeLink-spezifisch:
`"nicht_optimiert" | "infiziert" | "voll_compliant"` (vgl. `basics.md`,
Szene E: "volle Compliance trotz kognitiver Ablehnung").

`get_knowledge_state` liefert weiterhin auch das grobe Phasen-Fliesstext-Feld
(`knowledge_state`, aus Plan 1) fuer Abwaertskompatibilitaet, ergaenzt aber ab
TASK-012 um den kapitelgenauen Zustand aus `state_by_chapter`, falls
vorhanden -- mit Fallback auf den zuletzt bekannten Stand vor dem
angefragten Kapitel (Figuren aendern ihren Zustand nicht rueckwirkend).
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

    Kombiniert das grobe Phasen-Fliesstext-Feld (`knowledge_state`, Plan 1)
    mit dem kapitelgenauen Zustand aus `state_by_chapter` (TASK-012), falls
    vorhanden. Fuer den kapitelgenauen Teil gilt: der zuletzt bekannte
    Zustand *vor oder bei* `chapter` gilt weiter, solange kein neuerer
    Eintrag existiert (Figuren "vergessen" ihren Zustand nicht zwischen
    Kapiteln ohne expliziten Eintrag).

    Args:
        name: Exakter Figurenname.
        chapter: 1-basierte Kapitelnummer, fuer die der Wissensstand
            interessiert.

    Returns:
        Bei Erfolg `{"status": "success", "name": str, "chapter": int,
        "knowledge_state": str, "chapter_state": dict | None}`.
        `chapter_state` ist `None`, wenn fuer diese oder eine fruehere
        Kapitelnummer noch kein Eintrag existiert. Ist die Figur nicht
        bekannt: `{"status": "not_found", "name": name}`.
    """
    character = _find_character(_read_characters(), name)
    if character is None:
        return {"status": "not_found", "name": name}
    chapter_state = _latest_chapter_state(character, chapter)
    return {
        "status": "success",
        "name": name,
        "chapter": chapter,
        "knowledge_state": character.get("knowledge_state", ""),
        "chapter_state": chapter_state,
    }


def _latest_chapter_state(character: dict, chapter: int) -> dict | None:
    """Der zuletzt bekannte kapitelweise Zustand bei oder vor `chapter`."""
    states = character.get("state_by_chapter", {})
    candidates = [
        (int(key), value) for key, value in states.items() if int(key) <= chapter
    ]
    if not candidates:
        return None
    latest_chapter, state = max(candidates, key=lambda item: item[0])
    return {"chapter": latest_chapter, **state}


def update_character_state(
    name: str,
    chapter: int,
    location: str = "",
    knowledge: str = "",
    emotional_state: str = "",
    infection_status: str = "",
) -> dict:
    """Aktualisiert den kapitelweisen Zustand einer Figur (TASK-012).

    Wird als Post-Write-Schritt der Schreib-Pipeline pro Szene aufgerufen
    (siehe `app/pipelines/writing.py`) -- deterministisches Schreiben, auch
    wenn die zugrundeliegende Extraktion (welche Werte gelten) kuenftig
    LLM-gestuetzt erfolgen kann. Ueberschreibt einen bestehenden Eintrag fuer
    dasselbe Kapitel (letzter Stand gewinnt, analog zu `write_scene`s
    Replace-Semantik pro Szene).

    Args:
        name: Exakter Figurenname.
        chapter: 1-basierte Kapitelnummer.
        location: Aktueller Aufenthaltsort der Figur.
        knowledge: Kurzbeschreibung des aktuellen Wissensstands.
        emotional_state: Aktueller emotionaler Zustand.
        infection_status: `"nicht_optimiert" | "infiziert" | "voll_compliant"`.

    Returns:
        Bei Erfolg `{"status": "success", "name": str, "chapter": int}`.
        Ist die Figur nicht bekannt: `{"status": "not_found", "name": name}`.
    """
    data = _read_characters()
    character = _find_character(data, name)
    if character is None:
        return {"status": "not_found", "name": name}
    states = character.setdefault("state_by_chapter", {})
    states[str(chapter)] = {
        "location": location,
        "knowledge": knowledge,
        "emotional_state": emotional_state,
        "infection_status": infection_status,
    }
    _write_characters(data)
    return {"status": "success", "name": name, "chapter": chapter}


def check_knowledge_prerequisite(
    name: str, chapter: int, required_knowledge: str
) -> dict:
    """Warnt, wenn eine Szene Wissen voraussetzt, das eine Figur zu diesem
    Zeitpunkt laut ihrem gepflegten Zustand noch nicht haben kann.

    Rein stringbasierter, deterministischer Abgleich (kein LLM-Aufruf): das
    `required_knowledge`-Stichwort muss entweder im kapitelgenauen
    `knowledge`-Feld des zuletzt bekannten Zustands oder im groben
    Phasen-Fliesstext (`knowledge_state`) vorkommen. Ist kein kapitelgenauer
    Zustand fuer diese oder eine fruehere Kapitelnummer bekannt, wird das
    NICHT automatisch als Verstoss gewertet (fehlende Daten sind kein
    Widerspruchsbeweis) -- `status` ist dann `"unknown"`.

    Args:
        name: Exakter Figurenname.
        chapter: 1-basierte Kapitelnummer der zu pruefenden Szene.
        required_knowledge: Stichwort/Kurzsatz des vorausgesetzten Wissens.

    Returns:
        `{"status": "ok" | "violation" | "unknown", "name": str,
        "chapter": int, "required_knowledge": str}`. Ist die Figur nicht
        bekannt: `{"status": "not_found", "name": name}`.
    """
    result = get_knowledge_state(name, chapter)
    if result["status"] == "not_found":
        return result
    chapter_state = result.get("chapter_state")
    if chapter_state is None:
        return {
            "status": "unknown",
            "name": name,
            "chapter": chapter,
            "required_knowledge": required_knowledge,
        }
    known_text = (
        f"{chapter_state.get('knowledge', '')} {result.get('knowledge_state', '')}"
    )
    status = "ok" if required_knowledge.lower() in known_text.lower() else "violation"
    return {
        "status": status,
        "name": name,
        "chapter": chapter,
        "required_knowledge": required_knowledge,
    }
