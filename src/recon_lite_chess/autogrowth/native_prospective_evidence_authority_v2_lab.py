"""Laboratory-only registry for frozen V2 exposure engineering checks."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind

from .native_prospective_evidence_authority_v2 import (
    CanonicalExposureCommitment,
    NativeProspectiveAuthorityV2,
    OutcomeBlindExposureScanner,
    ProspectiveV2IntegrityError,
    _canonical_source_manifest_digest,
    _sha,
)


LAB_REGISTRY_SCHEMA_VERSION = "native_v2_laboratory_registry.v2"
LAB_SCAN_WRAPPER_SCHEMA_VERSION = "native_v2_registry_scan_wrapper.v2"
POLICY_CRITICAL_SOURCE_PATHS = {
    "v2_authority": (
        "src/recon_lite_chess/autogrowth/"
        "native_prospective_evidence_authority_v2.py"
    ),
    "v2_laboratory_registry": (
        "src/recon_lite_chess/autogrowth/"
        "native_prospective_evidence_authority_v2_lab.py"
    ),
    "native_trace_competence_authority": (
        "src/recon_lite_chess/autogrowth/"
        "native_trace_competence_authority.py"
    ),
    "native_competence_envelope": (
        "src/recon_lite_chess/autogrowth/native_competence_envelope.py"
    ),
    "native_authority_handover": (
        "src/recon_lite_chess/autogrowth/native_authority_handover.py"
    ),
    "native_single_graph_curriculum": (
        "src/recon_lite_chess/autogrowth/native_single_graph_curriculum.py"
    ),
    "recon_formal_engine": (
        "libs/recon-lite/src/recon_lite/formal_engine.py"
    ),
    "recon_frame_context": (
        "libs/recon-lite/src/recon_lite/frame_context.py"
    ),
    "recon_graph": "libs/recon-lite/src/recon_lite/graph.py",
    "recon_choice_genome": (
        "libs/recon-lite/src/recon_lite/choice_genome.py"
    ),
    "hector_stem_cell": "src/recon_lite_hector/nodes/stem_cell.py",
    "hector_m5_structure": (
        "src/recon_lite_hector/learning/m5_structure.py"
    ),
    "hector_pack_template": (
        "src/recon_lite_hector/nodes/pack_template.py"
    ),
}


def policy_critical_package_hashes(
    repository_root: Path | None = None,
) -> dict[str, str]:
    root = (
        Path(__file__).resolve().parents[3]
        if repository_root is None else Path(repository_root).resolve()
    )
    result = {}
    for identity, relative_path in sorted(
        POLICY_CRITICAL_SOURCE_PATHS.items()
    ):
        source_path = root / relative_path
        if not source_path.is_file():
            raise ProspectiveV2IntegrityError(
                f"policy-critical source is absent: {relative_path}"
            )
        result[identity] = hashlib.sha256(source_path.read_bytes()).hexdigest()
    return result


def _validated_package_hashes(
    supplied: Mapping[str, str],
) -> tuple[tuple[str, str], ...]:
    expected = policy_critical_package_hashes()
    for identity, digest in expected.items():
        if supplied.get(identity) != digest:
            raise ProspectiveV2IntegrityError(
                "laboratory package omits or alters policy-critical source: "
                + identity
            )
    return tuple(sorted(
        (str(identity), str(digest))
        for identity, digest in supplied.items()
    ))


def _source_binding_identity(
    organism: NativeProspectiveAuthorityV2,
) -> str:
    return _sha({
        "source_organism_identity": (
            organism.base.r0.source_organism_identity()
        ),
        "source_state_identity": organism.base.r0.trace_state_identity(),
        "source_manifest_digest": _canonical_source_manifest_digest(
            organism.base.r0
        ),
        "candidate_manifest_digest": organism._candidate_manifest_digest(),
        "authority_topology_digest": _sha(organism.authority_topology),
    })


@dataclass(frozen=True)
class RegisteredV2Organism:
    organism_id: str
    payload_sha256: str
    continuation_digest: str
    experimental_identity_digest: str
    candidate_population_identity: str
    source_binding_identity: str

    def manifest(self) -> dict[str, str]:
        return {
            "organism_id": self.organism_id,
            "payload_sha256": self.payload_sha256,
            "continuation_digest": self.continuation_digest,
            "experimental_identity_digest": (
                self.experimental_identity_digest
            ),
            "candidate_population_identity": (
                self.candidate_population_identity
            ),
            "source_binding_identity": self.source_binding_identity,
        }


@dataclass(frozen=True)
class RegisteredV2ExposureRow:
    """One exact, laboratory-owned pre-outcome tape row."""

    row_id: str
    frame_id: str
    predecessor_fen: str

    def __post_init__(self) -> None:
        if not self.row_id or not self.frame_id:
            raise ProspectiveV2IntegrityError(
                "registered exposure row has an empty identity"
            )
        try:
            canonical_fen = chess.Board(self.predecessor_fen).fen()
        except ValueError as exc:
            raise ProspectiveV2IntegrityError(
                "registered exposure row has invalid FEN"
            ) from exc
        if canonical_fen != self.predecessor_fen:
            raise ProspectiveV2IntegrityError(
                "registered exposure row FEN is noncanonical"
            )

    def manifest(self) -> dict[str, str]:
        return {
            "row_id": self.row_id,
            "frame_id": self.frame_id,
            "predecessor_fen": self.predecessor_fen,
        }


@dataclass(frozen=True)
class V2LaboratoryRegistry:
    """External registry; none of its fields may enter learner state."""

    schema_version: str
    registry_id: str
    tape_identity: str
    row_order: tuple[str, ...]
    run_identity: str
    package_hashes: tuple[tuple[str, str], ...]
    organisms: tuple[RegisteredV2Organism, ...]
    exposure_rows: tuple[
        tuple[str, tuple[RegisteredV2ExposureRow, ...]], ...
    ]

    @classmethod
    def freeze(
        cls,
        payloads: Mapping[str, bytes],
        *,
        exposure_rows: Mapping[
            str, Sequence[RegisteredV2ExposureRow]
        ],
        row_order: Sequence[str],
        run_identity: str,
        package_hashes: Mapping[str, str],
    ) -> "V2LaboratoryRegistry":
        if not payloads:
            raise ProspectiveV2IntegrityError(
                "registry requires frozen organisms"
            )
        canonical_package_hashes = _validated_package_hashes(package_hashes)
        rows = tuple(map(str, row_order))
        if len(rows) != len(set(rows)):
            raise ProspectiveV2IntegrityError(
                "registry row order contains duplicates"
            )
        if set(exposure_rows) != set(payloads):
            raise ProspectiveV2IntegrityError(
                "registry exposure cohort differs from organism cohort"
            )
        frozen_exposure_rows = []
        frame_ids = set()
        for organism_id, organism_rows in sorted(exposure_rows.items()):
            exact_rows = tuple(organism_rows)
            if not all(
                isinstance(item, RegisteredV2ExposureRow)
                for item in exact_rows
            ):
                raise ProspectiveV2IntegrityError(
                    "registry rejects noncanonical nested exposure schema"
                )
            if tuple(item.row_id for item in exact_rows) != rows:
                raise ProspectiveV2IntegrityError(
                    "registry exposure rows differ from frozen row order"
                )
            physical_predecessors = [
                item.predecessor_fen for item in exact_rows
            ]
            if len(set(physical_predecessors)) != len(
                physical_predecessors
            ):
                raise ProspectiveV2IntegrityError(
                    "registry tape repeats one physical interaction"
                )
            for item in exact_rows:
                if item.frame_id in frame_ids:
                    raise ProspectiveV2IntegrityError(
                        "registry exposure frame identity is duplicated"
                    )
                frame_ids.add(item.frame_id)
            frozen_exposure_rows.append((str(organism_id), exact_rows))

        entries = []
        payload_digests = set()
        continuation_digests = set()
        for organism_id, payload in sorted(payloads.items()):
            if not isinstance(payload, bytes):
                raise TypeError("registry accepts serialized organisms only")
            organism = NativeProspectiveAuthorityV2.loads(payload)
            cls._require_frozen_preoutcome(organism)
            payload_digest = hashlib.sha256(payload).hexdigest()
            if payload_digest in payload_digests:
                raise ProspectiveV2IntegrityError(
                    "registry contains duplicate serialized organism"
                )
            payload_digests.add(payload_digest)
            continuation = organism.continuation_digest()
            if continuation in continuation_digests:
                raise ProspectiveV2IntegrityError(
                    "registry contains duplicate organism state"
                )
            continuation_digests.add(continuation)
            identity = organism.experimental_identity
            assert identity is not None
            entries.append(RegisteredV2Organism(
                organism_id=str(organism_id),
                payload_sha256=payload_digest,
                continuation_digest=continuation,
                experimental_identity_digest=identity["identity_digest"],
                candidate_population_identity=(
                    identity["candidate_population_identity"]
                ),
                source_binding_identity=_source_binding_identity(organism),
            ))

        tape_manifest = {
            "row_order": list(rows),
            "organisms": {
                organism_id: [item.manifest() for item in organism_rows]
                for organism_id, organism_rows in frozen_exposure_rows
            },
        }
        tape_identity = _sha(tape_manifest)
        unsigned = {
            "schema_version": LAB_REGISTRY_SCHEMA_VERSION,
            "tape_identity": tape_identity,
            "tape_manifest": tape_manifest,
            "run_identity": str(run_identity),
            "package_hashes": [
                list(item) for item in canonical_package_hashes
            ],
            "organisms": [item.manifest() for item in entries],
        }
        return cls(
            schema_version=LAB_REGISTRY_SCHEMA_VERSION,
            registry_id=_sha(unsigned),
            tape_identity=tape_identity,
            row_order=rows,
            run_identity=str(run_identity),
            package_hashes=canonical_package_hashes,
            organisms=tuple(entries),
            exposure_rows=tuple(frozen_exposure_rows),
        )

    @staticmethod
    def _require_frozen_preoutcome(
        organism: NativeProspectiveAuthorityV2,
    ) -> None:
        # Private callers invoke this only after verified deserialization.
        epoch = organism.base.envelope.nomination_epoch
        if epoch is None or not epoch.nomination_closed:
            raise ProspectiveV2IntegrityError(
                "registry organism nomination is not closed"
            )
        if (
            organism.pending_event is not None
            or organism.consumed_receipts
            or organism.emissions
            or any(
                row.get("state") == "CONSUMED"
                for row in organism.event_transactions.values()
            )
        ):
            raise ProspectiveV2IntegrityError(
                "registry organism is not pre-outcome and transaction-closed"
            )
        if organism.experimental_identity is None:
            raise ProspectiveV2IntegrityError(
                "registry organism lacks experimental identity"
            )

    def _entry(self, organism_id: str) -> RegisteredV2Organism:
        matches = [
            item for item in self.organisms
            if item.organism_id == organism_id
        ]
        if len(matches) != 1:
            raise ProspectiveV2IntegrityError(
                "organism is absent or duplicated in registry"
            )
        return matches[0]

    def _rows(
        self, organism_id: str
    ) -> tuple[RegisteredV2ExposureRow, ...]:
        matches = [
            rows for item_id, rows in self.exposure_rows
            if item_id == organism_id
        ]
        if len(matches) != 1:
            raise ProspectiveV2IntegrityError(
                "organism tape is absent or duplicated in registry"
            )
        return matches[0]

    def scan(
        self,
        organism_id: str,
        payload: bytes,
        commitments: Sequence[CanonicalExposureCommitment],
        *,
        tape_identity: str,
        row_order: Sequence[str],
        run_identity: str,
        package_hashes: Mapping[str, str],
    ) -> dict[str, Any]:
        if (
            self.schema_version != LAB_REGISTRY_SCHEMA_VERSION
            or tape_identity != self.tape_identity
            or tuple(row_order) != self.row_order
            or run_identity != self.run_identity
            or _validated_package_hashes(package_hashes)
            != self.package_hashes
        ):
            raise ProspectiveV2IntegrityError(
                "laboratory registry tape/order/run/package mismatch"
            )
        if len(commitments) != len(self.row_order):
            raise ProspectiveV2IntegrityError(
                "laboratory exposure count differs from frozen row order"
            )
        entry = self._entry(organism_id)
        if hashlib.sha256(payload).hexdigest() != entry.payload_sha256:
            raise ProspectiveV2IntegrityError(
                "serialized organism differs from registry"
            )
        organism = NativeProspectiveAuthorityV2.loads(payload)
        self._require_frozen_preoutcome(organism)
        before = organism.continuation_digest()
        if before != entry.continuation_digest:
            raise ProspectiveV2IntegrityError(
                "registered continuation identity mismatch"
            )
        identity = organism.experimental_identity
        assert identity is not None
        if (
            identity["identity_digest"]
            != entry.experimental_identity_digest
            or identity["candidate_population_identity"]
            != entry.candidate_population_identity
        ):
            raise ProspectiveV2IntegrityError(
                "registered experimental identity mismatch"
            )

        canonical = []
        expected_rows = self._rows(organism_id)
        seen_interactions = set()
        for expected, commitment in zip(expected_rows, commitments):
            if not isinstance(commitment, CanonicalExposureCommitment):
                raise ProspectiveV2IntegrityError(
                    "registry rejects noncanonical or post-outcome row"
                )
            if (
                commitment.trace.frame_id != expected.frame_id
                or commitment.predecessor_fen != expected.predecessor_fen
            ):
                raise ProspectiveV2IntegrityError(
                    "registry commitment differs from frozen tape: "
                    f"{expected.row_id}"
                )
            if commitment.interaction_fingerprint in seen_interactions:
                raise ProspectiveV2IntegrityError(
                    "registry rejects duplicate exposure interaction"
                )
            seen_interactions.add(commitment.interaction_fingerprint)
            board = chess.Board(commitment.predecessor_fen)
            regenerated = organism.probe_real_exposure(FrameContext(
                commitment.trace.frame_id,
                FrameKind.REAL,
                values={"board": board},
            ))
            if regenerated != commitment:
                raise ProspectiveV2IntegrityError(
                    "registry commitment differs from exact organism: "
                    f"{expected.row_id}"
                )
            canonical.append(commitment)
        scan = OutcomeBlindExposureScanner.scan(organism, canonical)
        if organism.continuation_digest() != before:
            raise ProspectiveV2IntegrityError(
                "registry exposure mutated frozen organism"
            )
        return {
            "schema_version": LAB_SCAN_WRAPPER_SCHEMA_VERSION,
            "registry_id": self.registry_id,
            "organism_id": organism_id,
            "tape_identity": self.tape_identity,
            "row_order": list(self.row_order),
            "run_identity": self.run_identity,
            "package_hashes": [list(item) for item in self.package_hashes],
            "payload_sha256": entry.payload_sha256,
            "continuation_digest": entry.continuation_digest,
            "experimental_identity_digest": (
                entry.experimental_identity_digest
            ),
            "candidate_population_identity": (
                entry.candidate_population_identity
            ),
            "source_binding_identity": entry.source_binding_identity,
            "scan_digest": _sha(scan),
            "scan": scan,
        }

    def adjudicate_cohort(
        self,
        results: Sequence[Mapping[str, Any]],
        *,
        tape_identity: str,
        row_order: Sequence[str],
        run_identity: str,
        package_hashes: Mapping[str, str],
    ) -> dict[str, Any]:
        """Associate every raw scan with its frozen registry entry first."""

        if (
            self.schema_version != LAB_REGISTRY_SCHEMA_VERSION
            or tape_identity != self.tape_identity
            or tuple(row_order) != self.row_order
            or run_identity != self.run_identity
            or _validated_package_hashes(package_hashes)
            != self.package_hashes
        ):
            raise ProspectiveV2IntegrityError(
                "laboratory adjudication authority mismatch"
            )
        required_keys = {
            "schema_version", "registry_id", "organism_id",
            "tape_identity", "row_order", "run_identity",
            "package_hashes", "payload_sha256", "continuation_digest",
            "experimental_identity_digest",
            "candidate_population_identity", "source_binding_identity",
            "scan_digest", "scan",
        }
        if len(results) != len(self.organisms):
            raise ProspectiveV2IntegrityError(
                "registry adjudication requires one result per organism"
            )
        scans_by_id = {}
        for result in results:
            if not isinstance(result, Mapping) or set(result) != required_keys:
                raise ProspectiveV2IntegrityError(
                    "registry adjudication rejects raw-only scan result"
                )
            if (
                result["schema_version"]
                != LAB_SCAN_WRAPPER_SCHEMA_VERSION
                or result["registry_id"] != self.registry_id
                or result["tape_identity"] != self.tape_identity
                or tuple(result["row_order"]) != self.row_order
                or result["run_identity"] != self.run_identity
                or tuple(
                    tuple(item) for item in result["package_hashes"]
                ) != self.package_hashes
            ):
                raise ProspectiveV2IntegrityError(
                    "foreign registry scan result"
                )
            organism_id = str(result["organism_id"])
            if organism_id in scans_by_id:
                raise ProspectiveV2IntegrityError(
                    "duplicate registry scan result"
                )
            entry = self._entry(organism_id)
            for key in (
                "payload_sha256", "continuation_digest",
                "experimental_identity_digest",
                "candidate_population_identity",
                "source_binding_identity",
            ):
                if result[key] != getattr(entry, key):
                    raise ProspectiveV2IntegrityError(
                        "swapped registry scan result"
                    )
            scan = result["scan"]
            if (
                not isinstance(scan, Mapping)
                or _sha(scan) != result["scan_digest"]
                or scan.get("source_binding_identity")
                != entry.source_binding_identity
            ):
                raise ProspectiveV2IntegrityError(
                    "altered or swapped registry scan payload"
                )
            scans_by_id[organism_id] = scan
        expected_ids = {item.organism_id for item in self.organisms}
        if set(scans_by_id) != expected_ids:
            raise ProspectiveV2IntegrityError(
                "registry adjudication has missing or foreign organism"
            )
        if len(self.organisms) != 32:
            raise ProspectiveV2IntegrityError(
                "exposure admission requires exactly 32 organisms"
            )
        ordered_scans = [
            scans_by_id[item.organism_id] for item in self.organisms
        ]
        qualifications = [
            OutcomeBlindExposureScanner._validate_raw_scan(scan)
            for scan in ordered_scans
        ]
        identities = [
            str(scan["source_binding_identity"]) for scan in ordered_scans
        ]
        if len(set(identities)) != 32:
            raise ProspectiveV2IntegrityError(
                "exposure cohort requires 32 distinct bound organisms"
            )
        qualifying = sum(qualifications)
        return {
            "organism_count": 32,
            "qualifying_organisms": qualifying,
            "required_qualifying_organisms": 24,
            "admitted": qualifying >= 24,
            "stop_reason": (
                None if qualifying >= 24
                else "prospective_evidence_starvation"
            ),
        }
