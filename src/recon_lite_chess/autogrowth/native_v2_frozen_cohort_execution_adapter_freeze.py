"""Frozen-cohort execution adapter for the accepted V2 identity boundary.

The module is outer orchestration only.  It reuses the immutable V2 driver,
canonical contract comparison, stable launcher, registry, journal, and atomic
execution mechanisms.  This package runs readiness only; exposure and science
commands are frozen for later explicit authorization.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Mapping, MutableMapping, Sequence

from recon_lite_chess.autogrowth import (
    native_v2_fresh_discriminator_review_repair_v2 as driver,
)
from recon_lite_chess.autogrowth import (
    native_v2_frozen_cohort_canonical_contract_reclosure as canonical,
)
from recon_lite_chess.autogrowth import (
    native_v2_frozen_cohort_import_path_launcher_reclosure as launcher,
)


ROOT = driver.ROOT
PACKAGE_ID = "native_v2_frozen_cohort_execution_adapter_freeze.v1"
ADAPTER_MODULE = (
    "recon_lite_chess.autogrowth."
    "native_v2_frozen_cohort_execution_adapter_freeze"
)
DRIVER_MODULE = (
    "recon_lite_chess.autogrowth."
    "native_v2_fresh_discriminator_review_repair_v2"
)
CANONICAL_MODULE = (
    "recon_lite_chess.autogrowth."
    "native_v2_frozen_cohort_canonical_contract_reclosure"
)
LAUNCHER_MODULE = (
    "recon_lite_chess.autogrowth."
    "native_v2_frozen_cohort_import_path_launcher_reclosure"
)

PACKAGE_DIR = Path(
    "reports/autogrowth/native_authority/"
    "v2_frozen_cohort_execution_adapter_freeze"
)
SOURCE_MANIFEST_PATH = PACKAGE_DIR / "source_manifest.json"
ARTIFACT_BINDING_PATH = PACKAGE_DIR / "artifact_binding_manifest.json"
READINESS_PATH = PACKAGE_DIR / "readiness.json"
READINESS_FAILURE_PATH = PACKAGE_DIR / "readiness_failure.json"
EXPOSURE_PATH = PACKAGE_DIR / "preoutcome_exposure.json"
EXECUTION_MANIFEST_PATH = PACKAGE_DIR / "execution_manifest.json"
EXPOSURE_FAILURE_PATH = PACKAGE_DIR / "exposure_failure.json"
SCIENCE_JOURNAL_DIR = PACKAGE_DIR / "science_journal"
SCIENCE_CARRIER_DIR = PACKAGE_DIR / "science_carrier"
RESULT_PATH = PACKAGE_DIR / "canonical_result.json.gz"
SCIENCE_FAILURE_PATH = PACKAGE_DIR / "science_failure.json"

STARTING_HEAD = "2916fb04f4020bc682c29474ec3b1e9cb8dbf405"
PASSING_LAUNCHER_RESULT_SHA256 = (
    "92cf2e099a1f860deef4c90515f6b0617d7b95af521ab1c8604baecccd7202df"
)
ACCEPTED_COHORT_DIGEST = (
    "a144fe94f4479c819756dfc44b22a2594e2b9df09367d571d39ab54007560bb8"
)
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
COMPRESSED_SNAPSHOT_SHA256 = (
    "92b8e7aa1b437281e346ddc57b1f4cb5c139ef68190c57f1699e6acd86f8d43f"
)
PREFLIGHT_RECEIPT_SHA256 = (
    "a20aec5ac0263deb6780c7426a5d2c3c02e92e0279f121735b2c1c3ca33afb92"
)
PREFLIGHT_RECEIPT_DIGEST = (
    "bfd01aa67abbbb18849f5e15f2a8b05901fdd5ad158095612f1fda8b8033ec2e"
)

PASSING_LAUNCHER_RESULT_PATH = (
    launcher.PACKAGE_DIR / "canonical_launcher_verification.json"
)
RAW_SNAPSHOT_MANIFEST_PATH = (
    driver.SNAPSHOT_ROOT / "arm_snapshot_manifest.json"
)
COMPRESSED_SNAPSHOT_PATH = (
    driver.SNAPSHOT_ROOT / "arm_snapshot_manifest.json.gz"
)
PREFLIGHT_RECEIPT_PATH = driver.SNAPSHOT_ROOT / "global_preflight_receipt.json"

SOURCE_FILES = (
    "src/recon_lite_chess/autogrowth/"
    "native_v2_frozen_cohort_execution_adapter_freeze.py",
    "tests/autogrowth/"
    "test_native_v2_frozen_cohort_execution_adapter_freeze.py",
    "docs/autogrowth/"
    "NATIVE_V2_FROZEN_COHORT_EXECUTION_ADAPTER_FREEZE_"
    "PREREGISTRATION_20260727.md",
)

DETERMINISTIC_ENV = copy.deepcopy(launcher.DETERMINISTIC_ENV)
PUBLIC_COMMANDS = ("verify-readiness", "run-exposure", "run-science")

DRIVER_SUFFIX_OUTPUTS = (
    driver.EXPOSURE_PATH,
    driver.EXECUTION_MANIFEST_PATH,
    driver.SCIENCE_JOURNAL_DIR,
    driver.SCIENCE_CARRIER_DIR,
    driver.RESULT_PATH,
)

CRITICAL_GLOBAL_BINDINGS = {
    "driver": (
        "_restore_snapshot_entry",
        "_verify_prefix_snapshot_metadata",
        "_reconstruct_exposure_value",
        "execute_fresh_seed_atomically",
        "committed_seed_results",
        "adjudicate_committed_results",
        "EXPOSURE_PATH",
        "EXECUTION_MANIFEST_PATH",
        "SCIENCE_JOURNAL_DIR",
        "SCIENCE_CARRIER_DIR",
        "RESULT_PATH",
    ),
    "canonical": (
        "compare_complete_contracts",
        "legacy_raw_contract_check",
        "_verify_target_identity",
    ),
    "launcher": ("CHILD_MODULE", "RESULT_PATH", "FAILURE_PATH"),
}


class AdapterIntegrityError(RuntimeError):
    """The frozen execution adapter or an immutable input failed."""


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


def streamed_canonical_identity(value: Any) -> dict[str, Any]:
    """Hash exact canonical JSON bytes without retaining a giant byte string."""

    encoder = json.JSONEncoder(
        sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    hasher = hashlib.sha256()
    size = 0
    for text in encoder.iterencode(value):
        payload = text.encode("utf-8")
        hasher.update(payload)
        size += len(payload)
    return {"sha256": hasher.hexdigest(), "size": size}


def _git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def _require_clean_worktree() -> None:
    if _git("status", "--porcelain=v1"):
        raise AdapterIntegrityError("adapter command requires a clean worktree")


def _require_commit(commit: str) -> None:
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
        raise AdapterIntegrityError(f"required commit is not an ancestor:{commit}")


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
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AdapterIntegrityError(f"expected JSON object:{path}")
    return value


def _verify_self_digest(
    value: Mapping[str, Any], field: str, *, label: str
) -> str:
    expected = value.get(field)
    observed = digest({key: item for key, item in value.items() if key != field})
    if expected != observed:
        raise AdapterIntegrityError(
            f"{label} self-digest mismatch:expected={expected}:observed={observed}"
        )
    return observed


def _path_bytes_in_head(relative: Path) -> bytes:
    name = relative.as_posix()
    completed = subprocess.run(
        ("git", "show", f"HEAD:{name}"),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AdapterIntegrityError(f"required artifact is not committed:{name}")
    return completed.stdout


def require_committed_artifact(relative: Path) -> dict[str, Any]:
    path = ROOT / relative
    payload = path.read_bytes()
    committed = _path_bytes_in_head(relative)
    if payload != committed:
        raise AdapterIntegrityError(f"working artifact differs from HEAD:{relative}")
    return {
        "path": relative.as_posix(),
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def build_public_command(command: str) -> tuple[str, ...]:
    if command not in PUBLIC_COMMANDS:
        raise AdapterIntegrityError(f"unknown public adapter command:{command}")
    return (sys.executable, "-m", ADAPTER_MODULE, command)


def build_help_command() -> tuple[str, ...]:
    return (sys.executable, "-m", ADAPTER_MODULE, "--help")


def deterministic_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(DETERMINISTIC_ENV)
    return environment


def execute_public_process(argv: Sequence[str]) -> dict[str, Any]:
    exact = tuple(map(str, argv))
    started = time.perf_counter()
    process = subprocess.Popen(
        exact,
        cwd=ROOT,
        env=deterministic_environment(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    process_id = process.pid
    stdout, stderr = process.communicate()
    return {
        "argv": list(exact),
        "process_id": process_id,
        "returncode": int(process.returncode),
        "stdout": stdout,
        "stderr": stderr,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }


def _resolved_module(module_name: str) -> dict[str, Any]:
    specification = importlib.util.find_spec(module_name)
    if specification is None or specification.origin is None:
        raise AdapterIntegrityError(f"module cannot be resolved:{module_name}")
    path = Path(specification.origin).resolve()
    return {
        "module": module_name,
        "path": str(path),
        "sha256": sha256_file(path),
    }


def capture_critical_bindings() -> dict[tuple[str, str], Any]:
    modules = {"driver": driver, "canonical": canonical, "launcher": launcher}
    return {
        (module_name, name): getattr(modules[module_name], name)
        for module_name, names in CRITICAL_GLOBAL_BINDINGS.items()
        for name in names
    }


def require_bindings_unchanged(
    before: Mapping[tuple[str, str], Any]
) -> list[str]:
    after = capture_critical_bindings()
    changed = [
        f"{module}.{name}"
        for (module, name), value in before.items()
        if after[(module, name)] is not value
    ]
    if changed:
        raise AdapterIntegrityError(f"module-global replacement detected:{changed}")
    return [f"{module}.{name}" for module, name in sorted(before)]


def _old_output_identity() -> dict[str, Any]:
    paths = DRIVER_SUFFIX_OUTPUTS + (
        canonical.RESULT_PATH,
        canonical.FAILURE_PATH,
        launcher.RESULT_PATH,
        launcher.FAILURE_PATH,
    )
    rows = []
    for relative in paths:
        path = ROOT / relative
        rows.append({
            "path": relative.as_posix(),
            "exists": path.exists(),
            "size": path.stat().st_size if path.is_file() else None,
            "sha256": sha256_file(path) if path.is_file() else None,
        })
    return {"rows": rows, "digest": digest(rows)}


def verify_frozen_inputs() -> dict[str, Any]:
    _require_commit(STARTING_HEAD)
    launcher_package = launcher.verify_package_manifests()
    driver_identity = driver.verify_outer_manifest("execution adapter binding")
    laboratory_hashes = driver.laboratory_package_hashes()

    result_path = ROOT / PASSING_LAUNCHER_RESULT_PATH
    if sha256_file(result_path) != PASSING_LAUNCHER_RESULT_SHA256:
        raise AdapterIntegrityError("passing launcher result changed")
    launcher_result = _load_json(result_path)
    _verify_self_digest(launcher_result, "result_digest", label="launcher result")
    if (
        launcher_result.get("identical_cohort_digest") != ACCEPTED_COHORT_DIGEST
        or launcher_result.get("verified_seed_count_per_order") != 32
        or launcher_result.get("verified_organism_count_per_order") != 96
        or launcher_result.get("exposure_rows_read") != 0
        or launcher_result.get("outcome_access") != {"count": 0, "event_ids": []}
    ):
        raise AdapterIntegrityError("accepted launcher result binding changed")

    prefix_path = ROOT / driver.PREFIX_MANIFEST_PATH
    raw_path = ROOT / RAW_SNAPSHOT_MANIFEST_PATH
    compressed_path = ROOT / COMPRESSED_SNAPSHOT_PATH
    receipt_path = ROOT / PREFLIGHT_RECEIPT_PATH
    checks = {
        "prefix_manifest_sha256": sha256_file(prefix_path),
        "raw_snapshot_size": raw_path.stat().st_size,
        "raw_snapshot_sha256": sha256_file(raw_path),
        "compressed_snapshot_sha256": sha256_file(compressed_path),
        "preflight_receipt_sha256": sha256_file(receipt_path),
    }
    expected = {
        "prefix_manifest_sha256": PREFIX_MANIFEST_SHA256,
        "raw_snapshot_size": RAW_SNAPSHOT_MANIFEST_SIZE,
        "raw_snapshot_sha256": RAW_SNAPSHOT_MANIFEST_SHA256,
        "compressed_snapshot_sha256": COMPRESSED_SNAPSHOT_SHA256,
        "preflight_receipt_sha256": PREFLIGHT_RECEIPT_SHA256,
    }
    if checks != expected:
        raise AdapterIntegrityError(
            f"frozen cohort transport binding changed:{checks}"
        )
    prefix = driver._load_prefix_manifest()
    if prefix.get("prefix_manifest_digest") != PREFIX_MANIFEST_DIGEST:
        raise AdapterIntegrityError("prefix manifest digest changed")
    receipt = _load_json(receipt_path)
    if (
        driver.canonical_digest({
            key: item for key, item in receipt.items() if key != "receipt_digest"
        })
        != receipt.get("receipt_digest")
        or receipt.get("receipt_digest") != PREFLIGHT_RECEIPT_DIGEST
        or receipt.get("coverage")
        != {
            "seed_count": 32,
            "arm_count": 3,
            "artifact_count": 96,
            "complete": True,
        }
        or receipt.get("outcome_access") != {"count": 0, "event_ids": []}
    ):
        raise AdapterIntegrityError("complete stored-cohort receipt changed")
    targets = {
        "planted": sum(
            row["targets"].get("planted") is not None
            for row in prefix["results"]
        ),
        "selected_comparison": sum(
            row["targets"].get("selected_spurious") is not None
            for row in prefix["results"]
        ),
    }
    if targets != {"planted": 32, "selected_comparison": 30}:
        raise AdapterIntegrityError(f"frozen target counts changed:{targets}")
    return {
        "starting_head": STARTING_HEAD,
        "passing_launcher_result": {
            "path": PASSING_LAUNCHER_RESULT_PATH.as_posix(),
            "sha256": PASSING_LAUNCHER_RESULT_SHA256,
            "result_digest": launcher_result["result_digest"],
            "cohort_digest": ACCEPTED_COHORT_DIGEST,
        },
        "launcher_package": {
            "source_manifest_sha256": launcher_package[
                "source_manifest_sha256"
            ],
            "source_manifest_digest": launcher_package[
                "source_manifest_digest"
            ],
            "artifact_binding_sha256": launcher_package[
                "artifact_binding_sha256"
            ],
            "artifact_binding_digest": launcher_package[
                "artifact_binding_digest"
            ],
        },
        "driver_identity": driver_identity,
        "laboratory_package_hashes": laboratory_hashes,
        "laboratory_package_digest": digest(laboratory_hashes),
        "transport_checks": checks,
        "prefix_manifest_digest": PREFIX_MANIFEST_DIGEST,
        "preflight_receipt_digest": PREFLIGHT_RECEIPT_DIGEST,
        "target_counts": targets,
        "module_paths": {
            name: _resolved_module(name)
            for name in (
                DRIVER_MODULE,
                CANONICAL_MODULE,
                LAUNCHER_MODULE,
                ADAPTER_MODULE,
            )
        },
        "old_output_identity": _old_output_identity(),
        "exposure_rows_read": 0,
        "outcome_reads": 0,
    }


def construct_runtime_contract_view(
    manifest: Mapping[str, Any],
    observed_contracts: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create a canonical-equal, representation-native in-memory view."""

    before = streamed_canonical_identity(manifest)
    metadata = manifest.get("metadata")
    if not isinstance(metadata, Mapping):
        raise AdapterIntegrityError("snapshot metadata is missing")
    expected_contracts = metadata.get("per_seed_identity_contracts")
    if not isinstance(expected_contracts, Mapping):
        raise AdapterIntegrityError("stored candidate contracts are missing")
    if set(expected_contracts) != set(observed_contracts):
        raise AdapterIntegrityError("runtime contract coverage changed")
    native_contracts = {}
    rows = []
    for key in sorted(expected_contracts, key=lambda value: int(value)):
        expected = expected_contracts[key]
        observed = observed_contracts[key]
        comparison = canonical.compare_complete_contracts(
            expected, observed, seed_ordinal=int(key)
        )
        native_contracts[key] = observed
        rows.append(comparison)
    runtime_metadata = dict(metadata)
    runtime_metadata["per_seed_identity_contracts"] = native_contracts
    runtime_view = dict(manifest)
    runtime_view["metadata"] = runtime_metadata
    runtime_identity = streamed_canonical_identity(runtime_view)
    source_after = streamed_canonical_identity(manifest)
    if before != runtime_identity or before != source_after:
        raise AdapterIntegrityError("ephemeral runtime view changed canonical bytes")
    return runtime_view, {
        "source_before": before,
        "runtime_view": runtime_identity,
        "source_after": source_after,
        "contract_rows": rows,
        "contract_row_set_digest": digest(rows),
    }


