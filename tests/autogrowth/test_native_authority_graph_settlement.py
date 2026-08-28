from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, replace
from typing import Any

import pytest

from recon_lite import FormalReConEngine, NodeState
from recon_lite_hector.nodes import StemCellState
from recon_lite_chess.autogrowth.native_authority_handover import (
    GraphActuation,
    GraphSignalTrace,
    GraphTerminalSignal,
)
from recon_lite_chess.autogrowth.native_competence_envelope import (
    AvailabilityState,
    DormantOrigin,
    SpecializationMode,
    StructuralMatchDescriptor,
    canonical_structural_pattern_matches,
)
from recon_lite_chess.autogrowth import (
    native_prospective_evidence_authority_v2 as authority_module,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    AcceptedRealReference,
    AuthorityMeasurementSnapshot,
    FrozenHypothesis,
    InitializationOrigin,
    ProspectiveAuthorityState,
    ProspectiveV2IntegrityError,
    ProvenanceKind,
    V2GroundedReceipt,
    _sha,
)


def _trace(*signal_ids: str) -> GraphSignalTrace:
    actuation = GraphActuation(
        actuator_identity="actuator:test",
        move_uci="a2a3",
        option_identity="option:test",
        activation=1.0,
        candidate_count=1,
        formal_ticks=1,
    )
    return GraphSignalTrace(
        frame_id="frame:test",
        frame_kind="REAL",
        source_organism_identity="organism:test",
        source_state_identity="state:test",
        option_identity="option:test",
        actuation=actuation,
        confirmed_base_terminal_node_ids=(),
        confirmed_mature_composite_ids=(),
        terminal_signals=tuple(
            GraphTerminalSignal(
                identity=identity,
                role="BASE_TERMINAL",
                source_node_identity=f"source:{index}",
                terminal_kind="TEST",
                provenance="test",
            )
            for index, identity in enumerate(signal_ids)
        ),
    )


def _historical_hypothesis(
    cell_id: str,
    members: tuple[str, ...],
    receipt_ids: tuple[str, ...],
    *,
    structural_state: StemCellState = StemCellState.MATURE,
    dormant_origin: DormantOrigin | None = None,
    discovery_support_receipt_ids: tuple[str, ...] = (),
) -> FrozenHypothesis:
    return FrozenHypothesis(
        cell_id=cell_id,
        members=members,
        polarity=AvailabilityState.AVAILABLE,
        lineage_parent_id=None,
        specialization_depth=0,
        discovery_receipt_ids=receipt_ids,
        discovery_receipt_digest=_sha(list(receipt_ids)),
        birth_frontier=len(receipt_ids),
        structural_state=structural_state.name,
        nomination_operation="historical",
        triggering_receipt_id=None,
        graph_request_root_state=None,
        graph_request_terminal_state=None,
        considered_context_ids=(),
        selected_context_ids=(),
        nomination_read_frontier=0,
        certification_frontier=len(receipt_ids),
        nomination_escrow_digest=None,
        provenance_kind=ProvenanceKind.HISTORICAL_ACCEPTED_LEDGER,
        nomination_read_sets=(),
        transitive_ancestor_receipt_ids=(),
        discovery_exclusion_receipt_ids=receipt_ids,
        initialization_origin=InitializationOrigin.HISTORICAL,
        dormant_origin=dormant_origin,
        discovery_support_receipt_ids=discovery_support_receipt_ids,
    )


def _state(
    cell_id: str,
    members: tuple[str, ...],
    *,
    receipt_ids: tuple[str, ...] | None = None,
    specialization_parent: bool = False,
) -> ProspectiveAuthorityState:
    receipts = receipt_ids or (f"discovery:{cell_id}",)
    hypothesis = _historical_hypothesis(
        cell_id,
        members,
        receipts,
        structural_state=(
            StemCellState.DORMANT
            if specialization_parent
            else StemCellState.MATURE
        ),
        dormant_origin=(
            DormantOrigin.MIXED_OUTCOME_SHADOW
            if specialization_parent
            else None
        ),
        discovery_support_receipt_ids=(receipts if specialization_parent else ()),
    )
    return ProspectiveAuthorityState(
        hypothesis=hypothesis,
        prospectively_certified=True,
        certification_receipt_ids=receipts,
        support_receipt_ids=receipts,
        successes=len(receipts),
        contradictions=0,
        support=len(receipts),
    )


