"""Deterministic metric `scene_word_count_in_range` (see eval_config.yaml).

Prueft, ob die generierte Szene innerhalb eines plausiblen Wortzahl-
Korridors liegt -- weder ein Fragment (wenige Saetze) noch ein unkontrolliert
langes Kapitel-Konvolut statt einer einzelnen Szene.

**Provisorischer Korridor:** die exakten Korridore pro Szene sind eine noch
offene Autoren-Entscheidung (`.claude/plans/01-fundament-und-kontext/plan.md`
-> Offene Frage #1 "Wortzahl-Korridore"). Bis der Autor engere, szenen-
spezifische Werte liefert, gilt hier ein bewusst weiter, generischer
Korridor (250-1800 Woerter) als Fragment-/Runaway-Schutz -- kein
Qualitaetsurteil ueber die ideale Szenenlaenge.
"""

from __future__ import annotations

import re
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

MIN_WORDS = 250
MAX_WORDS = 1800


def evaluate(instance):
    response_text = extract_text(instance.get("response"))
    word_count = len(re.findall(r"\S+", response_text))

    if MIN_WORDS <= word_count <= MAX_WORDS:
        return {
            "score": 1,
            "explanation": f"{word_count} Woerter, im Korridor [{MIN_WORDS}, {MAX_WORDS}].",
        }
    return {
        "score": 0,
        "explanation": (
            f"{word_count} Woerter, ausserhalb des Korridors [{MIN_WORDS}, {MAX_WORDS}]."
        ),
    }
