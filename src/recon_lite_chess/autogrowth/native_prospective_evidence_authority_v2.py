"""Graph-native prospective competence-evidence authority V2."""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import hmac
import json
import pickle
from typing import Any, Mapping, Sequence

import chess

from recon_lite import FormalReConEngine, FrameContext, FrameKind, Graph, Node, NodeState, NodeType
from recon_lite_hector.nodes import StemCellState

from .native_authority_handover import GraphActuation, GraphSignalTrace
from .native_competence_envelope import (
    AvailabilityState, CompetenceContextCell, EnvelopeClassification,
    wilson_lower_bound,
)
from .native_trace_competence_authority import TraceNativeCompetenceOrganism


SCHEMA_VERSION = "native_prospective_evidence_authority_v2.v2"
IMPLEMENTATION_IDENTITY = "native_prospective_two_phase_authority.v2"
EXPECTED_RECEIPT_ISSUER = "native_v2_environment_terminal"
OUTCOME_TERMINAL_IDENTITY = "native_r0_real_completion_terminal"
AUTHORITY_ROLES = (
    "commitment", "available", "refuted", "support", "contradiction",
    "maturity", "revocation",
)
ROLE_ROOTS = {role: f"v2_authority_{role}_root" for role in AUTHORITY_ROLES}
NOMINATION_READ_CATEGORIES = (
    "direct", "parent_support", "eligibility", "contradiction_trigger",
)
WILSON_Z = 1.6448536269514722
MIN_SUPPORT = 4
LOWER_BOUND = 0.55


def _json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_json(value)).hexdigest()


class ProspectiveV2IntegrityError(RuntimeError):
    """Fail-hard causal, structural, or authority contract violation."""


class ProspectiveProvenanceUnavailable(ProspectiveV2IntegrityError):
    """Exact discovery provenance is unavailable."""


class V2Mode(str, Enum):
    PROSPECTIVE = "prospective"
    LEGACY = "legacy_same_ledger"


class ProvenanceKind(str, Enum):
    HISTORICAL_ACCEPTED_LEDGER = "historical_complete_accepted_ledger"
    EXACT_NOMINATION_READ_SET = "exact_nomination_read_set"


@dataclass(frozen=True)
class FrozenHypothesis:
    cell_id: str
    members: tuple[str, ...]
    polarity: AvailabilityState
    lineage_parent_id: str | None
    specialization_depth: int
    discovery_receipt_ids: tuple[str, ...]
    discovery_receipt_digest: str
    birth_frontier: int
    structural_state: str
    provenance_kind: ProvenanceKind = ProvenanceKind.EXACT_NOMINATION_READ_SET
    nomination_read_sets: tuple[tuple[str, tuple[str, ...]], ...] = ()

    def __post_init__(self) -> None:
        if self.polarity is None:
            raise ProspectiveV2IntegrityError(
                "polarity=None at live candidate birth is forbidden"
            )
        object.__setattr__(self, "polarity", AvailabilityState(self.polarity))
        object.__setattr__(
            self, "provenance_kind", ProvenanceKind(self.provenance_kind)
        )
        if not self.members:
            raise ProspectiveV2IntegrityError("empty pattern at candidate birth")
        canonical = tuple(sorted(set(self.discovery_receipt_ids)))
        if not canonical:
            raise ProspectiveProvenanceUnavailable(
                "prospective_provenance_unavailable: empty discovery set"
            )
        if canonical != self.discovery_receipt_ids:
            raise ProspectiveV2IntegrityError(
                "discovery receipt IDs are not canonical"
            )
        if self.discovery_receipt_digest != _sha(list(canonical)):
            raise ProspectiveV2IntegrityError("discovery receipt digest mismatch")
        categories = tuple(
            (str(name), tuple(sorted(set(receipt_ids))))
            for name, receipt_ids in self.nomination_read_sets
        )
        if categories != self.nomination_read_sets:
            raise ProspectiveV2IntegrityError(
                "nomination read sets are not canonical"
            )
        if self.provenance_kind is ProvenanceKind.HISTORICAL_ACCEPTED_LEDGER:
            if categories:
                raise ProspectiveV2IntegrityError(
                    "historical escrow cannot claim exact nomination reads"
                )
        else:
            if tuple(name for name, _ids in categories) != NOMINATION_READ_CATEGORIES:
                raise ProspectiveProvenanceUnavailable(
                    "prospective_provenance_unavailable: incomplete nomination read set"
                )
            union = tuple(sorted({
                receipt_id
                for _name, receipt_ids in categories
                for receipt_id in receipt_ids
            }))
            if union != canonical:
                raise ProspectiveV2IntegrityError(
                    "nomination read-set union differs from discovery ledger"
                )

    def manifest(self) -> dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "members": list(self.members),
            "polarity": self.polarity.value,
            "lineage_parent_id": self.lineage_parent_id,
            "specialization_depth": self.specialization_depth,
            "discovery_receipt_ids": list(self.discovery_receipt_ids),
            "discovery_receipt_digest": self.discovery_receipt_digest,
            "birth_frontier": self.birth_frontier,
            "structural_state": self.structural_state,
            "provenance_kind": self.provenance_kind.value,
            "nomination_read_sets": {
                name: list(receipt_ids)
                for name, receipt_ids in self.nomination_read_sets
            },
        }


@dataclass(frozen=True)
class CellStructuralInvariant:
    cell_id: str
    members: tuple[str, ...]
    polarity: AvailabilityState
    lineage_parent_id: str | None
    specialization_depth: int
    structural_state: str
    authority_node_ids: tuple[str, ...]
    authority_topology_identity: str

    def manifest(self) -> dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "members": list(self.members),
            "polarity": self.polarity.value,
            "lineage_parent_id": self.lineage_parent_id,
            "specialization_depth": self.specialization_depth,
            "structural_state": self.structural_state,
            "authority_node_ids": list(self.authority_node_ids),
            "authority_topology_identity": self.authority_topology_identity,
        }


@dataclass
class ProspectiveAuthorityState:
    hypothesis: FrozenHypothesis
    prospectively_certified: bool
    certification_receipt_ids: tuple[str, ...] = ()
    support_receipt_ids: tuple[str, ...] = ()
    contradiction_receipt_ids: tuple[str, ...] = ()
    successes: int = 0
    contradictions: int = 0
    support: int = 0
    success_lower_bound: float = 0.0
    contradiction_lower_bound: float = 0.0
    transition_rows: tuple[dict[str, Any], ...] = ()

    def manifest(self) -> dict[str, Any]:
        return {
            "hypothesis": self.hypothesis.manifest(),
            "prospectively_certified": self.prospectively_certified,
            "certification_receipt_ids": list(self.certification_receipt_ids),
            "support_receipt_ids": list(self.support_receipt_ids),
            "contradiction_receipt_ids": list(self.contradiction_receipt_ids),
            "successes": self.successes,
            "contradictions": self.contradictions,
            "support": self.support,
            "success_lower_bound": self.success_lower_bound,
            "contradiction_lower_bound": self.contradiction_lower_bound,
            "transition_rows": list(self.transition_rows),
        }


