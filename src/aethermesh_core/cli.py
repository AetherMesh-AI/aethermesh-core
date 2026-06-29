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
from aethermesh_core.message_bus import LocalMessageBus
from aethermesh_core.message_log import (
    MessageLogPersistenceError,
    build_message_log_document,
    build_replayed_message_log_document,
    load_message_log_messages,
    write_message_log,
)
from aethermesh_core.messages import MeshMessage
from aethermesh_core.models import Job, NodeIdentity
from aethermesh_core.node_service import InboxProcessResult, LocalNodeService
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

    inbox = subcommands.add_parser(
        "process-local-inbox",
        help="Replay a local message log and process one node's assigned inbox work.",
    )
    inbox.add_argument(
        "--node-id",
        required=True,
        help="Local node id whose replayed inbox should be processed.",
    )
    inbox.add_argument(
        "--message-log-path",
        required=True,
        help="Path to a version 1 local message log produced by run-local-batch.",
    )
    inbox.add_argument(
        "--ledger-path",
        default=None,
        help="Opt in to persisting validation-gated contribution records.",
    )
    inbox.add_argument(
        "--output-message-log-path",
        default=None,
        help="Opt in to writing replayed plus emitted worker messages as a local message log.",
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


def process_local_inbox(
    *,
    node_id: str,
    message_log_path: str,
    ledger_path: str | None = None,
    output_message_log_path: str | None = None,
) -> dict[str, object]:
    """Replay a saved local message log and process one node inbox."""

    messages = load_message_log_messages(message_log_path)
    ledger, extra_fields = (
        load_ledger_document(ledger_path)
        if ledger_path is not None
        else (ContributionLedger(), {})
    )
    message_bus = LocalMessageBus()
    for registered_node_id in _node_ids_from_replayed_messages(messages, node_id):
        message_bus.register_node(registered_node_id)
    for message in messages:
        message_bus.send(message)

    service = LocalNodeService(
        identity=NodeIdentity(node_id=node_id),
        message_bus=message_bus,
        runner=LocalRunner(NodeIdentity(node_id=node_id)),
        ledger=ledger,
    )
    inbox_result = service.process_inbox()
    if ledger_path is not None:
        save_ledger_document(ledger_path, ledger, extra_fields)
    payload = _inbox_process_result_to_dict(inbox_result, ledger, ledger_path)
    if output_message_log_path is not None:
        emitted_messages = _emitted_messages_from_inbox_result(inbox_result)
        output_document = build_replayed_message_log_document(
            replayed_messages=messages,
            emitted_messages=emitted_messages,
            node_id=node_id,
            source_message_log_path=message_log_path,
            ledger_path=ledger_path,
            processed_assignment_count=len(inbox_result.processed),
            ignored_message_ids=list(inbox_result.ignored_message_ids),
        )
        write_message_log(output_message_log_path, output_document)
        payload["output_message_log_path"] = output_message_log_path
        payload["final_message_count"] = len(messages) + len(emitted_messages)
    return payload


def _emitted_messages_from_inbox_result(
    inbox_result: InboxProcessResult,
) -> list[MeshMessage]:
    return [
        message
        for assignment in inbox_result.processed
        for message in assignment.emitted_messages
    ]


def _node_ids_from_replayed_messages(messages: Sequence[object], node_id: str) -> list[str]:
    node_ids = {node_id, "local-ledger"}
    for message in messages:
        sender = getattr(message, "sender_node_id")
        recipient = getattr(message, "recipient_node_id")
        node_ids.add(sender)
        if recipient is not None:
            node_ids.add(recipient)
    return sorted(node_ids)


def _inbox_process_result_to_dict(
    inbox_result: InboxProcessResult,
    ledger: ContributionLedger,
    ledger_path: str | None,
) -> dict[str, object]:
    emitted_messages = [
        {
            "id": message.message_id,
            "type": message.message_type,
            "sender": message.sender_node_id,
            "recipient": message.recipient_node_id,
        }
        for assignment in inbox_result.processed
        for message in assignment.emitted_messages
    ]
    validation_outcomes = [
        {
            "job_id": assignment.job.job_id,
            "valid": assignment.validation.valid,
            "credited_units": assignment.contribution_record.contribution_units,
            "reason": assignment.validation.reason,
        }
        for assignment in inbox_result.processed
    ]
    payload: dict[str, object] = {
        "command": "process-local-inbox",
        "node_id": inbox_result.node_id,
        "processed_assignment_count": len(inbox_result.processed),
        "ignored_message_ids": list(inbox_result.ignored_message_ids),
        "emitted_messages": emitted_messages,
        "validation_outcomes": validation_outcomes,
    }
    if ledger_path is not None:
        node_summary = ledger.summary_for_node(inbox_result.node_id)
        node_ids = ledger.node_ids()
        payload["ledger_summary"] = {
            "path": ledger_path,
            "total_units": sum(
                ledger.summary_for_node(summary_node_id).total_contribution_units
                for summary_node_id in node_ids
            ),
            "node_units": node_summary.total_contribution_units,
            "record_count": sum(
                ledger.summary_for_node(summary_node_id).total_result_count
                for summary_node_id in node_ids
            ),
        }
    return payload


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

    if args.command == "process-local-inbox":
        try:
            payload = process_local_inbox(
                node_id=args.node_id,
                message_log_path=args.message_log_path,
                ledger_path=args.ledger_path,
                output_message_log_path=args.output_message_log_path,
            )
        except (MessageLogPersistenceError, LedgerPersistenceError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(payload, sort_keys=True))
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
