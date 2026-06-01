# Reproduction Milestones

**Current: core_claim_plus**

## Progress Log

### [2026-06-01 22:55] - core_claim
- Implemented sharpASP-sR's subtractive reduction: Clark-completion overcount minus projected surplus over two loop-atom copy formulas.
- Ran the scaled non-tight disjunctive benchmark end-to-end; sharpASP-sR exactly counted all four instances up to `2^14` answer sets while capped enumeration completed two.
- Packaged method, baseline, evaluation, scoring, and scripts for a reusable CPU-only environment.

### [2026-06-01 22:57] - core_claim_plus
- Audited the workspace and confirmed the proposed method implements the paper's overcount-minus-projected-surplus reduction rather than a surrogate.
- Fixed the capped enumeration baseline so it infers independent binary choices from parsed ASP rules instead of using manifest expected-count metadata.
- Expanded the scaled benchmark to six settings, reaching `2^20` answer sets; sharpASP-sR solved all six exactly while capped enumeration completed two.

## Stop Justification
- Completed at milestone `core_claim_plus`.
