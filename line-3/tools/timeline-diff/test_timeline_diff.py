import copy
import unittest

import timeline_diff as tool


class TimelineDiffTests(unittest.TestCase):
    A = b"2026-10-18T10:00:00Z accepted\n"
    B = b"2026-10-18T10:00:02Z completed\n"

    def pack(self, a=None, b=None, **options):
        return tool.replay.make_pack([("a.log", self.A if a is None else a),
                                      ("b.log", self.B if b is None else b)], **options)

    def compare(self, first, second, left_line=1):
        return tool.compare(first, second, "a.log", left_line, "b.log", 1)

    def test_same_evidence_changed_assumption_changes_order(self):
        result = self.compare(self.pack(), self.pack(clock_uncertainty_ms=750))
        pair = result["pair"]
        self.assertEqual(pair["before"]["relation"], "left-before-right")
        self.assertEqual(pair["after"]["relation"], "unresolved-overlap")
        self.assertEqual(pair["assessment"], "relation-changed")
        self.assertTrue(pair["same_line_evidence"])
        self.assertEqual(result["line_changes"]["counts"]["changed-interval"], 2)
        self.assertEqual(result["source_changes"], [])

    def test_changed_line_never_claims_stable_evidence(self):
        result = self.compare(self.pack(), self.pack(a=b"2026-10-18T10:00:00Z different\n"))
        self.assertEqual(result["line_changes"]["counts"]["changed-line"], 1)
        self.assertEqual(result["pair"]["assessment"], "different-or-unavailable-evidence")
        self.assertFalse(result["pair"]["same_line_evidence"])
        self.assertEqual(len(result["source_changes"]), 1)

    def test_missing_citation_is_explicit(self):
        result = self.compare(self.pack(), self.pack(a=b""))
        self.assertEqual(result["pair"]["after"]["relation"], "unavailable")
        self.assertEqual(result["pair"]["after"]["left"]["status"], "absent")
        self.assertEqual(result["line_changes"]["counts"]["removed"], 1)

    def test_physical_line_movement_is_add_remove(self):
        result = self.compare(self.pack(), self.pack(a=b"\n" + self.A))
        self.assertEqual(result["line_changes"]["counts"]["added"], 1)
        self.assertEqual(result["line_changes"]["counts"]["removed"], 1)
        self.assertEqual(result["pair"]["assessment"], "different-or-unavailable-evidence")

    def test_omission_is_visible_and_inert_source_name(self):
        before = tool.replay.make_pack([("/not/a/file", b"bad line\n"),
                                        ("b.log", self.B)], ignore_unmatched=True)
        after = tool.replay.make_pack([("/not/a/file", self.A),
                                       ("b.log", self.B)], ignore_unmatched=True)
        result = tool.compare(before, after, "/not/a/file", 1, "b.log", 1)
        self.assertEqual(result["pair"]["before"]["left"]["status"], "omitted")
        self.assertEqual(result["pair"]["before"]["relation"], "unavailable")
        self.assertEqual(result["line_changes"]["counts"]["changed-line"], 1)

    def test_tampered_pack_rejected_and_arguments_validated(self):
        first, second = self.pack(), self.pack()
        second["timeline"]["events"][0]["message"] = "forged"
        with self.assertRaises(tool.replay.ReplayError):
            self.compare(first, second)
        with self.assertRaises(tool.replay.ReplayError):
            self.compare(first, self.pack(), True)

    def test_deterministic_and_no_mutation(self):
        first, second = self.pack(), self.pack(clock_uncertainty_ms=1)
        originals = copy.deepcopy((first, second))
        self.assertEqual(self.compare(first, second), self.compare(first, second))
        self.assertEqual((first, second), originals)

    def test_detail_cap_reports_exact_count(self):
        lines = b"2026-10-18T10:00:00Z x\n" * 250
        first = self.pack(a=lines)
        second = self.pack(a=b"2026-10-18T10:00:01Z x\n" * 250)
        result = self.compare(first, second)
        changes = result["line_changes"]
        self.assertEqual(changes["total"], 250)
        self.assertEqual(len(changes["shown"]), tool.DETAIL_LIMIT)
        self.assertEqual(changes["omitted_details"], 50)


if __name__ == "__main__":
    unittest.main()
