"""Provider-agnostic LLM-judge for mk34's local eval-grundgeruest (TASK-003).

`judge(rubric, prompt, response, agent_data)` is the single call site every
`custom_metrics` function goes through. The model is resolved from the
rubric's `tier` frontmatter (`fast` -> `MK34_JUDGE_MODEL_FAST`, `craft` ->
`MK34_JUDGE_MODEL_CRAFT`, Entscheidung E4) directly from the process
environment (`os.environ`) -- never hardcoded at the call site. The provider
is resolved from the model string's prefix (`gemini-*` -> `google-genai` SDK,
`claude-*` -> `anthropic` SDK), so switching a judge tier from Gemini to
Claude is a `.env` change, not a code change (Entscheidung E6).

Deliberately independent of `app.*`: `agents-cli eval grade` executes
`custom_metrics` in its own Python environment (a separate `uv tool install`,
not this project's `.venv`), which does not have `google-adk` installed.
Importing anything under the `app` package would trigger `app/__init__.py`
(which imports `app.agent` -> `google.adk`) and fail there -- so this module
reads `MK34_JUDGE_MODEL_FAST`/`MK34_JUDGE_MODEL_CRAFT` straight from
`os.environ`, using the same defaults as `app/config.py`'s `Settings`,
instead of going through `app.config.get_settings()`.
"""

from __future__ import annotations

import json
import os
import re
import time
from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel

RUBRICS_DIR = Path(__file__).resolve().parent / "rubrics"
_MAX_RETRIES = 2
_RETRY_BASE_DELAY_SECONDS = 0.5

# Mirrors app/config.py's Settings defaults (Startwerte E4/E6) -- kept in
# sync manually since this module cannot import app.config (see docstring).
_DEFAULT_JUDGE_MODEL_FAST = "gemini-3.7-flash"
_DEFAULT_JUDGE_MODEL_CRAFT = "gemini-3.1-pro-preview"


class Verdict(BaseModel):
    """Schema-enforced judge output."""

    score: int
    explanation: str


class _CostLog:
    """Judge call counts, separated by tier -- TASK-003 acceptance criterion
    "Judge-Kosten werden getrennt nach Stufe protokolliert"."""

    def __init__(self) -> None:
        self._counts: dict[str, int] = {"fast": 0, "craft": 0}

    def record(self, tier: str) -> None:
        self._counts[tier] = self._counts.get(tier, 0) + 1

    def snapshot(self) -> dict[str, int]:
        return dict(self._counts)

    def reset(self) -> None:
        self._counts = {"fast": 0, "craft": 0}


cost_log = _CostLog()


def load_rubric(name: str) -> tuple[str, str]:
    """Loads `rubrics/<name>.md`, returns `(tier, rubric_body)`.

    Raises:
        FileNotFoundError: No rubric file `<name>.md`.
        ValueError: Missing or invalid `tier: fast|craft` frontmatter.
    """
    path = RUBRICS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Rubrik nicht gefunden: {path}")
    raw = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", raw, re.DOTALL)
    if not match:
        raise ValueError(
            f"Rubrik {name!r} hat kein Frontmatter (erwartet 'tier: fast|craft')."
        )
    frontmatter, body = match.groups()
    tier_match = re.search(r"^tier:\s*(fast|craft)\s*$", frontmatter, re.MULTILINE)
    if not tier_match:
        raise ValueError(f"Rubrik {name!r}: Frontmatter-Feld 'tier' fehlt/ungueltig.")
    return tier_match.group(1), body.strip()


def _model_for_tier(tier: str) -> str:
    if tier == "fast":
        return os.environ.get("MK34_JUDGE_MODEL_FAST", _DEFAULT_JUDGE_MODEL_FAST)
    return os.environ.get("MK34_JUDGE_MODEL_CRAFT", _DEFAULT_JUDGE_MODEL_CRAFT)


