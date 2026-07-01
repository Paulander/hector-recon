import gzip
import json
from pathlib import Path

import chess

from recon_lite_chess.autogrowth import (
    TG48a2SameSideMicrostageConfig,
    generate_same_side_microstage_datasets,
    run_tg48a2_same_side_microstage,
)
from recon_lite_chess.autogrowth.clean_edge_fence_stage import _load_json
from recon_lite_chess.autogrowth.edge_killbox_curriculum import (
    classify_edge_killbox_family,
    edge_killbox_invariants,
)
from recon_lite_chess.autogrowth.handoff_reachability_audit import _reconstruct_parent_foundation_from_m4_audit
from recon_lite_chess.autogrowth.tg48a2_same_side_microstage import (
    FORBIDDEN_MICROSTAGE_TERMS,
    _micro_success,
    _micro_terminal_keys,
)


def _parent(config: TG48a2SameSideMicrostageConfig):
    parent_artifact = _load_json(config.parent_foundation_artifact_path)
    return _reconstruct_parent_foundation_from_m4_audit(
        parent_artifact=parent_artifact,
        parent_m4_audit_path=config.parent_foundation_m4_audit_path,
    )


def test_tg48a2_generator_focuses_same_side_and_routes_boundary_positive() -> None:
    cfg = TG48a2SameSideMicrostageConfig(
        train_count=4,
        heldout_count=4,
        regression_count=3,
        decoy_count=2,
        hard_decoy_count=2,
        max_generation_attempts=80_000,
    )
    datasets, gate = generate_same_side_microstage_datasets(config=cfg, parent=_parent(cfg))

    for split in ("train", "heldout", "regression"):
        assert len(datasets[split]) == getattr(cfg, f"{split}_count")
        for row in datasets[split]:
            board = chess.Board(row["fen"])
            assert row["family"] == "edge_killbox_same_side_rook_danger"
            assert classify_edge_killbox_family(board) == "edge_killbox_same_side_rook_danger"
            assert edge_killbox_invariants(board)["legal_krk"]
            assert edge_killbox_invariants(board)["black_king_on_edge"]
            assert row["validator_metadata"]["learner_visible_labels"] is False

    assert gate["accepted_hard_decoy_count"] == cfg.hard_decoy_count
    assert gate["hard_decoy_generator_mislabel_count"] == 0
    assert all(row["split"] == "boundary_positive" for row in datasets["boundary_positive"])


def test_tg48a2_micro_terminal_keys_do_not_leak_forbidden_terms() -> None:
    cfg = TG48a2SameSideMicrostageConfig(
        train_count=1,
        heldout_count=1,
        regression_count=1,
        decoy_count=1,
        hard_decoy_count=1,
        max_generation_attempts=80_000,
    )
    datasets, _gate = generate_same_side_microstage_datasets(config=cfg, parent=_parent(cfg))
    board = chess.Board(datasets["train"][0]["fen"])
    keys = [key for move in board.legal_moves for key, _scale in _micro_terminal_keys(board, move)]

    assert keys
    lowered = json.dumps(keys).lower()
    for term in FORBIDDEN_MICROSTAGE_TERMS:
        assert term not in lowered


