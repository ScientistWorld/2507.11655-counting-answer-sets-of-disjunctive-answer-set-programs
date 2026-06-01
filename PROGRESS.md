# Progress

## What Works

Implemented a scaled exact sharpASP-sR reproduction:

- Parser for ground disjunctive ASP rules.
- Positive dependency graph and loop-atom detection.
- Clark completion encoding.
- Two-copy surplus formula from the paper.
- Exact in-repo model and projected-model counters.
- Capped enumeration baseline for the scaled benchmark.
- Method-agnostic evaluation pipeline writing `scoring/scores.json`.

## Results

Local smoke result on the scaled benchmark:

- `sharpasp_sr`: 4/4 solved, exact count accuracy 1.0, largest solved count `2^14`.
- `enumeration_cap_1000`: 2/4 solved, exact count accuracy 0.5, largest completed count `2^8`.

Paper headline reference:

- sharpASP-sR: 825/1125 solved, PAR2 2939.
- clingo: 708/1125 solved, PAR2 4118.
- clingo + sharpASP-sR hybrid: 918/1125 solved, PAR2 1600.

## Remaining

The current reproduction uses a scaled synthetic benchmark derived from the paper's illustrative non-tight program, not the full 1125-instance benchmark suite or GANAK. A higher milestone would require obtaining the supplementary benchmark set and integrating an external projected model counter such as GANAK.

## Issues

No blocker for the scaled core claim. The full paper benchmark was reported as supplementary material but is not present in the provided workspace.

## Deviations from Paper

- Paper used GANAK as the projected model counter; this reproduction uses a small exact projected counter implemented in `method/sharpasp_sr/counter.py` so the environment is self-contained.
- Paper evaluated 1125 benchmark instances; this reproduction uses a small generated benchmark derived from the paper's Example 1 with independent disjunctive choices to demonstrate the same exact-counting scaling effect.
- Paper hybrid threshold was `10^4`; this scaled reproduction uses enumeration cap `10^3` to keep the smoke benchmark lightweight.
