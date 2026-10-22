"""Independent population-truth derivation/validation; imports no production helpers."""
from __future__ import annotations
import csv, hashlib, json, math, sys
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent;MASTER=20261002;PHI75=0.6744897501960817
MU=np.array([10.,12.,14.,16.,18.]);J=np.ones((5,5));P=np.eye(5)-J/5
H=np.zeros((5,4))
for j in range(4):
 k=j+1;H[:k,j]=1/math.sqrt(k*(k+1));H[k,j]=-k/math.sqrt(k*(k+1))
C=np.fromfunction(lambda i,j:.3**np.abs(i-j),(5,5),dtype=float)
SIGMA=.5*J+.5*(H@H.T)+.5*C
SC={"S1":(.8,.8,"none","continuous"),"S2":(.8,0.,"none","continuous"),"S3":(.8,.8,"common","continuous"),"S4":(.8,.8,"shape","continuous"),"S5":(.8,.8,"none","round"),"S6":(.8,.8,"none","mixture")}
def rng(*parts):
 seed=int.from_bytes(hashlib.sha256("|".join(map(str,(MASTER,)+parts)).encode()).digest()[:16],"little")
 return np.random.Generator(np.random.PCG64DXSM(seed))
def normcdf(x):return .5*(1+math.erf(x/math.sqrt(2)))
def rounded_variance(sd):
 return sum(k*k*(normcdf((k+.5)/sd)-normcdf((k-.5)/sd)) for k in range(-20,21))
def ref_params(sid,scale):
 if sid=="S5":
  sd=math.sqrt(rounded_variance(math.sqrt(1.4)));p0=2*normcdf(.5/math.sqrt(1.4))-1;p1=2*normcdf(1.5/math.sqrt(1.4))-1
  if not (p0<.5<p1):raise ValueError("rounded MAD convention not uniquely one")
  s=1/PHI75 if scale=="MAD" else sd;return MU.copy(),np.repeat(s,5),{"p_abs_zero":p0,"p_abs_le_one":p1}
 if sid=="S6":
  if scale=="MAD":return MU.copy(),np.zeros(5),{"point_mass_at_mu":.6,"structural_zero_mad":True}
  return MU.copy(),np.repeat(math.sqrt(.4*1.4),5),{"point_mass_at_mu":.6}
 return MU.copy(),np.repeat(math.sqrt(1.4),5),{"normal_mad_equals_sd":True}
def moment_truth(sid,scale):
 center,s,_=ref_params(sid,scale)
 if np.any(s==0):return None
 rl,rs,shift,mech=SC[sid];cross=.5*rl*J+.5*rs*(H@H.T);within=SIGMA.copy()
 if mech=="mixture":
  within=np.where(np.eye(5,dtype=bool),.4*SIGMA,.16*SIGMA);cross=.16*cross
 D=np.diag(1/s);v=D@within@D;cv=D@cross@D
 delta=np.zeros(5)
 if shift=="common":delta=np.repeat(.5,5)
 elif shift=="shape":delta=.5*H[:,0]
 dz=D@delta;a=np.ones(5)/5
 vl=float(a@v@a);cov=float(a@cv@a);dmean=float(a@dz)
 icc=2*cov/(2*vl+dmean*dmean)
 dcov=2*v-2*cv;rms=math.sqrt((float(np.trace(P@dcov))+float(dz@P@dz))/5)
 return {"level_icc_a1":icc,"mean_level_change":dmean,"rms_shape_displacement":rms}
def gen(n,r,sid):
 rl,rs,shift,mech=SC[sid]
 u=r.normal(size=n);v=r.normal(size=n);l1=math.sqrt(.5)*u;l2=math.sqrt(.5)*(rl*u+math.sqrt(1-rl*rl)*v)
 u=r.normal(size=(n,4));v=r.normal(size=(n,4));s1=math.sqrt(.5)*u;s2=math.sqrt(.5)*(rs*u+math.sqrt(1-rs*rs)*v)
 ch=np.linalg.cholesky(.5*C);e1=r.normal(size=(n,5))@ch.T;e2=r.normal(size=(n,5))@ch.T
 y1=MU+l1[:,None]+s1@H.T+e1;y2=MU+l2[:,None]+s2@H.T+e2
 if shift=="common":y2+=.5
 elif shift=="shape":y2+=.5*H[:,0]
 if mech=="round":y1=np.rint(y1);y2=np.rint(y2)
 elif mech=="mixture":y1=MU+(y1-MU)*(r.random(y1.shape)<.4);y2=MU+(y2-MU)*(r.random(y2.shape)<.4)
 return y1,y2
