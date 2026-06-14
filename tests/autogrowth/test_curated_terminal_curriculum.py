import json

from recon_lite_chess.autogrowth import (
    CuratedTerminalCurriculumConfig,
    curated_stage_entries,
    run_curated_terminal_curriculum,
    stage_inventory,
    validate_learner_record,
)
from recon_lite_chess.autogrowth.terminal_substrate import (
    TerminalSubstrateConfig,
    train_terminal_foundation_bundle,
)


def test_tg26j_curated_stage_inventory_separates_foundation_from_later_rollout() -> None:
    entries = curated_stage_entries(include_symmetries=False)
    inventory = stage_inventory(entries)

    assert inventory["source"].endswith("krk_curriculum.py::KRK_STAGES")
    assert inventory["by_stage"]["Mate_In_1"]["mate_in_one_count"] > 0
    assert inventory["by_stage"]["Mate_In_2"]["forced_mate_in_two_count"] > 0
    assert any(
        stage["later_graded_rollout_count"] > 0
        for stage in inventory["by_stage"].values()
    )
    validate_learner_record(inventory["examples"]["forced_mate_in_two"])


def test_tg26j_curated_terminal_curriculum_artifact_contract(tmp_path) -> None:
    result = run_curated_terminal_curriculum(
        config=CuratedTerminalCurriculumConfig(
            train_repetitions=1,
            max_samples=4,
        )
    )
    output = result.write_json(tmp_path / "tg26j.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_tg26j_curated_terminal_curriculum.v0"
    assert payload["purity_boundary"]["stage_labels_learner_visible"] is False
    assert payload["purity_boundary"]["direct_provider_override"] is False
    assert payload["original_position_run"]["dataset"]["source_labels_learner_visible"] is False
    assert payload["original_position_run"]["mate1"]["evaluation"]["position_count"] > 0
    assert payload["original_position_run"]["mate2"]["evaluation"]["position_count"] > 0
    assert payload["original_position_run"]["mate1"]["training"]["m3_update_count"] > 0
    assert payload["original_position_run"]["mate2"]["training"]["first_learner_m3_update_count"] > 0


def test_tg26h_terminal_bundle_preserves_mate2_fen_provenance() -> None:
    bundle = train_terminal_foundation_bundle(
        config=TerminalSubstrateConfig(
            seed=2691,
            mate1_train_count=40,
            mate1_heldout_count=10,
            mate1_mirror_count=4,
            mate2_train_count=3,
            mate2_heldout_count=2,
            mate1_pass_threshold=0.70,
            mate2_pass_threshold=0.0,
            max_generation_attempts=120_000,
            max_samples=2,
        )
    )

    assert len(bundle.mate2_train) == 3
    assert len(bundle.mate2_heldout) == 2
    assert bundle.payload["mate2"]["dataset"]["train_count"] == 3
    assert bundle.payload["mate2"]["dataset"]["heldout_count"] == 2
