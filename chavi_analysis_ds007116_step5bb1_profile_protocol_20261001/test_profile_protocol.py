from __future__ import annotations
import csv, importlib.util, json, math, unittest
from pathlib import Path

BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("pe",BASE/"profile_estimands.py")
pe=importlib.util.module_from_spec(spec);spec.loader.exec_module(pe)

class TestProfileProtocol(unittest.TestCase):
 def test_helmert(self):
  import numpy as np
  self.assertTrue(np.allclose(pe.H.T@pe.H,np.eye(4),atol=1e-12))
  self.assertTrue(np.allclose(pe.H.T@np.ones(5),0,atol=1e-12))
 def test_geometry(self):
  g=pe.profile_geometry([1,2,3,4,5]);self.assertEqual(g["level"],3);self.assertAlmostEqual(g["scatter"],math.sqrt(2))
  self.assertTrue(all(abs(x-y)<1e-12 for x,y in zip(pe.H@g["contrasts"],g["centered_shape"])))
 def test_pair_identity(self):
  p=pe.pair_geometry([1,2,3,4,5],[3,3,4,7,8])
  self.assertAlmostEqual(p["total_displacement"]**2,p["delta_level"]**2+p["shape_displacement"]**2)
 def test_flat(self): self.assertIsNone(pe.profile_correlation([2]*5,[1,2,3,4,5]))
 def test_missing_support(self):
  with self.assertRaises(ValueError):pe.profile_geometry([1,2,3,4,5],[1,1,0,1,1])
 def test_support_counts(self):
  with (BASE/"profile_pair_support_summary.csv").open(encoding="utf-8",newline="") as f:r=list(csv.DictReader(f))
  got={(x["analytical_stratum"],x["coordinate_model"],x["scale_method"]):int(x["complete_supported_pairs"]) for x in r}
  for scale in ["MAD","SD"]:
   self.assertEqual(got[("primary_vf","M1",scale)],42);self.assertEqual(got[("vonly_reselected","M1",scale)],36);self.assertEqual(got[("fixed_primary_pair_strict_v","M1",scale)],33)
 def test_validator_results(self):
  d=json.loads((BASE/"validation_results.json").read_text(encoding="utf-8"));self.assertEqual(d["status"],"PASS");self.assertGreaterEqual(d["checks_passed"],20)
 def test_spec_status(self):
  d=json.loads((BASE/"profile_analysis_specification_recommended.json").read_text(encoding="utf-8"));self.assertEqual(d["status"],"RECOMMENDED SCIENTIFIC PROTOCOL — NOT YET ADOPTED FOR EMPIRICAL EXECUTION.")
 def test_no_empirical_outputs(self):
  banned=("empirical_profile","profile_icc_results","bootstrap_results","monte_carlo_results")
  self.assertFalse(any(any(b in p.name.lower() for b in banned) for p in BASE.rglob("*")))

if __name__=="__main__":unittest.main()
