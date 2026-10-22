# CHAVI Step 2C review report

Verified/reused 41 staged Step 1B payloads from ds007116 snapshot 1.0.6 at `fc7dc36fa2598b0b2e4579baef37d148cc085207`. Checkout status before/after remained unchanged. Configuration: `step2c_specification.json`.

## Corrections and feasibility

QC is now exact-meaning based. The fixed proxy uses identical fields across occasions. Pair counts and intervals are in `paired_profile_feasibility.csv` and `pair_manifest.csv`; reason flags and sequential reconciliation are in `exclusion_flow.csv`. Outcome denominators are in `outcome_matched_feasibility.csv`.

Selected fixed-profile rows: `[
  {
    "specification_id": "fixed_five_domain",
    "specification_type": "explicit-task-intersection",
    "profile_label": "fixed_task_based_proxy_profile",
    "scenario_id": "unfiltered_observed",
    "selected_tasks_exact": "{\"Complex cognition\": \"penn_matrix_reasoning_test:cnb_pmat_cr\", \"Episodic memory\": \"penn_face_memory_test:cnb_cpf_cr\", \"Executive control\": \"short_letter_2back:cnb_lnb_mcr\", \"Sensorimotor performance\": \"short_computerized_finger_tapping_task:cnb_ctap_dom\", \"Social cognition\": \"penn_emotion_recognition_task:cnb_er40_cr\"}",
    "eligible_occasions": 202,
    "eligible_participants_at_least_1": 123,
    "participants_2plus_eligible_occasions": 63,
    "participants_3plus_eligible_occasions": 16,
    "all_possible_unordered_pair_count": 95,
    "all_possible_pair_counts": "{\"ses-1 + ses-2\": 60, \"ses-1 + ses-3\": 18, \"ses-2 + ses-3\": 17}",
    "complete_scheduled_ses1_ses2_pairs": 60,
    "complete_scheduled_ses1_ses2_participants": 60,
    "scheduled_ses1_ses2_observation_count": 183,
    "first_two_eligible_pair_count": 63,
    "first_two_eligible_assessments_participants": 63,
    "interval_all_pairs": "{\"max_days\": 1651.9583333333333, \"median_days\": 680.375, \"min_days\": 394.2083333333333, \"missing_timing\": 0, \"n_valid_intervals\": 95, \"nonpositive_intervals\": 0, \"timestamp_caveat\": \"rounded/anonymized acquisition timestamp; not exact cognitive-assessment time\", \"unparseable_timing\": 0}",
    "interval_first_two": "{\"max_days\": 1258.0, \"median_days\": 680.375, \"min_days\": 394.2083333333333, \"missing_timing\": 0, \"n_valid_intervals\": 63, \"nonpositive_intervals\": 0, \"timestamp_caveat\": \"rounded/anonymized acquisition timestamp; not exact cognitive-assessment time\", \"unparseable_timing\": 0}",
    "interval_complete_scheduled": "{\"max_days\": 1258.0, \"median_days\": 678.1458333333333, \"min_days\": 394.2083333333333, \"missing_timing\": 0, \"n_valid_intervals\": 60, \"nonpositive_intervals\": 0, \"timestamp_caveat\": \"rounded/anonymized acquisition timestamp; not exact cognitive-assessment time\", \"unparseable_timing\": 0}",
    "nominal_interval_days_summary": "{\"max_days\": 1651.9583333333333, \"median_days\": 680.375, \"min_days\": 394.2083333333333, \"missing_timing\": 0, \"n_valid_intervals\": 95, \"nonpositive_intervals\": 0, \"timestamp_caveat\": \"rounded/anonymized acquisition timestamp; not exact cognitive-assessment time\", \"unparseable_timing\": 0}",
    "timing_limitation": "acq_time is rounded/anonymized; interval is nominal, not an exact cognitive-assessment interval",
    "missing_score_loss_from_recorded_sessions": 23,
    "qc_loss_from_unfiltered_keys": 0,
    "comparability_uncertainty_status": "uncertain: task version, administration conditions, and exact cognitive timing are not established",
    "profile_any_unresolved_component_count": 24,
    "profile_all_components_unresolved_count": 13,
    "profile_mixed_unresolved_and_explicit_invalid_count": 0,
    "sub20812_continuation_keys": 0,
    "notes": "Complete scheduled pairs require both eligible ses-1 and ses-2 observations. A pair is a participant-level first-two eligible occasion summary; overlapping pairs are not independent participants. Missing-score loss is against recorded repository sessions; QC loss is against the unfiltered profile intersection."
  },
  {
    "specification_id": "fixed_five_domain",
    "specification_type": "explicit-task-intersection",
    "profile_label": "fixed_task_based_proxy_profile",
    "scenario_id": "documented_valid_or_likely_valid",
    "selected_tasks_exact": "{\"Complex cognition\": \"penn_matrix_reasoning_test:cnb_pmat_cr\", \"Episodic memory\": \"penn_face_memory_test:cnb_cpf_cr\", \"Executive control\": \"short_letter_2back:cnb_lnb_mcr\", \"Sensorimotor performance\": \"short_computerized_finger_tapping_task:cnb_ctap_dom\", \"Social cognition\": \"penn_emotion_recognition_task:cnb_er40_cr\"}",
    "eligible_occasions": 176,
    "eligible_participants_at_least_1": 109,
    "participants_2plus_eligible_occasions": 52,
    "participants_3plus_eligible_occasions": 15,
    "all_possible_unordered_pair_count": 82,
    "all_possible_pair_counts": "{\"ses-1 + ses-2\": 48, \"ses-1 + ses-3\": 17, \"ses-2 + ses-3\": 17}",
    "complete_scheduled_ses1_ses2_pairs": 48,
    "complete_scheduled_ses1_ses2_participants": 48,
    "scheduled_ses1_ses2_observation_count": 157,
    "first_two_eligible_pair_count": 52,
    "first_two_eligible_assessments_participants": 52,
    "interval_all_pairs": "{\"max_days\": 1651.9583333333333, \"median_days\": 686.25, \"min_days\": 463.1666666666667, \"missing_timing\": 0, \"n_valid_intervals\": 82, \"nonpositive_intervals\": 0, \"timestamp_caveat\": \"rounded/anonymized acquisition timestamp; not exact cognitive-assessment time\", \"unparseable_timing\": 0}",
    "interval_first_two": "{\"max_days\": 1258.0, \"median_days\": 686.25, \"min_days\": 465.9583333333333, \"missing_timing\": 0, \"n_valid_intervals\": 52, \"nonpositive_intervals\": 0, \"timestamp_caveat\": \"rounded/anonymized acquisition timestamp; not exact cognitive-assessment time\", \"unparseable_timing\": 0}",
    "interval_complete_scheduled": "{\"max_days\": 1258.0, \"median_days\": 686.25, \"min_days\": 465.9583333333333, \"missing_timing\": 0, \"n_valid_intervals\": 48, \"nonpositive_intervals\": 0, \"timestamp_caveat\": \"rounded/anonymized acquisition timestamp; not exact cognitive-assessment time\", \"unparseable_timing\": 0}",
    "nominal_interval_days_summary": "{\"max_days\": 1651.9583333333333, \"median_days\": 686.25, \"min_days\": 463.1666666666667, \"missing_timing\": 0, \"n_valid_intervals\": 82, \"nonpositive_intervals\": 0, \"timestamp_caveat\": \"rounded/anonymized acquisition timestamp; not exact cognitive-assessment time\", \"unparseable_timing\": 0}",
    "timing_limitation": "acq_time is rounded/anonymized; interval is nominal, not an exact cognitive-assessment interval",
    "missing_score_loss_from_recorded_sessions": 23,
    "qc_loss_from_unfiltered_keys": 26,
    "comparability_uncertainty_status": "uncertain: task version, administration conditions, and exact cognitive timing are not established",
    "profile_any_unresolved_component_count": 24,
    "profile_all_components_unresolved_count": 13,
    "profile_mixed_unresolved_and_explicit_invalid_count": 0,
    "sub20812_continuation_keys": 0,
    "notes": "Complete scheduled pairs require both eligible ses-1 and ses-2 observations. A pair is a participant-level first-two eligible occasion summary; overlapping pairs are not independent participants. Missing-score loss is against recorded repository sessions; QC loss is against the unfiltered profile intersection."
  },
  {
    "specification_id": "fixed_five_domain",
    "specification_type": "explicit-task-intersection",
    "profile_label": "fixed_task_based_proxy_profile",
    "scenario_id": "strict_documented_V_only",
    "selected_tasks_exact": "{\"Complex cognition\": \"penn_matrix_reasoning_test:cnb_pmat_cr\", \"Episodic memory\": \"penn_face_memory_test:cnb_cpf_cr\", \"Executive control\": \"short_letter_2back:cnb_lnb_mcr\", \"Sensorimotor performance\": \"short_computerized_finger_tapping_task:cnb_ctap_dom\", \"Social cognition\": \"penn_emotion_recognition_task:cnb_er40_cr\"}",
    "eligible_occasions": 157,
    "eligible_participants_at_least_1": 101,
    "participants_2plus_eligible_occasions": 45,
    "participants_3plus_eligible_occasions": 11,
    "all_possible_unordered_pair_count": 67,
    "all_possible_pair_counts": "{\"ses-1 + ses-2\": 39, \"ses-1 + ses-3\": 12, \"ses-2 + ses-3\": 16}",
    "complete_scheduled_ses1_ses2_pairs": 39,
    "complete_scheduled_ses1_ses2_participants": 39,
    "scheduled_ses1_ses2_observation_count": 139,
    "first_two_eligible_pair_count": 45,
    "first_two_eligible_assessments_participants": 45,
    "interval_all_pairs": "{\"max_days\": 1334.9166666666667, \"median_days\": 667.875, \"min_days\": 463.1666666666667, \"missing_timing\": 0, \"n_valid_intervals\": 67, \"nonpositive_intervals\": 0, \"timestamp_caveat\": \"rounded/anonymized acquisition timestamp; not exact cognitive-assessment time\", \"unparseable_timing\": 0}",
    "interval_first_two": "{\"max_days\": 1308.8333333333333, \"median_days\": 667.875, \"min_days\": 465.9583333333333, \"missing_timing\": 0, \"n_valid_intervals\": 45, \"nonpositive_intervals\": 0, \"timestamp_caveat\": \"rounded/anonymized acquisition timestamp; not exact cognitive-assessment time\", \"unparseable_timing\": 0}",
    "interval_complete_scheduled": "{\"max_days\": 1258.0, \"median_days\": 680.375, \"min_days\": 465.9583333333333, \"missing_timing\": 0, \"n_valid_intervals\": 39, \"nonpositive_intervals\": 0, \"timestamp_caveat\": \"rounded/anonymized acquisition timestamp; not exact cognitive-assessment time\", \"unparseable_timing\": 0}",
    "nominal_interval_days_summary": "{\"max_days\": 1334.9166666666667, \"median_days\": 667.875, \"min_days\": 463.1666666666667, \"missing_timing\": 0, \"n_valid_intervals\": 67, \"nonpositive_intervals\": 0, \"timestamp_caveat\": \"rounded/anonymized acquisition timestamp; not exact cognitive-assessment time\", \"unparseable_timing\": 0}",
    "timing_limitation": "acq_time is rounded/anonymized; interval is nominal, not an exact cognitive-assessment interval",
    "missing_score_loss_from_recorded_sessions": 23,
    "qc_loss_from_unfiltered_keys": 45,
    "comparability_uncertainty_status": "uncertain: task version, administration conditions, and exact cognitive timing are not established",
    "profile_any_unresolved_component_count": 24,
    "profile_all_components_unresolved_count": 13,
    "profile_mixed_unresolved_and_explicit_invalid_count": 0,
    "sub20812_continuation_keys": 0,
    "notes": "Complete scheduled pairs require both eligible ses-1 and ses-2 observations. A pair is a participant-level first-two eligible occasion summary; overlapping pairs are not independent participants. Missing-score loss is against recorded repository sessions; QC loss is against the unfiltered profile intersection."
  }
]`.

## Readiness

The audit is ready for supervisor review of the measurement specification and SAP. It is not ready to freeze final scores: QC scope, selected-task definitions, comparability, direction, and weighting decisions remain appropriately scoped blockers.

Executable fixtures: `passed`.
