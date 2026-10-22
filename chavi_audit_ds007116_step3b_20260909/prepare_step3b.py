from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import platform
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SNAPSHOT = "1.0.6"
COMMIT = "fc7dc36fa2598b0b2e4579baef37d148cc085207"
TASKS = {
    "letter_nback": ("short_letter_2back", "cnb_lnb_mcr", "Letter n-back"),
    "face_memory": ("penn_face_memory_test", "cnb_cpf_cr", "Face memory"),
    "matrix_reasoning": ("penn_matrix_reasoning_test", "cnb_pmat_cr", "Matrix reasoning"),
    "emotion_recognition": ("penn_emotion_recognition_task", "cnb_er40_cr", "Emotion recognition"),
    "dominant_finger_tapping": ("short_computerized_finger_tapping_task", "cnb_ctap_dom", "Dominant-hand finger tapping"),
}
OUTCOMES = {
    "eswan_adhd_inattention_total": "E-SWAN inattention total",
    "eswan_adhd_total_score": "E-SWAN total score",
    "mapssr_total_score": "MAPS-SR total score",
    "im_average": "Wolf intrinsic motivation average",
    "em_average": "Wolf extrinsic motivation average",
}
POLICIES = (
    "unfiltered_observed",
    "documented_valid_or_likely_valid",
    "strict_documented_V_only",
    "descriptive_unresolved_qc",
    "unresolved_inclusive",
)
PAIR_RULES = ("first_two_eligible_occasions", "complete_scheduled_ses-1_ses-2_pairs")


