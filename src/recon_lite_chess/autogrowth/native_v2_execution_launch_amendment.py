"""Data-free execution-launch amendment over the frozen V2 closure."""
from __future__ import annotations

import argparse
import copy
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import gzip
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
from typing import Any, Callable, Iterator, Mapping, Sequence
import uuid

from . import native_v2_process_readiness_repair as prior


ROOT = prior.ROOT
PACKAGE_ID = "native_v2_execution_launch_amendment.v1"
MODULE_PATH = (
    "recon_lite_chess.autogrowth."
    "native_v2_execution_launch_amendment"
)
STARTING_HEAD = "e6c4a292a4fd4a448ce7a1bb12aae713e656f8dd"
ACCEPTED_COHORT_DIGEST = prior.ACCEPTED_COHORT_DIGEST
EXPANDED_PACKAGE_MAP_DIGEST = prior.EXPANDED_PACKAGE_MAP_DIGEST
CANARY_DURATION_SECONDS = 1085

PACKAGE_DIR = Path(
    "reports/autogrowth/native_authority/"
    "v2_execution_launch_amendment"
)
SOURCE_MANIFEST_PATH = PACKAGE_DIR / "source_manifest.json"
ARTIFACT_BINDING_PATH = PACKAGE_DIR / "artifact_binding_manifest.json"
LAUNCH_READINESS_PATH = PACKAGE_DIR / "launch_readiness.json"
LAUNCH_READINESS_FAILURE_PATH = PACKAGE_DIR / "launch_readiness_failure.json"
SERVICE_CANARY_RECORD_PATH = PACKAGE_DIR / "service_canary_record.json"
READINESS_PATH = PACKAGE_DIR / "readiness.json"
READINESS_FAILURE_PATH = PACKAGE_DIR / "readiness_failure.json"
PRODUCTION_RECORD_DIR = PACKAGE_DIR / "production_attempts"
OUTCOME_RESULT_BINDING_PATH = PACKAGE_DIR / "outcome_result_binding.json"

SOURCE_FILES = (
    "src/recon_lite_chess/autogrowth/"
    "native_v2_execution_launch_amendment.py",
    "tests/autogrowth/"
    "test_native_v2_execution_launch_amendment.py",
    "docs/autogrowth/"
    "NATIVE_V2_EXECUTION_LAUNCH_AMENDMENT_PREREGISTRATION_20260728.md",
)
PRE_REVIEW_FILES = (
    "src/recon_lite_chess/autogrowth/"
    "native_v2_process_readiness_repair.py",
    "tests/autogrowth/test_native_v2_process_readiness_repair.py",
    prior.SOURCE_MANIFEST_PATH.as_posix(),
    prior.ARTIFACT_BINDING_PATH.as_posix(),
    prior.LAUNCH_READINESS_PATH.as_posix(),
    prior.SERVICE_CANARY_RECORD_PATH.as_posix(),
    prior.READINESS_PATH.as_posix(),
    "docs/autogrowth/"
    "NATIVE_V2_PROCESS_READINESS_REPAIR_RESULT_20260728.md",
)

PUBLIC_CHILD_COMMANDS = (
    "run-exposure",
    "run-science",
    "service-canary",
)
PRODUCTION_COMMANDS = ("run-exposure", "run-science")
SERVICE_PREFIX = "recon-v2-execution-launch-amendment"
ATOMIC_SUFFIX = ".native-v2-execution-launch-amendment.atomic.tmp"

CONTEXT_ATTEMPT = "RECON_V2_LAUNCH_ATTEMPT_ID"
CONTEXT_COMMAND = "RECON_V2_LAUNCH_COMMAND"
CONTEXT_DIGEST = "RECON_V2_LAUNCH_DIGEST"
CONTEXT_RECORD = "RECON_V2_LAUNCH_RECORD"
CONTEXT_READINESS_SHA = "RECON_V2_FINAL_READINESS_SHA256"
CONTEXT_READINESS_DIGEST = "RECON_V2_FINAL_READINESS_DIGEST"
CONTEXT_KEYS = (
    CONTEXT_ATTEMPT,
    CONTEXT_COMMAND,
    CONTEXT_DIGEST,
    CONTEXT_RECORD,
    CONTEXT_READINESS_SHA,
    CONTEXT_READINESS_DIGEST,
)

_ATTEMPT_ID = re.compile(r"^\d{8}T\d{12}Z-[0-9a-f]{32}$")
_PRODUCTION_RECORD = re.compile(
    r"^production_attempts/(run-exposure|run-science)/"
    r"(\d{8}T\d{12}Z-[0-9a-f]{32})\.json$"
)


class ExecutionLaunchAmendmentError(RuntimeError):
    """One immutable execution-launch boundary changed."""


def canonical_bytes(value: Any) -> bytes:
    return prior.canonical_bytes(value)


def pretty_json_bytes(value: Mapping[str, Any]) -> bytes:
    return prior.pretty_json_bytes(value)


def digest(value: Any) -> str:
    return prior.digest(value)


def sha256_bytes(value: bytes) -> str:
    return prior.sha256_bytes(value)


def sha256_file(path: Path) -> str:
    return prior.sha256_file(path)


def load_json(path: Path) -> dict[str, Any]:
    return prior.load_json(path)


def verify_self_digest(
    value: Mapping[str, Any], key: str, *, label: str
) -> str:
    return prior.verify_self_digest(value, key, label=label)


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def atomic_temporary_path(path: Path) -> Path:
    return path.with_name(f".{path.name}{ATOMIC_SUFFIX}")


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_bytes(path: Path, payload: bytes) -> dict[str, bool]:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = atomic_temporary_path(path)
    if path.exists():
        if temporary.exists():
            raise ExecutionLaunchAmendmentError(
                f"atomic target and temporary both exist:"
                f"target={path}:temporary={temporary}"
            )
        if path.read_bytes() != payload:
            raise ExecutionLaunchAmendmentError(
                f"divergent existing target:{path}"
            )
        return {"created": False, "recovered": False}
    if temporary.exists():
        if temporary.read_bytes() != payload:
            raise ExecutionLaunchAmendmentError(
                f"divergent interrupted temporary:{temporary}"
            )
        os.replace(temporary, path)
        _fsync_directory(path.parent)
        return {"created": False, "recovered": True}
    with temporary.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    _fsync_directory(path.parent)
    return {"created": True, "recovered": False}


def atomic_json(path: Path, value: Mapping[str, Any]) -> dict[str, bool]:
    return atomic_bytes(path, pretty_json_bytes(value))


def require_committed(relative: Path | str) -> dict[str, Any]:
    path = Path(relative)
    return prior.require_committed_artifact(path)


def pre_review_bindings() -> tuple[dict[str, Any], ...]:
    return tuple(require_committed(path) for path in PRE_REVIEW_FILES)


def verify_pre_review_closure() -> dict[str, Any]:
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", STARTING_HEAD, "HEAD"],
        cwd=ROOT,
        check=False,
    ).returncode != 0:
        raise ExecutionLaunchAmendmentError(
            "pre-review starting commit is not an ancestor"
        )
    package = prior.verify_package_manifests()
    readiness_binding = require_committed(prior.READINESS_PATH)
    readiness = load_json(ROOT / prior.READINESS_PATH)
    verify_self_digest(
        readiness, "readiness_digest", label="pre-review readiness"
    )
    if (
        readiness.get("schema_version")
        != "native_v2_process_readiness_final.v1"
        or readiness.get("package_id") != prior.PACKAGE_ID
        or readiness.get("source_manifest", {}).get("sha256")
        != package["source_manifest_sha256"]
        or readiness.get("source_manifest", {}).get("digest")
        != package["source_manifest_digest"]
        or readiness.get("artifact_binding", {}).get("sha256")
        != package["artifact_binding_sha256"]
        or readiness.get("artifact_binding", {}).get("digest")
        != package["artifact_binding_digest"]
        or readiness.get("cohort_digest") != ACCEPTED_COHORT_DIGEST
        or readiness.get("expanded_package_map_digest")
        != EXPANDED_PACKAGE_MAP_DIGEST
        or readiness.get("verified_seed_count") != 32
        or readiness.get("verified_organism_count") != 96
        or readiness.get("real_exposure_run") is not False
        or readiness.get("real_outcome_run") is not False
        or readiness.get("outcome_access")
        != {"count": 0, "event_ids": []}
        or readiness.get("stop_before_exposure") is not True
    ):
        raise ExecutionLaunchAmendmentError(
            "pre-review final readiness identity changed"
        )
    bindings = pre_review_bindings()
    value = {
        "starting_head": STARTING_HEAD,
        "package": package,
        "readiness": {
            **readiness_binding,
            "digest": readiness["readiness_digest"],
        },
        "file_bindings": list(bindings),
        "file_binding_digest": digest(bindings),
        "cohort_digest": ACCEPTED_COHORT_DIGEST,
        "expanded_package_map_digest": EXPANDED_PACKAGE_MAP_DIGEST,
        "outcome_access": {"count": 0, "event_ids": []},
    }
    value["pre_review_digest"] = digest(value)
    return value


