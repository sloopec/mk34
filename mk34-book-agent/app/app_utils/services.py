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

"""Process-wide ADK session/artifact services shared by every serving surface.

Registered under ``shared://`` so the ADK web routes, the A2A path, and the
reasoning_engine adapter share one instance: a session created on any surface
is visible to the others.
"""

from __future__ import annotations

import functools
import os
from pathlib import Path

from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService
from google.adk.cli.service_registry import get_service_registry
from google.adk.cli.utils.service_factory import create_session_service_from_options
from google.adk.sessions import DatabaseSessionService

SESSION_SERVICE_URI = "shared://session"
ARTIFACT_SERVICE_URI = "shared://artifact"

# mk34 (Entscheidung E3, plan.md): persistente Sessions ab dem ersten Setup.
# Voraussetzung fuer runner.rewind_async (Phase 5) und sitzungsuebergreifendes
# Weiterarbeiten ueber mehrere `agents-cli run`-Aufrufe hinweg. Ueberschreibbar
# via MK34_SESSION_DB_URL (siehe plan.md -> Configuration).
#
# Abweichung von plan.md/TASK-001 ("sqlite:///./data/sessions.db"): ADK 2.7's
# DatabaseSessionService requires an async SQLAlchemy driver
# (sqlalchemy.exc.InvalidRequestError otherwise) -- the plain "sqlite://"
# scheme uses the sync pysqlite driver. Using "sqlite+aiosqlite://" instead;
# same file, same directory, same gitignore rule.
DEFAULT_SESSION_DB_URL = "sqlite+aiosqlite:///./data/sessions.db"

_AGENT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


def _ensure_sqlite_parent_dir(db_url: str) -> None:
    """Creates the parent directory for a file-based sqlite URL if needed.

    SQLite (via aiosqlite/pysqlite) refuses to open a database file whose
    parent directory does not exist yet -- unlike most server-backed
    SQLAlchemy dialects, it never creates it for you. `data/` is gitignored,
    so on a fresh checkout it simply does not exist until now.
    """
    from sqlalchemy.engine import make_url

    url = make_url(db_url)
    if url.get_backend_name() != "sqlite" or not url.database:
        return
    if url.database == ":memory:":
        return
    db_path = Path(url.database)
    if not db_path.is_absolute():
        db_path = Path(_AGENT_DIR) / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)


@functools.cache
def get_session_service():
    """Process-wide session service shared across every serving surface."""
    if uri := os.environ.get("SESSION_SERVICE_URI"):
        return create_session_service_from_options(
            base_dir=_AGENT_DIR, session_service_uri=uri
        )
    if agent_engine_id := os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID"):
        from google.adk.sessions.vertex_ai_session_service import VertexAiSessionService

        return VertexAiSessionService(
            project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
            # Runtime-injected agent-engine region, not GOOGLE_CLOUD_LOCATION
            # (which agent.py pins to "global").
            location=os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_LOCATION")
            or os.environ.get("GOOGLE_CLOUD_LOCATION"),
            agent_engine_id=agent_engine_id,
        )
    db_url = os.environ.get("MK34_SESSION_DB_URL", DEFAULT_SESSION_DB_URL)
    _ensure_sqlite_parent_dir(db_url)
    return DatabaseSessionService(db_url=db_url)


@functools.cache
def get_artifact_service():
    """Process-wide artifact service: GCS when a bucket is set, else in-memory."""
    if bucket := os.environ.get("LOGS_BUCKET_NAME"):
        return GcsArtifactService(bucket_name=bucket)
    return InMemoryArtifactService()


_registry = get_service_registry()
_registry.register_session_service("shared", lambda uri, **kw: get_session_service())
_registry.register_artifact_service("shared", lambda uri, **kw: get_artifact_service())
