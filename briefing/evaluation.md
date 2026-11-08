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
