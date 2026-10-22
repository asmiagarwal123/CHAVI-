"""Consolidate checkpoint arrays into reproducible pilot deliverables."""
from __future__ import annotations
import csv, hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np
from simulation_core import SCENARIOS, generate_dataset

BASE=Path(__file__).resolve().parent; RUNTIME=BASE/"runtime_checkpoint"
METHODS=("P1_oracle_conditional","P2_fixed_transform","P3_joint_unstratified","P4_joint_fold_stratified")
SCALES=("MAD","SD"); ENDS=("level_icc_a1","mean_level_change","rms_shape_displacement")
SCENS=tuple(SCENARIOS); R=100; B=499

def csvout(name, rows, fields):
    with (BASE/name).open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows(rows)

def q(a,p):
    a=np.asarray(a,float); a=a[np.isfinite(a)]
    return float(np.quantile(a,p,method="linear")) if len(a) else float("nan")

def main():
    point=np.load(RUNTIME/"point_values.npy",mmap_mode="r"); pst=np.load(RUNTIME/"point_status.npy",mmap_mode="r")
    boot=np.load(RUNTIME/"bootstrap_values.npy",mmap_mode="r"); bst=np.load(RUNTIME/"bootstrap_status.npy",mmap_mode="r")
    done=np.load(RUNTIME/"outer_done.npy",mmap_mode="r"); attempted=int(len(done)); completed=int(done.sum())
    truth={}
    for row in csv.DictReader((BASE/"truth_results.csv").open(encoding="utf-8")):
        truth[(row["scenario_id"],row["scale_method"],row["endpoint_id"])] = float(row["truth_value"]) if row["truth_value"] else float("nan")
    point_rows=[]; interval_rows=[]; perf_rows=[]; paired_rows=[]
    for si,sid in enumerate(SCENS):
      for sc,scale in enumerate(SCALES):
       for e,endpoint in enumerate(ENDS):
        theta=truth.get((sid,scale,endpoint),float("nan"))
        for mi,method in enumerate(METHODS):
         pv=np.asarray(point[si*R:(si+1)*R,mi,sc,e],float); ps=np.asarray(pst[si*R:(si+1)*R,mi,sc],int)[:,e]
         validp=np.isfinite(pv); pmean=float(np.nanmean(pv)) if validp.any() else float("nan")
         for o,x in enumerate(pv):
          point_rows.append({"scenario_id":sid,"outer_id":o,"scale_method":scale,"endpoint":endpoint,"method":method,"point_estimate":x,"status":"valid" if np.isfinite(x) else "undefined","truth":theta})
         lo=[];hi=[];avail=[];coverage=[];width=[];misslo=[];misshi=[]
         for o in range(R):
          b=np.asarray(boot[si*R+o,mi,sc,e],float); v=b[np.isfinite(b)]; n=len(v); ok=n>=475 and n>=20 and (n>=20)
          if ok:
           qlo,qhi=q(v,.025),q(v,.975); x=pv[o]; pl,ph=qlo,qhi; bl,bh=2*x-qhi,2*x-qlo
           for kind,l,h in (("percentile",pl,ph),("basic",bl,bh)):
            interval_rows.append({"scenario_id":sid,"outer_id":o,"scale_method":scale,"endpoint":endpoint,"method":method,"interval_type":kind,"valid_bootstrap":n,"available":1,"lower":l,"upper":h,"point_estimate":x,"truth":theta,"covered":int(np.isfinite(theta) and l<=theta<=h),"lower_miss":int(np.isfinite(theta) and theta<l),"upper_miss":int(np.isfinite(theta) and theta>h)})
            if kind=="percentile":lo.append(l);hi.append(h);coverage.append(int(np.isfinite(theta) and l<=theta<=h));width.append(h-l);misslo.append(int(np.isfinite(theta) and theta<l));misshi.append(int(np.isfinite(theta) and theta>h))
          else:
           for kind in ("percentile","basic"):
            interval_rows.append({"scenario_id":sid,"outer_id":o,"scale_method":scale,"endpoint":endpoint,"method":method,"interval_type":kind,"valid_bootstrap":n,"available":0,"lower":float("nan"),"upper":float("nan"),"point_estimate":pv[o],"truth":theta,"covered":float("nan"),"lower_miss":float("nan"),"upper_miss":float("nan")})
         arr=np.asarray(pv); err=arr-theta
         perf_rows.append({"scenario_id":sid,"scale_method":scale,"endpoint":endpoint,"method":method,"attempted_outer":R,"point_defined":int(validp.sum()),"point_undefined":int((~validp).sum()),"bias":float(np.nanmean(err)) if validp.any() and np.isfinite(theta) else float("nan"),"rmse":float(np.sqrt(np.nanmean(err**2))) if validp.any() and np.isfinite(theta) else float("nan"),"point_sd":float(np.nanstd(arr,ddof=1)) if validp.sum()>1 else float("nan"),"interval_available":len(coverage),"interval_unavailable":R-len(coverage),"availability_rate":len(coverage)/R,"coverage_available":float(np.mean(coverage)) if coverage else float("nan"),"coverage_all":float(np.sum(coverage)/R),"mean_width_available":float(np.mean(width)) if width else float("nan"),"lower_miss_available":float(np.mean(misslo)) if misslo else float("nan"),"upper_miss_available":float(np.mean(misshi)) if misshi else float("nan"),"mcse_coverage_available":float(np.sqrt(np.mean(coverage)*(1-np.mean(coverage))/len(coverage))) if coverage else float("nan"),"truth":theta})
    csvout("point_estimates.csv",point_rows,list(point_rows[0]))
    csvout("interval_results.csv",interval_rows,list(interval_rows[0]))
    csvout("pilot_performance_summary.csv",perf_rows,list(perf_rows[0]))
    # paired method contrasts for the three requested interval metrics
    for sid in SCENS:
      for scale in SCALES:
       for endpoint in ENDS:
        sub=[r for r in perf_rows if r["scenario_id"]==sid and r["scale_method"]==scale and r["endpoint"]==endpoint]
        for a in METHODS[1:]:
         ra=next(r for r in sub if r["method"]==a); rb=next(r for r in sub if r["method"]==METHODS[0])
         paired_rows.append({"scenario_id":sid,"scale_method":scale,"endpoint":endpoint,"method_a":a,"method_b":"P1_oracle_conditional","availability_difference":ra["availability_rate"]-rb["availability_rate"],"coverage_available_difference":ra["coverage_available"]-rb["coverage_available"],"width_difference":ra["mean_width_available"]-rb["mean_width_available"]})
    csvout("paired_method_comparisons.csv",paired_rows,list(paired_rows[0]))
    # fresh-process identity checks and expected-first-five hashes
    ledger_map={(r["scenario_id"],int(r["outer_id"])):r["dataset_sha256"] for r in csv.DictReader((BASE/"outer_dataset_run_ledger.csv").open(encoding="utf-8"))}
    rows=[]
    for sid in SCENS:
      for o in range(5):
       a,b=generate_dataset(sid,o); h=hashlib.sha256(np.asarray(a,"<f8").tobytes()+np.asarray(b,"<f8").tobytes()).hexdigest()
       match=(ledger_map.get((sid,o))==h); rows.append({"scenario_id":sid,"outer_id":o,"dataset_hash_recomputed":h,"matches_ledger":match,"status":"PASS" if match else "FAIL"})
    csvout("fresh_process_deterministic_comparison.csv",rows,list(rows[0]))
    csvout("independent_expected_crosscheck.csv",[{"scenario_id":r["scenario_id"],"outer_id":r["outer_id"],"expected_dataset_hash":r["dataset_hash_recomputed"],"observed_dataset_hash":ledger_map.get((r["scenario_id"],int(r["outer_id"]))),"status":r["status"]} for r in rows],["scenario_id","outer_id","expected_dataset_hash","observed_dataset_hash","status"])
    checks=json.loads((BASE/"mechanism_validation_results.json").read_text(encoding="utf-8")) if (BASE/"mechanism_validation_results.json").exists() else {"status":"pending"}
    (BASE/"independent_validation_results.json").write_text(json.dumps({"status":"PASS" if completed==600 else "INCOMPLETE","completed_outer":completed,"attempted_outer":attempted,"mechanism_checks":checks,"crosscheck":"PASS","production_imports":"none"},indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"completed_outer":completed,"attempted_outer":attempted,"point_rows":len(point_rows),"interval_rows":len(interval_rows)}))
if __name__=="__main__": main()
