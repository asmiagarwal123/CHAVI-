"""Independent source-based validator; does not import production code."""
from __future__ import annotations
import csv, hashlib, json, math, re
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np

OUT=Path(__file__).resolve().parent; ROOT=OUT.parent
STEP3B=ROOT/"chavi_audit_ds007116_step3b_20260909"; DATASET=ROOT/"ds007116"; STAGE=ROOT/"chavi_step1b_phenotype_staging_20260907"
TASKS=[("letter_nback","short_letter_2back","cnb_lnb_mcr","cnb_lnb_valid_code"),("face_memory","penn_face_memory_test","cnb_cpf_cr","cnb_cpf_valid_code"),("matrix_reasoning","penn_matrix_reasoning_test","cnb_pmat_cr","cnb_pmat_valid_code"),("emotion_recognition","penn_emotion_recognition_task","cnb_er40_cr","cnb_er40_valid_code"),("dominant_finger_tapping","short_computerized_finger_tapping_task","cnb_ctap_dom","cnb_ctap_valid_code")]
TKEY=[x[0] for x in TASKS]; META={x[0]:x[1:] for x in TASKS}; STRATA=["primary_vf","vonly_reselected","fixed_primary_pair_strict_v"]
MAD_DENOM=0.6744897501960817; EPS=np.finfo(float).eps; ABS=1e-12; REL=1e-10

def read(path,delimiter=","):
    with Path(path).open("r",encoding="utf-8-sig",newline="") as h:return list(csv.DictReader(h,delimiter=delimiter))
def write(path,rows):
    with Path(path).open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)
def hvals(v):return hashlib.sha256(("\n".join(sorted(v))+"\n").encode()).hexdigest()
def pkh(f,t,m,s):return hashlib.sha256(f"B_target_plus_auxiliary|{f}|{t}|{m}|{s}\n".encode()).hexdigest()
def finite(v):
    try:return math.isfinite(float(v))
    except:return False
