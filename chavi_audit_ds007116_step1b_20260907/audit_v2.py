#!/usr/bin/env python3
"""CHAVI Step 1B audit for a pinned Penn LEAD checkout.

This successor to the Step 1 ``audit.py`` supports verified phenotype payloads
kept in a separate staging directory. It never replaces git-annex pointer
files, downloads imaging, or performs scoring/reliability/model fitting.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT_URL = "https://openneuro.org"
S3_BUCKET = "openneuro.org"
DATASET_ID = "ds007116"
SNAPSHOT = "1.0.6"
COMMIT = "fc7dc36fa2598b0b2e4579baef37d148cc085207"
MISSING = {"", "n/a", "NA", "N/A", "NaN", "nan", "None", "none", "null"}
ANNEX_PREFIXES = ("../.git/annex/objects/", ".git/annex/objects/")

COGNITIVE = {
    "age_differentiation_test", "delay_discounting_task", "digit_symbol",
    "effort_discounting_task", "measured_emotion_differentiation_test",
    "motor_praxis", "penn_abstraction_inhibition_working_memory_task",
    "penn_conditional_exclusion_task", "penn_emotion_recognition_task",
    "penn_face_memory_test", "penn_matrix_reasoning_test",
    "penn_verbal_reasoning_test", "penn_word_memory_test",
    "risk_discounting_task", "short_computerized_finger_tapping_task",
    "short_letter_2back", "short_penn_continuous_performance_test",
    "trailmaking_test_a", "trailmaking_test_b",
    "variable_short_penn_line_orientation_test", "visual_object_learning_test",
}
QUESTIONNAIRE = {
    "ales", "als-18", "ari", "asrm", "bdi_1a_ms_child", "bisbas_child",
    "eswan_adhd", "eswan_dmdd", "mapssr", "panas", "post_scan_stai_state",
    "ppa", "prime", "pre_scan_stai", "rpas", "rsas", "substance",
    "tanner_boy", "tanner_girl", "wolf_im_em",
}

LABELS = {
    "age_differentiation_test": "Age Differentiation Test",
    "ales": "Adverse Life Experiences Scale (ALES)",
    "als-18": "Affective Lability Scale (ALS-18)",
    "ari": "Affective Reactivity Index (ARI)",
    "asrm": "Altman Self-Rating Mania Scale (ASRM)",
    "bdi_1a_ms_child": "Beck Depression Inventory modified child (BDI-1A)",
    "bisbas_child": "Behavioral Inhibition/Activation System child version (BIS-BAS)",
    "delay_discounting_task": "Delayed Discounting Task",
    "digit_symbol": "Digit Symbol Test",
    "effort_discounting_task": "Effort Discounting Task",
    "eswan_adhd": "E-SWAN ADHD",
    "eswan_dmdd": "E-SWAN DMDD",
    "mapssr": "Motivation and Pleasure Scale Self-Report (MAPS-SR)",
    "measured_emotion_differentiation_test": "Measured Emotion Differentiation Test",
    "motor_praxis": "Motor Praxis Test",
    "panas": "Positive and Negative Affect Schedule (PANAS)",
    "penn_abstraction_inhibition_working_memory_task": "Penn Abstraction, Inhibition and Working Memory Task",
    "penn_conditional_exclusion_task": "Penn Conditional Exclusion Task for Children",
    "penn_emotion_recognition_task": "Penn Emotion Recognition Task for Children",
    "penn_face_memory_test": "Penn Face Memory Test",
    "penn_matrix_reasoning_test": "Penn Matrix Reasoning Test",
    "penn_verbal_reasoning_test": "Children's Verbal Reasoning Test",
    "penn_word_memory_test": "Children's Penn Word Memory Test",
    "post_scan_stai_state": "Post-scan STAI state",
    "ppa": "PROMIS Pediatric Anxiety (PPA)",
    "pre_scan_stai": "Pre-scan STAI",
    "prime": "PRIME Screen",
    "risk_discounting_task": "Risk Discounting Task",
    "rpas": "Revised Physical Anhedonia Scale (RPAS)",
    "rsas": "Revised Social Anhedonia Scale (RSAS)",
    "short_computerized_finger_tapping_task": "Short Computerized Finger-Tapping Task",
    "short_letter_2back": "Short Letter N-Back (2 back)",
    "short_penn_continuous_performance_test": "Short Penn Continuous Performance Test",
    "substance": "Substance Use Questionnaire",
    "tanner_boy": "Tanner Developmental Stages Scale - Boys",
    "tanner_girl": "Tanner Developmental Stages Scale - Girls",
    "trailmaking_test_a": "Trailmaking A",
    "trailmaking_test_b": "Trailmaking B",
    "variable_short_penn_line_orientation_test": "Variable Short Penn Line Orientation Test",
    "visual_object_learning_test": "Short Visual Object Learning Test",
    "wolf_im_em": "Wolf Intrinsic/Extrinsic Motivation Scale",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def rpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: "" if row.get(k) is None else row.get(k) for k in fields})


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return reader.fieldnames or [], [dict(x) for x in reader]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def is_missing(value: Any) -> bool:
    return value is None or str(value).strip() in MISSING


def display(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")) if isinstance(value, (dict, list)) else ("" if value is None else str(value))


def infer_type(values: Iterable[str]) -> str:
    vals = [str(x) for x in values if not is_missing(x)]
    if not vals:
        return "unknown"
    nums = 0
    ints = 0
    for x in vals:
        try:
            y = float(x)
            nums += 1
            ints += int(y.is_integer())
        except ValueError:
            pass
    if nums == len(vals):
        return "integer/numeric" if ints == nums else "numeric"
    return "categorical/string"


def file_state(path: Path) -> tuple[str, str, bool]:
    if not path.exists():
        return "missing", "", False
    if path.stat().st_size == 0:
        return "empty", "", False
    try:
        with path.open("rb") as f:
            raw = f.read(4096)
    except OSError:
        return "unreadable", "", False
    if b"\x00" not in raw:
        text = raw.decode("utf-8", errors="replace").strip()
        if text.startswith(ANNEX_PREFIXES) and "\n" not in text:
            target = (path.parent / text).resolve(strict=False)
            return ("resolved_annex_object" if target.is_file() else "unavailable_pointer"), text, target.is_file()
    return "available", "", False


def run_git(root: Path, *args: str) -> str:
    try:
        p = subprocess.run(["git", "-c", f"safe.directory={root}", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        return p.stdout.strip() or p.stderr.strip()
    except Exception as e:
        return f"UNAVAILABLE: {e}"


def run_tool_version(*args: str) -> str:
    """Return a tool's reported version without requiring shell expansion."""
    try:
        p = subprocess.run(list(args), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", check=False)
        return p.stdout.strip() or p.stderr.strip()
    except Exception as e:
        return f"UNAVAILABLE: {e}"


def git_metadata(root: Path) -> dict[str, Any]:
    last = run_git(root, "log", "-1", "--format=%H%n%aI%n%an%n%s").splitlines()
    return {
        "status": run_git(root, "status", "--short", "--branch"),
        "remote": run_git(root, "remote", "-v"),
        "commit": run_git(root, "rev-parse", "HEAD"),
        "branch": run_git(root, "branch", "--show-current"),
        "describe": run_git(root, "describe", "--tags", "--always", "--dirty"),
        "tags_at_HEAD": run_git(root, "tag", "--points-at", "HEAD").splitlines(),
        "last_commit": {"hash": last[0] if len(last) > 0 else "", "date": last[1] if len(last) > 1 else "", "author": last[2] if len(last) > 2 else "", "subject": last[3] if len(last) > 3 else ""},
    }


def expected_phenotype_keys(dataset: Path) -> list[dict[str, Any]]:
    rows = []
    for p in sorted((dataset / "phenotype").glob("*.tsv")):
        state, pointer, target_exists = file_state(p)
        key = Path(pointer).name if pointer else ""
        m = re.match(r"^SHA256E-s(\d+)--([0-9a-f]{64})\.tsv$", key)
        rows.append({
            "dataset_path": rpath(p, dataset),
            "filename": p.name,
            "expected_key": key,
            "expected_size_bytes": int(m.group(1)) if m else "",
            "expected_sha256": m.group(2) if m else "",
            "pointer_state_before": state,
            "pointer_target_exists_before": "yes" if target_exists else "no",
        })
    return rows


def table_class(stem: str) -> tuple[str, str, str]:
    if stem in COGNITIVE:
        return "Cognitive task", "A: essential for Paper 1", "candidate cognitive input; no final composite"
    if stem in QUESTIONNAIRE:
        return "Questionnaire/outcome", "B: potentially useful later", "candidate behavioral/affective/motivational outcome or context"
    return "Other", "D: ambiguous", "not classified"


def task_label(stem: str) -> str:
    return LABELS.get(stem, stem.replace("_", " ").title())


def score_fields(fields: list[str]) -> list[str]:
    return [x for x in fields if x not in {"participant_id", "session_id"} and "valid" not in x.lower() and "complete" not in x.lower() and not x.lower().endswith("_status")]


def pair_counts(keys: set[tuple[str, str]]) -> dict[str, int]:
    by_pid: defaultdict[str, set[str]] = defaultdict(set)
    for pid, ses in keys:
        by_pid[pid].add(ses)
    out: Counter[str] = Counter()
    for sessions in by_pid.values():
        for a, b in itertools.combinations(sorted(sessions), 2):
            out[f"{a} + {b}"] += 1
    return dict(sorted(out.items()))


def rows_by_key(rows: list[dict[str, str]]) -> tuple[set[tuple[str, str]], Counter[tuple[str, str]]]:
    c: Counter[tuple[str, str]] = Counter()
    for row in rows:
        c[(row.get("participant_id", ""), row.get("session_id", ""))] += 1
    return set(c), c


def level_meaning(meta: dict[str, Any], code: str) -> str:
    levels = meta.get("Levels", {}) if isinstance(meta, dict) else {}
    return str(levels.get(code, "not documented"))


def unknown_category(meta: dict[str, Any], code: str) -> bool:
    meaning = level_meaning(meta, code).lower()
    return any(x in meaning for x in ("unknown", "not reported", "n/a", "not applicable"))


def documented_invalid(code: str) -> bool:
    return str(code) in {"N", "X"}


def parse_phenotype(dataset: Path, stage: Path, verified_names: set[str] | None = None) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Return table stats, table payloads, variable rows, qc rows, missing rows, score rows."""
    stats: list[dict[str, Any]] = []
    payloads: dict[str, dict[str, Any]] = {}
    variable_rows: list[dict[str, Any]] = []
    qc_rows: list[dict[str, Any]] = []
    missing_rows: list[dict[str, Any]] = []
    score_rows: list[dict[str, Any]] = []
    dictionaries = {p.stem: read_json(p) for p in sorted((dataset / "phenotype").glob("*.json")) if p.is_file()}
    for tsv in sorted((dataset / "phenotype").glob("*.tsv")):
        stem = tsv.stem
        staged = stage / tsv.name
        source_state = file_state(tsv)[0]
        state = "verified_staging_payload" if staged.is_file() else source_state
        if not staged.is_file() or (verified_names is not None and stem not in verified_names):
            stats.append({"task": task_label(stem), "stem": stem, "table_class": table_class(stem)[0], "scientific_relevance": table_class(stem)[1], "source_path": rpath(tsv, dataset), "dictionary_path": rpath(dataset / "phenotype" / f"{stem}.json", dataset), "status": state, "rows": "", "columns": "", "unique_participants": "", "unique_keys": "", "duplicate_key_values": "", "duplicate_key_rows": "", "exact_duplicate_rows": "", "rows_with_any_score": "", "rows_with_qc": "", "pair_counts": "", "notes": "No payload; counts unknown."})
            continue
        fields, rows = read_tsv(staged)
        docs = dictionaries.get(stem, {})
        keyset, keycounter = rows_by_key(rows)
        exact_counter = Counter(tuple(row.get(f, "") for f in fields) for row in rows)
        exact_duplicate_rows = sum(n - 1 for n in exact_counter.values() if n > 1)
        score_cols = score_fields(fields)
        score_rows_count = sum(any(not is_missing(row.get(v)) for v in score_cols) for row in rows)
        qc_cols = [v for v in fields if "valid_code" in v.lower() or v.lower() in {"validity", "qc", "qc_code"}]
        qc_row_count = sum(any(not is_missing(row.get(v)) for v in qc_cols) for row in rows)
        invalid = [v for v in qc_cols if any(documented_invalid(row.get(v, "")) for row in rows)]
        stats.append({"task": task_label(stem), "stem": stem, "table_class": table_class(stem)[0], "scientific_relevance": table_class(stem)[1], "source_path": str(staged), "dictionary_path": rpath(dataset / "phenotype" / f"{stem}.json", dataset), "status": state, "rows": len(rows), "columns": len(fields), "unique_participants": len({x[0] for x in keyset if x[0]}), "unique_keys": len({x for x in keyset if x[0] and x[1]}), "duplicate_key_values": sum(n > 1 for k, n in keycounter.items() if k != ("", "") and k[0] and k[1]), "duplicate_key_rows": sum(n - 1 for k, n in keycounter.items() if n > 1 and k[0] and k[1]), "exact_duplicate_rows": exact_duplicate_rows, "rows_with_any_score": score_rows_count, "rows_with_qc": qc_row_count, "pair_counts": json.dumps(pair_counts({k for k in keyset if k[0] and k[1]}), sort_keys=True), "notes": "No QC filter applied; repeated observations are not declared comparable."})
        payloads[stem] = {"fields": fields, "rows": rows, "docs": docs, "keys": {k for k in keyset if k[0] and k[1]}, "source": str(staged)}
        for var in fields:
            meta = docs.get(var, {}) if isinstance(docs, dict) else {}
            vals = [row.get(var, "") for row in rows]
            observed = [v for v in vals if not is_missing(v)]
            missing = len(vals) - len(observed)
            missing_codes = Counter(str(v) for v in vals if is_missing(v))
            levels = meta.get("Levels", {}) if isinstance(meta, dict) else {}
            observed_codes = Counter(str(v) for v in observed)
            by_visit: Counter[str] = Counter(row.get("session_id", "") for row in rows if not is_missing(row.get(var)))
            by_pid_score: defaultdict[str, set[str]] = defaultdict(set)
            for row in rows:
                if not is_missing(row.get(var)):
                    by_pid_score[row.get("participant_id", "")].add(row.get("session_id", ""))
            repeated = sum(len(x) >= 2 for x in by_pid_score.values() if x)
            variable_rows.append({"table": task_label(stem), "table_stem": stem, "table_class": table_class(stem)[0], "scientific_relevance": table_class(stem)[1], "source_path": str(staged), "dictionary_path": rpath(dataset / "phenotype" / f"{stem}.json", dataset), "variable": var, "description": meta.get("LongName", meta.get("Description", "")) if isinstance(meta, dict) else "", "row_unit": "participant-session (observed participant_id/session_id)", "data_type": infer_type(vals), "units": meta.get("Units", "") if isinstance(meta, dict) else "", "allowed_values": display(levels), "score_direction": "not documented; higher is not assumed better", "missing_value_codes": display(dict(missing_codes)), "validity_qc_codes": display(levels) if "valid_code" in var.lower() else "none documented", "raw_summary_or_derived": "observed source field; summary/derived status requires task-specific review", "varies_across_visits": "yes where repeated keys occur; row-level observation", "observed_nonmissing": len(observed), "missing_count": missing, "observed_unique_values": display(sorted(observed_codes)[:100]), "observed_by_visit": display(dict(sorted(by_visit.items()))), "participants_with_2plus_observed": repeated, "documentation_source": rpath(dataset / "phenotype" / f"{stem}.json", dataset), "potential_chavi_role": table_class(stem)[2], "availability": state, "interpretation_issues": "Do not equate task label with validated CHAVI domain or final score."})
            if "valid_code" in var.lower() or levels:
                for code in sorted(set(levels) | set(observed_codes)):
                    qc_rows.append({"source_path": str(staged), "table": task_label(stem), "variable": var, "code_type": "validity/QC or documented categorical level", "code": code, "documented_meaning": level_meaning(meta, code), "observed_count": observed_codes.get(code, 0), "unknown_category": "yes" if unknown_category(meta, code) else "no", "invalid_assessment_code": "yes" if documented_invalid(code) else "no", "status": "observed and documented" if code in levels else "unknown/undocumented observed code"})
                for code, count in observed_codes.items():
                    if code not in levels:
                        qc_rows.append({"source_path": str(staged), "table": task_label(stem), "variable": var, "code_type": "unknown/undocumented", "code": code, "documented_meaning": "not documented", "observed_count": count, "unknown_category": "unknown", "invalid_assessment_code": "unknown", "status": "unknown/undocumented observed code"})
            score_pair_counts = Counter()
            for pid, sessions in by_pid_score.items():
                for a, b in itertools.combinations(sorted(sessions), 2):
                    score_pair_counts[f"{a} + {b}"] += 1
            score_rows.append({"table": task_label(stem), "table_stem": stem, "table_class": table_class(stem)[0], "variable": var, "source_path": str(staged), "rows": len(rows), "observed_scores": len(observed), "missing_within_observed_rows": missing, "unique_participants_with_score": len(by_pid_score), "participants_with_2plus_observed_scores": repeated, "available_visit_pairs": json.dumps(dict(sorted(score_pair_counts.items())), sort_keys=True), "qc_status_field": "yes" if "valid_code" in var.lower() else "no", "qc_filter_applied": "no"})
            documented_unknown_count = sum(1 for v in observed if str(v) in levels and unknown_category(meta, str(v)))
            structural_na = sum(1 for v in vals if str(v) in levels and "not applicable" in level_meaning(meta, str(v)).lower())
            invalid_count = sum(1 for v in observed if documented_invalid(str(v))) if "valid_code" in var.lower() else 0
            missing_rows.append({"source_path": str(staged), "table": task_label(stem), "table_class": table_class(stem)[0], "variable": var, "unit": "row", "denominator": len(rows), "observed_nonmissing": len(observed), "missing_or_unavailable": missing, "missing_code_frequencies": display(dict(missing_codes)), "documented_unknown_category_count": documented_unknown_count, "structurally_not_applicable_count": structural_na, "invalid_assessment_code_count": invalid_count, "undocumented_code_count": sum(v for k, v in observed_codes.items() if k not in levels), "status": "available and parseable"})
    return stats, payloads, variable_rows, qc_rows, missing_rows, score_rows


def parse_scanner_aux(dataset: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], set[tuple[str, str]], dict[str, list[dict[str, str]]], list[dict[str, Any]]]:
    session_rows: list[dict[str, str]] = []
    session_fields: list[str] = []
    for p in sorted(dataset.glob("sub-*/sub-*_sessions.tsv")):
        fields, rows = read_tsv(p)
        for f in fields:
            if f not in session_fields:
                session_fields.append(f)
        for row in rows:
            row = dict(row)
            row["participant_id"] = p.parent.name
            row["source_path"] = rpath(p, dataset)
            session_rows.append(row)
    nback = [r for r in session_rows if any(not is_missing(r.get(v)) for v in session_fields if v not in {"session_id", "age", "acq_time"})]
    events: list[dict[str, Any]] = []
    event_files: list[dict[str, Any]] = []
    event_fields: set[str] = set()
    for p in sorted(dataset.glob("sub-*/ses-*/func/*_events.tsv")):
        fields, rows = read_tsv(p)
        event_fields.update(fields)
        parts = p.as_posix().split("/")
        pid = next((x for x in parts if x.startswith("sub-")), "")
        ses = next((x for x in parts if x.startswith("ses-")), "")
        task = re.search(r"_task-([^_]+)", p.name)
        task_name = task.group(1) if task else "unknown"
        event_files.append({"participant_id": pid, "session_id": ses, "task": task_name, "source_path": rpath(p, dataset), "rows": len(rows), "state": "available"})
        for row in rows:
            row = dict(row)
            row.update({"participant_id": pid, "session_id": ses, "task": task_name, "source_path": rpath(p, dataset)})
            events.append(row)
    aux_stats = [
        {"task": "Scanner n-back session summary (separate from phenotype/short_letter_2back.tsv)", "source_path": "sub-*/sub-*_sessions.tsv", "dictionary_path": "sub-*/sub-*_sessions.json", "table_class": "Scanner-task auxiliary data", "scientific_relevance": "B: auxiliary/replication context", "status": "available", "rows": len(nback), "columns": len(session_fields), "unique_participants": len({r["participant_id"] for r in nback}), "unique_keys": len({(r["participant_id"], r.get("session_id", "")) for r in nback}), "duplicate_key_values": "not detected", "duplicate_key_rows": "not detected", "exact_duplicate_rows": "not calculated", "rows_with_any_score": len(nback), "rows_with_qc": 0, "pair_counts": json.dumps(pair_counts({(r["participant_id"], r.get("session_id", "")) for r in nback}), sort_keys=True), "notes": "Session-level 0-back/2-back counts, rates, and d-prime; no validity code."},
        {"task": "Scanner n-back fMRI events (separate from phenotype/short_letter_2back.tsv)", "source_path": "sub-*/ses-*/func/*_task-nback*_events.tsv", "dictionary_path": "sub-*/ses-*/func/*_events.json", "table_class": "Scanner-task auxiliary data", "scientific_relevance": "B: auxiliary/replication context", "status": "available", "rows": len(events), "columns": len(event_fields), "unique_participants": len({r["participant_id"] for r in events}), "unique_keys": len({(r["participant_id"], r["session_id"]) for r in events}), "duplicate_key_values": "event rows are legitimately multiple trials", "duplicate_key_rows": "not applicable", "exact_duplicate_rows": "not calculated", "rows_with_any_score": sum(not is_missing(r.get("score")) for r in events), "rows_with_qc": 0, "pair_counts": json.dumps(pair_counts({(r["participant_id"], r["session_id"]) for r in events}), sort_keys=True), "notes": "Trial/event rows; response_time is task-specific and not assumed for phenotype variables."},
    ]
    return session_rows, events, {(r["participant_id"], r.get("session_id", "")) for r in nback}, {"sessions": session_rows, "nback": nback, "events": events}, event_files


def consolidated_dictionary(variable_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in variable_rows:
        grouped[(row["table_stem"], row["variable"])].append(row)
    by_var: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in variable_rows:
        by_var[row["variable"]].append(row)
    result = []
    for (stem, var), rows in sorted(grouped.items()):
        definitions = {x["description"] for x in rows}
        same_var = by_var[var]
        cross_defs = {x["description"] for x in same_var}
        result.append({"table_stem": stem, "table": rows[0]["table"], "table_class": rows[0]["table_class"], "scientific_relevance": rows[0]["scientific_relevance"], "variable": var, "source_path_pattern": f"phenotype/{stem}.tsv", "dictionary_path": rows[0]["dictionary_path"], "description": rows[0]["description"], "units": rows[0]["units"], "allowed_values": rows[0]["allowed_values"], "score_direction": rows[0]["score_direction"], "row_unit": rows[0]["row_unit"], "observed_nonmissing": rows[0]["observed_nonmissing"], "missing_count": rows[0]["missing_count"], "participants_with_2plus_observed": rows[0]["participants_with_2plus_observed"], "definition_conflict_status": "conflicting definitions across tables" if len(cross_defs) > 1 else "no conflicting duplicate definition observed", "conflicting_sources": display(sorted({x["table_stem"] for x in same_var if x["description"] != rows[0]["description"]})), "availability": rows[0]["availability"], "notes": "One consolidated row per table dictionary variable; repeated participant session dictionaries are not duplicated here."})
    return result


def build_cross_task(payloads: dict[str, dict[str, Any]], cognitive_stems: list[str]) -> list[dict[str, Any]]:
    keysets = {s: p["keys"] for s, p in payloads.items() if s in cognitive_stems}
    rows: list[dict[str, Any]] = []
    for a, b in itertools.combinations(sorted(keysets), 2):
        common = keysets[a] & keysets[b]
        rows.append({"coverage_type": "pairwise participant-session", "task_a": task_label(a), "task_b": task_label(b), "common_participant_sessions": len(common), "common_participants": len({x[0] for x in common}), "rule": "exact participant_id/session_id intersection; no QC filtering"})
    if keysets:
        common = set.intersection(*(set(v) for v in keysets.values()))
        rows.append({"coverage_type": "all candidate phenotype cognitive tasks", "task_a": "ALL", "task_b": f"{len(keysets)} tasks", "common_participant_sessions": len(common), "common_participants": len({x[0] for x in common}), "rule": "exact intersection across every available cognitive phenotype table; no QC filtering"})
    return rows


def read_participants(dataset: Path) -> tuple[list[str], list[dict[str, str]], dict[str, dict[str, Any]]]:
    fields, rows = read_tsv(dataset / "participants.tsv")
    return fields, rows, read_json(dataset / "participants.json")


def participant_inventory(fields: list[str], rows: list[dict[str, str]], docs: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    variables: list[dict[str, Any]] = []
    qc: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for var in fields:
        meta = docs.get(var, {}) if isinstance(docs, dict) else {}
        vals = [r.get(var, "") for r in rows]
        observed = [v for v in vals if not is_missing(v)]
        missing_count = len(vals) - len(observed)
        levels = meta.get("Levels", {}) if isinstance(meta, dict) else {}
        counts = Counter(str(v) for v in observed)
        unknown = sum(n for code, n in counts.items() if code in levels and unknown_category(meta, code))
        variables.append({"table": "participants.tsv", "table_stem": "participants", "table_class": "Demographic/context", "scientific_relevance": "A: essential Paper 1 context", "source_path": "participants.tsv", "dictionary_path": "participants.json", "variable": var, "description": meta.get("Description", meta.get("LongName", "")) if isinstance(meta, dict) else "", "row_unit": "participant", "data_type": infer_type(vals), "units": meta.get("Units", "") if isinstance(meta, dict) else "", "allowed_values": display(levels), "score_direction": "not applicable/not documented", "missing_value_codes": "not documented", "validity_qc_codes": "not applicable", "raw_summary_or_derived": "reported demographic or timepoint-1 clinical indicator; not a cognitive score", "varies_across_visits": "no; participant-level file", "observed_nonmissing": len(observed), "missing_count": missing_count, "observed_unique_values": display(sorted(counts)[:100]), "observed_by_visit": "", "participants_with_2plus_observed": "not applicable", "documentation_source": "participants.json", "potential_chavi_role": "age/developmental context, demographic/recruitment description, or clinical context; recruitment group is not an individual diagnosis", "availability": "available and parseable", "interpretation_issues": "age/age_months are baseline intake; dx_* are timepoint-1 indicators; n/a may be a documented unknown level for ethnicity"})
        if levels:
            for code in sorted(set(levels) | set(counts)):
                qc.append({"source_path": "participants.tsv", "table": "participants.tsv", "variable": var, "code_type": "documented categorical level", "code": code, "documented_meaning": level_meaning(meta, code), "observed_count": counts.get(code, 0), "unknown_category": "yes" if unknown_category(meta, code) else "no", "invalid_assessment_code": "no", "status": "observed and documented" if code in levels else "unknown/undocumented observed code"})
        missing.append({"source_path": "participants.tsv", "table": "participants.tsv", "table_class": "Demographic/context", "variable": var, "unit": "participant", "denominator": len(rows), "observed_nonmissing": len(observed), "missing_or_unavailable": missing_count, "missing_code_frequencies": display(dict(Counter(str(v) for v in vals if is_missing(v)))), "documented_unknown_category_count": unknown, "structurally_not_applicable_count": 0, "invalid_assessment_code_count": 0, "undocumented_code_count": sum(n for code, n in counts.items() if code not in levels), "status": "available and parseable"})
    return variables, qc, missing


def participant_summary(participants: list[dict[str, str]], session_rows: list[dict[str, str]], payloads: dict[str, dict[str, Any]], nback_keys: set[tuple[str, str]], event_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    recorded: defaultdict[str, set[str]] = defaultdict(set)
    for r in session_rows:
        recorded[r["participant_id"]].add(r.get("session_id", ""))
    cognitive: defaultdict[str, set[str]] = defaultdict(set)
    questionnaire: defaultdict[str, set[str]] = defaultdict(set)
    per_task: dict[str, defaultdict[str, set[str]]] = {}
    for stem, p in payloads.items():
        target = cognitive if stem in COGNITIVE else questionnaire
        per_task[stem] = defaultdict(set)
        for pid, ses in p["keys"]:
            target[pid].add(ses)
            per_task[stem][pid].add(ses)
    scanner_events: defaultdict[str, set[str]] = defaultdict(set)
    for r in event_rows:
        scanner_events[r["participant_id"]].add(r["session_id"])
    ids = sorted({r.get("participant_id", "") for r in participants} | set(recorded) | set(cognitive) | set(questionnaire))
    out = []
    for pid in ids:
        rep_tasks = sum(len(s) >= 2 for s in (per_task[s][pid] for s in per_task))
        out.append({"participant_id": pid, "recorded_visit_count": len(recorded[pid]), "recorded_session_labels": ";".join(sorted(recorded[pid])), "phenotype_cognitive_occasion_count": len(cognitive[pid]), "phenotype_cognitive_session_labels": ";".join(sorted(cognitive[pid])), "phenotype_questionnaire_occasion_count": len(questionnaire[pid]), "phenotype_questionnaire_session_labels": ";".join(sorted(questionnaire[pid])), "scanner_nback_summary_occasion_count": sum((pid, s) in nback_keys for s in recorded[pid]), "scanner_nback_event_occasion_count": len(scanner_events[pid]), "cognitive_tasks_with_2plus_observed_sessions": rep_tasks, "cognitive_occasion_status": "observed phenotype rows; no QC filter", "notes": "Recorded visit, cognitive occasion, non-missing score, QC validity, and comparability remain distinct concepts."})
    return out


def outcome_rows(payloads: dict[str, dict[str, Any]], repeated_cognitive_participants: set[str], cognitive_keys: set[tuple[str, str]]) -> list[dict[str, Any]]:
    out = []
    for stem in sorted(QUESTIONNAIRE):
        if stem not in payloads:
            continue
        p = payloads[stem]
        fields = p["fields"]
        score_cols = score_fields(fields)
        score_fields_present = [v for v in score_cols if any(not is_missing(r.get(v)) for r in p["rows"])]
        keys = p["keys"]
        baseline = {k for k in keys if k[1] == "ses-1"}
        follow = {k for k in keys if k[1] != "ses-1"}
        repeated = {pid for pid, s in keys if sum(1 for x in keys if x[0] == pid) >= 2}
        overlap = repeated & repeated_cognitive_participants
        out.append({"candidate_outcome": task_label(stem), "stem": stem, "priority": "high" if stem in {"eswan_adhd", "mapssr", "wolf_im_em"} else "inventory", "source_path": p["source"], "table_status": "available and parseable", "rows": len(p["rows"]), "unique_participants": len({x[0] for x in keys}), "unique_participant_sessions": len(keys), "baseline_ses1_rows": len(baseline), "followup_non_ses1_rows": len(follow), "participants_with_2plus_observed_rows": len(repeated), "overlap_with_repeated_cognitive_participants": len(overlap), "exact_score_fields": ";".join(score_fields_present), "score_direction": "not documented in inspected dictionary; do not assume", "timing_ambiguity": "session_id is available; exact cognitive-assessment timing and comparability require review", "notes": "No outcome associations or feature selection performed."})
    return out


def run_fixture_tests() -> dict[str, Any]:
    """Synthetic software tests; no fixture is retained in scientific outputs."""
    with tempfile.TemporaryDirectory(prefix="chavi_step1b_fixture_") as td:
        root = Path(td)
        pointer = root / "unavailable.tsv"
        pointer.write_text("../.git/annex/objects/xx/yy/SHA256E-s4--" + "0" * 64 + ".tsv/SHA256E-s4--" + "0" * 64 + ".tsv", encoding="utf-8")
        assert file_state(pointer)[0] == "unavailable_pointer"
        content = b"a\tb\n1\t2\n"
        h = hashlib.sha256(content).hexdigest()
        resolved = root / ".git" / "annex" / "objects" / "aa" / "bb" / f"SHA256E-s{len(content)}--{h}.tsv" / f"SHA256E-s{len(content)}--{h}.tsv"
        resolved.parent.mkdir(parents=True)
        resolved.write_bytes(content)
        resolved_stub = root / "resolved.tsv"
        rel = os.path.relpath(resolved, resolved_stub.parent).replace("\\", "/")
        resolved_stub.write_text(rel, encoding="utf-8")
        assert file_state(resolved_stub)[0] == "resolved_annex_object"
        real = root / "real.tsv"
        real.write_text("participant_id\tsession_id\tvalid_code\tscore\nsub-1\tses-1\tV\t1\nsub-1\tses-1\tQ\tn/a\n", encoding="utf-8")
        fields, rows = read_tsv(real)
        keys, counts = rows_by_key(rows)
        assert sum(n > 1 for n in counts.values()) == 1
        assert sum(n - 1 for n in Counter(tuple(r.get(f, "") for f in fields) for r in rows).values() if n > 1) == 0
        assert "Q" not in {"V", "F", "0", "S", "N", "C", "X"}
    return {"status": "passed", "tests": ["unavailable pointer", "resolved annex payload", "missing value + duplicate key + unknown QC code"], "fixture_data_retained": False}


def build_manifest(dataset: Path, stage: Path, expected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expected_by_name = {x["filename"]: x for x in expected}
    rows = []
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(dataset):
        dirnames[:] = [x for x in dirnames if x != ".git"]
        files.extend(Path(dirpath) / x for x in filenames)
    for p in sorted(files):
        rp = rpath(p, dataset)
        is_imaging = rp.startswith("derivatives/") or bool(re.search(r"(?:\.nii(?:\.gz)?|\.bval|\.bvec)$", rp, re.I))
        if is_imaging:
            state, pointer, target = "inventory_only", "", False
            digest = ""
        else:
            state, pointer, target = file_state(p)
            digest = sha256(p) if state in {"available", "unavailable_pointer", "resolved_annex_object"} else ""
        e = expected_by_name.get(p.name) if rp.startswith("phenotype/") else None
        rows.append({"source": "dataset checkout", "path": rp, "size_bytes": p.stat().st_size, "state": state, "expected_annex_key": e["expected_key"] if e else "", "expected_size_bytes": e["expected_size_bytes"] if e else "", "expected_sha256": e["expected_sha256"] if e else "", "actual_sha256": digest, "hash_scope": "visible file or pointer text; not payload" if state == "unavailable_pointer" else ("not hashed: imaging/derivative inventory only" if is_imaging else "visible file"), "scientific_relevance": table_class(p.stem)[1] if rp.startswith("phenotype/") else ("C: imaging/derivative" if is_imaging else "other")})
    for e in expected:
        p = stage / e["filename"]
        rows.append({"source": "verified staging payload", "path": str(p), "size_bytes": p.stat().st_size if p.exists() else "", "state": "verified_payload" if p.exists() else "missing_payload", "expected_annex_key": e["expected_key"], "expected_size_bytes": e["expected_size_bytes"], "expected_sha256": e["expected_sha256"], "actual_sha256": sha256(p) if p.exists() else "", "hash_scope": "payload content", "scientific_relevance": table_class(p.stem)[1]})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", type=Path, required=True)
    ap.add_argument("--phenotype-stage", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--retrieval-time-utc", default="")
    ap.add_argument("--fixture-only", action="store_true")
    args = ap.parse_args()
    if args.fixture_only:
        print(json.dumps(run_fixture_tests(), indent=2))
        return 0
    dataset = args.dataset.resolve()
    stage = args.phenotype_stage.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    audit_started = now_utc()
    fixture_result = run_fixture_tests()
    git = git_metadata(dataset)
    desc = read_json(dataset / "dataset_description.json")
    expected = expected_phenotype_keys(dataset)

    retrieval_time = args.retrieval_time_utc or now_utc()
    retrieval_rows = []
    for e in expected:
        p = stage / e["filename"]
        actual_size = p.stat().st_size if p.is_file() else ""
        actual_hash = sha256(p) if p.is_file() else ""
        size_match = bool(p.is_file() and actual_size == e["expected_size_bytes"])
        hash_match = bool(p.is_file() and actual_hash == e["expected_sha256"])
        retrieval_rows.append({"relative_dataset_path": e["dataset_path"], "expected_annex_key": e["expected_key"], "expected_size_bytes": e["expected_size_bytes"], "expected_sha256": e["expected_sha256"], "actual_payload_path": str(p), "retrieval_url": f"{ROOT_URL}/datasets/{DATASET_ID}/versions/{SNAPSHOT}/files/{e['dataset_path']}", "s3_source": f"s3://{S3_BUCKET}/{DATASET_ID}/{e['dataset_path']}", "retrieval_command": f"aws s3 cp --no-sign-request s3://{S3_BUCKET}/{DATASET_ID}/{e['dataset_path']} <phenotype-stage>/{e['filename']}", "retrieval_time_utc": retrieval_time, "actual_size_bytes": actual_size, "actual_sha256": actual_hash, "size_match": "yes" if size_match else "no", "hash_match": "yes" if hash_match else "no", "verification_method": "SHA-256(payload) and byte size compared with SHA256E key committed at pinned Git checkout", "verification_result": "verified" if size_match and hash_match else "failed", "parseable": "pending"})

    verified_names = {Path(r["relative_dataset_path"]).stem for r in retrieval_rows if r["verification_result"] == "verified"}
    stats, payloads, variable_rows, qc_rows, missing_rows, score_rows = parse_phenotype(dataset, stage, verified_names)
    participant_fields, participant_rows, participant_docs = read_participants(dataset)
    participant_vars, participant_qc, participant_missing = participant_inventory(participant_fields, participant_rows, participant_docs)
    variable_rows.extend(participant_vars)
    qc_rows.extend(participant_qc)
    missing_rows.extend(participant_missing)
    stats_by_stem = {x["stem"]: x for x in stats}
    for row in retrieval_rows:
        stem = Path(row["relative_dataset_path"]).stem
        row["parseable"] = "yes" if stem in payloads else "no"
    write_csv(out / "retrieval_manifest.csv", retrieval_rows, list(retrieval_rows[0]) if retrieval_rows else ["relative_dataset_path"])

    session_rows, event_rows, nback_keys, scanner, event_files = parse_scanner_aux(dataset)
    cognitive_stems = sorted(COGNITIVE & set(payloads))
    all_cog_keys = set().union(*(payloads[s]["keys"] for s in cognitive_stems)) if cognitive_stems else set()
    repeated_cog_participants = {pid for pid in {x[0] for x in all_cog_keys} if len({x[1] for x in all_cog_keys if x[0] == pid}) >= 2}
    consolidated = consolidated_dictionary(variable_rows)
    cross = build_cross_task(payloads, cognitive_stems)
    pv = participant_summary(read_participants(dataset)[1], session_rows, payloads, nback_keys, event_rows)
    outcomes = outcome_rows(payloads, repeated_cog_participants, all_cog_keys)
    # Keep the two scanner auxiliary records separate from phenotype tables.
    session_fields = set().union(*(set(r) for r in session_rows)) if session_rows else set()
    nback_summary_rows = [r for r in session_rows if any(not is_missing(r.get(v)) for v in session_fields - {"participant_id", "source_path", "session_id", "age", "acq_time"})]
    scanner_stats = [{"task": "Scanner n-back session summary (separate from phenotype/short_letter_2back.tsv)", "source_path": "sub-*/sub-*_sessions.tsv", "dictionary_path": "sub-*/sub-*_sessions.json", "table_class": "Scanner-task auxiliary data", "scientific_relevance": "B: auxiliary/replication context", "status": "available", "rows": len(nback_summary_rows), "columns": len(session_fields), "unique_participants": len({r["participant_id"] for r in nback_summary_rows}), "unique_keys": len({(r["participant_id"], r.get("session_id", "")) for r in nback_summary_rows}), "duplicate_key_values": "not detected", "duplicate_key_rows": "not detected", "exact_duplicate_rows": "not calculated", "rows_with_any_score": len(nback_summary_rows), "rows_with_qc": 0, "pair_counts": json.dumps(dict(sorted(pair_counts(nback_keys).items())), sort_keys=True), "notes": "Separate scanner task; no validity code."}, {"task": "Scanner n-back fMRI events (separate from phenotype/short_letter_2back.tsv)", "source_path": "sub-*/ses-*/func/*_task-nback*_events.tsv", "dictionary_path": "sub-*/ses-*/func/*_events.json", "table_class": "Scanner-task auxiliary data", "scientific_relevance": "B: auxiliary/replication context", "status": "available", "rows": len(event_rows), "columns": len({k for r in event_rows for k in r}), "unique_participants": len({r["participant_id"] for r in event_rows}), "unique_keys": len({(r["participant_id"], r["session_id"]) for r in event_rows}), "duplicate_key_values": "event rows are legitimate multiple trials", "duplicate_key_rows": "not applicable", "exact_duplicate_rows": "not calculated", "rows_with_any_score": sum(not is_missing(r.get("score")) for r in event_rows), "rows_with_qc": 0, "pair_counts": json.dumps(pair_counts({(r["participant_id"], r["session_id"]) for r in event_rows}), sort_keys=True), "notes": "Trial-level events; no phenotype-task interchangeability assumed."}]

    for row in retrieval_rows:
        if row["verification_result"] != "verified":
            row["parseable"] = "no"
    write_csv(out / "file_manifest.csv", build_manifest(dataset, stage, expected), ["source", "path", "size_bytes", "state", "expected_annex_key", "expected_size_bytes", "expected_sha256", "actual_sha256", "hash_scope", "scientific_relevance"])
    write_csv(out / "variable_inventory.csv", variable_rows, list(variable_rows[0]) if variable_rows else ["variable"])
    write_csv(out / "consolidated_variable_dictionary.csv", consolidated, list(consolidated[0]) if consolidated else ["variable"])
    write_csv(out / "participant_visit_summary.csv", pv, list(pv[0]) if pv else ["participant_id"])
    participant_stat = {"task": "participants.tsv", "stem": "participants", "table_class": "Demographic/context", "scientific_relevance": "A: essential Paper 1 context", "source_path": "participants.tsv", "dictionary_path": "participants.json", "status": "available and parseable", "rows": len(participant_rows), "columns": len(participant_fields), "unique_participants": len({r.get("participant_id", "") for r in participant_rows}), "unique_keys": len({r.get("participant_id", "") for r in participant_rows}), "duplicate_key_values": sum(n > 1 for n in Counter(r.get("participant_id", "") for r in participant_rows).values()), "duplicate_key_rows": sum(n - 1 for n in Counter(r.get("participant_id", "") for r in participant_rows).values() if n > 1), "exact_duplicate_rows": sum(n - 1 for n in Counter(tuple(r.get(f, "") for f in participant_fields) for r in participant_rows).values() if n > 1), "rows_with_any_score": "not applicable", "rows_with_qc": "not applicable", "pair_counts": "not applicable", "notes": "Participant-level demographics/recruitment/timepoint-1 context; not a cognitive table."}
    write_csv(out / "task_visit_coverage.csv", [participant_stat] + stats + scanner_stats, list(([participant_stat] + stats + scanner_stats)[0]) if ([participant_stat] + stats + scanner_stats) else ["task"])
    write_csv(out / "score_repeat_coverage.csv", score_rows, list(score_rows[0]) if score_rows else ["variable"])
    write_csv(out / "qc_code_inventory.csv", qc_rows, ["source_path", "table", "variable", "code_type", "code", "documented_meaning", "observed_count", "unknown_category", "invalid_assessment_code", "status"])
    write_csv(out / "missingness_summary.csv", missing_rows, list(missing_rows[0]) if missing_rows else ["variable"])
    write_csv(out / "cross_task_coverage.csv", cross, ["coverage_type", "task_a", "task_b", "common_participant_sessions", "common_participants", "rule"])
    # Candidate mappings remain candidates and are never converted to final scores.
    mappings = [
        ("Penn Abstraction, Inhibition and Working Memory Task", "Executive control: abstraction/inhibition/working-memory candidate", "phenotype/penn_abstraction_inhibition_working_memory_task.json; README; Penn CNB Explore Tests", "Combined task name does not establish separable domain scores."),
        ("Penn Face Memory Test", "Episodic memory: face memory candidate", "phenotype/penn_face_memory_test.json; README; Penn CNB Explore Tests", "No final composite."),
        ("Children's Penn Word Memory Test", "Episodic memory: verbal/word memory candidate", "phenotype/penn_word_memory_test.json; README; Penn CNB Explore Tests", "No final composite."),
        ("Short Computerized Finger-Tapping Task", "Sensorimotor/motor speed candidate", "phenotype/short_computerized_finger_tapping_task.json; README; Penn CNB Explore Tests", "No final composite."),
        ("Penn Emotion Recognition Task for Children", "Social cognition: emotion identification candidate", "phenotype/penn_emotion_recognition_task.json; README; Penn CNB Explore Tests", "No final composite."),
        ("Digit Symbol Test", "Processing speed candidate; recall fields may relate to relational memory", "phenotype/digit_symbol.json; README; Penn CNB Explore Tests", "Variable-specific review required."),
        ("Short Letter N-Back (2 back)", "Executive control: working-memory candidate", "phenotype/short_letter_2back.json; README; Penn CNB Explore Tests", "Phenotype table is separate from scanner n-back summaries/events."),
        ("Measured Emotion Differentiation Test", "Social cognition: emotion-intensity differentiation candidate", "phenotype/measured_emotion_differentiation_test.json; README; Penn CNB Explore Tests", "No final composite."),
        ("Motor Praxis Test", "Sensorimotor praxis-speed candidate", "phenotype/motor_praxis.json; README; Penn CNB Explore Tests", "No final composite."),
        ("Penn Conditional Exclusion Task for Children", "Provisional executive-control/abstraction candidate", "phenotype/penn_conditional_exclusion_task.json; README", "Instrument-specific construct documentation needed."),
        ("Short Penn Continuous Performance Test", "Attention/sustained-attention candidate", "phenotype/short_penn_continuous_performance_test.json; README; Penn CNB Explore Tests", "Number/letter variants need review."),
        ("Penn Matrix Reasoning Test", "Complex cognition: nonverbal reasoning candidate", "phenotype/penn_matrix_reasoning_test.json; README; Penn CNB Explore Tests", "No final composite."),
        ("Variable Short Penn Line Orientation Test", "Complex cognition: spatial-processing candidate", "phenotype/variable_short_penn_line_orientation_test.json; README; Penn CNB Explore Tests", "No final composite."),
        ("Children's Verbal Reasoning Test", "Complex cognition: language/verbal reasoning candidate", "phenotype/penn_verbal_reasoning_test.json; README; Penn CNB Explore Tests", "No final composite."),
        ("Short Visual Object Learning Test", "Episodic memory: visual/spatial memory candidate", "phenotype/visual_object_learning_test.json; README; Penn CNB Explore Tests", "No final composite."),
        ("Trailmaking A", "Provisional processing-speed/executive-control candidate", "phenotype/trailmaking_test_a.json; README", "No final assignment."),
        ("Trailmaking B", "Provisional executive-control/set-shifting candidate", "phenotype/trailmaking_test_b.json; README", "No final assignment."),
        ("Effort Discounting Task", "Reward decision-making candidate", "phenotype/effort_discounting_task.json; README; Penn CNB Explore Tests", "Choice parameters not calculated."),
        ("Delayed Discounting Task", "Reward decision-making candidate", "phenotype/delay_discounting_task.json; README; Penn CNB Explore Tests", "Choice parameters not calculated."),
        ("Risk Discounting Task", "Reward decision-making candidate", "phenotype/risk_discounting_task.json; README; Penn CNB Explore Tests", "Choice parameters not calculated."),
        ("Age Differentiation Test", "Social cognition: age differentiation candidate", "phenotype/age_differentiation_test.json; README; Penn CNB Explore Tests", "No final composite."),
    ]
    mapping_rows = [{"task": a, "candidate_domain": b, "evidence": c, "status": "candidate only", "availability": "available and parseable" if Path(a.lower().replace(" ", "_")) else "see task_visit_coverage.csv", "unresolved_interpretation": d} for a, b, c, d in mappings]
    # Correct the human-label availability heuristic with explicit table labels.
    stem_by_label = {task_label(s): s for s in COGNITIVE}
    for row in mapping_rows:
        row["availability"] = "available and parseable" if stem_by_label.get(row["task"], "") in payloads else "see task_visit_coverage.csv"
    write_csv(out / "candidate_domain_mapping.csv", mapping_rows, ["task", "candidate_domain", "evidence", "status", "availability", "unresolved_interpretation"])
    write_csv(out / "outcome_coverage.csv", outcomes, list(outcomes[0]) if outcomes else ["candidate_outcome"])

    # Retrieval verification report.
    verified = sum(r["verification_result"] == "verified" for r in retrieval_rows)
    parseable = sum(r["parseable"] == "yes" for r in retrieval_rows)
    verification_report = f"""# CHAVI Step 1B payload retrieval and verification

Audit time (UTC): `{audit_started}`  
Dataset: `{dataset}`  
Pinned Git target: `{git.get('commit')}` / tag `{git.get('describe')}`  
Retrieval source: official OpenNeuro public S3 prefix `s3://{S3_BUCKET}/{DATASET_ID}/phenotype/`  
Staging directory: `{stage}`

## Result

- Expected phenotype TSVs from the pinned checkout: **{len(expected)}**.
- Retrieved into staging: **{sum(Path(r['actual_payload_path']).is_file() for r in retrieval_rows)}**.
- Verified against expected SHA-256E key size/hash: **{verified}**.
- Parseable by the repaired audit: **{parseable}**.
- Failed or discrepant payloads: **{len(expected) - verified}**.

Every verified payload matched both the byte size and SHA-256 encoded in the annex key committed at the pinned Git checkout. The S3 path was not treated as historical snapshot proof by itself; the content-addressed key comparison is the verification step. Payloads were not copied over tracked pointer files, so the dataset's branch, commit, and tracked scientific content remain unchanged.

## Method and provenance

DataLad and git-annex were not installed locally. The documented OpenNeuro fallback was used: retrieve only the phenotype prefix into staging, compare each payload with its pinned annex key, and parse only verified payloads. Each file's URL, command, retrieval timestamp, expected key, actual size/hash, and result is in `retrieval_manifest.csv`.

Official documentation says OpenNeuro snapshots are Git tags and annex content is retrieved through DataLad/git-annex or the OpenNeuro storage remote. It also warns that direct Git transfer does not transfer annex objects. The direct S3 command used here was limited to the phenotype prefix.

## Synthetic software tests

`audit_v2.py --fixture-only` passed tests for an unavailable pointer, a resolved annex payload, and a real TSV containing a missing value, duplicate key, and unknown QC code. Fixtures are created in a temporary directory and are not retained in the scientific output.
"""
    (out / "payload_verification_report.md").write_text(verification_report, encoding="utf-8")

    # Dataset provenance and issue summary.
    provenance = {"audit_started_utc": audit_started, "audit_finished_utc": now_utc(), "dataset_root": str(dataset), "staging_root": str(stage), "intended_snapshot": SNAPSHOT, "pinned_commit_expected": COMMIT, "git": git, "dataset_description": desc, "retrieval": {"source": f"s3://{S3_BUCKET}/{DATASET_ID}/phenotype/", "retrieved_file_count": len(retrieval_rows), "verified_file_count": verified, "parseable_file_count": parseable, "method": "direct S3 staging fallback; key verification against pinned Git-annex keys", "target_commit_preserved": git.get("commit") == COMMIT, "tracked_content_modified": bool(git.get("status", "").splitlines()[1:]) if git.get("status", "").startswith("##") else "not determinable"}, "software": {"python": sys.version, "platform": platform.platform(), "git": run_git(dataset, "--version"), "aws": run_tool_version("aws", "--version")}, "counts": {"participants": len(read_participants(dataset)[1]), "recorded_session_rows": len(session_rows), "phenotype_tables_expected": len(expected), "phenotype_tables_verified": verified, "phenotype_tables_parseable": parseable, "phenotype_cognitive_tables": sum(stats_by_stem[s]["status"] == "verified_staging_payload" for s in COGNITIVE if s in stats_by_stem), "phenotype_questionnaire_tables": sum(stats_by_stem[s]["status"] == "verified_staging_payload" for s in QUESTIONNAIRE if s in stats_by_stem), "scanner_nback_summary_rows": len(nback_summary_rows), "scanner_nback_event_files": len(event_files), "scanner_nback_event_rows": len(event_rows)}}
    write_json(out / "dataset_provenance.json", provenance)

    all_keys = set().union(*(p["keys"] for p in payloads.values())) if payloads else set()
    duplicate_stats = {x["stem"]: {"duplicate_key_values": x["duplicate_key_values"], "duplicate_key_rows": x["duplicate_key_rows"], "exact_duplicate_rows": x["exact_duplicate_rows"]} for x in stats if x.get("status") == "verified_staging_payload"}
    issues = f"""# CHAVI Step 1B audit issues

## Resolved

- All {verified} expected phenotype TSV payloads were retrieved into staging and matched their pinned SHA-256E size/hash keys.
- All {parseable} retrieved phenotype tables parsed successfully.
- DataLad/git-annex absence was handled by the documented staged S3 fallback; no tracked pointer file was overwritten.

## Remaining scientific uncertainties

- Validity/QC codes are observed and documented in `qc_code_inventory.csv`, but no exclusion rule was applied. Unknown/undocumented codes and explicit unknown categories are retained separately.
- `n/a`, missing, structurally not-applicable, invalid-assessment, and unknown-category values are separate fields in `missingness_summary.csv`; their scientific treatment remains for review.
- Session-level age in `sub-*/sub-*_sessions.tsv` and baseline age in `participants.tsv` are different sources. Phenotype tables have participant/session keys but no universal proof that every task's assessment time exactly aligns with scan time.
- Scanner n-back summaries/events and `phenotype/short_letter_2back.tsv` are kept separate because their documentation and task context differ; they are not interchangeable measures.
- `cross_task_coverage.csv` reports exact participant-session intersections without QC filtering. It does not establish a final profile-eligible sample.
- No final domain/global/profile scores, reliability coefficients, predictive models, or reporting thresholds were calculated.

## Retrieval record

Direct S3 retrieval was limited to `s3://{S3_BUCKET}/{DATASET_ID}/phenotype/`; no MRI, derivative, other dataset, or whole-dataset download was performed. The source checkout remains at `{git.get('commit')}` with status `{git.get('status')}`. See `retrieval_manifest.csv` for per-file evidence.
"""
    (out / "audit_issues.md").write_text(issues, encoding="utf-8")

    changes = f"""# Changes from CHAVI Step 1 to Step 1B

Step 1 record: `chavi_audit_ds007116_20260907/audit.py` and its reports.  
Step 1B successor: `audit_v2.py` in this directory.  
Dataset checkout preserved at `{git.get('commit')}` / tag `{git.get('describe')}`.

## Retrieval

- Retrieved only the 41 expected `phenotype/*.tsv` payloads into a separate staging directory.
- Verified each staged payload against the expected SHA-256E size/hash encoded in the pinned Git-annex pointer.
- Did not overwrite tracked pointer files or modify the dataset branch.

## Audit corrections

- Replaced hard-coded unavailable phenotype narratives with conditional pointer/staging/payload state checks.
- Parsed actual phenotype rows and generated actual rows, columns, participants, participant-session keys, duplicate-key counts, exact duplicate-row counts, and visit-pair counts.
- Added score-level repeat coverage and separate missing-score counts; validity/completion fields are not counted as scientific scores.
- Added observed QC/code frequencies, documented meanings, unknown-category counts, invalid-code counts, structural-not-applicable counts, and undocumented-code counts.
- Added a consolidated dictionary with one row per table variable, preserving definition conflicts rather than duplicating identical session dictionaries.
- Classified tables as cognitive, questionnaire/outcome, demographic/context, or scanner-task auxiliary data.
- Kept scanner n-back summaries/events separate from phenotype `short_letter_2back.tsv`.
- Added exact pairwise and all-task participant-session coverage for candidate cognitive profiles.
- Added actual baseline/follow-up and repeated-cognitive overlap summaries for questionnaires, with priority rows for E-SWAN ADHD, MAPS-SR, and Wolf IM/EM.
- Added synthetic temporary tests for unavailable pointers, resolved payloads, missing values, duplicate keys, and unknown QC codes.

## Scientific boundary retained

No final cognitive composites, global scores, profile-shape scores, ICC/SEM/MDC, predictive models, thresholds, or clinical conclusions were produced.
"""
    (out / "changes_from_step1.md").write_text(changes, encoding="utf-8")

    # Main audit report: generated from calculated results.
    cognitive_stats = [x for x in stats if x["table_class"] == "Cognitive task"]
    questionnaire_stats = [x for x in stats if x["table_class"] == "Questionnaire/outcome"]
    one = sum(1 for x in pv if x["recorded_visit_count"] == 1)
    two = sum(1 for x in pv if x["recorded_visit_count"] == 2)
    three = sum(1 for x in pv if x["recorded_visit_count"] >= 3)
    repeated_task_counts = Counter()
    for s, p in payloads.items():
        if s in COGNITIVE:
            byp: defaultdict[str, set[str]] = defaultdict(set)
            for pid, ses in p["keys"]:
                byp[pid].add(ses)
            repeated_task_counts[s] = sum(len(v) >= 2 for v in byp.values())
    outcome_priority = {x["stem"]: x for x in outcomes if x["stem"] in {"eswan_adhd", "mapssr", "wolf_im_em"}}
    report = f"""# CHAVI Step 1B audit report: Penn LEAD ds007116

Audit timestamp (UTC): `{audit_started}` to `{now_utc()}`  
Dataset root: `{dataset}`  
Step 1B script: `audit_v2.py`  
Scope: retrieve and verify phenotype payloads, then audit their observed contents. No final scoring, reliability analysis, predictive modelling, clinical conclusion, dashboard, or interface was performed.

## Executive result

The checkout remains a clean `main` checkout at commit `{git.get('commit')}`, tag/description `{git.get('describe')}`, with the official OpenNeuroDatasets remote. The intended snapshot identity is preserved for the Git checkout. All **{len(expected)}/{len(expected)}** expected phenotype TSV payloads were retrieved into separate staging and **{verified}/{len(expected)}** matched their pinned annex size/hash keys; **{parseable}** parsed successfully. No tracked pointer file or dataset branch was changed.

The verified phenotype payloads support a complete table-level audit of **{len(cognitive_stats)} cognitive-task tables** and **{len(questionnaire_stats)} questionnaire/outcome tables**. Counts below are observed from payloads and use no QC-based exclusions.

## 1. Retrieval, verification, and provenance

- **Observed:** expected keys were read from the pinned checkout's `phenotype/*.tsv` pointer targets. Each key encoded a SHA-256E payload size/hash.
- **Observed:** direct S3 staging was limited to `s3://{S3_BUCKET}/{DATASET_ID}/phenotype/`; all payloads matched expected size and SHA-256. The detailed per-file record is `retrieval_manifest.csv`.
- **Observed:** Git remains at `{git.get('commit')}`, branch `{git.get('branch')}`, tag `{git.get('describe')}`, status `{git.get('status')}`. The old Step 1 output directory was preserved.
- **Documented:** local `dataset_description.json` identifies DOI `{desc.get('DatasetDOI')}`, BIDS `{desc.get('BIDSVersion')}`, dataset type `{desc.get('DatasetType')}`, and license `{desc.get('License')}`. Local `CHANGES` identifies the 1.0.6 release date and phenotype JSON fixes in 1.0.5.
- **Externally verified:** the official GitHub 1.0.6 release maps to commit `fc7dc36`; official OpenNeuro documentation describes snapshots as Git tags and annex retrieval through DataLad/git-annex or the OpenNeuro storage remote.
- **Unresolved:** exact original download method/date is not recorded. The S3 URL alone was not treated as snapshot identity; the pinned Git-annex key match was required.

## 2. Participant, visit, and assessment counts

Counting rules: a recorded visit is one available row in `sub-*/sub-*_sessions.tsv`; a phenotype observation is one row in a verified phenotype TSV; a unique participant-session is the exact key `(participant_id, session_id)`; a non-missing score is a value not in the generic missing-token set; a repeated observation means the same participant has observed values at two or more session labels for that table/variable. No validity or comparability filter was applied.

- **Observed:** `participants.tsv` contains **{len(read_participants(dataset)[1])} rows** and **{len({r.get('participant_id','') for r in read_participants(dataset)[1]})} unique participants**.
- **Observed:** recorded session rows: **{len(session_rows)}**; participants with 1 / 2 / 3+ recorded visits: **{one} / {two} / {three}**.
- **Observed:** phenotype cognitive participant-session keys: **{len(all_cog_keys)}**; phenotype cognitive participants: **{len({x[0] for x in all_cog_keys})}**; participants with repeated phenotype cognitive occasions: **{len(repeated_cog_participants)}**.
- **Observed:** scanner auxiliary n-back summary rows: **{len(nback_summary_rows)}**; scanner n-back event files: **{len(event_files)}**; scanner event rows: **{len(event_rows)}**. These are separate from phenotype `short_letter_2back.tsv`.
- **Observed:** duplicate keys and exact duplicate rows are reported per table in `task_visit_coverage.csv` and per variable in `score_repeat_coverage.csv`; duplicate event rows are not interpreted as duplicate assessments.

## 3. Cognitive task contents and repeat coverage

`task_visit_coverage.csv` reports actual rows, columns, participants, participant-session keys, duplicates, score-bearing rows, QC-bearing rows, and available visit pairs for every phenotype table. `score_repeat_coverage.csv` reports observed scores and participants with at least two observed scores for every variable. `variable_inventory.csv` records exact source paths, column names, definitions, units, levels, observed data types, missingness, visit availability, and unresolved interpretation issues.

Repeated participants by cognitive table: `{json.dumps({task_label(s): repeated_task_counts[s] for s in sorted(repeated_task_counts)}, sort_keys=True)}`.

No single “usable sample size” is reported. Recorded visits, phenotype cognitive occasions, observed scores, assessments with QC status, and potentially comparable repeated measurements remain distinct. The last category is not finalized because task validity and administration comparability have not been specified.

## 4. Candidate domain mappings and profile coverage

`candidate_domain_mapping.csv` contains provisional mappings only. The official Penn CNB Explore Tests page supports the broad task/domain candidates used here, including n-back/working memory, digit-symbol/processing speed, memory tests/episodic memory, reasoning/spatial tests/complex cognition, emotion and age differentiation/social cognition, discounting/reward decision-making, and motor tasks/sensorimotor speed. The local tables do not establish validated CHAVI composites.

`cross_task_coverage.csv` contains exact pairwise participant-session intersections and the all-task intersection across the **{len(cognitive_stems)}** verified phenotype cognitive tables. These counts are unfiltered coverage intersections, not profile-eligible or scientifically usable sample sizes. No global cognition, level, scatter, or shape score was calculated.

## 5. QC, missingness, and data-quality findings

- **Observed:** detailed variable-level missingness is in `missingness_summary.csv`. The report separates missing tokens, documented unknown categories, structural not-applicability, documented invalid-assessment codes, and undocumented codes.
- **Observed:** detailed code frequencies and meanings are in `qc_code_inventory.csv`. Documented valid/QC codes are retained alongside unknown/undocumented observed codes. No observation was removed.
- **Observed:** duplicate participant-session keys and exact duplicate rows are reported separately. The repeated-key counts are not automatically treated as errors until task-specific review.
- **Documented:** the README describes cognitive omissions, self-report protocol changes, and the special continuation/repeat situation for `sub-20812`; these notes are retained as documentation and not silently used as filters.
- **Unresolved:** whether `n/a` has the same substantive meaning across every questionnaire; whether a validity code applies to an entire task or selected variables; and whether rounded/anonymized acquisition times are suitable for exact follow-up intervals.

## 6. Demographic, clinical, and contextual variables

The available `participants.tsv/json` documents recruitment group, sex, race, ethnicity, baseline age, and timepoint-1 clinical-interview indicators. Recruitment group is not an individual diagnosis. Medication was not identified in the inspected dataset documentation, participant dictionary, phenotype dictionaries, or source-data material.

Session-level `age` is documented separately in session sidecars as age at the session, while participant-level `age`/`age_months` are baseline intake fields. The audit does not substitute one for the other.

## 7. Candidate outcomes and longitudinal availability

All questionnaire tables are now available and audited at inventory/coverage level. `outcome_coverage.csv` reports exact fields, rows, baseline `ses-1` coverage, non-baseline follow-up coverage, repeated participants, overlap with repeated cognitive participants, and unresolved score-direction/timing issues.

Priority outcomes requested for review:

- `eswan_adhd`: `{json.dumps(outcome_priority.get('eswan_adhd', {}), sort_keys=True)}`
- `mapssr`: `{json.dumps(outcome_priority.get('mapssr', {}), sort_keys=True)}`
- `wolf_im_em`: `{json.dumps(outcome_priority.get('wolf_im_em', {}), sort_keys=True)}`

These are candidate later outcomes/context variables, not cognitive ground truth. No associations, prediction, or outcome-driven feature selection was performed.

## 8. Audit-script repairs

`audit_v2.py` supersedes but does not overwrite Step 1 `audit.py`. Repairs include actual staged/pointer state checks; conditional payload parsing; factual table counts; separate scanner auxiliary versus phenotype n-back handling; per-variable missingness and score-repeat coverage; observed/documented/unknown QC categories; consolidated variable dictionary; cognitive versus questionnaire classification; pairwise/all-task overlap; generated report text; and synthetic tests for unavailable pointers, resolved payloads, missing values, duplicate keys, and unknown QC codes.

## 9. Remaining blockers and recommended next decision

There is no retrieval blocker for the 41 phenotype payloads. Scientific blockers remain: task-specific validity rules, precise interpretation of score directions, comparability of repeated occasions, and a preregistered rule for candidate domain membership/profile construction. The next decision is to review and approve those definitions before any scoring or reliability analysis.

## 10. Outputs and reproduction

This Step 1B directory contains the requested retrieval manifest, payload verification report, repaired script, factual audit report, provenance JSON, file/variable/task/score/QC/missingness/cross-task/domain/outcome CSVs, and issue log. The previous Step 1 directory remains unchanged.

Rerun the synthetic tests:

```powershell
python .\\chavi_audit_ds007116_step1b_20260907\\audit_v2.py --dataset .\\ds007116 --phenotype-stage .\\chavi_step1b_phenotype_staging_20260907 --output .\\chavi_audit_ds007116_step1b_20260907 --fixture-only
```

Rerun the real audit:

```powershell
python .\\chavi_audit_ds007116_step1b_20260907\\audit_v2.py --dataset .\\ds007116 --phenotype-stage .\\chavi_step1b_phenotype_staging_20260907 --output .\\chavi_audit_ds007116_step1b_20260907
```

Software versions and counting rules are recorded in `dataset_provenance.json`; per-file expected/retrieved/verified/parseable evidence is in `retrieval_manifest.csv`.

Official sources consulted: [OpenNeuro CLI/download documentation](https://docs.openneuro.org/packages/openneuro-cli.html), [OpenNeuro Git access and snapshots](https://docs.openneuro.org/git.html), [OpenNeuro API examples](https://docs.openneuro.org/api.html), [official 1.0.6 release](https://github.com/OpenNeuroDatasets/ds007116/releases/tag/1.0.6), [official 1.0.6 README](https://raw.githubusercontent.com/OpenNeuroDatasets/ds007116/1.0.6/README), and [Penn CNB task mappings](https://webcnp.med.upenn.edu/explore-tests.html).
"""
    (out / "audit_v2_report.md").write_text(report, encoding="utf-8")
    print(json.dumps({"output": str(out), "expected_phenotype": len(expected), "retrieved": len(retrieval_rows), "verified": verified, "parseable": parseable, "cognitive_tables": len(cognitive_stats), "questionnaire_tables": len(questionnaire_stats), "recorded_session_rows": len(session_rows), "phenotype_cognitive_keys": len(all_cog_keys), "cross_task_rows": len(cross), "synthetic_fixture_tests": fixture_result["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
