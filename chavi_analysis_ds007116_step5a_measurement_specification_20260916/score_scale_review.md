# Score-scale review (Step 5A)

The five selected fields were read from the pinned local JSON dictionaries. The dictionaries provide exact field names and LongName text, but they do not consistently document theoretical ranges or directional transformations. Observed minima and maxima in `score_semantics_and_direction.csv` are descriptive raw-value ranges only and must not be treated as validated scale bounds.

The Penn CNB official Explore Tests page supplies task context: Letter N-back, Face Memory, Matrix Reasoning, Emotion Identification, and Finger Tapping are described there. The official page supports the task context and trial descriptions, not undocumented denominator or scoring transformations. The local CTAP LongName says “Mean of Dominant Hand Trials”; combined with the official press-per-10-second task description, this supports a positive faster-performance direction, while the exact unit/aggregation remains a confirmation item. No score was reversed, standardized, centered, or combined in Step 5A.

Sources: [https://webcnp.med.upenn.edu/explore-tests.html](https://webcnp.med.upenn.edu/explore-tests.html), [https://webcnp.med.upenn.edu/manual.html](https://webcnp.med.upenn.edu/manual.html), [https://github.com/OpenNeuroDatasets/ds007116/releases/tag/1.0.6](https://github.com/OpenNeuroDatasets/ds007116/releases/tag/1.0.6).
