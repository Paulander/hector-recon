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


@dataclass(frozen=True)
class StructuralCandidate:
    """Non-causal structural repair/growth hypothesis emitted by a monitor."""

    candidate_type: str
    source_monitor_script: str
    source_terms: List[str]
    trigger_failure_classes: List[str]
    target_skill: str
    parent_skill: str
    proposed_change: Dict[str, Any]
    evidence_artifacts: List[str] = field(default_factory=list)
    governor_status: Literal[
        "settling",
        "needs_more_weight_training",
        "structure_insufficient",
        "growth_allowed",
        "growth_blocked_by_cooldown",
        "growth_blocked_by_guardrail",
        "growth_blocked_by_active_candidate_limit",
        "growth_blocked_by_improving_performance",
    ] = "settling"
    governor_metadata: Dict[str, Any] = field(default_factory=dict)
    topology_weight_diagnosis: Dict[str, Any] = field(default_factory=dict)
    candidate_diagnostic_labels: List[str] = field(default_factory=list)
    promotion_status: Literal[
        "shadow",
        "proposed",
        "sandbox_ready",
        "sandboxed",
        "validated",
        "promoted",
        "quarantined",
        "rejected",
    ] = "proposed"
    causal_status: Literal["non_causal"] = "non_causal"
    credit: float = 0.0
    schema_version: str = "structural_candidate.v1"
    candidate_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.causal_status != "non_causal":
            raise ValueError("StructuralCandidate must remain non_causal")
        if float(self.credit) != 0.0:
            raise ValueError("StructuralCandidate credit must be 0.0")
        allowed_governor_statuses = {
            "settling",
            "needs_more_weight_training",
            "structure_insufficient",
            "growth_allowed",
            "growth_blocked_by_cooldown",
            "growth_blocked_by_guardrail",
            "growth_blocked_by_active_candidate_limit",
            "growth_blocked_by_improving_performance",
        }
        if self.governor_status not in allowed_governor_statuses:
            raise ValueError(f"invalid Growth Governor status: {self.governor_status}")
        if self.candidate_id is None:
            object.__setattr__(
                self,
                "candidate_id",
                stable_record_id(
                    "cand",
                    self.target_skill,
                    self.candidate_type,
                    self.source_monitor_script,
                    self.trigger_failure_classes,
                    self.proposed_change,
                ),
            )

    def to_dict(self) -> Dict[str, Any]:
        return _jsonable(asdict(self))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "StructuralCandidate":
        return cls(**dict(payload))


@dataclass(frozen=True)
class PlanCapsuleSpec:
    """Non-causal multi-step plan/commitment candidate specification.

    A plan capsule describes a bounded continuation hypothesis with visible
    entry/progress/exit/abort terms. It is design and training evidence only
    until explicitly sandboxed and promoted into visible topology.
    """

    capsule_id: str
    source_candidate_id: str
    source_monitor_script: str
    source_terms: List[str]
    domain: str
    target_skill: str
    entry_terms: List[str] = field(default_factory=list)
    progress_terms: List[str] = field(default_factory=list)
    exit_terms: List[str] = field(default_factory=list)
    abort_terms: List[str] = field(default_factory=list)
    ttl_white_moves: int = 3
    owned_roles: List[str] = field(default_factory=list)
    owned_providers: List[str] = field(default_factory=list)
    handoff_exports: Dict[str, float] = field(default_factory=dict)
    self_model: Dict[str, Any] = field(default_factory=dict)
    training_source: Optional[str] = None
    validation_protocol: Dict[str, Any] = field(default_factory=dict)
    guardrails: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    causal_status: Literal["non_causal"] = "non_causal"
    promotion_status: Literal[
        "proposed",
        "sandbox_ready",
        "sandboxed",
        "validated",
        "promoted",
        "quarantined",
        "rejected",
    ] = "proposed"
    schema_version: str = "plan_capsule_spec.v1"
    record_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.causal_status != "non_causal":
            raise ValueError("PlanCapsuleSpec must remain non_causal until promoted topology exists")
        if int(self.ttl_white_moves) <= 0:
            raise ValueError("PlanCapsuleSpec ttl_white_moves must be positive and bounded")
        if self.record_id is None:
            object.__setattr__(
                self,
                "record_id",
                stable_record_id(
                    "plan_capsule",
                    self.capsule_id,
                    self.source_candidate_id,
                    self.target_skill,
                    self.entry_terms,
                    self.progress_terms,
                    self.exit_terms,
                    self.abort_terms,
                    self.ttl_white_moves,
                ),
            )

    def to_dict(self) -> Dict[str, Any]:
        return _jsonable(asdict(self))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PlanCapsuleSpec":
        return cls(**dict(payload))


