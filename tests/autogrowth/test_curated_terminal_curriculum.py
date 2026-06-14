import json

import chess

from recon_lite_chess.autogrowth import (
    ContextGatedCurriculumConfig,
    CuratedReplayCurriculumConfig,
    CuratedTerminalCurriculumConfig,
    context_terminal_keys,
    curated_stage_entries,
    run_context_gated_curriculum,
    run_curated_replay_curriculum,
    run_curated_terminal_curriculum,
    stage_inventory,
    train_context_gated_foundation_bundle,
    validate_learner_record,
)
from recon_lite_chess.autogrowth.curated_stockfish_validation import (
    _exact_classification,
    _mate_two_claim_entries,
    _stockfish_classification,
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


def test_tg26j_stockfish_validator_scope_and_exact_classification() -> None:
    claims = _mate_two_claim_entries(include_symmetries=False)
    mate_stage_claims = [entry for entry in claims if entry.stage_name == "Mate_In_2"]

    assert len(mate_stage_claims) == 5
    assert {
        _exact_classification(chess.Board(entry.fen))["classification"]
        for entry in mate_stage_claims
    } == {"strict_forced_mate_in_two"}
    assert _stockfish_classification(2) == "stockfish_mate_in_2"


def test_tg26k_curated_replay_curriculum_records_growth_and_replay(tmp_path) -> None:
    result = run_curated_replay_curriculum(
        config=CuratedReplayCurriculumConfig(
            include_symmetries=False,
            train_repetitions=1,
            replay_repetitions=1,
            mate1_regression_threshold=0.80,
            mate2_bucket_threshold=0.0,
            mate2_cumulative_threshold=0.0,
            max_samples=8,
        )
    )
    payload = result.to_dict()
    output = result.write_json(tmp_path / "tg26k.json")

    assert output.exists()
    assert payload["schema_version"] == "krk_autogrowth_tg26k_curated_replay_curriculum.v0"
    assert payload["purity_boundary"]["stage_labels_learner_visible"] is False
    assert payload["dataset"]["mate2_bucket_count"] == 5
    assert payload["mate1_foundation"]["training"]["m3_update_count"] > 0
    assert payload["mate2_bucket_sequence"][0]["growth"]["m3_update_delta"] > 0
    assert payload["mate2_bucket_sequence"][1]["replay"]["prior_replay_position_count"] > 0
    assert payload["final_evaluation"]["terminal_substrate"]["mate2_first_terminal_count"] > 0


def test_tg26l_context_gated_curriculum_uses_generic_terminal_gates(tmp_path) -> None:
    board = chess.Board("1k6/8/K7/8/8/8/8/R7 w - - 0 1")
    keys = context_terminal_keys(board)
    assert keys
    assert all(key.startswith("before_terminal:") for key in keys)

    result = run_context_gated_curriculum(
        config=ContextGatedCurriculumConfig(
            include_symmetries=False,
            train_repetitions=1,
            gate_granularity="position",
            gate_min_overlap=0.72,
            mate2_threshold=0.0,
            max_samples=8,
        )
    )
    payload = result.to_dict()
    output = result.write_json(tmp_path / "tg26l.json")

    assert output.exists()
    assert payload["schema_version"] == "krk_autogrowth_tg26l_context_gated_curriculum.v0"
    assert payload["purity_boundary"]["stage_labels_learner_visible"] is False
    assert payload["purity_boundary"]["direct_provider_override"] is False
    assert payload["dataset"]["gate_granularity"] == "position"
    assert payload["dataset"]["mate2_gate_context_count"] >= payload["dataset"]["mate2_bucket_count"]
    assert payload["evaluation"]["gate_activation_summary"]["no_confirmed_gate_count"] == 0
    assert payload["training"]["mate2_first_terminal_count_by_bucket"]


def test_tg26l_context_gated_foundation_bundle_exposes_runtime_handoff() -> None:
    bundle = train_context_gated_foundation_bundle(
        config=ContextGatedCurriculumConfig(
            include_symmetries=False,
            train_repetitions=1,
            gate_granularity="position",
            gate_min_overlap=0.72,
            mate2_threshold=0.0,
            max_samples=4,
        )
    )
    board = chess.Board(bundle.mate2_fens[0])
    first = bundle.mate2_first_learner.choose(board)

    assert bundle.payload["schema_version"] == "krk_autogrowth_tg26l_context_gated_curriculum.v0"
    assert bundle.payload["training"]["mate1_self_evaluation"]["accuracy"] >= 0.0
    assert first is not None
    assert bundle.mate2_first_learner.choose_first(board)[1]["had_confirmed_gate"] is True
