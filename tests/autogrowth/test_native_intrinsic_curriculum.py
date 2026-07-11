from __future__ import annotations

from collections import Counter
import copy
import pickle

import chess
import pytest

from recon_lite import LinkType

from recon_lite_hector.learning import (
    IntrinsicCreditConfig,
    IntrinsicCreditEngine,
    OutcomeCalibratedPrototypeGate,
    Responsibility,
)
from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    NativeIntrinsicCurriculumConfig,
    R0_BALANCED_STRATA,
    R0_COMPETENCE_ID,
    R1_BALANCED_STRATA,
    R1_RETIRED_DEVELOPMENT_FENS,
    R1CheckpointInterrupt,
    _Pools,
    _balanced_r0_quotas,
    _balanced_r1_quotas,
    _build_r0_replay_memory,
    _choose_with_child_priority,
    _classify_r0_stratum,
    _classify_r1_stratum,
    _execute_white_and_observe,
    _generate_balanced_r0_split,
    _generate_balanced_r1_split,
    _r0_available,
    _r0_available_with_dispatch_cache,
    _r1_orbit_key,
    _replay_r0,
    _run_r1_arm,
)
from recon_lite_chess.autogrowth.foundation_curriculum import (
    _forced_mate_in_two_first_moves,
    _mate_moves,
)
from recon_lite_chess.autogrowth.native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
)


MATE_ONE_FEN = "k7/8/1K6/8/8/8/8/7R w - - 0 1"


def _graph() -> NativeReConKRKGraph:
    return NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            eta_m3=0.1,
            max_ticks=80,
            key_mode="canonical",
            shared_feature_atoms=True,
            shared_projection_atoms=True,
            include_grouped_cache_terminals=False,
            score_action_pattern_atoms=True,
            score_hierarchy_edge_weights=True,
        )
    )


def test_native_intrinsic_graph_starts_with_empty_learned_state() -> None:
    graph = _graph()
    audit = graph.learned_state_audit()

    assert audit == {
        "node_count": 1,
        "edge_count": 0,
        "triplet_count": 0,
        "trainable_edge_count": 0,
        "nonzero_trainable_edge_count": 0,
        "nonzero_local_weight_node_count": 0,
        "m3_update_count": 0,
        "m4_event_count": 0,
    }


def test_native_graph_pickle_roundtrip_restores_runtime_predicates() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        graph.ensure_triplet(board, move, stage="snapshot_test")

    restored = pickle.loads(pickle.dumps(graph, protocol=5))

    assert restored.learned_state_audit() == graph.learned_state_audit()
    assert restored.audit_choice(board) == graph.audit_choice(board)
    assert all(
        node.predicate is not None
        for node in restored.graph.nodes.values()
        if node.ntype.name == "TERMINAL"
    )


def test_frozen_policy_token_cache_matches_live_formal_confirmation() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    for _ in range(4):
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            terminal = _execute_white_and_observe(board, move)
            graph.apply_intrinsic_td(
                board,
                move,
                td_error=1.0 if terminal == "mate" else -1.0,
                stage_diagnostic="cache_token_test",
            )
    graph.mature_existing_graph()
    graph.freeze_existing_parameters(reason="cache_token_test")
    allowed = frozenset(graph.triplet_ids)

    token_cache: dict[str, dict] = {}
    miss = _r0_available_with_dispatch_cache(
        graph,
        None,
        board,
        mode="virtual_frame_verified",
        allowed_triplets=allowed,
        cache=token_cache,
        enabled=True,
        cache_validation_mode="frozen_policy_token",
    )
    token_hit = _r0_available_with_dispatch_cache(
        graph,
        None,
        board,
        mode="virtual_frame_verified",
        allowed_triplets=allowed,
        cache=token_cache,
        enabled=True,
        cache_validation_mode="frozen_policy_token",
    )
    live_hit = _r0_available_with_dispatch_cache(
        graph,
        None,
        board,
        mode="virtual_frame_verified",
        allowed_triplets=allowed,
        cache=token_cache,
        enabled=True,
        cache_validation_mode="live_formal",
    )

    assert miss[0] is True and miss[2] is False
    assert token_hit[0] == live_hit[0] == miss[0]
    assert token_hit[1]["selected_move"] == live_hit[1]["selected_move"]
    assert token_hit[1]["selected_triplet"] == live_hit[1]["selected_triplet"]
    assert token_hit[1]["cache_validation_mode"] == "frozen_policy_token"
    assert live_hit[1]["cache_validation_mode"] == "live_formal"
    assert token_hit[2] is True and live_hit[2] is True
    assert token_hit[3] is False and live_hit[3] is False
    assert graph.frozen_child_policy_token(allowed) == token_cache[board.fen()][
        "frozen_policy_token"
    ]
    assert graph.frozen_child_policy_token(frozenset()) is None


