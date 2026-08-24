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

"""Kontext-Loader-Tools: holen den Story-Kanon aus `<MK34_BOOK_ROOT>/store/`
in den Agenten-Kontext (TASK-002).

`load_scene_context` ist die Hauptschnittstelle fuer die Schreib-Pipeline
(`app/pipelines/writing.py`, TASK-008): sie kombiniert Beat, beteiligte
Figuren und Weltregeln in einem Aufruf und schreibt das Ergebnis zusaetzlich
selbst unter `scene_context` in den Session-State -- unabhaengig davon, ob
sie von einem Agenten mit `output_key="scene_context"` umhuellt wird (wie in
TASK-008) oder direkt als Tool-Call eines LLM aufgerufen wird.

`update_plot_outline` und `read_chapter_summaries` werden erst in TASK-004
(Plot Agent) implementiert -- dort entsteht auch das `scene_beats`-Feld in
`plot_outline.json`, das `load_scene_context` hier bereits konsumiert
(vorwaertskompatibel: fehlt es noch, liefert `load_scene_context` `beat:
None`, statt zu scheitern).
"""

from __future__ import annotations

import json

from google.adk.tools import ToolContext

from app.tools._paths import store_dir

_MAX_TENSION_LEVEL = 10
_MIN_TENSION_LEVEL = 1


