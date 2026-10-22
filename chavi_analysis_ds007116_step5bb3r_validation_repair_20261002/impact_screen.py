"""Reconstruct all original multiplicities and inventory absent-fold repair paths."""
from pathlib import Path
import csv,json,sys
import numpy as np
BASE=Path(__file__).resolve().parent;sys.path.insert(0,str(BASE))
import simulation_core as sc
rows=[];summary=[]
stages={'corrected_pilot':(('S1','S2','S3','S4','S5','S6'),100),'confirmatory':(('S1','S5'),2000)}
for stage,(scenarios,R) in stages.items():
 sc.STREAM_NAMESPACE=stage
 for sid in scenarios:
  draws=0;outers=set()
  for outer in range(R):
   tw,aw,sw=sc.draw_multiplicities(sid,outer,999)
   counts=np.column_stack([tw[:,sc.FOLDS==fold].sum(axis=1) for fold in range(5)]); affected=np.flatnonzero(np.any(counts==0,axis=1))
   draws+=len(affected)
   if len(affected):outers.add(outer)
   for rep in affected:
    missing=';'.join(str(f) for f in range(5) if counts[rep,f]==0)
    for scale in ('MAD','SD'):
     rows.append({'stage':stage,'scenario_id':sid,'outer_id':outer,'method':'P3_joint_unstratified','scale_method':scale,'replicate_id':int(rep),'missing_folds':missing,'potentially_affected':True,'dependency_reason':'unrepresented analysis fold left zero-weight coordinates as NaN in B3 optimized reduction'})
  summary.append({'stage':stage,'scenario_id':sid,'affected_draws':draws,'affected_outer_datasets':len(outers),'attempted_draws':R*999})
with (BASE/'affected_replicate_inventory.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
with (BASE/'affected_replicate_summary.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(summary[0]),lineterminator='\n');w.writeheader();w.writerows(summary)
(BASE/'impact_screen_results.json').write_text(json.dumps({'affected_key_rows':len(rows),'unique_draws':len(rows)//2,'summary':summary,'numpy_version':np.__version__},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'affected_key_rows':len(rows),'unique_draws':len(rows)//2,'summary':summary}))
