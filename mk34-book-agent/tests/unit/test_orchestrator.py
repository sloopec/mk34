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

"""Unit tests for `app/agent.py`'s Orchestrator `root_agent` (TASK-007).

Structure only, no live LLM call -- see TASK-007 walkthrough for the live
`agents-cli run` routing verification.
"""

from __future__ import annotations

from google.adk.tools import AgentTool

from app.agent import app, root_agent


def test_root_agent_is_the_orchestrator() -> None:
    assert root_agent.name == "orchestrator"


def test_app_name_matches_agent_directory() -> None:
    # Prevents "Session not found" during eval (ADK infers the app name from
    # the directory path; a mismatch here breaks agents-cli eval).
    assert app.name == "app"


def test_root_agent_has_plot_and_editor_as_sub_agents() -> None:
    sub_agent_names = {a.name for a in root_agent.sub_agents}
    assert sub_agent_names == {"plot_agent", "editor_agent"}


def test_root_agent_has_character_agent_as_agent_tool() -> None:
    agent_tools = [t for t in root_agent.tools if isinstance(t, AgentTool)]
    assert len(agent_tools) == 1
    assert agent_tools[0].agent.name == "character_agent"


def test_root_agent_has_read_only_lookup_tools() -> None:
    plain_tool_names = {
        getattr(t, "__name__", None)
        for t in root_agent.tools
        if not isinstance(t, AgentTool)
    }
    assert plain_tool_names == {"list_chapters", "chapter_stats", "load_plot_outline"}


def test_root_agent_has_initialize_state_callback() -> None:
    assert root_agent.before_agent_callback is not None
