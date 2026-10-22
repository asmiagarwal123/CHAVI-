"""Finalize preservation, determinism, manifest, and ZIP for Step 5B-B1."""
from __future__ import annotations
import csv, hashlib, json, subprocess, sys, zipfile
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent
ZIP=ROOT/(BASE.name+".zip");ZIPHASH=ROOT/(BASE.name+".zip.sha256.txt")
def sha(p):
 d=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):d.update(b)
 return d.hexdigest()
def csvwrite(p,rows,fields):
 with p.open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
def protected():
 paths=[]
 for rel in ["chavi_analysis_ds007116_step5ba_clean_rebuild_20261001","chavi_audit_ds007116_step3b_20260909","chavi_analysis_ds007116_step5a_measurement_specification_20260916","chavi_analysis_ds007116_step5ad_decision_freeze_20260916","chavi_analysis_ds007116_step4b_five_tasks_20260916","chavi_recovery_preflight_correction_20261001"]:
  p=ROOT/rel
  if p.exists():paths.extend(x for x in p.rglob("*") if x.is_file())
 for n in ["CURRENT_PROJECT_STATE.md","PROJECT_MASTER_CONTEXT.md","RESEARCH_STATUS.md","CHAVI_MASTER_PROJECT_SPECIFICATION_AND_HANDOFF.md","CHATGPT_CODEX_HANDOFF.md"]:
  if (ROOT/n).exists():paths.append(ROOT/n)
 return sorted(set(paths))
def snap():return {p.relative_to(ROOT).as_posix():(p.stat().st_size,sha(p)) for p in protected()}
def main():
 before=snap(); artifacts=[BASE/"synthetic/independent_expected_outputs.json",BASE/"synthetic/production_outputs.json",BASE/"synthetic/comparison_records.csv",BASE/"validation_results.json"]
 runs=[]
 for run in [1,2]:
  cp=subprocess.run([sys.executable,str(BASE/"independent_profile_validator.py")],cwd=ROOT,capture_output=True,text=True)
  if cp.returncode:raise RuntimeError(cp.stderr+cp.stdout)
  for p in artifacts:runs.append({"run":run,"relative_path":p.relative_to(BASE).as_posix(),"sha256":sha(p)})
 by={}
 for r in runs:by.setdefault(r["relative_path"],[]).append(r["sha256"])
 for r in runs:r["matches_across_fresh_processes"]="yes" if len(set(by[r["relative_path"]]))==1 else "no"
 if any(r["matches_across_fresh_processes"]!="yes" for r in runs):raise ValueError("determinism failure")
 csvwrite(BASE/"fresh_process_deterministic_comparison.csv",runs,["run","relative_path","sha256","matches_across_fresh_processes"])
 after=snap(); rows=[]
 for k in sorted(set(before)|set(after)):
  b=before.get(k);a=after.get(k);rows.append({"relative_path":k,"before_size":b[0] if b else "","before_sha256":b[1] if b else "","after_size":a[0] if a else "","after_sha256":a[1] if a else "","unchanged":"yes" if a==b else "no"})
 if any(r["unchanged"]!="yes" for r in rows):raise ValueError("protected artifact changed")
 csvwrite(BASE/"historical_input_before_after_preservation_ledger.csv",rows,["relative_path","before_size","before_sha256","after_size","after_sha256","unchanged"])
 # Manifest excludes itself and enclosing ZIP so no circular self-hash is implied.
 files=sorted(p for p in BASE.rglob("*") if p.is_file() and p.name!="milestone_artifact_manifest.csv" and "__pycache__" not in p.parts and p.suffix!=".pyc")
 manifest=[]
 for p in files:
  count=""
  if p.suffix.lower()==".csv":
   with p.open(encoding="utf-8-sig",newline="") as f:count=sum(1 for _ in csv.DictReader(f))
  manifest.append({"relative_path":p.relative_to(BASE).as_posix(),"size_bytes":p.stat().st_size,"sha256":sha(p),"row_count_if_csv":count,"convention":"member; manifest itself and enclosing ZIP excluded"})
 csvwrite(BASE/"milestone_artifact_manifest.csv",manifest,["relative_path","size_bytes","sha256","row_count_if_csv","convention"])
 if ZIP.exists():ZIP.unlink()
 with zipfile.ZipFile(ZIP,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(x for x in BASE.rglob("*") if x.is_file() and "__pycache__" not in x.parts and x.suffix!=".pyc"):z.write(p,(Path(BASE.name)/p.relative_to(BASE)).as_posix())
 digest=sha(ZIP);ZIPHASH.write_text(f"{digest}  {ZIP.name}\n",encoding="utf-8",newline="\n")
 print(json.dumps({"status":"PASS","manifest_members":len(manifest),"protected_files":len(rows),"zip":str(ZIP),"zip_sha256":digest},indent=2))
if __name__=="__main__":main()
