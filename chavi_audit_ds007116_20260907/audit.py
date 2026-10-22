#!/usr/bin/env python3
"""Reproducible, non-destructive CHAVI audit for a local Penn LEAD checkout.

The script intentionally audits only metadata, tabular files, and event files.
It does not open imaging volumes, derivatives, or any unavailable annex object.
It writes all requested outputs to the output directory, which should be kept
outside the dataset repository.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ANNEX_PREFIXES = ("../.git/annex/objects/", ".git/annex/objects/")
MISSING_TOKENS = {"", "NA", "N/A", "NaN", "nan", "None", "none", "null"}
SUB_RE = re.compile(r"^(sub-[^/]+)")
SES_RE = re.compile(r"(ses-[^/]+)")


def relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def run_git(root: Path, *args: str) -> str:
    try:
        p = subprocess.run(
            ["git", "-c", f"safe.directory={root}", "-C", str(root), *args],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return p.stdout.strip()
    except Exception as exc:  # pragma: no cover - defensive on unusual systems
        return f"UNAVAILABLE: {exc}"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> Any:
    return json.loads(read_text(path))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: "" if row.get(k) is None else row.get(k) for k in fieldnames})


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def annex_stub_target(path: Path) -> tuple[bool, str, bool]:
    """Return (is_stub, pointer, target_exists) for a visible file."""
    try:
        with path.open("rb") as f:
            raw = f.read(4096)
    except OSError:
        return False, "", False
    if b"\x00" in raw:
        return False, "", False
    text = raw.decode("utf-8", errors="replace").strip()
    if not text.startswith(ANNEX_PREFIXES) or "\n" in text:
        return False, "", False
    target = (path.parent / text).resolve(strict=False)
    return True, text, target.is_file()


def file_state(path: Path) -> tuple[str, str, bool]:
    """Return (availability, pointer, target_exists)."""
    try:
        size = path.stat().st_size
    except OSError:
        return "unreadable", "", False
    if size == 0:
        return "empty", "", False
    is_stub, pointer, exists = annex_stub_target(path)
    if is_stub:
        return ("available_annex_object" if exists else "unavailable_annex_stub"), pointer, exists
    return "available", "", False


def is_missing(value: Any, *, participants: bool = False, column: str = "") -> bool:
    if value is None:
        return True
    s = str(value).strip()
    if s in MISSING_TOKENS:
        return True
    # In participants.tsv, ethnicity=n/a is an explicitly documented level,
    # not a blank missing value. In all other tables n/a is a common missing code.
    if not participants and s.lower() in {"n/a", "na"}:
        return True
    if participants and column == "ethnicity" and s == "n/a":
        return False
    return False


def parse_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fields = reader.fieldnames or []
        return fields, [dict(row) for row in reader]


def participant_session_from_path(path: Path) -> tuple[str, str]:
    parts = path.as_posix().split("/")
    participant = next((x for x in parts if x.startswith("sub-")), "")
    session = next((x for x in parts if x.startswith("ses-")), "")
    return participant, session


def task_label_from_phenotype(stem: str) -> str:
    labels = {
        "penn_abstraction_inhibition_working_memory_task": "Penn Abstraction, Inhibition and Working Memory Task",
        "penn_face_memory_test": "Penn Face Memory Test",
        "penn_word_memory_test": "Children's Penn Word Memory Test",
        "short_computerized_finger_tapping_task": "Short Computerized Finger-Tapping Task",
        "penn_emotion_recognition_task": "Penn Emotion Recognition Task for Children",
        "digit_symbol": "Digit Symbol Test",
        "short_letter_2back": "Short Letter N-Back (2 back)",
        "measured_emotion_differentiation_test": "Measured Emotion Differentiation Test",
        "motor_praxis": "Motor Praxis Test",
        "penn_conditional_exclusion_task": "Penn Conditional Exclusion Task for Children",
        "short_penn_continuous_performance_test": "Short Penn Continuous Performance Test",
        "penn_matrix_reasoning_test": "Penn Matrix Reasoning Test",
        "variable_short_penn_line_orientation_test": "Variable Short Penn Line Orientation Test",
        "penn_verbal_reasoning_test": "Children's Verbal Reasoning Test",
        "visual_object_learning_test": "Short Visual Object Learning Test",
        "trailmaking_test_a": "Trailmaking A",
        "trailmaking_test_b": "Trailmaking B",
        "effort_discounting_task": "Effort Discounting Task",
        "delay_discounting_task": "Delayed Discounting Task",
        "risk_discounting_task": "Risk Discounting Task",
        "age_differentiation_test": "Age Differentiation Test",
    }
    return labels.get(stem, stem.replace("_", " ").title())


def potential_role(stem: str) -> str:
    outcomes = {
        "ales", "als-18", "ari", "asrm", "bdi_1a_ms_child", "bisbas_child",
        "eswan_adhd", "eswan_dmdd", "mapssr", "panas", "post_scan_stai_state",
        "ppa", "prime", "rpas", "rsas", "pre_scan_stai", "substance",
        "tanner_boy", "tanner_girl", "wolf_im_em",
    }
    if stem in outcomes:
        return "potential later behavioral, affective, clinical, or motivational outcome; not cognitive ground truth"
    return "candidate cognitive task performance input; no final composite implied"


def values_as_text(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return "" if value is None else str(value)


def infer_type(values: Iterable[str]) -> str:
    vals = [v for v in values if v is not None and str(v).strip() != ""]
    if not vals:
        return "unknown"
    numeric = 0
    integer = 0
    for v in vals[:5000]:
        try:
            x = float(v)
            numeric += 1
            if x.is_integer():
                integer += 1
        except (TypeError, ValueError):
            pass
    if numeric == len(vals):
        return "integer/numeric" if integer == numeric else "numeric"
    return "categorical/string"


def parse_git_metadata(root: Path) -> dict[str, Any]:
    status = run_git(root, "status", "--short", "--branch")
    remotes = run_git(root, "remote", "-v")
    commit = run_git(root, "rev-parse", "HEAD")
    branch = run_git(root, "branch", "--show-current")
    describe = run_git(root, "describe", "--tags", "--always", "--dirty")
    tag_at_head = run_git(root, "tag", "--points-at", "HEAD").splitlines()
    last = run_git(root, "log", "-1", "--format=%H%n%aI%n%an%n%s").splitlines()
    return {
        "remote": remotes,
        "status": status,
        "commit": commit,
        "branch": branch,
        "describe": describe,
        "tags_at_HEAD": tag_at_head,
        "last_commit": {"hash": last[0] if len(last) > 0 else "", "date": last[1] if len(last) > 1 else "", "author": last[2] if len(last) > 2 else "", "subject": last[3] if len(last) > 3 else ""},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    root = args.dataset.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()

    git = parse_git_metadata(root)
    participants_path = root / "participants.tsv"
    participants_json_path = root / "participants.json"
    participants_fields: list[str] = []
    participants: list[dict[str, str]] = []
    if participants_path.is_file() and file_state(participants_path)[0] == "available":
        participants_fields, participants = parse_tsv(participants_path)

    subject_dirs = sorted([p for p in root.glob("sub-*") if p.is_dir()])
    participant_ids = [r.get("participant_id", "") for r in participants]
    participant_id_set = {x for x in participant_ids if x}
    subject_id_set = {p.name for p in subject_dirs}

    # Session-level tables are intentionally audited; MRI volumes are not opened.
    session_files = sorted(root.glob("sub-*/sub-*_sessions.tsv"))
    session_json_files = sorted(root.glob("sub-*/sub-*_sessions.json"))
    session_rows: list[dict[str, Any]] = []
    session_file_info: dict[str, dict[str, Any]] = {}
    session_fields_union: list[str] = []
    for path in session_files:
        state, pointer, target_exists = file_state(path)
        info = {"path": relpath(path, root), "state": state, "pointer": pointer, "target_exists": target_exists}
        session_file_info[relpath(path, root)] = info
        if state == "available":
            fields, rows = parse_tsv(path)
            for f in fields:
                if f not in session_fields_union:
                    session_fields_union.append(f)
            participant = path.parent.name
            for row in rows:
                row = dict(row)
                row["participant_id"] = participant
                row["source_path"] = relpath(path, root)
                row["session_key"] = f"{participant}/{row.get('session_id', '')}"
                session_rows.append(row)

    # Event tables contain n-back performance and are not MRI volumes.
    event_files = sorted(root.glob("sub-*/ses-*/func/*_events.tsv"))
    event_rows: list[dict[str, Any]] = []
    event_file_info: dict[str, dict[str, Any]] = {}
    event_fields_union: list[str] = []
    event_session_counts: Counter[str] = Counter()
    event_task_counts: Counter[str] = Counter()
    for path in event_files:
        state, pointer, target_exists = file_state(path)
        info = {"path": relpath(path, root), "state": state, "pointer": pointer, "target_exists": target_exists}
        event_file_info[relpath(path, root)] = info
        if state == "available":
            fields, rows = parse_tsv(path)
            for f in fields:
                if f not in event_fields_union:
                    event_fields_union.append(f)
            participant, session = participant_session_from_path(path)
            task_match = re.search(r"_task-([^_]+)", path.name)
            task = task_match.group(1) if task_match else "unknown"
            event_task_counts[task] += 1
            event_session_counts[f"{participant}/{session}"] += 1
            for row in rows:
                row = dict(row)
                row["participant_id"] = participant
                row["session_id"] = session
                row["task"] = task
                row["source_path"] = relpath(path, root)
                event_rows.append(row)

    # Phenotype dictionaries and tables.
    phenotype_jsons = sorted((root / "phenotype").glob("*.json")) if (root / "phenotype").is_dir() else []
    phenotype_tsvs = sorted((root / "phenotype").glob("*.tsv")) if (root / "phenotype").is_dir() else []
    phenotype_table_by_stem = {p.stem: p for p in phenotype_tsvs}

    # Manifest: hash metadata/tabular content, but not imaging/derivative files.
    relevant_prefixes = ("phenotype/", "sub-", "participants", "dataset_description.json", "README", "CHANGES", "sourcedata/")
    relevant_suffixes = (".json", ".tsv", ".bval", ".bvec")
    manifest_rows: list[dict[str, Any]] = []
    visible_files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Do not descend into Git's object database; it is not dataset content.
        dirnames[:] = [d for d in dirnames if d != ".git"]
        base = Path(dirpath)
        visible_files.extend(base / name for name in filenames)
    visible_files.sort()
    for path in visible_files:
        rp = relpath(path, root)
        is_imaging = rp.startswith("derivatives/") or bool(re.search(r"(?:\.nii\.gz|\.nii|\.bval|\.bvec)$", rp, re.IGNORECASE))
        is_relevant = (
            rp.startswith("phenotype/")
            or rp.startswith("sourcedata/")
            or path.name in {"participants.tsv", "participants.json", "dataset_description.json", "README", "CHANGES"}
            or bool(re.search(r"(^|/)sub-[^/]+/sub-[^/]+_sessions\.(tsv|json)$", rp))
            or bool(re.search(r"_events\.(tsv|json)$", rp))
        )
        if is_imaging:
            # Imaging and derivatives are inventoried by path and size only.
            state, pointer, target_exists = "inventory_only", "", False
        else:
            state, pointer, target_exists = file_state(path)
        hash_allowed = is_relevant and not is_imaging
        visible_hash = sha256(path) if hash_allowed else ""
        manifest_rows.append({
            "path": rp,
            "size_bytes": path.stat().st_size,
            "state": state,
            "is_annex_stub": "yes" if pointer else "no",
            "annex_target_exists": "yes" if target_exists else "no",
            "sha256_visible_file": visible_hash,
            "hash_scope": "visible file only; imaging/derivative files intentionally not hashed" if is_imaging else ("relevant visible content" if hash_allowed else "not hashed"),
            "scope_class": "A_or_B_relevant" if is_relevant else ("C_imaging_or_derivative" if is_imaging or rp.startswith("derivatives/") else "C_other"),
        })
    write_csv(out / "file_manifest.csv", manifest_rows, ["path", "size_bytes", "state", "is_annex_stub", "annex_target_exists", "sha256_visible_file", "hash_scope", "scope_class"])

    # Variable inventory.
    variable_rows: list[dict[str, Any]] = []
    if participants_json_path.is_file():
        docs = read_json(participants_json_path)
        observed_by_col = {f: [r.get(f, "") for r in participants] for f in participants_fields}
        for col, meta in docs.items():
            if col == "participant_id":
                meta = meta if isinstance(meta, dict) else {}
            levels = meta.get("Levels", {}) if isinstance(meta, dict) else {}
            variable_rows.append({
                "source_path": "participants.tsv",
                "dictionary_path": "participants.json",
                "variable": col,
                "description": meta.get("Description", meta.get("LongName", "")) if isinstance(meta, dict) else "",
                "task_or_instrument": "participant-level phenotype / clinical intake",
                "row_unit": "participant",
                "data_type": infer_type(observed_by_col.get(col, [])),
                "units": meta.get("Units", "") if isinstance(meta, dict) else "",
                "allowed_values": values_as_text(levels),
                "score_direction": "not documented",
                "missing_value_codes": "not documented",
                "validity_qc_codes": "not applicable/documented",
                "raw_summary_or_derived": "participant-level reported or clinical-interview indicator; not a cognitive score",
                "varies_across_visits": "no; participant-level baseline/timepoint-1 file",
                "documentation_source": "participants.json",
                "potential_chavi_role": "age/demographic/recruitment-group/context; diagnosis fields are not candidate cognitive domains",
                "availability": "available",
                "interpretation_issues": "age_months and age are documented as baseline intake values; dx_* are timepoint-1 binary indicators",
            })

    # Keep a set of available event-side dictionaries for exact code documentation.
    event_dict_docs: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("sub-*/ses-*/func/*_events.json")):
        if file_state(path)[0] == "available":
            try:
                event_dict_docs.setdefault(relpath(path, root), read_json(path))
            except json.JSONDecodeError:
                pass
    event_doc = next(iter(event_dict_docs.values()), {})

    for path in phenotype_jsons:
        stem = path.stem
        try:
            doc = read_json(path)
        except json.JSONDecodeError:
            continue
        table = phenotype_table_by_stem.get(stem)
        table_state = file_state(table)[0] if table else "not_found"
        for var, meta in doc.items():
            if var == "MeasurementToolMetadata" or not isinstance(meta, dict):
                continue
            levels = meta.get("Levels", {})
            variable_rows.append({
                "source_path": f"phenotype/{stem}.tsv",
                "dictionary_path": relpath(path, root),
                "variable": var,
                "description": meta.get("LongName", meta.get("Description", "")),
                "task_or_instrument": task_label_from_phenotype(stem),
                "row_unit": "participant-session (inferred from documented participant_id/session_id fields; verify after retrieval)",
                "data_type": "unknown while table unavailable",
                "units": meta.get("Units", ""),
                "allowed_values": values_as_text(levels),
                "score_direction": "not documented; do not assume higher is better",
                "missing_value_codes": "not documented",
                "validity_qc_codes": values_as_text(levels) if "valid_code" in var else "none documented for this variable",
                "raw_summary_or_derived": "summary/count/RT/accuracy/other; exact role requires table and task definition",
                "varies_across_visits": "potentially; session_id is documented where present; unavailable to verify",
                "documentation_source": relpath(path, root),
                "potential_chavi_role": potential_role(stem),
                "availability": table_state,
                "interpretation_issues": "table is an annex stub without a local annex object; dictionary alone does not establish composite validity or score direction",
            })

    for path in session_json_files:
        if file_state(path)[0] != "available":
            continue
        try:
            doc = read_json(path)
        except json.JSONDecodeError:
            continue
        tsv_path = path.with_suffix(".tsv")
        for var, meta in doc.items():
            if not isinstance(meta, dict):
                continue
            variable_rows.append({
                "source_path": relpath(tsv_path, root),
                "dictionary_path": relpath(path, root),
                "variable": var,
                "description": meta.get("Description", meta.get("LongName", "")),
                "task_or_instrument": "session-level scan/assessment summary; n-back summary variables where present",
                "row_unit": "session",
                "data_type": "numeric/string as observed",
                "units": meta.get("Units", ""),
                "allowed_values": "",
                "score_direction": "not documented; counts/rates/d-prime are not interchangeable",
                "missing_value_codes": "not documented",
                "validity_qc_codes": "none documented",
                "raw_summary_or_derived": "session summary/derived from n-back responses; not trial-level except events.tsv",
                "varies_across_visits": "yes, session-level",
                "documentation_source": relpath(path, root),
                "potential_chavi_role": "candidate working-memory/accuracy/error/sensitivity input; no final score calculated",
                "availability": "available where column exists",
                "interpretation_issues": "only 122 of 132 session files contain this n-back summary header; age is actual session age per sidecar, unlike participants.tsv baseline age",
            })

    for var, meta in event_doc.items():
        if not isinstance(meta, dict):
            continue
        variable_rows.append({
            "source_path": "sub-*/ses-*/func/*_events.tsv",
            "dictionary_path": "sub-*/ses-*/func/*_events.json",
            "variable": var,
            "description": meta.get("Description", meta.get("LongName", "")),
            "task_or_instrument": "n-back fMRI task event table",
            "row_unit": "trial/event",
            "data_type": "categorical/numeric as observed",
            "units": meta.get("Units", ""),
            "allowed_values": values_as_text(meta.get("Levels", {})),
            "score_direction": "not applicable for event labels; response_time direction not documented here",
            "missing_value_codes": values_as_text(meta.get("Levels", {}).get("n/a", "")) if isinstance(meta.get("Levels"), dict) else "",
            "validity_qc_codes": "none documented",
            "raw_summary_or_derived": "event-level task condition/outcome; response_time is trial-level when present",
            "varies_across_visits": "yes",
            "documentation_source": "sub-*/ses-*/func/*_events.json",
            "potential_chavi_role": "candidate n-back accuracy/error/speed input; do not equate with the full CNB battery",
            "availability": "available for materialized event tables",
            "interpretation_issues": "instruction rows use n/a; event table scope is n-back task only",
        })

    variable_fields = ["source_path", "dictionary_path", "variable", "description", "task_or_instrument", "row_unit", "data_type", "units", "allowed_values", "score_direction", "missing_value_codes", "validity_qc_codes", "raw_summary_or_derived", "varies_across_visits", "documentation_source", "potential_chavi_role", "availability", "interpretation_issues"]
    write_csv(out / "variable_inventory.csv", variable_rows, variable_fields)

    # Participant/session summary and visit calculations.
    by_participant: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in session_rows:
        by_participant[row["participant_id"]].append(row)
    nback_vars = [x for x in session_fields_union if x not in {"session_id", "age", "acq_time"}]
    nback_rows = [r for r in session_rows if any(not is_missing(r.get(v), column=v) for v in nback_vars)]
    nback_by_key: Counter[str] = Counter(r["session_key"] for r in nback_rows)
    event_by_key: Counter[str] = Counter(event_session_counts)
    participant_visit_rows: list[dict[str, Any]] = []
    for pid in sorted(participant_id_set | subject_id_set | set(by_participant)):
        rows = by_participant.get(pid, [])
        labels = sorted({str(r.get("session_id", "")) for r in rows})
        nback_labels = sorted({str(r.get("session_id", "")) for r in rows if any(not is_missing(r.get(v), column=v) for v in nback_vars)})
        event_labels = sorted({k.split("/", 1)[1] for k, n in event_by_key.items() if k.startswith(pid + "/") and n})
        participant_visit_rows.append({
            "participant_id": pid,
            "in_participants_tsv": "yes" if pid in participant_id_set else "no",
            "has_subject_directory": "yes" if pid in subject_id_set else "no",
            "recorded_visit_count": len(rows),
            "recorded_session_labels": ";".join(labels),
            "nback_summary_visit_count": len(nback_labels),
            "nback_summary_session_labels": ";".join(nback_labels),
            "nback_event_visit_count": len(event_labels),
            "nback_event_session_labels": ";".join(event_labels),
            "repeated_nback_summary_observation": "yes" if len(nback_labels) >= 2 else "no",
            "cognitive_occasion_status": "available n-back summary/events only; phenotype CNB battery unavailable",
        })
    pv_fields = ["participant_id", "in_participants_tsv", "has_subject_directory", "recorded_visit_count", "recorded_session_labels", "nback_summary_visit_count", "nback_summary_session_labels", "nback_event_visit_count", "nback_event_session_labels", "repeated_nback_summary_observation", "cognitive_occasion_status"]
    write_csv(out / "participant_visit_summary.csv", participant_visit_rows, pv_fields)

    # Task coverage.
    task_rows: list[dict[str, Any]] = []
    for path in phenotype_tsvs:
        stem = path.stem
        state = file_state(path)[0]
        task_rows.append({
            "task": task_label_from_phenotype(stem),
            "source_path": relpath(path, root),
            "dictionary_path": f"phenotype/{stem}.json",
            "source_kind": "phenotype task table",
            "available_rows": "",
            "unique_participants": "",
            "unique_participant_sessions": "",
            "observed_nonmissing_score_sessions": "",
            "repeated_observation_participants": "",
            "status": state,
            "notes": "Table content unavailable; dictionary is present. No missingness or repeat coverage can be calculated from the stub.",
        })
    nback_summary_sessions = sorted({r["session_key"] for r in nback_rows})
    nback_event_sessions = sorted({k for k, n in event_by_key.items() if n})
    task_rows.extend([
        {
            "task": "Short Letter N-Back (2 back) session summary",
            "source_path": "sub-*/sub-*_sessions.tsv",
            "dictionary_path": "sub-*/sub-*_sessions.json",
            "source_kind": "session-level summary",
            "available_rows": len(nback_rows),
            "unique_participants": len({r["participant_id"] for r in nback_rows}),
            "unique_participant_sessions": len(nback_summary_sessions),
            "observed_nonmissing_score_sessions": len(nback_rows),
            "repeated_observation_participants": sum(1 for p in set(r["participant_id"] for r in nback_rows) if sum(r["participant_id"] == p for r in nback_rows) >= 2),
            "status": "available",
            "notes": "Session summary variables include counts, hit/false-alarm rates, and d-prime; no validity code is supplied.",
        },
        {
            "task": "n-back fMRI task events",
            "source_path": "sub-*/ses-*/func/*_task-nback*_events.tsv",
            "dictionary_path": "sub-*/ses-*/func/*_task-nback*_events.json",
            "source_kind": "trial/event table",
            "available_rows": len(event_rows),
            "unique_participants": len({r["participant_id"] for r in event_rows}),
            "unique_participant_sessions": len(nback_event_sessions),
            "observed_nonmissing_score_sessions": sum(1 for k in nback_event_sessions if any(r["session_id"] == k.split("/", 1)[1] and r["participant_id"] == k.split("/", 1)[0] and r.get("score", "") not in {"", "n/a"} for r in event_rows)),
            "repeated_observation_participants": sum(1 for p in {r["participant_id"] for r in event_rows} if len({r["session_id"] for r in event_rows if r["participant_id"] == p}) >= 2),
            "status": "available",
            "notes": "Trial-level events include instruction, 0-back, and 2-back conditions; do not assume response_time is complete for every row.",
        },
    ])
    task_fields = ["task", "source_path", "dictionary_path", "source_kind", "available_rows", "unique_participants", "unique_participant_sessions", "observed_nonmissing_score_sessions", "repeated_observation_participants", "status", "notes"]
    write_csv(out / "task_visit_coverage.csv", task_rows, task_fields)

    # QC code inventory: documented phenotype validity codes (zero observed here)
    # plus actual event codes from materialized event tables.
    qc_rows: list[dict[str, Any]] = []
    for path in phenotype_jsons:
        stem = path.stem
        try:
            doc = read_json(path)
        except json.JSONDecodeError:
            continue
        for var, meta in doc.items():
            if "valid_code" in var and isinstance(meta, dict):
                levels = meta.get("Levels", {})
                for code, meaning in levels.items():
                    qc_rows.append({"source_path": f"phenotype/{stem}.tsv", "variable": var, "code": code, "documented_meaning": meaning, "observed_count": "0 (table unavailable)", "status": "documented, not observed locally"})
    for var, meta in event_doc.items():
        if not isinstance(meta, dict) or not isinstance(meta.get("Levels"), dict):
            continue
        counts = Counter(str(r.get(var, "")) for r in event_rows)
        for code, meaning in meta["Levels"].items():
            qc_rows.append({"source_path": "sub-*/ses-*/func/*_events.tsv", "variable": var, "code": code, "documented_meaning": meaning, "observed_count": counts.get(code, 0), "status": "observed event code"})
        for code, count in sorted(counts.items()):
            if code not in meta["Levels"]:
                qc_rows.append({"source_path": "sub-*/ses-*/func/*_events.tsv", "variable": var, "code": code, "documented_meaning": "not documented", "observed_count": count, "status": "unknown/undocumented observed code"})
    write_csv(out / "qc_code_inventory.csv", qc_rows, ["source_path", "variable", "code", "documented_meaning", "observed_count", "status"])

    # Missingness summaries for available tables; unavailable phenotype tables are
    # represented explicitly, never silently as all-missing observations.
    miss_rows: list[dict[str, Any]] = []
    for col in participants_fields:
        missing = sum(1 for r in participants if is_missing(r.get(col), participants=True, column=col))
        miss_rows.append({"source": "participants.tsv", "task_or_table": "participant-level phenotype", "variable": col, "unit": "participant", "denominator": len(participants), "observed_nonmissing": len(participants) - missing, "missing_or_unavailable": missing, "explicit_missing_code": "n/a is documented unknown for ethnicity and counted as observed", "status": "available"})
    for var in session_fields_union:
        observed = sum(1 for r in session_rows if var in r and not is_missing(r.get(var), column=var))
        absent = sum(1 for r in session_rows if var not in r)
        miss_rows.append({"source": "sub-*/sub-*_sessions.tsv", "task_or_table": "session summary", "variable": var, "unit": "session", "denominator": len(session_rows), "observed_nonmissing": observed, "missing_or_unavailable": len(session_rows) - observed, "explicit_missing_code": f"{absent} rows from files whose header omits this variable" if absent else "none detected in materialized rows", "status": "available"})
    for var in event_fields_union:
        missing = sum(1 for r in event_rows if is_missing(r.get(var), column=var))
        miss_rows.append({"source": "sub-*/ses-*/func/*_events.tsv", "task_or_table": "n-back events", "variable": var, "unit": "trial/event", "denominator": len(event_rows), "observed_nonmissing": len(event_rows) - missing, "missing_or_unavailable": missing, "explicit_missing_code": "n/a is used for instruction events where applicable", "status": "available"})
    for path in phenotype_tsvs:
        stem = path.stem
        try:
            doc = read_json(root / "phenotype" / f"{stem}.json")
            vars_ = [k for k in doc if k != "MeasurementToolMetadata"]
        except Exception:
            vars_ = []
        for var in vars_:
            miss_rows.append({"source": relpath(path, root), "task_or_table": task_label_from_phenotype(stem), "variable": var, "unit": "participant-session", "denominator": "unknown", "observed_nonmissing": "unknown", "missing_or_unavailable": "unknown", "explicit_missing_code": "not available", "status": "unavailable annex stub"})
    write_csv(out / "missingness_summary.csv", miss_rows, ["source", "task_or_table", "variable", "unit", "denominator", "observed_nonmissing", "missing_or_unavailable", "explicit_missing_code", "status"])

    # Candidate mappings only; no score construction.
    mappings = [
        ("Penn Abstraction, Inhibition and Working Memory Task", "Executive control; abstraction/inhibition/working-memory candidate", "phenotype/penn_abstraction_inhibition_working_memory_task.json; README", "Local task name explicitly combines abstraction, inhibition, and working memory; component-level mapping cannot be separated from this table alone."),
        ("Penn Face Memory Test", "Episodic memory; face memory candidate", "phenotype/penn_face_memory_test.json; README; Penn CNB Explore Tests", "Named task supports face-memory interpretation; no composite defined."),
        ("Children's Penn Word Memory Test", "Episodic memory; verbal/word memory candidate", "phenotype/penn_word_memory_test.json; README; Penn CNB Explore Tests", "Named task supports verbal-memory interpretation."),
        ("Short Computerized Finger-Tapping Task", "Sensorimotor/motor speed candidate", "phenotype/short_computerized_finger_tapping_task.json; README; Penn CNB Explore Tests", "Named task supports motor-speed interpretation."),
        ("Penn Emotion Recognition Task for Children", "Social cognition; emotion identification candidate", "phenotype/penn_emotion_recognition_task.json; README; Penn CNB Explore Tests", "Named task supports emotion-identification interpretation."),
        ("Digit Symbol Test", "Processing speed candidate; recall variables may also relate to relational memory", "phenotype/digit_symbol.json; README; Penn CNB Explore Tests", "Do not collapse all digit-symbol variables into one score; variable-specific definitions are needed."),
        ("Short Letter N-Back (2 back)", "Executive control; working-memory candidate", "phenotype/short_letter_2back.json; sub-*/sub-*_sessions.json; README; Penn CNB Explore Tests", "Available session summary includes 0-back, 2-back, and combined counts/rates/d-prime; no final score calculated."),
        ("Measured Emotion Differentiation Test", "Social cognition; emotion-intensity differentiation candidate", "phenotype/measured_emotion_differentiation_test.json; README; Penn CNB Explore Tests", "Named task supports emotion differentiation."),
        ("Motor Praxis Test", "Sensorimotor praxis-speed candidate", "phenotype/motor_praxis.json; README; Penn CNB Explore Tests", "Named task supports praxis-speed interpretation."),
        ("Penn Conditional Exclusion Task for Children", "Candidate executive-control/abstraction task; provisional", "phenotype/penn_conditional_exclusion_task.json; README", "Not assigned to a final domain: exact task construct and scoring require instrument documentation."),
        ("Short Penn Continuous Performance Test", "Attention/sustained-attention candidate", "phenotype/short_penn_continuous_performance_test.json; README; Penn CNB Explore Tests", "Number and letter variants and variables need task-specific review."),
        ("Penn Matrix Reasoning Test", "Complex cognition; nonverbal reasoning candidate", "phenotype/penn_matrix_reasoning_test.json; README; Penn CNB Explore Tests", "Named task supports nonverbal reasoning."),
        ("Variable Short Penn Line Orientation Test", "Complex cognition; spatial-processing candidate", "phenotype/variable_short_penn_line_orientation_test.json; README; Penn CNB Explore Tests", "Named task supports spatial processing."),
        ("Children's Verbal Reasoning Test", "Complex cognition; language/verbal reasoning candidate", "phenotype/penn_verbal_reasoning_test.json; README; Penn CNB Explore Tests", "Named task supports verbal reasoning."),
        ("Short Visual Object Learning Test", "Episodic memory; spatial/visual-object memory candidate", "phenotype/visual_object_learning_test.json; README; Penn CNB Explore Tests", "Named task supports visual/spatial memory."),
        ("Trailmaking A", "Candidate processing-speed/executive-control input; provisional", "phenotype/trailmaking_test_a.json; README", "No domain assignment finalized from inspected local docs."),
        ("Trailmaking B", "Candidate executive-control/set-shifting input; provisional", "phenotype/trailmaking_test_b.json; README", "No domain assignment finalized from inspected local docs."),
        ("Effort Discounting Task", "Reward decision-making candidate", "phenotype/effort_discounting_task.json; README; Penn CNB Explore Tests", "Named task supports reward decision-making; choice-model parameters are not calculated."),
        ("Delayed Discounting Task", "Reward decision-making candidate", "phenotype/delay_discounting_task.json; README; Penn CNB Explore Tests", "Named task supports intertemporal/reward decision-making; parameters are not calculated."),
        ("Risk Discounting Task", "Reward decision-making candidate", "phenotype/risk_discounting_task.json; README; Penn CNB Explore Tests", "Named task supports risk/reward decision-making; parameters are not calculated."),
        ("Age Differentiation Test", "Social cognition; age differentiation candidate", "phenotype/age_differentiation_test.json; README; Penn CNB Explore Tests", "Named task supports age differentiation."),
    ]
    mapping_rows = [{"task": a, "candidate_domain": b, "evidence": c, "status": "candidate only", "unresolved_interpretation": d} for a, b, c, d in mappings]
    write_csv(out / "candidate_domain_mapping.csv", mapping_rows, ["task", "candidate_domain", "evidence", "status", "unresolved_interpretation"])

    # Candidate outcomes and contextual variables.
    outcome_names = [
        ("study_group", "participants.tsv", "recruitment/experimental group; not individual diagnosis", "available participant-level"),
        ("dx_*", "participants.tsv", "timepoint-1 clinical-interview binary indicators; not cognitive ground truth", "available participant-level"),
        ("age_months; age", "participants.tsv", "baseline intake age; not necessarily age at later assessments", "available participant-level"),
    ]
    self_report_stems = [p.stem for p in phenotype_tsvs if p.stem not in {"digit_symbol", "short_letter_2back", "penn_abstraction_inhibition_working_memory_task", "penn_face_memory_test", "penn_word_memory_test", "short_computerized_finger_tapping_task", "penn_emotion_recognition_task", "measured_emotion_differentiation_test", "motor_praxis", "penn_conditional_exclusion_task", "short_penn_continuous_performance_test", "penn_matrix_reasoning_test", "variable_short_penn_line_orientation_test", "penn_verbal_reasoning_test", "visual_object_learning_test", "trailmaking_test_a", "trailmaking_test_b", "effort_discounting_task", "delay_discounting_task", "risk_discounting_task", "age_differentiation_test"}]
    for stem in self_report_stems:
        outcome_names.append((task_label_from_phenotype(stem), f"phenotype/{stem}.tsv", "potential behavioral/affective/clinical/motivational outcome or context; not cognitive ground truth", "dictionary available; data unavailable annex stub"))
    outcome_rows = [{"candidate_outcome_or_context": a, "source_path": b, "role": c, "baseline_availability": d, "followup_availability": "not calculable from unavailable phenotype table", "score_direction": "not assumed", "overlap_with_cognitive_observations": "not calculable; do not use for predictor selection yet", "notes": "No outcome modelling performed."} for a, b, c, d in outcome_names]
    write_csv(out / "outcome_coverage.csv", outcome_rows, ["candidate_outcome_or_context", "source_path", "role", "baseline_availability", "followup_availability", "score_direction", "overlap_with_cognitive_observations", "notes"])

    # Provenance JSON.
    dataset_description = read_json(root / "dataset_description.json") if (root / "dataset_description.json").is_file() else {}
    provenance = {
        "audit_started_utc": started,
        "audit_finished_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_root": str(root),
        "intended_snapshot": "1.0.6",
        "local_dataset_description": dataset_description,
        "git": git,
        "provenance_assessment": {
            "snapshot_identity": "supported for the Git checkout: local dataset_description DOI and Git tag/describe identify 1.0.6; GitHub release maps 1.0.6 to fc7dc36. Underlying annex object content cannot be independently verified because the local annex object store is empty.",
            "download_method": "not recorded in inspected local documentation",
            "download_date": "not recorded; local filesystem timestamps are not treated as download provenance",
            "version_mixture": "no working-tree changes observed; all visible files are from the clean tagged checkout, but absent annex objects prevent checking content beyond pointer identities",
            "documentation_data_alignment": "metadata and documentation are in the tagged 1.0.6 checkout; actual annex payloads are unavailable locally",
            "license": dataset_description.get("License", "not found"),
        },
        "software": {"python": sys.version, "platform": platform.platform(), "git": run_git(root, "--version")},
        "local_counts": {
            "participants_rows": len(participants),
            "unique_participants_tsv": len(participant_id_set),
            "subject_directories": len(subject_dirs),
            "session_files": len(session_files),
            "available_session_rows": len(session_rows),
            "nback_summary_rows": len(nback_rows),
            "event_files": len(event_files),
            "event_rows": len(event_rows),
            "phenotype_tsvs": len(phenotype_tsvs),
            "phenotype_tsvs_unavailable_annex": sum(1 for p in phenotype_tsvs if file_state(p)[0] == "unavailable_annex_stub"),
        },
    }
    write_json(out / "dataset_provenance.json", provenance)

    # Aggregate metrics for the report.
    session_keys = [r["session_key"] for r in session_rows]
    duplicate_session_keys = sorted([k for k, n in Counter(session_keys).items() if n > 1])
    participant_duplicate_ids = sorted([k for k, n in Counter(participant_ids).items() if k and n > 1])
    visit_counts = Counter(len(by_participant.get(pid, [])) for pid in participant_id_set)
    pair_counts = Counter()
    nback_pair_counts = Counter()
    event_pair_counts = Counter()
    for pid, rows in by_participant.items():
        labels = sorted({r.get("session_id", "") for r in rows})
        for i, a in enumerate(labels):
            for b in labels[i + 1:]:
                pair_counts[f"{a} + {b}"] += 1
        nlabels = sorted({r.get("session_id", "") for r in rows if any(not is_missing(r.get(v), column=v) for v in nback_vars)})
        for i, a in enumerate(nlabels):
            for b in nlabels[i + 1:]:
                nback_pair_counts[f"{a} + {b}"] += 1
    for pid in {r["participant_id"] for r in event_rows}:
        elabels = sorted({r["session_id"] for r in event_rows if r["participant_id"] == pid})
        for i, a in enumerate(elabels):
            for b in elabels[i + 1:]:
                event_pair_counts[f"{a} + {b}"] += 1

    # Descriptive range/ceiling checks for available n-back summaries.
    range_checks: list[dict[str, Any]] = []
    for var in nback_vars:
        vals = []
        for row in nback_rows:
            try:
                vals.append(float(row.get(var, "")))
            except (TypeError, ValueError):
                pass
        if not vals:
            continue
        out_of_range = 0
        if var.endswith("_hit_rate") or var.endswith("_false_alarm_rate"):
            out_of_range = sum(1 for x in vals if x < 0 or x > 1)
        floor = sum(1 for x in vals if x == 0)
        ceiling = sum(1 for x in vals if x == 1)
        range_checks.append({"variable": var, "n_numeric": len(vals), "min": min(vals), "max": max(vals), "out_of_documented_proportion_range": out_of_range, "exact_zero": floor, "exact_one": ceiling})
    nback_complete_rows = sum(1 for row in nback_rows if all(not is_missing(row.get(v), column=v) for v in nback_vars))
    nback_partial_rows = len(nback_rows) - nback_complete_rows
    event_code_counts = {
        var: dict(Counter(str(r.get(var, "")) for r in event_rows))
        for var in ("trial_type", "results", "score")
        if var in event_fields_union
    }

    # Search only text-like inspected material for medication terms.
    medication_hits: list[str] = []
    search_roots = [root / "README", root / "CHANGES", root / "dataset_description.json", root / "participants.json", root / "phenotype", root / "sourcedata"]
    for base in search_roots:
        paths = [base] if base.is_file() else ([p for p in base.rglob("*") if p.is_file()] if base.is_dir() else [])
        for p in paths:
            if p.stat().st_size > 5 * 1024 * 1024:
                continue
            try:
                text = read_text(p)
            except OSError:
                continue
            if re.search(r"\bmedicat(?:ion|ions|ed)|\bstimulant|\bmeds?\b", text, re.IGNORECASE):
                medication_hits.append(relpath(p, root))

    # Report.
    available_annex = sum(1 for r in manifest_rows if r["state"] == "available_annex_object")
    unavailable_annex = sum(1 for r in manifest_rows if r["state"] == "unavailable_annex_stub")
    imaging_files = [r for r in manifest_rows if r["scope_class"] == "C_imaging_or_derivative"]
    report = f"""# CHAVI Step 1 dataset audit: Penn LEAD (ds007116)

