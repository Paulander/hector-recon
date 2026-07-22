"""Laboratory-only registry for frozen V2 exposure engineering checks."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Mapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind

from .native_prospective_evidence_authority_v2 import (
    CanonicalExposureCommitment,
    NativeProspectiveAuthorityV2,
    OutcomeBlindExposureScanner,
    ProspectiveV2IntegrityError,
    _sha,
)


@dataclass(frozen=True)
class RegisteredV2Organism:
    organism_id: str
    payload_sha256: str
    continuation_digest: str
    experimental_identity_digest: str
    candidate_population_identity: str

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
            "tape_identity": tape_identity,
            "tape_manifest": tape_manifest,
            "run_identity": str(run_identity),
            "package_hashes": [
                list(item) for item in sorted(package_hashes.items())
            ],
            "organisms": [item.manifest() for item in entries],
        }
        return cls(
            registry_id=_sha(unsigned),
            tape_identity=tape_identity,
            row_order=rows,
            run_identity=str(run_identity),
            package_hashes=tuple(sorted(
                (str(key), str(value))
                for key, value in package_hashes.items()
            )),
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
            tape_identity != self.tape_identity
            or tuple(row_order) != self.row_order
            or run_identity != self.run_identity
            or tuple(sorted(package_hashes.items())) != self.package_hashes
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
            "registry_id": self.registry_id,
            "organism_id": organism_id,
            "tape_identity": self.tape_identity,
            "row_order": list(self.row_order),
            "run_identity": self.run_identity,
            "package_hashes": [list(item) for item in self.package_hashes],
            "scan": scan,
        }
