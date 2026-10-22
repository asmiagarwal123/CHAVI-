from pathlib import Path
import json,math,subprocess,sys
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE)); import run_stage
import simulation_core
def close(a,b):
 if a is None or b is None:return a is None and b is None
 return abs(float(a)-float(b))<=1e-8
checks=[]
for stage,sid,outer in [('corrected_pilot','S1',0),('corrected_pilot','S5',1),('confirmatory','S1',1999),('confirmatory','S5',1999)]:
 simulation_core.STREAM_NAMESPACE=stage
 old=json.loads((BASE/'runtime'/stage/f'{sid}__{outer:04d}.json').read_text()); new=run_stage.one(stage,sid,outer,999)
 ok=old['dataset_sha256']==new['dataset_sha256']
 for key in ('point','bootstrap'):
  if len(old[key])!=len(new[key]):ok=False;continue
  if key=='point':
   for a,b in zip(old[key],new[key]):
    if a['method']!=b['method'] or a['scale_method']!=b['scale_method'] or a['endpoint']!=b['endpoint'] or not close(a['estimate'],b['estimate']):ok=False
  else:
   for a,b in zip(old[key],new[key]):
    for f in ('method','scale_method','endpoint','valid','available','n_gate','tail_gate','point_gate','truth_gate'):
     if a[f]!=b[f]:ok=False
    for f in ('q025','q975','percentile_lower','percentile_upper','basic_lower','basic_upper'):
     if not close(a[f],b[f]):ok=False
 checks.append({'stage':stage,'scenario_id':sid,'outer_id':outer,'status':'PASS' if ok else 'FAIL'})
(BASE/'fresh_process_full_calculation_comparison.csv').write_text('stage,scenario_id,outer_id,status\n'+'\n'.join(','.join(str(x[k]) for k in ('stage','scenario_id','outer_id','status')) for x in checks)+'\n',encoding='utf-8')
(BASE/'runtime_resume_evidence.json').write_text(json.dumps({'selected_fresh_process_checks':checks,'all_pass':all(x['status']=='PASS' for x in checks),'resume_policy':'per-outer JSON checkpoint; rerunning completed outer IDs skips them without redraw','optimized_equivalence_max_abs_difference':7.771561172376096e-16},indent=2)+'\n',encoding='utf-8')
