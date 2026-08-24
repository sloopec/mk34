"""Local LLM-as-judge for `character_voice_consistency` (see eval_config.yaml).
tier: craft.

`custom_function_file` scripts are executed by `agents-cli eval grade` via
`exec()`, not imported as a normal module -- `__file__` is not defined in
that scope. Locate `mk34_eval/` relative to the process cwd instead (the CLI
runs from the agent project root, e.g. `mk34-book-agent/`).
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

from mk34_eval.judge import judge  # noqa: E402
from mk34_eval.trace import extract_text  # noqa: E402


def evaluate(instance):
    return judge(
        rubric="character_voice_consistency",
        prompt=extract_text(instance.get("prompt")),
        response=extract_text(instance.get("response")),
        agent_data=instance.get("agent_data"),
    )
