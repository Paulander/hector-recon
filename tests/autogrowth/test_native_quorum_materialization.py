import random

import chess

from recon_lite import FormalReConEngine, Graph, Node, NodeState, NodeType
from recon_lite_chess.autogrowth import (
    NativeQuorumMaterializationConfig,
    extract_learner_features,
    generate_position_sets,
    load_canonical_mate2_first_scorer,
    evaluate_chain_confidence_gate,
    run_mate_in_one_basin_recognizer,
    run_mate_in_one_skill,
    run_mate_in_two_skill,
    run_native_quorum_materialization,
    run_reply_quantifier,
    train_chain_confidence_gate,
)
from recon_lite_chess.autogrowth.foundation_curriculum import (
    _forced_mate_in_two_first_moves,
    _generate_mate_in_one_positions,
    _generate_forced_mate_in_two_positions,
    _mate_moves,
    _random_krk_board,
    _valid_foundation_board,
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


def _basin_eval_rows(positive_fens: list[str], negative_fens: list[str]) -> list[dict]:
    rows = []
    for expected, fen in [(True, fen) for fen in positive_fens] + [
        (False, fen) for fen in negative_fens
    ]:
        board = chess.Board(fen)
        assert bool(_mate_moves(board)) is expected
        audit = run_mate_in_one_basin_recognizer(board, record_trace=True)
        rows.append(
            {
                "fen": fen,
                "expected": expected,
                "confirmed": audit["confirmed"],
                "basin_state": audit["basin_state"],
                "escape_restricted_state": audit["escape_restricted_state"],
                "king_support_geometry_state": audit["king_support_geometry_state"],
                "edge_relative_opposition_state": audit["edge_relative_opposition_state"],
                "corner_knight_support_state": audit["corner_knight_support_state"],
                "ticks": audit["ticks"],
                "mate_moves": [move.uci() for move in _mate_moves(board)],
                "trace_messages": {
                    (message["src"], message["dst"], message["link_type"], message["message"])
                    for frame in audit["trace"]
                    for message in frame["messages"]
                },
            }
        )
    return rows


def _basin_confusion(rows: list[dict]) -> dict[str, float | int]:
    true_positive = sum(row["expected"] and row["confirmed"] for row in rows)
    false_negative = sum(row["expected"] and not row["confirmed"] for row in rows)
    false_positive = sum((not row["expected"]) and row["confirmed"] for row in rows)
    true_negative = sum((not row["expected"]) and not row["confirmed"] for row in rows)
    return {
        "true_positive": true_positive,
        "false_negative": false_negative,
        "false_positive": false_positive,
        "true_negative": true_negative,
        "precision": true_positive / max(1, true_positive + false_positive),
        "recall": true_positive / max(1, true_positive + false_negative),
    }


def _skill_eval_rows(positive_fens: list[str], negative_fens: list[str]) -> list[dict]:
    rows = []
    for expected, fen in [(True, fen) for fen in positive_fens] + [
        (False, fen) for fen in negative_fens
    ]:
        board = chess.Board(fen)
        assert bool(_mate_moves(board)) is expected
        audit = run_mate_in_one_skill(board, record_trace=True)
        bound_move = (
            None if audit["bound_move"] is None else chess.Move.from_uci(audit["bound_move"])
        )
        mate_moves = _mate_moves(board)
        rows.append(
            {
                "fen": fen,
                "expected": expected,
                "confirmed": audit["confirmed"],
                "bound_move": None if bound_move is None else bound_move.uci(),
                "delivered_mate": bound_move in mate_moves if bound_move is not None else False,
                "root_state": audit["root_state"],
                "skill_state": audit["skill_state"],
                "recognizer_step_state": audit["recognizer_step_state"],
                "basin_state": audit["basin_state"],
                "actuator_script_state": audit["actuator_script_state"],
                "actuator_state": audit["actuator_state"],
                "mate_moves": [move.uci() for move in mate_moves],
                "trace_messages": _trace_messages(audit["trace"]),
            }
        )
    return rows


def _has_stalemate_trap(board: chess.Board) -> list[str]:
    traps = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        after = board.copy(stack=False)
        after.push(move)
        if after.legal_moves.count() == 0 and not after.is_check():
            traps.append(move.uci())
    return traps


def _generate_non_mate_in_two_positions(*, count: int, seed: int) -> tuple[list[str], list[dict]]:
    rng = random.Random(seed)
    positions: list[str] = []
    used: set[str] = set()
    trap_rows: list[dict] = []
    for _ in range(800_000):
        if len(positions) >= count and trap_rows:
            break
        board = _random_krk_board(rng)
        if not _valid_foundation_board(board):
            continue
        fen = board.fen()
        if fen in used:
            continue
        if _mate_moves(board) or _forced_mate_in_two_first_moves(board):
            continue
        traps = _has_stalemate_trap(board)
        if traps:
            trap_rows.append({"fen": fen, "trap_moves": traps})
            if len(positions) < count:
                positions.insert(0, fen)
                used.add(fen)
        elif len(positions) < count:
            positions.append(fen)
            used.add(fen)
    if len(positions) < count:
        raise RuntimeError(f"generated {len(positions)} non-mate-in-2 positions, needed {count}")
    return positions[:count], trap_rows


def _validates_mate_in_two_delivery(board: chess.Board, move_uci: str | None) -> bool:
    if move_uci is None:
        return False
    move = chess.Move.from_uci(move_uci)
    if move not in board.legal_moves:
        return False
    after_first = board.copy(stack=False)
    after_first.push(move)
    replies = list(after_first.legal_moves)
    if not replies:
        return after_first.is_check()
    for reply in replies:
        post_reply = after_first.copy(stack=False)
        post_reply.push(reply)
        audit = run_mate_in_one_skill(post_reply, record_trace=False)
        if not audit["confirmed"] or audit["bound_move"] is None:
            return False
        if chess.Move.from_uci(audit["bound_move"]) not in _mate_moves(post_reply):
            return False
    return True


def test_phase2_mate_in_one_basin_quorum_generalizes_on_generated_heldout() -> None:
    known_false_positive_fens = {
        "2K5/8/k7/8/8/8/8/4R3 w - - 0 1",
        "8/8/8/7R/8/8/K7/2k5 w - - 0 1",
    }
    known_false_positive_rows = _basin_eval_rows([], list(known_false_positive_fens))
    corner_regression_rows = _basin_eval_rows(["7R/8/8/8/8/1K6/8/k7 w - - 0 1"], [])

    assert not any(row["confirmed"] for row in known_false_positive_rows)
    corner_row = corner_regression_rows[0]
    assert corner_row["confirmed"]
    assert corner_row["corner_knight_support_state"] == "CONFIRMED"
    assert (
        "mate_in_1_corner_knight_support",
        "mate_in_1_king_support_geometry",
        "SUR",
        "confirm",
    ) in corner_row["trace_messages"]

    positive_fens = _generate_mate_in_one_positions(
        count=48,
        seed=20260731,
        max_attempts=240_000,
    )
    negative_set = generate_position_sets(
        seed=20260731,
        train_count=0,
        heldout_weakness_count=24,
        heldout_broader_count=24,
    )
    negative_fens = list(negative_set.heldout)

    original_rows = _basin_eval_rows(positive_fens, negative_fens)
    original_confusion = _basin_confusion(original_rows)

    assert original_confusion == {
        "true_positive": 48,
        "false_negative": 0,
        "false_positive": 0,
        "true_negative": 48,
        "precision": 1.0,
        "recall": 1.0,
    }
    assert not any(
        row["fen"] in known_false_positive_fens and row["confirmed"]
        for row in original_rows
    )
    confirmed_row = next(row for row in original_rows if row["confirmed"])
    assert ("mate_in_1_basin", "phase2_basin_root", "SUR", "confirm") in confirmed_row["trace_messages"]

    prior_fresh_positive_fens = _generate_mate_in_one_positions(
        count=64,
        seed=20260817,
        max_attempts=320_000,
    )
    prior_fresh_negative_set = generate_position_sets(
        seed=20260817,
        train_count=0,
        heldout_weakness_count=32,
        heldout_broader_count=32,
    )
    fresh_rows = _basin_eval_rows(
        prior_fresh_positive_fens,
        list(prior_fresh_negative_set.heldout),
    )
    fresh_confusion = _basin_confusion(fresh_rows)

    assert fresh_confusion == {
        "true_positive": 64,
        "false_negative": 0,
        "false_positive": 0,
        "true_negative": 64,
        "precision": 1.0,
        "recall": 1.0,
    }

    new_fresh_positive_fens = _generate_mate_in_one_positions(
        count=64,
        seed=20260901,
        max_attempts=320_000,
    )
    new_fresh_negative_set = generate_position_sets(
        seed=20260901,
        train_count=0,
        heldout_weakness_count=32,
        heldout_broader_count=32,
    )
    new_fresh_rows = _basin_eval_rows(
        new_fresh_positive_fens,
        list(new_fresh_negative_set.heldout),
    )
    new_fresh_confusion = _basin_confusion(new_fresh_rows)

    assert new_fresh_confusion == {
        "true_positive": 64,
        "false_negative": 0,
        "false_positive": 0,
        "true_negative": 64,
        "precision": 1.0,
        "recall": 1.0,
    }


def test_phase2_mate_in_one_skill_binds_basin_to_edge_mate_actuator() -> None:
    positive_fens = _generate_mate_in_one_positions(
        count=64,
        seed=20261001,
        max_attempts=320_000,
    )
    negative_set = generate_position_sets(
        seed=20261001,
        train_count=0,
        heldout_weakness_count=32,
        heldout_broader_count=32,
    )
    rows = _skill_eval_rows(positive_fens, list(negative_set.heldout))
    positive_rows = [row for row in rows if row["expected"]]
    negative_rows = [row for row in rows if not row["expected"]]
    misses = [
        row for row in positive_rows if not row["confirmed"] or not row["delivered_mate"]
    ]
    false_emissions = [
        row for row in negative_rows if row["confirmed"] or row["bound_move"] is not None
    ]

    assert len(positive_rows) == 64
    assert len(negative_rows) == 64
    assert misses == []
    assert false_emissions == []

    traced = positive_rows[0]["trace_messages"]
    assert ("phase2_mate_in_1_skill_root", "mate_in_1_skill", "SUB", "request") in traced
    assert (
        "mate_in_1_skill",
        "mate_in_1_basin_recognizer_step",
        "SUB",
        "request",
    ) in traced
    assert (
        "mate_in_1_basin",
        "mate_in_1_basin_recognizer_step",
        "SUR",
        "confirm",
    ) in traced
    assert (
        "mate_in_1_basin_recognizer_step",
        "deliver_edge_mate_step",
        "POR",
        "inhibit_request",
    ) in traced
    assert ("deliver_edge_mate_step", "deliver_edge_mate", "SUB", "request") in traced
    assert ("deliver_edge_mate", "deliver_edge_mate_step", "SUR", "confirm") in traced
    assert ("deliver_edge_mate_step", "mate_in_1_skill", "SUR", "confirm") in traced


def test_phase2_reply_quantifier_zero_reply_semantics() -> None:
    mate_board = chess.Board("7k/5K2/7R/8/8/8/8/8 b - - 1 1")
    stalemate_board = chess.Board("k7/1R6/2K5/8/8/8/8/8 b - - 0 1")

    assert mate_board.legal_moves.count() == 0
    assert mate_board.is_check()
    mate_audit = run_reply_quantifier(mate_board, record_trace=True)
    assert mate_audit["confirmed"]
    assert mate_audit["reply_count"] == 0

    assert stalemate_board.legal_moves.count() == 0
    assert not stalemate_board.is_check()
    stalemate_audit = run_reply_quantifier(stalemate_board, record_trace=True)
    assert not stalemate_audit["confirmed"]
    assert stalemate_audit["root_state"] == "FAILED"
    assert (
        "zero_reply_semantics",
        "mate_in_2_reply_quantifier",
        "SUR",
        "fail",
    ) in _trace_messages(stalemate_audit["trace"])


def test_phase2_mate_in_two_skill_trace_reaches_reply_mate_in_one() -> None:
    fen = "5k2/7K/8/8/4R3/8/8/8 w - - 0 1"
    board = chess.Board(fen)
    forced_moves = _forced_mate_in_two_first_moves(board)
    assert [move.uci() for move in forced_moves] == ["h7g6"]

    audit = run_mate_in_two_skill(board, record_trace=True)
    traced = _trace_messages(audit["trace"])
    after_first = board.copy(stack=False)
    after_first.push(forced_moves[0])
    reply = sorted(after_first.legal_moves, key=lambda item: item.uci())[0]
    reply_child = f"candidate_h7g6__reply_{reply.uci()}__reply_child"
    reply_skill = f"candidate_h7g6__reply_{reply.uci()}__mate_in_1_skill"

    assert audit["confirmed"]
    assert audit["bound_move"] == "h7g6"
    assert ("phase2_mate_in_2_skill_root", "mate_in_2_skill", "SUB", "request") in traced
    assert ("mate_in_2_skill", "candidate_h7g6__mate_in_2_candidate", "SUB", "request") in traced
    assert (
        "candidate_h7g6__mate_in_2_candidate",
        "candidate_h7g6__mate_in_2_reply_quantifier",
        "SUB",
        "request",
    ) in traced
    assert (
        "candidate_h7g6__mate_in_2_reply_quantifier",
        reply_child,
        "SUB",
        "request",
    ) in traced
    assert (reply_child, reply_skill, "SUB", "request") in traced
    assert (reply_skill, reply_child, "SUR", "confirm") in traced

    scorer = load_canonical_mate2_first_scorer()
    ordered_audit = run_mate_in_two_skill(
        board,
        record_trace=False,
        move_orderer=scorer.order_moves,
    )

    assert ordered_audit["confirmed"]
    assert ordered_audit["bound_move"] == "h7g6"
    assert ordered_audit["bound_move_rank"] == 1
    assert ordered_audit["requested_candidate_count"] == 1
    assert ordered_audit["virtual_frame_count"] < ordered_audit["built_virtual_frame_count"]


def test_phase2_mate_in_two_skill_exact_quantifier_generalizes_on_generated_heldout() -> None:
    positive_fens = _generate_forced_mate_in_two_positions(
        count=64,
        seed=20261021,
        max_attempts=400_000,
    )
    negative_fens, trap_rows = _generate_non_mate_in_two_positions(
        count=64,
        seed=20261022,
    )

    failures = []
    false_emissions = []
    frame_counts = []
    for fen in positive_fens:
        board = chess.Board(fen)
        audit = run_mate_in_two_skill(
            board,
            record_trace=False,
            lazy_candidates=False,
            max_ticks=192,
        )
        if not audit["confirmed"] or not _validates_mate_in_two_delivery(
            board,
            audit["bound_move"],
        ):
            failures.append(
                {
                    "fen": fen,
                    "bound_move": audit["bound_move"],
                    "forced_moves": [
                        move.uci() for move in _forced_mate_in_two_first_moves(board)
                    ],
                }
            )
        frame_counts.append(audit["virtual_frame_count"])

    for fen in negative_fens:
        board = chess.Board(fen)
        audit = run_mate_in_two_skill(
            board,
            record_trace=False,
            lazy_candidates=False,
            max_ticks=192,
        )
        if audit["confirmed"] or audit["bound_move"] is not None:
            false_emissions.append(
                {
                    "fen": fen,
                    "bound_move": audit["bound_move"],
                    "stalemate_traps": _has_stalemate_trap(board),
                }
            )
        frame_counts.append(audit["virtual_frame_count"])

    assert failures == []
    assert false_emissions == []
    assert trap_rows
    assert round(sum(frame_counts) / len(frame_counts), 6) == 96.804688
    assert max(frame_counts) == 182


def test_phase2_chain_confidence_gate_trains_weighted_threshold() -> None:
    rows = []
    for index in range(40):
        label = index < 20
        signal = 1.0 if label else 0.0
        rows.append(
            {
                "row_id": index,
                "exact_mate_in_2_label": label,
                "exact_ordered_frames": 11 if label else 17,
                "gate_features": {
                    "white_king_file": float(index % 8),
                    "black_king_nearest_edge_distance": 0.0 if label else 3.0,
                    "internal_mate_in_1_basin_confirms": 0.0,
                    "internal_fence_or_opposition_confirms": signal,
                },
            }
        )

    model = train_chain_confidence_gate(
        rows,
        seed=20261211,
        heldout_fraction=0.25,
        epochs=20,
    )
    heldout_ids = set(model["heldout_row_ids"])
    heldout = [row for row in rows if row["row_id"] in heldout_ids]
    evaluation = evaluate_chain_confidence_gate(heldout, model=model)
    recall_row = evaluation["thresholds"]["recall_favoring"]
    balanced_row = evaluation["thresholds"]["balanced"]

    assert model["schema_version"] == "phase2_chain_confidence_weighted_threshold.v0"
    assert recall_row["recall"] == 1.0
    assert recall_row["end_to_end_conversion"] == 1.0
    assert balanced_row["precision"] == 1.0
    assert balanced_row["end_to_end_conversion"] == 1.0


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
