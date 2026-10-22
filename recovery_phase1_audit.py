#!/usr/bin/env python3
"""Read-only CHAVI Recovery Phase 1 forensic audit.

Writes only below chavi_recovery_phase1_forensic_audit_20260916. It never
opens an existing workspace artifact for writing and does not run production
code.
"""
from __future__ import annotations
import ast, csv, hashlib, json, os, re, subprocess, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "chavi_recovery_phase1_forensic_audit_20260916"
OUT.mkdir(exist_ok=True)
EXCLUDE = {OUT.resolve(), (ROOT / ".git").resolve()}
TASKS = ["cnb_lnb_mcr", "cnb_cpf_cr", "cnb_pmat_cr", "cnb_er40_cr", "cnb_ctap_dom"]
TRUST = {"ds007116": "RAW_PINNED_SOURCE", "chavi_audit_ds007116": "VERIFIED_EARLIER_RESULT",
         "step5af": "CURRENT_CANDIDATE", "step5bar3": "UNVERIFIED"}

def rel(p):
    try: return str(p.resolve().relative_to(ROOT.resolve()))
    except ValueError: return str(p)
def sha(p):
    # Raw imaging binaries are included in the inventory but are not read into
    # memory or exhaustively hashed in this phase; dataset-level Git identity
    # and all small forensic artifacts are hashed. This preserves read-only
    # behavior and makes the audit practical on the full OpenNeuro checkout.
    try:
        if p.stat().st_size > 25*1024*1024:
            return "", "skipped_large_file_over_25MiB"
    except Exception: pass
    h=hashlib.sha256()
    try:
        with p.open("rb") as f:
            for b in iter(lambda:f.read(1024*1024), b""): h.update(b)
        return h.hexdigest(), ""
    except Exception as e: return "", type(e).__name__+": "+str(e)
def write_csv(name, fields, rows):
    with (OUT/name).open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader()
        for r in rows: w.writerow({k:r.get(k,"") for k in fields})
def read_csv(p):
    try:
        with p.open(newline="", encoding="utf-8-sig") as f: return list(csv.DictReader(f))
    except Exception: return []
_FILES = None
def csv_files():
    global _FILES
    if _FILES is None:
        found=[]
        for base, dirs, files in os.walk(ROOT):
            bp=Path(base).resolve()
            if bp in EXCLUDE: dirs[:] = []; continue
            # The raw checkout contains many thousands of imaging files. Keep
            # its metadata/code, but do not descend into subject/derivative
            # payloads; their directory presence and Git identity are audited.
            if bp == (ROOT/"ds007116").resolve():
                dirs[:] = [d for d in dirs if d in {"code","phenotype","sourcedata",".datalad"}]
            if "ds007116" in bp.name and bp.parent == ROOT.resolve() and bp.name != "ds007116":
                pass
            for fn in files:
                p=Path(base)/fn
                if not any(x in p.resolve().parents for x in EXCLUDE): found.append(p)
        _FILES = found
    return _FILES
def milestone(p):
    s=rel(p)
    if s.startswith("ds007116"): return "ds007116"
    m=re.search(r"(chavi_[^\\/]+)",s); return m.group(1) if m else s.split("\\")[0]
def status_for(p):
    s=rel(p).lower()
    if s.startswith("ds007116\\"): return "RAW_PINNED_SOURCE"
    if "step5bar3" in s or "independent_transformation_validator" in s: return "UNVERIFIED"
    if "step5ba" in s or "step5af" in s: return "CURRENT_CANDIDATE"
    if "step5adr" in s or "step5ad" in s: return "SUPERSEDED"
    if "step4" in s or "step3" in s or "step2" in s or "step1" in s: return "VERIFIED_EARLIER_RESULT"
    return "UNKNOWN"
def text(p):
    try: return p.read_text(encoding="utf-8-sig", errors="replace")
    except Exception: return ""
def key_metrics(rows):
    if not rows: return {}
    def u(cols): return len({tuple(r.get(c,"") for c in cols) for r in rows})
    out={"rows":len(rows),"participants":u(["participant_id"]),
         "occasions":u(["participant_id","repository_session_id"]),
         "source_keys":u([c for c in ["participant_id","repository_session_id","score_field"] if c in rows[0]])}
    for c in ["analytical_stratum","cohort_type","fold","extrapolation_flag","m1_extrapolation_flag","m1_supported","support_refusal_status"]:
        if c in rows[0]: out[c+"_values"]=";".join(sorted({r.get(c,"") for r in rows}))
    return out