@dataclass(frozen=True)
class PendingRealEvent:
    ordinal: int
    frame_id: str
    trace_digest: str
    typed_signal_digest: str
    source_organism_identity: str
    source_state_identity: str
    predecessor_fen: str
    actuation: GraphActuation
    pre_outcome_classification: EnvelopeClassification
    matching_cell_ids: tuple[str, ...]
    matching_cell_digest: str
    structure_invariant_digest: str
    pending_token: str
    outcome_terminal_identity: str
    state: str = "OPEN"

    def manifest(self) -> dict[str, Any]:
        return {
            "ordinal": self.ordinal,
            "frame_id": self.frame_id,
            "trace_digest": self.trace_digest,
            "typed_signal_digest": self.typed_signal_digest,
            "source_organism_identity": self.source_organism_identity,
            "source_state_identity": self.source_state_identity,
            "predecessor_fen": self.predecessor_fen,
            "actuation": asdict(self.actuation),
            "pre_outcome_classification":
                self.pre_outcome_classification.to_manifest(),
            "matching_cell_ids": list(self.matching_cell_ids),
            "matching_cell_digest": self.matching_cell_digest,
            "structure_invariant_digest": self.structure_invariant_digest,
            "pending_token": self.pending_token,
            "outcome_terminal_identity": self.outcome_terminal_identity,
            "state": self.state,
        }


@dataclass(frozen=True)
class V2GroundedReceipt:
    receipt_id: str
    ordinal: int
    pending_token: str
    frame_kind: str
    source_organism_identity: str
    source_state_identity: str
    predecessor_fen: str
    trace: GraphSignalTrace
    selected_actuation: GraphActuation
    successor_fen: str
    outcome_terminal_identity: str
    observed_outcome: bool
    interaction_fingerprint: str
    issuer_identity: str
    signature: str

    def unsigned_manifest(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "ordinal": self.ordinal,
            "pending_token": self.pending_token,
            "frame_kind": self.frame_kind,
            "source_organism_identity": self.source_organism_identity,
            "source_state_identity": self.source_state_identity,
            "predecessor_fen": self.predecessor_fen,
            "trace": self.trace.canonical_manifest(),
            "selected_actuation": asdict(self.selected_actuation),
            "successor_fen": self.successor_fen,
            "outcome_terminal_identity": self.outcome_terminal_identity,
            "observed_outcome": self.observed_outcome,
            "interaction_fingerprint": self.interaction_fingerprint,
            "issuer_identity": self.issuer_identity,
        }

    def manifest(self) -> dict[str, Any]:
        return {**self.unsigned_manifest(), "signature": self.signature}


