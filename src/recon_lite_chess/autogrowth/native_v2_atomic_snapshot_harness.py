"""Atomic semantic snapshots and tri-arm execution for V2 laboratories.

This is an outer engineering harness.  It intentionally does not modify the
validated V2.1 authority organism or laboratory registry.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Protocol, Sequence
import base64
import argparse
import copy
import gzip
import hashlib
import json
import pickle
import sys

from .native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    V2Mode,
)


SCHEMA_VERSION = "native_v2_atomic_snapshot_harness.v1"
SNAPSHOT_MANIFEST_SCHEMA = "native_v2_arm_snapshot_manifest.v1"
PREFLIGHT_RECEIPT_SCHEMA = "native_v2_global_preflight_receipt.v1"
PREFLIGHT_FAILURE_SCHEMA = "native_v2_global_preflight_failure.v1"
JOURNAL_SCHEMA = "native_v2_atomic_journal.v1"
ARMS = ("A", "B", "C")
DEFAULT_SEED_ORDINALS = tuple(range(32))
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RECLOSURE_ROOT = ROOT / (
    "reports/autogrowth/native_authority/v2_atomic_snapshot_reclosure"
)
PROTECTED_HASHES = {
    ROOT / (
        "src/recon_lite_chess/autogrowth/"
        "native_prospective_evidence_authority_v2.py"
    ): "25945864fd998caf22ae12cbcb9bcb4779447337c0079f705640c63d2356f029",
    ROOT / (
        "src/recon_lite_chess/autogrowth/"
        "native_prospective_evidence_authority_v2_lab.py"
    ): "f3aee5cccf761af1cb6a5de94b886d5e758c0a07cb0f6d77b8898f662ca73b58",
}


class AtomicSnapshotIntegrityError(RuntimeError):
    """Fail-closed outer harness boundary."""


class NonResumableJournal(AtomicSnapshotIntegrityError):
    """A PREPARED seed has uncertain outcome access."""


class InjectedHarnessFailure(RuntimeError):
    """Test-only fault injected into a synthetic transaction stage."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def verify_protected_v2_1() -> dict[str, str]:
    observed = {path.as_posix(): sha256_file(path) for path in PROTECTED_HASHES}
    for path, expected in PROTECTED_HASHES.items():
        if observed[path.as_posix()] != expected:
            raise AtomicSnapshotIntegrityError(
                f"protected V2.1 source changed:{path}"
            )
    return observed


def _atomic_bytes(path: Path, payload: bytes, *, replace: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not replace:
        raise FileExistsError(f"refusing to overwrite frozen artifact: {path}")
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def atomic_json(path: Path, value: Any, *, replace: bool = False) -> None:
    payload = json.dumps(
        value, indent=2, sort_keys=True, allow_nan=False
    ).encode("utf-8") + b"\n"
    _atomic_bytes(path, payload, replace=replace)


def gzip_deterministic(payload: bytes) -> bytes:
    return gzip.compress(payload, compresslevel=9, mtime=0)


def _pointer_token(value: Any) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def json_pointer_differences(
    expected: Any,
    observed: Any,
    *,
    pointer: str = "",
) -> list[dict[str, Any]]:
    """Return complete deterministic recursive canonical-JSON differences."""

    if type(expected) is not type(observed):
        return [{
            "path": pointer or "/",
            "kind": "type",
            "expected": expected,
            "observed": observed,
        }]
    if isinstance(expected, Mapping):
        rows: list[dict[str, Any]] = []
        keys = sorted(set(expected) | set(observed), key=str)
        for key in keys:
            path = f"{pointer}/{_pointer_token(key)}"
            if key not in expected:
                rows.append({
                    "path": path,
                    "kind": "unexpected",
                    "expected": None,
                    "observed": observed[key],
                })
            elif key not in observed:
                rows.append({
                    "path": path,
                    "kind": "missing",
                    "expected": expected[key],
                    "observed": None,
                })
            else:
                rows.extend(json_pointer_differences(
                    expected[key], observed[key], pointer=path
                ))
        return rows
    if isinstance(expected, list):
        rows = []
        size = max(len(expected), len(observed))
        for index in range(size):
            path = f"{pointer}/{index}"
            if index >= len(expected):
                rows.append({
                    "path": path,
                    "kind": "unexpected",
                    "expected": None,
                    "observed": observed[index],
                })
            elif index >= len(observed):
                rows.append({
                    "path": path,
                    "kind": "missing",
                    "expected": expected[index],
                    "observed": None,
                })
            else:
                rows.extend(json_pointer_differences(
                    expected[index], observed[index], pointer=path
                ))
        return rows
    if expected != observed:
        return [{
            "path": pointer or "/",
            "kind": "value",
            "expected": expected,
            "observed": observed,
        }]
    return []


def first_differing_byte(expected: bytes, observed: bytes) -> int | None:
    for index, (left, right) in enumerate(zip(expected, observed)):
        if left != right:
            return index
    if len(expected) != len(observed):
        return min(len(expected), len(observed))
    return None


@dataclass
class OutcomeAccessGuard:
    """Harness-owned accounting for environment outcome access."""

    count: int = 0
    event_ids: tuple[str, ...] = ()

    def open(self, event_id: str) -> None:
        self.count += 1
        self.event_ids = (*self.event_ids, str(event_id))

    def manifest(self) -> dict[str, Any]:
        return {"count": self.count, "event_ids": list(self.event_ids)}


class SemanticSnapshotCodec(Protocol):
    codec_identity: str

    def dumps(self, value: Any) -> bytes: ...
    def loads(self, payload: bytes) -> Any: ...
    def semantic_identity(self, value: Any) -> dict[str, Any]: ...


@contextmanager
def legacy_main_graph_compatibility() -> Iterable[None]:
    """Load preserved ``__main__`` graph pickles; never used for new graphs."""

    from .native_prospective_evidence_v2_science import OpaqueChessEcologyGraph

    main = sys.modules["__main__"]
    sentinel = object()
    previous = getattr(main, "OpaqueChessEcologyGraph", sentinel)
    setattr(main, "OpaqueChessEcologyGraph", OpaqueChessEcologyGraph)
    try:
        yield
    finally:
        if previous is sentinel:
            delattr(main, "OpaqueChessEcologyGraph")
        else:
            setattr(main, "OpaqueChessEcologyGraph", previous)


def v2_semantic_identity(
    wrapper: NativeProspectiveAuthorityV2,
) -> dict[str, Any]:
    continuation = wrapper.continuation_manifest()
    experimental = copy.deepcopy(wrapper.experimental_identity)
    if not isinstance(experimental, dict):
        raise AtomicSnapshotIntegrityError("missing V2 experimental identity")
    source = experimental.get("source")
    if not isinstance(source, dict):
        raise AtomicSnapshotIntegrityError("missing V2 source identity")
    polarities = {
        cell_id: state.hypothesis.polarity.value
        for cell_id, state in sorted(wrapper.states.items())
    }
    initial_authority = {
        cell_id: bool(state.prospectively_certified)
        for cell_id, state in sorted(wrapper.states.items())
    }
    expected_authority = {
        cell_id: bool(
            wrapper.mode is V2Mode.LEGACY
            and state.hypothesis.structural_state == "MATURE"
        )
        for cell_id, state in sorted(wrapper.states.items())
    }
    lawful = initial_authority == expected_authority
    population = experimental.get("candidate_population", {})
    executed_topology = (
        population.get("executed_authority_topology")
        if isinstance(population, dict) else None
    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "codec": "native_v2_authority",
        "continuation_manifest": continuation,
        "continuation_digest": canonical_digest(continuation),
        "experiment_identity": experimental.get("identity_digest"),
        "source_organism_identity": source.get("organism_identity"),
        "source_state_identity": source.get("state_identity"),
        "source_base_continuation_digest": source.get(
            "base_continuation_digest"
        ),
        "candidate_population_identity": experimental.get(
            "candidate_population_identity"
        ),
        "polarity_manifest": polarities,
        "polarity_identity": canonical_digest(polarities),
        "topology_identity": canonical_digest(wrapper.authority_topology),
        "executed_topology_identity": canonical_digest(executed_topology),
        "authority_manifest": initial_authority,
        "authority_identity": canonical_digest(initial_authority),
        "mode": wrapper.mode.value,
        "lawful_initial_authority": lawful,
    }
    if not lawful:
        raise AtomicSnapshotIntegrityError("unlawful V2 initial authority state")
    return result


class V2SnapshotCodec:
    codec_identity = "native_v2_authority_snapshot.v1"

    def __init__(self, *, legacy_main_compatibility: bool = False) -> None:
        self.legacy_main_compatibility = bool(legacy_main_compatibility)

    def dumps(self, value: NativeProspectiveAuthorityV2) -> bytes:
        return value.dumps()

    def loads(self, payload: bytes) -> NativeProspectiveAuthorityV2:
        if self.legacy_main_compatibility:
            with legacy_main_graph_compatibility():
                return NativeProspectiveAuthorityV2.loads(payload)
        return NativeProspectiveAuthorityV2.loads(payload)

    def semantic_identity(
        self, value: NativeProspectiveAuthorityV2
    ) -> dict[str, Any]:
        return v2_semantic_identity(value)


class PickleSemanticCodec:
    """Small engineering codec for synthetic transaction tests."""

    codec_identity = "pickle_semantic_test.v1"

    def dumps(self, value: Any) -> bytes:
        return pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)

    def loads(self, payload: bytes) -> Any:
        return pickle.loads(payload)

    def semantic_identity(self, value: Any) -> dict[str, Any]:
        manifest = value.semantic_manifest()
        return {
            "schema_version": SCHEMA_VERSION,
            "codec": self.codec_identity,
            "continuation_manifest": manifest,
            "continuation_digest": canonical_digest(manifest),
            "experiment_identity": value.experiment_identity,
            "source_organism_identity": value.source_organism_identity,
            "source_state_identity": value.source_state_identity,
            "source_base_continuation_digest": value.source_state_identity,
            "candidate_population_identity": value.candidate_population_identity,
            "polarity_manifest": {"cell": value.polarity},
            "polarity_identity": canonical_digest({"cell": value.polarity}),
            "topology_identity": value.topology_identity,
            "executed_topology_identity": value.topology_identity,
            "authority_manifest": {"cell": value.authority},
            "authority_identity": canonical_digest({"cell": value.authority}),
            "mode": value.mode,
            "lawful_initial_authority": bool(value.lawful_initial_authority),
        }


