#!/usr/bin/env python3
"""Review provider identity/provenance signal in selector evidence.

This is a non-causal architecture review. It explains why provider identity
currently beats trace-only observation terms without converting that fact into
runtime routing.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FEATURE_DATASET = Path("reports/krk_selector_feature_dataset_v0.json")
FEATURE_PROBE = Path("reports/krk_selector_feature_baseline_probe_v0.json")
OUT_JSON = Path("reports/krk_provider_identity_maturity_review_v0.json")
OUT_MD = Path("reports/krk_provider_identity_maturity_review_v0.md")


PROVIDER_METADATA: dict[str, dict[str, Any]] = {
    "krk.stage0_basin": {
        "provider_family": "stage0_basin",
        "source_stage": "stage0",
        "provider_maturity": "foundation_frozen",
        "protected_provider": True,
        "overlay_provider": False,
        "validated_role": "mate_basin_finish",
    },
    "krk.edge_trap_close": {
        "provider_family": "edge_trap",
        "source_stage": "stage5",
        "provider_maturity": "validated_low_plasticity",
        "protected_provider": True,
        "overlay_provider": False,
        "validated_role": "edge_trap_close",
    },
    "krk.edge_trap_enemy_between": {
        "provider_family": "edge_trap",
        "source_stage": "stage5",
        "provider_maturity": "validated_low_plasticity",
        "protected_provider": True,
        "overlay_provider": False,
        "validated_role": "edge_trap_enemy_between",
    },
    "krk.edge_trap_wrong_tempo": {
        "provider_family": "edge_trap",
        "source_stage": "stage5",
        "provider_maturity": "validated_low_plasticity",
        "protected_provider": True,
        "overlay_provider": False,
        "validated_role": "edge_trap_wrong_tempo",
    },
    "krk.fence_established": {
        "provider_family": "fence",
        "source_stage": "stage5",
        "provider_maturity": "validated_low_plasticity",
        "protected_provider": True,
        "overlay_provider": False,
        "validated_role": "fence_established",
    },
    "krk.drive_to_edge": {
        "provider_family": "drive_to_edge",
        "source_stage": "stage6",
        "provider_maturity": "validated_overlay",
        "protected_provider": True,
        "overlay_provider": True,
        "validated_role": "drive_to_edge",
    },
    "krk.box_shrink": {
        "provider_family": "box_shrink",
        "source_stage": "stage7",
        "provider_maturity": "quarantined_no_plasticity",
        "protected_provider": False,
        "overlay_provider": True,
        "validated_role": "local_valid_composition_quarantined",
    },
    "krk.post_box_shrink_continuation": {
        "provider_family": "post_box_continuation",
        "source_stage": "stage7",
        "provider_maturity": "quarantined_no_plasticity",
        "protected_provider": False,
        "overlay_provider": True,
        "validated_role": "selected_but_closed_loop_fails",
    },
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _rate(counter: Counter[str], label: str) -> float | None:
    total = sum(counter.values())
    if total == 0:
        return None
    return counter.get(label, 0) / total


def _summarize_group(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, Counter[str]] = defaultdict(Counter)
    stages: dict[str, Counter[str]] = defaultdict(Counter)
    landmarks: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        value = str(row.get(key) or "unknown")
        label = str(row.get("label") or "none")
        groups[value][label] += 1
        stages[value][str(row.get("source_stage") or "unknown")] += 1
        landmarks[value][str(row.get("active_landmark_label") or "unknown")] += 1
    result = []
    for value, counts in sorted(groups.items()):
        metadata = PROVIDER_METADATA.get(value, {}) if key == "provider_id" else {}
        result.append({
            key: value,
            "count": sum(counts.values()),
            "label_counts": dict(sorted(counts.items())),
            "positive_rate": _rate(counts, "positive"),
            "negative_rate": _rate(counts, "negative"),
            "stage_distribution": dict(sorted(stages[value].items())),
            "active_landmark_distribution": dict(sorted(landmarks[value].items())),
            "metadata": metadata,
        })
    return result


def build_review() -> dict[str, Any]:
    dataset = _load_json(FEATURE_DATASET)
    probe = _load_json(FEATURE_PROBE)
    rows = [
        row for row in dataset.get("rows", []) or []
        if row.get("target_kind") == "selected_playout_success"
        and row.get("usable_for_training")
        and row.get("label") in {"positive", "negative"}
    ]
    provider_summary = _summarize_group(rows, "provider_id")
    stage_summary = _summarize_group(rows, "source_stage")
    landmark_summary = _summarize_group(rows, "active_landmark_label")
    provider_prior = next(
        item for item in probe.get("baselines", [])
        if item.get("name") == "provider_prior_loo"
    )
    feature_best = probe.get("best_baseline", {})
    provider_counts = {item["provider_id"]: item for item in provider_summary}
    stage0_rate = provider_counts.get("krk.stage0_basin", {}).get("positive_rate")
    edge_rates = [
        item.get("positive_rate")
        for item in provider_summary
        if str(item.get("provider_id", "")).startswith("krk.edge_trap")
    ]
    raw_provider_id_is_principled = False
    return {
        "schema_version": "krk_provider_identity_maturity_review.v0",
        "causal_status": "non_causal_architecture_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifacts": [str(FEATURE_DATASET), str(FEATURE_PROBE)],
        "row_count": len(rows),
        "provider_prior_accuracy": provider_prior.get("accuracy"),
        "best_feature_probe_baseline": feature_best,
        "provider_summary": provider_summary,
        "stage_summary": stage_summary,
        "active_landmark_summary": landmark_summary,
        "interpretation": {
            "raw_provider_id_is_principled_runtime_signal": raw_provider_id_is_principled,
            "provider_identity_signal": "strong_but_not_causal_ready",
            "reason": [
                "Provider identity currently beats trace-only observation terms on selected-playout labels.",
                "The signal is mostly a maturity/provenance prior: stage0_basin selected-playout controls are often positive while edge-trap variants are often negative in this dataset.",
                "Raw provider id can encode dataset and label bias, so it should be decomposed into explicit provenance, maturity, scope, and validation-status features before any future sandbox.",
                "Stage7 rows remain held out and should not be used to tune a selector."
            ],
            "stage0_basin_positive_rate": stage0_rate,
            "edge_trap_positive_rates": edge_rates,
        },
        "decision": {
            "status": "provider_identity_signal_requires_provenance_decomposition",
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "stage7_repair_allowed": False,
            "stage8_training_allowed": False,
            "recommended_next_step": "add_provider_provenance_maturity_features_non_causal",
        },
        "required_future_features": [
            "provider_maturity",
            "provider_version",
            "source_stage",
            "validated_profile",
            "frozen_provider",
            "overlay_provider",
            "guardrail_status",
            "plasticity_scope",
            "promotion_status",
            "protected_provider",
        ],
        "blocked_next_work": [
            "runtime_arbiter",
            "selector_sandbox",
            "raw_provider_id_runtime_prior",
            "provider_support_adapter",
            "score_bonus_or_penalty",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Provider Identity / Maturity Review v0",
        "",
        "This non-causal review explains why provider identity is currently the strongest selector baseline and why that does not authorize runtime arbitration.",
        "",
        "## Summary",
        "",
        f"- Rows: `{payload['row_count']}` selected-playout training examples",
        f"- Provider-prior LOO accuracy: `{payload['provider_prior_accuracy']}`",
        f"- Decision: `{payload['decision']['status']}`",
        f"- Runtime arbiter allowed: `{payload['decision']['runtime_arbiter_allowed']}`",
        f"- Selector sandbox ready: `{payload['decision']['selector_sandbox_ready']}`",
        "",
        "## Provider Outcomes",
        "",
    ]
    for item in payload["provider_summary"]:
        lines.append(
            f"- `{item['provider_id']}` count=`{item['count']}` "
            f"positive_rate=`{item['positive_rate']}` labels=`{item['label_counts']}` "
            f"maturity=`{item['metadata'].get('provider_maturity', 'unknown')}`"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
    ])
    for reason in payload["interpretation"]["reason"]:
        lines.append(f"- {reason}")
    lines.extend([
        "",
        "## Required Future Features",
        "",
    ])
    for feature in payload["required_future_features"]:
        lines.append(f"- `{feature}`")
    lines.extend([
        "",
        "## Blocked",
        "",
    ])
    for blocked in payload["blocked_next_work"]:
        lines.append(f"- `{blocked}`")
    lines.extend([
        "",
        "## Recommended Next Step",
        "",
        f"`{payload['decision']['recommended_next_step']}`",
        "",
        "Decompose provider identity into explicit non-causal provenance/maturity features before considering more selector baselines or any sandbox design.",
    ])
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)


if __name__ == "__main__":
    main()
