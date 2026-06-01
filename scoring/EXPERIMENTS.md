# Experiment Overview

## scaled_disjunctive_counting
Tests whether an exact counter can handle non-tight disjunctive ASP instances with growing answer-set counts while preserving exact agreement with known counts. The comparison includes a capped enumeration reference to expose the central scaling issue: exact enumeration is fine for small answer-set counts but stops being a useful strategy as counts grow. The tracked scale now reaches `2^20` answer sets.

## scaled_hybrid_counting
Tests whether a hybrid exact counter can use enumeration for small-count instances and still solve larger-count instances by falling back to a stronger exact counter. The experiment measures both final exactness and how many instances are handled before the fallback is needed.