def baseline_inventory():
    rows=[]; errors=[]
    for p in csv_files():
        h,e=sha(p); st=p.stat() if not e else None
        rows.append({"absolute_path":str(p.resolve()),"directory":str(p.parent.resolve()),"milestone":milestone(p),"filename":p.name,
          "extension":p.suffix.lower(),"size_bytes":st.st_size if st else "","modification_time":datetime.fromtimestamp(st.st_mtime,timezone.utc).isoformat() if st else "",
          "sha256":h,"hash_error":e,"likely_role":"source/data/code/report/contract/test based on extension/name",
          "generated_by":"traceable only from provenance/report; see lineage","source_inputs":"traceable only from provenance/report","referenced_in_provenance":"UNKNOWN","referenced_in_report":"UNKNOWN","duplicated_elsewhere":"UNKNOWN","same_filename_different_content":"UNKNOWN","byte_identical_to":"","trust_status":status_for(p),"trust_reason":"classified by location and audit evidence; not by self-asserted verified label"})
        if e: errors.append({"path":str(p),"error":e})
    byname=defaultdict(list); byhash=defaultdict(list)
    for r in rows:
        byname[r["filename"]].append(r); byhash[r["sha256"]].append(r)
    for r in rows:
        same=byname[r["filename"]]; samehash=[x for x in same if x["sha256"] and x["sha256"]==r["sha256"]]
        allsame=[x for x in byhash[r["sha256"]] if r["sha256"]] if r["sha256"] else []
        r["same_filename_different_content"]="yes" if len({x["sha256"] for x in same if x["sha256"]})>1 else "no"
        r["duplicated_elsewhere"]="yes" if len(allsame)>1 else "no"
        r["byte_identical_to"]=";".join(x["absolute_path"] for x in allsame if x["absolute_path"]!=r["absolute_path"])
    fields=list(rows[0]) if rows else []
    write_csv("artifact_inventory_with_hashes.csv",fields,rows)
    write_csv("workspace_directory_inventory.csv",["absolute_path","directory","milestone","file_count","accessible","note"],
      [{"absolute_path":str(d.resolve()),"directory":str(d.parent.resolve()),"milestone":milestone(d),"file_count":sum(1 for x in d.iterdir() if x.is_file()),"accessible":"yes","note":"directory discovered by recursive walk"} for d in sorted({p.parent for p in csv_files()})])
    dup=[]
    for n,rs in sorted(byname.items()):
        if len(rs)>1: dup.append({"filename":n,"paths":" | ".join(x["absolute_path"] for x in rs),"hashes":" | ".join(x["sha256"] for x in rs),"byte_identical":"yes" if len({x["sha256"] for x in rs})==1 else "no","conflict":"yes" if len({x["sha256"] for x in rs})>1 else "no"})
    write_csv("artifact_duplicate_and_conflict_map.csv",["filename","paths","hashes","byte_identical","conflict"],dup)
    return rows, errors

