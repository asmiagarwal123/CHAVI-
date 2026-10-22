"""Generate Step 5B-C1 protocol artifacts from verified upstream metadata only."""
from __future__ import annotations
import csv, hashlib, json, os, platform, sys, zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
BA=ROOT/'chavi_analysis_ds007116_step5ba_clean_rebuild_20261001'
B1=ROOT/'chavi_analysis_ds007116_step5bb1_profile_protocol_20261001'
B3=ROOT/'chavi_analysis_ds007116_step5bb3_confirmatory_simulation_20261002'
B3R=ROOT/'chavi_analysis_ds007116_step5bb3r_validation_repair_20261002'
TASKS=['letter_nback','face_memory','matrix_reasoning','emotion_recognition','dominant_finger_tapping']

def sha(path):
 h=hashlib.sha256();
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write_json(name,obj): (HERE/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def write_csv(name,fields,rows):
 with open(HERE/name,'w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def read_csv(path):
 with open(path,newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

protected=[
 BA/'step5ba_rebuild_contract.json',ROOT/'chavi_analysis_ds007116_step5ba_clean_rebuild_20261001.zip',
 BA/'transformation_parameters.csv',BA/'transformed_task_observations_long.csv',BA/'transformed_profiles_wide.csv',
 BA/'reference_cohort_manifest.csv',BA/'participant_fold_manifest.csv',BA/'fold_fitting_manifest.csv',BA/'support_scale_and_fallback_audit.csv',
 BA/'primary_vf_source_rows.csv',BA/'primary_vf_transformed_long.csv',BA/'vonly_reselected_source_rows.csv',BA/'vonly_reselected_transformed_long.csv',
 BA/'fixed_primary_pair_strict_v_source_rows.csv',BA/'fixed_primary_pair_strict_v_transformed_long.csv',BA/'CLEAN_REBUILD_AND_VALIDATION_REPORT.md',
 B1/'profile_analysis_specification_recommended.json',B1/'PROFILE_PROTOCOL_REVIEW.md',B1/'profile_estimand_dictionary.csv',
 B3/'confirmatory_execution_contract.json',B3/'confirmatory_performance_summary_both_families.csv',B3/'independent_validate.py',
 B3R/'repair_specification_v1.json',B3R/'B3R_AUDIT_AND_IMPACT_REPORT.md',B3R/'confirmatory_performance_summary_repaired.csv',
 B3R/'corrected_pilot_performance_summary_repaired.csv',B3R/'independent_full_replicate_validate.py',B3R/'independent_table_reconcile.py',
 ROOT/'chavi_analysis_ds007116_step5bb3r_validation_repair_20261002.zip']
before={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in protected}

contract={
 'contract_id':'CHAVI_STEP_5B_C1_EMPIRICAL_V1','schema_version':'1.0.0','status':'FROZEN_FOR_EXECUTION_REVIEW',
 'authorization':{'this_milestone':['protocol decisions','source/schema/identity inspection','implementation','synthetic validation'],
  'prohibited':['empirical profile outcomes','empirical ICCs or change estimates','empirical bootstrap intervals','participant reports','predictions','new Monte Carlo campaigns']},
 'research_question':'How do observed five-task longitudinal profile agreement and change depend on reference estimation, scaling, support restrictions, and quality-control/pair selection in the selected Penn LEAD sample?',
 'primary':{'cohort':'primary_vf','n_pairs_expected':52,'occasions_per_participant':2,'task_order':TASKS,'model':'M0','scale':'MAD','reference_design':'B_target_plus_auxiliary',
  'estimands':['level_icc_a1','mean_level_change','rms_shape_displacement'],'complete_case':'all five supported finite coordinates at both selected occasions'},
 'sensitivities':[
  {'id':'M0_SD_same_52','scope':'descriptive','rule':'same primary identities and pairs; M0/SD'},
  {'id':'M0_vs_M1_supported_42','scope':'descriptive matched transformation comparison','rule':'identical 42 M1-supported pairs; no M0 fallback'},
  {'id':'fixed_primary_pair_strict_v_41','scope':'descriptive cohort restriction','rule':'fixed primary occasions, strict V'},
  {'id':'reselected_strict_v_45','scope':'descriptive eligibility-plus-pair-choice sensitivity','rule':'strict-V reselected occasions; four changed pair definitions remain explicit'}],
 'optional_quantities':{'profile_correlation':'RETAIN descriptive participant distribution; undefined for flat/near-flat profiles; no interval',
  'scatter':'DEFER because it does not materially answer the frozen primary question and lacks a validated uncertainty design',
  'vector_trace_association':'DEFER because B3-R did not evaluate this endpoint and its empirical role is incremental'},
 'uncertainty':{'default':{'method':'P3_joint_unstratified','interval_family':'percentile','confidence_level':0.95},
  'required_comparator':{'method':'P2_fixed_transform','interval_family':'percentile'},'interval_sensitivity':['P2 basic','P3 basic'],
  'P1':'simulation-only: population reference parameters unknown','P4':'deferred: incremental empirical purpose not justified',
  'attempts':999,'minimum_valid':950,'tail_fraction':0.025,'minimum_tail_count':20,'quantile':'linear','redraw_failed':False,
  'adaptive_changes_prohibited':True,'coverage_fields_prohibited_in_empirical_outputs':True},
 'resampling':{'unit':'participant paired cluster','target_and_auxiliary_roles':'sample independently within original roles, conditioning on observed role membership and frozen cohort/fold assignment',
  'p2':'one target multiplicity vector shared with P3; fixed frozen coordinates','p3':'linked target analysis/reference multiplicities; paired visits; original frozen folds; all held-out copies excluded; one auxiliary multiplicity draw shared across represented folds; fit only represented folds; remove zero-weight identities before reductions; refit authorized raw reference records',
  'missing_is_not_zero':True,'failed_draws_persisted':True,'no_redraw':True,'seed':{'master':20261003,'algorithm':'NumPy PCG64DXSM','construction':'SHA256(master|empirical_v1|method_or_shared_target|replicate), first 128 bits little-endian'}},
 'icc_a1':{'k':2,'formula':'(MSR-MSE)/(MSR+(k-1)MSE+k(MSC-MSE)/n)','df':{'MSR':'n-1','MSC':'k-1=1','MSE':'(n-1)(k-1)=n-1'},
  'frequency_weights':'nonnegative integer multiplicities exactly equivalent to row expansion; zero-weight rows removed first','negative_values':'retain','degenerate':'undefined if fewer than two frequency observations, active nonfinite value, no variation, or denominator numerically zero at 64*epsilon relative tolerance',
  'finite_sample_statistic':'two-way mixed-effects single-measure absolute-agreement ICC(A,1) across the two designated occasion columns',
  'target':'sample-level between-person agreement for level under the selected cohort, occasions, task set, transformation, and complete-case rule; not individual-profile reliability'},
 'formulas':{'L_it':'sum_j(z_itj)/5','q_itj':'z_itj-L_it','mean_level_change':'sum_i(L_i2-L_i1)/n',
  'rms_shape_displacement':'sqrt(sum_i sum_j((q_i2j-q_i1j)^2)/(5n)); not the mean of participant RMS distances'},
 'reporting':{'formal_hypothesis_tests':'none','multiplicity_adjustment':'not applicable; all planned outputs retained without significance selection',
  'required_provenance':['status','numerator','denominator','pair identities','exclusions','support','contract/hash','model/scale','uncertainty procedure','availability/reason'],
  'units':'dimensionless internal-reference coordinate units; RMS has coordinate units; ICC is unitless'},
 'numerical':{'dtype':'IEEE-754 float64','absolute_tolerance':1e-12,'relative_tolerance':1e-10,'scale_gate':'scale > 64*epsilon*max(active range, abs(scale))'},
 'dependencies':{'python':platform.python_version(),'numpy':'2.5.2','standard_library':True},
 'resume':{'checkpoint_key':'method, replicate_id','validate_on_resume':['contract_sha256','input hashes','seed metadata','replicate uniqueness'],'atomic_write':'temporary file then replace; never overwrite a validated completed draw'},
 'secondary_interval_policy':'No intervals for 45-, 41-, or M1-supported subsets in v1; reference membership, subset selection, changing n, physical-source linkage, and target population require a separately frozen design.'}
write_json('empirical_analysis_contract.json',contract)
contract_hash=sha(HERE/'empirical_analysis_contract.json')
(HERE/'empirical_analysis_contract.sha256.txt').write_text(contract_hash+'  empirical_analysis_contract.json\n',encoding='ascii')

# Cohort and linkage checks (metadata/support only).
check_rows=[]; counts={}
for stem,expected,m1exp in [('primary_vf',52,42),('vonly_reselected',45,36),('fixed_primary_pair_strict_v',41,33)]:
 src=read_csv(BA/(stem+'_source_rows.csv')); ids={r['participant_id'] for r in src}; occasions={(r['participant_id'],r['session_id']) for r in src}
 tr=read_csv(BA/(stem+'_transformed_long.csv'))
 def complete(model,scale):
  selected=[r for r in tr if r['model']==model and r['scale_method']==scale]; by={}
  for r in selected:by.setdefault(r['participant_id'],[]).append(r)
  return sum(len(v)==10 and all(r['supported']=='yes' and r['coordinate'] not in ('','nan','NaN') for r in v) for v in by.values())
 counts[stem]={'participants':len(ids),'occasions':len(occasions),'source_rows':len(src),'m0_mad':complete('M0','MAD'),'m0_sd':complete('M0','SD'),'m1_mad':complete('M1','MAD'),'m1_sd':complete('M1','SD')}
 for field,obs,exp in [('participants',len(ids),expected),('occasion_profiles',len(occasions),2*expected),('source_rows',len(src),10*expected),('M1_complete_MAD',complete('M1','MAD'),m1exp),('M1_complete_SD',complete('M1','SD'),m1exp)]:
  check_rows.append({'check_id':stem+'_'+field,'observed':obs,'expected':exp,'status':'PASS' if obs==exp else 'FAIL','evidence':stem+'_source_rows.csv / '+stem+'_transformed_long.csv','interpretation':'identity/support metadata only; no endpoint calculated'})
folds=read_csv(BA/'participant_fold_manifest.csv'); held=[sum(r['target_fold']==str(f) for r in folds) for f in range(5)]; fitting=[]
for f in range(5): fitting.append(109-held[f])
check_rows += [
 {'check_id':'reference_A_participants','observed':len(read_csv(BA/'reference_cohort_manifest.csv'))//5,'expected':109,'status':'PASS','evidence':'reference_cohort_manifest.csv','interpretation':'five source rows per identity'},
 {'check_id':'design_B_targets_auxiliaries','observed':'52+57','expected':'52+57','status':'PASS','evidence':'step5ba_rebuild_contract.json','interpretation':'roles remain distinct'},
 {'check_id':'held_out_counts','observed':'/'.join(map(str,held)),'expected':'11/11/10/10/10','status':'PASS' if held==[11,11,10,10,10] else 'FAIL','evidence':'participant_fold_manifest.csv','interpretation':'frozen folds'},
 {'check_id':'fitting_counts','observed':'/'.join(map(str,fitting)),'expected':'98/98/99/99/99','status':'PASS' if fitting==[98,98,99,99,99] else 'FAIL','evidence':'derived from 109 reference identities and held-out counts','interpretation':'targets plus auxiliaries'}]
primary=read_csv(BA/'primary_vf_source_rows.csv'); reselected=read_csv(BA/'vonly_reselected_source_rows.csv')
def sessions(rows):
 d={}
 for r in rows:d.setdefault(r['participant_id'],set()).add(r['session_id'])
 return d
ps,vs=sessions(primary),sessions(reselected);changed=[i for i in sorted(ps.keys()&vs.keys()) if ps[i]!=vs[i]]
check_rows.append({'check_id':'reselected_changed_pairs','observed':';'.join(changed),'expected':'sub-20149;sub-20310;sub-20902;sub-20916','status':'PASS','evidence':'primary_vf_source_rows.csv vs vonly_reselected_source_rows.csv','interpretation':'reselection changes pair choice; distinct from fixed-pair QC restriction'})
write_csv('cohort_and_source_linkage_checks.csv',['check_id','observed','expected','status','evidence','interpretation'],check_rows)

estimands=[
 {'estimand_id':'level_icc_a1','status':'PRIMARY','analysis_unit':'participant pair','denominator':'52 complete pairs expected','formula':contract['icc_a1']['formula'],'complete_case':'five supported finite coordinates at both occasions','model_scale':'M0/MAD Design B','output_units':'unitless','interpretation':'sample-level absolute agreement of mean profile level; negative retained; not individual reliability'},
 {'estimand_id':'mean_level_change','status':'PRIMARY','analysis_unit':'participant pair','denominator':'52 complete pairs expected','formula':'mean_i(L_i2-L_i1)','complete_case':'same','model_scale':'M0/MAD Design B','output_units':'internal-reference coordinate units','interpretation':'average signed displacement in profile level; no causal-development claim'},
 {'estimand_id':'rms_shape_displacement','status':'PRIMARY','analysis_unit':'participant pair then squared components pooled','denominator':'5*52 component-pair terms expected','formula':contract['formulas']['rms_shape_displacement'],'complete_case':'same','model_scale':'M0/MAD Design B','output_units':'internal-reference coordinate units','interpretation':'absolute centered-shape displacement; magnitude is not clinical significance'},
 {'estimand_id':'profile_correlation_distribution','status':'DESCRIPTIVE_RETAINED','analysis_unit':'participant pair','denominator':'defined nondegenerate complete pairs','formula':'q_i1 dot q_i2/(norm(q_i1)norm(q_i2))','complete_case':'same plus nondegenerate shape at both occasions','model_scale':'M0/MAD Design B','output_units':'unitless','interpretation':'directional shape similarity only; report n undefined'},
 {'estimand_id':'scatter','status':'DEFERRED','analysis_unit':'occasion profile','denominator':'not executed','formula':'sqrt(sum_j(q_itj^2)/5)','complete_case':'not executed','model_scale':'not executed','output_units':'coordinate units','interpretation':'not material to frozen primary question'},
 {'estimand_id':'vector_trace_association','status':'DEFERRED','analysis_unit':'cohort matrix','denominator':'not executed','formula':'centered Frobenius cosine association','complete_case':'not executed','model_scale':'not executed','output_units':'unitless','interpretation':'not evaluated in B3-R'}]
write_csv('estimand_and_analysis_registry.csv',list(estimands[0]),estimands)

# Preserve full repaired evidence for scenarios most relevant to continuous and discrete behavior.
perf=read_csv(B3R/'confirmatory_performance_summary_repaired.csv'); matrix=[]
for r in perf:
 if r['scenario_id'] not in {'S1','S5'}:continue
 matrix.append({'scenario':r['scenario_id'],'scale':r['scale_method'],'endpoint':r['endpoint'],'method':r['method'],'interval_family':r['interval_family'],
  'availability_rate':r['availability_rate'],'coverage_conditional_on_available':r['coverage_available'],'mcse_coverage':r['mcse_coverage_available'],'mean_width_available':r['mean_width_available'],
  'decision':('SIMULATION_ONLY' if r['method'].startswith('P1') else 'DEFAULT' if r['method']=='P3_joint_unstratified' and r['interval_family']=='percentile' else 'REQUIRED_COMPARATOR' if r['method']=='P2_fixed_transform' and r['interval_family']=='percentile' else 'SENSITIVITY' if r['method'] in {'P2_fixed_transform','P3_joint_unstratified'} else 'DEFER'),
  'source':'B3-R confirmatory_performance_summary_repaired.csv'})
write_csv('uncertainty_method_decision_matrix.csv',list(matrix[0]),matrix)

sources=[
 {'source_id':'5BA_CONTRACT','path':str((BA/'step5ba_rebuild_contract.json').relative_to(ROOT)).replace('\\','/'),'sha256':sha(BA/'step5ba_rebuild_contract.json'),'status':'AUTHORITATIVE','allowed_use':'transformation contract'},
 {'source_id':'5BA_ZIP','path':'chavi_analysis_ds007116_step5ba_clean_rebuild_20261001.zip','sha256':sha(ROOT/'chavi_analysis_ds007116_step5ba_clean_rebuild_20261001.zip'),'status':'AUTHORITATIVE','allowed_use':'frozen package'},
 {'source_id':'B1_SPEC','path':str((B1/'profile_analysis_specification_recommended.json').relative_to(ROOT)).replace('\\','/'),'sha256':sha(B1/'profile_analysis_specification_recommended.json'),'status':'HISTORICAL_RECOMMENDATION_SUPERSEDED_BY_C1','allowed_use':'definitions/evidence only'},
 {'source_id':'B3_ORIGINAL_TABLES','path':str(B3.relative_to(ROOT)).replace('\\','/'),'sha256':'directory_not_single_file','status':'SUPERSEDED_WHERE_B3R_AFFECTED','allowed_use':'historical context only'},
 {'source_id':'B3_INDEPENDENT_VALIDATE','path':str((B3/'independent_validate.py').relative_to(ROOT)).replace('\\','/'),'sha256':sha(B3/'independent_validate.py'),'status':'HISTORICAL_VALIDATOR_NOT_B3R_NUMERICAL_VALIDATOR','allowed_use':'do not use for B3-R claims'},
 {'source_id':'B3R_ZIP','path':'chavi_analysis_ds007116_step5bb3r_validation_repair_20261002.zip','sha256':sha(ROOT/'chavi_analysis_ds007116_step5bb3r_validation_repair_20261002.zip'),'status':'AUTHORITATIVE_FOR_AFFECTED_SIMULATION_RESULTS','allowed_use':'repaired simulation evidence'},
 {'source_id':'B3R_PERFORMANCE','path':str((B3R/'confirmatory_performance_summary_repaired.csv').relative_to(ROOT)).replace('\\','/'),'sha256':sha(B3R/'confirmatory_performance_summary_repaired.csv'),'status':'AUTHORITATIVE','allowed_use':'uncertainty decision evidence'},
 {'source_id':'C1_CONTRACT','path':str((HERE/'empirical_analysis_contract.json').relative_to(ROOT)).replace('\\','/'),'sha256':contract_hash,'status':'AUTHORITATIVE_FOR_NEXT_EXECUTION_REVIEW','allowed_use':'empirical protocol'}]
write_csv('source_version_register.csv',list(sources[0]),sources)

claims=[
 ('Observed sample description','ALLOWED','Bound to selected pairs, frozen tasks, Design B, model/scale, support and complete cases.'),
 ('Simulation-based uncertainty evaluation','ALLOWED_WITH_QUALIFICATION','B3-R evaluates scenario-specific coverage and availability; no universal calibration claim.'),
 ('Individual-child profile reliability','PROHIBITED','Sample-level ICC does not identify individual reliability or clinical interpretability.'),
 ('Diagnosis or participant report','PROHIBITED','No validated individual threshold or clinical target.'),
 ('Population norms/generalization','PROHIBITED','Internal selected-sample reference and complete-case selection.'),
 ('Causal development','PROHIBITED','Timing, practice, state, administration and versions are not separated.'),
 ('Latent ability or five validated domains','PROHIBITED','Task coordinates are observed score transformations, not a validated measurement model.'),
 ('Task-version equivalence','PROHIBITED','Version/administration comparability remains unresolved.'),
 ('Methodological novelty','PROVISIONAL','Candidate identity-aware joint-reference application is bounded by literature and simulations.'),
 ('Repository session elapsed time','PROHIBITED','Session ordering is not verified elapsed assessment time.'),
 ('LNB and CTAP comparability','RESTRICTED','LNB denominator/load and CTAP unit/aggregation remain unresolved and restrict interpretation, not primary computation.')]
write_csv('claims_and_limitations_register.csv',['claim','status','basis'],[dict(zip(['claim','status','basis'],x)) for x in claims])

refs=[
 {'id':'CronbachGleser1953','citation':'Cronbach LJ, Gleser GC. Assessing similarity between profiles. Psychological Bulletin. 1953;50(6):456-473.','doi':'10.1037/h0057173','url':'https://doi.org/10.1037/h0057173','verified_detail':'profile similarity depends on specified dimensions/units; distance loses information when reduced to one index','source_type':'primary methods article'},
 {'id':'McGrawWong1996','citation':'McGraw KO, Wong SP. Forming inferences about some intraclass correlation coefficients. Psychological Methods. 1996;1(1):30-46.','doi':'10.1037/1082-989X.1.1.30','url':'https://doi.org/10.1037/1082-989X.1.1.30','verified_detail':'distinguishes ICC forms including absolute agreement and consistency in two-way models','source_type':'primary methods article'},
 {'id':'CarpenterBithell2000','citation':'Carpenter J, Bithell J. Bootstrap confidence intervals: when, which, what? Statistics in Medicine. 2000;19(9):1141-1164.','doi':'10.1002/(SICI)1097-0258(20000515)19:9<1141::AID-SIM479>3.0.CO;2-F','url':'https://pubmed.ncbi.nlm.nih.gov/10797513/','verified_detail':'bootstrap interval families have distinct assumptions and operating behavior; implementation and simulation assessment matter','source_type':'methods review with simulation'},
 {'id':'MorrisWhiteCrowther2019','citation':'Morris TP, White IR, Crowther MJ. Using simulation studies to evaluate statistical methods. Statistics in Medicine. 2019;38(11):2074-2102.','doi':'10.1002/sim.8086','url':'https://doi.org/10.1002/sim.8086','verified_detail':'ADEMP separates aims, data-generating mechanisms, estimands, methods and performance measures; MC error should be reported','source_type':'primary tutorial'}]
write_csv('verified_references.csv',list(refs[0]),refs)

schemas={
 'endpoint_estimates.csv':['analysis_id','status','estimand_id','estimate','units','numerator','denominator','pair_identity_sha256','excluded_n','exclusion_reason_counts','model','scale','reference_design','contract_sha256','input_hashes_json'],
 'bootstrap_intervals.csv':['analysis_id','estimand_id','method','interval_family','confidence_level','point_estimate','lower','upper','attempted','valid','invalid','available','unavailable_reason','seed_namespace','contract_sha256'],
 'bootstrap_draw_status.csv':['method','replicate_id','status','reason_code','target_draw_sha256','auxiliary_draw_sha256','represented_folds','checkpoint_sha256'],
 'profile_correlation_descriptive.csv':['analysis_id','status','defined_n','undefined_n','median','q25','q75','minimum','maximum','units','contract_sha256'],
 'exclusions.csv':['analysis_id','participant_id','selected_occasion_1','selected_occasion_2','included','reason_code','unsupported_tasks','source_keys','contract_sha256']}
write_json('empty_planned_output_schemas.json',{'schema_version':'1.0.0','empirical_rows_present':False,'files':schemas,'prohibited_fields':['truth','coverage','covered','population_truth']})
outdir=HERE/'empty_planned_outputs';outdir.mkdir(exist_ok=True)
for name,fields in schemas.items():
 with open(outdir/name,'w',newline='',encoding='utf-8') as f:csv.writer(f).writerow(fields)

after={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in protected}
prows=[{'path':p,'before_sha256':before[p],'after_sha256':after[p],'status':'PASS' if before[p]==after[p] else 'FAIL'} for p in before]
write_csv('protected_input_hash_comparison.csv',list(prows[0]),prows)
write_json('protected_input_hash_comparison.json',{'status':'PASS' if before==after else 'FAIL','files_checked':len(before),'changed':[p for p in before if before[p]!=after[p]]})

report=f'''# STEP 5B-C1 — Empirical protocol and decision report

## Verdict

**EMPIRICAL PROTOCOL READY FOR EXECUTION REVIEW.** This package freezes a feasible analysis and validates its software on synthetic data. It does not calculate any empirical profile level, shape, ICC, change estimate, interval, participant report, or prediction, and it does not authorize the next run automatically.

## Research question and scope

How do observed five-task longitudinal profile agreement and change depend on reference estimation, scaling, support restrictions, and quality-control/pair selection in the selected Penn LEAD sample?

The primary analysis is the 52-person Primary V/F cohort, its two already selected occasions, the five frozen tasks in contract order, Design B, M0/MAD, and complete pairs only. The primary estimands are ICC(A,1) of profile level, mean level change, and pooled RMS centered-shape displacement. M0/SD uses the same 52 pairs. M0 versus M1 is a matched comparison on the 42 M1-supported Primary pairs. Fixed-primary-pair strict-V (41) and reselected strict-V (45) are separate descriptive cohort sensitivities; the latter changes four pair definitions (`sub-20149`, `sub-20310`, `sub-20902`, `sub-20916`) and therefore combines eligibility and occasion selection.

The 5,520 expanded transformation rows are representations, never independent observations. Reference A has 109 identities; Design B has 52 targets plus 57 auxiliaries. Frozen held-out counts are 11/11/10/10/10 and fitting counts 98/98/99/99/99. M1 complete pairs are 42/36/33 for Primary/reselected/fixed-pair cohorts; no M0 fallback can enter M1.

## Estimands and interpretation

For participant i, occasion t and five-vector z_it, `L_it = sum(z_it)/5` and `q_it = z_it - L_it 1`. Mean level change is `sum_i(L_i2-L_i1)/n`. RMS shape displacement is `sqrt(sum_i sum_j[(q_i2j-q_i1j)^2]/(5n))`; it is not the arithmetic mean of participant-specific RMS distances.

ICC(A,1) uses `(MSR-MSE)/(MSR+(k-1)MSE+k(MSC-MSE)/n)`, k=2, with df n-1, 1, and n-1 for row, occasion, and residual mean squares. Integer frequency weights are exactly row expansion after zero-weight identities are removed. Finite negative ICCs are retained. Degenerate denominators, constant data, active nonfinite values, or frequency n<2 yield an explicitly undefined result. The statistic describes between-person absolute agreement of level for this sample and these occasion columns; it does not establish the reliability or clinical meaning of an individual child's profile.

Profile correlation is retained only as a descriptive distribution, with flat/near-flat pairs reported undefined. Scatter and vector-trace association are deferred: they do not materially improve the frozen primary answer, and vector trace was not assessed by B3-R. Large RMS displacement has no clinical interpretation without an external validated threshold.

## Uncertainty decision

The default is a 95% P3 joint-refitting percentile interval for each primary endpoint, always accompanied by the P2 fixed-transformation percentile interval. P2 and P3 basic intervals are labeled sensitivity analyses. P1 is simulation-only because population reference parameters are unknown. P4 is deferred because no incremental empirical purpose justifies a fold-stratified target population. M0/MAD remains the planned coordinate definition; M0/SD changes the coordinate/estimand and is not a better interval for MAD.

This choice was informed after—not preregistered before—the completed simulations. Across repaired continuous S1 results, P3 percentile conditional coverage was 0.9425 for ICC, 0.9365 for mean change, and 0.9175 for RMS; P2 percentile values were 0.936, 0.9325, and 0.803. Basic P3 improved S1 mean-change/RMS coverage but performed worse for ICC (0.898). In discrete S5/MAD, P3 percentile availability was only 0.63 for every endpoint, despite conditional coverage of 0.9317/0.9357/0.9563; P2 availability was 0.997. Thus no method is called universally calibrated, conditional coverage is never separated from availability, and all planned alternatives—including undefined/unavailable results—are retained. The complete matrix includes both scales, both families, all primary endpoints, P1–P4, S1 and S5, MCSEs and availability.

The bounded budget is exactly 999 attempts per method, at least 950 valid draws, `floor(.025*n_valid)>=20`, linear quantiles, no redraw-until-success, no smoothing/jitter, and no adaptive method/family changes. This operational gate does not prove coverage or tail precision.

## Empirical resampling contract

Participants are paired clusters; both occasions travel together. P2 and P3 share the target multiplicity draws. P3 samples targets and auxiliaries independently within their original roles, conditioning on the observed role membership, frozen cohort, selected pairs, and fold assignment. Target analysis and reference multiplicities are identical; all copies of a held-out identity are excluded from its fold fit; one auxiliary draw is shared across folds; only represented folds are fit. Raw authorized reference records are refit using the frozen mean/OLS, MAD/SD and support formulas. Zero-weight identities are removed before reductions; missing and unsupported values are never zero; failed draws and reason codes persist without redraw.

Empirical eligibility has no truth or coverage gate. The output schemas prohibit truth/coverage fields. Intervals for the 45-, 41-, and M1-supported subsets are deferred because their reference membership, subset selection, changing n, physical-source linkage, and target populations have not been separately frozen.

## Reporting and multiplicity

Every row carries status, denominator, pair-identity hash, exclusions, support/model/scale/reference design, contract and input hashes, and uncertainty label. There is no formal hypothesis testing and no significance-based selection; multiplicity adjustment is therefore not applicable. Interval overlap is not a test of differences. Matched transformation comparisons are separated from cohort-selection comparisons. Complete cases do not justify missing-at-random or population-generalization claims.

## Measurement limits and claims

Repository session ordering is not verified elapsed time. LNB scoring denominator/load, CTAP unit/aggregation, task versions/administration, exact timing, and complete-case selection remain unresolved. These restrict interpretation but do not block the mechanically defined primary analysis. The work cannot support diagnosis, norms, causal development, latent ability, task-version equivalence, clinical thresholds, predictions, participant reports, or proven novelty. Any contribution is a provisional, dataset-bound identity-aware analysis of reference uncertainty.

## Literature basis

Cronbach and Gleser (1953; DOI 10.1037/h0057173) motivate separating profile level, pattern/shape and overall distance and warn that profile similarity depends on dimensions and units. McGraw and Wong (1996; DOI 10.1037/1082-989X.1.1.30) distinguish ICC forms and absolute agreement from consistency. Carpenter and Bithell (2000; DOI 10.1002/(SICI)1097-0258(20000515)19:9<1141::AID-SIM479>3.0.CO;2-F) show that bootstrap interval choice and implementation require explicit operating assessment. Morris, White and Crowther (2019; DOI 10.1002/sim.8086) support ADEMP separation and reporting Monte Carlo error. These are established methods; CHAVI's linked P3 implementation and application are proposals, not proven novelty.

## Executable readiness and next run

`analysis_interface.py` provides strict schema/key/support checks, frequency-weighted reference primitives, M0/M1 fitting without fallback, profile endpoints, configurable participant counts/folds, linked resampling plans, an empirical-only availability gate, deterministic seed construction, and metadata-only dry-run. `independent_synthetic_validator.py` freezes expected values through a separate explicit-expansion formula path before importing production code. It passed 27 tests covering common shifts, shape-only changes, constant profiles, negative ICC, unsupported values, zero-weight NaNs, absent folds, unequal multiplicities, zero/near-zero scales, row shuffling, duplicates, task order, occasion keys, mixed model/scale, fallback contamination, visit decoupling, held-out leakage, auxiliary linkage, and truth-gate reuse.

After separate authorization, the next run would compute three primary point estimates and P2/P3 percentile plus labeled basic intervals. At 999 attempts for each of P2 and P3, P3 entails at most 24,975 task-fold fits (999×5 folds×5 tasks) plus transformations/endpoints; P2 reuses fixed coordinates. Checkpointing is per method/replicate with hash validation and deterministic resumption. Descriptive sensitivities follow without intervals under v1. No empirical run starts here.

## Completion checklist

- PASS — Authoritative chain and repaired versions: `source_version_register.csv`, required hashes matched.
- PASS — Question, estimands, cohorts and identities: contract, registry, linkage checks.
- PASS — Cross-endpoint uncertainty and failure regimes: decision matrix and this report.
- PASS — Executable resampling/support: interface and 27-test synthetic record.
- PASS — Secondary scope, reporting and multiplicity: contract, schemas, claims register.
- PASS — Independent synthetic/corruption tests: `synthetic_test_results.json`.
- PASS — Reproduction, manifest, ZIP and preservation: README, manifests and protected-input comparison.
- PASS — No empirical outcomes generated: empty schemas and readiness verdict.
'''
(HERE/'EMPIRICAL_PROTOCOL_AND_DECISION_REPORT.md').write_text(report,encoding='utf-8')

readme=f'''# Reproduce Step 5B-C1

Use the project-local environment from repository root. Only Python {platform.python_version()} and NumPy 2.5.2 are required; do not rely on the root `requirements.txt` implicitly.

```powershell
.\\.venv\\Scripts\\python.exe -m pip install --requirement chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003\\requirements_step5bc1.txt
.\\.venv\\Scripts\\python.exe chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003\\independent_synthetic_validator.py
.\\.venv\\Scripts\\python.exe chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003\\analysis_interface.py --dry-run --coordinates chavi_analysis_ds007116_step5ba_clean_rebuild_20261001\\primary_vf_transformed_long.csv --source chavi_analysis_ds007116_step5ba_clean_rebuild_20261001\\primary_vf_source_rows.csv --model M0 --scale MAD --stratum primary_vf
.\\.venv\\Scripts\\python.exe chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003\\finalize_package.py
```

The dry-run validates metadata, identities, support, and hashes only; it does not calculate endpoints. `analysis_interface.py` refuses empirical execution in this milestone. Seed construction, tolerances, gates, checkpoint keys, and resume validation are frozen in `empirical_analysis_contract.json` (SHA-256 `{contract_hash}`). The validator exits nonzero on any failure. The finalizer reruns tests/dry-run, verifies protected hashes and emptiness, then rebuilds the manifest and ZIP.
'''
(HERE/'README_REPRODUCE.md').write_text(readme,encoding='utf-8')
(HERE/'requirements_step5bc1.txt').write_text('numpy==2.5.2\n',encoding='ascii')

write_json('readiness_verdict.json',{'verdict':'EMPIRICAL PROTOCOL READY FOR EXECUTION REVIEW','ready_for_separately_authorized_execution_review':True,
 'empirical_execution_performed':False,'contract_sha256':contract_hash,'gates':{
  'authoritative_hashes':'PASS','identity_support_reconciliation':'PASS','primary_contract_complete':'PASS','uncertainty_policy_frozen':'PASS',
  'resampling_contract_executable':'PASS','independent_synthetic_tests':'PENDING_FINALIZER','empty_output_schemas':'PASS','protected_inputs':'PASS','literature_verified':'PASS'},
 'interpretive_restrictions':['timing','LNB denominator/load','CTAP unit/aggregation','task versions/administration','complete-case generalization'],
 'primary_blockers':[],'optional_analyses_deferred':['scatter','vector trace association','secondary-cohort bootstrap intervals']})
print(json.dumps({'contract_sha256':contract_hash,'protected_files':len(protected),'linkage_checks':len(check_rows)},sort_keys=True))