def _grounded_receipt(
    trace: GraphSignalTrace,
    *,
    observed_outcome: bool = False,
) -> V2GroundedReceipt:
    return V2GroundedReceipt(
        receipt_id="receipt:contradiction",
        ordinal=100,
        pending_token="pending:test",
        frame_kind="REAL",
        source_organism_identity=trace.source_organism_identity,
        source_state_identity=trace.source_state_identity,
        predecessor_fen="predecessor:test",
        trace=trace,
        selected_actuation=trace.actuation,
        successor_fen="successor:test",
        outcome_terminal_identity="outcome:test",
        environment_outcome_terminal_identity="environment:test",
        observed_outcome=observed_outcome,
        interaction_fingerprint="interaction:test",
        issuer_identity="issuer:test",
        signature="signature:test",
    )


def _reference(
    receipt_id: str,
    ordinal: int,
    identities: tuple[str, ...],
) -> AcceptedRealReference:
    return AcceptedRealReference(
        receipt_id=receipt_id,
        ordinal=ordinal,
        stable_physical_interaction_id=f"physical:{receipt_id}",
        trace_digest=f"trace:{receipt_id}",
        typed_signal_digest=f"typed:{receipt_id}",
        observed_outcome=True,
        source_generation=0,
        ordered_signal_identities=identities,
        typed_signal_roles=tuple(sorted(
            (identity, "BASE_TERMINAL") for identity in identities
        )),
    )


def _grounded_reference(
    receipt: V2GroundedReceipt,
) -> AcceptedRealReference:
    return AcceptedRealReference(
        receipt_id=receipt.receipt_id,
        ordinal=receipt.ordinal,
        stable_physical_interaction_id=receipt.interaction_fingerprint,
        trace_digest=receipt.trace.digest(),
        typed_signal_digest=_sha([
            asdict(item) for item in receipt.trace.terminal_signals
        ]),
        observed_outcome=receipt.observed_outcome,
        source_generation=0,
        ordered_signal_identities=receipt.trace.ordered_signal_identities,
        typed_signal_roles=tuple(sorted(
            (item.identity, item.role)
            for item in receipt.trace.terminal_signals
        )),
    )


def _node_semantics(graph: Any) -> dict[str, tuple[str, int, float]]:
    return {
        node_id: (
            node.state.name,
            node.tick_entered,
            float(node.activation.value),
        )
        for node_id, node in sorted(graph.nodes.items())
    }


def _legacy_full_cap_main_run(
    states: Mapping[str, ProspectiveAuthorityState],
    snapshot: AuthorityMeasurementSnapshot,
) -> tuple[dict[str, Any], dict[str, tuple[str, int, float]]]:
    graph = authority_module._build_authority_graph(states)
    engine = FormalReConEngine(graph, record_trace=False)
    for role in authority_module.CELL_AUTHORITY_ROLES:
        engine.request(authority_module.ROLE_ROOTS[role])
    engine.run(
        max_ticks=max(
            32,
            len(states) * len(authority_module.AUTHORITY_ROLES) * 4,
        ),
        env={
            "authority_snapshot": snapshot,
            "authority_states": states,
            "specialization_mode": SpecializationMode.DISCONNECTED.value,
            "lifetime_requested_parent_ids": (),
        },
    )
    result = {
        role: tuple(sorted(
            cell_id
            for cell_id in states
            if graph.nodes[f"v2:{role}:{cell_id}"].state
            == NodeState.CONFIRMED
        ))
        for role in authority_module.CELL_AUTHORITY_ROLES
    }
    result["specialization_eligibility"] = ()
    result["specialization_candidate_states"] = ()
    return result, _node_semantics(graph)


@pytest.mark.parametrize("matching_count", [0, 1, 3])
def test_settlement_matches_full_cap_for_zero_one_and_many_successes(
    monkeypatch: pytest.MonkeyPatch,
    matching_count: int,
) -> None:
    states = {
        f"cell-{index}": _state(f"cell-{index}", (f"signal:{index}",))
        for index in range(3)
    }
    snapshot = AuthorityMeasurementSnapshot(
        _trace(*(f"signal:{index}" for index in range(matching_count)))
    )
    expected, expected_nodes = _legacy_full_cap_main_run(states, snapshot)

    original_run = authority_module.FormalReConEngine.run
    calls: list[dict[str, Any]] = []

    def recording_run(self, *args, **kwargs):
        result = original_run(self, *args, **kwargs)
        calls.append({
            "tick": self.tick,
            "until": kwargs.get("until"),
            "nodes": _node_semantics(self.g),
        })
        return result

    monkeypatch.setattr(
        authority_module.FormalReConEngine, "run", recording_run
    )
    actual = authority_module._run_authority_graph(states, snapshot)

    assert actual == expected
    assert len(calls) == 1
    assert callable(calls[0]["until"])
    assert calls[0]["tick"] <= 7
    assert calls[0]["nodes"] == expected_nodes


