from __future__ import annotations

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def houston_hospitals_dir() -> Path:
    """Canonical per-hospital ingestion output directory. Always resolves to the
    repo root's houston_hospitals/ regardless of process cwd, matching the
    docker-compose volume mount — HOUSTON_HOSPITALS_PATH overrides it (used by
    the container, set to /app/houston_hospitals).
    """
    override = os.environ.get("HOUSTON_HOSPITALS_PATH")
    if override:
        return Path(override)
    return _REPO_ROOT / "houston_hospitals"