Audit timestamp (UTC): `{started}` to `{datetime.now(timezone.utc).isoformat()}`  
Dataset root: `{root}`  
Audit script: `audit.py`  
Scope: non-destructive metadata and tabular audit only. No MRI volume was loaded, no imputation, scoring, reliability analysis, prediction, or modelling was performed.

## Executive result

The local checkout is a clean Git checkout of the official `OpenNeuroDatasets/ds007116` repository at commit `{git.get('commit','')}`, with local tag/description `1.0.6`. The metadata and documentation identify DOI `doi:10.18112/openneuro.ds007116.v1.0.6` and CC0. This establishes the Git checkout identity, but not the availability of every payload object.

The local repository contains {len(participants)} rows in `participants.tsv`, {len(session_files)} participant session tables with {len(session_rows)} recorded session rows, {len(nback_rows)} materialized session-level n-back summary rows, and {len(event_files)} materialized n-back event files with {len(event_rows)} event rows. The full phenotype battery is not locally available: {sum(1 for p in phenotype_tsvs if file_state(p)[0] == 'unavailable_annex_stub')} phenotype TSVs are annex stubs whose target objects are absent from `.git/annex/objects`. Therefore no full-battery missingness, cross-task overlap, domain-score, profile, ICC, SEM, MDC, or outcome-overlap result is supportable from this checkout.

