"""Trace-native competence learning and grounded-outcome authority closure.

This module is deliberately a capability boundary, not a Python sandbox.  The
environment adapter may execute chess and mint a receipt; production learning
accepts only that receipt and reconstructs its evidence from the selected graph
trace carried by the receipt.
"""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
import hashlib
from enum import Enum
import hmac
import json
import pickle
from typing import Any, Iterable, Mapping, Sequence

import chess

from recon_lite import ChildResponse, FrameContext, FrameKind

from .native_authority_handover import (
    ChildQuery,
    GraphSignalTrace,
    GraphTerminalSignal,
    NativeR0DreamSession,
    NativeR0Organism,
)
from .native_competence_envelope import (
    AvailabilityState,
    CompetenceContextGrowthGenome,
    CompetenceEvidenceRecord,
    EnvelopeClassification,
    GraphNativeCompetenceEnvelope,
    MatureCorrectionEmission,
    MixedOutcomeDisposition,
    NativeCompetenceSessionAudit,
    ProspectiveDiscoveryEpoch,
    SpecializationMode,
)


SCHEMA_VERSION = "trace_native_competence_organism.v1"
MANIFEST_VERSION = "continuation_manifest.v3"
FEATURE_EXTRACTOR_IDENTITY = "selected_graph_signal_trace.v1"
GENOME_IMPLEMENTATION_IDENTITY = "CompetenceContextGrowthGenome.v1"
COMPLETION_TERMINAL_ROLE = "OUTCOME_GROUNDED_COMPLETION"


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _canonical_persistent_value(value: Any) -> Any:
    """Encode persistent Python state without pickle memo/layout artifacts."""

    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, bytes):
        return {"__bytes_hex__": value.hex()}
    if isinstance(value, Enum):
        return {
            "__enum__": f"{type(value).__module__}.{type(value).__qualname__}",
            "name": value.name,
        }
    if isinstance(value, Mapping):
        return {
            str(key): _canonical_persistent_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_persistent_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        items = [_canonical_persistent_value(item) for item in value]
        return sorted(items, key=lambda item: json.dumps(item, sort_keys=True))
    if callable(value):
        return {
            "__callable__": (
                f"{getattr(value, '__module__', type(value).__module__)}."
                f"{getattr(value, '__qualname__', type(value).__qualname__)}"
            )
        }
    if hasattr(value, "__dict__"):
        return {
            "__type__": f"{type(value).__module__}.{type(value).__qualname__}",
            "fields": _canonical_persistent_value(vars(value)),
        }
    raise TypeError(
        "unsupported persistent state type: "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


@dataclass(frozen=True)
class TraceNativeLearningConfig:
    lifecycle_connected: bool
    specialization_mode: SpecializationMode
    genome_seed: int
    feature_extractor_identity: str = FEATURE_EXTRACTOR_IDENTITY
    genome_implementation_identity: str = GENOME_IMPLEMENTATION_IDENTITY
    completion_terminal_identity: str = "mate"
    completion_terminal_role: str = COMPLETION_TERMINAL_ROLE
    receipt_issuer_identity: str = "native_chess_environment_adapter.v1"
    receipt_capability_key: str = "native-r0-grounded-receipt-capability.v1"

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "specialization_mode", SpecializationMode(self.specialization_mode)
        )
        if self.feature_extractor_identity != FEATURE_EXTRACTOR_IDENTITY:
            raise ValueError("unfrozen trace feature extractor")
        if self.genome_implementation_identity != GENOME_IMPLEMENTATION_IDENTITY:
            raise ValueError("unfrozen competence genome implementation")
        if not self.completion_terminal_identity:
            raise ValueError("completion terminal identity is required")

    def to_manifest(self) -> dict[str, Any]:
        value = asdict(self)
        value["specialization_mode"] = self.specialization_mode.value
        value["receipt_capability_key_sha256"] = hashlib.sha256(
            self.receipt_capability_key.encode("utf-8")
        ).hexdigest()
        del value["receipt_capability_key"]
        return value


@dataclass(frozen=True)
class GroundedOutcomeReceipt:
    event_id: str
    event_ordinal: int
    context_fingerprint: str
    decision_trace: GraphSignalTrace
    predecessor_fen: str
    successor_fen: str
    completion_terminal_identity: str
    completion_terminal_role: str
    completion_terminal_provenance: str
    observed_terminal_result: bool
    issuer_identity: str
    signature: str

    def unsigned_manifest(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_ordinal": self.event_ordinal,
            "context_fingerprint": self.context_fingerprint,
            "decision_trace": self.decision_trace.canonical_manifest(),
            "predecessor_fen": self.predecessor_fen,
            "successor_fen": self.successor_fen,
            "completion_terminal_identity": self.completion_terminal_identity,
            "completion_terminal_role": self.completion_terminal_role,
            "completion_terminal_provenance": self.completion_terminal_provenance,
            "observed_terminal_result": self.observed_terminal_result,
            "issuer_identity": self.issuer_identity,
        }

    def canonical_manifest(self) -> dict[str, Any]:
        return {**self.unsigned_manifest(), "signature": self.signature}

    def digest(self) -> str:
        return _sha256_json(self.canonical_manifest())


def _receipt_signature(
    config: TraceNativeLearningConfig, unsigned: Mapping[str, Any]
) -> str:
    return hmac.new(
        config.receipt_capability_key.encode("utf-8"),
        _canonical_json(unsigned),
        hashlib.sha256,
    ).hexdigest()


@dataclass
class TraceNativeCompetenceOrganism:
    r0: NativeR0Organism
    envelope: GraphNativeCompetenceEnvelope
    learning_config: TraceNativeLearningConfig
    receipts: dict[str, GroundedOutcomeReceipt] = field(default_factory=dict)
    observation_emissions: dict[str, MatureCorrectionEmission] = field(
        default_factory=dict
    )
    _next_event_ordinal: int = 0
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("unsupported trace-native competence schema")
        if self.r0.retrieval_budget_per_actuator != self.envelope.config.retrieval_budget:
            raise ValueError("R0 retrieval budget differs from envelope budget")
        if self.learning_config.genome_seed != self.envelope.config.selection_seed:
            raise ValueError("persistent genome seed differs from envelope config")
        self._canonical_rebuild()

    @classmethod
    def empty(
        cls,
        r0: NativeR0Organism,
        *,
        envelope_config: Any,
        learning_config: TraceNativeLearningConfig,
    ) -> "TraceNativeCompetenceOrganism":
        return cls(
            r0=copy.deepcopy(r0),
            envelope=GraphNativeCompetenceEnvelope(config=envelope_config),
            learning_config=learning_config,
        )

    def _canonical_rebuild(self) -> None:
        self.envelope.rebuild_graph()

    def validate_canonical_evidence_ledger(self) -> None:
        """Require receipts and competence evidence to be one exact ledger.

        Prospective wrapping is an authority boundary, not a legacy migration
        path. In particular, opening an epoch must never manufacture missing
        evidence from historical receipts.
        """

        receipt_ids = set(self.receipts)
        evidence_ids = set(self.envelope.evidence)
        if receipt_ids != evidence_ids:
            raise RuntimeError(
                "noncanonical receipt/evidence ledger: identity mismatch"
            )
        for receipt_id in sorted(receipt_ids):
            receipt = self.receipts[receipt_id]
            expected = self._record_from_receipt(receipt)
            if self.envelope.evidence[receipt_id] != expected:
                raise RuntimeError(
                    "noncanonical receipt/evidence ledger: record mismatch "
                    f"for {receipt_id}"
                )
        for cell in self.envelope.cells.values():
            referenced = set(cell.evidence_keys)
            escrow = cell.nomination_escrow
            if escrow is not None:
                referenced.update(escrow.discovery_receipt_ids)
                referenced.update(escrow.discovery_exclusion_receipt_ids)
                referenced.update(escrow.transitive_ancestor_receipt_ids)
                referenced.add(escrow.triggering_receipt_id)
                for _category, category_receipt_ids in (
                    escrow.categorized_reads
                ):
                    referenced.update(category_receipt_ids)
            unknown = referenced.difference(receipt_ids)
            if unknown:
                raise RuntimeError(
                    "noncanonical receipt/evidence ledger: cell references "
                    f"unknown evidence {sorted(unknown)}"
                )

    def validate_prospective_discovery_epoch(self) -> None:
        epoch = self.envelope.nomination_epoch
        if epoch is None:
            return
        epoch.validate()
        ordinals = {
            key: value.event_ordinal
            for key, value in self.receipts.items()
        }
        outcomes = {
            key: value.observed_terminal_result
            for key, value in self.receipts.items()
        }
        if dict(epoch.receipt_ordinals) != ordinals:
            raise RuntimeError("epoch receipt ordinals differ from organism ledger")
        if set(self.envelope.evidence) != set(self.receipts):
            raise RuntimeError("epoch evidence differs from organism receipt ledger")
        if dict(epoch.receipt_outcomes) != outcomes:
            raise RuntimeError("epoch receipt outcomes differ from organism ledger")
        current_post = tuple(sorted(
            set(self.envelope.cells).difference(epoch.opened_cell_ids)
        ))
        if current_post != epoch.post_epoch_cell_ids:
            raise RuntimeError("epoch post-birth identity ledger mismatch")
        if epoch.nomination_closed:
            self.envelope._close_nomination_epoch()
        for cell_id in current_post:
            if self.envelope.cells[cell_id].nomination_escrow is None:
                raise RuntimeError("post-epoch cell lacks native nomination escrow")

    def open_prospective_discovery_epoch(
        self,
    ) -> ProspectiveDiscoveryEpoch:
        self.validate_canonical_evidence_ledger()
        candidate = copy.deepcopy(self)
        candidate.envelope._open_nomination_epoch(
            receipt_ordinals={
                key: value.event_ordinal
                for key, value in candidate.receipts.items()
            },
            receipt_outcomes={
                key: value.observed_terminal_result
                for key, value in candidate.receipts.items()
            },
        )
        candidate.validate_prospective_discovery_epoch()
        self.__dict__.clear()
        self.__dict__.update(candidate.__dict__)
        assert self.envelope.nomination_epoch is not None
        return self.envelope.nomination_epoch

    def close_prospective_nomination(
        self,
    ) -> tuple[tuple[str, str], ...]:
        self.validate_prospective_discovery_epoch()
        manifest = self.envelope._close_nomination_epoch()
        self.validate_prospective_discovery_epoch()
        return manifest

    def completion_terminal(self) -> "NativeChessCompletionTerminal":
        return NativeChessCompletionTerminal(self)

    def _reserve_event_ordinal(self) -> int:
        ordinal = self._next_event_ordinal
        self._next_event_ordinal += 1
        return ordinal

    def _validate_trace(self, trace: GraphSignalTrace, *, require_real: bool) -> None:
        if not isinstance(trace, GraphSignalTrace):
            raise TypeError("competence authority requires GraphSignalTrace")
        if require_real and trace.frame_kind != FrameKind.REAL.name:
            raise ValueError("grounded learning requires a REAL graph trace")
        if trace.source_organism_identity != self.r0.source_organism_identity():
            raise RuntimeError("trace belongs to another R0 organism")
        if trace.source_state_identity != self.r0.trace_state_identity():
            raise RuntimeError("trace belongs to stale R0 state")
        if trace.option_identity != trace.actuation.option_identity:
            raise RuntimeError("trace option differs from graph actuation")
        policy = tuple(
            item for item in trace.terminal_signals if item.role == "POLICY_RESPONSE"
        )
        if len(policy) != 1 or policy[0].identity != "internal:policy_response":
            raise RuntimeError("actuating trace lacks exact POLICY_RESPONSE")
        if trace.ordered_signal_identities != tuple(
            sorted(trace.ordered_signal_identities)
        ):
            raise RuntimeError("trace signals are not canonical")

    def classify_trace(self, trace: GraphSignalTrace) -> EnvelopeClassification:
        self._validate_trace(trace, require_real=False)
        return self.envelope.classify(
            trace.ordered_signal_identities, policy_response=True
        )

    def dream_session(
        self, *, audit: NativeCompetenceSessionAudit | None = None
    ) -> "TraceNativeCompetenceDreamSession":
        return TraceNativeCompetenceDreamSession(self, audit=audit)

    def _validate_receipt(self, receipt: GroundedOutcomeReceipt) -> None:
        if not isinstance(receipt, GroundedOutcomeReceipt):
            raise TypeError("production learning accepts GroundedOutcomeReceipt only")
        self._validate_trace(receipt.decision_trace, require_real=True)
        if receipt.issuer_identity != self.learning_config.receipt_issuer_identity:
            raise RuntimeError("untrusted receipt issuer")
        if (
            receipt.completion_terminal_identity
            != self.learning_config.completion_terminal_identity
            or receipt.completion_terminal_role
            != self.learning_config.completion_terminal_role
        ):
            raise RuntimeError("receipt terminal differs from organism configuration")
        if receipt.event_ordinal < 0:
            raise RuntimeError("receipt event ordinal must be nonnegative")
        expected_signature = _receipt_signature(
            self.learning_config, receipt.unsigned_manifest()
        )
        if not hmac.compare_digest(receipt.signature, expected_signature):
            raise RuntimeError("grounded receipt signature mismatch")
        board = chess.Board(receipt.predecessor_fen)
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(receipt.decision_trace.actuation.move_uci))
        if successor.fen() != receipt.successor_fen:
            raise RuntimeError("receipt successor is not the selected real transition")
        if successor.is_checkmate() != receipt.observed_terminal_result:
            raise RuntimeError("receipt terminal result differs from environment")
        context = _sha256_json({
            "predecessor_fen": receipt.predecessor_fen,
            "actuator_identity": receipt.decision_trace.actuation.actuator_identity,
            "successor_fen": receipt.successor_fen,
            "terminal_identity": receipt.completion_terminal_identity,
        })
        if context != receipt.context_fingerprint:
            raise RuntimeError("receipt context fingerprint mismatch")

    @staticmethod
    def _record_from_receipt(
        receipt: GroundedOutcomeReceipt,
    ) -> CompetenceEvidenceRecord:
        trace = receipt.decision_trace
        return CompetenceEvidenceRecord(
            evidence_key=receipt.event_id,
            active_signal_ids=trace.ordered_signal_identities,
            policy_response=True,
            observed_completion=receipt.observed_terminal_result,
            actuator_identity=trace.actuation.actuator_identity,
            completion_terminal_identity=receipt.completion_terminal_identity,
            signal_provenance=trace.terminal_signals,
        )

    def _accept_receipt(
        self, receipt: GroundedOutcomeReceipt
    ) -> tuple[CompetenceEvidenceRecord, bool]:
        self._validate_receipt(receipt)
        existing = self.receipts.get(receipt.event_id)
        if existing is not None:
            if existing != receipt:
                raise RuntimeError("event-id collision with altered grounded receipt")
            return self._record_from_receipt(receipt), False
        ordinal_owner = next((
            item.event_id for item in self.receipts.values()
            if item.event_ordinal == receipt.event_ordinal
        ), None)
        if ordinal_owner is not None:
            raise RuntimeError("event-ordinal collision with distinct event ID")
        epoch = self.envelope.nomination_epoch
        if epoch is not None and epoch.nomination_closed:
            raise RuntimeError("nomination epoch is closed")
        self.envelope._register_epoch_receipt(
            receipt_id=receipt.event_id,
            ordinal=receipt.event_ordinal,
            observed_outcome=receipt.observed_terminal_result,
        )
        self.receipts[receipt.event_id] = receipt
        self._next_event_ordinal = max(
            self._next_event_ordinal, receipt.event_ordinal + 1
        )
        return self._record_from_receipt(receipt), True

    def grow_from_grounded_receipts(
        self,
        receipts: Sequence[GroundedOutcomeReceipt],
        *,
        finalize: bool = True,
        mixed_outcome_disposition: MixedOutcomeDisposition = (
            MixedOutcomeDisposition.TOMBSTONE
        ),
    ) -> Any:
        records = []
        for receipt in receipts:
            record, inserted = self._accept_receipt(receipt)
            if not inserted:
                raise RuntimeError("initial growth tape contains duplicate event")
            records.append(record)
        return self.envelope.grow(
            records,
            genome=CompetenceContextGrowthGenome(
                self.learning_config.genome_seed
            ),
            finalize=finalize,
            mixed_outcome_disposition=mixed_outcome_disposition,
        )

    def observe_grounded(
        self, receipt: GroundedOutcomeReceipt
    ) -> MatureCorrectionEmission:
        record, inserted = self._accept_receipt(receipt)
        self.envelope._transaction_checkpoint("receipt_acceptance")
        if not inserted:
            prior = self.observation_emissions.get(receipt.event_id)
            if prior is None:
                raise RuntimeError(
                    "grounded event was already consumed by initial growth"
                )
            return prior
        emission = self.envelope.observe_real_outcome(
            FrameContext(
                "grounded-observation:" + receipt.event_id,
                FrameKind.REAL,
                values={},
            ),
            record,
            lifecycle_connected=self.learning_config.lifecycle_connected,
            specialization_mode=self.learning_config.specialization_mode,
            specialization_genome=CompetenceContextGrowthGenome(
                self.learning_config.genome_seed
            ),
        )
        self.observation_emissions[receipt.event_id] = emission
        return emission

    def continuation_manifest_v3(self) -> dict[str, Any]:
        self.validate_prospective_discovery_epoch()
        canonical_envelope = copy.deepcopy(self.envelope)
        canonical_envelope.rebuild_graph()
        r0_persistent_state = self.r0.persistent_identity_audit()
        cell_state_hashes = {
            cell_id: _sha256_json(_canonical_persistent_value(cell))
            for cell_id, cell in sorted(canonical_envelope.cells.items())
        }
        return {
            "schema_version": MANIFEST_VERSION,
            "organism_schema_version": self.schema_version,
            "learning_config": self.learning_config.to_manifest(),
            "genome": {
                "identity": self.learning_config.genome_implementation_identity,
                "seed": self.learning_config.genome_seed,
            },
            "feature_extractor_identity": (
                self.learning_config.feature_extractor_identity
            ),
            "terminal_role_allowlist": ["BASE_TERMINAL", "MATURE_COMPOSITE"],
            "completion_terminal": {
                "identity": self.learning_config.completion_terminal_identity,
                "role": self.learning_config.completion_terminal_role,
                "issuer": self.learning_config.receipt_issuer_identity,
            },
            "event_counter": self._next_event_ordinal,
            "receipts": [
                item.canonical_manifest()
                for item in sorted(self.receipts.values(), key=lambda row: row.event_id)
            ],
            "receipt_digests": {
                key: value.digest() for key, value in sorted(self.receipts.items())
            },
            "observation_emissions": {
                key: asdict(value)
                for key, value in sorted(self.observation_emissions.items())
            },
            "r0_persistent_state": {
                key: r0_persistent_state[key]
                for key in (
                    "topology_sha256", "weights_sha256", "credit_sha256",
                    "lifecycle_sha256",
                )
            },
            "r0_trace_state_identity": self.r0.trace_state_identity(),
            "r0_source_manifest": copy.deepcopy(self.r0.source_manifest),
            "envelope_continuation_v2_historical": (
                canonical_envelope.continuation_manifest_v2()
            ),
            "cell_complete_state_sha256": cell_state_hashes,
            "canonical_graph_snapshot": canonical_envelope.graph.to_snapshot(),
            "predicate_registry": [
                "POLICY_RESPONSE", "CONTEXT_MEMBER", "AVAILABILITY_ERROR",
                "CELL_LOCAL_PREDICTION_ERROR", "SPECIALIZATION_ELIGIBILITY",
            ],
            "transient_execution_state": "discarded_and_canonically_rebuilt",
        }

    def continuation_digest_v3(self) -> str:
        return _sha256_json(self.continuation_manifest_v3())

    def dumps(self) -> bytes:
        self.validate_prospective_discovery_epoch()
        canonical = copy.deepcopy(self)
        canonical._canonical_rebuild()
        return pickle.dumps(canonical, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def loads(cls, payload: bytes) -> "TraceNativeCompetenceOrganism":
        item = pickle.loads(payload)
        if not isinstance(item, cls):
            raise TypeError("serialized trace-native organism has wrong type")
        item._canonical_rebuild()
        item.validate_prospective_discovery_epoch()
        return item


class NativeChessCompletionTerminal:
    """Environment-facing terminal that observes, validates and signs outcomes."""

    def __init__(self, organism: TraceNativeCompetenceOrganism) -> None:
        self._organism = organism
        self._next_ordinal = organism._next_event_ordinal

    def mint(
        self,
        trace: GraphSignalTrace,
        predecessor: chess.Board,
        successor: chess.Board,
    ) -> GroundedOutcomeReceipt:
        self._organism._validate_trace(trace, require_real=True)
        frame = FrameContext(
            trace.frame_id, FrameKind.REAL, values={"board": predecessor}
        )
        actuation, regenerated = self._organism.r0.emit_action_with_trace(frame)
        if actuation != trace.actuation or regenerated != trace:
            raise RuntimeError("completion terminal rejected fabricated graph trace")
        expected = predecessor.copy(stack=False)
        expected.push(chess.Move.from_uci(trace.actuation.move_uci))
        if expected.fen() != successor.fen():
            raise RuntimeError("completion terminal received wrong real successor")
        ordinal = self._next_ordinal
        self._next_ordinal += 1
        context = _sha256_json({
            "predecessor_fen": predecessor.fen(),
            "actuator_identity": trace.actuation.actuator_identity,
            "successor_fen": successor.fen(),
            "terminal_identity": self._organism.learning_config.completion_terminal_identity,
        })
        event_id = _sha256_json({
            "issuer": self._organism.learning_config.receipt_issuer_identity,
            "ordinal": ordinal,
            "context_fingerprint": context,
            "trace_digest": trace.digest(),
        })
        unsigned = {
            "event_id": event_id,
            "event_ordinal": ordinal,
            "context_fingerprint": context,
            "decision_trace": trace.canonical_manifest(),
            "predecessor_fen": predecessor.fen(),
            "successor_fen": successor.fen(),
            "completion_terminal_identity": self._organism.learning_config.completion_terminal_identity,
            "completion_terminal_role": self._organism.learning_config.completion_terminal_role,
            "completion_terminal_provenance": "observed_after_exact_real_graph_actuation",
            "observed_terminal_result": successor.is_checkmate(),
            "issuer_identity": self._organism.learning_config.receipt_issuer_identity,
        }
        signature = _receipt_signature(self._organism.learning_config, unsigned)
        return GroundedOutcomeReceipt(
            event_id=event_id,
            event_ordinal=ordinal,
            context_fingerprint=context,
            decision_trace=trace,
            predecessor_fen=predecessor.fen(),
            successor_fen=successor.fen(),
            completion_terminal_identity=self._organism.learning_config.completion_terminal_identity,
            completion_terminal_role=self._organism.learning_config.completion_terminal_role,
            completion_terminal_provenance="observed_after_exact_real_graph_actuation",
            observed_terminal_result=successor.is_checkmate(),
            issuer_identity=self._organism.learning_config.receipt_issuer_identity,
            signature=signature,
        )


class TraceNativeCompetenceDreamSession:
    def __init__(
        self,
        organism: TraceNativeCompetenceOrganism,
        *,
        audit: NativeCompetenceSessionAudit | None = None,
    ) -> None:
        self.organism = organism
        self.r0_session: NativeR0DreamSession = organism.r0.dream_session()
        self.audit = audit

        self.before = organism.continuation_digest_v3()
        self.closed = False
        if audit is not None:
            audit.session_open_count += 1
            audit.open_events.append({"trace_native": True})

    def request(self, frame: FrameContext) -> ChildQuery:
        if self.closed:
            raise RuntimeError("trace-native dream session is closed")
        query = self.r0_session.request(frame)
        trace = query.graph_signal_trace
        if query.actuation is not None and trace is None:
            raise RuntimeError("R0 actuation lacks selected graph trace")
        classification = (
            EnvelopeClassification(
                AvailabilityState.UNKNOWN, 0.5, 1.0, (), (), False, False, False
            )
            if trace is None
            else self.organism.classify_trace(trace)
        )
        r0_provenance = dict(query.availability_provenance or {})
        local_provider = r0_provenance.get("local_provider")
        if not isinstance(local_provider, Mapping):
            local_provider = None
        locally_available = local_provider is not None
        available = bool(
            locally_available
            or classification.state == AvailabilityState.AVAILABLE
        )
        legacy_grounded = bool(
            self.organism.r0.provenance.grounded
            and self.organism.r0.provenance.can_emit
        )
        grounded = bool(locally_available or legacy_grounded)
        response = ChildResponse(
            child_id=(
                str(local_provider["cell_id"])
                if local_provider is not None
                else self.organism.r0.provenance.child_id
            ),
            confirmed=available,
            policy_response=query.actuation is not None,
            available=available,
            expected_value=(
                float(local_provider["expected_value"])
                if local_provider is not None
                else (
                    self.organism.r0.provenance.consolidated_value
                    if available
                    else 0.0
                )
            ),
            uncertainty=(
                float(local_provider["uncertainty"])
                if local_provider is not None
                else classification.uncertainty
            ),
            grounded=grounded,
            grounding_source=(
                str(local_provider["grounding_source"])
                if local_provider is not None
                else self.organism.r0.provenance.grounding_source
            ),
        )
        result = ChildQuery(
            response=response,
            actuation=query.actuation,
            frame_id=query.frame_id,
            persistent_mutation_count=query.persistent_mutation_count,
            effect_attempts=query.effect_attempts,
            active_competence_signal_ids=(
                () if trace is None else trace.ordered_signal_identities
            ),
            availability_provenance={
                "classification": classification.to_manifest(),
                "authority": "selected_graph_signal_trace",
                "local_provider": (
                    None
                    if local_provider is None
                    else copy.deepcopy(dict(local_provider))
                ),
                "r0_availability_provenance": r0_provenance,
                "effective_source": (
                    "native_local_direct_outcome_provider"
                    if local_provider is not None
                    else "trace_native_competence_envelope"
                ),
            },
            graph_signal_trace=trace,
        )
        if self.audit is not None:
            self.audit.request_count += 1
            self.audit.request_events.append({
                "frame_id": frame.frame_id,
                "trace_digest": None if trace is None else trace.digest(),
                "classification": classification.to_manifest(),
            })
        if self.organism.continuation_digest_v3() != self.before:
            raise RuntimeError("dream request mutated trace-native organism")
        return result

    def close(self) -> None:
        self.r0_session.close()
        if self.organism.continuation_digest_v3() != self.before:
            raise RuntimeError("trace-native dream session leaked persistent state")
        self.closed = True
        if self.audit is not None:
            self.audit.session_close_count += 1
            self.audit.close_events.append({"persistent_state_identical": True})