def median(v):
    a=sorted(float(x) for x in v); n=len(a); return a[n//2] if n%2 else (a[n//2-1]+a[n//2])/2
def imean(v):return sum(float(x) for x in v)/len(v)
def imad(v):
    med=median(v);return median([abs(float(x)-med) for x in v])/MAD_DENOM
def isd(v):
    m=imean(v);return math.sqrt(sum((float(x)-m)**2 for x in v)/(len(v)-1)) if len(v)>=2 else math.nan
def state(s,D,n):
    if n<2:return "insufficient_scale_observations"
    if not math.isfinite(s):return "nonfinite_scale"
    if s<=0:return "nonpositive_scale"
    if s<=64*EPS*max(D,abs(s)):return "numerically_degenerate_scale"
    return "supported"
def close(a,b):return abs(a-b)<=ABS+REL*abs(b)

def reconstruct():
    obs=read(STEP3B/"task_observations_long.csv"); maps=read(STEP3B/"assessment_occasion_mapping_step3a.csv"); registered={r["participant_id"] for r in read(DATASET/"participants.tsv","\t")}
    mk=[(r["participant_id"],r["original_session_id"]) for r in maps]
    if len(mk)!=len(set(mk)):raise AssertionError("duplicate map key")
    md={k:r for k,r in zip(mk,maps)}; continuation={k for k,r in md.items() if "continuation" in (r["comparability_status"]+" "+r["proposed_cognitive_occasion_id"]).lower()}
    source={}
    for r in obs:
        if r["task_key"] not in META:continue
        k=(r["participant_id"],r["repository_session_id"],r["task_key"])
        if k in source or r["participant_id"] not in registered:raise AssertionError("source key/frame")
        stem,field,qc=META[r["task_key"]]
        if (r["task_table_stem"],r["score_field"],r["applicable_qc_fields"])!=(stem,field,qc):raise AssertionError("source metadata")
        parsed=float(r["original_value"]) if finite(r["original_value"]) else None
        if (parsed is None)!=(not finite(r["parsed_numeric_value"])) or (parsed is not None and parsed!=float(r["parsed_numeric_value"])):raise AssertionError("parse mismatch")
        source[k]=r
    occ=sorted({(p,s) for p,s,_ in source},key=lambda z:(z[0],int(z[1].split("-")[1])))
    if set(occ)-set(md):raise AssertionError("missing map")
    def comp(allowed):
        d=defaultdict(list)
        for p,s in occ:
            if (p,s) in continuation:continue
            if all((r:=source.get((p,s,t))) and finite(r["original_value"]) and r["raw_qc_codes"] in allowed for t in TKEY):d[p].append(s)
        return {p:sorted(set(ss),key=lambda x:int(x.split("-")[1])) for p,ss in d.items()}
    vf=comp({"V","F"}); vv=comp({"V"}); ref=sorted(vf); primary=sorted(p for p in vf if len(vf[p])>=2); vonly=sorted(p for p in vv if len(vv[p])>=2)
    ps={p:vf[p][:2] for p in primary}; vs={p:vv[p][:2] for p in vonly}; fixed=sorted(p for p in primary if all(source[(p,s,t)]["raw_qc_codes"]=="V" for s in ps[p] for t in TKEY)); fs={p:ps[p] for p in fixed}
    perm=[str(x) for x in np.random.default_rng(42).permuted(np.array(primary))]; fmap={p:i%5 for i,p in enumerate(perm)}
    strata={"primary_vf":(primary,ps),"vonly_reselected":(vonly,vs),"fixed_primary_pair_strict_v":(fixed,fs)}
    rows=[]
    for st,(ids,sessions) in strata.items():
        for p in ids:
            for s in sessions[p]:
                for t in TKEY:
                    r=source[(p,s,t)];rows.append({"participant_id":p,"analytical_stratum":st,"session_id":s,"task_key":t,"raw_score":r["original_value"],"parsed_score":format(float(r["original_value"]),".17g"),"raw_qc_code":r["raw_qc_codes"],"session_age":r["session_age"],"source_filename":r["source_filename"],"source_row_reference":r["source_row_reference"]})
    refrows=[]
    for p in ref:
        s=vf[p][0]
        for t in TKEY:
            r=source[(p,s,t)];refrows.append({"participant_id":p,"session_id":s,"task_key":t,"parsed_score":format(float(r["original_value"]),".17g"),"session_age":r["session_age"],"source_row_reference":r["source_row_reference"]})
    return ref,primary,fmap,refrows,rows

def calculate(contract_hash):
    refids,primary,fmap,refrows,source_rows=reconstruct(); bytask=defaultdict(list)
    for r in refrows:bytask[r["task_key"]].append(r)
    params=[];lookup={}
    for fold in range(5):
      held={p for p in primary if fmap[p]==fold}; trainids=sorted(set(refids)-held)
      for task in TKEY:
        tr=sorted([r for r in bytask[task] if r["participant_id"] in set(trainids)],key=lambda r:r["participant_id"]); ids=[r["participant_id"] for r in tr]; y=[float(r["parsed_score"]) for r in tr]; keys=["|".join((r["participant_id"],r["session_id"],r["task_key"],r["source_row_reference"])) for r in tr]
        c=imean(y); D=max(y)-min(y); m=imad(y); s=isd(y)
        for sn,sc in (("MAD",m),("SD",s)):
            st=state(sc,D,len(y));row={"reference_design":"B_target_plus_auxiliary","target_fold":fold,"task_key":task,"model":"M0","scale_method":sn,"parameter_key_sha256":pkh(fold,task,"M0",sn),"training_count":len(ids),"training_identities":";".join(ids),"training_identities_sha256":hvals(ids),"training_source_keys_sha256":hvals(keys),"effective_training_count":len(ids),"effective_training_identities_sha256":hvals(ids),"excluded_training_identities":"","center":c,"age_center":"","centered_intercept":"","intercept":"","slope":"","scale":sc,"training_score_range":D,"support_age_min":"","support_age_max":"","fit_status":st,"failure_reason":"" if st=="supported" else st,"contract_sha256":contract_hash};params.append(row);lookup[(fold,task,"M0",sn)]=row
        eff=[r for r in tr if finite(r["session_age"])];ei=[r["participant_id"] for r in eff]; ages=[float(r["session_age"]) for r in eff]; yy=[float(r["parsed_score"]) for r in eff]; base="supported";reason="";xbar=intercept=slope=cint=math.nan;res=[];amin=amax=math.nan
        if len(eff)<3:base=reason="insufficient_effective_training_data"
        elif len(set(ages))<2:base=reason="rank_deficient_age_model"
        else:
            xbar=imean(ages);ybar=imean(yy);den=sum((x-xbar)**2 for x in ages)
            if den<=0:base=reason="rank_deficient_age_model"
            else:
                slope=sum((x-xbar)*(y-ybar) for x,y in zip(ages,yy))/den;intercept=ybar-slope*xbar;cint=ybar;res=[y-(intercept+slope*x) for x,y in zip(ages,yy)];amin=min(ages);amax=max(ages)
        D1=max(yy)-min(yy) if yy else math.nan;m1=imad(res) if res else math.nan;s1=isd(res) if res else math.nan
        for sn,sc in (("MAD",m1),("SD",s1)):
            ss=state(sc,D1,len(res));st=base if base!="supported" else ss;fr="" if st=="supported" else ("invalid_scale:"+ss if base=="supported" else reason)
            row={"reference_design":"B_target_plus_auxiliary","target_fold":fold,"task_key":task,"model":"M1","scale_method":sn,"parameter_key_sha256":pkh(fold,task,"M1",sn),"training_count":len(ids),"training_identities":";".join(ids),"training_identities_sha256":hvals(ids),"training_source_keys_sha256":hvals(keys),"effective_training_count":len(ei),"effective_training_identities_sha256":hvals(ei),"excluded_training_identities":";".join(sorted(set(ids)-set(ei))),"center":"","age_center":xbar if math.isfinite(xbar) else "","centered_intercept":cint if math.isfinite(cint) else "","intercept":intercept if math.isfinite(intercept) else "","slope":slope if math.isfinite(slope) else "","scale":sc if math.isfinite(sc) else "","training_score_range":D1 if math.isfinite(D1) else "","support_age_min":amin if math.isfinite(amin) else "","support_age_max":amax if math.isfinite(amax) else "","fit_status":st,"failure_reason":fr,"contract_sha256":contract_hash};params.append(row);lookup[(fold,task,"M1",sn)]=row
    params.sort(key=lambda r:(int(r["target_fold"]),TKEY.index(r["task_key"]),r["model"],r["scale_method"]))
    coords=[]
    for r in sorted(source_rows,key=lambda x:(STRATA.index(x["analytical_stratum"]),x["participant_id"],int(x["session_id"].split("-")[1]),TKEY.index(x["task_key"]))):
      fold=fmap[r["participant_id"]];y=float(r["parsed_score"]);age=float(r["session_age"]) if finite(r["session_age"]) else None
      for model in ("M0","M1"):
       for sn in ("MAD","SD"):
        p=lookup[(fold,r["task_key"],model,sn)];sup=p["fit_status"]=="supported";reason="" if sup else p["failure_reason"];coord=pred=resid=None
        if model=="M0" and sup:resid=y-float(p["center"]);coord=resid/float(p["scale"])
        elif model=="M1" and sup:
            if age is None:sup=False;reason="missing_or_nonfinite_target_age"
            elif age<float(p["support_age_min"]) or age>float(p["support_age_max"]):sup=False;reason="outside_inclusive_training_age_support"
            else:pred=float(p["intercept"])+float(p["slope"])*age;resid=y-pred;coord=resid/float(p["scale"])
        fb="";fbc=""
        if model=="M1" and not sup:
            mp=lookup[(fold,r["task_key"],"M0",sn)];fb="M0";fbc=(y-float(mp["center"]))/float(mp["scale"]) if mp["fit_status"]=="supported" else ""
        coords.append({"participant_id":r["participant_id"],"analytical_stratum":r["analytical_stratum"],"session_id":r["session_id"],"task_key":r["task_key"],"model":model,"scale_method":sn,"reference_design":"B_target_plus_auxiliary","target_fold":fold,"raw_score":r["raw_score"],"parsed_score":r["parsed_score"],"raw_qc_code":r["raw_qc_code"],"session_age":r["session_age"],"coordinate":"" if coord is None else coord,"supported":"yes" if sup else "no","unsupported_reason":reason,"prediction":"" if pred is None else pred,"residual":"" if resid is None else resid,"age_support_status":"not_applicable" if model=="M0" else ("supported" if sup else "unsupported"),"extrapolation":"true" if reason=="outside_inclusive_training_age_support" else "false","fallback_model":fb,"fallback_coordinate":fbc,"parameter_key_sha256":p["parameter_key_sha256"],"training_identities_sha256":p["training_identities_sha256"],"contract_sha256":contract_hash,"source_filename":r["source_filename"],"source_row_reference":r["source_row_reference"]})
    return params,coords

def main():
    import hashlib
    cp=OUT/"step5ba_rebuild_contract.json";ch=hashlib.sha256(cp.read_bytes()).hexdigest(); expected_p,expected_c=calculate(ch)
    # Persist expectations before opening production outputs.
    write(OUT/"independent_expected_parameters.csv",expected_p);write(OUT/"independent_expected_coordinates_long.csv",expected_c)
    prodp=read(OUT/"transformation_parameters.csv");prodc=read(OUT/"transformed_task_observations_long.csv")
    pkey=lambda r:(r["reference_design"],r["target_fold"],r["task_key"],r["model"],r["scale_method"]);ckey=lambda r:(r["participant_id"],r["analytical_stratum"],r["session_id"],r["task_key"],r["model"],r["scale_method"])
    pp={pkey(r):r for r in prodp};ep={pkey({k:str(v) for k,v in r.items()}):r for r in expected_p};pc={ckey(r):r for r in prodc};ec={ckey({k:str(v) for k,v in r.items()}):r for r in expected_c}
    if set(pp)!=set(ep) or set(pc)!=set(ec):raise AssertionError("independent key mismatch")
    pnum=["center","age_center","centered_intercept","intercept","slope","scale","training_score_range","support_age_min","support_age_max"]
    pexact=["parameter_key_sha256","training_count","training_identities","training_identities_sha256","training_source_keys_sha256","effective_training_count","effective_training_identities_sha256","excluded_training_identities","fit_status","failure_reason","contract_sha256"]
    prows=[];maxp=0.0
    for k in sorted(pp):
        a,b=pp[k],ep[k];exact=all(a[x]==str(b[x]) for x in pexact);md=0.0;ok=True
        for x in pnum:
            av=a[x];bv=b[x]
            if (av=="")!=(bv==""):ok=False;continue
            if av!="":d=abs(float(av)-float(bv));md=max(md,d);ok &= close(float(av),float(bv))
        maxp=max(maxp,md);prows.append({"reference_design":k[0],"target_fold":k[1],"task_key":k[2],"model":k[3],"scale_method":k[4],"exact_fields_match":"yes" if exact else "no","numeric_within_tolerance":"yes" if ok else "no","max_abs_discrepancy":md,"validation_pass":"yes" if exact and ok else "no"})
    cnum=["coordinate","prediction","residual","fallback_coordinate"]
    cexact=["reference_design","target_fold","raw_score","parsed_score","raw_qc_code","session_age","supported","unsupported_reason","age_support_status","extrapolation","fallback_model","parameter_key_sha256","training_identities_sha256","contract_sha256","source_filename","source_row_reference"]
    crows=[];maxc=0.0
    for k in sorted(pc):
        a,b=pc[k],ec[k];exact=all(a[x]==str(b[x]) for x in cexact);md=0.0;ok=True;null=True
        for x in cnum:
            av=a[x];bv=b[x];null &= ((av=="")== (bv==""))
            if (av=="")!=(bv==""):ok=False
            elif av!="":d=abs(float(av)-float(bv));md=max(md,d);ok &= close(float(av),float(bv))
        maxc=max(maxc,md);crows.append({"participant_id":k[0],"analytical_stratum":k[1],"session_id":k[2],"task_key":k[3],"model":k[4],"scale_method":k[5],"exact_fields_match":"yes" if exact else "no","nullness_match":"yes" if null else "no","numeric_within_tolerance":"yes" if ok else "no","max_abs_discrepancy":md,"validation_pass":"yes" if exact and null and ok else "no"})
    write(OUT/"independent_parameter_crosscheck.csv",prows);write(OUT/"independent_coordinate_crosscheck.csv",crows)
    # Same physical rows repeated across strata must have identical transformation result/provenance.
    repeat=defaultdict(list)
    for r in prodc:repeat[(r["participant_id"],r["session_id"],r["task_key"],r["model"],r["scale_method"])].append(r)
    repeat_fail=0;repeat_checked=0
    for rr in repeat.values():
        if len(rr)>1:
            repeat_checked+=1;base=rr[0]
            for r in rr[1:]:
                if any(r[x]!=base[x] for x in ["coordinate","supported","unsupported_reason","fallback_coordinate","parameter_key_sha256","training_identities_sha256"]):repeat_fail+=1
    passed=all(r["validation_pass"]=="yes" for r in prows+crows) and repeat_fail==0
    results={"independent_validation_passed":passed,"expected_files_persisted_before_production_read":True,"parameter_records":len(prows),"coordinate_records":len(crows),"parameter_failures":sum(r["validation_pass"]!="yes" for r in prows),"coordinate_failures":sum(r["validation_pass"]!="yes" for r in crows),"max_parameter_abs_discrepancy":maxp,"max_coordinate_abs_discrepancy":maxc,"tolerance":{"absolute":ABS,"relative":REL},"repeated_physical_groups_checked":repeat_checked,"repeated_physical_failures":repeat_fail,"production_module_imported":False,"calculation_path":"centered covariance OLS and independently implemented sorted-median/two-pass scale"}
    (OUT/"validation_results.json").write_text(json.dumps(results,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(results,indent=2))
    if not passed:raise SystemExit(2)

if __name__=="__main__":main()
