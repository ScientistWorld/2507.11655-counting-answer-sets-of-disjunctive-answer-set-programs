"""Exact model/projected counting with independent CNF component products.

The reduction is unchanged. Components have disjoint variables, so their
counts multiply; unmentioned projection variables contribute a power of two.
"""
from __future__ import annotations

from functools import lru_cache
from math import prod


def simplify(clauses, lit):
    out = []
    for clause in clauses:
        if lit in clause:
            continue
        reduced = tuple(x for x in clause if x != -lit)
        if not reduced:
            return None
        out.append(reduced)
    return tuple(out)


def components(clauses):
    parent = {}

    def find(v):
        parent.setdefault(v, v)
        if parent[v] != v:
            parent[v] = find(parent[v])
        return parent[v]

    for clause in clauses:
        first = abs(clause[0])
        for lit in clause:
            parent[find(abs(lit))] = find(first)
    groups = {}
    for clause in clauses:
        groups.setdefault(find(abs(clause[0])), []).append(clause)
    return tuple(tuple(group) for group in groups.values())


@lru_cache(maxsize=None)
def rec(clauses, projection):
    if any(not clause for clause in clauses):
        return 0
    while True:
        unit = next((clause[0] for clause in clauses if len(clause) == 1), None)
        if unit is None:
            break
        clauses = simplify(clauses, unit)
        if clauses is None:
            return 0
        projection = projection - {abs(unit)}
    if not clauses:
        return 1 << len(projection)
    used = frozenset(abs(lit) for clause in clauses for lit in clause)
    free_factor = 1 << len(projection - used)
    projection = projection & used
    parts = components(clauses)
    if len(parts) > 1:
        return free_factor * prod(
            rec(part, projection & frozenset(abs(lit) for clause in part for lit in clause))
            for part in parts
        )
    if not projection:
        # Existential variables require a SAT answer, not their model count.
        return free_factor if sat(clauses) else 0
    occurrences = {v: 0 for v in projection}
    for clause in clauses:
        for lit in clause:
            if abs(lit) in occurrences:
                occurrences[abs(lit)] += 1
    var = max(sorted(projection), key=occurrences.get)
    total = 0
    for lit in (var, -var):
        branch = simplify(clauses, lit)
        if branch is not None:
            total += rec(branch, projection - {var})
    return free_factor * total


@lru_cache(maxsize=None)
def sat(clauses):
    if any(not clause for clause in clauses):
        return False
    if not clauses:
        return True
    unit = next((clause[0] for clause in clauses if len(clause) == 1), None)
    candidates = (unit,) if unit is not None else (clauses[0][0], -clauses[0][0])
    for lit in candidates:
        branch = simplify(clauses, lit)
        if branch is not None and sat(branch):
            return True
    return False


def canonical(clauses):
    return tuple(sorted(set(tuple(sorted(set(c))) for c in clauses)))


def count_models(clauses, num_vars):
    return rec(canonical(clauses), frozenset(range(1, num_vars + 1)))


def is_sat(clauses):
    return sat(canonical(clauses))


def projected_count(clauses, projection_vars):
    return rec(canonical(clauses), frozenset(projection_vars))
