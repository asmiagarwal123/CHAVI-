#!/usr/bin/env python3
"""CHAVI Step 4B: reusable five-task longitudinal dependability analysis.

The module intentionally uses only the Python standard library.  It reads the
pinned local dataset, verified Step 1B phenotype payloads, Step 3A/3B
preparation outputs, and the independently validated Step 4A Face Memory
outputs.  It writes only this new Step 4B directory.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import random
import re
import statistics
import struct
import subprocess
import sys
import zlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
DATASET = ROOT / "ds007116"
STAGE = ROOT / "chavi_step1b_phenotype_staging_20260907"
STEP3A = ROOT / "chavi_audit_ds007116_step3a_20260907"
STEP3B = ROOT / "chavi_audit_ds007116_step3b_20260909"
STEP4A = ROOT / "chavi_analysis_ds007116_step4a_face_memory_20260914"
STEP4A_REVIEW = ROOT / "chavi_analysis_ds007116_step4a_review_20260914"

DATASET_COMMIT = "fc7dc36fa2598b0b2e4579baef37d148cc085207"
BOOTSTRAP_REPLICATES = 5000
BOOTSTRAP_SEED = 20260914
MISSING_TOKENS = {"", "n/a", "na", "null", "none", "missing"}
QC_MEANINGS = {
    "V": "Valid",
    "F": "Likely valid, problem occurred which affected performance for a limited number of responses/mild to moderate effect",
    "0": "No autovalidation rule available",
    "S": "Skipped",
    "N": "Not Valid",
    "C": "Assessor Comment",
    "X": "Excluded",
}

TASKS = [
    {"task_key": "letter_nback", "label": "Letter N-back", "stem": "short_letter_2back", "score_field": "cnb_lnb_mcr", "qc_field": "cnb_lnb_valid_code", "filename": "short_letter_2back.tsv"},
    {"task_key": "face_memory", "label": "Face Memory", "stem": "penn_face_memory_test", "score_field": "cnb_cpf_cr", "qc_field": "cnb_cpf_valid_code", "filename": "penn_face_memory_test.tsv"},
    {"task_key": "matrix_reasoning", "label": "Matrix Reasoning", "stem": "penn_matrix_reasoning_test", "score_field": "cnb_pmat_cr", "qc_field": "cnb_pmat_valid_code", "filename": "penn_matrix_reasoning_test.tsv"},
    {"task_key": "emotion_recognition", "label": "Emotion Recognition", "stem": "penn_emotion_recognition_task", "score_field": "cnb_er40_cr", "qc_field": "cnb_er40_valid_code", "filename": "penn_emotion_recognition_task.tsv"},
    {"task_key": "dominant_finger_tapping", "label": "Dominant Finger Tapping", "stem": "short_computerized_finger_tapping_task", "score_field": "cnb_ctap_dom", "qc_field": "cnb_ctap_valid_code", "filename": "short_computerized_finger_tapping_task.tsv"},
]


class Step4BError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_file(path: Path, role: str) -> None:
    if not path.is_file():
        raise Step4BError(f"Required {role} is unavailable: {path}")


def read_csv_strict(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    require_file(path, "tabular input")
    try:
        reader = csv.reader(io.StringIO(path.read_text(encoding="utf-8-sig")), strict=True, delimiter=delimiter)
        header = next(reader)
        if len(header) != len(set(header)):
            raise Step4BError(f"Duplicate fields in {path}")
        rows = []
        for line, values in enumerate(reader, start=2):
            if len(values) != len(header):
                raise Step4BError(f"Field-count mismatch at {path}:{line}")
            rows.append(dict(zip(header, values)))
        return rows
    except (csv.Error, StopIteration) as exc:
        raise Step4BError(f"Malformed or empty CSV/TSV: {path}: {exc}") from exc


def read_json(path: Path) -> Any:
    require_file(path, "JSON input")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Step4BError(f"Invalid JSON: {path}: {exc}") from exc


def parse_finite(value: Any) -> tuple[float | None, str]:
    text = "" if value is None else str(value).strip()
    if text.lower() in MISSING_TOKENS:
        return None, "missing"
    try:
        number = float(text)
    except (TypeError, ValueError):
        return None, "unparseable_non_numeric"
    if not math.isfinite(number):
        return None, "nonfinite"
    return number, "finite"


def session_number(session_id: str) -> int | None:
    match = re.fullmatch(r"ses-(\d+)", str(session_id).strip())
    return int(match.group(1)) if match else None


def parse_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def qc_class(code: str) -> tuple[str, str]:
    normalized = str(code).strip()
    if normalized == "V":
        return "documented_valid", QC_MEANINGS[normalized]
    if normalized == "F":
        return "documented_likely_valid", QC_MEANINGS[normalized]
    if normalized in QC_MEANINGS:
        return {"0": "no_automatic_validation", "S": "documented_skipped", "N": "documented_invalid", "C": "comment_conditional", "X": "documented_excluded"}[normalized], QC_MEANINGS[normalized]
    if normalized.lower() in MISSING_TOKENS:
        return "missing_qc", ""
    return "unknown_or_undocumented", ""


def git_state() -> dict[str, str]:
    dataset = str(DATASET.resolve()).replace("\\", "/")
    def run(*args: str) -> str:
        return subprocess.check_output(["git", "-c", f"safe.directory={dataset}", "-C", str(DATASET), *args], text=True, stderr=subprocess.STDOUT).strip()
    try:
        return {"status": run("status", "--short", "--branch"), "commit": run("rev-parse", "HEAD"), "describe": run("describe", "--tags", "--always"), "branch": run("branch", "--show-current"), "remote": run("remote", "-v")}
    except (OSError, subprocess.CalledProcessError) as exc:
        raise Step4BError(f"Unable to inspect dataset Git state: {exc}") from exc


def directory_hashes(directory: Path) -> list[dict[str, Any]]:
    return [{"relative_path": str(path.relative_to(directory)), "size_bytes": path.stat().st_size, "sha256": sha256(path)} for path in sorted(directory.rglob("*")) if path.is_file()]


def input_hash(path: Path, role: str) -> dict[str, Any]:
    require_file(path, role)
    return {"path": str(path.resolve()), "role": role, "size_bytes": path.stat().st_size, "sha256": sha256(path)}


def load_inputs() -> dict[str, Any]:
    required = [
        (DATASET / "dataset_description.json", "dataset description"), (DATASET / "participants.tsv", "participant metadata"),
        (STEP3B / "assessment_occasion_mapping_step3a.csv", "occasion mapping"), (STEP3B / "task_observations_long.csv", "Step 3B task table"),
        (STEP3B / "paired_task_observations.csv", "Step 3B paired task table"), (STEP3B / "paired_profile_manifest.csv", "Step 3B paired profile table"),
        (STEP3B / "analysis_data_dictionary.csv", "Step 3B data dictionary"), (STEP3B / "cohort_reconciliation.csv", "Step 3B reconciliation"),
        (STEP3B / "decision_register_step3b.csv", "Step 3B decision register"), (STEP3B / "executable_specification.json", "Step 3B specification"),
        (STEP3B / "prepare_step3b.py", "Step 3B executable script"), (STEP3B / "provenance_step3b.json", "Step 3B provenance"),
        (STEP3A / "step3a_specification.json", "Step 3A specification"), (STEP3A / "audit_v6.py", "Step 3A executable script"),
        (STEP4A / "face_memory_included_pairs.csv", "Step 4A included pairs"), (STEP4A / "face_memory_agreement_results.csv", "Step 4A agreement results"),
        (STEP4A / "face_memory_bootstrap_results.csv", "Step 4A bootstrap results"), (STEP4A / "step4a_analysis_contract.json", "Step 4A contract"),
        (STEP4A / "step4a_provenance.json", "Step 4A provenance"), (STEP4A_REVIEW / "statistical_crosscheck.csv", "Step 4A independent statistical crosscheck"),
        (STEP4A_REVIEW / "bootstrap_diagnostics.csv", "Step 4A bootstrap diagnostics"), (STEP4A_REVIEW / "reproduction_and_tests.md", "Step 4A independent validation tests"),
    ]
    for task in TASKS:
        required.extend([(STAGE / task["filename"], f"verified {task['label']} phenotype payload"), (DATASET / "phenotype" / task["filename"], f"{task['label']} dataset pointer"), (DATASET / "phenotype" / task["filename"].replace(".tsv", ".json"), f"{task['label']} dictionary")])
    for path, role in required:
        require_file(path, role)
    occasion_rows = read_csv_strict(STEP3B / "assessment_occasion_mapping_step3a.csv")
    occasion_map: dict[tuple[str, str], dict[str, str]] = {}
    for row in occasion_rows:
        key = (row["participant_id"], row["original_session_id"])
        if key in occasion_map:
            raise Step4BError(f"Duplicate occasion mapping key: {key}")
        occasion_map[key] = row
    step3b_rows = read_csv_strict(STEP3B / "task_observations_long.csv")
    input_paths = [path for path, _ in required]
    prior_hashes = {str(directory): directory_hashes(directory) for directory in (STEP4A, STEP4A_REVIEW)}
    dataset_input_hashes = [input_hash(path, role) for path, role in required if path.is_relative_to(DATASET)]
    return {"occasion_map": occasion_map, "step3b_rows": step3b_rows, "input_hashes": [input_hash(path, role) for path, role in required], "dataset_input_hashes_before": dataset_input_hashes, "prior_output_hashes_before": prior_hashes, "git_before": git_state()}


def build_observations(task: dict[str, str], inputs: dict[str, Any]) -> list[dict[str, Any]]:
    source = STAGE / task["filename"]
    raw_rows = read_csv_strict(source, delimiter="\t")
    needed = {"participant_id", "session_id", task["score_field"], task["qc_field"]}
    if not raw_rows or not needed.issubset(raw_rows[0]):
        raise Step4BError(f"{task['label']} payload lacks required fields: {sorted(needed)}")
    step3b = [row for row in inputs["step3b_rows"] if row.get("task_table_stem") == task["stem"] and row.get("score_field") == task["score_field"]]
    if len(step3b) != len(raw_rows):
        raise Step4BError(f"Step 3B row count mismatch for {task['label']}: {len(step3b)} != {len(raw_rows)}")
    by_ref = {row["source_row_reference"]: row for row in step3b}
    if len(by_ref) != len(step3b):
        raise Step4BError(f"Duplicate Step 3B source reference for {task['label']}")
    seen: set[tuple[str, str, str, str]] = set()
    observations = []
    for row_number, row in enumerate(raw_rows, start=1):
        participant, session = row["participant_id"].strip(), row["session_id"].strip()
        key = (participant, session, task["stem"], task["score_field"])
        if key in seen:
            raise Step4BError(f"Duplicate analytical key for {task['label']}: {key}")
        seen.add(key)
        reference = f"phenotype/{task['filename']}#data-row-{row_number}"
        if reference not in by_ref:
            raise Step4BError(f"Step 3B has no matching source row for {task['label']}: {reference}")
        score, score_status = parse_finite(row.get(task["score_field"], ""))
        qc_status, qc_meaning = qc_class(row.get(task["qc_field"], ""))
        session_idx = session_number(session)
        occasion = inputs["occasion_map"].get((participant, session), {})
        continuation = "continuation" in occasion.get("comparability_status", "").lower() or "continuation" in occasion.get("proposed_cognitive_occasion_id", "").lower()
        # Invalid/skipped/excluded QC is deliberately recorded before score
        # missingness so explicit invalidity overrides a missing/unresolved score.
        if session_idx is None:
            reason = "ambiguous_session_label"
        elif continuation:
            reason = "continuation_session_not_new_CNB_occasion"
        elif qc_status in {"documented_invalid", "documented_skipped", "documented_excluded"}:
            reason = qc_status
        elif score_status == "missing":
            reason = "missing_selected_score"
        elif score_status != "finite":
            reason = "nonfinite_or_unparseable_score"
        elif qc_status not in {"documented_valid", "documented_likely_valid"}:
            reason = qc_status
        else:
            reason = row.get(task["qc_field"], "").strip()
        eligible = score_status == "finite" and qc_status in {"documented_valid", "documented_likely_valid"} and session_idx is not None and not continuation
        observations.append({"task_key": task["task_key"], "task_label": task["label"], "task_stem": task["stem"], "score_field": task["score_field"], "qc_field": task["qc_field"], "participant_id": participant, "session_id": session, "session_number": session_idx, "score_raw": row.get(task["score_field"], ""), "score": score, "score_status": score_status, "qc_raw_code": row.get(task["qc_field"], "").strip(), "qc_status": qc_status, "qc_meaning": qc_meaning, "eligible": eligible, "eligibility_reason": reason, "source_row_reference": reference, "source_row_number": row_number, "occasion": occasion, "continuation": continuation, "step3b_row": by_ref[reference]})
    return observations


def interval_info(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    first_time = parse_time(first.get("occasion", {}).get("rounded_acq_time", ""))
    second_time = parse_time(second.get("occasion", {}).get("rounded_acq_time", ""))
    if first_time is None or second_time is None:
        return {"interval_days": "", "interval_status": "missing_or_unparseable_timing", "timing_missing": "yes", "interval_warning": "Rounded/anonymized acquisition timing is missing or unparseable; nominal numeric session order is used."}
    delta = (second_time - first_time).total_seconds() / 86400.0
    if not math.isfinite(delta) or delta <= 0:
        return {"interval_days": "", "interval_status": "nonpositive_or_ambiguous_timing", "timing_missing": "no", "interval_warning": "Rounded/anonymized timing is nonpositive or ambiguous; it is not used as exact chronology."}
    return {"interval_days": f"{delta:.10g}", "interval_status": "positive_rounded_anonymized_interval", "timing_missing": "no", "interval_warning": "Interval is derived from rounded/anonymized acquisition timing and is not an exact cognitive-assessment interval."}


def require_positive_session_interval(first: int | None, second: int | None) -> None:
    if first is None or second is None or second <= first:
        raise Step4BError(f"Nonpositive or ambiguous nominal session interval: {first} -> {second}")


def make_pair(task: dict[str, str], first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    require_positive_session_interval(first["session_number"], second["session_number"])
    timing = interval_info(first, second)
    return {"task_key": task["task_key"], "task_label": task["label"], "task_table_stem": task["stem"], "score_field": task["score_field"], "participant_id": first["participant_id"], "earlier_session_id": first["session_id"], "later_session_id": second["session_id"], "earlier_session_number": first["session_number"], "later_session_number": second["session_number"], "earlier_raw_score": first["score_raw"], "later_raw_score": second["score_raw"], "earlier_score": f"{first['score']:.10g}", "later_score": f"{second['score']:.10g}", "paired_difference_later_minus_earlier": f"{second['score'] - first['score']:.10g}", "pair_mean": f"{(second['score'] + first['score']) / 2:.10g}", "pair_interval_days": timing["interval_days"], "interval_status": timing["interval_status"], "timing_missing": timing["timing_missing"], "interval_warning": timing["interval_warning"], "earlier_age": first["occasion"].get("session_age", ""), "later_age": second["occasion"].get("session_age", ""), "source_table": f"phenotype/{task['filename']}", "earlier_source_row_reference": first["source_row_reference"], "later_source_row_reference": second["source_row_reference"], "earlier_qc_raw_code": first["qc_raw_code"], "later_qc_raw_code": second["qc_raw_code"], "earlier_qc_dictionary_meaning": first["qc_meaning"], "later_qc_dictionary_meaning": second["qc_meaning"], "qc_policy": "documented_valid_or_likely_valid", "inclusion_status": "included_primary_pair", "exclusion_reason": "", "task_version_comparability_status": "unresolved; candidate comparable by session label only", "task_version_comparability_note": "Available metadata do not establish unchanged task/version equivalence, exact cognitive-assessment timing, or identical administration conditions.", "participant_pair_key": f"{first['participant_id']}|{task['stem']}|{task['score_field']}|first_two_eligible_observations"}


def candidate_accounting(task: dict[str, str], observations: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in observations:
        grouped[row["participant_id"]].append(row)
    accounting, pairs, exclusions, intervals = [], [], [], []
    for participant in sorted(grouped):
        candidate = sorted(grouped[participant], key=lambda r: (r["session_number"] is None, r["session_number"] if r["session_number"] is not None else 10**9, r["source_row_number"]))
        eligible = [r for r in candidate if r["eligible"]]
        earlier_candidate = candidate[0] if candidate else None
        later_candidate = candidate[1] if len(candidate) > 1 else None
        record = {"task_key": task["task_key"], "task_label": task["label"], "participant_id": participant, "candidate_observation_count": len(candidate), "eligible_observation_count": len(eligible), "candidate_earlier_score_status": earlier_candidate["score_status"] if earlier_candidate else "not_observed", "candidate_later_score_status": later_candidate["score_status"] if later_candidate else "not_observed", "candidate_earlier_score_missing": "yes" if earlier_candidate and earlier_candidate["score_status"] == "missing" else "no", "candidate_later_score_missing": "yes" if later_candidate and later_candidate["score_status"] == "missing" else "no", "candidate_later_slot_unavailable": "yes" if later_candidate is None else "no", "included_primary_pair": "no", "inclusion_or_exclusion_reason": "", "candidate_source_rows": ";".join(r["source_row_reference"] for r in candidate), "eligible_source_rows": ";".join(r["source_row_reference"] for r in eligible)}
        if earlier_candidate and later_candidate:
            candidate_timing = interval_info(earlier_candidate, later_candidate)
            intervals.append({"task_key": task["task_key"], "task_label": task["label"], "participant_id": participant, "interval_stage": "candidate_first_two_source_observations", "earlier_session_id": earlier_candidate["session_id"], "later_session_id": later_candidate["session_id"], **candidate_timing})
        else:
            intervals.append({"task_key": task["task_key"], "task_label": task["label"], "participant_id": participant, "interval_stage": "candidate_first_two_source_observations", "earlier_session_id": earlier_candidate["session_id"] if earlier_candidate else "", "later_session_id": "", "interval_days": "", "interval_status": "not_enough_source_observations", "timing_missing": "yes", "interval_warning": "No later source observation was available for an interval."})
        if len(eligible) >= 2:
            first, second = eligible[:2]
            pair = make_pair(task, first, second)
            pairs.append(pair)
            record["included_primary_pair"], record["inclusion_or_exclusion_reason"] = "yes", "included_primary_pair"
            intervals.append({"task_key": task["task_key"], "task_label": task["label"], "participant_id": participant, "interval_stage": "selected_primary_pair", "earlier_session_id": first["session_id"], "later_session_id": second["session_id"], "interval_days": pair["pair_interval_days"], "interval_status": pair["interval_status"], "timing_missing": pair["timing_missing"], "interval_warning": pair["interval_warning"]})
        else:
            if any(r["qc_status"] in {"documented_invalid", "documented_skipped", "documented_excluded"} for r in candidate):
                reason = "QC_not_documented_valid_or_likely_valid"
            elif any(r["continuation"] for r in candidate) and not eligible:
                reason = "continuation_session_not_new_CNB_occasion"
            elif len(eligible) == 1:
                reason = "only_one_eligible_observation"
            elif any(r["score_status"] in {"missing", "nonfinite", "unparseable_non_numeric"} for r in candidate):
                reason = "missing_or_nonfinite_selected_score"
            else:
                reason = "no_eligible_observation"
            record["inclusion_or_exclusion_reason"] = reason
            exclusions.append({**record, "exclusion_detail": "; ".join(sorted(set(r["eligibility_reason"] for r in candidate))), "raw_qc_codes_observed": ";".join(sorted(set(r["qc_raw_code"] or "<missing>" for r in candidate))), "raw_score_statuses_observed": ";".join(sorted(set(r["score_status"] for r in candidate)))})
        accounting.append(record)
    if len(accounting) != len(grouped) or len(pairs) + len(exclusions) != len(accounting):
        raise Step4BError(f"Candidate accounting does not partition {task['label']} participants exactly once")
    return accounting, pairs, exclusions, intervals


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("quantile requires values")
    position = (len(ordered) - 1) * probability
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] if low == high else ordered[low] + (position - low) * (ordered[high] - ordered[low])


def descriptive(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0, "mean": None, "sd": None, "median": None, "iqr": None, "min": None, "max": None, "missing_count": 0}
    return {"n": len(values), "mean": statistics.mean(values), "sd": statistics.stdev(values) if len(values) > 1 else None, "median": statistics.median(values), "iqr": quantile(values, .75) - quantile(values, .25), "min": min(values), "max": max(values), "missing_count": 0}


def ranks(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    result = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        average = (i + 1 + j) / 2.0
        for position in range(i, j):
            result[indexed[position][0]] = average
        i = j
    return result


def pearson(x: list[float], y: list[float]) -> float | None:
    if len(x) != len(y) or len(x) < 2:
        return None
    mx, my = statistics.mean(x), statistics.mean(y)
    numerator = sum((a - mx) * (b - my) for a, b in zip(x, y))
    denominator = math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
    return numerator / denominator if denominator > 0 else None


def spearman(x: list[float], y: list[float]) -> float | None:
    return pearson(ranks(x), ranks(y))


def icc_absolute_agreement(x: list[float], y: list[float]) -> tuple[float | None, str]:
    if len(x) != len(y) or len(x) < 2:
        return None, "fewer_than_two_participants"
    n, k = len(x), 2
    grand = statistics.mean(x + y)
    row_means = [(a + b) / 2 for a, b in zip(x, y)]
    col_means = [statistics.mean(x), statistics.mean(y)]
    ms_rows = k * sum((value - grand) ** 2 for value in row_means) / (n - 1)
    ms_cols = n * sum((value - grand) ** 2 for value in col_means) / (k - 1)
    ms_error = sum((a - rm - col_means[0] + grand) ** 2 + (b - rm - col_means[1] + grand) ** 2 for a, b, rm in zip(x, y, row_means)) / ((n - 1) * (k - 1))
    denominator = ms_rows + (k - 1) * ms_error + k * (ms_cols - ms_error) / n
    if not math.isfinite(denominator) or abs(denominator) <= 1e-15:
        return None, "undefined_zero_or_nonfinite_denominator"
    estimate = (ms_rows - ms_error) / denominator
    return (estimate, "ok") if math.isfinite(estimate) else (None, "nonfinite_estimate")


def icc_consistency(x: list[float], y: list[float]) -> tuple[float | None, str]:
    if len(x) != len(y) or len(x) < 2:
        return None, "fewer_than_two_participants"
    n, k = len(x), 2
    grand = statistics.mean(x + y)
    row_means = [(a + b) / 2 for a, b in zip(x, y)]
    ms_rows = k * sum((value - grand) ** 2 for value in row_means) / (n - 1)
    col_means = [statistics.mean(x), statistics.mean(y)]
    ms_error = sum((a - rm - col_means[0] + grand) ** 2 + (b - rm - col_means[1] + grand) ** 2 for a, b, rm in zip(x, y, row_means)) / ((n - 1) * (k - 1))
    denominator = ms_rows + (k - 1) * ms_error
    if not math.isfinite(denominator) or abs(denominator) <= 1e-15:
        return None, "undefined_zero_or_nonfinite_denominator"
    estimate = (ms_rows - ms_error) / denominator
    return (estimate, "ok") if math.isfinite(estimate) else (None, "nonfinite_estimate")


def point_statistics(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    earlier = [float(row["earlier_score"]) for row in pairs]
    later = [float(row["later_score"]) for row in pairs]
    differences = [b - a for a, b in zip(earlier, later)]
    primary, primary_status = icc_absolute_agreement(earlier, later)
    consistency, consistency_status = icc_consistency(earlier, later)
    p, s = pearson(earlier, later), spearman(earlier, later)
    return {"n": len(pairs), "earlier": earlier, "later": later, "differences": differences, "pair_means": [(a + b) / 2 for a, b in zip(earlier, later)], "earlier_summary": descriptive(earlier), "later_summary": descriptive(later), "difference_summary": descriptive(differences), "increasing_count": sum(d > 0 for d in differences), "unchanged_count": sum(d == 0 for d in differences), "decreasing_count": sum(d < 0 for d in differences), "increasing_proportion": sum(d > 0 for d in differences) / len(differences) if differences else None, "unchanged_proportion": sum(d == 0 for d in differences) / len(differences) if differences else None, "decreasing_proportion": sum(d < 0 for d in differences) / len(differences) if differences else None, "icc_a1": primary, "icc_a1_status": primary_status, "icc_c1": consistency, "icc_c1_status": consistency_status, "pearson": p, "pearson_status": "ok" if p is not None else "undefined_zero_variance", "spearman": s, "spearman_status": "ok" if s is not None else "undefined_zero_variance_or_ties"}


METRICS = ("mean_difference", "icc_a1", "icc_c1", "pearson", "spearman")


def bootstrap(pairs: list[dict[str, Any]], seed: int = BOOTSTRAP_SEED) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    rng, n = random.Random(seed), len(pairs)
    rows, values, failures = [], defaultdict(list), Counter()
    if n < 2:
        raise Step4BError("Bootstrap requires at least two participant pairs")
    for replicate in range(1, BOOTSTRAP_REPLICATES + 1):
        indices = [rng.randrange(n) for _ in range(n)]
        sample = [{**pairs[index], "bootstrap_copy_id": f"{pairs[index]['participant_id']}|boot-{copy_index:04d}"} for copy_index, index in enumerate(indices, 1)]
        stats = point_statistics(sample)
        row: dict[str, Any] = {"replicate_id": replicate, "bootstrap_seed": seed, "n_pairs": n, "unique_source_participants": len({pairs[index]["participant_id"] for index in indices}), "duplicate_sampled_participant_copies": n - len({pairs[index]["participant_id"] for index in indices})}
        for metric in METRICS:
            value = stats["difference_summary"]["mean"] if metric == "mean_difference" else stats[metric]
            status = "ok" if metric == "mean_difference" and value is not None else "undefined" if metric == "mean_difference" else stats[f"{metric}_status"]
            row[metric], row[f"{metric}_status"] = "" if value is None else f"{float(value):.12g}", status
            if value is None or status != "ok":
                failures[f"{metric}:{status}"] += 1
            else:
                values[metric].append(float(value))
        rows.append(row)
    summaries = {}
    for metric in METRICS:
        valid = values[metric]
        summaries[metric] = {"successful_replicates": len(valid), "failed_or_undefined_replicates": BOOTSTRAP_REPLICATES - len(valid), "failure_reasons": {reason: count for reason, count in sorted(failures.items()) if reason.startswith(metric + ":")}, "percentile_2.5": quantile(valid, .025) if valid else None, "percentile_97.5": quantile(valid, .975) if valid else None}
    return rows, summaries


def finite_number(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.12g}" if math.isfinite(value) else ""
    return str(value)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: finite_number(row.get(field, "")) for field in fields})


def chart_geometry(values: Iterable[float], minimum: float | None = None, maximum: float | None = None) -> tuple[float, float, list[float]]:
    values = list(values)
    low = min(values) if minimum is None else minimum
    high = max(values) if maximum is None else maximum
    if high <= low:
        low, high = low - 1, high + 1
    padding = (high - low) * .08
    low, high = low - padding, high + padding
    return low, high, [low + (high - low) * i / 5 for i in range(6)]


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)


FONT = {" ": ("00000",) * 7, "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"), ".": ("00000", "00000", "00000", "00000", "00000", "00110", "00110"), ":": ("00000", "00110", "00110", "00000", "00110", "00110", "00000"), "=": ("00000", "11111", "00000", "11111", "00000", "00000", "00000")}
_FONT_ROWS = {"0":"01110 10001 10011 10101 11001 10001 01110", "1":"00100 01100 00100 00100 00100 00100 01110", "2":"01110 10001 00001 00010 00100 01000 11111", "3":"11110 00001 00001 01110 00001 00001 11110", "4":"00010 00110 01010 10010 11111 00010 00010", "5":"11111 10000 10000 11110 00001 00001 11110", "6":"00110 01000 10000 11110 10001 10001 01110", "7":"11111 00001 00010 00100 01000 01000 01000", "8":"01110 10001 10001 01110 10001 10001 01110", "9":"01110 10001 10001 01111 00001 00010 11100"}
for _char, _rows in zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", ["01110 10001 10001 11111 10001 10001 10001", "11110 10001 10001 11110 10001 10001 11110", "01111 10000 10000 10000 10000 10000 01111", "11110 10001 10001 10001 10001 10001 11110", "11111 10000 10000 11110 10000 10000 11111", "11111 10000 10000 11110 10000 10000 10000", "01111 10000 10000 10111 10001 10001 01111", "10001 10001 10001 11111 10001 10001 10001", "11111 00100 00100 00100 00100 00100 11111", "00111 00010 00010 00010 00010 10010 01100", "10001 10010 10100 11000 10100 10010 10001", "10000 10000 10000 10000 10000 10000 11111", "10001 11011 10101 10101 10001 10001 10001", "10001 11001 10101 10011 10001 10001 10001", "01110 10001 10001 10001 10001 10001 01110", "11110 10001 10001 11110 10000 10000 10000", "01110 10001 10001 10001 10101 10010 01101", "11110 10001 10001 11110 10100 10010 10001", "01111 10000 10000 01110 00001 00001 11110", "11111 00100 00100 00100 00100 00100 00100", "10001 10001 10001 10001 10001 10001 01110", "10001 10001 10001 10001 10001 01010 00100", "10001 10001 10001 10101 10101 11011 10001", "10001 10001 01010 00100 01010 10001 10001", "10001 10001 01010 00100 00100 00100 00100", "11111 00001 00010 00100 01000 10000 11111"]):
    FONT[_char] = tuple(_rows.split())
for _char, _rows in _FONT_ROWS.items():
    FONT[_char] = tuple(_rows.split())


class Raster:
    def __init__(self, width: int, height: int) -> None:
        self.width, self.height, self.pixels = width, height, bytearray((255, 255, 255) * (width * height))
    def pixel(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            offset = (y * self.width + x) * 3
            self.pixels[offset:offset + 3] = bytes(color)
    def line(self, x1: int, y1: int, x2: int, y2: int, color: tuple[int, int, int], width: int = 1) -> None:
        steps = max(abs(x2 - x1), abs(y2 - y1), 1)
        for i in range(steps + 1):
            x, y = round(x1 + (x2 - x1) * i / steps), round(y1 + (y2 - y1) * i / steps)
            for ox in range(-width // 2, width // 2 + 1):
                for oy in range(-width // 2, width // 2 + 1):
                    self.pixel(x + ox, y + oy, color)
    def circle(self, cx: int, cy: int, radius: int, color: tuple[int, int, int]) -> None:
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= radius * radius:
                    self.pixel(x, y, color)
    def text(self, x: int, y: int, value: str, color: tuple[int, int, int] = (40, 48, 60), scale: int = 3) -> None:
        cursor = x
        for char in value.upper():
            for row_index, row in enumerate(FONT.get(char, FONT[" "])):
                for column_index, cell in enumerate(row):
                    if cell == "1":
                        for oy in range(scale):
                            for ox in range(scale):
                                self.pixel(cursor + column_index * scale + ox, y + row_index * scale + oy, color)
            cursor += 6 * scale
    def save(self, path: Path, metadata: str) -> None:
        raw = b"".join(b"\x00" + bytes(self.pixels[y * self.width * 3:(y + 1) * self.width * 3]) for y in range(self.height))
        text = b"Description\x00" + metadata.encode("latin-1", "replace")
        data = b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0)) + png_chunk(b"tEXt", text) + png_chunk(b"IDAT", zlib.compress(raw, 9)) + png_chunk(b"IEND", b"")
        path.write_bytes(data)


def svg_escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def write_scatter_plots(task: dict[str, str], pairs: list[dict[str, Any]], out_png: Path, out_svg: Path) -> None:
    x, y = [float(row["earlier_score"]) for row in pairs], [float(row["later_score"]) for row in pairs]
    low, high, ticks = chart_geometry(x + y)
    W, H, left, top, right, bottom = 1600, 1000, 170, 70, 60, 150
    px = lambda value: round(left + (value - low) / (high - low) * (W - left - right))
    py = lambda value: round(H - bottom - (value - low) / (high - low) * (H - top - bottom))
    raster = Raster(W, H)
    for tick in ticks:
        raster.line(left, py(tick), W - right, py(tick), (224, 228, 234), 2); raster.line(px(tick), top, px(tick), H - bottom, (224, 228, 234), 2)
    raster.line(left, H - bottom, W - right, H - bottom, (40, 48, 60), 4); raster.line(left, top, left, H - bottom, (40, 48, 60), 4); raster.line(px(low), py(low), px(high), py(high), (140, 145, 155), 3)
    for a, b in zip(x, y): raster.circle(px(a), py(b), 7, (32, 100, 170))
    raster.text(220, 18, f"{task['label']} EARLIER VERSUS LATER", scale=3); raster.text(360, H - 58, f"EARLIER {task['score_field']}", scale=3); raster.text(25, top + 25, f"LATER {task['score_field']}", scale=3); raster.text(W - 610, top + 22, f"N = {len(pairs)} IDENTITY LINE", scale=2)
    raster.save(out_png, f"title={task['label']} earlier versus later; x-axis=earlier {task['score_field']}; y-axis=later {task['score_field']}; n={len(pairs)}; identity line y=x")
    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><title>{svg_escape(task["label"])} earlier versus later, n={len(pairs)}</title><desc>x-axis earlier {task["score_field"]}; y-axis later {task["score_field"]}; identity line y=x</desc><rect width="100%" height="100%" fill="white"/><style>.grid{{stroke:#e0e4ea;stroke-width:2}}.axis{{stroke:#28303c;stroke-width:3}}.point{{fill:#2064aa;fill-opacity:.78}}.identity{{stroke:#8c919b;stroke-width:3;stroke-dasharray:10 8}}text{{font-family:Arial,sans-serif;fill:#28303c}}</style>']
    for tick in ticks: elements.append(f'<line class="grid" x1="{left}" y1="{py(tick)}" x2="{W-right}" y2="{py(tick)}"/><line class="grid" x1="{px(tick)}" y1="{top}" x2="{px(tick)}" y2="{H-bottom}"/>')
    elements += [f'<line class="axis" x1="{left}" y1="{H-bottom}" x2="{W-right}" y2="{H-bottom}"/><line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{H-bottom}"/><line class="identity" x1="{px(low)}" y1="{py(low)}" x2="{px(high)}" y2="{py(high)}"/>']
    elements += [f'<circle class="point" cx="{px(a)}" cy="{py(b)}" r="6"/>' for a, b in zip(x, y)]
    elements += [f'<text x="{W/2}" y="35" text-anchor="middle" font-size="28" font-weight="bold">{svg_escape(task["label"])}: earlier versus later raw score</text>', f'<text x="{W/2}" y="{H-35}" text-anchor="middle" font-size="24">Earlier {task["score_field"]}</text>', f'<text x="35" y="{H/2}" text-anchor="middle" font-size="24" transform="rotate(-90 35 {H/2})">Later {task["score_field"]}</text>', f'<text x="{W-right-10}" y="{top+30}" text-anchor="end" font-size="20">n = {len(pairs)}; dashed line = identity</text>', '</svg>']
    out_svg.write_text("\n".join(elements), encoding="utf-8")


def write_difference_plot(task: dict[str, str], pairs: list[dict[str, Any]], out_png: Path, out_svg: Path) -> None:
    means, diffs = [float(row["pair_mean"]) for row in pairs], [float(row["paired_difference_later_minus_earlier"]) for row in pairs]
    mean_diff, sd_diff = statistics.mean(diffs), statistics.stdev(diffs) if len(diffs) > 1 else 0.0
    loa_low, loa_high = mean_diff - 1.96 * sd_diff, mean_diff + 1.96 * sd_diff
    xlow, xhigh, xticks = chart_geometry(means); ylow, yhigh, yticks = chart_geometry(diffs, min(diffs + [0.0, loa_low]), max(diffs + [0.0, loa_high]))
    W, H, left, top, right, bottom = 1600, 1000, 170, 70, 60, 150
    px = lambda value: round(left + (value - xlow) / (xhigh - xlow) * (W - left - right)); py = lambda value: round(H - bottom - (value - ylow) / (yhigh - ylow) * (H - top - bottom))
    raster = Raster(W, H)
    for tick in xticks: raster.line(px(tick), top, px(tick), H - bottom, (224, 228, 234), 2)
    for tick in yticks: raster.line(left, py(tick), W - right, py(tick), (224, 228, 234), 2)
    raster.line(left, H - bottom, W - right, H - bottom, (40, 48, 60), 4); raster.line(left, top, left, H - bottom, (40, 48, 60), 4)
    for value, color, width in [(0.0, (20, 20, 20), 3), (mean_diff, (190, 70, 55), 4), (loa_low, (140, 145, 155), 2), (loa_high, (140, 145, 155), 2)]: raster.line(left, py(value), W - right, py(value), color, width)
    for a, b in zip(means, diffs): raster.circle(px(a), py(b), 7, (32, 100, 170))
    raster.text(170, 18, f"{task['label']} DIFFERENCE VERSUS MEAN", scale=3); raster.text(230, H - 58, "PAIR MEAN OF RAW SCORES", scale=3); raster.text(25, top + 25, "LATER MINUS EARLIER", scale=3); raster.text(W - 830, top + 22, f"N = {len(pairs)} ZERO AND LOA LINES", scale=2)
    raster.save(out_png, f"title={task['label']} difference versus pair mean; x-axis=pair mean; y-axis=later minus earlier; n={len(pairs)}; zero line and limits of agreement")
    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><title>{svg_escape(task["label"])} difference versus pair mean, n={len(pairs)}</title><desc>x-axis pair mean; y-axis later minus earlier; zero line; mean difference {mean_diff:.6g}; limits of agreement {loa_low:.6g}, {loa_high:.6g}</desc><rect width="100%" height="100%" fill="white"/><style>.grid{{stroke:#e0e4ea;stroke-width:2}}.axis{{stroke:#28303c;stroke-width:3}}.point{{fill:#2064aa;fill-opacity:.78}}.mean{{stroke:#be4637;stroke-width:4}}.zero{{stroke:#141414;stroke-width:3}}.loa{{stroke:#8c919b;stroke-width:2;stroke-dasharray:10 8}}text{{font-family:Arial,sans-serif;fill:#28303c}}</style>']
    for tick in xticks: elements.append(f'<line class="grid" x1="{px(tick)}" y1="{top}" x2="{px(tick)}" y2="{H-bottom}"/>')
    for tick in yticks: elements.append(f'<line class="grid" x1="{left}" y1="{py(tick)}" x2="{W-right}" y2="{py(tick)}"/>')
    elements += [f'<line class="axis" x1="{left}" y1="{H-bottom}" x2="{W-right}" y2="{H-bottom}"/><line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{H-bottom}"/><line class="zero" x1="{left}" y1="{py(0)}" x2="{W-right}" y2="{py(0)}"/><line class="mean" x1="{left}" y1="{py(mean_diff)}" x2="{W-right}" y2="{py(mean_diff)}"/><line class="loa" x1="{left}" y1="{py(loa_low)}" x2="{W-right}" y2="{py(loa_low)}"/><line class="loa" x1="{left}" y1="{py(loa_high)}" x2="{W-right}" y2="{py(loa_high)}"/>']
    elements += [f'<circle class="point" cx="{px(a)}" cy="{py(b)}" r="6"/>' for a, b in zip(means, diffs)]
    elements += [f'<text x="{W/2}" y="35" text-anchor="middle" font-size="28" font-weight="bold">{svg_escape(task["label"])}: difference versus pair mean</text>', f'<text x="{W/2}" y="{H-35}" text-anchor="middle" font-size="24">Pair mean of raw {task["score_field"]} scores</text>', f'<text x="35" y="{H/2}" text-anchor="middle" font-size="24" transform="rotate(-90 35 {H/2})">Later minus earlier</text>', f'<text x="{W-right-10}" y="{top+30}" text-anchor="end" font-size="20">n = {len(pairs)}; zero, mean, and LoA lines</text>', '</svg>']
    out_svg.write_text("\n".join(elements), encoding="utf-8")


def contract(inputs: dict[str, Any]) -> dict[str, Any]:
    value = {"contract_name": "CHAVI Step 4B five-task task-level longitudinal dependability", "contract_version": "step4b-five-task-1", "generated_utc": utc_now(), "dataset": {"name": "OpenNeuro ds007116", "snapshot": "1.0.6", "commit_expected": DATASET_COMMIT, "dataset_root": str(DATASET.resolve())}, "tasks": TASKS, "primary_qc_policy": {"include_raw_codes": ["V", "F"], "require_finite_score": True, "invalidity_precedence": "documented invalid/skipped/excluded QC remains the explicit reason even when score is missing/unresolved"}, "primary_pairing": {"rule": "first two eligible observations per participant", "unit": "one participant contributes at most one pair per task", "order": "strict numeric ses-<integer> order", "positive_interval": "nonpositive or ambiguous nominal session intervals are rejected; rounded timestamps are auxiliary timing provenance"}, "statistics": {"primary": "ICC(A,1), two-way random-effects absolute agreement, single measurement", "icc_a1_formula": "(MS_R - MS_E) / (MS_R + (k-1)MS_E + k*(MS_C-MS_E)/n), k=2", "sensitivity": ["ICC(C,1)", "Pearson correlation", "Spearman correlation"], "negative_icc": "retained; no arbitrary reliability labels"}, "bootstrap": {"unit": "participant pair", "replicates": BOOTSTRAP_REPLICATES, "seed": BOOTSTRAP_SEED, "interval": "linear-interpolated percentile 95% interval"}, "plots": {"scatter": "earlier score on x, later score on y, identity line y=x", "bland_altman": "later-minus-earlier difference versus pair mean with zero, mean, and 1.96 SD agreement-limit lines; independent y-axis limits"}, "input_hashes": inputs["input_hashes"], "explicit_non_actions": ["no profile construction", "no ipsative scoring", "no simulation", "no Report/Caution/Refuse", "no prediction", "no LLM", "no UI", "no diagnosis", "no clinical interpretation", "no external dataset analysis", "no standardization, age adjustment, imputation, composite, SEM, or MDC"]}
    (OUT / "step4b_analysis_contract.json").write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return value


def write_outputs(inputs: dict[str, Any], all_results: list[dict[str, Any]], contract_value: dict[str, Any]) -> dict[str, Any]:
    all_accounting = [row for result in all_results for row in result["accounting"]]; all_exclusions = [row for result in all_results for row in result["exclusions"]]; all_intervals = [row for result in all_results for row in result["intervals"]]; all_pairs = [row for result in all_results for row in result["pairs"]]
    write_csv(OUT / "five_task_candidate_accounting.csv", all_accounting)
    write_csv(OUT / "five_task_exclusions.csv", all_exclusions)
    write_csv(OUT / "five_task_interval_audit.csv", all_intervals)
    pair_fields = list(all_pairs[0]) if all_pairs else []
    write_csv(OUT / "five_task_pair_manifest.csv", all_pairs, pair_fields)
    agreement, bootstrap_rows, descriptive_rows = [], [], []
    for result in all_results:
        task, pairs, stats, boot_summary = result["task"], result["pairs"], result["stats"], result["boot_summary"]
        ba_mean = stats["difference_summary"]["mean"]
        ba_sd = stats["difference_summary"]["sd"] or 0.0
        ba_low, ba_high = ba_mean - 1.96 * ba_sd, ba_mean + 1.96 * ba_sd
        for metric in ("icc_a1", "icc_c1", "pearson", "spearman"):
            summary = boot_summary[metric]
            agreement.append({"task_key": task["task_key"], "task_label": task["label"], "statistic": metric, "n_pairs": stats["n"], "estimate": stats[metric], "ci_method": "participant-pair bootstrap percentile", "ci_level": .95, "ci_low": summary["percentile_2.5"], "ci_high": summary["percentile_97.5"], "successful_bootstrap_replicates": summary["successful_replicates"], "failed_or_undefined_bootstrap_replicates": summary["failed_or_undefined_replicates"], "failure_reasons_json": json.dumps(summary["failure_reasons"], sort_keys=True), "status": stats[f"{metric}_status"], "formula_or_definition": "ICC(A,1) two-way random absolute agreement single measurement" if metric == "icc_a1" else "ICC(C,1) two-way consistency single measurement" if metric == "icc_c1" else "linear association" if metric == "pearson" else "rank association with average ties", "bland_altman_mean_difference": ba_mean, "bland_altman_loa_low": ba_low, "bland_altman_loa_high": ba_high})
        summary = boot_summary["mean_difference"]
        agreement.append({"task_key": task["task_key"], "task_label": task["label"], "statistic": "mean_paired_difference", "n_pairs": stats["n"], "estimate": ba_mean, "ci_method": "participant-pair bootstrap percentile", "ci_level": .95, "ci_low": summary["percentile_2.5"], "ci_high": summary["percentile_97.5"], "successful_bootstrap_replicates": summary["successful_replicates"], "failed_or_undefined_bootstrap_replicates": summary["failed_or_undefined_replicates"], "failure_reasons_json": json.dumps(summary["failure_reasons"], sort_keys=True), "status": "ok", "formula_or_definition": "later score minus earlier score", "bland_altman_mean_difference": ba_mean, "bland_altman_loa_low": ba_low, "bland_altman_loa_high": ba_high})
        bootstrap_rows.extend({"task_key": task["task_key"], "task_label": task["label"], **row} for row in result["bootstrap_rows"])
        for subset, summary in (("earlier", stats["earlier_summary"]), ("later", stats["later_summary"]), ("paired_difference_later_minus_earlier", stats["difference_summary"])):
            for metric in ("n", "mean", "sd", "median", "iqr", "min", "max", "missing_count"):
                descriptive_rows.append({"task_key": task["task_key"], "task_label": task["label"], "result_family": "raw_descriptive", "subset": subset, "metric": metric, "value": summary[metric], "unit": "count" if metric in {"n", "missing_count"} else f"raw {task['score_field']} points", "missingness_basis": "complete selected primary pairs"})
        accounting = result["accounting"]
        descriptive_rows.extend([
            {"task_key": task["task_key"], "task_label": task["label"], "result_family": "pre_pair_missingness", "subset": "candidate_earlier_slot", "metric": "missing_score_count", "value": sum(row["candidate_earlier_score_missing"] == "yes" for row in accounting), "unit": "count", "missingness_basis": "counted before complete-pair filtering"},
            {"task_key": task["task_key"], "task_label": task["label"], "result_family": "pre_pair_missingness", "subset": "candidate_later_slot", "metric": "missing_score_count", "value": sum(row["candidate_later_score_missing"] == "yes" for row in accounting), "unit": "count", "missingness_basis": "counted before complete-pair filtering"},
            {"task_key": task["task_key"], "task_label": task["label"], "result_family": "pre_pair_missingness", "subset": "candidate_later_slot", "metric": "slot_unavailable_count", "value": sum(row["candidate_later_slot_unavailable"] == "yes" for row in accounting), "unit": "count", "missingness_basis": "counted before complete-pair filtering"},
        ])
        for label in ("increasing_count", "unchanged_count", "decreasing_count", "increasing_proportion", "unchanged_proportion", "decreasing_proportion"):
            descriptive_rows.append({"task_key": task["task_key"], "task_label": task["label"], "result_family": "paired_change", "subset": "included_pairs", "metric": label, "value": stats[label], "unit": "count" if label.endswith("count") else "proportion", "missingness_basis": "complete selected primary pairs"})
        write_scatter_plots(task, pairs, OUT / f"{task['task_key']}_earlier_later_scatter.png", OUT / f"{task['task_key']}_earlier_later_scatter.svg")
        write_difference_plot(task, pairs, OUT / f"{task['task_key']}_bland_altman.png", OUT / f"{task['task_key']}_bland_altman.svg")
    write_csv(OUT / "five_task_agreement_results.csv", agreement)
    write_csv(OUT / "five_task_bootstrap_results.csv", bootstrap_rows)
    write_csv(OUT / "five_task_descriptive_results.csv", descriptive_rows)
    return {"agreement": agreement, "descriptive": descriptive_rows, "pairs": all_pairs}


def face_memory_reproduction(all_results: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    face = next(result for result in all_results if result["task"]["task_key"] == "face_memory")
    reference = {row["published_statistic"] + ":" + row["quantity"]: float(row["independent_value"]) for row in read_csv_strict(STEP4A_REVIEW / "statistical_crosscheck.csv") if row["independent_value"] and row["quantity"] in {"estimate", "ci_low", "ci_high"}}
    actual = {"n:estimate": float(len(face["pairs"])), "icc_a1:estimate": face["stats"]["icc_a1"], "icc_a1:ci_low": face["boot_summary"]["icc_a1"]["percentile_2.5"], "icc_a1:ci_high": face["boot_summary"]["icc_a1"]["percentile_97.5"], "icc_c1:estimate": face["stats"]["icc_c1"], "pearson:estimate": face["stats"]["pearson"], "spearman:estimate": face["stats"]["spearman"], "mean_paired_difference:estimate": face["stats"]["difference_summary"]["mean"], "mean_paired_difference:ci_low": face["boot_summary"]["mean_difference"]["percentile_2.5"], "mean_paired_difference:ci_high": face["boot_summary"]["mean_difference"]["percentile_97.5"]}
    # Include all independently published correlation/change values and their CIs.
    actual.update({"icc_c1:ci_low": face["boot_summary"]["icc_c1"]["percentile_2.5"], "icc_c1:ci_high": face["boot_summary"]["icc_c1"]["percentile_97.5"], "pearson:ci_low": face["boot_summary"]["pearson"]["percentile_2.5"], "pearson:ci_high": face["boot_summary"]["pearson"]["percentile_97.5"], "spearman:ci_low": face["boot_summary"]["spearman"]["percentile_2.5"], "spearman:ci_high": face["boot_summary"]["spearman"]["percentile_97.5"]})
    rows, passed = [], True
    for key, expected in sorted(reference.items()):
        metric, quantity = key.split(":")
        actual_value = actual.get(key)
        ok = actual_value is not None and abs(actual_value - expected) <= 1e-9
        rows.append({"task_key": "face_memory", "statistic": metric, "quantity": quantity, "expected_independent_value": expected, "actual_step4b_value": actual_value, "absolute_difference": abs(actual_value - expected) if actual_value is not None else "", "tolerance": 1e-9, "within_tolerance": "yes" if ok else "no"})
        passed = passed and ok
    if len(face["pairs"]) != 59:
        passed = False
    return rows, passed


def write_report(all_results: list[dict[str, Any]], reproduction: list[dict[str, Any]], passed: bool, inputs: dict[str, Any]) -> None:
    lines = ["# CHAVI Step 4B review report", "", "Step 4B is a task-level longitudinal dependability analysis of five prespecified raw Penn LEAD fields. It does not construct profiles or make diagnostic, clinical, predictive, AI, or external-dataset conclusions.", "", "## Results", "", "| Task | Candidate participants | Excluded | Pairs | ICC(A,1) | Bootstrap 95% CI | Mean later-minus-earlier | Bootstrap 95% CI | Bland-Altman LoA |", "|---|---:|---:|---:|---:|---|---:|---|---|"]
    for result in all_results:
        t, s = result["task"], result["stats"]
        ba_mean = s['difference_summary']['mean']; ba_sd = s['difference_summary']['sd'] or 0.0
        lines.append(f"| {t['label']} | {len(result['accounting'])} | {len(result['exclusions'])} | {len(result['pairs'])} | {s['icc_a1']:.6f} | [{result['boot_summary']['icc_a1']['percentile_2.5']:.6f}, {result['boot_summary']['icc_a1']['percentile_97.5']:.6f}] | {ba_mean:.6f} | [{result['boot_summary']['mean_difference']['percentile_2.5']:.6f}, {result['boot_summary']['mean_difference']['percentile_97.5']:.6f}] | [{ba_mean - 1.96 * ba_sd:.6f}, {ba_mean + 1.96 * ba_sd:.6f}] |")
    lines += ["", "## Accounting and QC", "", "For every task, candidate participants partition exactly into one included primary pair or one exclusion. Missing earlier and later score counts are reported in `five_task_descriptive_results.csv` under `pre_pair_missingness` before complete-pair filtering. Exclusions retain row-level reasons and observed QC/score statuses in `five_task_exclusions.csv`. Exact `V` and `F` are primary inclusion codes; invalid, skipped, excluded, unresolved, missing, and nonfinite states are not silently merged.", "", "## Timing", "", "Pairs are ordered by numeric session label and require a strictly positive nominal session interval. Rounded/anonymized acquisition timing is reported separately; missing or nonpositive timing is not silently treated as an exact positive cognitive-assessment interval. Interval distributions and timing missingness are in `five_task_interval_audit.csv`.", "", "## Face Memory reproduction", "", f"Face Memory independent reproduction: **{'PASS' if passed else 'FAIL'}**. The detailed comparison is in `face_memory_reproduction_check.csv`; the required independent result is n=59, ICC(A,1) approximately 0.560473, bootstrap CI approximately [0.343745, 0.718958], and mean change approximately 0.847458 with CI approximately [-0.372881, 2.034322].", "", "## Boundaries", "", "No arbitrary reliability labels are applied. Correlation, ICC, and mean-change estimates describe the released score fields across eligible recorded occasions only; they do not separate development, practice, state change, and measurement noise, and they do not establish task-version equivalence or clinical validity.", "", "## Reproducibility", "", f"The pinned dataset Git state before and after execution is required to remain clean at `{DATASET_COMMIT}`. Step 4A and Step 4A-R inputs are hash-recorded. Prior Step 4A output directories are hash-checked before and after execution. Focused tests are listed in `step4b_reproduction_and_tests.md`.", "", "## Scientific-review readiness", "", f"Five-task task-level foundation ready for scientific review: **{'YES' if passed else 'NO'}**, conditional on review of the explicit task-specific exclusions, unresolved timing/version metadata, and interval distributions. This package does not automatically continue to Phase 2."]
    (OUT / "step4b_review_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_method_notes(all_results: list[dict[str, Any]], inputs: dict[str, Any]) -> None:
    text = f"""# CHAVI Step 4B method notes

