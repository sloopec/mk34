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

"""Manuskript-Tools: read/write/list/stats gegen `<MK34_BOOK_ROOT>/manuscript/`.

Szenengrenzen werden ueber Markdown-Marker realisiert (`<!-- scene:N -->`),
damit `write_scene` eine einzelne Szene idempotent ersetzen kann, ohne die
uebrigen Szenen des Kapitels stillschweigend zu ueberschreiben. Diese Tools
sind szenen-agnostisch (reiner Dateizugriff) -- der Agent, der `write_scene`
kreativ befuellt, kommt erst in `03-szenen-und-lokales-llm/TASK-002`
(siehe `.claude/plans/02-agenten-kern-und-kontinuitaet/tasks/TASK-001-manuskript-tools.md`).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.tools._paths import manuscript_dir, resolve_within, store_dir

_SCENE_MARKER = re.compile(r"<!-- scene:(\d+) -->")
_CHAPTER_FILENAME_RE = re.compile(r"^chapter_(\d+)\.md$")
_MAX_CHAPTER = 9999
_MAX_SCENE = 9999


class ManuscriptPathError(ValueError):
    """Raised for invalid/unsafe chapter or scene identifiers."""


def _validate_number(value: object, *, label: str, maximum: int) -> int:
    if isinstance(value, bool):  # bool is an int subclass -- reject explicitly
        raise ManuscriptPathError(f"Ungueltige {label}: {value!r}")
    try:
        number = int(value)  # rejects "1/../../etc" etc. -- not a valid int
    except (TypeError, ValueError) as exc:
        raise ManuscriptPathError(f"Ungueltige {label}: {value!r}") from exc
    if number <= 0 or number > maximum:
        raise ManuscriptPathError(
            f"{label} ausserhalb des gueltigen Bereichs: {number}"
        )
    return number


def _chapter_path(chapter: object) -> Path:
    number = _validate_number(chapter, label="Kapitelnummer", maximum=_MAX_CHAPTER)
    return resolve_within(manuscript_dir(), f"chapter_{number:02d}.md")


def _parse_scenes(content: str) -> dict[int, str]:
    """Splits chapter markdown into `{scene_number: scene_text}`."""
    matches = list(_SCENE_MARKER.finditer(content))
    scenes: dict[int, str] = {}
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        scenes[int(match.group(1))] = content[start:end].strip("\n")
    return scenes


def _extract_header(content: str) -> str | None:
    """Returns the free-text header before the first scene marker, if any."""
    match = _SCENE_MARKER.search(content)
    header = content[: match.start()] if match else content
    header = header.strip()
    return header or None


def _render_chapter(chapter: int, scenes: dict[int, str], header: str | None) -> str:
    lines: list[str] = []
    if header:
        lines.append(header)
        lines.append("")
    else:
        lines.append(f"# Kapitel {chapter}")
        lines.append("")
    for number in sorted(scenes):
        lines.append(f"<!-- scene:{number} -->")
        lines.append(scenes[number].strip())
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def read_manuscript(chapter: int) -> dict:
    """Liest den vollstaendigen Text eines Kapitels aus dem Manuskript.

    Args:
        chapter: 1-basierte Kapitelnummer.

    Returns:
        Bei Erfolg `{"status": "success", "chapter": int, "text": str,
        "scene_count": int}`. Existiert das Kapitel nicht:
        `{"status": "not_found", "chapter": int}`. Bei ungueltiger
        Kapitelnummer: `{"status": "error", "message": str}`.
    """
    try:
        path = _chapter_path(chapter)
    except ManuscriptPathError as exc:
        return {"status": "error", "message": str(exc)}
    if not path.exists():
        return {"status": "not_found", "chapter": chapter}
    content = path.read_text(encoding="utf-8")
    scenes = _parse_scenes(content)
    return {
        "status": "success",
        "chapter": chapter,
        "text": content,
        "scene_count": len(scenes),
    }


def write_scene(chapter: int, scene: int, text: str) -> dict:
    """Schreibt oder ersetzt genau eine Szene innerhalb einer Kapiteldatei.

    Ueberschreibt niemals ein ganzes Kapitel: bestehende Szenen desselben
    Kapitels bleiben unveraendert, nur die angegebene Szenennummer wird
    ersetzt bzw. neu angelegt. Legt die Kapiteldatei an, falls sie noch
    nicht existiert.

    Args:
        chapter: 1-basierte Kapitelnummer.
        scene: 1-basierte Szenennummer innerhalb des Kapitels.
        text: Der vollstaendige Szenentext (darf nicht leer sein).

    Returns:
        Bei Erfolg `{"status": "success", "chapter": int, "scene": int,
        "scene_count": int}`. Bei ungueltigen Eingaben oder leerem Text:
        `{"status": "error", "message": str}`.
    """
    try:
        path = _chapter_path(chapter)
        scene_number = _validate_number(scene, label="Szenennummer", maximum=_MAX_SCENE)
    except ManuscriptPathError as exc:
        return {"status": "error", "message": str(exc)}
    if not isinstance(text, str) or not text.strip():
        return {"status": "error", "message": "Szenentext darf nicht leer sein."}

    header: str | None = None
    scenes: dict[int, str] = {}
    if path.exists():
        content = path.read_text(encoding="utf-8")
        scenes = _parse_scenes(content)
        header = _extract_header(content)

    scenes[scene_number] = text.strip()
    path.write_text(_render_chapter(chapter, scenes, header), encoding="utf-8")
    return {
        "status": "success",
        "chapter": chapter,
        "scene": scene_number,
        "scene_count": len(scenes),
    }


def list_chapters() -> dict:
    """Listet alle vorhandenen Kapitel im Manuskript mit ihrer Szenenzahl.

    Returns:
        `{"status": "success", "chapters": [{"chapter": int,
        "scene_count": int}, ...]}`, aufsteigend sortiert nach Kapitelnummer.
    """
    chapters: list[dict] = []
    for path in sorted(manuscript_dir().iterdir()):
        match = _CHAPTER_FILENAME_RE.match(path.name)
        if not match:
            continue
        content = path.read_text(encoding="utf-8")
        chapters.append(
            {"chapter": int(match.group(1)), "scene_count": len(_parse_scenes(content))}
        )
    chapters.sort(key=lambda c: c["chapter"])
    return {"status": "success", "chapters": chapters}


def _known_character_names() -> list[str]:
    characters_path = store_dir() / "characters.json"
    if not characters_path.exists():
        return []
    try:
        data = json.loads(characters_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [c["name"] for c in data.get("characters", []) if c.get("name")]


def _characters_mentioned(text: str) -> list[str]:
    present = []
    for name in _known_character_names():
        # Match on the last name-token too (e.g. "Sarah" for "Dr. Sarah Lin"),
        # so dialogue-only mentions ("Sarah sagte...") are still detected.
        tokens = [name, *name.split()]
        if any(token and token in text for token in tokens):
            present.append(name)
    return present


def chapter_stats(chapter: int) -> dict:
    """Liefert Wortzahl, Szenenzahl und auftretende Figuren fuer ein Kapitel.

    Args:
        chapter: 1-basierte Kapitelnummer.

    Returns:
        Bei Erfolg `{"status": "success", "chapter": int, "word_count": int,
        "scene_count": int, "characters_present": list[str]}`. Existiert das
        Kapitel nicht: `{"status": "not_found", "chapter": int}`.
    """
    result = read_manuscript(chapter)
    if result["status"] != "success":
        return result
    text = result["text"]
    return {
        "status": "success",
        "chapter": chapter,
        "word_count": len(re.findall(r"\S+", text)),
        "scene_count": result["scene_count"],
        "characters_present": _characters_mentioned(text),
    }
