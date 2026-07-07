"""Local node identity persistence helpers."""

from __future__ import annotations

import csv
import json
import os
import platform
import re
import subprocess  # nosec B404 - fixed local hardware probe commands only; no user input.
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from hashlib import sha256
from io import StringIO
from pathlib import Path
from typing import TextIO

from aethermesh_core.json_io import atomic_write_json
from aethermesh_core.models import NodeIdentity

IDENTITY_SCHEMA_VERSION = 1
UNKNOWN_CPU_ARCHITECTURE = "UNKNOWN_CPU_ARCHITECTURE"
UNKNOWN_CPU_VENDOR = "UNKNOWN_CPU_VENDOR"
UNKNOWN_CPU_BRAND = "UNKNOWN_CPU_BRAND"
UNKNOWN_PHYSICAL_CORE_COUNT = "UNKNOWN_PHYSICAL_CORE_COUNT"
UNKNOWN_LOGICAL_THREAD_COUNT = "UNKNOWN_LOGICAL_THREAD_COUNT"
UNKNOWN_GPU_VENDOR = "UNKNOWN_GPU_VENDOR"
UNKNOWN_GPU_MODEL = "UNKNOWN_GPU_MODEL"
UNKNOWN_GPU_DEVICE_ID = "UNKNOWN_GPU_DEVICE_ID"
UNKNOWN_GPU_COUNT = "UNKNOWN_GPU_COUNT"
UNKNOWN_GPU_VRAM = "UNKNOWN_GPU_VRAM"
UNKNOWN_RAM_GB = "UNKNOWN_RAM_GB"
NO_GPU_DETECTED = "NO_GPU_DETECTED"

FileReader = Callable[[str], str]
CommandRunner = Callable[..., str]
HostnameReader = Callable[[], str]


@dataclass(frozen=True)
class HardwareIdentityInputs:
    """Normalized-source hardware facts used to derive the public node id."""

    cpu_architecture: str
    cpu_vendor: str
    cpu_brand_or_chip_name: str
    physical_core_count: int | str
    logical_thread_count: int | str
    permanent_mac_addresses: tuple[str, ...]
    gpu_vendor: str
    gpu_model_or_chip_name: str
    gpu_device_id_if_available: str
    gpu_count: int | str
    max_gpu_vram_gb: float | int | str
    total_installed_ram_gb: float | int | str


@dataclass(frozen=True)
class HardwareComponentHashes:
    """Readable hardware hash derivation details for tests and debug output."""

    cpu_input: str
    cpu_hash: str
    mac_input: str
    mac_hash: str
    gpu_input: str
    gpu_hash: str
    ram_input: str
    ram_hash: str


class IdentityPersistenceError(ValueError):
    """Raised when local identity JSON cannot be safely loaded or saved."""


def load_or_create_identity(
    path: str | Path,
    *,
    goos: str | None = None,
    read_file: FileReader | None = None,
    run_command: CommandRunner | None = None,
    read_hostname: HostnameReader | None = None,
    hardware_inputs: HardwareIdentityInputs | None = None,
    account_id: str | None = None,
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
            hardware_inputs=hardware_inputs,
            account_id=account_id,
        )
    )
    _save_identity(identity_path, identity)
    return identity


def deterministic_machine_node_id(
    *,
    debug: bool = False,
    output: TextIO | None = None,
    goos: str | None = None,
    read_file: Callable[[str], str] | None = None,
    run_command: Callable[..., str] | None = None,
    read_hostname: Callable[[], str] | None = None,
    hardware_inputs: HardwareIdentityInputs | None = None,
    account_id: str | None = None,
) -> str:
    """Return NODE_ID as the deterministic hardware-root SHA256 hex string.

    account_id is accepted only to keep account ownership concerns separate from
    node identity derivation. It is intentionally not used in the calculation.
    """

    del account_id, read_hostname
    hardware = hardware_inputs or collect_hardware_identity_inputs(
        goos=_default_goos() if goos is None else goos,
        read_file=_read_text_file if read_file is None else read_file,
        run_command=_run_command if run_command is None else run_command,
    )
    hashes = _component_hashes(hardware)
    root_json = _canonical_root_json(hashes)
    node_id = _sha256_hex(root_json)
    if debug:
        print_hardware_node_id_debug(
            hashes=hashes, root_json=root_json, node_id=node_id, output=output
        )
    return node_id


