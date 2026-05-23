#!/usr/bin/env python3
"""Review cross-stage capacity evidence for KRK candidate-generation refresh."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MERGED_DATASET = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_dataset_v2_capacity_merged.json"
)
REFRESH_PROBE = Path(
    "reports/strategy_arbitration/krk_candidate_generation_refresh_probe_v2_after_labels.json"
)
TRAINING_REFRESH_DESIGN = Path(
    "reports/strategy_arbitration/krk_candidate_generation_training_refresh_design_v2.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_candidate_generation_cross_stage_capacity_review_v2.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_candidate_generation_cross_stage_capacity_review_v2.md"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _capacity_rows(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in dataset.get("rows") or []:
        if not isinstance(row, dict):
            continue
        if row.get("stage7_challenge_row"):
            continue
        if row.get("evidence_channel") != "validated_provider_capacity":
            continue
        if row.get("capacity_label") not in {"positive_capacity", "negative_capacity"}:
            continue
        rows.append(row)
    return rows


def _cell_key(row: dict[str, Any]) -> tuple[str, str]:
    return (
        str(row.get("source_stage") or "unknown"),
        str(row.get("candidate_strategy_family") or "unknown"),
    )


def _cell_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_cell: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_cell[_cell_key(row)].append(row)
    summary = {}
    for (stage, family), items in sorted(by_cell.items()):
        label_counts = Counter(row.get("capacity_label") for row in items)
        positive = label_counts.get("positive_capacity", 0)
        negative = label_counts.get("negative_capacity", 0)
        support = positive + negative
        if positive and negative:
            maturity = "mixed_capacity_cell"
        elif support < 2:
            maturity = "underpowered_cell"
        elif positive:
            maturity = "positive_only_cell"
        else:
            maturity = "negative_only_cell"
        summary[f"{stage}|{family}"] = {
            "source_stage": stage,
            "candidate_strategy_family": family,
            "support": support,
            "positive_capacity": positive,
            "negative_capacity": negative,
            "positive_rate": positive / support if support else 0.0,
            "maturity": maturity,
            "example_state_ids": sorted(
                {str(row.get("state_id") or "unknown") for row in items}
            )[:5],
        }
    return summary


def _stage_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_stage[str(row.get("source_stage") or "unknown")].append(row)
    summary = {}
    for stage, items in sorted(by_stage.items()):
        label_counts = Counter(row.get("capacity_label") for row in items)
        families = Counter(row.get("candidate_strategy_family") for row in items)
        summary[stage] = {
            "row_count": len(items),
            "positive_capacity": label_counts.get("positive_capacity", 0),
            "negative_capacity": label_counts.get("negative_capacity", 0),
            "families": dict(sorted(families.items())),
        }
    return summary


def _review_findings(
    cell_summary: dict[str, dict[str, Any]], probe: dict[str, Any]
) -> dict[str, Any]:
    positive_only = [key for key, cell in cell_summary.items() if cell["maturity"] == "positive_only_cell"]
    negative_only = [key for key, cell in cell_summary.items() if cell["maturity"] == "negative_only_cell"]
    mixed = [key for key, cell in cell_summary.items() if cell["maturity"] == "mixed_capacity_cell"]
    underpowered = [key for key, cell in cell_summary.items() if cell["maturity"] == "underpowered_cell"]
    leave_stage = (probe.get("summary") or {}).get("leave_stage_out_aggregate") or {}
    return {
        "positive_only_cells": positive_only,
        "negative_only_cells": negative_only,
        "mixed_capacity_cells": mixed,
        "underpowered_cells": underpowered,
        "leave_stage_out_positive_recall": leave_stage.get("positive_recall"),
        "leave_stage_out_negative_suppression": leave_stage.get("negative_suppression"),
        "stage_specific_interaction_likely": bool(positive_only or negative_only or mixed),
        "cross_stage_generalization_blocker": (
            "stage_family_capacity_is_not_uniform_across_protected_stages"
            if positive_only or negative_only or mixed
            else "capacity_evidence_underpowered"
        ),
    }


def build_payload(
    merged_dataset: dict[str, Any] | None = None,
    refresh_probe: dict[str, Any] | None = None,
    training_design: dict[str, Any] | None = None,
) -> dict[str, Any]:
    merged_dataset = merged_dataset or _load(MERGED_DATASET)
    refresh_probe = refresh_probe or _load(REFRESH_PROBE)
    training_design = training_design or _load(TRAINING_REFRESH_DESIGN)
    rows = _capacity_rows(merged_dataset)
    cells = _cell_summary(rows)
    stage_summary = _stage_summary(rows)
    findings = _review_findings(cells, refresh_probe)
    needs_manifest = (
        not (training_design.get("readiness_assessment") or {}).get(
            "cross_stage_generalization_supported", False
        )
        and len(rows) > 0
    )
    return {
        "schema_version": "krk_candidate_generation_cross_stage_capacity_review.v2",
        "causal_status": "non_causal_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            str(MERGED_DATASET),
            str(REFRESH_PROBE),
            str(TRAINING_REFRESH_DESIGN),
        ],
        "summary": {
            "capacity_row_count": len(rows),
            "stage_counts": dict(
                sorted(Counter(row.get("source_stage") for row in rows).items())
            ),
            "family_counts": dict(
                sorted(Counter(row.get("candidate_strategy_family") for row in rows).items())
            ),
            "stage_family_cell_count": len(cells),
            "stage7_readiness_training_row_count": sum(
                1
                for row in rows
                if row.get("stage7_challenge_row")
                and (
                    row.get("usable_for_selector_training_v2")
                    or row.get("usable_for_candidate_generation_training_v2")
                )
            ),
        },
        "stage_summary": stage_summary,
        "stage_family_cells": cells,
        "findings": findings,
        "recommended_manifest_scope": {
            "needed": needs_manifest,
            "scope": "protected_stage4_stage5_stage6_only",
            "stage7_jobs_allowed": False,
            "max_jobs_first_slice": 12,
            "selection_rule": (
                "prefer cells with single-class support, underpowered support, "
                "or large leave-stage-out error contribution"
            ),
            "label_semantics": "forced_provider_capacity_not_runtime_ownership",
        },
        "interpretation": {
            "candidate_generation_refresh_supported_in_sample": (
                (training_design.get("readiness_assessment") or {}).get(
                    "candidate_refresh_supported"
                )
            ),
            "candidate_generation_refresh_cross_stage_ready": (
                (training_design.get("readiness_assessment") or {}).get(
                    "cross_stage_generalization_supported"
                )
            ),
            "selector_supported": False,
            "capacity_labels_are_not_ownership_labels": True,
            "main_blocker": findings["cross_stage_generalization_blocker"],
        },
        "decision": {
            "status": (
                "cross_stage_capacity_review_recommends_stratified_capacity_manifest"
                if needs_manifest
                else "cross_stage_capacity_review_no_manifest_needed"
            ),
            "selector_allowed": False,
            "runtime_candidate_generator_refresh_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "build_targeted_cross_stage_capacity_manifest_non_causal"
                if needs_manifest
                else "candidate_generation_training_refresh_review"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    findings = payload["findings"]
    lines = [
        "# KRK Candidate-Generation Cross-Stage Capacity Review v2",
        "",
        "This review explains why the candidate-generation refresh signal is useful in-sample but weak under leave-stage-out evaluation.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- runtime_candidate_generator_refresh_allowed: `{payload['decision']['runtime_candidate_generator_refresh_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- capacity_row_count: {summary['capacity_row_count']}",
        f"- stage_counts: `{summary['stage_counts']}`",
        f"- family_counts: `{summary['family_counts']}`",
        f"- stage_family_cell_count: {summary['stage_family_cell_count']}",
        f"- stage7_readiness_training_row_count: {summary['stage7_readiness_training_row_count']}",
        "",
        "## Findings",
        "",
        f"- positive_only_cells: `{findings['positive_only_cells']}`",
        f"- negative_only_cells: `{findings['negative_only_cells']}`",
        f"- mixed_capacity_cells: `{findings['mixed_capacity_cells']}`",
        f"- underpowered_cells: `{findings['underpowered_cells']}`",
        f"- leave_stage_out_positive_recall: {findings['leave_stage_out_positive_recall']}",
        f"- leave_stage_out_negative_suppression: {findings['leave_stage_out_negative_suppression']}",
        f"- main_blocker: `{payload['interpretation']['main_blocker']}`",
        "",
        "## Stage-Family Cells",
        "",
    ]
    for key, cell in payload["stage_family_cells"].items():
        lines.append(
            f"- `{key}`: support={cell['support']} positive={cell['positive_capacity']} "
            f"negative={cell['negative_capacity']} maturity=`{cell['maturity']}`"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a candidate-generation capacity review only. Forced-provider capacity labels remain offline evidence, not selector labels or runtime ownership authority.",
        ]
    )
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
