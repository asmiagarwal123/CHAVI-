from pathlib import Path
import csv
BASE=Path(__file__).resolve().parent
for suffix,out in [('bootstrap_status_and_failure_reason_counts.csv','bootstrap_status_and_failure_reason_counts.csv'),('interval_results_both_families.csv','interval_results_both_families.csv'),('performance_summary_both_families.csv','performance_summary_both_families.csv'),('paired_outer_method_comparisons.csv','paired_outer_method_comparisons.csv')]:
 rows=[]
 for stage in ('corrected_pilot','confirmatory'):
  p=BASE/f'{stage}_{suffix}'
  with p.open(encoding='utf-8',newline='') as f: rows.extend(csv.DictReader(f))
 if rows:
  with (BASE/out).open('w',encoding='utf-8',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
