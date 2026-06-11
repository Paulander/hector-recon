import json

from recon_lite_chess.autogrowth import (
    GrowthTrainingConfig,
    load_candidate_pool,
    train_growth_candidates,
    validate_learner_record,
)


def test_m8_growth_training_updates_candidate_lifecycle() -> None:
    candidates = load_candidate_pool(
        "reports/autogrowth/krk_autogrowth_m4_candidates_smoke.json",
        candidate_count=4,
    )
    result = train_growth_candidates(
        config=GrowthTrainingConfig(
            seed=20260610,
            train_count=12,
            heldout_weakness_count=4,
            heldout_broader_count=4,
            candidate_path="unused",
            candidate_count=4,
            cycles=2,
            train_horizon=16,
            eval_horizon=16,
            prune_max_rook_losses=0,
        ),
        candidates=candidates,
    )
    payload = result.to_dict()

    assert payload["schema_version"] == "krk_autogrowth_m8_training.v0"
    assert payload["summary"]["candidate_nodes_spawned"] == 4
    assert payload["summary"]["m3_update_count"] > 0
    assert payload["cycle_summaries"]
    assert any(
        state["experience_count"] > 0
        for state in payload["candidate_lifecycle"].values()
    )
    assert payload["heldout"]["learning_decision"]["decision"] in {"promote", "quarantine"}
    validate_learner_record(payload["candidates"])


def test_m8_growth_training_writes_json_artifact(tmp_path) -> None:
    candidates = load_candidate_pool(
        "reports/autogrowth/krk_autogrowth_m4_candidates_smoke.json",
        candidate_count=3,
    )
    result = train_growth_candidates(
        config=GrowthTrainingConfig(
            seed=7,
            train_count=8,
            heldout_weakness_count=3,
            heldout_broader_count=3,
            candidate_path="unused",
            candidate_count=3,
            cycles=1,
            train_horizon=10,
            eval_horizon=10,
        ),
        candidates=candidates,
    )
    output = result.write_json(tmp_path / "training.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["summary"]["candidate_nodes_spawned"] == 3
    assert "candidate_lifecycle" in payload
    assert "heldout" in payload
    assert payload["summary"]["m4_consolidation_event_count"] in {0, 1}