def test_frozen_policy_token_full_arm_matches_live_formal_with_cache_hits(
    tmp_path,
) -> None:
    base_graph = _graph()
    r1_fen = R1_RETIRED_DEVELOPMENT_FENS[0]
    r1_board = chess.Board(r1_fen)
    forced_first = tuple(_forced_mate_in_two_first_moves(r1_board))
    assert forced_first

    # Build a small, real Mate-in-1 child from every successor of one forced
    # Mate-in-2 move. This is test setup only; R1 training still receives no
    # forced-move labels and selects actions through the native graph.
    after_first = r1_board.copy(stack=False)
    after_first.push(forced_first[0])
    for reply in tuple(after_first.legal_moves):
        successor = after_first.copy(stack=False)
        successor.push(reply)
        for _ in range(4):
            for move in sorted(successor.legal_moves, key=lambda item: item.uci()):
                terminal = _execute_white_and_observe(successor, move)
                base_graph.apply_intrinsic_td(
                    successor,
                    move,
                    td_error=1.0 if terminal == "mate" else -1.0,
                    stage_diagnostic="cache_arm_test_r0",
                )
    base_graph.mature_existing_graph()
    base_graph.freeze_existing_parameters(reason="cache_arm_test")
    child_triplets = frozenset(base_graph.triplet_ids)

    base_credit = IntrinsicCreditEngine(IntrinsicCreditConfig())
    base_credit.register(R0_COMPETENCE_ID, mature=True)
    gate = OutcomeCalibratedPrototypeGate(
        feature_names=("probe",),
        offsets=(0.0,),
        scales=(1.0,),
        prototypes=((0.0,), (1.0,)),
        outcomes=(False, True),
        neighbors=1,
        threshold=0.5,
        train_metrics={},
        validation_metrics={},
        mature=True,
    )
    pools = _Pools(
        r0_train=(MATE_ONE_FEN,),
        r0_validation=(MATE_ONE_FEN,),
        r0_regression=(MATE_ONE_FEN,),
        gate_train_decoys=(),
        gate_validation_decoys=(),
        gate_regression_decoys=(),
        r1_train=(r1_fen,),
        r1_validation=(r1_fen,),
        r1_regression=(r1_fen,),
        r0_train_strata=("test",),
        r0_validation_strata=("test",),
        r0_regression_strata=("test",),
        r0_excluded_fens=(),
        r0_pool_mode="test",
        r1_train_strata=("test",),
        r1_validation_strata=("test",),
        r1_regression_strata=("test",),
        r1_pool_mode="test",
    )

    def run_arm(mode: str):
        graph = copy.deepcopy(base_graph)
        credit = copy.deepcopy(base_credit)
        config = NativeIntrinsicCurriculumConfig(
            r0_replay_per_r1_epoch=0,
            r1_validation_interval=30,
            r1_snapshot_interval=30,
            r1_mastery_threshold=2.0,
            max_samples=0,
            progress_path=str(tmp_path / f"{mode}_progress.json"),
            r1_snapshot_dir=str(tmp_path / mode),
            resume_r1_snapshots=False,
            r0_child_cache_validation_mode=mode,
        )
        result = _run_r1_arm(
            "full_intrinsic",
            graph,
            credit,
            gate,
            pools,
            r0_replay_memory=(),
            r0_child_triplet_ids=child_triplets,
            max_epochs=30,
            config=config,
        )
        return graph, credit, result

    live_graph, live_credit, live = run_arm("live_formal")
    token_graph, token_credit, token = run_arm("frozen_policy_token")

    assert live["training"]["r0_child_dispatch_cache_hit_count"] > 0
    assert token["training"]["r0_child_dispatch_cache_certified_hit_count"] == live[
        "training"
    ]["r0_child_dispatch_cache_hit_count"]
    assert token["training"]["child_handoff_count"] == live["training"][
        "child_handoff_count"
    ]
    assert token["validation"] == live["validation"]
    assert token["regression"] == live["regression"]
    assert token["r0_retention"] == live["r0_retention"]
    assert token_graph.learned_state_audit() == live_graph.learned_state_audit()
    assert token_credit.snapshot() == live_credit.snapshot()


