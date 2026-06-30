import unittest

from aethermesh_core.contribution import score_validated_contribution
from aethermesh_core.models import Job, JobResult
from aethermesh_core.validation import validate_job_result


class ValidationTests(unittest.TestCase):
    def test_completed_echo_result_with_matching_output_is_valid(self) -> None:
        job = Job(job_id="echo-1", job_type="echo", payload={"message": "hello"})
        result = JobResult(
            job_id="echo-1",
            node_id="node-a",
            status="completed",
            output="hello",
            error=None,
            contribution_units=1,
        )

        validation = validate_job_result(job, result)

        self.assertTrue(validation.valid)
        self.assertEqual(validation.reason, "ok")
        self.assertEqual(
            validation.to_dict(),
            {
                "job_id": "echo-1",
                "result_job_id": "echo-1",
                "valid": True,
                "reason": "ok",
            },
        )

    def test_mismatched_job_id_is_invalid(self) -> None:
        validation = validate_job_result(
            Job(job_id="echo-1", job_type="echo", payload={"message": "hello"}),
            JobResult(
                job_id="echo-other",
                node_id="node-a",
                status="completed",
                output="hello",
                error=None,
                contribution_units=1,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "job_id_mismatch")

    def test_unsupported_job_type_is_invalid(self) -> None:
        validation = validate_job_result(
            Job(job_id="job-1", job_type="unsupported", payload={"message": "hello"}),
            JobResult(
                job_id="job-1",
                node_id="node-a",
                status="completed",
                output="hello",
                error=None,
                contribution_units=1,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "unsupported_job_type")

    def test_non_completed_result_is_invalid(self) -> None:
        validation = validate_job_result(
            Job(job_id="echo-1", job_type="echo", payload={"message": "hello"}),
            JobResult(
                job_id="echo-1",
                node_id="node-a",
                status="failed",
                output=None,
                error="boom",
                contribution_units=0,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "result_not_completed")

    def test_missing_payload_message_is_invalid(self) -> None:
        validation = validate_job_result(
            Job(job_id="echo-1", job_type="echo", payload={}),
            JobResult(
                job_id="echo-1",
                node_id="node-a",
                status="completed",
                output="",
                error=None,
                contribution_units=1,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "missing_payload_message")

    def test_non_string_payload_message_is_invalid(self) -> None:
        validation = validate_job_result(
            Job(job_id="echo-1", job_type="echo", payload={"message": 123}),
            JobResult(
                job_id="echo-1",
                node_id="node-a",
                status="completed",
                output=123,
                error=None,
                contribution_units=1,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "missing_payload_message")

    def test_incorrect_output_is_invalid(self) -> None:
        validation = validate_job_result(
            Job(job_id="echo-1", job_type="echo", payload={"message": "expected"}),
            JobResult(
                job_id="echo-1",
                node_id="node-a",
                status="completed",
                output="actual",
                error=None,
                contribution_units=1,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "output_mismatch")

    def test_completed_result_with_unexpected_contribution_units_is_invalid(
        self,
    ) -> None:
        validation = validate_job_result(
            Job(job_id="echo-1", job_type="echo", payload={"message": "hello"}),
            JobResult(
                job_id="echo-1",
                node_id="node-a",
                status="completed",
                output="hello",
                error=None,
                contribution_units=999,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "unexpected_contribution_units")

    def test_completed_text_stats_result_with_matching_output_is_valid(self) -> None:
        validation = validate_job_result(
            Job(
                job_id="text-stats-1",
                job_type="text_stats",
                payload={"text": "hello mesh\nhello node"},
            ),
            JobResult(
                job_id="text-stats-1",
                node_id="node-a",
                status="completed",
                output={
                    "character_count": len("hello mesh\nhello node"),
                    "word_count": 4,
                    "line_count": 2,
                    "normalized_preview": "hello mesh hello node",
                },
                error=None,
                contribution_units=1,
            ),
        )

        self.assertEqual(
            validation.to_dict(),
            {
                "job_id": "text-stats-1",
                "result_job_id": "text-stats-1",
                "valid": True,
                "reason": "ok",
            },
        )

    def test_text_stats_recomputes_expected_output(self) -> None:
        validation = validate_job_result(
            Job(
                job_id="text-stats-1", job_type="text_stats", payload={"text": "hello"}
            ),
            JobResult(
                job_id="text-stats-1",
                node_id="node-a",
                status="completed",
                output={
                    "character_count": 999,
                    "word_count": 1,
                    "line_count": 1,
                    "normalized_preview": "hello",
                },
                error=None,
                contribution_units=1,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "output_mismatch")

    def test_text_stats_malformed_payload_is_invalid(self) -> None:
        missing = validate_job_result(
            Job(job_id="text-stats-missing", job_type="text_stats", payload={}),
            JobResult(
                job_id="text-stats-missing",
                node_id="node-a",
                status="completed",
                output=None,
                error=None,
                contribution_units=1,
            ),
        )
        non_string = validate_job_result(
            Job(
                job_id="text-stats-non-string",
                job_type="text_stats",
                payload={"text": 123},
            ),
            JobResult(
                job_id="text-stats-non-string",
                node_id="node-a",
                status="completed",
                output=None,
                error=None,
                contribution_units=1,
            ),
        )

        self.assertFalse(missing.valid)
        self.assertEqual(missing.reason, "missing_payload_text")
        self.assertFalse(non_string.valid)
        self.assertEqual(non_string.reason, "missing_payload_text")

    def test_completed_keyword_extract_result_with_matching_output_is_valid(
        self,
    ) -> None:
        validation = validate_job_result(
            Job(
                job_id="keyword-1",
                job_type="keyword_extract",
                payload={
                    "text": "AetherMesh nodes process useful local work for the mesh.",
                    "limit": 5,
                },
            ),
            JobResult(
                job_id="keyword-1",
                node_id="node-a",
                status="completed",
                output={
                    "keywords": [
                        {"term": "aethermesh", "count": 1},
                        {"term": "local", "count": 1},
                        {"term": "mesh", "count": 1},
                        {"term": "nodes", "count": 1},
                        {"term": "process", "count": 1},
                    ],
                    "unique_terms": 7,
                    "total_terms": 7,
                },
                error=None,
                contribution_units=1,
            ),
        )

        self.assertTrue(validation.valid)
        self.assertEqual(validation.reason, "ok")

    def test_keyword_extract_rejects_changed_output(self) -> None:
        job = Job(
            job_id="keyword-1",
            job_type="keyword_extract",
            payload={"text": "alpha beta beta", "limit": 2},
        )
        valid_output = {
            "keywords": [
                {"term": "beta", "count": 2},
                {"term": "alpha", "count": 1},
            ],
            "unique_terms": 2,
            "total_terms": 3,
        }
        cases = [
            (
                "changed_order",
                {
                    "keywords": list(reversed(valid_output["keywords"])),
                    "unique_terms": 2,
                    "total_terms": 3,
                },
            ),
            (
                "missing_terms",
                {
                    "keywords": [valid_output["keywords"][0]],
                    "unique_terms": 2,
                    "total_terms": 3,
                },
            ),
            (
                "changed_count",
                {
                    "keywords": [
                        {"term": "beta", "count": 1},
                        {"term": "alpha", "count": 1},
                    ],
                    "unique_terms": 2,
                    "total_terms": 3,
                },
            ),
            (
                "incorrect_totals",
                {
                    "keywords": valid_output["keywords"],
                    "unique_terms": 99,
                    "total_terms": 3,
                },
            ),
            ("malformed_output", ["beta", "alpha"]),
        ]

        for name, output in cases:
            with self.subTest(name=name):
                validation = validate_job_result(
                    job,
                    JobResult(
                        job_id="keyword-1",
                        node_id="node-a",
                        status="completed",
                        output=output,
                        error=None,
                        contribution_units=1,
                    ),
                )
                self.assertFalse(validation.valid)
                self.assertEqual(validation.reason, "output_mismatch")

    def test_keyword_extract_rejects_output_from_different_payload(self) -> None:
        validation = validate_job_result(
            Job(
                job_id="keyword-1",
                job_type="keyword_extract",
                payload={"text": "alpha beta"},
            ),
            JobResult(
                job_id="keyword-1",
                node_id="node-a",
                status="completed",
                output={
                    "keywords": [{"term": "gamma", "count": 1}],
                    "unique_terms": 1,
                    "total_terms": 1,
                },
                error=None,
                contribution_units=1,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "output_mismatch")

    def test_keyword_extract_malformed_payload_is_invalid(self) -> None:
        validation = validate_job_result(
            Job(
                job_id="keyword-blank", job_type="keyword_extract", payload={"text": ""}
            ),
            JobResult(
                job_id="keyword-blank",
                node_id="node-a",
                status="completed",
                output={"keywords": [], "unique_terms": 0, "total_terms": 0},
                error=None,
                contribution_units=1,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "malformed_keyword_extract_payload")

    def test_failed_keyword_extract_result_earns_zero_credit(self) -> None:
        validation = validate_job_result(
            Job(
                job_id="keyword-1",
                job_type="keyword_extract",
                payload={"text": "alpha"},
            ),
            JobResult(
                job_id="keyword-1",
                node_id="node-a",
                status="failed",
                output=None,
                error="keyword_extract payload requires non-empty string field: text",
                contribution_units=0,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "result_not_completed")

    def test_completed_text_chunk_result_with_matching_output_is_valid(self) -> None:
        validation = validate_job_result(
            Job(
                job_id="chunk-1",
                job_type="text_chunk",
                payload={"text": "alpha beta gamma", "max_chars": 10},
            ),
            JobResult(
                job_id="chunk-1",
                node_id="node-a",
                status="completed",
                output={
                    "chunks": [
                        {"index": 0, "text": "alpha beta", "character_count": 10},
                        {"index": 1, "text": " gamma", "character_count": 6},
                    ],
                    "chunk_count": 2,
                    "character_count": 16,
                },
                error=None,
                contribution_units=1,
            ),
        )

        self.assertTrue(validation.valid)
        self.assertEqual(validation.reason, "ok")

    def test_text_chunk_rejects_changed_output(self) -> None:
        job = Job(
            job_id="chunk-1",
            job_type="text_chunk",
            payload={"text": "alpha beta gamma", "max_chars": 10},
        )
        valid_output = {
            "chunks": [
                {"index": 0, "text": "alpha beta", "character_count": 10},
                {"index": 1, "text": " gamma", "character_count": 6},
            ],
            "chunk_count": 2,
            "character_count": 16,
        }
        cases = [
            (
                "changed_text",
                {
                    **valid_output,
                    "chunks": [{"index": 0, "text": "alpha", "character_count": 5}],
                },
            ),
            (
                "changed_order",
                {**valid_output, "chunks": list(reversed(valid_output["chunks"]))},
            ),
            ("changed_chunk_count", {**valid_output, "chunk_count": 99}),
            ("changed_total", {**valid_output, "character_count": 99}),
            ("malformed_output", ["alpha beta", " gamma"]),
        ]

        for name, output in cases:
            with self.subTest(name=name):
                validation = validate_job_result(
                    job,
                    JobResult(
                        job_id="chunk-1",
                        node_id="node-a",
                        status="completed",
                        output=output,
                        error=None,
                        contribution_units=1,
                    ),
                )
                self.assertFalse(validation.valid)
                self.assertEqual(validation.reason, "output_mismatch")

    def test_text_chunk_malformed_payload_is_invalid(self) -> None:
        validation = validate_job_result(
            Job(
                job_id="chunk-bad",
                job_type="text_chunk",
                payload={"text": "hello", "max_chars": 0},
            ),
            JobResult(
                job_id="chunk-bad",
                node_id="node-a",
                status="completed",
                output={"chunks": [], "chunk_count": 0, "character_count": 0},
                error=None,
                contribution_units=1,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "malformed_text_chunk_payload")

    def test_failed_text_chunk_result_earns_zero_credit(self) -> None:
        validation = validate_job_result(
            Job(job_id="chunk-1", job_type="text_chunk", payload={"text": "alpha"}),
            JobResult(
                job_id="chunk-1",
                node_id="node-a",
                status="failed",
                output=None,
                error="text_chunk payload requires string field: text",
                contribution_units=0,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "result_not_completed")

    def test_completed_text_embed_result_with_matching_output_is_valid(self) -> None:
        validation = validate_job_result(
            Job(
                job_id="embed-1",
                job_type="text_embed",
                payload={
                    "text": "AetherMesh nodes process useful local work for the mesh.",
                    "dimensions": 8,
                },
            ),
            JobResult(
                job_id="embed-1",
                node_id="node-a",
                status="completed",
                output={
                    "dimensions": 8,
                    "token_count": 9,
                    "unique_terms": 9,
                    "vector": [4, 1, 1, 1, 0, 0, 1, 1],
                },
                error=None,
                contribution_units=1,
            ),
        )

        self.assertTrue(validation.valid)
        self.assertEqual(validation.reason, "ok")

    def test_text_embed_rejects_changed_output(self) -> None:
        job = Job(
            job_id="embed-1",
            job_type="text_embed",
            payload={"text": "alpha beta beta", "dimensions": 4},
        )
        valid_output = {
            "dimensions": 4,
            "token_count": 3,
            "unique_terms": 2,
            "vector": [0, 2, 1, 0],
        }
        cases = [
            ("changed_dimensions", {**valid_output, "dimensions": 8}),
            ("changed_token_count", {**valid_output, "token_count": 99}),
            ("changed_unique_terms", {**valid_output, "unique_terms": 99}),
            ("changed_vector", {**valid_output, "vector": [3, 0, 0, 0]}),
            ("malformed_output", [0, 2, 1, 0]),
        ]

        for name, output in cases:
            with self.subTest(name=name):
                validation = validate_job_result(
                    job,
                    JobResult(
                        job_id="embed-1",
                        node_id="node-a",
                        status="completed",
                        output=output,
                        error=None,
                        contribution_units=1,
                    ),
                )
                self.assertFalse(validation.valid)
                self.assertEqual(validation.reason, "output_mismatch")

    def test_text_embed_malformed_payload_is_invalid(self) -> None:
        cases = [
            Job(job_id="embed-missing", job_type="text_embed", payload={}),
            Job(job_id="embed-blank", job_type="text_embed", payload={"text": "  "}),
            Job(
                job_id="embed-non-string", job_type="text_embed", payload={"text": 123}
            ),
            Job(
                job_id="embed-bool-dimensions",
                job_type="text_embed",
                payload={"text": "hello", "dimensions": True},
            ),
            Job(
                job_id="embed-small-dimensions",
                job_type="text_embed",
                payload={"text": "hello", "dimensions": 1},
            ),
            Job(
                job_id="embed-large-dimensions",
                job_type="text_embed",
                payload={"text": "hello", "dimensions": 65},
            ),
        ]

        for job in cases:
            with self.subTest(job_id=job.job_id):
                validation = validate_job_result(
                    job,
                    JobResult(
                        job_id=job.job_id,
                        node_id="node-a",
                        status="completed",
                        output=None,
                        error=None,
                        contribution_units=1,
                    ),
                )
                self.assertFalse(validation.valid)
                self.assertEqual(validation.reason, "malformed_text_embed_payload")

    def test_failed_text_embed_result_earns_zero_credit(self) -> None:
        validation = validate_job_result(
            Job(job_id="embed-1", job_type="text_embed", payload={"text": "alpha"}),
            JobResult(
                job_id="embed-1",
                node_id="node-a",
                status="failed",
                output=None,
                error="text_embed payload requires non-empty string field: text",
                contribution_units=0,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "result_not_completed")

    def test_completed_extractive_summary_result_with_matching_output_is_valid(
        self,
    ) -> None:
        validation = validate_job_result(
            Job(
                job_id="summary-1",
                job_type="extractive_summary",
                payload={
                    "text": "AetherMesh nodes run local useful work. Local work reports deterministic outputs. Deterministic outputs make validation and contribution accounting auditable.",
                    "max_sentences": 2,
                },
            ),
            JobResult(
                job_id="summary-1",
                node_id="node-a",
                status="completed",
                output={
                    "summary": "Local work reports deterministic outputs. Deterministic outputs make validation and contribution accounting auditable.",
                    "sentences": [
                        {
                            "index": 1,
                            "text": "Local work reports deterministic outputs.",
                            "score": 9,
                            "token_count": 5,
                        },
                        {
                            "index": 2,
                            "text": "Deterministic outputs make validation and contribution accounting auditable.",
                            "score": 9,
                            "token_count": 8,
                        },
                    ],
                    "sentence_count": 2,
                    "source_sentence_count": 3,
                    "character_count": 158,
                },
                error=None,
                contribution_units=1,
            ),
        )

        self.assertTrue(validation.valid)
        self.assertEqual(validation.reason, "ok")

    def test_extractive_summary_contribution_rejects_malformed_output_shapes(
        self,
    ) -> None:
        job = Job(
            job_id="summary-1",
            job_type="extractive_summary",
            payload={"text": "Alpha beta. Gamma gamma beta.", "max_sentences": 1},
        )
        base_output = {
            "summary": "Gamma gamma beta.",
            "sentences": [
                {"index": 1, "text": "Gamma gamma beta.", "score": 6, "token_count": 3}
            ],
            "sentence_count": 1,
            "source_sentence_count": 2,
            "character_count": 29,
        }
        malformed_outputs = [
            None,
            {**base_output, "summary": None},
            {**base_output, "sentences": "not-a-list"},
            {**base_output, "sentence_count": -1},
            {**base_output, "source_sentence_count": -1},
            {**base_output, "character_count": -1},
            {**base_output, "sentence_count": 2},
            {**base_output, "source_sentence_count": 0},
            {**base_output, "sentences": ["not-a-dict"]},
            {
                **base_output,
                "sentences": [{**base_output["sentences"][0], "index": -1}],
            },
            {
                **base_output,
                "sentences": [{**base_output["sentences"][0], "text": 123}],
            },
            {
                **base_output,
                "sentences": [{**base_output["sentences"][0], "score": -1}],
            },
            {
                **base_output,
                "sentences": [{**base_output["sentences"][0], "token_count": -1}],
            },
        ]

        for output in malformed_outputs:
            with self.subTest(output=output):
                self.assertEqual(
                    score_validated_contribution(
                        job,
                        JobResult(
                            job_id="summary-1",
                            node_id="node-a",
                            status="completed",
                            output=output,
                            error=None,
                            contribution_units=0,
                        ),
                    ),
                    0,
                )

    def test_extractive_summary_rejects_changed_output(self) -> None:
        job = Job(
            job_id="summary-1",
            job_type="extractive_summary",
            payload={"text": "Alpha beta. Gamma gamma beta.", "max_sentences": 1},
        )
        valid_output = {
            "summary": "Gamma gamma beta.",
            "sentences": [
                {"index": 1, "text": "Gamma gamma beta.", "score": 6, "token_count": 3}
            ],
            "sentence_count": 1,
            "source_sentence_count": 2,
            "character_count": 29,
        }
        cases = [
            ("changed_summary", {**valid_output, "summary": "Alpha beta."}),
            (
                "changed_metadata",
                {
                    **valid_output,
                    "sentences": [
                        {
                            "index": 1,
                            "text": "Gamma gamma beta.",
                            "score": 4,
                            "token_count": 3,
                        }
                    ],
                },
            ),
            ("changed_counts", {**valid_output, "sentence_count": 2}),
            ("malformed_output", ["Gamma gamma beta."]),
        ]

        for name, output in cases:
            with self.subTest(name=name):
                validation = validate_job_result(
                    job,
                    JobResult(
                        job_id="summary-1",
                        node_id="node-a",
                        status="completed",
                        output=output,
                        error=None,
                        contribution_units=1,
                    ),
                )
                self.assertFalse(validation.valid)
                self.assertEqual(validation.reason, "output_mismatch")

    def test_extractive_summary_malformed_payload_is_invalid(self) -> None:
        cases = [
            Job(job_id="summary-missing", job_type="extractive_summary", payload={}),
            Job(
                job_id="summary-blank",
                job_type="extractive_summary",
                payload={"text": "  "},
            ),
            Job(
                job_id="summary-non-string",
                job_type="extractive_summary",
                payload={"text": 123},
            ),
            Job(
                job_id="summary-bool-max",
                job_type="extractive_summary",
                payload={"text": "hello", "max_sentences": True},
            ),
            Job(
                job_id="summary-large-max",
                job_type="extractive_summary",
                payload={"text": "hello", "max_sentences": 11},
            ),
        ]

        for job in cases:
            with self.subTest(job_id=job.job_id):
                validation = validate_job_result(
                    job,
                    JobResult(
                        job_id=job.job_id,
                        node_id="node-a",
                        status="completed",
                        output=None,
                        error=None,
                        contribution_units=1,
                    ),
                )
                self.assertFalse(validation.valid)
                self.assertEqual(
                    validation.reason, "malformed_extractive_summary_payload"
                )

    def test_failed_extractive_summary_result_earns_zero_credit(self) -> None:
        validation = validate_job_result(
            Job(
                job_id="summary-1",
                job_type="extractive_summary",
                payload={"text": "alpha"},
            ),
            JobResult(
                job_id="summary-1",
                node_id="node-a",
                status="failed",
                output=None,
                error="extractive_summary payload requires non-empty string field: text",
                contribution_units=0,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "result_not_completed")


if __name__ == "__main__":
    unittest.main()
