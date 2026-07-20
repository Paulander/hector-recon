"""Prospective evidence authority for graph-native competence cells.

This module separates pattern discovery from lifecycle authority.  Historical
GraphNativeCompetenceEnvelope behavior remains untouched; the prospective
organism wraps a trace-native organism and owns the new law.
"""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import hmac
import json
import math
import pickle
from typing import Any, Iterable, Mapping, Sequence

from recon_lite import FormalReConEngine, FrameContext, FrameKind, Graph, Node, NodeState, NodeType
from recon_lite_hector.nodes import StemCellState

from .native_authority_handover import GraphSignalTrace
from .native_competence_envelope import (
    AVAILABLE_ROOT_ID,
    REFUTED_ROOT_ID,
    SHADOW_ROOT_ID,
    AvailabilityState,
    CompetenceContextCell,
    CompetenceEvidenceRecord,
    EnvelopeClassification,
    SpecializationMode,
    wilson_lower_bound,
)
from .native_trace_competence_authority import (
    GroundedOutcomeReceipt,
    TraceNativeCompetenceDreamSession,
    TraceNativeCompetenceOrganism,
)


SCHEMA_VERSION = "native_prospective_evidence_authority.v1"
DEFICIT_ROOT_ID = "prospective_evidence_deficit_root"


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


class CertificationMode(str, Enum):
    PROSPECTIVE = "prospective"
    LEGACY_SAME_LEDGER = "legacy_same_ledger"
    PROSPECTIVE_OUTCOME_SHUFFLED = "prospective_outcome_shuffled"


class CertificationStatus(str, Enum):
    PROVISIONAL = "provisional"
    MATURE = "mature"
    REVOKED = "revoked"
    PRUNED = "pruned"


@dataclass(frozen=True)
class ProspectiveCertificationConfig:
    mode: CertificationMode
    minimum_support: int = 4
    wilson_z: float = 1.6448536269514722
    lower_bound_threshold: float = 0.55
    outcome_shuffle_shift: int = 1
    implementation_identity: str = "prospective_certification_law.v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", CertificationMode(self.mode))
        if self.minimum_support != 4:
            raise ValueError("frozen prospective support threshold changed")
        if not math.isclose(self.wilson_z, 1.6448536269514722):
            raise ValueError("frozen Wilson z changed")
        if not math.isclose(self.lower_bound_threshold, 0.55):
            raise ValueError("frozen Wilson lower-bound threshold changed")
        if self.mode is CertificationMode.PROSPECTIVE_OUTCOME_SHUFFLED:
            if self.outcome_shuffle_shift == 0:
                raise ValueError("shuffled control requires nonzero shift")


@dataclass(frozen=True)
class ProspectiveLifecycleTransition:
    transition: str
    receipt_id: str
    event_ordinal: int
    outcome_source_receipt_id: str
    prospective_successes: int
    prospective_contradictions: int
    success_lower_bound: float


@dataclass
class ProspectiveCellCertification:
    cell_id: str
    members: tuple[str, ...]
    polarity: AvailabilityState
    lineage_parent_id: str | None
    specialization_depth: int
    birth_event_ordinal: int | None
    certification_frontier: int
    proposal_receipt_ids: tuple[str, ...]
    discovery_receipt_ids: tuple[str, ...]
    discovery_support: int
    discovery_successes: int
    discovery_failures: int
    discovery_success_lower_bound: float
    discovery_failure_lower_bound: float
    certification_receipt_ids: tuple[str, ...] = ()
    prospective_success_receipt_ids: tuple[str, ...] = ()
    prospective_contradiction_receipt_ids: tuple[str, ...] = ()
    prospective_successes: int = 0
    prospective_contradictions: int = 0
    prospective_support: int = 0
    prospective_success_lower_bound: float = 0.0
    prospective_failure_lower_bound: float = 0.0
    status: CertificationStatus = CertificationStatus.PROVISIONAL
    maturity_receipt_id: str | None = None
    revocation_receipt_id: str | None = None
    demotion_receipt_ids: tuple[str, ...] = ()
    transitions: tuple[ProspectiveLifecycleTransition, ...] = ()
    excluded_receipt_rows: tuple[dict[str, Any], ...] = ()

    @property
    def evidence_deficit(self) -> int:
        return max(0, 4 - self.prospective_successes)

    @property
    def contradiction_blocked(self) -> bool:
        return self.prospective_contradictions > 0

    def to_manifest(self) -> dict[str, Any]:
        value = asdict(self)
        value["polarity"] = self.polarity.value
        value["status"] = self.status.value
        value["transitions"] = [asdict(item) for item in self.transitions]
        return value


@dataclass(frozen=True)
class PredictionEmission:
    prediction_id: str
    prediction_ordinal: int
    trace_identity: str
    frame_kind: str
    classification: EnvelopeClassification
    active_cell_ids: tuple[str, ...]
    emitted_before_outcome: bool = True

    def to_manifest(self) -> dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "prediction_ordinal": self.prediction_ordinal,
            "trace_identity": self.trace_identity,
            "frame_kind": self.frame_kind,
            "classification": self.classification.to_manifest(),
            "active_cell_ids": list(self.active_cell_ids),
            "emitted_before_outcome": self.emitted_before_outcome,
        }


