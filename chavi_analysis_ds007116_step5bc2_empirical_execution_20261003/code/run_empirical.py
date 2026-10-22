"""Authorized CHAVI Step 5B-C2 empirical runner."""
from __future__ import annotations
import csv, hashlib, json, math, os, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import c2_analysis as c
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parents[1];RESULTS=OUT/'results';PUB=RESULTS/'public_aggregate';AUD=RESULTS/'participant_linked_audit';VAL=OUT/'validation';LOG=OUT/'logs';BA=ROOT/'chavi_analysis_ds007116_step5ba_clean_rebuild_20261001'
SPEC_PATH=OUT/'c2_execution_specification.json'
def atomic_json(path,obj):
 path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8');os.replace(tmp,path)
def metadata(spec,attempts):
 return {'spec_sha256':c.sha_file(SPEC_PATH),'c1_sha256':spec['adopted_c1_contract_sha256'],'implementation_sha256':c.sha_file(Path(__file__).with_name('c2_analysis.py')),
  'primary_coordinates_sha256':c.sha_file(BA/'primary_vf_transformed_long.csv'),'reference_sha256':c.sha_file(BA/'reference_cohort_manifest.csv'),
  'target_order_sha256':c.sha_bytes('\n'.join(spec['canonical_identity_order']['targets']).encode()),'aux_order_sha256':c.sha_bytes('\n'.join(spec['canonical_identity_order']['auxiliaries']).encode()),
  'attempts':attempts,'namespace':'empirical_v1','master_seed':20261003,'methods':['P2_fixed_transform','P3_joint_unstratified']}
def run_bootstrap(adapter,fixed_z,attempts,checkpoint,max_new=None):
 meta=metadata(adapter.spec,attempts);records=[];provenance=[];start_rep=0
 checkpoint=Path(checkpoint);candidates=([checkpoint] if checkpoint.exists() else [])+list(checkpoint.parent.glob(checkpoint.stem+'.[0-9][0-9][0-9][0-9]'+checkpoint.suffix))
 if candidates:
  parsed=[]
  for candidate in candidates:
   obj=json.loads(candidate.read_text(encoding='utf-8'));parsed.append((obj.get('completed',-1),candidate,obj))
  _,chosen,old=max(parsed,key=lambda x:x[0])
  if old.get('metadata')!=meta:raise c.ValidationError('checkpoint_provenance_mismatch')
  records=old['records'];provenance=old['provenance'];start_rep=old['completed']
  if len(provenance)!=start_rep or len(records)!=start_rep*6:raise c.ValidationError('checkpoint_incomplete')
 limit=attempts if max_new is None else min(attempts,start_rep+max_new);raw=adapter.primary_raw_pairs();t0=time.perf_counter()
 for rep in range(start_rep,limit):
  tw,aw=c.draws(rep,52,57);fit_t={};fit_a={};represented=sorted({adapter.fold[adapter.tids[i]] for i in range(52) if tw[i]>0})
  for f in represented:fit_t[f]=np.array([0 if adapter.fold[x]==f else tw[i] for i,x in enumerate(adapter.tids)],dtype=np.int64);fit_a[f]=aw.copy()
  c.validate_plan(adapter.tids,adapter.aids,adapter.fold,tw,aw,fit_t,fit_a,adapter.fold)
  p2=c.endpoints(fixed_z,tw);z3,represented,fit_fail=adapter.p3(raw,tw,aw);p3=c.endpoints(z3,tw)
  for method,vals in [('P2_fixed_transform',p2),('P3_joint_unstratified',p3)]:
   for endpoint,(value,reason) in vals.items():
    if method.startswith('P3') and fit_fail: value=None;reason='reference_fit_failure:'+'|'.join(fit_fail)
    records.append({'method':method,'replicate_id':rep,'endpoint':endpoint,'status':'valid' if value is not None and math.isfinite(value) else 'invalid','reason_code':reason,'estimate':'' if value is None else repr(float(value))})
  provenance.append({'replicate_id':rep,'target_multiplicities':';'.join(map(str,tw.tolist())),'auxiliary_multiplicities':';'.join(map(str,aw.tolist())),
   'target_draw_sha256':c.sha_bytes(tw.tobytes()),'auxiliary_draw_sha256':c.sha_bytes(aw.tobytes()),'represented_folds':';'.join(map(str,represented)),
   'p3_fit_status':'valid' if not fit_fail else 'invalid','p3_fit_reasons':'|'.join(fit_fail)})
  if (rep+1)%50==0 or rep+1==limit:
   destination=checkpoint if not checkpoint.exists() else checkpoint.with_name(checkpoint.stem+f'.{rep+1:04d}'+checkpoint.suffix)
   atomic_json(destination,{'metadata':meta,'completed':rep+1,'records':records,'provenance':provenance})
 elapsed=time.perf_counter()-t0
 return records,provenance,{'start_rep':start_rep,'end_rep':limit,'new_attempts':limit-start_rep,'elapsed_seconds':elapsed,'attempts_per_second':None if limit==start_rep else (limit-start_rep)/elapsed}
