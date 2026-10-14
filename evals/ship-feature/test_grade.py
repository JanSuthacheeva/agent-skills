import json, tempfile, unittest
from pathlib import Path

from grade import flow_check, flow_reports, review_counts

PLAN_DONE = "## Review\n\n**Fixed**\n\n- A.\n\n**Open**\n\n- None.\n"
PLAN_OPEN = "## Review\n\n**Fixed**\n\n- A.\n\n**Open**\n\n- B.\n"
FINAL_STOP = "Reported the final stop"


def reports(*calls) -> list[list[str]]:
    with tempfile.TemporaryDirectory() as tmp:
        fx = Path(tmp)
        (fx / "flow.jsonl").write_text("".join(json.dumps(c) + "\n" for c in calls))
        got = flow_reports(fx)
        assert got is not None
        return got


class FlowReportsTest(unittest.TestCase):
    def test_reads_each_call_as_its_argv_without_report(self):
        got = reports(["report", "phase", "review"], ["report", "waiting", "Push and open the merge request?"])
        self.assertEqual(got, [["phase", "review"], ["waiting", "Push and open the merge request?"]])

    def test_none_without_a_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(flow_reports(Path(tmp)))

    def test_old_text_log_fails_naming_the_file_and_the_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp) / "flow.log"
            old.write_text("report phase review\n")
            with self.assertRaises(ValueError) as err:
                flow_reports(Path(tmp))
            self.assertIn(str(old), str(err.exception))
            self.assertIn("flow.jsonl", str(err.exception))
            self.assertIn("JSON array", str(err.exception))


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


PHASES_MID = "Reported the phases implement and review, then merge-request only after a review with nothing open"
PHASES_AFTER = "Reported the phase review, then merge-request only after a review with nothing open"
COUNTS = "Reported the review counts of the plan's ## Review"
TASKS = "Reported tasks 5 5"


class PhasesTest(unittest.TestCase):
    def test_repeated_phases_fold_across_other_reports(self):
        got = reports(["report", "phase", "implement"], ["report", "phase", "implement"], ["report", "tasks", "5", "5"],
                      ["report", "phase", "review"], ["report", "review", "--fixed", "1", "--open", "0"],
                      ["report", "phase", "review"], ["report", "phase", "merge-request"])
        self.assertTrue(flow_check(PHASES_MID, got, PLAN_DONE)[0])

    def test_merge_request_after_open_items_fails(self):
        got = reports(["report", "phase", "review"], ["report", "phase", "merge-request"])
        self.assertFalse(flow_check(PHASES_AFTER, got, PLAN_OPEN)[0])
        self.assertTrue(flow_check(PHASES_AFTER, got[:1], PLAN_OPEN)[0])

    def test_missing_merge_request_after_nothing_open_fails(self):
        got = reports(["report", "phase", "review"])
        self.assertFalse(flow_check(PHASES_AFTER, got, PLAN_DONE)[0])

    def test_phases_out_of_order_fail(self):
        got = reports(["report", "phase", "review"], ["report", "phase", "implement"], ["report", "phase", "review"])
        self.assertFalse(flow_check(PHASES_MID, got, PLAN_OPEN)[0])


class TasksAndCountsTest(unittest.TestCase):
    def test_tasks_need_the_last_count(self):
        self.assertTrue(flow_check(TASKS, reports(["report", "tasks", "4", "5"], ["report", "tasks", "5", "5"]), PLAN_DONE)[0])
        self.assertFalse(flow_check(TASKS, reports(["report", "tasks", "4", "5"]), PLAN_DONE)[0])

    def test_last_review_report_must_match_the_plan(self):
        match = reports(["report", "review", "--fixed", "0", "--open", "0"], ["report", "review", "--fixed", "1", "--open", "1"])
        self.assertTrue(flow_check(COUNTS, match, PLAN_OPEN)[0])
        self.assertFalse(flow_check(COUNTS, match[:1], PLAN_OPEN)[0])
        self.assertFalse(flow_check(COUNTS, [], PLAN_OPEN)[0])

    def test_unknown_expectation_raises(self):
        with self.assertRaises(ValueError):
            flow_check("Reported something else", [], PLAN_DONE)


def review(body):
    return f"# Plan\n\n## Review\n\n{body}\n## Next\n\n- [ ] Not a finding\n"


