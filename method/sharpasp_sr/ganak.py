"""Thin wrapper around the GANAK exact (projected) model counter.

The paper's prototype uses GANAK as the projected model counter. GANAK is run
in its deterministic exact mode (``--prob 0``), so the returned counts carry no
probabilistic-hashing error.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[2]
_COUNT_RE = re.compile(r"^c s exact arb int (\d+)\s*$", re.MULTILINE)


def ganak_binary() -> str:
    candidates = []
    if os.environ.get("GANAK_BIN"):
        candidates.append(os.environ["GANAK_BIN"])
    candidates.append(str(ROOT / "data" / "downloads" / "ganak"))
    found = shutil.which("ganak")
    if found:
        candidates.append(found)
    for cand in candidates:
        if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    raise FileNotFoundError("GANAK binary not found; run scripts/download.sh (expects data/downloads/ganak)")


def write_dimacs(path: Path, num_vars: int, clauses: Iterable[Sequence[int]], projection: Sequence[int] | None = None) -> None:
    clauses = list(clauses)
    with open(path, "w") as handle:
        handle.write(f"p cnf {num_vars} {len(clauses)}\n")
        if projection is not None:
            handle.write("c p show " + " ".join(str(v) for v in projection) + " 0\n")
        for clause in clauses:
            handle.write(" ".join(str(lit) for lit in clause) + " 0\n")


def ganak_count(num_vars: int, clauses: Iterable[Sequence[int]], projection: Sequence[int] | None = None) -> int:
    """Exact model count (projected onto ``projection`` if given)."""
    binary = ganak_binary()
    with tempfile.TemporaryDirectory(prefix="ganak_") as tmp:
        cnf_path = Path(tmp) / "formula.cnf"
        write_dimacs(cnf_path, num_vars, clauses, projection)
        proc = subprocess.run(
            [binary, "--prob", "0", "--verb", "0", "--seed", "0", str(cnf_path)],
            capture_output=True,
            text=True,
            cwd=tmp,
            check=False,
        )
    match = _COUNT_RE.search(proc.stdout)
    if match is None:
        raise RuntimeError(f"GANAK failed (rc={proc.returncode}): {proc.stdout[-400:]} {proc.stderr[-400:]}")
    return int(match.group(1))
