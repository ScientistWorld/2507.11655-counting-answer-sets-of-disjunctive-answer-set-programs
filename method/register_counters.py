#!/usr/bin/env python3
"""Register the paper's counters for evaluation.

Writes checkpoints/<name>/counter.json for:
  sharpasp_sr         -- direct subtractive-reduction counter (GANAK backend)
  hybrid_sharpasp_sr  -- clingo enumeration up to 10^4 answer sets, then sharpASP-sR
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

COUNTERS = {
    "sharpasp_sr": ["python", "method/count.py", "--mode", "direct"],
    "hybrid_sharpasp_sr": ["python", "method/count.py", "--mode", "hybrid", "--enum-limit", "10000"],
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="checkpoints")
    args = parser.parse_args()
    for name, command in COUNTERS.items():
        out = Path(args.registry) / name / "counter.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"command": command}, indent=2) + "\n")
        print(f"registered {name} -> {out}")


if __name__ == "__main__":
    main()
