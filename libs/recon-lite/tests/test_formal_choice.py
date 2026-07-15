from __future__ import annotations

import pytest

from recon_lite import FormalReConEngine, Graph, Node, NodeState, NodeType


def _terminal(value: float, success: bool = True):
    def predicate(node: Node, _env: dict[str, object]) -> tuple[bool, bool]:
        node.activation.value = value
        return True, success
    return predicate


def _choice_graph(values: tuple[float, ...]) -> Graph:
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT, meta={"confirm_policy": "choice"}))
    for index, value in enumerate(values):
        option = f"option_{index}"
        sensor = f"strength_{index}"
        actuator = f"actuator_{index}"
        graph.add_node(Node(option, NodeType.SCRIPT, meta={
            "confirm_policy": "and",
            "actuator_identity": actuator,
            "choice_strength_node_ids": [sensor],
            "choice_strength_require_all": True,
        }))
        graph.add_node(Node(sensor, NodeType.TERMINAL, predicate=_terminal(value)))
        graph.add_hierarchy_pair("root", option)
        graph.add_hierarchy_pair(option, sensor)
    return graph


def test_choice_waits_then_emits_exactly_one_graph_actuator() -> None:
    graph = _choice_graph((0.2, 0.8, 0.4))
    engine = FormalReConEngine(graph)
    engine.request("root")
    engine.run(max_ticks=24, until=lambda item: item.g.nodes["root"].state in {NodeState.CONFIRMED, NodeState.FAILED})
    assert graph.nodes["root"].state == NodeState.CONFIRMED
    assert engine.emit_exactly_one_actuator("root") == "actuator_1"
    assert [
        node_id for node_id in graph.children("root")
        if graph.nodes[node_id].meta.get("choice_selected")
    ] == ["option_1"]


def test_choice_uses_stable_anonymous_identity_tie_break() -> None:
    graph = _choice_graph((0.5, 0.5))
    engine = FormalReConEngine(graph)
    engine.request("root")
    engine.run(max_ticks=24, until=lambda item: item.g.nodes["root"].state == NodeState.CONFIRMED)
    assert engine.emit_exactly_one_actuator("root") == "actuator_1"


def test_exactly_one_actuator_fails_hard_without_graph_emission() -> None:
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    graph.add_node(Node("leaf", NodeType.TERMINAL))
    graph.add_hierarchy_pair("root", "leaf")
    engine = FormalReConEngine(graph)
    engine.request("root")
    engine.run(max_ticks=12, until=lambda item: item.g.nodes["root"].state == NodeState.CONFIRMED)
    with pytest.raises(RuntimeError, match="emitted 0 actuators"):
        engine.emit_exactly_one_actuator("root")
