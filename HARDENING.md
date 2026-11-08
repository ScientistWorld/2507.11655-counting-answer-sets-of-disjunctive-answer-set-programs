# Hardening report (iteration 11)

## Verdict: better results now score higher

The audited test (REDTEAM.md) could not reward science. A 5.7x faster exact counter tied the reference. Seven shortcuts beat it, including constant `2^1024` (+34.1) and negative "structure" fields (+344.8). Its three test programs shared one 5-atom core, their answers sat in `data/benchmarks.json`, and the evaluator trusted the `complete` flags, structure fields and fallback flags the method wrote about itself.

The rebuilt test runs every registered counter on 27 **hidden** programs under a fixed budget. It credits a program only when the printed count equals an independently computed exact count, and it fails the run on any wrong or impossible count. On it, every better variant scores above the reference, and every weaker variant and every shortcut scores below.

Δ below is the rank change against the reference: Σ over scored experiments of weight × Σ coefficient × (variant − reference), using `scoring/reference.json`. The reference rows are `sharpasp_sr` in `large_count_counting` and `hybrid_full_spectrum`'s proposed row `hybrid_sharpasp_sr`. "Before" values come from REDTEAM.md, on the old metric set. Computed by `redteam/hardening/rank.py`; raw scores are in `redteam/hardening/scores_test_*.json`, and per-program outcomes in `redteam/hardening/details/`.

| Variant | What it changes | Before Δ (old test) | After: solved large / full (of 14 / 13) | After Δ |
|---|---|---:|---:|---:|
| Reference (sharpASP-sR / hybrid) | paper's reduction + GANAK; hybrid = clingo ≤10^4 answer sets, then sharpASP-sR | 0 | 7 / 10 (hybrid), 7 / 9 (direct) | 0 |
| Better: one-copy surplus encoding | replaces the paper's two-copy φ2 by Comp ∧ Copy′ ∧ ∨(x ∧ ¬x′) (equivalent by Lemma 3; agrees with brute force on 80 random programs) | REDTEAM's better counter: **0 (tie)** | 12 / 10 | **+2.306** |
| Better: hybrid + one-copy | same, behind the 10^4 enumeration stage | — | 12 / 11 | **+2.656** |
| Better: adaptive hybrid | enumerate up to 3·10^5 answer sets before switching | — | 7 / 11 | **+0.350** |
| Better: adaptive hybrid + one-copy | both | — | 12 / 12 | **+3.006** |
| Weaker: no surplus correction | reports #Comp(P) only | −0.547 | wrong on 24 programs → run failed | **−16.928** |
| Weaker: in-repo Python backend | paper's reduction on the old toy counter | — | 0 / 2 | **−6.367** |
| Baseline: clingo enumeration | full enumeration under the budget | (capped variant +0.063) | 0 / 7 | −4.573 |

Paired comparison on identical hidden programs: the one-copy variant solves 6 programs the reference does not and loses none. The combined variant gains 7 over the hybrid and loses none. The adaptive hybrid gains 1 and loses none. Run-to-run noise is zero: three complete hidden-test runs of the reference rows (two in the hardening job and one in the final `reproduce.sh` run) produced identical per-program outcomes. Every reference solve used ≤3.74 CPU s of the 10 s budget, and every unsolved program was still running when killed (they needed >25 s in calibration). So the smallest improvement the test registers, one more solved program (+0.35 or +0.45), lies above the noise.

## Per major shortcut: fix and score

All shortcuts below were re-run through the hidden test as registered counters (`redteam/hardening/shortcut_counter.py`; scores in `redteam/hardening/scores_test_shortcuts.json`).

