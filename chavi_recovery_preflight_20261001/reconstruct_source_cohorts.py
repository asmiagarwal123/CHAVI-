"""Independent CHAVI recovery-preflight source/cohort/fold reconstruction.

This script intentionally stops before fitting transformation parameters or creating
coordinates. It uses Step 3B source observations and the Step 3A occasion map. Step
5A and Recovery Phase 1 artifacts are comparison targets only, never calculation
inputs for cohort membership.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
STEP3B = ROOT / "chavi_audit_ds007116_step3b_20260909"
STEP5A = ROOT / "chavi_analysis_ds007116_step5a_measurement_specification_20260916"
R2 = ROOT / "chavi_analysis_ds007116_step5adr2_final_review_20260916"
FREEZE = ROOT / "chavi_analysis_ds007116_step5af_contract_freeze_20260916"
RECOVERY = ROOT / "chavi_recovery_phase1_forensic_audit_20260916"
DATASET = ROOT / "ds007116"
STAGE = ROOT / "chavi_step1b_phenotype_staging_20260907"

TASKS = (
    ("letter_nback", "short_letter_2back", "cnb_lnb_mcr", "cnb_lnb_valid_code"),
    ("face_memory", "penn_face_memory_test", "cnb_cpf_cr", "cnb_cpf_valid_code"),
    ("matrix_reasoning", "penn_matrix_reasoning_test", "cnb_pmat_cr", "cnb_pmat_valid_code"),
    ("emotion_recognition", "penn_emotion_recognition_task", "cnb_er40_cr", "cnb_er40_valid_code"),
    ("dominant_finger_tapping", "short_computerized_finger_tapping_task", "cnb_ctap_dom", "cnb_ctap_valid_code"),
)
TASK_KEYS = tuple(t[0] for t in TASKS)
VF = {"V", "F"}
FOLD_SEED = 42
N_FOLDS = 5

HANDOFFS = (
    "CHATGPT_CODEX_HANDOFF.md",
    "CHAVI_MASTER_PROJECT_SPECIFICATION_AND_HANDOFF.md",
    "CURRENT_PROJECT_STATE.md",
    "PROJECT_FILE_MAP.md",
    "PROJECT_IMPLEMENTATION_HISTORY.md",
    "PROJECT_MASTER_CONTEXT.md",
    "RESEARCH_STATUS.md",
    "summary.md",
)

GOVERNING_INPUTS = (
    "ds007116/dataset_description.json",
    "ds007116/participants.tsv",
    "chavi_audit_ds007116_step1b_20260907/retrieval_manifest.csv",
    "chavi_audit_ds007116_step1b_20260907/dataset_provenance.json",
    "chavi_audit_ds007116_step3b_20260909/task_observations_long.csv",
    "chavi_audit_ds007116_step3b_20260909/paired_task_observations.csv",
    "chavi_audit_ds007116_step3b_20260909/paired_profile_manifest.csv",
    "chavi_audit_ds007116_step3b_20260909/assessment_occasion_mapping_step3a.csv",
    "chavi_audit_ds007116_step3b_20260909/executable_specification.json",
    "chavi_audit_ds007116_step3b_20260909/provenance_step3b.json",
    "chavi_analysis_ds007116_step5a_measurement_specification_20260916/synchronized_profile_occasions.csv",
    "chavi_analysis_ds007116_step5a_measurement_specification_20260916/synchronized_profile_pair_candidates.csv",
    "chavi_analysis_ds007116_step5a_measurement_specification_20260916/profile_pair_source_trace.csv",
    "chavi_analysis_ds007116_step5a_measurement_specification_20260916/score_semantics_and_direction.csv",
    "chavi_analysis_ds007116_step5a_measurement_specification_20260916/step5a_provenance.json",
    "chavi_analysis_ds007116_step5adr2_final_review_20260916/step5adr2_transformation_contract_candidate.json",
    "chavi_analysis_ds007116_step5adr2_final_review_20260916/step5adr2_decision_matrix.csv",
    "chavi_analysis_ds007116_step5adr2_final_review_20260916/reference_109_vs_52_comparison.csv",
    "chavi_analysis_ds007116_step5adr2_final_review_20260916/age_model_comparison_final.csv",
    "chavi_analysis_ds007116_step5adr2_final_review_20260916/sd_mad_diagnostics_final.csv",
    "chavi_analysis_ds007116_step5adr2_final_review_20260916/extrapolation_accounting_final.csv",
    "chavi_analysis_ds007116_step5adr2_final_review_20260916/bootstrap_feasibility_summary.json",
    "chavi_analysis_ds007116_step5af_contract_freeze_20260916/SUPERVISOR_APPROVAL.yaml",
    "chavi_analysis_ds007116_step5af_contract_freeze_20260916/step5af_transformation_contract_frozen.json",
    "chavi_analysis_ds007116_step5af_contract_freeze_20260916/step5af_provenance.json",
    "chavi_recovery_phase1_forensic_audit_20260916/RECOVERY_PHASE1_FORENSIC_AUDIT_REPORT.md",
    "chavi_recovery_phase1_forensic_audit_20260916/trusted_boundary_and_recovery_recommendation.md",
    "chavi_recovery_phase1_forensic_audit_20260916/MASTER_ISSUE_REGISTER.csv",
    "chavi_recovery_phase1_forensic_audit_20260916/reference_a_fold_expected_counts.csv",
    "chavi_recovery_phase1_forensic_audit_20260916/reference_a_implementation_comparison.csv",
    "chavi_recovery_phase1_forensic_audit_20260916/contract_field_comparison.csv",
    "chavi_recovery_phase1_forensic_audit_20260916/validation_independence_classification.csv",
)


def read_csv(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def identity_hash(values: list[str]) -> str:
    return hashlib.sha256(("\n".join(values) + "\n").encode("utf-8")).hexdigest()


def finite_number(value: str) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def session_order(value: str) -> tuple[int, str]:
    match = re.fullmatch(r"ses-(\d+)", value or "")
    return (int(match.group(1)), value) if match else (10**9, value or "")


def git_value(*args: str) -> str:
    command = ["git", "-c", f"safe.directory={DATASET.as_posix()}", "-C", str(DATASET), *args]
    return subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip()


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()

    # Hash/document all governing inputs. Five task dictionaries and staged payloads
    # are added explicitly because they control field/QC semantics and source content.
    input_relpaths = list(HANDOFFS) + list(GOVERNING_INPUTS)
    for _, stem, _, _ in TASKS:
        input_relpaths.extend((f"ds007116/phenotype/{stem}.json", f"chavi_step1b_phenotype_staging_20260907/{stem}.tsv"))
    input_relpaths = sorted(set(input_relpaths))
    input_manifest: list[dict[str, object]] = []
    for rel in input_relpaths:
        path = ROOT / rel
        exists = path.is_file()
        input_manifest.append({
            "relative_path": rel,
            "role": "handoff/context" if rel in HANDOFFS else "governing/comparison evidence",
            "exists": "yes" if exists else "no",
            "size_bytes": path.stat().st_size if exists else "",
            "sha256": sha256_file(path) if exists else "",
            "verification_outcome": "hashed" if exists else "missing",
        })
    if any(row["exists"] == "no" for row in input_manifest):
        raise AssertionError("One or more declared governing inputs are missing")

    # Independently reverify every staged phenotype payload against the pinned
    # retrieval manifest. Historical absolute paths are ignored.
    retrieval = read_csv(ROOT / "chavi_audit_ds007116_step1b_20260907/retrieval_manifest.csv")
    retrieval_failures: list[str] = []
    for row in retrieval:
        staged = STAGE / Path(row["relative_dataset_path"]).name
        if not staged.is_file():
            retrieval_failures.append(f"missing:{staged.name}")
            continue
        actual_hash = sha256_file(staged)
        actual_size = staged.stat().st_size
        if actual_hash != row["expected_sha256"] or actual_size != int(row["expected_size_bytes"]):
            retrieval_failures.append(f"hash_or_size:{staged.name}")

    # Verify exact dictionary meanings for the two accepted raw QC codes.
    qc_dictionary_rows: list[dict[str, str]] = []
    qc_semantics_ok = True
    for task_key, stem, _, qc_field in TASKS:
        dictionary = json.loads((DATASET / "phenotype" / f"{stem}.json").read_text(encoding="utf-8"))
        levels = dictionary[qc_field]["Levels"]
        v_meaning = levels.get("V", "")
        f_meaning = levels.get("F", "")
        task_ok = v_meaning.strip().lower() == "valid" and f_meaning.strip().lower().startswith("likely valid")
        qc_semantics_ok = qc_semantics_ok and task_ok
        qc_dictionary_rows.append({
            "task_key": task_key,
            "qc_field": qc_field,
            "V_meaning": v_meaning,
            "F_meaning": f_meaning,
            "vf_mapping_verified": "yes" if task_ok else "no",
        })

    participants = read_csv(DATASET / "participants.tsv", "\t")
    participant_ids = [row["participant_id"] for row in participants]
    if len(participant_ids) != 132 or len(set(participant_ids)) != 132:
        raise AssertionError("Registered participant frame is not 132 unique identities")

    mappings = read_csv(STEP3B / "assessment_occasion_mapping_step3a.csv")
    mapping_by_key = {(r["participant_id"], r["original_session_id"]): r for r in mappings}
    continuation_keys = {
        key for key, row in mapping_by_key.items()
        if "continuation" in (row.get("comparability_status", "") + " " + row.get("proposed_cognitive_occasion_id", "")).lower()
    }

    observations = read_csv(STEP3B / "task_observations_long.csv")
    expected_task_meta = {key: (stem, field, qc) for key, stem, field, qc in TASKS}
    source: dict[tuple[str, str, str], dict[str, str]] = {}
    duplicate_keys: list[tuple[str, str, str]] = []
    source_metadata_mismatches: list[str] = []
    eligible_flag_mismatches: list[str] = []
    for row in observations:
        key = (row["participant_id"], row["repository_session_id"], row["task_key"])
        if key in source:
            duplicate_keys.append(key)
        source[key] = row
        if row["task_key"] in expected_task_meta:
            stem, field, _ = expected_task_meta[row["task_key"]]
            if row["task_table_stem"] != stem or row["score_field"] != field:
                source_metadata_mismatches.append("|".join(key))
            raw_qc = row["raw_qc_codes"]
            expected_eligible = finite_number(row["parsed_numeric_value"]) and raw_qc in VF
            actual_eligible = row["eligible_documented_valid_or_likely_valid"] == "yes"
            if expected_eligible != actual_eligible:
                eligible_flag_mismatches.append("|".join(key))
    if duplicate_keys:
        raise AssertionError(f"Duplicate source keys: {duplicate_keys[:5]}")

    def task_eligible(row: dict[str, str] | None, policy: str) -> bool:
        if not row or not finite_number(row["parsed_numeric_value"]):
            return False
        code = row["raw_qc_codes"]
        if policy == "vf":
            return code in VF and row["eligible_documented_valid_or_likely_valid"] == "yes"
        if policy == "v_only":
            return code == "V" and row["eligible_strict_documented_V_only"] == "yes"
        raise ValueError(policy)

    all_occurrence_keys = sorted(
        {(p, s) for p, s, task in source if task in TASK_KEYS},
        key=lambda item: (item[0], session_order(item[1])),
    )

    def complete_occasions(policy: str) -> dict[str, list[str]]:
        result: dict[str, list[str]] = defaultdict(list)
        for pid, session in all_occurrence_keys:
            if (pid, session) in continuation_keys:
                continue
            if all(task_eligible(source.get((pid, session, task)), policy) for task in TASK_KEYS):
                result[pid].append(session)
        for pid in result:
            result[pid] = sorted(set(result[pid]), key=session_order)
        return dict(result)

    vf_complete = complete_occasions("vf")
    v_complete = complete_occasions("v_only")
    ref_a_ids = sorted(vf_complete)
    primary_ids = sorted(pid for pid, sessions in vf_complete.items() if len(sessions) >= 2)
    vonly_ids = sorted(pid for pid, sessions in v_complete.items() if len(sessions) >= 2)
    ref_b_ids = primary_ids.copy()
    primary_sessions = {pid: vf_complete[pid][:2] for pid in primary_ids}
    vonly_sessions = {pid: v_complete[pid][:2] for pid in vonly_ids}

    # Independently reconstruct task-specific first-two eligible pairs and their
    # identity/session alignment; do not consume Step 4B pair manifests here.
    task_pair_sessions: dict[str, dict[str, tuple[str, str]]] = {task: {} for task in TASK_KEYS}
    for task in TASK_KEYS:
        sessions_by_pid: dict[str, list[str]] = defaultdict(list)
        for pid, session in all_occurrence_keys:
            if (pid, session) in continuation_keys:
                continue
            if task_eligible(source.get((pid, session, task)), "vf"):
                sessions_by_pid[pid].append(session)
        for pid, sessions in sessions_by_pid.items():
            ordered = sorted(set(sessions), key=session_order)
            if len(ordered) >= 2:
                task_pair_sessions[task][pid] = (ordered[0], ordered[1])
    intersection_53 = set.intersection(*(set(task_pair_sessions[task]) for task in TASK_KEYS))
    aligned_50 = {
        pid for pid in intersection_53
        if len({task_pair_sessions[task][pid] for task in TASK_KEYS}) == 1
    }

    # Proposed repair: apply the frozen algorithm wording to the approved Ref-A
    # universe. This is emitted as candidate evidence, not called historically approved.
    sorted_ref = sorted(ref_a_ids)
    rng = np.random.default_rng(FOLD_SEED)
    shuffled = rng.permuted(np.array(sorted_ref))
    fold_map = {str(pid): int(index % N_FOLDS) for index, pid in enumerate(shuffled)}
    rng_repeat = np.random.default_rng(FOLD_SEED)
    shuffled_repeat = rng_repeat.permuted(np.array(sorted_ref))
    deterministic = [str(v) for v in shuffled] == [str(v) for v in shuffled_repeat]

    expected_fold_rows = read_csv(RECOVERY / "reference_a_fold_expected_counts.csv")
    expected_by_fold = {int(row["fold"]): row for row in expected_fold_rows}
    fold_rows: list[dict[str, object]] = []
    fold_comparison_rows: list[dict[str, object]] = []
    fold_identity_match = True
    sorted_round_robin_map = {pid: index % N_FOLDS for index, pid in enumerate(sorted_ref)}
    for pid in sorted_ref:
        fold = fold_map[pid]
        held_out = sorted(p for p in sorted_ref if fold_map[p] == fold)
        training = sorted(p for p in sorted_ref if fold_map[p] != fold)
        expected = expected_by_fold[fold]
        expected_held = expected["held_out_identity_list"].split(";")
        expected_train = expected["training_identity_list"].split(";")
        this_match = held_out == expected_held and training == expected_train
        fold_identity_match = fold_identity_match and this_match
        fold_rows.append({
            "participant_id": pid,
            "held_out_fold": fold,
            "in_reference_a": "yes",
            "in_primary_vf": "yes" if pid in primary_ids else "no",
            "in_vonly_sensitivity": "yes" if pid in vonly_ids else "no",
            "reference_session_id": vf_complete[pid][0],
            "held_out_count": len(held_out),
            "training_count": len(training),
            "held_out_identity_list": ";".join(held_out),
            "training_identity_list": ";".join(training),
            "held_out_identities_sha256": identity_hash(held_out),
            "training_identities_sha256": identity_hash(training),
            "matches_recovery_expected_identity_lists": "yes" if this_match else "no",
        })
    for fold in range(N_FOLDS):
        permuted_ids = sorted(pid for pid in sorted_ref if fold_map[pid] == fold)
        sorted_rr_ids = sorted(pid for pid in sorted_ref if sorted_round_robin_map[pid] == fold)
        recovery_ids = expected_by_fold[fold]["held_out_identity_list"].split(";")
        fold_comparison_rows.append({
            "fold": fold,
            "permuted_seed42_count": len(permuted_ids),
            "permuted_seed42_identity_list": ";".join(permuted_ids),
            "permuted_seed42_sha256": identity_hash(permuted_ids),
            "sorted_round_robin_count": len(sorted_rr_ids),
            "sorted_round_robin_identity_list": ";".join(sorted_rr_ids),
            "sorted_round_robin_sha256": identity_hash(sorted_rr_ids),
            "recovery_expected_identity_list": ";".join(recovery_ids),
            "recovery_expected_sha256": identity_hash(recovery_ids),
            "seed42_matches_recovery": "yes" if permuted_ids == recovery_ids else "no",
            "sorted_round_robin_matches_recovery": "yes" if sorted_rr_ids == recovery_ids else "no",
            "identity_overlap_seed42_vs_recovery": len(set(permuted_ids) & set(recovery_ids)),
        })

    # Reference source rows: exactly one earliest complete synchronized occasion
    # and exactly five task rows per participant.
    reference_rows: list[dict[str, object]] = []
    for pid in sorted_ref:
        session = vf_complete[pid][0]
        mapping = mapping_by_key.get((pid, session), {})
        for task_key, stem, field, qc_field in TASKS:
            row = source[(pid, session, task_key)]
            reference_rows.append({
                "participant_id": pid,
                "reference_session_id": session,
                "cognitive_occasion_id": row["cognitive_occasion_id"],
                "session_age": row["session_age"],
                "task_key": task_key,
                "task_table_stem": stem,
                "score_field": field,
                "raw_value": row["original_value"],
                "parsed_numeric_value": row["parsed_numeric_value"],
                "qc_field": qc_field,
                "raw_qc_code": row["raw_qc_codes"],
                "qc_meaning": row["documented_qc_meanings"],
                "source_filename": row["source_filename"],
                "source_row_reference": row["source_row_reference"],
                "occasion_comparability_status": mapping.get("comparability_status", row["comparability_status"]),
                "held_out_fold_candidate": fold_map[pid],
            })

    # One identity-level row per registered participant makes every set difference
    # auditable without forcing the expected counts.
    source_participants = {row["participant_id"] for row in observations}
    reconciliation_rows: list[dict[str, object]] = []
    for pid in participant_ids:
        pair_values = sorted({"/".join(task_pair_sessions[t][pid]) for t in TASK_KEYS if pid in task_pair_sessions[t]})
        reconciliation_rows.append({
            "participant_id": pid,
            "registered": "yes",
            "present_in_step3b_task_source": "yes" if pid in source_participants else "no",
            "complete_vf_occasion_count": len(vf_complete.get(pid, [])),
            "complete_vf_sessions": ";".join(vf_complete.get(pid, [])),
            "reference_a": "yes" if pid in ref_a_ids else "no",
            "reference_a_session": vf_complete.get(pid, [""])[0] if pid in vf_complete else "",
            "primary_vf": "yes" if pid in primary_ids else "no",
            "primary_vf_sessions": ";".join(primary_sessions.get(pid, [])),
            "complete_vonly_occasion_count": len(v_complete.get(pid, [])),
            "complete_vonly_sessions": ";".join(v_complete.get(pid, [])),
            "vonly_sensitivity": "yes" if pid in vonly_ids else "no",
            "vonly_sessions": ";".join(vonly_sessions.get(pid, [])),
            "all_five_task_pair_intersection": "yes" if pid in intersection_53 else "no",
            "task_pair_session_combinations": ";".join(pair_values),
            "all_five_task_pairs_aligned": "yes" if pid in aligned_50 else "no",
            "continuation_sessions_excluded": ";".join(sorted(s for p, s in continuation_keys if p == pid)),
        })

    write_csv(OUT / "input_artifact_manifest.csv", input_manifest,
              ["relative_path", "role", "exists", "size_bytes", "sha256", "verification_outcome"])
    write_csv(OUT / "source_cohort_reconciliation.csv", reconciliation_rows, list(reconciliation_rows[0]))
    write_csv(OUT / "reference_cohort_manifest.csv", reference_rows, list(reference_rows[0]))
    write_csv(OUT / "participant_fold_manifest.csv", fold_rows, list(fold_rows[0]))
    write_csv(OUT / "fold_algorithm_comparison.csv", fold_comparison_rows, list(fold_comparison_rows[0]))
    write_csv(OUT / "qc_dictionary_verification.csv", qc_dictionary_rows, list(qc_dictionary_rows[0]))

    # Compare identity sets with Step 5A outputs only after independent reconstruction.
    step5a_pairs = read_csv(STEP5A / "synchronized_profile_pair_candidates.csv")
    step5a_primary_ids = sorted(r["participant_id"] for r in step5a_pairs)
    step5a_occasions = read_csv(STEP5A / "synchronized_profile_occasions.csv")
    step5a_ref_ids = sorted({r["participant_id"] for r in step5a_occasions if r["synchronized_occasion_status"] == "complete_synchronized_vf"})

    fold_counts = {fold: sum(1 for pid in sorted_ref if fold_map[pid] == fold) for fold in range(N_FOLDS)}
    training_counts = {fold: len(sorted_ref) - fold_counts[fold] for fold in range(N_FOLDS)}
    primary_row_count = sum(len(primary_sessions[pid]) * len(TASKS) for pid in primary_ids)
    vonly_row_count = sum(len(vonly_sessions[pid]) * len(TASKS) for pid in vonly_ids)

    checks = {
        "dataset": {
            "commit": git_value("rev-parse", "HEAD"),
            "tag_at_head": git_value("tag", "--points-at", "HEAD"),
            "branch_status": git_value("status", "--short", "--branch"),
            "clean": len(git_value("status", "--porcelain")) == 0,
        },
        "payload_verification": {
            "manifest_rows": len(retrieval),
            "fresh_hash_size_failures": retrieval_failures,
            "all_41_verified": len(retrieval) == 41 and not retrieval_failures,
        },
        "source_integrity": {
            "task_rows": len(observations),
            "unique_task_keys": len(source),
            "duplicate_keys": ["|".join(k) for k in duplicate_keys],
            "source_metadata_mismatches": source_metadata_mismatches,
            "eligible_flag_mismatches": eligible_flag_mismatches,
            "qc_dictionary_vf_mapping_verified": qc_semantics_ok,
            "continuation_keys": ["|".join(k) for k in sorted(continuation_keys)],
        },
        "cohorts": {
            "registered_participants": len(participant_ids),
            "source_participants": len(source_participants),
            "complete_vf_occasions": sum(map(len, vf_complete.values())),
            "reference_a_participants": len(ref_a_ids),
            "reference_a_rows": len(reference_rows),
            "primary_vf_participants": len(primary_ids),
            "primary_vf_occasions": sum(len(v) for v in primary_sessions.values()),
            "primary_vf_rows": primary_row_count,
            "vonly_participants": len(vonly_ids),
            "vonly_occasions": sum(len(v) for v in vonly_sessions.values()),
            "vonly_rows": vonly_row_count,
            "task_pair_intersection": len(intersection_53),
            "task_pair_aligned": len(aligned_50),
            "profile_not_aligned_50": sorted(set(primary_ids) - aligned_50),
            "task_intersection_not_profile_52": sorted(intersection_53 - set(primary_ids)),
            "matches_step5a_primary_identities": primary_ids == step5a_primary_ids,
            "matches_step5a_reference_identity_set": ref_a_ids == step5a_ref_ids,
        },
        "candidate_folds": {
            "classification": "PROPOSED_AMENDMENT_APPLICATION_TO_REFERENCE_A",
            "algorithm": "numpy 2.5.2 default_rng(42).permuted(sorted Reference-A IDs), fold=index mod 5",
            "numpy_version": np.__version__,
            "held_out_counts": fold_counts,
            "training_counts": training_counts,
            "each_reference_participant_exactly_one_fold": len(fold_map) == len(ref_a_ids) == len(set(fold_map)),
            "no_holdout_in_training": all(not (set(r["held_out_identity_list"].split(";")) & set(r["training_identity_list"].split(";"))) for r in fold_rows),
            "all_primary_map_to_reference_a": set(primary_ids) <= set(ref_a_ids),
            "all_vonly_map_to_reference_a": set(vonly_ids) <= set(ref_a_ids),
            "deterministic_same_process_repeat": deterministic,
            "matches_recovery_phase1_expected_identity_lists": fold_identity_match,
        },
        "fresh_environment": {
            "timestamp_utc": started,
            "executable": sys.executable,
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "isolated_environment": str(Path(sys.prefix)),
        },
    }
    (OUT / "preflight_results.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")

    required = (
        checks["dataset"]["commit"] == "fc7dc36fa2598b0b2e4579baef37d148cc085207"
        and checks["dataset"]["tag_at_head"] == "1.0.6"
        and checks["dataset"]["clean"]
        and checks["payload_verification"]["all_41_verified"]
        and not source_metadata_mismatches
        and not eligible_flag_mismatches
        and qc_semantics_ok
        and len(ref_a_ids) == 109 and len(reference_rows) == 545
        and len(primary_ids) == 52 and primary_row_count == 520
        and len(vonly_ids) == 45 and vonly_row_count == 450
        and fold_counts == {0: 22, 1: 22, 2: 22, 3: 22, 4: 21}
        and training_counts == {0: 87, 1: 87, 2: 87, 3: 87, 4: 88}
        and fold_identity_match and deterministic
    )
    print(json.dumps({"preflight_source_and_fold_checks_passed": required, **checks["cohorts"], **checks["candidate_folds"]}, indent=2))
    return 0 if required else 2


if __name__ == "__main__":
    raise SystemExit(main())
