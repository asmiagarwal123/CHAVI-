"""Deterministic mechanism checks and real-path corruption tests."""
from __future__ import annotations
import copy,csv,json,math,sys
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True
from simulation_core import *
BASE=Path(__file__).resolve().parent
def expect_error(fn,needle):
 try:fn()
 except Exception as e:return needle.lower() in str(e).lower()
 return False
def run():
 checks=[]
 def add(i,name,ok,detail):checks.append({"check_id":i,"check":name,"status":"PASS" if ok else "FAIL","detail":detail})
 # A: reference-center cancellation at fixed scale.
 pair,_=generate_dataset("S1",999);scale=np.array([1.1,1.2,1.3,1.4,1.5]);c1=np.zeros(5);c2=np.array([2,-3,1,4,-2.])
 z1=(pair-c1)/scale;z2=(pair-c2)/scale;v1,_=endpoints(z1,np.ones(52,int));v2,_=endpoints(z2,np.ones(52,int))
 add("A","center perturbation cancellation",np.isclose(v1["mean_level_change"],v2["mean_level_change"]) and np.isclose(v1["rms_shape_displacement"],v2["rms_shape_displacement"]),"mean change and RMS shape unchanged")
 # B: fold-specific common offsets can alter between-person level ICC.
 base=np.column_stack([np.arange(52,dtype=float),np.arange(52,dtype=float)+np.sin(np.arange(52))*.2]);off=np.array([0,1,-1,2,-2.])[FOLDS]
 changed=base-off[:,None];a=stable_icc_a1(base,np.ones(52,int));b=stable_icc_a1(changed,np.ones(52,int))
 add("B","fold-center effect on level ICC",abs(a-b)>1e-8,f"base={a:.12g}; perturbed={b:.12g}")
 # C/D transformations.
 common=np.zeros((1,2,5));common[0,1]=.5;shape=np.zeros((1,2,5));shape[0,1]=.5*H[:,0]
 def pairparts(x):
  l=x.mean(2);q=x-l[:,:,None];return l[0,1]-l[0,0],math.sqrt(np.sum((q[0,1]-q[0,0])**2)/5)
 add("C","reference scale perturbation",np.isclose(pairparts(common/2)[0],pairparts(common)[0]/2) and np.isclose(pairparts(shape/2)[1],pairparts(shape)[1]/2),"endpoint magnitudes scale inversely")
 add("D","common versus shape shift decomposition",np.allclose(pairparts(common),(.5,0)) and np.allclose(pairparts(shape),(0,.5/math.sqrt(5))),"orthogonal level/shape shifts")
 # E: frequency weights versus explicit expansion.
 x=np.array([1.,2.,4.,8.]);w=np.array([2,0,3,1]);ex=np.repeat(x,w);pairs=np.array([[1,1],[2,2],[3,4],[4,5.]],float);wp=np.array([2,0,3,1]);pex=np.repeat(pairs,wp,axis=0)
 zp=np.zeros((4,2,5));zp[:,:,0]=pairs;zp[:,:,1]=pairs+.2;zp[:,:,2]=pairs-.1;zp[:,:,3]=pairs+.4;zp[:,:,4]=pairs-.5;zex=np.repeat(zp,wp,axis=0)
 we,_=endpoints(zp,wp);ee,_=endpoints(zex,np.ones(len(zex),int))
 ok=np.isclose(weighted_mean(x,w),ex.mean()) and np.isclose(weighted_sd(x,w),ex.std(ddof=1)) and np.isclose(weighted_median(x,w),np.median(ex)) and np.isclose(weighted_mad(x,w),np.median(abs(ex-np.median(ex)))/MAD_DENOM) and np.isclose(stable_icc_a1(pairs,wp),stable_icc_a1(pex,np.ones(len(pex),int))) and all(np.isclose(we[k],ee[k]) for k in we)
 add("E","integer frequency equivalence",ok,"mean/SD/median/MAD/ICC/change/RMS equal explicit expansion")
 # F: zero MAD and supported SD, without substitution.
 zx=np.array([0]*6+[1]*4,float);zw=np.ones(10,int);mad=weighted_mad(zx,zw);sd=weighted_sd(zx,zw)
 add("F","zero MAD versus SD",mad==0 and sd>0 and not scale_supported(zx,zw,mad)[0] and scale_supported(zx,zw,sd)[0],f"MAD={mad}; SD={sd}")
 # G: only fold 0 represented; unused folds not fitted.
 tw=np.zeros(52,int);tw[0]=52;aw=np.ones(57,int);p=make_plan(tw,aw);validate_multiplicity_plan(p);fit,fail=fit_references(pair[:,0],generate_dataset("S1",999)[1],tw,aw,p["needed_folds"],"SD")
 add("G","unrepresented folds",p["needed_folds"]==[0] and set(fit)=={0} and not fail,"unused folds explicitly not_needed")
 # H: support and ICC invariance.
 flags=profile_geometry([1,2,3,4,5],["yes"]*5)[0]==3 and expect_error(lambda:profile_geometry([1,2,3,4,5],["yes","yes","no","yes","yes"]),"unsupported") and expect_error(lambda:profile_geometry([1,2,3,4,5],["yes","yes",None,"yes","yes"]),"missing") and expect_error(lambda:profile_geometry([1,2,3,4,5],["yes","yes","maybe","yes","yes"]),"unknown")
 ip=np.array([[1,1],[2,2],[3,4],[4,5.]],float);iw=np.ones(4,int);ia=stable_icc_a1(ip,iw);ic=stable_icc_c1(ip,iw)
 inv=all(np.isclose(stable_icc_a1(ip*s,iw),ia) and np.isclose(stable_icc_c1(ip*s,iw),ic) for s in [1e-8,1,1e8]) and all(np.isclose(stable_icc_a1(ip+t,iw),ia) and np.isclose(stable_icc_c1(ip+t,iw),ic) for t in [-1e9,0,1e9])
 add("H","strict support and numerical invariance",flags and inv,"yes/no explicit; ICC invariant at 1e-8/1/1e8 and translations")
 # I: exact multiplicity validation and actual corruption paths.
 good=make_plan(np.bincount(np.arange(52)%17,minlength=52),np.bincount(np.arange(57)%19,minlength=57));validate_multiplicity_plan(good)
 corrupt=[]
 def bad(label,mut,needle):
  q=copy.deepcopy(good);mut(q);corrupt.append((label,expect_error(lambda:validate_multiplicity_plan(q),needle)))
 bad("omitted eligible target",lambda q:q["target_fit_by_fold"][str(q["needed_folds"][0])].pop(next(i for i in TARGET_IDS if q["fold_membership"][i]!=q["needed_folds"][0])),"omitted")
 bad("omitted auxiliary",lambda q:q["auxiliary_fit_by_fold"][str(q["needed_folds"][0])].pop(AUX_IDS[0]),"omitted")
 bad("added identity",lambda q:q["target_analysis"].__setitem__("T999",0),"added")
 bad("incorrect weight",lambda q:q["target_fit_by_fold"][str(q["needed_folds"][0])].__setitem__(next(i for i in TARGET_IDS if q["fold_membership"][i]!=q["needed_folds"][0]),99),"mismatch")
 bad("negative",lambda q:q["target_analysis"].__setitem__(TARGET_IDS[0],-1),"negative")
 bad("noninteger",lambda q:q["auxiliary_draw"].__setitem__(AUX_IDS[0],1.5),"noninteger")
 bad("changed fold",lambda q:q["fold_membership"].__setitem__(TARGET_IDS[0],4),"changed")
 def shift_map(q,key):q[key].__setitem__(TARGET_IDS[0],q[key][TARGET_IDS[0]]+1);q[key].__setitem__(TARGET_IDS[1],q[key][TARGET_IDS[1]]-1)
 bad("decoupled",lambda q:shift_map(q,"target_reference"),"decoupled")
 bad("visits",lambda q:shift_map(q,"visit_multiplicity"),"visits")
 f=str(good["needed_folds"][0]);held=next(i for i in TARGET_IDS if good["fold_membership"][i]==int(f));bad("heldout retained",lambda q:q["target_fit_by_fold"][f].__setitem__(held,1),"mismatch")
 add("I","complete multiplicity corruption rejection",all(x[1] for x in corrupt),";".join(f"{a}={'PASS' if b else 'FAIL'}" for a,b in corrupt))
 # Persist actual deterministic multiplicity fixture records.
 records=[]
 for mapname in ["target_analysis","target_reference","visit_multiplicity","auxiliary_draw"]:
  for ident,val in good[mapname].items():records.append({"fixture_id":"linked_integer_weights","map":mapname,"fold":"","identity":ident,"multiplicity":val})
 for mapname in ["target_fit_by_fold","auxiliary_fit_by_fold"]:
  for f,m in good[mapname].items():
   for ident,val in m.items():records.append({"fixture_id":"linked_integer_weights","map":mapname,"fold":f,"identity":ident,"multiplicity":val})
 with (BASE/"deterministic_multiplicity_fixture_records.csv").open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator="\n");w.writeheader();w.writerows(records)
 with (BASE/"mechanism_check_results.csv").open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=list(checks[0]),lineterminator="\n");w.writeheader();w.writerows(checks)
 result={"status":"PASS" if all(x["status"]=="PASS" for x in checks) else "FAIL","checks":len(checks),"passed":sum(x["status"]=="PASS" for x in checks)}
 (BASE/"mechanism_validation_results.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
 return result
if __name__=="__main__":
 r=run();print(json.dumps(r,sort_keys=True));raise SystemExit(0 if r["status"]=="PASS" else 1)
