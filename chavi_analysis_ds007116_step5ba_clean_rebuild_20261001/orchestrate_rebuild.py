"""One-command end-to-end orchestration for the clean rebuild."""
import csv, hashlib, json, os, subprocess, sys
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent
def sha(p):
    d=hashlib.sha256()
    with Path(p).open("rb") as h:
        for b in iter(lambda:h.read(1024*1024),b""):d.update(b)
    return d.hexdigest()
def write(path,rows,fields=None):
    fields=fields or list(rows[0])
    with Path(path).open("w",encoding="utf-8",newline="") as h:w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
def protected():
    paths=[]
    for d in ROOT.iterdir():
        if d.is_dir() and d.name.startswith("chavi_") and d.resolve()!=OUT.resolve():paths.extend(p for p in d.rglob("*") if p.is_file())
    paths.extend(p for p in ROOT.iterdir() if p.is_file())
    paths += [ROOT/"ds007116/participants.tsv",ROOT/"ds007116/dataset_description.json"]
    paths += list((ROOT/"ds007116/phenotype").glob("*.json"))
    return sorted(set(p.resolve() for p in paths if p.exists() and p.resolve()!= (ROOT/f"{OUT.name}.zip").resolve()))
def snapshot(paths):return {p.relative_to(ROOT).as_posix():(p.stat().st_size,sha(p)) for p in paths}
def run(script,*args):
    cmd=[sys.executable,str(OUT/script),*args];p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
    rec={"command":" ".join(cmd),"exit_code":p.returncode,"stdout":p.stdout[-12000:],"stderr":p.stderr[-12000:]}
    if p.returncode:raise RuntimeError(json.dumps(rec,indent=2))
    return rec
def scientific_names():
    return ["protocol_adoption_record.json","step5ba_rebuild_contract.json","executable_output_schemas.json","input_artifact_manifest.csv","reference_cohort_manifest.csv","participant_fold_manifest.csv","fold_fitting_manifest.csv","primary_vf_source_rows.csv","vonly_reselected_source_rows.csv","fixed_primary_pair_strict_v_source_rows.csv","transformation_parameters.csv","transformed_task_observations_long.csv","transformed_profiles_wide.csv","primary_vf_transformed_long.csv","primary_vf_transformed_wide.csv","vonly_reselected_transformed_long.csv","vonly_reselected_transformed_wide.csv","fixed_primary_pair_strict_v_transformed_long.csv","fixed_primary_pair_strict_v_transformed_wide.csv","support_scale_and_fallback_audit.csv","denominator_and_identity_reconciliation.csv","independent_expected_parameters.csv","independent_expected_coordinates_long.csv","independent_parameter_crosscheck.csv","independent_coordinate_crosscheck.csv","validation_results.json","production_results.json","claims_register.csv","contract_sha256.txt"]
def main():
    pp=protected();before=snapshot(pp);commands=[]
    commands += [run("prepare_contract.py"),run("run_clean_rebuild.py"),run("independent_validator.py"),run("validate_schemas.py")]
    commands.append(run("test_clean_rebuild.py"))
    first={n:sha(OUT/n) for n in scientific_names()}
    # Every scientific calculation is rerun in a new interpreter process.
    commands += [run("prepare_contract.py"),run("run_clean_rebuild.py"),run("independent_validator.py"),run("validate_schemas.py")]
    commands.append(run("test_clean_rebuild.py"))
    second={n:sha(OUT/n) for n in scientific_names()}
    fresh=[{"relative_path":n,"first_sha256":first[n],"fresh_process_sha256":second[n],"match":"yes" if first[n]==second[n] else "no"} for n in scientific_names()]
    write(OUT/"fresh_process_hash_comparison.csv",fresh)
    after=snapshot(pp);hist=[]
    for rel in sorted(set(before)|set(after)):
        b=before.get(rel);a=after.get(rel);hist.append({"relative_path":rel,"scope":"all prior chavi_* milestone/staging files plus root files; selected ds metadata/dictionaries with Git clean check","before_size_bytes":b[0] if b else "","before_sha256":b[1] if b else "","after_size_bytes":a[0] if a else "","after_sha256":a[1] if a else "","unchanged":"yes" if b==a and b is not None else "no"})
    write(OUT/"historical_artifact_before_after_hashes.csv",hist)
    # Dataset-wide preservation is additionally enforced through clean Git state.
    git=subprocess.run(["git","-c",f"safe.directory={(ROOT/'ds007116').as_posix()}","-C",str(ROOT/"ds007116"),"status","--porcelain"],capture_output=True,text=True,check=True)
    if git.stdout.strip():raise RuntimeError("dataset Git became dirty")
    if any(r["match"]!="yes" for r in fresh) or any(r["unchanged"]!="yes" for r in hist):raise RuntimeError("determinism or preservation gate failed")
    result={"status":"all_prepackage_gates_passed","commands":commands,"scientific_artifacts_repeated":len(fresh),"fresh_hash_mismatches":sum(r["match"]!="yes" for r in fresh),"protected_artifacts":len(hist),"protected_changes":sum(r["unchanged"]!="yes" for r in hist)}
    (OUT/"orchestration_results.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    report_run=run("make_reports.py");commands.append(report_run);result["commands"]=commands;(OUT/"orchestration_results.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    run("make_reports.py")
    first_pack=run("finalize_package.py");commands.append(first_pack);result["commands"]=commands;(OUT/"orchestration_results.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    run("make_reports.py")
    final=run("finalize_package.py")
    print(final["stdout"])
if __name__=="__main__":main()
