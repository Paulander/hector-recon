"""Outer canonical-contract compatibility for the frozen V2 cohort.

This module is deliberately separate from the stopped review-repair runner.  It
can validate and restore the already-persisted cohort, but it has no exposure or
outcome execution entry point.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping, Sequence

from . import native_v2_fresh_discriminator_review_repair_v2 as stopped
from .native_v2_atomic_snapshot_harness import (
    ARMS,
    OutcomeAccessGuard,
    canonical_digest,
    json_pointer_differences,
)


ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ID = "native_v2_frozen_cohort_canonical_contract_reclosure.v1"
PACKAGE_DIR = Path(
    "reports/autogrowth/native_authority/"
    "v2_frozen_cohort_canonical_contract_reclosure"
)
STOPPED_PACKAGE_DIR = Path(
    "reports/autogrowth/native_authority/"
    "v2_fresh_discriminator_review_repair_v2"
)
PREFIX_MANIFEST_PATH = STOPPED_PACKAGE_DIR / "prefix_candidate_manifest.json"
SNAPSHOT_PACKAGE_DIR = STOPPED_PACKAGE_DIR / "arm_snapshot_package"
SNAPSHOT_TRANSPORT_PATH = SNAPSHOT_PACKAGE_DIR / "arm_snapshot_manifest.json.gz"
SNAPSHOT_TRANSPORT_BINDING_PATH = (
    SNAPSHOT_PACKAGE_DIR / "arm_snapshot_manifest_transport.json"
)
PREFLIGHT_RECEIPT_PATH = SNAPSHOT_PACKAGE_DIR / "global_preflight_receipt.json"
SOURCE_MANIFEST_PATH = PACKAGE_DIR / "source_manifest.json"
ARTIFACT_BINDING_PATH = PACKAGE_DIR / "artifact_binding_manifest.json"
RESULT_PATH = PACKAGE_DIR / "canonical_contract_verification.json"
FAILURE_PATH = PACKAGE_DIR / "canonical_contract_verification_failure.json"

DISCOVERY_COMMIT = "ca9c45803b84794ce693884f434a7a24ea5208d9"
ORGANISM_COMMIT = "58ed832b912629a25a1450acc1007c011e958840"
ABORT_COMMIT = "a504ba919d92e7f1d1838a3ca318eac3d983811b"
PREFIX_MANIFEST_SHA256 = (
    "b927528e1566f7c057cd5bedbf48d69b449633330c9a010c2667e29d22c0c542"
)
PREFIX_MANIFEST_DIGEST = (
    "9397f9734d42dbcfd0d614d5c30accd5253a73020b6c260f1a095db585bc642e"
)
RAW_SNAPSHOT_MANIFEST_SIZE = 1_129_782_531
RAW_SNAPSHOT_MANIFEST_SHA256 = (
    "ccb91d226c61b3354cb1c89cc939123c01a24723a0868ac5da36bf9b14a0b2e4"
)
RAW_SNAPSHOT_MANIFEST_DIGEST = (
    "9415a2cf6527de69e8048b6b0b33e46be92180992fcac8931dfaafa95f67eb68"
)
COMPRESSED_SNAPSHOT_MANIFEST_SHA256 = (
    "92b8e7aa1b437281e346ddc57b1f4cb5c139ef68190c57f1699e6acd86f8d43f"
)
PREFLIGHT_RECEIPT_SHA256 = (
    "a20aec5ac0263deb6780c7426a5d2c3c02e92e0279f121735b2c1c3ca33afb92"
)
PREFLIGHT_RECEIPT_DIGEST = (
    "bfd01aa67abbbb18849f5e15f2a8b05901fdd5ad158095612f1fda8b8033ec2e"
)
SEED_ZERO_CONTRACT_DIGEST = (
    "a5f275b7dc3d897f7870535d7e0f471969eb3ff8c9bec2452d77f8445c9d95aa"
)

PROTECTED_SOURCE_HASHES = {
    "src/recon_lite_chess/autogrowth/"
    "native_v2_fresh_discriminator_review_repair_v2.py": (
        "75cfd4221c05665259e17c7dcc3bc2a3ebff9b53e6b0868bb019246742bfaeae"
    ),
    "src/recon_lite_chess/autogrowth/"
    "native_prospective_evidence_authority_v2.py": (
        "25945864fd998caf22ae12cbcb9bcb4779447337c0079f705640c63d2356f029"
    ),
    "src/recon_lite_chess/autogrowth/"
    "native_prospective_evidence_authority_v2_lab.py": (
        "f3aee5cccf761af1cb6a5de94b886d5e758c0a07cb0f6d77b8898f662ca73b58"
    ),
    "src/recon_lite_chess/autogrowth/native_v2_atomic_snapshot_harness.py": (
        "8611853ca56c2dab3e2a44ebad18997f9d9d55578627acbaff6e727a578fd894"
    ),
    "src/recon_lite_chess/autogrowth/native_v2_atomic_snapshot_graph.py": (
        "d2516068af30ea59b5c544286c677b7dbcc267d540f89ea35e5edb3a6f14aa68"
    ),
}

SOURCE_FILES = (
    "src/recon_lite_chess/autogrowth/"
    "native_v2_frozen_cohort_canonical_contract_reclosure.py",
    "tests/autogrowth/"
    "test_native_v2_frozen_cohort_canonical_contract_reclosure.py",
    "docs/autogrowth/"
    "NATIVE_V2_FROZEN_COHORT_CANONICAL_CONTRACT_RECLOSURE_PREREGISTRATION_20260727.md",
)

DETERMINISTIC_ENV = {
    "PYTHONHASHSEED": "0",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "TZ": "UTC",
    "LC_ALL": "C.UTF-8",
    "LANG": "C.UTF-8",
}

ORDER_MAP = {
    "ascending": tuple(range(32)),
    "descending": tuple(reversed(range(32))),
    "even_then_odd": (*range(0, 32, 2), *range(1, 32, 2)),
}

STOPPED_OUTPUT_PATHS = (
    STOPPED_PACKAGE_DIR / "preoutcome_exposure_admission.json",
    STOPPED_PACKAGE_DIR / "execution_manifest.json",
    STOPPED_PACKAGE_DIR / "science_journal",
    STOPPED_PACKAGE_DIR / "science_carrier",
    STOPPED_PACKAGE_DIR / "canonical_result.json.gz",
)


class CanonicalContractIntegrityError(RuntimeError):
    """A frozen outer-contract or artifact binding failed."""


class CanonicalContractMismatch(CanonicalContractIntegrityError):
    """Complete canonical contract values differ."""

    def __init__(self, manifest: Mapping[str, Any]) -> None:
        self.manifest = copy.deepcopy(dict(manifest))
        first = self.manifest["differences"][0]
        super().__init__(
            "canonical contract mismatch:"
            f"seed={self.manifest['seed_ordinal']}:path={first['path']}"
        )


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def _require_clean_worktree() -> None:
    if _git("status", "--porcelain=v1"):
        raise CanonicalContractIntegrityError("closure requires a clean worktree")


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite frozen artifact:{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        value, indent=2, sort_keys=True, allow_nan=False
    ).encode("utf-8") + b"\n"
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise CanonicalContractIntegrityError(f"expected object:{path}")
    return value


def _unsigned(value: Mapping[str, Any], signature_field: str) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != signature_field}


def _verify_signed(
    value: Mapping[str, Any], signature_field: str, *, label: str
) -> str:
    expected = value.get(signature_field)
    observed = digest(_unsigned(value, signature_field))
    if expected != observed:
        raise CanonicalContractIntegrityError(
            f"{label} self-digest mismatch:expected={expected}:observed={observed}"
        )
    return observed


def _verify_commit_ancestry() -> None:
    for commit in (DISCOVERY_COMMIT, ORGANISM_COMMIT, ABORT_COMMIT):
        subprocess.run(
            ("git", "cat-file", "-e", f"{commit}^{{commit}}"),
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if subprocess.run(
            ("git", "merge-base", "--is-ancestor", commit, "HEAD"),
            cwd=ROOT,
            check=False,
        ).returncode != 0:
            raise CanonicalContractIntegrityError(
                f"bound commit is not an ancestor:{commit}"
            )


def verify_static_bindings() -> dict[str, Any]:
    _verify_commit_ancestry()
    protected = {}
    for relative, expected in PROTECTED_SOURCE_HASHES.items():
        observed = sha256_file(ROOT / relative)
        protected[relative] = observed
        if observed != expected:
            raise CanonicalContractIntegrityError(
                f"protected source changed:{relative}:{observed}"
            )
    fixed_files = {
        PREFIX_MANIFEST_PATH: PREFIX_MANIFEST_SHA256,
        SNAPSHOT_TRANSPORT_PATH: COMPRESSED_SNAPSHOT_MANIFEST_SHA256,
        PREFLIGHT_RECEIPT_PATH: PREFLIGHT_RECEIPT_SHA256,
    }
    observed_files = {}
    for relative, expected in fixed_files.items():
        observed = sha256_file(ROOT / relative)
        observed_files[relative.as_posix()] = observed
        if observed != expected:
            raise CanonicalContractIntegrityError(
                f"bound artifact changed:{relative}:{observed}"
            )
    transport = _load_json(ROOT / SNAPSHOT_TRANSPORT_BINDING_PATH)
    if (
        transport.get("raw", {}).get("size") != RAW_SNAPSHOT_MANIFEST_SIZE
        or transport.get("raw", {}).get("sha256")
        != RAW_SNAPSHOT_MANIFEST_SHA256
        or transport.get("raw", {}).get("canonical_manifest_digest")
        != RAW_SNAPSHOT_MANIFEST_DIGEST
        or transport.get("compressed", {}).get("sha256")
        != COMPRESSED_SNAPSHOT_MANIFEST_SHA256
    ):
        raise CanonicalContractIntegrityError("manifest transport binding changed")
    prefix = _load_json(ROOT / PREFIX_MANIFEST_PATH)
    if (
        _verify_signed(
            prefix, "prefix_manifest_digest", label="prefix manifest"
        )
        != PREFIX_MANIFEST_DIGEST
        or len(prefix.get("results", ())) != 32
        or prefix.get("all_32_retained") is not True
    ):
        raise CanonicalContractIntegrityError("prefix cohort binding changed")
    receipt = _load_json(ROOT / PREFLIGHT_RECEIPT_PATH)
    if (
        _verify_signed(receipt, "receipt_digest", label="preflight receipt")
        != PREFLIGHT_RECEIPT_DIGEST
        or receipt.get("manifest_digest") != RAW_SNAPSHOT_MANIFEST_DIGEST
        or receipt.get("coverage")
        != {
            "seed_count": 32,
            "arm_count": 3,
            "artifact_count": 96,
            "complete": True,
        }
        or receipt.get("outcome_access") != {"count": 0, "event_ids": []}
    ):
        raise CanonicalContractIntegrityError("preflight receipt binding changed")
    target_counts = {
        "planted": sum(
            item["targets"].get("planted") is not None
            for item in prefix["results"]
        ),
        "selected_comparison": sum(
            item["targets"].get("selected_spurious") is not None
            for item in prefix["results"]
        ),
    }
    if target_counts != {"planted": 32, "selected_comparison": 30}:
        raise CanonicalContractIntegrityError(
            f"frozen target counts changed:{target_counts}"
        )
    return {
        "protected_source_hashes": protected,
        "artifact_hashes": observed_files,
        "transport_binding_sha256": sha256_file(
            ROOT / SNAPSHOT_TRANSPORT_BINDING_PATH
        ),
        "prefix": prefix,
        "receipt": receipt,
        "target_counts": target_counts,
    }


def reconstruct_snapshot_manifest() -> tuple[dict[str, Any], dict[str, Any]]:
    compressed_path = ROOT / SNAPSHOT_TRANSPORT_PATH
    if sha256_file(compressed_path) != COMPRESSED_SNAPSHOT_MANIFEST_SHA256:
        raise CanonicalContractIntegrityError("compressed manifest hash mismatch")
    with tempfile.TemporaryDirectory(
        prefix="native-v2-canonical-contract-"
    ) as temporary:
        raw_path = Path(temporary) / "arm_snapshot_manifest.json"
        hasher = hashlib.sha256()
        size = 0
        with gzip.open(compressed_path, "rb") as source, raw_path.open("wb") as sink:
            while chunk := source.read(1024 * 1024):
                sink.write(chunk)
                hasher.update(chunk)
                size += len(chunk)
        raw_sha256 = hasher.hexdigest()
        if (
            size != RAW_SNAPSHOT_MANIFEST_SIZE
            or raw_sha256 != RAW_SNAPSHOT_MANIFEST_SHA256
        ):
            raise CanonicalContractIntegrityError(
                "reconstructed raw manifest transport mismatch"
            )
        with raw_path.open("r", encoding="utf-8") as handle:
            manifest = json.load(handle)
    if not isinstance(manifest, dict):
        raise CanonicalContractIntegrityError("snapshot manifest is not an object")
    unsigned = _unsigned(manifest, "manifest_digest")
    observed_manifest_digest = canonical_digest(unsigned)
    if (
        manifest.get("manifest_digest") != observed_manifest_digest
        or observed_manifest_digest != RAW_SNAPSHOT_MANIFEST_DIGEST
    ):
        raise CanonicalContractIntegrityError("snapshot manifest digest mismatch")
    expected_pairs = {(ordinal, arm) for ordinal in range(32) for arm in ARMS}
    observed_pairs = {
        (int(item["seed_ordinal"]), str(item["arm"]))
        for item in manifest.get("entries", ())
    }
    if observed_pairs != expected_pairs or len(manifest.get("entries", ())) != 96:
        raise CanonicalContractIntegrityError("snapshot manifest lacks exact 96")
    contracts = manifest.get("metadata", {}).get("per_seed_identity_contracts")
    if not isinstance(contracts, dict) or set(contracts) != {
        str(ordinal) for ordinal in range(32)
    }:
        raise CanonicalContractIntegrityError("frozen contracts are incomplete")
    for ordinal in range(32):
        verify_contract_self_digest(
            contracts[str(ordinal)], label=f"stored seed {ordinal}"
        )
    return manifest, {
        "compressed_sha256": COMPRESSED_SNAPSHOT_MANIFEST_SHA256,
        "raw_sha256": raw_sha256,
        "raw_size": size,
        "manifest_digest": observed_manifest_digest,
    }


def contract_without_digest(contract: Mapping[str, Any]) -> dict[str, Any]:
    return _unsigned(contract, "contract_digest")


def verify_contract_self_digest(
    contract: Mapping[str, Any], *, label: str
) -> str:
    return _verify_signed(contract, "contract_digest", label=label)


def sign_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(dict(contract))
    value.pop("contract_digest", None)
    value["contract_digest"] = digest(value)
    return value


def canonical_json_value(value: Any) -> Any:
    return json.loads(canonical_bytes(value).decode("utf-8"))


def compare_complete_contracts(
    expected: Mapping[str, Any],
    observed: Mapping[str, Any],
    *,
    seed_ordinal: int,
) -> dict[str, Any]:
    expected_digest = verify_contract_self_digest(
        expected, label=f"expected seed {seed_ordinal}"
    )
    observed_digest = verify_contract_self_digest(
        observed, label=f"observed seed {seed_ordinal}"
    )
    expected_bytes = canonical_bytes(expected)
    observed_bytes = canonical_bytes(observed)
    if expected_bytes != observed_bytes:
        normalized_expected = canonical_json_value(expected)
        normalized_observed = canonical_json_value(observed)
        differences = json_pointer_differences(
            normalized_expected, normalized_observed
        )
        failure = {
            "schema_version": "native_v2_canonical_contract_mismatch.v1",
            "seed_ordinal": int(seed_ordinal),
            "expected_contract_digest": expected_digest,
            "observed_contract_digest": observed_digest,
            "difference_count": len(differences),
            "differences": differences[:32],
            "differences_bounded_at": 32,
        }
        failure["failure_digest"] = digest(failure)
        raise CanonicalContractMismatch(failure)
    if expected_digest != observed_digest:
        raise CanonicalContractIntegrityError(
            f"canonical bytes equal but self-digests differ:seed={seed_ordinal}"
        )
    return {
        "seed_ordinal": int(seed_ordinal),
        "contract_digest": expected_digest,
        "canonical_equal": True,
        "canonical_size": len(expected_bytes),
        "raw_python_equal": expected == observed,
    }


def legacy_raw_contract_check(
    expected: Mapping[str, Any],
    observed: Mapping[str, Any],
    *,
    seed_ordinal: int,
) -> None:
    """Reproduce the stopped runner's representation-sensitive comparison."""

    if observed != expected:
        raise stopped.FreshScientificIntegrityError(
            f"snapshot candidate contract mismatch:{int(seed_ordinal)}"
        )


