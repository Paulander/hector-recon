import json

from recon_lite_chess.autogrowth import (
    SingleGraphCurriculumConfig,
    run_single_graph_curriculum,
    validate_learner_record,
)


def test_tg26n_single_graph_curriculum_contract(tmp_path) -> None:
    result = run_single_graph_curriculum(
        config=SingleGraphCurriculumConfig(
            include_symmetries=False,
            train_repetitions=1,
            continuation_repetitions=1,
            mate1_threshold=0.0,
            mate2_threshold=0.0,
            max_samples=4,
        )
    )
    output = result.write_json(tmp_path / "tg26n.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_tg26n_single_graph_curriculum.v0"
    assert payload["purity_boundary"]["one_persistent_recon_graph_across_curriculum"] is True
    assert payload["purity_boundary"]["separate_mate1_or_mate2_networks"] is False
    assert payload["purity_boundary"]["hardcoded_mate1_handoff"] is False
    assert payload["purity_boundary"]["direct_provider_override"] is False
    assert payload["purity_boundary"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["config"]["normalize_terminal_activation"] is True
    assert payload["maturation"]["matured_terminal_count"] > 0
    assert payload["maturation"]["matured_triplet_count"] > 0
    assert payload["mate2"]["training"]["continuation_experience_uses_same_graph"] is True
    assert payload["mate2"]["evaluation"]["hardcoded_mate1_handoff"] is False
    assert payload["mate2"]["evaluation"]["same_graph_second_move_count"] > 0
    assert payload["graph"]["single_persistent_graph"] is True
    assert payload["graph"]["separate_stage_networks"] is False
    assert payload["graph"]["triplet_count"] > 0
    validate_learner_record(payload["graph"]["top_positive_triplets"])


def test_tg26n_triplets_are_structural_not_direct_move_provider() -> None:
    result = run_single_graph_curriculum(
        config=SingleGraphCurriculumConfig(
            include_symmetries=False,
            train_repetitions=1,
            continuation_repetitions=1,
            mate1_threshold=0.0,
            mate2_threshold=0.0,
            max_samples=2,
        )
    )
    payload = result.to_dict()
    triplets = payload["graph"]["top_positive_triplets"]

    assert triplets
    assert all(item["represented_as"] == "before_terminal -> action_delta -> after_terminal" for item in triplets)
    assert all(item["chooses_move_directly"] is False for item in triplets)
    assert all(item["stem_cell_state"] in {"TRIAL", "MATURE"} for item in triplets)
