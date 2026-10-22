# ICC formula validation

For n participants and k=2 ordered occasions, the ANOVA path uses MS_R (participant), MS_C (occasion), and MS_E (residual):

- ICC(A,1) = (MS_R − MS_E) / [MS_R + (k−1)MS_E + k(MS_C−MS_E)/n].
- ICC(C,1) = (MS_R − MS_E) / [MS_R + (k−1)MS_E].

An independent component path calculates MS_E from centred within-person differences and MS_C from the two column means. On the hand-checkable fixture earlier=[1,2,4,5], later=[2,2,5,7], ANOVA gives A=0.852459016393442, C=0.928571428571428; component path gives A=0.852459016393442, C=0.928571428571428; absolute discrepancies are 0 and 0, both within 1e-10.

Applying ICC(A,1) here assumes the two ordered session-labelled occasions are exchangeable measurements of a stable enough construct apart from occasion effects, participant rows are independent, score scale is comparable, and residual variance is interpretable across variable intervals. The release metadata do not establish equal intervals, identical task versions, or identical conditions. Thus this is longitudinal agreement across observed follow-up occasions, **not** pure short-interval test–retest reliability.
