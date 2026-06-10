#!/usr/bin/env python3
"""Audit Stage 7 ranking calibration after the offline objective benchmark.

This is a diagnostic-only pass. It explains why simple objective variants do or
do not separate DTM-positive moves from winning-but-slower hard negatives using
existing trajectory labels. It does not train, route, mutate topology, or use
DTM/tablebase at runtime.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

import benchmark_stage7_training_objectives as bench


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _term_stats(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for step in steps:
        for label in step["labels"]:
            target = str(label.get("target_class") or "")
            bucket = (
                "positive"
                if bench._is_positive(label)
                else "hard_negative"
                if target == "winning_nonoptimal_move"
                else "non_winning"
            )
            for term in bench._all_terms(label):
                counts[term][bucket] += 1
    rows: list[dict[str, Any]] = []
    for term, counter in counts.items():
        positive = counter["positive"]
        hard_negative = counter["hard_negative"]
        non_winning = counter["non_winning"]
        total = positive + hard_negative + non_winning
        if total == 0:
            continue
        collision_score = min(positive, hard_negative) / float(max(positive, hard_negative, 1))
        rows.append(
            {
                "term": term,
                "positive_count": positive,
                "hard_negative_count": hard_negative,
                "non_winning_count": non_winning,
                "total_count": total,
                "positive_rate": positive / float(total),
                "hard_negative_rate": hard_negative / float(total),
                "non_winning_rate": non_winning / float(total),
                "collision_score": collision_score,
                "diagnosis": _term_diagnosis(term, positive, hard_negative, non_winning),
            }
        )
    rows.sort(
        key=lambda item: (
            item["collision_score"],
            item["hard_negative_count"],
            item["positive_count"],
        ),
        reverse=True,
    )
    return rows


def _term_diagnosis(term: str, positive: int, hard_negative: int, non_winning: int) -> str:
    if hard_negative and positive and hard_negative >= positive:
        if "rook_safe" in term or "not_increased" in term:
            return "overbroad_safety_or_non_regression_term"
        if "box_area" in term:
            return "overbroad_box_progress_term"
        if "king" in term or "support" in term:
            return "ambiguous_king_support_term"
        return "positive_hard_negative_collision"
    if non_winning > positive + hard_negative:
        return "safety_veto_candidate"
    if positive > hard_negative * 2:
        return "positive_separating_term"
    return "weak_or_neutral_term"


def _model_summary(benchmark: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for model in benchmark.get("models") or []:
        test = model.get("test") or {}
        rows.append(
            {
                "model_id": model.get("model_id"),
                "test_top1_dtm_positive_accuracy": test.get("top1_dtm_positive_accuracy"),
                "test_top3_dtm_positive_accuracy": test.get("top3_dtm_positive_accuracy"),
                "test_dtm_optimal_top1_accuracy": test.get("dtm_optimal_top1_accuracy"),
                "hard_negative_above_positive_rate": test.get("hard_negative_above_positive_rate"),
                "draw_stalemate_candidate_top1_rate": test.get("draw_stalemate_candidate_top1_rate"),
                "first_miss": test.get("first_miss"),
                "diagnosis": _model_diagnosis(model),
            }
        )
    return rows


def _model_diagnosis(model: dict[str, Any]) -> str:
    model_id = str(model.get("model_id") or "")
    test = model.get("test") or {}
    top1 = float(test.get("top1_dtm_positive_accuracy") or 0.0)
    top3 = float(test.get("top3_dtm_positive_accuracy") or 0.0)
    hard_neg = float(test.get("hard_negative_above_positive_rate") or 0.0)
    draw = float(test.get("draw_stalemate_candidate_top1_rate") or 0.0)
    if model_id.startswith("oracle_"):
        return "oracle_ceiling_not_runtime_candidate"
    if top3 >= 0.75 and top1 < 0.55 and hard_neg >= 0.4:
        return "candidate_set_contains_signal_but_hard_negative_calibration_fails"
    if top1 > 0.45 and hard_neg >= 0.35:
        return "top1_improves_but_hard_negatives_remain_too_high"
    if draw > 0.1:
        return "unsafe_draw_prone_objective"
    if top1 < 0.25 and hard_neg > 0.7:
        return "objective_overweights_ambiguous_hard_negative_terms"
    return "partial_signal_or_inconclusive"


def _label_distribution(steps: list[dict[str, Any]]) -> dict[str, Any]:
    targets = Counter()
    labels = Counter()
    moves_per_state = []
    positives_per_state = []
    for step in steps:
        moves_per_state.append(len(step["labels"]))
        pos = 0
        for label in step["labels"]:
            targets[str(label.get("target_class") or "")] += 1
            labels[int(label.get("label", 0) or 0)] += 1
            if bench._is_positive(label):
                pos += 1
        positives_per_state.append(pos)
    return {
        "target_class_counts": dict(targets),
        "binary_label_counts": {str(k): v for k, v in labels.items()},
        "avg_legal_moves_per_state": mean(moves_per_state) if moves_per_state else 0.0,
        "avg_positive_moves_per_state": mean(positives_per_state) if positives_per_state else 0.0,
        "hard_negative_to_positive_ratio": (
            targets["winning_nonoptimal_move"] / float(max(targets["optimal_dtm_move"], 1))
        ),
    }


def _family_first_misses(benchmark: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for model in benchmark.get("models") or []:
        first_miss = ((model.get("test") or {}).get("first_miss") or {})
        if not first_miss:
            continue
        rows.append(
            {
                "model_id": model.get("model_id"),
                "fen": first_miss.get("fen"),
                "selected_move": first_miss.get("selected_move"),
                "selected_target_class": first_miss.get("selected_target_class"),
                "positive_rank": first_miss.get("positive_rank"),
                "top_moves": first_miss.get("top_moves"),
            }
        )
    return rows


def build_audit(artifact_root: Path) -> dict[str, Any]:
    benchmark_path = artifact_root / "stage7_training_objective_benchmark.json"
    seed_path = artifact_root / "stage7_post_box_dtm_trajectory_seed_expanded_h40.json"
    benchmark = _load_json(benchmark_path)
    seed = _load_json(seed_path)
    steps = bench._trajectory_steps(seed)
    train_steps, test_steps = bench._split_steps(steps)
    term_rows = _term_stats(steps)
    model_rows = _model_summary(benchmark)

    high_collision_terms = [
        item
        for item in term_rows
        if item["positive_count"] > 0 and item["hard_negative_count"] > 0 and item["collision_score"] >= 0.25
    ][:25]
    positive_separators = [item for item in term_rows if item["diagnosis"] == "positive_separating_term"][:20]
    veto_candidates = [item for item in term_rows if item["diagnosis"] == "safety_veto_candidate"][:20]

    findings = []
    label_dist = _label_distribution(steps)
    if label_dist["hard_negative_to_positive_ratio"] > 3.0:
        findings.append(
            "Winning-nonoptimal hard negatives heavily outnumber optimal positives, so global term scorers are biased toward broad progress/safety terms shared by both classes."
        )
    if any(row["diagnosis"] == "top1_improves_but_hard_negatives_remain_too_high" for row in model_rows):
        findings.append(
            "At least one visible-term scorer improves top-1 but leaves hard-negative ranking too high, indicating calibration rather than missing signal alone."
        )
    if any(row["diagnosis"] == "objective_overweights_ambiguous_hard_negative_terms" for row in model_rows):
        findings.append(
            "The simple ranked objective overweights ambiguous terms and performs worse than the current learned scorer."
        )
    if high_collision_terms:
        findings.append(
            "Several visible terms are shared by positives and winning-nonoptimal hard negatives; state-local contrast or interaction terms are needed before another runtime sandbox."
        )

    audit = {
        "schema_version": "stage7_ranking_calibration_audit.v1",
        "causal_status": "non_causal_offline_audit",
        "runtime_behavior_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "stage7_status": "local_valid_composition_quarantined",
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": {
            "benchmark": str(benchmark_path),
            "expanded_trajectory_seed": str(seed_path),
        },
        "dataset": {
            "step_count": len(steps),
            "train_step_count": len(train_steps),
            "test_step_count": len(test_steps),
            **label_dist,
        },
        "model_error_profiles": model_rows,
        "term_collision_summary": {
            "high_collision_terms": high_collision_terms,
            "positive_separating_terms": positive_separators,
            "safety_veto_candidates": veto_candidates,
        },
        "first_miss_by_model": _family_first_misses(benchmark),
        "findings": findings,
        "candidate_status": "term_collision_and_state_local_ranking_gap",
        "recommended_next_step": (
            "Do not add runtime behavior. If continuing Stage 7, design the next offline benchmark around "
            "state-local contrastive ranking or interaction features that separate optimal DTM moves from "
            "winning-nonoptimal hard negatives; otherwise pause Stage 7 and ask for architecture review."
        ),
        "blocked_next_steps": [
            "runtime_repair",
            "stage7_promotion",
            "stage8_training",
            "support_adapter",
            "score_bonus_or_provider_penalty",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_audit(audit)
    return audit


def validate_audit(audit: dict[str, Any]) -> None:
    if audit.get("schema_version") != "stage7_ranking_calibration_audit.v1":
        raise ValueError("unexpected audit schema")
    if audit.get("causal_status") != "non_causal_offline_audit":
        raise ValueError("audit must be non-causal")
    if audit.get("runtime_behavior_changed") is not False:
        raise ValueError("audit must not change runtime behavior")
    if audit.get("runtime_dtm_or_tablebase_lookup") is not False:
        raise ValueError("audit must not use runtime DTM/tablebase")
    if audit.get("stage7_promotion_allowed") is not False or audit.get("stage8_training_allowed") is not False:
        raise ValueError("Stage 7 promotion and Stage 8 training must remain blocked")


def render_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Ranking Calibration Audit",
        "",
        "This audit is offline-only and non-causal. It explains ranking failures from existing benchmark/trajectory artifacts.",
        "",
        "## Status",
        "",
        f"- Candidate status: `{audit['candidate_status']}`",
        f"- Recommended next step: {audit['recommended_next_step']}",
        f"- Stage 7 promotion allowed: `{audit['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{audit['stage8_training_allowed']}`",
        "",
        "## Dataset",
        "",
        f"- Steps: `{audit['dataset']['step_count']}`",
        f"- Train/test: `{audit['dataset']['train_step_count']}` / `{audit['dataset']['test_step_count']}`",
        f"- Target classes: `{audit['dataset']['target_class_counts']}`",
        f"- Hard-negative/positive ratio: `{audit['dataset']['hard_negative_to_positive_ratio']:.3f}`",
        "",
        "## Findings",
        "",
    ]
    lines.extend(f"- {item}" for item in audit["findings"])
    lines.extend(["", "## Model Error Profiles", ""])
    for row in audit["model_error_profiles"]:
        lines.append(
            f"- `{row['model_id']}`: top1={row['test_top1_dtm_positive_accuracy']}, "
            f"top3={row['test_top3_dtm_positive_accuracy']}, "
            f"hard_neg_rate={row['hard_negative_above_positive_rate']}, diagnosis=`{row['diagnosis']}`"
        )
    lines.extend(["", "## High-Collision Terms", ""])
    for row in audit["term_collision_summary"]["high_collision_terms"][:12]:
        lines.append(
            f"- `{row['term']}`: pos={row['positive_count']}, hard_neg={row['hard_negative_count']}, "
            f"nonwin={row['non_winning_count']}, diagnosis=`{row['diagnosis']}`"
        )
    lines.extend(["", "## First Miss By Model", ""])
    for row in audit["first_miss_by_model"]:
        lines.append(
            f"- `{row['model_id']}`: move `{row['selected_move']}` as `{row['selected_target_class']}`, "
            f"positive_rank=`{row['positive_rank']}`"
        )
    lines.extend(["", "## Blocked Next Steps", ""])
    lines.extend(f"- {item}" for item in audit["blocked_next_steps"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=Path("reports/structural_candidates"))
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    audit = build_audit(args.artifact_root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(audit), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