def test_native_stem_composite_uses_graph_and_separates_correlation_from_causation() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    rows = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        triplet_id = graph.ensure_triplet(board, move, stage="composite_test")
        atoms = {
            node_id
            for node_id in graph.triplet_nodes[triplet_id]
            if graph.graph.nodes[node_id].meta.get("shared_feature_atom")
        }
        rows.append((move, triplet_id, atoms))

    selected = None
    for first_move, first_triplet, first_atoms in rows:
        for second_move, _second_triplet, second_atoms in rows:
            common = sorted(first_atoms & second_atoms)
            first_only = sorted(first_atoms - second_atoms)
            if first_move != second_move and common and first_only:
                selected = (
                    first_move,
                    first_triplet,
                    second_move,
                    (common[0], first_only[0]),
                )
                break
        if selected is not None:
            break
    assert selected is not None
    first_move, first_triplet, contrast_move, members = selected

    composite_id = graph.materialize_shared_composite(
        members,
        (first_triplet,),
        stage="composite_test",
    )
    cell = graph.composite_cells[composite_id]
    composite_node_id = graph.composite_node_by_triplet[(composite_id, first_triplet)]
    assert cell.state.name == "TRIAL"
    assert cell.is_composition is True
    assert tuple(cell.children) == tuple(sorted(members))
    assert graph.graph.nodes[composite_node_id].meta["confirm_policy"] == "k_of_n"
    assert graph.graph.nodes[composite_node_id].meta["confirm_k"] == 2

    graph.confirm_candidate(
        board,
        triplet_id=first_triplet,
        move_uci=first_move.uci(),
    )
    assert graph.graph.nodes[composite_node_id].state.name in {"TRUE", "CONFIRMED"}
    graph.apply_intrinsic_td(
        board,
        first_move,
        td_error=1.0,
        stage_diagnostic="composite_test",
    )
    assert cell.candidate_stats.relevance_stats.activation_count == 1
    assert cell.candidate_stats.credit_stats.positive_correlation == 1
    assert cell.candidate_stats.credit_stats.total_interventions == 0
    assert cell.candidate_stats.decision(xp=cell.xp) == "trial"

    graph.confirm_candidate(
        board,
        triplet_id=first_triplet,
        move_uci=contrast_move.uci(),
    )
    assert graph.graph.nodes[composite_node_id].state.name == "FAILED"

    graph.confirm_candidate(
        board,
        triplet_id=first_triplet,
        move_uci=first_move.uci(),
    )
    enabled_score = graph.confirm_candidate(
        board,
        triplet_id=first_triplet,
        move_uci=first_move.uci(),
    )["selected_score"]
    assert graph.graph.nodes[composite_node_id].state.name in {"TRUE", "CONFIRMED"}
    assert graph._confirmed_composite_score(first_triplet)[0] > 0.0
    graph.set_composite_enabled(composite_id, enabled=False)
    disabled_score = graph.confirm_candidate(
        board,
        triplet_id=first_triplet,
        move_uci=first_move.uci(),
    )["selected_score"]
    assert enabled_score is not None and disabled_score is not None
    assert enabled_score > disabled_score

    for cycle in range(5):
        assert graph.record_composite_intervention(
            composite_id,
            enabled_return=1.0,
            disabled_return=0.0,
            cycle=cycle,
        ) == "positive"
    assert cell.candidate_stats.credit_stats.positive_intervention == 5
    assert cell.candidate_stats.decision(xp=cell.xp) == "mature"

    restored = pickle.loads(pickle.dumps(graph, protocol=5))
    assert composite_id in restored.composite_cells
    assert restored.composite_member_ids[composite_id] == tuple(sorted(members))
    assert restored.to_dict()["composite_candidate_count"] == 1