def semantic_identity_set_digest(
    identities: Mapping[str, Mapping[str, Any]],
) -> str:
    if set(identities) != set(driver.ARMS):
        raise AdapterIntegrityError("semantic identity arm coverage changed")
    return digest({arm: identities[arm] for arm in driver.ARMS})


def _semantic_set(
    restored: Mapping[tuple[int, str], Any]
) -> dict[str, str]:
    codec = driver.V2SnapshotCodec()
    return {
        str(ordinal): semantic_identity_set_digest({
            arm: codec.semantic_identity(restored[(ordinal, arm)])
            for arm in driver.ARMS
        })
        for ordinal in range(driver.SEED_COUNT)
    }


def _restore_complete_cohort(
    manifest: Mapping[str, Any]
) -> dict[tuple[int, str], Any]:
    return {
        (ordinal, arm): driver._restore_snapshot_entry(manifest, ordinal, arm)
        for ordinal in range(driver.SEED_COUNT)
        for arm in driver.ARMS
    }


def build_readiness_context() -> dict[str, Any]:
    fixed = verify_frozen_inputs()
    prefix = driver._load_prefix_manifest()
    manifest_path = ROOT / RAW_SNAPSHOT_MANIFEST_PATH
    manifest_file_before = {
        "size": manifest_path.stat().st_size,
        "sha256": sha256_file(manifest_path),
    }
    manifest = driver._validated_snapshot_manifest()
    unsigned = {
        key: item for key, item in manifest.items() if key != "manifest_digest"
    }
    if driver.canonical_digest(unsigned) != manifest.get("manifest_digest"):
        raise AdapterIntegrityError("snapshot manifest self-digest changed")
    manifest_digest_before = manifest["manifest_digest"]
    bindings_before = capture_critical_bindings()
    old_outputs_before = _old_output_identity()

    restored = _restore_complete_cohort(manifest)
    semantic_before = _semantic_set(restored)
    observed_contracts: dict[str, Mapping[str, Any]] = {}
    legacy_abort_reproduced = False
    for ordinal in range(driver.SEED_COUNT):
        arms = {arm: restored[(ordinal, arm)] for arm in driver.ARMS}
        observed = driver.exact_arm_identity_contract(arms)
        expected = manifest["metadata"]["per_seed_identity_contracts"][
            str(ordinal)
        ]
        canonical.compare_complete_contracts(
            expected, observed, seed_ordinal=ordinal
        )
        if ordinal == 0:
            try:
                canonical.legacy_raw_contract_check(
                    expected, observed, seed_ordinal=ordinal
                )
            except driver.FreshScientificIntegrityError as exc:
                legacy_abort_reproduced = (
                    str(exc) == "snapshot candidate contract mismatch:0"
                )
            if not legacy_abort_reproduced:
                raise AdapterIntegrityError("stopped seed-0 abort did not reproduce")
        canonical._verify_target_identity(
            prefix["results"][ordinal], arms, ordinal=ordinal
        )
        observed_contracts[str(ordinal)] = observed

    runtime_view, view_proof = construct_runtime_contract_view(
        manifest, observed_contracts
    )
    prefix_verification = driver._verify_prefix_snapshot_metadata(
        prefix, runtime_view, restored
    )
    semantic_after = _semantic_set(restored)
    if semantic_before != semantic_after:
        raise AdapterIntegrityError("runtime view changed candidate or graph state")
    unchanged_bindings = require_bindings_unchanged(bindings_before)
    manifest_file_after = {
        "size": manifest_path.stat().st_size,
        "sha256": sha256_file(manifest_path),
    }
    if manifest_file_before != manifest_file_after:
        raise AdapterIntegrityError("stored manifest file changed")
    if manifest.get("manifest_digest") != manifest_digest_before:
        raise AdapterIntegrityError("stored manifest canonical digest changed")
    old_outputs_after = _old_output_identity()
    if old_outputs_before != old_outputs_after:
        raise AdapterIntegrityError("earlier package output identity changed")

    seed_rows = []
    for row in view_proof["contract_rows"]:
        ordinal = int(row["seed_ordinal"])
        seed_rows.append({
            **row,
            "before_semantic_set_digest": semantic_before[str(ordinal)],
            "after_semantic_set_digest": semantic_after[str(ordinal)],
            "no_candidate_or_graph_mutation": True,
            "planted_target_present": (
                prefix["results"][ordinal]["targets"]["planted"] is not None
            ),
            "selected_comparison_target_present": (
                prefix["results"][ordinal]["targets"]["selected_spurious"]
                is not None
            ),
        })
    reconstruction = {
        "compressed_sha256": COMPRESSED_SNAPSHOT_SHA256,
        "raw_size": RAW_SNAPSHOT_MANIFEST_SIZE,
        "raw_sha256": RAW_SNAPSHOT_MANIFEST_SHA256,
        "manifest_digest": manifest["manifest_digest"],
    }
    core = {
        "seed_rows": seed_rows,
        "snapshot_transport_set_digest": (
            canonical._snapshot_transport_set_digest(manifest)
        ),
        "prefix_transport_set_digest": (
            canonical._prefix_transport_set_digest(prefix)
        ),
        "raw_manifest_reconstruction": reconstruction,
        "outcome_access": {"count": 0, "event_ids": []},
        "exposure_rows_read": 0,
        "stopped_output_paths_present": canonical._forbidden_stopped_outputs(),
    }
    cohort_digest = canonical.digest(core)
    if cohort_digest != ACCEPTED_COHORT_DIGEST:
        raise AdapterIntegrityError(
            f"accepted cohort digest changed:{cohort_digest}"
        )
    summary = {
        "fixed_inputs": fixed,
        "verified_seed_count": len(seed_rows),
        "verified_organism_count": len(restored),
        "cohort_digest": cohort_digest,
        "core": core,
        "runtime_view_proof": view_proof,
        "frozen_raw_verifier": prefix_verification,
        "legacy_seed_zero_abort_reproduced": legacy_abort_reproduced,
        "manifest_file_before": manifest_file_before,
        "manifest_file_after": manifest_file_after,
        "manifest_digest_before": manifest_digest_before,
        "manifest_digest_after": manifest["manifest_digest"],
        "semantic_state_before_digest": digest(semantic_before),
        "semantic_state_after_digest": digest(semantic_after),
        "candidate_or_graph_mutation_count": 0,
        "unchanged_module_global_bindings": unchanged_bindings,
        "module_global_replacement_count": 0,
        "old_output_identity_before": old_outputs_before,
        "old_output_identity_after": old_outputs_after,
        "exposure_rows_read": 0,
        "outcome_access": {"count": 0, "event_ids": []},
    }
    return {
        "summary": summary,
        "prefix": prefix,
        "manifest": manifest,
        "runtime_manifest": runtime_view,
        "restored": restored,
    }


