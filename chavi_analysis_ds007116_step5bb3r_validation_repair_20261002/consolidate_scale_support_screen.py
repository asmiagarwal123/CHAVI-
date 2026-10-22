from pathlib import Path
import json
BASE=Path(__file__).resolve().parent;root=BASE/'scale_support_screen';expected=[f'corrected_pilot__S{i}.json' for i in range(1,7)]+['confirmatory__S1.json','confirmatory__S5.json'];rows=[];missing=[]
for n in expected:
 p=root/n
 if not p.exists():missing.append(n)
 else:rows.append(json.loads(p.read_text()))
result={'status':'PASS' if not missing and all(r['old_supported_new_rejected']==0 for r in rows) else 'FAIL','expected_stage_scenarios':len(expected),'completed_stage_scenarios':len(rows),'missing':missing,'method_scale_draws_screened':sum(r['method_scale_draws_screened'] for r in rows),'old_supported_new_rejected':sum(r['old_supported_new_rejected'] for r in rows),'minimum_supported_sd_scale_to_tolerance_ratio':min((r['minimum_supported_sd_scale_to_tolerance_ratio'] for r in rows),default=None),'screen_method':'corrected pilot: exact every-draw weighted rank/count screen; confirmatory: stronger dataset-level lower bound over every possible nonnegative integer weighting','candidate_keys':[x for r in rows for x in r['candidate_keys']]}
(BASE/'scale_support_screen_summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));raise SystemExit(result['status']!='PASS')
