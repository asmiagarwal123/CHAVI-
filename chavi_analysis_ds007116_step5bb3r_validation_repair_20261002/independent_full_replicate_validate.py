"""Independent scalar/explicit-expansion audit; imports no production helper."""
from pathlib import Path
import csv,hashlib,json,math,platform,sys
import numpy as np
BASE=Path(__file__).resolve().parent;B3=BASE.parent/'chavi_analysis_ds007116_step5bb3_confirmatory_simulation_20261002'
MU=np.array([10.,12.,14.,16.,18.]);MADK=.6744897501960817;EPS=np.finfo(float).eps;FOLDS=np.array([0]*11+[1]*11+[2]*10+[3]*10+[4]*10)
METHODS=('P1_oracle_conditional','P2_fixed_transform','P3_joint_unstratified','P4_joint_fold_stratified');ENDS=('level_icc_a1','mean_level_change','rms_shape_displacement')
H=np.zeros((5,4))
for j in range(4):H[:j+1,j]=1/math.sqrt((j+1)*(j+2));H[j+1,j]=-(j+1)/math.sqrt((j+1)*(j+2))
C=np.fromfunction(lambda i,j:.3**np.abs(i-j),(5,5));CH=np.linalg.cholesky(.5*C)
def keyed(ns,*parts):return np.random.Generator(np.random.PCG64DXSM(int.from_bytes(hashlib.sha256('|'.join(map(str,(20261002,ns)+parts)).encode()).digest()[:16],'little')))
def scores(n,g,rl,rs):
 u=g.normal(size=n);v=g.normal(size=n);l1=math.sqrt(.5)*u;l2=math.sqrt(.5)*(rl*u+math.sqrt(1-rl*rl)*v);u=g.normal(size=(n,4));v=g.normal(size=(n,4));s1=math.sqrt(.5)*u;s2=math.sqrt(.5)*(rs*u+math.sqrt(1-rs*rs)*v);e1=g.normal(size=(n,5))@CH.T;e2=g.normal(size=(n,5))@CH.T;return MU+l1[:,None]+s1@H.T+e1,MU+l2[:,None]+s2@H.T+e2
def generate(sid,o,ns):
 cfg={'S1':(.8,.8,'none','continuous'),'S2':(.8,0.,'none','continuous'),'S3':(.8,.8,'common','continuous'),'S4':(.8,.8,'helmert','continuous'),'S5':(.8,.8,'none','round'),'S6':(.8,.8,'none','mass')}[sid];g=keyed(ns,'outer_dataset',sid,o);y1,y2=scores(52,g,cfg[0],cfg[1]);a,_=scores(57,g,cfg[0],cfg[1])
 if cfg[2]=='common':y2+=.5
 if cfg[2]=='helmert':y2+=.5*H[:,0]
 if cfg[3]=='round':y1=np.rint(y1);y2=np.rint(y2);a=np.rint(a)
 if cfg[3]=='mass':y1=MU+(y1-MU)*(g.random(y1.shape)<.4);y2=MU+(y2-MU)*(g.random(y2.shape)<.4);a=MU+(a-MU)*(g.random(a.shape)<.4)
 return np.stack([y1,y2],1),a
def mult(sid,o,ns):
 rt=keyed(ns,'bootstrap_target_unstratified',sid,o);ra=keyed(ns,'bootstrap_auxiliary',sid,o);rs=keyed(ns,'bootstrap_target_stratified',sid,o);tw=np.zeros((999,52),int);aw=np.zeros((999,57),int);sw=np.zeros((999,52),int)
 for b in range(999):tw[b]=np.bincount(rt.integers(0,52,52),minlength=52);aw[b]=np.bincount(ra.integers(0,57,57),minlength=57)
 for fold in range(5):
  ix=np.flatnonzero(FOLDS==fold)
  for b in range(999):sw[b,ix]=np.bincount(rs.integers(0,len(ix),len(ix)),minlength=len(ix))
 return tw,aw,sw
def wmed(x,w):
 e=np.repeat(np.asarray(x,float),np.asarray(w,int));return float(np.median(e)) if len(e) else math.nan
