# Experiment Overview

## scaled_disjunctive_counting
Tests whether an exact counter can handle non-tight disjunctive ASP instances with growing answer-set counts while preserving exact agreement with known counts. The comparison includes a capped enumeration reference to expose the central scaling issue: exact enumeration is fine for small answer-set counts but stops being a useful strategy as counts grow.
