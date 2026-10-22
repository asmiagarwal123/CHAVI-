"""CHAVI Step 5A: synchronized profile-cohort reconstruction and measurement specification.

This script is intentionally preparation-only. It reconstructs raw, synchronized
five-task occasions and emits specifications/audits. It does not standardize,
construct profile scores, estimate reliability, fit an age model, predict, or
make clinical claims.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
DATASET = ROOT / "ds007116"
STAGE = ROOT / "chavi_step1b_phenotype_staging_20260907"
STEP3A = ROOT / "chavi_audit_ds007116_step3a_20260907"
STEP3B = ROOT / "chavi_audit_ds007116_step3b_20260909"
STEP4B = ROOT / "chavi_analysis_ds007116_step4b_five_tasks_20260916"
STEP4BR = ROOT / "chavi_analysis_ds007116_step4b_review_20260916"

TASKS = [
    {"key": "letter_nback", "label": "Letter N-back", "stem": "short_letter_2back", "field": "cnb_lnb_mcr", "qc": "cnb_lnb_valid_code", "dict": "short_letter_2back.json"},
    {"key": "face_memory", "label": "Face Memory", "stem": "penn_face_memory_test", "field": "cnb_cpf_cr", "qc": "cnb_cpf_valid_code", "dict": "penn_face_memory_test.json"},
    {"key": "matrix_reasoning", "label": "Matrix Reasoning", "stem": "penn_matrix_reasoning_test", "field": "cnb_pmat_cr", "qc": "cnb_pmat_valid_code", "dict": "penn_matrix_reasoning_test.json"},
    {"key": "emotion_recognition", "label": "Emotion Recognition", "stem": "penn_emotion_recognition_task", "field": "cnb_er40_cr", "qc": "cnb_er40_valid_code", "dict": "penn_emotion_recognition_task.json"},
    {"key": "dominant_finger_tapping", "label": "Dominant Finger Tapping", "stem": "short_computerized_finger_tapping_task", "field": "cnb_ctap_dom", "qc": "cnb_ctap_valid_code", "dict": "short_computerized_finger_tapping_task.json"},
]
TASK_KEYS = [t["key"] for t in TASKS]
TASK_BY_KEY = {t["key"]: t for t in TASKS}
VF = {"V", "F"}


def read_csv(path: Path, delimiter=","):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def write_csv(name, rows, fieldnames):
    path = OUT / name
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return path


def write_text(name, text):
    path = OUT / name
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def sha256_file(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tree_hashes(path: Path):
    if path.is_file():
        return {str(path.relative_to(ROOT)): sha256_file(path)}
    return {str(p.relative_to(ROOT)): sha256_file(p) for p in sorted(path.rglob("*")) if p.is_file()}


def directory_signature(path: Path):
    """Fast before/after mutation sentinel for a large directory tree."""
    h = hashlib.sha256()
    count = 0
    total = 0
    for p in sorted(path.rglob("*")):
        if p.is_file():
            st = p.stat()
            rel = str(p.relative_to(ROOT)).encode("utf-8")
            h.update(rel + b"\0" + str(st.st_size).encode("ascii") + b"\0" + str(st.st_mtime_ns).encode("ascii") + b"\n")
            count += 1
            total += st.st_size
    return {"file_count": count, "total_bytes": total, "path_size_mtime_sha256": h.hexdigest()}


def num(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def session_order(s):
    m = re.fullmatch(r"ses-(\d+)", str(s or ""))
    return int(m.group(1)) if m else None


def json_value(path: Path, field: str):
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get(field, {})


def snapshot_inputs():
    dirs = [DATASET, STAGE, STEP3A, STEP3B, STEP4B, STEP4BR]
    critical = [
        DATASET / "participants.tsv",
        DATASET / "participants.json",
        *[DATASET / "phenotype" / t["dict"] for t in TASKS],
        *[STAGE / f"{t['stem']}.tsv" for t in TASKS],
        STEP3A / "executable_specification.json",
        STEP3B / "task_observations_long.csv",
        STEP3B / "assessment_occasion_mapping_step3a.csv",
        STEP3B / "paired_profile_manifest.csv",
        STEP4B / "five_task_agreement_results.csv",
        STEP4B / "five_task_pair_manifest.csv",
        STEP4BR / "cross_task_session_alignment.csv",
        STEP4BR / "plot_validation_checks.csv",
        STEP4BR / "step4b_review_provenance.json",
    ]
    return {
        "directory_signatures": {str(p.relative_to(ROOT)): directory_signature(p) for p in dirs},
        "critical_file_hashes": {str(p.relative_to(ROOT)): sha256_file(p) for p in critical if p.exists()},
    }


def main():
    before = snapshot_inputs()
    registered = read_csv(DATASET / "participants.tsv", "\t")
    registered_ids = [r["participant_id"] for r in registered]
    mapping = {(r["participant_id"], r["original_session_id"]): r for r in read_csv(STEP3B / "assessment_occasion_mapping_step3a.csv")}
    observations = read_csv(STEP3B / "task_observations_long.csv")
    key_seen = set()
    source = {}
    for r in observations:
        k = (r["participant_id"], r["repository_session_id"], r["task_key"], r["score_field"])
        if k in key_seen:
            raise AssertionError(f"duplicate source key: {k}")
        key_seen.add(k)
        source[(r["participant_id"], r["repository_session_id"], r["task_key"])] = r

    continuation = {(p, s) for (p, s), r in mapping.items() if "continuation" in (r.get("comparability_status", "") + " " + r.get("proposed_cognitive_occasion_id", "")).lower()}
    all_keys = set(mapping) | {(p, s) for p, s, _ in source}
    occasion_rows = []
    complete = {}
    for pid, sid in sorted(all_keys, key=lambda x: (x[0], session_order(x[1]) or 999, x[1])):
        mr = mapping.get((pid, sid), {})
        is_cont = (pid, sid) in continuation
        row = {
            "participant_id": pid,
            "repository_session_id": sid,
            "cognitive_occasion_id": mr.get("proposed_cognitive_occasion_id", ""),
            "session_order": session_order(sid) or "",
            "session_age": mr.get("session_age", ""),
            "baseline_participant_age": mr.get("baseline_participant_age", ""),
            "rounded_acq_time": mr.get("rounded_acq_time", ""),
            "occasion_mapping_status": mr.get("comparability_status", ""),
            "continuation_excluded": "yes" if is_cont else "no",
            "all_five_source_records": "yes" if all((pid, sid, t["key"]) in source for t in TASKS) else "no",
            "all_five_finite": "no",
            "exact_vf_qc_eligible": "no",
            "synchronized_occasion_status": "excluded_continuation" if is_cont else "incomplete_or_ineligible",
        }
        values = {}
        for t in TASKS:
            r = source.get((pid, sid, t["key"]), {})
            row[f"{t['key']}_original_value"] = r.get("original_value", "")
            row[f"{t['key']}_parsed_numeric_value"] = r.get("parsed_numeric_value", "")
            row[f"{t['key']}_qc_code"] = r.get("raw_qc_codes", "")
            row[f"{t['key']}_score_field"] = r.get("score_field", t["field"] if r else "")
            row[f"{t['key']}_source_row_reference"] = r.get("source_row_reference", "")
            row[f"{t['key']}_source_filename"] = r.get("source_filename", "")
            row[f"{t['key']}_eligibility_reason"] = r.get("eligibility_reason_documented_valid_or_likely_valid", "")
            values[t["key"]] = r
        finite = not is_cont and all(num(values[t["key"]].get("parsed_numeric_value")) is not None for t in TASKS)
        qc_ok = finite and all(values[t["key"]].get("raw_qc_codes", "") in VF for t in TASKS)
        row["all_five_finite"] = "yes" if finite else "no"
        row["exact_vf_qc_eligible"] = "yes" if qc_ok else "no"
        if qc_ok:
            row["synchronized_occasion_status"] = "complete_synchronized_vf"
            complete[(pid, sid)] = (row, values)
        occasion_rows.append(row)

    occ_fields = [
        "participant_id", "repository_session_id", "cognitive_occasion_id", "session_order", "session_age", "baseline_participant_age", "rounded_acq_time", "occasion_mapping_status", "continuation_excluded", "all_five_source_records", "all_five_finite", "exact_vf_qc_eligible", "synchronized_occasion_status"
    ]
    for t in TASKS:
        occ_fields += [f"{t['key']}_{s}" for s in ["original_value", "parsed_numeric_value", "qc_code", "score_field", "source_row_reference", "source_filename", "eligibility_reason"]]
    write_csv("synchronized_profile_occasions.csv", occasion_rows, occ_fields)

    complete_by_pid = defaultdict(list)
    for (pid, sid), item in complete.items():
        complete_by_pid[pid].append((session_order(sid), sid, item))
    for pid in complete_by_pid:
        complete_by_pid[pid].sort(key=lambda x: (x[0], x[1]))

    pair_rows, trace_rows, exclusions = [], [], []
    for pid in registered_ids:
        occs = complete_by_pid.get(pid, [])
        if len(occs) >= 2:
            earlier, later = occs[0], occs[1]
            erow, evals = earlier[2]
            lrow, lvals = later[2]
            base = {
                "participant_id": pid, "earlier_session_id": earlier[1], "later_session_id": later[1],
                "earlier_occasion_id": erow["cognitive_occasion_id"], "later_occasion_id": lrow["cognitive_occasion_id"],
                "earlier_session_age": erow["session_age"], "later_session_age": lrow["session_age"],
                "baseline_participant_age": erow["baseline_participant_age"], "nominal_interval_days": "",
                "pair_rule": "first_two_jointly_complete_synchronized_vf_occasions", "qc_policy": "exact_raw_V_or_F_each_task_at_both_occasions",
                "pair_status": "candidate_for_phase2_measurement_specification",
            }
            if erow.get("rounded_acq_time") and lrow.get("rounded_acq_time"):
                # Dates are intentionally left as source text; interval is not a score and is only provenance.
                try:
                    d1 = datetime.fromisoformat(erow["rounded_acq_time"])
                    d2 = datetime.fromisoformat(lrow["rounded_acq_time"])
                    base["nominal_interval_days"] = str((d2 - d1).total_seconds() / 86400)
                except ValueError:
                    base["nominal_interval_days"] = ""
            for t in TASKS:
                k = t["key"]
                base[f"earlier_{k}_raw"] = evals[k].get("original_value", "")
                base[f"later_{k}_raw"] = lvals[k].get("original_value", "")
                base[f"earlier_{k}_qc"] = evals[k].get("raw_qc_codes", "")
                base[f"later_{k}_qc"] = lvals[k].get("raw_qc_codes", "")
                base[f"earlier_{k}_source"] = evals[k].get("source_row_reference", "")
                base[f"later_{k}_source"] = lvals[k].get("source_row_reference", "")
                trace_rows += [{"participant_id": pid, "pair_rule": base["pair_rule"], "occasion_role": "earlier", "session_id": earlier[1], "occasion_id": erow["cognitive_occasion_id"], "task_key": k, "score_field": t["field"], "raw_value": evals[k].get("original_value", ""), "parsed_numeric_value": evals[k].get("parsed_numeric_value", ""), "qc_code": evals[k].get("raw_qc_codes", ""), "source_filename": evals[k].get("source_filename", ""), "source_row_reference": evals[k].get("source_row_reference", ""), "eligibility": "yes"}, {"participant_id": pid, "pair_rule": base["pair_rule"], "occasion_role": "later", "session_id": later[1], "occasion_id": lrow["cognitive_occasion_id"], "task_key": k, "score_field": t["field"], "raw_value": lvals[k].get("original_value", ""), "parsed_numeric_value": lvals[k].get("parsed_numeric_value", ""), "qc_code": lvals[k].get("raw_qc_codes", ""), "source_filename": lvals[k].get("source_filename", ""), "source_row_reference": lvals[k].get("source_row_reference", ""), "eligibility": "yes"}]
            pair_rows.append(base)
        else:
            sessions = sorted({s for p, s in all_keys if p == pid}, key=lambda s: session_order(s) or 999)
            reason = "no source task/session records" if not sessions else ("fewer than two complete synchronized five-task V/F occasions" if len(occs) < 2 else "not selected")
            exclusions.append({"participant_id": pid, "observed_source_session_count": len(sessions), "observed_source_sessions": "|".join(sessions), "complete_synchronized_vf_occasion_count": len(occs), "excluded": "yes", "exclusion_reason": reason})

    pair_fields = ["participant_id", "earlier_session_id", "later_session_id", "earlier_occasion_id", "later_occasion_id", "earlier_session_age", "later_session_age", "baseline_participant_age", "nominal_interval_days", "pair_rule", "qc_policy", "pair_status"]
    for t in TASKS:
        pair_fields += [f"earlier_{t['key']}_{s}" for s in ["raw", "qc", "source"]]
        pair_fields += [f"later_{t['key']}_{s}" for s in ["raw", "qc", "source"]]
    write_csv("synchronized_profile_pair_candidates.csv", pair_rows, pair_fields)
    write_csv("profile_pair_exclusions.csv", exclusions, ["participant_id", "observed_source_session_count", "observed_source_sessions", "complete_synchronized_vf_occasion_count", "excluded", "exclusion_reason"])
    write_csv("profile_pair_source_trace.csv", trace_rows, ["participant_id", "pair_rule", "occasion_role", "session_id", "occasion_id", "task_key", "score_field", "raw_value", "parsed_numeric_value", "qc_code", "source_filename", "source_row_reference", "eligibility"])

    # Independent denominator reconciliation: profile-first is computed from raw observations above.
    task_pair_sets = {}
    for r in read_csv(STEP4BR / "independent_pair_manifest.csv"):
        task_pair_sets.setdefault(r["task_key"], set()).add(r["participant_id"])
    intersection_53 = set.intersection(*(task_pair_sets[k] for k in TASK_KEYS))
    alignment = {r["participant_id"]: r for r in read_csv(STEP4BR / "cross_task_session_alignment.csv")}
    aligned_50 = {p for p in intersection_53 if alignment.get(p, {}).get("alignment_status") == "aligned_all_five"}
    profile_52 = {r["participant_id"] for r in pair_rows}
    if len(intersection_53) != 53 or len(aligned_50) != 50 or len(profile_52) != 52:
        raise AssertionError((len(intersection_53), len(aligned_50), len(profile_52)))
    only_profile = sorted(profile_52 - aligned_50)
    only_task_intersection = sorted(intersection_53 - profile_52)
    reconciliation = [
        {"denominator_id": "registered", "count": 132, "construction": "ds007116/participants.tsv", "relationship": "starting frame"},
        {"denominator_id": "source_candidate_participants", "count": len({r["participant_id"] for r in observations}), "construction": "raw verified five-task observation rows", "relationship": "131; sub-23582 has no source task record"},
        {"denominator_id": "task_pair_intersection", "count": len(intersection_53), "construction": "intersection of five Step 4B task-specific pair participant sets", "relationship": "53 = profile-first 52 + task-pair-only participant(s)"},
        {"denominator_id": "task_pair_same_session_alignment", "count": len(aligned_50), "construction": "Step 4B-R five task-specific pairs share both session labels", "relationship": "50; excludes task-specific pair misalignment"},
        {"denominator_id": "profile_first_synchronized_primary_candidate", "count": len(profile_52), "construction": "first two jointly complete same-session occasions, exact V/F across all five tasks", "relationship": "52 = aligned 50 + " + "|".join(only_profile)},
        {"denominator_id": "task_pair_intersection_not_profile_first", "count": len(only_task_intersection), "construction": "task-specific union/intersection but no two jointly complete V/F occasions", "relationship": "|".join(only_task_intersection)},
    ]
    write_csv("cohort_count_reconciliation.csv", reconciliation, ["denominator_id", "count", "construction", "relationship"])

    review_ids = sorted(set(["sub-20259", "sub-20494", "sub-21035"]) | set(only_profile) | set(only_task_intersection))
    task_pair_rows = {p: [] for p in review_ids}
    for r in read_csv(STEP4B / "five_task_pair_manifest.csv") if (STEP4B / "five_task_pair_manifest.csv").exists() else []:
        if r.get("participant_id") in task_pair_rows:
            task_pair_rows[r["participant_id"]].append(r)
    discrep = []
    for pid in review_ids:
        for sid in sorted({s for p, s in all_keys if p == pid}, key=lambda s: session_order(s) or 999):
            vals = []
            for t in TASKS:
                r = source.get((pid, sid, t["key"]), {})
                vals.append(f"{t['key']}={r.get('original_value','')};qc={r.get('raw_qc_codes','')};eligible_vf={'yes' if r.get('raw_qc_codes','') in VF and num(r.get('parsed_numeric_value')) is not None else 'no'}")
            discrep.append({"participant_id": pid, "session_id": sid, "session_age": mapping.get((pid, sid), {}).get("session_age", ""), "task_session_qc_missing_summary": " || ".join(vals), "is_complete_synchronized_vf_occasion": "yes" if (pid, sid) in complete else "no", "step4b_task_pair_summary": "see cross_task_session_alignment.csv; " + json.dumps(alignment.get(pid, {}), sort_keys=True), "has_two_jointly_complete_profile_occasions": "yes" if pid in profile_52 else "no", "profile_first_decision": "included" if pid in profile_52 else "excluded", "exact_reason": "two same-session complete V/F occasions" if pid in profile_52 else "no two same-session complete V/F occasions"})
    write_csv("discrepant_participant_review.csv", discrep, ["participant_id", "session_id", "session_age", "task_session_qc_missing_summary", "is_complete_synchronized_vf_occasion", "step4b_task_pair_summary", "has_two_jointly_complete_profile_occasions", "profile_first_decision", "exact_reason"])

    flow = [
        {"stage": "registered participants", "n": 132, "rule": "all participants in participants.tsv"},
        {"stage": "source candidate participants", "n": len({r["participant_id"] for r in observations}), "rule": "at least one verified selected-task source row"},
        {"stage": "at least one complete synchronized V/F occasion", "n": len(complete_by_pid), "rule": "all five exact task fields finite and raw QC exactly V or F at same session"},
        {"stage": "at least two complete synchronized V/F occasions", "n": len(profile_52), "rule": "first two numeric-ordered jointly complete occasions"},
        {"stage": "Step 5A primary candidate pair denominator", "n": len(pair_rows), "rule": "one jointly synchronized first/two pair per participant; no imputation"},
    ]
    write_csv("profile_cohort_flow.csv", flow, ["stage", "n", "rule"])

    # Semantics and range audit. Observed ranges are calculated from raw finite source values only.
    sem_rows = []
    urls = {
        "penn": "https://webcnp.med.upenn.edu/explore-tests.html",
        "manual": "https://webcnp.med.upenn.edu/manual.html",
        "dataset_release": "https://github.com/OpenNeuroDatasets/ds007116/releases/tag/1.0.6",
    }
    official_context = {
        "letter_nback": "Official Penn page describes 45 target trials across 0-, 1-, and 2-back conditions; the selected local field is specifically true-positive responses for 1-back and 2-back trials.",
        "face_memory": "Official Penn page describes 20 target faces mixed with 20 foils; the selected local field is CPF Total Correct Responses.",
        "matrix_reasoning": "Official Penn page describes 24 trials with a five-consecutive-error stopping rule; the selected local field is PMAT Total Correct Responses.",
        "emotion_recognition": "Official Penn page describes 40 faces across five emotion choices; the selected local field is ER40 Total Correct Responses.",
        "dominant_finger_tapping": "Official Penn page describes motor speed as presses with one index finger in 10-second trials, five trials per hand; the selected local field is CTAP Mean of Dominant Hand Trials.",
    }
    for t in TASKS:
        d = json_value(DATASET / "phenotype" / t["dict"], t["field"])
        vals = [num(r.get("parsed_numeric_value")) for r in observations if r["task_key"] == t["key"]]
        vals = [v for v in vals if v is not None]
        long_name = d.get("LongName", d.get("Description", ""))
        unit = d.get("Units", "not documented locally")
        direction = "higher raw value = more correct responses; exact denominator/version remains a caveat" if t["key"] != "dominant_finger_tapping" else "higher raw value = more dominant-hand presses per recorded trial and therefore faster motor performance in the official task context; exact unit/aggregation should still be confirmed"
        sem_rows.append({"task_key": t["key"], "score_field": t["field"], "description": long_name, "unit": unit, "observed_min": min(vals) if vals else "", "observed_max": max(vals) if vals else "", "theoretical_range": "not documented sufficiently for this released field; no range inferred" if t["key"] in {"letter_nback", "face_memory", "matrix_reasoning", "emotion_recognition"} else "not documented", "higher_score_meaning": direction, "discreteness_or_ties": "count-like/discrete with ties" if t["key"] != "dominant_finger_tapping" else "mean of trials; decimals possible; ties possible", "observed_floor_ceiling": "observed range only; not a floor/ceiling claim", "accuracy_count_speed": "accuracy/count-like" if t["key"] != "dominant_finger_tapping" else "speed-related mean; exact unit/rate convention unresolved", "transformation_direction": "retain positive direction; confirm exact transformation before standardization", "unresolved": "task version/condition and exact denominator may remain unresolved" if t["key"] in {"letter_nback", "matrix_reasoning", "emotion_recognition"} else "field identity is documented; exact scale/aggregation and cross-occasion version equivalence require confirmation", "local_dictionary": str(DATASET / "phenotype" / t["dict"]), "official_source_url": urls["penn"], "official_context": official_context[t["key"]]})
    write_csv("score_semantics_and_direction.csv", sem_rows, list(sem_rows[0]))
    write_text("score_scale_review.md", f"""# Score-scale review (Step 5A)

