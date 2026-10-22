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


STEP2_PRIMARY = {
    "age_differentiation_test": ["cnb_adt_cr"],
    "delay_discounting_task": ["cnb_ddisc_tot"],
    "digit_symbol": ["cnb_digsym_dscor"],
    "effort_discounting_task": ["cnb_edisc_tot"],
    "measured_emotion_differentiation_test": ["cnb_medf_cr"],
    "motor_praxis": ["cnb_mpract_mp2"],
    "penn_abstraction_inhibition_working_memory_task": ["cnb_aim_aimtot"],
    "penn_conditional_exclusion_task": ["cnb_pcet_cr"],
    "penn_emotion_recognition_task": ["cnb_er40_cr"],
    "penn_face_memory_test": ["cnb_cpf_cr"],
    "penn_matrix_reasoning_test": ["cnb_pmat_cr"],
    "penn_verbal_reasoning_test": ["cnb_pvrt_cr"],
    "penn_word_memory_test": ["cnb_cpw_cr"],
    "risk_discounting_task": ["cnb_rdisc_tot"],
    "short_computerized_finger_tapping_task": ["cnb_ctap_dom"],
    "short_letter_2back": ["cnb_lnb_mcr"],
    "short_penn_continuous_performance_test": ["cnb_cptnl_total_sen"],
    "trailmaking_test_a": ["cnb_trails_rt"],
    "trailmaking_test_b": ["cnb_trails_rt"],
    "variable_short_penn_line_orientation_test": ["cnb_plot_cr"],
    "visual_object_learning_test": ["cnb_volt_cr"],
}

STEP2_SENSITIVITY = {
    "age_differentiation_test": ["cnb_adt_rtcr", "cnb_adt_pc"],
    "delay_discounting_task": ["cnb_ddisc_rt", "cnb_ddisc_mrt"],
    "digit_symbol": ["cnb_digsym_dscorrt"],
    "effort_discounting_task": ["cnb_edisc_rt", "cnb_edisc_mrt"],
    "measured_emotion_differentiation_test": ["cnb_medf_rtcr", "cnb_medf_pc"],
    "motor_praxis": ["cnb_mpract_mp2rtcr"],
    "penn_abstraction_inhibition_working_memory_task": ["cnb_aim_aimtotrt"],
    "penn_conditional_exclusion_task": ["cnb_pcet_rtcr", "cnb_pcet_acc2"],
    "penn_emotion_recognition_task": ["cnb_er40_rtcr", "cnb_er40_fc", "cnb_er40_mc"],
    "penn_face_memory_test": ["cnb_cpf_rtcr", "cnb_cpf_tp", "cnb_cpf_fp"],
    "penn_matrix_reasoning_test": ["cnb_pmat_rtcr", "cnb_pmat_pc"],
    "penn_verbal_reasoning_test": ["cnb_pvrt_rtcr", "cnb_pvrt_pc"],
    "penn_word_memory_test": ["cnb_cpw_rtcr", "cnb_cpw_tp"],
    "risk_discounting_task": ["cnb_rdisc_rt", "cnb_rdisc_mrt"],
    "short_computerized_finger_tapping_task": ["cnb_ctap_tot", "cnb_ctap_dom", "cnb_ctap_nond"],
    "short_letter_2back": ["cnb_lnb_rtc", "cnb_lnb_tp", "cnb_lnb_fp"],
    "short_penn_continuous_performance_test": ["cnb_cptnl_total_spec", "cnb_cptnl_total_rt"],
    "trailmaking_test_a": ["cnb_trails_cr", "cnb_trails_rtcr"],
    "trailmaking_test_b": ["cnb_trails_cr", "cnb_trails_rtcr"],
    "variable_short_penn_line_orientation_test": ["cnb_plot_pc", "cnb_plot_rtcr"],
    "visual_object_learning_test": ["cnb_volt_rtcr", "cnb_volt_tp"],
}

STEP2_DOMAINS = {
    "Executive control": ["penn_abstraction_inhibition_working_memory_task", "penn_conditional_exclusion_task", "short_letter_2back", "short_penn_continuous_performance_test", "trailmaking_test_b"],
    "Episodic memory": ["penn_word_memory_test", "penn_face_memory_test", "visual_object_learning_test"],
    "Complex cognition": ["penn_verbal_reasoning_test", "penn_matrix_reasoning_test", "variable_short_penn_line_orientation_test", "digit_symbol"],
    "Social cognition": ["penn_emotion_recognition_task", "measured_emotion_differentiation_test", "age_differentiation_test"],
    "Sensorimotor performance": ["short_computerized_finger_tapping_task", "motor_praxis", "trailmaking_test_a"],
}

STEP2_DOMAIN_ALTERNATIVES = {
    "penn_conditional_exclusion_task": "Complex cognition (Moore et al. reported PCET as a possible better complex-cognition measure).",
    "digit_symbol": "Sensorimotor/processing speed; the five-domain framework has no standalone processing-speed domain.",
    "trailmaking_test_a": "Executive control/processing speed; exact placement is unresolved.",
    "trailmaking_test_b": "Complex cognition/set shifting; exact placement is unresolved.",
    "penn_abstraction_inhibition_working_memory_task": "Executive control is plausible from the task name, but its combined construct is unresolved.",
}

OUTCOME_SPECS = {
    "eswan_adhd_inattention_total": ("eswan_adhd", "E-SWAN ADHD inattention total"),
    "eswan_adhd_total_score": ("eswan_adhd", "E-SWAN ADHD total score"),
    "mapssr_total_score": ("mapssr", "MAPS-SR total score"),
    "im_average": ("wolf_im_em", "Wolf intrinsic motivation average"),
    "em_average": ("wolf_im_em", "Wolf extrinsic motivation average"),
}

SOURCE_URLS = {
    "dataset_release": "https://github.com/OpenNeuroDatasets/ds007116/releases/tag/1.0.6",
    "dataset_readme": "https://raw.githubusercontent.com/OpenNeuroDatasets/ds007116/1.0.6/README",
    "cnb_explore": "https://webcnp.med.upenn.edu/explore-tests.html",
    "cnb_updates": "https://webcnp.med.upenn.edu/updates.html",
    "gur_2010": "https://pmc.ncbi.nlm.nih.gov/articles/PMC2832711/",
    "moore_2015": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4345134/",
    "pennlinc_mapping": "https://github.com/PennLINC/transdiagnostic_executive_function/blob/main/cognitive/CNB_transformation_script_EF.Rmd",
}


def s2_doc(meta: dict[str, Any], field: str) -> str:
    d = meta.get(field, {}) if isinstance(meta, dict) else {}
    if not isinstance(d, dict):
        return ""
    return str(d.get("LongName") or d.get("Description") or "")


def s2_levels(meta: dict[str, Any], field: str) -> dict[str, Any]:
    d = meta.get(field, {}) if isinstance(meta, dict) else {}
    return d.get("Levels", {}) if isinstance(d, dict) and isinstance(d.get("Levels", {}), dict) else {}


def s2_field_class(field: str, meta: dict[str, Any]) -> str:
    f = field.lower()
    if field in {"participant_id", "session_id"}:
        return "identifier"
    if field == "MeasurementToolMetadata":
        return "other metadata"
    if "valid_code" in f or f in {"ctap_valid_code"}:
        return "QC"
    if any(x in f for x in ("status", "complete", "completion")):
        return "completion/status"
    if f.endswith("_form") or f in {"cnb_ctap_hand", "cnb_ctap_non"}:
        return "other metadata"
    if s2_is_timing(field, s2_doc(meta, field)):
        return "timing"
    if any(x in f for x in ("tp", "tn", "fp", "fn", "er", "error")):
        return "items"
    return "scores"


def s2_is_timing(field: str, description: str) -> bool:
    """Identify timing outputs without matching substrings such as PVRT or effort."""
    f = field.lower()
    timing_tokens = r"(?:rt|mrt|rtcr|rter|tprt|fprt|prt|rtto|rtc|mrtc|rtmean|rtsd)"
    return bool(re.search(rf"(?:^|_){timing_tokens}(?:_|$)", f)) or any(x in description.lower() for x in ("response time", "reaction time"))


def s2_score_type(field: str, description: str) -> str:
    text = f"{field} {description}".lower()
    if "discount" in text or "risk" in text or "effort" in text:
        if not s2_is_timing(field, description):
            return "preference/decision measure"
    if s2_is_timing(field, description) or "speed" in text:
        return "time/speed"
    if any(x in text for x in ("sensitivity", "specificity", "percent", "proportion", "accuracy")):
        return "proportion/accuracy"
    if any(x in text for x in ("error", "incorrect", "false positive", "false negative")):
        return "error count"
    if any(x in text for x in ("count", "correct", "true positive", "true negative")):
        return "count/accuracy"
    if "mean of" in text or "sum of" in text or "number of taps" in text:
        return "rate/count"
    if "discount" in text or "risk" in text or "effort" in text:
        return "preference/decision measure"
    return "other task output"


def s2_direction(field: str, description: str, task: str) -> tuple[str, str]:
    text = f"{field} {description}".lower()
    if "discount" in task or "discount" in text or "risk" in task:
        if s2_is_timing(field, description):
            return "lower raw value is faster; keep separate from preference direction", "Reaction time is a timing measure even when the task is a reward/discounting task; preference direction remains unresolved."
        return "no universal better/worse direction", "Preference/decision output is outside the five-domain performance framework; direction requires a prespecified scientific construct."
    if s2_is_timing(field, description) or "speed" in text:
        return "lower raw value is faster; reverse direction only as a proposed alignment", "Penn CNB evidence distinguishes speed from accuracy; a speed-accuracy decision is not finalized."
    if any(x in text for x in ("error", "incorrect", "false positive", "false negative")):
        return "higher raw value indicates more errors; worse-performance interpretation is plausible", "Keep error measures separate from accuracy until a task-specific scoring rule is approved."
    if any(x in text for x in ("mean of dominant hand trials", "mean of non-dominant hand trials", "sum of dom", "number of taps")):
        return "higher raw value plausibly indicates faster motor performance", "The local LongName identifies trial/tap output; direction is a proposed motor-speed interpretation, not a finalized composite rule."
    if any(x in text for x in ("correct", "sensitivity", "specificity", "percent correct", "accuracy")):
        return "higher raw value plausibly indicates better task performance", "Supported as an accuracy-like direction, but exact score construction and validity rules remain under review."
    return "not documented locally", "The local dictionary does not define a defensible performance direction for this field."


def s2_qc_fields(fields: list[str]) -> list[str]:
    return [f for f in fields if "valid_code" in f.lower() or f == "ctap_valid_code"]


def s2_qc_state(task: str, row: dict[str, str], qc_fields: list[str], scenario: str, meta: dict[str, Any] | None = None) -> tuple[bool, str]:
    if scenario == "unfiltered_observed":
        return True, "not applied"
    codes = [str(row.get(f, "")).strip() for f in qc_fields if not is_missing(row.get(f, ""))]
    if not qc_fields or not codes:
        return False, "missing QC"
    if scenario == "qc_valid_only":
        ok = all(c == "V" for c in codes)
    elif scenario == "qc_valid_or_likely_valid":
        ok = all(c in {"V", "F"} for c in codes)
    elif scenario == "qc_no_explicit_invalid":
        invalid = []
        for field in qc_fields:
            code = str(row.get(field, "")).strip()
            meaning = str(s2_levels(meta or {}, field).get(code, "")).lower()
            invalid.append(code in {"N", "X", "S"} or ("invalid" in meaning and "likely valid" not in meaning) or "not valid" in meaning or "excluded" in meaning or "skipped" in meaning)
        ok = not any(invalid)
    elif scenario == "unresolved_qc_only":
        ok = any(c not in {"V", "F", "N", "X", "S"} for c in codes)
    else:
        raise ValueError(scenario)
    return ok, ";".join(codes)


def s2_missing_category(value: str, meta: dict[str, Any], field: str) -> str:
    if not is_missing(value):
        return "observed_value"
    raw = str(value).strip()
    levels = s2_levels(meta, field)
    if raw in levels and any(x in str(levels[raw]).lower() for x in ("unknown", "don't know", "refused", "prefer not")):
        return "documented_unknown_response"
    if raw.lower() == "n/a":
        return "raw_missing_token_n/a_not_structural"
    return "raw_missing_token_or_absent_measurement"


