from __future__ import annotations

from pathlib import Path

from recon_lite_hector.benchmarks.planted_composition import (
    BenchmarkConfig,
    NativeBooleanComposite,
    build_dataset,
    build_frequency_widened_policy,
    build_matched_random_policy,
    build_point_policy,
    discover_composite,
    evaluate_policy,
    fit_atom_only_policy,
    run_planted_composition_certification,
)


def test_balanced_xor_has_zero_single_atom_information_and_atom_policy_is_chance() -> None:
    dataset = build_dataset(BenchmarkConfig(dataset_salt="unit-test"))
    train = dataset["train"]
    policy = fit_atom_only_policy(train, dataset["atom_ids"])
    result = evaluate_policy(policy, train, arm="atom_only", seed=11)

    assert result["win_rate"] == 0.5
    assert set(policy.weights.values()) == {0}
    for atom_id in dataset["atom_ids"]:
        for value in (False, True):
            labels = [row.correct_action for row in train if row.atoms[atom_id] is value]
            assert labels.count("A") == labels.count("B")


def test_native_and_xor_and_k_of_n_truth_tables() -> None:
    and_cell = NativeBooleanComposite("and", (("p", True), ("q", True)), operator="and")
    xor_cell = NativeBooleanComposite("xor", (("p", True), ("q", True)), operator="xor")
    quorum = NativeBooleanComposite(
        "quorum",
        (("p", True), ("q", True), ("r", True)),
        operator="k_of_n",
        k=2,
    )

    assert [and_cell.evaluate({"p": p, "q": q}).confirmed for p, q in ((False, False), (False, True), (True, False), (True, True))] == [False, False, False, True]
    assert [xor_cell.evaluate({"p": p, "q": q}).confirmed for p, q in ((False, False), (False, True), (True, False), (True, True))] == [False, True, True, False]
    assert quorum.evaluate({"p": True, "q": False, "r": True}).confirmed is True
    assert quorum.evaluate({"p": True, "q": False, "r": False}).confirmed is False


def test_group_splits_are_disjoint_and_final_rows_are_frozen() -> None:
    dataset = build_dataset(BenchmarkConfig(dataset_salt="unit-test"))
    groups = {split: {row.group_id for row in dataset[split]} for split in ("train", "validation", "final_test")}
    assert groups["train"].isdisjoint(groups["validation"])
    assert groups["train"].isdisjoint(groups["final_test"])
    assert groups["validation"].isdisjoint(groups["final_test"])
    assert dataset["manifest"]["final_test"]["sha256"]


def test_blind_candidate_enumeration_recovers_behavioral_xor() -> None:
    dataset = build_dataset(BenchmarkConfig(dataset_salt="unit-test"))
    discovery = discover_composite(
        dataset["train"],
        dataset["validation"],
        dataset["atom_ids"],
        seed=11,
    )
    assert discovery["selected_validation_accuracy"] == 1.0
    assert discovery["truth_table_equivalent"] is True
    assert discovery["candidate_generation_used_target_rule"] is False
    assert discovery["selected_cell_state"] == "MATURE"


def test_content_blind_widening_beats_points_and_matched_random_on_unseen_groups() -> None:
    dataset = build_dataset(BenchmarkConfig(dataset_salt="unit-test"))
    atom = fit_atom_only_policy(dataset["train"], dataset["atom_ids"])
    points = build_point_policy(dataset["train"], dataset["atom_ids"], fallback=atom)
    widened = build_frequency_widened_policy(
        dataset["train"], dataset["atom_ids"], width=2, seed=11, fallback=atom
    )
    random_control = build_matched_random_policy(
        dataset["train"], dataset["atom_ids"], widened, seed=11, fallback=atom
    )
    point_eval = evaluate_policy(points, dataset["validation"], arm="points", seed=11)
    wide_eval = evaluate_policy(widened, dataset["validation"], arm="widened", seed=11)
    random_eval = evaluate_policy(random_control, dataset["validation"], arm="random", seed=11)

    assert wide_eval["win_rate"] == 1.0
    assert point_eval["win_rate"] == 0.5
    assert random_eval["win_rate"] == 0.5
    assert wide_eval["valid_predicate_evaluated_coverage"] > point_eval["valid_predicate_evaluated_coverage"]
    assert wide_eval["valid_predicate_evaluated_coverage"] > random_eval["valid_predicate_evaluated_coverage"]
    assert random_control.population_size == widened.population_size
    assert random_control.training_firing_rate == widened.training_firing_rate


def test_full_certification_writes_compact_artifacts_and_touches_final_once(tmp_path: Path) -> None:
    summary = run_planted_composition_certification(
        config=BenchmarkConfig(output_dir=str(tmp_path / "certification"), dataset_salt="unit-test")
    )

    assert summary["engine_semantic_pass"] is True
    assert summary["measurement_pass"] is True
    assert summary["discovery_pass"] is True
    assert summary["widening_pass"] is True
    assert summary["causal_ablation_pass"] is True
    assert summary["final_test"]["touch_count"] == 1
    assert summary["stop_reason"] is None
    assert len(summary["per_seed"]) == 5
    assert (tmp_path / "certification" / "rows.jsonl").stat().st_size < 5_000_000
