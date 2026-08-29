"""Graph-native prospective competence-evidence authority V2."""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field, replace
from enum import Enum
import hashlib
import hmac
import json
import pickle
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import chess

from recon_lite import (
    ChildResponse, FormalReConEngine, FrameContext, FrameKind, Graph, Node,
    NodeState, NodeType,
)
from recon_lite_hector.nodes import StemCellState
from recon_lite_hector.nodes import StemCellTerminal

from .native_authority_handover import (
    ChildQuery,
    GraphActuation,
    GraphSignalTrace,
    NativeR0DreamSession,
)
from .native_competence_envelope import (
    AvailabilityState, CompetenceContextCell, CompetenceContextGrowthGenome,
    DormantOrigin, EnvelopeClassification, GrowthProposal,
    NOMINATION_READ_CATEGORIES_V1, NOMINATION_READ_CATEGORIES_V2,
    NOMINATION_READ_CATEGORIES_V3, NOMINATION_ESCROW_V3,
    NominationEscrow, SpecializationMode, StructuralMatchDescriptor,
    _GraphSpecializationRequest, canonical_structural_pattern_matches,
    wilson_lower_bound,
)
from .native_trace_competence_authority import TraceNativeCompetenceOrganism


SCHEMA_VERSION = (
    "native_prospective_evidence_authority_v2."
    "v7_mixed_evidence_specialization"
)
IMPLEMENTATION_IDENTITY = (
    "native_prospective_two_phase_authority."
    "v7_mixed_evidence_specialization"
)
EXPECTED_RECEIPT_ISSUER = "native_v2_environment_terminal"
OUTCOME_TERMINAL_IDENTITY = "native_r0_real_completion_terminal"
EXPOSURE_SCHEMA_VERSION = "native_v2_bound_exposure.v5"
PHYSICAL_TRACE_PROJECTION_SCHEMA = "native_v2_physical_trace_projection.v1"
_EXPOSURE_BINDING_SECRET = b"native-v2-bound-exposure-capability.v1"
CELL_AUTHORITY_ROLES = (
    "commitment", "available", "refuted", "support", "contradiction",
    "maturity", "revocation", "specialization_request",
)
AUTHORITY_ROLES = (*CELL_AUTHORITY_ROLES, "specialization_eligibility")
ROLE_ROOTS = {role: f"v2_authority_{role}_root" for role in AUTHORITY_ROLES}
NOMINATION_READ_CATEGORIES = NOMINATION_READ_CATEGORIES_V1
WILSON_Z = 1.6448536269514722
MIN_SUPPORT = 4
LOWER_BOUND = 0.55
VIRTUAL_AVAILABLE_VALUE = 1.0
VIRTUAL_RESPONSE_UNCERTAINTY = 0.0
REQUEST_QUEUE_CAPACITY = 192
DORMANT_SPECIALIZATION_CHILD_CAPACITY = 192
INCREMENTAL_HISTORY_SCHEMA = "native_v2_incremental_real_history.v1"
INCREMENTAL_HISTORY_EVENT_SCHEMA = (
    "native_v2_incremental_real_history_event.v1"
)
HISTORY_VALIDATION_INCREMENTAL = "incremental"
HISTORY_VALIDATION_LEGACY = "legacy_full_replay"
HISTORY_VALIDATION_MODES = frozenset({
    HISTORY_VALIDATION_INCREMENTAL,
    HISTORY_VALIDATION_LEGACY,
})
# These authority graphs contain immediate terminal leaves under requested OR
# roots.  A successful component reaches root CONFIRMED by formal tick seven;
# keep a wider invariant guard so an engine/topology regression fails hard.
_AUTHORITY_COMPONENT_MAX_TICKS = 32
_AUTHORITY_SETTLED_STATES = frozenset({
    NodeState.CONFIRMED,
    NodeState.FAILED,
})
_AUTHORITY_TERMINAL_CACHE_ENV_KEY = (
    "__native_v2_authority_terminal_evaluation_cache__"
)


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


class GenerationPhase(str, Enum):
    STRUCTURAL_OPEN = "STRUCTURAL_OPEN"
    PROSPECTIVE_OPEN = "PROSPECTIVE_OPEN"
    PROSPECTIVE_SEALED = "PROSPECTIVE_SEALED"


class RequestBasis(str, Enum):
    CERTIFIED_REVOCATION = "CERTIFIED_REVOCATION"
    UNCERTIFIED_MIXED_EVIDENCE = "UNCERTIFIED_MIXED_EVIDENCE"


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
    nomination_operation: str
    triggering_receipt_id: str | None
    graph_request_root_state: str | None
    graph_request_terminal_state: str | None
    considered_context_ids: tuple[str, ...]
    selected_context_ids: tuple[str, ...]
    nomination_read_frontier: int
    certification_frontier: int
    nomination_escrow_digest: str | None
    provenance_kind: ProvenanceKind = ProvenanceKind.EXACT_NOMINATION_READ_SET
    nomination_read_sets: tuple[tuple[str, tuple[str, ...]], ...] = ()
    transitive_ancestor_receipt_ids: tuple[str, ...] = ()
    discovery_exclusion_receipt_ids: tuple[str, ...] = ()
    initialization_origin: InitializationOrigin = InitializationOrigin.PROSPECTIVE
    hypothesis_digest: str = ""
    dormant_origin: DormantOrigin | None = None
    parent_hypothesis_digest: str | None = None
    source_generation: int = 0
    discovery_support_receipt_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.polarity is None:
            raise ProspectiveV2IntegrityError(
                "polarity=None at live candidate birth is forbidden"
            )
        object.__setattr__(self, "polarity", AvailabilityState(self.polarity))
        if self.polarity is AvailabilityState.UNKNOWN:
            raise ProspectiveV2IntegrityError(
                "UNKNOWN is not a live fixed hypothesis polarity"
            )
        if self.nomination_operation not in {
            "historical", "ordinary", "specialization",
        }:
            raise ProspectiveV2IntegrityError(
                "unknown frozen nomination operation"
            )
        if self.birth_frontier != self.certification_frontier:
            raise ProspectiveV2IntegrityError(
                "birth frontier differs from certification frontier"
            )
        if self.nomination_read_frontier > self.certification_frontier:
            raise ProspectiveV2IntegrityError(
                "nomination frontier exceeds certification frontier"
            )
        for context_ids in (
            self.considered_context_ids, self.selected_context_ids,
        ):
            if (
                tuple(sorted(set(context_ids))) != context_ids
                or len(set(context_ids)) != len(context_ids)
            ):
                raise ProspectiveV2IntegrityError(
                    "noncanonical frozen context identities"
                )
        if not set(self.selected_context_ids).issubset(
            self.considered_context_ids
        ):
            raise ProspectiveV2IntegrityError(
                "selected frozen context was not considered"
            )
        object.__setattr__(
            self, "provenance_kind", ProvenanceKind(self.provenance_kind)
        )
        object.__setattr__(
            self,
            "initialization_origin",
            InitializationOrigin(self.initialization_origin),
        )
        if self.dormant_origin is not None:
            object.__setattr__(
                self, "dormant_origin", DormantOrigin(self.dormant_origin)
            )
        if self.structural_state == StemCellState.DORMANT.name:
            if self.dormant_origin is None:
                raise ProspectiveV2IntegrityError(
                    "dormant hypothesis lacks explicit origin"
                )
        elif self.dormant_origin is not None:
            raise ProspectiveV2IntegrityError(
                "non-dormant hypothesis carries dormant origin"
            )
        if self.source_generation < 0:
            raise ProspectiveV2IntegrityError("negative source generation")
        discovery_support = tuple(sorted(set(
            self.discovery_support_receipt_ids
        )))
        if discovery_support != self.discovery_support_receipt_ids:
            raise ProspectiveV2IntegrityError(
                "noncanonical discovery support receipts"
            )
        if not set(discovery_support).issubset(self.discovery_receipt_ids):
            raise ProspectiveV2IntegrityError(
                "discovery support is outside discovery reads"
            )
        if self.source_generation > 0 and (
            self.nomination_operation != "specialization"
            or self.dormant_origin
            is not DormantOrigin.DEFERRED_SPECIALIZATION_CHILD
            or not self.parent_hypothesis_digest
        ):
            raise ProspectiveV2IntegrityError(
                "successor hypothesis lacks deferred lineage binding"
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
                or self.nomination_operation != "historical"
                or self.triggering_receipt_id is not None
                or self.graph_request_root_state is not None
                or self.graph_request_terminal_state is not None
                or self.considered_context_ids
                or self.selected_context_ids
                or self.nomination_escrow_digest is not None
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
            if (
                self.nomination_operation not in {
                    "ordinary", "specialization"
                }
                or not self.triggering_receipt_id
                or self.graph_request_root_state != NodeState.CONFIRMED.name
                or self.graph_request_terminal_state != NodeState.CONFIRMED.name
                or not self.nomination_escrow_digest
            ):
                raise ProspectiveV2IntegrityError(
                    "prospective frozen escrow identity is incomplete"
                )
            if tuple(name for name, _ids in categories) not in {
                NOMINATION_READ_CATEGORIES_V1,
                NOMINATION_READ_CATEGORIES_V2,
                NOMINATION_READ_CATEGORIES_V3,
            }:
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
            "nomination_operation": self.nomination_operation,
            "triggering_receipt_id": self.triggering_receipt_id,
            "graph_request_root_state": self.graph_request_root_state,
            "graph_request_terminal_state": self.graph_request_terminal_state,
            "considered_context_ids": list(self.considered_context_ids),
            "selected_context_ids": list(self.selected_context_ids),
            "nomination_read_frontier": self.nomination_read_frontier,
            "certification_frontier": self.certification_frontier,
            "nomination_escrow_digest": self.nomination_escrow_digest,
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
            "dormant_origin": (
                None if self.dormant_origin is None
                else self.dormant_origin.value
            ),
            "parent_hypothesis_digest": self.parent_hypothesis_digest,
            "source_generation": self.source_generation,
            "discovery_support_receipt_ids": list(
                self.discovery_support_receipt_ids
            ),
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
    dormant_origin: DormantOrigin | None
    immutable_hypothesis_digest: str | None
    parent_hypothesis_digest: str | None

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
            "dormant_origin": (
                None if self.dormant_origin is None
                else self.dormant_origin.value
            ),
            "immutable_hypothesis_digest": self.immutable_hypothesis_digest,
            "parent_hypothesis_digest": self.parent_hypothesis_digest,
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
    predecessor_continuation_digest: str
    pending_token: str
    outcome_terminal_identity: str
    environment_outcome_terminal_identity: str
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
            "predecessor_continuation_digest": (
                self.predecessor_continuation_digest
            ),
            "pending_token": self.pending_token,
            "outcome_terminal_identity": self.outcome_terminal_identity,
            "environment_outcome_terminal_identity": (
                self.environment_outcome_terminal_identity
            ),
            "state": self.state,
        }


@dataclass(frozen=True)
class IncrementalHistoryValidationState:
    """Non-authoritative append-only validation state for accepted REAL events.

    The graph never reads this state.  It can only reject an invalid append;
    complete reconstruction remains authoritative at explicit boundaries.
    """

    schema_version: str
    origin_digest: str
    first_ordinal: int
    event_count: int
    last_ordinal: int | None
    last_receipt_id: str | None
    last_event_digest: str | None
    history_digest: str

    def manifest(self) -> dict[str, Any]:
        return asdict(self)


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
    environment_outcome_terminal_identity: str
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
            "environment_outcome_terminal_identity": (
                self.environment_outcome_terminal_identity
            ),
            "observed_outcome": self.observed_outcome,
            "interaction_fingerprint": self.interaction_fingerprint,
            "issuer_identity": self.issuer_identity,
        }

    def manifest(self) -> dict[str, Any]:
        return {**self.unsigned_manifest(), "signature": self.signature}


@dataclass(frozen=True)
class AcceptedRealReference:
    """Immutable task-generic identity for one accepted REAL interaction."""

    receipt_id: str
    ordinal: int
    stable_physical_interaction_id: str
    trace_digest: str
    typed_signal_digest: str
    observed_outcome: bool
    source_generation: int
    ordered_signal_identities: tuple[str, ...]
    typed_signal_roles: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if not self.receipt_id or not self.stable_physical_interaction_id:
            raise ProspectiveV2IntegrityError("incomplete accepted REAL reference")
        if self.ordinal < 0 or self.source_generation < 0:
            raise ProspectiveV2IntegrityError("negative REAL reference ordinal")
        if tuple(sorted(self.typed_signal_roles)) != self.typed_signal_roles:
            raise ProspectiveV2IntegrityError("noncanonical typed signal roles")

    def manifest(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "ordinal": self.ordinal,
            "stable_physical_interaction_id": (
                self.stable_physical_interaction_id
            ),
            "trace_digest": self.trace_digest,
            "typed_signal_digest": self.typed_signal_digest,
            "observed_outcome": self.observed_outcome,
            "source_generation": self.source_generation,
            "ordered_signal_identities": list(self.ordered_signal_identities),
            "typed_signal_roles": [list(item) for item in self.typed_signal_roles],
        }


@dataclass(frozen=True)
class SpecializationCandidateTerminalState:
    identity: str
    node_id: str
    role_permitted: bool
    recursively_implied_by_parent: bool
    supporting_receipt_ids: tuple[str, ...]
    supporting_stable_physical_interaction_ids: tuple[str, ...]
    supporting_occurrence_count: int
    present_in_triggering_contradiction: bool
    specialization_mode: SpecializationMode
    confirmed: bool
    node_state: str
    inspected_receipt_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "specialization_mode",
            SpecializationMode(self.specialization_mode),
        )
        if self.supporting_occurrence_count != len(
            self.supporting_receipt_ids
        ):
            raise ProspectiveV2IntegrityError(
                "eligibility support count differs from receipts"
            )
        if (
            len(set(self.supporting_receipt_ids))
            != len(self.supporting_receipt_ids)
            or tuple(sorted(self.supporting_receipt_ids))
            != self.supporting_receipt_ids
            or len(set(self.supporting_stable_physical_interaction_ids))
            != len(self.supporting_stable_physical_interaction_ids)
            or tuple(sorted(
                self.supporting_stable_physical_interaction_ids
            )) != self.supporting_stable_physical_interaction_ids
            or len(self.supporting_receipt_ids)
            != len(self.supporting_stable_physical_interaction_ids)
        ):
            raise ProspectiveV2IntegrityError(
                "noncanonical eligibility support evidence"
            )
        if (
            len(set(self.inspected_receipt_ids))
            != len(self.inspected_receipt_ids)
            or tuple(sorted(self.inspected_receipt_ids))
            != self.inspected_receipt_ids
            or not set(self.supporting_receipt_ids).issubset(
                self.inspected_receipt_ids
            )
        ):
            raise ProspectiveV2IntegrityError(
                "noncanonical eligibility inspected evidence"
            )
        expected_confirmation = bool(
            self.role_permitted
            and not self.recursively_implied_by_parent
            and self.supporting_occurrence_count >= MIN_SUPPORT
            and (
                self.specialization_mode
                is SpecializationMode.COUNTEREXAMPLE_BLIND
                or (
                    self.specialization_mode
                    is SpecializationMode.LOCAL_CONTRAST
                    and not self.present_in_triggering_contradiction
                )
            )
        )
        expected_node_state = (
            NodeState.CONFIRMED.name
            if expected_confirmation else NodeState.FAILED.name
        )
        if (
            self.confirmed is not expected_confirmation
            or self.node_state != expected_node_state
        ):
            raise ProspectiveV2IntegrityError(
                "eligibility terminal result differs from graph rule"
            )

    def manifest(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "node_id": self.node_id,
            "role_permitted": self.role_permitted,
            "recursively_implied_by_parent": (
                self.recursively_implied_by_parent
            ),
            "supporting_receipt_ids": list(self.supporting_receipt_ids),
            "supporting_stable_physical_interaction_ids": list(
                self.supporting_stable_physical_interaction_ids
            ),
            "supporting_occurrence_count": self.supporting_occurrence_count,
            "present_in_triggering_contradiction": (
                self.present_in_triggering_contradiction
            ),
            "specialization_mode": self.specialization_mode.value,
            "confirmed": self.confirmed,
            "node_state": self.node_state,
            "inspected_receipt_ids": list(self.inspected_receipt_ids),
        }


@dataclass(frozen=True)
class DeferredSpecializationRequest:
    request_id: str
    source_generation: int
    parent_cell_id: str
    parent_hypothesis_digest: str
    fixed_polarity: AvailabilityState
    request_basis: RequestBasis
    request_emission_receipt_id: str
    request_emission_ordinal: int
    contradiction_receipt_id: str
    contradiction_ordinal: int
    specialization_mode: SpecializationMode
    parent_discovery_receipt_ids: tuple[str, ...]
    parent_discovery_support_receipt_ids: tuple[str, ...]
    parent_prospective_support_receipt_ids: tuple[str, ...]
    transitive_ancestor_receipt_ids: tuple[str, ...]
    candidate_terminals: tuple[SpecializationCandidateTerminalState, ...]
    graph_revocation_confirmed: bool
    graph_request_confirmed: bool

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "fixed_polarity", AvailabilityState(self.fixed_polarity)
        )
        object.__setattr__(
            self, "specialization_mode", SpecializationMode(
                self.specialization_mode
            )
        )
        object.__setattr__(
            self, "request_basis", RequestBasis(self.request_basis)
        )
        if not isinstance(self.graph_revocation_confirmed, bool) or not (
            isinstance(self.graph_request_confirmed, bool)
        ):
            raise ProspectiveV2IntegrityError(
                "request graph confirmations are not Boolean"
            )
        if self.specialization_mode is SpecializationMode.DISCONNECTED:
            raise ProspectiveV2IntegrityError("disconnected dummy request")
        if not self.graph_request_confirmed:
            raise ProspectiveV2IntegrityError(
                "request lacks graph confirmation"
            )
        if (
            not self.request_id
            or not self.request_emission_receipt_id
            or not self.contradiction_receipt_id
            or self.source_generation < 0
            or self.request_emission_ordinal < 0
            or self.contradiction_ordinal < 0
            or self.contradiction_ordinal > self.request_emission_ordinal
        ):
            raise ProspectiveV2IntegrityError(
                "invalid specialization request identity or order"
            )
        if self.request_basis is RequestBasis.CERTIFIED_REVOCATION:
            if (
                not self.graph_revocation_confirmed
                or self.contradiction_receipt_id
                != self.request_emission_receipt_id
                or self.contradiction_ordinal
                != self.request_emission_ordinal
            ):
                raise ProspectiveV2IntegrityError(
                    "certified-revocation request lacks its current "
                    "contradiction anchor"
                )
        elif self.graph_revocation_confirmed:
            raise ProspectiveV2IntegrityError(
                "uncertified mixed-evidence request claims revocation"
            )

    def identity_manifest(self) -> dict[str, Any]:
        """All causal request fields bound by ``request_id``."""

        return {
            "source_generation": self.source_generation,
            "parent_cell_id": self.parent_cell_id,
            "parent_hypothesis_digest": self.parent_hypothesis_digest,
            "fixed_polarity": self.fixed_polarity.value,
            "request_basis": self.request_basis.value,
            "request_emission_receipt_id": (
                self.request_emission_receipt_id
            ),
            "request_emission_ordinal": self.request_emission_ordinal,
            "contradiction_receipt_id": self.contradiction_receipt_id,
            "contradiction_ordinal": self.contradiction_ordinal,
            "specialization_mode": self.specialization_mode.value,
            "parent_discovery_receipt_ids": list(
                self.parent_discovery_receipt_ids
            ),
            "parent_discovery_support_receipt_ids": list(
                self.parent_discovery_support_receipt_ids
            ),
            "parent_prospective_support_receipt_ids": list(
                self.parent_prospective_support_receipt_ids
            ),
            "transitive_ancestor_receipt_ids": list(
                self.transitive_ancestor_receipt_ids
            ),
            "candidate_terminals": [
                item.manifest() for item in self.candidate_terminals
            ],
            "graph_revocation_confirmed": self.graph_revocation_confirmed,
            "graph_request_confirmed": self.graph_request_confirmed,
        }

    @property
    def eligible_base_ids(self) -> tuple[str, ...]:
        return tuple(
            item.identity for item in self.candidate_terminals
            if item.confirmed
        )

    def manifest(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            **self.identity_manifest(),
        }