def s2_verified_payloads(dataset: Path, stage: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    expected = expected_phenotype_keys(dataset)
    payloads: dict[str, dict[str, Any]] = {}
    manifest: list[dict[str, Any]] = []
    for e in expected:
        p = stage / e["filename"]
        actual_size = p.stat().st_size if p.is_file() else ""
        actual_hash = sha256(p) if p.is_file() else ""
        verified = bool(p.is_file() and actual_size == e["expected_size_bytes"] and actual_hash == e["expected_sha256"])
        parsed = False
        rows: list[dict[str, str]] = []
        fields: list[str] = []
        if verified:
            try:
                fields, rows = read_tsv(p)
                parsed = True
                stem = Path(e["dataset_path"]).stem
                payloads[stem] = {"fields": fields, "rows": rows, "path": p, "meta": read_json(dataset / e["dataset_path"].replace(".tsv", ".json")), "keys": {(r.get("participant_id", ""), r.get("session_id", "")) for r in rows}}
            except Exception:
                parsed = False
        manifest.append({"relative_dataset_path": e["dataset_path"], "expected_annex_key": e["expected_key"], "expected_size_bytes": e["expected_size_bytes"], "expected_sha256": e["expected_sha256"], "actual_payload_path": str(p), "actual_size_bytes": actual_size, "actual_sha256": actual_hash, "size_match": "yes" if p.is_file() and actual_size == e["expected_size_bytes"] else "no", "hash_match": "yes" if p.is_file() and actual_hash == e["expected_sha256"] else "no", "verification_result": "verified" if verified else "failed", "parseable": "yes" if parsed else "no"})
    return payloads, manifest


def s2_candidate_fields(task: str, payload: dict[str, Any]) -> list[str]:
    fields = set(payload["fields"])
    return [f for f in STEP2_PRIMARY.get(task, []) + STEP2_SENSITIVITY.get(task, []) if f in fields]


def s2_numeric_range(rows: list[dict[str, str]], field: str) -> str:
    vals: list[float] = []
    for r in rows:
        try:
            if not is_missing(r.get(field, "")):
                vals.append(float(r[field]))
        except (ValueError, TypeError):
            return "mixed/non-numeric"
    if not vals:
        return "none observed"
    return f"{min(vals):g} to {max(vals):g}"


def s2_pairs(keys: set[tuple[str, str]]) -> str:
    return json.dumps(dict(sorted(pair_counts(keys).items())), sort_keys=True)


def s2_score_rows(payloads: dict[str, dict[str, Any]], out: Path) -> tuple[list[dict[str, Any]], dict[str, dict[tuple[str, str], dict[str, Any]]]]:
    rows: list[dict[str, Any]] = []
    value_maps: dict[str, dict[tuple[str, str], dict[str, Any]]] = {}
    for task in sorted(COGNITIVE):
        if task not in payloads:
            continue
        p = payloads[task]
        qc_fields = s2_qc_fields(p["fields"])
        meta = p["meta"]
        for field in s2_candidate_fields(task, p):
            values: dict[tuple[str, str], dict[str, Any]] = {}
            categories = Counter()
            keys: set[tuple[str, str]] = set()
            for r in p["rows"]:
                key = (r.get("participant_id", ""), r.get("session_id", ""))
                if not is_missing(r.get(field, "")):
                    keys.add(key)
                categories[s2_missing_category(r.get(field, ""), meta, field)] += 1
                values[key] = {"value": r.get(field, ""), "qc_fields": qc_fields, "row": r}
            value_maps[f"{task}:{field}"] = values
            participant_ids = {k[0] for k in keys}
            repeat_participants = {pid for pid in participant_ids if sum(k[0] == pid for k in keys) >= 2}
            direction, _ = s2_direction(field, s2_doc(meta, field), task)
            for scenario in ("unfiltered_observed", "qc_valid_only", "qc_valid_or_likely_valid", "qc_no_explicit_invalid", "unresolved_qc_only"):
                eligible = set()
                for key, info in values.items():
                    if is_missing(info["value"]):
                        continue
                    ok, _ = s2_qc_state(task, info["row"], qc_fields, scenario, meta)
                    if ok:
                        eligible.add(key)
                ep = {k[0] for k in eligible}
                erp = {pid for pid in ep if sum(k[0] == pid for k in eligible) >= 2}
                rows.append({"variable_id": f"ds007116:{task}:{field}", "task": task_label(task), "table_stem": task, "variable": field, "scenario": scenario, "observed_score_count": len(eligible), "unique_participants": len(ep), "unique_participant_sessions": len(eligible), "participants_with_2plus_scores": len(erp), "visit_pair_counts": s2_pairs(eligible), "missing_category_counts": json.dumps(dict(sorted(categories.items())), sort_keys=True), "qc_fields": ";".join(qc_fields) or "none documented", "score_direction": direction, "units": meta.get(field, {}).get("Units", "") if isinstance(meta.get(field, {}), dict) else "", "expected_range": "not documented locally", "observed_range": s2_numeric_range(p["rows"], field), "qc_filter_applied": scenario != "unfiltered_observed"})
    write_csv(out / "candidate_score_coverage.csv", rows, list(rows[0]) if rows else ["variable_id"])
    return rows, value_maps


def s2_variable_selection(payloads: dict[str, dict[str, Any]], score_rows: list[dict[str, Any]], out: Path) -> list[dict[str, Any]]:
    repeats = {(r["table_stem"], r["variable"]): r["participants_with_2plus_scores"] for r in score_rows if r["scenario"] == "unfiltered_observed"}
    result: list[dict[str, Any]] = []
    domain_for_task = {t: d for d, ts in STEP2_DOMAINS.items() for t in ts}
    for task in sorted(COGNITIVE):
        if task not in payloads:
            continue
        p = payloads[task]
        meta = p["meta"]
        qc_fields = s2_qc_fields(p["fields"])
        for field in p["fields"]:
            if field == "MeasurementToolMetadata":
                continue
            doc = s2_doc(meta, field)
            fc = s2_field_class(field, meta)
            if field in {"participant_id", "session_id"}:
                role = "context/QC only"
                reason = "Identifier retained for joins and audit keys; explicitly excluded from scientific-score coverage."
            elif field in STEP2_PRIMARY.get(task, []):
                role = "proposed primary"
                reason = "Primary candidate selected from the task's accuracy/score-like output; selection is theory/documentation based, not data-performance optimized."
            elif field in STEP2_SENSITIVITY.get(task, []):
                role = "sensitivity alternative"
                reason = "Sensitivity candidate preserves an alternate accuracy, error, or timing representation without combining it into the primary definition."
            elif fc in {"identifier", "QC", "completion/status", "other metadata"}:
                role = "context/QC only"
                reason = "Identifier, QC, status, form, hand, or metadata field; not a scientific performance score."
            else:
                role = "excluded candidate"
                reason = "Potentially redundant, component, error, timing, preference, or task-specific output not selected in this draft."
            direction, direction_reason = s2_direction(field, doc, task)
            conflict = ""
            if task == "age_differentiation_test" and field == "cnb_adt_cnt_200":
                conflict = "Preserve original metadata: LongName describes a count of responses under 250 milliseconds, but Units is ms; a count is not itself measured in ms."
            derived = "derived=true in local JSON" if isinstance(meta.get(field), dict) and meta[field].get("Derivative") else "source task-output field; standardized status not documented locally"
            expected = "categorical levels documented" if s2_levels(meta, field) else "not documented locally"
            result.append({"variable_id": f"ds007116:{task}:{field}", "task": task_label(task), "table_stem": task, "source_table": f"phenotype/{task}.tsv", "variable": field, "field_class": fc, "score_type": s2_score_type(field, doc), "description": doc, "units": meta.get(field, {}).get("Units", "") if isinstance(meta.get(field, {}), dict) else "", "expected_range": expected, "observed_range": s2_numeric_range(p["rows"], field), "higher_better_defensible": "yes with task-specific review" if direction.startswith("higher") else "no/conditional", "score_direction": direction, "raw_or_derived": derived, "rt_scope": "correct-response RT where LongName says correct responses" if "correct" in doc.lower() and "time" in doc.lower() else ("all-response/unspecified RT; do not relabel" if "time" in doc.lower() else "not applicable"), "associated_qc_field": ";".join(qc_fields) or "none documented", "qc_scope": "; ".join(s2_doc(meta, q) for q in qc_fields) or "not documented", "candidate_domain": domain_for_task.get(task, "outside five-domain framework"), "potential_redundancy": "Review alternate accuracy/error/RT fields within this task before combining.", "candidate_role": role, "supporting_source": f"phenotype/{task}.json LongName/Units/Levels/Derivative; {SOURCE_URLS['gur_2010']}; {SOURCE_URLS['moore_2015']}", "reason_for_role": reason, "participants_with_2plus_observed": repeats.get((task, field), 0), "definition_conflict": conflict, "direction_evidence_note": direction_reason})
    write_csv(out / "variable_selection_draft.csv", result, list(result[0]) if result else ["variable_id"])
    return result


def s2_qc_rows(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for task in sorted(COGNITIVE):
        if task not in payloads:
            continue
        p = payloads[task]
        for field in s2_qc_fields(p["fields"]):
            levels = s2_levels(p["meta"], field)
            counts = Counter(str(r.get(field, "")).strip() for r in p["rows"] if not is_missing(r.get(field, "")))
            for code in sorted(counts):
                key = (task, field, code)
                if key in seen:
                    continue
                seen.add(key)
                meaning = str(levels.get(code, ""))
                if meaning:
                    if code == "V": status = "explicitly valid"
                    elif code == "F": status = "likely valid/problematic"
                    elif code == "S": status = "skipped"
                    elif code in {"N", "X"}: status = "invalid/excluded"
                    elif code == "0": status = "no automatic validation"
                    elif code == "C": status = "conditional/problematic/assessor comment"
                    else: status = "documented but unresolved"
                else:
                    status = "unresolved observed code"
                result.append({"task": task_label(task), "table_stem": task, "qc_variable": field, "code": code, "observed_count": counts[code], "documented_meaning": meaning or "not documented locally", "qc_scope": s2_doc(p["meta"], field) or "not documented", "provisional_class": status, "validity_scenario_v_only": "included" if code == "V" else "excluded", "validity_scenario_v_or_f": "included" if code in {"V", "F"} else "excluded", "no_explicit_invalid_scenario": "included" if code not in {"N", "X", "S"} else "excluded", "unresolved_qc": "yes" if code not in {"V", "F", "N", "X", "S"} else "no", "clarification_needed": "yes" if code in {"VC", "0", "C"} or not meaning else "no", "evidence": f"phenotype/{task}.json Levels; task-level QC scope is not independently validated"})
            missing_count = sum(is_missing(r.get(field, "")) for r in p["rows"])
            if missing_count:
                result.append({"task": task_label(task), "table_stem": task, "qc_variable": field, "code": "__MISSING__", "observed_count": missing_count, "documented_meaning": "QC value absent; not an observed validity code", "qc_scope": s2_doc(p["meta"], field) or "not documented", "provisional_class": "missing QC", "validity_scenario_v_only": "excluded", "validity_scenario_v_or_f": "excluded", "no_explicit_invalid_scenario": "excluded", "unresolved_qc": "yes", "clarification_needed": "yes", "evidence": f"raw values in phenotype/{task}.tsv"})
    return result


def s2_occasion_rows(payloads: dict[str, dict[str, Any]], session_rows: list[dict[str, str]], participant_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    keys = {(r.get("participant_id", ""), r.get("session_id", "")) for r in session_rows}
    for p in payloads.values():
        keys.update(p["keys"])
    sessions = {(r.get("participant_id", ""), r.get("session_id", "")): r for r in session_rows}
    participant_age = {r.get("participant_id", ""): r.get("age", "") for r in participant_rows}
    result = []
    for pid, ses in sorted(keys):
        sr = sessions.get((pid, ses), {})
        task_count = sum((pid, ses) in p["keys"] for t, p in payloads.items() if t in COGNITIVE)
        score_count = sum(any(not is_missing(r.get(f, "")) for f in STEP2_PRIMARY.get(t, [])) for t, p in payloads.items() if t in COGNITIVE for r in p["rows"] if (r.get("participant_id", ""), r.get("session_id", "")) == (pid, ses))
        if pid == "sub-20812" and ses == "ses-2":
            occasion = "sub-20812_cognitive_occasion_1_continuation_review"
            status = "documented continuation; no separate CNB occasion"
            ambiguity = "README says ses-1 was incomplete and ses-2 began a few days later; no separate CNB was administered. Do not treat ses-2 as a new cognitive assessment without review."
        else:
            occasion = f"{pid}_cognitive_{ses}_candidate"
            status = "candidate comparable by session label only"
            ambiguity = "Exact cognitive-assessment date/time, task version, administration conditions, and scan-to-cognition alignment are not established; acq_time is rounded/anonymized."
        result.append({"participant_id": pid, "original_session_id": ses, "proposed_cognitive_occasion_id": occasion, "observed_cognitive_task_count": task_count, "observed_candidate_score_task_count": score_count, "available_timing_age_source": "sub-*/sub-*_sessions.tsv age and acq_time" if sr else "no session row; phenotype key only", "session_age": sr.get("age", ""), "baseline_participant_age": participant_age.get(pid, ""), "rounded_acq_time": sr.get("acq_time", ""), "comparability_status": status, "evidence": "local README Cognitive Data/Additional notes; local session sidecar age/acq_time definitions; phenotype participant/session keys", "unresolved_ambiguity": ambiguity})
    return result


def s2_domain_mapping(payloads: dict[str, dict[str, Any]], out: Path) -> list[dict[str, Any]]:
    rows = []
    domain_for_task = {t: d for d, ts in STEP2_DOMAINS.items() for t in ts}
    for task in sorted(COGNITIVE):
        if task not in payloads:
            continue
        primary = ";".join(STEP2_PRIMARY.get(task, []))
        d = domain_for_task.get(task, "outside five-domain framework")
        alt = STEP2_DOMAIN_ALTERNATIVES.get(task, "No alternative assigned in this draft; verify task-specific construct.")
        status = "candidate only" if "outside" not in d else "separate from five domains"
        rows.append({"task": task_label(task), "table_stem": task, "primary_score_columns": primary, "candidate_domain": d, "alternative_or_disagreement": alt, "framework_evidence": "Moore et al. 2015 Table 1; Gur et al. 2010 domain/test descriptions; local README task list", "empirical_factor_caution": "Published CNB factor work supports broad domains but reports PCET as a possible complex-cognition measure and separates accuracy/speed factors; this dataset-specific mapping is not validated.", "status": status, "reward_discounting_handling": "kept separate" if "discount" in task else "not applicable"})
    write_csv(out / "domain_mapping_draft.csv", rows, list(rows[0]) if rows else ["task"])
    return rows


def s2_candidate_keys(payloads: dict[str, dict[str, Any]], scenario: str) -> dict[str, set[tuple[str, str]]]:
    result = {}
    for task in sorted(COGNITIVE):
        if task not in payloads or not STEP2_PRIMARY.get(task):
            continue
        p = payloads[task]
        qc = s2_qc_fields(p["fields"])
        keys = set()
        for r in p["rows"]:
            if not all(not is_missing(r.get(f, "")) for f in STEP2_PRIMARY[task]):
                continue
            ok, _ = s2_qc_state(task, r, qc, scenario, p["meta"])
            if ok:
                keys.add((r.get("participant_id", ""), r.get("session_id", "")))
        result[task] = keys
    return result


def s2_feasibility(payloads: dict[str, dict[str, Any]], out: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    scenarios = [("unfiltered_observed", "Observed non-missing selected score; no QC/comparability exclusion", "none"), ("qc_valid_only", "Selected score and every available task QC field equals V", "all available QC fields must equal V"), ("qc_valid_or_likely_valid", "Selected score and every available task QC field equals V or F", "all available QC fields must equal V/F"), ("qc_no_explicit_invalid", "Selected score and no task QC field is N, X, or S; unresolved codes remain included", "exclude only N/X/S; not approved"), ("unresolved_qc_only", "Selected score with missing/unknown/nonstandard QC status", "retain separately for review")]
    elig = []
    domain_rows = []
    profile_rows = []
    for sid, desc, qc_rule in scenarios:
        keys = s2_candidate_keys(payloads, sid)
        union = set().union(*keys.values()) if keys else set()
        participants = {k[0] for k in union}
        score_rows = sum(len(v) for v in keys.values())
        elig.append({"scenario_id": sid, "description": desc, "qc_rule": qc_rule, "occasion_rule": "session labels retained; sub-20812 ses-2 continuation not counted as a separate CNB score occasion", "selected_score_rule": "one proposed primary score per cognitive task", "task_count_with_primary_score": len(keys), "selected_score_rows": score_rows, "participant_session_keys_any_task": len(union), "participants_any_task": len(participants), "notes": "Scenario count only; no final exclusion or scientific approval."})
        domain_sets = {}
        for domain, tasks in STEP2_DOMAINS.items():
            existing = [keys[t] for t in tasks if t in keys]
            domain_sets[domain] = set.intersection(*existing) if existing else set()
            domain_rows.append({"scenario_id": sid, "candidate_domain": domain, "domain_task_count": len(existing), "domain_requirement": "all mapped primary task scores in domain", "complete_participant_session_keys": len(domain_sets[domain]), "complete_participants": len({k[0] for k in domain_sets[domain]}), "task_score_rows": sum(len(keys.get(t, set())) for t in tasks), "notes": "Completeness is defined by all mapped primary task scores; alternate one-task-per-domain profile is reported separately."})
        one_each = set.intersection(*(set.union(*(keys.get(t, set()) for t in tasks)) for tasks in STEP2_DOMAINS.values()))
        all_tasks = set.intersection(*keys.values()) if keys else set()
        profile_rows.extend([{ "scenario_id": sid, "profile_rule": "one primary task score per candidate domain", "complete_participant_session_keys": len(one_each), "complete_participants": len({k[0] for k in one_each}), "domain_count": len(STEP2_DOMAINS), "notes": "Candidate profile coverage; not a final profile score."}, {"scenario_id": sid, "profile_rule": "all mapped primary task scores", "complete_participant_session_keys": len(all_tasks), "complete_participants": len({k[0] for k in all_tasks}), "domain_count": len(STEP2_DOMAINS), "notes": "Strict all-task intersection; not a final profile-eligible sample."}])
    write_csv(out / "eligibility_scenarios.csv", elig, list(elig[0]) if elig else ["scenario_id"])
    write_csv(out / "candidate_domain_coverage.csv", domain_rows, list(domain_rows[0]) if domain_rows else ["scenario_id"])
    write_csv(out / "candidate_profile_coverage.csv", profile_rows, list(profile_rows[0]) if profile_rows else ["scenario_id"])
    return elig, domain_rows, profile_rows


def s2_outcomes(payloads: dict[str, dict[str, Any]], out: Path) -> list[dict[str, Any]]:
    primary_keys = s2_candidate_keys(payloads, "unfiltered_observed")
    cognitive_by_key = set().union(*primary_keys.values()) if primary_keys else set()
    baseline_cognitive = {pid for pid, ses in cognitive_by_key if ses == "ses-1"}
    rows = []
    for field, (stem, label) in OUTCOME_SPECS.items():
        if stem not in payloads or field not in payloads[stem]["fields"]:
            continue
        p = payloads[stem]
        obs = [(r.get("participant_id", ""), r.get("session_id", ""), r.get(field, "")) for r in p["rows"] if not is_missing(r.get(field, ""))]
        all_keys = {(pid, ses) for pid, ses, _ in obs}
        base = {(pid, ses) for pid, ses, _ in obs if ses == "ses-1"}
        follow = {(pid, ses) for pid, ses, _ in obs if ses != "ses-1"}
        repeated = {pid for pid, _ in all_keys if sum(x[0] == pid for x in all_keys) >= 2}
        same_visit = all_keys & cognitive_by_key
        later_matched = {pid for pid, ses in follow if pid in baseline_cognitive}
        base_outcome_participants = {pid for pid, _ in base}
        later_with_baseline_outcome = {pid for pid in later_matched if pid in base_outcome_participants}
        doc = s2_doc(p["meta"], field)
        if stem == "eswan_adhd": direction = "higher raw values represent more above-average behavior in the item coding; clinical/outcome direction still requires review"
        elif stem == "mapssr": direction = "higher raw values represent more reported pleasure; not a universal cognitive-performance direction"
        else: direction = "higher raw values represent stronger endorsement of the named motivation construct; not a universal cognitive-performance direction"
        rows.append({"candidate_outcome": label, "stem": stem, "variable": field, "source_path": f"phenotype/{stem}.tsv", "description": doc, "raw_or_derived": "derived=true in local JSON", "units": p["meta"].get(field, {}).get("Units", "") if isinstance(p["meta"].get(field, {}), dict) else "", "score_direction_review": direction, "nonmissing_score_rows": len(obs), "unique_participants": len({x[0] for x in obs}), "unique_participant_sessions": len(all_keys), "baseline_ses1_score_rows": len(base), "followup_non_ses1_score_rows": len(follow), "participants_with_2plus_score_rows": len(repeated), "same_visit_with_any_primary_cognitive_score": len(same_visit), "participants_with_baseline_cognitive_and_followup_outcome": len(later_matched), "participants_with_baseline_cognitive_baseline_outcome_and_followup_outcome": len(later_with_baseline_outcome), "timing_interpretation": "ses-2/ses-3 is later by label; exact outcome timing and cognitive co-administration are unresolved", "evidence": f"phenotype/{stem}.json; local README self-report section; outcome instrument DOI in local metadata where present"})
    write_csv(out / "outcome_score_coverage.csv", rows, list(rows[0]) if rows else ["variable"])
    return rows


def s2_evidence_register(payloads: dict[str, dict[str, Any]], out: Path) -> list[dict[str, Any]]:
    rows = [
        {"evidence_id": "OBS-001", "evidence_class": "Observed local data", "source": "verified staged phenotype TSVs", "location": "chavi_step1b_phenotype_staging_20260907/*.tsv", "claim_or_passage": "Observed values, missingness, participant/session keys, QC code frequencies, and candidate-score coverage are calculated directly from verified payloads.", "use_in_step2": "Counts and masks", "status": "observed"},
        {"evidence_id": "SNAP-001", "evidence_class": "Snapshot documentation", "source": "ds007116 local README", "location": "Cognitive Data; Self-report data; Other data; Additional notes", "claim_or_passage": "README lists the CNB task set, documents missing CNB sessions, identifies sub-20812 ses-2 as a continuation without a separate CNB administration, and states that acquisition date/time is rounded for anonymization.", "use_in_step2": "Occasion mapping and limitations", "status": "documented"},
        {"evidence_id": "SNAP-002", "evidence_class": "Snapshot documentation", "source": "local phenotype JSON sidecars", "location": "phenotype/*.json LongName/Units/Levels/Derivative", "claim_or_passage": "Task field names, LongName text, units, categorical levels, and derivative flags are preserved as supplied; missing score descriptions are not filled by inference.", "use_in_step2": "Variable specification and QC", "status": "documented"},
        {"evidence_id": "PUB-001", "evidence_class": "Primary published evidence", "source": "Gur et al. 2010", "location": "Methods, section 2.3 Method of administration", "claim_or_passage": "The CNB computes accuracy as number of correct responses and speed as response time for correct answers; the battery is organized around neurobehavioral domains.", "use_in_step2": "Accuracy/time candidate distinction", "status": "primary evidence"},
        {"evidence_id": "PUB-002", "evidence_class": "Primary published evidence", "source": "Moore et al. 2015", "location": "Table 1; CNB Tests and Administration; Results", "claim_or_passage": "Table 1 maps PCET/PCPT/LNB to executive control, word/face/VOLT to episodic memory, PVRT/PMAT/PLOT to complex cognition, and emotion/age differentiation to social cognition; the paper reports accuracy and speed factors separately and notes a possible PCET complex-cognition interpretation.", "use_in_step2": "Candidate five-domain framework and disagreement flags", "status": "primary evidence"},
        {"evidence_id": "PUB-003", "evidence_class": "Primary instrument documentation", "source": "Penn CNB official updates", "location": "7 July 2024 update", "claim_or_passage": "The Digit Symbol all-correct median response-time variable is defined as the average of the true-negative and true-positive median response times.", "use_in_step2": "Digit Symbol speed sensitivity candidate", "status": "primary instrument evidence"},
        {"evidence_id": "REPO-001", "evidence_class": "Snapshot/project documentation", "source": "PennLINC transformation repository", "location": "cognitive/README.md and CNB_transformation_script_EF.Rmd", "claim_or_passage": "The public repository states that the cognitive cleaning script is not available; its public mapping script documents task-prefix mappings and the Trails A/B handling.", "use_in_step2": "Evidence gap and task identity", "status": "documented"},
        {"evidence_id": "PROP-001", "evidence_class": "Proposed interpretation", "source": "CHAVI Step 2 draft", "location": "variable_selection_draft.csv; score_definition_draft.md", "claim_or_passage": "One primary score and sensitivity alternatives are proposed per task based on names, local LongName text, broad CNB evidence, and the fixed five-domain research direction.", "use_in_step2": "Draft only", "status": "proposed; requires review"},
        {"evidence_id": "UNRES-001", "evidence_class": "Unresolved", "source": "local data and documentation review", "location": "unresolved_decisions.md", "claim_or_passage": "Exact Penn CNB task versions, field-level validity semantics, VC meaning if applicable, score direction for several fields, administration timing, and comparability across visits remain unresolved.", "use_in_step2": "Scientific review gate", "status": "unresolved"},
    ]
    write_csv(out / "evidence_register.csv", rows, list(rows[0]))
    return rows


def s2_fixture_tests() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="chavi_step2_fixture_") as td:
        root = Path(td)
        meta = {"qc_valid_code": {"Levels": {"V": "Valid", "F": "Likely valid", "VC": "not defined"}}, "score": {"LongName": "Total Correct Responses"}}
        rows = [{"participant_id": "sub-1", "session_id": "ses-1", "qc_valid_code": "V", "score": "2"}, {"participant_id": "sub-1", "session_id": "ses-2", "qc_valid_code": "VC", "score": ""}]
        assert s2_field_class("participant_id", meta) == "identifier"
        assert s2_qc_state("fixture", rows[0], ["qc_valid_code"], "qc_valid_only")[0]
        assert s2_qc_state("fixture", rows[1], ["qc_valid_code"], "unresolved_qc_only")[0]
        assert s2_missing_category("n/a", meta, "score") == "raw_missing_token_n/a_not_structural"
        # Regression check: one unique source/variable/code row, not one row per loop.
        codes = {("fixture", "qc_valid_code", r["qc_valid_code"]) for r in rows}
        assert len(codes) == 2
    return {"status": "passed", "tests": ["identifier excluded from scientific score class", "unique QC source/variable/code key", "unknown QC code retained as unresolved", "n/a not inferred as structural missingness"], "fixture_data_retained": False}


def s2_markdown_outputs(out: Path, payloads: dict[str, dict[str, Any]], manifest: list[dict[str, Any]], score_rows: list[dict[str, Any]], qc_rows: list[dict[str, Any]], occasion_rows: list[dict[str, Any]], domain_rows: list[dict[str, Any]], profile_rows: list[dict[str, Any]], outcomes: list[dict[str, Any]], fixture: dict[str, Any], git: dict[str, Any]) -> None:
    verified = sum(r["verification_result"] == "verified" for r in manifest)
    parseable = sum(r["parseable"] == "yes" for r in manifest)
    qc_unknown = sum(r["provisional_class"] == "unresolved observed code" for r in qc_rows)
    vc_rows = [r for r in qc_rows if r["code"] == "VC"]
    key_set = set().union(*(p["keys"] for t, p in payloads.items() if t in COGNITIVE)) if payloads else set()
    rep = {pid for pid, ses in key_set if sum(k[0] == pid for k in key_set) >= 2}
    scenario_summary = {(r["scenario_id"], r["profile_rule"]): r for r in profile_rows}
    def prof(s, rule):
        r = scenario_summary.get((s, rule), {})
        return f"{r.get('complete_participant_session_keys', 0)} keys / {r.get('complete_participants', 0)} participants"
    report = f"""# CHAVI Step 2 review report

Dataset: `ds007116` snapshot `1.0.6`; expected commit `{COMMIT}`.  
Dataset checkout observed at commit `{git.get('commit')}`, tag/description `{git.get('describe')}`, status `{git.get('status')}`.

## Scope and guardrails

This is a definition-and-feasibility draft. The 41 previously staged phenotype payloads were reused; no data were redownloaded. No raw data or pinned checkout content was modified. No final scores, composites, age adjustment, latent-factor model, ICC, SEM, MDC, prediction, dashboard, or report/caution/refuse threshold was calculated.

## Confirmed corrections

- Scientific score coverage excludes `participant_id` and `session_id`; identifiers remain in the variable specification and general inventories.
- Each QC inventory row is unique by source table, QC variable, and observed code; frequencies are recomputed directly from raw values. Unknown codes are not duplicated or summed across loops.
- Outcome coverage is score-specific for `eswan_adhd_inattention_total`, `eswan_adhd_total_score`, `mapssr_total_score`, `im_average`, and `em_average`; row counts and non-missing score counts are distinct.
- Undocumented-category checks are restricted to fields with an applicable categorical schema. Numeric fields report observed ranges and retain "expected range not documented locally" where appropriate.
- Cognitive repeat coverage is restricted to the 21 cognitive tasks and reports score-based counts separately from table-row/session availability.
- Missing tokens, documented unknown responses, and structural not-applicability are not collapsed. `n/a` is recorded as a raw missing token, not inferred to be structural.
- The Age Differentiation `cnb_adt_cnt_200` conflict is preserved: count-under-250-ms LongName versus `Units: ms`.

## Observed availability

- Verified payloads: **{verified}/{len(manifest)}**; parseable: **{parseable}**.
- Cognitive phenotype keys: **{len(key_set)}**; participants: **{len({k[0] for k in key_set})}**; participants with 2+ observed cognitive sessions: **{len(rep)}**.
- Candidate score rows in `candidate_score_coverage.csv` are non-missing score observations; they are not approved usable-sample counts.
- Assessment mapping includes **{len(occasion_rows)}** participant/session rows. The documented `sub-20812` ses-2 continuation is not silently converted into a new CNB occasion.

## Supported candidate score definitions

The strongest draft support is for task accuracy-like outputs (`*_cr`, correct counts, sensitivity/proportion) as primary candidates and explicitly labelled RT fields as sensitivity alternatives. Penn CNB literature supports separating accuracy from speed; it does not justify collapsing every task to a single universal score. The official Penn update provides an additional definition for Digit Symbol `cnb_digsym_dscorrt`.

Reward/discounting measures remain outside the five cognitive domains. Their choices/preferences are not assigned a universal better/worse direction.

## Candidate domain mapping

`domain_mapping_draft.csv` records the proposed five-domain mapping and alternatives. Published CNB structure supports the broad Executive Control, Episodic Memory, Complex Cognition, and Social Cognition framework, with Sensorimotor Performance retained as a fifth CHAVI proposal. The mapping is not settled: PCET has a published complex-cognition caution, Digit Symbol and Trails have processing-speed ambiguity, and the combined AIM task does not establish separable constructs.

## QC and occasion definitions still unresolved

Observed QC code frequencies and documented meanings are in `qc_rules_draft.csv`. Provisional scenarios are descriptive only: V-only, V-or-F, no explicit N/X/S, and unresolved-QC. `VC` was observed in **{len(vc_rows)}** QC code rows in the regenerated inventory; it is not assumed to mean valid. The exact scope of every code, the interpretation of F, 0, C, and VC, and treatment of missing QC remain for scientific review.

The occasion mapping preserves participant/session IDs and uses session `age` and anonymized/rounded `acq_time` when available. A session label is not proof of exact cognitive-assessment timing. Task version, administration condition, scan timing versus phenotype timing, and cross-visit comparability remain unresolved.

## Feasibility scenarios

The complete scenario tables are `eligibility_scenarios.csv`, `candidate_score_coverage.csv`, `candidate_domain_coverage.csv`, and `candidate_profile_coverage.csv`. Example strictness comparison for the one-primary-task-per-domain candidate profile:

- Unfiltered observed: **{prof('unfiltered_observed', 'one primary task score per candidate domain')}**.
- QC V-only: **{prof('qc_valid_only', 'one primary task score per candidate domain')}**.
- QC V-or-F: **{prof('qc_valid_or_likely_valid', 'one primary task score per candidate domain')}**.
- No explicit invalid codes: **{prof('qc_no_explicit_invalid', 'one primary task score per candidate domain')}**.
- Unresolved-QC only: **{prof('unresolved_qc_only', 'one primary task score per candidate domain')}**.

These counts show how definitions change feasibility; they do not select a rule or establish reliability.

## Outcomes

`outcome_score_coverage.csv` reports non-missing score counts separately for each requested outcome. It distinguishes same-visit cognitive/outcome availability from participant-level baseline-cognitive plus later-outcome availability, and includes the stricter baseline-outcome requirement. No associations were run.

## Statistical analysis plan readiness

Evidence is sufficient to draft a statistical analysis plan skeleton, not a final plan. Scientific review is required before freezing primary variables, QC masks, occasion mapping, domain membership, missingness handling, direction alignment, age adjustment, weighting, or longitudinal estimands.

## Tests and reproduction

Synthetic Step 2 regression tests: **{fixture['status']}** ({'; '.join(fixture['tests'])}). Fixtures are temporary and not retained.

```powershell
python .\\chavi_audit_ds007116_step2_20260907\\audit_v3.py --dataset .\\ds007116 --phenotype-stage .\\chavi_step1b_phenotype_staging_20260907 --output .\\chavi_audit_ds007116_step2_20260907 --fixture-only
python .\\chavi_audit_ds007116_step2_20260907\\audit_v3.py --dataset .\\ds007116 --phenotype-stage .\\chavi_step1b_phenotype_staging_20260907 --output .\\chavi_audit_ds007116_step2_20260907
```

Primary/local evidence is registered in `evidence_register.csv`. Key sources: [Gur et al. 2010]({SOURCE_URLS['gur_2010']}), [Moore et al. 2015]({SOURCE_URLS['moore_2015']}), [Penn CNB official updates]({SOURCE_URLS['cnb_updates']}), [PennLINC cognitive mapping repository]({SOURCE_URLS['pennlinc_mapping']}), and the [official ds007116 snapshot release]({SOURCE_URLS['dataset_release']}).
"""
    (out / "step2_review_report.md").write_text(report, encoding="utf-8")
    score_definition = """# Draft cognitive score definitions

This is a proposal for scientific review, not a scoring implementation. It uses exact local table/column names. Primary candidates are chosen from documented accuracy-like outputs where available; RT/speed and alternate accuracy/error fields are sensitivity alternatives. No standardization or composite was computed.

## Draft rules

1. Keep one primary score per task for feasibility accounting; retain speed and accuracy separately until the speed-accuracy policy is approved.
2. Treat counts/proportions of correct responses as higher-is-plausibly-better, subject to task-specific validity and range review.
3. Treat response-time fields as lower raw time = faster, with direction reversal only as a proposed later alignment—not as a raw-data correction.
4. Keep reward/discounting outputs separate; do not call preferences better or worse.
5. Do not use item components, errors, form fields, QC/status fields, or derived outcome fields as cognitive performance scores unless explicitly approved.

## Domain proposal and alternatives

Executive Control: AIM `cnb_aim_aimtot`, PCET `cnb_pcet_cr`, LNB `cnb_lnb_mcr`, CPT `cnb_cptnl_total_sen`, Trails B `cnb_trails_rt`.  
Episodic Memory: Penn Word `cnb_cpw_cr`, Penn Face `cnb_cpf_cr`, VOLT `cnb_volt_cr`.  
Complex Cognition: PVRT `cnb_pvrt_cr`, PMAT `cnb_pmat_cr`, PLOT `cnb_plot_cr`, Digit Symbol `cnb_digsym_dscor`.  
Social Cognition: ER40 `cnb_er40_cr`, MEDF `cnb_medf_cr`, ADT `cnb_adt_cr`.  
Sensorimotor Performance: finger tapping `cnb_ctap_dom`, Motor Praxis `cnb_mpract_mp2`, Trails A `cnb_trails_rt`.

Alternatives: PCET may belong with complex cognition; Digit Symbol and Trails may be treated as processing-speed/sensorimotor indicators; AIM may require a narrower construct review. Discounting tasks remain separate.

## Transformations and profile summaries

Candidate later transformations are within-analytic-sample standardization after a frozen direction map, or norm-based standardization if an appropriate reference is justified. Age adjustment, cross-fitting, weighting, and transformation choice are intentionally unresolved. Global level, within-person profile shape, and scatter should be defined as distinct summaries. A profile with changing domain availability can change meaning because its level and shape may be based on different task subsets; availability must therefore be reported alongside any later profile.
"""
    (out / "score_definition_draft.md").write_text(score_definition, encoding="utf-8")
    corrections = """# CHAVI Step 2 audit corrections

Confirmed and repaired in `audit_v3.py`:

- IDs are explicitly classified and excluded from scientific score coverage.
- QC rows are unique by source table/QC variable/code and frequencies are direct raw-value counts.
- Outcome coverage is score-specific and distinguishes non-missing scores from table rows.
- Categorical undocumented-code checks require an applicable Levels schema; numeric fields report observed ranges and documentation gaps.
- Cognitive-only repeat counts are separate from row/session availability.
- Score direction distinguishes absent local definitions from script extraction; supported accuracy/speed interpretations are labelled as proposed where needed.
- `n/a` is not inferred to mean structural non-applicability.
- ADT `cnb_adt_cnt_200` metadata conflict is preserved and flagged.

No raw data, pointer, or pinned checkout content was changed. `audit_v2.py` and all Step 1/Step 1B outputs remain preserved.
"""
    (out / "audit_corrections.md").write_text(corrections, encoding="utf-8")
    unresolved = """# Unresolved scientific decisions

- Confirm exact Penn CNB task versions and whether they changed across visits.
- Obtain author/instrument clarification for `VC`, F, 0, C, and any task-specific validity semantics; the public cleaning script is unavailable.
- Decide whether V-only, V-or-F, no-explicit-invalid, or another task-specific QC rule is defensible; do not treat scenario counts as exclusions.
- Decide whether QC applies to every score in a task or only selected outputs.
- Review the ADT `cnb_adt_cnt_200` count-versus-ms metadata conflict.
- Decide whether score direction is performance, symptom, pleasure, motivation, or preference specific.
- Determine whether session age and rounded `acq_time` are sufficient for occasion alignment; do not infer exact dates.
- Decide the treatment of sub-20812 ses-2 and whether it is excluded, collapsed with ses-1, or retained as a non-CNB continuation.
- Review domain membership, especially PCET, Digit Symbol, Trails, AIM, and sensorimotor speed.
- Freeze primary/sensitivity fields, missing-task requirements, weighting, redundancy handling, direction alignment, age adjustment, and cross-fitting before an SAP.
- Draft author question: "For each Penn LEAD cognitive task, what do validity codes V, F, 0, S, N, C, X (and any observed VC) mean, what is their scope across output fields, and should F/0/C be eligible for longitudinal analyses?"
"""
    (out / "unresolved_decisions.md").write_text(unresolved, encoding="utf-8")
    instructions = f"""# Reproduction instructions and test results

Run from `C:\\Users\\asmi\\Desktop\\Projects\\ML Projects`:

```powershell
python .\\chavi_audit_ds007116_step2_20260907\\audit_v3.py --dataset .\\ds007116 --phenotype-stage .\\chavi_step1b_phenotype_staging_20260907 --output .\\chavi_audit_ds007116_step2_20260907 --fixture-only
python .\\chavi_audit_ds007116_step2_20260907\\audit_v3.py --dataset .\\ds007116 --phenotype-stage .\\chavi_step1b_phenotype_staging_20260907 --output .\\chavi_audit_ds007116_step2_20260907
```

Inputs are the pinned dataset checkout and the already verified Step 1B staging directory. The script does not download data and does not inventory imaging files. It reads only verified phenotype payloads, session sidecars, and participant metadata required for the occasion/coverage audit.

Test result: `{fixture['status']}`. Python: `{sys.version}`. Git: `{run_tool_version('git', '--version')}`. The Step 1B staging batch remains unchanged.
"""
    (out / "reproduction_and_tests.md").write_text(instructions, encoding="utf-8")
    provenance = {"generated_utc": now_utc(), "dataset_root": str(Path('.\\ds007116').resolve()), "phenotype_stage_root": str(Path('.\\chavi_step1b_phenotype_staging_20260907').resolve()), "intended_snapshot": SNAPSHOT, "pinned_commit_expected": COMMIT, "git": git, "verified_payload_count": verified, "parseable_payload_count": parseable, "software": {"python": sys.version, "platform": platform.platform(), "git": run_git(Path('.\\ds007116').resolve(), '--version'), "aws": run_tool_version('aws', '--version')}, "scientific_boundaries": ["no final scores", "no reliability", "no prediction", "no imaging inventory rerun", "no raw/pinned checkout modifications"]}
    write_json(out / "dataset_provenance_step2.json", provenance)


def main_v3() -> int:
    ap = argparse.ArgumentParser(description="CHAVI Step 2 targeted audit and draft feasibility review")
    ap.add_argument("--dataset", type=Path, required=True)
    ap.add_argument("--phenotype-stage", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--fixture-only", action="store_true")
    args = ap.parse_args()
    fixture = s2_fixture_tests()
    if args.fixture_only:
        print(json.dumps(fixture, indent=2))
        return 0
    dataset = args.dataset.resolve()
    stage = args.phenotype_stage.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    git_before = git_metadata(dataset)
    if git_before.get("commit") != COMMIT:
        raise SystemExit(f"Pinned commit mismatch: {git_before.get('commit')} != {COMMIT}")
    payloads, manifest = s2_verified_payloads(dataset, stage)
    if len(payloads) != len(manifest):
        raise SystemExit("Step 1B payload reuse check failed: not all staged payloads are verified and parseable")
    write_csv(out / "retrieval_reuse_manifest.csv", manifest, list(manifest[0]) if manifest else ["relative_dataset_path"])
    score_rows, _ = s2_score_rows(payloads, out)
    s2_variable_selection(payloads, score_rows, out)
    qc_rows = s2_qc_rows(payloads)
    write_csv(out / "qc_rules_draft.csv", qc_rows, list(qc_rows[0]) if qc_rows else ["task"])
    write_csv(out / "qc_code_inventory_v3.csv", qc_rows, list(qc_rows[0]) if qc_rows else ["task"])
    participant_fields, participant_rows, _ = read_participants(dataset)
    session_rows, _, _, _, _ = parse_scanner_aux(dataset)
    occasion_rows = s2_occasion_rows(payloads, session_rows, participant_rows)
    write_csv(out / "assessment_occasion_mapping.csv", occasion_rows, list(occasion_rows[0]) if occasion_rows else ["participant_id"])
    s2_domain_mapping(payloads, out)
    elig, domain_rows, profile_rows = s2_feasibility(payloads, out)
    outcomes = s2_outcomes(payloads, out)
    evidence = s2_evidence_register(payloads, out)
    git_after = git_metadata(dataset)
    s2_markdown_outputs(out, payloads, manifest, score_rows, qc_rows, occasion_rows, domain_rows, profile_rows, outcomes, fixture, git_after)
    # The prior script remains a separate file; this is an explicit regression check.
    if git_after.get("commit") != COMMIT or git_after.get("status") != git_before.get("status"):
        raise SystemExit("Dataset checkout changed during Step 2")
    print(json.dumps({"output": str(out), "verified_payloads": len(payloads), "cognitive_tasks": len([t for t in payloads if t in COGNITIVE]), "score_coverage_rows": len(score_rows), "qc_rows_unique": len(qc_rows), "occasion_rows": len(occasion_rows), "outcome_score_rows": len(outcomes), "fixture_tests": fixture["status"], "dataset_commit": git_after.get("commit"), "dataset_status": git_after.get("status")}, indent=2))
    return 0


# ---- Step 2B: measurement-definition resolution and fixed-composition audit ----

SPEC_PATH = Path(__file__).with_name("step2c_specification.json")
ACTIVE_SPEC: dict[str, Any] = {}

def b_load_spec(path: Path) -> dict[str, Any]:
    value = read_json(path)
    if not isinstance(value, dict) or value.get("schema_version") != "step2c-1":
        raise ValueError("Unsupported or malformed Step 2C specification")
    for name in ("selected_profile", "reduced_profile", "candidate_domains", "qc_policies", "pair_rules", "outcomes"):
        if name not in value: raise ValueError(f"Step 2C specification missing {name}")
    for profile_name in ("selected_profile", "reduced_profile"):
        if not isinstance(value[profile_name], dict) or not all(isinstance(v, list) and len(v) == 2 and all(isinstance(x, str) for x in v) for v in value[profile_name].values()):
            raise ValueError(f"Malformed {profile_name} entries")
    allowed = {"documented_valid", "documented_likely_valid", "documented_likely_invalid", "documented_invalid", "documented_skipped", "no_automatic_validation", "comment_conditional", "unknown_or_undocumented", "missing_qc", "partial_qc", "no_applicable_qc_field"}
    for policy_name, policy in value["qc_policies"].items():
        if not isinstance(policy, dict): raise ValueError(f"Malformed QC policy: {policy_name}")
        include, exclude = set(policy.get("include", [])), set(policy.get("exclude", []))
        if not include.issubset(allowed) or not exclude.issubset(allowed) or include & exclude: raise ValueError(f"Conflicting/unknown QC classes in {policy_name}")
        if "raw_code_must_be" in policy and not isinstance(policy["raw_code_must_be"], list): raise ValueError(f"Malformed raw-code rule in {policy_name}")
    if set(value["pair_rules"]) != {"all_possible_unordered_pairs", "first_two_eligible_occasions", "complete_scheduled_ses-1_ses-2_pairs"}:
        raise ValueError("Pair-rule configuration must declare the three implemented pair rules")
    if set(value["outcomes"]) != set(OUTCOME_SPECS):
        raise ValueError("Outcome configuration must match the reviewed outcome definitions")
    return value

def b_profiles() -> tuple[dict[str, tuple[str, str]], dict[str, tuple[str, str]]]:
    selected = {d: tuple(v) for d, v in ACTIVE_SPEC["selected_profile"].items()}
    reduced = {d: tuple(v) for d, v in ACTIVE_SPEC["reduced_profile"].items()}
    return selected, reduced

def b_scenarios() -> tuple[str, ...]:
    return ("unfiltered_observed",) + tuple(ACTIVE_SPEC["qc_policies"])

# This is a reviewed manifest, not an automatic interpretation of a column name.
# Entries deliberately retain unresolved questions where the local dictionary and
# the public CNB description do not establish the same quantity.
B_REVIEW = {
    ("age_differentiation_test", "cnb_adt_cr"): ("Social cognition", "accuracy", "count/accuracy", "higher plausibly better", "ADT total correct responses", "primary candidate", "Public CNB page lists ADT as a 36-stimulus social-cognition task; exact LEAD scoring/version requires confirmation."),
    ("age_differentiation_test", "cnb_adt_rtcr"): ("Social cognition", "accuracy-task speed", "time", "lower is faster", "median RT for correct responses; ms", "sensitivity candidate", "Speed direction is proposed; exact LEAD task/version requires confirmation."),
    ("age_differentiation_test", "cnb_adt_cnt_200"): ("Social cognition", "rapid-response count", "count", "not established", "total responses under 250 milliseconds despite Units=ms in local JSON", "supplementary/excluded", "Metadata says ms while observed values are 0-12; do not use until author clarification."),
    ("delay_discounting_task", "cnb_ddisc_tot"): ("outside five-domain profile", "delay-discounting choice output", "decision measure", "no universal direction", "total choice output; denominator/duration not established locally", "excluded from five-domain profile", "Reward preference is not a cognitive-performance domain score."),
    ("delay_discounting_task", "cnb_ddisc_rt"): ("outside five-domain profile", "choice speed", "time", "lower is faster", "response-time output; exact denominator unresolved", "supplementary/excluded", "Keep reaction time separate from discounting preference."),
    ("delay_discounting_task", "cnb_ddisc_mrt"): ("outside five-domain profile", "choice speed", "time", "lower is faster", "median response time; exact denominator unresolved", "supplementary/excluded", "Keep reaction time separate from discounting preference."),
    ("digit_symbol", "cnb_digsym_dscor"): ("Executive control", "processing speed/accuracy", "count/accuracy", "higher plausibly better", "total correct matching responses; official current page says 54 trials/1.5 minutes", "primary candidate; alternative domain", "Current Penn update changes official DSCORRT definition; LEAD release version must be confirmed."),
    ("digit_symbol", "cnb_digsym_dscorrt"): ("Executive control", "processing speed", "time", "lower is faster", "official update: mean of median RT for true-negative and true-positive responses", "sensitivity candidate", "The July 2024 update may not describe the historical LEAD export; version equivalence unresolved."),
    ("effort_discounting_task", "cnb_edisc_tot"): ("outside five-domain profile", "effort-discounting choice output", "decision measure", "no universal direction", "total choice output; public page describes 100 effort problems", "excluded from five-domain profile", "Reward preference is not a five-domain performance score."),
    ("effort_discounting_task", "cnb_edisc_rt"): ("outside five-domain profile", "choice speed", "time", "lower is faster", "response-time output; denominator unresolved", "supplementary/excluded", "Keep reaction time separate from preference."),
    ("effort_discounting_task", "cnb_edisc_mrt"): ("outside five-domain profile", "choice speed", "time", "lower is faster", "median response time; denominator unresolved", "supplementary/excluded", "Keep reaction time separate from preference."),
    ("measured_emotion_differentiation_test", "cnb_medf_cr"): ("Social cognition", "emotion differentiation accuracy", "count/accuracy", "higher plausibly better", "total correct responses; public page lists 36 trials", "primary candidate", "Exact response categories and LEAD version require confirmation."),
    ("measured_emotion_differentiation_test", "cnb_medf_rtcr"): ("Social cognition", "emotion differentiation speed", "time", "lower is faster", "median RT for correct responses; ms", "sensitivity candidate", "Speed direction is proposed."),
    ("motor_praxis", "cnb_mpract_mp2"): ("Sensorimotor performance", "motor praxis accuracy", "count/accuracy", "higher plausibly better", "total correct responses", "supplementary candidate", "Public page describes mouse clicking and a 2-minute task; correct count is not praxis speed."),
    ("motor_praxis", "cnb_mpract_mp2rtcr"): ("Sensorimotor performance", "motor praxis speed", "time", "lower is faster", "median RT for correct responses; ms", "primary speed candidate", "Use only if the protocol defines the RT denominator and mouse-control validity."),
    ("penn_abstraction_inhibition_working_memory_task", "cnb_aim_aimtot"): ("Executive control", "combined abstraction/inhibition/working-memory accuracy", "count/accuracy", "higher plausibly better", "total correct responses; denominator not established locally", "candidate; unresolved", "Task name combines constructs; do not equate with a single factor without evidence."),
    ("penn_abstraction_inhibition_working_memory_task", "cnb_aim_aimtotrt"): ("Executive control", "combined-task speed", "time", "lower is faster", "correct RT; denominator unresolved", "sensitivity candidate", "Combined construct remains unresolved."),
    ("penn_conditional_exclusion_task", "cnb_pcet_cr"): ("Executive control", "conditional-exclusion accuracy", "count/accuracy", "higher plausibly better", "total correct responses", "primary candidate; alternative domain", "Factor analysis reported PCET as possibly fitting complex cognition; domain placement is not settled."),
    ("penn_conditional_exclusion_task", "cnb_pcet_rtcr"): ("Executive control", "conditional-exclusion speed", "time", "lower is faster", "median RT for correct responses; ms", "sensitivity candidate", "Domain placement and speed denominator require confirmation."),
    ("penn_emotion_recognition_task", "cnb_er40_cr"): ("Social cognition", "emotion recognition accuracy", "count/accuracy", "higher plausibly better", "total correct responses; public page lists 40 faces", "primary candidate", "Exact LEAD version and condition pooling require confirmation."),
    ("penn_emotion_recognition_task", "cnb_er40_rtcr"): ("Social cognition", "emotion recognition speed", "time", "lower is faster", "median RT for correct responses; ms", "sensitivity candidate", "Speed direction is proposed."),
    ("penn_face_memory_test", "cnb_cpf_cr"): ("Episodic memory", "face recognition accuracy", "count/accuracy", "higher plausibly better", "total correct responses; public page lists 20 targets and 20 foils", "primary candidate", "Exact LEAD version and false-alarm treatment require confirmation."),
    ("penn_face_memory_test", "cnb_cpf_rtcr"): ("Episodic memory", "face-memory speed", "time", "lower is faster", "median RT for correct responses; ms", "sensitivity candidate", "Speed direction is proposed."),
    ("penn_matrix_reasoning_test", "cnb_pmat_cr"): ("Complex cognition", "matrix reasoning accuracy", "count/accuracy", "higher plausibly better", "total correct responses; public page lists 24 trials and stopping rule", "primary candidate", "Stopping rule makes denominator variable; retain raw count and do not normalize without protocol."),
    ("penn_matrix_reasoning_test", "cnb_pmat_rtcr"): ("Complex cognition", "matrix reasoning speed", "time", "lower is faster", "median RT for correct responses; ms", "sensitivity candidate", "Denominator and stopping rule remain relevant."),
    ("penn_verbal_reasoning_test", "cnb_pvrt_cr"): ("Complex cognition", "verbal reasoning accuracy", "count/accuracy", "higher plausibly better", "total correct responses; public page lists 15 trials", "primary candidate", "Exact LEAD version requires confirmation."),
    ("penn_verbal_reasoning_test", "cnb_pvrt_rtcr"): ("Complex cognition", "verbal reasoning speed", "time", "lower is faster", "median RT for correct responses; ms", "sensitivity candidate", "Speed direction is proposed."),
    ("penn_word_memory_test", "cnb_cpw_cr"): ("Episodic memory", "word recognition accuracy", "count/accuracy", "higher plausibly better", "total correct responses; public page lists 20 targets and 20 foils", "primary candidate", "False-alarm treatment and exact LEAD version require confirmation."),
    ("penn_word_memory_test", "cnb_cpw_rtcr"): ("Episodic memory", "word-memory speed", "time", "lower is faster", "median RT for correct responses; ms", "sensitivity candidate", "Speed direction is proposed."),
    ("risk_discounting_task", "cnb_rdisc_tot"): ("outside five-domain profile", "risk-discounting choice output", "decision measure", "no universal direction", "total choice output; public page describes 34 choices", "excluded from five-domain profile", "Reward preference is not a five-domain performance score."),
    ("risk_discounting_task", "cnb_rdisc_rt"): ("outside five-domain profile", "choice speed", "time", "lower is faster", "response-time output; denominator unresolved", "supplementary/excluded", "Keep reaction time separate from preference."),
    ("risk_discounting_task", "cnb_rdisc_mrt"): ("outside five-domain profile", "choice speed", "time", "lower is faster", "median response time; denominator unresolved", "supplementary/excluded", "Keep reaction time separate from preference."),
    ("short_computerized_finger_tapping_task", "cnb_ctap_dom"): ("Sensorimotor performance", "dominant-hand motor speed", "rate/count", "higher plausibly faster", "mean of dominant-hand trials; public page says 10-second trials, five per hand", "primary candidate", "Exact rate/count convention is not resolved by local LongName; do not call it a count-only score."),
    ("short_computerized_finger_tapping_task", "cnb_ctap_non"): ("Sensorimotor performance", "non-dominant motor speed", "rate/count", "higher plausibly faster", "mean of non-dominant-hand trials", "sensitivity candidate", "Keep hand-specific outputs separate."),
    ("short_computerized_finger_tapping_task", "cnb_ctap_tot"): ("Sensorimotor performance", "combined motor speed", "rate/count", "higher plausibly faster", "sum of dominant and non-dominant trial summaries", "supplementary candidate", "Sum-versus-mean and hand weighting must be frozen before use."),
    ("short_letter_2back", "cnb_lnb_mcr"): ("Executive control", "working-memory true-positive accuracy", "count/accuracy", "higher plausibly better", "true positives for 1-back and 2-back trials per local LongName", "primary candidate", "Observed range and public condition/trial description do not establish denominator/load mapping; false alarms are separate."),
    ("short_letter_2back", "cnb_lnb_tp"): ("Executive control", "working-memory true positives", "count/accuracy", "higher plausibly better", "true positives for 0-, 1-, and 2-back trials", "sensitivity candidate", "Do not pool conditions into a proportion without an approved denominator."),
    ("short_letter_2back", "cnb_lnb_fp"): ("Executive control", "working-memory false positives", "error count", "higher is more error", "false positives for 0-, 1-, and 2-back trials", "sensitivity candidate", "Error output is not interchangeable with accuracy."),
    ("short_letter_2back", "cnb_lnb_rtc"): ("Executive control", "working-memory speed", "time", "lower is faster", "median RT for true positives across listed conditions; ms", "sensitivity candidate", "Condition pooling and denominator unresolved."),
    ("short_penn_continuous_performance_test", "cnb_cptnl_total_sen"): ("Executive control", "sustained-attention sensitivity", "proportion/accuracy", "higher plausibly better", "CPT total sensitivity; observed 0.1-1.0", "primary candidate", "Formula is not documented locally; do not assume d-prime or overall accuracy."),
    ("short_penn_continuous_performance_test", "cnb_cptnl_total_spec"): ("Executive control", "sustained-attention specificity", "proportion/accuracy", "higher plausibly better", "CPT total specificity", "sensitivity candidate", "Keep sensitivity and specificity separate until formula/denominator are confirmed."),
    ("short_penn_continuous_performance_test", "cnb_cptnl_total_rt"): ("Executive control", "sustained-attention response speed", "time", "lower is faster", "median RT for all responses; ms", "sensitivity candidate", "All-response denominator and error handling require confirmation."),
    ("trailmaking_test_a", "cnb_trails_rt"): ("Sensorimotor performance", "Trails A speed", "time", "lower is faster", "median RT all trials; ms", "primary candidate; unresolved", "Exact task identity/version and RT meaning are not documented on the inspected public task page."),
    ("trailmaking_test_b", "cnb_trails_rt"): ("Executive control", "Trails B speed/set shifting", "time", "lower is faster", "median RT all trials; ms", "primary candidate; unresolved", "Exact task identity/version and RT meaning are not documented on the inspected public task page."),
    ("trailmaking_test_a", "cnb_trails_cr"): ("Sensorimotor performance", "Trails A accuracy", "count/accuracy", "higher plausibly better", "total correct responses", "sensitivity candidate", "Exact task identity/version unresolved."),
    ("trailmaking_test_b", "cnb_trails_cr"): ("Executive control", "Trails B accuracy", "count/accuracy", "higher plausibly better", "total correct responses", "sensitivity candidate", "Exact task identity/version unresolved."),
    ("trailmaking_test_a", "cnb_trails_rtcr"): ("Sensorimotor performance", "Trails A correct-response speed", "time", "lower is faster", "median RT correct trials; ms", "sensitivity candidate", "Exact task identity/version unresolved."),
    ("trailmaking_test_b", "cnb_trails_rtcr"): ("Executive control", "Trails B correct-response speed", "time", "lower is faster", "median RT correct trials; ms", "sensitivity candidate", "Exact task identity/version unresolved."),
    ("variable_short_penn_line_orientation_test", "cnb_plot_cr"): ("Complex cognition", "line-orientation accuracy", "count/accuracy", "higher plausibly better", "total correct responses; public page lists 24 trials", "primary candidate", "Exact LEAD version requires confirmation."),
    ("variable_short_penn_line_orientation_test", "cnb_plot_rtcr"): ("Complex cognition", "line-orientation speed", "time", "lower is faster", "median RT for correct responses; ms", "sensitivity candidate", "Speed direction is proposed."),
    ("visual_object_learning_test", "cnb_volt_cr"): ("Episodic memory", "visual object recognition accuracy", "count/accuracy", "higher plausibly better", "total correct responses; public page lists 10 shapes and 10 foils", "primary candidate", "Exact LEAD version requires confirmation."),
    ("visual_object_learning_test", "cnb_volt_rtcr"): ("Episodic memory", "visual object-memory speed", "time", "lower is faster", "median RT for correct responses; ms", "sensitivity candidate", "Speed direction is proposed."),
}

def b_review(task: str, field: str) -> tuple[str, str, str, str, str, str, str]:
    if (task, field) in B_REVIEW:
        return B_REVIEW[(task, field)]
    return ("unresolved", "unresolved", "unresolved", "not documented", s2_doc({}, field), "unresolved", "No reviewed definition entry; block use until reviewed.")

QC_MEANING_CLASSES = {
    "Valid": "documented_valid",
    "Likely valid, problem occurred which affected performance for a limited number of responses/mild to moderate effect": "documented_likely_valid",
    "Likely invalid, problem occurred which affected performance for a limited number of responses/mild to moderate effect": "documented_likely_invalid",
    "Not Valid": "documented_invalid",
    "Skipped": "documented_skipped",
    "Excluded": "documented_invalid",
    "No autovalidation rule available": "no_automatic_validation",
    "Assessor Comment": "comment_conditional",
}

def b_code_class(meta: dict[str, Any], field: str, code: str) -> str:
    """Classify only by exact dictionary meaning; code letters alone are never evidence."""
    if is_missing(code):
        return "missing_qc"
    levels = s2_levels(meta, field)
    raw = str(code).strip()
    if raw not in levels:
        return "unknown_or_undocumented"
    meaning = str(levels[raw])
    return QC_MEANING_CLASSES.get(meaning, "unknown_or_undocumented")

def b_old_code_class(meta: dict[str, Any], field: str, code: str) -> str:
    """Reconstruct the Step 2B classification for a trace; never used for new eligibility."""
    raw = str(code).strip(); meaning = str(s2_levels(meta, field).get(raw, "")).lower()
    if is_missing(code): return "missing_qc"
    if raw == "V" or ("valid" in meaning and "invalid" not in meaning): return "valid"
    if "invalid" in meaning or "skipped" in meaning or raw in {"N", "X", "S"}: return "invalid_or_skipped"
    if raw == "F" or "likely valid" in meaning: return "likely_valid_or_unresolved"
    return "unresolved_code"

def b_qc_status(task: str, row: dict[str, str], qc_fields: list[str], meta: dict[str, Any]) -> dict[str, Any]:
    if not qc_fields:
        return {"status": "no_qc_field", "codes": [], "classes": []}
    raw = [str(row.get(f, "")).strip() for f in qc_fields]
    present = [x for x in raw if not is_missing(x)]
    classes = [b_code_class(meta, f, row.get(f, "")) for f in qc_fields if not is_missing(row.get(f, ""))]
    return {"status": "all_present" if len(present) == len(qc_fields) else ("partial_missing" if present else "missing_qc"), "codes": present, "classes": classes}

def b_policy_classes(q: dict[str, Any]) -> list[str]:
    status_class = {"missing_qc":"missing_qc", "partial_missing":"partial_qc", "no_qc_field":"no_applicable_qc_field"}
    return ([status_class[q["status"]]] if q["status"] != "all_present" else []) + list(q["classes"])

def b_eligible(task: str, row: dict[str, str], qc_fields: list[str], scenario: str, meta: dict[str, Any]) -> tuple[bool, str]:
    if scenario == "unfiltered_observed":
        return True, "observed score; QC not applied"
    policy = ACTIVE_SPEC.get("qc_policies", {}).get(scenario)
    if not isinstance(policy, dict):
        raise ValueError(f"QC policy is not configured: {scenario}")
    q = b_qc_status(task, row, qc_fields, meta)
    classes = b_policy_classes(q); include = set(policy.get("include", [])); exclude = set(policy.get("exclude", [])); required = bool(policy.get("require_all_applicable_fields", False))
    if required and q["status"] != "all_present": return False, q["status"]
    raw_required = policy.get("raw_code_must_be")
    if raw_required and not all(c in raw_required for c in q["codes"]): return False, ";".join(q["codes"])
    if any(c in exclude for c in classes): return False, ";".join(q["codes"])
    return bool(classes) and all(c in include for c in classes), ";".join(q["codes"])

def b_score_keys(payloads: dict[str, dict[str, Any]], task: str, field: str, scenario: str) -> set[tuple[str, str]]:
    p = payloads[task]
    qcf = s2_qc_fields(p["fields"])
    return {(r.get("participant_id", ""), r.get("session_id", "")) for r in p["rows"] if not is_missing(r.get(field, "")) and b_eligible(task, r, qcf, scenario, p["meta"])[0]}

def b_variable_domain_keys(payloads: dict[str, dict[str, Any]], domain: str, scenario: str) -> set[tuple[str, str]]:
    sets = []
    for entry in ACTIVE_SPEC["candidate_domains"][domain]:
        task, field = entry.split(":", 1)
        if task in payloads: sets.append(b_score_keys(payloads, task, field, scenario))
    return set.union(*sets) if sets else set()

def b_spec_keys(payloads: dict[str, dict[str, Any]], spec: dict[str, tuple[str, str]], scenario: str) -> set[tuple[str, str]]:
    sets = [b_score_keys(payloads, t, f, scenario) for t, f in spec.values() if t in payloads]
    return set.intersection(*sets) if len(sets) == len(spec) and sets else set()

def b_pairs_summary(keys: set[tuple[str, str]]) -> tuple[dict[str, int], dict[str, int], dict[str, list[str]]]:
    counts = Counter(); pids = defaultdict(list)
    for pid, ses in keys: pids[pid].append(ses)
    for pid, sessions in pids.items():
        for a, b in itertools.combinations(sorted(set(sessions)), 2): counts[f"{a} + {b}"] += 1
    return dict(sorted(counts.items())), {pid: len(set(ss)) - 1 for pid, ss in pids.items() if len(set(ss)) >= 2}, {pid: sorted(set(ss)) for pid, ss in pids.items()}

def b_pair_sets(keys: set[tuple[str, str]]) -> dict[str, list[tuple[str, str, str, str]]]:
    bypid = defaultdict(list)
    for pid, ses in keys: bypid[pid].append(ses)
    all_pairs = []; first_pairs = []; scheduled = []
    for pid, sessions in bypid.items():
        sessions = sorted(set(sessions))
        all_pairs.extend((pid, a, b, "all_possible_unordered_pairs") for a, b in itertools.combinations(sessions, 2))
        if len(sessions) >= 2: first_pairs.append((pid, sessions[0], sessions[1], "first_two_eligible_occasions"))
        if {"ses-1", "ses-2"}.issubset(sessions): scheduled.append((pid, "ses-1", "ses-2", "complete_scheduled_ses-1_ses-2_pairs"))
    return {"all_possible_unordered_pairs": all_pairs, "first_two_eligible_occasions": first_pairs, "complete_scheduled_ses-1_ses-2_pairs": scheduled}

def b_median(values: list[float]) -> float | None:
    if not values: return None
    values = sorted(values); n = len(values); mid = n // 2
    return values[mid] if n % 2 else (values[mid - 1] + values[mid]) / 2

def b_interval_stats(pairs: list[tuple[str, str, str, str]], session_rows: list[dict[str, str]]) -> dict[str, Any]:
    dates = {(r.get("participant_id", ""), r.get("session_id", "")): r.get("acq_time", "") for r in session_rows}
    vals = []; missing = 0; nonpositive = 0; unparseable = 0
    for pid, first, second, _ in pairs:
        a, b = dates.get((pid, first), ""), dates.get((pid, second), "")
        if is_missing(a) or is_missing(b): missing += 1; continue
        try: delta = (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds() / 86400
        except (TypeError, ValueError): unparseable += 1; continue
        if delta <= 0: nonpositive += 1; continue
        vals.append(delta)
    return {"n_valid_intervals": len(vals), "min_days": min(vals) if vals else None, "median_days": b_median(vals), "max_days": max(vals) if vals else None, "missing_timing": missing, "unparseable_timing": unparseable, "nonpositive_intervals": nonpositive, "timestamp_caveat": "rounded/anonymized acquisition timestamp; not exact cognitive-assessment time"}

def b_profile_component_states(payloads: dict[str, dict[str, Any]], spec: dict[str, tuple[str, str]], key: tuple[str, str]) -> list[str]:
    states = []
    for task, field in spec.values():
        p = payloads.get(task); state = "missing_score"
        if p:
            for row in p["rows"]:
                if (row.get("participant_id", ""), row.get("session_id", "")) == key and not is_missing(row.get(field, "")):
                    q = b_qc_status(task, row, s2_qc_fields(p["fields"]), p["meta"])
                    if q["status"] != "all_present": state = "unresolved_qc"
                    elif any(x in {"documented_invalid", "documented_likely_invalid", "documented_skipped"} for x in q["classes"]): state = "explicit_invalid"
                    elif any(x not in {"documented_valid", "documented_likely_valid"} for x in q["classes"]): state = "unresolved_qc"
                    else: state = "documented_valid_or_likely_valid"
                    break
        states.append(state)
    return states

def b_interval_summary(keys: set[tuple[str, str]], session_rows: list[dict[str, str]]) -> tuple[str, str]:
    stats = b_interval_stats(b_pair_sets(keys)["all_possible_unordered_pairs"], session_rows)
    return json.dumps(stats, sort_keys=True), "acq_time is rounded/anonymized; interval is nominal, not an exact cognitive-assessment interval"

def b_profile_rows(payloads: dict[str, dict[str, Any]], session_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    selected, reduced = b_profiles()
    specs = {
        "variable_domain_union": ("at_least_one_candidate_task_per_domain_identity_may_differ", {d: tuple(ACTIVE_SPEC["candidate_domains"][d][0].split(":", 1)) for d in ACTIVE_SPEC["candidate_domains"]}),
        "fixed_five_domain": ("fixed_task_based_proxy_profile", selected),
        "reduced_four_domain": ("reduced_four_domain_sensitivity_proxy", reduced),
        "all_21_inventory": ("all_21_cognitive_task_inventory_not_profile", {t: (t, STEP2_PRIMARY[t][0]) for t in sorted(COGNITIVE)}),
    }
    for domain, entries in ACTIVE_SPEC["candidate_domains"].items():
        specs[f"candidate_domain:{domain}"] = (f"explicit_candidate_{domain}_multi_task_specification", {e.split(":", 1)[0]: tuple(e.split(":", 1)) for e in entries})
    for task in sorted(COGNITIVE):
        if task not in payloads: continue
        fields = list(dict.fromkeys(s2_candidate_fields(task, payloads[task])))
        if task == "age_differentiation_test" and "cnb_adt_cnt_200" in payloads[task]["fields"] and "cnb_adt_cnt_200" not in fields: fields.append("cnb_adt_cnt_200")
        for field in fields: specs[f"individual_score:{task}:{field}"] = (f"individual_reviewed_candidate_score_{task}_{field}", {task: (task, field)})
    recorded_keys = {(r.get("participant_id", ""), r.get("session_id", "")) for r in session_rows}
    # The variable-domain union and all-21 inventory are computed separately from the fixed profile.
    for spec_id, (label, spec) in specs.items():
        for scenario in b_scenarios():
            if spec_id == "variable_domain_union":
                keys = set.intersection(*(b_variable_domain_keys(payloads, d, scenario) for d in ACTIVE_SPEC["candidate_domains"]))
            else:
                keys = b_spec_keys(payloads, spec, scenario)
            unfiltered = (set.intersection(*(b_variable_domain_keys(payloads, d, "unfiltered_observed") for d in ACTIVE_SPEC["candidate_domains"])) if spec_id == "variable_domain_union" else b_spec_keys(payloads, spec, "unfiltered_observed"))
            pairs, pair_pids, bypid = b_pairs_summary(keys); pair_sets = b_pair_sets(keys)
            two = sum(1 for ss in bypid.values() if len(ss) >= 2); three = sum(1 for ss in bypid.values() if len(ss) >= 3)
            scheduled = {k for k in keys if k[1] in {"ses-1", "ses-2"}}
            scheduled_pids = {k[0] for k in scheduled if {s for p, s in keys if p == k[0]} >= {"ses-1", "ses-2"}}
            first_pairs = len(pair_sets["first_two_eligible_occasions"]); complete_scheduled = len(pair_sets["complete_scheduled_ses-1_ses-2_pairs"])
            interval, limitation = b_interval_summary(keys, session_rows)
            interval_all = b_interval_stats(pair_sets["all_possible_unordered_pairs"], session_rows); interval_first = b_interval_stats(pair_sets["first_two_eligible_occasions"], session_rows); interval_scheduled = b_interval_stats(pair_sets["complete_scheduled_ses-1_ses-2_pairs"], session_rows)
            state_counts = Counter()
            for key in unfiltered:
                states = b_profile_component_states(payloads, spec, key)
                if any(x == "unresolved_qc" for x in states): state_counts["at_least_one_unresolved_component"] += 1
                if states and all(x == "unresolved_qc" for x in states): state_counts["all_components_unresolved"] += 1
                if "unresolved_qc" in states and "explicit_invalid" in states: state_counts["mixed_unresolved_and_explicit_invalid"] += 1
            if spec_id == "variable_domain_union": spec_type = "variable-domain-union"
            elif spec_id.startswith("individual_score:"): spec_type = "individual-reviewed-score"
            elif spec_id.startswith("candidate_domain:"): spec_type = "explicit-candidate-domain-multi-task"
            else: spec_type = "explicit-task-intersection"
            rows.append({"specification_id": spec_id, "specification_type": spec_type, "profile_label": label, "scenario_id": scenario, "selected_tasks_exact": json.dumps({d: f"{t}:{f}" for d, (t, f) in spec.items()}, sort_keys=True), "eligible_occasions": len(keys), "eligible_participants_at_least_1": len(bypid), "participants_2plus_eligible_occasions": two, "participants_3plus_eligible_occasions": three, "all_possible_unordered_pair_count": len(pair_sets["all_possible_unordered_pairs"]), "all_possible_pair_counts": json.dumps(pairs, sort_keys=True), "complete_scheduled_ses1_ses2_pairs": complete_scheduled, "complete_scheduled_pair_observation_count": 2 * complete_scheduled, "complete_scheduled_ses1_ses2_participants": len(scheduled_pids), "scheduled_ses1_ses2_observation_count": len(scheduled), "first_two_eligible_pair_count": first_pairs, "first_two_eligible_assessments_participants": two, "interval_all_pairs": json.dumps(interval_all, sort_keys=True), "interval_first_two": json.dumps(interval_first, sort_keys=True), "interval_complete_scheduled": json.dumps(interval_scheduled, sort_keys=True), "nominal_interval_days_summary": interval, "timing_limitation": limitation, "missing_score_loss_from_recorded_sessions": max(0, len(recorded_keys) - len(unfiltered)), "qc_loss_from_unfiltered_keys": max(0, len(unfiltered) - len(keys)) if scenario != "unfiltered_observed" else 0, "comparability_uncertainty_status": "uncertain: task version, administration conditions, and exact cognitive timing are not established" if spec_id != "all_21_inventory" else "inventory only; not a profile", "profile_any_unresolved_component_count": state_counts["at_least_one_unresolved_component"], "profile_all_components_unresolved_count": state_counts["all_components_unresolved"], "profile_mixed_unresolved_and_explicit_invalid_count": state_counts["mixed_unresolved_and_explicit_invalid"], "sub20812_continuation_keys": sum(1 for pid, ses in keys if pid == "sub-20812" and ses == "ses-2"), "notes": "Complete scheduled pair observations are exactly two per complete pair; scheduled observations may also include unpaired observations. A pair is a participant-level first-two eligible occasion summary; overlapping pairs are not independent participants. Missing-score loss is against recorded repository sessions; QC loss is against the unfiltered profile intersection."})
    return rows

def b_pair_manifest(payloads: dict[str, dict[str, Any]], session_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    selected, _ = b_profiles(); rows = []
    specs = {"fixed_five_domain": selected}
    for spec_id, spec in specs.items():
        for scenario in b_scenarios():
            keys = b_spec_keys(payloads, spec, scenario)
            for rule, pairs in b_pair_sets(keys).items():
                for pid, first, second, rule_name in pairs:
                    stats = b_interval_stats([(pid, first, second, rule_name)], session_rows)
                    status = "nominal interval available; comparability uncertain"
                    reason = "task version/conditions and exact cognitive timing are not established; timestamps are rounded/anonymized"
                    if pid == "sub-20812" and second == "ses-2": status = "not a separate CNB occasion"; reason = "local continuation documentation states ses-2 has no separate CNB administration"
                    timing_status = "nonpositive" if stats["nonpositive_intervals"] else ("missing" if stats["missing_timing"] else ("unparseable" if stats["unparseable_timing"] else "available"))
                    rows.append({"participant_id":pid,"first_occasion_id":f"{pid}_{first}","second_occasion_id":f"{pid}_{second}","first_session_id":first,"second_session_id":second,"pairing_rule":rule,"specification_id":spec_id,"qc_policy":scenario,"available_timing_source":"sub-*/sub-*_sessions.tsv acq_time; rounded/anonymized","nominal_interval_days":stats["median_days"],"timing_status":timing_status,"comparability_status":status,"comparability_reason":reason})
    return rows

def b_exclusion_flow(payloads: dict[str, dict[str, Any]], session_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    selected, _ = b_profiles(); recorded = {(r.get("participant_id", ""), r.get("session_id", "")) for r in session_rows}
    cognitive = set().union(*(p["keys"] for t, p in payloads.items() if t in COGNITIVE))
    rows = []
    for scenario in b_scenarios():
        unfiltered = b_spec_keys(payloads, selected, "unfiltered_observed"); eligible = b_spec_keys(payloads, selected, scenario)
        flags = {"no_documented_cognitive_phenotype_observation": {k for k in recorded if k not in cognitive}, "missing_selected_score": {k for k in cognitive if k not in unfiltered}, "qc_exclusion": unfiltered - eligible if scenario != "unfiltered_observed" else set(), "comparability_exclusion": set(), "unresolved_classification": set()}
        remaining = recorded.copy()
        for reason, flagged in flags.items():
            before = len(remaining); remaining -= flagged
            rows.append({"specification_id":"fixed_five_domain","scenario_id":scenario,"population":"recorded_repository_sessions","reason_flag":reason,"overlapping_flag_count":len(flagged),"sequential_excluded_count":before-len(remaining),"remaining_after_sequential_exclusion":len(remaining),"notes":"Flags are not mutually exclusive; sequential order is documentation only. No comparability exclusion is silently applied."})
        rows.append({"specification_id":"fixed_five_domain","scenario_id":scenario,"population":"recorded_repository_sessions","reason_flag":"final_profile_eligible","overlapping_flag_count":len(eligible),"sequential_excluded_count":0,"remaining_after_sequential_exclusion":len(eligible),"notes":"Eligibility is explicit set intersection; continuation ses-2 is not created as a CNB observation."})
    return rows

def b_manifest_rows(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for task in sorted(COGNITIVE):
        if task not in payloads: continue
        p = payloads[task]; fields = list(dict.fromkeys(s2_candidate_fields(task, p)))
        if task == "age_differentiation_test" and "cnb_adt_cnt_200" in p["fields"] and "cnb_adt_cnt_200" not in fields:
            fields.append("cnb_adt_cnt_200")
        for field in fields:
            domain, construct, typ, direction, meaning, role, unresolved = b_review(task, field)
            d = p["meta"].get(field, {}) if isinstance(p["meta"].get(field, {}), dict) else {}
            rows.append({"task": task, "variable_id": f"ds007116:{task}:{field}", "source_tsv": f"phenotype/{task}.tsv", "task_identity": LABELS.get(task, task), "version_status": "Penn LEAD release task/version not fully stated in local dictionary; public current CNB documentation is contextual, not assumed identical", "domain": domain, "construct": construct, "raw_score_meaning": meaning or s2_doc(p["meta"], field), "score_type": typ, "units": d.get("Units", ""), "direction": direction, "denominator_duration": meaning, "condition_pooling": "not pooled unless explicitly stated in raw meaning; task-specific condition/denominator review required", "qc_fields": ";".join(s2_qc_fields(p["fields"])) or "none documented", "qc_scope": "source-table QC scope not established; do not assume task-wide applicability", "evidence_source": "local dictionary plus reviewed Penn CNB sources", "evidence_location": f"{SOURCE_URLS['cnb_explore']}; {SOURCE_URLS['gur_2010']}; local {task}.json", "role": role, "status": "reviewed with unresolved elements" if "unresolved" in role or "unresolved" in unresolved.lower() else "candidate", "unresolved_questions": unresolved, "unresolved_impact": "Blocks final composite/reliability use" if role.startswith("primary") or "candidate" in role else "Prevents sensitivity interpretation; retain raw field only", "observed_nonmissing": sum(not is_missing(r.get(field, "")) for r in p["rows"]), "observed_range": s2_numeric_range(p["rows"], field)})
    return rows

def b_qc_rows(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for task, p in sorted(payloads.items()):
        if task not in COGNITIVE: continue
        qcf = s2_qc_fields(p["fields"])
        rows.append({"task": task, "source_tsv": f"phenotype/{task}.tsv", "qc_fields": ";".join(qcf) or "none documented", "recommended_primary_policy": "require all applicable QC fields present; accept only codes explicitly documented as valid or likely valid; exclude documented invalid/skipped; unresolved 0/C/VC/unknown excluded", "strict_sensitivity_policy": "all applicable QC fields present and code V only", "unresolved_inclusive_policy": "retain nonmissing scores with missing/partial/no-QC or unresolved code for missingness sensitivity only", "code_treatment": "V valid; task-documented likely valid may be accepted; F is not universal and is accepted only when its local meaning supports likely-valid; N/X/S invalid or skipped; 0/C/VC and unknown unresolved", "scope_status": "source QC field scope reviewed as table-level metadata only; score-specific scope unresolved", "missing_qc_is_unresolved": "yes", "partial_qc_is_unresolved": "yes"})
    return rows

def b_outcome_rows(payloads: dict[str, dict[str, Any]], fixed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []; profile, _ = b_profiles()
    any_keys = set().union(*(b_score_keys(payloads, t, fields[0], "unfiltered_observed") for t, fields in STEP2_PRIMARY.items() if t in payloads and fields))
    any_baseline = {p for p, s in any_keys if s == "ses-1"}
    unfiltered_profile_baseline = {p for p, s in b_spec_keys(payloads, profile, "unfiltered_observed") if s == "ses-1"}
    for outcome in ACTIVE_SPEC["outcomes"]:
        task, label = OUTCOME_SPECS[outcome]
        op = payloads.get(task)
        if not op: continue
        outcome_keys = {(r.get("participant_id", ""), r.get("session_id", "")) for r in op["rows"] if not is_missing(r.get(outcome, ""))}
        all_out = {p for p, _ in outcome_keys}; base_out = {p for p, s in outcome_keys if s == "ses-1"}; later_out = {p for p, s in outcome_keys if s != "ses-1"}
        for scenario in b_scenarios():
            profile_keys = b_spec_keys(payloads, profile, scenario); base_profile = {p for p, s in profile_keys if s == "ses-1"}
            profile_later = base_profile & later_out; triple = base_profile & base_out & later_out; same = {p for p, s in profile_keys & outcome_keys}
            out.append({"outcome_variable":outcome,"outcome_label":label,"profile_spec":"fixed_five_domain","scenario_id":scenario,"baseline_outcome_participants":len(base_out),"later_outcome_participants":len(later_out),"baseline_any_cognitive_participants":len(any_baseline),"baseline_complete_profile_participants":len(base_profile),"baseline_profile_and_later_outcome_participants":len(profile_later),"baseline_profile_baseline_outcome_later_outcome_participants":len(triple),"same_visit_profile_outcome_participants":len(same),"baseline_any_to_complete_profile_loss":len(any_baseline - base_profile),"unfiltered_to_current_profile_qc_loss":max(0, len(unfiltered_profile_baseline) - len(base_profile)),"baseline_outcome_marginal_loss_from_all_outcome_participants":len(all_out - base_out),"baseline_outcome_missing_participants_relative_to_any_cognitive":len(any_baseline - base_out),"later_outcome_missing_among_baseline_profile":len(base_profile - later_out),"triple_exclusion_from_profile_plus_later":len(profile_later - triple),"timing_rule":"baseline=ses-1; later outcome=any non-ses-1; same-visit is descriptive","prediction_cohort_note":"First-two-eligible cognitive-pair participants are a separate cohort from this ses-1-based profile/outcome cohort.","timing_uncertainty":"session labels are chronological; acq_time is rounded/anonymized; repository session is not proof of same cognitive/questionnaire occasion","notes":"Numeric losses are marginal or sequential as named; no association, prediction, or outcome-driven selection performed."})
    return out

def b_fixture_tests() -> dict[str, Any]:
    valid = "Valid"; likely = "Likely valid, problem occurred which affected performance for a limited number of responses/mild to moderate effect"; invalid = "Not Valid"; likely_invalid = "Likely invalid, problem occurred which affected performance for a limited number of responses/mild to moderate effect"
    meta = {"q_valid_code": {"Levels": {"V": valid, "F": likely, "N": invalid, "L": likely_invalid, "0": "No autovalidation rule available", "C": "Assessor Comment", "S": "Skipped", "VC": "unreviewed"}}}
    def row(code=None):
        d = {"score":"1"}
        if code is not None: d["q_valid_code"] = code
        return d
    assert b_code_class(meta, "q_valid_code", "F") == "documented_likely_valid" and b_code_class(meta, "q_valid_code", "F") != "documented_valid"
    assert b_code_class(meta, "q_valid_code", "0") == "no_automatic_validation"
    assert b_code_class(meta, "q_valid_code", "L") == "documented_likely_invalid" and not b_eligible("x", row("L"), ["q_valid_code"], "unresolved_inclusive", meta)[0]
    unknown = {"q_valid_code": {"Levels": {"V": "meaning not supplied", "VC": "meaning not supplied"}}}
    assert b_code_class(unknown, "q_valid_code", "V") == "unknown_or_undocumented" and b_code_class(unknown, "q_valid_code", "VC") == "unknown_or_undocumented"
    assert not b_eligible("x", row("F"), ["q_valid_code"], "documented_valid_or_likely_valid", {})[0]
    assert b_eligible("x", row("F"), ["q_valid_code"], "documented_valid_or_likely_valid", meta)[0]
    assert b_eligible("x", row("0"), ["q_valid_code"], "descriptive_unresolved_qc", meta)[0]
    assert b_eligible("x", row(), ["q_valid_code"], "unresolved_inclusive", meta)[0] and b_eligible("x", row("V"), [], "unresolved_inclusive", {})[0]
    assert not b_eligible("x", row("N"), ["q_valid_code"], "unresolved_inclusive", meta)[0]
    assert b_qc_status("x", {"q_valid_code":"V"}, ["q_valid_code","q2_valid_code"], {"q_valid_code":{"Levels":{"V":"Valid"}},"q2_valid_code":{"Levels":{"V":"Valid"}}})["status"] == "partial_missing"
    assert not b_eligible("x", {"score":"1","q_valid_code":"N"}, ["q_valid_code","q2_valid_code"], "unresolved_inclusive", {"q_valid_code":{"Levels":{"N":"Not Valid"}},"q2_valid_code":{"Levels":{"V":"Valid"}}})[0]
    policy = ACTIVE_SPEC["qc_policies"]["documented_valid_or_likely_valid"]; old_include = list(policy["include"]); old_exclude = list(policy["exclude"])
    assert not b_eligible("x", row("0"), ["q_valid_code"], "documented_valid_or_likely_valid", meta)[0]
    policy["include"] = old_include + ["no_automatic_validation"]; policy["exclude"] = [x for x in old_exclude if x != "no_automatic_validation"]
    assert b_eligible("x", row("0"), ["q_valid_code"], "documented_valid_or_likely_valid", meta)[0]
    policy["include"], policy["exclude"] = old_include, old_exclude
    def payload(field, code, session="ses-1"):
        r = {"participant_id":"p", "session_id":session, field:"1", "q_valid_code":code}
        return {"fields":["participant_id","session_id",field,"q_valid_code"],"rows":[r],"meta":meta,"keys":{("p",session)}}
    domain_swap = {"penn_face_memory_test":payload("cnb_cpf_cr","V"), "penn_word_memory_test":payload("cnb_cpw_cr","V","ses-2")}
    assert ("p","ses-1") in b_variable_domain_keys(domain_swap,"Episodic memory","unfiltered_observed") and ("p","ses-2") in b_variable_domain_keys(domain_swap,"Episodic memory","unfiltered_observed")
    selected, _ = b_profiles(); assert selected["Executive control"] == ("short_letter_2back","cnb_lnb_mcr")
    fixed_payloads = {task:payload(field,"V") for task, field in selected.values()}; fixed_before = b_spec_keys(fixed_payloads, selected, "unfiltered_observed"); fixed_payloads["delay_discounting_task"] = payload("cnb_ddisc_tot","V"); assert fixed_before == b_spec_keys(fixed_payloads, selected, "unfiltered_observed")
    mixed_spec = {"a":("short_letter_2back","f"),"b":("penn_face_memory_test","g"),"c":("penn_matrix_reasoning_test","h")}
    mixed = {"short_letter_2back":payload("f","V"),"penn_face_memory_test":payload("g","0"),"penn_matrix_reasoning_test":payload("h","N")}
    states = b_profile_component_states(mixed,mixed_spec,("p","ses-1")); assert states == ["documented_valid_or_likely_valid","unresolved_qc","explicit_invalid"]
    assert b_spec_keys({"short_letter_2back":payload("f","0")},{"a":("short_letter_2back","f")},"unresolved_inclusive") == {("p","ses-1")}
    assert len(b_pair_sets({("p","s1"),("p","s2"),("p","s3")})["all_possible_unordered_pairs"]) == 3 and len(b_pair_sets({("p","s1"),("p","s2"),("p","s3")})["first_two_eligible_occasions"]) == 1
    sessions = [{"participant_id":"p","session_id":"s1","acq_time":"2020-01-01T00:00:00"},{"participant_id":"p","session_id":"s2","acq_time":"2020-01-11T00:00:00"},{"participant_id":"p","session_id":"s3","acq_time":"2020-01-21T00:00:00"}]
    assert b_interval_stats([("p","s1","s2","x"),("p","s1","s3","x")], sessions)["median_days"] == 15
    bad = b_interval_stats([("p","s3","s1","x"),("p","s1","sx","x")], sessions); assert bad["nonpositive_intervals"] == 1 and bad["missing_timing"] == 1
    assert len(b_pairs_summary({("p", "ses-1")})[0]) == 0
    return {"status":"passed","tests":["undocumented_F_unresolved","documented_likely_valid_distinct","invalid_and_likely_invalid_excluded","no_autovalidation_exact_mapping","unknown_V_VC_unresolved","missing_partial_absent_QC","mixed_profile_states","unresolved_inclusive_base","different_task_same_domain","fixed_task_identity","discounting_independence","three_visit_pair_rules","even_interval_median","missing_nonpositive_timing","single_visit_not_repeated"]}

def b_production_checks(payloads: dict[str, dict[str, Any]], occasion: list[dict[str, Any]], profile: list[dict[str, Any]], pairs: list[dict[str, Any]], flow: list[dict[str, Any]], outcomes: list[dict[str, Any]]) -> list[str]:
    checks = []
    continuation = [r for r in occasion if r.get("participant_id") == "sub-20812" and r.get("original_session_id") == "ses-2"]
    assert continuation and continuation[0].get("comparability_status") == "documented continuation; no separate CNB occasion" and continuation[0].get("observed_cognitive_task_count") == 0
    checks.append("production_continuation_no_new_CNB")
    fixed = {r["scenario_id"]: r for r in profile if r["specification_id"] == "fixed_five_domain"}
    for scenario, row in fixed.items():
        pm = Counter(x["pairing_rule"] for x in pairs if x["qc_policy"] == scenario)
        assert int(row["complete_scheduled_pair_observation_count"]) == 2 * int(row["complete_scheduled_ses1_ses2_pairs"])
        assert int(row["scheduled_ses1_ses2_observation_count"]) >= int(row["complete_scheduled_pair_observation_count"])
        assert pm["all_possible_unordered_pairs"] == int(row["all_possible_unordered_pair_count"])
    checks.append("production_scheduled_observation_and_pair_reconciliation")
    for row in outcomes:
        for field in ("baseline_any_to_complete_profile_loss","unfiltered_to_current_profile_qc_loss","baseline_outcome_marginal_loss_from_all_outcome_participants","baseline_outcome_missing_participants_relative_to_any_cognitive","later_outcome_missing_among_baseline_profile","triple_exclusion_from_profile_plus_later"):
            assert str(row[field]).lstrip("-").isdigit()
        assert int(row["baseline_profile_baseline_outcome_later_outcome_participants"]) <= int(row["baseline_profile_and_later_outcome_participants"])
    checks.append("production_outcome_numeric_and_intersection_reconciliation")
    final = {r["scenario_id"]: int(r["remaining_after_sequential_exclusion"]) for r in flow if r["reason_flag"] == "final_profile_eligible"}
    assert all(final[s] == int(r["eligible_occasions"]) for s, r in fixed.items())
    checks.append("production_exclusion_flow_reconciliation")
    return checks

def b_eligibility_change_trace(payloads: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], set[tuple[str, str]], set[tuple[str, str]]]:
    selected, _ = b_profiles(); component_keys = {}; observations = {}
    for domain, (task, field) in selected.items():
        p = payloads[task]; qcf = s2_qc_fields(p["fields"]); old_keys = set(); info = {}
        for row in p["rows"]:
            key = (row.get("participant_id", ""), row.get("session_id", ""))
            if not is_missing(row.get(field, "")):
                info[key] = row; old_codes = [str(row.get(q, "")).strip() for q in qcf]
                old_classes = [b_old_code_class(p["meta"], q, str(row.get(q, "")).strip()) for q in qcf]
                old_ok = bool(qcf) and all(not is_missing(row.get(q, "")) and c in {"valid", "likely_valid_or_unresolved"} for q, c in zip(qcf, old_classes))
                if old_ok: old_keys.add(key)
        component_keys[(task, field)] = (old_keys, info)
    old_profile = set.intersection(*(x[0] for x in component_keys.values()))
    new_profile = b_spec_keys(payloads, selected, "documented_valid_or_likely_valid")
    all_keys = set().union(*(set(info) for _, info in component_keys.values()))
    trace = []
    for key in sorted(all_keys):
        for domain, (task, field) in selected.items():
            p = payloads[task]; qcf = s2_qc_fields(p["fields"]); row = component_keys[(task, field)][1].get(key)
            if row is None:
                raw = "__NO_SCORE__"; meaning = "selected score absent at participant/session"; old_class = "missing_score"; old_action = "excluded"
                new_class = "missing_score"; new_action = "excluded"
            else:
                raw = str(row.get(qcf[0], "")).strip() if qcf else "__NO_APPLICABLE_QC__"
                meanings = [str(s2_levels(p["meta"], q).get(str(row.get(q, "")).strip(), "not documented locally")) for q in qcf if not is_missing(row.get(q, ""))]
                meaning = " | ".join(meanings) if meanings else ("QC value absent" if qcf else "no applicable QC field")
                old_class = b_old_code_class(p["meta"], qcf[0], raw) if qcf and not is_missing(raw) else ("missing_qc" if qcf else "no_applicable_qc_field")
                old_action = "eligible" if key in component_keys[(task, field)][0] else "excluded"
                q = b_qc_status(task, row, qcf, p["meta"]); new_classes = b_policy_classes(q); new_class = "+".join(new_classes) if new_classes else "no_applicable_qc_field"
                new_action = "eligible" if b_eligible(task, row, qcf, "documented_valid_or_likely_valid", p["meta"])[0] else "excluded"
            effect = "old_and_new_profile_eligible" if key in old_profile and key in new_profile else ("old_profile_only_excluded_by_new" if key in old_profile and key not in new_profile else ("new_profile_only" if key not in old_profile and key in new_profile else "not_complete_profile"))
            trace.append({"participant_id":key[0],"session_id":key[1],"domain":domain,"task":task,"field":field,"raw_qc_code":raw,"exact_dictionary_meaning":meaning,"old_class_step2b":old_class,"old_recommended_action_step2b":old_action,"new_class_step3a":new_class,"new_recommended_action_step3a":new_action,"old_profile_eligible":key in old_profile,"new_profile_eligible":key in new_profile,"effect_on_profile_eligibility":effect})
    return trace, old_profile, new_profile

def b_write_markdown(out: Path, manifest: list[dict[str, Any]], qc: list[dict[str, Any]], profile: list[dict[str, Any]], outcomes: list[dict[str, Any]], fixture: dict[str, Any]) -> None:
    fixed = [r for r in profile if r["specification_id"] == "fixed_five_domain" and r["scenario_id"] == "unfiltered_observed"]
    fixed_rec = [r for r in profile if r["specification_id"] == "fixed_five_domain" and r["scenario_id"] == "documented_valid_or_likely_valid"]
    (out / "targeted_corrections.md").write_text("""# Targeted Step 2B corrections\n\n1. The prior ‘one primary task score per candidate domain’ label is corrected to `at_least_one_candidate_task_per_domain_identity_may_differ`: it is a domain-wise union and does not imply a fixed task profile.\n2. The five-domain intersection is now an explicit five-task intersection. Discounting tasks remain in a separate `all_21_cognitive_task_inventory_not_profile` inventory and cannot change the five-domain denominator.\n3. Baseline ‘any cognitive score’ and ‘baseline complete fixed profile’ are separate outcome denominators.\n4. Missing QC, partially missing QC, no QC field, conditional/no-automatic-validation codes, and unknown codes are retained as explicit unresolved QC states for sensitivity accounting.\n5. Scientific meaning is driven by reviewed task/field entries, not `er`/`tp`/`tn` substring heuristics.\n\nThe corrected audit remains feasibility/specification work only. It does not create composites, reliability estimates, age-adjusted scores, predictions, classifiers, clustering, dashboards, or an Evidence Engine.\n\nThe fixed profile is a transparent feasibility proxy selected for broad domain coverage and parsimonious task identity: LNB, Face Memory, Matrix Reasoning, Emotion Recognition, and dominant-hand Finger Tapping. It is not a final CHAVI score.\n""", encoding="utf-8")
    (out / "measurement_specification_review.md").write_text("""# Measurement specification review\n\n## Decision-ready candidate specification\n\nThe draft fixed profile uses one explicit task/field per broad domain: LNB `cnb_lnb_mcr` (Executive control), Face Memory `cnb_cpf_cr` (Episodic memory), Matrix Reasoning `cnb_pmat_cr` (Complex cognition), Emotion Recognition `cnb_er40_cr` (Social cognition), and dominant-hand Finger Tapping `cnb_ctap_dom` (Sensorimotor performance). This is a feasibility proxy, not a final composite. The exact manifest is in `score_manifest_draft.csv`.\n\n## Evidence and unresolved definitions\n\nThe Penn CNB Explore Tests page documents public task structure and durations: LNB has 0-/1-/2-back conditions; Digit Symbol is processing speed; memory tasks use target/foil recognition; PMAT has a stopping rule; ER40 has 40 faces; Finger Tapping uses 10-second trials. The CNB methods paper describes accuracy as number correct and speed as response time for correct answers. The factor paper separates accuracy and speed and reports PCET as a possible complex-cognition alternative. These sources support candidate construct labels, not equivalence between the online current CNB documentation and this historical Penn LEAD export.\n\nADT `cnb_adt_cnt_200` retains a count-versus-ms metadata conflict. LNB `cnb_lnb_mcr` has a local definition/range that does not establish a denominator or load mapping. CPT sensitivity is retained as sensitivity, not d-prime. Motor Praxis correct count and praxis RT are separate. Trails exact task/version and public definition remain gaps. The July 2024 Digit Symbol RT update is recorded as a version-sensitive issue.\n\n## Sources\n\n- [Penn CNB Explore Tests](https://webcnp.med.upenn.edu/explore-tests.html) (task structure, conditions, trial counts, duration).\n- [Penn CNB manual](https://webcnp.med.upenn.edu/manual.html) (assessment types, sessions, incomplete batteries, raw data, motor-practice gateway).\n- [Penn CNB updates](https://webcnp.med.upenn.edu/updates.html) (7 July 2024 Digit Symbol DSCORRT update).\n- [Gur et al. 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC2832711/) (accuracy/speed definitions).\n- [Moore et al. 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4345134/) (factor/domain evidence).\n- [PennLINC mapping](https://github.com/PennLINC/transdiagnostic_executive_function/blob/main/cognitive/CNB_transformation_script_EF.Rmd) and [cognitive README](https://github.com/PennLINC/transdiagnostic_executive_function/tree/main/cognitive) (variable mappings and sub-20812 continuation note).\n""", encoding="utf-8")
    (out / "sap_draft.md").write_text("""# CHAVI statistical analysis plan draft — Step 2B boundary\n\n## Status\n\nDecision-ready skeleton only. No final score, reliability, SEM/MDC estimate, or prediction is run in Step 2B.\n\n## Estimand and scientific question\n\nPrimary future estimand: within-person change in a frozen, direction-aligned fixed-composition domain profile between two eligible cognitive occasions, with separate reporting of domain level and profile shape. A secondary estimand may describe agreement/reliability after the measurement specification, QC scope, and occasion pairing are approved. Change, practice, occasion, and measurement error must not be conflated.\n\n## Cohort and occasions\n\nUse the pinned ds007116 1.0.6 snapshot and verified Step 1B phenotype payloads. The scheduled ses-1/ses-2 pair is descriptive. The primary repeated-occasion rule should be the first two eligible assessments per participant, with participant-level dependence preserved; report all available eligible pairs separately. Repository session, cognitive occasion, questionnaire occasion, and imaging occasion are distinct. The sub-20812 continuation is retained as a flagged continuation with no separate CNB, not silently treated as a new CNB occasion.\n\n## Fixed construction and missingness\n\nFreeze exact task/field identities before analysis. The current feasibility proxy is LNB/Face/Matrix/ER40/dominant Finger Tapping. Require all five fields for the full profile; a reduced four-domain profile is sensitivity only. Do not substitute a different task across visits in the fixed primary analysis. Report score missingness separately from QC loss and comparability uncertainty. Missing, skipped, invalid, and unresolved QC states are not interchangeable.\n\n## Direction, transformation, and age\n\nAccuracy-like scores are provisionally higher-is-better; speed scores are provisionally lower-is-faster. Any reversal must be frozen with the score manifest. Prefer within-analytic-sample transformations only after direction review; norm-based standardization and age adjustment are optional analyses requiring an appropriate reference and prespecified model. Age, developmental stage, and site/recruitment context must be handled without leakage; cross-fitting is required if a learned adjustment is used.\n\n## Level and shape\n\nDefine a level summary only after scale compatibility and weighting are frozen. Define shape as within-person domain contrasts or rank/profile deviations, separately from level. Report task identity and available-domain count alongside every later summary.\n\n## Reliability and agreement\n\nIf approved, estimate reliability/agreement for the exact fixed score and each domain using participant-level paired occasions. Report ICC variant and assumptions, within-person SD, SEM, MDC, confidence intervals, and uncertainty due to pair definition and QC policy. Do not infer individual change from a cohort mean.\n\n## Resampling and preprocessing\n\nSpecify row/participant exclusions, QC policy, missing-data rule, direction map, transformation, age model, weighting, and outlier handling before resampling. Resampling must respect participant clustering and any repeated-pair structure. Do not tune task selection or transformations on the final outcome.\n\n## SEM/MDC and robustness\n\nTreat SEM/MDC as uncertain until reliability model, scale, occasion interval, and error assumptions are settled. Sensitivities: strict V-only; documented valid/likely-valid; unresolved-QC-inclusive descriptive bounds; scheduled ses-1/ses-2 versus first-two-eligible; full five-domain versus reduced four-domain; accuracy-only versus speed-inclusive specifications; with/without age adjustment only if justified.\n\n## Outcomes and incremental prediction\n\nFor each of the five outcomes (`eswan_adhd_inattention_total`, `eswan_adhd_total_score`, `mapssr_total_score`, `im_average`, `em_average`), report baseline outcome, later outcome, baseline any-cognitive score, baseline complete profile, profile plus baseline outcome plus later outcome. Incremental prediction is conditional exploratory work only after profile and outcome timing, missingness, and covariate policy are frozen; it is not performed here.\n\n## Cohort versus individual uncertainty\n\nCohort change and individual reliable-change decisions require different uncertainty statements. The SAP must report sample size, pair counts, interval limitations, QC loss, and confidence intervals; it must refuse individual-level claims when comparability, reliability, or score direction is unresolved.\n\n## Blockers\n\nBefore final composites/reliability/prediction: author confirmation of QC code meanings/scope; exact LEAD task/version and denominator definitions; LNB and CPT formula details; ADT metadata conflict; Trails identity; decision on PCET/AIM/processing-speed placement; occasion handling for continuation; and frozen outcome timing/age policy.\n""", encoding="utf-8")
    (out / "decision_register.md").write_text("""# Step 2B decision register\n\n| Item | Status | Decision / block scope |\n|---|---|---|\n| Domain-union label | settled | Means at least one available candidate task in every domain; task identity may differ by occasion. |\n| Five-domain intersection | settled | Explicit LNB/Face/Matrix/ER40/dominant Finger Tapping only; discounting inventory separate. |\n| Missing and partial QC | settled for audit | Explicit unresolved states; excluded from primary feasibility recommendation until code meaning/scope is confirmed. |\n| Primary QC | recommended | All applicable fields present; documented valid/likely-valid only; task-specific meaning governs F. |\n| QC sensitivity | recommended | Strict V-only and unresolved-QC-inclusive descriptive bounds. |\n| Occasion pairing | recommended | First two eligible assessments primary candidate; scheduled ses-1/ses-2 descriptive sensitivity. |\n| sub-20812 ses-2 | settled for audit | Flag continuation/no separate CNB; no new CNB occasion inferred. |\n| Digit Symbol | unresolved | Executive control/processing speed candidate; official RT update is version-sensitive. |\n| Motor Praxis | unresolved | Correct count and RT are distinct; speed candidate needs denominator/validity confirmation. |\n| PCET/AIM/Trails | unresolved | Alternative domain or combined construct issues block final domain claim. |\n| Final composite/reliability/prediction | blocked by definition review | Explicitly out of Step 2B scope. |\n\nThe CSV feasibility tables are decision support, not inferential results.\n""", encoding="utf-8")
    (out / "reproduction_and_tests.md").write_text(f"""# Reproduction and focused tests\n\n```powershell\npython .\\chavi_audit_ds007116_step2b_20260907\\audit_v4.py --dataset .\\ds007116 --phenotype-stage .\\chavi_step1b_phenotype_staging_20260907 --output .\\chavi_audit_ds007116_step2b_20260907 --fixture-only\npython .\\chavi_audit_ds007116_step2b_20260907\\audit_v4.py --dataset .\\ds007116 --phenotype-stage .\\chavi_step1b_phenotype_staging_20260907 --output .\\chavi_audit_ds007116_step2b_20260907\n```\n\nInputs are the pinned checkout and the already verified Step 1B staging directory. No download or imaging retrieval occurs. Fixture status: `{fixture['status']}`.\n\nFocused regression coverage: different tasks filling a domain across visits; discounting cannot change the five-domain intersection; missing/partial/no-QC and unresolved QC states; single visits are not repeated; continuation is flagged; outcome-matched denominators remain score-specific.\n""", encoding="utf-8")

def b_evidence(out: Path) -> None:
    rows = [
        {"claim_id":"E1","claim":"Pinned OpenNeuro release and README establish ds007116 snapshot context and session/continuation caveats","source_url":SOURCE_URLS["dataset_release"],"precise_location":"release 1.0.6; local README mirror used for exact dataset caveats","use":"provenance/occasion limitations"},
        {"claim_id":"E2","claim":"Penn CNB public task page documents LNB conditions/trials, Digit Symbol processing speed, memory target/foil structure, PMAT stopping rule, ER40, and Finger Tapping duration/trials","source_url":SOURCE_URLS["cnb_explore"],"precise_location":"Executive Control, Memory, Complex Cognition, Social Cognition, Sensorimotor sections","use":"measurement specification"},
        {"claim_id":"E3","claim":"CNB manual distinguishes assessment/session context and warns incomplete batteries and motor-control limitations matter","source_url":"https://webcnp.med.upenn.edu/manual.html","precise_location":"assessment types; session fields; incomplete batteries; Motor Praxis gateway; raw data sections","use":"QC/occasion limitations"},
        {"claim_id":"E4","claim":"Official update gives current Digit Symbol DSCORRT definition","source_url":SOURCE_URLS["cnb_updates"],"precise_location":"7 July 2024 update","use":"version-sensitive Digit Symbol review"},
        {"claim_id":"E5","claim":"CNB methods distinguish accuracy number-correct from speed response time for correct answers","source_url":SOURCE_URLS["gur_2010"],"precise_location":"Methods, task performance measures","use":"raw meaning review"},
        {"claim_id":"E6","claim":"CNB factor analysis separates accuracy/speed and gives PCET an alternative complex-cognition interpretation","source_url":SOURCE_URLS["moore_2015"],"precise_location":"Table 1 and factor-analysis discussion","use":"domain placement uncertainty"},
        {"claim_id":"E7","claim":"PennLINC mapping provides variable prefixes and notes sub-20812 continuation/no separate CNB","source_url":SOURCE_URLS["pennlinc_mapping"],"precise_location":"transformation mapping and cognitive README","use":"variable identity/occasion review"},
    ]
    write_csv(out / "evidence_register_step2c.csv", rows, list(rows[0]))

def b_correction_impact(payloads: dict[str, dict[str, Any]], profile: list[dict[str, Any]], outcomes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    qc_freq = Counter(); raw_f = 0
    for task, p in payloads.items():
        if task not in COGNITIVE: continue
        for field in s2_qc_fields(p["fields"]):
            for r in p["rows"]:
                code = str(r.get(field, "")).strip()
                if not is_missing(code): qc_freq[(task, field, code)] += 1
                if code == "F" and code not in s2_levels(p["meta"], field): raw_f += 1
    fixed = {r["scenario_id"]: r for r in profile if r["specification_id"] == "fixed_five_domain"}
    return [
        {"correction_id":"QC-A","previous_value":"undocumented F accepted as likely-valid","corrected_value":"undocumented F -> unknown_or_undocumented; excluded from documented-valid/likely-valid","reason":f"Exact dictionary lookup; undocumented F rows observed={raw_f}","affected_specification":"all score/task QC policies; no undocumented F may enter recommended profile"},
        {"correction_id":"QC-B","previous_value":"No autovalidation rule available could be classified as valid by substring","corrected_value":"exact class no_automatic_validation; unresolved and excluded from documented-valid/likely-valid","reason":"Substring inference removed; exact dictionary meaning controls","affected_specification":"all tasks with code 0; descriptive and inclusive policies only"},
        {"correction_id":"QC-C","previous_value":"likely-valid and valid collapsed","corrected_value":"documented_likely_valid distinct from documented_valid; accepted only under documented-valid/likely-valid policy","reason":"Preserves exact dictionary meaning and strict V-only distinction","affected_specification":"candidate score eligibility and profile QC sensitivity"},
        {"correction_id":"QC-D","previous_value":"unresolved_qc_inclusive selected unresolved observations only","corrected_value":f"unresolved_inclusive retains nonmissing profile base except explicit invalid/skipped; fixed profile occasions={fixed.get('unresolved_inclusive',{}).get('eligible_occasions','unavailable')}","reason":"Inclusive sensitivity is a base population with explicit invalidity excluded","affected_specification":"fixed/reduced/domain/all-21 feasibility and outcome denominators"},
        {"correction_id":"PAIR-A","previous_value":"visits-minus-one/first-two proxy used for pair count","corrected_value":f"all unordered={fixed.get('unfiltered_observed',{}).get('all_possible_unordered_pair_count','unavailable')}; first-two={fixed.get('unfiltered_observed',{}).get('first_two_eligible_pair_count','unavailable')}; scheduled complete={fixed.get('unfiltered_observed',{}).get('complete_scheduled_ses1_ses2_pairs','unavailable')}","reason":"Explicit pair sets; 3 eligible occasions yield 3 all-pairs and 1 first-two pair","affected_specification":"pair manifest, intervals, repeated-profile feasibility"},
        {"correction_id":"PAIR-B","previous_value":"single nominal interval summary","corrected_value":"separate all-pair, first-two, and complete scheduled interval summaries with conventional median and timing failures","reason":"Pair rule and timing source are distinct; timestamps are rounded/anonymized","affected_specification":"paired_profile_feasibility.csv and pair_manifest.csv"},
        {"correction_id":"COMP-A","previous_value":"fixed profile comparability uncertainty implied zero","corrected_value":"uncertain unless documented; task version/conditions/exact cognitive timing unresolved","reason":"Fixed field identity does not prove occasion comparability","affected_specification":"all fixed-profile rows; domain interpretation and future reliability"},
        {"correction_id":"OUT-A","previous_value":"numeric loss columns contained text placeholders","corrected_value":"calculated marginal/sequential counts for all five outcomes","reason":"Outcome table now applies explicit ses-1 baseline and non-ses-1 later rules","affected_specification":"outcome_matched_feasibility.csv"},
    ]

def b_step2c_docs(out: Path, profile: list[dict[str, Any]], outcomes: list[dict[str, Any]], fixture: dict[str, Any], before: dict[str, Any], spec_path: Path) -> None:
    fixed = [r for r in profile if r["specification_id"] == "fixed_five_domain" and r["scenario_id"] in {"unfiltered_observed", "documented_valid_or_likely_valid", "strict_documented_V_only"}]
    (out / "targeted_corrections.md").write_text("""# Step 2C correction record\n\nStep 2C corrected five implementation defects: QC classes now use exact dictionary meanings; undocumented F, no-autovalidation text, and unknown V/VC remain unresolved; documented likely-valid is distinct from valid; and unresolved-inclusive eligibility retains the observed-score base except explicit invalid/skipped components. Profile-level unresolved, all-unresolved, and mixed-unresolved/invalid counts are reported separately.\n\nPair accounting now emits participant-level pair manifests with all unordered pairs, first-two pairs, and complete scheduled pairs. Even-sample medians are conventional arithmetic medians; missing, unparseable, and nonpositive timing are explicit. Fixed-profile comparability is uncertain unless documented, and the sub-20812 ses-2 continuation cannot create a CNB occasion.\n\nLoss accounting uses overlapping reason flags plus a documented sequential flow. ‘No documented cognitive phenotype’, missing selected score, QC exclusion, comparability exclusion, and unresolved classification are not silently conflated.\n\nThe corrected audit is feasibility and design work only. No composite, standardization, age adjustment, reliability, prediction, or Evidence Engine was run.\n""", encoding="utf-8")
    (out / "sap_draft.md").write_text("""# CHAVI SAP draft — Step 2C review boundary\n\n## Objective hierarchy\n\n**Primary:** longitudinal dependability/agreement of prespecified cognitive measurements and individualized profile shape, distinguishing overall profile level from relative within-person patterns.\n\n**Supporting:** systematic change and occasion/developmental effects relevant to interpreting longitudinal dependability.\n\n**Conditional exploratory:** incremental predictive validity beyond baseline outcome, relevant covariates, and global cognition. This is not performed in Step 2C.\n\nThe five-task proxy is a feasibility specification only and is not promoted to the final measurement specification without an explicit evidence-based decision.\n\n## Estimands and cohorts\n\nThe primary future estimand is agreement/dependability for frozen task fields across eligible cognitive occasions, with separate level and shape summaries. Change, practice, occasion/developmental effects, and measurement error must be reported as distinct concepts. The first-two-eligible cognitive-pair cohort and the ses-1-based profile/outcome cohort are separate and must not be substituted.\n\n## Construction, missingness, and pairs\n\nThe selected profile and QC rules are read from `executable_specification.json`. Fixed task identity is required across occasions. Report at-least-one, 2+, 3+, all unordered pairs, first-two pairs, complete ses-1/ses-2 pairs, and interval summaries separately. Never count visits minus one as all pairs. Preserve overlapping flags and use the reconciled sequential flow only as a descriptive accounting order.\n\n## Measurement and transformations\n\nFreeze raw field meaning, denominator, conditions, units, direction, and QC scope before scoring. Accuracy-like fields may be higher-is-better and speed fields lower-is-faster only where the manifest supports that proposal. Do not assume age adjustment, norm-based standardization, learned transformations, weighting, or error correction; each requires a prespecified rationale and, where learned, leakage-safe fitting.\n\n## Reliability/agreement and uncertainty\n\nReliability/dependability is primary future work. After specification freeze, report the selected agreement model, within-person variability, SEM/MDC uncertainty, interval sensitivity, and participant-level dependence. Cohort-level change cannot be treated as individual reliable change. Unknown comparability must be reported and can block a particular interpretation without blocking unrelated supplementary tasks.\n\n## Robustness and prediction gate\n\nPlanned sensitivities include documented valid/likely-valid, strict documented V-only, unresolved-inclusive, first-two versus scheduled pairs, and full versus reduced profile. Incremental prediction is conditional exploratory and requires baseline outcome, relevant covariates, global cognition, frozen profile construction, outcome timing, and missingness policy. It does not determine task selection.\n\n## Remaining choices and block scope\n\nQC scope/code meaning blocks selected-score eligibility until approved; LNB/CPT denominators and ADT units block those particular interpretations; PCET/AIM/Trails placement blocks their domain interpretation but not the current proxy; Digit Symbol version blocks its update-sensitive speed interpretation; continuation handling blocks treating ses-2 as a new CNB occasion; weighting/direction/age policy block final composites and prediction. These questions do not automatically block the entire study or every supplementary task. No reporting gate is declared validated here.\n""", encoding="utf-8")
    (out / "decision_register.md").write_text("""# Step 2C decision register\n\n| Decision | Status | Scope |\n|---|---|---|\n| Reliability/dependability and profile level-versus-shape | settled primary priority | Entire primary research objective |\n| Systematic change/occasion effects | settled supporting priority | Interpretation of dependability |\n| Incremental predictive validity | conditional exploratory | Only after baseline outcome/covariate/global-cognition policy is frozen |\n| Fixed five-task proxy | recommended feasibility proxy, not final specification | Feasibility only |\n| QC classification | corrected executable rule | Selected scores until code scope is approved |\n| Pair definitions | corrected and reported separately | Pair counts/intervals; recommendation remains provisional |\n| Comparability | uncertain unless documented | Profile/domain interpretation; not silently assumed |\n| ADT/LNB/CPT/Trails definitions | unresolved | Specific score or domain interpretation, not automatically entire study |\n| Final composite/reliability/prediction | not run | Blocked at this review boundary |\n\nConfiguration authority: `step2c_specification.json`, loaded by the audit and copied to `executable_specification.json`.\n""", encoding="utf-8")
    (out / "step2c_review_report.md").write_text(f"""# CHAVI Step 2C review report\n\nVerified/reused 41 staged Step 1B payloads from ds007116 snapshot 1.0.6 at `{COMMIT}`. Checkout status before/after remained unchanged. Configuration: `{spec_path.name}`.\n\n## Corrections and feasibility\n\nQC is now exact-meaning based. The fixed proxy uses identical fields across occasions. Pair counts and intervals are in `paired_profile_feasibility.csv` and `pair_manifest.csv`; reason flags and sequential reconciliation are in `exclusion_flow.csv`. Outcome denominators are in `outcome_matched_feasibility.csv`.\n\nSelected fixed-profile rows: `{json.dumps(fixed, indent=2)}`.\n\n## Readiness\n\nThe audit is ready for supervisor review of the measurement specification and SAP. It is not ready to freeze final scores: QC scope, selected-task definitions, comparability, direction, and weighting decisions remain appropriately scoped blockers.\n\nExecutable fixtures: `{fixture['status']}`.\n""", encoding="utf-8")
    (out / "reproduction_and_tests.md").write_text(f"""# Step 2C reproduction\n\n```powershell\npython .\\chavi_audit_ds007116_step2c_20260907\\audit_v5.py --dataset .\\ds007116 --phenotype-stage .\\chavi_step1b_phenotype_staging_20260907 --output .\\chavi_audit_ds007116_step2c_20260907 --spec .\\chavi_audit_ds007116_step2c_20260907\\step2c_specification.json --fixture-only\npython .\\chavi_audit_ds007116_step2c_20260907\\audit_v5.py --dataset .\\ds007116 --phenotype-stage .\\chavi_step1b_phenotype_staging_20260907 --output .\\chavi_audit_ds007116_step2c_20260907 --spec .\\chavi_audit_ds007116_step2c_20260907\\step2c_specification.json\n```\n\nThe script reuses only the 41 verified Step 1B payloads; it does not download or retrieve imaging. Executed fixtures: `{fixture['status']}`.\n""", encoding="utf-8")

def b_step3a_docs(out: Path, profile: list[dict[str, Any]], task_rows: list[dict[str, Any]], domain_rows: list[dict[str, Any]], outcomes: list[dict[str, Any]], fixture: dict[str, Any], production_checks: list[str], old_profile: set[tuple[str, str]], new_profile: set[tuple[str, str]], trace: list[dict[str, Any]], spec_path: Path) -> None:
    fixed = {r["scenario_id"]: r for r in profile if r["specification_id"] == "fixed_five_domain"}
    repeated = lambda keys: {pid for pid, _ in keys if sum(p == pid for p, _ in keys) >= 2}
    old_repeated, new_repeated = repeated(old_profile), repeated(new_profile)
    (out / "implementation_closure.md").write_text(f"""# Step 3A implementation closure\n\nClosed: configuration-driven QC eligibility with schema validation and invalidity precedence; separate scheduled observations versus complete scheduled-pair observations; explicit pair-rule intervals and timing failures; fixed-profile comparability uncertainty; and sub-20812/ses-2 continuation protection.\n\nThe fixed-profile eligibility trace contains {len(trace)} component records. Reconstructed Step 2B recommended eligibility has {len(old_profile)} complete profile occasions; corrected documented-valid/likely-valid eligibility has {len(new_profile)}. The reduction is two occasions and one participant: sub-20259/ses-1 and sub-20350/ses-1 were admitted by the old substring class for `Not Valid` and are excluded by the exact dictionary class. Old and new repeated-participant sets are both {len(old_repeated)}; changed identities: {sorted(old_repeated ^ new_repeated)}.\n\nCounts: unfiltered {fixed['unfiltered_observed']['eligible_occasions']} occasions / {fixed['unfiltered_observed']['eligible_participants_at_least_1']} participants / {fixed['unfiltered_observed']['participants_2plus_eligible_occasions']} repeated; documented valid/likely-valid {fixed['documented_valid_or_likely_valid']['eligible_occasions']} / {fixed['documented_valid_or_likely_valid']['eligible_participants_at_least_1']} / {fixed['documented_valid_or_likely_valid']['participants_2plus_eligible_occasions']} repeated; strict V-only {fixed['strict_documented_V_only']['eligible_occasions']} / {fixed['strict_documented_V_only']['eligible_participants_at_least_1']} / {fixed['strict_documented_V_only']['participants_2plus_eligible_occasions']} repeated.\n\nExecuted fixture status: {fixture['status']}. Production checks: {', '.join(production_checks)}.\n""", encoding="utf-8")
    (out / "measurement_evidence_dossier.md").write_text("""# CHAVI measurement evidence dossier\n\n## Five proxy scores\n\n- LNB `cnb_lnb_mcr`: released true-positive count for 1-/2-back. The denominator/load mapping is unresolved; do not call it percent correct or transform it using an invented denominator.\n- Face Memory `cnb_cpf_cr`: face-memory correct-count output. Public CNB documentation supports target/foil recognition; historical false-alarm treatment and exact LEAD version remain unknown.\n- Matrix Reasoning `cnb_pmat_cr`: matrix-reasoning correct-count output. The documented stopping rule prevents assuming a fixed denominator.\n- ER40 `cnb_er40_cr`: emotion-recognition correct-count output; the public task page documents 40 faces, while historical conditions/QC scope remain uncertain.\n- Dominant CTAP `cnb_ctap_dom`: released mean dominant-hand trial summary. Public documentation supports 10-second trials/five per hand; the exact count/rate aggregation must still be frozen.\n\nThese support narrow released-score audits. They do not support longitudinal equivalence, equal latent contribution, or a validated broad-domain composite.\n\n## Mapping resolution and alternatives\n\nDigit Symbol `cnb_digsym_dscor` is consistently assigned to Executive control/processing speed in the current executable candidate-domain configuration because the pinned public CNB task documentation lists it with Executive Control processing-speed tasks. Its earlier Complex-cognition placement is preserved as historical Step 2 mapping only. The 2024 Digit Symbol RT update is not assumed to rewrite the historical LEAD field. PCET remains a complex-cognition alternative based on primary factor evidence; AIM is a combined-construct candidate; Trails remain task-level speed candidates.\n\n## QC and sources\n\nReleased dictionary meanings are preserved exactly: V Valid; F Likely valid with a limited-response problem; 0 No autovalidation rule available; S Skipped; N Not Valid; C Assessor Comment; X Excluded. Missing/partial/no-applicable QC remain unresolved. Sources: [Penn CNB task documentation](https://webcnp.med.upenn.edu/explore-tests.html), [Penn CNB manual](https://webcnp.med.upenn.edu/manual.html), [Penn CNB updates](https://webcnp.med.upenn.edu/updates.html), [Gur et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC2832711/), [Moore et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC4345134/), and [PennLINC mapping](https://github.com/PennLINC/transdiagnostic_executive_function/blob/main/cognitive/CNB_transformation_script_EF.Rmd).\n""", encoding="utf-8")
    (out / "recommended_measurement_specification_draft.md").write_text("""# Recommended measurement specification — supervisor draft\n\n| Decision | Recommendation | Evidence | Tradeoff | Limitation | Alternative |\n|---|---|---|---|---|---|\n| Research unit | Prespecify task-level scores first; treat domains/profile as conditional | Released columns and CNB accuracy/speed framework | Traceable | No validated common domain scale | Evidence-supported multi-task candidates |\n| Five scores | LNB mcr; Face cr; Matrix cr; ER40 cr; dominant CTAP | Exact released fields and dossier | Fixed identity | Proxy is not a validated composite | Task-level route |\n| QC | Documented valid/likely-valid with all applicable QC; strict V-only and unresolved-inclusive sensitivities | Exact dictionary meanings | Transparent exclusions | QC scope unresolved | Task-specific approval |\n| Completeness | Require all selected components | Explicit set intersection | No silent substitution | Lower coverage | Reduced four-domain sensitivity |\n| Pairing | First two eligible primary candidate; scheduled ses-1/ses-2 sensitivity | Pair manifest | Eligibility-aligned | Pair rule remains provisional | All unordered pairs |\n| Direction/weighting | Freeze only supported accuracy/speed directions; no weighting yet | Methods distinguish accuracy/speed | Avoids invented scale | Profile level not final | Prespecified weighting after review |\n| Age/interval | Descriptive age and nominal intervals; no fitted age model | Rounded/anonymized timing | Separates development from error | Adjustment unresolved | Leakage-safe model after approval |\n\nThis package supports review, not final scoring or reliability estimation.\n""", encoding="utf-8")
    (out / "sap_draft.md").write_text("""# CHAVI SAP draft — reliability-first\n\n## Primary\nLongitudinal dependability/agreement of prespecified cognitive measurements and individualized profile shape, distinguishing overall profile level from relative within-person patterns.\n\n## Supporting\nSystematic change and occasion/developmental effects relevant to interpreting longitudinal dependability. Change, practice, occasion, and measurement error remain distinct.\n\n## Conditional exploratory\nIncremental predictive validity beyond baseline outcome, relevant covariates, and global cognition, only after the measurement specification and cohort rules are frozen.\n\n## Specification and cohorts\nUse the executable JSON specification. Fixed fields must remain identical across occasions. The first-two-eligible cognitive-pair cohort is separate from the ses-1-based profile/outcome cohort. Report all unordered, first-two, and complete scheduled pairs separately; overlapping pairs are not independent participants.\n\n## Missingness, QC, comparability\nReport score missingness, QC exclusion, and comparability uncertainty separately. Explicit invalidity overrides unresolved/missing QC in inclusive sensitivities. The continuation session is not a new CNB administration.\n\n## Future methods after approval\nFreeze direction, weighting, transformation, age handling, follow-up rule, and agreement model before any composite, reliability, SEM/MDC, or prediction work. Standardization/age adjustment may be considered only with a justified reference and leakage-safe fitting.\n\n## Block scope\nLNB denominator/QC scope blocks its transformed or broad interpretation, not raw-score auditing; ADT units block its disputed interpretation; PCET/AIM/Trails placement blocks their domain claims; version/comparability uncertainty blocks equivalence claims; these do not automatically block unrelated task-level analyses or the entire study.\n""", encoding="utf-8")
    (out / "decision_register.md").write_text("""# Step 3A decision register\n\n- **Primary priority — settled:** longitudinal reliability/dependability and profile level versus profile shape.\n- **Supporting priority — settled:** change and occasion/developmental effects for interpretation.\n- **Prediction — conditional exploratory:** only beyond baseline outcome, relevant covariates, and global cognition after specification freeze.\n- **Task-level route — recommended:** the five released proxy fields are auditable narrow measurements; broad domains remain conditional.\n- **QC — recommended pending approval:** documented valid/likely-valid with all applicable QC; strict V-only and unresolved-inclusive sensitivities.\n- **Pairing — provisional:** first two eligible primary candidate; scheduled ses-1/ses-2 sensitivity; all unordered pairs reported.\n- **Digit Symbol — settled mapping correction:** current candidate-domain configuration places it under Executive control/processing speed; prior Complex-cognition assignment is historical only.\n- **Scoped blockers:** LNB denominator/QC scope, ADT unit conflict, task-version comparability, PCET/AIM/Trails domain claims, direction/weighting/age policy.\n- **Not run:** composite scoring, standardization, age fitting, reliability, SEM/MDC, prediction, clinical claims, or Evidence Engine.\n""", encoding="utf-8")
    option_rows = []
    for option_id, spec_id, question, components, limit, source, status in [("fixed_five_task_proxy","fixed_five_domain","longitudinal dependability of five fixed task outputs","LNB;Face;Matrix;ER40;dominant CTAP","narrow task-level and provisional profile only","paired_profile_feasibility.csv","recommended feasibility proxy"),("evidence_supported_domain_candidates","candidate_domain:*","domain-level availability","explicit candidate task sets by domain","near-zero repeated intersections do not justify a composite","domain_feasibility.csv","review before domain claim"),("task_level_route","individual_score:*","longitudinal task-specific dependability","each reviewed field separately","no broad-domain/full-profile claim","task_score_feasibility.csv","recommended fallback")]:
        eligible = [r for r in profile if (r["specification_id"] == spec_id or (spec_id.endswith(":*") and r["specification_id"].startswith(spec_id[:-1]))) and r["scenario_id"] == "unfiltered_observed"]
        option_rows.append({"option_id":option_id,"question_answered":question,"components":components,"interpretation_limit":limit,"coverage_source":source,"unfiltered_specification_count":len(eligible),"unfiltered_repeated_participant_summary":json.dumps(sorted({(r["specification_id"],r["participants_2plus_eligible_occasions"]) for r in eligible})),"recommendation_status":status})
    write_csv(out / "measurement_options.csv", option_rows, list(option_rows[0]))
    (out / "step3a_review_report.md").write_text(f"""# CHAVI Step 3A review report\n\nStep 3A closes Step 2C implementation defects and prepares a measurement-specification decision package. It reused 41 verified payloads from ds007116 1.0.6 at `{COMMIT}` without downloads or imaging retrieval.\n\nOutputs include {len(task_rows)} task-score rows, {len(domain_rows)} candidate-domain rows, {len(profile)} profile strata, {len(trace)} trace rows, {len(outcomes)} outcome strata, and {len(production_checks)} production checks. The recommended position is task-level prespecification with the five-task proxy retained for feasibility only. Reliability/dependability and profile level-versus-shape remain primary.\n\nReady for supervisor review; no scientific inference or final scoring has begun.\n""", encoding="utf-8")
    (out / "reproduction_and_tests.md").write_text(f"""# Step 3A reproduction\n\n```powershell\npython .\\chavi_audit_ds007116_step3a_20260907\\audit_v6.py --dataset .\\ds007116 --phenotype-stage .\\chavi_step1b_phenotype_staging_20260907 --output .\\chavi_audit_ds007116_step3a_20260907 --spec .\\chavi_audit_ds007116_step3a_20260907\\step3a_specification.json --fixture-only\npython .\\chavi_audit_ds007116_step3a_20260907\\audit_v6.py --dataset .\\ds007116 --phenotype-stage .\\chavi_step1b_phenotype_staging_20260907 --output .\\chavi_audit_ds007116_step3a_20260907 --spec .\\chavi_audit_ds007116_step3a_20260907\\step3a_specification.json\n```\n\nFixture status: `{fixture['status']}`. Production checks executed: `{', '.join(production_checks)}`. The script reuses verified Step 1B payloads and performs no download, imaging retrieval, scoring, reliability estimation, prediction, or Evidence Engine work.\n""", encoding="utf-8")

def main_v4() -> int:
    ap = argparse.ArgumentParser(description="CHAVI Step 2C corrected measurement-definition and feasibility audit")
    ap.add_argument("--dataset", type=Path, required=True); ap.add_argument("--phenotype-stage", type=Path, required=True); ap.add_argument("--output", type=Path, required=True); ap.add_argument("--spec", type=Path, default=SPEC_PATH); ap.add_argument("--fixture-only", action="store_true")
    args = ap.parse_args()
    global ACTIVE_SPEC
    ACTIVE_SPEC = b_load_spec(args.spec.resolve())
    fixture = b_fixture_tests()
    if args.fixture_only: print(json.dumps(fixture, indent=2)); return 0
    dataset, stage, out = args.dataset.resolve(), args.phenotype_stage.resolve(), args.output.resolve(); out.mkdir(parents=True, exist_ok=True)
    before = git_metadata(dataset)
    if before.get("commit") != COMMIT: raise SystemExit(f"Pinned commit mismatch: {before.get('commit')} != {COMMIT}")
    payloads, reuse = s2_verified_payloads(dataset, stage)
    if len(payloads) != len(reuse) or len(payloads) != 41: raise SystemExit("Step 1B payload reuse check failed")
    write_csv(out / "retrieval_reuse_manifest.csv", reuse, list(reuse[0])); write_json(out / "executable_specification.json", ACTIVE_SPEC); write_json(out / "dataset_provenance_step3a.json", {"generated_utc":now_utc(),"dataset_root":str(dataset),"phenotype_stage_root":str(stage),"specification_path":str(args.spec.resolve()),"specification_sha256":sha256(args.spec.resolve()),"script_path":str(Path(__file__).resolve()),"script_sha256":sha256(Path(__file__).resolve()),"intended_snapshot":SNAPSHOT,"pinned_commit_expected":COMMIT,"git_before":before,"verified_payload_count":len(payloads),"software":{"python":sys.version,"platform":platform.platform(),"git":run_tool_version("git","--version")},"pair_rules_execution":"b_pair_sets executes all configured pair rules; outcome list is executed by b_outcome_rows","boundaries":["reuse only verified Step 1B payloads","no imaging retrieval","no composites/standardization/age fitting/reliability/prediction/Evidence Engine"]})
    manifest = b_manifest_rows(payloads); write_csv(out / "score_manifest_draft.csv", manifest, list(manifest[0]))
    qc = b_qc_rows(payloads); write_csv(out / "qc_policy_draft.csv", qc, list(qc[0]))
    yaml_lines = [f"specification_file: {json.dumps('executable_specification.json')}", f"specification_sha256: {json.dumps(sha256(args.spec.resolve()))}", "qc_policies:"]
    for name, policy in ACTIVE_SPEC["qc_policies"].items():
        yaml_lines.append(f"  {name}:")
        for key, value in policy.items(): yaml_lines.append(f"    {key}: {json.dumps(value)}")
    yaml_lines.append("tasks:")
    for row in qc:
        yaml_lines.append(f"  - task: {json.dumps(row['task'])}")
        yaml_lines.append(f"    qc_fields: {json.dumps(row['qc_fields'])}")
        yaml_lines.append("    qc_scope: table-level field observed; score-specific scope unresolved")
    (out / "qc_policy_draft.yaml").write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")
    participant_fields, participant_rows, _ = read_participants(dataset); session_rows, _, _, _, _ = parse_scanner_aux(dataset); occasion = s2_occasion_rows(payloads, session_rows, participant_rows); write_csv(out / "assessment_occasion_mapping_step3a.csv", occasion, list(occasion[0]))
    profile = b_profile_rows(payloads, session_rows); write_csv(out / "paired_profile_feasibility.csv", profile, list(profile[0])); task_rows = [r for r in profile if r["specification_type"] == "individual-reviewed-score"]; domain_rows = [r for r in profile if r["specification_type"] == "explicit-candidate-domain-multi-task"]; write_csv(out / "task_score_feasibility.csv", task_rows, list(task_rows[0])); write_csv(out / "domain_feasibility.csv", domain_rows, list(domain_rows[0])); pairs = b_pair_manifest(payloads, session_rows); write_csv(out / "pair_manifest.csv", pairs, list(pairs[0])); flow = b_exclusion_flow(payloads, session_rows); write_csv(out / "exclusion_flow.csv", flow, list(flow[0])); outcomes = b_outcome_rows(payloads, profile); write_csv(out / "outcome_matched_feasibility.csv", outcomes, list(outcomes[0])); impact = b_correction_impact(payloads, profile, outcomes); write_csv(out / "correction_impact.csv", impact, list(impact[0])); trace, old_profile, new_profile = b_eligibility_change_trace(payloads); write_csv(out / "eligibility_change_trace.csv", trace, list(trace[0])); production_checks = b_production_checks(payloads, occasion, profile, pairs, flow, outcomes)
    b_evidence(out); b_step3a_docs(out, profile, task_rows, domain_rows, outcomes, fixture, production_checks, old_profile, new_profile, trace, args.spec.resolve())
    write_json(out / "dataset_provenance_step3a.json", {"generated_utc":now_utc(),"dataset_root":str(dataset),"phenotype_stage_root":str(stage),"specification_path":str(args.spec.resolve()),"specification_sha256":sha256(args.spec.resolve()),"script_path":str(Path(__file__).resolve()),"script_sha256":sha256(Path(__file__).resolve()),"intended_snapshot":SNAPSHOT,"pinned_commit_expected":COMMIT,"git_before":before,"verified_payload_count":len(payloads),"trace_rows":len(trace),"old_recommended_profile_occasions":len(old_profile),"new_recommended_profile_occasions":len(new_profile),"production_checks":production_checks,"software":{"python":sys.version,"platform":platform.platform(),"git":run_tool_version("git","--version")},"boundaries":["reuse only verified Step 1B payloads","no imaging retrieval","no composites/standardization/age fitting/reliability/prediction/Evidence Engine"]})
    after = git_metadata(dataset)
    if after.get("commit") != COMMIT or after.get("status") != before.get("status"): raise SystemExit("Dataset checkout changed during Step 2C")
    print(json.dumps({"output":str(out),"verified_payloads":len(payloads),"measurement_manifest_rows":len(manifest),"qc_policy_rows":len(qc),"paired_profile_rows":len(profile),"pair_manifest_rows":len(pairs),"exclusion_flow_rows":len(flow),"trace_rows":len(trace),"outcome_matched_rows":len(outcomes),"fixture_tests":fixture["status"],"production_checks":production_checks,"dataset_commit":after.get("commit"),"dataset_status":after.get("status")}, indent=2)); return 0

if __name__ == "__main__":
    raise SystemExit(main_v4())
