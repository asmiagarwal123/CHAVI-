"""B3R readiness aggregator. Completion is a conjunction, never a row-count shortcut."""
from pathlib import Path
import json
BASE=Path(__file__).resolve().parent
REQUIRED={
 'defects_reproduced':('defect_reproduction.json','all_reproduced'),
 'corruption_tests':('independent_corruption_checks.json','status'),
 'edge_tests':('edge_case_test_results.json','status'),
 'affected_recalculation':('recalculation_status.json','status'),
 'checkpoint_validation':('checkpoint_validation_results.json','status'),
 'independent_full_replicates_both_stages':('independent_numerical_validation_results.json','status'),
 'independent_all_tables_both_stages':('independent_table_validation_results.json','status'),
 'truth':('truth_convergence_and_sensitivity_evidence.json','status'),
 'reproduction_resume':('runtime_resume_evidence.json','status'),
 'scale_support_full_stream':('scale_support_screen_summary.json','status'),
 'protected_inputs':('protected_input_rehash_results.json','status'),
 'package_verification':('package_verification.json','status')}
def main():
 gates={}
 for name,(fn,key) in REQUIRED.items():
  p=BASE/fn
  if not p.exists():gates[name]={'status':'NOT RUN','evidence':fn};continue
  value=json.loads(p.read_text()).get(key);ok=value is True if key=='all_reproduced' else value=='PASS';gates[name]={'status':'PASS' if ok else 'FAIL','evidence':fn,'observed':value}
 ready=all(x['status']=='PASS' for x in gates.values());out={'status':'PASS' if ready else 'BLOCKED','ready_for_separate_empirical_protocol_review':ready,'gates':gates,'authorization':'simulation evidence only; does not authorize empirical inference'}
 (BASE/'readiness_verdict.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));raise SystemExit(0 if ready else 1)
if __name__=='__main__':main()
