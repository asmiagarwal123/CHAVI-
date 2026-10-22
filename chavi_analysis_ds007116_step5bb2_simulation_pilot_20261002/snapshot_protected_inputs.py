"""Create the immutable pre-execution snapshot for Step 5B-B2."""
from __future__ import annotations
import csv, hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent
PROTECTED=[ROOT/"chavi_analysis_ds007116_step5ba_clean_rebuild_20261001",ROOT/"chavi_analysis_ds007116_step5bb1_profile_protocol_20261001"]
EXTRA=[ROOT/"chavi_analysis_ds007116_step5ba_clean_rebuild_20261001.zip",ROOT/"chavi_analysis_ds007116_step5bb1_profile_protocol_20261001.zip"]
def sha(p):
 d=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):d.update(b)
 return d.hexdigest()
paths=[]
for d in PROTECTED:paths.extend(p for p in d.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix!=".pyc")
paths.extend(EXTRA)
rows=[{"relative_path":p.relative_to(ROOT).as_posix(),"before_size_bytes":p.stat().st_size,"before_sha256":sha(p)} for p in sorted(set(paths))]
with (BASE/"protected_inputs_before.csv").open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)
print(f"snapshotted={len(rows)}")
