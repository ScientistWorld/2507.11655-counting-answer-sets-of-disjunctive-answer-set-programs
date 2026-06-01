from __future__ import annotations

from functools import lru_cache
from typing import Iterable

from .cnf import Clause


def _simplify(clauses: tuple[Clause, ...], lit: int) -> tuple[Clause, ...] | None:
    out: list[Clause] = []
    for clause in clauses:
        if lit in clause:
            continue
        if -lit in clause:
            reduced = tuple(x for x in clause if x != -lit)
            if not reduced:
                return None
            out.append(reduced)
        else:
            out.append(clause)
    return tuple(out)


def _unit_propagate(clauses: tuple[Clause, ...]) -> tuple[tuple[Clause, ...] | None, set[int]]:
    assigned: set[int] = set()
    changed = True
    while changed:
        changed = False
        unit = None
        for clause in clauses:
            if len(clause) == 0:
                return None, assigned
            if len(clause) == 1:
                unit = clause[0]
                break
        if unit is not None:
            clauses = _simplify(clauses, unit)
            if clauses is None:
                return None, assigned
            assigned.add(abs(unit))
            changed = True
    return clauses, assigned


def count_models(clauses: Iterable[Clause], num_vars: int) -> int:
    base = tuple(tuple(sorted(c, key=abs)) for c in clauses)

    @lru_cache(maxsize=None)
    def rec(state: tuple[Clause, ...], remaining: frozenset[int]) -> int:
        simplified, assigned = _unit_propagate(state)
        if simplified is None:
            return 0
        remaining = frozenset(v for v in remaining if v not in assigned)
        used = {abs(lit) for clause in simplified for lit in clause}
        if not simplified:
            return 2 ** len(remaining)
        unconstrained = len([v for v in remaining if v not in used])
        remaining = frozenset(v for v in remaining if v in used)
        if not remaining:
            return 2 ** unconstrained
        var = min(remaining, key=lambda v: sum(v == abs(l) for c in simplified for l in c))
        rest = frozenset(v for v in remaining if v != var)
        total = 0
        for lit in (var, -var):
            nxt = _simplify(simplified, lit)
            if nxt is not None:
                total += rec(nxt, rest)
        return total * (2 ** unconstrained)

    return rec(base, frozenset(range(1, num_vars + 1)))


def is_sat(clauses: Iterable[Clause]) -> bool:
    used = {abs(lit) for clause in clauses for lit in clause}
    return count_models(clauses, max(used) if used else 0) > 0


def projected_count(clauses: list[Clause], projection_vars: list[int]) -> int:
    """Count distinct assignments to projection_vars extendable to clauses."""
    project = frozenset(projection_vars)
    base = tuple(tuple(sorted(c, key=abs)) for c in clauses)

    @lru_cache(maxsize=None)
    def rec(state: tuple[Clause, ...]) -> int:
        simplified, _assigned = _unit_propagate(state)
        if simplified is None:
            return 0
        if not simplified:
            return 1
        used_projected = sorted({abs(lit) for clause in simplified for lit in clause if abs(lit) in project})
        if not used_projected:
            return 1 if is_sat(simplified) else 0
        var = min(used_projected, key=lambda v: sum(v == abs(l) for c in simplified for l in c))
        total = 0
        for lit in (var, -var):
            nxt = _simplify(simplified, lit)
            if nxt is not None:
                total += rec(nxt)
        return total

    return rec(base)
