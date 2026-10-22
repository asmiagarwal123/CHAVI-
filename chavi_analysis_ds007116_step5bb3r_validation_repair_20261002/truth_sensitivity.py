"""Frozen-truth verification and conservative +/-4SE S5 coverage sensitivity."""
from pathlib import Path
import csv,hashlib,json,math
BASE=Path(__file__).resolve().parent;B2=BASE.parent/'chavi_analysis_ds007116_step5bb2_simulation_pilot_20261002';B3=BASE.parent/'chavi_analysis_ds007116_step5bb3_confirmatory_simulation_20261002'
def read(p):
 with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
truth=read(BASE/'truth_results.csv');tm={(r['scenario_id'],r['scale_method'],r['endpoint_id']):r for r in truth};exact=[r for r in truth if r['scenario_id']=='S5' and r['endpoint_id']=='mean_level_change'];assert len(exact)==2 and all(float(r['truth_value'])==0 for r in exact)
ints=read(BASE/'confirmatory_interval_results_repaired.csv');out=[]
for scale in ('MAD','SD'):
 for endpoint in ('level_icc_a1','mean_level_change','rms_shape_displacement'):
  tr=tm[('S5',scale,endpoint)];theta=float(tr['truth_value']);se=float(tr['numerical_se']) if tr['numerical_se'] else 0.;radius=0. if endpoint=='mean_level_change' else 4*se
  for method in ('P1_oracle_conditional','P2_fixed_transform','P3_joint_unstratified','P4_joint_fold_stratified'):
   for fam in ('percentile','basic'):
    rr=[r for r in ints if r['scenario_id']=='S5' and r['scale_method']==scale and r['endpoint']==endpoint and r['method']==method and r['interval_family']==fam and r['available']=='True'];rates=[]
    for t in (theta-radius,theta,theta+radius):rates.append(sum(float(r['lower'])<=t<=float(r['upper']) for r in rr)/len(rr) if rr else math.nan)
    out.append({'scenario_id':'S5','scale_method':scale,'endpoint':endpoint,'method':method,'interval_family':fam,'available_intervals':len(rr),'frozen_truth':theta,'numerical_se':se,'sensitivity_radius_4se':radius,'coverage_truth_minus_4se':rates[0],'coverage_frozen_truth':rates[1],'coverage_truth_plus_4se':rates[2],'minimum_sensitivity_coverage':min(rates),'maximum_sensitivity_coverage':max(rates)})
with (BASE/'truth_sensitivity.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]),lineterminator='\n');w.writeheader();w.writerows(out)
conv=BASE/'truth_convergence_restored_from_b2.csv';repro=json.loads((BASE/'truth_reproduction_results.json').read_text()) if (BASE/'truth_reproduction_results.json').exists() else {};result={'status':'PASS','frozen_truth_unchanged_from_b3':hashlib.sha256((BASE/'truth_results.csv').read_bytes()).hexdigest()==hashlib.sha256((B3/'truth_results.csv').read_bytes()).hexdigest(),'s5_exact_zero_rows':len(exact),'s5_exact_zero_verified':True,'isolated_truth_engine_plus_exact_zero_correction_reproduced':repro.get('status')=='PASS','truth_reproduction_evidence':'truth_reproduction_results.json','convergence_dependency_resolution':'restored byte-for-byte from inherited B2 artifact and independently regenerated in an isolated process; frozen truth was not overwritten','restored_convergence_sha256':hashlib.sha256(conv.read_bytes()).hexdigest(),'b2_source_sha256':hashlib.sha256((B2/'truth_convergence.csv').read_bytes()).hexdigest(),'sensitivity_rule':'frozen truth +/- 4 documented numerical SE; exact-zero mean change uses radius 0','sensitivity_rows':len(out),'truth_regeneration_commands':['..\\.venv\\Scripts\\python.exe truth_engine.py','..\\.venv\\Scripts\\python.exe repair_truth.py']}
if not result['frozen_truth_unchanged_from_b3'] or not result['isolated_truth_engine_plus_exact_zero_correction_reproduced'] or result['restored_convergence_sha256']!=result['b2_source_sha256']:result['status']='FAIL'
(BASE/'truth_convergence_and_sensitivity_evidence.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
