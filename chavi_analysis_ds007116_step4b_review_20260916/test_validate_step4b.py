#!/usr/bin/env python3
"""Focused independent Step 4B-R validation tests."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("validate_step4b.py")
SPEC = importlib.util.spec_from_file_location("validate_step4b", MODULE_PATH)
assert SPEC and SPEC.loader
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class IndependentStep4BTests(unittest.TestCase):
    def test_independent_icc_fixtures(self) -> None:
        self.assertAlmostEqual(review.icc_abs([1, 2, 3], [2, 3, 4]), 2 / 3, places=12)
        self.assertAlmostEqual(review.icc_consistency([1, 2, 3], [2, 3, 4]), 1.0, places=12)
        self.assertAlmostEqual(review.icc_abs([1, 2, 3], [1, 2, 3]), 1.0, places=12)
        self.assertIsNone(review.icc_abs([5, 5, 5], [5, 5, 5]))
        self.assertAlmostEqual(review.icc_abs([1, 2, 3], [3, 2, 1]), -3.0, places=12)

    def test_tie_aware_spearman(self) -> None:
        self.assertEqual(review.ranks([1, 1, 2]), [1.5, 1.5, 3.0])
        self.assertAlmostEqual(review.corr(review.ranks([1, 1, 2]), review.ranks([3, 3, 4])), 1.0, places=12)

    def test_participant_partition_and_one_pair_per_task(self) -> None:
        context = review.load_context()
        for task in review.TASKS:
            result = review.reconstruct(task, context)
            self.assertEqual(len(result["accounting"]), len(result["grouped"]))
            self.assertEqual(len(result["pairs"]) + len(result["exclusions"]), len(result["grouped"]))
            self.assertEqual(len({row["participant_id"] for row in result["pairs"]}), len(result["pairs"]))
            self.assertEqual(len(result["grouped"]), 131)

    def test_raw_to_independent_pair_reconstruction(self) -> None:
        context = review.load_context()
        independent = [pair for task in review.TASKS for pair in review.reconstruct(task, context)["pairs"]]
        stored = review.read_csv(review.STEP4B / "five_task_pair_manifest.csv")
        comparison = review.compare_pairs(independent, stored)
        self.assertTrue(comparison)
        self.assertTrue(all(row["status"] == "pass" for row in comparison))

    def test_cross_task_intersection_and_session_alignment(self) -> None:
        overlap = review.read_csv(review.OUT / "five_task_cross_task_overlap.csv")
        summary = next(row for row in overlap if row["participant_id"] == "__SUMMARY__")
        self.assertEqual(summary["eligible_pair_count"], "53")
        alignment = review.read_csv(review.OUT / "cross_task_session_alignment.csv")
        self.assertTrue(any(row["alignment_status"] == "mismatched_or_incomplete" for row in alignment))
        self.assertEqual(sum(row["alignment_status"] == "aligned_all_five" for row in alignment), 50)

    def test_stored_bootstrap_percentiles_and_determinism(self) -> None:
        validation = review.read_csv(review.OUT / "bootstrap_validation.csv")
        self.assertEqual(len(validation), 25)
        self.assertTrue(all(row["status"] == "pass" for row in validation))
        pairs = review.reconstruct(review.TASKS[1], review.load_context())["pairs"][:4]
        first = review.independent_bootstrap(pairs)
        second = review.independent_bootstrap(pairs)
        self.assertEqual(first, second)

    def test_plot_metadata_and_reference_line_checks(self) -> None:
        checks = review.read_csv(review.OUT / "plot_validation_checks.csv")
        self.assertEqual(len(checks), 20)
        self.assertTrue(all(row["status"] == "pass" for row in checks if row["file"].endswith(".svg")))
        self.assertEqual(sum(row["status"] == "fail" for row in checks), 5)
        self.assertTrue((review.OUT / "reviewed_face_memory_bland_altman.png").is_file())
        self.assertIn("cnb_cpf_cr", (review.OUT / "reviewed_face_memory_bland_altman.png").read_bytes().decode("latin-1", "ignore"))

    def test_before_after_hash_integrity(self) -> None:
        provenance = review.read_json(review.OUT / "step4b_review_provenance.json")
        self.assertEqual(provenance["dataset_git_before"], provenance["dataset_git_after"])
        self.assertTrue(provenance["earlier_output_hashes_unchanged"])
        self.assertEqual(provenance["step4b_output_hashes_before"], provenance["step4b_output_hashes_after"])
        self.assertEqual(provenance["step4a_and_step4a_r_output_hashes_before"], provenance["step4a_and_step4a_r_output_hashes_after"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
