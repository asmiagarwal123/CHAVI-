"""Freeze deterministic full-replicate audit records before independent calculation."""
from pathlib import Path
import json,hashlib,datetime
BASE=Path(__file__).resolve().parent
cases=[]
for sid in ('S1','S2','S3','S4','S5','S6'):
    cases.append({'stage':'corrected_pilot','scenario_id':sid,'outer_id':0,'methods':['P1_oracle_conditional','P2_fixed_transform','P3_joint_unstratified','P4_joint_fold_stratified'],'sampling_role':'representative','reason':'fixed first outer; covers every scenario/method/scale/endpoint'})
for sid,outer in [('S1',0),('S2',14),('S3',21),('S4',19),('S5',5),('S6',15)]:
    if outer:
        cases.append({'stage':'corrected_pilot','scenario_id':sid,'outer_id':outer,'methods':['P3_joint_unstratified'],'sampling_role':'targeted','reason':'lowest outer with an unrepresented-fold draw'})
for sid,outer in [('S1',40),('S5',2)]:
    cases.append({'stage':'confirmatory','scenario_id':sid,'outer_id':outer,'methods':['P3_joint_unstratified'],'sampling_role':'targeted','reason':'lowest confirmatory outer with an unrepresented-fold draw'})
cases += [
 {'stage':'confirmatory','scenario_id':'S5','outer_id':1000,'methods':['P3_joint_unstratified'],'sampling_role':'targeted','reason':'original metadata has exactly 950 valid MAD draws; eligibility boundary'},
 {'stage':'corrected_pilot','scenario_id':'S5','outer_id':3,'methods':['P3_joint_unstratified','P4_joint_fold_stratified'],'sampling_role':'targeted','reason':'unsupported-fit-rich MAD record below eligibility threshold'}]
obj={'specification_id':'B3R-NUMERICAL-AUDIT-v1','frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selection_basis':'deterministic identifiers and pre-repair structural/failure metadata; no repaired interval outcome used','attempts_per_method_scale':999,'scales':['MAD','SD'],'endpoints':['level_icc_a1','mean_level_change','rms_shape_displacement'],'absolute_tolerance':1e-10,'relative_tolerance':1e-10,'nan_policy':'both invalid only passes when failure category agrees and independent rule says undefined','cases':cases}
raw=(json.dumps(obj,indent=2)+'\n').encode();(BASE/'numerical_audit_specification.json').write_bytes(raw);print(hashlib.sha256(raw).hexdigest(),len(cases))
