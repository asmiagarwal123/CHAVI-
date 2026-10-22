import csv
import hashlib
import json
import unittest
from pathlib import Path


OUT = Path(__file__).resolve().parent
ROOT = OUT.parent


def rows(name):
    with (OUT / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class PreflightArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = json.loads((OUT / "preflight_results.json").read_text(encoding="utf-8"))
        cls.ref = rows("reference_cohort_manifest.csv")
        cls.recon = rows("source_cohort_reconciliation.csv")
        cls.folds = rows("participant_fold_manifest.csv")

    def test_source_counts(self):
        self.assertEqual(self.results["source_integrity"]["task_rows"], 1095)
        self.assertEqual(self.results["source_integrity"]["duplicate_keys"], [])
        self.assertEqual(self.results["source_integrity"]["eligible_flag_mismatches"], [])

    def test_reference_identity_and_rows(self):
        self.assertEqual(len({r["participant_id"] for r in self.ref}), 109)
        self.assertEqual(len(self.ref), 545)
        self.assertTrue(all(sum(x["participant_id"] == p for x in self.ref) == 5 for p in {r["participant_id"] for r in self.ref}))

    def test_reference_unique_keys(self):
        keys = {(r["participant_id"], r["reference_session_id"], r["task_key"]) for r in self.ref}
        self.assertEqual(len(keys), 545)

    def test_primary_and_vonly_identities(self):
        self.assertEqual(sum(r["primary_vf"] == "yes" for r in self.recon), 52)
        self.assertEqual(sum(r["vonly_sensitivity"] == "yes" for r in self.recon), 45)

    def test_50_52_53_reconciliation(self):
        self.assertEqual(sum(r["all_five_task_pair_intersection"] == "yes" for r in self.recon), 53)
        self.assertEqual(sum(r["all_five_task_pairs_aligned"] == "yes" for r in self.recon), 50)
        self.assertEqual(self.results["cohorts"]["profile_not_aligned_50"], ["sub-20259", "sub-20494"])
        self.assertEqual(self.results["cohorts"]["task_intersection_not_profile_52"], ["sub-21035"])

    def test_fold_counts_and_no_leakage(self):
        for fold in range(5):
            members = [r for r in self.folds if int(r["held_out_fold"]) == fold]
            self.assertEqual(len(members), 22 if fold < 4 else 21)
            held = set(members[0]["held_out_identity_list"].split(";"))
            train = set(members[0]["training_identity_list"].split(";"))
            self.assertFalse(held & train)
            self.assertEqual(len(train), 87 if fold < 4 else 88)

    def test_fold_hash_definition(self):
        first = self.folds[0]
        values = first["held_out_identity_list"].split(";")
        observed = hashlib.sha256(("\n".join(values) + "\n").encode("utf-8")).hexdigest()
        self.assertEqual(observed, first["held_out_identities_sha256"])

    def test_all_analysis_participants_map_to_reference(self):
        self.assertTrue(self.results["candidate_folds"]["all_primary_map_to_reference_a"])
        self.assertTrue(self.results["candidate_folds"]["all_vonly_map_to_reference_a"])

    def test_fold_conflict_is_not_hidden(self):
        self.assertFalse(self.results["candidate_folds"]["matches_recovery_phase1_expected_identity_lists"])
        comparison = rows("fold_algorithm_comparison.csv")
        self.assertTrue(all(r["seed42_matches_recovery"] == "no" for r in comparison))
        self.assertTrue(all(r["sorted_round_robin_matches_recovery"] == "yes" for r in comparison))

    def test_no_transformation_outputs_created(self):
        names = {p.name for p in OUT.iterdir() if p.is_file()}
        self.assertNotIn("transformation_parameters.csv", names)
        self.assertNotIn("transformed_task_observations_long.csv", names)
        self.assertNotIn("transformed_profiles_wide.csv", names)


if __name__ == "__main__":
    unittest.main(verbosity=2)