@dataclass(frozen=True)
class ValidatedCertificationEvent:
    receipt_id: str
    event_ordinal: int
    trace_identity: str
    active_signal_ids: tuple[str, ...]
    observed_outcome: bool
    frame_kind: str
    grounded_provenance: str


@dataclass(frozen=True)
class CertificationEmission:
    receipt_id: str
    inserted: bool
    prediction_id: str | None
    active_cell_ids: tuple[str, ...]
    certified_cell_ids: tuple[str, ...]
    matured_cell_ids: tuple[str, ...]
    revoked_cell_ids: tuple[str, ...]
    excluded_cell_ids: tuple[str, ...]
    outcome_source_receipt_id: str | None
    graph_local_revocation_ids: tuple[str, ...] = ()

    def to_manifest(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProspectiveEvidenceAudit:
    real_predictions: int = 0
    virtual_predictions: int = 0
    grounded_events: int = 0
    duplicate_events: int = 0
    excluded_pre_frontier: int = 0
    excluded_not_previously_active: int = 0
    matured_transitions: int = 0
    revoked_transitions: int = 0
    graph_local_revocations: int = 0
    prediction_rows: list[dict[str, Any]] = field(default_factory=list)
    receipt_rows: list[dict[str, Any]] = field(default_factory=list)
    shuffle_rows: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class _DeficitSnapshot:
    rows: tuple[tuple[str, int], ...]

    def deficit(self, cell_id: str) -> int | None:
        return dict(self.rows).get(cell_id)


@dataclass
class ProspectiveEvidenceAuthority:
    config: ProspectiveCertificationConfig
    cells: dict[str, ProspectiveCellCertification]
    pending_predictions: dict[str, PredictionEmission] = field(default_factory=dict)
    consumed_receipt_ids: set[str] = field(default_factory=set)
    emissions: dict[str, CertificationEmission] = field(default_factory=dict)
    audit: ProspectiveEvidenceAudit = field(default_factory=ProspectiveEvidenceAudit)
    _next_prediction_ordinal: int = 0

    def _cell_active(
        self, cell: ProspectiveCellCertification, active: set[str]
    ) -> bool:
        if not set(cell.members).issubset(active):
            return False
        if cell.lineage_parent_id is None:
            return True
        parent = self.cells.get(cell.lineage_parent_id)
        return bool(
            parent is not None
            and parent.status in {
                CertificationStatus.MATURE, CertificationStatus.REVOKED
            }
        )

    def classify(
        self, active_signal_ids: Iterable[str], *, policy_response: bool
    ) -> EnvelopeClassification:
        active = set(map(str, active_signal_ids))
        mature = [
            cell for cell in self.cells.values()
            if cell.status is CertificationStatus.MATURE
            and self._cell_active(cell, active)
        ]
        available_ids = tuple(sorted(
            cell.cell_id for cell in mature
            if cell.polarity is AvailabilityState.AVAILABLE
        ))
        refuted_ids = tuple(sorted(
            cell.cell_id for cell in mature
            if cell.polarity is AvailabilityState.REFUTED
        ))
        formal_available = bool(policy_response and available_ids)
        formal_refuted = bool(policy_response and refuted_ids)
        if formal_available and not formal_refuted:
            state = AvailabilityState.AVAILABLE
            probability = max(
                self.cells[cell_id].prospective_success_lower_bound
                for cell_id in available_ids
            )
            uncertainty = max(
                0.0, 1.0 - probability
            )
        elif formal_refuted and not formal_available:
            state = AvailabilityState.REFUTED
            probability = 0.0
            confidence = max(
                self.cells[cell_id].prospective_success_lower_bound
                for cell_id in refuted_ids
            )
            uncertainty = max(0.0, 1.0 - confidence)
        else:
            state = AvailabilityState.UNKNOWN
            probability = 0.5
            uncertainty = 1.0
        return EnvelopeClassification(
            state=state,
            probability=float(probability),
            uncertainty=float(uncertainty),
            available_cell_ids=available_ids,
            refuted_cell_ids=refuted_ids,
            formal_available=formal_available,
            formal_refuted=formal_refuted,
            policy_response=bool(policy_response),
        )

    def predict(
        self,
        *,
        trace_identity: str,
        active_signal_ids: Iterable[str],
        policy_response: bool,
        frame_kind: FrameKind,
    ) -> PredictionEmission:
        signals = tuple(sorted(set(map(str, active_signal_ids))))
        classification = self.classify(signals, policy_response=policy_response)
        active_ids = tuple(sorted(
            cell.cell_id for cell in self.cells.values()
            if cell.status is not CertificationStatus.PRUNED
            and self._cell_active(cell, set(signals))
        ))
        ordinal = self._next_prediction_ordinal
        prediction_id = _sha256({
            "authority": self.config.implementation_identity,
            "ordinal": ordinal,
            "trace_identity": trace_identity,
            "frame_kind": frame_kind.name,
            "active_cell_ids": active_ids,
            "classification": classification.to_manifest(),
        })
        emission = PredictionEmission(
            prediction_id=prediction_id,
            prediction_ordinal=ordinal,
            trace_identity=str(trace_identity),
            frame_kind=frame_kind.name,
            classification=classification,
            active_cell_ids=active_ids,
        )
        if frame_kind is FrameKind.REAL:
            self._next_prediction_ordinal += 1
            self.pending_predictions[prediction_id] = emission
            self.audit.real_predictions += 1
        else:
            return emission
        self.audit.prediction_rows.append(emission.to_manifest())
        return emission

    def _pending_for(self, event: ValidatedCertificationEvent) -> PredictionEmission:
        candidates = sorted(
            (
                item for item in self.pending_predictions.values()
                if item.trace_identity == event.trace_identity
                and item.frame_kind == FrameKind.REAL.name
            ),
            key=lambda item: item.prediction_ordinal,
        )
        if not candidates:
            raise RuntimeError("grounded receipt arrived without prior REAL prediction")
        return candidates[0]

    def consume(
        self,
        event: ValidatedCertificationEvent,
        *,
        authority_outcome: bool | None = None,
        outcome_source_receipt_id: str | None = None,
    ) -> CertificationEmission:
        if event.receipt_id in self.consumed_receipt_ids:
            return self.emissions[event.receipt_id]
        if event.frame_kind != FrameKind.REAL.name:
            raise ValueError("virtual events cannot certify competence")
        prediction = self._pending_for(event)
        del self.pending_predictions[prediction.prediction_id]
        outcome = event.observed_outcome if authority_outcome is None else bool(authority_outcome)
        source_id = outcome_source_receipt_id or event.receipt_id
        matured: list[str] = []
        revoked: list[str] = []
        certified: list[str] = []
        excluded: list[str] = []
        for cell_id in prediction.active_cell_ids:
            cell = self.cells[cell_id]
            if event.event_ordinal <= cell.certification_frontier:
                cell.excluded_receipt_rows = (*cell.excluded_receipt_rows, {
                    "receipt_id": event.receipt_id,
                    "event_ordinal": event.event_ordinal,
                    "reason": "at_or_before_birth_frontier",
                })
                self.audit.excluded_pre_frontier += 1
                excluded.append(cell_id)
                continue
            if event.receipt_id in cell.proposal_receipt_ids:
                raise RuntimeError("proposal event attempted to certify its own cell")
            if event.receipt_id in cell.certification_receipt_ids:
                raise RuntimeError("duplicate certification receipt in cell ledger")
            expected = cell.polarity is AvailabilityState.AVAILABLE
            supports = outcome == expected
            cell.certification_receipt_ids = (
                *cell.certification_receipt_ids, event.receipt_id
            )
            if supports:
                cell.prospective_success_receipt_ids = (
                    *cell.prospective_success_receipt_ids, event.receipt_id
                )
                cell.prospective_successes += 1
            else:
                cell.prospective_contradiction_receipt_ids = (
                    *cell.prospective_contradiction_receipt_ids, event.receipt_id
                )
                cell.prospective_contradictions += 1
            cell.prospective_support += 1
            cell.prospective_success_lower_bound = wilson_lower_bound(
                cell.prospective_successes,
                cell.prospective_support,
                self.config.wilson_z,
            )
            cell.prospective_failure_lower_bound = wilson_lower_bound(
                cell.prospective_contradictions,
                cell.prospective_support,
                self.config.wilson_z,
            )
            certified.append(cell_id)
            if (
                cell.status is CertificationStatus.PROVISIONAL
                and cell.prospective_successes >= self.config.minimum_support
                and cell.prospective_contradictions == 0
                and cell.prospective_success_lower_bound
                >= self.config.lower_bound_threshold
            ):
                cell.status = CertificationStatus.MATURE
                cell.maturity_receipt_id = event.receipt_id
                transition = ProspectiveLifecycleTransition(
                    transition="PROVISIONAL_TO_MATURE",
                    receipt_id=event.receipt_id,
                    event_ordinal=event.event_ordinal,
                    outcome_source_receipt_id=source_id,
                    prospective_successes=cell.prospective_successes,
                    prospective_contradictions=cell.prospective_contradictions,
                    success_lower_bound=cell.prospective_success_lower_bound,
                )
                cell.transitions = (*cell.transitions, transition)
                matured.append(cell_id)
            elif (
                cell.status is CertificationStatus.MATURE and not supports
            ):
                cell.status = CertificationStatus.REVOKED
                cell.revocation_receipt_id = event.receipt_id
                cell.demotion_receipt_ids = (
                    *cell.demotion_receipt_ids, event.receipt_id
                )
                transition = ProspectiveLifecycleTransition(
                    transition="MATURE_TO_REVOKED",
                    receipt_id=event.receipt_id,
                    event_ordinal=event.event_ordinal,
                    outcome_source_receipt_id=source_id,
                    prospective_successes=cell.prospective_successes,
                    prospective_contradictions=cell.prospective_contradictions,
                    success_lower_bound=cell.prospective_success_lower_bound,
                )
                cell.transitions = (*cell.transitions, transition)
                revoked.append(cell_id)
        self.consumed_receipt_ids.add(event.receipt_id)
        self.audit.grounded_events += 1
        self.audit.matured_transitions += len(matured)
        self.audit.revoked_transitions += len(revoked)
        emission = CertificationEmission(
            receipt_id=event.receipt_id,
            inserted=True,
            prediction_id=prediction.prediction_id,
            active_cell_ids=prediction.active_cell_ids,
            certified_cell_ids=tuple(certified),
            matured_cell_ids=tuple(matured),
            revoked_cell_ids=tuple(revoked),
            excluded_cell_ids=tuple(excluded),
            outcome_source_receipt_id=source_id,
        )
        self.emissions[event.receipt_id] = emission
        self.audit.receipt_rows.append({
            **emission.to_manifest(),
            "event_ordinal": event.event_ordinal,
            "observed_outcome": event.observed_outcome,
            "authority_outcome": outcome,
            "grounded_provenance": event.grounded_provenance,
        })
        return emission

    def consume_frozen_shuffled_batch(
        self, events: Sequence[ValidatedCertificationEvent]
    ) -> tuple[CertificationEmission, ...]:
        if self.config.mode is not CertificationMode.PROSPECTIVE_OUTCOME_SHUFFLED:
            raise RuntimeError("frozen shuffle is only available in control arm")
        if not events:
            return ()
        shift = self.config.outcome_shuffle_shift % len(events)
        outcomes = [event.observed_outcome for event in events]
        emissions = []
        for index, event in enumerate(events):
            source_index = (index + shift) % len(events)
            source = events[source_index]
            emission = self.consume(
                event,
                authority_outcome=outcomes[source_index],
                outcome_source_receipt_id=source.receipt_id,
            )
            self.audit.shuffle_rows.append({
                "receipt_id": event.receipt_id,
                "outcome_source_receipt_id": source.receipt_id,
                "observed_outcome": event.observed_outcome,
                "authority_outcome": outcomes[source_index],
            })
            emissions.append(emission)
        return tuple(emissions)

    def legacy_certify(
        self, events: Sequence[ValidatedCertificationEvent]
    ) -> tuple[str, ...]:
        if self.config.mode is not CertificationMode.LEGACY_SAME_LEDGER:
            raise RuntimeError("legacy certification is only available in control arm")
        matured = []
        for cell in self.cells.values():
            matching = [
                event for event in events
                if set(cell.members).issubset(event.active_signal_ids)
            ]
            successes = sum(
                event.observed_outcome
                == (cell.polarity is AvailabilityState.AVAILABLE)
                for event in matching
            )
            contradictions = len(matching) - successes
            lower = wilson_lower_bound(successes, len(matching), self.config.wilson_z)
            if (
                successes >= self.config.minimum_support
                and contradictions == 0
                and lower >= self.config.lower_bound_threshold
            ):
                cell.certification_receipt_ids = tuple(
                    event.receipt_id for event in matching
                )
                cell.prospective_success_receipt_ids = cell.certification_receipt_ids
                cell.prospective_successes = successes
                cell.prospective_support = len(matching)
                cell.prospective_success_lower_bound = lower
                cell.status = CertificationStatus.MATURE
                cell.maturity_receipt_id = matching[-1].receipt_id
                cell.transitions = (*cell.transitions, ProspectiveLifecycleTransition(
                    transition="LEGACY_SAME_LEDGER_TO_MATURE",
                    receipt_id=matching[-1].receipt_id,
                    event_ordinal=matching[-1].event_ordinal,
                    outcome_source_receipt_id=matching[-1].receipt_id,
                    prospective_successes=successes,
                    prospective_contradictions=0,
                    success_lower_bound=lower,
                ))
                matured.append(cell.cell_id)
        self.audit.matured_transitions += len(matured)
        return tuple(sorted(matured))

    def deficit_manifest(self) -> dict[str, Any]:
        graph = Graph()
        graph.add_node(Node(
            DEFICIT_ROOT_ID,
            NodeType.SCRIPT,
            meta={"confirm_policy": "and", "role": "prospective_evidence_deficit"},
        ))
        live = [
            cell for cell in sorted(self.cells.values(), key=lambda item: item.cell_id)
            if cell.status in {CertificationStatus.PROVISIONAL, CertificationStatus.MATURE}
        ]
        for cell in live:
            node_id = "prospective_evidence_deficit:" + cell.cell_id
            graph.add_node(Node(
                node_id,
                NodeType.TERMINAL,
                predicate=_prospective_deficit_terminal,
                meta={
                    "terminal_kind": "EVIDENCE_DEFICIT",
                    "cell_id": cell.cell_id,
                },
            ))
            graph.add_hierarchy_pair(DEFICIT_ROOT_ID, node_id)
        if not live:
            graph.add_node(Node(
                "prospective_evidence_deficit:none",
                NodeType.TERMINAL,
                predicate=_zero_deficit_terminal,
                meta={"terminal_kind": "EVIDENCE_DEFICIT_EMPTY"},
            ))
            graph.add_hierarchy_pair(
                DEFICIT_ROOT_ID, "prospective_evidence_deficit:none"
            )
        snapshot = _DeficitSnapshot(tuple(
            (cell.cell_id, cell.evidence_deficit) for cell in live
        ))
        engine = FormalReConEngine(graph, record_trace=False)
        engine.request(DEFICIT_ROOT_ID)
        engine.run(
            max_ticks=max(16, len(live) * 4),
            env={"prospective_deficit_snapshot": snapshot},
            until=lambda item: item.g.nodes[DEFICIT_ROOT_ID].state
            in {NodeState.CONFIRMED, NodeState.FAILED},
        )
        rows = []
        for cell in live:
            node = graph.nodes["prospective_evidence_deficit:" + cell.cell_id]
            rows.append({
                "cell_id": cell.cell_id,
                "deficit": int(node.activation.value),
                "terminal_state": node.state.name,
                "terminal_kind": node.meta["terminal_kind"],
                "changed_exposure": False,
                "scheduled_trial": False,
            })
        return {
            "root_state": graph.nodes[DEFICIT_ROOT_ID].state.name,
            "rows": rows,
            "changed_exposure": False,
            "scheduled_trials": 0,
        }

    def to_manifest(self) -> dict[str, Any]:
        return {
            "config": {
                **asdict(self.config),
                "mode": self.config.mode.value,
            },
            "cells": [
                cell.to_manifest()
                for cell in sorted(self.cells.values(), key=lambda item: item.cell_id)
            ],
            "pending_predictions": {
                key: value.to_manifest()
                for key, value in sorted(self.pending_predictions.items())
            },
            "consumed_receipt_ids": sorted(self.consumed_receipt_ids),
            "emissions": {
                key: value.to_manifest()
                for key, value in sorted(self.emissions.items())
            },
            "audit": asdict(self.audit),
            "next_prediction_ordinal": self._next_prediction_ordinal,
            "deficit_manifest": self.deficit_manifest(),
        }


def _prospective_deficit_terminal(
    node: Node, env: Mapping[str, Any]
) -> tuple[bool, bool]:
    snapshot = env.get("prospective_deficit_snapshot")
    if not isinstance(snapshot, _DeficitSnapshot):
        node.activation.value = 0.0
        return True, False
    deficit = snapshot.deficit(str(node.meta["cell_id"]))
    if deficit is None:
        node.activation.value = 0.0
        return True, False
    node.activation.value = float(deficit)
    return True, True


def _zero_deficit_terminal(
    node: Node, _env: Mapping[str, Any]
) -> tuple[bool, bool]:
    node.activation.value = 0.0
    return True, True


def _flatten_members(
    cell: CompetenceContextCell,
    cells: Mapping[str, CompetenceContextCell],
    visiting: set[str] | None = None,
) -> tuple[str, ...]:
    seen = set() if visiting is None else set(visiting)
    if cell.cell_id in seen:
        raise RuntimeError("cyclic competence lineage")
    seen.add(cell.cell_id)
    members: set[str] = set()
    for member in cell.members:
        if member.startswith("context:"):
            parent_id = member.split(":", 1)[1]
            parent = cells.get(parent_id)
            if parent is None:
                raise RuntimeError("missing lineage parent")
            members.update(_flatten_members(parent, cells, seen))
        else:
            members.add(member)
    return tuple(sorted(members))


def _proposal_receipts(
    organism: TraceNativeCompetenceOrganism,
    cell: CompetenceContextCell,
) -> tuple[str, ...]:
    if cell.specialization_depth == 1:
        found = [
            str(row["evidence_key"])
            for row in organism.envelope.specialization_audit.request_rows
            if row.get("cell_id") == cell.cell_id and row.get("admitted")
        ]
        return tuple(sorted(set(found)))
    ordered = sorted(
        organism.receipts.values(), key=lambda item: item.event_ordinal
    )
    ordinal = cell.born_request_ordinal
    if 0 <= ordinal < len(ordered):
        return (ordered[ordinal].event_id,)
    return ()


def _birth_event_ordinal(
    organism: TraceNativeCompetenceOrganism,
    proposal_receipt_ids: Sequence[str],
) -> int | None:
    ordinals = [
        organism.receipts[item].event_ordinal
        for item in proposal_receipt_ids
        if item in organism.receipts
    ]
    return max(ordinals) if ordinals else None


@dataclass
class NativeProspectiveCompetenceOrganism:
    base: TraceNativeCompetenceOrganism
    authority: ProspectiveEvidenceAuthority
    schema_version: str = SCHEMA_VERSION

    @classmethod
    def from_frozen_patterns(
        cls,
        source: TraceNativeCompetenceOrganism,
        *,
        config: ProspectiveCertificationConfig,
        certification_frontier: int,
        reset_historical_authority: bool,
    ) -> "NativeProspectiveCompetenceOrganism":
        base = copy.deepcopy(source)
        states: dict[str, ProspectiveCellCertification] = {}
        for cell in sorted(
            base.envelope.cells.values(), key=lambda item: item.cell_id
        ):
            if cell.state is StemCellState.PRUNED or cell.polarity is None:
                continue
            proposal_ids = _proposal_receipts(base, cell)
            state = ProspectiveCellCertification(
                cell_id=cell.cell_id,
                members=_flatten_members(cell, base.envelope.cells),
                polarity=cell.polarity,
                lineage_parent_id=cell.lineage_parent_id,
                specialization_depth=cell.specialization_depth,
                birth_event_ordinal=_birth_event_ordinal(base, proposal_ids),
                certification_frontier=int(certification_frontier),
                proposal_receipt_ids=proposal_ids,
                discovery_receipt_ids=tuple(cell.evidence_keys),
                discovery_support=int(cell.support),
                discovery_successes=int(cell.successes),
                discovery_failures=int(cell.failures),
                discovery_success_lower_bound=float(cell.success_lower_bound),
                discovery_failure_lower_bound=float(cell.failure_lower_bound),
                status=(
                    CertificationStatus.MATURE
                    if not reset_historical_authority and cell.is_mature
                    else (
                        CertificationStatus.REVOKED
                        if (
                            not reset_historical_authority
                            and cell.state is StemCellState.PROBATION
                        )
                        else CertificationStatus.PROVISIONAL
                    )
                ),
            )
            setattr(cell, "prospective_certification", state)
            states[cell.cell_id] = state
            if reset_historical_authority:
                cell.stem_cell.state = StemCellState.TRIAL
                cell.stem_cell.trial_parent_id = SHADOW_ROOT_ID
                cell.stem_cell.metadata["shadow_only"] = True
                cell.stem_cell.metadata["historical_maturity_authority_removed"] = True
        base.envelope.rebuild_graph()
        return cls(
            base=base,
            authority=ProspectiveEvidenceAuthority(config=config, cells=states),
        )

    def register_new_cells(
        self, *, certification_frontier: int
    ) -> tuple[str, ...]:
        """Attach the prospective law to every newly materialized graph cell.

        Discovery remains owned by the frozen envelope/genome.  This hook only
        removes same-ledger authority and records the frontier after which a
        distinct grounded receipt may certify the already-existing cell.
        """
        registered: list[str] = []
        for cell in sorted(
            self.base.envelope.cells.values(), key=lambda item: item.cell_id
        ):
            if (
                cell.cell_id in self.authority.cells
                or cell.state is StemCellState.PRUNED
                or cell.polarity is None
            ):
                continue
            proposal_ids = _proposal_receipts(self.base, cell)
            birth_ordinal = _birth_event_ordinal(self.base, proposal_ids)
            frontier = max(
                int(certification_frontier),
                -1 if birth_ordinal is None else birth_ordinal,
            )
            state = ProspectiveCellCertification(
                cell_id=cell.cell_id,
                members=_flatten_members(cell, self.base.envelope.cells),
                polarity=cell.polarity,
                lineage_parent_id=cell.lineage_parent_id,
                specialization_depth=cell.specialization_depth,
                birth_event_ordinal=birth_ordinal,
                certification_frontier=frontier,
                proposal_receipt_ids=proposal_ids,
                discovery_receipt_ids=tuple(cell.evidence_keys),
                discovery_support=int(cell.support),
                discovery_successes=int(cell.successes),
                discovery_failures=int(cell.failures),
                discovery_success_lower_bound=float(cell.success_lower_bound),
                discovery_failure_lower_bound=float(cell.failure_lower_bound),
                status=CertificationStatus.PROVISIONAL,
            )
            setattr(cell, "prospective_certification", state)
            self.authority.cells[cell.cell_id] = state
            cell.stem_cell.state = StemCellState.TRIAL
            cell.stem_cell.trial_parent_id = SHADOW_ROOT_ID
            cell.stem_cell.metadata["shadow_only"] = True
            cell.stem_cell.metadata["prospective_authority_required"] = True
            registered.append(cell.cell_id)
        if registered:
            self.base.envelope.rebuild_graph()
        return tuple(registered)

    def _sync_graph_authority(
        self,
        emission: CertificationEmission,
        record: CompetenceEvidenceRecord,
    ) -> CertificationEmission:
        graph_revoked: list[str] = []
        if emission.revoked_cell_ids:
            query = self.base.envelope._emit_mature_correction(
                record, specialization_mode=SpecializationMode.DISCONNECTED
            )
            confirmed = set(query["confirmed_cell_ids"])
            for cell_id in emission.revoked_cell_ids:
                if cell_id not in confirmed:
                    raise RuntimeError(
                        "prospective contradiction lacked graph-local revocation"
                    )
                graph_revoked.append(cell_id)
        for cell_id in emission.matured_cell_ids:
            cell = self.base.envelope.cells[cell_id]
            state = self.authority.cells[cell_id]
            if (
                state.prospective_successes < self.authority.config.minimum_support
                or state.prospective_contradictions
            ):
                raise RuntimeError("prospective maturity violated frozen law")
            cell.stem_cell.state = StemCellState.MATURE
            cell.stem_cell.trial_parent_id = (
                AVAILABLE_ROOT_ID
                if cell.polarity is AvailabilityState.AVAILABLE
                else REFUTED_ROOT_ID
            )
            cell.stem_cell.metadata["shadow_only"] = False
            cell.stem_cell.metadata["prospective_maturity_receipt_id"] = (
                state.maturity_receipt_id
            )
        for cell_id in emission.revoked_cell_ids:
            cell = self.base.envelope.cells[cell_id]
            cell.stem_cell.state = StemCellState.PROBATION
            cell.stem_cell.metadata["maturity_revoked"] = True
            cell.stem_cell.metadata["prospective_revocation_receipt_id"] = (
                self.authority.cells[cell_id].revocation_receipt_id
            )
        if emission.matured_cell_ids or emission.revoked_cell_ids:
            self.base.envelope.rebuild_graph()
        self.authority.audit.graph_local_revocations += len(graph_revoked)
        updated = CertificationEmission(
            **{
                **emission.to_manifest(),
                "graph_local_revocation_ids": tuple(graph_revoked),
            }
        )
        self.authority.emissions[emission.receipt_id] = updated
        return updated

    def predict_real_trace(self, trace: GraphSignalTrace) -> PredictionEmission:
        self.base._validate_trace(trace, require_real=True)
        return self.authority.predict(
            trace_identity=trace.digest(),
            active_signal_ids=trace.ordered_signal_identities,
            policy_response=True,
            frame_kind=FrameKind.REAL,
        )

    def observe_grounded(
        self, receipt: GroundedOutcomeReceipt
    ) -> CertificationEmission:
        record, inserted = self.base._accept_receipt(receipt)
        if not inserted:
            prior = self.authority.emissions.get(receipt.event_id)
            if prior is None:
                raise RuntimeError("receipt predates prospective authority")
            return prior
        event = ValidatedCertificationEvent(
            receipt_id=receipt.event_id,
            event_ordinal=receipt.event_ordinal,
            trace_identity=receipt.decision_trace.digest(),
            active_signal_ids=receipt.decision_trace.ordered_signal_identities,
            observed_outcome=receipt.observed_terminal_result,
            frame_kind=receipt.decision_trace.frame_kind,
            grounded_provenance=receipt.completion_terminal_provenance,
        )
        emission = self.authority.consume(event)
        return self._sync_graph_authority(emission, record)

    def observe_grounded_shuffled(
        self,
        receipt: GroundedOutcomeReceipt,
        outcome_source: GroundedOutcomeReceipt,
    ) -> CertificationEmission:
        if (
            self.authority.config.mode
            is not CertificationMode.PROSPECTIVE_OUTCOME_SHUFFLED
        ):
            raise RuntimeError("outcome shuffle is only available in frozen control")
        self.base._validate_receipt(outcome_source)
        record, inserted = self.base._accept_receipt(receipt)
        if not inserted:
            prior = self.authority.emissions.get(receipt.event_id)
            if prior is None:
                raise RuntimeError("receipt predates prospective authority")
            return prior
        event = ValidatedCertificationEvent(
            receipt_id=receipt.event_id,
            event_ordinal=receipt.event_ordinal,
            trace_identity=receipt.decision_trace.digest(),
            active_signal_ids=receipt.decision_trace.ordered_signal_identities,
            observed_outcome=receipt.observed_terminal_result,
            frame_kind=receipt.decision_trace.frame_kind,
            grounded_provenance=receipt.completion_terminal_provenance,
        )
        emission = self.authority.consume(
            event,
            authority_outcome=outcome_source.observed_terminal_result,
            outcome_source_receipt_id=outcome_source.event_id,
        )
        self.authority.audit.shuffle_rows.append({
            "receipt_id": receipt.event_id,
            "outcome_source_receipt_id": outcome_source.event_id,
            "observed_outcome": receipt.observed_terminal_result,
            "authority_outcome": outcome_source.observed_terminal_result,
        })
        return self._sync_graph_authority(emission, record)

    def observe_grounded_shuffled_batch(
        self, receipts: Sequence[GroundedOutcomeReceipt]
    ) -> tuple[CertificationEmission, ...]:
        if (
            self.authority.config.mode
            is not CertificationMode.PROSPECTIVE_OUTCOME_SHUFFLED
        ):
            raise RuntimeError("outcome shuffle is only available in frozen control")
        validated: list[tuple[ValidatedCertificationEvent, CompetenceEvidenceRecord]] = []
        for receipt in receipts:
            record, inserted = self.base._accept_receipt(receipt)
            if not inserted:
                raise RuntimeError("shuffled batch contains duplicate receipt")
            validated.append((
                ValidatedCertificationEvent(
                    receipt_id=receipt.event_id,
                    event_ordinal=receipt.event_ordinal,
                    trace_identity=receipt.decision_trace.digest(),
                    active_signal_ids=receipt.decision_trace.ordered_signal_identities,
                    observed_outcome=receipt.observed_terminal_result,
                    frame_kind=receipt.decision_trace.frame_kind,
                    grounded_provenance=receipt.completion_terminal_provenance,
                ),
                record,
            ))
        outcomes = [event.observed_outcome for event, _record in validated]
        shift = self.authority.config.outcome_shuffle_shift % len(outcomes)
        shifted = outcomes[shift:] + outcomes[:shift]
        emissions = []
        for index, ((event, record), outcome) in enumerate(zip(validated, shifted, strict=True)):
            source_index = (index + shift) % len(validated)
            source_id = validated[source_index][0].receipt_id
            emission = self.authority.consume(
                event,
                authority_outcome=outcome,
                outcome_source_receipt_id=source_id,
            )
            self.authority.audit.shuffle_rows.append({
                "receipt_id": event.receipt_id,
                "outcome_source_receipt_id": source_id,
                "observed_outcome": event.observed_outcome,
                "authority_outcome": outcome,
            })
            emissions.append(self._sync_graph_authority(emission, record))
        return tuple(emissions)

    def dream_session(self) -> "NativeProspectiveDreamSession":
        return NativeProspectiveDreamSession(self)

    def continuation_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "base_v3": self.base.continuation_manifest_v3(),
            "authority": self.authority.to_manifest(),
        }

    def continuation_digest(self) -> str:
        return _sha256(self.continuation_manifest())

    def dumps(self) -> bytes:
        return pickle.dumps(copy.deepcopy(self), protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def loads(cls, payload: bytes) -> "NativeProspectiveCompetenceOrganism":
        item = pickle.loads(payload)
        if not isinstance(item, cls):
            raise TypeError("serialized prospective organism has wrong type")
        for cell_id, state in item.authority.cells.items():
            attached = getattr(
                item.base.envelope.cells[cell_id],
                "prospective_certification",
                None,
            )
            if attached is None or attached.to_manifest() != state.to_manifest():
                raise RuntimeError("cell-local prospective state restore mismatch")
        item.base._canonical_rebuild()
        return item


class NativeProspectiveDreamSession:
    def __init__(self, organism: NativeProspectiveCompetenceOrganism) -> None:
        self.organism = organism
        self.before = organism.continuation_digest()
        self.base_session: TraceNativeCompetenceDreamSession = (
            organism.base.dream_session()
        )
        self.closed = False

    def request(self, frame: FrameContext) -> Any:
        if self.closed:
            raise RuntimeError("prospective dream session is closed")
        query = self.base_session.r0_session.request(frame)
        trace = query.graph_signal_trace
        classification = (
            EnvelopeClassification(
                AvailabilityState.UNKNOWN, 0.5, 1.0, (), (), False, False, False
            )
            if trace is None
            else self.organism.authority.classify(
                trace.ordered_signal_identities, policy_response=True
            )
        )
        if self.organism.continuation_digest() != self.before:
            raise RuntimeError("virtual prospective evaluation mutated authority")
        return {
            "query": query,
            "classification": classification,
            "certification_support_added": 0,
        }

    def close(self) -> None:
        self.base_session.close()
        if self.organism.continuation_digest() != self.before:
            raise RuntimeError("virtual prospective session leaked")
        self.closed = True


@dataclass(frozen=True)
class SyntheticGroundedReceipt:
    event_id: str
    event_ordinal: int
    active_signal_ids: tuple[str, ...]
    observed_outcome: bool
    frame_kind: str
    issuer_identity: str
    signature: str

    def unsigned_manifest(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_ordinal": self.event_ordinal,
            "active_signal_ids": list(self.active_signal_ids),
            "observed_outcome": self.observed_outcome,
            "frame_kind": self.frame_kind,
            "issuer_identity": self.issuer_identity,
        }


@dataclass(frozen=True)
class SyntheticReceiptIssuer:
    identity: str = "generic_sequential_environment.v1"
    capability_key: str = "generic-prospective-canary-capability.v1"

    def mint(
        self,
        *,
        event_ordinal: int,
        active_signal_ids: Iterable[str],
        observed_outcome: bool,
    ) -> SyntheticGroundedReceipt:
        signals = tuple(sorted(set(map(str, active_signal_ids))))
        event_id = _sha256({
            "issuer": self.identity,
            "ordinal": event_ordinal,
            "signals": signals,
            "outcome": bool(observed_outcome),
        })
        unsigned = {
            "event_id": event_id,
            "event_ordinal": int(event_ordinal),
            "active_signal_ids": list(signals),
            "observed_outcome": bool(observed_outcome),
            "frame_kind": FrameKind.REAL.name,
            "issuer_identity": self.identity,
        }
        signature = hmac.new(
            self.capability_key.encode("utf-8"),
            _canonical_json(unsigned),
            hashlib.sha256,
        ).hexdigest()
        return SyntheticGroundedReceipt(
            event_id=event_id,
            event_ordinal=int(event_ordinal),
            active_signal_ids=signals,
            observed_outcome=bool(observed_outcome),
            frame_kind=FrameKind.REAL.name,
            issuer_identity=self.identity,
            signature=signature,
        )

    def validate(
        self, receipt: SyntheticGroundedReceipt
    ) -> ValidatedCertificationEvent:
        if receipt.issuer_identity != self.identity:
            raise RuntimeError("untrusted synthetic receipt issuer")
        expected = hmac.new(
            self.capability_key.encode("utf-8"),
            _canonical_json(receipt.unsigned_manifest()),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(receipt.signature, expected):
            raise RuntimeError("synthetic grounded receipt signature mismatch")
        if receipt.frame_kind != FrameKind.REAL.name:
            raise ValueError("synthetic virtual receipt cannot be grounded")
        return ValidatedCertificationEvent(
            receipt_id=receipt.event_id,
            event_ordinal=receipt.event_ordinal,
            trace_identity=_sha256({
                "ordinal": receipt.event_ordinal,
                "signals": receipt.active_signal_ids,
            }),
            active_signal_ids=receipt.active_signal_ids,
            observed_outcome=receipt.observed_outcome,
            frame_kind=receipt.frame_kind,
            grounded_provenance="signed_generic_real_environment_observation",
        )


def synthetic_prediction(
    authority: ProspectiveEvidenceAuthority,
    receipt: SyntheticGroundedReceipt,
) -> PredictionEmission:
    return authority.predict(
        trace_identity=_sha256({
            "ordinal": receipt.event_ordinal,
            "signals": receipt.active_signal_ids,
        }),
        active_signal_ids=receipt.active_signal_ids,
        policy_response=True,
        frame_kind=FrameKind.REAL,
    )
