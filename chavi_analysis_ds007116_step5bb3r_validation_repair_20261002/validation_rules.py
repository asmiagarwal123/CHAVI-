"""Executable identity, interval, and structural-result validators."""
import math
from simulation_core import validate_multiplicity_plan
def validate_plan(plan): return validate_multiplicity_plan(plan)
def validate_support_result(supported_flags,values):
    if len(supported_flags)!=len(values): raise ValueError('support/value length mismatch')
    for flag,value in zip(supported_flags,values):
        if flag not in ('yes','no',True,False): raise ValueError('unknown support flag')
        supported=flag in ('yes',True)
        if not supported and value is not None: raise ValueError('unsupported coordinate assigned numerical value')
    return True
def validate_basic_interval(point,q025,q975,lower,upper,tol=1e-12):
    if not all(math.isfinite(x) for x in (point,q025,q975,lower,upper)): raise ValueError('nonfinite basic interval input')
    if abs(lower-(2*point-q975))>tol or abs(upper-(2*point-q025))>tol: raise ValueError('basic interval centered on wrong point estimate')
    return True
def validate_eligibility(attempted,valid,point_defined,truth_defined,available):
    if attempted==499 and available: raise ValueError('499 draws cannot satisfy the 20-per-tail B3-R rule')
    n_gate=valid>=950; tail_gate=math.floor(.025*valid)>=20; expected=attempted==999 and n_gate and tail_gate and point_defined and truth_defined
    if available!=expected: raise ValueError('interval availability inconsistent with frozen eligibility rule')
    return True
def validate_structural_coverage(scenario,scale,truth_defined,coverage):
    if scenario=='S6' and scale=='MAD' and (truth_defined or coverage is not None): raise ValueError('structural S6/MAD target assigned numerical coverage')
    return True