@pytest.mark.parametrize("observed_outcome", [False, True])
def test_grounded_settlement_matches_full_cap_for_every_lifecycle_role(
    monkeypatch: pytest.MonkeyPatch,
    observed_outcome: bool,
) -> None:
    certified_available = _state(
        "certified-available", ("signal:shared",)
    )
    certified_refuted = _state("certified-refuted", ("signal:shared",))
    certified_refuted.hypothesis = replace(
        certified_refuted.hypothesis,
        polarity=AvailabilityState.REFUTED,
        hypothesis_digest="",
    )
    immature = _state(
        "immature",
        ("signal:shared",),
        receipt_ids=("immature:0", "immature:1", "immature:2"),
    )
    immature.prospectively_certified = False
    states = {
        "certified-available": certified_available,
        "certified-refuted": certified_refuted,
        "immature": immature,
    }
    trace = _trace("signal:shared")
    snapshot = AuthorityMeasurementSnapshot(
        trace,
        _grounded_receipt(trace, observed_outcome=observed_outcome),
    )
    expected, expected_nodes = _legacy_full_cap_main_run(states, snapshot)

    original_run = authority_module.FormalReConEngine.run
    calls: list[dict[str, Any]] = []

    def recording_run(self, *args, **kwargs):
        result = original_run(self, *args, **kwargs)
        calls.append({
            "tick": self.tick,
            "until": kwargs.get("until"),
            "nodes": _node_semantics(self.g),
        })
        return result

    monkeypatch.setattr(
        authority_module.FormalReConEngine, "run", recording_run
    )
    assert snapshot.grounded_receipt is not None
    actual = authority_module._run_authority_graph(
        states,
        snapshot,
        current_real_reference=_grounded_reference(
            snapshot.grounded_receipt
        ),
    )

    assert actual == expected
    assert len(calls) == 1
    assert callable(calls[0]["until"])
    assert calls[0]["tick"] <= 7
    assert calls[0]["nodes"] == expected_nodes


def test_match_facts_are_reused_within_a_call_but_not_between_snapshots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    states = {
        f"cell-{index}": _state(f"cell-{index}", (f"signal:{index}",))
        for index in range(3)
    }
    original_descriptors = authority_module._structural_match_descriptors
    original_wilson = authority_module.wilson_lower_bound
    descriptor_builds = 0
    fact_evaluations = 0

    def counting_descriptors(states_arg):
        nonlocal descriptor_builds
        descriptor_builds += 1
        return original_descriptors(states_arg)

    def counting_wilson(successes, support, z):
        nonlocal fact_evaluations
        fact_evaluations += 1
        return original_wilson(successes, support, z)

    monkeypatch.setattr(
        authority_module, "_structural_match_descriptors", counting_descriptors
    )
    monkeypatch.setattr(
        authority_module, "wilson_lower_bound", counting_wilson
    )
    absent = authority_module._run_authority_graph(
        states, AuthorityMeasurementSnapshot(_trace())
    )
    assert absent["commitment"] == ()
    assert descriptor_builds == 1
    assert fact_evaluations == len(states)

    present = authority_module._run_authority_graph(
        states,
        AuthorityMeasurementSnapshot(_trace("signal:0", "signal:1", "signal:2")),
    )
    assert present["commitment"] == tuple(sorted(states))
    assert descriptor_builds == 2
    assert fact_evaluations == 2 * len(states)


def _descriptor(
    cell_id: str,
    members: tuple[str, ...],
    structural_state: StemCellState,
    *,
    parent: str | None = None,
    depth: int = 0,
    operation: str = "historical",
    parent_digest: str | None = None,
    digest: str | None = None,
) -> StructuralMatchDescriptor:
    return StructuralMatchDescriptor(
        cell_id=cell_id,
        members=members,
        structural_state=structural_state.name,
        lineage_parent_id=parent,
        specialization_depth=depth,
        nomination_operation=operation,
        parent_hypothesis_digest=parent_digest,
        hypothesis_digest=digest,
    )