def deterministic_environment(
    extra: Mapping[str, str] | None = None,
) -> dict[str, str]:
    value = prior.deterministic_environment()
    if extra:
        value.update({
            str(key): str(item) for key, item in extra.items()
        })
    return dict(sorted(value.items()))


def build_public_command(command: str) -> tuple[str, ...]:
    if command not in PUBLIC_CHILD_COMMANDS:
        raise ExecutionLaunchAmendmentError(
            f"invalid service child command:{command}"
        )
    return (sys.executable, "-m", MODULE_PATH, command)


def service_attempt_root() -> Path:
    state = os.environ.get("XDG_STATE_HOME")
    base = Path(state) if state else Path.home() / ".local" / "state"
    return (
        base
        / "hector-recon-v2-execution-launch-amendment"
        / "attempts"
    )


def service_lock_root() -> Path:
    return service_attempt_root().parent / "locks"


def production_record_path(command: str, attempt_id: str) -> Path:
    if command not in PRODUCTION_COMMANDS or not _ATTEMPT_ID.fullmatch(
        attempt_id
    ):
        raise ExecutionLaunchAmendmentError(
            "invalid production record identity"
        )
    return (
        PRODUCTION_RECORD_DIR / command / f"{attempt_id}.json"
    )


def is_recognized_amendment_temporary(path: Path) -> bool:
    try:
        relative = path.resolve().relative_to((ROOT / PACKAGE_DIR).resolve())
    except ValueError:
        return False
    name = relative.name
    if not name.startswith(".") or not name.endswith(ATOMIC_SUFFIX):
        return False
    target_name = name[1:-len(ATOMIC_SUFFIX)]
    target_relative = relative.with_name(target_name)
    fixed = {
        SOURCE_MANIFEST_PATH.relative_to(PACKAGE_DIR),
        ARTIFACT_BINDING_PATH.relative_to(PACKAGE_DIR),
        LAUNCH_READINESS_PATH.relative_to(PACKAGE_DIR),
        LAUNCH_READINESS_FAILURE_PATH.relative_to(PACKAGE_DIR),
        SERVICE_CANARY_RECORD_PATH.relative_to(PACKAGE_DIR),
        READINESS_PATH.relative_to(PACKAGE_DIR),
        READINESS_FAILURE_PATH.relative_to(PACKAGE_DIR),
        OUTCOME_RESULT_BINDING_PATH.relative_to(PACKAGE_DIR),
    }
    return (
        target_relative in fixed
        or bool(_PRODUCTION_RECORD.fullmatch(target_relative.as_posix()))
    )


def intended_target_for_temporary(
    temporary: Path, suffix: str
) -> Path:
    name = temporary.name
    if not name.startswith(".") or not name.endswith(suffix):
        raise ExecutionLaunchAmendmentError(
            f"not an exact package temporary:{temporary}"
        )
    return temporary.with_name(name[1:-len(suffix)])


@dataclass(frozen=True)
class TemporaryNamespace:
    root: Path
    package_dir: Path
    suffix: str
    recognizer: Callable[[Path], bool]


def production_temporary_namespaces() -> tuple[TemporaryNamespace, ...]:
    return (
        TemporaryNamespace(
            root=ROOT,
            package_dir=prior.PACKAGE_DIR,
            suffix=prior.ATOMIC_SUFFIX,
            recognizer=prior.is_recognized_package_temporary,
        ),
        TemporaryNamespace(
            root=ROOT,
            package_dir=PACKAGE_DIR,
            suffix=ATOMIC_SUFFIX,
            recognizer=is_recognized_amendment_temporary,
        ),
    )


def enforce_entry_temporary_invariants(
    namespaces: Sequence[TemporaryNamespace] | None = None,
) -> dict[str, Any]:
    scanned = namespaces or production_temporary_namespaces()
    pending = []
    for namespace in scanned:
        base = namespace.root / namespace.package_dir
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or not path.name.startswith("."):
                continue
            if not path.name.endswith(namespace.suffix):
                continue
            if not namespace.recognizer(path):
                raise ExecutionLaunchAmendmentError(
                    f"unrecognized package temporary:{path}"
                )
            target = intended_target_for_temporary(
                path, namespace.suffix
            )
            if target.exists():
                raise ExecutionLaunchAmendmentError(
                    "ambiguous atomic state:"
                    f"target={target}:temporary={path}"
                )
            pending.append({
                "temporary": str(path),
                "target": str(target),
                "recovery_owner": "existing_exact_atomic_write",
            })
    value = {
        "pending_exact_recoveries": pending,
        "pending_count": len(pending),
    }
    value["temporary_entry_digest"] = digest(value)
    return value


def validate_production_worktree_rows(
    rows: Sequence[str],
) -> dict[str, Any]:
    invalid = []
    for row in rows:
        candidate = row[3:].strip()
        if not prior.is_allowed_runtime_worktree_path(candidate):
            invalid.append(row)
    if invalid:
        raise ExecutionLaunchAmendmentError(
            f"unexpected production worktree changes:{invalid}"
        )
    value = {
        "row_count": len(rows),
        "rows": list(rows),
        "allowed": True,
    }
    value["worktree_digest"] = digest(value)
    return value


def require_launch_worktree(command: str) -> dict[str, Any]:
    rows = _git("status", "--porcelain=v1").splitlines()
    if command == "service-canary":
        if rows:
            raise ExecutionLaunchAmendmentError(
                f"canary worktree is not clean:{rows}"
            )
        return {
            "row_count": 0,
            "rows": [],
            "allowed": True,
            "worktree_digest": digest({
                "row_count": 0, "rows": [], "allowed": True
            }),
        }
    if command not in PRODUCTION_COMMANDS:
        raise ExecutionLaunchAmendmentError(
            f"invalid worktree command:{command}"
        )
    value = validate_production_worktree_rows(rows)
    # The row-level gate establishes that only inherited runtime roots appear.
    # The inherited deep scan then proves every file inside those roots has one
    # of the exact frozen journal/carrier/marker names.
    prior._require_clean_worktree(allow_runtime=True)
    return value


