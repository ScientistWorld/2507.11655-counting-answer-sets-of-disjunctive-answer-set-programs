# Reproduction Milestones
**Current: core_claim_plus**

## Progress Log

### [2026-06-01 22:43] - none
- Started from a partial workspace for the sharpASP-sR paper.
- Identified the central claim: exact counting for non-tight disjunctive ASP via subtractive reduction to projected model counting.

### [2026-06-01 22:58] - method_runs
- Implemented and ran the paper's actual computation at scaled size: Clark completion overcount, loop-atom copy formulas, projected surplus counting, and subtraction.
- Added a capped enumeration baseline using shared ASP semantics outside `method/`.

### [2026-06-01 23:02] - core_claim
- Verified the scaled generated benchmark end to end in the compute container.
- sharpASP-sR counted all benchmark instances exactly while capped enumeration stopped after small-count cases.

### [2026-06-01 23:02] - core_claim_plus
- Added and verified the scaled hybrid experiment: enumerate easy instances first, then fall back to sharpASP-sR.
- Scope note: this milestone is for the scaled generated benchmark derived from the paper example, not the full 1125-instance benchmark with GANAK.

### [2026-06-01 23:18] - core_claim_plus
- Fixed the in-repo projected model counter so unconstrained projected variables are counted correctly.
- Fixed fresh-variable allocation for copy and auxiliary variables so program atoms cannot collide with `Copy(P)`.
- Added `method/selftest.py` regression checks for projected counting, the paper example, and copy-variable freshness before the next container job.

## Stop Justification
- Not stopped. A CPU test job is being submitted to regenerate artifacts after the projected-counting fix.