def record_handoff_composition_event(
    episode_summary: Any,
    *,
    tick: int,
    from_skill: str,
    to_skill: Optional[str] = None,
    role: Optional[str] = None,
    move_shape: Optional[str] = None,
    status: str,
    handoff_packet: HandoffPacket | Mapping[str, Any] | None = None,
    route_decision: RouteDecision | Mapping[str, Any] | None = None,
    shadow_candidate: ShadowStemCandidate | Mapping[str, Any] | None = None,
    plies_to_mate: Optional[int] = None,
    meta: Optional[Mapping[str, Any]] = None,
) -> None:
    """Export handoff-composition evidence into an EpisodeSummary event.

    This helper is intentionally non-causal: it records zero-credit metadata for
    later analysis/consolidation, while M4 remains driven by normal episode edge
    deltas.
    """
    if not hasattr(episode_summary, "record_learning_event"):
        raise TypeError("episode_summary must provide record_learning_event")

    payload: Dict[str, Any] = {
        "schema_version": "handoff_composition_event.v1",
        "from_skill": from_skill,
        "to_skill": to_skill,
        "role": role,
        "move_shape": move_shape,
        "status": status,
        "plies_to_mate": plies_to_mate,
    }
    if handoff_packet is not None:
        payload["handoff_packet"] = (
            handoff_packet.to_dict() if hasattr(handoff_packet, "to_dict") else dict(handoff_packet)
        )
    if route_decision is not None:
        payload["route_decision"] = (
            route_decision.to_dict() if hasattr(route_decision, "to_dict") else dict(route_decision)
        )
    if shadow_candidate is not None:
        payload["shadow_candidate"] = (
            shadow_candidate.to_dict()
            if hasattr(shadow_candidate, "to_dict")
            else dict(shadow_candidate)
        )
    if meta:
        payload["meta"] = dict(meta)
    payload = _jsonable(payload)
    subject_id = stable_record_id(
        "handoff_event",
        from_skill,
        to_skill,
        role,
        move_shape,
        status,
        tick,
        payload.get("handoff_packet", {}).get("packet_id")
        if isinstance(payload.get("handoff_packet"), dict)
        else None,
    )
    episode_summary.record_learning_event(
        tick=tick,
        event_type="handoff_composition_event",
        subject_id=subject_id,
        parent_id=from_skill,
        credit=0.0,
        meta=payload,
    )


def record_provider_promotion_event(
    episode_summary: Any,
    *,
    tick: int,
    skill_id: str,
    provider_version: str,
    promotion_status: str,
    source_checkpoint: Optional[str] = None,
    base_provider_version: Optional[str] = None,
    overlay_provider_version: Optional[str] = None,
    validated_profile: Optional[str] = None,
    stage_artifact: Optional[str] = None,
    guardrail_artifacts: Optional[List[str]] = None,
    promotion_eval: Mapping[str, Any] | None = None,
    meta: Optional[Mapping[str, Any]] = None,
) -> None:
    """Export provider-preservation/promotion evidence into an EpisodeSummary.

    This is deliberately non-causal. It gives M5/promotion tooling and later
    analysis a durable trace record while M4 consolidation still ignores it and
    consumes ordinary edge-delta summaries only.
    """
    if not hasattr(episode_summary, "record_learning_event"):
        raise TypeError("episode_summary must provide record_learning_event")

    payload: Dict[str, Any] = {
        "schema_version": "provider_promotion_event.v1",
        "skill_id": skill_id,
        "provider_version": provider_version,
        "promotion_status": promotion_status,
        "source_checkpoint": source_checkpoint,
        "base_provider_version": base_provider_version,
        "overlay_provider_version": overlay_provider_version,
        "validated_profile": validated_profile,
        "stage_artifact": stage_artifact,
        "guardrail_artifacts": guardrail_artifacts or [],
    }
    if promotion_eval is not None:
        payload["promotion_eval"] = dict(promotion_eval)
    if meta:
        payload["meta"] = dict(meta)
    payload = _jsonable(payload)
    subject_id = stable_record_id(
        "provider_promotion_event",
        skill_id,
        provider_version,
        promotion_status,
        source_checkpoint,
        stage_artifact,
        guardrail_artifacts or [],
    )
    episode_summary.record_learning_event(
        tick=tick,
        event_type="provider_promotion_event",
        subject_id=subject_id,
        parent_id=skill_id,
        credit=0.0,
        meta=payload,
    )


def record_structural_candidate_event(
    episode_summary: Any,
    *,
    tick: int,
    candidate: StructuralCandidate | Mapping[str, Any],
    meta: Optional[Mapping[str, Any]] = None,
) -> None:
    """Export a structural growth candidate into an EpisodeSummary.

    The event is zero-credit evidence for later M5 review. It must not affect
    runtime routing, M3 adaptation, or M4 edge consolidation by itself.
    """
    if not hasattr(episode_summary, "record_learning_event"):
        raise TypeError("episode_summary must provide record_learning_event")

    candidate_payload = candidate.to_dict() if hasattr(candidate, "to_dict") else dict(candidate)
    payload: Dict[str, Any] = {
        "schema_version": "structural_candidate_event.v1",
        "structural_candidate": candidate_payload,
    }
    if meta:
        payload["meta"] = dict(meta)
    payload = _jsonable(payload)
    episode_summary.record_learning_event(
        tick=tick,
        event_type="structural_candidate_event",
        subject_id=str(candidate_payload.get("candidate_id")),
        parent_id=str(candidate_payload.get("parent_skill")),
        credit=0.0,
        meta=payload,
    )


def record_plan_capsule_event(
    episode_summary: Any,
    *,
    tick: int,
    capsule: PlanCapsuleSpec | Mapping[str, Any],
    meta: Optional[Mapping[str, Any]] = None,
) -> None:
    """Export a non-causal plan capsule candidate into an EpisodeSummary."""
    if not hasattr(episode_summary, "record_learning_event"):
        raise TypeError("episode_summary must provide record_learning_event")

    capsule_payload = capsule.to_dict() if hasattr(capsule, "to_dict") else dict(capsule)
    payload: Dict[str, Any] = {
        "schema_version": "plan_capsule_event.v1",
        "plan_capsule": capsule_payload,
    }
    if meta:
        payload["meta"] = dict(meta)
    payload = _jsonable(payload)
    episode_summary.record_learning_event(
        tick=tick,
        event_type="plan_capsule_event",
        subject_id=str(capsule_payload.get("capsule_id")),
        parent_id=str(capsule_payload.get("target_skill")),
        credit=0.0,
        meta=payload,
    )
