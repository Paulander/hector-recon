#!/usr/bin/env python3
"""Write review packet for selector-objective benchmark v2.

The packet is deliberately non-causal. A passing visible heuristic on the seed
set can only justify independent protected validation before any runtime review.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = Path("reports/strategy_arbitration/krk_selector_objective_benchmark_v2.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_selector_objective_benchmark_review_packet_v2.json")
OUT_MD = Path("reports/strategy_arbitration/krk_selector_objective_benchmark_review_packet_v2.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected object: {path}")
    return payload


def build_payload(benchmark: dict[str, Any] | None = None) -> dict[str, Any]:
    benchmark = benchmark or _load(BENCHMARK)
    summary = benchmark.get("summary") or {}
    best_model_id = summary.get("best_runtime_model")
    best_model = (benchmark.get("results") or {}).get(best_model_id or "", {})
    passing_count = int(summary.get("runtime_threshold_passing_model_count") or 0)
    review_ready = benchmark.get("decision", {}).get("status") == (
        "selector_objective_benchmark_v2_runtime_feature_review_ready"
    )
    return {
        "schema_version": "krk_selector_objective_benchmark_review_packet.v2",
        "source_artifacts": [str(BENCHMARK)],
        "decision": {
            "status": (
                "selector_objective_benchmark_review_ready_for_independent_validation"
                if review_ready
                else "selector_objective_benchmark_review_blocked"
            ),
            "runtime_review_ready": False,
            "independent_validation_review_ready": review_ready,
            "implementation_authorized_by_this_packet": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "run_bounded_independent_protected_selector_objective_validation"
                if review_ready
                else "keep_selector_blocked_or_collect_more_visible_features"
            ),
        },
        "benchmark_summary": summary,
        "best_visible_model": {
            "model_id": best_model_id,
            "model_kind": best_model.get("model_kind"),
            "accuracy": best_model.get("accuracy"),
            "switch_precision": best_model.get("switch_precision"),
            "switch_recall": best_model.get("switch_recall"),
            "preserve_recall": best_model.get("preserve_recall"),
            "abstain_recall": best_model.get("abstain_recall"),
            "runtime_feature_eligible": best_model.get("runtime_feature_eligible"),
            "notes": best_model.get("notes"),
        },
        "acceptance_for_independent_validation": {
            "protected_stages": ["stage4", "stage5", "stage6"],
            "excluded_stages": ["stage7", "stage8"],
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
            "max_new_rows_first_slice": 12,
            "target_metrics": {
                "switch_precision_min": 0.70,
                "switch_recall_min": 0.70,
                "preserve_recall_min": 0.80,
                "abstain_recall_min": 0.60,
            },
        },
        "risks": [
            "best visible heuristic may be overfit to the current 18-row seed",
            "capacity evidence remains separate from ownership labels",
            "passing benchmark does not authorize runtime selector behavior",
            "Stage 7 remains held out and must not enter readiness training rows",
        ],
        "explicitly_forbidden": [
            "runtime_selector",
            "selector_training",
            "score_changes",
            "provider_suppression",
            "direct_provider_routing",
            "capacity_labels_as_ownership_labels",
            "stage7_training_or_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
        "review_observations": {
            "passing_runtime_feature_model_count": passing_count,
            "independent_validation_required": review_ready,
            "runtime_selector_supported": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    decision = payload["decision"]
    best = payload["best_visible_model"]
    lines = [
        "# KRK Selector Objective Benchmark Review Packet v2",
        "",
        "This packet reviews the non-causal selector-objective benchmark v2. It does not authorize runtime selector implementation.",
        "",
        "## Decision",
        "",
    ]
    for key, value in decision.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Best Visible Model",
            "",
        ]
    )
    for key, value in best.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Independent Validation Acceptance",
            "",
        ]
    )
    for key, value in payload["acceptance_for_independent_validation"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Risks", ""])
    for item in payload["risks"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Explicitly Forbidden", ""])
    for item in payload["explicitly_forbidden"]:
        lines.append(f"- `{item}`")
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