def main():
 spec=json.loads(SPEC_PATH.read_text(encoding='utf-8'));assert c.sha_file(ROOT/'chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003'/'empirical_analysis_contract.json')==spec['adopted_c1_contract_sha256']
 adapter=c.Adapter(ROOT,spec)
 slices={};audits=[]
 for s in spec['analysis_slices']:
  ids,z,a=adapter.slice(s['stratum'],s['model'],s['scale'],s['pair_set'],s['expected_n']);slices[s['id']]=(ids,z);audits.extend(dict(x,analysis_id=s['id']) for x in a)
 # Unit-weight primary fit and all-coordinate reconciliation, required before endpoints.
 params,calc=adapter.unit_fits_and_coordinates();frozen=slices['A_primary_M0_MAD_52'][1]
 param_rows=[r for r in c.read_csv(BA/'transformation_parameters.csv') if r['model']=='M0' and r['scale_method']=='MAD']
 pmap={(int(r['target_fold']),r['task_key']):r for r in param_rows};comparisons=[]
 for r in params:
  u=pmap[(r['target_fold'],r['task_key'])];dc=abs(r['center']-float(u['center']));ds=abs(r['scale']-float(u['scale']));passed=np.isclose(r['center'],float(u['center']),atol=1e-12,rtol=1e-10) and np.isclose(r['scale'],float(u['scale']),atol=1e-12,rtol=1e-10)
  comparisons.append(dict(r,upstream_center=u['center'],upstream_scale=u['scale'],center_abs_diff=dc,scale_abs_diff=ds,status='PASS' if passed else 'FAIL'))
 dif=np.abs(calc-frozen);coord_ok=bool(np.allclose(calc,frozen,atol=1e-12,rtol=1e-10));
 c.write_csv(VAL/'unit_weight_reference_fit_comparison.csv',list(comparisons[0]),comparisons)
 c.write_csv(VAL/'primary_coordinate_reconciliation.csv',['coordinates_compared','maximum_absolute_difference','status'],[{'coordinates_compared':520,'maximum_absolute_difference':float(dif.max()),'status':'PASS' if coord_ok else 'FAIL'}])
 if not coord_ok or any(x['status']!='PASS' for x in comparisons):raise SystemExit('pre-execution fit/coordinate reconciliation failed')
 # Empirical point estimates only after prechecks pass.
 point_rows=[]
 for s in spec['analysis_slices']:
  ids,z=slices[s['id']];vals=c.endpoints(z)
  for e,(v,reason) in vals.items():point_rows.append({'analysis_id':s['id'],'analysis_status':s['status'],'estimand_id':e,'estimate':'' if v is None else repr(v),'status':'defined' if v is not None else 'undefined','reason_code':reason,'denominator':len(ids),'model':s['model'],'scale':s['scale'],'stratum':s['stratum'],'participant_identity_sha256':c.sha_bytes('\n'.join(ids).encode()),'c2_spec_sha256':c.sha_file(SPEC_PATH)})
 c.write_csv(PUB/'endpoint_estimates.csv',list(point_rows[0]),point_rows)
 corr=c.corr_summary(frozen);corr.update({'analysis_id':'A_primary_M0_MAD_52','model':'M0','scale':'MAD','denominator':52,'c2_spec_sha256':c.sha_file(SPEC_PATH)})
 c.write_csv(PUB/'profile_correlation_summary.csv',list(corr),[corr])
 c.write_csv(AUD/'analysis_source_linkage.csv',list(audits[0]),audits)
 # Pair/exclusion audit.
 all_primary=set(adapter.tids);m1_ids=set(slices['C_primary_supported_M0_MAD_42'][0]);ex=[]
 for s in spec['analysis_slices']:
  ids=set(slices[s['id']][0]);universe=all_primary if s['stratum']=='primary_vf' else ids
  if s['pair_set']=='M1_supported_primary':universe=all_primary
  for pid in sorted(universe):ex.append({'analysis_id':s['id'],'participant_id':pid,'included':'yes' if pid in ids else 'no','reason_code':'' if pid in ids else 'incomplete_M1_support','occasion_pair':';'.join(spec['ordered_occasion_keys'][pid]['primary' if s['pair_set']=='M1_supported_primary' else s['pair_set']])})
 c.write_csv(AUD/'exclusions_and_pair_identities.csv',list(ex[0]),ex)
 # Bootstrap and checkpoint.
 checkpoint=LOG/'checkpoints'/'primary_bootstrap_checkpoint.json';rec,prov,runtime=run_bootstrap(adapter,frozen,999,checkpoint)
 c.write_csv(AUD/'bootstrap_replicate_endpoints.csv',list(rec[0]),rec);c.write_csv(AUD/'bootstrap_draw_provenance.csv',list(prov[0]),prov)
 runtime.update({'total_attempts_per_method':999,'P2_endpoint_records':2997,'P3_endpoint_records':2997});(LOG/'runtime_evidence.json').write_text(json.dumps(runtime,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 # Intervals.
 primary_points={r['estimand_id']:float(r['estimate']) for r in point_rows if r['analysis_id']=='A_primary_M0_MAD_52' and r['status']=='defined'};intervals=[]
 for method in ('P2_fixed_transform','P3_joint_unstratified'):
  for e in c.ENDPOINTS:
   rr=[r for r in rec if r['method']==method and r['endpoint']==e];vals=np.array([float(r['estimate']) for r in rr if r['status']=='valid']);valid=len(vals);invalid=999-valid;available,why=c.interval_gate(999,valid,invalid,e in primary_points)
   qlo,qhi=(np.quantile(vals,[.025,.975],method='linear') if available else (None,None))
   for family in ('percentile','basic'):
    if available and family=='percentile':lo,hi=float(qlo),float(qhi)
    elif available:lo,hi=float(2*primary_points[e]-qhi),float(2*primary_points[e]-qlo)
    else:lo=hi=None
    intervals.append({'method':method,'endpoint':e,'interval_family':family,'reporting_role':'default' if method.startswith('P3') and family=='percentile' else 'required_comparator' if method.startswith('P2') and family=='percentile' else 'sensitivity','confidence_level':0.95,'point_estimate':primary_points.get(e,''),'lower':'' if lo is None else repr(lo),'upper':'' if hi is None else repr(hi),'attempted':999,'valid':valid,'invalid':invalid,'available':'yes' if available else 'no','unavailable_reason':'' if available else why,'quantile_method':'linear','c2_spec_sha256':c.sha_file(SPEC_PATH)})
 c.write_csv(PUB/'primary_bootstrap_intervals.csv',list(intervals[0]),intervals)
 # Summarize statuses.
 status=[]
 for method in ('P2_fixed_transform','P3_joint_unstratified'):
  for e in c.ENDPOINTS:
   rr=[r for r in rec if r['method']==method and r['endpoint']==e];counts={x:sum(r['reason_code']==x for r in rr) for x in sorted({r['reason_code'] for r in rr})}
   status.append({'method':method,'endpoint':e,'attempted':999,'valid':sum(r['status']=='valid' for r in rr),'invalid':sum(r['status']=='invalid' for r in rr),'reason_counts_json':json.dumps(counts,sort_keys=True)})
 c.write_csv(PUB/'bootstrap_status_summary.csv',list(status[0]),status)
 summary={'status':'EXECUTION_COMPLETE_PENDING_INDEPENDENT_VALIDATION','point_rows':len(point_rows),'interval_rows':len(intervals),'replicate_endpoint_rows':len(rec),'draw_rows':len(prov),'coordinate_reconciliation':'PASS','runtime':runtime}
 (RESULTS/'execution_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps(summary,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