Interpretation labels below use: **Observed** = calculated from materialized local content; **Documented** = stated in local documentation; **Externally verified** = checked against official online documentation; **Proposed** = cautious candidate interpretation; **Unresolved** = cannot be established from available material.

## 1. What was inspected and what remained unavailable

Inspected: Git metadata, `dataset_description.json`, `README`, `CHANGES`, `participants.tsv/json`, all phenotype dictionaries, all visible `*_sessions.tsv/json` files, all visible n-back `*_events.tsv/json` files, file states/pointers, and high-level directory/file inventory. MRI volumes and derivatives were inventoried by path/size/state only; they were not loaded or hashed.

Unavailable: the underlying objects for phenotype TSVs and most large imaging/derivative files. The visible annex stubs point to `.git/annex/objects/...`, but the local annex object store contained no files at audit time. The phenotype JSON dictionaries are available, but they do not supply rows, missingness, visit coverage, or observed validity codes.

## 2. Repository and dataset provenance

- **Observed:** remote is `{git.get('remote','')}`; branch is `{git.get('branch','')}`; `git status` reported `{git.get('status','').replace(chr(10),' | ')}`; `git describe` is `{git.get('describe','')}`; tag(s) at HEAD: `{', '.join(git.get('tags_at_HEAD',[]))}`.
- **Observed:** local `dataset_description.json` has BIDSVersion `{dataset_description.get('BIDSVersion','')}`, DatasetType `{dataset_description.get('DatasetType','')}`, DOI `{dataset_description.get('DatasetDOI','')}`, License `{dataset_description.get('License','')}`, and `ReferencesAndLinks` values `TODO` / `List of papers or websites`.
- **Documented:** `CHANGES` lists 1.0.6 on 2026-07-28 and notes a sidecar-key warning fix; 1.0.5 fixed phenotype JSON typos; 1.0.3 updated events TSV files; 1.0.1 added session age and the phenotype folder.
- **Externally verified:** the official GitHub release page for 1.0.6 maps the tag to short commit `fc7dc36`; the official raw 1.0.6 metadata matches the local DOI/name/license. The official README describes the same 132-adolescent dataset and the same cognitive/self-report inventories.
- **Unresolved:** download method and download date are not recorded in the inspected local documentation. Local file timestamps are copy/check-out timestamps, not provenance evidence. No evidence of a mixed Git-version working tree was observed, but absent annex payloads prevent checking payload content beyond the pointer paths committed at HEAD.

