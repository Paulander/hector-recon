#!/usr/bin/env python3
"""Deterministic engineering canary for frame-aware mature-child handover.

This is not a behavioral experiment and uses no fresh or KRK data. The final
argmax/actuator bus is intentionally host-executed and reads graph terminal
activations only.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from recon_lite import (
    ChildResponse,
    DreamStateLeakError,
    FormalReConEngine,
    FrameContext,
    FrameKind,
    Graph,
    Node,
    NodeState,
    NodeType,
    VirtualFrameExecutor,
    child_response_terminal,
    prediction_surprise_terminal,
)

ACTIONS = ("advance", "stall")


def grounded(value: float, uncertainty: float = 0.1) -> ChildResponse:
    return ChildResponse(
        child_id="grounded_mature_child",
        confirmed=True,
        expected_value=value,
        uncertainty=uncertainty,
        grounded=True,
        grounding_source="observed_outcome_history",
    )


def external_successor_terminal(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
    frame = env.get("__frame_context__")
    successor = float(env.get("successor_sensor", 0.0))
    node.activation.value = successor
    return True, isinstance(frame, FrameContext) and successor > 0.0


def build_handover_graph(*, disconnected_decoy: bool = False) -> Graph:
    graph = Graph()
    graph.add_node(Node(
        "parent",
        NodeType.SCRIPT,
        meta={"role": "frame_aware_parent_selector"},
    ))
    for action in ACTIONS:
        leg = f"leg_{action}"
        graph.add_node(Node(
            leg,
            NodeType.SCRIPT,
            meta={"role": "virtual_action_leg", "action_id": action, "confirm_policy": "and"},
        ))
        graph.add_node(Node(
            f"external_{action}",
            NodeType.TERMINAL,
            predicate=external_successor_terminal,
            meta={"role": "external_successor_sensor", "action_id": action},
        ))
        graph.add_node(Node(
            f"child_{action}",
            NodeType.TERMINAL,
            predicate=child_response_terminal,
            meta={"role": "CHILD_RESPONSE", "action_id": action},
        ))
        graph.add_hierarchy_pair("parent", leg)
        graph.add_hierarchy_pair(leg, f"external_{action}")
        graph.add_hierarchy_pair(leg, f"child_{action}")
    if disconnected_decoy:
        def decoy(node: Node, _env: dict[str, Any]) -> tuple[bool, bool]:
            node.activation.value = 1.0
            return True, True
        graph.add_node(Node(
            "disconnected_internal_terminal",
            NodeType.TERMINAL,
            predicate=decoy,
            meta={"role": "CHILD_RESPONSE_CONTROL"},
        ))
    graph.validate_formal_pairs()
    return graph


def select_and_actuate(*, shuffled: bool = False, disconnected: bool = False) -> dict[str, Any]:
    graph = build_handover_graph(disconnected_decoy=disconnected)
    graph_before = deepcopy(graph.to_snapshot())
    protected = {
        "weights": {"parent": 0.25},
        "lifecycle": {"parent": "trial", "child": "mature"},
        "reservoir": ["observed-1", "observed-2"],
        "maturity": {"child": True},
        "reward": 0.0,
    }
    protected_before = deepcopy(protected)
    responses = {"advance": grounded(0.9), "stall": grounded(0.2)}
    if shuffled:
        responses = {"advance": responses["stall"], "stall": responses["advance"]}

    evaluations = {}
    scores = {}
    executor = VirtualFrameExecutor()
    for action in ACTIONS:
        frame = FrameContext(
            frame_id=f"virtual-successor-{action}",
            kind=FrameKind.VIRTUAL,
            values={"successor_sensor": 1.0, "child_response": responses[action]},
            parent_frame_id="real-start",
            hypothetical_action=action,
        )
        result = executor.evaluate(
            graph, f"leg_{action}", frame, protected_state=protected
        )
        scores[action] = result.activations[f"child_{action}"]
        evaluations[action] = {
            "root_state": result.root_state.name,
            "child_response": responses[action].to_dict(),
            "child_activation": scores[action],
            "external_activation": result.activations[f"external_{action}"],
            "effect_attempts": list(result.effect_attempts),
        }
        if disconnected:
            evaluations[action]["disconnected_activation"] = result.activations[
                "disconnected_internal_terminal"
            ]

    # Generic final actuator bus: it consumes emitted graph strength and action
    # identity, never hidden child fields or successor semantics.
    selected = min(ACTIONS, key=lambda action: (-scores[action], action))
    real_world = {"state": 0, "actuator_calls": []}
    real_world["actuator_calls"].append(selected)
    real_world["state"] += 1 if selected == "advance" else 0

    imagined = responses[selected]
    observed = grounded(0.7 if real_world["state"] == 1 else 0.1)
    surprise_graph = Graph()
    surprise_graph.add_node(Node("surprise_root", NodeType.SCRIPT))
    surprise_graph.add_node(Node(
        "prediction_surprise",
        NodeType.TERMINAL,
        predicate=prediction_surprise_terminal,
        meta={"role": "PREDICTION_SURPRISE"},
    ))
    surprise_graph.add_hierarchy_pair("surprise_root", "prediction_surprise")
    real_frame = FrameContext(
        "real-successor",
        FrameKind.REAL,
        {
            "imagined_child_response": imagined,
            "observed_child_response": observed,
        },
    )
    engine = FormalReConEngine(surprise_graph)
    engine.request("surprise_root")
    engine.run(
        max_ticks=16,
        env=real_frame.to_env_overlay(),
        until=lambda e: e.g.nodes["surprise_root"].state == NodeState.CONFIRMED,
    )
    return {
        "selected_action": selected,
        "scores": scores,
        "evaluations": evaluations,
        "real_actuator_calls": list(real_world["actuator_calls"]),
        "real_successor_state": real_world["state"],
        "prediction_surprise": surprise_graph.nodes["prediction_surprise"].activation.value,
        "raw_prediction_surprise": surprise_graph.nodes["prediction_surprise"].meta["raw_prediction_surprise"],
        "persistent_graph_unchanged": graph.to_snapshot() == graph_before,
        "persistent_learning_state_unchanged": protected == protected_before,
        "disconnected_activation": (
            evaluations["advance"].get("disconnected_activation", 0.0)
            if disconnected else None
        ),
    }


def no_frame_control() -> dict[str, Any]:
    graph = build_handover_graph()
    try:
        VirtualFrameExecutor().evaluate(
            graph, "leg_advance", FrameContext("real", FrameKind.REAL)
        )
    except ValueError as exc:
        return {"blocked": True, "reason": str(exc)}
    return {"blocked": False}


def dream_leak_control() -> dict[str, Any]:
    protected = {"weights": [0.25], "lifecycle": "trial", "reservoir": []}
    before = deepcopy(protected)
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    def leak(_node: Node, _env: dict[str, Any]) -> tuple[bool, bool]:
        protected["weights"].append(1.0)
        return True, True
    graph.add_node(Node("leak", NodeType.TERMINAL, predicate=leak))
    graph.add_hierarchy_pair("root", "leak")
    try:
        VirtualFrameExecutor().evaluate(
            graph,
            "root",
            FrameContext("leak-frame", FrameKind.VIRTUAL, hypothetical_action="leak"),
            protected_state=protected,
        )
    except DreamStateLeakError as exc:
        return {"blocked": True, "rolled_back": protected == before, "reason": str(exc)}
    return {"blocked": False, "rolled_back": protected == before}


def self_credit_control() -> dict[str, Any]:
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    def self_credit(_node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        env["__frame_effects__"].set_maturity("child", True)
        return True, True
    graph.add_node(Node("self_credit", NodeType.TERMINAL, predicate=self_credit))
    graph.add_hierarchy_pair("root", "self_credit")
    result = VirtualFrameExecutor().evaluate(
        graph,
        "root",
        FrameContext("credit-frame", FrameKind.VIRTUAL, hypothetical_action="credit"),
    )
    return {
        "blocked": result.root_state == NodeState.FAILED,
        "effect_attempts": list(result.effect_attempts),
    }


def run_canary() -> dict[str, Any]:
    baseline = select_and_actuate()
    shuffled = select_and_actuate(shuffled=True)
    disconnected = select_and_actuate(disconnected=True)
    no_frame = no_frame_control()
    leakage = dream_leak_control()
    self_credit = self_credit_control()
    checks = {
        "grounded_child_routes_parent_leg": baseline["selected_action"] == "advance",
        "shuffled_child_response_changes_leg": shuffled["selected_action"] == "stall",
        "only_selected_leg_actuates_real_environment": baseline["real_actuator_calls"] == ["advance"],
        "prediction_surprise_observed_on_real_successor": baseline["raw_prediction_surprise"] > 0,
        "disconnected_terminal_cannot_route": (
            disconnected["selected_action"] == "advance"
            and disconnected["disconnected_activation"] == 0.0
        ),
        "no_virtual_frame_blocks_dream_query": no_frame["blocked"],
        "persistent_graph_unchanged": baseline["persistent_graph_unchanged"],
        "persistent_learning_state_unchanged": baseline["persistent_learning_state_unchanged"],
        "hidden_dream_leak_fails_and_rolls_back": leakage["blocked"] and leakage["rolled_back"],
        "dream_self_credit_is_blocked": self_credit["blocked"],
    }
    payload = {
        "schema_version": "recon_virtual_frame_child_response_canary.v1",
        "claim_scope": "deterministic engineering canary; no fresh data or KRK behavioral claim",
        "architecture_boundary": "graph-native terminals; host-executed generic final actuator bus",
        "baseline": baseline,
        "controls": {
            "shuffled_child_response": shuffled,
            "disconnected_internal_terminal": disconnected,
            "no_virtual_frame": no_frame,
            "dream_state_leakage": leakage,
            "self_credit_attempt": self_credit,
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["content_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/virtual_frame_child_response_canary_20260713.json"),
    )
    args = parser.parse_args()
    payload = run_canary()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "all_checks_pass": payload["all_checks_pass"],
        "content_sha256": payload["content_sha256"],
        "output": str(args.output),
    }, sort_keys=True))
    if not payload["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
