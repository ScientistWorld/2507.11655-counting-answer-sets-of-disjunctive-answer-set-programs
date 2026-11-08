> **Superseded (iteration 11, hardening).** This file records an earlier iteration of the gym. The evaluation it describes (six visible `choices_*` programs, `results.json` artifacts, self-reported structural metrics, in-repo Python counter) was replaced: counters are now run by the evaluators on hidden programs under a fixed budget, with GANAK as the reference backend. See `HARDENING.md` and `briefing/evaluation.md` for the current gym.

# Design Notes

## Checks Performed

- Read `scripts/evaluate_train.sh` and `scripts/evaluate_test.sh` side by side. The wrappers call `eval/train/evaluate_counts.py` and `eval/test/evaluate_counts.py` respectively, write `scoring/scores_train.json` and `scoring/scores_test.json`, and do not hardcode a method name.
- Read both split evaluators. They enumerate result artifacts from `checkpoints/*/results.json` plus explicit result paths, so future methods are scored through artifacts rather than by importing or rerunning this paper's method.
- Checked train/test import leakage with grep and `python validate.py --reference-only`; the validator reported train/test independence, eval-method separation, method-output reads, and script rewiring as OK.
- Checked `scoring/reference.json` for paper-agreement metric names. No metric rewards matching a published value; the train/test metrics score scientific quantities such as exact count accuracy, scale handled, count error, and fallback behavior.
- Confirmed `scoring/scores_train.json` and `scoring/scores_test.json` do not exist.

## Changes Made

- Added `large_exact_count_accuracy` to both train and test evaluators. This separately scores instances above the 1000-answer-set enumeration cap, making capped-enumeration shortcuts visible even if they perform well on small cases.
- Added `small_exact_count_accuracy` so the split still tracks easy-instance correctness and the hybrid enumeration path.
- Added `answer_set_log2_mae`, a lower-is-better count-error metric. This catches approximate or clipped counts that are not exact, instead of relying only on binary exactness.
- Added top-level `slice` markers to train/test score output so artifacts are not byte-identical in shape.
- Added `structural_report_fraction` and made the clause-ratio calculation tolerate partially missing structural fields. This fixes a gaming pattern where omitting `loop_atoms`, `phi1_clauses`, or `phi2_clauses` made structural cost look like zero.
- Added the required `higher_is_better`, `coefficient`, and `description` fields for all active metrics in `scoring/reference.json`; reduced the weight of method-reported structural-cost metrics so they remain constraints but do not dominate exact counting quality.

## Runtime Concerns For Next Iteration

- The split is very small: train has `paper_example`, `choices_14`, `choices_20`; test has `choices_8`, `choices_12`, `choices_16`. The added large/small and log-error metrics improve triangulation, but the runner should watch for saturation.
- `data/benchmarks.json` exposes all generated instance names and expected counts. That predates this pass and is outside the allowed edit scope, but it means the hidden test mainly detects methods that overfit visible evaluator code or visible result artifacts, not agents that inspect all public data.
- `structural_report_fraction`, `avg_loop_atoms`, and `avg_phi2_to_phi1_clause_ratio` are artifact-reported. They are useful for catching missing-reduction metadata, but a dishonest method could still fabricate them. Treat exactness and large-instance metrics as the primary anti-shortcut signals.
- The test evaluator optionally filters to methods present in `scoring/scores_train.json` if that file exists. If the final runner invokes test without first running train, it will score all discovered artifacts instead; this is acceptable but should be understood when comparing train/test gaps.
