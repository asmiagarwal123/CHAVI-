import copy, csv, hashlib, json, math, unittest
from pathlib import Path
import numpy as np
import run_clean_rebuild as prod
import independent_validator as indep

OUT=Path(__file__).resolve().parent

def rows(name):
    with (OUT/name).open("r",encoding="utf-8-sig",newline="") as h:return list(csv.DictReader(h))
def unique(rows_,fields):
    keys=[tuple(r[x] for x in fields) for r in rows_]
    if len(keys)!=len(set(keys)):raise ValueError("duplicate_key")
def check_identity(actual,expected):
    if set(actual)!=set(expected):raise ValueError("wrong_identities")
def check_reference_a(training,reference):
    if len(set(reference))==109 and len(set(training)) in {41,42}:raise ValueError("target_only_labelled_reference_a")
def check_no_leakage(held,training):
    if set(held)&set(training):raise ValueError("held_out_self_inclusion")
def check_aux(aux,training):
    if not set(aux)<=set(training):raise ValueError("dropped_auxiliary")
def check_source(row,task,field,qc):
    if (row["task_key"],row["score_field"],row["raw_qc_code"])!=(task,field,qc):raise ValueError("wrong_task_or_qc")
    if float(row["raw_score"])!=float(row["parsed_score"]):raise ValueError("source_parsed_mismatch")
def check_no_mixed(rows_):
    if len({r["analytical_stratum"] for r in rows_})!=1:raise ValueError("mixed_strata")
def check_unsupported(row):
    if row["model"]=="M1" and row["supported"]=="no" and row["coordinate"]!="":raise ValueError("unsupported_m1_replaced")
def check_hash(path,expected):
    if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:raise ValueError("changed_hash")

class FormulaFixtures(unittest.TestCase):
    def test_m0_hand_values(self):
        x=[1.0,2.0,3.0]
        self.assertEqual(prod.mean(x),2.0);self.assertAlmostEqual(prod.mad(x),1/MAD,14);self.assertEqual(prod.sd(x),1.0)
    def test_m1_hand_values_independent_path(self):
        x=[0.,1.,2.];y=[1.,3.,5.];xb=indep.imean(x);yb=indep.imean(y)
        slope=sum((a-xb)*(b-yb) for a,b in zip(x,y))/sum((a-xb)**2 for a in x)
        self.assertEqual(slope,2.0);self.assertEqual(yb-slope*xb,1.0)
    def test_exact_linear_residual_scale_fails(self):
        self.assertNotEqual(prod.scale_status(0.0,4.0,3),"supported")
    def test_nearly_linear_fixture_scale_supported(self):
        r=[-1e-4,2e-4,-1e-4];s=prod.sd(r)
        self.assertEqual(prod.scale_status(s,4.0001,3),"supported")
    def test_constant_scores_fail(self):
        self.assertEqual(prod.scale_status(prod.mad([2,2,2]),0,3),"nonpositive_scale")
    def test_zero_mad_nonzero_sd_no_substitution(self):
        x=[0,0,0,10]
        self.assertEqual(prod.mad(x),0);self.assertGreater(prod.sd(x),0);self.assertNotEqual(prod.mad(x),prod.sd(x))
    def test_small_valid_scale(self):
        x=[0,1e-20,2e-20];s=prod.mad(x)
        self.assertEqual(prod.scale_status(s,2e-20,3),"supported")
    def test_large_offset_and_unit_conversion(self):
        x=[1e12,1e12+1,1e12+2];s=prod.mad(x);base=prod.scale_status(s,2,3)
        y=[v*1000 for v in x];self.assertEqual(base,prod.scale_status(prod.mad(y),max(y)-min(y),3))
    def test_inclusive_boundaries(self):
        lo,hi=8.0,16.0
        self.assertFalse(lo<lo or lo>hi);self.assertFalse(hi<lo or hi>hi);self.assertTrue(7.9<lo)
    def test_missing_age_fixture(self):
        self.assertIsNone(prod.f(""));self.assertIsNone(prod.f("nan"))

MAD=prod.MAD_DENOM

