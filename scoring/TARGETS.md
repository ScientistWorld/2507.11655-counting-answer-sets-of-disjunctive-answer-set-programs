# Evaluation Targets

All metrics are computed by `eval/train/evaluate.py` (train, visible) and `eval/test/evaluate.py` (hidden test) from the counts the registered counters print, under a fixed budget of 10 CPU seconds per program.

## Primary: large_count_counting
Exact counting on programs with at least 2^23 answer sets (paper Table 1 / Figure 3, scaled).
- **Metric**: `solved_instances` (higher is better; primary, coefficient 1.0)
- **Metric**: `max_log2_count_solved` (higher is better; coefficient 0.02)
- **Constraint**: `wrong_count_instances` (must be 0; coefficient -1.0; any nonzero value fails the run)
- **Reference (hidden test, 14 programs)**: sharpASP-sR 7, hybrid 7, clingo enumeration 0
- **Run**: `bash scripts/reproduce.sh` (or `bash scripts/evaluate_test.sh` with counters registered)

## Secondary: hybrid_full_spectrum
Exact counting across small, mid and large counts, mostly with many loop atoms (paper Tables 2-3, scaled).
- **Metric**: `solved_instances` (higher is better; primary, coefficient 1.0)
- **Metric**: `max_log2_count_solved` (higher is better; coefficient 0.02)
- **Constraint**: `wrong_count_instances` (must be 0; coefficient -1.0; any nonzero value fails the run)
- **Reference (hidden test, 13 programs)**: hybrid 10, sharpASP-sR 9, clingo enumeration 7
- **Run**: `bash scripts/reproduce.sh`

## Constraint (both experiments): exactness under a fixed budget
Counts must be exact; a single wrong, negative or non-integer count on a split zeroes `solved_instances` and `max_log2_count_solved` for that run in every experiment. The budget (10 CPU s, 20 s wall, counter plus waited-for children) is fixed in the evaluators and identical for every counter.
