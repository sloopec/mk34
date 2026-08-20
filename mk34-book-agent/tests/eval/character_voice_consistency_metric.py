"""Local LLM-as-judge for `character_voice_consistency` (see eval_config.yaml).
tier: craft.
"""

import sys
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parent
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from mk34_eval.judge import judge  # noqa: E402
from mk34_eval.trace import extract_text  # noqa: E402


def evaluate(instance):
    return judge(
        rubric="character_voice_consistency",
        prompt=extract_text(instance.get("prompt")),
        response=extract_text(instance.get("response")),
        agent_data=instance.get("agent_data"),
    )
