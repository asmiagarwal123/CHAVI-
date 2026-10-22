# Code lineage and independence review

The CSV lineage outputs record every discovered Python script. Static evidence flags `replace()`/copy language, production imports, production-generated parameter reads, and shared helpers. A copied script with string replacements is not independent; self-comparison against production-generated parameters is not independent. No independent validator was accepted as verification.
