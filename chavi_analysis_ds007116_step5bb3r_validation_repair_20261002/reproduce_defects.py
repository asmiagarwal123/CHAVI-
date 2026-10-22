"""Executable pre-repair reproductions against the copied B3 implementation."""
from pathlib import Path
import ast,csv,json,sys
import numpy as np
BASE=Path(__file__).resolve().parent;sys.path.insert(0,str(BASE))
import run_stage,simulation_core
simulation_core.STREAM_NAMESPACE='corrected_pilot'
rows=[]
src=(BASE/'independent_corruption_checks.py').read_text(encoding='utf-8'); tree=ast.parse(src)
hardcoded="checks=[" in src and "'PASS'" in src and 'assert ' not in src
rows.append({'defect_id':'A','name':'hard-coded corruption PASS rows','reproduced':hardcoded,'detail':'nine literal PASS rows; no assertions or actual validators'})
# Unused-fold fixture: only two fold-0 identities represented, each frequency 26.
pair,aux=run_stage.generate_dataset('S1',0);tw=np.zeros(52,int);tw[0]=tw[1]=26;aw=np.ones(57,int)
batch,bad=run_stage.batch_refit(pair,aux,tw[None,:],aw[None,:],'SD',False)
fits,fail=simulation_core.fit_references(pair[:,0],aux,tw,aw,[0],'SD');z=simulation_core.transform_targets(pair,fits,[0]);scalar,_=simulation_core.endpoints(z,tw); expanded,_=simulation_core.endpoints(np.repeat(z[:2],26,axis=0),np.ones(52,int))
rows.append({'defect_id':'B','name':'zero-weight NaNs contaminate reductions','reproduced':bool(np.isnan(batch[0,1]) and np.isnan(batch[0,2]) and np.isfinite(expanded['mean_level_change']) and np.isfinite(expanded['rms_shape_displacement'])),'detail':f"batch={batch[0].tolist()}; scalar={[scalar[k] for k in run_stage.ENDS]}; expanded={[expanded[k] for k in run_stage.ENDS]}"})
# Near-zero MAD scale: scalar rule rejects while optimized path only checks >0/finite.
p=np.zeros((52,2,5));p[:2,0]=[0,1e-20,2e-20,3e-20,4e-20];p[:2,1]=p[:2,0]+1e-20;a=np.zeros((57,5));a[:4]=np.array([0,1e-20,2e-20,1])[:,None];t=np.zeros(52,int);t[:2]=26;w=np.zeros(57,int);w[:4]=1
sfits,sfail=simulation_core.fit_references(p[:,0],a,t,w,[0],'MAD');bval,bbad=run_stage.batch_refit(p,a,t[None],w[None],'MAD',False)
rows.append({'defect_id':'C','name':'optimized scale eligibility differs from scalar','reproduced':bool(sfail and not bbad[0]),'detail':f"scalar_failures={len(sfail)}; scalar_status={sfits[0]['status']}; optimized_bad={bool(bbad[0])}"})
iv=(BASE/'independent_validate.py').read_text(encoding='utf-8');mf=(BASE/'make_final_report.py').read_text(encoding='utf-8')
scope={'dataset_hashes':'all 600 corrected and 4000 confirmatory records','point_estimates':'outer IDs 0-4; estimated-reference P2-P4 only','bootstrap_values':'outer IDs 0-1; selected replicate IDs 0,1,2,17,101,498,998 only','not_compared':['all 999 values for any outer','quantiles','eligibility gates','percentile/basic bounds','coverage indicators','complete aggregate arithmetic'],'readiness_defect':'make_final_report checks confirmatory ledger row count plus corrected-pilot independent PASS; it does not require confirmatory independent validation PASS'}
rows.append({'defect_id':'D','name':'validation/readiness scope overstated','reproduced':('n==4000' in mf and "indep.get('status')=='PASS'" in mf),'detail':scope['readiness_defect']})
with (BASE/'defect_reproduction.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
(BASE/'validation_scope_initial.json').write_text(json.dumps(scope,indent=2)+'\n',encoding='utf-8')
(BASE/'defect_reproduction.json').write_text(json.dumps({'all_reproduced':all(r['reproduced'] for r in rows),'rows':rows},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'all_reproduced':all(r['reproduced'] for r in rows),'defects':len(rows)}))
if not all(r['reproduced'] for r in rows): raise SystemExit(1)
