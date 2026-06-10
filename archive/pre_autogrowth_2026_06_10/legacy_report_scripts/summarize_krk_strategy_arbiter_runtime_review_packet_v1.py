#!/usr/bin/env python3
"""Build the KRK strategy arbiter runtime review packet.

This packet is intentionally non-causal. It packages the evidence needed for an
architecture decision before any default-off runtime sandbox can be implemented.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTECTED_STATUS = Path("reports/krk_protected_stage_status.json")
READINESS_V3 = Path("reports/krk_selector_readiness_v3_plan.json")
DEFAULT_OFF_DESIGN = Path("reports/krk_strategy_arbiter_default_off_design_review_v1.json")
CONTRAST_PROBE = Path("reports/krk_strategy_owner_contrast_probe_v0.json")
OUT_JSON = Path("reports/krk_strategy_arbiter_runtime_review_packet_v1.json")
OUT_MD = Path("reports/krk_strategy_arbiter_runtime_review_packet_v1.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _decision_status(payload: dict[str, Any]) -> str | None:
    decision = payload.get("decision")
    if isinstance(decision, dict):
        status = decision.get("status")
        return status if isinstance(status, str) else None
    return None


def build_packet() -> dict[str, Any]:
    protected = _load_json(PROTECTED_STATUS)
    readiness = _load_json(READINESS_V3)
    design = _load_json(DEFAULT_OFF_DESIGN)
    contrast = _load_json(CONTRAST_PROBE)

    if protected.get("causal_status") != "non_causal_status_audit":
        raise ValueError("protected status must remain non-causal")
    if readiness.get("causal_status") != "non_causal_design_plan":
        raise ValueError("readiness v3 must remain non-causal")
    if design.get("causal_status") != "non_causal_design_review":
        raise ValueError("default-off design must remain non-causal")
    if contrast.get("causal_status") != "non_causal_probe":
        raise ValueError("contrast probe must remain non-causal")

    readiness_decision = readiness.get("decision") or {}
    design_decision = design.get("decision") or {}
    if readiness_decision.get("runtime_arbiter_allowed") is not False:
        raise ValueError("runtime arbiter is not allowed by readiness v3")
    if design_decision.get("implementation_allowed") is not False:
        raise ValueError("default-off design review must not allow implementation")

    stage_statuses = protected.get("stage_statuses") or []
    protected_components = [
        {
            "stage": item.get("stage"),
            "status": item.get("status"),
            "solved_under_current_architecture": item.get("solved_under_current_architecture"),
            "caveat": item.get("caveat"),
        }
        for item in stage_statuses
    ]
    contrast_metrics = contrast.get("metrics") or {}
    packet = {
        "schema_version": "krk_strategy_arbiter_runtime_review_packet.v1",
        "causal_status": "non_causal_review_packet",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "selector_sandbox_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(PROTECTED_STATUS), str(READINESS_V3), str(DEFAULT_OFF_DESIGN), str(CONTRAST_PROBE)],
        "current_stack_summary": {
            "profile": (protected.get("summary") or {}).get("current_architecture_profile"),
            "protected_components": protected_components,
            "stage7_status": protected.get("stage7_status"),
        },
        "evidence_summary": {
            "readiness_v3_status": _decision_status(readiness),
            "default_off_design_status": _decision_status(design),
            "contrast_probe_status": _decision_status(contrast),
            "conversion_positive_provider_families": sorted(
                family
                for family, stats in (contrast_metrics.get("training_provider_family_rates") or {}).items()
                if (stats or {}).get("positive", 0) > 0
            ),
            "training_positive_label_count": contrast_metrics.get("training_positive_label_count"),
            "training_negative_label_count": contrast_metrics.get("training_negative_label_count"),
            "stage7_heldout_row_count": contrast_metrics.get("heldout_row_count"),
        },
        "review_question": (
            "Should the project implement a default-off, traceable KRK strategy-arbiter sandbox "
            "using the v1 contract, or require additional non-causal evidence first?"
        ),
        "review_options": [
            {
                "option": "approve_default_off_sandbox_implementation",
                "allowed_next_step": "implement default-off trace-only or bounded-support sandbox according to the v1 contract",
                "required_conditions": [
                    "default-off equivalence tests are implemented before enabled tests",
                    "Stage7 remains held out from training and tuning",
                    "no runtime DTM/tablebase input",
                    "no gameplay topology mutation",
                    "every recommendation cites StrategyProposalFrame and provider metadata",
                ],
            },
            {
                "option": "request_more_non_causal_evidence",
                "allowed_next_step": "collect one bounded non-causal evidence slice identified by review",
                "required_conditions": [
                    "no runtime selector implementation",
                    "no Stage7 repair",
                    "no Stage8 training",
                    "evidence gap must be specific and bounded",
                ],
            },
            {
                "option": "reject_sandbox_path_for_now",
                "allowed_next_step": "return to curriculum or sequence-policy architecture planning without runtime selector work",
                "required_conditions": [
                    "record rejection reason",
                    "keep existing observability and evidence artifacts non-causal",
                ],
            },
        ],
        "non_negotiable_runtime_invariants": [
            "no hidden Python controller",
            "no runtime DTM/tablebase policy",
            "no gameplay-time topology mutation",
            "unpromoted StructuralCandidate/InternalTerminalSpec/PlanCapsuleSpec remain non-causal",
            "preserve M1-M4 plasticity/consolidation semantics",
            "validated Stage5/6 providers remain protected/frozen unless an explicit sandbox says otherwise",
        ],
        "implementation_blocked_until_review": True,
        "decision": {
            "status": "runtime_review_packet_ready",
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "implementation_allowed": False,
            "recommended_next_step": "external_architecture_review_decision",
        },
        "blocked_next_steps": [
            "implement_runtime_arbiter_without_review",
            "enable_selector_sandbox_without_review",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_packet(packet)
    return packet


def validate_packet(packet: dict[str, Any]) -> None:
    if packet.get("causal_status") != "non_causal_review_packet":
        raise ValueError("runtime review packet must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_arbiter_implemented",
        "selector_sandbox_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if packet.get(key) is not False:
            raise ValueError(f"{key} must be false")
    decision = packet.get("decision") or {}
    if decision.get("implementation_allowed") is not False:
        raise ValueError("implementation must remain blocked")
    if not packet.get("implementation_blocked_until_review"):
        raise ValueError("packet must block implementation until review")


def render_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# KRK Strategy Arbiter Runtime Review Packet v1",
        "",
        "This packet packages the current evidence for architecture review. It does not implement or authorize a runtime arbiter.",
        "",
        "## Review Question",
        "",
        packet["review_question"],
        "",
        "## Current Stack",
        "",
        f"- Profile: `{packet['current_stack_summary']['profile']}`",
        f"- Stage 7 status: `{packet['current_stack_summary']['stage7_status']}`",
        "",
    ]
    for component in packet["current_stack_summary"]["protected_components"]:
        lines.append(
            f"- `{component['stage']}` status=`{component['status']}` "
            f"solved=`{component['solved_under_current_architecture']}`"
        )
    lines.extend(["", "## Evidence Summary", ""])
    for key, value in packet["evidence_summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Review Options", ""])
    for option in packet["review_options"]:
        lines.append(f"### `{option['option']}`")
        lines.append("")
        lines.append(f"Allowed next step: `{option['allowed_next_step']}`")
        lines.append("")
        lines.append("Required conditions:")
        for condition in option["required_conditions"]:
            lines.append(f"- `{condition}`")
        lines.append("")
    lines.extend(["## Non-Negotiable Invariants", ""])
    for invariant in packet["non_negotiable_runtime_invariants"]:
        lines.append(f"- `{invariant}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{packet['decision']['status']}`",
            f"- Recommended next step: `{packet['decision']['recommended_next_step']}`",
            "- Implementation remains blocked until review.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    packet = build_packet()
    (ROOT / OUT_JSON).write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(packet), encoding="utf-8")
    print(json.dumps(packet["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
