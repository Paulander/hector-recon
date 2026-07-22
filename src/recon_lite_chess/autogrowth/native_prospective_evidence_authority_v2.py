"""Graph-native prospective competence-evidence authority V2."""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field, replace
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
    NominationEscrow, wilson_lower_bound,
)
from .native_trace_competence_authority import TraceNativeCompetenceOrganism


SCHEMA_VERSION = "native_prospective_evidence_authority_v2.v2"
IMPLEMENTATION_IDENTITY = "native_prospective_two_phase_authority.v2"
EXPECTED_RECEIPT_ISSUER = "native_v2_environment_terminal"
OUTCOME_TERMINAL_IDENTITY = "native_r0_real_completion_terminal"
EXPOSURE_SCHEMA_VERSION = "native_v2_bound_exposure.v3"
_EXPOSURE_BINDING_SECRET = b"native-v2-bound-exposure-capability.v1"
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


class InitializationOrigin(str, Enum):
    HISTORICAL = "historical"
    PROSPECTIVE = "prospective"


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
    transitive_ancestor_receipt_ids: tuple[str, ...] = ()
    discovery_exclusion_receipt_ids: tuple[str, ...] = ()
    initialization_origin: InitializationOrigin = InitializationOrigin.PROSPECTIVE
    hypothesis_digest: str = ""

    def __post_init__(self) -> None:
        if self.polarity is None:
            raise ProspectiveV2IntegrityError(
                "polarity=None at live candidate birth is forbidden"
            )
        object.__setattr__(self, "polarity", AvailabilityState(self.polarity))
        object.__setattr__(
            self, "provenance_kind", ProvenanceKind(self.provenance_kind)
        )
        object.__setattr__(
            self,
            "initialization_origin",
            InitializationOrigin(self.initialization_origin),
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
        ancestors = tuple(sorted(set(self.transitive_ancestor_receipt_ids)))
        exclusion = tuple(sorted(set(self.discovery_exclusion_receipt_ids)))
        if ancestors != self.transitive_ancestor_receipt_ids:
            raise ProspectiveV2IntegrityError(
                "transitive ancestor provenance is not canonical"
            )
        if exclusion != self.discovery_exclusion_receipt_ids:
            raise ProspectiveV2IntegrityError(
                "discovery exclusion set is not canonical"
            )
        if self.provenance_kind is ProvenanceKind.HISTORICAL_ACCEPTED_LEDGER:
            if (
                categories
                or ancestors
                or self.initialization_origin is not InitializationOrigin.HISTORICAL
            ):
                raise ProspectiveV2IntegrityError(
                    "historical escrow cannot claim exact nomination reads"
                )
            if exclusion != canonical:
                raise ProspectiveV2IntegrityError(
                    "historical exclusion differs from accepted ledger"
                )
        else:
            if self.initialization_origin is not InitializationOrigin.PROSPECTIVE:
                raise ProspectiveV2IntegrityError(
                    "prospective escrow has historical origin"
                )
            if tuple(name for name, _ids in categories) != NOMINATION_READ_CATEGORIES:
                raise ProspectiveProvenanceUnavailable(
                    "prospective_provenance_unavailable: incomplete nomination read set"
                )
            union = tuple(sorted({
                receipt_id
                for _name, receipt_ids in categories
                for receipt_id in receipt_ids
            } | set(ancestors)))
            if union != canonical:
                raise ProspectiveV2IntegrityError(
                    "nomination read-set union differs from discovery ledger"
                )
            if not set(canonical).issubset(exclusion):
                raise ProspectiveV2IntegrityError(
                    "discovery reads missing from exclusion set"
                )
        expected_digest = _sha(self.identity_manifest())
        if self.hypothesis_digest and self.hypothesis_digest != expected_digest:
            raise ProspectiveV2IntegrityError("immutable hypothesis digest mismatch")
        object.__setattr__(self, "hypothesis_digest", expected_digest)

    def identity_manifest(self) -> dict[str, Any]:
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
            "transitive_ancestor_receipt_ids": list(
                self.transitive_ancestor_receipt_ids
            ),
            "discovery_exclusion_receipt_ids": list(
                self.discovery_exclusion_receipt_ids
            ),
            "initialization_origin": self.initialization_origin.value,
        }

    def manifest(self) -> dict[str, Any]:
        return {
            **self.identity_manifest(),
            "hypothesis_digest": self.hypothesis_digest,
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
class CanonicalExposureCommitment:
    schema_version: str
    source_organism_identity: str
    source_state_identity: str
    source_manifest_digest: str
    candidate_manifest_digest: str
    authority_topology_digest: str
    predecessor_fen: str
    trace: GraphSignalTrace
    selected_actuation: GraphActuation
    successor_fen: str
    matching_cell_ids: tuple[str, ...]
    matching_cell_digest: str
    outcome_terminal_identity: str
    interaction_fingerprint: str
    source_binding_identity: str
    binding_signature: str

    def unsigned_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_organism_identity": self.source_organism_identity,
            "source_state_identity": self.source_state_identity,
            "source_manifest_digest": self.source_manifest_digest,
            "candidate_manifest_digest": self.candidate_manifest_digest,
            "authority_topology_digest": self.authority_topology_digest,
            "predecessor_fen": self.predecessor_fen,
            "trace": self.trace.canonical_manifest(),
            "selected_actuation": asdict(self.selected_actuation),
            "successor_fen": self.successor_fen,
            "matching_cell_ids": list(self.matching_cell_ids),
            "matching_cell_digest": self.matching_cell_digest,
            "outcome_terminal_identity": self.outcome_terminal_identity,
            "interaction_fingerprint": self.interaction_fingerprint,
            "source_binding_identity": self.source_binding_identity,
        }

    def manifest(self) -> dict[str, Any]:
        return {
            **self.unsigned_manifest(),
            "binding_signature": self.binding_signature,
        }


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
            parent_usable = (
                parent_state == StemCellState.MATURE.name
            ) or (
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
        and receipt.receipt_id not in state.hypothesis.discovery_exclusion_receipt_ids
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
        epoch = base.open_prospective_discovery_epoch()
        base.validate_prospective_discovery_epoch()
        historical_ledger_ids = epoch.opened_receipt_ids
        if epoch.opened_cell_ids and not historical_ledger_ids:
            raise ProspectiveProvenanceUnavailable(
                "prospective_provenance_unavailable: empty historical accepted ledger"
            )
        states: dict[str, ProspectiveAuthorityState] = {}
        tombstones: dict[str, dict[str, Any]] = {}
        historical_states = {
            StemCellState.MATURE,
            StemCellState.SPECIALIZED,
            StemCellState.PROBATION,
        }
        opened_cells = set(epoch.opened_cell_ids)
        for cell in sorted(
            base.envelope.cells.values(), key=lambda item: item.cell_id
        ):
            historical = cell.cell_id in opened_cells
            if cell.state == StemCellState.PRUNED:
                if not historical and cell.nomination_escrow is None:
                    raise ProspectiveProvenanceUnavailable(
                        "post-epoch pruned cell lacks native nomination escrow"
                    )
                tombstones[cell.cell_id] = cell.to_manifest()
                continue
            if historical and cell.state not in historical_states:
                raise ProspectiveProvenanceUnavailable(
                    "prospective_provenance_unavailable: live historical candidate "
                    f"{cell.cell_id} lacks prospective birth escrow"
                )
            if cell.polarity is None:
                raise ProspectiveV2IntegrityError(
                    "polarity=None on live hypothesis"
                )
            if historical:
                frozen = FrozenHypothesis(
                    cell_id=cell.cell_id,
                    members=tuple(cell.members),
                    polarity=cell.polarity,
                    lineage_parent_id=cell.lineage_parent_id,
                    specialization_depth=cell.specialization_depth,
                    discovery_receipt_ids=historical_ledger_ids,
                    discovery_receipt_digest=_sha(list(historical_ledger_ids)),
                    birth_frontier=epoch.opening_frontier,
                    structural_state=cell.state.name,
                    provenance_kind=ProvenanceKind.HISTORICAL_ACCEPTED_LEDGER,
                    discovery_exclusion_receipt_ids=historical_ledger_ids,
                    initialization_origin=InitializationOrigin.HISTORICAL,
                )
            else:
                escrow = cell.nomination_escrow
                if not isinstance(escrow, NominationEscrow):
                    raise ProspectiveProvenanceUnavailable(
                        "post-epoch cell lacks native nomination escrow"
                    )
                if escrow.fixed_polarity is not cell.polarity:
                    raise ProspectiveV2IntegrityError(
                        "native escrow polarity differs from cell"
                    )
                known = set(base.receipts)
                mentioned = (
                    set(escrow.discovery_receipt_ids)
                    | set(escrow.discovery_exclusion_receipt_ids)
                )
                if not mentioned.issubset(known):
                    raise ProspectiveV2IntegrityError(
                        "native nomination escrow contains unknown receipt"
                    )
                frozen = FrozenHypothesis(
                    cell_id=cell.cell_id,
                    members=tuple(cell.members),
                    polarity=cell.polarity,
                    lineage_parent_id=cell.lineage_parent_id,
                    specialization_depth=cell.specialization_depth,
                    discovery_receipt_ids=escrow.discovery_receipt_ids,
                    discovery_receipt_digest=_sha(
                        list(escrow.discovery_receipt_ids)
                    ),
                    birth_frontier=escrow.birth_frontier,
                    structural_state=cell.state.name,
                    provenance_kind=ProvenanceKind.EXACT_NOMINATION_READ_SET,
                    nomination_read_sets=escrow.categorized_reads,
                    transitive_ancestor_receipt_ids=(
                        escrow.transitive_ancestor_receipt_ids
                    ),
                    discovery_exclusion_receipt_ids=(
                        escrow.discovery_exclusion_receipt_ids
                    ),
                    initialization_origin=InitializationOrigin.PROSPECTIVE,
                )
            states[cell.cell_id] = ProspectiveAuthorityState(
                hypothesis=frozen,
                prospectively_certified=(
                    mode is V2Mode.LEGACY and cell.is_mature
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
        self.base.validate_prospective_discovery_epoch()
        epoch = self.base.envelope.nomination_epoch
        assert epoch is not None
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
            if hypothesis.hypothesis_digest != _sha(hypothesis.identity_manifest()):
                raise ProspectiveV2IntegrityError(
                    f"immutable hypothesis digest mismatch: {cell_id}"
                )
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
            historical = cell_id in epoch.opened_cell_ids
            if historical != (
                hypothesis.initialization_origin
                is InitializationOrigin.HISTORICAL
            ):
                raise ProspectiveV2IntegrityError(
                    f"epoch/hypothesis origin mismatch: {cell_id}"
                )
            if not historical:
                escrow = cell.nomination_escrow
                if not isinstance(escrow, NominationEscrow):
                    raise ProspectiveV2IntegrityError(
                        f"post-epoch cell lacks escrow: {cell_id}"
                    )
                if (
                    hypothesis.nomination_read_sets != escrow.categorized_reads
                    or hypothesis.transitive_ancestor_receipt_ids
                    != escrow.transitive_ancestor_receipt_ids
                    or hypothesis.discovery_exclusion_receipt_ids
                    != escrow.discovery_exclusion_receipt_ids
                    or hypothesis.birth_frontier != escrow.birth_frontier
                    or hypothesis.polarity is not escrow.fixed_polarity
                ):
                    raise ProspectiveV2IntegrityError(
                        f"native escrow/hypothesis mismatch: {cell_id}"
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
        if unknown and epoch.nomination_closed:
            raise ProspectiveV2IntegrityError(
                "candidate born or synced after nomination closure"
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

        self._verify_ledger_derived_state()

    def _validate_replayed_receipt(
        self, receipt: V2GroundedReceipt, transaction: Mapping[str, Any]
    ) -> None:
        if receipt.issuer_identity != EXPECTED_RECEIPT_ISSUER:
            raise ProspectiveV2IntegrityError("unexpected receipt issuer")
        expected_signature = hmac.new(
            self._receipt_secret,
            _json(receipt.unsigned_manifest()),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_signature, receipt.signature):
            raise ProspectiveV2IntegrityError("receipt signature mismatch")
        if (
            receipt.frame_kind != FrameKind.REAL.name
            or receipt.trace.frame_kind != FrameKind.REAL.name
        ):
            raise ProspectiveV2IntegrityError("VIRTUAL-to-REAL receipt pairing")
        if (
            receipt.source_organism_identity
            != self.base.r0.source_organism_identity()
            or receipt.source_state_identity
            != self.base.r0.trace_state_identity()
        ):
            raise ProspectiveV2IntegrityError("source identity mismatch")
        if receipt.selected_actuation != receipt.trace.actuation:
            raise ProspectiveV2IntegrityError("trace/actuation mismatch")
        if receipt.outcome_terminal_identity != OUTCOME_TERMINAL_IDENTITY:
            raise ProspectiveV2IntegrityError("outcome terminal mismatch")
        board = chess.Board(receipt.predecessor_fen)
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(receipt.selected_actuation.move_uci))
        if successor.fen() != receipt.successor_fen:
            raise ProspectiveV2IntegrityError("successor mismatch")
        if successor.is_checkmate() != receipt.observed_outcome:
            raise ProspectiveV2IntegrityError("outcome terminal mismatch")
        fingerprint = _interaction_fingerprint(
            source_organism_identity=receipt.source_organism_identity,
            source_state_identity=receipt.source_state_identity,
            predecessor_fen=receipt.predecessor_fen,
            trace=receipt.trace,
            actuation=receipt.selected_actuation,
            successor_fen=receipt.successor_fen,
            outcome_terminal_identity=receipt.outcome_terminal_identity,
        )
        if fingerprint != receipt.interaction_fingerprint:
            raise ProspectiveV2IntegrityError("interaction fingerprint mismatch")
        receipt_id = _sha({
            "fingerprint": fingerprint,
            "ordinal": receipt.ordinal,
            "token": receipt.pending_token,
        })
        if receipt_id != receipt.receipt_id:
            raise ProspectiveV2IntegrityError("receipt ID mismatch")
        expected_transaction = {
            "ordinal": receipt.ordinal,
            "trace_digest": receipt.trace.digest(),
            "typed_signal_digest": _sha([
                asdict(item) for item in receipt.trace.terminal_signals
            ]),
            "source_organism_identity": receipt.source_organism_identity,
            "source_state_identity": receipt.source_state_identity,
            "predecessor_fen": receipt.predecessor_fen,
            "actuation": asdict(receipt.selected_actuation),
            "pending_token": receipt.pending_token,
            "outcome_terminal_identity": receipt.outcome_terminal_identity,
        }
        for key, value in expected_transaction.items():
            if transaction.get(key) != value:
                raise ProspectiveV2IntegrityError(
                    f"accepted ledger transaction mismatch: {key}"
                )
        if (
            transaction.get("state") != "CONSUMED"
            or transaction.get("consumed_receipt_id") != receipt.receipt_id
        ):
            raise ProspectiveV2IntegrityError(
                "accepted receipt lacks consumed pre-outcome transaction"
            )

    def _verify_ledger_derived_state(self) -> None:
        epoch = self.base.envelope.nomination_epoch
        if epoch is None:
            raise ProspectiveV2IntegrityError(
                "prospective discovery epoch is absent"
            )
        derived = {
            cell_id: ProspectiveAuthorityState(
                hypothesis=state.hypothesis,
                prospectively_certified=(
                    self.mode is V2Mode.LEGACY
                    and state.hypothesis.structural_state
                    == StemCellState.MATURE.name
                ),
            )
            for cell_id, state in self.states.items()
        }
        ordered = sorted(
            self.consumed_receipts.values(),
            key=lambda item: (item.ordinal, item.receipt_id),
        )
        expected_start = max(dict(epoch.receipt_ordinals).values(), default=-1) + 1
        expected_tokens: set[str] = set()
        expected_fingerprints: dict[str, str] = {}
        expected_emissions: dict[str, V2CertificationEmission] = {}
        for offset, receipt in enumerate(ordered):
            if receipt.ordinal != expected_start + offset:
                raise ProspectiveV2IntegrityError(
                    "accepted receipt ledger has ordinal gap"
                )
            if self.consumed_receipts.get(receipt.receipt_id) != receipt:
                raise ProspectiveV2IntegrityError(
                    "accepted receipt key differs from receipt identity"
                )
            if receipt.pending_token in expected_tokens:
                raise ProspectiveV2IntegrityError("duplicate consumed token")
            if receipt.interaction_fingerprint in expected_fingerprints:
                raise ProspectiveV2IntegrityError(
                    "duplicate accepted interaction fingerprint"
                )
            transaction = self.event_transactions.get(receipt.pending_token)
            if not isinstance(transaction, Mapping):
                raise ProspectiveV2IntegrityError(
                    "accepted receipt lacks pre-outcome transaction"
                )
            self._validate_replayed_receipt(receipt, transaction)
            pre_graph = _run_authority_graph(
                derived, AuthorityMeasurementSnapshot(receipt.trace, None)
            )
            matching = pre_graph["commitment"]
            if list(matching) != transaction.get("matching_cell_ids"):
                raise ProspectiveV2IntegrityError(
                    "replayed commitment differs from pre-outcome commitment"
                )
            if _sha(list(matching)) != transaction.get("matching_cell_digest"):
                raise ProspectiveV2IntegrityError(
                    "replayed commitment digest mismatch"
                )
            classification = self._classification_from_emissions(
                derived, pre_graph
            ).to_manifest()
            if classification != transaction.get("pre_outcome_classification"):
                raise ProspectiveV2IntegrityError(
                    "replayed pre-outcome classification mismatch"
                )
            if transaction.get("structure_invariant_digest") != (
                self._structure_invariant_digest()
            ):
                raise ProspectiveV2IntegrityError(
                    "replayed structure invariant mismatch"
                )
            graph = _run_authority_graph(
                derived, AuthorityMeasurementSnapshot(receipt.trace, receipt)
            )
            supporting = graph["support"]
            contradictions = graph["contradiction"]
            if set(supporting).union(contradictions) != set(matching):
                raise ProspectiveV2IntegrityError(
                    "replayed lifecycle omitted commitment"
                )
            for cell_id in matching:
                state = derived[cell_id]
                state.support += 1
                state.certification_receipt_ids = (
                    *state.certification_receipt_ids, receipt.receipt_id
                )
                if cell_id in supporting:
                    state.successes += 1
                    state.support_receipt_ids = (
                        *state.support_receipt_ids, receipt.receipt_id
                    )
                else:
                    state.contradictions += 1
                    state.contradiction_receipt_ids = (
                        *state.contradiction_receipt_ids, receipt.receipt_id
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
            expected_emissions[receipt.receipt_id] = V2CertificationEmission(
                receipt_id=receipt.receipt_id,
                matching_cell_ids=matching,
                supporting_cell_ids=supporting,
                contradiction_cell_ids=contradictions,
                matured_cell_ids=graph["maturity"],
                revoked_cell_ids=graph["revocation"],
                graph_maturity_ids=graph["maturity"],
                graph_revocation_ids=graph["revocation"],
                nomination_allowed_after_lifecycle=False,
            )
            expected_tokens.add(receipt.pending_token)
            expected_fingerprints[
                receipt.interaction_fingerprint
            ] = receipt.receipt_id
        if derived != self.states:
            raise ProspectiveV2IntegrityError(
                "mutable authority cache differs from grounded ledger replay"
            )
        if self.emissions != expected_emissions:
            raise ProspectiveV2IntegrityError(
                "persisted graph emission differs from grounded ledger replay"
            )
        if self.consumed_tokens != expected_tokens:
            raise ProspectiveV2IntegrityError("consumed-token ledger mismatch")
        if self.interaction_fingerprints != expected_fingerprints:
            raise ProspectiveV2IntegrityError(
                "interaction-fingerprint ledger mismatch"
            )
        expected_next = expected_start + len(ordered)
        if self.next_expected_ordinal != expected_next:
            raise ProspectiveV2IntegrityError("next ordinal differs from ledger")
        transaction_tokens = set(expected_tokens)
        if self.pending_event is not None:
            pending = self.pending_event
            if pending.ordinal != expected_next or pending.state != "OPEN":
                raise ProspectiveV2IntegrityError("invalid pending transaction")
            if self.event_transactions.get(pending.pending_token) != pending.manifest():
                raise ProspectiveV2IntegrityError(
                    "pending transaction manifest mismatch"
                )
            transaction_tokens.add(pending.pending_token)
        if set(self.event_transactions) != transaction_tokens:
            raise ProspectiveV2IntegrityError("event transaction ledger mismatch")


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
        epoch = self.base.envelope.nomination_epoch
        if epoch is None or not epoch.nomination_closed:
            raise ProspectiveV2IntegrityError(
                "first certification event requires closed nomination"
            )
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
            nomination_allowed_after_lifecycle=False,
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

    def _frozen_prospective_hypothesis(
        self, cell: CompetenceContextCell
    ) -> FrozenHypothesis:
        escrow = cell.nomination_escrow
        if not isinstance(escrow, NominationEscrow):
            raise ProspectiveProvenanceUnavailable(
                "post-epoch cell lacks native nomination escrow"
            )
        try:
            self.base.envelope._validate_escrow(escrow)
        except RuntimeError as exc:
            raise ProspectiveV2IntegrityError(str(exc)) from exc
        if cell.polarity is None or escrow.fixed_polarity is not cell.polarity:
            raise ProspectiveV2IntegrityError(
                "native nomination polarity differs from cell"
            )
        mentioned = (
            set(escrow.discovery_receipt_ids)
            | set(escrow.discovery_exclusion_receipt_ids)
        )
        if not mentioned.issubset(self.base.receipts):
            raise ProspectiveV2IntegrityError(
                "native nomination escrow contains unknown receipt"
            )
        ordinals = {
            key: value.event_ordinal
            for key, value in self.base.receipts.items()
        }
        if any(
            ordinals[item] > escrow.birth_frontier
            for item in mentioned
        ):
            raise ProspectiveV2IntegrityError(
                "native nomination escrow contains post-birth receipt"
            )
        outcomes = {
            key: value.observed_terminal_result
            for key, value in self.base.receipts.items()
        }
        categories = dict(escrow.categorized_reads)
        expected = escrow.fixed_polarity is AvailabilityState.AVAILABLE
        if escrow.operation == "ordinary":
            if outcomes[escrow.triggering_receipt_id] is not expected:
                raise ProspectiveV2IntegrityError(
                    "ordinary nomination polarity-inconsistent provenance"
                )
        else:
            if outcomes[escrow.triggering_receipt_id] is expected:
                raise ProspectiveV2IntegrityError(
                    "specialization contradiction polarity mismatch"
                )
            if any(outcomes[item] is not expected for item in categories["parent_support"]):
                raise ProspectiveV2IntegrityError(
                    "specialization parent support polarity mismatch"
                )
        context_ids = tuple(
            member.split(":", 1)[1]
            for member in cell.members
            if member.startswith("context:")
        )
        if escrow.operation == "specialization":
            if categories["eligibility"] != escrow.discovery_exclusion_receipt_ids:
                raise ProspectiveV2IntegrityError(
                    "specialization eligibility traversal is incomplete"
                )
            expected_parent_support = tuple(sorted(
                set(self.base.envelope._supporting_receipts(context_ids))
                & set(escrow.discovery_exclusion_receipt_ids)
            ))
            if categories["parent_support"] != expected_parent_support:
                raise ProspectiveV2IntegrityError(
                    "specialization parent support read set mismatch"
                )
            expected_direct = tuple(sorted(
                receipt_id
                for receipt_id in escrow.discovery_exclusion_receipt_ids
                if self.base.envelope._cell_pattern_matches(
                    cell, self.base.envelope.evidence[receipt_id], set()
                )
            ))
            if categories["direct"] != expected_direct:
                raise ProspectiveV2IntegrityError(
                    "specialization direct read set mismatch"
                )
        required_ancestors = (
            self.base.envelope._transitive_ancestor_provenance(context_ids)
        )
        if required_ancestors != escrow.transitive_ancestor_receipt_ids:
            raise ProspectiveV2IntegrityError(
                "nomination escrow omitted or added ancestor provenance"
            )
        return FrozenHypothesis(
            cell_id=cell.cell_id,
            members=tuple(cell.members),
            polarity=cell.polarity,
            lineage_parent_id=cell.lineage_parent_id,
            specialization_depth=cell.specialization_depth,
            discovery_receipt_ids=escrow.discovery_receipt_ids,
            discovery_receipt_digest=_sha(list(escrow.discovery_receipt_ids)),
            birth_frontier=escrow.birth_frontier,
            structural_state=cell.state.name,
            provenance_kind=ProvenanceKind.EXACT_NOMINATION_READ_SET,
            nomination_read_sets=escrow.categorized_reads,
            transitive_ancestor_receipt_ids=(
                escrow.transitive_ancestor_receipt_ids
            ),
            discovery_exclusion_receipt_ids=(
                escrow.discovery_exclusion_receipt_ids
            ),
            initialization_origin=InitializationOrigin.PROSPECTIVE,
        )
    def _sync_open_discovery_baseline(self) -> None:
        """Refresh only organism-derived state before nomination is frozen."""
        epoch = self.base.envelope.nomination_epoch
        if epoch is None or epoch.nomination_closed:
            return
        if self.pending_event is not None or self.consumed_receipts:
            raise ProspectiveV2IntegrityError(
                "discovery baseline cannot change after certification"
            )
        ledger_ids = tuple(sorted(dict(epoch.receipt_ordinals)))
        frontier = max(dict(epoch.receipt_ordinals).values(), default=-1)
        allowed = {
            (StemCellState.MATURE.name, StemCellState.MATURE.name),
            (StemCellState.MATURE.name, StemCellState.PROBATION.name),
            (StemCellState.PROBATION.name, StemCellState.PROBATION.name),
            (StemCellState.SPECIALIZED.name, StemCellState.SPECIALIZED.name),
        }
        for cell_id in sorted(set(epoch.opened_cell_ids) & set(self.states)):
            cell = self.base.envelope.cells[cell_id]
            current = self._invariant_from_cell(cell)
            prior = self.structural_invariants[cell_id]
            if replace(current, structural_state=prior.structural_state) != prior:
                raise ProspectiveV2IntegrityError(
                    f"non-lifecycle structural mutation during discovery: {cell_id}"
                )
            if (prior.structural_state, current.structural_state) not in allowed:
                raise ProspectiveV2IntegrityError(
                    f"invalid native lifecycle transition during discovery: {cell_id}"
                )
            previous = self.states[cell_id]
            hypothesis = FrozenHypothesis(
                cell_id=cell.cell_id,
                members=tuple(cell.members),
                polarity=cell.polarity,
                lineage_parent_id=cell.lineage_parent_id,
                specialization_depth=cell.specialization_depth,
                discovery_receipt_ids=ledger_ids,
                discovery_receipt_digest=_sha(list(ledger_ids)),
                birth_frontier=frontier,
                structural_state=current.structural_state,
                provenance_kind=ProvenanceKind.HISTORICAL_ACCEPTED_LEDGER,
                discovery_exclusion_receipt_ids=ledger_ids,
                initialization_origin=InitializationOrigin.HISTORICAL,
            )
            self.states[cell_id] = ProspectiveAuthorityState(
                hypothesis=hypothesis,
                prospectively_certified=(
                    self.mode is V2Mode.LEGACY and cell.is_mature
                ),
                certification_receipt_ids=previous.certification_receipt_ids,
                support_receipt_ids=previous.support_receipt_ids,
                contradiction_receipt_ids=previous.contradiction_receipt_ids,
                successes=previous.successes,
                contradictions=previous.contradictions,
                support=previous.support,
                success_lower_bound=previous.success_lower_bound,
                contradiction_lower_bound=previous.contradiction_lower_bound,
                transition_rows=previous.transition_rows,
            )
            self.structural_invariants[cell_id] = current
        for cell_id in sorted(
            set(epoch.opened_cell_ids) & set(self.historical_tombstones)
        ):
            self.historical_tombstones[cell_id] = (
                self.base.envelope.cells[cell_id].to_manifest()
            )



    def _sync_organism_nominations_in_place(self) -> tuple[str, ...]:
        """Register native escrows created atomically by the wrapped genome."""
        epoch = self.base.envelope.nomination_epoch
        if epoch is None:
            raise ProspectiveV2IntegrityError(
                "prospective discovery epoch is absent"
            )
        if epoch.nomination_closed:
            raise ProspectiveV2IntegrityError("nomination epoch is closed")
        if self.pending_event is not None or self.consumed_receipts:
            raise ProspectiveV2IntegrityError(
                "suffix nomination after certification is forbidden"
            )
        self._sync_open_discovery_baseline()
        self.next_expected_ordinal = max(
            dict(epoch.receipt_ordinals).values(), default=-1
        ) + 1
        self._verify_invariants(allow_unregistered=True)
        new_ids = tuple(sorted(
            set(self.base.envelope.cells).difference(
                self.states, self.historical_tombstones
            )
        ))
        if not set(new_ids).issubset(epoch.post_epoch_cell_ids):
            raise ProspectiveV2IntegrityError(
                "cell birth was not registered by organism epoch"
            )
        additions: list[tuple[CompetenceContextCell, FrozenHypothesis]] = []
        tombstone_additions: dict[str, dict[str, Any]] = {}
        for cell_id in new_ids:
            cell = self.base.envelope.cells[cell_id]
            if cell.nomination_escrow is None:
                raise ProspectiveProvenanceUnavailable(
                    "post-epoch cell lacks native nomination escrow"
                )
            if cell.state == StemCellState.PRUNED:
                self._frozen_prospective_hypothesis(cell)
                tombstone_additions[cell_id] = cell.to_manifest()
                continue
            additions.append((
                cell, self._frozen_prospective_hypothesis(cell)
            ))
        for cell, hypothesis in additions:
            self.states[cell.cell_id] = ProspectiveAuthorityState(
                hypothesis=hypothesis,
                prospectively_certified=(
                    self.mode is V2Mode.LEGACY and cell.is_mature
                ),
            )
            self.structural_invariants[cell.cell_id] = (
                self._invariant_from_cell(cell)
            )
        self.historical_tombstones.update(tombstone_additions)
        self.authority_topology = _authority_topology_manifest(self.states)
        if additions or tombstone_additions:
            self.nomination_events = (
                *self.nomination_events,
                {
                    "event": "NATIVE_ATOMIC_NOMINATION_SYNC",
                    "cell_ids": [
                        cell.cell_id for cell, _hypothesis in additions
                    ],
                    "tombstone_ids": sorted(tombstone_additions),
                    "epoch_id": epoch.epoch_id,
                    "authority_topology_digest": _sha(self.authority_topology),
                    "structure_invariant_digest": (
                        self._structure_invariant_digest()
                    ),
                },
            )
        self._verify_invariants()
        return tuple(cell.cell_id for cell, _hypothesis in additions)

    def sync_organism_nominations(self) -> tuple[str, ...]:
        """Atomically import native births into prospective authority."""
        candidate = copy.deepcopy(self)
        result = candidate._sync_organism_nominations_in_place()
        self.__dict__.clear()
        self.__dict__.update(candidate.__dict__)
        return result


    def nominate_prefix_from_grounded_receipts(
        self, receipts: Sequence[Any]
    ) -> tuple[str, ...]:
        candidate = copy.deepcopy(self)
        epoch = candidate.base.envelope.nomination_epoch
        if epoch is None or epoch.nomination_closed:
            raise ProspectiveV2IntegrityError("nomination epoch is closed")
        if candidate.pending_event is not None or candidate.consumed_receipts:
            raise ProspectiveV2IntegrityError(
                "suffix nomination after certification is forbidden"
            )
        candidate.base.grow_from_grounded_receipts(receipts)
        result = candidate._sync_organism_nominations_in_place()
        self.__dict__.clear()
        self.__dict__.update(candidate.__dict__)
        return result

    def close_nomination(self) -> tuple[tuple[str, str], ...]:
        candidate = copy.deepcopy(self)
        epoch = candidate.base.envelope.nomination_epoch
        if epoch is None:
            raise ProspectiveV2IntegrityError(
                "prospective discovery epoch is absent"
            )
        if epoch.nomination_closed:
            candidate._verify_invariants()
            return epoch.frozen_candidate_manifest
        candidate._sync_organism_nominations_in_place()
        manifest = candidate.base.close_prospective_nomination()
        epoch = candidate.base.envelope.nomination_epoch
        assert epoch is not None
        candidate.nomination_events = (
            *candidate.nomination_events,
            {
                "event": "NATIVE_NOMINATION_CLOSED",
                "epoch_id": epoch.epoch_id,
                "candidate_manifest_digest": (
                    epoch.frozen_candidate_manifest_digest
                ),
                "candidate_count": len(manifest),
            },
        )
        candidate._verify_invariants()
        self.__dict__.clear()
        self.__dict__.update(candidate.__dict__)
        return manifest

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

    def _candidate_manifest_digest(self) -> str:
        epoch = self.base.envelope.nomination_epoch
        if epoch is None or not epoch.nomination_closed:
            raise ProspectiveV2IntegrityError(
                "exposure requires frozen nomination"
            )
        return _sha({
            "hypotheses": {
                key: value.hypothesis.manifest()
                for key, value in sorted(self.states.items())
            },
            "tombstones": self.historical_tombstones,
            "epoch_candidate_manifest_digest": (
                epoch.frozen_candidate_manifest_digest
            ),
        })

    def probe_real_exposure(
        self, frame: FrameContext
    ) -> CanonicalExposureCommitment:
        self._verify_invariants()
        epoch = self.base.envelope.nomination_epoch
        if epoch is None or not epoch.nomination_closed:
            raise ProspectiveV2IntegrityError(
                "exposure requires frozen nomination"
            )
        if frame.kind is not FrameKind.REAL:
            raise ProspectiveV2IntegrityError(
                "exposure requires REAL frame"
            )
        board = frame.values.get("board")
        if not isinstance(board, chess.Board):
            raise TypeError("REAL exposure requires chess.Board")
        before = self.continuation_digest()
        actuation, trace = self.base.r0.emit_action_with_trace(frame)
        if actuation is None or trace is None:
            raise ProspectiveV2IntegrityError(
                "graph emitted no REAL exposure actuation"
            )
        if trace.actuation != actuation:
            raise ProspectiveV2IntegrityError(
                "exposure trace/action mismatch"
            )
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(actuation.move_uci))
        matching = self._graph_measure(trace)["commitment"]
        source_manifest_digest = _sha({
            "source_manifest": self.base.r0.source_manifest,
            "persistent_state": self.base.r0.persistent_state_audit(),
        })
        candidate_manifest_digest = self._candidate_manifest_digest()
        topology_digest = _sha(self.authority_topology)
        fingerprint = _interaction_fingerprint(
            source_organism_identity=trace.source_organism_identity,
            source_state_identity=trace.source_state_identity,
            predecessor_fen=board.fen(),
            trace=trace,
            actuation=actuation,
            successor_fen=successor.fen(),
            outcome_terminal_identity=OUTCOME_TERMINAL_IDENTITY,
        )
        source_binding_identity = _sha({
            "source_organism_identity": trace.source_organism_identity,
            "source_state_identity": trace.source_state_identity,
            "source_manifest_digest": source_manifest_digest,
            "candidate_manifest_digest": candidate_manifest_digest,
            "authority_topology_digest": topology_digest,
        })
        unsigned = CanonicalExposureCommitment(
            schema_version=EXPOSURE_SCHEMA_VERSION,
            source_organism_identity=trace.source_organism_identity,
            source_state_identity=trace.source_state_identity,
            source_manifest_digest=source_manifest_digest,
            candidate_manifest_digest=candidate_manifest_digest,
            authority_topology_digest=topology_digest,
            predecessor_fen=board.fen(),
            trace=trace,
            selected_actuation=actuation,
            successor_fen=successor.fen(),
            matching_cell_ids=matching,
            matching_cell_digest=_sha(list(matching)),
            outcome_terminal_identity=OUTCOME_TERMINAL_IDENTITY,
            interaction_fingerprint=fingerprint,
            source_binding_identity=source_binding_identity,
            binding_signature="",
        )
        signature = hmac.new(
            _EXPOSURE_BINDING_SECRET,
            _json(unsigned.unsigned_manifest()),
            hashlib.sha256,
        ).hexdigest()
        result = CanonicalExposureCommitment(
            **{
                **unsigned.__dict__,
                "binding_signature": signature,
            }
        )
        if self.continuation_digest() != before:
            raise ProspectiveV2IntegrityError(
                "exposure probe mutated organism"
            )
        return result


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
    """Read-only scanner for organism-issued, outcome-free commitments."""

    TOP_LEVEL_KEYS = frozenset({
        "schema_version", "source_binding_identity",
        "source_organism_identity", "source_state_identity",
        "source_manifest_digest", "candidate_manifest_digest",
        "authority_topology_digest", "candidate_cell_ids",
        "raw_opportunities", "raw_manifest_digest", "cells",
        "outcome_fields_read", "source_binding_signature",
    })
    COMMITMENT_KEYS = frozenset({
        "schema_version", "source_organism_identity",
        "source_state_identity", "source_manifest_digest",
        "candidate_manifest_digest", "authority_topology_digest",
        "predecessor_fen", "trace", "selected_actuation",
        "successor_fen", "matching_cell_ids", "matching_cell_digest",
        "outcome_terminal_identity", "interaction_fingerprint",
        "source_binding_identity", "binding_signature",
    })
    ROW_KEYS = COMMITMENT_KEYS | {"cell_id", "opportunity_id"}

    @staticmethod
    def _binding_signature(unsigned: Mapping[str, Any]) -> str:
        return hmac.new(
            _EXPOSURE_BINDING_SECRET,
            _json(unsigned),
            hashlib.sha256,
        ).hexdigest()

    @classmethod
    def _validate_commitment(
        cls,
        organism: NativeProspectiveAuthorityV2,
        commitment: CanonicalExposureCommitment,
    ) -> None:
        if not isinstance(commitment, CanonicalExposureCommitment):
            raise TypeError(
                "exposure scan requires graph-produced commitment"
            )
        if commitment.schema_version != EXPOSURE_SCHEMA_VERSION:
            raise ProspectiveV2IntegrityError(
                "noncanonical exposure schema"
            )
        if commitment.outcome_terminal_identity != OUTCOME_TERMINAL_IDENTITY:
            raise ProspectiveV2IntegrityError(
                "noncanonical exposure terminal"
            )
        unsigned = commitment.unsigned_manifest()
        if not hmac.compare_digest(
            cls._binding_signature(unsigned),
            commitment.binding_signature,
        ):
            raise ProspectiveV2IntegrityError(
                "exposure source binding signature mismatch"
            )
        trace = commitment.trace
        if trace.frame_kind != FrameKind.REAL.name:
            raise ProspectiveV2IntegrityError(
                "exposure requires REAL trace"
            )
        if commitment.selected_actuation != trace.actuation:
            raise ProspectiveV2IntegrityError(
                "exposure trace/action mismatch"
            )
        if (
            commitment.source_organism_identity
            != organism.base.r0.source_organism_identity()
            or commitment.source_state_identity
            != organism.base.r0.trace_state_identity()
            or trace.source_organism_identity
            != commitment.source_organism_identity
            or trace.source_state_identity
            != commitment.source_state_identity
        ):
            raise ProspectiveV2IntegrityError(
                "exposure source-organism identity mismatch"
            )
        source_manifest_digest = _sha({
            "source_manifest": organism.base.r0.source_manifest,
            "persistent_state": organism.base.r0.persistent_state_audit(),
        })
        if commitment.source_manifest_digest != source_manifest_digest:
            raise ProspectiveV2IntegrityError(
                "exposure source manifest mismatch"
            )
        if (
            commitment.candidate_manifest_digest
            != organism._candidate_manifest_digest()
            or commitment.authority_topology_digest
            != _sha(organism.authority_topology)
        ):
            raise ProspectiveV2IntegrityError(
                "exposure candidate or topology mismatch"
            )
        board = chess.Board(commitment.predecessor_fen)
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(
            commitment.selected_actuation.move_uci
        ))
        if successor.fen() != commitment.successor_fen:
            raise ProspectiveV2IntegrityError(
                "exposure successor mismatch"
            )
        matching = organism._graph_measure(trace)["commitment"]
        if (
            matching != commitment.matching_cell_ids
            or _sha(list(matching)) != commitment.matching_cell_digest
        ):
            raise ProspectiveV2IntegrityError(
                "exposure graph commitment mismatch"
            )
        fingerprint = _interaction_fingerprint(
            source_organism_identity=commitment.source_organism_identity,
            source_state_identity=commitment.source_state_identity,
            predecessor_fen=commitment.predecessor_fen,
            trace=trace,
            actuation=commitment.selected_actuation,
            successor_fen=commitment.successor_fen,
            outcome_terminal_identity=OUTCOME_TERMINAL_IDENTITY,
        )
        if fingerprint != commitment.interaction_fingerprint:
            raise ProspectiveV2IntegrityError(
                "exposure interaction fingerprint mismatch"
            )
        binding = _sha({
            "source_organism_identity": commitment.source_organism_identity,
            "source_state_identity": commitment.source_state_identity,
            "source_manifest_digest": commitment.source_manifest_digest,
            "candidate_manifest_digest": (
                commitment.candidate_manifest_digest
            ),
            "authority_topology_digest": (
                commitment.authority_topology_digest
            ),
        })
        if binding != commitment.source_binding_identity:
            raise ProspectiveV2IntegrityError(
                "exposure source binding identity mismatch"
            )

    @classmethod
    def scan(
        cls,
        organism: NativeProspectiveAuthorityV2,
        commitments: Sequence[CanonicalExposureCommitment],
    ) -> dict[str, Any]:
        organism._verify_invariants()
        before = organism.continuation_digest()
        raw_by_id: dict[str, dict[str, Any]] = {}
        for commitment in commitments:
            cls._validate_commitment(organism, commitment)
            for cell_id in commitment.matching_cell_ids:
                state = organism.states.get(cell_id)
                if state is None:
                    raise ProspectiveV2IntegrityError(
                        "exposure names unknown frozen candidate"
                    )
                if organism.next_expected_ordinal <= state.hypothesis.birth_frontier:
                    continue
                opportunity_id = _sha({
                    "interaction_fingerprint": (
                        commitment.interaction_fingerprint
                    ),
                    "matched_frozen_cell": cell_id,
                })
                raw_by_id[opportunity_id] = {
                    **commitment.manifest(),
                    "cell_id": cell_id,
                    "opportunity_id": opportunity_id,
                }
        raw = sorted(
            raw_by_id.values(), key=lambda row: row["opportunity_id"]
        )
        cells = {cell_id: [] for cell_id in organism.states}
        for row in raw:
            cells[row["cell_id"]].append(row["opportunity_id"])
        source = commitments[0] if commitments else None
        if source is None:
            source_binding_identity = _sha({
                "source_organism_identity": (
                    organism.base.r0.source_organism_identity()
                ),
                "source_state_identity": organism.base.r0.trace_state_identity(),
                "source_manifest_digest": _sha({
                    "source_manifest": organism.base.r0.source_manifest,
                    "persistent_state": organism.base.r0.persistent_state_audit(),
                }),
                "candidate_manifest_digest": organism._candidate_manifest_digest(),
                "authority_topology_digest": _sha(organism.authority_topology),
            })
            source_manifest_digest = _sha({
                "source_manifest": organism.base.r0.source_manifest,
                "persistent_state": organism.base.r0.persistent_state_audit(),
            })
        else:
            source_binding_identity = source.source_binding_identity
            source_manifest_digest = source.source_manifest_digest
        body = {
            "schema_version": EXPOSURE_SCHEMA_VERSION,
            "source_binding_identity": source_binding_identity,
            "source_organism_identity": (
                organism.base.r0.source_organism_identity()
            ),
            "source_state_identity": organism.base.r0.trace_state_identity(),
            "source_manifest_digest": source_manifest_digest,
            "candidate_manifest_digest": organism._candidate_manifest_digest(),
            "authority_topology_digest": _sha(organism.authority_topology),
            "candidate_cell_ids": sorted(organism.states),
            "raw_opportunities": raw,
            "raw_manifest_digest": _sha(raw),
            "cells": {
                cell_id: {
                    "distinct_opportunities": len(ids),
                    "opportunity_ids": sorted(ids),
                }
                for cell_id, ids in sorted(cells.items())
            },
            "outcome_fields_read": 0,
        }
        result = {
            **body,
            "source_binding_signature": cls._binding_signature(body),
        }
        if organism.continuation_digest() != before:
            raise ProspectiveV2IntegrityError(
                "exposure scan mutated organism"
            )
        return result

    @classmethod
    def _validate_raw_scan(cls, scan: Mapping[str, Any]) -> bool:
        if set(scan) != cls.TOP_LEVEL_KEYS:
            raise ProspectiveV2IntegrityError(
                "noncanonical or outcome-bearing exposure fields"
            )
        if scan.get("schema_version") != EXPOSURE_SCHEMA_VERSION:
            raise ProspectiveV2IntegrityError(
                "noncanonical exposure schema"
            )
        if scan.get("outcome_fields_read") != 0:
            raise ProspectiveV2IntegrityError(
                "outcome-bearing exposure input"
            )
        body = {
            key: scan[key]
            for key in cls.TOP_LEVEL_KEYS
            if key != "source_binding_signature"
        }
        if not hmac.compare_digest(
            cls._binding_signature(body),
            str(scan["source_binding_signature"]),
        ):
            raise ProspectiveV2IntegrityError(
                "raw scan source binding signature mismatch"
            )
        raw = scan["raw_opportunities"]
        if not isinstance(raw, list) or _sha(raw) != scan["raw_manifest_digest"]:
            raise ProspectiveV2IntegrityError(
                "raw exposure manifest digest mismatch"
            )
        binding = _sha({
            "source_organism_identity": scan["source_organism_identity"],
            "source_state_identity": scan["source_state_identity"],
            "source_manifest_digest": scan["source_manifest_digest"],
            "candidate_manifest_digest": scan["candidate_manifest_digest"],
            "authority_topology_digest": scan["authority_topology_digest"],
        })
        if binding != scan["source_binding_identity"]:
            raise ProspectiveV2IntegrityError(
                "raw scan source binding identity mismatch"
            )
        candidate_ids = tuple(scan["candidate_cell_ids"])
        if tuple(sorted(set(candidate_ids))) != candidate_ids:
            raise ProspectiveV2IntegrityError(
                "noncanonical candidate identity manifest"
            )
        seen: set[str] = set()
        per_cell = {cell_id: set() for cell_id in candidate_ids}
        for row in raw:
            if not isinstance(row, Mapping) or set(row) != cls.ROW_KEYS:
                raise ProspectiveV2IntegrityError(
                    "noncanonical or outcome-bearing exposure row"
                )
            if (
                row["schema_version"] != EXPOSURE_SCHEMA_VERSION
                or row["outcome_terminal_identity"]
                != OUTCOME_TERMINAL_IDENTITY
                or row["source_binding_identity"]
                != scan["source_binding_identity"]
            ):
                raise ProspectiveV2IntegrityError(
                    "raw exposure authority binding mismatch"
                )
            for key in (
                "source_organism_identity", "source_state_identity",
                "source_manifest_digest", "candidate_manifest_digest",
                "authority_topology_digest",
            ):
                if row[key] != scan[key]:
                    raise ProspectiveV2IntegrityError(
                        "mixed-organism raw exposure manifest"
                    )
            unsigned = {
                key: row[key]
                for key in cls.COMMITMENT_KEYS
                if key != "binding_signature"
            }
            if not hmac.compare_digest(
                cls._binding_signature(unsigned),
                str(row["binding_signature"]),
            ):
                raise ProspectiveV2IntegrityError(
                    "raw commitment binding signature mismatch"
                )
            trace = row["trace"]
            actuation = row["selected_actuation"]
            if (
                not isinstance(trace, Mapping)
                or not isinstance(actuation, Mapping)
                or trace.get("frame_kind") != FrameKind.REAL.name
                or trace.get("actuation") != actuation
            ):
                raise ProspectiveV2IntegrityError(
                    "raw exposure trace/action mismatch"
                )
            if (
                trace.get("source_organism_identity")
                != scan["source_organism_identity"]
                or trace.get("source_state_identity")
                != scan["source_state_identity"]
            ):
                raise ProspectiveV2IntegrityError(
                    "raw exposure trace source mismatch"
                )
            board = chess.Board(str(row["predecessor_fen"]))
            successor = board.copy(stack=False)
            successor.push(chess.Move.from_uci(str(actuation["move_uci"])))
            if successor.fen() != row["successor_fen"]:
                raise ProspectiveV2IntegrityError(
                    "raw exposure successor mismatch"
                )
            matching = tuple(row["matching_cell_ids"])
            if (
                tuple(sorted(set(matching))) != matching
                or _sha(list(matching)) != row["matching_cell_digest"]
                or row["cell_id"] not in matching
                or row["cell_id"] not in per_cell
            ):
                raise ProspectiveV2IntegrityError(
                    "raw exposure candidate commitment mismatch"
                )
            fingerprint = _sha(_interaction_manifest(
                source_organism_identity=str(
                    scan["source_organism_identity"]
                ),
                source_state_identity=str(scan["source_state_identity"]),
                predecessor_fen=str(row["predecessor_fen"]),
                trace_manifest=trace,
                actuation_manifest=actuation,
                successor_fen=str(row["successor_fen"]),
                outcome_terminal_identity=OUTCOME_TERMINAL_IDENTITY,
            ))
            if fingerprint != row["interaction_fingerprint"]:
                raise ProspectiveV2IntegrityError(
                    "raw interaction fingerprint mismatch"
                )
            opportunity = _sha({
                "interaction_fingerprint": fingerprint,
                "matched_frozen_cell": row["cell_id"],
            })
            if opportunity != row["opportunity_id"] or opportunity in seen:
                raise ProspectiveV2IntegrityError(
                    "duplicate or altered raw opportunity"
                )
            seen.add(opportunity)
            per_cell[row["cell_id"]].add(opportunity)
        expected_cells = {
            cell_id: {
                "distinct_opportunities": len(ids),
                "opportunity_ids": sorted(ids),
            }
            for cell_id, ids in sorted(per_cell.items())
        }
        if scan["cells"] != expected_cells:
            raise ProspectiveV2IntegrityError(
                "cell exposure summary differs from raw opportunities"
            )
        return any(len(ids) >= MIN_SUPPORT for ids in per_cell.values())

    @classmethod
    def adjudicate_cohort(
        cls, scans: Sequence[Mapping[str, Any]]
    ) -> dict[str, Any]:
        if len(scans) != 32:
            raise ProspectiveV2IntegrityError(
                "exposure admission requires exactly 32 organisms"
            )
        qualifications = [cls._validate_raw_scan(scan) for scan in scans]
        identities = [
            str(scan["source_binding_identity"]) for scan in scans
        ]
        if len(set(identities)) != 32:
            raise ProspectiveV2IntegrityError(
                "exposure cohort requires 32 distinct bound organisms"
            )
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
