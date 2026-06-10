#!/usr/bin/env python3
"""Offline probe over ranked KRK StrategyProposalFrame rows."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/krk_ranked_strategy_proposal_frames_v1.json")
OUT_JSON = Path("reports/krk_ranked_strategy_proposal_frame_probe_v1.json")
OUT_MD = Path("reports/krk_ranked_strategy_proposal_frame_probe_v1.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _label_bool(outcome: str) -> bool | None:
    if outcome == "mate":
        return True
    if outcome == "max_plies":
        return False
    return None


def _bucket_raw(score: float | None) -> str:
    if score is None:
        return "missing"
    if score >= 20:
        return "raw_high"
    if score >= 1:
        return "raw_mid"
    return "raw_low"


def _group_frames(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_frame: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_frame[str(row.get("frame_id"))].append(row)

    frames = []
    for frame_id, frame_rows in by_frame.items():
        sorted_rows = sorted(frame_rows, key=lambda row: int(row.get("global_raw_score_rank") or 999))
        top = sorted_rows[0]
        families = Counter(str(row.get("provider_family")) for row in sorted_rows)
        max_norm_by_family: dict[str, float] = {}
        for row in sorted_rows:
            family = str(row.get("provider_family"))
            value = row.get("normalized_score")
            score = float(value) if isinstance(value, (int, float)) else 0.0
            max_norm_by_family[family] = max(score, max_norm_by_family.get(family, 0.0))
        outcome = str(top.get("frame_outcome") or "unknown")
        frames.append({
            "frame_id": frame_id,
            "state_id": top.get("state_id"),
            "source_stage": top.get("source_stage"),
            "active_landmark_label": top.get("active_landmark_label"),
            "frame_outcome": outcome,
            "label_positive": _label_bool(outcome),
            "stage7_challenge": bool(top.get("stage7_challenge_row")),
            "proposal_count": len(sorted_rows),
            "top_provider_family": top.get("provider_family"),
            "top_provider_maturity": top.get("provider_maturity"),
            "top_raw_score_bucket": _bucket_raw(top.get("raw_score")),
            "top_normalized_score_bucket": _bucket_raw(top.get("normalized_score")),
            "provider_family_set": sorted(families),
            "has_drive_to_edge": "drive_to_edge" in families,
            "has_edge_trap": "edge_trap" in families,
            "has_fence_established": "fence_established" in families,
            "has_stage0_basin": "stage0_basin" in families,
            "max_norm_by_family": max_norm_by_family,
            "causal_status": "non_causal",
        })
    return frames


def _key(frame: dict[str, Any], keys: tuple[str, ...]) -> tuple[str, ...]:
    values = []
    for key in keys:
        value = frame.get(key)
        if isinstance(value, list):
            value = ",".join(value)
        values.append(str(value))
    return tuple(values)


def _loo(frames: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[str, Any]:
    labeled = [frame for frame in frames if frame.get("label_positive") is not None and not frame.get("stage7_challenge")]
    predictions = []
    for index, frame in enumerate(labeled):
        train = labeled[:index] + labeled[index + 1 :]
        global_rate = sum(1 for item in train if item["label_positive"]) / len(train) if train else 0.5
        rates: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
        for item in train:
            rates[_key(item, keys)]["positive" if item["label_positive"] else "negative"] += 1
        counter = rates.get(_key(frame, keys))
        if counter:
            total = counter["positive"] + counter["negative"]
            score = counter["positive"] / total if total else global_rate
        else:
            score = global_rate
        predictions.append({
            "frame_id": frame["frame_id"],
            "score": score,
            "predicted_positive": score >= 0.5,
            "label_positive": frame["label_positive"],
        })
    return _metrics(predictions)


def _metrics(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(predictions)
    correct = sum(1 for item in predictions if item["predicted_positive"] == item["label_positive"])
    tp = sum(1 for item in predictions if item["predicted_positive"] and item["label_positive"])
    fp = sum(1 for item in predictions if item["predicted_positive"] and not item["label_positive"])
    tn = sum(1 for item in predictions if not item["predicted_positive"] and not item["label_positive"])
    fn = sum(1 for item in predictions if not item["predicted_positive"] and item["label_positive"])
    return {
        "row_count": total,
        "accuracy": correct / total if total else None,
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "positive_precision": tp / (tp + fp) if tp + fp else None,
        "positive_recall": tp / (tp + fn) if tp + fn else None,
        "negative_suppression": tn / (tn + fp) if tn + fp else None,
    }


def build_probe() -> dict[str, Any]:
    dataset = _load_json(DATASET)
    if dataset.get("causal_status") != "non_causal_ranked_frame_dataset":
        raise ValueError("ranked proposal dataset must remain non-causal")

    frames = _group_frames(list(dataset.get("rows") or []))
    specs = {
        "top_provider_family": ("top_provider_family",),
        "top_family_maturity": ("top_provider_family", "top_provider_maturity"),
        "active_label_top_family": ("active_landmark_label", "top_provider_family"),
        "top_family_raw_bucket": ("top_provider_family", "top_raw_score_bucket"),
        "provider_family_set": ("provider_family_set",),
        "source_stage_top_family": ("source_stage", "top_provider_family"),
    }
    results = {name: _loo(frames, keys) for name, keys in specs.items()}
    best_name, best_metrics = max(
        results.items(), key=lambda item: item[1]["accuracy"] if item[1]["accuracy"] is not None else -1
    )
    training_frames = [f for f in frames if f.get("label_positive") is not None and not f.get("stage7_challenge")]
    stage7_frames = [f for f in frames if f.get("stage7_challenge")]
    underpowered = len(training_frames) < 30

    probe = {
        "schema_version": "krk_ranked_strategy_proposal_frame_probe.v1",
        "causal_status": "non_causal_offline_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifact": str(DATASET),
        "frame_summary": {
            "frame_count": len(frames),
            "training_frame_count": len(training_frames),
            "stage7_challenge_frame_count": len(stage7_frames),
            "outcome_counts": dict(Counter(str(f["frame_outcome"]) for f in frames)),
            "top_provider_family_counts": dict(Counter(str(f["top_provider_family"]) for f in frames)),
            "stage7_top_provider_family_counts": dict(
                Counter(str(f["top_provider_family"]) for f in stage7_frames)
            ),
        },
        "results": results,
        "best_result": {"objective": best_name, **{k: v for k, v in best_metrics.items() if k != "predictions"}},
        "benchmark_underpowered": underpowered,
        "interpretation": {
            "stage7_training_leakage": False,
            "finding": (
                "Ranked proposal-frame context is available, but frame-level outcome labels are "
                "too coarse to identify the winning proposal inside a frame."
            ),
        },
        "decision": {
            "status": (
                "ranked_frames_available_label_semantics_too_coarse"
                if underpowered
                else "ranked_frames_probe_complete_review_required"
            ),
            "recommended_next_step": "derive_state_local_contrast_labels_before_runtime_selector",
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_probe(probe)
    return probe


def validate_probe(probe: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if probe.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if probe.get("decision", {}).get("runtime_test_allowed_next") is not False:
        raise ValueError("runtime tests remain blocked")


def render_markdown(probe: dict[str, Any]) -> str:
    lines = [
        "# KRK Ranked Strategy Proposal Frame Probe v1",
        "",
        "This offline probe evaluates frame-level ranked proposal context. It does not treat every proposal in a successful frame as a positive owner.",
        "",
        "## Frame Summary",
        "",
    ]
    for key, value in probe["frame_summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Results", ""])
    for name, metrics in probe["results"].items():
        lines.append(
            f"- `{name}` accuracy=`{metrics['accuracy']}` "
            f"precision=`{metrics['positive_precision']}` "
            f"recall=`{metrics['positive_recall']}` "
            f"negative_suppression=`{metrics['negative_suppression']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Stage 7 training leakage: `{probe['interpretation']['stage7_training_leakage']}`",
            f"- Finding: {probe['interpretation']['finding']}",
            "",
            "## Decision",
            "",
            f"- Status: `{probe['decision']['status']}`",
            f"- Recommended next step: `{probe['decision']['recommended_next_step']}`",
            f"- Runtime test allowed next: `{probe['decision']['runtime_test_allowed_next']}`",
            f"- Stage 7 promotion allowed: `{probe['decision']['stage7_promotion_allowed']}`",
            f"- Stage 8 training allowed: `{probe['decision']['stage8_training_allowed']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    probe = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(probe, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(probe), encoding="utf-8")
    print(json.dumps(probe["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
