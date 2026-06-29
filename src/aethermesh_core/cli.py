"""Command-line interface for the local AetherMesh prototype."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from aethermesh_core.ledger import ContributionLedger
from aethermesh_core.models import Job, NodeIdentity
from aethermesh_core.runner import LocalRunner
from aethermesh_core.simulation import run_local_simulation


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
    demo.add_argument(
        "--include-ledger",
        action="store_true",
        help="Include an in-memory contribution summary for the demo result.",
    )

    subcommands.add_parser(
        "simulate-local",
        help="Run a deterministic local multi-node simulation and print JSON.",
    )

    return parser


def run_demo(
    node_id: str | None, message: str, include_ledger: bool = False
) -> dict[str, object]:
    identity = NodeIdentity(node_id=node_id) if node_id else NodeIdentity.ephemeral()
    job = Job(job_id="demo-echo", job_type="echo", payload={"message": message})
    result = LocalRunner(identity).run(job)
    result_dict = result.to_dict()
    if not include_ledger:
        return result_dict

    ledger = ContributionLedger()
    ledger.record(result)
    return {
        "result": result_dict,
        "ledger_summary": ledger.summary_for_node(identity.node_id).to_dict(),
    }


def run_default_local_simulation() -> dict[str, object]:
    """Run the fixed local simulation demo used by the CLI command."""

    jobs = [
        Job(job_id="echo-1", job_type="echo", payload={"message": "hello mesh one"}),
        Job(job_id="echo-2", job_type="echo", payload={"message": "hello mesh two"}),
        Job(job_id="echo-3", job_type="echo", payload={"message": "hello mesh three"}),
    ]
    return run_local_simulation(
        node_ids=["local-node-a", "local-node-b"], jobs=jobs
    ).to_dict()


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run-demo":
        print(
            json.dumps(
                run_demo(args.node_id, args.message, args.include_ledger), sort_keys=True
            )
        )
        return 0

    if args.command == "simulate-local":
        print(json.dumps(run_default_local_simulation(), sort_keys=True))
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
