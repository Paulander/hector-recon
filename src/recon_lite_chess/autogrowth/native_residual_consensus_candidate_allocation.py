"""Bounded residual-consensus allocation over opaque REAL trace identities."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence

from recon_lite import FrameKind

from .native_competence_envelope import (
    AvailabilityState,
    CompetenceContextGrowthGenome,
    GrowthProposal,
)
from .native_trace_competence_authority import GroundedOutcomeReceipt
from .native_trace_competence_authority import TraceNativeCompetenceOrganism


MEMORY_SCHEMA = "native_residual_consensus_memory.v1"
ALLOCATOR_SCHEMA = "native_residual_consensus_allocator.v1"


def _json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_json(value)).hexdigest()


class AllocationMode(str, Enum):
    TRUE_CONSENSUS = "true_residual_consensus_without_replacement"
    RESPONSIBILITY_DERANGED = (
        "responsibility_deranged_consensus_without_replacement"
    )
    HASH_WITHOUT_REPLACEMENT = "hash_priority_without_replacement"


@dataclass(frozen=True)
class ResidualConsensusConfig:
    maximum_stored_events: int = 64
    maximum_stored_tuple_entries: int = 4096
    maximum_tuple_updates_per_event: int = 4096
    maximum_candidate_score_evaluations_per_request: int = 16
    minimum_deranged_polarity_changes: int = 16
    event_eviction: str = "largest_content_blind_hash"
    tuple_overflow: str = "fail_closed_without_eviction"
    tie_breaking: str = "blake2b_content_blind_genome_hash"

    def __post_init__(self) -> None:
        if self.maximum_stored_events != 64:
            raise ValueError("frozen residual-event capacity changed")
        if self.maximum_stored_tuple_entries != 4096:
            raise ValueError("frozen attempted-pattern capacity changed")
        if self.maximum_tuple_updates_per_event != 4096:
            raise ValueError("frozen per-event tuple-update cap changed")
        if self.maximum_candidate_score_evaluations_per_request != 16:
            raise ValueError("frozen per-request evaluation cap changed")
        if self.minimum_deranged_polarity_changes != 16:
            raise ValueError("frozen derangement engagement minimum changed")


@dataclass(frozen=True)
class ResidualEvent:
    record_identity: str
    physical_interaction_identity: str
    ordinal: int
    pre_outcome_state: str
    pre_outcome_probability: float
    signed_availability_residual: float
    residual_polarity: str
    active_terminal_identities: tuple[str, ...]
    active_identity_cardinality: int
    structural_rounds: tuple[int, ...] = (0, 1, 2)

    def manifest(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResidualConsensusMemory:
    config: ResidualConsensusConfig = field(
        default_factory=ResidualConsensusConfig
    )
    events: dict[str, ResidualEvent] = field(default_factory=dict)
    physical_identities: dict[str, str] = field(default_factory=dict)
    attempted_patterns: dict[str, dict[str, Any]] = field(default_factory=dict)
    frozen: bool = False
    duplicate_deliveries: int = 0
    event_evictions: int = 0
    tuple_overflow_rejections: int = 0
    virtual_mutation_attempts: int = 0

    def ingest(
        self,
        *,
        frame_kind: FrameKind,
        receipt: GroundedOutcomeReceipt,
        pre_outcome_state: AvailabilityState,
        pre_outcome_probability: float,
        signed_availability_residual: float,
    ) -> bool:
        if FrameKind(frame_kind) is not FrameKind.REAL:
            raise ValueError("residual memory accepts REAL interactions only")
        if self.frozen:
            raise RuntimeError("residual memory is frozen")
        existing_record = self.events.get(receipt.event_id)
        physical_owner = self.physical_identities.get(
            receipt.context_fingerprint
        )
        if existing_record is not None or physical_owner is not None:
            if (
                existing_record is not None
                and existing_record.physical_interaction_identity
                == receipt.context_fingerprint
                and physical_owner == receipt.event_id
            ):
                self.duplicate_deliveries += 1
                return False
            raise RuntimeError("residual memory identity collision")
        residual = float(signed_availability_residual)
        if residual == 0.0:
            raise ValueError("zero signed residual has no request polarity")
        event = ResidualEvent(
            record_identity=receipt.event_id,
            physical_interaction_identity=receipt.context_fingerprint,
            ordinal=int(receipt.event_ordinal),
            pre_outcome_state=AvailabilityState(pre_outcome_state).value,
            pre_outcome_probability=float(pre_outcome_probability),
            signed_availability_residual=residual,
            residual_polarity=(
                AvailabilityState.AVAILABLE.value
                if residual > 0.0 else AvailabilityState.REFUTED.value
            ),
            active_terminal_identities=tuple(
                receipt.decision_trace.ordered_signal_identities
            ),
            active_identity_cardinality=len(set(
                receipt.decision_trace.ordered_signal_identities
            )),
        )
        self.events[event.record_identity] = event
        self.physical_identities[event.physical_interaction_identity] = (
            event.record_identity
        )
        self._evict_if_needed()
        return True

    def _evict_if_needed(self) -> None:
        while len(self.events) > self.config.maximum_stored_events:
            victim = max(
                self.events.values(),
                key=lambda item: _sha({
                    "physical_interaction_identity": (
                        item.physical_interaction_identity
                    )
                }),
            )
            del self.events[victim.record_identity]
            del self.physical_identities[
                victim.physical_interaction_identity
            ]
            self.event_evictions += 1

    def freeze(self) -> None:
        if len(self.events) != self.config.maximum_stored_events:
            raise RuntimeError("complete unique discovery prefix is absent")
        ordinals = sorted(event.ordinal for event in self.events.values())
        if ordinals != list(range(self.config.maximum_stored_events)):
            raise RuntimeError("residual event ordinals are incomplete")
        self.frozen = True

    def reserve_pattern(
        self,
        members: Sequence[str],
        *,
        round_index: int,
        request_ordinal: int,
        proposal_slot: int,
    ) -> bool:
        if not self.frozen:
            raise RuntimeError("attempted-pattern ledger requires frozen memory")
        canonical = tuple(sorted(set(map(str, members))))
        identity = _sha({"members": list(canonical)})
        if identity in self.attempted_patterns:
            return False
        if (
            len(self.attempted_patterns)
            >= self.config.maximum_stored_tuple_entries
        ):
            self.tuple_overflow_rejections += 1
            return False
        self.attempted_patterns[identity] = {
            "members_digest": identity,
            "width": len(canonical),
            "round_index": int(round_index),
            "request_ordinal": int(request_ordinal),
            "proposal_slot": int(proposal_slot),
        }
        return True

    @property
    def ordered_events(self) -> tuple[ResidualEvent, ...]:
        return tuple(sorted(self.events.values(), key=lambda item: item.ordinal))

    def manifest(self) -> dict[str, Any]:
        return {
            "schema_version": MEMORY_SCHEMA,
            "config": asdict(self.config),
            "events": [event.manifest() for event in self.ordered_events],
            "event_digest": _sha([
                event.manifest() for event in self.ordered_events
            ]),
            "physical_identity_count": len(self.physical_identities),
            "attempted_pattern_count": len(self.attempted_patterns),
            "attempted_pattern_digest": _sha(self.attempted_patterns),
            "attempted_pattern_widths": {
                str(width): sum(
                    row["width"] == width
                    for row in self.attempted_patterns.values()
                )
                for width in (1, 2, 3)
            },
            "frozen": self.frozen,
            "duplicate_deliveries": self.duplicate_deliveries,
            "event_evictions": self.event_evictions,
            "tuple_overflow_rejections": self.tuple_overflow_rejections,
            "virtual_mutation_attempts": self.virtual_mutation_attempts,
        }


def responsibility_derangement(
    events: Sequence[ResidualEvent], *, seed: int,
) -> tuple[dict[str, str], dict[str, Any]]:
    ordered = tuple(sorted(
        events,
        key=lambda item: hashlib.blake2b(
            f"{seed}|derangement|{item.record_identity}".encode(),
            digest_size=16,
        ).digest(),
    ))
    if len(ordered) < 2:
        raise ValueError("derangement requires at least two events")
    best: tuple[int, int, int] | None = None
    best_mapping: dict[str, str] | None = None
    for shift in range(1, len(ordered)):
        mapping = {
            item.record_identity: ordered[(index + shift) % len(ordered)].record_identity
            for index, item in enumerate(ordered)
        }
        if any(owner == donor for owner, donor in mapping.items()):
            continue
        by_id = {item.record_identity: item for item in ordered}
        same_cardinality = sum(
            by_id[owner].active_identity_cardinality
            == by_id[donor].active_identity_cardinality
            for owner, donor in mapping.items()
        )
        polarity_changes = sum(
            by_id[owner].residual_polarity != by_id[donor].residual_polarity
            for owner, donor in mapping.items()
        )
        score = (same_cardinality, polarity_changes, -shift)
        if best is None or score > best:
            best = score
            best_mapping = mapping
    assert best is not None and best_mapping is not None
    manifest = {
        "mapping": dict(sorted(best_mapping.items())),
        "mapping_digest": _sha(dict(sorted(best_mapping.items()))),
        "fixed_points": sum(
            owner == donor for owner, donor in best_mapping.items()
        ),
        "same_cardinality_assignments": best[0],
        "polarity_changes": best[1],
        "event_count": len(ordered),
    }
    return best_mapping, manifest


def bounded_derangement_statistic_probe(
    events: Sequence[ResidualEvent],
    mapping: Mapping[str, str],
    *,
    seed: int,
    probe_count: int = 16,
) -> dict[str, Any]:
    """Compare a bounded content-blind singleton probe before execution."""

    by_id = {event.record_identity: event for event in events}
    identities = sorted(
        {
            identity
            for event in events
            for identity in event.active_terminal_identities
        },
        key=lambda identity: hashlib.blake2b(
            f"{seed}|derangement-probe|{identity}".encode(),
            digest_size=16,
        ).digest(),
    )[:probe_count]
    rows = []
    for identity in identities:
        for polarity in (
            AvailabilityState.AVAILABLE.value,
            AvailabilityState.REFUTED.value,
        ):
            true_count = sum(
                event.residual_polarity == polarity
                and identity in event.active_terminal_identities
                for event in events
            )
            deranged_count = sum(
                by_id[mapping[event.record_identity]].residual_polarity
                == polarity
                and identity in event.active_terminal_identities
                for event in events
            )
            rows.append({
                "identity_digest": _sha(identity),
                "polarity": polarity,
                "true_count": true_count,
                "deranged_count": deranged_count,
            })
    changed = sum(
        row["true_count"] != row["deranged_count"] for row in rows
    )
    return {
        "bounded_probe_count": len(identities),
        "score_entry_count": len(rows),
        "changed_score_entries": changed,
        "changed": changed > 0,
        "rows_digest": _sha(rows),
    }


class ResidualConsensusGrowthGenome(CompetenceContextGrowthGenome):
    """Bounded organism-owned allocation with a common candidate stream."""

    def __init__(
        self,
        *,
        seed: int,
        memory: ResidualConsensusMemory,
        mode: AllocationMode,
        derangement: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(seed)
        if not memory.frozen:
            raise ValueError("allocator requires frozen residual memory")
        self.memory = memory
        self.mode = AllocationMode(mode)
        self.derangement = dict(derangement or {})
        if self.mode is AllocationMode.RESPONSIBILITY_DERANGED:
            if set(self.derangement) != set(memory.events):
                raise ValueError("incomplete responsibility derangement")
            if any(key == value for key, value in self.derangement.items()):
                raise ValueError("responsibility derangement has a fixed point")
        elif self.derangement:
            raise ValueError("non-deranged arm received a reassignment")
        self.proposal_slots_consumed = 0
        self.candidate_score_evaluations = 0
        self.duplicate_candidate_slots = 0
        self.empty_candidate_requests = 0
        self.requests_by_width = {1: 0, 2: 0, 3: 0}
        self.nominated_by_width = {1: 0, 2: 0, 3: 0}
        self.selected_score_total = 0
        self.tuple_updates_by_event = {
            event.record_identity: 0 for event in memory.ordered_events
        }
        self._current_request_emitted = True

    def consider_request(
        self, *, request_emitted: bool, **kwargs: Any
    ) -> GrowthProposal | None:
        self._current_request_emitted = bool(request_emitted)
        try:
            return self.propose(**kwargs)
        finally:
            self._current_request_emitted = True

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
            base_width, tuple_width = 1, 1
        elif round_index == 1:
            base_width, tuple_width = 2, 2
        elif round_index == 2 and contexts:
            base_width, tuple_width = 1, 2
        elif round_index == 2:
            base_width, tuple_width = 3, 3
        else:
            raise ValueError("unsupported frozen structural round")
        self.requests_by_width[tuple_width] += 1
        if len(bases) < base_width:
            self.empty_candidate_requests += 1
            return None
        evaluated: list[tuple[int, bytes, tuple[str, ...]]] = []
        cap = self.memory.config.maximum_candidate_score_evaluations_per_request
        for local_slot in range(cap):
            proposal_slot = self.proposal_slots_consumed
            self.proposal_slots_consumed += 1
            members = self._candidate(
                bases=bases,
                contexts=contexts,
                base_width=base_width,
                round_index=round_index,
                request_ordinal=request_ordinal,
                local_slot=local_slot,
            )
            if not self.memory.reserve_pattern(
                members,
                round_index=round_index,
                request_ordinal=request_ordinal,
                proposal_slot=proposal_slot,
            ):
                self.duplicate_candidate_slots += 1
                continue
            score = self._consensus_score(members, request_ordinal)
            self.candidate_score_evaluations += 1
            evaluated.append((
                score,
                self._tuple_priority(
                    members, round_index, request_ordinal
                ),
                members,
            ))
        if not evaluated:
            self.empty_candidate_requests += 1
            return None
        if self.mode is AllocationMode.HASH_WITHOUT_REPLACEMENT:
            selected = min(evaluated, key=lambda item: item[1])
        else:
            selected = min(evaluated, key=lambda item: (-item[0], item[1]))
        if not self._current_request_emitted:
            return None
        self.selected_score_total += selected[0]
        self.nominated_by_width[tuple_width] += 1
        consensus_reads = (
            () if self.mode is AllocationMode.HASH_WITHOUT_REPLACEMENT
            else tuple(sorted(self.memory.events))
        )
        return GrowthProposal(
            members=selected[2],
            round_index=round_index,
            request_ordinal=request_ordinal,
            genome_seed=self.seed,
            consensus_read_ids=consensus_reads,
        )

    def _candidate(
        self,
        *,
        bases: Sequence[str],
        contexts: Sequence[str],
        base_width: int,
        round_index: int,
        request_ordinal: int,
        local_slot: int,
    ) -> tuple[str, ...]:
        chosen: list[str] = []
        for position in range(base_width):
            ranked = sorted(
                (item for item in bases if item not in chosen),
                key=lambda item: hashlib.blake2b(
                    (
                        f"{self.seed}|candidate|{round_index}|"
                        f"{request_ordinal}|{local_slot}|{position}|{item}"
                    ).encode(),
                    digest_size=16,
                ).digest(),
            )
            if not ranked:
                return ()
            chosen.append(ranked[0])
        if contexts:
            context = min(
                contexts,
                key=lambda item: hashlib.blake2b(
                    (
                        f"{self.seed}|context|{round_index}|"
                        f"{request_ordinal}|{local_slot}|{item}"
                    ).encode(),
                    digest_size=16,
                ).digest(),
            )
            chosen.append(f"context:{context}")
        return tuple(sorted(chosen))

    def _consensus_score(
        self, members: Sequence[str], request_ordinal: int,
    ) -> int:
        if self.mode is AllocationMode.HASH_WITHOUT_REPLACEMENT:
            return 0
        events = self.memory.ordered_events
        request = next(
            item for item in events if item.ordinal == request_ordinal
        )
        requested_polarity = request.residual_polarity
        by_id = {item.record_identity: item for item in events}
        score = 0
        plain_members = tuple(
            member for member in members if not member.startswith("context:")
        )
        for trace_event in events:
            self.tuple_updates_by_event[trace_event.record_identity] += 1
            if (
                self.tuple_updates_by_event[trace_event.record_identity]
                > self.memory.config.maximum_tuple_updates_per_event
            ):
                raise RuntimeError("per-event tuple-update cap exceeded")
            residual_event = (
                by_id[self.derangement[trace_event.record_identity]]
                if self.mode is AllocationMode.RESPONSIBILITY_DERANGED
                else trace_event
            )
            if (
                residual_event.residual_polarity == requested_polarity
                and set(plain_members).issubset(
                    trace_event.active_terminal_identities
                )
            ):
                score += 1
        return score

    def _tuple_priority(
        self, members: Sequence[str], round_index: int, request_ordinal: int,
    ) -> bytes:
        return hashlib.blake2b(
            _json({
                "seed": self.seed,
                "round_index": round_index,
                "request_ordinal": request_ordinal,
                "members": list(members),
            }),
            digest_size=16,
        ).digest()

    def manifest(self) -> dict[str, Any]:
        return {
            "schema_version": ALLOCATOR_SCHEMA,
            "mode": self.mode.value,
            "seed": self.seed,
            "tie_breaking": self.memory.config.tie_breaking,
            "proposal_slots_consumed": self.proposal_slots_consumed,
            "unique_candidate_tuples_examined": len(
                self.memory.attempted_patterns
            ),
            "candidate_score_evaluations": self.candidate_score_evaluations,
            "duplicate_candidate_slots": self.duplicate_candidate_slots,
            "empty_candidate_requests": self.empty_candidate_requests,
            "proposal_slots_by_tuple_width": {
                str(width): self.requests_by_width[width]
                * self.memory.config.maximum_candidate_score_evaluations_per_request
                for width in (1, 2, 3)
            },
            "nominated_by_tuple_width": {
                str(width): self.nominated_by_width[width]
                for width in (1, 2, 3)
            },
            "selected_score_total": self.selected_score_total,
            "maximum_tuple_updates_observed_per_event": max(
                self.tuple_updates_by_event.values(), default=0
            ),
            "attempted_pattern_digest": _sha(
                self.memory.attempted_patterns
            ),
        }


@dataclass
class ResidualConsensusCompetenceOrganism:
    """Own the fixed allocator while preserving the legacy growth API law."""

    organism: TraceNativeCompetenceOrganism
    allocator: ResidualConsensusGrowthGenome

    def __post_init__(self) -> None:
        if self.organism.envelope.consensus_memory is not self.allocator.memory:
            raise ValueError("allocator memory is not organism-owned")
        if self.organism.learning_config.genome_seed != self.allocator.seed:
            raise ValueError("allocator seed differs from organism seed")

    def grow_from_grounded_receipts(
        self, receipts: Sequence[GroundedOutcomeReceipt]
    ) -> Any:
        records = []
        for receipt in receipts:
            record, inserted = self.organism._accept_receipt(receipt)
            if not inserted:
                raise RuntimeError("initial consensus growth tape has duplicate event")
            records.append(record)
        return self.organism.envelope.grow(
            records, genome=self.allocator
        )
