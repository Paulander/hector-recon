#!/usr/bin/env python3
"""Offline Stage 7 training-objective benchmark.

This compares scoring objectives on existing Stage 7 post-box DTM trajectory
labels. It is non-causal: no runtime repair, no topology mutation, no Stage 8
training, and no tablebase/DTM lookup outside the precomputed artifacts.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Callable


DEFAULT_ARTIFACTS = {
    "neutral_matrix": "stage7_neutral_diagnostic_matrix.json",
    "evidence_merge": "stage7_evidence_merge_table.json",
    "trajectory_seed": "stage7_post_box_dtm_trajectory_seed_h40.json",
    "expanded_trajectory_seed": "stage7_post_box_dtm_trajectory_seed_expanded_h40.json",
    "capsule_fidelity": "stage7_capsule_trajectory_fidelity_audit.json",
    "expanded_capsule_fidelity": "stage7_expanded_ranked_capsule_trajectory_fidelity_audit.json",
    "expanded_capsule_replay": "stage7_expanded_ranked_capsule_phase1_replay_h40.json",
    "candidate_move_0926": "stage7_0926_move_shape_role_candidate_audit.json",
    "candidate_move_2cc": "stage7_2cc_candidate_move_dtm_alignment.json",
    "remaining_dtm": "stage7_remaining_dtm_candidate_summary.json",
    "family_diagnosis": "stage7_post_box_family_diagnosis.json",
}


def _load_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _all_terms(label: dict[str, Any], *, include_coordinate_terms: bool = False) -> set[str]:
    keys = ["move_shape_terms", "post_move_terms", "worst_reply_terms", "safety_terms"]
    if include_coordinate_terms:
        keys.append("coordinate_terms")
    terms: set[str] = set()
    for key in keys:
        for term in label.get(key) or []:
            terms.add(f"{key}.{term}")
    piece = label.get("piece")
    if piece:
        terms.add(f"piece.{piece}")
    return terms


def _target_value(label: dict[str, Any]) -> float:
    target = str(label.get("target_class") or "")
    if target == "optimal_dtm_move" or int(label.get("label", 0) or 0) == 1:
        return 3.0
    if target == "winning_nonoptimal_move":
        child = label.get("child_dtm")
        # Winning but slower moves are acceptable, not primary targets.
        return 1.0 if child is not None else 0.75
    return -2.0


def _is_positive(label: dict[str, Any]) -> bool:
    return int(label.get("label", 0) or 0) == 1 or str(label.get("target_class") or "") == "optimal_dtm_move"


def _is_optimal(label: dict[str, Any]) -> bool:
    return str(label.get("target_class") or "") == "optimal_dtm_move"


def _is_hard_negative(label: dict[str, Any]) -> bool:
    return str(label.get("target_class") or "") == "winning_nonoptimal_move"


def _is_bad_safety(label: dict[str, Any]) -> bool:
    target = str(label.get("target_class") or "")
    terms = set(label.get("safety_terms") or []) | set(label.get("post_move_terms") or [])
    return target == "non_winning_move" or any(
        term in terms for term in ["draw_after_move", "stalemate_after_move", "rook_unsafe_after_move"]
    )


def _trajectory_steps(seed: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for trajectory_index, trajectory in enumerate(seed.get("trajectories") or []):
        if not isinstance(trajectory, dict):
            continue
        for step_index, step in enumerate(trajectory.get("white_training_steps") or []):
            if not isinstance(step, dict) or not step.get("fen"):
                continue
            labels = [dict(item) for item in step.get("legal_move_labels") or [] if isinstance(item, dict)]
            if not labels:
                continue
            rows.append(
                {
                    "trajectory_index": trajectory_index,
                    "step_index": step_index,
                    "fen": str(step["fen"]),
                    "teacher_move": str(step.get("move") or ""),
                    "labels": labels,
                }
            )
    return rows


def _split_steps(steps: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    train: list[dict[str, Any]] = []
    test: list[dict[str, Any]] = []
    for row in steps:
        # Family-split-ish deterministic holdout: every fourth trajectory.
        if int(row["trajectory_index"]) % 4 == 0:
            test.append(row)
        else:
            train.append(row)
    if not train and test:
        train, test = test[:-1], test[-1:]
    if not test and train:
        test = train[-max(1, len(train) // 5) :]
        train = train[: -len(test)] or train
    return train, test


def _fit_log_odds(train_steps: list[dict[str, Any]], *, include_coordinate_terms: bool = False) -> dict[str, float]:
    pos_counts: Counter[str] = Counter()
    neg_counts: Counter[str] = Counter()
    pos_total = 0
    neg_total = 0
    for step in train_steps:
        for label in step["labels"]:
            terms = _all_terms(label, include_coordinate_terms=include_coordinate_terms)
            if _is_positive(label):
                pos_total += 1
                pos_counts.update(terms)
            else:
                neg_total += 1
                neg_counts.update(terms)
    vocab = set(pos_counts) | set(neg_counts)
    weights: dict[str, float] = {}
    for term in vocab:
        p_pos = (pos_counts[term] + 1.0) / (pos_total + 2.0)
        p_neg = (neg_counts[term] + 1.0) / (neg_total + 2.0)
        weights[term] = math.log(p_pos / p_neg)
    return weights


def _fit_ranked_weights(train_steps: list[dict[str, Any]], *, include_coordinate_terms: bool = False) -> dict[str, float]:
    values: defaultdict[str, list[float]] = defaultdict(list)
    all_values: list[float] = []
    for step in train_steps:
        for label in step["labels"]:
            value = _target_value(label)
            all_values.append(value)
            for term in _all_terms(label, include_coordinate_terms=include_coordinate_terms):
                values[term].append(value)
    baseline = mean(all_values) if all_values else 0.0
    return {term: mean(vals) - baseline for term, vals in values.items() if vals}


def _score_with_weights(weights: dict[str, float], label: dict[str, Any], *, include_coordinate_terms: bool = False) -> float:
    return sum(weights.get(term, 0.0) for term in _all_terms(label, include_coordinate_terms=include_coordinate_terms))


def _heuristic_score(kind: str, label: dict[str, Any]) -> float:
    terms = set(label.get("move_shape_terms") or []) | set(label.get("post_move_terms") or []) | set(
        label.get("safety_terms") or []
    )
    score = 0.0
    if kind == "king_support_improvement":
        score += 2.0 if "king_moves_toward_rook_support" in terms else 0.0
        score += 2.0 if "white_king_distance_to_rook_decreases" in terms else 0.0
        score += 1.5 if "white_king_distance_to_enemy_decreases" in terms else 0.0
    elif kind == "fence_cut_preservation":
        score += 2.0 if "cut_preserved_after_move" in terms or "cut_created_after_move" in terms else 0.0
        score += 2.0 if "fence_exists_after_move" in terms else 0.0
        score += 2.0 if "fence_stable_after_move" in terms else 0.0
    elif kind == "edge_corner_net_pressure":
        score += 2.0 if "corner_net_pressure_increases" in terms else 0.0
        score += 1.5 if "enemy_corner_distance_decreases_after_move" in terms else 0.0
        score += 1.0 if "rook_to_edge_file" in terms or "rook_to_edge_rank" in terms else 0.0
        score += 1.5 if "safe_check_created" in terms or "checking_line_created" in terms else 0.0
    elif kind == "box_area_relevance":
        score += 2.0 if "box_area_decreases_after_move" in terms else 0.0
        score += 1.0 if "box_area_not_increased_after_move" in terms else 0.0
        score += 1.0 if "black_king_escape_count_decreases_after_move" in terms else 0.0
    elif kind == "safety_non_draw_rook_safe":
        score += 2.0 if "rook_safe_after_move" in terms or "rook_safe_after_candidate" in terms else 0.0
        score -= 5.0 if _is_bad_safety(label) else 0.0
        score -= 1.0 if "black_king_escape_count_increases_after_move" in terms else 0.0
    else:
        raise ValueError(f"unknown heuristic kind: {kind}")
    return score


def _rank_labels(labels: list[dict[str, Any]], score_fn: Callable[[dict[str, Any]], float]) -> list[dict[str, Any]]:
    rows = [
        {
            "move": str(label.get("move") or ""),
            "score": float(score_fn(label)),
            "target_class": label.get("target_class"),
            "label": label.get("label"),
            "child_dtm": label.get("child_dtm"),
            "is_positive": _is_positive(label),
            "is_optimal": _is_optimal(label),
            "is_hard_negative": _is_hard_negative(label),
            "is_bad_safety": _is_bad_safety(label),
        }
        for label in labels
    ]
    # Tie-break without label/DTM leakage. Otherwise a zero-information scorer
    # can look perfect simply because positive moves sort ahead of negatives.
    return sorted(rows, key=lambda item: (-item["score"], item["move"]))


def _first_positive_rank(ranked: list[dict[str, Any]]) -> int | None:
    for idx, item in enumerate(ranked, start=1):
        if item["is_positive"]:
            return idx
    return None


def _first_optimal_rank(ranked: list[dict[str, Any]]) -> int | None:
    for idx, item in enumerate(ranked, start=1):
        if item["is_optimal"]:
            return idx
    return None


def _evaluate_ranker(
    *,
    model_id: str,
    train_steps: list[dict[str, Any]],
    test_steps: list[dict[str, Any]],
    score_fn: Callable[[dict[str, Any]], float],
    contribution_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    def eval_split(split_steps: list[dict[str, Any]]) -> dict[str, Any]:
        top1_positive = 0
        top3_positive = 0
        top1_optimal = 0
        top3_optimal = 0
        bad_safety_top1 = 0
        hard_negative_above_positive = 0
        first_miss: dict[str, Any] | None = None
        rows: list[dict[str, Any]] = []
        for row in split_steps:
            ranked = _rank_labels(row["labels"], score_fn)
            if not ranked:
                continue
            top3 = ranked[:3]
            positive_rank = _first_positive_rank(ranked)
            optimal_rank = _first_optimal_rank(ranked)
            if ranked[0]["is_positive"]:
                top1_positive += 1
            if any(item["is_positive"] for item in top3):
                top3_positive += 1
            if ranked[0]["is_optimal"]:
                top1_optimal += 1
            if any(item["is_optimal"] for item in top3):
                top3_optimal += 1
            if ranked[0]["is_bad_safety"]:
                bad_safety_top1 += 1
            if positive_rank is not None:
                best_hard_neg_rank = next((idx for idx, item in enumerate(ranked, start=1) if item["is_hard_negative"]), None)
                if best_hard_neg_rank is not None and best_hard_neg_rank < positive_rank:
                    hard_negative_above_positive += 1
            if first_miss is None and not ranked[0]["is_positive"]:
                first_miss = {
                    "trajectory_index": row["trajectory_index"],
                    "step_index": row["step_index"],
                    "fen": row["fen"],
                    "selected_move": ranked[0]["move"],
                    "selected_target_class": ranked[0]["target_class"],
                    "positive_rank": positive_rank,
                    "top_moves": ranked[:5],
                }
            rows.append(
                {
                    "trajectory_index": row["trajectory_index"],
                    "step_index": row["step_index"],
                    "fen": row["fen"],
                    "top_move": ranked[0],
                    "positive_rank": positive_rank,
                    "optimal_rank": optimal_rank,
                    "top3_moves": top3,
                }
            )
        total = len(split_steps)
        denom = float(total or 1)
        return {
            "state_count": total,
            "top1_dtm_positive_accuracy": top1_positive / denom,
            "top3_dtm_positive_accuracy": top3_positive / denom,
            "dtm_optimal_top1_accuracy": top1_optimal / denom,
            "dtm_optimal_top3_accuracy": top3_optimal / denom,
            "draw_stalemate_candidate_top1_rate": bad_safety_top1 / denom,
            "hard_negative_above_positive_rate": hard_negative_above_positive / denom,
            "first_miss": first_miss,
            "sample_rows": rows[:8],
        }

    result = {
        "model_id": model_id,
        "train": eval_split(train_steps),
        "test": eval_split(test_steps),
        "contribution_summary": contribution_summary or {},
    }
    return result


def _evaluate_current_scorer(fidelity: dict[str, Any]) -> dict[str, Any]:
    records = [r for r in fidelity.get("teacher_forced_records") or [] if isinstance(r, dict)]
    train = [r for r in records if int(r.get("trajectory_index", 0) or 0) % 4 != 0]
    test = [r for r in records if int(r.get("trajectory_index", 0) or 0) % 4 == 0]
    if not test and records:
        test = records[-max(1, len(records) // 5) :]
        train = records[: -len(test)] or records

    def eval_records(split: list[dict[str, Any]]) -> dict[str, Any]:
        top1_pos = top3_pos = top1_opt = top3_opt = hard_neg = bad_safety = 0
        first_miss = None
        rows = []
        for record in split:
            top_moves = [item for item in record.get("top_moves") or [] if isinstance(item, dict)]
            if not top_moves:
                continue
            top = top_moves[0]
            top3 = top_moves[:3]
            if int(top.get("label", 0) or 0) == 1:
                top1_pos += 1
            if any(int(item.get("label", 0) or 0) == 1 for item in top3):
                top3_pos += 1
            if str(top.get("target_class") or "") == "optimal_dtm_move":
                top1_opt += 1
            if any(str(item.get("target_class") or "") == "optimal_dtm_move" for item in top3):
                top3_opt += 1
            if str(top.get("target_class") or "") == "non_winning_move":
                bad_safety += 1
            positive_rank = record.get("positive_move_rank")
            if positive_rank is not None:
                hard_neg_rank = next(
                    (
                        idx
                        for idx, item in enumerate(top_moves, start=1)
                        if str(item.get("target_class") or "") == "winning_nonoptimal_move"
                    ),
                    None,
                )
                if hard_neg_rank is not None and int(hard_neg_rank) < int(positive_rank):
                    hard_neg += 1
            if first_miss is None and int(top.get("label", 0) or 0) != 1:
                first_miss = {
                    "trajectory_index": record.get("trajectory_index"),
                    "step_index": record.get("step_index"),
                    "fen": record.get("fen"),
                    "selected_move": top.get("move"),
                    "selected_target_class": top.get("target_class"),
                    "positive_rank": positive_rank,
                    "top_moves": top_moves[:5],
                }
            rows.append(
                {
                    "trajectory_index": record.get("trajectory_index"),
                    "step_index": record.get("step_index"),
                    "fen": record.get("fen"),
                    "top_move": top,
                    "positive_rank": positive_rank,
                    "optimal_rank": record.get("optimal_move_rank"),
                    "top3_moves": top3,
                }
            )
        total = len(split)
        denom = float(total or 1)
        return {
            "state_count": total,
            "top1_dtm_positive_accuracy": top1_pos / denom,
            "top3_dtm_positive_accuracy": top3_pos / denom,
            "dtm_optimal_top1_accuracy": top1_opt / denom,
            "dtm_optimal_top3_accuracy": top3_opt / denom,
            "draw_stalemate_candidate_top1_rate": bad_safety / denom,
            "hard_negative_above_positive_rate": hard_neg / denom,
            "first_miss": first_miss,
            "sample_rows": rows[:8],
        }

    return {
        "model_id": "current_learned_post_box_scorer",
        "train": eval_records(train),
        "test": eval_records(test),
        "contribution_summary": {
            "source": "stage7_expanded_ranked_capsule_trajectory_fidelity_audit.teacher_forced_records",
        },
    }


def _top_weights(weights: dict[str, float], n: int = 12) -> dict[str, list[dict[str, Any]]]:
    positive = sorted(weights.items(), key=lambda item: item[1], reverse=True)[:n]
    negative = sorted(weights.items(), key=lambda item: item[1])[:n]
    return {
        "positive_terms": [{"term": term, "weight": weight} for term, weight in positive],
        "negative_terms": [{"term": term, "weight": weight} for term, weight in negative],
    }


def _oracle_result(steps: list[dict[str, Any]], model_id: str) -> dict[str, Any]:
    return {
        "model_id": model_id,
        "train": {
            "state_count": len(steps),
            "top1_dtm_positive_accuracy": 1.0 if steps else 0.0,
            "top3_dtm_positive_accuracy": 1.0 if steps else 0.0,
            "dtm_optimal_top1_accuracy": 1.0 if steps else 0.0,
            "dtm_optimal_top3_accuracy": 1.0 if steps else 0.0,
            "draw_stalemate_candidate_top1_rate": 0.0,
            "hard_negative_above_positive_rate": 0.0,
            "first_miss": None,
            "sample_rows": [],
        },
        "test": {
            "state_count": len(steps),
            "top1_dtm_positive_accuracy": 1.0 if steps else 0.0,
            "top3_dtm_positive_accuracy": 1.0 if steps else 0.0,
            "dtm_optimal_top1_accuracy": 1.0 if steps else 0.0,
            "dtm_optimal_top3_accuracy": 1.0 if steps else 0.0,
            "draw_stalemate_candidate_top1_rate": 0.0,
            "hard_negative_above_positive_rate": 0.0,
            "first_miss": None,
            "sample_rows": [],
        },
        "contribution_summary": {
            "ceiling_type": "offline_label_oracle",
            "runtime_causal": False,
        },
    }


def _known_failed_move_analysis(models: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for model in models:
        for split_name in ["train", "test"]:
            split = model.get(split_name) or {}
            first_miss = split.get("first_miss")
            if first_miss:
                rows.append(
                    {
                        "model_id": model["model_id"],
                        "split": split_name,
                        "selected_move": first_miss.get("selected_move"),
                        "selected_target_class": first_miss.get("selected_target_class"),
                        "positive_rank": first_miss.get("positive_rank"),
                    }
                )
    return {
        "known_failed_move_rows": rows,
        "models_ranking_failed_moves_above_positive_count": sum(
            1 for row in rows if row.get("positive_rank") is None or int(row.get("positive_rank") or 999) > 1
        ),
    }


def _controls(artifact_root: Path) -> dict[str, Any]:
    audit_0926 = _load_optional_json(artifact_root / DEFAULT_ARTIFACTS["candidate_move_0926"])
    align_2cc = _load_optional_json(artifact_root / DEFAULT_ARTIFACTS["candidate_move_2cc"])
    return {
        "candidate_move_0926": {
            "summary": audit_0926.get("summary") or {},
            "causal_status": audit_0926.get("causal_status"),
        },
        "candidate_move_2cc": {
            "dtm": align_2cc.get("dtm") or {},
            "legal_first_current_graph": align_2cc.get("legal_first_current_graph") or {},
            "candidate_diagnosis": (align_2cc.get("candidate_update") or {}).get("diagnosis"),
        },
    }


def build_benchmark(artifact_root: Path) -> dict[str, Any]:
    expanded_seed = _load_optional_json(artifact_root / DEFAULT_ARTIFACTS["expanded_trajectory_seed"])
    if not expanded_seed:
        expanded_seed = _load_optional_json(artifact_root / DEFAULT_ARTIFACTS["trajectory_seed"])
    fidelity = _load_optional_json(artifact_root / DEFAULT_ARTIFACTS["expanded_capsule_fidelity"])
    if not fidelity:
        fidelity = _load_optional_json(artifact_root / DEFAULT_ARTIFACTS["capsule_fidelity"])

    steps = _trajectory_steps(expanded_seed)
    train_steps, test_steps = _split_steps(steps)

    log_odds_weights = _fit_log_odds(train_steps)
    ranked_weights = _fit_ranked_weights(train_steps)
    ranked_coord_weights = _fit_ranked_weights(train_steps, include_coordinate_terms=True)

    models: list[dict[str, Any]] = []
    models.append(_evaluate_current_scorer(fidelity))
    models.append(
        _evaluate_ranker(
            model_id="visible_term_log_odds_scorer",
            train_steps=train_steps,
            test_steps=test_steps,
            score_fn=lambda label: _score_with_weights(log_odds_weights, label),
            contribution_summary=_top_weights(log_odds_weights),
        )
    )
    models.append(
        _evaluate_ranker(
            model_id="pairwise_ranked_preference_scorer",
            train_steps=train_steps,
            test_steps=test_steps,
            score_fn=lambda label: _score_with_weights(ranked_weights, label),
            contribution_summary=_top_weights(ranked_weights),
        )
    )
    models.append(
        _evaluate_ranker(
            model_id="pairwise_ranked_preference_with_coordinate_terms",
            train_steps=train_steps,
            test_steps=test_steps,
            score_fn=lambda label: _score_with_weights(
                ranked_coord_weights, label, include_coordinate_terms=True
            ),
            contribution_summary=_top_weights(ranked_coord_weights),
        )
    )
    for heuristic_id in [
        "king_support_improvement",
        "fence_cut_preservation",
        "edge_corner_net_pressure",
        "box_area_relevance",
        "safety_non_draw_rook_safe",
    ]:
        models.append(
            _evaluate_ranker(
                model_id=f"heuristic_{heuristic_id}",
                train_steps=train_steps,
                test_steps=test_steps,
                score_fn=lambda label, h=heuristic_id: _heuristic_score(h, label),
                contribution_summary={"heuristic_terms": heuristic_id},
            )
        )
    models.append(_oracle_result(test_steps, "oracle_dtm_positive_topk_ceiling"))
    models.append(_oracle_result(test_steps, "oracle_teacher_forced_trajectory_ceiling"))

    current = next(model for model in models if model["model_id"] == "current_learned_post_box_scorer")
    learned_test = current["test"]
    ranked = next(model for model in models if model["model_id"] == "pairwise_ranked_preference_scorer")
    ranked_test = ranked["test"]
    visible = next(model for model in models if model["model_id"] == "visible_term_log_odds_scorer")
    visible_test = visible["test"]

    ranked_improvement = (
        ranked_test["top1_dtm_positive_accuracy"] - learned_test["top1_dtm_positive_accuracy"]
    )
    visible_improvement = (
        visible_test["top1_dtm_positive_accuracy"] - learned_test["top1_dtm_positive_accuracy"]
    )
    if ranked_improvement >= 0.15 and ranked_test["hard_negative_above_positive_rate"] <= learned_test[
        "hard_negative_above_positive_rate"
    ]:
        candidate_status = "training_objective_benchmark_supports_ranked_sequence_policy"
        next_action = "design default-off ranked Plan Capsule sandbox, not promotion"
    elif visible_improvement >= 0.15 and visible_test["top1_dtm_positive_accuracy"] >= ranked_test[
        "top1_dtm_positive_accuracy"
    ]:
        candidate_status = "missing_feature_or_ontology_candidate"
        next_action = "propose non-causal visible term refinement, not runtime patch"
    elif ranked_test["top3_dtm_positive_accuracy"] >= 0.8 and ranked_test["top1_dtm_positive_accuracy"] < 0.5:
        candidate_status = "ranking_calibration_gap"
        next_action = "improve ranking objective / data, not topology"
    elif ranked_improvement <= 0.0 and visible_improvement <= 0.0:
        candidate_status = "model_expression_gap_not_solved_by_simple_ranking"
        next_action = "consider broader representation / curriculum-boundary / continuation-capacity diagnosis"
    else:
        candidate_status = "ranking_calibration_gap"
        next_action = "improve ranking objective / data, not topology"

    benchmark = {
        "schema_version": "stage7_training_objective_benchmark.v1",
        "causal_status": "non_causal_offline_benchmark",
        "runtime_behavior_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "stage7_status": "local_valid_composition_quarantined",
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "artifact_root": str(artifact_root),
        "dataset": {
            "trajectory_seed_source": str(artifact_root / DEFAULT_ARTIFACTS["expanded_trajectory_seed"]),
            "trajectory_count": expanded_seed.get("trajectory_count") or len(expanded_seed.get("trajectories") or []),
            "white_training_step_count": len(steps),
            "legal_move_label_count": sum(len(step["labels"]) for step in steps),
            "train_step_count": len(train_steps),
            "test_step_count": len(test_steps),
            "split_rule": "trajectory_index_mod_4_equals_0_is_test",
            "target_class_counts": dict(
                Counter(
                    str(label.get("target_class") or "")
                    for step in steps
                    for label in step["labels"]
                )
            ),
        },
        "models": models,
        "known_failed_move_analysis": _known_failed_move_analysis(models),
        "controls": _controls(artifact_root),
        "decision": {
            "candidate_status": candidate_status,
            "next_action": next_action,
            "ranked_top1_improvement_over_current": ranked_improvement,
            "visible_top1_improvement_over_current": visible_improvement,
            "thresholds": {
                "material_top1_improvement": 0.15,
                "top3_should_remain_high": 0.8,
                "hard_negative_rate_should_not_increase": True,
            },
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
    if benchmark.get("schema_version") != "stage7_training_objective_benchmark.v1":
        raise ValueError("unexpected benchmark schema")
    if benchmark.get("causal_status") != "non_causal_offline_benchmark":
        raise ValueError("benchmark must be non-causal")
    if benchmark.get("runtime_behavior_changed") is not False:
        raise ValueError("benchmark must not change runtime behavior")
    if benchmark.get("runtime_dtm_or_tablebase_lookup") is not False:
        raise ValueError("DTM/tablebase must not be runtime-causal")
    if benchmark.get("stage7_promotion_allowed") is not False or benchmark.get("stage8_training_allowed") is not False:
        raise ValueError("Stage 7 promotion and Stage 8 training must remain blocked")
    model_ids = {model.get("model_id") for model in benchmark.get("models") or []}
    required = {
        "current_learned_post_box_scorer",
        "visible_term_log_odds_scorer",
        "pairwise_ranked_preference_scorer",
        "heuristic_king_support_improvement",
        "heuristic_fence_cut_preservation",
        "heuristic_edge_corner_net_pressure",
        "heuristic_box_area_relevance",
        "heuristic_safety_non_draw_rook_safe",
        "oracle_dtm_positive_topk_ceiling",
    }
    missing = required - model_ids
    if missing:
        raise ValueError(f"benchmark missing models: {sorted(missing)}")


def render_markdown(benchmark: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Training-Objective Benchmark",
        "",
        "This benchmark is offline-only and non-causal. It does not implement a runtime repair, promote Stage 7, train Stage 8, or use DTM/tablebase at runtime.",
        "",
        "## Decision",
        "",
        f"- Candidate status: `{benchmark['decision']['candidate_status']}`",
        f"- Next action: {benchmark['decision']['next_action']}",
        f"- Ranked top-1 improvement over current: `{benchmark['decision']['ranked_top1_improvement_over_current']:.3f}`",
        f"- Visible top-1 improvement over current: `{benchmark['decision']['visible_top1_improvement_over_current']:.3f}`",
        "",
        "## Dataset",
        "",
        f"- Trajectories: `{benchmark['dataset']['trajectory_count']}`",
        f"- White training steps: `{benchmark['dataset']['white_training_step_count']}`",
        f"- Legal move labels: `{benchmark['dataset']['legal_move_label_count']}`",
        f"- Train/test: `{benchmark['dataset']['train_step_count']}` / `{benchmark['dataset']['test_step_count']}`",
        f"- Target classes: `{benchmark['dataset']['target_class_counts']}`",
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
    lines.extend(
        [
            "## Controls",
            "",
            f"- 0926 candidate-move summary: `{benchmark['controls']['candidate_move_0926']['summary']}`",
            f"- 2cc DTM/current-graph summary: `{benchmark['controls']['candidate_move_2cc']}`",
            "",
            "## Blocked Next Steps",
            "",
        ]
    )
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
