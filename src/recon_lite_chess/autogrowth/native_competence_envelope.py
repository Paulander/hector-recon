"""Graph-native, outcome-grounded competence envelope around frozen native R0."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import math
import pickle
from typing import Any, Iterable, Mapping, Sequence

import chess

from recon_lite import (
    ChildResponse,
    FormalReConEngine,
    FrameContext,
    FrameKind,
    Graph,
    Node,
    NodeState,
    NodeType,
)
from recon_lite_hector.nodes import StemCellState, StemCellTerminal

from .native_authority_handover import (
    ChildQuery,
    GraphActuation,
    NativeR0DreamSession,
    NativeR0Organism,
)
from .native_single_graph_curriculum import _triplet_keys


POLICY_RESPONSE_SIGNAL_ID = "internal:policy_response"
AVAILABLE_ROOT_ID = "competence_available_root"
REFUTED_ROOT_ID = "competence_refuted_root"
SHADOW_ROOT_ID = "competence_shadow_root"
GROWTH_REQUEST_ROOT_ID = "competence_growth_request_root"
AVAILABILITY_ERROR_ID = "internal:availability_error"
CORRECTION_ROOT_ID = "competence_mature_correction_root"
SPECIALIZATION_REQUEST_ROOT_ID = "competence_specialization_request_root"
SPECIALIZATION_ELIGIBILITY_ROOT_ID = "competence_specialization_eligibility_root"
SCHEMA_VERSION = "native_r0_competence_envelope.v1"


class AvailabilityState(str, Enum):
    AVAILABLE = "available"
    REFUTED = "refuted"
    UNKNOWN = "unknown"


class SpecializationMode(str, Enum):
    DISCONNECTED = "disconnected"
    LOCAL_CONTRAST = "local_contrast"
    COUNTEREXAMPLE_BLIND = "counterexample_blind"


@dataclass(frozen=True)
class CompetenceEnvelopeConfig:
    wilson_z: float = 1.6448536269514722
    min_maturity_support: int = 4
    lower_bound_threshold: float = 0.55
    positive_capacity: int = 32
    refuted_capacity: int = 32
    trial_capacity: int = 192
    proposal_attempt_cap: int = 192
    structural_rounds: int = 3
    selection_seed: int = 2026071606
    retrieval_budget: int = 16

    def __post_init__(self) -> None:
        if self.min_maturity_support != 4:
            raise ValueError("frozen minimum maturity support changed")
        if not math.isclose(self.lower_bound_threshold, 0.55):
            raise ValueError("frozen lower-bound threshold changed")
        if self.structural_rounds != 3:
            raise ValueError("frozen structural-round count changed")
        if self.proposal_attempt_cap != 192 or self.trial_capacity != 192:
            raise ValueError("frozen competence resource cap changed")
        if self.retrieval_budget != 16:
            raise ValueError("frozen R0 retrieval budget changed")


@dataclass(frozen=True)
class CompetenceEvidenceRecord:
    evidence_key: str
    active_signal_ids: tuple[str, ...]
    policy_response: bool
    observed_completion: bool
    actuator_identity: str
    completion_terminal_identity: str

    def __post_init__(self) -> None:
        if not self.evidence_key:
            raise ValueError("evidence_key is required")
        if not self.actuator_identity:
            raise ValueError("actuator_identity is required")
        if any("fen" in item.lower() for item in self.active_signal_ids):
            raise ValueError("FEN identity is forbidden in competence signals")


@dataclass
class CompetenceContextCell:
    cell_id: str
    members: tuple[str, ...]
    born_round: int
    born_request_ordinal: int
    stem_cell: StemCellTerminal
    polarity: AvailabilityState | None = None
    evidence_keys: tuple[str, ...] = ()
    successes: int = 0
    failures: int = 0
    support: int = 0
    success_lower_bound: float = 0.0
    failure_lower_bound: float = 0.0
    conservative_success_estimate: float = 0.0
    uncertainty: float = 1.0
    maturity_review: int | None = None
    prune_reason: str | None = None
    revoked_evidence_key: str | None = None
    revocation_count: int = 0
    lineage_parent_id: str | None = None
    specialization_depth: int = 0
    specialization_request_ordinal: int | None = None
    specialization_proposal_ordinal: int | None = None
    provenance: str = "unique_real_r0_completion"

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        self.__dict__.update(state)
        self.__dict__.setdefault("revoked_evidence_key", None)
        self.__dict__.setdefault("revocation_count", 0)
        self.__dict__.setdefault("lineage_parent_id", None)
        self.__dict__.setdefault("specialization_depth", 0)
        self.__dict__.setdefault("specialization_request_ordinal", None)
        self.__dict__.setdefault("specialization_proposal_ordinal", None)

    @property
    def state(self) -> StemCellState:
        return self.stem_cell.state

    @property
    def is_mature(self) -> bool:
        return self.stem_cell.state == StemCellState.MATURE

    @property
    def is_trial(self) -> bool:
        return self.stem_cell.state == StemCellState.TRIAL

    def to_manifest(self) -> dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "members": list(self.members),
            "born_round": self.born_round,
            "born_request_ordinal": self.born_request_ordinal,
            "stem_cell": self.stem_cell.to_dict(),
            "polarity": None if self.polarity is None else self.polarity.value,
            "evidence_keys": list(self.evidence_keys),
            "successes": self.successes,
            "failures": self.failures,
            "support": self.support,
            "success_lower_bound": self.success_lower_bound,
            "failure_lower_bound": self.failure_lower_bound,
            "conservative_success_estimate": self.conservative_success_estimate,
            "uncertainty": self.uncertainty,
            "maturity_review": self.maturity_review,
            "prune_reason": self.prune_reason,
            "revoked_evidence_key": self.revoked_evidence_key,
            "revocation_count": self.revocation_count,
            "provenance": self.provenance,
        }


@dataclass(frozen=True)
class EnvelopeClassification:
    state: AvailabilityState
    probability: float
    uncertainty: float
    available_cell_ids: tuple[str, ...]
    refuted_cell_ids: tuple[str, ...]
    formal_available: bool
    formal_refuted: bool
    policy_response: bool

    @property
    def predicted_availability(self) -> float:
        if self.state == AvailabilityState.AVAILABLE:
            return 1.0
        if self.state == AvailabilityState.REFUTED:
            return 0.0
        return 0.5

    def to_manifest(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "probability": self.probability,
            "uncertainty": self.uncertainty,
            "available_cell_ids": list(self.available_cell_ids),
            "refuted_cell_ids": list(self.refuted_cell_ids),
            "formal_available": self.formal_available,
            "formal_refuted": self.formal_refuted,
            "policy_response": self.policy_response,
        }


@dataclass
class NativeCompetenceSessionAudit:
    """Ephemeral observation sink; never part of serialized organism state."""

    session_open_count: int = 0
    request_count: int = 0
    session_close_count: int = 0
    open_events: list[dict[str, Any]] = field(default_factory=list)
    request_events: list[dict[str, Any]] = field(default_factory=list)
    close_events: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class GrowthRequestEmission:
    emitted: bool
    availability_error: float
    root_state: str
    terminal_state: str


@dataclass(frozen=True)
class GrowthProposal:
    members: tuple[str, ...]
    round_index: int
    request_ordinal: int
    genome_seed: int


@dataclass
class GrowthAudit:
    request_opportunities: int = 0
    graph_request_emissions: int = 0
    proposal_attempts: int = 0
    admitted_proposals: int = 0
    duplicate_rejections: int = 0
    capacity_rejections: int = 0
    insufficient_member_rejections: int = 0
    proposal_rows: list[dict[str, Any]] = field(default_factory=list)
    lifecycle_reviews: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class MatureCorrectionAudit:
    unique_real_observations: int = 0
    duplicate_observations: int = 0
    contradiction_hits: int = 0
    mature_to_probation_transitions: int = 0
    query_rows: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SpecializationAudit:
    request_opportunities: int = 0
    graph_request_emissions: int = 0
    proposal_attempts: int = 0
    admitted_proposals: int = 0
    empty_eligibility_rejections: int = 0
    duplicate_rejections: int = 0
    capacity_rejections: int = 0
    request_rows: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class MatureCorrectionEmission:
    evidence_key: str
    evidence_inserted: bool
    matching_cell_ids: tuple[str, ...]
    supporting_cell_ids: tuple[str, ...]
    contradiction_cell_ids: tuple[str, ...]
    transitioned_cell_ids: tuple[str, ...]
    lifecycle_connected: bool
    root_state: str
    leg_states: tuple[tuple[str, str], ...]
    specialization_mode: str = SpecializationMode.DISCONNECTED.value
    specialization_request_parent_ids: tuple[str, ...] = ()
    specialization_child_ids: tuple[str, ...] = ()
    specialization_eligible_terminal_ids: tuple[tuple[str, tuple[str, ...]], ...] = ()


@dataclass(frozen=True)
class _GraphSpecializationRequest:
    context_member: str
    eligible_base_ids: tuple[str, ...]
    request_ordinal: int



class CompetenceContextGrowthGenome:
    """Content-blind member choice owned by the generic growth genome."""

    def __init__(
        self, seed: int = 2026071606,
        ordinal_permutation: Sequence[int] | None = None,
    ) -> None:
        self.seed = int(seed)
        self.ordinal_permutation = (
            None if ordinal_permutation is None
            else tuple(map(int, ordinal_permutation))
        )

    def propose(
        self,
        *,
        active_base_ids: Iterable[str],
        active_mature_context_ids: Iterable[str],
        round_index: int,
        request_ordinal: int,
    ) -> GrowthProposal | None:
        bases = tuple(sorted(set(map(str, active_base_ids))))
        contexts = tuple(sorted(set(map(str, active_mature_context_ids))))
        if round_index == 0:
            selected = self._take(bases, 1, round_index, request_ordinal)
        elif round_index == 1:
            selected = self._take(bases, 2, round_index, request_ordinal)
        elif round_index == 2 and contexts:
            parent = self._take(
                tuple(f"context:{item}" for item in contexts),
                1,
                round_index,
                request_ordinal,
            )
            base = self._take(bases, 1, round_index, request_ordinal + 1)
            selected = (*parent, *base)
        elif round_index == 2:
            selected = self._take(bases, 3, round_index, request_ordinal)
        else:
            raise ValueError("unsupported frozen structural round")
        expected_count = 2 if round_index == 2 and contexts else round_index + 1
        if len(selected) != expected_count:
            return None
        return GrowthProposal(
            members=tuple(selected),
            round_index=round_index,
            request_ordinal=request_ordinal,
            genome_seed=self.seed,
        )

    def propose_specialization(
        self, request: _GraphSpecializationRequest
    ) -> GrowthProposal | None:
        """Choose one anonymous base terminal from a graph-owned request."""

        if not isinstance(request, _GraphSpecializationRequest):
            raise TypeError("specialization requires a graph-owned request")
        selected = self._take(
            request.eligible_base_ids, 1, 2, request.request_ordinal
        )
        if len(selected) != 1:
            return None
        return GrowthProposal(
            members=(request.context_member, selected[0]),
            round_index=2,
            request_ordinal=request.request_ordinal,
            genome_seed=self.seed,
        )

    def _take(
        self,
        identities: Sequence[str],
        count: int,
        round_index: int,
        request_ordinal: int,
    ) -> tuple[str, ...]:
        ranked = sorted(
            set(identities),
            key=lambda identity: self._priority(
                identity, round_index, request_ordinal
            ),
        )
        return tuple(ranked[:count])

    def _priority(
        self, identity: str, round_index: int, request_ordinal: int
    ) -> bytes:
        if self.ordinal_permutation:
            request_ordinal = self.ordinal_permutation[
                request_ordinal % len(self.ordinal_permutation)
            ]
        payload = (
            f"{self.seed}|{round_index}|{request_ordinal}|{identity}"
        ).encode("utf-8")
        return hashlib.blake2b(payload, digest_size=16).digest()


@dataclass
class GraphNativeCompetenceEnvelope:
    config: CompetenceEnvelopeConfig = field(default_factory=CompetenceEnvelopeConfig)
    cells: dict[str, CompetenceContextCell] = field(default_factory=dict)
    evidence: dict[str, CompetenceEvidenceRecord] = field(default_factory=dict)
    audit: GrowthAudit = field(default_factory=GrowthAudit)
    correction_audit: MatureCorrectionAudit = field(
        default_factory=MatureCorrectionAudit
    )
    specialization_audit: SpecializationAudit = field(
        default_factory=SpecializationAudit
    )
    schema_version: str = SCHEMA_VERSION
    graph: Graph = field(init=False)
    _member_specs: set[tuple[str, ...]] = field(default_factory=set, init=False)
    _next_cell_index: int = 0
    _review_count: int = 0
    _specialization_request_ordinal: int = 0
    _specialization_proposal_ordinal: int = 0

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        self.__dict__.update(state)
        self.__dict__.setdefault("correction_audit", MatureCorrectionAudit())
        self.__dict__.setdefault("specialization_audit", SpecializationAudit())
        self.__dict__.setdefault("_specialization_request_ordinal", 0)
        self.__dict__.setdefault("_specialization_proposal_ordinal", 0)

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported envelope schema: {self.schema_version}")
        self._member_specs = {cell.members for cell in self.cells.values()}
        self._next_cell_index = max(
            (
                int(cell_id.rsplit("_", 1)[-1]) + 1
                for cell_id in self.cells
                if cell_id.rsplit("_", 1)[-1].isdigit()
            ),
            default=self._next_cell_index,
        )
        self.rebuild_graph()

    def add_unique_evidence(self, record: CompetenceEvidenceRecord) -> bool:
        existing = self.evidence.get(record.evidence_key)
        if existing is not None:
            if existing != record:
                raise RuntimeError("evidence-key collision with different record")
            return False
        self.evidence[record.evidence_key] = record
        return True

    def observe_real_outcome(
        self,
        frame: FrameContext,
        record: CompetenceEvidenceRecord,
        *,
        lifecycle_connected: bool,
        specialization_mode: SpecializationMode = SpecializationMode.DISCONNECTED,
        specialization_genome: CompetenceContextGrowthGenome | None = None,
    ) -> MatureCorrectionEmission:
        """Ground one unique real outcome and consume graph-emitted corrections."""

        if not isinstance(frame, FrameContext) or frame.kind is not FrameKind.REAL:
            raise ValueError("competence correction requires a REAL FrameContext")
        mode = SpecializationMode(specialization_mode)
        inserted = self.add_unique_evidence(record)
        if not inserted:
            self.correction_audit.duplicate_observations += 1
            return MatureCorrectionEmission(
                evidence_key=record.evidence_key,
                evidence_inserted=False,
                matching_cell_ids=(),
                supporting_cell_ids=(),
                contradiction_cell_ids=(),
                transitioned_cell_ids=(),
                lifecycle_connected=bool(lifecycle_connected),
                root_state="NOT_REQUESTED_DUPLICATE",
                leg_states=(),
                specialization_mode=mode.value,
            )
        self.correction_audit.unique_real_observations += 1
        matching = tuple(sorted(
            cell.cell_id
            for cell in self.cells.values()
            if self._cell_pattern_matches(cell, record, set())
        ))
        for cell_id in matching:
            self._refresh_cell_evidence(self.cells[cell_id])
        query = self._emit_mature_correction(record, specialization_mode=mode)
        contradictory = query["confirmed_cell_ids"]
        supporting = tuple(sorted(
            cell_id for cell_id in matching
            if cell_id not in set(contradictory)
        ))
        transitioned: list[str] = []
        if lifecycle_connected:
            for cell_id in contradictory:
                cell = self.cells[cell_id]
                if cell.state != StemCellState.MATURE:
                    continue
                cell.stem_cell.state = StemCellState.PROBATION
                cell.stem_cell.metadata["maturity_revoked"] = True
                cell.stem_cell.metadata["revoked_evidence_key"] = record.evidence_key
                cell.revoked_evidence_key = record.evidence_key
                cell.revocation_count += 1
                transitioned.append(cell_id)
        request_parents: list[str] = []
        child_ids: list[str] = []
        if lifecycle_connected and mode is not SpecializationMode.DISCONNECTED:
            graph_requests = set(query["specialization_request_parent_ids"])
            eligible_by_parent = dict(query["eligible_terminal_ids_by_parent"])
            genome = specialization_genome or CompetenceContextGrowthGenome(
                self.config.selection_seed
            )
            for parent_id in transitioned:
                parent = self.cells[parent_id]
                if parent.specialization_depth != 0:
                    continue
                if parent.specialization_request_ordinal is not None:
                    continue
                if parent_id not in graph_requests:
                    raise RuntimeError(
                        "transitioned parent lacked graph specialization request"
                    )
                request_ordinal = self._specialization_request_ordinal
                self._specialization_request_ordinal += 1
                parent.specialization_request_ordinal = request_ordinal
                request_parents.append(parent_id)
                self.specialization_audit.request_opportunities += 1
                self.specialization_audit.graph_request_emissions += 1
                self.specialization_audit.proposal_attempts += 1
                proposal_ordinal = self._specialization_proposal_ordinal
                self._specialization_proposal_ordinal += 1
                eligible = tuple(eligible_by_parent.get(parent_id, ()))
                proposal = genome.propose_specialization(
                    _GraphSpecializationRequest(
                        context_member=f"context:{parent_id}",
                        eligible_base_ids=eligible,
                        request_ordinal=request_ordinal,
                    )
                )
                child = self._materialize_specialization(
                    parent=parent,
                    proposal=proposal,
                    proposal_ordinal=proposal_ordinal,
                    mode=mode,
                    eligible_terminal_ids=eligible,
                    evidence_key=record.evidence_key,
                )
                if child is not None:
                    child_ids.append(child.cell_id)
            if child_ids:
                self._review_lifecycle(final=False)
        self.correction_audit.contradiction_hits += len(contradictory)
        self.correction_audit.mature_to_probation_transitions += len(transitioned)
        row = {
            "evidence_key": record.evidence_key,
            "matching_cell_ids": list(matching),
            "supporting_cell_ids": list(supporting),
            "contradiction_cell_ids": list(contradictory),
            "transitioned_cell_ids": list(transitioned),
            "lifecycle_connected": bool(lifecycle_connected),
            "root_state": query["root_state"],
            "leg_states": [list(item) for item in query["leg_states"]],
        }
        self.correction_audit.query_rows.append(row)
        if transitioned or child_ids:
            self.rebuild_graph()
        return MatureCorrectionEmission(
            evidence_key=record.evidence_key,
            evidence_inserted=True,
            matching_cell_ids=matching,
            supporting_cell_ids=supporting,
            contradiction_cell_ids=contradictory,
            transitioned_cell_ids=tuple(transitioned),
            lifecycle_connected=bool(lifecycle_connected),
            root_state=query["root_state"],
            leg_states=query["leg_states"],
            specialization_mode=mode.value,
            specialization_request_parent_ids=tuple(request_parents),
            specialization_child_ids=tuple(child_ids),
            specialization_eligible_terminal_ids=tuple(
                (parent_id, tuple(query["eligible_terminal_ids_by_parent"].get(parent_id, ())))
                for parent_id in request_parents
            ),
        )

    def _emit_mature_correction(
        self,
        record: CompetenceEvidenceRecord,
        *,
        specialization_mode: SpecializationMode,
    ) -> dict[str, Any]:
        runtime = copy.deepcopy(self.graph)
        candidate_pairs = self._attach_specialization_candidate_terminals(runtime)
        eligible_pairs = self._eligible_specialization_pairs(
            record, mode=specialization_mode
        )
        legs = tuple(sorted(
            (
                node_id,
                str(node.meta["cell_id"]),
            )
            for node_id, node in runtime.nodes.items()
            if node.meta.get("role") == "mature_correction_leg"
        ))
        engine = FormalReConEngine(runtime, record_trace=False)
        engine.request(CORRECTION_ROOT_ID)
        specialization_connected = (
            specialization_mode is not SpecializationMode.DISCONNECTED
        )
        if specialization_connected:
            engine.request(SPECIALIZATION_REQUEST_ROOT_ID)
            engine.request(SPECIALIZATION_ELIGIBILITY_ROOT_ID)
        engine.run(
            max_ticks=192,
            env={
                "active_signal_ids": frozenset(record.active_signal_ids),
                "observed_completion": bool(record.observed_completion),
                "eligible_specialization_pairs": frozenset(eligible_pairs),
            },
            until=lambda item: all(
                item.g.nodes[node_id].state
                in {NodeState.CONFIRMED, NodeState.FAILED}
                for node_id, _cell_id in legs
            ) and (
                not specialization_connected
                or (
                    item.g.nodes[SPECIALIZATION_REQUEST_ROOT_ID].state
                    in {NodeState.CONFIRMED, NodeState.FAILED}
                    and item.g.nodes[SPECIALIZATION_ELIGIBILITY_ROOT_ID].state
                    in {NodeState.CONFIRMED, NodeState.FAILED}
                    and all(
                        item.g.nodes[node_id].state
                        in {NodeState.CONFIRMED, NodeState.FAILED}
                        for _parent_id, _base_id, node_id in candidate_pairs
                    )

                )
            ),
        )
        leg_states = tuple(
            (cell_id, runtime.nodes[node_id].state.name)
            for node_id, cell_id in legs
        )
        confirmed = tuple(sorted(
            cell_id for node_id, cell_id in legs
            if runtime.nodes[node_id].state == NodeState.CONFIRMED
        ))
        request_parents = tuple(sorted(
            str(node.meta["cell_id"])
            for node in runtime.nodes.values()
            if node.meta.get("role") == "specialization_request_leg"
            and node.state == NodeState.CONFIRMED
        ))
        eligible_by_parent = {
            parent_id: tuple(sorted(
                base_id for candidate_parent, base_id, node_id in candidate_pairs
                if candidate_parent == parent_id
                and runtime.nodes[node_id].state == NodeState.CONFIRMED
            ))
            for parent_id in request_parents
        }
        return {
            "confirmed_cell_ids": confirmed,
            "root_state": runtime.nodes[CORRECTION_ROOT_ID].state.name,
            "leg_states": leg_states,
            "specialization_request_parent_ids": request_parents,
            "eligible_terminal_ids_by_parent": eligible_by_parent,
        }

    def _eligible_specialization_pairs(
        self,
        record: CompetenceEvidenceRecord,
        *,
        mode: SpecializationMode,
    ) -> set[tuple[str, str]]:
        if mode is SpecializationMode.DISCONNECTED:
            return set()
        pairs: set[tuple[str, str]] = set()
        for parent in self.cells.values():
            if (
                not parent.is_mature
                or parent.polarity not in {
                    AvailabilityState.AVAILABLE,
                    AvailabilityState.REFUTED,
                }
                or parent.specialization_depth != 0
                or parent.specialization_request_ordinal is not None
            ):
                continue
            for base_id in self._supporting_base_vocabulary(parent):
                if (
                    mode is SpecializationMode.LOCAL_CONTRAST
                    and base_id in record.active_signal_ids
                ):
                    continue
                pairs.add((parent.cell_id, base_id))
        return pairs

    def _supporting_base_vocabulary(
        self, parent: CompetenceContextCell
    ) -> tuple[str, ...]:
        counts: dict[str, int] = {}
        for evidence in self.evidence.values():
            if not self._cell_pattern_matches(parent, evidence, set()):
                continue
            supports = (
                evidence.observed_completion
                if parent.polarity == AvailabilityState.AVAILABLE
                else not evidence.observed_completion
            )
            if not supports:
                continue
            for identity in set(evidence.active_signal_ids):
                if self._specialization_member_forbidden(identity):
                    continue
                counts[identity] = counts.get(identity, 0) + 1
        implied = self._implied_base_members(parent, set())
        return tuple(sorted(
            identity for identity, count in counts.items()
            if count >= self.config.min_maturity_support
            and identity not in implied
        ))

    @staticmethod
    def _specialization_member_forbidden(identity: str) -> bool:
        lowered = str(identity).lower()
        forbidden = (
            "policy_response", "completion", "outcome", "experiment",
            "row", "identity", "fen", "mate", "checkmate", "stalemate",
            "rook_loss", "correct_move", "tablebase", "stockfish",
        )
        return any(token in lowered for token in forbidden)

    def _implied_base_members(
        self, cell: CompetenceContextCell, visiting: set[str]
    ) -> set[str]:
        if cell.cell_id in visiting:
            raise RuntimeError("cyclic competence context")
        nested_visiting = set(visiting)
        nested_visiting.add(cell.cell_id)
        implied: set[str] = set()
        for member in cell.members:
            if member.startswith("context:"):
                parent = self.cells.get(member.split(":", 1)[1])
                if parent is not None:
                    implied.update(self._implied_base_members(parent, nested_visiting))
            else:
                implied.add(member)
        return implied

    def _attach_specialization_candidate_terminals(
        self, runtime: Graph
    ) -> tuple[tuple[str, str, str], ...]:
        attached: list[tuple[str, str, str]] = []
        for parent in sorted(self.cells.values(), key=lambda item: item.cell_id):
            if (
                not parent.is_mature
                or parent.specialization_depth != 0
                or parent.specialization_request_ordinal is not None
            ):
                continue
            for base_id in self._supporting_base_vocabulary(parent):
                token = hashlib.sha256(
                    f"{parent.cell_id}|{base_id}".encode("utf-8")
                ).hexdigest()[:16]
                node_id = f"specialization_eligible:{token}"
                runtime.add_node(Node(
                    node_id,
                    NodeType.TERMINAL,
                    predicate=_specialization_eligibility_terminal,
                    meta={
                        "terminal_kind": "SPECIALIZATION_ELIGIBILITY",
                        "role": "specialization_eligible_terminal",
                        "parent_cell_id": parent.cell_id,
                        "base_identity": base_id,
                    },
                ))
                runtime.add_hierarchy_pair(
                    SPECIALIZATION_ELIGIBILITY_ROOT_ID, node_id
                )
                attached.append((parent.cell_id, base_id, node_id))
        return tuple(attached)

    def _materialize_specialization(
        self,
        *,
        parent: CompetenceContextCell,
        proposal: GrowthProposal | None,
        proposal_ordinal: int,
        mode: SpecializationMode,
        eligible_terminal_ids: Sequence[str],
        evidence_key: str,
    ) -> CompetenceContextCell | None:
        row: dict[str, Any] = {
            "evidence_key": evidence_key,
            "parent_cell_id": parent.cell_id,
            "parent_polarity": parent.polarity.value,
            "mode": mode.value,
            "request_ordinal": parent.specialization_request_ordinal,
            "proposal_ordinal": proposal_ordinal,
            "eligible_count": len(eligible_terminal_ids),
            "admitted": False,
            "reason": None,
        }
        if proposal is None:
            self.specialization_audit.empty_eligibility_rejections += 1
            row["reason"] = "empty_eligibility"
            self.specialization_audit.request_rows.append(row)
            return None
        members = tuple(proposal.members)
        row["members"] = list(members)
        expected_context = f"context:{parent.cell_id}"
        if (
            len(members) != 2
            or members[0] != expected_context
            or members[1] not in set(eligible_terminal_ids)
        ):
            raise RuntimeError("specialization genome emitted an ineligible child")
        if members in self._member_specs:
            self.specialization_audit.duplicate_rejections += 1
            row["reason"] = "duplicate"
            self.specialization_audit.request_rows.append(row)
            return None
        live = sum(
            cell.state != StemCellState.PRUNED for cell in self.cells.values()
        )
        if live >= self.config.trial_capacity:
            self.specialization_audit.capacity_rejections += 1
            row["reason"] = "trial_capacity"
            self.specialization_audit.request_rows.append(row)
            return None
        cell_id = f"competence_context_{self._next_cell_index:04d}"
        self._next_cell_index += 1
        stem = StemCellTerminal(cell_id)
        stem.state = StemCellState.TRIAL
        stem.trial_node_id = cell_id
        stem.trial_parent_id = SHADOW_ROOT_ID
        stem.depth = parent.stem_cell.depth + 1
        stem.children = list(members)
        stem.is_composition = True
        stem.metadata.update({
            "origin": "contradiction_triggered_one_level_specialization",
            "member_identities": list(members),
            "lineage_parent_id": parent.cell_id,
            "specialization_depth": 1,
            "specialization_request_ordinal": parent.specialization_request_ordinal,
            "specialization_proposal_ordinal": proposal_ordinal,
            "shadow_only": True,
        })
        cell = CompetenceContextCell(
            cell_id=cell_id,
            members=members,
            born_round=2,
            born_request_ordinal=int(parent.specialization_request_ordinal),
            stem_cell=stem,
            polarity=parent.polarity,
            lineage_parent_id=parent.cell_id,
            specialization_depth=1,
            specialization_request_ordinal=parent.specialization_request_ordinal,
            specialization_proposal_ordinal=proposal_ordinal,
        )
        self.cells[cell_id] = cell
        self._member_specs.add(members)
        self.specialization_audit.admitted_proposals += 1
        row.update({"admitted": True, "cell_id": cell_id})
        self.specialization_audit.request_rows.append(row)
        return cell

    def _refresh_cell_evidence(self, cell: CompetenceContextCell) -> None:
        matched = tuple(
            record for record in self.evidence.values()
            if self._cell_pattern_matches(cell, record, set())
        )
        successes = sum(record.observed_completion for record in matched)
        failures = len(matched) - successes
        cell.evidence_keys = tuple(sorted(record.evidence_key for record in matched))
        cell.successes = int(successes)
        cell.failures = int(failures)
        cell.support = len(matched)
        cell.success_lower_bound = wilson_lower_bound(
            successes, len(matched), self.config.wilson_z
        )
        cell.failure_lower_bound = wilson_lower_bound(
            failures, len(matched), self.config.wilson_z
        )
        cell.conservative_success_estimate = cell.success_lower_bound
        cell.uncertainty = 1.0 - max(
            cell.success_lower_bound, cell.failure_lower_bound
        )
        stats = cell.stem_cell.candidate_stats
        stats.relevance_stats.request_exposures = len(self.evidence)
        stats.relevance_stats.activation_count = len(matched)
        stats.relevance_stats.confirm_count = successes
        stats.credit_stats.positive_correlation = successes
        stats.credit_stats.negative_correlation = failures
        stats.recompute_survival()

    def classify(
        self,
        active_signal_ids: Iterable[str],
        *,
        policy_response: bool,
    ) -> EnvelopeClassification:
        signals = frozenset(map(str, active_signal_ids))
        runtime = copy.deepcopy(self.graph)
        engine = FormalReConEngine(runtime, record_trace=False)
        engine.request(AVAILABLE_ROOT_ID)
        engine.request(REFUTED_ROOT_ID)
        engine.run(
            max_ticks=96,
            env={
                "active_signal_ids": signals,
                "policy_response": bool(policy_response),
            },
            until=lambda item: all(
                item.g.nodes[root].state
                in {NodeState.CONFIRMED, NodeState.FAILED}
                for root in (AVAILABLE_ROOT_ID, REFUTED_ROOT_ID)
            ),
        )
        formal_available = (
            runtime.nodes[AVAILABLE_ROOT_ID].state == NodeState.CONFIRMED
        )
        formal_refuted = (
            runtime.nodes[REFUTED_ROOT_ID].state == NodeState.CONFIRMED
        )
        available_ids = tuple(sorted(
            str(node.meta["cell_id"])
            for node in runtime.nodes.values()
            if node.meta.get("role") == "available_context_root"
            and node.state == NodeState.CONFIRMED
        ))
        refuted_ids = tuple(sorted(
            str(node.meta["cell_id"])
            for node in runtime.nodes.values()
            if node.meta.get("role") == "refuted_context_root"
            and node.state == NodeState.CONFIRMED
        ))
        if formal_available and not formal_refuted:
            state = AvailabilityState.AVAILABLE
            probability = max(
                (self.cells[cell_id].success_lower_bound for cell_id in available_ids),
                default=0.5,
            )
            uncertainty = max(
                (self.cells[cell_id].uncertainty for cell_id in available_ids),
                default=1.0,
            )
        elif formal_refuted and not formal_available:
            state = AvailabilityState.REFUTED
            probability = 0.0
            uncertainty = max(
                (self.cells[cell_id].uncertainty for cell_id in refuted_ids),
                default=1.0,
            )
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

    def emit_growth_request(
        self,
        *,
        observed_completion: bool,
        classification: EnvelopeClassification,
    ) -> GrowthRequestEmission:
        runtime = copy.deepcopy(self.graph)
        engine = FormalReConEngine(runtime, record_trace=False)
        engine.request(GROWTH_REQUEST_ROOT_ID)
        engine.run(
            max_ticks=16,
            env={
                "observed_completion": bool(observed_completion),
                "predicted_availability": classification.predicted_availability,
            },
            until=lambda item: item.g.nodes[GROWTH_REQUEST_ROOT_ID].state
            in {NodeState.CONFIRMED, NodeState.FAILED},
        )
        terminal = runtime.nodes[AVAILABILITY_ERROR_ID]
        error = float(terminal.activation.value)
        return GrowthRequestEmission(
            emitted=runtime.nodes[GROWTH_REQUEST_ROOT_ID].state
            == NodeState.CONFIRMED,
            availability_error=error,
            root_state=runtime.nodes[GROWTH_REQUEST_ROOT_ID].state.name,
            terminal_state=terminal.state.name,
        )

    def grow(
        self,
        records: Sequence[CompetenceEvidenceRecord],
        *,
        genome: CompetenceContextGrowthGenome | None = None,
    ) -> GrowthAudit:
        growth_genome = genome or CompetenceContextGrowthGenome(
            self.config.selection_seed
        )
        for record in records:
            self.add_unique_evidence(record)
        for round_index in range(self.config.structural_rounds):
            for request_ordinal, record in enumerate(records):
                self.audit.request_opportunities += 1
                classification = self.classify(
                    record.active_signal_ids,
                    policy_response=record.policy_response,
                )
                emission = self.emit_growth_request(
                    observed_completion=record.observed_completion,
                    classification=classification,
                )
                if not emission.emitted:
                    continue
                self.audit.graph_request_emissions += 1
                if self.audit.proposal_attempts >= self.config.proposal_attempt_cap:
                    self.audit.capacity_rejections += 1
                    continue
                self.audit.proposal_attempts += 1
                active_contexts = tuple(
                    cell.cell_id
                    for cell in self.cells.values()
                    if cell.is_mature and self._cell_matches(cell, record, set())
                )
                proposal = growth_genome.propose(
                    active_base_ids=record.active_signal_ids,
                    active_mature_context_ids=active_contexts,
                    round_index=round_index,
                    request_ordinal=request_ordinal,
                )
                if proposal is None:
                    self.audit.insufficient_member_rejections += 1
                    continue
                self._materialize_proposal(proposal, emission)
            self._review_lifecycle(
                final=round_index == self.config.structural_rounds - 1
            )
            self.rebuild_graph()
        return self.audit

    def _materialize_proposal(
        self,
        proposal: GrowthProposal,
        emission: GrowthRequestEmission,
    ) -> CompetenceContextCell | None:
        members = tuple(proposal.members)
        row = {
            "round_index": proposal.round_index,
            "request_ordinal": proposal.request_ordinal,
            "members": list(members),
            "genome_seed": proposal.genome_seed,
            "availability_error": emission.availability_error,
            "graph_request_state": emission.root_state,
            "admitted": False,
            "reason": None,
        }
        if members in self._member_specs:
            self.audit.duplicate_rejections += 1
            row["reason"] = "duplicate"
            self.audit.proposal_rows.append(row)
            return None
        live = sum(
            cell.state != StemCellState.PRUNED for cell in self.cells.values()
        )
        if live >= self.config.trial_capacity:
            self.audit.capacity_rejections += 1
            row["reason"] = "trial_capacity"
            self.audit.proposal_rows.append(row)
            return None
        cell_id = f"competence_context_{self._next_cell_index:04d}"
        self._next_cell_index += 1
        stem = StemCellTerminal(cell_id)
        stem.state = StemCellState.TRIAL
        stem.trial_node_id = cell_id
        stem.trial_parent_id = SHADOW_ROOT_ID
        stem.depth = max(
            (self._member_depth(member) for member in members),
            default=0,
        )
        stem.children = list(members)
        stem.is_composition = len(members) > 1 or any(
            member.startswith("context:") for member in members
        )
        stem.metadata.update({
            "origin": "graph_native_competence_envelope",
            "member_identities": list(members),
            "born_round": proposal.round_index,
            "born_request_ordinal": proposal.request_ordinal,
            "shadow_only": True,
        })
        cell = CompetenceContextCell(
            cell_id=cell_id,
            members=members,
            born_round=proposal.round_index,
            born_request_ordinal=proposal.request_ordinal,
            stem_cell=stem,
        )
        self.cells[cell_id] = cell
        self._member_specs.add(members)
        self.audit.admitted_proposals += 1
        row.update({"admitted": True, "cell_id": cell_id})
        self.audit.proposal_rows.append(row)
        return cell

    def _member_depth(self, member: str) -> int:
        if not member.startswith("context:"):
            return 0
        parent = self.cells.get(member.split(":", 1)[1])
        return 1 if parent is None else parent.stem_cell.depth + 1

    def _review_lifecycle(self, *, final: bool) -> None:
        self._review_count += 1
        positive_count = sum(
            cell.is_mature and cell.polarity == AvailabilityState.AVAILABLE
            for cell in self.cells.values()
        )
        refuted_count = sum(
            cell.is_mature and cell.polarity == AvailabilityState.REFUTED
            for cell in self.cells.values()
        )
        review_rows = []
        records = tuple(self.evidence.values())
        for cell in self.cells.values():
            if not cell.is_trial:
                continue
            matched = tuple(
                record for record in records
                if self._cell_matches(cell, record, set())
            )
            successes = sum(record.observed_completion for record in matched)
            failures = len(matched) - successes
            success_lower = wilson_lower_bound(
                successes, len(matched), self.config.wilson_z
            )
            failure_lower = wilson_lower_bound(
                failures, len(matched), self.config.wilson_z
            )
            cell.evidence_keys = tuple(sorted(
                record.evidence_key for record in matched
            ))
            cell.successes = int(successes)
            cell.failures = int(failures)
            cell.support = len(matched)
            cell.success_lower_bound = success_lower
            cell.failure_lower_bound = failure_lower
            cell.conservative_success_estimate = success_lower
            cell.uncertainty = 1.0 - max(success_lower, failure_lower)
            stats = cell.stem_cell.candidate_stats
            stats.relevance_stats.request_exposures = len(records)
            stats.relevance_stats.activation_count = len(matched)
            stats.relevance_stats.confirm_count = successes
            stats.credit_stats.positive_correlation = successes
            stats.credit_stats.negative_correlation = failures
            stats.recompute_survival()
            positive = (
                cell.lineage_parent_id is None
                or cell.polarity == AvailabilityState.AVAILABLE
            ) and (

                len(matched) >= self.config.min_maturity_support
                and failures == 0
                and success_lower >= self.config.lower_bound_threshold
            )
            refuted = (
                cell.lineage_parent_id is None
                or cell.polarity == AvailabilityState.REFUTED
            ) and (

                len(matched) >= self.config.min_maturity_support
                and successes == 0
                and failure_lower >= self.config.lower_bound_threshold
            )
            if positive and positive_count < self.config.positive_capacity:
                cell.polarity = AvailabilityState.AVAILABLE
                cell.stem_cell.state = StemCellState.MATURE
                cell.stem_cell.trial_parent_id = AVAILABLE_ROOT_ID
                cell.stem_cell.metadata["shadow_only"] = False
                cell.maturity_review = self._review_count
                positive_count += 1
            elif refuted and refuted_count < self.config.refuted_capacity:
                cell.polarity = AvailabilityState.REFUTED
                cell.stem_cell.state = StemCellState.MATURE
                cell.stem_cell.trial_parent_id = REFUTED_ROOT_ID
                cell.stem_cell.metadata["shadow_only"] = False
                cell.maturity_review = self._review_count
                refuted_count += 1
            elif final:
                cell.stem_cell.state = StemCellState.PRUNED
                if len(matched) < self.config.min_maturity_support:
                    cell.prune_reason = "insufficient_support"
                elif successes and failures:
                    cell.prune_reason = "mixed_outcomes"
                else:
                    cell.prune_reason = "lower_bound_or_capacity"
            review_rows.append(cell.to_manifest())
        self.audit.lifecycle_reviews.append({
            "review_index": self._review_count,
            "final": bool(final),
            "positive_mature": positive_count,
            "refuted_mature": refuted_count,
            "cells": review_rows,
        })

    def _cell_matches(
        self,
        cell: CompetenceContextCell,
        record: CompetenceEvidenceRecord,
        visiting: set[str],
    ) -> bool:
        if cell.cell_id in visiting:
            raise RuntimeError("cyclic competence context")
        next_visiting = set(visiting)
        next_visiting.add(cell.cell_id)
        active = set(record.active_signal_ids)
        for member in cell.members:
            if member.startswith("context:"):
                parent_id = member.split(":", 1)[1]
                parent = self.cells.get(parent_id)
                if parent is None:
                    return False
                parent_usable = parent.is_mature or (
                    cell.lineage_parent_id == parent_id
                    and parent.state == StemCellState.PROBATION
                )
                if not parent_usable:
                    return False
                if not self._cell_matches(parent, record, next_visiting):
                    return False
            elif member not in active:
                return False
        return True

    def _cell_pattern_matches(
        self,
        cell: CompetenceContextCell,
        record: CompetenceEvidenceRecord,
        visiting: set[str],
    ) -> bool:
        """Match retained pattern identity without requiring current authority."""

        if cell.cell_id in visiting:
            raise RuntimeError("cyclic competence context")
        next_visiting = set(visiting)
        next_visiting.add(cell.cell_id)
        active = set(record.active_signal_ids)
        for member in cell.members:
            if member.startswith("context:"):
                parent = self.cells.get(member.split(":", 1)[1])
                if parent is None or parent.state == StemCellState.PRUNED:
                    return False
                if not self._cell_pattern_matches(parent, record, next_visiting):
                    return False
            elif member not in active:
                return False
        return True

    def rebuild_graph(self) -> None:
        graph = Graph()
        graph.add_node(Node(
            AVAILABLE_ROOT_ID,
            NodeType.SCRIPT,
            meta={"confirm_policy": "and", "role": "AVAILABLE"},
        ))
        graph.add_node(Node(
            "competence_policy_response_available",
            NodeType.TERMINAL,
            predicate=_policy_response_terminal,
            meta={"terminal_kind": "POLICY_RESPONSE"},
        ))
        graph.add_node(Node(
            "competence_positive_or",
            NodeType.SCRIPT,
            meta={"confirm_policy": "or", "role": "positive_context_or"},
        ))
        graph.add_hierarchy_pair(
            AVAILABLE_ROOT_ID, "competence_policy_response_available"
        )
        graph.add_hierarchy_pair(AVAILABLE_ROOT_ID, "competence_positive_or")

        graph.add_node(Node(
            REFUTED_ROOT_ID,
            NodeType.SCRIPT,
            meta={"confirm_policy": "and", "role": "REFUTED"},
        ))
        graph.add_node(Node(
            "competence_policy_response_refuted",
            NodeType.TERMINAL,
            predicate=_policy_response_terminal,
            meta={"terminal_kind": "POLICY_RESPONSE"},
        ))
        graph.add_node(Node(
            "competence_refuted_or",
            NodeType.SCRIPT,
            meta={"confirm_policy": "or", "role": "refuted_context_or"},
        ))
        graph.add_hierarchy_pair(
            REFUTED_ROOT_ID, "competence_policy_response_refuted"
        )
        graph.add_hierarchy_pair(REFUTED_ROOT_ID, "competence_refuted_or")

        graph.add_node(Node(
            SHADOW_ROOT_ID,
            NodeType.SCRIPT,
            meta={"confirm_policy": "or", "role": "shadow_only_trials"},
        ))
        graph.add_node(Node(
            GROWTH_REQUEST_ROOT_ID,
            NodeType.SCRIPT,
            meta={"confirm_policy": "and", "role": "growth_request"},
        ))
        graph.add_node(Node(
            AVAILABILITY_ERROR_ID,
            NodeType.TERMINAL,
            predicate=_availability_error_terminal,
            meta={
                "terminal_kind": "AVAILABILITY_ERROR",
                "distinct_from_value_residual": True,
            },
        ))
        graph.add_hierarchy_pair(GROWTH_REQUEST_ROOT_ID, AVAILABILITY_ERROR_ID)
        graph.add_node(Node(
            CORRECTION_ROOT_ID,
            NodeType.SCRIPT,
            meta={"confirm_policy": "or", "role": "mature_correction"},
        ))

        graph.add_node(Node(
            SPECIALIZATION_REQUEST_ROOT_ID,
            NodeType.SCRIPT,
            meta={"confirm_policy": "or", "role": "specialization_request"},
        ))
        graph.add_node(Node(
            SPECIALIZATION_ELIGIBILITY_ROOT_ID,
            NodeType.SCRIPT,
            meta={"confirm_policy": "or", "role": "specialization_eligibility"},
        ))
        self._add_false_child(
            graph, SPECIALIZATION_ELIGIBILITY_ROOT_ID, "dynamic_default"
        )

        positive = [
            cell for cell in self.cells.values()
            if cell.is_mature and cell.polarity == AvailabilityState.AVAILABLE
        ]
        refuted = [
            cell for cell in self.cells.values()
            if cell.is_mature and cell.polarity == AvailabilityState.REFUTED
        ]
        trials = [cell for cell in self.cells.values() if cell.is_trial]
        correction_cells = [
            cell for cell in self.cells.values()
            if cell.state in {StemCellState.MATURE, StemCellState.PROBATION}
            and cell.polarity in {
                AvailabilityState.AVAILABLE,
                AvailabilityState.REFUTED,
            }
        ]
        if positive:
            for index, cell in enumerate(positive):
                self._add_cell_subtree(
                    graph,
                    "competence_positive_or",
                    cell,
                    prefix=f"available_{index}",
                    top_role="available_context_root",
                    visiting=set(),
                )
        else:
            self._add_false_child(graph, "competence_positive_or", "no_positive")
        if refuted:
            for index, cell in enumerate(refuted):
                self._add_cell_subtree(
                    graph,
                    "competence_refuted_or",
                    cell,
                    prefix=f"refuted_{index}",
                    top_role="refuted_context_root",
                    visiting=set(),
                )
        else:
            self._add_false_child(graph, "competence_refuted_or", "no_refuted")
        if trials:
            for index, cell in enumerate(trials):
                self._add_cell_subtree(
                    graph,
                    SHADOW_ROOT_ID,
                    cell,
                    prefix=f"shadow_{index}",
                    top_role="shadow_context_root",
                    visiting=set(),
                )
        else:
            self._add_false_child(graph, SHADOW_ROOT_ID, "no_trials")
        specialization_request_count = 0

        if correction_cells:
            for index, cell in enumerate(correction_cells):
                leg_id = f"correction_{index}:{cell.cell_id}"
                graph.add_node(Node(
                    leg_id,
                    NodeType.SCRIPT,
                    meta={
                        "confirm_policy": "and",
                        "role": "mature_correction_leg",
                        "cell_id": cell.cell_id,
                        "polarity": cell.polarity.value,
                    },
                ))
                graph.add_hierarchy_pair(CORRECTION_ROOT_ID, leg_id)
                self._add_cell_subtree(
                    graph,
                    leg_id,
                    cell,
                    prefix=f"correction_{index}:context",
                    top_role="correction_context_root",
                    visiting=set(),
                    require_mature_nested=False,
                )
                error_id = f"correction_{index}:prediction_error"
                graph.add_node(Node(
                    error_id,
                    NodeType.TERMINAL,
                    predicate=_cell_prediction_error_terminal,
                    meta={
                        "terminal_kind": "CELL_LOCAL_PREDICTION_ERROR",
                        "cell_id": cell.cell_id,
                        "polarity": cell.polarity.value,
                    },
                ))
                graph.add_hierarchy_pair(leg_id, error_id)
                if (
                    cell.is_mature
                    and cell.specialization_depth == 0
                    and cell.specialization_request_ordinal is None
                ):
                    request_index = specialization_request_count
                    specialization_request_count += 1
                    request_leg_id = (
                        f"specialization_request_{request_index}:{cell.cell_id}"
                    )
                    graph.add_node(Node(
                        request_leg_id,
                        NodeType.SCRIPT,
                        meta={
                            "confirm_policy": "and",
                            "role": "specialization_request_leg",
                            "cell_id": cell.cell_id,
                            "polarity": cell.polarity.value,
                        },
                    ))
                    graph.add_hierarchy_pair(
                        SPECIALIZATION_REQUEST_ROOT_ID, request_leg_id
                    )
                    self._add_cell_subtree(
                        graph,
                        request_leg_id,
                        cell,
                        prefix=f"specialization_request_{request_index}:context",
                        top_role="specialization_request_context",
                        visiting=set(),
                        require_mature_nested=False,
                    )
                    request_error_id = (
                        f"specialization_request_{request_index}:prediction_error"
                    )
                    graph.add_node(Node(
                        request_error_id,
                        NodeType.TERMINAL,
                        predicate=_cell_prediction_error_terminal,
                        meta={
                            "terminal_kind": "CELL_LOCAL_PREDICTION_ERROR",
                            "cell_id": cell.cell_id,
                            "polarity": cell.polarity.value,
                        },
                    ))
                    graph.add_hierarchy_pair(request_leg_id, request_error_id)

        else:
            self._add_false_child(
                graph, CORRECTION_ROOT_ID, "no_correctable_cells"
            )
        if specialization_request_count == 0:
            self._add_false_child(
                graph, SPECIALIZATION_REQUEST_ROOT_ID, "no_requestable_parents"
            )

        self.graph = graph

    def _add_cell_subtree(
        self,
        graph: Graph,
        parent_id: str,
        cell: CompetenceContextCell,
        *,
        prefix: str,
        top_role: str,
        visiting: set[str],
        require_mature_nested: bool = True,
    ) -> str:
        if cell.cell_id in visiting:
            raise RuntimeError("cyclic competence context topology")
        next_visiting = set(visiting)
        next_visiting.add(cell.cell_id)
        node_id = f"{prefix}:{cell.cell_id}"
        graph.add_node(Node(
            node_id,
            NodeType.SCRIPT,
            meta={
                "confirm_policy": "and",
                "role": top_role,
                "cell_id": cell.cell_id,
                "polarity": (
                    None if cell.polarity is None else cell.polarity.value
                ),
                "stem_cell_state": cell.state.name,
                "support": cell.support,
                "success_lower_bound": cell.success_lower_bound,
                "failure_lower_bound": cell.failure_lower_bound,
            },
        ))
        graph.add_hierarchy_pair(parent_id, node_id)
        for member_index, member in enumerate(cell.members):
            if member.startswith("context:"):
                nested_id = member.split(":", 1)[1]
                nested = self.cells.get(nested_id)
                nested_allowed = bool(
                    nested is not None
                    and (
                        nested.is_mature
                        or (
                            cell.lineage_parent_id == nested_id
                            and nested.state == StemCellState.PROBATION
                        )
                        or (
                            not require_mature_nested
                            and nested.state == StemCellState.PROBATION
                        )
                    )
                )
                if not nested_allowed:
                    self._add_false_child(
                        graph, node_id, f"{prefix}_missing_{member_index}"
                    )
                else:
                    self._add_cell_subtree(
                        graph,
                        node_id,
                        nested,
                        prefix=f"{prefix}:nested_{member_index}",
                        top_role="nested_context",
                        visiting=next_visiting,
                        require_mature_nested=require_mature_nested,
                    )
            else:
                terminal_id = f"{prefix}:member_{member_index}"
                graph.add_node(Node(
                    terminal_id,
                    NodeType.TERMINAL,
                    predicate=_active_signal_terminal,
                    meta={
                        "terminal_kind": "CONTEXT_MEMBER",
                        "member_identity": member,
                    },
                ))
                graph.add_hierarchy_pair(node_id, terminal_id)
        return node_id

    @staticmethod
    def _add_false_child(graph: Graph, parent_id: str, suffix: str) -> None:
        node_id = f"{parent_id}:{suffix}:false"
        graph.add_node(Node(
            node_id,
            NodeType.TERMINAL,
            predicate=_false_terminal,
            meta={"terminal_kind": "EMPTY_CONTEXT"},
        ))
        graph.add_hierarchy_pair(parent_id, node_id)

    def continuation_manifest_v2(self) -> dict[str, Any]:
        """Exhaustive deterministic state for exact scientific continuation."""

        cells = []
        for cell in sorted(self.cells.values(), key=lambda item: item.cell_id):
            cells.append({
                **cell.to_manifest(),
                "lineage_parent_id": cell.lineage_parent_id,
                "specialization_depth": cell.specialization_depth,
                "specialization_request_ordinal": (
                    cell.specialization_request_ordinal
                ),
                "specialization_proposal_ordinal": (
                    cell.specialization_proposal_ordinal
                ),
            })
        evidence = [
            {
                "evidence_key": record.evidence_key,
                "active_signal_ids": list(record.active_signal_ids),
                "policy_response": record.policy_response,
                "observed_completion": record.observed_completion,
                "actuator_identity": record.actuator_identity,
                "completion_terminal_identity": (
                    record.completion_terminal_identity
                ),
            }
            for record in sorted(
                self.evidence.values(), key=lambda item: item.evidence_key
            )
        ]
        return {
            "schema_version": "continuation_manifest.v2",
            "organism_schema_version": self.schema_version,
            "config": {
                key: getattr(self.config, key)
                for key in self.config.__dataclass_fields__
            },
            "evidence_records": evidence,
            "cells": cells,
            "member_specs": [
                list(item) for item in sorted(self._member_specs)
            ],
            "continuation_counters": {
                "next_cell_index": self._next_cell_index,
                "review_count": self._review_count,
                "specialization_request_ordinal": (
                    self._specialization_request_ordinal
                ),
                "specialization_proposal_ordinal": (
                    self._specialization_proposal_ordinal
                ),
            },
            "growth_audit": {
                "request_opportunities": self.audit.request_opportunities,
                "graph_request_emissions": self.audit.graph_request_emissions,
                "proposal_attempts": self.audit.proposal_attempts,
                "admitted_proposals": self.audit.admitted_proposals,
                "duplicate_rejections": self.audit.duplicate_rejections,
                "capacity_rejections": self.audit.capacity_rejections,
                "insufficient_member_rejections": (
                    self.audit.insufficient_member_rejections
                ),
                "proposal_rows": copy.deepcopy(self.audit.proposal_rows),
                "lifecycle_reviews": copy.deepcopy(
                    self.audit.lifecycle_reviews
                ),
            },
            "correction_audit": {
                "unique_real_observations": (
                    self.correction_audit.unique_real_observations
                ),
                "duplicate_observations": (
                    self.correction_audit.duplicate_observations
                ),
                "contradiction_hits": self.correction_audit.contradiction_hits,
                "mature_to_probation_transitions": (
                    self.correction_audit.mature_to_probation_transitions
                ),
                "query_rows": copy.deepcopy(
                    self.correction_audit.query_rows
                ),
            },
            "specialization_audit": {
                "request_opportunities": (
                    self.specialization_audit.request_opportunities
                ),
                "graph_request_emissions": (
                    self.specialization_audit.graph_request_emissions
                ),
                "proposal_attempts": (
                    self.specialization_audit.proposal_attempts
                ),
                "admitted_proposals": (
                    self.specialization_audit.admitted_proposals
                ),
                "empty_eligibility_rejections": (
                    self.specialization_audit.empty_eligibility_rejections
                ),
                "duplicate_rejections": (
                    self.specialization_audit.duplicate_rejections
                ),
                "capacity_rejections": (
                    self.specialization_audit.capacity_rejections
                ),
                "request_rows": copy.deepcopy(
                    self.specialization_audit.request_rows
                ),
            },
            "graph_snapshot": self.graph.to_snapshot(),
        }

    def continuation_digest_v2(self) -> str:
        payload = json.dumps(
            self.continuation_manifest_v2(),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


    def to_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "config": {
                key: getattr(self.config, key)
                for key in self.config.__dataclass_fields__
            },
            "cells": [
                cell.to_manifest()
                for cell in sorted(
                    self.cells.values(), key=lambda item: item.cell_id
                )
            ],
            "evidence_keys": sorted(self.evidence),
            "evidence_count": len(self.evidence),
            "audit": {
                "request_opportunities": self.audit.request_opportunities,
                "graph_request_emissions": self.audit.graph_request_emissions,
                "proposal_attempts": self.audit.proposal_attempts,
                "admitted_proposals": self.audit.admitted_proposals,
                "duplicate_rejections": self.audit.duplicate_rejections,
                "capacity_rejections": self.audit.capacity_rejections,
                "insufficient_member_rejections": (
                    self.audit.insufficient_member_rejections
                ),
                "proposal_rows": list(self.audit.proposal_rows),
                "lifecycle_reviews": list(self.audit.lifecycle_reviews),
            },
            "correction_audit": {
                "unique_real_observations": (
                    self.correction_audit.unique_real_observations
                ),
                "duplicate_observations": (
                    self.correction_audit.duplicate_observations
                ),
                "contradiction_hits": self.correction_audit.contradiction_hits,
                "mature_to_probation_transitions": (
                    self.correction_audit.mature_to_probation_transitions
                ),
                "query_rows": list(self.correction_audit.query_rows),
            },
            "graph_snapshot": self.graph.to_snapshot(),
        }


@dataclass
class NativeR0CompetenceOrganism:
    r0: NativeR0Organism
    envelope: GraphNativeCompetenceEnvelope
    schema_version: str = "native_r0_with_competence_envelope.v1"

    def __post_init__(self) -> None:
        if self.r0.retrieval_budget_per_actuator != self.envelope.config.retrieval_budget:
            raise ValueError("R0 retrieval budget differs from frozen envelope budget")

    def classify_board(
        self,
        board: chess.Board,
        actuation: GraphActuation | None,
    ) -> EnvelopeClassification:
        signals = extract_active_competence_signals(self.r0, board, actuation)
        return self.envelope.classify(
            signals,
            policy_response=actuation is not None,
        )

    def apply_to_query(
        self,
        query: ChildQuery,
        classification: EnvelopeClassification,
        *,
        active_signal_ids: Iterable[str],
    ) -> ChildQuery:
        """Adapt an envelope-owned classification; never accept a host Boolean."""

        if not isinstance(classification, EnvelopeClassification):
            raise TypeError("competence adapter requires EnvelopeClassification")
        available = classification.state == AvailabilityState.AVAILABLE
        policy_response = bool(
            query.actuation is not None or query.response.policy_response
        )
        grounded = bool(
            self.r0.provenance.grounded and self.r0.provenance.can_emit
        )
        response = ChildResponse(
            child_id=self.r0.provenance.child_id,
            confirmed=available,
            policy_response=policy_response,
            available=available,
            expected_value=(
                self.r0.provenance.consolidated_value if available else 0.0
            ),
            uncertainty=classification.uncertainty,
            grounded=grounded,
            grounding_source=(
                self.r0.provenance.grounding_source if grounded else None
            ),
        )
        provenance = {
            "classification": classification.to_manifest(),
            "envelope_schema_version": self.envelope.schema_version,
            "child_id": self.r0.provenance.child_id,
            "child_mature": self.r0.provenance.mature,
            "child_grounded": self.r0.provenance.grounded,
            "child_grounding_source": self.r0.provenance.grounding_source,
        }
        return ChildQuery(
            response=response,
            actuation=query.actuation,
            frame_id=query.frame_id,
            persistent_mutation_count=query.persistent_mutation_count,
            effect_attempts=query.effect_attempts,
            active_competence_signal_ids=tuple(sorted(map(str, active_signal_ids))),
            availability_provenance=provenance,
        )

    def persistent_state_audit(self) -> Mapping[str, str]:
        r0_audit = dict(self.r0.persistent_state_audit())
        envelope_exact = hashlib.sha256(
            pickle.dumps(
                copy.deepcopy(self.envelope),
                protocol=pickle.HIGHEST_PROTOCOL,
            )
        ).hexdigest()
        combined = hashlib.sha256(
            pickle.dumps(
                (r0_audit, envelope_exact, self.schema_version),
                protocol=pickle.HIGHEST_PROTOCOL,
            )
        ).hexdigest()
        return {
            **{f"r0_{key}": value for key, value in r0_audit.items()},
            "envelope_exact_state_sha256": envelope_exact,
            "exact_state_sha256": combined,
            "serialized_state_sha256": hashlib.sha256(
                self.dumps()
            ).hexdigest(),
        }

    def dream_session(
        self,
        *,
        audit: NativeCompetenceSessionAudit | None = None,
    ) -> "NativeCompetenceDreamSession":
        return NativeCompetenceDreamSession(self, audit=audit)

    def dumps(self) -> bytes:
        return pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def loads(cls, payload: bytes) -> "NativeR0CompetenceOrganism":
        item = pickle.loads(payload)
        if not isinstance(item, cls):
            raise TypeError("serialized competence organism has wrong type")
        return item


class NativeCompetenceDreamSession:
    """Read-only virtual child requests with graph-native local availability."""

    def __init__(
        self,
        organism: NativeR0CompetenceOrganism,
        *,
        audit: NativeCompetenceSessionAudit | None = None,
    ) -> None:
        self.organism = organism
        self.r0_session: NativeR0DreamSession = organism.r0.dream_session()
        self.audit = audit
        self.envelope_digest = organism.persistent_state_audit()[
            "exact_state_sha256"
        ]
        self.closed = False
        if self.audit is not None:
            self.audit.session_open_count += 1
            self.audit.open_events.append({
                "child_id": organism.r0.provenance.child_id,
                "child_mature": organism.r0.provenance.mature,
                "child_grounded": organism.r0.provenance.grounded,
                "child_grounding_source": organism.r0.provenance.grounding_source,
                "mature_envelope_cell_ids": sorted(
                    cell.cell_id
                    for cell in organism.envelope.cells.values()
                    if cell.is_mature
                ),
            })

    def request(self, frame: Any) -> ChildQuery:
        if self.closed:
            raise RuntimeError("competence dream session is closed")
        query = self.r0_session.request(frame)
        board = frame.to_env_overlay().get("board")
        if not isinstance(board, chess.Board):
            raise TypeError("competence frame requires a chess.Board")
        signals = extract_active_competence_signals(
            self.organism.r0, board, query.actuation
        )
        classification = self.organism.envelope.classify(
            signals,
            policy_response=query.actuation is not None,
        )
        result = self.organism.apply_to_query(
            query,
            classification,
            active_signal_ids=signals,
        )
        if self.audit is not None:
            self.audit.request_count += 1
            actuation = None
            if result.actuation is not None:
                actuation = {
                    "actuator_identity": result.actuation.actuator_identity,
                    "move_uci": result.actuation.move_uci,
                    "option_identity": result.actuation.option_identity,
                    "activation": result.actuation.activation,
                    "candidate_count": result.actuation.candidate_count,
                    "formal_ticks": result.actuation.formal_ticks,
                    "graph_owned": result.actuation.graph_owned,
                    "host_fallback": result.actuation.host_fallback,
                }
            self.audit.request_events.append({
                "frame_id": frame.frame_id,
                "actuation": actuation,
                "active_competence_signal_ids": list(
                    result.active_competence_signal_ids
                ),
                "classification": classification.to_manifest(),
                "consumed_available": result.response.available,
                "availability_provenance": dict(
                    result.availability_provenance or {}
                ),
            })
        if (
            self.organism.persistent_state_audit()["exact_state_sha256"]
            != self.envelope_digest
        ):
            raise RuntimeError("virtual competence request mutated organism")
        return result

    def close(self) -> None:
        self.r0_session.close()
        if (
            self.organism.persistent_state_audit()["exact_state_sha256"]
            != self.envelope_digest
        ):
            raise RuntimeError("competence dream session leaked")
        self.closed = True
        if self.audit is not None:
            self.audit.session_close_count += 1
            self.audit.close_events.append({
                "request_count_at_close": self.audit.request_count,
                "persistent_state_identical": True,
            })


def evidence_key(
    board: chess.Board,
    actuation: GraphActuation,
    completion_terminal_identity: str,
) -> str:
    payload = (
        f"{board.fen()}|{actuation.actuator_identity}|"
        f"{completion_terminal_identity}"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def extract_active_competence_signals(
    organism: NativeR0Organism,
    board: chess.Board,
    actuation: GraphActuation | None,
) -> tuple[str, ...]:
    if actuation is None:
        return ()
    move = chess.Move.from_uci(actuation.move_uci)
    triplet_id = actuation.option_identity.rsplit(":", 1)[0]
    keys = _triplet_keys(board, move, key_mode=organism.graph.config.key_mode)
    active_atoms = organism.graph._shared_atom_ids_for_keys(keys)
    relevant_atoms = active_atoms.intersection(
        organism.graph.triplet_nodes.get(triplet_id, set())
    )
    signals = set(relevant_atoms)
    signals.add(POLICY_RESPONSE_SIGNAL_ID)
    for composite_id, members in organism.graph.composite_member_ids.items():
        cell = organism.graph.composite_cells.get(composite_id)
        if (
            cell is not None
            and cell.state == StemCellState.MATURE
            and triplet_id in organism.graph.composite_triplets.get(
                composite_id, set()
            )
            and set(members).issubset(active_atoms)
        ):
            signals.add(composite_id)
    return tuple(sorted(signals))


def flatten_consumed_availability_mask(
    slots: Mapping[str, Sequence[ChildQuery]],
) -> tuple[dict[str, Any], ...]:
    """Return the exact response mask consumed by fail-closed handover."""

    rows: list[dict[str, Any]] = []
    for action_identity in sorted(slots):
        for reply_index, query in enumerate(slots[action_identity]):
            rows.append({
                "action_identity": action_identity,
                "reply_index": reply_index,
                "frame_id": query.frame_id,
                "available": bool(query.response.available),
                "policy_response": bool(query.response.policy_response),
                "active_competence_signal_ids": list(
                    query.active_competence_signal_ids
                ),
                "availability_provenance": (
                    None
                    if query.availability_provenance is None
                    else dict(query.availability_provenance)
                ),
            })
    return tuple(rows)


def wilson_lower_bound(successes: int, support: int, z: float) -> float:
    if support <= 0:
        return 0.0
    successes = max(0, min(int(successes), int(support)))
    n = float(support)
    p = successes / n
    z2 = z * z
    denominator = 1.0 + z2 / n
    center = p + z2 / (2.0 * n)
    margin = z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * n)) / n)
    return max(0.0, min(1.0, (center - margin) / denominator))


def _policy_response_terminal(
    node: Node, env: Mapping[str, Any]
) -> tuple[bool, bool]:
    success = bool(env.get("policy_response", False))
    node.activation.value = 1.0 if success else 0.0
    return True, success


def _active_signal_terminal(
    node: Node, env: Mapping[str, Any]
) -> tuple[bool, bool]:
    identity = str(node.meta["member_identity"])
    success = identity in env.get("active_signal_ids", ())
    node.activation.value = 1.0 if success else 0.0
    return True, success


def _false_terminal(
    node: Node, _env: Mapping[str, Any]
) -> tuple[bool, bool]:
    node.activation.value = 0.0
    return True, False


def _availability_error_terminal(
    node: Node, env: Mapping[str, Any]
) -> tuple[bool, bool]:
    observed = 1.0 if bool(env.get("observed_completion", False)) else 0.0
    predicted = float(env.get("predicted_availability", 0.5))
    if not 0.0 <= predicted <= 1.0:
        raise ValueError("predicted availability must be in [0, 1]")
    error = observed - predicted
    node.activation.value = error
    node.meta["last_availability_error"] = error
    node.meta["growth_request_emitted"] = not math.isclose(error, 0.0)
    return True, not math.isclose(error, 0.0)


def _specialization_eligibility_terminal(
    node: Node, env: Mapping[str, Any]
) -> tuple[bool, bool]:
    pair = (
        str(node.meta["parent_cell_id"]),
        str(node.meta["base_identity"]),
    )
    success = pair in env.get("eligible_specialization_pairs", ())
    node.activation.value = 1.0 if success else 0.0
    return True, success



def _cell_prediction_error_terminal(
    node: Node, env: Mapping[str, Any]
) -> tuple[bool, bool]:
    polarity = AvailabilityState(str(node.meta["polarity"]))
    observed = bool(env.get("observed_completion", False))
    predicted = polarity == AvailabilityState.AVAILABLE
    contradiction = observed != predicted
    node.activation.value = 1.0 if contradiction else 0.0
    node.meta["last_prediction_error"] = int(contradiction)
    return True, contradiction