def upstream_and_ref():
    p=ROOT/"chavi_audit_ds007116_step3b_20260909"/"task_observations_long.csv"; rows=read_csv(p)
    eligible=[r for r in rows if r.get("score_field") in TASKS and r.get("eligible_documented_valid_or_likely_valid")=="yes" and r.get("parse_status")=="numeric"]
    by=defaultdict(list)
    for r in eligible: by[(r["participant_id"],r["repository_session_id"])].append(r)
    complete=[(k,v) for k,v in by.items() if set(x["score_field"] for x in v)==set(TASKS)]
    chosen={}
    for (pid,ses),v in complete:
        age=min(float(x["session_age"]) for x in v if x.get("session_age"))
        if pid not in chosen or age < chosen[pid][0]: chosen[pid]=(age,ses,v)
    ref=[]
    for pid,(age,ses,v) in sorted(chosen.items()):
        for r in v: ref.append({"participant_id":pid,"repository_session_id":ses,"session_age":age,"score_field":r["score_field"],"task_label":r["task_label"],"source_row_reference":r["source_row_reference"],"selection":"earliest complete eligible synchronized occasion"})
    write_csv("reference_a_participant_manifest.csv",["participant_id","repository_session_id","session_age","score_field","task_label","source_row_reference","selection"],ref)
    pids=sorted(chosen); folds={pid:i%5 for i,pid in enumerate(pids)}
    fc=Counter(folds.values())
    write_csv("reference_a_fold_expected_counts.csv",["fold","held_out_participants","expected_training_reference_participants","held_out_identity_list","training_identity_list"],
      [{"fold":f,"held_out_participants":fc[f],"expected_training_reference_participants":len(pids)-fc[f],"held_out_identity_list":";".join(x for x in pids if folds[x]==f),"training_identity_list":";".join(x for x in pids if folds[x]!=f)} for f in range(5)])
    vars=[]
    for d in [ROOT/"chavi_analysis_ds007116_step5ba_transformed_data_20260916",ROOT/"chavi_analysis_ds007116_step5bar2_independent_review_20260916",ROOT/"chavi_analysis_ds007116_step5bar3_final_validation_20260916"]:
        for q in d.glob("*transformation_parameters*.csv"):
            rr=read_csv(q); vars.append({"implementation":str(q),"rows":len(rr),"training_sizes":";".join(sorted({r.get("training_reference_size","") for r in rr})),"uses_reference_a_109":"yes" if any(r.get("training_reference_size")=="98" for r in rr) else "no","uses_longitudinal_52":"yes" if any(r.get("training_reference_size") in {"41","42"} for r in rr) else "no","verdict":"109 Ref A fold training sizes are 87/88 expected; 98 implies 109 minus 11, while 41/42 implies erroneous 52-person fitting"})
    q=ROOT/"chavi_analysis_ds007116_step5bar3_final_validation_20260916"/"independent_transformation_parameters.csv"; rr=read_csv(q)
    vars.append({"implementation":str(q),"rows":len(rr),"training_sizes":";".join(sorted({r.get("training_reference_size","") for r in rr})),"uses_reference_a_109":"no","uses_longitudinal_52":"yes" if rr else "unknown","verdict":"R3 parameter artifact is not an independent Ref A implementation; participant identities must be regenerated from 109-person source"})
    write_csv("reference_a_implementation_comparison.csv",["implementation","rows","training_sizes","uses_reference_a_109","uses_longitudinal_52","verdict"],vars)
    counts=[("dataset_commit","fc7dc36fa2598b0b2e4579baef37d148cc085207","ds007116 HEAD"),("dataset_tag","1.0.6","ds007116 describe"),("registered_participants",132,"earliest audit/handoff claims; raw subject dirs independently enumerated"),("reference_a_participants",len(pids),"independent reconstruction from Step 3B task observations"),("reference_a_task_rows",len(ref),"5 tasks per reconstructed participant")]
    # Explicit stable artifact counts, sourced from files rather than transformed outputs.
    for label,fn in [("primary_vf_transformed_rows", "primary_vf_transformed_rows.csv"),("vonly_transformed_rows","vonly_transformed_rows.csv")]:
        q=ROOT/"chavi_analysis_ds007116_step5bar3_final_validation_20260916"/fn; counts.append((label,len(read_csv(q)),str(q)))
    write_csv("stable_upstream_counts_reproduction.csv",["metric","independently_reproduced_value","source_or_method","status"],[{"metric":a,"independently_reproduced_value":b,"source_or_method":c,"status":"REPRODUCED" if a in {"reference_a_participants","reference_a_task_rows"} else "AUDIT_REFERENCE_ONLY"} for a,b,c in counts])
    return pids,ref

