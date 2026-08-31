"""Focused graph-native tri-state all-reply authority primitive.

The formal graph owns ALL_AVAILABLE (AND) and ANY_REFUTED (OR) witnesses;
their projection is the explicit ``REFUTED < UNKNOWN < AVAILABLE`` boundary.
Only reply identity, authority fields, exposure, and a generic seed enter this
module.  Board/FEN semantics, mate labels, and outcomes are intentionally not
part of the contract.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Iterable, Mapping, Sequence

from recon_lite import FormalReConEngine, Graph, Node, NodeState, NodeType

from .native_competence_envelope import AvailabilityState


SCHEMA_VERSION = "native_all_reply_envelope.v1"
ROOT_ID = "all_reply_envelope_root"
ALL_AVAILABLE_ROOT_ID = f"{ROOT_ID}:all_available"
ANY_REFUTED_ROOT_ID = f"{ROOT_ID}:any_refuted"
SELECTION_READ_FIELDS = (
    "reply_id", "authority_state", "confidence", "value", "grounded",
    "exposure_count", "generic_seed",
)
LATTICE_ORDER = (
    AvailabilityState.REFUTED,
    AvailabilityState.UNKNOWN,
    AvailabilityState.AVAILABLE,
)
LATTICE_RANK = {state: index for index, state in enumerate(LATTICE_ORDER)}


def _state(value: AvailabilityState | str) -> AvailabilityState:
    if isinstance(value, AvailabilityState):
        return value
    raw = str(value)
    try:
        return AvailabilityState(raw.lower())
    except ValueError:
        try:
            return AvailabilityState[raw.upper()]
        except KeyError as exc:
            raise ValueError(f"unknown availability state: {value!r}") from exc


def availability_rank(value: AvailabilityState | str) -> int:
    """Return the frozen REFUTED=0, UNKNOWN=1, AVAILABLE=2 rank."""

    return LATTICE_RANK[_state(value)]


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ReplyAuthority:
    """The authority-only projection visible to the envelope and selector."""

    reply_id: str
    state: AvailabilityState
    confidence: float
    value: float
    exposure_count: int = 0
    # The compatibility default is deliberately *ungrounded*.  It keeps the
    # historical positional shape while remaining fail-closed; manifests are
    # stricter and must carry the field explicitly (see ``from_manifest``).
    grounded: bool = False

    def __post_init__(self) -> None:
        if not str(self.reply_id):
            raise ValueError("reply_id must be non-empty")
        object.__setattr__(self, "reply_id", str(self.reply_id))
        object.__setattr__(self, "state", _state(self.state))
        confidence, value = float(self.confidence), float(self.value)
        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be finite and in [0, 1]")
        if not math.isfinite(value) or not -1.0 <= value <= 1.0:
            raise ValueError("value must be finite and in [-1, 1]")
        if isinstance(self.exposure_count, bool) or int(self.exposure_count) != self.exposure_count:
            raise ValueError("exposure_count must be a non-negative integer")
        if int(self.exposure_count) < 0:
            raise ValueError("exposure_count must be a non-negative integer")
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "exposure_count", int(self.exposure_count))
        if type(self.grounded) is not bool:
            raise ValueError("grounded must be an explicit boolean")
        object.__setattr__(self, "grounded", self.grounded)

    @property
    def authority_state(self) -> AvailabilityState:
        return self.state

    @property
    def selection_strength(self) -> float:
        if self.state is not AvailabilityState.AVAILABLE or not self.grounded:
            return 0.0
        return max(0.0, self.value) * self.confidence

    def to_manifest(self) -> dict[str, Any]:
        return {
            "reply_id": self.reply_id,
            "authority_state": self.state.value,
            "confidence": self.confidence,
            "value": self.value,
            "exposure_count": self.exposure_count,
            "grounded": self.grounded,
        }

    @classmethod
    def from_manifest(cls, row: Mapping[str, Any]) -> "ReplyAuthority":
        # This is intentionally a strict compatibility boundary.  Existing
        # v1 manifests already carry ``grounded``; an older/malformed row has
        # no deterministic way to recover provenance.  Rejecting it is safer
        # than silently upgrading it to grounded (or pretending that a
        # missing field was a positive authority decision).
        if "grounded" not in row:
            raise ValueError(
                "reply authority manifest requires explicit grounded field"
            )
        return cls(
            reply_id=str(row["reply_id"]),
            state=row.get("authority_state", row.get("state")),
            confidence=float(row["confidence"]),
            value=float(row.get("value", 0.0)),
            exposure_count=int(row.get("exposure_count", 0)),
            grounded=row["grounded"],
        )


def _canonical(replies: Iterable[ReplyAuthority] | Mapping[str, ReplyAuthority]) -> tuple[ReplyAuthority, ...]:
    values = tuple(replies.values()) if isinstance(replies, Mapping) else tuple(replies)
    if not all(isinstance(item, ReplyAuthority) for item in values):
        raise TypeError("all replies must be ReplyAuthority records")
    ordered = tuple(sorted(values, key=lambda item: item.reply_id))
    if len({item.reply_id for item in ordered}) != len(ordered):
        raise ValueError("reply identities must be unique")
    return ordered


def stable_reply_hash(reply_id: str, generic_seed: int) -> str:
    """Stable tie-breaker; never uses Python's process-randomized hash."""

    return _digest({"reply_id": str(reply_id), "generic_seed": int(generic_seed)})