def _record_failure(path: Path, command: str, exc: Exception) -> None:
    if path.exists():
        return
    value = {
        "schema_version": "native_v2_execution_adapter_failure.v1",
        "package_id": PACKAGE_ID,
        "command": command,
        "exception_type": type(exc).__name__,
        "detail": str(exc),
        "parent_argv": list(getattr(sys, "orig_argv", sys.argv)),
        "process_id": os.getpid(),
        "exposure_rows_read": 0 if command == "verify-readiness" else None,
        "outcome_access": {"count": 0, "event_ids": []},
    }
    if isinstance(exc, canonical.CanonicalContractMismatch):
        value["canonical_difference"] = copy.deepcopy(exc.manifest)
    value["failure_digest"] = digest(value)
    _atomic_json(ROOT / path, value)


def _readiness_artifact_value(
    context: Mapping[str, Any], package: Mapping[str, Any], started: float
) -> dict[str, Any]:
    summary = context["summary"]
    value = {
        "schema_version": "native_v2_execution_adapter_readiness.v1",
        "package_id": PACKAGE_ID,
        "source_manifest": {
            "sha256": package["source_manifest_sha256"],
            "digest": package["source_manifest_digest"],
        },
        "artifact_binding": {
            "sha256": package["artifact_binding_sha256"],
            "digest": package["artifact_binding_digest"],
        },
        "public_command": list(build_public_command("verify-readiness")),
        "actual_parent_argv": list(getattr(sys, "orig_argv", sys.argv)),
        "process_id": os.getpid(),
        "python_executable": sys.executable,
        "working_directory": str(ROOT),
        "deterministic_environment": copy.deepcopy(DETERMINISTIC_ENV),
        **copy.deepcopy(summary),
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "evaluation_suffix_unopened": True,
    }
    value["readiness_digest"] = digest(value)
    return value


