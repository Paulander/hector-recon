#!/usr/bin/env python3
"""Review selected-provider diversity evidence after bounded sampling."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPLAY_SCAN = Path("reports/krk_selected_provider_diversity_replay_free_scan_v0.json")
OBS_SCAN = Path("reports/krk_selected_provider_diversity_observation_scan_v0.json")
CONTRAST_PROBE = Path("reports/krk_strategy_owner_contrast_probe_v0.json")
OUT_JSON = Path("reports/krk_selected_provider_diversity_architecture_review_v0.json")
OUT_MD = Path("reports/krk_selected_provider_diversity_architecture_review_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    replay = _load_json(REPLAY_SCAN)
    obs = _load_json(OBS_SCAN)
    contrast = _load_json(CONTRAST_PROBE)
    if replay.get("causal_status") != "non_causal_scan":
        raise ValueError("replay-free scan must remain non-causal")
    if obs.get("causal_status") != "non_causal_observation_scan":
        raise ValueError("observation scan must remain non-causal")
    if contrast.get("causal_status") != "non_causal_probe":
        raise ValueError("contrast probe must remain non-causal")
    replay_summary = replay.get("summary") or {}
    obs_summary = obs.get("summary") or {}
    contrast_metrics = contrast.get("metrics") or {}
    review = {
        "schema_version": "krk_selected_provider_diversity_architecture_review.v0",
        "causal_status": "non_causal_architecture_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(REPLAY_SCAN), str(OBS_SCAN), str(CONTRAST_PROBE)],
        "evidence": {
            "replay_free_selected_provider_families": replay_summary.get("selected_provider_family_counts"),
            "replay_free_distinct_families": replay_summary.get("distinct_selected_provider_families"),
            "replay_free_max_dominance": replay_summary.get("max_selected_provider_family_dominance"),
            "sampled_selected_provider_families": obs_summary.get("selected_provider_family_counts"),
            "sampled_distinct_families": obs_summary.get("distinct_selected_provider_families"),
            "sampled_max_dominance": obs_summary.get("max_selected_provider_family_dominance"),
            "contrast_training_family_rates": contrast_metrics.get("training_provider_family_rates"),
            "contrast_findings": contrast.get("findings"),
        },
        "interpretation": {
            "current_selected_provider_diversity_status": "failed_by_current_arbitration_stage0_dominance",
            "reason": (
                "Replay-free selected records only show stage0_basin/edge_trap, and bounded protected "
                "selection sampling selected stage0_basin for every sampled state. This is a property "
                "of the current raw arbitration policy, not evidence that other providers lack conversion value."
            ),
            "contrast_evidence_status": "provider_contrast_signal_present",
            "readiness_v2_issue": (
                "Requiring diverse normal selected providers before testing an arbiter may be too hard, "
                "because the proposed arbiter is intended to correct current selected-provider dominance."
            ),
        },
        "decision": {
            "status": "selected_provider_diversity_requirement_should_be_reframed",
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": "define_selector_readiness_v3_proposal_diversity_criteria",
        },
        "proposed_readiness_v3_direction": {
            "replace_hard_requirement": "distinct_current_selected_provider_families",
            "with_requirements": [
                "diverse_strategy_proposal_families_present",
                "diverse_forced_or_compatible_conversion_positive_families_present",
                "stage7_held_out_challenge_preserved",
                "default_off_equivalence_required_before_any_sandbox",
                "guardrail_regression_zero_tolerance_for_protected_stack",
            ],
            "selected_provider_dominance_role": (
                "diagnostic blocker for promotion, but not necessarily a blocker for a default-off "
                "sandbox design review if proposal/forced contrast evidence is strong."
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
    interpretation = review["interpretation"]
    direction = review["proposed_readiness_v3_direction"]
    lines = [
        "# KRK Selected Provider Diversity Architecture Review v0",
        "",
        "This review interprets replay-free and sampled selected-provider evidence. "
        "It does not implement a selector or authorize a sandbox.",
        "",
        "## Evidence",
        "",
        f"- Replay-free selected provider families: `{evidence['replay_free_selected_provider_families']}`",
        f"- Replay-free distinct families: `{evidence['replay_free_distinct_families']}`",
        f"- Replay-free max dominance: `{evidence['replay_free_max_dominance']}`",
        f"- Sampled selected provider families: `{evidence['sampled_selected_provider_families']}`",
        f"- Sampled distinct families: `{evidence['sampled_distinct_families']}`",
        f"- Sampled max dominance: `{evidence['sampled_max_dominance']}`",
        f"- Contrast findings: `{evidence['contrast_findings']}`",
        "",
        "## Interpretation",
        "",
        f"- Current selected-provider diversity: `{interpretation['current_selected_provider_diversity_status']}`",
        f"- Contrast evidence: `{interpretation['contrast_evidence_status']}`",
        "",
        interpretation["reason"],
        "",
        interpretation["readiness_v2_issue"],
        "",
        "## Decision",
        "",
        f"- Status: `{review['decision']['status']}`",
        f"- Recommended next step: `{review['decision']['recommended_next_step']}`",
        "- Runtime arbiter and selector sandbox remain blocked.",
        "",
        "## Proposed Readiness v3 Direction",
        "",
        f"- Replace hard requirement: `{direction['replace_hard_requirement']}`",
        f"- Selected-provider dominance role: {direction['selected_provider_dominance_role']}",
        "",
    ]
    for requirement in direction["with_requirements"]:
        lines.append(f"- `{requirement}`")
    return "\n".join(lines) + "\n"


def main() -> None:
    review = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(review), encoding="utf-8")
    print(json.dumps(review["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
