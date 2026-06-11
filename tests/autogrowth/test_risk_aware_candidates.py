import json

from recon_lite_chess.autogrowth import (
    KRKPositionSet,
    RiskAwareCandidateConfig,
    generate_risk_aware_candidates,
    run_risk_aware_candidate_experiment,
    validate_learner_record,
)


def test_m13_generates_recon_action_candidates_from_safe_legal_actions() -> None:
    fens = (
        "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1",
        "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1",
        "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1",
    )
    candidates, summary = generate_risk_aware_candidates(
        fens,
        config=RiskAwareCandidateConfig(
            train_count=3,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            min_support=3,
            max_candidates=4,
            min_candidate_credit=0.01,
            horizon=4,
        ),
    )

    assert summary["total_legal_white_actions_considered"] > 0
    assert summary["candidate_count"] > 0
    assert candidates
    assert candidates[0]["recon_topology_plan"]["node_types"] == [
        "TERMINAL",
        "ACTION",
        "TERMINAL",
        "SCRIPT",
    ]
    assert candidates[0]["behavior_change_applied"] is False
    validate_learner_record(candidates)


def test_m13_risk_aware_experiment_writes_artifact(tmp_path) -> None:
    fen = "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1"
    result = run_risk_aware_candidate_experiment(
        config=RiskAwareCandidateConfig(
            seed=1,
            train_count=3,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            min_support=3,
            max_candidates=4,
            min_candidate_credit=0.01,
            horizon=4,
            activation_max_distance=0.0,
        ),
        positions=KRKPositionSet(
            seed=1,
            train=(fen, fen, fen),
            heldout_weakness=(fen,),
            heldout_broader=(),
        ),
    )
    output = result.write_json(tmp_path / "risk_candidates.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_m13_risk_aware_candidates.v0"
    assert payload["decision"]["move_choice_mediated_by_local_action_nodes"] is True
    assert payload["decision"]["direct_move_override"] is False
    assert payload["generation_summary"]["candidate_count"] > 0
    assert payload["local_arbitration_result"]["schema_version"] == "krk_autogrowth_m12_local_arbitration.v0"