def run_readiness() -> dict[str, Any]:
    _require_clean_worktree()
    if (ROOT / READINESS_PATH).exists() or (ROOT / READINESS_FAILURE_PATH).exists():
        raise FileExistsError("readiness output already exists")
    require_committed_artifact(SOURCE_MANIFEST_PATH)
    require_committed_artifact(ARTIFACT_BINDING_PATH)
    started = time.perf_counter()
    try:
        package = verify_package_manifests()
        context = build_readiness_context()
        value = _readiness_artifact_value(context, package, started)
        _atomic_json(ROOT / READINESS_PATH, value)
        return value
    except Exception as exc:
        _record_failure(READINESS_FAILURE_PATH, "verify-readiness", exc)
        raise


def require_zero_outcomes(value: Mapping[str, Any], *, label: str) -> None:
    if value.get("outcome_access") != {"count": 0, "event_ids": []}:
        raise AdapterIntegrityError(f"{label} opened an outcome")


def _load_and_verify_readiness(*, committed: bool) -> dict[str, Any]:
    if committed:
        require_committed_artifact(READINESS_PATH)
    value = _load_json(ROOT / READINESS_PATH)
    _verify_self_digest(value, "readiness_digest", label="readiness artifact")
    if (
        value.get("cohort_digest") != ACCEPTED_COHORT_DIGEST
        or value.get("verified_seed_count") != 32
        or value.get("verified_organism_count") != 96
        or value.get("candidate_or_graph_mutation_count") != 0
        or value.get("exposure_rows_read") != 0
    ):
        raise AdapterIntegrityError("readiness gate changed")
    require_zero_outcomes(value, label="readiness")
    return value


