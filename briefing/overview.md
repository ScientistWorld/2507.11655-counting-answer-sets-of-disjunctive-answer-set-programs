# Overview

- **Paper ID:** 2507.11655
- **Title:** Counting Answer Sets of Disjunctive Answer Set Programs
- **Domain:** Knowledge Representation / Answer Set Programming / Exact Counting
- **TL;DR:** The paper counts answer sets of disjunctive ASP programs exactly by subtracting projected-counted non-answer-set completion models from a completion-model overcount.

## Short Summary

The paper targets exact answer-set counting for non-tight disjunctive ASP programs, a setting where enumeration and counters for normal programs do not scale well. It defines a loop-atom copy construction that identifies surplus Clark-completion models that are not stable models. The resulting sharpASP-sR counter reduces the problem to projected model counting and outperforms clingo, Wasp, and DynASP on the paper's benchmark suite.

## Key Results

- On 1125 benchmark instances, sharpASP-sR solves 825 instances versus 708 for clingo, 432 for Wasp, and 89 for DynASP.
- The hybrid clingo plus sharpASP-sR approach solves 918 instances with PAR2 1600.
- The paper reports sharpASP-sR counting instances up to roughly `2^127` answer sets, while enumeration systems time out at much lower counts.
