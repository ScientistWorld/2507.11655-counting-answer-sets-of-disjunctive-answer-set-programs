# Scientist Constraints

## Data
Use the benchmark instances listed in `data/benchmarks.json` for `scaled_disjunctive_counting`. Do not replace them with easier tight programs or instances without positive cycles; the benchmark is specifically about exact counting for non-tight disjunctive ASP.

## Output Contract
Methods must write `checkpoints/<method>/results.json` with per-instance exact counts. `scripts/evaluate.sh` must remain method-agnostic and must not import from `method/`.

## Exactness
Reported counts must be exact. Approximate counters may be studied separately, but they cannot be scored as satisfying `exact_count_accuracy` unless exact equality is established for each instance.

## Compliance Checklist
- [ ] Evaluated the instances from `data/benchmarks.json`.
- [ ] Did not train or tune on expected counts from the manifest.
- [ ] Wrote method outputs under `checkpoints/<method>/results.json`.
- [ ] Ran `bash scripts/evaluate.sh` to produce `scoring/scores.json`.
- [ ] Reported exact counts, not estimates.