@dataclass(frozen=True)
class V2CertificationEmission:
    receipt_id: str
    matching_cell_ids: tuple[str, ...]
    supporting_cell_ids: tuple[str, ...]
    contradiction_cell_ids: tuple[str, ...]
    matured_cell_ids: tuple[str, ...]
    revoked_cell_ids: tuple[str, ...]
    graph_maturity_ids: tuple[str, ...]
    graph_revocation_ids: tuple[str, ...]
    nomination_allowed_after_lifecycle: bool

    def manifest(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AuthorityMeasurementSnapshot:
    trace: GraphSignalTrace
    grounded_receipt: V2GroundedReceipt | None = None


@dataclass(frozen=True)
class ExposureProbe:
    predecessor_fen: str
    trace: GraphSignalTrace
    outcome_terminal_identity: str = OUTCOME_TERMINAL_IDENTITY


def _cell_node_ids(cell_id: str) -> tuple[str, ...]:
    return tuple(f"v2:{role}:{cell_id}" for role in AUTHORITY_ROLES)


def _cell_topology_identity(cell_id: str) -> str:
    return _sha({
        "cell_id": cell_id,
        "nodes": list(_cell_node_ids(cell_id)),
        "edges": [
            [ROLE_ROOTS[role], f"v2:{role}:{cell_id}", "SUB_SUR"]
            for role in AUTHORITY_ROLES
        ],
    })


def _authority_topology_manifest(
    states: Mapping[str, ProspectiveAuthorityState],
) -> dict[str, Any]:
    return {
        "roles": list(AUTHORITY_ROLES),
        "roots": dict(sorted(ROLE_ROOTS.items())),
        "cells": {
            cell_id: {
                "node_ids": list(_cell_node_ids(cell_id)),
                "topology_identity": _cell_topology_identity(cell_id),
            }
            for cell_id in sorted(states)
        },
    }


def _structural_pattern_matches(
    cell_id: str,
    states: Mapping[str, ProspectiveAuthorityState],
    active_signal_ids: Sequence[str],
    visiting: frozenset[str] = frozenset(),
) -> bool:
    if cell_id in visiting:
        raise ProspectiveV2IntegrityError("cyclic competence context")
    state = states.get(cell_id)
    if state is None:
        return False
    hypothesis = state.hypothesis
    active = set(active_signal_ids)
    next_visiting = visiting | {cell_id}
    for member in hypothesis.members:
        if member.startswith("context:"):
            parent_id = member.split(":", 1)[1]
            parent = states.get(parent_id)
            if parent is None:
                return False
            parent_state = parent.hypothesis.structural_state
            parent_usable = parent_state in {
                StemCellState.MATURE.name,
                StemCellState.SPECIALIZED.name,
            } or (
                hypothesis.lineage_parent_id == parent_id
                and parent_state == StemCellState.PROBATION.name
            )
            if not parent_usable or not _structural_pattern_matches(
                parent_id, states, active_signal_ids, next_visiting
            ):
                return False
        elif member not in active:
            return False
    return True


def _receipt_supports(
    state: ProspectiveAuthorityState, receipt: V2GroundedReceipt
) -> bool:
    return receipt.observed_outcome == (
        state.hypothesis.polarity is AvailabilityState.AVAILABLE
    )


def _authority_terminal(
    node: Node, env: Mapping[str, Any]
) -> tuple[bool, bool]:
    snapshot = env.get("authority_snapshot")
    states = env.get("authority_states")
    if (
        not isinstance(snapshot, AuthorityMeasurementSnapshot)
        or not isinstance(states, Mapping)
    ):
        return True, False
    role = str(node.meta["authority_role"])
    cell_id = str(node.meta["cell_id"])
    state = states.get(cell_id)
    if not isinstance(state, ProspectiveAuthorityState):
        return True, False
    matched = _structural_pattern_matches(
        cell_id, states, snapshot.trace.ordered_signal_identities
    )
    receipt = snapshot.grounded_receipt
    post_frontier = (
        receipt is not None
        and bool(receipt.receipt_id)
        and receipt.ordinal > state.hypothesis.birth_frontier
    )
    supports = bool(
        post_frontier and receipt is not None
        and _receipt_supports(state, receipt)
    )
    contradicts = bool(post_frontier and not supports)
    projected_support = state.support + int(post_frontier)
    projected_successes = state.successes + int(supports)
    projected_contradictions = state.contradictions + int(contradicts)
    projected_success_lower = wilson_lower_bound(
        projected_successes, projected_support, WILSON_Z
    )
    values = {
        "commitment": matched,
        "available": (
            matched and state.prospectively_certified
            and state.hypothesis.polarity is AvailabilityState.AVAILABLE
        ),
        "refuted": (
            matched and state.prospectively_certified
            and state.hypothesis.polarity is AvailabilityState.REFUTED
        ),
        "support": matched and supports,
        "contradiction": matched and contradicts,
        "maturity": (
            matched and supports and not state.prospectively_certified
            and projected_successes >= MIN_SUPPORT
            and projected_contradictions == 0
            and projected_success_lower >= LOWER_BOUND
        ),
        "revocation": (
            matched and contradicts and state.prospectively_certified
        ),
    }
    confirmed = bool(values[role])
    node.activation.value = 1.0 if confirmed else 0.0
    return True, confirmed


def _build_authority_graph(
    states: Mapping[str, ProspectiveAuthorityState],
) -> Graph:
    """Build the canonical organism-owned authority graph."""
    graph = Graph()
    for role in AUTHORITY_ROLES:
        graph.add_node(Node(
            ROLE_ROOTS[role], NodeType.SCRIPT,
            meta={"confirm_policy": "or", "authority_role": role},
        ))
        for cell_id in sorted(states):
            node_id = f"v2:{role}:{cell_id}"
            graph.add_node(Node(
                node_id, NodeType.TERMINAL, predicate=_authority_terminal,
                meta={
                    "terminal_kind": f"PROSPECTIVE_{role.upper()}",
                    "authority_role": role,
                    "cell_id": cell_id,
                    "frozen_hypothesis":
                        states[cell_id].hypothesis.manifest(),
                },
            ))
            graph.add_hierarchy_pair(ROLE_ROOTS[role], node_id)
    return graph
def _run_authority_graph(
    states: Mapping[str, ProspectiveAuthorityState],
    snapshot: AuthorityMeasurementSnapshot,
) -> dict[str, tuple[str, ...]]:
    if not states:
        return {role: () for role in AUTHORITY_ROLES}
    graph = _build_authority_graph(states)
    engine = FormalReConEngine(graph, record_trace=False)
    for role in AUTHORITY_ROLES:
        engine.request(ROLE_ROOTS[role])
    engine.run(
        max_ticks=max(32, len(states) * len(AUTHORITY_ROLES) * 4),
        env={"authority_snapshot": snapshot, "authority_states": states},
    )
    return {
        role: tuple(sorted(
            cell_id for cell_id in states
            if graph.nodes[f"v2:{role}:{cell_id}"].state
            == NodeState.CONFIRMED
        ))
        for role in AUTHORITY_ROLES
    }


def _interaction_manifest(
    *,
    source_organism_identity: str,
    source_state_identity: str,
    predecessor_fen: str,
    trace_manifest: Mapping[str, Any],
    actuation_manifest: Mapping[str, Any],
    successor_fen: str,
    outcome_terminal_identity: str,
) -> dict[str, Any]:
    return {
        "source_organism_identity": source_organism_identity,
        "source_state_identity": source_state_identity,
        "predecessor": predecessor_fen,
        "exact_trace": trace_manifest,
        "selected_actuation": actuation_manifest,
        "successor": successor_fen,
        "outcome_terminal_identity": outcome_terminal_identity,
    }


def _interaction_fingerprint(
    *,
    source_organism_identity: str,
    source_state_identity: str,
    predecessor_fen: str,
    trace: GraphSignalTrace,
    actuation: GraphActuation,
    successor_fen: str,
    outcome_terminal_identity: str,
) -> str:
    return _sha(_interaction_manifest(
        source_organism_identity=source_organism_identity,
        source_state_identity=source_state_identity,
        predecessor_fen=predecessor_fen,
        trace_manifest=trace.canonical_manifest(),
        actuation_manifest=asdict(actuation),
        successor_fen=successor_fen,
        outcome_terminal_identity=outcome_terminal_identity,
    ))


@dataclass
class NativeProspectiveAuthorityV2:
    base: TraceNativeCompetenceOrganism
    mode: V2Mode
    states: dict[str, ProspectiveAuthorityState]
    structural_invariants: dict[str, CellStructuralInvariant]
    authority_topology: dict[str, Any]
    historical_tombstones: dict[str, dict[str, Any]]
    next_expected_ordinal: int
    pending_event: PendingRealEvent | None = None
    consumed_receipts: dict[str, V2GroundedReceipt] = field(default_factory=dict)
    consumed_tokens: set[str] = field(default_factory=set)
    interaction_fingerprints: dict[str, str] = field(default_factory=dict)
    emissions: dict[str, V2CertificationEmission] = field(default_factory=dict)
    event_transactions: dict[str, dict[str, Any]] = field(default_factory=dict)
    nomination_events: tuple[dict[str, Any], ...] = ()
    schema_version: str = SCHEMA_VERSION
    _receipt_secret: bytes = field(
        default=b"native-prospective-v2-environment-terminal"
    )

    @classmethod
    def from_organism(
        cls,
        source: TraceNativeCompetenceOrganism,
        *,
        mode: V2Mode,
        frontier: int | None = None,
    ) -> "NativeProspectiveAuthorityV2":
        if frontier is not None:
            raise ProspectiveV2IntegrityError(
                "runner-supplied frontier is forbidden"
            )
        mode = V2Mode(mode)
        base = copy.deepcopy(source)
        ledger_ids = tuple(sorted(base.receipts))
        if not ledger_ids:
            raise ProspectiveProvenanceUnavailable(
                "prospective_provenance_unavailable: empty historical accepted ledger"
            )
        frontier_value = max(
            base.receipts[item].event_ordinal for item in ledger_ids
        )
        states: dict[str, ProspectiveAuthorityState] = {}
        tombstones: dict[str, dict[str, Any]] = {}
        historical_states = {
            StemCellState.MATURE,
            StemCellState.SPECIALIZED,
            StemCellState.PROBATION,
        }
        mature_states = {
            StemCellState.MATURE,
            StemCellState.SPECIALIZED,
        }
        for cell in sorted(
            base.envelope.cells.values(), key=lambda item: item.cell_id
        ):
            if cell.state == StemCellState.PRUNED:
                tombstones[cell.cell_id] = cell.to_manifest()
                continue
            if cell.state not in historical_states:
                raise ProspectiveProvenanceUnavailable(
                    "prospective_provenance_unavailable: live historical candidate "
                    f"{cell.cell_id} lacks prospective birth escrow"
                )
            if cell.polarity is None:
                raise ProspectiveV2IntegrityError(
                    "polarity=None on live historical hypothesis"
                )
            frozen = FrozenHypothesis(
                cell_id=cell.cell_id,
                members=tuple(cell.members),
                polarity=cell.polarity,
                lineage_parent_id=cell.lineage_parent_id,
                specialization_depth=cell.specialization_depth,
                discovery_receipt_ids=ledger_ids,
                discovery_receipt_digest=_sha(list(ledger_ids)),
                birth_frontier=frontier_value,
                structural_state=cell.state.name,
                provenance_kind=ProvenanceKind.HISTORICAL_ACCEPTED_LEDGER,
            )
            states[cell.cell_id] = ProspectiveAuthorityState(
                hypothesis=frozen,
                prospectively_certified=(
                    mode is V2Mode.LEGACY and cell.state in mature_states
                ),
            )
        topology = _authority_topology_manifest(states)
        invariants = {
            cell_id: cls._invariant_from_cell(base.envelope.cells[cell_id])
            for cell_id in states
        }
        item = cls(
            base=base,
            mode=mode,
            states=states,
            structural_invariants=invariants,
            authority_topology=topology,
            historical_tombstones=tombstones,
            next_expected_ordinal=base._next_event_ordinal,
        )
        item._verify_invariants()
        return item

    @staticmethod
    def _invariant_from_cell(
        cell: CompetenceContextCell,
    ) -> CellStructuralInvariant:
        if cell.polarity is None:
            raise ProspectiveV2IntegrityError(
                "polarity=None at live candidate birth is forbidden"
            )
        return CellStructuralInvariant(
            cell_id=cell.cell_id,
            members=tuple(cell.members),
            polarity=AvailabilityState(cell.polarity),
            lineage_parent_id=cell.lineage_parent_id,
            specialization_depth=cell.specialization_depth,
            structural_state=cell.state.name,
            authority_node_ids=_cell_node_ids(cell.cell_id),
            authority_topology_identity=_cell_topology_identity(cell.cell_id),
        )

    def _structural_manifest(self) -> dict[str, Any]:
        return {
            cell_id: invariant.manifest()
            for cell_id, invariant in sorted(self.structural_invariants.items())
        }

    def _structure_invariant_digest(self) -> str:
        return _sha({
            "live": self._structural_manifest(),
            "authority_topology": self.authority_topology,
            "tombstones": self.historical_tombstones,
        })

    def _verify_invariants(
        self, *, allow_unregistered: bool = False
    ) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ProspectiveV2IntegrityError("unsupported V2 schema")
        registered = set(self.states)
        if set(self.structural_invariants) != registered:
            raise ProspectiveV2IntegrityError(
                "live invariant/state identity mismatch"
            )
        for cell_id in sorted(registered):
            cell = self.base.envelope.cells.get(cell_id)
            if cell is None:
                raise ProspectiveV2IntegrityError(
                    "live competence cell disappeared"
                )
            current = self._invariant_from_cell(cell)
            if current != self.structural_invariants[cell_id]:
                raise ProspectiveV2IntegrityError(
                    f"live structural invariant mutation: {cell_id}"
                )
            hypothesis = self.states[cell_id].hypothesis
            if (
                hypothesis.members != current.members
                or hypothesis.polarity != current.polarity
                or hypothesis.lineage_parent_id != current.lineage_parent_id
                or hypothesis.specialization_depth
                != current.specialization_depth
                or hypothesis.structural_state != current.structural_state
            ):
                raise ProspectiveV2IntegrityError(
                    f"frozen hypothesis/invariant mismatch: {cell_id}"
                )
        current_tombstones = {
            cell_id: cell.to_manifest()
            for cell_id, cell in sorted(self.base.envelope.cells.items())
            if cell_id in self.historical_tombstones
        }
        if current_tombstones != self.historical_tombstones:
            raise ProspectiveV2IntegrityError(
                "historical tombstone mutation"
            )
        unknown = set(self.base.envelope.cells).difference(
            registered, self.historical_tombstones
        )
        if unknown and not allow_unregistered:
            raise ProspectiveV2IntegrityError(
                "unregistered live or tombstone candidate: "
                + ",".join(sorted(unknown))
            )
        if self.authority_topology != _authority_topology_manifest(self.states):
            raise ProspectiveV2IntegrityError(
                "authority topology identity mismatch"
            )

    def _graph_measure(
        self,
        trace: GraphSignalTrace,
        receipt: V2GroundedReceipt | None = None,
    ) -> dict[str, tuple[str, ...]]:
        return _run_authority_graph(
            self.states, AuthorityMeasurementSnapshot(trace, receipt)
        )

    @staticmethod
    def _classification_from_emissions(
        states: Mapping[str, ProspectiveAuthorityState],
        emissions: Mapping[str, tuple[str, ...]],
    ) -> EnvelopeClassification:
        available = tuple(emissions["available"])
        refuted = tuple(emissions["refuted"])
        if available and not refuted:
            state = AvailabilityState.AVAILABLE
            probability = max(
                states[item].success_lower_bound or 0.5
                for item in available
            )
        elif refuted and not available:
            state = AvailabilityState.REFUTED
            probability = 0.0
        else:
            state = AvailabilityState.UNKNOWN
            probability = 0.5
        return EnvelopeClassification(
            state=state,
            probability=float(probability),
            uncertainty=(
                1.0 if state is AvailabilityState.UNKNOWN
                else 1.0 - float(probability)
            ),
            available_cell_ids=available,
            refuted_cell_ids=refuted,
            formal_available=bool(available),
            formal_refuted=bool(refuted),
            policy_response=True,
        )

    def open_real_event(
        self, frame: FrameContext
    ) -> tuple[PendingRealEvent, GraphSignalTrace]:
        self._verify_invariants()
        before = self.continuation_digest()
        if frame.kind is not FrameKind.REAL:
            raise ProspectiveV2IntegrityError(
                "VIRTUAL cannot open certification event"
            )
        if self.pending_event is not None:
            raise ProspectiveV2IntegrityError(
                "exactly one pending event is permitted"
            )
        board = frame.values.get("board")
        if not isinstance(board, chess.Board):
            raise TypeError("REAL event requires chess.Board")
        actuation, trace = self.base.r0.emit_action_with_trace(frame)
        if actuation is None or trace is None:
            raise ProspectiveV2IntegrityError(
                "graph emitted no REAL actuation"
            )
        graph = self._graph_measure(trace)
        matching = graph["commitment"]
        classification = self._classification_from_emissions(
            self.states, graph
        )
        typed_digest = _sha([
            asdict(item) for item in trace.terminal_signals
        ])
        structure_digest = self._structure_invariant_digest()
        token = _sha({
            "implementation": IMPLEMENTATION_IDENTITY,
            "ordinal": self.next_expected_ordinal,
            "frame_id": frame.frame_id,
            "trace": trace.digest(),
            "matching": list(matching),
            "structure_invariant_digest": structure_digest,
        })
        pending = PendingRealEvent(
            ordinal=self.next_expected_ordinal,
            frame_id=frame.frame_id,
            trace_digest=trace.digest(),
            typed_signal_digest=typed_digest,
            source_organism_identity=trace.source_organism_identity,
            source_state_identity=trace.source_state_identity,
            predecessor_fen=board.fen(),
            actuation=actuation,
            pre_outcome_classification=classification,
            matching_cell_ids=matching,
            matching_cell_digest=_sha(list(matching)),
            structure_invariant_digest=structure_digest,
            pending_token=token,
            outcome_terminal_identity=OUTCOME_TERMINAL_IDENTITY,
        )
        if self.continuation_digest() != before:
            raise ProspectiveV2IntegrityError(
                "prediction mutated persistent state"
            )
        self.pending_event = pending
        self.event_transactions[token] = pending.manifest()
        return pending, trace

    def mint_environment_receipt(
        self,
        *,
        pending_token: str,
        trace: GraphSignalTrace,
        predecessor: chess.Board,
        successor: chess.Board,
        terminal_identity: str = OUTCOME_TERMINAL_IDENTITY,
    ) -> V2GroundedReceipt:
        pending = self.pending_event
        if pending is None or pending.pending_token != pending_token:
            raise ProspectiveV2IntegrityError("wrong pending token")
        if terminal_identity != pending.outcome_terminal_identity:
            raise ProspectiveV2IntegrityError("outcome terminal mismatch")
        if trace.frame_kind != FrameKind.REAL.name:
            raise ProspectiveV2IntegrityError(
                "VIRTUAL trace cannot mint REAL receipt"
            )
        fingerprint = _interaction_fingerprint(
            source_organism_identity=trace.source_organism_identity,
            source_state_identity=trace.source_state_identity,
            predecessor_fen=predecessor.fen(),
            trace=trace,
            actuation=trace.actuation,
            successor_fen=successor.fen(),
            outcome_terminal_identity=terminal_identity,
        )
        receipt_id = _sha({
            "fingerprint": fingerprint,
            "ordinal": pending.ordinal,
            "token": pending_token,
        })
        unsigned = {
            "receipt_id": receipt_id,
            "ordinal": pending.ordinal,
            "pending_token": pending_token,
            "frame_kind": FrameKind.REAL.name,
            "source_organism_identity": trace.source_organism_identity,
            "source_state_identity": trace.source_state_identity,
            "predecessor_fen": predecessor.fen(),
            "trace": trace.canonical_manifest(),
            "selected_actuation": asdict(trace.actuation),
            "successor_fen": successor.fen(),
            "outcome_terminal_identity": terminal_identity,
            "observed_outcome": successor.is_checkmate(),
            "interaction_fingerprint": fingerprint,
            "issuer_identity": EXPECTED_RECEIPT_ISSUER,
        }
        signature = hmac.new(
            self._receipt_secret, _json(unsigned), hashlib.sha256
        ).hexdigest()
        return V2GroundedReceipt(
            receipt_id=receipt_id,
            ordinal=pending.ordinal,
            pending_token=pending_token,
            frame_kind=FrameKind.REAL.name,
            source_organism_identity=trace.source_organism_identity,
            source_state_identity=trace.source_state_identity,
            predecessor_fen=predecessor.fen(),
            trace=trace,
            selected_actuation=trace.actuation,
            successor_fen=successor.fen(),
            outcome_terminal_identity=terminal_identity,
            observed_outcome=successor.is_checkmate(),
            interaction_fingerprint=fingerprint,
            issuer_identity=EXPECTED_RECEIPT_ISSUER,
            signature=signature,
        )

    def _validate_receipt(self, receipt: V2GroundedReceipt) -> None:
        if receipt.issuer_identity != EXPECTED_RECEIPT_ISSUER:
            raise ProspectiveV2IntegrityError(
                "unexpected receipt issuer"
            )
        expected_signature = hmac.new(
            self._receipt_secret,
            _json(receipt.unsigned_manifest()),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_signature, receipt.signature):
            raise ProspectiveV2IntegrityError(
                "receipt signature mismatch"
            )
        if (
            receipt.frame_kind != FrameKind.REAL.name
            or receipt.trace.frame_kind != FrameKind.REAL.name
        ):
            raise ProspectiveV2IntegrityError(
                "VIRTUAL-to-REAL receipt pairing"
            )
        pending = self.pending_event
        if pending is None:
            raise ProspectiveV2IntegrityError(
                "receipt before prediction"
            )
        if (
            receipt.ordinal != self.next_expected_ordinal
            or receipt.ordinal != pending.ordinal
        ):
            raise ProspectiveV2IntegrityError(
                "out-of-order ordinal or ordinal gap"
            )
        if (
            receipt.pending_token != pending.pending_token
            or receipt.pending_token in self.consumed_tokens
        ):
            raise ProspectiveV2IntegrityError(
                "wrong or consumed pending token"
            )
        if receipt.trace.digest() != pending.trace_digest:
            raise ProspectiveV2IntegrityError("trace mismatch")
        typed_digest = _sha([
            asdict(item) for item in receipt.trace.terminal_signals
        ])
        if typed_digest != pending.typed_signal_digest:
            raise ProspectiveV2IntegrityError(
                "typed-signal digest mismatch"
            )
        if receipt.selected_actuation != pending.actuation:
            raise ProspectiveV2IntegrityError("actuation mismatch")
        if receipt.trace.actuation != receipt.selected_actuation:
            raise ProspectiveV2IntegrityError(
                "trace/actuation mismatch"
            )
        if receipt.predecessor_fen != pending.predecessor_fen:
            raise ProspectiveV2IntegrityError("predecessor mismatch")
        if (
            receipt.source_organism_identity
            != pending.source_organism_identity
            or receipt.source_state_identity
            != pending.source_state_identity
        ):
            raise ProspectiveV2IntegrityError("source identity mismatch")
        if (
            receipt.outcome_terminal_identity
            != pending.outcome_terminal_identity
        ):
            raise ProspectiveV2IntegrityError(
                "outcome terminal mismatch"
            )
        board = chess.Board(receipt.predecessor_fen)
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(
            pending.actuation.move_uci
        ))
        if successor.fen() != receipt.successor_fen:
            raise ProspectiveV2IntegrityError("successor mismatch")
        if successor.is_checkmate() != receipt.observed_outcome:
            raise ProspectiveV2IntegrityError(
                "outcome terminal mismatch"
            )
        expected_fingerprint = _interaction_fingerprint(
            source_organism_identity=receipt.source_organism_identity,
            source_state_identity=receipt.source_state_identity,
            predecessor_fen=receipt.predecessor_fen,
            trace=receipt.trace,
            actuation=receipt.selected_actuation,
            successor_fen=receipt.successor_fen,
            outcome_terminal_identity=
                receipt.outcome_terminal_identity,
        )
        if expected_fingerprint != receipt.interaction_fingerprint:
            raise ProspectiveV2IntegrityError(
                "interaction fingerprint mismatch"
            )
        expected_receipt_id = _sha({
            "fingerprint": expected_fingerprint,
            "ordinal": receipt.ordinal,
            "token": receipt.pending_token,
        })
        if expected_receipt_id != receipt.receipt_id:
            raise ProspectiveV2IntegrityError("receipt ID mismatch")

    def consume(
        self, receipt: V2GroundedReceipt
    ) -> V2CertificationEmission:
        self._verify_invariants()
        if (
            self.pending_event is not None
            and self.pending_event.structure_invariant_digest
            != self._structure_invariant_digest()
        ):
            raise ProspectiveV2IntegrityError(
                "live structure changed between open and consume"
            )
        existing = self.consumed_receipts.get(receipt.receipt_id)
        if existing is not None:
            if existing != receipt:
                raise ProspectiveV2IntegrityError(
                    "receipt ID collision"
                )
            return self.emissions[receipt.receipt_id]
        known_id = self.interaction_fingerprints.get(
            receipt.interaction_fingerprint
        )
        if known_id is not None:
            raise ProspectiveV2IntegrityError(
                "reminted interaction fingerprint under new receipt identity"
            )
        self._validate_receipt(receipt)
        pending = self.pending_event
        assert pending is not None
        graph = self._graph_measure(receipt.trace, receipt)
        if graph["commitment"] != pending.matching_cell_ids:
            raise ProspectiveV2IntegrityError(
                "consumption commitment differs from pre-outcome commitment"
            )
        supporting = graph["support"]
        contradictions = graph["contradiction"]
        if set(supporting).intersection(contradictions):
            raise ProspectiveV2IntegrityError(
                "support/contradiction overlap"
            )
        if (
            set(supporting).union(contradictions)
            != set(pending.matching_cell_ids)
        ):
            raise ProspectiveV2IntegrityError(
                "lifecycle accounting omitted commitment"
            )
        for cell_id in pending.matching_cell_ids:
            state = self.states[cell_id]
            state.support += 1
            state.certification_receipt_ids = (
                *state.certification_receipt_ids,
                receipt.receipt_id,
            )
            if cell_id in supporting:
                state.successes += 1
                state.support_receipt_ids = (
                    *state.support_receipt_ids,
                    receipt.receipt_id,
                )
            else:
                state.contradictions += 1
                state.contradiction_receipt_ids = (
                    *state.contradiction_receipt_ids,
                    receipt.receipt_id,
                )
            state.success_lower_bound = wilson_lower_bound(
                state.successes, state.support, WILSON_Z
            )
            state.contradiction_lower_bound = wilson_lower_bound(
                state.contradictions, state.support, WILSON_Z
            )
            transition = None
            if cell_id in graph["maturity"]:
                state.prospectively_certified = True
                transition = "GRAPH_PROSPECTIVE_MATURITY"
            if cell_id in graph["revocation"]:
                state.prospectively_certified = False
                transition = "GRAPH_LOCAL_REVOCATION"
            if transition is not None:
                state.transition_rows = (
                    *state.transition_rows,
                    {
                        "transition": transition,
                        "receipt_id": receipt.receipt_id,
                        "ordinal": receipt.ordinal,
                        "pending_token": receipt.pending_token,
                    },
                )
        emission = V2CertificationEmission(
            receipt_id=receipt.receipt_id,
            matching_cell_ids=pending.matching_cell_ids,
            supporting_cell_ids=supporting,
            contradiction_cell_ids=contradictions,
            matured_cell_ids=graph["maturity"],
            revoked_cell_ids=graph["revocation"],
            graph_maturity_ids=graph["maturity"],
            graph_revocation_ids=graph["revocation"],
            nomination_allowed_after_lifecycle=True,
        )
        self.consumed_receipts[receipt.receipt_id] = receipt
        self.consumed_tokens.add(receipt.pending_token)
        self.interaction_fingerprints[
            receipt.interaction_fingerprint
        ] = receipt.receipt_id
        self.emissions[receipt.receipt_id] = emission
        self.next_expected_ordinal += 1
        self.event_transactions[receipt.pending_token] = {
            **pending.manifest(),
            "state": "CONSUMED",
            "consumed_receipt_id": receipt.receipt_id,
        }
        self.pending_event = None
        self._verify_invariants()
        return emission

    def _nomination_read_sets(
        self, cell: CompetenceContextCell
    ) -> tuple[tuple[str, tuple[str, ...]], ...]:
        raw = cell.stem_cell.metadata.get(
            "prospective_nomination_read_set"
        )
        if not isinstance(raw, Mapping):
            raise ProspectiveProvenanceUnavailable(
                "prospective_provenance_unavailable: growth interface did not "
                "expose exact nomination read set"
            )
        extra = set(map(str, raw)).difference(
            NOMINATION_READ_CATEGORIES
        )
        if extra:
            raise ProspectiveV2IntegrityError(
                "unknown nomination read categories: "
                + ",".join(sorted(extra))
            )
        categories = tuple(
            (
                name,
                tuple(sorted(set(map(str, raw.get(name, ()))))),
            )
            for name in NOMINATION_READ_CATEGORIES
        )
        if not categories[0][1]:
            raise ProspectiveProvenanceUnavailable(
                "prospective_provenance_unavailable: empty direct nomination reads"
            )
        if cell.lineage_parent_id is not None:
            required = {
                "parent_support",
                "eligibility",
                "contradiction_trigger",
            }
            missing = sorted(
                name for name, ids in categories
                if name in required and not ids
            )
            if missing:
                raise ProspectiveProvenanceUnavailable(
                    "prospective_provenance_unavailable: incomplete specialization "
                    + ",".join(missing)
                )
        all_ids = {
            receipt_id
            for _name, receipt_ids in categories
            for receipt_id in receipt_ids
        }
        unknown = sorted(all_ids.difference(self.base.receipts))
        if unknown:
            raise ProspectiveProvenanceUnavailable(
                "prospective_provenance_unavailable: "
                + ",".join(unknown)
            )
        return categories

    def sync_organism_nominations(self) -> tuple[str, ...]:
        """Attach exact birth escrow to cells born by the wrapped genome."""
        if self.pending_event is not None:
            raise ProspectiveV2IntegrityError(
                "candidate born during event before authority lifecycle completed"
            )
        self._verify_invariants(allow_unregistered=True)
        new_ids = tuple(sorted(
            set(self.base.envelope.cells).difference(
                self.states, self.historical_tombstones
            )
        ))
        additions: list[
            tuple[CompetenceContextCell, FrozenHypothesis]
        ] = []
        tombstone_additions: dict[str, dict[str, Any]] = {}
        for cell_id in new_ids:
            cell = self.base.envelope.cells[cell_id]
            if cell.state == StemCellState.PRUNED:
                tombstone_additions[cell_id] = cell.to_manifest()
                continue
            if cell.polarity is None:
                raise ProspectiveV2IntegrityError(
                    "polarity=None at live candidate birth is forbidden"
                )
            categories = self._nomination_read_sets(cell)
            discovery = tuple(sorted({
                receipt_id
                for _name, receipt_ids in categories
                for receipt_id in receipt_ids
            }))
            ordinals = [
                self.base.receipts[item].event_ordinal
                for item in discovery
            ]
            hypothesis = FrozenHypothesis(
                cell_id=cell.cell_id,
                members=tuple(cell.members),
                polarity=cell.polarity,
                lineage_parent_id=cell.lineage_parent_id,
                specialization_depth=cell.specialization_depth,
                discovery_receipt_ids=discovery,
                discovery_receipt_digest=_sha(list(discovery)),
                birth_frontier=max(ordinals),
                structural_state=cell.state.name,
                provenance_kind=
                    ProvenanceKind.EXACT_NOMINATION_READ_SET,
                nomination_read_sets=categories,
            )
            additions.append((cell, hypothesis))
        for cell, hypothesis in additions:
            self.states[cell.cell_id] = ProspectiveAuthorityState(
                hypothesis=hypothesis,
                prospectively_certified=False,
            )
            self.structural_invariants[
                cell.cell_id
            ] = self._invariant_from_cell(cell)
        self.historical_tombstones.update(tombstone_additions)
        self.authority_topology = _authority_topology_manifest(
            self.states
        )
        if additions or tombstone_additions:
            self.nomination_events = (
                *self.nomination_events,
                {
                    "event":
                        "GRAPH_OWNED_NOMINATION_INVARIANT_EXTENSION",
                    "cell_ids": [
                        cell.cell_id for cell, _hypothesis in additions
                    ],
                    "tombstone_ids": sorted(tombstone_additions),
                    "authority_topology_digest":
                        _sha(self.authority_topology),
                    "structure_invariant_digest":
                        self._structure_invariant_digest(),
                },
            )
        self._verify_invariants()
        return tuple(
            cell.cell_id for cell, _hypothesis in additions
        )

    def retrospective_certify(
        self, *_args: Any, **_kwargs: Any
    ) -> None:
        raise ProspectiveV2IntegrityError(
            "retrospective ledger scan cannot grant prospective authority"
        )

    def match_after_outcome(
        self, *_args: Any, **_kwargs: Any
    ) -> None:
        raise ProspectiveV2IntegrityError(
            "post-outcome matching is forbidden"
        )

    def consume_with_authority_outcome(
        self, *_args: Any, **_kwargs: Any
    ) -> None:
        raise ProspectiveV2IntegrityError(
            "authority-layer outcome relabeling is forbidden"
        )

    def nominate_suffix(
        self, *_args: Any, **_kwargs: Any
    ) -> None:
        raise ProspectiveV2IntegrityError(
            "suffix nomination is forbidden"
        )

    def assert_candidate_parity(
        self, other: "NativeProspectiveAuthorityV2"
    ) -> None:
        left = _sha({
            key: value.hypothesis.manifest()
            for key, value in sorted(self.states.items())
        })
        right = _sha({
            key: value.hypothesis.manifest()
            for key, value in sorted(other.states.items())
        })
        if left != right:
            raise ProspectiveV2IntegrityError(
                "candidate-manifest disparity"
            )

    def open_virtual(self, frame: FrameContext) -> dict[str, Any]:
        self._verify_invariants()
        before = self.continuation_digest()
        if frame.kind is not FrameKind.VIRTUAL:
            raise ProspectiveV2IntegrityError(
                "virtual capability requires VIRTUAL frame"
            )
        session = self.base.dream_session()
        result = session.request(frame)
        session.close()
        if self.continuation_digest() != before:
            raise ProspectiveV2IntegrityError(
                "VIRTUAL evaluation mutated state"
            )
        return {
            "query": result,
            "certification_commitment": None,
        }

    def continuation_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "mode": self.mode.value,
            "base_v3": self.base.continuation_manifest_v3(),
            "states": {
                key: value.manifest()
                for key, value in sorted(self.states.items())
            },
            "structural_invariants": self._structural_manifest(),
            "authority_topology":
                copy.deepcopy(self.authority_topology),
            "historical_tombstones": copy.deepcopy(
                dict(sorted(self.historical_tombstones.items()))
            ),
            "next_expected_ordinal": self.next_expected_ordinal,
            "pending_event": (
                None if self.pending_event is None
                else self.pending_event.manifest()
            ),
            "consumed_receipts": {
                key: value.manifest()
                for key, value in sorted(
                    self.consumed_receipts.items()
                )
            },
            "consumed_tokens": sorted(self.consumed_tokens),
            "interaction_fingerprints": dict(sorted(
                self.interaction_fingerprints.items()
            )),
            "emissions": {
                key: value.manifest()
                for key, value in sorted(self.emissions.items())
            },
            "event_transactions": copy.deepcopy(dict(sorted(
                self.event_transactions.items()
            ))),
            "nomination_events": list(self.nomination_events),
        }

    def continuation_digest(self) -> str:
        return _sha(self.continuation_manifest())

    def dumps(self) -> bytes:
        self._verify_invariants()
        return pickle.dumps(
            copy.deepcopy(self), protocol=pickle.HIGHEST_PROTOCOL
        )

    @classmethod
    def loads(
        cls, payload: bytes
    ) -> "NativeProspectiveAuthorityV2":
        item = pickle.loads(payload)
        if not isinstance(item, cls):
            raise TypeError("wrong V2 organism type")
        before = item.continuation_manifest()
        item.base._canonical_rebuild()
        item._verify_invariants()
        if item.continuation_manifest() != before:
            raise ProspectiveV2IntegrityError(
                "serialization restore changed state"
            )
        return item


