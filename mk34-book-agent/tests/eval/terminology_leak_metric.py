"""Deterministic metric `terminology_leak` (see eval_config.yaml).

Prueft die harte Terminologie-Regel aus `world_bible.md` Abschnitt 3, Regel 6
/ `style_guide.md` Abschnitt 1: David (und die uebrigen Laien-Figuren)
sagen nie "Naniten"; die Wissenschaftler-Figuren (Sarah, Voss, Aris) sagen
nie "Nanobots". Deterministisch ueber Satz-Naeherung (Figurenname + Begriff
im selben Satz) -- keine echte Sprecherzuordnung, analog zur bereits
etablierten `_check_terminology`-Logik in `app/tools/consistency.py`.

Bewusst self-contained (kein `import app`) -- siehe Docstring von
`pov_character_present_metric.py` fuer die Begruendung.
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

# (Figuren-Namenstoken, verbotener Begriff, Regel-Referenz) -- siehe
# style_guide.md Abschnitt 1 / world_bible.md Regel 6.
_LAIEN_TOKENS = ["David", "Ronan", "Vorstand"]
_WISSENSCHAFT_TOKENS = [
    "Sarah",
    "Dr. Sarah Lin",
    "Voss",
    "Dr. Elias Voss",
    "Aris",
    "Dr. Aris",
]


def _split_sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def evaluate(instance):
    response_text = extract_text(instance.get("response"))
    violations: list[str] = []

    for sentence in _split_sentences(response_text):
        lowered = sentence.lower()
        if any(token.lower() in lowered for token in _LAIEN_TOKENS) and (
            "naniten" in lowered
        ):
            violations.append(f"Laien-Figur + 'Naniten': {sentence.strip()!r}")
        if any(token.lower() in lowered for token in _WISSENSCHAFT_TOKENS) and (
            "nanobots" in lowered
        ):
            violations.append(f"Wissenschafts-Figur + 'Nanobots': {sentence.strip()!r}")

    if violations:
        return {
            "score": 0,
            "explanation": "Terminologie-Registerbruch gefunden: "
            + "; ".join(violations),
        }
    return {"score": 1, "explanation": "Kein Terminologie-Registerbruch gefunden."}
