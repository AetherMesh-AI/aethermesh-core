"""Command-line interface for the local AetherMesh prototype."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from aethermesh_core.models import Job, NodeIdentity
from aethermesh_core.runner import LocalRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aethermesh-core")
    subcommands = parser.add_subparsers(dest="command", required=True)

    demo = subcommands.add_parser(
        "run-demo", help="Run one local echo job and print its JSON result."
    )
    demo.add_argument(
        "--node-id",
        default=None,
        help="Node id to use for the demo. Defaults to an ephemeral id.",
    )
    demo.add_argument(
        "--message",
        default="hello mesh",
        help="Message payload for the local echo job.",
    )

    return parser


def run_demo(node_id: str | None, message: str) -> dict[str, object]:
    identity = NodeIdentity(node_id=node_id) if node_id else NodeIdentity.ephemeral()
    job = Job(job_id="demo-echo", job_type="echo", payload={"message": message})
    result = LocalRunner(identity).run(job)
    return result.to_dict()


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run-demo":
        print(json.dumps(run_demo(args.node_id, args.message), sort_keys=True))
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
