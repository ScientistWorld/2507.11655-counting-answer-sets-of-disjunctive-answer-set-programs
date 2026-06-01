#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


def paper_example_with_choices(n: int) -> str:
    rules = [
        "p0 | p1.",
        "q0 | q1.",
        "q0 :- w.",
        "q1 :- w.",
        "w :- p0.",
        "w :- p1, q1.",
        ":- not w.",
    ]
    for i in range(n):
        rules.append(f"c{i}_0 | c{i}_1.")
    return "\n".join(rules) + "\n"


def main() -> None:
    root = Path("data/instances")
    root.mkdir(parents=True, exist_ok=True)
    specs = [
        ("paper_example", 0),
        ("choices_8", 8),
        ("choices_12", 12),
        ("choices_14", 14),
    ]
    instances = []
    for name, n in specs:
        path = root / f"{name}.lp"
        path.write_text(paper_example_with_choices(n))
        instances.append(
            {
                "name": name,
                "path": str(path),
                "choice_pairs": n,
                "expected_answer_sets": 2**n,
                "source": "Paper Example 1 extended with independent disjunctive choice pairs.",
            }
        )
    Path("data/benchmarks.json").write_text(json.dumps({"instances": instances}, indent=2) + "\n")


if __name__ == "__main__":
    main()
