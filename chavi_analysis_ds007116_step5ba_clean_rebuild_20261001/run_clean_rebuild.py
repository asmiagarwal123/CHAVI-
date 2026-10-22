"""Production implementation for the adopted CHAVI Design-B transformation contract."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


OUT = Path(__file__).resolve().parent
TASKS = ["letter_nback","face_memory","matrix_reasoning","emotion_recognition","dominant_finger_tapping"]
STRATA = ["primary_vf","vonly_reselected","fixed_primary_pair_strict_v"]
SOURCES = {s:OUT/f"{s}_source_rows.csv" for s in STRATA}
MAD_DENOM = 0.6744897501960817
EPS = np.finfo(np.float64).eps


def read_csv(path):
    with Path(path).open("r",encoding="utf-8-sig",newline="") as h: return list(csv.DictReader(h))


def write_csv(path,rows,fields=None):
    fields=fields or list(rows[0])
    with Path(path).open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields,extrasaction="ignore",lineterminator="\n"); w.writeheader(); w.writerows(rows)


def sha256(path):
    d=hashlib.sha256()
    with Path(path).open("rb") as h:
        for b in iter(lambda:h.read(1024*1024),b""): d.update(b)
    return d.hexdigest()


def canonical_hash(values): return hashlib.sha256(("\n".join(sorted(values))+"\n").encode()).hexdigest()


def parameter_key_hash(fold,task,model,scale):
    return hashlib.sha256(f"B_target_plus_auxiliary|{fold}|{task}|{model}|{scale}\n".encode()).hexdigest()


def f(value):
    try:
        x=float(value); return x if math.isfinite(x) else None
    except (TypeError,ValueError): return None


def mean(values): return math.fsum(float(v) for v in values)/len(values)


def mad(values):
    a=np.asarray(values,dtype=np.float64); med=float(np.median(a)); return float(np.median(np.abs(a-med))/MAD_DENOM)


def sd(values):
    if len(values)<2: return math.nan
    m=mean(values); return math.sqrt(math.fsum((float(v)-m)**2 for v in values)/(len(values)-1))


def scale_status(scale,D,n):
    if n<2: return "insufficient_scale_observations"
    if not math.isfinite(scale): return "nonfinite_scale"
    if scale<=0: return "nonpositive_scale"
    if scale<=64*EPS*max(D,abs(scale)): return "numerically_degenerate_scale"
    return "supported"


def warnings(values,mad_value,sd_value):
    a=np.asarray(values,dtype=np.float64); D=float(np.max(a)-np.min(a)); maxabs=float(np.max(np.abs(a)))
    result=[]
    if len(np.unique(a))<len(a): result.append("ties_present")
    if D>0 and D<=64*EPS*maxabs: result.append("large_offset_representability_warning")
    if mad_value>0 and math.isfinite(sd_value) and sd_value/mad_value>1.3: result.append("large_sd_mad_ratio_descriptive")
    return ";".join(result)


def main():
    contract_path=OUT/"step5ba_rebuild_contract.json"; contract_hash=sha256(contract_path)
    adoption=json.loads((OUT/"protocol_adoption_record.json").read_text(encoding="utf-8"))
    if adoption["contract_sha256"]!=contract_hash: raise ValueError("contract hash mismatch")
    contract=json.loads(contract_path.read_text(encoding="utf-8"))
    if contract["reference_design"]!="B_target_plus_auxiliary": raise ValueError("wrong design")
    folds=read_csv(OUT/"fold_fitting_manifest.csv")
    fold_map={p:int(r["target_fold"]) for r in folds for p in r["held_out_target_identities"].split(";")}
    reference=read_csv(OUT/"reference_cohort_manifest.csv")
    ref_by_task=defaultdict(list)
    for r in reference: ref_by_task[r["task_key"]].append(r)
    all_source=[]
    for stratum in STRATA:
        rows=read_csv(SOURCES[stratum])
        if any(r["analytical_stratum"]!=stratum for r in rows): raise ValueError("mixed strata")
        all_source.extend(rows)

    params=[]; lookup={}
    for fold_row in folds:
        fold=int(fold_row["target_fold"]); training_ids=fold_row["training_identities"].split(";")
        if canonical_hash(training_ids)!=fold_row["training_identities_sha256"]: raise ValueError("training identity hash mismatch")
        for task in TASKS:
            tr=sorted((r for r in ref_by_task[task] if r["participant_id"] in set(training_ids)),key=lambda r:r["participant_id"])
            y=[float(r["parsed_score"]) for r in tr]; ids=[r["participant_id"] for r in tr]
            source_keys=["|".join((r["participant_id"],r["session_id"],r["task_key"],r["source_row_reference"])) for r in tr]
            if ids!=training_ids: raise ValueError(f"training identity rows mismatch fold={fold} task={task}")
            c=mean(y); m0_res=[v-c for v in y]; mad0=mad(y); sd0=sd(y); D0=max(y)-min(y)
            for scale_name,scale in (("MAD",mad0),("SD",sd0)):
                status=scale_status(scale,D0,len(y)); reason="" if status=="supported" else status
                row={"reference_design":"B_target_plus_auxiliary","target_fold":fold,"task_key":task,"model":"M0","scale_method":scale_name,
                    "parameter_key_sha256":parameter_key_hash(fold,task,"M0",scale_name),"training_count":len(ids),"training_identities":";".join(ids),
                    "training_identities_sha256":canonical_hash(ids),"training_source_keys":";".join(source_keys),"training_source_keys_sha256":canonical_hash(source_keys),
                    "effective_training_count":len(ids),"effective_training_identities":";".join(ids),"effective_training_identities_sha256":canonical_hash(ids),
                    "excluded_training_identities":"","center":c,"age_center":"","centered_intercept":"","intercept":"","slope":"","scale":scale,
                    "training_score_range":D0,"support_age_min":"","support_age_max":"","fit_status":status,"failure_reason":reason,
                    "scientific_warnings":warnings(y,mad0,sd0),"contract_sha256":contract_hash}
                params.append(row); lookup[(fold,task,"M0",scale_name)]=row

            effective=[r for r in tr if f(r["session_age"]) is not None]
            eff_ids=[r["participant_id"] for r in effective]; excluded=sorted(set(ids)-set(eff_ids)); ages=np.asarray([float(r["session_age"]) for r in effective],dtype=np.float64); yy=np.asarray([float(r["parsed_score"]) for r in effective],dtype=np.float64)
            m1_base_status="supported"; m1_reason=""; age_center=intercept=slope=centered_intercept=math.nan; resid=[]; amin=amax=math.nan
            if len(effective)<3:
                m1_base_status=m1_reason="insufficient_effective_training_data"
            elif len(np.unique(ages))<2:
                m1_base_status=m1_reason="rank_deficient_age_model"
            else:
                age_center=float(np.mean(ages)); X=np.column_stack((np.ones(len(ages)),ages-age_center)); rank=int(np.linalg.matrix_rank(X))
                if rank<2: m1_base_status=m1_reason="rank_deficient_age_model"
                else:
                    coef=np.linalg.lstsq(X,yy,rcond=None)[0]; centered_intercept=float(coef[0]); slope=float(coef[1]); intercept=float(centered_intercept-slope*age_center)
                    pred=centered_intercept+slope*(ages-age_center); resid=[float(v) for v in (yy-pred)]; amin=float(np.min(ages)); amax=float(np.max(ages))
            D1=float(np.max(yy)-np.min(yy)) if len(yy) else math.nan
            mad1=mad(resid) if resid else math.nan; sd1=sd(resid) if resid else math.nan
            for scale_name,scale in (("MAD",mad1),("SD",sd1)):
                scale_state=scale_status(scale,D1,len(resid)); status=m1_base_status if m1_base_status!="supported" else scale_state; reason="" if status=="supported" else ("invalid_scale:"+scale_state if m1_base_status=="supported" else m1_reason)
                row={"reference_design":"B_target_plus_auxiliary","target_fold":fold,"task_key":task,"model":"M1","scale_method":scale_name,
                    "parameter_key_sha256":parameter_key_hash(fold,task,"M1",scale_name),"training_count":len(ids),"training_identities":";".join(ids),
                    "training_identities_sha256":canonical_hash(ids),"training_source_keys":";".join(source_keys),"training_source_keys_sha256":canonical_hash(source_keys),
                    "effective_training_count":len(eff_ids),"effective_training_identities":";".join(eff_ids),"effective_training_identities_sha256":canonical_hash(eff_ids),
                    "excluded_training_identities":";".join(excluded),"center":"","age_center":age_center if math.isfinite(age_center) else "","centered_intercept":centered_intercept if math.isfinite(centered_intercept) else "",
                    "intercept":intercept if math.isfinite(intercept) else "","slope":slope if math.isfinite(slope) else "","scale":scale if math.isfinite(scale) else "",
                    "training_score_range":D1 if math.isfinite(D1) else "","support_age_min":amin if math.isfinite(amin) else "","support_age_max":amax if math.isfinite(amax) else "",
                    "fit_status":status,"failure_reason":reason,"scientific_warnings":warnings(resid,mad1,sd1) if resid else "","contract_sha256":contract_hash}
                params.append(row); lookup[(fold,task,"M1",scale_name)]=row
    params.sort(key=lambda r:(int(r["target_fold"]),TASKS.index(r["task_key"]),r["model"],r["scale_method"]))
    if len(params)!=100: raise ValueError("parameter count")
    write_csv(OUT/"transformation_parameters.csv",params)

    long=[]
    for r in sorted(all_source,key=lambda x:(STRATA.index(x["analytical_stratum"]),x["participant_id"],int(x["session_id"].split("-")[1]),TASKS.index(x["task_key"]))):
        pid=r["participant_id"]; fold=fold_map[pid]; y=f(r["parsed_score"]); age=f(r["session_age"])
        for model in ("M0","M1"):
            for scale_name in ("MAD","SD"):
                p=lookup[(fold,r["task_key"],model,scale_name)]; supported=p["fit_status"]=="supported"; reason="" if supported else p["failure_reason"]; coordinate=None; prediction=None; residual=None
                if y is None: supported=False; reason="missing_or_nonfinite_score"
                elif model=="M0" and supported:
                    residual=y-f(p["center"]); coordinate=residual/f(p["scale"])
                elif model=="M1" and supported:
                    if age is None: supported=False; reason="missing_or_nonfinite_target_age"
                    elif age < f(p["support_age_min"]) or age > f(p["support_age_max"]): supported=False; reason="outside_inclusive_training_age_support"
                    else:
                        prediction=f(p["centered_intercept"])+f(p["slope"])*(age-f(p["age_center"])); residual=y-prediction
                        if not math.isfinite(prediction) or not math.isfinite(residual): supported=False; reason="nonfinite_prediction_or_residual"
                        else: coordinate=residual/f(p["scale"])
                fallback_model=fallback_coordinate=fallback_reason=""
                if model=="M1" and not supported:
                    mp=lookup[(fold,r["task_key"],"M0",scale_name)]; fallback_model="M0"
                    if y is not None and mp["fit_status"]=="supported": fallback_coordinate=(y-f(mp["center"]))/f(mp["scale"])
                    else: fallback_reason="corresponding_m0_unsupported"
                long.append({"participant_id":pid,"analytical_stratum":r["analytical_stratum"],"session_id":r["session_id"],"task_key":r["task_key"],"model":model,"scale_method":scale_name,
                    "reference_design":"B_target_plus_auxiliary","target_fold":fold,"raw_score":r["raw_score"],"parsed_score":r["parsed_score"],"raw_qc_code":r["raw_qc_code"],"session_age":r["session_age"],
                    "coordinate":"" if coordinate is None else coordinate,"supported":"yes" if supported else "no","unsupported_reason":reason,
                    "prediction":"" if prediction is None else prediction,"residual":"" if residual is None else residual,"age_support_status":"not_applicable" if model=="M0" else ("supported" if supported else "unsupported"),
                    "extrapolation":"false" if model=="M0" else ("true" if reason=="outside_inclusive_training_age_support" else "false"),
                    "fallback_model":fallback_model,"fallback_coordinate":fallback_coordinate,"fallback_reason":fallback_reason,
                    "parameter_key_sha256":p["parameter_key_sha256"],"training_identities_sha256":p["training_identities_sha256"],"contract_sha256":contract_hash,
                    "source_filename":r["source_filename"],"source_row_reference":r["source_row_reference"],"comparability_status":r["comparability_status"]})
    if len(long)!=5520: raise ValueError(f"long count {len(long)}")
    write_csv(OUT/"transformed_task_observations_long.csv",long)
    for stratum in STRATA: write_csv(OUT/f"{stratum}_transformed_long.csv",[r for r in long if r["analytical_stratum"]==stratum])

    # Safe pivot: task-varying fields become task-prefixed columns.
    groups=defaultdict(dict)
    for r in long:
        key=(r["participant_id"],r["analytical_stratum"],r["session_id"],r["model"],r["scale_method"])
        if r["task_key"] in groups[key]: raise ValueError("pivot row multiplication")
        groups[key][r["task_key"]]=r
    wide=[]
    for key,task_rows in sorted(groups.items(),key=lambda x:(STRATA.index(x[0][1]),x[0][0],int(x[0][2].split("-")[1]),x[0][3],x[0][4])):
        if set(task_rows)!=set(TASKS): raise ValueError(f"incomplete wide tasks {key}")
        fold_values={r["target_fold"] for r in task_rows.values()}; age_values={r["session_age"] for r in task_rows.values()}; source_contracts={r["contract_sha256"] for r in task_rows.values()}
        if len(fold_values)!=1 or len(age_values)!=1 or len(source_contracts)!=1: raise ValueError("nonconstant occasion metadata")
        row={"participant_id":key[0],"analytical_stratum":key[1],"session_id":key[2],"model":key[3],"scale_method":key[4],"reference_design":"B_target_plus_auxiliary","target_fold":next(iter(fold_values)),"session_age":next(iter(age_values)),"contract_sha256":contract_hash}
        for task in TASKS:
            tr=task_rows[task]
            for name in ("coordinate","supported","unsupported_reason","fallback_model","fallback_coordinate","parameter_key_sha256","training_identities_sha256","raw_score","raw_qc_code","source_row_reference"):
                row[f"{task}_{name}"]=tr[name]
        wide.append(row)
    if len(wide)!=1104: raise ValueError(f"wide count {len(wide)}")
    write_csv(OUT/"transformed_profiles_wide.csv",wide)
    for stratum in STRATA: write_csv(OUT/f"{stratum}_transformed_wide.csv",[r for r in wide if r["analytical_stratum"]==stratum])

    # Round-trip every task-specific value from wide to long.
    original={(r["participant_id"],r["analytical_stratum"],r["session_id"],r["task_key"],r["model"],r["scale_method"]):r for r in long}
    checked=0
    for w in wide:
        for task in TASKS:
            o=original[(w["participant_id"],w["analytical_stratum"],w["session_id"],task,w["model"],w["scale_method"])]
            for name in ("coordinate","supported","unsupported_reason","fallback_model","fallback_coordinate","parameter_key_sha256","training_identities_sha256","raw_score","raw_qc_code","source_row_reference"):
                if str(w[f"{task}_{name}"])!=str(o[name]): raise ValueError(f"roundtrip mismatch {task} {name}")
            checked+=1

    audit=[]
    for stratum in STRATA:
        for model in ("M0","M1"):
            for task in TASKS:
                for scale_name in ("MAD","SD"):
                    rr=[r for r in long if r["analytical_stratum"]==stratum and r["model"]==model and r["task_key"]==task and r["scale_method"]==scale_name]
                    reasons=Counter(r["unsupported_reason"] or "supported" for r in rr)
                    coords=[abs(float(r["coordinate"])) for r in rr if r["coordinate"]!=""]
                    audit.append({"analytical_stratum":stratum,"model":model,"task_key":task,"scale_method":scale_name,"denominator":len(rr),"supported":sum(r["supported"]=="yes" for r in rr),"unsupported":sum(r["supported"]=="no" for r in rr),"reason_counts_json":json.dumps(dict(sorted(reasons.items())),separators=(",",":")),"fallback_available":sum(r["fallback_coordinate"]!="" for r in rr),"max_abs_coordinate":"" if not coords else max(coords)})
    write_csv(OUT/"support_scale_and_fallback_audit.csv",audit)
    source_by_stratum={s:read_csv(SOURCES[s]) for s in STRATA}
    physical={ (r["participant_id"],r["session_id"],r["task_key"],r["source_row_reference"]) for rows in source_by_stratum.values() for r in rows }
    recon=[]
    expected={"primary_vf":(52,104,520,2080,416),"vonly_reselected":(45,90,450,1800,360),"fixed_primary_pair_strict_v":(41,82,410,1640,328)}
    for s,e in expected.items():
        rows=source_by_stratum[s]; actual=(len({r["participant_id"] for r in rows}),len({(r["participant_id"],r["session_id"]) for r in rows}),len(rows),len([r for r in long if r["analytical_stratum"]==s]),len([r for r in wide if r["analytical_stratum"]==s]))
        recon.append({"scope":s,"participants":actual[0],"occasions":actual[1],"source_stratum_rows":actual[2],"expanded_long_rows":actual[3],"wide_rows":actual[4],"expected_tuple":"/".join(map(str,e)),"matches_expected":"yes" if actual==e else "no"})
    recon += [{"scope":"all_strata","participants":"","occasions":"","source_stratum_rows":len(all_source),"expanded_long_rows":len(long),"wide_rows":len(wide),"expected_tuple":"1380/5520/1104","matches_expected":"yes" if (len(all_source),len(long),len(wide))==(1380,5520,1104) else "no"},
              {"scope":"unique_physical_source_union","participants":len({x[0] for x in physical}),"occasions":len({x[:2] for x in physical}),"source_stratum_rows":len(physical),"expanded_long_rows":"","wide_rows":"","expected_tuple":"not a stratified denominator","matches_expected":"not_applicable"}]
    write_csv(OUT/"denominator_and_identity_reconciliation.csv",recon)
    claims=[
      {"claim_id":"CLM-001","claim":"Coordinates are computationally generated under the user-adopted Design-B protocol","status":"eligible_after_independent_validation"},
      {"claim_id":"CLM-002","claim":"Coordinates are internal sample-referenced task coordinates","status":"supported_boundary"},
      {"claim_id":"CLM-003","claim":"Coordinates are population norms or clinical z-scores","status":"prohibited"},
      {"claim_id":"CLM-004","claim":"Five tasks are five validated domains or permanent strengths/weaknesses","status":"not_established"},
      {"claim_id":"CLM-005","claim":"M0/MAD is optimal","status":"not_established_adopted_choice"},
      {"claim_id":"CLM-006","claim":"Historical R2 diagnostics validate Design B","status":"false_historical_R2_used_Design_C"},
      {"claim_id":"CLM-007","claim":"Bootstrap/profile reliability/reportability","status":"deferred_not_computed"}]
    write_csv(OUT/"claims_register.csv",claims)
    summary={"contract_sha256":contract_hash,"parameters":len(params),"long_rows":len(long),"wide_rows":len(wide),"roundtrip_task_records":checked,"unique_physical_source_rows":len(physical),"parameter_status_counts":dict(Counter(r["fit_status"] for r in params)),"coordinate_status_counts":dict(Counter(r["supported"] for r in long))}
    (OUT/"production_results.json").write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__": main()
