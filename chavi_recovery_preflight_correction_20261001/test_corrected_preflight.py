import csv
import json
import math
import unittest
from pathlib import Path

import reconstruct_and_audit as audit


OUT = Path(__file__).resolve().parent


def rows(name):
    with (OUT / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class CorruptedFixtureTests(unittest.TestCase):
    """Every test uses a deliberately bad fixture and must catch the named failure."""

    def test_raw_valid_rejected_by_bad_upstream_flag_is_detected(self):
        fixture = [{"participant_id":"p1","repository_session_id":"s1","task_key":"t","parsed_numeric_value":"1","raw_qc_codes":"V","eligible_documented_valid_or_likely_valid":"no","eligible_strict_documented_V_only":"yes"}]
        vf, strict = audit.upstream_flag_mismatches(fixture)
        self.assertEqual(len(vf), 1); self.assertEqual(strict, [])

    def test_incorrect_strict_v_flag_is_detected(self):
        fixture = [{"participant_id":"p1","repository_session_id":"s1","task_key":"t","parsed_numeric_value":"1","raw_qc_codes":"F","eligible_documented_valid_or_likely_valid":"yes","eligible_strict_documented_V_only":"yes"}]
        vf, strict = audit.upstream_flag_mismatches(fixture)
        self.assertEqual(vf, []); self.assertEqual(len(strict), 1)

    def test_duplicate_source_key_is_rejected(self):
        fixture = [{"p":"1","s":"1","t":"1"}, {"p":"1","s":"1","t":"1"}]
        with self.assertRaisesRegex(ValueError, "duplicate_source_keys"):
            audit.ensure_unique(fixture, ("p","s","t"), "source")

    def test_duplicate_occasion_map_key_is_rejected(self):
        fixture = [{"p":"1","s":"1"}, {"p":"1","s":"1"}]
        with self.assertRaisesRegex(ValueError, "duplicate_occasion_map_keys"):
            audit.ensure_unique(fixture, ("p","s"), "occasion_map")

    def test_missing_required_mapping_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing_required_occasion_mapping"):
            audit.validate_required_mappings({("p1","s1")}, set())

    def test_correct_count_wrong_identities_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "identity_mismatch"):
            audit.validate_identity_set(["p1","p2"], ["p1","p3"])

    def test_valid_design_b_is_accepted(self):
        ref = {f"p{i}" for i in range(109)}; held = {f"p{i}" for i in range(11)}
        fitting = ref - held
        audit.validate_reference_design("Reference_A", fitting, ref)
        audit.validate_no_leakage(held, fitting)
        self.assertEqual(len(fitting), 98)

    def test_design_c_cannot_be_labelled_reference_a(self):
        ref = {f"p{i}" for i in range(109)}
        with self.assertRaisesRegex(ValueError, "design_c_incorrectly_labelled_reference_a"):
            audit.validate_reference_design("Reference_A", {f"p{i}" for i in range(41)}, ref)

    def test_held_out_identity_in_fit_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "held_out_identity_in_fitting_data"):
            audit.validate_no_leakage({"p1"}, {"p1","p2"})

    def test_nonconstant_metadata_splitting_wide_key_is_rejected(self):
        fixture = [{"id":"p1","session":"s1","age":"10"},{"id":"p1","session":"s1","age":"11"}]
        with self.assertRaisesRegex(ValueError, "nonconstant_metadata_splits_wide_key"):
            audit.validate_wide_metadata(fixture, ("id","session"), ("age",))

    def test_m0_cannot_inherit_m1_support_flag(self):
        with self.assertRaisesRegex(ValueError, "m0_inherits_m1_support_status"):
            audit.validate_support_semantics("M0", "outside_age_support")

    def test_m1_missing_age_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "m1_missing_or_nonfinite_training_age"):
            audit.validate_m1_training([10.0, math.nan])

    def test_m1_constant_age_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "m1_constant_age_rank_deficient"):
            audit.validate_m1_training([10.0, 10.0])

    def test_duplicate_bootstrap_copy_of_holdout_is_rejected(self):
        fixture = [("p1","draw-1"),("p1","draw-2"),("p2","draw-3")]
        with self.assertRaisesRegex(ValueError, "held_out_identity_copy_in_bootstrap_training"):
            audit.bootstrap_training_draws(fixture, {"p1"})

    def test_scale_exact_degeneracy_is_handled(self):
        self.assertEqual(audit.scale_status([2.0,2.0], 0.0), "exactly_degenerate")

    def test_scale_policy_is_translation_and_unit_invariant(self):
        x = [1.0, 1.0 + 1e-10]
        base = audit.scale_status(x, 1e-10)
        shifted = audit.scale_status([v + 1e6 for v in x], 1e-10)
        scaled = audit.scale_status([v * 1000 for v in x], 1e-7)
        self.assertEqual(base, shifted); self.assertEqual(base, scaled)


class FreshArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((OUT / "reconstruction_results_corrected.json").read_text(encoding="utf-8"))

    def test_consolidated_computational_gate(self):
        self.assertTrue(self.result["readiness_gate"]["computational_gate_passed"])
        self.assertEqual(self.result["readiness_gate"]["failures"], [])

    def test_required_cohort_counts(self):
        c = self.result["cohorts"]
        self.assertEqual((c["reference_a_participants"],c["reference_a_rows"]),(109,545))
        self.assertEqual((c["primary_participants"],c["primary_rows"]),(52,520))
        self.assertEqual((c["vonly_reselected_participants"],c["vonly_reselected_rows"]),(45,450))

    def test_named_pair_shifts(self):
        self.assertEqual(self.result["cohorts"]["changed_vonly_pairs"], ["sub-20149","sub-20310","sub-20902","sub-20916"])

    def test_source_rows_match_staged_payloads(self):
        self.assertEqual(self.result["source"]["staged_source_value_qc_mismatches"], [])

    def test_upstream_flags_are_comparison_only_and_match(self):
        self.assertEqual(self.result["source"]["vf_upstream_flag_mismatches"], [])
        self.assertEqual(self.result["source"]["strict_v_upstream_flag_mismatches"], [])

    def test_design_b_candidate_and_historical_map_match(self):
        self.assertTrue(self.result["crossfit"]["design_b_map_matches_historical_52_target_manifest"])
        maps = rows("crossfit_candidate_identity_maps.csv")
        b = [r for r in maps if r["candidate_design_id"] == "B_seeded_targets52_plus_aux57"]
        self.assertEqual([int(r["fitting_count"]) for r in b], [98,98,99,99,99])
        self.assertTrue(all(r["self_inclusion_count"] == "0" for r in b))

    def test_historical_artifacts_preserved(self):
        hashes = rows("historical_artifact_before_after_hashes.csv")
        self.assertEqual(len(hashes), 79)
        self.assertTrue(all(r["unchanged"] == "yes" for r in hashes))

    def test_no_production_outputs_in_correction_folder(self):
        forbidden = {"transformation_parameters.csv","transformed_task_observations_long.csv","transformed_profiles_wide.csv"}
        self.assertFalse(forbidden & {p.name for p in OUT.iterdir()})


if __name__ == "__main__":
    unittest.main(verbosity=2)