def _verify_target_identity(
    prefix_item: Mapping[str, Any],
    arms: Mapping[str, Any],
    *,
    ordinal: int,
) -> None:
    targets = prefix_item["targets"]
    for arm in ARMS:
        wrapper = arms[arm]
        if (
            wrapper.experimental_identity["candidate_population_identity"]
            != targets["candidate_population_digest"]
            or digest(stopped.structural_identity(wrapper))
            != prefix_item["structural_identity_digest"]
        ):
            raise CanonicalContractIntegrityError(
                f"snapshot candidate population mismatch:{ordinal}:{arm}"
            )
        for name in ("planted", "selected_spurious"):
            target = targets[name]
            if target is None:
                continue
            state = wrapper.states.get(str(target["cell_id"]))
            if (
                state is None
                or digest(state.hypothesis.manifest())
                != target["hypothesis_digest"]
                or list(state.hypothesis.members) != target["members"]
            ):
                raise CanonicalContractIntegrityError(
                    f"snapshot target metadata mismatch:{ordinal}:{arm}:{name}"
                )


def _snapshot_transport_set_digest(manifest: Mapping[str, Any]) -> str:
    rows = []
    for entry in sorted(
        manifest["entries"],
        key=lambda item: (int(item["seed_ordinal"]), str(item["arm"])),
    ):
        path = ROOT / SNAPSHOT_PACKAGE_DIR / str(entry["path"])
        observed_size = path.stat().st_size
        observed_sha256 = sha256_file(path)
        if (
            observed_size != int(entry["compressed_size"])
            or observed_sha256 != entry["compressed_sha256"]
        ):
            raise CanonicalContractIntegrityError(
                f"snapshot transport changed:{entry['seed_ordinal']}:{entry['arm']}"
            )
        rows.append({
            "seed_ordinal": int(entry["seed_ordinal"]),
            "arm": str(entry["arm"]),
            "path": str(entry["path"]),
            "compressed_size": observed_size,
            "compressed_sha256": observed_sha256,
            "raw_size": int(entry["raw_size"]),
            "raw_sha256": str(entry["raw_sha256"]),
            "semantic_identity_digest": str(entry["semantic_identity_digest"]),
        })
    return digest(rows)


