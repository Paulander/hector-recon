import gzip
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
from recon_lite_chess.autogrowth.tg48a2_same_side_diagnostic import (
    TG48a2SameSideDiagnosticConfig,
    run_tg48a2_same_side_diagnostic,
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
        board_sample_path=str(output_dir / "pools" / "tg48a_repair_board_samples.md"),
        boundary_positive_path=str(output_dir / "pools" / "tg48a_boundary_positive_routed.jsonl.gz"),
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
    if payload["decision"]["behavioral_advancement"]:
        assert payload["decision"]["M4_promoted_affordance_count"] > 0
        assert payload["decision"]["hard_decoy_false_handoff_count"] == 0
        assert payload["decision"]["graph_positive_false_basin_reduced_vs_parent"]
    assert payload["decision"]["parent_foundation_weight_delta_during_stage"] == 0
    assert payload["decision"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["decision"]["action_ranker_used_for_runtime"] is False
    assert payload["decision"]["python_final_selector_used"] is False
    assert payload["decision"]["direct_provider_override"] is False
    assert payload["decision"]["stage_labels_learner_visible"] is False
    assert payload["decision"]["tempo_opposition_labels_learner_visible"] is False
    assert "positive_affordance_candidate_count" in payload["decision"]
    assert "positive_affordance_rejection_reason_counts" in payload["decision"]
    assert Path(cfg.train_trace_path).exists()
    assert Path(cfg.eval_trace_path).exists()
    assert Path(cfg.generator_samples_path).exists()
    assert Path(cfg.graph_summary_path).exists()
    assert Path(cfg.board_sample_path).exists()
    assert Path(cfg.boundary_positive_path).exists()
    assert "TG48a Repair Board Samples" in Path(cfg.board_sample_path).read_text(encoding="utf-8")
    assert "hard_decoy_generator_mislabel_count" in payload["decision"]
    assert "true_hard_decoy_leak_count" in payload["decision"]
    assert "boundary_positive_routed_count" in payload["decision"]
    assert (
        payload["decision"]["hard_decoy_false_handoff_count_after_excluding_generator_mislabels"]
        == payload["decision"]["true_hard_decoy_leak_count"]
    )
    assert payload["decision"]["hard_decoy_generator_mislabel_count"] == 0
    assert payload["decision"]["true_hard_decoy_leak_count"] == 0
    assert (
        payload["decision"]["boundary_positive_routed_count"]
        == payload["hard_decoy_gate"]["boundary_positive_routed_count"]
    )

    with gzip.open(cfg.eval_trace_path, "rt", encoding="utf-8") as handle:
        eval_rows = [json.loads(line) for line in handle]
    assert all(
        not row["success"]
        for row in eval_rows
        if row["metrics"].get("graph_positive_false_basin")
    )
    assert all(
        not row["metrics"]["validated_entry"]
        for row in eval_rows
        if row["trace_type"] == "TG48a_decoy_M4" and row["family"] == "hard_decoy_edge_killbox"
    )
    assert all(not row["success"] for row in eval_rows if row["metrics"].get("partial_only_near_basin"))

    with gzip.open(cfg.train_trace_path, "rt", encoding="utf-8") as handle:
        train_rows = [json.loads(line) for line in handle]
    assert all(row["split"] != "boundary_positive" for row in train_rows)
    assert all(row["family"] != "boundary_positive_edge_killbox" for row in train_rows)

    with gzip.open(cfg.boundary_positive_path, "rt", encoding="utf-8") as handle:
        boundary_rows = [json.loads(line) for line in handle]
    assert len(boundary_rows) == payload["decision"]["boundary_positive_routed_count"]
    assert all(row["split"] == "boundary_positive" for row in boundary_rows)
    assert all(row["validator_metadata"]["learner_visible_labels"] is False for row in boundary_rows)

    for row in payload["m4_audit"]["candidate_rows"]:
        key = row["terminal_key"]
        forbidden = ("stage", "basin", "curriculum", "tempo", "opposition", "quality", "reply_policy")
        assert not any(term in key.lower() for term in forbidden)

    assert payload["decision"]["parent_foundation_m3_delta_during_stage"] == 0
    assert payload["decision"]["parent_foundation_m4_delta_during_stage"] == 0


def test_tg48a2_diagnostic_classifies_hard_decoy_and_keeps_slices_separate(tmp_path: Path) -> None:
    output_dir = tmp_path / "tg48a2"
    cfg = TG48a2SameSideDiagnosticConfig(
        output_dir=str(output_dir),
        output_path=str(output_dir / "krk_tg48a2_same_side_diagnostic.json"),
        markdown_path=str(output_dir / "krk_tg48a2_same_side_diagnostic.md"),
        hard_decoy_relabel_path=str(output_dir / "pools" / "tg48a2_hard_decoy_relabel_audit.jsonl.gz"),
        hard_decoy_markdown_path=str(output_dir / "tg48a2_hard_decoy_relabel_audit.md"),
        same_side_slice_path=str(output_dir / "pools" / "tg48a2_same_side_slice.jsonl.gz"),
        same_side_markdown_path=str(output_dir / "tg48a2_same_side_slice.md"),
        terminal_precision_path=str(output_dir / "pools" / "tg48a2_terminal_precision_audit.jsonl.gz"),
        same_side_count=3,
        max_generation_attempts=80_000,
        top_rejected_affordance_count=3,
    )

    result = run_tg48a2_same_side_diagnostic(config=cfg)
    payload = json.loads(Path(cfg.output_path).read_text(encoding="utf-8"))

    assert result.decision["checkpoint_pass"] is True
    assert payload["decision"]["hard_decoy_false_handoff_count"] > 0
    assert (
        payload["decision"]["hard_decoy_generator_strict_mislabel_count"]
        + payload["decision"]["legitimate_boundary_positive_count"]
        + payload["decision"]["true_hard_decoy_leak_count"]
        + payload["decision"]["partial_only_boundary_count"]
        + payload["decision"]["validator_bug_count"]
        + payload["decision"]["ambiguous_hard_decoy_count"]
        == payload["decision"]["hard_decoy_false_handoff_count"]
    )
    assert payload["decision"]["parent_frozen_deltas"] == {"m3": 0, "m4": 0, "weight": 0}
    assert payload["decision"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["decision"]["action_ranker_used_for_runtime"] is False
    assert payload["decision"]["python_final_selector_used"] is False
    assert payload["decision"]["direct_provider_override"] is False
    assert payload["decision"]["stage_labels_learner_visible"] is False
    assert payload["decision"]["basin_labels_learner_visible"] is False
    assert payload["decision"]["curriculum_labels_learner_visible"] is False
    assert payload["decision"]["tempo_opposition_labels_learner_visible"] is False

    with gzip.open(cfg.hard_decoy_relabel_path, "rt", encoding="utf-8") as handle:
        hard_rows = [json.loads(line) for line in handle]
    assert hard_rows
    assert all(row["classification"] for row in hard_rows)
    assert all(
        not row["partial_only"] or row["classification"] == "partial_only_boundary"
        for row in hard_rows
    )

    with gzip.open(cfg.same_side_slice_path, "rt", encoding="utf-8") as handle:
        same_rows = [json.loads(line) for line in handle]
    assert len(same_rows) == 3
    assert {row["family"] for row in same_rows} == {"edge_killbox_same_side_rook_danger"}
    assert all("edge_killbox_opposed_side" not in row["family"] for row in same_rows)

    with gzip.open(cfg.terminal_precision_path, "rt", encoding="utf-8") as handle:
        terminal_rows = [json.loads(line) for line in handle]
    assert terminal_rows
    for row in terminal_rows:
        for key in (
            "decoy_activation_count",
            "hard_decoy_activation_count",
            "unsafe_activation_count",
            "same_side_activation_count",
            "opposed_side_activation_count",
            "validated_success_activation_count",
            "false_basin_activation_count",
        ):
            assert key in row
        assert not any(
            term in row["terminal_key"].lower()
            for term in ("stage", "basin", "curriculum", "tempo", "opposition", "quality", "reply_policy")
        )
