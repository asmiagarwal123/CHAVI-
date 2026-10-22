import json, re, subprocess, sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
base=root/'code'/'validate_c6.py'
subprocess.run([sys.executable,str(base)],check=False)
p=root/'validation'/'checks.json'; out=json.loads(p.read_text(encoding='utf-8'))
man=(root/'CHAVI_FACULTY_REVIEW_MANUSCRIPT.md').read_text(encoding='utf-8')
bib=(root/'references.bib').read_text(encoding='utf-8')
keys=set(re.findall(r'@article\{([^,]+),',bib))
expected={'carpenter2000','chernozhukov2018','cronbach1953','ibrahim2015','mcgraw1996','morris2019','sevchik2026','slade2008','sullivan2017'}
refs=['Carpenter','Chernozhukov','Cronbach','Ibrahim','McGraw','Morris','Sevchik','Slade','Sullivan']
intext=['Carpenter and Bithell, 2000','Chernozhukov et al., 2018','Cronbach and Gleser (1953)','Ibrahim et al., 2015','McGraw and Wong, 1996','Morris et al., 2019','Sevchik et al., 2026','Slade et al., 2008','Sullivan et al., 2017']
def add(name,ok,evidence,observed): out['checks'].append({'requirement':name,'status':'PASS' if ok else 'FAIL','evidence':evidence,'observed':observed})
add('citation set equality', keys==expected and all(x in man for x in refs) and all(x in man for x in intext),'manuscript, References, references.bib',{'bib_keys':sorted(keys),'expected':sorted(expected),'intext_count':sum(x in man for x in intext)})
paths=re.findall(r'`([^`]+(?:\.md|\.csv))`',man)
add('internal manuscript paths exist',all((root/x).exists() for x in paths),'manuscript backtick paths',{'paths':paths,'missing':[x for x in paths if not (root/x).exists()]})
extra=['FACULTY_REVIEW_HANDOFF.md','CORRECTIONS_FROM_C6.md','JOURNAL_FIT_COMPARISON.md','CITATION_VERIFICATION.md']
add('C6-FINAL handoff deliverables exist',all((root/x).exists() for x in extra),'C6-FINAL root',extra)
out['overall']='PASS' if all(c['status']=='PASS' for c in out['checks']) else 'FAIL'
p.write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
sys.exit(0 if out['overall']=='PASS' else 1)
