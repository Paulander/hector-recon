#!/usr/bin/env python3
"""Create a runtime-review packet for paired ownership selector semantics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROBE = Path("reports/krk_state_local_paired_ownership_probe_v1.json")
REVIEW = Path("reports/krk_state_local_paired_ownership_review_v1.json")
OUT_JSON = Path("reports/krk_state_local_paired_selector_runtime_review_packet_v0.json")
OUT_MD = Path("reports/krk_state_local_paired_selector_runtime_review_packet_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_packet() -> dict[str, Any]:
    probe = _load(PROBE)
    review = _load(REVIEW)
    if probe.get("causal_status") != "non_causal_offline_probe":
        raise ValueError("probe must remain non-causal")
    if review.get("causal_status") != "non_causal_architecture_review":
        raise ValueError("review must remain non-causal")
    best = probe.get("best_result") or {}
    threshold_passing = probe.get("threshold_passing_models") or {}
    runtime_feature_passing = probe.get("runtime_feature_passing_models") or {}
    translation_blocker = bool(threshold_passing) and not bool(runtime_feature_passing)
    payload = {
        "schema_version": "krk_state_local_paired_selector_runtime_review_packet.v0",
        "causal_status": "non_causal_runtime_review_packet",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "selector_training_allowed": False,
        "implementation_allowed_by_this_packet": False,
        "source_artifacts": [str(PROBE), str(REVIEW)],
        "summary": {
            "review_status": (review.get("decision") or {}).get("status"),
            "best_objective": best.get("objective"),
            "prefer_capacity_recall": best.get("prefer_capacity_recall"),
            "selected_preservation_recall": best.get("selected_preservation_recall"),
            "safe_preservation_recall": best.get("safe_preservation_recall"),
            "strong_conflict_accuracy": best.get("strong_conflict_accuracy"),
            "threshold_passing_model_count": len(threshold_passing),
            "runtime_feature_passing_model_count": len(runtime_feature_passing),
            "runtime_feature_translation_blocker": translation_blocker,
            "stage7_row_count": (probe.get("summary") or {}).get("stage7_row_count"),
        },
        "runtime_sandbox_requirements": [
            "default_off",
            "profile_scoped_to_handoff_composition_v1_or_successor_review_profile",
            "trace_every_suppression_or_prefer_capacity_decision",
            "never_use_dtm_or_tablebase_at_runtime",
            "no_gameplay_topology_mutation",
            "no_direct_provider_request_from_metadata",
            "rollback_tag_before_implementation",
        ],
        "translation_requirements_before_implementation": [
            "replace offline owner_a_positive with visible selected-owner safety/failure-risk proxy",
            "replace owner_b_positive forced-capacity labels with visible candidate-support evidence",
            "preserve selected-mate/safe-owner behavior unless visible failure evidence is present",
            "keep Stage 7 as held-out evaluation only",
        ],
        "guardrails_required_before_any_promotion": [
            "default_off_equivalence",
            "protected_stage4_control",
            "protected_stage5_fence",
            "protected_stage6_drive",
            "Stage7_holdout_challenge_no_regression",
            "M1_M4_preservation_suite",
        ],
        "decision": {
            "status": (
                "runtime_review_packet_ready_with_translation_blocker"
                if translation_blocker
                else "runtime_review_packet_ready"
            ),
            "implementation_allowed_by_this_packet": False,
            "recommended_next_step": (
                "explicit_architecture_review_for_visible_runtime_proxy_design"
                if translation_blocker
                else "explicit_approval_required_before_default_off_sandbox_implementation"
            ),
        },
        "blocked_next_steps": [
            "runtime_selector_implementation_without_explicit_approval",
            "selector_training",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_packet(payload)
    return payload


def validate_packet(payload: dict[str, Any]) -> None:
    if payload.get("causal_status") != "non_causal_runtime_review_packet":
        raise ValueError("packet must remain non-causal")
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
        "selector_training_allowed",
        "implementation_allowed_by_this_packet",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK State-Local Paired Selector Runtime Review Packet v0",
        "",
        "This packet summarizes non-causal readiness evidence. It does not authorize implementation.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Runtime Sandbox Requirements", ""])
    for item in payload["runtime_sandbox_requirements"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Translation Requirements Before Implementation", ""])
    for item in payload["translation_requirements_before_implementation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Guardrails Required", ""])
    for item in payload["guardrails_required_before_any_promotion"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def write_outputs(repo_root: Path, payload: dict[str, Any]) -> None:
    (repo_root / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (repo_root / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    payload = build_packet()
    write_outputs(repo_root, payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