def _prefix_transport_set_digest(prefix: Mapping[str, Any]) -> str:
    rows = []
    for item in sorted(prefix["results"], key=lambda value: int(value["ordinal"])):
        path = ROOT / str(item["path"])
        observed_size = path.stat().st_size
        observed_sha256 = sha256_file(path)
        if (
            observed_size != int(item["compressed_size"])
            or observed_sha256 != item["compressed_sha256"]
        ):
            raise CanonicalContractIntegrityError(
                f"prefix organism changed:{item['ordinal']}"
            )
        rows.append({
            "ordinal": int(item["ordinal"]),
            "path": str(item["path"]),
            "compressed_size": observed_size,
            "compressed_sha256": observed_sha256,
            "uncompressed_size": int(item["uncompressed_size"]),
            "uncompressed_sha256": str(item["uncompressed_sha256"]),
        })
    return digest(rows)


def verify_seed_contract(
    manifest: Mapping[str, Any],
    prefix: Mapping[str, Any],
    ordinal: int,
) -> dict[str, Any]:
    expected = manifest["metadata"]["per_seed_identity_contracts"][str(ordinal)]
    arms = {
        arm: stopped._restore_snapshot_entry(manifest, ordinal, arm)
        for arm in ARMS
    }
    codec = stopped.V2SnapshotCodec()
    before = {arm: codec.semantic_identity(arms[arm]) for arm in ARMS}
    before_digest = digest(before)
    observed = stopped.exact_arm_identity_contract(arms)
    comparison = compare_complete_contracts(
        expected, observed, seed_ordinal=ordinal
    )
    _verify_target_identity(prefix["results"][ordinal], arms, ordinal=ordinal)
    after = {arm: codec.semantic_identity(arms[arm]) for arm in ARMS}
    after_digest = digest(after)
    if canonical_bytes(before) != canonical_bytes(after):
        raise CanonicalContractIntegrityError(
            f"contract verification mutated organism:seed={ordinal}"
        )
    return {
        **comparison,
        "before_semantic_set_digest": before_digest,
        "after_semantic_set_digest": after_digest,
        "no_candidate_or_graph_mutation": before_digest == after_digest,
        "planted_target_present": (
            prefix["results"][ordinal]["targets"]["planted"] is not None
        ),
        "selected_comparison_target_present": (
            prefix["results"][ordinal]["targets"]["selected_spurious"]
            is not None
        ),
    }


