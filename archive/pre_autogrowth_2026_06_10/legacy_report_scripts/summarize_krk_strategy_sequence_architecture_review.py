#!/usr/bin/env python3
"""Summarize the next KRK strategy/sequence architecture direction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STAGE7_CLEAN_REVIEW = Path("reports/structural_candidates/stage7_clean_control_architecture_review_v0.json")
SELECTOR_REVIEW = Path("reports/krk_runtime_selector_readiness_review_v1.json")
NORMALIZED_REVIEW = Path("reports/krk_normalized_selector_probe_review_v1.json")
OUT_JSON = Path("reports/krk_strategy_sequence_architecture_review_v0.json")
OUT_MD = Path("reports/krk_strategy_sequence_architecture_review_v0.md")


def _load_optional(path: Path) -> dict[str, Any] | None:
    full = ROOT / path
    if not full.exists():
        return None
    payload = json.loads(full.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def build_review() -> dict[str, Any]:
    stage7 = _load_optional(STAGE7_CLEAN_REVIEW) or {}
    selector = _load_optional(SELECTOR_REVIEW)
    normalized = _load_optional(NORMALIZED_REVIEW)
    return {
        "schema_version": "krk_strategy_sequence_architecture_review.v0",
        "causal_status": "non_causal_architecture_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            str(STAGE7_CLEAN_REVIEW),
            str(SELECTOR_REVIEW),
            str(NORMALIZED_REVIEW),
        ],
        "input_status": {
            "stage7_clean_control_review_status": (stage7.get("decision") or {}).get("status"),
            "selector_review_present": selector is not None,
            "normalized_review_present": normalized is not None,
        },
        "core_interpretation": [
            "Validated Stage 5/6 providers remain protected enough to serve as base/overlay components.",
            "Stage 7 remains a held-out boundary/challenge, not a promotion target.",
            "Stage 7-only clean-control collection is not producing enough novel success controls to justify runtime work.",
            "Future evidence should separate strategy ownership from multi-step continuation policy instead of collapsing both into another local Stage 7 repair.",
        ],
        "next_architecture_objectives": [
            {
                "objective_id": "strategy_ownership_evidence",
                "question": "Which provider/strategy should own a decision state under shared terminal-space context?",
                "evidence_needed": [
                    "state-local StrategyProposalFrame rows",
                    "provider-local rank and normalized score",
                    "forced-provider h40 compatibility labels",
                    "protected Stage 4/5/6 coverage",
                    "Stage 7 held-out challenge rows only",
                ],
            },
            {
                "objective_id": "sequence_policy_evidence",
                "question": "When ownership is correct, can the selected provider or plan convert over multiple steps?",
                "evidence_needed": [
                    "clean successful continuation controls outside Stage 7-only repair artifacts",
                    "hard-negative contrast sets",
                    "closed-loop h40 outcomes",
                    "plan progress/exit/handoff labels",
                    "family-held-out evaluation",
                ],
            },
            {
                "objective_id": "curriculum_boundary_evidence",
                "question": "Should box_shrink remain a standalone owner or become local evidence / handoff trigger?",
                "evidence_needed": [
                    "near-edge phase-boundary examples",
                    "box-area relevance and edge-net/king-support context",
                    "successful handoff examples from validated providers",
                    "negative examples where box_shrink ownership stalls",
                ],
            },
        ],
        "forbidden_shortcuts": [
            "another Stage 7 local repair",
            "more unreviewed Stage 7 labels",
            "runtime selector implementation from current evidence",
            "support bonus escalation",
            "Stage 7 promotion",
            "Stage 8 training",
            "runtime DTM/tablebase policy",
        ],
        "recommended_next_slice": {
            "slice_id": "krk_strategy_sequence_evidence_plan_v0",
            "description": "Design a bounded non-causal evidence plan that collects diverse protected state-local ownership labels and sequence-policy controls while keeping Stage 7 held out.",
            "runtime_behavior_allowed": False,
        },
        "decision": {
            "status": "broader_krk_strategy_sequence_review_ready",
            "recommended_next_step": "define_krk_strategy_sequence_evidence_plan_v0",
            "runtime_work_allowed": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Strategy / Sequence Architecture Review v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "This review closes the Stage 7 clean-control loop and moves the next work back to broader KRK architecture evidence.",
        "",
        "## Core Interpretation",
        "",
    ]
    for item in payload["core_interpretation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Next Architecture Objectives", ""])
    for item in payload["next_architecture_objectives"]:
        lines.append(f"- `{item['objective_id']}`: {item['question']}")
    lines.extend(["", "## Forbidden Shortcuts", ""])
    for item in payload["forbidden_shortcuts"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Recommended Next Slice",
            "",
            f"- `{payload['recommended_next_slice']['slice_id']}`: {payload['recommended_next_slice']['description']}",
            "",
            f"Recommended next step: `{payload['decision']['recommended_next_step']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
