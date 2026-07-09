"""Reusable local node runtime work execution paths.

CLI commands should call these functions and only format their structured results.
The functions in this module own manifest-backed local work execution,
contribution attribution, optional ledger persistence, and optional audit message
log creation for the local-only prototype.
"""

from __future__ import annotations

from aethermesh_core.job_manifest import ManifestError, load_job_manifest
from aethermesh_core.ledger import load_ledger_document, save_ledger_document
from aethermesh_core.message_log import (
    build_message_log_document,
    write_message_log,
)
from aethermesh_core.simulation import run_local_simulation


def run_local_batch(
    manifest_path: str,
    ledger_path: str | None = None,
    message_log_path: str | None = None,
) -> dict[str, object]:
    """Run a local simulation from a validated JSON manifest.

    Returns a JSON-serializable result without printing so CLIs, APIs, tests, and
    future local frontends can reuse the same runtime path.
    """

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