def _forbidden_stopped_outputs() -> dict[str, bool]:
    return {
        path.as_posix(): (ROOT / path).exists() for path in STOPPED_OUTPUT_PATHS
    }


def _verify_frozen_package_manifests() -> dict[str, Any]:
    source = _load_json(ROOT / SOURCE_MANIFEST_PATH)
    source_digest = _verify_signed(
        source, "source_manifest_digest", label="source manifest"
    )
    for relative, expected in source["source_hashes"].items():
        observed = sha256_file(ROOT / relative)
        if observed != expected:
            raise CanonicalContractIntegrityError(
                f"closure source changed:{relative}:{observed}"
            )
    binding = _load_json(ROOT / ARTIFACT_BINDING_PATH)
    binding_digest = _verify_signed(
        binding, "artifact_binding_digest", label="artifact binding"
    )
    if (
        binding["source_manifest"]["sha256"]
        != sha256_file(ROOT / SOURCE_MANIFEST_PATH)
        or binding["source_manifest"]["digest"] != source_digest
    ):
        raise CanonicalContractIntegrityError("source/artifact binding mismatch")
    return {
        "source_manifest": source,
        "source_manifest_sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
        "source_manifest_digest": source_digest,
        "artifact_binding": binding,
        "artifact_binding_sha256": sha256_file(ROOT / ARTIFACT_BINDING_PATH),
        "artifact_binding_digest": binding_digest,
    }


