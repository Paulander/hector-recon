from __future__ import annotations

import json
import pickle

import pytest

from recon_lite_hector.learning import (
    CompetenceSignal,
    CompetenceGateConfig,
    CompetenceGateExample,
    IntrinsicCreditConfig,
    IntrinsicCreditEngine,
    OutcomeCalibratedCompetenceGate,
    OutcomeCalibratedPrototypeGate,
    PrototypeCompetenceGateConfig,
    Responsibility,
    apply_credit_event_to_edges,
)
from recon_lite_hector.nodes import StemCellState, StemCellTerminal
from recon_lite_hector.plasticity import PlasticityConfig, init_plasticity_state
from recon_lite import Graph, LinkType, Node, NodeType


def _config(**overrides: object) -> IntrinsicCreditConfig:
    values = {
        "eta_fast": 0.5,
        "eta_slow": 1.0,
        "min_grounding_evidence": 3,
        "min_causal_confirmations": 1,
    }
    values.update(overrides)
    return IntrinsicCreditConfig(**values)


def _train_terminal(
    engine: IntrinsicCreditEngine,
    cell_id: str,
    terminal_kind: str,
    episodes: int = 8,
) -> None:
    for _ in range(episodes):
        engine.begin_episode()
        engine.transition(cell_id, terminal_kind=terminal_kind)


def _train_handoff(
    engine: IntrinsicCreditEngine,
    cell_id: str,
    child_id: str,
    episodes: int = 8,
) -> None:
    for _ in range(episodes):
        engine.begin_episode()
        event = engine.transition(cell_id, successor_ids=(child_id,))
        assert event.provider_ids == (child_id,)


def test_value_requires_maturity_grounding_causality_and_consolidation() -> None:
    engine = IntrinsicCreditEngine(_config())
    state = engine.register("mate1", mature=False)
    _train_terminal(engine, "mate1", "mate")

    assert state.fast_value > 0.0
    assert engine.successor_signal(("mate1",))[0] is None

    engine.set_mature("mate1")
    assert engine.successor_signal(("mate1",))[0] is None

    engine.record_paired_intervention(
        "mate1", enabled_return=1.0, disabled_return=-0.25
    )
    assert engine.successor_signal(("mate1",))[0] is not None
    assert engine.successor_signal(("mate1",))[0].value == 0.0

    engine.consolidate(("mate1",))
    signal, rejected = engine.successor_signal(("mate1",))
    assert rejected is False
    assert signal is not None
    assert signal.value > 0.9
    assert signal.grounding_level == 1


def test_exact_real_returns_can_authorize_a_local_provider_without_global_gate() -> None:
    engine = IntrinsicCreditEngine(_config())
    engine.register("clean")
    engine.register("mixed")
    for _ in range(3):
        engine.begin_episode()
        engine.transition("clean", terminal_kind="mate")
        engine.begin_episode()
        engine.transition("mixed", terminal_kind="mate")
    engine.begin_episode()
    engine.transition("mixed")

    audit = engine.consolidate_direct_outcome_providers(("clean", "mixed"))

    assert audit["provider_ids"] == ["clean"]
    assert audit["aggregate_score_read"] is False
    assert engine.direct_outcome_provider_response("clean") is not None
    assert engine.direct_outcome_provider_response("mixed") is None
    assert engine.states["clean"].causal_confirmations == 0
    assert engine.states["mixed"].direct_contrast_evidence == 1


def test_eligibility_credit_cannot_fake_direct_action_evidence() -> None:
    engine = IntrinsicCreditEngine(_config())
    engine.register("selected")
    engine.register("parent")
    for _ in range(3):
        engine.begin_episode()
        engine.transition(
            "selected",
            responsibilities=(
                Responsibility("selected", parent_distance=0),
                Responsibility("parent", parent_distance=1),
            ),
            terminal_kind="mate",
        )

    audit = engine.consolidate_direct_outcome_providers(
        ("selected", "parent")
    )

    assert audit["provider_ids"] == ["selected"]
    assert engine.states["parent"].terminal_evidence == 3
    assert engine.states["parent"].direct_positive_evidence == 0


