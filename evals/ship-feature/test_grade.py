import json, tempfile, unittest
from pathlib import Path

from grade import flow_check, flow_reports

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


if __name__ == "__main__":
    unittest.main()