def test_native_composite_proposals_are_selective_bounded_and_deterministic() -> None:
    graph = _graph()
    observed_triplets = set()
    for fen_index, fen in enumerate(R1_RETIRED_DEVELOPMENT_FENS[:4]):
        board = chess.Board(fen)
        for move_index, move in enumerate(
            sorted(board.legal_moves, key=lambda item: item.uci())
        ):
            triplet_id = graph.apply_intrinsic_td(
                board,
                move,
                td_error=1.0 if (fen_index + move_index) % 4 == 0 else -1.0,
                stage_diagnostic="proposal_test",
            )
            observed_triplets.add(triplet_id)

    first = graph.rank_shared_composite_candidates(
        observed_triplets,
        max_candidates=5,
        max_atoms_per_triplet=256,
        min_support=2,
    )
    second = graph.rank_shared_composite_candidates(
        reversed(sorted(observed_triplets)),
        max_candidates=5,
        max_atoms_per_triplet=256,
        min_support=2,
    )

    assert first
    assert first == second
    assert len(first) <= 5
    assert all(
        row["support"] < min(row["member_supports"])
        and row["candidate_generation_used_outcome_label"] is False
        and row["candidate_generation_signal"] == "native_root_edge_weight"
        for row in first
    )
    controls = graph.matched_random_shared_composite_candidates(
        observed_triplets,
        first,
        seed=20260721,
        max_atoms_per_triplet=256,
        min_support=2,
    )
    repeated_controls = graph.matched_random_shared_composite_candidates(
        reversed(sorted(observed_triplets)),
        first,
        seed=20260721,
        max_atoms_per_triplet=256,
        min_support=2,
    )
    assert controls == repeated_controls
    assert len(controls) == len(first)
    assert {row["candidate_id"] for row in controls}.isdisjoint(
        row["candidate_id"] for row in first
    )
    assert all(
        row["control_selection_used_outcome_signal"] is False
        and row["control_tie_break"] == "seeded_candidate_identity_sha256"
        for row in controls
    )
    selected = first[0]
    composite_id = graph.materialize_shared_composite(
        selected["member_atom_ids"],
        selected["parent_triplet_ids"],
        stage="proposal_test",
    )
    assert composite_id == selected["candidate_id"]
    assert graph.composite_triplets[composite_id] == set(
        selected["parent_triplet_ids"]
    )


def test_r1_structural_epoch_materializes_trial_candidates_without_causal_maturity(
    tmp_path,
    monkeypatch,
) -> None:
    def fake_rank(self, triplet_ids, **_kwargs):
        triplet_id = sorted(triplet_ids)[0]
        members = sorted(
            node_id
            for node_id in self.triplet_nodes[triplet_id]
            if self.graph.nodes[node_id].meta.get("shared_feature_atom")
        )[:2]
        assert len(members) == 2
        return (
            {
                "candidate_id": "structural_hook_test_candidate",
                "member_atom_ids": members,
                "parent_triplet_ids": [triplet_id],
                "candidate_generation_used_outcome_label": False,
                "candidate_generation_signal": "native_root_edge_weight",
            },
        )

    monkeypatch.setattr(
        NativeReConKRKGraph,
        "rank_shared_composite_candidates",
        fake_rank,
    )
    graph = _graph()
    credit = IntrinsicCreditEngine(IntrinsicCreditConfig())
    credit.register(R0_COMPETENCE_ID, mature=True)
    gate = OutcomeCalibratedPrototypeGate(
        feature_names=("probe",),
        offsets=(0.0,),
        scales=(1.0,),
        prototypes=((0.0,), (1.0,)),
        outcomes=(False, True),
        neighbors=1,
        threshold=0.5,
        train_metrics={},
        validation_metrics={},
        mature=True,
    )
    r1_fen = R1_RETIRED_DEVELOPMENT_FENS[0]
    pools = _Pools(
        r0_train=(MATE_ONE_FEN,),
        r0_validation=(MATE_ONE_FEN,),
        r0_regression=(MATE_ONE_FEN,),
        gate_train_decoys=(),
        gate_validation_decoys=(),
        gate_regression_decoys=(),
        r1_train=(r1_fen,),
        r1_validation=(r1_fen,),
        r1_regression=(r1_fen,),
        r0_train_strata=("test",),
        r0_validation_strata=("test",),
        r0_regression_strata=("test",),
        r0_excluded_fens=(),
        r0_pool_mode="test",
        r1_train_strata=("test",),
        r1_validation_strata=("test",),
        r1_regression_strata=("test",),
        r1_pool_mode="test",
    )
    config = NativeIntrinsicCurriculumConfig(
        r0_replay_per_r1_epoch=0,
        r1_validation_interval=1,
        r1_snapshot_interval=1,
        r1_mastery_threshold=2.0,
        max_samples=0,
        progress_path=str(tmp_path / "progress.json"),
        r1_snapshot_dir=str(tmp_path / "snapshots"),
        resume_r1_snapshots=False,
        r1_composite_proposal_epochs=(1,),
        r1_composite_max_candidates=1,
    )

    result = _run_r1_arm(
        "full_intrinsic",
        graph,
        credit,
        gate,
        pools,
        r0_replay_memory=(),
        r0_child_triplet_ids=frozenset(),
        max_epochs=1,
        config=config,
    )

    assert result["training"]["composite_candidate_count"] == 1
    assert result["training"]["composite_mature_count"] == 0
    assert result["training"]["composite_causal_intervention_count"] == 0
    assert result["training"]["composition_events"][0]["new_candidate_count"] == 1
    cell = next(iter(graph.composite_cells.values()))
    assert cell.state.name == "TRIAL"
    assert cell.candidate_stats.credit_stats.total_interventions == 0


