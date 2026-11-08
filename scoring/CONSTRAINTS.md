# Scientist Constraints

## Task
Count answer sets of ground disjunctive ASP programs exactly. The evaluators run your counter (registered as `checkpoints/<name>/counter.json`, see `briefing/evaluation.md`) on each program and read only the integer it prints last.

## Exactness
Every printed count must be exact. Approximate, estimated or guessed counts are out of scope: a single wrong or impossible count fails the whole run on that split. If your counter cannot finish, print nothing (or exit non-zero).

## Fixed operating point
The per-program budget (10 CPU seconds including waited-for child processes, 20 s wall) is fixed by the evaluators for every counter. Do not change the evaluators, the budget, the programs, or the ground truth; do not spread work across processes you do not wait for to escape CPU accounting.

## Data
Develop on `data/train/` (programs plus exact counts). The hidden test programs are drawn from the same families with a different random draw. Do not read files under `eval/test/` from your counter, and do not hardcode answers (for example by hashing programs): the hidden programs are different.

## General methods
Improvements must be general exact counting techniques for disjunctive programs. Decoders that recognize one benchmark generator's encoding and bypass general answer-set counting are out of scope.

## Compliance Checklist
- [ ] Counter registered under `checkpoints/<name>/counter.json` and runnable from `/home/user` without internet.
- [ ] Prints exact counts only; prints nothing when it cannot finish.
- [ ] Does not read `eval/test/`, does not look up answers, does not modify `eval/` or `data/train/`.
- [ ] Evaluated with `bash scripts/evaluate.sh` (train) before submission.