def test_later_local_contrast_revokes_an_authorized_provider() -> None:
    engine = IntrinsicCreditEngine(_config())
    engine.register("branch")
    for _ in range(3):
        engine.begin_episode()
        engine.transition("branch", terminal_kind="mate")
    engine.consolidate_direct_outcome_providers(("branch",))
    assert engine.direct_outcome_provider_response("branch") is not None

    engine.begin_episode()
    engine.transition("branch", terminal_kind="horizon")
    assert engine.direct_outcome_provider_response("branch") is None
    audit = engine.consolidate_direct_outcome_providers(("branch",))
    assert audit["provider_ids"] == []
    assert engine.states["branch"].mature is False


def test_legacy_credit_pickle_defaults_to_no_local_authority() -> None:
    engine = IntrinsicCreditEngine(_config())
    state = engine.register("legacy")
    del state.direct_positive_evidence
    del state.direct_contrast_evidence
    del state.direct_outcome_authorized

    restored = pickle.loads(pickle.dumps(engine))
    restored_state = restored.states["legacy"]
    assert restored_state.direct_positive_evidence == 0
    assert restored_state.direct_contrast_evidence == 0
    assert restored_state.direct_outcome_authorized is False
    assert restored.direct_outcome_provider_ids() == ()


def test_known_positive_competence_bootstraps_a_three_rung_chain() -> None:
    engine = IntrinsicCreditEngine(_config())
    for cell_id in ("mate1", "mate2", "edge_killbox"):
        engine.register(cell_id, mature=True)

    _train_terminal(engine, "mate1", "mate")
    engine.record_paired_intervention("mate1", enabled_return=1.0, disabled_return=0.0)
    engine.consolidate(("mate1",))

    _train_handoff(engine, "mate2", "mate1")
    engine.record_paired_intervention("mate2", enabled_return=1.0, disabled_return=0.0)
    engine.consolidate(("mate2",))

    _train_handoff(engine, "edge_killbox", "mate2")
    engine.record_paired_intervention(
        "edge_killbox", enabled_return=1.0, disabled_return=0.0
    )
    engine.consolidate(("edge_killbox",))

    mate1 = engine.states["mate1"]
    mate2 = engine.states["mate2"]
    killbox = engine.states["edge_killbox"]
    assert mate1.grounding_level == 0
    assert mate2.grounding_level == 1
    assert killbox.grounding_level == 2
    assert mate1.slow_value > mate2.slow_value > killbox.slow_value > 0.0
    assert mate2.grounding_ancestors == {"mate1"}
    assert killbox.grounding_ancestors == {"mate1", "mate2"}


def test_trial_or_uncorroborated_child_cannot_reward_parent() -> None:
    engine = IntrinsicCreditEngine(_config())
    child = engine.register("child", mature=False, initial_fast_value=1.0, initial_slow_value=1.0)
    child.terminal_evidence = 100
    child.grounding_level = 0
    child.causal_confirmations = 100
    engine.register("parent", mature=True)

    event = engine.transition("parent", successor_ids=("child",))
    assert event.provider_ids == ()
    assert event.successor_value == 0.0
    assert event.td_error < 0.0


def test_grounding_provenance_rejects_circular_reward() -> None:
    engine = IntrinsicCreditEngine(_config())
    for cell_id in ("a", "b"):
        engine.register(cell_id, mature=True)

    _train_terminal(engine, "a", "mate")
    engine.record_paired_intervention("a", enabled_return=1.0, disabled_return=0.0)
    engine.consolidate(("a",))
    _train_handoff(engine, "b", "a")
    engine.record_paired_intervention("b", enabled_return=1.0, disabled_return=0.0)
    engine.consolidate(("b",))

    engine.begin_episode()
    event = engine.transition("a", successor_ids=("b",))
    assert event.cycle_rejected is True
    assert event.provider_ids == ()
    assert event.successor_value == 0.0