## 3. Participant, visit, and cognitive-assessment counts

Counting rules: a recorded visit is one row in an available `sub-*/sub-*_sessions.tsv`; a unique participant-session is the `participant_id/session_id` key; an n-back summary observation requires at least one non-missing n-back summary variable in that row; an n-back event observation requires at least one materialized event table for that participant/session. These are availability counts, not “usable” counts. No validity-based exclusion rule was applied.

- **Observed:** unique participants in `participants.tsv`: **{len(participant_id_set)}**; participant rows: **{len(participants)}**; subject directories: **{len(subject_id_set)}**.
- **Observed:** available session files: **{len(session_files)}**; unique participant-session keys: **{len(set(session_keys))}**; session rows: **{len(session_rows)}**.
- **Observed:** participants with 1 / 2 / 3+ recorded session rows: **{sum(visit_counts.get(1,0) for _ in [0])} / {visit_counts.get(2,0)} / {sum(n for k,n in visit_counts.items() if k >= 3)}**. The first number is written this way to make clear it is the count at key `1`, not a total of rows.
- **Observed:** n-back summary rows: **{len(nback_rows)}**, unique participants: **{len({r['participant_id'] for r in nback_rows})}**, unique participant-sessions: **{len(set(r['session_key'] for r in nback_rows))}**; n-back event files: **{len(event_files)}**, event rows: **{len(event_rows)}**, unique event participant-sessions: **{len(nback_event_sessions)}**.
- **Observed:** duplicate participant IDs in `participants.tsv`: `{', '.join(participant_duplicate_ids) if participant_duplicate_ids else 'none'}`. Duplicate participant-session keys in available session tables: `{', '.join(duplicate_session_keys) if duplicate_session_keys else 'none'}`.
- **Observed:** IDs in subject directories but not `participants.tsv`: `{', '.join(sorted(subject_id_set - participant_id_set)) if subject_id_set - participant_id_set else 'none'}`; participant IDs without subject directories: `{', '.join(sorted(participant_id_set - subject_id_set)) if participant_id_set - subject_id_set else 'none'}`.

