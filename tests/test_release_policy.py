import unittest

from scripts import release_policy


class ReleasePolicyTests(unittest.TestCase):
    def test_sequence_starts_at_116_and_ignores_legacy_tags(self) -> None:
        self.assertEqual(
            release_policy.next_build(["v0.2.0-alpha-deadbeef", "v0.1.0"]), 116
        )

    def test_sequence_is_shared_across_numbered_tags(self) -> None:
        tags = ["v0.2.0-alpha.116", "v0.2.0-alpha.120", "v0.2.0-alpha-hash"]
        self.assertEqual(release_policy.next_build(tags), 121)
        self.assertEqual(release_policy.latest_numbered_tag(tags), "v0.2.0-alpha.120")

    def test_required_checks_reject_missing_pending_skipped_and_failing(self) -> None:
        required = {
            "contexts": ["legacy", "pending"],
            "checks": [{"context": "tests"}, {"context": "skipped"}],
        }
        checks = {
            "check_runs": [
                {"name": "tests", "conclusion": "success"},
                {"name": "skipped", "conclusion": "skipped"},
                {"name": "pending", "conclusion": None},
            ]
        }
        statuses = {"statuses": [{"context": "legacy", "state": "failure"}]}

        self.assertEqual(
            release_policy.verify_required_checks(required, checks, statuses),
            [
                "legacy: check=missing, status=failure",
                "pending: check=None, status=missing",
                "skipped: check=skipped, status=missing",
            ],
        )

    def test_required_checks_accept_successful_checks_and_statuses(self) -> None:
        required = {"contexts": ["legacy"], "checks": [{"context": "tests"}]}
        checks = {"check_runs": [{"name": "tests", "conclusion": "success"}]}
        statuses = {"statuses": [{"context": "legacy", "state": "success"}]}
        self.assertEqual(
            release_policy.verify_required_checks(required, checks, statuses), []
        )


if __name__ == "__main__":
    unittest.main()
