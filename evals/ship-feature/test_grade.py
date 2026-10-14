import json, tempfile, unittest
from pathlib import Path

from grade import flow_check, flow_reports, review_counts

PLAN_DONE = "## Review\n\n**Fixed**\n\n- A.\n\n**Open**\n\n- None.\n"
PLAN_OPEN = "## Review\n\n**Fixed**\n\n- A.\n\n**Open**\n\n- B.\n"
FINAL_STOP = "Reported the final stop"


def reports(*calls):
    with tempfile.TemporaryDirectory() as tmp:
        fx = Path(tmp)
        (fx / "flow.jsonl").write_text("".join(json.dumps(c) + "\n" for c in calls))
        return flow_reports(fx)


class FlowReportsTest(unittest.TestCase):
    def test_reads_each_call_as_its_argv_without_report(self):
        got = reports(["report", "phase", "review"], ["report", "waiting", "Push and open the merge request?"])
        self.assertEqual(got, [["phase", "review"], ["waiting", "Push and open the merge request?"]])

    def test_none_without_a_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(flow_reports(Path(tmp)))


class FinalStopTest(unittest.TestCase):
    def test_quoted_question_passes(self):
        got = reports(["report", "phase", "merge-request"], ["report", "waiting", "Push and open the merge request?"])
        self.assertTrue(flow_check(FINAL_STOP, got, PLAN_DONE)[0])

    def test_unquoted_question_fails(self):
        got = reports(["report", "phase", "merge-request"], ["report", "waiting", "Push", "and", "open?"])
        self.assertFalse(flow_check(FINAL_STOP, got, PLAN_DONE)[0])

    def test_quoted_block_passes(self):
        got = reports(["report", "review", "--fixed", "1", "--open", "1"], ["report", "blocked", "1 open review item"])
        self.assertTrue(flow_check(FINAL_STOP, got, PLAN_OPEN)[0])

    def test_unquoted_block_fails(self):
        got = reports(["report", "review", "--fixed", "1", "--open", "1"], ["report", "blocked", "1", "open", "item"])
        self.assertFalse(flow_check(FINAL_STOP, got, PLAN_OPEN)[0])


def review(body):
    return f"# Plan\n\n## Review\n\n{body}\n## Next\n\n- [ ] Not a finding\n"


class ReviewCountsTest(unittest.TestCase):
    def test_finding_shaped_like_a_label_is_a_finding(self):
        body = "**Fixed**\n\n- Fixed duplicate tags: deduped in store.\n- **Fixed exit code**: now 2.\n- Open list --tag: rejected.\n\n**Open**\n\n- One.\n"
        self.assertEqual(review_counts(review(body)), (3, 1))

    def test_none_is_no_finding(self):
        body = "Fixed:\n\n- A.\n\nOpen:\n\n- None.\n\nWhere to look:\n\n1. grade.py\n"
        self.assertEqual(review_counts(review(body)), (1, 0))

    def test_labels_with_a_note_before_the_colon(self):
        body = "Fixed (`0e06f9c`):\n- A.\n- B.\n\nOpen (asked the user):\n- C.\n"
        self.assertEqual(review_counts(review(body)), (2, 1))

    def test_label_forms(self):
        body = ("### Fixed\n- A.\n**Fixed** (commit abc)\n- B.\n**Open questions**\n- C.\n"
                "- Open: none\nWhere to look\n- D.\nOpen: none. Not reviewed again.\n")
        self.assertEqual(review_counts(review(body)), (2, 1))

    def test_continuation_line_does_not_switch_label(self):
        body = "**Fixed**\n\n- A, which left one\n  open item.\n- B.\n  Fixed in 0aa0932.\n\n**Open**\n\n- C.\n"
        self.assertEqual(review_counts(review(body)), (2, 1))

    def test_nested_details_do_not_count(self):
        body = "**Open**\n\n- A.\n  - detail\n  - detail\n- B.\n"
        self.assertEqual(review_counts(review(body)), (0, 2))


if __name__ == "__main__":
    unittest.main()
