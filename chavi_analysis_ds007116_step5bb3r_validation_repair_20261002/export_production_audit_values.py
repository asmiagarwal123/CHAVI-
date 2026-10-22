"""Export every production value for the pre-frozen numerical audit set."""
from pathlib import Path
import hashlib,json,math,sys
import numpy as np
BASE=Path(__file__).resolve().parent;sys.path.insert(0,str(BASE))
import simulation_core as sc
import run_stage as rs

def safe(s):return s.replace('_','-')
def main():
 spec=json.loads((BASE/'numerical_audit_specification.json').read_text());refs=json.loads((BASE/'truth_reference_parameters.json').read_text());truth=rs.truth_table(); arrays={}; records=[]
 for case in spec['cases']:
  stage=case['stage'];sid=case['scenario_id'];outer=case['outer_id'];sc.STREAM_NAMESPACE=stage;rs.STREAM_NAMESPACE=stage;rs.assert_stage_namespace(stage)
  pair,aux=rs.generate_dataset(sid,outer);tw,aw,sw=rs.draw_multiplicities(sid,outer,999); ones_t=np.ones(52,int);ones_a=np.ones(57,int)
  source=json.loads((BASE.parent/'chavi_analysis_ds007116_step5bb3_confirmatory_simulation_20261002'/'runtime'/stage/f'{sid}__{outer:04d}.json').read_text())
  for scale in ('MAD','SD'):
   fixed_z,fits,failure=rs.fit_transform(pair,aux,ones_t,ones_a,scale)
   ref=refs.get(f'{sid}|{scale}');oracle={f:{'center':np.array(ref['center']),'scale':np.array(ref['scale']),'status':'supported'} for f in range(5)} if ref and ref.get('status')=='defined' else None
   for method in case['methods']:
    if method=='P1_oracle_conditional':
      vals=rs.batch_fixed(sc.transform_targets(pair,oracle),tw) if oracle else np.full((999,3),np.nan);bad=np.zeros(999,bool)
    elif method=='P2_fixed_transform':vals=rs.batch_fixed(fixed_z,tw) if not failure else np.full((999,3),np.nan);bad=np.full(999,bool(failure))
    else:
      W=tw if method=='P3_joint_unstratified' else sw;vals,bad=rs.batch_refit(pair,aux,W,aw,scale,method.endswith('stratified') and method.startswith('P4'))
    status=np.where(np.isfinite(vals),0,np.where(bad[:,None],1,2)).astype(np.int8)
    tag='__'.join(map(str,(stage,sid,outer,safe(method),scale)));arrays[tag+'__values']=vals;arrays[tag+'__status']=status
    for ei,endpoint in enumerate(rs.ENDS):
      v=vals[:,ei];ok=np.isfinite(v);n=int(ok.sum());p=next(r['estimate'] for r in source['point'] if r['method']==method and r['scale_method']==scale and r['endpoint']==endpoint);theta=truth[(sid,scale,endpoint)];eligible=n>=950 and math.floor(.025*n)>=20 and p is not None and math.isfinite(theta);qlo=float(np.quantile(v[ok],.025,method='linear')) if n else None;qhi=float(np.quantile(v[ok],.975,method='linear')) if n else None
      records.append({'stage':stage,'scenario_id':sid,'outer_id':outer,'method':method,'scale_method':scale,'endpoint':endpoint,'sampling_role':case['sampling_role'],'dataset_sha256':rs.hash_pair(pair,aux),'valid':n,'unsupported':int(np.sum(status[:,ei]==1)),'undefined':int(np.sum(status[:,ei]==2)),'q025':qlo,'q975':qhi,'n_gate':n>=950,'tail_gate':math.floor(.025*n)>=20,'point_gate':p is not None,'truth_gate':math.isfinite(theta),'available':eligible,'percentile_lower':qlo if eligible else None,'percentile_upper':qhi if eligible else None,'basic_lower':2*p-qhi if eligible else None,'basic_upper':2*p-qlo if eligible else None,'percentile_covered':bool(qlo<=theta<=qhi) if eligible else None,'basic_covered':bool(2*p-qhi<=theta<=2*p-qlo) if eligible else None})
  print(json.dumps({'stage':stage,'scenario':sid,'outer':outer,'methods':len(case['methods'])}),flush=True)
 np.savez_compressed(BASE/'production_numerical_audit_values.npz',**arrays)
 (BASE/'production_numerical_audit_records.json').write_text(json.dumps({'specification_sha256':hashlib.sha256((BASE/'numerical_audit_specification.json').read_bytes()).hexdigest(),'records':records},indent=2)+'\n')
 print(json.dumps({'status':'PASS','records':len(records),'array_pairs':len(arrays)//2}))
if __name__=='__main__':main()
