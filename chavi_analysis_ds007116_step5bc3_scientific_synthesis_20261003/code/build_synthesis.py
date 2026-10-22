#!/usr/bin/env python3
"""Build Step 5B-C3 public aggregate tables and figures from frozen evidence.

Standard-library only.  No participant-linked input is read.  SVG is the native
figure; an installed Chromium-family browser is used for PDF/PNG rendering.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import html
import json
import math
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parents[1]
C2 = ROOT / "chavi_analysis_ds007116_step5bc2_empirical_execution_20261003"
B3R = ROOT / "chavi_analysis_ds007116_step5bb3r_validation_repair_20261002"
TABLES = OUT / "aggregate_tables"
FIGURES = OUT / "figures"

ENDPOINT_LABEL = {
    "level_icc_a1": "Level ICC(A,1)",
    "mean_level_change": "Mean level change",
    "rms_shape_displacement": "RMS centered-shape displacement",
}
METHOD_SHORT = {
    "P1_oracle_conditional": "P1",
    "P2_fixed_transform": "P2",
    "P3_joint_unstratified": "P3",
    "P4_joint_fold_stratified": "P4",
}


def rows(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, data, fields=None):
    data = list(data)
    if fields is None:
        fields = list(data[0]) if data else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(data)


def fnum(x):
    return float(x)


def build_tables():
    endpoint = rows(C2 / "results/public_aggregate/endpoint_estimates.csv")
    intervals = rows(C2 / "results/public_aggregate/primary_bootstrap_intervals.csv")
    corr = rows(C2 / "results/public_aggregate/profile_correlation_summary.csv")
    write_csv(TABLES / "empirical_all_planned_point_estimates.csv", endpoint)
    write_csv(TABLES / "empirical_primary_intervals.csv", intervals)
    write_csv(TABLES / "empirical_profile_correlation_summary.csv", corr)

    lookup = {(r["endpoint"], r["interval_family"], r["method"]): r for r in intervals}
    comparisons = []
    for endpoint_id in ENDPOINT_LABEL:
        for family in ("percentile", "basic"):
            p2 = lookup[(endpoint_id, family, "P2_fixed_transform")]
            p3 = lookup[(endpoint_id, family, "P3_joint_unstratified")]
            w2 = fnum(p2["upper"]) - fnum(p2["lower"])
            w3 = fnum(p3["upper"]) - fnum(p3["lower"])
            comparisons.append({
                "endpoint": endpoint_id, "interval_family": family,
                "point_estimate": p2["point_estimate"],
                "p2_lower": p2["lower"], "p2_upper": p2["upper"],
                "p2_width": repr(w2), "p3_lower": p3["lower"],
                "p3_upper": p3["upper"], "p3_width": repr(w3),
                "width_difference_p3_minus_p2": repr(w3 - w2),
                "width_ratio_p3_over_p2": repr(w3 / w2),
                "interpretation_role": "descriptive_realized_interval_comparison",
                "denominator": "52 participant pairs; each interval uses 999 valid of 999 attempted draws",
            })
    write_csv(TABLES / "empirical_primary_interval_comparisons.csv", comparisons)

    sim = []
    for name in ("corrected_pilot_performance_summary_repaired.csv", "confirmatory_performance_summary_repaired.csv"):
        for r in rows(B3R / name):
            r = dict(r)
            r["coverage_denominator"] = "available_intervals"
            r["availability_denominator"] = "attempted_outer"
            r["available_and_covered_denominator"] = "attempted_outer"
            r["width_denominator"] = "available_intervals"
            sim.append(r)
    write_csv(TABLES / "simulation_synthesis_all_prespecified.csv", sim)

    paired = []
    for name in ("corrected_pilot_paired_comparisons_repaired.csv", "confirmatory_paired_comparisons_repaired.csv"):
        paired.extend(rows(B3R / name))
    write_csv(TABLES / "simulation_paired_monte_carlo_comparisons.csv", paired)

    failures = {}
    for name in ("corrected_pilot_bootstrap_status_repaired.csv", "confirmatory_bootstrap_status_repaired.csv"):
        for r in rows(B3R / name):
            key = (r["stage"], r["scenario_id"], r["scale_method"], r["endpoint"], r["method"])
            dst = failures.setdefault(key, {"attempted": 0, "valid": 0, "invalid": 0, "available_outer": 0, "outer_replicates": 0, "reasons": {}})
            dst["attempted"] += int(r["attempted"]); dst["valid"] += int(r["valid"])
            dst["invalid"] += int(r["invalid"]); dst["available_outer"] += int(r["available"] == "True")
            dst["outer_replicates"] += 1
            for reason, count in ast.literal_eval(r["failure_reasons"]).items():
                dst["reasons"][reason] = dst["reasons"].get(reason, 0) + int(count)
    failure_rows = []
    for key, d in sorted(failures.items()):
        failure_rows.append({
            "stage": key[0], "scenario_id": key[1], "scale_method": key[2],
            "endpoint": key[3], "method": key[4], **{k: d[k] for k in ("outer_replicates", "attempted", "valid", "invalid", "available_outer")},
            "unavailable_outer": d["outer_replicates"] - d["available_outer"],
            "failure_reason_counts_json": json.dumps(d["reasons"], sort_keys=True, separators=(",", ":")),
        })
    write_csv(TABLES / "simulation_failure_reason_summary.csv", failure_rows)

    cohort = [
        {"flow_order": 1, "cohort": "reference_A", "participants": 109, "role": "reference-eligible participants in clean rebuild", "identity_public": "no"},
        {"flow_order": 2, "cohort": "primary_vf", "participants": 52, "role": "primary V-to-F paired analysis", "identity_public": "no"},
        {"flow_order": 3, "cohort": "matched_support_M1", "participants": 42, "role": "same participants for matched-support M0/M1 comparison", "identity_public": "no"},
        {"flow_order": 4, "cohort": "fixed_primary_pair_strict_v", "participants": 41, "role": "strict-V rule applied to primary identities", "identity_public": "no"},
        {"flow_order": 5, "cohort": "vonly_reselected", "participants": 45, "role": "strict-V eligibility with pair reselection", "identity_public": "no"},
    ]
    write_csv(TABLES / "cohort_flow.csv", cohort)

    primary_plot = []
    for r in intervals:
        if r["interval_family"] == "percentile":
            primary_plot.append({k: r[k] for k in ("endpoint", "method", "point_estimate", "lower", "upper")})
    write_csv(FIGURES / "figure1_primary_intervals_data.csv", primary_plot)

    anchor = [r for r in sim if r["stage"] == "confirmatory" and r["scenario_id"] in ("S1", "S5") and r["scale_method"] == "MAD" and r["endpoint"] == "rms_shape_displacement" and r["interval_family"] == "percentile"]
    write_csv(FIGURES / "figure2_simulation_tradeoffs_data.csv", anchor)

    sensitivity = [r for r in endpoint if r["analysis_id"] != "A_primary_M0_MAD_52"]
    write_csv(FIGURES / "figure3_sensitivity_estimates_data.csv", sensitivity)
    return endpoint, intervals, sim, anchor, sensitivity


def esc(s): return html.escape(str(s))


def svg_start(title, subtitle, width=1500, height=900):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#ffffff"/>',
            '<style>text{font-family:Arial,sans-serif;fill:#18212b}.title{font-size:30px;font-weight:700}.sub{font-size:17px;fill:#52606d}.lab{font-size:17px}.small{font-size:14px;fill:#52606d}.axis{stroke:#52606d;stroke-width:1.5}.grid{stroke:#d9e2ec;stroke-width:1}.p2{stroke:#1769aa;fill:#1769aa}.p3{stroke:#c23b22;fill:#c23b22}.p1{stroke:#66788a;fill:#66788a}.p4{stroke:#6a3d9a;fill:#6a3d9a}</style>',
            f'<text x="55" y="48" class="title">{esc(title)}</text>', f'<text x="55" y="78" class="sub">{esc(subtitle)}</text>']


def mapx(v, lo, hi, x0, x1):
    return x0 + (v-lo)/(hi-lo)*(x1-x0)


def figure1(intervals):
    data = [r for r in intervals if r["interval_family"] == "percentile"]
    out = svg_start("Primary empirical 95% percentile intervals", "Three endpoint-specific axes; n=52 pairs; 999/999 valid draws per method")
    colors = {"P2_fixed_transform": "p2", "P3_joint_unstratified": "p3"}
    panels = [("level_icc_a1", 0.25, 0.90), ("mean_level_change", 0.10, 0.62), ("rms_shape_displacement", 0.55, 1.45)]
    for i,(ep,lo,hi) in enumerate(panels):
        x0,x1=390,1420; y0=180+i*225
        out.append(f'<text x="55" y="{y0-25}" class="lab" font-weight="700">{esc(ENDPOINT_LABEL[ep])}</text>')
        for t in range(6):
            v=lo+(hi-lo)*t/5; x=mapx(v,lo,hi,x0,x1)
            out += [f'<line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y0+110}" class="grid"/>', f'<text x="{x:.1f}" y="{y0+140}" class="small" text-anchor="middle">{v:.2f}</text>']
        out.append(f'<line x1="{x0}" y1="{y0+110}" x2="{x1}" y2="{y0+110}" class="axis"/>')
        for j,r in enumerate([x for x in data if x["endpoint"]==ep]):
            y=y0+30+j*55; xl=mapx(fnum(r["lower"]),lo,hi,x0,x1); xu=mapx(fnum(r["upper"]),lo,hi,x0,x1); xp=mapx(fnum(r["point_estimate"]),lo,hi,x0,x1); c=colors[r["method"]]
            out += [f'<text x="330" y="{y+6}" class="lab" text-anchor="end">{METHOD_SHORT[r["method"]]}</text>', f'<line x1="{xl:.1f}" y1="{y}" x2="{xu:.1f}" y2="{y}" class="{c}" stroke-width="6"/>', f'<circle cx="{xp:.1f}" cy="{y}" r="8" class="{c}"/>']
    out += ['<text x="55" y="855" class="small">P2 fixes the fitted transformation; P3 resamples participants and refits it. Differences are descriptive, not a superiority test.</text>', '</svg>']
    (FIGURES/"figure1_primary_intervals.svg").write_text("\n".join(out),encoding="utf-8")


def figure2(anchor):
    out=svg_start("Confirmatory RMS interval performance", "MAD scale, percentile intervals; error bars are ±1.96 Monte Carlo SE for conditional coverage")
    for panel,(scenario,label) in enumerate((("S1","S1 continuous correlated"),("S5","S5 rounded/tied"))):
        xbase=100+panel*720; ytop=165
        out.append(f'<text x="{xbase}" y="125" class="lab" font-weight="700">{label}</text>')
        for t in range(6):
            v=.5+t*.1; y=ytop+500-(v-.5)/.5*500
            out += [f'<line x1="{xbase}" y1="{y}" x2="{xbase+600}" y2="{y}" class="grid"/>', f'<text x="{xbase-12}" y="{y+5}" class="small" text-anchor="end">{v:.1f}</text>']
        ynom=ytop+500-(.95-.5)/.5*500
        out.append(f'<line x1="{xbase}" y1="{ynom}" x2="{xbase+600}" y2="{ynom}" stroke="#111" stroke-dasharray="10,7" stroke-width="2"/>')
        subset=sorted([r for r in anchor if r["scenario_id"]==scenario],key=lambda r:r["method"])
        for i,r in enumerate(subset):
            x=xbase+80+i*140; cov=fnum(r["coverage_available"]); av=fnum(r["availability_rate"]); se=fnum(r["mcse_coverage_available"])
            yc=ytop+500-(cov-.5)/.5*500; ya=ytop+500-(av-.5)/.5*500; e=1.96*se/.5*500
            c=METHOD_SHORT[r["method"]].lower()
            out += [f'<line x1="{x-18}" y1="{yc-e:.1f}" x2="{x-18}" y2="{yc+e:.1f}" class="{c}" stroke-width="2"/>', f'<circle cx="{x-18}" cy="{yc:.1f}" r="8" class="{c}"/>', f'<rect x="{x+9}" y="{ya-7:.1f}" width="14" height="14" class="{c}"/>', f'<text x="{x}" y="{ytop+535}" class="lab" text-anchor="middle">{METHOD_SHORT[r["method"]]}</text>']
        out += [f'<line x1="{xbase}" y1="{ytop+500}" x2="{xbase+600}" y2="{ytop+500}" class="axis"/>']
    out += ['<circle cx="105" cy="760" r="8" fill="#263238"/><text x="125" y="766" class="lab">Conditional coverage (among available intervals)</text>', '<rect x="585" y="752" width="14" height="14" fill="#263238"/><text x="610" y="766" class="lab">Availability (among attempted outer replicates)</text>', '<line x1="105" y1="810" x2="155" y2="810" stroke="#111" stroke-dasharray="10,7" stroke-width="2"/><text x="170" y="816" class="lab">Nominal 0.95 coverage</text>', '</svg>']
    (FIGURES/"figure2_simulation_tradeoffs.svg").write_text("\n".join(out),encoding="utf-8")


def figure3(sensitivity):
    out=svg_start("Empirical sensitivity estimates", "Point estimates only; no inferential bars are available or invented. Denominator shown in each label.")
    panels=[("level_icc_a1",0.45,0.75),("mean_level_change",0,0.45),("rms_shape_displacement",0.7,1.18)]
    labels={
      "B_scale_M0_SD_52":"M0 / SD (n=52)", "C_matched_M0_MAD_42":"Matched M0 / MAD (n=42)",
      "D_matched_M1_MAD_42":"Matched M1 / MAD (n=42)", "E_fixed_strictV_M0_MAD_41":"Fixed strict-V (n=41)",
      "F_reselected_strictV_M0_MAD_45":"Reselected strict-V (n=45)"}
    for p,(ep,lo,hi) in enumerate(panels):
        x0=110+p*480; x1=x0+370; y0=180
        out.append(f'<text x="{x0}" y="130" class="lab" font-weight="700">{esc(ENDPOINT_LABEL[ep])}</text>')
        for t in range(6):
            v=lo+(hi-lo)*t/5; x=mapx(v,lo,hi,x0,x1)
            out += [f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y0+500}" class="grid"/>',f'<text x="{x}" y="{y0+530}" class="small" text-anchor="middle">{v:.2f}</text>']
        vals=[r for r in sensitivity if r["estimand_id"]==ep]
        for i,r in enumerate(vals):
            y=y0+55+i*88; x=mapx(fnum(r["estimate"]),lo,hi,x0,x1)
            out += [f'<circle cx="{x}" cy="{y}" r="10" fill="#1769aa"/>',f'<text x="{x0}" y="{y+28}" class="small">{esc(labels.get(r["analysis_id"],r["analysis_id"]))}</text>']
        out.append(f'<line x1="{x0}" y1="{y0+500}" x2="{x1}" y2="{y0+500}" class="axis"/>')
    out += ['<text x="55" y="850" class="small">Panels use endpoint-specific axes. Model, scale, eligibility, and reselection changes answer different sensitivity questions.</text>','</svg>']
    (FIGURES/"figure3_sensitivity_estimates.svg").write_text("\n".join(out),encoding="utf-8")


def browser_path():
    candidates=[Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")]
    return next((p for p in candidates if p.exists()),None)


def render_figures():
    browser=browser_path()
    if not browser:
        raise RuntimeError("No supported Chromium-family browser found")
    profile = OUT / "validation" / "chromium_profile"
    profile.mkdir(parents=True, exist_ok=True)
    common=[str(browser),"--headless","--disable-gpu","--no-sandbox",f"--user-data-dir={profile}"]
    for stem in ("figure1_primary_intervals","figure2_simulation_tradeoffs","figure3_sensitivity_estimates"):
        uri=(FIGURES/f"{stem}.svg").resolve().as_uri()
        subprocess.run(common+["--no-pdf-header-footer",f"--print-to-pdf={FIGURES/f'{stem}.pdf'}",uri],check=True)
        subprocess.run(common+["--hide-scrollbars","--window-size=1500,900",f"--screenshot={FIGURES/f'{stem}.png'}",uri],check=True)


def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()


def main():
    TABLES.mkdir(parents=True,exist_ok=True); FIGURES.mkdir(parents=True,exist_ok=True)
    endpoint,intervals,sim,anchor,sensitivity=build_tables()
    figure1(intervals); figure2(anchor); figure3(sensitivity)
    if "--no-render" not in sys.argv: render_figures()
    print(json.dumps({"point_rows":len(endpoint),"interval_rows":len(intervals),"simulation_rows":len(sim),"anchor_rows":len(anchor),"sensitivity_rows":len(sensitivity)},sort_keys=True))


if __name__=="__main__": main()