def freeze_package_manifests(source_commit: str) -> dict[str, Any]:
    if _git("status", "--porcelain=v1"):
        raise ExecutionLaunchAmendmentError("worktree is not clean")
    if _git("rev-parse", "HEAD") != source_commit:
        raise ExecutionLaunchAmendmentError(
            "source freeze commit is not HEAD"
        )
    if (ROOT / SOURCE_MANIFEST_PATH).exists() or (
        ROOT / ARTIFACT_BINDING_PATH
    ).exists():
        raise FileExistsError("amendment manifests already exist")
    pre_review = verify_pre_review_closure()
    source = {
        "schema_version": "native_v2_execution_launch_source.v1",
        "package_id": PACKAGE_ID,
        "source_freeze_commit": source_commit,
        "source_hashes": {
            relative: sha256_file(ROOT / relative)
            for relative in SOURCE_FILES
        },
        "module_path": MODULE_PATH,
        "public_child_commands": {
            command: list(build_public_command(command))
            for command in PUBLIC_CHILD_COMMANDS
        },
        "runtime": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "working_directory": str(ROOT),
        },
        "pre_review": pre_review,
        "architecture": {
            "outer_launch_amendment_only": True,
            "passed_scientific_logic_imported": True,
            "module_global_replacement": False,
            "large_driver_copy": False,
            "final_readiness_required_for_production": True,
            "recorded_launch_context_required": True,
            "atomic_per_command_launch_lock": True,
            "terminal_capture_before_cleanup": True,
        },
    }
    source["source_manifest_digest"] = digest(source)
    atomic_json(ROOT / SOURCE_MANIFEST_PATH, source)
    binding = {
        "schema_version": "native_v2_execution_launch_binding.v1",
        "package_id": PACKAGE_ID,
        "source_manifest": {
            "path": SOURCE_MANIFEST_PATH.as_posix(),
            "sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
            "digest": source["source_manifest_digest"],
        },
        "pre_review": pre_review,
        "paths": {
            "launch_readiness": LAUNCH_READINESS_PATH.as_posix(),
            "service_canary_record": SERVICE_CANARY_RECORD_PATH.as_posix(),
            "readiness": READINESS_PATH.as_posix(),
            "production_records": PRODUCTION_RECORD_DIR.as_posix(),
            "outcome_result_binding": (
                OUTCOME_RESULT_BINDING_PATH.as_posix()
            ),
        },
        "service_law": {
            "unique_attempt": True,
            "four_item_python_argv": True,
            "recorded_launch_context": True,
            "per_command_lock": True,
            "terminal_cleanup": True,
            "canary_duration_seconds": CANARY_DURATION_SECONDS,
        },
        "outcome_access": {"count": 0, "event_ids": []},
    }
    binding["artifact_binding_digest"] = digest(binding)
    atomic_json(ROOT / ARTIFACT_BINDING_PATH, binding)
    return {
        "source_manifest_sha256": sha256_file(
            ROOT / SOURCE_MANIFEST_PATH
        ),
        "source_manifest_digest": source["source_manifest_digest"],
        "artifact_binding_sha256": sha256_file(
            ROOT / ARTIFACT_BINDING_PATH
        ),
        "artifact_binding_digest": binding["artifact_binding_digest"],
    }


def verify_package_manifests() -> dict[str, Any]:
    source = load_json(ROOT / SOURCE_MANIFEST_PATH)
    source_digest = verify_self_digest(
        source, "source_manifest_digest", label="source manifest"
    )
    for relative, expected in source["source_hashes"].items():
        if sha256_file(ROOT / relative) != expected:
            raise ExecutionLaunchAmendmentError(
                f"amendment source changed:{relative}"
            )
    binding = load_json(ROOT / ARTIFACT_BINDING_PATH)
    binding_digest = verify_self_digest(
        binding, "artifact_binding_digest", label="artifact binding"
    )
    pre_review = verify_pre_review_closure()
    if (
        binding["source_manifest"]["sha256"]
        != sha256_file(ROOT / SOURCE_MANIFEST_PATH)
        or binding["source_manifest"]["digest"] != source_digest
        or canonical_bytes(source["pre_review"])
        != canonical_bytes(pre_review)
        or canonical_bytes(binding["pre_review"])
        != canonical_bytes(pre_review)
        or binding["outcome_access"]
        != {"count": 0, "event_ids": []}
    ):
        raise ExecutionLaunchAmendmentError(
            "amendment manifest binding changed"
        )
    return {
        "source_manifest_sha256": sha256_file(
            ROOT / SOURCE_MANIFEST_PATH
        ),
        "source_manifest_digest": source_digest,
        "artifact_binding_sha256": sha256_file(
            ROOT / ARTIFACT_BINDING_PATH
        ),
        "artifact_binding_digest": binding_digest,
        "pre_review_digest": pre_review["pre_review_digest"],
    }


def run_launch_readiness() -> dict[str, Any]:
    require_launch_worktree("service-canary")
    if (ROOT / LAUNCH_READINESS_PATH).exists():
        raise FileExistsError("launch readiness already exists")
    require_committed(SOURCE_MANIFEST_PATH)
    require_committed(ARTIFACT_BINDING_PATH)
    started = time.perf_counter()
    package = verify_package_manifests()
    pre_review = verify_pre_review_closure()
    value = {
        "schema_version": "native_v2_execution_launch_readiness.v1",
        "package_id": PACKAGE_ID,
        "source_manifest": {
            "sha256": package["source_manifest_sha256"],
            "digest": package["source_manifest_digest"],
        },
        "artifact_binding": {
            "sha256": package["artifact_binding_sha256"],
            "digest": package["artifact_binding_digest"],
        },
        "pre_review_readiness": pre_review["readiness"],
        "cohort_digest": ACCEPTED_COHORT_DIGEST,
        "expanded_package_map_digest": EXPANDED_PACKAGE_MAP_DIGEST,
        "canary_duration_seconds": CANARY_DURATION_SECONDS,
        "production_launch_authorized": False,
        "real_exposure_run": False,
        "real_outcome_run": False,
        "outcome_access": {"count": 0, "event_ids": []},
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }
    value["launch_readiness_digest"] = digest(value)
    atomic_json(ROOT / LAUNCH_READINESS_PATH, value)
    return value


def load_and_verify_launch_readiness(
    *, committed: bool
) -> dict[str, Any]:
    if committed:
        require_committed(LAUNCH_READINESS_PATH)
    value = load_json(ROOT / LAUNCH_READINESS_PATH)
    verify_self_digest(
        value, "launch_readiness_digest", label="launch readiness"
    )
    package = verify_package_manifests()
    pre_review = verify_pre_review_closure()
    if (
        value.get("schema_version")
        != "native_v2_execution_launch_readiness.v1"
        or value.get("package_id") != PACKAGE_ID
        or value.get("source_manifest")
        != {
            "sha256": package["source_manifest_sha256"],
            "digest": package["source_manifest_digest"],
        }
        or value.get("artifact_binding")
        != {
            "sha256": package["artifact_binding_sha256"],
            "digest": package["artifact_binding_digest"],
        }
        or value.get("pre_review_readiness")
        != pre_review["readiness"]
        or value.get("cohort_digest") != ACCEPTED_COHORT_DIGEST
        or value.get("expanded_package_map_digest")
        != EXPANDED_PACKAGE_MAP_DIGEST
        or value.get("production_launch_authorized") is not False
        or value.get("real_exposure_run") is not False
        or value.get("real_outcome_run") is not False
        or value.get("outcome_access")
        != {"count": 0, "event_ids": []}
    ):
        raise ExecutionLaunchAmendmentError(
            "launch readiness identity changed"
        )
    return value


def load_and_verify_final_readiness(
    *, committed: bool = True
) -> dict[str, Any]:
    if committed:
        require_committed(READINESS_PATH)
    value = load_json(ROOT / READINESS_PATH)
    verify_self_digest(value, "readiness_digest", label="final readiness")
    package = verify_package_manifests()
    launch = load_and_verify_launch_readiness(committed=True)
    canary_binding = require_committed(SERVICE_CANARY_RECORD_PATH)
    canary = load_json(ROOT / SERVICE_CANARY_RECORD_PATH)
    verify_self_digest(
        canary, "final_record_digest", label="service canary"
    )
    pre_review = verify_pre_review_closure()
    expected = {
        "schema_version": "native_v2_execution_launch_final.v1",
        "package_id": PACKAGE_ID,
        "source_manifest": {
            "sha256": package["source_manifest_sha256"],
            "digest": package["source_manifest_digest"],
        },
        "artifact_binding": {
            "sha256": package["artifact_binding_sha256"],
            "digest": package["artifact_binding_digest"],
        },
        "launch_readiness": {
            "sha256": sha256_file(ROOT / LAUNCH_READINESS_PATH),
            "digest": launch["launch_readiness_digest"],
        },
        "service_canary": {
            **canary_binding,
            "digest": canary["final_record_digest"],
            "attempt_id": canary["attempt_id"],
            "elapsed_seconds": canary["child_result"][
                "elapsed_seconds"
            ],
        },
        "pre_review_readiness": pre_review["readiness"],
        "cohort_digest": ACCEPTED_COHORT_DIGEST,
        "expanded_package_map_digest": EXPANDED_PACKAGE_MAP_DIGEST,
        "production_launch_authorized": True,
        "real_exposure_run": False,
        "real_outcome_run": False,
        "outcome_access": {"count": 0, "event_ids": []},
        "stop_before_exposure": True,
    }
    validate_final_readiness_identity(value, expected)
    return value


