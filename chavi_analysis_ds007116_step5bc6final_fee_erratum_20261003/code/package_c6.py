import csv, hashlib, subprocess, sys, zipfile
from pathlib import Path

root=Path(__file__).resolve().parents[1]
repo=root.parent
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
upstreams=['chavi_analysis_ds007116_step5bc1_empirical_protocol_20261003.zip','chavi_analysis_ds007116_step5bc2_empirical_execution_20261003.zip','chavi_analysis_ds007116_step5bb3r_validation_repair_20261002.zip','chavi_analysis_ds007116_step5bc3_scientific_synthesis_20261003.zip','chavi_analysis_ds007116_step5bc5_revised_manuscript_20261003.zip']
with open(root/'input_manifest.csv','w',newline='',encoding='utf-8') as f:
 w=csv.writer(f); w.writerow(['input','sha256']); w.writerows((x,sha(repo/x)) for x in upstreams)
def manifest():
 with open(root/'output_manifest.csv','w',newline='',encoding='utf-8') as f:
  w=csv.writer(f); w.writerow(['path','sha256','bytes'])
  for p in sorted(root.rglob('*')):
   if p.is_file() and p.name not in ['output_manifest.csv']:
    w.writerow([str(p.relative_to(root)).replace('\\','/'),sha(p),p.stat().st_size])
def zipit():
 z=repo/(root.name+'.zip')
 with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as out:
  for p in sorted(root.rglob('*')):
   if p.is_file(): out.write(p,p.relative_to(root).as_posix())
 return z
manifest(); zipit()
subprocess.run([sys.executable,str(root/'code'/'validate_fee_erratum.py')],check=False)
manifest(); z=zipit()
subprocess.run([sys.executable,str(root/'code'/'validate_fee_erratum.py')],check=True)
(repo/(root.name+'.zip.sha256.txt')).write_text(sha(z)+'  '+z.name+'\n',encoding='ascii')
print('ZIP',z.name,sha(z))
