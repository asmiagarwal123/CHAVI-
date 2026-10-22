#!/usr/bin/env python3
"""Targeted C3 validation, manifest construction, and deterministic packaging."""
from __future__ import annotations
import csv, hashlib, json, re, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parents[1]
TABLES=OUT/"aggregate_tables"; FIGURES=OUT/"figures"; VALID=OUT/"validation"
ZIP=ROOT/f"{OUT.name}.zip"

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def readcsv(path):
    with path.open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))

def check(name, condition, evidence, detail=""):
    return {"check":name,"status":"PASS" if condition else "FAIL","evidence":evidence,"detail":detail}

def main():
    VALID.mkdir(exist_ok=True)
    checks=[]
    inputs=readcsv(OUT/"input_manifest.csv")
    checked=0; missing=[]; mismatched=[]
    for r in inputs:
        p=ROOT/r["relative_path"]
        if not p.exists(): missing.append(r["source_id"]); continue
        # ZIP sidecars store the expected package digest as text; other rows hash bytes.
        if r["source_id"].endswith("ZIP_SIDECAR"):
            ok=r["sha256"] in p.read_text(encoding="utf-8").lower()
        else: ok=sha(p)==r["sha256"]
        checked+=1
        if not ok:mismatched.append(r["source_id"])
    checks.append(check("authoritative_input_hashes",not missing and not mismatched,"input_manifest.csv",f"checked={checked}; missing={missing}; mismatched={mismatched}"))

    pts=readcsv(TABLES/"empirical_all_planned_point_estimates.csv")
    ints=readcsv(TABLES/"empirical_primary_intervals.csv")
    sims=readcsv(TABLES/"simulation_synthesis_all_prespecified.csv")
    checks.append(check("planned_row_counts",len(pts)==18 and len(ints)==12 and len(sims)==384,"aggregate_tables",f"points={len(pts)}, intervals={len(ints)}, simulation_cells={len(sims)}"))

    src_pts=readcsv(ROOT/"chavi_analysis_ds007116_step5bc2_empirical_execution_20261003/results/public_aggregate/endpoint_estimates.csv")
    src_ints=readcsv(ROOT/"chavi_analysis_ds007116_step5bc2_empirical_execution_20261003/results/public_aggregate/primary_bootstrap_intervals.csv")
    checks.append(check("empirical_exact_mapping",pts==src_pts and ints==src_ints,"C2 public aggregates versus C3 copies"))

    comp=readcsv(TABLES/"empirical_primary_interval_comparisons.csv")
    width_ok=all(abs(float(r["p2_width"])-(float(r["p2_upper"])-float(r["p2_lower"])))<1e-15 and abs(float(r["p3_width"])-(float(r["p3_upper"])-float(r["p3_lower"])))<1e-15 for r in comp)
    checks.append(check("unrounded_width_recalculation",width_ok,"aggregate_tables/empirical_primary_interval_comparisons.csv"))

    idx={(r["stage"],r["scenario_id"],r["scale_method"],r["endpoint"],r["method"],r["interval_family"]):r for r in sims}
    s1p2=idx[("confirmatory","S1","MAD","rms_shape_displacement","P2_fixed_transform","percentile")]
    s1p3=idx[("confirmatory","S1","MAD","rms_shape_displacement","P3_joint_unstratified","percentile")]
    s5p2=idx[("confirmatory","S5","MAD","rms_shape_displacement","P2_fixed_transform","percentile")]
    s5p3=idx[("confirmatory","S5","MAD","rms_shape_displacement","P3_joint_unstratified","percentile")]
    anchors=(float(s1p2["coverage_available"])==1606/2000 and float(s1p3["coverage_available"])==1835/2000 and int(s5p2["available_intervals"])==1994 and float(s5p2["available_and_covered_all"])==.916 and int(s5p3["available_intervals"])==1260 and float(s5p3["available_and_covered_all"])==.6025)
    denominator_ok=all(abs(float(r["availability_rate"])-int(r["available_intervals"])/int(r["attempted_outer"]))<1e-14 and abs(float(r["available_and_covered_all"])-((float(r["coverage_available"])*int(r["available_intervals"]))/int(r["attempted_outer"])))<1e-12 for r in sims if int(r["available_intervals"])>0)
    checks.append(check("simulation_anchors_and_denominators",anchors and denominator_ok,"simulation_synthesis_all_prespecified.csv","S1/S5 anchors and all availability denominators recalculated"))

    fig1=readcsv(FIGURES/"figure1_primary_intervals_data.csv")
    expected_fig1=[{k:r[k] for k in ("endpoint","method","point_estimate","lower","upper")} for r in ints if r["interval_family"]=="percentile"]
    fig2=readcsv(FIGURES/"figure2_simulation_tradeoffs_data.csv")
    expected_fig2=[r for r in sims if r["stage"]=="confirmatory" and r["scenario_id"] in ("S1","S5") and r["scale_method"]=="MAD" and r["endpoint"]=="rms_shape_displacement" and r["interval_family"]=="percentile"]
    formats_ok=True
    for stem in ("figure1_primary_intervals","figure2_simulation_tradeoffs","figure3_sensitivity_estimates"):
        formats_ok &= (FIGURES/f"{stem}.svg").stat().st_size>1000
        formats_ok &= (FIGURES/f"{stem}.pdf").read_bytes()[:4]==b"%PDF"
        formats_ok &= (FIGURES/f"{stem}.png").read_bytes()[:8]==b"\x89PNG\r\n\x1a\n"
    checks.append(check("figure_source_and_formats",fig1==expected_fig1 and fig2==expected_fig2 and formats_ok,"figures/*_data.csv and SVG/PDF/PNG files","PNG/SVG visually inspected; pdftoppm unavailable, PDFs share the same SVG/Chromium source"))

    public=[]
    for p in OUT.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".md",".csv",".json",".bib",".py",".svg"}:
            public.append(p)
    identifier_hits=[]
    pattern=re.compile(r"\bsub-\d+\b",re.I)
    for p in public:
        if pattern.search(p.read_text(encoding="utf-8",errors="ignore")):identifier_hits.append(p.relative_to(OUT).as_posix())
    checks.append(check("public_privacy_scan",not identifier_hits,"all C3 text/csv/json/bib/py/svg files",f"participant_identifier_hits={identifier_hits}"))

    required=["SCIENTIFIC_SYNTHESIS_AND_PUBLICATION_DECISION.md","PLAIN_LANGUAGE_PROJECT_EXPLANATION.md","FINAL_SCOPE_AND_RESEARCH_QUESTION.md","literature_search_log.csv","closest_work_matrix.csv","references.bib","claim_evidence_matrix.csv","COMPLETION_CHECKLIST.md","README.md","input_manifest.csv"]
    checks.append(check("required_deliverables",all((OUT/x).exists() for x in required),"C3 milestone root"))
    overall="PASS" if all(c["status"]=="PASS" for c in checks) else "FAIL"
    report={"overall_status":overall,"generated_by":"code/validate_and_package.py","automated_checks":checks,"scientific_judgments_are_not_mechanically_proven":True,"pdf_visual_qa_note":"Poppler/pdftoppm was unavailable. Native SVG and same-source PNG outputs were visually inspected; PDF signatures and non-empty output were checked."}
    (VALID/"synthesis_checks.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    if overall!="PASS": raise SystemExit("Validation failed")

    manifest=[]
    excluded={"artifact_manifest.csv"}
    for p in sorted(x for x in OUT.rglob("*") if x.is_file() and x.name not in excluded):
        manifest.append({"relative_path":p.relative_to(OUT).as_posix(),"size_bytes":p.stat().st_size,"sha256":sha(p)})
    with (OUT/"artifact_manifest.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["relative_path","size_bytes","sha256"]);w.writeheader();w.writerows(manifest)

    fixed=(2026,10,3,0,0,0)
    with zipfile.ZipFile(ZIP,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(x for x in OUT.rglob("*") if x.is_file()):
            info=zipfile.ZipInfo(f"{OUT.name}/{p.relative_to(OUT).as_posix()}",fixed);info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,p.read_bytes(),compresslevel=9)
    zhash=sha(ZIP)
    with zipfile.ZipFile(ZIP) as z:
        bad=z.testzip(); names=set(z.namelist())
    expected={f"{OUT.name}/{p.relative_to(OUT).as_posix()}" for p in OUT.rglob("*") if p.is_file()}
    verified=(bad is None and names==expected)
    sidecar=ROOT/f"{ZIP.name}.sha256.txt"; sidecar.write_text(f"{zhash}  {ZIP.name}\n",encoding="ascii")
    verification=ROOT/f"{ZIP.name}.verification.json"
    verification.write_text(json.dumps({"zip":ZIP.name,"sha256":zhash,"zip_test_passed":bad is None,"member_set_matches":names==expected,"member_count":len(names)},indent=2)+"\n",encoding="utf-8")
    if not verified: raise SystemExit("ZIP integrity failed")
    print(json.dumps({"validation":overall,"artifact_count":len(manifest),"zip_sha256":zhash,"zip_members":len(names)},sort_keys=True))

if __name__=="__main__":main()
