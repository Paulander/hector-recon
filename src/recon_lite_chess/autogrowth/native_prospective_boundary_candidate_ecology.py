"""Pure, data-free ecology for prospective boundary candidates.

The ecology owns only generic graph-visible identities and grounded Boolean
receipts.  It can bud a few cheap conjunction sketches before the native
authority graph is materialized; authority integration is deliberately left
to its caller.
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from enum import Enum
import hashlib
from itertools import combinations
import json
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "native_prospective_boundary_candidate_ecology.v8"
IMPLEMENTATION_IDENTITY = "content_blind_positive_shell_residual_incarnations.v8"
REAL_RECEIPT_KIND = "REAL"
DEFAULT_SIGNAL_ROLE = "graph_visible_signal"
PERMITTED_CANDIDATE_ROLES = frozenset({
    DEFAULT_SIGNAL_ROLE,
    "BASE_TERMINAL",
    "MATURE_COMPOSITE",
})
MAX_WIDTH = 3
# Candidate discovery is deliberately a small host-side beam.  These are
# resource limits, not scientific knobs: a demand can inspect at most this
# many bounded local rows and evaluate at most this many opaque conjunctions.
DEFAULT_CANDIDATE_BEAM_WIDTH = 16
MAX_CANDIDATE_BEAM_WIDTH = 64
DEFAULT_CANDIDATE_SEARCH_BUDGET = 4096
MAX_CANDIDATE_SEARCH_BUDGET = 8192
DEFAULT_LOCAL_OBSERVATION_CAP = 256
MAX_LOCAL_OBSERVATION_CAP = 1024
# A contradiction is a refinement opportunity, not a verdict.  These limits
# keep that opportunity finite at each event and over a candidate's lifetime;
# they are ecological safety bounds, not learner parameters.
DEFAULT_REFINEMENT_CHILD_CAP = 3
MAX_REFINEMENT_CHILD_CAP = MAX_WIDTH
DEFAULT_REFINEMENT_EVENT_CAP = 4
MAX_REFINEMENT_EVENT_CAP = 16
MIN_CONTRADICTIONS_BEFORE_DEATH = 2
# Candidate-local vectors are an event-time cache, not the certification
# ledger.  The complete accepted REAL ledger remains in ``_observations`` and
# is reread only by the explicit ``full_audit=True`` promotion path.  Keeping
# these maxima explicit makes active scans and snapshots independent of
# lifetime history.
MAX_RETAINED_SUPPORT_RECEIPTS = 4
MAX_RETAINED_CONTRADICTION_RECEIPTS = max(
    MIN_CONTRADICTIONS_BEFORE_DEATH,
    MAX_REFINEMENT_CHILD_CAP,
)
MAX_RETAINED_REFINEMENT_RECEIPTS = MAX_REFINEMENT_EVENT_CAP
MAX_RETAINED_READ_RECEIPTS = (
    1 + MAX_RETAINED_SUPPORT_RECEIPTS + MAX_RETAINED_REFINEMENT_RECEIPTS
)
MAX_RETAINED_RESIDUAL_IDS = (
    MAX_REFINEMENT_CHILD_CAP * MAX_REFINEMENT_EVENT_CAP
)
# Keep a fixed exploration share in every staged width.  It prevents a
# reliable-looking narrow beam from completely suppressing wider residuals,
# without making exploration another tunable scientific parameter.
EXPLORATION_QUOTA_DIVISOR = 8
WILSON_Z = 1.6448536269514722


def _json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _digest(value: Any) -> str:
    return hashlib.sha256(_json(value)).hexdigest()


def _evidence_token(observation: "BoundaryObservation") -> bytes:
    """Hash one matching REAL event without retaining its feature payload."""

    return hashlib.sha256(_json({
        "ordinal": observation.ordinal,
        "receipt_id": observation.receipt_id,
        "observed": observation.observed,
    })).digest()


def _mix_evidence_digest(
    prior: str,
    observation: "BoundaryObservation",
) -> str:
    """Commutatively fold matching evidence for permutation-stable replay."""

    left = bytes.fromhex(prior) if len(prior) == 64 else bytes(32)
    right = _evidence_token(observation)
    return bytes(a ^ b for a, b in zip(left, right)).hex()


def _priority(seed: int, ordinal: int, width: int, identity: str) -> bytes:
    """Stable content-blind ordering, equivalent to a genome hash."""

    return hashlib.blake2b(
        f"{seed}|boundary|{ordinal}|{width}|{identity}".encode(),
        digest_size=16,
    ).digest()


def wilson_lower_bound(successes: int, support: int, z: float = WILSON_Z) -> float:
    if support <= 0:
        return 0.0
    n = float(support)
    p = max(0.0, min(1.0, int(successes) / n))
    z2 = float(z) ** 2
    denominator = 1.0 + z2 / n
    center = p + z2 / (2.0 * n)
    margin = float(z) * ((p * (1.0 - p) + z2 / (4.0 * n)) / n) ** 0.5
    return max(0.0, min(1.0, (center - margin) / denominator))


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _ordinal(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("ordinal must be a non-negative integer")
    return value


def _signals(
    signal_ids: Sequence[str],
    signal_roles: Mapping[str, str] | Sequence[Sequence[str]] | None,
) -> tuple[tuple[str, str], ...]:
    ids = tuple(_text(item, "signal_id") for item in signal_ids)
    if len(set(ids)) != len(ids):
        raise ValueError("signal IDs must be unique")
    if signal_roles is None or signal_roles == ():
        by_id = {item: DEFAULT_SIGNAL_ROLE for item in ids}
    elif isinstance(signal_roles, Mapping):
        by_id = {str(key): value for key, value in signal_roles.items()}
    else:
        pairs = tuple(signal_roles)
        if len(pairs) == len(ids) and all(isinstance(pair, str) for pair in pairs):
            by_id = dict(zip(ids, pairs))
        elif len(pairs) != len(ids) or any(len(pair) != 2 for pair in pairs):
            raise ValueError("signal_roles must contain (signal_id, role) pairs")
        else:
            by_id = {str(key): value for key, value in pairs}
    if set(by_id) != set(ids):
        raise ValueError("signal_roles must cover signal_ids exactly")
    return tuple(sorted((_text(key, "signal_id"), _text(value, "signal_role")) for key, value in by_id.items()))


@dataclass(frozen=True)
class BoundaryObservation:
    """Immutable grounded REAL input; no domain/semantic selector fields."""

    ordinal: int
    receipt_id: str
    physical_id: str
    signal_ids: tuple[str, ...]
    observed: bool
    signal_roles: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _ordinal(self.ordinal)
        _text(self.receipt_id, "receipt_id")
        _text(self.physical_id, "physical_id")
        if not isinstance(self.observed, bool):
            raise ValueError("observed must be Boolean")
        pairs = _signals(self.signal_ids, self.signal_roles)
        object.__setattr__(self, "signal_ids", tuple(item[0] for item in pairs))
        object.__setattr__(self, "signal_roles", pairs)

    @property
    def receipt_kind(self) -> str:
        return REAL_RECEIPT_KIND

    def to_manifest(self) -> dict[str, Any]:
        return {
            "ordinal": self.ordinal,
            "receipt_id": self.receipt_id,
            "physical_id": self.physical_id,
            "signal_ids": list(self.signal_ids),
            "signal_roles": [list(item) for item in self.signal_roles],
            "observed": self.observed,
            "receipt_kind": REAL_RECEIPT_KIND,
        }

    @classmethod
    def from_manifest(cls, value: Mapping[str, Any]) -> "BoundaryObservation":
        if value.get("receipt_kind", REAL_RECEIPT_KIND) != REAL_RECEIPT_KIND:
            raise ValueError("only REAL receipts are accepted")
        return cls(
            ordinal=value["ordinal"],
            receipt_id=value["receipt_id"],
            physical_id=value["physical_id"],
            signal_ids=tuple(value.get("signal_ids", ())),
            signal_roles=tuple(tuple(item) for item in value.get("signal_roles", ())),
            observed=value["observed"],
        )


GroundedBoundaryObservation = BoundaryObservation


@dataclass(frozen=True)
class BoundaryExpandDemand:
    """Generic EXPAND request; candidate width is capped at three."""

    ordinal: int
    signal_ids: tuple[str, ...] = ()
    candidate_width: int = MAX_WIDTH
    signal_roles: tuple[tuple[str, str], ...] = ()
    triggering_receipt_id: str | None = None
    polarity: bool | None = None

    def __post_init__(self) -> None:
        _ordinal(self.ordinal)
        if isinstance(self.candidate_width, bool) or not 1 <= self.candidate_width <= MAX_WIDTH:
            raise ValueError("candidate_width must be between 1 and 3")
        if self.triggering_receipt_id is None or self.polarity is not True:
            raise ValueError(
                "EXPAND must bind a positive triggering_receipt_id; "
                "negative outcomes are contrast evidence, never birth triggers"
            )
        _text(self.triggering_receipt_id, "triggering_receipt_id")
        pairs = _signals(self.signal_ids, self.signal_roles or None)
        ids = tuple(item[0] for item in pairs)
        object.__setattr__(self, "signal_ids", ids)
        object.__setattr__(self, "signal_roles", pairs)

    def to_manifest(self) -> dict[str, Any]:
        return {
            "ordinal": self.ordinal,
            "signal_ids": list(self.signal_ids),
            "candidate_width": self.candidate_width,
            "signal_roles": [list(item) for item in self.signal_roles],
            "triggering_receipt_id": self.triggering_receipt_id,
            "polarity": self.polarity,
        }

    @classmethod
    def from_manifest(cls, value: Mapping[str, Any]) -> "BoundaryExpandDemand":
        return cls(
            ordinal=value["ordinal"],
            signal_ids=tuple(value.get("signal_ids", ())),
            candidate_width=value.get("candidate_width", MAX_WIDTH),
            signal_roles=tuple(tuple(item) for item in value.get("signal_roles", ())),
            triggering_receipt_id=value.get("triggering_receipt_id"),
            polarity=value.get("polarity"),
        )


class SketchLifecycle(str, Enum):
    ACTIVE = "ACTIVE"
    REFINING = "REFINING"
    DORMANT = "DORMANT"
    DEAD = "DEAD"


@dataclass(frozen=True)
class BoundarySketch:
    """A cheap monotone conjunction and its local grounded ledger."""

    sketch_id: str
    members: tuple[str, ...]
    birth_ordinal: int
    triggering_receipt_id: str
    polarity: bool
    state: SketchLifecycle = SketchLifecycle.ACTIVE
    positive_receipt_ids: tuple[str, ...] = ()
    negative_receipt_ids: tuple[str, ...] = ()
    read_receipt_ids: tuple[str, ...] = ()
    last_observation_ordinal: int | None = None
    retirement_reason: str | None = None
    parent_sketch_id: str | None = None
    refinement_source_receipt_id: str | None = None
    abstained_receipt_ids: tuple[str, ...] = ()
    refinement_receipt_ids: tuple[str, ...] = ()
    residual_sketch_ids: tuple[str, ...] = ()
    lifetime_match_count: int = 0
    lifetime_support_count: int = 0
    lifetime_contradiction_count: int = 0
    evidence_digest: str = ""

    def __post_init__(self) -> None:
        if not self.sketch_id or not 1 <= len(self.members) <= MAX_WIDTH:
            raise ValueError("invalid sketch identity or width")
        _ordinal(self.birth_ordinal)
        if tuple(sorted(self.members)) != tuple(self.members) or len(set(self.members)) != len(self.members):
            raise ValueError("sketch members must be sorted and unique")
        if self.polarity is not True:
            raise ValueError(
                "boundary sketches are positive-only; negative observations "
                "are contrast evidence"
            )
        for member in self.members:
            _text(member, "sketch member")
        object.__setattr__(self, "state", SketchLifecycle(self.state))
        positives = tuple(sorted(set(self.positive_receipt_ids)))
        negatives = tuple(sorted(set(self.negative_receipt_ids)))
        reads = tuple(sorted(set(self.read_receipt_ids)))
        abstained = tuple(sorted(set(self.abstained_receipt_ids)))
        refinements = tuple(sorted(set(self.refinement_receipt_ids)))
        residuals = tuple(sorted(set(self.residual_sketch_ids)))
        lifetime_values = (
            self.lifetime_match_count,
            self.lifetime_support_count,
            self.lifetime_contradiction_count,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in lifetime_values
        ):
            raise ValueError("invalid lifetime evidence counters")
        lifetime_match = self.lifetime_match_count
        lifetime_support = self.lifetime_support_count
        lifetime_contradiction = self.lifetime_contradiction_count
        if lifetime_support == lifetime_contradiction == lifetime_match == 0:
            # Internal callers created before the lifetime counters were
            # introduced can still be reconstructed from their birth cache.
            lifetime_support = len(positives)
            lifetime_contradiction = len(negatives)
            lifetime_match = lifetime_support + lifetime_contradiction
        if (
            lifetime_match != lifetime_support + lifetime_contradiction
        ):
            raise ValueError("invalid lifetime evidence counters")
        if (
            len(positives) > lifetime_support
            or len(negatives) > lifetime_contradiction
        ):
            raise ValueError("retained evidence exceeds lifetime counters")
        digest = self.evidence_digest
        if not isinstance(digest, str) or (digest and len(digest) != 64):
            raise ValueError("evidence_digest must be a 64-character hex digest")
        if lifetime_match and not digest:
            raise ValueError("matching evidence requires an evidence digest")
        if digest:
            try:
                bytes.fromhex(digest)
            except ValueError as error:
                raise ValueError("evidence_digest must be hexadecimal") from error
        if len(positives) > MAX_RETAINED_SUPPORT_RECEIPTS:
            raise ValueError("positive receipt cache exceeds its bound")
        if len(negatives) > MAX_RETAINED_CONTRADICTION_RECEIPTS:
            raise ValueError("negative receipt cache exceeds its bound")
        if len(reads) > MAX_RETAINED_READ_RECEIPTS:
            raise ValueError("read receipt cache exceeds its bound")
        if len(abstained) > MAX_RETAINED_REFINEMENT_RECEIPTS:
            raise ValueError("abstention receipt cache exceeds its bound")
        if len(refinements) > MAX_RETAINED_REFINEMENT_RECEIPTS:
            raise ValueError("refinement receipt cache exceeds its bound")
        if len(residuals) > MAX_RETAINED_RESIDUAL_IDS:
            raise ValueError("residual sketch cache exceeds its bound")
        if set(positives) & set(negatives):
            raise ValueError("receipt cannot have two outcomes")
        if self.triggering_receipt_id not in reads:
            raise ValueError("triggering receipt must be in sketch read set")
        if not set(positives) | set(negatives) <= set(reads):
            raise ValueError("outcome receipts must be in sketch read set")
        if not set(abstained) <= set(reads):
            raise ValueError("abstention receipts must be in sketch read set")
        if self.parent_sketch_id is not None:
            _text(self.parent_sketch_id, "parent_sketch_id")
            if self.parent_sketch_id == self.sketch_id:
                raise ValueError("sketch cannot refine itself")
        if self.refinement_source_receipt_id is not None:
            _text(self.refinement_source_receipt_id, "refinement_source_receipt_id")
        if any(not isinstance(item, str) or not item for item in residuals):
            raise ValueError("residual sketch IDs must be non-empty strings")
        object.__setattr__(self, "positive_receipt_ids", positives)
        object.__setattr__(self, "negative_receipt_ids", negatives)
        object.__setattr__(self, "read_receipt_ids", reads)
        object.__setattr__(self, "abstained_receipt_ids", abstained)
        object.__setattr__(self, "refinement_receipt_ids", refinements)
        object.__setattr__(self, "residual_sketch_ids", residuals)
        object.__setattr__(self, "lifetime_match_count", lifetime_match)
        object.__setattr__(self, "lifetime_support_count", lifetime_support)
        object.__setattr__(
            self,
            "lifetime_contradiction_count",
            lifetime_contradiction,
        )
        object.__setattr__(self, "evidence_digest", digest)

    @property
    def arity(self) -> int:
        return len(self.members)

    @property
    def positive_count(self) -> int:
        return self.lifetime_support_count

    @property
    def negative_count(self) -> int:
        return self.lifetime_contradiction_count

    @property
    def support(self) -> int:
        return self.support_count

    @property
    def contrast(self) -> int:
        return self.contradiction_count

    @property
    def same_polarity_support(self) -> int:
        return self.support_count

    @property
    def contrast_count(self) -> int:
        return self.contradiction_count

    @property
    def support_count(self) -> int:
        return self.lifetime_support_count

    @property
    def contradiction_count(self) -> int:
        return self.lifetime_contradiction_count

    @property
    def supporting_receipt_ids(self) -> tuple[str, ...]:
        return self.positive_receipt_ids if self.polarity else self.negative_receipt_ids

    @property
    def contradicting_receipt_ids(self) -> tuple[str, ...]:
        return self.negative_receipt_ids if self.polarity else self.positive_receipt_ids

    def lower_bound(self, z: float = WILSON_Z) -> float:
        return wilson_lower_bound(self.support_count, self.support_count + self.contradiction_count, z)

    def to_manifest(self) -> dict[str, Any]:
        return {
            "sketch_id": self.sketch_id,
            "members": list(self.members),
            "birth_ordinal": self.birth_ordinal,
            "triggering_receipt_id": self.triggering_receipt_id,
            "polarity": self.polarity,
            "state": self.state.value,
            "positive_receipt_ids": list(self.positive_receipt_ids),
            "negative_receipt_ids": list(self.negative_receipt_ids),
            "read_receipt_ids": list(self.read_receipt_ids),
            "last_observation_ordinal": self.last_observation_ordinal,
            "retirement_reason": self.retirement_reason,
            "parent_sketch_id": self.parent_sketch_id,
            "refinement_source_receipt_id": self.refinement_source_receipt_id,
            "abstained_receipt_ids": list(self.abstained_receipt_ids),
            "refinement_receipt_ids": list(self.refinement_receipt_ids),
            "residual_sketch_ids": list(self.residual_sketch_ids),
            "lifetime_match_count": self.lifetime_match_count,
            "lifetime_support_count": self.lifetime_support_count,
            "lifetime_contradiction_count": self.lifetime_contradiction_count,
            "evidence_digest": self.evidence_digest,
        }

    @classmethod
    def from_manifest(cls, value: Mapping[str, Any]) -> "BoundarySketch":
        return cls(
            sketch_id=value["sketch_id"],
            members=tuple(value["members"]),
            birth_ordinal=value["birth_ordinal"],
            triggering_receipt_id=value["triggering_receipt_id"],
            polarity=value["polarity"],
            state=value.get("state", SketchLifecycle.ACTIVE.value),
            positive_receipt_ids=tuple(value.get("positive_receipt_ids", ())),
            negative_receipt_ids=tuple(value.get("negative_receipt_ids", ())),
            read_receipt_ids=tuple(value.get("read_receipt_ids", ())),
            last_observation_ordinal=value.get("last_observation_ordinal"),
            retirement_reason=value.get("retirement_reason"),
            parent_sketch_id=value.get("parent_sketch_id"),
            refinement_source_receipt_id=value.get("refinement_source_receipt_id"),
            abstained_receipt_ids=tuple(value.get("abstained_receipt_ids", ())),
            refinement_receipt_ids=tuple(value.get("refinement_receipt_ids", ())),
            residual_sketch_ids=tuple(value.get("residual_sketch_ids", ())),
            lifetime_match_count=value.get("lifetime_match_count", 0),
            lifetime_support_count=value.get("lifetime_support_count", 0),
            lifetime_contradiction_count=value.get(
                "lifetime_contradiction_count",
                0,
            ),
            evidence_digest=value.get("evidence_digest", ""),
        )


@dataclass(frozen=True)
class PromotionDecision:
    """Immutable promotion gate and its bounded or fully audited read set."""

    candidate_id: str | None
    members: tuple[str, ...]
    triggering_receipt_id: str | None
    eligible: bool
    polarity: bool | None
    lifecycle_state: SketchLifecycle | None
    support_count: int
    contradiction_count: int
    wilson_lower_bound: float
    supporting_receipt_ids: tuple[str, ...]
    contradicting_receipt_ids: tuple[str, ...]
    inspected_receipt_ids: tuple[str, ...]
    discovery_exclusion_receipt_ids: tuple[str, ...]
    ranked_candidate_ids: tuple[str, ...]
    reason: str
    inspected_ordinal_interval: tuple[int, int] | None = None

    @property
    def promotion_eligible(self) -> bool:
        return self.eligible

    @property
    def supporting_real_receipt_ids(self) -> tuple[str, ...]:
        return self.supporting_receipt_ids

    def to_manifest(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "members": list(self.members),
            "triggering_receipt_id": self.triggering_receipt_id,
            "eligible": self.eligible,
            "polarity": self.polarity,
            "lifecycle_state": None if self.lifecycle_state is None else self.lifecycle_state.value,
            "support_count": self.support_count,
            "contradiction_count": self.contradiction_count,
            "wilson_lower_bound": self.wilson_lower_bound,
            "supporting_receipt_ids": list(self.supporting_receipt_ids),
            "contradicting_receipt_ids": list(self.contradicting_receipt_ids),
            "inspected_receipt_ids": list(self.inspected_receipt_ids),
            "discovery_exclusion_receipt_ids": list(self.discovery_exclusion_receipt_ids),
            "ranked_candidate_ids": list(self.ranked_candidate_ids),
            "reason": self.reason,
            "inspected_ordinal_interval": (
                None if self.inspected_ordinal_interval is None else list(self.inspected_ordinal_interval)
            ),
            "receipt_kind": REAL_RECEIPT_KIND,
        }

@dataclass(frozen=True)
class BoundaryEcologyConfig:
    genome_seed: int = 2026071606
    max_candidates_per_demand: int = MAX_WIDTH
    active_sketch_cap: int = 32
    candidate_beam_width: int = DEFAULT_CANDIDATE_BEAM_WIDTH
    candidate_search_budget: int = DEFAULT_CANDIDATE_SEARCH_BUDGET
    local_observation_cap: int = DEFAULT_LOCAL_OBSERVATION_CAP
    minimum_support: int = 4
    lower_bound_threshold: float = 0.55
    wilson_z: float = WILSON_Z
    refinement_child_cap: int = DEFAULT_REFINEMENT_CHILD_CAP
    refinement_event_cap: int = DEFAULT_REFINEMENT_EVENT_CAP

    def __post_init__(self) -> None:
        if not 1 <= self.max_candidates_per_demand <= MAX_WIDTH:
            raise ValueError("max_candidates_per_demand must be between 1 and 3")
        if self.active_sketch_cap < 1:
            raise ValueError("active_sketch_cap must be positive")
        if (
            isinstance(self.candidate_beam_width, bool)
            or not isinstance(self.candidate_beam_width, int)
            or not 1 <= self.candidate_beam_width <= MAX_CANDIDATE_BEAM_WIDTH
        ):
            raise ValueError(
                "candidate_beam_width must be between 1 and "
                f"{MAX_CANDIDATE_BEAM_WIDTH}"
            )
        if (
            isinstance(self.candidate_search_budget, bool)
            or not isinstance(self.candidate_search_budget, int)
            or not 1
            <= self.candidate_search_budget
            <= MAX_CANDIDATE_SEARCH_BUDGET
        ):
            raise ValueError(
                "candidate_search_budget must be between 1 and "
                f"{MAX_CANDIDATE_SEARCH_BUDGET}"
            )
        if (
            isinstance(self.local_observation_cap, bool)
            or not isinstance(self.local_observation_cap, int)
            or not 1 <= self.local_observation_cap <= MAX_LOCAL_OBSERVATION_CAP
        ):
            raise ValueError(
                "local_observation_cap must be between 1 and "
                f"{MAX_LOCAL_OBSERVATION_CAP}"
            )
        if self.minimum_support != 4 or abs(self.lower_bound_threshold - 0.55) > 1e-12:
            raise ValueError("promotion thresholds are fixed at 4 and 0.55")
        if self.wilson_z <= 0:
            raise ValueError("wilson_z must be positive")
        if (
            isinstance(self.refinement_child_cap, bool)
            or not isinstance(self.refinement_child_cap, int)
            or not 1 <= self.refinement_child_cap <= MAX_REFINEMENT_CHILD_CAP
        ):
            raise ValueError(
                "refinement_child_cap must be between 1 and "
                f"{MAX_REFINEMENT_CHILD_CAP}"
            )
        if (
            isinstance(self.refinement_event_cap, bool)
            or not isinstance(self.refinement_event_cap, int)
            or not 1 <= self.refinement_event_cap <= MAX_REFINEMENT_EVENT_CAP
        ):
            raise ValueError(
                "refinement_event_cap must be between 1 and "
                f"{MAX_REFINEMENT_EVENT_CAP}"
            )

    def to_manifest(self) -> dict[str, Any]:
        return {
            "genome_seed": self.genome_seed,
            "max_candidates_per_demand": self.max_candidates_per_demand,
            "active_sketch_cap": self.active_sketch_cap,
            "candidate_beam_width": self.candidate_beam_width,
            "candidate_search_budget": self.candidate_search_budget,
            "local_observation_cap": self.local_observation_cap,
            "minimum_support": self.minimum_support,
            "lower_bound_threshold": self.lower_bound_threshold,
            "wilson_z": self.wilson_z,
            "refinement_child_cap": self.refinement_child_cap,
            "refinement_event_cap": self.refinement_event_cap,
        }


class DuplicatePhysicalReceiptError(ValueError):
    """Receipt or physical interaction identity was already consumed."""


class ProspectiveBoundaryCandidateEcology:
    """Mutable event ledger whose values and decisions are immutable."""

    def __init__(self, config: BoundaryEcologyConfig | None = None) -> None:
        self.config = config or BoundaryEcologyConfig()
        self._sketches: dict[str, BoundarySketch] = {}
        self._active_ids: set[str] = set()
        # Derived, active-cap-bounded indexes.  Lifetime tombstones remain in
        # ``_sketches`` for replay but recurring birth/refinement decisions
        # must never scan them.
        self._live_pattern_index: dict[tuple[str, ...], set[str]] = {}
        self._live_residual_index: dict[str, set[str]] = {}
        self._demand_birth_ids: dict[int, tuple[str, ...]] = {}
        self._tombstones: dict[str, BoundarySketch] = {}
        self._observations: dict[str, BoundaryObservation] = {}
        self._physical: dict[str, str] = {}
        self._ordinals: dict[int, str] = {}
        self._observation_ordinals: list[int] = []
        self._observation_receipt_order: list[str] = []
        # A deterministic, bounded view of the accepted REAL ledger used only
        # for proposal scoring.  Promotion still recloses against the complete
        # immutable observation ledger.  Keeping this index sorted by the
        # opaque event ordinal makes direct and permuted ingestion equivalent.
        self._local_receipt_ids: list[str] = []
        self._demands: dict[int, BoundaryExpandDemand] = {}
        self._frontier = -1
        self._births = 0
        self._capacity_rejections = 0
        self._duplicate_rejections = 0
        self._prune_counts = {
            "contradiction": 0,
            "refinement": 0,
            "capacity": 0,
            "redundant_authority_pattern": 0,
        }
        self._last_refinement_ids: tuple[str, ...] = ()

    @staticmethod
    def _is_live(candidate: BoundarySketch) -> bool:
        return candidate.state in {
            SketchLifecycle.ACTIVE,
            SketchLifecycle.REFINING,
        }

    def _index_live_sketch(self, candidate: BoundarySketch) -> None:
        if not self._is_live(candidate):
            return
        self._active_ids.add(candidate.sketch_id)
        if candidate.polarity is True:
            self._live_pattern_index.setdefault(
                candidate.members, set()
            ).add(candidate.sketch_id)
        if candidate.parent_sketch_id is not None:
            self._live_residual_index.setdefault(
                candidate.parent_sketch_id, set()
            ).add(candidate.sketch_id)

    def _deindex_live_sketch(self, candidate: BoundarySketch) -> None:
        self._active_ids.discard(candidate.sketch_id)
        pattern_ids = self._live_pattern_index.get(candidate.members)
        if pattern_ids is not None:
            pattern_ids.discard(candidate.sketch_id)
            if not pattern_ids:
                self._live_pattern_index.pop(candidate.members, None)
        if candidate.parent_sketch_id is not None:
            residual_ids = self._live_residual_index.get(
                candidate.parent_sketch_id
            )
            if residual_ids is not None:
                residual_ids.discard(candidate.sketch_id)
                if not residual_ids:
                    self._live_residual_index.pop(
                        candidate.parent_sketch_id, None
                    )

    def _store_sketch(self, candidate: BoundarySketch) -> None:
        prior = self._sketches.get(candidate.sketch_id)
        if prior is not None:
            self._deindex_live_sketch(prior)
        self._sketches[candidate.sketch_id] = candidate
        if self._is_live(candidate):
            self._index_live_sketch(candidate)
        else:
            self._active_ids.discard(candidate.sketch_id)
            self._tombstones[candidate.sketch_id] = candidate

    def _rebuild_live_indexes(self) -> None:
        """Rebuild derived indexes only at restoration/full-audit boundaries."""

        ordered_observations = tuple(sorted(
            self._observations.values(),
            key=lambda item: (item.ordinal, item.receipt_id),
        ))
        self._observation_ordinals = [
            item.ordinal for item in ordered_observations
        ]
        self._observation_receipt_order = [
            item.receipt_id for item in ordered_observations
        ]
        self._active_ids = set()
        self._live_pattern_index = {}
        self._live_residual_index = {}
        demand_births: dict[int, list[str]] = {
            ordinal: [] for ordinal in self._demands
        }
        for candidate in self._sketches.values():
            self._index_live_sketch(candidate)
            demand = self._demands.get(candidate.birth_ordinal)
            if (
                demand is not None
                and candidate.triggering_receipt_id
                == demand.triggering_receipt_id
                and candidate.polarity is demand.polarity
                and candidate.parent_sketch_id is None
                and candidate.refinement_source_receipt_id is None
            ):
                demand_births[demand.ordinal].append(candidate.sketch_id)
        self._demand_birth_ids = {
            ordinal: tuple(sorted(candidate_ids))
            for ordinal, candidate_ids in demand_births.items()
        }

    def _verify_live_indexes(self) -> None:
        """Full-boundary check for the bounded derived indexes."""

        expected_active = {
            candidate.sketch_id for candidate in self._sketches.values()
            if self._is_live(candidate)
        }
        expected_patterns: dict[tuple[str, ...], set[str]] = {}
        expected_residuals: dict[str, set[str]] = {}
        demand_births: dict[int, list[str]] = {
            ordinal: [] for ordinal in self._demands
        }
        for candidate in self._sketches.values():
            if not self._is_live(candidate):
                pass
            else:
                if candidate.polarity is True:
                    expected_patterns.setdefault(candidate.members, set()).add(
                        candidate.sketch_id
                    )
                if candidate.parent_sketch_id is not None:
                    expected_residuals.setdefault(
                        candidate.parent_sketch_id, set()
                    ).add(candidate.sketch_id)
            demand = self._demands.get(candidate.birth_ordinal)
            if (
                demand is not None
                and candidate.triggering_receipt_id
                == demand.triggering_receipt_id
                and candidate.polarity is demand.polarity
                and candidate.parent_sketch_id is None
                and candidate.refinement_source_receipt_id is None
            ):
                demand_births[demand.ordinal].append(candidate.sketch_id)
        expected_demands = {
            ordinal: tuple(sorted(candidate_ids))
            for ordinal, candidate_ids in demand_births.items()
        }
        expected_observations = tuple(sorted(
            self._observations.values(),
            key=lambda item: (item.ordinal, item.receipt_id),
        ))
        if (
            self._observation_ordinals != [
                item.ordinal for item in expected_observations
            ]
            or self._observation_receipt_order != [
                item.receipt_id for item in expected_observations
            ]
            or self._active_ids != expected_active
            or self._live_pattern_index != expected_patterns
            or self._live_residual_index != expected_residuals
            or self._demand_birth_ids != expected_demands
        ):
            raise ValueError("boundary ecology live indexes are inconsistent")

    @property
    def sketches(self) -> Mapping[str, BoundarySketch]:
        return MappingProxyType(self._sketches)

    @property
    def active_sketches(self) -> tuple[BoundarySketch, ...]:
        return tuple(
            self._sketches[key]
            for key in sorted(self._active_ids)
            if self._is_live(self._sketches[key])
        )

    @property
    def tombstones(self) -> Mapping[str, BoundarySketch]:
        return MappingProxyType(self._tombstones)

    @property
    def observations(self) -> Mapping[str, BoundaryObservation]:
        return MappingProxyType(self._observations)

    @property
    def active_sketch_count(self) -> int:
        return len(self.active_sketches)

    @property
    def lifetime_birth_count(self) -> int:
        return self._births

    @property
    def frontier_ordinal(self) -> int:
        return self._frontier

    @property
    def last_refinement_ids(self) -> tuple[str, ...]:
        """Children created by the most recent accepted REAL observation.

        This is a convenience event view for the curriculum.  The durable
        source of truth is the immutable parent/child metadata in
        :meth:`manifest`; callers must not use this transient view for
        certification.
        """

        return self._last_refinement_ids

    def expand(self, demand: BoundaryExpandDemand) -> tuple[BoundarySketch, ...]:
        """Handle one EXPAND and bud at most three scored sketches.

        Discovery is intentionally weaker than certification.  It may read a
        bounded local prefix of accepted REAL observations to find residual
        conjunctions, but the resulting sketches start with only their own
        trigger receipt.  An ordinary promotion gate uses bounded local
        counters; an authority caller may explicitly request a complete
        post-birth reread with ``full_audit=True``.
        """

        if not isinstance(demand, BoundaryExpandDemand):
            raise TypeError("expand requires BoundaryExpandDemand")
        if demand.polarity is not True:
            # BoundaryExpandDemand already rejects this.  Keep the guard at
            # the mutation boundary in case a future caller supplies a
            # duck-typed demand or bypasses dataclass construction.
            raise ValueError("negative outcomes cannot create boundary sketches")
        trigger = self._observations.get(demand.triggering_receipt_id)
        if trigger is None:
            raise ValueError("EXPAND trigger must already be an accepted observation")
        if trigger.observed is not True:
            raise ValueError("EXPAND trigger must be a positive REAL outcome")
        if trigger.observed is not demand.polarity:
            raise ValueError("EXPAND polarity disagrees with trigger outcome")
        if not set(demand.signal_ids).issubset(trigger.signal_ids):
            raise ValueError("EXPAND signals must be visible in its trigger")
        prior = self._demands.get(demand.ordinal)
        if prior is not None:
            if prior != demand:
                raise ValueError("demand ordinal collision")
            return self._born_for(demand)
        self._demands[demand.ordinal] = demand
        self._frontier = max(self._frontier, demand.ordinal)
        trigger_roles = dict(trigger.signal_roles)
        roles = dict(demand.signal_roles or trigger.signal_roles)
        if any(trigger_roles[item] != roles[item] for item in demand.signal_ids):
            raise ValueError("EXPAND signal roles differ from its trigger")
        # Only reusable graph-visible micropatterns may seed competence.  In
        # particular, the universal internal policy-response marker is not a
        # candidate: admitting it would create a tautological hypothesis.
        pool = tuple(
            item for item in (demand.signal_ids or trigger.signal_ids)
            if roles[item] in PERMITTED_CANDIDATE_ROLES
        )
        proposals = self._ranked_residual_candidates(
            pool,
            trigger=trigger,
            candidate_width=demand.candidate_width,
            ordinal=demand.ordinal,
            polarity=bool(demand.polarity),
        )
        born: list[BoundarySketch] = []
        for members in proposals:
            if members in [item.members for item in born]:
                continue
            member_roles = tuple((item, roles.get(item, DEFAULT_SIGNAL_ROLE)) for item in members)
            sketch_id = self._incarnation_id(
                members=members,
                roles=member_roles,
                birth_kind="surprise_positive",
                trigger_receipt_id=demand.triggering_receipt_id,
                birth_ordinal=demand.ordinal,
            )
            if self._has_live_pattern(members):
                continue
            if sketch_id in self._sketches:
                raise ValueError("boundary sketch incarnation identity collision")
            if self.active_sketch_count >= self.config.active_sketch_cap:
                self._evict_for_capacity()
            candidate = BoundarySketch(
                sketch_id,
                members,
                demand.ordinal,
                demand.triggering_receipt_id,
                demand.polarity,
                positive_receipt_ids=(demand.triggering_receipt_id,) if demand.polarity else (),
                negative_receipt_ids=(demand.triggering_receipt_id,) if not demand.polarity else (),
                read_receipt_ids=(demand.triggering_receipt_id,),
                last_observation_ordinal=trigger.ordinal,
                lifetime_match_count=1,
                lifetime_support_count=1,
                lifetime_contradiction_count=0,
                evidence_digest=_mix_evidence_digest(
                    "0" * 64,
                    trigger,
                ),
            )
            self._store_sketch(candidate)
            self._births += 1
            born.append(candidate)
        self._demand_birth_ids[demand.ordinal] = tuple(sorted(
            item.sketch_id for item in born
        ))
        return tuple(born)

    def _has_live_pattern(self, members: Sequence[str]) -> bool:
        """Return whether this positive micropattern already has a live bud."""

        return bool(self._live_pattern_ids(members))

    def _live_pattern_ids(self, members: Sequence[str]) -> tuple[str, ...]:
        """Return live incarnations of one canonical positive pattern."""

        canonical = tuple(sorted(members))
        return tuple(sorted(
            candidate_id
            for candidate_id in self._live_pattern_index.get(canonical, ())
            if candidate_id in self._active_ids
        ))

    def _incarnation_id(
        self,
        *,
        members: Sequence[str],
        roles: Sequence[tuple[str, str]],
        birth_kind: str,
        trigger_receipt_id: str,
        birth_ordinal: int,
        parent_sketch_id: str | None = None,
        refinement_source_receipt_id: str | None = None,
    ) -> str:
        """Derive a deterministic, never-reused birth incarnation ID.

        Pattern equality is intentionally separate from identity equality:
        ``_has_live_pattern`` suppresses simultaneous duplicate buds, while
        this digest lets a later positive event rebud a retired pattern under
        a fresh ID without reviving its tombstone.
        """

        return _digest({
            "seed": self.config.genome_seed,
            "birth_kind": birth_kind,
            "birth_ordinal": int(birth_ordinal),
            "trigger_receipt_id": str(trigger_receipt_id),
            "parent_sketch_id": parent_sketch_id,
            "refinement_source_receipt_id": refinement_source_receipt_id,
            "members": tuple(sorted(members)),
            "roles": tuple(sorted(roles)),
            "polarity": True,
        })[:32]

    def _local_rows_for_candidate(
        self,
        candidate: BoundarySketch,
        *,
        through_ordinal: int | None = None,
    ) -> tuple[BoundaryObservation, ...]:
        """Return bounded local rows that contain a candidate's coarse pattern."""

        limit = (
            self._frontier if through_ordinal is None else int(through_ordinal)
        )
        return tuple(
            row
            for row in self._local_observations(through_ordinal=limit)
            if row.ordinal >= candidate.birth_ordinal
            and set(candidate.members).issubset(row.signal_ids)
        )

    def _residual_specs(
        self,
        candidate: BoundarySketch,
        contradiction: BoundaryObservation,
    ) -> tuple[
        tuple[
            tuple[str, ...],
            BoundaryObservation,
            tuple[tuple[str, str], ...],
            int,
            int,
        ],
        ...,
    ]:
        """Rank bounded positive residuals that exclude one false region.

        A residual may only add locally observed, graph-visible signals that
        occur in a positive row and are absent from the contradicting row.
        This is the key locality constraint: the ecology never invents a
        board selector or imports an answer from outside its REAL ledger.
        """

        if candidate.polarity is not True or candidate.arity >= MAX_WIDTH:
            return ()
        rows = self._local_rows_for_candidate(
            candidate,
            through_ordinal=contradiction.ordinal,
        )
        positives = tuple(row for row in rows if row.observed is True)
        if not positives:
            return ()
        coarse = set(candidate.members)
        false_signals = set(contradiction.signal_ids)
        role_by_signal: dict[str, str] = {}
        disallowed: set[str] = set()
        for row in positives:
            for signal_id, role in row.signal_roles:
                if signal_id in coarse:
                    continue
                prior = role_by_signal.get(signal_id)
                if prior is not None and prior != role:
                    # A signal with unstable local typing cannot be a safe
                    # micropattern.  Keep it in contrast data only.
                    disallowed.add(signal_id)
                role_by_signal.setdefault(signal_id, role)
        extras = tuple(sorted(
            signal_id
            for signal_id in role_by_signal
            if signal_id not in false_signals
            and signal_id not in disallowed
            and role_by_signal[signal_id] in PERMITTED_CANDIDATE_ROLES
        ))
        remaining = MAX_WIDTH - candidate.arity
        if not extras or remaining < 1:
            return ()

        ranked: list[
            tuple[
                tuple[str, ...],
                BoundaryObservation,
                tuple[tuple[str, str], ...],
                int,
                int,
                bytes,
                float,
            ]
        ] = []
        search_budget = min(
            self.config.candidate_search_budget,
            max(1, self.config.refinement_child_cap * self.config.candidate_beam_width),
        )
        considered = 0
        for width in range(1, remaining + 1):
            for extra_members in combinations(extras, width):
                if considered >= search_budget:
                    break
                considered += 1
                members = tuple(sorted((*candidate.members, *extra_members)))
                member_set = set(members)
                support_rows = tuple(
                    row for row in positives if member_set.issubset(row.signal_ids)
                )
                contrast_rows = tuple(
                    row
                    for row in rows
                    if row.observed is False and member_set.issubset(row.signal_ids)
                )
                if not support_rows:
                    continue
                source = min(
                    support_rows,
                    key=lambda row: (row.ordinal, row.receipt_id),
                )
                roles = tuple(
                    (member, role_by_signal.get(member, DEFAULT_SIGNAL_ROLE))
                    for member in members
                )
                priority = _priority(
                    self.config.genome_seed,
                    contradiction.ordinal,
                    len(members),
                    "|".join((candidate.sketch_id, *members)),
                )
                support = len(support_rows)
                contrast = len(contrast_rows)
                lower = wilson_lower_bound(
                    support,
                    support + contrast,
                    self.config.wilson_z,
                )
                ranked.append(
                    (
                        members,
                        source,
                        roles,
                        support,
                        contrast,
                        priority,
                        lower,
                    )
                )
            if considered >= search_budget:
                break

        ranked.sort(
            key=lambda item: (
                -item[6],
                -item[3],
                item[4],
                len(item[0]),
                item[5],
            )
        )
        return tuple(item[:5] for item in ranked[: self.config.refinement_child_cap])

    def _spawn_residual_refinements(
        self,
        candidate: BoundarySketch,
        contradiction: BoundaryObservation,
    ) -> tuple[str, ...]:
        """Materialize a bounded local residual beam for one contradiction."""

        if len(candidate.refinement_receipt_ids) >= self.config.refinement_event_cap:
            return ()
        specs = self._residual_specs(candidate, contradiction)
        born: list[str] = []
        for members, source, roles, _support, _contrast in specs:
            # A pattern is canonical across independent local explanations;
            # do not consume a slot for an identical live bud.
            sketch_id = self._incarnation_id(
                members=members,
                roles=roles,
                birth_kind="residual_refinement",
                trigger_receipt_id=source.receipt_id,
                birth_ordinal=source.ordinal,
                parent_sketch_id=candidate.sketch_id,
                refinement_source_receipt_id=contradiction.receipt_id,
            )
            existing = self._sketches.get(sketch_id)
            if existing is not None:
                if existing.members != members or existing.polarity is not True:
                    raise ValueError("boundary sketch identity collision")
                # A same-source replay must resolve to the same incarnation;
                # a tombstoned incarnation is never revived.
                continue
            live_pattern_ids = self._live_pattern_ids(members)
            if live_pattern_ids:
                # The initial beam may already have discovered exactly this
                # strict residual before its parent sees the contrast.  Reuse
                # that live incarnation and record the parent-to-residual
                # relationship; do not create a duplicate identity.
                if not (
                    set(candidate.members) < set(members)
                    and not set(members).issubset(contradiction.signal_ids)
                ):
                    continue
                born.extend(live_pattern_ids)
                continue
            if self.active_sketch_count >= self.config.active_sketch_cap:
                # Never evict the parent while its contradiction is being
                # committed.  Otherwise the subsequent immutable parent
                # update could leave a stale tombstone and make replay
                # ambiguous.  If no other slot is available this residual is
                # simply deferred; the parent remains a live refiner.
                self._evict_for_capacity(exclude_ids={candidate.sketch_id})
            if self.active_sketch_count >= self.config.active_sketch_cap:
                break
            child = BoundarySketch(
                sketch_id=sketch_id,
                members=members,
                birth_ordinal=source.ordinal,
                triggering_receipt_id=source.receipt_id,
                polarity=True,
                state=SketchLifecycle.ACTIVE,
                positive_receipt_ids=(source.receipt_id,),
                negative_receipt_ids=(),
                read_receipt_ids=(source.receipt_id,),
                last_observation_ordinal=contradiction.ordinal,
                retirement_reason=None,
                parent_sketch_id=candidate.sketch_id,
                refinement_source_receipt_id=contradiction.receipt_id,
                lifetime_match_count=1,
                lifetime_support_count=1,
                lifetime_contradiction_count=0,
                evidence_digest=_mix_evidence_digest(
                    "0" * 64,
                    source,
                ),
            )
            self._store_sketch(child)
            self._births += 1
            self._prune_counts["refinement"] += 1
            born.append(sketch_id)
        return tuple(born)

    def _local_observations(self, *, through_ordinal: int) -> tuple[BoundaryObservation, ...]:
        """Return the bounded deterministic proposal-scoring ledger view."""

        rows = [
            self._observations[receipt_id]
            for receipt_id in self._local_receipt_ids
            if self._observations[receipt_id].ordinal <= through_ordinal
        ]
        # A trigger can be outside the bounded window only when a caller has
        # supplied an out-of-order event.  Include it explicitly; this keeps a
        # newborn candidate grounded in its own current REAL observation.
        return tuple(rows)

    def _ranked_residual_candidates(
        self,
        pool: Sequence[str],
        *,
        trigger: BoundaryObservation,
        candidate_width: int,
        ordinal: int,
        polarity: bool,
    ) -> tuple[tuple[str, ...], ...]:
        """Find bounded residual-guided beams of opaque conjunctions.

        Each width gets a deterministic slice of the total search budget.
        Width one is scored first; only its top beam is extended to width two,
        and only the top width-two beam is extended to width three.  A fixed
        hash-ordered exploration quota is interleaved at every width so an
        impure narrow projection cannot make a useful wider residual
        unreachable.  The final API still emits one representative per
        available arity, but ``candidate_beam_width`` now changes the search
        frontier rather than merely slicing an already-complete scan.
        """

        if not pool or candidate_width < 1:
            return ()
        maximum_width = min(int(candidate_width), MAX_WIDTH, len(pool))
        local = self._local_observations(through_ordinal=trigger.ordinal)
        if trigger.receipt_id not in {item.receipt_id for item in local}:
            local = (*local, trigger)
            local = tuple(sorted(local, key=lambda item: (item.ordinal, item.receipt_id)))
            if len(local) > self.config.local_observation_cap:
                # Preserve the trigger while keeping the explicit local-row
                # bound even for a caller that supplies an out-of-order event.
                prior = tuple(
                    item for item in local
                    if item.receipt_id != trigger.receipt_id
                )
                keep_count = max(0, self.config.local_observation_cap - 1)
                kept_prior = prior[-keep_count:] if keep_count else ()
                local = tuple(sorted(
                    (*kept_prior, trigger),
                    key=lambda item: (item.ordinal, item.receipt_id),
                ))

        # The current trigger is the only source of the newborn polarity.  All
        # other rows are merely opaque contrastive evidence for proposal rank.
        canonical_pool = tuple(sorted(set(pool)))
        hash_pool = tuple(sorted(
            canonical_pool,
            key=lambda item: _priority(
                self.config.genome_seed,
                ordinal,
                0,
                item,
            ),
        ))
        local_sets = tuple(
            (set(observation.signal_ids), observation.observed)
            for observation in local
        )
        # Divide the finite budget before any width is searched.  This is
        # deliberately not a remainder-of-budget calculation: a large signal
        # vocabulary may consume width one, but it may not starve widths two
        # and three.
        base_budget, remainder = divmod(
            self.config.candidate_search_budget,
            maximum_width,
        )
        width_budgets = tuple(
            base_budget + int(index < remainder)
            for index in range(maximum_width)
        )
        ranked_by_width: dict[int, tuple[tuple[str, ...], ...]] = {}
        row_lookup: dict[
            tuple[str, ...], tuple[tuple[int, int], bytes]
        ] = {}

        def score_key(
            members: tuple[str, ...],
        ) -> tuple[float, int, int, int, bytes]:
            (support, contradiction), priority = row_lookup[members]
            lower = wilson_lower_bound(
                support,
                support + contradiction,
                self.config.wilson_z,
            )
            # A first contradiction triggers local abstention/refinement, not
            # death; later exhaustion or bounded capacity may retire the
            # lineage. Reliability still outranks raw support in this score.
            return (
                -lower,
                -support,
                contradiction,
                len(members),
                priority,
            )

        previous_beam: tuple[tuple[str, ...], ...] = ()
        for width, width_budget in enumerate(width_budgets, start=1):
            if width == 1:
                exploitation = iter(combinations(canonical_pool, 1))
            else:
                def extend_beam(
                    beam: tuple[tuple[str, ...], ...],
                ) -> Iterable[tuple[str, ...]]:
                    # Interleave prefixes instead of exhausting the first
                    # one.  This makes the finite width slice a genuine
                    # breadth-limited beam: every retained residual gets a
                    # chance to extend before one prefix consumes the slice.
                    for member in canonical_pool:
                        for prefix in beam:
                            prefix_set = set(prefix)
                            if member not in prefix_set:
                                yield tuple(sorted((*prefix, member)))

                exploitation = iter(extend_beam(previous_beam))
            exploration = iter(combinations(hash_pool, width))
            streams = (exploitation, exploration)
            exhausted = [False, False]
            seen: set[tuple[str, ...]] = set()
            width_rows: list[tuple[str, ...]] = []
            width_evaluated = 0
            exploration_evaluated = 0
            exploration_quota = max(
                1,
                min(
                    width_budget,
                    width_budget // EXPLORATION_QUOTA_DIVISOR,
                ),
            )
            stream_index = 1  # Start with hash exploration at every width.
            while width_evaluated < width_budget:
                if exhausted[0] and exhausted[1]:
                    break
                # Reserve the exploration quota first.  Afterwards alternate
                # both streams, so exploitation cannot monopolize the slice
                # while the hash order still has unseen candidates.
                if exploration_evaluated < exploration_quota:
                    selected_stream = 1
                else:
                    selected_stream = stream_index % len(streams)
                    stream_index += 1
                if exhausted[selected_stream]:
                    selected_stream = 1 - selected_stream
                    if exhausted[selected_stream]:
                        break
                try:
                    raw_members = next(streams[selected_stream])
                except StopIteration:
                    exhausted[selected_stream] = True
                    continue
                members = tuple(sorted(raw_members))
                if members in seen:
                    continue
                seen.add(members)
                width_rows.append(members)
                width_evaluated += 1
                if selected_stream == 1:
                    exploration_evaluated += 1
                support = 0
                contradiction = 0
                member_set = set(members)
                for active, observed in local_sets:
                    if not member_set.issubset(active):
                        continue
                    if observed is polarity:
                        support += 1
                    else:
                        contradiction += 1
                priority = _priority(
                    self.config.genome_seed,
                    ordinal,
                    width,
                    "\x1f".join(members),
                )
                row_lookup[members] = ((support, contradiction), priority)

            ranked = tuple(sorted(width_rows, key=score_key))
            previous_beam = ranked[: self.config.candidate_beam_width]
            ranked_by_width[width] = previous_beam

        # Emit one best candidate for each available arity, retaining the
        # historical at-most-three birth contract while the staged beams above
        # control which wider residuals are actually reachable.
        selected = tuple(
            ranked_by_width[width][0]
            for width in range(1, maximum_width + 1)
            if ranked_by_width.get(width)
        )
        return tuple(
            sorted(
                selected,
                key=score_key,
            )
        )[: self.config.max_candidates_per_demand]

    def _born_for(self, demand: BoundaryExpandDemand) -> tuple[BoundarySketch, ...]:
        return tuple(
            self._sketches[sketch_id]
            for sketch_id in self._demand_birth_ids.get(demand.ordinal, ())
        )

    def observe(self, observation: BoundaryObservation) -> bool:
        """Accept one unique receipt and update every matching sketch."""

        if not isinstance(observation, BoundaryObservation):
            raise TypeError("observe requires BoundaryObservation")
        if observation.receipt_id in self._observations or observation.physical_id in self._physical:
            self._duplicate_rejections += 1
            raise DuplicatePhysicalReceiptError("duplicate receipt or physical interaction")
        if observation.ordinal in self._ordinals:
            self._duplicate_rejections += 1
            raise DuplicatePhysicalReceiptError("duplicate observation ordinal")
        self._observations[observation.receipt_id] = observation
        self._physical[observation.physical_id] = observation.receipt_id
        self._ordinals[observation.ordinal] = observation.receipt_id
        order_index = bisect_left(
            self._observation_ordinals, observation.ordinal
        )
        self._observation_ordinals.insert(order_index, observation.ordinal)
        self._observation_receipt_order.insert(
            order_index, observation.receipt_id
        )
        self._local_receipt_ids.append(observation.receipt_id)
        self._local_receipt_ids.sort(
            key=lambda receipt_id: (
                self._observations[receipt_id].ordinal,
                receipt_id,
            )
        )
        if len(self._local_receipt_ids) > self.config.local_observation_cap:
            del self._local_receipt_ids[: -self.config.local_observation_cap]
        self._frontier = max(self._frontier, observation.ordinal)
        self._last_refinement_ids = ()
        active = set(observation.signal_ids)
        for sketch_id in tuple(sorted(self._active_ids)):
            candidate = self._sketches[sketch_id]
            if not self._is_live(candidate):
                self._deindex_live_sketch(candidate)
                continue
            reads = set(candidate.read_receipt_ids)
            matches = all(
                member in active for member in candidate.members
            )
            positive = set(candidate.positive_receipt_ids)
            negative = set(candidate.negative_receipt_ids)
            lifetime_match = candidate.lifetime_match_count
            lifetime_support = candidate.lifetime_support_count
            lifetime_contradiction = candidate.lifetime_contradiction_count
            evidence_digest = candidate.evidence_digest
            if matches:
                is_support = observation.observed is candidate.polarity
                lifetime_match += 1
                evidence_digest = _mix_evidence_digest(
                    evidence_digest,
                    observation,
                )
                if is_support:
                    lifetime_support += 1
                else:
                    lifetime_contradiction += 1
                # Keep a bounded local evidence cache.  Exact support and
                # contradiction totals live in scalar counters; only the
                # receipts needed for a local gate are retained here.
                if (
                    is_support
                    and candidate.support_count < self.config.minimum_support
                    and len(positive) < MAX_RETAINED_SUPPORT_RECEIPTS
                ):
                    positive.add(observation.receipt_id)
                    reads.add(observation.receipt_id)
                elif (
                    not is_support
                    and candidate.contradiction_count < max(
                        MIN_CONTRADICTIONS_BEFORE_DEATH,
                        self.config.refinement_child_cap,
                    )
                    and len(negative) < MAX_RETAINED_CONTRADICTION_RECEIPTS
                ):
                    negative.add(observation.receipt_id)
                    reads.add(observation.receipt_id)
            contradiction = candidate.polarity is not observation.observed and matches
            state = candidate.state
            reason = candidate.retirement_reason
            abstained = set(candidate.abstained_receipt_ids)
            refinement_receipts = set(candidate.refinement_receipt_ids)
            residual_sketch_ids = set(candidate.residual_sketch_ids)
            if contradiction and state is SketchLifecycle.ACTIVE:
                # The coarse conjunction must abstain from this region, but
                # its lineage remains alive while a local residual beam is
                # tried.  A first contradiction is therefore never death.
                state = SketchLifecycle.REFINING
                reason = "contrast_requires_residual_refinement"
                if len(refinement_receipts) < self.config.refinement_event_cap:
                    abstained.add(observation.receipt_id)
                    refinement_receipts.add(observation.receipt_id)
                    refinement_ids = self._spawn_residual_refinements(
                        candidate,
                        observation,
                    )
                else:
                    refinement_ids = ()
                self._last_refinement_ids = tuple(sorted(set(
                    (*self._last_refinement_ids, *refinement_ids)
                )))
                residual_sketch_ids.update(refinement_ids)
                self._prune_counts["contradiction"] += 1
            elif contradiction and state is SketchLifecycle.REFINING:
                # New contrast may reveal a different missing local feature.
                # Do not retry indefinitely; the event cap is part of the
                # deterministic ecology state.
                if (
                    observation.receipt_id not in refinement_receipts
                    and len(refinement_receipts) < self.config.refinement_event_cap
                ):
                    abstained.add(observation.receipt_id)
                    refinement_receipts.add(observation.receipt_id)
                    refinement_ids = self._spawn_residual_refinements(
                        candidate,
                        observation,
                    )
                    self._last_refinement_ids = tuple(sorted(set(
                        (*self._last_refinement_ids, *refinement_ids)
                    )))
                    residual_sketch_ids.update(refinement_ids)
                    self._prune_counts["contradiction"] += 1
            if contradiction and len(reads) < MAX_RETAINED_READ_RECEIPTS:
                # This is only a bounded event-time cache.  The complete
                # observation remains in ``_observations`` for certification;
                # it must not make the active candidate scan grow with age.
                reads.add(observation.receipt_id)
            if state is SketchLifecycle.REFINING:
                terminal = self._exhausted_refinement_state(
                    sketch_id,
                    len(refinement_receipts),
                )
                if terminal is not None:
                    state, reason = terminal
            updated = BoundarySketch(
                sketch_id=candidate.sketch_id,
                members=candidate.members,
                birth_ordinal=candidate.birth_ordinal,
                triggering_receipt_id=candidate.triggering_receipt_id,
                polarity=candidate.polarity,
                state=state,
                positive_receipt_ids=tuple(sorted(positive)),
                negative_receipt_ids=tuple(sorted(negative)),
                read_receipt_ids=tuple(sorted(reads)),
                last_observation_ordinal=max(
                    candidate.last_observation_ordinal
                    if candidate.last_observation_ordinal is not None
                    else observation.ordinal,
                    observation.ordinal,
                ),
                retirement_reason=reason,
                parent_sketch_id=candidate.parent_sketch_id,
                refinement_source_receipt_id=candidate.refinement_source_receipt_id,
                abstained_receipt_ids=tuple(sorted(abstained)),
                refinement_receipt_ids=tuple(sorted(refinement_receipts)),
                residual_sketch_ids=tuple(sorted(residual_sketch_ids))[
                    :MAX_RETAINED_RESIDUAL_IDS
                ],
                lifetime_match_count=lifetime_match,
                lifetime_support_count=lifetime_support,
                lifetime_contradiction_count=lifetime_contradiction,
                evidence_digest=evidence_digest,
            )
            self._store_sketch(updated)
        return True

    def observe_many(self, observations: Iterable[BoundaryObservation]) -> tuple[bool, ...]:
        return tuple(self.observe(item) for item in sorted(observations, key=lambda item: (item.ordinal, item.receipt_id)))

    def _residual_child_ids(self, parent_id: str) -> tuple[str, ...]:
        parent = self._sketches.get(parent_id)
        referenced = set(() if parent is None else parent.residual_sketch_ids)
        referenced.update(self._live_residual_index.get(parent_id, ()))
        return tuple(sorted(
            candidate_id
            for candidate_id in referenced
            if candidate_id in self._sketches
            and self._is_live(self._sketches[candidate_id])
            and parent is not None
            and set(parent.members) < set(self._sketches[candidate_id].members)
        ))

    def _exhausted_refinement_state(
        self,
        candidate_id: str,
        refinement_count: int,
    ) -> tuple[SketchLifecycle, str] | None:
        """Return the terminal state once a parent's refinement budget is spent.

        A refining parent is an active event consumer only while it still has
        refinement budget.  At the cap, a live strict residual can continue
        the local ecology while the parent becomes a dormant historical shell;
        without one, the contradicted parent is dead.  Checking child
        lifecycle (rather than merely a retained ID) prevents a dead/dormant
        child from keeping the parent in the hot path forever.
        """

        if refinement_count < self.config.refinement_event_cap:
            return None
        if self._residual_child_ids(candidate_id):
            return SketchLifecycle.DORMANT, "residual_refinement"
        return SketchLifecycle.DEAD, "exhausted_refinement_budget"

    def _death_eligible(self, candidate: BoundarySketch) -> bool:
        """Apply the bounded death policy after refinement has had a chance."""

        if candidate.state is not SketchLifecycle.REFINING:
            return False
        if len(candidate.refinement_receipt_ids) >= self.config.refinement_event_cap:
            # Budget exhaustion is terminal even when the coarse parent had
            # high support; without a live residual there is no safe reason
            # to keep matching it.  This check precedes the bounded support
            # test so small-cap configurations obey the same rule.
            return not self._residual_child_ids(candidate.sketch_id)
        if len(candidate.refinement_receipt_ids) < MIN_CONTRADICTIONS_BEFORE_DEATH:
            return False
        if candidate.support_count + candidate.contradiction_count < self.config.minimum_support:
            return False
        if self._residual_child_ids(candidate.sketch_id):
            return False
        # A high-support candidate with a small amount of contrast remains a
        # dormant refinement parent rather than being declared dead.  Death
        # requires the bounded local utility to be no better than chance.
        return candidate.lower_bound(self.config.wilson_z) < self.config.lower_bound_threshold

    def settle_refinements(self) -> tuple[BoundarySketch, ...]:
        """Close refinement rounds at a caller-chosen safe point.

        Event ingestion can create local buds, but a caller controls when
        lifecycle changes become visible to authority.  Parents with a live
        residual child become dormant; exhausted parents die only after the
        bounded evidence/utility criteria in :meth:`_death_eligible` hold.
        """

        changed: list[BoundarySketch] = []
        for candidate in tuple(self.active_sketches):
            if candidate.state is not SketchLifecycle.REFINING:
                continue
            children = self._residual_child_ids(candidate.sketch_id)
            if children:
                state = SketchLifecycle.DORMANT
                reason = "residual_refinement"
            elif self._death_eligible(candidate):
                state = SketchLifecycle.DEAD
                reason = "exhausted_refinement_utility"
            else:
                continue
            updated = BoundarySketch(
                sketch_id=candidate.sketch_id,
                members=candidate.members,
                birth_ordinal=candidate.birth_ordinal,
                triggering_receipt_id=candidate.triggering_receipt_id,
                polarity=True,
                state=state,
                positive_receipt_ids=candidate.positive_receipt_ids,
                negative_receipt_ids=candidate.negative_receipt_ids,
                read_receipt_ids=candidate.read_receipt_ids,
                last_observation_ordinal=candidate.last_observation_ordinal,
                retirement_reason=reason,
                parent_sketch_id=candidate.parent_sketch_id,
                refinement_source_receipt_id=candidate.refinement_source_receipt_id,
                abstained_receipt_ids=candidate.abstained_receipt_ids,
                refinement_receipt_ids=candidate.refinement_receipt_ids,
                residual_sketch_ids=candidate.residual_sketch_ids,
                lifetime_match_count=candidate.lifetime_match_count,
                lifetime_support_count=candidate.lifetime_support_count,
                lifetime_contradiction_count=candidate.lifetime_contradiction_count,
                evidence_digest=candidate.evidence_digest,
            )
            self._store_sketch(updated)
            changed.append(updated)
        return tuple(changed)

    def _evict_for_capacity(self, *, exclude_ids: Iterable[str] = ()) -> None:
        excluded = frozenset(str(item) for item in exclude_ids)
        active = tuple(
            item for item in self.active_sketches
            if item.sketch_id not in excluded
        )
        if not active:
            return
        victim = min(
            active,
            key=lambda item: (
                item.lower_bound(self.config.wilson_z),
                item.support_count,
                -item.contradiction_count,
                -item.arity,
                item.sketch_id,
            ),
        )
        updated = BoundarySketch(
            victim.sketch_id,
            victim.members,
            victim.birth_ordinal,
            victim.triggering_receipt_id,
            victim.polarity,
            SketchLifecycle.DORMANT,
            victim.positive_receipt_ids,
            victim.negative_receipt_ids,
            victim.read_receipt_ids,
            victim.last_observation_ordinal,
            "capacity_pressure",
            victim.parent_sketch_id,
            victim.refinement_source_receipt_id,
            victim.abstained_receipt_ids,
            victim.refinement_receipt_ids,
            victim.residual_sketch_ids,
            lifetime_match_count=victim.lifetime_match_count,
            lifetime_support_count=victim.lifetime_support_count,
            lifetime_contradiction_count=victim.lifetime_contradiction_count,
            evidence_digest=victim.evidence_digest,
        )
        self._store_sketch(updated)
        self._prune_counts["capacity"] += 1

    def rank_candidates(self) -> tuple[BoundarySketch, ...]:
        # Refining parents are intentionally absent from the promotion beam:
        # they abstain until a residual child earns its own independent
        # positive certificate.
        return tuple(sorted(
            (
                item for item in self.active_sketches
                if item.state is SketchLifecycle.ACTIVE
            ),
            key=lambda item: (
                -item.lower_bound(self.config.wilson_z),
                -item.support_count,
                item.contradiction_count,
                item.arity,
                item.sketch_id,
            ),
        ))

    def mark_promoted(self, candidate_id: str) -> BoundarySketch:
        """Retire one accepted sketch using its bounded local gate."""

        candidate = self._sketches.get(str(candidate_id))
        if candidate is None:
            raise ValueError("unknown promoted candidate")
        if candidate.state is not SketchLifecycle.ACTIVE:
            raise ValueError("only an active candidate can be promoted")
        # Commit-time retirement must stay bounded as the ecology ages.  The
        # authority request carries the same bounded gate plus its scalar
        # lifetime counts; a complete ledger reclosure is an explicit audit
        # operation only, never part of recurring learning.
        decision = self.promotion_decision(candidate.sketch_id)
        if not decision.eligible:
            raise ValueError("ineligible candidate cannot be promoted")
        promoted = BoundarySketch(
            candidate.sketch_id,
            candidate.members,
            candidate.birth_ordinal,
            candidate.triggering_receipt_id,
            candidate.polarity,
            SketchLifecycle.DORMANT,
            candidate.positive_receipt_ids,
            candidate.negative_receipt_ids,
            candidate.read_receipt_ids,
            candidate.last_observation_ordinal,
            "promoted",
            candidate.parent_sketch_id,
            candidate.refinement_source_receipt_id,
            candidate.abstained_receipt_ids,
            candidate.refinement_receipt_ids,
            candidate.residual_sketch_ids,
            lifetime_match_count=candidate.lifetime_match_count,
            lifetime_support_count=candidate.lifetime_support_count,
            lifetime_contradiction_count=candidate.lifetime_contradiction_count,
            evidence_digest=candidate.evidence_digest,
        )
        self._store_sketch(promoted)
        return promoted

    def retire_redundant(self, candidate_id: str) -> BoundarySketch:
        """Dorm one sketch already represented by the committed authority."""

        candidate = self._sketches.get(str(candidate_id))
        if candidate is None:
            raise ValueError("unknown redundant candidate")
        if candidate.state is not SketchLifecycle.ACTIVE:
            raise ValueError("only an active candidate can be retired")
        retired = BoundarySketch(
            candidate.sketch_id,
            candidate.members,
            candidate.birth_ordinal,
            candidate.triggering_receipt_id,
            candidate.polarity,
            SketchLifecycle.DORMANT,
            candidate.positive_receipt_ids,
            candidate.negative_receipt_ids,
            candidate.read_receipt_ids,
            candidate.last_observation_ordinal,
            "redundant_authority_pattern",
            candidate.parent_sketch_id,
            candidate.refinement_source_receipt_id,
            candidate.abstained_receipt_ids,
            candidate.refinement_receipt_ids,
            candidate.residual_sketch_ids,
            lifetime_match_count=candidate.lifetime_match_count,
            lifetime_support_count=candidate.lifetime_support_count,
            lifetime_contradiction_count=candidate.lifetime_contradiction_count,
            evidence_digest=candidate.evidence_digest,
        )
        self._store_sketch(retired)
        self._prune_counts["redundant_authority_pattern"] += 1
        return retired

    def _full_promotion_audit(
        self,
        candidate: BoundarySketch,
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        """Reclose one candidate against the complete REAL ledger.

        This intentionally remains an explicit, authority-bound operation.
        Ordinary event-time promotion gates use the candidate-local vectors
        instead; callers that need an exact exclusion set must opt into this
        full audit before submitting an authority request.
        """

        members = set(candidate.members)
        matching: list[BoundaryObservation] = []
        inspected: list[str] = []
        start = bisect_left(
            self._observation_ordinals, candidate.birth_ordinal
        )
        for receipt_id in self._observation_receipt_order[start:]:
            item = self._observations[receipt_id]
            inspected.append(item.receipt_id)
            if members.issubset(item.signal_ids):
                matching.append(item)
        support = tuple(
            item.receipt_id
            for item in matching
            if item.observed is candidate.polarity
        )
        contrast = tuple(
            item.receipt_id
            for item in matching
            if item.observed is not candidate.polarity
        )
        return support, contrast, tuple(inspected)

    def promotion_decision(
        self,
        candidate_id: str | None = None,
        *,
        full_audit: bool = False,
    ) -> PromotionDecision:
        """Return a bounded local gate or an explicit full certification audit.

        The default path never scans ``_observations``: it uses the bounded
        candidate cache and is safe for recurring event-time ranking.  Set
        ``full_audit=True`` only at the authority handoff boundary; that path
        reconstructs the complete post-birth support and exclusion set.
        """

        ranked = self.rank_candidates()
        candidate = self._sketches.get(candidate_id) if candidate_id else (ranked[0] if ranked else None)
        ranked_ids = tuple(item.sketch_id for item in ranked)
        if candidate is None:
            return PromotionDecision(None, (), None, False, None, None, 0, 0, 0.0, (), (), (), (), ranked_ids, "no_candidate")
        if full_audit:
            support, contrast, inspected = self._full_promotion_audit(candidate)
            support_count = len(support)
            contradiction_count = len(contrast)
        else:
            support = candidate.supporting_receipt_ids
            contrast = candidate.contradicting_receipt_ids
            inspected = candidate.read_receipt_ids
            support_count = candidate.support_count
            contradiction_count = candidate.contradiction_count
        lower = wilson_lower_bound(
            support_count,
            support_count + contradiction_count,
            self.config.wilson_z,
        )
        eligible = (
            candidate.state is SketchLifecycle.ACTIVE
            and candidate.polarity is True
            and support_count >= self.config.minimum_support
            and contradiction_count == 0
            and lower >= self.config.lower_bound_threshold
        )
        if candidate.state is not SketchLifecycle.ACTIVE:
            reason = f"lifecycle_{candidate.state.value.lower()}"
        elif support_count < self.config.minimum_support or candidate.polarity is not True:
            reason = "insufficient_support"
        elif contradiction_count:
            reason = "contradiction"
        elif lower < 0.55:
            reason = "wilson_lower_bound_below_threshold"
        else:
            reason = "eligible"
        if full_audit:
            order = lambda ids: tuple(sorted(
                ids,
                key=lambda key: (self._observations[key].ordinal, key),
            ))
            support_for_decision = order(support)
            contrast_for_decision = order(contrast)
        else:
            # Candidate vectors are already canonicalized by BoundarySketch;
            # ordering them here must not look up the unbounded REAL ledger.
            support_for_decision = tuple(support)
            contrast_for_decision = tuple(contrast)
        interval = None
        if full_audit and inspected:
            interval = (
                self._observations[inspected[0]].ordinal,
                self._observations[inspected[-1]].ordinal,
            )
        return PromotionDecision(
            candidate.sketch_id,
            candidate.members,
            candidate.triggering_receipt_id,
            eligible,
            candidate.polarity,
            candidate.state,
            support_count,
            contradiction_count,
            lower,
            support_for_decision,
            contrast_for_decision,
            inspected,
            inspected,
            ranked_ids,
            reason,
            interval,
        )

    def _reconcile_failed_full_audit(
        self,
        decision: PromotionDecision,
    ) -> BoundarySketch:
        """Commit one exact-audit failure into the local lifecycle.

        Residual buds may be grounded in a historical positive receipt.  Their
        bounded event-time cache intentionally does not replay the intervening
        ledger, so the first exact promotion audit can discover older contrast
        that the cheap local gate has not seen.  That discovery is itself
        evidence: leave ACTIVE immediately, attempt one bounded residual
        refinement, and replace scalar counters with the exact post-birth
        totals.  Consequently the same failed candidate cannot trigger a
        growing full-ledger audit again on every later event.
        """

        if decision.candidate_id is None:
            raise ValueError("failed audit lacks a candidate")
        candidate = self._sketches.get(decision.candidate_id)
        if candidate is None or candidate.state is not SketchLifecycle.ACTIVE:
            raise ValueError("failed audit candidate is not active")
        if decision.eligible:
            raise ValueError("eligible audit cannot be reconciled as failure")
        if (
            not decision.inspected_receipt_ids
            or decision.inspected_ordinal_interval is None
            or decision.inspected_ordinal_interval[0]
            != candidate.birth_ordinal
            or decision.inspected_ordinal_interval[1] != self._frontier
        ):
            raise ValueError("failed audit is not current and complete")

        support_ids = tuple(decision.supporting_receipt_ids)
        contrast_ids = tuple(decision.contradicting_receipt_ids)
        matching_ids = tuple(sorted(
            {*support_ids, *contrast_ids},
            key=lambda receipt_id: (
                self._observations[receipt_id].ordinal,
                receipt_id,
            ),
        ))
        if (
            candidate.triggering_receipt_id not in support_ids
            or len(matching_ids)
            != decision.support_count + decision.contradiction_count
        ):
            raise ValueError("failed audit evidence is not self-consistent")

        def bounded_with_required(
            receipt_ids: Sequence[str],
            *,
            limit: int,
            required: Sequence[str] = (),
        ) -> tuple[str, ...]:
            available = set(receipt_ids)
            chosen = [
                receipt_id for receipt_id in sorted(set(required))
                if receipt_id in available
            ][:limit]
            chosen.extend(
                receipt_id for receipt_id in sorted(available)
                if receipt_id not in chosen
            )
            return tuple(sorted(chosen[:limit]))

        positives = bounded_with_required(
            support_ids,
            limit=MAX_RETAINED_SUPPORT_RECEIPTS,
            required=(candidate.triggering_receipt_id,),
        )
        negatives: tuple[str, ...] = ()
        abstained = set(candidate.abstained_receipt_ids)
        refinement_receipts = set(candidate.refinement_receipt_ids)
        residual_ids = set(candidate.residual_sketch_ids)
        refinement_ids: tuple[str, ...] = ()

        if contrast_ids:
            contradiction_id = min(
                contrast_ids,
                key=lambda receipt_id: (
                    self._observations[receipt_id].ordinal,
                    receipt_id,
                ),
            )
            contradiction = self._observations[contradiction_id]
            # Retain only contrasts that have actually entered the bounded
            # refinement budget.  The exact scalar counter already commits
            # every other hidden contrast; keeping extra receipt IDs here
            # could make later abstentions exceed the fixed read cache.
            negatives = bounded_with_required(
                (*candidate.negative_receipt_ids, contradiction_id),
                limit=MAX_RETAINED_CONTRADICTION_RECEIPTS,
                required=(contradiction_id,),
            )
            state = SketchLifecycle.REFINING
            reason = "exact_audit_contrast_requires_residual_refinement"
            if (
                contradiction_id not in refinement_receipts
                and len(refinement_receipts)
                < self.config.refinement_event_cap
            ):
                abstained.add(contradiction_id)
                refinement_receipts.add(contradiction_id)
                refinement_ids = self._spawn_residual_refinements(
                    candidate,
                    contradiction,
                )
                residual_ids.update(refinement_ids)
                self._last_refinement_ids = tuple(sorted({
                    *self._last_refinement_ids,
                    *refinement_ids,
                }))
                self._prune_counts["contradiction"] += 1
            terminal = self._exhausted_refinement_state(
                candidate.sketch_id,
                len(refinement_receipts),
            )
            if terminal is not None:
                state, reason = terminal
        else:
            # A locally eligible candidate with no exact contrast should also
            # be exactly eligible.  Treat any other discrepancy as a dormant,
            # fail-closed tombstone rather than scheduling repeated audits.
            state = SketchLifecycle.DORMANT
            reason = "exact_audit_ineligible"

        evidence_digest = "0" * 64
        for receipt_id in matching_ids:
            evidence_digest = _mix_evidence_digest(
                evidence_digest,
                self._observations[receipt_id],
            )
        reads = tuple(sorted({
            candidate.triggering_receipt_id,
            *positives,
            *negatives,
            *abstained,
        }))
        if len(reads) > MAX_RETAINED_READ_RECEIPTS:
            raise ValueError("failed audit reconciliation exceeds read bound")
        updated = BoundarySketch(
            sketch_id=candidate.sketch_id,
            members=candidate.members,
            birth_ordinal=candidate.birth_ordinal,
            triggering_receipt_id=candidate.triggering_receipt_id,
            polarity=candidate.polarity,
            state=state,
            positive_receipt_ids=positives,
            negative_receipt_ids=negatives,
            read_receipt_ids=reads,
            last_observation_ordinal=self._frontier,
            retirement_reason=reason,
            parent_sketch_id=candidate.parent_sketch_id,
            refinement_source_receipt_id=(
                candidate.refinement_source_receipt_id
            ),
            abstained_receipt_ids=tuple(sorted(abstained)),
            refinement_receipt_ids=tuple(sorted(refinement_receipts)),
            residual_sketch_ids=tuple(sorted(residual_ids))[
                :MAX_RETAINED_RESIDUAL_IDS
            ],
            lifetime_match_count=len(matching_ids),
            lifetime_support_count=len(support_ids),
            lifetime_contradiction_count=len(contrast_ids),
            evidence_digest=evidence_digest,
        )
        self._store_sketch(updated)
        return updated

    def audit_promotion_at_safe_point(
        self,
        candidate_id: str,
    ) -> PromotionDecision:
        """Audit one locally eligible bud once and reconcile exact failure."""

        local = self.promotion_decision(candidate_id)
        if not local.eligible:
            return local
        audited = self.promotion_decision(
            candidate_id,
            full_audit=True,
        )
        if not audited.eligible:
            self._reconcile_failed_full_audit(audited)
        return audited

    def manifest(self) -> dict[str, Any]:
        self._verify_live_indexes()
        observations = tuple(
            self._observations[receipt_id]
            for receipt_id in self._observation_receipt_order
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "implementation_identity": IMPLEMENTATION_IDENTITY,
            "receipt_kind": REAL_RECEIPT_KIND,
            "config": self.config.to_manifest(),
            "frontier_ordinal": self._frontier,
            "lifetime_birth_count": self._births,
            "capacity_rejections": self._capacity_rejections,
            "duplicate_rejections": self._duplicate_rejections,
            "prune_counts": dict(self._prune_counts),
            "last_refinement_ids": list(self._last_refinement_ids),
            "demands": [self._demands[key].to_manifest() for key in sorted(self._demands)],
            "observations": [item.to_manifest() for item in observations],
            "sketches": [self._sketches[key].to_manifest() for key in sorted(self._sketches)],
            "tombstones": [self._tombstones[key].to_manifest() for key in sorted(self._tombstones)],
        }

    to_manifest = manifest

    def dumps(self) -> str:
        return json.dumps(self.manifest(), sort_keys=True, separators=(",", ":"))

    def manifest_digest(self) -> str:
        return _digest(self.manifest())

    @classmethod
    def loads(cls, value: str | bytes) -> "ProspectiveBoundaryCandidateEcology":
        return cls.from_manifest(json.loads(value))

    @classmethod
    def from_manifest(cls, value: Mapping[str, Any]) -> "ProspectiveBoundaryCandidateEcology":
        if value.get("schema_version") != SCHEMA_VERSION or value.get("implementation_identity") != IMPLEMENTATION_IDENTITY:
            raise ValueError("unsupported boundary ecology manifest")
        ecology = cls(BoundaryEcologyConfig(**value.get("config", {})))
        for item in value.get("demands", ()):
            demand = BoundaryExpandDemand.from_manifest(item)
            ecology._demands[demand.ordinal] = demand
        for item in value.get("observations", ()):
            observation = BoundaryObservation.from_manifest(item)
            if observation.receipt_id in ecology._observations or observation.physical_id in ecology._physical or observation.ordinal in ecology._ordinals:
                raise ValueError("duplicate observation in manifest")
            ecology._observations[observation.receipt_id] = observation
            ecology._physical[observation.physical_id] = observation.receipt_id
            ecology._ordinals[observation.ordinal] = observation.receipt_id
        ecology._local_receipt_ids = [
            item.receipt_id
            for item in sorted(
                ecology._observations.values(),
                key=lambda item: (item.ordinal, item.receipt_id),
            )[-ecology.config.local_observation_cap :]
        ]
        for item in value.get("sketches", ()):
            candidate = BoundarySketch.from_manifest(item)
            ecology._sketches[candidate.sketch_id] = candidate
            if ecology._is_live(candidate):
                ecology._active_ids.add(candidate.sketch_id)
        for item in value.get("tombstones", ()):
            candidate = BoundarySketch.from_manifest(item)
            existing = ecology._sketches.get(candidate.sketch_id)
            if existing is not None and existing != candidate:
                raise ValueError("tombstone differs from sketch")
            ecology._tombstones[candidate.sketch_id] = candidate
        ecology._rebuild_live_indexes()
        ecology._frontier = int(value.get("frontier_ordinal", -1))
        ecology._births = int(value.get("lifetime_birth_count", len(ecology._sketches)))
        ecology._capacity_rejections = int(value.get("capacity_rejections", 0))
        ecology._duplicate_rejections = int(value.get("duplicate_rejections", 0))
        ecology._prune_counts.update(value.get("prune_counts", {}))
        ecology._last_refinement_ids = tuple(
            str(item) for item in value.get("last_refinement_ids", ())
        )
        if tuple(sorted(set(ecology._last_refinement_ids))) != ecology._last_refinement_ids:
            raise ValueError("manifest last refinements are not canonical")
        for demand in ecology._demands.values():
            trigger = ecology._observations.get(demand.triggering_receipt_id)
            if (
                trigger is None
                or trigger.ordinal != demand.ordinal
                or trigger.observed is not True
                or demand.polarity is not True
                or not set(demand.signal_ids).issubset(trigger.signal_ids)
            ):
                raise ValueError("manifest contains an invalid EXPAND demand")
        for candidate in ecology._sketches.values():
            trigger = ecology._observations.get(
                candidate.triggering_receipt_id
            )
            if (
                trigger is None
                or trigger.ordinal != candidate.birth_ordinal
                or trigger.observed is not True
                or candidate.polarity is not True
                or not set(candidate.members).issubset(trigger.signal_ids)
            ):
                raise ValueError("manifest contains an invalid boundary sketch")
            if (
                candidate.refinement_source_receipt_id is not None
                and candidate.refinement_source_receipt_id
                not in ecology._observations
            ):
                raise ValueError("manifest contains an unknown refinement source")
            if (
                candidate.refinement_source_receipt_id is not None
                and ecology._observations[candidate.refinement_source_receipt_id].observed
                is not False
            ):
                raise ValueError("manifest refinement source is not a contrast")
            if (
                candidate.parent_sketch_id is not None
                and candidate.parent_sketch_id not in ecology._sketches
            ):
                raise ValueError("manifest contains an unknown refinement parent")
            if any(
                residual_id not in ecology._sketches
                for residual_id in candidate.residual_sketch_ids
            ):
                raise ValueError("manifest contains an unknown residual reference")
            if (
                candidate.state is SketchLifecycle.REFINING
                and len(candidate.refinement_receipt_ids)
                >= ecology.config.refinement_event_cap
            ):
                raise ValueError(
                    "manifest contains an exhausted refining candidate"
                )
        inactive_ids = {
            item.sketch_id for item in ecology._sketches.values()
            if not ecology._is_live(item)
        }
        if set(ecology._tombstones) != inactive_ids:
            raise ValueError("manifest tombstones differ from inactive sketches")
        if any(item not in ecology._sketches for item in ecology._last_refinement_ids):
            raise ValueError("manifest contains an unknown last refinement")
        expected_frontier = max(
            (*ecology._ordinals, *ecology._demands), default=-1
        )
        if ecology._frontier != expected_frontier:
            raise ValueError("manifest frontier differs from accepted events")
        if ecology._births != len(ecology._sketches):
            raise ValueError("manifest lifetime birth count is inconsistent")
        if ecology.active_sketch_count > ecology.config.active_sketch_cap:
            raise ValueError("manifest exceeds active sketch cap")
        return ecology


__all__ = [
    "SCHEMA_VERSION", "IMPLEMENTATION_IDENTITY", "REAL_RECEIPT_KIND",
    "MAX_WIDTH", "DEFAULT_CANDIDATE_BEAM_WIDTH",
    "MAX_CANDIDATE_BEAM_WIDTH", "DEFAULT_CANDIDATE_SEARCH_BUDGET",
    "MAX_CANDIDATE_SEARCH_BUDGET", "DEFAULT_LOCAL_OBSERVATION_CAP",
    "MAX_LOCAL_OBSERVATION_CAP", "DEFAULT_REFINEMENT_CHILD_CAP",
    "MAX_REFINEMENT_CHILD_CAP", "DEFAULT_REFINEMENT_EVENT_CAP",
    "MAX_REFINEMENT_EVENT_CAP", "MIN_CONTRADICTIONS_BEFORE_DEATH",
    "MAX_RETAINED_SUPPORT_RECEIPTS", "MAX_RETAINED_CONTRADICTION_RECEIPTS",
    "MAX_RETAINED_REFINEMENT_RECEIPTS", "MAX_RETAINED_READ_RECEIPTS",
    "MAX_RETAINED_RESIDUAL_IDS",
    "BoundaryObservation", "GroundedBoundaryObservation", "BoundaryExpandDemand",
    "SketchLifecycle", "BoundarySketch", "PromotionDecision",
    "BoundaryEcologyConfig", "DuplicatePhysicalReceiptError",
    "ProspectiveBoundaryCandidateEcology", "wilson_lower_bound",
]
