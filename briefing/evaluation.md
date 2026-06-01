# Evaluation

## Metrics

- `solved_instances`: number of benchmark instances for which an exact count is returned.
- `exact_count_accuracy`: fraction of scaled benchmark instances whose returned count equals the known exact count.
- `max_log2_count_solved`: largest solved answer-set count, reported as base-2 logarithm.
- `par2`: paper metric for timeout-penalized runtime; lower is better. It is retained in `reference.json` but not used as a reproduced score because wall-clock speed is hardware dependent.
- Structural constraint diagnostics: average number of loop atoms and generated formula-size ratio.

## Baselines and Targets

The paper compares exact counting against clingo, DynASP, and Wasp on 1125 non-tight disjunctive instances. The headline target is higher solved count than enumeration-based systems while preserving exactness. This workspace includes a scaled enumeration baseline with an answer-set cap, mirroring the paper's observation that enumeration degrades when counts grow.

## Evaluation Protocol

Run `scripts/reproduce.sh` to generate the scaled benchmark, run the capped enumeration baseline, run the proposed exact counter, and write `scoring/scores.json`. Future methods should write the same result artifact format under `checkpoints/<method>/results.json` and then call `scripts/evaluate.sh`. Evaluation code must not import from `method/`.