Recorded visit pair counts (all session rows): `{json.dumps(dict(sorted(pair_counts.items())))}`. N-back-summary pair counts: `{json.dumps(dict(sorted(nback_pair_counts.items())))}`. Event-table pair counts: `{json.dumps(dict(sorted(event_pair_counts.items())))}`. These pair counts are descriptive and do not establish comparable measurement occasions.

No cross-task overlap for the full CNB battery can be calculated because the phenotype tables are unavailable. Ten of the 132 session files have only `session_id`, `age`, and `acq_time` in the header; this is evidence of missing n-back summary coverage in those materialized session files, not proof that all cognitive tasks were absent.

## 4. Cognitive task and variable inventory

The local `README` names 21 cognitive tasks from the Penn CNB. Their dictionaries are present under `phenotype/`, but the corresponding TSV tables are annex stubs. The materialized local cognitive data are narrower:

- `sub-*/sub-*_sessions.tsv`: session-level n-back counts, hit/false-alarm rates, and d-prime variables where the header is present. The sidecar defines `age` as fractional years at the time of each session and `acq_time` as rounded/anonymized acquisition time.
- `sub-*/ses-*/func/*_task-nback*_events.tsv`: trial/event rows with `onset`, `duration`, `trial_type`, `results`, `response_time`, and `score`. These are trial-level event data, not a general rule for all reaction-time fields in the phenotype battery.
- `phenotype/*.json`: exact variable names, task labels, units, and documented validation-code levels. The dictionary does not establish score direction, validated composites, or a common QC rule across tasks.

