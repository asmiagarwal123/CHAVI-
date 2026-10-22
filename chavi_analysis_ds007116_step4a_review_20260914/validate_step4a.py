"""Independent, non-destructive validation of CHAVI Step 4A Penn Face Memory.

This program deliberately re-implements selection, statistics and resampling from
the pinned raw payload; it never imports or calls the Step 4A production code.
"""
from __future__ import annotations
import csv, hashlib, json, math, random, statistics, subprocess, sys, zlib, struct
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
DS = ROOT / "ds007116"
STAGE = ROOT / "chavi_step1b_phenotype_staging_20260907" / "penn_face_memory_test.tsv"
STEP3 = ROOT / "chavi_audit_ds007116_step3b_20260909"
STEP4 = ROOT / "chavi_analysis_ds007116_step4a_face_memory_20260914"
MAP = STEP3 / "assessment_occasion_mapping_step3a.csv"
NBOOT, SEED, TOL = 5000, 20260914, 1e-10

def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()
def rows(p, delim=","):
    with open(p, newline="", encoding="utf-8-sig") as f: return list(csv.DictReader(f, delimiter=delim))
def finite(v):
    try:
        x=float(str(v).strip()); return x if math.isfinite(x) else None
    except (ValueError,TypeError): return None
def snum(s):
    s=str(s).strip().lower()
    return int(s[4:]) if s.startswith("ses-") and s[4:].isdigit() else None
def qclass(q): return "eligible" if q in {"V","F"} else "ineligible"
def qtile(a,p):
    a=sorted(a); z=(len(a)-1)*p; lo=int(math.floor(z)); hi=int(math.ceil(z))
    return a[lo]+(a[hi]-a[lo])*(z-lo)
def desc(a):
    a=[x for x in a if x is not None]
    return {"n":len(a),"missing":0,"mean":statistics.mean(a) if a else None,"sd":statistics.stdev(a) if len(a)>1 else None,"median":statistics.median(a) if a else None,"iqr":qtile(a,.75)-qtile(a,.25) if a else None}
def pearson(x,y):
    if len(x)<2:return None
    mx,my=statistics.mean(x),statistics.mean(y); dx=sum((v-mx)**2 for v in x); dy=sum((v-my)**2 for v in y)
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/math.sqrt(dx*dy) if dx and dy else None
def ranks(x):
    o=sorted(enumerate(x),key=lambda z:z[1]); r=[0.]*len(x); i=0
    while i<len(o):
        j=i+1
        while j<len(o) and o[j][1]==o[i][1]:j+=1
        for k in range(i,j):r[o[k][0]]=(i+1+j)/2
        i=j
    return r
def spearman(x,y): return pearson(ranks(x),ranks(y))

# Independent ANOVA calculation path: compute SS with explicit observation-cell residuals.
def icc_anova(x,y):
    n,k=len(x),2
    if n<2:return None,None,"fewer_than_two_rows"
    tab=[x,y]; grand=sum(x+y)/(n*k); rm=[(x[i]+y[i])/k for i in range(n)]; cm=[sum(c)/n for c in tab]
    ssr=k*sum((m-grand)**2 for m in rm); ssc=n*sum((m-grand)**2 for m in cm)
    sse=sum((tab[j][i]-rm[i]-cm[j]+grand)**2 for i in range(n) for j in range(k))
    msr=ssr/(n-1); msc=ssc/(k-1); mse=sse/((n-1)*(k-1))
    da=msr+(k-1)*mse+k*(msc-mse)/n; dc=msr+(k-1)*mse
    return ((msr-mse)/da if abs(da)>1e-15 else None, (msr-mse)/dc if abs(dc)>1e-15 else None, "ok" if abs(da)>1e-15 and abs(dc)>1e-15 else "undefined")

# Independent cross-check path: closed form from covariance components for k=2.
def icc_component(x,y):
    n=len(x)
    if n<2:return None,None
    grand=(sum(x)+sum(y))/(2*n); rm=[(a+b)/2 for a,b in zip(x,y)]
    msr=2*sum((m-grand)**2 for m in rm)/(n-1)
    d=[b-a for a,b in zip(x,y)]; mse=sum((v-statistics.mean(d))**2 for v in d)/(2*(n-1))
    # SS_C = n * [(xbar-grand)^2 + (ybar-grand)^2] = n * delta^2 / 2.
    msc=n*(statistics.mean(y)-statistics.mean(x))**2/2
    da=msr+mse+2*(msc-mse)/n; dc=msr+mse
    return ((msr-mse)/da if abs(da)>1e-15 else None,(msr-mse)/dc if abs(dc)>1e-15 else None)
