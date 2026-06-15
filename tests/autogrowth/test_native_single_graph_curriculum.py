import chess

from recon_lite import Graph, LinkType, Node, NodeState, NodeType, ReConEngine
from recon_lite_chess.autogrowth import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
)
from recon_lite_chess.autogrowth.foundation_curriculum import _mate_moves, _move_reward


MATE_ONE_FEN = "k7/8/1K6/8/8/8/8/7R w - - 0 1"


def test_action_nodes_are_native_recon_leaves() -> None:
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    graph.add_node(Node("act", NodeType.ACTION, predicate=lambda _node, _env: (True, True)))
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
    assert payload["node_type_counts"]["ACTION"] > 0
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


def test_tg26o_native_graph_contract_without_full_curriculum() -> None:
    network = NativeReConKRKGraph(config=NativeSingleGraphConfig(include_symmetries=False, train_repetitions=1))
    board = chess.Board(MATE_ONE_FEN)
    positives = {move.uci() for move in _mate_moves(board)}
    rewards = {move.uci(): _move_reward(board, move, positive_moves=positives) for move in board.legal_moves}
    network.train_action_rewards(board, rewards=rewards, stage="Mate_In_1")

    payload = network.to_dict()
    assert payload["native_recon_graph"] is True
    assert payload["formal_pairs_valid"] is True
    assert payload["node_type_counts"]["ACTION"] > 0
    assert payload["node_type_counts"]["TERMINAL"] > payload["node_type_counts"]["ACTION"]
    assert payload["edge_type_counts"]["SUB"] == payload["edge_type_counts"]["SUR"]
    assert payload["edge_type_counts"]["POR"] == payload["edge_type_counts"]["RET"]
