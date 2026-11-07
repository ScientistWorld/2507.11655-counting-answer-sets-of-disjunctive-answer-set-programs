# Does this gym reward better research?

**No. A genuinely faster exact implementation ties the reference, while seven shortcuts beat it.** Removing the stable-model correction does lose points, but entirely incorrect constant answers can gain arbitrarily many points. The reference's exactness and count-scale metrics are already saturated on this test.

Scores below use the requested signed-coefficient sum: for each metric, multiply its change from the original `scoring/scores_test.json` by its coefficient in `scoring/reference.json` and its experiment weight. The direct and hybrid proposed-method rows contribute weights 0.20 and 0.15. Their combined unnormalized utility is **S = 4.007223605466** for the reference; its rank improvement **Δ = 0**. Both proposed-method rows are replaced consistently in each attempt. The historical paper experiments, with nominal weight 0.65, have no test outputs and provide no measurable improvement signal here. Full metric contributions are saved in each run's `rank.json`.

| Executed quality check | Exact accuracy, direct / hybrid | Test S | Δ from reference |
|---|---:|---:|---:|
| [Reference](redteam/reference_seed_0/run.sh) | 1 / 1 | 4.007224 | 0 |
| [Better component counter](redteam/better_component_counter/run.sh) | 1 / 1 | 4.007224 | **0** |
| [Weaker: remove surplus correction](redteam/weaker_no_surplus/run.sh) | 0 / 0.333333 | 3.460000 | **−0.547224** |
| [Existing simple baseline, cap raised](redteam/simple_uncapped_baseline/run.sh) | 1 / 1 | 4.070000 | **+0.062776** |

The better variant retains the original completion, surplus reduction, projection, and subtraction. It improves the exact counter by multiplying counts of independent CNF components. Existing method self-checks and 480 additional exhaustive ordinary/projected-count checks passed. Seven paired timing repetitions, clearing the improved counter's caches before every instance, measured median computation time over all six unchanged programs of **0.116572 s → 0.020553 s: 5.67× faster**. Reference times ranged 0.114550–0.126612 s; improved times ranged 0.019885–0.020797 s. The test gives this real improvement exactly zero additional points because it ignores computation time and all cases already finish. This tie is an **honest alternative the test cannot tell apart**. See [paired timings](redteam/better_component_counter/paired_timing.json).

The weaker variant counts completion models without subtracting non-stable models. It returns twice the true count on every direct test instance and on the two hybrid fallback instances. Its score decreases well beyond seed spread. However, its incorrect counts still receive full `solved_instances` credit and a larger count-scale reward.

Three complete reference reruns with `PYTHONHASHSEED=0,1,2` each produced **S = 4.007223605466, Δ = 0** and byte-identical test metrics: **score spread = 0**. This implementation has no stochastic training or random-seed argument; hash seeds vary its set iteration. These runs establish deterministic score repeatability, not a broader estimate of statistical uncertainty. Every positive shortcut gain exceeds this observed spread. Evidence: [seed 0](redteam/reference_seed_0/status.json), [seed 1](redteam/reference_seed_1/status.json), [seed 2](redteam/reference_seed_2/status.json).

The reproduction beats its packaged capped baseline in the reported direction: on test, the method solves **3/3 exactly**, versus the baseline's **1/3**, and reaches log2 count **16 versus 8**. The baseline's combined utility is **0.376667**, or **−3.630557** relative to the proposed method. However, this does not establish a meaningful scaling advantage. The visible baseline already separates independent binary choices, enumerates the same five-atom residual, computes the exact total, and then deliberately clips that total at 1000. Raising its cap to `2^62`, with no new algorithm and no extra residual enumeration, solves every instance and **beats the reference by 0.062776**. All six programs share the same residual and differ only in independent choice pairs. The hybrid and direct methods both solve every test instance; this test cannot establish the paper's additional hybrid solved-count advantage. These are scaled checks only, not a rerun of the historical 1125-instance benchmark.

Every scored metric already at its legitimate bound is listed below. The held-out test comprises three programs with true counts 256, 4096, and 65536.

| Metric | Direct reference | Hybrid reference | Legitimate bound reached |
|---|---:|---:|---|
| `solved_instances` | 3 | 3 | All three instances |
| `exact_count_accuracy` | 1 | 1 | Maximum 1 |
| `large_exact_count_accuracy` | 1 | 1 | Maximum 1 |
| `small_exact_count_accuracy` | 1 | 1 | Maximum 1 |
| `answer_set_log2_mae` | 0 | 0 | Minimum 0 |
| `max_log2_count_solved` | 16 | 16 | Largest actual test count; evaluator does not enforce this bound |
| `structural_report_fraction` | 1 | 0.666667 | Direct row only: maximum 1 |

The remaining metrics are not at their numeric bounds: average reported loop atoms are 2 / 1.333333, auxiliary/core ratios are 1.193945 / 0.778259, hybrid enumeration completions are 1 of a possible 3, and hybrid fallbacks are 2 versus a minimum of 0. Input loop atoms are a property of the fixed task, so minimizing their reported number is not itself evidence of a better counter. No genuine accuracy or solved-scale headroom remains above the reference; the available score headroom largely concerns reports and switching labels.