def build_execution_manifest(
    *,
    identity: Mapping[str, Any],
    prefix: Mapping[str, Any],
    ecology: Mapping[str, Any],
    manifest: Mapping[str, Any],
    exposure: Mapping[str, Any],
    readiness: Mapping[str, Any],
    exposure_path: Path = EXPOSURE_PATH,
) -> dict[str, Any]:
    require_zero_outcomes(exposure, label="exposure")
    value = {
        "schema_version": "native_v2_execution_adapter_manifest.v1",
        "package_id": PACKAGE_ID,
        "experiment_id": driver.EXPERIMENT_ID,
        "source_tree_identity": {
            "source_freeze_commit": identity["source_freeze_commit"],
            "source_runtime_digest": identity["source_runtime_digest"],
        },
        "experiment_package_identity": {
            "outer_manifest_sha256": identity["outer_sha256"],
            "laboratory_package_digest": digest(
                driver.laboratory_package_hashes()
            ),
        },
        "adapter_package": {
            "source_manifest_sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
            "artifact_binding_sha256": sha256_file(ROOT / ARTIFACT_BINDING_PATH),
            "readiness_sha256": sha256_file(ROOT / READINESS_PATH),
            "readiness_digest": readiness["readiness_digest"],
        },
        "seed_manifest": {
            "sha256": sha256_file(ROOT / driver.SEED_MANIFEST_PATH),
            "digest": driver._load_json(
                ROOT / driver.SEED_MANIFEST_PATH
            )["seed_manifest_digest"],
        },
        "ecology_manifest": {
            "sha256": sha256_file(ROOT / driver.ECOLOGY_MANIFEST_PATH),
            "digest": ecology["ecology_digest"],
        },
        "prefix_manifest": {
            "sha256": sha256_file(ROOT / driver.PREFIX_MANIFEST_PATH),
            "digest": prefix["prefix_manifest_digest"],
            "candidate_manifest_digest": driver._candidate_manifest_digest(prefix),
        },
        "snapshot_manifest": {
            "sha256": sha256_file(ROOT / RAW_SNAPSHOT_MANIFEST_PATH),
            "digest": manifest["manifest_digest"],
            "entry_set_digest": digest(manifest["entries"]),
            "artifact_count": len(manifest["entries"]),
        },
        "exposure_artifact": {
            "path": exposure_path.as_posix(),
            "sha256": sha256_file(ROOT / exposure_path),
            "digest": exposure["exposure_digest"],
        },
        "parity_digest": exposure["parity_digest"],
        "qualification_digest": exposure["qualification_digest"],
        "qualifying_seed_count": exposure["qualifying_seed_count"],
        "required_qualifying_seed_count": exposure[
            "required_qualifying_seed_count"
        ],
        "admitted": exposure["admitted"],
        "zero_outcome_read_result": copy.deepcopy(exposure["outcome_access"]),
        "complete_snapshot_identity": copy.deepcopy(
            exposure["complete_snapshot_identity"]
        ),
        "global_preflight_receipt_digest": exposure[
            "global_preflight_receipt"
        ]["receipt_digest"],
    }
    value["execution_manifest_digest"] = digest(value)
    return value


