"""No-game provenance regression tests for the seven private AOT shards."""
from copy import deepcopy
import unittest

from validate_source_runs import REQUIRED, validate

REPO = "hansifelix/kazuma-laboratorio-privado"
BRANCH = "lingshu-etapa167-atomic16-cx16-20261030"
SHA = "a" * 40


def run(kind, run_id):
    return {
        "id": run_id,
        "path": REQUIRED[kind],
        "status": "completed",
        "conclusion": "success",
        "head_branch": BRANCH,
        "head_sha": SHA,
        "event": "workflow_dispatch",
        "repository": {"full_name": REPO},
        "head_repository": {"full_name": REPO},
    }


class ProvenanceTest(unittest.TestCase):
    def setUp(self):
        self.main = run("main", 1537)
        self.sdk = run("sdk", 1527)

    def check(self, word):
        with self.assertRaisesRegex(ValueError, word):
            validate(self.main, self.sdk, REPO, BRANCH, 1537, 1527)

    def test_valid(self):
        self.assertEqual(validate(self.main, self.sdk, REPO, BRANCH, 1537, 1527), SHA)

    def test_selected_run_id_mismatch(self):
        self.main["id"] = 5
        self.check("does not match")

    def test_failure(self):
        self.sdk["conclusion"] = "failure"
        self.check("completed/success")

    def test_pending(self):
        self.main["status"] = "in_progress"
        self.check("completed/success")

    def test_wrong_branch(self):
        self.main["head_branch"] = "some-other-branch"
        self.check("branch")

    def test_wrong_workflow(self):
        self.sdk["path"] = REQUIRED["main"]
        self.check("workflow path")

    def test_different_sha(self):
        self.sdk["head_sha"] = "b" * 40
        self.check("different Git commits")

    def test_invalid_sha(self):
        self.main["head_sha"] = "not-a-sha"
        self.check("commit SHA")

    def test_forked_head(self):
        self.main["head_repository"] = {"full_name": "outsider/other"}
        self.check("head_repository")

    def test_wrong_repository(self):
        self.sdk["repository"] = {"full_name": "outsider/other"}
        self.check("repository")

    def test_unexpected_event(self):
        self.main["event"] = "pull_request"
        self.check("trigger")

    def test_missing_head_repository(self):
        self.main.pop("head_repository")
        self.check("head_repository")


if __name__ == "__main__":
    unittest.main()
