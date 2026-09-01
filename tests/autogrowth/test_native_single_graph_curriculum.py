import chess

from recon_lite import Graph, Node, NodeState, NodeType, ReConEngine
from recon_lite_chess.autogrowth import (
    NativeLocalTrainingDecision,
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
)
from recon_lite_chess.autogrowth.foundation_curriculum import _mate_moves, _move_reward
from recon_lite_chess.autogrowth.native_single_graph_curriculum import (
    _triplet_id,
    _triplet_keys,
)


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


def test_observed_td_moves_the_exact_confirmed_policy_score() -> None:
    network = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            train_repetitions=1,
            max_ticks=80,
        )
    )
    board = chess.Board(MATE_ONE_FEN)
    move = sorted(board.legal_moves, key=lambda item: item.uci())[0]
    triplet_id = network.ensure_triplet(board, move, stage="policy_credit_identity")

    before = network.confirm_candidate(
        board, triplet_id=triplet_id, move_uci=move.uci()
    )
    before_score = float(before["selected_score_raw"])
    network.apply_intrinsic_td(
        board,
        move,
        td_error=0.05,
        stage_diagnostic="policy_credit_identity",
    )
    after = network.confirm_candidate(
        board, triplet_id=triplet_id, move_uci=move.uci()
    )
    after_score = float(after["selected_score_raw"])

    assert before["selected_score"] == round(before_score, 6)
    assert after["selected_score"] == round(after_score, 6)
    assert after_score > before_score


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


def test_local_training_audit_does_not_change_exposure_counters() -> None:
    network = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            train_repetitions=1,
            max_ticks=80,
        )
    )
    board = chess.Board(MATE_ONE_FEN)
    rewards = {move.uci(): 0.0 for move in board.legal_moves}
    network.train_action_rewards(board, rewards=rewards, stage="audit_exposure")
    before_root = int(network.graph.nodes["tg26o_root"].meta["request_exposures"])
    before_triplets = {
        triplet_id: int(
            network.graph.nodes[triplet_id].meta["request_exposures"]
        )
        for triplet_id in network.triplet_ids
    }

    network.audit_choice(board)

    assert int(network.graph.nodes["tg26o_root"].meta["request_exposures"]) == before_root
    assert {
        triplet_id: int(
            network.graph.nodes[triplet_id].meta["request_exposures"]
        )
        for triplet_id in network.triplet_ids
    } == before_triplets


def test_local_training_materializes_only_the_emitted_branch_and_preserves_id_parity(
    monkeypatch,
) -> None:
    network = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            train_repetitions=1,
            max_ticks=80,
        )
    )
    board = chess.Board(MATE_ONE_FEN)
    legacy_audit = network.audit_choice

    def forbidden_host_picker(*_args, **_kwargs):
        raise AssertionError("legacy host picker reached by local selector")

    monkeypatch.setattr(network, "choose", forbidden_host_picker)
    monkeypatch.setattr(network, "audit_choice", forbidden_host_picker)

    decision = network.choose_local_training_action(board, "local_r1")

    expected_id = _triplet_id(
        *_triplet_keys(board, decision.move, key_mode=network.config.key_mode)
    )
    assert isinstance(decision, NativeLocalTrainingDecision)
    assert decision.triplet_id == decision.pattern_id == expected_id
    assert network.triplet_ids == {decision.triplet_id}
    assert int(network.graph.nodes["tg26o_root"].meta["request_exposures"]) == 0
    assert int(network.graph.nodes[decision.triplet_id].meta["request_exposures"]) == 0
    assert decision.materialized_after_emission is True
    assert decision.confirmed is True
    assert decision.policy_supported is False
    assert decision.prediction_source == "pre_emission_native_raw"

    network.apply_intrinsic_td(
        board,
        decision.move,
        td_error=0.25,
        stage_diagnostic="local_r1",
    )
    assert int(network.graph.nodes["tg26o_root"].meta["request_exposures"]) == 1
    assert int(network.graph.nodes[decision.triplet_id].meta["request_exposures"]) == 1
    legacy_audit(board)
    assert int(network.graph.nodes["tg26o_root"].meta["request_exposures"]) == 1
    assert int(network.graph.nodes[decision.triplet_id].meta["request_exposures"]) == 1


