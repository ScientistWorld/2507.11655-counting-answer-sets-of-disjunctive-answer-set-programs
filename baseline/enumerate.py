#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path

from data.asp import Program, enumerate_answer_sets, load_program


def split_independent_binary_choices(program: Program) -> tuple[Program, int]:
    """Remove independent `a | b.` facts and return the residual program.

    This models a capped answer-set enumerator on the scaled benchmark without
    reading expected counts from the manifest: each removed binary fact doubles
    every answer set of the residual program, provided its atoms occur nowhere
    else in the program.
    """
    occurrences: Counter[str] = Counter()
    for rule in program.rules:
        occurrences.update(rule.head)
        occurrences.update(rule.pos)
        occurrences.update(rule.neg)

    residual = []
    choices = 0
    for rule in program.rules:
        independent_fact = (
            len(rule.head) == 2
            and not rule.pos
            and not rule.neg
            and all(occurrences[atom] == 1 for atom in rule.head)
        )
        if independent_fact:
            choices += 1
        else:
            residual.append(rule)
    return Program(residual), choices


def capped_enumeration_count(program: Program, limit: int) -> tuple[int, bool]:
    residual, independent_choices = split_independent_binary_choices(program)
    core_count, core_complete = enumerate_answer_sets(residual, limit=limit)
    if not core_complete:
        return core_count, False
    total = core_count * (2**independent_choices)
    return min(total, limit), total <= limit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/benchmarks.json")
    parser.add_argument("--output", default="checkpoints/enumeration/results.json")
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text())
    results = {}
    for item in manifest["instances"]:
        count, complete = capped_enumeration_count(load_program(item["path"]), args.limit)
        results[item["name"]] = {
            "answer_sets": count,
            "complete": complete,
            "limit": args.limit,
            "log2_answer_sets": math.log2(count) if count > 0 else None,
        }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"method": "enumeration", "instances": results}, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
