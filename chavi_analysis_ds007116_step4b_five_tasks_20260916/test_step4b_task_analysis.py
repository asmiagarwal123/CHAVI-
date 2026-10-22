#!/usr/bin/env python3
"""Focused Step 4B unit, statistical, regression, and integrity tests."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).with_name("run_step4b_task_analysis.py")
SPEC = importlib.util.spec_from_file_location("step4b", MODULE_PATH)
assert SPEC and SPEC.loader
step4b = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(step4b)


TASK = step4b.TASKS[1]


def observation(participant: str, session: str, score: float | None, qc_status: str = "documented_valid", row_number: int = 1, reason: str = "V") -> dict:
    score_status = "finite" if score is not None else "missing"
    return {"task_key": TASK["task_key"], "task_label": TASK["label"], "task_stem": TASK["stem"], "score_field": TASK["score_field"], "qc_field": TASK["qc_field"], "participant_id": participant, "session_id": session, "session_number": step4b.session_number(session), "score_raw": "" if score is None else str(score), "score": score, "score_status": score_status, "qc_raw_code": "V" if qc_status == "documented_valid" else "N", "qc_status": qc_status, "qc_meaning": "Valid", "eligible": score_status == "finite" and qc_status in {"documented_valid", "documented_likely_valid"}, "eligibility_reason": reason, "source_row_reference": f"phenotype/{TASK['filename']}#data-row-{row_number}", "source_row_number": row_number, "occasion": {"session_age": "16", "rounded_acq_time": "1800-01-01T12:00:00" if session == "ses-1" else "1801-01-01T12:00:00"}, "continuation": False}


class Step4BTests(unittest.TestCase):
    def test_icc_formula_known_fixture(self) -> None:
        absolute, status_a = step4b.icc_absolute_agreement([1.0, 2.0, 3.0], [2.0, 3.0, 4.0])
        consistency, status_c = step4b.icc_consistency([1.0, 2.0, 3.0], [2.0, 3.0, 4.0])
        self.assertEqual((status_a, status_c), ("ok", "ok"))
        self.assertAlmostEqual(absolute, 2 / 3, places=12)
        self.assertAlmostEqual(consistency, 1.0, places=12)

    def test_bootstrap_is_deterministic_and_participant_level(self) -> None:
        pairs = [{"participant_id": f"sub-{i}", "earlier_score": str(i), "later_score": str(i + 1), "pair_mean": str(i + .5), "paired_difference_later_minus_earlier": "1"} for i in range(1, 6)]
        first_rows, first_summary = step4b.bootstrap(pairs, seed=123)
        second_rows, second_summary = step4b.bootstrap(pairs, seed=123)
        self.assertEqual(first_rows, second_rows)
        self.assertEqual(first_summary, second_summary)
        self.assertTrue(any(int(row["duplicate_sampled_participant_copies"]) > 0 for row in first_rows))
        self.assertEqual(first_summary["mean_difference"]["successful_replicates"], step4b.BOOTSTRAP_REPLICATES)

    def test_missing_earlier_and_later_are_counted_before_filtering(self) -> None:
        rows = [observation("sub-a", "ses-1", None, row_number=1), observation("sub-a", "ses-2", 4, row_number=2), observation("sub-b", "ses-1", 2, row_number=3), observation("sub-b", "ses-2", None, row_number=4)]
        accounting, pairs, exclusions, _ = step4b.candidate_accounting(TASK, rows)
        self.assertEqual(len(pairs), 0)
        self.assertEqual(sum(row["candidate_earlier_score_missing"] == "yes" for row in accounting), 1)
        self.assertEqual(sum(row["candidate_later_score_missing"] == "yes" for row in accounting), 1)
        self.assertEqual(len(exclusions), 2)

    def test_exact_v_f_inclusion_and_invalidity_overrides_missing(self) -> None:
        rows = [observation("sub-good", "ses-1", 1, "documented_valid", 1), observation("sub-good", "ses-2", 2, "documented_likely_valid", 2), observation("sub-bad", "ses-1", None, "documented_invalid", 3, "documented_invalid"), observation("sub-bad", "ses-2", 2, "documented_valid", 4)]
        accounting, pairs, exclusions, _ = step4b.candidate_accounting(TASK, rows)
        self.assertEqual([row["participant_id"] for row in pairs], ["sub-good"])
        self.assertEqual(exclusions[0]["inclusion_or_exclusion_reason"], "QC_not_documented_valid_or_likely_valid")
        self.assertIn("documented_invalid", exclusions[0]["exclusion_detail"])

    def test_one_primary_pair_and_visit_order(self) -> None:
        rows = [observation("sub-a", "ses-2", 5, row_number=2), observation("sub-a", "ses-1", 3, row_number=1), observation("sub-a", "ses-3", 7, row_number=3)]
        _, pairs, _, _ = step4b.candidate_accounting(TASK, rows)
        self.assertEqual(len(pairs), 1)
        self.assertEqual((pairs[0]["earlier_session_id"], pairs[0]["later_session_id"]), ("ses-1", "ses-2"))

    def test_nonpositive_interval_is_rejected(self) -> None:
        with self.assertRaises(step4b.Step4BError):
            step4b.require_positive_session_interval(2, 1)
        with self.assertRaises(step4b.Step4BError):
            step4b.require_positive_session_interval(1, 1)

    def test_duplicate_analytical_key_is_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            path = stage / TASK["filename"]
            path.write_text("participant_id\tsession_id\tcnb_cpf_valid_code\tcnb_cpf_cr\nsub-a\tses-1\tV\t1\nsub-a\tses-1\tV\t2\n", encoding="utf-8")
            inputs = {"occasion_map": {("sub-a", "ses-1"): {}} , "step3b_rows": [{"source_row_reference": f"phenotype/{TASK['filename']}#data-row-1"}, {"source_row_reference": f"phenotype/{TASK['filename']}#data-row-2"}]}
            with patch.object(step4b, "STAGE", stage):
                with self.assertRaises(step4b.Step4BError):
                    step4b.build_observations(TASK, inputs)

    def test_face_memory_regression_and_output_pair_manifest(self) -> None:
        rows = step4b.read_csv_strict(step4b.OUT / "face_memory_reproduction_check.csv")
        self.assertTrue(rows)
        self.assertTrue(all(row["within_tolerance"] == "yes" for row in rows))
        pairs = step4b.read_csv_strict(step4b.OUT / "five_task_pair_manifest.csv")
        face = [row for row in pairs if row["task_key"] == "face_memory"]
        self.assertEqual(len(face), 59)

    def test_plot_file_generation(self) -> None:
        pairs = step4b.read_csv_strict(step4b.OUT / "five_task_pair_manifest.csv")
        pairs = [row for row in pairs if row["task_key"] == "face_memory"]
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            step4b.write_scatter_plots(TASK, pairs, target / "scatter.png", target / "scatter.svg")
            step4b.write_difference_plot(TASK, pairs, target / "ba.png", target / "ba.svg")
            for name in ("scatter.png", "scatter.svg", "ba.png", "ba.svg"):
                self.assertGreater((target / name).stat().st_size, 100)
            self.assertIn("identity", (target / "scatter.svg").read_text(encoding="utf-8").lower())
            self.assertIn("zero", (target / "ba.svg").read_text(encoding="utf-8").lower())

    def test_dataset_and_previous_output_hashes_unchanged(self) -> None:
        provenance = step4b.read_json(step4b.OUT / "step4b_provenance.json")
        self.assertEqual(provenance["git_before"], provenance["git_after"])
        self.assertEqual(provenance["dataset_input_hashes_before"], provenance["dataset_input_hashes_after"])
        self.assertEqual(provenance["prior_output_hashes_before"], provenance["prior_output_hashes_after"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
