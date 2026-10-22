"""Hardened M0 simulation, fitting, and profile-statistic primitives for Step 5B-B2.

Simulated data only. This module does not read CHAVI participant coordinates.
"""
from __future__ import annotations
import hashlib, math
from dataclasses import dataclass
from typing import Mapping
import numpy as np

TASK_ORDER=("letter_nback","face_memory","matrix_reasoning","emotion_recognition","dominant_finger_tapping")
MU=np.array([10.,12.,14.,16.,18.]); MAD_DENOM=0.6744897501960817; EPS=np.finfo(float).eps
FOLDS=np.array([0]*11+[1]*11+[2]*10+[3]*10+[4]*10,dtype=int)
TARGET_IDS=tuple(f"T{i:03d}" for i in range(52)); AUX_IDS=tuple(f"A{i:03d}" for i in range(57))
MASTER_SEED=20261002

def helmert():
 h=np.zeros((5,4))
 for j in range(4):
  k=j+1;h[:k,j]=1/math.sqrt(k*(k+1));h[k,j]=-k/math.sqrt(k*(k+1))
 return h
H=helmert(); P=np.eye(5)-np.ones((5,5))/5
C=np.fromfunction(lambda i,j:0.3**np.abs(i-j),(5,5),dtype=float)

SCENARIOS={
 "S1":{"rho_level":.8,"rho_shape":.8,"shift":"none","mechanism":"continuous"},
 "S2":{"rho_level":.8,"rho_shape":0.,"shift":"none","mechanism":"continuous"},
 "S3":{"rho_level":.8,"rho_shape":.8,"shift":"common_0.5","mechanism":"continuous"},
 "S4":{"rho_level":.8,"rho_shape":.8,"shift":"helmert1_0.5","mechanism":"continuous"},
 "S5":{"rho_level":.8,"rho_shape":.8,"shift":"none","mechanism":"nearest_integer_ties_to_even"},
 "S6":{"rho_level":.8,"rho_shape":.8,"shift":"none","mechanism":"independent_point_mass_p0.6"},
}

def keyed_rng(*parts):
 key="|".join(map(str,(MASTER_SEED,)+parts)).encode()
 seed=int.from_bytes(hashlib.sha256(key).digest()[:16],"little")
 return np.random.Generator(np.random.PCG64DXSM(seed))

def parse_support(flags):
 a=np.asarray(flags,dtype=object)
 if a.shape!=(5,):raise ValueError("exactly five support flags required")
 out=[]
 for x in a.tolist():
  if type(x) is bool:out.append(x)
  elif type(x) is str and x in {"yes","no"}:out.append(x=="yes")
  elif x is None or (type(x) is str and x==""):raise ValueError("missing support flag")
  else:raise ValueError(f"unknown support flag: {x!r}")
 return np.array(out,dtype=bool)

def profile_geometry(z,supported=("yes",)*5):
 z=np.asarray(z,float)
 if z.shape!=(5,) or not np.all(np.isfinite(z)):raise ValueError("five finite task coordinates required")
 if not np.all(parse_support(supported)):raise ValueError("unsupported task coordinate")
 level=float(np.mean(z));q=z-level
 return level,q,float(np.sqrt(np.dot(q,q)/5)),H.T@q

def _weights(w,n):
 w=np.asarray(w)
 if w.shape!=(n,) or np.issubdtype(w.dtype,np.bool_) or not np.issubdtype(w.dtype,np.integer) or np.any(w<0):raise ValueError("weights must be nonnegative integers")
 return w.astype(np.int64,copy=False)

def weighted_mean(x,w):
 x=np.asarray(x,float);w=_weights(w,len(x));n=int(w.sum())
 if n==0:return None
 return np.sum(x*w.reshape((-1,)+(1,)*(x.ndim-1)),axis=0)/n

