#!/usr/bin/env python3
from __future__ import annotations

import random
import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

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


def _random_program(rng: random.Random, n: int, m: int) -> str:
    atoms = [f"a{i}" for i in range(n)]
    lines = []
    for _ in range(m):
        head = rng.sample(atoms, rng.choice([0, 1, 1, 2, 2]))
        rest = [a for a in atoms if a not in head]
        pos = rng.sample(rest, min(len(rest), rng.randint(0 if head else 1, 2)))
        rest = [a for a in rest if a not in pos]
        neg = rng.sample(rest, min(len(rest), rng.randint(0, 1)))
        body = pos + [f"not {a}" for a in neg]
        text = " | ".join(head)
        if body:
            text += (" :- " if head else ":- ") + ", ".join(body)
        lines.append(text + ".")
    return "\n".join(lines) + "\n"


def test_ganak_backend_matches_brute_force() -> None:
    """The GANAK-backed counter (the evaluated configuration) vs brute-force stable models."""
    rng = random.Random(2507)
    checked = 0
    for _ in range(40):
        text = _random_program(rng, rng.randint(4, 9), rng.randint(5, 14))
        program = parse_program(text)
        expected, complete = enumerate_answer_sets(program)
        assert complete
        got = sharpasp_sr_count(program, backend="ganak")
        assert got["answer_sets"] == expected, (text, expected, got)
        checked += 1
    paper = parse_program("p0 | p1. q0 | q1. q0 :- w. q1 :- w. w :- p0. w :- p1, q1. :- not w.")
    assert sharpasp_sr_count(paper, backend="ganak")["answer_sets"] == 1
    print(f"ganak backend: {checked} random programs agree with brute-force enumeration")


def main() -> None:
    test_projected_count_unconstrained_projection()
    test_paper_example_count()
    test_copy_variables_are_fresh()
    test_small_programs_match_answer_set_semantics()
    test_ganak_backend_matches_brute_force()
    print("selftest passed")


if __name__ == "__main__":
    main()
