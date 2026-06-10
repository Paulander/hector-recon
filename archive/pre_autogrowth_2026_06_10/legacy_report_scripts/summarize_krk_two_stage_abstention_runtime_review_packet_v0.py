#!/usr/bin/env python3
"""Package the two-stage abstention evidence for architecture review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROBE = Path("reports/krk_two_stage_abstention_objective_probe_v0.json")
LABEL_REVIEW = Path("reports/krk_abstention_safe_preservation_label_review_v0.json")
ERROR_AUDIT = Path("reports/krk_abstention_context_error_audit_v0.json")
OUT_JSON = Path("reports/krk_two_stage_abstention_runtime_review_packet_v0.json")
OUT_MD = Path("reports/krk_two_stage_abstention_runtime_review_packet_v0.md")


def _load_json(root: Path, path: Path) -> dict[str, Any]:
    payload = json.loads((root / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def validate_packet(payload: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["decision"]["implementation_allowed_by_this_packet"] is not False:
        raise ValueError("review packet must not directly authorize implementation")


def build_packet(root: Path = ROOT) -> dict[str, Any]:
    probe = _load_json(root, PROBE)
    label_review = _load_json(root, LABEL_REVIEW)
    error_audit = _load_json(root, ERROR_AUDIT)
    for name, payload in (("probe", probe), ("label_review", label_review), ("error_audit", error_audit)):
        if not str(payload.get("causal_status") or "").startswith("non_causal"):
            raise ValueError(f"{name} must remain non-causal")
    best = probe.get("best_threshold_passing_result") or {}
    packet = {
        "schema_version": "krk_two_stage_abstention_runtime_review_packet.v0",
        "causal_status": "non_causal_architecture_review_packet",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(PROBE), str(LABEL_REVIEW), str(ERROR_AUDIT)],
        "accepted_evidence": {
            "row_count": (probe.get("summary") or {}).get("row_count"),
            "state_count": (probe.get("summary") or {}).get("state_count"),
            "stage_counts": (probe.get("summary") or {}).get("stage_counts"),
            "threshold_passing_objective_count": (probe.get("summary") or {}).get("threshold_passing_objective_count"),
            "best_objective_id": best.get("objective_id"),
            "best_negative_suppression": best.get("negative_suppression"),
            "best_safe_preservation": best.get("safe_preservation"),
            "best_accuracy": best.get("accuracy"),
            "best_error_counts": best.get("error_counts"),
        },
        "why_this_is_different_from_prior_runtime_tests": [
            "Earlier additive support and one-stage context objectives either failed to move ownership or over-rejected safe owners.",
            "The two-stage objective explicitly separates safe-owner preservation from unsafe-owner suppression.",
            "The best threshold-passing objective clears both offline review thresholds on protected Stage 4/5/6 rows and keeps Stage 7 out of training.",
        ],
        "remaining_risks": [
            "The evidence is still small: 51 rows across 15 states.",
            "The features include FEN-derived proxy context and monitor signatures; these must be exposed as visible trace/state if ever used causally.",
            "Stage 7 remains a held-out challenge and is not solved by this packet.",
            "This packet does not prove guardrail safety under runtime arbitration.",
            "A runtime selector could still perturb protected provider ownership if not strictly default-off and scoped.",
        ],
        "future_sandbox_requirements_if_approved": [
            "default_off_flag_required",
            "default_off_equivalence_required_before_enabled_smoke",
            "visible_trace_metadata_for_preserve_score_and_unsafe_score",
            "no_runtime_dtm_or_tablebase",
            "no_gameplay_topology_mutation",
            "no_stage7_training_or_promotion",
            "protected_stage4_stage5_stage6_guardrails_before_any_promotion_discussion",
            "M1_M4_preservation_suite_before_any_promotion_discussion",
        ],
        "suggested_future_flag_names_if_approved": [
            "--enable-krk-two-stage-abstention-selector",
            "--krk-abstention-preserve-threshold",
            "--krk-abstention-unsafe-threshold",
        ],
        "review_question": (
            "Should the next slice implement a strictly default-off two-stage abstention selector sandbox "
            "using the threshold-passing objective, with default-off equivalence and trace-only first?"
        ),
        "decision": {
            "status": "two_stage_abstention_review_ready_implementation_blocked",
            "recommended_next_step": "explicit_review_before_default_off_runtime_selector_implementation",
            "implementation_allowed_by_this_packet": False,
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_packet(packet)
    return packet


def render_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# KRK Two-Stage Abstention Runtime Review Packet v0",
        "",
        "This packet summarizes the first offline abstention result that clears both review thresholds. It does not implement or authorize runtime selector behavior.",
        "",
        "## Accepted Evidence",
        "",
    ]
    for key, value in packet["accepted_evidence"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Why This Is Different", ""])
    for item in packet["why_this_is_different_from_prior_runtime_tests"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Remaining Risks", ""])
    for item in packet["remaining_risks"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Future Sandbox Requirements If Approved", ""])
    for item in packet["future_sandbox_requirements_if_approved"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Review Question", "", packet["review_question"], "", "## Decision", ""])
    lines.append(f"- Status: `{packet['decision']['status']}`")
    lines.append(f"- Recommended next step: `{packet['decision']['recommended_next_step']}`")
    lines.append(f"- Implementation allowed by this packet: `{packet['decision']['implementation_allowed_by_this_packet']}`")
    lines.append(f"- Runtime test allowed next: `{packet['decision']['runtime_test_allowed_next']}`")
    lines.append(f"- Stage 7 promotion allowed: `{packet['decision']['stage7_promotion_allowed']}`")
    lines.append(f"- Stage 8 training allowed: `{packet['decision']['stage8_training_allowed']}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    packet = build_packet()
    (ROOT / OUT_JSON).write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(packet), encoding="utf-8")
    print(json.dumps(packet["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
