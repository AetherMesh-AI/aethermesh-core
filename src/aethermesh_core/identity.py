"""Local node identity persistence helpers."""

from __future__ import annotations

import json
import socket
import subprocess  # nosec B404 - fixed local machine-id commands only; no user input.
import sys
from collections.abc import Callable
from hashlib import sha256
from pathlib import Path

from aethermesh_core.json_io import atomic_write_json
from aethermesh_core.models import NodeIdentity

IDENTITY_SCHEMA_VERSION = 1
DARWIN_UUID_COMMAND = (
    "ioreg -rd1 -c IOPlatformExpertDevice | awk '/IOPlatformUUID/ { print $3; }'"
)

FileReader = Callable[[str], str]
CommandRunner = Callable[..., str]
HostnameReader = Callable[[], str]


class IdentityPersistenceError(ValueError):
    """Raised when local identity JSON cannot be safely loaded or saved."""


def load_or_create_identity(
    path: str | Path,
    *,
    goos: str | None = None,
    read_file: FileReader | None = None,
    run_command: CommandRunner | None = None,
    read_hostname: HostnameReader | None = None,
) -> NodeIdentity:
    """Load a versioned local node identity, creating one if the file is missing."""

    identity_path = Path(path)
    if identity_path.exists():
        return _load_identity(identity_path)

    identity = NodeIdentity(
        node_id=deterministic_machine_node_id(
            goos=goos,
            read_file=read_file,
            run_command=run_command,
            read_hostname=read_hostname,
        )
    )
    _save_identity(identity_path, identity)
    return identity


def deterministic_machine_node_id(
    *,
    goos: str | None = None,
    read_file: FileReader | None = None,
    run_command: CommandRunner | None = None,
    read_hostname: HostnameReader | None = None,
) -> str:
    """Return a stable local node id derived from machine identifiers."""

    fingerprint = _machine_fingerprint(
        _default_goos() if goos is None else goos,
        _read_text_file if read_file is None else read_file,
        _run_command if run_command is None else run_command,
        socket.gethostname if read_hostname is None else read_hostname,
    )
    return f"local-{sha256(fingerprint.encode('utf-8')).hexdigest()}"


def _machine_fingerprint(
    goos: str,
    read_file: FileReader | None,
    run_command: CommandRunner | None,
    read_hostname: HostnameReader | None,
) -> str:
    parts: list[str]
    if goos == "linux":
        parts = [
            _read_or_empty(read_file, "/etc/machine-id"),
            _read_or_empty(read_file, "/var/lib/dbus/machine-id"),
            _run_or_empty(run_command, "cat", "/sys/class/dmi/id/product_uuid"),
        ]
    elif goos == "windows":
        parts = [
            _run_or_empty(run_command, "wmic", "csproduct", "get", "uuid"),
            _run_or_empty(
                run_command,
                "powershell",
                "-command",
                "Get-WmiObject Win32_ComputerSystemProduct | Select-Object -ExpandProperty UUID",
            ),
        ]
    elif goos == "darwin":
        parts = [_run_or_empty(run_command, "sh", "-c", DARWIN_UUID_COMMAND)]
    else:
        parts = ["unknown-os", goos]

    filtered = _filter_empty(parts)
    if filtered:
        return "|".join(filtered)
    return "|".join(_fallback_parts(goos, read_hostname))


def _default_goos() -> str:
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "darwin"
    if sys.platform.startswith("win"):
        return "windows"
    return sys.platform


def _read_text_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8").strip()


def _run_command(name: str, *args: str) -> str:
    return subprocess.check_output(  # nosec B603 - fixed machine-id probes, shell disabled.
        [name, *args], stderr=subprocess.STDOUT, text=True
    ).strip()


def _read_or_empty(read_file: FileReader | None, path: str) -> str:
    if read_file is None:
        return ""
    try:
        return read_file(path).strip()
    except OSError:
        return ""


def _run_or_empty(
    run_command: CommandRunner | None,
    name: str,
    *args: str,
) -> str:
    if run_command is None:
        return ""
    try:
        return run_command(name, *args).strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _fallback_parts(goos: str, read_hostname: HostnameReader | None) -> list[str]:
    parts = ["fallback-os", goos]
    if read_hostname is None:
        return parts
    try:
        hostname = read_hostname().strip()
    except OSError:
        return parts
    if hostname:
        parts.append(hostname)
    return parts


def _filter_empty(values: list[str]) -> list[str]:
    return [trimmed for value in values if (trimmed := value.strip())]


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
