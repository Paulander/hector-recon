#!/usr/bin/env python3
"""Assess whether Stage 7 post-box continuation is a useful M3 warmup target.

This is an offline Growth Governor helper. It does not run plasticity, mutate
weights, alter topology, or promote the candidate. Its purpose is to separate:

* activation/routing calibration, where M3 edge updates may be meaningful; from
* scripted-provider capacity gaps, where the provider fires but has no
  trainable internal move-selection parameters.
"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _node_meta(topology: dict[str, Any], node_id: str) -> dict[str, Any]:
    node = topology.get("nodes", {}).get(node_id)
    if not isinstance(node, dict):
        return {}
    meta = node.get("meta")
    return meta if isinstance(meta, dict) else {}


def _post_reply_packets(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        packet
        for packet in diagnostic.get("handoff_packets") or []
        if isinstance(packet, dict) and packet.get("phase") == "post_opponent_reply"
    ]


def _provider_nodes(topology: dict[str, Any], provider_skill_id: str, role_id: str) -> list[str]:
    nodes: list[str] = []
    for node_id, node in topology.get("nodes", {}).items():
        if not isinstance(node, dict):
            continue
        meta = node.get("meta") or {}
        if not isinstance(meta, dict):
            continue
        providers = {str(item) for item in meta.get("provider_skill_ids") or []}
        if meta.get("provider_skill_id"):
            providers.add(str(meta["provider_skill_id"]))
        if (
            str(meta.get("skill_id") or "") == provider_skill_id
            or provider_skill_id in providers
            or (
                str(meta.get("role_id") or "") == role_id
                and bool(meta.get("stage7_post_box_continuation_provider"))
            )
        ):
            nodes.append(str(node_id))
    return sorted(nodes)


def _trainable_internal_edges(topology: dict[str, Any], provider_nodes: set[str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for edge in topology.get("edges") or []:
        if not isinstance(edge, dict):
            continue
        edge_type = str(edge.get("type") or "")
        if edge_type not in {"SUB", "POR"}:
            continue
        src = str(edge.get("src") or "")
        dst = str(edge.get("dst") or "")
        if src not in provider_nodes or dst not in provider_nodes:
            continue
        src_meta = _node_meta(topology, src)
        dst_meta = _node_meta(topology, dst)
        if not (src_meta.get("can_m3_update") or dst_meta.get("can_m3_update")):
            continue
        result.append({
            "src": src,
            "dst": dst,
            "type": edge_type,
            "initial_weight": edge.get("weight", 1.0),
            "reason": "candidate_provider_internal",
        })
    return result


def _activation_edges(topology: dict[str, Any], provider_nodes: set[str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for edge in topology.get("edges") or []:
        if not isinstance(edge, dict):
            continue
        if str(edge.get("type") or "") != "SUB":
            continue
        src = str(edge.get("src") or "")
        dst = str(edge.get("dst") or "")
        if dst not in provider_nodes:
            continue
        result.append({
            "src": src,
            "dst": dst,
            "type": "SUB",
            "initial_weight": edge.get("weight", 1.0),
            "reason": "candidate_provider_activation_observe_only",
            "trainable_for_move_policy": False,
        })
    return result


def assess_stage7_post_box_m3_trainability(
    *,
    topology_path: Path,
    diagnostic_path: Path,
    target_role: str = "krk.post_box_shrink_continuation",
    target_provider: str = "krk.stage7_post_box_continuation",
) -> dict[str, Any]:
    start = time.perf_counter()
    topology = _load_json(topology_path)
    diagnostic = _load_json(diagnostic_path)
    provider_node_ids = set(_provider_nodes(topology, target_provider, target_role))
    internal_edges = _trainable_internal_edges(topology, provider_node_ids)
    activation_edges = _activation_edges(topology, provider_node_ids)

    counts: Counter[str] = Counter()
    sample_rows: list[dict[str, Any]] = []
    for packet in _post_reply_packets(diagnostic):
        evidence = packet.get("evidence_terms")
        if not isinstance(evidence, dict):
            continue
        selected = str(evidence.get("successor_selected_skill") or "")
        result = str(evidence.get("playout_result") or "")
        successor = evidence.get("successor_skills")
        provider_payload = {}
        if isinstance(successor, dict):
            maybe_payload = successor.get(target_provider)
            if isinstance(maybe_payload, dict):
                provider_payload = maybe_payload
        license_payload = provider_payload.get("visible_stage7_post_box_continuation_license")
        license_met = isinstance(license_payload, dict) and bool(license_payload)
        if license_met:
            counts["visible_license_met"] += 1
        if selected == target_provider:
            counts["candidate_provider_selected"] += 1
            counts[f"candidate_provider_selected_{result or 'unknown'}"] += 1
            if result == "mate":
                counts["candidate_provider_selected_mate"] += 1
            else:
                counts["candidate_provider_selected_failed"] += 1
        if license_met or selected == target_provider:
            sample_rows.append({
                "packet_id": packet.get("packet_id"),
                "fen": evidence.get("fen"),
                "post_reply_fen": evidence.get("post_reply_fen"),
                "post_reply_state_signature": evidence.get("post_reply_state_signature"),
                "selected_successor": selected,
                "playout_result": result,
                "licensed_move": license_payload.get("move") if isinstance(license_payload, dict) else None,
                "source_terms": license_payload.get("source_terms") if isinstance(license_payload, dict) else [],
            })

    selected_total = counts["candidate_provider_selected"]
    selected_failed = counts["candidate_provider_selected_failed"]
    if selected_total > 0 and selected_failed == selected_total and not internal_edges:
        probe_result = "scripted_provider_selected_but_not_trainable_for_move_policy"
        recommended_next_action = "train_or_compile_learned_candidate_provider_before_m3_warmup"
        labels = [
            "visible_provider_ownership_available",
            "candidate_selected_but_all_selected_outcomes_failed",
            "no_candidate_internal_m3_edges",
            "expressive_but_untrained_or_capacity_limited",
        ]
    elif selected_total > 0 and internal_edges:
        probe_result = "candidate_local_m3_warmup_feasible"
        recommended_next_action = "run_bounded_candidate_local_m3_warmup"
        labels = ["candidate_edges_have_eligibility"]
    elif counts["visible_license_met"] > 0:
        probe_result = "blocked_no_candidate_provider_selection"
        recommended_next_action = "fix_visible_owner_arbitration_before_m3"
        labels = ["license_met_provider_not_selected"]
    else:
        probe_result = "insufficient_target_evidence"
        recommended_next_action = "collect_more_targeted_diagnostics"
        labels = ["insufficient_evidence"]

    return {
        "schema_version": "stage7_post_box_m3_trainability_assessment.v1",
        "causal_status": "non_causal",
        "topology_source": str(topology_path),
        "diagnostic_source": str(diagnostic_path),
        "target_role": target_role,
        "target_provider": target_provider,
        "provider_nodes": sorted(provider_node_ids),
        "probe_result": probe_result,
        "recommended_next_action": recommended_next_action,
        "diagnostic_labels": labels,
        "counts": dict(counts),
        "trainable_internal_edge_count": len(internal_edges),
        "trainable_internal_edges": internal_edges,
        "activation_edge_count": len(activation_edges),
        "activation_edges_observe_only": activation_edges,
        "sample_rows": sample_rows[:20],
        "safety": {
            "m4_consolidation_enabled": False,
            "topology_mutation_enabled": False,
            "protected_provider_mutation_enabled": False,
            "dtm_or_tablebase_runtime_enabled": False,
            "hard_blocks": [
                "do_not_train_stage8",
                "do_not_promote_stage7",
                "do_not_enable_by_default",
                "do_not_make_candidates_causal",
            ],
        },
        "performance": {
            "wall_time_seconds": time.perf_counter() - start,
            "post_reply_packets": len(_post_reply_packets(diagnostic)),
        },
    }


def _write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Stage 7 Post-Box M3 Trainability Assessment",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Target role: `{payload['target_role']}`",
        f"Target provider: `{payload['target_provider']}`",
        f"Probe result: `{payload['probe_result']}`",
        f"Recommended next action: `{payload['recommended_next_action']}`",
        "",
        "## Counts",
        "",
    ]
    for key, value in sorted((payload.get("counts") or {}).items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend([
        f"- `trainable_internal_edge_count`: {payload.get('trainable_internal_edge_count')}",
        f"- `activation_edge_count`: {payload.get('activation_edge_count')}",
        "",
        "## Diagnostic Labels",
        "",
    ])
    for label in payload.get("diagnostic_labels") or []:
        lines.append(f"- `{label}`")
    lines.extend(["", "## Safety", ""])
    for key, value in sorted((payload.get("safety") or {}).items()):
        if key == "hard_blocks":
            continue
        lines.append(f"- `{key}`: `{value}`")
    for block in (payload.get("safety") or {}).get("hard_blocks") or []:
        lines.append(f"- hard block: `{block}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Assess Stage 7 post-box M3 trainability")
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--target-role", default="krk.post_box_shrink_continuation")
    parser.add_argument("--target-provider", default="krk.stage7_post_box_continuation")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = assess_stage7_post_box_m3_trainability(
        topology_path=args.topology,
        diagnostic_path=args.diagnostic,
        target_role=args.target_role,
        target_provider=args.target_provider,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        _write_markdown(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
