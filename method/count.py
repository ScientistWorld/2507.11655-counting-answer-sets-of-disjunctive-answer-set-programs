#!/usr/bin/env python3
"""Count answer sets of a ground disjunctive ASP program (counter interface).

Usage:
    python method/count.py [--mode direct|hybrid] [--enum-limit N] PROGRAM.lp

Prints the exact number of answer sets as the last stdout line. Exits non-zero
if no exact count could be produced.

  direct : sharpASP-sR, i.e. #Comp(P) - #exists(CV' u CV*) phi2 with GANAK.
  hybrid : the paper's hybrid counter: enumerate answer sets with clingo up to
           N (default 10^4, the paper's switching threshold); if enumeration
           does not finish within N answer sets, fall back to sharpASP-sR.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "method"))

from data.asp import load_program  # noqa: E402
from sharpasp_sr.reduction import sharpasp_sr_count  # noqa: E402


def enumerate_up_to(path: Path, limit: int) -> int | None:
    """Return the answer-set count if clingo enumerates all of them within ``limit``."""
    import clingo

    ctl = clingo.Control([str(limit + 1), "--warn=none"])
    ctl.add("base", [], path.read_text())
    ctl.ground([("base", [])])
    result = ctl.solve()
    enumerated = int(ctl.statistics["summary"]["models"]["enumerated"])
    if result.exhausted and enumerated <= limit:
        return enumerated
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("program")
    parser.add_argument("--mode", choices=["direct", "hybrid"], default="direct")
    parser.add_argument("--enum-limit", type=int, default=10_000)
    args = parser.parse_args()

    path = Path(args.program)
    if args.mode == "hybrid":
        count = enumerate_up_to(path, args.enum_limit)
        if count is not None:
            print(count)
            return
    result = sharpasp_sr_count(load_program(path), backend="ganak")
    print(result["answer_sets"])


if __name__ == "__main__":
    main()