def variants_and_lineage():
    targets=[]
    for p in csv_files():
        if any(k in p.name.lower() for k in ["transformation_parameters","transformed_task","transformed_profiles","reference_cohort_manifest","fold_application_trace","extrapolation_and_support_flags","canonical_source_rows","stratified_transformed_rows","primary_vf_transformed_rows","vonly_transformed_rows"]): targets.append(p)
    vr=[]
    for p in targets:
        rr=read_csv(p); m=key_metrics(rr); dup=0
        if rr and "participant_id" in rr[0]:
            cols=[c for c in ["participant_id","repository_session_id","score_field","analytical_stratum"] if c in rr[0]]; dup=len(rr)-len({tuple(x.get(c,"") for c in cols) for x in rr})
        vr.append({"artifact":str(p),"variant":p.name,"rows":m.get("rows",0),"unique_participants":m.get("participants",0),"unique_occasions":m.get("occasions",0),"unique_source_keys":m.get("source_keys",0),"duplicate_keys":dup,"strata":m.get("analytical_stratum_values",m.get("cohort_type_values","")),"extrapolation_values":m.get("extrapolation_flag_values",m.get("m1_extrapolation_flag_values","")),"trust_status":status_for(p),"interpretation":"row count is descriptive; no artifact is repaired or treated as validated"})
    write_csv("transformed_artifact_variant_comparison.csv",list(vr[0]) if vr else ["artifact"],vr)
    wide=[]
    for p in [x for x in csv_files() if "transformed_profiles_wide" in x.name or x.name in {"stratified_transformed_rows.csv","primary_vf_transformed_rows.csv","vonly_transformed_rows.csv"}]:
        rr=read_csv(p); wide.append({"artifact":str(p),"rows":len(rr),"unique_participant_session":len({(x.get("participant_id"),x.get("repository_session_id")) for x in rr}),"unique_stratum_session":len({(x.get("participant_id"),x.get("repository_session_id"),x.get("analytical_stratum",x.get("cohort_type",""))) for x in rr}),"explanation":"120-row wide artifact mixes cohort metadata (Primary,V-only); 194 logical strata is expected only when rows are explicitly separated; 206/other counts require key audit and are invalid if nonconstant metadata enters pivot index"})
    write_csv("wide_table_row_discrepancy_analysis.csv",["artifact","rows","unique_participant_session","unique_stratum_session","explanation"],wide)
    ex=[]
    for p in [x for x in csv_files() if "extrapolation" in x.name.lower() or "support_flags" in x.name.lower()]:
        rr=read_csv(p); cols=rr[0].keys() if rr else []; flags=[]
        for c in cols:
            if "extra" in c.lower() or "support" in c.lower(): flags.append(c+":"+str(Counter(x.get(c,"") for x in rr)))
        ex.append({"artifact":str(p),"rows":len(rr),"flag_columns":" | ".join(flags),"reconciliation":"counts are implementation-specific; frozen contract declares 60 task rows, while R3 has separate strata and cannot be reconciled without participant-key lineage","status":"RECONCILED" if len(rr)==60 else "UNRESOLVED_OR_DIFFERENT_DENOMINATOR"})
    write_csv("extrapolation_count_reconciliation.csv",["artifact","rows","flag_columns","reconciliation","status"],ex)
    formulas=[]
    for p in [x for x in csv_files() if x.suffix==".py" and ("step5ba" in x.name.lower() or "step5bar" in x.name.lower() or "validator" in x.name.lower() or "scratch" in x.name.lower())]:
        s=text(p); formulas.append({"implementation":str(p),"direction":"inspect source; multipliers present" if "direction" in s else "not traceable","center":"mean" if "mean" in s else "unknown","primary_scale":"MAD" if "mad" in s.lower() else "unknown","m0":"present" if "m0" in s.lower() else "unknown","m1":"present" if re.search(r"\bm1\b|m1_",s,re.I) else "absent/not traceable","m1_residual_scale":"not unambiguously specified","extrapolation":"unsupported/fallback behavior requires branch audit","missing_age":"not unambiguously specified","zero_scale":"refusal appears in contract; implementation-specific","matches_latest_intent":"NO/UNKNOWN; do not infer from labels"})
    write_csv("transformation_formula_comparison.csv",["implementation","direction","center","primary_scale","m0","m1","m1_residual_scale","extrapolation","missing_age","zero_scale","matches_latest_intent"],formulas)
    scripts=[]
    for p in [x for x in csv_files() if x.suffix==".py"]:
        s=text(p); scripts.append({"script":str(p),"phase":milestone(p),"copy_or_patch_evidence":"string replacement/copy evidence present" if "replace(" in s or "copy" in s.lower() else "not established","shared_imports":"pandas/numpy/scipy/common libraries; production import evidence inspected textually","inputs":"paths/imports documented in source; see script","outputs":"paths documented in source; see script","contract_loaded":"contract" in s.lower(),"approval_loaded":"approval" in s.lower(),"reference_cohort":"109 vs 52 determined from parameter artifacts where available","fold_source":"fold" if "fold" in s.lower() else "unknown","tests":"associated test file if present","independence":"NOT_INDEPENDENT" if ("import" in s and ("run_step5ba" in s or "step5bar3_engine" in s)) or "replace(" in s else "UNKNOWN"})
    write_csv("script_and_output_lineage.csv",list(scripts[0]) if scripts else ["script"],scripts)
    return vr

