import json

from recon_lite_chess.autogrowth import (
    KRKPositionSet,
    RetryCandidateExpansionConfig,
    mine_retry_expansion_candidates,
    run_retry_candidate_expansion,
    validate_learner_record,
)


def test_tg23_mines_retry_context_script_candidates() -> None:
    contexts = [
        {
            "classification": "no_local_sibling_available",
            "fen_before": "8/k7/8/2K5/8/1R6/8/8 w - - 2 2",
            "position_index": 1,
        }
    ]

    candidates, summary = mine_retry_expansion_candidates(
        contexts,
        config=RetryCandidateExpansionConfig(
            min_support=1,
            max_expansion_candidates=3,
            min_sequence_credit=-10.0,
        ),
    )

    assert summary["retry_contexts_considered"] == 1
    assert summary["expansion_candidate_count"] > 0
    assert candidates
    assert candidates[0]["script_plan"]["node_type"] == "SCRIPT"
    assert candidates[0]["script_plan"]["relation_plan"]["chooses_move_directly"] is False
    assert candidates[0]["retry_context_expansion"]["chooses_move_directly"] is False
    validate_learner_record(candidates)


def test_tg23_retry_candidate_expansion_writes_artifact(tmp_path) -> None:
    fen = "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1"
    result = run_retry_candidate_expansion(
        config=RetryCandidateExpansionConfig(
            seed=1,
            train_count=2,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            min_support=1,
            max_candidates=2,
            max_expansion_candidates=2,
            horizons=(4,),
            min_sequence_credit=0.01,
            activation_max_distance=1.0,
            after_max_distance=4.0,
            chain_max_distance=4.0,
            max_chain_edges=8,
        ),
        positions=KRKPositionSet(seed=1, train=(fen, fen), heldout_weakness=(fen,), heldout_broader=()),
    )
    output = result.write_json(tmp_path / "tg23_retry_candidate_expansion.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_tg23_retry_candidate_expansion.v0"
    assert payload["local_recon_structure"]["expansion_candidates_active_only_as_local_siblings"] is True
    assert payload["local_recon_structure"]["direct_move_override"] is False
    assert payload["decision"]["direct_move_override"] is False
    assert "expanded_retry" in payload["arms"]
