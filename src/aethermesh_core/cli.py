"""Command-line interface for the local AetherMesh prototype."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import replace

from aethermesh_core.ledger import (
    ContributionLedger,
    LedgerPersistenceError,
    load_ledger_document,
    save_ledger_document,
)
from aethermesh_core.models import Job, NodeIdentity
from aethermesh_core.runner import LocalRunner
from aethermesh_core.simulation import run_local_simulation
from aethermesh_core.validation import validate_job_result


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
    demo.add_argument(
        "--ledger-path",
        default=None,
        help="Opt in to JSON-file-backed local contribution ledger persistence.",
    )

    subcommands.add_parser(
        "simulate-local",
        help="Run a deterministic local multi-node simulation and print JSON.",
    )

    return parser


def run_demo(
    node_id: str | None,
    message: str,
    include_ledger: bool = False,
    ledger_path: str | None = None,
) -> dict[str, object]:
    identity = NodeIdentity(node_id=node_id) if node_id else NodeIdentity.ephemeral()
    job = Job(job_id="demo-echo", job_type="echo", payload={"message": message})
    result = LocalRunner(identity).run(job)
    result_dict = result.to_dict()
    if not include_ledger and ledger_path is None:
        return result_dict

    validation = validate_job_result(job, result)
    record_result = result if validation.valid else replace(result, contribution_units=0)
    if ledger_path is None:
        ledger = ContributionLedger()
        ledger.record(record_result)
        return {
            "result": result_dict,
            "validation": validation.to_dict(),
            "ledger_summary": ledger.summary_for_node(identity.node_id).to_dict(),
        }

    ledger, extra_fields = load_ledger_document(ledger_path)
    ledger.record(record_result)
    save_ledger_document(ledger_path, ledger, extra_fields)
    return {
        "result": result_dict,
        "validation": validation.to_dict(),
        "ledger_path": ledger_path,
        "persisted_ledger_summary": ledger.summary_for_node(identity.node_id).to_dict(),
    }


def run_default_local_simulation() -> dict[str, object]:
    """Run the fixed local simulation demo used by the CLI command."""

    jobs = [
        Job(job_id="echo-1", job_type="echo", payload={"message": "hello mesh one"}),
        Job(
            job_id="text-stats-1",
            job_type="text_stats",
            payload={"text": "hello mesh\nhello node"},
        ),
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
        try:
            payload = run_demo(
                args.node_id, args.message, args.include_ledger, args.ledger_path
            )
        except LedgerPersistenceError as exc:
            parser.error(str(exc))
        print(json.dumps(payload, sort_keys=True))
        return 0

    if args.command == "simulate-local":
        print(json.dumps(run_default_local_simulation(), sort_keys=True))
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