def _read_json(path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _read_text(path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def load_world_bible() -> dict:
    """Laedt die Naniten-Regeln und das Weltenbau-Dokument.

    Returns:
        `{"status": "success", "text": str}`, oder `{"status": "not_found"}`,
        falls `world_bible.md` im aktiven Buchprojekt noch nicht existiert.
    """
    text = _read_text(store_dir() / "world_bible.md")
    if text is None:
        return {"status": "not_found"}
    return {"status": "success", "text": text}


def load_style_guide() -> dict:
    """Laedt das Sprachregister pro Figur, Ton- und POV-Regeln.

    Returns:
        `{"status": "success", "text": str}`, oder `{"status": "not_found"}`,
        falls `style_guide.md` im aktiven Buchprojekt noch nicht existiert.
    """
    text = _read_text(store_dir() / "style_guide.md")
    if text is None:
        return {"status": "not_found"}
    return {"status": "success", "text": text}


def load_plot_outline(act: int) -> dict:
    """Laedt die Beats fuer einen Akt/eine Phase (0-basiert, Phase 0-5).

    Args:
        act: Phasennummer aus `basics.md` (0 = Der Pitch, ... 5 = Die Loesung?).

    Returns:
        Bei Erfolg `{"status": "success", "act": int, "title": str,
        "focus_characters": list[str], "summary": str, "beats": list[str],
        "example_scenes": list[str]}`. Existiert die Phase nicht:
        `{"status": "not_found", "act": int}`.
    """
    data = _read_json(store_dir() / "plot_outline.json")
    for phase in data.get("phases", []):
        if phase.get("id") == act:
            return {
                "status": "success",
                "act": act,
                "title": phase.get("title", ""),
                "focus_characters": phase.get("focus_characters", []),
                "summary": phase.get("summary", ""),
                "beats": phase.get("beats", []),
                "example_scenes": phase.get("example_scenes", []),
            }
    return {"status": "not_found", "act": act}


def _find_scene_beat(plot_data: dict, chapter: int, scene: int) -> dict | None:
    """Looks up a per-scene beat written by the Plot Agent (TASK-004).

    `plot_outline.json` does not carry a `scene_beats` array yet in this
    plan's store fixture -- `update_plot_outline` (TASK-004) is what starts
    populating it. Returning `None` here (instead of raising) keeps this
    loader usable before that task lands.
    """
    for beat in plot_data.get("scene_beats", []):
        if beat.get("chapter") == chapter and beat.get("scene") == scene:
            return beat
    return None


def _load_characters_by_name(names: list[str]) -> list[dict]:
    data = _read_json(store_dir() / "characters.json")
    by_name = {c["name"]: c for c in data.get("characters", []) if c.get("name")}
    return [by_name[name] for name in names if name in by_name]


def load_scene_context(chapter: int, scene: int, tool_context: ToolContext) -> dict:
    """Laedt den kombinierten Kontext fuer eine Szene: Beat, beteiligte
    Figuren (inkl. Sprachregister) und die anwendbaren Weltregeln.

    Args:
        chapter: 1-basierte Kapitelnummer der Zielszene.
        scene: 1-basierte Szenennummer innerhalb des Kapitels.

    Returns:
        `{"status": "success", "chapter": int, "scene": int, "beat": dict |
        None, "characters": list[dict], "world_rules": str | None,
        "style_guide": str | None}`. `beat` ist `None`, solange der Plot
        Agent (TASK-004) noch keinen Beat fuer diese Szene geschrieben hat.
    """
    plot_data = _read_json(store_dir() / "plot_outline.json")
    beat = _find_scene_beat(plot_data, chapter, scene)
    character_names = beat.get("characters_present", []) if beat else []

    result = {
        "status": "success",
        "chapter": chapter,
        "scene": scene,
        "beat": beat,
        "characters": _load_characters_by_name(character_names),
        "world_rules": load_world_bible().get("text"),
        "style_guide": load_style_guide().get("text"),
    }
    # Written directly (not only via an enclosing Agent's output_key), so
    # {scene_context} is available to downstream instructions regardless of
    # whether this tool is wrapped in a dedicated context-loader agent
    # (as in app/pipelines/writing.py, TASK-008) or called ad hoc.
    tool_context.state["scene_context"] = result
    return result


def read_chapter_summaries() -> dict:
    """Liest eine Kurz-Zusammenfassung (erste ~300 Zeichen) jedes vorhandenen
    Kapitels im Manuskript.

    Returns:
        `{"status": "success", "summaries": [{"chapter": int, "summary": str}, ...]}`,
        aufsteigend nach Kapitelnummer sortiert. Ist noch kein Kapitel
        geschrieben, ist `summaries` eine leere Liste.
    """
    # Local import to avoid a module-level cycle (manuscript.py doesn't
    # import context_loader, but keeps the two tool modules independently
    # importable for callers that only need one of them).
    from app.tools.manuscript import list_chapters, read_manuscript

    summaries = []
    for entry in list_chapters().get("chapters", []):
        chapter_num = entry["chapter"]
        result = read_manuscript(chapter_num)
        text = result.get("text", "") if result.get("status") == "success" else ""
        snippet = " ".join(text.split())[:300]
        summaries.append({"chapter": chapter_num, "summary": snippet})
    return {"status": "success", "summaries": summaries}


def update_plot_outline(
    chapter: int,
    scene: int,
    pov_character: str,
    location: str,
    beat: str,
    turning_point: bool,
    tension_level: int,
    characters_present: list[str],
) -> dict:
    """Schreibt oder aktualisiert einen Szenen-Beat in `plot_outline.json`.

    Idempotent: ein bereits vorhandener Beat fuer dasselbe (chapter, scene)
    wird ersetzt, alle anderen Beats und die bestehenden `phases` bleiben
    unveraendert.

    Args:
        chapter: 1-basierte Kapitelnummer.
        scene: 1-basierte Szenennummer innerhalb des Kapitels.
        pov_character: Name der Point-of-View-Figur.
        location: Schauplatz der Szene.
        beat: Kurzbeschreibung, was in der Szene passiert.
        turning_point: Ist dieser Beat ein Wendepunkt?
        tension_level: Spannungslevel 1-10 (wird auf diesen Bereich geklemmt).
        characters_present: Namen aller anwesenden Figuren.

    Returns:
        `{"status": "success", "chapter": int, "scene": int}`.
    """
    path = store_dir() / "plot_outline.json"
    data = _read_json(path)
    beats = data.setdefault("scene_beats", [])
    new_beat = {
        "chapter": chapter,
        "scene": scene,
        "pov_character": pov_character,
        "location": location,
        "beat": beat,
        "turning_point": turning_point,
        "tension_level": max(
            _MIN_TENSION_LEVEL, min(_MAX_TENSION_LEVEL, tension_level)
        ),
        "characters_present": characters_present,
    }
    for index, existing in enumerate(beats):
        if existing.get("chapter") == chapter and existing.get("scene") == scene:
            beats[index] = new_beat
            break
    else:
        beats.append(new_beat)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {"status": "success", "chapter": chapter, "scene": scene}
