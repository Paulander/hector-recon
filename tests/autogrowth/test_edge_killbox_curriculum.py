import json
from pathlib import Path

import chess

from recon_lite_chess.autogrowth.edge_killbox_curriculum import (
    EdgeKillboxCurriculumConfig,
    classify_edge_killbox_family,
    edge_killbox_invariants,
    generate_edge_killbox_datasets,
    geometry_summary,
    run_edge_killbox_curriculum,
)
from recon_lite_chess.autogrowth.features import extract_learner_features, validate_learner_record


def test_tg48_geometry_features_are_generic_and_firewall_safe() -> None:
    board = chess.Board("8/8/8/8/8/8/4R3/4K1k1 w - - 0 1")
    features = extract_learner_features(board)

    for key in (
        "king_delta_file_abs",
        "king_delta_rank_abs",
        "king_support_l_shape",
        "king_pair_knight_distance_like",
        "king_support_chebyshev_distance",
        "king_support_manhattan_distance",
        "rook_black_king_same_side_of_white_king_on_primary_axis",
        "rook_black_king_opposite_sides_of_white_king_on_primary_axis",
        "rook_distance_to_black_king_edge_line",
        "rook_fence_depth_relative_to_black_king_edge",
        "rook_lateral_escape_available",
        "black_king_on_edge",
        "black_king_corner_distance",
        "white_king_controls_escape_band",
    ):
        assert key in features
    validate_learner_record(features)


def test_tg48_generator_produces_disjoint_valid_invariant_checked_splits() -> None:
    cfg = EdgeKillboxCurriculumConfig(
        train_count=6,
        heldout_count=6,
        regression_count=6,
        decoy_count=3,
        hard_decoy_count=3,
        max_generation_attempts=80_000,
    )

    datasets = generate_edge_killbox_datasets(cfg)

    all_fens = [row["fen"] for rows in datasets.values() for row in rows]
    assert len(all_fens) == len(set(all_fens))
    assert {row["family"] for row in datasets["train"]} >= {
        "edge_killbox_opposed_side",
        "edge_killbox_same_side_rook_danger",
        "edge_killbox_mixed",
    }
    for split, rows in datasets.items():
        for row in rows:
            board = chess.Board(row["fen"])
            invariants = edge_killbox_invariants(board, allow_rook_risk=split in {"decoy", "hard_decoy"})
            assert invariants["legal_krk"]
            assert invariants["black_king_on_edge"]
            assert row["geometry_summary"] == geometry_summary(board)
            assert classify_edge_killbox_family(board) is not None
            assert row["validator_metadata"]["learner_visible_labels"] is False


def test_tg48_tiny_run_writes_artifact_and_preserves_purity(tmp_path: Path) -> None:
    output_dir = tmp_path / "tg48a"
    cfg = EdgeKillboxCurriculumConfig(
        output_dir=str(output_dir),
        output_path=str(output_dir / "krk_tg48a_edge_killbox_curriculum.json"),
        markdown_path=str(output_dir / "krk_tg48a_edge_killbox_curriculum.md"),
        train_trace_path=str(output_dir / "pools" / "tg48a_train_traces.jsonl.gz"),
        eval_trace_path=str(output_dir / "pools" / "tg48a_eval_traces.jsonl.gz"),
        failure_pool_path=str(output_dir / "pools" / "tg48a_failure_pool.jsonl.gz"),
        generator_samples_path=str(output_dir / "pools" / "tg48a_generator_samples.jsonl.gz"),
        graph_summary_path=str(output_dir / "pools" / "tg48a_graph_summary.json"),
        run_scale_label="test",
        train_count=3,
        heldout_count=3,
        regression_count=3,
        decoy_count=2,
        hard_decoy_count=2,
        m4_min_positive_support=1,
        m4_min_negative_support=1,
        max_generation_attempts=80_000,
    )

    result = run_edge_killbox_curriculum(config=cfg)
    payload = json.loads(Path(cfg.output_path).read_text(encoding="utf-8"))

    assert result.decision["checkpoint_pass"] is True
    assert payload["decision"]["parent_foundation_weight_delta_during_stage"] == 0
    assert payload["decision"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["decision"]["action_ranker_used_for_runtime"] is False
    assert payload["decision"]["python_final_selector_used"] is False
    assert payload["decision"]["direct_provider_override"] is False
    assert payload["decision"]["stage_labels_learner_visible"] is False
    assert payload["decision"]["tempo_opposition_labels_learner_visible"] is False
    assert Path(cfg.train_trace_path).exists()
    assert Path(cfg.eval_trace_path).exists()
    assert Path(cfg.generator_samples_path).exists()
    assert Path(cfg.graph_summary_path).exists()
