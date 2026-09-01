import copy
import chess
import pytest

from recon_lite import Graph, LinkType, Node, NodeState, NodeType, ReConEngine
from recon_lite_chess.autogrowth import (
    NativeLocalTrainingDecision,
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
    native_single_graph_curriculum as graph_module,
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
    control_decision = control.choose_local_policy_action(board)
    assert control_decision is not None

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
    treated_decision = treated.choose_local_policy_action(board)
    assert treated_decision is not None

    assert treated_decision.move_uci == target.uci()
    assert treated_decision.move_uci != control_decision.move_uci
    assert treated_decision.source is not None
    assert treated_decision.prediction_source == "pre_emission_native_raw"

    # Training remains curious after the positive event, but once the other
    # equally exposed local patterns receive their ordinary neutral visits,
    # the credited pattern is revisited without a host action schedule.
    revisited = False
    for _ in range(len(tuple(board.legal_moves))):
        exploratory = treated.choose_local_training_action(board, "local_r1")
        if exploratory.pattern_id == treated_decision.pattern_id:
            revisited = True
            break
        treated.apply_intrinsic_td(
            board,
            exploratory.move,
            td_error=0.0,
            stage_diagnostic="local_r1_neutral_revisit",
        )
    assert revisited


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


def test_shared_retrieval_keeps_high_utility_source_below_overlap_width(monkeypatch) -> None:
    network = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            shared_feature_atoms=True,
            shared_atom_min_overlap=1,
            max_prototype_candidates_per_move=2,
            max_ticks=8,
        )
    )
    board = chess.Board(MATE_ONE_FEN)
    moves = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))[:4]
    source_ids = tuple(
        network.ensure_triplet(board, move, stage="retrieval_incumbent")
        for move in moves
    )
    active_atom_ids = tuple(f"synthetic_active_atom_{index}" for index in range(4))
    network.shared_atom_triplets = {
        active_atom_ids[0]: set(source_ids),
        active_atom_ids[1]: set(source_ids[:3]),
        active_atom_ids[2]: set(source_ids[:2]),
        active_atom_ids[3]: {source_ids[0]},
    }
    monkeypatch.setattr(
        network,
        "_shared_atom_ids_for_keys",
        lambda _keys: set(active_atom_ids),
    )
    for source_id, weight in zip(source_ids, (0.10, 0.20, 0.30, 0.95)):
        edge = network.graph.get_edge("tg26o_root", source_id, LinkType.SUB)
        assert edge is not None
        edge.w = weight

    retrieved = network._triplets_from_active_shared_atoms(
        _triplet_keys(board, moves[0], key_mode=network.config.key_mode)
    )

    assert len(retrieved) == network.config.max_prototype_candidates_per_move
    assert retrieved[0] == source_ids[-1]
    assert source_ids[-1] in retrieved


def test_local_full_audit_keeps_exact_and_generalized_source_and_generalized_can_win(
    monkeypatch,
) -> None:
    network = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            shared_feature_atoms=True,
            max_prototype_candidates_per_move=3,
            max_shared_atom_candidates_per_choice=8,
            max_ticks=8,
        )
    )
    board = chess.Board(MATE_ONE_FEN)
    target = sorted(board.legal_moves, key=lambda item: item.uci())[0]
    generalized_source_move = sorted(board.legal_moves, key=lambda item: item.uci())[1]
    exact_id = network.ensure_triplet(board, target, stage="exact_source")
    generalized_id = network.ensure_triplet(
        board,
        generalized_source_move,
        stage="generalized_source",
    )
    assert generalized_id != exact_id
    monkeypatch.setattr(
        network,
        "_triplets_from_active_shared_atoms",
        lambda _keys: (generalized_id,),
    )
    observed: list[tuple[str, str]] = []

    def fake_confirmed_candidates(
        legal,
        triplet_ids,
        candidate_move_by_triplet=None,
    ):
        triplet_id = sorted(triplet_ids)[0]
        move_uci = str((candidate_move_by_triplet or {})[triplet_id])
        observed.append((triplet_id, move_uci))
        score = 0.10 if triplet_id == exact_id else 0.90
        return [(score, move_uci, triplet_id)]

    monkeypatch.setattr(network, "_confirmed_action_candidates", fake_confirmed_candidates)
    candidates = network._full_audit_candidates(
        board,
        {target.uci(): target},
    )

    assert {triplet_id for triplet_id, _move_uci in observed} == {
        exact_id,
        generalized_id,
    }
    assert max(candidates)[2] == generalized_id


