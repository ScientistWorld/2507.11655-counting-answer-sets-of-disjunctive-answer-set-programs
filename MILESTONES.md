# Reproduction Milestones
**Current: secondary_claims**

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

### [2026-06-01 23:19] - secondary_claims
- Container job `82247c77-a43` reran `scripts/reproduce.sh` successfully after the projected-counting and fresh-variable fixes.
- Verified the scaled hybrid secondary claim: capped enumeration completed the two easy instances, then sharpASP-sR solved the four fallback instances exactly.
- `python validate.py --compare` passes with both scored experiments aligned to the reusable scoring contract.

### [2026-06-01 23:46] - secondary_claims
- Added semantic regression checks comparing sharpASP-sR against brute-force answer-set enumeration on small disjunctive, cyclic, default-negation, and inconsistent programs.
- Local `method/selftest.py` and `python validate.py --compare` both pass before the next CPU container verification job.

### [2026-06-02 00:08] - secondary_claims
- Final verification passed after renaming the public structural scoring metric to the method-agnostic `avg_auxiliary_to_core_clause_ratio`.
- Revalidated top-level, train, and test evaluators plus method self-tests.

### [2026-11-08 03:40] - secondary_claims
- Hardening (iteration 11): rebuilt the test. Counters are registered via `checkpoints/<name>/counter.json` and run by the evaluators on 27 hidden programs (`eval/test/`, secret seed, salted answer digests) and 37 visible train programs under a fixed 10 CPU s budget; a program counts only when the printed count equals independently computed ground truth; any wrong/impossible count fails the run.
- Reference sharpASP-sR now uses GANAK (the paper's projected counter); baseline is clingo enumeration under the same budget; hybrid follows the paper's 10^4 threshold.
- Hidden test: large counts sharpASP-sR 7/14 vs enumeration 0/14; full spectrum hybrid 10/13 > sharpASP-sR 9/13 > enumeration 7/13; three runs identical. Better variants (one-copy surplus encoding, adaptive switching) score +0.35 to +3.0 above the reference; all REDTEAM shortcuts and weaker variants score below it. Details in `HARDENING.md`.

## Stop Justification
- Completed at milestone `secondary_claims`.
