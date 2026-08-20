"""Helpers for reading eval-instance data: `agent_data.turns` and the
`{prompt}`/`{response}` `Content`-shaped dicts produced by `eval generate`.
"""

from __future__ import annotations


def get_turns(instance: dict) -> list[dict]:
    """Returns `instance["agent_data"]["turns"]`, or `[]` if absent."""
    agent_data = instance.get("agent_data") or {}
    return agent_data.get("turns") or []


def extract_text(content: object) -> str:
    """Extracts concatenated text from a `Content`-shaped value.

    Handles the `{"role": ..., "parts": [{"text": "..."}]}` shape that
    `instance["prompt"]`/`instance["response"]` carry in `custom_function`
    callbacks. Plain strings and anything else pass through as `str(...)`.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        parts = content.get("parts", [])
        texts = [
            part.get("text", "")
            for part in parts
            if isinstance(part, dict) and part.get("text")
        ]
        if texts:
            return " ".join(texts)
        return ""
    return str(content)


def get_tool_calls(instance: dict) -> list[dict]:
    """Flattens every `function_call` part across all turns/events.

    Trace shape varies by ADK version; this walks both a `turn["events"]`
    list and a flat `turn["parts"]` list, whichever is present, and collects
    any dict that looks like a function call (`name` + `args`).
    """
    calls: list[dict] = []
    for turn in get_turns(instance):
        events = turn.get("events") or turn.get("parts") or []
        for event in events:
            if not isinstance(event, dict):
                continue
            content = event.get("content", event)
            parts = content.get("parts", []) if isinstance(content, dict) else []
            for part in parts:
                if isinstance(part, dict) and "function_call" in part:
                    calls.append(part["function_call"])
    return calls
