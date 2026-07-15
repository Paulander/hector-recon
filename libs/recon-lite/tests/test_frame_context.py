from __future__ import annotations

from copy import deepcopy

import pytest

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
    prediction_residual_terminal,
    prediction_surprise_terminal,
)


def _grounded(value: float, uncertainty: float = 0.0) -> ChildResponse:
    return ChildResponse(
        child_id="mature_child",
        confirmed=True,
        expected_value=value,
        uncertainty=uncertainty,
        grounded=True,
        grounding_source="observed_outcomes",
    )


def _run_real(graph: Graph, root: str, frame: FrameContext) -> FormalReConEngine:
    engine = FormalReConEngine(graph)
    engine.request(root)
    engine.run(
        max_ticks=16,
        env=frame.to_env_overlay(),
        until=lambda e: e.g.nodes[root].state in {NodeState.CONFIRMED, NodeState.FAILED},
    )
    return engine


def test_frame_context_is_typed_immutable_and_existing_overlay_accepts_it() -> None:
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))

    def sensor(node: Node, env: dict[str, object]) -> tuple[bool, bool]:
        frame = env["__frame_context__"]
        node.activation.value = float(env["external_value"])
        return True, isinstance(frame, FrameContext) and frame.frame_id == "typed-v1"

    graph.add_node(Node("sensor", NodeType.TERMINAL, predicate=sensor))
    graph.add_hierarchy_pair("root", "sensor")
    frame = FrameContext(
        "typed-v1",
        FrameKind.VIRTUAL,
        {"external_value": 0.75},
        hypothetical_action="advance",
    )
    engine = FormalReConEngine(graph)
    engine.request("root")
    engine.run(
        max_ticks=16,
        env={"virtual_frames": {"root": frame}},
        until=lambda e: e.g.nodes["root"].state == NodeState.CONFIRMED,
    )
    assert graph.nodes["root"].state == NodeState.CONFIRMED
    assert graph.nodes["sensor"].activation.value == pytest.approx(0.75)
    with pytest.raises(TypeError):
        frame.values["external_value"] = 0.0  # type: ignore[index]


def test_virtual_executor_deep_isolates_nested_frame_values() -> None:
    source = {"nested": {"items": ["source"]}}
    frame = FrameContext(
        "nested-dream",
        FrameKind.VIRTUAL,
        source,
        hypothetical_action="inspect",
    )
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    observations: list[tuple[bool, list[str]]] = []

    def mutate_runtime(_node: Node, env: dict[str, object]) -> tuple[bool, bool]:
        runtime = env["nested"]
        runtime_frame = env["__frame_context__"]
        assert isinstance(runtime, dict)
        assert isinstance(runtime_frame, FrameContext)
        same_runtime_object = runtime is runtime_frame.values["nested"]
        runtime["items"].append("terminal")
        observations.append((same_runtime_object, list(runtime["items"])))
        return True, True

    graph.add_node(Node("mutator", NodeType.TERMINAL, predicate=mutate_runtime))
    graph.add_hierarchy_pair("root", "mutator")
    result = VirtualFrameExecutor().evaluate(graph, "root", frame)

    assert result.root_state == NodeState.CONFIRMED
    assert observations == [(True, ["source", "terminal"])]
    assert source == {"nested": {"items": ["source"]}}
    assert frame.values["nested"] == {"items": ["source"]}


def test_virtual_executor_evaluates_external_and_internal_terminals_without_mutation() -> None:
    graph = Graph()
    graph.add_node(Node("action_leg", NodeType.SCRIPT, meta={"confirm_policy": "and"}))

    def external_sensor(node: Node, env: dict[str, object]) -> tuple[bool, bool]:
        node.activation.value = float(env["successor_sensor"])
        return True, bool(env["successor_sensor"])

    graph.add_node(Node("external_sensor", NodeType.TERMINAL, predicate=external_sensor))
    graph.add_node(Node(
        "child_response",
        NodeType.TERMINAL,
        predicate=child_response_terminal,
        meta={"role": "CHILD_RESPONSE"},
    ))
    graph.add_hierarchy_pair("action_leg", "external_sensor")
    graph.add_hierarchy_pair("action_leg", "child_response")
    before = deepcopy(graph.to_snapshot())
    protected = {
        "weights": {"w": 0.4},
        "lifecycle": "mature",
        "reservoir": [1, 2],
        "reward": 0.0,
    }
    protected_before = deepcopy(protected)
    frame = FrameContext(
        "successor-advance",
        FrameKind.VIRTUAL,
        {
            "successor_sensor": 1.0,
            "child_response": _grounded(0.9, 0.1),
        },
        parent_frame_id="real-0",
        hypothetical_action="advance",
    )
    result = VirtualFrameExecutor().evaluate(
        graph, "action_leg", frame, protected_state=protected
    )
    assert result.root_state == NodeState.CONFIRMED
    assert result.activations["external_sensor"] == pytest.approx(1.0)
    assert result.activations["child_response"] == pytest.approx(0.81)
    assert graph.to_snapshot() == before
    assert all(node.state == NodeState.INACTIVE for node in graph.nodes.values())
    assert protected == protected_before
    assert result.effect_attempts == ()


