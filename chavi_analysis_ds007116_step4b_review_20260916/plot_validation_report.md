# Step 4B plot validation report

All 20 Step 4B PNG/SVG plots were checked programmatically for task label, score field, sample size, required reference lines, SVG title, and point count. Original-plot failures: 5.

Visual review requirement: representative scatter and Bland-Altman plots were inspected for clipping and axis configuration. The original Step 4B Bland-Altman PNG annotations omit the exact score-field token required by the contract; reviewed copies with corrected field metadata were created in this directory and the original Step 4B plots were not overwritten.

| File | Type | Metadata | Points | Status |
|---|---|---|---|---|
| letter_nback_earlier_later_scatter.svg | scatter | pass | pass | pass |
| letter_nback_earlier_later_scatter.png | scatter | pass | pass | pass |
| letter_nback_bland_altman.svg | difference | pass | pass | pass |
| letter_nback_bland_altman.png | difference | fail | pass | fail |
| face_memory_earlier_later_scatter.svg | scatter | pass | pass | pass |
| face_memory_earlier_later_scatter.png | scatter | pass | pass | pass |
| face_memory_bland_altman.svg | difference | pass | pass | pass |
| face_memory_bland_altman.png | difference | fail | pass | fail |
| matrix_reasoning_earlier_later_scatter.svg | scatter | pass | pass | pass |
| matrix_reasoning_earlier_later_scatter.png | scatter | pass | pass | pass |
| matrix_reasoning_bland_altman.svg | difference | pass | pass | pass |
| matrix_reasoning_bland_altman.png | difference | fail | pass | fail |
| emotion_recognition_earlier_later_scatter.svg | scatter | pass | pass | pass |
| emotion_recognition_earlier_later_scatter.png | scatter | pass | pass | pass |
| emotion_recognition_bland_altman.svg | difference | pass | pass | pass |
| emotion_recognition_bland_altman.png | difference | fail | pass | fail |
| dominant_finger_tapping_earlier_later_scatter.svg | scatter | pass | pass | pass |
| dominant_finger_tapping_earlier_later_scatter.png | scatter | pass | pass | pass |
| dominant_finger_tapping_bland_altman.svg | difference | pass | pass | pass |
| dominant_finger_tapping_bland_altman.png | difference | fail | pass | fail |