def test_r1_interval_snapshot_resume_matches_uninterrupted(tmp_path) -> None:
    base_graph = _graph()
    base_credit = IntrinsicCreditEngine(IntrinsicCreditConfig())
    base_credit.register(R0_COMPETENCE_ID, mature=True)
    gate = OutcomeCalibratedPrototypeGate(
        feature_names=("probe",),
        offsets=(0.0,),
        scales=(1.0,),
        prototypes=((0.0,), (1.0,)),
        outcomes=(False, True),
        neighbors=1,
        threshold=0.5,
        train_metrics={},
        validation_metrics={},
        mature=True,
    )
    pools = _Pools(
        r0_train=(MATE_ONE_FEN,),
        r0_validation=(MATE_ONE_FEN,),
        r0_regression=(MATE_ONE_FEN,),
        gate_train_decoys=(),
        gate_validation_decoys=(),
        gate_regression_decoys=(),
        r1_train=(R1_RETIRED_DEVELOPMENT_FENS[0],),
        r1_validation=(R1_RETIRED_DEVELOPMENT_FENS[1],),
        r1_regression=(R1_RETIRED_DEVELOPMENT_FENS[2],),
        r0_train_strata=("test",),
        r0_validation_strata=("test",),
        r0_regression_strata=("test",),
        r0_excluded_fens=(),
        r0_pool_mode="test",
        r1_train_strata=("test",),
        r1_validation_strata=("test",),
        r1_regression_strata=("test",),
        r1_pool_mode="test",
    )
    common = dict(
        r0_replay_per_r1_epoch=0,
        r1_validation_interval=1,
        r1_snapshot_interval=1,
        r1_mastery_threshold=2.0,
        mature_child_priority=False,
        max_samples=0,
    )
    uninterrupted_config = NativeIntrinsicCurriculumConfig(
        progress_path=str(tmp_path / "uninterrupted_progress.json"),
        r1_snapshot_dir=str(tmp_path / "uninterrupted"),
        resume_r1_snapshots=False,
        **common,
    )
    uninterrupted_graph = copy.deepcopy(base_graph)
    uninterrupted_credit = copy.deepcopy(base_credit)
    uninterrupted = _run_r1_arm(
        "no_bootstrap",
        uninterrupted_graph,
        uninterrupted_credit,
        gate,
        pools,
        r0_replay_memory=(),
        r0_child_triplet_ids=frozenset(),
        max_epochs=4,
        config=uninterrupted_config,
    )

    resume_config = NativeIntrinsicCurriculumConfig(
        progress_path=str(tmp_path / "resume_progress.json"),
        r1_snapshot_dir=str(tmp_path / "resume"),
        resume_r1_snapshots=True,
        **common,
    )
    with pytest.raises(R1CheckpointInterrupt) as interrupted:
        _run_r1_arm(
            "no_bootstrap",
            copy.deepcopy(base_graph),
            copy.deepcopy(base_credit),
            gate,
            pools,
            r0_replay_memory=(),
            r0_child_triplet_ids=frozenset(),
            max_epochs=4,
            config=resume_config,
            stop_after_epoch=2,
        )
    assert interrupted.value.epoch == 2
    assert interrupted.value.snapshot_path.exists()

    resumed_graph = copy.deepcopy(base_graph)
    resumed_credit = copy.deepcopy(base_credit)
    resumed = _run_r1_arm(
        "no_bootstrap",
        resumed_graph,
        resumed_credit,
        gate,
        pools,
        r0_replay_memory=(),
        r0_child_triplet_ids=frozenset(),
        max_epochs=4,
        config=resume_config,
    )

    ignored_training_keys = {
        "duration_seconds",
        "resumed_from_snapshot",
        "snapshot_path",
        "snapshot_write_count",
    }
    assert {
        key: value
        for key, value in resumed["training"].items()
        if key not in ignored_training_keys
    } == {
        key: value
        for key, value in uninterrupted["training"].items()
        if key not in ignored_training_keys
    }
    assert resumed["validation"] == uninterrupted["validation"]
    assert resumed["regression"] == uninterrupted["regression"]
    assert resumed["r0_retention"] == uninterrupted["r0_retention"]
    assert resumed_graph.learned_state_audit() == uninterrupted_graph.learned_state_audit()
    assert resumed_credit.snapshot() == uninterrupted_credit.snapshot()
    assert resumed["training"]["resumed_from_snapshot"] is True


