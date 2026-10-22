"""Executable valid-control and exact-reason corruption tests."""
from __future__ import annotations
import json,math,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import c2_analysis as c
records=[]
def ok(name,fn):
 fn();records.append({'test':name,'status':'PASS','reason':'valid_control_accepted'})
def reject(name,reason,fn):
 try:fn()
 except c.ValidationError as e:
  assert reason in str(e),(reason,str(e));records.append({'test':name,'status':'PASS','reason':str(e)});return
 raise AssertionError(name+' accepted')
def main():
 tids=['T0','T1','T2'];aids=['A0','A1'];fold={'T0':0,'T1':1,'T2':2};tw=np.array([2,0,1]);aw=np.array([0,2]);fit={f:np.array([0 if fold[x]==f else tw[i] for i,x in enumerate(tids)]) for f in (0,2)};aux={f:aw.copy() for f in (0,2)}
 ok('valid_plan',lambda:c.validate_plan(tids,aids,fold,tw,aw,fit,aux))
 bad={f:v.copy() for f,v in aux.items()};bad[0][0]=-1;bad[0][1]=3;bad[2]=bad[0].copy();reject('negative_auxiliary','negative_multiplicity',lambda:c.validate_plan(tids,aids,fold,tw,bad[0],fit,bad))
 reject('boolean_target','weights_not_integer_nonboolean',lambda:c.validate_plan(tids,aids,fold,np.array([True,True,True]),aw,fit,aux))
 reject('wrong_target_total','incorrect_total',lambda:c.validate_plan(tids,aids,fold,np.array([1,0,1]),aw,fit,aux))
 reject('overlap_roles','role_identities_not_disjoint',lambda:c.validate_plan(tids,['A0','T0'],fold,tw,aw,fit,aux))
 altered=dict(fold);altered['T0']=2;arep=sorted({altered[tids[i]] for i in range(3) if tw[i]>0});afit={f:np.array([0 if altered[x]==f else tw[i] for i,x in enumerate(tids)]) for f in arep};aaux={f:aw.copy() for f in arep}
 reject('altered_external_fold','externally_frozen_fold_map_mismatch',lambda:c.validate_plan(tids,aids,altered,tw,aw,afit,aaux,fold))
 extra=dict(fit);extra[1]=np.array([2,0,1]);extraa=dict(aux);extraa[1]=aw.copy();reject('extra_unused_fold','represented_fold_fit_keys_mismatch',lambda:c.validate_plan(tids,aids,fold,tw,aw,extra,extraa))
 leak={f:v.copy() for f,v in fit.items()};leak[0][0]=1;reject('held_out_leakage','held_out_leakage_or_altered_fold',lambda:c.validate_plan(tids,aids,fold,tw,aw,leak,aux))
 unshared={f:v.copy() for f,v in aux.items()};unshared[2]=np.array([1,1]);reject('unshared_aux','auxiliary_draw_not_shared',lambda:c.validate_plan(tids,aids,fold,tw,aw,fit,unshared))
 ok('support_yes_numeric',lambda:c.validate_support_value('yes','1.25'))
 ok('support_no_null',lambda:c.validate_support_value('no',''))
 reject('unknown_support','unknown_support_label',lambda:c.validate_support_value('MAYBE',''))
 reject('supported_missing','supported_coordinate_missing',lambda:c.validate_support_value('yes',''))
 reject('supported_nonnumeric','supported_coordinate_nonnumeric',lambda:c.validate_support_value('yes','abc'))
 reject('supported_nonfinite','supported_coordinate_nonfinite',lambda:c.validate_support_value('yes','nan'))
 reject('unsupported_present','unsupported_coordinate_not_null',lambda:c.validate_support_value('no','0'))
 assert c.interval_gate(999,999,0,True)==(True,'available');records.append({'test':'valid_interval_gate','status':'PASS','reason':'available'})
 reject('valid_exceeds_attempted','count_accounting_invalid',lambda:c.interval_gate(999,1000,-1,True))
 reject('count_sum','count_accounting_invalid',lambda:c.interval_gate(999,998,0,True))
 reject('noninteger_count','counts_not_integer',lambda:c.interval_gate(999,999.0,0,True))
 const=np.ones((3,2,5));e=c.endpoints(const);assert e['level_icc_a1'][0] is None and e['mean_level_change'][0]==0 and e['rms_shape_displacement'][0]==0
 records.append({'test':'endpoint_specific_degeneracy','status':'PASS','reason':'ICC undefined; other endpoints defined'})
 shifted=np.array([[[0,1,2,3,4],[2,3,4,5,6]],[[4,3,2,1,0],[6,5,4,3,2]]],float);e=c.endpoints(shifted);assert e['rms_shape_displacement'][0]==0 and math.isclose(e['mean_level_change'][0],2)
 records.append({'test':'common_shift','status':'PASS','reason':'known expected endpoints'})
 flat=np.ones((2,2,5));s=c.corr_summary(flat);assert s['defined_n']==0 and s['undefined_n']==2
 records.append({'test':'scale_aware_flat_correlation','status':'PASS','reason':'two undefined'})
 out={'status':'PASS','tests_total':len(records),'tests_passed':len(records),'records':records};p=Path(__file__).resolve().parents[1]/'validation'/'c2_test_results.json';p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:out[k] for k in ('status','tests_total')}));return 0
if __name__=='__main__':raise SystemExit(main())
