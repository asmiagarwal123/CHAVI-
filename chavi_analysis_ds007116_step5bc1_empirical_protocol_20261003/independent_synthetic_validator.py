"""Independent expected-value and corruption validator for Step 5B-C1.

Expected endpoint values are derived below without calling production helpers.
The production module is imported only after those expectations are frozen.
"""
from __future__ import annotations
import copy, json, math, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

def independent_endpoints(z, weights=None):
    z = np.asarray(z, float); w = np.ones(len(z), dtype=int) if weights is None else np.asarray(weights, int)
    expanded = np.repeat(z[w > 0], w[w > 0], axis=0); n = len(expanded); k = 2
    levels = np.sum(expanded, axis=2) / 5.0
    centered = expanded - levels[:, :, None]
    delta = levels[:, 1] - levels[:, 0]
    rms = math.sqrt(float(np.sum((centered[:, 1] - centered[:, 0]) ** 2) / (5.0 * n)))
    grand = float(np.sum(levels) / (n * k)); row = np.sum(levels, axis=1) / k; col = np.sum(levels, axis=0) / n
    msr = k * float(np.sum((row - grand) ** 2)) / (n - 1)
    msc = n * float(np.sum((col - grand) ** 2)) / (k - 1)
    residual = levels - row[:, None] - col[None, :] + grand
    mse = float(np.sum(residual ** 2)) / ((n - 1) * (k - 1))
    denominator = msr + (k - 1) * mse + k * (msc - mse) / n
    icc = None if denominator == 0 else (msr - mse) / denominator
    return {"level_icc_a1": icc, "mean_level_change": float(np.sum(delta) / n), "rms_shape_displacement": rms, "frequency_denominator": n}

def assert_close(actual, expected, tol=1e-12):
    if actual is None or expected is None:
        assert actual is expected
    else:
        assert math.isclose(actual, expected, rel_tol=1e-10, abs_tol=tol), (actual, expected)

def expect_failure(name, fn, records):
    try: fn()
    except Exception as e:
        records.append({"test": name, "status": "PASS", "evidence": type(e).__name__ + ": " + str(e)}); return
    raise AssertionError(name + " did not fail")

def coordinate_rows(z, model="M0", scale="MAD", supported=True):
    rows=[]
    for i in range(len(z)):
        for v, session in enumerate(("ses-a", "ses-b")):
            for j, task in enumerate(("letter_nback","face_memory","matrix_reasoning","emotion_recognition","dominant_finger_tapping")):
                rows.append({"participant_id":f"T{i}","session_id":session,"task_key":task,"model":model,"scale_method":scale,
                  "analytical_stratum":"synthetic","reference_design":"B_target_plus_auxiliary","coordinate":str(z[i,v,j]) if supported else "",
                  "supported":"yes" if supported else "no"})
    return rows