@dataclass(frozen=True)
class StructuralRequestConsumption:
    request_id: str
    attempt_ordinal: int
    genome_seed: int
    genome_call_count: int
    selected_members: tuple[str, ...]
    disposition: str
    child_cell_id: str | None = None

    def manifest(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "attempt_ordinal": self.attempt_ordinal,
            "genome_seed": self.genome_seed,
            "genome_call_count": self.genome_call_count,
            "selected_members": list(self.selected_members),
            "disposition": self.disposition,
            "child_cell_id": self.child_cell_id,
        }


@dataclass(frozen=True)
class DeferredChildBirth:
    """A consumed structural request awaiting or recording one child birth."""

    request_id: str
    child_cell_id: str
    members: tuple[str, ...]
    genome_seed: int
    proposal_ordinal: int
    source_generation: int
    disposition: str

    def manifest(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "child_cell_id": self.child_cell_id,
            "members": list(self.members),
            "genome_seed": self.genome_seed,
            "proposal_ordinal": self.proposal_ordinal,
            "source_generation": self.source_generation,
            "disposition": self.disposition,
        }


@dataclass(frozen=True)
class GenerationBoundary:
    generation: int
    phase: GenerationPhase
    event_frontier: int
    prior_continuation_digest: str
    accepted_real_ledger_digest: str
    request_queue_digest: str
    structural_epoch_schedule_digest: str
    candidate_manifest_digest: str
    parent_decision_history_digest: str
    specialization_genome_seed: int

    def manifest(self) -> dict[str, Any]:
        return {
            "generation": self.generation,
            "phase": self.phase.value,
            "event_frontier": self.event_frontier,
            "prior_continuation_digest": self.prior_continuation_digest,
            "accepted_real_ledger_digest": self.accepted_real_ledger_digest,
            "request_queue_digest": self.request_queue_digest,
            "structural_epoch_schedule_digest": (
                self.structural_epoch_schedule_digest
            ),
            "candidate_manifest_digest": self.candidate_manifest_digest,
            "parent_decision_history_digest": (
                self.parent_decision_history_digest
            ),
            "specialization_genome_seed": self.specialization_genome_seed,
        }


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
    graph_specialization_request_ids: tuple[str, ...] = ()
    eligible_ids_by_request: tuple[tuple[str, tuple[str, ...]], ...] = ()
    candidate_terminal_states: tuple[
        tuple[str, tuple[SpecializationCandidateTerminalState, ...]], ...
    ] = ()
    request_queue_appended_ids: tuple[str, ...] = ()
    # Cells whose committed pre-outcome decision was contradicted.
    prequential_false_authority_ids: tuple[str, ...] = ()

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
    environment_outcome_terminal_identity: str
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
            "environment_outcome_terminal_identity": (
                self.environment_outcome_terminal_identity
            ),
            "interaction_fingerprint": self.interaction_fingerprint,
            "source_binding_identity": self.source_binding_identity,
        }

    def manifest(self) -> dict[str, Any]:
        return {
            **self.unsigned_manifest(),
            "binding_signature": self.binding_signature,
        }


def _cell_node_ids(cell_id: str) -> tuple[str, ...]:
    return tuple(f"v2:{role}:{cell_id}" for role in CELL_AUTHORITY_ROLES)


def _cell_topology_identity(cell_id: str) -> str:
    return _sha({
        "cell_id": cell_id,
        "nodes": list(_cell_node_ids(cell_id)),
        "edges": [
            [ROLE_ROOTS[role], f"v2:{role}:{cell_id}", "SUB_SUR"]
            for role in CELL_AUTHORITY_ROLES
        ],
    })


def _structural_match_descriptors(
    states: Mapping[str, ProspectiveAuthorityState],
) -> Mapping[str, StructuralMatchDescriptor]:
    """Freeze the graph-call structural input consumed by all terminals."""

    return MappingProxyType({
        item_id: StructuralMatchDescriptor(
            cell_id=item_id,
            members=value.hypothesis.members,
            structural_state=value.hypothesis.structural_state,
            lineage_parent_id=value.hypothesis.lineage_parent_id,
            specialization_depth=value.hypothesis.specialization_depth,
            nomination_operation=value.hypothesis.nomination_operation,
            parent_hypothesis_digest=(
                value.hypothesis.parent_hypothesis_digest
            ),
            hypothesis_digest=value.hypothesis.hypothesis_digest,
        )
        for item_id, value in states.items()
    })


def _structural_pattern_matches_descriptors(
    cell_id: str,
    descriptors: Mapping[str, StructuralMatchDescriptor],
    active_signal_ids: Sequence[str],
    visiting: frozenset[str] = frozenset(),
) -> bool:
    """Invoke the canonical matcher with V2's fail-hard error type."""

    try:
        return canonical_structural_pattern_matches(
            cell_id,
            descriptors,
            active_signal_ids,
            visiting,
        )
    except RuntimeError as exc:
        raise ProspectiveV2IntegrityError(str(exc)) from exc


def _structural_pattern_matches(
    cell_id: str,
    states: Mapping[str, ProspectiveAuthorityState],
    active_signal_ids: Sequence[str],
    visiting: frozenset[str] = frozenset(),
) -> bool:
    return _structural_pattern_matches_descriptors(
        cell_id,
        _structural_match_descriptors(states),
        active_signal_ids,
        visiting,
    )


@dataclass
class _StructuralPatternMatchCache:
    """Call-local top-level memo around the canonical semantic source."""

    descriptors: Mapping[str, StructuralMatchDescriptor]
    active_signal_ids: frozenset[str]
    matches: dict[str, bool] = field(default_factory=dict)

    def match(
        self,
        cell_id: str,
        visiting: frozenset[str] = frozenset(),
    ) -> bool:
        if not visiting and cell_id in self.matches:
            return self.matches[cell_id]
        result = _structural_pattern_matches_descriptors(
            cell_id,
            self.descriptors,
            tuple(self.active_signal_ids),
            visiting,
        )
        if not visiting:
            self.matches[cell_id] = result
        return result


def _receipt_supports(
    state: ProspectiveAuthorityState, receipt: V2GroundedReceipt
) -> bool:
    return receipt.observed_outcome == (
        state.hypothesis.polarity is AvailabilityState.AVAILABLE
    )


def _specialization_request_basis(
    state: ProspectiveAuthorityState,
    *,
    matched: bool,
    post_frontier: bool,
    supports: bool,
    contradicts: bool,
    specialization_mode: SpecializationMode,
    already_requested: bool,
) -> RequestBasis | None:
    """Return the unique causal basis for a projected REAL event."""

    if supports and contradicts:
        raise ProspectiveV2IntegrityError(
            "specialization trigger cannot support and contradict"
        )
    if not (
        matched
        and post_frontier
        and (supports or contradicts)
        and state.hypothesis.specialization_depth == 0
        and state.hypothesis.dormant_origin
        is DormantOrigin.MIXED_OUTCOME_SHADOW
        and not already_requested
        and specialization_mode is not SpecializationMode.DISCONNECTED
    ):
        return None
    if state.prospectively_certified and contradicts:
        return RequestBasis.CERTIFIED_REVOCATION
    projected_successes = state.successes + int(supports)
    projected_contradictions = state.contradictions + int(contradicts)
    if (
        not state.prospectively_certified
        and projected_successes >= MIN_SUPPORT
        and projected_contradictions >= 1
    ):
        return RequestBasis.UNCERTIFIED_MIXED_EVIDENCE
    return None


@dataclass(frozen=True)
class _SpecializationRequestTrigger:
    basis: RequestBasis
    emission_reference: AcceptedRealReference
    contradiction_reference: AcceptedRealReference
    parent_prospective_support_receipt_ids: tuple[str, ...]
    all_support_receipt_ids: tuple[str, ...]


def _validate_current_real_reference(
    receipt: V2GroundedReceipt,
    current_reference: AcceptedRealReference,
) -> None:
    """Prove that one accepted reference is the grounded REAL receipt."""

    if (
        current_reference.receipt_id != receipt.receipt_id
        or current_reference.ordinal != receipt.ordinal
        or current_reference.stable_physical_interaction_id
        != receipt.interaction_fingerprint
        or current_reference.observed_outcome != receipt.observed_outcome
        or current_reference.trace_digest != receipt.trace.digest()
        or current_reference.typed_signal_digest != _sha([
            asdict(item) for item in receipt.trace.terminal_signals
        ])
        or current_reference.ordered_signal_identities
        != receipt.trace.ordered_signal_identities
        or current_reference.typed_signal_roles != tuple(sorted(
            (item.identity, item.role)
            for item in receipt.trace.terminal_signals
        ))
    ):
        raise ProspectiveV2IntegrityError(
            "current REAL reference differs from grounded receipt"
        )


def _derive_specialization_request_trigger(
    state: ProspectiveAuthorityState,
    receipt: V2GroundedReceipt,
    current_reference: AcceptedRealReference,
    references: Mapping[str, AcceptedRealReference],
    *,
    matched: bool,
    specialization_mode: SpecializationMode,
    already_requested: bool,
    current_reference_validated: bool = False,
) -> _SpecializationRequestTrigger | None:
    """Bind request timing, current support, and the earliest contradiction."""

    if not current_reference_validated:
        _validate_current_real_reference(receipt, current_reference)
    post_frontier = bool(
        receipt.receipt_id
        and receipt.ordinal > state.hypothesis.certification_frontier
        and receipt.receipt_id
        not in state.hypothesis.discovery_exclusion_receipt_ids
    )
    supports = bool(post_frontier and _receipt_supports(state, receipt))
    contradicts = bool(post_frontier and not supports)
    basis = _specialization_request_basis(
        state,
        matched=matched,
        post_frontier=post_frontier,
        supports=supports,
        contradicts=contradicts,
        specialization_mode=specialization_mode,
        already_requested=already_requested,
    )
    if basis is None:
        return None

    prospective_support_ids = (
        *state.support_receipt_ids,
        *((receipt.receipt_id,) if supports else ()),
    )
    contradiction_ids = (
        *state.contradiction_receipt_ids,
        *((receipt.receipt_id,) if contradicts else ()),
    )
    missing = tuple(sorted(
        receipt_id for receipt_id in {
            *prospective_support_ids,
            *contradiction_ids,
            *state.hypothesis.discovery_support_receipt_ids,
            receipt.receipt_id,
        }
        if receipt_id not in references
    ))
    if missing:
        raise ProspectiveV2IntegrityError(
            "specialization trigger references are incomplete: "
            + ",".join(missing)
        )
    if not contradiction_ids:
        raise ProspectiveV2IntegrityError(
            "specialization request has no contradiction anchor"
        )
    contradiction_reference = min(
        (references[item] for item in contradiction_ids),
        key=lambda item: (item.ordinal, item.receipt_id),
    )
    return _SpecializationRequestTrigger(
        basis=basis,
        emission_reference=current_reference,
        contradiction_reference=contradiction_reference,
        parent_prospective_support_receipt_ids=tuple(sorted(
            prospective_support_ids
        )),
        all_support_receipt_ids=tuple(sorted({
            *state.hypothesis.discovery_support_receipt_ids,
            *prospective_support_ids,
        })),
    )


@dataclass(frozen=True)
class _AuthorityCellFacts:
    """One terminal-owned evaluation shared by a cell's eight role leaves."""

    commitment: bool
    available: bool
    refuted: bool
    support: bool
    contradiction: bool
    maturity: bool
    revocation: bool
    specialization_request: bool
    specialization_request_basis: RequestBasis | None

    def confirms(self, role: str) -> bool:
        if role not in CELL_AUTHORITY_ROLES:
            raise KeyError(role)
        return bool(getattr(self, role))


@dataclass
class _AuthorityTerminalEvaluationCache:
    """Graph-call-local common facts; never an injected authority-ID set."""

    snapshot: AuthorityMeasurementSnapshot
    states: Mapping[str, ProspectiveAuthorityState]
    specialization_mode: SpecializationMode
    lifetime_requested_parent_ids: frozenset[str]
    structural_matches: _StructuralPatternMatchCache
    facts: dict[str, _AuthorityCellFacts] = field(default_factory=dict)
    failures: dict[str, Exception] = field(default_factory=dict)

    @classmethod
    def from_environment(
        cls,
        snapshot: AuthorityMeasurementSnapshot,
        states: Mapping[str, ProspectiveAuthorityState],
        env: Mapping[str, Any],
    ) -> _AuthorityTerminalEvaluationCache:
        return cls(
            snapshot=snapshot,
            states=states,
            specialization_mode=SpecializationMode(env.get(
                "specialization_mode", SpecializationMode.DISCONNECTED.value
            )),
            lifetime_requested_parent_ids=frozenset(
                env.get("lifetime_requested_parent_ids", ())
            ),
            structural_matches=_StructuralPatternMatchCache(
                descriptors=_structural_match_descriptors(states),
                active_signal_ids=frozenset(
                    snapshot.trace.ordered_signal_identities
                ),
            ),
        )

    def facts_for(self, cell_id: str) -> _AuthorityCellFacts:
        if cell_id in self.facts:
            return self.facts[cell_id]
        if cell_id in self.failures:
            raise self.failures[cell_id]
        try:
            state = self.states.get(cell_id)
            if not isinstance(state, ProspectiveAuthorityState):
                raise ProspectiveV2IntegrityError(
                    "authority cell state is unavailable"
                )
            matched = self.structural_matches.match(cell_id)
            receipt = self.snapshot.grounded_receipt
            post_frontier = bool(
                receipt is not None
                and receipt.receipt_id
                and receipt.ordinal > state.hypothesis.certification_frontier
                and receipt.receipt_id
                not in state.hypothesis.discovery_exclusion_receipt_ids
            )
            supports = bool(
                post_frontier
                and receipt is not None
                and _receipt_supports(state, receipt)
            )
            contradicts = bool(post_frontier and not supports)
            projected_support = state.support + int(post_frontier)
            projected_successes = state.successes + int(supports)
            projected_contradictions = (
                state.contradictions + int(contradicts)
            )
            projected_success_lower = wilson_lower_bound(
                projected_successes, projected_support, WILSON_Z
            )
            request_basis = _specialization_request_basis(
                state,
                matched=matched,
                post_frontier=post_frontier,
                supports=supports,
                contradicts=contradicts,
                specialization_mode=self.specialization_mode,
                already_requested=(
                    cell_id in self.lifetime_requested_parent_ids
                ),
            )
            result = _AuthorityCellFacts(
                commitment=matched,
                available=(
                    matched and state.prospectively_certified
                    and state.hypothesis.polarity
                    is AvailabilityState.AVAILABLE
                ),
                refuted=(
                    matched and state.prospectively_certified
                    and state.hypothesis.polarity
                    is AvailabilityState.REFUTED
                ),
                support=matched and supports,
                contradiction=matched and contradicts,
                maturity=(
                    matched and supports
                    and not state.prospectively_certified
                    and projected_successes >= MIN_SUPPORT
                    and projected_contradictions == 0
                    and projected_success_lower >= LOWER_BOUND
                ),
                revocation=(
                    matched and contradicts and state.prospectively_certified
                ),
                specialization_request=request_basis is not None,
                specialization_request_basis=request_basis,
            )
        except Exception as exc:
            # The formal engine turns predicate exceptions into FAILED leaves.
            # Re-raising the same cached failure preserves that behavior for
            # every role without repeating an invalid structural traversal.
            self.failures[cell_id] = exc
            raise
        self.facts[cell_id] = result
        return result


def _authority_terminal_evaluation_cache(
    env: Mapping[str, Any],
    snapshot: AuthorityMeasurementSnapshot,
    states: Mapping[str, ProspectiveAuthorityState],
) -> _AuthorityTerminalEvaluationCache:
    root_env = env.get("__root_env__")
    owner = root_env if isinstance(root_env, dict) else env
    cached = owner.get(_AUTHORITY_TERMINAL_CACHE_ENV_KEY)
    if cached is None:
        cached = _AuthorityTerminalEvaluationCache.from_environment(
            snapshot, states, env
        )
        if isinstance(owner, dict):
            owner[_AUTHORITY_TERMINAL_CACHE_ENV_KEY] = cached
    if not isinstance(cached, _AuthorityTerminalEvaluationCache):
        raise ProspectiveV2IntegrityError(
            "invalid authority terminal evaluation cache"
        )
    if cached.snapshot is not snapshot or cached.states is not states:
        raise ProspectiveV2IntegrityError(
            "authority terminal evaluation cache crossed graph calls"
        )
    return cached


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
    facts = _authority_terminal_evaluation_cache(env, snapshot, states)
    confirmed = facts.facts_for(cell_id).confirms(role)
    node.activation.value = 1.0 if confirmed else 0.0
    return True, confirmed


def _specialization_identity_role_permitted(
    reference: AcceptedRealReference, identity: str
) -> bool:
    if identity == "internal:policy_response":
        return False
    roles = {
        role for item_identity, role in reference.typed_signal_roles
        if item_identity == identity
    }
    return bool(roles.intersection({"BASE_TERMINAL", "MATURE_COMPOSITE"}))


def _recursively_implied_signal_ids(
    cell_id: str,
    states: Mapping[str, ProspectiveAuthorityState],
    visiting: frozenset[str] = frozenset(),
) -> frozenset[str]:
    """Return the opaque signals required by one frozen structural pattern."""

    if cell_id in visiting:
        raise ProspectiveV2IntegrityError("cyclic implied-parent pattern")
    state = states.get(cell_id)
    if state is None:
        raise ProspectiveV2IntegrityError("implied-parent pattern is absent")
    implied: set[str] = set()
    next_visiting = visiting | {cell_id}
    for member in state.hypothesis.members:
        if member.startswith("context:"):
            implied.update(_recursively_implied_signal_ids(
                member.split(":", 1)[1], states, next_visiting
            ))
        else:
            implied.add(member)
    return frozenset(implied)


def _v2_specialization_eligibility_terminal(
    node: Node, env: Mapping[str, Any]
) -> tuple[bool, bool]:
    del env
    mode = SpecializationMode(str(node.meta["specialization_mode"]))
    confirmed = bool(
        node.meta["role_permitted"]
        and not node.meta["recursively_implied_by_parent"]
        and int(node.meta["supporting_occurrence_count"]) >= MIN_SUPPORT
        and (
            mode is SpecializationMode.COUNTEREXAMPLE_BLIND
            or (
                mode is SpecializationMode.LOCAL_CONTRAST
                and not node.meta["present_in_triggering_contradiction"]
            )
        )
    )
    node.activation.value = 1.0 if confirmed else 0.0
    return True, confirmed


def _build_authority_graph(
    states: Mapping[str, ProspectiveAuthorityState],
) -> Graph:
    """Build the canonical organism-owned authority graph."""
    graph = Graph()
    for role in CELL_AUTHORITY_ROLES:
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


