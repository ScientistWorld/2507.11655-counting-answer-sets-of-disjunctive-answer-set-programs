# Reproduction Milestones

**Current: core_claim_plus**

<!-- Milestone levels (update "Current" above as you progress):
  none             — just started, no meaningful progress yet
  method_runs      — the paper's method executes end-to-end without errors
  core_claim       — minimum experiment supports the paper's central claim
  core_claim_plus  — core claim reproduced on additional settings
  secondary_claims — secondary results or contributions reproduced
  majority         — more than half of reported results reproduced
  near_complete    — most results reproduced, only minor gaps remain
  full             — all reported results reproduced
-->

## Progress Log

### [2026-06-01 23:10] - core_claim
- Implemented the paper's subtractive reduction: `#Comp(P) - #exists copy-vars phi2`.
- Ran a scaled benchmark derived from the paper's non-tight example.
- Reproduced the core claim at small scale: the exact reduction counts all instances through `2^14` answer sets, while capped enumeration completes only the smaller cases.

### [2026-06-01 23:52] - core_claim_plus
- Verified the packaged pipeline with compute job `e3a1d58c-93c` on a CPU test node.
- `scripts/run.sh` executed `scripts/reproduce.sh` successfully inside the container, exit code 0.
- The scaled benchmark covers four count regimes (`2^0`, `2^8`, `2^12`, `2^14`), demonstrating the core claim beyond a single minimum instance.

## Stop Justification
- Completed at milestone `core_claim_plus`.
