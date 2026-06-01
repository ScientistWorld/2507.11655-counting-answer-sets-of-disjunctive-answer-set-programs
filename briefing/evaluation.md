# Evaluation

## Metrics

- `solved_instances`: number of benchmark instances for which an exact count is returned.
- `exact_count_accuracy`: fraction of scaled benchmark instances whose returned count equals the known exact count.
- `max_log2_count_solved`: largest solved answer-set count, reported as base-2 logarithm.
- `par2`: paper-reported timeout-penalized runtime. It is retained only as historical context in `reference.json`; it is not assigned scoring weight because wall-clock speed is hardware dependent.
- Structural constraint diagnostics: average number of loop atoms and generated formula-size ratio.

## Baselines and Targets

The paper compares exact counting systems on 1125 non-tight disjunctive instances. The headline target is higher solved count than enumeration-based systems while preserving exactness. This workspace includes a scaled enumeration baseline with an answer-set cap, mirroring the observation that enumeration degrades when counts grow.

The paper also evaluates a hybrid strategy that enumerates answer sets up to a threshold and invokes an exact fallback counter only when enumeration exceeds that threshold. This workspace reproduces that secondary claim on the scaled benchmark with a cap of 1000.

## Evaluation Protocol

Run `scripts/reproduce.sh` to generate the scaled benchmark, run the capped enumeration baseline, run an exact counter, and write `scoring/scores.json`. The scaled benchmark ranges from a small non-tight program through independent-choice extensions with up to `2^20` answer sets. Future methods should write the same result artifact format under `checkpoints/<method>/results.json` and then call `scripts/evaluate.sh`. Evaluation code must not import from `method/`.
