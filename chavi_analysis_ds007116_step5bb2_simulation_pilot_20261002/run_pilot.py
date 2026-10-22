"""Execute/resume the frozen 600-dataset Step 5B-B2 simulation pilot."""
from __future__ import annotations
import csv,gzip,hashlib,json,math,sys,time
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True
from simulation_core import *
BASE=Path(__file__).resolve().parent;RUNTIME=BASE/"runtime_checkpoint";RUNTIME.mkdir(exist_ok=True)
SCENARIO_IDS=tuple(SCENARIOS);METHODS=("P1_oracle_conditional","P2_fixed_transform","P3_joint_unstratified","P4_joint_fold_stratified");SCALES=("MAD","SD");ENDPOINTS=("level_icc_a1","mean_level_change","rms_shape_displacement");B=499;R=100
REASONS={0:"",1:"unsupported_reference_fit",2:"undefined_statistic",3:"structurally_undefined_oracle_reference"}

def _open(name,shape,dtype,fill):
 p=RUNTIME/name
 if p.exists():return np.lib.format.open_memmap(p,mode="r+",dtype=dtype,shape=shape)
 a=np.lib.format.open_memmap(p,mode="w+",dtype=dtype,shape=shape);a[:]=fill;a.flush();return a
def load_truth_refs():
 d=json.loads((BASE/"truth_reference_parameters.json").read_text(encoding="utf-8"));out={}
 for k,v in d.items():sid,scale=k.split("|");out[(sid,scale,"reference")]=v
 return out
def batch_fixed(z,W):
 W=np.asarray(W,float);n=52.;level=z.mean(2);q=z-level[:,:,None];dl=level[:,1]-level[:,0];ds2=np.sum((q[:,1]-q[:,0])**2,axis=1)/5
 mean=W@dl/n;rms=np.sqrt(W@ds2/n)
 origin=float(level.mean());unit=float(np.max(np.abs(level-origin)));icc=np.full(len(W),np.nan)
 if unit>0:
  y=(level-origin)/unit;rm=y.mean(1);row2=np.sum(y*y,axis=1);sumrow=np.sum(y,axis=1)
  gm=W@sumrow/(2*n);cm=W@y/n
  msr=2*(W@(rm*rm)-n*gm*gm)/(n-1);msc=n*np.sum((cm-gm[:,None])**2,axis=1)
  sst=W@row2-2*n*gm*gm;ssr=(n-1)*msr;ssc=msc;mse=(sst-ssr-ssc)/(n-1)
  den=msr+mse+2*(msc-mse)/n;rel=np.maximum.reduce([np.abs(msr),np.abs(msc),np.abs(mse),np.abs(den)])
  ok=(rel>0)&(np.abs(den)>64*EPS*rel);icc[ok]=(msr[ok]-mse[ok])/den[ok]
 return np.stack([icc,mean,rms],axis=1)
def dataset_hash(pair,aux):
 h=hashlib.sha256();h.update(np.asarray(pair,"<f8").tobytes());h.update(np.asarray(aux,"<f8").tobytes());return h.hexdigest()
def fit_transform(pair,aux,tw,aw,needed,scale):
 fits,fail=fit_references(pair[:,0],aux,tw,aw,needed,scale);z=transform_targets(pair,fits,needed);return z,fits,fail