def test_negative_grounded_competence_propagates_debt() -> None:
    engine = IntrinsicCreditEngine(_config())
    engine.register("stalemate_basin", mature=True)
    engine.register("upstream", mature=True)
    _train_terminal(engine, "stalemate_basin", "stalemate")
    engine.record_paired_intervention(
        "stalemate_basin", enabled_return=-1.0, disabled_return=0.0
    )
    engine.consolidate(("stalemate_basin",))

    engine.begin_episode()
    event = engine.transition("upstream", successor_ids=("stalemate_basin",))
    assert event.provider_ids == ("stalemate_basin",)
    assert event.successor_value < -0.9
    assert event.td_error < -0.9


def test_real_move_and_virtual_frame_costs_are_distinct_and_virtual_is_not_grounding() -> None:
    engine = IntrinsicCreditEngine(_config(real_move_cost=0.02, virtual_frame_cost=0.002))
    engine.register("cell")

    engine.begin_episode()
    virtual = engine.transition("cell", real_step=False)
    engine.begin_episode()
    real = engine.transition("cell", real_step=True)
    assert virtual.immediate_reward == -0.002
    assert real.immediate_reward == -0.02
    assert engine.states["cell"].grounding_evidence == 0
    with pytest.raises(ValueError, match="virtual frames"):
        engine.transition("cell", terminal_kind="mate", real_step=False)


def test_parent_credit_is_normalized_and_slower_than_local_credit() -> None:
    engine = IntrinsicCreditEngine(_config(parent_learning_decay=0.5))
    engine.register("local", hierarchy_depth=0)
    engine.register("parent", hierarchy_depth=1)
    engine.transition(
        "local",
        responsibilities=(
            Responsibility("local", weight=1.0, parent_distance=0),
            Responsibility("parent", weight=1.0, parent_distance=1),
        ),
        terminal_kind="mate",
    )
    assert 0.0 < engine.states["parent"].fast_value < engine.states["local"].fast_value


def test_correlation_does_not_grant_stem_cell_maturation_credit() -> None:
    engine = IntrinsicCreditEngine(_config())
    stem = StemCellTerminal("trial")
    stem.state = StemCellState.TRIAL
    stem.xp = 50
    engine.register_stem_cell(stem)

    assert engine.record_correlation(stem, 1.0) == "positive"
    assert stem.xp == 50
    assert stem.candidate_stats.credit_stats.positive_correlation == 1
    assert stem.candidate_stats.credit_stats.total_interventions == 0

    credit = engine.record_paired_intervention(
        "trial", enabled_return=1.0, disabled_return=0.0, stem_cell=stem
    )
    assert credit.valence == "positive"
    assert stem.xp == 60
    assert stem.candidate_stats.credit_stats.positive_intervention == 1


def test_snapshot_is_json_serializable_and_auditable() -> None:
    engine = IntrinsicCreditEngine(_config())
    engine.register("mate1", mature=True)
    _train_terminal(engine, "mate1", "mate", episodes=3)
    engine.record_paired_intervention("mate1", enabled_return=1.0, disabled_return=0.0)
    engine.consolidate()

    payload = engine.snapshot()
    assert payload["states"]["mate1"]["can_emit"] is True
    assert payload["states"]["mate1"]["grounding_ancestors"] == []
    assert json.loads(json.dumps(payload))["event_count"] == 3


def test_intrinsic_td_error_updates_existing_recon_edge_weights() -> None:
    graph = Graph()
    graph.add_node(Node("parent", NodeType.SCRIPT))
    graph.add_node(Node("child", NodeType.SCRIPT))
    graph.add_edge("parent", "child", LinkType.POR)
    edge_state = init_plasticity_state(graph)
    plasticity = PlasticityConfig(eta_tick=0.1, lambda_decay=0.8)

    engine = IntrinsicCreditEngine(_config())
    engine.register("child")
    event = engine.transition("child", terminal_kind="mate")
    deltas = apply_credit_event_to_edges(
        event,
        edge_state=edge_state,
        graph=graph,
        fired_edges=({"src": "parent", "dst": "child", "ltype": "POR"},),
        plasticity_config=plasticity,
    )

    assert deltas["parent->child:POR"] > 0.0
    assert graph.edge_by_key[("parent", "child", LinkType.POR)].w > 1.0