The five selected fields were read from the pinned local JSON dictionaries. The dictionaries provide exact field names and LongName text, but they do not consistently document theoretical ranges or directional transformations. Observed minima and maxima in `score_semantics_and_direction.csv` are descriptive raw-value ranges only and must not be treated as validated scale bounds.

The Penn CNB official Explore Tests page supplies task context: Letter N-back, Face Memory, Matrix Reasoning, Emotion Identification, and Finger Tapping are described there. The official page supports the task context and trial descriptions, not undocumented denominator or scoring transformations. The local CTAP LongName says “Mean of Dominant Hand Trials”; combined with the official press-per-10-second task description, this supports a positive faster-performance direction, while the exact unit/aggregation remains a confirmation item. No score was reversed, standardized, centered, or combined in Step 5A.

Sources: [{urls['penn']}]({urls['penn']}), [{urls['manual']}]({urls['manual']}), [{urls['dataset_release']}]({urls['dataset_release']}).
""")
    evidence = []
    for t in TASKS:
        evidence.append({"evidence_id": f"DICT-{t['key']}", "claim_or_question": "selected field identity and local LongName", "source_type": "pinned local JSON dictionary", "source": str(DATASET / "phenotype" / t["dict"]), "supports": "field identity/label only", "does_not_support": "theoretical range, score reversal, clinical interpretation", "status": "supported"})
    evidence += [
        {"evidence_id": "PENN-EXPLORE", "claim_or_question": "official task context and trial descriptions", "source_type": "official Penn CNB documentation", "source": urls["penn"], "supports": "task context, target/foil/trial descriptions as stated", "does_not_support": "undocumented local score denominator or direction transformation", "status": "supported"},
        {"evidence_id": "PENN-MANUAL", "claim_or_question": "CNB measures accuracy and speed and uses standardized administration", "source_type": "official Penn CNB manual", "source": urls["manual"], "supports": "battery-level accuracy/speed context", "does_not_support": "this dataset's exact administration equivalence", "status": "supported with caveat"},
    ]
    write_csv("measurement_evidence_register.csv", evidence, list(evidence[0]))

    # Age support audit: label the exact candidate baseline/follow-up occasion and
    # expose support/extrapolation checks before any model is chosen.
    pair_role = {}
    for p in pair_rows:
        pair_role[(p["participant_id"], p["earlier_session_id"])] = "baseline_candidate"
        pair_role[(p["participant_id"], p["later_session_id"])] = "followup_candidate"
    participant_baseline_age = defaultdict(list)
    for p in pair_rows:
        a = num(p["earlier_session_age"])
        if a is not None:
            participant_baseline_age[p["participant_id"]].append(a)
    baseline_population_ages = [a for values in participant_baseline_age.values() for a in values]
    baseline_population_min = min(baseline_population_ages) if baseline_population_ages else ""
    baseline_population_max = max(baseline_population_ages) if baseline_population_ages else ""
    age_rows = []
    for r in occasion_rows:
        if r["synchronized_occasion_status"] == "complete_synchronized_vf":
            pid, sid = r["participant_id"], r["repository_session_id"]
            age = num(r["session_age"])
            participant_support = participant_baseline_age.get(pid, [])
            role = pair_role.get((pid, sid), "other_complete_candidate_occasion")
            baseline_age = participant_support[0] if participant_support else None
            delta = age - baseline_age if age is not None and baseline_age is not None and role == "followup_candidate" else None
            outside = "yes" if age is not None and role == "followup_candidate" and baseline_population_ages and (age < baseline_population_min or age > baseline_population_max) else "no"
            age_rows.append({"participant_id": pid, "session_id": sid, "occasion_id": r["cognitive_occasion_id"], "occasion_role_candidate": role, "session_age": r["session_age"], "baseline_participant_age": r["baseline_participant_age"], "age_units": "years per local session sidecar/Step 3A evidence", "age_precision": "decimal years as recorded", "age_available": "yes" if age is not None else "no", "rounded_timing": r["rounded_acq_time"], "age_timing_caveat": "session age is available, but acquisition time is rounded/anonymized and is not exact cognitive timing", "baseline_support_min": baseline_population_min, "baseline_support_max": baseline_population_max, "outside_baseline_support": outside, "age_delta_from_candidate_baseline": delta if delta is not None else "", "age_timestamp_consistency": "not testable as exact because timestamp is rounded/anonymized", "study_group": next((p.get("study_group", "") for p in registered if p["participant_id"] == pid), ""), "sex": next((p.get("sex", "") for p in registered if p["participant_id"] == pid), "")})
    write_csv("age_support_audit.csv", age_rows, list(age_rows[0]) if age_rows else ["participant_id"])
    ages = [num(r["session_age"]) for r in age_rows if num(r["session_age"]) is not None]
    baseline_ages = [num(r["session_age"]) for r in age_rows if r["occasion_role_candidate"] == "baseline_candidate" and num(r["session_age"]) is not None]
    follow_ages = [num(r["session_age"]) for r in age_rows if r["occasion_role_candidate"] == "followup_candidate" and num(r["session_age"]) is not None]
    band_counts = Counter(f"{int(a)//2*2:02d}-{int(a)//2*2+1:02d}" for a in ages)
    def age_summary_row(label, vals, selector):
        support_min, support_max = (min(baseline_ages), max(baseline_ages)) if baseline_ages else ("", "")
        local_bands = Counter(f"{int(a)//2*2:02d}-{int(a)//2*2+1:02d}" for a in vals)
        return {"subset": label, "n_observations": len(vals), "n_participants": len({r["participant_id"] for r in age_rows if selector(r)}), "age_missing_n": sum(selector(r) and num(r["session_age"]) is None for r in age_rows), "age_min": min(vals) if vals else "", "age_max": max(vals) if vals else "", "age_median": sorted(vals)[len(vals)//2] if vals else "", "age_unique_n": len(set(vals)), "baseline_support_min": support_min, "baseline_support_max": support_max, "followup_outside_baseline_support_n": sum(r["outside_baseline_support"] == "yes" for r in age_rows if selector(r)), "age_band_counts_json": json.dumps(dict(sorted(local_bands.items()))), "study_group_levels": "|".join(sorted({r["study_group"] for r in age_rows if selector(r) and r["study_group"]})), "sex_levels": "|".join(sorted({r["sex"] for r in age_rows if selector(r) and r["sex"]}))}
    age_summary = [
        age_summary_row("complete synchronized V/F occasions", ages, lambda r: True),
        age_summary_row("candidate baseline occasion", baseline_ages, lambda r: r["occasion_role_candidate"] == "baseline_candidate"),
        age_summary_row("candidate follow-up occasion", follow_ages, lambda r: r["occasion_role_candidate"] == "followup_candidate"),
    ]
    write_csv("age_distribution_summary.csv", age_summary, list(age_summary[0]))
    write_text("age_adjustment_feasibility.md", f"""# Age-support audit

