#!/usr/bin/env python3
"""Focused Step 4A synthetic tests; no project data are modified."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("step4a_face_memory.py")
SPEC = importlib.util.spec_from_file_location("step4a_face_memory", MODULE_PATH)
assert SPEC and SPEC.loader
step4a = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(step4a)


class Step4ATests(unittest.TestCase):
    def test_finite_and_nonfinite_values(self) -> None:
        self.assertEqual(step4a.parse_finite("3.5"), (3.5, "finite"))
        self.assertEqual(step4a.parse_finite("NaN")[1], "nonfinite")
        self.assertEqual(step4a.parse_finite("inf")[1], "nonfinite")
        self.assertEqual(step4a.parse_finite("-inf")[1], "nonfinite")
        self.assertEqual(step4a.parse_finite("n/a")[1], "missing")

    def test_duplicate_analytical_key_is_not_silently_deduplicated(self) -> None:
        observation = {
            "participant_id": "sub-test",
            "session_id": "ses-1",
            "session_number": 1,
            "score": 10.0,
            "score_raw": "10",
            "score_status": "finite",
            "qc_raw_code": "V",
            "qc_status": "documented_valid",
            "qc_meaning": "Valid",
            "eligible_step4a": True,
            "eligibility_reason_step4a": "V",
            "source_row_reference": "synthetic#1",
            "source_row_number": 1,
            "occasion": {},
            "continuation": False,
        }
        with self.assertRaises(step4a.Step4AError):
            step4a.candidate_accounting([observation, {**observation, "source_row_reference": "synthetic#2", "source_row_number": 2}])

    def test_qc_states_are_distinct(self) -> None:
        self.assertEqual(step4a.qc_class("V")[0], "documented_valid")
        self.assertEqual(step4a.qc_class("F")[0], "documented_likely_valid")
        self.assertEqual(step4a.qc_class("N")[0], "documented_invalid")
        self.assertEqual(step4a.qc_class("n/a")[0], "missing_qc")
        self.assertEqual(step4a.qc_class("VC")[0], "unknown_or_undocumented")

    def test_malformed_decision_register_fails_strictly(self) -> None:
        fields = ["category", "decision_id", "status", "decision_or_unresolved_issue", "scope", "implemented_evidence", "proposed_minimal_option", "tradeoff", "analysis_blocked"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "malformed.csv"
            path.write_text(",".join(fields) + "\n" + "a,b,settled,\"unterminated,b,c,d,e,f\n", encoding="utf-8")
            with self.assertRaises(step4a.Step4AError):
                step4a.strict_decision_register(path)

    def test_actual_decision_register_repair_is_explicit_and_in_memory(self) -> None:
        rows, repair = step4a.strict_decision_register_with_explicit_repair(step4a.STEP3B_DECISIONS)
        self.assertEqual(repair["status"], "repaired_in_memory_after_strict_failure")
        self.assertEqual(len(rows), 25)
        self.assertEqual(repair["repaired_line_numbers"], list(range(6, 27)))

    def test_ambiguous_chronology_is_explicit(self) -> None:
        first = {"occasion": {"rounded_acq_time": "1800-01-01T12:00:00"}}
        second = {"occasion": {"rounded_acq_time": "1800-01-01T12:00:00"}}
        result = step4a.interval_info(first, second)
        self.assertEqual(result["interval_status"], "ambiguous_nonpositive_rounded_timestamp")
        self.assertEqual(result["interval_days"], "")

    def test_continuation_cannot_be_eligible(self) -> None:
        inputs = {"raw_rows": [{"participant_id": "sub-test", "session_id": "ses-2", "cnb_cpf_cr": "20", "cnb_cpf_valid_code": "V"}], "occasion_map": {("sub-test", "ses-2"): {"comparability_status": "documented continuation; no separate CNB occasion", "proposed_cognitive_occasion_id": "continuation"}}}
        observations = step4a.build_observations(inputs)
        self.assertFalse(observations[0]["eligible_step4a"])
        self.assertEqual(observations[0]["eligibility_reason_step4a"], "continuation_session_not_new_CNB_occasion")

    def test_known_icc_examples(self) -> None:
        absolute, absolute_status = step4a.icc_absolute_agreement([1.0, 2.0, 3.0], [2.0, 3.0, 4.0])
        consistency, consistency_status = step4a.icc_consistency([1.0, 2.0, 3.0], [2.0, 3.0, 4.0])
        self.assertEqual(absolute_status, "ok")
        self.assertEqual(consistency_status, "ok")
        self.assertAlmostEqual(absolute, 2.0 / 3.0, places=12)
        self.assertAlmostEqual(consistency, 1.0, places=12)

    def test_constant_score_is_undefined(self) -> None:
        estimate, status = step4a.icc_absolute_agreement([5.0, 5.0, 5.0], [5.0, 5.0, 5.0])
        self.assertIsNone(estimate)
        self.assertEqual(status, "undefined_zero_or_nonfinite_denominator")
        self.assertIsNone(step4a.pearson([5.0, 5.0], [5.0, 5.0]))

    def test_bootstrap_keeps_repeated_sampled_participants_as_copies(self) -> None:
        pairs = [
            {"participant_id": "sub-a", "earlier_score": "1", "later_score": "2", "pair_mean": "1.5", "paired_difference_later_minus_earlier": "1"},
            {"participant_id": "sub-b", "earlier_score": "2", "later_score": "3", "pair_mean": "2.5", "paired_difference_later_minus_earlier": "1"},
        ]
        rows, summary = step4a.bootstrap(pairs)
        self.assertEqual(len(rows), step4a.BOOTSTRAP_REPLICATES)
        self.assertTrue(any(int(row["duplicate_sampled_participant_copies"]) > 0 for row in rows))
        self.assertEqual(summary["mean_difference"]["successful_replicates"], step4a.BOOTSTRAP_REPLICATES)

    def test_figures_reproduce_from_included_pair_table(self) -> None:
        included_path = step4a.OUT / "face_memory_included_pairs.csv"
        rows = step4a.read_csv_strict(included_path)
        self.assertEqual(len(rows), 59)
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            step4a.write_scatter_plots(rows, directory_path / "scatter.png", directory_path / "scatter.svg")
            step4a.write_difference_plot(rows, directory_path / "difference.png", directory_path / "difference.svg", {})
            for name in ("scatter.png", "scatter.svg", "difference.png", "difference.svg"):
                self.assertGreater((directory_path / name).stat().st_size, 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
