"""Deterministic metric `pov_character_present` (see eval_config.yaml).

Prueft, ob mindestens eine der im Prompt namentlich genannten Kanon-Figuren
auch tatsaechlich im Szenentext (der Antwort) vorkommt -- eine Szene, deren
Prompt eine POV-Figur benennt, aber deren Text komplett an dieser Figur
vorbeischreibt, waere ein Trajektorie-Fehler.

Bewusst self-contained (kein `import app`): `custom_function_file`-Skripte
laufen in `agents-cli eval grade`s eigener Python-Umgebung ohne `google-adk`
(siehe `mk34_eval/judge.py`-Docstring) -- ein `app`-Import wuerde ueber
`app/__init__.py` -> `app.agent` -> `google.adk` scheitern. Die Kanon-
Figurennamen sind deshalb hier dupliziert statt aus `characters.json`
geladen, analog zur bereits etablierten Konvention, Figurennamen direkt in
den Rubriken zu hardcoden (siehe `character_voice_consistency.md`).
"""

from __future__ import annotations

import sys
from pathlib import Path


def _mk34_eval_dir() -> Path:
    for candidate in (Path.cwd() / "tests" / "eval", Path.cwd() / "eval", Path.cwd()):
        if (candidate / "mk34_eval").is_dir():
            return candidate
    raise RuntimeError(
        "mk34_eval-Paket nicht gefunden (weder unter tests/eval noch im cwd "
        f"{Path.cwd()})."
    )


_EVAL_DIR = _mk34_eval_dir()
for _p in (str(_EVAL_DIR), str(Path.cwd())):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from mk34_eval.trace import extract_text  # noqa: E402

# Kanon-Figuren aus `books/life_link/store/characters.json` (Stand Plan 1-3).
# Auch Namensbestandteile ("Sarah" fuer "Dr. Sarah Lin"), analog zu
# `app/tools/manuscript.py::_characters_mentioned`.
_CANON_CHARACTERS = [
    "David",
    "Elena",
    "Dr. Sarah Lin",
    "Sarah",
    "Dr. Elias Voss",
    "Voss",
    "Dr. Aris",
    "Aris",
    "Ronan",
    "Markus",
    "Sophie",
]


def _mentioned(text: str) -> set[str]:
    lowered = text.lower()
    return {name for name in _CANON_CHARACTERS if name.lower() in lowered}


def evaluate(instance):
    prompt_text = extract_text(instance.get("prompt"))
    response_text = extract_text(instance.get("response"))

    prompt_characters = _mentioned(prompt_text)
    if not prompt_characters:
        # Der Prompt nennt keine Kanon-Figur namentlich -- die Metrik kann
        # dann nichts pruefen (kein Trajektorie-Fehlerbeweis moeglich), also
        # kein Abzug (vacuously pass), analog zum Umgang mit fehlendem
        # Kontext in anderen deterministischen Metriken dieses Projekts.
        return {
            "score": 1,
            "explanation": "Keine Kanon-Figur im Prompt genannt -- nicht pruefbar, kein Abzug.",
        }

    response_characters = _mentioned(response_text)
    overlap = prompt_characters & response_characters
    if overlap:
        return {
            "score": 1,
            "explanation": f"Im Prompt genannte Figur(en) kommen im Text vor: {sorted(overlap)}.",
        }
    return {
        "score": 0,
        "explanation": (
            f"Im Prompt genannte Figur(en) {sorted(prompt_characters)} kommen im "
            "Szenentext nicht vor."
        ),
    }
