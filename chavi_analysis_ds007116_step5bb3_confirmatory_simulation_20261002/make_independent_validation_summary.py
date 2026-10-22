from pathlib import Path
import json,csv
BASE=Path(__file__).resolve().parent
c=json.loads((BASE/'corrected_pilot_independent_comparison_records.json').read_text())
f=json.loads((BASE/'confirmatory_independent_comparison_records.json').read_text())
cr=json.loads((BASE/'independent_corruption_checks.json').read_text())
inv=list(csv.DictReader((BASE/'protected_inventory_before_after.csv').open(encoding='utf-8')))
out={'status':'PASS' if c['status']=='PASS' and f['status']=='PASS' and cr['status']=='PASS' and all(x['status']=='UNCHANGED' for x in inv) else 'FAIL','corrected':c,'confirmatory':f,'corruption_checks':cr,'protected_inventory':{'rows':len(inv),'changed':sum(x['status']=='CHANGED' for x in inv),'missing':sum(x['status']=='MISSING' for x in inv)},'independent_path':'standalone formulas; no imports from simulation_core.py, run_stage.py, consolidate.py, or B2 finalizers'}
(BASE/'independent_validation_results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