def test_local_selector_cache_preserves_decision_and_semantic_manifest(
    monkeypatch,
) -> None:
    config = NativeSingleGraphConfig(
        include_symmetries=False,
        key_mode="canonical",
        max_ticks=24,
    )
    board = chess.Board(MATE_ONE_FEN)
    baseline = NativeReConKRKGraph(config=config)
    optimized = NativeReConKRKGraph(config=config)

    # Exercise an uncached reference path by making the cache's key accessor
    # recompute on every request.  The selector's externally visible decision
    # and persistent graph state must remain byte-for-byte equivalent.
    original_triplet_keys = graph_module._triplet_keys
    baseline_key_calls = 0

    def baseline_triplet_keys(position, move, *, key_mode):
        nonlocal baseline_key_calls
        baseline_key_calls += 1
        return original_triplet_keys(position, move, key_mode=key_mode)

    monkeypatch.setattr(graph_module, "_triplet_keys", baseline_triplet_keys)
    monkeypatch.setattr(
        graph_module._LocalDecisionCache,
        "keys",
        lambda _cache, position, move, *, key_mode: baseline_triplet_keys(
            position,
            move,
            key_mode=key_mode,
        ),
    )
    baseline_decision = baseline.choose_local_training_action(board, "cache")
    monkeypatch.undo()

    optimized_key_calls = 0

    def optimized_triplet_keys(position, move, *, key_mode):
        nonlocal optimized_key_calls
        optimized_key_calls += 1
        return original_triplet_keys(position, move, key_mode=key_mode)

    monkeypatch.setattr(graph_module, "_triplet_keys", optimized_triplet_keys)
    optimized_decision = optimized.choose_local_training_action(board, "cache")

    assert optimized_decision.to_manifest() == baseline_decision.to_manifest()
    assert optimized.canonical_semantic_manifest() == baseline.canonical_semantic_manifest()
    assert optimized_key_calls < baseline_key_calls
    assert not hasattr(optimized, "_local_decision_cache")


def test_generalized_dead_before_branch_skips_formal_ticks_with_parity(
    monkeypatch,
) -> None:
    config = NativeSingleGraphConfig(
        include_symmetries=False,
        key_mode="canonical",
        prototype_distance_threshold=0,
        max_prototype_candidates_per_move=1,
        max_ticks=8,
        tick_feature_terminals=False,
    )
    source_board = chess.Board(MATE_ONE_FEN)
    query_board = chess.Board("1k6/8/8/2K5/8/8/8/7R w - - 0 1")
    move = chess.Move.from_uci("h1h2")
    assert move in source_board.legal_moves
    assert move in query_board.legal_moves

    seed = NativeReConKRKGraph(config=config)
    source_id = seed.ensure_triplet(source_board, move, stage="dead_branch")

    def force_source(_keys):
        return ((source_id, 0),)

    baseline = copy.deepcopy(seed)
    optimized = copy.deepcopy(seed)
    monkeypatch.setattr(baseline, "_nearest_triplets_for_keys", force_source)
    monkeypatch.setattr(optimized, "_nearest_triplets_for_keys", force_source)
    monkeypatch.setattr(
        baseline,
        "_before_role_can_confirm",
        lambda *_args, **_kwargs: True,
    )
    legal = {move.uci(): move}

    baseline_candidates = baseline._full_audit_candidates(query_board, legal)
    optimized_candidates = optimized._full_audit_candidates(query_board, legal)

    assert baseline_candidates == optimized_candidates == []
    assert baseline.scheduler_stats["formal_ticks_run"] > 0
    assert optimized.scheduler_stats["formal_ticks_run"] == 0
    assert optimized._before_role_can_confirm(
        query_board,
        source_id,
        move.uci(),
    ) is False
    # Runtime settling is diagnostic only; semantic graph state must be
    # unchanged by rejecting the impossible serial branch.
    assert optimized.canonical_semantic_manifest() == seed.canonical_semantic_manifest()


def test_shared_global_cap_preserves_fair_incumbents_and_is_deterministic() -> None:
    network = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            shared_feature_atoms=True,
            max_prototype_candidates_per_move=2,
            max_shared_atom_candidates_per_choice=4,
        )
    )
    board = chess.Board(MATE_ONE_FEN)
    moves = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))[:3]
    source_moves = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))[:6]
    source_ids = tuple(
        network.ensure_triplet(board, move, stage="global_cap_source")
        for move in source_moves
    )
    weights = (0.90, 0.20, 0.80, 0.10, 0.70, 0.05)
    for source_id, weight in zip(source_ids, weights):
        edge = network.graph.get_edge("tg26o_root", source_id, LinkType.SUB)
        assert edge is not None
        edge.w = weight
    candidate_pairs = [
        (source_ids[0], moves[0].uci(), 0),
        (source_ids[1], moves[0].uci(), 1),
        (source_ids[2], moves[1].uci(), 0),
        (source_ids[3], moves[1].uci(), 1),
        (source_ids[4], moves[2].uci(), 0),
        (source_ids[5], moves[2].uci(), 1),
    ]

    capped = network._cap_shared_candidate_pairs(candidate_pairs)
    replayed = network._cap_shared_candidate_pairs(tuple(reversed(candidate_pairs)))

    assert capped == replayed
    assert len(capped) == network.config.max_shared_atom_candidates_per_choice
    assert {move_uci for _triplet_id, move_uci, _rank in capped[:3]} == {
        move.uci() for move in moves
    }
    assert {triplet_id for triplet_id, _move_uci, _rank in capped[:3]} == {
        source_ids[0],
        source_ids[2],
        source_ids[4],
    }
    assert capped[3][0] == source_ids[1]


