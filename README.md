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

Count the number of answer sets of a finite ground disjunctive Answer Set Programming (ASP) program exactly. The challenge is to handle non-tight programs where stable-model minimality matters and where plain answer-set enumeration becomes infeasible when the number of answer sets is large.

## Why It Matters

Exact answer-set counts are used in probabilistic reasoning, network reliability, answer-set navigation, and other ASP applications. Disjunctive programs are more expressive than normal programs, but practical exact counters for them are limited.

## Success Criteria

Successful systems must return exact counts, agree with enumeration on small instances, and scale to instances with many answer sets under fixed resource limits. Evaluation should also track structural difficulty, especially positive cycles, so improvements cannot be achieved by silently ignoring the hard non-tight cases.

---

# Paper's Method

## Key Contribution

The paper introduces sharpASP-sR, an exact counter for disjunctive ASP programs based on a subtractive reduction to projected propositional model counting.

## Approach

For a program `P`, the method builds Clark completion `Comp(P)` and counts its models as an overcount. It then constructs a surplus formula using two copies of the loop atoms in the positive dependency graph. The surplus formula captures models of the completion that are not answer sets, and projected model counting counts each original interpretation once. The final answer-set count is:

`|AS(P)| = #Comp(P) - #exists_{copy variables} phi2`.

This reproduction implements the same reduction and uses a small exact in-repo projected counter for the scaled benchmark rather than GANAK.

## Main Claims

Primary claim: the subtractive projected-counting approach is exact and scales better than enumeration on disjunctive programs with large answer-set counts.

Secondary claims: a hybrid strategy that enumerates only small-count cases and falls back to sharpASP-sR solves more instances, and sharpASP-sR performance is sensitive to the number of loop atoms.

---

# Evaluation

## Metrics

- `solved_instances`: number of benchmark instances for which an exact count is returned.
- `exact_count_accuracy`: fraction of scaled benchmark instances whose returned count equals the known exact count.
- `max_log2_count_solved`: largest solved answer-set count, reported as base-2 logarithm.
- `par2`: paper metric for timeout-penalized runtime; lower is better. It is retained in `reference.json` but not used as a reproduced score because wall-clock speed is hardware dependent.
- Structural constraint diagnostics: average number of loop atoms and generated formula-size ratio.

## Baselines and Targets

The paper compares exact counting against clingo, DynASP, and Wasp on 1125 non-tight disjunctive instances. The headline target is higher solved count than enumeration-based systems while preserving exactness. This workspace includes a scaled enumeration baseline with an answer-set cap, mirroring the paper's observation that enumeration degrades when counts grow.

The paper also evaluates a hybrid strategy that enumerates answer sets up to a threshold and invokes sharpASP-sR only when enumeration exceeds that threshold. This workspace reproduces that secondary claim on the scaled benchmark with a cap of 1000.

## Evaluation Protocol

Run `scripts/reproduce.sh` to generate the scaled benchmark, run the capped enumeration baseline, run the proposed exact counter, and write `scoring/scores.json`. The scaled benchmark ranges from the paper's illustrative non-tight program through independent-choice extensions with up to `2^20` answer sets. Future methods should write the same result artifact format under `checkpoints/<method>/results.json` and then call `scripts/evaluate.sh`. Evaluation code must not import from `method/`.

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


---

# Reproduction Milestones

**Current: secondary_claims**

## Stop Justification
- Completed at milestone `secondary_claims`.