| REDTEAM shortcut | Fix | Before Δ | After (form it can take now) | After Δ |
|---|---|---:|---|---:|
| Manifest-answer copy | Test programs and answers live only in `eval/test/` (secret seed, salted PBKDF2 digests; no plain-text counts anywhere). Visible train answers don't match hidden programs. | +0.063 | `train_lookup`: copy visible train answers by program text → 0 solved | −7.128 |
| (same, guessing on a miss) | Wrong count fails the run | — | `train_lookup_guess` → 27 wrong, run failed | −17.978 |
| Generator-answer (`2**choice_pairs`) | No generator metadata for test programs; guesses are wrong → run failed | +0.063 | `structure_guess` (2^#binary facts) → failed | −17.978 |
| Fake reports (zero loop atoms / no fallback) | Evaluator reads only the printed integer; self-reported structure/fallback fields are no longer scored | +0.115 | `fake_reports` (genuine counts + forged JSON report) = reference counts, no gain | −0.350* |
| Huge constant count `2^1024` | `solved` and count scale only credit verified-exact answers; wrong count fails the run | +34.083 | `constant_huge` → failed | −17.978 |
| Negative counts / structure | Negative / non-integer values are impossible → run failed; structure not scored | +344.795 | `negative` → failed | −17.978 |
| Ground-truth edit (2^20 everywhere) | Ground truth is not in mutable task data; evaluator reads only `eval/test/answers.json` | +0.693 | `constant_2pow20` → failed | −17.978 |
| Fixed-instance replacement | Programs are owned by `eval/test/`, copied to a temp file per run; a changed program would no longer match its stored digest | +0.063 | not runnable as a counter; closed by construction | — |
| Direct score write | Unchanged defense: the evaluator writes the score file after all runs | −5.257 | `write_scores` (forges `scoring/scores_test.json`, prints 0) → overwritten; prints wrong counts → failed | −17.978 |
| Constant zero / empty / null | Zero is wrong on every non-empty test program → failed; empty/`null` = no answer (null no longer crashes the evaluator) | −1.25 / −1.82 / crash | failed / 0 solved / 0 solved | −17.978 / −7.128 / −7.128 |
| *New:* read hidden answers at run time | Answers stored only as salted 400k-iteration PBKDF2 digests (~0.14 s per guess) | — | `read_hidden_answers` inverts only a tiny count (1 program, solved by everyone) | −6.747 |
| *New:* print an estimate on timeout | Any wrong count fails the run | — | `guess_on_timeout` → failed | −11.678 |

\* `fake_reports` wraps the direct counter, so in `hybrid_full_spectrum` it is compared with the hybrid row and scores the direct counter's −1 program. It gains nothing from its forged fields.

Other changes:
- **Budget accounting.** The evaluator counts the CPU time of the counter process plus all children it waits for, and caps each process with `RLIMIT_CPU`. A counter that runs parallel child processes to get more CPU per second than the budget allows is marked over budget (verified).
- **Fixed comparison.** The budget, programs, ground truth, test size and baselines are all fixed in `eval/`. The evaluator discovers every `checkpoints/*/counter.json` with no method name hardcoded, and `scripts/evaluate_test.sh` needs no arguments.

## Shortcuts left open

- **Generator-specific decoders.** A counter that recognizes the 2QBF saturation pattern (despite randomized atom names and shuffled rules) could count it through the matrix directly, the way the ground truth is computed. That is exact, but it bypasses general answer-set counting. It is out of scope in `scoring/CONSTRAINTS.md` and `DIRECTION.md`, and left to the shortcut grader. I did not build a test-time defense: the families are the paper's own benchmark families, and hiding the encoding would change the task.
- **Reading `eval/test/` at run time.** This is closed in effect (digests are not invertible within the budget except for tiny counts that every counter solves anyway), but not prevented. Forbidden in CONSTRAINTS.md.
- **Hardware-dependent budget.** The solve criterion is a CPU-time budget, which is how the paper measures (#solved under 5000 s); no wall-clock metric is scored. Programs where any reference counter finished between 4 s and 25 s of CPU were excluded during the build, so the reference outcomes hold under a 2.5x speed change. A future method that finishes right at 10 s may flip between machines. That is that method's noise, not the reference's.
- **Untracked grandchildren.** Processes a counter deliberately detaches (double fork) escape CPU accounting until the wall-clock kill (20 s). With 1-CPU test jobs this gives at most 2x the budget. Not defended, per instructions, and forbidden in CONSTRAINTS.md.

## Reference score before and after

- Before (old test, old metrics, direct + hybrid rows): S = 4.007; exact accuracy 1 / 1 on 3 programs. Every accuracy metric was at its bound.
- After (hidden test, 27 programs): `large_count_counting` sharpASP-sR 7/14 solved, max log2 count 29.77; `hybrid_full_spectrum` hybrid 10/13 solved, max log2 count 29.94. S = 0.45·7.5955 + 0.35·10.5988 = **7.128**. The scale differs from the old S; only Δs within one test are comparable.
- The reproduction shows the paper's claims in the paper's direction:
  - Large counts (Table 1 / Figure 3): sharpASP-sR 7 vs enumeration 0.
  - Full spectrum (Table 2): hybrid 10 > sharpASP-sR 9 > enumeration 7.
  - Over both slices: sharpASP-sR 16 > enumeration 7.
  - Loop atoms (Table 3): on the hidden programs with many loop atoms (33–115), enumeration solves all 7, while the direct counter misses 2 (65 and 105 loop atoms) and the hybrid misses the one above its 10^4 switch. On few-loop-atom programs with large counts, the direct counter is the only one that succeeds.
- The paper's reported numbers are unchanged in `paper_main_benchmark` / `paper_hybrid_benchmark`.

## Headroom check

- **Bounds.** The primary metric `solved_instances` has headroom in both slices. In `large_count_counting` the reference solves 7/14 (best variant 12/14); in `hybrid_full_spectrum` the hybrid solves 10/13 (best variant 12/13). Three hidden programs (2 + 1) remain unsolved by every counter I tried, though their ground truth is known.
- **Count scale.** `max_log2_count_solved` is at its bound for the reference in `hybrid_full_spectrum`: the reference solves that slice's largest count, 2^29.94. In `large_count_counting` it has headroom for the reference (2^29.77), but the best variant reaches the slice maximum (2^35.97). This metric carries a small coefficient (0.02 per bit); the ranking signal is `solved_instances`.
- **Constraint metric.** `wrong_count_instances` is 0 for every correct counter by definition, and nonzero for every broken one (10–14 per slice for the weaker and shortcut rows). It is the exactness constraint, not a benefit metric.
- **Where the paper falls short.** Programs from where the paper's method falls short are part of the scored set. These are programs with many loop atoms (7 of the 13 `hybrid_full_spectrum` programs have 33–115; Table 3 of the paper), and 2QBF programs whose surplus formula the two-copy encoding cannot finish within the budget.
- **No simple variant reaches the bound.** The paper-side improvement (adaptive switching) gains 1 program. An encoding change gains 5–6. Three hidden programs stay unsolved by every variant tried.
- **Baselines.** Enumeration scores clearly below the reference (0 vs 7, 7 vs 10). The old toy counter scores 0 / 2.

## Train / test

- **Splits.** The train split (`data/train/`, 37 programs, visible counts) is drawn from the same generator grid as the hidden test (27 programs) with a different seed. It is larger, with similar solved / unsolved proportions.
- **Code separation.** `eval/train/` and `eval/test/` share no code, the test builder `eval/test/build_hidden.py` is self-contained, and nothing in `eval/` imports `method/`.
- **Same interface.** Both evaluators score through the same counter interface with the same budget and metrics.
- **Honest methods score alike on both splits:**

| Counter | large-count solved, train (of 17) / test (of 14) | full-spectrum solved, train (of 20) / test (of 13) | Δ train | Δ test |
|---|---:|---:|---:|---:|
| sharpasp_sr | 9 / 7 | 12 / 9 | -0.700 | -0.350 |
| hybrid_sharpasp_sr | 9 / 7 | 14 / 10 | +0.000 | +0.000 |
| clingo_enumeration | 0 / 0 | 12 / 7 | -5.054 | -4.573 |
| better_sharpasp_sr_onecopy | 15 / 12 | 15 / 10 | +3.141 | +2.306 |
| better_hybrid_onecopy | 15 / 12 | 17 / 11 | +3.841 | +2.656 |
| better_hybrid_adaptive | 9 / 7 | 16 / 11 | +0.700 | +0.350 |
| better_hybrid_adaptive_onecopy | 15 / 12 | 19 / 12 | +4.541 | +3.006 |
| weaker_no_surplus | 0 / 0 | 0 / 0 | -21.248 | -16.928 |
| weaker_python_backend | 0 / 0 | 3 / 2 | -8.252 | -6.367 |

  Weaker variants fail on both splits (no-surplus: wrong counts on every non-tight program; python backend: 0 large-count solves). The variant ordering matches on train and test.

- **Overfitting to train loses on test.** A counter that memorizes the visible train answers solves 0 test programs (`train_lookup`).

## What changed (summary)

- **Task assets.** Visible toy instances and the answer manifest were replaced by generated benchmarks:
  - **2QBF saturation programs.** Ground truth is 2^|X| − #∃Y·CNF(¬matrix), counted with GANAK exact mode on a formula with no ASP reduction.
  - **Random non-tight disjunctive programs.** Ground truth is exhaustive clingo enumeration; programs it cannot finish are discarded.
  - **Agreement.** Across 174 calibrated candidates, the reference counters never disagreed with ground truth.
- **Counters are run, not trusted.** Method results are no longer artifacts: counters are registered and executed by the evaluators, as the protocol prescribes for methods that need no training.
- **Paper's backend.** The reference method now uses GANAK, the paper's projected model counter, instead of the in-repo toy counter. The reduction itself (Comp(P), two copy sets, projection, subtraction) is unchanged. The baseline is real clingo enumeration under the same budget (the old one clipped an exact total at 1000), and the hybrid uses the paper's 10^4 threshold.
- **Metrics.** Self-reported structure and switching metrics were removed. The scored metrics are solved programs, largest verified count, and the exactness constraint. `par2` stays at coefficient 0 as historical context.
- **Weights.** The scored experiments now carry 0.45 (`large_count_counting`, the paper's headline claim) and 0.35 (`hybrid_full_spectrum`, its secondary claim). The two historical paper experiments, which have no scaled outputs, dropped from 0.45 / 0.2 to 0.1 / 0.1. Previously 65% of the weight sat on experiments nothing could improve.
- **Packaging.**
  - `scripts/download.sh` fetches the pinned GANAK release (sha256-verified) into `data/downloads/`.
  - `environment/setup.sh` installs `clingo==5.8.3`.
  - `scripts/reproduce.sh` registers the counters and scores train and the hidden test.
  - Regenerating the benchmarks (`data/make_benchmarks.py`, `eval/test/build_hidden.py`) is documented but not part of reproduction, since it takes about an hour per split.

## Not fixed / limitations

- **Small test.** 27 hidden programs, and `hybrid_full_spectrum` has 13 instead of the 18 targeted: too few candidates were both reliably timed and in the small/mid-count, reference-unsolved strata. The noise is zero, so single-program gains are measurable, but the per-slice resolution is coarse.
- **Thin hard tail.** The headroom above the best variant I tried is 2 programs in `large_count_counting` and 1 in `hybrid_full_spectrum`. Future breakthroughs mainly gain through count scale and those programs.
- **Count range.** Random-family programs are limited to ≤ about 1.5·10^7 answer sets (independent enumeration must finish). Counts beyond that come only from the 2QBF family.
- **Scale.** The setup is scaled: 10 CPU s instead of 5000 s, programs with tens to a few hundred atoms instead of the paper's 1125-instance competition suite. Absolute solved fractions are not comparable with the paper's.
