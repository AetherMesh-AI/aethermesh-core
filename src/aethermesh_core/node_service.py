"""Local-only node inbox processing service for assigned work messages."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from aethermesh_core.ledger import ContributionLedger, ContributionRecord
from aethermesh_core.message_bus import LocalMessageBus
from aethermesh_core.messages import MeshMessage
from aethermesh_core.models import Job, JobResult, NodeIdentity
from aethermesh_core.runner import LocalRunner
from aethermesh_core.validation import ValidationResult, validate_job_result


@dataclass(frozen=True)
class ProcessedAssignment:
    """Deterministic audit data for one inbox assignment processed locally."""

    message_id: str
    correlation_id: str | None
    job: Job
    result: JobResult
    validation: ValidationResult
    contribution_record: ContributionRecord
    emitted_messages: list[MeshMessage]


@dataclass(frozen=True)
class InboxProcessResult:
    """Structured result returned by one local inbox processing pass."""

    node_id: str
    processed: list[ProcessedAssignment]
    ignored_message_ids: list[str]
    skipped_processed_message_ids: list[str]
    processed_message_ids: list[str]


class LocalNodeService:
    """Synchronous local-only handler for one node's assigned-work inbox."""

    def __init__(
        self,
        *,
        identity: NodeIdentity,
        message_bus: LocalMessageBus,
        runner: LocalRunner,
        ledger: ContributionLedger,
        ledger_node_id: str = "local-ledger",
        processed_message_ids: list[str] | None = None,
    ) -> None:
        self.identity = identity
        self.message_bus = message_bus
        self.runner = runner
        self.ledger = ledger
        self.ledger_node_id = ledger_node_id
        self._processed_message_ids_in_order = list(processed_message_ids or [])
        self._processed_message_ids: set[str] = set(self._processed_message_ids_in_order)

    def process_inbox(self) -> InboxProcessResult:
        """Process unhandled ``job_assigned`` messages addressed to this node.

        The service is intentionally in-memory and instance-idempotent: a single
        service instance records each assignment message at most once.
        """

        processed: list[ProcessedAssignment] = []
        ignored_message_ids: list[str] = []
        skipped_processed_message_ids: list[str] = []

        for message in self.message_bus.inbox_for(self.identity.node_id):
            if message.message_id in self._processed_message_ids:
                ignored_message_ids.append(message.message_id)
                skipped_processed_message_ids.append(message.message_id)
                continue
            if message.message_type != "job_assigned":
                ignored_message_ids.append(message.message_id)
                continue
            if message.recipient_node_id != self.identity.node_id:
                ignored_message_ids.append(message.message_id)
                continue

            assignment = self._process_assignment(message)
            processed.append(assignment)
            self._processed_message_ids.add(message.message_id)
            self._processed_message_ids_in_order.append(message.message_id)

        return InboxProcessResult(
            node_id=self.identity.node_id,
            processed=processed,
            ignored_message_ids=ignored_message_ids,
            skipped_processed_message_ids=skipped_processed_message_ids,
            processed_message_ids=list(self._processed_message_ids_in_order),
        )

    def _process_assignment(self, message: MeshMessage) -> ProcessedAssignment:
        job = _job_from_assignment_payload(message)
        result = self.runner.run(job)
        validation = validate_job_result(job, result)
        accounted_result = result if validation.valid else replace(result, contribution_units=0)
        record = self.ledger.record(
            accounted_result,
            validation_valid=validation.valid,
            validation_reason=validation.reason,
            job_type=job.job_type,
        )

        result_message = self._send_message(
            message_type="job_result_reported",
            recipient_node_id=self.ledger_node_id,
            payload={
                "job_id": result.job_id,
                "status": result.status,
                "success": result.status == "completed",
                "output": result.output,
                "error": result.error,
            },
            correlation_id=message.correlation_id or job.job_id,
        )
        contribution_message = self._send_message(
            message_type="contribution_recorded",
            recipient_node_id=self.identity.node_id,
            payload={
                "job_id": record.job_id,
                "node_id": record.node_id,
                "status": record.status,
                "valid": validation.valid,
                "validation": validation.reason,
                "contribution_units": record.contribution_units,
            },
            correlation_id=message.correlation_id or job.job_id,
        )

        return ProcessedAssignment(
            message_id=message.message_id,
            correlation_id=message.correlation_id,
            job=job,
            result=result,
            validation=validation,
            contribution_record=record,
            emitted_messages=[result_message, contribution_message],
        )

    def _send_message(
        self,
        *,
        message_type: str,
        recipient_node_id: str | None,
        payload: dict[str, Any],
        correlation_id: str | None,
    ) -> MeshMessage:
        message = MeshMessage(
            message_id=f"msg-{len(self.message_bus.log()) + 1:04d}",
            message_type=message_type,
            sender_node_id=(
                self.identity.node_id
                if message_type == "job_result_reported"
                else self.ledger_node_id
            ),
            recipient_node_id=recipient_node_id,
            payload=payload,
            correlation_id=correlation_id,
        )
        return self.message_bus.send(message)


def _job_from_assignment_payload(message: MeshMessage) -> Job:
    payload = message.payload
    job_id = payload.get("job_id")
    job_type = payload.get("job_type")
    job_payload = payload.get("payload", {})

    if not isinstance(job_id, str) or job_id == "":
        job_id = _fallback_job_id(message)
    if not isinstance(job_type, str) or job_type == "":
        job_type = "__malformed_assignment__"
    if not isinstance(job_payload, dict):
        job_payload = {}

    return Job(job_id=job_id, job_type=job_type, payload=dict(job_payload))


def _fallback_job_id(message: MeshMessage) -> str:
    if message.correlation_id is not None:
        return message.correlation_id
    return f"malformed-{message.message_id}"