@dataclass
class OutcomeBlindExposureScanner:
    """Read-only raw exposure manifest; no outcome qualification."""

    @staticmethod
    def scan(
        organism: NativeProspectiveAuthorityV2,
        probes: Sequence[ExposureProbe],
    ) -> dict[str, Any]:
        organism._verify_invariants()
        before = organism.continuation_digest()
        raw_by_id: dict[str, dict[str, Any]] = {}
        for probe in probes:
            if not isinstance(probe, ExposureProbe):
                raise TypeError(
                    "exposure scan requires ExposureProbe"
                )
            trace = probe.trace
            if trace.frame_kind != FrameKind.REAL.name:
                raise ProspectiveV2IntegrityError(
                    "exposure requires REAL trace"
                )
            if (
                trace.source_organism_identity
                != organism.base.r0.source_organism_identity()
                or trace.source_state_identity
                != organism.base.r0.trace_state_identity()
            ):
                raise ProspectiveV2IntegrityError(
                    "exposure source-organism identity mismatch"
                )
            board = chess.Board(probe.predecessor_fen)
            successor = board.copy(stack=False)
            successor.push(chess.Move.from_uci(
                trace.actuation.move_uci
            ))
            graph = organism._graph_measure(trace)
            fingerprint = _interaction_fingerprint(
                source_organism_identity=
                    trace.source_organism_identity,
                source_state_identity=
                    trace.source_state_identity,
                predecessor_fen=probe.predecessor_fen,
                trace=trace,
                actuation=trace.actuation,
                successor_fen=successor.fen(),
                outcome_terminal_identity=
                    probe.outcome_terminal_identity,
            )
            for cell_id in graph["commitment"]:
                state = organism.states[cell_id]
                if (
                    organism.next_expected_ordinal
                    <= state.hypothesis.birth_frontier
                ):
                    continue
                opportunity_id = _sha({
                    "interaction_fingerprint": fingerprint,
                    "matched_frozen_cell": cell_id,
                })
                raw_by_id[opportunity_id] = {
                    "opportunity_id": opportunity_id,
                    "cell_id": cell_id,
                    "interaction_fingerprint": fingerprint,
                    "source_organism_identity":
                        trace.source_organism_identity,
                    "source_state_identity":
                        trace.source_state_identity,
                    "predecessor_fen": probe.predecessor_fen,
                    "trace": trace.canonical_manifest(),
                    "selected_actuation": asdict(
                        trace.actuation
                    ),
                    "successor_fen": successor.fen(),
                    "outcome_terminal_identity":
                        probe.outcome_terminal_identity,
                }
        raw = sorted(
            raw_by_id.values(),
            key=lambda row: row["opportunity_id"],
        )
        per_cell: dict[str, list[str]] = {
            cell_id: [] for cell_id in organism.states
        }
        for row in raw:
            per_cell[row["cell_id"]].append(
                row["opportunity_id"]
            )
        result = {
            "schema_version": "native_v2_exposure_manifest.v2",
            "organism_identity":
                organism.base.r0.source_organism_identity(),
            "source_state_identity":
                organism.base.r0.trace_state_identity(),
            "raw_opportunities": raw,
            "raw_manifest_digest": _sha(raw),
            "cells": {
                cell_id: {
                    "distinct_opportunities":
                        len(opportunity_ids),
                    "opportunity_ids":
                        sorted(opportunity_ids),
                }
                for cell_id, opportunity_ids
                in sorted(per_cell.items())
            },
            "outcome_fields_read": 0,
        }
        if organism.continuation_digest() != before:
            raise ProspectiveV2IntegrityError(
                "exposure scan mutated organism"
            )
        return result

    @staticmethod
    def _validate_raw_scan(
        scan: Mapping[str, Any]
    ) -> bool:
        if "qualifies" in scan:
            raise ProspectiveV2IntegrityError(
                "caller-supplied exposure qualification is forbidden"
            )
        raw = scan.get("raw_opportunities")
        if not isinstance(raw, list):
            raise ProspectiveV2IntegrityError(
                "missing raw exposure manifest"
            )
        if _sha(raw) != scan.get("raw_manifest_digest"):
            raise ProspectiveV2IntegrityError(
                "raw exposure manifest digest mismatch"
            )
        organism_identity = str(
            scan.get("organism_identity", "")
        )
        source_state_identity = str(
            scan.get("source_state_identity", "")
        )
        if not organism_identity or not source_state_identity:
            raise ProspectiveV2IntegrityError(
                "missing exposure source identity"
            )
        seen: set[str] = set()
        per_cell: dict[str, set[str]] = {}
        for row in raw:
            if (
                row.get("source_organism_identity")
                != organism_identity
                or row.get("source_state_identity")
                != source_state_identity
            ):
                raise ProspectiveV2IntegrityError(
                    "mixed-organism raw exposure manifest"
                )
            trace = row.get("trace")
            actuation = row.get("selected_actuation")
            if (
                not isinstance(trace, Mapping)
                or not isinstance(actuation, Mapping)
            ):
                raise ProspectiveV2IntegrityError(
                    "malformed raw exposure row"
                )
            if trace.get("frame_kind") != FrameKind.REAL.name:
                raise ProspectiveV2IntegrityError(
                    "raw exposure contains VIRTUAL trace"
                )
            expected_fingerprint = _sha(_interaction_manifest(
                source_organism_identity=organism_identity,
                source_state_identity=source_state_identity,
                predecessor_fen=str(row["predecessor_fen"]),
                trace_manifest=trace,
                actuation_manifest=actuation,
                successor_fen=str(row["successor_fen"]),
                outcome_terminal_identity=str(
                    row["outcome_terminal_identity"]
                ),
            ))
            if (
                expected_fingerprint
                != row.get("interaction_fingerprint")
            ):
                raise ProspectiveV2IntegrityError(
                    "raw interaction fingerprint mismatch"
                )
            expected_opportunity = _sha({
                "interaction_fingerprint":
                    expected_fingerprint,
                "matched_frozen_cell": str(row["cell_id"]),
            })
            if expected_opportunity != row.get("opportunity_id"):
                raise ProspectiveV2IntegrityError(
                    "raw opportunity identity mismatch"
                )
            if expected_opportunity in seen:
                raise ProspectiveV2IntegrityError(
                    "duplicate raw opportunity was not collapsed"
                )
            seen.add(expected_opportunity)
            per_cell.setdefault(
                str(row["cell_id"]), set()
            ).add(expected_opportunity)
        supplied_cells = scan.get("cells")
        recomputed_cells = {
            cell_id: {
                "distinct_opportunities": len(ids),
                "opportunity_ids": sorted(ids),
            }
            for cell_id, ids in sorted(per_cell.items())
        }
        supplied_nonempty = {
            str(cell_id): value
            for cell_id, value in dict(
                supplied_cells or {}
            ).items()
            if int(value.get(
                "distinct_opportunities", 0
            )) > 0
        }
        if supplied_nonempty != recomputed_cells:
            raise ProspectiveV2IntegrityError(
                "cell exposure summary differs from raw opportunities"
            )
        return any(
            len(ids) >= MIN_SUPPORT
            for ids in per_cell.values()
        )

    @staticmethod
    def adjudicate_cohort(
        scans: Sequence[Mapping[str, Any]]
    ) -> dict[str, Any]:
        if len(scans) != 32:
            raise ProspectiveV2IntegrityError(
                "exposure admission requires exactly 32 organisms"
            )
        identities = [
            str(scan.get("organism_identity", ""))
            for scan in scans
        ]
        if len(set(identities)) != 32:
            raise ProspectiveV2IntegrityError(
                "exposure cohort requires 32 distinct organisms"
            )
        qualifications = [
            OutcomeBlindExposureScanner._validate_raw_scan(scan)
            for scan in scans
        ]
        qualifying = sum(qualifications)
        return {
            "organism_count": 32,
            "qualifying_organisms": qualifying,
            "required_qualifying_organisms": 24,
            "admitted": qualifying >= 24,
            "stop_reason": (
                None if qualifying >= 24
                else "prospective_evidence_starvation"
            ),
        }