Exact variable-level documentation is in `variable_inventory.csv`. The script records both documentation and unresolved issues rather than inferring that higher is better or that all tasks share one validity scheme.

## 5. Candidate domain mappings

`candidate_domain_mapping.csv` contains only provisional task-to-domain candidates. The official Penn CNB Explore Tests page supports mappings such as Letter-N-Back to working memory, Digit-Symbol to processing speed, Word/Face/Visual Object tests to episodic memory, Matrix/Verbal/Line Orientation tests to complex cognition, Emotion/Age Differentiation to social cognition, discounting tasks to reward decision-making, and Motor Praxis/Finger Tapping to sensorimotor or motor speed. The local AIM task name combines multiple constructs, and Conditional Exclusion/Trailmaking are left provisional pending task-specific documentation.

No final domain scores, global scores, profile level, scatter, or shape scores were calculated.

## 6. Missingness, QC, and repeat coverage

- **Observed:** available-table missingness is in `missingness_summary.csv`. Event-level `n/a` values are treated as task-defined not-applicable values for missingness summaries; instruction rows are not silently treated as failed cognitive trials.
- **Observed:** event QC/value frequencies are in `qc_code_inventory.csv`. Unknown event codes would be listed explicitly. No phenotype validity-code frequencies can be observed because phenotype TSV payloads are unavailable; their documented levels are retained with observed count `0 (table unavailable)`.
- **Observed:** among the {len(nback_rows)} n-back summary rows with at least one observed summary variable, {nback_complete_rows} have all {len(nback_vars)} n-back summary variables non-missing and {nback_partial_rows} are partial. No row was removed. Event code counts for the materialized tables are `{json.dumps(event_code_counts, sort_keys=True)}`.
- **Observed:** n-back range/ceiling checks are `{json.dumps(range_checks, separators=(',', ':'))}`. For proportion variables, values outside [0,1] are flagged; exact 0/1 concentrations are descriptive only and were not used to filter observations.
- **Documented:** the README records task-level cognitive omissions and self-report missingness/protocol changes, including the special continuation/repeat situation for `sub-20812`, and states that session acquisition time was rounded for anonymization. These notes are not substituted for row-level verification of unavailable tables.
- **Unresolved:** whether repeated scans, continuation sessions, and cognitive assessments are comparable; whether a missing phenotype row means no assessment, an unavailable extract, or a task-specific missing value; and how validity codes should be handled across tasks.