def main(limit=None):
 truth=load_truth_refs();N=len(SCENARIO_IDS)*R
 boot=_open("bootstrap_values.npy",(N,4,2,3,B),"float64",np.nan);bst=_open("bootstrap_status.npy",(N,4,2,3,B),"int8",-1)
 point=_open("point_values.npy",(N,4,2,3),"float64",np.nan);pst=_open("point_status.npy",(N,4,2,3),"int8",-1);done=_open("outer_done.npy",(N,),"int8",0)
 dsfile=RUNTIME/"simulated_outer_datasets.npz"
 if dsfile.exists():d=np.load(dsfile);pairs=d["pairs"];auxes=d["auxes"]
 else:
  pairs=np.empty((N,52,2,5));auxes=np.empty((N,57,5))
  for si,sid in enumerate(SCENARIO_IDS):
   for o in range(R):pairs[si*R+o],auxes[si*R+o]=generate_dataset(sid,o)
  np.savez_compressed(dsfile,pairs=pairs,auxes=auxes,folds=FOLDS)
 fit_audit=[];ledger=[];start=time.perf_counter();processed=0
 for si,sid in enumerate(SCENARIO_IDS):
  for o in range(R):
   idx=si*R+o
   if done[idx]:continue
   if limit is not None and processed>=limit:break
   pair=pairs[idx];aux=auxes[idx];ones_t=np.ones(52,dtype=int);ones_a=np.ones(57,dtype=int);tw,aw,sw=draw_multiplicities(sid,o,B)
   for sc,scale in enumerate(SCALES):
    ref=truth[(sid,scale,"reference")]
    if ref["status"]=="defined":
     ofits={f:{"center":np.asarray(ref["center"]),"scale":np.asarray(ref["scale"]),"status":"supported"} for f in range(5)};oz=transform_targets(pair,ofits)
     vals,reason=endpoints(oz,ones_t);arr=np.array([vals[e] if vals[e] is not None else np.nan for e in ENDPOINTS]);point[idx,0,sc]=arr;pst[idx,0,sc]=np.where(np.isfinite(arr),0,2)
     bv=batch_fixed(oz,tw);boot[idx,0,sc]=bv.T;bst[idx,0,sc]=np.where(np.isfinite(bv.T),0,2)
    else:pst[idx,0,sc]=3;bst[idx,0,sc]=3
    # P2 is a fixed-transform bootstrap: estimate the reference once from
    # the original outer dataset, then freeze it while resampling targets.
    ez,efits,efail=fit_transform(pair,aux,ones_t,ones_a,range(5),scale);vals,reason=endpoints(ez,ones_t);arr=np.array([vals[e] if vals[e] is not None else np.nan for e in ENDPOINTS])
    for m in [1,2,3]:point[idx,m,sc]=arr;pst[idx,m,sc]=np.where(np.isfinite(arr),0,1 if efail else 2)
    if not efail:
     fixed_bv=batch_fixed(ez,tw);boot[idx,1,sc]=fixed_bv.T;bst[idx,1,sc]=np.where(np.isfinite(fixed_bv.T),0,2)
    else:bst[idx,1,sc]=1
    for f,x in efits.items():
     for j,t in enumerate(TASK_ORDER):fit_audit.append({"scenario_id":sid,"outer_id":o,"reference_kind":"estimated_original","scale_method":scale,"fold":f,"task_id":t,"center":format(x["center"][j],".17g"),"scale":format(x["scale"][j],".17g"),"status":x["status"],"n_frequency":x["n_frequency"]})
    for mi,W in [(2,tw),(3,sw)]:
     for b in range(B):
      twa=W[b].astype(int,copy=False);awa=aw[b].astype(int,copy=False)
      if twa.sum()!=52 or awa.sum()!=57 or np.any(twa<0) or np.any(awa<0):raise ValueError("generated multiplicity invariant failure")
      needed=sorted(set(FOLDS[twa>0].tolist()))
      if o<5 and b in {0,1,2,17,101,498}:validate_multiplicity_plan(make_plan(twa,awa))
      z,fits,fail=fit_transform(pair,aux,twa,awa,needed,scale)
      vals,reason=endpoints(z,twa);arr=np.array([vals[e] if vals[e] is not None else np.nan for e in ENDPOINTS]);boot[idx,mi,sc,:,b]=arr;bst[idx,mi,sc,:,b]=np.where(np.isfinite(arr),0,1 if fail else 2)
      if o<5 and b in {0,1,2,17,101,498}:
       for f,x in fits.items():
        for j,t in enumerate(TASK_ORDER):fit_audit.append({"scenario_id":sid,"outer_id":o,"reference_kind":f"{METHODS[mi]}_bootstrap_{b}","scale_method":scale,"fold":f,"task_id":t,"center":format(x["center"][j],".17g"),"scale":format(x["scale"][j],".17g") if np.isfinite(x["scale"][j]) else "","status":x["status"],"n_frequency":x["n_frequency"]})
   done[idx]=1;boot.flush();bst.flush();point.flush();pst.flush();done.flush();processed+=1
   ledger.append({"scenario_id":sid,"outer_id":o,"run_index":idx,"status":"completed","dataset_sha256":dataset_hash(pair,aux),"target_n":52,"auxiliary_n":57,"fold_counts":"11;11;10;10;10"})
   if processed%10==0:print(json.dumps({"newly_completed":processed,"last":f"{sid}/{o}","elapsed_seconds":round(time.perf_counter()-start,2)}),flush=True)
  if limit is not None and processed>=limit:break
 # Full deterministic ledger reconstructed, including earlier resumed rows.
 allledger=[]
 for si,sid in enumerate(SCENARIO_IDS):
  for o in range(R):
   idx=si*R+o;allledger.append({"scenario_id":sid,"outer_id":o,"run_index":idx,"status":"completed" if done[idx] else "pending","dataset_sha256":dataset_hash(pairs[idx],auxes[idx]),"target_n":52,"auxiliary_n":57,"fold_counts":"11;11;10;10;10"})
 with (BASE/"outer_dataset_run_ledger.csv").open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=list(allledger[0]),lineterminator="\n");w.writeheader();w.writerows(allledger)
 # Regenerate the preselected fit audit for all completed first-five runs on consolidation via separate script; append current rows for smoke diagnostics.
 if fit_audit:
  mode="at" if (BASE/"reference_fit_audit_partial.csv").exists() else "wt"
  with (BASE/"reference_fit_audit_partial.csv").open(mode,encoding="utf-8",newline="") as f:
   w=csv.DictWriter(f,fieldnames=list(fit_audit[0]),lineterminator="\n");
   if mode=="wt":w.writeheader()
   w.writerows(fit_audit)
 print(json.dumps({"status":"complete" if np.all(done) else "partial","completed":int(done.sum()),"attempted":N,"newly_processed":processed,"seconds":time.perf_counter()-start},sort_keys=True))
if __name__=="__main__":
 limit=int(sys.argv[2]) if len(sys.argv)>2 and sys.argv[1]=="--limit" else None;main(limit)