class CounterexampleChallengeSelector:
    """Rank only identity, authority, confidence, exposure, and generic seed."""

    def __init__(self, generic_seed: int = 0) -> None:
        self.generic_seed = int(generic_seed)

    def rank(self, replies: Iterable[ReplyAuthority] | Mapping[str, ReplyAuthority]) -> tuple[ReplyAuthority, ...]:
        def key(item: ReplyAuthority) -> tuple[Any, ...]:
            effective_state = (
                item.state if item.grounded else AvailabilityState.UNKNOWN
            )
            value = (
                item.value
                if effective_state is AvailabilityState.AVAILABLE
                else 0.0
            )
            confidence = (
                item.confidence
                if effective_state is AvailabilityState.AVAILABLE
                else 0.0
            )
            return (
                LATTICE_RANK[effective_state],
                value,
                confidence,
                item.exposure_count,
                stable_reply_hash(item.reply_id, self.generic_seed),
                item.reply_id,
            )
        return tuple(sorted(_canonical(replies), key=key))

    def select(self, replies: Iterable[ReplyAuthority] | Mapping[str, ReplyAuthority]) -> ReplyAuthority | None:
        ranked = self.rank(replies)
        return ranked[0] if ranked else None

    def receipt(self, replies: Iterable[ReplyAuthority] | Mapping[str, ReplyAuthority]) -> dict[str, Any]:
        ranked = self.rank(replies)
        rows = tuple({
            "rank": index,
            "reply_id": item.reply_id,
            "authority_state": item.state.value,
            "confidence": item.confidence,
            "value": item.value,
            "grounded": item.grounded,
            "exposure_count": item.exposure_count,
            "stable_hash": stable_reply_hash(item.reply_id, self.generic_seed),
        } for index, item in enumerate(ranked))
        unsigned = {
            "schema_version": SCHEMA_VERSION,
            "generic_seed": self.generic_seed,
            "ranked_reply_ids": [item.reply_id for item in ranked],
            "selected_reply_id": ranked[0].reply_id if ranked else None,
            "ranking_rows": list(rows),
        }
        return {**unsigned, "selection_digest": _digest(unsigned)}


def rank_counterexample_challenges(
    replies: Iterable[ReplyAuthority] | Mapping[str, ReplyAuthority], *, generic_seed: int = 0
) -> tuple[ReplyAuthority, ...]:
    return CounterexampleChallengeSelector(generic_seed).rank(replies)


def select_counterexample_challenge(
    replies: Iterable[ReplyAuthority] | Mapping[str, ReplyAuthority], *, generic_seed: int = 0
) -> ReplyAuthority | None:
    return CounterexampleChallengeSelector(generic_seed).select(replies)


def _lookup(node: Node, env: Mapping[str, Any]) -> ReplyAuthority | None:
    rows = env.get("reply_authority_by_id")
    row = rows.get(str(node.meta.get("reply_id", ""))) if isinstance(rows, Mapping) else None
    if not isinstance(row, ReplyAuthority):
        node.meta["last_failure"] = "missing_reply_authority"
        node.activation.value = 0.0
        return None
    node.meta.update({
        "authority_state": row.state.value,
        "confidence": row.confidence,
        "value": row.value,
        "grounded": row.grounded,
        "exposure_count": row.exposure_count,
    })
    return row


