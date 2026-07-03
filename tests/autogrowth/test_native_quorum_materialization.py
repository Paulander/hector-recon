import chess

from recon_lite import FormalReConEngine, Graph, Node, NodeState, NodeType
from recon_lite_chess.autogrowth import (
    NativeQuorumMaterializationConfig,
    extract_learner_features,
    run_native_quorum_materialization,
)


OPPOSITION_FEN = "8/8/8/4k3/8/4K3/8/R7 w - - 0 1"
NON_OPPOSITION_FEN = "8/8/8/4k3/8/3K4/8/R7 w - - 0 1"


def _percept_equals(feature_name: str, expected: float):
    def predicate(node: Node, env: dict) -> tuple[bool, bool]:
        value = float(env["features"][feature_name])
        node.meta["last_value"] = value
        node.activation.value = 1.0 if value == expected else 0.0
        return True, value == expected

    return predicate


def _direct_opposition_graph() -> Graph:
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    graph.add_node(Node("direct_opposition", NodeType.SCRIPT))
    graph.add_node(
        Node(
            "same_file",
            NodeType.TERMINAL,
            predicate=_percept_equals("king_delta_file_abs", 0.0),
        )
    )
    graph.add_node(
        Node(
            "distance_two",
            NodeType.TERMINAL,
            predicate=_percept_equals("king_support_chebyshev_distance", 2.0),
        )
    )
    graph.add_hierarchy_pair("root", "direct_opposition")
    graph.add_hierarchy_pair("direct_opposition", "same_file")
    graph.add_hierarchy_pair("direct_opposition", "distance_two")
    graph.set_confirm_policy("direct_opposition", policy="k_of_n", k=2)
    graph.validate_formal_pairs()
    return graph


def _run_direct_opposition(fen: str) -> tuple[Graph, list[dict]]:
    graph = _direct_opposition_graph()
    board = chess.Board(fen)
    engine = FormalReConEngine(graph, record_trace=True)
    engine.request("root")
    trace = engine.run(
        max_ticks=16,
        env={"board": board, "features": extract_learner_features(board)},
        until=lambda _engine: graph.nodes["root"].state
        in (NodeState.CONFIRMED, NodeState.FAILED),
    )
    return graph, trace


def _trace_messages(trace: list[dict]) -> set[tuple[str, str, str, str]]:
    return {
        (message["src"], message["dst"], message["link_type"], message["message"])
        for frame in trace
        for message in frame["messages"]
    }


def test_phase2_quorum_direct_opposition_executes_with_formal_trace() -> None:
    graph, trace = _run_direct_opposition(OPPOSITION_FEN)
    messages = _trace_messages(trace)

    assert graph.nodes["direct_opposition"].state == NodeState.CONFIRMED
    assert graph.nodes["root"].state == NodeState.CONFIRMED
    assert ("direct_opposition", "same_file", "SUB", "request") in messages
    assert ("direct_opposition", "distance_two", "SUB", "request") in messages
    assert ("same_file", "direct_opposition", "SUR", "confirm") in messages
    assert ("distance_two", "direct_opposition", "SUR", "confirm") in messages

    graph, trace = _run_direct_opposition(NON_OPPOSITION_FEN)
    messages = _trace_messages(trace)

    assert graph.nodes["direct_opposition"].state == NodeState.FAILED
    assert graph.nodes["root"].state == NodeState.FAILED
    assert ("same_file", "direct_opposition", "SUR", "fail") in messages
    assert ("distance_two", "direct_opposition", "SUR", "confirm") in messages


def test_tg26u_smoke_materializes_native_quorum_and_reports_ablations() -> None:
    result = run_native_quorum_materialization(
        config=NativeQuorumMaterializationConfig(
            train_count=3,
            heldout_count=2,
            max_ticks=20,
            max_samples=4,
            max_candidates_per_move=1,
            max_shared_atom_candidates_per_choice=2,
            shared_atom_min_overlap=6,
            equivalence_count=1,
        )
    )

    payload = result.to_dict()
    decision = payload["decision"]
    assert payload["checkpoint"] == "TG26u_native_quorum_materialization"
    assert payload["purity_boundary"]["strict_native_quorum_materialized"] is True
    assert payload["purity_boundary"]["soft_quorum_diagnostic_only"] is True
    assert payload["purity_boundary"]["action_ranker_used_for_runtime"] is False
    assert payload["purity_boundary"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["purity_boundary"]["stage_labels_learner_visible"] is False

    for key in (
        "checkpoint_pass",
        "baseline_prototype_accuracy",
        "soft_quorum_accuracy",
        "materialized_quorum_accuracy",
        "materialized_quorum_nulls",
        "strict_native_quorum_materialized",
        "soft_quorum_selected_without_full_triplet_confirmation_count",
        "materialized_quorum_confirmed_inside_formal_engine_count",
        "featurehub_backed_atoms_used",
        "scheduler_equivalence_mismatch_count",
        "top_atom_ablation_accuracy",
        "action_atom_ablation_accuracy",
        "actuator_ablation_accuracy",
        "purity_boundary",
    ):
        assert key in decision

    assert decision["strict_native_quorum_materialized"] is True
    assert decision["actuator_ablation_accuracy"] == 0.0
    assert payload["materialized_quorum_veto_atoms"]["heldout"]["strict_native_quorum_materialized"] is True
    assert payload["ablations"]["remove_materialized_quorum_keep_shared_atoms"]["accuracy"] == 0.0
