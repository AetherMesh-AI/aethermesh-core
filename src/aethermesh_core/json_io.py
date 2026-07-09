"""Shared JSON file persistence helpers for local-only artifacts."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any


def atomic_write_json(path: Path, document: dict[str, Any]) -> None:
    """Write one JSON document using a temp file and atomic replace."""

    _publish_json(path, document, os.replace)


def atomic_create_json(path: Path, document: dict[str, Any]) -> None:
    """Create one JSON document atomically without replacing an existing file."""

    _publish_json(path, document, os.link)


def _publish_json(
    path: Path, document: dict[str, Any], publish: Callable[[str, Path], None]
) -> None:
    parent = path.parent
    temp_name: str | None = None
    try:
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            json.dump(document, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        publish(temp_name, path)
    except (OSError, TypeError, ValueError):
        if temp_name is not None:
            remove_temp_file(temp_name)
        raise
    remove_temp_file(temp_name)


def remove_temp_file(path: str) -> None:
    """Best-effort removal for abandoned atomic-write temp files."""

    try:
        os.unlink(path)
    except FileNotFoundError:
        return