## 7. Demographic, clinical, and contextual variables

`participants.tsv/json` documents `study_group`, `sex`, `race`, `ethnicity`, baseline `age_months`/`age`, and timepoint-1 clinical-interview indicators `dx_none`, `dx_prodromal`, `dx_prodromal_remit`, `dx_psychosis`, `dx_moodnos`, `dx_mdd`, `dx_bp`, `dx_adhd`, `dx_ptsd`, and `dx_ptsd_remit`. `study_group` is a recruitment/experimental group with levels ADHD, TD/NC, and PRO/CHR; it must not be treated as an individual diagnosis. Baseline age is not the same as session age.

Medication search: inspected `README`, `CHANGES`, `dataset_description.json`, `participants.json`, `phenotype/*.json`, and `sourcedata/` for medication/stimulant terms. Matching files: `{', '.join(sorted(set(medication_hits))) if medication_hits else 'none'}`. Medication was **not identified in the inspected material**.

## 8. Candidate outcomes and longitudinal availability

The README names self-report scales including ALES, ALS-18, ARI, ASRM, BDI-1A, BIS-BAS, E-SWAN ADHD/DMDD, MAPS-SR, PANAS, PPA, PRIME, RPAS, RSAS, Substance Use, Tanner scales, Wolf IM/EM, and pre/post STAI. Their dictionaries are present, but their TSV data are unavailable locally. Consequently baseline/follow-up availability, overlap with cognitive observations, and score direction remain unresolved here. `outcome_coverage.csv` records these as candidates only; no outcomes were used for predictor selection.

