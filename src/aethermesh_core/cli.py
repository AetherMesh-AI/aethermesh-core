"""Command-line interface for the local AetherMesh prototype."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import replace

from aethermesh_core.identity import IdentityPersistenceError, load_or_create_identity
from aethermesh_core.job_manifest import ManifestError, load_job_manifest
from aethermesh_core.ledger import (
    ContributionLedger,
    LedgerPersistenceError,
    load_existing_ledger_document,
    load_ledger_document,
    save_ledger_document,
)
from aethermesh_core.message_log import (
    MessageLogPersistenceError,
    build_message_log_document,
    write_message_log,
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
        "--identity-path",
        default=None,
        help="Opt in to JSON-file-backed local node identity persistence.",
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

    batch = subcommands.add_parser(
        "run-local-batch",
        help="Run a manifest-backed local multi-node job batch and print JSON.",
    )
    batch.add_argument(
        "--manifest",
        required=True,
        help="Path to a version 1 local job-batch JSON manifest.",
    )
    batch.add_argument(
        "--ledger-path",
        default=None,
        help="Opt in to JSON-file-backed local contribution ledger persistence.",
    )
    batch.add_argument(
        "--message-log-path",
        default=None,
        help="Opt in to overwriting a local JSON audit log of deterministic mesh messages.",
    )

    ledger_summary = subcommands.add_parser(
        "ledger-summary",
        help="Inspect an existing local contribution ledger and print JSON totals.",
    )
    ledger_summary.add_argument(
        "--ledger-path",
        required=True,
        help="Path to an existing version 1 local contribution ledger JSON file.",
    )

    return parser


def run_demo(
    node_id: str | None,
    message: str,
    include_ledger: bool = False,
    ledger_path: str | None = None,
    identity_path: str | None = None,
) -> dict[str, object]:
    if node_id and identity_path:
        raise IdentityPersistenceError("--node-id and --identity-path are mutually exclusive")
    if identity_path is not None:
        identity = load_or_create_identity(identity_path)
    else:
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
        ledger.record(
            record_result,
            validation_valid=validation.valid,
            validation_reason=validation.reason,
            job_type=job.job_type,
        )
        return {
            "result": result_dict,
            "validation": validation.to_dict(),
            "ledger_summary": ledger.summary_for_node(identity.node_id).to_dict(),
        }

    ledger, extra_fields = load_ledger_document(ledger_path)
    ledger.record(
        record_result,
        validation_valid=validation.valid,
        validation_reason=validation.reason,
        job_type=job.job_type,
    )
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


def run_local_batch(
    manifest_path: str,
    ledger_path: str | None = None,
    message_log_path: str | None = None,
) -> dict[str, object]:
    """Run a local simulation from a validated JSON manifest."""

    batch = load_job_manifest(manifest_path)
    simulation = run_local_simulation(node_ids=batch.nodes, jobs=batch.jobs)
    result = simulation.to_dict()
    unsupported_count = int(result["validation_summary"]["unsupported"])
    if ledger_path is not None:
        ledger, extra_fields = load_ledger_document(ledger_path)
        for job, accounted_result, validation in zip(
            batch.jobs, simulation.accounted_results, simulation.validations
        ):
            ledger.record(
                accounted_result,
                validation_valid=validation.valid,
                validation_reason=validation.reason,
                job_type=job.job_type,
            )
        save_ledger_document(ledger_path, ledger, extra_fields)
        result["ledger_path"] = ledger_path
        result["persisted_ledger_summaries"] = [
            ledger.summary_for_node(node_id).to_dict() for node_id in batch.node_ids
        ]

    if message_log_path is not None:
        message_log_document = build_message_log_document(
            simulation=simulation,
            jobs=batch.jobs,
            manifest_path=manifest_path,
        )
        write_message_log(message_log_path, message_log_document)
        result["message_log_path"] = message_log_path

    if unsupported_count:
        unsupported_errors = sorted(
            {
                str(item["error"])
                for item in result["results"]
                if item.get("status") == "failed"
                and isinstance(item.get("error"), str)
                and item["error"].startswith("Unsupported job type:")
            }
        )
        details = "; ".join(unsupported_errors) or "unsupported job type"
        raise ManifestError(f"local batch execution failed: {details}")

    return result


def summarize_ledger(ledger_path: str) -> dict[str, object]:
    """Load an existing ledger and return read-only aggregate totals."""

    ledger, _extra_fields = load_existing_ledger_document(ledger_path)
    return ledger.summary_document(ledger_path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run-demo":
        try:
            payload = run_demo(
                args.node_id,
                args.message,
                args.include_ledger,
                args.ledger_path,
                args.identity_path,
            )
        except (IdentityPersistenceError, LedgerPersistenceError) as exc:
            parser.error(str(exc))
        print(json.dumps(payload, sort_keys=True))
        return 0

    if args.command == "simulate-local":
        print(json.dumps(run_default_local_simulation(), sort_keys=True))
        return 0

    if args.command == "run-local-batch":
        try:
            payload = run_local_batch(
                args.manifest, args.ledger_path, args.message_log_path
            )
        except ManifestError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except (LedgerPersistenceError, MessageLogPersistenceError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except ValueError as exc:
            print(f"error: local batch execution failed: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(payload, sort_keys=True))
        return 0

    if args.command == "ledger-summary":
        try:
            payload = summarize_ledger(args.ledger_path)
        except LedgerPersistenceError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(payload, sort_keys=True))
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
