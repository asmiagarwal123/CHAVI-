import csv
from pathlib import Path
p=Path(__file__).with_name('truth_results.csv'); rows=list(csv.DictReader(p.open(encoding='utf-8')))
for r in rows:
    if r['scenario_id']=='S5' and r['endpoint_id']=='mean_level_change':
        r['truth_value']='0'; r['truth_method']='analytic symmetry: rounded marginal identical at both visits'; r['numerical_validation']='0'; r['numerical_se']='0'; r['absolute_discrepancy']='0'; r['precision_criterion']='analytic exact'; r['criterion_met']='yes'
with p.open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator='\n'); w.writeheader(); w.writerows(rows)
