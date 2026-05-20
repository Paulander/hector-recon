#!/usr/bin/env python3
"""Review stronger non-causal selector/capacity-risk feature candidates."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TARGETS = Path("reports/krk_hard_negative_selector_target_dataset_v2.json")
SEMANTICS = Path("reports/krk_hard_negative_label_semantics_review_v1.json")
ABLATION = Path("reports/krk_hard_negative_selector_feature_ablation_v2.json")
OUT_JSON = Path("reports/krk_stronger_selector_feature_review_v0.json")
OUT_MD = Path("reports/krk_stronger_selector_feature_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _label_positive(row: dict[str, Any]) -> bool | None:
    if row.get("target_kind") == "positive_capacity_context":
        return True
    if row.get("target_kind") == "hard_negative_capacity":
        return False
    return None


def _provider_family(provider_id: str) -> str:
    if "stage0_basin" in provider_id:
        return "stage0_basin"
    if "drive_to_edge" in provider_id:
        return "drive_to_edge"
    if "fence_established" in provider_id:
        return "fence_established"
    if "edge_trap" in provider_id:
        return "edge_trap"
    return provider_id.rsplit(".", 1)[-1]


def _delta_bucket(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "missing"
    if value < 0:
        return "improves"
    if value > 0:
        return "worsens"
    return "same"


def _reply_bucket(value: Any) -> str:
    if not isinstance(value, int):
        return "missing"
    if value <= 3:
        return "low"
    if value <= 8:
        return "medium"
    return "high"


def _role_fit(row: dict[str, Any]) -> str:
    label = str(row.get("active_landmark_label") or "")
    family = str(row.get("provider_family") or _provider_family(str(row.get("provider_id") or "")))
    if label == "fence_established" and family in {"fence_established", "edge_trap", "stage0_basin"}:
        return "label_compatible"
    if label == "drive_to_edge" and family in {"drive_to_edge", "stage0_basin"}:
        return "label_compatible"
    if label == "wrong_tempo_control" and family in {"edge_trap", "stage0_basin"}:
        return "label_compatible"
    return "label_mismatch"


def _derived_row(row: dict[str, Any]) -> dict[str, Any]:
    provider_family = str(row.get("provider_family") or _provider_family(str(row.get("provider_id") or "")))
    piece = str(row.get("forced_piece_type") or "missing")
    king_delta = _delta_bucket(row.get("white_king_distance_delta"))
    rook_delta = _delta_bucket(row.get("rook_distance_delta"))
    rook_line = (
        "same_file"
        if row.get("rook_same_file_as_black_after")
        else "same_rank"
        if row.get("rook_same_rank_as_black_after")
        else "no_line"
    )
    return {
        **row,
        "provider_family": provider_family,
        "role_fit": _role_fit(row),
        "piece_motion": f"{piece}:king_{king_delta}:rook_{rook_delta}",
        "rook_line_after": rook_line,
        "reply_pressure": _reply_bucket(row.get("black_king_legal_reply_count_after")),
        "stage_role_fit": f"{row.get('source_stage')}:{_role_fit(row)}",
        "family_role_fit": f"{provider_family}:{_role_fit(row)}",
        "family_piece_motion": f"{provider_family}:{piece}:king_{king_delta}:rook_{rook_delta}",
        "family_rook_line": f"{provider_family}:{rook_line}",
        "family_reply_pressure": f"{provider_family}:{_reply_bucket(row.get('black_king_legal_reply_count_after'))}",
    }


def _feature_value(row: dict[str, Any], key: str) -> str:
    return str(row.get(key))


def _feature_key(row: dict[str, Any], keys: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_feature_value(row, key) for key in keys)


def _score_positive(train: list[dict[str, Any]], row: dict[str, Any], keys: tuple[str, ...]) -> float:
    labeled = [item for item in train if _label_positive(item) is not None]
    global_rate = sum(1 for item in labeled if _label_positive(item)) / len(labeled) if labeled else 0.5
    counts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    for item in labeled:
        counts[_feature_key(item, keys)]["positive" if _label_positive(item) else "negative"] += 1
    counter = counts.get(_feature_key(row, keys))
    if not counter:
        return global_rate
    total = counter["positive"] + counter["negative"]
    return counter["positive"] / total if total else global_rate


def _metrics(rows: list[dict[str, Any]], keys: tuple[str, ...], threshold: float) -> dict[str, Any]:
    predictions = []
    for state_id in sorted({str(row.get("state_id")) for row in rows}):
        train = [row for row in rows if str(row.get("state_id")) != state_id]
        test = [row for row in rows if str(row.get("state_id")) == state_id]
        for row in test:
            label = _label_positive(row)
            if label is None:
                continue
            score = _score_positive(train, row, keys)
            predictions.append(
                {
                    "state_id": row.get("state_id"),
                    "provider_id": row.get("provider_id"),
                    "target_kind": row.get("target_kind"),
                    "score": score,
                    "threshold": threshold,
                    "predicted_positive": score >= threshold,
                    "label_positive": label,
                    "feature_key": list(_feature_key(row, keys)),
                }
            )
    tp = sum(1 for item in predictions if item["predicted_positive"] and item["label_positive"])
    fp = sum(1 for item in predictions if item["predicted_positive"] and not item["label_positive"])
    tn = sum(1 for item in predictions if not item["predicted_positive"] and not item["label_positive"])
    fn = sum(1 for item in predictions if not item["predicted_positive"] and item["label_positive"])
    total = len(predictions)
    return {
        "row_count": total,
        "threshold": threshold,
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "accuracy": (tp + tn) / total if total else None,
        "positive_precision": tp / (tp + fp) if tp + fp else None,
        "positive_recall": tp / (tp + fn) if tp + fn else None,
        "negative_suppression": tn / (tn + fp) if tn + fp else None,
        "predictions": predictions,
    }


def _feature_stats(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        counts[str(row.get(key))]["positive" if _label_positive(row) else "negative"] += 1
    return {
        value: {
            "positive": counter["positive"],
            "negative": counter["negative"],
            "negative_rate": counter["negative"] / (counter["positive"] + counter["negative"]),
        }
        for value, counter in sorted(counts.items())
    }


def build_review() -> dict[str, Any]:
    targets = _load(TARGETS)
    semantics = _load(SEMANTICS)
    ablation = _load(ABLATION)
    if targets.get("causal_status") != "non_causal_target_dataset":
        raise ValueError("targets must remain non-causal")
    if semantics.get("causal_status") != "non_causal_semantics_review":
        raise ValueError("semantics review must remain non-causal")
    if ablation.get("causal_status") != "non_causal_feature_ablation":
        raise ValueError("ablation must remain non-causal")
    rows = [_derived_row(row) for row in targets.get("rows") or [] if _label_positive(row) is not None]
    specs = {
        "role_fit": ("role_fit",),
        "stage_role_fit": ("stage_role_fit",),
        "family_role_fit": ("family_role_fit",),
        "piece_motion": ("piece_motion",),
        "family_piece_motion": ("family_piece_motion",),
        "family_rook_line": ("family_rook_line",),
        "family_reply_pressure": ("family_reply_pressure",),
        "role_fit_motion": ("role_fit", "piece_motion"),
        "stage_family_role_motion": ("source_stage", "family_role_fit", "piece_motion"),
    }
    thresholds = (0.5, 0.6, 0.75)
    results = {
        f"{name}@{threshold}": {"features": list(keys), **_metrics(rows, keys, threshold)}
        for name, keys in specs.items()
        for threshold in thresholds
    }
    best_name, best = max(
        results.items(),
        key=lambda item: (
            item[1]["negative_suppression"] if item[1]["negative_suppression"] is not None else -1,
            item[1]["positive_recall"] if item[1]["positive_recall"] is not None else -1,
            item[1]["accuracy"] if item[1]["accuracy"] is not None else -1,
        ),
    )
    previous_best = ablation.get("best_result") or {}
    improved = (best.get("negative_suppression") or 0) > (previous_best.get("negative_suppression") or 0)
    robust = (best.get("negative_suppression") or 0) >= 0.5 and (best.get("positive_recall") or 0) >= 0.75
    status = "stronger_features_promising_but_not_runtime_ready" if improved else "stronger_features_no_clear_gain"
    if robust:
        status = "stronger_features_review_ready_runtime_still_blocked"
    payload = {
        "schema_version": "krk_stronger_selector_feature_review.v0",
        "causal_status": "non_causal_feature_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(TARGETS), str(SEMANTICS), str(ABLATION)],
        "summary": {
            "row_count": len(rows),
            "state_count": len({row.get("state_id") for row in rows}),
            "positive_context_count": sum(1 for row in rows if _label_positive(row)),
            "hard_negative_count": sum(1 for row in rows if _label_positive(row) is False),
            "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
            "previous_best_negative_suppression": previous_best.get("negative_suppression"),
            "previous_best_positive_recall": previous_best.get("positive_recall"),
            "best_negative_suppression": best.get("negative_suppression"),
            "best_positive_recall": best.get("positive_recall"),
            "improved_over_v2_ablation": improved,
        },
        "results": results,
        "best_result": {"objective": best_name, **{key: value for key, value in best.items() if key != "predictions"}},
        "feature_stats": {
            key: _feature_stats(rows, key)
            for key in (
                "role_fit",
                "family_role_fit",
                "piece_motion",
                "family_piece_motion",
                "family_rook_line",
                "family_reply_pressure",
            )
        },
        "interpretation": {
            "primary": "This probes richer offline capacity-risk features only; it does not authorize selector training.",
            "semantics_warning": "Because inputs are forced-provider capacity labels, the best feature is a capacity-risk diagnostic, not a runtime ownership selector.",
        },
        "decision": {
            "status": status,
            "recommended_next_step": (
                "architecture_review_before_selector_training_or_runtime"
                if robust
                else "refine_capacity_risk_features_or_collect_targeted_state_local_contrasts"
            ),
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_review(payload)
    return payload


def validate_review(payload: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_candidate_generator_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["summary"]["stage7_row_count"] != 0:
        raise ValueError("Stage 7 rows must remain excluded")
    if payload["decision"]["selector_training_allowed"] is not False:
        raise ValueError("selector training remains blocked")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Stronger Selector Feature Review v0",
        "",
        "Offline review of richer capacity-risk features. This does not implement or train a runtime selector.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Best Result", "", f"`{payload['best_result']}`", "", "## Results", ""])
    for name, result in payload["results"].items():
        lines.append(
            f"- `{name}` negative_suppression=`{result['negative_suppression']}` "
            f"positive_recall=`{result['positive_recall']}` accuracy=`{result['accuracy']}`"
        )
    lines.extend(["", "## Interpretation", ""])
    for key, value in payload["interpretation"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