def test_outcome_calibrated_gate_requires_selective_validation_before_maturity() -> None:
    train = [
        CompetenceGateExample((0.9, 0.8), True),
        CompetenceGateExample((0.8, 0.7), True),
        CompetenceGateExample((0.2, 0.1), False),
        CompetenceGateExample((0.1, 0.2), False),
    ] * 8
    validation = [
        CompetenceGateExample((0.85, 0.75), True),
        CompetenceGateExample((0.75, 0.85), True),
        CompetenceGateExample((0.15, 0.15), False),
    ] * 6
    gate = OutcomeCalibratedCompetenceGate.fit(
        ("response", "margin"),
        train,
        validation,
        CompetenceGateConfig(
            steps=2_000,
            min_validation_true_positives=10,
            max_validation_false_positives=0,
        ),
    )

    assert gate.mature is True
    assert gate.confirms((0.9, 0.9)) is True
    assert gate.confirms((0.1, 0.1)) is False
    assert gate.validation_metrics["false_positive"] == 0


def test_outcome_calibrated_prototype_gate_learns_nonlinear_xor_boundary() -> None:
    train = [
        CompetenceGateExample((0.0, 0.0), True),
        CompetenceGateExample((1.0, 1.0), True),
        CompetenceGateExample((0.0, 1.0), False),
        CompetenceGateExample((1.0, 0.0), False),
    ] * 8
    validation = [
        CompetenceGateExample((0.05, 0.05), True),
        CompetenceGateExample((0.95, 0.95), True),
        CompetenceGateExample((0.05, 0.95), False),
        CompetenceGateExample((0.95, 0.05), False),
    ] * 6
    gate = OutcomeCalibratedPrototypeGate.fit(
        ("response_a", "response_b"),
        train,
        validation,
        PrototypeCompetenceGateConfig(
            neighbors=3,
            min_validation_true_positives=10,
            max_validation_false_positives=0,
            min_validation_precision=1.0,
        ),
    )

    assert gate.mature is True
    assert gate.validation_metrics["true_positive"] == 12
    assert gate.validation_metrics["false_positive"] == 0
    assert gate.confirms((0.02, 0.02)) is True
    assert gate.confirms((0.02, 0.98)) is False


def test_transition_can_subtract_exact_external_graph_prediction() -> None:
    engine = IntrinsicCreditEngine(_config())
    engine.register("chosen_branch", initial_fast_value=0.75)

    engine.begin_episode()
    event = engine.transition(
        "chosen_branch",
        terminal_value=0.0,
        prediction_override=-0.5,
    )

    assert event.predicted_value == -0.5
    assert event.td_error > 0.0
    assert event.updated_values["chosen_branch"] > 0.75


def test_transition_rejects_nonfinite_prediction_override() -> None:
    engine = IntrinsicCreditEngine(_config())
    engine.register("chosen_branch")
    engine.states["chosen_branch"].eligibility = 0.75
    before = engine.snapshot()

    with pytest.raises(ValueError, match="prediction_override must be finite"):
        engine.transition(
            "chosen_branch",
            terminal_value=0.0,
            prediction_override=float("nan"),
        )
    assert engine.snapshot() == before


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"terminal_value": float("nan")}, "terminal_value must be finite"),
        (
            {"responsibilities": (Responsibility("missing"),)},
            "unregistered competence",
        ),
        (
            {"responsibilities": (Responsibility("chosen_branch", weight=float("inf")),)},
            "responsibility weights must be finite",
        ),
    ),
)
def test_transition_late_input_validation_is_atomic(
    kwargs: dict[str, object],
    message: str,
) -> None:
    engine = IntrinsicCreditEngine(_config())
    engine.register("chosen_branch")
    engine.states["chosen_branch"].eligibility = 0.75
    before = engine.snapshot()

    with pytest.raises((KeyError, ValueError), match=message):
        engine.transition("chosen_branch", **kwargs)
    assert engine.snapshot() == before


