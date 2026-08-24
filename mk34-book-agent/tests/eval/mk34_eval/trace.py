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


def get_state_delta(instance: dict, key: str) -> object | None:
    """Returns the last value written to `state[key]` across all events in
    the trace (`actions.stateDelta[key]`), or `None` if never written.

    Used by deterministic metrics that need to inspect what a
    `before_agent_callback`/`after_agent_callback`/tool wrote into session
    state during the run (e.g. `state["route"]`, Plan 3/TASK-004/005),
    rather than the agent's free-text final response. Trace shape varies by
    ADK version; this walks both a `turn["events"]` list and a flat
    `turn["parts"]` list, whichever is present, analogous to
    `get_tool_calls`.
    """
    value = None
    for turn in get_turns(instance):
        events = turn.get("events") or turn.get("parts") or []
        for event in events:
            if not isinstance(event, dict):
                continue
            actions = event.get("actions")
            if not isinstance(actions, dict):
                continue
            state_delta = actions.get("stateDelta")
            if isinstance(state_delta, dict) and key in state_delta:
                value = state_delta[key]
    return value


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