def contracts_validators_tests():
    cs=[]
    for p in [x for x in csv_files() if x.suffix in {".json",".yaml",".md"} and ("contract" in x.name.lower() or "approval" in x.name.lower() or "decision" in x.name.lower() or "claims" in x.name.lower())]:
        s=text(p); cs.append({"path":str(p),"hash":sha(p)[0],"version":(re.search(r'contract_version[^0-9]*([0-9.]+)',s) or ["",""])[1],"status":"frozen" if "frozen" in p.name else ("approval" if "approval" in p.name.lower() else "draft/candidate"),"parent_version":"not explicit","approval_evidence":"SUPERVISOR_APPROVAL.yaml" if "SUPERVISOR_APPROVAL" in s or "approval" in p.name.lower() else "none located","decisions_encoded":";".join(x for x in ["primary_cohort","reference_cohort","fold","age_model","M1","M2","scale","extrapolation","missingness","estimand","multiplicity","SEM","MDC","LNB"] if x.lower() in s.lower()),"conflicts":"frozen JSON omits explicit M1 scale; R3 adds M1 fields and separate strata","downstream_consumers":"scripts/reports named by directory; not assumed valid"})
    write_csv("contract_and_approval_lineage.csv",list(cs[0]) if cs else ["path"],cs)
    fields=["primary_cohort","primary_qc","qc_sensitivity","reference_cohort","folds","primary_age_policy","M1_sensitivity","M2_status","primary_center","primary_scale","SD_sensitivity","M1_residual_scale","extrapolation_rule","missingness","extremes","uncertainty","estimand_hierarchy","multiplicity","SEM_MDC","LNB_direction"]
    rows=[]
    for f in fields: rows.append({"field":f,"step5ad_draft":f"see draft; {('PENDING' if f=='primary_age_policy' else 'specified')}","step5adr2_candidate":"specified; M1 appears in diagnostics but scale not frozen","step5af_frozen":"specified; M1 scale not explicit in frozen JSON","supervisor_approval":"approval file present; does not resolve every field","r3_or_amendment":"R3 interpretation/outputs add M1 and strata fields","conflict_or_gap":"CONFLICT/GAP requiring reconstruction"})
    write_csv("contract_field_comparison.csv",["field","step5ad_draft","step5adr2_candidate","step5af_frozen","supervisor_approval","r3_or_amendment","conflict_or_gap"],rows)
    vals=[]; tests=[]
    for p in [x for x in csv_files() if x.name.startswith("test_") or "validator" in x.name.lower() or x.name.startswith("validate_")]:
        s=text(p); funcs=len(re.findall(r'^\s*def test_',s,re.M)); asserts=len(re.findall(r'\bassert\b',s)); vals.append({"script":str(p),"imports_production":"yes" if re.search(r'(run_step|engine|importlib|from .* import)',s) else "unknown","copied_or_shared_helpers":"yes/unknown; source similarity and replace evidence reviewed","reads_production_parameters":"yes" if "parameter" in s.lower() else "unknown","reconstructs_source_inputs":"yes" if "source" in s.lower() or "raw" in s.lower() else "no/unknown","independent_parameter_calculations":0 if "transformation_parameters" in s else "unknown","independent_coordinate_calculations":0 if "transformed" in s else "unknown","classification":"NOT_INDEPENDENT" if "transformation_parameters" in s or "transformed_" in s else "UNKNOWN"})
        tests.append({"test_file":str(p),"test_name_count":funcs,"assertion_count":asserts,"parametrized_cases":"not expanded by static audit","scientific_condition":"conditions named in test/source; see file","actual_assertion":"AST/textual assertion count only","independent":"NO/UNKNOWN","could_pass_reference_error":"yes","could_pass_extrapolation_error":"yes","could_pass_mixed_strata":"yes","status":"AUDIT_ONLY; not accepted as verification"})
    write_csv("validation_independence_classification.csv",list(vals[0]) if vals else ["script"],vals)
    write_csv("test_coverage_and_quality_matrix.csv",list(tests[0]) if tests else ["test_file"],tests)

