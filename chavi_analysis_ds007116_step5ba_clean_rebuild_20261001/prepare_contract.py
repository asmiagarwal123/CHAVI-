"""Verify inputs, reconstruct cohorts, and freeze the adopted contract before fitting."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np


OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
DATASET = ROOT / "ds007116"
STEP3B = ROOT / "chavi_audit_ds007116_step3b_20260909"
STAGE = ROOT / "chavi_step1b_phenotype_staging_20260907"
CORR = ROOT / "chavi_recovery_preflight_correction_20261001"
TASKS = (
    ("letter_nback", "short_letter_2back", "cnb_lnb_mcr", "cnb_lnb_valid_code", 1),
    ("face_memory", "penn_face_memory_test", "cnb_cpf_cr", "cnb_cpf_valid_code", 1),
    ("matrix_reasoning", "penn_matrix_reasoning_test", "cnb_pmat_cr", "cnb_pmat_valid_code", 1),
    ("emotion_recognition", "penn_emotion_recognition_task", "cnb_er40_cr", "cnb_er40_valid_code", 1),
    ("dominant_finger_tapping", "short_computerized_finger_tapping_task", "cnb_ctap_dom", "cnb_ctap_valid_code", 1),
)
TASK_KEYS = [x[0] for x in TASKS]
TASK_META = {x[0]: x[1:] for x in TASKS}
SOURCE_HASH = "8b435d4b23d0b5f70b3c56ade4215d215028426dbdb46eaaf8daaa3cd0dc1978"


def read_csv(path, delimiter=","):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def write_csv(path, rows, fields=None):
    fields = fields or list(rows[0])
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ids_hash(values):
    return hashlib.sha256(("\n".join(sorted(values)) + "\n").encode("utf-8")).hexdigest()


def keys_hash(values):
    return hashlib.sha256(("\n".join(sorted(values)) + "\n").encode("utf-8")).hexdigest()


def finite(value):
    try: return math.isfinite(float(value))
    except (TypeError, ValueError): return False


def session_order(value):
    match = re.fullmatch(r"ses-(\d+)", value or "")
    if not match: raise ValueError(f"nonnumeric session label: {value}")
    return int(match.group(1))


def complete(source, occasion_keys, continuation, allowed):
    out = defaultdict(list)
    for pid, session in occasion_keys:
        if (pid, session) in continuation: continue
        if all((row := source.get((pid, session, task))) and finite(row["original_value"]) and row["raw_qc_codes"] in allowed for task in TASK_KEYS):
            out[pid].append(session)
    return {p: sorted(set(ss), key=session_order) for p, ss in out.items()}


def source_rows(ids, sessions, source, mappings, stratum):
    rows = []
    for pid in ids:
        for session in sessions[pid]:
            for task in TASK_KEYS:
                r = source[(pid, session, task)]
                rows.append({
                    "participant_id":pid, "analytical_stratum":stratum, "session_id":session,
                    "task_key":task, "task_table_stem":r["task_table_stem"], "score_field":r["score_field"],
                    "raw_score":r["original_value"], "parsed_score":format(float(r["original_value"]), ".17g"),
                    "raw_qc_code":r["raw_qc_codes"], "session_age":r["session_age"],
                    "source_filename":r["source_filename"], "source_row_reference":r["source_row_reference"],
                    "cognitive_occasion_id":r["cognitive_occasion_id"],
                    "comparability_status":mappings[(pid, session)]["comparability_status"],
                })
    return rows


def main():
    required_corrected = ["step5ba_rebuild_specification_recommended.json", "contract_decision_register_corrected.csv",
        "independent_validation_plan_corrected.md", "crossfit_candidate_identity_maps.csv", "reference_a_source_rows.csv",
        "primary_vf_source_rows.csv", "vonly_source_rows.csv", "qc_pairing_sensitivity_identity_comparison.csv",
        "corrected_source_cohort_reconciliation.csv", "milestone_artifact_manifest.csv"]
    correction_manifest = {r["relative_path"]:r for r in read_csv(CORR / "milestone_artifact_manifest.csv")}
    for name in required_corrected:
        path = CORR / name
        if not path.is_file(): raise FileNotFoundError(path)
        if name != "milestone_artifact_manifest.csv":
            entry = correction_manifest.get(name)
            if not entry or sha256(path) != entry["sha256"] or path.stat().st_size != int(entry["size_bytes"]):
                raise ValueError(f"corrected package integrity failure: {name}")

    if sha256(STEP3B / "task_observations_long.csv") != SOURCE_HASH:
        raise ValueError("canonical Step3B source hash mismatch")
    git = lambda *args: subprocess.run(["git","-c",f"safe.directory={DATASET.as_posix()}","-C",str(DATASET),*args],capture_output=True,text=True,check=True).stdout.strip()
    if git("rev-parse","HEAD") != "fc7dc36fa2598b0b2e4579baef37d148cc085207" or git("tag","--points-at","HEAD") != "1.0.6" or git("status","--porcelain"):
        raise ValueError("dataset identity/tag/clean check failed")

    input_paths = [DATASET/"participants.tsv", STEP3B/"task_observations_long.csv", STEP3B/"assessment_occasion_mapping_step3a.csv",
                   ROOT/"chavi_audit_ds007116_step1b_20260907/retrieval_manifest.csv"] + [CORR/n for n in required_corrected]
    retrieval = read_csv(ROOT / "chavi_audit_ds007116_step1b_20260907/retrieval_manifest.csv")
    input_paths += [STAGE / Path(r["relative_dataset_path"]).name for r in retrieval]
    input_paths += [DATASET / "phenotype" / f"{stem}.json" for _,stem,_,_,_ in TASKS]
    input_paths = sorted(set(p.resolve() for p in input_paths))
    manifest = [{"relative_path":p.relative_to(ROOT).as_posix(),"role":"actual_input","size_bytes":p.stat().st_size,"sha256":sha256(p)} for p in input_paths]

    for r in retrieval:
        p = STAGE / Path(r["relative_dataset_path"]).name
        if p.stat().st_size != int(r["expected_size_bytes"]) or sha256(p) != r["expected_sha256"]:
            raise ValueError(f"staged payload mismatch: {p.name}")
    for task,stem,field,qc,_ in TASKS:
        d = json.loads((DATASET/"phenotype"/f"{stem}.json").read_text(encoding="utf-8"))
        if d[qc]["Levels"].get("V") != "Valid" or not d[qc]["Levels"].get("F","").startswith("Likely valid"):
            raise ValueError(f"QC dictionary mismatch: {task}")

    observations = read_csv(STEP3B/"task_observations_long.csv")
    mappings_raw = read_csv(STEP3B/"assessment_occasion_mapping_step3a.csv")
    participants = read_csv(DATASET/"participants.tsv", "\t")
    registered = {r["participant_id"] for r in participants}
    source, source_keys = {}, []
    staged_cache = {stem:read_csv(STAGE/f"{stem}.tsv", "\t") for _,stem,_,_,_ in TASKS}
    for r in observations:
        if r["task_key"] not in TASK_META: continue
        key = (r["participant_id"],r["repository_session_id"],r["task_key"])
        if key in source: raise ValueError(f"duplicate source key: {key}")
        if r["participant_id"] not in registered: raise ValueError(f"unregistered source identity: {key}")
        stem,field,qc,_ = TASK_META[r["task_key"]]
        if (r["task_table_stem"],r["score_field"],r["applicable_qc_fields"]) != (stem,field,qc): raise ValueError(f"source metadata mismatch: {key}")
        # Parse original score independently; Step3B parsed value is comparison only.
        parsed = float(r["original_value"]) if finite(r["original_value"]) else None
        if (parsed is None) != (not finite(r["parsed_numeric_value"])) or (parsed is not None and parsed != float(r["parsed_numeric_value"])):
            raise ValueError(f"source parsed score mismatch: {key}")
        exp_vf = parsed is not None and r["raw_qc_codes"] in {"V","F"}
        exp_v = parsed is not None and r["raw_qc_codes"] == "V"
        if exp_vf != (r["eligible_documented_valid_or_likely_valid"] == "yes") or exp_v != (r["eligible_strict_documented_V_only"] == "yes"):
            raise ValueError(f"upstream eligibility mismatch: {key}")
        m = re.fullmatch(r"phenotype/([^#]+)\.tsv#data-row-(\d+)",r["source_row_reference"])
        if not m or m.group(1) != stem: raise ValueError(f"source reference mismatch: {key}")
        sr = staged_cache[stem][int(m.group(2))-1]
        norm = lambda x: "" if (x or "").lower() in {"","n/a","na","nan"} else x
        if (sr["participant_id"],sr["session_id"],norm(sr[field]),norm(sr[qc])) != (r["participant_id"],r["repository_session_id"],norm(r["original_value"]),norm(r["raw_qc_codes"])):
            raise ValueError(f"staged source mismatch: {key}")
        source[key] = r; source_keys.append("|".join(key))
    map_keys = [(r["participant_id"],r["original_session_id"]) for r in mappings_raw]
    if len(map_keys) != len(set(map_keys)): raise ValueError("duplicate occasion map key")
    mappings = {k:r for k,r in zip(map_keys,mappings_raw)}
    occasion_keys = sorted({(p,s) for p,s,_ in source},key=lambda x:(x[0],session_order(x[1])))
    if set(occasion_keys) - set(mappings): raise ValueError("missing required occasion mapping")
    continuation = {k for k,r in mappings.items() if "continuation" in (r["comparability_status"]+" "+r["proposed_cognitive_occasion_id"]).lower()}
    if continuation != {("sub-20812","ses-2")}: raise ValueError(f"continuation keys changed: {continuation}")

    vf = complete(source,occasion_keys,continuation,{"V","F"}); strict = complete(source,occasion_keys,continuation,{"V"})
    ref_ids = sorted(vf); primary_ids = sorted(p for p,ss in vf.items() if len(ss)>=2); vonly_ids = sorted(p for p,ss in strict.items() if len(ss)>=2)
    p_sessions = {p:vf[p][:2] for p in primary_ids}; v_sessions = {p:strict[p][:2] for p in vonly_ids}
    fixed_ids = sorted(p for p in primary_ids if all(source[(p,s,t)]["raw_qc_codes"]=="V" for s in p_sessions[p] for t in TASK_KEYS))
    fixed_sessions = {p:p_sessions[p] for p in fixed_ids}; ref_sessions = {p:[vf[p][0]] for p in ref_ids}
    if (len(ref_ids),len(primary_ids),len(vonly_ids),len(fixed_ids),sum(map(len,vf.values()))) != (109,52,45,41,176): raise ValueError("cohort counts changed")
    if not set(vonly_ids)<=set(primary_ids) or not set(fixed_ids)<=set(primary_ids): raise ValueError("strict-V sets not Primary subsets")

    reference_rows = source_rows(ref_ids,ref_sessions,source,mappings,"reference_a")
    primary_rows = source_rows(primary_ids,p_sessions,source,mappings,"primary_vf")
    vonly_rows = source_rows(vonly_ids,v_sessions,source,mappings,"vonly_reselected")
    fixed_rows = source_rows(fixed_ids,fixed_sessions,source,mappings,"fixed_primary_pair_strict_v")
    if [len(x) for x in (reference_rows,primary_rows,vonly_rows,fixed_rows)] != [545,520,450,410]: raise ValueError("source row counts changed")

    # Independently regenerate adopted 52-target seeded map and compare all identities/hashes.
    permutation = [str(x) for x in np.random.default_rng(42).permuted(np.array(primary_ids))]
    fold_map = {p:i%5 for i,p in enumerate(permutation)}
    corrected_b = {int(r["fold"]):r for r in read_csv(CORR/"crossfit_candidate_identity_maps.csv") if r["candidate_design_id"]=="B_seeded_targets52_plus_aux57"}
    fold_rows=[]
    for fold in range(5):
        held=sorted(p for p in primary_ids if fold_map[p]==fold); fitting=sorted(set(ref_ids)-set(held)); aux=sorted(set(ref_ids)-set(primary_ids))
        cr=corrected_b[fold]
        if held != cr["held_out_identity_list"].split(";") or fitting != cr["fitting_identity_list"].split(";") or ids_hash(held)!=cr["held_out_sha256"] or ids_hash(fitting)!=cr["fitting_sha256"]:
            raise ValueError(f"corrected Design-B identity mismatch fold {fold}")
        fold_rows.append({"reference_design":"B_target_plus_auxiliary","target_fold":fold,"fold_seed":42,
            "held_out_target_count":len(held),"auxiliary_count":len(aux),"training_count":len(fitting),
            "held_out_target_identities":";".join(held),"held_out_target_sha256":ids_hash(held),
            "auxiliary_identities":";".join(aux),"auxiliary_sha256":ids_hash(aux),
            "training_identities":";".join(fitting),"training_identities_sha256":ids_hash(fitting),"self_inclusion_count":len(set(held)&set(fitting))})
    participant_fold_rows=[]
    by_fold={int(r["target_fold"]):r for r in fold_rows}
    for pid in primary_ids:
        fold=fold_map[pid];fr=by_fold[fold]
        participant_fold_rows.append({"participant_id":pid,"reference_design":"B_target_plus_auxiliary","target_fold":fold,
            "primary_sessions":";".join(p_sessions[pid]),"same_fold_for_all_visits_and_strata":"yes",
            "held_out_target_count":fr["held_out_target_count"],"training_count":fr["training_count"],
            "held_out_target_sha256":fr["held_out_target_sha256"],"training_identities_sha256":fr["training_identities_sha256"],
            "is_excluded_from_own_fitting_set":"yes" if pid not in fr["training_identities"].split(";") else "no"})

    tasks_contract=[{"order":i+1,"task_key":t,"table":stem,"score_field":field,"qc_field":qc,"direction":direction} for i,(t,stem,field,qc,direction) in enumerate(TASKS)]
    contract={
      "schema_version":"1.0.0","status":"adopted_for_this_bounded_rebuild","authorization":"Researcher protocol adoption through the user-submitted execution prompt.",
      "reference_design":"B_target_plus_auxiliary","rng":{"library":"numpy","version":np.__version__,"generator":"default_rng","seed":42,"algorithm":"permuted(sorted 52 target IDs), permutation index modulo 5"},
      "inputs":{r["relative_path"]:r["sha256"] for r in manifest},"tasks":tasks_contract,
      "cohorts":{"reference_a":{"participants":109,"occasions":109,"rows":545,"rule":"earliest complete V/F non-continuation occasion"},
        "primary_vf":{"participants":52,"occasions":104,"rows":520,"rule":"first two complete V/F non-continuation occasions"},
        "vonly_reselected":{"participants":45,"occasions":90,"rows":450,"rule":"first two complete strict-V non-continuation occasions"},
        "fixed_primary_pair_strict_v":{"participants":41,"occasions":82,"rows":410,"rule":"Primary pair retained and all ten records strict V"}},
      "folds":fold_rows,"formulas":{"M0":{"role":"primary","center":"arithmetic_mean(y)","coordinate":"(y-center)/scale","age_support":"not_applicable"},
        "M1":{"role":"sensitivity","fit":"float64 OLS with intercept using numerically stable least squares","minimum_effective_n":3,"minimum_distinct_age":2,"prediction":"intercept+slope*age","residual":"y-prediction","residual_center":0,"support":"inclusive finite effective-training age min/max","fallback":"separately labelled corresponding M0"},
        "MAD":{"formula":"median(abs(v-median(v)))/0.6744897501960817","constant":0.6744897501960817},"SD":{"formula":"sample SD ddof=1"}},
      "numerical_policy":{"dtype":"IEEE float64","machine_epsilon":float(np.finfo(float).eps),"threshold":"scale <= 64*epsilon*max(D,abs(scale))","M0_D":"range of direction-adjusted training score","M1_D":"range of direction-adjusted effective training score","reject":["nonfinite_scale","nonpositive_scale","insufficient_scale_observations","numerically_degenerate_scale"],"no_clipping":True,"no_silent_scale_substitution":True},
      "unsupported_reason_codes":["missing_or_nonfinite_score","missing_or_nonfinite_target_age","outside_inclusive_training_age_support","insufficient_effective_training_data","rank_deficient_age_model","invalid_scale","nonfinite_prediction_or_residual"],
      "keys":{"parameter":["reference_design","target_fold","task_key","model","scale_method"],"long":["participant_id","analytical_stratum","session_id","task_key","model","scale_method"],"wide":["participant_id","analytical_stratum","session_id","model","scale_method"]},
      "expected_counts":{"parameters":100,"source_stratum_rows":1380,"long_rows":5520,"wide_rows":1104,"primary_vf":{"long":2080,"wide":416},"vonly_reselected":{"long":1800,"wide":360},"fixed_primary_pair_strict_v":{"long":1640,"wide":328}},
      "tolerance":{"absolute":1e-12,"relative":1e-10},"bootstrap":"deferred",
      "limitations":["internal sample-referenced task coordinates; not population or clinical z-scores","complete-case selection","repository-session age is not proven exact cognitive-assessment age","candidate comparability by repository session label only","LNB denominator/load uncertainty","CTAP unit/aggregation uncertainty","task-version/administration comparability uncertainty","M0/MAD adopted but not established optimal"]}
    contract_path=OUT/"step5ba_rebuild_contract.json"
    contract_path.write_text(json.dumps(contract,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    contract_hash=sha256(contract_path)
    adoption={"record_type":"protocol_adoption","status":"adopted_for_bounded_task_coordinate_rebuild","authorization_source":"Researcher protocol adoption through the user-submitted execution prompt.","date":"2026-10-01","contract_file":"step5ba_rebuild_contract.json","contract_sha256":contract_hash,"does_not_claim":["supervisor signature","institutional approval","historical approval"],"authorized_outputs":"task-coordinate transformation only","bootstrap":"deferred","downstream_profile_analysis":"not_authorized"}
    (OUT/"protocol_adoption_record.json").write_text(json.dumps(adoption,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    (OUT/"contract_sha256.txt").write_text(contract_hash+"  step5ba_rebuild_contract.json\n",encoding="utf-8",newline="\n")
    write_csv(OUT/"input_artifact_manifest.csv",manifest)
    write_csv(OUT/"reference_cohort_manifest.csv",reference_rows)
    write_csv(OUT/"participant_fold_manifest.csv",participant_fold_rows)
    write_csv(OUT/"fold_fitting_manifest.csv",fold_rows)
    write_csv(OUT/"primary_vf_source_rows.csv",primary_rows)
    write_csv(OUT/"vonly_reselected_source_rows.csv",vonly_rows)
    write_csv(OUT/"fixed_primary_pair_strict_v_source_rows.csv",fixed_rows)
    print(json.dumps({"contract_sha256":contract_hash,"input_files":len(manifest),"source_counts":[len(reference_rows),len(primary_rows),len(vonly_rows),len(fixed_rows)],"fold_training_counts":[r["training_count"] for r in fold_rows]},indent=2))


if __name__=="__main__": main()