def support(x,w,s):
 p=np.asarray(x)[np.asarray(w)>0]
 if not math.isfinite(s) or s<=0 or len(p)<2:return False
 span=float(np.max(p)-np.min(p));return s>64*EPS*max(span,abs(s))
def fit(pair,aux,tw,aw,scale,needed):
 fits={};fail=False
 for fold in needed:
  keep=FOLDS!=fold;x=np.vstack([pair[keep,0],aux]);w=np.r_[tw[keep],aw];active=w>0;x=x[active];w=w[active];n=int(w.sum());center=np.sum(w[:,None]*x,axis=0)/n;ss=[]
  for j in range(5):
   s=wmed(np.abs(x[:,j]-wmed(x[:,j],w)),w)/MADK if scale=='MAD' else math.sqrt(float(np.dot(w,(x[:,j]-center[j])**2)/(n-1)));ss.append(s);fail |= not support(x[:,j],w,s)
  fits[fold]=(center,np.array(ss))
 return fits,fail
def transform(pair,fits):
 z=np.full_like(pair,np.nan)
 for fold,(c,s) in fits.items():z[FOLDS==fold]=(pair[FOLDS==fold]-c)/s
 return z
def endpoint(z,w):
 active=w>0;z=z[active];w=w[active];n=int(w.sum())
 if n<2 or not np.all(np.isfinite(z)):return np.full(3,np.nan),2
 level=z.mean(2);q=z-level[:,:,None];delta=level[:,1]-level[:,0];shape=np.sum((q[:,1]-q[:,0])**2,axis=1)/5
 origin=float(np.sum(w[:,None]*level)/(2*n));unit=float(np.max(np.abs(level-origin)));icc=np.nan
 if unit>0 and math.isfinite(unit):
  y=(level-origin)/unit;gm=float(np.sum(w[:,None]*y)/(2*n));rm=y.mean(1);cm=np.sum(w[:,None]*y,0)/n;msr=2*float(np.dot(w,(rm-gm)**2))/(n-1);msc=n*float(np.sum((cm-gm)**2));res=y-rm[:,None]-cm[None,:]+gm;mse=float(np.sum(w[:,None]*res**2))/(n-1);den=msr+mse+2*(msc-mse)/n;rel=max(abs(msr),abs(msc),abs(mse),abs(den));icc=(msr-mse)/den if rel>0 and abs(den)>64*EPS*rel else np.nan
 return np.array([icc,float(np.dot(w,delta)/n),math.sqrt(float(np.dot(w,shape)/n))]),0
def calculate(pair,aux,tw,aw,sw,method,scale,refs):
 vals=np.full((999,3),np.nan);status=np.full((999,3),2,np.int8);ones_t=np.ones(52,int);ones_a=np.ones(57,int)
 fixed,ff=fit(pair,aux,ones_t,ones_a,scale,range(5));ref=refs.get(f'{SID}|{scale}');oracle={f:(np.array(ref['center']),np.array(ref['scale'])) for f in range(5)} if ref and ref.get('status')=='defined' else None
 if method in METHODS[:2]:
  fits=oracle if method==METHODS[0] else fixed;failed=(oracle is None) if method==METHODS[0] else ff;z=transform(pair,fits) if not failed else np.full_like(pair,np.nan)
  for b in range(999):
   vals[b],_=endpoint(z,tw[b]);status[b]=np.where(np.isfinite(vals[b]),0,1 if method==METHODS[1] and failed else 2)
 else:
  W=tw if method==METHODS[2] else sw
  for b in range(999):
   needed=sorted(set(FOLDS[W[b]>0].tolist()));fits,failed=fit(pair,aux,W[b],aw[b],scale,needed)
   if failed:status[b]=1;continue
   vals[b],_=endpoint(transform(pair,fits),W[b]);status[b]=np.where(np.isfinite(vals[b]),0,2)
 return vals,status