def validate_admission_values(
    *,
    exposure: Mapping[str, Any],
    execution: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> None:
    _verify_self_digest(exposure, "exposure_digest", label="exposure")
    _verify_self_digest(
        execution, "execution_manifest_digest", label="execution manifest"
    )
    require_zero_outcomes(exposure, label="exposure")
    if exposure.get("admitted") is not True or execution.get("admitted") is not True:
        raise AdapterIntegrityError("frozen exposure is not admitted")
    checks = {
        "exposure_digest": execution.get("exposure_artifact", {}).get("digest"),
        "exposure_sha256": execution.get("exposure_artifact", {}).get("sha256"),
        "prefix_sha256": execution.get("prefix_manifest", {}).get("sha256"),
        "prefix_digest": execution.get("prefix_manifest", {}).get("digest"),
        "snapshot_sha256": execution.get("snapshot_manifest", {}).get("sha256"),
        "snapshot_digest": execution.get("snapshot_manifest", {}).get("digest"),
        "readiness_sha256": execution.get("adapter_package", {}).get(
            "readiness_sha256"
        ),
        "readiness_digest": execution.get("adapter_package", {}).get(
            "readiness_digest"
        ),
    }
    if checks != dict(expected):
        raise AdapterIntegrityError(
            f"exposure/prefix/snapshot/execution identity mismatch:{checks}"
        )
    if checks["exposure_digest"] != exposure.get("exposure_digest"):
        raise AdapterIntegrityError("execution names a foreign exposure")


def run_exposure() -> dict[str, Any]:
    _require_clean_worktree()
    if any((ROOT / path).exists() for path in (
        EXPOSURE_PATH, EXECUTION_MANIFEST_PATH, EXPOSURE_FAILURE_PATH
    )):
        raise FileExistsError("adapter exposure output already exists")
    try:
        verify_package_manifests()
        readiness = _load_and_verify_readiness(committed=True)
        context = build_readiness_context()
        identity = driver.verify_outer_manifest("adapter preoutcome exposure")
        ecology = driver._load_json(ROOT / driver.ECOLOGY_MANIFEST_PATH)
        receipt = _load_json(ROOT / PREFLIGHT_RECEIPT_PATH)
        guard = driver.OutcomeAccessGuard()
        exposure = driver._reconstruct_exposure_value(
            identity=identity,
            prefix=context["prefix"],
            ecology=ecology,
            manifest=context["runtime_manifest"],
            receipt=receipt,
            restored=context["restored"],
            guard=guard,
        )
        require_zero_outcomes(exposure, label="adapter exposure")
        _atomic_json(ROOT / EXPOSURE_PATH, exposure)
        execution = build_execution_manifest(
            identity=identity,
            prefix=context["prefix"],
            ecology=ecology,
            manifest=context["runtime_manifest"],
            exposure=exposure,
            readiness=readiness,
        )
        _atomic_json(ROOT / EXECUTION_MANIFEST_PATH, execution)
        return exposure
    except Exception as exc:
        _record_failure(EXPOSURE_FAILURE_PATH, "run-exposure", exc)
        raise


def _expected_admission_identity(
    exposure: Mapping[str, Any],
    readiness: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "exposure_digest": exposure["exposure_digest"],
        "exposure_sha256": sha256_file(ROOT / EXPOSURE_PATH),
        "prefix_sha256": PREFIX_MANIFEST_SHA256,
        "prefix_digest": PREFIX_MANIFEST_DIGEST,
        "snapshot_sha256": RAW_SNAPSHOT_MANIFEST_SHA256,
        "snapshot_digest": canonical.RAW_SNAPSHOT_MANIFEST_DIGEST,
        "readiness_sha256": sha256_file(ROOT / READINESS_PATH),
        "readiness_digest": readiness["readiness_digest"],
    }


def reconstruct_adapter_admission() -> dict[str, Any]:
    verify_package_manifests()
    readiness = _load_and_verify_readiness(committed=True)
    require_committed_artifact(EXPOSURE_PATH)
    require_committed_artifact(EXECUTION_MANIFEST_PATH)
    exposure = _load_json(ROOT / EXPOSURE_PATH)
    execution = _load_json(ROOT / EXECUTION_MANIFEST_PATH)
    validate_admission_values(
        exposure=exposure,
        execution=execution,
        expected=_expected_admission_identity(exposure, readiness),
    )
    context = build_readiness_context()
    identity = driver.verify_outer_manifest("adapter immediate pre-outcome")
    ecology = driver._load_json(ROOT / driver.ECOLOGY_MANIFEST_PATH)
    receipt = _load_json(ROOT / PREFLIGHT_RECEIPT_PATH)
    guard = driver.OutcomeAccessGuard()
    reconstructed = driver._reconstruct_exposure_value(
        identity=identity,
        prefix=context["prefix"],
        ecology=ecology,
        manifest=context["runtime_manifest"],
        receipt=receipt,
        restored=context["restored"],
        guard=guard,
    )
    if canonical_bytes(reconstructed) != canonical_bytes(exposure):
        raise AdapterIntegrityError("current cohort differs from frozen exposure")
    rebuilt = build_execution_manifest(
        identity=identity,
        prefix=context["prefix"],
        ecology=ecology,
        manifest=context["runtime_manifest"],
        exposure=exposure,
        readiness=readiness,
    )
    if canonical_bytes(rebuilt) != canonical_bytes(execution):
        raise AdapterIntegrityError("current cohort differs from execution freeze")
    require_zero_outcomes(reconstructed, label="immediate reconstruction")
    if reconstructed.get("admitted") is not True:
        raise AdapterIntegrityError("reconstructed cohort was not admitted")
    return {
        "readiness": readiness,
        "identity": identity,
        "ecology": ecology,
        "receipt": receipt,
        "authorization": reconstructed["preflight_authorization"],
        "exposure": reconstructed,
        "execution_manifest": execution,
        **context,
    }


def restart_plan(
    journal: driver.DurableHashJournal, seed_ordinals: Sequence[int]
) -> dict[str, Any]:
    seeds = tuple(map(int, seed_ordinals))
    next_seed = journal.next_seed(seeds)
    completed_count = len(seeds) if next_seed is None else seeds.index(next_seed)
    value = {
        "seed_ordinals": list(seeds),
        "completed_ordinals": list(seeds[:completed_count]),
        "next_unfinished_seed": next_seed,
        "remaining_ordinals": list(seeds[completed_count:]),
    }
    value["restart_plan_digest"] = digest(value)
    return value


def execute_remaining_or_reconstruct(
    *,
    journal: driver.DurableHashJournal,
    seed_ordinals: Sequence[int],
    execute_seed: Callable[[int], None],
    reconstruct_summary: Callable[[Sequence[int]], Any],
) -> dict[str, Any]:
    plan = restart_plan(journal, seed_ordinals)
    executed = []
    for seed in plan["remaining_ordinals"]:
        execute_seed(int(seed))
        executed.append(int(seed))
    final_plan = restart_plan(journal, seed_ordinals)
    if final_plan["next_unfinished_seed"] is not None:
        raise AdapterIntegrityError("execution ended before all seeds committed")
    summary = reconstruct_summary(tuple(map(int, seed_ordinals)))
    return {
        "entry_plan": plan,
        "final_plan": final_plan,
        "executed_ordinals": executed,
        "summary": summary,
    }


def _science_worktree_is_clean_enough() -> None:
    rows = _git("status", "--porcelain=v1").splitlines()
    allowed_prefixes = (
        SCIENCE_JOURNAL_DIR.as_posix(),
        SCIENCE_CARRIER_DIR.as_posix(),
    )
    unexpected = []
    for row in rows:
        path = row[3:].strip()
        if not any(path.startswith(prefix) for prefix in allowed_prefixes):
            unexpected.append(row)
    if unexpected:
        raise AdapterIntegrityError(
            f"unexpected worktree changes before science:{unexpected}"
        )


def run_science() -> dict[str, Any]:
    _science_worktree_is_clean_enough()
    if (ROOT / RESULT_PATH).exists():
        raise FileExistsError("adapter canonical result already exists")
    try:
        baseline = reconstruct_adapter_admission()
        context = baseline
        prefix = context["prefix"]
        runtime_manifest = context["runtime_manifest"]
        restored = context["restored"]
        ecology = context["ecology"]
        environment_value = driver._load_json(ROOT / driver.ENVIRONMENT_MANIFEST_PATH)
        environment = driver.FrozenTruthfulEnvironment(environment_value)
        rows = driver._suffix_outcome_blind_rows(ecology)
        seed_metadata = {
            int(item["ordinal"]): {
                "genome_seed": int(item["genome_seed"]),
                "targets": copy.deepcopy(item["targets"]),
            }
            for item in prefix["results"]
        }
        journal = driver.DurableHashJournal(ROOT / SCIENCE_JOURNAL_DIR)
        entry_plan = restart_plan(journal, tuple(range(driver.SEED_COUNT)))
        completed = driver.committed_seed_results(
            journal,
            expected_ordinals=tuple(entry_plan["completed_ordinals"]),
            expected_rows=rows,
            baseline_wrappers=restored,
            expected_seed_metadata=seed_metadata,
            environment_manifest=environment_value,
        )
        if len(completed) != len(entry_plan["completed_ordinals"]):
            raise AdapterIntegrityError("completed seed verification mismatch")
        for ordinal in entry_plan["remaining_ordinals"]:
            live: MutableMapping[str, Any] = {
                arm: restored[(ordinal, arm)] for arm in driver.ARMS
            }
            adapter = driver.FreshScienceAdapter(
                seed_ordinal=ordinal,
                genome_seed=seed_metadata[ordinal]["genome_seed"],
                targets=seed_metadata[ordinal]["targets"],
                identity_contract=runtime_manifest["metadata"][
                    "per_seed_identity_contracts"
                ][str(ordinal)],
            )
            driver.execute_fresh_seed_atomically(
                seed_ordinal=ordinal,
                live_arms=live,
                rows=rows,
                adapter=adapter,
                journal_root=ROOT / SCIENCE_JOURNAL_DIR,
                carrier_root=ROOT / SCIENCE_CARRIER_DIR,
                environment=environment,
                preflight_receipt=context["receipt"],
                snapshot_manifest=runtime_manifest,
                authorization=context["authorization"],
            )
        final_journal = driver.DurableHashJournal(ROOT / SCIENCE_JOURNAL_DIR)
        final_plan = restart_plan(final_journal, tuple(range(driver.SEED_COUNT)))
        if final_plan["next_unfinished_seed"] is not None:
            raise AdapterIntegrityError("canonical science ended before seed 31")
        seed_results = driver.committed_seed_results(
            final_journal,
            expected_ordinals=tuple(range(driver.SEED_COUNT)),
            expected_rows=rows,
            baseline_wrappers=restored,
            expected_seed_metadata=seed_metadata,
            environment_manifest=environment_value,
        )
        adjudication = driver.adjudicate_committed_results(seed_results)
        value = {
            "schema_version": "native_v2_execution_adapter_result.v1",
            "package_id": PACKAGE_ID,
            "experiment_id": driver.EXPERIMENT_ID,
            "exposure_digest": context["exposure"]["exposure_digest"],
            "execution_manifest_digest": context["execution_manifest"][
                "execution_manifest_digest"
            ],
            "all_32_committed": True,
            "restart_plan_at_entry": entry_plan,
            "restart_plan_at_completion": final_plan,
            "seed_result_digests": [
                item["seed_result_digest"] for item in seed_results
            ],
            "recomputed_result_digests": [
                item["recomputed_result_digest"] for item in seed_results
            ],
            "adjudication": adjudication,
            "journal_chain_digest": digest(final_journal._records()),
        }
        value["canonical_result_digest"] = digest(value)
        driver._atomic_bytes(
            ROOT / RESULT_PATH,
            driver.deterministic_gzip(canonical_bytes(value)),
        )
        return value
    except Exception as exc:
        _record_failure(SCIENCE_FAILURE_PATH, "run-science", exc)
        raise


def freeze_package_manifests(source_commit: str) -> dict[str, Any]:
    _require_clean_worktree()
    if _git("rev-parse", "HEAD") != source_commit:
        raise AdapterIntegrityError("source freeze commit is not HEAD")
    if (ROOT / SOURCE_MANIFEST_PATH).exists() or (
        ROOT / ARTIFACT_BINDING_PATH
    ).exists():
        raise FileExistsError("adapter manifests already exist")
    fixed = verify_frozen_inputs()
    source_hashes = {
        relative: sha256_file(ROOT / relative) for relative in SOURCE_FILES
    }
    source = {
        "schema_version": "native_v2_execution_adapter_source_manifest.v1",
        "package_id": PACKAGE_ID,
        "source_freeze_commit": source_commit,
        "source_hashes": source_hashes,
        "module_paths": {
            "adapter": ADAPTER_MODULE,
            "driver": DRIVER_MODULE,
            "canonical": CANONICAL_MODULE,
            "launcher": LAUNCHER_MODULE,
        },
        "public_commands": {
            command: list(build_public_command(command))
            for command in PUBLIC_COMMANDS
        },
        "deterministic_environment": copy.deepcopy(DETERMINISTIC_ENV),
        "runtime": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "working_directory": str(ROOT),
        },
        "preservation": {
            "outer_adapter_only": True,
            "no_module_global_replacement": True,
            "old_packages_byte_identical": True,
            "real_exposure_not_run": True,
            "real_outcomes_not_read": True,
        },
    }
    source["source_manifest_digest"] = digest(source)
    _atomic_json(ROOT / SOURCE_MANIFEST_PATH, source)
    binding = {
        "schema_version": "native_v2_execution_adapter_artifact_binding.v1",
        "package_id": PACKAGE_ID,
        "source_manifest": {
            "path": SOURCE_MANIFEST_PATH.as_posix(),
            "sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
            "digest": source["source_manifest_digest"],
        },
        "frozen_inputs": fixed,
        "output_paths": {
            "readiness": READINESS_PATH.as_posix(),
            "exposure": EXPOSURE_PATH.as_posix(),
            "execution_manifest": EXECUTION_MANIFEST_PATH.as_posix(),
            "science_journal": SCIENCE_JOURNAL_DIR.as_posix(),
            "science_carrier": SCIENCE_CARRIER_DIR.as_posix(),
            "result": RESULT_PATH.as_posix(),
        },
        "scientific_constants": {
            "seed_count": driver.SEED_COUNT,
            "arms": list(driver.ARMS),
            "suffix_rows": 16,
            "minimum_target_opportunities": driver.MIN_TARGET_OPPORTUNITIES,
            "minimum_qualifying_seeds": driver.MIN_QUALIFYING_SEEDS,
            "minimum_favorable_seeds": driver.MIN_FAVORABLE_SEEDS,
            "holm_test_count": 2,
            "all_32_paired": True,
        },
        "stop_boundary": {
            "readiness_only_in_this_package": True,
            "exposure_command_frozen_not_run": True,
            "science_command_frozen_not_run": True,
        },
    }
    binding["artifact_binding_digest"] = digest(binding)
    _atomic_json(ROOT / ARTIFACT_BINDING_PATH, binding)
    return {
        "source_manifest_path": SOURCE_MANIFEST_PATH.as_posix(),
        "source_manifest_sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
        "source_manifest_digest": source["source_manifest_digest"],
        "artifact_binding_path": ARTIFACT_BINDING_PATH.as_posix(),
        "artifact_binding_sha256": sha256_file(ROOT / ARTIFACT_BINDING_PATH),
        "artifact_binding_digest": binding["artifact_binding_digest"],
    }


