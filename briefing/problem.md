# Problem Definition

## Research Question

Count the number of answer sets of a finite ground disjunctive Answer Set Programming (ASP) program exactly. The hard case is non-tight programs (positive cycles among atoms), where stable-model minimality matters: classical models of the program's completion can outnumber its answer sets, and enumerating answer sets one by one becomes infeasible when there are many of them.

## Why It Matters

Exact answer-set counts are used in probabilistic reasoning, network reliability, answer-set navigation, and other ASP applications. Disjunctive programs are more expressive than normal programs (answer-set checking is co-NP-hard, counting is #·co-NP-complete), and practical exact counters for them are scarce.

## Success Criteria

A counter succeeds on a program when it prints the exact number of answer sets within a fixed per-program resource budget. Wrong counts are not partially credited: exactness is a hard constraint, and any wrong or impossible count invalidates a run. Better counters solve more programs under the same budget, including programs whose counts are far beyond what enumeration can reach and programs with many cyclic (loop) atoms.
