#!/usr/bin/env python3
"""Write a runtime-review packet for exact candidate-generation trace enrichment.

The packet is review-only. It does not authorize implementation, selection,
scoring, routing, guardrails, promotion, or Stage 8 training.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OPTIONS = Path("reports/strategy_arbitration/krk_candidate_source_expansion_options_v0.json")
MANIFEST = Path("reports/strategy_arbitration/krk_candidate_source_gap_manifest_v0.json")
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_exact_trace_enrichment_runtime_review_packet_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_exact_trace_enrichment_runtime_review_packet_v0.md"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _runtime_false_block() -> dict[str, bool]:
    return {
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
    }


def _gap_cells(manifest: dict[str, Any]) -> dict[str, list[str]]:
    cells: dict[str, set[str]] = defaultdict(set)
    for record in manifest.get("gap_records") or []:
        if not isinstance(record, dict):
            continue
        if record.get("gap_type") != "policy_cell_covered_exact_missing":
            continue
        stage = str(record.get("source_stage") or "")
        family = str(record.get("candidate_strategy_family") or "")
        if stage in {"stage5", "stage6"} and family:
            cells[stage].add(family)
    return {stage: sorted(families) for stage, families in sorted(cells.items())}


def build_payload(
    options: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    options = options or _load(OPTIONS)
    manifest = manifest or _load(MANIFEST)
    osummary = options.get("summary") or {}
    msummary = manifest.get("summary") or {}
    decision = options.get("decision") or {}
    preferred = options.get("preferred_next_review")
    exact_missing = int(msummary.get("exact_missing_positive_capacity_count", 0) or 0)
    policy_cell_covered = int(msummary.get("policy_cell_covered_exact_missing_count", 0) or 0)
    policy_cell_missing = int(msummary.get("policy_cell_missing_count", 0) or 0)
    review_ready = (
        decision.get("status")
        == "candidate_source_expansion_options_review_complete_runtime_packet_required"
        and preferred == "exact_trace_enrichment_within_existing_policy_cells"
        and policy_cell_covered > 0
        and exact_missing > 0
    )
    candidate_cells = _gap_cells(manifest)
    return {
        "schema_version": "krk_exact_trace_enrichment_runtime_review_packet.v1",
        "causal_status": "non_causal_runtime_review_packet",
        **_runtime_false_block(),
        "source_artifacts": [str(OPTIONS), str(MANIFEST)],
        "evidence_summary": {
            "options_status": decision.get("status"),
            "preferred_next_review": preferred,
            "exact_missing_positive_capacity_count": exact_missing,
            "policy_cell_covered_exact_missing_count": policy_cell_covered,
            "policy_cell_missing_count": policy_cell_missing,
            "gap_count_by_stage": msummary.get("gap_count_by_stage"),
            "gap_count_by_family": msummary.get("gap_count_by_family"),
            "options_summary": osummary,
        },
        "approved_scope_if_later_authorized": {
            "sandbox_type": "default_off_exact_trace_enrichment",
            "allowed_effect": "emit_additional_exact_candidate_generation_observation_frames_only",
            "base_policy": "trace_stage_family_context",
            "candidate_generation_cells": candidate_cells,
            "protected_stages": ["stage5", "stage6"],
            "excluded_stages": ["stage4", "stage7", "stage8"],
            "stage4_status": "excluded_until_separate_review",
            "stage7_use": "held_out_challenge_only_no_training_rows",
            "direct_request": False,
            "score_delta": 0.0,
            "causal_status_for_frames": "candidate_generation_only",
            "capacity_label_semantics": "offline_capacity_not_runtime_ownership",
        },
        "explicitly_forbidden": [
            "selector_training",
            "provider_selection",
            "move_selection",
            "score_changes",
            "provider_suppression",
            "direct_provider_routing",
            "runtime_dtm_or_tablebase",
            "state_hash_or_exact_move_runtime_exception",
            "gameplay_topology_mutation",
            "stage4_runtime_scope_without_separate_review",
            "stage7_training_rows",
            "stage7_promotion",
            "stage8_training",
            "guardrails_before_default_off_equivalence_and_enabled_smoke",
        ],
        "implementation_requirements_if_explicitly_approved_later": [
            "new explicit opt-in flag or extension of existing refresh flag with visible mode",
            "default-off equivalence before enabled smoke",
            "bounded candidate count per decision",
            "zero selected move/provider delta",
            "zero score delta",
            "direct_request=false on every generated frame",
            "source_terms policy_cell and exact_enrichment_reason recorded on every frame",
            "capacity_evidence_kind recorded as positive_capacity negative_capacity or unknown_capacity",
            "Stage 7 rows excluded from training/readiness and marked held_out if ever traced diagnostically",
            "target smoke before guardrails",
            "separate selector review before generated frames can affect routing or scoring",
        ],
        "risk_register": [
            "capacity labels are still not ownership labels",
            "exact enrichment may increase trace volume without improving selection",
            "policy-cell-covered gaps may include alternative moves that are not safe owners",
            "Stage 4 gaps remain excluded and require separate review",
            "PlanCapsule or sequence candidates are still not covered by this packet",
        ],
        "decision": {
            "status": (
                "exact_trace_enrichment_runtime_review_ready"
                if review_ready
                else "exact_trace_enrichment_runtime_review_blocked"
            ),
            "runtime_review_ready": review_ready,
            "implementation_authorized_by_this_packet": False,
            "runtime_candidate_generation_allowed_by_this_packet": False,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "explicit_approval_required_for_default_off_exact_trace_enrichment_sandbox"
                if review_ready
                else "continue_non_causal_candidate_source_review"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    decision = payload["decision"]
    evidence = payload["evidence_summary"]
    scope = payload["approved_scope_if_later_authorized"]
    lines = [
        "# KRK Exact Trace Enrichment Runtime Review Packet v0",
        "",
        "This packet reviews a possible future default-off exact trace enrichment sandbox. It does not authorize implementation, selection, scoring, routing, guardrails, promotion, or Stage 8 training.",
        "",
        "## Decision",
        "",
        f"- status: `{decision['status']}`",
        f"- runtime_review_ready: `{decision['runtime_review_ready']}`",
        f"- implementation_authorized_by_this_packet: `{decision['implementation_authorized_by_this_packet']}`",
        f"- runtime_candidate_generation_allowed_by_this_packet: `{decision['runtime_candidate_generation_allowed_by_this_packet']}`",
        f"- selector_allowed: `{decision['selector_allowed']}`",
        f"- recommended_next_step: `{decision['recommended_next_step']}`",
        "",
        "## Evidence",
        "",
    ]
    for key, value in evidence.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Approved Scope If Later Authorized", ""])
    for key, value in scope.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Explicitly Forbidden", ""])
    lines.extend(f"- `{item}`" for item in payload["explicitly_forbidden"])
    lines.extend(["", "## Implementation Requirements If Explicitly Approved Later", ""])
    lines.extend(
        f"- `{item}`" for item in payload["implementation_requirements_if_explicitly_approved_later"]
    )
    lines.extend(["", "## Risk Register", ""])
    lines.extend(f"- `{item}`" for item in payload["risk_register"])
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