def collect_hardware_identity_inputs(
    *,
    goos: str,
    read_file: FileReader,
    run_command: CommandRunner,
) -> HardwareIdentityInputs:
    """Collect hardware facts without account, install, hostname, or OS IDs."""

    if goos == "darwin":
        return _darwin_hardware_inputs(run_command)
    if goos == "linux":
        return _linux_hardware_inputs(read_file, run_command)
    if goos == "windows":
        return _windows_hardware_inputs(run_command)
    return HardwareIdentityInputs(
        cpu_architecture=platform.machine(),
        cpu_vendor="",
        cpu_brand_or_chip_name=platform.processor(),
        physical_core_count=_physical_core_count_fallback(),
        logical_thread_count=os.cpu_count() or 0,
        permanent_mac_addresses=(),
        gpu_vendor="",
        gpu_model_or_chip_name="",
        gpu_device_id_if_available="",
        gpu_count=0,
        max_gpu_vram_gb="",
        total_installed_ram_gb=0,
    )


def print_hardware_node_id_debug(
    *,
    hashes: HardwareComponentHashes,
    root_json: str,
    node_id: str,
    output: TextIO | None = None,
) -> None:
    """Print the full hardware-root derivation in a readable debug format."""

    destination = sys.stdout if output is None else output
    lines = [
        f"[DEBUG] CPU_INPUT = {hashes.cpu_input}",
        f"[DEBUG] CPU_HASH = {hashes.cpu_hash}",
        f"[DEBUG] MAC_INPUT = {hashes.mac_input}",
        f"[DEBUG] MAC_HASH = {hashes.mac_hash}",
        f"[DEBUG] GPU_INPUT = {hashes.gpu_input}",
        f"[DEBUG] GPU_HASH = {hashes.gpu_hash}",
        f"[DEBUG] RAM_INPUT = {hashes.ram_input}",
        f"[DEBUG] RAM_HASH = {hashes.ram_hash}",
        f"[DEBUG] ROOT_JSON = {root_json}",
        f"[DEBUG] NODE_ID = {node_id}",
    ]
    print("\n".join(lines), file=destination)


def _component_hashes(hardware: HardwareIdentityInputs) -> HardwareComponentHashes:
    cpu_input = _join_normalized(
        (
            (hardware.cpu_architecture, UNKNOWN_CPU_ARCHITECTURE),
            (hardware.cpu_vendor, UNKNOWN_CPU_VENDOR),
            (hardware.cpu_brand_or_chip_name, UNKNOWN_CPU_BRAND),
            (hardware.physical_core_count, UNKNOWN_PHYSICAL_CORE_COUNT),
            (hardware.logical_thread_count, UNKNOWN_LOGICAL_THREAD_COUNT),
        )
    )
    mac_input = "|".join(
        sorted(
            {
                normalized
                for value in hardware.permanent_mac_addresses
                if (normalized := _normalize_mac_address(value))
            }
        )
    )
    gpu_input = _gpu_input(hardware)
    ram_input = _rounded_gb_input(hardware.total_installed_ram_gb, UNKNOWN_RAM_GB)
    return HardwareComponentHashes(
        cpu_input=cpu_input,
        cpu_hash=_sha256_hex(cpu_input),
        mac_input=mac_input,
        mac_hash=_sha256_hex(mac_input),
        gpu_input=gpu_input,
        gpu_hash=_sha256_hex(gpu_input),
        ram_input=ram_input,
        ram_hash=_sha256_hex(ram_input),
    )


