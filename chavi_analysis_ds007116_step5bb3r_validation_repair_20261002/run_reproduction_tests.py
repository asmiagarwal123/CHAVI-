"""Genuine separate-process and interrupted/resumed atomic-checkpoint test."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
BASE=Path(__file__).resolve().parent;root=BASE/'reproduction_fixture';runid=str(int(time.time()*1000));inter=root/f'interrupted_resumed_{runid}';fresh=root/f'fresh_{runid}'
commands=[]
def run(args):
 c=[sys.executable,str(BASE/'reproduction_worker.py')]+args;p=subprocess.run(c,capture_output=True,text=True,check=False);commands.append({'command':c,'returncode':p.returncode,'stdout':p.stdout.strip(),'stderr':p.stderr.strip()});assert p.returncode==0,p.stderr
run(['--outdir',str(inter),'--limit','1']);assert len(list(inter.glob('*.json')))==1
run(['--outdir',str(inter)]);assert len(list(inter.glob('*.json')))==2
run(['--outdir',str(fresh)]);assert len(list(fresh.glob('*.json')))==2
def hashes(d):return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.glob('*.json'))}
same=hashes(inter)==hashes(fresh);result={'status':'PASS' if same else 'FAIL','processes_launched':3,'interruption_after_checkpoints':1,'resumed_complete':len(hashes(inter)),'fresh_complete':len(hashes(fresh)),'byte_identical_checkpoint_hashes':same,'atomic_temp_files_remaining':len(list(root.rglob('*.tmp'))),'interrupted_resumed_hashes':hashes(inter),'fresh_hashes':hashes(fresh),'commands':commands}
if result['atomic_temp_files_remaining']:result['status']='FAIL'
(BASE/'runtime_resume_evidence.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));raise SystemExit(result['status']!='PASS')