def _validate_arm_semantics(
    seed: int,
    identities: Mapping[str, Mapping[str, Any]],
) -> None:
    if set(identities) != set(ARMS):
        raise AtomicSnapshotIntegrityError(f"seed {seed} arm coverage mismatch")
    for arm in ARMS:
        identity = identities[arm]
        if arm != "B":
            expected_mode = V2Mode.PROSPECTIVE.value
        elif identity.get("codec") == "native_v2_authority":
            expected_mode = V2Mode.LEGACY.value
        else:
            expected_mode = "legacy"
        if identity.get("mode") != expected_mode:
            raise AtomicSnapshotIntegrityError(
                f"seed {seed} arm {arm} mode mismatch"
            )
        if identity.get("lawful_initial_authority") is not True:
            raise AtomicSnapshotIntegrityError(
                f"seed {seed} arm {arm} unlawful initial authority"
            )
    parity_fields = (
        "source_organism_identity",
        "source_state_identity",
        "candidate_population_identity",
        "polarity_identity",
        "topology_identity",
        "executed_topology_identity",
    )
    for field_name in parity_fields:
        values = {identities[arm].get(field_name) for arm in ARMS}
        if len(values) != 1:
            raise AtomicSnapshotIntegrityError(
                f"seed {seed} {field_name} arm parity mismatch"
            )


