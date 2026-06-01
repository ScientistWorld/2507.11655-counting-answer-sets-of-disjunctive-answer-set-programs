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
- Shared ASP parsing and answer-set semantics live in `data/asp.py`, so the baseline does not import the proposed method.

## Results

Local smoke result on the expanded scaled benchmark:

- `sharpasp_sr`: 6/6 solved, exact count accuracy 1.0, largest solved count `2^20`.
- `enumeration_cap_1000`: 2/6 solved, exact count accuracy 0.3333333333333333, largest completed count `2^8`.
- Local hybrid result: `enumeration_then_sharpasp_sr` solved 6/6 exactly, handled two instances by enumeration, and fell back to sharpASP-sR on four instances.

Compute verification:

- Job `e3a1d58c-93c` ran `bash /home/user/scripts/run.sh` inside the container.
- Exit code: 0.
- Duration: 22.8 seconds on a CPU test node.
- The job regenerated the same `scoring/scores.json` structure used by local validation.

Paper headline reference:

- sharpASP-sR: 825/1125 solved, PAR2 2939.
- clingo: 708/1125 solved, PAR2 4118.
- clingo + sharpASP-sR hybrid: 918/1125 solved, PAR2 1600.

## Remaining

The current reproduction uses a scaled synthetic benchmark derived from the paper's illustrative non-tight program, not the full 1125-instance benchmark suite or GANAK. The hybrid secondary claim is implemented locally and is being submitted for compute verification. A higher milestone beyond `secondary_claims` would require obtaining the supplementary benchmark set and integrating an external projected model counter such as GANAK.

## Issues

No blocker for the scaled core claim. During continuation audit, the capped enumeration baseline was found to use manifest count metadata for generated choice instances; this was fixed so it now infers independent binary choice facts from the parsed program and counts extensions from executable ASP semantics. Job `da9a1309-c57` failed because the container did not resolve the workspace `data` module when running `baseline/enumerate.py`; the fix adds `data/__init__.py` and exports `/home/user` on `PYTHONPATH` in all entrypoint scripts. The full paper benchmark was reported as supplementary material but is not present in the provided workspace. The job logs contain Hive metadata only because the scripts run quietly on success; the result artifact and zero exit code verify completion.

## Deviations from Paper

- Paper used GANAK as the projected model counter; this reproduction uses a small exact projected counter implemented in `method/sharpasp_sr/counter.py` so the environment is self-contained.
- Paper evaluated 1125 benchmark instances; this reproduction uses a small generated benchmark derived from the paper's Example 1 with independent disjunctive choices to demonstrate the same exact-counting scaling effect.
- Paper hybrid threshold was `10^4`; this scaled reproduction uses enumeration cap `10^3` to keep the smoke benchmark lightweight.