def test_virtual_executor_rejects_real_frame() -> None:
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    graph.add_node(Node("terminal", NodeType.TERMINAL, predicate=lambda _n, _e: (True, True)))
    graph.add_hierarchy_pair("root", "terminal")
    with pytest.raises(ValueError, match="requires a virtual"):
        VirtualFrameExecutor().evaluate(
            graph, "root", FrameContext("real", FrameKind.REAL)
        )


@pytest.mark.parametrize(
    "operation",
    (
        "actuate",
        "reward",
        "update_weight",
        "update_lifecycle",
        "update_reservoir",
        "update_topology",
        "set_maturity",
    ),
)
def test_dream_effect_bus_blocks_every_persistent_effect(operation: str) -> None:
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))

    def cheat(_node: Node, env: dict[str, object]) -> tuple[bool, bool]:
        bus = env["__frame_effects__"]
        getattr(bus, operation)("target", 1.0)
        return True, True

    graph.add_node(Node("forbidden_effect", NodeType.TERMINAL, predicate=cheat))
    graph.add_hierarchy_pair("root", "forbidden_effect")
    result = VirtualFrameExecutor().evaluate(
        graph,
        "root",
        FrameContext("dream", FrameKind.VIRTUAL, hypothetical_action="cheat"),
    )
    assert result.root_state == NodeState.FAILED
    assert [row["operation"] for row in result.effect_attempts] == [operation]
    assert graph.nodes["forbidden_effect"].state == NodeState.INACTIVE


def test_hidden_dream_state_leak_is_rolled_back_and_fails_hard() -> None:
    protected = {"weights": [0.25], "maturity": False, "reservoir": []}
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))

    def hidden_leak(_node: Node, _env: dict[str, object]) -> tuple[bool, bool]:
        protected["weights"].append(0.99)
        protected["maturity"] = True
        return True, True

    graph.add_node(Node("leak", NodeType.TERMINAL, predicate=hidden_leak))
    graph.add_hierarchy_pair("root", "leak")
    before = deepcopy(protected)
    with pytest.raises(DreamStateLeakError, match="rolled back"):
        VirtualFrameExecutor().evaluate(
            graph,
            "root",
            FrameContext("dream", FrameKind.VIRTUAL, hypothetical_action="leak"),
            protected_state=protected,
        )
    assert protected == before
    assert all(node.state == NodeState.INACTIVE for node in graph.nodes.values())


def test_child_response_requires_grounding_and_cannot_certify_itself() -> None:
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    graph.add_node(Node("child", NodeType.TERMINAL, predicate=child_response_terminal))
    graph.add_hierarchy_pair("root", "child")
    frame = FrameContext(
        "dream",
        FrameKind.VIRTUAL,
        {
            "child_response": ChildResponse(
                child_id="dream_child",
                confirmed=True,
                expected_value=1.0,
                uncertainty=0.0,
                grounded=False,
            )
        },
        hypothetical_action="self-certify",
    )
    result = VirtualFrameExecutor().evaluate(graph, "root", frame)
    assert result.root_state == NodeState.FAILED
    assert result.activations["child"] == 0.0


def test_prediction_residual_is_real_frame_local_and_read_only() -> None:
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    graph.add_node(Node(
        "surprise",
        NodeType.TERMINAL,
        predicate=prediction_residual_terminal,
        meta={"role": "PREDICTION_RESIDUAL"},
    ))
    graph.add_hierarchy_pair("root", "surprise")
    real = FrameContext(
        "real-successor",
        FrameKind.REAL,
        {
            "imagined_child_response": _grounded(0.9, 0.1),
            "observed_child_response": _grounded(0.7, 0.1),
        },
    )
    _run_real(graph, "root", real)
    assert graph.nodes["root"].state == NodeState.CONFIRMED
    assert graph.nodes["surprise"].activation.value == pytest.approx(0.1)
    assert graph.nodes["surprise"].meta["raw_prediction_residual"] == pytest.approx(0.2)


def test_prediction_surprise_name_is_only_a_residual_compatibility_alias() -> None:
    node = Node("legacy", NodeType.TERMINAL)
    env = FrameContext(
        "real",
        FrameKind.REAL,
        {
            "imagined_child_response": _grounded(0.9),
            "observed_child_response": _grounded(0.7),
        },
    ).to_env_overlay()
    assert prediction_surprise_terminal(node, env) == (True, True)
    assert node.meta["raw_prediction_residual"] == pytest.approx(0.2)
    assert node.meta["raw_prediction_surprise"] == pytest.approx(0.2)
