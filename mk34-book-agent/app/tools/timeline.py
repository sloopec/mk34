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

"""Timeline-Tools gegen `<MK34_BOOK_ROOT>/store/timeline.json` (TASK-012).

Persistiert die Chronologie des Manuskripts als flache Ereignisliste
(`{"chapter", "scene", "timestamp", "location", "description", "characters"}`)
und stellt eine rein deterministische Konsistenzpruefung (`validate_chronology`)
darueber bereit: Zeitspruenge (Zeitstempel laeuft ohne erkennbaren
Tageswechsel-Hinweis rueckwaerts) und Parallelitaets-Konflikte (dieselbe
Figur zur selben Uhrzeit an zwei verschiedenen Orten).

`append_event` ist idempotent bezueglich `(chapter, scene)`: ein
wiederholter Aufruf fuer dieselbe Szene ersetzt den bestehenden Eintrag,
statt ihn zu duplizieren -- analog zur Replace-Semantik von
`app/tools/manuscript.py::write_scene`.

Zeitstempel-Format wie im Manuskript ueblich: `"HH:MM Uhr"` (vgl.
`app/retrieval/index.py::_TIMESTAMP_RE`, Szene E: "20:43 Uhr").
"""

from __future__ import annotations

import json
import re

from app.tools._paths import store_dir

_TIMELINE_FILE = "timeline.json"
_TIMESTAMP_RE = re.compile(r"\b(\d{1,2}):(\d{2})\s*Uhr\b")


def _timeline_path():
    return store_dir() / _TIMELINE_FILE


def _read_timeline() -> dict:
    path = _timeline_path()
    if not path.exists():
        return {"book_slug": "", "source": "", "events": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"book_slug": "", "source": "", "events": []}
    data.setdefault("events", [])
    return data


def _write_timeline(data: dict) -> None:
    path = _timeline_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _sort_key(event: dict) -> tuple[int, int]:
    return (event.get("chapter", 0), event.get("scene", 0))


def extract_timestamp(text: str) -> str:
    """Extrahiert eine Uhrzeit im Format `"HH:MM Uhr"` aus Szenentext,
    best-effort (vgl. `app/retrieval/index.py`). Leerer String, wenn keine
    Uhrzeit gefunden wurde."""
    match = _TIMESTAMP_RE.search(text)
    return f"{match.group(1)}:{match.group(2)} Uhr" if match else ""


def _parse_minutes(timestamp: str) -> int | None:
    match = _TIMESTAMP_RE.search(timestamp)
    if not match:
        return None
    return int(match.group(1)) * 60 + int(match.group(2))


def append_event(
    chapter: int,
    scene: int,
    timestamp: str,
    location: str,
    description: str,
    characters: list[str],
) -> dict:
    """Traegt ein Ereignis fuer eine Szene in die Timeline ein (oder ersetzt
    ein bestehendes Ereignis derselben Kapitel/Szenen-Kombination).

    Args:
        chapter: 1-basierte Kapitelnummer.
        scene: 1-basierte Szenennummer.
        timestamp: Uhrzeit der Szene im Format `"HH:MM Uhr"`, oder `""`, wenn
            keine bekannt ist.
        location: Handlungsort der Szene.
        description: Kurzbeschreibung, was in der Szene passiert.
        characters: Namen der in der Szene anwesenden Figuren.

    Returns:
        `{"status": "success", "chapter": int, "scene": int, "event_count": int}`.
    """
    data = _read_timeline()
    events = [
        e
        for e in data["events"]
        if not (e.get("chapter") == chapter and e.get("scene") == scene)
    ]
    events.append(
        {
            "chapter": chapter,
            "scene": scene,
            "timestamp": timestamp or "",
            "location": location or "",
            "description": description or "",
            "characters": list(characters or []),
        }
    )
    events.sort(key=_sort_key)
    data["events"] = events
    _write_timeline(data)
    return {
        "status": "success",
        "chapter": chapter,
        "scene": scene,
        "event_count": len(events),
    }