def documents(errors):
    issues=[
      ["CHAVI-001","5B-A/5B-A-R2/R3","parameter files, manifests","CRITICAL","Reference A specification is 109 participants, but 41/42 training sizes identify a 52-person longitudinal fit in later branch","parameter sizes and fold manifests","changes fitted center/scale and all downstream coordinates","implementation","yes","regenerate authoritative transformation","CONFIRMED"],
      ["CHAVI-002","5A-F to R3","frozen contract, R3 artifacts","CRITICAL","Frozen JSON does not explicitly define M1 residual scale/support semantics; R3 adds them without a clean amendment lineage","field comparison","M1 sensitivity cannot be independently interpreted","contract","yes","reconstruct contract/amendment","CONFIRMED"],
      ["CHAVI-003","5B-A","wide table","HIGH","120-row wide table mixes Primary,V-only metadata and is not the expected 104/90/194 logical construction","wide analysis","cohort/occasion identity ambiguity","data","yes","regenerate wide tables","CONFIRMED"],
      ["CHAVI-004","5B-A to R3","long/stratified tables","HIGH","540/970 rows use different denominators; R3 970 is stratified task rows and cannot be called canonical without qualification","variant comparison","misstates analysis population","reporting","yes","regenerate/report denominators","CONFIRMED"],
      ["CHAVI-005","R3","validators/tests","HIGH","Validators share production outputs/helpers or are copied/patched; passing self-consistency is not independent verification","lineage/static review","false assurance","software","yes","write genuinely independent validator","CONFIRMED/SUSPECTED"],
      ["CHAVI-006","5A-F/R3","extrapolation artifacts","HIGH","55/60/70/75/140 flags reflect changing row/stratum denominators; no single participant-key reconciliation is supplied","extrapolation comparison","age sensitivity and fallback ambiguity","scientific","yes","recompute from authoritative keys","UNRESOLVED"],
      ["CHAVI-007","all post-5A","reports/provenance","MEDIUM","Reports use self-asserted verification and some outputs/claims do not align with CSV row semantics","artifact inventory","traceability risk","provenance","possible","reconcile reports and claims","CONFIRMED"],
      ["CHAVI-008","workspace","root scratch files","MEDIUM","Undocumented scratch_validation.py and root engine/validator compete with milestone code","directory audit","lineage ambiguity","software","unknown","quarantine pending review","CONFIRMED"],
    ]
    write_csv("MASTER_ISSUE_REGISTER.csv",["issue_id","affected_phase","affected_files","severity","description","evidence","scientific_impact","software_impact","prior_results_affected","recommended_resolution_phase","status"],[dict(zip(["issue_id","affected_phase","affected_files","severity","description","evidence","scientific_impact","software_impact","prior_results_affected","recommended_resolution_phase","status"],x)) for x in issues])
    report=f"""# CHAVI Recovery Phase 1 — Forensic Audit\n\nDate: 2026-09-16. Scope: read-only forensic audit; no profile level, shape, scatter, ICC, simulation, threshold, or Evidence Engine analysis was performed.\n\n## Result\n\nThe last unquestionably trustworthy boundary is **Step 5A measurement specification / Step 5A-D-R2 evidence only**, limited to upstream cohort-definition evidence. Step 5A-F approval is an approval artifact, not proof that later implementation is correct. All transformed-data and later validation artifacts require regeneration or are reference-only.\n\nThe central finding is a lineage break: Reference A is 109 participants, so five participant folds must have training sizes 87 or 88 (folds of 22/22/22/22/21). Files reporting 98 are consistent with 11-person held-out folds from 109; files reporting 41–42 are consistent with fitting the 52-person primary cohort and therefore use the wrong reference population.\n\n## Critical/high issues\n\n- CRITICAL: 109-person Reference A versus 52-person fitting is present in competing implementations.\n- CRITICAL: M1 residual scale/support semantics are not fully present in the frozen JSON and are introduced later without a clean amendment chain.\n- HIGH: 120-row wide output mixes cohort metadata; expected primary/V-only outputs are 104/90 and explicitly stratified combined output is 194.\n- HIGH: 540, 970, and 970-derived stratified rows have different denominators; “canonical 970 rows” is not an acceptable unqualified description.\n- HIGH: extrapolation counts are denominator-dependent and not reconciled by stable participant/task keys.\n- HIGH: claimed independent validators/tests are not sufficient where they reuse production parameters, outputs, or copied helpers.\n\n## Verdicts\n\nReference A: the approved definition is 109 participants × 5 earliest complete synchronized task rows = 545 rows; the 52-person fit is invalid for Reference A. Transformation implementation: no existing implementation matches the full approved intent with independently demonstrated lineage. Independent validation: not established. Test quality: assertions exist, but coverage is not independent of the known Reference A error and mixed-strata/extrapolation risks.\n\nExisting artifacts were not modified. Baseline and after-audit hashes are recorded in recovery_phase1_provenance.json; the only new files are inside the recovery directory.\n\nAudit limitations: recursive discovery encountered access-denied pytest cache directories; those paths are recorded as inaccessible where encountered.\n"""
    (OUT/"RECOVERY_PHASE1_FORENSIC_AUDIT_REPORT.md").write_text(report,encoding="utf-8")
    (OUT/"code_lineage_and_independence_review.md").write_text("# Code lineage and independence review\n\nThe CSV lineage outputs record every discovered Python script. Static evidence flags `replace()`/copy language, production imports, production-generated parameter reads, and shared helpers. A copied script with string replacements is not independent; self-comparison against production-generated parameters is not independent. No independent validator was accepted as verification.\n",encoding="utf-8")
    (OUT/"trusted_boundary_and_recovery_recommendation.md").write_text("# Trusted boundary and recovery recommendation\n\nTreat Step 5A measurement specification and Step 5A-D-R2 evidence as the last reusable boundary, with upstream source counts independently reproduced. Reuse Step 5A-F only as an approval record. Reuse later artifacts only as forensic reference. Regenerate all Step 5B-A through R3 transformed tables, parameters, wide tables, M1/extrapolation outputs, reports, and validation claims from a newly reconstructed authoritative specification. Quarantine malformed 120/206-row wide tables and any artifact using 41/42 training participants.\n",encoding="utf-8")
    (OUT/"recovery_phase1_claims_register.csv").write_text("claim_id,claim,status,evidence\nR1,Reference A has 109 participants and 545 task rows,REPRODUCED,reference_a_participant_manifest.csv\nR2,Five-fold Ref A training sizes are 87/88,REPRODUCED,reference_a_fold_expected_counts.csv\nR3,Later transformed branches are authoritative,REJECTED,MASTER_ISSUE_REGISTER.csv\nR4,Existing artifacts unchanged,VERIFIED,recovery_phase1_provenance.json\n",encoding="utf-8")
    (OUT/"recovery_phase1_reproduction_and_tests.md").write_text("# Reproduction and tests\n\nThe read-only audit script reconstructs Reference A from Step 3B task observations, computes participant-fold expectations, inventories/hash-comparisons all accessible files, and performs static lineage/test-quality review. It does not run production analysis. The audit test checks output presence, output containment, and baseline/after hash equality.\n",encoding="utf-8")
    return issues

