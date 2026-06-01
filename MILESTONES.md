# Reproduction Milestones

**Current: core_claim**

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

## Stop Justification
- Not stopped; current submission will rerun the packaged pipeline in the compute environment.