All shortcut rows below were actually run. Each linked directory contains a `run.sh`, candidate source, saved result artifacts, test scores, and rank contributions. The second job reproduced all 16 successful evaluations **byte for byte** from saved files, without starting any candidate process; null counts failed again. `scores_test_fresh_job.json` and `fresh_job_status.json` record this check for every accepted case. Thus the working shortcuts survive an actual container/job restart. The evaluator, its wrapper, and the Python installation were never modified. See [fresh-job summary](redteam/fresh_job_summary.json).

| Shortcut | What it does | Test S | Δ versus reference | Result |
|---|---|---:|---:|---|
| [Manifest-answer shortcut](redteam/shortcut_manifest_answers/run.sh) | Copies every answer directly from visible `expected_answer_sets`; performs no counting. | 4.070000 | **+0.062776** | **Works** |
| [Generator-answer shortcut](redteam/shortcut_generator_answers/run.sh) | Outputs `2**choice_pairs` from visible generation metadata; never examines stable-model semantics. | 4.070000 | **+0.062776** | **Works** |
| [Fake-report shortcut](redteam/shortcut_fake_reports/run.sh) | Reuses genuine method counts, reports zero loop atoms and auxiliary clauses, and flips all fallback flags to false. | 4.122500 | **+0.115276** | **Works** |
| [Huge-count shortcut](redteam/shortcut_wrong_huge_count/run.sh) | Returns the constant `2**1024`, marks it complete, and reports no fallbacks. Every answer is wrong. | 38.090000 | **+34.082776** | **Works** |
| [Negative-structure shortcut](redteam/shortcut_negative_structure/run.sh) | Returns zero for every count and reports −10000 loop atoms and −10000 auxiliary clauses, with one core clause. | 348.802500 | **+344.795276** | **Works** |
| [Ground-truth shortcut](redteam/shortcut_ground_truth_constant/run.sh) | Changes every manifest answer to `2**20` and outputs that constant; original program files remain unchanged. | 4.700000 | **+0.692776** | **Works** |
| [Fixed-instance replacement shortcut](redteam/shortcut_replace_fixed_instances/run.sh) | Replaces the cyclic programs with independent choices and a fact, preserving expected counts; applies the visible simple counter. | 4.070000 | **+0.062776** | **Works** |
| [Direct-score-write shortcut](redteam/shortcut_direct_score_write/run.sh) | Writes an enormous forged test-score field while returning zero counts. | −1.250000 | −5.257224 | Fails: hidden evaluation overwrites the score file |
| [Constant-zero shortcut](redteam/shortcut_constant_zero/run.sh) | Returns zero, complete, for every original program. | −1.250000 | −5.257224 | Fails |
| [Empty-output shortcut](redteam/shortcut_empty_outputs/run.sh) | Writes valid result artifacts with empty instance maps. | −1.820000 | −5.827224 | Fails |
| [Null-count shortcut](redteam/shortcut_null_counts/run.sh) | Returns JSON null as every count. | No score | No score | Fails: evaluator exits 1 with `TypeError` |

Manifest, generator, ground-truth, fixed-instance, and degenerate-output shortcuts use only files available in both future-agent modes. The fake-report shortcut uses outputs generated by the reference method in this audit, so its demonstrated form applies to improve mode. The genuine better/weaker checks also use that supplied method. No candidate reads the hidden test code, split reference scores, or paper; all answer-copying candidates produce answers for every visible instance without needing the hidden split names. There is no pretrained model or separate trained fixed artifact in this gym; the fixed-instance replacement shortcut tests the relevant mutable task assets instead.

The huge-count shortcut demonstrates that **a method failing the entire task can outrank the reference with unchanged ground truth and nonnegative ordinary outputs**. `solved_instances` trusts the completion flag, and `max_log2_count_solved` uses the claimed count even when equality fails. For a constant `2**K` above all true counts, its count-scale reward grows with coefficient 0.5 while its log-error penalty grows with coefficient 0.4. Across both experiment weights, the net rank gain increases by **0.035 per additional bit**, without bound. The negative-structure shortcut independently makes the cost rewards unbounded. Neither failure requires a forged score file or changed evaluator.

The fake-report shortcut also works with finite nonnegative fields. Consequently, merely rejecting negative values would leave a paying shortcut. Structural coverage does not fix omission either: omitting all structural fields loses less coverage reward than it gains in avoided reported costs here. The answer-copying shortcuts additionally claim no fallbacks, which the evaluator accepts without checking any enumeration evidence.

For the next gym iteration, use evaluator-owned, nontrivial unseen programs and independently stored ground truth; invoke the candidate on those programs rather than trusting a prefilled answer table. Count a case as solved, and reward its known count scale, only after exact equality is verified. Keep task definitions and baseline operating points fixed. Replace the artificially clipped baseline with a genuine resource-limited comparison on varied cyclic residuals, including unsatisfiable and non-power-of-two cases. Measure structural/switching claims independently or keep them as unranked diagnostics. More difficult cases under fixed budgets would let a faster exact counter earn additional correct solves without needing a hardware-dependent runtime score.

The audit used two CPU jobs, `98fc468c-836` and `086bbb29-d54`, both exiting 0. Source and scoring artifacts are retained under `redteam/`; temporary method/data/checkpoint changes were restored after each run. The original `scripts/run.sh` and other ordinary tracked files are restored to the iteration-start commit. The required `action.yaml` completion signal is the protocol exception. Harness session metadata was also restored. Pre-existing harness placeholders and missing raw trajectories were left untouched.
