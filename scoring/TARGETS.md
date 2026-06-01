# Evaluation Targets

## Primary: scaled_disjunctive_counting
Tests whether an exact disjunctive ASP counter returns correct counts on non-tight programs whose answer-set count grows from the paper example to `2^20`, beyond a small enumeration cap.
- **Metric**: `exact_count_accuracy` (higher is better)
- **Metric**: `solved_instances` (higher is better)
- **Metric**: `max_log2_count_solved` (higher is better)
- **Run**: `bash scripts/reproduce.sh`

## Constraint: scaled_disjunctive_counting
Tracks structural and encoding cost so an improvement cannot ignore the non-tight cyclic part of the programs or hide unbounded formula growth.
- **Metric**: `avg_loop_atoms` (lower is better at equal accuracy/count scale)
- **Metric**: `avg_phi2_to_phi1_clause_ratio` (lower is better at equal accuracy/count scale)
- **Run**: `bash scripts/evaluate.sh` after producing result artifacts.

## Secondary: scaled_hybrid_counting
Tests whether a hybrid exact counter preserves enumeration on easy instances and falls back to sharpASP-sR when the enumeration cap is exceeded.
- **Metric**: `exact_count_accuracy` (higher is better)
- **Metric**: `solved_instances` (higher is better)
- **Metric**: `enumeration_completed_instances` (higher is better at equal accuracy)
- **Metric**: `fallback_instances` (lower is better at equal accuracy/count scale)
- **Run**: `bash scripts/reproduce.sh`
