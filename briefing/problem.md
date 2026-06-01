# Problem Definition

## Research Question

Count the number of answer sets of a finite ground disjunctive Answer Set Programming (ASP) program exactly. The challenge is to handle non-tight programs where stable-model minimality matters and where plain answer-set enumeration becomes infeasible when the number of answer sets is large.

## Why It Matters

Exact answer-set counts are used in probabilistic reasoning, network reliability, answer-set navigation, and other ASP applications. Disjunctive programs are more expressive than normal programs, but practical exact counters for them are limited.

## Success Criteria

Successful systems must return exact counts, agree with enumeration on small instances, and scale to instances with many answer sets under fixed resource limits. Evaluation should also track structural difficulty, especially positive cycles, so improvements cannot be achieved by silently ignoring the hard non-tight cases.