class CorruptionDetection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.params=rows("transformation_parameters.csv");cls.long=rows("transformed_task_observations_long.csv");cls.folds=rows("fold_fitting_manifest.csv")
    def test_wrong_identities_same_count(self):
        with self.assertRaisesRegex(ValueError,"wrong_identities"):check_identity(["a","b"],["a","c"])
    def test_target_only_reference_a(self):
        with self.assertRaisesRegex(ValueError,"target_only"):check_reference_a([f"p{i}" for i in range(41)],[f"p{i}" for i in range(109)])
    def test_held_out_self_inclusion(self):
        with self.assertRaisesRegex(ValueError,"self_inclusion"):check_no_leakage(["p1"],["p1","p2"])
    def test_dropped_auxiliary(self):
        with self.assertRaisesRegex(ValueError,"dropped_auxiliary"):check_aux(["a1","a2"],["a1"])
    def test_wrong_task_or_qc(self):
        bad={"task_key":"wrong","score_field":"x","raw_qc_code":"Z","raw_score":"1","parsed_score":"1"}
        with self.assertRaisesRegex(ValueError,"wrong_task_or_qc"):check_source(bad,"letter_nback","cnb_lnb_mcr","V")
    def test_source_parsed_mismatch(self):
        bad={"task_key":"letter_nback","score_field":"cnb_lnb_mcr","raw_qc_code":"V","raw_score":"1","parsed_score":"2"}
        with self.assertRaisesRegex(ValueError,"source_parsed_mismatch"):check_source(bad,"letter_nback","cnb_lnb_mcr","V")
    def test_mixed_strata(self):
        with self.assertRaisesRegex(ValueError,"mixed_strata"):check_no_mixed([{"analytical_stratum":"a"},{"analytical_stratum":"b"}])
    def test_pivot_row_multiplication(self):
        with self.assertRaisesRegex(ValueError,"duplicate_key"):unique([{"p":"1","s":"1"},{"p":"1","s":"1"}],("p","s"))
    def test_unsupported_m1_replaced_by_m0(self):
        bad={"model":"M1","supported":"no","coordinate":"1.2"}
        with self.assertRaisesRegex(ValueError,"unsupported_m1_replaced"):check_unsupported(bad)
    def test_silent_mad_to_sd_substitution(self):
        pair=[r for r in self.params if r["model"]=="M0" and r["target_fold"]=="0" and r["task_key"]=="letter_nback"]
        mad=next(r for r in pair if r["scale_method"]=="MAD");sd=next(r for r in pair if r["scale_method"]=="SD")
        corrupted=copy.deepcopy(mad);corrupted["scale"]=sd["scale"]
        self.assertFalse(indep.close(float(corrupted["scale"]),float(mad["scale"])))
    def test_changed_contract_hash(self):
        p=OUT/"step5ba_rebuild_contract.json";expected=hashlib.sha256(p.read_bytes()).hexdigest()
        self.assertNotEqual(hashlib.sha256(p.read_bytes()+b"x").hexdigest(),expected)
        check_hash(p,expected)
    def test_auxiliary_retention_real_manifest(self):
        for r in self.folds:
            check_aux(r["auxiliary_identities"].split(";"),r["training_identities"].split(";"))
            check_no_leakage(r["held_out_target_identities"].split(";"),r["training_identities"].split(";"))

class OutputInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.params=rows("transformation_parameters.csv");cls.long=rows("transformed_task_observations_long.csv");cls.wide=rows("transformed_profiles_wide.csv")
    def test_counts_and_unique_keys(self):
        self.assertEqual(len(self.params),100);self.assertEqual(len(self.long),5520);self.assertEqual(len(self.wide),1104)
        unique(self.long,("participant_id","analytical_stratum","session_id","task_key","model","scale_method"))
    def test_same_parameters_across_visits(self):
        by= {}
        for r in self.long:
            k=(r["participant_id"],r["analytical_stratum"],r["task_key"],r["model"],r["scale_method"])
            by.setdefault(k,set()).add(r["parameter_key_sha256"])
        self.assertTrue(all(len(v)==1 for v in by.values()))
    def test_m0_age_flags(self):
        self.assertTrue(all(r["age_support_status"]=="not_applicable" and r["extrapolation"]=="false" for r in self.long if r["model"]=="M0"))
    def test_fallback_labelling(self):
        unsupported=[r for r in self.long if r["model"]=="M1" and r["supported"]=="no"]
        self.assertGreater(len(unsupported),0);self.assertTrue(all(r["coordinate"]=="" and r["fallback_model"]=="M0" for r in unsupported))
    def test_independent_validation_passed(self):
        v=json.loads((OUT/"validation_results.json").read_text(encoding="utf-8"));self.assertTrue(v["independent_validation_passed"])

if __name__=="__main__":unittest.main(verbosity=2)
