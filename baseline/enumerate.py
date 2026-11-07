#!/usr/bin/env python3
"""Enumeration baseline (the paper's clingo baseline), counter interface.

Usage:
    python baseline/enumerate.py PROGRAM.lp          # count by full enumeration
    python baseline/enumerate.py --register          # write checkpoints/clingo_enumeration/counter.json

Enumerates every answer set with clingo and prints how many there are. Under
the evaluator's fixed per-instance budget this succeeds only when the count is
small enough to enumerate, which is the scaling limitation the paper targets.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def enumerate_all(path: Path) -> int:
    import clingo

    ctl = clingo.Control(["0", "--warn=none"])
    ctl.add("base", [], path.read_text())
    ctl.ground([("base", [])])
    result = ctl.solve()
    if not result.exhausted:
        raise SystemExit(1)
    return int(ctl.statistics["summary"]["models"]["enumerated"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("program", nargs="?")
    parser.add_argument("--register", action="store_true")
    parser.add_argument("--registry", default="checkpoints")
    args = parser.parse_args()
    if args.register:
        out = Path(args.registry) / "clingo_enumeration" / "counter.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"command": ["python", "baseline/enumerate.py"]}, indent=2) + "\n")
        print(f"registered clingo_enumeration -> {out}")
        return
    if not args.program:
        parser.error("PROGRAM.lp required")
    print(enumerate_all(Path(args.program)))


if __name__ == "__main__":
    main()
