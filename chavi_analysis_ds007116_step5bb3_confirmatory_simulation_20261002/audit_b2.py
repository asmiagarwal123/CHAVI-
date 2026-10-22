"""Reconcile published B2 outputs independently of B2 finalization code."""
from pathlib import Path
import csv, hashlib, json, zipfile
BASE=Path(__file__).resolve().parent; B2=BASE.parent/'chavi_analysis_ds007116_step5bb2_simulation_pilot_20261002'
def read(name):
    with (B2/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def uniq(rows, keys): return len({tuple(r[k] for k in keys) for r in rows})
def main():
    point=read('point_estimates.csv'); ints=read('interval_results.csv'); truth=read('truth_results.csv'); perf=read('pilot_performance_summary.csv'); paired=read('paired_method_comparisons.csv')
    result={"point_rows":len(point),"point_unique_keys":uniq(point,['scenario_id','outer_id','scale_method','endpoint','method']),"interval_rows":len(ints),"interval_unique_keys":uniq(ints,['scenario_id','outer_id','scale_method','endpoint','method','interval_type']),"truth_rows":len(truth),"truth_unique_keys":uniq(truth,['scenario_id','scale_method','endpoint_id']),"performance_rows":len(perf),"paired_rows":len(paired)}
    result["interval_families"] = sorted({r['interval_type'] for r in ints}); result["performance_interval_families"] = sorted({r.get('interval_type','') for r in perf})
    result["b2_gate_contradiction"]={"B":499,"tail_fraction":0.025,"max_tail_count":12,"required_tail_count":20,"mathematically_possible":False}
    result["interpretation"]="B2 interval coverage is exploratory and not validated under its declared per-tail rule. B2 performance summary contains percentile summaries only; interval_results contains percentile and basic rows."
    z=BASE.parent/'chavi_analysis_ds007116_step5bb2_simulation_pilot_20261002.zip'; result['b2_zip_sha256']=hashlib.sha256(z.read_bytes()).hexdigest()
    with (BASE/'B2_CONTRACT_AND_OUTPUT_RECONCILIATION.md').open('w',encoding='utf-8') as f:
      f.write('# B2 contract and output reconciliation\n\n')
      f.write('B2 declared 499 replicates and required at least 20 valid estimates in each 2.5% nominal tail. Even with 499 valid draws, `floor(0.025*499)=12`, so the eligibility gate is impossible. The implementation applied a total-valid rule and therefore its issued intervals are exploratory, not validated under the declared rule. Historical B2 files are not rewritten.\n\n')
      f.write('Independent key-based reconciliation:\n\n')
      for k,v in result.items():
       if k not in {'interpretation','b2_gate_contradiction'}: f.write(f'- `{k}`: `{v}`\n')
      f.write('\nThe ZIP excludes `runtime_checkpoint` arrays, so point/interval row counts and published statuses can be reconciled from the ZIP; individual bootstrap values and complete failure-reason arrays cannot be audited from the ZIP alone. The B2 README references `independent_validate.py`, which is absent from the ZIP; B3 reproduction instructions point to the actual B3 validator. B2 protected_inputs_before.csv contains 80 rows, whereas its two-row after ledger is not a full preservation check. B3 repeats the same accessible path inventory before and after. Dataset-hash comparisons in B2 do not independently validate all fitted statistics or intervals.\n')
    (BASE/'b2_reconciliation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
