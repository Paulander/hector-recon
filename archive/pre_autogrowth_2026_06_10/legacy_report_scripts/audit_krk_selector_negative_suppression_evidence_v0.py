#!/usr/bin/env python3
"""Audit evidence for KRK selector negative suppression and label balance."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRAST = Path("reports/krk_state_local_contrast_labels_v2.json")
PROBE = Path("reports/krk_state_local_contrast_selector_probe_v2.json")
CAPACITY_FRAMES = Path("reports/krk_protected_provider_coverage_frames_v0.json")
TWO_STAGE = Path("reports/krk_two_stage_candidate_selection_benchmark_v0.json")
OUT_JSON = Path("reports/krk_selector_negative_suppression_evidence_v0.json")
OUT_MD = Path("reports/krk_selector_negative_suppression_evidence_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _bucket_rank(rank: Any) -> str:
    if not isinstance(rank, (int, float)):
        return "missing"
    if rank <= 1:
        return "rank_1"
    if rank <= 3:
        return "rank_2_3"
    return "rank_4_plus"


def _bucket_score(score: Any) -> str:
    if not isinstance(score, (int, float)):
        return "missing"
    if score >= 0.75:
        return "score_high"
    if score >= 0.25:
        return "score_mid"
    return "score_low"


def _feature_value(row: dict[str, Any], key: str) -> str:
    if key == "provider_local_rank_bucket":
        return _bucket_rank(row.get("provider_local_rank"))
    if key == "global_raw_score_rank_bucket":
        return _bucket_rank(row.get("global_raw_score_rank"))
    if key == "normalized_score_bucket":
        return _bucket_score(row.get("normalized_score"))
    return str(row.get(key))


def _feature_key(row: dict[str, Any], keys: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_feature_value(row, key) for key in keys)


def _label_positive(row: dict[str, Any]) -> bool | None:
    label = row.get("contrast_label")
    if label == "positive":
        return True
    if label == "negative":
        return False
    return None


def _score(train: list[dict[str, Any]], row: dict[str, Any], keys: tuple[str, ...]) -> float:
    labeled = [item for item in train if _label_positive(item) is not None]
    positive_count = sum(1 for item in labeled if _label_positive(item))
    global_rate = positive_count / len(labeled) if labeled else 0.5
    counts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    for item in labeled:
        label = _label_positive(item)
        if label is None:
            continue
        counts[_feature_key(item, keys)]["positive" if label else "negative"] += 1
    counter = counts.get(_feature_key(row, keys))
    if not counter:
        return global_rate
    total = counter["positive"] + counter["negative"]
    return counter["positive"] / total if total else global_rate


def _leave_state_out_predictions(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    labeled = [row for row in rows if _label_positive(row) is not None]
    predictions = []
    for state_id in sorted({str(row.get("state_id")) for row in labeled}):
        train = [row for row in labeled if str(row.get("state_id")) != state_id]
        test = [row for row in labeled if str(row.get("state_id")) == state_id]
        for row in test:
            label = _label_positive(row)
            assert label is not None
            score = _score(train, row, keys)
            predictions.append({
                "state_id": row.get("state_id"),
                "source_stage": row.get("source_stage"),
                "provider_id": row.get("provider_id"),
                "provider_family": row.get("provider_family"),
                "provider_maturity": row.get("provider_maturity"),
                "global_raw_score_rank": row.get("global_raw_score_rank"),
                "provider_local_rank": row.get("provider_local_rank"),
                "normalized_score": row.get("normalized_score"),
                "forced_result": row.get("forced_result"),
                "forced_plies": row.get("forced_plies"),
                "score": score,
                "predicted_positive": score >= 0.5,
                "label_positive": label,
                "feature_key": list(_feature_key(row, keys)),
            })
    return predictions


def build_audit() -> dict[str, Any]:
    contrast = _load(CONTRAST)
    probe = _load(PROBE)
    capacity = _load(CAPACITY_FRAMES)
    two_stage = _load(TWO_STAGE)
    if contrast.get("causal_status") != "non_causal_state_local_contrast_dataset":
        raise ValueError("contrast dataset must remain non-causal")
    if probe.get("causal_status") != "non_causal_offline_probe":
        raise ValueError("selector probe must remain non-causal")
    if capacity.get("causal_status") != "non_causal_capacity_frame_dataset":
        raise ValueError("capacity frames must remain non-causal")
    if two_stage.get("causal_status") != "non_causal_benchmark":
        raise ValueError("two-stage benchmark must remain non-causal")

    rows = list(contrast.get("rows") or [])
    train = [row for row in rows if row.get("usable_for_training")]
    heldout = [row for row in rows if row.get("stage7_challenge_row")]
    train_pos = [row for row in train if row.get("contrast_label") == "positive"]
    train_neg = [row for row in train if row.get("contrast_label") == "negative"]
    capacity_rows = list(capacity.get("rows") or [])
    capacity_pos = [row for row in capacity_rows if row.get("capacity_label") == "positive_capacity"]
    capacity_neg = [row for row in capacity_rows if row.get("capacity_label") == "negative_capacity"]

    keys = ("source_stage", "provider_family", "provider_local_rank_bucket", "normalized_score_bucket")
    predictions = _leave_state_out_predictions(train, keys)
    false_positives = [
        prediction for prediction in predictions if prediction["predicted_positive"] and not prediction["label_positive"]
    ]
    true_negatives = [
        prediction for prediction in predictions if not prediction["predicted_positive"] and not prediction["label_positive"]
    ]
    positive_predictions = [
        prediction for prediction in predictions if prediction["predicted_positive"] and prediction["label_positive"]
    ]
    status = "selector_negative_suppression_evidence_collected"
    recommended = "design_selector_negative_balance_or_scoring_feature_fix"
    if len(train_neg) < 5:
        status = "selector_negative_evidence_underbalanced"
        recommended = "add_or_reclassify_protected_negative_capacity_controls_non_causal"
    if false_positives and not true_negatives:
        status = "selector_negative_suppression_failure_confirmed"
        recommended = "design_non_causal_negative_suppression_feature_and_label_balance_fix"

    payload = {
        "schema_version": "krk_selector_negative_suppression_evidence.v0",
        "causal_status": "non_causal_evidence_audit",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(CONTRAST), str(PROBE), str(CAPACITY_FRAMES), str(TWO_STAGE)],
        "label_balance": {
            "training_rows": len(train),
            "training_positive_count": len(train_pos),
            "training_negative_count": len(train_neg),
            "training_negative_state_count": len({row.get("state_id") for row in train_neg}),
            "training_negative_stage_counts": dict(Counter(str(row.get("source_stage")) for row in train_neg)),
            "training_negative_provider_family_counts": dict(Counter(str(row.get("provider_family")) for row in train_neg)),
            "stage7_heldout_negative_count": sum(1 for row in heldout if row.get("contrast_label") == "negative"),
            "capacity_positive_count": len(capacity_pos),
            "capacity_negative_count": len(capacity_neg),
            "capacity_negative_state_count": len({row.get("state_id") for row in capacity_neg}),
            "capacity_negative_stage_counts": dict(Counter(str(row.get("source_stage")) for row in capacity_neg)),
            "capacity_negative_provider_family_counts": dict(Counter(str(row.get("provider_family")) for row in capacity_neg)),
        },
        "feature_overlap": {
            "all_training_normalized_score_values": sorted({row.get("normalized_score") for row in train}),
            "negative_training_feature_keys": [
                {
                    "state_id": row.get("state_id"),
                    "provider_id": row.get("provider_id"),
                    "feature_key": list(_feature_key(row, keys)),
                    "global_raw_score_rank": row.get("global_raw_score_rank"),
                    "provider_local_rank": row.get("provider_local_rank"),
                    "normalized_score": row.get("normalized_score"),
                }
                for row in train_neg
            ],
            "positive_training_feature_key_counts": dict(Counter("|".join(_feature_key(row, keys)) for row in train_pos)),
            "negative_training_feature_key_counts": dict(Counter("|".join(_feature_key(row, keys)) for row in train_neg)),
        },
        "leave_state_out_best_objective_replay": {
            "objective": "stage_family_rank_score",
            "feature_keys": list(keys),
            "prediction_count": len(predictions),
            "positive_prediction_count": len(positive_predictions),
            "false_positive_count": len(false_positives),
            "true_negative_count": len(true_negatives),
            "negative_suppression": len(true_negatives) / (len(true_negatives) + len(false_positives))
            if true_negatives or false_positives
            else None,
            "false_positive_rows": false_positives,
        },
        "capacity_negative_controls": [
            {
                "state_id": row.get("state_id"),
                "source_stage": row.get("source_stage"),
                "provider_id": row.get("provider_id"),
                "provider_family": row.get("provider_family"),
                "forced_first_move": row.get("forced_first_move"),
                "forced_plies": row.get("forced_plies"),
                "existing_frame_providers": row.get("existing_frame_providers"),
            }
            for row in capacity_neg
        ],
        "interpretation": {
            "primary": "Negative suppression failure is real but the training negatives are underbalanced and concentrated.",
            "feature_gap": (
                "Current selector features mostly collapse to stage/family/rank/normalized-score buckets; normalized scores are all high, "
                "so current features cannot express why same-family candidates differ in capacity."
            ),
            "data_gap": "Protected negative-capacity controls exist but are not yet proposal-compatible or selector-training rows.",
            "directed_fix_class": "non_causal_negative_balance_and_candidate_scoring_feature_fix_before_runtime",
        },
        "decision": {
            "status": status,
            "recommended_next_step": recommended,
            "runtime_work_allowed": False,
            "candidate_generator_runtime_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_audit(payload)
    return payload


def validate_audit(payload: dict[str, Any]) -> None:
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
    if payload["decision"]["selector_training_allowed"] is not False:
        raise ValueError("selector training remains blocked")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Selector Negative Suppression Evidence v0",
        "",
        "This replay-free audit explains why the two-stage benchmark is blocked on selector negative suppression.",
        "",
        "## Label Balance",
        "",
    ]
    for key, value in payload["label_balance"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Feature Overlap", ""])
    for key, value in payload["feature_overlap"].items():
        lines.append(f"- `{key}`: `{value}`")
    replay = payload["leave_state_out_best_objective_replay"]
    lines.extend(
        [
            "",
            "## Leave-State-Out Replay",
            "",
            f"- Objective: `{replay['objective']}`",
            f"- False positives: `{replay['false_positive_count']}`",
            f"- True negatives: `{replay['true_negative_count']}`",
            f"- Negative suppression: `{replay['negative_suppression']}`",
            "",
            "## False Positive Rows",
            "",
        ]
    )
    for row in replay["false_positive_rows"]:
        lines.append(
            f"- state=`{row['state_id']}` stage=`{row['source_stage']}` provider=`{row['provider_id']}` "
            f"score=`{row['score']}` feature_key=`{row['feature_key']}` forced=`{row['forced_result']}`"
        )
    lines.extend(["", "## Capacity Negative Controls", ""])
    for row in payload["capacity_negative_controls"]:
        lines.append(
            f"- state=`{row['state_id']}` stage=`{row['source_stage']}` provider=`{row['provider_id']}` "
            f"forced_move=`{row['forced_first_move']}` existing=`{row['existing_frame_providers']}`"
        )
    lines.extend(["", "## Interpretation", ""])
    for key, value in payload["interpretation"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_audit()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
