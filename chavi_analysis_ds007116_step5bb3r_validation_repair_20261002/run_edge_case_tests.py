"""Executable numerical equivalence and edge-case tests with persisted evidence."""
from pathlib import Path
import csv,json,math,sys,traceback
import numpy as np
BASE=Path(__file__).resolve().parent;sys.path.insert(0,str(BASE))
import simulation_core as sc,run_stage as rs
sc.STREAM_NAMESPACE='corrected_pilot'; records=[]
def record(name,expected,observed,ok,tol='',exc=''):
    records.append({'test':name,'expected':str(expected),'observed':str(observed),'tolerance':str(tol),'exception':exc,'status':'PASS' if ok else 'FAIL'})
def close(a,b,tol=1e-10): return (a is None and b is None) or (a is not None and b is not None and math.isclose(float(a),float(b),rel_tol=tol,abs_tol=tol))
try:
 pair,aux=rs.generate_dataset('S1',0);tw=np.zeros(52,int);tw[:2]=26;aw=np.ones(57,int);bv,bad=rs.batch_refit(pair,aux,tw[None],aw[None],'SD',False);fits,fail=sc.fit_references(pair[:,0],aux,tw,aw,[0],'SD');z=sc.transform_targets(pair,fits,[0]);sv,_=sc.endpoints(z,tw);ev,_=sc.endpoints(np.repeat(z[:2],26,axis=0),np.ones(52,int)); exp=np.array([ev[e] for e in rs.ENDS]);record('absent_fold_all_endpoints',exp,bv[0],np.allclose(exp,bv[0],rtol=1e-10,atol=1e-10,equal_nan=True),1e-10)
except Exception as e:record('absent_fold_all_endpoints','finite defined change endpoints','exception',False,1e-10,repr(e))
try:
 zz=np.full((4,2,5),np.nan);zz[:2]=np.arange(20,dtype=float).reshape(2,2,5);w=np.array([3,2,0,0]);a,_=sc.endpoints(zz,w);b,_=sc.endpoints(np.repeat(zz[:2],w[:2],axis=0),np.ones(5,int));ok=all(close(a[e],b[e]) for e in rs.ENDS);record('zero_weight_nan_masking',[b[e] for e in rs.ENDS],[a[e] for e in rs.ENDS],ok,1e-10)
except Exception as e:record('zero_weight_nan_masking','matches expansion','exception',False,1e-10,repr(e))
try:
 zz=np.zeros((2,2,5));zz[0,0,0]=np.nan;a,reason=sc.endpoints(zz,np.ones(2,int));ok=reason=='unsupported_coordinate' and all(a[e] is None for e in rs.ENDS);record('active_nan_rejected','all None/unsupported_coordinate',(a,reason),ok,'exact')
except Exception as e:record('active_nan_rejected','unsupported','exception',False,'exact',repr(e))
try:
 z=np.arange(30,dtype=float).reshape(3,2,5);w=np.array([101,2,0]);a,_=sc.endpoints(z,w);b,_=sc.endpoints(np.repeat(z[:2],w[:2],axis=0),np.ones(103,int));record('unequal_frequency_expansion',[b[e] for e in rs.ENDS],[a[e] for e in rs.ENDS],all(close(a[e],b[e]) for e in rs.ENDS),1e-10)
except Exception as e:record('unequal_frequency_expansion','matches expansion','exception',False,1e-10,repr(e))
for name,x,w in [('weighted_median_odd',[1.,2.,9.],[1,1,1]),('weighted_median_even',[1.,2.,9.],[1,1,2])]:
 try:
  obs=sc.weighted_median(np.array(x),np.array(w));exp=float(np.median(np.repeat(x,w)));record(name,exp,obs,close(obs,exp),1e-15)
 except Exception as e:record(name,'expanded median','exception',False,1e-15,repr(e))
try:
 ok0,reason0=sc.scale_supported(np.array([1.,1.]),np.ones(2,int),0.0);ok1,reason1=sc.scale_supported(np.array([0.,1e-20,2e-20,1.]),np.ones(4,int),1e-20);record('zero_and_near_zero_scales','both rejected',[(ok0,reason0),(ok1,reason1)],not ok0 and not ok1 and reason1=='numerically_degenerate_scale','exact')
except Exception as e:record('zero_and_near_zero_scales','rejected','exception',False,'exact',repr(e))
try:
 z=np.ones((4,2,5));a,_=sc.endpoints(z,np.ones(4,int));record('constant_profile_icc','ICC undefined, changes zero',[a[e] for e in rs.ENDS],a['level_icc_a1'] is None and close(a['mean_level_change'],0) and close(a['rms_shape_displacement'],0),1e-15)
except Exception as e:record('constant_profile_icc','defined change/undefined ICC','exception',False,1e-15,repr(e))
try:
 x=np.array([[1,4],[2,3],[3,2],[4,1.]],float);v=sc.stable_icc_a1(x,np.ones(4,int));record('negative_icc_retained','<0',v,v<0,'sign')
except Exception as e:record('negative_icc_retained','<0','exception',False,'sign',repr(e))
try:
 x=np.array([[1,1],[2,2],[3,4],[4,5.]],float);w=np.ones(4,int);v=sc.stable_icc_a1(x,w);vals=[sc.stable_icc_a1(x*1e-8,w),sc.stable_icc_a1(x*1e8+1e9,w)];record('representable_affine_icc',[v,v],vals,all(close(v,q,1e-10) for q in vals),1e-10)
except Exception as e:record('representable_affine_icc','invariant','exception',False,1e-10,repr(e))
try:
 pair,aux=rs.generate_dataset('S1',7);tw,aw,sw=rs.draw_multiplicities('S1',7,12);diffs=[]
 for scale in ('MAD','SD'):
  for W,strat in ((tw,False),(sw,True)):
   fast,bad=rs.batch_refit(pair,aux,W,aw,scale,strat)
   for i in range(12):
    needed=sorted(set(sc.FOLDS[W[i]>0].tolist()));fits,fail=sc.fit_references(pair[:,0],aux,W[i],aw[i],needed,scale);vals,_=sc.endpoints(sc.transform_targets(pair,fits,needed),W[i]);slow=np.array([vals[e] if vals[e] is not None else np.nan for e in rs.ENDS]);diffs.append(np.nanmax(np.abs(fast[i]-slow)))
 record('optimized_scalar_mad_sd_all_endpoints','max difference <=1e-10',max(diffs),max(diffs)<=1e-10,1e-10)
except Exception as e:record('optimized_scalar_mad_sd_all_endpoints','equivalent','exception',False,1e-10,repr(e))
try:
 sc.STREAM_NAMESPACE='confirmatory';caught=''
 try:rs.assert_stage_namespace('corrected_pilot')
 except RuntimeError as e:caught=str(e)
 record('stage_namespace_mismatch_fails','RuntimeError containing mismatch',caught,bool(caught) and 'mismatch' in caught,'exact')
finally:sc.STREAM_NAMESPACE='corrected_pilot'
with (BASE/'edge_case_test_records.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator='\n');w.writeheader();w.writerows(records)
out={'status':'PASS' if all(r['status']=='PASS' for r in records) else 'FAIL','tests':len(records),'passed':sum(r['status']=='PASS' for r in records),'records_file':'edge_case_test_records.csv'}
(BASE/'edge_case_test_results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
if out['status']!='PASS': raise SystemExit(1)