def _provider_for_model(model: str) -> str:
    if model.startswith("gemini-"):
        return "google-genai"
    if model.startswith("claude-"):
        return "anthropic"
    raise ValueError(f"Unbekannter Judge-Provider fuer Modell {model!r}")


def _build_prompt(
    rubric_body: str, prompt: str, response: str, agent_data: object
) -> str:
    return (
        "Du bist ein strenger, konsistenter Gutachter (Judge) fuer ein "
        "KI-Agentensystem. Bewerte ausschliesslich anhand der folgenden Rubrik.\n\n"
        f"# Rubrik\n{rubric_body}\n\n"
        f"# User-Prompt\n{prompt}\n\n"
        f"# Agenten-Antwort\n{response}\n\n"
        f"# Vollstaendiger Trace (Tool-Aufrufe, Zwischenschritte)\n{agent_data}\n\n"
        "Antworte ausschliesslich mit validem JSON exakt in diesem Format: "
        '{"score": <ganze Zahl 1-5>, "explanation": "<kurze Begruendung auf Deutsch>"}.'
    )


def _get_genai_client():
    from google import genai

    return genai.Client()


def _get_anthropic_client():
    import anthropic

    return anthropic.Anthropic()


def _extract_json(text: str) -> str:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text


def _call_gemini(model: str, prompt: str) -> Verdict:
    from google.genai import types

    client = _get_genai_client()
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0,  # deterministic grading
                    response_mime_type="application/json",
                    response_schema=Verdict,
                ),
            )
            if response.parsed is not None:
                return response.parsed
            last_exc = ValueError("Gemini-Judge lieferte kein parsbares Ergebnis.")
        except Exception as exc:  # retry transient errors (rate limit, 5xx, ...)
            last_exc = exc
        if attempt < _MAX_RETRIES:
            time.sleep(_RETRY_BASE_DELAY_SECONDS * (attempt + 1))
    raise RuntimeError(
        f"Gemini-Judge fehlgeschlagen nach {_MAX_RETRIES + 1} Versuchen: {last_exc}"
    )


def _call_claude(model: str, prompt: str) -> Verdict:
    client = _get_anthropic_client()
    schema = {
        "type": "object",
        "properties": {
            "score": {"type": "integer"},
            "explanation": {"type": "string"},
        },
        "required": ["score", "explanation"],
        "additionalProperties": False,
    }
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=512,
                output_config={"format": {"type": "json_schema", "schema": schema}},
                messages=[{"role": "user", "content": prompt}],
            )
            text_block = next(b for b in response.content if b.type == "text")
            data = json.loads(_extract_json(text_block.text))
            return Verdict(**data)
        except Exception as exc:  # retry transient errors
            last_exc = exc
        if attempt < _MAX_RETRIES:
            time.sleep(_RETRY_BASE_DELAY_SECONDS * (attempt + 1))
    raise RuntimeError(
        f"Claude-Judge fehlgeschlagen nach {_MAX_RETRIES + 1} Versuchen: {last_exc}"
    )


_PROVIDER_CALLERS: dict[str, Callable[[str, str], Verdict]] = {
    "google-genai": _call_gemini,
    "anthropic": _call_claude,
}


def judge(rubric: str, prompt: str, response: str, agent_data: object = None) -> dict:
    """Judges an agent response against a named rubric, on a 1-5 scale.

    Args:
        rubric: Rubric filename without `.md`, resolved against `rubrics/`.
        prompt: The user prompt.
        response: The agent's final response text.
        agent_data: Optional trace (tool calls etc.) for judge context.

    Returns:
        `{"score": int (1-5, clamped), "explanation": str}`.
    """
    tier, rubric_body = load_rubric(rubric)
    model = _model_for_tier(tier)
    provider = _provider_for_model(model)
    caller = _PROVIDER_CALLERS[provider]

    full_prompt = _build_prompt(
        rubric_body, prompt, response, agent_data if agent_data else {}
    )
    verdict = caller(model, full_prompt)
    cost_log.record(tier)

    return {"score": max(1, min(5, verdict.score)), "explanation": verdict.explanation}
