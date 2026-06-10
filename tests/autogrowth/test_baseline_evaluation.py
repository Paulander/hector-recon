import json

from recon_lite_chess.autogrowth import (
    EvaluationConfig,
    evaluate_baseline_and_sham,
    generate_position_sets,
)


def test_baseline_and_sham_are_identical_without_candidate() -> None:
    positions = generate_position_sets(
        seed=2026,
        train_count=5,
        heldout_weakness_count=3,
        heldout_broader_count=3,
    )
    result = evaluate_baseline_and_sham(
        config=EvaluationConfig(
            seed=2026,
            train_count=5,
            heldout_weakness_count=3,
            heldout_broader_count=3,
            horizons=(4, 8),
        ),
        positions=positions,
    )
    payload = result.to_dict()

    assert payload["decision"]["autogrowth_candidate_enabled"] is False
    assert payload["decision"]["selector_behavior_enabled"] is False
    assert payload["decision"]["runtime_tablebase_or_dtm_provider"] is False
    assert payload["learning_counters"]["candidate_nodes_spawned"] == 0
    assert payload["learning_counters"]["m3_update_count"] == 0
    assert payload["arms"]["baseline"]["4"]["total"] == 6
    assert payload["arms"]["baseline"]["8"]["total"] == 6
    assert "rook_losses" in payload["arms"]["baseline"]["4"]
    assert "draws" in payload["arms"]["baseline"]["4"]
    assert payload["arms"]["baseline"]["4"]["mates"] == payload["arms"]["sham_growth"]["4"]["mates"]
    assert payload["arms"]["baseline"]["8"]["mates"] == payload["arms"]["sham_growth"]["8"]["mates"]
    assert payload["paired_deltas"]["4"]["outcome_changed_count"] == 0
    assert payload["paired_deltas"]["8"]["outcome_changed_count"] == 0


def test_evaluation_writes_minimal_json_artifact(tmp_path) -> None:
    result = evaluate_baseline_and_sham(
        config=EvaluationConfig(
            seed=5,
            train_count=3,
            heldout_weakness_count=2,
            heldout_broader_count=2,
            horizons=(4,),
        )
    )
    output = result.write_json(tmp_path / "baseline.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_m1_m3_baseline.v0"
    assert payload["dataset"]["train_count"] == 3
    assert payload["dataset"]["heldout_count"] == 4
    assert set(payload["arms"]) == {"baseline", "sham_growth"}
    assert "reports/strategy_arbitration" not in json.dumps(payload)
    assert "reports/structural_candidates" not in json.dumps(payload)