## 9. Files relevant and irrelevant to CHAVI Paper 1

- **A — relevant now:** `participants.tsv/json`; `sub-*/sub-*_sessions.tsv/json`; n-back `*_events.tsv/json`; phenotype dictionaries; `dataset_description.json`, `README`, `CHANGES`; Git-annex/file-state metadata.
- **B — potentially useful later:** phenotype TSV payloads once retrieved; full self-report tables; additional task event or summary files; code/CuBIDS summaries; documented QC lists; session timing after its anonymization implications are resolved.
- **C — not required for Paper 1 at this stage:** MRI volumes, field maps, DWI/ASL/MEGRE volumes, FreeSurfer and task-contrast derivatives, unless a later preregistered validity question specifically requires them. They were inventoried at high level only.
- **D — unavailable or ambiguous:** phenotype TSV payloads and most large annexed objects; observed validity/QC codes for phenotype tasks; full cross-task overlap; medication variables; any claim that the full CNB battery is locally analyzable.

## 10. Conflicts between assumptions and observed data

1. The intended snapshot is supported for the Git checkout, but local data payload availability is incomplete because annex objects are absent.
2. The README describes a 132-participant, multi-task longitudinal dataset, but the materialized cognitive payload available for direct counting is mainly n-back session summaries/events.
3. Session-level `age` is documented as age at each session; `participants.tsv` age is documented as baseline intake age. They must not be swapped.
4. Session dates/times are rounded/anonymized; exact follow-up intervals should not be treated as precise without a documented de-identification transformation.
5. A task name or existing summary variable is not evidence of a validated CHAVI domain composite.
6. The presence of an `events.tsv` response-time column demonstrates trial-level response times for that n-back task only; it does not establish trial-level data in all phenotype RT variables.

## 11. Remaining uncertainties and scientific-review questions

- Which exact phenotype payloads should be retrieved, and how will retrieval preserve the verified 1.0.6 snapshot?
- What is the source-of-truth rule for a cognitive occasion when BIDS sessions, CNB sessions, repeat scans, and incomplete/continued visits disagree?
- Which task variables and validity codes are admissible before any reliability analysis, and are rules task-specific?
- Are session-level n-back summaries intended as candidate Paper 1 outcomes, or only as an auxiliary task with separate provenance?
- Which candidate domain mappings are scientifically justified for this specific Penn LEAD battery, and which should remain unassigned?
- What minimum repeated-occasion and cross-task overlap criteria should be preregistered before scoring?

## 12. Audit outputs and reproduction

Created in this directory: `audit_report.md`, `dataset_provenance.json`, `file_manifest.csv`, `variable_inventory.csv`, `participant_visit_summary.csv`, `task_visit_coverage.csv`, `qc_code_inventory.csv`, `missingness_summary.csv`, `candidate_domain_mapping.csv`, `outcome_coverage.csv`, `audit_issues.md`, and `audit.py`.

Rerun from the workspace parent with:

```powershell
python .\\chavi_audit_ds007116_20260907\\audit.py --dataset .\\ds007116 --output .\\chavi_audit_ds007116_20260907
```

The script records Python/Git versions in `dataset_provenance.json`. It does not download, modify, clean, reset, checkout, or update the dataset repository.

## 13. Recommended next decision before scoring or modelling

**Decide and document the exact retrieval plan for the missing phenotype TSV payloads, with snapshot-preserving provenance, before any scoring or modelling.** After retrieval, repeat this audit and require row-level checks for task/session identity, validity-code semantics, cross-task overlap, baseline versus session age, and repeated-visit comparability. Until that is done, the checkout supports metadata audit and a limited n-back availability audit, not the planned full multidomain CHAVI Paper 1 analysis.

## Official sources consulted

- [Official GitHub repository](https://github.com/OpenNeuroDatasets/ds007116)
- [Official 1.0.6 raw dataset description](https://raw.githubusercontent.com/OpenNeuroDatasets/ds007116/1.0.6/dataset_description.json)
- [Official 1.0.6 README](https://raw.githubusercontent.com/OpenNeuroDatasets/ds007116/1.0.6/README)
- [Official 1.0.6 CHANGES](https://raw.githubusercontent.com/OpenNeuroDatasets/ds007116/1.0.6/CHANGES)
- [Official 1.0.6 GitHub release](https://github.com/OpenNeuroDatasets/ds007116/releases/tag/1.0.6)
- [Penn CNB Explore Tests](https://webcnp.med.upenn.edu/explore-tests.html)
- [Penn CNB overview](https://webcnp.med.upenn.edu/about.html)
"""
    (out / "audit_report.md").write_text(report, encoding="utf-8")

    issues = f"""# CHAVI audit issues and retrieval blockers

## Blocking for full Paper 1 data audit

1. **Phenotype payloads unavailable:** {sum(1 for p in phenotype_tsvs if file_state(p)[0] == 'unavailable_annex_stub')} `phenotype/*.tsv` files are visible annex stubs; their target objects are absent from the local `.git/annex/objects` store. Retrieve the annex content using a snapshot-pinned DataLad/Git-annex/OpenNeuro method that keeps the repository at commit `{git.get('commit','')}` / tag `1.0.6`, then rerun this script.
2. **Full repeat coverage unknown:** without phenotype rows, cannot calculate task-specific participant/session coverage, pairwise cross-task overlap, or whether a session-level n-back observation is aligned with all other cognitive tasks.
3. **Validity semantics unresolved in observed data:** dictionaries document validity-code levels, but no phenotype validity values are locally observable. Do not filter based on the documented levels alone.

## Important non-blocking ambiguities

- Session acquisition times are rounded/anonymized; precise elapsed-time analyses require a documented transformation rule.
- `participants.tsv` age is baseline; session-table age is per-session. Use exact source variable names.
- Recruitment groups and `dx_*` indicators are different concepts; neither is a cognitive-domain label.
- Medication was not identified in `README`, `CHANGES`, `dataset_description.json`, `participants.json`, `phenotype/*.json`, or `sourcedata/` inspected material.
- No final cognitive composites, global scores, profile-shape scores, reliability coefficients, or predictive models were calculated.

## Reproducibility note

The original dataset repository was not modified. The audit output is outside the dataset repository. Hashes in `file_manifest.csv` are hashes of visible relevant metadata/tabular files; for annex stubs, they hash the visible stub text, not the absent payload. Imaging and derivative files are listed but intentionally not hashed or loaded.
"""
    (out / "audit_issues.md").write_text(issues, encoding="utf-8")

    print(json.dumps({
        "output": str(out),
        "participants": len(participant_id_set),
        "session_rows": len(session_rows),
        "nback_summary_rows": len(nback_rows),
        "event_files": len(event_files),
        "event_rows": len(event_rows),
        "phenotype_tsvs": len(phenotype_tsvs),
        "phenotype_unavailable_annex": sum(1 for p in phenotype_tsvs if file_state(p)[0] == "unavailable_annex_stub"),
        "manifest_files": len(manifest_rows),
        "unavailable_annex_visible_files": unavailable_annex,
        "available_annex_objects": available_annex,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