## Frozen scope

The five prespecified fields are Letter N-back `{TASKS[0]['score_field']}`, Face Memory `{TASKS[1]['score_field']}`, Matrix Reasoning `{TASKS[2]['score_field']}`, Emotion Recognition `{TASKS[3]['score_field']}`, and Dominant Finger Tapping `{TASKS[4]['score_field']}`. The source is the local verified Step 1B payload corresponding to Penn LEAD ds007116 snapshot 1.0.6 at commit `{DATASET_COMMIT}`.

## Eligibility and pairing

All raw rows are counted before filtering. A score is eligible only when finite, its QC code is exactly `V` or `F`, its session label is `ses-<integer>`, and the Step 3B occasion is not marked as a continuation without a new CNB occasion. Invalid/skipped/excluded QC takes precedence as the row-level exclusion reason when score missingness is also present. The first two eligible observations per participant are selected in strict numeric session order. Nonpositive nominal intervals are rejected. Participants contribute at most one pair per task.

## Statistics

ICC(A,1) is two-way random-effects absolute agreement, single measure, with the documented ANOVA formula `(MS_R - MS_E) / (MS_R + (k-1)MS_E + k*(MS_C-MS_E)/n)` for `k=2`. ICC(C,1), Pearson, Spearman, later-minus-earlier mean change, and descriptive Bland-Altman limits of agreement are sensitivities/descriptives. Negative estimates are retained and no arbitrary reliability categories are used.

