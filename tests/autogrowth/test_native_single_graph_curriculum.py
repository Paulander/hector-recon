import chess

from recon_lite import Graph, Node, NodeState, NodeType, ReConEngine
from recon_lite_chess.autogrowth import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
)
from recon_lite_chess.autogrowth.foundation_curriculum import _mate_moves, _move_reward


MATE_ONE_FEN = "k7/8/1K6/8/8/8/8/7R w - - 0 1"


def test_actuator_affordances_are_terminal_leaves() -> None:
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    graph.add_node(
        Node(
            "act",
            NodeType.TERMINAL,
            predicate=lambda _node, _env: (True, True),
            meta={"terminal_kind": "actuator_affordance"},
        )
    )
    graph.add_hierarchy_pair("root", "act")
    graph.validate_formal_pairs()

    engine = ReConEngine(graph)
    graph.nodes["root"].state = NodeState.REQUESTED
    for _ in range(6):
        engine.step({})

    assert graph.nodes["act"].state == NodeState.CONFIRMED
    assert graph.nodes["root"].state == NodeState.CONFIRMED


def test_tg26o_materializes_real_nodes_and_edges() -> None:
    network = NativeReConKRKGraph(config=NativeSingleGraphConfig(include_symmetries=False, train_repetitions=1, max_ticks=80))
    board = chess.Board(MATE_ONE_FEN)
    move = next(iter(_mate_moves(board)))
    network.ensure_triplet(board, move, stage="Mate_In_1")

    payload = network.to_dict()
    assert payload["native_recon_graph"] is True
    assert payload["formal_pairs_valid"] is True
    assert payload["node_type_counts"]["SCRIPT"] > 0
    assert payload["node_type_counts"]["TERMINAL"] > 0
    assert "ACTION" not in payload["node_type_counts"]
    assert payload["actuator_terminal_count"] > 0
    assert payload["edge_type_counts"]["SUB"] > 8
    assert payload["edge_type_counts"]["SUR"] > 8
    assert payload["edge_type_counts"]["POR"] == 2
    assert payload["edge_type_counts"]["RET"] == 2


def test_tg26o_native_runtime_learns_mate_one_smoke() -> None:
    network = NativeReConKRKGraph(config=NativeSingleGraphConfig(include_symmetries=False, train_repetitions=1, max_ticks=80))
    board = chess.Board(MATE_ONE_FEN)
    positives = {move.uci() for move in _mate_moves(board)}
    rewards = {move.uci(): _move_reward(board, move, positive_moves=positives) for move in board.legal_moves}

    for _ in range(5):
        network.train_action_rewards(board, rewards=rewards, stage="Mate_In_1")

    selected = network.choose(board)
    assert selected is not None
    assert selected.uci() in positives
    assert network.to_dict()["runtime_choice_count"] > 0


def test_tg26p_indexed_scheduler_uses_native_choice_and_skips_irrelevant_triplets() -> None:
    indexed = NativeReConKRKGraph(config=NativeSingleGraphConfig(include_symmetries=False, train_repetitions=1, max_ticks=80, indexed_scheduler=True))
    board = chess.Board(MATE_ONE_FEN)
    extra_board = chess.Board("k7/8/8/8/8/8/1K6/7R w - - 0 1")
    positives = {move.uci() for move in _mate_moves(board)}
    rewards = {move.uci(): _move_reward(board, move, positive_moves=positives) for move in board.legal_moves}
    extra_rewards = {move.uci(): 0.0 for move in extra_board.legal_moves}

    for _ in range(5):
        indexed.train_action_rewards(board, rewards=rewards, stage="Mate_In_1")
    indexed.train_action_rewards(extra_board, rewards=extra_rewards, stage="Mate_In_1_extra_neutral")

    indexed_move = indexed.choose(board)

    assert indexed_move is not None
    assert indexed_move.uci() in positives
    stats = indexed.to_dict()["scheduler_stats"]
    assert stats["indexed_scheduler_used"] is True
    assert stats["candidate_triplets_ticked"] > 0
    assert stats["triplets_skipped_by_index"] > 0
    assert stats["full_graph_node_resets_avoided"] > 0


def test_tg26o_native_graph_contract_without_full_curriculum() -> None:
    network = NativeReConKRKGraph(config=NativeSingleGraphConfig(include_symmetries=False, train_repetitions=1))
    board = chess.Board(MATE_ONE_FEN)
    positives = {move.uci() for move in _mate_moves(board)}
    rewards = {move.uci(): _move_reward(board, move, positive_moves=positives) for move in board.legal_moves}
    network.train_action_rewards(board, rewards=rewards, stage="Mate_In_1")

    payload = network.to_dict()
    assert payload["native_recon_graph"] is True
    assert payload["formal_pairs_valid"] is True
    assert "ACTION" not in payload["node_type_counts"]
    assert payload["actuator_terminal_count"] > 0
    assert payload["node_type_counts"]["TERMINAL"] > payload["actuator_terminal_count"]
    assert payload["edge_type_counts"]["SUB"] == payload["edge_type_counts"]["SUR"]
    assert payload["edge_type_counts"]["POR"] == payload["edge_type_counts"]["RET"]


def test_consolidation_freezes_existing_parameters_but_not_new_growth() -> None:
    network = NativeReConKRKGraph(config=NativeSingleGraphConfig(include_symmetries=False))
    board = chess.Board(MATE_ONE_FEN)
    moves = tuple(sorted(board.legal_moves, key=lambda move: move.uci()))
    first = moves[0]
    triplet = network.apply_intrinsic_td(board, first, td_error=1.0, stage_diagnostic="R0")
    node_ids = tuple(network.triplet_nodes[triplet])
    before_nodes = {nid: float(network.graph.nodes[nid].meta["local_weight"]) for nid in node_ids}
    before_edges = tuple(float(edge.w) for edge in network.triplet_trainable_edges[triplet])
    frozen = network.freeze_existing_parameters(reason="R0_joint_mastery")
    assert frozen["frozen_node_parameter_count"] > 0
    assert frozen["frozen_edge_parameter_count"] > 0
    network.apply_intrinsic_td(board, first, td_error=-1.0, stage_diagnostic="R1")
    assert {nid: float(network.graph.nodes[nid].meta["local_weight"]) for nid in node_ids} == before_nodes
    assert tuple(float(edge.w) for edge in network.triplet_trainable_edges[triplet]) == before_edges
    second = moves[1]
    new_triplet = network.apply_intrinsic_td(board, second, td_error=1.0, stage_diagnostic="R1")
    new_edges = network.triplet_trainable_edges[new_triplet]
    assert new_triplet != triplet
    assert any(float(edge.w) > 0.0 for edge in new_edges)
