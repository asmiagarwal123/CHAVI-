"""Freeze C2 execution decisions before empirical endpoint calculation."""
from __future__ import annotations
import csv, hashlib, json, platform
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parents[1]
BA=ROOT/'chavi_analysis_ds007116_step5ba_clean_rebuild_20261001';C1=ROOT/'chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003';B3R=ROOT/'chavi_analysis_ds007116_step5bb3r_validation_repair_20261002'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rows(p):
 with open(p,newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
deps=[C1/'empirical_analysis_contract.json',ROOT/'chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003.zip',BA/'step5ba_rebuild_contract.json',ROOT/'chavi_analysis_ds007116_step5ba_clean_rebuild_20261001.zip',ROOT/'chavi_analysis_ds007116_step5bb3r_validation_repair_20261002.zip',BA/'primary_vf_source_rows.csv',BA/'primary_vf_transformed_long.csv',BA/'vonly_reselected_source_rows.csv',BA/'vonly_reselected_transformed_long.csv',BA/'fixed_primary_pair_strict_v_source_rows.csv',BA/'fixed_primary_pair_strict_v_transformed_long.csv',BA/'reference_cohort_manifest.csv',BA/'participant_fold_manifest.csv',BA/'fold_fitting_manifest.csv',BA/'transformation_parameters.csv',ROOT/'chavi_recovery_preflight_correction_20261001'/'qc_pairing_sensitivity_identity_comparison.csv']
fold_rows=rows(BA/'participant_fold_manifest.csv');target_ids=sorted(r['participant_id'] for r in fold_rows)
fold_map={r['participant_id']:int(r['target_fold']) for r in fold_rows}
fit=rows(BA/'fold_fitting_manifest.csv');aux_ids=sorted(fit[0]['auxiliary_identities'].split(';'))
pair_rows=rows(ROOT/'chavi_recovery_preflight_correction_20261001'/'qc_pairing_sensitivity_identity_comparison.csv')
pairs={r['participant_id']:{'primary':r['primary_vf_sessions'].split(';') if r['primary_vf_sessions'] else [],'reselected':r['reselected_strict_v_sessions'].split(';') if r['reselected_strict_v_sessions'] else [],'fixed_strict_v':r['fixed_primary_pair_sessions'].split(';') if r['fixed_primary_pair_sessions'] else []} for r in pair_rows}
spec={'specification_id':'CHAVI_STEP_5B_C2_EXECUTION_V1','status':'FROZEN_BEFORE_EMPIRICAL_OUTCOMES','authorization':'User prompt authorizes bounded primary estimates, P2/P3 bootstrap intervals, descriptive sensitivities, and participant-linked verification records; prohibits diagnostic/individual/predictive/testing/publication claims.',
 'adopted_c1_contract_sha256':sha(C1/'empirical_analysis_contract.json'),'task_order':['letter_nback','face_memory','matrix_reasoning','emotion_recognition','dominant_finger_tapping'],
 'canonical_identity_order':{'rule':'Unicode code-point ascending participant_id, materialized below','targets':target_ids,'auxiliaries':aux_ids},'fold_map':fold_map,
 'ordered_occasion_keys':pairs,'occasion_order_source':'qc_pairing_sensitivity_identity_comparison.csv semicolon order; never inferred from row or lexical order',
 'analysis_slices':[
  {'id':'A_primary_M0_MAD_52','stratum':'primary_vf','model':'M0','scale':'MAD','pair_set':'primary','expected_n':52,'status':'PRIMARY'},
  {'id':'B_primary_M0_SD_52','stratum':'primary_vf','model':'M0','scale':'SD','pair_set':'primary','expected_n':52,'status':'DESCRIPTIVE_SCALE'},
  {'id':'C_primary_supported_M0_MAD_42','stratum':'primary_vf','model':'M0','scale':'MAD','pair_set':'M1_supported_primary','expected_n':42,'status':'DESCRIPTIVE_MATCHED'},
  {'id':'D_primary_supported_M1_MAD_42','stratum':'primary_vf','model':'M1','scale':'MAD','pair_set':'M1_supported_primary','expected_n':42,'status':'DESCRIPTIVE_MATCHED'},
  {'id':'E_fixed_strict_v_M0_MAD_41','stratum':'fixed_primary_pair_strict_v','model':'M0','scale':'MAD','pair_set':'fixed_strict_v','expected_n':41,'status':'DESCRIPTIVE_QC'},
  {'id':'F_reselected_strict_v_M0_MAD_45','stratum':'vonly_reselected','model':'M0','scale':'MAD','pair_set':'reselected','expected_n':45,'status':'DESCRIPTIVE_RESELECTION'}],
 'bootstrap':{'attempts':999,'master_seed':20261003,'namespace':'empirical_v1','generator':'NumPy PCG64DXSM','seed_bytes':'first 128 SHA-256 bits interpreted little-endian','target_stream_label':'shared_target','auxiliary_stream_label':'p3_auxiliary','target_draw_shared_by_P2_P3':True,'quantile':'linear','minimum_valid':950,'tail_fraction':0.025,'minimum_tail_count':20,'no_redraw':True},
 'failure_semantics':{'malformed_input_or_software_exception':'blocks execution','reference_fit_failure':'ordinary P3 endpoint-invalid draw, reason retained','icc_degenerate':'ICC invalid only; mean change and RMS evaluated independently','active_nonfinite_coordinate':'all coordinate-dependent endpoints invalid','failed_draws':'never redrawn'},
 'profile_correlation':{'threshold':'norm(q) <= 64*float64_epsilon*max(norm(z),sqrt(5)*abs(mean(z)),float64_tiny)','summaries':['defined_n','undefined_n','minimum','q25','median','q75','maximum'],'quantile':'linear'},
 'implementation_repairs':['strict yes/no support labels and numeric/null consistency','non-Boolean integer nonnegative multiplicities, exact totals and disjoint roles','external fold-map identity and exact represented fitting keys','valid/invalid counts bounded and summing to attempted','exact frozen occasion and physical-source keys'],
 'schemas':{'replicate_endpoint':'v2 endpoint-specific status; additive clarification to C1 coarse draw template','intervals':'12 rows = 2 methods x 3 endpoints x 2 families; no truth/coverage fields'},
 'dependencies':{'python':platform.python_version(),'numpy':'2.5.2'},'tolerances':{'fit_coordinate_abs':1e-12,'fit_coordinate_rel':1e-10,'independent_endpoint_abs':1e-12,'independent_endpoint_rel':1e-10},
 'inputs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in deps]}
p=OUT/'c2_execution_specification.json';p.write_text(json.dumps(spec,indent=2,sort_keys=True)+'\n',encoding='utf-8');digest=sha(p)
(OUT/'c2_execution_specification.sha256.txt').write_text(digest+'  c2_execution_specification.json\n',encoding='ascii')
(OUT/'authorization_record.json').write_text(json.dumps({'authorization_received':True,'scope':spec['authorization'],'c1_contract_sha256':spec['adopted_c1_contract_sha256'],'c2_specification_sha256':digest,'empirical_execution_may_begin_after_prechecks':True},indent=2,sort_keys=True)+'\n',encoding='utf-8')
with open(OUT/'validation'/'upstream_dependency_hashes_before.csv','w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=['path','sha256']);w.writeheader();w.writerows(spec['inputs'])
print(json.dumps({'status':'FROZEN','specification_sha256':digest,'targets':len(target_ids),'auxiliaries':len(aux_ids)},sort_keys=True))
