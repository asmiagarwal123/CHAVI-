"""Proposed CHAVI profile calculations. Synthetic use only in Step 5B-B1.

Status: RECOMMENDED SCIENTIFIC PROTOCOL — NOT YET ADOPTED FOR EMPIRICAL EXECUTION.
This module never reads CHAVI empirical coordinate files.
"""
from __future__ import annotations

import math
from typing import Iterable, Mapping, Sequence

import numpy as np

TASK_ORDER = (
    "letter_nback", "face_memory", "matrix_reasoning",
    "emotion_recognition", "dominant_finger_tapping",
)


def helmert_matrix() -> np.ndarray:
    """Return fixed 5x4 orthonormal Helmert contrast matrix."""
    h = np.zeros((5, 4), dtype=float)
    for col in range(4):
        k = col + 1
        h[:k, col] = 1.0 / math.sqrt(k * (k + 1.0))
        h[k, col] = -k / math.sqrt(k * (k + 1.0))
    return h


H = helmert_matrix()


def _vector(values: Sequence[float] | Mapping[str, float], supported=None) -> np.ndarray:
    if isinstance(values, Mapping):
        if tuple(values.keys()) != TASK_ORDER:
            raise ValueError("task mapping keys/order must exactly match TASK_ORDER")
        values = [values[t] for t in TASK_ORDER]
    z = np.asarray(values, dtype=float)
    if z.shape != (5,):
        raise ValueError("exactly five task coordinates are required")
    if not np.all(np.isfinite(z)):
        raise ValueError("all five coordinates must be finite")
    if supported is not None:
        flags = np.asarray(supported, dtype=bool)
        if flags.shape != (5,) or not bool(np.all(flags)):
            raise ValueError("all five task coordinates must be supported")
    return z


def profile_geometry(values, supported=None) -> dict:
    z = _vector(values, supported)
    level = float(np.mean(z))
    q = z - level
    scatter = float(np.sqrt(np.dot(q, q) / 5.0))
    # Center first to avoid cancellation in H.T @ z at large common offsets.
    c = H.T @ q
    return {"level": level, "centered_shape": q, "scatter": scatter,
            "contrasts": c, "shape_norm": float(np.linalg.norm(q))}


def degeneracy_threshold(values) -> float:
    """Floating-point resolvability threshold; declared before empirical use.

    The level term makes the rule conservative after very large translations,
    where subtraction can destroy representable task differences.
    """
    z = _vector(values)
    level = float(np.mean(z))
    scale = max(float(np.linalg.norm(z)), math.sqrt(5.0) * abs(level),
                np.finfo(float).tiny)
    return float(64.0 * np.finfo(float).eps * scale)


def profile_correlation(first, second) -> float | None:
    a, b = _vector(first), _vector(second)
    qa = a - np.mean(a)
    qb = b - np.mean(b)
    if np.linalg.norm(qa) <= degeneracy_threshold(a):
        return None
    if np.linalg.norm(qb) <= degeneracy_threshold(b):
        return None
    return float(np.dot(qa, qb) / (np.linalg.norm(qa) * np.linalg.norm(qb)))


def pair_geometry(first, second) -> dict:
    a, b = _vector(first), _vector(second)
    ga, gb = profile_geometry(a), profile_geometry(b)
    dq = gb["centered_shape"] - ga["centered_shape"]
    dz = b - a
    return {
        "delta_level": gb["level"] - ga["level"],
        "delta_scatter": gb["scatter"] - ga["scatter"],
        "shape_displacement": float(np.sqrt(np.dot(dq, dq) / 5.0)),
        "total_displacement": float(np.sqrt(np.dot(dz, dz) / 5.0)),
        "profile_correlation": profile_correlation(a, b),
    }


