"""Strict prospective evidence authority V2.

Engineering-only authority escrow.  It leaves the wrapped competence graph's
structural StemCell state unchanged and adds an organism-owned, graph-consumed
prospective authority transaction.
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

import chess

from recon_lite import FormalReConEngine, FrameContext, FrameKind, Graph, Node, NodeState, NodeType

from .native_authority_handover import GraphActuation, GraphSignalTrace
from .native_competence_envelope import (
    AvailabilityState,
    CompetenceContextCell,
    CompetenceEvidenceRecord,
    EnvelopeClassification,
    wilson_lower_bound,
)
from .native_trace_competence_authority import TraceNativeCompetenceOrganism

SCHEMA_VERSION = "native_prospective_evidence_authority_v2.v1"
IMPLEMENTATION_IDENTITY = "native_prospective_two_phase_authority.v2"
AUTHORITY_AVAILABLE_ROOT = "v2_authority_available_root"
AUTHORITY_REFUTED_ROOT = "v2_authority_refuted_root"
ACTIVATION_COMMITMENT_ROOT = "v2_activation_commitment_root"
LIFECYCLE_ROOT = "v2_lifecycle_root"


def _json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_json(value)).hexdigest()


class ProspectiveV2IntegrityError(RuntimeError):
    """Fail-hard causal or authority contract violation."""


class ProspectiveProvenanceUnavailable(ProspectiveV2IntegrityError):
    """Authoritative organism state cannot supply complete discovery provenance."""


class V2Mode(str, Enum):
    PROSPECTIVE = "prospective"
    LEGACY = "legacy_same_ledger"


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

    def __post_init__(self) -> None:
        if self.polarity is None:
            raise ProspectiveV2IntegrityError(
                "polarity=None at candidate birth is forbidden"
            )
        object.__setattr__(self, "polarity", AvailabilityState(self.polarity))
        if not self.members:
            raise ProspectiveV2IntegrityError("empty pattern at candidate birth")
        if not self.discovery_receipt_ids:
            raise ProspectiveProvenanceUnavailable(
                "prospective_provenance_unavailable: empty discovery set"
            )
        canonical = tuple(sorted(set(self.discovery_receipt_ids)))
        if canonical != self.discovery_receipt_ids:
            raise ProspectiveV2IntegrityError("discovery receipt IDs are not canonical")
        expected = _sha(list(canonical))
        if self.discovery_receipt_digest != expected:
            raise ProspectiveV2IntegrityError("discovery receipt digest mismatch")

    def manifest(self) -> dict[str, Any]:
        value = asdict(self)
        value["polarity"] = self.polarity.value
        return value


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
            "pre_outcome_classification": self.pre_outcome_classification.to_manifest(),
            "matching_cell_ids": list(self.matching_cell_ids),
            "matching_cell_digest": self.matching_cell_digest,
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
class _AuthorityGraphSnapshot:
    matching_ids: frozenset[str]
    certified_available_ids: frozenset[str]
    certified_refuted_ids: frozenset[str]
    maturity_ids: frozenset[str] = frozenset()
    revocation_ids: frozenset[str] = frozenset()


def _membership_terminal(node: Node, env: Mapping[str, Any]) -> tuple[bool, bool]:
    snapshot = env.get("authority_snapshot")
    if not isinstance(snapshot, _AuthorityGraphSnapshot):
        return True, False
    role = str(node.meta["authority_role"])
    cell_id = str(node.meta["cell_id"])
    values = {
        "commitment": snapshot.matching_ids,
        "available": snapshot.certified_available_ids,
        "refuted": snapshot.certified_refuted_ids,
        "maturity": snapshot.maturity_ids,
        "revocation": snapshot.revocation_ids,
    }[role]
    node.activation.value = 1.0 if cell_id in values else 0.0
    return True, cell_id in values


def _graph_emissions(
    *,
    states: Mapping[str, ProspectiveAuthorityState],
    snapshot: _AuthorityGraphSnapshot,
    roles: Sequence[str],
) -> dict[str, tuple[str, ...]]:
    graph = Graph()
    roots = {
        "commitment": ACTIVATION_COMMITMENT_ROOT,
        "available": AUTHORITY_AVAILABLE_ROOT,
        "refuted": AUTHORITY_REFUTED_ROOT,
        "maturity": LIFECYCLE_ROOT + ":maturity",
        "revocation": LIFECYCLE_ROOT + ":revocation",
    }
    for role in roles:
        graph.add_node(Node(
            roots[role], NodeType.SCRIPT,
            meta={"confirm_policy": "or", "role": f"v2_{role}_root"},
        ))
        for cell_id in sorted(states):
            node_id = f"v2:{role}:{cell_id}"
            graph.add_node(Node(
                node_id, NodeType.TERMINAL, predicate=_membership_terminal,
                meta={
                    "terminal_kind": f"PROSPECTIVE_{role.upper()}",
                    "authority_role": role,
                    "cell_id": cell_id,
                },
            ))
            graph.add_hierarchy_pair(roots[role], node_id)
    engine = FormalReConEngine(graph, record_trace=False)
    for role in roles:
        engine.request(roots[role])
    engine.run(max_ticks=max(32, len(states) * len(roles) * 4), env={"authority_snapshot": snapshot})
    return {
        role: tuple(sorted(
            cell_id for cell_id in states
            if graph.nodes[f"v2:{role}:{cell_id}"].state == NodeState.CONFIRMED
        ))
        for role in roles
    }


def _interaction_fingerprint(
    *, source_organism_identity: str, source_state_identity: str,
    predecessor_fen: str, trace: GraphSignalTrace, actuation: GraphActuation,
    successor_fen: str, outcome_terminal_identity: str,
) -> str:
    return _sha({
        "source_organism_identity": source_organism_identity,
        "source_state_identity": source_state_identity,
        "predecessor": predecessor_fen,
        "exact_trace": trace.canonical_manifest(),
        "selected_actuation": asdict(actuation),
        "successor": successor_fen,
        "outcome_terminal_identity": outcome_terminal_identity,
    })


@dataclass
class NativeProspectiveAuthorityV2:
    base: TraceNativeCompetenceOrganism
    mode: V2Mode
    states: dict[str, ProspectiveAuthorityState]
    next_expected_ordinal: int
    pending_event: PendingRealEvent | None = None
    consumed_receipts: dict[str, V2GroundedReceipt] = field(default_factory=dict)
    consumed_tokens: set[str] = field(default_factory=set)
    interaction_fingerprints: dict[str, str] = field(default_factory=dict)
    emissions: dict[str, V2CertificationEmission] = field(default_factory=dict)
    event_transactions: dict[str, dict[str, Any]] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION
    _receipt_secret: bytes = field(default=b"native-prospective-v2-environment-terminal")

    @classmethod
    def from_organism(
        cls, source: TraceNativeCompetenceOrganism, *, mode: V2Mode,
        frontier: int | None = None,
    ) -> "NativeProspectiveAuthorityV2":
        if frontier is not None:
            raise ProspectiveV2IntegrityError("runner-supplied frontier is forbidden")
        mode = V2Mode(mode)
        base = copy.deepcopy(source)
        states: dict[str, ProspectiveAuthorityState] = {}
        memo: dict[str, frozenset[str]] = {}
        for cell in sorted(base.envelope.cells.values(), key=lambda item: item.cell_id):
            frozen = cls._hypothesis_from_cell(base, cell, memo)
            states[cell.cell_id] = ProspectiveAuthorityState(
                hypothesis=frozen,
                prospectively_certified=(mode is V2Mode.LEGACY and cell.is_mature),
            )
        return cls(
            base=base, mode=mode, states=states,
            next_expected_ordinal=base._next_event_ordinal,
        )

    @classmethod
    def _hypothesis_from_cell(
        cls,
        organism: TraceNativeCompetenceOrganism,
        cell: CompetenceContextCell,
        memo: dict[str, frozenset[str]],
    ) -> FrozenHypothesis:
        if cell.polarity is None:
            raise ProspectiveV2IntegrityError(
                "polarity=None at candidate birth is forbidden"
            )
        discovery = cls._complete_provenance(organism, cell, memo, set())
        ordinals = []
        for receipt_id in discovery:
            receipt = organism.receipts.get(receipt_id)
            if receipt is None:
                raise ProspectiveProvenanceUnavailable(
                    "prospective_provenance_unavailable: " + receipt_id
                )
            ordinals.append(receipt.event_ordinal)
        return FrozenHypothesis(
            cell_id=cell.cell_id,
            members=tuple(cell.members),
            polarity=cell.polarity,
            lineage_parent_id=cell.lineage_parent_id,
            specialization_depth=cell.specialization_depth,
            discovery_receipt_ids=tuple(sorted(discovery)),
            discovery_receipt_digest=_sha(sorted(discovery)),
            birth_frontier=max(ordinals),
            structural_state=cell.state.name,
        )

    @classmethod
    def _complete_provenance(
        cls, organism: TraceNativeCompetenceOrganism,
        cell: CompetenceContextCell,
        memo: dict[str, frozenset[str]], visiting: set[str],
    ) -> frozenset[str]:
        if cell.cell_id in memo:
            return memo[cell.cell_id]
        if cell.cell_id in visiting:
            raise ProspectiveProvenanceUnavailable(
                "prospective_provenance_unavailable: cyclic lineage"
            )
        visiting = {*visiting, cell.cell_id}
        found = set(map(str, cell.evidence_keys))
        if cell.lineage_parent_id is not None:
            parent = organism.envelope.cells.get(cell.lineage_parent_id)
            if parent is None:
                raise ProspectiveProvenanceUnavailable(
                    "prospective_provenance_unavailable: missing parent"
                )
            found.update(cls._complete_provenance(organism, parent, memo, visiting))
            admitted = [
                row for row in organism.envelope.specialization_audit.request_rows
                if row.get("admitted") and row.get("cell_id") == cell.cell_id
            ]
            if len(admitted) != 1 or not admitted[0].get("evidence_key"):
                raise ProspectiveProvenanceUnavailable(
                    "prospective_provenance_unavailable: missing contradiction trigger"
                )
            found.add(str(admitted[0]["evidence_key"]))
        if not found:
            raise ProspectiveProvenanceUnavailable(
                "prospective_provenance_unavailable: empty consulted set"
            )
        unknown = sorted(found.difference(organism.receipts))
        if unknown:
            raise ProspectiveProvenanceUnavailable(
                "prospective_provenance_unavailable: " + ",".join(unknown)
            )
        memo[cell.cell_id] = frozenset(found)
        return memo[cell.cell_id]

    def _structural_manifest(self) -> dict[str, Any]:
        return {
            cell_id: {
                "state": cell.state.name,
                "members": list(cell.members),
                "lineage_parent_id": cell.lineage_parent_id,
                "specialization_depth": cell.specialization_depth,
            }
            for cell_id, cell in sorted(self.base.envelope.cells.items())
        }

    def _matching_ids(self, trace: GraphSignalTrace) -> tuple[str, ...]:
        record = CompetenceEvidenceRecord(
            evidence_key="pre-outcome-commitment",
            active_signal_ids=trace.ordered_signal_identities,
            policy_response=True,
            observed_completion=False,
            actuator_identity=trace.actuation.actuator_identity,
            completion_terminal_identity="pending",
            signal_provenance=trace.terminal_signals,
        )
        matching = frozenset(
            cell_id for cell_id, state in self.states.items()
            if self.base.envelope._cell_matches(
                self.base.envelope.cells[cell_id], record, set()
            )
        )
        certified_available = frozenset(
            cell_id for cell_id in matching
            if self.states[cell_id].prospectively_certified
            and self.states[cell_id].hypothesis.polarity is AvailabilityState.AVAILABLE
        )
        certified_refuted = frozenset(
            cell_id for cell_id in matching
            if self.states[cell_id].prospectively_certified
            and self.states[cell_id].hypothesis.polarity is AvailabilityState.REFUTED
        )
        emitted = _graph_emissions(
            states=self.states,
            snapshot=_AuthorityGraphSnapshot(
                matching, certified_available, certified_refuted
            ),
            roles=("commitment", "available", "refuted"),
        )
        if set(emitted["commitment"]) != set(matching):
            raise ProspectiveV2IntegrityError("activation graph emission mismatch")
        return emitted["commitment"]

    def _classification(
        self, trace: GraphSignalTrace, matching_ids: Sequence[str]
    ) -> EnvelopeClassification:
        matching = frozenset(matching_ids)
        available = frozenset(
            cell_id for cell_id in matching
            if self.states[cell_id].prospectively_certified
            and self.states[cell_id].hypothesis.polarity is AvailabilityState.AVAILABLE
        )
        refuted = frozenset(
            cell_id for cell_id in matching
            if self.states[cell_id].prospectively_certified
            and self.states[cell_id].hypothesis.polarity is AvailabilityState.REFUTED
        )
        emitted = _graph_emissions(
            states=self.states,
            snapshot=_AuthorityGraphSnapshot(matching, available, refuted),
            roles=("available", "refuted"),
        )
        aids, rids = emitted["available"], emitted["refuted"]
        if aids and not rids:
            state, probability = AvailabilityState.AVAILABLE, max(
                self.states[i].success_lower_bound or 0.5 for i in aids
            )
        elif rids and not aids:
            state, probability = AvailabilityState.REFUTED, 0.0
        else:
            state, probability = AvailabilityState.UNKNOWN, 0.5
        return EnvelopeClassification(
            state, float(probability), 1.0 if state is AvailabilityState.UNKNOWN else 1.0 - float(probability),
            aids, rids, bool(aids), bool(rids), True,
        )

    def open_real_event(self, frame: FrameContext) -> tuple[PendingRealEvent, GraphSignalTrace]:
        before = self.continuation_digest()
        if frame.kind is not FrameKind.REAL:
            raise ProspectiveV2IntegrityError("VIRTUAL cannot open certification event")
        if self.pending_event is not None:
            raise ProspectiveV2IntegrityError("exactly one pending event is permitted")
        board = frame.values.get("board")
        if not isinstance(board, chess.Board):
            raise TypeError("REAL event requires chess.Board")
        actuation, trace = self.base.r0.emit_action_with_trace(frame)
        if actuation is None or trace is None:
            raise ProspectiveV2IntegrityError("graph emitted no REAL actuation")
        matching = self._matching_ids(trace)
        classification = self._classification(trace, matching)
        typed_digest = _sha([asdict(item) for item in trace.terminal_signals])
        token = _sha({
            "implementation": IMPLEMENTATION_IDENTITY,
            "ordinal": self.next_expected_ordinal,
            "frame_id": frame.frame_id,
            "trace": trace.digest(),
            "matching": list(matching),
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
            pending_token=token,
            outcome_terminal_identity="native_r0_real_completion_terminal",
        )
        if self.continuation_digest() != before:
            raise ProspectiveV2IntegrityError("prediction mutated persistent state")
        self.pending_event = pending
        self.event_transactions[token] = pending.manifest()
        return pending, trace

    def mint_environment_receipt(
        self, *, pending_token: str, trace: GraphSignalTrace,
        predecessor: chess.Board, successor: chess.Board,
        terminal_identity: str = "native_r0_real_completion_terminal",
    ) -> V2GroundedReceipt:
        pending = self.pending_event
        if pending is None or pending.pending_token != pending_token:
            raise ProspectiveV2IntegrityError("wrong pending token")
        if terminal_identity != pending.outcome_terminal_identity:
            raise ProspectiveV2IntegrityError("outcome terminal mismatch")
        if trace.frame_kind != FrameKind.REAL.name:
            raise ProspectiveV2IntegrityError("VIRTUAL trace cannot mint REAL receipt")
        fingerprint = _interaction_fingerprint(
            source_organism_identity=trace.source_organism_identity,
            source_state_identity=trace.source_state_identity,
            predecessor_fen=predecessor.fen(), trace=trace,
            actuation=trace.actuation, successor_fen=successor.fen(),
            outcome_terminal_identity=terminal_identity,
        )
        receipt_id = _sha({"fingerprint": fingerprint, "ordinal": pending.ordinal, "token": pending_token})
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
            "issuer_identity": "native_v2_environment_terminal",
        }
        signature = hmac.new(self._receipt_secret, _json(unsigned), hashlib.sha256).hexdigest()
        return V2GroundedReceipt(
            receipt_id, pending.ordinal, pending_token, FrameKind.REAL.name,
            trace.source_organism_identity, trace.source_state_identity,
            predecessor.fen(), trace, trace.actuation, successor.fen(), terminal_identity,
            successor.is_checkmate(), fingerprint,
            "native_v2_environment_terminal", signature,
        )

    def _validate_receipt(self, receipt: V2GroundedReceipt) -> None:
        expected_sig = hmac.new(
            self._receipt_secret, _json(receipt.unsigned_manifest()), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, receipt.signature):
            raise ProspectiveV2IntegrityError("receipt signature mismatch")
        if receipt.frame_kind != FrameKind.REAL.name or receipt.trace.frame_kind != FrameKind.REAL.name:
            raise ProspectiveV2IntegrityError("VIRTUAL-to-REAL receipt pairing")
        pending = self.pending_event
        if pending is None:
            raise ProspectiveV2IntegrityError("receipt before prediction")
        if receipt.ordinal != self.next_expected_ordinal or receipt.ordinal != pending.ordinal:
            raise ProspectiveV2IntegrityError("out-of-order ordinal or ordinal gap")
        if receipt.pending_token != pending.pending_token or receipt.pending_token in self.consumed_tokens:
            raise ProspectiveV2IntegrityError("wrong or consumed pending token")
        if receipt.trace.digest() != pending.trace_digest:
            raise ProspectiveV2IntegrityError("trace mismatch")
        if receipt.selected_actuation != pending.actuation:
            raise ProspectiveV2IntegrityError("actuation mismatch")
        if receipt.trace.actuation != receipt.selected_actuation:
            raise ProspectiveV2IntegrityError("trace/actuation mismatch")
        if receipt.predecessor_fen != pending.predecessor_fen:
            raise ProspectiveV2IntegrityError("predecessor mismatch")
        if receipt.source_organism_identity != pending.source_organism_identity or receipt.source_state_identity != pending.source_state_identity:
            raise ProspectiveV2IntegrityError("source identity mismatch")
        if receipt.outcome_terminal_identity != pending.outcome_terminal_identity:
            raise ProspectiveV2IntegrityError("outcome terminal mismatch")
        board = chess.Board(receipt.predecessor_fen)
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(pending.actuation.move_uci))
        if successor.fen() != receipt.successor_fen:
            raise ProspectiveV2IntegrityError("successor mismatch")
        if successor.is_checkmate() != receipt.observed_outcome:
            raise ProspectiveV2IntegrityError("outcome terminal mismatch")
        expected_fp = _interaction_fingerprint(
            source_organism_identity=receipt.source_organism_identity,
            source_state_identity=receipt.source_state_identity,
            predecessor_fen=receipt.predecessor_fen, trace=receipt.trace,
            actuation=receipt.selected_actuation, successor_fen=receipt.successor_fen,
            outcome_terminal_identity=receipt.outcome_terminal_identity,
        )
        if expected_fp != receipt.interaction_fingerprint:
            raise ProspectiveV2IntegrityError("interaction fingerprint mismatch")

    def consume(self, receipt: V2GroundedReceipt) -> V2CertificationEmission:
        existing = self.consumed_receipts.get(receipt.receipt_id)
        if existing is not None:
            if existing != receipt:
                raise ProspectiveV2IntegrityError("receipt ID collision")
            return self.emissions[receipt.receipt_id]
        known_id = self.interaction_fingerprints.get(receipt.interaction_fingerprint)
        if known_id is not None:
            raise ProspectiveV2IntegrityError(
                "reminted interaction fingerprint under new receipt identity"
            )
        self._validate_receipt(receipt)
        pending = self.pending_event
        assert pending is not None
        structural_before = self._structural_manifest()
        projected_mature: set[str] = set()
        projected_revoke: set[str] = set()
        supporting: list[str] = []
        contradictions: list[str] = []
        projected: dict[str, tuple[int, int, int, float, float]] = {}
        for cell_id in pending.matching_cell_ids:
            state = self.states[cell_id]
            if receipt.ordinal <= state.hypothesis.birth_frontier:
                continue
            supports = receipt.observed_outcome == (
                state.hypothesis.polarity is AvailabilityState.AVAILABLE
            )
            successes = state.successes + int(supports)
            contradiction_count = state.contradictions + int(not supports)
            support = state.support + 1
            success_lower = wilson_lower_bound(successes, support, 1.6448536269514722)
            contradiction_lower = wilson_lower_bound(contradiction_count, support, 1.6448536269514722)
            projected[cell_id] = (
                successes, contradiction_count, support, success_lower,
                contradiction_lower,
            )
            if supports:
                supporting.append(cell_id)
                if not state.prospectively_certified and successes >= 4 and contradiction_count == 0 and success_lower >= 0.55:
                    projected_mature.add(cell_id)
            else:
                contradictions.append(cell_id)
                if state.prospectively_certified:
                    projected_revoke.add(cell_id)
        graph = _graph_emissions(
            states=self.states,
            snapshot=_AuthorityGraphSnapshot(
                frozenset(pending.matching_cell_ids), frozenset(), frozenset(),
                frozenset(projected_mature), frozenset(projected_revoke),
            ),
            roles=("maturity", "revocation"),
        )
        if set(graph["maturity"]) != projected_mature or set(graph["revocation"]) != projected_revoke:
            raise ProspectiveV2IntegrityError("graph lifecycle emission mismatch")
        for cell_id in projected:
            if (
                self.states[cell_id].hypothesis.polarity
                != self.base.envelope.cells[cell_id].polarity
            ):
                raise ProspectiveV2IntegrityError(
                    "polarity mutation during certification"
                )
        for cell_id, values in projected.items():
            state = self.states[cell_id]
            state.successes, state.contradictions, state.support, state.success_lower_bound, state.contradiction_lower_bound = values
            state.certification_receipt_ids = (*state.certification_receipt_ids, receipt.receipt_id)
            if cell_id in supporting:
                state.support_receipt_ids = (*state.support_receipt_ids, receipt.receipt_id)
            else:
                state.contradiction_receipt_ids = (*state.contradiction_receipt_ids, receipt.receipt_id)
            transition = None
            if cell_id in graph["maturity"]:
                state.prospectively_certified = True
                transition = "GRAPH_PROSPECTIVE_MATURITY"
            elif cell_id in graph["revocation"]:
                state.prospectively_certified = False
                transition = "GRAPH_LOCAL_REVOCATION"
            if transition:
                state.transition_rows = (*state.transition_rows, {
                    "transition": transition,
                    "receipt_id": receipt.receipt_id,
                    "ordinal": receipt.ordinal,
                    "pending_token": receipt.pending_token,
                })
        emission = V2CertificationEmission(
            receipt.receipt_id, pending.matching_cell_ids,
            tuple(sorted(supporting)), tuple(sorted(contradictions)),
            graph["maturity"], graph["revocation"],
            graph["maturity"], graph["revocation"], True,
        )
        self.consumed_receipts[receipt.receipt_id] = receipt
        self.consumed_tokens.add(receipt.pending_token)
        self.interaction_fingerprints[receipt.interaction_fingerprint] = receipt.receipt_id
        self.emissions[receipt.receipt_id] = emission
        self.next_expected_ordinal += 1
        self.event_transactions[receipt.pending_token] = {
            **pending.manifest(),
            "state": "CONSUMED",
            "consumed_receipt_id": receipt.receipt_id,
        }
        self.pending_event = None
        if self._structural_manifest() != structural_before:
            raise ProspectiveV2IntegrityError("prospective authority altered structural state")
        return emission

    def sync_organism_nominations(self) -> tuple[str, ...]:
        """Attach authority escrow only to cells already born inside the organism."""
        if self.pending_event is not None:
            raise ProspectiveV2IntegrityError(
                "candidate born during event before authority lifecycle completed"
            )
        new_ids = tuple(sorted(set(self.base.envelope.cells).difference(self.states)))
        memo: dict[str, frozenset[str]] = {}
        frozen = [
            self._hypothesis_from_cell(
                self.base, self.base.envelope.cells[cell_id], memo
            )
            for cell_id in new_ids
        ]
        for hypothesis in frozen:
            self.states[hypothesis.cell_id] = ProspectiveAuthorityState(
                hypothesis=hypothesis,
                prospectively_certified=False,
            )
        return new_ids

    def retrospective_certify(self, *_args: Any, **_kwargs: Any) -> None:
        raise ProspectiveV2IntegrityError(
            "retrospective ledger scan cannot grant prospective authority"
        )

    def match_after_outcome(self, *_args: Any, **_kwargs: Any) -> None:
        raise ProspectiveV2IntegrityError("post-outcome matching is forbidden")

    def consume_with_authority_outcome(self, *_args: Any, **_kwargs: Any) -> None:
        raise ProspectiveV2IntegrityError("authority-layer outcome relabeling is forbidden")

    def nominate_suffix(self, *_args: Any, **_kwargs: Any) -> None:
        raise ProspectiveV2IntegrityError("suffix nomination is forbidden")

    def assert_candidate_parity(self, other: "NativeProspectiveAuthorityV2") -> None:
        left = _sha({key: value.hypothesis.manifest() for key, value in sorted(self.states.items())})
        right = _sha({key: value.hypothesis.manifest() for key, value in sorted(other.states.items())})
        if left != right:
            raise ProspectiveV2IntegrityError("candidate-manifest disparity")

    def open_virtual(self, frame: FrameContext) -> dict[str, Any]:
        before = self.continuation_digest()
        if frame.kind is not FrameKind.VIRTUAL:
            raise ProspectiveV2IntegrityError("virtual capability requires VIRTUAL frame")
        session = self.base.dream_session()
        result = session.request(frame)
        session.close()
        if self.continuation_digest() != before:
            raise ProspectiveV2IntegrityError("VIRTUAL evaluation mutated state")
        return {"query": result, "certification_commitment": None}

    def continuation_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "mode": self.mode.value,
            "base_v3": self.base.continuation_manifest_v3(),
            "states": {key: value.manifest() for key, value in sorted(self.states.items())},
            "next_expected_ordinal": self.next_expected_ordinal,
            "pending_event": None if self.pending_event is None else self.pending_event.manifest(),
            "consumed_receipts": {key: value.manifest() for key, value in sorted(self.consumed_receipts.items())},
            "consumed_tokens": sorted(self.consumed_tokens),
            "interaction_fingerprints": dict(sorted(self.interaction_fingerprints.items())),
            "emissions": {key: value.manifest() for key, value in sorted(self.emissions.items())},
            "event_transactions": copy.deepcopy(dict(sorted(self.event_transactions.items()))),
            "structural_manifest": self._structural_manifest(),
        }

    def continuation_digest(self) -> str:
        return _sha(self.continuation_manifest())

    def dumps(self) -> bytes:
        return pickle.dumps(copy.deepcopy(self), protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def loads(cls, payload: bytes) -> "NativeProspectiveAuthorityV2":
        item = pickle.loads(payload)
        if not isinstance(item, cls):
            raise TypeError("wrong V2 organism type")
        before = item.continuation_manifest()
        item.base._canonical_rebuild()
        if item.continuation_manifest() != before:
            raise ProspectiveV2IntegrityError("serialization restore changed state")
        return item


@dataclass
class OutcomeBlindExposureScanner:
    """Read-only exposure admission; accepts traces and frozen states, no outcomes."""

    @staticmethod
    def scan(
        organism: NativeProspectiveAuthorityV2,
        traces: Sequence[GraphSignalTrace],
    ) -> dict[str, Any]:
        before = organism.continuation_digest()
        opportunities: dict[str, set[str]] = {cell_id: set() for cell_id in organism.states}
        for offset, trace in enumerate(traces):
            if trace.frame_kind != FrameKind.REAL.name:
                continue
            prospective_ordinal = organism.next_expected_ordinal + offset
            matching = organism._matching_ids(trace)
            for cell_id in matching:
                state = organism.states[cell_id]
                if prospective_ordinal > state.hypothesis.birth_frontier:
                    opportunities[cell_id].add(_sha({
                        "ordinal": prospective_ordinal,
                        "trace": trace.digest(),
                        "cell_id": cell_id,
                    }))
        result = {
            "cells": {
                cell_id: {
                    "distinct_opportunities": len(sorted(values)),
                    "opportunity_ids": sorted(values),
                }
                for cell_id, values in sorted(opportunities.items())
            },
            "qualifies": any(len(values) >= 4 for values in opportunities.values()),
            "outcome_fields_read": 0,
        }
        if organism.continuation_digest() != before:
            raise ProspectiveV2IntegrityError("exposure scan mutated organism")
        return result

    @staticmethod
    def adjudicate_cohort(scans: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        if len(scans) != 32:
            raise ProspectiveV2IntegrityError(
                "exposure admission requires exactly 32 organisms"
            )
        qualifying = sum(bool(scan.get("qualifies")) for scan in scans)
        admitted = qualifying >= 24
        return {
            "organism_count": 32,
            "qualifying_organisms": qualifying,
            "required_qualifying_organisms": 24,
            "admitted": admitted,
            "stop_reason": None if admitted else "prospective_evidence_starvation",
        }