def load_audit(path: Path):
    spec = importlib.util.spec_from_file_location("chavi_step3a_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load Step 3A audit script: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def as_num(audit, value: Any) -> tuple[str, str]:
    if audit.is_missing(value):
        return "", "missing"
    try:
        return str(float(str(value).strip())), "numeric"
    except (TypeError, ValueError):
        return "", "unparseable_non_numeric"


def session_number(session_id: str) -> tuple[int, str]:
    if str(session_id).startswith("ses-"):
        try:
            return int(str(session_id)[4:]), str(session_id)
        except ValueError:
            pass
    return 10**9, str(session_id)


def parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def interval_info(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    a, b = parse_time(first.get("rounded_acq_time")), parse_time(second.get("rounded_acq_time"))
    if a is None or b is None:
        return {"nominal_interval_days": "", "timing_status": "missing_or_unparseable_acq_time", "timing_caveat": "session labels provide nominal order; acquisition time unavailable or unparseable; timestamps are rounded/anonymized"}
    delta = (b - a).total_seconds() / 86400
    if delta <= 0:
        return {"nominal_interval_days": str(delta), "timing_status": "nonpositive_acq_time_interval", "timing_caveat": "nonpositive rounded/anonymized acquisition-time difference; do not interpret as a valid elapsed interval"}
    return {"nominal_interval_days": str(delta), "timing_status": "available_from_rounded_acq_time", "timing_caveat": "rounded/anonymized acquisition time; not exact cognitive-assessment time"}


def occasion_map(audit, dataset: Path, payloads: dict[str, Any], participant_rows: list[dict[str, str]], session_rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, Any]]:
    rows = audit.s2_occasion_rows(payloads, session_rows, participant_rows)
    return {(r["participant_id"], r["original_session_id"]): r for r in rows}


def qc_details(audit, task: str, row: dict[str, str], payload: dict[str, Any]) -> dict[str, str]:
    qcf = audit.s2_qc_fields(payload["fields"])
    q = audit.b_qc_status(task, row, qcf, payload["meta"])
    meanings = []
    for field in qcf:
        raw = str(row.get(field, "")).strip()
        if audit.is_missing(raw):
            meanings.append(f"{field}=<missing QC value>")
        else:
            meanings.append(f"{field}={audit.s2_levels(payload['meta'], field).get(raw, 'not documented locally')}")
    classes = audit.b_policy_classes(q)
    return {
        "applicable_qc_fields": ";".join(qcf) or "none documented",
        "raw_qc_codes": ";".join(q["codes"]) or "",
        "qc_status": q["status"],
        "qc_classes": ";".join(classes) or "",
        "documented_qc_meanings": " | ".join(meanings) or "no applicable QC field",
        "qc_interpretation_status": "documented" if classes and all(c in {"documented_valid", "documented_likely_valid", "documented_invalid", "documented_likely_invalid", "documented_skipped"} for c in classes) else "unresolved_or_missing",
    }


def task_rows(audit, payloads: dict[str, Any], occasions: dict[tuple[str, str], dict[str, Any]], stage: Path) -> tuple[list[dict[str, Any]], dict[tuple[str, str, str, str], dict[str, Any]], dict[tuple[str, str, str], list[dict[str, Any]]]]:
    out: list[dict[str, Any]] = []
    lookup: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    duplicate_keys: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for task_key, (task, field, label) in TASKS.items():
        payload = payloads[task]
        qcf = audit.s2_qc_fields(payload["fields"])
        source_tsv = f"phenotype/{task}.tsv"
        for row_number, source_row in enumerate(payload["rows"], start=1):
            pid, ses = source_row.get("participant_id", ""), source_row.get("session_id", "")
            key = (pid, ses, task, field)
            duplicate_keys[(pid, ses, task)].append(source_row)
            original = source_row.get(field, "")
            parsed, parse_status = as_num(audit, original)
            miss = audit.s2_missing_category(original, payload["meta"], field)
            if parse_status == "unparseable_non_numeric":
                miss = "non_numeric_observed_value"
            qc = qc_details(audit, task, source_row, payload)
            occ = occasions.get((pid, ses), {})
            row = {
                "participant_id": pid,
                "repository_session_id": ses,
                "cognitive_occasion_id": occ.get("proposed_cognitive_occasion_id", f"{pid}_cognitive_{ses}_unmapped"),
                "occasion_mapping_status": occ.get("comparability_status", "no occasion mapping row"),
                "task_key": task_key,
                "task_label": label,
                "task_table_stem": task,
                "score_field": field,
                "original_value": original,
                "parsed_numeric_value": parsed,
                "parse_status": parse_status,
                "missingness_category": miss,
                "documented_units": (payload["meta"].get(field, {}) or {}).get("Units", "") if isinstance(payload["meta"].get(field, {}), dict) else "",
                "interpretation_status": audit.b_review(task, field)[6],
                "raw_score_interpretation": audit.b_review(task, field)[4],
                "timing_source": occ.get("available_timing_age_source", ""),
                "session_age": occ.get("session_age", ""),
                "rounded_acq_time": occ.get("rounded_acq_time", ""),
                "timing_caveat": "session age/acq_time are available only where session sidecar exists; acq_time is rounded/anonymized and not exact cognitive timing",
                "comparability_status": occ.get("comparability_status", "unresolved"),
                "comparability_caveat": occ.get("unresolved_ambiguity", "task version, administration conditions, and exact cognitive timing remain unresolved"),
                "source_filename": source_tsv,
                "source_row_reference": f"{source_tsv}#data-row-{row_number}",
                **qc,
            }
            for policy in POLICIES:
                if audit.is_missing(original):
                    eligible, reason = False, "missing_selected_score"
                else:
                    eligible, reason = audit.b_eligible(task, source_row, qcf, policy, payload["meta"])
                row[f"eligible_{policy}"] = "yes" if eligible else "no"
                row[f"eligibility_reason_{policy}"] = reason
            out.append(row)
            lookup[key] = row
    dup = {k: v for k, v in duplicate_keys.items() if len(v) > 1}
    return out, lookup, dup


def eligible_keys(rows: list[dict[str, Any]], task_key: str, policy: str) -> set[tuple[str, str]]:
    return {(r["participant_id"], r["repository_session_id"]) for r in rows if r["task_key"] == task_key and r[f"eligible_{policy}"] == "yes"}


def pairs_for_keys(keys: set[tuple[str, str]], rule: str) -> list[tuple[str, str, str]]:
    by_pid: dict[str, list[str]] = defaultdict(list)
    for pid, ses in keys:
        by_pid[pid].append(ses)
    pairs = []
    for pid, sessions in sorted(by_pid.items()):
        sessions = sorted(set(sessions), key=session_number)
        if rule == "first_two_eligible_occasions" and len(sessions) >= 2:
            pairs.append((pid, sessions[0], sessions[1]))
        elif rule == "complete_scheduled_ses-1_ses-2_pairs" and {"ses-1", "ses-2"}.issubset(sessions):
            pairs.append((pid, "ses-1", "ses-2"))
    return pairs


def paired_task_rows(lookup: dict[tuple[str, str, str, str], dict[str, Any]], task_rows_all: list[dict[str, Any]], occasions: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for task_key, (task, field, label) in TASKS.items():
        for policy in POLICIES:
            keys = eligible_keys(task_rows_all, task_key, policy)
            for rule in PAIR_RULES:
                for pid, first, second in pairs_for_keys(keys, rule):
                    a = lookup[(pid, first, task, field)]
                    b = lookup[(pid, second, task, field)]
                    timing = interval_info(occasions.get((pid, first), {}), occasions.get((pid, second), {}))
                    rows.append({
                        "participant_id": pid, "task_key": task_key, "task_label": label, "task_table_stem": task, "score_field": field,
                        "qc_policy": policy, "pairing_rule": rule,
                        "first_occasion_id": a["cognitive_occasion_id"], "second_occasion_id": b["cognitive_occasion_id"],
                        "first_session_id": first, "second_session_id": second,
                        "first_original_value": a["original_value"], "second_original_value": b["original_value"],
                        "first_parsed_numeric_value": a["parsed_numeric_value"], "second_parsed_numeric_value": b["parsed_numeric_value"],
                        "first_eligibility_reason": a[f"eligibility_reason_{policy}"], "second_eligibility_reason": b[f"eligibility_reason_{policy}"],
                        "first_qc_status": a["qc_status"], "second_qc_status": b["qc_status"],
                        "nominal_interval_days": timing["nominal_interval_days"], "timing_status": timing["timing_status"], "timing_caveat": timing["timing_caveat"],
                        "first_comparability_status": a["comparability_status"], "second_comparability_status": b["comparability_status"],
                        "first_source_row_reference": a["source_row_reference"], "second_source_row_reference": b["source_row_reference"],
                        "participant_pair_key": f"{pid}|{task_key}|{policy}|{rule}",
                    })
    return rows


def profile_manifest(audit, task_rows_all: list[dict[str, Any]], occasions: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    profile_json = json.dumps({k: f"{task}:{field}" for k, (task, field, _) in TASKS.items()}, sort_keys=True)
    for policy in POLICIES:
        sets = [eligible_keys(task_rows_all, task_key, policy) for task_key in TASKS]
        keys = set.intersection(*sets)
        for rule in PAIR_RULES:
            for pid, first, second in pairs_for_keys(keys, rule):
                timing = interval_info(occasions.get((pid, first), {}), occasions.get((pid, second), {}))
                rows.append({
                    "participant_id": pid, "profile_id": "fixed_five_task_candidate_profile", "qc_policy": policy, "pairing_rule": rule,
                    "first_occasion_id": occasions.get((pid, first), {}).get("proposed_cognitive_occasion_id", f"{pid}_{first}"),
                    "second_occasion_id": occasions.get((pid, second), {}).get("proposed_cognitive_occasion_id", f"{pid}_{second}"),
                    "first_session_id": first, "second_session_id": second,
                    "selected_task_fields_json": profile_json, "task_identity_rule": "same five exact task/field identities required at both occasions; no same-domain substitution",
                    "nominal_interval_days": timing["nominal_interval_days"], "timing_status": timing["timing_status"], "timing_caveat": timing["timing_caveat"],
                    "comparability_status": "nominally pairable; task version/conditions and exact cognitive timing unresolved",
                    "participant_pair_key": f"{pid}|fixed_five_task_candidate_profile|{policy}|{rule}",
                    "analysis_status": "candidate cohort manifest; not an approved profile or inferential cohort",
                })
    return rows


def outcome_rows(audit, payloads: dict[str, Any], occasions: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for field, label in OUTCOMES.items():
        stem = audit.OUTCOME_SPECS[field][0]
        payload = payloads[stem]
        for row_number, source_row in enumerate(payload["rows"], start=1):
            pid, ses = source_row.get("participant_id", ""), source_row.get("session_id", "")
            original = source_row.get(field, "")
            parsed, parse_status = as_num(audit, original)
            miss = audit.s2_missing_category(original, payload["meta"], field)
            if parse_status == "unparseable_non_numeric":
                miss = "non_numeric_observed_value"
            occ = occasions.get((pid, ses), {})
            rows.append({
                "participant_id": pid, "repository_session_id": ses, "outcome_variable": field, "outcome_label": label,
                "outcome_table_stem": stem, "raw_value": original, "parsed_numeric_value": parsed, "parse_status": parse_status,
                "missingness_category": miss, "documented_units": (payload["meta"].get(field, {}) or {}).get("Units", "") if isinstance(payload["meta"].get(field, {}), dict) else "",
                "session_age": occ.get("session_age", ""), "rounded_acq_time": occ.get("rounded_acq_time", ""),
                "timing_source": occ.get("available_timing_age_source", ""), "timing_caveat": "session label is nominal chronology; acq_time is rounded/anonymized and not exact outcome timing",
                "source_filename": f"phenotype/{stem}.tsv", "source_row_reference": f"phenotype/{stem}.tsv#data-row-{row_number}",
                "outcome_direction_status": "not frozen; review respondent, version, coding and construct direction before prediction",
            })
    return rows


def candidate_prediction_rows(audit, task_rows_all: list[dict[str, Any]], outcomes: list[dict[str, Any]], occasions: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    all_cognitive_baseline = {r["participant_id"] for r in task_rows_all if r["repository_session_id"] == "ses-1" and r["parse_status"] == "numeric" and r["task_table_stem"] in audit.STEP2_PRIMARY and r["score_field"] in audit.STEP2_PRIMARY[r["task_table_stem"]]}
    profile_by_policy = {}
    for policy in POLICIES:
        sets = [eligible_keys(task_rows_all, task_key, policy) for task_key in TASKS]
        profile_by_policy[policy] = set.intersection(*sets)
    out_by_field: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in outcomes:
        if row["parse_status"] == "numeric":
            out_by_field[row["outcome_variable"]].append(row)
    participant_ids = sorted({r["participant_id"] for r in task_rows_all} | {r["participant_id"] for r in outcomes})
    rows = []
    for policy in POLICIES:
        for field, label in OUTCOMES.items():
            obs = out_by_field[field]
            base = {r["participant_id"]: r for r in obs if r["repository_session_id"] == "ses-1"}
            later: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for r in obs:
                if r["repository_session_id"] != "ses-1":
                    later[r["participant_id"]].append(r)
            for pid in participant_ids:
                profile_base = (pid, "ses-1") in profile_by_policy[policy]
                later_rows = sorted(later.get(pid, []), key=lambda r: session_number(r["repository_session_id"]))
                selected = later_rows[0] if later_rows else None
                base_occ = occasions.get((pid, "ses-1"), {})
                chrono = "not_available"
                if selected:
                    later_occ = occasions.get((pid, selected["repository_session_id"]), {})
                    base_dt, later_dt = parse_time(base_occ.get("rounded_acq_time")), parse_time(later_occ.get("rounded_acq_time"))
                    if session_number(selected["repository_session_id"])[0] > 1:
                        chrono = "supported_by_session_label; exact timestamp unavailable" if base_dt is None or later_dt is None else ("supported_by_session_label_and_positive_timestamp" if later_dt > base_dt else "ambiguous_nonpositive_timestamp_despite_later_session_label")
                    else:
                        chrono = "ambiguous_session_order"
                final = bool(profile_base and pid in base and selected and chrono != "not_available")
                exact_interval = ""
                if selected:
                    exact_interval = interval_info(base_occ, occasions.get((pid, selected["repository_session_id"]), {}))["nominal_interval_days"]
                rows.append({
                    "participant_id": pid, "outcome_variable": field, "outcome_label": label, "qc_policy": policy,
                    "baseline_cognitive_available_unfiltered": "yes" if pid in all_cognitive_baseline else "no",
                    "baseline_complete_profile_available": "yes" if profile_base else "no",
                    "baseline_outcome_available": "yes" if pid in base else "no",
                    "later_outcome_available": "yes" if later_rows else "no",
                    "earliest_later_outcome_session_id": selected["repository_session_id"] if selected else "",
                    "earliest_later_outcome_source_row_reference": selected["source_row_reference"] if selected else "",
                    "earliest_later_outcome_raw_value": selected["raw_value"] if selected else "",
                    "chronology_status": chrono,
                    "nominal_interval_days_if_available": exact_interval,
                    "final_candidate_intersection": "yes" if final else "no",
                    "candidate_rule_status": "PROPOSED—NOT APPROVED; ses-1 baseline and earliest subsequent observed outcome",
                    "timing_caveat": "session labels are used for nominal ordering; exact cognitive/questionnaire timing is unresolved and no false precision is assigned",
                    "alternative_later_observations": "retained in outcome_observations_long.csv",
                })
    return rows


def reconciliation(audit, task_rows_all: list[dict[str, Any]], paired_tasks: list[dict[str, Any]], profile: list[dict[str, Any]], candidates: list[dict[str, Any]], outcomes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    expected = {
        "unfiltered_observed": {"occasions": 202, "participants": 123, "repeated_participants": 63, "first_pairs": 63, "scheduled_pairs": 60},
        "documented_valid_or_likely_valid": {"occasions": 176, "participants": 109, "repeated_participants": 52, "first_pairs": 52, "scheduled_pairs": 48},
        "strict_documented_V_only": {"occasions": 157, "participants": 101, "repeated_participants": 45, "first_pairs": 45, "scheduled_pairs": 39},
    }
    for policy in POLICIES:
        sets = [eligible_keys(task_rows_all, k, policy) for k in TASKS]
        fixed = set.intersection(*sets)
        observed = len(fixed); participants = len({p for p, _ in fixed}); repeated = len({p for p, _ in fixed if sum(x == p for x, _ in fixed) >= 2})
        first = len([r for r in profile if r["qc_policy"] == policy and r["pairing_rule"] == PAIR_RULES[0]])
        scheduled = len([r for r in profile if r["qc_policy"] == policy and r["pairing_rule"] == PAIR_RULES[1]])
        for metric, value in (("eligible_fixed_profile_occasions", observed), ("eligible_fixed_profile_participants", participants), ("repeated_fixed_profile_participants", repeated), ("first_two_fixed_profile_pairs", first), ("complete_scheduled_fixed_profile_pairs", scheduled)):
            bench_key = {"eligible_fixed_profile_occasions":"occasions", "eligible_fixed_profile_participants":"participants", "repeated_fixed_profile_participants":"repeated_participants", "first_two_fixed_profile_pairs":"first_pairs", "complete_scheduled_fixed_profile_pairs":"scheduled_pairs"}[metric]
            bench = expected.get(policy, {}).get(bench_key, "")
            rows.append({"cohort": "fixed_five_task_candidate_profile", "qc_policy": policy, "pairing_rule": "not applicable" if "pairs" not in metric else (PAIR_RULES[0] if "first" in metric else PAIR_RULES[1]), "metric": metric, "observed_count": value, "step3a_benchmark": bench, "reconciles": "yes" if bench == "" or value == bench else "no", "source_or_rule": "task_observations_long.csv exact five-task intersection; profile manifest; Step 3A fixed-profile benchmark", "note": "Feasibility/accounting only; not an inferential sample-size claim."})
    for field in OUTCOMES:
        for policy in POLICIES:
            subset = [r for r in candidates if r["outcome_variable"] == field and r["qc_policy"] == policy]
            count = sum(r["final_candidate_intersection"] == "yes" for r in subset)
            rows.append({"cohort": "candidate_prediction_cohort", "qc_policy": policy, "pairing_rule": "ses-1 baseline + earliest subsequent observed outcome", "metric": f"final_candidate_intersection:{field}", "observed_count": count, "step3a_benchmark": "", "reconciles": "yes", "source_or_rule": "candidate_prediction_cohort.csv; no model run", "note": "Candidate follow-up rule is explicitly proposed, not approved."})
    rows.append({"cohort": "task_observations_long", "qc_policy": "all", "pairing_rule": "not applicable", "metric": "rows", "observed_count": len(task_rows_all), "step3a_benchmark": "", "reconciles": "yes", "source_or_rule": "five staged TSVs; one source row per selected field", "note": "Includes missing selected scores to preserve source-level missingness."})
    rows.append({"cohort": "paired_task_observations", "qc_policy": "all", "pairing_rule": "first-two and complete scheduled", "metric": "rows", "observed_count": len(paired_tasks), "step3a_benchmark": "", "reconciles": "yes", "source_or_rule": "task-specific eligible-key sets and explicit pair rules", "note": "Task-specific cohorts remain distinct from complete-profile pairs."})
    rows.append({"cohort": "outcome_observations_long", "qc_policy": "not applicable", "pairing_rule": "not applicable", "metric": "rows", "observed_count": len(outcomes), "step3a_benchmark": "", "reconciles": "yes", "source_or_rule": "five audited outcome fields in staged TSVs", "note": "No outcome filtering beyond raw numeric/missingness preservation."})
    return rows


def data_dictionary() -> list[dict[str, str]]:
    groups = {
        "task_observations_long.csv": {
            "participant_id": "Repository participant identifier; join key, not a predictor.", "repository_session_id": "Repository session identifier; not automatically a cognitive occasion.", "cognitive_occasion_id": "Step 3A proposed cognitive occasion identifier.", "occasion_mapping_status": "Step 3A occasion/comparability status.", "task_key": "Narrow CHAVI task label key.", "task_label": "Narrow task label; not a validated broad domain.", "task_table_stem": "Pinned phenotype table stem.", "score_field": "Exact selected released score field.", "original_value": "Untouched source-cell string.", "parsed_numeric_value": "Numeric parse of original value; no transformation.", "parse_status": "numeric, missing, or unparseable_non_numeric.", "missingness_category": "Source-aware missingness category.", "documented_units": "Units copied from local dictionary where present.", "interpretation_status": "Reviewed interpretation caveat; not a validation claim.", "raw_score_interpretation": "Narrow documented/local interpretation.", "timing_source": "Session age/acq_time source description.", "session_age": "Session-sidecar age where available.", "rounded_acq_time": "Rounded/anonymized acquisition time where available.", "timing_caveat": "Timing limitation.", "comparability_status": "Step 3A comparability status.", "comparability_caveat": "Unresolved version/condition/timing caveat.", "source_filename": "Repository-relative source filename.", "source_row_reference": "Repository-relative source file and one-based data-row reference.", "applicable_qc_fields": "QC fields present in source table.", "raw_qc_codes": "Raw QC code values.", "qc_status": "all_present, partial_missing, missing_qc, or no_qc_field.", "qc_classes": "Exact dictionary-derived QC classes.", "documented_qc_meanings": "Exact dictionary meanings by QC field.", "qc_interpretation_status": "Documented versus unresolved/missing.", "eligible_<policy>": "yes/no eligibility under a configured policy.", "eligibility_reason_<policy>": "Policy decision reason/codes."},
        "paired_task_observations.csv": {
            "participant_id": "Participant-level dependence unit.", "task_key": "Narrow task identifier.", "task_label": "Narrow task label.", "task_table_stem": "Source phenotype table stem.", "score_field": "Exact score field shared across both observations.", "qc_policy": "Configured eligibility policy.", "pairing_rule": "First-two eligible or complete scheduled ses-1/ses-2.", "first_occasion_id": "First observation occasion identifier.", "second_occasion_id": "Second observation occasion identifier.", "first_session_id": "First repository session.", "second_session_id": "Second repository session.", "first_original_value": "First raw source-cell string.", "second_original_value": "Second raw source-cell string.", "first_parsed_numeric_value": "First raw numeric parse.", "second_parsed_numeric_value": "Second raw numeric parse.", "first_eligibility_reason": "First policy reason.", "second_eligibility_reason": "Second policy reason.", "first_qc_status": "First QC status.", "second_qc_status": "Second QC status.", "nominal_interval_days": "Difference between rounded/anonymized acquisition times where positive and parseable.", "timing_status": "Timing availability/validity status.", "timing_caveat": "Interval interpretation caveat.", "first_comparability_status": "First occasion status.", "second_comparability_status": "Second occasion status.", "first_source_row_reference": "First raw source row.", "second_source_row_reference": "Second raw source row.", "participant_pair_key": "Unique participant/task/policy/rule pair key."},
        "paired_profile_manifest.csv": {
            "participant_id": "Participant-level dependence unit.", "profile_id": "Fixed five exact task/field candidate profile identifier.", "qc_policy": "Configured eligibility policy.", "pairing_rule": "First-two eligible or complete scheduled pair.", "first_occasion_id": "First profile occasion.", "second_occasion_id": "Second profile occasion.", "first_session_id": "First repository session.", "second_session_id": "Second repository session.", "selected_task_fields_json": "Exact five task/field identities; no substitution.", "task_identity_rule": "Completeness rule.", "nominal_interval_days": "Nominal rounded/acq_time interval.", "timing_status": "Timing status.", "timing_caveat": "Timing limitation.", "comparability_status": "Profile comparability limitation.", "participant_pair_key": "Unique participant/profile/policy/rule key.", "analysis_status": "Candidate manifest only."},
        "outcome_observations_long.csv": {
            "participant_id": "Participant join key.", "repository_session_id": "Outcome repository session.", "outcome_variable": "Exact audited outcome field.", "outcome_label": "Narrow outcome label.", "outcome_table_stem": "Outcome table stem.", "raw_value": "Untouched source-cell string.", "parsed_numeric_value": "Numeric parse only.", "parse_status": "Numeric/missing/unparseable status.", "missingness_category": "Source-aware missingness.", "documented_units": "Dictionary units if present.", "session_age": "Session-sidecar age if available.", "rounded_acq_time": "Rounded/anonymized acquisition time.", "timing_source": "Timing source description.", "timing_caveat": "Outcome timing caveat.", "source_filename": "Repository-relative source filename.", "source_row_reference": "One-based source row reference.", "outcome_direction_status": "Direction/respondent/version remains to be reviewed."},
        "candidate_prediction_cohort.csv": {
            "participant_id": "Participant join and validation unit.", "outcome_variable": "Candidate outcome field.", "outcome_label": "Candidate outcome label.", "qc_policy": "Baseline profile policy.", "baseline_cognitive_available_unfiltered": "Any selected primary cognitive field at ses-1, unfiltered.", "baseline_complete_profile_available": "All five exact fields at ses-1 under policy.", "baseline_outcome_available": "Numeric outcome at ses-1.", "later_outcome_available": "Numeric outcome on any non-ses-1 session.", "earliest_later_outcome_session_id": "Earliest nominal later session selected for candidate row.", "earliest_later_outcome_source_row_reference": "Selected later outcome source row.", "earliest_later_outcome_raw_value": "Selected later raw value.", "chronology_status": "Nominal chronology and timestamp caveat.", "nominal_interval_days_if_available": "Positive rounded/acq_time interval only; not exact assessment timing.", "final_candidate_intersection": "Baseline profile + baseline outcome + later outcome + nominal chronology.", "candidate_rule_status": "Explicitly proposed, not approved.", "timing_caveat": "No false precision; session labels are nominal.", "alternative_later_observations": "Pointer to full long table."},
    }
    row_units = {
        "task_observations_long.csv": "participant × repository session × fixed task × selected score source row",
        "paired_task_observations.csv": "participant × task × QC policy × pair rule",
        "paired_profile_manifest.csv": "participant × fixed five-task profile × QC policy × pair rule",
        "outcome_observations_long.csv": "participant × repository session × outcome field source row",
        "candidate_prediction_cohort.csv": "participant × outcome × baseline-profile QC policy",
    }
    rows = []
    for table, fields in groups.items():
        for field, description in fields.items():
            rows.append({"table_name": table, "field_name": field, "row_unit": row_units[table], "description": description, "status": "preparation field; not an inferential result", "traceability": "source row, Step 3A occasion map, executable policy, or deterministic cohort rule"})
    return rows


def focused_tests(audit, spec: dict[str, Any], task_rows_all: list[dict[str, Any]], paired_tasks: list[dict[str, Any]], profile: list[dict[str, Any]], occasions: dict[tuple[str, str], dict[str, Any]], duplicates: dict[tuple[str, str, str], list[dict[str, Any]]]) -> list[str]:
    audit.ACTIVE_SPEC = spec
    audit_tests = audit.b_fixture_tests()
    if audit_tests["status"] != "passed":
        raise AssertionError("Step 3A fixture tests did not pass")
    if duplicates:
        raise AssertionError(f"Duplicate analytical task keys found: {list(duplicates)[:5]}")
    # A policy edit must change eligibility in the exact-meaning fixture.
    meta = {"q": {"Levels": {"V": "Valid", "F": "Likely valid, problem occurred which affected performance for a limited number of responses/mild to moderate effect", "N": "Not Valid"}}}
    row = {"score": "1", "q": "F"}
    old = dict(spec["qc_policies"]["documented_valid_or_likely_valid"])
    old_result = audit.b_eligible("fixture", row, ["q"], "documented_valid_or_likely_valid", meta)[0]
    spec["qc_policies"]["documented_valid_or_likely_valid"] = {"include": ["documented_valid"], "require_all_applicable_fields": True}
    changed_result = audit.b_eligible("fixture", row, ["q"], "documented_valid_or_likely_valid", meta)[0]
    spec["qc_policies"]["documented_valid_or_likely_valid"] = old
    if not old_result or changed_result:
        raise AssertionError("Configured policy change did not change fixture eligibility")
    accepted_classes = {"documented_valid", "documented_likely_valid"}
    for row in task_rows_all:
        if row["eligible_documented_valid_or_likely_valid"] == "yes" and any(c not in accepted_classes for c in row["qc_classes"].split(";") if c):
            raise AssertionError("Unresolved or invalid QC was silently accepted by recommended policy")
    # Pair rows are grouped by participant and profile task identities are fixed.
    if any(not r["participant_pair_key"].startswith(r["participant_id"] + "|") for r in paired_tasks):
        raise AssertionError("Pair key does not retain participant grouping")
    for r in profile:
        selected = json.loads(r["selected_task_fields_json"])
        if set(selected) != set(TASKS):
            raise AssertionError("Profile manifest task identity changed")
    continuation = occasions.get(("sub-20812", "ses-2"))
    if not continuation or continuation.get("comparability_status") != "documented continuation; no separate CNB occasion":
        raise AssertionError("Continuation protection missing")
    return ["step3a_fixture_tests", "no_duplicate_task_analytical_keys", "configured_policy_change_changes_eligibility", "unresolved_qc_not_silently_accepted", "participant_grouped_pair_keys", "fixed_task_identity", "continuation_cannot_create_new_CNB_occasion"]


def input_hashes(audit, dataset: Path, stage: Path, payloads: dict[str, Any], spec_path: Path) -> list[dict[str, Any]]:
    files: list[tuple[str, Path, str]] = []
    for task, payload in sorted(payloads.items()):
        files.append((f"staged/{task}.tsv", Path(payload["path"]), "verified Step 1B phenotype payload"))
    for task, _, _ in TASKS.values():
        files.append((f"dataset/phenotype/{task}.json", dataset / "phenotype" / f"{task}.json", "selected source dictionary"))
    for name in ("participants.tsv", "participants.json"):
        files.append((f"dataset/{name}", dataset / name, "participant metadata"))
    for path in sorted(dataset.glob("sub-*/sub-*_sessions.tsv")):
        files.append((f"dataset/{path.relative_to(dataset)}", path, "session age/acq_time metadata"))
    files.append(("step3a/step3a_specification.json", spec_path, "executable input specification"))
    rows = []
    for logical, path, role in files:
        rows.append({"logical_path": logical, "absolute_path": str(path.resolve()), "role": role, "exists": "yes" if path.is_file() else "no", "size_bytes": path.stat().st_size if path.is_file() else "", "sha256": sha256(path) if path.is_file() else ""})
    return rows


def provenance(audit, out: Path, dataset: Path, stage: Path, spec_path: Path, payloads: dict[str, Any], input_hash: list[dict[str, Any]], before: dict[str, Any], tests: list[str], duplicate_count: int) -> dict[str, Any]:
    output_hashes = []
    for path in sorted(out.iterdir()):
        if path.name == "provenance_step3b.json":
            continue
        if path.is_file():
            output_hashes.append({"relative_path": path.relative_to(out).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha256(path)})
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "dataset_snapshot": SNAPSHOT, "pinned_commit_expected": COMMIT,
        "dataset_root": str(dataset.resolve()), "phenotype_stage_root": str(stage.resolve()),
        "step3a_specification_path": str(spec_path.resolve()), "step3a_specification_sha256": sha256(spec_path),
        "step3a_audit_script_path": str(Path(audit.__file__).resolve()), "step3a_audit_script_sha256": sha256(Path(audit.__file__).resolve()),
        "step3b_script_path": str((out / "prepare_step3b.py").resolve()), "step3b_script_sha256": sha256(out / "prepare_step3b.py"),
        "verified_payload_count": len(payloads), "verified_payloads_reused_without_download": len(payloads) == 41,
        "input_hashes": input_hash, "output_hashes_excluding_this_file": output_hashes,
        "git_before": before, "software": {"python": sys.version, "platform": platform.platform(), "audit_module": "Step 3A audit_v6.py"},
        "focused_tests": tests, "duplicate_analytical_key_count": duplicate_count,
        "boundaries": ["raw traceable preparation only", "no final standardization/composite", "no ICC/SEM/MDC", "no fitted age effects", "no prediction model", "no imputation", "no Evidence Engine decision"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="CHAVI Step 3B raw analysis-table preparation")
    ap.add_argument("--dataset", type=Path, default=Path("ds007116"))
    ap.add_argument("--phenotype-stage", type=Path, default=Path("chavi_step1b_phenotype_staging_20260907"))
    ap.add_argument("--step3a-dir", type=Path, default=Path("chavi_audit_ds007116_step3a_20260907"))
    ap.add_argument("--output", type=Path, default=Path("chavi_audit_ds007116_step3b_20260909"))
    ap.add_argument("--fixture-only", action="store_true")
    args = ap.parse_args()
    audit = load_audit((args.step3a_dir / "audit_v6.py").resolve())
    spec_path = (args.step3a_dir / "step3a_specification.json").resolve()
    spec = audit.b_load_spec(spec_path)
    audit.ACTIVE_SPEC = spec
    if args.fixture_only:
        print(json.dumps(audit.b_fixture_tests(), indent=2))
        return 0
    dataset, stage, out = args.dataset.resolve(), args.phenotype_stage.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    before = audit.git_metadata(dataset)
    if before.get("commit") != COMMIT:
        raise SystemExit(f"Pinned dataset commit mismatch: {before.get('commit')} != {COMMIT}")
    payloads, reuse = audit.s2_verified_payloads(dataset, stage)
    if len(payloads) != 41 or len(reuse) != 41:
        raise SystemExit("Step 3B requires all 41 verified Step 1B payloads")
    participant_fields, participant_rows, _ = audit.read_participants(dataset)
    session_rows, _, _, _, _ = audit.parse_scanner_aux(dataset)
    occasions = occasion_map(audit, dataset, payloads, participant_rows, session_rows)
    task_long, lookup, duplicates = task_rows(audit, payloads, occasions, stage)
    paired_tasks = paired_task_rows(lookup, task_long, occasions)
    profile = profile_manifest(audit, task_long, occasions)
    outcomes = outcome_rows(audit, payloads, occasions)
    candidates = candidate_prediction_rows(audit, task_long, outcomes, occasions)
    recon = reconciliation(audit, task_long, paired_tasks, profile, candidates, outcomes)
    tests = focused_tests(audit, spec, task_long, paired_tasks, profile, occasions, duplicates)

    shutil.copy2(spec_path, out / "executable_specification.json")
    shutil.copy2((args.step3a_dir / "assessment_occasion_mapping_step3a.csv").resolve(), out / "assessment_occasion_mapping_step3a.csv")
    write_csv(out / "task_observations_long.csv", task_long)
    write_csv(out / "paired_task_observations.csv", paired_tasks)
    write_csv(out / "paired_profile_manifest.csv", profile)
    write_csv(out / "outcome_observations_long.csv", outcomes)
    write_csv(out / "candidate_prediction_cohort.csv", candidates)
    write_csv(out / "analysis_data_dictionary.csv", data_dictionary())
    write_csv(out / "cohort_reconciliation.csv", recon)
    write_csv(out / "retrieval_reuse_manifest.csv", reuse)
    write_json(out / "input_manifest.json", {"dataset_snapshot": SNAPSHOT, "commit": COMMIT, "verified_payload_count": len(payloads), "participant_fields": participant_fields, "source_payloads": sorted(payloads)})
    write_json(out / "provenance_step3b.json", provenance(audit, out, dataset, stage, spec_path, payloads, input_hashes(audit, dataset, stage, payloads, spec_path), before, tests, len(duplicates)))
    after = audit.git_metadata(dataset)
    if after.get("commit") != before.get("commit") or after.get("status") != before.get("status"):
        raise SystemExit("Dataset checkout changed during Step 3B")
    print(json.dumps({"output": str(out), "verified_payloads_reused": len(payloads), "task_observation_rows": len(task_long), "paired_task_rows": len(paired_tasks), "profile_manifest_rows": len(profile), "outcome_observation_rows": len(outcomes), "candidate_rows": len(candidates), "duplicate_analytical_keys": len(duplicates), "focused_tests": tests, "dataset_commit": after.get("commit"), "dataset_status": after.get("status")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