The candidate synchronized profile cohort has {len(pair_rows)} participants and {len(age_rows)} complete V/F occasions in the audit table. Age is represented in decimal years from the local session sidecar provenance used by Step 3A/3B; the recorded acquisition timestamps are rounded/anonymized and are not exact cognitive-assessment times. The audit reports missingness, baseline/follow-up ranges, available sex/study-group levels, and age precision before any model choice.

No age model was fit. Before Step 5B, inspect whether the baseline and follow-up support overlap, whether age is sufficiently variable within the reference population, whether group/sex strata are estimable, and whether nonlinear terms are supported without extrapolation. The default candidate is a simple age term only if supported; nonlinear terms should be sensitivity candidates, not automatic additions. Age adjustment must not use follow-up information to define a participant's baseline reference in a way that leaks across the test/retest pair.
""")

    # Formal correction acceptance, based on Step 4B-R validation artifacts.
    checks = read_csv(STEP4BR / "plot_validation_checks.csv")
    svgs = [r for r in checks if r["plot_type"] == "difference" and r["file"].endswith(".svg")]
    pngs = [r for r in checks if r["plot_type"] == "difference" and r["file"].endswith(".png")]
    reviewed = [STEP4BR / f"reviewed_{t['key']}_bland_altman.png" for t in TASKS]
    write_text("step4b_correction_acceptance.md", f"""# Step 4B-R correction acceptance

