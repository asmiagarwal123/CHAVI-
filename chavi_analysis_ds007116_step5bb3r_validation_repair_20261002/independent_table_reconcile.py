"""Independent full-table arithmetic and keyed-denominator reconciliation."""
from pathlib import Path
import ast,csv,json,math,statistics
BASE=Path(__file__).resolve().parent;B3=BASE.parent/'chavi_analysis_ds007116_step5bb3_confirmatory_simulation_20261002'
def read(p):
 with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def b(x):return str(x).lower()=='true'
def num(x):
 try:return float(x)
 except:return math.nan
def eq(a,c,tol=1e-12):
 a=num(a);c=num(c);return (not math.isfinite(a) and not math.isfinite(c)) or (math.isfinite(a) and math.isfinite(c) and abs(a-c)<=tol+tol*abs(c))
def sdse(x):return math.sqrt(statistics.variance(x)/len(x)) if len(x)>1 else math.nan
def stage_check(stage):
 ints=read(BASE/f'{stage}_interval_results_repaired.csv');boots=read(BASE/f'{stage}_bootstrap_status_repaired.csv');points=read(B3/f'{stage}_point_estimates.csv');perf=read(BASE/f'{stage}_performance_summary_repaired.csv');paired=read(BASE/f'{stage}_paired_comparisons_repaired.csv')
 bmap={(r['scenario_id'],r['outer_id'],r['method'],r['scale_method'],r['endpoint']):r for r in boots};pmap={(r['scenario_id'],r['outer_id'],r['method'],r['scale_method'],r['endpoint']):r for r in points};row_errors=[];seen=set()
 for r in ints:
  k=(r['scenario_id'],r['outer_id'],r['method'],r['scale_method'],r['endpoint']);seen.add(k+(r['interval_family'],));br=bmap[k];pr=pmap[k];valid=int(br['valid']);attempted=int(br['attempted']);fam=r['interval_family'];lo=br[fam+'_lower'];hi=br[fam+'_upper'];available=(valid>=950 and math.floor(.025*valid)>=20 and pr['estimate']!='' and br['truth']!='')
  checks=[int(r['attempted_bootstrap'])==attempted,int(r['valid_bootstrap'])==valid,int(r['invalid_bootstrap'])==attempted-valid,b(r['n_gate'])==(valid>=950),b(r['tail_gate'])==(math.floor(.025*valid)>=20),b(r['point_gate'])==(pr['estimate']!=''),b(r['truth_gate'])==(br['truth']!=''),b(r['available'])==available,eq(r['lower'],lo),eq(r['upper'],hi),eq(r['truth'],br['truth'])]
  if available:
   truth=float(br['truth']);checks += [b(r['covered'])==(float(lo)<=truth<=float(hi)),b(r['lower_miss'])==(truth<float(lo)),b(r['upper_miss'])==(truth>float(hi))]
  else:checks += [r['covered']=='',r['lower_miss']=='',r['upper_miss']=='']
  if not all(checks):row_errors.append(k+(fam,))
 expected=(600 if stage=='corrected_pilot' else 4000)*4*2*3*2
 # Independently rebuild every performance row.
 ig={};pg={}
 for r in ints:ig.setdefault((r['scenario_id'],r['scale_method'],r['endpoint'],r['method'],r['interval_family']),[]).append(r)
 for r in points:pg.setdefault((r['scenario_id'],r['scale_method'],r['endpoint'],r['method']),[]).append(r)
 perf_errors=[]
 for obs in perf:
  key=(obs['scenario_id'],obs['scale_method'],obs['endpoint'],obs['method'],obs['interval_family']);ii=ig[key];pp=pg[key[:-1]];theta=num(ii[0]['truth']);pe=[num(x['estimate']) for x in pp if math.isfinite(num(x['estimate']))];errs=[x-theta for x in pe] if math.isfinite(theta) else [];av=[x for x in ii if b(x['available'])];cov=[int(b(x['covered'])) for x in av];width=[num(x['upper'])-num(x['lower']) for x in av];n=len(ii)
  exp={'attempted_outer':n,'point_defined':len(pe),'point_undefined':n-len(pe),'point_bias':statistics.mean(errs) if errs else math.nan,'point_sd':statistics.stdev(pe) if len(pe)>1 else math.nan,'point_rmse':math.sqrt(statistics.mean(x*x for x in errs)) if errs else math.nan,'attempted_bootstrap':sum(int(x['attempted_bootstrap']) for x in ii),'valid_bootstrap':sum(int(x['valid_bootstrap']) for x in ii),'invalid_bootstrap':sum(int(x['invalid_bootstrap']) for x in ii),'available_intervals':len(av),'unavailable_intervals':n-len(av),'availability_rate':len(av)/n,'coverage_available':statistics.mean(cov) if cov else math.nan,'available_and_covered_all':sum(cov)/n,'lower_misses':sum(b(x['lower_miss']) for x in av),'upper_misses':sum(b(x['upper_miss']) for x in av),'mean_width_available':statistics.mean(width) if width else math.nan,'median_width_available':statistics.median(width) if width else math.nan,'mcse_coverage_available':math.sqrt(statistics.mean(cov)*(1-statistics.mean(cov))/len(cov)) if cov else math.nan,'truth':theta}
  if any(not eq(obs[k],v) for k,v in exp.items()):perf_errors.append(key)
 # Independently rebuild paired outer calculations.
 pair_errors=[]
 for obs in paired:
  sid,scale,end,fam,ma,mb=(obs[x] for x in ('scenario_id','scale_method','endpoint','interval_family','method_a','method_b'));a={r['outer_id']:r for r in ig[(sid,scale,end,ma,fam)]};bb={r['outer_id']:r for r in ig[(sid,scale,end,mb,fam)]};ids=sorted(set(a)&set(bb),key=int);da=[int(b(a[i]['available']))-int(b(bb[i]['available'])) for i in ids];ac=[int(b(a[i]['available']) and b(a[i]['covered']))-int(b(bb[i]['available']) and b(bb[i]['covered'])) for i in ids];both=[i for i in ids if b(a[i]['available']) and b(bb[i]['available'])];cd=[int(b(a[i]['covered']))-int(b(bb[i]['covered'])) for i in both];wd=[(num(a[i]['upper'])-num(a[i]['lower']))-(num(bb[i]['upper'])-num(bb[i]['lower'])) for i in both];exp={'n_outer':len(ids),'availability_diff_mean':statistics.mean(da),'availability_diff_mcse':sdse(da),'available_and_covered_diff_mean':statistics.mean(ac),'available_and_covered_diff_mcse':sdse(ac),'both_available_n':len(both),'conditional_coverage_diff_mean':statistics.mean(cd) if cd else math.nan,'conditional_coverage_diff_mcse':sdse(cd),'paired_width_n':len(wd),'paired_width_diff_mean':statistics.mean(wd) if wd else math.nan,'paired_width_diff_mcse':sdse(wd)}
  if any(not eq(obs[k],v) for k,v in exp.items()):pair_errors.append((sid,scale,end,fam,ma,mb))
 return {'stage':stage,'interval_rows':len(ints),'expected_interval_rows':expected,'unique_interval_keys':len(seen),'interval_arithmetic_failures':len(row_errors),'bootstrap_rows':len(boots),'performance_rows':len(perf),'performance_failures':len(perf_errors),'paired_rows':len(paired),'paired_failures':len(pair_errors),'status':'PASS' if len(ints)==expected and len(seen)==expected and not row_errors and not perf_errors and not pair_errors else 'FAIL'}
if __name__=='__main__':
 out=[stage_check(s) for s in ('corrected_pilot','confirmatory')];result={'status':'PASS' if all(x['status']=='PASS' for x in out) else 'FAIL','scope':'every repaired interval row; every performance and paired summary cell','stages':out};(BASE/'independent_table_validation_results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