def test_tg48a2_tiny_run_writes_artifacts_and_preserves_purity(tmp_path: Path) -> None:
    output_dir = tmp_path / "tg48a2_micro"
    cfg = TG48a2SameSideMicrostageConfig(
        output_dir=str(output_dir),
        output_path=str(output_dir / "krk_tg48a2_same_side_microstage.json"),
        markdown_path=str(output_dir / "krk_tg48a2_same_side_microstage.md"),
        train_trace_path=str(output_dir / "pools" / "train.jsonl.gz"),
        eval_trace_path=str(output_dir / "pools" / "eval.jsonl.gz"),
        failure_pool_path=str(output_dir / "pools" / "failure.jsonl.gz"),
        generator_samples_path=str(output_dir / "pools" / "generator.jsonl.gz"),
        boundary_positive_path=str(output_dir / "pools" / "boundary_positive.jsonl.gz"),
        graph_summary_path=str(output_dir / "pools" / "graph.json"),
        board_sample_path=str(output_dir / "pools" / "boards.md"),
        train_count=5,
        heldout_count=4,
        regression_count=3,
        decoy_count=2,
        hard_decoy_count=2,
        m4_min_positive_support=1,
        m4_min_negative_support=1,
        max_generation_attempts=80_000,
    )

    result = run_tg48a2_same_side_microstage(config=cfg)
    payload = json.loads(Path(cfg.output_path).read_text(encoding="utf-8"))

    assert result.decision["checkpoint_pass"] is True
    assert payload["decision"]["same_side_train_count"] == 5
    assert payload["decision"]["same_side_heldout_count"] == 4
    assert payload["decision"]["parent_foundation_weight_delta_during_stage"] == 0
    assert payload["decision"]["parent_foundation_m3_delta_during_stage"] == 0
    assert payload["decision"]["parent_foundation_m4_delta_during_stage"] == 0
    assert payload["decision"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["decision"]["action_ranker_used_for_runtime"] is False
    assert payload["decision"]["python_final_selector_used"] is False
    assert payload["decision"]["direct_provider_override"] is False
    assert payload["decision"]["same_side_labels_learner_visible"] is False
    assert payload["decision"]["hard_decoy_generator_mislabel_count"] == 0
    assert payload["decision"]["hard_decoy_false_handoff_count"] == 0
    assert Path(cfg.train_trace_path).exists()
    assert Path(cfg.eval_trace_path).exists()
    assert Path(cfg.failure_pool_path).exists()
    assert Path(cfg.boundary_positive_path).exists()
    assert Path(cfg.graph_summary_path).exists()
    assert Path(cfg.board_sample_path).exists()

    with gzip.open(cfg.train_trace_path, "rt", encoding="utf-8") as handle:
        train_rows = [json.loads(line) for line in handle]
    assert all(row["split"] != "boundary_positive" for row in train_rows)

    with gzip.open(cfg.eval_trace_path, "rt", encoding="utf-8") as handle:
        eval_rows = [json.loads(line) for line in handle]
    assert all(not row["success"] for row in eval_rows if row["metrics"].get("partial_only_near_basin"))
    assert all(not row["success"] for row in eval_rows if row["metrics"].get("graph_positive_false_basin"))
    assert all(
        not row["metrics"]["validated_entry"]
        for row in eval_rows
        if row["trace_type"] == "TG48a2_decoy_M4" and row["family"] == "hard_decoy_edge_killbox"
    )

    learner_visible = {
        "graph_summary": payload["graph_summary"],
        "candidate_rows": payload["m4_audit"]["candidate_rows"],
    }
    lowered = json.dumps(learner_visible).lower()
    for term in FORBIDDEN_MICROSTAGE_TERMS:
        assert term not in lowered


def test_tg48a2_partial_and_false_basin_do_not_count_as_micro_success() -> None:
    base = {
        "illegal": False,
        "rook_blunder": False,
        "rook_missing": False,
        "stalemate": False,
        "confinement_regression": False,
        "graph_positive_false_basin": False,
        "partial_only_near_basin": False,
        "immediate_checkmate": False,
        "validated_entry": False,
        "mate_conversion_within_horizon": False,
    }
    partial = {
        "metrics": {**base, "partial_only_near_basin": True},
        "safe_lateral_reposition": True,
        "axis_pattern_improved": True,
        "friendly_geometry": True,
    }
    false_basin = {
        "metrics": {**base, "graph_positive_false_basin": True},
        "safe_lateral_reposition": True,
        "axis_pattern_improved": True,
        "friendly_geometry": True,
    }

    assert _micro_success(partial) is False
    assert _micro_success(false_basin) is False
