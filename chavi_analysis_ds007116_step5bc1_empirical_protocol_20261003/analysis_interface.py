"""CHAVI Step 5B-C1 reusable empirical-analysis primitives.

The CLI defaults to metadata-only dry-run. Empirical endpoint calculation requires
the explicit ``--authorize-empirical-execution`` switch and is outside Step 5B-C1.
Only NumPy and the Python standard library are required.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np

TASK_ORDER = (
    "letter_nback", "face_memory", "matrix_reasoning",
    "emotion_recognition", "dominant_finger_tapping",
)
MODELS = {"M0", "M1"}
SCALES = {"MAD", "SD"}
DESIGN = "B_target_plus_auxiliary"
MAD_DENOMINATOR = 0.6744897501960817
EPS = np.finfo(np.float64).eps


class ContractError(ValueError):
    """Raised when input violates the frozen analysis contract."""


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _integer_weights(weights: Sequence[int], n: int) -> np.ndarray:
    w = np.asarray(weights)
    if w.shape != (n,) or np.issubdtype(w.dtype, np.bool_) or not np.issubdtype(w.dtype, np.integer):
        raise ContractError("weights must be an integer vector matching the identity count")
    if np.any(w < 0):
        raise ContractError("weights must be nonnegative")
    return w.astype(np.int64, copy=False)


def weighted_mean(x: Sequence[float], weights: Sequence[int]) -> float | None:
    a = np.asarray(x, dtype=np.float64); w = _integer_weights(weights, len(a)); keep = w > 0
    if not np.any(keep): return None
    a, w = a[keep], w[keep]
    if not np.all(np.isfinite(a)): raise ContractError("active nonfinite value")
    return float(np.dot(a, w) / w.sum())


def weighted_median(x: Sequence[float], weights: Sequence[int]) -> float | None:
    a = np.asarray(x, dtype=np.float64); w = _integer_weights(weights, len(a)); keep = w > 0
    if not np.any(keep): return None
    a, w = a[keep], w[keep]
    if not np.all(np.isfinite(a)): raise ContractError("active nonfinite value")
    order = np.argsort(a, kind="stable"); a, w = a[order], w[order]; cumulative = np.cumsum(w); total = int(w.sum())
    def at(rank: int) -> float: return float(a[np.searchsorted(cumulative, rank + 1, side="left")])
    return at(total // 2) if total % 2 else (at(total // 2 - 1) + at(total // 2)) / 2.0


def weighted_sd(x: Sequence[float], weights: Sequence[int]) -> float | None:
    a = np.asarray(x, dtype=np.float64); w = _integer_weights(weights, len(a)); keep = w > 0
    a, w = a[keep], w[keep]; total = int(w.sum())
    if total < 2: return None
    if not np.all(np.isfinite(a)): raise ContractError("active nonfinite value")
    mean = float(np.dot(a, w) / total)
    return math.sqrt(float(np.dot(w, (a - mean) ** 2)) / (total - 1))


def weighted_mad(x: Sequence[float], weights: Sequence[int]) -> float | None:
    median = weighted_median(x, weights)
    if median is None: return None
    raw = weighted_median(np.abs(np.asarray(x, dtype=np.float64) - median), weights)
    return None if raw is None else raw / MAD_DENOMINATOR


def validate_scale(values: Sequence[float], weights: Sequence[int], scale: float | None) -> None:
    a = np.asarray(values, dtype=np.float64); w = _integer_weights(weights, len(a)); active = a[w > 0]
    if scale is None or not math.isfinite(scale) or scale <= 0:
        raise ContractError("nonpositive_or_nonfinite_scale")
    if len(active) < 2: raise ContractError("insufficient_scale_observations")
    if not np.all(np.isfinite(active)): raise ContractError("active_nonfinite_reference_value")
    data_range = float(active.max() - active.min())
    if scale <= 64 * EPS * max(data_range, abs(scale)):
        raise ContractError("numerically_degenerate_scale")


def fit_task_reference(values: Sequence[float], ages: Sequence[float], weights: Sequence[int],
                       model: str, scale_method: str) -> dict:
    """Fit one task from raw reference observations using frequency weights."""
    y = np.asarray(values, dtype=np.float64); age = np.asarray(ages, dtype=np.float64)
    if y.shape != age.shape: raise ContractError("value/age shape mismatch")
    w = _integer_weights(weights, len(y)); active = w > 0
    y, age, w = y[active], age[active], w[active]
    if not np.all(np.isfinite(y)): raise ContractError("active nonfinite reference score")
    if model == "M0":
        center = weighted_mean(y, w); residual = y - center; intercept, slope = center, 0.0
        age_min = age_max = None
    elif model == "M1":
        if len(y) < 2 or int(w.sum()) < 3 or not np.all(np.isfinite(age)) or len(np.unique(age)) < 2:
            raise ContractError("insufficient_effective_training_data")
        expanded_age = np.repeat(age, w); expanded_y = np.repeat(y, w)
        age_origin = float(expanded_age.mean()); x = expanded_age - age_origin
        denominator = float(np.dot(x, x))
        if denominator <= 64 * EPS * max(float(np.dot(expanded_age, expanded_age)), 1.0):
            raise ContractError("rank_deficient_age_model")
        slope = float(np.dot(x, expanded_y - expanded_y.mean()) / denominator)
        intercept = float(expanded_y.mean() - slope * age_origin)
        residual = y - (intercept + slope * age)
        center = 0.0; age_min, age_max = float(age.min()), float(age.max())
    else: raise ContractError("unknown model")
    if scale_method == "MAD": scale = weighted_mad(residual, w)
    elif scale_method == "SD": scale = weighted_sd(residual, w)
    else: raise ContractError("unknown scale")
    validate_scale(residual, w, scale)
    return {"model": model, "scale_method": scale_method, "center": float(center), "intercept": float(intercept),
            "slope": float(slope), "scale": float(scale), "age_min": age_min, "age_max": age_max,
            "frequency_n": int(w.sum())}


def transform_task(raw_score: float, age: float, fit: Mapping) -> tuple[float | None, bool, str]:
    """Apply a fitted raw-score reference; M1 never falls back to M0."""
    if not math.isfinite(raw_score): return None, False, "missing_or_nonfinite_score"
    if fit["model"] == "M0": prediction = fit["center"]
    else:
        if not math.isfinite(age): return None, False, "missing_or_nonfinite_target_age"
        if age < fit["age_min"] or age > fit["age_max"]: return None, False, "outside_inclusive_training_age_support"
        prediction = fit["intercept"] + fit["slope"] * age
    value = (raw_score - prediction) / fit["scale"]
    if not math.isfinite(value): return None, False, "nonfinite_prediction_or_residual"
    return float(value), True, ""


def profile_geometry(z: Sequence[float], support: Sequence[bool] | None = None) -> dict:
    a = np.asarray(z, dtype=np.float64)
    if a.shape != (5,) or not np.all(np.isfinite(a)): raise ContractError("five finite coordinates required")
    if support is not None:
        s = np.asarray(support)
        if s.shape != (5,) or s.dtype != np.bool_ or not bool(np.all(s)):
            raise ContractError("all five coordinates must be supported")
    level = float(a.mean()); q = a - level
    return {"level": level, "centered_shape": q, "scatter": math.sqrt(float(np.dot(q, q)) / 5.0)}


def _active_pairs(z: np.ndarray, weights: Sequence[int]) -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(z, dtype=np.float64); w = _integer_weights(weights, len(a)); keep = w > 0
    a, w = a[keep], w[keep]
    if a.ndim != 3 or a.shape[1:] != (2, 5): raise ContractError("coordinates must have shape n x 2 x 5")
    if int(w.sum()) < 2: raise ContractError("frequency denominator must be at least two")
    if not np.all(np.isfinite(a)): raise ContractError("active unsupported/nonfinite coordinate")
    return a, w


def icc_a1(two_occasion_values: Sequence[Sequence[float]], weights: Sequence[int] | None = None) -> float | None:
    x = np.asarray(two_occasion_values, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != 2: raise ContractError("ICC requires n x 2 values")
    w = np.ones(len(x), dtype=np.int64) if weights is None else _integer_weights(weights, len(x))
    keep = w > 0; x, w = x[keep], w[keep]; n = int(w.sum()); k = 2
    if n < 2 or not np.all(np.isfinite(x)): raise ContractError("ICC requires two finite frequency observations")
    origin = float(np.sum(w[:, None] * x) / (n * k)); centered = x - origin; unit = float(np.max(np.abs(centered)))
    if unit == 0 or not math.isfinite(unit): return None
    y = centered / unit; gm = float(np.sum(w[:, None] * y) / (n * k)); rm = y.mean(axis=1); cm = np.sum(w[:, None] * y, axis=0) / n
    msr = k * float(np.dot(w, (rm - gm) ** 2)) / (n - 1)
    msc = n * float(np.sum((cm - gm) ** 2)) / (k - 1)
    residual = y - rm[:, None] - cm[None, :] + gm
    mse = float(np.sum(w[:, None] * residual ** 2)) / ((n - 1) * (k - 1))
    denominator = msr + (k - 1) * mse + k * (msc - mse) / n
    relative = max(abs(msr), abs(msc), abs(mse), abs(denominator))
    if relative == 0 or abs(denominator) <= 64 * EPS * relative: return None
    return float((msr - mse) / denominator)  # retain negative finite values


def endpoints(z: np.ndarray, weights: Sequence[int] | None = None) -> dict:
    a = np.asarray(z, dtype=np.float64); w0 = np.ones(len(a), dtype=np.int64) if weights is None else weights
    a, w = _active_pairs(a, w0); level = a.mean(axis=2); q = a - level[:, :, None]
    delta_level = level[:, 1] - level[:, 0]
    squared_shape = np.sum((q[:, 1] - q[:, 0]) ** 2, axis=1) / 5.0
    return {
        "level_icc_a1": icc_a1(level, w),
        "mean_level_change": float(np.dot(w, delta_level) / w.sum()),
        "rms_shape_displacement": math.sqrt(float(np.dot(w, squared_shape) / w.sum())),
        "frequency_denominator": int(w.sum()),
    }


def validate_coordinate_rows(rows: Iterable[Mapping[str, str]], expected_model: str, expected_scale: str,
                             expected_stratum: str, task_order: Sequence[str] = TASK_ORDER) -> dict:
    if tuple(task_order) != TASK_ORDER: raise ContractError("incorrect task order")
    if expected_model not in MODELS or expected_scale not in SCALES: raise ContractError("unknown model or scale")
    rows = list(rows); seen = set(); groups: dict[tuple[str, str], dict[str, Mapping[str, str]]] = defaultdict(dict)
    for row in rows:
        key = (row["participant_id"], row["session_id"], row["task_key"], row["model"], row["scale_method"])
        if key in seen: raise ContractError(f"duplicate coordinate key: {key}")
        seen.add(key)
        if row["model"] != expected_model or row["scale_method"] != expected_scale: raise ContractError("mixed model/scale rows")
        if row["analytical_stratum"] != expected_stratum or row["reference_design"] != DESIGN: raise ContractError("wrong stratum/design")
        supported = row["supported"] == "yes"
        coordinate_present = row.get("coordinate", "") not in ("", "nan", "NaN")
        if row["model"] == "M1" and not supported and coordinate_present: raise ContractError("M1 fallback contamination")
        if supported != coordinate_present: raise ContractError("support/value mismatch")
        groups[(row["participant_id"], row["session_id"])][row["task_key"]] = row
    for key, tasks in groups.items():
        if set(tasks) != set(TASK_ORDER) or len(tasks) != 5: raise ContractError(f"incomplete task set: {key}")
    sessions = defaultdict(set)
    for pid, session in groups: sessions[pid].add(session)
    if any(len(v) != 2 for v in sessions.values()): raise ContractError("each participant requires exactly two selected occasions")
    complete = sum(all(all(groups[(pid, ses)][t]["supported"] == "yes" for t in TASK_ORDER) for ses in sess)
                   for pid, sess in sessions.items())
    return {"rows": len(rows), "participants": len(sessions), "occasion_profiles": len(groups), "complete_pairs": complete}


def validate_source_rows(rows: Iterable[Mapping[str, str]]) -> dict:
    rows = list(rows); seen = set(); groups = defaultdict(set)
    for row in rows:
        key = (row["participant_id"], row["session_id"], row["task_key"])
        if key in seen: raise ContractError(f"duplicate source record: {key}")
        seen.add(key); groups[(row["participant_id"], row["session_id"])].add(row["task_key"])
    if any(tasks != set(TASK_ORDER) for tasks in groups.values()): raise ContractError("source occasion lacks exact five-task set")
    return {"rows": len(rows), "occasion_profiles": len(groups), "participants": len({x[0] for x in groups})}


def make_resampling_plan(target_ids: Sequence[str], auxiliary_ids: Sequence[str], fold_by_target: Mapping[str, int],
                         target_draw: Sequence[str], auxiliary_draw: Sequence[str]) -> dict:
    if len(set(target_ids)) != len(target_ids) or len(set(auxiliary_ids)) != len(auxiliary_ids): raise ContractError("duplicate identity")
    if set(fold_by_target) != set(target_ids): raise ContractError("fold map does not match targets")
    if len(target_draw) != len(target_ids) or set(target_draw) - set(target_ids): raise ContractError("invalid target draw")
    if len(auxiliary_draw) != len(auxiliary_ids) or set(auxiliary_draw) - set(auxiliary_ids): raise ContractError("invalid auxiliary draw")
    tw, aw = Counter(target_draw), Counter(auxiliary_draw)
    target_weights = {i: int(tw[i]) for i in target_ids}; auxiliary_weights = {i: int(aw[i]) for i in auxiliary_ids}
    represented = sorted({fold_by_target[i] for i in target_ids if target_weights[i] > 0})
    return {
        "target_analysis": target_weights, "target_reference": dict(target_weights),
        "visit_multiplicity": dict(target_weights), "auxiliary_draw": auxiliary_weights,
        "fold_membership": dict(fold_by_target), "represented_folds": represented,
        "target_fit_by_fold": {str(f): {i: (0 if fold_by_target[i] == f else target_weights[i]) for i in target_ids} for f in represented},
        "auxiliary_fit_by_fold": {str(f): dict(auxiliary_weights) for f in represented},
    }


def validate_resampling_plan(plan: Mapping, target_ids: Sequence[str], auxiliary_ids: Sequence[str]) -> None:
    target_set, aux_set = set(target_ids), set(auxiliary_ids)
    for key in ("target_analysis", "target_reference", "visit_multiplicity"):
        if set(plan[key]) != target_set: raise ContractError(f"{key} identity mismatch")
    if set(plan["auxiliary_draw"]) != aux_set: raise ContractError("auxiliary identity mismatch")
    if plan["target_analysis"] != plan["target_reference"]: raise ContractError("target analysis/reference multiplicities decoupled")
    if plan["target_analysis"] != plan["visit_multiplicity"]: raise ContractError("independent visit resampling")
    folds = plan["fold_membership"]
    represented = sorted({folds[i] for i in target_ids if plan["target_analysis"][i] > 0})
    if list(plan["represented_folds"]) != represented: raise ContractError("absent/extra fold fitting")
    for f in represented:
        fit = plan["target_fit_by_fold"].get(str(f)); aux = plan["auxiliary_fit_by_fold"].get(str(f))
        if fit is None or set(fit) != target_set or aux != plan["auxiliary_draw"]: raise ContractError("fit map or shared auxiliary draw invalid")
        for i in target_ids:
            expected = 0 if folds[i] == f else plan["target_reference"][i]
            if fit[i] != expected: raise ContractError("held-out leakage or incorrect target weight")


def empirical_interval_gate(attempted: int, valid: int, point_defined: bool) -> tuple[bool, str]:
    if attempted != 999: return False, "attempt_count_not_999"
    if valid < 950: return False, "fewer_than_950_valid"
    if math.floor(0.025 * valid) < 20: return False, "insufficient_tail_count"
    if not point_defined: return False, "undefined_point_estimate"
    return True, "available"


def seed_for(master_seed: int, namespace: str, method: str, replicate: int) -> int:
    payload = f"{master_seed}|{namespace}|{method}|{replicate}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:16], "little")


def dry_run(coordinates_csv: Path, source_csv: Path, model: str, scale: str, stratum: str) -> dict:
    with open(coordinates_csv, newline="", encoding="utf-8-sig") as f: coordinate_rows = list(csv.DictReader(f))
    with open(source_csv, newline="", encoding="utf-8-sig") as f: source_rows = list(csv.DictReader(f))
    selected = [r for r in coordinate_rows if r["model"] == model and r["scale_method"] == scale and r["analytical_stratum"] == stratum]
    selected_source = [r for r in source_rows if r["analytical_stratum"] == stratum]
    if not selected or not selected_source: raise ContractError("requested analysis slice is absent")
    return {
        "mode": "dry_run_metadata_only", "empirical_estimands_calculated": False,
        "coordinate_validation": validate_coordinate_rows(selected, model, scale, stratum),
        "source_validation": validate_source_rows(selected_source),
        "input_sha256": {str(coordinates_csv): sha256_file(coordinates_csv), str(source_csv): sha256_file(source_csv)},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coordinates", type=Path); parser.add_argument("--source", type=Path)
    parser.add_argument("--model", default="M0"); parser.add_argument("--scale", default="MAD"); parser.add_argument("--stratum", default="primary_vf")
    parser.add_argument("--dry-run", action="store_true"); parser.add_argument("--authorize-empirical-execution", action="store_true")
    args = parser.parse_args()
    if args.authorize_empirical_execution:
        raise SystemExit("Step 5B-C1 does not execute empirical estimands; use a separately authorized runner.")
    if not args.dry_run or args.coordinates is None or args.source is None:
        parser.error("metadata-only use requires --dry-run, --coordinates, and --source")
    print(json.dumps(dry_run(args.coordinates, args.source, args.model, args.scale, args.stratum), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