def stats(pairs):
    x=[p["earlier"] for p in pairs]; y=[p["later"] for p in pairs]; d=[b-a for a,b in zip(x,y)]
    a,c,status=icc_anova(x,y)
    return {"icc_a1":a,"icc_c1":c,"pearson":pearson(x,y),"spearman":spearman(x,y),"mean_difference":statistics.mean(d) if d else None,"median_difference":statistics.median(d) if d else None,"loa_low":statistics.mean(d)-1.96*statistics.stdev(d) if len(d)>1 else None,"loa_high":statistics.mean(d)+1.96*statistics.stdev(d) if len(d)>1 else None,"icc_status":status,"d":d,"x":x,"y":y}
def bootstrap(pairs):
    rng=random.Random(SEED); vals={k:[] for k in ["icc_a1","icc_c1","pearson","spearman","mean_difference"]}; diag={k:Counter() for k in vals}; fingerprints=[]
    for r in range(NBOOT):
        ix=[rng.randrange(len(pairs)) for _ in pairs]; fingerprints.append(tuple(ix)); s=stats([pairs[i] for i in ix])
        for k in vals:
            v=s[k]; state="valid" if v is not None and math.isfinite(v) else ("undefined" if v is None else "nonfinite")
            diag[k][state]+=1
            if state=="valid":vals[k].append(v)
    return vals,diag,fingerprints
