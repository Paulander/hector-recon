import json

from recon_lite_chess.autogrowth import (
    KRKPositionSet,
    LocalScriptConfig,
    ScriptFragmentConfig,
    generalize_script_candidates_to_fragments,
    generate_local_script_candidates,
    run_script_fragment_experiment,
    validate_learner_record,
)


def test_m16_generalizes_script_candidates_to_local_fragments() -> None:
    fens = (
        "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1",
        "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1",
    )
    exact_candidates, _summary = generate_local_script_candidates(
        fens,
        config=LocalScriptConfig(
            train_count=2,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            min_support=1,
            max_candidates=2,
            min_sequence_credit=0.01,
            horizon=4,
        ),
    )

    fragments = generalize_script_candidates_to_fragments(
        exact_candidates,
        fragment_feature_names=("black_king_nearest_edge_distance", "rook_attacked_by_black", "is_check"),
    )

    assert fragments
    assert fragments[0]["candidate_key"].startswith("m16_fragment_")
    assert fragments[0]["source_candidate_key"] == exact_candidates[0]["candidate_key"]
    assert fragments[0]["subcondition_fragment"]["node_type"] == "TERMINAL"
    assert fragments[0]["subcondition_fragment"]["chooses_move_directly"] is False
    assert fragments[0]["script_plan"]["node_type"] == "SCRIPT"
    assert len(fragments[0]["script_plan"]["actions"]) == 2
    assert fragments[0]["script_plan"]["relation_plan"]["fragment_confirmation_relation"] == "SUR"
    assert fragments[0]["script_plan"]["relation_plan"]["chooses_move_directly"] is False
    validate_learner_record(fragments)


def test_m16_fragment_experiment_writes_readiness_artifact(tmp_path) -> None:
    fen = "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1"
    result = run_script_fragment_experiment(
        config=ScriptFragmentConfig(
            seed=1,
            train_count=2,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            min_support=1,
            max_candidates=2,
            min_sequence_credit=0.01,
            horizon=4,
            activation_max_distance=1.0,
            fragment_feature_names=("black_king_nearest_edge_distance", "rook_attacked_by_black", "is_check"),
        ),
        positions=KRKPositionSet(seed=1, train=(fen, fen), heldout_weakness=(fen,), heldout_broader=()),
    )
    output = result.write_json(tmp_path / "script_fragments.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_m16_script_fragments.v0"
    assert payload["local_recon_structure"]["fragment_confirms_script_locally"] is True
    assert payload["local_recon_structure"]["direct_move_override"] is False
    assert payload["generation_summary"]["fragment_candidate_count"] > 0
    assert "partial_curriculum_ready" in payload["decision"]