## Bootstrap

Each task uses {BOOTSTRAP_REPLICATES} resamples of n participant pairs with replacement and seed {BOOTSTRAP_SEED}. The participant pair is the resampling unit. Repeated sampled participants remain repeated bootstrap copies and are not collapsed. Percentile intervals use linear interpolation at 2.5% and 97.5%.

## Missingness and timing correction

Missing earlier and later score counts are computed from the first two source observations per participant before complete-pair filtering. Structural absence of a later candidate slot is reported separately. Timing is derived from rounded/anonymized acquisition metadata only when available and positive; it is not presented as exact cognitive-assessment timing.

## Reproduction and integrity

Face Memory is compared against the independent Step 4A-R statistical crosscheck in `face_memory_reproduction_check.csv`. Input hashes, dataset Git state, and prior Step 4A/Step 4A-R directory hashes are in `step4b_provenance.json`. The new output directory is the only directory written by this script.
"""
    (OUT / "step4b_method_notes.md").write_text(text, encoding="utf-8")


def write_reproduction_and_tests(tests: list[str], reproduction_passed: bool) -> None:
    text = f"""# CHAVI Step 4B reproduction and focused tests

Run from the project root:

```powershell
python .\\chavi_analysis_ds007116_step4b_five_tasks_20260916\\run_step4b_task_analysis.py
python -m unittest -v .\\chavi_analysis_ds007116_step4b_five_tasks_20260916\\test_step4b_task_analysis.py
```

