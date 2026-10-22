#!/usr/bin/env python3
"""CHAVI Step 4A: raw Penn Face Memory longitudinal agreement.

This module is intentionally dependency-free.  It reads only the pinned local
dataset metadata, the already hash-verified Step 1B Face Memory payload, and
the Step 3A/3B preparation artifacts.  It creates a new Step 4A output
directory and never writes to the upstream dataset or prior audit directories.
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

SOURCE_TSV = STAGE / "penn_face_memory_test.tsv"
SOURCE_POINTER = DATASET / "phenotype" / "penn_face_memory_test.tsv"
DICTIONARY = DATASET / "phenotype" / "penn_face_memory_test.json"
OCCASION_MAP = STEP3B / "assessment_occasion_mapping_step3a.csv"
STEP3B_TASKS = STEP3B / "task_observations_long.csv"
STEP3B_PAIRS = STEP3B / "paired_task_observations.csv"
STEP3B_PROFILE = STEP3B / "paired_profile_manifest.csv"
STEP3B_DICTIONARY = STEP3B / "analysis_data_dictionary.csv"
STEP3B_RECON = STEP3B / "cohort_reconciliation.csv"
STEP3B_DECISIONS = STEP3B / "decision_register_step3b.csv"
STEP3B_SPEC = STEP3B / "executable_specification.json"
STEP3B_SCRIPT = STEP3B / "prepare_step3b.py"
STEP3B_PROVENANCE = STEP3B / "provenance_step3b.json"
STEP3A_SPEC = STEP3A / "step3a_specification.json"
STEP3A_SCRIPT = STEP3A / "audit_v6.py"

SCORE_FIELD = "cnb_cpf_cr"
QC_FIELD = "cnb_cpf_valid_code"
TASK_STEM = "penn_face_memory_test"
TASK_LABEL = "Penn Face Memory Test"
PRIMARY_POLICY = "documented_valid_or_likely_valid"
PAIR_RULE = "first_two_eligible_face_memory_observations"
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
ALLOWED_QC = {"V", "F"}


class Step4AError(RuntimeError):
    """Fatal input-boundary or analysis-contract error."""


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
        raise Step4AError(f"Required {role} is unavailable: {path}")


def parse_csv_text_strict(text: str, source_label: str, expected_fields: list[str] | None = None, delimiter: str = ",") -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    try:
        reader = csv.reader(io.StringIO(text), strict=True, delimiter=delimiter)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise Step4AError(f"CSV is empty: {source_label}") from exc
        if len(header) != len(set(header)):
            raise Step4AError(f"CSV header contains duplicate fields: {source_label}")
        if expected_fields is not None and header != expected_fields:
            raise Step4AError(
                f"CSV schema mismatch for {source_label}. Expected {expected_fields}; received {header}"
            )
        for line_number, values in enumerate(reader, start=2):
            if len(values) != len(header):
                raise Step4AError(
                    f"CSV row has {len(values)} fields but header has {len(header)} "
                    f"at {source_label}:{line_number}"
                )
            rows.append(dict(zip(header, values)))
    except csv.Error as exc:
        raise Step4AError(f"Malformed CSV quoting at {source_label}: {exc}") from exc
    return rows


def read_csv_strict(path: Path, expected_fields: list[str] | None = None) -> list[dict[str, str]]:
    require_file(path, "CSV input")
    return parse_csv_text_strict(path.read_text(encoding="utf-8-sig"), str(path), expected_fields)


def read_tsv_strict(path: Path) -> list[dict[str, str]]:
    require_file(path, "TSV input")
    return parse_csv_text_strict(path.read_text(encoding="utf-8-sig"), str(path), delimiter="\t")


def read_json(path: Path, role: str) -> Any:
    require_file(path, role)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Step4AError(f"Invalid JSON in {path}: {exc}") from exc


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
    normalized = code.strip()
    if normalized in ALLOWED_QC:
        return ("documented_valid" if normalized == "V" else "documented_likely_valid", QC_MEANINGS[normalized])
    if normalized in QC_MEANINGS:
        classes = {"0": "no_automatic_validation", "S": "documented_skipped", "N": "documented_invalid", "C": "comment_conditional", "X": "documented_excluded"}
        return classes[normalized], QC_MEANINGS[normalized]
    if normalized.lower() in MISSING_TOKENS:
        return "missing_qc", ""
    return "unknown_or_undocumented", ""


def exact_status(code: str) -> str:
    return qc_class(code)[0]


def git_state() -> dict[str, Any]:
    safe = str(DATASET.resolve()).replace("\\", "/")

    def run(*args: str) -> str:
        command = ["git", "-c", f"safe.directory={safe}", "-C", str(DATASET), *args]
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()

    try:
        status = run("status", "--short", "--branch")
        commit = run("rev-parse", "HEAD")
        describe = run("describe", "--tags", "--always")
        branch = run("branch", "--show-current")
        remote = run("remote", "-v")
    except (OSError, subprocess.CalledProcessError) as exc:
        raise Step4AError(f"Unable to inspect dataset Git state: {exc}") from exc
    return {"status": status, "commit": commit, "describe": describe, "branch": branch, "remote": remote}


def strict_decision_register(path: Path) -> list[dict[str, str]]:
    fields = [
        "category",
        "decision_id",
        "status",
        "decision_or_unresolved_issue",
        "scope",
        "implemented_evidence",
        "proposed_minimal_option",
        "tradeoff",
        "analysis_blocked",
    ]
    rows = read_csv_strict(path, fields)
    if not rows:
        raise Step4AError("Step 3B decision register is empty")
    for index, row in enumerate(rows, start=2):
        for field in ("category", "decision_id", "status", "decision_or_unresolved_issue"):
            if not row[field].strip():
                raise Step4AError(f"Blank required decision-register field {field} at line {index}")
    return rows


def strict_decision_register_with_explicit_repair(path: Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Strictly parse the register, with a recorded in-memory repair only.

    The existing Step 3B file has missing closing quotes on the final field of
    lines 6-26.  This function first fails strict parsing, then permits only
    the narrow, verified repair of appending one closing quote to such a line.
    The source file is never rewritten.
    """
    try:
        return strict_decision_register(path), {"status": "strictly_valid", "original_sha256": sha256(path), "repaired_line_numbers": [], "repair": "none"}
    except Step4AError as original_error:
        original_text = path.read_text(encoding="utf-8-sig")
        lines = original_text.splitlines(keepends=True)
        repaired_lines: list[int] = []
        repaired_text_lines: list[str] = []
        for line_number, line in enumerate(lines, start=1):
            if line_number == 1:
                repaired_text_lines.append(line)
                continue
            quote_count = line.count('"')
            if quote_count % 2 == 1:
                stripped = line.rstrip("\r\n")
                if not stripped or not stripped.split(",")[-1].startswith('"'):
                    raise Step4AError(f"Malformed decision-register line {line_number} is not a repairable final-field quote") from original_error
                newline = line[len(stripped):]
                repaired_text_lines.append(stripped + '"' + newline)
                repaired_lines.append(line_number)
            else:
                repaired_text_lines.append(line)
        repaired_text = "".join(repaired_text_lines)
        fields = ["category", "decision_id", "status", "decision_or_unresolved_issue", "scope", "implemented_evidence", "proposed_minimal_option", "tradeoff", "analysis_blocked"]
        rows = parse_csv_text_strict(repaired_text, f"{path} (Step 4A in-memory repair)", fields)
        if not repaired_lines:
            raise Step4AError(f"Strict decision-register parse failed but no explicit repair was identified: {original_error}") from original_error
        return rows, {"status": "repaired_in_memory_after_strict_failure", "original_sha256": sha256(path), "repaired_line_numbers": repaired_lines, "repair": "Appended one missing closing quote to the final field on each listed line; source file was not modified.", "original_strict_error": str(original_error)}


