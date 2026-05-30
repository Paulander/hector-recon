#!/usr/bin/env python3
"""Run the non-causal selector-objective benchmark v0.

This benchmark compares simple rules over seed manifest v2. It never trains or
authorizes a runtime selector; offline owner labels define benchmark targets
only.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json")
SEED_PROBE = Path("reports/strategy_arbitration/krk_selector_objective_seed_probe_v2.json")
OWNERSHIP_CONTEXT = Path("reports/krk_ownership_selection_context_dataset_v3.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_selector_objective_benchmark_v0.json")
OUT_MD = Path("reports/strategy_arbitration/krk_selector_objective_benchmark_v0.md")
DECISION_JSON = Path(
    "reports/strategy_arbitration/krk_selector_objective_benchmark_decision_v0.json"
)
DECISION_MD = Path(
    "reports/strategy_arbitration/krk_selector_objective_benchmark_decision_v0.md"
)

CLASSES = (
    "preserve_selected_owner",
    "prefer_visible_alternative",
    "abstain_context_only",
)

COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_provider_suppression": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "hidden_python_controller": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _context_index(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("state_id") or ""): row
        for row in payload.get("rows") or []
        if isinstance(row, dict) and row.get("state_id")
    }


def _context_term(context: dict[str, Any], prefix: str) -> str:
    needle = f"{prefix}:"
    for term in context.get("context_terms") or []:
        if str(term).startswith(needle):
            return str(term).split(":", 1)[1]
    return ""


def _provider_family(row: dict[str, Any]) -> str:
    return str(row.get("selected_provider_family") or row.get("selected_provider") or "").replace(
        "krk.", ""
    )


def _positive_bucket(row: dict[str, Any]) -> str:
    count = int(row.get("positive_trace_provider_candidate_count") or 0)
    if count <= 0:
        return "none"
    if count <= 3:
        return "low"
    if count <= 10:
        return "medium"
    return "high"


def _target_action(row: dict[str, Any]) -> str:
    channel = row.get("objective_channel")
    if channel == "candidate_switch_contrast_seed":
        return "prefer_visible_alternative"
    if channel == "safe_preservation_contrast_seed":
        return "preserve_selected_owner"
    if channel == "progress_window_failure_contrast_candidate":
        if row.get("selected_owner_label") == "selected_owner_failed":
            return "prefer_visible_alternative"
        return "preserve_selected_owner"
    return "abstain_context_only"


def _augment_row(row: dict[str, Any], context_by_state: dict[str, dict[str, Any]]) -> dict[str, Any]:
    context = context_by_state.get(str(row.get("state_id") or ""), {})
    move_context = context.get("selected_move_context") or {}
    out = dict(row)
    out["target_action"] = _target_action(row)
    out["selected_provider_family"] = _provider_family(row)
    out["active_landmark_label"] = context.get("active_landmark_label") or row.get(
        "active_landmark_label"
    )
    out["edge_bucket"] = _context_term(context, "edge_bucket")
    out["support_bucket"] = _context_term(context, "support_bucket")
    out["box_area_relevance"] = _context_term(context, "box_area_relevance")
    out["selected_piece"] = move_context.get("selected_piece") or _context_term(
        context, "selected_piece"
    )
    out["positive_trace_count_bucket"] = _positive_bucket(out)
    return out


def _majority(rows: list[dict[str, Any]]) -> str:
    counts = Counter(row["target_action"] for row in rows)
    if not counts:
        return "preserve_selected_owner"
    return max(
        CLASSES,
        key=lambda action: (
            counts[action],
            action == "preserve_selected_owner",
            action == "abstain_context_only",
        ),
    )


def _feature_key(row: dict[str, Any], keys: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(row.get(key) or "") for key in keys)


def _predict_prior(train: list[dict[str, Any]], row: dict[str, Any], keys: tuple[str, ...]) -> str:
    fallback = _majority(train)
    by_key: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for item in train:
        by_key[_feature_key(item, keys)].append(item)
    matches = by_key.get(_feature_key(row, keys))
    if not matches:
        return fallback
    return _majority(matches)


def _leave_state_out_predictions(
    rows: list[dict[str, Any]],
    predictor: Callable[[list[dict[str, Any]], dict[str, Any]], str],
) -> list[dict[str, Any]]:
    predictions = []
    for state_id in sorted({str(row.get("state_id")) for row in rows}):
        train = [row for row in rows if str(row.get("state_id")) != state_id]
        test = [row for row in rows if str(row.get("state_id")) == state_id]
        for row in test:
            predictions.append(_prediction_row(row, predictor(train, row), "leave_state_out"))
    return predictions


def _leave_stage_out_predictions(
    rows: list[dict[str, Any]],
    predictor: Callable[[list[dict[str, Any]], dict[str, Any]], str],
) -> list[dict[str, Any]]:
    predictions = []
    for stage in sorted({str(row.get("source_stage")) for row in rows}):
        train = [row for row in rows if str(row.get("source_stage")) != stage]
        test = [row for row in rows if str(row.get("source_stage")) == stage]
        if not train:
            continue
        for row in test:
            predictions.append(_prediction_row(row, predictor(train, row), "leave_stage_out"))
    return predictions


def _prediction_row(row: dict[str, Any], predicted: str, split: str) -> dict[str, Any]:
    return {
        "state_id": row.get("state_id"),
        "source_stage": row.get("source_stage"),
        "selected_provider": row.get("selected_provider"),
        "selected_provider_family": row.get("selected_provider_family"),
        "objective_channel": row.get("objective_channel"),
        "target_action": row["target_action"],
        "predicted_action": predicted,
        "correct": predicted == row["target_action"],
        "split": split,
    }


def _direct_rule_predictions(
    rows: list[dict[str, Any]],
    rule: Callable[[dict[str, Any]], str],
) -> list[dict[str, Any]]:
    return [_prediction_row(row, rule(row), "direct_rule_evaluation") for row in rows]


def _trace_context_rule(row: dict[str, Any]) -> str:
    if int(row.get("positive_trace_provider_candidate_count") or 0) <= 0:
        return "abstain_context_only"
    if row.get("edge_bucket") == "near_edge" or row.get("box_area_relevance") == "medium":
        return "prefer_visible_alternative"
    if row.get("source_stage") == "stage6" and row.get("support_bucket") == "far":
        return "prefer_visible_alternative"
    return "preserve_selected_owner"


def _proposal_count_rule(row: dict[str, Any]) -> str:
    bucket = row.get("positive_trace_count_bucket")
    if bucket == "none":
        return "abstain_context_only"
    if bucket == "low":
        return "prefer_visible_alternative"
    return "preserve_selected_owner"


def _combined_rule(row: dict[str, Any]) -> str:
    if int(row.get("positive_trace_provider_candidate_count") or 0) <= 0:
        return "abstain_context_only"
    if row.get("positive_trace_count_bucket") == "high":
        return "preserve_selected_owner"
    if row.get("edge_bucket") == "near_edge" or row.get("box_area_relevance") == "medium":
        return "prefer_visible_alternative"
    if row.get("source_stage") == "stage6" and row.get("support_bucket") == "far":
        return "prefer_visible_alternative"
    if (
        row.get("active_landmark_label") == "wrong_tempo_control"
        and row.get("selected_piece") == "king"
    ):
        return "prefer_visible_alternative"
    if (
        row.get("active_landmark_label") == "fence_established"
        and row.get("selected_piece") == "king"
        and row.get("support_bucket") == "close"
    ):
        return "prefer_visible_alternative"
    return "preserve_selected_owner"


def _metrics(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(predictions)
    correct = sum(1 for row in predictions if row["correct"])
    confusion = {
        actual: {predicted: 0 for predicted in CLASSES}
        for actual in CLASSES
    }
    per_class: dict[str, dict[str, Any]] = {}
    for row in predictions:
        confusion[row["target_action"]][row["predicted_action"]] += 1
    for action in CLASSES:
        tp = confusion[action][action]
        fp = sum(confusion[actual][action] for actual in CLASSES if actual != action)
        fn = sum(confusion[action][predicted] for predicted in CLASSES if predicted != action)
        per_class[action] = {
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else 0.0,
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
        }
    return {
        "row_count": total,
        "correct_count": correct,
        "accuracy": correct / total if total else 0.0,
        "per_class": per_class,
        "confusion_matrix": confusion,
        "safe_preservation_recall": per_class["preserve_selected_owner"]["recall"],
        "switch_contrast_recall": per_class["prefer_visible_alternative"]["recall"],
        "abstain_recall": per_class["abstain_context_only"]["recall"],
        "predictions": predictions,
    }


def _model_result(
    *,
    model_id: str,
    model_kind: str,
    evaluation_method: str,
    predictions: list[dict[str, Any]],
    runtime_feature_eligible: bool,
    prediction_uses_offline_only_labels: bool,
    training_targets_use_offline_labels: bool,
) -> dict[str, Any]:
    return {
        "model_id": model_id,
        "model_kind": model_kind,
        "evaluation_method": evaluation_method,
        "runtime_feature_eligible": runtime_feature_eligible,
        "prediction_uses_offline_only_labels": prediction_uses_offline_only_labels,
        "training_targets_use_offline_labels": training_targets_use_offline_labels,
        **_metrics(predictions),
    }


def _build_models(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    majority_predictor = lambda train, _row: _majority(train)
    provider_predictor = lambda train, row: _predict_prior(train, row, ("selected_provider_family",))
    stage_provider_predictor = lambda train, row: _predict_prior(
        train, row, ("source_stage", "selected_provider_family")
    )
    return {
        "majority_baseline": _model_result(
            model_id="majority_baseline",
            model_kind="leave_state_out_majority_baseline",
            evaluation_method="leave_state_out",
            predictions=_leave_state_out_predictions(rows, majority_predictor),
            runtime_feature_eligible=False,
            prediction_uses_offline_only_labels=False,
            training_targets_use_offline_labels=True,
        ),
        "provider_prior": _model_result(
            model_id="provider_prior",
            model_kind="leave_state_out_provider_family_prior",
            evaluation_method="leave_state_out",
            predictions=_leave_state_out_predictions(rows, provider_predictor),
            runtime_feature_eligible=True,
            prediction_uses_offline_only_labels=False,
            training_targets_use_offline_labels=True,
        ),
        "stage_provider_family_prior": _model_result(
            model_id="stage_provider_family_prior",
            model_kind="leave_state_out_stage_provider_family_prior",
            evaluation_method="leave_state_out",
            predictions=_leave_state_out_predictions(rows, stage_provider_predictor),
            runtime_feature_eligible=True,
            prediction_uses_offline_only_labels=False,
            training_targets_use_offline_labels=True,
        ),
        "trace_context_feature_rule": _model_result(
            model_id="trace_context_feature_rule",
            model_kind="fixed_visible_context_rule",
            evaluation_method="direct_rule_evaluation",
            predictions=_direct_rule_predictions(rows, _trace_context_rule),
            runtime_feature_eligible=True,
            prediction_uses_offline_only_labels=False,
            training_targets_use_offline_labels=False,
        ),
        "proposal_count_positive_alternative_rule": _model_result(
            model_id="proposal_count_positive_alternative_rule",
            model_kind="fixed_positive_alternative_count_rule",
            evaluation_method="direct_rule_evaluation",
            predictions=_direct_rule_predictions(rows, _proposal_count_rule),
            runtime_feature_eligible=True,
            prediction_uses_offline_only_labels=False,
            training_targets_use_offline_labels=False,
        ),
        "combined_simple_rule": _model_result(
            model_id="combined_simple_rule",
            model_kind="fixed_combined_visible_rule",
            evaluation_method="direct_rule_evaluation",
            predictions=_direct_rule_predictions(rows, _combined_rule),
            runtime_feature_eligible=True,
            prediction_uses_offline_only_labels=False,
            training_targets_use_offline_labels=False,
        ),
        "majority_baseline_leave_stage_out": _model_result(
            model_id="majority_baseline_leave_stage_out",
            model_kind="leave_stage_out_majority_baseline",
            evaluation_method="leave_stage_out",
            predictions=_leave_stage_out_predictions(rows, majority_predictor),
            runtime_feature_eligible=False,
            prediction_uses_offline_only_labels=False,
            training_targets_use_offline_labels=True,
        ),
        "stage_provider_family_prior_leave_stage_out": _model_result(
            model_id="stage_provider_family_prior_leave_stage_out",
            model_kind="leave_stage_out_stage_provider_family_prior",
            evaluation_method="leave_stage_out",
            predictions=_leave_stage_out_predictions(rows, stage_provider_predictor),
            runtime_feature_eligible=True,
            prediction_uses_offline_only_labels=False,
            training_targets_use_offline_labels=True,
        ),
    }


def _promising(result: dict[str, Any]) -> bool:
    return (
        result.get("runtime_feature_eligible") is True
        and result.get("prediction_uses_offline_only_labels") is False
        and (result.get("safe_preservation_recall") or 0.0) >= 0.80
        and (result.get("switch_contrast_recall") or 0.0) >= 0.70
        and (result.get("abstain_recall") or 0.0) >= 0.60
        and (result.get("accuracy") or 0.0) >= 0.75
    )


def build_payload(
    *,
    manifest: dict[str, Any] | None = None,
    seed_probe: dict[str, Any] | None = None,
    ownership_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = manifest or _load(MANIFEST)
    seed_probe = seed_probe or _load(SEED_PROBE)
    ownership_context = ownership_context or _load(OWNERSHIP_CONTEXT)
    context_by_state = _context_index(ownership_context)
    rows = [
        _augment_row(row, context_by_state)
        for row in manifest.get("seed_rows") or []
        if isinstance(row, dict) and not row.get("stage7_training_row")
    ]
    models = _build_models(rows)
    runtime_models = [
        result
        for result in models.values()
        if result.get("runtime_feature_eligible")
        and result.get("evaluation_method") in {"leave_state_out", "direct_rule_evaluation"}
    ]
    promising_models = [result for result in runtime_models if _promising(result)]
    best_model = max(
        runtime_models,
        key=lambda result: (
            result.get("switch_contrast_recall") or 0.0,
            result.get("safe_preservation_recall") or 0.0,
            result.get("abstain_recall") or 0.0,
            result.get("accuracy") or 0.0,
        ),
        default={},
    )
    target_counts = Counter(row["target_action"] for row in rows)
    underpowered = (
        len(rows) < 16
        or target_counts["preserve_selected_owner"] < 4
        or target_counts["prefer_visible_alternative"] < 4
        or target_counts["abstain_context_only"] < 4
    )
    return {
        "schema_version": "krk_selector_objective_benchmark.v0",
        "causal_status": "non_causal_selector_objective_benchmark",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            str(MANIFEST),
            str(SEED_PROBE),
            str(OWNERSHIP_CONTEXT),
            "reports/strategy_arbitration/krk_joined_trace_ownership_collection_v0.json",
            "reports/strategy_arbitration/krk_stage4_joined_trace_ownership_collection_v0.json",
            "reports/strategy_arbitration/krk_selector_objective_fresh_diversity_collection_v0.json",
        ],
        "classes": list(CLASSES),
        "summary": {
            "seed_row_count": len(rows),
            "target_action_counts": dict(sorted(target_counts.items())),
            "benchmark_underpowered": underpowered,
            "model_count": len(models),
            "runtime_feature_eligible_model_count": sum(
                1 for result in models.values() if result.get("runtime_feature_eligible")
            ),
            "promising_runtime_feature_model_count": len(promising_models),
            "best_model": best_model.get("model_id"),
            "best_accuracy": best_model.get("accuracy"),
            "best_safe_preservation_recall": best_model.get("safe_preservation_recall"),
            "best_switch_contrast_recall": best_model.get("switch_contrast_recall"),
            "best_abstain_recall": best_model.get("abstain_recall"),
            "offline_label_prediction_model_count": sum(
                1 for result in models.values() if result.get("prediction_uses_offline_only_labels")
            ),
            "runtime_feature_eligible_prediction_count": sum(
                len(result.get("predictions") or [])
                for result in models.values()
                if result.get("runtime_feature_eligible")
            ),
            "selector_training_row_count": (manifest.get("summary") or {}).get(
                "selector_training_row_count"
            ),
            "stage7_training_row_count": (manifest.get("summary") or {}).get(
                "stage7_training_row_count"
            ),
            "runtime_authorization_row_count": (manifest.get("summary") or {}).get(
                "runtime_authorization_row_count", 0
            ),
            "seed_probe_status": (seed_probe.get("decision") or {}).get("status"),
        },
        "models": models,
        "interpretation": {
            "selector_training_supported": False,
            "runtime_selector_supported": False,
            "runtime_review_packet_is_strongest_allowed_next_step": bool(promising_models),
            "capacity_labels_are_not_ownership_labels": True,
            "reason": (
                "The benchmark uses offline owner labels only as non-causal targets. "
                "No model authorizes runtime selector behavior or provider/routing/score changes."
            ),
        },
        "decision": {
            "status": (
                "selector_objective_benchmark_underpowered_after_all"
                if underpowered
                else "selector_objective_benchmark_promising_non_causal"
                if promising_models
                else "selector_objective_benchmark_needs_features"
            ),
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "write_runtime_review_packet_not_implementation"
                if promising_models and not underpowered
                else "recover_more_runtime_visible_features_or_keep_selector_blocked"
            ),
        },
    }


def build_decision(benchmark: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "krk_selector_objective_benchmark_decision.v0",
        "causal_status": "non_causal_benchmark_decision",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_selector_objective_benchmark_v0.json"
        ],
        "summary": {
            "benchmark_status": benchmark["decision"]["status"],
            "seed_row_count": benchmark["summary"]["seed_row_count"],
            "target_action_counts": benchmark["summary"]["target_action_counts"],
            "best_model": benchmark["summary"]["best_model"],
            "best_accuracy": benchmark["summary"]["best_accuracy"],
            "best_safe_preservation_recall": benchmark["summary"][
                "best_safe_preservation_recall"
            ],
            "best_switch_contrast_recall": benchmark["summary"]["best_switch_contrast_recall"],
            "best_abstain_recall": benchmark["summary"]["best_abstain_recall"],
            "promising_runtime_feature_model_count": benchmark["summary"][
                "promising_runtime_feature_model_count"
            ],
            "selector_training_row_count": benchmark["summary"]["selector_training_row_count"],
            "stage7_training_row_count": benchmark["summary"]["stage7_training_row_count"],
            "runtime_authorization_row_count": benchmark["summary"][
                "runtime_authorization_row_count"
            ],
        },
        "decision": {
            "status": benchmark["decision"]["status"],
            "runtime_review_packet_allowed_next": (
                benchmark["decision"]["status"]
                == "selector_objective_benchmark_promising_non_causal"
            ),
            "implementation_authorized_by_this_packet": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": benchmark["decision"]["recommended_next_step"],
        },
    }


def _write_markdown(path: Path, title: str, payload: dict[str, Any]) -> None:
    lines = [
        f"# {title}",
        "",
        "This artifact is non-causal. It does not train or authorize a runtime selector.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- runtime_changes_allowed: `{payload['decision']['runtime_changes_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    if "models" in payload:
        lines.extend(["", "## Models", ""])
        for model_id, result in payload["models"].items():
            lines.append(
                "- "
                f"`{model_id}` "
                f"accuracy={result.get('accuracy')} "
                f"safe_recall={result.get('safe_preservation_recall')} "
                f"switch_recall={result.get('switch_contrast_recall')} "
                f"abstain_recall={result.get('abstain_recall')} "
                f"runtime_feature_eligible={result.get('runtime_feature_eligible')}"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    benchmark = build_payload()
    decision = build_decision(benchmark)
    (ROOT / OUT_JSON).write_text(
        json.dumps(benchmark, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_markdown(ROOT / OUT_MD, "KRK Selector Objective Benchmark v0", benchmark)
    (ROOT / DECISION_JSON).write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_markdown(
        ROOT / DECISION_MD,
        "KRK Selector Objective Benchmark Decision v0",
        decision,
    )
    print(json.dumps(decision["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