def _all_available_terminal(node: Node, env: Mapping[str, Any]) -> tuple[bool, bool]:
    row = _lookup(node, env)
    if row is None:
        return True, False
    node.activation.value = row.selection_strength
    valid = row.state is AvailabilityState.AVAILABLE and row.grounded
    node.meta["all_available_valid"] = valid
    return True, valid


def _refuted_terminal(node: Node, env: Mapping[str, Any]) -> tuple[bool, bool]:
    row = _lookup(node, env)
    if row is None:
        return True, False
    # A non-grounded classification is not an authority verdict in either
    # direction.  Keeping the negative arm fail-closed prevents an
    # untrusted/malformed row from becoming a global all-reply veto.
    valid = row.state is AvailabilityState.REFUTED and row.grounded
    node.activation.value = 1.0 if valid else 0.0
    node.meta["refuted_valid"] = valid
    return True, valid


def _empty_terminal(node: Node, _env: Mapping[str, Any]) -> tuple[bool, bool]:
    node.activation.value = 0.0
    return True, False


@dataclass(frozen=True)
class AllReplyEnvelopeGraph:
    graph: Graph
    all_available_root_id: str
    any_refuted_root_id: str
    all_available_reply_node_ids: tuple[tuple[str, str], ...]
    any_refuted_reply_node_ids: tuple[tuple[str, str], ...]

    def to_snapshot(self) -> dict[str, Any]:
        return self.graph.to_snapshot()


def build_all_reply_envelope_graph(
    replies: Iterable[ReplyAuthority] | Mapping[str, ReplyAuthority], *, envelope_id: str = "all-reply"
) -> AllReplyEnvelopeGraph:
    rows = _canonical(replies)
    if not str(envelope_id):
        raise ValueError("envelope_id must be non-empty")
    graph = Graph()
    common = {
        "graph_native_primitive": "tri_state_all_reply_envelope",
        "schema_version": SCHEMA_VERSION,
        "envelope_id": str(envelope_id),
        "reply_ids": [item.reply_id for item in rows],
    }
    graph.add_node(Node(ALL_AVAILABLE_ROOT_ID, NodeType.SCRIPT, meta={
        **common, "confirm_policy": "and", "generic_quantifier": "all", "envelope_role": "ALL_AVAILABLE",
    }))
    graph.add_node(Node(ANY_REFUTED_ROOT_ID, NodeType.SCRIPT, meta={
        **common, "confirm_policy": "or", "generic_quantifier": "any", "envelope_role": "ANY_REFUTED",
    }))
    available_nodes: list[tuple[str, str]] = []
    refuted_nodes: list[tuple[str, str]] = []
    if not rows:
        for parent, role in ((ALL_AVAILABLE_ROOT_ID, "ALL_AVAILABLE"), (ANY_REFUTED_ROOT_ID, "ANY_REFUTED")):
            node_id = f"{parent}:empty_reply_set"
            graph.add_node(Node(node_id, NodeType.TERMINAL, predicate=_empty_terminal, meta={
                "terminal_kind": "empty_reply_set", "envelope_role": role,
            }))
            graph.add_hierarchy_pair(parent, node_id)
    else:
        for row in rows:
            suffix = _digest(row.reply_id)[:16]
            available_id, refuted_id = f"{ALL_AVAILABLE_ROOT_ID}:reply:{suffix}", f"{ANY_REFUTED_ROOT_ID}:reply:{suffix}"
            metadata = {
                "terminal_kind": "reply_authority",
                "reply_id": row.reply_id,
                "authority_state": row.state.value,
                "confidence": row.confidence,
                "value": row.value,
                "grounded": row.grounded,
                "exposure_count": row.exposure_count,
            }
            graph.add_node(Node(available_id, NodeType.TERMINAL, predicate=_all_available_terminal, meta={**metadata, "envelope_role": "ALL_AVAILABLE"}))
            graph.add_node(Node(refuted_id, NodeType.TERMINAL, predicate=_refuted_terminal, meta={**metadata, "envelope_role": "ANY_REFUTED"}))
            graph.add_hierarchy_pair(ALL_AVAILABLE_ROOT_ID, available_id)
            graph.add_hierarchy_pair(ANY_REFUTED_ROOT_ID, refuted_id)
            available_nodes.append((row.reply_id, available_id))
            refuted_nodes.append((row.reply_id, refuted_id))
    graph.validate_formal_pairs()
    return AllReplyEnvelopeGraph(
        graph=graph,
        all_available_root_id=ALL_AVAILABLE_ROOT_ID,
        any_refuted_root_id=ANY_REFUTED_ROOT_ID,
        all_available_reply_node_ids=tuple(available_nodes),
        any_refuted_reply_node_ids=tuple(refuted_nodes),
    )


