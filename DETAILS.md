# Overview

- **Paper ID:** 2507.11655
- **Title:** Counting Answer Sets of Disjunctive Answer Set Programs
- **Domain:** Knowledge Representation / Answer Set Programming / Exact Counting
- **TL;DR:** The paper counts answer sets of disjunctive ASP programs exactly by subtracting projected-counted non-answer-set completion models from a completion-model overcount.

## Short Summary

The paper targets exact answer-set counting for non-tight disjunctive ASP programs, a setting where enumeration and counters for normal programs do not scale well. It defines a loop-atom copy construction that identifies surplus Clark-completion models that are not stable models. The resulting sharpASP-sR counter reduces the problem to projected model counting and outperforms clingo, Wasp, and DynASP on the paper's benchmark suite.

## Key Results

- On 1125 benchmark instances, sharpASP-sR solves 825 instances versus 708 for clingo, 432 for Wasp, and 89 for DynASP.
- The hybrid clingo plus sharpASP-sR approach solves 918 instances with PAR2 1600.
- The paper reports sharpASP-sR counting instances up to roughly `2^127` answer sets, while enumeration systems time out at much lower counts.

---

# Problem Definition

## Research Question

Count the number of answer sets of a finite ground disjunctive Answer Set Programming (ASP) program exactly. The hard case is non-tight programs (positive cycles among atoms), where stable-model minimality matters: classical models of the program's completion can outnumber its answer sets, and enumerating answer sets one by one becomes infeasible when there are many of them.

## Why It Matters

