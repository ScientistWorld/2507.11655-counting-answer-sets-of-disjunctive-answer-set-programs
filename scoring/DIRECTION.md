# Research Direction

## Research Problem
Improve practical exact counting of answer sets of ground disjunctive ASP programs, especially non-tight programs where stable-model minimality creates surplus classical models and answer-set enumeration scales poorly with the number of answer sets.

## Core Contribution
Work should stay within exact counting for disjunctive ASP and preserve stable-model semantics. Good targets: programs with very large counts that current counters cannot finish under the budget, and programs with many loop atoms where formula-based counting struggles.

## Approach Scope
In scope: better reductions or encodings to (projected) model counting, preprocessing and simplification of programs or formulas, decomposition, better use of model counters, smarter combinations of enumeration and counting, and new exact algorithms.

## Out of Bounds
Approximate counting; changing the budget, programs, ground truth or evaluators; reading hidden test files; hardcoded answers; generator-specific decoders that bypass general answer-set counting; restricting to tight or normal programs only.
