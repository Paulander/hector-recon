#!/usr/bin/env python3
"""Benchmark non-causal selector-objective feature models over seed v2.

This benchmark separates target semantics from runtime eligibility. It trains no
selector and makes no runtime decision. Offline labels define the benchmark
targets only; runtime-eligible feature models may use visible/provenance fields
from seed rows but not selected-owner outcome labels.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json")
SEED_PROBE = Path("reports/strategy_arbitration/krk_selector_objective_seed_probe_v2.json")
OWNERSHIP_CONTEXT = Path("reports/krk_ownership_selection_context_dataset_v3.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_selector_objective_benchmark_v2.json")
OUT_MD = Path("reports/strategy_arbitration/krk_selector_objective_benchmark_v2.md")


FEATURE_SETS: dict[str, tuple[str, ...]] = {
    "source_stage": ("source_stage",),
    "selected_provider_family": ("selected_provider_family",),
    "trace_source_profile": ("trace_source_profile",),
    "positive_trace_count_bucket": ("positive_trace_count_bucket",),
    "has_positive_trace_capacity": ("has_positive_trace_capacity",),
    "active_landmark_label": ("active_landmark_label",),
    "edge_bucket": ("edge_bucket",),
    "support_bucket": ("support_bucket",),
    "box_area_relevance": ("box_area_relevance",),
    "selected_piece": ("selected_piece",),
    "rook_distance_delta_bucket": ("rook_distance_delta_bucket",),
    "box_area_delta_bucket": ("box_area_delta_bucket",),
    "stage_provider_family": ("source_stage", "selected_provider_family"),
    "stage_active_landmark": ("source_stage", "active_landmark_label"),
    "stage_positive_bucket": ("source_stage", "positive_trace_count_bucket"),
    "support_positive_bucket": ("support_bucket", "positive_trace_count_bucket"),
    "active_landmark_support": ("active_landmark_label", "support_bucket"),
    "stage_support_positive_bucket": (
        "source_stage",
        "support_bucket",
        "positive_trace_count_bucket",
    ),
    "stage_provider_positive_bucket": (
        "source_stage",
        "selected_provider_family",
        "positive_trace_count_bucket",
    ),
    "stage_trace_positive_bucket": (
        "source_stage",
        "trace_source_profile",
        "positive_trace_count_bucket",
    ),
    "stage_support_rook_positive_bucket": (
        "source_stage",
        "support_bucket",
        "rook_distance_delta_bucket",
        "positive_trace_count_bucket",
    ),
    "stage_active_support_positive_bucket": (
        "source_stage",
        "active_landmark_label",
        "support_bucket",
        "positive_trace_count_bucket",
    ),
    "stage_box_relevance_positive_bucket": (
        "source_stage",
        "box_area_relevance",
        "positive_trace_count_bucket",
    ),
    "active_support_piece_positive_bucket": (
        "active_landmark_label",
        "support_bucket",
        "selected_piece",
        "positive_trace_count_bucket",
    ),
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


def _context_term_value(context: dict[str, Any], prefix: str) -> str:
    needle = f"{prefix}:"
    for term in context.get("context_terms") or []:
        if str(term).startswith(needle):
            return str(term).split(":", 1)[1]
    return ""


def _augment_row(row: dict[str, Any], context_by_state: dict[str, dict[str, Any]]) -> dict[str, Any]:
    context = context_by_state.get(str(row.get("state_id") or ""), {})
    move_context = context.get("selected_move_context") or {}
    augmented = dict(row)
    augmented["active_landmark_label"] = context.get("active_landmark_label", "")
    augmented["edge_bucket"] = _context_term_value(context, "edge_bucket")
    augmented["support_bucket"] = _context_term_value(context, "support_bucket")
    augmented["box_area_relevance"] = _context_term_value(context, "box_area_relevance")
    augmented["selected_piece"] = move_context.get("selected_piece") or _context_term_value(
        context, "selected_piece"
    )
    augmented["rook_distance_delta_bucket"] = move_context.get(
        "rook_distance_delta_bucket"
    ) or _context_term_value(context, "rook_distance_delta")
    augmented["box_area_delta_bucket"] = move_context.get(
        "box_area_delta_bucket"
    ) or _context_term_value(context, "box_area_delta")
    return augmented


def _target_action(row: dict[str, Any]) -> str:
    channel = row.get("objective_channel")
    if channel == "candidate_switch_contrast_seed":
        return "switch"
    if channel == "safe_preservation_contrast_seed":
        return "preserve"
    return "abstain"


def _trace_source_profile(row: dict[str, Any]) -> str:
    return "+".join(sorted(str(item) for item in row.get("trace_sources") or [])) or "none"


def _trace_count_bucket(row: dict[str, Any]) -> str:
    value = int(row.get("positive_trace_provider_candidate_count") or 0)
    if value <= 0:
        return "none"
    if value <= 3:
        return "low"
    if value <= 10:
        return "medium"
    return "high"


def _feature_value(row: dict[str, Any], key: str) -> str:
    if key == "trace_source_profile":
        return _trace_source_profile(row)
    if key == "positive_trace_count_bucket":
        return _trace_count_bucket(row)
    if key == "has_positive_trace_capacity":
        return str(int(row.get("positive_trace_provider_candidate_count") or 0) > 0)
    return str(row.get(key) or "")


def _feature_key(row: dict[str, Any], keys: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_feature_value(row, key) for key in keys)


def _majority_action(rows: list[dict[str, Any]]) -> str:
    counts = Counter(_target_action(row) for row in rows)
    if not counts:
        return "preserve"
    # Prefer preservation on ties; false switch is the riskiest error.
    return max(("preserve", "abstain", "switch"), key=lambda action: (counts[action], action == "preserve"))


def _predict(train: list[dict[str, Any]], row: dict[str, Any], keys: tuple[str, ...]) -> str:
    global_default = _majority_action(train)
    by_key: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for item in train:
        by_key[_feature_key(item, keys)].append(item)
    matches = by_key.get(_feature_key(row, keys))
    if not matches:
        return global_default
    return _majority_action(matches)


def _metrics(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(predictions)
    correct = sum(1 for item in predictions if item["predicted_action"] == item["target_action"])
    per_action: dict[str, dict[str, Any]] = {}
    for action in ("switch", "preserve", "abstain"):
        tp = sum(
            1
            for item in predictions
            if item["predicted_action"] == action and item["target_action"] == action
        )
        fp = sum(
            1
            for item in predictions
            if item["predicted_action"] == action and item["target_action"] != action
        )
        fn = sum(
            1
            for item in predictions
            if item["predicted_action"] != action and item["target_action"] == action
        )
        per_action[action] = {
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
        "switch_precision": per_action["switch"]["precision"],
        "switch_recall": per_action["switch"]["recall"],
        "preserve_precision": per_action["preserve"]["precision"],
        "preserve_recall": per_action["preserve"]["recall"],
        "abstain_precision": per_action["abstain"]["precision"],
        "abstain_recall": per_action["abstain"]["recall"],
        "per_action": per_action,
        "predictions": predictions,
    }


def _feature_model(rows: list[dict[str, Any]], model_id: str, keys: tuple[str, ...]) -> dict[str, Any]:
    predictions = []
    for state_id in sorted({str(row.get("state_id")) for row in rows}):
        train = [row for row in rows if str(row.get("state_id")) != state_id]
        test = [row for row in rows if str(row.get("state_id")) == state_id]
        for row in test:
            predictions.append(
                {
                    "state_id": row.get("state_id"),
                    "source_stage": row.get("source_stage"),
                    "selected_provider": row.get("selected_provider"),
                    "objective_channel": row.get("objective_channel"),
                    "feature_key": list(_feature_key(row, keys)),
                    "target_action": _target_action(row),
                    "predicted_action": _predict(train, row, keys),
                    "runtime_feature_eligible": True,
                }
            )
    return {
        "model_id": model_id,
        "model_kind": "leave_state_out_majority_feature_model",
        "features": list(keys),
        "runtime_feature_eligible": True,
        **_metrics(predictions),
    }


def _visible_failure_risk_heuristic(row: dict[str, Any]) -> str:
    """Visible rule probe for switch/preserve/abstain semantics.

    This is a non-causal benchmark candidate. It intentionally uses only
    visible context/provenance/candidate-count terms, never owner outcome labels.
    """
    positive_count = int(row.get("positive_trace_provider_candidate_count") or 0)
    if positive_count <= 0:
        return "abstain"

    stage = str(row.get("source_stage") or "")
    active = str(row.get("active_landmark_label") or "")
    support = str(row.get("support_bucket") or "")
    edge = str(row.get("edge_bucket") or "")
    box_relevance = str(row.get("box_area_relevance") or "")
    selected_piece = str(row.get("selected_piece") or "")
    positive_bucket = _trace_count_bucket(row)

    if positive_bucket == "high":
        return "preserve"
    if edge == "near_edge" or box_relevance == "medium":
        return "switch"
    if stage == "stage6" and support == "far":
        return "switch"
    if active == "wrong_tempo_control" and selected_piece == "king":
        return "switch"
    if active == "fence_established" and selected_piece == "king" and support == "close":
        return "switch"
    return "preserve"


def _conservative_visible_failure_risk_heuristic(row: dict[str, Any]) -> str:
    positive_count = int(row.get("positive_trace_provider_candidate_count") or 0)
    if positive_count <= 0:
        return "abstain"

    support = str(row.get("support_bucket") or "")
    edge = str(row.get("edge_bucket") or "")
    box_relevance = str(row.get("box_area_relevance") or "")
    positive_bucket = _trace_count_bucket(row)
    stage = str(row.get("source_stage") or "")

    if positive_bucket == "high":
        return "preserve"
    if edge == "near_edge" or box_relevance == "medium":
        return "switch"
    if stage == "stage6" and support == "far":
        return "switch"
    return "preserve"


def _heuristic_model(
    rows: list[dict[str, Any]],
    model_id: str,
    heuristic,
) -> dict[str, Any]:
    predictions = [
        {
            "state_id": row.get("state_id"),
            "source_stage": row.get("source_stage"),
            "selected_provider": row.get("selected_provider"),
            "objective_channel": row.get("objective_channel"),
            "target_action": _target_action(row),
            "predicted_action": heuristic(row),
            "runtime_feature_eligible": True,
            "feature_key": [
                str(row.get("source_stage") or ""),
                str(row.get("active_landmark_label") or ""),
                str(row.get("edge_bucket") or ""),
                str(row.get("box_area_relevance") or ""),
                str(row.get("support_bucket") or ""),
                str(row.get("selected_piece") or ""),
                _trace_count_bucket(row),
            ],
        }
        for row in rows
    ]
    return {
        "model_id": model_id,
        "model_kind": "fixed_visible_heuristic_probe",
        "runtime_feature_eligible": True,
        "notes": (
            "Non-causal visible-term probe only. Passing thresholds here justifies "
            "independent validation or a review packet, not runtime selector use."
        ),
        **_metrics(predictions),
    }


def _offline_oracle(rows: list[dict[str, Any]]) -> dict[str, Any]:
    predictions = [
        {
            "state_id": row.get("state_id"),
            "source_stage": row.get("source_stage"),
            "selected_provider": row.get("selected_provider"),
            "objective_channel": row.get("objective_channel"),
            "target_action": _target_action(row),
            "predicted_action": _target_action(row),
            "runtime_feature_eligible": False,
        }
        for row in rows
    ]
    return {
        "model_id": "offline_target_label_oracle",
        "model_kind": "offline_semantic_oracle",
        "runtime_feature_eligible": False,
        "notes": "Uses objective labels; ceiling only.",
        **_metrics(predictions),
    }


def _passes_review_thresholds(result: dict[str, Any]) -> bool:
    return (
        result.get("runtime_feature_eligible") is True
        and (result.get("switch_recall") or 0.0) >= 0.70
        and (result.get("switch_precision") or 0.0) >= 0.70
        and (result.get("preserve_recall") or 0.0) >= 0.80
        and (result.get("abstain_recall") or 0.0) >= 0.60
    )


def build_payload(
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
    results: dict[str, dict[str, Any]] = {}
    for name, keys in FEATURE_SETS.items():
        results[name] = _feature_model(rows, name, keys)
    results["visible_failure_risk_heuristic_v2"] = _heuristic_model(
        rows, "visible_failure_risk_heuristic_v2", _visible_failure_risk_heuristic
    )
    results["conservative_visible_failure_risk_heuristic_v2"] = _heuristic_model(
        rows,
        "conservative_visible_failure_risk_heuristic_v2",
        _conservative_visible_failure_risk_heuristic,
    )
    results["offline_target_label_oracle"] = _offline_oracle(rows)
    runtime_results = [
        result for result in results.values() if result.get("runtime_feature_eligible")
    ]
    passing_results = [result for result in runtime_results if _passes_review_thresholds(result)]
    best_runtime = max(
        runtime_results,
        key=lambda item: (
            item.get("switch_recall") or 0.0,
            item.get("preserve_recall") or 0.0,
            item.get("abstain_recall") or 0.0,
            item.get("switch_precision") or 0.0,
            item.get("accuracy") or 0.0,
        ),
        default={},
    )
    target_counts = Counter(_target_action(row) for row in rows)
    ready_for_review = bool(passing_results)
    return {
        "schema_version": "krk_selector_objective_benchmark.v2",
        "causal_status": "non_causal_selector_objective_benchmark",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MANIFEST), str(SEED_PROBE), str(OWNERSHIP_CONTEXT)],
        "summary": {
            "seed_row_count": len(rows),
            "target_action_counts": dict(sorted(target_counts.items())),
            "runtime_feature_model_count": len(runtime_results),
            "runtime_threshold_passing_model_count": len(passing_results),
            "context_row_count": len(context_by_state),
            "best_runtime_model": best_runtime.get("model_id"),
            "best_runtime_accuracy": best_runtime.get("accuracy"),
            "best_runtime_switch_precision": best_runtime.get("switch_precision"),
            "best_runtime_switch_recall": best_runtime.get("switch_recall"),
            "best_runtime_preserve_recall": best_runtime.get("preserve_recall"),
            "best_runtime_abstain_recall": best_runtime.get("abstain_recall"),
            "offline_oracle_accuracy": results["offline_target_label_oracle"].get("accuracy"),
            "selector_training_row_count": (manifest.get("summary") or {}).get(
                "selector_training_row_count"
            ),
            "stage7_training_row_count": (manifest.get("summary") or {}).get(
                "stage7_training_row_count"
            ),
            "seed_probe_status": (seed_probe.get("decision") or {}).get("status"),
        },
        "results": results,
        "interpretation": {
            "runtime_feature_benchmark_ready_for_review": ready_for_review,
            "selector_training_supported": False,
            "runtime_selector_supported": False,
            "independent_validation_required_before_runtime": ready_for_review,
            "offline_semantics_confirmed": results["offline_target_label_oracle"].get("accuracy")
            == 1.0,
            "reason": (
                "Seed v2 supports a non-causal benchmark with switch/preserve/abstain labels. "
                "Passing runtime-feature models would justify a later review packet only; this "
                "artifact does not train or implement a selector. Heuristic probes are not enough "
                "for runtime use without independent protected validation."
            ),
        },
        "decision": {
            "status": (
                "selector_objective_benchmark_v2_runtime_feature_review_ready"
                if ready_for_review
                else "selector_objective_benchmark_v2_no_runtime_ready_features"
            ),
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "write_selector_objective_benchmark_review_packet"
                if ready_for_review
                else "collect_more_runtime_visible_selector_features_or_keep_selector_blocked"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Selector Objective Benchmark v2",
        "",
        "This benchmark evaluates runtime-visible feature models over the v2 selector-objective seed set. It does not train or authorize a selector.",
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
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Runtime Feature Models", ""])
    for model_id, result in sorted(payload["results"].items()):
        if not result.get("runtime_feature_eligible"):
            continue
        lines.append(
            "- "
            f"`{model_id}` "
            f"accuracy={result.get('accuracy')} "
            f"switch_precision={result.get('switch_precision')} "
            f"switch_recall={result.get('switch_recall')} "
            f"preserve_recall={result.get('preserve_recall')} "
            f"abstain_recall={result.get('abstain_recall')}"
        )
    lines.extend(["", "## Interpretation", ""])
    for key, value in payload["interpretation"].items():
        lines.append(f"- {key}: `{value}`")
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
