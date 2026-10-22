"""Replace only repaired P3 outer records and rebuild summaries/paired MCSEs."""
from pathlib import Path
import ast,csv,json,math,statistics

BASE=Path(__file__).resolve().parent
B3=BASE.parent/'chavi_analysis_ds007116_step5bb3_confirmatory_simulation_20261002'
METHODS=("P1_oracle_conditional","P2_fixed_transform","P3_joint_unstratified","P4_joint_fold_stratified")
SCALES=("MAD","SD"); ENDS=("level_icc_a1","mean_level_change","rms_shape_displacement"); FAMS=("percentile","basic")

def read_csv(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write_csv(path,rows,fields=None):
    if fields is None: fields=list(rows[0])
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
def b(x):return str(x).lower()=='true'
def f(x):return float(x) if x not in ('',None,'None','nan') else math.nan
def sdse(x):return math.sqrt(statistics.variance(x)/len(x)) if len(x)>1 else math.nan

def repair_map(stage):
    out={}
    for p in sorted((BASE/'runtime_repaired'/stage).glob('*.json')):
        o=json.loads(p.read_text(encoding='utf-8'))
        for r in o['records']:
            out[(o['scenario_id'],str(o['outer_id']),r['scale_method'],r['endpoint'])]=r
    return out

def rebuild(stage):
    rep=repair_map(stage)
    expected={('corrected_pilot',s):n for s,n in [('S1',8),('S2',5),('S3',4),('S4',4),('S5',6),('S6',5)]}
    expected.update({('confirmatory','S1'):106,('confirmatory','S5'):110})
    for sid in ({k[0] for k in rep}):
        got=len({int(k[1]) for k in rep if k[0]==sid})
        if got!=expected[(stage,sid)]:raise RuntimeError(f'incomplete repaired runtime {stage}/{sid}: {got}')
    ipath=B3/f'{stage}_interval_results_both_families.csv'
    ints=read_csv(ipath); changed_interval_rows=0
    for row in ints:
        key=(row['scenario_id'],row['outer_id'],row['scale_method'],row['endpoint'])
        if row['method']!='P3_joint_unstratified' or key not in rep:continue
        r=rep[key]; fam=row['interval_family']; lo=r[fam+'_lower']; hi=r[fam+'_upper']; truth=r['truth']; avail=r['available']
        updates={'attempted_bootstrap':r['attempted'],'valid_bootstrap':r['valid'],'invalid_bootstrap':r['invalid'],'n_gate':r['n_gate'],'tail_gate':r['tail_gate'],'point_gate':r['point_gate'],'truth_gate':r['truth_gate'],'available':avail,'lower':lo,'upper':hi,'truth':truth,
                 'covered':(lo is not None and hi is not None and truth is not None and lo<=truth<=hi) if avail else '',
                 'lower_miss':(truth<lo) if avail else '','upper_miss':(truth>hi) if avail else ''}
        before=tuple(row[k] for k in updates); row.update({k:str(v) if v is not None else '' for k,v in updates.items()})
        if tuple(row[k] for k in updates)!=before:changed_interval_rows+=1
    write_csv(BASE/f'{stage}_interval_results_repaired.csv',ints)

    boots=read_csv(B3/f'{stage}_bootstrap_status_and_failure_reason_counts.csv'); changed_boot_rows=0
    for row in boots:
        key=(row['scenario_id'],row['outer_id'],row['scale_method'],row['endpoint'])
        if row['method']!='P3_joint_unstratified' or key not in rep:continue
        r=rep[key]; fr={'valid':r['valid'],'undefined':r['invalid'],'unsupported_fit':r['unsupported_fit']}
        updates={'attempted':r['attempted'],'valid':r['valid'],'invalid':r['invalid'],'failure_reasons':str(fr),'n_gate':r['n_gate'],'tail_gate':r['tail_gate'],'point_gate':r['point_gate'],'truth_gate':r['truth_gate'],'available':r['available'],'q025':r['q025'],'q975':r['q975'],'percentile_lower':r['percentile_lower'],'percentile_upper':r['percentile_upper'],'basic_lower':r['basic_lower'],'basic_upper':r['basic_upper'],'truth':r['truth']}
        before=tuple(row[k] for k in updates);row.update({k:str(v) if v is not None else '' for k,v in updates.items()})
        if tuple(row[k] for k in updates)!=before:changed_boot_rows+=1
    write_csv(BASE/f'{stage}_bootstrap_status_repaired.csv',boots)

    points=read_csv(B3/f'{stage}_point_estimates.csv'); pgroup={}
    for r in points:pgroup.setdefault((r['scenario_id'],r['scale_method'],r['endpoint'],r['method']),[]).append(r)
    igroup={}
    for r in ints:igroup.setdefault((r['scenario_id'],r['scale_method'],r['endpoint'],r['method'],r['interval_family']),[]).append(r)
    perf=[]
    for key,ii in sorted(igroup.items()):
        sid,scale,endpoint,method,fam=key;p=pgroup[(sid,scale,endpoint,method)];theta=f(ii[0]['truth']);pe=[f(r['estimate']) for r in p if math.isfinite(f(r['estimate']))];errs=[x-theta for x in pe] if math.isfinite(theta) else []
        av=[r for r in ii if b(r['available'])];cov=[int(b(r['covered'])) for r in av];width=[f(r['upper'])-f(r['lower']) for r in av];n=len(ii);covered=sum(cov)
        perf.append({'stage':stage,'scenario_id':sid,'scale_method':scale,'endpoint':endpoint,'method':method,'interval_family':fam,'contract_hash':ii[0]['contract_hash'],'attempted_outer':n,'point_defined':len(pe),'point_undefined':n-len(pe),'point_bias':statistics.mean(errs) if errs else math.nan,'point_sd':statistics.stdev(pe) if len(pe)>1 else math.nan,'point_rmse':math.sqrt(statistics.mean(x*x for x in errs)) if errs else math.nan,'attempted_bootstrap':sum(int(r['attempted_bootstrap']) for r in ii),'valid_bootstrap':sum(int(r['valid_bootstrap']) for r in ii),'invalid_bootstrap':sum(int(r['invalid_bootstrap']) for r in ii),'available_intervals':len(av),'unavailable_intervals':n-len(av),'availability_rate':len(av)/n,'coverage_available':statistics.mean(cov) if cov else math.nan,'available_and_covered_all':covered/n,'lower_misses':sum(b(r['lower_miss']) for r in av),'upper_misses':sum(b(r['upper_miss']) for r in av),'mean_width_available':statistics.mean(width) if width else math.nan,'median_width_available':statistics.median(width) if width else math.nan,'mcse_coverage_available':math.sqrt(statistics.mean(cov)*(1-statistics.mean(cov))/len(cov)) if cov else math.nan,'truth':theta})
    write_csv(BASE/f'{stage}_performance_summary_repaired.csv',perf)

    paired=[]
    for sid in sorted({r['scenario_id'] for r in ints}):
      for scale in SCALES:
       for endpoint in ENDS:
        for fam in FAMS:
         def rows(m):return {r['outer_id']:r for r in ints if r['scenario_id']==sid and r['scale_method']==scale and r['endpoint']==endpoint and r['interval_family']==fam and r['method']==m}
         for ma,mb in [('P2_fixed_transform','P3_joint_unstratified'),('P1_oracle_conditional','P2_fixed_transform'),('P1_oracle_conditional','P3_joint_unstratified'),('P3_joint_unstratified','P4_joint_fold_stratified')]:
          a,bb=rows(ma),rows(mb);ids=sorted(set(a)&set(bb),key=int);da=[int(b(a[i]['available']))-int(b(bb[i]['available'])) for i in ids];ac=[int(b(a[i]['available']) and b(a[i]['covered']))-int(b(bb[i]['available']) and b(bb[i]['covered'])) for i in ids];both=[i for i in ids if b(a[i]['available']) and b(bb[i]['available'])];cd=[int(b(a[i]['covered']))-int(b(bb[i]['covered'])) for i in both];wd=[(f(a[i]['upper'])-f(a[i]['lower']))-(f(bb[i]['upper'])-f(bb[i]['lower'])) for i in both]
          paired.append({'stage':stage,'scenario_id':sid,'scale_method':scale,'endpoint':endpoint,'interval_family':fam,'contract_hash':ints[0]['contract_hash'],'method_a':ma,'method_b':mb,'n_outer':len(ids),'availability_diff_mean':statistics.mean(da),'availability_diff_mcse':sdse(da),'available_and_covered_diff_mean':statistics.mean(ac),'available_and_covered_diff_mcse':sdse(ac),'both_available_n':len(both),'conditional_coverage_diff_mean':statistics.mean(cd) if cd else math.nan,'conditional_coverage_diff_mcse':sdse(cd),'paired_width_n':len(wd),'paired_width_diff_mean':statistics.mean(wd) if wd else math.nan,'paired_width_diff_mcse':sdse(wd)})
    write_csv(BASE/f'{stage}_paired_comparisons_repaired.csv',paired)
    return {'stage':stage,'repaired_outer_records':len({(k[0],k[1]) for k in rep}),'interval_rows':len(ints),'changed_interval_rows':changed_interval_rows,'changed_bootstrap_rows':changed_boot_rows}

def compare(stage,kind,newname):
    old=read_csv(B3/f'{stage}_{kind}.csv');new=read_csv(BASE/newname)
    keys=['stage','scenario_id','scale_method','endpoint','method','interval_family']
    if 'paired' in kind:keys+=['method_a','method_b'];keys.remove('method')
    om={tuple(r[k] for k in keys):r for r in old};rows=[]
    for nr in new:
        key=tuple(nr[k] for k in keys);orr=om[key]
        for col in nr:
            if col in keys or col=='contract_hash':continue
            try:
                ov=f(orr[col]);nv=f(nr[col]);delta=nv-ov if math.isfinite(ov) and math.isfinite(nv) else (0.0 if (not math.isfinite(ov) and not math.isfinite(nv)) else math.nan)
                rows.append({'stage':stage,'table':kind,'scenario_id':nr['scenario_id'],'scale_method':nr['scale_method'],'endpoint':nr['endpoint'],'method':nr.get('method',''),'interval_family':nr['interval_family'],'method_a':nr.get('method_a',''),'method_b':nr.get('method_b',''),'metric':col,'original':orr[col],'repaired':nr[col],'delta':delta,'changed':(math.isfinite(delta) and abs(delta)>1e-15) or (math.isfinite(ov)!=math.isfinite(nv))})
            except (ValueError,KeyError):pass
    return rows

if __name__=='__main__':
    status=[rebuild(s) for s in ('corrected_pilot','confirmatory')]
    comp=[]
    for s in ('corrected_pilot','confirmatory'):
        comp+=compare(s,'performance_summary_both_families',f'{s}_performance_summary_repaired.csv')
        comp+=compare(s,'paired_outer_method_comparisons',f'{s}_paired_comparisons_repaired.csv')
    write_csv(BASE/'original_vs_repaired_results.csv',comp)
    (BASE/'recalculation_status.json').write_text(json.dumps({'status':'PASS','stages':status,'comparison_cells':len(comp),'changed_cells':sum(str(r['changed']).lower()=='true' for r in comp)},indent=2)+'\n',encoding='utf-8')
    print((BASE/'recalculation_status.json').read_text())