def verify_order(order_name: str) -> dict[str, Any]:
    started = time.perf_counter()
    if order_name not in ORDER_MAP:
        raise CanonicalContractIntegrityError(f"unknown seed order:{order_name}")
    package = _verify_frozen_package_manifests()
    static = verify_static_bindings()
    manifest, reconstruction = reconstruct_snapshot_manifest()
    binding = package["artifact_binding"]
    if (
        binding["snapshot_manifest"]["manifest_digest"]
        != manifest["manifest_digest"]
        or binding["snapshot_manifest"]["raw_sha256"]
        != reconstruction["raw_sha256"]
    ):
        raise CanonicalContractIntegrityError("frozen manifest binding mismatch")
    snapshot_before = _snapshot_transport_set_digest(manifest)
    prefix_before = _prefix_transport_set_digest(static["prefix"])
    contract_rows = [
        {
            "ordinal": ordinal,
            "contract_digest": verify_contract_self_digest(
                manifest["metadata"]["per_seed_identity_contracts"][str(ordinal)],
                label=f"frozen seed {ordinal}",
            ),
        }
        for ordinal in range(32)
    ]
    if (
        snapshot_before != binding["snapshot_set_digest"]
        or prefix_before != binding["prefix_organism_set_digest"]
        or digest(contract_rows) != binding["contract_set_digest"]
    ):
        raise CanonicalContractIntegrityError(
            "frozen prefix, snapshot, or contract set binding mismatch"
        )
    guard = OutcomeAccessGuard()
    seed_rows = []
    for ordinal in ORDER_MAP[order_name]:
        seed_rows.append(
            verify_seed_contract(manifest, static["prefix"], int(ordinal))
        )
    snapshot_after = _snapshot_transport_set_digest(manifest)
    prefix_after = _prefix_transport_set_digest(static["prefix"])
    if snapshot_before != snapshot_after or prefix_before != prefix_after:
        raise CanonicalContractIntegrityError("frozen artifact mutation detected")
    forbidden = _forbidden_stopped_outputs()
    if any(forbidden.values()):
        raise CanonicalContractIntegrityError(
            f"stopped package output unexpectedly exists:{forbidden}"
        )
    canonical_rows = sorted(seed_rows, key=lambda row: row["seed_ordinal"])
    core = {
        "seed_rows": canonical_rows,
        "snapshot_transport_set_digest": snapshot_after,
        "prefix_transport_set_digest": prefix_after,
        "raw_manifest_reconstruction": reconstruction,
        "outcome_access": guard.manifest(),
        "exposure_rows_read": 0,
        "stopped_output_paths_present": forbidden,
    }
    value = {
        "schema_version": "native_v2_canonical_contract_order_result.v1",
        "package_id": PACKAGE_ID,
        "process_id": os.getpid(),
        "order_name": order_name,
        "evaluation_order": list(ORDER_MAP[order_name]),
        "verified_seed_count": len(canonical_rows),
        "verified_organism_count": len(canonical_rows) * len(ARMS),
        "core": core,
        "cohort_digest": digest(core),
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }
    value["order_result_digest"] = digest(value)
    return value


