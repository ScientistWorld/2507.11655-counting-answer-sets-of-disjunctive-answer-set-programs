#!/usr/bin/env python3
from __future__ import annotations

from itertools import product

from data.asp import parse_program
from sharpasp_sr.counter import projected_count
from sharpasp_sr.reduction import sharpasp_sr_count


def _sat(clauses: list[tuple[int, ...]], assignment: dict[int, bool]) -> bool:
    return all(any(assignment[abs(lit)] == (lit > 0) for lit in clause) for clause in clauses)


def _naive_projected_count(clauses: list[tuple[int, ...]], projection: list[int], nvars: int) -> int:
    seen = set()
    for bits in product([False, True], repeat=nvars):
        assignment = {idx + 1: bit for idx, bit in enumerate(bits)}
        if _sat(clauses, assignment):
            seen.add(tuple(assignment[var] for var in projection))
    return len(seen)


def test_projected_count_unconstrained_projection() -> None:
    cases = [
        ([], [1, 2], 2),
        ([(1,)], [1, 2], 2),
        ([(3,)], [1, 2], 3),
        ([(1, 2)], [1, 2], 2),
        ([(1, 3), (-1, 3)], [1, 2], 3),
    ]
    for clauses, projection, nvars in cases:
        expected = _naive_projected_count(clauses, projection, nvars)
        got = projected_count(clauses, projection)
        assert got == expected, (clauses, projection, expected, got)


def test_paper_example_count() -> None:
    program = parse_program(
        """
        p0 | p1.
        q0 | q1.
        q0 :- w.
        q1 :- w.
        w :- p0.
        w :- p1, q1.
        :- not w.
        """
    )
    result = sharpasp_sr_count(program)
    assert result["answer_sets"] == 1, result
    assert result["overcount"] > result["answer_sets"], result


def test_copy_variables_are_fresh() -> None:
    program = parse_program(
        """
        a :- a.
        a__prime.
        """
    )
    result = sharpasp_sr_count(program)
    assert result["answer_sets"] == 1, result


def main() -> None:
    test_projected_count_unconstrained_projection()
    test_paper_example_count()
    test_copy_variables_are_fresh()


if __name__ == "__main__":
    main()