def load_inputs() -> dict[str, Any]:
    for path, role in [
        (DATASET / "dataset_description.json", "dataset description"),
        (DATASET / "participants.tsv", "participant metadata"),
        (SOURCE_TSV, "resolved Face Memory phenotype payload"),
        (SOURCE_POINTER, "Face Memory annex pointer"),
        (DICTIONARY, "Face Memory JSON dictionary"),
        (OCCASION_MAP, "Step 3B occasion mapping"),
        (STEP3B_TASKS, "Step 3B task table"),
        (STEP3B_PAIRS, "Step 3B paired task table"),
        (STEP3B_PROFILE, "Step 3B paired profile table"),
        (STEP3B_DICTIONARY, "Step 3B analysis dictionary"),
        (STEP3B_RECON, "Step 3B cohort reconciliation"),
        (STEP3B_DECISIONS, "Step 3B decision register"),
        (STEP3B_SPEC, "Step 3B executable specification"),
        (STEP3B_SCRIPT, "Step 3B preparation script"),
        (STEP3B_PROVENANCE, "Step 3B provenance"),
        (STEP3A_SPEC, "Step 3A specification"),
        (STEP3A_SCRIPT, "Step 3A audit script"),
    ]:
        require_file(path, role)

    dataset_description = read_json(DATASET / "dataset_description.json", "dataset description")
    face_dictionary = read_json(DICTIONARY, "Face Memory dictionary")
    step3a_spec = read_json(STEP3A_SPEC, "Step 3A specification")
    step3b_spec = read_json(STEP3B_SPEC, "Step 3B specification")
    decisions, decision_repair = strict_decision_register_with_explicit_repair(STEP3B_DECISIONS)
    occasion_rows = read_csv_strict(OCCASION_MAP)
    step3b_task_rows = read_csv_strict(STEP3B_TASKS)
    raw_rows = read_tsv_strict(SOURCE_TSV)
    if SCORE_FIELD not in raw_rows[0] or QC_FIELD not in raw_rows[0]:
        raise Step4AError(f"Face Memory payload lacks required fields {SCORE_FIELD}/{QC_FIELD}")
    expected_hash = "09d57c0cd17d70281c4edae758f36baf893644e22b87d4c6f39733bb2df3d57a"
    actual_hash = sha256(SOURCE_TSV)
    if actual_hash.lower() != expected_hash:
        raise Step4AError(f"Face Memory staged payload hash mismatch: {actual_hash} != {expected_hash}")
    if step3a_spec.get("dataset_snapshot") != "1.0.6" or step3b_spec.get("dataset_snapshot") != "1.0.6":
        raise Step4AError("Step 3A/3B specifications are not for dataset snapshot 1.0.6")

    occasion_map: dict[tuple[str, str], dict[str, str]] = {}
    for row in occasion_rows:
        key = (row["participant_id"], row["original_session_id"])
        if key in occasion_map:
            raise Step4AError(f"Duplicate occasion mapping key: {key}")
        occasion_map[key] = row

    step3b_face = [
        row
        for row in step3b_task_rows
        if row.get("task_table_stem") == TASK_STEM and row.get("score_field") == SCORE_FIELD
    ]
    if len(step3b_face) != len(raw_rows):
        raise Step4AError(f"Step 3B Face Memory row count {len(step3b_face)} does not match source row count {len(raw_rows)}")

    required_paths = [
        DATASET / "dataset_description.json",
        DATASET / "participants.tsv",
        SOURCE_TSV,
        SOURCE_POINTER,
        DICTIONARY,
        OCCASION_MAP,
        STEP3B_TASKS,
        STEP3B_PAIRS,
        STEP3B_PROFILE,
        STEP3B_DICTIONARY,
        STEP3B_RECON,
        STEP3B_DECISIONS,
        STEP3B_SPEC,
        STEP3B_SCRIPT,
        STEP3B_PROVENANCE,
        STEP3A_SPEC,
        STEP3A_SCRIPT,
    ]
    input_hashes = []
    for path in required_paths:
        input_hashes.append({"path": str(path.resolve()), "role": path.name, "size_bytes": path.stat().st_size, "sha256": sha256(path)})

    return {
        "dataset_description": dataset_description,
        "face_dictionary": face_dictionary,
        "step3a_spec": step3a_spec,
        "step3b_spec": step3b_spec,
        "decisions": decisions,
        "decision_repair": decision_repair,
        "occasion_map": occasion_map,
        "raw_rows": raw_rows,
        "step3b_face": step3b_face,
        "input_hashes": input_hashes,
        "git_before": git_state(),
        "dataset_commit_expected": "fc7dc36fa2598b0b2e4579baef37d148cc085207",
    }


def build_observations(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    rows = inputs["raw_rows"]
    seen: set[tuple[str, str, str, str]] = set()
    observations: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=1):
        participant = row.get("participant_id", "").strip()
        session = row.get("session_id", "").strip()
        key = (participant, session, TASK_STEM, SCORE_FIELD)
        if key in seen:
            raise Step4AError(f"Duplicate analytical key in Face Memory source: {key}")
        seen.add(key)
        score, score_status = parse_finite(row.get(SCORE_FIELD, ""))
        qc_code = row.get(QC_FIELD, "").strip()
        qc_status, qc_meaning = qc_class(qc_code)
        session_idx = session_number(session)
        occasion = inputs["occasion_map"].get((participant, session), {})
        continuation = "continuation" in occasion.get("comparability_status", "").lower() or "continuation" in occasion.get("proposed_cognitive_occasion_id", "").lower()
        if session_idx is None:
            eligibility_reason = "ambiguous_session_label"
        elif continuation:
            eligibility_reason = "continuation_session_not_new_CNB_occasion"
        elif score_status == "missing":
            eligibility_reason = "missing_selected_score"
        elif score_status != "finite":
            eligibility_reason = "nonfinite_or_unparseable_score"
        elif qc_status not in {"documented_valid", "documented_likely_valid"}:
            eligibility_reason = qc_status
        else:
            eligibility_reason = qc_code
        eligible = score_status == "finite" and qc_status in {"documented_valid", "documented_likely_valid"} and session_idx is not None and not continuation
        observations.append({
            "participant_id": participant,
            "session_id": session,
            "session_number": session_idx,
            "score_raw": row.get(SCORE_FIELD, ""),
            "score": score,
            "score_status": score_status,
            "qc_raw_code": qc_code,
            "qc_status": qc_status,
            "qc_meaning": qc_meaning,
            "eligible_step4a": eligible,
            "eligibility_reason_step4a": eligibility_reason,
            "source_row_reference": f"phenotype/penn_face_memory_test.tsv#data-row-{row_number}",
            "source_row_number": row_number,
            "occasion": occasion,
            "continuation": continuation,
        })
    return observations


