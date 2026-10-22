"""Independent full raw-data validation; imports no production C2 helpers."""
from __future__ import annotations
import csv,hashlib,json,math,sys,time
from collections import defaultdict
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parents[1];BA=ROOT/'chavi_analysis_ds007116_step5ba_clean_rebuild_20261001';PUB=OUT/'results'/'public_aggregate';AUD=OUT/'results'/'participant_linked_audit';VAL=OUT/'validation'
TASKS=('letter_nback','face_memory','matrix_reasoning','emotion_recognition','dominant_finger_tapping');EPS=np.finfo(float).eps;MAD_DEN=.6744897501960817;ENDS=('level_icc_a1','mean_level_change','rms_shape_displacement')
def rows(p):
 with open(p,newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def digest(b):return hashlib.sha256(b).hexdigest()
def rng_weights(rep,n,label):
 seed=int.from_bytes(hashlib.sha256(f'20261003|empirical_v1|{label}|{rep}'.encode()).digest()[:16],'little');rng=np.random.Generator(np.random.PCG64DXSM(seed));return np.bincount(rng.integers(0,n,size=n),minlength=n)
def fit_expanded(y,w):
 x=np.repeat(np.asarray(y,float),np.asarray(w,int));center=float(np.mean(x));med=float(np.median(x));scale=float(np.median(np.abs(x-med))/MAD_DEN)
 if not math.isfinite(scale) or scale<=64*EPS*max(float(np.ptp(x)),abs(scale)):raise ValueError('independent_scale_failure')
 return center,scale
def calc(z,w=None):
 z=np.asarray(z,float);w=np.ones(len(z),int) if w is None else np.asarray(w,int);x=np.repeat(z,w,axis=0);n=len(x);levels=x.mean(2);q=x-levels[:,:,None]
 grand=float(levels.mean());rm=levels.mean(1);cm=levels.mean(0);msr=2*float(np.sum((rm-grand)**2))/(n-1);msc=n*float(np.sum((cm-grand)**2));res=levels-rm[:,None]-cm[None,:]+grand;mse=float(np.sum(res**2))/(n-1);den=msr+mse+2*(msc-mse)/n
 icc=None if max(abs(msr),abs(msc),abs(mse),abs(den))==0 or abs(den)<=64*EPS*max(abs(msr),abs(msc),abs(mse),abs(den)) else (msr-mse)/den
 return {'level_icc_a1':icc,'mean_level_change':float(np.mean(levels[:,1]-levels[:,0])),'rms_shape_displacement':math.sqrt(float(np.sum((q[:,1]-q[:,0])**2)/(5*n)))}
def slice_array(spec,s):
 stem={'primary_vf':'primary_vf','fixed_primary_pair_strict_v':'fixed_primary_pair_strict_v','vonly_reselected':'vonly_reselected'}[s['stratum']];rr=[r for r in rows(BA/(stem+'_transformed_long.csv')) if r['model']==s['model'] and r['scale_method']==s['scale']];m={(r['participant_id'],r['session_id'],r['task_key']):r for r in rr};ids=sorted({r['participant_id'] for r in rr})
 if s['pair_set']=='M1_supported_primary':
  m1=[r for r in rows(BA/'primary_vf_transformed_long.csv') if r['model']=='M1' and r['scale_method']=='MAD'];d=defaultdict(list)
  for r in m1:d[r['participant_id']].append(r)
  ids=sorted(i for i,v in d.items() if len(v)==10 and all(x['supported']=='yes' and x['coordinate']!='' for x in v))
 z=np.empty((len(ids),2,5));kind='primary' if s['pair_set']=='M1_supported_primary' else s['pair_set']
 for i,p in enumerate(ids):
  for v,ses in enumerate(spec['ordered_occasion_keys'][p][kind]):
   for j,t in enumerate(TASKS):z[i,v,j]=float(m[(p,ses,t)]['coordinate'])
 return ids,z
def main():
 t0=time.perf_counter();spec=json.loads((OUT/'c2_execution_specification.json').read_text());tids=spec['canonical_identity_order']['targets'];aids=spec['canonical_identity_order']['auxiliaries'];fold={k:int(v) for k,v in spec['fold_map'].items()}
 prod_points=rows(PUB/'endpoint_estimates.csv');point_cmp=[];slice_cache={}
 for s in spec['analysis_slices']:
  ids,z=slice_array(spec,s);slice_cache[s['id']]=(ids,z);vals=calc(z)
  for e,v in vals.items():
   p=next(r for r in prod_points if r['analysis_id']==s['id'] and r['estimand_id']==e);pv=float(p['estimate']);diff=abs(v-pv);point_cmp.append({'analysis_id':s['id'],'endpoint':e,'production':pv,'independent':v,'abs_diff':diff,'status':'PASS' if math.isclose(v,pv,abs_tol=1e-12,rel_tol=1e-10) else 'FAIL'})
 # Reference raw arrays.
 ref=rows(BA/'reference_cohort_manifest.csv');allids=tids+aids;ix={x:i for i,x in enumerate(allids)};ti={t:i for i,t in enumerate(TASKS)};R=np.empty((109,5))
 for r in ref:R[ix[r['participant_id']],ti[r['task_key']]]=float(r['parsed_score'])
 TR=R[:52];AR=R[52:];src=rows(BA/'primary_vf_source_rows.csv');sm={(r['participant_id'],r['session_id'],r['task_key']):float(r['parsed_score']) for r in src};raw=np.empty((52,2,5))
 for i,p in enumerate(tids):
  for v,ses in enumerate(spec['ordered_occasion_keys'][p]['primary']):
   for j,t in enumerate(TASKS):raw[i,v,j]=sm[(p,ses,t)]
 # Unit fits and coordinate check independently by explicit expansion.
 fitprod=rows(VAL/'unit_weight_reference_fit_comparison.csv');fitcmp=[];indcoord=np.empty_like(raw)
 for f in range(5):
  held=np.array([fold[p]==f for p in tids]);y=np.vstack([TR[~held],AR]);w=np.ones(len(y),int)
  for j,t in enumerate(TASKS):
   ce,sc=fit_expanded(y[:,j],w);p=next(r for r in fitprod if int(r['target_fold'])==f and r['task_key']==t);diff=max(abs(ce-float(p['center'])),abs(sc-float(p['scale'])));fitcmp.append({'fold':f,'task':t,'max_abs_diff':diff,'status':'PASS' if diff<=1e-12+1e-10*max(abs(ce),abs(sc)) else 'FAIL'});who=[i for i,x in enumerate(tids) if fold[x]==f];indcoord[who,:,j]=(raw[who,:,j]-ce)/sc
 assert np.allclose(indcoord,slice_cache['A_primary_M0_MAD_52'][1],atol=1e-12,rtol=1e-10)
 # Correlation summary separate formulas.
 cors=[]
 for pair in indcoord:
  q=[a-a.mean() for a in pair];thr=[64*EPS*max(np.linalg.norm(pair[k]),math.sqrt(5)*abs(pair[k].mean()),np.finfo(float).tiny) for k in range(2)]
  if all(np.linalg.norm(q[k])>thr[k] for k in range(2)):cors.append(float(np.dot(q[0],q[1])/(np.linalg.norm(q[0])*np.linalg.norm(q[1]))))
 prodcorr=rows(PUB/'profile_correlation_summary.csv')[0];cs={'defined_n':len(cors),'undefined_n':52-len(cors),'minimum':min(cors),'q25':float(np.quantile(cors,.25,method='linear')),'median':float(np.quantile(cors,.5,method='linear')),'q75':float(np.quantile(cors,.75,method='linear')),'maximum':max(cors)}
 corrcmp=[{'field':k,'production':prodcorr[k],'independent':v,'status':'PASS' if (int(prodcorr[k])==v if k.endswith('_n') else math.isclose(float(prodcorr[k]),v,abs_tol=1e-12,rel_tol=1e-10)) else 'FAIL'} for k,v in cs.items()]
 # All draws and endpoint values.
 prodrec={(r['method'],int(r['replicate_id']),r['endpoint']):r for r in rows(AUD/'bootstrap_replicate_endpoints.csv')};prov={int(r['replicate_id']):r for r in rows(AUD/'bootstrap_draw_provenance.csv')};rep_cmp=[];indvals={(m,e):[] for m in ('P2_fixed_transform','P3_joint_unstratified') for e in ENDS};linkage_fail=0
 for rep in range(999):
  tw=rng_weights(rep,52,'shared_target');aw=rng_weights(rep,57,'p3_auxiliary');pr=prov[rep]
  if pr['target_multiplicities']!=';'.join(map(str,tw.tolist())) or pr['auxiliary_multiplicities']!=';'.join(map(str,aw.tolist())) or int(tw.sum())!=52 or int(aw.sum())!=57:linkage_fail+=1
  represented=sorted({fold[tids[i]] for i in range(52) if tw[i]>0});z3=np.full_like(raw,np.nan)
  for f in represented:
   ft=np.array([0 if fold[p]==f else tw[i] for i,p in enumerate(tids)]);y=np.vstack([TR,AR]);w=np.r_[ft,aw];who=[i for i,p in enumerate(tids) if fold[p]==f]
   if any(ft[i]!=0 for i,p in enumerate(tids) if fold[p]==f):linkage_fail+=1
   for j in range(5):ce,sc=fit_expanded(y[:,j],w);z3[who,:,j]=(raw[who,:,j]-ce)/sc
  for method,vals in [('P2_fixed_transform',calc(indcoord,tw)),('P3_joint_unstratified',calc(z3,tw))]:
   for e,v in vals.items():
    p=prodrec[(method,rep,e)];pv=float(p['estimate']);passed=p['status']=='valid' and math.isclose(v,pv,abs_tol=1e-12,rel_tol=1e-10);rep_cmp.append({'method':method,'replicate_id':rep,'endpoint':e,'abs_diff':abs(v-pv),'status':'PASS' if passed else 'FAIL'});indvals[(method,e)].append(v)
 # Independently derive all intervals.
 prodint=rows(PUB/'primary_bootstrap_intervals.csv');intcmp=[];primary=calc(indcoord)
 for method in ('P2_fixed_transform','P3_joint_unstratified'):
  for e in ENDS:
   a=np.array(indvals[(method,e)]);qlo,qhi=np.quantile(a,[.025,.975],method='linear')
   for fam in ('percentile','basic'):
    lo,hi=(qlo,qhi) if fam=='percentile' else (2*primary[e]-qhi,2*primary[e]-qlo);p=next(r for r in prodint if r['method']==method and r['endpoint']==e and r['interval_family']==fam);passed=p['available']=='yes' and int(p['attempted'])==999 and int(p['valid'])==999 and int(p['invalid'])==0 and math.isclose(lo,float(p['lower']),abs_tol=1e-12,rel_tol=1e-10) and math.isclose(hi,float(p['upper']),abs_tol=1e-12,rel_tol=1e-10)
    intcmp.append({'method':method,'endpoint':e,'family':fam,'independent_lower':lo,'independent_upper':hi,'status':'PASS' if passed else 'FAIL'})
 # Write detailed comparisons.
 def write(name,data):
  with open(VAL/name,'w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
 write('independent_point_comparison.csv',point_cmp);write('independent_unit_fit_comparison.csv',fitcmp);write('independent_correlation_comparison.csv',corrcmp);write('independent_full_replicate_comparison.csv',rep_cmp);write('independent_interval_comparison.csv',intcmp)
 failures=sum(r['status']!='PASS' for group in (point_cmp,fitcmp,corrcmp,rep_cmp,intcmp) for r in group)+linkage_fail
 result={'status':'PASS' if failures==0 else 'FAIL','failures':failures,'point_values_compared':len(point_cmp),'unit_fits_compared':len(fitcmp),'correlation_fields_compared':len(corrcmp),'replicate_endpoint_values_compared':len(rep_cmp),'interval_rows_compared':len(intcmp),'draw_linkage_records_checked':999,'linkage_failures':linkage_fail,'elapsed_seconds':time.perf_counter()-t0,'imports_production_helpers':False}
 (VAL/'independent_validation_results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps(result,sort_keys=True));return 0 if failures==0 else 1
if __name__=='__main__':raise SystemExit(main())