def test_balanced_r1_quotas_cover_all_setup_and_orientation_strata() -> None:
    quotas = _balanced_r1_quotas(16)

    assert tuple(quotas) == R1_BALANCED_STRATA
    assert sum(quotas.values()) == 16
    assert all(
        quotas[f"rook_barrier:{side}"] == 2
        for side in ("left", "right", "bottom", "top")
    )
    assert all(
        quotas[f"king_edge:{side}"] == 1
        for side in ("left", "right", "bottom", "top")
    )
    assert all(
        quotas[f"king_corner:{corner}"] == 1
        for corner in ("a1", "a8", "h1", "h8")
    )
    with pytest.raises(ValueError):
        _balanced_r1_quotas(12)


def test_balanced_r0_splits_cover_all_locations_and_are_orbit_disjoint() -> None:
    used_fens: set[str] = set()
    used_orbits: set[str] = set()
    train, train_labels = _generate_balanced_r0_split(
        count=16,
        seed=20260719,
        used_fens=used_fens,
        used_orbits=used_orbits,
        max_attempts=300_000,
    )
    heldout, heldout_labels = _generate_balanced_r0_split(
        count=8,
        seed=20260720,
        used_fens=used_fens,
        used_orbits=used_orbits,
        max_attempts=300_000,
    )

    assert tuple(_balanced_r0_quotas(8)) == R0_BALANCED_STRATA
    assert Counter(train_labels) == Counter(_balanced_r0_quotas(16))
    assert Counter(heldout_labels) == Counter(_balanced_r0_quotas(8))
    generated_orbits = [_r1_orbit_key(fen) for fen in (*train, *heldout)]
    assert len(generated_orbits) == len(set(generated_orbits))
    for fen, label in zip(
        (*train, *heldout), (*train_labels, *heldout_labels), strict=True
    ):
        board = chess.Board(fen)
        assert _mate_moves(board)
        assert _classify_r0_stratum(board) == label
    with pytest.raises(ValueError):
        _balanced_r0_quotas(12)


def test_balanced_r1_splits_are_stratified_and_orbit_disjoint() -> None:
    used_fens: set[str] = set()
    retired_orbits = {_r1_orbit_key(fen) for fen in R1_RETIRED_DEVELOPMENT_FENS}
    used_orbits = set(retired_orbits)

    train, train_labels = _generate_balanced_r1_split(
        count=16,
        seed=20260718,
        used_fens=used_fens,
        used_orbits=used_orbits,
        max_attempts=300_000,
    )
    heldout, heldout_labels = _generate_balanced_r1_split(
        count=16,
        seed=20260719,
        used_fens=used_fens,
        used_orbits=used_orbits,
        max_attempts=300_000,
    )

    assert Counter(train_labels) == Counter(_balanced_r1_quotas(16))
    assert Counter(heldout_labels) == Counter(_balanced_r1_quotas(16))
    assert set(train).isdisjoint(heldout)
    generated_orbits = [_r1_orbit_key(fen) for fen in (*train, *heldout)]
    assert len(generated_orbits) == len(set(generated_orbits))
    assert not retired_orbits.intersection(generated_orbits)

    for fen, label in zip((*train, *heldout), (*train_labels, *heldout_labels), strict=True):
        board = chess.Board(fen)
        forced = tuple(_forced_mate_in_two_first_moves(board))
        assert forced
        assert _classify_r1_stratum(board, forced) == label


