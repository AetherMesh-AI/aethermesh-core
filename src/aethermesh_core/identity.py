"""Local node identity persistence helpers."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from aethermesh_core.json_io import atomic_write_json
from aethermesh_core.models import NodeIdentity

IDENTITY_SCHEMA_VERSION = 1


class IdentityPersistenceError(ValueError):
    """Raised when local identity JSON cannot be safely loaded or saved."""


def load_or_create_identity(path: str | Path) -> NodeIdentity:
    """Load a versioned local node identity, creating one if the file is missing."""

    identity_path = Path(path)
    if identity_path.exists():
        return _load_identity(identity_path)

    identity = NodeIdentity(node_id=f"local-{uuid4().hex}")
    _save_identity(identity_path, identity)
    return identity


def _load_identity(path: Path) -> NodeIdentity:
    try:
        with path.open("r", encoding="utf-8") as handle:
            document = json.load(handle)
    except json.JSONDecodeError as exc:
        raise IdentityPersistenceError(
            f"identity JSON is malformed: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise IdentityPersistenceError(f"could not read identity file: {exc}") from exc

    if not isinstance(document, dict):
        raise IdentityPersistenceError("identity JSON must be an object")
    version = document.get("version")
    if version != IDENTITY_SCHEMA_VERSION:
        raise IdentityPersistenceError("identity JSON must contain version 1")
    node = document.get("node")
    if not isinstance(node, dict):
        raise IdentityPersistenceError("identity JSON field 'node' must be an object")
    node_id = node.get("node_id")
    if not isinstance(node_id, str) or not node_id:
        raise IdentityPersistenceError(
            "identity JSON field 'node.node_id' must be a non-empty string"
        )
    return NodeIdentity(node_id=node_id)


def _save_identity(path: Path, identity: NodeIdentity) -> None:
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    document = _identity_document(identity)
    try:
        atomic_write_json(path, document)
    except OSError as exc:
        raise IdentityPersistenceError(f"could not write identity file: {exc}") from exc


def _identity_document(identity: NodeIdentity) -> dict[str, object]:
    return {
        "version": IDENTITY_SCHEMA_VERSION,
        "node": {"node_id": identity.node_id},
    }
