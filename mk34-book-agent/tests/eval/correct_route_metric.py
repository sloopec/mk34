"""Deterministic metric `correct_route` (see eval_config.yaml, Plan 3,
TASK-004/005, Stufe B).

Prueft nicht den Szenentext, sondern die **Route**: liest
`state["route"]` (gesetzt vom Content-Classifier bzw. einem manuellen
Override, `app/pipelines/writing.py::_apply_route_decision`) aus dem Trace
und vergleicht sie gegen die im `eval_case_id`-Praefix kodierte erwartete
Route (`local_...`/`cloud_...`, siehe `tests/eval/datasets/
uncensored-routing.json`).

**Warum ueber `eval_case_id` statt eines eigenen Dataset-Feldes:** das
dokumentierte `agents-cli eval`-Dataset-Schema (`tests/eval/datasets/
README.md`) fuehrt nur `eval_case_id`/`prompt`/`agent_data` als garantierte
Felder; ob zusaetzliche, frei erfundene Felder zuverlaessig bis in die
`custom_function`-`instance` durchgereicht werden, ist nicht dokumentiert.
`eval_case_id` ist dagegen garantiert vorhanden -- die erwartete Route steht
deshalb als Praefix direkt im Case-Namen.
"""

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

from mk34_eval.trace import get_state_delta  # noqa: E402

_VALID_ROUTES = ("local", "cloud")


def evaluate(instance):
    case_id = instance.get("eval_case_id") or ""
    expected = next((r for r in _VALID_ROUTES if case_id.startswith(f"{r}_")), None)
    if expected is None:
        # Kein Routing-Case (z. B. scene-writing.json) -- nicht anwendbar,
        # vacuously pass statt fehlerhaftem Abzug auf nicht dafuer gedachten
        # Datasets (analog zu pov_character_present_metric.py).
        return {
            "score": 1,
            "explanation": (
                f"eval_case_id {case_id!r} hat kein 'local_'/'cloud_'-Praefix -- "
                "kein Routing-Case, nicht anwendbar."
            ),
        }

    actual = get_state_delta(instance, "route")
    if actual is None:
        return {
            "score": 0,
            "explanation": "Kein state['route'] im Trace gefunden (Classifier-Schritt "
            "hat nicht gelaufen oder stateDelta fehlt im Trace-Format).",
        }
    if actual == expected:
        return {
            "score": 1,
            "explanation": f"Erwartete Route {expected!r} korrekt gesetzt.",
        }
    return {
        "score": 0,
        "explanation": f"Erwartete Route {expected!r}, tatsaechlich {actual!r}.",
    }