def test_observed_action_td_updates_only_executed_native_branch() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    mating_move = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) == "mate"
    )
    triplet_id = graph.ensure_triplet(board, mating_move, stage="R0_test")
    confirmation = graph.confirm_candidate(
        board,
        triplet_id=triplet_id,
        move_uci=mating_move.uci(),
    )
    assert confirmation["selected_move"] == mating_move.uci()

    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(
            eta_fast=0.5,
            eta_slow=1.0,
            min_grounding_evidence=1,
        )
    )
    credit.register(R0_COMPETENCE_ID)
    credit.register(triplet_id, hierarchy_depth=1)
    credit.begin_episode()
    event = credit.transition(
        triplet_id,
        responsibilities=(
            Responsibility(triplet_id),
            Responsibility(R0_COMPETENCE_ID, parent_distance=1),
        ),
        terminal_kind="mate",
    )
    graph.apply_intrinsic_td(
        board,
        mating_move,
        td_error=event.td_error,
        stage_diagnostic="R0_test",
    )

    audit = graph.learned_state_audit()
    assert audit["triplet_count"] == 1
    assert audit["m3_update_count"] > 0
    assert audit["nonzero_trainable_edge_count"] > 0
    assert credit.states[R0_COMPETENCE_ID].terminal_evidence == 1


def test_nonmating_action_receives_only_metabolic_td_not_teacher_failure() -> None:
    board = chess.Board(MATE_ONE_FEN)
    nonmating = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) is None
    )
    assert _execute_white_and_observe(board, nonmating) is None

    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(real_move_cost=0.02, eta_fast=0.5)
    )
    credit.register("observed_action")
    event = credit.transition("observed_action", terminal_kind=None)

    assert event.immediate_reward == -0.02
    assert event.successor_value == 0.0
    assert event.terminal_kind is None
    assert credit.states["observed_action"].terminal_evidence == 0


def test_shared_triplet_is_evaluated_for_each_overlapping_current_move() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    mating_move = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) == "mate"
    )
    triplet_id = graph.apply_intrinsic_td(
        board,
        mating_move,
        td_error=1.0,
        stage_diagnostic="R0_pair_mapping_test",
    )

    audit = graph.audit_choice(board)
    rows = [
        row
        for row in audit["confirmed_candidates"]
        if row["triplet_id"] == triplet_id
    ]

    assert audit["candidate_triplet_count"] > audit["unique_candidate_triplet_count"]
    assert len({row["move"] for row in rows}) > 1
    assert any(
        row["move"] != mating_move.uci() and row["score"] > 0.0
        for row in rows
    )


def test_hierarchy_score_uses_current_triplet_edge_for_shared_atom() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    first_move, second_move = list(board.legal_moves)[:2]
    first_id = graph.ensure_triplet(board, first_move, stage="shared_parent_test")
    second_id = graph.ensure_triplet(board, second_move, stage="shared_parent_test")
    roles = {
        "before_feature",
        "delta_feature",
        "after_feature",
        "projection_feature",
    }
    shared_ids = [
        node_id
        for node_id in graph.triplet_nodes[first_id] & graph.triplet_nodes[second_id]
        if graph.graph.nodes[node_id].meta.get("role") in roles
    ]
    assert shared_ids

    def parent_id(triplet_id: str, role: str) -> str:
        suffix = {
            "before_feature": "before_script",
            "delta_feature": "action_script",
            "projection_feature": "action_script",
            "after_feature": "after_script",
        }[role]
        return f"{triplet_id}_{suffix}"

    for node_id in graph.triplet_nodes[second_id]:
        node = graph.graph.nodes[node_id]
        role = str(node.meta.get("role", ""))
        node.meta["local_weight"] = 0.0
        if role in roles:
            edge = graph.graph.get_edge(parent_id(second_id, role), node_id, LinkType.SUB)
            assert edge is not None
            edge.w = 0.0
    shared_id = shared_ids[0]
    role = str(graph.graph.nodes[shared_id].meta["role"])
    first_edge = graph.graph.get_edge(parent_id(first_id, role), shared_id, LinkType.SUB)
    second_edge = graph.graph.get_edge(parent_id(second_id, role), shared_id, LinkType.SUB)
    assert first_edge is not None and second_edge is not None
    first_edge.w = 1.0
    second_edge.w = -1.0

    confirmation = graph.confirm_candidate(
        board, triplet_id=second_id, move_uci=second_move.uci()
    )
    assert confirmation["selected_move"] == second_move.uci()
    score, _ = graph._confirmed_terminal_score(second_id)
    assert score == pytest.approx(-1.0)