def _canonical_root_json(hashes: HardwareComponentHashes) -> str:
    return json.dumps(
        {
            "cpu_hash": hashes.cpu_hash,
            "mac_hash": hashes.mac_hash,
            "gpu_hash": hashes.gpu_hash,
            "ram_hash": hashes.ram_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _gpu_input(hardware: HardwareIdentityInputs) -> str:
    gpu_count = _safe_int(hardware.gpu_count)
    gpu_detected = gpu_count > 0 or any(
        _normalize_value(value)
        for value in (
            hardware.gpu_vendor,
            hardware.gpu_model_or_chip_name,
            hardware.gpu_device_id_if_available,
            hardware.max_gpu_vram_gb,
        )
    )
    if not gpu_detected:
        return NO_GPU_DETECTED
    return _join_normalized(
        (
            (hardware.gpu_vendor, UNKNOWN_GPU_VENDOR),
            (hardware.gpu_model_or_chip_name, UNKNOWN_GPU_MODEL),
            (hardware.gpu_device_id_if_available, UNKNOWN_GPU_DEVICE_ID),
            (hardware.gpu_count, UNKNOWN_GPU_COUNT),
            (
                _rounded_gb_input(hardware.max_gpu_vram_gb, UNKNOWN_GPU_VRAM),
                UNKNOWN_GPU_VRAM,
            ),
        )
    )


def _join_normalized(values: Iterable[tuple[object, str]]) -> str:
    return "|".join(
        _normalize_value(value, placeholder) for value, placeholder in values
    )


def _normalize_value(value: object, placeholder: str = "") -> str:
    normalized = re.sub(r"\s+", " ", str(value).strip()).upper()
    return normalized or placeholder


def _rounded_gb_input(value: object, placeholder: str) -> str:
    if str(value).strip() == "":
        return placeholder
    rounded = _round_installed_ram_gb(value)
    if rounded <= 0:
        return placeholder
    return str(rounded)


def _normalize_mac_address(value: object) -> str:
    normalized = re.sub(r"[^0-9A-Fa-f]", "", str(value).strip()).upper()
    if len(normalized) != 12 or normalized == "000000000000":
        return ""
    return normalized


def _round_installed_ram_gb(value: object) -> int:
    try:
        return int(float(str(value).strip()) + 0.5)
    except (TypeError, ValueError):
        return 0


def _sha256_hex(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _darwin_hardware_inputs(run_command: CommandRunner) -> HardwareIdentityInputs:
    displays = _run_or_empty(run_command, "system_profiler", "SPDisplaysDataType")
    return HardwareIdentityInputs(
        cpu_architecture=platform.machine(),
        cpu_vendor=_run_or_empty(run_command, "sysctl", "-n", "machdep.cpu.vendor"),
        cpu_brand_or_chip_name=_run_or_empty(
            run_command, "sysctl", "-n", "machdep.cpu.brand_string"
        ),
        physical_core_count=_run_or_empty(
            run_command, "sysctl", "-n", "hw.physicalcpu"
        ),
        logical_thread_count=_run_or_empty(
            run_command, "sysctl", "-n", "hw.logicalcpu"
        ),
        permanent_mac_addresses=tuple(
            _physical_mac_addresses(
                _run_or_empty(run_command, "networksetup", "-listallhardwareports"),
                source="darwin-networksetup",
            )
        ),
        gpu_vendor=_extract_labeled_value(displays, "Vendor"),
        gpu_model_or_chip_name=_extract_labeled_value(displays, "Chipset Model"),
        gpu_device_id_if_available=_extract_labeled_value(displays, "Device ID"),
        gpu_count=_count_display_chips(displays),
        max_gpu_vram_gb=_max_gpu_vram_gb(displays),
        total_installed_ram_gb=_bytes_to_gb(
            _safe_int(_run_or_empty(run_command, "sysctl", "-n", "hw.memsize"))
        ),
    )


def _linux_hardware_inputs(
    read_file: FileReader, run_command: CommandRunner
) -> HardwareIdentityInputs:
    cpuinfo = _read_or_empty(read_file, "/proc/cpuinfo")
    meminfo = _read_or_empty(read_file, "/proc/meminfo")
    lscpu = _run_or_empty(run_command, "lscpu")
    lspci = _run_or_empty(run_command, "lspci", "-nn")
    return HardwareIdentityInputs(
        cpu_architecture=platform.machine(),
        cpu_vendor=_linux_cpu_value(cpuinfo, lscpu, "vendor_id", "Vendor ID"),
        cpu_brand_or_chip_name=_linux_cpu_value(
            cpuinfo, lscpu, "model name", "Model name"
        ),
        physical_core_count=_linux_physical_core_count(cpuinfo, lscpu),
        logical_thread_count=os.cpu_count() or _linux_lscpu_int(lscpu, "CPU(s)") or 0,
        permanent_mac_addresses=tuple(
            _physical_mac_addresses(
                _run_or_empty(run_command, "ip", "-o", "link"),
                source="linux-ip-link",
            )
        ),
        gpu_vendor=_linux_gpu_vendor(lspci),
        gpu_model_or_chip_name=_linux_gpu_model(lspci),
        gpu_device_id_if_available=_linux_gpu_device_id(lspci),
        gpu_count=_linux_gpu_count(lspci),
        max_gpu_vram_gb=_max_gpu_vram_gb(lspci),
        total_installed_ram_gb=_linux_memtotal_gb(meminfo),
    )


def _windows_hardware_inputs(run_command: CommandRunner) -> HardwareIdentityInputs:
    cpu = _run_or_empty(
        run_command,
        "wmic",
        "cpu",
        "get",
        "Manufacturer,Name,NumberOfCores,NumberOfLogicalProcessors",
        "/format:csv",
    )
    gpu = _run_or_empty(
        run_command,
        "wmic",
        "path",
        "win32_VideoController",
        "get",
        "AdapterCompatibility,Name,PNPDeviceID,AdapterRAM",
        "/format:csv",
    )
    ram = _run_or_empty(run_command, "wmic", "memorychip", "get", "capacity")
    macs = _run_or_empty(run_command, "getmac", "/fo", "csv", "/v")
    return HardwareIdentityInputs(
        cpu_architecture=platform.machine(),
        cpu_vendor=_csv_first_value(cpu, "Manufacturer"),
        cpu_brand_or_chip_name=_csv_first_value(cpu, "Name"),
        physical_core_count=_csv_first_value(cpu, "NumberOfCores"),
        logical_thread_count=_csv_first_value(cpu, "NumberOfLogicalProcessors"),
        permanent_mac_addresses=tuple(
            _physical_mac_addresses(macs, source="windows-getmac")
        ),
        gpu_vendor=_csv_first_value(gpu, "AdapterCompatibility"),
        gpu_model_or_chip_name=_csv_first_value(gpu, "Name"),
        gpu_device_id_if_available=_csv_first_value(gpu, "PNPDeviceID"),
        gpu_count=max(1, len([line for line in gpu.splitlines() if line.strip()][1:])),
        max_gpu_vram_gb=_bytes_to_gb(_max_csv_int(gpu, "AdapterRAM")),
        total_installed_ram_gb=_bytes_to_gb(
            sum(_safe_int(value) for value in re.findall(r"\b\d{8,}\b", ram))
        ),
    )


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
    return subprocess.check_output(  # nosec B603 - fixed hardware probes, shell disabled.
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


def _physical_core_count_fallback() -> int:
    count = os.cpu_count()
    if count is None:
        return 0
    return max(1, count // 2)


def _physical_mac_addresses(text: str, *, source: str) -> list[str]:
    if source == "darwin-networksetup":
        return _darwin_physical_mac_addresses(text)
    if source == "linux-ip-link":
        return _linux_physical_mac_addresses(text)
    if source == "windows-getmac":
        return _windows_physical_mac_addresses(text)
    return []


def _darwin_physical_mac_addresses(text: str) -> list[str]:
    addresses: list[str] = []
    for block in re.split(r"\n\s*\n", text.strip()):
        port = _extract_labeled_value(block, "Hardware Port")
        if not _is_darwin_physical_ethernet_or_wifi_port(port):
            continue
        address = _extract_labeled_value(block, "Ethernet Address")
        if _is_usable_mac_address(address):
            addresses.append(address)
    return addresses


def _linux_physical_mac_addresses(text: str) -> list[str]:
    addresses: list[str] = []
    for line in text.splitlines():
        match = re.match(r"\s*\d+:\s*([^:@]+)(?:@[^:]+)?:.*?link/ether\s+(\S+)", line)
        if not match:
            continue
        interface_name, address = match.groups()
        if _is_physical_linux_network_interface(
            interface_name
        ) and _is_usable_mac_address(address):
            addresses.append(address)
    return addresses


def _windows_physical_mac_addresses(text: str) -> list[str]:
    addresses: list[str] = []
    for row in csv.DictReader(StringIO(text)):
        description = " ".join(
            str(row.get(field, ""))
            for field in ("Connection Name", "Network Adapter", "Description")
        )
        address = str(
            row.get("Physical Address") or row.get("PhysicalAddress") or ""
        ).strip()
        if _is_physical_ethernet_or_wifi_name(description) and _is_usable_mac_address(
            address
        ):
            addresses.append(address)
    return addresses


def _is_physical_linux_network_interface(name: str) -> bool:
    lowered = name.lower()
    if _is_virtual_or_non_hardware_network_name(lowered):
        return False
    return lowered.startswith(("eth", "en", "wlan", "wl"))


def _is_darwin_physical_ethernet_or_wifi_port(name: str) -> bool:
    lowered = _normalize_network_name(name)
    if lowered in {"ethernet", "wi-fi", "wifi"}:
        return True
    if _is_virtual_or_non_hardware_network_name(lowered):
        return False
    if "adapter" in lowered or "iphone" in lowered:
        return False
    return "usb" in lowered and bool(
        re.search(r"\b(ethernet|lan|wi-?fi|wireless)\b", lowered)
    )


def _is_physical_ethernet_or_wifi_name(name: str) -> bool:
    lowered = _normalize_network_name(name)
    if _is_virtual_or_non_hardware_network_name(lowered):
        return False
    return bool(re.search(r"\b(ethernet|wi-?fi|wireless|802\.11)\b", lowered))


def _normalize_network_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).lower()


def _is_virtual_or_non_hardware_network_name(name: str) -> bool:
    if name.startswith(
        (
            "bridge",
            "docker",
            "veth",
            "vmnet",
            "awdl",
            "llw",
            "p2p",
            "utun",
            "tun",
            "tap",
        )
    ):
        return True
    return bool(
        re.search(
            r"\b(virtual|bridge|bluetooth|thunderbolt|tunnel|tap|tun|docker|veth|vmnet|hyper-v|loopback|awdl|llw|p2p|utun|vpn)\b",
            name,
        )
    )


def _is_usable_mac_address(value: str) -> bool:
    normalized = _normalize_mac_address(value)
    return bool(normalized and normalized != "FFFFFFFFFFFF")


def _extract_mac_addresses(text: str) -> list[str]:
    return [
        value
        for value in re.findall(r"(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}", text)
        if _normalize_mac_address(value) != "FFFFFFFFFFFF"
    ]


def _extract_labeled_value(text: str, label: str) -> str:
    pattern = re.compile(rf"^\s*{re.escape(label)}\s*:\s*(.+?)\s*$", re.MULTILINE)
    match = pattern.search(text)
    return match.group(1) if match else ""


def _count_display_chips(text: str) -> int:
    models = re.findall(r"^\s*Chipset Model\s*:", text, flags=re.MULTILINE)
    return len(models)


def _max_gpu_vram_gb(text: str) -> float:
    values = [
        _vram_value_to_gb(amount, unit)
        for amount, unit in re.findall(
            r"(?:VRAM|AdapterRAM|Video Memory|Dedicated Memory|size)\s*(?:\([^)]*\))?\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)\s*([KMGT]?B?|[KMGT])?",
            text,
            flags=re.IGNORECASE,
        )
    ]
    return max(values, default=0)


def _vram_value_to_gb(amount: str, unit: str | None) -> float:
    try:
        value = float(amount)
    except ValueError:
        return 0
    normalized_unit = (unit or "GB").strip().upper()
    if normalized_unit in {"", "G", "GB"}:
        return value
    if normalized_unit in {"M", "MB"}:
        return value / 1024
    if normalized_unit in {"K", "KB"}:
        return value / float(1024**2)
    if normalized_unit in {"T", "TB"}:
        return value * 1024
    return value


def _bytes_to_gb(value: int) -> float:
    if value <= 0:
        return 0
    return value / float(1024**3)


def _linux_memtotal_gb(meminfo: str) -> float:
    match = re.search(r"^\s*MemTotal\s*:\s*(\d+)\s+kB", meminfo, flags=re.MULTILINE)
    if not match:
        return 0
    kib = _safe_int(match.group(1))
    return kib / float(1024**2)


def _linux_cpu_value(cpuinfo: str, lscpu: str, cpuinfo_key: str, lscpu_key: str) -> str:
    value = _colon_value(cpuinfo, cpuinfo_key)
    return value or _colon_value(lscpu, lscpu_key)


def _colon_value(text: str, key: str) -> str:
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*:\s*(.+?)\s*$", re.MULTILINE)
    match = pattern.search(text)
    return match.group(1) if match else ""


def _linux_physical_core_count(cpuinfo: str, lscpu: str) -> int | str:
    pairs = set(
        re.findall(r"physical id\s*:\s*(\S+).*?core id\s*:\s*(\S+)", cpuinfo, re.S)
    )
    if pairs:
        return len(pairs)
    cores_per_socket = _linux_lscpu_int(lscpu, "Core(s) per socket")
    sockets = _linux_lscpu_int(lscpu, "Socket(s)")
    if cores_per_socket and sockets:
        return cores_per_socket * sockets
    return _physical_core_count_fallback()


def _linux_lscpu_int(lscpu: str, key: str) -> int:
    return _safe_int(_colon_value(lscpu, key))


def _linux_gpu_lines(lspci: str) -> list[str]:
    return [
        line
        for line in lspci.splitlines()
        if re.search(r"\b(VGA|3D|Display)\b", line, flags=re.IGNORECASE)
    ]


def _linux_gpu_count(lspci: str) -> int:
    return len(_linux_gpu_lines(lspci))


def _linux_gpu_model(lspci: str) -> str:
    lines = _linux_gpu_lines(lspci)
    if not lines:
        return ""
    match = re.search(r"\]:\s*(.+)$", lines[0])
    if match:
        return match.group(1)
    return re.sub(r"^[0-9A-Fa-f:.]+\s+[^:]+:\s*", "", lines[0])


def _linux_gpu_vendor(lspci: str) -> str:
    model = _linux_gpu_model(lspci)
    return model.split(" ", 1)[0] if model else ""


def _linux_gpu_device_id(lspci: str) -> str:
    lines = _linux_gpu_lines(lspci)
    if not lines:
        return ""
    match = re.search(r"\[([0-9A-Fa-f]{4}:[0-9A-Fa-f]{4})\]", lines[0])
    return match.group(1) if match else ""


def _csv_first_value(text: str, key: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return ""
    headers = [part.strip() for part in lines[0].split(",")]
    try:
        index = headers.index(key)
    except ValueError:
        return ""
    values = [part.strip() for part in lines[1].split(",")]
    return values[index] if index < len(values) else ""


def _max_csv_int(text: str, key: str) -> int:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return 0
    headers = [part.strip() for part in lines[0].split(",")]
    try:
        index = headers.index(key)
    except ValueError:
        return 0
    return max(
        (
            _safe_int(values[index])
            for values in (
                [part.strip() for part in line.split(",")] for line in lines[1:]
            )
            if index < len(values)
        ),
        default=0,
    )


def _safe_int(value: object) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


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