def run():
    expected_cases = {}
    base = np.array([
      [[0,1,2,3,4],[2,3,4,5,6]],
      [[1,1,1,1,1],[1,2,1,0,1]],
      [[4,3,2,1,0],[4,3,2,1,0]],
      [[0,2,0,2,0],[1,1,1,1,1]],
    ], float)
    expected_cases["mixed"] = independent_endpoints(base)
    expected_cases["unequal_multiplicity"] = independent_endpoints(base, [2,0,3,1])
    level_shift = np.array([[[0,1,2,3,4],[7,8,9,10,11]], [[4,3,2,1,0],[11,10,9,8,7]]], float)
    expected_cases["common_level_shift"] = independent_endpoints(level_shift)
    shape_only = np.array([[[0,0,0,0,0],[2,-2,0,0,0]], [[1,1,1,1,1],[0,1,2,1,1]]], float)
    expected_cases["shape_only"] = independent_endpoints(shape_only)
    negative = np.array([[[0]*5,[3]*5], [[1]*5,[2]*5], [[2]*5,[1]*5], [[3]*5,[0]*5]], float)
    expected_cases["negative_icc"] = independent_endpoints(negative)
    import analysis_interface as prod
    records=[]
    for name, data, weights in [
      ("mixed",base,None),("unequal_multiplicity",base,[2,0,3,1]),("common_level_shift",level_shift,None),
      ("shape_only",shape_only,None),("negative_icc",negative,None)]:
        actual=prod.endpoints(data, weights); expected=expected_cases[name]
        for key in expected: assert_close(actual[key], expected[key])
        records.append({"test":name,"status":"PASS","evidence":actual})
    assert expected_cases["common_level_shift"]["rms_shape_displacement"] == 0.0
    assert expected_cases["shape_only"]["mean_level_change"] == 0.0
    assert expected_cases["negative_icc"]["level_icc_a1"] < 0
    const=np.ones((3,2,5)); assert prod.endpoints(const)["level_icc_a1"] is None
    records.append({"test":"constant_profiles_degenerate_icc","status":"PASS","evidence":"None retained"})
    active_bad=base.copy();active_bad[0,0,0]=np.nan
    expect_failure("active_unsupported_values",lambda:prod.endpoints(active_bad),records)
    zero_nan=base.copy();zero_nan[1]=np.nan; got=prod.endpoints(zero_nan,[1,0,1,1]); assert got["frequency_denominator"]==3
    records.append({"test":"zero_weight_nan","status":"PASS","evidence":"inactive NaNs excluded before reduction"})
    assert_close(prod.weighted_median([1,9,100],[2,1,0]), np.median([1,1,9])); assert_close(prod.weighted_sd([1,9,100],[2,1,0]),np.std([1,1,9],ddof=1))
    records.append({"test":"frequency_weight_equivalence","status":"PASS","evidence":"median and sample SD match explicit expansion"})
    for vals,label in [([1,1,1],[1,1,1]),([1,1+1e-16,1],[1,1,1])]:
        scale=prod.weighted_sd(vals,label); expect_failure("zero_or_near_zero_scale_"+str(len(records)),lambda s=scale,v=vals,w=label:prod.validate_scale(v,w,s),records)
    y=[1,4,5,8]; ages=[10,11,12,13]; weights=[1,2,1,0]
    m1=prod.fit_task_reference(y,ages,weights,"M1","SD")
    expanded_y=np.repeat(np.array(y,float),weights);expanded_a=np.repeat(np.array(ages,float),weights)
    expected_slope=float(np.cov(expanded_a,expanded_y,ddof=0)[0,1]/np.var(expanded_a))
    assert_close(m1["slope"],expected_slope)
    value,supported,reason=prod.transform_task(9,14,m1);assert value is None and not supported and reason=="outside_inclusive_training_age_support"
    records.append({"test":"m1_weighted_refit_and_no_fallback","status":"PASS","evidence":{"slope":m1["slope"],"outside_support":reason}})
    rows=coordinate_rows(base); summary=prod.validate_coordinate_rows(list(reversed(rows)),"M0","MAD","synthetic")
    assert summary["participants"]==4; records.append({"test":"shuffled_rows","status":"PASS","evidence":"keyed reconstruction accepted"})
    dup=rows+[dict(rows[0])]; expect_failure("duplicate_coordinate_record",lambda:prod.validate_coordinate_rows(dup,"M0","MAD","synthetic"),records)
    expect_failure("incorrect_task_order",lambda:prod.validate_coordinate_rows(rows,"M0","MAD","synthetic",tuple(reversed(prod.TASK_ORDER))),records)
    mixed=copy.deepcopy(rows);mixed[0]["scale_method"]="SD";expect_failure("mixed_scale_rows",lambda:prod.validate_coordinate_rows(mixed,"M0","MAD","synthetic"),records)
    mixed=copy.deepcopy(rows);mixed[0]["model"]="M1";expect_failure("mixed_model_rows",lambda:prod.validate_coordinate_rows(mixed,"M0","MAD","synthetic"),records)
    fallback=coordinate_rows(base,"M1");fallback[0]["supported"]="no";expect_failure("fallback_contamination",lambda:prod.validate_coordinate_rows(fallback,"M1","MAD","synthetic"),records)
    swapped=copy.deepcopy(rows);swapped[0]["session_id"]="ses-c";expect_failure("swapped_occasion_key",lambda:prod.validate_coordinate_rows(swapped,"M0","MAD","synthetic"),records)
    source=[{"participant_id":r["participant_id"],"session_id":r["session_id"],"task_key":r["task_key"]} for r in rows]
    expect_failure("duplicate_source_record",lambda:prod.validate_source_rows(source+[dict(source[0])]),records)
    tids=["T0","T1","T2","T3"];aids=["A0","A1","A2"];folds={"T0":0,"T1":0,"T2":1,"T3":2}
    plan=prod.make_resampling_plan(tids,aids,folds,["T0","T0","T2","T3"],["A0","A0","A2"]);prod.validate_resampling_plan(plan,tids,aids)
    assert plan["represented_folds"]==[0,1,2];records.append({"test":"valid_linked_resampling_unequal_multiplicity","status":"PASS","evidence":plan["represented_folds"]})
    absent=prod.make_resampling_plan(tids,aids,folds,["T0"]*4,["A0"]*3);prod.validate_resampling_plan(absent,tids,aids);assert absent["represented_folds"]==[0]
    records.append({"test":"absent_folds_not_fit","status":"PASS","evidence":[0]})
    bad=copy.deepcopy(plan);bad["visit_multiplicity"]["T1"]=1;expect_failure("independent_visit_resampling",lambda:prod.validate_resampling_plan(bad,tids,aids),records)
    bad=copy.deepcopy(plan);bad["target_fit_by_fold"]["0"]["T0"]=1;expect_failure("held_out_leakage",lambda:prod.validate_resampling_plan(bad,tids,aids),records)
    bad=copy.deepcopy(plan);bad["auxiliary_fit_by_fold"]["1"]["A1"]=1;expect_failure("fold_specific_auxiliary_draw",lambda:prod.validate_resampling_plan(bad,tids,aids),records)
    assert prod.empirical_interval_gate(999,950,True)==(True,"available")
    assert prod.empirical_interval_gate(999,949,True)[0] is False
    records.append({"test":"empirical_gate_no_truth_argument","status":"PASS","evidence":"999/950 plus tail and point gates only"})
    try: prod.empirical_interval_gate(999,950,True,True)
    except TypeError: records.append({"test":"simulation_truth_gate_reuse_rejected","status":"PASS","evidence":"truth argument unsupported"})
    else: raise AssertionError("truth gate accidentally accepted")
    out={"status":"PASS","tests_total":len(records),"tests_passed":len(records),"production_module":str(ROOT/'analysis_interface.py'),"independent_expected_path":True,"records":records}
    (ROOT/"synthetic_test_results.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({k:out[k] for k in ("status","tests_total","tests_passed")},sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(run())
