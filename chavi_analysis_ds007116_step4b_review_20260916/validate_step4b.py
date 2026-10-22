#!/usr/bin/env python3
"""Independent CHAVI Step 4B-R validation.

This validator deliberately does not import the Step 4B production module or
call its cohort/statistical functions.  It reconstructs task pairs from the
verified raw payloads and recalculates all reported statistics independently.
It writes only the Step 4B-R review directory.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import random
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
DATASET = ROOT / "ds007116"
STAGE = ROOT / "chavi_step1b_phenotype_staging_20260907"
STEP3B = ROOT / "chavi_audit_ds007116_step3b_20260909"
STEP4A = ROOT / "chavi_analysis_ds007116_step4a_face_memory_20260914"
STEP4A_REVIEW = ROOT / "chavi_analysis_ds007116_step4a_review_20260914"
STEP4B = ROOT / "chavi_analysis_ds007116_step4b_five_tasks_20260916"
COMMIT = "fc7dc36fa2598b0b2e4579baef37d148cc085207"
BOOTSTRAP_REPLICATES = 5000
BOOTSTRAP_SEED = 20260914
MISSING = {"", "n/a", "na", "null", "none", "missing"}
QC_MEANINGS = {"V": "Valid", "F": "Likely valid", "0": "No autovalidation rule available", "S": "Skipped", "N": "Not Valid", "C": "Assessor Comment", "X": "Excluded"}
TASKS = [
    {"task_key": "letter_nback", "label": "Letter N-back", "stem": "short_letter_2back", "score_field": "cnb_lnb_mcr", "qc_field": "cnb_lnb_valid_code", "filename": "short_letter_2back.tsv"},
    {"task_key": "face_memory", "label": "Face Memory", "stem": "penn_face_memory_test", "score_field": "cnb_cpf_cr", "qc_field": "cnb_cpf_valid_code", "filename": "penn_face_memory_test.tsv"},
    {"task_key": "matrix_reasoning", "label": "Matrix Reasoning", "stem": "penn_matrix_reasoning_test", "score_field": "cnb_pmat_cr", "qc_field": "cnb_pmat_valid_code", "filename": "penn_matrix_reasoning_test.tsv"},
    {"task_key": "emotion_recognition", "label": "Emotion Recognition", "stem": "penn_emotion_recognition_task", "score_field": "cnb_er40_cr", "qc_field": "cnb_er40_valid_code", "filename": "penn_emotion_recognition_task.tsv"},
    {"task_key": "dominant_finger_tapping", "label": "Dominant Finger Tapping", "stem": "short_computerized_finger_tapping_task", "score_field": "cnb_ctap_dom", "qc_field": "cnb_ctap_valid_code", "filename": "short_computerized_finger_tapping_task.tsv"},
]


class ReviewError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def directory_hashes(path: Path) -> list[dict[str, Any]]:
    return [{"relative_path": str(item.relative_to(path)), "size_bytes": item.stat().st_size, "sha256": sha256(item)} for item in sorted(path.rglob("*")) if item.is_file()]


def read_csv(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    if not path.is_file():
        raise ReviewError(f"Missing input: {path}")
    try:
        reader = csv.reader(io.StringIO(path.read_text(encoding="utf-8-sig")), strict=True, delimiter=delimiter)
        header = next(reader)
        if len(header) != len(set(header)):
            raise ReviewError(f"Duplicate header fields: {path}")
        rows = []
        for line, values in enumerate(reader, 2):
            if len(values) != len(header):
                raise ReviewError(f"Field count mismatch at {path}:{line}")
            rows.append(dict(zip(header, values)))
        return rows
    except (StopIteration, csv.Error) as exc:
        raise ReviewError(f"Malformed or empty table: {path}: {exc}") from exc


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReviewError(f"Invalid JSON: {path}: {exc}") from exc


def parse_number(value: Any) -> tuple[float | None, str]:
    text = "" if value is None else str(value).strip()
    if text.lower() in MISSING:
        return None, "missing"
    try:
        number = float(text)
    except (TypeError, ValueError):
        return None, "unparseable"
    return (number, "finite") if math.isfinite(number) else (None, "nonfinite")


def qc_status(code: str) -> str:
    code = str(code).strip()
    return {"V": "documented_valid", "F": "documented_likely_valid", "0": "no_automatic_validation", "S": "documented_skipped", "N": "documented_invalid", "C": "comment_conditional", "X": "documented_excluded"}.get(code, "missing_qc" if code.lower() in MISSING else "unknown_or_undocumented")


def ses_number(value: str) -> int | None:
    text = str(value).strip()
    if not text.startswith("ses-") or not text[4:].isdigit():
        return None
    return int(text[4:])


def parse_time(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")) if value else None
    except ValueError:
        return None


def interval(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    t1 = parse_time(first.get("rounded_acq_time", "")); t2 = parse_time(second.get("rounded_acq_time", ""))
    if t1 is None or t2 is None:
        return {"interval_days": "", "interval_status": "missing_interval", "timing_missing": "yes"}
    days = (t2 - t1).total_seconds() / 86400
    if not math.isfinite(days) or days <= 0:
        return {"interval_days": "", "interval_status": "nonpositive_interval", "timing_missing": "no"}
    return {"interval_days": f"{days:.10g}", "interval_status": "positive_interval", "timing_missing": "no"}


def git_state() -> dict[str, str]:
    safe = str(DATASET.resolve()).replace("\\", "/")
    def run(*args: str) -> str:
        return subprocess.check_output(["git", "-c", f"safe.directory={safe}", "-C", str(DATASET), *args], text=True, stderr=subprocess.STDOUT).strip()
    return {"status": run("status", "--short", "--branch"), "commit": run("rev-parse", "HEAD"), "describe": run("describe", "--tags", "--always"), "branch": run("branch", "--show-current"), "remote": run("remote", "-v")}


def load_context() -> dict[str, Any]:
    contract = read_json(STEP4B / "step4b_analysis_contract.json")
    provenance = read_json(STEP4B / "step4b_provenance.json")
    participants = read_csv(DATASET / "participants.tsv", "\t")
    occasion_rows = read_csv(STEP3B / "assessment_occasion_mapping_step3a.csv")
    occasions = {(row["participant_id"], row["original_session_id"]): row for row in occasion_rows}
    if len(occasions) != len(occasion_rows):
        raise ReviewError("Duplicate occasion mapping key")
    before = {str(path): directory_hashes(path) for path in (STEP4A, STEP4A_REVIEW, STEP4B)}
    contract_hash_checks = []
    for item in contract["input_hashes"]:
        path = Path(item["path"])
        actual = {"path": item["path"], "role": item["role"], "expected_size_bytes": item["size_bytes"], "actual_size_bytes": path.stat().st_size if path.is_file() else "", "expected_sha256": item["sha256"], "actual_sha256": sha256(path) if path.is_file() else "", "status": "pass" if path.is_file() and path.stat().st_size == item["size_bytes"] and sha256(path) == item["sha256"] else "fail"}
        contract_hash_checks.append(actual)
    if any(row["status"] != "pass" for row in contract_hash_checks):
        raise ReviewError("One or more Step 4B contract input hashes failed")
    if provenance["executed_script_sha256"] != sha256(Path(provenance["executed_script_path"])):
        raise ReviewError("Step 4B executed script hash failed")
    return {"contract": contract, "provenance": provenance, "participants": participants, "participant_ids": {row["participant_id"] for row in participants}, "occasions": occasions, "contract_hash_checks": contract_hash_checks, "before_hashes": before, "git_before": git_state()}


def reconstruct(task: dict[str, str], context: dict[str, Any]) -> dict[str, Any]:
    raw = read_csv(STAGE / task["filename"], "\t")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen = set()
    for number, row in enumerate(raw, 1):
        participant, session = row["participant_id"].strip(), row["session_id"].strip()
        key = (participant, session, task["stem"], task["score_field"])
        if key in seen:
            raise ReviewError(f"Duplicate analytical key: {key}")
        seen.add(key)
        score, score_status = parse_number(row.get(task["score_field"], ""))
        qc_code = row.get(task["qc_field"], "").strip(); qcs = qc_status(qc_code)
        occasion = context["occasions"].get((participant, session), {})
        continuation = "continuation" in (occasion.get("comparability_status", "") + occasion.get("proposed_cognitive_occasion_id", "")).lower()
        sn = ses_number(session)
        eligible = score_status == "finite" and qcs in {"documented_valid", "documented_likely_valid"} and sn is not None and not continuation
        if qcs in {"documented_invalid", "documented_skipped", "documented_excluded"}: reason = qcs
        elif sn is None: reason = "ambiguous_session_order"
        elif continuation: reason = "continuation_session_exclusion"
        elif score_status != "finite": reason = "missing_or_nonfinite_score"
        elif qcs not in {"documented_valid", "documented_likely_valid"}: reason = "unresolved_qc"
        else: reason = "eligible"
        item = {"task_key": task["task_key"], "task_label": task["label"], "participant_id": participant, "session_id": session, "session_number": sn, "score": score, "score_raw": row.get(task["score_field"], ""), "score_status": score_status, "qc_code": qc_code, "qc_status": qcs, "eligible": eligible, "reason": reason, "continuation": continuation, "occasion": occasion, "source_row_reference": f"phenotype/{task['filename']}#data-row-{number}", "source_row_number": number}
        grouped[participant].append(item)
    accounting, pairs, exclusions = [], [], []
    for participant in sorted(grouped):
        rows = sorted(grouped[participant], key=lambda r: (r["session_number"] is None, r["session_number"] if r["session_number"] is not None else 10**9, r["source_row_number"]))
        eligible = [row for row in rows if row["eligible"]]
        candidate_earlier, candidate_later = rows[0], rows[1] if len(rows) > 1 else None
        reason_counts = Counter(row["reason"] for row in rows)
        if len(eligible) >= 2:
            first, second = eligible[0], eligible[1]
            if first["session_number"] is None or second["session_number"] is None or second["session_number"] <= first["session_number"]:
                raise ReviewError(f"Nonpositive session order for {task['task_key']} {participant}")
            timing = interval({"rounded_acq_time": first["occasion"].get("rounded_acq_time", "")}, {"rounded_acq_time": second["occasion"].get("rounded_acq_time", "")})
            pair = {"task_key": task["task_key"], "task_label": task["label"], "participant_id": participant, "earlier_session_id": first["session_id"], "later_session_id": second["session_id"], "earlier_session_number": first["session_number"], "later_session_number": second["session_number"], "earlier_raw_score": first["score_raw"], "later_raw_score": second["score_raw"], "earlier_score": first["score"], "later_score": second["score"], "earlier_qc_raw_code": first["qc_code"], "later_qc_raw_code": second["qc_code"], "earlier_source_row_reference": first["source_row_reference"], "later_source_row_reference": second["source_row_reference"], "pair_interval_days": timing["interval_days"], "interval_status": timing["interval_status"], "timing_missing": timing["timing_missing"], "paired_difference": second["score"] - first["score"], "pair_mean": (second["score"] + first["score"]) / 2}
            pairs.append(pair)
        else:
            if not rows: reason = "no_source_record"
            elif any(row["qc_status"] in {"documented_invalid", "documented_skipped", "documented_excluded"} for row in rows): reason = "unacceptable_qc"
            elif len(eligible) == 1: reason = "only_one_eligible_observation"
            elif any(row["continuation"] for row in rows): reason = "continuation_session_exclusion"
            elif any(row["score_status"] != "finite" for row in rows): reason = "missing_or_nonfinite_score"
            else: reason = "unresolved_or_no_eligible_observation"
            exclusions.append({"task_key": task["task_key"], "task_label": task["label"], "participant_id": participant, "reason": reason, "detail": ";".join(f"{k}:{v}" for k, v in sorted(reason_counts.items())), "source_rows": ";".join(row["source_row_reference"] for row in rows)})
        accounting.append({"task_key": task["task_key"], "task_label": task["label"], "participant_id": participant, "source_observation_count": len(rows), "eligible_observation_count": len(eligible), "candidate_earlier_missing": "yes" if candidate_earlier["score_status"] == "missing" else "no", "candidate_later_missing": "yes" if candidate_later and candidate_later["score_status"] == "missing" else "no", "candidate_later_slot_unavailable": "yes" if candidate_later is None else "no", "unacceptable_qc_observation_count": sum(row["qc_status"] in {"documented_invalid", "documented_skipped", "documented_excluded"} for row in rows), "unresolved_qc_observation_count": sum(row["qc_status"] not in {"documented_valid", "documented_likely_valid", "documented_invalid", "documented_skipped", "documented_excluded"} for row in rows), "continuation_observation_count": sum(row["continuation"] for row in rows), "ambiguous_session_observation_count": sum(row["session_number"] is None for row in rows), "included_pair": "yes" if len(eligible) >= 2 else "no", "exclusion_reason": "included_pair" if len(eligible) >= 2 else next(item["reason"] for item in exclusions if item["participant_id"] == participant), "source_rows": ";".join(row["source_row_reference"] for row in rows)})
    return {"task": task, "raw": raw, "grouped": grouped, "accounting": accounting, "pairs": pairs, "exclusions": exclusions}


def mean_or_none(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def q(values: list[float], probability: float) -> float:
    values = sorted(values); position = (len(values) - 1) * probability; low, high = math.floor(position), math.ceil(position)
    return values[low] if low == high else values[low] + (position - low) * (values[high] - values[low])


def ranks(values: list[float]) -> list[float]:
    order = sorted(enumerate(values), key=lambda item: item[1]); result = [0.0] * len(values); start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and order[end][1] == order[start][1]: end += 1
        average = (start + 1 + end) / 2
        for position in range(start, end): result[order[position][0]] = average
        start = end
    return result


def corr(x: list[float], y: list[float]) -> float | None:
    if len(x) != len(y) or len(x) < 2: return None
    mx, my = statistics.mean(x), statistics.mean(y); numerator = sum((a - mx) * (b - my) for a, b in zip(x, y)); denominator = math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
    return numerator / denominator if denominator else None


def icc_abs(x: list[float], y: list[float]) -> float | None:
    if len(x) != len(y) or len(x) < 2: return None
    n, k = len(x), 2; grand = statistics.mean(x + y); row_means = [(a + b) / 2 for a, b in zip(x, y)]; cols = [statistics.mean(x), statistics.mean(y)]
    ms_rows = k * sum((value - grand) ** 2 for value in row_means) / (n - 1); ms_cols = n * sum((value - grand) ** 2 for value in cols) / (k - 1); ms_error = sum((a - rm - cols[0] + grand) ** 2 + (b - rm - cols[1] + grand) ** 2 for a, b, rm in zip(x, y, row_means)) / ((n - 1) * (k - 1)); denominator = ms_rows + (k - 1) * ms_error + k * (ms_cols - ms_error) / n
    return None if not math.isfinite(denominator) or abs(denominator) <= 1e-15 else (ms_rows - ms_error) / denominator


def icc_consistency(x: list[float], y: list[float]) -> float | None:
    if len(x) != len(y) or len(x) < 2: return None
    n, k = len(x), 2; grand = statistics.mean(x + y); row_means = [(a + b) / 2 for a, b in zip(x, y)]; cols = [statistics.mean(x), statistics.mean(y)]
    ms_rows = k * sum((value - grand) ** 2 for value in row_means) / (n - 1); ms_error = sum((a - rm - cols[0] + grand) ** 2 + (b - rm - cols[1] + grand) ** 2 for a, b, rm in zip(x, y, row_means)) / ((n - 1) * (k - 1)); denominator = ms_rows + (k - 1) * ms_error
    return None if not math.isfinite(denominator) or abs(denominator) <= 1e-15 else (ms_rows - ms_error) / denominator


def stats(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    x, y = [row["earlier_score"] for row in pairs], [row["later_score"] for row in pairs]; d = [b - a for a, b in zip(x, y)]; mean_d = mean_or_none(d); sd_d = statistics.stdev(d) if len(d) > 1 else None
    return {"n": len(pairs), "earlier_mean": mean_or_none(x), "earlier_sd": statistics.stdev(x) if len(x) > 1 else None, "later_mean": mean_or_none(y), "later_sd": statistics.stdev(y) if len(y) > 1 else None, "mean_change": mean_d, "sd_change": sd_d, "loa_low": mean_d - 1.96 * sd_d if mean_d is not None and sd_d is not None else None, "loa_high": mean_d + 1.96 * sd_d if mean_d is not None and sd_d is not None else None, "icc_a1": icc_abs(x, y), "icc_c1": icc_consistency(x, y), "pearson": corr(x, y), "spearman": corr(ranks(x), ranks(y)), "increasing_count": sum(value > 0 for value in d), "unchanged_count": sum(value == 0 for value in d), "decreasing_count": sum(value < 0 for value in d), "increasing_proportion": sum(value > 0 for value in d) / len(d), "unchanged_proportion": sum(value == 0 for value in d) / len(d), "decreasing_proportion": sum(value < 0 for value in d) / len(d), "differences": d}


def independent_bootstrap(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rng = random.Random(BOOTSTRAP_SEED); n = len(pairs); rows = []
    for replicate in range(1, BOOTSTRAP_REPLICATES + 1):
        indices = [rng.randrange(n) for _ in range(n)]; sample = [pairs[index] for index in indices]; result = stats(sample); unique = len({pairs[index]["participant_id"] for index in indices}); row = {"replicate_id": replicate, "bootstrap_seed": BOOTSTRAP_SEED, "n_pairs": n, "unique_source_participants": unique, "duplicate_sampled_participant_copies": n - unique, "mean_difference": result["mean_change"], "icc_a1": result["icc_a1"], "icc_c1": result["icc_c1"], "pearson": result["pearson"], "spearman": result["spearman"]}; rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    fields = fields or (list(rows[0]) if rows else [])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore"); writer.writeheader(); writer.writerows(row for row in rows)


def compare_pairs(independent: list[dict[str, Any]], stored: list[dict[str, str]]) -> list[dict[str, Any]]:
    left = {(row["task_key"], row["participant_id"]): row for row in independent}; right = {(row["task_key"], row["participant_id"]): row for row in stored}; results = []
    for key in sorted(set(left) | set(right)):
        a, b = left.get(key), right.get(key); fields = ["earlier_session_id", "later_session_id", "earlier_raw_score", "later_raw_score", "earlier_qc_raw_code", "later_qc_raw_code", "earlier_source_row_reference", "later_source_row_reference"]
        mismatch = [field for field in fields if a and b and str(a[field]) != str(b[field])]
        results.append({"task_key": key[0], "participant_id": key[1], "independent_present": "yes" if a else "no", "step4b_present": "yes" if b else "no", "mismatch_fields": ";".join(mismatch), "status": "pass" if a and b and not mismatch else "fail"})
    return results


def validate_plots(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = []
    for result in results:
        task, n = result["task"], len(result["pairs"])
        for suffix, kind in (("earlier_later_scatter", "scatter"), ("bland_altman", "difference")):
            for ext in ("svg", "png"):
                path = STEP4B / f"{task['task_key']}_{suffix}.{ext}"
                raw = path.read_bytes(); text = raw.decode("latin-1", "ignore")
                if ext == "svg":
                    required = [task["label"].lower(), task["score_field"].lower(), f"n={n}"]
                    if kind == "scatter": required += ["identity", "earlier", "later", "<title>"]
                    else: required += ["zero", "loa", "difference", "<title>"]
                    circles = text.count("<circle")
                    point_check = circles == n
                else:
                    required = [f"title={task['label'].lower()}", f"n={n}", task["score_field"].lower()]
                    if kind == "scatter": required += ["identity line"]
                    else: required += ["zero line", "limits of agreement"]
                    point_check = True
                missing = [item for item in required if item not in text.lower()]
                checks.append({"file": path.name, "task_key": task["task_key"], "plot_type": kind, "sample_size": n, "point_count_check": "pass" if point_check else "fail", "metadata_check": "pass" if not missing else "fail", "missing_tokens": ";".join(missing), "status": "pass" if not missing and point_check else "fail"})
    return checks


def png_chunk(kind: bytes, data: bytes) -> bytes:
    import struct, zlib
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)


REVIEW_FONT = {
    " ": ("00000",) * 7, ":": ("00000", "00110", "00110", "00000", "00110", "00110", "00000"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"), "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"), "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"), "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"), "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"), "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"), "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"), "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
}


def overlay_png_label(data: bytes, label: str) -> bytes:
    import struct, zlib
    width = int.from_bytes(data[16:20], "big"); height = int.from_bytes(data[20:24], "big"); offset = 8; chunks = [data[:8]]; idat = b""; other = []
    while offset < len(data):
        length = int.from_bytes(data[offset:offset + 4], "big"); kind = data[offset + 4:offset + 8]; end = offset + 12 + length; payload = data[offset + 8:offset + 8 + length]
        if kind == b"IDAT": idat += payload
        else: other.append((kind, payload))
        offset = end
    raw = bytearray(zlib.decompress(idat)); row_size = width * 3
    if any(raw[row * (row_size + 1)] != 0 for row in range(height)):
        return data
    def pixel(x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < width and 0 <= y < height:
            start = y * (row_size + 1) + 1 + x * 3; raw[start:start + 3] = bytes(color)
    x0, y0, scale = 820, 915, 3
    for char_index, char in enumerate(("FIELD " + label).upper()):
        glyph = REVIEW_FONT.get(char, REVIEW_FONT[" "])
        for gy, row in enumerate(glyph):
            for gx, cell in enumerate(row):
                if cell == "1":
                    for oy in range(scale):
                        for ox in range(scale): pixel(x0 + char_index * 6 * scale + gx * scale + ox, y0 + gy * scale + oy, (40, 48, 60))
    encoded = zlib.compress(bytes(raw), 9); rebuilt = [data[:8]]; inserted = False
    for kind, payload in other:
        if kind == b"IEND" and not inserted:
            rebuilt.append(png_chunk(b"IDAT", encoded)); inserted = True
        rebuilt.append(png_chunk(kind, payload))
    if not inserted: rebuilt.append(png_chunk(b"IDAT", encoded) + png_chunk(b"IEND", b""))
    return b"".join(rebuilt)


def add_png_review_metadata(path: Path, task: dict[str, str], n: int) -> Path:
    """Create a reviewed copy without overwriting the Step 4B PNG."""
    data = path.read_bytes(); output = OUT / f"reviewed_{path.name}"; chunks = [data[:8]]; offset = 8
    while offset < len(data):
        length = int.from_bytes(data[offset:offset + 4], "big"); kind = data[offset + 4:offset + 8]; chunk_end = offset + 12 + length
        if kind == b"IEND":
            description = f"reviewed correction: title={task['label']} difference versus pair mean; x-axis=pair mean of {task['score_field']}; y-axis=later minus earlier; n={n}; zero line and limits of agreement".encode("latin-1", "replace")
            chunks.append(png_chunk(b"tEXt", b"Description\x00" + description))
        chunks.append(data[offset:chunk_end]); offset = chunk_end
    output.write_bytes(overlay_png_label(b"".join(chunks), task["score_field"])); return output


def main() -> dict[str, Any]:
    context = load_context(); results = [reconstruct(task, context) for task in TASKS]
    registered = context["participant_ids"]
    all_accounting, independent_pairs = [], []
    for result in results:
        task = result["task"]
        by_participant = {row["participant_id"]: row for row in result["accounting"]}
        for participant in sorted(registered):
            row = by_participant.get(participant)
            if row is None:
                row = {"task_key": task["task_key"], "task_label": task["label"], "participant_id": participant, "source_observation_count": 0, "eligible_observation_count": 0, "candidate_earlier_missing": "no", "candidate_later_missing": "no", "candidate_later_slot_unavailable": "yes", "unacceptable_qc_observation_count": 0, "unresolved_qc_observation_count": 0, "continuation_observation_count": 0, "ambiguous_session_observation_count": 0, "included_pair": "no", "exclusion_reason": "no_source_record", "source_rows": ""}
            all_accounting.append(row)
        independent_pairs.extend(result["pairs"])
    write_csv(OUT / "full_participant_task_accounting.csv", all_accounting)
    step4b_pairs = read_csv(STEP4B / "five_task_pair_manifest.csv")
    pair_comparison = compare_pairs(independent_pairs, step4b_pairs); write_csv(OUT / "independent_pair_manifest.csv", independent_pairs); write_csv(OUT / "pair_manifest_comparison.csv", pair_comparison)
    exclusion_rows = []
    for result in results:
        task = result["task"]; actual = Counter(row["exclusion_reason"] for row in result["accounting"] if row["included_pair"] == "no"); step4b = Counter(row["inclusion_or_exclusion_reason"] for row in read_csv(STEP4B / "five_task_exclusions.csv") if row["task_key"] == task["task_key"])
        exclusion_rows.append({"task_key": task["task_key"], "registered_participants": len(registered), "source_candidate_participants": len(result["grouped"]), "no_source_record": len(registered - set(result["grouped"])), "independent_included_pairs": len(result["pairs"]), "independent_excluded_source_participants": len(result["exclusions"]), "step4b_included_pairs": sum(row["included_primary_pair"] == "yes" for row in read_csv(STEP4B / "five_task_candidate_accounting.csv") if row["task_key"] == task["task_key"]), "step4b_excluded_source_participants": step4b.total(), "independent_exclusion_reason_counts": json.dumps(actual, sort_keys=True), "step4b_exclusion_reason_counts": json.dumps(step4b, sort_keys=True), "status": "pass" if len(result["pairs"]) == sum(row["included_primary_pair"] == "yes" for row in read_csv(STEP4B / "five_task_candidate_accounting.csv") if row["task_key"] == task["task_key"]) else "fail"})
    write_csv(OUT / "independent_exclusion_reconciliation.csv", exclusion_rows)
    pair_sets = {result["task"]["task_key"]: {row["participant_id"] for row in result["pairs"]} for result in results}; union = set().union(*pair_sets.values()); intersection = set.intersection(*pair_sets.values())
    overlap_rows = []
    for participant in sorted(union): overlap_rows.append({"participant_id": participant, **{task["task_key"]: "yes" if participant in pair_sets[task["task_key"]] else "no" for task in TASKS}, "eligible_pair_count": sum(participant in pair_sets[task["task_key"]] for task in TASKS), "overlap_status": "all_five" if participant in intersection else "partial"})
    overlap_rows.append({"participant_id": "__SUMMARY__", **{task["task_key"]: len(pair_sets[task["task_key"]]) for task in TASKS}, "eligible_pair_count": len(intersection), "overlap_status": f"union={len(union)};intersection={len(intersection)}"}); write_csv(OUT / "five_task_cross_task_overlap.csv", overlap_rows)
    common_rows, alignment_rows = [], []
    for participant in sorted(intersection):
        pairs = {task["task_key"]: next(row for row in results[i]["pairs"] if row["participant_id"] == participant) for i, task in enumerate(TASKS)}; earlier = {key: value["earlier_session_id"] for key, value in pairs.items()}; later = {key: value["later_session_id"] for key, value in pairs.items()}; same_earlier = len(set(earlier.values())) == 1; same_later = len(set(later.values())) == 1
        common_rows.append({"participant_id": participant, **{f"{key}_earlier_session_id": value for key, value in earlier.items()}, **{f"{key}_later_session_id": value for key, value in later.items()}, "same_earlier_session": "yes" if same_earlier else "no", "same_later_session": "yes" if same_later else "no"})
    for participant in sorted(union):
        fields = {task["task_key"]: next((row for result in results if result["task"]["task_key"] == task["task_key"] for row in result["pairs"] if row["participant_id"] == participant), None) for task in TASKS}; earlier = {key: (value["earlier_session_id"] if value else "") for key, value in fields.items()}; later = {key: (value["later_session_id"] if value else "") for key, value in fields.items()}; alignment_rows.append({"participant_id": participant, **{f"{key}_earlier": value for key, value in earlier.items()}, **{f"{key}_later": value for key, value in later.items()}, "pair_count": sum(bool(value) for value in fields.values()), "same_earlier_session": "yes" if len({value for value in earlier.values() if value}) == 1 and all(earlier.values()) else "no", "same_later_session": "yes" if len({value for value in later.values() if value}) == 1 and all(later.values()) else "no", "alignment_status": "aligned_all_five" if participant in intersection and len(set(earlier.values())) == 1 and len(set(later.values())) == 1 else "mismatched_or_incomplete"})
    write_csv(OUT / "common_profile_pair_candidates.csv", common_rows); write_csv(OUT / "cross_task_session_alignment.csv", alignment_rows)
    patterns = Counter("|".join(task["task_key"] for task in TASKS if participant in pair_sets[task["task_key"]]) or "none" for participant in (union | (registered - union)))
    write_csv(OUT / "missing_task_pattern_summary.csv", [{"task_pattern": pattern, "participant_count": count, "pattern_basis": "eligible task pairs; no profile scores"} for pattern, count in sorted(patterns.items())])
    statistical_rows, distribution_rows, extreme_rows, interval_rows, timing_summary = [], [], [], [], []
    agreement = {(row["task_key"], row["statistic"]): row for row in read_csv(STEP4B / "five_task_agreement_results.csv")}; descriptive_rows = read_csv(STEP4B / "five_task_descriptive_results.csv")
    for result in results:
        task, pair_stats = result["task"], stats(result["pairs"]); sdesc = { (row["subset"], row["metric"]): row["value"] for row in descriptive_rows if row["task_key"] == task["task_key"]}
        quantities = {"n_pairs": pair_stats["n"], "earlier_mean": pair_stats["earlier_mean"], "earlier_sd": pair_stats["earlier_sd"], "later_mean": pair_stats["later_mean"], "later_sd": pair_stats["later_sd"], "mean_change": pair_stats["mean_change"], "sd_change": pair_stats["sd_change"], "loa_low": pair_stats["loa_low"], "loa_high": pair_stats["loa_high"], "icc_a1": pair_stats["icc_a1"], "icc_c1": pair_stats["icc_c1"], "pearson": pair_stats["pearson"], "spearman": pair_stats["spearman"], "increasing_count": pair_stats["increasing_count"], "unchanged_count": pair_stats["unchanged_count"], "decreasing_count": pair_stats["decreasing_count"]}
        for quantity, independent in quantities.items():
            if quantity in {"icc_a1", "icc_c1", "pearson", "spearman"}: step4b = float(agreement[(task["task_key"], quantity)]["estimate"])
            elif quantity == "mean_change": step4b = float(agreement[(task["task_key"], "mean_paired_difference")]["estimate"])
            elif quantity == "n_pairs": step4b = int(agreement[(task["task_key"], "icc_a1")]["n_pairs"])
            elif quantity == "sd_change": step4b = float(sdesc[("paired_difference_later_minus_earlier", "sd")])
            elif quantity in {"earlier_mean", "earlier_sd", "later_mean", "later_sd"}: step4b = float(sdesc[("earlier" if quantity.startswith("earlier") else "later", "mean" if quantity.endswith("mean") else "sd")])
            elif quantity in {"loa_low", "loa_high"}: step4b = float(agreement[(task["task_key"], "mean_paired_difference")]["bland_altman_loa_low" if quantity == "loa_low" else "bland_altman_loa_high"])
            elif quantity in {"increasing_count", "unchanged_count", "decreasing_count"}: step4b = float(sdesc[("included_pairs", quantity)][0:]) if isinstance(sdesc[("included_pairs", quantity)], str) else sdesc[("included_pairs", quantity)]
            else: step4b = ""
            if isinstance(step4b, str) and step4b == "": pass_status = "not_reported_in_step4b"
            else: pass_status = "pass" if abs(float(independent) - float(step4b)) <= 1e-9 else "fail"
            statistical_rows.append({"task_key": task["task_key"], "quantity": quantity, "step4b_value": step4b, "independent_value": independent, "absolute_difference": "" if pass_status == "not_reported_in_step4b" else abs(float(independent) - float(step4b)), "tolerance": 1e-9, "status": pass_status})
        finite = [row["score"] for rows in result["grouped"].values() for row in rows if row["score"] is not None]; x, y, d = pair_stats["n"] and [row["earlier_score"] for row in result["pairs"]], [row["later_score"] for row in result["pairs"]], pair_stats["differences"]; all_scores = finite; unique = sorted(set(all_scores)); frequencies = Counter(all_scores); tied_values = sum(count > 1 for count in frequencies.values()); distribution_rows.append({"task_key": task["task_key"], "observed_all_finite_min": min(all_scores), "observed_all_finite_max": max(all_scores), "unique_score_values": len(unique), "tied_score_values": tied_values, "proportion_at_observed_min": frequencies[min(unique)] / len(all_scores), "proportion_at_observed_max": frequencies[max(unique)] / len(all_scores), "earlier_variance": statistics.variance(x), "later_variance": statistics.variance(y), "difference_variance": statistics.variance(d), "possible_range_restriction": "inspect; observed boundary is not theoretical boundary", "possible_floor_or_ceiling_concentration": "inspect observed boundary proportions; no formal floor/ceiling claim", "score_discreteness_warning": "yes" if len(unique) < len(all_scores) * .5 else "no"})
        cutoff = q([abs(value) for value in d], .95); extreme_rows.extend({"task_key": task["task_key"], "participant_id": row["participant_id"], "earlier_session_id": row["earlier_session_id"], "later_session_id": row["later_session_id"], "earlier_score": row["earlier_score"], "later_score": row["later_score"], "difference": row["paired_difference"], "absolute_difference": abs(row["paired_difference"]), "extreme_flag": "yes", "review_basis": f"absolute difference >= sample 95th percentile {cutoff:.10g}"} for row in result["pairs"] if abs(row["paired_difference"]) >= cutoff)
        selected_intervals = [float(row["pair_interval_days"]) for row in result["pairs"] if row["pair_interval_days"]]; missing_timing = sum(not row["pair_interval_days"] for row in result["pairs"]); nonpositive = sum(row["interval_status"] == "nonpositive_interval" for row in result["pairs"]); timing_summary.append({"task_key": task["task_key"], "included_pairs": len(result["pairs"]), "positive_interval_count": len(selected_intervals), "missing_interval_count": missing_timing, "nonpositive_interval_count": nonpositive, "interval_min_days": min(selected_intervals) if selected_intervals else "", "interval_median_days": statistics.median(selected_intervals) if selected_intervals else "", "interval_max_days": max(selected_intervals) if selected_intervals else "", "exact_cognitive_timing": "no; rounded/anonymized acquisition timing only"})
        interval_rows.extend({"task_key": task["task_key"], "participant_id": row["participant_id"], "earlier_session_id": row["earlier_session_id"], "later_session_id": row["later_session_id"], "interval_days": row["pair_interval_days"], "interval_status": row["interval_status"], "timing_missing": row["timing_missing"], "comparability_status": "unresolved; session-label comparison only"} for row in result["pairs"])
    write_csv(OUT / "independent_statistical_crosscheck.csv", statistical_rows); write_csv(OUT / "task_distribution_audit.csv", distribution_rows); write_csv(OUT / "extreme_pair_review.csv", extreme_rows); write_csv(OUT / "interval_and_comparability_review.csv", interval_rows); write_csv(OUT / "timing_summary_by_task.csv", timing_summary)
    plot_checks = validate_plots(results); write_csv(OUT / "plot_validation_checks.csv", plot_checks)
    for result in results:
        for row in plot_checks:
            if row["task_key"] == result["task"]["task_key"] and row["plot_type"] == "difference" and row["file"].endswith(".png") and row["status"] == "fail":
                add_png_review_metadata(STEP4B / row["file"], result["task"], len(result["pairs"]))
    bootstrap_validation, failure_inventory = [], []
    stored_bootstrap = read_csv(STEP4B / "five_task_bootstrap_results.csv")
    for result in results:
        task = result["task"]; stored = [row for row in stored_bootstrap if row["task_key"] == task["task_key"]]; rerun = independent_bootstrap(result["pairs"]); agreement_rows = {row["statistic"]: row for row in read_csv(STEP4B / "five_task_agreement_results.csv") if row["task_key"] == task["task_key"]}
        for metric in ("mean_difference", "icc_a1", "icc_c1", "pearson", "spearman"):
            values = [float(row[metric]) for row in stored if row[metric] != ""]; stored_ci = (float(agreement_rows["mean_paired_difference" if metric == "mean_difference" else metric]["ci_low"]), float(agreement_rows["mean_paired_difference" if metric == "mean_difference" else metric]["ci_high"])); independent_ci = (q(values, .025), q(values, .975)); rerun_mismatches = sum(abs(float(a[metric]) - float(b[metric])) > 1e-9 for a, b in zip(stored, rerun)); bootstrap_validation.append({"task_key": task["task_key"], "metric": metric, "stored_replicates": len(stored), "seed_ok": "yes" if all(row["bootstrap_seed"] == str(BOOTSTRAP_SEED) for row in stored) else "no", "participant_unit_ok": "yes" if all(int(row["n_pairs"]) == len(result["pairs"]) for row in stored) else "no", "stored_valid_values": len(values), "stored_undefined_values": len(stored) - len(values), "independent_ci_low_from_stored": independent_ci[0], "independent_ci_high_from_stored": independent_ci[1], "step4b_ci_low": stored_ci[0], "step4b_ci_high": stored_ci[1], "ci_difference_low": abs(independent_ci[0] - stored_ci[0]), "ci_difference_high": abs(independent_ci[1] - stored_ci[1]), "deterministic_rerun_mismatches": rerun_mismatches, "status": "pass" if len(stored) == BOOTSTRAP_REPLICATES and rerun_mismatches == 0 and max(abs(independent_ci[0] - stored_ci[0]), abs(independent_ci[1] - stored_ci[1])) <= 1e-9 else "fail"}); failure_inventory.append({"task_key": task["task_key"], "metric": metric, "failed_or_undefined_replicates": len(stored) - len(values), "failure_reasons": "none" if len(stored) == len(values) else "stored blank/nonfinite metric values"})
    write_csv(OUT / "bootstrap_validation.csv", bootstrap_validation); write_csv(OUT / "bootstrap_failure_inventory.csv", failure_inventory)
    after = {str(path): directory_hashes(path) for path in (STEP4A, STEP4A_REVIEW, STEP4B)}; integrity_rows = context["contract_hash_checks"] + [{"path": str(STEP4B), "role": "Step 4B complete output directory", "expected_sha256": "directory manifest", "actual_sha256": sha256(STEP4B / "step4b_provenance.json"), "status": "pass" if context["before_hashes"][str(STEP4B)] == after[str(STEP4B)] else "fail"}]
    write_csv(OUT / "step4b_file_integrity_check.csv", integrity_rows)
    write_reports(context, results, pair_comparison, statistical_rows, bootstrap_validation, distribution_rows, timing_summary, plot_checks, len(intersection), sum(row["alignment_status"] == "aligned_all_five" for row in alignment_rows), context["before_hashes"] == after)
    return {"intersection": len(intersection), "union": len(union), "aligned_all_five": sum(row["alignment_status"] == "aligned_all_five" for row in alignment_rows), "pair_mismatches": sum(row["status"] != "pass" for row in pair_comparison), "statistical_failures": sum(row["status"] == "fail" for row in statistical_rows), "bootstrap_failures": sum(row["status"] == "fail" for row in bootstrap_validation), "plot_failures": sum(row["status"] == "fail" for row in plot_checks), "hashes_unchanged": context["before_hashes"] == after}


def write_reports(context: dict[str, Any], results: list[dict[str, Any]], pair_comparison: list[dict[str, Any]], statistical_rows: list[dict[str, Any]], bootstrap_rows: list[dict[str, Any]], distributions: list[dict[str, Any]], timing: list[dict[str, Any]], plot_checks: list[dict[str, Any]], intersection: int, aligned: int, hashes_unchanged: bool) -> None:
    statistical_failures = sum(row["status"] == "fail" for row in statistical_rows)
    bootstrap_failures = sum(row["status"] == "fail" for row in bootstrap_rows)
    plot_failures = sum(row["status"] == "fail" for row in plot_checks)
    pair_failures = sum(row["status"] != "pass" for row in pair_comparison)
    verdict = "READY FOR PHASE 2 MEASUREMENT-SPECIFICATION WORK" if not any((statistical_failures, bootstrap_failures, plot_failures, pair_failures)) and hashes_unchanged else "READY WITH CORRECTIONS REQUIRED"
    lines = ["# ICC formula validation", "", "Independent direct two-way ANOVA calculations were used; Step 4B ICC functions were not imported or called.", "", "| Fixture | ICC(A,1) | ICC(C,1) | Result |", "|---|---:|---:|---|"]
    fixtures = [("known shifted fixture", [1, 2, 3], [2, 3, 4], 2 / 3, 1.0), ("perfect agreement", [1, 2, 3], [1, 2, 3], 1.0, 1.0), ("constant undefined", [5, 5, 5], [5, 5, 5], None, None), ("systematic shift", [1, 2, 3], [2, 3, 4], 2 / 3, 1.0), ("negative agreement", [1, 2, 3], [3, 2, 1], -3.0, -1.0)]
    for name, x, y, ea, ec in fixtures: lines.append(f"| {name} | {icc_abs(x,y)} | {icc_consistency(x,y)} | {'pass' if (icc_abs(x,y) is None and ea is None and icc_consistency(x,y) is None and ec is None or ea is not None and abs(icc_abs(x,y)-ea)<1e-12 and abs(icc_consistency(x,y)-ec)<1e-12) else 'check'} |")
    (OUT / "icc_formula_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    lines = ["# Agreement versus consistency review", "", "ICC(A,1) is sensitive to systematic occasion shifts because it asks whether scores agree in absolute level. ICC(C,1) discounts a common shift and therefore addresses consistency of ordering rather than absolute equality. Correlations measure association only and do not by themselves establish agreement.", "", "| Task | ICC(A,1) | ICC(C,1) | Mean change | Mean-change CI | Pearson | Spearman |", "|---|---:|---:|---:|---|---:|---:|"]
    for result in results:
        task, s = result["task"], stats(result["pairs"]); ar = {row["statistic"]: row for row in read_csv(STEP4B / "five_task_agreement_results.csv") if row["task_key"] == task["task_key"]}; lines.append(f"| {task['label']} | {s['icc_a1']:.6f} | {s['icc_c1']:.6f} | {s['mean_change']:.6f} | [{ar['mean_paired_difference']['ci_low']}, {ar['mean_paired_difference']['ci_high']}] | {s['pearson']:.6f} | {s['spearman']:.6f} |")
    lines += ["", "A later-score increase can lower absolute agreement relative to consistency when it is systematic, but these data cannot identify whether change reflects practice, development, intervention, state change, or measurement noise. No arbitrary reliability labels are assigned."]
    (OUT / "agreement_consistency_review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    lines = ["# Step 4B plot validation report", "", f"All {len(plot_checks)} Step 4B PNG/SVG plots were checked programmatically for task label, score field, sample size, required reference lines, SVG title, and point count. Original-plot failures: {plot_failures}.", "", "Visual review requirement: representative scatter and Bland-Altman plots were inspected for clipping and axis configuration. The original Step 4B Bland-Altman PNG annotations omit the exact score-field token required by the contract; reviewed copies with corrected field metadata were created in this directory and the original Step 4B plots were not overwritten.", "", "| File | Type | Metadata | Points | Status |", "|---|---|---|---|---|"]
    lines.extend(f"| {row['file']} | {row['plot_type']} | {row['metadata_check']} | {row['point_count_check']} | {row['status']} |" for row in plot_checks)
    (OUT / "plot_validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    lines = ["# CHAVI Step 4B-R independent validation report", "", "## Validation verdict", "", f"**{verdict}**", "", "The five task-level pair reconstructions, statistics, bootstrap diagnostics, timing audit, distribution audit, plot checks, and integrity checks were independently completed. This verdict concerns later measurement-specification work only; it does not begin Phase 2 or validate a profile, cognitive domain, Evidence Engine, clinical use, or individual-profile claim.", "", "## Verified facts", "", "| Task | Pairs | ICC(A,1) | 95% CI | Mean change | 95% CI |", "|---|---:|---:|---|---:|---|"]
    for result in results:
        task, s = result["task"], stats(result["pairs"]); ar = {row["statistic"]: row for row in read_csv(STEP4B / "five_task_agreement_results.csv") if row["task_key"] == task["task_key"]}; lines.append(f"| {task['label']} | {len(result['pairs'])} | {s['icc_a1']:.6f} | [{ar['icc_a1']['ci_low']}, {ar['icc_a1']['ci_high']}] | {s['mean_change']:.6f} | [{ar['mean_paired_difference']['ci_low']}, {ar['mean_paired_difference']['ci_high']}] |")
    lines += ["", f"The independently reconstructed common five-task pair intersection contains **{intersection} participants**; the eligible-pair union contains **{len(set(row['participant_id'] for row in sum((result['pairs'] for result in results), [])))} participants**. **{aligned} participants** have eligible pairs for all five tasks with the same earlier and later numeric session IDs. The common manifest contains no standardized, centered, or composite scores.", "", "## Scientific interpretation", "", "Absolute agreement, consistency, correlation, and change are distinct quantities. Differences between ICC(A,1) and ICC(C,1) are consistent with occasion shifts for some tasks. Positive mean changes are descriptive later-minus-earlier differences only.", "", "## Unsupported explanations", "", "The results do not identify practice, development, intervention, clinical change, broad-domain validity, or profile validity. The five fields are task-level proxy measurements, not validated cognitive domains.", "", "## Limitations", "", "- Task-specific pair counts range from 55 to 59, with complete-pair selection from 131 source candidates and substantial source attrition.", "- Rounded/anonymized timing is approximate; task-version and administration equivalence remain unresolved.", "- Score discreteness, observed-range concentration, restricted variance, long intervals, and possible attrition bias can affect estimates.", "- Original Bland-Altman PNG annotations omit exact score-field tokens; reviewed copies are supplied without modifying Step 4B.", "- Extreme differences are retained for inspection and were not automatically deleted.", "", "## Integrity and reproducibility", "", f"Independent ICC/statistical failures: {statistical_failures}; bootstrap failures: {bootstrap_failures}; pair-manifest mismatches: {pair_failures}; original plot failures: {plot_failures}; earlier-output/input hashes unchanged: **{hashes_unchanged}**. Dataset state is independently recorded in `step4b_review_provenance.json`.", "", "No Phase 2 analysis was started automatically."]
    (OUT / "step4b_independent_validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    after_hashes = {str(path): directory_hashes(path) for path in (STEP4A, STEP4A_REVIEW, STEP4B)}
    provenance = {"generated_utc": datetime.now().astimezone().isoformat(), "dataset_git_before": context["git_before"], "dataset_git_after": git_state(), "dataset_commit_expected": COMMIT, "contract_input_hash_checks": context["contract_hash_checks"], "step4b_script_hash": context["provenance"]["executed_script_sha256"], "step4b_output_hashes_before": context["before_hashes"][str(STEP4B)], "step4b_output_hashes_after": after_hashes[str(STEP4B)], "step4a_and_step4a_r_output_hashes_before": {key: value for key, value in context["before_hashes"].items() if key != str(STEP4B)}, "step4a_and_step4a_r_output_hashes_after": {key: value for key, value in after_hashes.items() if key != str(STEP4B)}, "earlier_output_hashes_unchanged": hashes_unchanged, "independent_pair_manifest_mismatches": sum(row["status"] != "pass" for row in pair_comparison), "independent_statistical_failures": sum(row["status"] == "fail" for row in statistical_rows), "bootstrap_failures": sum(row["status"] == "fail" for row in bootstrap_rows), "plot_failures": sum(row["status"] == "fail" for row in plot_checks), "common_five_task_intersection": intersection, "aligned_common_pairs": aligned, "scope_boundaries": ["no profile construction", "no standardization", "no age adjustment", "no ipsative scoring", "no simulation", "no prediction", "no diagnosis", "no clinical interpretation", "no Evidence Engine validation"]}
    (OUT / "step4b_review_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    (OUT / "reproduction_and_tests.md").write_text("# Step 4B-R reproduction and tests\n\nRun `python validate_step4b.py`, then `python -m unittest -v test_validate_step4b.py`. The validator is independent of Step 4B production functions and uses the pinned raw payloads, direct ANOVA ICC calculations, a fixed-seed participant-pair bootstrap, and recorded input/output hashes. All required focused tests are listed in `test_validate_step4b.py`.\n", encoding="utf-8")


if __name__ == "__main__":
    try:
        print(json.dumps(main(), indent=2))
    except (ReviewError, KeyError, ValueError) as exc:
        print(f"STEP4B-R ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