def numeric_batch(sid,scale,batch,n,chunk=100000):
 center,s,_=ref_params(sid,scale)
 if np.any(s==0):return None
 r=rng("truth",sid,scale,batch);sum_l1=sum_l2=sum_l1sq=sum_l2sq=sum_cross=sum_delta=sum_ds2=0.;seen=0
 while seen<n:
  m=min(chunk,n-seen);y1,y2=gen(m,r,sid);z1=(y1-center)/s;z2=(y2-center)/s;l1=z1.mean(1);l2=z2.mean(1);d=l2-l1
  q1=z1-l1[:,None];q2=z2-l2[:,None]
  sum_l1+=l1.sum();sum_l2+=l2.sum();sum_l1sq+=l1@l1;sum_l2sq+=l2@l2;sum_cross+=l1@l2;sum_delta+=d.sum();sum_ds2+=np.sum((q2-q1)**2)/5;seen+=m
 ml1=sum_l1/n;ml2=sum_l2/n;v1=sum_l1sq/n-ml1**2;v2=sum_l2sq/n-ml2**2;cv=sum_cross/n-ml1*ml2;dm=sum_delta/n
 return {"level_icc_a1":2*cv/(v1+v2+dm*dm),"mean_level_change":dm,"rms_shape_displacement":math.sqrt(sum_ds2/n)}
def main():
 refs={};rows=[];conv=[]
 for sid in SC:
  for scale in ["MAD","SD"]:
   c,s,meta=ref_params(sid,scale);status="undefined" if np.any(s==0) else "defined"
   refs[f"{sid}|{scale}"]={"center":c.tolist(),"scale":s.tolist(),"status":status,"metadata":meta}
   analytic=moment_truth(sid,scale)
   n=500000 if sid=="S5" else 250000
   batches=[] if status=="undefined" else [numeric_batch(sid,scale,b,n) for b in [0,1]]
   for ep in ["level_icc_a1","mean_level_change","rms_shape_displacement"]:
    if status=="undefined":rows.append({"target_id":f"{sid}_{scale}_{ep}","scenario_id":sid,"scale_method":scale,"endpoint_id":ep,"truth_status":"structurally_undefined","truth_value":"","truth_method":"population MAD is zero","numerical_validation":"not_applicable","numerical_se":"","absolute_discrepancy":"","precision_criterion":"not_applicable","criterion_met":"not_applicable"});continue
    vals=[x[ep] for x in batches];num=sum(vals)/2;se=abs(vals[0]-vals[1])/2
    target=num if sid=="S5" else analytic[ep];method="two independent 500000-pair batches" if sid=="S5" else "analytic moments"
    disc=abs(target-num);crit=.005
    rows.append({"target_id":f"{sid}_{scale}_{ep}","scenario_id":sid,"scale_method":scale,"endpoint_id":ep,"truth_status":"defined","truth_value":format(target,".17g"),"truth_method":method,"numerical_validation":format(num,".17g"),"numerical_se":format(se,".17g"),"absolute_discrepancy":format(disc,".17g"),"precision_criterion":"numerical_se<=0.005 and analytic discrepancy<=max(0.005,4*SE)","criterion_met":"yes" if se<=crit and (sid=="S5" or disc<=max(crit,4*se)) else "no"})
   for b,x in enumerate(batches):
    for ep,v in x.items():conv.append({"scenario_id":sid,"scale_method":scale,"batch_id":b,"pairs":n,"endpoint_id":ep,"estimate":format(v,".17g"),"stream_id":f"truth|{sid}|{scale}|{b}"})
 with (BASE/"truth_reference_parameters.json").open("w",encoding="utf-8",newline="\n") as f:json.dump(refs,f,indent=2);f.write("\n")
 for name,data,fields in [("truth_results.csv",rows,list(rows[0])),("truth_convergence.csv",conv,list(conv[0]))]:
  with (BASE/name).open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(data)
 if any(r["criterion_met"]=="no" for r in rows):raise RuntimeError("truth precision criterion failed")
 print(json.dumps({"status":"PASS","truth_rows":len(rows),"convergence_rows":len(conv)},sort_keys=True))
if __name__=="__main__":main()