def read_timeline(
    from_chapter: int | None = None, to_chapter: int | None = None
) -> dict:
    """Liest Ereignisse der Timeline, optional auf einen Kapitelbereich
    eingeschraenkt (jeweils inklusive Grenzen).

    Args:
        from_chapter: Erste einzuschliessende Kapitelnummer, oder `None` fuer
            "von Anfang an".
        to_chapter: Letzte einzuschliessende Kapitelnummer, oder `None` fuer
            "bis zum Ende".

    Returns:
        `{"status": "success", "events": [...]}`, aufsteigend nach
        `(chapter, scene)` sortiert.
    """
    events = _read_timeline()["events"]
    if from_chapter is not None:
        events = [e for e in events if e.get("chapter", 0) >= from_chapter]
    if to_chapter is not None:
        events = [e for e in events if e.get("chapter", 0) <= to_chapter]
    return {"status": "success", "events": sorted(events, key=_sort_key)}


def validate_chronology() -> dict:
    """Prueft die Timeline deterministisch auf zwei Arten von Widersprueche:

    - **Zeitspruenge**: Ein spaeteres Ereignis (in Erzaehlreihenfolge, also
      nach `(chapter, scene)` sortiert) hat einen Zeitstempel, der -- ohne
      erkennbaren Tageswechsel-Hinweis in der Beschreibung (z. B. "am
      naechsten Tag", "Stunden spaeter") -- vor dem Zeitstempel des
      vorherigen Ereignisses liegt. Das ist ein starkes Signal fuer einen
      unbeabsichtigten Zeitsprung, keine perfekte Kalenderpruefung (die
      Manuskript-Zeitstempel tragen kein Datum).
    - **Parallelitaets-Konflikte**: Dieselbe Figur ist laut Zeitstempel zur
      exakt selben Uhrzeit an zwei unterschiedlichen Orten gelistet.

    Returns:
        `{"status": "success", "time_jumps": [...], "parallel_conflicts": [...]}`.
        Beide Listen sind leer, wenn keine Konflikte gefunden wurden.
    """
    events = sorted(_read_timeline()["events"], key=_sort_key)

    time_jumps: list[dict] = []
    previous = None
    for event in events:
        minutes = _parse_minutes(event.get("timestamp", ""))
        if minutes is not None and previous is not None:
            prev_minutes, prev_event = previous
            day_change_hint = any(
                marker in event.get("description", "").lower()
                for marker in (
                    "naechsten tag",
                    "nächsten tag",
                    "am naechsten morgen",
                    "am nächsten morgen",
                    "tage spaeter",
                    "tage später",
                    "stunden spaeter",
                    "stunden später",
                    "am folgetag",
                )
            )
            if minutes < prev_minutes and not day_change_hint:
                time_jumps.append(
                    {
                        "type": "Zeitsprung",
                        "from": {
                            "chapter": prev_event["chapter"],
                            "scene": prev_event["scene"],
                            "timestamp": prev_event["timestamp"],
                        },
                        "to": {
                            "chapter": event["chapter"],
                            "scene": event["scene"],
                            "timestamp": event["timestamp"],
                        },
                        "detail": (
                            f"Zeitstempel laeuft von {prev_event['timestamp']} "
                            f"(Kapitel {prev_event['chapter']}, Szene "
                            f"{prev_event['scene']}) auf {event['timestamp']} "
                            f"(Kapitel {event['chapter']}, Szene {event['scene']}) "
                            "rueckwaerts, ohne erkennbaren Tageswechsel-Hinweis."
                        ),
                    }
                )
        if minutes is not None:
            previous = (minutes, event)

    parallel_conflicts: list[dict] = []
    by_timestamp: dict[str, list[dict]] = {}
    for event in events:
        timestamp = event.get("timestamp", "")
        if not timestamp:
            continue
        by_timestamp.setdefault(timestamp, []).append(event)

    for timestamp, same_time_events in by_timestamp.items():
        locations_by_character: dict[str, set[str]] = {}
        for event in same_time_events:
            for character in event.get("characters", []):
                locations_by_character.setdefault(character, set()).add(
                    event.get("location", "")
                )
        for character, locations in locations_by_character.items():
            locations.discard("")
            if len(locations) > 1:
                parallel_conflicts.append(
                    {
                        "type": "Parallelitaets-Konflikt",
                        "character": character,
                        "timestamp": timestamp,
                        "locations": sorted(locations),
                        "detail": (
                            f"{character} ist um {timestamp} laut Timeline "
                            f"gleichzeitig an mehreren Orten: {', '.join(sorted(locations))}."
                        ),
                    }
                )

    return {
        "status": "success",
        "time_jumps": time_jumps,
        "parallel_conflicts": parallel_conflicts,
    }
