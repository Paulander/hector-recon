#!/usr/bin/env python3
"""Plan a bounded candidate-local M3 warmup scope.

This is an offline safety/planning tool. It reads a topology plus a Growth
Governor evaluation plan and emits the exact edge whitelist that a later M3
warmup probe may use. It does not run plasticity, mutate weights, alter
routing, update topology, or promote candidates.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_TRAINING_LIMITS = {
    "schema_version": "candidate_local_m3_limits.v0",
    "max_warmup_episodes": 20,
    "max_delta_episode": 0.25,
    "eta_eff": 0.02,
    "lambda_decay": 0.8,
    "m4_consolidation_enabled": False,
    "topology_mutation_enabled": False,
    "protected_provider_mutation_enabled": False,
}


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


def _edge_key(edge: dict[str, Any]) -> tuple[str, str, str]:
    return (str(edge.get("src")), str(edge.get("dst")), str(edge.get("type")))


def _role_plan(growth_plan: dict[str, Any], target_role: str) -> dict[str, Any]:
    for item in growth_plan.get("role_plans") or []:
        if isinstance(item, dict) and item.get("candidate_role") == target_role:
            return item
    raise ValueError(f"role {target_role!r} not found in growth plan")


def _role_nodes(topology: dict[str, Any], target_role: str) -> list[str]:
    result = []
    for node_id, node in topology.get("nodes", {}).items():
        if not isinstance(node, dict):
            continue
        meta = node.get("meta") or {}
        if isinstance(meta, dict) and meta.get("role_id") == target_role:
            result.append(str(node_id))
    return sorted(result)


def _provider_nodes(topology: dict[str, Any], provider_skill_ids: set[str]) -> dict[str, list[str]]:
    by_provider: dict[str, list[str]] = defaultdict(list)
    for node_id, node in topology.get("nodes", {}).items():
        if not isinstance(node, dict):
            continue
        meta = node.get("meta") or {}
        if not isinstance(meta, dict):
            continue
        skill_id = meta.get("skill_id")
        if skill_id in provider_skill_ids:
            by_provider[str(skill_id)].append(str(node_id))
    return {key: sorted(value) for key, value in by_provider.items()}


def _subtree_from_edges(root_ids: set[str], edges: list[dict[str, Any]]) -> set[str]:
    """Return nodes reachable from roots by forward SUB/POR provider edges."""
    children_by_src: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        if edge.get("type") not in {"SUB", "POR"}:
            continue
        children_by_src[str(edge.get("src"))].append(str(edge.get("dst")))

    seen = set(root_ids)
    frontier = list(root_ids)
    while frontier:
        current = frontier.pop()
        for child in children_by_src.get(current, []):
            if child not in seen:
                seen.add(child)
                frontier.append(child)
    return seen


def _is_frozen(meta: dict[str, Any]) -> bool:
    return bool(meta.get("frozen_provider") or meta.get("provider_maturity") == "foundation_frozen")


def _can_m3_update(meta: dict[str, Any]) -> bool:
    if _is_frozen(meta):
        return False
    if meta.get("can_m3_update") is None:
        return bool(meta.get("overlay_provider"))
    return bool(meta.get("can_m3_update"))


def plan_candidate_local_m3_warmup(
    *,
    topology_path: Path,
    growth_plan_path: Path,
    target_role: str = "krk.box_shrink_to_drive_repair",
) -> dict[str, Any]:
    topology = _load_json(topology_path)
    growth_plan = _load_json(growth_plan_path)
    plan = _role_plan(growth_plan, target_role)
    role_node_ids = _role_nodes(topology, target_role)
    if not role_node_ids:
        raise ValueError(f"no topology node exposes role_id={target_role!r}")

    provider_skill_ids: set[str] = set()
    for node_id in role_node_ids:
        for provider in _node_meta(topology, node_id).get("provider_skill_ids") or []:
            provider_skill_ids.add(str(provider))
    if not provider_skill_ids:
        raise ValueError(f"role {target_role!r} does not expose provider_skill_ids")

    edges = [edge for edge in topology.get("edges", []) if isinstance(edge, dict)]
    provider_nodes = _provider_nodes(topology, provider_skill_ids)
    provider_root_ids = {
        node_id
        for ids in provider_nodes.values()
        for node_id in ids
        if node_id.startswith("skill.krk.")
    }
    provider_subtree = _subtree_from_edges(provider_root_ids, edges)

    frozen_provider_versions = set()
    protected_nodes = set()
    overlay_nodes_missing_maturity = []
    for node_id, node in topology.get("nodes", {}).items():
        if not isinstance(node, dict):
            continue
        meta = node.get("meta") or {}
        if not isinstance(meta, dict):
            continue
        if _is_frozen(meta):
            protected_nodes.add(str(node_id))
            if meta.get("provider_version"):
                frozen_provider_versions.add(str(meta["provider_version"]))
        if meta.get("overlay_provider") and (
            meta.get("provider_maturity") is None
            or meta.get("plasticity_scope") is None
            or meta.get("can_m3_update") is None
        ):
            overlay_nodes_missing_maturity.append(str(node_id))

    eligible_edges: list[dict[str, Any]] = []
    excluded_counts: Counter[str] = Counter()
    for edge in edges:
        src, dst, ltype = _edge_key(edge)
        if ltype not in {"SUB", "POR"}:
            excluded_counts["non_trainable_link_type"] += 1
            continue
        if src in protected_nodes or dst in protected_nodes:
            excluded_counts["protected_frozen_provider"] += 1
            continue
        if src not in provider_subtree or dst not in provider_subtree:
            excluded_counts["outside_candidate_provider_subtree"] += 1
            continue
        src_meta = _node_meta(topology, src)
        dst_meta = _node_meta(topology, dst)
        if not (_can_m3_update(src_meta) or _can_m3_update(dst_meta)):
            excluded_counts["not_m3_update_enabled"] += 1
            continue
        reason = "candidate_provider_internal"
        if src in provider_root_ids:
            reason = "candidate_provider_leg_selection"
        elif ltype == "POR":
            reason = "candidate_provider_triplet_temporal"
        eligible_edges.append({
            "src": src,
            "dst": dst,
            "type": ltype,
            "reason": reason,
            "initial_weight": edge.get("weight", 1.0),
        })

    role_support_edges = [
        {
            "src": src,
            "dst": dst,
            "type": ltype,
            "reason": "visible_role_activation_support_observe_only",
            "trainable": False,
        }
        for edge in edges
        for src, dst, ltype in [_edge_key(edge)]
        if ltype == "SUB" and (src in role_node_ids or dst in role_node_ids)
    ]

    return {
        "schema_version": "candidate_local_m3_warmup_plan.v1",
        "causal_status": "non_causal",
        "topology_source": str(topology_path),
        "growth_plan_source": str(growth_plan_path),
        "target_role": target_role,
        "target_providers": sorted(provider_skill_ids),
        "growth_governor_decision": plan.get("governor_decision"),
        "growth_governor_phase": plan.get("evaluation_phase"),
        "warmup_scope": "candidate_local_provider_only",
        "role_nodes": role_node_ids,
        "provider_nodes": provider_nodes,
        "provider_subtree_node_count": len(provider_subtree),
        "eligible_edge_whitelist": eligible_edges,
        "eligible_edge_count": len(eligible_edges),
        "observe_only_role_support_edges": role_support_edges,
        "excluded_edge_counts": dict(excluded_counts),
        "protected_provider_versions": sorted(frozen_provider_versions),
        "metadata_warnings": {
            "overlay_nodes_missing_maturity_fields": sorted(overlay_nodes_missing_maturity),
            "requires_topology_regeneration": bool(overlay_nodes_missing_maturity),
        },
        "training_limits": DEFAULT_TRAINING_LIMITS,
        "guardrails": plan.get("guardrails") or [],
        "hard_blocks": growth_plan.get("hard_blocks") or [],
        "next_probe_command_template": [
            "run_candidate_local_m3_warmup_probe",
            "--edge-whitelist",
            "<this_artifact>.eligible_edge_whitelist",
            "--freeze-provider-versions",
            ",".join(sorted(frozen_provider_versions)) or "<none>",
            "--m4-consolidation",
            "disabled",
            "--topology-mutation",
            "disabled",
        ],
    }


def _write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Candidate-Local M3 Warmup Plan",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Target role: `{payload['target_role']}`",
        f"Target providers: `{', '.join(payload['target_providers'])}`",
        f"Governor decision: `{payload['growth_governor_decision']}`",
        f"Governor phase: `{payload['growth_governor_phase']}`",
        f"Eligible M3 edges: `{payload['eligible_edge_count']}`",
        "",
        "## Safety",
        "",
    ]
    for item in payload.get("hard_blocks") or []:
        lines.append(f"- `{item}`")
    limits = payload.get("training_limits") or {}
    lines.extend([
        f"- M4 consolidation enabled: `{limits.get('m4_consolidation_enabled')}`",
        f"- Topology mutation enabled: `{limits.get('topology_mutation_enabled')}`",
        f"- Protected provider mutation enabled: `{limits.get('protected_provider_mutation_enabled')}`",
        "",
        "## Eligible Edge Reasons",
        "",
    ])
    counts = Counter(edge.get("reason") for edge in payload.get("eligible_edge_whitelist") or [])
    for reason, count in sorted(counts.items()):
        lines.append(f"- `{reason}`: {count}")
    lines.extend(["", "## Excluded Edge Counts", ""])
    for reason, count in sorted((payload.get("excluded_edge_counts") or {}).items()):
        lines.append(f"- `{reason}`: {count}")
    warnings = payload.get("metadata_warnings") or {}
    if warnings.get("requires_topology_regeneration"):
        lines.extend([
            "",
            "## Metadata Warning",
            "",
            "The topology has overlay nodes missing maturity/plasticity fields. Regenerate the sandbox topology before running an actual warmup probe.",
        ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan candidate-local M3 warmup edge scope")
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--growth-plan", type=Path, required=True)
    parser.add_argument("--target-role", default="krk.box_shrink_to_drive_repair")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = plan_candidate_local_m3_warmup(
        topology_path=args.topology,
        growth_plan_path=args.growth_plan,
        target_role=args.target_role,
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