def validate_final_readiness_identity(
    value: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> None:
    if set(value) != {*expected, "readiness_digest"}:
        raise ExecutionLaunchAmendmentError(
            "final readiness field set changed"
        )
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise ExecutionLaunchAmendmentError(
                f"final readiness identity changed:{key}"
            )


def run_final_readiness() -> dict[str, Any]:
    require_launch_worktree("service-canary")
    if (ROOT / READINESS_PATH).exists():
        raise FileExistsError("final readiness already exists")
    package = verify_package_manifests()
    launch = load_and_verify_launch_readiness(committed=True)
    canary_binding = require_committed(SERVICE_CANARY_RECORD_PATH)
    canary = load_json(ROOT / SERVICE_CANARY_RECORD_PATH)
    verify_self_digest(
        canary, "final_record_digest", label="service canary"
    )
    child = canary.get("child_result", {})
    if (
        canary.get("command") != "service-canary"
        or canary.get("terminal") is not True
        or canary.get("terminal_status", {}).get("result") != "success"
        or canary.get("terminal_status", {}).get("exit_status") != 0
        or canary.get("terminal_status", {}).get("runtime_max_usec")
        not in {"infinity", "18446744073709551615"}
        or canary.get("cleanup", {}).get("completed") is not True
        or float(child.get("elapsed_seconds", 0))
        < CANARY_DURATION_SECONDS
        or child.get("requested_seconds") != CANARY_DURATION_SECONDS
        or canary.get("launch", {}).get("readiness", {}).get("sha256")
        != sha256_file(ROOT / LAUNCH_READINESS_PATH)
    ):
        raise ExecutionLaunchAmendmentError(
            "corrected detached canary gate failed"
        )
    pre_review = verify_pre_review_closure()
    value = {
        "schema_version": "native_v2_execution_launch_final.v1",
        "package_id": PACKAGE_ID,
        "source_manifest": {
            "sha256": package["source_manifest_sha256"],
            "digest": package["source_manifest_digest"],
        },
        "artifact_binding": {
            "sha256": package["artifact_binding_sha256"],
            "digest": package["artifact_binding_digest"],
        },
        "launch_readiness": {
            "sha256": sha256_file(ROOT / LAUNCH_READINESS_PATH),
            "digest": launch["launch_readiness_digest"],
        },
        "service_canary": {
            **canary_binding,
            "digest": canary["final_record_digest"],
            "attempt_id": canary["attempt_id"],
            "elapsed_seconds": child["elapsed_seconds"],
        },
        "pre_review_readiness": pre_review["readiness"],
        "cohort_digest": ACCEPTED_COHORT_DIGEST,
        "expanded_package_map_digest": EXPANDED_PACKAGE_MAP_DIGEST,
        "production_launch_authorized": True,
        "real_exposure_run": False,
        "real_outcome_run": False,
        "outcome_access": {"count": 0, "event_ids": []},
        "stop_before_exposure": True,
    }
    value["readiness_digest"] = digest(value)
    atomic_json(ROOT / READINESS_PATH, value)
    return value


def _systemctl_show(service_name: str) -> dict[str, str]:
    properties = (
        "LoadState",
        "ActiveState",
        "SubState",
        "Result",
        "ExecMainPID",
        "ExecMainCode",
        "ExecMainStatus",
        "ExecMainStartTimestamp",
        "ExecMainExitTimestamp",
        "RuntimeMaxUSec",
        "InvocationID",
    )
    result = subprocess.run(
        [
            "systemctl", "--user", "show", service_name, "--no-pager",
            *[f"--property={item}" for item in properties],
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ExecutionLaunchAmendmentError(json.dumps({
            "detail": "service status unavailable",
            "service_name": service_name,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }, sort_keys=True))
    values = {}
    for line in result.stdout.splitlines():
        key, separator, item = line.partition("=")
        if separator:
            values[key] = item
    if set(properties) - set(values):
        raise ExecutionLaunchAmendmentError(
            f"incomplete service status:{service_name}"
        )
    return values


def _service_terminal(status: Mapping[str, str]) -> bool:
    return (
        status["SubState"] in {"exited", "dead", "failed"}
        and bool(status["ExecMainCode"])
    )


def _load_external(path: Path, key: str) -> dict[str, Any]:
    value = load_json(path)
    verify_self_digest(value, key, label=str(path))
    return value


def _external_attempt_dirs(root: Path) -> tuple[Path, ...]:
    return () if not root.exists() else tuple(sorted(
        path for path in root.iterdir() if path.is_dir()
    ))


def reject_concurrent_matching_run(
    command: str,
    *,
    attempt_root: Path,
    status_reader: Callable[[str], Mapping[str, str]],
) -> None:
    for directory in _external_attempt_dirs(attempt_root):
        launch_path = directory / "launch.json"
        if not launch_path.is_file():
            continue
        launch = _load_external(launch_path, "launch_record_digest")
        if launch.get("command") != command:
            continue
        final_path = directory / "final.json"
        if final_path.exists():
            _load_external(final_path, "final_record_digest")
            continue
        status = status_reader(str(launch["service_name"]))
        if not _service_terminal(status):
            raise ExecutionLaunchAmendmentError(
                f"concurrent matching service:{launch['attempt_id']}"
            )
        raise ExecutionLaunchAmendmentError(
            "terminal matching service must be finalized before relaunch:"
            f"{launch['attempt_id']}"
        )


@contextmanager
def acquire_launch_lock(
    command: str,
    *,
    lock_root: Path,
    owner: str,
) -> Iterator[dict[str, Any]]:
    if command not in PUBLIC_CHILD_COMMANDS:
        raise ExecutionLaunchAmendmentError(
            f"invalid lock command:{command}"
        )
    lock_root.mkdir(parents=True, exist_ok=True)
    path = lock_root / f"{command}.lock"
    value = {
        "schema_version": "native_v2_execution_launch_lock.v1",
        "package_id": PACKAGE_ID,
        "command": command,
        "owner": owner,
        "process_id": os.getpid(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    value["lock_digest"] = digest(value)
    payload = pretty_json_bytes(value)
    try:
        descriptor = os.open(
            path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
        )
    except FileExistsError as exc:
        raise ExecutionLaunchAmendmentError(
            f"launch lock already exists:{path}"
        ) from exc
    try:
        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _fsync_directory(lock_root)
    try:
        yield {**value, "path": str(path)}
    finally:
        path.unlink()
        _fsync_directory(lock_root)


def build_service_argv(
    *,
    service_name: str,
    stdout_path: Path,
    stderr_path: Path,
    environment: Mapping[str, str],
    child_command: Sequence[str],
) -> tuple[str, ...]:
    values = [
        "systemd-run",
        "--user",
        f"--unit={service_name}",
        "--property=Type=exec",
        "--property=RemainAfterExit=yes",
        f"--property=WorkingDirectory={ROOT}",
        f"--property=StandardOutput=file:{stdout_path}",
        f"--property=StandardError=file:{stderr_path}",
    ]
    values.extend(
        f"--setenv={key}={item}"
        for key, item in sorted(environment.items())
    )
    values.extend(("--", *child_command))
    return tuple(values)


def _readiness_launch_identity(
    command: str,
    *,
    final_loader: Callable[..., Mapping[str, Any]],
    launch_loader: Callable[..., Mapping[str, Any]],
) -> dict[str, Any]:
    if command == "service-canary":
        value = dict(launch_loader(committed=True))
        return {
            "kind": "launch_readiness",
            "path": LAUNCH_READINESS_PATH.as_posix(),
            "sha256": sha256_file(ROOT / LAUNCH_READINESS_PATH),
            "digest": value["launch_readiness_digest"],
        }
    value = dict(final_loader(committed=True))
    return {
        "kind": "final_readiness",
        "path": READINESS_PATH.as_posix(),
        "sha256": sha256_file(ROOT / READINESS_PATH),
        "digest": value["readiness_digest"],
    }


def _new_attempt_id() -> str:
    return (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        + "-"
        + uuid.uuid4().hex
    )


def _completed_process(argv: Sequence[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(argv),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def launch_service_attempt(
    command: str,
    *,
    canary_seconds: int | None = None,
    attempt_root: Path | None = None,
    lock_root: Path | None = None,
    attempt_id_factory: Callable[[], str] = _new_attempt_id,
    worktree_validator: Callable[[str], Mapping[str, Any]] = (
        require_launch_worktree
    ),
    package_verifier: Callable[[], Mapping[str, Any]] = (
        verify_package_manifests
    ),
    final_readiness_loader: Callable[..., Mapping[str, Any]] = (
        load_and_verify_final_readiness
    ),
    launch_readiness_loader: Callable[..., Mapping[str, Any]] = (
        load_and_verify_launch_readiness
    ),
    readiness_identity: Mapping[str, Any] | None = None,
    status_reader: Callable[[str], Mapping[str, str]] = _systemctl_show,
    dispatch_runner: Callable[
        [Sequence[str]], subprocess.CompletedProcess
    ] = _completed_process,
    exact_head: str | None = None,
) -> dict[str, Any]:
    if command not in PUBLIC_CHILD_COMMANDS:
        raise ExecutionLaunchAmendmentError(
            f"invalid service command:{command}"
        )
    if command == "service-canary":
        if canary_seconds is None or canary_seconds < 1:
            raise ExecutionLaunchAmendmentError(
                "service canary duration is absent"
            )
        extra = {"RECON_SERVICE_CANARY_SECONDS": str(canary_seconds)}
    elif canary_seconds is not None:
        raise ExecutionLaunchAmendmentError(
            "duration applies only to service canary"
        )
    else:
        extra = {}
    enforce_entry_temporary_invariants()
    worktree = dict(worktree_validator(command))
    package = dict(package_verifier())
    readiness = (
        copy.deepcopy(dict(readiness_identity))
        if readiness_identity is not None
        else _readiness_launch_identity(
            command,
            final_loader=final_readiness_loader,
            launch_loader=launch_readiness_loader,
        )
    )
    if command == "run-science":
        load_successful_exposure_attempt_record()
    attempt_base = attempt_root or service_attempt_root()
    locks = lock_root or service_lock_root()
    owner = uuid.uuid4().hex
    with acquire_launch_lock(command, lock_root=locks, owner=owner) as lock:
        reject_concurrent_matching_run(
            command,
            attempt_root=attempt_base,
            status_reader=status_reader,
        )
        attempt_id = attempt_id_factory()
        if not _ATTEMPT_ID.fullmatch(attempt_id):
            raise ExecutionLaunchAmendmentError(
                f"invalid generated attempt ID:{attempt_id}"
            )
        directory = attempt_base / attempt_id
        directory.mkdir(parents=True, exist_ok=False)
        stdout_path = directory / "stdout.log"
        stderr_path = directory / "stderr.log"
        child_command = build_public_command(command)
        head = exact_head or _git("rev-parse", "HEAD")
        identity = {
            "schema_version": "native_v2_launch_identity.v1",
            "package_id": PACKAGE_ID,
            "attempt_id": attempt_id,
            "command": command,
            "service_name": (
                f"{SERVICE_PREFIX}-{command}-{attempt_id}"
            ),
            "exact_head": head,
            "readiness": readiness,
            "exact_python_argv": list(child_command),
            "working_directory": str(ROOT),
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "base_environment": deterministic_environment(extra),
            "package_identity": package,
            "worktree": worktree,
        }
        launch_digest = digest(identity)
        context = {
            CONTEXT_ATTEMPT: attempt_id,
            CONTEXT_COMMAND: command,
            CONTEXT_DIGEST: launch_digest,
            CONTEXT_RECORD: str(directory / "launch.json"),
            CONTEXT_READINESS_SHA: (
                readiness["sha256"]
                if readiness["kind"] == "final_readiness"
                else ""
            ),
            CONTEXT_READINESS_DIGEST: (
                readiness["digest"]
                if readiness["kind"] == "final_readiness"
                else ""
            ),
        }
        environment = deterministic_environment({**extra, **context})
        systemd_argv = build_service_argv(
            service_name=identity["service_name"],
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            environment=environment,
            child_command=child_command,
        )
        launch = {
            "schema_version": "native_v2_launch_record.v1",
            "package_id": PACKAGE_ID,
            "attempt_id": attempt_id,
            "command": command,
            "service_name": identity["service_name"],
            "identity": identity,
            "launch_digest": launch_digest,
            "child_context": context,
            "environment": environment,
            "systemd_argv": list(systemd_argv),
            "launch_lock": {
                "command": lock["command"],
                "owner": lock["owner"],
                "lock_digest": lock["lock_digest"],
            },
            "requested_at_utc": datetime.now(timezone.utc).isoformat(),
            "no_shell_transformation": True,
            "no_wall_clock_timeout": True,
            "lawful_restart_requires_new_attempt": True,
        }
        launch["launch_record_digest"] = digest(launch)
        atomic_json(directory / "launch.json", launch)
        result = dispatch_runner(systemd_argv)
        dispatch = {
            "schema_version": "native_v2_launch_dispatch.v1",
            "package_id": PACKAGE_ID,
            "attempt_id": attempt_id,
            "returncode": int(result.returncode),
            "stdout": str(result.stdout),
            "stderr": str(result.stderr),
            "dispatched_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        dispatch["dispatch_digest"] = digest(dispatch)
        atomic_json(directory / "dispatch.json", dispatch)
        if result.returncode != 0:
            raise ExecutionLaunchAmendmentError(
                f"service dispatch failed:{attempt_id}:"
                f"{result.returncode}"
            )
        observed = None
        for _ in range(60):
            status = dict(status_reader(identity["service_name"]))
            if (
                status["ExecMainPID"] not in {"", "0"}
                or _service_terminal(status)
            ):
                observed = status
                break
            time.sleep(0.1)
        if observed is None:
            raise ExecutionLaunchAmendmentError(
                f"service PID was not observed:{attempt_id}"
            )
        observation = {
            "schema_version": "native_v2_launch_observation.v1",
            "package_id": PACKAGE_ID,
            "attempt_id": attempt_id,
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": observed,
        }
        observation["observation_digest"] = digest(observation)
        atomic_json(directory / "observation.json", observation)
    return {
        "attempt_id": attempt_id,
        "service_name": identity["service_name"],
        "process_id": int(observed["ExecMainPID"] or 0),
        "status": observed,
        "external_attempt_directory": str(directory),
        "launch_digest": launch_digest,
        "launch_record_digest": launch["launch_record_digest"],
    }


def validate_launch_context(
    expected_command: str,
    *,
    environment: Mapping[str, str] | None = None,
    attempt_root: Path | None = None,
    final_readiness_loader: Callable[..., Mapping[str, Any]] = (
        load_and_verify_final_readiness
    ),
    launch_readiness_loader: Callable[..., Mapping[str, Any]] = (
        load_and_verify_launch_readiness
    ),
    readiness_identity: Mapping[str, Any] | None = None,
    package_identity: Mapping[str, Any] | None = None,
    expected_head: str | None = None,
) -> dict[str, Any]:
    env = os.environ if environment is None else environment
    missing = [key for key in CONTEXT_KEYS if key not in env]
    if missing:
        raise ExecutionLaunchAmendmentError(
            f"recorded launch context is absent:{missing}"
        )
    attempt_id = str(env[CONTEXT_ATTEMPT])
    if not _ATTEMPT_ID.fullmatch(attempt_id):
        raise ExecutionLaunchAmendmentError(
            "launch context attempt ID is invalid"
        )
    record_path = Path(str(env[CONTEXT_RECORD]))
    root = attempt_root or service_attempt_root()
    expected_path = root / attempt_id / "launch.json"
    if record_path.resolve() != expected_path.resolve():
        raise ExecutionLaunchAmendmentError(
            "launch context record path is foreign"
        )
    launch = _load_external(record_path, "launch_record_digest")
    identity = launch["identity"]
    expected_service_name = (
        f"{SERVICE_PREFIX}-{expected_command}-{attempt_id}"
    )
    expected_stdout = expected_path.parent / "stdout.log"
    expected_stderr = expected_path.parent / "stderr.log"
    extra = (
        {
            "RECON_SERVICE_CANARY_SECONDS": str(
                env.get("RECON_SERVICE_CANARY_SECONDS", "")
            )
        }
        if expected_command == "service-canary"
        else {}
    )
    expected_base_environment = deterministic_environment(extra)
    expected_child_context = {
        key: str(env[key]) for key in CONTEXT_KEYS
    }
    expected_environment = deterministic_environment(
        {**extra, **expected_child_context}
    )
    expected_package = (
        copy.deepcopy(dict(package_identity))
        if package_identity is not None
        else verify_package_manifests()
    )
    current_head = expected_head or _git("rev-parse", "HEAD")
    expected_identity_fields = {
        "schema_version",
        "package_id",
        "attempt_id",
        "command",
        "service_name",
        "exact_head",
        "readiness",
        "exact_python_argv",
        "working_directory",
        "stdout_path",
        "stderr_path",
        "base_environment",
        "package_identity",
        "worktree",
    }
    expected_launch_fields = {
        "schema_version",
        "package_id",
        "attempt_id",
        "command",
        "service_name",
        "identity",
        "launch_digest",
        "child_context",
        "environment",
        "systemd_argv",
        "launch_lock",
        "requested_at_utc",
        "no_shell_transformation",
        "no_wall_clock_timeout",
        "lawful_restart_requires_new_attempt",
        "launch_record_digest",
    }
    expected_systemd_argv = list(build_service_argv(
        service_name=expected_service_name,
        stdout_path=expected_stdout,
        stderr_path=expected_stderr,
        environment=expected_environment,
        child_command=build_public_command(expected_command),
    ))
    launch_lock = launch.get("launch_lock", {})
    if (
        expected_command not in PUBLIC_CHILD_COMMANDS
        or set(identity) != expected_identity_fields
        or set(launch) != expected_launch_fields
        or identity.get("schema_version")
        != "native_v2_launch_identity.v1"
        or launch.get("schema_version")
        != "native_v2_launch_record.v1"
        or identity.get("package_id") != PACKAGE_ID
        or launch.get("package_id") != PACKAGE_ID
        or launch.get("command") != expected_command
        or launch.get("attempt_id") != attempt_id
        or identity.get("command") != expected_command
        or identity.get("attempt_id") != attempt_id
        or launch.get("service_name") != expected_service_name
        or identity.get("service_name") != expected_service_name
        or identity.get("exact_head") != current_head
        or launch.get("launch_digest") != digest(identity)
        or env[CONTEXT_COMMAND] != expected_command
        or env[CONTEXT_DIGEST] != launch["launch_digest"]
        or launch.get("child_context") != expected_child_context
        or identity.get("exact_python_argv")
        != list(build_public_command(expected_command))
        or identity.get("working_directory") != str(Path.cwd())
        or identity.get("stdout_path") != str(expected_stdout)
        or identity.get("stderr_path") != str(expected_stderr)
        or identity.get("base_environment")
        != expected_base_environment
        or identity.get("package_identity") != expected_package
        or launch.get("environment") != expected_environment
        or launch.get("systemd_argv") != expected_systemd_argv
        or set(launch_lock) != {"command", "owner", "lock_digest"}
        or launch_lock.get("command") != expected_command
        or not re.fullmatch(
            r"[0-9a-f]{32}", str(launch_lock.get("owner", ""))
        )
        or not re.fullmatch(
            r"[0-9a-f]{64}", str(launch_lock.get("lock_digest", ""))
        )
        or launch.get("no_shell_transformation") is not True
        or launch.get("no_wall_clock_timeout") is not True
        or launch.get("lawful_restart_requires_new_attempt") is not True
    ):
        raise ExecutionLaunchAmendmentError(
            "recorded launch context identity changed"
        )
    readiness = identity["readiness"]
    if readiness_identity is not None:
        expected_readiness = copy.deepcopy(dict(readiness_identity))
    elif expected_command == "service-canary":
        current = dict(launch_readiness_loader(committed=True))
        expected_readiness = {
            "kind": "launch_readiness",
            "path": LAUNCH_READINESS_PATH.as_posix(),
            "sha256": sha256_file(ROOT / LAUNCH_READINESS_PATH),
            "digest": current["launch_readiness_digest"],
        }
    else:
        current = dict(final_readiness_loader(committed=True))
        expected_readiness = {
            "kind": "final_readiness",
            "path": READINESS_PATH.as_posix(),
            "sha256": sha256_file(ROOT / READINESS_PATH),
            "digest": current["readiness_digest"],
        }
    if expected_command == "service-canary":
        if env[CONTEXT_READINESS_SHA] or env[CONTEXT_READINESS_DIGEST]:
            raise ExecutionLaunchAmendmentError(
                "canary received production readiness context"
            )
    else:
        if (
            env[CONTEXT_READINESS_SHA] != expected_readiness["sha256"]
            or env[CONTEXT_READINESS_DIGEST]
            != expected_readiness["digest"]
        ):
            raise ExecutionLaunchAmendmentError(
                "production final readiness context changed"
            )
    if readiness != expected_readiness:
        raise ExecutionLaunchAmendmentError(
            "launch record readiness identity changed"
        )
    value = {
        "attempt_id": attempt_id,
        "command": expected_command,
        "launch_digest": launch["launch_digest"],
        "launch_record_digest": launch["launch_record_digest"],
        "readiness": readiness,
    }
    value["validated_context_digest"] = digest(value)
    return value


def bind_json_artifact(
    relative: Path,
    *,
    digest_key: str,
    require_git_commit: bool,
) -> dict[str, Any]:
    if require_git_commit:
        committed = require_committed(relative)
    else:
        path = ROOT / relative
        if not path.is_file():
            raise ExecutionLaunchAmendmentError(
                f"required artifact is absent:{relative}"
            )
        committed = {
            "path": relative.as_posix(),
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
        }
    value = load_json(ROOT / relative)
    artifact_digest = verify_self_digest(
        value, digest_key, label=relative.as_posix()
    )
    return {**committed, "digest": artifact_digest}


def bind_result_artifact(
    *, require_git_commit: bool
) -> dict[str, Any]:
    relative = prior.RESULT_PATH
    path = ROOT / relative
    if require_git_commit:
        binding = require_committed(relative)
    else:
        if not path.is_file():
            raise ExecutionLaunchAmendmentError(
                "scientific result is absent"
            )
        binding = {
            "path": relative.as_posix(),
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
        }
    value = json.loads(gzip.decompress(path.read_bytes()))
    result_digest = verify_self_digest(
        value, "canonical_result_digest", label="scientific result"
    )
    return {**binding, "digest": result_digest}


def bind_production_artifacts(
    command: str, *, require_git_commit: bool
) -> dict[str, Any]:
    if command == "run-exposure":
        value = {
            "exposure": bind_json_artifact(
                prior.EXPOSURE_PATH,
                digest_key="exposure_digest",
                require_git_commit=require_git_commit,
            ),
            "execution_manifest": bind_json_artifact(
                prior.EXECUTION_MANIFEST_PATH,
                digest_key="execution_manifest_digest",
                require_git_commit=require_git_commit,
            ),
            "completion": bind_json_artifact(
                prior.EXPOSURE_COMPLETION_PATH,
                digest_key="completion_digest",
                require_git_commit=require_git_commit,
            ),
        }
    elif command == "run-science":
        value = {
            "scientific_result": bind_result_artifact(
                require_git_commit=require_git_commit
            )
        }
    else:
        raise ExecutionLaunchAmendmentError(
            f"no production artifact binding:{command}"
        )
    value["artifact_set_digest"] = digest(value)
    return value


def load_successful_exposure_attempt_record() -> dict[str, Any]:
    root = ROOT / PRODUCTION_RECORD_DIR / "run-exposure"
    paths = () if not root.exists() else tuple(sorted(root.glob("*.json")))
    successes = []
    for path in paths:
        relative = path.relative_to(ROOT)
        require_committed(relative)
        value = load_json(path)
        verify_self_digest(
            value, "final_record_digest", label=relative.as_posix()
        )
        if (
            value.get("command") == "run-exposure"
            and value.get("terminal_status", {}).get("exit_status") == 0
            and value.get("terminal_status", {}).get("result") == "success"
        ):
            successes.append(value)
    if len(successes) != 1:
        raise ExecutionLaunchAmendmentError(
            "science requires exactly one committed successful "
            f"exposure service record:{len(successes)}"
        )
    record = successes[0]
    readiness = load_and_verify_final_readiness(committed=True)
    validate_successful_exposure_record(
        record,
        readiness_identity={
            "kind": "final_readiness",
            "path": READINESS_PATH.as_posix(),
            "sha256": sha256_file(ROOT / READINESS_PATH),
            "digest": readiness["readiness_digest"],
        },
        artifact_binding=bind_production_artifacts(
            "run-exposure", require_git_commit=True
        ),
    )
    return record


def validate_successful_exposure_record(
    record: Mapping[str, Any],
    *,
    readiness_identity: Mapping[str, Any],
    artifact_binding: Mapping[str, Any],
) -> None:
    if (
        record.get("command") != "run-exposure"
        or record.get("terminal") is not True
        or record.get("terminal_status", {}).get("exit_status") != 0
        or record.get("terminal_status", {}).get("result") != "success"
        or record.get("launch", {}).get("identity", {}).get("readiness")
        != readiness_identity
        or record.get("artifact_binding") != artifact_binding
    ):
        raise ExecutionLaunchAmendmentError(
            "successful exposure service/artifact binding changed"
        )


def validate_science_admission(
    *,
    readiness_loader: Callable[..., Mapping[str, Any]] = (
        load_and_verify_final_readiness
    ),
    exposure_record_loader: Callable[[], Mapping[str, Any]] = (
        load_successful_exposure_attempt_record
    ),
    completed_exposure_loader: Callable[[], Mapping[str, Any]] = (
        prior.validate_completed_exposure
    ),
) -> dict[str, Any]:
    readiness = dict(readiness_loader(committed=True))
    exposure_record = dict(exposure_record_loader())
    completed = dict(completed_exposure_loader())
    value = {
        "final_readiness_digest": readiness["readiness_digest"],
        "exposure_attempt_id": exposure_record["attempt_id"],
        "exposure_record_digest": exposure_record[
            "final_record_digest"
        ],
        "exposure_digest": completed["exposure"]["exposure_digest"],
        "execution_manifest_digest": completed["execution_manifest"][
            "execution_manifest_digest"
        ],
        "completion_digest": completed["completion"][
            "completion_digest"
        ],
    }
    value["science_admission_digest"] = digest(value)
    return value


@dataclass(frozen=True)
class ChildDependencies:
    entry_gate: Callable[[], Mapping[str, Any]]
    readiness_loader: Callable[..., Mapping[str, Any]]
    context_validator: Callable[[str], Mapping[str, Any]]
    worktree_validator: Callable[[str], Mapping[str, Any]]
    exposure_admission: Callable[[], Mapping[str, Any]]
    exposure_delegate: Callable[[], Mapping[str, Any]]
    science_delegate: Callable[[], Mapping[str, Any]]


def production_child_dependencies() -> ChildDependencies:
    return ChildDependencies(
        entry_gate=enforce_entry_temporary_invariants,
        readiness_loader=load_and_verify_final_readiness,
        context_validator=validate_launch_context,
        worktree_validator=require_launch_worktree,
        exposure_admission=validate_science_admission,
        exposure_delegate=prior.run_exposure,
        science_delegate=prior.run_science,
    )


def _bounded_child_result(
    command: str,
    context: Mapping[str, Any],
    delegated: Mapping[str, Any],
    *,
    admission: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    value = {
        "schema_version": "native_v2_recorded_child_result.v1",
        "package_id": PACKAGE_ID,
        "command": command,
        "attempt_id": context["attempt_id"],
        "launch_digest": context["launch_digest"],
        "final_readiness": context["readiness"],
        "delegated_result_digest": digest(delegated),
        "admission": (
            None if admission is None else copy.deepcopy(dict(admission))
        ),
    }
    value["child_result_digest"] = digest(value)
    return value


def run_exposure_child(
    dependencies: ChildDependencies | None = None,
) -> dict[str, Any]:
    deps = dependencies or production_child_dependencies()
    deps.entry_gate()
    deps.readiness_loader(committed=True)
    context = dict(deps.context_validator("run-exposure"))
    deps.worktree_validator("run-exposure")
    delegated = dict(deps.exposure_delegate())
    return _bounded_child_result(
        "run-exposure", context, delegated
    )


def run_science_child(
    dependencies: ChildDependencies | None = None,
) -> dict[str, Any]:
    deps = dependencies or production_child_dependencies()
    deps.entry_gate()
    deps.readiness_loader(committed=True)
    context = dict(deps.context_validator("run-science"))
    deps.worktree_validator("run-science")
    admission = dict(deps.exposure_admission())
    delegated = dict(deps.science_delegate())
    return _bounded_child_result(
        "run-science", context, delegated, admission=admission
    )


def service_canary_child() -> dict[str, Any]:
    enforce_entry_temporary_invariants()
    context = validate_launch_context("service-canary")
    seconds = int(os.environ.get("RECON_SERVICE_CANARY_SECONDS", "0"))
    if seconds < 1:
        raise ExecutionLaunchAmendmentError(
            "service canary duration is invalid"
        )
    started_at = datetime.now(timezone.utc)
    monotonic_start = time.monotonic()
    time.sleep(seconds)
    elapsed = time.monotonic() - monotonic_start
    value = {
        "schema_version": "native_v2_recorded_canary_result.v1",
        "package_id": PACKAGE_ID,
        "command": "service-canary",
        "attempt_id": context["attempt_id"],
        "launch_digest": context["launch_digest"],
        "process_id": os.getpid(),
        "parent_process_id": os.getppid(),
        "requested_seconds": seconds,
        "elapsed_seconds": elapsed,
        "started_at_utc": started_at.isoformat(),
        "ended_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    value["child_result_digest"] = digest(value)
    return value


def _terminal_capture(
    *,
    directory: Path,
    launch: Mapping[str, Any],
    dispatch: Mapping[str, Any],
    observation: Mapping[str, Any],
    status: Mapping[str, str],
    artifact_binder: Callable[..., Mapping[str, Any]] = (
        bind_production_artifacts
    ),
) -> dict[str, Any]:
    stdout_path = Path(str(launch["identity"]["stdout_path"]))
    stderr_path = Path(str(launch["identity"]["stderr_path"]))
    if not stdout_path.is_file() or not stderr_path.is_file():
        raise ExecutionLaunchAmendmentError(
            f"terminal service logs are absent:{launch['attempt_id']}"
        )
    observed_pid = int(observation["status"]["ExecMainPID"] or 0)
    terminal_pid = int(status["ExecMainPID"] or 0)
    if observed_pid < 1 and terminal_pid < 1:
        raise ExecutionLaunchAmendmentError(
            "terminal service process ID is absent"
        )
    if observed_pid > 0 and terminal_pid > 0 and observed_pid != terminal_pid:
        raise ExecutionLaunchAmendmentError(
            "terminal service process ID changed"
        )
    code = status["ExecMainCode"]
    capture = {
        "schema_version": "native_v2_terminal_capture.v1",
        "package_id": PACKAGE_ID,
        "attempt_id": launch["attempt_id"],
        "command": launch["command"],
        "launch": copy.deepcopy(dict(launch)),
        "dispatch": copy.deepcopy(dict(dispatch)),
        "observation": copy.deepcopy(dict(observation)),
        "process_id": observed_pid or terminal_pid,
        "actual_start_timestamp": status["ExecMainStartTimestamp"],
        "actual_end_timestamp": status["ExecMainExitTimestamp"],
        "terminal_status": {
            "load_state": status["LoadState"],
            "active_state": status["ActiveState"],
            "sub_state": status["SubState"],
            "result": status["Result"],
            "exec_main_code": code,
            "exec_main_status": status["ExecMainStatus"],
            "exit_status": (
                int(status["ExecMainStatus"]) if code == "1" else None
            ),
            "signal_status": (
                int(status["ExecMainStatus"]) if code != "1" else None
            ),
            "runtime_max_usec": status["RuntimeMaxUSec"],
            "invocation_id": status["InvocationID"],
        },
        "stdout_log": {
            "path": str(stdout_path),
            "size": stdout_path.stat().st_size,
            "sha256": sha256_file(stdout_path),
        },
        "stderr_log": {
            "path": str(stderr_path),
            "size": stderr_path.stat().st_size,
            "sha256": sha256_file(stderr_path),
        },
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    if stdout_path.stat().st_size:
        child = json.loads(stdout_path.read_text(encoding="utf-8"))
        verify_self_digest(
            child, "child_result_digest", label="service child result"
        )
        if (
            child.get("attempt_id") != launch["attempt_id"]
            or child.get("command") != launch["command"]
            or child.get("launch_digest") != launch["launch_digest"]
        ):
            raise ExecutionLaunchAmendmentError(
                "service child result identity changed"
            )
        capture["child_result"] = child
    if (
        capture["terminal_status"]["exit_status"] == 0
        and launch["command"] in PRODUCTION_COMMANDS
    ):
        capture["artifact_binding"] = dict(artifact_binder(
            launch["command"], require_git_commit=False
        ))
    capture["terminal_capture_digest"] = digest(capture)
    atomic_json(directory / "terminal.json", capture)
    return capture


def cleanup_retained_service(
    service_name: str,
    *,
    runner: Callable[
        [Sequence[str]], subprocess.CompletedProcess
    ] = _completed_process,
) -> dict[str, Any]:
    actions = []
    for action in ("stop", "reset-failed"):
        argv = ("systemctl", "--user", action, service_name)
        result = runner(argv)
        actions.append({
            "action": action,
            "argv": list(argv),
            "returncode": int(result.returncode),
            "stdout": str(result.stdout),
            "stderr": str(result.stderr),
        })
    value = {
        "schema_version": "native_v2_service_cleanup.v1",
        "package_id": PACKAGE_ID,
        "service_name": service_name,
        "actions": actions,
        "completed": all(
            item["returncode"] == 0 for item in actions
        ),
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    value["cleanup_digest"] = digest(value)
    return value


def _persist_repository_terminal_record(
    final: Mapping[str, Any],
) -> Path:
    command = str(final["command"])
    if command == "service-canary":
        relative = SERVICE_CANARY_RECORD_PATH
    elif command in PRODUCTION_COMMANDS:
        relative = production_record_path(
            command, str(final["attempt_id"])
        )
    else:
        raise ExecutionLaunchAmendmentError(
            f"invalid terminal record command:{command}"
        )
    atomic_json(ROOT / relative, final)
    if (
        command == "run-science"
        and final["terminal_status"]["exit_status"] == 0
    ):
        result_binding = {
            "schema_version": "native_v2_outcome_result_binding.v1",
            "package_id": PACKAGE_ID,
            "attempt_id": final["attempt_id"],
            "launch_digest": final["launch"]["launch_digest"],
            "terminal_record": {
                "path": relative.as_posix(),
                "digest": final["final_record_digest"],
            },
            "scientific_result": final["artifact_binding"][
                "scientific_result"
            ],
        }
        result_binding["outcome_result_binding_digest"] = digest(
            result_binding
        )
        atomic_json(ROOT / OUTCOME_RESULT_BINDING_PATH, result_binding)
    return relative


def poll_service_attempt(
    attempt_id: str,
    *,
    attempt_root: Path | None = None,
    status_reader: Callable[[str], Mapping[str, str]] = _systemctl_show,
    cleanup_runner: Callable[
        [Sequence[str]], subprocess.CompletedProcess
    ] = _completed_process,
    readiness_validator: Callable[[str], Mapping[str, Any]] | None = None,
    record_persister: Callable[[Mapping[str, Any]], Path] = (
        _persist_repository_terminal_record
    ),
    artifact_binder: Callable[..., Mapping[str, Any]] = (
        bind_production_artifacts
    ),
) -> dict[str, Any]:
    if not _ATTEMPT_ID.fullmatch(attempt_id):
        raise ExecutionLaunchAmendmentError("invalid poll attempt ID")
    root = attempt_root or service_attempt_root()
    directory = root / attempt_id
    launch = _load_external(
        directory / "launch.json", "launch_record_digest"
    )
    if readiness_validator is not None:
        readiness_validator(str(launch["command"]))
    elif launch["command"] == "service-canary":
        load_and_verify_launch_readiness(committed=True)
    else:
        load_and_verify_final_readiness(committed=True)
    final_path = directory / "final.json"
    if final_path.is_file():
        final = _load_external(final_path, "final_record_digest")
        record_persister(final)
        return final
    dispatch = _load_external(
        directory / "dispatch.json", "dispatch_digest"
    )
    observation = _load_external(
        directory / "observation.json", "observation_digest"
    )
    terminal_path = directory / "terminal.json"
    if terminal_path.is_file():
        capture = _load_external(
            terminal_path, "terminal_capture_digest"
        )
    else:
        status = dict(status_reader(str(launch["service_name"])))
        if not _service_terminal(status):
            return {
                "attempt_id": attempt_id,
                "terminal": False,
                "status": status,
            }
        capture = _terminal_capture(
            directory=directory,
            launch=launch,
            dispatch=dispatch,
            observation=observation,
            status=status,
            artifact_binder=artifact_binder,
        )
    cleanup_path = directory / "cleanup.json"
    if cleanup_path.is_file():
        cleanup = _load_external(cleanup_path, "cleanup_digest")
    else:
        cleanup = cleanup_retained_service(
            str(launch["service_name"]), runner=cleanup_runner
        )
        atomic_json(cleanup_path, cleanup)
    if cleanup.get("completed") is not True:
        raise ExecutionLaunchAmendmentError(
            f"service cleanup failed:{attempt_id}"
        )
    final = {
        "schema_version": "native_v2_terminal_service_record.v1",
        "package_id": PACKAGE_ID,
        "attempt_id": attempt_id,
        "command": launch["command"],
        **{
            key: copy.deepcopy(item)
            for key, item in capture.items()
            if key not in {
                "schema_version",
                "package_id",
                "terminal_capture_digest",
            }
        },
        "terminal_capture_digest": capture[
            "terminal_capture_digest"
        ],
        "cleanup": cleanup,
        "terminal": True,
        "finalized_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    final["final_record_digest"] = digest(final)
    atomic_json(final_path, final)
    record_persister(final)
    return final


def _print(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    freeze = commands.add_parser("freeze-manifests")
    freeze.add_argument("--source-commit", required=True)
    commands.add_parser("verify-launch-readiness")
    commands.add_parser("verify-final-readiness")
    launch = commands.add_parser("launch-service")
    launch.add_argument(
        "--command",
        dest="service_command",
        choices=PUBLIC_CHILD_COMMANDS,
        required=True,
    )
    launch.add_argument("--canary-seconds", type=int)
    poll = commands.add_parser("poll-service")
    poll.add_argument("--attempt-id", required=True)
    commands.add_parser("run-exposure")
    commands.add_parser("run-science")
    commands.add_parser("service-canary")
    args = parser.parse_args(argv)
    if args.command == "freeze-manifests":
        value = freeze_package_manifests(args.source_commit)
    elif args.command == "verify-launch-readiness":
        value = run_launch_readiness()
    elif args.command == "verify-final-readiness":
        value = run_final_readiness()
    elif args.command == "launch-service":
        value = launch_service_attempt(
            args.service_command,
            canary_seconds=args.canary_seconds,
        )
    elif args.command == "poll-service":
        value = poll_service_attempt(args.attempt_id)
    elif args.command == "run-exposure":
        value = run_exposure_child()
    elif args.command == "run-science":
        value = run_science_child()
    elif args.command == "service-canary":
        value = service_canary_child()
    else:  # pragma: no cover
        raise AssertionError(args.command)
    _print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