def test_transition_uses_exact_grounded_composed_successor_signal() -> None:
    engine = IntrinsicCreditEngine(_config())
    engine.register("mate1", mature=True)
    engine.register("mate2_candidate")
    _train_terminal(engine, "mate1", "mate")
    engine.record_paired_intervention(
        "mate1", enabled_return=1.0, disabled_return=0.0
    )
    engine.consolidate(("mate1",))
    learned_child_value = engine.states["mate1"].slow_value
    assert learned_child_value != pytest.approx(0.31)

    engine.begin_episode()
    event = engine.transition(
        "mate2_candidate",
        explicit_successor_signal=CompetenceSignal(
            value=0.31,
            confidence=0.72,
            provider_ids=("mate1",),
            grounding_level=1,
            grounding_ancestors=("mate1",),
        ),
    )

    assert event.successor_value == pytest.approx(0.31)
    assert event.successor_value != pytest.approx(learned_child_value)
    assert event.provider_ids == ("mate1",)
    assert event.td_error == pytest.approx(-0.01 + 0.97 * 0.31)
    state = engine.states["mate2_candidate"]
    assert state.handoff_evidence == 1
    assert state.grounding_level == 1
    assert state.grounding_ancestors == {"mate1"}


def test_explicit_successor_signal_cannot_exceed_internal_provider() -> None:
    engine = IntrinsicCreditEngine(_config())
    provider = engine.register("provider", mature=True)
    provider.slow_value = 0.2
    provider.fast_value = 0.2
    provider.terminal_evidence = 3
    provider.causal_confirmations = 1
    provider.grounding_level = 0
    engine.register("recipient")
    before = engine.snapshot()

    with pytest.raises(ValueError, match="exceeds its provider envelope"):
        engine.transition(
            "recipient",
            explicit_successor_signal=CompetenceSignal(
                value=0.21,
                confidence=0.51,
                provider_ids=("provider",),
                grounding_level=1,
                grounding_ancestors=("provider",),
            ),
        )
    assert engine.snapshot() == before


def test_explicit_successor_signal_fails_closed_before_credit_mutation() -> None:
    engine = IntrinsicCreditEngine(_config())
    engine.register("mate1", mature=True)
    engine.register("recipient")
    _train_terminal(engine, "mate1", "mate")
    engine.record_paired_intervention(
        "mate1", enabled_return=1.0, disabled_return=0.0
    )
    engine.consolidate(("mate1",))
    valid = CompetenceSignal(
        value=0.4,
        confidence=0.8,
        provider_ids=("mate1",),
        grounding_level=1,
        grounding_ancestors=("mate1",),
    )
    before = engine.snapshot()

    invalid_calls = (
        {"explicit_successor_signal": valid, "successor_ids": ("mate1",)},
        {"explicit_successor_signal": valid, "terminal_kind": "mate"},
        {"explicit_successor_signal": valid, "real_step": False},
        {
            "explicit_successor_signal": CompetenceSignal(
                value=float("nan"),
                confidence=0.8,
                provider_ids=("mate1",),
                grounding_level=1,
                grounding_ancestors=("mate1",),
            )
        },
        {
            "explicit_successor_signal": CompetenceSignal(
                value=0.4,
                confidence=0.8,
                provider_ids=("recipient",),
                grounding_level=1,
                grounding_ancestors=("recipient",),
            )
        },
    )
    for kwargs in invalid_calls:
        with pytest.raises(ValueError):
            engine.transition("recipient", **kwargs)
        assert engine.snapshot() == before