def test_local_td_credit_changes_a_later_executed_action_relative_to_control() -> None:
    config = NativeSingleGraphConfig(
        include_symmetries=False,
        train_repetitions=1,
        max_ticks=80,
    )
    board = chess.Board(MATE_ONE_FEN)
    target = sorted(board.legal_moves, key=lambda item: item.uci())[0]
    neutral_rewards = {move.uci(): 0.0 for move in board.legal_moves}

    control = NativeReConKRKGraph(config=config)
    for _ in range(10):
        control.train_action_rewards(
            board,
            rewards=neutral_rewards,
            stage="local_r1_neutral_exposure",
        )
    control.apply_intrinsic_td(
        board,
        target,
        td_error=0.0,
        stage_diagnostic="local_r1_control_exposure",
    )
    control_decision = control.choose_local_training_action(board, "local_r1")

    treated = NativeReConKRKGraph(config=config)
    for _ in range(10):
        treated.train_action_rewards(
            board,
            rewards=neutral_rewards,
            stage="local_r1_neutral_exposure",
        )
    treated.apply_intrinsic_td(
        board,
        target,
        td_error=1.0,
        stage_diagnostic="local_r1",
    )
    treated_decision = treated.choose_local_training_action(board, "local_r1")

    assert treated_decision.move_uci == target.uci()
    assert treated_decision.move_uci != control_decision.move_uci
    assert treated_decision.source is not None
    assert treated_decision.prediction_source == "pre_emission_native_raw"


def test_local_training_choice_is_deterministic_and_alias_representative_is_exposure_indexed() -> None:
    config = NativeSingleGraphConfig(
        include_symmetries=False,
        key_mode="canonical",
        train_repetitions=1,
        max_ticks=80,
    )
    board = chess.Board(MATE_ONE_FEN)
    first = NativeReConKRKGraph(config=config)
    second = NativeReConKRKGraph(config=config)

    first_decision = first.choose_local_training_action(board, "local_r1")
    second_decision = second.choose_local_training_action(board, "local_r1")

    assert first_decision.to_manifest() == second_decision.to_manifest()
    assert first_decision.alias_group_size >= 1
    if first_decision.alias_group_size > 1:
        assert first_decision.alias_index == 0
        assert first_decision.move_uci == first_decision.source_move_uci or first_decision.source is None


def test_local_policy_query_is_exploitation_only_and_semantically_read_only() -> None:
    network = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            train_repetitions=1,
            max_ticks=80,
        )
    )
    board = chess.Board(MATE_ONE_FEN)
    target = sorted(board.legal_moves, key=lambda item: item.uci())[0]
    network.apply_intrinsic_td(
        board,
        target,
        td_error=1.0,
        stage_diagnostic="local_policy_setup",
    )
    before = network.canonical_semantic_manifest()
    triplets_before = frozenset(network.triplet_ids)

    decision = network.choose_local_policy_action(board)

    assert decision is not None
    assert decision.move in board.legal_moves
    assert decision.policy_supported is True
    assert decision.exploration_bonus == 0.0
    assert decision.materialized_after_emission is False
    assert frozenset(network.triplet_ids) == triplets_before
    assert network.canonical_semantic_manifest() == before


def test_empty_local_policy_abstains_instead_of_emitting_a_zero_score_guess() -> None:
    network = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            train_repetitions=1,
            max_ticks=80,
        )
    )
    board = chess.Board(MATE_ONE_FEN)

    before = network.canonical_semantic_manifest()
    assert network.choose_local_policy_action(board) is None
    assert network.canonical_semantic_manifest() == before


def test_local_policy_keeps_supported_negative_option_over_unsupported_zeroes() -> None:
    network = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            train_repetitions=1,
            max_ticks=80,
        )
    )
    board = chess.Board(MATE_ONE_FEN)
    target = sorted(board.legal_moves, key=lambda item: item.uci())[0]
    network.apply_intrinsic_td(
        board,
        target,
        td_error=-1.0,
        stage_diagnostic="local_policy_negative_support",
    )

    decision = network.choose_local_policy_action(board)

    assert decision is not None
    assert decision.move == target
    assert decision.policy_supported is True
    assert decision.raw_value < 0.0


def test_local_full_audit_respects_shared_candidate_cap(monkeypatch) -> None:
    network = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            shared_feature_atoms=True,
            max_shared_atom_candidates_per_choice=2,
            max_ticks=8,
        )
    )
    source_board = chess.Board(MATE_ONE_FEN)
    source_ids = tuple(
        network.ensure_triplet(source_board, move, stage="shared_source")
        for move in sorted(source_board.legal_moves, key=lambda item: item.uci())[:2]
    )
    query_board = chess.Board("8/8/8/8/4K3/8/6R1/7k w - - 0 1")
    calls = []

    monkeypatch.setattr(
        network,
        "_triplets_from_active_shared_atoms",
        lambda _keys: source_ids,
    )

    def capture_candidates(legal, triplet_ids, candidate_move_by_triplet=None):
        calls.append((tuple(triplet_ids), dict(candidate_move_by_triplet or {})))
        return []

    monkeypatch.setattr(network, "_confirmed_action_candidates", capture_candidates)
    network._full_audit_candidates(query_board)

    assert len(calls) == network.config.max_shared_atom_candidates_per_choice
    stats = network.scheduler_stats
    assert stats["shared_atom_candidate_pairs_before_cap"] >= len(calls)
    assert stats["shared_atom_candidate_pairs_after_cap"] == len(calls)