def test_virtual_frame_availability_uses_child_move_without_grounding() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    mating_move = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) == "mate"
    )
    graph.apply_intrinsic_td(
        board,
        mating_move,
        td_error=1.0,
        stage_diagnostic="R0_virtual_frame_test",
    )

    available, response = _r0_available(
        graph,
        None,
        board,
        mode="virtual_frame_verified",
    )

    assert available is True
    assert response["selected_move"] == mating_move.uci()
    assert response["availability_source"] == "mature_child_selected_virtual_frame"
    assert response["virtual_frame_terminal_grounding_granted"] is False

    graph.freeze_existing_parameters(reason="R0_test_consolidation")
    cache: dict[str, dict[str, object]] = {}
    first_available, _first_response, first_hit, first_mismatch = (
        _r0_available_with_dispatch_cache(
            graph,
            None,
            board,
            mode="virtual_frame_verified",
            allowed_triplets=frozenset(graph.triplet_ids),
            cache=cache,
            enabled=True,
        )
    )
    second_available, second_response, second_hit, second_mismatch = (
        _r0_available_with_dispatch_cache(
            graph,
            None,
            board,
            mode="virtual_frame_verified",
            allowed_triplets=frozenset(graph.triplet_ids),
            cache=cache,
            enabled=True,
        )
    )
    assert (first_available, first_hit, first_mismatch) == (True, False, False)
    assert (second_available, second_hit, second_mismatch) == (True, True, False)
    assert second_response["availability_source"] == "live_confirmed_frozen_child_dispatch_memory"
    hierarchical = _choose_with_child_priority(
        graph,
        board,
        r0_child_triplet_ids=frozenset(graph.triplet_ids),
    )
    assert hierarchical == mating_move


def test_r0_replay_uses_graph_selected_action_and_real_outcome() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    mating_move = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) == "mate"
    )
    graph.apply_intrinsic_td(
        board,
        mating_move,
        td_error=1.0,
        stage_diagnostic="R0_replay_setup",
    )
    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(
            eta_fast=0.5,
            min_grounding_evidence=1,
        )
    )
    credit.register(R0_COMPETENCE_ID)
    before_updates = graph.m3_update_count

    replay = _replay_r0(
        graph,
        credit,
        (MATE_ONE_FEN,),
        epoch=0,
        count=1,
    )

    assert replay["episodes"] == 1
    assert replay["observed_mates"] == 1
    assert replay["observed_nonmates"] == 0
    assert replay["formal_confirmation_failures"] == 0
    assert replay["cached_outcome_mismatches"] == 0
    assert graph.m3_update_count > before_updates
    assert credit.states[R0_COMPETENCE_ID].terminal_evidence == 1


def test_cached_r0_replay_is_graph_memory_live_confirmed_and_reexecuted() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    mating_move = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) == "mate"
    )
    for _ in range(8):
        graph.apply_intrinsic_td(
            board,
            mating_move,
            td_error=1.0,
            stage_diagnostic="R0_cached_replay_setup",
        )
    memory, audit = _build_r0_replay_memory(graph, (MATE_ONE_FEN,))
    assert audit["teacher_solution_labels_consumed"] == 0
    assert audit["experience_count"] == 1
    assert memory[0].move_uci == mating_move.uci()
    assert memory[0].observed_terminal == "mate"

    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(eta_fast=0.5, min_grounding_evidence=1)
    )
    credit.register(R0_COMPETENCE_ID)
    replay = _replay_r0(
        graph,
        credit,
        (MATE_ONE_FEN,),
        epoch=0,
        count=1,
        memory=memory,
    )

    assert replay["episodes"] == 1
    assert replay["observed_mates"] == 1
    assert replay["formal_confirmation_failures"] == 0
    assert replay["cached_outcome_mismatches"] == 0