def icc_a1(pairs: Iterable[Sequence[float]]) -> float | None:
    """Two-way mixed-effects, single-measure, absolute-agreement ICC(A,1)."""
    x = np.asarray(list(pairs), dtype=float)
    if x.ndim != 2 or x.shape[1] != 2 or x.shape[0] < 2 or not np.all(np.isfinite(x)):
        raise ValueError("finite n-by-2 paired observations with n>=2 required")
    n, k = x.shape
    gm = float(np.mean(x)); rm = np.mean(x, axis=1); cm = np.mean(x, axis=0)
    msr = k * float(np.sum((rm - gm) ** 2)) / (n - 1)
    msc = n * float(np.sum((cm - gm) ** 2)) / (k - 1)
    resid = x - rm[:, None] - cm[None, :] + gm
    mse = float(np.sum(resid ** 2)) / ((n - 1) * (k - 1))
    den = msr + (k - 1) * mse + k * (msc - mse) / n
    return None if abs(den) <= 64 * np.finfo(float).eps * max(abs(msr), abs(msc), abs(mse), 1.0) else (msr - mse) / den


def icc_c1(pairs: Iterable[Sequence[float]]) -> float | None:
    """Two-way mixed-effects, single-measure, consistency ICC(C,1)."""
    x = np.asarray(list(pairs), dtype=float)
    if x.ndim != 2 or x.shape[1] != 2 or x.shape[0] < 2 or not np.all(np.isfinite(x)):
        raise ValueError("finite n-by-2 paired observations with n>=2 required")
    n, k = x.shape
    gm = float(np.mean(x)); rm = np.mean(x, axis=1); cm = np.mean(x, axis=0)
    msr = k * float(np.sum((rm - gm) ** 2)) / (n - 1)
    resid = x - rm[:, None] - cm[None, :] + gm
    mse = float(np.sum(resid ** 2)) / ((n - 1) * (k - 1))
    den = msr + (k - 1) * mse
    return None if abs(den) <= 64 * np.finfo(float).eps * max(abs(msr), abs(mse), 1.0) else (msr - mse) / den


def shape_trace_association(c1, c2) -> float | None:
    """Descriptive centered cross-covariance trace association, not an ICC."""
    a, b = np.asarray(c1, float), np.asarray(c2, float)
    if a.ndim != 2 or b.shape != a.shape or a.shape[1] != 4 or a.shape[0] < 2:
        raise ValueError("matching finite n-by-4 contrast matrices required")
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError("finite contrasts required")
    ac, bc = a - a.mean(0), b - b.mean(0)
    num = float(np.sum(ac * bc))
    den = math.sqrt(float(np.sum(ac * ac) * np.sum(bc * bc)))
    return None if den <= 64 * np.finfo(float).eps * max(np.linalg.norm(ac), np.linalg.norm(bc), 1.0) ** 2 else num / den


def validate_unique_keys(rows: Iterable[Mapping], keys=("participant_id", "session_id", "variant")) -> None:
    seen = set()
    for row in rows:
        key = tuple(row[k] for k in keys)
        if key in seen:
            raise ValueError(f"duplicate key: {key}")
        seen.add(key)


def validate_m1_null_policy(row: Mapping) -> None:
    if row.get("model") == "M1" and row.get("supported") in (False, "no"):
        if row.get("coordinate") not in (None, ""):
            raise ValueError("unsupported M1 coordinate must be null; fallback is separate")


def validate_bootstrap_multiplicities(plan: Mapping) -> None:
    """Validate identity-linked multiplicities for one deterministic toy replicate."""
    tf, ta = plan["target_fit_multiplicity"], plan["target_analysis_multiplicity"]
    if tf != ta:
        raise ValueError("target fitting and analysis multiplicities must match")
    if plan["visit_multiplicity"] != ta:
        raise ValueError("both visits must share participant multiplicity")
    aux = plan["auxiliary_multiplicity_by_fold"]
    if len({tuple(sorted(v.items())) for v in aux.values()}) != 1:
        raise ValueError("auxiliary multiplicity must be reused across folds")
    for fold, held_out in plan["held_out_targets_by_fold"].items():
        fitted = plan["fitted_target_multiplicity_by_fold"][fold]
        if any(fitted.get(pid, 0) for pid in held_out):
            raise ValueError("all copies of held-out targets must be excluded")