def persist_arm_snapshots_once(
    *,
    seed_ordinals: Sequence[int],
    arm_factory: Callable[[int], Mapping[str, Any]],
    package_root: Path,
    codec: SemanticSnapshotCodec,
    experiment_id: str,
    source_manifest_digest: str,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Construct each tri-arm seed cohort once and persist all raw payloads."""

    ordinals = tuple(map(int, seed_ordinals))
    if len(set(ordinals)) != len(ordinals):
        raise AtomicSnapshotIntegrityError("duplicate seed ordinal")
    entries: list[dict[str, Any]] = []
    for seed in ordinals:
        arms = dict(arm_factory(seed))
        if set(arms) != set(ARMS):
            raise AtomicSnapshotIntegrityError(
                f"seed {seed} factory did not return exact A/B/C"
            )
        identities = {
            arm: codec.semantic_identity(arms[arm]) for arm in ARMS
        }
        _validate_arm_semantics(seed, identities)
        for arm in ARMS:
            raw = codec.dumps(arms[arm])
            compressed = gzip_deterministic(raw)
            relative = Path("arm_snapshots") / f"seed-{seed:02d}" / f"{arm}.pkl.gz"
            _atomic_bytes(package_root / relative, compressed)
            entries.append({
                "seed_ordinal": seed,
                "arm": arm,
                "path": relative.as_posix(),
                "raw_sha256": sha256_bytes(raw),
                "raw_size": len(raw),
                "compressed_sha256": sha256_bytes(compressed),
                "compressed_size": len(compressed),
                "compressed_reference_b64": base64.b64encode(
                    compressed
                ).decode("ascii"),
                "semantic_identity": identities[arm],
                "semantic_identity_digest": canonical_digest(identities[arm]),
            })
    manifest = {
        "schema_version": SNAPSHOT_MANIFEST_SCHEMA,
        "experiment_id": experiment_id,
        "codec_identity": codec.codec_identity,
        "source_manifest_digest": source_manifest_digest,
        "metadata": copy.deepcopy(dict(metadata or {})),
        "seed_ordinals": list(ordinals),
        "arms": list(ARMS),
        "entries": entries,
    }
    manifest["manifest_digest"] = canonical_digest(manifest)
    atomic_json(package_root / "arm_snapshot_manifest.json", manifest)
    return manifest


def _failure_template(
    *,
    classification: str,
    seed: int | None,
    arm: str | None,
    path: str | None,
    expected_raw_hash: str | None,
    observed_raw_hash: str | None,
    expected_raw_size: int | None,
    observed_raw_size: int | None,
    first_difference: int | None,
    expected_continuation: str | None,
    observed_continuation: str | None,
    differences: Sequence[Mapping[str, Any]],
    detail: str,
    guard: OutcomeAccessGuard,
    expected_compressed_hash: str | None = None,
    observed_compressed_hash: str | None = None,
    expected_compressed_size: int | None = None,
    observed_compressed_size: int | None = None,
) -> dict[str, Any]:
    value = {
        "schema_version": PREFLIGHT_FAILURE_SCHEMA,
        "classification": classification,
        "seed_ordinal": seed,
        "arm": arm,
        "path": path,
        "expected_raw_sha256": expected_raw_hash,
        "observed_raw_sha256": observed_raw_hash,
        "expected_raw_size": expected_raw_size,
        "observed_raw_size": observed_raw_size,
        "expected_compressed_sha256": expected_compressed_hash,
        "observed_compressed_sha256": observed_compressed_hash,
        "expected_compressed_size": expected_compressed_size,
        "observed_compressed_size": observed_compressed_size,
        "first_differing_byte_offset": first_difference,
        "expected_continuation_digest": expected_continuation,
        "observed_continuation_digest": observed_continuation,
        "canonical_json_pointer_differences": list(differences),
        "detail": detail,
        "outcome_access": guard.manifest(),
    }
    value["failure_digest"] = canonical_digest(value)
    return value


def _write_and_raise_failure(
    failure_path: Path,
    failure: Mapping[str, Any],
) -> None:
    atomic_json(failure_path, failure)
    raise AtomicSnapshotIntegrityError(
        f"global preflight failed:{failure['classification']}:"
        f"{failure.get('seed_ordinal')}:{failure.get('arm')}"
    )


def global_all_arm_preflight(
    *,
    manifest_path: Path,
    package_root: Path,
    receipt_path: Path,
    failure_path: Path,
    codec: SemanticSnapshotCodec,
    guard: OutcomeAccessGuard,
    required_seed_ordinals: Sequence[int] = DEFAULT_SEED_ORDINALS,
) -> tuple[dict[str, Any], dict[tuple[int, str], Any]]:
    """Restore and semantically verify the complete cohort before outcomes."""

    if guard.count != 0:
        failure = _failure_template(
            classification="semantic drift", seed=None, arm=None, path=None,
            expected_raw_hash=None, observed_raw_hash=None,
            expected_raw_size=None, observed_raw_size=None,
            first_difference=None, expected_continuation=None,
            observed_continuation=None, differences=(),
            detail="outcome-access counter was nonzero before preflight",
            guard=guard,
        )
        _write_and_raise_failure(failure_path, failure)
    manifest = json.loads(manifest_path.read_text())
    expected_manifest_digest = manifest.get("manifest_digest")
    unsigned = {k: v for k, v in manifest.items() if k != "manifest_digest"}
    if expected_manifest_digest != canonical_digest(unsigned):
        failure = _failure_template(
            classification="transport corruption", seed=None, arm=None,
            path=manifest_path.as_posix(), expected_raw_hash=None,
            observed_raw_hash=sha256_bytes(manifest_path.read_bytes()),
            expected_raw_size=None, observed_raw_size=manifest_path.stat().st_size,
            first_difference=None, expected_continuation=None,
            observed_continuation=None, differences=(),
            detail="snapshot manifest digest mismatch", guard=guard,
        )
        _write_and_raise_failure(failure_path, failure)
    required = {
        (int(seed), arm)
        for seed in required_seed_ordinals for arm in ARMS
    }
    header_differences = json_pointer_differences(
        {
            "seed_ordinals": list(map(int, required_seed_ordinals)),
            "arms": list(ARMS),
            "codec_identity": codec.codec_identity,
        },
        {
            "seed_ordinals": manifest.get("seed_ordinals"),
            "arms": manifest.get("arms"),
            "codec_identity": manifest.get("codec_identity"),
        },
    )
    if header_differences:
        failure = _failure_template(
            classification="semantic drift", seed=None, arm=None,
            path=manifest_path.as_posix(), expected_raw_hash=None,
            observed_raw_hash=None, expected_raw_size=None,
            observed_raw_size=None, first_difference=None,
            expected_continuation=None, observed_continuation=None,
            differences=header_differences,
            detail="snapshot manifest header or codec mismatch", guard=guard,
        )
        _write_and_raise_failure(failure_path, failure)
    entries = list(manifest.get("entries", ()))
    indexed: dict[tuple[int, str], dict[str, Any]] = {}
    seen_paths: set[str] = set()
    for entry in entries:
        key = (int(entry.get("seed_ordinal", -1)), str(entry.get("arm")))
        path = str(entry.get("path"))
        if key in indexed or path in seen_paths:
            failure = _failure_template(
                classification="semantic drift", seed=key[0], arm=key[1],
                path=path, expected_raw_hash=entry.get("raw_sha256"),
                observed_raw_hash=None, expected_raw_size=entry.get("raw_size"),
                observed_raw_size=None, first_difference=None,
                expected_continuation=entry.get("semantic_identity", {}).get(
                    "continuation_digest"
                ), observed_continuation=None, differences=(),
                detail="duplicate organism key or snapshot path", guard=guard,
            )
            _write_and_raise_failure(failure_path, failure)
        indexed[key] = entry
        seen_paths.add(path)
    if set(indexed) != required:
        missing = sorted(required - set(indexed))
        foreign = sorted(set(indexed) - required)
        failure = _failure_template(
            classification="semantic drift",
            seed=(missing or foreign or [(None, None)])[0][0],
            arm=(missing or foreign or [(None, None)])[0][1], path=None,
            expected_raw_hash=None, observed_raw_hash=None,
            expected_raw_size=None, observed_raw_size=None,
            first_difference=None, expected_continuation=None,
            observed_continuation=None,
            differences=[{"path": "/coverage", "kind": "value",
                          "expected": [list(item) for item in sorted(required)],
                          "observed": [list(item) for item in sorted(indexed)]}],
            detail="missing, omitted, or foreign cohort member", guard=guard,
        )
        _write_and_raise_failure(failure_path, failure)
    restored: dict[tuple[int, str], Any] = {}
    observed_identities: dict[int, dict[str, dict[str, Any]]] = {}
    verification_rows = []
    for key in sorted(required):
        seed, arm = key
        entry = indexed[key]
        relative = Path(entry["path"])
        if relative.is_absolute() or ".." in relative.parts:
            failure = _failure_template(
                classification="transport corruption", seed=seed, arm=arm,
                path=entry["path"], expected_raw_hash=entry["raw_sha256"],
                observed_raw_hash=None, expected_raw_size=entry["raw_size"],
                observed_raw_size=None, first_difference=None,
                expected_continuation=entry["semantic_identity"][
                    "continuation_digest"
                ], observed_continuation=None, differences=(),
                detail="snapshot path escaped package root", guard=guard,
            )
            _write_and_raise_failure(failure_path, failure)
        path = package_root / relative
        expected_compressed = base64.b64decode(
            entry["compressed_reference_b64"].encode("ascii")
        )
        if (
            len(expected_compressed) != int(entry["compressed_size"])
            or sha256_bytes(expected_compressed) != entry["compressed_sha256"]
        ):
            failure = _failure_template(
                classification="transport corruption", seed=seed, arm=arm,
                path=entry["path"], expected_raw_hash=entry["raw_sha256"],
                observed_raw_hash=None, expected_raw_size=entry["raw_size"],
                observed_raw_size=None, first_difference=None,
                expected_continuation=entry["semantic_identity"][
                    "continuation_digest"
                ], observed_continuation=None, differences=(),
                detail="forensic transport reference differs from manifest",
                guard=guard,
                expected_compressed_hash=entry["compressed_sha256"],
                observed_compressed_hash=sha256_bytes(expected_compressed),
                expected_compressed_size=entry["compressed_size"],
                observed_compressed_size=len(expected_compressed),
            )
            _write_and_raise_failure(failure_path, failure)
        observed_compressed = path.read_bytes() if path.exists() else b""
        compressed_ok = (
            len(observed_compressed) == int(entry["compressed_size"])
            and sha256_bytes(observed_compressed) == entry["compressed_sha256"]
        )
        if not compressed_ok:
            failure = _failure_template(
                classification="transport corruption", seed=seed, arm=arm,
                path=entry["path"], expected_raw_hash=entry["raw_sha256"],
                observed_raw_hash=None, expected_raw_size=entry["raw_size"],
                observed_raw_size=None,
                first_difference=first_differing_byte(
                    expected_compressed, observed_compressed
                ),
                expected_continuation=entry["semantic_identity"][
                    "continuation_digest"
                ], observed_continuation=None, differences=(),
                detail="compressed transport hash or size mismatch",
                guard=guard,
                expected_compressed_hash=entry["compressed_sha256"],
                observed_compressed_hash=sha256_bytes(observed_compressed),
                expected_compressed_size=entry["compressed_size"],
                observed_compressed_size=len(observed_compressed),
            )
            _write_and_raise_failure(failure_path, failure)
        try:
            raw = gzip.decompress(observed_compressed)
        except Exception as exc:
            failure = _failure_template(
                classification="restore failure", seed=seed, arm=arm,
                path=entry["path"], expected_raw_hash=entry["raw_sha256"],
                observed_raw_hash=None, expected_raw_size=entry["raw_size"],
                observed_raw_size=None, first_difference=None,
                expected_continuation=entry["semantic_identity"][
                    "continuation_digest"
                ], observed_continuation=None, differences=(),
                detail=f"gzip restore failed:{type(exc).__name__}:{exc}",
                guard=guard,
            )
            _write_and_raise_failure(failure_path, failure)
        raw_hash = sha256_bytes(raw)
        if raw_hash != entry["raw_sha256"] or len(raw) != entry["raw_size"]:
            failure = _failure_template(
                classification="transport corruption", seed=seed, arm=arm,
                path=entry["path"], expected_raw_hash=entry["raw_sha256"],
                observed_raw_hash=raw_hash, expected_raw_size=entry["raw_size"],
                observed_raw_size=len(raw), first_difference=None,
                expected_continuation=entry["semantic_identity"][
                    "continuation_digest"
                ], observed_continuation=None, differences=(),
                detail="raw transport hash or size mismatch", guard=guard,
            )
            _write_and_raise_failure(failure_path, failure)
        try:
            value = codec.loads(raw)
            observed_identity = codec.semantic_identity(value)
        except Exception as exc:
            failure = _failure_template(
                classification="restore failure", seed=seed, arm=arm,
                path=entry["path"], expected_raw_hash=entry["raw_sha256"],
                observed_raw_hash=raw_hash, expected_raw_size=entry["raw_size"],
                observed_raw_size=len(raw), first_difference=None,
                expected_continuation=entry["semantic_identity"][
                    "continuation_digest"
                ], observed_continuation=None, differences=(),
                detail=f"organism restore failed:{type(exc).__name__}:{exc}",
                guard=guard,
            )
            _write_and_raise_failure(failure_path, failure)
        expected_identity = entry["semantic_identity"]
        if entry.get("semantic_identity_digest") != canonical_digest(
            expected_identity
        ):
            failure = _failure_template(
                classification="semantic drift", seed=seed, arm=arm,
                path=entry["path"], expected_raw_hash=entry["raw_sha256"],
                observed_raw_hash=raw_hash, expected_raw_size=entry["raw_size"],
                observed_raw_size=len(raw), first_difference=None,
                expected_continuation=expected_identity.get(
                    "continuation_digest"
                ), observed_continuation=observed_identity.get(
                    "continuation_digest"
                ), differences=[{
                    "path": "/semantic_identity_digest",
                    "kind": "value",
                    "expected": canonical_digest(expected_identity),
                    "observed": entry.get("semantic_identity_digest"),
                }], detail="semantic identity digest mismatch", guard=guard,
            )
            _write_and_raise_failure(failure_path, failure)
        differences = json_pointer_differences(
            expected_identity, observed_identity
        )
        if differences:
            failure = _failure_template(
                classification="semantic drift", seed=seed, arm=arm,
                path=entry["path"], expected_raw_hash=entry["raw_sha256"],
                observed_raw_hash=raw_hash, expected_raw_size=entry["raw_size"],
                observed_raw_size=len(raw), first_difference=None,
                expected_continuation=expected_identity.get(
                    "continuation_digest"
                ), observed_continuation=observed_identity.get(
                    "continuation_digest"
                ), differences=differences,
                detail="restored canonical semantic identity changed",
                guard=guard,
            )
            _write_and_raise_failure(failure_path, failure)
        restored[key] = value
        observed_identities.setdefault(seed, {})[arm] = observed_identity
        verification_rows.append({
            "seed_ordinal": seed,
            "arm": arm,
            "path": entry["path"],
            "raw_sha256": raw_hash,
            "semantic_identity_digest": canonical_digest(observed_identity),
        })
    try:
        for seed in required_seed_ordinals:
            _validate_arm_semantics(int(seed), observed_identities[int(seed)])
    except Exception as exc:
        failure = _failure_template(
            classification="semantic drift", seed=None, arm=None, path=None,
            expected_raw_hash=None, observed_raw_hash=None,
            expected_raw_size=None, observed_raw_size=None,
            first_difference=None, expected_continuation=None,
            observed_continuation=None, differences=(), detail=str(exc),
            guard=guard,
        )
        _write_and_raise_failure(failure_path, failure)
    if guard.count != 0:
        raise AtomicSnapshotIntegrityError(
            "outcome access occurred during global preflight"
        )
    receipt = {
        "schema_version": PREFLIGHT_RECEIPT_SCHEMA,
        "manifest_path": manifest_path.name,
        "manifest_digest": expected_manifest_digest,
        "codec_identity": codec.codec_identity,
        "coverage": {
            "seed_count": len(tuple(required_seed_ordinals)),
            "arm_count": len(ARMS),
            "artifact_count": len(verification_rows),
            "complete": True,
        },
        "verification_rows": verification_rows,
        "outcome_access": guard.manifest(),
    }
    receipt["receipt_digest"] = canonical_digest(receipt)
    atomic_json(receipt_path, receipt)
    return receipt, restored


def verify_preflight_receipt(
    receipt: Mapping[str, Any],
    manifest: Mapping[str, Any],
    guard: OutcomeAccessGuard,
) -> None:
    unsigned = {k: v for k, v in receipt.items() if k != "receipt_digest"}
    if receipt.get("receipt_digest") != canonical_digest(unsigned):
        raise AtomicSnapshotIntegrityError("preflight receipt digest mismatch")
    if receipt.get("manifest_digest") != manifest.get("manifest_digest"):
        raise AtomicSnapshotIntegrityError("preflight receipt/manifest mismatch")
    if receipt.get("coverage", {}).get("complete") is not True:
        raise AtomicSnapshotIntegrityError("preflight coverage is incomplete")
    if receipt.get("outcome_access") != {"count": 0, "event_ids": []}:
        raise AtomicSnapshotIntegrityError("preflight receipt opened outcomes")
    del guard


@dataclass
class DurableHashJournal:
    root: Path
    fail_on_kind: str | None = None

    def _records(self) -> list[dict[str, Any]]:
        if not self.root.exists():
            return []
        rows = []
        previous = "GENESIS"
        for path in sorted(self.root.glob("*.json")):
            row = json.loads(path.read_text())
            unsigned = {k: v for k, v in row.items() if k != "record_hash"}
            if row.get("record_hash") != canonical_digest(unsigned):
                raise AtomicSnapshotIntegrityError("journal record hash mismatch")
            if row.get("previous_hash") != previous:
                raise AtomicSnapshotIntegrityError("journal chain mismatch")
            previous = row["record_hash"]
            rows.append(row)
        return rows

    def append(self, kind: str, *, seed: int, payload: Mapping[str, Any]) -> dict[str, Any]:
        if self.fail_on_kind == kind:
            raise InjectedHarnessFailure(f"durable_commit:{kind}")
        rows = self._records()
        unsigned = {
            "schema_version": JOURNAL_SCHEMA,
            "index": len(rows),
            "previous_hash": rows[-1]["record_hash"] if rows else "GENESIS",
            "kind": kind,
            "seed_ordinal": int(seed),
            "payload": copy.deepcopy(dict(payload)),
        }
        row = {**unsigned, "record_hash": canonical_digest(unsigned)}
        name = f"{len(rows):06d}_{kind}.json"
        atomic_json(self.root / name, row)
        return row

    def prepare_seed(
        self,
        seed: int,
        state: Mapping[str, Any],
        outcome_access: Mapping[str, Any],
    ) -> dict[str, Any]:
        expected = self.next_seed(tuple(range(seed + 1)))
        if expected != seed:
            raise AtomicSnapshotIntegrityError(
                f"journal expected seed {expected}, not {seed}"
            )
        return self.append(
            "PREPARED", seed=seed,
            payload={
                "initial_state": state,
                "outcome_access": outcome_access,
            },
        )

    def commit_row(
        self,
        seed: int,
        row_id: str,
        state: Mapping[str, Any],
        outcome_access: Mapping[str, Any],
    ) -> dict[str, Any]:
        return self.append(
            "TRI_ARM_ROW_COMMITTED", seed=seed,
            payload={
                "row_id": row_id,
                "staged_state": state,
                "outcome_access": outcome_access,
            },
        )

    def commit_seed(
        self,
        seed: int,
        state: Mapping[str, Any],
        outcome_access: Mapping[str, Any],
    ) -> dict[str, Any]:
        return self.append(
            "COMMITTED", seed=seed,
            payload={
                "final_state": state,
                "outcome_access": outcome_access,
            },
        )

    def fail(
        self,
        seed: int,
        detail: str,
        outcome_access: Mapping[str, Any],
    ) -> None:
        try:
            self.append(
                "FAILED", seed=seed,
                payload={
                    "detail": detail,
                    "outcome_access": outcome_access,
                },
            )
        except Exception:
            pass

    def next_seed(self, seed_ordinals: Sequence[int]) -> int | None:
        rows = self._records()
        prepared: set[int] = set()
        committed: set[int] = set()
        for row in rows:
            seed = int(row["seed_ordinal"])
            if row["kind"] == "PREPARED":
                if seed in prepared or seed in committed:
                    raise AtomicSnapshotIntegrityError(
                        f"duplicate PREPARED seed:{seed}"
                    )
                prepared.add(seed)
            elif row["kind"] in {"TRI_ARM_ROW_COMMITTED", "FAILED"}:
                if seed not in prepared or seed in committed:
                    raise AtomicSnapshotIntegrityError(
                        f"journal row outside PREPARED seed:{seed}"
                    )
            elif row["kind"] == "COMMITTED":
                if seed not in prepared or seed in committed:
                    raise AtomicSnapshotIntegrityError(
                        f"COMMITTED without unique PREPARED:{seed}"
                    )
                committed.add(seed)
        dangling = sorted(prepared - committed)
        if dangling:
            raise NonResumableJournal(
                f"dangling PREPARED seed is nonresumable:{dangling[0]}"
            )
        ordered = tuple(map(int, seed_ordinals))
        committed_prefix = tuple(seed for seed in ordered if seed in committed)
        if committed_prefix != ordered[:len(committed_prefix)]:
            raise AtomicSnapshotIntegrityError(
                "journal committed seeds are not a contiguous prefix"
            )
        for seed in ordered:
            if int(seed) not in committed:
                return int(seed)
        return None

    def restored_outcome_guard(self) -> OutcomeAccessGuard:
        rows = self._records()
        if not rows:
            return OutcomeAccessGuard()
        prepared = {int(row["seed_ordinal"]) for row in rows if row["kind"] == "PREPARED"}
        committed = [row for row in rows if row["kind"] == "COMMITTED"]
        if prepared - {int(row["seed_ordinal"]) for row in committed}:
            raise NonResumableJournal("dangling PREPARED outcome counter")
        if not committed:
            return OutcomeAccessGuard()
        manifest = committed[-1]["payload"]["outcome_access"]
        return OutcomeAccessGuard(
            count=int(manifest["count"]),
            event_ids=tuple(map(str, manifest["event_ids"])),
        )


class TriArmAdapter(Protocol):
    def clone(self, arm: Any) -> Any: ...
    def state_manifest(self, arm: Any) -> dict[str, Any]: ...
    def preflight_state(self, arm: Any, arm_id: str, row: Mapping[str, Any]) -> None: ...
    def open(self, arm: Any, arm_id: str, row: Mapping[str, Any]) -> Any: ...
    def verify_commitments(self, commitments: Mapping[str, Any], row: Mapping[str, Any]) -> None: ...
    def mint(self, arm: Any, arm_id: str, row: Mapping[str, Any], commitment: Any, guard: OutcomeAccessGuard) -> Any: ...
    def consume(self, arm: Any, arm_id: str, row: Mapping[str, Any], receipt: Any) -> None: ...
    def validate(self, arm: Any, arm_id: str, row: Mapping[str, Any]) -> None: ...


def _tri_state(
    arms: Mapping[str, Any], adapter: TriArmAdapter
) -> dict[str, Any]:
    return {arm: adapter.state_manifest(arms[arm]) for arm in ARMS}


def execute_seed_atomically(
    *,
    seed: int,
    live_arms: MutableMapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    adapter: TriArmAdapter,
    journal: DurableHashJournal,
    guard: OutcomeAccessGuard,
    preflight_receipt: Mapping[str, Any],
    snapshot_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Execute row-major tri-arm barriers, committing live state only by seed."""

    if set(live_arms) != set(ARMS):
        raise AtomicSnapshotIntegrityError("live tri-arm coverage mismatch")
    verify_preflight_receipt(preflight_receipt, snapshot_manifest, guard)
    restored_guard = journal.restored_outcome_guard()
    if restored_guard.manifest() != guard.manifest():
        raise AtomicSnapshotIntegrityError(
            "live outcome counter differs from durable journal"
        )
    initial = _tri_state(live_arms, adapter)
    journal.prepare_seed(seed, initial, guard.manifest())
    staged = {arm: adapter.clone(live_arms[arm]) for arm in ARMS}
    try:
        for row in rows:
            for arm in ARMS:
                adapter.preflight_state(staged[arm], arm, row)
            commitments = {
                arm: adapter.open(staged[arm], arm, row) for arm in ARMS
            }
            adapter.verify_commitments(commitments, row)
            receipts = {
                arm: adapter.mint(
                    staged[arm], arm, row, commitments[arm], guard
                ) for arm in ARMS
            }
            for arm in ARMS:
                adapter.consume(staged[arm], arm, row, receipts[arm])
            for arm in ARMS:
                adapter.validate(staged[arm], arm, row)
            journal.commit_row(
                seed, str(row["row_id"]), _tri_state(staged, adapter),
                guard.manifest(),
            )
        final_state = _tri_state(staged, adapter)
        journal.commit_seed(seed, final_state, guard.manifest())
    except Exception as exc:
        journal.fail(seed, f"{type(exc).__name__}:{exc}", guard.manifest())
        if _tri_state(live_arms, adapter) != initial:
            raise AtomicSnapshotIntegrityError(
                "failed transaction mutated live tri-arm state"
            ) from exc
        raise
    live_arms.clear()
    live_arms.update(staged)
    return {
        "seed_ordinal": seed,
        "row_count": len(rows),
        "outcome_access": guard.manifest(),
        "initial_state_digest": canonical_digest(initial),
        "final_state_digest": canonical_digest(final_state),
        "journal_next_seed": journal.next_seed((seed, seed + 1)),
    }


@dataclass
class SyntheticHarnessArm:
    arm: str
    mode: str
    experiment_identity: str = "synthetic-atomic-canary"
    source_organism_identity: str = "synthetic-source"
    source_state_identity: str = "synthetic-state"
    candidate_population_identity: str = "synthetic-candidates"
    topology_identity: str = "synthetic-topology"
    polarity: str = "POSITIVE"
    authority: bool = False
    value: int = 0
    history: tuple[dict[str, Any], ...] = ()
    pending: str | None = None
    layout: dict[str, int] = field(default_factory=dict)

    @property
    def lawful_initial_authority(self) -> bool:
        return self.authority is (self.mode == "legacy")

    def semantic_manifest(self) -> dict[str, Any]:
        return {
            "arm": self.arm,
            "mode": self.mode,
            "experiment_identity": self.experiment_identity,
            "source_organism_identity": self.source_organism_identity,
            "source_state_identity": self.source_state_identity,
            "candidate_population_identity": self.candidate_population_identity,
            "topology_identity": self.topology_identity,
            "polarity": self.polarity,
            "authority": self.authority,
            "value": self.value,
            "history": list(self.history),
            "pending": self.pending,
            "layout": dict(sorted(self.layout.items())),
        }


@dataclass
class SyntheticTriArmAdapter:
    fail_stage: str | None = None
    fail_arm: str | None = None

    def _maybe_fail(self, stage: str, arm: str | None = None) -> None:
        if self.fail_stage == stage and (
            self.fail_arm is None or self.fail_arm == arm
        ):
            raise InjectedHarnessFailure(f"{stage}:{arm}")

    def clone(self, arm: SyntheticHarnessArm) -> SyntheticHarnessArm:
        return copy.deepcopy(arm)

    def state_manifest(self, arm: SyntheticHarnessArm) -> dict[str, Any]:
        return arm.semantic_manifest()

    def preflight_state(self, arm: SyntheticHarnessArm, arm_id: str, row: Mapping[str, Any]) -> None:
        self._maybe_fail("preflight", arm_id)
        if arm.arm != arm_id or arm.pending is not None:
            raise AtomicSnapshotIntegrityError("synthetic preflight state mismatch")

    def open(self, arm: SyntheticHarnessArm, arm_id: str, row: Mapping[str, Any]) -> dict[str, Any]:
        self._maybe_fail("open", arm_id)
        arm.pending = str(row["row_id"])
        return {"row_id": str(row["row_id"]), "option": row.get("option", "x")}

    def verify_commitments(self, commitments: Mapping[str, Any], row: Mapping[str, Any]) -> None:
        self._maybe_fail("commitment", None)
        if len({canonical_digest(value) for value in commitments.values()}) != 1:
            raise AtomicSnapshotIntegrityError("tri-arm commitment mismatch")

    def mint(self, arm: SyntheticHarnessArm, arm_id: str, row: Mapping[str, Any], commitment: Any, guard: OutcomeAccessGuard) -> dict[str, Any]:
        self._maybe_fail("mint", arm_id)
        guard.open(f"{row['row_id']}:{arm_id}")
        return {
            "row_id": str(row["row_id"]),
            "outcome": bool(row.get("outcomes", {}).get(arm_id, True)),
        }

    def consume(self, arm: SyntheticHarnessArm, arm_id: str, row: Mapping[str, Any], receipt: Any) -> None:
        self._maybe_fail("consume", arm_id)
        if arm.pending != receipt["row_id"]:
            raise AtomicSnapshotIntegrityError("synthetic pending mismatch")
        arm.value += 1 if receipt["outcome"] else -1
        arm.history = (*arm.history, copy.deepcopy(dict(receipt)))
        arm.pending = None

    def validate(self, arm: SyntheticHarnessArm, arm_id: str, row: Mapping[str, Any]) -> None:
        self._maybe_fail("invariant", arm_id)
        if arm.pending is not None:
            raise AtomicSnapshotIntegrityError("synthetic pending leaked")


def synthetic_arm_factory(seed: int) -> dict[str, SyntheticHarnessArm]:
    del seed
    return {
        "A": SyntheticHarnessArm("A", "prospective", authority=False),
        "B": SyntheticHarnessArm("B", "legacy", authority=True),
        "C": SyntheticHarnessArm("C", "prospective", authority=False),
    }


def _legacy_science_inputs() -> tuple[Any, dict[str, Any], dict[str, Any]]:
    from . import native_prospective_evidence_v2_science as science

    prefix = json.loads((science.ROOT / science.PREFIX_MANIFEST_PATH).read_text())
    preoutcome = json.loads((science.ROOT / science.EXPOSURE_PATH).read_text())
    if (science.ROOT / science.RESULT_PATH).exists():
        raise AtomicSnapshotIntegrityError(
            "closed legacy package unexpectedly has canonical result"
        )
    if preoutcome.get("suffix_outcomes_opened") is not False:
        raise AtomicSnapshotIntegrityError(
            "preserved preoutcome artifact is not outcome-pristine"
        )
    return science, prefix, preoutcome


def build_legacy_diagnosis(
    output_path: Path,
) -> dict[str, Any]:
    """Reproduce the raw/semantic diagnosis without opening an outcome."""

    science, prefix, preoutcome = _legacy_science_inputs()
    entry = prefix["results"][0]
    with legacy_main_graph_compatibility():
        original = science.load_prefix_wrapper(entry)
    arms = science.candidate_identical_arms(original)
    rows = {}
    for arm in ARMS:
        frozen = preoutcome["arms"][arm]["per_seed"][0]
        raw = arms[arm].dumps()
        semantic = v2_semantic_identity(arms[arm])
        rows[arm] = {
            "frozen_raw_sha256": frozen["payload_sha256"],
            "reconstructed_raw_sha256": sha256_bytes(raw),
            "raw_equal": frozen["payload_sha256"] == sha256_bytes(raw),
            "frozen_continuation_digest": frozen["continuation_digest"],
            "reconstructed_continuation_digest": semantic[
                "continuation_digest"
            ],
            "semantic_equal": frozen["continuation_digest"] == semantic[
                "continuation_digest"
            ],
            "semantic_identity_digest": canonical_digest(semantic),
        }
    diagnosis = {
        "schema_version": "native_v2_atomic_snapshot_legacy_diagnosis.v1",
        "source_prefix_sha256": sha256_file(
            science.ROOT / science.PREFIX_MANIFEST_PATH
        ),
        "source_preoutcome_sha256": sha256_file(
            science.ROOT / science.EXPOSURE_PATH
        ),
        "construction": {
            "preoutcome": "three separate candidate_identical_arms calls",
            "canonical_suffix": "one candidate_identical_arms call retaining A/B/C",
        },
        "seed_ordinal": 0,
        "arms": rows,
        "nonalias": {
            "wrapper": arms["A"] is not arms["B"],
            "base": arms["A"].base is not arms["B"].base,
            "envelope": arms["A"].base.envelope is not arms["B"].base.envelope,
            "r0": arms["A"].base.r0 is not arms["B"].base.r0,
            "states": arms["A"].states is not arms["B"].states,
        },
        "all_semantic_equal": all(row["semantic_equal"] for row in rows.values()),
        "any_raw_different": any(not row["raw_equal"] for row in rows.values()),
        "outcome_access": {"count": 0, "event_ids": []},
        "verdict": "raw_pickle_is_transport_only;canonical_continuation_is_semantic",
    }
    diagnosis["diagnosis_digest"] = canonical_digest(diagnosis)
    atomic_json(output_path, diagnosis)
    return diagnosis


def run_synthetic_atomic_canary(
    *,
    output_path: Path,
    journal_root: Path,
) -> dict[str, Any]:
    manifest = {"manifest_digest": "synthetic-atomic-snapshot-manifest"}
    receipt = {
        "schema_version": PREFLIGHT_RECEIPT_SCHEMA,
        "manifest_digest": manifest["manifest_digest"],
        "coverage": {"complete": True},
        "outcome_access": {"count": 0, "event_ids": []},
    }
    receipt["receipt_digest"] = canonical_digest(receipt)
    live = synthetic_arm_factory(0)
    initial = {arm: live[arm].semantic_manifest() for arm in ARMS}
    guard = OutcomeAccessGuard()
    journal = DurableHashJournal(journal_root)
    execution = execute_seed_atomically(
        seed=0,
        live_arms=live,
        rows=(
            {"row_id": "synthetic-row-0", "outcomes": {arm: True for arm in ARMS}},
            {"row_id": "synthetic-row-1", "outcomes": {arm: False for arm in ARMS}},
        ),
        adapter=SyntheticTriArmAdapter(),
        journal=journal,
        guard=guard,
        preflight_receipt=receipt,
        snapshot_manifest=manifest,
    )
    records = journal._records()
    result = {
        "schema_version": "native_v2_synthetic_atomic_canary.v1",
        "engineering_only": True,
        "rows": 2,
        "arms": list(ARMS),
        "initial_state_digest": canonical_digest(initial),
        "final_state_digest": canonical_digest({
            arm: live[arm].semantic_manifest() for arm in ARMS
        }),
        "values": {arm: live[arm].value for arm in ARMS},
        "outcome_access": guard.manifest(),
        "journal_record_kinds": [row["kind"] for row in records],
        "journal_chain_digest": canonical_digest(records),
        "restart_next_seed": journal.next_seed((0, 1)),
        "execution": execution,
        "old_suffix_used": False,
    }
    result["result_digest"] = canonical_digest(result)
    atomic_json(output_path, result)
    return result


def run_legacy_atomic_snapshot_reclosure(
    output_root: Path = DEFAULT_RECLOSURE_ROOT,
) -> dict[str, Any]:
    """Run the one outcome-free 96-arm preflight and synthetic canary."""

    if output_root.exists():
        raise FileExistsError(
            f"refusing to overwrite reclosure package: {output_root}"
        )
    protected = verify_protected_v2_1()
    science, prefix, preoutcome = _legacy_science_inputs()
    diagnosis = build_legacy_diagnosis(output_root / "legacy_diagnosis.json")
    entries = {int(item["ordinal"]): item for item in prefix["results"]}
    construction_calls: list[int] = []

    def arm_factory(seed: int) -> Mapping[str, NativeProspectiveAuthorityV2]:
        construction_calls.append(seed)
        with legacy_main_graph_compatibility():
            original = science.load_prefix_wrapper(entries[seed])
        return science.candidate_identical_arms(original)

    codec = V2SnapshotCodec(legacy_main_compatibility=True)
    source_manifest = {
        "prefix_sha256": sha256_file(science.ROOT / science.PREFIX_MANIFEST_PATH),
        "preoutcome_sha256": sha256_file(science.ROOT / science.EXPOSURE_PATH),
        "preoutcome_digest": preoutcome["preoutcome_digest"],
        "protected_hashes": protected,
    }
    manifest = persist_arm_snapshots_once(
        seed_ordinals=DEFAULT_SEED_ORDINALS,
        arm_factory=arm_factory,
        package_root=output_root,
        codec=codec,
        experiment_id="native_v2_atomic_snapshot_reclosure.engineering.v1",
        source_manifest_digest=canonical_digest(source_manifest),
        metadata={
            "engineering_only": True,
            "legacy_main_compatibility_loader": True,
            "future_graph_module": (
                "recon_lite_chess.autogrowth."
                "native_v2_atomic_snapshot_graph"
            ),
            "old_suffix_used": False,
        },
    )
    if construction_calls != list(DEFAULT_SEED_ORDINALS):
        raise AtomicSnapshotIntegrityError(
            "arm factory was not called exactly once per seed"
        )
    guard = OutcomeAccessGuard()
    receipt, restored = global_all_arm_preflight(
        manifest_path=output_root / "arm_snapshot_manifest.json",
        package_root=output_root,
        receipt_path=output_root / "global_preflight_receipt.json",
        failure_path=output_root / "global_preflight_failure.json",
        codec=codec,
        guard=guard,
        required_seed_ordinals=DEFAULT_SEED_ORDINALS,
    )
    if len(restored) != 96 or guard.count != 0:
        raise AtomicSnapshotIntegrityError(
            "legacy global preflight did not close 96 arms outcome-free"
        )
    canary = run_synthetic_atomic_canary(
        output_path=output_root / "synthetic_atomic_canary.json",
        journal_root=output_root / "synthetic_journal",
    )
    return {
        "diagnosis_digest": diagnosis["diagnosis_digest"],
        "manifest_digest": manifest["manifest_digest"],
        "preflight_receipt_digest": receipt["receipt_digest"],
        "synthetic_canary_digest": canary["result_digest"],
        "snapshot_count": len(manifest["entries"]),
        "outcome_access_count": guard.count,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", choices=("run-reclosure", "diagnose-legacy")
    )
    parser.add_argument(
        "--output-root", type=Path, default=DEFAULT_RECLOSURE_ROOT
    )
    args = parser.parse_args(argv)
    if args.command == "run-reclosure":
        result = run_legacy_atomic_snapshot_reclosure(args.output_root)
    else:
        result = build_legacy_diagnosis(
            args.output_root / "legacy_diagnosis.json"
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


__all__ = [
    "ARMS",
    "AtomicSnapshotIntegrityError",
    "DurableHashJournal",
    "InjectedHarnessFailure",
    "NonResumableJournal",
    "OutcomeAccessGuard",
    "PickleSemanticCodec",
    "SyntheticHarnessArm",
    "SyntheticTriArmAdapter",
    "V2SnapshotCodec",
    "canonical_digest",
    "execute_seed_atomically",
    "first_differing_byte",
    "global_all_arm_preflight",
    "json_pointer_differences",
    "persist_arm_snapshots_once",
    "synthetic_arm_factory",
    "v2_semantic_identity",
]


if __name__ == "__main__":
    raise SystemExit(main())
