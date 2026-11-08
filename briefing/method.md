# Paper's Method

## Key Contribution

The paper introduces sharpASP-sR, an exact counter for disjunctive ASP programs based on a subtractive reduction to projected propositional model counting.

## Approach

For a program `P`, the method builds Clark completion `Comp(P)` and counts its models as an overcount. It then constructs a surplus formula `phi2` using two copies (`x'`, `x*`) of every loop atom of the positive dependency graph; `phi2`'s models projected onto the program atoms are exactly the completion models that are not answer sets. The final answer-set count is:

`|AS(P)| = #Comp(P) - #exists_{CV' u CV*} phi2`.

This reproduction implements that reduction (`method/sharpasp_sr/reduction.py`) and, like the paper's prototype, uses GANAK (v2.8.0, exact mode `--prob 0`) as the (projected) model counter (`method/sharpasp_sr/ganak.py`). Counter interface: `method/count.py --mode direct|hybrid PROGRAM.lp`. The hybrid mode follows the paper: clingo enumeration up to 10^4 answer sets, then sharpASP-sR.

## Main Claims

Primary claim: the subtractive projected-counting approach is exact and solves more programs than enumeration, in particular programs with large answer-set counts.

Secondary claims: a hybrid that enumerates small-count cases and falls back to sharpASP-sR solves more than either component; sharpASP-sR's performance degrades as the number of loop atoms grows.
