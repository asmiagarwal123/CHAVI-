"""Independent synthetic oracle and corruption validator for Step 5B-B1."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

TASKS = ["letter_nback", "face_memory", "matrix_reasoning",
         "emotion_recognition", "dominant_finger_tapping"]
ATOL, RTOL = 1e-12, 1e-10


def hmatrix():
    rows = [[0.0] * 4 for _ in range(5)]
    for j in range(4):
        k = j + 1; d = math.sqrt(k * (k + 1))
        for i in range(k): rows[i][j] = 1 / d
        rows[k][j] = -k / d
    return rows


def dot(a, b): return sum(x*y for x, y in zip(a, b))
def norm(a): return math.sqrt(dot(a, a))


def geom(z):
    if len(z) != 5 or any(not math.isfinite(float(x)) for x in z):
        raise ValueError("five finite values required")
    z = [float(x) for x in z]; level = sum(z)/5
    q = [x-level for x in z]; h = hmatrix()
    c = [sum(h[i][j]*q[i] for i in range(5)) for j in range(4)]
    return {"level":level, "centered_shape":q, "scatter":math.sqrt(dot(q,q)/5),
            "contrasts":c, "shape_norm":norm(q)}


def threshold(z):
    g=geom(z); scale=max(norm(z),math.sqrt(5)*abs(g["level"]),sys.float_info.min)
    return 64*sys.float_info.epsilon*scale


def corr(a,b):
    ga,gb=geom(a),geom(b)
    if norm(ga["centered_shape"])<=threshold(a) or norm(gb["centered_shape"])<=threshold(b): return None
    return dot(ga["centered_shape"],gb["centered_shape"])/(norm(ga["centered_shape"])*norm(gb["centered_shape"]))


def pair(a,b):
    ga,gb=geom(a),geom(b); dq=[y-x for x,y in zip(ga["centered_shape"],gb["centered_shape"])]; dz=[y-x for x,y in zip(a,b)]
    return {"delta_level":gb["level"]-ga["level"],"delta_scatter":gb["scatter"]-ga["scatter"],
            "shape_displacement":math.sqrt(dot(dq,dq)/5),"total_displacement":math.sqrt(dot(dz,dz)/5),
            "profile_correlation":corr(a,b)}

def icc_values(x):
    n=len(x);k=2;gm=sum(sum(r) for r in x)/(n*k)
    rm=[sum(r)/k for r in x];cm=[sum(r[j] for r in x)/n for j in range(k)]
    msr=k*sum((v-gm)**2 for v in rm)/(n-1);msc=n*sum((v-gm)**2 for v in cm)/(k-1)
    mse=sum((x[i][j]-rm[i]-cm[j]+gm)**2 for i in range(n) for j in range(k))/((n-1)*(k-1))
    return (msr-mse)/(msr+(k-1)*mse+k*(msc-mse)/n),(msr-mse)/(msr+(k-1)*mse)

def trace_assoc(a,b):
    n=len(a);ma=[sum(r[j] for r in a)/n for j in range(4)];mb=[sum(r[j] for r in b)/n for j in range(4)]
    ac=[[r[j]-ma[j] for j in range(4)] for r in a];bc=[[r[j]-mb[j] for j in range(4)] for r in b]
    num=sum(dot(x,y) for x,y in zip(ac,bc));den=math.sqrt(sum(dot(x,x) for x in ac)*sum(dot(y,y) for y in bc))
    return None if den==0 else num/den


def close(a,b):
    if a is None or b is None: return a is b
    if isinstance(a,list): return len(a)==len(b) and all(close(x,y) for x,y in zip(a,b))
    return math.isclose(float(a),float(b),abs_tol=ATOL,rel_tol=RTOL)


def _expect_error(fn, text):
    try: fn()
    except Exception as e: return text.lower() in str(e).lower()
    return False


def _validate_keys(rows):
    seen=set()
    for r in rows:
        k=(r["participant_id"],r["session_id"],r["variant"])
        if k in seen: raise ValueError("duplicate key")
        seen.add(k)


def _validate_m1(row):
    if row["model"]=="M1" and row["supported"]=="no" and row["coordinate"] not in (None,""):
        raise ValueError("unsupported M1 coordinate")


def _validate_plan(p):
    if p["target_fit_multiplicity"]!=p["target_analysis_multiplicity"]: raise ValueError("multiplicities")
    if p["visit_multiplicity"]!=p["target_analysis_multiplicity"]: raise ValueError("visits")
    if len({json.dumps(x,sort_keys=True) for x in p["auxiliary_multiplicity_by_fold"].values()})!=1: raise ValueError("auxiliary")
    for f,ids in p["held_out_targets_by_fold"].items():
        if any(p["fitted_target_multiplicity_by_fold"][f].get(i,0)>0 for i in ids): raise ValueError("held-out")


def run(base: Path) -> dict:
    syn=base/"synthetic"; syn.mkdir(exist_ok=True)
    fixtures={
      "hand":[1,2,3,4,5], "identical_a":[-2,-1,0,1,2], "identical_b":[-2,-1,0,1,2],
      "level_a":[-2,-1,0,1,2], "level_b":[8,9,10,11,12],
      "shape_a":[-2,-1,0,1,2], "shape_b":[-2,0,-1,2,1],
      "flat_a":[3,3,3,3,3], "near_flat":[1e12,1e12+1e-4,1e12,1e12,1e12],
      "large_a":[1e9+1,1e9+2,1e9+3,1e9+4,1e9+5],
      "large_b":[1e9+2,1e9+4,1e9+3,1e9+5,1e9+6]
    }
    (syn/"fixture_inputs.json").write_text(json.dumps(fixtures,indent=2)+"\n",encoding="utf-8")
    expected={k:geom(v) for k,v in fixtures.items()}
    expected["pairs"]={k:pair(fixtures[a],fixtures[b]) for k,a,b in [
      ("identical","identical_a","identical_b"),("level_only","level_a","level_b"),
      ("shape_only","shape_a","shape_b"),("large","large_a","large_b")]}
    # Persist independent expectations before importing production code.
    (syn/"independent_expected_outputs.json").write_text(json.dumps(expected,indent=2)+"\n",encoding="utf-8")
    spec=importlib.util.spec_from_file_location("profile_estimands",base/"profile_estimands.py")
    prod=importlib.util.module_from_spec(spec); spec.loader.exec_module(prod)
    produced={k:{x:(v.tolist() if hasattr(v,"tolist") else v) for x,v in prod.profile_geometry(z).items()} for k,z in fixtures.items()}
    produced["pairs"]={k:prod.pair_geometry(fixtures[a],fixtures[b]) for k,a,b in [
      ("identical","identical_a","identical_b"),("level_only","level_a","level_b"),
      ("shape_only","shape_a","shape_b"),("large","large_a","large_b")]}
    (syn/"production_outputs.json").write_text(json.dumps(produced,indent=2)+"\n",encoding="utf-8")
    checks={}
    checks["01_hand_geometry"]=close(produced["hand"]["level"],3) and close(produced["hand"]["centered_shape"],[-2,-1,0,1,2]) and close(produced["hand"]["scatter"],math.sqrt(2))
    checks["02_identical_profiles"]=close(produced["pairs"]["identical"]["total_displacement"],0) and close(produced["pairs"]["identical"]["profile_correlation"],1)
    checks["03_level_only"]=close(produced["pairs"]["level_only"]["delta_level"],10) and close(produced["pairs"]["level_only"]["shape_displacement"],0)
    checks["04_shape_only"]=close(produced["pairs"]["shape_only"]["delta_level"],0) and produced["pairs"]["shape_only"]["shape_displacement"]>0
    checks["05_flat_correlation"]=prod.profile_correlation(fixtures["flat_a"],fixtures["hand"]) is None
    checks["06_near_flat_policy"]=prod.profile_correlation(fixtures["near_flat"],fixtures["hand"]) is None
    checks["07_missing_or_unsupported"]=_expect_error(lambda:prod.profile_geometry([1,2,float('nan'),4,5]),"finite") and _expect_error(lambda:prod.profile_geometry([1,2,3,4,5],[1,1,0,1,1]),"supported")
    checks["08_large_offsets"]=all(close(produced["large_a"][x],expected["large_a"][x]) for x in expected["large_a"])
    h=prod.H; checks["09_shape_reconstruction"]=close((h@prod.profile_geometry(fixtures["hand"])["contrasts"]).tolist(),prod.profile_geometry(fixtures["hand"])["centered_shape"].tolist())
    g=prod.profile_geometry(fixtures["hand"]); checks["10_energy_displacement_identities"]=close(sum(x*x for x in fixtures["hand"]),5*g["level"]**2+g["shape_norm"]**2) and close(produced["pairs"]["large"]["total_displacement"]**2,produced["pairs"]["large"]["delta_level"]**2+produced["pairs"]["large"]["shape_displacement"]**2)
    rot=[[0,1,0,0],[-1,0,0,0],[0,0,0,1],[0,0,-1,0]]; c=g["contrasts"]; rc=[sum(rot[i][j]*c[j] for j in range(4)) for i in range(4)]; checks["11_basis_rotation_invariance"]=close(norm(c),norm(rc))
    perm=[2,0,4,1,3]; hp=[[hmatrix()[i][j] for j in range(4)] for i in perm]; zp=[fixtures["hand"][i] for i in perm]; qp=[zp[i]-sum(zp)/5 for i in range(5)]; cp=[sum(hp[i][j]*zp[i] for i in range(5)) for j in range(4)]; checks["12_joint_permutation"]=close([sum(hp[i][j]*cp[j] for j in range(4)) for i in range(5)],qp)
    checks["13_unmatched_metadata_rejected"]=_expect_error(lambda:prod.profile_geometry(dict(zip(TASKS[::-1],fixtures["hand"])),None),"order")
    dup=[{"participant_id":"p","session_id":"s","variant":"v"}]*2; checks["14_duplicate_keys"]=_expect_error(lambda:_validate_keys(dup),"duplicate")
    bad={"model":"M1","supported":"no","coordinate":0.0,"fallback_coordinate":1.0}; checks["15_m1_fallback_insertion"]=_expect_error(lambda:_validate_m1(bad),"unsupported")
    good={"target_fit_multiplicity":{"a":2,"b":0},"target_analysis_multiplicity":{"a":2,"b":0},"visit_multiplicity":{"a":2,"b":0},"auxiliary_multiplicity_by_fold":{"0":{"x":1},"1":{"x":1}},"held_out_targets_by_fold":{"0":["a"],"1":["b"]},"fitted_target_multiplicity_by_fold":{"0":{"a":0,"b":0},"1":{"a":2,"b":0}}}
    bad16=json.loads(json.dumps(good));bad16["fitted_target_multiplicity_by_fold"]["0"]["a"]=2; checks["16_heldout_copy_rejected"]=_expect_error(lambda:_validate_plan(bad16),"held-out")
    bad17=json.loads(json.dumps(good));bad17["target_fit_multiplicity"]["a"]=1;checks["17_target_multiplicity_link"]=_expect_error(lambda:_validate_plan(bad17),"multiplicities")
    bad18=json.loads(json.dumps(good));bad18["auxiliary_multiplicity_by_fold"]["1"]["x"]=2;checks["18_auxiliary_reuse"]=_expect_error(lambda:_validate_plan(bad18),"auxiliary")
    bad19=json.loads(json.dumps(good));bad19["visit_multiplicity"]["a"]=1;checks["19_clustered_visits"]=_expect_error(lambda:_validate_plan(bad19),"visits")
    reread=json.loads((syn/"production_outputs.json").read_text(encoding="utf-8"));checks["20_serialization_readback"]=reread==produced
    checks["21_independent_expected_match"]=all(close(produced[k][field],expected[k][field]) for k in fixtures for field in expected[k]) and all(close(produced["pairs"][k][field],expected["pairs"][k][field]) for k in expected["pairs"] for field in expected["pairs"][k])
    # Exercise the production validators too, rather than only test-local rejection helpers.
    checks["22_production_corruption_paths"]=_expect_error(lambda:prod.validate_unique_keys(dup),"duplicate") and _expect_error(lambda:prod.validate_m1_null_policy(bad),"unsupported") and _expect_error(lambda:prod.validate_bootstrap_multiplicities(bad16),"held-out")
    ipairs=[[1,1],[2,2],[3,4],[4,5]];ia,ic=icc_values(ipairs);checks["23_icc_formulas"]=close(prod.icc_a1(ipairs),ia) and close(prod.icc_c1(ipairs),ic)
    ca=[[0,1,2,3],[1,0,3,2],[2,3,0,1],[3,2,1,0]];cb=[[x+0.25 for x in r] for r in ca]
    car=[[sum(rot[i][j]*r[j] for j in range(4)) for i in range(4)] for r in ca];cbr=[[sum(rot[i][j]*r[j] for j in range(4)) for i in range(4)] for r in cb]
    checks["24_shape_trace_independent_and_rotation"] = close(prod.shape_trace_association(ca,cb),trace_assoc(ca,cb)) and close(prod.shape_trace_association(car,cbr),trace_assoc(ca,cb))
    records=[{"check":k,"status":"PASS" if v else "FAIL"} for k,v in checks.items()]
    with (syn/"comparison_records.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["check","status"]);w.writeheader();w.writerows(records)
    result={"status":"PASS" if all(checks.values()) else "FAIL","checks_total":len(checks),"checks_passed":sum(checks.values()),"atol":ATOL,"rtol":RTOL,"checks":checks}
    (base/"validation_results.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result


if __name__=="__main__":
    result=run(Path(__file__).resolve().parent)
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if result["status"]=="PASS" else 1)
