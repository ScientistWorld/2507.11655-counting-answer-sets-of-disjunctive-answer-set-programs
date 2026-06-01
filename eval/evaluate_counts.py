#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def load_result(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def summarize_method(results: dict, manifest: dict) -> dict:
    expected = {item["name"]: item for item in manifest["instances"]}
    solved = 0
    exact = 0
    large_total = 0
    large_exact = 0
    small_total = 0
    small_exact = 0
    log_error_total = 0.0
    max_log = 0.0
    total_loop_atoms = 0
    total_phi2_ratio = 0.0
    structural_reports = 0
    miss_penalty = 32.0
    for name, item in expected.items():
        got = results.get("instances", {}).get(name)
        expected_count = item["expected_answer_sets"]
        expected_log = math.log2(expected_count) if expected_count > 0 else 0.0
        is_large = expected_count > 1000
        if not got:
            log_error_total += miss_penalty
            if is_large:
                large_total += 1
            else:
                small_total += 1
            continue
        complete = got.get("complete", True)
        if complete:
            solved += 1
        is_exact = complete and got.get("answer_sets") == expected_count
        if is_exact:
            exact += 1
        if is_large:
            large_total += 1
            if is_exact:
                large_exact += 1
        else:
            small_total += 1
            if is_exact:
                small_exact += 1
        if complete and got.get("answer_sets", 0) > 0:
            log_error_total += abs(math.log2(got["answer_sets"]) - expected_log)
        else:
            log_error_total += miss_penalty
        if complete and got.get("answer_sets", 0) > 0:
            max_log = max(max_log, math.log2(got["answer_sets"]))
        has_structure = "loop_atoms" in got and "phi1_clauses" in got and "phi2_clauses" in got
        if has_structure:
            structural_reports += 1
            total_loop_atoms += got["loop_atoms"]
            if got["phi1_clauses"]:
                total_phi2_ratio += got["phi2_clauses"] / got["phi1_clauses"]
    n = len(expected)
    return {
        "solved_instances": solved,
        "exact_count_accuracy": exact / n if n else 0.0,
        "large_exact_count_accuracy": large_exact / large_total if large_total else 0.0,
        "small_exact_count_accuracy": small_exact / small_total if small_total else 0.0,
        "answer_set_log2_mae": log_error_total / n if n else 0.0,
        "max_log2_count_solved": max_log,
        "avg_loop_atoms": total_loop_atoms / structural_reports if structural_reports else 0.0,
        "avg_phi2_to_phi1_clause_ratio": total_phi2_ratio / structural_reports if structural_reports else 0.0,
        "structural_report_fraction": structural_reports / n if n else 0.0,
    }


def summarize_hybrid(results: dict, manifest: dict) -> dict:
    summary = summarize_method(results, manifest)
    instances = results.get("instances", {})
    summary["fallback_instances"] = sum(1 for item in instances.values() if item.get("used_fallback"))
    summary["enumeration_completed_instances"] = sum(
        1 for item in instances.values() if item.get("complete", True) and not item.get("used_fallback", False)
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/benchmarks.json")
    parser.add_argument("--method-results", default="checkpoints/sharpasp_sr/results.json")
    parser.add_argument("--baseline-results", default="checkpoints/enumeration/results.json")
    parser.add_argument("--hybrid-results", default="checkpoints/hybrid/results.json")
    parser.add_argument("--output", default="scoring/scores.json")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text())
    method_result = load_result(Path(args.method_results))
    baseline_result = load_result(Path(args.baseline_results))
    hybrid_result = load_result(Path(args.hybrid_results))

    counting_results = {}
    hybrid_results = {}
    if baseline_result is not None:
        baseline_counting = summarize_method(baseline_result, manifest)
        counting_results["enumeration_cap_1000"] = baseline_counting
        hybrid_results["enumeration_cap_1000"] = summarize_hybrid(baseline_result, manifest)
    if method_result is not None:
        counting_results["sharpasp_sr"] = summarize_method(method_result, manifest)
    if hybrid_result is not None:
        hybrid_results["enumeration_then_sharpasp_sr"] = summarize_hybrid(hybrid_result, manifest)
    if not counting_results and not hybrid_results:
        raise FileNotFoundError("No result artifacts found to evaluate.")

    scores = {
        "experiments": {
            "scaled_disjunctive_counting": {
                "results": counting_results
            },
            "scaled_hybrid_counting": {
                "results": hybrid_results
            }
        }
    }
    Path(args.output).write_text(json.dumps(scores, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
