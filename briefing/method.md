# Paper's Method

## Key Contribution

The paper introduces sharpASP-sR, an exact counter for disjunctive ASP programs based on a subtractive reduction to projected propositional model counting.

## Approach

For a program `P`, the method builds Clark completion `Comp(P)` and counts its models as an overcount. It then constructs a surplus formula using two copies of the loop atoms in the positive dependency graph. The surplus formula captures models of the completion that are not answer sets, and projected model counting counts each original interpretation once. The final answer-set count is:

`|AS(P)| = #Comp(P) - #exists_{copy variables} phi2`.

This reproduction implements the same reduction and uses a small exact in-repo projected counter for the scaled benchmark rather than GANAK.

## Main Claims

Primary claim: the subtractive projected-counting approach is exact and scales better than enumeration on disjunctive programs with large answer-set counts.

Secondary claims: a hybrid strategy that enumerates only small-count cases and falls back to sharpASP-sR solves more instances, and sharpASP-sR performance is sensitive to the number of loop atoms.
