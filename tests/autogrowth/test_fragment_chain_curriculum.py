import json

import chess

from recon_lite_chess.autogrowth import (
    FragmentChainCurriculumConfig,
    KRKPositionSet,
    evaluate_fragment_chain_arm,
    run_fragment_chain_curriculum,
)


def test_tg18_empty_chain_arm_falls_back_without_override() -> None:
    metrics, outcomes = evaluate_fragment_chain_arm(
        ["8/8/8/8/2K5/6k1/2R5/8 w - - 0 1"],
        script_nodes=[],
        chain_adjacency={},
        horizon=4,
        activation_max_distance=0.5,
        after_max_distance=1.5,
        chain_request_bonus=0.75,
        eta_m3=0.08,
        update_nodes=False,
    )

    assert metrics.chain_start_count == 0
    assert metrics.chain_step_count == 0
    assert metrics.baseline_fallback_count > 0
    assert outcomes[0]["candidate_move_count"] == 0


def test_tg18_curriculum_writes_machine_readable_artifact(tmp_path) -> None:
    fen = "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1"
    result = run_fragment_chain_curriculum(
        config=FragmentChainCurriculumConfig(
            seed=1,
            train_count=2,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            min_support=1,
            max_candidates=2,
            horizons=(4,),
            min_sequence_credit=0.01,
            activation_max_distance=1.0,
            after_max_distance=4.0,
            chain_max_distance=4.0,
            max_chain_edges=8,
        ),
        positions=KRKPositionSet(seed=1, train=(fen, fen), heldout_weakness=(fen,), heldout_broader=()),
    )
    output = result.write_json(tmp_path / "tg18.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_tg18_fragment_chain_curriculum.v0"
    assert payload["local_recon_structure"]["move_choice_mediated_by_local_script_nodes"] is True
    assert payload["local_recon_structure"]["direct_move_override"] is False
    assert payload["local_recon_structure"]["selector_behavior_enabled"] is False
    assert "baseline" in payload["arms"]
    assert "sham_fragment_chain" in payload["arms"]
    assert "real_fragment_chain" in payload["arms"]
    assert payload["decision"]["runtime_tablebase_or_dtm_move_source"] is False


def test_tg18_chess_import_remains_available_for_position_contract() -> None:
    assert chess.Board("8/8/8/8/2K5/6k1/2R5/8 w - - 0 1").turn == chess.WHITE
