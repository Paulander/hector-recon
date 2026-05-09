"""Versioned routing, skill-contract, and handoff trace records.

These records are intentionally non-causal. They make ReCoN-visible routing
and handoff evidence serializable for diagnostics and later consolidation, but
runtime behavior must continue to flow through graph activations and node state.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Mapping, Optional


def _jsonable(value: Any) -> Any:
    """Return a stable JSON-compatible representation."""
    if hasattr(value, "uci"):
        return value.uci()
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def stable_record_id(prefix: str, *parts: Any, length: int = 12) -> str:
    """Create a deterministic ID from semantic fields, not randomness."""
    payload = json.dumps(_jsonable(parts), sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:length]
    return f"{prefix}.{digest}"


@dataclass(frozen=True)
class SkillContractSpec:
    """Static contract metadata for a SCRIPT/subgraph skill."""

    skill_id: str
    source_node_id: str
    scope: str
    affordance_terms: List[str] = field(default_factory=list)
    request_terms: List[str] = field(default_factory=list)
    confirmation_terms: List[str] = field(default_factory=list)
    continuation_exports: Dict[str, float] = field(default_factory=dict)
    evidence_terms: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "skill_contract_spec.v1"
    record_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.record_id is None:
            object.__setattr__(
                self,
                "record_id",
                stable_record_id("skill", self.skill_id, self.source_node_id, self.scope),
            )

    def to_dict(self) -> Dict[str, Any]:
        return _jsonable(asdict(self))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SkillContractSpec":
        return cls(**dict(payload))


@dataclass(frozen=True)
class SkillContractStats:
    """Runtime summary stats for a skill contract.

    Stats are storage only. They must not influence routing unless separately
    exposed through a visible TERMINAL/SCRIPT.
    """

    skill_id: str
    context_bucket: str = "global"
    attempts: int = 0
    confirmations: int = 0
    handoff_gaps: int = 0
    conversions_passed: int = 0
    conversions_failed: int = 0
    schema_version: str = "skill_contract_stats.v1"
    record_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.record_id is None:
            object.__setattr__(
                self,
                "record_id",
                stable_record_id("skill_stats", self.skill_id, self.context_bucket),
            )

    def to_dict(self) -> Dict[str, Any]:
        return _jsonable(asdict(self))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SkillContractStats":
        return cls(**dict(payload))


@dataclass(frozen=True)
class RouteDecision:
    """Serializable explanation of a router decision."""

    router_id: str
    router_kind: str
    selected_route: Optional[str]
    route_scores: Dict[str, float] = field(default_factory=dict)
    route_evidence: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    domain_approach_affordance: Dict[str, float] = field(default_factory=dict)
    domain_execution_eligibility: Dict[str, bool] = field(default_factory=dict)
    execution_veto_reason: Dict[str, str] = field(default_factory=dict)
    evidence_terms: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "route_decision.v1"
    record_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.record_id is None:
            object.__setattr__(
                self,
                "record_id",
                stable_record_id(
                    "route",
                    self.router_id,
                    self.selected_route,
                    self.route_scores,
                    self.domain_execution_eligibility,
                ),
            )

    def to_dict(self) -> Dict[str, Any]:
        return _jsonable(asdict(self))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RouteDecision":
        return cls(**dict(payload))


@dataclass(frozen=True)
class HandoffPacket:
    """Trace-only handoff confirmation packet."""

    packet_id: str
    from_skill: str
    phase: str
    status: Literal["confirmed", "failed", "not_checked"]
    scope: str = "runtime"
    to_skill: Optional[str] = None
    evidence_terms: Dict[str, Any] = field(default_factory=dict)
    achieved: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)
    continuation_exports: Dict[str, float] = field(default_factory=dict)
    source_router: Optional[str] = None
    route_selected: Optional[str] = None
    observed_outcome: Optional[str] = None
    schema_version: str = "handoff_packet.v1"

    @classmethod
    def create(
        cls,
        *,
        from_skill: str,
        phase: str,
        status: Literal["confirmed", "failed", "not_checked"],
        scope: str = "runtime",
        to_skill: Optional[str] = None,
        evidence_terms: Optional[Dict[str, Any]] = None,
        achieved: Optional[List[str]] = None,
        failed: Optional[List[str]] = None,
        continuation_exports: Optional[Dict[str, float]] = None,
        source_router: Optional[str] = None,
        route_selected: Optional[str] = None,
        observed_outcome: Optional[str] = None,
    ) -> "HandoffPacket":
        packet_id = stable_record_id(
            "packet",
            from_skill,
            phase,
            status,
            scope,
            to_skill,
            evidence_terms or {},
            observed_outcome,
        )
        return cls(
            packet_id=packet_id,
            from_skill=from_skill,
            phase=phase,
            status=status,
            scope=scope,
            to_skill=to_skill,
            evidence_terms=evidence_terms or {},
            achieved=achieved or [],
            failed=failed or [],
            continuation_exports=continuation_exports or {},
            source_router=source_router,
            route_selected=route_selected,
            observed_outcome=observed_outcome,
        )

    def to_dict(self) -> Dict[str, Any]:
        return _jsonable(asdict(self))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "HandoffPacket":
        return cls(**dict(payload))


@dataclass(frozen=True)
class ShadowStemCandidate:
    """Logged growth candidate; never mutates topology by itself."""

    trigger: str
    owner_router: str
    scope: str
    parent_skill: str
    state_signature: str
    route_scores: Dict[str, float] = field(default_factory=dict)
    packet_id: Optional[str] = None
    observed_outcome: Optional[str] = None
    priority: int = 0
    promotion_status: Literal["shadow"] = "shadow"
    schema_version: str = "shadow_stem_candidate.v1"
    candidate_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.candidate_id is None:
            object.__setattr__(
                self,
                "candidate_id",
                stable_record_id(
                    "cand",
                    self.trigger,
                    self.scope,
                    self.parent_skill,
                    self.state_signature,
                    self.packet_id,
                ),
            )

    def to_dict(self) -> Dict[str, Any]:
        return _jsonable(asdict(self))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ShadowStemCandidate":
        return cls(**dict(payload))
