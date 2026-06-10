#!/usr/bin/env python3
"""Probe KRK strategy-arbiter out-of-sample control labels.

This is replay-free and non-causal. It evaluates whether the new protected
control labels are informative enough for selector sandbox review.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LABELS = Path("reports/krk_strategy_arbiter_out_of_sample_control_labels_v0.json")
OUT_JSON = Path("reports/krk_strategy_arbiter_out_of_sample_control_probe_v0.json")
OUT_MD = Path("reports/krk_strategy_arbiter_out_of_sample_control_probe_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _result(label: dict[str, Any], key: str) -> str:
    value = (label.get(key) or {}).get("result")
    return str(value or "unknown")


def build_probe() -> dict[str, Any]:
    payload = _load_json(LABELS)
    if payload.get("causal_status") != "non_causal_label_run":
        raise ValueError("input labels must remain non-causal")
    labels = payload.get("labels") or []
    selected_counts = Counter(_result(label, "selected_playout_success") for label in labels)
    forced_counts = Counter(
        _result(label, "forced_provider_conversion_for_selected_provider") for label in labels
    )
    selected_provider_counts = Counter(str(label.get("selected_provider") or "unknown") for label in labels)
    stage_counts = Counter(str(label.get("source_stage") or "unknown") for label in labels)
    stage_result_counts = Counter(
        f"{label.get('source_stage')}:{_result(label, 'selected_playout_success')}"
        for label in labels
    )
    agreement_count = sum(
        1
        for label in labels
        if _result(label, "selected_playout_success")
        == _result(label, "forced_provider_conversion_for_selected_provider")
    )
    positive = selected_counts.get("mate", 0)
    negative = sum(count for result, count in selected_counts.items() if result != "mate")
    provider_dominance = (
        max(selected_provider_counts.values()) / len(labels)
        if labels and selected_provider_counts
        else 0.0
    )
    positive_rate = positive / len(labels) if labels else 0.0
    forced_agreement_rate = agreement_count / len(labels) if labels else 0.0
    sandbox_blockers = []
    if len(labels) < 12:
        sandbox_blockers.append("too_few_out_of_sample_labels")
    if positive == 0 or negative == 0:
        sandbox_blockers.append("single_class_labels")
    elif min(positive, negative) / max(positive, negative) < 0.5:
        sandbox_blockers.append("class_imbalance")
    if provider_dominance > 0.8:
        sandbox_blockers.append("selected_provider_dominance")
    if stage_counts.get("stage4", 0) == 0 or stage_counts.get("stage5", 0) == 0 or stage_counts.get("stage6", 0) == 0:
        sandbox_blockers.append("missing_protected_stage")
    status = (
        "out_of_sample_controls_guardrail_positive_selector_sandbox_blocked"
        if sandbox_blockers
        else "out_of_sample_controls_selector_review_ready"
    )
    return {
        "schema_version": "krk_strategy_arbiter_out_of_sample_control_probe.v0",
        "causal_status": "non_causal_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(LABELS)],
        "metrics": {
            "label_count": len(labels),
            "selected_result_counts": dict(sorted(selected_counts.items())),
            "forced_selected_provider_result_counts": dict(sorted(forced_counts.items())),
            "selected_provider_counts": dict(sorted(selected_provider_counts.items())),
            "stage_counts": dict(sorted(stage_counts.items())),
            "stage_result_counts": dict(sorted(stage_result_counts.items())),
            "positive_rate": positive_rate,
            "negative_count": negative,
            "forced_selected_agreement_rate": forced_agreement_rate,
            "selected_provider_dominance": provider_dominance,
        },
        "interpretation": {
            "protected_controls_mostly_convert": positive_rate >= 0.8,
            "selected_vs_forced_selected_agree": forced_agreement_rate >= 0.9,
            "selector_training_signal_is_weak": bool(sandbox_blockers),
            "stage4_caveat": stage_result_counts.get("stage4:max_plies", 0) > 0,
            "notes": [
                "Out-of-sample controls mostly confirm the protected stack converts under current routing.",
                "All selected providers are dominated by stage0_basin, so this is weak evidence for a general selector.",
                "The single Stage4 max_plies remains a protected-control caveat, not Stage7 evidence.",
            ],
        },
        "decision": {
            "status": status,
            "sandbox_blockers": sandbox_blockers,
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": (
                "architecture_review_of_selector_signal_before_runtime_sandbox"
                if sandbox_blockers
                else "prepare_default_off_selector_sandbox_design_review"
            ),
        },
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


def render_markdown(probe: dict[str, Any]) -> str:
    metrics = probe["metrics"]
    decision = probe["decision"]
    lines = [
        "# KRK Strategy Arbiter Out-of-Sample Control Probe v0",
        "",
        "This replay-free probe evaluates the new protected-control labels. It does not "
        "implement a selector, change runtime behavior, promote Stage 7, or train Stage 8.",
        "",
        "## Metrics",
        "",
        f"- Label count: `{metrics['label_count']}`",
        f"- Selected result counts: `{metrics['selected_result_counts']}`",
        f"- Forced selected-provider result counts: `{metrics['forced_selected_provider_result_counts']}`",
        f"- Selected provider counts: `{metrics['selected_provider_counts']}`",
        f"- Stage result counts: `{metrics['stage_result_counts']}`",
        f"- Forced selected agreement rate: `{metrics['forced_selected_agreement_rate']:.3f}`",
        f"- Selected provider dominance: `{metrics['selected_provider_dominance']:.3f}`",
        "",
        "## Interpretation",
        "",
    ]
    for note in probe["interpretation"]["notes"]:
        lines.append(f"- {note}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{decision['status']}`",
            f"- Sandbox blockers: `{decision['sandbox_blockers']}`",
            f"- Recommended next step: `{decision['recommended_next_step']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    probe = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(probe, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(probe), encoding="utf-8")
    print(json.dumps(probe["metrics"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