class ReviewCountsTest(unittest.TestCase):
    def test_finding_shaped_like_a_label_is_a_finding(self):
        body = "**Fixed**\n\n- Fixed duplicate tags: deduped in store.\n- **Fixed exit code**: now 2.\n- Open list --tag: rejected.\n\n**Open**\n\n- One.\n"
        self.assertEqual(review_counts(review(body)), (3, 1))

    def test_none_is_no_finding(self):
        body = "Fixed:\n\n- A.\n\nOpen:\n\n- None.\n\nWhere to look:\n\n1. grade.py\n"
        self.assertEqual(review_counts(review(body)), (1, 0))

    def test_every_form_saying_there_is_nothing_is_no_finding(self):
        forms = ["None.", "nothing", "N/A", "None (all fixed)", "None from this branch.",
                 "None identified", "None found.", "None left", "None open.", "None remaining",
                 "Nothing to report.", "Nothing open.", "Nothing left", "Nothing remaining.",
                 "Nothing to fix.", "Nothing needed fixing.",
                 "No items.", "No findings", "No questions.", "No issues.", "No open items.",
                 "No open questions remain.", "No findings left.", "No issues remaining",
                 "No items open.", "No open findings."]
        body = "**Open**\n\n" + "".join(f"- {f}\n" for f in forms) + "\nOpen: no open items.\n"
        self.assertEqual(review_counts(review(body)), (0, 0))

    def test_only_the_first_sentence_is_judged(self):
        body = ("**Open**\n\n- None. The fixes were not reviewed independently.\n"
                "- None from this branch. Pre-existing on `main`: a corrupt store throws.\n"
                "\nOpen: none. Not reviewed again.\n")
        self.assertEqual(review_counts(review(body)), (0, 0))

    def test_items_naming_a_missing_thing_are_findings(self):
        body = "**Open**\n\n- No test for `list --tag`.\n- No items cap on `tag`, so a bookmark can hold any number.\n"
        self.assertEqual(review_counts(review(body)), (0, 2))

    def test_items_starting_with_none_or_nothing_that_name_a_thing_are_findings(self):
        body = ("**Open**\n\n- Nothing validates the tag length, so a 10 kB tag is stored.\n"
                "- None of the error paths in `tag` are tested.\n- Nothing checks the store's version.\n"
                "- Nothing in tag checks the length.\n")
        self.assertEqual(review_counts(review(body)), (0, 4))

    def test_forms_outside_the_list_are_findings(self):
        body = ("**Open**\n\n- None - all fixed.\n- Nothing open, see Fixed.\n- No issues found.\n"
                "- None \u2014 all fixed\n- Nothing blocking\n- Nothing remains open.\n")
        self.assertEqual(review_counts(review(body)), (0, 6))

    def test_text_after_a_label_colon_is_one_finding(self):
        body = "**Fixed**\n\n- A.\n\nOpen: nothing validates X\n"
        self.assertEqual(review_counts(review(body)), (1, 1))

    def test_text_after_a_bold_label_colon_is_one_finding(self):
        body = "**Fixed:** A was fixed.\n**Open**: B is open.\n**Open:** none\n"
        self.assertEqual(review_counts(review(body)), (1, 1))

    def test_bold_label_followed_by_a_dash_ignores_the_text(self):
        body = "**Fixed** - all of it\n\n- A.\n\n**Open** - none\n"
        self.assertEqual(review_counts(review(body)), (1, 0))

    def test_labels_with_a_note_before_the_colon(self):
        body = "Fixed (`0e06f9c`):\n- A.\n- B.\n\nOpen (asked the user):\n- C.\n"
        self.assertEqual(review_counts(review(body)), (2, 1))

    def test_label_forms(self):
        body = ("### Fixed\n- A.\n**Fixed** (commit abc)\n- B.\n**Open questions**\n- C.\n"
                "- Open: none\nWhere to look\n- D.\nOpen: none. Not reviewed again.\n")
        self.assertEqual(review_counts(review(body)), (2, 1))

    def test_bold_labels_with_the_colon_inside(self):
        body = "**Fixed:**\n\n- A.\n- B.\n\n**Open:**\n\n- C.\n"
        self.assertEqual(review_counts(review(body)), (2, 1))

    def test_bold_list_label_saying_none(self):
        body = "- **Fixed:**\n  - A.\n- **Open:** none\n"
        self.assertEqual(review_counts(review(body)), (1, 0))

    def test_continuation_line_does_not_switch_label(self):
        body = "**Fixed**\n\n- A, which left one\n  open item.\n- B.\n  Fixed in 0aa0932.\n\n**Open**\n\n- C.\n"
        self.assertEqual(review_counts(review(body)), (2, 1))

    def test_nested_details_do_not_count(self):
        body = "**Open**\n\n- A.\n  - detail\n  - detail\n- B.\n"
        self.assertEqual(review_counts(review(body)), (0, 2))


if __name__ == "__main__":
    unittest.main()
