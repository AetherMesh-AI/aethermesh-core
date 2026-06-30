"""Command-line interface for the local AetherMesh prototype."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from urllib.parse import quote

from aethermesh_core.dispatch import dispatch_local_batch
from aethermesh_core.flow_audit import FlowAuditError, audit_local_flow
from aethermesh_core.identity import IdentityPersistenceError, load_or_create_identity
from aethermesh_core.job_manifest import ManifestError, load_job_manifest
from aethermesh_core.ledger import (
    ContributionLedger,
    LedgerPersistenceError,
    load_existing_ledger_document,
    load_ledger_document,
    save_ledger_document,
)
from aethermesh_core.local_transport import (
    LocalTransportError,
    load_local_inbox,
    materialize_local_inboxes,
)
from aethermesh_core.message_bus import LocalMessageBus
from aethermesh_core.message_log import (
    MessageLogPersistenceError,
    build_dispatch_message_log_document,
    build_flow_message_log_document,
    build_message_log_document,
    build_replayed_message_log_document,
    load_message_log_messages,
    load_worker_emitted_messages,
    write_message_log,
)
from aethermesh_core.messages import MeshMessage
from aethermesh_core.models import Job, NodeIdentity
from aethermesh_core.node_announcement import NodeAnnouncementError, announce_local_node
from aethermesh_core.node_service import InboxProcessResult, LocalNodeService
from aethermesh_core.node_state import (
    LocalNodeProcessingState,
    NodeStatePersistenceError,
    load_node_processing_state,
    save_node_processing_state,
)
from aethermesh_core.peer_registry import PeerRegistryError, peer_summary_document
from aethermesh_core.receipts import (
    ReceiptPersistenceError,
    build_receipt_document,
    load_receipt_document_if_exists,
    write_receipt_document,
)
from aethermesh_core.runner import LocalRunner
from aethermesh_core.scheduler import NodeStatus
from aethermesh_core.simulation import run_local_simulation
from aethermesh_core.validation import validate_job_result


@dataclass(frozen=True)
class InboxReplayRequest:
    node_id: str
    message_log_path: str | None = None
    transport_dir: str | None = None
    ledger_path: str | None = None
    output_message_log_path: str | None = None
    node_state_path: str | None = None


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

    dispatch = subcommands.add_parser(
        "dispatch-local-batch",
        help="Write assignment-only local dispatch messages for a manifest batch.",
    )
    dispatch.add_argument(
        "--manifest",
        required=True,
        help="Path to a version 1 local job-batch JSON manifest.",
    )
    dispatch.add_argument(
        "--message-log-path",
        required=True,
        help="Path to write the version 1 assignment-only local message log.",
    )

    local_flow = subcommands.add_parser(
        "run-local-flow",
        help="Run dispatch plus all available local worker inboxes for a manifest.",
    )
    local_flow.add_argument(
        "--manifest",
        required=True,
        help="Path to a version 1 local job-batch JSON manifest.",
    )
    local_flow.add_argument(
        "--output-dir",
        required=True,
        help="Directory for deterministic local flow artifacts.",
    )

    audit_local = subcommands.add_parser(
        "audit-local-flow",
        help="Read and verify a completed run-local-flow artifact directory.",
    )
    audit_local.add_argument(
        "--output-dir",
        required=True,
        help="Directory containing deterministic local flow artifacts to audit.",
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

    peer_summary = subcommands.add_parser(
        "peer-summary",
        help="Inspect heartbeat-derived peers from an existing local message log.",
    )
    peer_summary.add_argument(
        "--message-log-path",
        required=True,
        help="Path to an existing version 1 local message log.",
    )

    announce = subcommands.add_parser(
        "announce-local-node",
        help="Write one local node heartbeat announcement message log.",
    )
    announce.add_argument(
        "--node-id",
        required=True,
        help="Local node id to announce.",
    )
    announce.add_argument(
        "--message-log-path",
        required=True,
        help="New path to write the version 1 local announcement message log.",
    )
    announce.add_argument(
        "--status",
        default=NodeStatus.AVAILABLE.value,
        choices=[status.value for status in NodeStatus],
        help="Local node status to announce. Defaults to available.",
    )
    announce.add_argument(
        "--capability",
        action="append",
        default=None,
        help="Capability to announce. May be supplied multiple times; defaults to local capabilities.",
    )

    materialize = subcommands.add_parser(
        "materialize-local-inboxes",
        help="Materialize addressed message-log entries into file-backed local inboxes.",
    )
    materialize.add_argument(
        "--message-log-path",
        required=True,
        help="Path to a version 1 local dispatch/message log.",
    )
    materialize.add_argument(
        "--transport-dir",
        required=True,
        help="Directory where per-node local transport inboxes should be written.",
    )

    inbox = subcommands.add_parser(
        "process-local-inbox",
        help="Replay a local message log or local transport inbox for one node's work.",
    )
    inbox.add_argument(
        "--node-id",
        required=True,
        help="Local node id whose replayed inbox should be processed.",
    )
    inbox.add_argument(
        "--message-log-path",
        default=None,
        help="Path to a version 1 local message log produced by run-local-batch.",
    )
    inbox.add_argument(
        "--transport-dir",
        default=None,
        help="Read this node's file-backed local transport inbox instead of a message log.",
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
    inbox.add_argument(
        "--node-state-path",
        default=None,
        help="Opt in to JSON-file-backed local processed-assignment state for resume/idempotency.",
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
        raise IdentityPersistenceError(
            "--node-id and --identity-path are mutually exclusive"
        )
    if identity_path is not None:
        identity = load_or_create_identity(identity_path)
    else:
        identity = (
            NodeIdentity(node_id=node_id) if node_id else NodeIdentity.ephemeral()
        )
    job = Job(job_id="demo-echo", job_type="echo", payload={"message": message})
    result = LocalRunner(identity).run(job)
    result_dict = result.to_dict()
    if not include_ledger and ledger_path is None:
        return result_dict

    validation = validate_job_result(job, result)
    record_result = (
        result if validation.valid else replace(result, contribution_units=0)
    )
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
        Job(
            job_id="keyword-extract-1",
            job_type="keyword_extract",
            payload={
                "text": "AetherMesh nodes process useful local work for the mesh.",
                "limit": 5,
            },
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


def dispatch_local_batch_command(
    manifest_path: str,
    message_log_path: str,
) -> dict[str, object]:
    """Dispatch a manifest batch to a local message log without execution."""

    batch = load_job_manifest(manifest_path)
    dispatch = dispatch_local_batch(
        manifest_path=manifest_path,
        message_log_path=message_log_path,
        nodes=batch.nodes,
        jobs=batch.jobs,
    )
    message_log_document = build_dispatch_message_log_document(
        messages=dispatch.messages,
        jobs=dispatch.jobs,
        nodes=dispatch.nodes,
        assignments=dispatch.assignments,
        manifest_path=manifest_path,
    )
    write_message_log(message_log_path, message_log_document)
    return dispatch.to_dict()


def summarize_ledger(ledger_path: str) -> dict[str, object]:
    """Load an existing ledger and return read-only aggregate totals."""

    ledger, _extra_fields = load_existing_ledger_document(ledger_path)
    return ledger.summary_document(ledger_path)


def summarize_peers(message_log_path: str) -> dict[str, object]:
    """Load an existing message log and return a read-only peer roster."""

    return peer_summary_document(message_log_path)


def run_local_flow(manifest_path: str, output_dir: str) -> dict[str, object]:
    """Run dispatch and all available local worker inboxes as one local flow."""

    batch = load_job_manifest(manifest_path)
    output_path = Path(output_dir)
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ValueError(f"could not create output directory: {exc}") from exc

    dispatch_message_log_path = output_path / "dispatch-message-log.json"
    flow_message_log_path = output_path / "flow-message-log.json"
    ledger_path = output_path / "ledger.json"
    receipts_path = output_path / "receipts.json"
    node_state_dir = output_path / "node-state"
    worker_log_dir = output_path / "worker-message-logs"

    available_node_ids = [
        node.node_id for node in batch.nodes if node.status.value == "available"
    ]
    offline_node_ids = [
        node.node_id for node in batch.nodes if node.status.value == "offline"
    ]

    # Validate existing resumable inputs before overwriting any flow artifacts.
    load_ledger_document(ledger_path)
    existing_receipt_document = load_receipt_document_if_exists(receipts_path)
    for node_id in available_node_ids:
        load_node_processing_state(
            _node_artifact_path(node_state_dir, node_id), expected_node_id=node_id
        )

    dispatch_payload = dispatch_local_batch_command(
        manifest_path, str(dispatch_message_log_path)
    )

    per_node_results: list[dict[str, object]] = []
    processed_assignments = []
    emitted_messages_by_node: dict[str, list[MeshMessage]] = {}
    worker_message_log_paths: dict[str, str | Path] = {}
    for node_id in available_node_ids:
        node_state_path = _node_artifact_path(node_state_dir, node_id)
        worker_message_log_path = _node_artifact_path(worker_log_dir, node_id)
        worker_message_log_paths[node_id] = worker_message_log_path
        node_payload, inbox_result = _process_local_inbox(
            InboxReplayRequest(
                node_id=node_id,
                message_log_path=str(dispatch_message_log_path),
                ledger_path=str(ledger_path),
                output_message_log_path=str(worker_message_log_path),
                node_state_path=str(node_state_path),
            )
        )
        processed_assignments.extend(inbox_result.processed)
        raw_processed_count = node_payload["processed_assignment_count"]
        if not isinstance(raw_processed_count, int):
            raise ValueError("process-local-inbox returned invalid processed count")
        processed_count = raw_processed_count
        skipped_ids = node_payload.get("skipped_processed_message_ids", [])
        if not isinstance(skipped_ids, list):
            raise ValueError("process-local-inbox returned invalid skipped id list")
        ignored_ids = node_payload["ignored_message_ids"]
        if not isinstance(ignored_ids, list):
            raise ValueError("process-local-inbox returned invalid ignored id list")
        per_node_results.append(
            {
                "node_id": node_id,
                "node_state_path": str(node_state_path),
                "worker_message_log_path": str(worker_message_log_path),
                "processed_assignment_count": processed_count,
                "skipped_processed_assignment_count": len(skipped_ids),
                "ignored_message_count": len(ignored_ids),
                "ledger_summary": node_payload.get("ledger_summary"),
            }
        )
        emitted_messages_by_node[node_id] = load_worker_emitted_messages(
            worker_message_log_path
        )

    ledger_summary = summarize_ledger(str(ledger_path))
    processed_node_ids = [str(result["node_id"]) for result in per_node_results]
    processed_assignment_count = sum(
        _require_int_result_field(result, "processed_assignment_count")
        for result in per_node_results
    )
    skipped_processed_assignment_count = sum(
        _require_int_result_field(result, "skipped_processed_assignment_count")
        for result in per_node_results
    )
    flow_message_log_document = build_flow_message_log_document(
        dispatch_messages=load_message_log_messages(dispatch_message_log_path),
        emitted_messages_by_node=emitted_messages_by_node,
        manifest_path=manifest_path,
        dispatch_message_log_path=dispatch_message_log_path,
        ledger_path=ledger_path,
        worker_message_log_paths=worker_message_log_paths,
        available_node_ids=available_node_ids,
        offline_node_ids=offline_node_ids,
        processed_node_ids=processed_node_ids,
        processed_assignment_count=processed_assignment_count,
        skipped_processed_assignment_count=skipped_processed_assignment_count,
        total_contribution_units=int(str(ledger_summary["total_contribution_units"])),
    )
    write_message_log(flow_message_log_path, flow_message_log_document)
    receipt_document = build_receipt_document(
        processed_assignments,
        existing_document=existing_receipt_document,
    )
    write_receipt_document(receipts_path, receipt_document)
    return {
        "command": "run-local-flow",
        "manifest_path": manifest_path,
        "output_dir": output_dir,
        "dispatch_message_log_path": str(dispatch_message_log_path),
        "flow_message_log_path": str(flow_message_log_path),
        "receipts_path": str(receipts_path),
        "receipt_count": len(receipt_document["receipts"]),
        "flow_message_count": flow_message_log_document["metadata"]["message_count"],
        "flow_emitted_message_count": flow_message_log_document["metadata"][
            "emitted_message_count"
        ],
        "ledger_path": str(ledger_path),
        "available_node_ids": available_node_ids,
        "offline_node_ids": offline_node_ids,
        "processed_node_ids": processed_node_ids,
        "processed_assignment_count": processed_assignment_count,
        "skipped_processed_assignment_count": skipped_processed_assignment_count,
        "ignored_message_count": sum(
            _require_int_result_field(result, "ignored_message_count")
            for result in per_node_results
        ),
        "total_contribution_units": ledger_summary["total_contribution_units"],
        "ledger_summary": ledger_summary,
        "dispatch_summary": dispatch_payload,
        "node_results": per_node_results,
    }


def _require_int_result_field(result: dict[str, object], field_name: str) -> int:
    value = result.get(field_name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"node result field must be an integer: {field_name}")
    return value


def _node_artifact_path(directory: Path, node_id: str) -> Path:
    return directory / f"{_node_artifact_filename(node_id)}.json"


def _node_artifact_filename(node_id: str) -> str:
    """Return a deterministic, non-merging filename for one manifest node id."""

    if not isinstance(node_id, str) or node_id == "":
        raise ValueError("node id must be a non-empty string")
    return quote(node_id, safe="-._~")


def process_local_inbox(
    *,
    node_id: str,
    message_log_path: str | None = None,
    transport_dir: str | None = None,
    ledger_path: str | None = None,
    output_message_log_path: str | None = None,
    node_state_path: str | None = None,
) -> dict[str, object]:
    """Replay a saved local message log or local transport inbox for one node."""

    if (message_log_path is None) == (transport_dir is None):
        raise ValueError("provide exactly one of --message-log-path or --transport-dir")
    payload, _inbox_result = _process_local_inbox(
        InboxReplayRequest(
            node_id=node_id,
            message_log_path=message_log_path,
            transport_dir=transport_dir,
            ledger_path=ledger_path,
            output_message_log_path=output_message_log_path,
            node_state_path=node_state_path,
        )
    )
    return payload


def _process_local_inbox(
    request: InboxReplayRequest,
) -> tuple[dict[str, object], InboxProcessResult]:
    """Replay saved local messages and return payload plus structured result."""

    if (request.message_log_path is None) == (request.transport_dir is None):
        raise ValueError("provide exactly one of --message-log-path or --transport-dir")
    node_state = (
        load_node_processing_state(
            request.node_state_path, expected_node_id=request.node_id
        )
        if request.node_state_path is not None
        else None
    )
    if request.transport_dir is not None:
        messages = load_local_inbox(
            transport_dir=request.transport_dir, node_id=request.node_id
        )
        source_message_path = str(
            Path(request.transport_dir)
            / "inboxes"
            / f"{_node_artifact_filename(request.node_id)}.json"
        )
    else:
        if request.message_log_path is None:
            raise ValueError("message log path is required")
        messages = load_message_log_messages(request.message_log_path)
        source_message_path = request.message_log_path
    ledger, extra_fields = (
        load_ledger_document(request.ledger_path)
        if request.ledger_path is not None
        else (ContributionLedger(), {})
    )
    message_bus = LocalMessageBus()
    for registered_node_id in _node_ids_from_replayed_messages(
        messages, request.node_id
    ):
        message_bus.register_node(registered_node_id)
    for message in messages:
        message_bus.send(message)

    service = LocalNodeService(
        identity=NodeIdentity(node_id=request.node_id),
        message_bus=message_bus,
        runner=LocalRunner(NodeIdentity(node_id=request.node_id)),
        ledger=ledger,
        processed_message_ids=(
            list(node_state.processed_message_ids) if node_state is not None else None
        ),
    )
    inbox_result = service.process_inbox()
    if request.ledger_path is not None:
        save_ledger_document(request.ledger_path, ledger, extra_fields)
    payload = _inbox_process_result_to_dict(inbox_result, ledger, request.ledger_path)
    if request.output_message_log_path is not None:
        emitted_messages = _emitted_messages_from_inbox_result(inbox_result)
        output_document = build_replayed_message_log_document(
            replayed_messages=messages,
            emitted_messages=emitted_messages,
            node_id=request.node_id,
            source_message_log_path=source_message_path,
            ledger_path=request.ledger_path,
            processed_assignment_count=len(inbox_result.processed),
            ignored_message_ids=list(inbox_result.ignored_message_ids),
        )
        write_message_log(request.output_message_log_path, output_document)
        payload["output_message_log_path"] = request.output_message_log_path
        payload["final_message_count"] = len(messages) + len(emitted_messages)
    if request.node_state_path is not None and node_state is not None:
        updated_state = LocalNodeProcessingState(
            node_id=request.node_id,
            processed_message_ids=list(inbox_result.processed_message_ids),
            extra_fields=node_state.extra_fields,
        )
        save_node_processing_state(request.node_state_path, updated_state)
        payload["node_state_path"] = request.node_state_path
        payload["processed_message_ids"] = list(updated_state.processed_message_ids)
        payload["skipped_processed_message_ids"] = list(
            inbox_result.skipped_processed_message_ids
        )
    return payload, inbox_result


def _emitted_messages_from_inbox_result(
    inbox_result: InboxProcessResult,
) -> list[MeshMessage]:
    return [
        message
        for assignment in inbox_result.processed
        for message in assignment.emitted_messages
    ]


def _node_ids_from_replayed_messages(
    messages: Sequence[object], node_id: str
) -> list[str]:
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

    if args.command == "dispatch-local-batch":
        try:
            payload = dispatch_local_batch_command(args.manifest, args.message_log_path)
        except ManifestError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except MessageLogPersistenceError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except ValueError as exc:
            print(f"error: local batch dispatch failed: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(payload, sort_keys=True))
        return 0

    if args.command == "run-local-flow":
        try:
            payload = run_local_flow(args.manifest, args.output_dir)
        except ManifestError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except (
            MessageLogPersistenceError,
            LedgerPersistenceError,
            NodeStatePersistenceError,
            ValueError,
        ) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(payload, sort_keys=True))
        return 0

    if args.command == "audit-local-flow":
        try:
            payload = audit_local_flow(args.output_dir)
        except (
            FlowAuditError,
            MessageLogPersistenceError,
            LedgerPersistenceError,
            ReceiptPersistenceError,
            ValueError,
        ) as exc:
            print(f"error: {exc}", file=sys.stderr)
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

    if args.command == "peer-summary":
        try:
            payload = summarize_peers(args.message_log_path)
        except PeerRegistryError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(payload, sort_keys=True))
        return 0

    if args.command == "announce-local-node":
        try:
            payload = announce_local_node(
                node_id=args.node_id,
                message_log_path=args.message_log_path,
                status=args.status,
                capabilities=args.capability,
            )
        except NodeAnnouncementError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(payload, sort_keys=True))
        return 0

    if args.command == "materialize-local-inboxes":
        try:
            payload = materialize_local_inboxes(
                message_log_path=args.message_log_path,
                transport_dir=args.transport_dir,
            )
        except (MessageLogPersistenceError, LocalTransportError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(payload, sort_keys=True))
        return 0

    if args.command == "process-local-inbox":
        try:
            payload = process_local_inbox(
                node_id=args.node_id,
                message_log_path=args.message_log_path,
                transport_dir=args.transport_dir,
                ledger_path=args.ledger_path,
                output_message_log_path=args.output_message_log_path,
                node_state_path=args.node_state_path,
            )
        except (
            MessageLogPersistenceError,
            LocalTransportError,
            LedgerPersistenceError,
            NodeStatePersistenceError,
            ValueError,
        ) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(payload, sort_keys=True))
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
