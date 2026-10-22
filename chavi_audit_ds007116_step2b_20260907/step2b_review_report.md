# CHAVI Step 2B review report

Verified and reused `41/41` staged Step 1B phenotype payloads from pinned ds007116 snapshot `1.0.6` at commit `fc7dc36fa2598b0b2e4579baef37d148cc085207`. The dataset checkout was not modified.

## Fixed-composition feasibility

The explicit five-domain feasibility proxy is LNB/Face/Matrix/ER40/dominant Finger Tapping. Key rows: `[
  {
    "specification_id": "fixed_five_domain",
    "specification_type": "explicit-task-intersection",
    "profile_label": "fixed_task_based_proxy_profile",
    "scenario_id": "unfiltered_observed",
    "selected_tasks_exact": "{\"Complex cognition\": \"penn_matrix_reasoning_test:cnb_pmat_cr\", \"Episodic memory\": \"penn_face_memory_test:cnb_cpf_cr\", \"Executive control\": \"short_letter_2back:cnb_lnb_mcr\", \"Sensorimotor performance\": \"short_computerized_finger_tapping_task:cnb_ctap_dom\", \"Social cognition\": \"penn_emotion_recognition_task:cnb_er40_cr\"}",
    "eligible_keys": 202,
    "eligible_participants": 123,
    "participants_2plus_eligible_occasions": 63,
    "participants_3plus_eligible_occasions": 16,
    "all_available_pair_counts": "{\"ses-1 + ses-2\": 60, \"ses-1 + ses-3\": 18, \"ses-2 + ses-3\": 17}",
    "pair_participant_counts": "{\"sub-138950\": 1, \"sub-19861\": 1, \"sub-20139\": 2, \"sub-20149\": 2, \"sub-20188\": 2, \"sub-20214\": 2, \"sub-20252\": 1, \"sub-20253\": 2, \"sub-20259\": 2, \"sub-20302\": 1, \"sub-20303\": 2, \"sub-20310\": 2, \"sub-20328\": 1, \"sub-20352\": 1, \"sub-20399\": 1, \"sub-20427\": 1, \"sub-20463\": 1, \"sub-20494\": 1, \"sub-20533\": 1, \"sub-20572\": 1, \"sub-20626\": 1, \"sub-20691\": 1, \"sub-20712\": 2, \"sub-20721\": 2, \"sub-20812\": 1, \"sub-20823\": 1, \"sub-20836\": 1, \"sub-20865\": 1, \"sub-20866\": 1, \"sub-20902\": 2, \"sub-20916\": 2, \"sub-20923\": 1, \"sub-20936\": 2, \"sub-20953\": 1, \"sub-20961\": 1, \"sub-20966\": 2, \"sub-20968\": 2, \"sub-20976\": 2, \"sub-20983\": 1, \"sub-21023\": 1, \"sub-21035\": 1, \"sub-21038\": 1, \"sub-21104\": 1, \"sub-21112\": 1, \"sub-21118\": 1, \"sub-21139\": 1, \"sub-21141\": 1, \"sub-21161\": 1, \"sub-21193\": 1, \"sub-21325\": 1, \"sub-21493\": 1, \"sub-21516\": 1, \"sub-21553\": 1, \"sub-21554\": 1, \"sub-21560\": 1, \"sub-21580\": 1, \"sub-21623\": 1, \"sub-21712\": 1, \"sub-21855\": 1, \"sub-22045\": 1, \"sub-22064\": 1, \"sub-22473\": 1, \"sub-22654\": 1}",
    "scheduled_ses1_ses2_keys": 183,
    "scheduled_ses1_ses2_participants": 60,
    "first_two_eligible_assessments_pairs": 63,
    "first_two_eligible_assessments_participants": 63,
    "nominal_interval_days_summary": "{\"n\": 95, \"min_days\": 394, \"median_days\": 680, \"max_days\": 1651}",
    "timing_limitation": "acq_time is rounded/anonymized; interval is nominal, not an exact cognitive-assessment interval",
    "missing_score_loss_from_unfiltered_keys": 23,
    "qc_loss_from_unfiltered_keys": 0,
    "uncertain_comparability_keys": 0,
    "sub20812_continuation_keys": 0,
    "notes": "A pair is a participant-level first-two eligible occasion summary; overlapping pairs are not treated as independent. Scheduled ses-1/ses-2 is descriptive only. Missing-score loss is recorded against available repository sessions; QC loss is recorded against the unfiltered profile intersection."
  },
  {
    "specification_id": "fixed_five_domain",
    "specification_type": "explicit-task-intersection",
    "profile_label": "fixed_task_based_proxy_profile",
    "scenario_id": "recommended_documented_valid_or_likely_valid",
    "selected_tasks_exact": "{\"Complex cognition\": \"penn_matrix_reasoning_test:cnb_pmat_cr\", \"Episodic memory\": \"penn_face_memory_test:cnb_cpf_cr\", \"Executive control\": \"short_letter_2back:cnb_lnb_mcr\", \"Sensorimotor performance\": \"short_computerized_finger_tapping_task:cnb_ctap_dom\", \"Social cognition\": \"penn_emotion_recognition_task:cnb_er40_cr\"}",
    "eligible_keys": 178,
    "eligible_participants": 110,
    "participants_2plus_eligible_occasions": 52,
    "participants_3plus_eligible_occasions": 16,
    "all_available_pair_counts": "{\"ses-1 + ses-2\": 49, \"ses-1 + ses-3\": 18, \"ses-2 + ses-3\": 17}",
    "pair_participant_counts": "{\"sub-138950\": 1, \"sub-19861\": 1, \"sub-20139\": 2, \"sub-20149\": 2, \"sub-20188\": 2, \"sub-20214\": 2, \"sub-20252\": 1, \"sub-20253\": 2, \"sub-20259\": 2, \"sub-20302\": 1, \"sub-20303\": 2, \"sub-20310\": 2, \"sub-20328\": 1, \"sub-20352\": 1, \"sub-20399\": 1, \"sub-20427\": 1, \"sub-20463\": 1, \"sub-20494\": 1, \"sub-20533\": 1, \"sub-20572\": 1, \"sub-20626\": 1, \"sub-20691\": 1, \"sub-20712\": 2, \"sub-20721\": 2, \"sub-20812\": 1, \"sub-20823\": 1, \"sub-20865\": 1, \"sub-20866\": 1, \"sub-20902\": 2, \"sub-20916\": 2, \"sub-20923\": 1, \"sub-20936\": 2, \"sub-20953\": 1, \"sub-20966\": 2, \"sub-20968\": 2, \"sub-20976\": 2, \"sub-21023\": 1, \"sub-21038\": 1, \"sub-21104\": 1, \"sub-21112\": 1, \"sub-21118\": 1, \"sub-21141\": 1, \"sub-21161\": 1, \"sub-21193\": 1, \"sub-21493\": 1, \"sub-21516\": 1, \"sub-21553\": 1, \"sub-21560\": 1, \"sub-21623\": 1, \"sub-21712\": 1, \"sub-21855\": 1, \"sub-22064\": 1}",
    "scheduled_ses1_ses2_keys": 159,
    "scheduled_ses1_ses2_participants": 49,
    "first_two_eligible_assessments_pairs": 52,
    "first_two_eligible_assessments_participants": 52,
    "nominal_interval_days_summary": "{\"n\": 84, \"min_days\": 463, \"median_days\": 692, \"max_days\": 1651}",
    "timing_limitation": "acq_time is rounded/anonymized; interval is nominal, not an exact cognitive-assessment interval",
    "missing_score_loss_from_unfiltered_keys": 23,
    "qc_loss_from_unfiltered_keys": 24,
    "uncertain_comparability_keys": 0,
    "sub20812_continuation_keys": 0,
    "notes": "A pair is a participant-level first-two eligible occasion summary; overlapping pairs are not treated as independent. Scheduled ses-1/ses-2 is descriptive only. Missing-score loss is recorded against available repository sessions; QC loss is recorded against the unfiltered profile intersection."
  },
  {
    "specification_id": "fixed_five_domain",
    "specification_type": "explicit-task-intersection",
    "profile_label": "fixed_task_based_proxy_profile",
    "scenario_id": "strict_V_only",
    "selected_tasks_exact": "{\"Complex cognition\": \"penn_matrix_reasoning_test:cnb_pmat_cr\", \"Episodic memory\": \"penn_face_memory_test:cnb_cpf_cr\", \"Executive control\": \"short_letter_2back:cnb_lnb_mcr\", \"Sensorimotor performance\": \"short_computerized_finger_tapping_task:cnb_ctap_dom\", \"Social cognition\": \"penn_emotion_recognition_task:cnb_er40_cr\"}",
    "eligible_keys": 157,
    "eligible_participants": 101,
    "participants_2plus_eligible_occasions": 45,
    "participants_3plus_eligible_occasions": 11,
    "all_available_pair_counts": "{\"ses-1 + ses-2\": 39, \"ses-1 + ses-3\": 12, \"ses-2 + ses-3\": 16}",
    "pair_participant_counts": "{\"sub-138950\": 1, \"sub-19861\": 1, \"sub-20139\": 2, \"sub-20149\": 1, \"sub-20188\": 2, \"sub-20214\": 2, \"sub-20252\": 1, \"sub-20253\": 2, \"sub-20259\": 1, \"sub-20302\": 1, \"sub-20303\": 2, \"sub-20310\": 1, \"sub-20328\": 1, \"sub-20352\": 1, \"sub-20463\": 1, \"sub-20572\": 1, \"sub-20626\": 1, \"sub-20691\": 1, \"sub-20712\": 2, \"sub-20721\": 2, \"sub-20823\": 1, \"sub-20865\": 1, \"sub-20866\": 1, \"sub-20902\": 1, \"sub-20916\": 1, \"sub-20923\": 1, \"sub-20936\": 2, \"sub-20953\": 1, \"sub-20966\": 2, \"sub-20968\": 2, \"sub-20976\": 2, \"sub-21023\": 1, \"sub-21038\": 1, \"sub-21104\": 1, \"sub-21112\": 1, \"sub-21118\": 1, \"sub-21141\": 1, \"sub-21161\": 1, \"sub-21193\": 1, \"sub-21493\": 1, \"sub-21553\": 1, \"sub-21560\": 1, \"sub-21623\": 1, \"sub-21855\": 1, \"sub-22064\": 1}",
    "scheduled_ses1_ses2_keys": 139,
    "scheduled_ses1_ses2_participants": 39,
    "first_two_eligible_assessments_pairs": 45,
    "first_two_eligible_assessments_participants": 45,
    "nominal_interval_days_summary": "{\"n\": 67, \"min_days\": 463, \"median_days\": 667, \"max_days\": 1334}",
    "timing_limitation": "acq_time is rounded/anonymized; interval is nominal, not an exact cognitive-assessment interval",
    "missing_score_loss_from_unfiltered_keys": 23,
    "qc_loss_from_unfiltered_keys": 45,
    "uncertain_comparability_keys": 0,
    "sub20812_continuation_keys": 0,
    "notes": "A pair is a participant-level first-two eligible occasion summary; overlapping pairs are not treated as independent. Scheduled ses-1/ses-2 is descriptive only. Missing-score loss is recorded against available repository sessions; QC loss is recorded against the unfiltered profile intersection."
  }
]`. See `paired_profile_feasibility.csv` for all task, domain-union, fixed, reduced, all-21-inventory, QC, pair, and interval rows.

## Outcomes

`outcome_matched_feasibility.csv` covers the five requested outcomes and separates baseline outcome, baseline any-cognitive score, baseline complete profile, later outcome, and same-visit counts. No outcome association or prediction was run.

## Review decision

Measurement definitions and QC semantics remain the blockers for final composites and reliability. Step 2B is complete as a decision-ready audit/SAP draft, not a final analysis.

Regression fixtures: `passed`.
