#!/usr/bin/env python3
"""Compile a default-off visible Plan Capsule sandbox marker into topology."""

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


def compile_plan_capsule_sandbox(
    *,
    topology_path: Path,
    candidate_path: Path,
    output_path: Path,
    enable_by_default: bool = False,
) -> dict[str, Any]:
    topology = _load_json(topology_path)
    candidate = _load_json(candidate_path)
    capsule = candidate.get("plan_capsule") or {}
    if not isinstance(capsule, dict) or capsule.get("schema_version") != "plan_capsule_spec.v1":
        raise ValueError("candidate must contain a plan_capsule_spec.v1 payload")
    topology.setdefault("nodes", {})
    topology.setdefault("edges", [])
    topology.setdefault("meta", {})
    hub_id = "krk_successor_affordance_hub" if "krk_successor_affordance_hub" in topology["nodes"] else "krk_hub"
    if hub_id not in topology["nodes"]:
        raise ValueError("topology missing krk_successor_affordance_hub/krk_hub")

    capsule_id = str(capsule["capsule_id"])
    safe_id = capsule_id.replace(".", "_")
    node_id = f"script.{safe_id}"
    marker_id = f"terminal.{safe_id}.marker"
    topology["nodes"][node_id] = {
        "id": node_id,
        "type": "SCRIPT",
        "factory": "recon_lite_chess.krk_baseline_nodes:create_krk_plan_capsule_marker",
        "meta": {
            "plan_capsule_marker": True,
            "capsule_id": capsule_id,
            "source_candidate_id": capsule.get("source_candidate_id"),
            "source_monitor_script": capsule.get("source_monitor_script"),
            "source_terms": list(capsule.get("source_terms") or []),
            "entry_terms": list(capsule.get("entry_terms") or []),
            "progress_terms": list(capsule.get("progress_terms") or []),
            "exit_terms": list(capsule.get("exit_terms") or []),
            "abort_terms": list(capsule.get("abort_terms") or []),
            "ttl_white_moves": int(capsule.get("ttl_white_moves") or 0),
            "owned_roles": list(capsule.get("owned_roles") or []),
            "owned_providers": list(capsule.get("owned_providers") or []),
            "handoff_exports": dict(capsule.get("handoff_exports") or {}),
            "direct_request": False,
            "causal_status": "sandbox_opt_in_non_requesting",
            "enabled_by_default": bool(enable_by_default),
            "description": (
                "Default-off Plan Capsule sandbox marker. It records visible "
                "entry/progress/exit/abort evidence and does not request "
                "providers or alter move scores."
            ),
        },
    }
    topology["nodes"][marker_id] = {
        "id": marker_id,
        "type": "TERMINAL",
        "factory": "recon_lite_chess.krk_baseline_nodes:create_krk_affordance_marker_terminal",
        "meta": {
            "plan_capsule_marker_terminal": True,
            "capsule_id": capsule_id,
            "causal_status": "sandbox_opt_in_non_requesting",
            "direct_request": False,
        },
    }
    _add_edge(topology, hub_id, node_id, "SUB", 1.0, consolidate=False)
    _add_edge(topology, node_id, hub_id, "SUR", 1.0, consolidate=False)
    _add_edge(topology, node_id, marker_id, "SUB", 1.0, consolidate=False)
    _add_edge(topology, marker_id, node_id, "SUR", 1.0, consolidate=False)

    topology["meta"]["plan_capsule_sandbox"] = {
        "schema_version": "plan_capsule_sandbox.v1",
        "candidate_source": str(candidate_path),
        "capsule_id": capsule_id,
        "node_id": node_id,
        "marker_id": marker_id,
        "enabled_by_default": bool(enable_by_default),
        "causal_status": "sandbox_opt_in_non_requesting",
        "direct_request": False,
        "runtime_behavior_change_when_disabled": False,
    }
    if enable_by_default:
        root = topology.get("nodes", {}).get("krk_entry", {})
        if isinstance(root, dict):
            root.setdefault("meta", {})["plan_capsule_sandbox_enabled"] = True

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(topology, indent=2) + "\n", encoding="utf-8")
    return topology


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile default-off Plan Capsule sandbox marker into topology")
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--enable-by-default", action="store_true")
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    topology = compile_plan_capsule_sandbox(
        topology_path=args.topology,
        candidate_path=args.candidate,
        output_path=args.output,
        enable_by_default=args.enable_by_default,
    )
    summary = topology.get("meta", {}).get("plan_capsule_sandbox", {})
    if not args.no_json_stdout:
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
