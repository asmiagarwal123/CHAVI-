"""Executable schema and long/wide round-trip checks."""
import csv, json, math
from pathlib import Path

OUT=Path(__file__).resolve().parent
TASKS=["letter_nback","face_memory","matrix_reasoning","emotion_recognition","dominant_finger_tapping"]

def rows(name):
    with (OUT/name).open("r",encoding="utf-8-sig",newline="") as h:return list(csv.DictReader(h))

def main():
    schema=json.loads((OUT/"executable_output_schemas.json").read_text(encoding="utf-8"))["tables"]
    params=rows("transformation_parameters.csv"); long=rows("transformed_task_observations_long.csv"); wide=rows("transformed_profiles_wide.csv")
    data={"parameters":params,"long_coordinates":long,"wide_coordinates":wide}
    for name,rr in data.items():
        spec=schema[name]
        if len(rr)!=spec["expected_rows"]:raise AssertionError(f"{name} row count")
        if set(spec["required_columns"] if "required_columns" in spec else rr[0])-set(rr[0]):raise AssertionError(f"{name} required columns")
        keys=[tuple(r[x] for x in spec["unique_key"]) for r in rr]
        if len(keys)!=len(set(keys)):raise AssertionError(f"{name} duplicate keys")
    coord_cols=[c for c in wide[0] if c.endswith("_coordinate") and not c.endswith("fallback_coordinate")]
    if coord_cols!=[f"{t}_coordinate" for t in TASKS]:raise AssertionError(f"wide coordinate columns: {coord_cols}")
    lookup={(r["participant_id"],r["analytical_stratum"],r["session_id"],r["task_key"],r["model"],r["scale_method"]):r for r in long}
    checked=0
    for w in wide:
        for t in TASKS:
            r=lookup[(w["participant_id"],w["analytical_stratum"],w["session_id"],t,w["model"],w["scale_method"])]
            for suffix in schema["wide_coordinates"]["task_specific_suffixes"]:
                if w[f"{t}_{suffix}"]!=r[suffix]:raise AssertionError(f"roundtrip {t} {suffix}")
            checked+=1
    for r in long:
        if (r["supported"]=="yes")!=(r["coordinate"]!=""):raise AssertionError("support/null mismatch")
        if r["model"]=="M0" and (r["age_support_status"]!="not_applicable" or r["extrapolation"]!="false"):raise AssertionError("M0 support contamination")
        for field in ("coordinate","prediction","residual","fallback_coordinate"):
            if r[field] and not math.isfinite(float(r[field])):raise AssertionError("nonfinite CSV numeric")
    print(json.dumps({"schema_validation_passed":True,"parameter_rows":len(params),"long_rows":len(long),"wide_rows":len(wide),"roundtrip_task_records":checked},indent=2))

if __name__=="__main__":main()