The analysis uses Python `{sys.version.split()[0]}` standard-library parsing, statistics, deterministic bootstrap resampling, and custom SVG/PNG rendering. The participant pair is the bootstrap unit; each task uses {BOOTSTRAP_REPLICATES} resamples with seed {BOOTSTRAP_SEED}. Face Memory independent regression reproduction: **{'PASS' if reproduction_passed else 'FAIL'}**.

Focused checks implemented:

{chr(10).join('- ' + test for test in tests)}

No dataset, Step 3A/3B directory, Step 4A directory, or Step 4A-R directory is written by the analysis script. Integrity hashes are recorded in `step4b_provenance.json`.
"""
    (OUT / "step4b_reproduction_and_tests.md").write_text(text, encoding="utf-8")


def write_provenance(inputs: dict[str, Any], contract_value: dict[str, Any], all_results: list[dict[str, Any]], tests: list[str], reproduction_passed: bool) -> None:
    git_after = git_state()
    dataset_input_hashes_after = [input_hash(Path(item["path"]), item["role"]) for item in inputs["dataset_input_hashes_before"]]
    prior_after = {directory: directory_hashes(Path(directory)) for directory in inputs["prior_output_hashes_before"]}
    if git_after != inputs["git_before"] or git_after["commit"] != DATASET_COMMIT or git_after["status"] != "## main...origin/main":
        raise Step4BError(f"Dataset Git state changed or is not pinned: before={inputs['git_before']} after={git_after}")
    if dataset_input_hashes_after != inputs["dataset_input_hashes_before"] or prior_after != inputs["prior_output_hashes_before"]:
        raise Step4BError("Dataset input or prior Step 4A output hashes changed during Step 4B")
    result_summary = [{"task_key": r["task"]["task_key"], "candidate_participants": len(r["accounting"]), "excluded_participants": len(r["exclusions"]), "included_pairs": len(r["pairs"]), "icc_a1": r["stats"]["icc_a1"], "icc_a1_ci": [r["boot_summary"]["icc_a1"]["percentile_2.5"], r["boot_summary"]["icc_a1"]["percentile_97.5"]], "mean_change": r["stats"]["difference_summary"]["mean"], "mean_change_ci": [r["boot_summary"]["mean_difference"]["percentile_2.5"], r["boot_summary"]["mean_difference"]["percentile_97.5"]], "bootstrap_valid_replicates": r["boot_summary"]["icc_a1"]["successful_replicates"]} for r in all_results]
    provenance = {"generated_utc": utc_now(), "dataset_snapshot": "1.0.6", "dataset_commit_expected": DATASET_COMMIT, "git_before": inputs["git_before"], "git_after": git_after, "dataset_input_hashes_before": inputs["dataset_input_hashes_before"], "dataset_input_hashes_after": dataset_input_hashes_after, "prior_output_hashes_before": inputs["prior_output_hashes_before"], "prior_output_hashes_after": prior_after, "input_hashes": inputs["input_hashes"], "executed_script_path": str(Path(__file__).resolve()), "executed_script_sha256": sha256(Path(__file__).resolve()), "contract_path": str((OUT / "step4b_analysis_contract.json").resolve()), "contract_sha256": sha256(OUT / "step4b_analysis_contract.json"), "face_memory_reproduction_passed": reproduction_passed, "results_summary": result_summary, "tests": tests, "boundaries": contract_value["explicit_non_actions"]}
    (OUT / "step4b_provenance.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_analysis() -> dict[str, Any]:
    inputs = load_inputs()
    if inputs["git_before"]["commit"] != DATASET_COMMIT or inputs["git_before"]["status"] != "## main...origin/main":
        raise Step4BError(f"Dataset is not at required clean pinned state: {inputs['git_before']}")
    contract_value = contract(inputs)
    all_results = []
    for task in TASKS:
        observations = build_observations(task, inputs)
        accounting, pairs, exclusions, intervals = candidate_accounting(task, observations)
        if len(pairs) < 2:
            raise Step4BError(f"Too few pairs for {task['label']}: {len(pairs)}")
        stats = point_statistics(pairs)
        boot_rows, boot_summary = bootstrap(pairs)
        all_results.append({"task": task, "observations": observations, "accounting": accounting, "pairs": pairs, "exclusions": exclusions, "intervals": intervals, "stats": stats, "bootstrap_rows": boot_rows, "boot_summary": boot_summary})
    write_outputs(inputs, all_results, contract_value)
    reproduction, reproduction_passed = face_memory_reproduction(all_results)
    write_csv(OUT / "face_memory_reproduction_check.csv", reproduction)
    tests = ["known ICC(A,1) and ICC(C,1) fixture", "deterministic participant-level bootstrap", "pre-filter missing earlier/later accounting", "exact V/F QC inclusion and explicit invalidity precedence", "one primary pair per participant and strict visit ordering", "positive nominal interval enforcement and nonpositive interval rejection", "duplicate analytical-key rejection", "Face Memory independent regression reproduction", "PNG/SVG plot generation with labels, sample size, identity/zero/LoA lines", "dataset input and prior-output hashes unchanged"]
    write_method_notes(all_results, inputs); write_reproduction_and_tests(tests, reproduction_passed); write_report(all_results, reproduction, reproduction_passed, inputs); write_provenance(inputs, contract_value, all_results, tests, reproduction_passed)
    return {"tasks": [{"task_key": r["task"]["task_key"], "pairs": len(r["pairs"]), "icc_a1": r["stats"]["icc_a1"], "icc_a1_ci": [r["boot_summary"]["icc_a1"]["percentile_2.5"], r["boot_summary"]["icc_a1"]["percentile_97.5"]], "mean_change": r["stats"]["difference_summary"]["mean"], "mean_change_ci": [r["boot_summary"]["mean_difference"]["percentile_2.5"], r["boot_summary"]["mean_difference"]["percentile_97.5"]]} for r in all_results], "face_memory_reproduction_passed": reproduction_passed}


if __name__ == "__main__":
    try:
        print(json.dumps(run_analysis(), indent=2))
    except Step4BError as exc:
        print(f"STEP4B ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