def key(stage,sid,o,m,s,tail):return '__'.join(map(str,(stage,sid,o,m.replace('_','-'),s,tail)))
def close(a,b,atol,rtol):return abs(a-b)<=atol+rtol*abs(b)
def main():
 global SID
 spec=json.loads((BASE/'numerical_audit_specification.json').read_text());refs=json.loads((BASE/'truth_reference_parameters.json').read_text());prod=np.load(BASE/'production_numerical_audit_values.npz');precs=json.loads((BASE/'production_numerical_audit_records.json').read_text())['records'];pmap={(r['stage'],r['scenario_id'],r['outer_id'],r['method'],r['scale_method'],r['endpoint']):r for r in precs};rows=[]
 for case in spec['cases']:
  stage=case['stage'];SID=case['scenario_id'];o=case['outer_id'];pair,aux=generate(SID,o,stage);tw,aw,sw=mult(SID,o,stage)
  for scale in ('MAD','SD'):
   for method in case['methods']:
    vals,status=calculate(pair,aux,tw,aw,sw,method,scale,refs);pv=prod[key(stage,SID,o,method,scale,'values')];ps=prod[key(stage,SID,o,method,scale,'status')];vm=np.isfinite(vals)!=np.isfinite(pv);sm=status!=ps;both=np.isfinite(vals)&np.isfinite(pv);err=np.abs(vals[both]-pv[both]);tol=spec['absolute_tolerance']+spec['relative_tolerance']*np.abs(pv[both]);value_bad=int(np.sum(err>tol));maxerr=float(err.max()) if len(err) else 0.
    for ei,e in enumerate(ENDS):
     r=pmap[(stage,SID,o,method,scale,e)];v=vals[:,ei];ok=np.isfinite(v);n=int(ok.sum());qlo=float(np.quantile(v[ok],.025,method='linear')) if n else None;qhi=float(np.quantile(v[ok],.975,method='linear')) if n else None;summary_bad=(n!=r['valid'] or int(np.sum(status[:,ei]==1))!=r['unsupported'] or int(np.sum(status[:,ei]==2))!=r['undefined'] or ((qlo is None)!=(r['q025'] is None)) or (qlo is not None and (not close(qlo,r['q025'],1e-10,1e-10) or not close(qhi,r['q975'],1e-10,1e-10))))
     rows.append({'stage':stage,'scenario_id':SID,'outer_id':o,'method':method,'scale_method':scale,'endpoint':e,'sampling_role':case['sampling_role'],'replicates_compared':999,'validity_mask_mismatches':int(vm[:,ei].sum()),'failure_category_mismatches':int(sm[:,ei].sum()),'finite_value_mismatches':value_bad if ei==0 else '', 'max_abs_error_all_endpoints':maxerr if ei==0 else '','summary_mismatch':summary_bad,'status':'PASS' if not vm[:,ei].any() and not sm[:,ei].any() and value_bad==0 and not summary_bad else 'FAIL'})
  print(json.dumps({'stage':stage,'scenario':SID,'outer':o}),flush=True)
 # Independent identity verification against every original ledger row.
 hashes=[]
 for stage in ('corrected_pilot','confirmatory'):
  with (B3/f'{stage}_outer_dataset_run_ledger.csv').open() as f:
   for r in csv.DictReader(f):
    pair,aux=generate(r['scenario_id'],int(r['outer_id']),stage);h=hashlib.sha256(pair.astype('<f8').tobytes()+aux.astype('<f8').tobytes()).hexdigest();hashes.append(h==r['dataset_sha256'])
 with (BASE/'independent_full_replicate_comparisons.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
 result={'status':'PASS' if all(r['status']=='PASS' for r in rows) and all(hashes) else 'FAIL','calculation_path':'scalar explicit-frequency expansion; no production helper imports','audit_summary_rows':len(rows),'full_replicate_values_compared':sum(r['replicates_compared'] for r in rows),'audit_failures':sum(r['status']!='PASS' for r in rows),'dataset_identity_records':len(hashes),'dataset_hash_mismatches':sum(not x for x in hashes),'python':sys.version,'numpy':np.__version__,'platform':platform.platform(),'specification_sha256':hashlib.sha256((BASE/'numerical_audit_specification.json').read_bytes()).hexdigest()}
 (BASE/'independent_numerical_validation_results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