def _version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def freeze_package_manifests(source_commit: str) -> dict[str, Any]:
    _require_clean_worktree()
    if _git("rev-parse", "HEAD") != source_commit:
        raise CanonicalContractIntegrityError("source freeze commit is not HEAD")
    static = verify_static_bindings()
    source_hashes = {
        relative: sha256_file(ROOT / relative) for relative in SOURCE_FILES
    }
    source = {
        "schema_version": "native_v2_canonical_contract_source_manifest.v1",
        "package_id": PACKAGE_ID,
        "source_freeze_commit": source_commit,
        "source_hashes": source_hashes,
        "protected_source_hashes": copy.deepcopy(PROTECTED_SOURCE_HASHES),
        "deterministic_environment": copy.deepcopy(DETERMINISTIC_ENV),
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "python_chess": _version("python-chess"),
            "pytest": _version("pytest"),
        },
        "preservation": {
            "stopped_runner_byte_identical": True,
            "protected_v2_1_byte_identical": True,
            "snapshot_harness_byte_identical": True,
            "graph_and_registry_byte_identical": True,
        },
    }
    source["source_manifest_digest"] = digest(source)
    _atomic_json(ROOT / SOURCE_MANIFEST_PATH, source)

    manifest, reconstruction = reconstruct_snapshot_manifest()
    prefix_rows = []
    for item in sorted(static["prefix"]["results"], key=lambda row: row["ordinal"]):
        path = ROOT / item["path"]
        if (
            path.stat().st_size != item["compressed_size"]
            or sha256_file(path) != item["compressed_sha256"]
        ):
            raise CanonicalContractIntegrityError(
                f"prefix organism binding mismatch:{item['ordinal']}"
            )
        prefix_rows.append({
            "ordinal": int(item["ordinal"]),
            "path": str(item["path"]),
            "compressed_size": int(item["compressed_size"]),
            "compressed_sha256": str(item["compressed_sha256"]),
            "uncompressed_size": int(item["uncompressed_size"]),
            "uncompressed_sha256": str(item["uncompressed_sha256"]),
        })
    snapshot_rows = []
    for entry in sorted(
        manifest["entries"],
        key=lambda row: (int(row["seed_ordinal"]), str(row["arm"])),
    ):
        snapshot_rows.append({
            "seed_ordinal": int(entry["seed_ordinal"]),
            "arm": str(entry["arm"]),
            "path": str(entry["path"]),
            "compressed_size": int(entry["compressed_size"]),
            "compressed_sha256": str(entry["compressed_sha256"]),
            "raw_size": int(entry["raw_size"]),
            "raw_sha256": str(entry["raw_sha256"]),
            "semantic_identity_digest": str(entry["semantic_identity_digest"]),
        })
    contract_rows = []
    contracts = manifest["metadata"]["per_seed_identity_contracts"]
    for ordinal in range(32):
        contract_rows.append({
            "ordinal": ordinal,
            "contract_digest": verify_contract_self_digest(
                contracts[str(ordinal)], label=f"frozen seed {ordinal}"
            ),
        })
    source_sha256 = sha256_file(ROOT / SOURCE_MANIFEST_PATH)
    binding = {
        "schema_version": "native_v2_canonical_contract_artifact_binding.v1",
        "package_id": PACKAGE_ID,
        "bound_commits": {
            "discovery": DISCOVERY_COMMIT,
            "organisms": ORGANISM_COMMIT,
            "instrument_abort": ABORT_COMMIT,
        },
        "source_manifest": {
            "path": SOURCE_MANIFEST_PATH.as_posix(),
            "sha256": source_sha256,
            "digest": source["source_manifest_digest"],
        },
        "prefix_manifest": {
            "path": PREFIX_MANIFEST_PATH.as_posix(),
            "sha256": PREFIX_MANIFEST_SHA256,
            "digest": PREFIX_MANIFEST_DIGEST,
            "all_32_retained": True,
            "planted_target_count": 32,
            "selected_comparison_target_count": 30,
        },
        "prefix_organisms": prefix_rows,
        "prefix_organism_set_digest": digest(prefix_rows),
        "snapshot_manifest": {
            "compressed_path": SNAPSHOT_TRANSPORT_PATH.as_posix(),
            "compressed_sha256": COMPRESSED_SNAPSHOT_MANIFEST_SHA256,
            "raw_size": reconstruction["raw_size"],
            "raw_sha256": reconstruction["raw_sha256"],
            "manifest_digest": reconstruction["manifest_digest"],
        },
        "snapshots": snapshot_rows,
        "snapshot_set_digest": digest(snapshot_rows),
        "contracts": contract_rows,
        "contract_set_digest": digest(contract_rows),
        "verification_record": {
            "path": PREFLIGHT_RECEIPT_PATH.as_posix(),
            "sha256": PREFLIGHT_RECEIPT_SHA256,
            "digest": PREFLIGHT_RECEIPT_DIGEST,
            "verified_organism_count": 96,
            "outcome_reads": 0,
        },
        "disclosures": {
            "fixed_outcome_blindly_reused_candidate_cohort": True,
            "fixed_synthetic_ecology": True,
            "evaluation_suffix_unopened": True,
            "future_claim_conditional_on_fixed_cohort_and_ecology": True,
            "old_instrument_abort_remains_valid": True,
        },
    }
    binding["artifact_binding_digest"] = digest(binding)
    _atomic_json(ROOT / ARTIFACT_BINDING_PATH, binding)
    return {
        "source_manifest_path": SOURCE_MANIFEST_PATH.as_posix(),
        "source_manifest_sha256": source_sha256,
        "source_manifest_digest": source["source_manifest_digest"],
        "artifact_binding_path": ARTIFACT_BINDING_PATH.as_posix(),
        "artifact_binding_sha256": sha256_file(ROOT / ARTIFACT_BINDING_PATH),
        "artifact_binding_digest": binding["artifact_binding_digest"],
        "prefix_organism_count": len(prefix_rows),
        "snapshot_count": len(snapshot_rows),
        "contract_count": len(contract_rows),
    }