Status: **accepted as a metadata/presentation correction**.

- The five original Bland–Altman SVGs pass the task and exact score-field metadata checks ({len(svgs)}/{len(TASKS)}).
- The original Bland–Altman PNG calculations and plotted points were independently checked in Step 4B-R; the only defect was omission of the exact score-field token from the PNG annotation ({sum(r['metadata_check']=='fail' for r in pngs)}/{len(TASKS)} original PNGs).
- The reviewed corrected PNG copies exist: {', '.join(p.name for p in reviewed if p.exists())}.
- No numerical result, point, interval, or original plot file was changed. The original PNGs and SVGs remain in the Step 4B output directory; the corrected copies are separate review artifacts.

This is not a statistical correction, cohort correction, or unresolved scientific blocker. It is a metadata/presentation correction. Step 4B-R's numerical findings remain accepted subject to its documented caveats, including rounded/anonymized timing and unresolved exact task-version comparability.
""")

    write_text("standardization_options_comparison.md", """# Standardization options comparison (draft)

| Option | Definition | Advantages | Risks/requirements | Step 5A position |
|---|---|---|---|---|
| A. No age adjustment | retain raw task fields in task-native units | transparent; no model leakage; preserves observed meaning | different task scales and developmental age effects prevent a cross-task vector until a scale decision is approved | simplest reference/sensitivity; not a final profile score |
| B. Baseline-reference age adjustment | fit task-wise age model in a reference set using baseline observations; participant-grouped cross-fitting; apply frozen transformation to both occasions | preserves a baseline reference and avoids using follow-up to train the transform | reference definition, group/sex handling, nonlinear support, extrapolation, and cross-fitting must be approved | candidate primary only after human approval |
| C. Grouped all-occasion age adjustment | fit task-wise age model using all eligible occasions but keep participants grouped in resampling/fitting | more observations; can support flexible curves | follow-up contributes to transformation; optimistic leakage risk if not grouped; time and age are coupled | sensitivity only unless leakage controls and estimand are approved |