@pytest.mark.parametrize(
    ("descriptors", "cell_id", "signals"),
    [
        (
            {"cell": _descriptor(
                "cell", ("signal:a",), StemCellState.MATURE
            )},
            "cell",
            ("signal:a",),
        ),
        (
            {"cell": _descriptor(
                "cell", ("signal:a",), StemCellState.MATURE
            )},
            "cell",
            (),
        ),
        ({}, "absent", ("signal:a",)),
        (
            {
                "parent": _descriptor(
                    "parent", ("signal:a",), StemCellState.MATURE,
                    digest="parent-digest",
                ),
                "child": _descriptor(
                    "child", ("context:parent", "signal:b"),
                    StemCellState.DORMANT,
                ),
            },
            "child",
            ("signal:a", "signal:b"),
        ),
        (
            {
                "parent": _descriptor(
                    "parent", ("signal:a",), StemCellState.PRUNED,
                    digest="parent-digest",
                ),
                "child": _descriptor(
                    "child", ("context:parent",), StemCellState.DORMANT,
                ),
            },
            "child",
            ("signal:a",),
        ),
        *(
            (
                {
                    "parent": _descriptor(
                        "parent", ("signal:a",), parent_state,
                        digest="parent-digest",
                    ),
                    "child": _descriptor(
                        "child", ("context:parent", "signal:b"),
                        StemCellState.DORMANT,
                        parent="parent",
                        depth=1,
                        operation="specialization",
                        parent_digest="parent-digest",
                    ),
                },
                "child",
                ("signal:a", "signal:b"),
            )
            for parent_state in (StemCellState.DORMANT, StemCellState.PROBATION)
        ),
        (
            {
                "parent": _descriptor(
                    "parent", ("signal:a",), StemCellState.DORMANT,
                    digest="parent-digest",
                ),
                "child": _descriptor(
                    "child", ("context:parent", "signal:b"),
                    StemCellState.DORMANT,
                    parent="parent",
                    depth=1,
                    operation="specialization",
                    parent_digest="wrong-digest",
                ),
            },
            "child",
            ("signal:a", "signal:b"),
        ),
    ],
)
def test_memoized_structural_matcher_agrees_with_canonical_matcher(
    descriptors: Mapping[str, StructuralMatchDescriptor],
    cell_id: str,
    signals: tuple[str, ...],
) -> None:
    expected = canonical_structural_pattern_matches(
        cell_id, descriptors, signals
    )
    cache = authority_module._StructuralPatternMatchCache(
        descriptors=descriptors,
        active_signal_ids=frozenset(signals),
    )
    assert cache.match(cell_id) is expected
    assert cache.match(cell_id) is expected


def test_memoized_structural_matcher_preserves_cycle_failure() -> None:
    descriptors = {
        "cell-a": _descriptor(
            "cell-a", ("context:cell-b",), StemCellState.MATURE
        ),
        "cell-b": _descriptor(
            "cell-b", ("context:cell-a",), StemCellState.MATURE
        ),
    }
    with pytest.raises(RuntimeError, match="cyclic competence context"):
        canonical_structural_pattern_matches("cell-a", descriptors, ())
    cache = authority_module._StructuralPatternMatchCache(
        descriptors=descriptors,
        active_signal_ids=frozenset(),
    )
    with pytest.raises(ProspectiveV2IntegrityError, match="cyclic competence"):
        cache.match("cell-a")


def test_cyclic_match_failure_is_terminal_local_and_cache_does_not_leak() -> None:
    cyclic = {
        "cell-a": _state("cell-a", ("context:cell-b",)),
        "cell-b": _state("cell-b", ("context:cell-a",)),
    }
    failed = authority_module._run_authority_graph(
        cyclic, AuthorityMeasurementSnapshot(_trace())
    )
    assert all(
        failed[role] == ()
        for role in authority_module.CELL_AUTHORITY_ROLES
    )

    valid = {
        "cell-a": _state("cell-a", ("signal:a",)),
        "cell-b": _state("cell-b", ("signal:b",)),
    }
    recovered = authority_module._run_authority_graph(
        valid, AuthorityMeasurementSnapshot(_trace("signal:a", "signal:b"))
    )
    assert recovered["commitment"] == ("cell-a", "cell-b")
    assert recovered["available"] == ("cell-a", "cell-b")