def _authority_component_nodes(
    graph: Graph,
    root_ids: Sequence[str],
) -> frozenset[str]:
    """Return the requested authority stars and reject malformed components."""

    active: set[str] = set()
    for root_id in root_ids:
        root = graph.nodes.get(root_id)
        if root is None or root.ntype is not NodeType.SCRIPT:
            raise ProspectiveV2IntegrityError(
                f"authority component root is unavailable: {root_id}"
            )
        children = tuple(graph.children(root_id))
        if not children:
            raise ProspectiveV2IntegrityError(
                f"authority component has no terminals: {root_id}"
            )
        if any(
            graph.nodes.get(child_id) is None
            or graph.nodes[child_id].ntype is not NodeType.TERMINAL
            for child_id in children
        ):
            raise ProspectiveV2IntegrityError(
                f"authority component is not a terminal star: {root_id}"
            )
        active.add(root_id)
        active.update(children)
    return frozenset(active)


def _authority_component_settled(
    engine: FormalReConEngine,
    active_nodes: frozenset[str],
) -> bool:
    """All requested roots and leaves reached graph-absorbing states."""

    return all(
        engine.g.nodes[node_id].state in _AUTHORITY_SETTLED_STATES
        for node_id in active_nodes
    )


def _run_authority_component(
    graph: Graph,
    root_ids: Sequence[str],
    *,
    env: Mapping[str, Any],
) -> FormalReConEngine:
    """Execute immediate authority stars to absorption or fail hard."""

    roots = tuple(root_ids)
    active_nodes = _authority_component_nodes(graph, roots)
    engine = FormalReConEngine(graph, record_trace=False)
    for root_id in roots:
        engine.request(root_id)
    engine.run(
        max_ticks=_AUTHORITY_COMPONENT_MAX_TICKS,
        env=dict(env),
        until=lambda current: _authority_component_settled(
            current, active_nodes
        ),
        active_nodes=active_nodes,
    )
    if not _authority_component_settled(engine, active_nodes):
        unsettled = tuple(sorted(
            (node_id, graph.nodes[node_id].state.name)
            for node_id in active_nodes
            if graph.nodes[node_id].state not in _AUTHORITY_SETTLED_STATES
        ))
        raise ProspectiveV2IntegrityError(
            "authority graph did not settle within fail-hard cap: "
            f"{unsettled}"
        )
    return engine


def _predicate_identity(predicate: Any) -> str | None:
    if predicate is None:
        return None
    return (
        f"{getattr(predicate, '__module__', '')}:"
        f"{getattr(predicate, '__qualname__', repr(predicate))}"
    )


def _executed_authority_topology_manifest(
    states: Mapping[str, ProspectiveAuthorityState],
) -> dict[str, Any]:
    """Describe the exact freshly built graph that authority executes."""

    graph = _build_authority_graph(states)
    return {
        "graph_snapshot": graph.to_snapshot(),
        "predicate_identities": {
            node_id: _predicate_identity(getattr(node, "predicate", None))
            for node_id, node in sorted(graph.nodes.items())
        },
        "root_confirmation_policies": {
            role: (
                None
                if ROLE_ROOTS[role] not in graph.nodes
                else graph.nodes[ROLE_ROOTS[role]].meta.get(
                    "confirm_policy"
                )
            )
            for role in AUTHORITY_ROLES
        },
        "authority_roles": list(AUTHORITY_ROLES),
        "lifecycle_constants": {
            "minimum_support": MIN_SUPPORT,
            "lower_bound": LOWER_BOUND,
            "wilson_z": WILSON_Z,
            "native_maturity_property": (
                "CompetenceContextCell.is_mature:MATURE_only"
            ),
        },
    }


def _run_authority_graph(
    states: Mapping[str, ProspectiveAuthorityState],
    snapshot: AuthorityMeasurementSnapshot,
    *,
    accepted_real_references: Mapping[str, AcceptedRealReference] | None = None,
    current_real_reference: AcceptedRealReference | None = None,
    specialization_mode: SpecializationMode = SpecializationMode.DISCONNECTED,
    lifetime_requested_parent_ids: Sequence[str] = (),
) -> dict[str, Any]:
    if not states:
        return {
            **{role: () for role in AUTHORITY_ROLES},
            "specialization_candidate_states": (),
        }
    specialization_mode = SpecializationMode(specialization_mode)
    graph = _build_authority_graph(states)
    _run_authority_component(
        graph,
        tuple(ROLE_ROOTS[role] for role in CELL_AUTHORITY_ROLES),
        env={
            "authority_snapshot": snapshot,
            "authority_states": states,
            "specialization_mode": specialization_mode.value,
            "lifetime_requested_parent_ids": tuple(
                lifetime_requested_parent_ids
            ),
        },
    )
    result: dict[str, Any] = {
        role: tuple(sorted(
            cell_id for cell_id in states
            if graph.nodes[f"v2:{role}:{cell_id}"].state
            == NodeState.CONFIRMED
        ))
        for role in CELL_AUTHORITY_ROLES
    }
    request_parents = result["specialization_request"]
    candidate_states: list[
        tuple[str, tuple[SpecializationCandidateTerminalState, ...]]
    ] = []
    confirmed_tokens: list[str] = []
    receipt = snapshot.grounded_receipt
    references = dict(accepted_real_references or {})
    if receipt is None:
        if current_real_reference is not None:
            raise ProspectiveV2IntegrityError(
                "pre-outcome graph received a grounded REAL reference"
            )
    else:
        if current_real_reference is None:
            raise ProspectiveV2IntegrityError(
                "grounded graph lacks its current accepted REAL reference"
            )
        _validate_current_real_reference(receipt, current_real_reference)
        prior = references.get(current_real_reference.receipt_id)
        if prior is not None and prior != current_real_reference:
            raise ProspectiveV2IntegrityError(
                "grounded graph REAL reference collision"
            )
        references[current_real_reference.receipt_id] = (
            current_real_reference
        )
    if request_parents and receipt is None:
        raise ProspectiveV2IntegrityError(
            "specialization request lacks grounded REAL receipt"
        )
    if request_parents:
        graph.add_node(Node(
            ROLE_ROOTS["specialization_eligibility"],
            NodeType.SCRIPT,
            meta={
                "confirm_policy": "or",
                "authority_role": "specialization_eligibility",
            },
        ))
        eligibility_plans: list[
            tuple[str, tuple[str, ...], tuple[str, ...]]
        ] = []
        for parent_id in request_parents:
            state = states[parent_id]
            assert receipt is not None
            assert current_real_reference is not None
            trigger = _derive_specialization_request_trigger(
                state,
                receipt,
                current_real_reference,
                references,
                matched=True,
                specialization_mode=specialization_mode,
                already_requested=(
                    parent_id in lifetime_requested_parent_ids
                ),
                current_reference_validated=True,
            )
            if trigger is None:
                raise ProspectiveV2IntegrityError(
                    "graph request lacks a causal trigger"
                )
            implied_ids = _recursively_implied_signal_ids(parent_id, states)
            support_ids = trigger.all_support_receipt_ids
            support_refs = tuple(
                references[item] for item in support_ids if item in references
            )
            if len(support_refs) != len(support_ids):
                raise ProspectiveV2IntegrityError(
                    "request-bound support vocabulary is incomplete"
                )
            vocabulary = tuple(sorted({
                identity
                for reference in support_refs
                for identity in reference.ordered_signal_identities
                if _specialization_identity_role_permitted(
                    reference, identity
                )
            }))
            contradiction_signal_ids = (
                trigger.contradiction_reference.ordered_signal_identities
            )
            for identity in vocabulary:
                occurrence_refs = tuple(
                    reference for reference in support_refs
                    if identity in reference.ordered_signal_identities
                )
                supporting_receipt_ids = tuple(sorted(
                    reference.receipt_id for reference in occurrence_refs
                ))
                supporting_physical_ids = tuple(sorted(
                    reference.stable_physical_interaction_id
                    for reference in occurrence_refs
                ))
                role_permitted = any(
                    _specialization_identity_role_permitted(
                        reference, identity
                    )
                    for reference in occurrence_refs
                )
                present_in_contradiction = bool(
                    identity in contradiction_signal_ids
                )
                token = hashlib.sha256(
                    f"{parent_id}|{identity}".encode("utf-8")
                ).hexdigest()[:16]
                node_id = f"v2:specialization_eligibility:{token}"
                graph.add_node(Node(
                    node_id,
                    NodeType.TERMINAL,
                    predicate=_v2_specialization_eligibility_terminal,
                    meta={
                        "terminal_kind": "SPECIALIZATION_ELIGIBILITY",
                        "authority_role": "specialization_eligibility",
                        "parent_cell_id": parent_id,
                        "identity": identity,
                        "role_permitted": role_permitted,
                        "recursively_implied_by_parent": (
                            identity in implied_ids
                        ),
                        "supporting_receipt_ids": supporting_receipt_ids,
                        "supporting_stable_physical_interaction_ids": (
                            supporting_physical_ids
                        ),
                        "supporting_occurrence_count": len(
                            supporting_receipt_ids
                        ),
                        "present_in_triggering_contradiction": (
                            present_in_contradiction
                        ),
                        "specialization_mode": specialization_mode.value,
                    },
                ))
                graph.add_hierarchy_pair(
                    ROLE_ROOTS["specialization_eligibility"], node_id
                )
            inspected = tuple(sorted({
                *support_ids,
                trigger.contradiction_reference.receipt_id,
                trigger.emission_reference.receipt_id,
            }))
            eligibility_plans.append((parent_id, vocabulary, inspected))

        if any(
            vocabulary
            for _parent, vocabulary, _inspected in eligibility_plans
        ):
            _run_authority_component(
                graph,
                (ROLE_ROOTS["specialization_eligibility"],),
                env={},
            )

        for parent_id, vocabulary, inspected in eligibility_plans:
            terminal_rows: list[SpecializationCandidateTerminalState] = []
            for identity in vocabulary:
                token = hashlib.sha256(
                    f"{parent_id}|{identity}".encode("utf-8")
                ).hexdigest()[:16]
                node_id = f"v2:specialization_eligibility:{token}"
                meta = graph.nodes[node_id].meta
                confirmed = graph.nodes[node_id].state == NodeState.CONFIRMED
                if confirmed:
                    confirmed_tokens.append(f"{parent_id}|{identity}")
                terminal_rows.append(SpecializationCandidateTerminalState(
                    identity=identity,
                    node_id=node_id,
                    role_permitted=bool(meta["role_permitted"]),
                    recursively_implied_by_parent=bool(
                        meta["recursively_implied_by_parent"]
                    ),
                    supporting_receipt_ids=tuple(
                        meta["supporting_receipt_ids"]
                    ),
                    supporting_stable_physical_interaction_ids=tuple(
                        meta[
                            "supporting_stable_physical_interaction_ids"
                        ]
                    ),
                    supporting_occurrence_count=int(
                        meta["supporting_occurrence_count"]
                    ),
                    present_in_triggering_contradiction=bool(
                        meta["present_in_triggering_contradiction"]
                    ),
                    specialization_mode=SpecializationMode(
                        meta["specialization_mode"]
                    ),
                    confirmed=confirmed,
                    node_state=graph.nodes[node_id].state.name,
                    inspected_receipt_ids=inspected,
                ))
            candidate_states.append((parent_id, tuple(terminal_rows)))
    result["specialization_eligibility"] = tuple(sorted(confirmed_tokens))
    result["specialization_candidate_states"] = tuple(candidate_states)
    return result


def _canonical_source_manifest_digest(r0: Any) -> str:
    audit = r0.persistent_state_audit()
    return _sha({
        "source_manifest": r0.source_manifest,
        "persistent_state": {
            key: audit[key]
            for key in (
                "topology_sha256",
                "weights_sha256",
                "credit_sha256",
                "lifecycle_sha256",
            )
        },
    })


