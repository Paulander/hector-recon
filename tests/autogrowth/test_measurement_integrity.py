from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
import hashlib
import json

import pytest

from recon_lite_chess.autogrowth import persistent_staged_ladder as ladder
from recon_lite_chess.autogrowth.stage_b_ecological_discovery_probe import StageBEcologicalDiscoveryConfig

from recon_lite_chess.autogrowth.measurement_integrity import (
    CounterfactualSnapshot,
    RETIRED_DEVELOPMENT_ROW_IDS,
    apply_live_routing_weight,
    assert_complete_arm_record,
    assert_final_test_untouched,
    assert_noop_parity,
    counterfactual_plan,
    holm_adjusted_pvalues,
    live_population_item,
    paired_binary_outcomes,
    validate_analysis_population,
    validate_split_ids,
)


class _Node:
    def __init__(self) -> None:
        self.state = "INACTIVE"
        self.activation = {"value": 0.0}
        self.tick_entered = 0
        self.meta = {"formal_engine_eval_count": 0}


class _Edge:
    def __init__(self) -> None:
        self.w = 1.0
        self.meta = {"trace": 0}


def _runtime() -> SimpleNamespace:
    graph = SimpleNamespace(nodes={"cell_node": _Node()}, edges=[_Edge()])
    return SimpleNamespace(
        cfg=SimpleNamespace(mode="base"),
        native_graph=SimpleNamespace(graph=graph),
        population={
            "cell": {
                "composite_id": "cell",
                "routing_weight_override": 0.5,
                "requested_exposures": 2,
                "formal_engine_eval_count": 3,
            }
        },
        cells={"cell": {"xp": 4}},
        engine_call_count=7,
        engine_eval_count=5,
        engine_tick_total=11,
        formal_eval_node_ids={"cell_node"},
    )


def _evaluation(*, policy: str = "policy", seed: int = 9) -> dict[str, object]:
    return {
        "policy": policy,
        "success_by_row": {"1": True, "2": False},
        "endpoint_by_row": {"1": "success", "2": "horizon"},
        "trace_digest_by_row": {"1": "aaa", "2": "bbb"},
        "active_composite_ids_by_row": {"1": ["cell"], "2": []},
        "predicate_evaluated_ids_by_row": {"1": ["cell"], "2": []},
        "action_by_row": {"1": ["A"], "2": ["B"]},
        "runner_config": {
            "black_reply_policy": "deterministic_greedy_black",
            "seed": seed,
            "seed_schedule": "seed + row",
            "judge_version": "judge-v1",
            "fence_check_timing": "after each transition",
            "tick_budget": 16,
            "tie_break": "score_then_action",
            "deterministic_row_order": [1, 2],
        },
        "source_manifest": {
            "split": "validation",
            "sha256": "manifest-hash",
            "row_ids": [1, 2],
        },
    }


def test_noop_parity_requires_identical_rows_traces_actions_and_runner() -> None:
    full = _evaluation(policy="full")
    noop = _evaluation(policy="noop")
    parity = assert_noop_parity(full, noop)
    assert parity["paired"]["difference"] == 0.0
    assert parity["paired"]["favorable"] == parity["paired"]["unfavorable"] == 0
    assert parity["passed"] is True

    changed = deepcopy(noop)
    changed["action_by_row"]["2"] = ["A"]  # type: ignore[index]
    with pytest.raises(AssertionError, match="action_by_row"):
        assert_noop_parity(full, changed)


def test_live_target_is_reacquired_after_snapshot_restore() -> None:
    runtime = _runtime()
    discarded = runtime.population["cell"]
    snapshot = CounterfactualSnapshot.capture(runtime)
    runtime.population["cell"] = {"composite_id": "cell", "routing_weight_override": 99.0}
    snapshot.restore(runtime)

    live = live_population_item(runtime, "cell")
    assert live is runtime.population["cell"]
    assert live is not discarded
    live["routing_weight_override"] = 3.0
    assert runtime.population["cell"]["routing_weight_override"] == 3.0


def test_live_l_dose_records_requested_and_observed_weight() -> None:
    runtime = _runtime()
    record = apply_live_routing_weight(runtime, "cell", 4.5)
    assert record == {"requested_routing_weight": 4.5, "observed_routing_weight": 4.5}
    assert runtime.population["cell"]["routing_weight_override"] == 4.5


def test_g_is_binary_and_only_l_has_doses() -> None:
    assert counterfactual_plan("G", (1.0, 3.0, 9.0, 27.0)) == (
        {"intervention": "off", "dose_multiplier": None},
        {"intervention": "on", "dose_multiplier": None},
    )
    assert counterfactual_plan("L", (1.0, 3.0)) == (
        {"intervention": "off", "dose_multiplier": None},
        {"intervention": "on", "dose_multiplier": 1.0},
        {"intervention": "on", "dose_multiplier": 3.0},
    )