def test_shared_global_cap_reserves_materialized_exact_before_aliases() -> None:
    network = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            shared_feature_atoms=True,
            max_shared_atom_candidates_per_choice=2,
        )
    )
    board = chess.Board(MATE_ONE_FEN)
    moves = tuple(sorted(board.legal_moves, key=lambda item: item.uci()))[:3]
    exact_id = network.ensure_triplet(board, moves[0], stage="exact_cap_source")
    generalized_id = network.ensure_triplet(
        board,
        moves[1],
        stage="generalized_cap_source",
    )
    exact_edge = network.graph.get_edge("tg26o_root", exact_id, LinkType.SUB)
    generalized_edge = network.graph.get_edge(
        "tg26o_root", generalized_id, LinkType.SUB
    )
    assert exact_edge is not None and generalized_edge is not None
    exact_edge.w = 0.10
    generalized_edge.w = 0.90

    capped = network._cap_shared_candidate_pairs([
        (generalized_id, moves[0].uci(), 0),
        (exact_id, moves[0].uci(), -1),
        (generalized_id, moves[1].uci(), -1),
        (generalized_id, moves[2].uci(), 0),
    ])

    assert (exact_id, moves[0].uci(), -1) in capped
    assert all(retrieval_rank < 0 for _triplet, _move, retrieval_rank in capped)


def test_local_exploration_ignores_unrelated_global_exposure() -> None:
    network = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            shared_feature_atoms=True,
            max_ticks=80,
        )
    )
    # This counter includes outcomes from every position in the graph.  It is
    # retained for lifetime diagnostics, but must not drive a new local
    # population's novelty pressure.
    network.graph.nodes["tg26o_root"].meta["request_exposures"] = 10_000

    decision = network.choose_local_training_action(
        chess.Board(MATE_ONE_FEN),
        stage_diagnostic="local_exposure_scope",
    )

    assert decision.total_current_pattern_exposures == 0
    assert decision.pattern_exposure == 0
    assert decision.exploration_bonus == 1.0


@pytest.mark.parametrize(
    ("normalization", "expected_scale"),
    (
        ("mean", lambda count: 1.0),
        ("sqrt", lambda count: 1.0 / count**0.5),
        ("sum", lambda count: 1.0 / count),
    ),
)
def test_one_td_event_conserves_shared_feature_credit(
    normalization,
    expected_scale,
) -> None:
    network = NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            shared_feature_atoms=True,
            shared_projection_atoms=True,
            terminal_score_normalization=normalization,
            eta_m3=0.10,
            max_ticks=8,
        )
    )
    board = chess.Board(MATE_ONE_FEN)
    move = sorted(board.legal_moves, key=lambda item: item.uci())[0]
    triplet_id = network.ensure_triplet(
        board,
        move,
        stage="shared_credit_conservation",
    )
    shared_ids = tuple(
        node_id
        for node_id in network.triplet_nodes[triplet_id]
        if network.graph.nodes[node_id].meta.get("shared_feature_atom")
    )
    assert len(shared_ids) > 1

    network.apply_intrinsic_td(
        board,
        move,
        td_error=1.0,
        stage_diagnostic="shared_credit_conservation",
    )

    expected_atom_weight = network.config.eta_m3 * expected_scale(len(shared_ids))
    assert sorted(
        network.graph.nodes[node_id].meta["local_weight"]
        for node_id in shared_ids
    ) == pytest.approx([expected_atom_weight] * len(shared_ids))
    if normalization == "mean":
        aggregate = sum(
            network.graph.nodes[node_id].meta["local_weight"]
            for node_id in shared_ids
        ) / len(shared_ids)
    elif normalization == "sqrt":
        aggregate = sum(
            network.graph.nodes[node_id].meta["local_weight"]
            for node_id in shared_ids
        ) / len(shared_ids) ** 0.5
    else:
        aggregate = sum(
            network.graph.nodes[node_id].meta["local_weight"]
            for node_id in shared_ids
        )
    assert aggregate == pytest.approx(network.config.eta_m3)
    root_edge = network.graph.get_edge("tg26o_root", triplet_id, LinkType.SUB)
    assert root_edge is not None
    assert root_edge.w == pytest.approx(network.config.eta_m3)
