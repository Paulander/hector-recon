#!/usr/bin/env python3
"""Compile non-default gated role-provider support adapters into a sandbox topology."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _safe_id(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_")


def _edge_exists(topology: dict[str, Any], src: str, dst: str, edge_type: str) -> bool:
    for edge in topology.get("edges", []) or []:
        if not isinstance(edge, dict):
            continue
        if edge.get("src") == src and edge.get("dst") == dst and edge.get("type") == edge_type:
            return True
    return False


def _add_edge(topology: dict[str, Any], src: str, dst: str, edge_type: str, weight: float = 1.0, **meta) -> None:
    if _edge_exists(topology, src, dst, edge_type):
        return
    edge = {"src": src, "dst": dst, "type": edge_type, "weight": weight}
    edge.update(meta)
    topology.setdefault("edges", []).append(edge)


def compile_support_sandbox(
    *,
    topology_path: Path,
    proposal_path: Path,
    output_path: Path,
    enable_explicit_support_by_default: bool = False,
    support_weight: float | None = None,
) -> dict[str, Any]:
    topology = _load_json(topology_path)
    proposal = _load_json(proposal_path)
    topology.setdefault("nodes", {})
    topology.setdefault("edges", [])
    topology.setdefault("meta", {})
    hub_id = "krk_successor_affordance_hub"
    if hub_id not in topology["nodes"]:
        raise ValueError(f"topology missing {hub_id}")

    added_adapters = []
    for relation in proposal.get("proposed_support_relations") or []:
        if not isinstance(relation, dict):
            continue
        if not relation.get("requires_support_adapter"):
            continue
        role_id = str(proposal.get("target_role") or "")
        provider_id = str(proposal.get("target_provider") or "")
        source_role_script = str(relation.get("source_role_script") or "")
        target_provider_skill = str(relation.get("target_provider_skill") or "")
        if not role_id or not provider_id or source_role_script not in topology["nodes"]:
            continue
        relation_weight = (
            float(support_weight)
            if support_weight is not None
            else float(relation.get("initial_weight", 0.0) or 0.0)
        )
        adapter_id = f"script.krk.support.{_safe_id(role_id)}_to_{_safe_id(provider_id)}"
        marker_id = f"terminal.krk.support.{_safe_id(role_id)}_to_{_safe_id(provider_id)}_marker"
        topology["nodes"][adapter_id] = {
            "id": adapter_id,
            "type": "SCRIPT",
            "factory": "recon_lite_chess.krk_baseline_nodes:create_krk_role_provider_support_adapter",
            "meta": {
                "role_provider_support_adapter": True,
                "role_id": role_id,
                "provider_skill_id": provider_id,
                "source_role_script": source_role_script,
                "target_provider_skill": target_provider_skill,
                "support_marker_id": marker_id,
                "support_weight": relation_weight,
                "causal_status": "sandbox_opt_in",
                "enabled_by_default": bool(enable_explicit_support_by_default),
                "description": "Gated explicit role-provider support adapter; does not directly request provider skill.",
            },
        }
        topology["nodes"][marker_id] = {
            "id": marker_id,
            "type": "TERMINAL",
            "factory": "recon_lite_chess.krk_baseline_nodes:create_krk_affordance_marker_terminal",
            "meta": {
                "role_provider_support_marker": True,
                "role_id": role_id,
                "provider_skill_id": provider_id,
                "causal_status": "sandbox_opt_in",
                "description": "Marker terminal for explicit role-provider support adapter.",
            },
        }
        _add_edge(topology, hub_id, adapter_id, "SUB", 1.0, consolidate=False)
        _add_edge(topology, adapter_id, hub_id, "SUR", 1.0, consolidate=False)
        _add_edge(
            topology,
            adapter_id,
            marker_id,
            "SUB",
            relation_weight,
            consolidate=False,
            trainable=True,
            edge_kind="visible_role_provider_support_weight",
        )
        _add_edge(topology, marker_id, adapter_id, "SUR", 1.0, consolidate=False)
        added_adapters.append(adapter_id)

    topology["meta"]["role_provider_support_sandbox"] = {
        "schema_version": "role_provider_support_sandbox.v1",
        "proposal_source": str(proposal_path),
        "enabled_by_default": bool(enable_explicit_support_by_default),
        "adapter_count": len(added_adapters),
        "adapters": added_adapters,
        "support_weight_override": support_weight,
        "causal_status": "sandbox_opt_in",
        "compile_strategy": proposal.get("sandbox_compile_strategy"),
    }
    if enable_explicit_support_by_default:
        root = topology.get("nodes", {}).get("krk_entry", {})
        if isinstance(root, dict):
            root.setdefault("meta", {})["explicit_role_provider_support_enabled"] = True

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(topology, indent=2) + "\n", encoding="utf-8")
    return topology


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile role-provider support adapters into sandbox topology")
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--enable-explicit-support-by-default", action="store_true")
    parser.add_argument("--support-weight", type=float, default=None,
                        help="Override proposed initial support weight for adapter smoke tests")
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    topology = compile_support_sandbox(
        topology_path=args.topology,
        proposal_path=args.proposal,
        output_path=args.output,
        enable_explicit_support_by_default=args.enable_explicit_support_by_default,
        support_weight=args.support_weight,
    )
    summary = topology.get("meta", {}).get("role_provider_support_sandbox", {})
    if not args.no_json_stdout:
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