def test_counterfactual_snapshot_restores_all_mutable_runtime_state() -> None:
    runtime = _runtime()
    snapshot = CounterfactualSnapshot.capture(runtime)
    runtime.population["cell"].update(requested_exposures=99, routing_weight_override=8.0)
    runtime.cells["cell"]["xp"] = 99
    runtime.engine_call_count = 99
    runtime.formal_eval_node_ids.add("other")
    node = runtime.native_graph.graph.nodes["cell_node"]
    node.state = "CONFIRMED"
    node.activation["value"] = 1.0
    node.tick_entered = 9
    node.meta["formal_engine_eval_count"] = 99
    runtime.native_graph.graph.edges[0].w = 9.0
    runtime.native_graph.graph.edges[0].meta["trace"] = 99
    snapshot.restore(runtime)

    assert runtime.population["cell"]["requested_exposures"] == 2
    assert runtime.population["cell"]["routing_weight_override"] == 0.5
    assert runtime.cells["cell"]["xp"] == 4
    assert runtime.engine_call_count == 7
    assert runtime.formal_eval_node_ids == {"cell_node"}
    assert node.state == "INACTIVE"
    assert node.activation == {"value": 0.0}
    assert node.tick_entered == 0
    assert node.meta == {"formal_engine_eval_count": 0}
    assert runtime.native_graph.graph.edges[0].w == 1.0
    assert runtime.native_graph.graph.edges[0].meta == {"trace": 0}


def test_split_separation_and_retired_rows() -> None:
    manifest = validate_split_ids({1, 2}, {3, 4}, {5, 6})
    assert manifest["disjoint"] is True
    with pytest.raises(ValueError, match="overlap"):
        validate_split_ids({1, 2}, {2, 3}, {4})
    with pytest.raises(ValueError, match="retired development"):
        validate_split_ids({1}, {2}, {600})
    assert 727 in RETIRED_DEVELOPMENT_ROW_IDS


def test_final_test_rows_never_reach_adaptive_paths() -> None:
    assert_final_test_untouched(
        final_test_ids={90, 91},
        adaptive_row_ids={"training": {1}, "nomination": {2}, "threshold_selection": {3}},
    )
    with pytest.raises(ValueError, match="final-test rows"):
        assert_final_test_untouched(final_test_ids={90}, adaptive_row_ids={"audition": {4, 90}})


def test_arm_provenance_is_complete() -> None:
    record = _evaluation()
    assert_complete_arm_record(record)
    for missing in (
        "success_by_row",
        "endpoint_by_row",
        "trace_digest_by_row",
        "active_composite_ids_by_row",
        "predicate_evaluated_ids_by_row",
        "runner_config",
        "source_manifest",
    ):
        broken = deepcopy(record)
        broken.pop(missing)
        with pytest.raises(ValueError, match=missing):
            assert_complete_arm_record(broken)


def test_paired_wilson_interval_and_noninferiority_use_uncertainty() -> None:
    clear = paired_binary_outcomes([True] * 20, [False] * 20, confidence=0.95)
    assert clear["favorable"] == 20
    assert clear["ci_low"] > 0.0
    assert clear["superior"] is True

    # Observed delta is inside a raw 1/4 margin, but the lower confidence bound is not.
    noisy = paired_binary_outcomes(
        [True, False, True, False],
        [True, False, False, True],
        confidence=0.95,
        noninferiority_margin=0.25,
    )
    assert noisy["difference"] == 0.0
    assert noisy["ci_low"] < -0.25
    assert noisy["noninferior"] is False


def test_noop_seed_schedule_and_tie_break_must_match() -> None:
    full = _evaluation(policy="full", seed=9)
    wrong_seed = _evaluation(policy="noop", seed=10)
    with pytest.raises(AssertionError, match="runner_config"):
        assert_noop_parity(full, wrong_seed)

    wrong_tie = _evaluation(policy="noop", seed=9)
    wrong_tie["runner_config"]["tie_break"] = "random"  # type: ignore[index]
    with pytest.raises(AssertionError, match="runner_config"):
        assert_noop_parity(full, wrong_tie)


def test_analysis_population_is_predeclared_not_treatment_defined() -> None:
    validate_analysis_population(
        predeclared_row_ids={1, 2, 3, 4},
        analyzed_row_ids={1, 2, 3, 4},
        static_eligible_row_ids={1, 3},
        off_nonfiring_by_row={2: True, 4: True},
        on_nonfiring_by_row={2: True, 4: True},
    )
    with pytest.raises(ValueError, match="full predeclared pool"):
        validate_analysis_population(
            predeclared_row_ids={1, 2, 3, 4},
            analyzed_row_ids={1, 3},
            static_eligible_row_ids={1, 3},
            off_nonfiring_by_row={2: True, 4: True},
            on_nonfiring_by_row={2: True, 4: True},
        )
    with pytest.raises(ValueError, match="non-firing parity"):
        validate_analysis_population(
            predeclared_row_ids={1, 2},
            analyzed_row_ids={1, 2},
            static_eligible_row_ids={1},
            off_nonfiring_by_row={2: True},
            on_nonfiring_by_row={2: False},
        )