Exact answer-set counts are used in probabilistic reasoning, network reliability, answer-set navigation, and other ASP applications. Disjunctive programs are more expressive than normal programs (answer-set checking is co-NP-hard, counting is #·co-NP-complete), and practical exact counters for them are scarce.

## Success Criteria

A counter succeeds on a program when it prints the exact number of answer sets within a fixed per-program resource budget. Wrong counts are not partially credited: exactness is a hard constraint, and any wrong or impossible count invalidates a run. Better counters solve more programs under the same budget, including programs whose counts are far beyond what enumeration can reach and programs with many cyclic (loop) atoms.

---

# Paper's Method

## Key Contribution

The paper introduces sharpASP-sR, an exact counter for disjunctive ASP programs based on a subtractive reduction to projected propositional model counting.

## Approach

For a program `P`, the method builds Clark completion `Comp(P)` and counts its models as an overcount. It then constructs a surplus formula `phi2` using two copies (`x'`, `x*`) of every loop atom of the positive dependency graph; `phi2`'s models projected onto the program atoms are exactly the completion models that are not answer sets. The final answer-set count is:

`|AS(P)| = #Comp(P) - #exists_{CV' u CV*} phi2`.

This reproduction implements that reduction (`method/sharpasp_sr/reduction.py`) and, like the paper's prototype, uses GANAK (v2.8.0, exact mode `--prob 0`) as the (projected) model counter (`method/sharpasp_sr/ganak.py`). Counter interface: `method/count.py --mode direct|hybrid PROGRAM.lp`. The hybrid mode follows the paper: clingo enumeration up to 10^4 answer sets, then sharpASP-sR.

## Main Claims

Primary claim: the subtractive projected-counting approach is exact and solves more programs than enumeration, in particular programs with large answer-set counts.

Secondary claims: a hybrid that enumerates small-count cases and falls back to sharpASP-sR solves more than either component; sharpASP-sR's performance degrades as the number of loop atoms grows.

---

# Evaluation

## What is measured

Counters are evaluated by **running them** on ground disjunctive ASP programs. Each program has an exact answer-set count computed independently of any counter under evaluation (exhaustive enumeration with a long budget, or an independent propositional formulation for programs with very many answer sets). A counter solves a program when it prints that exact count within the budget.

- **Budget:** 10 CPU seconds per program (the counter process plus every child process it waits for), hard wall-clock kill at 20 seconds. The same budget applies to every counter, including the baselines. The paper used 5000 s and 8 GB per instance; the programs here are scaled down accordingly.
- **Programs:** two families modelled on the paper's benchmark suite: existential-universal 2QBF problems in the standard disjunctive saturation encoding, and random non-tight disjunctive programs (with default negation, or positive programs with integrity constraints). Atom names are randomized and rules shuffled. Programs on which the reference counters finish close to the budget were excluded, so outcomes do not hinge on small timing differences.
- **Splits:** visible train programs in `data/train/` (with exact counts in `data/train/manifest.json`); hidden test programs in `eval/test/` (not available during development; same families, same budget, a different random draw).

## Experiments (slices) and metrics

| Experiment | Programs | What it probes |
|---|---|---|
| `large_count_counting` | at least 2^23 answer sets | counting far beyond what enumeration reaches under the budget |
| `hybrid_full_spectrum` | small, mid and large counts; about half are programs with many (30-120) loop atoms | a counter that must work across the whole count spectrum |

Metrics per experiment (all computed by the evaluator from the printed counts):

- `solved_instances` (primary): programs whose exact count was printed within budget.
- `max_log2_count_solved`: log2 of the largest exactly-solved count.
- `wrong_count_instances` (constraint): programs answered within budget with a wrong count or an impossible value (negative, fractional, nan/inf). **Any wrong or impossible count on a split fails the whole run on that split: its `solved_instances` and `max_log2_count_solved` are set to 0 in every experiment.** Printing nothing (or exiting non-zero) is "no answer" and is not penalized beyond not solving the program.

Rank: for each experiment, sum of `coefficient x (your value - reference value)` over its metrics (coefficients in `scoring/reference.json`: 1.0, 0.02, -1.0), weighted by the experiment weight (0.45 and 0.35).

## Counter interface

Register a counter by writing `checkpoints/<name>/counter.json`:

```json
{"command": ["python", "path/to/your_counter.py", "--any", "flags"]}
```

The evaluator appends the path of one ground program (a temporary copy) and runs the command from `/home/user` with `PYTHONPATH=/home/user`. Print the exact number of answer sets as the **last non-empty stdout line** (a plain non-negative integer) and exit 0. A leading `python` is replaced by the evaluator's interpreter.

Program syntax (ground rules only): `a | b :- c, not d.` (disjunctive head, positive and default-negated body literals), facts `a.` / `a | b.`, and integrity constraints `:- a, not b.`. `data/asp.py` has a parser and a brute-force reference for tiny programs.

Available tools in the container: clingo 5.8.3 (Python package) and the GANAK v2.8.0 exact projected model counter (`data/downloads/ganak`, fetched by `scripts/download.sh`; use `--prob 0` for deterministic exact counts).

## Baselines and reference counters (registered by `scripts/baseline.sh` and `scripts/method.sh`)

- `clingo_enumeration`: enumerates every answer set with clingo under the budget (the paper's enumeration baseline).
- `sharpasp_sr`: the paper's exact counter.
- `hybrid_sharpasp_sr`: the paper's hybrid: enumerate up to 10^4 answer sets, otherwise fall back to the exact counter.

## Protocol

```bash
bash scripts/download.sh          # once, with internet (GANAK binary)
bash scripts/baseline.sh          # registers clingo_enumeration, scores train
bash scripts/method.sh            # registers the reference counters, scores train
bash scripts/evaluate.sh          # scores every registered counter on train -> scoring/scores.json
bash scripts/evaluate_train.sh    # same, -> scoring/scores_train.json
bash scripts/evaluate_test.sh     # hidden test (graders) -> scoring/scores_test.json
```

The evaluators never import `method/` and never read anything a counter writes other than its printed count.

---

# Reproduction Log

### Iteration 1: gpt-5.5
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 8m | **GPU**: 0.0h
- **Jobs**: 1 total (1 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-01 23:10] - core_claim
- Implemented the paper's subtractive reduction: `#Comp(P) - #exists copy-vars phi2`.
- Ran a scaled benchmark derived from the paper's non-tight example.
- Reproduced the core claim at small scale: the exact reduction counts all instances through `2^14` answer sets, while capped enumeration completes only the smaller cases.

### [2026-06-01 23:52] - core_claim_plus
- Verified the packaged pipeline with compute job `e3a1d58c-93c` on a CPU test node.
- `scripts/run.sh` executed `scripts/reproduce.sh` successfully inside the container, exit code 0.
- The scaled benchmark covers four count regimes (`2^0`, `2^8`, `2^12`, `2^14`), demonstrating the core claim beyond a single minimum instance.

</details>

### Iteration 2: gpt-5.5
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 7m | **GPU**: 0.0h
- **Jobs**: 3 total (2 completed, 1 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-01 22:55] - core_claim
- Implemented sharpASP-sR's subtractive reduction: Clark-completion overcount minus projected surplus over two loop-atom copy formulas.
- Ran the scaled non-tight disjunctive benchmark end-to-end; sharpASP-sR exactly counted all four instances up to `2^14` answer sets while capped enumeration completed two.
- Packaged method, baseline, evaluation, scoring, and scripts for a reusable CPU-only environment.

### [2026-06-01 22:57] - core_claim_plus
- Audited the workspace and confirmed the proposed method implements the paper's overcount-minus-projected-surplus reduction rather than a surrogate.
- Fixed the capped enumeration baseline so it infers independent binary choices from parsed ASP rules instead of using manifest expected-count metadata.
- Expanded the scaled benchmark to six settings, reaching `2^20` answer sets; sharpASP-sR solved all six exactly while capped enumeration completed two.

### [2026-06-01 23:02] - secondary_claims
- Added and compute-verified the paper's hybrid strategy on the scaled benchmark: enumerate up to 1000 answer sets, then fall back to sharpASP-sR.
- Job `42bdeff0-173` completed successfully in the container and regenerated `scoring/scores.json`.
- Hybrid solved all six scaled instances exactly, handled two by enumeration, and used sharpASP-sR fallback for four larger-count instances.

</details>

### Iteration 3: gpt-5.5
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 8m | **GPU**: 0.0h
- **Jobs**: 4 total (3 completed, 1 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 4: gpt-5.5 (designer_stage_1)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 4 total (3 completed, 1 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 5: gpt-5.5 (designer_stage_2)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 5m | **GPU**: 0.0h
- **Jobs**: 4 total (3 completed, 1 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 6: gpt-5.5 (designer_stage_3)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 1m | **GPU**: 0.0h
- **Jobs**: 5 total (4 completed, 1 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 7: gpt-5.5 (packager)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 1m | **GPU**: 0.0h
- **Jobs**: 5 total (4 completed, 1 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 8: gpt-5.5 (verifier)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 5m | **GPU**: 0.0h
- **Jobs**: 5 total (4 completed, 1 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 9: gpt-5.5 (verifier)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 7m | **GPU**: 0.0h
- **Jobs**: 5 total (4 completed, 1 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 10: gpt-6.1-sol (redteam)
- **Milestone**: `secondary_claims` | **Status**: done
- **Working time**: 8m | **GPU**: 0.0h
- **Jobs**: 5 total (4 completed, 1 failed)

<details>
<summary>Progress Log</summary>

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

</details>


---

# Reproduction Milestones

**Current: secondary_claims**

## Stop Justification
- Completed at milestone `secondary_claims`.
