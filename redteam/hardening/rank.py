#!/usr/bin/env python3
"""Rank change of each counter relative to the reference rows.

Delta(X) = sum over scored experiments e of  weight_e * sum_m coefficient_{e,m} * (X_{e,m} - R_{e,m}),
where R is the experiment's 'proposed' row in scoring/reference.json (large_count_counting:
sharpasp_sr, hybrid_full_spectrum: hybrid_sharpasp_sr), scored on the same split.

Usage: python redteam/hardening/rank.py REFERENCE_SCORES.json OTHER_SCORES.json [...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    ref_cfg = json.loads((ROOT / "scoring/reference.json").read_text())["experiments"]
    base = json.loads(Path(sys.argv[1]).read_text())["experiments"]
    rows: dict[str, dict] = {}
    for path in sys.argv[1:]:
        for exp, data in json.loads(Path(path).read_text())["experiments"].items():
            for name, metrics in data["results"].items():
                rows.setdefault(name, {})[exp] = metrics
    out = {}
    for name, per_exp in sorted(rows.items()):
        total, parts = 0.0, {}
        for exp, metrics in per_exp.items():
            cfg = ref_cfg[exp]
            proposed = next(m for m, r in cfg["results"].items() if r["type"] == "proposed")
            ref = base[exp]["results"][proposed]
            delta = sum(c["coefficient"] * (metrics[m] - ref[m]) for m, c in cfg["metrics"].items())
            parts[exp] = round(cfg["weight"] * delta, 4)
            total += cfg["weight"] * delta
        out[name] = {"delta": round(total, 4), "by_experiment": parts}
        print(f"{name:36s} delta={total:+8.3f}  " + "  ".join(f"{e}={v:+.3f}" for e, v in parts.items()))
    return out


if __name__ == "__main__":
    main()
