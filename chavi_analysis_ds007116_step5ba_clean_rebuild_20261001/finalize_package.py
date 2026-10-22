"""Final acceptance inventory and ZIP packaging."""
import csv, hashlib, json, zipfile
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent;MANIFEST=OUT/"milestone_artifact_manifest.csv";ZIP=ROOT/f"{OUT.name}.zip"
REQUIRED={"CLEAN_REBUILD_AND_VALIDATION_REPORT.md","protocol_adoption_record.json","step5ba_rebuild_contract.json","executable_output_schemas.json","input_artifact_manifest.csv","reference_cohort_manifest.csv","participant_fold_manifest.csv","fold_fitting_manifest.csv","primary_vf_source_rows.csv","vonly_reselected_source_rows.csv","fixed_primary_pair_strict_v_source_rows.csv","transformation_parameters.csv","transformed_task_observations_long.csv","transformed_profiles_wide.csv","primary_vf_transformed_long.csv","primary_vf_transformed_wide.csv","vonly_reselected_transformed_long.csv","vonly_reselected_transformed_wide.csv","fixed_primary_pair_strict_v_transformed_long.csv","fixed_primary_pair_strict_v_transformed_wide.csv","support_scale_and_fallback_audit.csv","denominator_and_identity_reconciliation.csv","independent_parameter_crosscheck.csv","independent_coordinate_crosscheck.csv","independent_expected_parameters.csv","independent_expected_coordinates_long.csv","validator_independence_review.md","validation_results.json","test_execution_report.md","historical_artifact_before_after_hashes.csv","claims_register.csv","provenance.json","environment_requirements.txt","README_REPRODUCE.md","prepare_contract.py","run_clean_rebuild.py","independent_validator.py","validate_schemas.py","test_clean_rebuild.py","orchestrate_rebuild.py","make_reports.py","finalize_package.py","fresh_process_hash_comparison.csv","orchestration_results.json","production_results.json","contract_sha256.txt"}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    available={p.name for p in OUT.iterdir() if p.is_file()};missing=REQUIRED-available
    if missing:raise AssertionError(f"missing: {sorted(missing)}")
    for p in OUT.glob("*.json"):json.loads(p.read_text(encoding="utf-8"),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(f"invalid constant {x}")))
    counts={}
    for p in OUT.glob("*.csv"):
        if p==MANIFEST:continue
        with p.open("r",encoding="utf-8-sig",newline="") as h:counts[p.name]=len(list(csv.DictReader(h)))
    expected={"reference_cohort_manifest.csv":545,"primary_vf_source_rows.csv":520,"vonly_reselected_source_rows.csv":450,"fixed_primary_pair_strict_v_source_rows.csv":410,"transformation_parameters.csv":100,"transformed_task_observations_long.csv":5520,"transformed_profiles_wide.csv":1104,"primary_vf_transformed_long.csv":2080,"primary_vf_transformed_wide.csv":416,"vonly_reselected_transformed_long.csv":1800,"vonly_reselected_transformed_wide.csv":360,"fixed_primary_pair_strict_v_transformed_long.csv":1640,"fixed_primary_pair_strict_v_transformed_wide.csv":328,"independent_parameter_crosscheck.csv":100,"independent_coordinate_crosscheck.csv":5520,"independent_expected_parameters.csv":100,"independent_expected_coordinates_long.csv":5520}
    expected.update({"participant_fold_manifest.csv":52,"fold_fitting_manifest.csv":5})
    for n,c in expected.items():
        if counts.get(n)!=c:raise AssertionError(f"{n}: {counts.get(n)} != {c}")
    validation=json.loads((OUT/"validation_results.json").read_text(encoding="utf-8"))
    if not validation["independent_validation_passed"]:raise AssertionError("validation failed")
    if any(r["validation_pass"]!="yes" for n in ["independent_parameter_crosscheck.csv","independent_coordinate_crosscheck.csv"] for r in csv.DictReader((OUT/n).open("r",encoding="utf-8-sig",newline=""))):raise AssertionError("crosscheck row failed")
    hist=list(csv.DictReader((OUT/"historical_artifact_before_after_hashes.csv").open("r",encoding="utf-8-sig",newline="")))
    fresh=list(csv.DictReader((OUT/"fresh_process_hash_comparison.csv").open("r",encoding="utf-8-sig",newline="")))
    if any(r["unchanged"]!="yes" for r in hist) or any(r["match"]!="yes" for r in fresh):raise AssertionError("preservation/determinism failure")
    files=sorted(p for p in OUT.iterdir() if p.is_file() and p!=MANIFEST and p.suffix!=".pyc")
    entries=[{"relative_path":p.name,"size_bytes":p.stat().st_size,"sha256":sha(p),"csv_data_rows":counts.get(p.name,""),"included_in_zip":"yes"} for p in files]
    with MANIFEST.open("w",encoding="utf-8",newline="") as h:w=csv.DictWriter(h,fieldnames=list(entries[0]),lineterminator="\n");w.writeheader();w.writerows(entries)
    package=sorted(p for p in OUT.iterdir() if p.is_file() and p.suffix!=".pyc")
    with zipfile.ZipFile(ZIP,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in package:z.write(p,arcname=f"{OUT.name}/{p.name}")
    print(json.dumps({"manifest_members":len(entries),"zip_entries":len(package),"zip_path":str(ZIP),"zip_bytes":ZIP.stat().st_size,"zip_sha256":sha(ZIP)},indent=2))
if __name__=="__main__":main()