def test_authority_fails_hard_when_the_cap_is_exhausted_unsettled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    states = {"cell": _state("cell", ("signal",))}

    def stalled_run(self, *args, **kwargs):
        del args, kwargs
        return self.trace

    monkeypatch.setattr(
        authority_module.FormalReConEngine, "run", stalled_run
    )
    with pytest.raises(ProspectiveV2IntegrityError, match="sett"):
        authority_module._run_authority_graph(
            states, AuthorityMeasurementSnapshot(_trace("signal"))
        )


def _specialization_case() -> tuple[
    dict[str, ProspectiveAuthorityState],
    AuthorityMeasurementSnapshot,
    dict[str, AcceptedRealReference],
]:
    states: dict[str, ProspectiveAuthorityState] = {}
    references: dict[str, AcceptedRealReference] = {}
    for parent in ("parent-a", "parent-b"):
        receipt_ids = tuple(f"support:{parent}:{index}" for index in range(4))
        trigger = f"trigger:{parent}"
        local = f"candidate:{parent}"
        identities = (local, "candidate:shared", trigger)
        states[parent] = _state(
            parent,
            (trigger,),
            receipt_ids=receipt_ids,
            specialization_parent=True,
        )
        references.update({
            receipt_id: _reference(receipt_id, index, identities)
            for index, receipt_id in enumerate(receipt_ids)
        })
    trace = _trace(
        "trigger:parent-a",
        "trigger:parent-b",
        "candidate:shared",
    )
    return states, AuthorityMeasurementSnapshot(
        trace, _grounded_receipt(trace)
    ), references


@pytest.mark.parametrize(
    ("mode", "expected_requests", "expected_eligible"),
    [
        (SpecializationMode.DISCONNECTED, (), ()),
        (
            SpecializationMode.LOCAL_CONTRAST,
            ("parent-a", "parent-b"),
            (
                "parent-a|candidate:parent-a",
                "parent-b|candidate:parent-b",
            ),
        ),
        (
            SpecializationMode.COUNTEREXAMPLE_BLIND,
            ("parent-a", "parent-b"),
            (
                "parent-a|candidate:parent-a",
                "parent-a|candidate:shared",
                "parent-b|candidate:parent-b",
                "parent-b|candidate:shared",
            ),
        ),
    ],
)
def test_multi_parent_eligibility_is_batched_once_for_every_mode(
    monkeypatch: pytest.MonkeyPatch,
    mode: SpecializationMode,
    expected_requests: tuple[str, ...],
    expected_eligible: tuple[str, ...],
) -> None:
    states, snapshot, references = _specialization_case()
    original_run = authority_module.FormalReConEngine.run
    original_reference_validation = (
        authority_module._validate_current_real_reference
    )
    calls: list[dict[str, Any]] = []
    reference_validations = 0

    def recording_run(self, *args, **kwargs):
        result = original_run(self, *args, **kwargs)
        calls.append({
            "tick": self.tick,
            "until": kwargs.get("until"),
            "active_nodes": kwargs.get("active_nodes"),
            "nodes": _node_semantics(self.g),
        })
        return result

    def recording_reference_validation(*args, **kwargs):
        nonlocal reference_validations
        reference_validations += 1
        return original_reference_validation(*args, **kwargs)

    monkeypatch.setattr(
        authority_module.FormalReConEngine, "run", recording_run
    )
    monkeypatch.setattr(
        authority_module,
        "_validate_current_real_reference",
        recording_reference_validation,
    )
    assert snapshot.grounded_receipt is not None
    result = authority_module._run_authority_graph(
        states,
        snapshot,
        accepted_real_references=references,
        current_real_reference=_grounded_reference(
            snapshot.grounded_receipt
        ),
        specialization_mode=mode,
    )

    assert result["specialization_request"] == expected_requests
    assert result["specialization_eligibility"] == expected_eligible
    assert reference_validations == 1
    assert len(calls) == (1 if mode is SpecializationMode.DISCONNECTED else 2)
    assert all(call["tick"] <= 7 for call in calls)
    assert all(callable(call["until"]) for call in calls)

    rows = {
        f"{parent}|{row.identity}": row
        for parent, parent_rows in result["specialization_candidate_states"]
        for row in parent_rows
    }
    assert {
        key for key, row in rows.items() if row.confirmed
    } == set(expected_eligible)
    for key, row in rows.items():
        assert row.node_state == (
            NodeState.CONFIRMED.name
            if key in expected_eligible
            else NodeState.FAILED.name
        )
        if len(calls) == 2:
            node_semantics = calls[1]["nodes"][row.node_id]
            assert node_semantics[0] == row.node_state
            assert node_semantics[2] == (1.0 if row.confirmed else 0.0)
