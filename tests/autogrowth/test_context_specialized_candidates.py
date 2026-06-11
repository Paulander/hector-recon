import json

from recon_lite_chess.autogrowth import (
    CONTEXT_SPECIALIZED_FEATURES,
    ContextSpecializedCandidateConfig,
    KRKPositionSet,
    generate_context_specialized_candidates,
    run_context_specialized_candidate_experiment,
    validate_learner_record,
)


def test_m14_generates_full_context_action_candidates() -> None:
    fens = (
        "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1",
        "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1",
    )
    candidates, summary = generate_context_specialized_candidates(
        fens,
        config=ContextSpecializedCandidateConfig(
            train_count=2,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            min_support=1,
            max_candidates=4,
            min_candidate_credit=0.01,
            horizon=4,
        ),
    )

    assert summary["context_feature_count"] == len(CONTEXT_SPECIALIZED_FEATURES)
    assert summary["candidate_count"] > 0
    assert candidates
    assert candidates[0]["status"] == "m14_context_specialized_not_spawned"
    assert candidates[0]["before_cluster"]["feature_names"] == list(CONTEXT_SPECIALIZED_FEATURES)
    validate_learner_record(candidates)


def test_m14_context_experiment_writes_artifact(tmp_path) -> None:
    fen = "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1"
    result = run_context_specialized_candidate_experiment(
        config=ContextSpecializedCandidateConfig(
            seed=1,
            train_count=2,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            min_support=1,
            max_candidates=4,
            min_candidate_credit=0.01,
            horizon=4,
            activation_max_distance=0.0,
        ),
        positions=KRKPositionSet(
            seed=1,
            train=(fen, fen),
            heldout_weakness=(fen,),
            heldout_broader=(),
        ),
    )
    output = result.write_json(tmp_path / "context_candidates.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_m14_context_specialized_candidates.v0"
    assert payload["decision"]["move_choice_mediated_by_local_action_nodes"] is True
    assert payload["decision"]["direct_move_override"] is False
    assert payload["generation_summary"]["candidate_count"] > 0
    assert payload["local_arbitration_result"]["schema_version"] == "krk_autogrowth_m12_local_arbitration.v0"
