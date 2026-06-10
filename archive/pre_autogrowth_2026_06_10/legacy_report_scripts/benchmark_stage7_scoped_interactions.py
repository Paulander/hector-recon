#!/usr/bin/env python3
"""Benchmark scoped visible-term interactions for Stage 7 offline.

This benchmark is diagnostic-only. It tests whether the non-causal visible-term
refinement candidates improve ranking when ambiguous terms are scoped by
state-local companion terms. It does not implement a runtime repair, promote
Stage 7, train Stage 8, or use DTM/tablebase at runtime.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Callable

import benchmark_stage7_training_objectives as bench


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _pair_feature(term_a: str, term_b: str) -> str:
    a, b = sorted([term_a, term_b])
    return f"PAIR::{a}&&{b}"


def _target_value(label: dict[str, Any]) -> float:
    target = str(label.get("target_class") or "")
    if bench._is_positive(label):
        return 3.0
    if target == "winning_nonoptimal_move":
        return 0.5
    return -3.0


def _candidate_sets(refinement: dict[str, Any]) -> dict[str, set[str]]:
    positive_terms = {
        str(item.get("term") or "")
        for item in refinement.get("positive_term_refinement_candidates") or []
        if item.get("term")
    }
    ambiguous_terms = {
        str(item.get("term") or "")
        for item in refinement.get("ambiguous_terms_requiring_scope") or []
        if item.get("term")
    }
    hard_context_terms = {
        str(item.get("term") or "")
        for item in refinement.get("hard_negative_or_veto_context_candidates") or []
        if item.get("term")
    }
    interaction_pairs = {
        _pair_feature(str(item.get("term_a") or ""), str(item.get("term_b") or ""))
        for item in refinement.get("interaction_refinement_candidates") or []
        if item.get("term_a") and item.get("term_b")
    }
    return {
        "positive_terms": positive_terms,
        "ambiguous_terms": ambiguous_terms,
        "hard_context_terms": hard_context_terms,
        "interaction_pairs": interaction_pairs,
    }


def _scoped_features(label: dict[str, Any], candidate_sets: dict[str, set[str]]) -> set[str]:
    terms = bench._all_terms(label)
    features: set[str] = set()
    ambiguous = candidate_sets["ambiguous_terms"]
    hard_context = candidate_sets["hard_context_terms"]
    for term in terms:
        if term in hard_context:
            features.add(f"HARD_CONTEXT::{term}")
        elif term not in ambiguous:
            features.add(f"TERM::{term}")

    for term_a, term_b in itertools.combinations(sorted(terms), 2):
        feature = _pair_feature(term_a, term_b)
        if feature in candidate_sets["interaction_pairs"]:
            features.add(feature)
    return features


def _fit_log_odds(
    train_steps: list[dict[str, Any]], feature_fn: Callable[[dict[str, Any]], set[str]]
) -> dict[str, float]:
    pos_counts: Counter[str] = Counter()
    neg_counts: Counter[str] = Counter()
    pos_total = 0
    neg_total = 0
    for step in train_steps:
        for label in step["labels"]:
            features = feature_fn(label)
            if bench._is_positive(label):
                pos_total += 1
                pos_counts.update(features)
            else:
                neg_total += 1
                neg_counts.update(features)
    weights: dict[str, float] = {}
    for feature in set(pos_counts) | set(neg_counts):
        p_pos = (pos_counts[feature] + 1.0) / (pos_total + 2.0)
        p_neg = (neg_counts[feature] + 1.0) / (neg_total + 2.0)
        weights[feature] = math.log(p_pos / p_neg)
    return weights


def _fit_ranked(
    train_steps: list[dict[str, Any]], feature_fn: Callable[[dict[str, Any]], set[str]]
) -> dict[str, float]:
    values: defaultdict[str, list[float]] = defaultdict(list)
    all_values: list[float] = []
    for step in train_steps:
        for label in step["labels"]:
            value = _target_value(label)
            all_values.append(value)
            for feature in feature_fn(label):
                values[feature].append(value)
    baseline = mean(all_values) if all_values else 0.0
    return {feature: mean(vals) - baseline for feature, vals in values.items() if vals}


def _score(weights: dict[str, float], features: set[str]) -> float:
    return sum(weights.get(feature, 0.0) for feature in features)


def _top_weights(weights: dict[str, float], limit: int = 20) -> dict[str, Any]:
    return {
        "positive": [
            {"feature": feature, "weight": value}
            for feature, value in sorted(weights.items(), key=lambda item: item[1], reverse=True)[:limit]
        ],
        "negative": [
            {"feature": feature, "weight": value}
            for feature, value in sorted(weights.items(), key=lambda item: item[1])[:limit]
        ],
    }


def _vote_score(label: dict[str, Any], candidate_sets: dict[str, set[str]]) -> float:
    terms = bench._all_terms(label)
    score = 0.0
    score += len(terms & candidate_sets["positive_terms"])
    score -= 0.4 * len(terms & candidate_sets["hard_context_terms"])
    for term_a, term_b in itertools.combinations(sorted(terms), 2):
        if _pair_feature(term_a, term_b) in candidate_sets["interaction_pairs"]:
            score += 2.0
    return score


def _model_lookup(benchmark: dict[str, Any], model_id: str) -> dict[str, Any]:
    for model in benchmark.get("models") or []:
        if model.get("model_id") == model_id:
            return model
    return {}


def build_benchmark(artifact_root: Path) -> dict[str, Any]:
    seed_path = artifact_root / "stage7_post_box_dtm_trajectory_seed_expanded_h40.json"
    objective_path = artifact_root / "stage7_training_objective_benchmark.json"
    refinement_path = artifact_root / "stage7_visible_term_refinement_audit.json"
    seed = _load_json(seed_path)
    objective = _load_json(objective_path)
    refinement = _load_json(refinement_path)
    steps = bench._trajectory_steps(seed)
    train_steps, test_steps = bench._split_steps(steps)
    candidate_sets = _candidate_sets(refinement)

    feature_fn = lambda label: _scoped_features(label, candidate_sets)
    log_odds = _fit_log_odds(train_steps, feature_fn)
    ranked = _fit_ranked(train_steps, feature_fn)

    models = [
        bench._evaluate_ranker(
            model_id="scoped_interaction_log_odds_scorer",
            train_steps=train_steps,
            test_steps=test_steps,
            score_fn=lambda label: _score(log_odds, feature_fn(label)),
            contribution_summary=_top_weights(log_odds),
        ),
        bench._evaluate_ranker(
            model_id="scoped_interaction_ranked_scorer",
            train_steps=train_steps,
            test_steps=test_steps,
            score_fn=lambda label: _score(ranked, feature_fn(label)),
            contribution_summary=_top_weights(ranked),
        ),
        bench._evaluate_ranker(
            model_id="state_local_refinement_vote_scorer",
            train_steps=train_steps,
            test_steps=test_steps,
            score_fn=lambda label: _vote_score(label, candidate_sets),
            contribution_summary={
                "positive_term_count": len(candidate_sets["positive_terms"]),
                "hard_context_term_count": len(candidate_sets["hard_context_terms"]),
                "interaction_pair_count": len(candidate_sets["interaction_pairs"]),
            },
        ),
    ]

    current = _model_lookup(objective, "current_learned_post_box_scorer")
    visible = _model_lookup(objective, "visible_term_log_odds_scorer")
    current_test = current.get("test") or {}
    visible_test = visible.get("test") or {}
    best_scoped = max(
        models,
        key=lambda model: (
            float((model.get("test") or {}).get("top1_dtm_positive_accuracy") or 0.0),
            -float((model.get("test") or {}).get("hard_negative_above_positive_rate") or 1.0),
        ),
    )
    best_test = best_scoped["test"]
    current_top1 = float(current_test.get("top1_dtm_positive_accuracy") or 0.0)
    visible_top1 = float(visible_test.get("top1_dtm_positive_accuracy") or 0.0)
    current_hard = float(current_test.get("hard_negative_above_positive_rate") or 1.0)
    visible_hard = float(visible_test.get("hard_negative_above_positive_rate") or 1.0)
    best_top1 = float(best_test.get("top1_dtm_positive_accuracy") or 0.0)
    best_hard = float(best_test.get("hard_negative_above_positive_rate") or 1.0)

    if best_top1 >= max(current_top1, visible_top1) + 0.10 and best_hard <= min(current_hard, visible_hard):
        candidate_status = "scoped_interaction_benchmark_supports_visible_term_refinement"
        next_step = "architecture review before any default-off visible-term sandbox"
    elif best_top1 >= visible_top1 and best_hard > visible_hard:
        candidate_status = "scoped_interaction_signal_but_hard_negative_calibration_gap"
        next_step = "do not patch; refine hard-negative/veto context offline"
    else:
        candidate_status = "scoped_interaction_benchmark_inconclusive"
        next_step = "do not patch; pause Stage 7 runtime work or request architecture review"

    benchmark = {
        "schema_version": "stage7_scoped_interaction_benchmark.v1",
        "causal_status": "non_causal_offline_benchmark",
        "runtime_behavior_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "stage7_status": "local_valid_composition_quarantined",
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": {
            "expanded_trajectory_seed": str(seed_path),
            "training_objective_benchmark": str(objective_path),
            "visible_term_refinement_audit": str(refinement_path),
        },
        "dataset": {
            "step_count": len(steps),
            "train_step_count": len(train_steps),
            "test_step_count": len(test_steps),
            "positive_term_count": len(candidate_sets["positive_terms"]),
            "hard_context_term_count": len(candidate_sets["hard_context_terms"]),
            "interaction_pair_count": len(candidate_sets["interaction_pairs"]),
        },
        "baseline_metrics": {
            "current_learned_post_box_scorer": current_test,
            "visible_term_log_odds_scorer": visible_test,
        },
        "models": models,
        "decision": {
            "candidate_status": candidate_status,
            "next_action": next_step,
            "best_scoped_model": best_scoped["model_id"],
            "best_top1_improvement_over_current": best_top1 - current_top1,
            "best_top1_improvement_over_visible": best_top1 - visible_top1,
            "best_hard_negative_delta_vs_current": best_hard - current_hard,
            "best_hard_negative_delta_vs_visible": best_hard - visible_hard,
        },
        "blocked_next_steps": [
            "implement_runtime_repair",
            "promote_stage7",
            "train_stage8",
            "add_support_adapter",
            "add_score_bonus_or_provider_penalty",
            "use_runtime_dtm_or_tablebase",
            "mutate_topology_during_gameplay",
        ],
    }
    validate_benchmark(benchmark)
    return benchmark


def validate_benchmark(benchmark: dict[str, Any]) -> None:
    if benchmark.get("schema_version") != "stage7_scoped_interaction_benchmark.v1":
        raise ValueError("unexpected benchmark schema")
    if benchmark.get("causal_status") != "non_causal_offline_benchmark":
        raise ValueError("benchmark must be non-causal")
    if benchmark.get("runtime_behavior_changed") is not False:
        raise ValueError("benchmark must not change runtime behavior")
    if benchmark.get("runtime_dtm_or_tablebase_lookup") is not False:
        raise ValueError("DTM/tablebase must not be runtime-causal")
    if benchmark.get("stage7_promotion_allowed") is not False or benchmark.get("stage8_training_allowed") is not False:
        raise ValueError("Stage 7 promotion and Stage 8 training must remain blocked")


def render_markdown(benchmark: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Scoped Interaction Benchmark",
        "",
        "This benchmark is offline-only and non-causal. It evaluates scoped interaction features before any runtime sandbox is considered.",
        "",
        "## Decision",
        "",
        f"- Candidate status: `{benchmark['decision']['candidate_status']}`",
        f"- Next action: {benchmark['decision']['next_action']}",
        f"- Best scoped model: `{benchmark['decision']['best_scoped_model']}`",
        f"- Best top-1 improvement over current: `{benchmark['decision']['best_top1_improvement_over_current']:.3f}`",
        f"- Best top-1 improvement over visible: `{benchmark['decision']['best_top1_improvement_over_visible']:.3f}`",
        f"- Best hard-negative delta vs current: `{benchmark['decision']['best_hard_negative_delta_vs_current']:.3f}`",
        f"- Best hard-negative delta vs visible: `{benchmark['decision']['best_hard_negative_delta_vs_visible']:.3f}`",
        "",
        "## Dataset",
        "",
        f"- `{benchmark['dataset']}`",
        "",
        "## Model Metrics",
        "",
    ]
    for model in benchmark["models"]:
        test = model["test"]
        train = model["train"]
        lines.extend(
            [
                f"### {model['model_id']}",
                "",
                f"- Train top1/top3 DTM-positive: `{train['top1_dtm_positive_accuracy']:.3f}` / `{train['top3_dtm_positive_accuracy']:.3f}`",
                f"- Test top1/top3 DTM-positive: `{test['top1_dtm_positive_accuracy']:.3f}` / `{test['top3_dtm_positive_accuracy']:.3f}`",
                f"- Test optimal top1/top3: `{test['dtm_optimal_top1_accuracy']:.3f}` / `{test['dtm_optimal_top3_accuracy']:.3f}`",
                f"- Test draw/stalemate top1 rate: `{test['draw_stalemate_candidate_top1_rate']:.3f}`",
                f"- Test hard-negative-above-positive rate: `{test['hard_negative_above_positive_rate']:.3f}`",
                f"- First miss: `{test['first_miss']}`",
                "",
            ]
        )
    lines.extend(["## Blocked Next Steps", ""])
    lines.extend(f"- {item}" for item in benchmark["blocked_next_steps"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=Path("reports/structural_candidates"))
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    benchmark = build_benchmark(args.artifact_root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(benchmark, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(benchmark), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(benchmark, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
