# CHAVI Step 1B payload retrieval and verification

Audit time (UTC): `2026-09-07T07:50:32.287095+00:00`  
Dataset: `C:\Users\asmi\Desktop\Projects\ML Projects\ds007116`  
Pinned Git target: `fc7dc36fa2598b0b2e4579baef37d148cc085207` / tag `1.0.6`  
Retrieval source: official OpenNeuro public S3 prefix `s3://openneuro.org/ds007116/phenotype/`  
Staging directory: `C:\Users\asmi\Desktop\Projects\ML Projects\chavi_step1b_phenotype_staging_20260907`

## Result

- Expected phenotype TSVs from the pinned checkout: **41**.
- Retrieved into staging: **41**.
- Verified against expected SHA-256E key size/hash: **41**.
- Parseable by the repaired audit: **41**.
- Failed or discrepant payloads: **0**.

Every verified payload matched both the byte size and SHA-256 encoded in the annex key committed at the pinned Git checkout. The S3 path was not treated as historical snapshot proof by itself; the content-addressed key comparison is the verification step. Payloads were not copied over tracked pointer files, so the dataset's branch, commit, and tracked scientific content remain unchanged.

## Method and provenance

DataLad and git-annex were not installed locally. The documented OpenNeuro fallback was used: retrieve only the phenotype prefix into staging, compare each payload with its pinned annex key, and parse only verified payloads. Each file's URL, command, retrieval timestamp, expected key, actual size/hash, and result is in `retrieval_manifest.csv`.

Official documentation says OpenNeuro snapshots are Git tags and annex content is retrieved through DataLad/git-annex or the OpenNeuro storage remote. It also warns that direct Git transfer does not transfer annex objects. The direct S3 command used here was limited to the phenotype prefix.

## Synthetic software tests

`audit_v2.py --fixture-only` passed tests for an unavailable pointer, a resolved annex payload, and a real TSV containing a missing value, duplicate key, and unknown QC code. Fixtures are created in a temporary directory and are not retained in the scientific output.