def run_all_order_verification() -> dict[str, Any]:
    _require_clean_worktree()
    if (ROOT / RESULT_PATH).exists() or (ROOT / FAILURE_PATH).exists():
        raise FileExistsError("canonical verification output already exists")
    package = _verify_frozen_package_manifests()
    results = []
    started = time.perf_counter()
    for order_name in ORDER_MAP:
        environment = os.environ.copy()
        environment.update(DETERMINISTIC_ENV)
        completed = subprocess.run(
            (
                sys.executable,
                "-m",
                __name__,
                "verify-order",
                "--order",
                order_name,
            ),
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            failure = {
                "schema_version": "native_v2_canonical_contract_run_failure.v1",
                "package_id": PACKAGE_ID,
                "order_name": order_name,
                "returncode": completed.returncode,
                "stdout": completed.stdout[-20_000:],
                "stderr": completed.stderr[-20_000:],
                "completed_order_count": len(results),
                "outcome_reads": 0,
                "exposure_rows_read": 0,
            }
            failure["failure_digest"] = digest(failure)
            _atomic_json(ROOT / FAILURE_PATH, failure)
            raise CanonicalContractIntegrityError(
                f"fresh-process verification failed:{order_name}"
            )
        results.append(json.loads(completed.stdout))
    cohort_digests = {item["cohort_digest"] for item in results}
    process_ids = {int(item["process_id"]) for item in results}
    if len(cohort_digests) != 1 or len(process_ids) != len(ORDER_MAP):
        raise CanonicalContractIntegrityError(
            "order result or fresh-process identity mismatch"
        )
    for item in results:
        if (
            item["verified_seed_count"] != 32
            or item["verified_organism_count"] != 96
            or item["core"]["outcome_access"] != {"count": 0, "event_ids": []}
            or item["core"]["exposure_rows_read"] != 0
            or not all(
                row["no_candidate_or_graph_mutation"]
                for row in item["core"]["seed_rows"]
            )
        ):
            raise CanonicalContractIntegrityError(
                f"order verification gate failed:{item['order_name']}"
            )
    seed_zero = results[0]["core"]["seed_rows"][0]
    if (
        seed_zero["contract_digest"] != SEED_ZERO_CONTRACT_DIGEST
        or seed_zero["raw_python_equal"] is not False
    ):
        raise CanonicalContractIntegrityError("seed-0 diagnosis did not reproduce")
    value = {
        "schema_version": "native_v2_canonical_contract_verification.v1",
        "package_id": PACKAGE_ID,
        "source_manifest": {
            "sha256": package["source_manifest_sha256"],
            "digest": package["source_manifest_digest"],
        },
        "artifact_binding": {
            "sha256": package["artifact_binding_sha256"],
            "digest": package["artifact_binding_digest"],
        },
        "orders": results,
        "fresh_process_count": len(process_ids),
        "identical_cohort_digest": next(iter(cohort_digests)),
        "verified_seed_count": 32,
        "verified_organism_count": 96,
        "stored_contract_digest_count": 32,
        "seed_zero_contract_digest": seed_zero["contract_digest"],
        "legacy_seed_zero_raw_comparison_aborts": True,
        "canonical_seed_zero_comparison_passes": True,
        "all_orders_identical": True,
        "candidate_or_graph_mutation_count": 0,
        "exposure_rows_read": 0,
        "outcome_access": {"count": 0, "event_ids": []},
        "evaluation_suffix_unopened": True,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }
    value["result_digest"] = digest(value)
    _atomic_json(ROOT / RESULT_PATH, value)
    return value


def _print(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    freeze = commands.add_parser("freeze-manifests")
    freeze.add_argument("--source-commit", required=True)
    verify = commands.add_parser("verify-order")
    verify.add_argument("--order", choices=tuple(ORDER_MAP), required=True)
    commands.add_parser("run-verification")
    args = parser.parse_args(argv)
    try:
        if args.command == "freeze-manifests":
            value = freeze_package_manifests(args.source_commit)
        elif args.command == "verify-order":
            value = verify_order(args.order)
        elif args.command == "run-verification":
            value = run_all_order_verification()
        else:  # pragma: no cover
            raise AssertionError(args.command)
    except CanonicalContractMismatch as exc:
        _print(exc.manifest)
        return 2
    _print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
