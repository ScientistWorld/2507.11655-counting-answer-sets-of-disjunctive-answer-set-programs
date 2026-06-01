#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Artifact:
    name: str
    path: Path
    results: dict


def unique_result_paths(results_root: Path, explicit_paths: list[str]) -> list[Path]:
    paths: list[Path] = []
    if results_root.exists():
        paths.extend(sorted(results_root.glob("*/results.json")))
    paths.extend(Path(item) for item in explicit_paths)

    unique: dict[Path, Path] = {}
    for path in paths:
        if path.exists():
            unique[path.resolve()] = path
    return list(unique.values())


def artifact_name(path: Path, results: dict) -> str:
    raw_name = str(results.get("method") or path.parent.name)
    if raw_name == "enumeration":
        limit = results.get("limit")
        for item in results.get("instances", {}).values():
            limit = item.get("limit", limit)
            if limit is not None:
                break
        if limit is not None:
            return f"enumeration_cap_{limit}"
    return raw_name


def load_artifacts(results_root: Path, explicit_paths: list[str]) -> dict[str, Artifact]:
    artifacts: dict[str, Artifact] = {}
    for path in unique_result_paths(results_root, explicit_paths):
        results = json.loads(path.read_text())
        name = artifact_name(path, results)
        artifacts[name] = Artifact(name=name, path=path, results=results)
    if not artifacts:
        raise FileNotFoundError(
            f"No result artifacts found under {results_root} and no explicit result paths existed."
        )
    return artifacts


def has_hybrid_fields(results: dict) -> bool:
    if "enumeration_limit" in results or "fallback_instances" in results:
        return True
    return any("used_fallback" in item for item in results.get("instances", {}).values())


def is_enumeration_baseline(name: str) -> bool:
    return name.startswith("enumeration_cap_")


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
    parser.add_argument("--results-root", default="checkpoints")
    parser.add_argument("--method-results", action="append", default=[])
    parser.add_argument("--baseline-results", action="append", default=[])
    parser.add_argument("--hybrid-results", action="append", default=[])
    parser.add_argument("--output", default="scoring/scores.json")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text())
    explicit_paths = args.method_results + args.baseline_results + args.hybrid_results
    artifacts = load_artifacts(Path(args.results_root), explicit_paths)

    counting_results = {}
    hybrid_results = {}
    for name, artifact in sorted(artifacts.items()):
        hybrid_like = has_hybrid_fields(artifact.results)
        if not hybrid_like or is_enumeration_baseline(name):
            counting_results[name] = summarize_method(artifact.results, manifest)
        if hybrid_like or is_enumeration_baseline(name):
            hybrid_results[name] = summarize_hybrid(artifact.results, manifest)

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
