#!/usr/bin/env python3
"""Summarize selector readiness after KRK strategy-owner contrast evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/krk_strategy_owner_contrast_dataset_v0.json")
PROBE = Path("reports/krk_strategy_owner_contrast_probe_v0.json")
OUT_JSON = Path("reports/krk_selector_readiness_after_contrast_probe_review_v0.json")
OUT_MD = Path("reports/krk_selector_readiness_after_contrast_probe_review_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    dataset = _load_json(DATASET)
    probe = _load_json(PROBE)
    if dataset.get("causal_status") != "non_causal_dataset":
        raise ValueError("dataset must remain non-causal")
    if probe.get("causal_status") != "non_causal_probe":
        raise ValueError("probe must remain non-causal")
    metrics = probe.get("metrics") or {}
    readiness = dataset.get("readiness_v2_assessment") or {}
    blockers = list(readiness.get("blockers") or [])
    evidence_strengths = []
    if readiness.get("contrast_probe_ready"):
        evidence_strengths.append("protected_strategy_owner_contrast_probe_ready")
    if "protected_conversion_positive_provider_diversity_present" in (probe.get("findings") or []):
        evidence_strengths.append("conversion_positive_provider_diversity_present")
    if "protected_label_balance_present" in (probe.get("findings") or []):
        evidence_strengths.append("protected_label_balance_present")
    residual_risks = []
    if "insufficient_selected_provider_family_diversity" in blockers:
        residual_risks.append("selected_provider_family_diversity_missing")
    if "heldout_stage7_contains_unresolved_all_negative_rows" in (probe.get("findings") or []):
        residual_risks.append("stage7_heldout_contains_unresolved_all_negative_rows")

    review = {
        "schema_version": "krk_selector_readiness_after_contrast_probe_review.v0",
        "causal_status": "non_causal_architecture_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(DATASET), str(PROBE)],
        "evidence": {
            "dataset_decision": (dataset.get("decision") or {}).get("status"),
            "probe_decision": (probe.get("decision") or {}).get("status"),
            "training_row_count": metrics.get("training_row_count"),
            "heldout_row_count": metrics.get("heldout_row_count"),
            "training_positive_label_count": metrics.get("training_positive_label_count"),
            "training_negative_label_count": metrics.get("training_negative_label_count"),
            "selected_training_provider_families": metrics.get("selected_training_provider_families"),
            "readiness_blockers": blockers,
            "evidence_strengths": evidence_strengths,
            "residual_risks": residual_risks,
        },
        "decision": {
            "status": "selector_sandbox_blocked_selected_provider_evidence_missing",
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": "design_non_causal_selected_provider_diversity_evidence_plan",
        },
        "next_allowed_options": [
            {
                "option": "selected_provider_diversity_evidence_plan",
                "status": "non_causal_design_only",
                "purpose": "Find protected states where normal arbitration selects non-stage0/non-edge providers without using Stage7 training rows.",
            },
            {
                "option": "strategy_owner_feature_probe_v2",
                "status": "non_causal_probe_only",
                "purpose": "Use the stronger contrast labels to test feature separability before any selector objective work.",
            },
            {
                "option": "pause_runtime_selector",
                "status": "safe_stop",
                "purpose": "Record that contrast evidence is useful but not enough for sandbox readiness.",
            },
        ],
        "blocked_next_steps": [
            "runtime_arbiter",
            "selector_sandbox",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_review(review)
    return review


def validate_review(review: dict[str, Any]) -> None:
    if review.get("causal_status") != "non_causal_architecture_review":
        raise ValueError("review must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_arbiter_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if review.get(key) is not False:
            raise ValueError(f"{key} must be false")


def render_markdown(review: dict[str, Any]) -> str:
    evidence = review["evidence"]
    lines = [
        "# KRK Selector Readiness After Contrast Probe Review v0",
        "",
        "This architecture review summarizes the non-causal strategy-owner contrast evidence. "
        "It does not implement a selector or authorize a sandbox.",
        "",
        "## Evidence",
        "",
        f"- Dataset decision: `{evidence['dataset_decision']}`",
        f"- Probe decision: `{evidence['probe_decision']}`",
        f"- Training rows: `{evidence['training_row_count']}`",
        f"- Held-out rows: `{evidence['heldout_row_count']}`",
        f"- Training positives / negatives: `{evidence['training_positive_label_count']}` / `{evidence['training_negative_label_count']}`",
        f"- Selected training provider families: `{evidence['selected_training_provider_families']}`",
        f"- Readiness blockers: `{evidence['readiness_blockers']}`",
        f"- Evidence strengths: `{evidence['evidence_strengths']}`",
        f"- Residual risks: `{evidence['residual_risks']}`",
        "",
        "## Decision",
        "",
        f"- Status: `{review['decision']['status']}`",
        f"- Recommended next step: `{review['decision']['recommended_next_step']}`",
        "- Runtime arbiter and selector sandbox remain blocked.",
        "",
        "## Next Allowed Options",
        "",
    ]
    for option in review["next_allowed_options"]:
        lines.append(f"- `{option['option']}`: {option['purpose']}")
    return "\n".join(lines) + "\n"


def main() -> None:
    review = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(review), encoding="utf-8")
    print(json.dumps(review["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