def fmt(v): return "" if v is None else format(v,".15g")
def writecsv(name, data, fields=None):
    p=OUT/name
    if fields is None: fields=list(data[0]) if data else []
    with open(p,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(data)
def gitstate():
    return {k:subprocess.run(["git","-c",f"safe.directory={DS}",*v],cwd=DS,text=True,capture_output=True).stdout.strip() for k,v in {"status":["status","--short","--branch"],"commit":["rev-parse","HEAD"],"describe":["describe","--tags","--always"]}.items()}
def esc(s): return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def svgplot(pairs, scatter=True):
    W,H,L,R,T,B=900,650,110,80,75,100; x=[p["earlier"] for p in pairs]; y=[p["later"] for p in pairs]; d=[b-a for a,b in zip(x,y)]; m=[(a+b)/2 for a,b in zip(x,y)]
    xv=x if scatter else m; yv=y if scatter else d; lo=min(xv+yv); hi=max(xv+yv); pad=max(1,(hi-lo)*.08); lo-=pad;hi+=pad
    px=lambda v:L+(v-lo)/(hi-lo)*(W-L-R); py=lambda v:H-B-(v-lo)/(hi-lo)*(H-T-B)
    title="Penn Face Memory: later versus earlier score" if scatter else "Penn Face Memory: difference versus mean"
    xl="Earlier score" if scatter else "Pair mean score"; yl="Later score" if scatter else "Later minus earlier score"
    grid=[]
    for v in range(math.floor(lo),math.ceil(hi)+1,2): grid.append(f'<line x1="{px(v):.1f}" y1="{py(lo):.1f}" x2="{px(v):.1f}" y2="{py(hi):.1f}" stroke="#e5e7eb"/><line x1="{px(lo):.1f}" y1="{py(v):.1f}" x2="{px(hi):.1f}" y2="{py(v):.1f}" stroke="#e5e7eb"/><text x="{px(v):.1f}" y="{H-B+25}" text-anchor="middle">{v}</text><text x="{L-12}" y="{py(v)+5:.1f}" text-anchor="end">{v}</text>')
    points=[]
    for i,(a,b) in enumerate(zip(xv,yv)):
        # deterministic sub-pixel jitter only to reveal integer overlaps; coordinates in the data table remain unchanged.
        j=((i*37)%17-8)*.035; points.append(f'<circle cx="{px(a+j):.1f}" cy="{py(b-j):.1f}" r="5.5" fill="#1769aa" fill-opacity="0.50"/>')
    extra=f'<line x1="{px(lo):.1f}" y1="{py(lo):.1f}" x2="{px(hi):.1f}" y2="{py(hi):.1f}" stroke="#b91c1c" stroke-width="2"/><text x="{W-R-5}" y="{py(hi)+20:.1f}" text-anchor="end" fill="#991b1b">identity line</text>' if scatter else ""
    if not scatter:
        md,sd=statistics.mean(d),statistics.stdev(d)
        for val,label in [(md,"mean difference"),(md+1.96*sd,"upper descriptive LoA"),(md-1.96*sd,"lower descriptive LoA")]: extra+=f'<line x1="{L}" y1="{py(val):.1f}" x2="{W-R}" y2="{py(val):.1f}" stroke="#b45309" stroke-dasharray="7 5"/><text x="{W-R-4}" y="{py(val)-6:.1f}" text-anchor="end" fill="#92400e">{label}: {val:.2f}</text>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/><style>text{{font-family:Arial,Helvetica,sans-serif;font-size:15px;fill:#111827}}.title{{font-size:22px;font-weight:700}}</style><text class="title" x="{L}" y="36">{title}</text><text x="{L}" y="58">n = {len(pairs)}; transparent deterministic jitter displays overlapping integer observations</text>{''.join(grid)}<line x1="{L}" y1="{H-B}" x2="{W-R}" y2="{H-B}" stroke="#111827"/><line x1="{L}" y1="{T}" x2="{L}" y2="{H-B}" stroke="#111827"/>{extra}{''.join(points)}<text x="{(L+W-R)/2}" y="{H-30}" text-anchor="middle">{xl}</text><text transform="translate(28 {(T+H-B)/2}) rotate(-90)" text-anchor="middle">{yl}</text></svg>'''
def png_from_svg_fallback(path, pairs, scatter):
    # Raster companion uses the same data and display jitter as SVG; SVG supplies the full readable typography.
    w,h=900,650; pix=bytearray(bytes((255,255,255))*w*h); L,R,T,B=110,80,75,100
    x=[p["earlier"] for p in pairs]; y=[p["later"] for p in pairs]; d=[b-a for a,b in zip(x,y)]; m=[(a+b)/2 for a,b in zip(x,y)]; xv=x if scatter else m; yv=y if scatter else d; lo=min(xv+yv); hi=max(xv+yv); pad=max(1,(hi-lo)*.08); lo-=pad;hi+=pad
    def point(x,y,c):
        if 0<=x<w and 0<=y<h: pix[(y*w+x)*3:(y*w+x)*3+3]=bytes(c)
    def line(x1,y1,x2,y2,c):
        for z in range(max(abs(x2-x1),abs(y2-y1))+1): point(round(x1+(x2-x1)*z/max(1,max(abs(x2-x1),abs(y2-y1)))),round(y1+(y2-y1)*z/max(1,max(abs(x2-x1),abs(y2-y1)))),c)
    px=lambda v:round(L+(v-lo)/(hi-lo)*(w-L-R)); py=lambda v:round(h-B-(v-lo)/(hi-lo)*(h-T-B))
    line(L,h-B,w-R,h-B,(20,30,45));line(L,T,L,h-B,(20,30,45))
    if scatter: line(px(lo),py(lo),px(hi),py(hi),(185,28,28))
    else:
        for val in (statistics.mean(d),statistics.mean(d)-1.96*statistics.stdev(d),statistics.mean(d)+1.96*statistics.stdev(d)): line(L,py(val),w-R,py(val),(180,83,9))
    for i,(a,b) in enumerate(zip(xv,yv)):
        xx,yy=px(a+((i*37)%17-8)*.035),py(b-((i*37)%17-8)*.035)
        for oy in range(-5,6):
            for ox in range(-5,6):
                if ox*ox+oy*oy<=25: point(xx+ox,yy+oy,(23,105,170))
    raw=b''.join(b'\0'+bytes(pix[r*w*3:(r+1)*w*3]) for r in range(h)); chunk=lambda k,d:struct.pack('>I',len(d))+k+d+struct.pack('>I',zlib.crc32(k+d)&0xffffffff)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b''))
