"""Graph-native prospective competence-evidence authority V2."""
from __future__ import annotations

from bisect import bisect_left, bisect_right
import copy
from dataclasses import asdict, dataclass, field, replace
from enum import Enum
import hashlib
import hmac
import json
import math
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
    NOMINATION_READ_CATEGORIES_V3, NOMINATION_ESCROW_V2,
    NOMINATION_ESCROW_V3, NOMINATION_ESCROW_V4,
    PROVENANCE_COMMITMENT_V4, PROVENANCE_WITNESS_LIMIT,
    NominationEscrow, ProvenanceCommitment, SpecializationMode,
    StructuralMatchDescriptor,
    _GraphSpecializationRequest, canonical_structural_pattern_matches,
    wilson_lower_bound,
)
from .native_trace_competence_authority import TraceNativeCompetenceOrganism
from .native_single_graph_curriculum import _triplet_id, _triplet_keys


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
_HOT_APPEND_DIGEST_SCHEMA = "native_v2_hot_append_digest.v1"
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
# This is a fixed execution-resource bound, not a learner-facing parameter.
# Candidate support remains exactly auditable at a full boundary; the live
# graph only needs a deterministic beam to avoid duplicating a late history
# prefix once per terminal leaf.
SPECIALIZATION_CANDIDATE_BEAM_WIDTH = 64
BOUNDARY_PROMOTION_REQUEST_SCHEMA = "native_v2_boundary_promotion_request.v1"
BOUNDARY_PROMOTION_GATE_STATE = "ELIGIBLE"
BOUNDARY_HYPOTHESIS_BIRTH_SCHEMA = "native_v2_continuous_hypothesis_birth.v1"
RETIREMENT_TOMBSTONE_SCHEMA = "native_v2_adaptive_retirement_tombstone.v1"
DEFAULT_RETIREMENT_REASON = "resource_rent"
# Generation-boundary ``prior_continuation_digest`` used to be the flat
# SHA-256 of the complete continuation manifest.  That representation is
# retained for old pickles, but it necessarily makes a historical boundary
# replay quadratic when the append-only ledgers grow.  New authorities use a
# versioned mutation-chain commitment: every durable mutation contributes one
# canonical operation record, so a replay advances the commitment once per
# event/boundary rather than rescanning the prefix.
BOUNDARY_DIGEST_SCHEMA_LEGACY = "flat_continuation_manifest_sha256.v1"
BOUNDARY_DIGEST_SCHEMA_BASE_V3 = "base_continuation_v3_sha256.v3"
BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN = (
    "native_v2_boundary_mutation_chain.v1"
)
_STRUCTURAL_CONSUMPTION_DISPOSITIONS = frozenset({
    "REJECTED_EMPTY_ELIGIBILITY",
    "REJECTED_DUPLICATE_PATTERN",
    "PENDING_CHILD",
    "MATERIALIZED",
})
_DEFERRED_BIRTH_DISPOSITIONS = frozenset({
    "PENDING_MATERIALIZATION",
    "MATERIALIZED",
})
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


def _empty_hot_append_digest(kind: str) -> str:
    return _sha({
        "schema_version": _HOT_APPEND_DIGEST_SCHEMA,
        "kind": kind,
        "count": 0,
    })


def _next_hot_append_digest(previous: str, kind: str, value: Any, count: int) -> str:
    return _sha({
        "schema_version": _HOT_APPEND_DIGEST_SCHEMA,
        "kind": kind,
        "count": int(count),
        "previous": previous,
        "value": value,
    })


def _append_log_digest(values: Sequence[Any], *, kind: str) -> str:
    """Build one append-log digest at initialization or a full boundary."""

    digest = _empty_hot_append_digest(kind)
    for count, value in enumerate(values, 1):
        digest = _next_hot_append_digest(digest, kind, value, count)
    return digest


def _bounded_provenance_witnesses(
    values: Sequence[str],
    *,
    limit: int = PROVENANCE_WITNESS_LIMIT,
) -> tuple[str, ...]:
    """Return deterministic bounded witnesses for a compact commitment.

    Witnesses are diagnostic and replay cross-checks only; the digest/count/
    frontier carry the authoritative extent.  Keeping this helper centralized
    prevents a caller from accidentally retaining a lifetime prefix in a new
    birth record.
    """

    if limit < 0 or limit > PROVENANCE_WITNESS_LIMIT:
        raise ProspectiveV2IntegrityError("invalid provenance witness limit")
    return tuple(sorted(set(map(str, values)))[:limit])


def _compact_set_commitment(
    values: Sequence[str],
    *,
    exclusive_frontier: int,
    query_digest: str | None = None,
    digest: str | None = None,
) -> ProvenanceCommitment:
    """Commit to a canonical read/support set without retaining its members."""

    canonical = tuple(sorted(set(map(str, values))))
    return ProvenanceCommitment(
        schema_version=PROVENANCE_COMMITMENT_V4,
        digest=_sha(list(canonical)) if digest is None else digest,
        count=len(canonical),
        exclusive_frontier=int(exclusive_frontier),
        witness_ids=_bounded_provenance_witnesses(canonical),
        query_digest=query_digest,
    )


def _compose_provenance_commitment(
    commitments: Sequence[ProvenanceCommitment],
    *,
    exclusive_frontier: int,
    query_digest: str | None = None,
) -> ProvenanceCommitment:
    """Build a bounded Merkle-DAG edge from already compact components."""

    parts = tuple(item.manifest() for item in commitments)
    witnesses = _bounded_provenance_witnesses(tuple(
        receipt_id
        for item in commitments
        for receipt_id in item.witness_ids
    ))
    return ProvenanceCommitment(
        schema_version=PROVENANCE_COMMITMENT_V4,
        digest=_sha({
            "schema_version": PROVENANCE_COMMITMENT_V4,
            "components": parts,
        }),
        count=sum(item.count for item in commitments),
        exclusive_frontier=int(exclusive_frontier),
        witness_ids=witnesses,
        query_digest=query_digest,
    )


def _compact_query_digest(value: Any) -> str:
    """Bind the exact category/query recipe, not its potentially large result."""

    return _sha({"schema_version": PROVENANCE_COMMITMENT_V4, "query": value})


def _provenance_commitment_from_manifest(
    value: Mapping[str, Any] | ProvenanceCommitment | None,
) -> ProvenanceCommitment | None:
    if value is None or isinstance(value, ProvenanceCommitment):
        return value
    return ProvenanceCommitment(
        schema_version=value["schema_version"],
        digest=value["digest"],
        count=int(value["count"]),
        exclusive_frontier=int(value["exclusive_frontier"]),
        witness_ids=tuple(value.get("witness_ids", ())),
        query_digest=value.get("query_digest"),
    )


class _AppendOnlyLedger(list):
    """A list-backed append log with tuple-compatible equality.

    The authority's public manifests continue to expose canonical lists and
    old callers often compare the in-memory fields with tuples.  Internally,
    however, REAL events must be able to append without allocating a copy of
    the complete receipt/request history.  This tiny compatibility type keeps
    that append-only storage detail out of the protocol surface.
    """

    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return list.__eq__(self, list(other))
        return list.__eq__(self, other)

    def __ne__(self, other: object) -> bool:
        # ``list.__ne__`` bypasses an overridden ``__eq__`` and would report
        # a tuple mismatch even when the canonical contents are identical.
        return not self == other


class _LiveAuthorityStateView(dict):
    """Marker for the already-maintained bounded live-state index."""

    # A digest-only topology is a property of the authority representation,
    # not of the current live subset.  In particular, retiring the last live
    # V4 child must not silently turn a new compact authority back into the
    # legacy full-manifest topology.  This attribute is runtime-only and is
    # restored from ``authority_topology`` at every explicit index refresh.
    topology_schema_version: str | None = None


class _ReferenceOverlay(Mapping[str, "AcceptedRealReference"]):
    """O(1) lookup view over accepted history plus one current REAL item."""

    def __init__(
        self,
        base: Mapping[str, "AcceptedRealReference"] | None,
        current: "AcceptedRealReference" | None = None,
    ) -> None:
        self._base = base if base is not None else MappingProxyType({})
        self._current = current

    def __getitem__(self, key: str) -> "AcceptedRealReference":
        if self._current is not None and key == self._current.receipt_id:
            return self._current
        return self._base[key]

    def __iter__(self):
        # Graph evaluation only performs keyed reads.  Iteration remains
        # correct for boundary/debug callers without copying the base map.
        if self._current is None or self._current.receipt_id in self._base:
            yield from self._base
            return
        yield from self._base
        yield self._current.receipt_id

    def __len__(self) -> int:
        if self._current is None or self._current.receipt_id in self._base:
            return len(self._base)
        return len(self._base) + 1

    def __contains__(self, key: object) -> bool:
        return bool(
            self._current is not None
            and key == self._current.receipt_id
        ) or key in self._base

    def get(
        self,
        key: str,
        default: "AcceptedRealReference | None" = None,
    ) -> "AcceptedRealReference | None":
        if self._current is not None and key == self._current.receipt_id:
            return self._current
        return self._base.get(key, default)


class _RealMutationJournal:
    """Reversible, bounded mutation log for one REAL transaction.

    Entries are recorded only for fields touched by the current matching
    topology and for O(1) ledger additions.  No lifetime map is cloned.  The
    journal is deliberately small and generic so late injected failures can
    restore the exact object graph, including append-only state logs.
    """

    def __init__(self) -> None:
        self._undo: list[Any] = []
        self._closed = False

    def set_attr(self, owner: Any, name: str, value: Any) -> None:
        old = getattr(owner, name)
        self._undo.append(lambda owner=owner, name=name, old=old: setattr(
            owner, name, old
        ))
        setattr(owner, name, value)

    def add_mapping(self, mapping: dict[Any, Any], key: Any, value: Any) -> None:
        existed = key in mapping
        old = mapping.get(key)
        self._undo.append(
            lambda mapping=mapping, key=key, existed=existed, old=old: (
                mapping.__setitem__(key, old)
                if existed
                else mapping.pop(key, None)
            )
        )
        mapping[key] = value

    def add_set(self, values: set[Any], value: Any) -> None:
        if value in values:
            return
        self._undo.append(lambda values=values, value=value: values.discard(
            value
        ))
        values.add(value)

    def append(self, values: list[Any], value: Any) -> None:
        old_length = len(values)

        def undo() -> None:
            del values[old_length:]

        self._undo.append(
            undo
        )
        values.append(value)

    def commit(self) -> None:
        self._undo.clear()
        self._closed = True

    def rollback(self) -> None:
        if self._closed:
            return
        for undo in reversed(self._undo):
            undo()
        self._undo.clear()
        self._closed = True


class _StructuralMutationJournal(_RealMutationJournal):
    """Bounded rollback journal for one event-driven structural safe point.

    The authority's frozen R0 and append-only evidence ledgers are never
    copied.  Structural settlement touches only a bounded live state/queue
    slice plus a finite set of newly appended ledger entries, all of which are
    reversible through the inherited attribute/map/set operations.
    """

    def remove_list_item(self, values: list[Any], value: Any) -> None:
        try:
            index = values.index(value)
        except ValueError:
            return
        old = values[index]
        self._undo.append(
            lambda values=values, index=index, old=old: values.insert(
                index, old
            )
        )
        values.pop(index)

    def delete_mapping(self, mapping: dict[Any, Any], key: Any) -> None:
        if key not in mapping:
            return
        old = mapping[key]
        self._undo.append(
            lambda mapping=mapping, key=key, old=old: mapping.__setitem__(
                key, old
            )
        )
        del mapping[key]

    def discard_set(self, values: set[Any], value: Any) -> None:
        if value not in values:
            return
        self._undo.append(lambda values=values, value=value: values.add(
            value
        ))
        values.discard(value)


def _specialization_feature_sort_key(
    identity: str,
    support_count: int,
    *,
    genome_seed: int = 0,
    request_ordinal: int = 0,
) -> tuple[int, bytes, str]:
    """Rank one local candidate by evidence, then frozen genome order."""

    genome = CompetenceContextGrowthGenome(genome_seed)
    return (
        -int(support_count),
        genome._priority(identity, 2, request_ordinal),
        identity,
    )


class ProspectiveV2IntegrityError(RuntimeError):
    """Fail-hard causal, structural, or authority contract violation."""


class ProspectiveProvenanceUnavailable(ProspectiveV2IntegrityError):
    """Exact discovery provenance is unavailable."""


class V2Mode(str, Enum):
    PROSPECTIVE = "prospective"
    LEGACY = "legacy_same_ledger"


class StructuralMode(str, Enum):
    """When deferred structural requests are allowed to settle."""

    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"


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
    # New recursive/deferred births use a Merkle-DAG edge to the parent and
    # bounded witnesses here.  The old fields above intentionally remain in
    # place so V1-V3/V7 pickles retain their historical manifest shape.
    provenance_schema_version: str | None = None
    discovery_read_commitment: ProvenanceCommitment | None = None
    discovery_exclusion_commitment: ProvenanceCommitment | None = None
    nomination_read_commitments: tuple[
        tuple[str, ProvenanceCommitment], ...
    ] = ()
    # Only the opt-in continuous protocol separates logical birth from graph
    # allocation.  Absent fields preserve every legacy hypothesis digest.
    hypothesis_birth_digest: str | None = None
    materialization_frontier: int | None = None
    semantic_source_identity: str | None = None
    semantic_member_roles: tuple[tuple[str, str], ...] = ()

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        # FrozenHypothesis predates compact provenance.  Supply defaults but
        # otherwise re-run the same validation/digest calculation so legacy
        # load/replay remains exact and tampering is fail-closed.
        for key, value in state.items():
            object.__setattr__(self, key, value)
        defaults = {
            "provenance_schema_version": None,
            "discovery_read_commitment": None,
            "discovery_exclusion_commitment": None,
            "nomination_read_commitments": (),
            "hypothesis_birth_digest": None,
            "materialization_frontier": None,
            "semantic_source_identity": None,
            "semantic_member_roles": (),
        }
        for key, value in defaults.items():
            if not hasattr(self, key):
                object.__setattr__(self, key, value)
        self.__post_init__()

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
        if self.hypothesis_birth_digest is not None:
            if (
                len(self.hypothesis_birth_digest) != 64
                or not isinstance(self.materialization_frontier, int)
                or isinstance(self.materialization_frontier, bool)
                or self.materialization_frontier < self.birth_frontier
                or not self.semantic_source_identity
                or tuple(key for key, _role in self.semantic_member_roles)
                != self.members
            ):
                raise ProspectiveV2IntegrityError("invalid continuous hypothesis identity")
        elif any((self.materialization_frontier is not None,
                  self.semantic_source_identity, self.semantic_member_roles)):
            # A newly selected deferred residual is born at allocation, not
            # at its ancestor's earlier semantic birth.  Its flattened typed
            # predicate is nevertheless frozen under the opted-in contract.
            if (self.materialization_frontier is not None
                or self.nomination_operation != "specialization"
                or not self.lineage_parent_id or not self.semantic_source_identity
                or not self.semantic_member_roles
                or tuple(sorted(set(self.semantic_member_roles))) != self.semantic_member_roles):
                raise ProspectiveV2IntegrityError("unbound continuous hypothesis fields")
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
        compact = (
            self.provenance_schema_version == PROVENANCE_COMMITMENT_V4
            or self.discovery_read_commitment is not None
            or self.discovery_exclusion_commitment is not None
            or bool(self.nomination_read_commitments)
        )
        if compact:
            if self.provenance_schema_version != PROVENANCE_COMMITMENT_V4:
                raise ProspectiveV2IntegrityError(
                    "compact hypothesis lacks V4 provenance schema"
                )
            if not isinstance(
                self.discovery_read_commitment, ProvenanceCommitment
            ) or not isinstance(
                self.discovery_exclusion_commitment, ProvenanceCommitment
            ):
                raise ProspectiveV2IntegrityError(
                    "compact hypothesis lacks provenance commitments"
                )
            if (
                self.discovery_read_commitment.digest
                != self.discovery_receipt_digest
                or tuple(self.discovery_receipt_ids)
                != tuple(self.discovery_read_commitment.witness_ids)
                or tuple(self.discovery_exclusion_receipt_ids)
                != tuple(self.discovery_exclusion_commitment.witness_ids)
            ):
                raise ProspectiveV2IntegrityError(
                    "compact hypothesis witnesses/digest disagree"
                )
            read_commitments = tuple(self.nomination_read_commitments)
            category_names = tuple(
                name for name, _ids in self.nomination_read_sets
            )
            if tuple(name for name, _item in read_commitments) != category_names:
                raise ProspectiveV2IntegrityError(
                    "compact hypothesis read commitments disagree"
                )
            if len(set(category_names)) != len(category_names):
                raise ProspectiveV2IntegrityError(
                    "compact hypothesis read categories duplicate"
                )
            category_map = dict(self.nomination_read_sets)
            for name, commitment in read_commitments:
                if not isinstance(commitment, ProvenanceCommitment):
                    raise ProspectiveV2IntegrityError(
                        "compact hypothesis category lacks commitment"
                    )
                if not set(category_map[name]).issubset(commitment.witness_ids):
                    raise ProspectiveV2IntegrityError(
                        "compact hypothesis category witness mismatch"
                    )
            direct_category = (
                "direct_child_matches"
                if "direct_child_matches" in category_map else "direct"
            )
            if not category_map.get(direct_category):
                raise ProspectiveV2IntegrityError(
                    "compact hypothesis has no explicit direct trigger read"
                )
            if self.triggering_receipt_id not in {
                *category_map.get(direct_category, ()),
                *category_map.get("contradiction_trigger", ()),
            }:
                raise ProspectiveV2IntegrityError(
                    "compact hypothesis trigger is not an explicit read"
                )
        discovery_support = tuple(sorted(set(
            self.discovery_support_receipt_ids
        )))
        if discovery_support != self.discovery_support_receipt_ids:
            raise ProspectiveV2IntegrityError(
                "noncanonical discovery support receipts"
            )
        if not compact and not set(discovery_support).issubset(
            self.discovery_receipt_ids
        ):
            raise ProspectiveV2IntegrityError(
                "discovery support is outside discovery reads"
            )
        if self.source_generation > 0:
            deferred = (
                self.nomination_operation == "specialization"
                and self.dormant_origin
                is DormantOrigin.DEFERRED_SPECIALIZATION_CHILD
                and bool(self.parent_hypothesis_digest)
            )
            adaptive = (
                self.nomination_operation == "ordinary"
                and self.dormant_origin
                is DormantOrigin.ADAPTIVE_BOUNDARY_CHILD
                and self.lineage_parent_id is None
                and self.specialization_depth == 0
                and self.parent_hypothesis_digest is None
            )
            if not (deferred or adaptive):
                raise ProspectiveV2IntegrityError(
                    "successor hypothesis lineage binding is invalid"
                )
        if not self.members:
            raise ProspectiveV2IntegrityError("empty pattern at candidate birth")
        canonical = tuple(sorted(set(self.discovery_receipt_ids)))
        if not canonical and not compact:
            raise ProspectiveProvenanceUnavailable(
                "prospective_provenance_unavailable: empty discovery set"
            )
        if canonical != self.discovery_receipt_ids:
            raise ProspectiveV2IntegrityError(
                "discovery receipt IDs are not canonical"
            )
        if not compact and self.discovery_receipt_digest != _sha(list(canonical)):
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
            if not compact and tuple(name for name, _ids in categories) not in {
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
            if not compact and union != canonical:
                raise ProspectiveV2IntegrityError(
                    "nomination read-set union differs from discovery ledger"
                )
            if not compact and not set(canonical).issubset(exclusion):
                raise ProspectiveV2IntegrityError(
                    "discovery reads missing from exclusion set"
                )
        expected_digest = _sha(self.identity_manifest())
        if self.hypothesis_digest and self.hypothesis_digest != expected_digest:
            raise ProspectiveV2IntegrityError("immutable hypothesis digest mismatch")
        object.__setattr__(self, "hypothesis_digest", expected_digest)

    def identity_manifest(self) -> dict[str, Any]:
        result = {
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
        if self.provenance_schema_version == PROVENANCE_COMMITMENT_V4:
            result.update({
                "provenance_schema_version": self.provenance_schema_version,
                "discovery_read_commitment": (
                    self.discovery_read_commitment.manifest()
                    if self.discovery_read_commitment is not None else None
                ),
                "discovery_exclusion_commitment": (
                    self.discovery_exclusion_commitment.manifest()
                    if self.discovery_exclusion_commitment is not None else None
                ),
                "nomination_read_commitments": {
                    name: commitment.manifest()
                    for name, commitment in self.nomination_read_commitments
                },
            })
        if self.semantic_source_identity is not None:
            result.update({
                "semantic_source_identity": self.semantic_source_identity,
                "semantic_member_roles": [list(item) for item in self.semantic_member_roles],
            })
        if self.hypothesis_birth_digest is not None:
            result.update({"hypothesis_birth_digest": self.hypothesis_birth_digest,
                           "materialization_frontier": self.materialization_frontier})
        return result

    def manifest(self) -> dict[str, Any]:
        return {
            **self.identity_manifest(),
            "hypothesis_digest": self.hypothesis_digest,
        }


def _receipt_is_post_birth(
    hypothesis: FrozenHypothesis,
    receipt: AcceptedRealReference | V2GroundedReceipt,
) -> bool:
    """Use the scalar compact event frontier, retaining legacy ID checks."""

    commitment = hypothesis.discovery_exclusion_commitment
    if (
        hypothesis.provenance_schema_version == PROVENANCE_COMMITMENT_V4
        and isinstance(commitment, ProvenanceCommitment)
    ):
        return receipt.ordinal >= commitment.exclusive_frontier
    return bool(
        receipt.ordinal > hypothesis.certification_frontier
        and receipt.receipt_id not in hypothesis.discovery_exclusion_receipt_ids
    )


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
    # Retired adaptive candidates stay in this append-only state ledger so
    # complete replay can still reconstruct every historical graph decision.
    # They are excluded from the live authority topology by
    # ``_live_authority_states``.  The defaults keep old pickles readable.
    retired: bool = False
    retirement_generation: int | None = None
    retirement_ordinal: int | None = None
    retirement_reason: str | None = None
    retirement_tombstone_digest: str | None = None
    # Runtime-only rolling summaries used by read-only VIRTUAL provenance.
    certification_receipt_digest: str = field(
        default="",
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        # Keep the protocol-facing tuple annotations for compatibility while
        # storing append-only event logs as mutable lists.  A REAL event then
        # appends in amortized O(1), and manifests/full replay canonicalize
        # them back to lists without changing their wire representation.
        for name in (
            "certification_receipt_ids",
            "support_receipt_ids",
            "contradiction_receipt_ids",
            "transition_rows",
        ):
            value = getattr(self, name)
            if not isinstance(value, _AppendOnlyLedger):
                setattr(self, name, _AppendOnlyLedger(value))
        if not self.certification_receipt_digest:
            self.certification_receipt_digest = (
                _append_log_digest(
                    self.certification_receipt_ids,
                    kind="certification_receipt",
                )
            )

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        """Make pre-metabolism authority pickles structurally readable."""

        self.__dict__.update(state)
        for name in (
            "certification_receipt_ids",
            "support_receipt_ids",
            "contradiction_receipt_ids",
            "transition_rows",
        ):
            value = getattr(self, name, ())
            if not isinstance(value, _AppendOnlyLedger):
                setattr(self, name, _AppendOnlyLedger(value))
        if not getattr(self, "certification_receipt_digest", ""):
            self.certification_receipt_digest = _append_log_digest(
                self.certification_receipt_ids,
                kind="certification_receipt",
            )
        self.__dict__.setdefault("retired", False)
        self.__dict__.setdefault("retirement_generation", None)
        self.__dict__.setdefault("retirement_ordinal", None)
        self.__dict__.setdefault("retirement_reason", None)
        self.__dict__.setdefault("retirement_tombstone_digest", None)

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
            "retired": bool(getattr(self, "retired", False)),
            "retirement_generation": getattr(
                self, "retirement_generation", None
            ),
            "retirement_ordinal": getattr(self, "retirement_ordinal", None),
            "retirement_reason": getattr(self, "retirement_reason", None),
            "retirement_tombstone_digest": getattr(
                self, "retirement_tombstone_digest", None
            ),
        }


def prospective_available_provider_records(
    states: Mapping[str, ProspectiveAuthorityState],
    classification: EnvelopeClassification,
) -> tuple[dict[str, Any], ...]:
    """Project certified positive cells into grounded local value providers.

    The projection reads only each cell's post-birth REAL certification
    ledger.  Discovery evidence may create the immutable hypothesis, but it
    contributes neither support nor value here.  Any contradiction, stale
    summary, retirement, or malformed scalar makes that cell abstain.
    """

    if classification.state is not AvailabilityState.AVAILABLE:
        return ()
    records: list[dict[str, Any]] = []
    for cell_id in classification.available_cell_ids:
        state = states.get(str(cell_id))
        if (
            not isinstance(state, ProspectiveAuthorityState)
            or bool(getattr(state, "retired", False))
            or not state.prospectively_certified
            or state.hypothesis.polarity is not AvailabilityState.AVAILABLE
            or state.hypothesis.initialization_origin
            is not InitializationOrigin.PROSPECTIVE
        ):
            continue
        # These append-only ledgers and the rolling certification digest are
        # maintained atomically by REAL consumption and fully reclosed at
        # serialization/audit boundaries.  A VIRTUAL provider read must stay
        # O(1) in lifetime evidence; rebuilding sets or rehashing the complete
        # ledger here would restore the historical quadratic hot path.
        certification_count = len(state.certification_receipt_ids)
        success_count = len(state.support_receipt_ids)
        contradiction_count = len(state.contradiction_receipt_ids)
        certification_digest = str(state.certification_receipt_digest)
        if (
            int(state.support) != certification_count
            or int(state.successes) != success_count
            or int(state.contradictions) != contradiction_count
            or certification_count != success_count + contradiction_count
            or int(state.successes) < MIN_SUPPORT
            or int(state.contradictions) != 0
            or len(certification_digest) != 64
        ):
            continue
        expected_lower_bound = wilson_lower_bound(
            int(state.successes),
            int(state.support),
            WILSON_Z,
        )
        try:
            recorded_lower_bound = float(state.success_lower_bound)
        except (TypeError, ValueError, OverflowError):
            continue
        if (
            not math.isfinite(recorded_lower_bound)
            or not math.isclose(
                recorded_lower_bound,
                expected_lower_bound,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            or recorded_lower_bound < LOWER_BOUND
            or recorded_lower_bound > 1.0
        ):
            continue
        records.append({
            "schema_version": "native_prospective_provider.v1",
            "provider_kind": "prospective_authority_cell",
            "cell_id": str(cell_id),
            "authority_cell_id": str(cell_id),
            "expected_value": recorded_lower_bound,
            "confidence": recorded_lower_bound,
            "uncertainty": 1.0 - recorded_lower_bound,
            "grounding_level": 0,
            "grounding_ancestors": (),
            "direct_positive_evidence": int(state.successes),
            "direct_contrast_evidence": int(state.contradictions),
            # The reply/credit adapter checks these exact post-birth counts
            # against the same ledger totals.  Omitting them makes a valid
            # certified cell fail the native provider contract and abstain.
            "support": certification_count,
            "successes": success_count,
            "contradictions": contradiction_count,
            "certification_receipt_count": certification_count,
            "certification_receipt_digest": certification_digest,
            "evidence_scope": "post_birth_real_certification_ledger",
            "discovery_evidence_used": False,
            "postbirth_real_certification": True,
            "prospectively_certified": True,
            "hypothesis_digest": state.hypothesis.hypothesis_digest,
            "lineage_parent_id": state.hypothesis.lineage_parent_id,
            "grounding_source": (
                "prospective_postbirth_real_certification"
            ),
        })
    return tuple(sorted(
        records,
        key=lambda item: (
            -float(item["expected_value"]),
            -int(item["direct_positive_evidence"]),
            str(item["cell_id"]),
        ),
    ))


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
    evidence_schema_version: str | None = None
    supporting_receipt_commitment: ProvenanceCommitment | None = None
    inspected_receipt_commitment: ProvenanceCommitment | None = None

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        for key, value in state.items():
            object.__setattr__(self, key, value)
        for key, value in {
            "evidence_schema_version": None,
            "supporting_receipt_commitment": None,
            "inspected_receipt_commitment": None,
        }.items():
            if not hasattr(self, key):
                object.__setattr__(self, key, value)
        self.__post_init__()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "specialization_mode",
            SpecializationMode(self.specialization_mode),
        )
        compact = (
            self.evidence_schema_version == PROVENANCE_COMMITMENT_V4
            or self.supporting_receipt_commitment is not None
            or self.inspected_receipt_commitment is not None
        )
        if compact:
            if self.evidence_schema_version != PROVENANCE_COMMITMENT_V4:
                raise ProspectiveV2IntegrityError(
                    "compact eligibility lacks V4 evidence schema"
                )
            if not isinstance(
                self.supporting_receipt_commitment,
                ProvenanceCommitment,
            ) or not isinstance(
                self.inspected_receipt_commitment,
                ProvenanceCommitment,
            ):
                raise ProspectiveV2IntegrityError(
                    "compact eligibility lacks evidence commitments"
                )
            if (
                self.supporting_occurrence_count
                != self.supporting_receipt_commitment.count
                or tuple(self.supporting_receipt_ids)
                != tuple(self.supporting_receipt_commitment.witness_ids)
                or tuple(self.inspected_receipt_ids)
                != tuple(self.inspected_receipt_commitment.witness_ids)
            ):
                raise ProspectiveV2IntegrityError(
                    "compact eligibility evidence disagrees"
                )
            if len(
                self.supporting_stable_physical_interaction_ids
            ) > PROVENANCE_WITNESS_LIMIT:
                raise ProspectiveV2IntegrityError(
                    "compact eligibility retains excess physical witnesses"
                )
        elif self.supporting_occurrence_count != len(
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
            or (
                not compact
                and len(self.supporting_receipt_ids)
                != len(self.supporting_stable_physical_interaction_ids)
            )
        ):
            raise ProspectiveV2IntegrityError(
                "noncanonical eligibility support evidence"
            )
        if (
            len(set(self.inspected_receipt_ids))
            != len(self.inspected_receipt_ids)
            or tuple(sorted(self.inspected_receipt_ids))
            != self.inspected_receipt_ids
            or (
                not compact
                and not set(self.supporting_receipt_ids).issubset(
                    self.inspected_receipt_ids
                )
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
        result = {
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
        if self.evidence_schema_version == PROVENANCE_COMMITMENT_V4:
            result.update({
                "evidence_schema_version": self.evidence_schema_version,
                "supporting_receipt_commitment": (
                    self.supporting_receipt_commitment.manifest()
                    if self.supporting_receipt_commitment is not None else None
                ),
                "inspected_receipt_commitment": (
                    self.inspected_receipt_commitment.manifest()
                    if self.inspected_receipt_commitment is not None else None
                ),
            })
        return result


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
    provenance_schema_version: str | None = None
    parent_discovery_commitment: ProvenanceCommitment | None = None
    parent_discovery_support_commitment: ProvenanceCommitment | None = None
    parent_prospective_support_commitment: ProvenanceCommitment | None = None
    transitive_ancestor_commitment: ProvenanceCommitment | None = None
    parent_query_commitment: str | None = None
    candidate_inspected_commitment: ProvenanceCommitment | None = None

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        for key, value in state.items():
            object.__setattr__(self, key, value)
        for key, value in {
            "provenance_schema_version": None,
            "parent_discovery_commitment": None,
            "parent_discovery_support_commitment": None,
            "parent_prospective_support_commitment": None,
            "transitive_ancestor_commitment": None,
            "parent_query_commitment": None,
            "candidate_inspected_commitment": None,
        }.items():
            if not hasattr(self, key):
                object.__setattr__(self, key, value)
        self.__post_init__()

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
        compact = (
            self.provenance_schema_version == PROVENANCE_COMMITMENT_V4
            or self.parent_discovery_commitment is not None
            or self.parent_discovery_support_commitment is not None
            or self.parent_prospective_support_commitment is not None
            or self.transitive_ancestor_commitment is not None
            or self.candidate_inspected_commitment is not None
        )
        if compact:
            if self.provenance_schema_version != PROVENANCE_COMMITMENT_V4:
                raise ProspectiveV2IntegrityError(
                    "compact request lacks V4 provenance schema"
                )
            commitments = (
                self.parent_discovery_commitment,
                self.parent_discovery_support_commitment,
                self.parent_prospective_support_commitment,
                self.transitive_ancestor_commitment,
                self.candidate_inspected_commitment,
            )
            if any(
                not isinstance(item, ProvenanceCommitment)
                for item in commitments
            ):
                raise ProspectiveV2IntegrityError(
                    "compact request lacks provenance commitment"
                )
            for values, commitment in zip(
                (
                    self.parent_discovery_receipt_ids,
                    self.parent_discovery_support_receipt_ids,
                    self.parent_prospective_support_receipt_ids,
                    self.transitive_ancestor_receipt_ids,
                ),
                commitments[:4],
            ):
                if tuple(values) != tuple(commitment.witness_ids):
                    raise ProspectiveV2IntegrityError(
                        "compact request witness mismatch"
                    )
            if self.parent_query_commitment is not None and (
                len(self.parent_query_commitment) != 64
                or any(
                    char not in "0123456789abcdef"
                    for char in self.parent_query_commitment
                )
            ):
                raise ProspectiveV2IntegrityError(
                    "compact request query commitment is not SHA-256"
                )
            if any(
                item.evidence_schema_version != PROVENANCE_COMMITMENT_V4
                for item in self.candidate_terminals
            ):
                raise ProspectiveV2IntegrityError(
                    "compact request contains legacy candidate evidence"
                )
            if len(self.candidate_terminals) > SPECIALIZATION_CANDIDATE_BEAM_WIDTH:
                raise ProspectiveV2IntegrityError(
                    "compact request exceeds specialization candidate beam"
                )

    def identity_manifest(self) -> dict[str, Any]:
        """All causal request fields bound by ``request_id``."""

        result = {
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
        if self.provenance_schema_version == PROVENANCE_COMMITMENT_V4:
            result.update({
                "provenance_schema_version": self.provenance_schema_version,
                "parent_discovery_commitment": (
                    self.parent_discovery_commitment.manifest()
                    if self.parent_discovery_commitment is not None else None
                ),
                "parent_discovery_support_commitment": (
                    self.parent_discovery_support_commitment.manifest()
                    if self.parent_discovery_support_commitment is not None
                    else None
                ),
                "parent_prospective_support_commitment": (
                    self.parent_prospective_support_commitment.manifest()
                    if self.parent_prospective_support_commitment is not None
                    else None
                ),
                "transitive_ancestor_commitment": (
                    self.transitive_ancestor_commitment.manifest()
                    if self.transitive_ancestor_commitment is not None else None
                ),
                "parent_query_commitment": self.parent_query_commitment,
                "candidate_inspected_commitment": (
                    self.candidate_inspected_commitment.manifest()
                    if self.candidate_inspected_commitment is not None else None
                ),
            })
        return result

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


def _boundary_promotion_gate_manifest(
    *,
    candidate_id: str,
    members: Sequence[str],
    fixed_polarity: AvailabilityState,
    triggering_receipt_id: str,
    supporting_receipt_ids: Sequence[str],
    inspected_receipt_ids: Sequence[str],
    promotion_gate_state: str,
) -> dict[str, Any]:
    """Return the small, content-blind gate payload bound by a request."""

    return {
        "candidate_id": candidate_id,
        "members": list(members),
        "fixed_polarity": fixed_polarity.value,
        "triggering_receipt_id": triggering_receipt_id,
        "supporting_receipt_ids": list(supporting_receipt_ids),
        "inspected_receipt_ids": list(inspected_receipt_ids),
        "promotion_gate_state": promotion_gate_state,
    }


@dataclass(frozen=True)
class BoundaryHypothesisBirth:
    """Outcome-blind fixed predicate committed before any certification read."""

    candidate_id: str
    members: tuple[str, ...]
    member_signal_roles: tuple[tuple[str, str], ...]
    source_identity: str
    semantic_identity: str
    birth_frontier_ordinal: int
    triggering_receipt_id: str
    source_generation: int
    sequence: int
    discovery_exclusion_commitment: ProvenanceCommitment
    birth_digest: str = ""

    def __post_init__(self) -> None:
        from .native_prospective_boundary_candidate_ecology import (
            boundary_candidate_semantic_identity,
        )
        if (
            not self.candidate_id or not self.source_identity
            or self.members != tuple(sorted(set(self.members)))
            or tuple(key for key, _ in self.member_signal_roles) != self.members
            or self.semantic_identity != boundary_candidate_semantic_identity(
                self.members, self.member_signal_roles, self.source_identity
            )
            or isinstance(self.birth_frontier_ordinal, bool)
            or self.birth_frontier_ordinal < 0
            or self.sequence < 0 or self.source_generation < 0
            or self.discovery_exclusion_commitment.exclusive_frontier
            != self.birth_frontier_ordinal + 1
        ):
            raise ProspectiveV2IntegrityError("invalid precommitted boundary hypothesis")
        expected = _sha(self.identity_manifest())
        if self.birth_digest and self.birth_digest != expected:
            raise ProspectiveV2IntegrityError("boundary hypothesis birth digest mismatch")
        object.__setattr__(self, "birth_digest", expected)

    def identity_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": BOUNDARY_HYPOTHESIS_BIRTH_SCHEMA,
            "candidate_id": self.candidate_id,
            "members": list(self.members),
            "member_signal_roles": [list(item) for item in self.member_signal_roles],
            "source_identity": self.source_identity,
            "semantic_identity": self.semantic_identity,
            "birth_frontier_ordinal": self.birth_frontier_ordinal,
            "triggering_receipt_id": self.triggering_receipt_id,
            "source_generation": self.source_generation,
            "sequence": self.sequence,
            "discovery_exclusion_commitment": self.discovery_exclusion_commitment.manifest(),
        }

    def manifest(self) -> dict[str, Any]:
        return {**self.identity_manifest(), "birth_digest": self.birth_digest}


@dataclass(frozen=True)
class BoundaryPromotionRequest:
    """Immutable authority input for one promoted ordinary boundary sketch."""

    candidate_id: str
    members: tuple[str, ...]
    fixed_polarity: AvailabilityState
    triggering_receipt_id: str
    supporting_receipt_ids: tuple[str, ...]
    inspected_receipt_ids: tuple[str, ...]
    source_generation: int
    promotion_gate_state: str = BOUNDARY_PROMOTION_GATE_STATE
    promotion_gate_digest: str = ""
    provenance_schema_version: str | None = None
    supporting_receipt_commitment: ProvenanceCommitment | None = None
    inspected_receipt_commitment: ProvenanceCommitment | None = None
    hypothesis_birth_digest: str | None = None

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        for key, value in state.items():
            object.__setattr__(self, key, value)
        for key, value in {
            "provenance_schema_version": None,
            "supporting_receipt_commitment": None,
            "inspected_receipt_commitment": None,
            "hypothesis_birth_digest": None,
        }.items():
            if not hasattr(self, key):
                object.__setattr__(self, key, value)
        self.__post_init__()

    def __post_init__(self) -> None:
        if self.hypothesis_birth_digest is not None and (
            not isinstance(self.hypothesis_birth_digest, str)
            or len(self.hypothesis_birth_digest) != 64
        ):
            raise ProspectiveV2IntegrityError("invalid boundary hypothesis birth link")
        if not isinstance(self.candidate_id, str) or not self.candidate_id:
            raise ProspectiveV2IntegrityError(
                "boundary promotion candidate identity is required"
            )
        members = tuple(self.members)
        if (
            not members
            or len(members) > 3
            or any(
                not isinstance(item, str)
                or not item
                or item.startswith("context:")
                or item == "internal:policy_response"
                for item in members
            )
            or tuple(sorted(set(members))) != members
        ):
            raise ProspectiveV2IntegrityError(
                "boundary promotion members are not canonical opaque signals"
            )
        object.__setattr__(self, "members", members)
        polarity = self.fixed_polarity
        if isinstance(polarity, bool):
            polarity = (
                AvailabilityState.AVAILABLE
                if polarity else AvailabilityState.REFUTED
            )
        try:
            polarity = AvailabilityState(polarity)
        except (TypeError, ValueError) as exc:
            raise ProspectiveV2IntegrityError(
                "boundary promotion polarity is not fixed"
            ) from exc
        if polarity is AvailabilityState.UNKNOWN:
            raise ProspectiveV2IntegrityError(
                "boundary promotion polarity cannot be UNKNOWN"
            )
        object.__setattr__(self, "fixed_polarity", polarity)
        if (
            not isinstance(self.triggering_receipt_id, str)
            or not self.triggering_receipt_id
        ):
            raise ProspectiveV2IntegrityError(
                "boundary promotion trigger receipt is required"
            )
        for name in (
            "supporting_receipt_ids", "inspected_receipt_ids",
        ):
            values = tuple(getattr(self, name))
            if (
                any(not isinstance(item, str) or not item for item in values)
                or len(set(values)) != len(values)
            ):
                raise ProspectiveV2IntegrityError(
                    f"boundary promotion {name} are not canonical"
                )
            object.__setattr__(self, name, tuple(sorted(values)))
        compact = (
            self.provenance_schema_version == PROVENANCE_COMMITMENT_V4
            or self.supporting_receipt_commitment is not None
            or self.inspected_receipt_commitment is not None
        )
        if compact:
            if self.provenance_schema_version != PROVENANCE_COMMITMENT_V4:
                raise ProspectiveV2IntegrityError(
                    "compact boundary request lacks V4 provenance schema"
                )
            if not isinstance(
                self.supporting_receipt_commitment, ProvenanceCommitment
            ) or not isinstance(
                self.inspected_receipt_commitment, ProvenanceCommitment
            ):
                raise ProspectiveV2IntegrityError(
                    "compact boundary request lacks evidence commitment"
                )
            if (
                self.supporting_receipt_ids
                != self.supporting_receipt_commitment.witness_ids
                or self.inspected_receipt_ids
                != self.inspected_receipt_commitment.witness_ids
            ):
                raise ProspectiveV2IntegrityError(
                    "compact boundary request witness mismatch"
                )
        if (
            isinstance(self.source_generation, bool)
            or not isinstance(self.source_generation, int)
            or self.source_generation < 0
        ):
            raise ProspectiveV2IntegrityError(
                "boundary promotion source generation is invalid"
            )
        gate_state = self.promotion_gate_state
        if isinstance(gate_state, bool):
            gate_state = (
                BOUNDARY_PROMOTION_GATE_STATE
                if gate_state else "REJECTED"
            )
        if gate_state != BOUNDARY_PROMOTION_GATE_STATE:
            raise ProspectiveV2IntegrityError(
                "boundary promotion gate did not confirm"
            )
        object.__setattr__(self, "promotion_gate_state", gate_state)
        expected_gate_digest = _sha(self.gate_manifest())
        if self.promotion_gate_digest:
            if self.promotion_gate_digest != expected_gate_digest:
                raise ProspectiveV2IntegrityError(
                    "boundary promotion gate digest mismatch"
                )
        else:
            object.__setattr__(
                self, "promotion_gate_digest", expected_gate_digest
            )

    def gate_manifest(self) -> dict[str, Any]:
        result = _boundary_promotion_gate_manifest(
            candidate_id=self.candidate_id,
            members=self.members,
            fixed_polarity=self.fixed_polarity,
            triggering_receipt_id=self.triggering_receipt_id,
            supporting_receipt_ids=self.supporting_receipt_ids,
            inspected_receipt_ids=self.inspected_receipt_ids,
            promotion_gate_state=self.promotion_gate_state,
        )
        if self.provenance_schema_version == PROVENANCE_COMMITMENT_V4:
            result["supporting_receipt_commitment"] = (
                self.supporting_receipt_commitment.manifest()
                if self.supporting_receipt_commitment is not None else None
            )
            result["inspected_receipt_commitment"] = (
                self.inspected_receipt_commitment.manifest()
                if self.inspected_receipt_commitment is not None else None
            )
        if self.hypothesis_birth_digest is not None:
            result["hypothesis_birth_digest"] = self.hypothesis_birth_digest
        return result

    def identity_manifest(self) -> dict[str, Any]:
        result = {
            "schema_version": BOUNDARY_PROMOTION_REQUEST_SCHEMA,
            **self.gate_manifest(),
            "source_generation": self.source_generation,
            "promotion_gate_digest": self.promotion_gate_digest,
        }
        if self.provenance_schema_version == PROVENANCE_COMMITMENT_V4:
            result["provenance_schema_version"] = self.provenance_schema_version
        return result

    @property
    def request_digest(self) -> str:
        return _sha({
            "kind": "V2_BOUNDARY_PROMOTION_REQUEST_V1",
            "request": self.identity_manifest(),
        })

    def manifest(self) -> dict[str, Any]:
        return {
            **self.identity_manifest(),
            "request_digest": self.request_digest,
        }

    @classmethod
    def from_manifest(
        cls, value: Mapping[str, Any]
    ) -> "BoundaryPromotionRequest":
        if value.get("schema_version") != BOUNDARY_PROMOTION_REQUEST_SCHEMA:
            raise ProspectiveV2IntegrityError(
                "unsupported boundary promotion request schema"
            )
        item = cls(
            candidate_id=value["candidate_id"],
            members=tuple(value["members"]),
            fixed_polarity=value["fixed_polarity"],
            triggering_receipt_id=value["triggering_receipt_id"],
            supporting_receipt_ids=tuple(value["supporting_receipt_ids"]),
            inspected_receipt_ids=tuple(value["inspected_receipt_ids"]),
            source_generation=value.get("source_generation", 0),
            promotion_gate_state=value.get(
                "promotion_gate_state", BOUNDARY_PROMOTION_GATE_STATE
            ),
            promotion_gate_digest=value.get("promotion_gate_digest", ""),
            provenance_schema_version=value.get("provenance_schema_version"),
            supporting_receipt_commitment=(
                _provenance_commitment_from_manifest(
                    value.get("supporting_receipt_commitment")
                )
            ),
            inspected_receipt_commitment=(
                _provenance_commitment_from_manifest(
                    value.get("inspected_receipt_commitment")
                )
            ),
            hypothesis_birth_digest=value.get("hypothesis_birth_digest"),
        )
        if value.get("request_digest") not in {None, item.request_digest}:
            raise ProspectiveV2IntegrityError(
                "boundary promotion request digest mismatch"
            )
        return item


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
class _DeferredRequestPlan:
    """Pure preview of one deferred genome request.

    A plan is intentionally separate from the mutable consumption record.  It
    lets a safe point run the organism-owned genome exactly once for every
    pending request, forecast the complete batch, and only then mutate the
    authority.  The resulting ``StructuralRequestConsumption`` is copied into
    the append-only ledger when the plan is committed.
    """

    consumption: StructuralRequestConsumption


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
    # The first structural boundary is anchored to the frozen base V3
    # continuation.  Subsequent boundaries in new authorities use the
    # authority mutation-chain commitment; old pickles omit this field and
    # remain on the flat-manifest verifier.
    prior_digest_schema: str = BOUNDARY_DIGEST_SCHEMA_LEGACY
    # Adaptive live-slot reclamations committed by this structural
    # transaction.  This is an audit-only projection: IDs remain tombstoned
    # in the authority state and are never reused.
    retired_cell_ids: tuple[str, ...] = ()

    def manifest(self) -> dict[str, Any]:
        manifest = {
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
            "retired_cell_ids": list(getattr(self, "retired_cell_ids", ())),
        }
        # Do not alter the canonical shape of pre-chain pickles: their flat
        # continuation digests were computed before this field existed.
        schema = getattr(
            self, "prior_digest_schema", BOUNDARY_DIGEST_SCHEMA_LEGACY
        )
        if schema != BOUNDARY_DIGEST_SCHEMA_LEGACY:
            manifest["prior_digest_schema"] = schema
        return manifest


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


def _cell_topology_identity(
    cell_id: str,
    hypothesis_digest: str | None = None,
) -> str:
    payload = {
        "cell_id": cell_id,
        "nodes": list(_cell_node_ids(cell_id)),
        "edges": [
            [ROLE_ROOTS[role], f"v2:{role}:{cell_id}", "SUB_SUR"]
            for role in CELL_AUTHORITY_ROLES
        ],
    }
    # Legacy invariants intentionally retain their historical identity.  A
    # V4 leaf, however, is executable only together with its immutable
    # hypothesis commitment; bind that digest so replacing its provenance
    # cannot leave a stale structural identity behind.
    if hypothesis_digest is not None:
        payload["hypothesis_digest"] = hypothesis_digest
    return _sha(payload)


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
        if not getattr(value, "retired", False)
    })


def _live_authority_states(
    states: Mapping[str, ProspectiveAuthorityState],
) -> dict[str, ProspectiveAuthorityState]:
    """Return the bounded live view while retaining retired state for replay.

    Retirement is an authority lifecycle operation, not deletion from the
    append-only evidence ledger.  Every graph constructor goes through this
    helper so a retired candidate can never match, emit, or consume a live
    successor slot even though its immutable evidence remains auditable.
    """

    if isinstance(states, _LiveAuthorityStateView):
        return states
    return {
        cell_id: state
        for cell_id, state in states.items()
        if not getattr(state, "retired", False)
    }


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


def _trace_source_policy_identity(trace: GraphSignalTrace) -> str:
    return _sha({"source_organism_identity": trace.source_organism_identity,
                 "source_state_identity": trace.source_state_identity})


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
        and state.hypothesis.dormant_origin in {
            DormantOrigin.MIXED_OUTCOME_SHADOW,
            DormantOrigin.DEFERRED_SPECIALIZATION_CHILD,
            DormantOrigin.ADAPTIVE_BOUNDARY_CHILD,
        }
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


def _bounded_specialization_evidence_ids(
    *,
    support_receipt_ids: Sequence[str],
    contradiction_receipt_ids: Sequence[str],
    discovery_support_receipt_ids: Sequence[str],
    emission_receipt_id: str,
    supports: bool,
    contradicts: bool,
    basis: RequestBasis,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Select the deterministic, bounded evidence window for one trigger.

    A request needs only enough prospective support to establish
    ``MIN_SUPPORT`` and one contradiction anchor.  The append-only ledgers
    remain complete for replay, but a late trigger must not materialize or
    sort their lifetime-sized contents.  Support ledgers are chronological,
    so their tail is sufficient; contradiction ledgers are chronological as
    well, making the first entry the earliest anchor in O(1).  Discovery
    support is an immutable R0-derived read set, not a per-event ledger, and
    is retained in full to preserve the request's existing candidate
    vocabulary semantics.  Thus the only growing history touched here is the
    fixed-size prospective window plus one contradiction anchor.

    ``support_receipt_ids`` and ``contradiction_receipt_ids`` describe the
    evidence *before* the triggering receipt.  The hot path naturally passes
    the pre-event state; full-boundary reconstruction supplies the same
    prefix explicitly.
    """

    prior_support_count = MIN_SUPPORT - 1 if supports else MIN_SUPPORT
    prior_support_ids = (
        () if prior_support_count <= 0
        else tuple(support_receipt_ids[-prior_support_count:])
    )
    prospective_support_ids = (
        (*prior_support_ids, emission_receipt_id)
        if supports else prior_support_ids
    )
    discovery_support_ids = (
        discovery_support_receipt_ids
        if isinstance(discovery_support_receipt_ids, tuple)
        else tuple(discovery_support_receipt_ids)
    )
    if basis is RequestBasis.CERTIFIED_REVOCATION:
        contradiction_ids = (emission_receipt_id,)
    elif contradiction_receipt_ids:
        contradiction_ids = (contradiction_receipt_ids[0],)
    elif contradicts:
        contradiction_ids = (emission_receipt_id,)
    else:
        contradiction_ids = ()
    all_support_ids = tuple(sorted({
        *discovery_support_ids,
        *prospective_support_ids,
    }))
    return (
        tuple(sorted(prospective_support_ids)),
        contradiction_ids,
        all_support_ids,
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
        receipt.receipt_id and _receipt_is_post_birth(state.hypothesis, receipt)
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

    (
        prospective_support_ids,
        contradiction_ids,
        all_support_ids,
    ) = _bounded_specialization_evidence_ids(
        support_receipt_ids=state.support_receipt_ids,
        contradiction_receipt_ids=state.contradiction_receipt_ids,
        discovery_support_receipt_ids=(
            state.hypothesis.discovery_support_receipt_ids
        ),
        emission_receipt_id=receipt.receipt_id,
        supports=supports,
        contradicts=contradicts,
        basis=basis,
    )
    missing = tuple(sorted(
        receipt_id for receipt_id in {
            *prospective_support_ids,
            *contradiction_ids,
            *all_support_ids,
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
    # ``contradiction_ids`` contains only the chronological first anchor (or
    # the current receipt for certified revocation), so lookup is O(1).
    contradiction_reference = references[contradiction_ids[0]]
    return _SpecializationRequestTrigger(
        basis=basis,
        emission_reference=current_reference,
        contradiction_reference=contradiction_reference,
        parent_prospective_support_receipt_ids=prospective_support_ids,
        all_support_receipt_ids=all_support_ids,
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
        requested = env.get("lifetime_requested_parent_ids", ())
        # The live authority supplies its persistent O(1) membership index.
        # Only legacy/boundary callers which hand us a sequence need a local
        # immutable conversion (those paths are not the REAL hot path).
        if not isinstance(requested, (set, frozenset)):
            requested = frozenset(requested)
        descriptors = _structural_match_descriptors(states)
        trace_roles = {item.identity: item.role for item in snapshot.trace.terminal_signals}
        trace_source = _trace_source_policy_identity(snapshot.trace)
        # Removing an inapplicable descriptor also removes its context from
        # recursive descendants through the same canonical matcher.
        descriptors = {key: descriptor for key, descriptor in descriptors.items()
                       if states[key].hypothesis.semantic_source_identity is None
                       or (states[key].hypothesis.semantic_source_identity == trace_source
                           and all(trace_roles.get(member) == role for member, role
                                   in states[key].hypothesis.semantic_member_roles))}
        return cls(
            snapshot=snapshot,
            states=states,
            specialization_mode=SpecializationMode(env.get(
                "specialization_mode", SpecializationMode.DISCONNECTED.value
            )),
            lifetime_requested_parent_ids=requested,
            structural_matches=_StructuralPatternMatchCache(
                descriptors=descriptors,
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
            if state.hypothesis.semantic_source_identity is not None:
                roles = {item.identity: item.role for item in self.snapshot.trace.terminal_signals}
                matched = bool(matched
                    and _trace_source_policy_identity(self.snapshot.trace) == state.hypothesis.semantic_source_identity
                    and all(roles.get(key) == role for key, role in state.hypothesis.semantic_member_roles))
            receipt = self.snapshot.grounded_receipt
            post_frontier = bool(
                receipt is not None
                and receipt.receipt_id
                and _receipt_is_post_birth(state.hypothesis, receipt)
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
        and int(node.meta.get("known_contradiction_count", 0)) == 0
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
    *,
    legacy_full_hypothesis_meta: bool = False,
) -> Graph:
    """Build the canonical organism-owned authority graph."""
    states = _live_authority_states(states)
    graph = Graph()
    for role in CELL_AUTHORITY_ROLES:
        graph.add_node(Node(
            ROLE_ROOTS[role], NodeType.SCRIPT,
            meta={"confirm_policy": "or", "authority_role": role},
        ))
        for cell_id in sorted(states):
            node_id = f"v2:{role}:{cell_id}"
            leaf_meta = {
                "terminal_kind": f"PROSPECTIVE_{role.upper()}",
                "authority_role": role,
                "cell_id": cell_id,
            }
            if legacy_full_hypothesis_meta:
                # Schema-less V1--V3 checkpoints persisted this exact leaf
                # payload.  It is rebuilt only for compatibility reclosure;
                # runtime execution always uses the compact digest identity.
                leaf_meta["frozen_hypothesis"] = (
                    states[cell_id].hypothesis.manifest()
                )
            else:
                leaf_meta["hypothesis_digest"] = (
                    states[cell_id].hypothesis.hypothesis_digest
                )
            graph.add_node(Node(
                node_id, NodeType.TERMINAL, predicate=_authority_terminal,
                meta=leaf_meta,
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

    sticky_schema = getattr(states, "topology_schema_version", None)
    compact = (
        sticky_schema == "native_v2_authority_topology.v2_digest_only"
        if sticky_schema is not None
        else any(
            state.hypothesis.provenance_schema_version
            == PROVENANCE_COMMITMENT_V4
            for state in states.values()
        )
    )
    if compact and hasattr(states, "topology_schema_version"):
        # Once a live V4 birth has selected the compact representation, keep
        # that representation even if the birth is subsequently retired and
        # no V4 state remains in this bounded live view.
        setattr(
            states,
            "topology_schema_version",
            "native_v2_authority_topology.v2_digest_only",
        )
    graph = _build_authority_graph(
        states,
        legacy_full_hypothesis_meta=not compact,
    )
    graph_snapshot = graph.to_snapshot()
    result = {
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
    if compact:
        # New compact authorities rebuild the execution graph from state and
        # bind only its digest in durable topology.  Legacy authorities keep
        # their old full snapshot so V1-V3/V7 load/replay remains exact.
        result.update({
            "topology_schema_version": (
                "native_v2_authority_topology.v2_digest_only"
            ),
            "graph_snapshot_digest": _sha(graph_snapshot),
            "graph_node_count": len(graph.nodes),
        })
    else:
        result["graph_snapshot"] = graph_snapshot
    return result


def _run_authority_graph(
    states: Mapping[str, ProspectiveAuthorityState],
    snapshot: AuthorityMeasurementSnapshot,
    *,
    accepted_real_references: Mapping[str, AcceptedRealReference] | None = None,
    current_real_reference: AcceptedRealReference | None = None,
    specialization_mode: SpecializationMode = SpecializationMode.DISCONNECTED,
    lifetime_requested_parent_ids: Sequence[str] = (),
    specialization_genome_seed: int = 0,
    compact_provenance: bool = False,
) -> dict[str, Any]:
    # Retired adaptive candidates remain in the replay state ledger, but are
    # deliberately absent from every live graph invocation.
    states = _live_authority_states(states)
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
            # This is a persistent membership index on the REAL path.  Do not
            # rebuild a tuple/frozenset from the lifetime request ledger for
            # every terminal evaluation.
            "lifetime_requested_parent_ids": lifetime_requested_parent_ids,
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
    references: Mapping[str, AcceptedRealReference] = _ReferenceOverlay(
        accepted_real_references
    )
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
        references = _ReferenceOverlay(
            accepted_real_references,
            current_real_reference,
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
            tuple[
                str,
                tuple[str, ...],
                tuple[str, ...],
                int,
                tuple[AcceptedRealReference, ...],
            ]
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
            vocabulary_set = {
                identity
                for reference in support_refs
                for identity in reference.ordered_signal_identities
                if _specialization_identity_role_permitted(
                    reference, identity
                )
            }
            support_counts = {
                identity: sum(
                    identity in reference.ordered_signal_identities
                    for reference in support_refs
                )
                for identity in vocabulary_set
            }
            vocabulary = tuple(sorted(
                vocabulary_set,
                key=lambda identity: _specialization_feature_sort_key(
                    identity,
                    support_counts[identity],
                    genome_seed=specialization_genome_seed,
                    request_ordinal=0,
                ),
            ))[:SPECIALIZATION_CANDIDATE_BEAM_WIDTH]
            contradiction_signal_ids = (
                trigger.contradiction_reference.ordered_signal_identities
            )
            inspected = tuple(sorted({
                *support_ids,
                trigger.contradiction_reference.receipt_id,
                trigger.emission_reference.receipt_id,
            }))
            inspected_witnesses = _bounded_provenance_witnesses(inspected)
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
                        "supporting_receipt_ids": (
                            _bounded_provenance_witnesses(
                                supporting_receipt_ids
                            )
                            if compact_provenance
                            else supporting_receipt_ids
                        ),
                        "supporting_stable_physical_interaction_ids": (
                            _bounded_provenance_witnesses(
                                supporting_physical_ids
                            )
                            if compact_provenance
                            else supporting_physical_ids
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
            eligibility_plans.append((
                parent_id,
                vocabulary,
                inspected,
                trigger.emission_reference.ordinal + 1,
                support_refs,
            ))

        if any(
            vocabulary
            for _parent, vocabulary, _inspected, _frontier, _support_refs
            in eligibility_plans
        ):
            _run_authority_component(
                graph,
                (ROLE_ROOTS["specialization_eligibility"],),
                env={},
            )

        for (
            parent_id,
            vocabulary,
            inspected,
            inspection_frontier,
            support_refs,
        ) in eligibility_plans:
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
                    inspected_receipt_ids=(
                        _bounded_provenance_witnesses(inspected)
                        if compact_provenance else inspected
                    ),
                    evidence_schema_version=(
                        PROVENANCE_COMMITMENT_V4
                        if compact_provenance else None
                    ),
                    supporting_receipt_commitment=(
                        _compact_set_commitment(
                            tuple(
                                reference.receipt_id
                                for reference in support_refs
                                if identity
                                in reference.ordered_signal_identities
                            ),
                            exclusive_frontier=inspection_frontier,
                        )
                        if compact_provenance else None
                    ),
                    inspected_receipt_commitment=(
                        _compact_set_commitment(
                            inspected,
                            exclusive_frontier=inspection_frontier,
                        )
                        if compact_provenance else None
                    ),
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
    # The tuple is the canonical persisted exclusion ledger.  REAL admission
    # uses this immutable set projection so a long discovery prefix is not
    # linearly rescanned for every post-nomination event.
    _discovery_prefix_physical_fingerprint_set: frozenset[str] = field(
        default_factory=frozenset, repr=False, compare=False
    )
    # Historical native-pruned cells and adaptive retirements are separate:
    # the former belong to the frozen discovery ledger, while the latter are
    # authority-local live-slot reclamations after prospective birth.
    retired_tombstones: dict[str, dict[str, Any]] = field(default_factory=dict)
    boundary_hypothesis_births: dict[str, BoundaryHypothesisBirth] = field(default_factory=dict)
    _boundary_hypothesis_birth_digest: str = ""
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
    boundary_promotion_requests: dict[str, BoundaryPromotionRequest] = field(
        default_factory=dict
    )
    adaptive_boundary_escrows: dict[str, NominationEscrow] = field(
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
    # New authorities commit boundary chronology with an append-only
    # mutation chain.  The legacy default is intentional for unpickled
    # authorities created before this versioned field existed.
    boundary_digest_schema: str = BOUNDARY_DIGEST_SCHEMA_LEGACY
    _boundary_commitment_origin_digest: str = field(
        default="", repr=False, compare=False
    )
    _boundary_commitment_digest: str = field(
        default="", repr=False, compare=False
    )
    _boundary_commitment_count: int = field(
        default=0, repr=False, compare=False
    )
    _boundary_accepted_real_digest: str = field(
        default="", repr=False, compare=False
    )
    _boundary_candidate_digest: str = field(
        default="", repr=False, compare=False
    )
    _boundary_decision_digest: str = field(
        default="", repr=False, compare=False
    )
    _boundary_schedule_digest: str = field(
        default="", repr=False, compare=False
    )
    _boundary_structure_digest: str = field(
        default="", repr=False, compare=False
    )
    _boundary_request_digest_cache: dict[tuple[str, ...], str] = field(
        default_factory=dict, repr=False, compare=False
    )
    # Replay-only indexes.  They are seeded once from the immutable ledgers
    # and then updated by the same structural deltas that replay applies.
    # Keeping them off the continuation manifest avoids making runtime cache
    # layout part of the persisted protocol.
    _boundary_replay_active_promotion_ids: set[str] = field(
        default_factory=set, repr=False, compare=False
    )
    _boundary_replay_promotions_by_generation: dict[
        int, tuple[tuple[str, BoundaryPromotionRequest], ...]
    ] = field(default_factory=dict, repr=False, compare=False)
    _boundary_replay_promotion_by_child: dict[str, str] = field(
        default_factory=dict, repr=False, compare=False
    )
    _active_boundary_promotion_ids: set[str] = field(
        default_factory=set, repr=False, compare=False
    )
    _boundary_promotion_by_child: dict[str, str] = field(
        default_factory=dict, repr=False, compare=False
    )
    schema_version: str = SCHEMA_VERSION
    _receipt_secret: bytes = field(
        default=b"native-prospective-v2-environment-terminal"
    )
    _history_validation_mode: str = field(
        default=HISTORY_VALIDATION_INCREMENTAL,
        repr=False,
        compare=False,
    )
    structural_mode: StructuralMode = StructuralMode.SCHEDULED
    # A scheduled successor previews its whole sealed batch at the structural
    # safe point.  Keeping those immutable plans through the subsequent
    # one-at-a-time compatibility API prevents a second genome call after a
    # snapshot/resume.  They are not learner state; the manifest nevertheless
    # records them so an interrupted structural phase is exact on reload.
    structural_request_plans: dict[str, StructuralRequestConsumption] = field(
        default_factory=dict,
        repr=False,
        compare=False,
    )
    # Runtime-only indexes.  They are rebuilt by the full invariant boundary
    # and let REAL/VIRTUAL graph calls see only the bounded live topology.
    _live_authority_state_cache: dict[str, ProspectiveAuthorityState] = field(
        default_factory=dict,
        repr=False,
        compare=False,
    )
    _requested_parent_index: set[str] = field(
        default_factory=set,
        repr=False,
        compare=False,
    )
    _pending_request_index: set[str] = field(
        default_factory=set,
        repr=False,
        compare=False,
    )
    _pending_request_order: list[str] = field(
        default_factory=list,
        repr=False,
        compare=False,
    )
    _request_queue_hot_digest: str = field(
        default="",
        repr=False,
        compare=False,
    )
    _requested_parent_hot_digest: str = field(
        default="",
        repr=False,
        compare=False,
    )
    _hot_path_revision: int = field(
        default=0,
        repr=False,
        compare=False,
    )
    _hot_path_indexes_ready: bool = field(
        default=False,
        repr=False,
        compare=False,
    )
    _hot_structure_digest: str = field(
        default="",
        repr=False,
        compare=False,
    )
    _hot_boundary_promotion_digest: str = field(
        default="",
        repr=False,
        compare=False,
    )
    # Bounded successor-slot occupancy.  ``states`` and the deferred birth
    # ledger are append-only for replay, so scanning either collection at
    # every event-driven safe point would reintroduce lifetime-linear work.
    # This set is rebuilt only at an explicit full boundary and then changed
    # transactionally with each reservation, materialization, or retirement.
    _successor_capacity_occupant_ids: set[str] = field(
        default_factory=set,
        repr=False,
        compare=False,
    )
    _pending_child_birth_request_ids: set[str] = field(
        default_factory=set,
        repr=False,
        compare=False,
    )
    _reserved_member_pairs: set[tuple[str, ...]] = field(
        default_factory=set,
        repr=False,
        compare=False,
    )
    _accepted_real_reference_order: list[str] = field(
        default_factory=list,
        repr=False,
        compare=False,
    )
    _accepted_real_prefix_witness_ids: tuple[str, ...] = field(
        default=(),
        repr=False,
        compare=False,
    )
    _accepted_real_reference_ordinals: list[int] = field(
        default_factory=list,
        repr=False,
        compare=False,
    )
    _accepted_real_by_signal_identity: dict[str, list[str]] = field(
        default_factory=dict,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        # The append-only ledgers are intentionally list-backed; conversion is
        # one-time initialization and never occurs on a REAL append.
        for name in (
            "request_queue",
            "lifetime_requested_parent_ids",
            "generation_boundaries",
        ):
            value = getattr(self, name)
            if not isinstance(value, _AppendOnlyLedger):
                setattr(self, name, _AppendOnlyLedger(value))
        if not isinstance(self._pending_request_order, list):
            self._pending_request_order = list(self._pending_request_order)
        self.structural_mode = StructuralMode(self.structural_mode)
        self.boundary_digest_schema = str(getattr(
            self,
            "boundary_digest_schema",
            BOUNDARY_DIGEST_SCHEMA_LEGACY,
        ))
        self._boundary_commitment_origin_digest = str(getattr(
            self, "_boundary_commitment_origin_digest", ""
        ))
        self._boundary_commitment_digest = str(getattr(
            self, "_boundary_commitment_digest", ""
        ))
        self._boundary_commitment_count = int(getattr(
            self, "_boundary_commitment_count", 0
        ))
        for name in (
            "_boundary_accepted_real_digest",
            "_boundary_candidate_digest",
            "_boundary_decision_digest",
            "_boundary_schedule_digest",
            "_boundary_structure_digest",
        ):
            setattr(self, name, str(getattr(self, name, "")))
        self._boundary_request_digest_cache = dict(getattr(
            self, "_boundary_request_digest_cache", {}
        ))
        self._discovery_prefix_physical_fingerprint_set = frozenset(
            getattr(
                self,
                "discovery_prefix_physical_fingerprints",
                (),
            )
        )
        self._boundary_replay_active_promotion_ids = set(getattr(
            self, "_boundary_replay_active_promotion_ids", set()
        ))
        self._boundary_replay_promotions_by_generation = dict(getattr(
            self, "_boundary_replay_promotions_by_generation", {}
        ))
        self._boundary_replay_promotion_by_child = dict(getattr(
            self, "_boundary_replay_promotion_by_child", {}
        ))
        self._active_boundary_promotion_ids = set(getattr(
            self, "_active_boundary_promotion_ids", set()
        ))
        self._boundary_promotion_by_child = dict(getattr(
            self, "_boundary_promotion_by_child", {}
        ))
        self._successor_capacity_occupant_ids = set(getattr(
            self, "_successor_capacity_occupant_ids", set()
        ))
        self._pending_child_birth_request_ids = set(getattr(
            self, "_pending_child_birth_request_ids", set()
        ))
        self._reserved_member_pairs = {
            tuple(item) for item in getattr(
                self, "_reserved_member_pairs", set()
            )
        }
        self._accepted_real_reference_order = list(getattr(
            self, "_accepted_real_reference_order", []
        ))
        self._accepted_real_prefix_witness_ids = tuple(getattr(
            self, "_accepted_real_prefix_witness_ids", ()
        ))
        self._accepted_real_reference_ordinals = list(getattr(
            self, "_accepted_real_reference_ordinals", []
        ))
        self._accepted_real_by_signal_identity = {
            str(identity): list(receipt_ids)
            for identity, receipt_ids in getattr(
                self, "_accepted_real_by_signal_identity", {}
            ).items()
        }

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        # Pickles produced before the explicit structural-mode field are
        # still scheduled authorities, preserving their old semantics.
        self.__dict__.update(state)
        self.boundary_hypothesis_births = dict(getattr(self, "boundary_hypothesis_births", {}))
        self._boundary_hypothesis_birth_digest = str(getattr(self, "_boundary_hypothesis_birth_digest", ""))
        self.structural_mode = StructuralMode(
            getattr(self, "structural_mode", StructuralMode.SCHEDULED)
        )
        self.boundary_digest_schema = str(getattr(
            self,
            "boundary_digest_schema",
            BOUNDARY_DIGEST_SCHEMA_LEGACY,
        ))
        self._boundary_commitment_origin_digest = str(getattr(
            self, "_boundary_commitment_origin_digest", ""
        ))
        self._boundary_commitment_digest = str(getattr(
            self, "_boundary_commitment_digest", ""
        ))
        self._boundary_commitment_count = int(getattr(
            self, "_boundary_commitment_count", 0
        ))
        for name in (
            "_boundary_accepted_real_digest",
            "_boundary_candidate_digest",
            "_boundary_decision_digest",
            "_boundary_schedule_digest",
            "_boundary_structure_digest",
        ):
            setattr(self, name, str(getattr(self, name, "")))
        self._boundary_request_digest_cache = dict(getattr(
            self, "_boundary_request_digest_cache", {}
        ))
        self._discovery_prefix_physical_fingerprint_set = frozenset(
            getattr(
                self,
                "discovery_prefix_physical_fingerprints",
                (),
            )
        )
        self._boundary_replay_active_promotion_ids = set(getattr(
            self, "_boundary_replay_active_promotion_ids", set()
        ))
        self._boundary_replay_promotions_by_generation = dict(getattr(
            self, "_boundary_replay_promotions_by_generation", {}
        ))
        self._boundary_replay_promotion_by_child = dict(getattr(
            self, "_boundary_replay_promotion_by_child", {}
        ))
        self._active_boundary_promotion_ids = set(getattr(
            self, "_active_boundary_promotion_ids", set()
        ))
        self._boundary_promotion_by_child = dict(getattr(
            self, "_boundary_promotion_by_child", {}
        ))
        self.boundary_promotion_requests = dict(getattr(
            self, "boundary_promotion_requests", {}
        ))
        self.adaptive_boundary_escrows = dict(getattr(
            self, "adaptive_boundary_escrows", {}
        ))
        self.retired_tombstones = dict(getattr(
            self, "retired_tombstones", {}
        ))
        self.structural_request_plans = dict(getattr(
            self, "structural_request_plans", {}
        ))
        for name in (
            "request_queue",
            "lifetime_requested_parent_ids",
            "generation_boundaries",
        ):
            value = getattr(self, name, ())
            if not isinstance(value, _AppendOnlyLedger):
                setattr(self, name, _AppendOnlyLedger(value))
        # Preserve the marker type across pickle/deepcopy.  A plain dict here
        # would make the next predecessor digest rebuild a filtered copy of
        # the complete state ledger even when the cached live view is current.
        self._live_authority_state_cache = _LiveAuthorityStateView(
            getattr(self, "_live_authority_state_cache", {})
        )
        restored_topology = getattr(self, "authority_topology", None)
        self._live_authority_state_cache.topology_schema_version = (
            restored_topology.get("topology_schema_version")
            if isinstance(restored_topology, Mapping)
            else None
        )
        self._requested_parent_index = set(getattr(
            self, "_requested_parent_index", set()
        ))
        self._pending_request_index = set(getattr(
            self, "_pending_request_index", set()
        ))
        pending_order = getattr(self, "_pending_request_order", None)
        if pending_order is None:
            # Older pickles do not carry this bounded cache.  Force one full
            # refresh before the next structural safe point rather than
            # deriving it from the lifetime queue on the hot path.
            self._pending_request_order = []
            self._hot_path_indexes_ready = False
        else:
            self._pending_request_order = list(pending_order)
        self._request_queue_hot_digest = str(getattr(
            self, "_request_queue_hot_digest", ""
        ))
        self._requested_parent_hot_digest = str(getattr(
            self, "_requested_parent_hot_digest", ""
        ))
        self._hot_path_revision = int(getattr(
            self, "_hot_path_revision", 0
        ))
        self._hot_path_indexes_ready = bool(getattr(
            self, "_hot_path_indexes_ready", False
        ))
        self._hot_structure_digest = str(getattr(
            self, "_hot_structure_digest", ""
        ))
        self._hot_boundary_promotion_digest = str(getattr(
            self, "_hot_boundary_promotion_digest", ""
        ))
        self._successor_capacity_occupant_ids = set(getattr(
            self, "_successor_capacity_occupant_ids", set()
        ))
        self._pending_child_birth_request_ids = set(getattr(
            self, "_pending_child_birth_request_ids", set()
        ))
        self._reserved_member_pairs = {
            tuple(item) for item in getattr(
                self, "_reserved_member_pairs", set()
            )
        }
        self._accepted_real_reference_order = list(getattr(
            self, "_accepted_real_reference_order", []
        ))
        self._accepted_real_prefix_witness_ids = tuple(getattr(
            self, "_accepted_real_prefix_witness_ids", ()
        ))
        self._accepted_real_reference_ordinals = list(getattr(
            self, "_accepted_real_reference_ordinals", []
        ))
        self._accepted_real_by_signal_identity = {
            str(identity): list(receipt_ids)
            for identity, receipt_ids in getattr(
                self, "_accepted_real_by_signal_identity", {}
            ).items()
        }

    @classmethod
    def from_organism(
        cls,
        source: TraceNativeCompetenceOrganism,
        *,
        mode: V2Mode,
        frontier: int | None = None,
        specialization_mode: SpecializationMode = SpecializationMode.DISCONNECTED,
        structural_epoch_schedule: Sequence[int] = (),
        structural_mode: StructuralMode = StructuralMode.SCHEDULED,
        event_driven: bool | None = None,
    ) -> "NativeProspectiveAuthorityV2":
        if frontier is not None:
            raise ProspectiveV2IntegrityError(
                "runner-supplied frontier is forbidden"
            )
        mode = V2Mode(mode)
        specialization_mode = SpecializationMode(specialization_mode)
        if event_driven is not None:
            requested_structural_mode = (
                StructuralMode.EVENT_DRIVEN
                if event_driven else StructuralMode.SCHEDULED
            )
            structural_mode = requested_structural_mode
        structural_mode = StructuralMode(structural_mode)
        schedule = tuple(map(int, structural_epoch_schedule))
        if tuple(sorted(set(schedule))) != schedule or any(
            item < 0 for item in schedule
        ):
            raise ProspectiveV2IntegrityError(
                "structural epoch schedule is not canonical"
            )
        if (
            structural_mode is StructuralMode.EVENT_DRIVEN
            and schedule
        ):
            raise ProspectiveV2IntegrityError(
                "event-driven structural mode cannot carry a schedule"
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
            structural_mode=structural_mode,
            boundary_digest_schema=BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN,
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
        compact_hypothesis_digest = None
        if (
            isinstance(cell.nomination_escrow, NominationEscrow)
            and cell.nomination_escrow.escrow_schema_version
            == NOMINATION_ESCROW_V4
        ):
            compact_hypothesis_digest = getattr(
                cell, "immutable_hypothesis_digest", None
            )
        return CellStructuralInvariant(
            cell_id=cell.cell_id,
            members=tuple(cell.members),
            polarity=AvailabilityState(cell.polarity),
            lineage_parent_id=cell.lineage_parent_id,
            specialization_depth=cell.specialization_depth,
            structural_state=cell.state.name,
            authority_node_ids=_cell_node_ids(cell.cell_id),
            authority_topology_identity=_cell_topology_identity(
                cell.cell_id, compact_hypothesis_digest
            ),
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

    def _canonical_structure_invariant_digest(self) -> str:
        """Hash the current structural topology once at a safe point.

        New authorities carry a mutation-chain projection of this value for
        chronological replay.  Keeping the canonical calculation separate
        prevents a replay boundary from accidentally re-scanning the full
        lifetime ledgers merely to validate a predecessor.
        """

        return _sha({
            "live": self._structural_manifest(),
            "authority_topology": self.authority_topology,
            "tombstones": self.historical_tombstones,
            "retired_tombstones": self.retired_tombstones,
        })

    def _structure_invariant_digest(self) -> str:
        if getattr(self, "boundary_digest_schema", BOUNDARY_DIGEST_SCHEMA_LEGACY) == (
            BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
        ):
            structure_digest = getattr(self, "_boundary_structure_digest", "")
            if structure_digest:
                return structure_digest
        return self._canonical_structure_invariant_digest()

    @staticmethod
    def _boundary_decision_row(
        cell_id: str,
        state: ProspectiveAuthorityState,
    ) -> dict[str, Any]:
        def ledger_tail(values: Sequence[Any]) -> dict[str, Any]:
            # Boundary decisions are emitted on the REAL hot path.  Counts
            # and the newest entry are enough to bind the append-only prefix
            # because the complete ledgers are independently reclosed at an
            # explicit full boundary; materializing ``list(values)`` here
            # would rescan lifetime evidence for every event.
            return {
                "count": len(values),
                "last": None if not values else values[-1],
            }

        return {
            "cell_id": cell_id,
            "prospectively_certified": state.prospectively_certified,
            "transition_rows": ledger_tail(state.transition_rows),
            "support_receipt_ids": ledger_tail(state.support_receipt_ids),
            "contradiction_receipt_ids": ledger_tail(
                state.contradiction_receipt_ids
            ),
        }

    def _boundary_seed_accepted_real_digest(self) -> str:
        values = [
            item.manifest() for item in sorted(
                self.accepted_real_references.values(),
                key=lambda row: (row.ordinal, row.receipt_id),
            )
        ]
        return self._append_log_digest(
            values, kind="boundary_accepted_real"
        )

    def _boundary_seed_candidate_digest(self) -> str:
        epoch = self.base.envelope.nomination_epoch
        if epoch is None:
            raise ProspectiveV2IntegrityError(
                "prospective discovery epoch is absent"
            )
        return _sha({
            "hypotheses": {
                key: value.hypothesis.manifest()
                for key, value in sorted(self.states.items())
            },
            "tombstones": self.historical_tombstones,
            "retired_tombstones": self.retired_tombstones,
            "epoch_candidate_manifest_digest": (
                epoch.frozen_candidate_manifest_digest
            ),
        })

    def _boundary_seed_decision_digest(self) -> str:
        return _sha({
            cell_id: self._boundary_decision_row(cell_id, state)
            for cell_id, state in sorted(self.states.items())
        })

    @staticmethod
    def _advance_boundary_field_digest(
        previous: str,
        *,
        field: str,
        operation: str,
        payload: Mapping[str, Any] | Sequence[Any] | str,
    ) -> str:
        return _sha({
            "schema_version": BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN,
            "field": field,
            "previous": previous,
            "operation": operation,
            "payload": payload,
        })

    def _boundary_commitment_origin_payload(self) -> dict[str, Any]:
        """Return the immutable post-nomination seed for the chain.

        The seed is intentionally a flat canonical manifest computed once at
        authority initialization.  It excludes only the append-only boundary
        log and the chain's own mutable bookkeeping; every later durable
        mutation is represented by an operation record in the chain.
        """

        manifest = self.continuation_manifest()
        for key in (
            "generation_boundaries",
            "boundary_commitment_origin_digest",
            "boundary_commitment_digest",
            "boundary_commitment_count",
            "boundary_accepted_real_digest",
            "boundary_candidate_digest",
            "boundary_decision_digest",
            "boundary_schedule_digest",
            "boundary_structure_digest",
        ):
            manifest.pop(key, None)
        return {
            "schema_version": BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN,
            "manifest": manifest,
        }

    def _active_mutation_journal(self) -> _RealMutationJournal | None:
        """Return the current reversible transaction, if any."""

        structural = getattr(self, "_structural_mutation_journal", None)
        if structural is not None:
            return structural
        return getattr(self, "_real_mutation_journal", None)

    def _mutation_set_attr(self, owner: Any, name: str, value: Any) -> None:
        journal = self._active_mutation_journal()
        if journal is None:
            setattr(owner, name, value)
        else:
            journal.set_attr(owner, name, value)

    def _mutation_append(self, values: list[Any], value: Any) -> None:
        journal = self._active_mutation_journal()
        if journal is None:
            values.append(value)
        else:
            journal.append(values, value)

    def _mutation_add_mapping(
        self,
        mapping: dict[Any, Any],
        key: Any,
        value: Any,
    ) -> None:
        journal = self._active_mutation_journal()
        if journal is None:
            mapping[key] = value
        else:
            journal.add_mapping(mapping, key, value)

    def _mutation_delete_mapping(
        self,
        mapping: dict[Any, Any],
        key: Any,
    ) -> None:
        journal = self._active_mutation_journal()
        if journal is None:
            mapping.pop(key, None)
        elif isinstance(journal, _StructuralMutationJournal):
            journal.delete_mapping(mapping, key)
        else:
            if key not in mapping:
                return
            old = mapping[key]
            journal._undo.append(
                lambda mapping=mapping, key=key, old=old: mapping.__setitem__(
                    key, old
                )
            )
            del mapping[key]

    def _mutation_pop_mapping(
        self,
        mapping: dict[Any, Any],
        key: Any,
        default: Any = None,
    ) -> Any:
        if key not in mapping:
            return default
        value = mapping[key]
        self._mutation_delete_mapping(mapping, key)
        return value

    def _mutation_remove_list_item(
        self,
        values: list[Any],
        value: Any,
    ) -> None:
        journal = self._active_mutation_journal()
        if journal is None:
            try:
                values.remove(value)
            except ValueError:
                pass
        elif isinstance(journal, _StructuralMutationJournal):
            journal.remove_list_item(values, value)
        else:
            try:
                index = values.index(value)
            except ValueError:
                return
            old = values[index]
            journal._undo.append(
                lambda values=values, index=index, old=old: values.insert(
                    index, old
                )
            )
            values.pop(index)

    def _mutation_add_set(self, values: set[Any], value: Any) -> None:
        journal = self._active_mutation_journal()
        if journal is None:
            values.add(value)
        else:
            journal.add_set(values, value)

    def _mutation_discard_set(self, values: set[Any], value: Any) -> None:
        journal = self._active_mutation_journal()
        if journal is None:
            values.discard(value)
        elif isinstance(journal, _StructuralMutationJournal):
            journal.discard_set(values, value)
        elif value in values:
            # The REAL journal currently only needs additive set entries;
            # retaining this branch keeps its rollback semantics explicit.
            journal._undo.append(
                lambda values=values, value=value: values.add(value)
            )
            values.discard(value)

    def _initialize_boundary_commitment(self) -> None:
        """Initialize the versioned chain exactly once after nomination."""

        if self.boundary_digest_schema != (
            BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
        ):
            return
        origin = _sha(self._boundary_commitment_origin_payload())
        existing = getattr(self, "_boundary_commitment_origin_digest", "")
        if existing and existing != origin:
            raise ProspectiveV2IntegrityError(
                "generation-boundary commitment origin changed"
            )
        self._boundary_commitment_origin_digest = origin
        self._boundary_commitment_digest = origin
        self._boundary_commitment_count = 0
        self._boundary_accepted_real_digest = (
            self._boundary_seed_accepted_real_digest()
        )
        self._boundary_candidate_digest = (
            self._boundary_seed_candidate_digest()
        )
        self._boundary_decision_digest = (
            self._boundary_seed_decision_digest()
        )
        self._boundary_schedule_digest = _sha(
            list(self.structural_epoch_schedule)
        )
        self._boundary_structure_digest = (
            self._canonical_structure_invariant_digest()
        )
        self._boundary_request_digest_cache = {}

    def _advance_boundary_commitment(
        self,
        operation: str,
        payload: Mapping[str, Any] | Sequence[Any] | str,
    ) -> None:
        """Append one canonical durable mutation to the boundary chain.

        This is deliberately an append-only SHA operation log, not the
        incremental predecessor digest used by REAL admission.  The latter
        is a hot-path projection; this chain is the versioned commitment used
        for exact boundary chronology.  Final full-manifest equality remains
        the independent closure for fields not represented by a delta.
        """

        if self.boundary_digest_schema != (
            BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
        ):
            return
        if not getattr(self, "_boundary_commitment_origin_digest", ""):
            self._initialize_boundary_commitment()
        count = int(getattr(self, "_boundary_commitment_count", 0))
        previous = getattr(self, "_boundary_commitment_digest", "")
        if not previous:
            raise ProspectiveV2IntegrityError(
                "generation-boundary commitment is uninitialized"
            )
        new_digest = _sha({
            "schema_version": BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN,
            "position": count,
            "previous": previous,
            "operation": operation,
            "payload": payload,
        })
        self._mutation_set_attr(
            self, "_boundary_commitment_digest", new_digest
        )
        self._mutation_set_attr(
            self, "_boundary_commitment_count", count + 1
        )

    @staticmethod
    def _boundary_structural_consumption_payload(
        consumption: StructuralRequestConsumption,
    ) -> dict[str, Any]:
        """Return the pre-materialization identity committed at consumption.

        The compatibility API records a request consumption before its child
        is materialized, then upgrades the durable disposition to
        ``MATERIALIZED``.  Replay sees the final ledger, so the chain payload
        must use the immutable pre-materialization disposition in both paths.
        The final continuation still binds the upgraded disposition itself.
        """

        payload = consumption.manifest()
        if payload["disposition"] == "MATERIALIZED":
            payload["disposition"] = "PENDING_CHILD"
        return payload

    def _record_boundary_accepted_real(
        self, reference: AcceptedRealReference
    ) -> None:
        if self.boundary_digest_schema != (
            BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
        ):
            return
        previous = self._boundary_accepted_real_digest
        if not previous:
            previous = self._boundary_seed_accepted_real_digest()
        self._mutation_set_attr(
            self,
            "_boundary_accepted_real_digest",
            _next_hot_append_digest(
                previous,
                "boundary_accepted_real",
                reference.manifest(),
                len(self.accepted_real_references),
            ),
        )

    def _record_boundary_candidate(
        self,
        operation: str,
        payload: Mapping[str, Any] | Sequence[Any] | str,
    ) -> None:
        if self.boundary_digest_schema != (
            BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
        ):
            return
        previous = self._boundary_candidate_digest
        if not previous:
            previous = self._boundary_seed_candidate_digest()
        self._mutation_set_attr(
            self,
            "_boundary_candidate_digest",
            self._advance_boundary_field_digest(
                previous,
                field="candidate_manifest",
                operation=operation,
                payload=payload,
            ),
        )

    def _record_boundary_decision(
        self,
        operation: str,
        payload: Mapping[str, Any] | Sequence[Any] | str,
    ) -> None:
        if self.boundary_digest_schema != (
            BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
        ):
            return
        previous = self._boundary_decision_digest
        if not previous:
            previous = self._boundary_seed_decision_digest()
        self._mutation_set_attr(
            self,
            "_boundary_decision_digest",
            self._advance_boundary_field_digest(
                previous,
                field="parent_decision_history",
                operation=operation,
                payload=payload,
            ),
        )

    def _record_boundary_structure(
        self,
        operation: str,
        payload: Mapping[str, Any] | Sequence[Any] | str,
    ) -> None:
        """Advance the structural commitment after one topology mutation.

        ``structure_invariant_digest`` is used by REAL transactions.  The
        canonical structural manifest is seeded once after nomination; each
        later child birth or retirement advances this independent chain with
        its exact local mutation payload.  Replay can therefore reclose
        transaction structure digests without rebuilding a lifetime manifest
        at every generation boundary.
        """

        if self.boundary_digest_schema != (
            BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
        ):
            return
        previous = self._boundary_structure_digest
        if not previous:
            previous = self._canonical_structure_invariant_digest()
        new_digest = self._advance_boundary_field_digest(
            previous,
            field="structure_invariant",
            operation=operation,
            payload=payload,
        )
        self._mutation_set_attr(
            self,
            "_boundary_structure_digest",
            new_digest,
        )
        # REAL admission compares against the same commitment that replay
        # uses for structure reclosure.  Keep this bounded projection in sync
        # with the chain while the structural journal can still roll it back.
        self._mutation_set_attr(self, "_hot_structure_digest", new_digest)

    def _refresh_active_boundary_promotion_digest(
        self,
        active_ids: set[str],
    ) -> None:
        """Refresh the bounded active-promotion projection in O(capacity)."""

        self._mutation_set_attr(
            self,
            "_hot_boundary_promotion_digest",
            _sha({
                candidate_id: self.boundary_promotion_requests[
                    candidate_id
                ].manifest()
                for candidate_id in sorted(active_ids)
            }),
        )

    def _boundary_replay_refresh_promotion_digest(self) -> None:
        self._refresh_active_boundary_promotion_digest(
            self._boundary_replay_active_promotion_ids
        )

    def _boundary_replay_add_live_state(
        self,
        replay: "NativeProspectiveAuthorityV2",
        cell_id: str,
    ) -> None:
        """Apply one replayed birth to the bounded live-state index."""

        replay._live_authority_state_cache[cell_id] = replay.states[cell_id]
        replay._successor_capacity_occupant_ids.add(cell_id)
        replay._hot_structure_digest = replay._boundary_structure_digest

    def _boundary_replay_retire_live_state(
        self,
        replay: "NativeProspectiveAuthorityV2",
        cell_id: str,
    ) -> None:
        """Apply one replayed retirement to the bounded live index."""

        replay._live_authority_state_cache.pop(cell_id, None)
        replay._successor_capacity_occupant_ids.discard(cell_id)
        candidate_id = replay._boundary_replay_promotion_by_child.get(
            cell_id
        )
        if candidate_id is not None:
            replay._boundary_replay_active_promotion_ids.discard(
                candidate_id
            )
            replay._boundary_replay_refresh_promotion_digest()
        replay._hot_structure_digest = replay._boundary_structure_digest

    def _boundary_queue_digest(self, request_ids: Sequence[str]) -> str:
        """Digest one canonical queue projection with one-entry memoization."""

        ids = tuple(request_ids)
        if self.boundary_digest_schema != (
            BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
        ):
            return self._request_queue_digest(ids)
        cached = self._boundary_request_digest_cache.get(ids)
        if cached is not None:
            return cached
        digest = self._append_log_digest(
            [self.deferred_requests[item].manifest() for item in ids],
            kind="boundary_request_queue",
        )
        # Only the current projection is useful on a hot safe point.  Keeping
        # every historical queue tuple here would turn a bounded cache into a
        # second lifetime ledger and make it grow once per boundary.
        journal = self._active_mutation_journal()
        replacement = {ids: digest}
        if journal is None:
            self._boundary_request_digest_cache = replacement
        else:
            self._mutation_set_attr(
                self, "_boundary_request_digest_cache", replacement
            )
        return digest

    def _boundary_prior_continuation_digest(self) -> str:
        """Return the exact versioned boundary prior commitment."""

        if self.boundary_digest_schema == (
            BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
        ):
            if not getattr(self, "_boundary_commitment_origin_digest", ""):
                self._initialize_boundary_commitment()
            return self._boundary_commitment_digest
        return self.continuation_digest()

    def _append_generation_boundary(self, boundary: GenerationBoundary) -> None:
        """Persist one boundary and commit its complete canonical fields."""

        if not isinstance(self.generation_boundaries, _AppendOnlyLedger):
            self._mutation_set_attr(
                self,
                "generation_boundaries",
                _AppendOnlyLedger(self.generation_boundaries),
            )
        journal = self._active_mutation_journal()
        if journal is None:
            self.generation_boundaries.append(boundary)
        else:
            journal.append(self.generation_boundaries, boundary)
        self._advance_boundary_commitment(
            "generation_boundary", boundary.manifest()
        )

    @staticmethod
    def _append_log_digest(
        values: Sequence[Any],
        *,
        kind: str,
    ) -> str:
        """Build a rolling digest at a full boundary or after restoration."""

        digest = _empty_hot_append_digest(kind)
        for count, value in enumerate(values, 1):
            digest = _next_hot_append_digest(
                digest, kind, value, count
            )
        return digest

    def _refresh_hot_path_indexes(self) -> None:
        """Rebuild runtime indexes at a structural/full-history boundary."""

        # Keep the canonical tuple and its exact membership projection
        # separate: the former is serialized and reclosed, while the latter
        # makes discovery-evidence exclusion O(1) on each REAL event.
        self._discovery_prefix_physical_fingerprint_set = frozenset(
            self.discovery_prefix_physical_fingerprints
        )
        live_states = {
            cell_id: state
            for cell_id, state in self.states.items()
            if not getattr(state, "retired", False)
        }
        self._live_authority_state_cache = _LiveAuthorityStateView(
            live_states
        )
        prior_topology_schema = None
        if isinstance(self.authority_topology, Mapping):
            prior_topology_schema = self.authority_topology.get(
                "topology_schema_version"
            )
        self._live_authority_state_cache.topology_schema_version = (
            prior_topology_schema
        )
        self._successor_capacity_occupant_ids = {
            cell_id for cell_id, state in live_states.items()
            if state.hypothesis.source_generation > 0
        }
        self._successor_capacity_occupant_ids.update(
            birth.child_cell_id
            for birth in self.deferred_child_births.values()
            if birth.child_cell_id not in getattr(
                self, "retired_tombstones", {}
            )
        )
        self._pending_child_birth_request_ids = {
            request_id
            for request_id, birth in self.deferred_child_births.items()
            if birth.disposition == "PENDING_MATERIALIZATION"
        }
        self._reserved_member_pairs = {
            tuple(state.hypothesis.members)
            for state in self.states.values()
        }
        self._reserved_member_pairs.update(
            tuple(birth.members)
            for birth in self.deferred_child_births.values()
        )
        self._reserved_member_pairs.update(
            tuple(consumption.selected_members)
            for consumption in self.request_consumptions.values()
            if consumption.selected_members
        )
        self._requested_parent_index = set(
            self.lifetime_requested_parent_ids
        )
        # Keep the deterministic append order separately from the lifetime
        # queue.  The queue is retained forever for replay, whereas this
        # order contains only the currently pending (bounded) requests.  A
        # full boundary is the one place where rebuilding it may scan the
        # historical queue; event-driven safe points consume this cache.
        self._pending_request_order = [
            request_id for request_id in self.request_queue
            if request_id not in self.request_consumptions
        ]
        self._pending_request_index = set(self._pending_request_order)
        self._request_queue_hot_digest = self._append_log_digest(
            self.request_queue,
            kind="request_queue",
        )
        self._accepted_real_reference_order = [
            reference.receipt_id
            for reference in sorted(
                self.accepted_real_references.values(),
                key=lambda item: (item.ordinal, item.receipt_id),
            )
        ]
        self._accepted_real_prefix_witness_ids = (
            _bounded_provenance_witnesses(
                self._accepted_real_reference_order
            )
        )
        self._accepted_real_reference_ordinals = [
            self.accepted_real_references[receipt_id].ordinal
            for receipt_id in self._accepted_real_reference_order
        ]
        by_signal: dict[str, list[str]] = {}
        for reference in self.accepted_real_references.values():
            for identity in reference.ordered_signal_identities:
                by_signal.setdefault(identity, []).append(
                    reference.receipt_id
                )
        self._accepted_real_by_signal_identity = {
            identity: _AppendOnlyLedger(receipt_ids)
            for identity, receipt_ids in by_signal.items()
        }
        self._requested_parent_hot_digest = self._append_log_digest(
            self.lifetime_requested_parent_ids,
            kind="requested_parent",
        )
        active_boundary_promotions = {}
        promotion_by_child = {}
        for candidate_id, request in sorted(
            getattr(self, "boundary_promotion_requests", {}).items()
        ):
            child_id = self._adaptive_boundary_child_id(request)
            promotion_by_child[child_id] = candidate_id
            if child_id in self._live_authority_state_cache:
                active_boundary_promotions[candidate_id] = request.manifest()
        self._active_boundary_promotion_ids = set(active_boundary_promotions)
        self._boundary_promotion_by_child = promotion_by_child
        self._hot_boundary_promotion_digest = _sha(
            active_boundary_promotions
        )
        self._hot_path_indexes_ready = True
        self._hot_path_revision = int(getattr(self, "_hot_path_revision", 0)) + 1
        self._hot_structure_digest = self._structure_invariant_digest()

    def _ensure_hot_path_indexes(self) -> None:
        if not getattr(self, "_hot_path_indexes_ready", False):
            # Normal authorities reach this through from_organism()'s full
            # boundary check or loads().  The fallback keeps hand-built test
            # fixtures safe; it is intentionally never taken per event after
            # initialization.
            self._refresh_hot_path_indexes()

    def _hot_live_states(self) -> Mapping[str, ProspectiveAuthorityState]:
        self._ensure_hot_path_indexes()
        return self._live_authority_state_cache

    def _hot_path_guard_digest(self) -> str:
        """Cheap mutation guard over only live topology and scalar ledgers."""

        self._ensure_hot_path_indexes()
        live = self._live_authority_state_cache
        lifecycle = {
            cell_id: {
                "hypothesis_digest": state.hypothesis.hypothesis_digest,
                "prospectively_certified": bool(
                    state.prospectively_certified
                ),
                "successes": int(state.successes),
                "contradictions": int(state.contradictions),
                "support": int(state.support),
                "success_lower_bound": state.success_lower_bound,
                "contradiction_lower_bound": (
                    state.contradiction_lower_bound
                ),
                "certification_count": len(state.certification_receipt_ids),
                "last_certification": (
                    state.certification_receipt_ids[-1]
                    if state.certification_receipt_ids else None
                ),
                "support_count": len(state.support_receipt_ids),
                "last_support": (
                    state.support_receipt_ids[-1]
                    if state.support_receipt_ids else None
                ),
                "contradiction_count": len(
                    state.contradiction_receipt_ids
                ),
                "last_contradiction": (
                    state.contradiction_receipt_ids[-1]
                    if state.contradiction_receipt_ids else None
                ),
                "transition_count": len(state.transition_rows),
                "last_transition": (
                    state.transition_rows[-1]
                    if state.transition_rows else None
                ),
            }
            for cell_id, state in sorted(live.items())
        }
        history = self.incremental_history_state
        return _sha({
            "schema_version": INCREMENTAL_HISTORY_SCHEMA,
            "revision": int(self._hot_path_revision),
            "generation": int(self.current_generation),
            "phase": GenerationPhase(self.generation_phase).value,
            "next_ordinal": int(self.next_expected_ordinal),
            "evaluation_sealed": bool(self.evaluation_sealed),
            "structure_digest": getattr(self, "_hot_structure_digest", ""),
            "boundary_promotion_digest": (
                self._hot_boundary_promotion_digest
            ),
            "request_queue_digest": self._request_queue_hot_digest,
            "request_queue_count": len(self.request_queue),
            "pending_request_count": len(self._pending_request_index),
            "requested_parent_digest": self._requested_parent_hot_digest,
            "requested_parent_count": len(
                self.lifetime_requested_parent_ids
            ),
            "history": (
                None if history is None else {
                    "event_count": history.event_count,
                    "last_ordinal": history.last_ordinal,
                    "last_receipt_id": history.last_receipt_id,
                    "last_event_digest": history.last_event_digest,
                    "history_digest": history.history_digest,
                }
            ),
            "consumed_count": len(self.consumed_receipts),
            "reference_count": len(self.accepted_real_references),
            "transaction_count": len(self.event_transactions),
            "pending_token": (
                None if self.pending_event is None
                else self.pending_event.pending_token
            ),
            **({"boundary_hypothesis_birth_digest": self._boundary_hypothesis_birth_digest}
               if self.boundary_hypothesis_births else {}),
            "live_lifecycle": lifecycle,
        })

    def _validate_real_hot_path(
        self,
        *,
        require_pending: bool = False,
        frozen_base_continuation_digest: str | None = None,
        virtual: bool = False,
    ) -> None:
        """Validate cheap local contracts before one REAL transaction.

        Full topology/history reconstruction is reserved for explicit
        structural, serialization, and ``verify_full_history_boundary`` calls.
        This validator checks only fixed source identity, scalar cardinalities,
        the cached bounded live view, and the one pending transaction.
        """

        self._ensure_hot_path_indexes()
        if self.schema_version != SCHEMA_VERSION:
            raise ProspectiveV2IntegrityError("unsupported V2 schema")
        if (
            not virtual
            and GenerationPhase(self.generation_phase)
            is not GenerationPhase.PROSPECTIVE_OPEN
        ):
            raise ProspectiveV2IntegrityError(
                "REAL event outside PROSPECTIVE_OPEN"
            )
        if not virtual and self.evaluation_sealed:
            raise ProspectiveV2IntegrityError(
                "sealed evaluation cannot consume evidence"
            )
        epoch = self.base.envelope.nomination_epoch
        if epoch is None or (not virtual and not epoch.nomination_closed):
            raise ProspectiveV2IntegrityError(
                "first certification event requires closed nomination"
            )
        if frozen_base_continuation_digest is not None:
            # A frame session already captured this immutable digest.  The
            # session's R0 close check owns the expensive source reclosure;
            # merely require a well-formed digest here.
            if len(str(frozen_base_continuation_digest)) != 64:
                raise ProspectiveV2IntegrityError(
                    "frozen base continuation digest is malformed"
                )
        history = self.incremental_history_state
        count = len(self.consumed_receipts)
        if history is None:
            if count:
                raise ProspectiveV2IntegrityError(
                    "incremental history missing for accepted REAL events"
                )
        elif (
            history.schema_version != INCREMENTAL_HISTORY_SCHEMA
            or history.event_count != count
            or self.next_expected_ordinal
            != history.first_ordinal + history.event_count
            or len(history.history_digest) != 64
        ):
            raise ProspectiveV2IntegrityError(
                "incremental history scalar state mismatch"
            )
        if (
            len(self.consumed_tokens) != count
            or len(self.prospective_physical_fingerprints) != count
            or len(self.emissions) != count
            or len(self.accepted_real_references)
            != len(self.base.receipts) + count
        ):
            raise ProspectiveV2IntegrityError(
                "REAL ledger cardinality mismatch"
            )
        if len(self._live_authority_state_cache) > (
            len(self.states)
        ):
            raise ProspectiveV2IntegrityError(
                "live authority index exceeds state ledger"
            )
        pending = self.pending_event
        if pending is None:
            if require_pending:
                raise ProspectiveV2IntegrityError("receipt before prediction")
            if len(self.event_transactions) != count:
                raise ProspectiveV2IntegrityError(
                    "transaction ledger cardinality mismatch"
                )
            return
        if (
            pending.state != "OPEN"
            or pending.ordinal != self.next_expected_ordinal
            or pending.structure_invariant_digest
            != getattr(self, "_hot_structure_digest", "")
            or self.event_transactions.get(pending.pending_token)
            != pending.manifest()
        ):
            raise ProspectiveV2IntegrityError(
                "pending REAL transaction local identity mismatch"
            )
        if history is not None and pending.predecessor_continuation_digest != (
            self._incremental_predecessor_continuation_digest()
        ):
            raise ProspectiveV2IntegrityError(
                "incremental pending predecessor disagreement"
            )
        if len(self.event_transactions) != count + 1:
            raise ProspectiveV2IntegrityError(
                "transaction ledger cardinality mismatch"
            )

    def _validate_structural_hot_path(
        self,
        *,
        expected_authority_topology: Mapping[str, Any] | None = None,
    ) -> None:
        """Validate one event-driven structural commit without reclosure.

        Structural safe points already have a bounded mutation journal and
        maintain the live/request/capacity projections incrementally.  A
        full invariant pass here would scan append-only state and evidence
        ledgers once per budding event, recreating the lifetime-quadratic
        behavior this journal is meant to remove.  Full canonical replay is
        still required at explicit load/checkpoint/audit boundaries.
        """

        if self.structural_mode is not StructuralMode.EVENT_DRIVEN:
            raise ProspectiveV2IntegrityError(
                "structural hot validation requires event-driven mode"
            )
        if self.generation_phase is not GenerationPhase.PROSPECTIVE_OPEN:
            raise ProspectiveV2IntegrityError(
                "structural hot validation requires PROSPECTIVE_OPEN"
            )
        if self.pending_event is not None or self.evaluation_sealed:
            raise ProspectiveV2IntegrityError(
                "structural hot validation requires a quiescent authority"
            )
        if not getattr(self, "_hot_path_indexes_ready", False):
            raise ProspectiveV2IntegrityError(
                "structural hot indexes are not initialized"
            )
        pending_order = self._pending_request_order
        pending_index = self._pending_request_index
        if (
            len(pending_order) != len(pending_index)
            or len(pending_order) > REQUEST_QUEUE_CAPACITY
            or len(set(pending_order)) != len(pending_order)
            or set(pending_order) != pending_index
        ):
            raise ProspectiveV2IntegrityError(
                "pending structural request projection is inconsistent"
            )
        occupancy = self._successor_capacity_occupant_ids
        if len(occupancy) > DORMANT_SPECIALIZATION_CHILD_CAPACITY:
            raise ProspectiveV2IntegrityError(
                "successor capacity projection exceeds bounded pool"
            )
        pending_births = self._pending_child_birth_request_ids
        if len(pending_births) > len(occupancy):
            raise ProspectiveV2IntegrityError(
                "pending child projection exceeds successor occupancy"
            )
        for request_id in pending_births:
            birth = self.deferred_child_births.get(request_id)
            if (
                birth is None
                or birth.disposition != "PENDING_MATERIALIZATION"
                or birth.child_cell_id not in occupancy
            ):
                raise ProspectiveV2IntegrityError(
                    "pending child projection has no live reservation"
                )
        for cell_id in occupancy:
            state = self._live_authority_state_cache.get(cell_id)
            if state is not None and getattr(state, "retired", False):
                raise ProspectiveV2IntegrityError(
                    "retired state remains in live structural projection"
                )
        active_promotions = self._active_boundary_promotion_ids
        if not active_promotions.issubset(
            self.boundary_promotion_requests
        ):
            raise ProspectiveV2IntegrityError(
                "active promotion projection names an unknown request"
            )
        ordinary_live = {
            cell_id for cell_id, state in self._live_authority_state_cache.items()
            if (
                state.hypothesis.dormant_origin
                is DormantOrigin.ADAPTIVE_BOUNDARY_CHILD
            )
        }
        if not ordinary_live.issubset(self._boundary_promotion_by_child):
            raise ProspectiveV2IntegrityError(
                "ordinary child missing promotion index"
            )
        if (
            self.boundary_digest_schema == BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
            and self._hot_structure_digest
            != self._boundary_structure_digest
        ):
            raise ProspectiveV2IntegrityError(
                "hot structure digest differs from structural commitment"
            )
        if expected_authority_topology is not None and (
            self.authority_topology != expected_authority_topology
        ):
            raise ProspectiveV2IntegrityError(
                "event-driven topology differs from committed safe point"
            )

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
            "retired_tombstones": copy.deepcopy(self.retired_tombstones),
            "epoch_close": epoch.manifest(),
            "executed_authority_topology": copy.deepcopy(
                self.authority_topology
            ),
        }
        unsigned = {
            "schema_version": self.schema_version,
            "implementation_identity": IMPLEMENTATION_IDENTITY,
            "mode": self.mode.value,
            "structural_mode": self.structural_mode.value,
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
            "structural_mode": self.structural_mode.value,
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
            "retired": bool(getattr(state, "retired", False)),
            "retirement_generation": getattr(
                state, "retirement_generation", None
            ),
            "retirement_ordinal": getattr(state, "retirement_ordinal", None),
            "retirement_reason": getattr(state, "retirement_reason", None),
            "retirement_tombstone_digest": getattr(
                state, "retirement_tombstone_digest", None
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
        request_queue_digest: str | None = None,
        requested_parent_digest: str | None = None,
        boundary_promotion_digest: str | None = None,
        hypothesis_birth_digest: str = "",
    ) -> str:
        active = (
            states
            if isinstance(states, _LiveAuthorityStateView)
            else {
                cell_id: state for cell_id, state in states.items()
                if state.hypothesis.source_generation <= generation
                and not getattr(state, "retired", False)
            }
        )
        topology_states: Mapping[str, ProspectiveAuthorityState] = active
        if not isinstance(states, _LiveAuthorityStateView) and any(
            state.hypothesis.source_generation <= generation
            and state.hypothesis.provenance_schema_version
            == PROVENANCE_COMMITMENT_V4
            for state in states.values()
        ):
            # Replay filters retired states out of ``active`` before deriving
            # the predecessor digest.  Compact topology is nevertheless a
            # sticky representation choice once a V4 state has existed in
            # this generation; otherwise retiring the last V4 leaf would
            # make replay silently fall back to the legacy full snapshot.
            compact_active = _LiveAuthorityStateView(active)
            compact_active.topology_schema_version = (
                "native_v2_authority_topology.v2_digest_only"
            )
            topology_states = compact_active
        if request_queue_digest is None:
            request_queue_digest = self._append_log_digest(
                request_ids,
                kind="request_queue",
            )
        if requested_parent_digest is None:
            requested_parent_digest = self._append_log_digest(
                lifetime_requested_parent_ids,
                kind="requested_parent",
            )
        if boundary_promotion_digest is None:
            if isinstance(states, _LiveAuthorityStateView):
                boundary_promotion_digest = (
                    self._hot_boundary_promotion_digest
                )
            else:
                boundary_promotion_digest = _sha({
                    candidate_id: request.manifest()
                    for candidate_id, request in sorted(
                        self.boundary_promotion_requests.items()
                    )
                    if (
                        self._adaptive_boundary_child_id(request)
                        in active
                    )
                })
        result = {
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
                _executed_authority_topology_manifest(topology_states)
            ),
            # Rolling digests retain the exact append order while avoiding a
            # lifetime list materialization on each REAL predecessor check.
            "request_ids_digest": request_queue_digest,
            "request_ids_count": len(request_ids),
            "lifetime_requested_parent_digest": requested_parent_digest,
            "lifetime_requested_parent_count": len(
                lifetime_requested_parent_ids
            ),
            "adaptive_boundary_promotions_digest": boundary_promotion_digest,
        }
        if hypothesis_birth_digest:
            result["boundary_hypothesis_birth_digest"] = hypothesis_birth_digest
        return _sha(result)

    def _incremental_predecessor_continuation_digest(
        self,
        history: IncrementalHistoryValidationState | None = None,
    ) -> str:
        history = (
            self.incremental_history_state
            if history is None
            else history
        )
        if history is None:
            raise ProspectiveV2IntegrityError(
                "incremental history is not initialized"
            )
        return self._incremental_predecessor_digest_from_parts(
            history=history,
            states=self._hot_live_states(),
            generation=self.current_generation,
            next_ordinal=self.next_expected_ordinal,
            request_ids=self.request_queue,
            lifetime_requested_parent_ids=self.lifetime_requested_parent_ids,
            request_queue_digest=self._request_queue_hot_digest,
            requested_parent_digest=self._requested_parent_hot_digest,
            boundary_promotion_digest=(
                self._hot_boundary_promotion_digest
            ),
            hypothesis_birth_digest=self._boundary_hypothesis_birth_digest,
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
        next_history = self._next_incremental_history_state(
            prior,
            receipt=receipt,
            transaction=transaction,
            reference=reference,
            emission=emission,
        )
        journal = getattr(self, "_real_mutation_journal", None)
        if journal is None:
            self.incremental_history_state = next_history
        else:
            journal.set_attr(
                self, "incremental_history_state", next_history
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
            self._verify_generation_boundary_replay()
            self._verify_deferred_specialization_requests(
                reconstruct_evidence=True
            )
            self._verify_boundary_promotion_request_history()
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
        protected_parents = self._retirement_protected_parent_ids()
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
            if (
                getattr(state, "retired", False)
                and request.parent_cell_id
                in protected_parents
            ):
                raise ProspectiveV2IntegrityError(
                    "specialization request parent retired before its "
                    "live dependency was released"
                )
            hypothesis = state.hypothesis
            compact_request = request.provenance_schema_version == (
                PROVENANCE_COMMITMENT_V4
            )
            if compact_request:
                expected_parent_query_commitment = _compact_query_digest({
                    "parent_cell_id": request.parent_cell_id,
                    "parent_hypothesis_digest": (
                        request.parent_hypothesis_digest
                    ),
                    "triggering_receipt_id": (
                        request.request_emission_receipt_id
                    ),
                    "contradiction_receipt_id": (
                        request.contradiction_receipt_id
                    ),
                    "specialization_mode": (
                        request.specialization_mode.value
                    ),
                })
                if request.parent_query_commitment != (
                    expected_parent_query_commitment
                ):
                    raise ProspectiveV2IntegrityError(
                        "specialization request parent query commitment mismatch"
                    )
                expected_parent_discovery = (
                    hypothesis.discovery_read_commitment
                )
                if expected_parent_discovery is None:
                    expected_parent_discovery = ProvenanceCommitment(
                        schema_version=PROVENANCE_COMMITMENT_V4,
                        digest=hypothesis.discovery_receipt_digest,
                        count=len(hypothesis.discovery_receipt_ids),
                        exclusive_frontier=(
                            hypothesis.certification_frontier + 1
                        ),
                        witness_ids=_bounded_provenance_witnesses(
                            hypothesis.discovery_receipt_ids
                        ),
                    )
                expected_parent_support = dict(
                    hypothesis.nomination_read_commitments
                ).get("parent_discovery_support")
                if expected_parent_support is None:
                    expected_parent_support = _compact_set_commitment(
                        hypothesis.discovery_support_receipt_ids,
                        exclusive_frontier=(
                            hypothesis.certification_frontier + 1
                        ),
                    )
                expected_parent_ancestors = dict(
                    hypothesis.nomination_read_commitments
                ).get("transitive_ancestor_reads")
                if expected_parent_ancestors is None:
                    expected_parent_ancestors = _compact_set_commitment(
                        hypothesis.transitive_ancestor_receipt_ids,
                        exclusive_frontier=(
                            hypothesis.certification_frontier + 1
                        ),
                    )
            if (
                request.specialization_mode != self.specialization_mode
                or request.source_generation > self.current_generation
                or hypothesis.source_generation > request.source_generation
                or hypothesis.hypothesis_digest
                != request.parent_hypothesis_digest
                or hypothesis.polarity is not request.fixed_polarity
                or hypothesis.dormant_origin not in {
                    DormantOrigin.MIXED_OUTCOME_SHADOW,
                    DormantOrigin.DEFERRED_SPECIALIZATION_CHILD,
                    DormantOrigin.ADAPTIVE_BOUNDARY_CHILD,
                }
                or (
                    (
                        request.parent_discovery_receipt_ids
                        != hypothesis.discovery_receipt_ids
                        or request.parent_discovery_support_receipt_ids
                        != hypothesis.discovery_support_receipt_ids
                        or request.transitive_ancestor_receipt_ids
                        != hypothesis.transitive_ancestor_receipt_ids
                    )
                    if not compact_request else (
                        request.parent_discovery_commitment
                        != expected_parent_discovery
                        or request.parent_discovery_support_commitment
                        != expected_parent_support
                        or request.transitive_ancestor_commitment
                        != expected_parent_ancestors
                    )
                )
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
                # The complete state ledgers are intentionally scanned only
                # at this explicit full-history boundary, where they are
                # already being reconstructed.  Feed the bounded prefix into
                # the same window selector used by the hot trigger: state
                # ledgers here include the triggering receipt, so strict
                # ``<`` recovers the pre-event history passed on the hot path.
                support_history = tuple(
                    receipt_id for receipt_id in state.support_receipt_ids
                    if references[receipt_id].ordinal
                    < request.request_emission_ordinal
                )
                contradiction_history = tuple(
                    receipt_id
                    for receipt_id in state.contradiction_receipt_ids
                    if references[receipt_id].ordinal
                    < request.request_emission_ordinal
                )
                (
                    prospective_support_ids,
                    contradiction_ids,
                    all_support_ids,
                ) = _bounded_specialization_evidence_ids(
                    support_receipt_ids=support_history,
                    contradiction_receipt_ids=contradiction_history,
                    discovery_support_receipt_ids=(
                        state.hypothesis.discovery_support_receipt_ids
                    ),
                    emission_receipt_id=(
                        request.request_emission_receipt_id
                    ),
                    supports=(
                        request.parent_cell_id
                        in emission.supporting_cell_ids
                    ),
                    contradicts=(
                        request.parent_cell_id
                        in emission.contradiction_cell_ids
                    ),
                    basis=request.request_basis,
                )
                all_support_references = tuple(
                    references[item] for item in all_support_ids
                )
            except KeyError as exc:
                raise ProspectiveV2IntegrityError(
                    "specialization request references unknown REAL evidence"
                ) from exc
            if (
                (
                    prospective_support_ids
                    != request.parent_prospective_support_receipt_ids
                ) if not compact_request else (
                    _compact_set_commitment(
                        prospective_support_ids,
                        exclusive_frontier=(
                            request.request_emission_ordinal + 1
                        ),
                    )
                    != request.parent_prospective_support_commitment
                )
                or not contradiction_ids
                or any(
                    reference.observed_outcome is not expected_outcome
                    for reference in all_support_references
                )
            ):
                raise ProspectiveV2IntegrityError(
                    "specialization request support contract mismatch"
                )
            earliest_contradiction = references[contradiction_ids[0]]
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
            vocabulary_set = {
                identity
                for reference in all_support_references
                for identity in reference.ordered_signal_identities
                if _specialization_identity_role_permitted(
                    reference, identity
                )
            }
            vocabulary = tuple(sorted(
                vocabulary_set,
                key=lambda identity: _specialization_feature_sort_key(
                    identity,
                    sum(
                        identity in reference.ordered_signal_identities
                        for reference in all_support_references
                    ),
                    genome_seed=self.specialization_genome_seed,
                    request_ordinal=0,
                ),
            ))[:SPECIALIZATION_CANDIDATE_BEAM_WIDTH]
            inspected_ids = tuple(sorted({
                *all_support_ids,
                request.contradiction_receipt_id,
                request.request_emission_receipt_id,
            }))
            inspected_witnesses = _bounded_provenance_witnesses(inspected_ids)
            expected_inspected_commitment = (
                _compact_set_commitment(
                    inspected_ids,
                    exclusive_frontier=(
                        request.request_emission_ordinal + 1
                    ),
                )
                if compact_request else None
            )
            if compact_request and request.candidate_inspected_commitment != (
                expected_inspected_commitment
            ):
                raise ProspectiveV2IntegrityError(
                    "specialization request inspected commitment mismatch"
                )
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
                        supporting_receipt_ids=(
                            _bounded_provenance_witnesses(supporting_ids)
                            if compact_request else supporting_ids
                        ),
                        supporting_stable_physical_interaction_ids=(
                            _bounded_provenance_witnesses(
                                supporting_physical_ids
                            )
                            if compact_request else supporting_physical_ids
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
                        inspected_receipt_ids=(
                            inspected_witnesses
                            if compact_request else inspected_ids
                        ),
                        evidence_schema_version=(
                            PROVENANCE_COMMITMENT_V4
                            if compact_request else None
                        ),
                        supporting_receipt_commitment=(
                            _compact_set_commitment(
                                supporting_ids,
                                exclusive_frontier=(
                                    request.request_emission_ordinal + 1
                                ),
                            )
                            if compact_request else None
                        ),
                        inspected_receipt_commitment=(
                            expected_inspected_commitment
                            if compact_request
                            else None
                        ),
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
        expected_parent_log = tuple(
            self.deferred_requests[request_id].parent_cell_id
            for request_id in self.request_queue
        )
        if (
            len(requested_parents) != len(set(requested_parents))
            or len(expected_parent_log) != len(set(expected_parent_log))
            or tuple(self.lifetime_requested_parent_ids)
            != expected_parent_log
        ):
            raise ProspectiveV2IntegrityError(
                "lifetime specialization request ledger mismatch"
            )

    def _verify_invariants(
        self,
        *,
        allow_unregistered: bool = False,
        frozen_base_continuation_digest: str | None = None,
        expected_authority_topology: Mapping[str, Any] | None = None,
    ) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ProspectiveV2IntegrityError("unsupported V2 schema")
        boundary_schema = str(getattr(
            self,
            "boundary_digest_schema",
            BOUNDARY_DIGEST_SCHEMA_LEGACY,
        ))
        if boundary_schema not in {
            BOUNDARY_DIGEST_SCHEMA_LEGACY,
            BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN,
        }:
            raise ProspectiveV2IntegrityError(
                "unknown generation-boundary digest schema"
            )
        if boundary_schema == BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN:
            commitment_count = getattr(self, "_boundary_commitment_count", 0)
            commitment_origin = getattr(
                self, "_boundary_commitment_origin_digest", ""
            )
            commitment_digest = getattr(
                self, "_boundary_commitment_digest", ""
            )
            if (
                isinstance(commitment_count, bool)
                or not isinstance(commitment_count, int)
                or commitment_count < 0
                or any(
                    value and len(value) != 64
                    for value in (
                        commitment_origin,
                        commitment_digest,
                        getattr(self, "_boundary_structure_digest", ""),
                    )
                )
            ):
                raise ProspectiveV2IntegrityError(
                    "generation-boundary mutation commitment is malformed"
                )
        # Full invariant checks are an explicit reclosure boundary.  Refresh
        # the bounded runtime indexes before any capacity/queue assertions so
        # those assertions cannot rely on a stale cache after restoration or
        # deliberate ledger tampering.  REAL/VIRTUAL hot paths use the cache
        # without calling this full verifier.
        self._refresh_hot_path_indexes()
        try:
            structural_mode = StructuralMode(self.structural_mode)
        except (TypeError, ValueError) as exc:
            raise ProspectiveV2IntegrityError(
                "unknown structural execution mode"
            ) from exc
        if (
            structural_mode is StructuralMode.EVENT_DRIVEN
            and self.structural_epoch_schedule
        ):
            raise ProspectiveV2IntegrityError(
                "event-driven structural mode carries a schedule"
            )
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
        retired_tombstones = self.retired_tombstones
        retired_ids = {
            cell_id for cell_id, state in self.states.items()
            if getattr(state, "retired", False)
        }
        if retired_ids != set(retired_tombstones):
            raise ProspectiveV2IntegrityError(
                "retired state/tombstone identity mismatch"
            )
        if set(retired_tombstones).intersection(self.historical_tombstones):
            raise ProspectiveV2IntegrityError(
                "adaptive retirement collides with historical tombstone"
            )
        protected_parents = self._retirement_protected_parent_ids()
        for cell_id in sorted(registered):
            state = self.states[cell_id]
            if not getattr(state, "retired", False):
                if any(
                    getattr(state, name, None) is not None
                    for name in (
                        "retirement_generation",
                        "retirement_ordinal",
                        "retirement_reason",
                        "retirement_tombstone_digest",
                    )
                ):
                    raise ProspectiveV2IntegrityError(
                        f"live state carries retirement metadata: {cell_id}"
                    )
                continue
            if (
                state.hypothesis.source_generation <= 0
                or state.hypothesis.initialization_origin
                is not InitializationOrigin.PROSPECTIVE
                or cell_id in protected_parents
                or not isinstance(
                    getattr(state, "retirement_generation", None), int
                )
                or not isinstance(
                    getattr(state, "retirement_ordinal", None), int
                )
                or getattr(state, "retirement_generation") < 0
                or getattr(state, "retirement_generation")
                > self.current_generation
                or getattr(state, "retirement_ordinal") < 0
                or getattr(state, "retirement_ordinal")
                > self.next_expected_ordinal
                or not getattr(state, "retirement_reason", None)
                or not getattr(state, "retirement_tombstone_digest", None)
            ):
                raise ProspectiveV2IntegrityError(
                    f"retired state is not a replaceable adaptive leaf: {cell_id}"
                )
            self._validate_retirement_tombstone(
                cell_id, state, retired_tombstones[cell_id]
            )
        self._verify_generation_boundary_retirements()
        if any(
            not isinstance(request, BoundaryPromotionRequest)
            or request.candidate_id != candidate_id
            for candidate_id, request
            in self.boundary_promotion_requests.items()
        ):
            raise ProspectiveV2IntegrityError(
                "boundary promotion request ledger is malformed"
            )
        compact_prefix_frontiers = tuple(
            hypothesis.birth_frontier + 1
            for hypothesis in (
                state.hypothesis for state in self.states.values()
            )
            if hypothesis.provenance_schema_version
            == PROVENANCE_COMMITMENT_V4
        )
        compact_prefix_commitments = (
            self._accepted_real_prefix_commitments(
                compact_prefix_frontiers
            )
            if compact_prefix_frontiers else {}
        )
        deferred_birth_by_child: dict[
            str, tuple[DeferredSpecializationRequest, DeferredChildBirth]
        ] = {}
        for request_id, birth in self.deferred_child_births.items():
            if birth.disposition != "MATERIALIZED":
                continue
            request = self.deferred_requests.get(request_id)
            if (
                request is None
                or birth.child_cell_id in deferred_birth_by_child
            ):
                raise ProspectiveV2IntegrityError(
                    "deferred child birth/request identity is ambiguous"
                )
            deferred_birth_by_child[birth.child_cell_id] = (
                request, birth
            )
        for cell_id in sorted(registered):
            hypothesis = self.states[cell_id].hypothesis
            if hypothesis.source_generation > self.current_generation:
                raise ProspectiveV2IntegrityError(
                    f"hypothesis source generation is in the future: {cell_id}"
                )
            if hypothesis.provenance_schema_version == (
                PROVENANCE_COMMITMENT_V4
            ):
                self._validate_compact_exclusion_commitment(
                    hypothesis.discovery_exclusion_commitment,
                    birth_frontier=hypothesis.birth_frontier,
                    label=f"hypothesis {cell_id}",
                    prefix_commitments=compact_prefix_commitments,
                )
            if (
                hypothesis.nomination_operation == "specialization"
                and hypothesis.lineage_parent_id is not None
            ):
                parent_state = self.states.get(hypothesis.lineage_parent_id)
                if (
                    parent_state is not None
                    and hypothesis.specialization_depth
                    != parent_state.hypothesis.specialization_depth + 1
                ):
                    raise ProspectiveV2IntegrityError(
                        f"specialization child depth is not parent+1: {cell_id}"
                    )
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
                if hypothesis.dormant_origin is DormantOrigin.ADAPTIVE_BOUNDARY_CHILD:
                    if (
                        hypothesis.nomination_operation != "ordinary"
                        or hypothesis.structural_state != StemCellState.DORMANT.name
                        or hypothesis.lineage_parent_id is not None
                        or hypothesis.specialization_depth != 0
                        or hypothesis.parent_hypothesis_digest is not None
                    ):
                        raise ProspectiveV2IntegrityError(
                            f"adaptive boundary child lineage mismatch: {cell_id}"
                        )
                    candidate_id = self._boundary_promotion_by_child.get(
                        cell_id
                    )
                    request = (
                        None if candidate_id is None
                        else self.boundary_promotion_requests.get(candidate_id)
                    )
                    if request is None:
                        raise ProspectiveV2IntegrityError(
                            f"adaptive boundary child request is absent: {cell_id}"
                        )
                    if hypothesis.source_generation != request.source_generation + 1:
                        raise ProspectiveV2IntegrityError(
                            f"adaptive boundary child generation mismatch: {cell_id}"
                        )
                    escrow = self.adaptive_boundary_escrows.get(cell_id)
                    if not isinstance(escrow, NominationEscrow):
                        raise ProspectiveV2IntegrityError(
                            f"adaptive boundary child lacks escrow: {cell_id}"
                        )
                    if (
                        escrow.escrow_schema_version not in {
                            NOMINATION_ESCROW_V2, NOMINATION_ESCROW_V4
                        }
                        or escrow.operation != "ordinary"
                        or escrow.fixed_polarity is not hypothesis.polarity
                        or hypothesis.nomination_escrow_digest
                        != escrow.escrow_digest
                        or hypothesis.nomination_read_sets
                        != escrow.categorized_reads
                        or hypothesis.discovery_exclusion_receipt_ids
                        != escrow.discovery_exclusion_receipt_ids
                        or hypothesis.discovery_support_receipt_ids
                        != (request.supporting_receipt_ids if request.hypothesis_birth_digest is None
                            else (request.triggering_receipt_id,))
                        or hypothesis.provenance_schema_version
                        != (
                            PROVENANCE_COMMITMENT_V4
                            if escrow.escrow_schema_version
                            == NOMINATION_ESCROW_V4 else None
                        )
                        or hypothesis.discovery_exclusion_commitment
                        != escrow.discovery_exclusion_commitment
                        or hypothesis.nomination_read_commitments
                        != escrow.nomination_read_commitments
                        or escrow.triggering_receipt_id
                        != request.triggering_receipt_id
                    ):
                        raise ProspectiveV2IntegrityError(
                            f"adaptive boundary child escrow mismatch: {cell_id}"
                        )
                    if self.boundary_promotion_requests.get(
                        request.candidate_id
                    ) != request:
                        raise ProspectiveV2IntegrityError(
                            f"adaptive boundary child request mismatch: {cell_id}"
                        )
                    if escrow.escrow_schema_version == NOMINATION_ESCROW_V4:
                        self._validate_compact_ordinary_birth_contract(
                            request, escrow, hypothesis
                        )
                    continue
                if hypothesis.nomination_operation != "specialization":
                    raise ProspectiveV2IntegrityError(
                        f"unknown successor hypothesis origin: {cell_id}"
                    )
                escrow = self.deferred_child_escrows.get(cell_id)
                if not isinstance(escrow, NominationEscrow):
                    raise ProspectiveV2IntegrityError(
                        f"successor child lacks V3 escrow: {cell_id}"
                    )
                parent_id = hypothesis.lineage_parent_id
                parent_state = (
                    None if parent_id is None else self.states.get(parent_id)
                )
                if parent_state is None:
                    raise ProspectiveV2IntegrityError(
                        f"successor child parent is absent: {cell_id}"
                    )
                if hypothesis.specialization_depth != (
                    parent_state.hypothesis.specialization_depth + 1
                ):
                    raise ProspectiveV2IntegrityError(
                        f"successor child depth is not parent+1: {cell_id}"
                    )
                if hypothesis.parent_hypothesis_digest != (
                    parent_state.hypothesis.hypothesis_digest
                ):
                    raise ProspectiveV2IntegrityError(
                        f"successor child parent digest mismatch: {cell_id}"
                    )
                if (
                    escrow.escrow_schema_version not in {
                        NOMINATION_ESCROW_V3, NOMINATION_ESCROW_V4
                    }
                    or hypothesis.nomination_escrow_digest
                    != escrow.escrow_digest
                    or hypothesis.nomination_read_sets
                    != escrow.categorized_reads
                    or hypothesis.discovery_exclusion_receipt_ids
                    != escrow.discovery_exclusion_receipt_ids
                    or hypothesis.parent_hypothesis_digest
                    != escrow.parent_hypothesis_digest
                    or hypothesis.provenance_schema_version
                    != (
                        PROVENANCE_COMMITMENT_V4
                        if escrow.escrow_schema_version
                        == NOMINATION_ESCROW_V4 else None
                    )
                    or hypothesis.discovery_exclusion_commitment
                    != escrow.discovery_exclusion_commitment
                    or hypothesis.nomination_read_commitments
                    != escrow.nomination_read_commitments
                ):
                    raise ProspectiveV2IntegrityError(
                        f"successor child escrow mismatch: {cell_id}"
                    )
                if escrow.escrow_schema_version == NOMINATION_ESCROW_V4:
                    request_birth = deferred_birth_by_child.get(cell_id)
                    if request_birth is None:
                        raise ProspectiveV2IntegrityError(
                            f"compact successor child request is absent: {cell_id}"
                        )
                    request, birth = request_birth
                    self._validate_compact_deferred_birth_contract(
                        request, birth, escrow, hypothesis
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
        for request in self.boundary_promotion_requests.values():
            child_id = self._adaptive_boundary_child_id(request)
            if child_id not in self.states:
                raise ProspectiveV2IntegrityError(
                    "boundary promotion request lacks materialized child"
                )
            if child_id not in self.adaptive_boundary_escrows:
                raise ProspectiveV2IntegrityError(
                    "boundary promotion child escrow is absent"
                )
        adaptive_state_ids = {
            cell_id for cell_id, state in self.states.items()
            if state.hypothesis.dormant_origin
            is DormantOrigin.ADAPTIVE_BOUNDARY_CHILD
        }
        if set(self.adaptive_boundary_escrows) != adaptive_state_ids:
            raise ProspectiveV2IntegrityError(
                "adaptive boundary escrow ledger mismatch"
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
        expected_topology = (
            _executed_authority_topology_manifest(
                self._live_authority_state_cache
            )
            if expected_authority_topology is None
            else expected_authority_topology
        )
        if self.authority_topology != expected_topology:
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

        if len(self._pending_request_ids()) > REQUEST_QUEUE_CAPACITY:
            raise ProspectiveV2IntegrityError("request queue capacity exceeded")
        if len(self._successor_capacity_occupants()) > (
            DORMANT_SPECIALIZATION_CHILD_CAPACITY
        ):
            raise ProspectiveV2IntegrityError(
                "dormant specialization-child capacity exceeded"
            )
        if set(self.deferred_requests) != set(self.request_queue):
            raise ProspectiveV2IntegrityError(
                "deferred request/queue identity mismatch"
            )
        request_ids_by_generation: dict[int, list[str]] = {}
        request_attempt_ordinals: dict[str, int] = {}
        for request_id in self.request_queue:
            request = self.deferred_requests[request_id]
            generation_ids = request_ids_by_generation.setdefault(
                request.source_generation, []
            )
            request_attempt_ordinals[request_id] = len(generation_ids)
            generation_ids.append(request_id)
        structural_plans = getattr(self, "structural_request_plans", {})
        for request_id, plan in sorted(structural_plans.items()):
            if (
                request_id not in self.sealed_request_ids
                or request_id in self.request_consumptions
                or self.generation_phase
                is not GenerationPhase.STRUCTURAL_OPEN
            ):
                raise ProspectiveV2IntegrityError(
                    "structural request plan cache is stale or malformed"
                )
            self._validate_structural_consumption_fields(
                request_id,
                plan,
                attempt_ordinal=request_attempt_ordinals[request_id],
            )
            if plan.disposition == "MATERIALIZED":
                raise ProspectiveV2IntegrityError(
                    "structural request plan is already materialized"
                )
            if plan.child_cell_id is not None:
                expected_child_id = (
                    f"v2_deferred_specialization_"
                    f"g{self.current_generation:02d}_"
                    f"{plan.attempt_ordinal:04d}"
                )
                if plan.child_cell_id != expected_child_id:
                    raise ProspectiveV2IntegrityError(
                        "structural request plan child identity mismatch"
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
        consumed_member_tuples: set[tuple[str, ...]] = {
            state.hypothesis.members
            for state in self.states.values()
        }
        for birth in self.deferred_child_births.values():
            consumed_member_tuples.discard(birth.members)
        for request_id in self.request_queue:
            consumption = self.request_consumptions.get(request_id)
            if consumption is None:
                continue
            request = self.deferred_requests[request_id]
            self._validate_structural_consumption_fields(
                request_id,
                consumption,
                attempt_ordinal=request_attempt_ordinals[request_id],
            )
            if consumption.selected_members:
                already_reserved = consumption.selected_members in (
                    consumed_member_tuples
                )
                if consumption.disposition == "REJECTED_DUPLICATE_PATTERN":
                    if not already_reserved:
                        raise ProspectiveV2IntegrityError(
                            "duplicate specialization tuple has no prior reservation"
                        )
                elif already_reserved:
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
        materialized_child_ids: set[str] = set()
        for request_id, birth in sorted(self.deferred_child_births.items()):
            if not isinstance(birth, DeferredChildBirth):
                raise ProspectiveV2IntegrityError(
                    "deferred child birth is malformed"
                )
            consumption = self.request_consumptions.get(request_id)
            if consumption is None:
                raise ProspectiveV2IntegrityError(
                    "child birth exists without consumed request"
                )
            request = self.deferred_requests.get(request_id)
            if request is None:
                raise ProspectiveV2IntegrityError(
                    "child birth names an unknown request"
                )
            if (
                birth.request_id != request_id
                or birth.child_cell_id != consumption.child_cell_id
                or birth.members != consumption.selected_members
                or birth.genome_seed != consumption.genome_seed
                or birth.proposal_ordinal != consumption.attempt_ordinal
                or isinstance(birth.source_generation, bool)
                or not isinstance(birth.source_generation, int)
                or birth.source_generation <= 0
                or birth.source_generation > self.current_generation
                or birth.disposition not in _DEFERRED_BIRTH_DISPOSITIONS
            ):
                raise ProspectiveV2IntegrityError(
                    "deferred child birth differs from request consumption"
                )
            expected_child_id = (
                f"v2_deferred_specialization_"
                f"g{birth.source_generation:02d}_"
                f"{birth.proposal_ordinal:04d}"
            )
            if birth.child_cell_id != expected_child_id:
                raise ProspectiveV2IntegrityError(
                    "deferred child birth identity differs from safe point"
                )
            if birth.disposition == "PENDING_MATERIALIZATION":
                if (
                    consumption.disposition != "PENDING_CHILD"
                    or birth.child_cell_id in self.states
                    or birth.child_cell_id in self.deferred_child_escrows
                ):
                    raise ProspectiveV2IntegrityError(
                        "pending deferred birth has materialized state"
                    )
                continue
            if consumption.disposition != "MATERIALIZED":
                raise ProspectiveV2IntegrityError(
                    "materialized deferred birth has non-materialized disposition"
                )
            state = self.states.get(birth.child_cell_id)
            escrow = self.deferred_child_escrows.get(birth.child_cell_id)
            if state is None or not isinstance(escrow, NominationEscrow):
                raise ProspectiveV2IntegrityError(
                    "materialized deferred birth lacks state or escrow"
                )
            hypothesis = state.hypothesis
            if (
                hypothesis.cell_id != birth.child_cell_id
                or hypothesis.members != birth.members
                or hypothesis.lineage_parent_id != request.parent_cell_id
                or hypothesis.parent_hypothesis_digest
                != request.parent_hypothesis_digest
                or hypothesis.source_generation != birth.source_generation
                or hypothesis.nomination_operation != "specialization"
                or hypothesis.dormant_origin
                is not DormantOrigin.DEFERRED_SPECIALIZATION_CHILD
            ):
                raise ProspectiveV2IntegrityError(
                    "materialized deferred birth state differs from ledger"
                )
            materialized_child_ids.add(birth.child_cell_id)
        if set(self.deferred_child_escrows) != materialized_child_ids:
            raise ProspectiveV2IntegrityError(
                "deferred child escrow/birth identity mismatch"
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

        for cell_id, state in self.states.items():
            expected_certification_digest = _append_log_digest(
                state.certification_receipt_ids,
                kind="certification_receipt",
            )
            if (
                getattr(state, "certification_receipt_digest", "")
                != expected_certification_digest
            ):
                raise ProspectiveV2IntegrityError(
                    "certification receipt rolling digest mismatch: "
                    f"{cell_id}"
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

    def _boundary_replay_seed(self) -> "NativeProspectiveAuthorityV2":
        """Make the post-nomination authority state used by full replay.

        A boundary digest is a digest of the authority *at that point*, not a
        digest of the final cache with a historical label attached.  The
        replay therefore starts with the immutable generation-zero population
        and the frozen historical ledger, then applies boundaries and REAL
        receipts in their causal order.  This is deliberately private and is
        used only at explicit full-history boundaries.
        """

        replay = copy.deepcopy(self)
        initial_ids = tuple(sorted(
            cell_id for cell_id, state in self.states.items()
            if state.hypothesis.source_generation == 0
        ))
        replay.states = {
            cell_id: ProspectiveAuthorityState(
                hypothesis=self.states[cell_id].hypothesis,
                prospectively_certified=(
                    self.mode is V2Mode.LEGACY
                    and self.states[cell_id].hypothesis.structural_state
                    == StemCellState.MATURE.name
                ),
            )
            for cell_id in initial_ids
        }
        replay.structural_invariants = {
            cell_id: self.structural_invariants[cell_id]
            for cell_id in initial_ids
        }
        # ``copy.deepcopy(self)`` carried the final live cache.  Replace it
        # before the seed topology is built so replay starts from the actual
        # generation-zero projection rather than a stale lifetime view.
        replay._live_authority_state_cache = _LiveAuthorityStateView(
            replay.states
        )
        replay._successor_capacity_occupant_ids = set()
        replay._pending_child_birth_request_ids = set()
        replay._reserved_member_pairs = {
            tuple(state.hypothesis.members)
            for state in replay.states.values()
        }
        replay.authority_topology = _executed_authority_topology_manifest(
            replay._live_authority_state_cache
        )
        replay.retired_tombstones = {}
        replay.current_generation = 0
        replay.generation_phase = GenerationPhase.PROSPECTIVE_OPEN
        replay.accepted_real_references = {
            reference.receipt_id: reference
            for reference in self._historical_real_references(replay.base)
        }
        replay.deferred_requests = {}
        replay.request_queue = _AppendOnlyLedger()
        replay.lifetime_requested_parent_ids = _AppendOnlyLedger()
        replay.request_consumptions = {}
        replay.deferred_child_births = {}
        replay.deferred_child_escrows = {}
        replay.boundary_promotion_requests = {}
        replay.boundary_hypothesis_births = {}
        replay._boundary_hypothesis_birth_digest = ""
        replay.adaptive_boundary_escrows = {}
        replay.generation_boundaries = _AppendOnlyLedger()
        replay.sealed_request_ids = ()
        replay.sealed_request_queue_digest = None
        replay.evaluation_sealed = False
        replay.pending_event = None
        replay.consumed_receipts = {}
        replay.consumed_tokens = set()
        replay.prospective_physical_fingerprints = {}
        replay.emissions = {}
        replay.event_transactions = {}
        replay.structural_request_plans = {}
        replay.incremental_history_state = None
        replay.next_expected_ordinal = self._history_expected_start()
        # Nomination events and experimental identity are created before the
        # first generation boundary and are immutable thereafter.
        replay.nomination_events = tuple(self.nomination_events)
        replay.experimental_identity = copy.deepcopy(
            self.experimental_identity
        )
        replay._history_validation_mode = HISTORY_VALIDATION_INCREMENTAL
        if replay.boundary_digest_schema == (
            BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
        ):
            expected_origin = _sha(
                replay._boundary_commitment_origin_payload()
            )
            if expected_origin != self._boundary_commitment_origin_digest:
                raise ProspectiveV2IntegrityError(
                    "generation-boundary commitment origin differs from replay"
                )
            replay._boundary_commitment_origin_digest = expected_origin
            replay._boundary_commitment_digest = expected_origin
            replay._boundary_commitment_count = 0
            replay._boundary_accepted_real_digest = (
                replay._boundary_seed_accepted_real_digest()
            )
            replay._boundary_candidate_digest = (
                replay._boundary_seed_candidate_digest()
            )
            replay._boundary_decision_digest = (
                replay._boundary_seed_decision_digest()
            )
            replay._boundary_schedule_digest = _sha(
                list(replay.structural_epoch_schedule)
            )
            replay._boundary_structure_digest = (
                replay._canonical_structure_invariant_digest()
            )
            replay._boundary_request_digest_cache = {}
            replay._boundary_replay_active_promotion_ids = set()
            by_generation: dict[
                int, list[tuple[str, BoundaryPromotionRequest]]
            ] = {}
            by_child: dict[str, str] = {}
            for candidate_id, request in sorted(
                self.boundary_promotion_requests.items()
            ):
                child_id = self._adaptive_boundary_child_id(request)
                state = self.states.get(child_id)
                if state is None:
                    raise ProspectiveV2IntegrityError(
                        "boundary promotion history lacks materialized child"
                    )
                generation = state.hypothesis.source_generation
                by_generation.setdefault(generation, []).append(
                    (candidate_id, request)
                )
                by_child[child_id] = candidate_id
            replay._boundary_replay_promotions_by_generation = {
                generation: tuple(sorted(
                    items,
                    key=lambda item: (
                        item[1].request_digest,
                        item[0],
                    ),
                ))
                for generation, items in by_generation.items()
            }
            replay._boundary_replay_promotion_by_child = by_child
        replay._refresh_hot_path_indexes()
        if replay.boundary_digest_schema == (
            BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
        ):
            # The refresh above seeds the live view from generation zero.  It
            # must not recreate the lifetime promotion projection: no
            # post-nomination child is live in this replay seed.
            replay._boundary_replay_active_promotion_ids = set()
            replay._boundary_replay_refresh_promotion_digest()
        return replay

    @staticmethod
    def _boundary_replay_classification(
        value: Mapping[str, Any],
    ) -> EnvelopeClassification:
        """Decode the persisted pre-outcome classification without trust."""

        try:
            return EnvelopeClassification(
                state=AvailabilityState(value["state"]),
                probability=float(value["probability"]),
                uncertainty=float(value["uncertainty"]),
                available_cell_ids=tuple(value["available_cell_ids"]),
                refuted_cell_ids=tuple(value["refuted_cell_ids"]),
                formal_available=bool(value["formal_available"]),
                formal_refuted=bool(value["formal_refuted"]),
                policy_response=bool(value["policy_response"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ProspectiveV2IntegrityError(
                "replayed transaction classification is malformed"
            ) from exc

    @classmethod
    def _boundary_replay_pending(
        cls,
        receipt: V2GroundedReceipt,
        transaction: Mapping[str, Any],
    ) -> PendingRealEvent:
        """Reconstruct the exact pending event committed before a receipt."""

        try:
            pending = PendingRealEvent(
                ordinal=int(transaction["ordinal"]),
                frame_id=str(transaction["frame_id"]),
                trace_digest=str(transaction["trace_digest"]),
                typed_signal_digest=str(transaction["typed_signal_digest"]),
                source_organism_identity=str(
                    transaction["source_organism_identity"]
                ),
                source_state_identity=str(transaction["source_state_identity"]),
                predecessor_fen=str(transaction["predecessor_fen"]),
                actuation=GraphActuation(**dict(transaction["actuation"])),
                pre_outcome_classification=(
                    cls._boundary_replay_classification(
                        transaction["pre_outcome_classification"]
                    )
                ),
                matching_cell_ids=tuple(transaction["matching_cell_ids"]),
                matching_cell_digest=str(transaction["matching_cell_digest"]),
                structure_invariant_digest=str(
                    transaction["structure_invariant_digest"]
                ),
                predecessor_continuation_digest=str(
                    transaction["predecessor_continuation_digest"]
                ),
                pending_token=str(transaction["pending_token"]),
                outcome_terminal_identity=str(
                    transaction["outcome_terminal_identity"]
                ),
                environment_outcome_terminal_identity=str(
                    transaction["environment_outcome_terminal_identity"]
                ),
                state="OPEN",
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ProspectiveV2IntegrityError(
                "replayed transaction pending event is malformed"
            ) from exc
        if pending.pending_token != receipt.pending_token:
            raise ProspectiveV2IntegrityError(
                "replayed transaction token differs from receipt"
            )
        manifest = pending.manifest()
        if any(
            transaction.get(key) != value
            for key, value in manifest.items()
            if key != "state"
        ) or transaction.get("state") != "CONSUMED" or transaction.get(
            "consumed_receipt_id"
        ) != receipt.receipt_id:
            raise ProspectiveV2IntegrityError(
                "consumed transaction does not close its pending manifest"
            )
        return pending

    @staticmethod
    def _boundary_replay_reset_state(
        state: ProspectiveAuthorityState,
    ) -> None:
        """Keep a newly born child at its zero-evidence lifecycle state."""

        # This helper documents the invariant and gives callers one place to
        # assert it; construction through ProspectiveAuthorityState already
        # initializes these values to zero.
        if any((
            state.certification_receipt_ids,
            state.support_receipt_ids,
            state.contradiction_receipt_ids,
            state.successes,
            state.contradictions,
            state.support,
            state.prospectively_certified,
        )):
            raise ProspectiveV2IntegrityError(
                "replayed child was born with lifecycle evidence"
            )

    def _boundary_replay_retire(
        self,
        replay: "NativeProspectiveAuthorityV2",
        cell_ids: Sequence[str],
    ) -> None:
        """Apply one safe-point retirement batch and verify ``state_before``."""

        for cell_id in tuple(cell_ids):
            state = replay.states.get(cell_id)
            tombstone = self.retired_tombstones.get(cell_id)
            if state is None or not isinstance(tombstone, Mapping):
                raise ProspectiveV2IntegrityError(
                    "boundary retirement names an unknown state"
                )
            if cell_id in replay.retired_tombstones:
                raise ProspectiveV2IntegrityError(
                    "boundary retirement is applied twice"
                )
            if dict(tombstone.get("state_before", {})) != state.manifest():
                raise ProspectiveV2IntegrityError(
                    "retirement tombstone state_before differs from replay"
                )
            state.retired = True
            state.prospectively_certified = False
            state.retirement_generation = tombstone.get(
                "retirement_generation"
            )
            state.retirement_ordinal = tombstone.get("retirement_ordinal")
            state.retirement_reason = tombstone.get("retirement_reason")
            state.retirement_tombstone_digest = tombstone.get(
                "retirement_tombstone_digest"
            )
            replay.retired_tombstones[cell_id] = copy.deepcopy(dict(tombstone))
            self._validate_retirement_tombstone(
                cell_id, state, replay.retired_tombstones[cell_id]
            )
        if cell_ids:
            retirement_payload = {
                "tombstones": [
                    copy.deepcopy(replay.retired_tombstones[cell_id])
                    for cell_id in cell_ids
                ],
            }
            replay._record_boundary_structure(
                "adaptive_retirement", retirement_payload
            )
            replay._record_boundary_candidate(
                "adaptive_retirement", retirement_payload
            )
            replay._advance_boundary_commitment(
                "adaptive_retirement",
                {
                    "retirement": retirement_payload,
                    "structure_digest": replay._boundary_structure_digest,
                },
            )
            for cell_id in cell_ids:
                self._boundary_replay_retire_live_state(replay, cell_id)
        if cell_ids:
            replay.authority_topology = _executed_authority_topology_manifest(
                replay._live_authority_state_cache
            )

    def _boundary_replay_materialize_children(
        self,
        replay: "NativeProspectiveAuthorityV2",
        *,
        generation: int,
        request_ids: Sequence[str],
        include_promotions: bool,
    ) -> None:
        """Replay one structural settlement from immutable birth ledgers."""

        def replay_deferred(request_id: str) -> None:
            if request_id in replay.request_consumptions:
                raise ProspectiveV2IntegrityError(
                    "structural request was replay-consumed twice"
                )
            consumption = self.request_consumptions.get(request_id)
            request = self.deferred_requests.get(request_id)
            if consumption is None or request is None:
                raise ProspectiveV2IntegrityError(
                    "boundary settlement names an unknown request"
                )
            if replay.boundary_hypothesis_births:
                expected_plan = replay._deferred_request_plan(
                    request_id, attempt_ordinal=consumption.attempt_ordinal,
                    target_generation=generation,
                    reserved_members=set(replay._reserved_member_pairs),
                ).consumption
                expected_consumption = (replace(expected_plan, disposition="MATERIALIZED")
                                        if consumption.disposition == "MATERIALIZED" else expected_plan)
                if expected_consumption != consumption:
                    raise ProspectiveV2IntegrityError("continuous residual eligibility differs from safe-point replay")
            replay.request_consumptions[request_id] = consumption
            replay._pending_request_index.discard(request_id)
            try:
                replay._pending_request_order.remove(request_id)
            except ValueError:
                pass
            replay._advance_boundary_commitment(
                "structural_consume",
                replay._boundary_structural_consumption_payload(consumption),
            )
            birth = self.deferred_child_births.get(request_id)
            if birth is None:
                if consumption.child_cell_id is not None:
                    raise ProspectiveV2IntegrityError(
                        "accepted structural request lacks child birth"
                    )
                return
            if birth.source_generation != generation:
                raise ProspectiveV2IntegrityError(
                    "structural child birth generation differs from boundary"
                )
            replay.deferred_child_births[request_id] = birth
            replay._pending_child_birth_request_ids.add(request_id)
            replay._successor_capacity_occupant_ids.add(
                birth.child_cell_id
            )
            replay._reserved_member_pairs.add(tuple(birth.members))
            child_id = birth.child_cell_id
            if child_id in replay.states:
                raise ProspectiveV2IntegrityError(
                    "structural child was replay-materialized twice"
                )
            final_state = self.states.get(child_id)
            invariant = self.structural_invariants.get(child_id)
            escrow = self.deferred_child_escrows.get(child_id)
            if (
                final_state is None
                or invariant is None
                or not isinstance(escrow, NominationEscrow)
            ):
                raise ProspectiveV2IntegrityError(
                    "structural child lacks replay birth artifacts"
                )
            hypothesis = final_state.hypothesis
            if hypothesis.provenance_schema_version == (
                PROVENANCE_COMMITMENT_V4
            ):
                expected_birth_frontier = replay.next_expected_ordinal - 1
                if (
                    hypothesis.birth_frontier != expected_birth_frontier
                    or hypothesis.certification_frontier
                    != expected_birth_frontier
                    or escrow.birth_frontier != expected_birth_frontier
                    or escrow.certification_frontier
                    != expected_birth_frontier
                ):
                    raise ProspectiveV2IntegrityError(
                        "compact deferred birth frontier differs from its "
                        "structural safe point"
                    )
            state = ProspectiveAuthorityState(
                hypothesis=hypothesis,
                prospectively_certified=False,
            )
            self._boundary_replay_reset_state(state)
            replay.states[child_id] = state
            replay.structural_invariants[child_id] = invariant
            replay.deferred_child_escrows[child_id] = escrow
            child_payload = {
                "request_id": request_id,
                "birth": birth.manifest(),
                "state": state.manifest(),
                "escrow": escrow.manifest(),
            }
            replay._record_boundary_structure(
                "deferred_child_materialize", child_payload
            )
            self._boundary_replay_add_live_state(replay, child_id)
            replay._pending_child_birth_request_ids.discard(request_id)
            replay._record_boundary_candidate(
                "deferred_child_materialize", child_payload
            )
            replay._record_boundary_decision(
                "deferred_child_materialize",
                {
                    "cell_id": child_id,
                    "row": replay._boundary_decision_row(child_id, state),
                },
            )
            replay._advance_boundary_commitment(
                "deferred_child_materialize",
                {
                    "child": child_payload,
                    "structure_digest": replay._boundary_structure_digest,
                },
            )

        def replay_promotion(
            candidate_id: str,
            request: BoundaryPromotionRequest,
        ) -> None:
            child_id = self._adaptive_boundary_child_id(request)
            final_state = self.states.get(child_id)
            if final_state is None or (
                final_state.hypothesis.source_generation != generation
            ):
                return
            if child_id in replay.states:
                raise ProspectiveV2IntegrityError(
                    "ordinary boundary child was replay-materialized twice"
                )
            invariant = self.structural_invariants.get(child_id)
            escrow = self.adaptive_boundary_escrows.get(child_id)
            if invariant is None or not isinstance(escrow, NominationEscrow):
                raise ProspectiveV2IntegrityError(
                    "ordinary child lacks replay birth artifacts"
                )
            hypothesis = final_state.hypothesis
            if hypothesis.provenance_schema_version == (
                PROVENANCE_COMMITMENT_V4
            ):
                expected_birth_frontier = replay.next_expected_ordinal - 1
                if request.hypothesis_birth_digest is not None:
                    semantic_birth = replay._continuous_birth_for_request(request)
                    if hypothesis.materialization_frontier != expected_birth_frontier:
                        raise ProspectiveV2IntegrityError("continuous graph allocation differs from safe point")
                    expected_birth_frontier = semantic_birth.birth_frontier_ordinal
                if (
                    hypothesis.birth_frontier != expected_birth_frontier
                    or hypothesis.certification_frontier
                    != expected_birth_frontier
                    or escrow.birth_frontier != expected_birth_frontier
                    or escrow.certification_frontier
                    != expected_birth_frontier
                ):
                    raise ProspectiveV2IntegrityError(
                        "compact ordinary birth frontier differs from its "
                        "structural safe point"
                    )
            state = ProspectiveAuthorityState(
                hypothesis=hypothesis,
                prospectively_certified=False,
            )
            self._boundary_replay_reset_state(state)
            if request.hypothesis_birth_digest is not None:
                replay._transfer_continuous_boundary_evidence(state, request)
            replay.states[child_id] = state
            replay.structural_invariants[child_id] = invariant
            replay.boundary_promotion_requests[candidate_id] = request
            replay.adaptive_boundary_escrows[child_id] = escrow
            replay._reserved_member_pairs.add(tuple(final_state.hypothesis.members))
            promotion_payload = {
                "candidate_id": candidate_id,
                "child_id": child_id,
                "request": request.manifest(),
                "state": state.manifest(),
                "escrow": escrow.manifest(),
            }
            replay._record_boundary_structure(
                "boundary_promotion_materialize", promotion_payload
            )
            self._boundary_replay_add_live_state(replay, child_id)
            replay._boundary_replay_active_promotion_ids.add(candidate_id)
            replay._boundary_replay_refresh_promotion_digest()
            replay._record_boundary_candidate(
                "boundary_promotion_materialize", promotion_payload
            )
            replay._record_boundary_decision(
                "boundary_promotion_materialize",
                {
                    "cell_id": child_id,
                    "row": replay._boundary_decision_row(child_id, state),
                },
            )
            replay._advance_boundary_commitment(
                "boundary_promotion_materialize",
                {
                    "promotion": promotion_payload,
                    "structure_digest": replay._boundary_structure_digest,
                },
            )

        # Event-driven settlement materializes ordinary promotions first and
        # then consumes deferred requests.  Scheduled settlement has no
        # promotion batch, but follows the same request order.
        if include_promotions:
            for candidate_id, request in (
                replay._boundary_replay_promotions_by_generation.get(
                    generation, ()
                )
            ):
                replay_promotion(candidate_id, request)
        for request_id in request_ids:
            replay_deferred(request_id)

        replay.authority_topology = _executed_authority_topology_manifest(
            replay._live_authority_state_cache
        )

    def _boundary_replay_assert_fields(
        self,
        replay: "NativeProspectiveAuthorityV2",
        boundary: GenerationBoundary,
        *,
        queue_ids: Sequence[str],
        prior_digest: str,
        prior_digest_schema: str,
    ) -> None:
        """Compare every persisted GenerationBoundary field to replay state."""

        try:
            phase = GenerationPhase(boundary.phase)
        except (TypeError, ValueError) as exc:
            raise ProspectiveV2IntegrityError(
                "generation boundary phase is malformed"
            ) from exc
        boundary_prior_schema = getattr(
            boundary, "prior_digest_schema", BOUNDARY_DIGEST_SCHEMA_LEGACY
        )
        if (
            boundary.generation != replay.current_generation
            or boundary.event_frontier != replay.next_expected_ordinal
            or phase is not replay.generation_phase
            or boundary.prior_continuation_digest != prior_digest
            or boundary_prior_schema != prior_digest_schema
            or boundary.accepted_real_ledger_digest
            != replay._accepted_real_ledger_digest()
            or boundary.request_queue_digest
            != replay._request_queue_digest(queue_ids)
            or boundary.structural_epoch_schedule_digest
            != replay._boundary_schedule_digest
            or boundary.candidate_manifest_digest
            != replay._candidate_manifest_digest()
            or boundary.parent_decision_history_digest
            != replay._parent_decision_history_digest()
            or boundary.specialization_genome_seed
            != replay.specialization_genome_seed
        ):
            raise ProspectiveV2IntegrityError(
                "generation boundary causal field differs from replay"
            )
        if tuple(getattr(boundary, "retired_cell_ids", ())) != tuple(
            sorted(getattr(boundary, "retired_cell_ids", ()))
        ):
            raise ProspectiveV2IntegrityError(
                "generation boundary retirement IDs are not canonical"
            )

    def _verify_generation_boundary_replay(self) -> None:
        """Causally reclose boundaries, transactions, references and retirements.

        The replay is a single chronological pass.  In particular, it never
        replays the complete REAL ledger once per boundary; each receipt is
        consumed once while the boundary cursor advances at its event
        frontier.
        """

        boundaries = tuple(self.generation_boundaries)
        replay = self._boundary_replay_seed()
        ordered = tuple(sorted(
            self.consumed_receipts.values(),
            key=lambda item: (item.ordinal, item.receipt_id),
        ))
        receipt_index = 0
        boundary_index = 0
        births = tuple(sorted(self.boundary_hypothesis_births.values(), key=lambda item: item.sequence))
        birth_index = 0

        def apply_semantic_births() -> None:
            nonlocal birth_index
            while birth_index < len(births) and births[birth_index].birth_frontier_ordinal < replay.next_expected_ordinal:
                birth = births[birth_index]
                if birth.source_generation != replay.current_generation:
                    raise ProspectiveV2IntegrityError("semantic birth generation differs from replay chronology")
                digest = replay.register_boundary_hypothesis_birth(
                    candidate_id=birth.candidate_id, members=birth.members,
                    member_signal_roles=birth.member_signal_roles, source_identity=birth.source_identity,
                    semantic_identity=birth.semantic_identity, birth_frontier_ordinal=birth.birth_frontier_ordinal,
                    triggering_receipt_id=birth.triggering_receipt_id,
                )
                if digest != birth.birth_digest:
                    raise ProspectiveV2IntegrityError("semantic birth differs from its causal precommitment")
                birth_index += 1

        def consume_receipt(receipt: V2GroundedReceipt) -> None:
            transaction = self.event_transactions.get(receipt.pending_token)
            if not isinstance(transaction, Mapping):
                raise ProspectiveV2IntegrityError(
                    "replay receipt lacks its event transaction"
                )
            expected_reference = replay._reference_from_v2_receipt(
                receipt, source_generation=replay.current_generation
            )
            stored_reference = self.accepted_real_references.get(
                receipt.receipt_id
            )
            if stored_reference != expected_reference:
                raise ProspectiveV2IntegrityError(
                    "accepted REAL reference generation differs from boundary "
                    "chronology"
                )
            if transaction.get("structure_invariant_digest") != (
                replay._structure_invariant_digest()
            ):
                raise ProspectiveV2IntegrityError(
                    "consumed transaction structure digest differs from replay"
                )
            replay._ensure_incremental_history_initialized()
            pending = self._boundary_replay_pending(receipt, transaction)
            replay.pending_event = pending
            replay.event_transactions[pending.pending_token] = pending.manifest()
            replay._advance_boundary_commitment(
                "real_open", pending.manifest()
            )
            replay._consume_in_place_core(receipt)

        def apply_boundary(boundary: GenerationBoundary) -> None:
            nonlocal boundary_index
            try:
                phase = GenerationPhase(boundary.phase)
            except (TypeError, ValueError) as exc:
                raise ProspectiveV2IntegrityError(
                    "generation boundary phase is malformed"
                ) from exc
            if (
                isinstance(boundary.generation, bool)
                or not isinstance(boundary.generation, int)
                or boundary.generation < 0
                or isinstance(boundary.event_frontier, bool)
                or not isinstance(boundary.event_frontier, int)
                or boundary.event_frontier < 0
            ):
                raise ProspectiveV2IntegrityError(
                    "generation boundary ordinal or generation is malformed"
                )
            if boundary.event_frontier != replay.next_expected_ordinal:
                raise ProspectiveV2IntegrityError(
                    "generation boundary is outside replay frontier"
                )
            first_initial_structural = (
                boundary_index == 0
                and not replay.generation_boundaries
                and phase is GenerationPhase.STRUCTURAL_OPEN
                and boundary.generation == 0
            )
            current = replay.generation_phase
            initial_boundary_phase: GenerationPhase | None = None
            prepared_structural_successor = False
            queue_ids: tuple[str, ...] = ()
            if (
                current is GenerationPhase.STRUCTURAL_OPEN
                and phase is GenerationPhase.PROSPECTIVE_OPEN
                and replay.current_generation > 0
            ):
                # The prospective boundary is emitted after the structural
                # compatibility API has consumed/materialized its sealed
                # queue.  Reconstruct that state before hashing ``prior``.
                if boundary.generation != replay.current_generation:
                    raise ProspectiveV2IntegrityError(
                        "prospective boundary generation differs from replay"
                    )
                queue_ids = tuple(replay.sealed_request_ids)
                if replay.structural_mode is StructuralMode.EVENT_DRIVEN:
                    self._boundary_replay_retire(
                        replay, getattr(boundary, "retired_cell_ids", ())
                    )
                trailing_ids = tuple(
                    request_id for request_id in queue_ids
                    if request_id in self.request_consumptions
                    and request_id not in replay.request_consumptions
                )
                self._boundary_replay_materialize_children(
                    replay,
                    generation=replay.current_generation,
                    request_ids=trailing_ids,
                    include_promotions=(
                        replay.structural_mode is StructuralMode.EVENT_DRIVEN
                    ),
                )
                replay.structural_request_plans = {}
                prepared_structural_successor = True

            prior = (
                replay.base.continuation_digest_v3()
                if first_initial_structural
                else replay._boundary_prior_continuation_digest()
            )
            prior_schema = (
                BOUNDARY_DIGEST_SCHEMA_BASE_V3
                if first_initial_structural
                else replay.boundary_digest_schema
            )
            if boundary.prior_continuation_digest != prior:
                raise ProspectiveV2IntegrityError(
                    "generation boundary prior continuation differs from replay"
                )

            if first_initial_structural:
                if getattr(boundary, "retired_cell_ids", ()):
                    raise ProspectiveV2IntegrityError(
                        "initial structural boundary retires a state"
                    )
                # ``close_nomination`` records the initial structural
                # boundary before mutating the live phase.  The immediately
                # following generation-zero prospective boundary therefore
                # hashes a continuation whose phase is still OPEN.
                initial_boundary_phase = replay.generation_phase
                replay.generation_phase = GenerationPhase.STRUCTURAL_OPEN
                queue_ids: tuple[str, ...] = ()
            elif prepared_structural_successor:
                replay.generation_phase = GenerationPhase.PROSPECTIVE_OPEN
            elif (
                current is GenerationPhase.PROSPECTIVE_OPEN
                and phase is GenerationPhase.PROSPECTIVE_SEALED
            ):
                if boundary.generation != replay.current_generation:
                    raise ProspectiveV2IntegrityError(
                        "sealed boundary generation differs from replay"
                    )
                # The replay seed maintains the bounded pending order.  Do
                # not rescan the append-only lifetime request queue at every
                # sealed boundary.
                queue_ids = tuple(
                    request_id for request_id in replay._pending_request_order
                    if (
                        replay.deferred_requests[request_id].source_generation
                        == replay.current_generation
                    )
                )
                replay.sealed_request_ids = queue_ids
                replay.sealed_request_queue_digest = replay._request_queue_digest(
                    queue_ids
                )
                replay.generation_phase = GenerationPhase.PROSPECTIVE_SEALED
            elif (
                current is GenerationPhase.PROSPECTIVE_SEALED
                and phase is GenerationPhase.STRUCTURAL_OPEN
            ):
                if boundary.generation != replay.current_generation + 1:
                    raise ProspectiveV2IntegrityError(
                        "structural boundary generation skips replay"
                    )
                replay.current_generation += 1
                replay.generation_phase = GenerationPhase.STRUCTURAL_OPEN
                queue_ids = tuple(replay.sealed_request_ids)
                if replay.structural_mode is StructuralMode.SCHEDULED:
                    self._boundary_replay_retire(
                        replay, getattr(boundary, "retired_cell_ids", ())
                    )
                    replay.structural_request_plans = {
                        request_id: self.structural_request_plans[request_id]
                        for request_id in queue_ids
                        if request_id in self.structural_request_plans
                    }
                elif getattr(boundary, "retired_cell_ids", ()):
                    raise ProspectiveV2IntegrityError(
                        "event-driven structural boundary retires a state"
                    )
            elif (
                current is GenerationPhase.STRUCTURAL_OPEN
                and phase is GenerationPhase.PROSPECTIVE_OPEN
            ):
                if boundary.generation != replay.current_generation:
                    raise ProspectiveV2IntegrityError(
                        "prospective boundary generation differs from replay"
                    )
                queue_ids = tuple(replay.sealed_request_ids)
                if replay.structural_mode is StructuralMode.EVENT_DRIVEN:
                    self._boundary_replay_retire(
                        replay, getattr(boundary, "retired_cell_ids", ())
                    )
                self._boundary_replay_materialize_children(
                    replay,
                    generation=replay.current_generation,
                    request_ids=queue_ids,
                    include_promotions=(
                        replay.structural_mode is StructuralMode.EVENT_DRIVEN
                    ),
                )
                replay.structural_request_plans = {}
                replay.generation_phase = GenerationPhase.PROSPECTIVE_OPEN
            elif (
                current is GenerationPhase.PROSPECTIVE_OPEN
                and phase is GenerationPhase.PROSPECTIVE_OPEN
            ):
                if boundary.generation != replay.current_generation:
                    raise ProspectiveV2IntegrityError(
                        "direct retirement boundary generation differs"
                    )
                queue_ids = tuple(replay.sealed_request_ids)
                self._boundary_replay_retire(
                    replay, getattr(boundary, "retired_cell_ids", ())
                )
            else:
                raise ProspectiveV2IntegrityError(
                    "generation boundary phase chronology is invalid"
                )

            self._boundary_replay_assert_fields(
                replay,
                boundary,
                queue_ids=queue_ids,
                prior_digest=prior,
                prior_digest_schema=prior_schema,
            )
            if initial_boundary_phase is not None:
                replay.generation_phase = initial_boundary_phase
            replay.generation_boundaries.append(boundary)
            replay._advance_boundary_commitment(
                "generation_boundary", boundary.manifest()
            )
            boundary_index += 1

        while receipt_index < len(ordered) or boundary_index < len(boundaries):
            apply_semantic_births()
            next_frontier = (
                boundaries[boundary_index].event_frontier
                if boundary_index < len(boundaries)
                else None
            )
            if (
                next_frontier is not None
                and receipt_index < len(ordered)
                and ordered[receipt_index].ordinal < next_frontier
            ):
                receipt = ordered[receipt_index]
                if receipt.ordinal != replay.next_expected_ordinal:
                    raise ProspectiveV2IntegrityError(
                        "replay receipt ordinal differs from frontier"
                    )
                consume_receipt(receipt)
                receipt_index += 1
                continue
            if boundary_index < len(boundaries):
                apply_boundary(boundaries[boundary_index])
                continue
            if receipt_index < len(ordered):
                receipt = ordered[receipt_index]
                if receipt.ordinal != replay.next_expected_ordinal:
                    raise ProspectiveV2IntegrityError(
                        "replay receipt ordinal differs from frontier"
                    )
                consume_receipt(receipt)
                receipt_index += 1

        apply_semantic_births()
        if birth_index != len(births):
            raise ProspectiveV2IntegrityError("unreplayed semantic hypothesis births")
        # A scheduled structural safe point is intentionally resumable: the
        # boundary is recorded before its one-at-a-time compatibility API
        # consumes/materializes the sealed queue, and the prospective boundary
        # is recorded only when that API is closed.  Replay those trailing
        # ledger entries when a checkpoint was taken in STRUCTURAL_OPEN.
        if replay.generation_phase is GenerationPhase.STRUCTURAL_OPEN:
            trailing_ids = tuple(
                request_id for request_id in replay.sealed_request_ids
                if request_id in self.request_consumptions
                and request_id not in replay.request_consumptions
            )
            self._boundary_replay_materialize_children(
                replay,
                generation=replay.current_generation,
                request_ids=trailing_ids,
                include_promotions=False,
            )
            replay.structural_request_plans = {
                request_id: self.structural_request_plans[request_id]
                for request_id in replay.sealed_request_ids
                if request_id in self.structural_request_plans
            }

        if self.pending_event is not None:
            pending = self.pending_event
            transaction = self.event_transactions.get(pending.pending_token)
            if not isinstance(transaction, Mapping):
                raise ProspectiveV2IntegrityError(
                    "pending event lacks its transaction during replay"
                )
            if transaction.get("structure_invariant_digest") != (
                replay._structure_invariant_digest()
            ):
                raise ProspectiveV2IntegrityError(
                    "pending transaction structure digest differs from replay"
                )
            if pending.structure_invariant_digest != (
                replay._structure_invariant_digest()
            ):
                raise ProspectiveV2IntegrityError(
                    "pending event structure digest differs from replay"
                )
            replay._ensure_incremental_history_initialized()
            replay.pending_event = pending
            replay.event_transactions[pending.pending_token] = pending.manifest()
            replay._advance_boundary_commitment(
                "real_open", pending.manifest()
            )

        # This final equality closes all fields not represented by a boundary
        # digest as well, while still keeping the actual reconstruction to one
        # chronological pass.
        replay_manifest = replay.continuation_manifest()
        persisted_manifest = self.continuation_manifest()
        if replay_manifest != persisted_manifest:
            differing = tuple(
                key for key in persisted_manifest
                if replay_manifest.get(key) != persisted_manifest[key]
            )
            raise ProspectiveV2IntegrityError(
                "full boundary replay differs from persisted continuation: "
                + ",".join(differing)
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
        retirement_metadata = {
            cell_id: {
                "retirement_generation": getattr(
                    state, "retirement_generation", None
                ),
                "retirement_ordinal": getattr(
                    state, "retirement_ordinal", None
                ),
                "retirement_reason": getattr(
                    state, "retirement_reason", None
                ),
                "retirement_tombstone_digest": getattr(
                    state, "retirement_tombstone_digest", None
                ),
            }
            for cell_id, state in self.states.items()
            if getattr(state, "retired", False)
        }
        for cell_id, metadata in retirement_metadata.items():
            if not isinstance(metadata["retirement_ordinal"], int):
                raise ProspectiveV2IntegrityError(
                    "retired state lacks a replayable retirement ordinal"
                )

        births_by_generation: dict[
            int, list[tuple[str, ProspectiveAuthorityState]]
        ] = {}
        for cell_id, state in derived.items():
            births_by_generation.setdefault(
                state.hypothesis.source_generation, []
            ).append((cell_id, state))
        birth_generations = tuple(sorted(births_by_generation))
        next_birth_generation = 0
        active_derived = _LiveAuthorityStateView()
        promotion_by_child = {
            self._adaptive_boundary_child_id(request): (
                candidate_id, request.manifest()
            )
            for candidate_id, request in self.boundary_promotion_requests.items()
        }
        active_promotion_manifests: dict[str, dict[str, Any]] = {}

        def activate_births_through(generation: int) -> None:
            """Enter each born state into replay's bounded live index once."""

            nonlocal next_birth_generation
            while (
                next_birth_generation < len(birth_generations)
                and birth_generations[next_birth_generation] <= generation
            ):
                birth_generation = birth_generations[next_birth_generation]
                for cell_id, state in births_by_generation[birth_generation]:
                    if state.hypothesis.hypothesis_birth_digest is not None:
                        candidate_request = self.boundary_promotion_requests.get(
                            next((key for key, item in self.boundary_promotion_requests.items()
                                  if self._adaptive_boundary_child_id(item) == cell_id), "")
                        )
                        if candidate_request is None:
                            raise ProspectiveV2IntegrityError("continuous replay child lacks promotion request")
                        self._transfer_continuous_boundary_evidence(state, candidate_request)
                    if not state.retired:
                        active_derived[cell_id] = state
                        promotion = promotion_by_child.get(cell_id)
                        if promotion is not None:
                            candidate_id, manifest = promotion
                            active_promotion_manifests[candidate_id] = manifest
                    if state.hypothesis.provenance_schema_version == (
                        PROVENANCE_COMMITMENT_V4
                    ):
                        active_derived.topology_schema_version = (
                            "native_v2_authority_topology.v2_digest_only"
                        )
                next_birth_generation += 1

        retirement_schedule = tuple(sorted(
            (
                int(metadata["retirement_ordinal"]),
                cell_id,
                metadata,
            )
            for cell_id, metadata in retirement_metadata.items()
        ))
        next_retirement = 0

        def apply_retirements_through(ordinal: int) -> None:
            """Apply safe-point retirements at their exact ledger ordinal."""

            nonlocal next_retirement
            while (
                next_retirement < len(retirement_schedule)
                and retirement_schedule[next_retirement][0] <= ordinal
            ):
                retirement_ordinal, cell_id, metadata = (
                    retirement_schedule[next_retirement]
                )
                next_retirement += 1
                state = derived[cell_id]
                if state.retired:
                    continue
                state.retired = True
                state.prospectively_certified = False
                state.retirement_generation = metadata[
                    "retirement_generation"
                ]
                state.retirement_ordinal = retirement_ordinal
                state.retirement_reason = metadata["retirement_reason"]
                state.retirement_tombstone_digest = metadata[
                    "retirement_tombstone_digest"
                ]
                active_derived.pop(cell_id, None)
                promotion = promotion_by_child.get(cell_id)
                if promotion is not None:
                    active_promotion_manifests.pop(promotion[0], None)
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
        replay_lifetime: list[str] = []
        replay_lifetime_index: set[str] = set()
        replay_queue_digest = _empty_hot_append_digest("request_queue")
        replay_lifetime_digest = _empty_hot_append_digest(
            "requested_parent"
        )
        if ordered and self.incremental_history_state is None:
            raise ProspectiveV2IntegrityError(
                "incremental history missing for accepted REAL events"
            )
        replay_history = (
            self._new_incremental_history_state()
            if self.incremental_history_state is not None
            else None
        )
        replay_generation = -1
        semantic_births = tuple(sorted(self.boundary_hypothesis_births.values(), key=lambda item: item.sequence))
        semantic_cursor = 0
        semantic_digest = ""
        for offset, receipt in enumerate(ordered):
            if receipt.ordinal != expected_start + offset:
                raise ProspectiveV2IntegrityError(
                    "accepted receipt ledger has ordinal gap"
                )
            reference = self.accepted_real_references.get(receipt.receipt_id)
            if reference is None:
                raise ProspectiveV2IntegrityError(
                    "accepted REAL reference is absent"
                )
            if reference.source_generation < replay_generation:
                raise ProspectiveV2IntegrityError(
                    "accepted REAL source generation is not monotone"
                )
            replay_generation = reference.source_generation
            while semantic_cursor < len(semantic_births) and semantic_births[semantic_cursor].birth_frontier_ordinal < receipt.ordinal:
                birth = semantic_births[semantic_cursor]
                semantic_cursor += 1
                semantic_digest = _next_hot_append_digest(
                    semantic_digest or _empty_hot_append_digest("hypothesis_birth"),
                    "hypothesis_birth", birth.manifest(), semantic_cursor,
                )
            activate_births_through(replay_generation)
            # A retirement is committed at ``next_expected_ordinal``.  It is
            # therefore visible to the predecessor graph of a receipt at the
            # same ordinal, but remains live for every earlier receipt.
            apply_retirements_through(receipt.ordinal)
            if self.consumed_receipts.get(receipt.receipt_id) != receipt:
                raise ProspectiveV2IntegrityError(
                    "accepted receipt key differs from receipt identity"
                )
            if receipt.pending_token in expected_tokens:
                raise ProspectiveV2IntegrityError("duplicate consumed token")
            if receipt.interaction_fingerprint in (
                self._discovery_prefix_physical_fingerprint_set
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
                    states=active_derived,
                    generation=reference.source_generation,
                    next_ordinal=receipt.ordinal,
                    request_ids=replay_queue,
                    lifetime_requested_parent_ids=replay_lifetime,
                    request_queue_digest=replay_queue_digest,
                    requested_parent_digest=replay_lifetime_digest,
                    boundary_promotion_digest=_sha(
                        active_promotion_manifests
                    ),
                    hypothesis_birth_digest=semantic_digest,
                )
            )
            if transaction.get(
                "predecessor_continuation_digest"
            ) != predecessor_digest:
                raise ProspectiveV2IntegrityError(
                    "incremental history predecessor disagreement "
                    f"at ordinal {receipt.ordinal}"
                )
            pre_graph = _run_authority_graph(
                active_derived,
                AuthorityMeasurementSnapshot(receipt.trace, None),
                accepted_real_references=replay_references,
                specialization_mode=self.specialization_mode,
                lifetime_requested_parent_ids=replay_lifetime_index,
                specialization_genome_seed=self.specialization_genome_seed,
                compact_provenance=(
                    self.boundary_digest_schema
                    == BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
                ),
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
                lifetime_requested_parent_ids=replay_lifetime_index,
                specialization_genome_seed=self.specialization_genome_seed,
                compact_provenance=(
                    self.boundary_digest_schema
                    == BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
                ),
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
                    already_requested=parent_id in replay_lifetime_index,
                    graph_revocation_confirmed=(
                        parent_id in graph["revocation"]
                    ),
                    candidate_rows=request_rows.get(parent_id, ()),
                    compact_provenance=(
                        self.boundary_digest_schema
                        == BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
                    ),
                )
                for parent_id in graph["specialization_request"]
            )
            for cell_id in matching:
                state = active_derived[cell_id]
                state.support += 1
                self._append_state_ledger(
                    state,
                    "certification_receipt_ids",
                    receipt.receipt_id,
                )
                if cell_id in supporting:
                    state.successes += 1
                    self._append_state_ledger(
                        state,
                        "support_receipt_ids",
                        receipt.receipt_id,
                    )
                else:
                    state.contradictions += 1
                    self._append_state_ledger(
                        state,
                        "contradiction_receipt_ids",
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
                    self._append_state_ledger(
                        state,
                        "transition_rows",
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
                replay_queue_digest = _next_hot_append_digest(
                    replay_queue_digest,
                    "request_queue",
                    request.request_id,
                    len(replay_queue),
                )
                if request.parent_cell_id not in replay_lifetime_index:
                    replay_lifetime_index.add(request.parent_cell_id)
                    replay_lifetime.append(request.parent_cell_id)
                    replay_lifetime_digest = _next_hot_append_digest(
                        replay_lifetime_digest,
                        "requested_parent",
                        request.parent_cell_id,
                        len(replay_lifetime),
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
        activate_births_through(self.current_generation)
        apply_retirements_through(expected_start + len(ordered))
        replay_retirements = self._retirement_state_projection(derived)
        if self._boundary_retirement_projection(
            self.generation_boundaries
        ) != replay_retirements:
            raise ProspectiveV2IntegrityError(
                "generation boundary retirement audit differs from replay"
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
        if tuple(self.lifetime_requested_parent_ids) != tuple(replay_lifetime):
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
            self._hot_live_states(),
            AuthorityMeasurementSnapshot(trace, receipt),
            accepted_real_references=self.accepted_real_references,
            current_real_reference=current_real_reference,
            specialization_mode=self.specialization_mode,
            lifetime_requested_parent_ids=self._requested_parent_index,
            specialization_genome_seed=self.specialization_genome_seed,
            compact_provenance=(
                self.boundary_digest_schema
                == BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
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

    def _accepted_real_prefix_commitment(
        self,
        accepted_real_references: Mapping[str, AcceptedRealReference],
        current_reference: AcceptedRealReference | None = None,
        *,
        query_digest: str | None = None,
    ) -> ProvenanceCommitment:
        """Commit to the accepted-REAL prefix without copying its IDs.

        The normal REAL path advances the already-maintained mutation-chain
        digest once for the current reference.  Replay/audit callers may pass
        a detached mapping; those are explicitly allowed to reconstruct the
        digest once, never once per persisted child.
        """

        current_is_authority_ledger = (
            accepted_real_references is self.accepted_real_references
        )
        if current_is_authority_ledger:
            digest = self._accepted_real_ledger_digest()
            count = len(accepted_real_references)
            if current_reference is not None and (
                current_reference.receipt_id not in accepted_real_references
            ):
                digest = _next_hot_append_digest(
                    digest,
                    "boundary_accepted_real",
                    current_reference.manifest(),
                    count + 1,
                )
                count += 1
        else:
            ordered = tuple(sorted(
                accepted_real_references.values(),
                key=lambda item: (item.ordinal, item.receipt_id),
            ))
            if current_reference is not None and all(
                item.receipt_id != current_reference.receipt_id
                for item in ordered
            ):
                ordered = (*ordered, current_reference)
                ordered = tuple(sorted(
                    ordered,
                    key=lambda item: (item.ordinal, item.receipt_id),
                ))
            digest = _append_log_digest(
                tuple(item.manifest() for item in ordered),
                kind="boundary_accepted_real",
            )
            count = len(ordered)
        witnesses = ()
        if current_is_authority_ledger:
            witnesses = tuple(getattr(
                self, "_accepted_real_prefix_witness_ids", ()
            ))
            if current_reference is not None and (
                current_reference.receipt_id
                not in accepted_real_references
            ):
                witnesses = _bounded_provenance_witnesses((
                    *witnesses,
                    current_reference.receipt_id,
                ))
        else:
            witnesses = _bounded_provenance_witnesses(
                tuple(item.receipt_id for item in ordered)
            )
        return ProvenanceCommitment(
            schema_version=PROVENANCE_COMMITMENT_V4,
            digest=digest,
            count=count,
            exclusive_frontier=(
                self.next_expected_ordinal
                if current_reference is None
                else max(self.next_expected_ordinal, current_reference.ordinal + 1)
            ),
            witness_ids=witnesses,
            query_digest=query_digest,
        )

    def _accepted_real_prefix_commitment_at(
        self,
        exclusive_frontier: int,
    ) -> ProvenanceCommitment:
        """Reclose one accepted-REAL prefix at an explicit audit boundary.

        V4 births retain only this commitment and bounded witnesses.  The
        complete chronology is therefore reconstructed only here (load/full
        history validation), never once per event or per child on the hot
        path.  The same append-log kind and ordinal order as the maintained
        rolling digest are used so a count/frontier or digest tamper cannot
        be hidden by the bounded witness sample.
        """

        try:
            frontier = int(exclusive_frontier)
        except (TypeError, ValueError) as exc:
            raise ProspectiveV2IntegrityError(
                "compact exclusion frontier is malformed"
            ) from exc
        if isinstance(exclusive_frontier, bool) or frontier < 0:
            raise ProspectiveV2IntegrityError(
                "compact exclusion frontier is malformed"
            )
        return self._accepted_real_prefix_commitments((frontier,))[frontier]

    def _accepted_real_prefix_commitments(
        self,
        exclusive_frontiers: Sequence[int],
    ) -> dict[int, ProvenanceCommitment]:
        """Reclose any number of historical prefixes in one ledger pass."""

        frontiers: list[int] = []
        for value in exclusive_frontiers:
            try:
                frontier = int(value)
            except (TypeError, ValueError) as exc:
                raise ProspectiveV2IntegrityError(
                    "compact exclusion frontier is malformed"
                ) from exc
            if isinstance(value, bool) or frontier < 0:
                raise ProspectiveV2IntegrityError(
                    "compact exclusion frontier is malformed"
                )
            if frontier > self.next_expected_ordinal:
                raise ProspectiveV2IntegrityError(
                    "compact exclusion frontier exceeds the accepted REAL "
                    "ledger"
                )
            frontiers.append(frontier)
        requested = tuple(sorted(set(frontiers)))
        if not requested:
            return {}
        ordered_ids = tuple(getattr(
            self, "_accepted_real_reference_order", ()
        ))
        if (
            len(ordered_ids) != len(self.accepted_real_references)
            or set(ordered_ids) != set(self.accepted_real_references)
        ):
            ordered_ids = tuple(
                reference.receipt_id
                for reference in sorted(
                    self.accepted_real_references.values(),
                    key=lambda item: (item.ordinal, item.receipt_id),
                )
            )
        ordered = tuple(
            self.accepted_real_references[receipt_id]
            for receipt_id in ordered_ids
        )
        result: dict[int, ProvenanceCommitment] = {}
        digest = _empty_hot_append_digest("boundary_accepted_real")
        count = 0
        witnesses: tuple[str, ...] = ()
        for frontier in requested:
            while count < len(ordered) and ordered[count].ordinal < frontier:
                reference = ordered[count]
                digest = _next_hot_append_digest(
                    digest,
                    "boundary_accepted_real",
                    reference.manifest(),
                    count + 1,
                )
                witnesses = _bounded_provenance_witnesses((
                    *witnesses,
                    reference.receipt_id,
                ))
                count += 1
            result[frontier] = ProvenanceCommitment(
                schema_version=PROVENANCE_COMMITMENT_V4,
                digest=digest,
                count=count,
                exclusive_frontier=frontier,
                witness_ids=witnesses,
            )
        return result

    def _validate_compact_exclusion_commitment(
        self,
        commitment: ProvenanceCommitment,
        *,
        birth_frontier: int,
        label: str,
        prefix_commitments: Mapping[int, ProvenanceCommitment] | None = None,
    ) -> None:
        """Fail closed when a compact discovery prefix disagrees with REAL."""

        if not isinstance(commitment, ProvenanceCommitment):
            raise ProspectiveV2IntegrityError(
                f"{label} lacks compact exclusion commitment"
            )
        if commitment.exclusive_frontier != birth_frontier + 1:
            raise ProspectiveV2IntegrityError(
                f"{label} compact exclusion frontier mismatch"
            )
        expected = (
            prefix_commitments.get(commitment.exclusive_frontier)
            if prefix_commitments is not None
            else self._accepted_real_prefix_commitment_at(
                commitment.exclusive_frontier
            )
        )
        if expected is None:
            raise ProspectiveV2IntegrityError(
                f"{label} compact exclusion frontier was not reclosed"
            )
        if expected != commitment:
            raise ProspectiveV2IntegrityError(
                f"{label} compact exclusion commitment mismatch"
            )

    def _validate_compact_ordinary_birth_contract(
        self,
        request: BoundaryPromotionRequest,
        escrow: NominationEscrow,
        hypothesis: FrozenHypothesis,
    ) -> None:
        """Re-derive every V4 ordinary birth edge from its exact request."""

        frontier = escrow.birth_frontier + 1
        continuous = request.hypothesis_birth_digest is not None
        if continuous:
            birth = self._continuous_birth_for_request(request)
            if (hypothesis.hypothesis_birth_digest != birth.birth_digest
                or hypothesis.birth_frontier != birth.birth_frontier_ordinal
                or hypothesis.semantic_source_identity != birth.source_identity
                or hypothesis.semantic_member_roles != birth.member_signal_roles
                or escrow.discovery_exclusion_commitment != birth.discovery_exclusion_commitment):
                raise ProspectiveV2IntegrityError("continuous birth escrow differs from precommitment")
        consensus = tuple(sorted(
            set(request.inspected_receipt_ids)
            - {request.triggering_receipt_id}
        )) if not continuous else ()
        expected_categories = (
            ("direct", (request.triggering_receipt_id,)),
            ("parent_support", ()),
            ("eligibility", ()),
            ("contradiction_trigger", ()),
            ("consensus_reads", consensus),
        )
        expected_categories = tuple(
            (name, _bounded_provenance_witnesses(receipt_ids))
            for name, receipt_ids in expected_categories
        )
        expected_read_commitments = (
            ("direct", _compact_set_commitment(
                (request.triggering_receipt_id,),
                exclusive_frontier=frontier,
            )),
            ("parent_support", _compact_set_commitment(
                (), exclusive_frontier=frontier
            )),
            ("eligibility", _compact_set_commitment(
                (), exclusive_frontier=frontier
            )),
            ("contradiction_trigger", _compact_set_commitment(
                (), exclusive_frontier=frontier
            )),
            ("consensus_reads", request.inspected_receipt_commitment if not continuous else _compact_set_commitment((), exclusive_frontier=frontier)),
        )
        if any(
            not isinstance(commitment, ProvenanceCommitment)
            for _name, commitment in expected_read_commitments
        ):
            raise ProspectiveV2IntegrityError(
                "compact ordinary birth lacks request commitment"
            )
        expected_discovery = _compose_provenance_commitment(
            tuple(item for _name, item in expected_read_commitments),
            exclusive_frontier=frontier,
            query_digest=_compact_query_digest({
                "operation": "ordinary",
                "candidate_id": request.candidate_id,
            }),
        )
        if (
            escrow.categorized_reads != expected_categories
            or escrow.nomination_read_commitments
            != expected_read_commitments
            or hypothesis.nomination_read_sets != expected_categories
            or hypothesis.nomination_read_commitments
            != expected_read_commitments
            or hypothesis.discovery_read_commitment != expected_discovery
            or hypothesis.discovery_receipt_digest
            != expected_discovery.digest
            or hypothesis.discovery_receipt_ids
            != expected_discovery.witness_ids
            or hypothesis.discovery_support_receipt_ids
            != _bounded_provenance_witnesses(
                request.supporting_receipt_ids if not continuous else (request.triggering_receipt_id,)
            )
        ):
            raise ProspectiveV2IntegrityError(
                "compact ordinary birth diverges from promotion request"
            )

    def _validate_compact_deferred_birth_contract(
        self,
        request: DeferredSpecializationRequest,
        birth: DeferredChildBirth,
        escrow: NominationEscrow,
        hypothesis: FrozenHypothesis,
    ) -> None:
        """Re-derive every V4 specialization edge from request/candidate."""

        selected_identity = birth.members[1]
        semantic_contract = self._continuous_deferred_contract(
            request, selected_identity, frontier=hypothesis.birth_frontier
        )
        if semantic_contract is not None:
            source, roles, support, contradictions = semantic_contract
            if (hypothesis.semantic_source_identity != source
                or hypothesis.semantic_member_roles != roles
                or support < MIN_SUPPORT or contradictions):
                raise ProspectiveV2IntegrityError("deferred residual erased its typed/source/known-negative contract")
        elif hypothesis.semantic_source_identity is not None:
            raise ProspectiveV2IntegrityError("deferred semantic binding predates protocol activation")
        try:
            candidate = next(
                item for item in request.candidate_terminals
                if item.identity == selected_identity
            )
        except StopIteration as exc:
            raise ProspectiveV2IntegrityError(
                "compact deferred birth selected an unknown candidate"
            ) from exc
        commitments = (
            ("direct_child_matches", candidate.supporting_receipt_commitment),
            ("parent_discovery_reads", request.parent_discovery_commitment),
            (
                "parent_discovery_support",
                request.parent_discovery_support_commitment,
            ),
            (
                "parent_prospective_support",
                request.parent_prospective_support_commitment,
            ),
            ("eligibility_reads", candidate.inspected_receipt_commitment),
            ("contradiction_trigger", _compact_set_commitment(
                (request.contradiction_receipt_id,),
                exclusive_frontier=request.contradiction_ordinal + 1,
            )),
            ("transitive_ancestor_reads", request.transitive_ancestor_commitment),
        )
        if any(
            not isinstance(commitment, ProvenanceCommitment)
            for _name, commitment in commitments
        ):
            raise ProspectiveV2IntegrityError(
                "compact deferred birth lacks request commitment"
            )
        categories = (
            ("direct_child_matches", candidate.supporting_receipt_ids),
            (
                "parent_discovery_reads",
                request.parent_discovery_receipt_ids,
            ),
            (
                "parent_discovery_support",
                request.parent_discovery_support_receipt_ids,
            ),
            (
                "parent_prospective_support",
                request.parent_prospective_support_receipt_ids,
            ),
            ("eligibility_reads", candidate.inspected_receipt_ids),
            ("contradiction_trigger", (request.contradiction_receipt_id,)),
            (
                "transitive_ancestor_reads",
                request.transitive_ancestor_receipt_ids,
            ),
        )
        expected_categories = tuple(
            (name, _bounded_provenance_witnesses(receipt_ids))
            for name, receipt_ids in categories
        )
        expected_discovery = _compose_provenance_commitment(
            tuple(item for _name, item in commitments),
            exclusive_frontier=escrow.birth_frontier + 1,
            query_digest=_compact_query_digest({
                "operation": "specialization",
                "parent_hypothesis_digest": (
                    request.parent_hypothesis_digest
                ),
            }),
        )
        if (
            escrow.categorized_reads != expected_categories
            or escrow.nomination_read_commitments != commitments
            or escrow.transitive_ancestor_receipt_ids
            != tuple(sorted(request.transitive_ancestor_receipt_ids))
            or hypothesis.nomination_read_sets != expected_categories
            or hypothesis.nomination_read_commitments != commitments
            or hypothesis.discovery_read_commitment != expected_discovery
            or hypothesis.discovery_receipt_digest
            != expected_discovery.digest
            or hypothesis.discovery_receipt_ids
            != expected_discovery.witness_ids
            or hypothesis.discovery_support_receipt_ids
        ):
            raise ProspectiveV2IntegrityError(
                "compact deferred birth diverges from specialization request"
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
        compact_provenance: bool = False,
    ) -> DeferredSpecializationRequest:
        hypothesis = state.hypothesis
        # Request construction needs keyed access to the accepted ledger and
        # the current receipt.  A mapping overlay avoids cloning the full
        # lifetime reference map for each matching parent.
        references: Mapping[str, AcceptedRealReference] = _ReferenceOverlay(
            accepted_real_references,
            current_reference,
        )
        prior = references.get(current_reference.receipt_id)
        if prior is not None and prior != current_reference:
            raise ProspectiveV2IntegrityError(
                "request builder REAL reference collision"
            )
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
        if not compact_provenance:
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
        existing_reads = dict(hypothesis.nomination_read_commitments)
        parent_discovery_commitment = hypothesis.discovery_read_commitment
        if parent_discovery_commitment is None:
            parent_discovery_commitment = ProvenanceCommitment(
                schema_version=PROVENANCE_COMMITMENT_V4,
                digest=hypothesis.discovery_receipt_digest,
                count=len(hypothesis.discovery_receipt_ids),
                exclusive_frontier=hypothesis.certification_frontier + 1,
                witness_ids=_bounded_provenance_witnesses(
                    hypothesis.discovery_receipt_ids
                ),
            )
        parent_support_ids = hypothesis.discovery_support_receipt_ids
        parent_support_commitment = existing_reads.get(
            "parent_discovery_support"
        ) or existing_reads.get("parent_discovery_support_receipts")
        if parent_support_commitment is None:
            parent_support_commitment = _compact_set_commitment(
                parent_support_ids,
                exclusive_frontier=hypothesis.certification_frontier + 1,
            )
        parent_ancestor_commitment = existing_reads.get(
            "transitive_ancestor_reads"
        )
        if parent_ancestor_commitment is None:
            parent_ancestor_commitment = _compact_set_commitment(
                hypothesis.transitive_ancestor_receipt_ids,
                exclusive_frontier=hypothesis.certification_frontier + 1,
            )
        prospective_support_commitment = _compact_set_commitment(
            trigger.parent_prospective_support_receipt_ids,
            exclusive_frontier=receipt.ordinal + 1,
        )
        candidate_inspected_commitment = (
            candidate_rows[0].inspected_receipt_commitment
            if candidate_rows
            else _compact_set_commitment(
                (receipt.receipt_id,),
                exclusive_frontier=receipt.ordinal + 1,
            )
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
                parent_discovery_commitment.witness_ids
            ),
            parent_discovery_support_receipt_ids=(
                parent_support_commitment.witness_ids
            ),
            parent_prospective_support_receipt_ids=(
                prospective_support_commitment.witness_ids
            ),
            transitive_ancestor_receipt_ids=(
                parent_ancestor_commitment.witness_ids
            ),
            candidate_terminals=candidate_rows,
            graph_revocation_confirmed=graph_revocation_confirmed,
            graph_request_confirmed=True,
            provenance_schema_version=PROVENANCE_COMMITMENT_V4,
            parent_discovery_commitment=parent_discovery_commitment,
            parent_discovery_support_commitment=parent_support_commitment,
            parent_prospective_support_commitment=(
                prospective_support_commitment
            ),
            transitive_ancestor_commitment=parent_ancestor_commitment,
            parent_query_commitment=_compact_query_digest({
                "parent_cell_id": parent_cell_id,
                "parent_hypothesis_digest": hypothesis.hypothesis_digest,
                "triggering_receipt_id": receipt.receipt_id,
                "contradiction_receipt_id": (
                    trigger.contradiction_reference.receipt_id
                ),
                "specialization_mode": specialization_mode.value,
            }),
            candidate_inspected_commitment=candidate_inspected_commitment,
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
        available = tuple(
            item for item in emissions["available"]
            if item in states and not getattr(states[item], "retired", False)
        )
        refuted = tuple(
            item for item in emissions["refuted"]
            if item in states and not getattr(states[item], "retired", False)
        )
        # Keep the authority's raw prospective classification faithful to all
        # active hypotheses.  ``source_generation == 0`` identifies discovery
        # provenance, not the immutable native core graph/local gate.  Core
        # precedence is an execution-level routing decision in the curriculum;
        # filtering adaptive refutations here would hide descendant evidence
        # whenever the local core abstains and would corrupt REAL accounting.
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

    @staticmethod
    def _append_state_ledger(
        state: ProspectiveAuthorityState,
        name: str,
        value: Any,
        *,
        journal: _RealMutationJournal | None = None,
    ) -> None:
        values = getattr(state, name)
        if not isinstance(values, _AppendOnlyLedger):
            converted = _AppendOnlyLedger(values)
            if journal is None:
                setattr(state, name, converted)
            else:
                journal.set_attr(state, name, converted)
            values = converted
        if journal is None:
            values.append(value)
        else:
            journal.append(values, value)
        if name == "certification_receipt_ids":
            previous = getattr(state, "certification_receipt_digest", "")
            if not previous:
                previous = _empty_hot_append_digest("certification_receipt")
            digest = _next_hot_append_digest(
                previous,
                "certification_receipt",
                value,
                len(values),
            )
            if journal is None:
                state.certification_receipt_digest = digest
            else:
                journal.set_attr(
                    state, "certification_receipt_digest", digest
                )

    def frame_session(self) -> NativeV2FrameSession:
        """Open one non-serializable frozen-R0 execution session."""

        # Opening a curriculum frame session is a hot-path operation.  The
        # session freezes only the base/R0 source; the authority-local REAL
        # contracts are already covered by the bounded projection validator.
        # Full ledger/topology reclosure remains explicit at serialization or
        # audit boundaries.
        self._validate_real_hot_path(virtual=True)
        return NativeV2FrameSession(self)

    def open_real_event(
        self,
        frame: FrameContext,
        *,
        frame_session: NativeV2FrameSession | None = None,
        expected_actuation: Mapping[str, Any] | None = None,
    ) -> tuple[PendingRealEvent, GraphSignalTrace]:
        if frame_session is not None:
            frame_session._require_open(self)
        self._validate_real_hot_path(
            frozen_base_continuation_digest=(
                None
                if frame_session is None
                else frame_session.base_continuation_digest
            )
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
        before = self._hot_path_guard_digest()
        frozen_r0 = self.base.r0
        frozen_r0_guard = (
            frozen_r0.inference_guard_identity()
            if frame_session is None
            else None
        )
        history = self.incremental_history_state
        if history is None:
            history = self._new_incremental_history_state()
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
        # Bind the REAL action to the preceding VIRTUAL all-reply query before
        # installing a pending transaction.  A mismatch is therefore a pure
        # read failure: no pending token, boundary commitment, or revision is
        # left behind for the caller to recover.
        if expected_actuation is not None:
            if not isinstance(expected_actuation, Mapping):
                raise TypeError("expected REAL actuation must be a mapping")
            selected_move = str(actuation.move_uci)
            selected_triplet = str(
                getattr(
                    actuation,
                    "selected_triplet_id",
                    actuation.option_identity,
                )
            )
            exact_action_pattern_id = _triplet_id(*_triplet_keys(
                board,
                chess.Move.from_uci(selected_move),
                key_mode=frozen_r0.graph.config.key_mode,
            ))
            expected = {
                "selected_move": expected_actuation.get("selected_move"),
                "selected_triplet": expected_actuation.get(
                    "selected_triplet"
                ),
                "selected_option_identity": expected_actuation.get(
                    "selected_option_identity"
                ),
                "exact_action_pattern_id": expected_actuation.get(
                    "exact_action_pattern_id"
                ),
            }
            observed = {
                "selected_move": selected_move,
                "selected_triplet": selected_triplet,
                "selected_option_identity": str(actuation.option_identity),
                "exact_action_pattern_id": exact_action_pattern_id,
            }
            if observed != expected:
                raise ProspectiveV2IntegrityError(
                    "VIRTUAL/REAL child actuation parity mismatch: "
                    + json.dumps(
                        {"expected": expected, "observed": observed},
                        sort_keys=True,
                    )
                )
        if (
            frozen_r0_guard is not None
            and frozen_r0.inference_guard_identity() != frozen_r0_guard
        ):
            raise ProspectiveV2IntegrityError(
                "REAL prediction mutated its shared frozen R0 source"
            )
        graph = self._graph_measure(trace)
        matching = graph["commitment"]
        classification = self._classification_from_emissions(
            self.states, graph
        )
        typed_digest = _sha([
            asdict(item) for item in trace.terminal_signals
        ])
        structure_digest = getattr(self, "_hot_structure_digest", "")
        if not structure_digest:
            raise ProspectiveV2IntegrityError(
                "cached structure invariant digest is unavailable"
            )
        predecessor_continuation_digest = (
            self._incremental_predecessor_continuation_digest(history)
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
        after = self._hot_path_guard_digest()
        if after != before:
            raise ProspectiveV2IntegrityError(
                "prediction mutated persistent state"
            )
        if self.incremental_history_state is None:
            self.incremental_history_state = history
        self.pending_event = pending
        self.event_transactions[token] = pending.manifest()
        self._advance_boundary_commitment(
            "real_open", pending.manifest()
        )
        self._hot_path_revision += 1
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
        """Atomically consume one REAL result; never materialize a child.

        The old implementation deep-copied the complete authority before
        every append.  This path now mutates only the bounded matching states
        and append-only ledgers under a reversible journal; a late failure
        restores the exact pre-transaction object graph.
        """

        frozen_r0 = self.base.r0
        frozen_r0_guard = (
            frozen_r0.inference_guard_identity()
            if frame_session is None
            else None
        )
        if frame_session is not None:
            frame_session._require_open(self)
        journal = _RealMutationJournal()
        prior_journal = getattr(self, "_real_mutation_journal", None)
        self._real_mutation_journal = journal
        try:
            result = self._consume_in_place(
                receipt,
                frozen_base_continuation_digest=(
                    None
                    if frame_session is None
                    else frame_session.base_continuation_digest
                ),
            )
            if (
                frozen_r0_guard is not None
                and frozen_r0.inference_guard_identity() != frozen_r0_guard
            ):
                raise ProspectiveV2IntegrityError(
                    "REAL transaction mutated its shared frozen R0 source"
                )
        except Exception:
            journal.rollback()
            raise
        else:
            journal.commit()
            return result
        finally:
            if prior_journal is None:
                self.__dict__.pop("_real_mutation_journal", None)
            else:
                self._real_mutation_journal = prior_journal

    def _consume_in_place(
        self,
        receipt: V2GroundedReceipt,
        *,
        frozen_base_continuation_digest: str | None = None,
    ) -> V2CertificationEmission:
        """Journalled implementation wrapper used by direct test callers."""

        active = getattr(self, "_real_mutation_journal", None)
        if active is not None:
            return self._consume_in_place_core(
                receipt,
                frozen_base_continuation_digest=(
                    frozen_base_continuation_digest
                ),
            )
        journal = _RealMutationJournal()
        self._real_mutation_journal = journal
        try:
            result = self._consume_in_place_core(
                receipt,
                frozen_base_continuation_digest=(
                    frozen_base_continuation_digest
                ),
            )
        except Exception:
            journal.rollback()
            raise
        else:
            journal.commit()
            return result
        finally:
            self.__dict__.pop("_real_mutation_journal", None)

    def _consume_in_place_core(
        self,
        receipt: V2GroundedReceipt,
        *,
        frozen_base_continuation_digest: str | None = None,
    ) -> V2CertificationEmission:
        journal = getattr(self, "_real_mutation_journal", None)
        self._validate_real_hot_path(
            require_pending=False,
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
            != getattr(self, "_hot_structure_digest", "")
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
        if receipt.interaction_fingerprint in (
            self._discovery_prefix_physical_fingerprint_set
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
                    and _receipt_is_post_birth(
                        self.states[cell_id].hypothesis, receipt
                    )
                ),
                supports=cell_id in supporting_set,
                contradicts=cell_id in contradiction_set,
                specialization_mode=self.specialization_mode,
                already_requested=(
                    cell_id in self._requested_parent_index
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
                    parent_id in self._requested_parent_index
                ),
                graph_revocation_confirmed=(
                    parent_id in graph["revocation"]
                ),
                candidate_rows=candidate_rows_by_parent.get(parent_id, ()),
                compact_provenance=(
                    self.boundary_digest_schema
                    == BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
                ),
            )
            for parent_id in request_parent_ids
        )
        self._validate_request_append_capacity(new_requests)
        for cell_id in pending.matching_cell_ids:
            state = self.states[cell_id]
            if journal is None:
                state.support += 1
            else:
                journal.set_attr(state, "support", state.support + 1)
            self._append_state_ledger(
                state,
                "certification_receipt_ids",
                receipt.receipt_id,
                journal=journal,
            )
            if cell_id in supporting:
                if journal is None:
                    state.successes += 1
                else:
                    journal.set_attr(state, "successes", state.successes + 1)
                self._append_state_ledger(
                    state,
                    "support_receipt_ids",
                    receipt.receipt_id,
                    journal=journal,
                )
            else:
                if journal is None:
                    state.contradictions += 1
                else:
                    journal.set_attr(
                        state,
                        "contradictions",
                        state.contradictions + 1,
                    )
                self._append_state_ledger(
                    state,
                    "contradiction_receipt_ids",
                    receipt.receipt_id,
                    journal=journal,
                )
            success_lower_bound = wilson_lower_bound(
                state.successes, state.support, WILSON_Z
            )
            contradiction_lower_bound = wilson_lower_bound(
                state.contradictions, state.support, WILSON_Z
            )
            if journal is None:
                state.success_lower_bound = success_lower_bound
                state.contradiction_lower_bound = contradiction_lower_bound
            else:
                journal.set_attr(
                    state, "success_lower_bound", success_lower_bound
                )
                journal.set_attr(
                    state,
                    "contradiction_lower_bound",
                    contradiction_lower_bound,
                )
            transition = None
            if cell_id in graph["maturity"]:
                if journal is None:
                    state.prospectively_certified = True
                else:
                    journal.set_attr(state, "prospectively_certified", True)
                transition = "GRAPH_PROSPECTIVE_MATURITY"
            if cell_id in graph["revocation"]:
                if journal is None:
                    state.prospectively_certified = False
                else:
                    journal.set_attr(state, "prospectively_certified", False)
                transition = "GRAPH_LOCAL_REVOCATION"
            if transition is not None:
                self._append_state_ledger(
                    state,
                    "transition_rows",
                    {
                        "transition": transition,
                        "receipt_id": receipt.receipt_id,
                        "ordinal": receipt.ordinal,
                        "pending_token": receipt.pending_token,
                    },
                    journal=journal,
                )
        self._record_boundary_decision(
            "real_consume",
            {
                cell_id: self._boundary_decision_row(
                    cell_id, self.states[cell_id]
                )
                for cell_id in pending.matching_cell_ids
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
        if journal is None:
            self.consumed_receipts[receipt.receipt_id] = receipt
            self.consumed_tokens.add(receipt.pending_token)
            self.prospective_physical_fingerprints[
                receipt.interaction_fingerprint
            ] = receipt.receipt_id
            self.emissions[receipt.receipt_id] = emission
        else:
            journal.add_mapping(
                self.consumed_receipts, receipt.receipt_id, receipt
            )
            journal.add_set(self.consumed_tokens, receipt.pending_token)
            journal.add_mapping(
                self.prospective_physical_fingerprints,
                receipt.interaction_fingerprint,
                receipt.receipt_id,
            )
            journal.add_mapping(
                self.emissions, receipt.receipt_id, emission
            )
        reference = current_reference
        if reference.receipt_id in self.accepted_real_references:
            raise ProspectiveV2IntegrityError(
                "accepted REAL reference identity collision"
            )
        if journal is None:
            self.accepted_real_references[reference.receipt_id] = reference
        else:
            journal.add_mapping(
                self.accepted_real_references,
                reference.receipt_id,
                reference,
            )
        self._mutation_append(
            self._accepted_real_reference_order, reference.receipt_id
        )
        self._mutation_append(
            self._accepted_real_reference_ordinals, reference.ordinal
        )
        self._mutation_set_attr(
            self,
            "_accepted_real_prefix_witness_ids",
            _bounded_provenance_witnesses((
                *self._accepted_real_prefix_witness_ids,
                reference.receipt_id,
            )),
        )
        for identity in reference.ordered_signal_identities:
            signal_index = self._accepted_real_by_signal_identity.get(identity)
            if signal_index is None:
                signal_index = _AppendOnlyLedger()
                self._mutation_add_mapping(
                    self._accepted_real_by_signal_identity,
                    identity,
                    signal_index,
                )
            self._mutation_append(signal_index, reference.receipt_id)
        self._record_boundary_accepted_real(reference)
        for request in new_requests:
            if request.request_id in self.deferred_requests:
                raise ProspectiveV2IntegrityError(
                    "deferred request identity collision"
                )
            if journal is None:
                self.deferred_requests[request.request_id] = request
            else:
                journal.add_mapping(
                    self.deferred_requests,
                    request.request_id,
                    request,
                )
        queue = self.request_queue
        lifetime = self.lifetime_requested_parent_ids
        for request in new_requests:
            if journal is None:
                queue.append(request.request_id)
            else:
                journal.append(queue, request.request_id)
            if journal is None:
                self._pending_request_order.append(request.request_id)
            else:
                journal.append(
                    self._pending_request_order, request.request_id
                )
            if journal is None:
                self._pending_request_index.add(request.request_id)
            else:
                journal.add_set(
                    self._pending_request_index, request.request_id
                )
            queue_count = len(queue)
            if journal is None:
                self._request_queue_hot_digest = _next_hot_append_digest(
                    self._request_queue_hot_digest,
                    "request_queue",
                    request.request_id,
                    queue_count,
                )
            else:
                journal.set_attr(
                    self,
                    "_request_queue_hot_digest",
                    _next_hot_append_digest(
                        self._request_queue_hot_digest,
                        "request_queue",
                        request.request_id,
                        queue_count,
                    ),
                )
        for parent_id in request_parent_ids:
            if parent_id in self._requested_parent_index:
                continue
            if journal is None:
                self._requested_parent_index.add(parent_id)
                lifetime.append(parent_id)
            else:
                journal.add_set(self._requested_parent_index, parent_id)
                journal.append(lifetime, parent_id)
            parent_count = len(lifetime)
            new_digest = _next_hot_append_digest(
                self._requested_parent_hot_digest,
                "requested_parent",
                parent_id,
                parent_count,
            )
            if journal is None:
                self._requested_parent_hot_digest = new_digest
            else:
                journal.set_attr(
                    self, "_requested_parent_hot_digest", new_digest
                )
        if journal is None:
            self.next_expected_ordinal += 1
        else:
            journal.set_attr(
                self,
                "next_expected_ordinal",
                self.next_expected_ordinal + 1,
            )
        transaction = {
            **pending.manifest(),
            "state": "CONSUMED",
            "consumed_receipt_id": receipt.receipt_id,
        }
        if journal is None:
            self.event_transactions[receipt.pending_token] = transaction
        else:
            journal.add_mapping(
                self.event_transactions,
                receipt.pending_token,
                transaction,
            )
        self._append_incremental_history(
            receipt=receipt,
            transaction=transaction,
            reference=reference,
            emission=emission,
        )
        if journal is not None:
            journal.set_attr(self, "pending_event", None)
            journal.set_attr(
                self, "_hot_path_revision", self._hot_path_revision + 1
            )
        else:
            self.pending_event = None
        self._validate_real_hot_path()
        self._advance_boundary_commitment(
            "real_consume",
            {
                "receipt": receipt.manifest(),
                "transaction": transaction,
                "accepted_reference": reference.manifest(),
                "emission": emission.manifest(),
            },
        )
        return emission

    def _pending_request_ids(self) -> tuple[str, ...]:
        """Return the bounded, retryable part of the request ledger.

        ``request_queue`` is deliberately append-only for replay and audit,
        so its length is a lifetime cardinality rather than a resource
        occupancy.  Only requests which have not yet been consumed occupy the
        active structural queue slot.
        """

        pending_order = getattr(self, "_pending_request_order", None)
        if pending_order is not None:
            if not getattr(self, "_hot_path_indexes_ready", False):
                if not hasattr(self, "structural_invariants"):
                    # Minimal object.__new__ structural fixtures have no REAL
                    # topology to refresh.  Keep their compatibility path
                    # outside production rather than forcing a fabricated
                    # authority manifest merely to consume a sealed batch.
                    queue = tuple(getattr(self, "request_queue", ())) or tuple(
                        getattr(self, "sealed_request_ids", ())
                    )
                    consumptions = set(getattr(
                        self, "request_consumptions", {}
                    ))
                    return tuple(
                        request_id for request_id in queue
                        if request_id not in consumptions
                    )
                # One-time compatibility path for pre-cache pickles (and
                # freshly hand-built authorities).  It performs the required
                # full refresh once; subsequent event-driven safe points use
                # the maintained order directly.
                self._ensure_hot_path_indexes()
                pending_order = self._pending_request_order
            # Do not derive this from request_queue/request_consumptions on a
            # REAL/VIRTUAL safe point: both are lifetime ledgers.  The order
            # is maintained incrementally and is bounded by queue capacity.
            return tuple(pending_order)
        # Small data-free structural harnesses and pre-cache pickles may not
        # carry the runtime cache.  This compatibility fallback is confined
        # to those old/non-production objects; normal authorities always
        # receive the cache at the first full boundary.
        queue = tuple(getattr(self, "request_queue", ()))
        if not queue:
            queue = tuple(getattr(self, "sealed_request_ids", ()))
        consumptions = set(getattr(self, "request_consumptions", {}))
        return tuple(
            request_id for request_id in queue
            if request_id not in consumptions
        )

    def _validate_structural_consumption_fields(
        self,
        request_id: str,
        consumption: StructuralRequestConsumption,
        *,
        attempt_ordinal: int,
    ) -> None:
        """Validate one immutable request disposition before using it.

        Dispositions are a closed protocol, not free-form annotations.  In
        particular, capacity is handled by the safe-point planner before a
        request is consumed, so the historical ledger must never contain a
        synthetic capacity rejection.  This helper intentionally validates
        only the request-local record; the caller separately checks whether a
        deferred birth, live state, and escrow agree with that record.
        """

        if not isinstance(consumption, StructuralRequestConsumption):
            raise ProspectiveV2IntegrityError(
                "structural request consumption is malformed"
            )
        request = self.deferred_requests.get(request_id)
        if request is None:
            raise ProspectiveV2IntegrityError(
                "structural request consumption names an unknown request"
            )
        if (
            consumption.request_id != request_id
            or isinstance(consumption.attempt_ordinal, bool)
            or not isinstance(consumption.attempt_ordinal, int)
            or consumption.attempt_ordinal != attempt_ordinal
            or isinstance(consumption.genome_seed, bool)
            or not isinstance(consumption.genome_seed, int)
            or consumption.genome_seed != self.specialization_genome_seed
            or isinstance(consumption.genome_call_count, bool)
            or not isinstance(consumption.genome_call_count, int)
            or consumption.genome_call_count != 1
        ):
            raise ProspectiveV2IntegrityError(
                "structural request consumption identity mismatch"
            )
        if consumption.disposition not in _STRUCTURAL_CONSUMPTION_DISPOSITIONS:
            if consumption.disposition == "REJECTED_CHILD_CAPACITY":
                raise ProspectiveV2IntegrityError(
                    "REJECTED_CHILD_CAPACITY is not a legal disposition"
                )
            raise ProspectiveV2IntegrityError(
                "unknown structural request disposition"
            )
        if not isinstance(consumption.selected_members, tuple):
            raise ProspectiveV2IntegrityError(
                "structural request selected members are not canonical"
            )
        if any(
            not isinstance(member, str) or not member
            for member in consumption.selected_members
        ):
            raise ProspectiveV2IntegrityError(
                "structural request selected members are malformed"
            )
        if consumption.disposition == "REJECTED_EMPTY_ELIGIBILITY":
            if consumption.selected_members or consumption.child_cell_id is not None:
                raise ProspectiveV2IntegrityError(
                    "empty-eligibility disposition carries a child"
                )
            return
        if len(consumption.selected_members) != 2:
            raise ProspectiveV2IntegrityError(
                "structural request child members are not a context pair"
            )
        if (
            consumption.selected_members[0]
            != f"context:{request.parent_cell_id}"
            or consumption.selected_members[1] not in request.eligible_base_ids
        ):
            raise ProspectiveV2IntegrityError(
                "structural request child is outside request eligibility"
            )
        if consumption.disposition == "REJECTED_DUPLICATE_PATTERN":
            if consumption.child_cell_id is not None:
                raise ProspectiveV2IntegrityError(
                    "duplicate disposition carries a child identity"
                )
            return
        if (
            not isinstance(consumption.child_cell_id, str)
            or not consumption.child_cell_id
        ):
            raise ProspectiveV2IntegrityError(
                "child disposition lacks a child identity"
            )

    @staticmethod
    def _retirement_state_projection(
        states: Mapping[str, ProspectiveAuthorityState],
    ) -> tuple[tuple[int, int, tuple[str, ...]], ...]:
        """Project tombstoned states into deterministic safe-point batches."""

        grouped: dict[tuple[int, int], list[str]] = {}
        for cell_id, state in states.items():
            if not getattr(state, "retired", False):
                continue
            generation = getattr(state, "retirement_generation", None)
            ordinal = getattr(state, "retirement_ordinal", None)
            if not isinstance(generation, int) or not isinstance(ordinal, int):
                raise ProspectiveV2IntegrityError(
                    "retired state lacks a replayable retirement safe point"
                )
            grouped.setdefault((generation, ordinal), []).append(cell_id)
        return tuple(
            (generation, ordinal, tuple(sorted(cell_ids)))
            for (generation, ordinal), cell_ids in sorted(grouped.items())
        )

    @staticmethod
    def _boundary_retirement_projection(
        boundaries: Sequence[GenerationBoundary],
    ) -> tuple[tuple[int, int, tuple[str, ...]], ...]:
        """Project recorded boundary retirement batches for audit comparison."""

        grouped: dict[tuple[int, int], list[str]] = {}
        seen_ids: set[str] = set()
        for boundary in boundaries:
            cell_ids = getattr(boundary, "retired_cell_ids", ())
            if not isinstance(cell_ids, tuple):
                raise ProspectiveV2IntegrityError(
                    "generation boundary retirement IDs are not canonical"
                )
            if tuple(sorted(set(cell_ids))) != cell_ids:
                raise ProspectiveV2IntegrityError(
                    "generation boundary retirement IDs are not canonical"
                )
            if not cell_ids:
                continue
            if boundary.phase not in {
                GenerationPhase.STRUCTURAL_OPEN,
                GenerationPhase.PROSPECTIVE_OPEN,
            }:
                raise ProspectiveV2IntegrityError(
                    "retirement IDs recorded outside a structural safe point"
                )
            if (
                isinstance(boundary.generation, bool)
                or not isinstance(boundary.generation, int)
                or isinstance(boundary.event_frontier, bool)
                or not isinstance(boundary.event_frontier, int)
            ):
                raise ProspectiveV2IntegrityError(
                    "generation boundary retirement safe point is malformed"
                )
            if seen_ids.intersection(cell_ids):
                raise ProspectiveV2IntegrityError(
                    "retirement ID is recorded at multiple safe points"
                )
            seen_ids.update(cell_ids)
            grouped.setdefault(
                (boundary.generation, boundary.event_frontier), []
            ).extend(cell_ids)
        return tuple(
            (generation, ordinal, tuple(sorted(cell_ids)))
            for (generation, ordinal), cell_ids
            in sorted(grouped.items())
        )

    def _verify_generation_boundary_retirements(self) -> None:
        """Require every adaptive retirement to be audited exactly once."""

        expected = self._retirement_state_projection(self.states)
        actual = self._boundary_retirement_projection(
            self.generation_boundaries
        )
        if expected != actual:
            raise ProspectiveV2IntegrityError(
                "generation boundary retirement audit differs from tombstones"
            )
        for generation, ordinal, cell_ids in actual:
            for cell_id in cell_ids:
                state = self.states.get(cell_id)
                if state is None or not getattr(state, "retired", False):
                    raise ProspectiveV2IntegrityError(
                        "generation boundary retires a non-retired state"
                    )
                if (
                    state.retirement_generation != generation
                    or state.retirement_ordinal != ordinal
                ):
                    raise ProspectiveV2IntegrityError(
                        "generation boundary retirement safe point mismatch"
                    )

    def _validate_request_append_capacity(
        self, requests: Sequence[DeferredSpecializationRequest]
    ) -> None:
        """Validate active request capacity without charging old history."""

        if not hasattr(self, "_pending_request_index"):
            # A few structural unit fixtures intentionally use object.__new__
            # with only the historical queue fields.  They are outside the
            # event path, so retain their simple derived fallback.
            pending = len(self._pending_request_ids())
        else:
            self._ensure_hot_path_indexes()
            pending = len(self._pending_request_index)
        incoming_ids = {
            request.request_id for request in requests
        }
        # The caller subsequently rejects identity collisions.  Count only
        # genuinely new queue entries here so replaying an exact request does
        # not spuriously consume capacity.
        deferred_requests = getattr(self, "deferred_requests", {})
        pending += sum(
            request_id not in deferred_requests
            for request_id in incoming_ids
        )
        if pending > REQUEST_QUEUE_CAPACITY:
            raise ProspectiveV2IntegrityError(
                "request queue capacity exceeded"
            )

    def _continuous_deferred_contract(
        self, request: DeferredSpecializationRequest, identity: str, *, frontier: int,
    ) -> tuple[str, tuple[tuple[str, str], ...], int, int] | None:
        """Bind a genuinely new residual without reusing discovery as proof."""

        if not any(birth.birth_frontier_ordinal <= frontier for birth in self.boundary_hypothesis_births.values()):
            return None
        candidate = next(item for item in request.candidate_terminals if item.identity == identity)
        members = tuple(sorted(_recursively_implied_signal_ids(request.parent_cell_id, self.states) | {identity}))
        source = self.source_policy_identity_for_receipt(request.request_emission_receipt_id)
        references = [self.accepted_real_references[key] for key in candidate.supporting_receipt_ids]
        references.sort(key=lambda item: (item.ordinal, item.receipt_id))
        expected_outcome = request.fixed_polarity is AvailabilityState.AVAILABLE
        first = next((row for row in references if set(members).issubset(row.ordered_signal_identities)
                      and self.source_policy_identity_for_receipt(row.receipt_id) == source), None)
        if first is None:
            return source, (), 0, 0
        first_roles = dict(first.typed_signal_roles)
        roles = tuple((member, first_roles.get(member, "")) for member in members)
        parent = self.states[request.parent_cell_id].hypothesis
        if (any(not role for _, role in roles)
            or parent.semantic_source_identity not in {None, source}
            or not set(parent.semantic_member_roles).issubset(roles)):
            return source, (), 0, 0

        def matches(row: AcceptedRealReference) -> bool:
            return bool(set(members).issubset(row.ordered_signal_identities)
                        and set(roles).issubset(row.typed_signal_roles)
                        and self.source_policy_identity_for_receipt(row.receipt_id) == source)

        # Bounded explicit proposal witnesses establish the unchanged minimum
        # support threshold.  All known matching failures (including arrivals
        # after the original request) constrain allocation, never certification.
        support = sum(row.observed_outcome is expected_outcome and matches(row) for row in references)
        contradictions = sum(row.observed_outcome is not expected_outcome and matches(row)
                             for row in self.accepted_real_references.values() if row.ordinal <= frontier)
        return source, roles, support, contradictions

    def _continuous_deferred_eligible_ids(
        self, request: DeferredSpecializationRequest, *, frontier: int,
    ) -> tuple[str, ...]:
        eligible = request.eligible_base_ids
        if not eligible or not any(birth.birth_frontier_ordinal <= frontier for birth in self.boundary_hypothesis_births.values()):
            return eligible
        graph = Graph()
        root_id = ROLE_ROOTS["specialization_eligibility"]
        graph.add_node(Node(root_id, NodeType.SCRIPT, meta={"confirm_policy": "or"}))
        for identity in eligible:
            contract = self._continuous_deferred_contract(request, identity, frontier=frontier)
            assert contract is not None
            _source, roles, support, contradictions = contract
            graph.add_node(Node(identity, NodeType.TERMINAL, predicate=_v2_specialization_eligibility_terminal, meta={
                "specialization_mode": request.specialization_mode.value,
                "role_permitted": bool(roles), "recursively_implied_by_parent": False,
                "supporting_occurrence_count": support,
                "present_in_triggering_contradiction": False,
                "known_contradiction_count": contradictions,
            }))
            graph.add_hierarchy_pair(root_id, identity)
        _run_authority_component(graph, (root_id,), env={})
        return tuple(identity for identity in eligible if graph.nodes[identity].state is NodeState.CONFIRMED)

    def _deferred_request_plan(
        self,
        request_id: str,
        *,
        attempt_ordinal: int,
        target_generation: int,
        reserved_members: set[tuple[str, ...]],
    ) -> _DeferredRequestPlan:
        """Preview one request with exactly one organism-owned genome call."""

        request = self.deferred_requests.get(request_id)
        if request is None:
            raise ProspectiveV2IntegrityError(
                "cannot plan an unknown structural request"
            )
        genome = CompetenceContextGrowthGenome(
            self.specialization_genome_seed
        )
        eligible_ids = self._continuous_deferred_eligible_ids(
            request, frontier=self.next_expected_ordinal - 1
        )
        proposal = genome.propose_specialization(_GraphSpecializationRequest(
            context_member=f"context:{request.parent_cell_id}",
            eligible_base_ids=eligible_ids,
            # Candidate rows use the frozen genome/hash order with a stable
            # zero tie ordinal; reuse it at consumption for exact parity.
            request_ordinal=0,
            eligible_base_support_counts=tuple(
                (
                    item.identity,
                    item.supporting_occurrence_count,
                )
                for item in request.candidate_terminals
                if item.confirmed and item.identity in eligible_ids
            ),
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
                or members[1] not in eligible_ids
            ):
                raise ProspectiveV2IntegrityError(
                    "genome emitted an ineligible specialization child"
                )
            if members in reserved_members:
                disposition = "REJECTED_DUPLICATE_PATTERN"
            else:
                child_id = (
                    f"v2_deferred_specialization_"
                    f"g{target_generation:02d}_{attempt_ordinal:04d}"
                )
                if (
                    child_id in self.states
                    or child_id in getattr(self, "retired_tombstones", {})
                    or child_id in self._successor_capacity_occupants()
                ):
                    raise ProspectiveV2IntegrityError(
                        "deferred child identity collision"
                    )
                reserved_members.add(members)
        return _DeferredRequestPlan(StructuralRequestConsumption(
            request_id=request_id,
            attempt_ordinal=attempt_ordinal,
            genome_seed=self.specialization_genome_seed,
            genome_call_count=1,
            selected_members=members,
            disposition=disposition,
            child_cell_id=child_id,
        ))

    def _plan_deferred_request_births(
        self,
        request_ids: Sequence[str],
        *,
        target_generation: int,
        incoming_promotion_members: Sequence[tuple[str, ...]] = (),
    ) -> tuple[_DeferredRequestPlan, ...]:
        """Preview all pending births without mutating authority state.

        Legacy planning reads only frozen requests and structural identities.
        After continuous-protocol activation, native eligibility also closes
        each residual against its exact typed/source predicate and all REAL
        contradictions visible at this safe point.  Every request receives
        one genome call, including empty or
        duplicate proposals; capacity is handled by the caller after all
        concrete proposals are known.
        """

        request_tuple = tuple(request_ids)
        if len(set(request_tuple)) != len(request_tuple):
            raise ProspectiveV2IntegrityError(
                "deferred request planner received duplicate IDs"
            )
        pending = set(self._pending_request_ids())
        if not set(request_tuple).issubset(pending):
            raise ProspectiveV2IntegrityError(
                "deferred request planner received a non-pending request"
            )
        reserved_members = set(getattr(self, "_reserved_member_pairs", ()))
        reserved_members.update(tuple(item) for item in incoming_promotion_members)

        # In scheduled mode the sealed queue defines attempt ordinals.  In
        # event-driven mode the queue is sealed immediately after this preview,
        # so pending order is the equivalent canonical source.
        sealed_index = {
            request_id: index
            for index, request_id in enumerate(self.sealed_request_ids)
        }
        plans: list[_DeferredRequestPlan] = []
        for pending_index, request_id in enumerate(request_tuple):
            attempt = sealed_index.get(request_id, pending_index)
            plans.append(self._deferred_request_plan(
                request_id,
                attempt_ordinal=attempt,
                target_generation=target_generation,
                reserved_members=reserved_members,
            ))
        return tuple(plans)

    def _successor_capacity_occupants(self) -> frozenset[str]:
        """Return each committed or reserved successor slot exactly once.

        Deferred child births occupy a live slot as soon as the genome accepts
        a proposal, even before structural materialization. Once such a birth
        is materialized, its child is also present in ``states``; the set
        union deliberately counts that reservation and materialization once
        rather than charging the shared cap twice. Ordinary boundary
        promotions enter through ``states`` and share this accounting.
        Retired states remain in the replay ledger but release their slot.
        """

        if getattr(self, "_hot_path_indexes_ready", False):
            return frozenset(self._successor_capacity_occupant_ids)

        materialized = {
            cell_id for cell_id, state in self.states.items()
            if (
                state.hypothesis.source_generation > 0
                and not getattr(state, "retired", False)
            )
        }
        reserved = {
            birth.child_cell_id
            for birth in self.deferred_child_births.values()
            if birth.child_cell_id not in getattr(
                self, "retired_tombstones", {}
            )
        }
        return frozenset(materialized | reserved)

    @staticmethod
    def _retirement_tombstone_payload(
        *,
        cell_id: str,
        state_before: Mapping[str, Any],
        state_after: Mapping[str, Any],
        retirement_generation: int,
        retirement_ordinal: int,
        retirement_reason: str,
    ) -> dict[str, Any]:
        """Return the content-blind, replay-stable retirement record.

        ``state_after`` deliberately carries a null tombstone digest in the
        hashed payload.  The digest is then written both to the live state and
        to the outer tombstone without creating a self-referential hash.
        """

        normalized_after = copy.deepcopy(dict(state_after))
        normalized_after["retirement_tombstone_digest"] = None
        return {
            "schema_version": RETIREMENT_TOMBSTONE_SCHEMA,
            "cell_id": cell_id,
            "retirement_generation": int(retirement_generation),
            "retirement_ordinal": int(retirement_ordinal),
            "retirement_reason": retirement_reason,
            "state_before": copy.deepcopy(dict(state_before)),
            "state_after": normalized_after,
        }

    @classmethod
    def _validate_retirement_tombstone(
        cls,
        cell_id: str,
        state: ProspectiveAuthorityState,
        tombstone: Mapping[str, Any],
    ) -> None:
        """Check one adaptive retirement record against its retained state."""

        required = {
            "schema_version", "cell_id", "retirement_generation",
            "retirement_ordinal", "retirement_reason", "state_before",
            "state_after", "retirement_tombstone_digest",
        }
        if set(tombstone) != required:
            raise ProspectiveV2IntegrityError(
                f"retirement tombstone fields are not canonical: {cell_id}"
            )
        if (
            tombstone["schema_version"] != RETIREMENT_TOMBSTONE_SCHEMA
            or tombstone["cell_id"] != cell_id
            or not isinstance(tombstone["retirement_reason"], str)
            or not tombstone["retirement_reason"]
            or not isinstance(tombstone["state_before"], Mapping)
            or not isinstance(tombstone["state_after"], Mapping)
        ):
            raise ProspectiveV2IntegrityError(
                f"retirement tombstone identity is invalid: {cell_id}"
            )
        if (
            tombstone["retirement_generation"]
            != getattr(state, "retirement_generation", None)
            or tombstone["retirement_ordinal"]
            != getattr(state, "retirement_ordinal", None)
            or tombstone["retirement_reason"]
            != getattr(state, "retirement_reason", None)
        ):
            raise ProspectiveV2IntegrityError(
                f"retirement tombstone lifecycle differs from state: {cell_id}"
            )
        if tombstone["state_before"].get("retired", False):
            raise ProspectiveV2IntegrityError(
                f"retirement tombstone began from a retired state: {cell_id}"
            )
        expected_after = state.manifest()
        expected_after["retirement_tombstone_digest"] = None
        if dict(tombstone["state_after"]) != expected_after:
            raise ProspectiveV2IntegrityError(
                f"retirement tombstone state mismatch: {cell_id}"
            )
        payload = cls._retirement_tombstone_payload(
            cell_id=cell_id,
            state_before=tombstone["state_before"],
            state_after=tombstone["state_after"],
            retirement_generation=int(tombstone["retirement_generation"]),
            retirement_ordinal=int(tombstone["retirement_ordinal"]),
            retirement_reason=str(tombstone["retirement_reason"]),
        )
        expected_digest = _sha(payload)
        if tombstone["retirement_tombstone_digest"] != expected_digest:
            raise ProspectiveV2IntegrityError(
                f"retirement tombstone digest mismatch: {cell_id}"
            )
        if getattr(state, "retirement_tombstone_digest", None) != expected_digest:
            raise ProspectiveV2IntegrityError(
                f"state retirement digest mismatch: {cell_id}"
            )

    def _replaceable_adaptive_leaf_ids(self) -> tuple[str, ...]:
        """Return adaptive leaves eligible for deterministic slot recovery."""

        live = self._hot_live_states()
        protected_parents = self._retirement_protected_parent_ids()
        replaceable: list[str] = []
        for cell_id, state in sorted(live.items()):
            hypothesis = state.hypothesis
            if (
                hypothesis.source_generation <= 0
                or hypothesis.initialization_origin
                is not InitializationOrigin.PROSPECTIVE
                or cell_id in protected_parents
            ):
                continue
            replaceable.append(cell_id)
        return tuple(replaceable)

    def _retirement_protected_parent_ids(self) -> frozenset[str]:
        """Return parents whose live/request dependency is still active.

        A consumed or rejected request does not pin a slot forever.  A parent
        remains protected while its request is pending, while a reserved
        child is awaiting materialization, or while any live descendant still
        depends on its lineage.  Once those dependencies are gone, the
        append-only request record remains replayable even if the parent is
        retired and its child is later retired too.
        """

        protected: set[str] = {
            self.deferred_requests[request_id].parent_cell_id
            for request_id in self._pending_request_ids()
            if request_id in self.deferred_requests
        }
        protected.update(
            self.deferred_requests[request_id].parent_cell_id
            for request_id in self._pending_child_birth_request_ids
            if request_id in self.deferred_requests
        )
        live = self._hot_live_states()
        for state in live.values():
            parent_id = getattr(state.hypothesis, "lineage_parent_id", None)
            visited: set[str] = set()
            while parent_id is not None:
                if parent_id in visited:
                    raise ProspectiveV2IntegrityError(
                        "cyclic live specialization lineage"
                    )
                visited.add(parent_id)
                protected.add(parent_id)
                parent = self.states.get(parent_id)
                if parent is None:
                    break
                parent_id = getattr(
                    parent.hypothesis, "lineage_parent_id", None
                )
        return frozenset(protected)

    def _validate_retirement_batch(
        self, cell_ids: Sequence[str]
    ) -> tuple[str, ...]:
        """Validate and canonicalize one authority-local retirement batch.

        The check is deliberately side-effect free.  Settlement performs it
        before entering its structural transaction so automatic reclamation
        can be selected on the same deepcopy as explicit reclamation and
        every later admission can still roll back as one unit.
        """

        requested = tuple(cell_ids)
        if any(not isinstance(item, str) or not item for item in requested):
            raise ProspectiveV2IntegrityError(
                "adaptive retirement IDs must be non-empty strings"
            )
        canonical = tuple(sorted(set(requested)))
        if canonical != requested:
            raise ProspectiveV2IntegrityError(
                "adaptive retirement IDs are not canonical"
            )
        replaceable = set(self._replaceable_adaptive_leaf_ids())
        for cell_id in canonical:
            state = self.states.get(cell_id)
            if state is None:
                raise ProspectiveV2IntegrityError(
                    f"adaptive retirement names unknown state: {cell_id}"
                )
            if cell_id in self.historical_tombstones:
                raise ProspectiveV2IntegrityError(
                    f"immutable historical candidate cannot retire: {cell_id}"
                )
            if cell_id in self.retired_tombstones or getattr(
                state, "retired", False
            ):
                raise ProspectiveV2IntegrityError(
                    f"adaptive candidate is already retired: {cell_id}"
                )
            if cell_id not in replaceable:
                raise ProspectiveV2IntegrityError(
                    f"adaptive candidate is not a replaceable leaf: {cell_id}"
                )
        return canonical

    def deterministic_retirement_candidates(
        self,
        required_slots: int = 1,
        *,
        exclude_cell_ids: Sequence[str] = (),
    ) -> tuple[str, ...]:
        """Choose the weakest replaceable leaves in a stable total order.

        This is deliberately a read-only selector.  The caller decides when a
        safe point is reached and passes the returned IDs to
        ``settle_pending_structural_requests`` (or to
        ``retire_adaptive_leaves``).  No outcome, board state, or external
        oracle is consulted: only the candidate's already-committed local
        evidence and immutable birth order participate in the tie break.
        """

        if (
            isinstance(required_slots, bool)
            or not isinstance(required_slots, int)
            or required_slots < 0
        ):
            raise ValueError("required_slots must be a non-negative integer")
        live = self._hot_live_states()
        excluded = tuple(exclude_cell_ids)
        if any(not isinstance(item, str) or not item for item in excluded):
            raise ValueError("excluded retirement IDs must be non-empty strings")
        if tuple(sorted(set(excluded))) != excluded:
            raise ValueError("excluded retirement IDs are not canonical")
        excluded_set = set(excluded)
        candidates = tuple(
            cell_id for cell_id in self._replaceable_adaptive_leaf_ids()
            if cell_id not in excluded_set
        )
        def retirement_tier(cell_id: str) -> int:
            state = live[cell_id]
            if not state.prospectively_certified:
                # This includes a locally revoked or never-certified leaf.
                return 0
            if state.hypothesis.polarity is AvailabilityState.REFUTED:
                return 1
            # Certified AVAILABLE shells are useful anchors and are therefore
            # the final replaceable tier, never preferred while another tier
            # has capacity to give.
            return 2

        ordered = sorted(
            candidates,
            key=lambda cell_id: (
                retirement_tier(cell_id),
                float(live[cell_id].success_lower_bound),
                -int(live[cell_id].contradictions),
                int(live[cell_id].support),
                int(live[cell_id].hypothesis.birth_frontier),
                cell_id,
            ),
        )
        return tuple(ordered[:required_slots])

    def live_successor_ids(self) -> tuple[str, ...]:
        """Expose the bounded live adaptive population for a safe-point caller."""

        return tuple(sorted(
            cell_id for cell_id in self._successor_capacity_occupants()
            if cell_id in self._live_authority_state_cache
        ))

    def _retire_adaptive_leaves_in_place(
        self,
        cell_ids: Sequence[str],
        *,
        reason: str = DEFAULT_RETIREMENT_REASON,
        require_structural_open: bool = False,
        rebuild_topology: bool = True,
    ) -> tuple[str, ...]:
        """Retire validated adaptive leaves, preserving exact audit records.

        This method intentionally mutates only an already-copied authority.
        Public callers and structural settlement both use an outer deepcopy,
        so any invalid batch leaves the original authority untouched.
        """

        if not isinstance(reason, str) or not reason.strip():
            raise ProspectiveV2IntegrityError(
                "adaptive retirement reason must be a non-empty string"
            )
        if require_structural_open and self.generation_phase is not GenerationPhase.STRUCTURAL_OPEN:
            raise ProspectiveV2IntegrityError(
                "adaptive retirement requires STRUCTURAL_OPEN"
            )
        canonical = self._validate_retirement_batch(cell_ids)

        retired: list[str] = []
        for cell_id in canonical:
            state = self.states[cell_id]
            state_before = state.manifest()
            self._mutation_set_attr(state, "retired", True)
            self._mutation_set_attr(state, "prospectively_certified", False)
            self._mutation_set_attr(
                state, "retirement_generation", self.current_generation
            )
            self._mutation_set_attr(
                state, "retirement_ordinal", self.next_expected_ordinal
            )
            self._mutation_set_attr(
                state, "retirement_reason", reason.strip()
            )
            state_after = state.manifest()
            payload = self._retirement_tombstone_payload(
                cell_id=cell_id,
                state_before=state_before,
                state_after=state_after,
                retirement_generation=self.current_generation,
                retirement_ordinal=self.next_expected_ordinal,
                retirement_reason=state.retirement_reason,
            )
            digest = _sha(payload)
            self._mutation_set_attr(
                state, "retirement_tombstone_digest", digest
            )
            self._mutation_add_mapping(
                self.retired_tombstones,
                cell_id,
                {**payload, "retirement_tombstone_digest": digest},
            )
            retired.append(cell_id)
        if retired:
            retirement_payload = {
                "tombstones": [
                    copy.deepcopy(self.retired_tombstones[cell_id])
                    for cell_id in retired
                ],
            }
            self._record_boundary_structure(
                "adaptive_retirement", retirement_payload
            )
            for cell_id in retired:
                if isinstance(
                    self._live_authority_state_cache,
                    _LiveAuthorityStateView,
                ):
                    self._mutation_delete_mapping(
                        self._live_authority_state_cache, cell_id
                    )
                self._mutation_discard_set(
                    self._successor_capacity_occupant_ids, cell_id
                )
                candidate_id = self._boundary_promotion_by_child.get(cell_id)
                if candidate_id is not None:
                    self._mutation_discard_set(
                        self._active_boundary_promotion_ids,
                        candidate_id,
                    )
            if retired:
                self._refresh_active_boundary_promotion_digest(
                    self._active_boundary_promotion_ids
                )
            if rebuild_topology:
                self._mutation_set_attr(
                    self,
                    "authority_topology",
                    _executed_authority_topology_manifest(
                        self._live_authority_state_cache
                    ),
                )
            self._record_boundary_candidate(
                "adaptive_retirement", retirement_payload
            )
            self._advance_boundary_commitment(
                "adaptive_retirement",
                {
                    "retirement": retirement_payload,
                    "structure_digest": self._boundary_structure_digest,
                },
            )
        return tuple(retired)

    def retire_adaptive_leaves(
        self,
        cell_ids: Sequence[str],
        *,
        reason: str = DEFAULT_RETIREMENT_REASON,
    ) -> tuple[str, ...]:
        """Atomically retire adaptive leaves at a quiescent safe point."""

        if self.pending_event is not None or self.evaluation_sealed:
            raise ProspectiveV2IntegrityError(
                "adaptive retirement requires a quiescent authority"
            )
        if self.generation_phase is not GenerationPhase.PROSPECTIVE_OPEN:
            raise ProspectiveV2IntegrityError(
                "adaptive retirement requires PROSPECTIVE_OPEN"
            )
        candidate = copy.deepcopy(self)
        prior = candidate._boundary_prior_continuation_digest()
        result = candidate._retire_adaptive_leaves_in_place(
            cell_ids, reason=reason
        )
        if result:
            # Direct quiescent retirement is still a structural safe point.
            # Record it as its own boundary so every tombstone has one
            # auditable (generation, event-frontier) owner, just like batch
            # retirement during scheduled or event-driven settlement.
            boundary = candidate._generation_boundary(
                phase=candidate.generation_phase,
                prior_continuation_digest=prior,
                queue_ids=candidate.sealed_request_ids,
                retired_cell_ids=result,
            )
            candidate._append_generation_boundary(boundary)
        candidate._verify_invariants()
        self.__dict__.clear()
        self.__dict__.update(candidate.__dict__)
        return result

    def _accepted_real_ledger_digest(self) -> str:
        if self.boundary_digest_schema == (
            BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
        ):
            if not self._boundary_accepted_real_digest:
                self._boundary_accepted_real_digest = (
                    self._boundary_seed_accepted_real_digest()
                )
            return self._boundary_accepted_real_digest
        return _sha([
            item.manifest() for item in sorted(
                self.accepted_real_references.values(),
                key=lambda row: (row.ordinal, row.receipt_id),
            )
        ])

    def _request_queue_digest(self, request_ids: Sequence[str]) -> str:
        if self.boundary_digest_schema == (
            BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
        ):
            return self._boundary_queue_digest(request_ids)
        return _sha([
            self.deferred_requests[item].manifest() for item in request_ids
        ])

    def _parent_decision_history_digest(self) -> str:
        if self.boundary_digest_schema == (
            BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
        ):
            if not self._boundary_decision_digest:
                self._boundary_decision_digest = (
                    self._boundary_seed_decision_digest()
                )
            return self._boundary_decision_digest
        return _sha({
            cell_id: self._boundary_decision_row(cell_id, state)
            for cell_id, state in sorted(self.states.items())
        })

    def _generation_boundary(
        self,
        *,
        phase: GenerationPhase,
        prior_continuation_digest: str,
        queue_ids: Sequence[str],
        retired_cell_ids: Sequence[str] = (),
        prior_digest_schema: str | None = None,
    ) -> GenerationBoundary:
        return GenerationBoundary(
            generation=self.current_generation,
            phase=phase,
            event_frontier=self.next_expected_ordinal,
            prior_continuation_digest=prior_continuation_digest,
            accepted_real_ledger_digest=self._accepted_real_ledger_digest(),
            request_queue_digest=self._request_queue_digest(queue_ids),
            structural_epoch_schedule_digest=(
                self._boundary_schedule_digest
                if self.boundary_digest_schema
                == BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
                and self._boundary_schedule_digest
                else _sha(list(self.structural_epoch_schedule))
            ),
            candidate_manifest_digest=self._candidate_manifest_digest(),
            parent_decision_history_digest=(
                self._parent_decision_history_digest()
            ),
            specialization_genome_seed=self.specialization_genome_seed,
            prior_digest_schema=(
                self.boundary_digest_schema
                if prior_digest_schema is None else prior_digest_schema
            ),
            retired_cell_ids=tuple(retired_cell_ids),
        )

    @staticmethod
    def _adaptive_boundary_child_id(
        request: BoundaryPromotionRequest,
    ) -> str:
        """Derive an order-independent authority child identity."""

        return f"v2_adaptive_boundary_{request.request_digest}"

    @staticmethod
    def _same_boundary_promotion_request(
        stored: BoundaryPromotionRequest,
        incoming: BoundaryPromotionRequest,
    ) -> bool:
        """Permit replay of the exact request while rejecting collisions."""

        if (
            stored.candidate_id != incoming.candidate_id
            or stored.members != incoming.members
            or stored.fixed_polarity is not incoming.fixed_polarity
            or stored.triggering_receipt_id
            != incoming.triggering_receipt_id
            or stored.supporting_receipt_ids
            != incoming.supporting_receipt_ids
            or stored.inspected_receipt_ids
            != incoming.inspected_receipt_ids
            or stored.source_generation != incoming.source_generation
            or stored.promotion_gate_state
            != incoming.promotion_gate_state
            or stored.promotion_gate_digest
            != incoming.promotion_gate_digest
        ):
            return False
        return True

    def source_policy_identity_for_receipt(self, receipt_id: str) -> str:
        """Identify the frozen actuator, never the changing graph generation."""

        receipt = self.consumed_receipts.get(receipt_id)
        if receipt is not None:
            trace = receipt.trace
        else:
            native = self.base.receipts.get(receipt_id)
            if native is None:
                raise ProspectiveV2IntegrityError("source identity requires accepted REAL receipt")
            trace = native.decision_trace
        return _trace_source_policy_identity(trace)

    def _continuous_reference_matches(
        self, birth: BoundaryHypothesisBirth, reference: AcceptedRealReference,
    ) -> bool:
        roles = dict(reference.typed_signal_roles)
        return bool(
            set(birth.members).issubset(reference.ordered_signal_identities)
            and all(roles.get(key) == role for key, role in birth.member_signal_roles)
            and self.source_policy_identity_for_receipt(reference.receipt_id)
            == birth.source_identity
        )

    def _append_boundary_hypothesis_birth(self, birth: BoundaryHypothesisBirth) -> None:
        """One bounded immutable append, shared by admission and exact replay."""

        self._mutation_add_mapping(self.boundary_hypothesis_births, birth.candidate_id, birth)
        previous = self._boundary_hypothesis_birth_digest or _empty_hot_append_digest("hypothesis_birth")
        self._mutation_set_attr(self, "_boundary_hypothesis_birth_digest", _next_hot_append_digest(
            previous, "hypothesis_birth", birth.manifest(), len(self.boundary_hypothesis_births)
        ))
        self._advance_boundary_commitment("boundary_hypothesis_birth", birth.manifest())
        self._mutation_set_attr(self, "_hot_path_revision", self._hot_path_revision + 1)

    def register_boundary_hypothesis_birth(
        self, *, candidate_id: str, members: Sequence[str],
        member_signal_roles: Sequence[tuple[str, str]], source_identity: str,
        semantic_identity: str, birth_frontier_ordinal: int,
        triggering_receipt_id: str,
    ) -> str:
        """Explicitly opt in one fixed predicate at its actual semantic birth.

        This may follow an observed discovery/contrast event, but must precede
        the next REAL transaction.  It grants no graph authority or credit.
        """

        if (self.pending_event is not None or self.evaluation_sealed
            or self.generation_phase is not GenerationPhase.PROSPECTIVE_OPEN
            or self.structural_mode is not StructuralMode.EVENT_DRIVEN):
            raise ProspectiveV2IntegrityError("hypothesis birth requires an unsealed quiescent event-local authority")
        if candidate_id in self.boundary_hypothesis_births:
            existing = self.boundary_hypothesis_births[candidate_id]
            if (existing.members == tuple(members)
                and existing.member_signal_roles == tuple(member_signal_roles)
                and existing.source_identity == source_identity
                and existing.semantic_identity == semantic_identity
                and existing.birth_frontier_ordinal == birth_frontier_ordinal
                and existing.triggering_receipt_id == triggering_receipt_id):
                return existing.birth_digest
            raise ProspectiveV2IntegrityError("hypothesis birth identity cannot be reused or changed")
        if (isinstance(birth_frontier_ordinal, bool)
            or birth_frontier_ordinal != self.next_expected_ordinal - 1):
            raise ProspectiveV2IntegrityError("hypothesis birth cannot be backdated or future-dated")
        latest = self.consumed_receipts.get(
            self._accepted_real_reference_order[-1] if self._accepted_real_reference_order else ""
        )
        if latest is None:
            raise ProspectiveV2IntegrityError("hypothesis birth requires a just-consumed prospective REAL")
        if self.accepted_real_references[latest.receipt_id].source_generation != self.current_generation:
            raise ProspectiveV2IntegrityError("hypothesis birth must precede its event's structural settlement")
        trigger = self.accepted_real_references.get(triggering_receipt_id)
        if trigger is None or not trigger.observed_outcome or trigger.ordinal > birth_frontier_ordinal:
            raise ProspectiveV2IntegrityError("hypothesis birth requires an already accepted positive discovery trigger")
        birth = BoundaryHypothesisBirth(
            candidate_id=str(candidate_id), members=tuple(members),
            member_signal_roles=tuple(member_signal_roles), source_identity=source_identity,
            semantic_identity=semantic_identity, birth_frontier_ordinal=birth_frontier_ordinal,
            triggering_receipt_id=triggering_receipt_id, source_generation=self.current_generation,
            sequence=len(self.boundary_hypothesis_births),
            discovery_exclusion_commitment=self._accepted_real_prefix_commitment(self.accepted_real_references),
        )
        if (not self._continuous_reference_matches(birth, trigger)
            or any(not _specialization_identity_role_permitted(trigger, member) for member in birth.members)
            or any(member.startswith("context:") or member == "internal:policy_response" for member in birth.members)
            or self.source_policy_identity_for_receipt(latest.receipt_id) != source_identity):
            raise ProspectiveV2IntegrityError("hypothesis birth predicate/source differs from discovery trace")
        journal = _StructuralMutationJournal()
        prior = getattr(self, "_structural_mutation_journal", None)
        self._structural_mutation_journal = journal
        try:
            self._append_boundary_hypothesis_birth(birth)
        except Exception:
            journal.rollback()
            raise
        else:
            journal.commit()
        finally:
            if prior is None:
                self.__dict__.pop("_structural_mutation_journal", None)
            else:
                self._structural_mutation_journal = prior
        return birth.birth_digest

    def _continuous_birth_for_request(self, request: BoundaryPromotionRequest) -> BoundaryHypothesisBirth:
        birth = self.boundary_hypothesis_births.get(request.candidate_id)
        if (birth is None or birth.birth_digest != request.hypothesis_birth_digest
            or birth.members != request.members
            or birth.triggering_receipt_id != request.triggering_receipt_id
            or request.fixed_polarity is not AvailabilityState.AVAILABLE):
            raise ProspectiveV2IntegrityError("promotion does not bind its precommitted hypothesis")
        return birth

    def _continuous_evidence_ids(
        self, birth: BoundaryHypothesisBirth, frontier: int,
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        """Read-only safe-point reclosure; never a lifetime per-event scan."""

        inspected = tuple(sorted(reference.receipt_id for reference in self.accepted_real_references.values()
                                 if birth.birth_frontier_ordinal < reference.ordinal <= frontier))
        # A remembered failure is applicability evidence, not certification
        # evidence.  An identical reincarnation cannot erase that constraint.
        relevant = tuple(reference for reference in self.accepted_real_references.values()
                         if reference.ordinal <= frontier and self._continuous_reference_matches(birth, reference))
        support = tuple(sorted(reference.receipt_id for reference in relevant
                               if reference.ordinal > birth.birth_frontier_ordinal and reference.observed_outcome))
        negatives = tuple(sorted(reference.receipt_id for reference in relevant if not reference.observed_outcome))
        return inspected, support, negatives

    def _validate_continuous_boundary_promotion(
        self, request: BoundaryPromotionRequest, *, evidence_frontier: int | None,
        require_current_generation: bool,
    ) -> BoundaryPromotionRequest:
        birth = self._continuous_birth_for_request(request)
        if request.provenance_schema_version != PROVENANCE_COMMITMENT_V4:
            raise ProspectiveV2IntegrityError("continuous promotion requires compact V4 provenance")
        frontier = self.next_expected_ordinal - 1 if evidence_frontier is None else int(evidence_frontier)
        if (require_current_generation and request.source_generation != self.current_generation
            or frontier < birth.birth_frontier_ordinal
            or frontier >= self.next_expected_ordinal):
            raise ProspectiveV2IntegrityError("continuous promotion frontier/generation differs")
        inspected, support, negatives = self._continuous_evidence_ids(birth, frontier)
        if negatives:
            raise ProspectiveV2IntegrityError("continuous hypothesis matches a known negative")
        if len(support) < MIN_SUPPORT:
            raise ProspectiveV2IntegrityError("continuous promotion requires four strictly postbirth positives")
        if request.provenance_schema_version == PROVENANCE_COMMITMENT_V4:
            if (request.inspected_receipt_commitment != _compact_set_commitment(inspected, exclusive_frontier=frontier + 1)
                or request.supporting_receipt_commitment != _compact_set_commitment(support, exclusive_frontier=frontier + 1)):
                raise ProspectiveV2IntegrityError("continuous promotion evidence commitment is incomplete")
        elif request.inspected_receipt_ids != inspected or request.supporting_receipt_ids != support:
            raise ProspectiveV2IntegrityError("continuous promotion evidence set is incomplete")
        return request

    def _transfer_continuous_boundary_evidence(
        self, state: ProspectiveAuthorityState, request: BoundaryPromotionRequest,
    ) -> None:
        """Replay precommitted evidence into newly allocated graph lifecycle.

        Historical REAL emissions remain untouched.  The authority was not
        physically present then, so its maturity is exposed only after this
        atomic allocation, never to the action that supplied the last read.
        """

        self._boundary_replay_reset_state(state)
        frontier = state.hypothesis.materialization_frontier
        if frontier is None:
            raise ProspectiveV2IntegrityError("continuous transfer lacks physical frontier")
        self._validate_continuous_boundary_promotion(
            request, evidence_frontier=frontier, require_current_generation=False
        )
        birth = self._continuous_birth_for_request(request)
        _inspected, support_ids, _negatives = self._continuous_evidence_ids(birth, frontier)
        for receipt_id in sorted(support_ids, key=lambda key: self.accepted_real_references[key].ordinal):
            receipt = self.consumed_receipts.get(receipt_id)
            if receipt is None or not _receipt_is_post_birth(state.hypothesis, receipt):
                raise ProspectiveV2IntegrityError("continuous transfer contains discovery or nonprospective evidence")
            graph = _run_authority_graph(
                {state.hypothesis.cell_id: state}, AuthorityMeasurementSnapshot(receipt.trace, receipt),
                accepted_real_references=self.accepted_real_references,
                current_real_reference=self.accepted_real_references[receipt_id],
                specialization_mode=SpecializationMode.DISCONNECTED,
                lifetime_requested_parent_ids=frozenset(),
                specialization_genome_seed=self.specialization_genome_seed,
                compact_provenance=True,
            )
            cell_id = state.hypothesis.cell_id
            if graph["commitment"] != (cell_id,) or graph["support"] != (cell_id,):
                raise ProspectiveV2IntegrityError("continuous evidence fails graph-native predicate support")
            state.support += 1
            state.successes += 1
            self._append_state_ledger(state, "certification_receipt_ids", receipt_id)
            self._append_state_ledger(state, "support_receipt_ids", receipt_id)
            state.success_lower_bound = wilson_lower_bound(state.successes, state.support, WILSON_Z)
            state.contradiction_lower_bound = wilson_lower_bound(0, state.support, WILSON_Z)
            if cell_id in graph["maturity"]:
                state.prospectively_certified = True
                self._append_state_ledger(state, "transition_rows", {
                    "transition": "GRAPH_PROSPECTIVE_MATURITY",
                    "receipt_id": receipt_id, "ordinal": receipt.ordinal,
                    "pending_token": receipt.pending_token,
                    "evidence_origin": BOUNDARY_HYPOTHESIS_BIRTH_SCHEMA,
                    "materialization_frontier": frontier,
                })
        if not state.prospectively_certified:
            raise ProspectiveV2IntegrityError("continuous evidence did not reach native graph maturity")

    def _validate_boundary_promotion_request(
        self,
        request: BoundaryPromotionRequest,
        *,
        evidence_frontier: int | None = None,
        require_current_generation: bool = True,
        ordered_reference_ids: Sequence[str] | None = None,
        reference_ordinals: Sequence[int] | None = None,
    ) -> BoundaryPromotionRequest:
        """Validate one ecology-produced request against accepted REAL data."""

        if request.hypothesis_birth_digest is not None:
            return self._validate_continuous_boundary_promotion(
                request, evidence_frontier=evidence_frontier,
                require_current_generation=require_current_generation,
            )
        if request.candidate_id in self.boundary_hypothesis_births:
            raise ProspectiveV2IntegrityError("continuous candidate omitted its birth link")

        if (
            require_current_generation
            and request.source_generation != self.current_generation
        ):
            raise ProspectiveV2IntegrityError(
                "boundary promotion source generation differs from current"
            )
        if request.promotion_gate_state != BOUNDARY_PROMOTION_GATE_STATE:
            raise ProspectiveV2IntegrityError(
                "boundary promotion gate did not confirm"
            )
        if request.fixed_polarity is not AvailabilityState.AVAILABLE:
            raise ProspectiveV2IntegrityError(
                "negative boundary successors are not promotable"
            )
        compact_request = request.provenance_schema_version == (
            PROVENANCE_COMMITMENT_V4
        )
        if ordered_reference_ids is None:
            ordered_reference_ids = self._accepted_real_reference_order
        if reference_ordinals is None:
            reference_ordinals = self._accepted_real_reference_ordinals
        if (
            len(ordered_reference_ids) != len(self.accepted_real_references)
            or len(reference_ordinals) != len(ordered_reference_ids)
        ):
            # Compatibility for pre-metabolism hand-built fixtures.  Normal
            # authorities initialize the order at their first full boundary.
            visible = tuple(sorted(
                self.accepted_real_references.values(),
                key=lambda item: (item.ordinal, item.receipt_id),
            ))
            ordered_reference_ids = tuple(
                item.receipt_id for item in visible
            )
            reference_ordinals = tuple(item.ordinal for item in visible)
        if not ordered_reference_ids:
            raise ProspectiveV2IntegrityError(
                "boundary promotion requires an accepted REAL ledger"
            )
        trigger_reference = self.accepted_real_references.get(
            request.triggering_receipt_id
        )
        if trigger_reference is None:
            raise ProspectiveV2IntegrityError(
                "boundary promotion trigger is not an accepted REAL receipt"
            )
        if (
            not trigger_reference.observed_outcome
            or not set(request.members).issubset(
                trigger_reference.ordered_signal_identities
            )
            or any(
                not _specialization_identity_role_permitted(
                    trigger_reference, member
                )
                for member in request.members
            )
        ):
            raise ProspectiveV2IntegrityError(
                "boundary promotion trigger is not positive matching evidence"
            )
        # A cheap local sketch may survive unrelated atomic commits while it
        # accumulates prospective support.  Its triggering evidence therefore
        # need not have been minted in the current structural generation.  The
        # request itself is nevertheless bound to the current generation and
        # every intervening REAL receipt is required below, so crossing a safe
        # point cannot hide evidence or make an old observation current again.
        current_frontier = int(reference_ordinals[-1])
        frontier = (
            current_frontier
            if evidence_frontier is None else int(evidence_frontier)
        )
        if compact_request:
            if request.inspected_receipt_commitment is None:
                raise ProspectiveV2IntegrityError(
                    "compact boundary request lacks inspected commitment"
                )
            if (
                evidence_frontier is None
                and request.inspected_receipt_commitment.exclusive_frontier
                != current_frontier + 1
            ):
                raise ProspectiveV2IntegrityError(
                    "boundary promotion did not inspect through the current "
                    "accepted-REAL frontier"
                )
            frontier = (
                current_frontier
                if evidence_frontier is None else int(evidence_frontier)
            )
        if frontier < trigger_reference.ordinal:
            raise ProspectiveV2IntegrityError(
                "boundary promotion frontier precedes its trigger"
            )
        interval_start = bisect_left(
            reference_ordinals, trigger_reference.ordinal
        )
        interval_stop = bisect_right(reference_ordinals, frontier)
        visible_interval = tuple(
            self.accepted_real_references[receipt_id]
            for receipt_id in ordered_reference_ids[
                interval_start:interval_stop
            ]
        )
        expected_inspected = tuple(sorted(
            item.receipt_id for item in visible_interval
        ))
        if compact_request:
            expected_inspected_commitment = _compact_set_commitment(
                expected_inspected,
                exclusive_frontier=frontier + 1,
            )
            if request.inspected_receipt_commitment != (
                expected_inspected_commitment
            ):
                raise ProspectiveV2IntegrityError(
                    "boundary promotion inspected commitment is incomplete"
                )
            inspected_ids = set(expected_inspected)
        elif request.inspected_receipt_ids != expected_inspected:
            raise ProspectiveV2IntegrityError(
                "boundary promotion inspected reads are incomplete"
            )
        referenced_ids = (
            set(expected_inspected)
            if compact_request else set(request.inspected_receipt_ids)
        )
        referenced_ids.update(
            request.supporting_receipt_commitment.witness_ids
            if compact_request and request.supporting_receipt_commitment
            else request.supporting_receipt_ids
        )
        referenced_ids.add(request.triggering_receipt_id)
        if any(
            receipt_id not in self.accepted_real_references
            or self.accepted_real_references[receipt_id].ordinal > frontier
            for receipt_id in referenced_ids
        ):
            raise ProspectiveV2IntegrityError(
                "boundary promotion names an unknown REAL receipt"
            )
        # Every accepted reference in this authority is produced by either the
        # native REAL ledger or the V2 REAL receipt path.  Check both concrete
        # ledgers here so a forged reference cannot masquerade as evidence.
        for receipt_id in referenced_ids:
            if receipt_id in self.consumed_receipts:
                receipt = self.consumed_receipts[receipt_id]
                if (
                    receipt.frame_kind != FrameKind.REAL.name
                    or receipt.trace.frame_kind != FrameKind.REAL.name
                ):
                    raise ProspectiveV2IntegrityError(
                        "boundary promotion names a non-REAL receipt"
                    )
            elif receipt_id not in self.base.receipts:
                raise ProspectiveV2IntegrityError(
                    "boundary promotion names an unknown REAL receipt"
                )
            elif self.base.receipts[receipt_id].decision_trace.frame_kind != (
                FrameKind.REAL.name
            ):
                raise ProspectiveV2IntegrityError(
                    "boundary promotion names a non-REAL receipt"
                )

        expected = request.fixed_polarity is AvailabilityState.AVAILABLE
        support_ids = set(
            request.supporting_receipt_commitment.witness_ids
            if compact_request and request.supporting_receipt_commitment
            else request.supporting_receipt_ids
        )
        if not compact_request:
            inspected_ids = set(request.inspected_receipt_ids)
        if request.triggering_receipt_id not in support_ids and not compact_request:
            raise ProspectiveV2IntegrityError(
                "boundary promotion trigger is not supporting evidence"
            )
        if not compact_request and not support_ids.issubset(inspected_ids):
            raise ProspectiveV2IntegrityError(
                "boundary promotion support is outside inspected reads"
            )
        support_reference_ids = (
            tuple(sorted(
                reference.receipt_id for reference in visible_interval
                if reference.receipt_id in inspected_ids
                and set(request.members).issubset(
                    reference.ordered_signal_identities
                )
                and reference.observed_outcome is expected
            ))
            if compact_request else request.supporting_receipt_ids
        )
        if compact_request:
            expected_support_commitment = _compact_set_commitment(
                support_reference_ids,
                exclusive_frontier=frontier + 1,
            )
            if request.supporting_receipt_commitment != (
                expected_support_commitment
            ):
                raise ProspectiveV2IntegrityError(
                    "boundary promotion support commitment is incomplete"
                )
            support_ids = set(support_reference_ids)
        if len(support_reference_ids) < MIN_SUPPORT:
            raise ProspectiveV2IntegrityError(
                "boundary promotion has insufficient support"
            )
        expected_support = tuple(sorted(
            reference.receipt_id for reference in visible_interval
            if (
                reference.receipt_id in inspected_ids
                and set(request.members).issubset(
                    reference.ordered_signal_identities
                )
                and reference.observed_outcome is expected
            )
        ))
        if not compact_request and request.supporting_receipt_ids != expected_support:
            raise ProspectiveV2IntegrityError(
                "boundary promotion support set is incomplete"
            )
        for receipt_id in support_ids:
            reference = self.accepted_real_references[receipt_id]
            if (
                reference.observed_outcome is not expected
                or not set(request.members).issubset(
                    reference.ordered_signal_identities
                )
                or any(
                    not _specialization_identity_role_permitted(
                        reference, member
                    )
                    for member in request.members
                )
            ):
                raise ProspectiveV2IntegrityError(
                    "boundary promotion support is polarity- or role-inconsistent"
                )
        for receipt_id in inspected_ids:
            reference = self.accepted_real_references[receipt_id]
            if (
                set(request.members).issubset(
                    reference.ordered_signal_identities
                )
                and reference.observed_outcome is not expected
            ):
                raise ProspectiveV2IntegrityError(
                    "boundary promotion contains contradictory support"
                )
        if wilson_lower_bound(len(support_ids), len(support_ids), WILSON_Z) < LOWER_BOUND:
            raise ProspectiveV2IntegrityError(
                "boundary promotion support fails the promotion gate"
            )

        return request

    def _verify_boundary_promotion_request_history(self) -> None:
        """Reconstruct every ordinary promotion at full-history boundaries."""

        compact_frontiers = tuple(
            self.states[self._adaptive_boundary_child_id(request)]
            .hypothesis.birth_frontier + 1
            for request in self.boundary_promotion_requests.values()
            if request.provenance_schema_version
            == PROVENANCE_COMMITMENT_V4
            and self._adaptive_boundary_child_id(request) in self.states
        )
        compact_prefix_commitments = (
            self._accepted_real_prefix_commitments(compact_frontiers)
            if compact_frontiers else {}
        )
        for request in self.boundary_promotion_requests.values():
            child_id = self._adaptive_boundary_child_id(request)
            state = self.states.get(child_id)
            escrow = self.adaptive_boundary_escrows.get(child_id)
            if state is None or escrow is None:
                raise ProspectiveV2IntegrityError(
                    "boundary promotion history lacks its materialized child"
                )
            frontier = (state.hypothesis.materialization_frontier
                        if request.hypothesis_birth_digest is not None else state.hypothesis.birth_frontier)
            self._validate_boundary_promotion_request(
                request,
                evidence_frontier=frontier,
                require_current_generation=False,
                ordered_reference_ids=self._accepted_real_reference_order,
                reference_ordinals=self._accepted_real_reference_ordinals,
            )
            if request.provenance_schema_version == (
                PROVENANCE_COMMITMENT_V4
            ):
                self._validate_compact_exclusion_commitment(
                    escrow.discovery_exclusion_commitment,
                    birth_frontier=state.hypothesis.birth_frontier,
                    label="boundary promotion escrow",
                    prefix_commitments=compact_prefix_commitments,
                )
                if (
                    state.hypothesis.discovery_exclusion_commitment
                    != escrow.discovery_exclusion_commitment
                    or state.hypothesis.discovery_exclusion_receipt_ids
                    != escrow.discovery_exclusion_commitment.witness_ids
                ):
                    raise ProspectiveV2IntegrityError(
                        "boundary promotion compact exclusion is incomplete"
                    )
            else:
                expected_exclusion = tuple(sorted(
                    reference.receipt_id
                    for reference in self.accepted_real_references.values()
                    if reference.ordinal <= frontier
                ))
                if (
                    escrow.discovery_exclusion_receipt_ids
                    != expected_exclusion
                    or state.hypothesis.discovery_exclusion_receipt_ids
                    != expected_exclusion
                    or state.hypothesis.discovery_receipt_ids
                    != request.inspected_receipt_ids
                ):
                    raise ProspectiveV2IntegrityError(
                        "boundary promotion discovery exclusion is incomplete"
                    )

    def _prepare_boundary_promotion_requests(
        self,
        promotions: Sequence[BoundaryPromotionRequest],
    ) -> tuple[BoundaryPromotionRequest, ...]:
        """Canonicalize a batch before the structural phase mutates state."""

        incoming = tuple(promotions)
        if any(not isinstance(item, BoundaryPromotionRequest) for item in incoming):
            raise TypeError(
                "boundary promotions require BoundaryPromotionRequest values"
            )
        candidate_ids = tuple(item.candidate_id for item in incoming)
        if len(set(candidate_ids)) != len(candidate_ids):
            raise ProspectiveV2IntegrityError(
                "duplicate boundary promotion candidate"
            )
        result: list[BoundaryPromotionRequest] = []
        for request in incoming:
            existing = self.boundary_promotion_requests.get(
                request.candidate_id
            )
            if existing is not None:
                if self._same_boundary_promotion_request(existing, request):
                    continue
                raise ProspectiveV2IntegrityError(
                    "boundary promotion candidate identity collision"
                )
            canonical = self._validate_boundary_promotion_request(request)
            pair = (canonical.members, canonical.fixed_polarity)
            live_states = self._hot_live_states()
            if any(
                (
                    state.hypothesis.members,
                    state.hypothesis.polarity,
                ) == pair
                for state in live_states.values()
            ) or any(
                (item.members, item.fixed_polarity) == pair
                for item in result
            ):
                raise ProspectiveV2IntegrityError(
                    "duplicate boundary promotion pattern and polarity"
                )
            result.append(canonical)
        return tuple(sorted(
            result,
            key=lambda item: (item.request_digest, item.candidate_id),
        ))

    def _materialize_boundary_promotion_in_place(
        self,
        request: BoundaryPromotionRequest,
        *,
        rebuild_topology: bool = True,
    ) -> str:
        """Allocate a hypothesis; continuous candidates keep their evidence."""

        child_id = self._adaptive_boundary_child_id(request)
        if child_id in self.states:
            existing = self.boundary_promotion_requests.get(request.candidate_id)
            if existing != request:
                raise ProspectiveV2IntegrityError(
                    "boundary promotion child identity collision"
                )
            return child_id
        if len(self._successor_capacity_occupants()) >= (
            DORMANT_SPECIALIZATION_CHILD_CAPACITY
        ):
            raise ProspectiveV2IntegrityError(
                "successor child capacity exceeded"
            )
        compact_request = request.provenance_schema_version == (
            PROVENANCE_COMMITMENT_V4
        )
        continuous_birth = (self._continuous_birth_for_request(request)
                            if request.hypothesis_birth_digest is not None else None)
        materialization_frontier = self.next_expected_ordinal - 1
        prefix_commitment = self._accepted_real_prefix_commitment(
            self.accepted_real_references
        )
        if continuous_birth is not None:
            prefix_commitment = continuous_birth.discovery_exclusion_commitment
        if not prefix_commitment.count:
            raise ProspectiveV2IntegrityError(
                "boundary promotion requires an accepted REAL ledger"
            )
        consensus_reads = tuple(sorted(
            set(request.inspected_receipt_ids)
            - {request.triggering_receipt_id}
        )) if continuous_birth is None else ()
        read_ids = tuple(sorted(
            set(consensus_reads) | {request.triggering_receipt_id}
        ))
        if compact_request:
            category_commitments = {
                "direct": _compact_set_commitment(
                    (request.triggering_receipt_id,),
                    exclusive_frontier=prefix_commitment.exclusive_frontier,
                ),
                "parent_support": _compact_set_commitment(
                    (), exclusive_frontier=prefix_commitment.exclusive_frontier
                ),
                "eligibility": _compact_set_commitment(
                    (), exclusive_frontier=prefix_commitment.exclusive_frontier
                ),
                "contradiction_trigger": _compact_set_commitment(
                    (), exclusive_frontier=prefix_commitment.exclusive_frontier
                ),
                "consensus_reads": (request.inspected_receipt_commitment
                                    if continuous_birth is None else _compact_set_commitment(
                                        (), exclusive_frontier=prefix_commitment.exclusive_frontier)),
            }
            if not isinstance(
                category_commitments["consensus_reads"],
                ProvenanceCommitment,
            ):
                raise ProspectiveV2IntegrityError(
                    "compact boundary request lacks consensus commitment"
                )
            read_commitments = tuple(
                (name, commitment)
                for name, commitment in category_commitments.items()
            )
            compact_categories = tuple(
                (name, _bounded_provenance_witnesses(ids))
                for name, ids in (
                    ("direct", (request.triggering_receipt_id,)),
                    ("parent_support", ()),
                    ("eligibility", ()),
                    ("contradiction_trigger", ()),
                    ("consensus_reads", consensus_reads),
                )
            )
            visible_ids = prefix_commitment.witness_ids
            nomination_frontier = (
                request.inspected_receipt_commitment.exclusive_frontier - 1
            ) if continuous_birth is None else continuous_birth.birth_frontier_ordinal
            birth_frontier = prefix_commitment.exclusive_frontier - 1
        else:
            ordinals = {
                item.receipt_id: item.ordinal
                for item in self.accepted_real_references.values()
            }
            visible_ids = tuple(sorted(ordinals))
            nomination_frontier = max(ordinals[item] for item in read_ids)
            birth_frontier = max(ordinals[item] for item in visible_ids)
            compact_categories = (
                ("direct", (request.triggering_receipt_id,)),
                ("parent_support", ()),
                ("eligibility", ()),
                ("contradiction_trigger", ()),
                ("consensus_reads", consensus_reads),
            )
            read_commitments = ()
        escrow = NominationEscrow(
            operation="ordinary",
            fixed_polarity=request.fixed_polarity,
            categorized_reads=compact_categories,
            transitive_ancestor_receipt_ids=(),
            discovery_exclusion_receipt_ids=visible_ids,
            birth_frontier=birth_frontier,
            triggering_receipt_id=request.triggering_receipt_id,
            graph_request_root_state=NodeState.CONFIRMED.name,
            graph_request_terminal_state=NodeState.CONFIRMED.name,
            considered_context_ids=(),
            selected_context_ids=(),
            nomination_read_frontier=nomination_frontier,
            certification_frontier=birth_frontier,
            escrow_schema_version=(
                NOMINATION_ESCROW_V4 if compact_request
                else NOMINATION_ESCROW_V2
            ),
            discovery_exclusion_commitment=(
                prefix_commitment if compact_request else None
            ),
            nomination_read_commitments=read_commitments,
        )
        discovery_commitment = (
            _compose_provenance_commitment(
                tuple(item for _name, item in read_commitments),
                exclusive_frontier=birth_frontier + 1,
                query_digest=_compact_query_digest({
                    "operation": "ordinary",
                    "candidate_id": request.candidate_id,
                }),
            )
            if compact_request else None
        )
        hypothesis = FrozenHypothesis(
            cell_id=child_id,
            members=request.members,
            polarity=request.fixed_polarity,
            lineage_parent_id=None,
            specialization_depth=0,
            discovery_receipt_ids=(
                discovery_commitment.witness_ids
                if compact_request else escrow.discovery_receipt_ids
            ),
            discovery_receipt_digest=(
                discovery_commitment.digest
                if compact_request else _sha(list(escrow.discovery_receipt_ids))
            ),
            birth_frontier=escrow.birth_frontier,
            structural_state=StemCellState.DORMANT.name,
            nomination_operation="ordinary",
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
            transitive_ancestor_receipt_ids=(),
            discovery_exclusion_receipt_ids=visible_ids,
            initialization_origin=InitializationOrigin.PROSPECTIVE,
            dormant_origin=DormantOrigin.ADAPTIVE_BOUNDARY_CHILD,
            parent_hypothesis_digest=None,
            source_generation=self.current_generation,
            discovery_support_receipt_ids=(
                _bounded_provenance_witnesses(request.supporting_receipt_ids
                    if continuous_birth is None else (request.triggering_receipt_id,))
                if compact_request else request.supporting_receipt_ids
            ),
            provenance_schema_version=(
                PROVENANCE_COMMITMENT_V4 if compact_request else None
            ),
            discovery_read_commitment=discovery_commitment,
            discovery_exclusion_commitment=(
                prefix_commitment if compact_request else None
            ),
            nomination_read_commitments=read_commitments,
            hypothesis_birth_digest=request.hypothesis_birth_digest,
            materialization_frontier=(materialization_frontier if continuous_birth is not None else None),
            semantic_source_identity=(continuous_birth.source_identity if continuous_birth is not None else None),
            semantic_member_roles=(continuous_birth.member_signal_roles if continuous_birth is not None else ()),
        )
        child_state = ProspectiveAuthorityState(
            hypothesis=hypothesis,
            prospectively_certified=False,
        )
        if continuous_birth is not None:
            self._transfer_continuous_boundary_evidence(child_state, request)
        self._mutation_add_mapping(self.states, child_id, child_state)
        child_invariant = CellStructuralInvariant(
            cell_id=child_id,
            members=request.members,
            polarity=request.fixed_polarity,
            lineage_parent_id=None,
            specialization_depth=0,
            structural_state=StemCellState.DORMANT.name,
            authority_node_ids=_cell_node_ids(child_id),
            authority_topology_identity=_cell_topology_identity(
                child_id,
                hypothesis.hypothesis_digest
                if compact_request else None,
            ),
            dormant_origin=DormantOrigin.ADAPTIVE_BOUNDARY_CHILD,
            immutable_hypothesis_digest=hypothesis.hypothesis_digest,
            parent_hypothesis_digest=None,
        )
        self._mutation_add_mapping(
            self.structural_invariants, child_id, child_invariant
        )
        self._mutation_add_mapping(
            self.boundary_promotion_requests,
            request.candidate_id,
            request,
        )
        self._mutation_add_mapping(
            self.adaptive_boundary_escrows, child_id, escrow
        )
        if isinstance(
            self._live_authority_state_cache, _LiveAuthorityStateView
        ):
            self._mutation_add_mapping(
                self._live_authority_state_cache, child_id, child_state
            )
        self._mutation_add_set(
            self._successor_capacity_occupant_ids, child_id
        )
        self._mutation_add_set(
            self._reserved_member_pairs, tuple(request.members)
        )
        self._mutation_add_set(
            self._active_boundary_promotion_ids, request.candidate_id
        )
        self._mutation_add_mapping(
            self._boundary_promotion_by_child,
            child_id,
            request.candidate_id,
        )
        self._refresh_active_boundary_promotion_digest(
            self._active_boundary_promotion_ids
        )
        if rebuild_topology:
            self._mutation_set_attr(
                self,
                "authority_topology",
                _executed_authority_topology_manifest(
                    self._live_authority_state_cache
                ),
            )
        promotion_payload = {
            "candidate_id": request.candidate_id,
            "child_id": child_id,
            "request": request.manifest(),
            "state": self.states[child_id].manifest(),
            "escrow": escrow.manifest(),
        }
        self._record_boundary_structure(
            "boundary_promotion_materialize", promotion_payload
        )
        self._record_boundary_candidate(
            "boundary_promotion_materialize", promotion_payload
        )
        self._record_boundary_decision(
            "boundary_promotion_materialize",
            {
                "cell_id": child_id,
                "row": self._boundary_decision_row(
                    child_id, self.states[child_id]
                ),
            },
        )
        self._advance_boundary_commitment(
            "boundary_promotion_materialize",
            {
                "promotion": promotion_payload,
                "structure_digest": self._boundary_structure_digest,
            },
        )
        return child_id

    def _require_scheduled_structural_mode(self) -> None:
        if self.structural_mode is StructuralMode.EVENT_DRIVEN:
            raise ProspectiveV2IntegrityError(
                "operation requires scheduled structural mode"
            )

    def settle_pending_structural_requests(
        self,
        promotions: Sequence[BoundaryPromotionRequest] = (),
        *,
        retire_cell_ids: Sequence[str] = (),
        retirement_reason: str = DEFAULT_RETIREMENT_REASON,
    ) -> GenerationBoundary | None:
        """Atomically settle event-driven requests at a REAL quiescent point.

        The caller chooses the event frontier by deciding when this method is
        called.  Every request emitted since the prior settlement is consumed
        in one structural successor and every accepted child is materialized
        before the next prospective generation opens.
        """

        # Preserve a true no-op for a quiescent authority: there is no
        # structural transaction to copy or commit when the queue is empty.
        if self.structural_mode is not StructuralMode.EVENT_DRIVEN:
            raise ProspectiveV2IntegrityError(
                "event-driven settlement requires event-driven structural mode"
            )
        if self.generation_phase is not GenerationPhase.PROSPECTIVE_OPEN:
            raise ProspectiveV2IntegrityError(
                "event-driven settlement requires PROSPECTIVE_OPEN"
            )
        if self.pending_event is not None:
            raise ProspectiveV2IntegrityError(
                "event-driven settlement requires a quiescent REAL boundary"
            )
        if self.evaluation_sealed:
            raise ProspectiveV2IntegrityError(
                "sealed evaluation cannot settle structural requests"
            )
        promotion_batch = tuple(promotions)
        pending_ids = self._pending_request_ids()
        # Validate explicit reclamation before selecting automatic candidates.
        # The journal below provides the all-or-nothing commit; this read-only
        # check keeps the capacity calculation honest when a caller supplied a
        # protected/unknown ID.
        retirement_batch = self._validate_retirement_batch(retire_cell_ids)
        if not pending_ids and not promotion_batch and not retirement_batch:
            return None

        # Structural settlement is an atomic mutation of a bounded live
        # projection.  A full authority deepcopy scales with every historical
        # receipt/request and made frequent local budding increasingly
        # expensive.  The journal records every touched scalar/map/set/list
        # entry and restores the exact object graph on any late failure.
        journal = _StructuralMutationJournal()
        prior_journal = getattr(self, "_structural_mutation_journal", None)
        self._structural_mutation_journal = journal
        try:
            result = self._settle_pending_structural_requests_in_place(
                promotion_batch,
                retire_cell_ids=retirement_batch,
                retirement_reason=retirement_reason,
            )
        except Exception:
            journal.rollback()
            raise
        else:
            journal.commit()
            return result
        finally:
            if prior_journal is None:
                self.__dict__.pop("_structural_mutation_journal", None)
            else:
                self._structural_mutation_journal = prior_journal

    def _settle_pending_structural_requests_in_place(
        self,
        promotions: Sequence[BoundaryPromotionRequest] = (),
        *,
        retire_cell_ids: Sequence[str] = (),
        retirement_reason: str = DEFAULT_RETIREMENT_REASON,
    ) -> GenerationBoundary | None:
        """In-place event-driven settlement; caller owns the transaction."""

        if self.structural_mode is not StructuralMode.EVENT_DRIVEN:
            raise ProspectiveV2IntegrityError(
                "event-driven settlement requires event-driven structural mode"
            )
        if self.generation_phase is not GenerationPhase.PROSPECTIVE_OPEN:
            raise ProspectiveV2IntegrityError(
                "event-driven settlement requires PROSPECTIVE_OPEN"
            )
        if self.pending_event is not None:
            raise ProspectiveV2IntegrityError(
                "event-driven settlement requires a quiescent REAL boundary"
            )
        if self.evaluation_sealed:
            raise ProspectiveV2IntegrityError(
                "sealed evaluation cannot settle structural requests"
            )

        promotion_batch = self._prepare_boundary_promotion_requests(
            promotions
        )
        pending_ids = self._pending_request_ids()
        # Validate explicit reclamation before selecting automatic candidates.
        # The transaction below is still all-or-nothing; this check simply
        # prevents an invalid explicit ID from influencing the slot forecast.
        retirement_batch = self._validate_retirement_batch(retire_cell_ids)
        if not pending_ids and not promotion_batch and not retirement_batch:
            return None
        if any(
            self.deferred_requests[request_id].source_generation
            != self.current_generation
            for request_id in pending_ids
        ):
            raise ProspectiveV2IntegrityError(
                "event-driven request queue spans structural generations"
            )

        # Preview every pending genome proposal before any phase transition.
        # Promotion members participate in the duplicate reservation set, so
        # a deferred child that would reproduce an incoming ordinary shell is
        # rejected as a duplicate rather than consuming a live slot.
        plans = self._plan_deferred_request_births(
            pending_ids,
            target_generation=self.current_generation + 1,
            incoming_promotion_members=tuple(
                item.members for item in promotion_batch
            ),
        )
        concrete_plans = tuple(
            plan for plan in plans
            if plan.consumption.child_cell_id is not None
        )

        # If the complete batch would overflow the bounded successor pool,
        # reclaim only the minimum number of weak, replaceable adaptive leaves
        # on this same transaction.  Immutable core cells, live parents, and
        # leaves with pending children are excluded by the authority-local
        # selector.  Certified REFUTED leaves are preferred over certified
        # AVAILABLE anchors; the latter are only a last-resort tier. Capacity
        # failure occurs before a request is consumed, so the original queue
        # remains pending and retryable when the outer transaction is
        # discarded.
        occupancy = self._successor_capacity_occupants()
        occupancy_after_explicit = len(
            occupancy.difference(retirement_batch)
        )
        capacity = DORMANT_SPECIALIZATION_CHILD_CAPACITY
        forecast_occupancy = (
            occupancy_after_explicit
            + len(promotion_batch)
            + len(concrete_plans)
        )
        slots_needed = max(
            0,
            forecast_occupancy - capacity,
        )
        automatic_retirement = self.deterministic_retirement_candidates(
            slots_needed,
            exclude_cell_ids=retirement_batch,
        )
        if len(automatic_retirement) < slots_needed:
            raise ProspectiveV2IntegrityError(
                "successor capacity requires "
                f"{slots_needed} adaptive retirement slots, but only "
                f"{len(automatic_retirement)} are replaceable"
            )
        retirement_batch = tuple(sorted({
            *retirement_batch,
            *automatic_retirement,
        }))

        # These three phase transitions mirror the scheduled contract, but
        # deliberately share one bounded journal and defer topology rebuilding
        # and full invariant verification until all requests have settled.  Admit
        # ordinary promotions first: they are already concrete candidates,
        # while deferred genome proposals are reservations.  This gives the
        # latter the same deterministic shared-capacity view when both kinds
        # arrive at one safe point.
        prior = self._boundary_prior_continuation_digest()
        self._mutation_set_attr(self, "sealed_request_ids", pending_ids)
        self._mutation_set_attr(
            self,
            "sealed_request_queue_digest",
            self._request_queue_digest(pending_ids),
        )
        self._mutation_set_attr(
            self, "generation_phase", GenerationPhase.PROSPECTIVE_SEALED
        )
        sealed_boundary = self._generation_boundary(
            phase=self.generation_phase,
            prior_continuation_digest=prior,
            queue_ids=pending_ids,
        )
        self._append_generation_boundary(sealed_boundary)

        prior = self._boundary_prior_continuation_digest()
        self._mutation_set_attr(
            self, "current_generation", self.current_generation + 1
        )
        self._mutation_set_attr(
            self, "generation_phase", GenerationPhase.STRUCTURAL_OPEN
        )
        structural_boundary = self._generation_boundary(
            phase=self.generation_phase,
            prior_continuation_digest=prior,
            queue_ids=pending_ids,
        )
        self._append_generation_boundary(structural_boundary)

        # Reclaim only validated adaptive leaves before admitting new births;
        # this is the sole point where one transaction can both retire and
        # reuse a bounded live successor slot.
        self._retire_adaptive_leaves_in_place(
            retirement_batch,
            reason=retirement_reason,
            require_structural_open=True,
            rebuild_topology=False,
        )
        for request in promotion_batch:
            self._materialize_boundary_promotion_in_place(
                request,
                rebuild_topology=False,
            )
        # Compact V4 children carry one shared accepted-REAL prefix
        # commitment.  Do not materialize the lifetime reference tuple/map on
        # the event-settlement hot path.  A legacy request still takes the old
        # exact compatibility route, but only when such a request is actually
        # present in this batch.
        compact_children = all(
            self.deferred_requests[plan.consumption.request_id]
            .provenance_schema_version == PROVENANCE_COMMITMENT_V4
            for plan in concrete_plans
        )
        visible_real_prefix_commitment = (
            self._accepted_real_prefix_commitment(
                self.accepted_real_references
            )
            if compact_children and concrete_plans
            else None
        )
        if not compact_children:
            if self._accepted_real_reference_order:
                visible_real_references = tuple(
                    self.accepted_real_references[receipt_id]
                    for receipt_id in self._accepted_real_reference_order
                )
            else:
                visible_real_references = tuple(sorted(
                    self.accepted_real_references.values(),
                    key=lambda item: (item.ordinal, item.receipt_id),
                ))
            visible_real_ids = tuple(sorted(self.accepted_real_references))
            visible_real_ordinals = {
                reference.receipt_id: reference.ordinal
                for reference in visible_real_references
            }
        else:
            visible_real_references = None
            visible_real_ids = None
            visible_real_ordinals = None
        planned_by_id = {
            plan.consumption.request_id: plan.consumption
            for plan in plans
        }
        while any(
            request_id not in self.request_consumptions
            for request_id in self.sealed_request_ids
        ):
            consumption = self._consume_next_structural_request_in_place(
                verify=False,
                planned=planned_by_id[
                    next(
                        request_id for request_id in self.sealed_request_ids
                        if request_id not in self.request_consumptions
                    )
                ],
            )
            if consumption.child_cell_id is not None:
                self._materialize_deferred_child_in_place_with_options(
                    consumption.request_id,
                    verify=False,
                    rebuild_topology=False,
                    visible_real_references=visible_real_references,
                    visible_real_ids=visible_real_ids,
                    visible_real_ordinals=visible_real_ordinals,
                    visible_real_prefix_commitment=(
                        visible_real_prefix_commitment
                    ),
                )

        # Rebuild once after the complete child set is known.  The final hot
        # validator consumes this exact snapshot; full canonical reclosure is
        # reserved for an explicit checkpoint/audit boundary.
        compact_topology_schema = (
            "native_v2_authority_topology.v2_digest_only"
        )
        if (
            getattr(
                self._live_authority_state_cache,
                "topology_schema_version",
                None,
            ) != compact_topology_schema
            and any(
                state.hypothesis.provenance_schema_version
                == PROVENANCE_COMMITMENT_V4
                for state in self._live_authority_state_cache.values()
            )
        ):
            # The topology builder keeps this marker sticky after the final
            # compact leaf retires.  Record the first transition in the same
            # structural journal as the birth so a late validation failure
            # restores the exact legacy cache as well as the durable fields.
            self._mutation_set_attr(
                self._live_authority_state_cache,
                "topology_schema_version",
                compact_topology_schema,
            )
        topology = _executed_authority_topology_manifest(
            self._live_authority_state_cache
        )
        self._mutation_set_attr(self, "authority_topology", topology)
        prior = self._boundary_prior_continuation_digest()
        self._mutation_set_attr(
            self, "generation_phase", GenerationPhase.PROSPECTIVE_OPEN
        )
        prospective_boundary = self._generation_boundary(
            phase=self.generation_phase,
            prior_continuation_digest=prior,
            queue_ids=pending_ids,
            retired_cell_ids=retirement_batch,
        )
        self._append_generation_boundary(prospective_boundary)
        self._mutation_set_attr(
            self, "_hot_path_revision", self._hot_path_revision + 1
        )
        self._validate_structural_hot_path(
            expected_authority_topology=topology
        )
        return prospective_boundary

    def seal_prospective_generation(self) -> GenerationBoundary:
        self._require_scheduled_structural_mode()
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
        prior = self._boundary_prior_continuation_digest()
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
        self._append_generation_boundary(boundary)
        self._verify_invariants()
        return boundary

    def open_structural_successor(self) -> GenerationBoundary:
        self._require_scheduled_structural_mode()
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
        target_generation = self.current_generation + 1
        plans = self._plan_deferred_request_births(
            self.sealed_request_ids,
            target_generation=target_generation,
        )
        concrete_count = sum(
            plan.consumption.child_cell_id is not None
            for plan in plans
        )
        slots_needed = max(
            0,
            len(self._successor_capacity_occupants())
            + concrete_count
            - DORMANT_SPECIALIZATION_CHILD_CAPACITY,
        )
        retirement_batch = self.deterministic_retirement_candidates(
            slots_needed
        )
        if len(retirement_batch) < slots_needed:
            raise ProspectiveV2IntegrityError(
                "successor capacity requires "
                f"{slots_needed} adaptive retirement slots, but only "
                f"{len(retirement_batch)} are replaceable"
            )
        prior = self._boundary_prior_continuation_digest()
        self.current_generation += 1
        self.generation_phase = GenerationPhase.STRUCTURAL_OPEN
        self._retire_adaptive_leaves_in_place(
            retirement_batch,
            reason=DEFAULT_RETIREMENT_REASON,
            require_structural_open=True,
            rebuild_topology=False,
        )
        self.structural_request_plans = {
            plan.consumption.request_id: plan.consumption
            for plan in plans
        }
        boundary = self._generation_boundary(
            phase=self.generation_phase,
            prior_continuation_digest=prior,
            queue_ids=self.sealed_request_ids,
            retired_cell_ids=retirement_batch,
        )
        self._append_generation_boundary(boundary)
        self._verify_invariants()
        return boundary

    def consume_next_structural_request(
        self,
    ) -> StructuralRequestConsumption:
        """Consume the next sealed request with the organism-frozen genome."""

        self._require_scheduled_structural_mode()
        candidate = copy.deepcopy(self)
        result = candidate._consume_next_structural_request_in_place()
        self.__dict__.clear()
        self.__dict__.update(candidate.__dict__)
        return result

    def _consume_next_structural_request_in_place(
        self,
        *,
        verify: bool = True,
        planned: StructuralRequestConsumption | None = None,
    ) -> StructuralRequestConsumption:
        if verify:
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
        if planned is None:
            planned = self._mutation_pop_mapping(
                getattr(self, "structural_request_plans", {}),
                request_id, None
            )
        if planned is None:
            planned = self._plan_deferred_request_births(
                (request_id,),
                target_generation=self.current_generation,
            )[0].consumption
        else:
            cached = self._mutation_pop_mapping(
                getattr(self, "structural_request_plans", {}),
                request_id, None
            )
            if cached is not None and cached != planned:
                raise ProspectiveV2IntegrityError(
                    "structural request plan cache differs from supplied plan"
                )
        consumption = planned
        if (
            consumption.request_id != request_id
            or consumption.attempt_ordinal != attempt
            or consumption.genome_seed != self.specialization_genome_seed
            or consumption.genome_call_count != 1
            or consumption.disposition == "REJECTED_CHILD_CAPACITY"
        ):
            raise ProspectiveV2IntegrityError(
                "structural request plan differs from sealed request"
            )
        if consumption.child_cell_id is not None:
            expected_child_id = (
                f"v2_deferred_specialization_"
                f"g{self.current_generation:02d}_{attempt:04d}"
            )
            if consumption.child_cell_id != expected_child_id:
                raise ProspectiveV2IntegrityError(
                    "structural request child identity differs from generation"
                )
            if len(self._successor_capacity_occupants()) >= (
                DORMANT_SPECIALIZATION_CHILD_CAPACITY
            ):
                # A direct scheduled consumer has no batch planner around it;
                # fail before writing a consumption so the request remains
                # retryable.  Event-driven settlement pre-forecasts and
                # retires any required slots before reaching this branch.
                raise ProspectiveV2IntegrityError(
                    "successor capacity exceeded before request admission"
                )
        self._mutation_add_mapping(
            self.request_consumptions, request_id, consumption
        )
        # Structural consumption releases one bounded queue slot.  The
        # append-only request_queue remains untouched for replay, so remove
        # only from the runtime pending order/index.
        pending_index = getattr(self, "_pending_request_index", None)
        pending_order = getattr(self, "_pending_request_order", None)
        if pending_index is not None:
            self._mutation_discard_set(pending_index, request_id)
        if pending_order is not None:
            self._mutation_remove_list_item(pending_order, request_id)
        if consumption.child_cell_id is not None:
            self._mutation_add_mapping(
                self.deferred_child_births,
                request_id,
                DeferredChildBirth(
                    request_id=request_id,
                    child_cell_id=consumption.child_cell_id,
                    members=consumption.selected_members,
                    genome_seed=self.specialization_genome_seed,
                    proposal_ordinal=attempt,
                    source_generation=self.current_generation,
                    disposition="PENDING_MATERIALIZATION",
                ),
            )
            self._mutation_add_set(
                self._pending_child_birth_request_ids, request_id
            )
            self._mutation_add_set(
                self._successor_capacity_occupant_ids,
                consumption.child_cell_id,
            )
            self._mutation_add_set(
                self._reserved_member_pairs,
                tuple(consumption.selected_members),
            )
        self._advance_boundary_commitment(
            "structural_consume",
            self._boundary_structural_consumption_payload(consumption),
        )
        if verify:
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
            for cell_id, state in _live_authority_states(self.states).items()
        }
        indexed_ids = self._accepted_real_by_signal_identity.get(identity)
        candidates = (
            tuple(
                self.accepted_real_references[receipt_id]
                for receipt_id in indexed_ids
            )
            if indexed_ids is not None
            else visible
        )
        return tuple(sorted(
            item.receipt_id for item in candidates
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
        self._require_scheduled_structural_mode()
        candidate = copy.deepcopy(self)
        result = candidate._materialize_deferred_child_in_place(request_id)
        self.__dict__.clear()
        self.__dict__.update(candidate.__dict__)
        return result

    def _materialize_deferred_child_in_place(self, request_id: str) -> str:
        self._materialize_deferred_child_in_place_with_options(request_id)
        return self.deferred_child_births[request_id].child_cell_id

    def _materialize_deferred_child_in_place_with_options(
        self,
        request_id: str,
        *,
        verify: bool = True,
        rebuild_topology: bool = True,
        visible_real_references: Sequence[AcceptedRealReference] | None = None,
        visible_real_ids: tuple[str, ...] | None = None,
        visible_real_ordinals: Mapping[str, int] | None = None,
        visible_real_prefix_commitment: ProvenanceCommitment | None = None,
    ) -> str:
        if verify:
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
        semantic_contract = self._continuous_deferred_contract(
            request, selected_identity, frontier=self.next_expected_ordinal - 1
        )
        if semantic_contract is not None and (
            semantic_contract[2] < MIN_SUPPORT or semantic_contract[3]
        ):
            raise ProspectiveV2IntegrityError("deferred materialization escaped native safe-point eligibility")
        compact_request = request.provenance_schema_version == (
            PROVENANCE_COMMITMENT_V4
        )
        if visible_real_references is None and not compact_request:
            ordered_reference_ids = self._accepted_real_reference_order
            if ordered_reference_ids:
                # REAL admission appends references in ordinal order.  Reuse
                # the maintained chronology instead of sorting the lifetime
                # mapping anew for every child materialization.
                visible = tuple(
                    self.accepted_real_references[receipt_id]
                    for receipt_id in ordered_reference_ids
                )
            else:
                # Compatibility for pre-metabolism hand-built fixtures.
                visible = tuple(sorted(
                    self.accepted_real_references.values(),
                    key=lambda item: (item.ordinal, item.receipt_id),
                ))
        elif visible_real_references is not None:
            visible = visible_real_references
        else:
            # Compact V4 children use the maintained signal index for direct
            # matching.  No lifetime reference tuple is retained or copied;
            # full resolution is reserved for explicit reclosure.
            visible = ()
        if compact_request and visible_real_prefix_commitment is None:
            visible_real_prefix_commitment = (
                self._accepted_real_prefix_commitment(
                    self.accepted_real_references
                )
            )
        if not visible:
            if not compact_request:
                raise ProspectiveV2IntegrityError(
                    "child birth has no REAL ledger"
                )
            if visible_real_prefix_commitment is None:
                visible_real_prefix_commitment = (
                    self._accepted_real_prefix_commitment(
                        self.accepted_real_references
                    )
                )
        if visible_real_ids is None:
            visible_ids = (
                tuple(sorted(item.receipt_id for item in visible))
                if visible
                else visible_real_prefix_commitment.witness_ids
            )
        else:
            visible_ids = visible_real_ids
        if visible_real_ordinals is None:
            ordinals = (
                {item.receipt_id: item.ordinal for item in visible}
                if visible
                else {}
            )
        else:
            ordinals = visible_real_ordinals
        candidate_state = next(
            item for item in request.candidate_terminals
            if item.identity == selected_identity
        )
        if compact_request:
            # Eligibility replay has already established that these are the
            # complete selected-identity occurrences in the bounded parent
            # support query.  Reuse its exact commitment; resolving the full
            # lifetime posting here made every late V4 birth history-linear.
            direct = candidate_state.supporting_receipt_ids
            direct_commitment = (
                candidate_state.supporting_receipt_commitment
            )
            if not isinstance(direct_commitment, ProvenanceCommitment):
                raise ProspectiveV2IntegrityError(
                    "compact child lacks direct-match commitment"
                )
        else:
            direct = self._matching_parent_plus_identity_receipts(
                request.parent_cell_id, selected_identity, visible
            )
            direct_commitment = None
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
        if compact_request:
            category_commitments = {
                "direct_child_matches": direct_commitment,
                "parent_discovery_reads": (
                    request.parent_discovery_commitment
                ),
                "parent_discovery_support": (
                    request.parent_discovery_support_commitment
                ),
                "parent_prospective_support": (
                    request.parent_prospective_support_commitment
                ),
                "eligibility_reads": (
                    candidate_state.inspected_receipt_commitment
                ),
                "contradiction_trigger": _compact_set_commitment(
                    (request.contradiction_receipt_id,),
                    exclusive_frontier=request.contradiction_ordinal + 1,
                ),
                "transitive_ancestor_reads": (
                    request.transitive_ancestor_commitment
                ),
            }
            if any(
                not isinstance(item, ProvenanceCommitment)
                for item in category_commitments.values()
            ):
                raise ProspectiveV2IntegrityError(
                    "compact child lacks a nomination read commitment"
                )
        else:
            category_commitments = {}
        categorized_ids = {
            receipt_id for _name, ids in categories for receipt_id in ids
        }
        if not compact_request and not categorized_ids.issubset(visible_ids):
            raise ProspectiveV2IntegrityError(
                "child escrow reads beyond V_birth"
            )
        nomination_frontier = (
            max((ordinals[item] for item in categorized_ids), default=-1)
            if ordinals else request.request_emission_ordinal
        )
        birth_frontier = (
            max(ordinals.values(), default=-1)
            if ordinals else visible_real_prefix_commitment.exclusive_frontier - 1
        )
        exclusion_commitment = (
            visible_real_prefix_commitment
            if compact_request else None
        )
        if compact_request:
            compact_categories = tuple(
                (name, _bounded_provenance_witnesses(ids))
                for name, ids in categories
            )
            compact_exclusion_ids = exclusion_commitment.witness_ids
            escrow_read_commitments = tuple(
                (name, category_commitments[name])
                for name, _ids in compact_categories
            )
        else:
            compact_categories = categories
            compact_exclusion_ids = visible_ids
            escrow_read_commitments = ()
        escrow = NominationEscrow(
            operation="specialization",
            fixed_polarity=request.fixed_polarity,
            categorized_reads=compact_categories,
            transitive_ancestor_receipt_ids=tuple(sorted(
                request.transitive_ancestor_receipt_ids
            )),
            discovery_exclusion_receipt_ids=compact_exclusion_ids,
            birth_frontier=birth_frontier,
            triggering_receipt_id=request.contradiction_receipt_id,
            graph_request_root_state=NodeState.CONFIRMED.name,
            graph_request_terminal_state=NodeState.CONFIRMED.name,
            considered_context_ids=(request.parent_cell_id,),
            selected_context_ids=(request.parent_cell_id,),
            nomination_read_frontier=nomination_frontier,
            certification_frontier=birth_frontier,
            parent_hypothesis_digest=request.parent_hypothesis_digest,
            escrow_schema_version=(
                NOMINATION_ESCROW_V4 if compact_request
                else NOMINATION_ESCROW_V3
            ),
            discovery_exclusion_commitment=exclusion_commitment,
            nomination_read_commitments=escrow_read_commitments,
        )
        if compact_request:
            discovery_commitment = _compose_provenance_commitment(
                tuple(item for _name, item in escrow_read_commitments),
                exclusive_frontier=birth_frontier + 1,
                query_digest=_compact_query_digest({
                    "operation": "specialization",
                    "parent_hypothesis_digest": (
                        request.parent_hypothesis_digest
                    ),
                }),
            )
        else:
            discovery_commitment = None
        hypothesis = FrozenHypothesis(
            cell_id=birth.child_cell_id,
            members=birth.members,
            polarity=request.fixed_polarity,
            lineage_parent_id=request.parent_cell_id,
            specialization_depth=(
                self.states[request.parent_cell_id].hypothesis
                .specialization_depth + 1
            ),
            discovery_receipt_ids=(
                discovery_commitment.witness_ids
                if compact_request else escrow.discovery_receipt_ids
            ),
            discovery_receipt_digest=(
                discovery_commitment.digest
                if compact_request else _sha(list(escrow.discovery_receipt_ids))
            ),
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
            provenance_schema_version=(
                PROVENANCE_COMMITMENT_V4 if compact_request else None
            ),
            discovery_read_commitment=discovery_commitment,
            discovery_exclusion_commitment=exclusion_commitment,
            nomination_read_commitments=escrow_read_commitments,
            semantic_source_identity=(semantic_contract[0] if semantic_contract is not None else None),
            semantic_member_roles=(semantic_contract[1] if semantic_contract is not None else ()),
        )
        child_state = ProspectiveAuthorityState(
            hypothesis=hypothesis,
            prospectively_certified=False,
        )
        self._mutation_add_mapping(
            self.states,
            birth.child_cell_id,
            child_state,
        )
        child_invariant = CellStructuralInvariant(
                cell_id=birth.child_cell_id,
                members=birth.members,
                polarity=request.fixed_polarity,
                lineage_parent_id=request.parent_cell_id,
                specialization_depth=(
                    self.states[request.parent_cell_id].hypothesis
                    .specialization_depth + 1
                ),
                structural_state=StemCellState.DORMANT.name,
                authority_node_ids=_cell_node_ids(birth.child_cell_id),
                authority_topology_identity=_cell_topology_identity(
                    birth.child_cell_id,
                    hypothesis.hypothesis_digest
                    if compact_request else None,
                ),
                dormant_origin=(
                    DormantOrigin.DEFERRED_SPECIALIZATION_CHILD
                ),
                immutable_hypothesis_digest=hypothesis.hypothesis_digest,
                parent_hypothesis_digest=(
                    request.parent_hypothesis_digest
                ),
            )
        self._mutation_add_mapping(
            self.structural_invariants,
            birth.child_cell_id,
            child_invariant,
        )
        self._mutation_add_mapping(
            self.deferred_child_escrows,
            birth.child_cell_id,
            escrow,
        )
        self._mutation_add_mapping(
            self.deferred_child_births,
            request_id,
            replace(birth, disposition="MATERIALIZED"),
        )
        self._mutation_discard_set(
            self._pending_child_birth_request_ids, request_id
        )
        self._mutation_add_set(
            self._successor_capacity_occupant_ids,
            birth.child_cell_id,
        )
        self._mutation_add_mapping(
            self.request_consumptions,
            request_id,
            replace(
                self.request_consumptions[request_id],
                disposition="MATERIALIZED",
            ),
        )
        if isinstance(
            self._live_authority_state_cache, _LiveAuthorityStateView
        ):
            self._mutation_add_mapping(
                self._live_authority_state_cache,
                birth.child_cell_id,
                child_state,
            )
        self._mutation_add_set(
            self._successor_capacity_occupant_ids,
            birth.child_cell_id,
        )
        if rebuild_topology:
            self._mutation_set_attr(
                self,
                "authority_topology",
                _executed_authority_topology_manifest(
                    self._live_authority_state_cache
                ),
            )
        child_payload = {
            "request_id": request_id,
            "birth": self.deferred_child_births[request_id].manifest(),
            "state": self.states[birth.child_cell_id].manifest(),
            "escrow": self.deferred_child_escrows[
                birth.child_cell_id
            ].manifest(),
        }
        self._record_boundary_structure(
            "deferred_child_materialize", child_payload
        )
        self._record_boundary_candidate(
            "deferred_child_materialize", child_payload
        )
        self._record_boundary_decision(
            "deferred_child_materialize",
            {
                "cell_id": birth.child_cell_id,
                "row": self._boundary_decision_row(
                    birth.child_cell_id, self.states[birth.child_cell_id]
                ),
            },
        )
        self._advance_boundary_commitment(
            "deferred_child_materialize",
            {
                "child": child_payload,
                "structure_digest": self._boundary_structure_digest,
            },
        )
        if verify:
            self._verify_invariants()
        return birth.child_cell_id

    def open_prospective_successor(self) -> GenerationBoundary:
        self._require_scheduled_structural_mode()
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
        prior = self._boundary_prior_continuation_digest()
        self.generation_phase = GenerationPhase.PROSPECTIVE_OPEN
        boundary = self._generation_boundary(
            phase=self.generation_phase,
            prior_continuation_digest=prior,
            queue_ids=self.sealed_request_ids,
        )
        self._append_generation_boundary(boundary)
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
        self._discovery_prefix_physical_fingerprint_set = frozenset(
            prefix_fingerprints
        )
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
        if candidate.boundary_digest_schema == (
            BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
        ):
            candidate._initialize_boundary_commitment()
        if not candidate.generation_boundaries:
            structural = candidate._generation_boundary(
                phase=GenerationPhase.STRUCTURAL_OPEN,
                prior_continuation_digest=(
                    candidate.base.continuation_digest_v3()
                ),
                queue_ids=(),
                prior_digest_schema=BOUNDARY_DIGEST_SCHEMA_BASE_V3,
            )
            candidate._append_generation_boundary(structural)
            prospective = candidate._generation_boundary(
                phase=GenerationPhase.PROSPECTIVE_OPEN,
                prior_continuation_digest=(
                    candidate._boundary_prior_continuation_digest()
                ),
                queue_ids=(),
            )
            candidate._append_generation_boundary(prospective)
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
                state.certification_receipt_ids = _AppendOnlyLedger()
                state.support_receipt_ids = _AppendOnlyLedger()
                state.contradiction_receipt_ids = _AppendOnlyLedger()
                state.certification_receipt_digest = _empty_hot_append_digest(
                    "certification_receipt"
                )
                state.successes = 0
                state.contradictions = 0
                state.support = 0
                state.success_lower_bound = 0.0
                state.contradiction_lower_bound = 0.0
                state.transition_rows = _AppendOnlyLedger()
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
        if self.boundary_digest_schema == (
            BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
        ):
            if not self._boundary_candidate_digest:
                self._boundary_candidate_digest = (
                    self._boundary_seed_candidate_digest()
                )
            return self._boundary_candidate_digest
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
            "retired_tombstones": self.retired_tombstones,
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


    def _native_provider_receipt_frontier_valid(self, cell_id: str) -> bool:
        """Check the bounded ends of one append-ordered REAL evidence log."""

        state = self.states.get(str(cell_id))
        if state is None or not state.certification_receipt_ids:
            return False
        first_id = str(state.certification_receipt_ids[0])
        last_id = str(state.certification_receipt_ids[-1])
        first = self.accepted_real_references.get(first_id)
        last = self.accepted_real_references.get(last_id)
        return bool(
            first is not None
            and last is not None
            and first.ordinal <= last.ordinal
            and first.observed_outcome
            and last.observed_outcome
            and _receipt_is_post_birth(state.hypothesis, first)
            and _receipt_is_post_birth(state.hypothesis, last)
        )

    def native_provider_records(
        self,
        classification: EnvelopeClassification,
    ) -> tuple[dict[str, Any], ...]:
        """Resolve currently live, locally certified shell providers.

        This is a read-only capability projection.  It neither creates a
        value cell nor promotes a hypothesis: the authority graph and its
        post-birth REAL ledger have already made those decisions.
        """

        if not isinstance(classification, EnvelopeClassification):
            raise TypeError("native provider resolution requires a classification")
        self._validate_real_hot_path(virtual=True)
        return tuple(
            record
            for record in prospective_available_provider_records(
                self.states,
                classification,
            )
            if self._native_provider_receipt_frontier_valid(
                str(record["cell_id"])
            )
        )

    def native_direct_provider_response(
        self,
        authority_cell_id: str,
    ) -> dict[str, Any] | None:
        """Project one frozen exact-action cell as a provider capability."""

        normalized = str(authority_cell_id)
        self._validate_real_hot_path(virtual=True)
        r0 = self.base.r0
        if normalized in r0.direct_provider_ids:
            direct = r0.credit.direct_outcome_provider_response(normalized)
            if isinstance(direct, Mapping):
                try:
                    expected_value = float(direct["expected_value"])
                    confidence = float(direct["confidence"])
                    uncertainty = float(direct["uncertainty"])
                    positive = direct["direct_positive_evidence"]
                    contrast = direct["direct_contrast_evidence"]
                    grounding_level = direct["grounding_level"]
                    grounding_ancestors = tuple(
                        direct["grounding_ancestors"]
                    )
                except (
                    KeyError,
                    TypeError,
                    ValueError,
                    OverflowError,
                ):
                    return None
                if (
                    any(
                        isinstance(value, bool)
                        for value in (
                            direct["expected_value"],
                            direct["confidence"],
                            direct["uncertainty"],
                        )
                    )
                    or isinstance(positive, bool)
                    or not isinstance(positive, int)
                    or isinstance(contrast, bool)
                    or not isinstance(contrast, int)
                    or isinstance(grounding_level, bool)
                    or not isinstance(grounding_level, int)
                    or any(
                        not isinstance(item, str) or not item
                        for item in grounding_ancestors
                    )
                    or tuple(sorted(set(grounding_ancestors)))
                    != grounding_ancestors
                    or not math.isfinite(expected_value)
                    or not 0.0 < expected_value <= 1.0
                    or not math.isfinite(confidence)
                    or not 0.0 < confidence <= 1.0
                    or not math.isfinite(uncertainty)
                    or not math.isclose(
                        confidence + uncertainty,
                        1.0,
                        rel_tol=0.0,
                        abs_tol=1e-12,
                    )
                    or positive < 1
                    or contrast != 0
                ):
                    return None
                hypothesis_digest = _sha({
                    "schema_version": "native_direct_provider.v1",
                    "cell_id": normalized,
                    "frozen_policy_token": r0.graph.frozen_policy_token,
                })
                evidence_digest = _sha({
                    "schema_version": "native_direct_provider_evidence.v1",
                    "cell_id": normalized,
                    "hypothesis_digest": hypothesis_digest,
                    "expected_value": expected_value,
                    "confidence": confidence,
                    "uncertainty": uncertainty,
                    "grounding_level": grounding_level,
                    "grounding_ancestors": list(grounding_ancestors),
                    "direct_positive_evidence": positive,
                    "direct_contrast_evidence": contrast,
                })
                provider_id = "native-r0-provider:" + normalized
                return {
                    "schema_version": "native_direct_provider.v1",
                    "provider_kind": "native_direct_outcome_cell",
                    # Provider capability and plastic decision identities are
                    # deliberately distinct.  The same canonical triplet may
                    # appear in the R1 graph, but it cannot shadow, demature,
                    # or circularly impersonate this frozen R0 authority.
                    "cell_id": provider_id,
                    "authority_cell_id": normalized,
                    "expected_value": expected_value,
                    "confidence": confidence,
                    "uncertainty": uncertainty,
                    "grounding_level": grounding_level,
                    "grounding_ancestors": grounding_ancestors,
                    "direct_positive_evidence": positive,
                    "direct_contrast_evidence": contrast,
                    # The external-provider contract calls this a
                    # certification commitment.  For the frozen core it binds
                    # the exact decision's direct REAL-return ledger instead
                    # of a prospective shell ledger.
                    "certification_receipt_count": positive,
                    "certification_receipt_digest": evidence_digest,
                    "evidence_scope": "exact_selected_real_return_ledger",
                    "discovery_evidence_used": False,
                    "postbirth_real_certification": False,
                    "prospectively_certified": False,
                    "direct_outcome_authorized": True,
                    "hypothesis_digest": hypothesis_digest,
                    "lineage_parent_id": None,
                    "grounding_source": "exact_selected_real_returns",
                }
        return None

    def native_provider_response(
        self,
        cell_id: str,
    ) -> dict[str, Any] | None:
        """Resolve one exact authority-owned provider for downstream TD."""

        normalized = str(cell_id)
        self._validate_real_hot_path(virtual=True)
        direct_prefix = "native-r0-provider:"
        if normalized.startswith(direct_prefix):
            direct = self.native_direct_provider_response(
                normalized[len(direct_prefix):]
            )
            if direct is None or direct["cell_id"] != normalized:
                return None
            return direct
        classification = EnvelopeClassification(
            state=AvailabilityState.AVAILABLE,
            probability=1.0,
            uncertainty=0.0,
            available_cell_ids=(normalized,),
            refuted_cell_ids=(),
            formal_available=True,
            formal_refuted=False,
            policy_response=True,
        )
        records = self.native_provider_records(classification)
        if len(records) != 1 or records[0]["cell_id"] != normalized:
            return None
        return records[0]

    def open_virtual(
        self,
        frame: FrameContext,
        *,
        frame_session: NativeV2FrameSession | None = None,
    ) -> dict[str, Any]:
        if frame_session is not None:
            frame_session._require_open(self)
        self._validate_real_hot_path(
            virtual=True,
            frozen_base_continuation_digest=(
                None
                if frame_session is None
                else frame_session.base_continuation_digest
            ),
        )
        before = self._hot_path_guard_digest()
        if frame.kind is not FrameKind.VIRTUAL:
            raise ProspectiveV2IntegrityError(
                "virtual capability requires VIRTUAL frame"
            )
        if frame_session is None:
            # V2 owns the competence-shell classification.  Query the frozen
            # R0 graph directly so the uncached path is semantically identical
            # to NativeV2FrameSession instead of passing through the obsolete
            # trace-envelope authority a second time.
            session = self.base.r0.dream_session()
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
        # Composition is monotone at the protected native core boundary: an
        # already grounded exact provider cannot be vetoed merely because the
        # prospective shell has no matching hypothesis yet.  A generalized
        # match receives authority only from its own post-birth REAL ledger;
        # the old singleton provenance remains a compatibility route for
        # historical non-local organisms, never a prerequisite for a native
        # prospective provider.
        base_availability_provenance = dict(
            raw.availability_provenance or {}
        )
        raw_base_local_provider = base_availability_provenance.get(
            "local_provider"
        )
        if not isinstance(raw_base_local_provider, Mapping):
            raw_base_local_provider = None
        base_local_provider = (
            self.native_direct_provider_response(
                str(raw_base_local_provider.get("cell_id", ""))
            )
            if raw_base_local_provider is not None
            else None
        )
        if (
            not isinstance(base_local_provider, Mapping)
            or base_local_provider.get("provider_kind")
            != "native_direct_outcome_cell"
        ):
            base_local_provider = None
        base_availability_provenance["local_provider"] = (
            None
            if base_local_provider is None
            else copy.deepcopy(dict(base_local_provider))
        )
        base_available = bool(
            raw.actuation is not None
            and base_availability_provenance.get(
                "local_direct_outcome_mode"
            ) is True
            and base_local_provider is not None
            and raw.response.available
            and raw.response.grounded is True
            and str(raw.response.child_id)
            == str(base_local_provider["authority_cell_id"])
        )
        native_provider_records = self.native_provider_records(classification)
        native_provider = (
            native_provider_records[0]
            if raw.actuation is not None and native_provider_records
            else None
        )
        native_shell_available = native_provider is not None
        legacy_provenance = self.base.r0.provenance
        legacy_shell_available = bool(
            raw.actuation is not None
            and not native_shell_available
            and classification.state is AvailabilityState.AVAILABLE
            and legacy_provenance.grounded is True
            and legacy_provenance.can_emit is True
        )
        available = bool(
            base_available
            or native_shell_available
            or legacy_shell_available
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
                # Keep read-only provenance bounded; the complete append log
                # remains available at full-history boundaries.
                "certification_receipt_count": len(
                    self.states[cell_id].certification_receipt_ids
                ),
                "certification_receipt_digest": (
                    self.states[cell_id].certification_receipt_digest
                ),
                "support": self.states[cell_id].support,
                "contradictions": self.states[cell_id].contradictions,
                "success_lower_bound": (
                    self.states[cell_id].success_lower_bound
                ),
            }
            for cell_id in matched_certified
        }
        response = ChildResponse(
            child_id=(
                str(base_local_provider["cell_id"])
                if base_available
                else (
                    str(native_provider["cell_id"])
                    if native_shell_available
                    else legacy_provenance.child_id
                )
            ),
            confirmed=available,
            policy_response=raw.actuation is not None,
            available=available,
            expected_value=(
                float(base_local_provider["expected_value"])
                if base_available
                else (
                    float(native_provider["expected_value"])
                    if native_shell_available
                    else (
                        VIRTUAL_AVAILABLE_VALUE
                        if legacy_shell_available
                        else 0.0
                    )
                )
            ),
            uncertainty=(
                float(base_local_provider["uncertainty"])
                if base_available
                else (
                    float(native_provider["uncertainty"])
                    if native_shell_available
                    else (
                        VIRTUAL_RESPONSE_UNCERTAINTY
                        if legacy_shell_available
                        else 1.0
                    )
                )
            ),
            grounded=(
                True
                if base_available
                else (
                    True
                    if native_shell_available
                    else (
                        legacy_provenance.grounded
                        if legacy_shell_available
                        else False
                    )
                )
            ),
            grounding_source=(
                str(base_local_provider["grounding_source"])
                if base_available
                else (
                    str(native_provider["grounding_source"])
                    if native_shell_available
                    else (
                        legacy_provenance.grounding_source
                        if legacy_shell_available
                        else None
                    )
                )
            ),
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
                "native_provider": (
                    None
                    if native_provider is None
                    else copy.deepcopy(native_provider)
                ),
                "native_provider_candidate_count": len(
                    native_provider_records
                ),
                "response_value": (
                    float(response.expected_value)
                ),
                "response_uncertainty": (
                    float(response.uncertainty)
                ),
                "availability_route": (
                    "native_local_direct_outcome_provider"
                    if base_available
                    else (
                        "prospectively_certified_local_shell_provider"
                        if native_shell_available
                        else (
                            "legacy_prospectively_certified_shell"
                            if legacy_shell_available
                            else "abstain"
                        )
                    )
                ),
                "base_child_id": raw.response.child_id,
                "base_grounded": raw.response.grounded,
                "base_grounding_source": raw.response.grounding_source,
                "base_availability_provenance": copy.deepcopy(
                    base_availability_provenance
                ),
                "certification_evidence_added": 0,
            },
            graph_signal_trace=trace,
        )
        after = self._hot_path_guard_digest()
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
        manifest = {
            "schema_version": self.schema_version,
            "mode": self.mode.value,
            "specialization_mode": self.specialization_mode.value,
            "specialization_genome_seed": self.specialization_genome_seed,
            "structural_mode": self.structural_mode.value,
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
            "retired_tombstones": copy.deepcopy(
                dict(sorted(self.retired_tombstones.items()))
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
            "boundary_promotion_requests": {
                key: value.manifest()
                for key, value in sorted(
                    self.boundary_promotion_requests.items()
                )
            },
            "adaptive_boundary_escrows": {
                key: value.manifest()
                for key, value in sorted(
                    self.adaptive_boundary_escrows.items()
                )
            },
            "generation_boundaries": [
                item.manifest() for item in self.generation_boundaries
            ],
            "sealed_request_ids": list(self.sealed_request_ids),
            "sealed_request_queue_digest": (
                self.sealed_request_queue_digest
            ),
            "structural_request_plans": {
                key: value.manifest()
                for key, value in sorted(
                    getattr(self, "structural_request_plans", {}).items()
                )
            },
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
        if self.boundary_hypothesis_births:
            manifest["boundary_hypothesis_births"] = {
                key: value.manifest() for key, value in sorted(self.boundary_hypothesis_births.items())
            }
            manifest["boundary_hypothesis_birth_digest"] = self._boundary_hypothesis_birth_digest
        if self.boundary_digest_schema == (
            BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
        ):
            manifest.update({
                "boundary_digest_schema": self.boundary_digest_schema,
                "boundary_commitment_origin_digest": getattr(
                    self, "_boundary_commitment_origin_digest", ""
                ),
                "boundary_commitment_digest": getattr(
                    self, "_boundary_commitment_digest", ""
                ),
                "boundary_commitment_count": int(getattr(
                    self, "_boundary_commitment_count", 0
                )),
                "boundary_accepted_real_digest": getattr(
                    self, "_boundary_accepted_real_digest", ""
                ),
                "boundary_candidate_digest": getattr(
                    self, "_boundary_candidate_digest", ""
                ),
                "boundary_decision_digest": getattr(
                    self, "_boundary_decision_digest", ""
                ),
                "boundary_schedule_digest": getattr(
                    self, "_boundary_schedule_digest", ""
                ),
                "boundary_structure_digest": getattr(
                    self, "_boundary_structure_digest", ""
                ),
            })
        return manifest

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
        live_states = _live_authority_states(organism.states)
        raw_by_id: dict[str, dict[str, Any]] = {}
        for commitment in commitments:
            cls._validate_commitment(organism, commitment)
            for cell_id in commitment.matching_cell_ids:
                state = live_states.get(cell_id)
                if state is None:
                    raise ProspectiveV2IntegrityError(
                        "exposure names unknown live frozen candidate"
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
        cells = {cell_id: [] for cell_id in live_states}
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
            "candidate_cell_ids": sorted(live_states),
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
