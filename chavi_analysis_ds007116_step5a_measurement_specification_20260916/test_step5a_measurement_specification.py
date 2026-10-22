import csv
import json
import unittest
from pathlib import Path


OUT = Path(__file__).resolve().parent
ROOT = OUT.parent


def rows(name):
    with (OUT / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


class Step5ATests(unittest.TestCase):
    def test_complete_session_construction_and_qc(self):
        data = rows("synchronized_profile_occasions.csv")
        complete = [r for r in data if r["synchronized_occasion_status"] == "complete_synchronized_vf"]
        self.assertEqual(len(complete), 176)
        self.assertTrue(all(r["all_five_source_records"] == "yes" for r in complete))
        self.assertTrue(all(r["all_five_finite"] == "yes" for r in complete))
        self.assertTrue(all(r["exact_vf_qc_eligible"] == "yes" for r in complete))

    def test_continuation_is_not_a_new_occasion(self):
        data = rows("synchronized_profile_occasions.csv")
        r = next(x for x in data if x["participant_id"] == "sub-20812" and x["repository_session_id"] == "ses-2")
        self.assertEqual(r["synchronized_occasion_status"], "excluded_continuation")
        self.assertEqual(r["continuation_excluded"], "yes")

    def test_duplicate_source_keys_were_rejected_by_preparation(self):
        source = rows("synchronized_profile_occasions.csv")
        keys = [(r["participant_id"], r["repository_session_id"]) for r in source]
        self.assertEqual(len(keys), len(set(keys)))
        pair = rows("synchronized_profile_pair_candidates.csv")
        self.assertEqual(len(pair), len({r["participant_id"] for r in pair}))

    def test_two_jointly_complete_occasion_selection(self):
        pair = rows("synchronized_profile_pair_candidates.csv")
        self.assertEqual(len(pair), 52)
        self.assertTrue(all(r["pair_rule"] == "first_two_jointly_complete_synchronized_vf_occasions" for r in pair))
        self.assertTrue(all(int(r["earlier_session_id"].split("-")[1]) < int(r["later_session_id"].split("-")[1]) for r in pair))

    def test_task_misalignment_and_50_52_53_reconcile(self):
        rec = {r["denominator_id"]: int(r["count"]) for r in rows("cohort_count_reconciliation.csv")}
        self.assertEqual((rec["task_pair_same_session_alignment"], rec["profile_first_synchronized_primary_candidate"], rec["task_pair_intersection"]), (50, 52, 53))
        review = rows("discrepant_participant_review.csv")
        ids = {r["participant_id"] for r in review}
        self.assertTrue({"sub-20259", "sub-20494", "sub-21035"}.issubset(ids))
        self.assertEqual(next(r for r in review if r["participant_id"] == "sub-21035")["profile_first_decision"], "excluded")
        self.assertEqual(next(r for r in review if r["participant_id"] == "sub-20259")["profile_first_decision"], "included")

    def test_registered_denominator_is_132(self):
        flow = {r["stage"]: int(r["n"]) for r in rows("profile_cohort_flow.csv")}
        self.assertEqual(flow["registered participants"], 132)
        self.assertEqual(flow["Step 5A primary candidate pair denominator"], 52)

    def test_score_direction_documentation_is_traceable(self):
        data = rows("score_semantics_and_direction.csv")
        self.assertEqual({r["task_key"] for r in data}, {"letter_nback", "face_memory", "matrix_reasoning", "emotion_recognition", "dominant_finger_tapping"})
        self.assertTrue(all(r["official_source_url"].startswith("https://webcnp.med.upenn.edu/") for r in data))
        self.assertTrue(all(r["description"] for r in data))
        self.assertIn("faster motor performance", next(r for r in data if r["task_key"] == "dominant_finger_tapping")["higher_score_meaning"])

    def test_no_standardized_or_profile_score_is_emitted(self):
        forbidden = ("standardized", "z_score", "centered_score", "composite_score", "profile_score", "elevation", "shape", "scatter")
        for name in ("synchronized_profile_occasions.csv", "synchronized_profile_pair_candidates.csv", "profile_pair_source_trace.csv"):
            with (OUT / name).open(encoding="utf-8") as f:
                header = next(csv.reader(f))
            self.assertFalse(any(any(token in field.lower() for token in forbidden) for field in header), (name, header))
        data = rows("synchronized_profile_pair_candidates.csv")
        self.assertTrue(all(r["pair_status"].startswith("candidate_for_phase2") for r in data))

    def test_hashes_and_prior_inputs_are_stable(self):
        p = json.loads((OUT / "step5a_provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(p["dataset"]["commit"], "fc7dc36fa2598b0b2e4579baef37d148cc085207")
        self.assertEqual(p["dataset"]["before_hashes"], p["dataset"]["after_hashes"])
        self.assertEqual(p["previous_input_output_hashes_before"], p["previous_input_output_hashes_after"])
        self.assertTrue(p["output_hashes"])

    def test_open_decisions_block_step5b(self):
        data = rows("decision_register_step5a.csv")
        self.assertTrue(any(r["status"] == "open" and r["blocks_implementation"] == "yes" for r in data))
        self.assertIn("not started", (OUT / "step5a_review_report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