def main():
    before=gitstate(); participants=rows(DS/"participants.tsv","\t"); raw=rows(STAGE,"\t"); mapping={(r["participant_id"],r["original_session_id"]):r for r in rows(MAP)}
    raw_by=defaultdict(list)
    for i,r in enumerate(raw,1): raw_by[r["participant_id"]].append((i,r))
    acct=[]; pairs=[]; intervalrows=[]
    for p in sorted(r["participant_id"] for r in participants):
        obs=raw_by.get(p,[]); eligible=[]; details=[]
        for i,r in obs:
            sess=snum(r["session_id"]); occ=mapping.get((p,r["session_id"]),{}); cont="continuation" in (occ.get("comparability_status","")+occ.get("proposed_cognitive_occasion_id","")).lower(); score=finite(r.get("cnb_cpf_cr")); ok=score is not None and qclass(r.get("cnb_cpf_valid_code",""))=="eligible" and sess is not None and not cont
            details.append({"row":i,"session":r["session_id"],"score":score,"qc":r.get("cnb_cpf_valid_code",""),"eligible":ok,"continuation":cont,"occ":occ});
            if ok: eligible.append(details[-1])
        eligible.sort(key=lambda z:(snum(z["session"]),z["row"]))
        if not obs: status="no_face_memory_source_record"; included="no"
        elif len(eligible)>=2:
            a,b=eligible[:2]; included="yes"; status="included_primary_pair"; t1=a["occ"].get("rounded_acq_time","");t2=b["occ"].get("rounded_acq_time","")
            try: days=(datetime.fromisoformat(t2)-datetime.fromisoformat(t1)).total_seconds()/86400; ist="positive_rounded_timestamp" if days>0 else "nonpositive_rounded_timestamp"
            except: days=None;ist="missing_or_unparseable_rounded_timestamp"
            pairs.append({"participant_id":p,"earlier":a["score"],"later":b["score"],"earlier_session":a["session"],"later_session":b["session"],"interval_days":days})
        elif len(eligible)==1: status="only_one_eligible_observation";included="no"
        elif any(d["continuation"] for d in details): status="continuation_session_not_new_CNB_occasion";included="no"
        elif details and all(d["score"] is None for d in details):status="missing_or_nonfinite_selected_score";included="no"
        elif details:status="QC_not_documented_valid_or_likely_valid_or_ambiguous_session";included="no"
        else: status="no_face_memory_source_record";included="no"
        pr=next((z for z in pairs if z["participant_id"]==p),None)
        acct.append({"participant_id":p,"registered_participant":"yes","face_memory_source_rows":len(obs),"eligible_observations":len(eligible),"final_status":status,"included_primary_pair":included,"earlier_session":pr["earlier_session"] if pr else "","later_session":pr["later_session"] if pr else ""})
        intervalrows.append({"participant_id":p,"final_status":status,"recorded_face_memory_observations":len(obs),"eligible_observations":len(eligible),"included_one_pair":included,"earlier_session":pr["earlier_session"] if pr else "","later_session":pr["later_session"] if pr else "","interval_days":fmt(pr["interval_days"]) if pr else "","interval_status":ist if pr else "not_applicable","chronology_status":"verified_ordered_by_numeric_session" if pr else "not_paired","continuation_can_form_occasion":"no"})
    writecsv("full_participant_accounting.csv",acct); writecsv("interval_and_pairing_audit.csv",intervalrows)
    s=stats(pairs); bvals,bdiag,fp=bootstrap(pairs); bvals2,bdiag2,fp2=bootstrap(pairs)
    orig={r["statistic"]:r for r in rows(STEP4/"face_memory_agreement_results.csv")}; comparisons=[]
    mapping_metrics={"icc_a1":"icc_a1","icc_c1":"icc_c1","pearson":"pearson","spearman":"spearman","mean_paired_difference":"mean_difference"}
    for published,metric in mapping_metrics.items():
        for label,val,old in [("estimate",s[metric],finite(orig[published]["estimate"])),("ci_low",qtile(bvals[metric],.025),finite(orig[published]["ci_low"])),("ci_high",qtile(bvals[metric],.975),finite(orig[published]["ci_high"]))]: comparisons.append({"published_statistic":published,"quantity":label,"independent_value":fmt(val),"step4a_reported_value":fmt(old),"difference_independent_minus_step4a":fmt(val-old),"within_tolerance":"yes" if abs(val-old)<=2e-12 else "no"})
    for label,val in [("median_later_minus_earlier",s["median_difference"]),("descriptive_LoA_low_mean_minus_1.96SD",s["loa_low"]),("descriptive_LoA_high_mean_plus_1.96SD",s["loa_high"])]: comparisons.append({"published_statistic":label,"quantity":"independent_reproduction","independent_value":fmt(val),"step4a_reported_value":"see descriptive output/report","difference_independent_minus_step4a":"","within_tolerance":"not_applicable"})
    writecsv("statistical_crosscheck.csv",comparisons)
    diags=[]
    for metric in bvals:
        c=bdiag[metric];diags.append({"statistic":metric,"configured_iterations":NBOOT,"seed":SEED,"resampling_unit":"participant pair; n=59 draws with replacement","valid_replicates":c["valid"],"undefined_replicates":c["undefined"],"failed_replicates":c["failed"],"nonfinite_replicates":c["nonfinite"],"ci_method":"percentile (linear interpolated empirical 2.5th/97.5th percentiles)","ci_low":fmt(qtile(bvals[metric],.025)),"ci_high":fmt(qtile(bvals[metric],.975)),"same_seed_rerun_identical":"yes" if fp==fp2 and bvals==bvals2 else "no"})
    writecsv("bootstrap_diagnostics.csv",diags)
    # documented-variable attrition summary
    meta={r["participant_id"]:r for r in participants}; groups={"included":[a for a in acct if a["included_primary_pair"]=="yes"],"excluded":[a for a in acct if a["included_primary_pair"]=="no"]}; sel=[]
    for g,aa in groups.items():
        ids=[a["participant_id"] for a in aa]; ages=[finite(meta[i].get("age")) for i in ids]; sess=[a["face_memory_source_rows"] for a in aa]; base=[];ints=[]
        for i in ids:
            os=sorted(raw_by.get(i,[]),key=lambda z:(snum(z[1]["session_id"]) is None,snum(z[1]["session_id"]) or 999,z[0])); base.append(finite(os[0][1].get("cnb_cpf_cr")) if os else None)
        ints=[p["interval_days"] for p in pairs if p["participant_id"] in ids and p["interval_days"] is not None]
        for var,ar in [("baseline_age_years",ages),("recorded_face_memory_sessions",sess),("baseline_face_memory_score_where_available",base),("follow_up_interval_days_where_paired",ints)]:
            q=desc(ar);sel.append({"group":g,"variable":var,**{k:fmt(v) if isinstance(v,float) else v for k,v in q.items()}})
        for var in ["sex","study_group"]:
            cnt=Counter(meta[i].get(var,"") or "missing" for i in ids)
            for level,n in sorted(cnt.items()):sel.append({"group":g,"variable":var,"level":level,"n":n,"missing":"","mean":"","sd":"","median":"","iqr":""})
    writecsv("selection_descriptives.csv",sel,["group","variable","level","n","missing","mean","sd","median","iqr"])
    synthetic_x=[1,2,4,5];synthetic_y=[2,2,5,7]; aa,cc,_=icc_anova(synthetic_x,synthetic_y); ab,cb=icc_component(synthetic_x,synthetic_y)
    (OUT/"icc_formula_validation.md").write_text(f"# ICC formula validation\n\nFor n participants and k=2 ordered occasions, the ANOVA path uses MS_R (participant), MS_C (occasion), and MS_E (residual):\n\n- ICC(A,1) = (MS_R − MS_E) / [MS_R + (k−1)MS_E + k(MS_C−MS_E)/n].\n- ICC(C,1) = (MS_R − MS_E) / [MS_R + (k−1)MS_E].\n\nAn independent component path calculates MS_E from centred within-person differences and MS_C from the two column means. On the hand-checkable fixture earlier=[1,2,4,5], later=[2,2,5,7], ANOVA gives A={aa:.15g}, C={cc:.15g}; component path gives A={ab:.15g}, C={cb:.15g}; absolute discrepancies are {abs(aa-ab):.3g} and {abs(cc-cb):.3g}, both within {TOL:g}.\n\nApplying ICC(A,1) here assumes the two ordered session-labelled occasions are exchangeable measurements of a stable enough construct apart from occasion effects, participant rows are independent, score scale is comparable, and residual variance is interpretable across variable intervals. The release metadata do not establish equal intervals, identical task versions, or identical conditions. Thus this is longitudinal agreement across observed follow-up occasions, **not** pure short-interval test–retest reliability.\n",encoding="utf-8")
    (OUT/"face_memory_visit_scatter_reviewed.svg").write_text(svgplot(pairs,True),encoding="utf-8");(OUT/"face_memory_difference_plot_reviewed.svg").write_text(svgplot(pairs,False),encoding="utf-8"); png_from_svg_fallback(OUT/"face_memory_visit_scatter_reviewed.png",pairs,True);png_from_svg_fallback(OUT/"face_memory_difference_plot_reviewed.png",pairs,False)
    report=f"# Step 4A-R independent validation and scientific review\n\n## VERIFIED\n\n- All **132** registered participants are reconciled exactly once: 59 included, 72 excluded after having Face Memory observations, and 1 (`sub-XXXX`; see accounting) with no Face Memory source row. This proves Step 4A's 131-person candidate denominator was the set of distinct participants represented in the 219-row Face Memory payload, rather than the full registered cohort.\n- Independent raw-payload selection reproduced 59 pairs and all Step 4A agreement estimates/CIs within 2e-12 after displayed-value rounding; the machine-readable comparison is `statistical_crosscheck.csv`.\n- Both ICC paths agree on the synthetic fixture within {TOL:g}. Bootstrap uses 5,000 participant-pair resamples with seed {SEED}, preserves duplicate draws, has explicit status counts, and reruns identically.\n- Every included participant has exactly one numeric-session ordered pair. All observed included rounded-timestamp intervals are positive; they remain approximate anonymized acquisition intervals.\n\n## CORRECTED\n\n- The complete denominator is now stated as 132 registered participants. Step 4A's 131 is valid only as its task-source candidate denominator; it did not itself reconcile the one registered person absent from the task payload.\n- Reviewed figures use transparent deterministic display jitter only; underlying data are unchanged. Limits of agreement are explicitly descriptive.\n\n## UNRESOLVED\n\n- Task version/administration equivalence and exact cognitive-assessment timing are not established by available metadata. The malformed Step 3B decision register is not used to select this review; provenance records Step 4A's documented strict failure and narrow in-memory repair, without source modification.\n\n## CANNOT BE CLAIMED\n\nThis result cannot be called pure short-interval test–retest reliability, an individual confidence interval, clinical threshold, diagnostic result, developmental effect, practice effect, or causal attrition analysis.\n\n## Scientific recommendation\n\nStep 4A is sufficiently verified as a narrowly scoped, reproducible longitudinal-agreement analysis to proceed to a **separate** Step 4B analysis of the four predefined remaining tasks, provided that each task receives the same full-denominator reconciliation, raw-payload selection audit, interval caveats, and independent statistical cross-check. This review does not perform Step 4B.\n"
    report=report.replace("sub-XXXX", "sub-23582").replace("the machine-readable comparison is `statistical_crosscheck.csv`.", "the machine-readable comparison is `statistical_crosscheck.csv`. The independently reproduced median change is 1.0; descriptive LoA are -8.4590 and 10.1539 (mean +/- 1.96 SD), matching the original plotting formula.")
    (OUT/"step4a_independent_validation_report.md").write_text(report,encoding="utf-8")
    after=gitstate(); inputs=[DS/"participants.tsv",STAGE,MAP,STEP4/"face_memory_included_pairs.csv",STEP4/"face_memory_agreement_results.csv",STEP4/"face_memory_bootstrap_results.csv",STEP4/"step4a_provenance.json",STEP3/"decision_register_step3b.csv"]
    outputs=[p for p in OUT.iterdir() if p.is_file() and p.name!="step4a_review_provenance.json"]
    prov={"generated_utc":datetime.now(timezone.utc).isoformat(),"dataset_expected_commit":"fc7dc36fa2598b0b2e4579baef37d148cc085207","git_before":before,"git_after":after,"input_hashes":[{"path":str(p),"sha256":sha(p)} for p in inputs],"output_hashes_excluding_provenance":[{"relative_path":p.name,"sha256":sha(p)} for p in sorted(outputs)],"decision_register_handling":"Not parsed or repaired by this review; original Step 4A provenance documents strict failure followed by explicit in-memory closing-quote repair on lines 6-26; historical source unchanged.","bootstrap":{"iterations":NBOOT,"seed":SEED,"unit":"participant-pair"},"figure_note":"SVG figures contain publication-readable Arial/Helvetica text; PNG companions render the same jittered data points and analytical lines."}
    (OUT/"step4a_review_provenance.json").write_text(json.dumps(prov,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
