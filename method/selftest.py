#!/usr/bin/env python3
from __future__ import annotations

from itertools import product

from data.asp import enumerate_answer_sets, parse_program
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


def test_small_programs_match_answer_set_semantics() -> None:
    cases = [
        """
        a | b.
        """,
        """
        a | b.
        a :- b.
        b :- a.
        """,
        """
        a | b :- c.
        c :- a.
        c :- b.
        :- not c.
        """,
        """
        a :- not b.
        b :- not a.
        c | d :- a.
        c :- d.
        d :- c.
        """,
        """
        a :- not a.
        """,
    ]
    for text in cases:
        program = parse_program(text)
        expected, complete = enumerate_answer_sets(program)
        assert complete
        result = sharpasp_sr_count(program)
        assert result["answer_sets"] == expected, (text, expected, result)
        assert result["overcount"] - result["surplus"] == expected, (text, expected, result)


def main() -> None:
    test_projected_count_unconstrained_projection()
    test_paper_example_count()
    test_copy_variables_are_fresh()
    test_small_programs_match_answer_set_semantics()


if __name__ == "__main__":
    main()