def verify_package_manifests() -> dict[str, Any]:
    source = _load_json(ROOT / SOURCE_MANIFEST_PATH)
    source_digest = _verify_self_digest(
        source, "source_manifest_digest", label="adapter source manifest"
    )
    for relative, expected in source["source_hashes"].items():
        observed = sha256_file(ROOT / relative)
        if observed != expected:
            raise AdapterIntegrityError(
                f"adapter source changed:{relative}:{observed}"
            )
    _require_commit(str(source["source_freeze_commit"]))
    binding = _load_json(ROOT / ARTIFACT_BINDING_PATH)
    binding_digest = _verify_self_digest(
        binding, "artifact_binding_digest", label="adapter artifact binding"
    )
    if (
        binding["source_manifest"]["sha256"]
        != sha256_file(ROOT / SOURCE_MANIFEST_PATH)
        or binding["source_manifest"]["digest"] != source_digest
    ):
        raise AdapterIntegrityError("adapter source/artifact binding mismatch")
    fixed = verify_frozen_inputs()
    if canonical_bytes(fixed) != canonical_bytes(binding["frozen_inputs"]):
        raise AdapterIntegrityError("adapter frozen-input binding mismatch")
    return {
        "source_manifest_sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
        "source_manifest_digest": source_digest,
        "artifact_binding_sha256": sha256_file(ROOT / ARTIFACT_BINDING_PATH),
        "artifact_binding_digest": binding_digest,
    }


def _print(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    freeze = commands.add_parser("freeze-manifests")
    freeze.add_argument("--source-commit", required=True)
    commands.add_parser("verify-readiness")
    commands.add_parser("run-exposure")
    commands.add_parser("run-science")
    args = parser.parse_args(argv)
    if args.command == "freeze-manifests":
        value = freeze_package_manifests(args.source_commit)
    elif args.command == "verify-readiness":
        value = run_readiness()
    elif args.command == "run-exposure":
        value = run_exposure()
    elif args.command == "run-science":
        value = run_science()
    else:  # pragma: no cover
        raise AssertionError(args.command)
    _print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
