import json

import chess

from recon_lite_chess.autogrowth import (
    KRKPositionSet,
    LocalScriptConfig,
    choose_local_script_action,
    generate_local_script_candidates,
    run_local_script_experiment,
    validate_learner_record,
)


def test_m15_generates_local_script_candidates() -> None:
    fens = (
        "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1",
        "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1",
    )
    candidates, summary = generate_local_script_candidates(
        fens,
        config=LocalScriptConfig(
            train_count=2,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            min_support=1,
            max_candidates=4,
            min_sequence_credit=0.01,
            horizon=4,
        ),
    )

    assert summary["first_step_actions_considered"] > 0
    assert summary["candidate_count"] > 0
    assert candidates
    assert candidates[0]["status"] == "m15_local_script_not_spawned"
    assert candidates[0]["script_plan"]["node_type"] == "SCRIPT"
    assert len(candidates[0]["script_plan"]["actions"]) == 2
    assert candidates[0]["script_plan"]["relation_plan"]["chooses_move_directly"] is False
    validate_learner_record(candidates)


def test_m15_script_choice_requires_script_node() -> None:
    decision = choose_local_script_action(
        chess.Board("8/8/8/8/2K5/6k1/2R5/8 w - - 0 1"),
        script_nodes=[],
        active_script=None,
        activation_max_distance=0.0,
    )

    assert decision["move"] is None


def test_m15_local_script_experiment_writes_artifact(tmp_path) -> None:
    fen = "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1"
    result = run_local_script_experiment(
        config=LocalScriptConfig(
            seed=1,
            train_count=2,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            min_support=1,
            max_candidates=4,
            min_sequence_credit=0.01,
            horizon=4,
            activation_max_distance=0.0,
        ),
        positions=KRKPositionSet(seed=1, train=(fen, fen), heldout_weakness=(fen,), heldout_broader=()),
    )
    output = result.write_json(tmp_path / "local_scripts.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_m15_local_script_candidates.v0"
    assert payload["local_recon_structure"]["move_choice_mediated_by_local_script_nodes"] is True
    assert payload["decision"]["direct_move_override"] is False
    assert payload["generation_summary"]["candidate_count"] > 0
