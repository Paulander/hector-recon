#!/usr/bin/env python3
"""Compare default-off KRK support-adapter diagnostics.

This is an offline regression helper: it verifies that adding sandbox adapter
topology does not alter behavior while the adapter runtime flag is disabled.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


TOP_LEVEL_KEYS = (
    "total",
    "no_move",
    "improved",
    "flat",
    "worsened",
    "optimal",
    "avg_reward",
    "avg_oracle_reward",
    "playouts",
    "one_ply_status_counts",
    "conversion_status_counts",
    "semantic_alignment_status_counts",
    "shadow_candidate_count",
    "adapter_fire_count",
    "adapter_supported_provider_by_outcome",
    "adapter_supported_move_by_outcome",
    "plan_capsule_marker_count",
    "plan_capsule_marker_by_outcome",
    "plan_capsule_entry_count",
    "plan_capsule_exit_count",
    "plan_capsule_abort_count",
    "plan_capsule_expired_count",
    "plan_capsule_progress_confirmed_count",
    "plan_capsule_status_by_outcome",
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _packet_summary(payload: Mapping[str, Any]) -> list[tuple[Any, ...]]:
    summary: list[tuple[Any, ...]] = []
    for packet in payload.get("handoff_packets") or []:
        if not isinstance(packet, Mapping):
            continue
        evidence = packet.get("evidence_terms") or {}
        if not isinstance(evidence, Mapping):
            evidence = {}
        adapter = evidence.get("visible_role_provider_support_adapter")
        adapter_summary = None
        if isinstance(adapter, Mapping) and adapter:
            adapter_summary = (
                adapter.get("enabled"),
                adapter.get("adapter_id"),
                adapter.get("provider_id"),
                adapter.get("support_amount"),
                adapter.get("direct_request"),
            )
        summary.append(
            (
                packet.get("from_skill"),
                packet.get("phase"),
                packet.get("status"),
                packet.get("observed_outcome"),
                evidence.get("fen"),
                evidence.get("move"),
                evidence.get("successor_selected_skill"),
                evidence.get("playout_result"),
                evidence.get("semantic_alignment_status"),
                adapter_summary,
            )
        )
    return summary


def _shadow_summary(payload: Mapping[str, Any]) -> list[tuple[Any, ...]]:
    summary: list[tuple[Any, ...]] = []
    for candidate in payload.get("shadow_candidates") or []:
        if not isinstance(candidate, Mapping):
            continue
        summary.append(
            (
                candidate.get("trigger"),
                candidate.get("scope"),
                candidate.get("parent_skill"),
                candidate.get("target_skill"),
                candidate.get("observed_outcome"),
            )
        )
    return summary


def compare(a: Mapping[str, Any], b: Mapping[str, Any]) -> dict[str, Any]:
    differences: list[dict[str, Any]] = []
    for key in TOP_LEVEL_KEYS:
        if a.get(key) != b.get(key):
            differences.append({"field": key, "a": a.get(key), "b": b.get(key)})

    packets_a = _packet_summary(a)
    packets_b = _packet_summary(b)
    if packets_a != packets_b:
        differences.append(
            {
                "field": "handoff_packets",
                "a_count": len(packets_a),
                "b_count": len(packets_b),
                "first_difference": next(
                    (
                        {"index": idx, "a": x, "b": y}
                        for idx, (x, y) in enumerate(zip(packets_a, packets_b))
                        if x != y
                    ),
                    None,
                ),
            }
        )

    shadows_a = _shadow_summary(a)
    shadows_b = _shadow_summary(b)
    if shadows_a != shadows_b:
        differences.append(
            {
                "field": "shadow_candidates",
                "a_count": len(shadows_a),
                "b_count": len(shadows_b),
                "first_difference": next(
                    (
                        {"index": idx, "a": x, "b": y}
                        for idx, (x, y) in enumerate(zip(shadows_a, shadows_b))
                        if x != y
                    ),
                    None,
                ),
            }
        )

    return {
        "schema_version": "krk_default_off_equivalence.v1",
        "equivalent": not differences,
        "differences": differences,
        "packet_count": len(packets_a),
        "shadow_candidate_count": len(shadows_a),
        "adapter_fire_count": int(a.get("adapter_fire_count", 0) or 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a", required=True, type=Path)
    parser.add_argument("--b", required=True, type=Path)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    result = compare(_load(args.a), _load(args.b))
    content = json.dumps(result, indent=2) + "\n"
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(content, encoding="utf-8")
    print(content, end="")
    return 0 if result["equivalent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