def weighted_median(x,w):
 x=np.asarray(x,float);w=_weights(w,len(x));n=int(w.sum())
 if n==0:return None
 order=np.argsort(x,kind="stable");xs=x[order];ws=w[order];cs=np.cumsum(ws)
 def at(rank):return float(xs[np.searchsorted(cs,rank+1,side="left")])
 return at(n//2) if n%2 else (at(n//2-1)+at(n//2))/2

def weighted_sd(x,w):
 x=np.asarray(x,float);w=_weights(w,len(x));n=int(w.sum())
 if n<2:return None
 m=float(np.dot(w,x)/n);return math.sqrt(float(np.dot(w,(x-m)**2))/(n-1))

def weighted_mad(x,w):
 med=weighted_median(x,w)
 if med is None:return None
 raw=weighted_median(np.abs(np.asarray(x,float)-med),w)
 return None if raw is None else raw/MAD_DENOM

def scale_supported(x,w,scale):
 if scale is None or not math.isfinite(scale) or scale<=0:return False,"nonpositive_or_nonfinite_scale"
 present=np.asarray(x,float)[np.asarray(w)>0]
 if len(present)<2:return False,"insufficient_scale_observations"
 D=float(np.max(present)-np.min(present))
 if scale<=64*EPS*max(D,abs(scale)):return False,"numerically_degenerate_scale"
 return True,""

def fit_references(target_y1,aux_y1,target_w,aux_w,needed_folds,scale_method):
 target_y1=np.asarray(target_y1,float);aux_y1=np.asarray(aux_y1,float)
 tw=_weights(target_w,52);aw=_weights(aux_w,57);fits={};fail=[]
 for f in sorted(set(int(x) for x in needed_folds)):
  mask=FOLDS!=f;x=np.vstack([target_y1[mask],aux_y1]);w=np.r_[tw[mask],aw]
  center=np.array([weighted_mean(x[:,j],w) for j in range(5)],float);sc=[]
  for j in range(5):
   s=weighted_mad(x[:,j],w) if scale_method=="MAD" else weighted_sd(x[:,j],w)
   ok,reason=scale_supported(x[:,j],w,s)
   if not ok:fail.append(f"fold_{f}:task_{j}:{reason}");sc.append(np.nan)
   else:sc.append(s)
  fits[f]={"center":center,"scale":np.array(sc),"n_frequency":int(w.sum()),"status":"supported" if np.all(np.isfinite(sc)) else "unsupported"}
 return fits,fail

def transform_targets(pair,fits,needed=None):
 pair=np.asarray(pair,float);z=np.full_like(pair,np.nan);needed=set(range(5)) if needed is None else set(needed)
 for f in needed:
  ix=np.flatnonzero(FOLDS==f)
  if fits.get(f,{}).get("status")!="supported":continue
  z[ix]=(pair[ix]-fits[f]["center"])/fits[f]["scale"]
 return z

def stable_icc_a1(x,w):
 x=np.asarray(x,float);w=_weights(w,len(x));keep=w>0;x=x[keep];w=w[keep];n=int(w.sum());k=2
 if n<2 or x.shape[1]!=2 or not np.all(np.isfinite(x)):return None
 origin=float(np.sum(w[:,None]*x)/(n*k));centered=x-origin;unit=float(np.max(np.abs(centered)))
 if unit==0 or not math.isfinite(unit):return None
 y=centered/unit;gm=float(np.sum(w[:,None]*y)/(n*k));rm=np.mean(y,axis=1);cm=np.sum(w[:,None]*y,axis=0)/n
 msr=k*float(np.dot(w,(rm-gm)**2))/(n-1);msc=n*float(np.sum((cm-gm)**2))/(k-1)
 resid=y-rm[:,None]-cm[None,:]+gm;mse=float(np.sum(w[:,None]*resid**2))/((n-1)*(k-1))
 den=msr+(k-1)*mse+k*(msc-mse)/n;relative=max(abs(msr),abs(msc),abs(mse),abs(den))
 if relative==0 or abs(den)<=64*EPS*relative:return None
 return (msr-mse)/den

def stable_icc_c1(x,w):
 x=np.asarray(x,float);w=_weights(w,len(x));keep=w>0;x=x[keep];w=w[keep];n=int(w.sum());k=2
 if n<2 or x.shape[1]!=2 or not np.all(np.isfinite(x)):return None
 origin=float(np.sum(w[:,None]*x)/(n*k));centered=x-origin;unit=float(np.max(np.abs(centered)))
 if unit==0:return None
 y=centered/unit;gm=float(np.sum(w[:,None]*y)/(n*k));rm=np.mean(y,axis=1);cm=np.sum(w[:,None]*y,axis=0)/n
 msr=k*float(np.dot(w,(rm-gm)**2))/(n-1);resid=y-rm[:,None]-cm[None,:]+gm;mse=float(np.sum(w[:,None]*resid**2))/((n-1)*(k-1));den=msr+(k-1)*mse
 if den==0:return None
 return (msr-mse)/den

def endpoints(z,w):
 z=np.asarray(z,float);w=_weights(w,len(z));active=w>0
 if int(w.sum())<2:raise ValueError("at least two analysed observations required")
 if not np.all(np.isfinite(z[active])):return {k:None for k in ("level_icc_a1","mean_level_change","rms_shape_displacement")},"unsupported_coordinate"
 level=z.mean(axis=2);q=z-level[:,:,None];dl=level[:,1]-level[:,0];dshape2=np.sum((q[:,1]-q[:,0])**2,axis=1)/5
 vals={"level_icc_a1":stable_icc_a1(level,w),"mean_level_change":float(np.dot(w,dl)/w.sum()),"rms_shape_displacement":math.sqrt(float(np.dot(w,dshape2)/w.sum()))}
 reason="" if all(v is not None and math.isfinite(v) for v in vals.values()) else "undefined_statistic"
 return vals,reason

def generate_scores(n,rng,rho_level,rho_shape):
 u=rng.normal(size=n);v=rng.normal(size=n);ell1=math.sqrt(.5)*u;ell2=math.sqrt(.5)*(rho_level*u+math.sqrt(1-rho_level**2)*v)
 u=rng.normal(size=(n,4));v=rng.normal(size=(n,4));s1=math.sqrt(.5)*u;s2=math.sqrt(.5)*(rho_shape*u+math.sqrt(1-rho_shape**2)*v)
 chol=np.linalg.cholesky(.5*C);e1=rng.normal(size=(n,5))@chol.T;e2=rng.normal(size=(n,5))@chol.T
 return MU+ell1[:,None]+s1@H.T+e1,MU+ell2[:,None]+s2@H.T+e2

def generate_dataset(scenario_id,outer_id):
 s=SCENARIOS[scenario_id];rng=keyed_rng("outer_dataset",scenario_id,outer_id)
 y1,y2=generate_scores(52,rng,s["rho_level"],s["rho_shape"]);a1,_=generate_scores(57,rng,s["rho_level"],s["rho_shape"])
 if s["shift"]=="common_0.5":y2=y2+.5
 elif s["shift"]=="helmert1_0.5":y2=y2+.5*H[:,0]
 if s["mechanism"]=="nearest_integer_ties_to_even":y1=np.rint(y1);y2=np.rint(y2);a1=np.rint(a1)
 elif s["mechanism"]=="independent_point_mass_p0.6":
  y1=MU+(y1-MU)*(rng.random(y1.shape)<.4);y2=MU+(y2-MU)*(rng.random(y2.shape)<.4);a1=MU+(a1-MU)*(rng.random(a1.shape)<.4)
 return np.stack([y1,y2],axis=1),a1

def oracle_reference(scenario_id,scale_method,truth_table):
 row=truth_table[(scenario_id,scale_method,"reference")]
 if row["status"]!="defined":return None
 return {f:{"center":np.array(row["center"],float),"scale":np.array(row["scale"],float),"status":"supported","n_frequency":None} for f in range(5)}

def draw_multiplicities(scenario_id,outer_id,B=499):
 rt=keyed_rng("bootstrap_target_unstratified",scenario_id,outer_id);ra=keyed_rng("bootstrap_auxiliary",scenario_id,outer_id);rs=keyed_rng("bootstrap_target_stratified",scenario_id,outer_id)
 ti=rt.integers(0,52,size=(B,52));ai=ra.integers(0,57,size=(B,57));tw=np.apply_along_axis(np.bincount,1,ti,minlength=52);aw=np.apply_along_axis(np.bincount,1,ai,minlength=57)
 sw=np.zeros((B,52),dtype=np.int16)
 for f in range(5):
  ix=np.flatnonzero(FOLDS==f);draw=rs.integers(0,len(ix),size=(B,len(ix)))
  for b in range(B):sw[b,ix]=np.bincount(draw[b],minlength=len(ix))
 return tw.astype(np.int16),aw.astype(np.int16),sw

def make_plan(target_w,aux_w):
 tw={i:int(target_w[k]) for k,i in enumerate(TARGET_IDS)};aw={i:int(aux_w[k]) for k,i in enumerate(AUX_IDS)}
 needed=sorted(set(FOLDS[np.asarray(target_w)>0].tolist()))
 return {"target_analysis":tw,"target_reference":dict(tw),"visit_multiplicity":dict(tw),"auxiliary_draw":aw,
  "fold_membership":{i:int(FOLDS[k]) for k,i in enumerate(TARGET_IDS)},"needed_folds":needed,
  "target_fit_by_fold":{str(f):{i:(0 if int(FOLDS[k])==f else int(target_w[k])) for k,i in enumerate(TARGET_IDS)} for f in needed},
  "auxiliary_fit_by_fold":{str(f):dict(aw) for f in needed}}

def _valid_mult_map(m,ids,total,label):
 if set(m)!=set(ids):raise ValueError(f"{label}: omitted or added identities")
 for v in m.values():
  if type(v) is not int or v<0:raise ValueError(f"{label}: negative or noninteger multiplicity")
 if sum(m.values())!=total:raise ValueError(f"{label}: incorrect total multiplicity")

def validate_multiplicity_plan(plan):
 for key in ["target_analysis","target_reference","visit_multiplicity"]:_valid_mult_map(plan[key],TARGET_IDS,52,key)
 _valid_mult_map(plan["auxiliary_draw"],AUX_IDS,57,"auxiliary_draw")
 if plan["target_analysis"]!=plan["target_reference"]:raise ValueError("decoupled target analysis/reference weights")
 if plan["target_analysis"]!=plan["visit_multiplicity"]:raise ValueError("independently sampled visits")
 expected_membership={i:int(FOLDS[k]) for k,i in enumerate(TARGET_IDS)}
 if plan["fold_membership"]!=expected_membership:raise ValueError("changed fold membership")
 needed=sorted(f for f in range(5) if any(plan["target_analysis"][i]>0 and expected_membership[i]==f for i in TARGET_IDS))
 if sorted(plan["needed_folds"])!=needed:raise ValueError("incorrect needed folds")
 if set(plan["target_fit_by_fold"])!={str(f) for f in needed} or set(plan["auxiliary_fit_by_fold"])!={str(f) for f in needed}:raise ValueError("fitting map fold keys mismatch")
 for f in needed:
  tm=plan["target_fit_by_fold"][str(f)];am=plan["auxiliary_fit_by_fold"][str(f)]
  if set(tm)!=set(TARGET_IDS):raise ValueError("target fit: omitted or added identities")
  if set(am)!=set(AUX_IDS):raise ValueError("auxiliary fit: omitted or added identities")
  for i in TARGET_IDS:
   exp=0 if expected_membership[i]==f else plan["target_reference"][i]
   if type(tm[i]) is not int or tm[i]!=exp:raise ValueError("target fit multiplicity mismatch")
  for i in AUX_IDS:
   if type(am[i]) is not int or am[i]!=plan["auxiliary_draw"][i]:raise ValueError("auxiliary fit multiplicity mismatch")
 return True

def plan_arrays(plan):
 return np.array([plan["target_analysis"][i] for i in TARGET_IDS]),np.array([plan["auxiliary_draw"][i] for i in AUX_IDS]),plan["needed_folds"]