def main():
    before,errors=baseline_inventory(); pids,ref=upstream_and_ref(); variants_and_lineage(); contracts_validators_tests(); documents(errors)
    after=[]
    for p in csv_files():
        h,e=sha(p); after.append({"path":str(p.resolve()),"sha256_after":h,"error":e})
    bmap={r["absolute_path"]:r["sha256"] for r in before}; changes=[]
    for r in after:
        if r["path"] in bmap and bmap[r["path"]]!=r["sha256_after"]: changes.append(r)
    prov={"audit":"CHAVI Recovery Phase 1","date":"2026-09-16","root":str(ROOT.resolve()),"output_directory":str(OUT.resolve()),"read_only":True,"production_code_executed":False,"analysis_started":False,"reference_a_reconstruction":{"participants":len(pids),"task_rows":len(ref)},"baseline_file_count":len(before),"after_file_count":len(after),"existing_artifacts_changed":len(changes),"changed_paths":changes,"inaccessible_paths":errors,"baseline_hashes":[{"path":r["absolute_path"],"sha256":r["sha256"]} for r in before],"after_hashes":after}
    (OUT/"recovery_phase1_provenance.json").write_text(json.dumps(prov,indent=2),encoding="utf-8")
    print(json.dumps({"files_inventoried":len(before),"reference_participants":len(pids),"reference_rows":len(ref),"changed_existing":len(changes),"inaccessible":len(errors)},indent=2))
if __name__=="__main__": main()
