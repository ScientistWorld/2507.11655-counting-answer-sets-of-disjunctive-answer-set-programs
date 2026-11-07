#!/usr/bin/env python3
"""Better / weaker variants of the reference counter, used only for the hardening check.

  --encoding paper   : the paper's two-copy surplus formula phi2 (reference)
  --encoding onecopy : Comp(P) & Copy(P)' & OR_{x in LA}(x & ~x') projected on at(P).
                       By Lemma 3 a completion model M is not an answer set iff
                       Copy(P)|M & OR_{x in M & LA} ~x' is satisfiable, which is
                       exactly what this formula's projection counts; it needs one
                       copy set instead of two.
  --mode hybrid --enum-limit N : clingo enumeration up to N answer sets first.
  --no-surplus       : weaker: report #Comp(P) only (drops the stable-model correction).
  --backend python   : weaker: the paper's reduction on the small in-repo counter.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "method"))

from count import enumerate_up_to  # noqa: E402  (method/count.py)
from data.asp import load_program, loop_atoms  # noqa: E402
from sharpasp_sr.cnf import CNF  # noqa: E402
from sharpasp_sr.ganak import ganak_count  # noqa: E402
from sharpasp_sr.reduction import add_completion, add_copy, build_phi1, build_phi2, sharpasp_sr_count  # noqa: E402


def onecopy_phi2(program):
    cnf = CNF()
    for atom in program.atoms:
        cnf.var(atom)
    add_completion(cnf, program)
    loops = loop_atoms(program)
    prime = add_copy(cnf, program, loops, "__prime")
    diff = []
    for atom in sorted(loops):
        aux = cnf.new_aux(f"diff_{atom}")
        cnf.add_and_equiv(aux, [cnf.lit(atom), cnf.lit(prime[atom], False)])
        diff.append(aux)
    cnf.add_clause(diff)
    return cnf, [cnf.var(atom) for atom in program.atoms]


def count(program, encoding: str, no_surplus: bool, backend: str) -> int:
    if backend == "python":
        return sharpasp_sr_count(program, backend="python")["answer_sets"]
    phi1, _, loops = build_phi1(program)
    overcount = ganak_count(len(phi1.var_ids), phi1.clauses)
    if no_surplus or not loops:
        return overcount
    if encoding == "paper":
        phi2, keep, _ = build_phi2(program)
    else:
        phi2, keep = onecopy_phi2(program)
    return overcount - ganak_count(len(phi2.var_ids), phi2.clauses, keep)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("program")
    parser.add_argument("--encoding", choices=["paper", "onecopy"], default="paper")
    parser.add_argument("--mode", choices=["direct", "hybrid"], default="direct")
    parser.add_argument("--enum-limit", type=int, default=10_000)
    parser.add_argument("--no-surplus", action="store_true")
    parser.add_argument("--backend", choices=["ganak", "python"], default="ganak")
    args = parser.parse_args()
    path = Path(args.program)
    if args.mode == "hybrid":
        n = enumerate_up_to(path, args.enum_limit)
        if n is not None:
            print(n)
            return
    print(count(load_program(path), args.encoding, args.no_surplus, args.backend))


if __name__ == "__main__":
    main()
