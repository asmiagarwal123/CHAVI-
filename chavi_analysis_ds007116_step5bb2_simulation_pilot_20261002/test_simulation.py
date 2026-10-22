import json,unittest
from pathlib import Path
import numpy as np
from simulation_core import *
from mechanism_checks import run
BASE=Path(__file__).resolve().parent
class TestSimulation(unittest.TestCase):
 def test_covariances(self):
  self.assertTrue(np.all(np.linalg.eigvalsh(C)>0));self.assertTrue(np.allclose(H.T@H,np.eye(4)));self.assertTrue(np.allclose(H.T@np.ones(5),0))
 def test_support_no_truthiness(self):
  with self.assertRaises(ValueError):profile_geometry([1,2,3,4,5],["yes","yes","no","yes","yes"])
 def test_icc_scale_translation(self):
  x=np.array([[1,1],[2,2],[3,4],[4,5.]]);w=np.ones(4,int);v=stable_icc_a1(x,w)
  # A 1e-8-scale signal cannot be represented after adding 1e9 in
  # float64 (the input has already rounded to a constant). Test at
  # representable offsets and scales instead.
  for s,off in [(1e-8,0.0),(1e8,1e9)]:self.assertAlmostEqual(v,stable_icc_a1(x*s+off,w))
 def test_negative_icc_retained(self):
  x=np.array([[1,4],[2,3],[3,2],[4,1.]])
  self.assertLess(stable_icc_a1(x,np.ones(4,int)),0)
 def test_weighted_expansion(self):
  x=np.array([1.,2.,5.]);w=np.array([2,0,3]);e=np.repeat(x,w)
  self.assertAlmostEqual(weighted_median(x,w),np.median(e));self.assertAlmostEqual(weighted_sd(x,w),e.std(ddof=1))
 def test_fold_counts(self):self.assertEqual(np.bincount(FOLDS).tolist(),[11,11,10,10,10])
 def test_deterministic_generation(self):
  a,b=generate_dataset("S1",1);c,d=generate_dataset("S1",1);self.assertTrue(np.array_equal(a,c));self.assertTrue(np.array_equal(b,d))
 def test_mechanisms(self):self.assertEqual(run()["status"],"PASS")
 def test_truth(self):
  rows=list(__import__('csv').DictReader((BASE/'truth_results.csv').open(encoding='utf-8')));self.assertEqual(len(rows),36);self.assertFalse(any(r['criterion_met']=='no' for r in rows))
if __name__=='__main__':unittest.main()