def _physical_trace_projection(
    trace_manifest: Mapping[str, Any],
    actuation_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Project an exact graph trace onto physical evidence identity.

    Frame labels and transaction identities are deliberately absent. Exact
    open-event pairing continues to use GraphSignalTrace.digest().
    """

    required_trace_keys = {
        "frame_id", "frame_kind", "source_organism_identity",
        "source_state_identity", "option_identity", "actuation",
        "confirmed_base_terminal_node_ids",
        "confirmed_mature_composite_ids", "terminal_signals",
    }
    required_signal_keys = {
        "identity", "role", "source_node_identity", "terminal_kind",
        "provenance", "stem_cell_identity",
    }
    required_actuation_keys = {
        "actuator_identity", "move_uci", "option_identity", "activation",
        "candidate_count", "formal_ticks", "graph_owned", "host_fallback",
    }
    signals = trace_manifest.get("terminal_signals")
    if (
        set(trace_manifest) != required_trace_keys
        or set(actuation_manifest) != required_actuation_keys
        or trace_manifest.get("frame_kind") != FrameKind.REAL.name
        or trace_manifest.get("actuation") != actuation_manifest
        or trace_manifest.get("option_identity")
        != actuation_manifest.get("option_identity")
        or not isinstance(signals, list)
    ):
        raise ProspectiveV2IntegrityError(
            "noncanonical physical trace projection"
        )
    typed_signals = []
    for signal in signals:
        if not isinstance(signal, Mapping) or set(signal) != required_signal_keys:
            raise ProspectiveV2IntegrityError(
                "noncanonical typed terminal signal"
            )
        typed_signals.append({
            key: signal[key] for key in (
                "identity", "role", "source_node_identity", "terminal_kind",
                "provenance", "stem_cell_identity",
            )
        })
    return {
        "schema_version": PHYSICAL_TRACE_PROJECTION_SCHEMA,
        "frame_kind": FrameKind.REAL.name,
        "source_organism_identity": trace_manifest.get(
            "source_organism_identity"
        ),
        "source_state_identity": trace_manifest.get("source_state_identity"),
        "option_identity": trace_manifest.get("option_identity"),
        "confirmed_base_terminal_node_ids": list(
            trace_manifest.get("confirmed_base_terminal_node_ids", ())
        ),
        "confirmed_mature_composite_ids": list(
            trace_manifest.get("confirmed_mature_composite_ids", ())
        ),
        "typed_terminal_signals": typed_signals,
        "selected_graph_actuation": copy.deepcopy(dict(actuation_manifest)),
    }


def _interaction_manifest(
    *,
    source_organism_identity: str,
    source_state_identity: str,
    predecessor_fen: str,
    trace_manifest: Mapping[str, Any],
    actuation_manifest: Mapping[str, Any],
    successor_fen: str,
    environment_outcome_terminal_identity: str,
) -> dict[str, Any]:
    physical_trace = _physical_trace_projection(
        trace_manifest, actuation_manifest
    )
    if (
        physical_trace["source_organism_identity"]
        != source_organism_identity
        or physical_trace["source_state_identity"]
        != source_state_identity
    ):
        raise ProspectiveV2IntegrityError(
            "physical trace source identity mismatch"
        )
    return {
        "projection_schema": PHYSICAL_TRACE_PROJECTION_SCHEMA,
        "source_organism_identity": source_organism_identity,
        "source_state_identity": source_state_identity,
        "predecessor": predecessor_fen,
        "physical_trace": physical_trace,
        "selected_actuation": copy.deepcopy(dict(actuation_manifest)),
        "successor": successor_fen,
        "environment_outcome_terminal_identity": (
            environment_outcome_terminal_identity
        ),
    }


def _interaction_fingerprint(
    *,
    source_organism_identity: str,
    source_state_identity: str,
    predecessor_fen: str,
    trace: GraphSignalTrace,
    actuation: GraphActuation,
    successor_fen: str,
    environment_outcome_terminal_identity: str,
) -> str:
    return _sha(_interaction_manifest(
        source_organism_identity=source_organism_identity,
        source_state_identity=source_state_identity,
        predecessor_fen=predecessor_fen,
        trace_manifest=trace.canonical_manifest(),
        actuation_manifest=asdict(actuation),
        successor_fen=successor_fen,
        environment_outcome_terminal_identity=(
            environment_outcome_terminal_identity
        ),
    ))


def _validated_prefix_physical_fingerprints(
    source: TraceNativeCompetenceOrganism,
) -> tuple[str, ...]:
    """Derive replay identity only from validated signed native receipts."""

    source.validate_canonical_evidence_ledger()
    fingerprints = []
    for receipt in sorted(
        source.receipts.values(),
        key=lambda item: (item.event_ordinal, item.event_id),
    ):
        source._validate_receipt(receipt)
        trace = receipt.decision_trace
        fingerprints.append(_interaction_fingerprint(
            source_organism_identity=trace.source_organism_identity,
            source_state_identity=trace.source_state_identity,
            predecessor_fen=receipt.predecessor_fen,
            trace=trace,
            actuation=trace.actuation,
            successor_fen=receipt.successor_fen,
            environment_outcome_terminal_identity=(
                receipt.completion_terminal_identity
            ),
        ))
    return tuple(sorted(set(fingerprints)))


class NativeV2FrameSession:
    """Epoch-local frozen-R0 runtime and immutable base-manifest guard."""

    def __init__(self, authority: "NativeProspectiveAuthorityV2") -> None:
        self.authority = authority
        self.base_manifest = copy.deepcopy(
            authority.base.continuation_manifest_v3()
        )
        self.base_continuation_digest = _sha(self.base_manifest)
        self.source_guard = authority.base.r0.inference_guard_identity()
        self.r0_session = NativeR0DreamSession(
            authority.base.r0,
            guard_each_request=False,
            persistent_digest=self.source_guard,
        )
        self.closed = False

    def _require_open(
        self, authority: "NativeProspectiveAuthorityV2"
    ) -> None:
        if self.closed:
            raise ProspectiveV2IntegrityError("V2 frame session is closed")
        if authority is not self.authority:
            raise ProspectiveV2IntegrityError(
                "V2 frame session belongs to another authority"
            )

    def continuation_digest(
        self, authority: "NativeProspectiveAuthorityV2"
    ) -> str:
        self._require_open(authority)
        return authority.continuation_digest(
            frozen_base_v3=self.base_manifest
        )

    def close(self) -> None:
        if self.closed:
            return
        runtime_error: Exception | None = None
        try:
            self.r0_session.close()
        except Exception as exc:  # preserve the first exact isolation failure
            runtime_error = exc
        current_base = self.authority.base.continuation_manifest_v3()
        current_source_guard = (
            self.authority.base.r0.inference_guard_identity()
        )
        self.closed = True
        if runtime_error is not None:
            raise runtime_error
        if current_base != self.base_manifest:
            raise ProspectiveV2IntegrityError(
                "V2 frame session observed base-organism mutation"
            )
        if current_source_guard != self.source_guard:
            raise ProspectiveV2IntegrityError(
                "V2 frame session observed frozen-R0 mutation"
            )


@dataclass
class NativeProspectiveAuthorityV2:
    base: TraceNativeCompetenceOrganism
    mode: V2Mode
    states: dict[str, ProspectiveAuthorityState]
    structural_invariants: dict[str, CellStructuralInvariant]
    authority_topology: dict[str, Any]
    historical_tombstones: dict[str, dict[str, Any]]
    next_expected_ordinal: int
    discovery_prefix_physical_fingerprints: tuple[str, ...]
    discovery_prefix_physical_fingerprint_digest: str
    specialization_genome_seed: int
    specialization_mode: SpecializationMode = SpecializationMode.DISCONNECTED
    structural_epoch_schedule: tuple[int, ...] = ()
    current_generation: int = 0
    generation_phase: GenerationPhase = GenerationPhase.PROSPECTIVE_OPEN
    accepted_real_references: dict[str, AcceptedRealReference] = field(
        default_factory=dict
    )
    deferred_requests: dict[str, DeferredSpecializationRequest] = field(
        default_factory=dict
    )
    request_queue: tuple[str, ...] = ()
    lifetime_requested_parent_ids: tuple[str, ...] = ()
    request_consumptions: dict[str, StructuralRequestConsumption] = field(
        default_factory=dict
    )
    deferred_child_births: dict[str, DeferredChildBirth] = field(
        default_factory=dict
    )
    deferred_child_escrows: dict[str, NominationEscrow] = field(
        default_factory=dict
    )
    generation_boundaries: tuple[GenerationBoundary, ...] = ()
    sealed_request_ids: tuple[str, ...] = ()
    sealed_request_queue_digest: str | None = None
    evaluation_sealed: bool = False
    pending_event: PendingRealEvent | None = None
    consumed_receipts: dict[str, V2GroundedReceipt] = field(default_factory=dict)
    consumed_tokens: set[str] = field(default_factory=set)
    prospective_physical_fingerprints: dict[str, str] = field(
        default_factory=dict
    )
    emissions: dict[str, V2CertificationEmission] = field(default_factory=dict)
    event_transactions: dict[str, dict[str, Any]] = field(default_factory=dict)
    nomination_events: tuple[dict[str, Any], ...] = ()
    experimental_identity: dict[str, Any] | None = None
    incremental_history_state: IncrementalHistoryValidationState | None = None
    schema_version: str = SCHEMA_VERSION
    _receipt_secret: bytes = field(
        default=b"native-prospective-v2-environment-terminal"
    )
    _history_validation_mode: str = field(
        default=HISTORY_VALIDATION_INCREMENTAL,
        repr=False,
        compare=False,
    )

    @classmethod
    def from_organism(
        cls,
        source: TraceNativeCompetenceOrganism,
        *,
        mode: V2Mode,
        frontier: int | None = None,
        specialization_mode: SpecializationMode = SpecializationMode.DISCONNECTED,
        structural_epoch_schedule: Sequence[int] = (),
    ) -> "NativeProspectiveAuthorityV2":
        if frontier is not None:
            raise ProspectiveV2IntegrityError(
                "runner-supplied frontier is forbidden"
            )
        mode = V2Mode(mode)
        specialization_mode = SpecializationMode(specialization_mode)
        schedule = tuple(map(int, structural_epoch_schedule))
        if tuple(sorted(set(schedule))) != schedule or any(
            item < 0 for item in schedule
        ):
            raise ProspectiveV2IntegrityError(
                "structural epoch schedule is not canonical"
            )
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
            StemCellState.DORMANT,
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
            if historical and cell.state is StemCellState.TRIAL:
                raise ProspectiveProvenanceUnavailable(
                    "prospective_provenance_unavailable: unsupported "
                    f"historical live TRIAL {cell.cell_id}"
                )
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
                    nomination_operation="historical",
                    triggering_receipt_id=None,
                    graph_request_root_state=None,
                    graph_request_terminal_state=None,
                    considered_context_ids=(),
                    selected_context_ids=(),
                    nomination_read_frontier=epoch.opening_frontier,
                    certification_frontier=epoch.opening_frontier,
                    nomination_escrow_digest=None,
                    provenance_kind=ProvenanceKind.HISTORICAL_ACCEPTED_LEDGER,
                    discovery_exclusion_receipt_ids=historical_ledger_ids,
                    initialization_origin=InitializationOrigin.HISTORICAL,
                    dormant_origin=getattr(cell, "dormant_origin", None),
                    source_generation=0,
                    discovery_support_receipt_ids=tuple(sorted(
                        receipt_id
                        for receipt_id in historical_ledger_ids
                        if cls._historical_receipt_supports_cell(
                            base, cell, receipt_id
                        )
                    )),
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
                    birth_frontier=escrow.certification_frontier,
                    structural_state=cell.state.name,
                    nomination_operation=escrow.operation,
                    triggering_receipt_id=escrow.triggering_receipt_id,
                    graph_request_root_state=escrow.graph_request_root_state,
                    graph_request_terminal_state=(
                        escrow.graph_request_terminal_state
                    ),
                    considered_context_ids=escrow.considered_context_ids,
                    selected_context_ids=escrow.selected_context_ids,
                    nomination_read_frontier=escrow.nomination_read_frontier,
                    certification_frontier=escrow.certification_frontier,
                    nomination_escrow_digest=escrow.escrow_digest,
                    provenance_kind=ProvenanceKind.EXACT_NOMINATION_READ_SET,
                    nomination_read_sets=escrow.categorized_reads,
                    transitive_ancestor_receipt_ids=(
                        escrow.transitive_ancestor_receipt_ids
                    ),
                    discovery_exclusion_receipt_ids=(
                        escrow.discovery_exclusion_receipt_ids
                    ),
                    initialization_origin=InitializationOrigin.PROSPECTIVE,
                    dormant_origin=getattr(cell, "dormant_origin", None),
                    parent_hypothesis_digest=escrow.parent_hypothesis_digest,
                    source_generation=0,
                    discovery_support_receipt_ids=tuple(sorted(
                        receipt_id
                        for receipt_id in escrow.discovery_receipt_ids
                        if cls._historical_receipt_supports_cell(
                            base, cell, receipt_id
                        )
                    )),
                )
            cell.immutable_hypothesis_digest = frozen.hypothesis_digest
            states[cell.cell_id] = ProspectiveAuthorityState(
                hypothesis=frozen,
                prospectively_certified=(
                    mode is V2Mode.LEGACY and cell.is_mature
                ),
            )
        topology = _executed_authority_topology_manifest(states)
        invariants = {
            cell_id: cls._invariant_from_cell(base.envelope.cells[cell_id])
            for cell_id in states
        }
        prefix_fingerprints = _validated_prefix_physical_fingerprints(base)
        item = cls(
            base=base,
            mode=mode,
            states=states,
            structural_invariants=invariants,
            authority_topology=topology,
            historical_tombstones=tombstones,
            next_expected_ordinal=base._next_event_ordinal,
            discovery_prefix_physical_fingerprints=prefix_fingerprints,
            discovery_prefix_physical_fingerprint_digest=_sha(
                list(prefix_fingerprints)
            ),
            specialization_genome_seed=base.learning_config.genome_seed,
            specialization_mode=specialization_mode,
            structural_epoch_schedule=schedule,
            accepted_real_references={
                reference.receipt_id: reference
                for reference in cls._historical_real_references(base)
            },
        )
        item._verify_invariants()
        return item

    @staticmethod
    def _historical_receipt_supports_cell(
        base: TraceNativeCompetenceOrganism,
        cell: CompetenceContextCell,
        receipt_id: str,
    ) -> bool:
        record = base.envelope.evidence[receipt_id]
        return bool(
            base.envelope._cell_pattern_matches(cell, record, set())
            and record.observed_completion
            == (cell.polarity is AvailabilityState.AVAILABLE)
        )

    @staticmethod
    def _historical_real_references(
        base: TraceNativeCompetenceOrganism,
    ) -> tuple[AcceptedRealReference, ...]:
        rows: list[AcceptedRealReference] = []
        for receipt in sorted(
            base.receipts.values(),
            key=lambda item: (item.event_ordinal, item.event_id),
        ):
            trace = receipt.decision_trace
            physical_identity = _interaction_fingerprint(
                source_organism_identity=trace.source_organism_identity,
                source_state_identity=trace.source_state_identity,
                predecessor_fen=receipt.predecessor_fen,
                trace=trace,
                actuation=trace.actuation,
                successor_fen=receipt.successor_fen,
                environment_outcome_terminal_identity=(
                    receipt.completion_terminal_identity
                ),
            )
            rows.append(AcceptedRealReference(
                receipt_id=receipt.event_id,
                ordinal=receipt.event_ordinal,
                stable_physical_interaction_id=physical_identity,
                trace_digest=trace.digest(),
                typed_signal_digest=_sha([
                    asdict(item) for item in trace.terminal_signals
                ]),
                observed_outcome=receipt.observed_terminal_result,
                source_generation=0,
                ordered_signal_identities=trace.ordered_signal_identities,
                typed_signal_roles=tuple(sorted(
                    (item.identity, item.role)
                    for item in trace.terminal_signals
                )),
            ))
        return tuple(rows)

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
            dormant_origin=getattr(cell, "dormant_origin", None),
            immutable_hypothesis_digest=getattr(
                cell, "immutable_hypothesis_digest", None
            ),
            parent_hypothesis_digest=(
                None if cell.nomination_escrow is None
                else cell.nomination_escrow.parent_hypothesis_digest
            ),
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

    def _build_experimental_identity(
        self,
        *,
        base_continuation_digest: str | None = None,
    ) -> dict[str, Any]:
        epoch = self.base.envelope.nomination_epoch
        if epoch is None or not epoch.nomination_closed:
            raise ProspectiveV2IntegrityError(
                "experimental identity requires closed nomination"
            )
        candidate_population = {
            "hypotheses": {
                key: value.hypothesis.manifest()
                for key, value in sorted(self.states.items())
            },
            "escrows": {
                cell_id: (
                    None
                    if self.base.envelope.cells[cell_id].nomination_escrow
                    is None
                    else self.base.envelope.cells[
                        cell_id
                    ].nomination_escrow.manifest()
                )
                for cell_id in sorted(self.states)
            },
            "lineage": {
                cell_id: {
                    "parent": value.hypothesis.lineage_parent_id,
                    "depth": value.hypothesis.specialization_depth,
                }
                for cell_id, value in sorted(self.states.items())
            },
            "tombstones": copy.deepcopy(self.historical_tombstones),
            "epoch_close": epoch.manifest(),
            "executed_authority_topology": copy.deepcopy(
                self.authority_topology
            ),
        }
        unsigned = {
            "schema_version": self.schema_version,
            "implementation_identity": IMPLEMENTATION_IDENTITY,
            "mode": self.mode.value,
            "source": {
                "organism_identity": (
                    self.base.r0.source_organism_identity()
                ),
                "state_identity": self.base.r0.trace_state_identity(),
                "base_continuation_digest": (
                    self.base.continuation_digest_v3()
                    if base_continuation_digest is None
                    else str(base_continuation_digest)
                ),
            },
            "candidate_population_identity": _sha(candidate_population),
            "candidate_population": candidate_population,
            "physical_evidence_identity": {
                "projection_schema": PHYSICAL_TRACE_PROJECTION_SCHEMA,
                "discovery_prefix_physical_fingerprints": list(
                    self.discovery_prefix_physical_fingerprints
                ),
                "discovery_prefix_physical_fingerprint_digest": (
                    self.discovery_prefix_physical_fingerprint_digest
                ),
            },
            "arm_initialization": {
                cell_id: {
                    "prospectively_certified": (
                        self.mode is V2Mode.LEGACY
                        and value.hypothesis.structural_state
                        == StemCellState.MATURE.name
                    ),
                    "fixed_polarity": value.hypothesis.polarity.value,
                    "structural_state": (
                        value.hypothesis.structural_state
                    ),
                }
                for cell_id, value in sorted(self.states.items())
            },
            "specialization_genome_seed": self.specialization_genome_seed,
            "close_event": copy.deepcopy(
                self.nomination_events[-1]
                if self.nomination_events else None
            ),
        }
        return {**unsigned, "identity_digest": _sha(unsigned)}

    def set_history_validation_mode_for_development(self, mode: str) -> None:
        """Select validation strategy without changing learner-visible state."""

        if mode not in HISTORY_VALIDATION_MODES:
            raise ValueError(f"unknown history validation mode: {mode}")
        if self.pending_event is not None:
            raise ProspectiveV2IntegrityError(
                "history validation mode cannot change during an open event"
            )
        self._history_validation_mode = mode

    def _history_expected_start(self) -> int:
        epoch = self.base.envelope.nomination_epoch
        if epoch is None:
            raise ProspectiveV2IntegrityError(
                "prospective discovery epoch is absent"
            )
        return max(dict(epoch.receipt_ordinals).values(), default=-1) + 1

    def _incremental_history_origin_digest(self) -> str:
        initial_ids = tuple(sorted(
            cell_id for cell_id, state in self.states.items()
            if state.hypothesis.source_generation == 0
        ))
        return _sha({
            "schema_version": INCREMENTAL_HISTORY_SCHEMA,
            "implementation_identity": IMPLEMENTATION_IDENTITY,
            "mode": self.mode.value,
            "specialization_mode": self.specialization_mode.value,
            "first_ordinal": self._history_expected_start(),
            "source_organism_identity": (
                self.base.r0.source_organism_identity()
            ),
            "source_state_identity": self.base.r0.trace_state_identity(),
            "discovery_prefix_physical_fingerprint_digest": (
                self.discovery_prefix_physical_fingerprint_digest
            ),
            "initial_hypotheses": {
                cell_id: self.states[cell_id].hypothesis.manifest()
                for cell_id in initial_ids
            },
            "initial_structural_invariants": {
                cell_id: self.structural_invariants[cell_id].manifest()
                for cell_id in initial_ids
            },
            "historical_tombstone_digest": _sha(
                self.historical_tombstones
            ),
        })

    def _new_incremental_history_state(
        self,
    ) -> IncrementalHistoryValidationState:
        first = self._history_expected_start()
        origin = self._incremental_history_origin_digest()
        return IncrementalHistoryValidationState(
            schema_version=INCREMENTAL_HISTORY_SCHEMA,
            origin_digest=origin,
            first_ordinal=first,
            event_count=0,
            last_ordinal=None,
            last_receipt_id=None,
            last_event_digest=None,
            history_digest=_sha({
                "schema_version": INCREMENTAL_HISTORY_SCHEMA,
                "origin_digest": origin,
                "first_ordinal": first,
            }),
        )

    def _ensure_incremental_history_initialized(self) -> None:
        if self.incremental_history_state is None:
            if self.consumed_receipts:
                raise ProspectiveV2IntegrityError(
                    "incremental history missing for accepted REAL events"
                )
            self.incremental_history_state = (
                self._new_incremental_history_state()
            )

    @staticmethod
    def _incremental_lifecycle_projection(
        state: ProspectiveAuthorityState,
    ) -> dict[str, Any]:
        return {
            "hypothesis_digest": state.hypothesis.hypothesis_digest,
            "source_generation": state.hypothesis.source_generation,
            "prospectively_certified": state.prospectively_certified,
            "successes": state.successes,
            "contradictions": state.contradictions,
            "support": state.support,
            "success_lower_bound": state.success_lower_bound,
            "contradiction_lower_bound": state.contradiction_lower_bound,
            "certification_receipt_count": len(
                state.certification_receipt_ids
            ),
            "last_certification_receipt_id": (
                state.certification_receipt_ids[-1]
                if state.certification_receipt_ids else None
            ),
            "support_receipt_count": len(state.support_receipt_ids),
            "last_support_receipt_id": (
                state.support_receipt_ids[-1]
                if state.support_receipt_ids else None
            ),
            "contradiction_receipt_count": len(
                state.contradiction_receipt_ids
            ),
            "last_contradiction_receipt_id": (
                state.contradiction_receipt_ids[-1]
                if state.contradiction_receipt_ids else None
            ),
            "transition_count": len(state.transition_rows),
            "last_transition": (
                state.transition_rows[-1] if state.transition_rows else None
            ),
        }

    def _incremental_predecessor_digest_from_parts(
        self,
        *,
        history: IncrementalHistoryValidationState,
        states: Mapping[str, ProspectiveAuthorityState],
        generation: int,
        next_ordinal: int,
        request_ids: Sequence[str],
        lifetime_requested_parent_ids: Sequence[str],
    ) -> str:
        active = {
            cell_id: state for cell_id, state in states.items()
            if state.hypothesis.source_generation <= generation
        }
        return _sha({
            "schema_version": INCREMENTAL_HISTORY_SCHEMA,
            "history": history.manifest(),
            "generation": generation,
            "next_ordinal": next_ordinal,
            "specialization_mode": self.specialization_mode.value,
            "active_lifecycle": {
                cell_id: self._incremental_lifecycle_projection(state)
                for cell_id, state in sorted(active.items())
            },
            "active_structural_invariants": {
                cell_id: self.structural_invariants[cell_id].manifest()
                for cell_id in sorted(active)
            },
            "active_authority_topology_digest": _sha(
                _executed_authority_topology_manifest(active)
            ),
            "request_ids": list(request_ids),
            "lifetime_requested_parent_ids": list(
                lifetime_requested_parent_ids
            ),
        })

    def _incremental_predecessor_continuation_digest(self) -> str:
        history = self.incremental_history_state
        if history is None:
            raise ProspectiveV2IntegrityError(
                "incremental history is not initialized"
            )
        return self._incremental_predecessor_digest_from_parts(
            history=history,
            states=self.states,
            generation=self.current_generation,
            next_ordinal=self.next_expected_ordinal,
            request_ids=self.request_queue,
            lifetime_requested_parent_ids=(
                self.lifetime_requested_parent_ids
            ),
        )

    @staticmethod
    def _incremental_event_manifest(
        *,
        position: int,
        previous_history_digest: str,
        receipt: V2GroundedReceipt,
        transaction: Mapping[str, Any],
        reference: AcceptedRealReference,
        emission: V2CertificationEmission,
    ) -> dict[str, Any]:
        return {
            "schema_version": INCREMENTAL_HISTORY_EVENT_SCHEMA,
            "position": position,
            "ordinal": receipt.ordinal,
            "previous_history_digest": previous_history_digest,
            "predecessor_continuation_digest": transaction.get(
                "predecessor_continuation_digest"
            ),
            "receipt": receipt.manifest(),
            "transaction": dict(transaction),
            "accepted_reference": reference.manifest(),
            "emission": emission.manifest(),
        }

    @classmethod
    def _next_incremental_history_state(
        cls,
        prior: IncrementalHistoryValidationState,
        *,
        receipt: V2GroundedReceipt,
        transaction: Mapping[str, Any],
        reference: AcceptedRealReference,
        emission: V2CertificationEmission,
    ) -> IncrementalHistoryValidationState:
        position = prior.event_count
        expected_ordinal = prior.first_ordinal + position
        if receipt.ordinal != expected_ordinal:
            raise ProspectiveV2IntegrityError(
                "incremental history append position mismatch"
            )
        if not transaction.get("predecessor_continuation_digest"):
            raise ProspectiveV2IntegrityError(
                "incremental history predecessor continuation is absent"
            )
        event = cls._incremental_event_manifest(
            position=position,
            previous_history_digest=prior.history_digest,
            receipt=receipt,
            transaction=transaction,
            reference=reference,
            emission=emission,
        )
        event_digest = _sha(event)
        history_digest = _sha({
            "schema_version": INCREMENTAL_HISTORY_SCHEMA,
            "previous_history_digest": prior.history_digest,
            "contiguous_position": position,
            "event_digest": event_digest,
        })
        return IncrementalHistoryValidationState(
            schema_version=INCREMENTAL_HISTORY_SCHEMA,
            origin_digest=prior.origin_digest,
            first_ordinal=prior.first_ordinal,
            event_count=position + 1,
            last_ordinal=receipt.ordinal,
            last_receipt_id=receipt.receipt_id,
            last_event_digest=event_digest,
            history_digest=history_digest,
        )

    def _append_incremental_history(
        self,
        *,
        receipt: V2GroundedReceipt,
        transaction: Mapping[str, Any],
        reference: AcceptedRealReference,
        emission: V2CertificationEmission,
    ) -> None:
        prior = self.incremental_history_state
        if prior is None:
            raise ProspectiveV2IntegrityError(
                "incremental history is not initialized at append"
            )
        self.incremental_history_state = self._next_incremental_history_state(
            prior,
            receipt=receipt,
            transaction=transaction,
            reference=reference,
            emission=emission,
        )

    def _verify_incremental_history_state(self) -> None:
        if self._history_validation_mode not in HISTORY_VALIDATION_MODES:
            raise ProspectiveV2IntegrityError(
                "unknown incremental history validation mode"
            )
        history = self.incremental_history_state
        count = len(self.consumed_receipts)
        if history is None:
            if count or self.pending_event is not None:
                raise ProspectiveV2IntegrityError(
                    "incremental history missing for active REAL history"
                )
            return
        if (
            history.schema_version != INCREMENTAL_HISTORY_SCHEMA
            or history.origin_digest
            != self._incremental_history_origin_digest()
            or history.first_ordinal != self._history_expected_start()
            or history.event_count != count
            or self.next_expected_ordinal
            != history.first_ordinal + history.event_count
        ):
            raise ProspectiveV2IntegrityError(
                "incremental history state identity mismatch"
            )
        expected_last = (
            None if not count else self.next_expected_ordinal - 1
        )
        if history.last_ordinal != expected_last:
            raise ProspectiveV2IntegrityError(
                "incremental history last ordinal mismatch"
            )
        if count:
            receipt = self.consumed_receipts.get(history.last_receipt_id or "")
            if receipt is None or receipt.ordinal != history.last_ordinal:
                raise ProspectiveV2IntegrityError(
                    "incremental history last receipt mismatch"
                )
        elif any((
            history.last_receipt_id,
            history.last_event_digest,
            history.last_ordinal,
        )):
            raise ProspectiveV2IntegrityError(
                "empty incremental history has a terminal event"
            )
        if any(len(value) != 64 for value in (
            history.origin_digest,
            history.history_digest,
            history.last_event_digest or "0" * 64,
        )):
            raise ProspectiveV2IntegrityError(
                "incremental history digest encoding mismatch"
            )
        if (
            len(self.consumed_tokens) != count
            or len(self.prospective_physical_fingerprints) != count
            or len(self.emissions) != count
            or len(self.accepted_real_references)
            != len(self.base.receipts) + count
        ):
            raise ProspectiveV2IntegrityError(
                "incremental history ledger cardinality mismatch"
            )
        expected_transactions = count + (
            1 if self.pending_event is not None else 0
        )
        if len(self.event_transactions) != expected_transactions:
            raise ProspectiveV2IntegrityError(
                "incremental history transaction cardinality mismatch"
            )
        if self.pending_event is not None:
            if (
                self.pending_event.ordinal != self.next_expected_ordinal
                or self.pending_event.predecessor_continuation_digest
                != self._incremental_predecessor_continuation_digest()
            ):
                raise ProspectiveV2IntegrityError(
                    "incremental pending predecessor disagreement"
                )

    def verify_full_history_boundary(self, boundary: str) -> None:
        """Reconstruct accepted REAL history and compare incremental state."""

        if not boundary:
            raise ValueError("full history boundary name is required")
        try:
            self._verify_invariants()
            if self._history_validation_mode != HISTORY_VALIDATION_LEGACY:
                self._verify_ledger_derived_state()
            self._verify_deferred_specialization_requests(
                reconstruct_evidence=True
            )
        except ProspectiveV2IntegrityError as exc:
            raise ProspectiveV2IntegrityError(
                f"full history boundary {boundary} failed: {exc}"
            ) from exc

    def _verify_deferred_specialization_requests(
        self, *, reconstruct_evidence: bool = False
    ) -> None:
        """Validate request bindings; reconstruct evidence at boundaries."""

        requested_parents: list[str] = []
        references = self.accepted_real_references
        for request_id, request in sorted(self.deferred_requests.items()):
            if request.request_id != request_id or request_id != _sha({
                "kind": "V2_GRAPH_SPECIALIZATION_REQUEST_V7",
                "request": request.identity_manifest(),
            }):
                raise ProspectiveV2IntegrityError(
                    "specialization request identity mismatch"
                )
            state = self.states.get(request.parent_cell_id)
            if state is None:
                raise ProspectiveV2IntegrityError(
                    "specialization request parent is absent"
                )
            hypothesis = state.hypothesis
            if (
                request.specialization_mode != self.specialization_mode
                or request.source_generation > self.current_generation
                or hypothesis.source_generation > request.source_generation
                or hypothesis.hypothesis_digest
                != request.parent_hypothesis_digest
                or hypothesis.polarity is not request.fixed_polarity
                or hypothesis.specialization_depth != 0
                or hypothesis.dormant_origin
                is not DormantOrigin.MIXED_OUTCOME_SHADOW
                or request.parent_discovery_receipt_ids
                != hypothesis.discovery_receipt_ids
                or request.parent_discovery_support_receipt_ids
                != hypothesis.discovery_support_receipt_ids
                or request.transitive_ancestor_receipt_ids
                != hypothesis.transitive_ancestor_receipt_ids
            ):
                raise ProspectiveV2IntegrityError(
                    "specialization request parent contract mismatch"
                )

            emission_reference = references.get(
                request.request_emission_receipt_id
            )
            contradiction_reference = references.get(
                request.contradiction_receipt_id
            )
            emission_receipt = self.consumed_receipts.get(
                request.request_emission_receipt_id
            )
            emission = self.emissions.get(
                request.request_emission_receipt_id
            )
            if (
                emission_reference is None
                or contradiction_reference is None
                or emission_receipt is None
                or emission is None
                or emission_reference.ordinal
                != request.request_emission_ordinal
                or contradiction_reference.ordinal
                != request.contradiction_ordinal
                or emission_reference.source_generation
                != request.source_generation
                or request.parent_cell_id
                not in emission.graph_specialization_request_ids
                or request.request_id
                not in emission.request_queue_appended_ids
            ):
                raise ProspectiveV2IntegrityError(
                    "specialization request emission contract mismatch"
                )
            expected_outcome = (
                request.fixed_polarity is AvailabilityState.AVAILABLE
            )
            if contradiction_reference.observed_outcome is expected_outcome:
                raise ProspectiveV2IntegrityError(
                    "specialization anchor is not contradictory"
                )
            if request.request_basis is RequestBasis.CERTIFIED_REVOCATION:
                if (
                    not request.graph_revocation_confirmed
                    or request.parent_cell_id
                    not in emission.graph_revocation_ids
                    or contradiction_reference != emission_reference
                ):
                    raise ProspectiveV2IntegrityError(
                        "certified-revocation request basis mismatch"
                    )
            elif (
                request.graph_revocation_confirmed
                or request.parent_cell_id in emission.graph_revocation_ids
            ):
                raise ProspectiveV2IntegrityError(
                    "uncertified mixed-evidence request basis mismatch"
                )
            if (
                dict(emission.eligible_ids_by_request).get(
                    request.parent_cell_id
                ) != request.eligible_base_ids
                or dict(emission.candidate_terminal_states).get(
                    request.parent_cell_id
                ) != request.candidate_terminals
            ):
                raise ProspectiveV2IntegrityError(
                    "specialization request differs from graph emission"
                )
            requested_parents.append(request.parent_cell_id)
            if not reconstruct_evidence:
                continue

            try:
                prospective_support_ids = tuple(sorted(
                    receipt_id for receipt_id in state.support_receipt_ids
                    if references[receipt_id].ordinal
                    <= request.request_emission_ordinal
                ))
                contradiction_ids = tuple(sorted(
                    receipt_id
                    for receipt_id in state.contradiction_receipt_ids
                    if references[receipt_id].ordinal
                    <= request.request_emission_ordinal
                ))
                all_support_ids = tuple(sorted({
                    *request.parent_discovery_support_receipt_ids,
                    *prospective_support_ids,
                }))
                all_support_references = tuple(
                    references[item] for item in all_support_ids
                )
            except KeyError as exc:
                raise ProspectiveV2IntegrityError(
                    "specialization request references unknown REAL evidence"
                ) from exc
            if (
                prospective_support_ids
                != request.parent_prospective_support_receipt_ids
                or not contradiction_ids
                or any(
                    reference.observed_outcome is not expected_outcome
                    for reference in all_support_references
                )
            ):
                raise ProspectiveV2IntegrityError(
                    "specialization request support contract mismatch"
                )
            earliest_contradiction = min(
                (references[item] for item in contradiction_ids),
                key=lambda item: (item.ordinal, item.receipt_id),
            )
            if earliest_contradiction != contradiction_reference:
                raise ProspectiveV2IntegrityError(
                    "specialization request did not anchor its earliest "
                    "contradiction"
                )

            transition_at_emission = tuple(
                row for row in state.transition_rows
                if row.get("receipt_id")
                == request.request_emission_receipt_id
            )
            if request.request_basis is RequestBasis.CERTIFIED_REVOCATION:
                if (
                    not request.graph_revocation_confirmed
                    or request.parent_cell_id
                    not in emission.graph_revocation_ids
                    or transition_at_emission != ({
                        "transition": "GRAPH_LOCAL_REVOCATION",
                        "receipt_id": request.request_emission_receipt_id,
                        "ordinal": request.request_emission_ordinal,
                        "pending_token": emission_receipt.pending_token,
                    },)
                    or contradiction_reference != emission_reference
                ):
                    raise ProspectiveV2IntegrityError(
                        "certified-revocation request basis mismatch"
                    )
            else:
                evidence_prefix = sorted(
                    (
                        (references[item].ordinal, item, True)
                        for item in prospective_support_ids
                    ),
                    key=lambda row: (row[0], row[1]),
                ) + sorted(
                    (
                        (references[item].ordinal, item, False)
                        for item in contradiction_ids
                    ),
                    key=lambda row: (row[0], row[1]),
                )
                evidence_prefix.sort(key=lambda row: (row[0], row[1]))
                successes = 0
                contradictions = 0
                first_mixed_ordinal: int | None = None
                for ordinal, _receipt_id, supports in evidence_prefix:
                    successes += int(supports)
                    contradictions += int(not supports)
                    if successes >= MIN_SUPPORT and contradictions >= 1:
                        first_mixed_ordinal = ordinal
                        break
                transaction = self.event_transactions.get(
                    emission_receipt.pending_token, {}
                )
                classification = transaction.get(
                    "pre_outcome_classification", {}
                )
                committed_ids = {
                    *classification.get("available_cell_ids", ()),
                    *classification.get("refuted_cell_ids", ()),
                }
                if (
                    request.graph_revocation_confirmed
                    or request.parent_cell_id in emission.graph_revocation_ids
                    or transition_at_emission
                    or first_mixed_ordinal
                    != request.request_emission_ordinal
                    or state.prospectively_certified
                    or request.parent_cell_id in committed_ids
                ):
                    raise ProspectiveV2IntegrityError(
                        "uncertified mixed-evidence request basis mismatch"
                    )

            implied_ids = _recursively_implied_signal_ids(
                request.parent_cell_id, self.states
            )
            vocabulary = tuple(sorted({
                identity
                for reference in all_support_references
                for identity in reference.ordered_signal_identities
                if _specialization_identity_role_permitted(
                    reference, identity
                )
            }))
            inspected_ids = tuple(sorted({
                *all_support_ids,
                request.contradiction_receipt_id,
                request.request_emission_receipt_id,
            }))
            expected_candidates: list[
                SpecializationCandidateTerminalState
            ] = []
            for identity in vocabulary:
                occurrence_references = tuple(
                    reference for reference in all_support_references
                    if identity in reference.ordered_signal_identities
                )
                supporting_ids = tuple(sorted(
                    item.receipt_id for item in occurrence_references
                ))
                supporting_physical_ids = tuple(sorted(
                    item.stable_physical_interaction_id
                    for item in occurrence_references
                ))
                role_permitted = any(
                    _specialization_identity_role_permitted(
                        reference, identity
                    )
                    for reference in occurrence_references
                )
                present_in_anchor = (
                    identity
                    in contradiction_reference.ordered_signal_identities
                )
                confirmed = bool(
                    role_permitted
                    and identity not in implied_ids
                    and len(supporting_ids) >= MIN_SUPPORT
                    and (
                        self.specialization_mode
                        is SpecializationMode.COUNTEREXAMPLE_BLIND
                        or (
                            self.specialization_mode
                            is SpecializationMode.LOCAL_CONTRAST
                            and not present_in_anchor
                        )
                    )
                )
                token = hashlib.sha256(
                    f"{request.parent_cell_id}|{identity}".encode("utf-8")
                ).hexdigest()[:16]
                expected_candidates.append(
                    SpecializationCandidateTerminalState(
                        identity=identity,
                        node_id=(
                            "v2:specialization_eligibility:" + token
                        ),
                        role_permitted=role_permitted,
                        recursively_implied_by_parent=(
                            identity in implied_ids
                        ),
                        supporting_receipt_ids=supporting_ids,
                        supporting_stable_physical_interaction_ids=(
                            supporting_physical_ids
                        ),
                        supporting_occurrence_count=len(supporting_ids),
                        present_in_triggering_contradiction=(
                            present_in_anchor
                        ),
                        specialization_mode=self.specialization_mode,
                        confirmed=confirmed,
                        node_state=(
                            NodeState.CONFIRMED.name
                            if confirmed else NodeState.FAILED.name
                        ),
                        inspected_receipt_ids=inspected_ids,
                    )
                )
            if tuple(expected_candidates) != request.candidate_terminals:
                raise ProspectiveV2IntegrityError(
                    "specialization candidate evidence contract mismatch"
                )
            if any(
                references[item].ordinal
                > request.request_emission_ordinal
                for item in inspected_ids
            ):
                raise ProspectiveV2IntegrityError(
                    "specialization candidate read beyond request emission"
                )
        if (
            len(requested_parents) != len(set(requested_parents))
            or tuple(sorted(requested_parents))
            != self.lifetime_requested_parent_ids
        ):
            raise ProspectiveV2IntegrityError(
                "lifetime specialization request ledger mismatch"
            )

    def _verify_invariants(
        self,
        *,
        allow_unregistered: bool = False,
        frozen_base_continuation_digest: str | None = None,
    ) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ProspectiveV2IntegrityError("unsupported V2 schema")
        if (
            isinstance(self.specialization_genome_seed, bool)
            or not isinstance(self.specialization_genome_seed, int)
            or self.specialization_genome_seed < 0
            or self.specialization_genome_seed
            != self.base.learning_config.genome_seed
        ):
            raise ProspectiveV2IntegrityError(
                "specialization genome seed differs from frozen organism"
            )
        try:
            self.base.validate_canonical_evidence_ledger()
        except RuntimeError as exc:
            raise ProspectiveV2IntegrityError(str(exc)) from exc
        self.base.validate_prospective_discovery_epoch()
        epoch = self.base.envelope.nomination_epoch
        assert epoch is not None
        expected_prefix_fingerprints = (
            _validated_prefix_physical_fingerprints(self.base)
        )
        if (
            self.discovery_prefix_physical_fingerprints
            != expected_prefix_fingerprints
            or self.discovery_prefix_physical_fingerprint_digest
            != _sha(list(expected_prefix_fingerprints))
        ):
            raise ProspectiveV2IntegrityError(
                "discovery-prefix physical-fingerprint identity mismatch"
            )
        registered = set(self.states)
        if set(self.structural_invariants) != registered:
            raise ProspectiveV2IntegrityError(
                "live invariant/state identity mismatch"
            )
        for cell_id in sorted(registered):
            hypothesis = self.states[cell_id].hypothesis
            if hypothesis.source_generation > 0:
                invariant = self.structural_invariants[cell_id]
                if (
                    hypothesis.members != invariant.members
                    or hypothesis.polarity != invariant.polarity
                    or hypothesis.lineage_parent_id
                    != invariant.lineage_parent_id
                    or hypothesis.specialization_depth
                    != invariant.specialization_depth
                    or hypothesis.structural_state
                    != invariant.structural_state
                    or hypothesis.dormant_origin
                    != invariant.dormant_origin
                    or hypothesis.hypothesis_digest
                    != invariant.immutable_hypothesis_digest
                    or hypothesis.parent_hypothesis_digest
                    != invariant.parent_hypothesis_digest
                ):
                    raise ProspectiveV2IntegrityError(
                        f"successor structural invariant mutation: {cell_id}"
                    )
                escrow = self.deferred_child_escrows.get(cell_id)
                if not isinstance(escrow, NominationEscrow):
                    raise ProspectiveV2IntegrityError(
                        f"successor child lacks V3 escrow: {cell_id}"
                    )
                if (
                    escrow.escrow_schema_version != NOMINATION_ESCROW_V3
                    or hypothesis.nomination_escrow_digest
                    != escrow.escrow_digest
                    or hypothesis.nomination_read_sets
                    != escrow.categorized_reads
                    or hypothesis.discovery_exclusion_receipt_ids
                    != escrow.discovery_exclusion_receipt_ids
                    or hypothesis.parent_hypothesis_digest
                    != escrow.parent_hypothesis_digest
                ):
                    raise ProspectiveV2IntegrityError(
                        f"successor child escrow mismatch: {cell_id}"
                    )
                continue
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
                    or hypothesis.birth_frontier
                    != escrow.certification_frontier
                    or hypothesis.nomination_operation != escrow.operation
                    or hypothesis.triggering_receipt_id
                    != escrow.triggering_receipt_id
                    or hypothesis.graph_request_root_state
                    != escrow.graph_request_root_state
                    or hypothesis.graph_request_terminal_state
                    != escrow.graph_request_terminal_state
                    or hypothesis.considered_context_ids
                    != escrow.considered_context_ids
                    or hypothesis.selected_context_ids
                    != escrow.selected_context_ids
                    or hypothesis.nomination_read_frontier
                    != escrow.nomination_read_frontier
                    or hypothesis.certification_frontier
                    != escrow.certification_frontier
                    or hypothesis.nomination_escrow_digest
                    != escrow.escrow_digest
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
        if self.authority_topology != _executed_authority_topology_manifest(self.states):
            raise ProspectiveV2IntegrityError(
                "authority topology identity mismatch"
            )
        successor_ids = {
            cell_id for cell_id, state in self.states.items()
            if state.hypothesis.source_generation > 0
        }
        if epoch.nomination_closed and not successor_ids:
            expected_identity = self._build_experimental_identity(
                base_continuation_digest=(
                    frozen_base_continuation_digest
                )
            )
            if self.experimental_identity != expected_identity:
                raise ProspectiveV2IntegrityError(
                    "experimental initialization identity mismatch"
                )
        elif not epoch.nomination_closed and self.experimental_identity is not None:
            raise ProspectiveV2IntegrityError(
                "open nomination carries experimental identity"
            )

        if len(self.request_queue) > REQUEST_QUEUE_CAPACITY:
            raise ProspectiveV2IntegrityError("request queue capacity exceeded")
        if len(successor_ids) > DORMANT_SPECIALIZATION_CHILD_CAPACITY:
            raise ProspectiveV2IntegrityError(
                "dormant specialization-child capacity exceeded"
            )
        if set(self.deferred_requests) != set(self.request_queue):
            raise ProspectiveV2IntegrityError(
                "deferred request/queue identity mismatch"
            )
        ordered_queue = tuple(sorted(
            self.request_queue,
            key=lambda request_id: (
                self.deferred_requests[
                    request_id
                ].request_emission_ordinal,
                self.deferred_requests[request_id].parent_cell_id,
            ),
        ))
        if self.request_queue != ordered_queue:
            raise ProspectiveV2IntegrityError("request queue is not canonical")
        self._verify_deferred_specialization_requests()
        if set(self.request_consumptions).difference(self.request_queue):
            raise ProspectiveV2IntegrityError(
                "consumption exists outside request queue"
            )
        consumed_member_tuples: set[tuple[str, ...]] = set()
        for request_id, consumption in sorted(
            self.request_consumptions.items()
        ):
            request = self.deferred_requests[request_id]
            generation_ids = tuple(
                item for item in self.request_queue
                if self.deferred_requests[item].source_generation
                == request.source_generation
            )
            if (
                consumption.request_id != request_id
                or consumption.attempt_ordinal
                != generation_ids.index(request_id)
                or consumption.genome_seed
                != self.specialization_genome_seed
                or consumption.genome_call_count != 1
            ):
                raise ProspectiveV2IntegrityError(
                    "structural request consumption identity mismatch"
                )
            if consumption.selected_members:
                if consumption.selected_members in consumed_member_tuples:
                    if consumption.disposition != "REJECTED_DUPLICATE_PATTERN":
                        raise ProspectiveV2IntegrityError(
                            "repeated specialization tuple was not rejected"
                        )
                else:
                    consumed_member_tuples.add(
                        consumption.selected_members
                    )
        current_consumed = tuple(
            request_id for request_id in self.sealed_request_ids
            if request_id in self.request_consumptions
        )
        if current_consumed != self.sealed_request_ids[
            :len(current_consumed)
        ]:
            raise ProspectiveV2IntegrityError(
                "sealed requests were skipped or reordered"
            )
        if set(self.deferred_child_births).difference(
            self.request_consumptions
        ):
            raise ProspectiveV2IntegrityError(
                "child birth exists without consumed request"
            )
        if self.specialization_mode is SpecializationMode.DISCONNECTED and (
            self.request_queue or self.deferred_requests
        ):
            raise ProspectiveV2IntegrityError(
                "disconnected mode contains a dummy request"
            )
        if any(
            boundary.specialization_genome_seed
            != self.specialization_genome_seed
            for boundary in self.generation_boundaries
        ):
            raise ProspectiveV2IntegrityError(
                "generation boundary genome seed mismatch"
            )
        stable_ids = [
            item.stable_physical_interaction_id
            for item in self.accepted_real_references.values()
        ]
        if len(stable_ids) != len(set(stable_ids)):
            raise ProspectiveV2IntegrityError(
                "accepted REAL physical identity replay"
            )

        if self._history_validation_mode == HISTORY_VALIDATION_LEGACY:
            self._verify_ledger_derived_state()
        else:
            self._verify_incremental_history_state()

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
        if (
            receipt.environment_outcome_terminal_identity
            != self.base.learning_config.completion_terminal_identity
        ):
            raise ProspectiveV2IntegrityError(
                "environment outcome terminal mismatch"
            )
        fingerprint = _interaction_fingerprint(
            source_organism_identity=receipt.source_organism_identity,
            source_state_identity=receipt.source_state_identity,
            predecessor_fen=receipt.predecessor_fen,
            trace=receipt.trace,
            actuation=receipt.selected_actuation,
            successor_fen=receipt.successor_fen,
            environment_outcome_terminal_identity=(
                receipt.environment_outcome_terminal_identity
            ),
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
            "environment_outcome_terminal_identity": (
                receipt.environment_outcome_terminal_identity
            ),
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
        historical_references = {
            item.receipt_id: item
            for item in self._historical_real_references(self.base)
        }
        replay_references = dict(historical_references)
        replay_requests: dict[str, DeferredSpecializationRequest] = {}
        replay_queue: list[str] = []
        replay_lifetime: set[str] = set()
        if ordered and self.incremental_history_state is None:
            raise ProspectiveV2IntegrityError(
                "incremental history missing for accepted REAL events"
            )
        replay_history = (
            self._new_incremental_history_state()
            if self.incremental_history_state is not None
            else None
        )
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
            if (
                receipt.interaction_fingerprint
                in self.discovery_prefix_physical_fingerprints
            ):
                raise ProspectiveV2IntegrityError(
                    "discovery-evidence replay in certification ledger"
                )
            if receipt.interaction_fingerprint in expected_fingerprints:
                raise ProspectiveV2IntegrityError(
                    "duplicate accepted physical interaction fingerprint"
                )
            transaction = self.event_transactions.get(receipt.pending_token)
            if not isinstance(transaction, Mapping):
                raise ProspectiveV2IntegrityError(
                    "accepted receipt lacks pre-outcome transaction"
                )
            self._validate_replayed_receipt(receipt, transaction)
            reference = self.accepted_real_references.get(receipt.receipt_id)
            if reference is None:
                raise ProspectiveV2IntegrityError(
                    "accepted REAL reference is absent"
                )
            if reference != self._reference_from_v2_receipt(
                receipt, source_generation=reference.source_generation
            ):
                raise ProspectiveV2IntegrityError(
                    "accepted REAL reference differs from receipt"
                )
            assert replay_history is not None
            predecessor_digest = (
                self._incremental_predecessor_digest_from_parts(
                    history=replay_history,
                    states=derived,
                    generation=reference.source_generation,
                    next_ordinal=receipt.ordinal,
                    request_ids=tuple(sorted(
                        replay_queue,
                        key=lambda request_id: (
                            replay_requests[
                                request_id
                            ].request_emission_ordinal,
                            replay_requests[
                                request_id
                            ].parent_cell_id,
                        ),
                    )),
                    lifetime_requested_parent_ids=tuple(sorted(
                        replay_lifetime
                    )),
                )
            )
            if transaction.get(
                "predecessor_continuation_digest"
            ) != predecessor_digest:
                raise ProspectiveV2IntegrityError(
                    "incremental history predecessor disagreement "
                    f"at ordinal {receipt.ordinal}"
                )
            active_derived = {
                cell_id: state for cell_id, state in derived.items()
                if state.hypothesis.source_generation
                <= reference.source_generation
            }
            pre_graph = _run_authority_graph(
                active_derived,
                AuthorityMeasurementSnapshot(receipt.trace, None),
                accepted_real_references=replay_references,
                specialization_mode=self.specialization_mode,
                lifetime_requested_parent_ids=tuple(sorted(replay_lifetime)),
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
                active_derived, pre_graph
            )
            if classification.to_manifest() != transaction.get(
                "pre_outcome_classification"
            ):
                raise ProspectiveV2IntegrityError(
                    "replayed pre-outcome classification mismatch"
                )
            prequential_false_ids = (
                self._prequential_false_authority_ids(
                    active_derived,
                    classification,
                    matching,
                    receipt.observed_outcome,
                )
            )
            if not transaction.get("structure_invariant_digest"):
                raise ProspectiveV2IntegrityError(
                    "replayed structure invariant is absent"
                )
            graph = _run_authority_graph(
                active_derived,
                AuthorityMeasurementSnapshot(receipt.trace, receipt),
                accepted_real_references=replay_references,
                current_real_reference=reference,
                specialization_mode=self.specialization_mode,
                lifetime_requested_parent_ids=tuple(sorted(replay_lifetime)),
            )
            supporting = graph["support"]
            contradictions = graph["contradiction"]
            if set(supporting).union(contradictions) != set(matching):
                raise ProspectiveV2IntegrityError(
                    "replayed lifecycle omitted commitment"
                )
            request_rows = dict(graph["specialization_candidate_states"])
            requests = tuple(
                self._request_from_graph_state(
                    parent_cell_id=parent_id,
                    state=active_derived[parent_id],
                    receipt=receipt,
                    current_reference=reference,
                    accepted_real_references=replay_references,
                    current_reference_validated=True,
                    source_generation=reference.source_generation,
                    specialization_mode=self.specialization_mode,
                    already_requested=parent_id in replay_lifetime,
                    graph_revocation_confirmed=(
                        parent_id in graph["revocation"]
                    ),
                    candidate_rows=request_rows.get(parent_id, ()),
                )
                for parent_id in graph["specialization_request"]
            )
            for cell_id in matching:
                state = active_derived[cell_id]
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
            for request in requests:
                replay_requests[request.request_id] = request
                replay_queue.append(request.request_id)
                replay_lifetime.add(request.parent_cell_id)
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
                graph_specialization_request_ids=tuple(
                    graph["specialization_request"]
                ),
                eligible_ids_by_request=tuple(
                    (item.parent_cell_id, item.eligible_base_ids)
                    for item in requests
                ),
                candidate_terminal_states=tuple(
                    (item.parent_cell_id, item.candidate_terminals)
                    for item in requests
                ),
                request_queue_appended_ids=tuple(
                    item.request_id for item in requests
                ),
                prequential_false_authority_ids=(
                    prequential_false_ids
                ),
            )
            replay_references[reference.receipt_id] = reference
            expected_tokens.add(receipt.pending_token)
            expected_fingerprints[
                receipt.interaction_fingerprint
            ] = receipt.receipt_id
            replay_history = self._next_incremental_history_state(
                replay_history,
                receipt=receipt,
                transaction=transaction,
                reference=reference,
                emission=expected_emissions[receipt.receipt_id],
            )
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
        if self.prospective_physical_fingerprints != expected_fingerprints:
            raise ProspectiveV2IntegrityError(
                "prospective physical-fingerprint ledger mismatch"
            )
        if self.accepted_real_references != {
            **historical_references,
            **{
                receipt.receipt_id: self._reference_from_v2_receipt(
                    receipt,
                    source_generation=self.accepted_real_references[
                        receipt.receipt_id
                    ].source_generation,
                )
                for receipt in ordered
            },
        }:
            raise ProspectiveV2IntegrityError(
                "accepted REAL reference ledger mismatch"
            )
        if self.deferred_requests != replay_requests:
            raise ProspectiveV2IntegrityError(
                "deferred request ledger differs from graph replay"
            )
        expected_queue = tuple(sorted(
            replay_queue,
            key=lambda request_id: (
                replay_requests[request_id].request_emission_ordinal,
                replay_requests[request_id].parent_cell_id,
            ),
        ))
        if self.request_queue != expected_queue:
            raise ProspectiveV2IntegrityError(
                "request queue differs from graph replay"
            )
        if self.lifetime_requested_parent_ids != tuple(sorted(replay_lifetime)):
            raise ProspectiveV2IntegrityError(
                "lifetime request ledger differs from graph replay"
            )
        if replay_history != self.incremental_history_state:
            raise ProspectiveV2IntegrityError(
                "incremental history disagreement with complete reconstruction"
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
        current_real_reference: AcceptedRealReference | None = None,
    ) -> dict[str, Any]:
        if receipt is not None and current_real_reference is None:
            current_real_reference = self._reference_from_v2_receipt(receipt)
        return _run_authority_graph(
            self.states,
            AuthorityMeasurementSnapshot(trace, receipt),
            accepted_real_references=self.accepted_real_references,
            current_real_reference=current_real_reference,
            specialization_mode=self.specialization_mode,
            lifetime_requested_parent_ids=(
                self.lifetime_requested_parent_ids
            ),
        )

    def _reference_from_v2_receipt(
        self,
        receipt: V2GroundedReceipt,
        *,
        source_generation: int | None = None,
    ) -> AcceptedRealReference:
        return AcceptedRealReference(
            receipt_id=receipt.receipt_id,
            ordinal=receipt.ordinal,
            stable_physical_interaction_id=(
                receipt.interaction_fingerprint
            ),
            trace_digest=receipt.trace.digest(),
            typed_signal_digest=_sha([
                asdict(item) for item in receipt.trace.terminal_signals
            ]),
            observed_outcome=receipt.observed_outcome,
            source_generation=(
                self.current_generation
                if source_generation is None
                else int(source_generation)
            ),
            ordered_signal_identities=(
                receipt.trace.ordered_signal_identities
            ),
            typed_signal_roles=tuple(sorted(
                (item.identity, item.role)
                for item in receipt.trace.terminal_signals
            )),
        )

    @staticmethod
    def _request_from_graph_state(
        *,
        parent_cell_id: str,
        state: ProspectiveAuthorityState,
        receipt: V2GroundedReceipt,
        current_reference: AcceptedRealReference,
        accepted_real_references: Mapping[str, AcceptedRealReference],
        current_reference_validated: bool,
        source_generation: int,
        specialization_mode: SpecializationMode,
        already_requested: bool,
        graph_revocation_confirmed: bool,
        candidate_rows: tuple[SpecializationCandidateTerminalState, ...],
    ) -> DeferredSpecializationRequest:
        hypothesis = state.hypothesis
        references = dict(accepted_real_references)
        prior = references.get(current_reference.receipt_id)
        if prior is not None and prior != current_reference:
            raise ProspectiveV2IntegrityError(
                "request builder REAL reference collision"
            )
        references[current_reference.receipt_id] = current_reference
        trigger = _derive_specialization_request_trigger(
            state,
            receipt,
            current_reference,
            references,
            matched=True,
            specialization_mode=specialization_mode,
            already_requested=already_requested,
            current_reference_validated=current_reference_validated,
        )
        if trigger is None:
            raise ProspectiveV2IntegrityError(
                "request builder lacks a causal trigger"
            )
        expected_revocation = (
            trigger.basis is RequestBasis.CERTIFIED_REVOCATION
        )
        if graph_revocation_confirmed is not expected_revocation:
            raise ProspectiveV2IntegrityError(
                "request basis differs from graph revocation"
            )
        if current_reference.source_generation != source_generation:
            raise ProspectiveV2IntegrityError(
                "request generation differs from emission reference"
            )
        draft = DeferredSpecializationRequest(
            request_id="UNBOUND_V7_SPECIALIZATION_REQUEST",
            source_generation=source_generation,
            parent_cell_id=parent_cell_id,
            parent_hypothesis_digest=hypothesis.hypothesis_digest,
            fixed_polarity=hypothesis.polarity,
            request_basis=trigger.basis,
            request_emission_receipt_id=receipt.receipt_id,
            request_emission_ordinal=receipt.ordinal,
            contradiction_receipt_id=(
                trigger.contradiction_reference.receipt_id
            ),
            contradiction_ordinal=trigger.contradiction_reference.ordinal,
            specialization_mode=specialization_mode,
            parent_discovery_receipt_ids=(
                hypothesis.discovery_receipt_ids
            ),
            parent_discovery_support_receipt_ids=(
                hypothesis.discovery_support_receipt_ids
            ),
            parent_prospective_support_receipt_ids=(
                trigger.parent_prospective_support_receipt_ids
            ),
            transitive_ancestor_receipt_ids=(
                hypothesis.transitive_ancestor_receipt_ids
            ),
            candidate_terminals=candidate_rows,
            graph_revocation_confirmed=graph_revocation_confirmed,
            graph_request_confirmed=True,
        )
        return replace(draft, request_id=_sha({
            "kind": "V2_GRAPH_SPECIALIZATION_REQUEST_V7",
            "request": draft.identity_manifest(),
        }))

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

    @staticmethod
    def _prequential_false_authority_ids(
        states: Mapping[str, ProspectiveAuthorityState],
        classification: EnvelopeClassification,
        matching_cell_ids: Sequence[str],
        observed_outcome: bool,
    ) -> tuple[str, ...]:
        """Cells whose committed pre-outcome decision was contradicted."""

        committed = {
            *classification.available_cell_ids,
            *classification.refuted_cell_ids,
        }
        return tuple(sorted(
            cell_id for cell_id in matching_cell_ids
            if (
                cell_id in committed
                and states[cell_id].prospectively_certified
                and observed_outcome
                != (
                    states[cell_id].hypothesis.polarity
                    is AvailabilityState.AVAILABLE
                )
            )
        ))

    def frame_session(self) -> NativeV2FrameSession:
        """Open one non-serializable frozen-R0 execution session."""

        self._verify_invariants()
        return NativeV2FrameSession(self)

    def open_real_event(
        self,
        frame: FrameContext,
        *,
        frame_session: NativeV2FrameSession | None = None,
    ) -> tuple[PendingRealEvent, GraphSignalTrace]:
        if frame_session is not None:
            frame_session._require_open(self)
        self._verify_invariants(
            frozen_base_continuation_digest=(
                None
                if frame_session is None
                else frame_session.base_continuation_digest
            )
        )
        if self.generation_phase is not GenerationPhase.PROSPECTIVE_OPEN:
            raise ProspectiveV2IntegrityError(
                "REAL event outside PROSPECTIVE_OPEN"
            )
        if self.evaluation_sealed:
            raise ProspectiveV2IntegrityError(
                "sealed evaluation cannot open a REAL transaction"
            )
        epoch = self.base.envelope.nomination_epoch
        if epoch is None or not epoch.nomination_closed:
            raise ProspectiveV2IntegrityError(
                "first certification event requires closed nomination"
            )
        self._ensure_incremental_history_initialized()
        before = (
            self.continuation_digest()
            if frame_session is None
            else frame_session.continuation_digest(self)
        )
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
        if frame_session is None:
            actuation, trace = self.base.r0.emit_action_with_trace(frame)
        else:
            actuation, trace = (
                frame_session.r0_session.emit_action_with_trace(frame)
            )
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
        predecessor_continuation_digest = (
            self._incremental_predecessor_continuation_digest()
        )
        token = _sha({
            "implementation": IMPLEMENTATION_IDENTITY,
            "ordinal": self.next_expected_ordinal,
            "frame_id": frame.frame_id,
            "trace": trace.digest(),
            "matching": list(matching),
            "structure_invariant_digest": structure_digest,
        })
        environment_terminal_identity = (
            self.base.learning_config.completion_terminal_identity
        )
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
            predecessor_continuation_digest=(
                predecessor_continuation_digest
            ),
            pending_token=token,
            outcome_terminal_identity=OUTCOME_TERMINAL_IDENTITY,
            environment_outcome_terminal_identity=(
                environment_terminal_identity
            ),
        )
        after = (
            self.continuation_digest()
            if frame_session is None
            else frame_session.continuation_digest(self)
        )
        if after != before:
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
            environment_outcome_terminal_identity=(
                pending.environment_outcome_terminal_identity
            ),
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
            "environment_outcome_terminal_identity": (
                pending.environment_outcome_terminal_identity
            ),
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
            environment_outcome_terminal_identity=(
                pending.environment_outcome_terminal_identity
            ),
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
        if (
            pending.predecessor_continuation_digest
            != self._incremental_predecessor_continuation_digest()
        ):
            raise ProspectiveV2IntegrityError(
                "incremental pending predecessor disagreement"
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
        if (
            receipt.environment_outcome_terminal_identity
            != pending.environment_outcome_terminal_identity
            or receipt.environment_outcome_terminal_identity
            != self.base.learning_config.completion_terminal_identity
        ):
            raise ProspectiveV2IntegrityError(
                "environment outcome terminal mismatch"
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
            environment_outcome_terminal_identity=(
                receipt.environment_outcome_terminal_identity
            ),
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
        self,
        receipt: V2GroundedReceipt,
        *,
        frame_session: NativeV2FrameSession | None = None,
    ) -> V2CertificationEmission:
        """Atomically consume one REAL result; never materialize a child."""

        frozen_r0 = self.base.r0
        frozen_r0_guard = (
            frozen_r0.inference_guard_identity()
            if frame_session is None
            else None
        )
        if frame_session is not None:
            frame_session._require_open(self)
        candidate = copy.deepcopy(self, {id(frozen_r0): frozen_r0})
        if candidate.base.r0 is not frozen_r0:
            raise ProspectiveV2IntegrityError(
                "REAL transaction failed to share the frozen R0 source"
            )
        try:
            result = candidate._consume_in_place(
                receipt,
                frozen_base_continuation_digest=(
                    None
                    if frame_session is None
                    else frame_session.base_continuation_digest
                ),
            )
        finally:
            if (
                frozen_r0_guard is not None
                and frozen_r0.inference_guard_identity() != frozen_r0_guard
            ):
                raise ProspectiveV2IntegrityError(
                    "REAL transaction mutated its shared frozen R0 source"
                )
        self.__dict__.clear()
        self.__dict__.update(candidate.__dict__)
        return result

    def _consume_in_place(
        self,
        receipt: V2GroundedReceipt,
        *,
        frozen_base_continuation_digest: str | None = None,
    ) -> V2CertificationEmission:
        self._verify_invariants(
            frozen_base_continuation_digest=(
                frozen_base_continuation_digest
            )
        )
        if self.generation_phase is not GenerationPhase.PROSPECTIVE_OPEN:
            raise ProspectiveV2IntegrityError(
                "REAL consumption outside PROSPECTIVE_OPEN"
            )
        if self.evaluation_sealed:
            raise ProspectiveV2IntegrityError(
                "sealed evaluation cannot consume evidence"
            )
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
        if (
            receipt.interaction_fingerprint
            in self.discovery_prefix_physical_fingerprints
        ):
            raise ProspectiveV2IntegrityError(
                "discovery-evidence replay under certification identity"
            )
        known_id = self.prospective_physical_fingerprints.get(
            receipt.interaction_fingerprint
        )
        if known_id is not None:
            raise ProspectiveV2IntegrityError(
                "reminted physical interaction under new receipt identity"
            )
        self._validate_receipt(receipt)
        pending = self.pending_event
        assert pending is not None
        prequential_false_ids = self._prequential_false_authority_ids(
            self.states,
            pending.pre_outcome_classification,
            pending.matching_cell_ids,
            receipt.observed_outcome,
        )
        current_reference = self._reference_from_v2_receipt(receipt)
        graph = self._graph_measure(
            receipt.trace, receipt, current_reference
        )
        if graph["commitment"] != pending.matching_cell_ids:
            raise ProspectiveV2IntegrityError(
                "consumption commitment differs from pre-outcome commitment"
            )
        supporting = graph["support"]
        contradictions = graph["contradiction"]
        supporting_set = set(supporting)
        contradiction_set = set(contradictions)
        matching_set = set(pending.matching_cell_ids)
        if supporting_set.intersection(contradiction_set):
            raise ProspectiveV2IntegrityError(
                "support/contradiction overlap"
            )
        if (
            supporting_set.union(contradiction_set) != matching_set
        ):
            raise ProspectiveV2IntegrityError(
                "lifecycle accounting omitted commitment"
            )
        request_parent_ids = tuple(graph["specialization_request"])
        candidate_rows_by_parent = dict(
            graph["specialization_candidate_states"]
        )
        required_request_ids = tuple(sorted(
            cell_id for cell_id in pending.matching_cell_ids
            if _specialization_request_basis(
                self.states[cell_id],
                matched=True,
                post_frontier=bool(
                    receipt.receipt_id
                    and receipt.ordinal > self.states[
                        cell_id
                    ].hypothesis.certification_frontier
                    and receipt.receipt_id not in self.states[
                        cell_id
                    ].hypothesis.discovery_exclusion_receipt_ids
                ),
                supports=cell_id in supporting_set,
                contradicts=cell_id in contradiction_set,
                specialization_mode=self.specialization_mode,
                already_requested=(
                    cell_id in self.lifetime_requested_parent_ids
                ),
            ) is not None
        ))
        if request_parent_ids != required_request_ids:
            raise ProspectiveV2IntegrityError(
                "graph request/trigger contract mismatch"
            )
        new_requests = tuple(
            self._request_from_graph_state(
                parent_cell_id=parent_id,
                state=self.states[parent_id],
                receipt=receipt,
                current_reference=current_reference,
                accepted_real_references=self.accepted_real_references,
                current_reference_validated=True,
                source_generation=self.current_generation,
                specialization_mode=self.specialization_mode,
                already_requested=(
                    parent_id in self.lifetime_requested_parent_ids
                ),
                graph_revocation_confirmed=(
                    parent_id in graph["revocation"]
                ),
                candidate_rows=candidate_rows_by_parent.get(parent_id, ()),
            )
            for parent_id in request_parent_ids
        )
        self._validate_request_append_capacity(new_requests)
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
            graph_specialization_request_ids=request_parent_ids,
            eligible_ids_by_request=tuple(
                (request.parent_cell_id, request.eligible_base_ids)
                for request in new_requests
            ),
            candidate_terminal_states=tuple(
                (request.parent_cell_id, request.candidate_terminals)
                for request in new_requests
            ),
            request_queue_appended_ids=tuple(
                request.request_id for request in new_requests
            ),
            prequential_false_authority_ids=prequential_false_ids,
        )
        self.consumed_receipts[receipt.receipt_id] = receipt
        self.consumed_tokens.add(receipt.pending_token)
        self.prospective_physical_fingerprints[
            receipt.interaction_fingerprint
        ] = receipt.receipt_id
        self.emissions[receipt.receipt_id] = emission
        reference = current_reference
        if reference.receipt_id in self.accepted_real_references:
            raise ProspectiveV2IntegrityError(
                "accepted REAL reference identity collision"
            )
        self.accepted_real_references[reference.receipt_id] = reference
        for request in new_requests:
            if request.request_id in self.deferred_requests:
                raise ProspectiveV2IntegrityError(
                    "deferred request identity collision"
                )
            self.deferred_requests[request.request_id] = request
        self.request_queue = tuple(sorted(
            (*self.request_queue, *(item.request_id for item in new_requests)),
            key=lambda request_id: (
                self.deferred_requests[
                    request_id
                ].request_emission_ordinal,
                self.deferred_requests[request_id].parent_cell_id,
            ),
        ))
        self.lifetime_requested_parent_ids = tuple(sorted({
            *self.lifetime_requested_parent_ids,
            *request_parent_ids,
        }))
        self.next_expected_ordinal += 1
        transaction = {
            **pending.manifest(),
            "state": "CONSUMED",
            "consumed_receipt_id": receipt.receipt_id,
        }
        self.event_transactions[receipt.pending_token] = transaction
        self._append_incremental_history(
            receipt=receipt,
            transaction=transaction,
            reference=reference,
            emission=emission,
        )
        self.pending_event = None
        self._verify_invariants(
            frozen_base_continuation_digest=(
                frozen_base_continuation_digest
            )
        )
        return emission

    def _validate_request_append_capacity(
        self, requests: Sequence[DeferredSpecializationRequest]
    ) -> None:
        if len(self.request_queue) + len(requests) > REQUEST_QUEUE_CAPACITY:
            raise ProspectiveV2IntegrityError(
                "request queue capacity exceeded"
            )

    def _accepted_real_ledger_digest(self) -> str:
        return _sha([
            item.manifest() for item in sorted(
                self.accepted_real_references.values(),
                key=lambda row: (row.ordinal, row.receipt_id),
            )
        ])

    def _request_queue_digest(self, request_ids: Sequence[str]) -> str:
        return _sha([
            self.deferred_requests[item].manifest() for item in request_ids
        ])

    def _parent_decision_history_digest(self) -> str:
        return _sha({
            cell_id: {
                "prospectively_certified": state.prospectively_certified,
                "transition_rows": list(state.transition_rows),
                "support_receipt_ids": list(state.support_receipt_ids),
                "contradiction_receipt_ids": list(
                    state.contradiction_receipt_ids
                ),
            }
            for cell_id, state in sorted(self.states.items())
        })

    def _generation_boundary(
        self,
        *,
        phase: GenerationPhase,
        prior_continuation_digest: str,
        queue_ids: Sequence[str],
    ) -> GenerationBoundary:
        return GenerationBoundary(
            generation=self.current_generation,
            phase=phase,
            event_frontier=self.next_expected_ordinal,
            prior_continuation_digest=prior_continuation_digest,
            accepted_real_ledger_digest=self._accepted_real_ledger_digest(),
            request_queue_digest=self._request_queue_digest(queue_ids),
            structural_epoch_schedule_digest=_sha(
                list(self.structural_epoch_schedule)
            ),
            candidate_manifest_digest=self._candidate_manifest_digest(),
            parent_decision_history_digest=(
                self._parent_decision_history_digest()
            ),
            specialization_genome_seed=self.specialization_genome_seed,
        )

    def seal_prospective_generation(self) -> GenerationBoundary:
        candidate = copy.deepcopy(self)
        result = candidate._seal_prospective_generation_in_place()
        self.__dict__.clear()
        self.__dict__.update(candidate.__dict__)
        return result

    def _seal_prospective_generation_in_place(self) -> GenerationBoundary:
        self._verify_invariants()
        if self.generation_phase is not GenerationPhase.PROSPECTIVE_OPEN:
            raise ProspectiveV2IntegrityError(
                "generation is not prospectively open"
            )
        if self.pending_event is not None or self.evaluation_sealed:
            raise ProspectiveV2IntegrityError(
                "generation cannot seal with open evidence capability"
            )
        if self.current_generation >= len(self.structural_epoch_schedule):
            raise ProspectiveV2IntegrityError(
                "no predetermined structural frontier"
            )
        expected_frontier = self.structural_epoch_schedule[
            self.current_generation
        ]
        if self.next_expected_ordinal != expected_frontier:
            raise ProspectiveV2IntegrityError(
                "structural transition is outside predetermined frontier"
            )
        prior = self.continuation_digest()
        sealed = tuple(
            request_id for request_id in self.request_queue
            if (
                self.deferred_requests[request_id].source_generation
                == self.current_generation
                and request_id not in self.request_consumptions
            )
        )
        self.sealed_request_ids = sealed
        self.sealed_request_queue_digest = self._request_queue_digest(sealed)
        self.generation_phase = GenerationPhase.PROSPECTIVE_SEALED
        boundary = self._generation_boundary(
            phase=self.generation_phase,
            prior_continuation_digest=prior,
            queue_ids=sealed,
        )
        self.generation_boundaries = (*self.generation_boundaries, boundary)
        self._verify_invariants()
        return boundary

    def open_structural_successor(self) -> GenerationBoundary:
        candidate = copy.deepcopy(self)
        result = candidate._open_structural_successor_in_place()
        self.__dict__.clear()
        self.__dict__.update(candidate.__dict__)
        return result

    def _open_structural_successor_in_place(self) -> GenerationBoundary:
        self._verify_invariants()
        if self.generation_phase is not GenerationPhase.PROSPECTIVE_SEALED:
            raise ProspectiveV2IntegrityError(
                "structural successor requires a sealed generation"
            )
        if self.sealed_request_queue_digest != self._request_queue_digest(
            self.sealed_request_ids
        ):
            raise ProspectiveV2IntegrityError("sealed request queue changed")
        prior = self.continuation_digest()
        self.current_generation += 1
        self.generation_phase = GenerationPhase.STRUCTURAL_OPEN
        boundary = self._generation_boundary(
            phase=self.generation_phase,
            prior_continuation_digest=prior,
            queue_ids=self.sealed_request_ids,
        )
        self.generation_boundaries = (*self.generation_boundaries, boundary)
        self._verify_invariants()
        return boundary

    def consume_next_structural_request(
        self,
    ) -> StructuralRequestConsumption:
        """Consume the next sealed request with the organism-frozen genome."""

        candidate = copy.deepcopy(self)
        result = candidate._consume_next_structural_request_in_place()
        self.__dict__.clear()
        self.__dict__.update(candidate.__dict__)
        return result

    def _consume_next_structural_request_in_place(
        self,
    ) -> StructuralRequestConsumption:
        self._verify_invariants()
        if self.generation_phase is not GenerationPhase.STRUCTURAL_OPEN:
            raise ProspectiveV2IntegrityError(
                "request consumption requires STRUCTURAL_OPEN"
            )
        unconsumed = tuple(
            request_id for request_id in self.sealed_request_ids
            if request_id not in self.request_consumptions
        )
        if not unconsumed:
            raise ProspectiveV2IntegrityError(
                "sealed structural request queue is fully consumed"
            )
        request_id = unconsumed[0]
        request = self.deferred_requests[request_id]
        attempt = self.sealed_request_ids.index(request_id)
        genome = CompetenceContextGrowthGenome(
            self.specialization_genome_seed
        )
        proposal = genome.propose_specialization(_GraphSpecializationRequest(
            context_member=f"context:{request.parent_cell_id}",
            eligible_base_ids=request.eligible_base_ids,
            request_ordinal=attempt,
        ))
        disposition = "PENDING_CHILD"
        members: tuple[str, ...] = ()
        child_id: str | None = None
        if proposal is None:
            disposition = "REJECTED_EMPTY_ELIGIBILITY"
        else:
            members = tuple(proposal.members)
            expected_context = f"context:{request.parent_cell_id}"
            if (
                len(members) != 2
                or members[0] != expected_context
                or members[1] not in request.eligible_base_ids
            ):
                raise ProspectiveV2IntegrityError(
                    "genome emitted an ineligible specialization child"
                )
            reserved_members = {
                state.hypothesis.members for state in self.states.values()
            }
            reserved_members.update(
                birth.members for birth in self.deferred_child_births.values()
            )
            reserved_members.update(
                item.selected_members
                for item in self.request_consumptions.values()
                if item.selected_members
            )
            if members in reserved_members:
                disposition = "REJECTED_DUPLICATE_PATTERN"
            elif len(self.deferred_child_births) >= (
                DORMANT_SPECIALIZATION_CHILD_CAPACITY
            ):
                disposition = "REJECTED_CHILD_CAPACITY"
            else:
                child_id = (
                    f"v2_deferred_specialization_"
                    f"g{self.current_generation:02d}_{attempt:04d}"
                )
        consumption = StructuralRequestConsumption(
            request_id=request_id,
            attempt_ordinal=attempt,
            genome_seed=self.specialization_genome_seed,
            genome_call_count=1,
            selected_members=members,
            disposition=disposition,
            child_cell_id=child_id,
        )
        self.request_consumptions[request_id] = consumption
        if child_id is not None:
            self.deferred_child_births[request_id] = DeferredChildBirth(
                request_id=request_id,
                child_cell_id=child_id,
                members=members,
                genome_seed=self.specialization_genome_seed,
                proposal_ordinal=attempt,
                source_generation=self.current_generation,
                disposition="PENDING_MATERIALIZATION",
            )
        self._verify_invariants()
        return consumption

    def _matching_parent_plus_identity_receipts(
        self,
        parent_id: str,
        identity: str,
        visible: Sequence[AcceptedRealReference],
    ) -> tuple[str, ...]:
        descriptors = {
            cell_id: StructuralMatchDescriptor(
                cell_id=cell_id,
                members=state.hypothesis.members,
                structural_state=state.hypothesis.structural_state,
                lineage_parent_id=state.hypothesis.lineage_parent_id,
                specialization_depth=state.hypothesis.specialization_depth,
                nomination_operation=state.hypothesis.nomination_operation,
                parent_hypothesis_digest=(
                    state.hypothesis.parent_hypothesis_digest
                ),
                hypothesis_digest=state.hypothesis.hypothesis_digest,
            )
            for cell_id, state in self.states.items()
        }
        return tuple(sorted(
            item.receipt_id for item in visible
            if (
                identity in item.ordered_signal_identities
                and canonical_structural_pattern_matches(
                    parent_id,
                    descriptors,
                    item.ordered_signal_identities,
                )
            )
        ))

    def materialize_deferred_child(
        self, request_id: str
    ) -> str:
        candidate = copy.deepcopy(self)
        result = candidate._materialize_deferred_child_in_place(request_id)
        self.__dict__.clear()
        self.__dict__.update(candidate.__dict__)
        return result

    def _materialize_deferred_child_in_place(self, request_id: str) -> str:
        self._verify_invariants()
        if self.generation_phase is not GenerationPhase.STRUCTURAL_OPEN:
            raise ProspectiveV2IntegrityError(
                "child birth requires STRUCTURAL_OPEN"
            )
        birth = self.deferred_child_births.get(request_id)
        if birth is None or birth.disposition != "PENDING_MATERIALIZATION":
            raise ProspectiveV2IntegrityError(
                "request has no pending child birth"
            )
        request = self.deferred_requests[request_id]
        selected_identity = birth.members[1]
        visible = tuple(sorted(
            self.accepted_real_references.values(),
            key=lambda item: (item.ordinal, item.receipt_id),
        ))
        if not visible:
            raise ProspectiveV2IntegrityError("child birth has no REAL ledger")
        visible_ids = tuple(sorted(item.receipt_id for item in visible))
        ordinals = {item.receipt_id: item.ordinal for item in visible}
        direct = self._matching_parent_plus_identity_receipts(
            request.parent_cell_id, selected_identity, visible
        )
        candidate_state = next(
            item for item in request.candidate_terminals
            if item.identity == selected_identity
        )
        categories = (
            ("direct_child_matches", direct),
            ("parent_discovery_reads", tuple(sorted(
                request.parent_discovery_receipt_ids
            ))),
            ("parent_discovery_support", tuple(sorted(
                request.parent_discovery_support_receipt_ids
            ))),
            ("parent_prospective_support", tuple(sorted(
                request.parent_prospective_support_receipt_ids
            ))),
            ("eligibility_reads", tuple(sorted(
                candidate_state.inspected_receipt_ids
            ))),
            ("contradiction_trigger", (
                request.contradiction_receipt_id,
            )),
            ("transitive_ancestor_reads", tuple(sorted(
                request.transitive_ancestor_receipt_ids
            ))),
        )
        categorized_ids = {
            receipt_id for _name, ids in categories for receipt_id in ids
        }
        if not categorized_ids.issubset(visible_ids):
            raise ProspectiveV2IntegrityError(
                "child escrow reads beyond V_birth"
            )
        nomination_frontier = max(
            (ordinals[item] for item in categorized_ids), default=-1
        )
        birth_frontier = max(ordinals.values(), default=-1)
        escrow = NominationEscrow(
            operation="specialization",
            fixed_polarity=request.fixed_polarity,
            categorized_reads=categories,
            transitive_ancestor_receipt_ids=tuple(sorted(
                request.transitive_ancestor_receipt_ids
            )),
            discovery_exclusion_receipt_ids=visible_ids,
            birth_frontier=birth_frontier,
            triggering_receipt_id=request.contradiction_receipt_id,
            graph_request_root_state=NodeState.CONFIRMED.name,
            graph_request_terminal_state=NodeState.CONFIRMED.name,
            considered_context_ids=(request.parent_cell_id,),
            selected_context_ids=(request.parent_cell_id,),
            nomination_read_frontier=nomination_frontier,
            certification_frontier=birth_frontier,
            parent_hypothesis_digest=request.parent_hypothesis_digest,
            escrow_schema_version=NOMINATION_ESCROW_V3,
        )
        hypothesis = FrozenHypothesis(
            cell_id=birth.child_cell_id,
            members=birth.members,
            polarity=request.fixed_polarity,
            lineage_parent_id=request.parent_cell_id,
            specialization_depth=1,
            discovery_receipt_ids=escrow.discovery_receipt_ids,
            discovery_receipt_digest=_sha(list(
                escrow.discovery_receipt_ids
            )),
            birth_frontier=escrow.birth_frontier,
            structural_state=StemCellState.DORMANT.name,
            nomination_operation="specialization",
            triggering_receipt_id=escrow.triggering_receipt_id,
            graph_request_root_state=escrow.graph_request_root_state,
            graph_request_terminal_state=escrow.graph_request_terminal_state,
            considered_context_ids=escrow.considered_context_ids,
            selected_context_ids=escrow.selected_context_ids,
            nomination_read_frontier=escrow.nomination_read_frontier,
            certification_frontier=escrow.certification_frontier,
            nomination_escrow_digest=escrow.escrow_digest,
            provenance_kind=ProvenanceKind.EXACT_NOMINATION_READ_SET,
            nomination_read_sets=escrow.categorized_reads,
            transitive_ancestor_receipt_ids=(
                escrow.transitive_ancestor_receipt_ids
            ),
            discovery_exclusion_receipt_ids=(
                escrow.discovery_exclusion_receipt_ids
            ),
            initialization_origin=InitializationOrigin.PROSPECTIVE,
            dormant_origin=DormantOrigin.DEFERRED_SPECIALIZATION_CHILD,
            parent_hypothesis_digest=request.parent_hypothesis_digest,
            source_generation=self.current_generation,
            discovery_support_receipt_ids=(),
        )
        self.states[birth.child_cell_id] = ProspectiveAuthorityState(
            hypothesis=hypothesis,
            prospectively_certified=False,
        )
        self.structural_invariants[birth.child_cell_id] = (
            CellStructuralInvariant(
                cell_id=birth.child_cell_id,
                members=birth.members,
                polarity=request.fixed_polarity,
                lineage_parent_id=request.parent_cell_id,
                specialization_depth=1,
                structural_state=StemCellState.DORMANT.name,
                authority_node_ids=_cell_node_ids(birth.child_cell_id),
                authority_topology_identity=_cell_topology_identity(
                    birth.child_cell_id
                ),
                dormant_origin=(
                    DormantOrigin.DEFERRED_SPECIALIZATION_CHILD
                ),
                immutable_hypothesis_digest=hypothesis.hypothesis_digest,
                parent_hypothesis_digest=(
                    request.parent_hypothesis_digest
                ),
            )
        )
        self.deferred_child_escrows[birth.child_cell_id] = escrow
        self.deferred_child_births[request_id] = replace(
            birth, disposition="MATERIALIZED"
        )
        self.request_consumptions[request_id] = replace(
            self.request_consumptions[request_id],
            disposition="MATERIALIZED",
        )
        self.authority_topology = _executed_authority_topology_manifest(
            self.states
        )
        self._verify_invariants()
        return birth.child_cell_id

    def open_prospective_successor(self) -> GenerationBoundary:
        candidate = copy.deepcopy(self)
        result = candidate._open_prospective_successor_in_place()
        self.__dict__.clear()
        self.__dict__.update(candidate.__dict__)
        return result

    def _open_prospective_successor_in_place(self) -> GenerationBoundary:
        self._verify_invariants()
        if self.generation_phase is not GenerationPhase.STRUCTURAL_OPEN:
            raise ProspectiveV2IntegrityError(
                "prospective successor requires STRUCTURAL_OPEN"
            )
        if set(self.sealed_request_ids).difference(
            self.request_consumptions
        ):
            raise ProspectiveV2IntegrityError(
                "sealed requests remain unconsumed"
            )
        if any(
            item.disposition == "PENDING_MATERIALIZATION"
            for item in self.deferred_child_births.values()
        ):
            raise ProspectiveV2IntegrityError(
                "pending child birth at prospective open"
            )
        prior = self.continuation_digest()
        self.generation_phase = GenerationPhase.PROSPECTIVE_OPEN
        boundary = self._generation_boundary(
            phase=self.generation_phase,
            prior_continuation_digest=prior,
            queue_ids=self.sealed_request_ids,
        )
        self.generation_boundaries = (*self.generation_boundaries, boundary)
        self._verify_invariants()
        return boundary

    def seal_read_only_evaluation(self) -> None:
        candidate = copy.deepcopy(self)
        candidate._verify_invariants()
        if (
            candidate.generation_phase
            is not GenerationPhase.PROSPECTIVE_OPEN
            or candidate.pending_event is not None
        ):
            raise ProspectiveV2IntegrityError(
                "evaluation seal requires idle PROSPECTIVE_OPEN"
            )
        candidate.evaluation_sealed = True
        candidate._verify_invariants()
        self.__dict__.clear()
        self.__dict__.update(candidate.__dict__)

    def evaluate_sealed_real(
        self, frame: FrameContext
    ) -> dict[str, Any]:
        if not self.evaluation_sealed:
            raise ProspectiveV2IntegrityError(
                "read-only evaluation capability is not sealed"
            )
        before = self.continuation_digest()
        commitment = self.probe_real_exposure(frame)
        graph = self._graph_measure(commitment.trace)
        classification = self._classification_from_emissions(
            self.states, graph
        )
        if self.continuation_digest() != before:
            raise ProspectiveV2IntegrityError(
                "sealed evaluation mutated authority"
            )
        return {
            "commitment": commitment,
            "classification": classification,
            "graph_emissions": graph,
        }

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
            ordinals[item] > escrow.certification_frontier
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
        if tuple(sorted(context_ids)) != escrow.selected_context_ids:
            raise ProspectiveV2IntegrityError(
                "selected nomination context identity mismatch"
            )
        if not set(escrow.selected_context_ids).issubset(
            escrow.considered_context_ids
        ):
            raise ProspectiveV2IntegrityError(
                "selected nomination context was not considered"
            )
        all_reads = set(escrow.discovery_receipt_ids)
        nomination_frontier = max(
            (ordinals[item] for item in all_reads), default=-1
        )
        certification_frontier = max(
            (
                ordinals[item]
                for item in escrow.discovery_exclusion_receipt_ids
            ),
            default=-1,
        )
        if (
            escrow.nomination_read_frontier != nomination_frontier
            or escrow.certification_frontier != certification_frontier
            or escrow.birth_frontier != certification_frontier
        ):
            raise ProspectiveV2IntegrityError(
                "native nomination frontier mismatch"
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
            birth_frontier=escrow.certification_frontier,
            structural_state=cell.state.name,
            nomination_operation=escrow.operation,
            triggering_receipt_id=escrow.triggering_receipt_id,
            graph_request_root_state=escrow.graph_request_root_state,
            graph_request_terminal_state=escrow.graph_request_terminal_state,
            considered_context_ids=escrow.considered_context_ids,
            selected_context_ids=escrow.selected_context_ids,
            nomination_read_frontier=escrow.nomination_read_frontier,
            certification_frontier=escrow.certification_frontier,
            nomination_escrow_digest=escrow.escrow_digest,
            provenance_kind=ProvenanceKind.EXACT_NOMINATION_READ_SET,
            nomination_read_sets=escrow.categorized_reads,
            transitive_ancestor_receipt_ids=(
                escrow.transitive_ancestor_receipt_ids
            ),
            discovery_exclusion_receipt_ids=(
                escrow.discovery_exclusion_receipt_ids
            ),
            initialization_origin=InitializationOrigin.PROSPECTIVE,
            dormant_origin=getattr(cell, "dormant_origin", None),
            parent_hypothesis_digest=escrow.parent_hypothesis_digest,
            source_generation=0,
            discovery_support_receipt_ids=tuple(sorted(
                receipt_id for receipt_id in escrow.discovery_receipt_ids
                if self._historical_receipt_supports_cell(
                    self.base, cell, receipt_id
                )
            )),
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
        prefix_fingerprints = _validated_prefix_physical_fingerprints(
            self.base
        )
        self.discovery_prefix_physical_fingerprints = prefix_fingerprints
        self.discovery_prefix_physical_fingerprint_digest = _sha(
            list(prefix_fingerprints)
        )
        self.accepted_real_references = {
            item.receipt_id: item
            for item in self._historical_real_references(self.base)
        }
        ledger_ids = tuple(sorted(dict(epoch.receipt_ordinals)))
        frontier = max(dict(epoch.receipt_ordinals).values(), default=-1)
        allowed = {
            (StemCellState.MATURE.name, StemCellState.MATURE.name),
            (StemCellState.MATURE.name, StemCellState.PROBATION.name),
            (StemCellState.PROBATION.name, StemCellState.PROBATION.name),
            (StemCellState.SPECIALIZED.name, StemCellState.SPECIALIZED.name),
            (StemCellState.DORMANT.name, StemCellState.DORMANT.name),
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
                nomination_operation="historical",
                triggering_receipt_id=None,
                graph_request_root_state=None,
                graph_request_terminal_state=None,
                considered_context_ids=(),
                selected_context_ids=(),
                nomination_read_frontier=frontier,
                certification_frontier=frontier,
                nomination_escrow_digest=None,
                provenance_kind=ProvenanceKind.HISTORICAL_ACCEPTED_LEDGER,
                discovery_exclusion_receipt_ids=ledger_ids,
                initialization_origin=InitializationOrigin.HISTORICAL,
                dormant_origin=getattr(cell, "dormant_origin", None),
                source_generation=0,
                discovery_support_receipt_ids=tuple(sorted(
                    receipt_id for receipt_id in ledger_ids
                    if self._historical_receipt_supports_cell(
                        self.base, cell, receipt_id
                    )
                )),
            )
            cell.immutable_hypothesis_digest = hypothesis.hypothesis_digest
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
            self.structural_invariants[cell_id] = self._invariant_from_cell(cell)
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
        self.authority_topology = (
            _executed_authority_topology_manifest(self.states)
        )
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
        self.authority_topology = _executed_authority_topology_manifest(self.states)
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


    def observe_grounded_and_sync(
        self, receipt: Any
    ) -> tuple[Any, tuple[str, ...]]:
        """Atomically ground one native outcome and import all births."""

        candidate = copy.deepcopy(self)
        epoch = candidate.base.envelope.nomination_epoch
        if epoch is None or epoch.nomination_closed:
            raise ProspectiveV2IntegrityError(
                "specialization transaction requires open nomination"
            )
        if candidate.pending_event is not None or candidate.consumed_receipts:
            raise ProspectiveV2IntegrityError(
                "specialization transaction after certification is forbidden"
            )
        emission = candidate.base.observe_grounded(receipt)
        added = candidate._sync_organism_nominations_in_place()
        candidate.base.envelope._transaction_checkpoint("wrapper_sync")
        candidate._verify_invariants()
        self.__dict__.clear()
        self.__dict__.update(candidate.__dict__)
        return emission, added

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
        candidate.experimental_identity = (
            candidate._build_experimental_identity()
        )
        if not candidate.generation_boundaries:
            structural = candidate._generation_boundary(
                phase=GenerationPhase.STRUCTURAL_OPEN,
                prior_continuation_digest=(
                    candidate.base.continuation_digest_v3()
                ),
                queue_ids=(),
            )
            candidate.generation_boundaries = (structural,)
            prospective = candidate._generation_boundary(
                phase=GenerationPhase.PROSPECTIVE_OPEN,
                prior_continuation_digest=candidate.continuation_digest(),
                queue_ids=(),
            )
            candidate.generation_boundaries = (
                *candidate.generation_boundaries, prospective
            )
        candidate._verify_invariants()
        self.__dict__.clear()
        self.__dict__.update(candidate.__dict__)
        return manifest

    def clone_candidate_identical_arms(
        self,
    ) -> tuple[
        "NativeProspectiveAuthorityV2",
        "NativeProspectiveAuthorityV2",
    ]:
        self._verify_invariants()
        epoch = self.base.envelope.nomination_epoch
        if epoch is None or not epoch.nomination_closed:
            raise ProspectiveV2IntegrityError(
                "candidate-identical cloning requires closed nomination"
            )
        if (
            self.pending_event is not None
            or self.consumed_receipts
            or self.emissions
        ):
            raise ProspectiveV2IntegrityError(
                "candidate-identical cloning requires unexposed arms"
            )
        prospective = copy.deepcopy(self)
        legacy = copy.deepcopy(self)
        for arm, mode in (
            (prospective, V2Mode.PROSPECTIVE),
            (legacy, V2Mode.LEGACY),
        ):
            arm.mode = mode
            for cell_id, state in arm.states.items():
                cell = arm.base.envelope.cells[cell_id]
                state.prospectively_certified = (
                    mode is V2Mode.LEGACY and cell.is_mature
                )
                state.certification_receipt_ids = ()
                state.support_receipt_ids = ()
                state.contradiction_receipt_ids = ()
                state.successes = 0
                state.contradictions = 0
                state.support = 0
                state.success_lower_bound = 0.0
                state.contradiction_lower_bound = 0.0
                state.transition_rows = ()
            arm.experimental_identity = arm._build_experimental_identity()
            arm._verify_invariants()
        prospective.assert_candidate_parity(legacy)
        if (
            prospective.experimental_identity[
                "candidate_population_identity"
            ]
            != legacy.experimental_identity[
                "candidate_population_identity"
            ]
        ):
            raise ProspectiveV2IntegrityError(
                "candidate-identical arm population mismatch"
            )
        return prospective, legacy

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
        source_manifest_digest = _canonical_source_manifest_digest(self.base.r0)
        candidate_manifest_digest = self._candidate_manifest_digest()
        topology_digest = _sha(self.authority_topology)
        environment_terminal_identity = (
            self.base.learning_config.completion_terminal_identity
        )
        fingerprint = _interaction_fingerprint(
            source_organism_identity=trace.source_organism_identity,
            source_state_identity=trace.source_state_identity,
            predecessor_fen=board.fen(),
            trace=trace,
            actuation=actuation,
            successor_fen=successor.fen(),
            environment_outcome_terminal_identity=(
                environment_terminal_identity
            ),
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
            environment_outcome_terminal_identity=(
                environment_terminal_identity
            ),
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


    def open_virtual(
        self,
        frame: FrameContext,
        *,
        frame_session: NativeV2FrameSession | None = None,
    ) -> dict[str, Any]:
        if frame_session is not None:
            frame_session._require_open(self)
        self._verify_invariants(
            frozen_base_continuation_digest=(
                None
                if frame_session is None
                else frame_session.base_continuation_digest
            )
        )
        before = (
            self.continuation_digest()
            if frame_session is None
            else frame_session.continuation_digest(self)
        )
        if frame.kind is not FrameKind.VIRTUAL:
            raise ProspectiveV2IntegrityError(
                "virtual capability requires VIRTUAL frame"
            )
        if frame_session is None:
            session = self.base.dream_session()
            try:
                raw = session.request(frame)
            finally:
                session.close()
        else:
            raw = frame_session.r0_session.request(frame)
        trace = raw.graph_signal_trace
        if raw.actuation is not None and trace is None:
            raise ProspectiveV2IntegrityError(
                "VIRTUAL R0 actuation lacks its exact graph trace"
            )
        if trace is None:
            graph = {role: () for role in AUTHORITY_ROLES}
            classification = EnvelopeClassification(
                AvailabilityState.UNKNOWN, 0.5, 1.0, (), (),
                False, False, False,
            )
        else:
            graph = self._graph_measure(trace)
            classification = self._classification_from_emissions(
                self.states, graph
            )
        available = (
            raw.actuation is not None
            and classification.state is AvailabilityState.AVAILABLE
        )
        matched_certified = tuple(
            cell_id for cell_id in graph["commitment"]
            if self.states[cell_id].prospectively_certified
        )
        provenance = {
            cell_id: {
                "hypothesis_digest": (
                    self.states[cell_id].hypothesis.hypothesis_digest
                ),
                "polarity": self.states[cell_id].hypothesis.polarity.value,
                "prospectively_certified": True,
                "certification_receipt_ids": list(
                    self.states[cell_id].certification_receipt_ids
                ),
                "certification_receipt_digest": _sha(list(
                    self.states[cell_id].certification_receipt_ids
                )),
                "support": self.states[cell_id].support,
                "contradictions": self.states[cell_id].contradictions,
                "success_lower_bound": (
                    self.states[cell_id].success_lower_bound
                ),
            }
            for cell_id in matched_certified
        }
        response = ChildResponse(
            child_id=self.base.r0.provenance.child_id,
            confirmed=available,
            policy_response=raw.actuation is not None,
            available=available,
            expected_value=VIRTUAL_AVAILABLE_VALUE if available else 0.0,
            uncertainty=VIRTUAL_RESPONSE_UNCERTAINTY,
            grounded=self.base.r0.provenance.grounded,
            grounding_source=self.base.r0.provenance.grounding_source,
        )
        result = ChildQuery(
            response=response,
            actuation=raw.actuation,
            frame_id=raw.frame_id,
            persistent_mutation_count=raw.persistent_mutation_count,
            effect_attempts=raw.effect_attempts,
            active_competence_signal_ids=(
                () if trace is None else trace.ordered_signal_identities
            ),
            availability_provenance={
                "authority": "NativeProspectiveAuthorityV2_graph_emission",
                "classification": classification.to_manifest(),
                "matching_certified_cell_ids": list(matched_certified),
                "available_cell_ids": list(graph["available"]),
                "refuted_cell_ids": list(graph["refuted"]),
                "certification_provenance": provenance,
                "response_value": VIRTUAL_AVAILABLE_VALUE if available else 0.0,
                "response_uncertainty": VIRTUAL_RESPONSE_UNCERTAINTY,
                "certification_evidence_added": 0,
            },
            graph_signal_trace=trace,
        )
        after = (
            self.continuation_digest()
            if frame_session is None
            else frame_session.continuation_digest(self)
        )
        if after != before:
            raise ProspectiveV2IntegrityError(
                "VIRTUAL evaluation mutated state"
            )
        return {
            "query": result,
            "certification_commitment": None,
            "classification": classification,
            "graph_emissions": graph,
        }

    def continuation_manifest(
        self,
        *,
        frozen_base_v3: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "mode": self.mode.value,
            "specialization_mode": self.specialization_mode.value,
            "specialization_genome_seed": self.specialization_genome_seed,
            "structural_epoch_schedule": list(
                self.structural_epoch_schedule
            ),
            "current_generation": self.current_generation,
            "generation_phase": self.generation_phase.value,
            "base_v3": (
                self.base.continuation_manifest_v3()
                if frozen_base_v3 is None
                else copy.deepcopy(dict(frozen_base_v3))
            ),
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
            "accepted_real_references": {
                key: value.manifest()
                for key, value in sorted(
                    self.accepted_real_references.items()
                )
            },
            "deferred_requests": {
                key: value.manifest()
                for key, value in sorted(self.deferred_requests.items())
            },
            "request_queue": list(self.request_queue),
            "lifetime_requested_parent_ids": list(
                self.lifetime_requested_parent_ids
            ),
            "request_consumptions": {
                key: value.manifest()
                for key, value in sorted(
                    self.request_consumptions.items()
                )
            },
            "deferred_child_births": {
                key: value.manifest()
                for key, value in sorted(
                    self.deferred_child_births.items()
                )
            },
            "deferred_child_escrows": {
                key: value.manifest()
                for key, value in sorted(
                    self.deferred_child_escrows.items()
                )
            },
            "generation_boundaries": [
                item.manifest() for item in self.generation_boundaries
            ],
            "sealed_request_ids": list(self.sealed_request_ids),
            "sealed_request_queue_digest": (
                self.sealed_request_queue_digest
            ),
            "evaluation_sealed": self.evaluation_sealed,
            "physical_trace_projection_schema": (
                PHYSICAL_TRACE_PROJECTION_SCHEMA
            ),
            "discovery_prefix_physical_fingerprints": list(
                self.discovery_prefix_physical_fingerprints
            ),
            "discovery_prefix_physical_fingerprint_digest": (
                self.discovery_prefix_physical_fingerprint_digest
            ),
            "incremental_history_state": (
                None
                if self.incremental_history_state is None
                else self.incremental_history_state.manifest()
            ),
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
            "prospective_physical_fingerprints": dict(sorted(
                self.prospective_physical_fingerprints.items()
            )),
            "emissions": {
                key: value.manifest()
                for key, value in sorted(self.emissions.items())
            },
            "event_transactions": copy.deepcopy(dict(sorted(
                self.event_transactions.items()
            ))),
            "nomination_events": list(self.nomination_events),
            "experimental_identity": copy.deepcopy(
                self.experimental_identity
            ),
        }

    def continuation_digest(
        self,
        *,
        frozen_base_v3: Mapping[str, Any] | None = None,
    ) -> str:
        return _sha(self.continuation_manifest(
            frozen_base_v3=frozen_base_v3
        ))

    def dumps(self) -> bytes:
        self.verify_full_history_boundary("serialization")
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
        if getattr(item, "schema_version", None) != SCHEMA_VERSION:
            raise ProspectiveV2IntegrityError("unsupported V2 schema")
        before = item.continuation_manifest()
        item.base._canonical_rebuild()
        item.verify_full_history_boundary("restoration")
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
        "outcome_terminal_identity",
        "environment_outcome_terminal_identity", "interaction_fingerprint",
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
        if (
            commitment.environment_outcome_terminal_identity
            != organism.base.learning_config.completion_terminal_identity
        ):
            raise ProspectiveV2IntegrityError(
                "noncanonical environment outcome terminal"
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
        source_manifest_digest = _canonical_source_manifest_digest(organism.base.r0)
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
            environment_outcome_terminal_identity=(
                commitment.environment_outcome_terminal_identity
            ),
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
                "source_manifest_digest": _canonical_source_manifest_digest(organism.base.r0),
                "candidate_manifest_digest": organism._candidate_manifest_digest(),
                "authority_topology_digest": _sha(organism.authority_topology),
            })
            source_manifest_digest = _canonical_source_manifest_digest(organism.base.r0)
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
                or not row["environment_outcome_terminal_identity"]
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
                environment_outcome_terminal_identity=str(
                    row["environment_outcome_terminal_identity"]
                ),
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
