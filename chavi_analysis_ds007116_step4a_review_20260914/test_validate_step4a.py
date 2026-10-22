import unittest
from validate_step4a import icc_anova, icc_component, pearson, ranks, spearman, stats
class TestIndependentValidation(unittest.TestCase):
 def test_icc_paths_agree_on_fixture(self):
  x,y=[1,2,4,5],[2,2,5,7]; a,c,_=icc_anova(x,y); b,d=icc_component(x,y); self.assertAlmostEqual(a,b,12);self.assertAlmostEqual(c,d,12)
 def test_known_association(self): self.assertAlmostEqual(pearson([1,2,3],[2,4,6]),1);self.assertAlmostEqual(spearman([1,1,2],[3,3,4]),1)
 def test_constant_is_undefined(self): self.assertIsNone(pearson([1,1],[2,3]));self.assertEqual(ranks([1,1,2]),[1.5,1.5,3])
 def test_ordered_change(self): self.assertEqual(stats([{"earlier":1,"later":3},{"earlier":2,"later":5}])["mean_difference"],2.5)
if __name__=='__main__':unittest.main()