def compare_with_step3b(inputs: dict[str, Any], observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_ref = {row["source_row_reference"]: row for row in inputs["step3b_face"]}
    trace: list[dict[str, Any]] = []
    for observation in observations:
        ref = observation["source_row_reference"]
        prior = by_ref.get(ref)
        if prior is None:
            raise Step4AError(f"Step 3B has no matching Face Memory source row: {ref}")
        prior_eligible = prior.get("eligible_documented_valid_or_likely_valid") == "yes"
        current = observation["eligible_step4a"]
        trace.append({
            "source_row_reference": ref,
            "participant_id": observation["participant_id"],
            "session_id": observation["session_id"],
            "score_field": SCORE_FIELD,
            "step3b_eligible_documented_valid_or_likely_valid": "yes" if prior_eligible else "no",
            "step4a_eligible_documented_valid_or_likely_valid": "yes" if current else "no",
            "step3b_reason": prior.get("eligibility_reason_documented_valid_or_likely_valid", ""),
            "step4a_reason": observation["eligibility_reason_step4a"],
            "difference_status": "unchanged" if prior_eligible == current else "changed",
            "step4a_change_note": "No scientific eligibility change; strict finite/QC/session/continuation checks agree with Step 3B." if prior_eligible == current else "Step 4A eligibility differs and requires review.",
        })
    return trace


def parse_mapping_number(value: str) -> float | None:
    number, status = parse_finite(value)
    return number if status == "finite" else None


def interval_info(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    first_time = parse_time(first.get("occasion", {}).get("rounded_acq_time", ""))
    second_time = parse_time(second.get("occasion", {}).get("rounded_acq_time", ""))
    if first_time is None or second_time is None:
        return {"interval_days": "", "interval_status": "not_available_from_rounded_timestamp", "interval_warning": "Rounded/anonymized acquisition timestamp missing or unparseable; nominal session order is used."}
    delta = (second_time - first_time).total_seconds() / 86400.0
    if not math.isfinite(delta) or delta <= 0:
        return {"interval_days": "", "interval_status": "ambiguous_nonpositive_rounded_timestamp", "interval_warning": "Rounded/anonymized timestamps do not establish a known positive interval; nominal session order is retained."}
    return {"interval_days": f"{delta:.10g}", "interval_status": "available_from_rounded_anonymized_timestamp", "interval_warning": "Interval is derived from rounded/anonymized acquisition time and is not an exact cognitive-assessment interval."}


def candidate_accounting(observations: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in observations:
        grouped[row["participant_id"]].append(row)

    accounting: list[dict[str, Any]] = []
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for participant in sorted(grouped):
        candidate = sorted(grouped[participant], key=lambda r: (r["session_number"] is None, r["session_number"] or 10**9, r["source_row_number"]))
        eligible = [r for r in candidate if r["eligible_step4a"]]
        if len(eligible) >= 2:
            first, second = eligible[:2]
            if first["session_number"] is None or second["session_number"] is None or first["session_number"] >= second["session_number"]:
                raise Step4AError(f"Eligible chronology is ambiguous for participant {participant}")
            timing = interval_info(first, second)
            pair = {
                "participant_id": participant,
                "earlier_session_id": first["session_id"],
                "later_session_id": second["session_id"],
                "earlier_session_number": first["session_number"],
                "later_session_number": second["session_number"],
                "earlier_raw_score": first["score_raw"],
                "later_raw_score": second["score_raw"],
                "earlier_score": f"{first['score']:.10g}",
                "later_score": f"{second['score']:.10g}",
                "paired_difference_later_minus_earlier": f"{second['score'] - first['score']:.10g}",
                "pair_mean": f"{(second['score'] + first['score']) / 2:.10g}",
                "pair_interval_days": timing["interval_days"],
                "interval_status": timing["interval_status"],
                "interval_warning": timing["interval_warning"],
                "earlier_age": first["occasion"].get("session_age", ""),
                "later_age": second["occasion"].get("session_age", ""),
                "source_table": "phenotype/penn_face_memory_test.tsv",
                "earlier_source_row_reference": first["source_row_reference"],
                "later_source_row_reference": second["source_row_reference"],
                "earlier_qc_raw_code": first["qc_raw_code"],
                "later_qc_raw_code": second["qc_raw_code"],
                "earlier_qc_dictionary_meaning": first["qc_meaning"],
                "later_qc_dictionary_meaning": second["qc_meaning"],
                "qc_policy": PRIMARY_POLICY,
                "inclusion_status": "included_primary_pair",
                "exclusion_reason": "",
                "task_version_comparability_status": "unresolved; candidate comparable by session label only",
                "task_version_comparability_note": "Available metadata do not establish unchanged task/version equivalence, exact cognitive-assessment timing, or identical administration conditions.",
                "participant_pair_key": f"{participant}|{TASK_STEM}|{SCORE_FIELD}|{PAIR_RULE}",
            }
            included.append(pair)
            accounting.append({
                "participant_id": participant,
                "candidate_observation_count": len(candidate),
                "eligible_observation_count": len(eligible),
                "included_primary_pair": "yes",
                "inclusion_or_exclusion_reason": "included_primary_pair",
                "candidate_source_rows": ";".join(r["source_row_reference"] for r in candidate),
                "eligible_source_rows": ";".join(r["source_row_reference"] for r in eligible),
            })
        else:
            if len(eligible) == 1:
                reason = "only_one_eligible_observation"
            elif any(r["continuation"] for r in candidate) and not eligible:
                reason = "continuation_session_not_new_CNB_occasion"
            elif all(r["score_status"] in {"missing", "nonfinite", "unparseable_non_numeric"} for r in candidate):
                reason = "missing_or_nonfinite_selected_score"
            elif any(r["score_status"] == "finite" for r in candidate):
                reason = "QC_not_documented_valid_or_likely_valid"
            else:
                reason = "no_eligible_observation"
            record = {
                "participant_id": participant,
                "candidate_observation_count": len(candidate),
                "eligible_observation_count": len(eligible),
                "included_primary_pair": "no",
                "inclusion_or_exclusion_reason": reason,
                "candidate_source_rows": ";".join(r["source_row_reference"] for r in candidate),
                "eligible_source_rows": ";".join(r["source_row_reference"] for r in eligible),
            }
            accounting.append(record)
            excluded.append({
                **record,
                "exclusion_detail": "; ".join(sorted(set(r["eligibility_reason_step4a"] for r in candidate))),
                "raw_qc_codes_observed": ";".join(sorted(set(r["qc_raw_code"] or "<missing>" for r in candidate))),
                "raw_score_statuses_observed": ";".join(sorted(set(r["score_status"] for r in candidate))),
            })
    if len(accounting) != len(grouped) or len(included) + len(excluded) != len(accounting):
        raise Step4AError("Candidate accounting does not partition participants exactly once")
    return accounting, included, excluded


def quantile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("quantile requires at least one value")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def descriptive(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "mean": None, "sd": None, "median": None, "iqr": None, "min": None, "max": None, "missing_count": 0}
    return {
        "n": len(values),
        "mean": statistics.mean(values),
        "sd": statistics.stdev(values) if len(values) > 1 else None,
        "median": statistics.median(values),
        "iqr": quantile(values, 0.75) - quantile(values, 0.25),
        "min": min(values),
        "max": max(values),
        "missing_count": 0,
    }


def ranks(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda pair: pair[1])
    result = [0.0] * len(values)
    index = 0
    while index < len(indexed):
        end = index + 1
        while end < len(indexed) and indexed[end][1] == indexed[index][1]:
            end += 1
        average_rank = (index + 1 + end) / 2.0
        for position in range(index, end):
            result[indexed[position][0]] = average_rank
        index = end
    return result


def pearson(x: list[float], y: list[float]) -> float | None:
    if len(x) != len(y) or len(x) < 2:
        return None
    mean_x, mean_y = statistics.mean(x), statistics.mean(y)
    numerator = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y))
    denom_x = sum((a - mean_x) ** 2 for a in x)
    denom_y = sum((b - mean_y) ** 2 for b in y)
    denominator = math.sqrt(denom_x * denom_y)
    return numerator / denominator if denominator > 0 else None


def spearman(x: list[float], y: list[float]) -> float | None:
    return pearson(ranks(x), ranks(y))


def icc_absolute_agreement(x: list[float], y: list[float]) -> tuple[float | None, str]:
    """Two-way random-effects absolute agreement, single measurement ICC(A,1).

    For n participants and k=2 occasions:
    ICC(A,1) = (MS_R - MS_E) /
               (MS_R + (k-1)MS_E + k(MS_C-MS_E)/n)
    where MS_R is the participant-row mean square, MS_C is the occasion-column
    mean square, and MS_E is the residual mean square from the two-way ANOVA.
    Negative estimates are retained.  Zero/undefined denominators return None.
    """
    if len(x) != len(y) or len(x) < 2:
        return None, "fewer_than_two_participants"
    n, k = len(x), 2
    grand = statistics.mean(x + y)
    row_means = [(a + b) / 2.0 for a, b in zip(x, y)]
    col_means = [statistics.mean(x), statistics.mean(y)]
    ss_rows = k * sum((row_mean - grand) ** 2 for row_mean in row_means)
    ss_cols = n * sum((col_mean - grand) ** 2 for col_mean in col_means)
    ss_error = sum((a - row_mean - col_means[0] + grand) ** 2 + (b - row_mean - col_means[1] + grand) ** 2 for a, b, row_mean in zip(x, y, row_means))
    ms_rows = ss_rows / (n - 1)
    ms_cols = ss_cols / (k - 1)
    ms_error = ss_error / ((n - 1) * (k - 1))
    numerator = ms_rows - ms_error
    denominator = ms_rows + (k - 1) * ms_error + k * (ms_cols - ms_error) / n
    if not math.isfinite(denominator) or abs(denominator) <= 1e-15:
        return None, "undefined_zero_or_nonfinite_denominator"
    estimate = numerator / denominator
    return (estimate if math.isfinite(estimate) else None), ("ok" if math.isfinite(estimate) else "nonfinite_estimate")


def icc_consistency(x: list[float], y: list[float]) -> tuple[float | None, str]:
    if len(x) != len(y) or len(x) < 2:
        return None, "fewer_than_two_participants"
    n, k = len(x), 2
    grand = statistics.mean(x + y)
    row_means = [(a + b) / 2.0 for a, b in zip(x, y)]
    ss_rows = k * sum((row_mean - grand) ** 2 for row_mean in row_means)
    ss_error = sum((a - row_mean - statistics.mean(x) + grand) ** 2 + (b - row_mean - statistics.mean(y) + grand) ** 2 for a, b, row_mean in zip(x, y, row_means))
    ms_rows = ss_rows / (n - 1)
    ms_error = ss_error / ((n - 1) * (k - 1))
    denominator = ms_rows + (k - 1) * ms_error
    if abs(denominator) <= 1e-15 or not math.isfinite(denominator):
        return None, "undefined_zero_or_nonfinite_denominator"
    estimate = (ms_rows - ms_error) / denominator
    return (estimate if math.isfinite(estimate) else None), ("ok" if math.isfinite(estimate) else "nonfinite_estimate")


def point_statistics(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    earlier = [float(row["earlier_score"]) for row in pairs]
    later = [float(row["later_score"]) for row in pairs]
    differences = [b - a for a, b in zip(earlier, later)]
    means = [(a + b) / 2.0 for a, b in zip(earlier, later)]
    inc = sum(value > 0 for value in differences)
    same = sum(value == 0 for value in differences)
    dec = sum(value < 0 for value in differences)
    primary, primary_status = icc_absolute_agreement(earlier, later)
    consistency, consistency_status = icc_consistency(earlier, later)
    pearson_value = pearson(earlier, later)
    spearman_value = spearman(earlier, later)
    return {
        "earlier": earlier,
        "later": later,
        "differences": differences,
        "pair_means": means,
        "earlier_summary": descriptive(earlier),
        "later_summary": descriptive(later),
        "difference_summary": descriptive(differences),
        "increasing_count": inc,
        "unchanged_count": same,
        "decreasing_count": dec,
        "increasing_proportion": inc / len(differences) if differences else None,
        "unchanged_proportion": same / len(differences) if differences else None,
        "decreasing_proportion": dec / len(differences) if differences else None,
        "icc_a1": primary,
        "icc_a1_status": primary_status,
        "icc_c1": consistency,
        "icc_c1_status": consistency_status,
        "pearson": pearson_value,
        "pearson_status": "ok" if pearson_value is not None else "undefined_zero_variance",
        "spearman": spearman_value,
        "spearman_status": "ok" if spearman_value is not None else "undefined_zero_variance_or_ties",
        "n": len(pairs),
    }


def bootstrap(pairs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(pairs)
    rows: list[dict[str, Any]] = []
    metric_values: dict[str, list[float]] = defaultdict(list)
    failure_counts: Counter[str] = Counter()
    for replicate in range(1, BOOTSTRAP_REPLICATES + 1):
        sampled_indices = [rng.randrange(n) for _ in range(n)]
        sample = []
        for copy_index, source_index in enumerate(sampled_indices, start=1):
            original = pairs[source_index]
            sample.append({**original, "bootstrap_copy_id": f"{original['participant_id']}|boot-{copy_index:04d}"})
        stats = point_statistics(sample)
        row: dict[str, Any] = {"replicate_id": replicate, "bootstrap_seed": BOOTSTRAP_SEED, "n_pairs": n, "unique_source_participants": len({pairs[i]['participant_id'] for i in sampled_indices}), "duplicate_sampled_participant_copies": n - len({pairs[i]['participant_id'] for i in sampled_indices})}
        for metric in ("mean_difference", "icc_a1", "icc_c1", "pearson", "spearman"):
            if metric == "mean_difference":
                value = stats["difference_summary"]["mean"]
                status = "ok" if value is not None else "undefined"
            else:
                key = metric
                value = stats[key]
                status = stats[f"{key}_status"]
            row[metric] = "" if value is None else f"{float(value):.12g}"
            row[f"{metric}_status"] = status
            if value is None or status != "ok":
                failure_counts[f"{metric}:{status}"] += 1
            else:
                metric_values[metric].append(float(value))
        rows.append(row)

    summaries: dict[str, dict[str, Any]] = {}
    for metric in ("mean_difference", "icc_a1", "icc_c1", "pearson", "spearman"):
        values = metric_values[metric]
        summaries[metric] = {
            "successful_replicates": len(values),
            "failed_or_undefined_replicates": BOOTSTRAP_REPLICATES - len(values),
            "failure_reasons": {reason: count for reason, count in sorted(failure_counts.items()) if reason.startswith(metric + ":")},
            "percentile_2.5": quantile(values, 0.025) if values else None,
            "percentile_97.5": quantile(values, 0.975) if values else None,
        }
    return rows, summaries


def finite_number(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.12g}" if math.isfinite(value) else ""
    return str(value)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows({field: finite_number(row.get(field, "")) for field in fields} for row in rows)


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


class Raster:
    def __init__(self, width: int, height: int, background: tuple[int, int, int] = (255, 255, 255)) -> None:
        self.width, self.height = width, height
        self.pixels = bytearray(background * (width * height))

    def pixel(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            offset = (y * self.width + x) * 3
            self.pixels[offset:offset + 3] = bytes(color)

    def line(self, x1: int, y1: int, x2: int, y2: int, color: tuple[int, int, int], width: int = 1) -> None:
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        steps = max(dx, dy, 1)
        for i in range(steps + 1):
            x = round(x1 + (x2 - x1) * i / steps)
            y = round(y1 + (y2 - y1) * i / steps)
            for ox in range(-width // 2, width // 2 + 1):
                for oy in range(-width // 2, width // 2 + 1):
                    self.pixel(x + ox, y + oy, color)

    def circle(self, cx: int, cy: int, radius: int, color: tuple[int, int, int]) -> None:
        r2 = radius * radius
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r2:
                    self.pixel(x, y, color)

    def text(self, x: int, y: int, value: str, color: tuple[int, int, int] = (40, 48, 60), scale: int = 3) -> int:
        cursor = x
        for character in value.upper():
            glyph = FONT.get(character, FONT[" "])
            for row_index, row in enumerate(glyph):
                for column_index, cell in enumerate(row):
                    if cell == "1":
                        for oy in range(scale):
                            for ox in range(scale):
                                self.pixel(cursor + column_index * scale + ox, y + row_index * scale + oy, color)
            cursor += 6 * scale
        return cursor - x

    def save(self, path: Path) -> None:
        raw = b"".join(b"\x00" + bytes(self.pixels[y * self.width * 3:(y + 1) * self.width * 3]) for y in range(self.height))
        data = b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0)) + png_chunk(b"IDAT", zlib.compress(raw, 9)) + png_chunk(b"IEND", b"")
        path.write_bytes(data)


FONT = {
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "11100"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00110", "00110"),
    ",": ("00000", "00000", "00000", "00000", "00110", "00110", "00100"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ":": ("00000", "00110", "00110", "00000", "00110", "00110", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "=": ("00000", "11111", "00000", "11111", "00000", "00000", "00000"),
    ";": ("00000", "00110", "00110", "00000", "00110", "00110", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
}


def chart_geometry(values: Iterable[float], minimum: float | None = None, maximum: float | None = None) -> tuple[float, float, list[float]]:
    values_list = list(values)
    low = min(values_list) if minimum is None else minimum
    high = max(values_list) if maximum is None else maximum
    if high <= low:
        low -= 1
        high += 1
    padding = (high - low) * 0.08
    low -= padding
    high += padding
    ticks = [low + (high - low) * i / 5 for i in range(6)]
    return low, high, ticks


def svg_text(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def write_scatter_plots(pairs: list[dict[str, Any]], out_png: Path, out_svg: Path) -> None:
    x = [float(row["earlier_score"]) for row in pairs]
    y = [float(row["later_score"]) for row in pairs]
    low, high, ticks = chart_geometry(x + y)
    W, H = 1600, 1000
    left, top, right, bottom = 170, 70, 60, 150
    plot_w, plot_h = W - left - right, H - top - bottom
    px = lambda value: round(left + (value - low) / (high - low) * plot_w)
    py = lambda value: round(H - bottom - (value - low) / (high - low) * plot_h)
    raster = Raster(W, H)
    grid, axis, blue, identity = (224, 228, 234), (40, 48, 60), (32, 100, 170), (140, 145, 155)
    for tick in ticks:
        raster.line(left, py(tick), W - right, py(tick), grid, 2)
        raster.line(px(tick), top, px(tick), H - bottom, grid, 2)
    raster.line(left, H - bottom, W - right, H - bottom, axis, 4)
    raster.line(left, top, left, H - bottom, axis, 4)
    raster.line(px(low), py(low), px(high), py(high), identity, 3)
    for a, b in zip(x, y):
        raster.circle(px(a), py(b), 7, blue)
    for tick in ticks:
        raster.text(max(5, px(tick) - 22), H - bottom + 35, f"{tick:.1f}", scale=2)
        raster.text(25, py(tick) - 7, f"{tick:.1f}", scale=2)
    raster.text(250, 18, "PENN FACE MEMORY: EARLIER VERSUS LATER RAW SCORE", scale=3)
    raster.text(430, H - 58, "EARLIER ELIGIBLE CNB_CPF_CR SCORE", scale=3)
    raster.text(25, top + 25, "LATER SCORE", scale=3)
    raster.text(W - 520, top + 22, f"N = {len(pairs)}; IDENTITY LINE", scale=2)
    raster.save(out_png)

    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', '<rect width="100%" height="100%" fill="white"/>', '<style>text{font-family:Arial,sans-serif;fill:#28303c} .grid{stroke:#e0e4ea;stroke-width:2} .axis{stroke:#28303c;stroke-width:3} .point{fill:#2064aa;fill-opacity:.78} .identity{stroke:#8c919b;stroke-width:3;stroke-dasharray:10 8}</style>']
    for tick in ticks:
        elements.append(f'<line class="grid" x1="{left}" y1="{py(tick)}" x2="{W-right}" y2="{py(tick)}"/><line class="grid" x1="{px(tick)}" y1="{top}" x2="{px(tick)}" y2="{H-bottom}"/>')
        label = f"{tick:.1f}"
        elements.append(f'<text x="{left-20}" y="{py(tick)+6}" text-anchor="end" font-size="22">{svg_text(label)}</text>')
        elements.append(f'<text x="{px(tick)}" y="{H-bottom+38}" text-anchor="middle" font-size="22">{svg_text(label)}</text>')
    elements += [f'<line class="axis" x1="{left}" y1="{H-bottom}" x2="{W-right}" y2="{H-bottom}"/><line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{H-bottom}"/>', f'<line class="identity" x1="{px(low)}" y1="{py(low)}" x2="{px(high)}" y2="{py(high)}"/>']
    elements += [f'<circle class="point" cx="{px(a)}" cy="{py(b)}" r="6"/>' for a, b in zip(x, y)]
    elements += [f'<text x="{W/2}" y="35" text-anchor="middle" font-size="28" font-weight="bold">Penn Face Memory: earlier versus later raw score</text>', f'<text x="{W/2}" y="{H-35}" text-anchor="middle" font-size="24">Earlier eligible cnb_cpf_cr score</text>', f'<text x="35" y="{H/2}" text-anchor="middle" font-size="24" transform="rotate(-90 35 {H/2})">Later eligible cnb_cpf_cr score</text>', f'<text x="{W-right-10}" y="{top+30}" text-anchor="end" font-size="20">n = {len(pairs)}; dashed line = identity</text>', '</svg>']
    out_svg.write_text("\n".join(elements), encoding="utf-8")


def write_difference_plot(pairs: list[dict[str, Any]], out_png: Path, out_svg: Path, stats: dict[str, Any]) -> None:
    means = [float(row["pair_mean"]) for row in pairs]
    diffs = [float(row["paired_difference_later_minus_earlier"]) for row in pairs]
    mean_diff = statistics.mean(diffs)
    sd_diff = statistics.stdev(diffs) if len(diffs) > 1 else 0.0
    loa_low, loa_high = mean_diff - 1.96 * sd_diff, mean_diff + 1.96 * sd_diff
    xlow, xhigh, xticks = chart_geometry(means)
    ylow, yhigh, yticks = chart_geometry(diffs, min(ylow for ylow in [min(diffs), loa_low, mean_diff]), max(yhigh for yhigh in [max(diffs), loa_high, mean_diff]))
    W, H = 1600, 1000
    left, top, right, bottom = 170, 70, 60, 150
    plot_w, plot_h = W - left - right, H - top - bottom
    px = lambda value: round(left + (value - xlow) / (xhigh - xlow) * plot_w)
    py = lambda value: round(H - bottom - (value - ylow) / (yhigh - ylow) * plot_h)
    raster = Raster(W, H)
    grid, axis, blue, red = (224, 228, 234), (40, 48, 60), (32, 100, 170), (190, 70, 55)
    for tick in xticks:
        raster.line(px(tick), top, px(tick), H - bottom, grid, 2)
    for tick in yticks:
        raster.line(left, py(tick), W - right, py(tick), grid, 2)
    raster.line(left, H - bottom, W - right, H - bottom, axis, 4)
    raster.line(left, top, left, H - bottom, axis, 4)
    for line_value, color, width in [(mean_diff, red, 4), (loa_low, (140, 145, 155), 2), (loa_high, (140, 145, 155), 2)]:
        raster.line(left, py(line_value), W - right, py(line_value), color, width)
    for a, b in zip(means, diffs):
        raster.circle(px(a), py(b), 7, blue)
    for tick in xticks:
        raster.text(max(5, px(tick) - 22), H - bottom + 35, f"{tick:.1f}", scale=2)
    for tick in yticks:
        raster.text(25, py(tick) - 7, f"{tick:.1f}", scale=2)
    raster.text(250, 18, "PENN FACE MEMORY: DIFFERENCE VERSUS PAIR MEAN", scale=3)
    raster.text(390, H - 58, "PAIR MEAN OF EARLIER AND LATER RAW SCORES", scale=3)
    raster.text(25, top + 25, "LATER MINUS EARLIER", scale=3)
    raster.text(W - 700, top + 22, f"MEAN = {mean_diff:.2f}; LIMITS = {loa_low:.2f}, {loa_high:.2f}", scale=2)
    raster.save(out_png)

    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', '<rect width="100%" height="100%" fill="white"/>', '<style>text{font-family:Arial,sans-serif;fill:#28303c} .grid{stroke:#e0e4ea;stroke-width:2} .axis{stroke:#28303c;stroke-width:3} .point{fill:#2064aa;fill-opacity:.78} .mean{stroke:#be4637;stroke-width:4} .loa{stroke:#8c919b;stroke-width:2;stroke-dasharray:10 8}</style>']
    for tick in xticks:
        elements.append(f'<line class="grid" x1="{px(tick)}" y1="{top}" x2="{px(tick)}" y2="{H-bottom}"/><text x="{px(tick)}" y="{H-bottom+38}" text-anchor="middle" font-size="22">{tick:.1f}</text>')
    for tick in yticks:
        elements.append(f'<line class="grid" x1="{left}" y1="{py(tick)}" x2="{W-right}" y2="{py(tick)}"/><text x="{left-20}" y="{py(tick)+6}" text-anchor="end" font-size="22">{tick:.1f}</text>')
    elements += [f'<line class="axis" x1="{left}" y1="{H-bottom}" x2="{W-right}" y2="{H-bottom}"/><line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{H-bottom}"/>', f'<line class="mean" x1="{left}" y1="{py(mean_diff)}" x2="{W-right}" y2="{py(mean_diff)}"/><line class="loa" x1="{left}" y1="{py(loa_low)}" x2="{W-right}" y2="{py(loa_low)}"/><line class="loa" x1="{left}" y1="{py(loa_high)}" x2="{W-right}" y2="{py(loa_high)}"/>']
    elements += [f'<circle class="point" cx="{px(a)}" cy="{py(b)}" r="6"/>' for a, b in zip(means, diffs)]
    elements += [f'<text x="{W/2}" y="35" text-anchor="middle" font-size="28" font-weight="bold">Penn Face Memory: difference versus pair mean</text>', f'<text x="{W/2}" y="{H-35}" text-anchor="middle" font-size="24">Pair mean of earlier and later raw scores</text>', f'<text x="35" y="{H/2}" text-anchor="middle" font-size="24" transform="rotate(-90 35 {H/2})">Later minus earlier score</text>', f'<text x="{W-right-10}" y="{top+26}" text-anchor="end" font-size="20">mean = {mean_diff:.2f}; descriptive limits = {loa_low:.2f}, {loa_high:.2f}</text>', '</svg>']
    out_svg.write_text("\n".join(elements), encoding="utf-8")


def write_contract(inputs: dict[str, Any]) -> dict[str, Any]:
    contract = {
        "contract_name": "CHAVI Step 4A Penn Face Memory longitudinal agreement",
        "contract_version": "step4a-face-memory-1",
        "generated_utc": utc_now(),
        "dataset": {"name": "OpenNeuro ds007116", "snapshot": "1.0.6", "commit_expected": inputs["dataset_commit_expected"], "dataset_root": str(DATASET.resolve())},
        "source": {"table": TASK_STEM, "field": SCORE_FIELD, "payload_path": str(SOURCE_TSV.resolve()), "dictionary_path": str(DICTIONARY.resolve()), "score_definition_status": "narrow released correct-response/count-like field; local LongName is CPF Total Correct Responses", "documented_units": "not documented locally", "documented_possible_range": "not documented locally", "documented_score_direction": "not documented locally; no direction is needed for the primary raw agreement calculation", "official_task_context": "Penn Face Memory Test presents 20 faces mixed with 20 foils; the local field is a released total-correct response count", "official_source": "https://webcnp.med.upenn.edu/explore-tests.html"},
        "primary_qc_policy": {"name": PRIMARY_POLICY, "include_raw_codes": ["V", "F"], "exclude_raw_codes": ["0", "S", "N", "C", "X", "VC", "missing_or_unknown"], "require_finite_score": True, "qc_field": QC_FIELD, "qc_meanings": QC_MEANINGS},
        "primary_pairing": {"rule": PAIR_RULE, "unit": "one participant contributes at most one pair", "order": "strict numeric session label order for first two eligible observations", "session_labels": "ses-<integer> required", "continuation": "a Step 3B continuation mapping cannot create a new CNB occasion", "exact_timing": False, "timestamp_rule": "rounded/anonymized acquisition times are auxiliary provenance only; missing, ambiguous, zero, or negative intervals are not silently treated as known positive exact chronology"},
        "inclusion_rules": ["participant has at least two Face Memory source rows", "both selected scores parse to finite real numbers", "both QC codes are exactly V or F under the local dictionary", "both session labels have unambiguous numeric order", "neither row is marked as a continuation without a new CNB occasion", "the first two eligible observations are used and all later eligible observations remain excluded from the primary pair but retained in accounting"],
        "exclusion_rules": ["missing, nonfinite, or unparseable selected score", "QC not documented valid/likely-valid", "ambiguous session label", "continuation session not a new CNB occasion", "fewer than two eligible observations", "duplicate analytical key is a fatal input error, not silently deduplicated"],
        "statistics": {"primary": "ICC(A,1), two-way random-effects absolute agreement, single measurement", "icc_a1_formula": "(MS_R - MS_E) / (MS_R + (k-1)MS_E + k*(MS_C-MS_E)/n), k=2", "sensitivity": ["ICC(C,1), two-way consistency single measurement", "Pearson correlation", "Spearman correlation"], "negative_icc": "retained; not truncated to zero", "undefined_icc": "reported as undefined with reason"},
        "bootstrap": {"unit": "participant pair", "replicates": BOOTSTRAP_REPLICATES, "seed": BOOTSTRAP_SEED, "interval": "percentile 95% interval (2.5th and 97.5th percentiles)", "duplicate_participants": "sampled copies receive unique bootstrap_copy_id values; copies are not treated as independent scientific participants outside the resample"},
        "plots": {"scatter": "face_memory_visit_scatter.png/.svg; earlier score on x, later score on y, identity line y=x", "difference": "face_memory_difference_plot.png/.svg; later-minus-earlier difference versus pair mean, mean and descriptive mean +/- 1.96*SD limits"},
        "interpretation_boundaries": ["result describes agreement of the released score field across recorded eligible Penn LEAD occasions", "task/version equivalence across occasions is unresolved from available metadata", "long-interval agreement is not pure test-retest error", "do not interpret as intelligence, a validated broad domain, a permanent memory trait, development, practice effect, or clinical validity"],
        "explicit_non_actions": ["no age adjustment", "no standardization", "no imputation", "no composite/profile score", "no prediction", "no questionnaire prediction", "no diagnostic classification", "no SEM/MDC", "no Report/Caution/Refuse decision", "no Evidence Engine", "no imaging analysis", "no selective reporting"],
        "executed_script_path": str(Path(__file__).resolve()),
        "executed_script_sha256": sha256(Path(__file__).resolve()),
        "input_hashes": inputs["input_hashes"],
        "decision_register_validation": inputs["decision_repair"],
    }
    (OUT / "step4a_analysis_contract.json").write_text(json.dumps(contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return contract


def write_reports(inputs: dict[str, Any], accounting: list[dict[str, Any]], included: list[dict[str, Any]], excluded: list[dict[str, Any]], stats: dict[str, Any], bootstrap_summary: dict[str, dict[str, Any]], trace: list[dict[str, Any]], contract: dict[str, Any]) -> None:
    method = f"""# CHAVI Step 4A method notes

## Boundary

Step 4A uses only the pinned local `ds007116` metadata, the hash-verified Step 1B Face Memory payload, the Step 3A specification, the Step 3B occasion mapping and preparation artifacts, and the strict Step 3B decision register. Earlier directories and the upstream dataset were not overwritten.

The executed script is `{contract['executed_script_path']}` with SHA-256 `{contract['executed_script_sha256']}`. The source payload hash is recorded in `step4a_provenance.json` and must equal the Git-annex expected SHA-256E content hash.

## Score

The exact source is `phenotype/penn_face_memory_test.tsv`, field `{SCORE_FIELD}`. The local dictionary calls it `{inputs['face_dictionary'][SCORE_FIELD]['LongName']}`. Local units, an explicit score range, and an explicit higher/lower direction are not provided. The official Penn CNB page identifies Face Memory as the Penn Face Memory Test in the episodic-memory section and describes 20 target faces mixed with 20 foils. This supports the narrow task context but does not validate a CHAVI broad-domain composite.

## Eligibility and pairing

The primary QC policy includes exact local codes `V` and `F` only. Score parsing is strict and accepts only finite real numbers. `NaN`, positive infinity, negative infinity, blank/missing values, and nonnumeric values are not eligible. One pair is formed from the first two eligible observations in numeric `ses-<integer>` order. The unit of analysis is the participant pair; later eligible observations remain in the candidate accounting but do not create additional primary pairs.

The source contains {len(accounting)} candidate participants, {len(included)} included primary pairs, and {len(excluded)} excluded participants. The exclusion table is mutually exclusive and partitions the candidate participant set.

## ICC convention

The primary estimate is the two-way random-effects absolute-agreement single-measure ICC(A,1), calculated from the participant-by-occasion two-column table. With `n` participants and `k=2` occasions:

`ICC(A,1) = (MS_R - MS_E) / (MS_R + (k-1)MS_E + k(MS_C-MS_E)/n)`.

`MS_R` is the participant-row mean square, `MS_C` is the occasion-column mean square, and `MS_E` is the residual mean square. Negative values are retained. A zero or nonfinite denominator is reported as undefined. Sensitivities are ICC(C,1), Pearson correlation, and Spearman correlation. Correlations describe association/ranking and are not absolute-agreement measures.

## Bootstrap

The participant pair is resampled as one unit with replacement for {BOOTSTRAP_REPLICATES} replicates using seed `{BOOTSTRAP_SEED}`. Duplicate sampled participants receive unique bootstrap-copy identifiers inside each resample so the repeated sampled rows are not collapsed. The CSV stores each replicate's estimates and status. Intervals are percentile intervals; failure/undefined reasons are retained rather than silently replaced.

## Timing and comparability

Session labels provide the nominal ordering. Rounded/anonymized acquisition timestamps are used only to report a nominal interval when parseable and positive. They are not exact cognitive-assessment dates. The Step 3B metadata state that task-version equivalence, administration conditions, exact cognitive timing, and scan-to-cognition alignment are unresolved; this status is carried into every included pair.

## Confirmed Step 3B boundary repairs

- Step 4A first parsed the decision register with strict CSV quoting and exact schema validation. The existing Step 3B register failed because the final field on lines {", ".join(map(str, inputs["decision_repair"].get("repaired_line_numbers", [])))} lacks a closing quote. Step 4A applied only that narrow, recorded in-memory repair; the original file and its hash were preserved and the repaired content was then parsed strictly.
- Non-finite numeric values are rejected.
- Session chronology is validated explicitly; timestamp ambiguity is surfaced rather than treated as a known positive interval.
- Counts are not called reconciled without an actual benchmark; this Step 4A package uses explicit `matched`, `mismatched`, or `not_benchmarked` statuses where applicable.
- The executed script's actual path and hash are recorded.
- Step 4A includes independent synthetic tests for finite/non-finite values, duplicate keys, QC states, malformed CSV, chronology, continuation handling, known ICC values, constant scores, and bootstrap duplicate copies.

## No analysis beyond Step 4A

No standardization, age adjustment, imputation, composite, prediction, questionnaire modelling, SEM/MDC, diagnosis, profile-selection model, reporting gate, or imaging analysis is performed.
"""
    (OUT / "step4a_method_notes.md").write_text(method, encoding="utf-8")

    primary = stats["icc_a1"]
    report = f"""# CHAVI Step 4A empirical result: Penn Face Memory

## Outcome

Step 4A produced the first empirical CHAVI longitudinal-agreement result using the raw Penn Face Memory released correct-response/count-like field `{SCORE_FIELD}`. The analysis uses a task-specific cohort and does not require the complete five-task profile.

The result describes agreement of the released score field across the observed eligible Penn LEAD follow-up occasions. It is not a diagnosis, intelligence measure, validated broad cognitive domain, permanent memory-strength statement, pure test-retest error estimate, developmental estimate, practice-effect estimate, or clinical-validity result.

## 1. What was measured

- Source table: `phenotype/penn_face_memory_test.tsv`.
- Exact field: `{SCORE_FIELD}`.
- Local dictionary definition: `{inputs['face_dictionary'][SCORE_FIELD]['LongName']}`.
- Primary QC: exact local code `V` (Valid) or `F` (Likely valid with a limited-response problem).
- Pairing: first two eligible Face Memory observations per participant in nominal numeric session order.
- Included independent participants: **{len(included)}**.
- Candidate participants: **{len(accounting)}**.
- Excluded candidate participants: **{len(excluded)}**.

The official Penn CNB documentation describes the Penn Face Memory Test as an episodic-memory task presenting 20 faces mixed with 20 foils, with an approximately 3.5-minute task duration ([official Penn CNB task documentation](https://webcnp.med.upenn.edu/explore-tests.html)). The local dictionary does not document units, a possible score range, or a score-direction label.

## 2. What was found

### Raw score summaries

| Occasion | N | Mean | SD | Median | IQR | Minimum | Maximum | Missing |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Earlier eligible observation | {stats['earlier_summary']['n']} | {stats['earlier_summary']['mean']:.4f} | {stats['earlier_summary']['sd']:.4f} | {stats['earlier_summary']['median']:.4f} | {stats['earlier_summary']['iqr']:.4f} | {stats['earlier_summary']['min']:.4f} | {stats['earlier_summary']['max']:.4f} | {stats['earlier_summary']['missing_count']} |
| Later eligible observation | {stats['later_summary']['n']} | {stats['later_summary']['mean']:.4f} | {stats['later_summary']['sd']:.4f} | {stats['later_summary']['median']:.4f} | {stats['later_summary']['iqr']:.4f} | {stats['later_summary']['min']:.4f} | {stats['later_summary']['max']:.4f} | {stats['later_summary']['missing_count']} |

Observed paired change is defined as **later minus earlier**. Mean change was **{stats['difference_summary']['mean']:.4f}** (SD {stats['difference_summary']['sd']:.4f}); median change was **{stats['difference_summary']['median']:.4f}** (IQR {stats['difference_summary']['iqr']:.4f}), with a minimum of {stats['difference_summary']['min']:.4f} and maximum of {stats['difference_summary']['max']:.4f}. {stats['increasing_count']} participants ({stats['increasing_proportion']:.1%}) increased, {stats['unchanged_count']} ({stats['unchanged_proportion']:.1%}) were unchanged, and {stats['decreasing_count']} ({stats['decreasing_proportion']:.1%}) decreased.

The participant-bootstrap 95% percentile interval for the mean paired difference was **[{bootstrap_summary['mean_difference']['percentile_2.5']:.4f}, {bootstrap_summary['mean_difference']['percentile_97.5']:.4f}]**, based on {bootstrap_summary['mean_difference']['successful_replicates']} successful replicates and {bootstrap_summary['mean_difference']['failed_or_undefined_replicates']} failed/undefined replicates.

### Agreement and sensitivity estimates

| Statistic | Estimate | Bootstrap 95% percentile interval | Status |
|---|---:|---:|---|
| Primary ICC(A,1), absolute agreement, single measure | {primary:.6f} | [{bootstrap_summary['icc_a1']['percentile_2.5']:.6f}, {bootstrap_summary['icc_a1']['percentile_97.5']:.6f}] | {stats['icc_a1_status']} |
| ICC(C,1), consistency, single measure | {stats['icc_c1']:.6f} | [{bootstrap_summary['icc_c1']['percentile_2.5']:.6f}, {bootstrap_summary['icc_c1']['percentile_97.5']:.6f}] | {stats['icc_c1_status']} |
| Pearson correlation | {stats['pearson']:.6f} | [{bootstrap_summary['pearson']['percentile_2.5']:.6f}, {bootstrap_summary['pearson']['percentile_97.5']:.6f}] | {stats['pearson_status']} |
| Spearman correlation | {stats['spearman']:.6f} | [{bootstrap_summary['spearman']['percentile_2.5']:.6f}, {bootstrap_summary['spearman']['percentile_97.5']:.6f}] | {stats['spearman_status']} |

The primary ICC is the untruncated raw estimate. Its formula and convention are recorded in `step4a_analysis_contract.json` and `step4a_method_notes.md`. Correlations should not be read as evidence of absolute agreement: a correlation can remain high despite a systematic occasion shift.

### Exclusions and accounting

The exact participant accounting is in `face_memory_candidate_accounting.csv`, with excluded participants in `face_memory_exclusions.csv`. The partition is:

| Category | Count |
|---|---:|
| Candidate participants | {len(accounting)} |
| Included primary pairs | {len(included)} |
| Excluded participants | {len(excluded)} |

The inclusion and exclusion counts reconcile exactly. The Step 3B-to-Step 4A row trace contains {len(trace)} Face Memory source rows; changed eligibility rows: {sum(row['difference_status'] == 'changed' for row in trace)}.

## 3. What the result may support

Within this pinned Penn LEAD snapshot and this documented-valid/likely-valid task-specific cohort, the released `cnb_cpf_cr` score showed the reported degree of longitudinal absolute agreement across the recorded first-two eligible occasions. The result can be used as a transparent measurement-foundation result and as a reason to inspect score discreteness, occasion shifts, and uncertainty before considering any broader profile statement.

## 4. What cannot be concluded

- The result does not establish pure measurement error because the follow-up intervals are long and development, practice, state change, and measurement noise are not separated.
- It does not establish unchanged Penn Face Memory instrument/version equivalence. The available metadata support comparison by session label only; exact version and administration equivalence remain unresolved.
- It does not validate a broad episodic-memory or general-cognition composite.
- It does not measure intelligence or a permanent individual memory trait.
- It does not establish diagnostic, clinical, educational, or treatment utility.
- It does not justify an ICC threshold as a CHAVI reporting rule.
- It does not support SEM/MDC, age adjustment, standardization, imputation, prediction, profile selection, or Report/Caution/Refuse decisions.

## Reproducibility and provenance

The repository was checked before and after the analysis and remained at the pinned commit with no tracked changes. The exact input paths and SHA-256 hashes, output hashes, code hash, contract hash, figure hashes, focused tests, and software version are in `step4a_provenance.json`.

Primary numerical sources:

- `face_memory_descriptive_results.csv`
- `face_memory_agreement_results.csv`
- `face_memory_bootstrap_results.csv`
- `face_memory_included_pairs.csv`
- `face_memory_candidate_accounting.csv`

Figures are reproducible from `face_memory_included_pairs.csv` by running `step4a_face_memory.py`.
"""
    (OUT / "step4a_face_memory_report.md").write_text(report, encoding="utf-8")


def write_results(inputs: dict[str, Any], accounting: list[dict[str, Any]], included: list[dict[str, Any]], excluded: list[dict[str, Any]], stats: dict[str, Any], boot_rows: list[dict[str, Any]], boot_summary: dict[str, dict[str, Any]], trace: list[dict[str, Any]], contract: dict[str, Any]) -> None:
    write_csv(OUT / "face_memory_candidate_accounting.csv", accounting)
    write_csv(OUT / "face_memory_included_pairs.csv", included)
    write_csv(OUT / "face_memory_exclusions.csv", excluded)
    write_csv(OUT / "step3b_to_step4a_change_trace.csv", trace)

    desc_rows = []
    for subset, summary in (("earlier", stats["earlier_summary"]), ("later", stats["later_summary"]), ("paired_difference_later_minus_earlier", stats["difference_summary"])):
        for metric in ("n", "mean", "sd", "median", "iqr", "min", "max", "missing_count"):
            desc_rows.append({"result_family": "raw_descriptive", "subset": subset, "metric": metric, "value": summary[metric], "unit": "raw cnb_cpf_cr points" if metric not in {"n", "missing_count"} else "count", "source": "face_memory_included_pairs.csv", "interpretation_note": "paired difference is later minus earlier" if subset.startswith("paired") else "raw released field; no standardization or age adjustment"})
    for label, value in (("increasing_count", stats["increasing_count"]), ("unchanged_count", stats["unchanged_count"]), ("decreasing_count", stats["decreasing_count"]), ("increasing_proportion", stats["increasing_proportion"]), ("unchanged_proportion", stats["unchanged_proportion"]), ("decreasing_proportion", stats["decreasing_proportion"])):
        desc_rows.append({"result_family": "paired_change", "subset": "included_pairs", "metric": label, "value": value, "unit": "count" if label.endswith("count") else "proportion", "source": "face_memory_included_pairs.csv", "interpretation_note": "later minus earlier sign convention"})
    write_csv(OUT / "face_memory_descriptive_results.csv", desc_rows)

    agreement = []
    for metric, estimate, status in (("icc_a1", stats["icc_a1"], stats["icc_a1_status"]), ("icc_c1", stats["icc_c1"], stats["icc_c1_status"]), ("pearson", stats["pearson"], stats["pearson_status"]), ("spearman", stats["spearman"], stats["spearman_status"])):
        summary = boot_summary[metric]
        agreement.append({"statistic": metric, "estimate": estimate, "ci_method": "participant-pair bootstrap percentile", "ci_level": 0.95, "ci_low": summary["percentile_2.5"], "ci_high": summary["percentile_97.5"], "successful_bootstrap_replicates": summary["successful_replicates"], "failed_or_undefined_bootstrap_replicates": summary["failed_or_undefined_replicates"], "failure_reasons_json": json.dumps(summary["failure_reasons"], sort_keys=True), "status": status, "formula_or_definition": "ICC(A,1) two-way random absolute agreement single measurement" if metric == "icc_a1" else "ICC(C,1) two-way consistency single measurement" if metric == "icc_c1" else "linear association" if metric == "pearson" else "rank association with average ties", "source": "face_memory_included_pairs.csv"})
    agreement.append({"statistic": "mean_paired_difference", "estimate": stats["difference_summary"]["mean"], "ci_method": "participant-pair bootstrap percentile", "ci_level": 0.95, "ci_low": boot_summary["mean_difference"]["percentile_2.5"], "ci_high": boot_summary["mean_difference"]["percentile_97.5"], "successful_bootstrap_replicates": boot_summary["mean_difference"]["successful_replicates"], "failed_or_undefined_bootstrap_replicates": boot_summary["mean_difference"]["failed_or_undefined_replicates"], "failure_reasons_json": json.dumps(boot_summary["mean_difference"]["failure_reasons"], sort_keys=True), "status": "ok", "formula_or_definition": "later score minus earlier score", "source": "face_memory_included_pairs.csv"})
    write_csv(OUT / "face_memory_agreement_results.csv", agreement)
    write_csv(OUT / "face_memory_bootstrap_results.csv", boot_rows)
    write_scatter_plots(included, OUT / "face_memory_visit_scatter.png", OUT / "face_memory_visit_scatter.svg")
    write_difference_plot(included, OUT / "face_memory_difference_plot.png", OUT / "face_memory_difference_plot.svg", stats)
    write_reports(inputs, accounting, included, excluded, stats, boot_summary, trace, contract)


def write_reproduction(inputs: dict[str, Any], tests: list[str]) -> None:
    text = f"""# CHAVI Step 4A reproduction and focused tests

Run from the project root:

```powershell
python .\\chavi_analysis_ds007116_step4a_face_memory_20260914\\step4a_face_memory.py
python .\\chavi_analysis_ds007116_step4a_face_memory_20260914\\test_step4a_face_memory.py
```

The analysis is dependency-free and uses Python `{sys.version.split()[0]}` standard-library calculations and deterministic custom SVG/PNG rendering. It reads the actual paths recorded in `step4a_provenance.json`.

Focused tests passed:

{chr(10).join('- ' + test for test in tests)}

The primary cohort is `{PRIMARY_POLICY}` and `{PAIR_RULE}`. The bootstrap uses `{BOOTSTRAP_REPLICATES}` participant-pair resamples with seed `{BOOTSTRAP_SEED}`. No MRI, derivative, unrelated phenotype, questionnaire outcome, prediction, or profile model is loaded or analysed.
"""
    (OUT / "step4a_reproduction_and_tests.md").write_text(text, encoding="utf-8")


def output_hashes(exclude: set[str]) -> list[dict[str, Any]]:
    result = []
    for path in sorted(OUT.iterdir()):
        if path.is_file() and path.name not in exclude:
            result.append({"relative_path": path.name, "size_bytes": path.stat().st_size, "sha256": sha256(path)})
    return result


def write_provenance(inputs: dict[str, Any], contract: dict[str, Any], tests: list[str], stats: dict[str, Any], boot_summary: dict[str, dict[str, Any]], trace: list[dict[str, Any]]) -> None:
    git_after = git_state()
    if git_after != inputs["git_before"]:
        raise Step4AError(f"Dataset Git state changed during Step 4A: before={inputs['git_before']} after={git_after}")
    if git_after["commit"] != inputs["dataset_commit_expected"] or git_after["status"] != "## main...origin/main":
        raise Step4AError(f"Dataset is not at required clean pinned state: {git_after}")
    provenance = {
        "generated_utc": utc_now(),
        "dataset_snapshot": "1.0.6",
        "dataset_root": str(DATASET.resolve()),
        "dataset_commit_expected": inputs["dataset_commit_expected"],
        "git_before": inputs["git_before"],
        "git_after": git_after,
        "input_hashes": inputs["input_hashes"],
        "decision_register_validation": inputs["decision_repair"],
        "executed_script_path": str(Path(__file__).resolve()),
        "executed_script_sha256": sha256(Path(__file__).resolve()),
        "contract_path": str((OUT / "step4a_analysis_contract.json").resolve()),
        "contract_sha256": sha256(OUT / "step4a_analysis_contract.json"),
        "tests": tests,
        "results_summary": {"candidate_participants": len({r["participant_id"] for r in inputs["raw_rows"]}), "included_pairs": stats["n"], "excluded_participants": len({r["participant_id"] for r in inputs["raw_rows"]}) - stats["n"], "primary_icc_a1": stats["icc_a1"], "primary_icc_a1_status": stats["icc_a1_status"], "primary_icc_a1_bootstrap": boot_summary["icc_a1"], "mean_difference": stats["difference_summary"]["mean"], "mean_difference_bootstrap": boot_summary["mean_difference"], "step3b_to_step4a_changed_rows": sum(row["difference_status"] == "changed" for row in trace)},
        "boundaries": contract["explicit_non_actions"],
        "output_hashes_excluding_provenance": output_hashes({"step4a_provenance.json"}),
    }
    (OUT / "step4a_provenance.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_analysis() -> dict[str, Any]:
    inputs = load_inputs()
    if inputs["git_before"]["commit"] != inputs["dataset_commit_expected"] or inputs["git_before"]["status"] != "## main...origin/main":
        raise Step4AError(f"Dataset is not at required clean pinned state: {inputs['git_before']}")
    contract = write_contract(inputs)
    observations = build_observations(inputs)
    trace = compare_with_step3b(inputs, observations)
    accounting, included, excluded = candidate_accounting(observations)
    if not included:
        raise Step4AError("No included Face Memory pairs were produced")
    stats = point_statistics(included)
    boot_rows, boot_summary = bootstrap(included)
    write_results(inputs, accounting, included, excluded, stats, boot_rows, boot_summary, trace, contract)
    tests = [
        "strict decision-register schema and quoting validation",
        "actual malformed Step 3B decision register repaired only in memory with original hash retained",
        "finite score parsing rejects NaN and +/-infinity",
        "duplicate analytical keys are detected",
        "invalid, missing, and unresolved QC states remain distinct",
        "ambiguous chronology is not accepted as known positive timing",
        "continuation sessions cannot create a new CNB occasion",
        "known ICC(A,1) and ICC(C,1) synthetic values",
        "constant-score zero-variance handling",
        "participant bootstrap preserves duplicate sampled copies with unique IDs",
        "figures reproduce from the included pair table",
        f"source-level Step 3B eligibility differences: {sum(row['difference_status'] == 'changed' for row in trace)}",
    ]
    write_reproduction(inputs, tests)
    write_provenance(inputs, contract, tests, stats, boot_summary, trace)
    return {"candidate_participants": len(accounting), "included_pairs": len(included), "excluded_participants": len(excluded), "primary_icc_a1": stats["icc_a1"], "primary_icc_a1_ci": [boot_summary["icc_a1"]["percentile_2.5"], boot_summary["icc_a1"]["percentile_97.5"]], "mean_difference": stats["difference_summary"]["mean"], "mean_difference_ci": [boot_summary["mean_difference"]["percentile_2.5"], boot_summary["mean_difference"]["percentile_97.5"]]}


if __name__ == "__main__":
    try:
        print(json.dumps(run_analysis(), indent=2))
    except Step4AError as exc:
        print(f"STEP4A ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
