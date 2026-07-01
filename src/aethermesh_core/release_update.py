"""Install the newest AetherMesh package from the latest GitHub release."""

from __future__ import annotations

import hashlib
import json
import subprocess  # nosec B404 - fixed pip invocation with shell disabled.
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_LATEST_RELEASE_URL = (
    "https://api.github.com/repos/AetherMesh-AI/aethermesh-core/releases/latest"
)


class ReleaseUpdateError(RuntimeError):
    """Raised when the latest release cannot be downloaded or installed."""


@dataclass(frozen=True)
class ReleaseUpdatePlan:
    release_tag: str
    release_name: str
    release_url: str | None
    wheel_name: str
    wheel_url: str
    checksum_url: str | None
    expected_sha256: str | None


@dataclass(frozen=True)
class ReleaseUpdateResult:
    release_tag: str
    release_name: str
    release_url: str | None
    wheel_name: str
    wheel_url: str
    sha256: str
    expected_sha256: str | None
    installed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "release_tag": self.release_tag,
            "release_name": self.release_name,
            "release_url": self.release_url,
            "wheel_name": self.wheel_name,
            "wheel_url": self.wheel_url,
            "sha256": self.sha256,
            "expected_sha256": self.expected_sha256,
            "installed": self.installed,
        }


def build_update_plan(
    release: dict[str, object], checksum_text: str = ""
) -> ReleaseUpdatePlan:
    assets = _release_assets(release)
    wheel = _find_asset(assets, lambda asset: asset["name"].endswith(".whl"))
    if wheel is None:
        raise ReleaseUpdateError("latest GitHub release does not include a wheel asset")

    checksum_asset = _find_asset(
        assets, lambda asset: asset["name"] == "SHA256SUMS.txt"
    )
    checksum_url = checksum_asset["url"] if checksum_asset is not None else None
    expected_sha256 = _checksum_for_asset(checksum_text, wheel["name"])
    return ReleaseUpdatePlan(
        release_tag=_string_field(release, "tag_name", default="unknown-release"),
        release_name=_string_field(release, "name", default="unknown release"),
        release_url=_optional_string_field(release, "html_url"),
        wheel_name=wheel["name"],
        wheel_url=wheel["url"],
        checksum_url=checksum_url,
        expected_sha256=expected_sha256,
    )


def update_from_latest_release(
    *,
    dry_run: bool = False,
    release_url: str | None = None,
    fetch_json: Callable[[str], dict[str, object]] | None = None,
    fetch_bytes: Callable[[str], bytes] | None = None,
    install_wheel: Callable[[Path], None] | None = None,
) -> ReleaseUpdateResult:
    json_fetcher = fetch_json if fetch_json is not None else _fetch_json
    bytes_fetcher = fetch_bytes if fetch_bytes is not None else _fetch_bytes
    installer = install_wheel if install_wheel is not None else _install_wheel
    release = json_fetcher(release_url or DEFAULT_LATEST_RELEASE_URL)
    checksum_text = _release_checksum_text(release, bytes_fetcher)
    plan = build_update_plan(release, checksum_text)
    wheel_bytes = bytes_fetcher(plan.wheel_url)
    actual_sha256 = hashlib.sha256(wheel_bytes).hexdigest()
    if plan.expected_sha256 is not None and actual_sha256 != plan.expected_sha256:
        raise ReleaseUpdateError(
            "downloaded wheel checksum mismatch: "
            f"expected {plan.expected_sha256}, got {actual_sha256}"
        )

    if not dry_run:
        with tempfile.TemporaryDirectory(prefix="aethermesh-update-") as temp_dir:
            wheel_path = Path(temp_dir) / plan.wheel_name
            wheel_path.write_bytes(wheel_bytes)
            installer(wheel_path)

    return ReleaseUpdateResult(
        release_tag=plan.release_tag,
        release_name=plan.release_name,
        release_url=plan.release_url,
        wheel_name=plan.wheel_name,
        wheel_url=plan.wheel_url,
        sha256=actual_sha256,
        expected_sha256=plan.expected_sha256,
        installed=not dry_run,
    )


def _release_checksum_text(
    release: dict[str, object], fetch_bytes: Callable[[str], bytes]
) -> str:
    checksum_asset = _find_asset(
        _release_assets(release), lambda asset: asset["name"] == "SHA256SUMS.txt"
    )
    if checksum_asset is None:
        return ""
    return fetch_bytes(checksum_asset["url"]).decode("utf-8")


def _release_assets(release: dict[str, object]) -> list[dict[str, str]]:
    raw_assets = release.get("assets")
    if not isinstance(raw_assets, list):
        raise ReleaseUpdateError("latest GitHub release response has no assets list")
    assets: list[dict[str, str]] = []
    for raw_asset in raw_assets:
        if not isinstance(raw_asset, dict):
            continue
        name = raw_asset.get("name")
        url = raw_asset.get("browser_download_url")
        if isinstance(name, str) and isinstance(url, str):
            assets.append({"name": name, "url": url})
    return assets


def _find_asset(
    assets: list[dict[str, str]], predicate: Callable[[dict[str, str]], bool]
) -> dict[str, str] | None:
    for asset in assets:
        if predicate(asset):
            return asset
    return None


def _checksum_for_asset(checksum_text: str, asset_name: str) -> str | None:
    for line in checksum_text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[-1].lstrip("*") == asset_name:
            return parts[0]
    return None


def _string_field(release: dict[str, object], field: str, *, default: str) -> str:
    value = release.get(field)
    return value if isinstance(value, str) and value else default


def _optional_string_field(release: dict[str, object], field: str) -> str | None:
    value = release.get(field)
    return value if isinstance(value, str) and value else None


def _fetch_json(url: str) -> dict[str, object]:
    try:
        payload = _fetch_bytes(url)
        value = json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ReleaseUpdateError(
            f"GitHub release response was not valid JSON: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise ReleaseUpdateError("GitHub release response was not a JSON object")
    return dict(value)


def _fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"Accept": "application/vnd.github+json"})
    try:
        with urlopen(request, timeout=30) as response:  # nosec B310 - fixed GitHub/download URLs.
            return bytes(response.read())
    except (HTTPError, URLError, OSError) as exc:
        raise ReleaseUpdateError(f"failed to download {url}: {exc}") from exc


def _install_wheel(path: Path) -> None:
    try:
        subprocess.check_call(  # nosec B603 - fixed interpreter pip invocation, shell disabled.
            [sys.executable, "-m", "pip", "install", "--upgrade", str(path)]
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseUpdateError(f"failed to install {path.name}: {exc}") from exc
