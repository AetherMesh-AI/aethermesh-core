"""First-class AetherMesh CLI for local node, API, and UI workflows."""

from __future__ import annotations

import threading
import webbrowser
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from aethermesh_core.release_update import (
    ReleaseUpdateError,
    update_from_latest_release,
)
from aethermesh_core.runtime_service import (
    DEFAULT_API_HOST,
    DEFAULT_API_PORT,
    NodeRuntimeService,
    RuntimeServiceError,
)

app = typer.Typer(help="AetherMesh local node CLI.", no_args_is_help=True)
node_app = typer.Typer(help="Local node runtime commands.")
app.add_typer(node_app, name="node")
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        service = NodeRuntimeService.default()
        console.print(service.get_node_status()["version"])
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = False,
) -> None:
    """AetherMesh local node CLI."""


@app.command()
def init() -> None:
    """Initialize local AetherMesh node config and data directories."""

    service = NodeRuntimeService.default()
    try:
        result = service.initialize_local_node_data()
    except RuntimeServiceError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(f"Initialized AetherMesh node [bold]{result['node_id']}[/bold]")
    console.print(f"Config: {result['config_path']}")
    console.print(f"Data:   {result['data_dir']}")


@app.command()
def status() -> None:
    """Show local node status."""

    _print_status(NodeRuntimeService.default().get_node_status())


@node_app.command("status")
def node_status() -> None:
    """Show local node runtime status."""

    _print_status(NodeRuntimeService.default().get_node_status())


@node_app.command("start")
def node_start(
    host: Annotated[
        str, typer.Option(help="API bind host. Keep 127.0.0.1 unless you know why.")
    ] = DEFAULT_API_HOST,
    port: Annotated[int, typer.Option(help="API bind port.")] = DEFAULT_API_PORT,
    dry_run: Annotated[
        bool, typer.Option(help="Show what would start without running the server.")
    ] = False,
) -> None:
    """Start the foreground local API/node runtime."""

    if host not in {"127.0.0.1", "localhost"}:
        console.print(
            "[yellow]Warning:[/yellow] non-localhost API binding is not recommended yet."
        )
    if dry_run:
        console.print(f"Would start AetherMesh local API on http://{host}:{port}")
        return
    _serve(host=host, port=port, open_browser=False)


@app.command()
def peers() -> None:
    """List known local peers."""

    payload = NodeRuntimeService.default().list_peers()
    if not payload["peers"]:
        console.print("No peers discovered yet.")
        console.print(payload["note"])
        return
    table = Table(title="Peers")
    table.add_column("Node ID")
    table.add_column("Status")
    table.add_column("Capabilities")
    for peer in payload["peers"]:
        table.add_row(
            peer.get("node_id", "unknown"),
            peer.get("status", "unknown"),
            ", ".join(peer.get("capabilities", [])),
        )
    console.print(table)


@app.command()
def jobs() -> None:
    """List current and recent local jobs."""

    payload = NodeRuntimeService.default().list_jobs()
    if not payload["current"]:
        console.print("No current jobs.")
    if not payload["completed"]:
        console.print("No completed jobs.")
    if not payload["failed"]:
        console.print("No failed jobs.")
    console.print(payload["note"])


@app.command()
def update(
    dry_run: Annotated[
        bool,
        typer.Option(help="Download and verify the latest release without installing."),
    ] = False,
    release_url: Annotated[
        str | None,
        typer.Option(help="Override the GitHub latest-release API URL."),
    ] = None,
) -> None:
    """Install the latest AetherMesh wheel from the newest GitHub release."""

    try:
        result = update_from_latest_release(dry_run=dry_run, release_url=release_url)
    except ReleaseUpdateError as exc:
        raise typer.BadParameter(str(exc)) from exc
    payload = result.to_dict()
    console.print(f"Release: {payload['release_tag']}")
    console.print(f"Wheel:   {payload['wheel_name']}")
    console.print(f"SHA256:  {payload['sha256']} verified")
    if payload["installed"]:
        console.print("Installed latest AetherMesh release.")
    else:
        console.print("Dry run complete; wheel verified but not installed.")


@app.command()
def ui(
    host: Annotated[str, typer.Option(help="API/UI bind host.")] = DEFAULT_API_HOST,
    port: Annotated[int, typer.Option(help="API/UI bind port.")] = DEFAULT_API_PORT,
    no_open: Annotated[
        bool, typer.Option(help="Do not open a browser automatically.")
    ] = False,
    dry_run: Annotated[
        bool, typer.Option(help="Print the dashboard URL without starting the server.")
    ] = False,
) -> None:
    """Open the local dashboard UI backed by the local API."""

    url = f"http://{host}:{port}"
    if dry_run:
        console.print(url)
        return
    _serve(host=host, port=port, open_browser=not no_open)


def _serve(*, host: str, port: int, open_browser: bool) -> None:
    if host not in {"127.0.0.1", "localhost"}:
        console.print(
            "[yellow]Warning:[/yellow] non-localhost API binding is not the safe default."
        )
    try:
        import uvicorn

        from aethermesh_core.api import create_app
    except ImportError as exc:
        raise typer.BadParameter(
            "API/UI dependencies are missing. Install with: python -m pip install -e '.[ui]'"
        ) from exc

    service = NodeRuntimeService.default()
    service.initialize_local_node_data()
    url = f"http://{host}:{port}"
    console.print(f"Starting AetherMesh local API/UI on {url}")
    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    uvicorn.run(create_app(service), host=host, port=port, log_level="info")


def _print_status(status: dict[str, object]) -> None:
    table = Table(title="AetherMesh Node Status")
    table.add_column("Field")
    table.add_column("Value")
    for key in [
        "node_id",
        "status",
        "version",
        "uptime_seconds",
        "config_path",
        "data_dir",
        "peer_count",
    ]:
        table.add_row(key, str(status.get(key)))
    api = status.get("api")
    if isinstance(api, dict):
        table.add_row("api", f"http://{api.get('host')}:{api.get('port')}")
    console.print(table)


if __name__ == "__main__":
    app()