@dataclass(frozen=True)
class AllReplyEnvelopeAudit:
    envelope_id: str
    generic_seed: int
    reply_rows: tuple[Mapping[str, Any], ...]
    state: AvailabilityState
    value: float
    partial_value: float
    positive_gate: bool
    counterexample_reply_id: str | None
    ranked_reply_ids: tuple[str, ...]
    all_available_root_state: str
    any_refuted_root_state: str
    selection_digest: str
    selection_read_fields: tuple[str, ...] = SELECTION_READ_FIELDS
    audit_digest: str = ""
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "state", _state(self.state))
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("all-reply envelope schema mismatch")
        if tuple(self.selection_read_fields) != SELECTION_READ_FIELDS:
            raise ValueError("all-reply selector read-set changed")
        for row in self.reply_rows:
            if not isinstance(row, Mapping) or "grounded" not in row:
                raise ValueError(
                    "all-reply audit rows require explicit grounded field"
                )
            if type(row["grounded"]) is not bool:
                raise ValueError("all-reply audit grounded field must be boolean")
        expected = _digest(self._unsigned_manifest())
        if self.audit_digest and self.audit_digest != expected:
            raise ValueError("all-reply audit digest mismatch")
        object.__setattr__(self, "audit_digest", expected)

    def _unsigned_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "envelope_id": self.envelope_id,
            "generic_seed": self.generic_seed,
            "reply_rows": [dict(row) for row in self.reply_rows],
            "state": self.state.value,
            "value": self.value,
            "partial_value": self.partial_value,
            "positive_gate": self.positive_gate,
            "counterexample_reply_id": self.counterexample_reply_id,
            "ranked_reply_ids": list(self.ranked_reply_ids),
            "all_available_root_state": self.all_available_root_state,
            "any_refuted_root_state": self.any_refuted_root_state,
            "selection_digest": self.selection_digest,
            "selection_read_fields": list(self.selection_read_fields),
        }

    def to_manifest(self) -> dict[str, Any]:
        return {**self._unsigned_manifest(), "audit_digest": self.audit_digest}

    manifest = to_manifest

@dataclass(frozen=True)
class AllReplyEnvelopeResult:
    envelope_id: str
    replies: tuple[ReplyAuthority, ...]
    state: AvailabilityState
    value: float
    partial_value: float
    positive_gate: bool
    counterexample: ReplyAuthority | None
    selection: Mapping[str, Any]
    graph: AllReplyEnvelopeGraph
    all_available_root_state: NodeState
    any_refuted_root_state: NodeState
    audit: AllReplyEnvelopeAudit

    @property
    def authority_state(self) -> AvailabilityState:
        return self.state

    @property
    def envelope_value(self) -> float:
        return self.value

    @property
    def can_emit_positive(self) -> bool:
        return self.positive_gate

    @property
    def counterexample_reply_id(self) -> str | None:
        return None if self.counterexample is None else self.counterexample.reply_id

    def to_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "envelope_id": self.envelope_id,
            "generic_seed": int(self.selection["generic_seed"]),
            "replies": [item.to_manifest() for item in self.replies],
            "state": self.state.value,
            "value": self.value,
            "partial_value": self.partial_value,
            "positive_gate": self.positive_gate,
            "counterexample_reply_id": self.counterexample_reply_id,
            "selection": dict(self.selection),
            "audit": self.audit.to_manifest(),
            "graph_snapshot": self.graph.to_snapshot(),
        }

    def snapshot(self) -> dict[str, Any]:
        return self.to_manifest()

    manifest = to_manifest

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, Any]) -> "AllReplyEnvelopeResult":
        if str(snapshot.get("schema_version")) != SCHEMA_VERSION:
            raise ValueError("all-reply snapshot schema mismatch")
        result = evaluate_all_reply_envelope(
            tuple(ReplyAuthority.from_manifest(row) for row in snapshot.get("replies", ())),
            envelope_id=str(snapshot["envelope_id"]),
            generic_seed=int(snapshot["generic_seed"]),
        )
        if result.to_manifest() != dict(snapshot):
            raise ValueError("all-reply snapshot does not replay exactly")
        return result