def test_holm_prevents_first_unadjusted_hit_from_counting() -> None:
    adjusted = holm_adjusted_pvalues([0.01, 0.03, 0.04], alpha=0.05)
    assert [row["rejected"] for row in adjusted] == [True, False, False]
    assert adjusted[1]["adjusted_p"] >= 0.05


def test_phase51_reacquires_every_target_after_arm_l_restore(monkeypatch: pytest.MonkeyPatch) -> None:
    class Runtime:
        def __init__(self) -> None:
            self.cfg = StageBEcologicalDiscoveryConfig(
                real_native_probation_validation_rows=2,
                real_native_probation_noise_margin_wins=0,
                real_native_probation_dose_multipliers=(1.0, 3.0, 9.0, 27.0),
            )
            self.native_graph = SimpleNamespace(
                graph=SimpleNamespace(
                    nodes={"n1": _Node(), "n2": _Node()},
                    edges=[_Edge(), _Edge()],
                )
            )
            self.population = {
                "c1": {
                    "composite_id": "c1",
                    "node_id": "n1",
                    "state": "PROBATION",
                    "birth_segment": "stage_a",
                    "children": ["x1"],
                    "formal_engine_eval_count": 0,
                    "routing_weight_override": 0.25,
                },
                "c2": {
                    "composite_id": "c2",
                    "node_id": "n2",
                    "state": "PROBATION",
                    "birth_segment": "stage_a",
                    "children": ["x2"],
                    "formal_engine_eval_count": 0,
                    "routing_weight_override": 0.5,
                },
            }
            self.cells = {"c1": {"xp": 1}, "c2": {"xp": 1}}
            self.engine_call_count = 0
            self.confirmed_ids: list[str] = []

        def apply_probation_confirmation(self, *, composite_id: str, **_: object) -> None:
            self.confirmed_ids.append(composite_id)

    def fake_eval(
        _cfg: object,
        rows: list[dict[str, object]],
        runtime: Runtime,
        _score_provider: object,
        *,
        seed: int,
        policy_name: str,
        enabled_non_mature_ids: tuple[str, ...] = (),
        **_: object,
    ) -> dict[str, object]:
        runtime.engine_call_count += 1
        for cid in enabled_non_mature_ids:
            live_population_item(runtime, cid)["formal_engine_eval_count"] += 1
        row_ids = [int(row["row_id"]) for row in rows]
        success = {str(row_id): False for row_id in row_ids}
        endpoint = {str(row_id): "horizon" for row_id in row_ids}
        active = {str(row_id): list(enabled_non_mature_ids) for row_id in row_ids}
        digest = {str(row_id): f"trace-{row_id}" for row_id in row_ids}
        source_payload = [{"row_id": row_id} for row_id in row_ids]
        return {
            "policy": policy_name,
            "wins": 0,
            "success_by_row": success,
            "endpoint_by_row": endpoint,
            "trace_digest_by_row": digest,
            "active_composite_ids": list(enabled_non_mature_ids),
            "active_composite_ids_by_row": active,
            "predicate_evaluated_ids_by_row": active,
            "action_by_row": {str(row_id): ["A"] for row_id in row_ids},
            "conditional_gate_applied_count": 0,
            "conditional_gate_changed_choice_count": 0,
            "conditional_gate_composite_ids": [],
            "runner_config": {
                "black_reply_policy": "deterministic_greedy_black",
                "seed": seed,
                "seed_schedule": "fixed",
                "judge_version": "fake",
                "fence_check_timing": "fake",
                "tick_budget": 1,
                "tie_break": "fixed",
                "deterministic_row_order": row_ids,
            },
            "source_manifest": {
                "split": "validation",
                "sha256": hashlib.sha256(json.dumps(source_payload).encode()).hexdigest(),
                "row_ids": row_ids,
            },
        }

    runtime = Runtime()
    monkeypatch.setattr(ladder, "_phase42_ecology_policy_traces", fake_eval)
    result = ladder._phase51_confirm_probation_cells_two_arm_dose_response(
        runtime.cfg,
        runtime=runtime,
        score_provider=object(),
        rows=[{"row_id": 1}, {"row_id": 2}],
        success_kind="fake",
        seed=17,
        step=3,
        segment_name="measurement_regression",
    )

    assert runtime.confirmed_ids == ["c1", "c2"]
    assert len(result["records"]) == 2
    for record in result["records"]:
        assert len(record["arm_records"]["G"]["binary_records"]) == 1
        assert record["arm_records"]["G"]["dose_records"] == []
        assert len(record["arm_records"]["L"]["dose_records"]) == 4
        assert record["predicate_eval_guard_passed"] is True
        assert all(
            dose["requested_routing_weight"] == dose["observed_routing_weight"]
            for dose in record["arm_records"]["L"]["dose_records"]
        )
