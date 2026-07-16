"""Graph-native, outcome-grounded competence envelope around frozen native R0."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import math
import pickle
from typing import Any, Iterable, Mapping, Sequence

import chess

from recon_lite import (
    ChildResponse,
    FormalReConEngine,
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
SCHEMA_VERSION = "native_r0_competence_envelope.v1"


class AvailabilityState(str, Enum):
    AVAILABLE = "available"
    REFUTED = "refuted"
    UNKNOWN = "unknown"


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
    provenance: str = "unique_real_r0_completion"

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
    schema_version: str = SCHEMA_VERSION
    graph: Graph = field(init=False)
    _member_specs: set[tuple[str, ...]] = field(default_factory=set, init=False)
    _next_cell_index: int = 0
    _review_count: int = 0

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
                len(matched) >= self.config.min_maturity_support
                and failures == 0
                and success_lower >= self.config.lower_bound_threshold
            )
            refuted = (
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
                if parent is None or not parent.is_mature:
                    return False
                if not self._cell_matches(parent, record, next_visiting):
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

        positive = [
            cell for cell in self.cells.values()
            if cell.is_mature and cell.polarity == AvailabilityState.AVAILABLE
        ]
        refuted = [
            cell for cell in self.cells.values()
            if cell.is_mature and cell.polarity == AvailabilityState.REFUTED
        ]
        trials = [cell for cell in self.cells.values() if cell.is_trial]
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
                if nested is None or not nested.is_mature:
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
