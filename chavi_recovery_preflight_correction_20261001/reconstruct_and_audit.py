"""Independent source reconstruction and cross-fit audit for CHAVI correction.

This script produces identity/source evidence only. It never fits transformation
parameters, creates coordinates, or runs an empirical bootstrap.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
DATASET = ROOT / "ds007116"
STAGE = ROOT / "chavi_step1b_phenotype_staging_20260907"
STEP3B = ROOT / "chavi_audit_ds007116_step3b_20260909"
STEP5A = ROOT / "chavi_analysis_ds007116_step5a_measurement_specification_20260916"
PRIOR = ROOT / "chavi_recovery_preflight_20261001"

TASKS = (
    ("letter_nback", "short_letter_2back", "cnb_lnb_mcr", "cnb_lnb_valid_code"),
    ("face_memory", "penn_face_memory_test", "cnb_cpf_cr", "cnb_cpf_valid_code"),
    ("matrix_reasoning", "penn_matrix_reasoning_test", "cnb_pmat_cr", "cnb_pmat_valid_code"),
    ("emotion_recognition", "penn_emotion_recognition_task", "cnb_er40_cr", "cnb_er40_valid_code"),
    ("dominant_finger_tapping", "short_computerized_finger_tapping_task", "cnb_ctap_dom", "cnb_ctap_valid_code"),
)
TASK_KEYS = tuple(x[0] for x in TASKS)
TASK_META = {x[0]: x[1:] for x in TASKS}
N_FOLDS = 5
SEED = 42

HISTORICAL_IMPLEMENTATIONS = (
    ("R2 age-model diagnostic", "chavi_analysis_ds007116_step5adr2_final_review_20260916/run_step5adr2.py", "C", "inner merge of 109-row Reference A with 52-row target fold map drops 57 auxiliaries", "41/41/42/42/42", "no target self-inclusion; does not implement 109-person Reference A"),
    ("Step 5B-A production (quarantined)", "chavi_analysis_ds007116_step5ba_transformed_data_20260916/run_step5ba.py", "B", "left merge preserves 57 auxiliaries with missing fold; missing != held-out fold retains them", "98/98/99/99/99", "no target self-inclusion; mathematically Reference A under Design B"),
    ("Step 5B-A-R2 copy (quarantined)", "chavi_analysis_ds007116_step5bar2_independent_review_20260916/run_step5bar2.py", "B", "same left-merge and fitting expression as Step 5B-A", "98/98/99/99/99", "no target self-inclusion; mathematically Reference A under Design B"),
    ("Step 5B-A-R3 engine (quarantined)", "step5bar3_engine.py", "C", "Reference set is earliest occasion of participants with >=2 complete occasions", "41/41/42/42/42", "no target self-inclusion; mislabeled Reference A"),
    ("R3 independent validator (quarantined)", "independent_transformation_validator.py", "C", "Reference identities explicitly require >=2 complete occasions", "41/41/42/42/42", "no target self-inclusion; mislabeled Reference A"),
    ("Recovery Phase 1 expected map", "chavi_recovery_phase1_forensic_audit_20260916/reference_a_fold_expected_counts.csv", "A-sorted", "all 109 identities folded by unpermuted sorted round-robin", "87/87/87/87/88", "no self-inclusion; conflicts with literal seeded wording"),
)


def read_csv(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0]) if rows else ["status"]
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


def identity_hash(values) -> str:
    ordered = sorted(str(v) for v in values)
    return hashlib.sha256(("\n".join(ordered) + "\n").encode()).hexdigest()


def finite(value: str) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def normalize_missing(value: str) -> str:
    return "" if (value or "").strip().lower() in {"", "n/a", "na", "nan"} else value


def session_order(value: str) -> tuple[int, str]:
    match = re.fullmatch(r"ses-(\d+)", value or "")
    return (int(match.group(1)), value) if match else (10**9, value or "")


def upstream_flag_mismatches(rows: list[dict[str, str]]) -> tuple[list[str], list[str]]:
    vf, strict = [], []
    for row in rows:
        key = "|".join((row["participant_id"], row["repository_session_id"], row["task_key"]))
        raw_vf = finite(row["parsed_numeric_value"]) and row["raw_qc_codes"] in {"V", "F"}
        raw_v = finite(row["parsed_numeric_value"]) and row["raw_qc_codes"] == "V"
        if raw_vf != (row["eligible_documented_valid_or_likely_valid"] == "yes"):
            vf.append(key)
        if raw_v != (row["eligible_strict_documented_V_only"] == "yes"):
            strict.append(key)
    return vf, strict


def ensure_unique(rows: list[dict[str, str]], fields: tuple[str, ...], label: str) -> None:
    keys = [tuple(r[f] for f in fields) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError(f"duplicate_{label}_keys")


def validate_required_mappings(occasion_keys, mapping_keys) -> None:
    missing = set(occasion_keys) - set(mapping_keys)
    if missing:
        raise ValueError("missing_required_occasion_mapping")


def validate_identity_set(actual, expected) -> None:
    if set(actual) != set(expected):
        raise ValueError("identity_mismatch_despite_possible_count_match")


def validate_reference_design(label: str, fitting_ids, reference_ids) -> None:
    if label == "Reference_A" and not set(fitting_ids) <= set(reference_ids):
        raise ValueError("fitting_identity_outside_reference_a")
    if label == "Reference_A" and len(set(reference_ids)) == 109 and len(set(fitting_ids)) in {41, 42}:
        raise ValueError("design_c_incorrectly_labelled_reference_a")


def validate_no_leakage(held_out_ids, fitting_ids) -> None:
    if set(held_out_ids) & set(fitting_ids):
        raise ValueError("held_out_identity_in_fitting_data")


def validate_support_semantics(model: str, support_status: str) -> None:
    if model == "M0" and support_status != "not_applicable":
        raise ValueError("m0_inherits_m1_support_status")


def complete_occasions(source, occasion_keys, continuation, policy: str):
    allowed = {"V", "F"} if policy == "vf" else {"V"}
    result = defaultdict(list)
    for pid, session in occasion_keys:
        if (pid, session) in continuation:
            continue
        eligible = True
        for task in TASK_KEYS:
            row = source.get((pid, session, task))
            eligible &= bool(row and finite(row["parsed_numeric_value"]) and row["raw_qc_codes"] in allowed)
        if eligible:
            result[pid].append(session)
    return {pid: sorted(set(sessions), key=session_order) for pid, sessions in result.items()}


def scale_status(values: list[float], scale: float) -> str:
    """Numerical policy: exact/nonfinite first, then machine-resolution test.

    Translation of input values cannot change the result. Scaling values by a
    nonzero unit conversion scales both scale and spread, preserving the result.
    """
    if not math.isfinite(scale):
        return "nonfinite"
    if scale == 0:
        return "exactly_degenerate"
    finite_values = [float(v) for v in values if math.isfinite(float(v))]
    if not finite_values:
        return "nonfinite_input"
    spread = max(finite_values) - min(finite_values)
    # Use scale/spread, not the score center or absolute origin. A separate
    # representability warning may inspect ulp(x) when values have huge offsets.
    magnitude = max(spread, abs(scale))
    floor = 64 * sys.float_info.epsilon * magnitude
    return "numerically_degenerate" if scale <= floor else "valid"


def validate_wide_metadata(rows: list[dict[str, str]], key_fields, metadata_fields) -> None:
    seen = {}
    for row in rows:
        key = tuple(row[k] for k in key_fields)
        metadata = tuple(row[m] for m in metadata_fields)
        if key in seen and seen[key] != metadata:
            raise ValueError("nonconstant_metadata_splits_wide_key")
        seen[key] = metadata


def validate_m1_training(ages: list[float]) -> None:
    if not ages or any(not math.isfinite(float(x)) for x in ages):
        raise ValueError("m1_missing_or_nonfinite_training_age")
    if len(set(float(x) for x in ages)) < 2:
        raise ValueError("m1_constant_age_rank_deficient")


def bootstrap_training_draws(draws: list[tuple[str, str]], held_out: set[str]):
    leaked = [(identity, draw_id) for identity, draw_id in draws if identity in held_out]
    if leaked:
        raise ValueError("held_out_identity_copy_in_bootstrap_training")
    return draws


def derive() -> dict:
    observations = read_csv(STEP3B / "task_observations_long.csv")
    mappings = read_csv(STEP3B / "assessment_occasion_mapping_step3a.csv")
    participants = read_csv(DATASET / "participants.tsv", "\t")
    ensure_unique(observations, ("participant_id", "repository_session_id", "task_key"), "source")
    ensure_unique(mappings, ("participant_id", "original_session_id"), "occasion_map")

    registered = [r["participant_id"] for r in participants]
    if len(registered) != len(set(registered)):
        raise ValueError("duplicate_registered_participant")
    registered_set = set(registered)
    retrieval = read_csv(ROOT / "chavi_audit_ds007116_step1b_20260907/retrieval_manifest.csv")
    payload_failures = []
    for row in retrieval:
        path = STAGE / Path(row["relative_dataset_path"]).name
        if (not path.is_file() or path.stat().st_size != int(row["expected_size_bytes"])
                or sha256_file(path) != row["expected_sha256"]):
            payload_failures.append(row["relative_dataset_path"])
    dictionary_errors = []
    for task, stem, score_field, qc_field in TASKS:
        dictionary = json.loads((DATASET / "phenotype" / f"{stem}.json").read_text(encoding="utf-8"))
        levels = dictionary[qc_field]["Levels"]
        if levels.get("V", "").strip().lower() != "valid" or not levels.get("F", "").strip().lower().startswith("likely valid"):
            dictionary_errors.append(task)
    source = {}
    metadata_errors, unregistered = [], []
    for row in observations:
        key = (row["participant_id"], row["repository_session_id"], row["task_key"])
        if row["task_key"] in TASK_META:
            stem, field, qc_field = TASK_META[row["task_key"]]
            if (row["task_table_stem"], row["score_field"], row["applicable_qc_fields"]) != (stem, field, qc_field):
                metadata_errors.append("|".join(key))
            source[key] = row
        if row["participant_id"] not in registered_set:
            unregistered.append("|".join(key))

    mapping_by_key = {(r["participant_id"], r["original_session_id"]): r for r in mappings}
    occasion_keys = sorted({(p, s) for p, s, _ in source}, key=lambda x: (x[0], session_order(x[1])))
    missing_mappings = ["|".join(k) for k in occasion_keys if k not in mapping_by_key]
    continuation = {k for k, r in mapping_by_key.items() if "continuation" in (r["comparability_status"] + " " + r["proposed_cognitive_occasion_id"]).lower()}
    vf_mismatch, strict_mismatch = upstream_flag_mismatches(list(source.values()))

    # Check source keys back to staged TSV payload rows, including raw score and QC.
    staged = {}
    for task, stem, score_field, qc_field in TASKS:
        staged[stem] = read_csv(STAGE / f"{stem}.tsv", "\t")
    staged_mismatches = []
    for key, row in source.items():
        match = re.fullmatch(r"phenotype/([^#]+)\.tsv#data-row-(\d+)", row["source_row_reference"])
        if not match or match.group(1) != row["task_table_stem"]:
            staged_mismatches.append("|".join(key) + ":bad_source_reference")
            continue
        index = int(match.group(2)) - 1
        stem, score_field, qc_field = TASK_META[row["task_key"]]
        try:
            original = staged[stem][index]
        except IndexError:
            staged_mismatches.append("|".join(key) + ":row_out_of_range")
            continue
        expected = (row["participant_id"], row["repository_session_id"], normalize_missing(row["original_value"]), normalize_missing(row["raw_qc_codes"]))
        actual = (original["participant_id"], original["session_id"], normalize_missing(original[score_field]), normalize_missing(original[qc_field]))
        if expected != actual:
            staged_mismatches.append("|".join(key) + f":expected={expected}:actual={actual}")

    vf = complete_occasions(source, occasion_keys, continuation, "vf")
    vonly = complete_occasions(source, occasion_keys, continuation, "v")
    ref_ids = sorted(vf)
    primary_ids = sorted(p for p, ss in vf.items() if len(ss) >= 2)
    vonly_ids = sorted(p for p, ss in vonly.items() if len(ss) >= 2)
    primary_sessions = {p: vf[p][:2] for p in primary_ids}
    vonly_sessions = {p: vonly[p][:2] for p in vonly_ids}
    auxiliary_ids = sorted(set(ref_ids) - set(primary_ids))

    def selected_rows(ids, sessions_by_id, stratum):
        rows = []
        for pid in ids:
            for session in sessions_by_id[pid]:
                mapping = mapping_by_key[(pid, session)]
                for task in TASK_KEYS:
                    src = source[(pid, session, task)]
                    rows.append({
                        "participant_id": pid, "session_id": session, "task_key": task,
                        "task_table_stem": src["task_table_stem"], "score_field": src["score_field"],
                        "original_value": src["original_value"], "parsed_numeric_value": src["parsed_numeric_value"],
                        "qc_field": src["applicable_qc_fields"], "raw_qc_code": src["raw_qc_codes"],
                        "source_filename": src["source_filename"], "source_row_reference": src["source_row_reference"],
                        "session_age": src["session_age"], "cognitive_occasion_id": src["cognitive_occasion_id"],
                        "comparability_status": mapping["comparability_status"], "analytical_stratum": stratum,
                    })
        return rows

    ref_sessions = {p: [vf[p][0]] for p in ref_ids}
    reference_rows = selected_rows(ref_ids, ref_sessions, "reference_a")
    primary_rows = selected_rows(primary_ids, primary_sessions, "primary_vf")
    vonly_rows = selected_rows(vonly_ids, vonly_sessions, "vonly_reselected")

    # Fixed-primary-pair strict-V comparison is identity-level and uses both
    # Primary sessions without selecting replacement visits.
    fixed_v_ids = []
    for pid in primary_ids:
        if all(source[(pid, session, task)]["raw_qc_codes"] == "V"
               for session in primary_sessions[pid] for task in TASK_KEYS):
            fixed_v_ids.append(pid)

    pairing_rows = []
    for pid in sorted(set(primary_ids) | set(vonly_ids)):
        ps = primary_sessions.get(pid, [])
        vs = vonly_sessions.get(pid, [])
        pairing_rows.append({
            "participant_id": pid,
            "primary_vf_sessions": ";".join(ps),
            "reselected_strict_v_sessions": ";".join(vs),
            "pair_differs": "yes" if ps and vs and ps != vs else "no",
            "in_reselected_strict_v": "yes" if pid in vonly_ids else "no",
            "in_fixed_primary_pair_strict_v": "yes" if pid in fixed_v_ids else "no",
            "fixed_primary_pair_sessions": ";".join(ps) if pid in fixed_v_ids else "",
        })

    # Candidate identity maps: Design and permutation are separate dimensions.
    rng_a = np.random.default_rng(SEED)
    perm_a = [str(x) for x in rng_a.permuted(np.array(ref_ids))]
    rng_b = np.random.default_rng(SEED)
    perm_b = [str(x) for x in rng_b.permuted(np.array(primary_ids))]
    maps = {
        "A_seeded_reference109": {pid: i % 5 for i, pid in enumerate(perm_a)},
        "A_sorted_round_robin_reference109": {pid: i % 5 for i, pid in enumerate(ref_ids)},
        "B_seeded_targets52_plus_aux57": {pid: i % 5 for i, pid in enumerate(perm_b)},
    }
    identity_rows = []
    for design, fmap in maps.items():
        universe = ref_ids if design.startswith("A_") else primary_ids
        for fold in range(5):
            held = sorted(p for p in universe if fmap[p] == fold)
            if design.startswith("A_"):
                fitting = sorted(set(ref_ids) - set(held))
                auxiliaries = []
            else:
                fitting = sorted((set(primary_ids) - set(held)) | set(auxiliary_ids))
                auxiliaries = auxiliary_ids
            identity_rows.append({
                "candidate_design_id": design, "candidate_status": "candidate_not_approved", "fold": fold,
                "fold_universe_count": len(universe), "target_count": len(primary_ids),
                "auxiliary_count": len(auxiliaries), "held_out_count": len(held), "fitting_count": len(fitting),
                "held_out_identity_list": ";".join(held), "held_out_sha256": identity_hash(held),
                "auxiliary_identity_list": ";".join(auxiliaries), "auxiliary_sha256": identity_hash(auxiliaries),
                "fitting_identity_list": ";".join(fitting), "fitting_sha256": identity_hash(fitting),
                "self_inclusion_count": len(set(held) & set(fitting)),
                "algorithm": "numpy 2.5.2 default_rng(42).permuted(sorted IDs), index modulo 5" if "seeded" in design else "sorted IDs, index modulo 5, no permutation",
            })

    # Compare actual 52-target historical fold manifest to candidate B identities.
    hist_folds = read_csv(ROOT / "chavi_analysis_ds007116_step5adr_correction_20260916/participant_grouped_fold_manifest.csv")
    hist_map = {r["participant_id"]: int(r["fold"]) for r in hist_folds}
    b_matches_historical = hist_map == maps["B_seeded_targets52_plus_aux57"]
    implementation_rows = []
    for name, rel, classification, evidence, counts, finding in HISTORICAL_IMPLEMENTATIONS:
        path = ROOT / rel
        implementation_rows.append({
            "implementation": name, "relative_path": rel, "sha256": sha256_file(path),
            "fold_universe": "109 Reference-A" if classification.startswith("A") else "52 Primary targets",
            "target_identities": "52 Primary", "auxiliary_identities": "57 retained" if classification == "B" else ("none; all Reference-A identities folded" if classification.startswith("A") else "57 dropped"),
            "actual_fitting_design": classification, "expected_training_counts": counts,
            "identity_evidence": evidence, "leakage_and_reference_finding": finding,
            "agreement_with_approval": "partial/ambiguous" if classification == "B" else "no" if classification == "C" else "conflicts with literal seeded wording",
        })

    # Task-specific pairs for 50/52/53 reconciliation.
    task_pairs = {task: {} for task in TASK_KEYS}
    for task in TASK_KEYS:
        by_pid = defaultdict(list)
        for pid, session in occasion_keys:
            row = source.get((pid, session, task))
            if (pid, session) not in continuation and row and finite(row["parsed_numeric_value"]) and row["raw_qc_codes"] in {"V", "F"}:
                by_pid[pid].append(session)
        for pid, sessions in by_pid.items():
            ordered = sorted(set(sessions), key=session_order)
            if len(ordered) >= 2:
                task_pairs[task][pid] = tuple(ordered[:2])
    intersection = set.intersection(*(set(task_pairs[t]) for t in TASK_KEYS))
    aligned = {p for p in intersection if len({task_pairs[t][p] for t in TASK_KEYS}) == 1}

    reconciliation_rows = []
    source_participants = {p for p, _, _ in source}
    for pid in registered:
        reconciliation_rows.append({
            "participant_id": pid, "registered": "yes",
            "present_in_selected_step3b_source": "yes" if pid in source_participants else "no",
            "complete_vf_occasion_count": len(vf.get(pid, [])), "complete_vf_sessions": ";".join(vf.get(pid, [])),
            "reference_a": "yes" if pid in ref_ids else "no", "reference_a_session": vf.get(pid, [""])[0] if pid in vf else "",
            "primary_vf": "yes" if pid in primary_ids else "no", "primary_vf_sessions": ";".join(primary_sessions.get(pid, [])),
            "complete_vonly_occasion_count": len(vonly.get(pid, [])), "complete_vonly_sessions": ";".join(vonly.get(pid, [])),
            "vonly_reselected": "yes" if pid in vonly_ids else "no", "vonly_reselected_sessions": ";".join(vonly_sessions.get(pid, [])),
            "fixed_primary_pair_strict_v": "yes" if pid in fixed_v_ids else "no",
            "task_pair_intersection_53": "yes" if pid in intersection else "no",
            "task_pair_aligned_50": "yes" if pid in aligned else "no",
            "continuation_sessions_excluded": ";".join(sorted(s for p, s in continuation if p == pid)),
        })

    result = {
        "source": {"rows": len(observations), "selected_rows": len(source), "retrieval_manifest_rows": len(retrieval),
                   "payload_hash_or_size_failures": payload_failures, "qc_dictionary_errors": dictionary_errors,
                   "metadata_errors": metadata_errors,
                   "unregistered_identity_errors": unregistered, "missing_mappings": missing_mappings,
                   "vf_upstream_flag_mismatches": vf_mismatch, "strict_v_upstream_flag_mismatches": strict_mismatch,
                   "staged_source_value_qc_mismatches": staged_mismatches},
        "cohorts": {"complete_vf_occasions": sum(map(len, vf.values())), "reference_a_participants": len(ref_ids),
                    "reference_a_rows": len(reference_rows), "primary_participants": len(primary_ids),
                    "primary_occasions": sum(map(len, primary_sessions.values())), "primary_rows": len(primary_rows),
                    "vonly_reselected_participants": len(vonly_ids), "vonly_reselected_occasions": sum(map(len, vonly_sessions.values())),
                    "vonly_reselected_rows": len(vonly_rows), "fixed_primary_pair_strict_v_participants": len(fixed_v_ids),
                    "fixed_primary_pair_strict_v_occasions": 2 * len(fixed_v_ids), "fixed_primary_pair_strict_v_rows": 10 * len(fixed_v_ids),
                    "task_pair_intersection": len(intersection), "task_pair_aligned": len(aligned),
                    "changed_vonly_pairs": sorted(r["participant_id"] for r in pairing_rows if r["pair_differs"] == "yes")},
        "crossfit": {"design_b_map_matches_historical_52_target_manifest": b_matches_historical,
                     "vonly_identities_are_subset_of_primary_targets": set(vonly_ids) <= set(primary_ids),
                     "candidate_fold_counts": {d: [sum(v == f for v in m.values()) for f in range(5)] for d, m in maps.items()}},
        "environment": {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
                        "executable": sys.executable, "platform": platform.platform(), "numpy": np.__version__},
    }
    result["readiness_gate"] = consolidated_gate(result)
    return {"result": result, "reference_rows": reference_rows, "primary_rows": primary_rows,
            "vonly_rows": vonly_rows, "pairing_rows": pairing_rows, "identity_rows": identity_rows,
            "implementation_rows": implementation_rows, "reconciliation_rows": reconciliation_rows}


def consolidated_gate(result: dict) -> dict:
    source = result["source"]
    c = result["cohorts"]
    failures = []
    for name in ("payload_hash_or_size_failures", "qc_dictionary_errors", "metadata_errors", "unregistered_identity_errors", "missing_mappings", "vf_upstream_flag_mismatches", "strict_v_upstream_flag_mismatches", "staged_source_value_qc_mismatches"):
        if source[name]:
            failures.append(name)
    expected = {"complete_vf_occasions": 176, "reference_a_participants": 109, "reference_a_rows": 545,
                "primary_participants": 52, "primary_occasions": 104, "primary_rows": 520,
                "vonly_reselected_participants": 45, "vonly_reselected_occasions": 90, "vonly_reselected_rows": 450,
                "task_pair_intersection": 53, "task_pair_aligned": 50}
    for key, value in expected.items():
        if c[key] != value:
            failures.append(f"{key}:expected={value}:actual={c[key]}")
    if c["changed_vonly_pairs"] != ["sub-20149", "sub-20310", "sub-20902", "sub-20916"]:
        failures.append("changed_vonly_pair_identities")
    return {"computational_gate_passed": not failures, "failures": failures,
            "unresolved_scientific_decisions": ["crossfit_design_A_vs_B", "candidate_identity_map_approval", "bootstrap_protocol_approval"],
            "expected_candidate_disagreement": ["A_seeded_vs_A_sorted_round_robin"]}


def protected_paths() -> list[Path]:
    paths = []
    prior_inputs = read_csv(PRIOR / "input_artifact_manifest.csv")
    paths.extend(ROOT / r["relative_path"] for r in prior_inputs)
    paths.extend(p for p in PRIOR.iterdir() if p.is_file())
    paths.append(ROOT / "chavi_recovery_preflight_20261001.zip")
    extra = [rel for _, rel, *_ in HISTORICAL_IMPLEMENTATIONS]
    extra += [
        "chavi_analysis_ds007116_step5ba_transformed_data_20260916/transformation_parameters.csv",
        "chavi_analysis_ds007116_step5ba_transformed_data_20260916/transformed_task_observations_long.csv",
        "chavi_analysis_ds007116_step5bar2_independent_review_20260916/transformation_parameters.csv",
        "chavi_analysis_ds007116_step5bar2_independent_review_20260916/transformed_task_observations_long.csv",
        "chavi_analysis_ds007116_step5bar3_final_validation_20260916/stratified_transformed_rows.csv",
    ]
    paths.extend(ROOT / rel for rel in extra)
    return sorted(set(p.resolve() for p in paths))


def hash_snapshot(paths: list[Path]) -> dict[str, tuple[int, str]]:
    return {str(p.relative_to(ROOT)).replace("\\", "/"): (p.stat().st_size, sha256_file(p)) for p in paths if p.is_file()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args()
    derived = derive()
    result = derived["result"]
    if args.verify_existing:
        stored = json.loads((OUT / "reconstruction_results_corrected.json").read_text(encoding="utf-8"))
        # Runtime metadata is expected to differ; all scientific content must match.
        stored_noenv = {k: v for k, v in stored.items() if k != "environment"}
        result_noenv = {k: v for k, v in result.items() if k != "environment"}
        if stored_noenv != result_noenv:
            raise AssertionError("fresh-process reconstruction differs")
        print(json.dumps({"fresh_process_reconstruction_match": True, "readiness_gate": result["readiness_gate"]}, indent=2))
        return 0

    paths = protected_paths()
    before = hash_snapshot(paths)
    write_csv(OUT / "reference_a_source_rows.csv", derived["reference_rows"])
    write_csv(OUT / "primary_vf_source_rows.csv", derived["primary_rows"])
    write_csv(OUT / "vonly_source_rows.csv", derived["vonly_rows"])
    write_csv(OUT / "qc_pairing_sensitivity_identity_comparison.csv", derived["pairing_rows"])
    write_csv(OUT / "crossfit_candidate_identity_maps.csv", derived["identity_rows"])
    write_csv(OUT / "crossfit_design_and_implementation_comparison.csv", derived["implementation_rows"])
    write_csv(OUT / "corrected_source_cohort_reconciliation.csv", derived["reconciliation_rows"])
    (OUT / "reconstruction_results_corrected.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    after = hash_snapshot(paths)
    hash_rows = []
    for rel in sorted(set(before) | set(after)):
        b, a = before.get(rel), after.get(rel)
        hash_rows.append({"relative_path": rel, "scope": "declared_prior_input_or_protected_preflight/transformation_artifact",
                          "before_size_bytes": b[0] if b else "", "before_sha256": b[1] if b else "",
                          "after_size_bytes": a[0] if a else "", "after_sha256": a[1] if a else "",
                          "unchanged": "yes" if b == a and b is not None else "no"})
    write_csv(OUT / "historical_artifact_before_after_hashes.csv", hash_rows)
    print(json.dumps(result, indent=2))
    return 0 if result["readiness_gate"]["computational_gate_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
