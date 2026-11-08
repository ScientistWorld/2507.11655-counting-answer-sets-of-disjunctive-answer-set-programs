# Experiment Overview

Both experiments run every registered counter on hidden ground disjunctive ASP programs under the same fixed budget (10 CPU seconds per program) and credit a program only when the printed count equals the independently computed exact count. Any wrong or impossible count fails the run.

## large_count_counting
Establishes whether an exact counter can handle non-tight disjunctive programs whose answer-set counts (at least 2^23, up to about 2^36 here) are far beyond what one-by-one enumeration reaches under the budget. Enumeration solves none of these programs; the reference counter solves about half; programs it cannot solve remain, so stronger exact counters can score higher. Also reports the largest exactly-solved count.

## hybrid_full_spectrum
Establishes whether one counter works across the whole spectrum of answer-set counts (from a handful to hundreds of millions), about half of them programs with many loop atoms. Some programs are easy to enumerate but hard for formula-based counting, others are the reverse, so the set rewards counters that do not fail on either side. Enumeration alone, the reference exact counter alone, and the reference hybrid each leave programs unsolved.