No option was executed. The next step must decide whether a common standardized coordinate is scientifically warranted, whether norms are external or internal, and whether the score direction is established for every task. If a simple model is adequate, prefer it over an unsupported nonlinear model.
""")
    age_specs = [
        {"option": "A", "model": "none", "reference": "task-native raw source values", "fit_unit": "none", "cross_fitting": "not applicable", "output": "no transformed score", "status": "candidate"},
        {"option": "B", "model": "task-wise simple age adjustment; nonlinear only if pre-specified and supported", "reference": "baseline reference population, to be approved", "fit_unit": "participant-grouped", "cross_fitting": "required; fold assignment by participant", "output": "age-adjusted task coordinate, not computed here", "status": "candidate/open"},
        {"option": "C", "model": "task-wise grouped all-occasion age adjustment", "reference": "all eligible occasions, to be approved", "fit_unit": "participant-grouped", "cross_fitting": "required; no occasion from held-out participant in fit", "output": "age-adjusted task coordinate, not computed here", "status": "sensitivity candidate/open"},
    ]
    write_csv("age_model_candidate_specification.csv", age_specs, list(age_specs[0]))

    write_text("profile_estimand_specification.md", """# Profile estimand specification (draft; no values computed)

After a future approved task-wise transformation produces comparable coordinates, let the five-dimensional occasion vector be `Z_it = (Z_it1, ..., Z_it5)` for participant `i` and occasion `t`. Step 5A does not create these values.

- Elevation: `L_it = (1/5) * sum_j Z_itj`. This is a level/elevation estimand in standardized task units; it is not a clinical severity score.
- Centered shape: `S_itj = Z_itj - L_it`. This is a within-occasion relative configuration; it deliberately removes common elevation.
- Scatter: `D_it = sqrt((1/5) * sum_j S_itj^2)`. This describes dispersion around that occasion's elevation; it is nonnegative and depends on the chosen task coordinates.
- Shape change: `RMSE_shape = sqrt((1/5) * sum_j (S_i2j - S_i1j)^2)`. This is absolute centered-vector change, not a reliability coefficient.
- Shape similarity: the Pearson correlation of the five centered components across occasions is a descriptive/sensitivity measure only; with five components it is discrete/fragile and undefined when a centered vector has zero variance.

Inputs must be the same five exact task fields, in the registered order, with units explicitly documented after transformation. Raw source scores are heterogeneous and must not be averaged across tasks as if commensurate. Limits: all profile estimands require five finite transformed components; shape/scatter measures are mathematically sensitive to component variance, ties, shared elevation, and error covariance. Individual-level interpretation requires separate uncertainty and beyond-error methods, which are not performed here.
""")
    formulas = [
        {"formula_id": "PROFILE-VECTOR", "name": "occasion vector", "formula": "Z_it=(Z_it1,...,Z_it5)", "input": "five approved comparable task coordinates", "units": "common transformed units", "range_or_limit": "requires five finite components", "level": "occasion/participant", "status": "specified; not computed"},
        {"formula_id": "PROFILE-LEVEL", "name": "elevation", "formula": "L_it=mean_j(Z_itj)", "input": "Z_it", "units": "common transformed units", "range_or_limit": "depends on coordinate scale", "level": "occasion/participant", "status": "specified; not computed"},
        {"formula_id": "PROFILE-SHAPE", "name": "centered shape", "formula": "S_itj=Z_itj-L_it", "input": "Z_it and L_it", "units": "common transformed units", "range_or_limit": "sum_j S_itj=0", "level": "occasion/participant/task", "status": "specified; not computed"},
        {"formula_id": "PROFILE-SCATTER", "name": "scatter", "formula": "D_it=sqrt(mean_j(S_itj^2))", "input": "S_it", "units": "common transformed units", "range_or_limit": "nonnegative; zero for flat shape", "level": "occasion/participant", "status": "specified; not computed"},
        {"formula_id": "SHAPE-RMSE", "name": "shape difference", "formula": "sqrt(mean_j((S_i2j-S_i1j)^2))", "input": "two centered occasion vectors", "units": "common transformed units", "range_or_limit": "nonnegative", "level": "participant pair", "status": "specified; not computed"},
        {"formula_id": "SHAPE-CORR", "name": "shape similarity", "formula": "correlation(S_i1,S_i2)", "input": "two centered five-component vectors", "units": "unitless", "range_or_limit": "undefined for zero variance; descriptive/sensitivity only", "level": "participant pair", "status": "specified; not computed"},
    ]
    write_csv("profile_formula_registry.csv", formulas, list(formulas[0]))

    write_text("ipsative_scoring_risk.md", """# Ipsative/difference-score risk

