from pathlib import Path
import json
BASE=Path(__file__).resolve().parent
sources=['defect_reproduction.json','independent_corruption_checks.json','edge_case_test_results.json','impact_screen_results.json','recalculation_status.json','checkpoint_validation_results.json','independent_numerical_validation_results.json','independent_table_validation_results.json','scale_support_screen_summary.json','truth_convergence_and_sensitivity_evidence.json','truth_reproduction_results.json','runtime_resume_evidence.json']
checks=[]
for n in sources:
 p=BASE/n
 if not p.exists():checks.append({'evidence':n,'status':'NOT RUN'});continue
 x=json.loads(p.read_text());v=x.get('status',x.get('all_reproduced'));ok=(v=='PASS' or v is True or (n=='impact_screen_results.json' and x.get('unique_draws')==257));checks.append({'evidence':n,'status':'PASS' if ok else 'FAIL'})
out={'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':checks};(BASE/'test_results.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));raise SystemExit(out['status']!='PASS')
