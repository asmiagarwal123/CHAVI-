"""Consolidate per-outer checkpoint records without importing B2 summarizers."""
from pathlib import Path
import csv,json,math,statistics
BASE=Path(__file__).resolve().parent
METHODS=("P1_oracle_conditional","P2_fixed_transform","P3_joint_unstratified","P4_joint_fold_stratified"); SCALES=("MAD","SD"); ENDS=("level_icc_a1","mean_level_change","rms_shape_displacement"); FAMS=("percentile","basic")
def readtruth():
 d={}
 for r in csv.DictReader((BASE/'truth_results.csv').open(encoding='utf-8')): d[(r['scenario_id'],r['scale_method'],r['endpoint_id'])]=float(r['truth_value']) if r['truth_value'] else math.nan
 return d
def csvout(name,rows):
 if not rows:return
 with (BASE/name).open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def sdse(a):
 a=[float(x) for x in a if math.isfinite(float(x))]; return math.sqrt(statistics.variance(a)/len(a)) if len(a)>1 else math.nan
def main(stage):
 d=BASE/'runtime'/stage; records=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(d.glob('*.json'))]; truth=readtruth(); point=[]; ints=[]; boots=[]; ledger=[]; audit=[]
 contract_hash=__import__('hashlib').sha256((BASE/('corrected_interval_execution_contract.json' if stage=='corrected_pilot' else 'confirmatory_execution_contract.json')).read_bytes()).hexdigest()
 for rec in records:
  ledger.append({'stage':stage,'scenario_id':rec['scenario_id'],'outer_id':rec['outer_id'],'dataset_sha256':rec['dataset_sha256'],'target_n':52,'auxiliary_n':57,'fold_counts':'11;11;10;10;10','status':'completed'})
  for r in rec['point']:
   r=dict(r); r.update(stage=stage,scenario_id=rec['scenario_id'],outer_id=rec['outer_id'],contract_hash=contract_hash); r['truth']=truth.get((rec['scenario_id'],r['scale_method'],r['endpoint']),math.nan); point.append(r)
  for r in rec['bootstrap']:
   r=dict(r); r.update(stage=stage,scenario_id=rec['scenario_id'],outer_id=rec['outer_id'],contract_hash=contract_hash); boots.append(r)
   for fam in FAMS:
    ints.append({'stage':stage,'scenario_id':rec['scenario_id'],'outer_id':rec['outer_id'],'method':r['method'],'scale_method':r['scale_method'],'endpoint':r['endpoint'],'interval_family':fam,'contract_hash':contract_hash,'attempted_bootstrap':r['attempted'],'valid_bootstrap':r['valid'],'invalid_bootstrap':r['invalid'],'n_gate':r['n_gate'],'tail_gate':r['tail_gate'],'point_gate':r['point_gate'],'truth_gate':r['truth_gate'],'available':r['available'],'lower':r[fam+'_lower'],'upper':r[fam+'_upper'],'truth':r['truth'],'covered':(r[fam+'_lower'] is not None and r[fam+'_upper'] is not None and r['truth'] is not None and r[fam+'_lower']<=r['truth']<=r[fam+'_upper']) if r['available'] else None,'lower_miss':(r[fam+'_lower'] is not None and r['truth'] is not None and r['truth']<r[fam+'_lower']) if r['available'] else None,'upper_miss':(r[fam+'_upper'] is not None and r['truth'] is not None and r['truth']>r[fam+'_upper']) if r['available'] else None})
  for r in rec['audit']:
   r=dict(r);r.update(stage=stage,scenario_id=rec['scenario_id'],outer_id=rec['outer_id'],contract_hash=contract_hash);audit.append(r)
 csvout(f'{stage}_point_estimates.csv',point); csvout(f'{stage}_bootstrap_status_and_failure_reason_counts.csv',boots); csvout(f'{stage}_interval_results_both_families.csv',ints); csvout(f'{stage}_outer_dataset_run_ledger.csv',ledger); csvout(f'{stage}_full_bootstrap_audit_subset.csv',audit)
 perf=[]
 for sid in sorted({r['scenario_id'] for r in point}):
  for scale in SCALES:
   for endpoint in ENDS:
    theta=truth.get((sid,scale,endpoint),math.nan)
    for method in METHODS:
     p=[r for r in point if r['scenario_id']==sid and r['scale_method']==scale and r['endpoint']==endpoint and r['method']==method]; pe=[float(r['estimate']) for r in p if r['estimate'] is not None]; errs=[x-theta for x in pe] if math.isfinite(theta) else []
     for fam in FAMS:
      ii=[r for r in ints if r['scenario_id']==sid and r['scale_method']==scale and r['endpoint']==endpoint and r['method']==method and r['interval_family']==fam]; av=[r for r in ii if r['available']]; cov=[int(r['covered']) for r in av if r['covered'] is not None]; widths=[float(r['upper'])-float(r['lower']) for r in av]; covered_all=sum(cov); low=sum(int(r['lower_miss']) for r in av if r['lower_miss'] is not None); up=sum(int(r['upper_miss']) for r in av if r['upper_miss'] is not None); n=len(ii)
      invalid=sum(int(r['invalid_bootstrap']) for r in ii); valid=sum(int(r['valid_bootstrap']) for r in ii)
      perf.append({'stage':stage,'scenario_id':sid,'scale_method':scale,'endpoint':endpoint,'method':method,'interval_family':fam,'contract_hash':contract_hash,'attempted_outer':n,'point_defined':len(pe),'point_undefined':n-len(pe),'point_bias':statistics.mean(errs) if errs else math.nan,'point_sd':statistics.stdev(pe) if len(pe)>1 else math.nan,'point_rmse':math.sqrt(statistics.mean(x*x for x in errs)) if errs else math.nan,'attempted_bootstrap':sum(int(r['attempted_bootstrap']) for r in ii),'valid_bootstrap':valid,'invalid_bootstrap':invalid,'available_intervals':len(av),'unavailable_intervals':n-len(av),'availability_rate':len(av)/n if n else math.nan,'coverage_available':statistics.mean(cov) if cov else math.nan,'available_and_covered_all':covered_all/n if n else math.nan,'lower_misses':low,'upper_misses':up,'mean_width_available':statistics.mean(widths) if widths else math.nan,'median_width_available':statistics.median(widths) if widths else math.nan,'mcse_coverage_available':math.sqrt(statistics.mean(cov)*(1-statistics.mean(cov))/len(cov)) if cov else math.nan,'truth':theta})
 csvout(f'{stage}_performance_summary_both_families.csv',perf)
 # Correct paired outer-level comparisons, not differences of marginal summaries.
 paired=[]
 for sid in sorted({r['scenario_id'] for r in ints}):
  for scale in SCALES:
   for endpoint in ENDS:
    for fam in FAMS:
     def rows(m): return {(r['outer_id']):r for r in ints if r['scenario_id']==sid and r['scale_method']==scale and r['endpoint']==endpoint and r['interval_family']==fam and r['method']==m}
     for ma,mb in [('P2_fixed_transform','P3_joint_unstratified'),('P1_oracle_conditional','P2_fixed_transform'),('P1_oracle_conditional','P3_joint_unstratified'),('P3_joint_unstratified','P4_joint_fold_stratified')]:
      a,b=rows(ma),rows(mb); ids=sorted(set(a)&set(b)); da=[int(a[i]['available'])-int(b[i]['available']) for i in ids]; ac=[(int(a[i]['available'] and a[i]['covered']))-(int(b[i]['available'] and b[i]['covered'])) for i in ids]; both=[i for i in ids if a[i]['available'] and b[i]['available']]; covdiff=[int(a[i]['covered'])-int(b[i]['covered']) for i in both]; wd=[(float(a[i]['upper'])-float(a[i]['lower']))-(float(b[i]['upper'])-float(b[i]['lower'])) for i in both]
      paired.append({'stage':stage,'scenario_id':sid,'scale_method':scale,'endpoint':endpoint,'interval_family':fam,'contract_hash':contract_hash,'method_a':ma,'method_b':mb,'n_outer':len(ids),'availability_diff_mean':statistics.mean(da) if da else math.nan,'availability_diff_mcse':sdse(da),'available_and_covered_diff_mean':statistics.mean(ac) if ac else math.nan,'available_and_covered_diff_mcse':sdse(ac),'both_available_n':len(both),'conditional_coverage_diff_mean':statistics.mean(covdiff) if covdiff else math.nan,'conditional_coverage_diff_mcse':sdse(covdiff),'paired_width_n':len(wd),'paired_width_diff_mean':statistics.mean(wd) if wd else math.nan,'paired_width_diff_mcse':sdse(wd)})
 csvout(f'{stage}_paired_outer_method_comparisons.csv',paired)
 print(json.dumps({'stage':stage,'outer_records':len(records),'point_rows':len(point),'interval_rows':len(ints),'audit_rows':len(audit)}))
if __name__=='__main__':
 import argparse; ap=argparse.ArgumentParser();ap.add_argument('--stage',required=True);main(ap.parse_args().stage)