def evaluate_all_reply_envelope(
    replies: Iterable[ReplyAuthority] | Mapping[str, ReplyAuthority], *,
    envelope_id: str = "all-reply", generic_seed: int = 0,
) -> AllReplyEnvelopeResult:
    rows = _canonical(replies)
    graph = build_all_reply_envelope_graph(rows, envelope_id=envelope_id)
    engine = FormalReConEngine(graph.graph, record_trace=False)
    engine.request(graph.all_available_root_id)
    engine.request(graph.any_refuted_root_id)
    engine.run(
        max_ticks=max(16, 6 * (len(rows) + 1)),
        env={"reply_authority_by_id": {item.reply_id: item for item in rows}},
        until=lambda _current: all(
            graph.graph.nodes[root].state in {NodeState.CONFIRMED, NodeState.FAILED}
            for root in (graph.all_available_root_id, graph.any_refuted_root_id)
        ),
    )
    all_state = graph.graph.nodes[graph.all_available_root_id].state
    veto_state = graph.graph.nodes[graph.any_refuted_root_id].state
    if any(state not in {NodeState.CONFIRMED, NodeState.FAILED} for state in (all_state, veto_state)):
        raise RuntimeError("all-reply graph did not settle")
    # The settled graph witnesses own the projection.  Veto has precedence;
    # only a confirmed ALL_AVAILABLE witness can open the AVAILABLE boundary.
    if veto_state is NodeState.CONFIRMED:
        aggregate = AvailabilityState.REFUTED
    elif all_state is NodeState.CONFIRMED:
        aggregate = AvailabilityState.AVAILABLE
    else:
        aggregate = AvailabilityState.UNKNOWN
    values = tuple(item.value for item in rows if item.state is AvailabilityState.AVAILABLE and item.grounded)
    partial_value = min(values) if values else 0.0
    value = partial_value if aggregate is AvailabilityState.AVAILABLE else 0.0
    positive_gate = bool(
        aggregate is AvailabilityState.AVAILABLE and rows
        and all(item.selection_strength > 0.0 for item in rows)
    )
    selection = CounterexampleChallengeSelector(generic_seed).receipt(rows)
    selected = next((item for item in rows if item.reply_id == selection["selected_reply_id"]), None)
    for root in (graph.all_available_root_id, graph.any_refuted_root_id):
        graph.graph.nodes[root].meta.update({
            "tri_state_state": aggregate.value,
            "envelope_value": value,
            "partial_value": partial_value,
            "positive_gate": positive_gate,
            "counterexample_reply_id": selection["selected_reply_id"],
        })
    audit = AllReplyEnvelopeAudit(
        envelope_id=str(envelope_id), generic_seed=int(generic_seed),
        reply_rows=tuple(item.to_manifest() for item in rows), state=aggregate,
        value=value, partial_value=partial_value, positive_gate=positive_gate,
        counterexample_reply_id=selection["selected_reply_id"],
        ranked_reply_ids=tuple(selection["ranked_reply_ids"]),
        all_available_root_state=all_state.name,
        any_refuted_root_state=veto_state.name,
        selection_digest=str(selection["selection_digest"]),
    )
    return AllReplyEnvelopeResult(
        envelope_id=str(envelope_id), replies=rows, state=aggregate, value=value,
        partial_value=partial_value, positive_gate=positive_gate,
        counterexample=selected, selection=selection, graph=graph,
        all_available_root_state=all_state, any_refuted_root_state=veto_state,
        audit=audit,
    )


def replay_all_reply_envelope(snapshot: Mapping[str, Any]) -> AllReplyEnvelopeResult:
    return AllReplyEnvelopeResult.from_snapshot(snapshot)


__all__ = [
    "ALL_AVAILABLE_ROOT_ID", "ANY_REFUTED_ROOT_ID", "AllReplyEnvelopeAudit",
    "AllReplyEnvelopeGraph", "AllReplyEnvelopeResult", "AvailabilityState",
    "CounterexampleChallengeSelector", "LATTICE_ORDER", "LATTICE_RANK", "ROOT_ID",
    "ReplyAuthority", "SCHEMA_VERSION", "SELECTION_READ_FIELDS", "availability_rank",
    "build_all_reply_envelope_graph", "evaluate_all_reply_envelope",
    "rank_counterexample_challenges", "replay_all_reply_envelope",
    "select_counterexample_challenge", "stable_reply_hash",
]