Centering each occasion by its own mean makes the shape vector ipsative: the five centered components sum to zero, so components are mechanically dependent. This can make a component's relative position change even when all raw task scores move together, and it can make shape change depend on task variance, intercorrelations, shared elevation, and correlated measurement error. Reliability is not guaranteed to be lower or higher by centering; the result depends on the covariance structure and the estimand.

Cronbach and Gleser (1953) emphasize that profile similarity is dimension-specific, loses information when reduced to one index, and is sensitive to non-comparable scale units. Cronbach and Furby (1970) show why observed difference scores do not automatically identify true change. Hedge, Powell, and Sumner (2018) illustrate how robust task effects can coexist with weak individual-difference reliability. Enkavi et al. (2019) document variable test–retest reliability across self-regulation measures. These are methodological warnings, not evidence for a universal direction of bias in CHAVI.

Sources: [Cronbach & Gleser (1953), DOI 10.1037/h0057173](https://doi.org/10.1037/h0057173); [Cronbach & Furby (1970), DOI 10.1037/h0029382](https://doi.org/10.1037/h0029382); [Hedge et al. (2018), DOI 10.3758/s13428-017-0935-1](https://doi.org/10.3758/s13428-017-0935-1); [Enkavi et al. (2019), DOI 10.1073/pnas.1818430116](https://doi.org/10.1073/pnas.1818430116).
""")
    write_text("mechanical_instability_analysis_plan.md", """# Mechanical-instability analysis plan (future; not executed)

Separate four quantities: (1) observed shape instability between synchronized occasions; (2) the mechanically expected effect of within-occasion centering; (3) estimated measurement error propagated through the centering operation; and (4) residual instability after accounting for expected mechanics.

Planned checks are: derive the analytic covariance of centered components from the empirical task covariance; simulate known true profiles under observed task variances/intercorrelations; estimate task-level reliability and propagate plausible error covariance structures; compare raw-elevation, centered-shape, Euclidean/RMSE, and profile-correlation summaries; and run sensitivity analyses for common-elevation shifts, task-specific change, ties, and zero-variance profiles. The participant is the resampling unit. No universal claim that ipsative scoring lowers reliability will be made.

This plan requires approved score transformations, an approved synchronized cohort, and task-level reliability inputs. It remains a future Phase 2/Step 5B+ analysis.
""")
    evidence_profile = [
        {"evidence_id": "CRONBACH-GLESER-1953", "methodological_point": "profile similarity is dimension-specific; scale comparability and index choice matter", "source": "https://doi.org/10.1037/h0057173", "role": "primary methodological evidence"},
        {"evidence_id": "CRONBACH-FURBY-1970", "methodological_point": "difference scores are affected by reliability and occasion relation; observed change is not automatically true change", "source": "https://doi.org/10.1037/h0029382", "role": "primary methodological evidence"},
        {"evidence_id": "HEDGE-POWELL-SUMNER-2018", "methodological_point": "robust task effects can coexist with low individual-difference reliability", "source": "https://doi.org/10.3758/s13428-017-0935-1", "role": "primary empirical/methodological evidence"},
        {"evidence_id": "ENKAVI-2019", "methodological_point": "test-retest reliability varies across measures and should be evaluated empirically", "source": "https://doi.org/10.1073/pnas.1818430116", "role": "primary empirical evidence"},
        {"evidence_id": "MCGRAW-WONG-1996", "methodological_point": "ICC form must match the intended agreement/reliability estimand", "source": "https://doi.org/10.1037/1082-989x.1.1.30", "role": "primary methodological evidence"},
    ]
    write_csv("profile_methodology_evidence_register.csv", evidence_profile, list(evidence_profile[0]))

    write_text("cohort_policy_draft.md", """# Cohort policy draft

Candidate primary cohort: one pair per participant consisting of the first two numeric-ordered, jointly complete synchronized occasions, with all five exact fields finite and each task QC code exactly `V` or `F`. This produces a Step 5A primary candidate denominator of 52 participants. It is a measurement-specification candidate, not a final inferential cohort.

Sensitivity cohorts: strict V-only; V/F as above; raw versus an approved age-adjusted coordinate; scheduled ses-1/ses-2 only if that session rule is scientifically supported; retaining versus flagging extreme raw changes; and influence diagnostics. Extreme changes must not be deleted automatically. Task-misaligned pairs are not synchronized profiles and are excluded from the primary profile cohort.
""")
    sens = [
        {"analysis_id": "PRIMARY", "cohort": "first two jointly complete synchronized occasions", "qc": "V/F", "score_input": "raw initially; transformation decision open", "session_rule": "numeric ordered first two", "extreme_policy": "retain; influence review", "role": "candidate primary"},
        {"analysis_id": "S1", "cohort": "same synchronized rule", "qc": "V only", "score_input": "same approved transformation", "session_rule": "numeric ordered first two", "extreme_policy": "retain", "role": "sensitivity"},
        {"analysis_id": "S2", "cohort": "same synchronized rule", "qc": "V/F", "score_input": "raw", "session_rule": "numeric ordered first two", "extreme_policy": "retain", "role": "raw-scale sensitivity"},
        {"analysis_id": "S3", "cohort": "same synchronized rule", "qc": "V/F", "score_input": "age-adjusted candidate", "session_rule": "numeric ordered first two", "extreme_policy": "retain", "role": "transformation sensitivity"},
        {"analysis_id": "S4", "cohort": "scheduled pair only", "qc": "V/F", "score_input": "same approved transformation", "session_rule": "ses-1/ses-2 only if supported", "extreme_policy": "retain", "role": "scheduled-session sensitivity"},
        {"analysis_id": "S5", "cohort": "same synchronized rule", "qc": "V/F", "score_input": "same approved transformation", "session_rule": "numeric ordered first two", "extreme_policy": "flag/review; no automatic deletion", "role": "extreme-change/influence sensitivity"},
    ]
    write_csv("sensitivity_analysis_matrix.csv", sens, list(sens[0]))

    write_text("phase2_reliability_method_matrix.csv", "method,domain,level_or_unit,estimand,input,interpretation,uncertainty,failure_or_limit,role\n" + "\n".join([
        "ICC(A,1),task-level,participant pairs,absolute agreement/reliability,raw or approved transformed task pair,occasion agreement under absolute agreement,participant bootstrap CI,scale/direction/QC mismatch; completed in Step 4B,completed task-level reference",
        "mean change,task/elevation,participant pairs,systematic change,later-earlier pair values,average observed change,participant bootstrap CI,not causal and timing is nominal,primary descriptive",
        "SEM/MDC,task/elevation,participant pairs,measurement error/beyond-error change,approved reliability and variance,absolute uncertainty for individual change,requires approved reliability model and assumptions,future",
        "scatter D agreement/change,profile occasion/pair,dispersion around elevation,change/agreement in scatter,approved Z vectors,dispersion stability,zero/near-zero and scale dependence,sensitivity",
        "centered component agreement,shape/task components,participant pairs,component-wise shape agreement,centered vectors,relative task configuration agreement,participant bootstrap CI,ipsative dependence and five-component limitation,sensitivity",
        "shape RMSE/Euclidean,shape,participant pairs,absolute shape change,centered vectors,absolute relative-shape movement,participant bootstrap CI,not a reliability coefficient,sensitivity",
        "profile correlation,shape,participant pairs,rank/configuration similarity,centered vectors,descriptive rank-shape similarity only,participant bootstrap CI,undefined/fragile with five components and ties,sensitivity only",
        "directional/rank summaries,shape,participant pairs,direction/rank consistency,approved transformed vectors,descriptive direction,not absolute agreement, sensitivity",
        "group-level profile agreement,profile,group/pair aggregate,group agreement under model assumptions,approved profile vectors and covariance,group-level only,not individual reliability and depends on covariance assumptions,future sensitivity",
    ]))
    write_text("uncertainty_specification.md", """# Future uncertainty specification

The participant is the resampling unit: all five task values and both synchronized occasions for a participant stay together in each bootstrap resample. Task-level ICC/mean-change intervals use the completed Step 4B conventions. Future profile-level intervals should report uncertainty for elevation, scatter, centered components, shape RMSE/Euclidean change, and descriptive profile correlation separately. Bootstrap percentile or BCa choices must be stated before execution, with failure counts and degenerate profiles reported.

SEM/MDC require an explicitly approved reliability/error model and should not be back-calculated from a single descriptive ICC without assumptions. Multiple task/profile summaries are a family of estimands; multiplicity adjustments are not automatic and belong in the final SAP decision. No interval or profile reliability value is computed in Step 5A.
""")

    write_text("missingness_and_imputation_policy.md", """# Missingness and imputation policy

Primary profile analysis uses observed synchronized complete five-task occasions only. Missing selected scores, nonfinite values, missing QC, invalid/skipped/excluded QC, continuation sessions, and task-misaligned occasions are not imputed into the primary profile cohort. The raw occurrence and reason remain visible in the occasion table and exclusion files.

Report missingness by task, session, QC category, and participant pattern. Consider complete-case versus V-only and other prespecified sensitivity cohorts. Mean imputation, model-based imputation, and task-wise borrowing are not automatic because they can create artificial synchrony and distort covariance/shape. Any future imputation would require a separate missing-data estimand and a sensitivity analysis.
""")

    write_text("sap_phase2_measurement_draft.md", """# Draft SAP: Phase 2 measurement specification

**Status:** draft, not final and not preregistered.

**Research question.** Can the five exact CHAVI cognitive task measurements be placed into a defensible longitudinal measurement framework after confirming score semantics, synchronized occasions, age support, and error structure? This draft does not answer a clinical, diagnostic, prediction, or intervention question.

**Data and cohort.** Use the pinned ds007116 snapshot 1.0.6 and verified Step 1B payloads, with Step 3A/3B occasion/QC provenance and Step 4A/4A-R/4B/4B-R artifacts. Start from 132 registered participants. The candidate primary profile denominator is 52 participants with two first numeric-ordered same-session complete occasions under exact V/F for all five fields. Task-specific pair intersection is 53 and same-session task-pair alignment is 50; these are not interchangeable.

**Synchronized visit rule.** A visit is complete only if all five exact task fields are finite and raw QC is exactly V or F in the same repository session; continuation sessions are excluded. Preserve raw values, QC, task, and source-row provenance. No imputation.

**Score semantics and transformation.** Read local JSON dictionaries and official Penn CNB documentation. Do not infer undocumented theoretical ranges or reverse directions. Option A (raw) is a transparent candidate; Option B (baseline-reference, participant-grouped cross-fitted age adjustment) and Option C (grouped all-occasion adjustment) are candidates pending approval. No transformation is run here.

**Profile formulas.** If approved transformed coordinates exist later, define `Z_it`, elevation `L_it`, centered shape `S_it`, scatter `D_it`, shape RMSE, and descriptive shape correlation as in `profile_formula_registry.csv`. Do not compute final participant profile values in this step.

**Planned analyses.** Step 4B task-level agreement is complete. Future Phase 2 work may specify ICC(A,1), mean change, SEM/MDC, bootstrap, scatter and shape summaries, with the participant as bootstrap unit. Profile-level ICC, profile shape stability, and any individual-level reliability are prohibited in Step 5A.

**Multiple comparisons.** Treat task-level and profile-level summaries as separate estimand families. Any adjustment or estimation hierarchy requires supervisor approval; none is silently applied here.

**Extremes and claims.** Retain extreme raw changes and conduct influence diagnostics; do not automatically delete. Permitted claims are data provenance, score-field descriptions, synchronized-cohort counts, and measurement-specification proposals. Prohibited claims include prediction, clinical/diagnostic interpretation, threshold performance, individual classification, final reliability, and profile stability.

**Open decisions.** Approve score direction, age-adjustment option/reference, cross-fitting implementation, profile level/shape/scatter primary estimands, missing/extreme policies, scheduled-session sensitivity, treatment of the three task-misaligned participants, ipsative-risk analysis, and version uncertainty.
""")

    decisions = [
        ("D01","Step4B-R correction acceptance","five SVGs pass; five PNGs have presentation-only field-token omission; corrected copies exist","accept metadata/presentation correction; reject; block","accept metadata/presentation correction","no numerical result changed and originals preserved","confirmed","no","not required"),
        ("D02","synchronized cohort rule","raw source rows; exact V/F; same-session all five; continuation exclusion","V/F; V-only; unresolved inclusive","exact V/F same-session complete occasions","preserves synchrony and documented QC","recommended","yes","supervisor confirmation"),
        ("D03","primary denominator","profile-first reconstruction yields 52","task-pair 53; aligned 50; profile-first 52","52 profile-first candidates","matches jointly complete occasions","recommended","yes","supervisor confirmation"),
        ("D04","age adjustment","age is available but model support not finalized","none; baseline-reference cross-fit; all-occasion grouped","simple model only if supported; otherwise raw sensitivity","avoid unsupported nonlinear/extrapolated correction","open","yes","supervisor approval"),
        ("D05","reference and cross-fitting","future transformation can leak participant information","external norms; baseline reference; grouped all-occasion","baseline reference with participant-grouped cross-fitting if used","protects longitudinal separation","open","yes","supervisor approval"),
        ("D06","score direction","local field labels and Penn context; CTAP direction not explicit","retain; reverse; defer","defer unresolved fields; no reversal now","prevents undocumented transformation","open","yes","supervisor approval"),
        ("D07","profile estimands","formula registry defines elevation, centered shape, scatter and change","level primary; shape primary; scatter primary; separate families","separate level/shape/scatter estimands","avoids conflating constructs","open","yes","supervisor approval"),
        ("D07-L","profile-level formula","candidate elevation is mean of five approved transformed task coordinates","mean; weighted mean; latent factor","L_it=mean_j(Z_itj)","transparent and directly tied to the requested estimand","open","yes","supervisor approval"),
        ("D07-S","shape formula","candidate within-occasion centering removes elevation","centered vector; alternative residualization","S_itj=Z_itj-L_it","defines relative configuration explicitly","open","yes","supervisor approval"),
        ("D07-D","scatter formula","candidate RMS distance from occasion elevation","RMS; SD-style denominator; alternative dispersion","D_it=sqrt(mean_j(S_itj^2))","nonnegative and interpretable in coordinate units","open","yes","supervisor approval"),
        ("D08","missingness/imputation","complete synchronized data are available for 52 pairs","impute; complete case; model-based","observed complete case; no imputation","avoids artificial synchrony","recommended","yes","supervisor confirmation"),
        ("D09","extreme changes","extremes may be genuine or influential","delete; winsorize; retain and diagnose","retain; influence analysis","preserves auditability","recommended","yes","supervisor confirmation"),
        ("D10","task-misaligned 3","Step4B-R identifies 53 task-pair intersection, 50 aligned; 3 misaligned include requested review IDs","include task-wise; exclude profile; resolve manually","exclude from synchronized profile; retain task-level records","profile requires same-session all five","recommended","yes","supervisor confirmation"),
        ("D11","ipsative risk","centering creates dependence; reliability direction is not universal","ignore; mechanical analysis; final stability","mechanical/error decomposition before claims","separates structural from empirical instability","recommended","yes","supervisor approval"),
        ("D12","version uncertainty","exact task version/conditions and cognitive timing unresolved","assume equivalent; stratify; sensitivity; defer","report caveat; defer equivalence claim","prevents overclaiming longitudinal comparability","open","yes","supervisor approval"),
        ("D13","session-pair rule","numeric session order and positive rounded timing are available but nominal","scheduled; first two; all pairs","first two jointly complete; scheduled sensitivity","one pair/person and reproducibility","recommended","yes","supervisor confirmation"),
    ]
    write_csv("decision_register_step5a.csv", [{"decision_id": a, "issue": b, "evidence": c, "options": d, "recommended": e, "reason": f, "status": g, "blocks_implementation": h, "human_approval": i} for a,b,c,d,e,f,g,h,i in decisions], ["decision_id","issue","evidence","options","recommended","reason","status","blocks_implementation","human_approval"])

    # Provenance and review artifacts are written last so output hashes cover everything.
    after = snapshot_inputs()
    if before != after:
        raise AssertionError("input/dataset/previous-output hashes changed during Step 5A")
    output_hashes = {str(p.relative_to(ROOT)): sha256_file(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "step5a_provenance.json"}
    provenance = {
        "step": "5A", "generated_utc": datetime.now(timezone.utc).isoformat(), "script": str(Path(__file__).relative_to(ROOT)),
        "dataset": {"path": str(DATASET), "release_tag": "1.0.6", "commit": "fc7dc36fa2598b0b2e4579baef37d148cc085207", "before_hashes": before["critical_file_hashes"], "after_hashes": after["critical_file_hashes"], "before_directory_signature": before["directory_signatures"][str(DATASET.relative_to(ROOT))], "after_directory_signature": after["directory_signatures"][str(DATASET.relative_to(ROOT))]},
        "input_roles": {"stage": str(STAGE), "step3a": str(STEP3A), "step3b": str(STEP3B), "step4b": str(STEP4B), "step4b_review": str(STEP4BR)},
        "previous_input_output_hashes_before": before, "previous_input_output_hashes_after": after,
        "output_hashes": output_hashes, "registered_n": 132, "source_candidate_n": len({r["participant_id"] for r in observations}),
        "profile_first_candidate_n": len(pair_rows), "task_pair_intersection_n": len(intersection_53), "task_pair_alignment_n": len(aligned_50),
        "prohibited_operations": ["final profile reliability", "profile ICC", "shape stability calculation", "prediction", "threshold calibration", "UI", "clinical/diagnostic claims", "external validation", "standardization", "final participant profile values"],
        "software": {"python": sys.version, "platform": platform.platform()},
    }
    (OUT / "step5a_provenance.json").write_text(json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")
    write_text("step5a_reproduction_and_tests.md", """# Step 5A reproduction and tests

Run from the repository root:

```powershell
python chavi_analysis_ds007116_step5a_measurement_specification_20260916/prepare_step5a_measurement_specification.py
python -m unittest discover -s chavi_analysis_ds007116_step5a_measurement_specification_20260916 -p 'test_*.py' -v
```

The preparation script uses only local pinned dataset, staged payload, Step 3A/3B, Step 4B, and Step 4B-R artifacts. It reconstructs complete same-session occasions from raw verified task rows, applies exact V/F eligibility, excludes the documented continuation, chooses the first two jointly complete occasions per participant, and writes provenance hashes. It does not create standardized, centered, composite, elevation, shape, scatter, reliability, prediction, threshold, or clinical outputs.
""")
    write_text("step5a_review_report.md", f"""# CHAVI Step 5A review report

Step 4B-R correction is closed as a metadata/presentation correction. The pinned dataset and previous Step 1B–4B-R inputs/outputs were hash-checked before and after generation with no changes.

The raw profile-first reconstruction starts from 132 registered participants, finds {len({r['participant_id'] for r in observations})} source candidates, {len(complete_by_pid)} participants with at least one complete synchronized V/F occasion, and {len(pair_rows)} participants with two jointly complete occasions. The 50/52/53 reconciliation is explicit: 53 is the intersection of task-specific pair participants, 50 have the same earlier and later session labels across all five task pairs, and 52 are selected from raw same-session complete V/F occasions. The profile-first candidate set adds {', '.join(only_profile) or 'none'} to the 50 aligned set and excludes {', '.join(only_task_intersection) or 'none'} from the 53 task-pair intersection.

Score semantics, age support, standardization options, profile formulas, ipsative risks, cohort policies, future reliability methods, missingness policy, and a draft SAP are documented. No final profile value, standardization, age model, profile ICC, shape stability estimate, prediction, threshold, clinical or diagnostic claim was produced.

Step 5A is ready for supervisor review of the open decision register, but Step 5B transformation implementation is not started and is not ready for execution until direction, reference/cross-fitting, age adjustment, and profile estimand decisions are approved.
""")
    # Recompute the output manifest after the final documentation files exist.
    provenance["output_hashes"] = {
        str(p.relative_to(ROOT)): sha256_file(p)
        for p in sorted(OUT.iterdir())
        if p.is_file() and p.name != "step5a_provenance.json"
    }
    (OUT / "step5a_provenance.json").write_text(json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
