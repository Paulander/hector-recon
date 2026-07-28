"""Data-free outer repair for native V2 process readiness.

The prior process-resilient package remains immutable.  This module fixes its
outer verification, admission, temporary-file, outcome-accounting, and
production-service boundaries without changing any scientific mechanism.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
from typing import Any, Callable, Mapping, MutableMapping, Sequence
import uuid

import chess

from recon_lite import FrameContext, FrameKind

from . import (
    native_v2_process_resilient_execution_reclosure as previous,
)
from .native_prospective_evidence_authority_v2_lab import (
    V2LaboratoryRegistry,
)


driver = previous.driver
frozen = previous.frozen
stopped_adapter = previous.stopped_adapter
ROOT = previous.ROOT
PACKAGE_ID = "native_v2_process_readiness_repair.v1"
MODULE_PATH = (
    "recon_lite_chess.autogrowth.native_v2_process_readiness_repair"
)
STARTING_HEAD = "f9f0afde10b7ad2bf6ad817bd04c2d47fefabb74"
ACCEPTED_COHORT_DIGEST = previous.ACCEPTED_COHORT_DIGEST
EXPANDED_PACKAGE_MAP_DIGEST = previous.EXPANDED_PACKAGE_MAP_DIGEST
ARMS = tuple(previous.ARMS)
SEED_COUNT = previous.SEED_COUNT
UNIT_COUNT = previous.UNIT_COUNT
ROW_COUNT = previous.ROW_COUNT
MIN_TARGET_OPPORTUNITIES = previous.MIN_TARGET_OPPORTUNITIES
MIN_QUALIFYING_SEEDS = previous.MIN_QUALIFYING_SEEDS
DETERMINISTIC_ENV = copy.deepcopy(previous.DETERMINISTIC_ENV)
CANARY_DURATION_SECONDS = 1085
_BASE_JOURNAL_GLOBALS = driver.DurableHashJournal.append.__globals__
_JOURNAL_SCHEMA = _BASE_JOURNAL_GLOBALS["JOURNAL_SCHEMA"]
_INJECTED_HARNESS_FAILURE = _BASE_JOURNAL_GLOBALS[
    "InjectedHarnessFailure"
]

PACKAGE_DIR = Path(
    "reports/autogrowth/native_authority/v2_process_readiness_repair"
)
SOURCE_MANIFEST_PATH = PACKAGE_DIR / "source_manifest.json"
ARTIFACT_BINDING_PATH = PACKAGE_DIR / "artifact_binding_manifest.json"
LAUNCH_READINESS_PATH = PACKAGE_DIR / "launch_readiness.json"
LAUNCH_READINESS_FAILURE_PATH = PACKAGE_DIR / "launch_readiness_failure.json"
SERVICE_CANARY_RECORD_PATH = PACKAGE_DIR / "service_canary_record.json"
READINESS_PATH = PACKAGE_DIR / "readiness.json"
READINESS_FAILURE_PATH = PACKAGE_DIR / "readiness_failure.json"
EXPOSURE_JOURNAL_DIR = PACKAGE_DIR / "exposure_journal"
EXPOSURE_PATH = PACKAGE_DIR / "preoutcome_exposure.json"
EXECUTION_MANIFEST_PATH = PACKAGE_DIR / "execution_manifest.json"
EXPOSURE_COMPLETION_PATH = PACKAGE_DIR / "exposure_completion.json"
EXPOSURE_FAILURE_PATH = PACKAGE_DIR / "exposure_failure.json"
SCIENCE_STARTED_PATH = PACKAGE_DIR / "science_started.json"
SCIENCE_JOURNAL_DIR = PACKAGE_DIR / "science_journal"
SCIENCE_CARRIER_DIR = PACKAGE_DIR / "science_carrier"
RESULT_PATH = PACKAGE_DIR / "canonical_result.json.gz"
SCIENCE_FAILURE_PATH = PACKAGE_DIR / "science_failure.json"

SOURCE_FILES = (
    "src/recon_lite_chess/autogrowth/"
    "native_v2_process_readiness_repair.py",
    "tests/autogrowth/test_native_v2_process_readiness_repair.py",
    "docs/autogrowth/"
    "NATIVE_V2_PROCESS_READINESS_REPAIR_PREREGISTRATION_20260728.md",
)
PUBLIC_CHILD_COMMANDS = (
    "run-exposure",
    "run-science",
    "service-canary",
)
ATOMIC_SUFFIX = ".native-v2-process-readiness-repair.atomic.tmp"
SERVICE_PREFIX = "recon-v2-process-readiness-repair"


class ProcessReadinessRepairError(RuntimeError):
    """One frozen process boundary changed."""


class InjectedAtomicInterruption(RuntimeError):
    """Test-only interruption after durable write and before rename."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def pretty_json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            value.update(chunk)
    return value.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProcessReadinessRepairError(f"expected JSON object:{path}")
    return value


def verify_self_digest(
    value: Mapping[str, Any], key: str, *, label: str
) -> str:
    observed = digest({name: item for name, item in value.items() if name != key})
    if value.get(key) != observed:
        raise ProcessReadinessRepairError(f"{label} self-digest mismatch")
    return observed


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def require_committed_artifact(relative: Path) -> dict[str, Any]:
    path = ROOT / relative
    if not path.is_file():
        raise ProcessReadinessRepairError(
            f"required committed artifact is absent:{relative}"
        )
    if subprocess.run(
        ["git", "cat-file", "-e", f"HEAD:{relative.as_posix()}"],
        cwd=ROOT,
        check=False,
    ).returncode != 0:
        raise ProcessReadinessRepairError(
            f"required artifact is not committed:{relative}"
        )
    committed = subprocess.check_output(
        ["git", "show", f"HEAD:{relative.as_posix()}"], cwd=ROOT
    )
    current = path.read_bytes()
    if current != committed:
        raise ProcessReadinessRepairError(
            f"required artifact differs from HEAD:{relative}"
        )
    return {
        "path": relative.as_posix(),
        "size": len(current),
        "sha256": sha256_bytes(current),
    }


def atomic_temporary_path(path: Path) -> Path:
    return path.with_name(f".{path.name}{ATOMIC_SUFFIX}")


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_bytes(
    path: Path,
    payload: bytes,
    *,
    after_fsync: Callable[[Path], None] | None = None,
) -> dict[str, Any]:
    """Write exactly once, or recover the one exact fsynced temporary."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = atomic_temporary_path(path)
    if path.exists():
        if temporary.exists():
            raise ProcessReadinessRepairError(
                f"atomic target and temporary both exist:{temporary}"
            )
        if path.read_bytes() != payload:
            raise ProcessReadinessRepairError(
                f"divergent existing atomic target:{path}"
            )
        return {"created": False, "recovered": False}
    if temporary.exists():
        if temporary.read_bytes() != payload:
            raise ProcessReadinessRepairError(
                f"divergent interrupted atomic temporary:{temporary}"
            )
        os.replace(temporary, path)
        _fsync_directory(path.parent)
        return {"created": False, "recovered": True}
    with temporary.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    if after_fsync is not None:
        after_fsync(temporary)
    os.replace(temporary, path)
    _fsync_directory(path.parent)
    return {"created": True, "recovered": False}


def atomic_json(
    path: Path,
    value: Mapping[str, Any],
    *,
    after_fsync: Callable[[Path], None] | None = None,
) -> dict[str, Any]:
    return atomic_bytes(
        path, pretty_json_bytes(value), after_fsync=after_fsync
    )


_EXPOSURE_RECORD = re.compile(
    r"^\d{6}_(?:PREPARED|COMMITTED)_\d{3}_[ABC]_seed-\d{2}\.json$"
)
_SCIENCE_RECORD = re.compile(
    r"^\d{6}_(?:PREPARED|OUTCOME_ACCESSED|"
    r"TRI_ARM_ROW_COMMITTED|COMMITTED|FAILED)\.json$"
)


def is_recognized_package_temporary(path: Path) -> bool:
    try:
        relative = path.resolve().relative_to((ROOT / PACKAGE_DIR).resolve())
    except ValueError:
        return False
    name = relative.name
    if not name.startswith(".") or not name.endswith(ATOMIC_SUFFIX):
        return False
    target_name = name[1:-len(ATOMIC_SUFFIX)]
    parent = relative.parent
    fixed_targets = {
        item.name
        for item in (
            SOURCE_MANIFEST_PATH,
            ARTIFACT_BINDING_PATH,
            LAUNCH_READINESS_PATH,
            LAUNCH_READINESS_FAILURE_PATH,
            SERVICE_CANARY_RECORD_PATH,
            READINESS_PATH,
            READINESS_FAILURE_PATH,
            EXPOSURE_PATH,
            EXECUTION_MANIFEST_PATH,
            EXPOSURE_COMPLETION_PATH,
            EXPOSURE_FAILURE_PATH,
            SCIENCE_STARTED_PATH,
            RESULT_PATH,
            SCIENCE_FAILURE_PATH,
        )
        if item.parent == PACKAGE_DIR / parent
    }
    if target_name in fixed_targets:
        return True
    if parent == EXPOSURE_JOURNAL_DIR.relative_to(PACKAGE_DIR):
        return bool(_EXPOSURE_RECORD.fullmatch(target_name))
    if parent == SCIENCE_JOURNAL_DIR.relative_to(PACKAGE_DIR):
        return bool(_SCIENCE_RECORD.fullmatch(target_name))
    if str(parent).startswith(str(SCIENCE_CARRIER_DIR.relative_to(PACKAGE_DIR))):
        return bool(
            target_name.endswith(".json")
            or target_name in {"A.pkl.gz", "B.pkl.gz", "C.pkl.gz"}
        )
    return False


def _require_clean_worktree(*, allow_runtime: bool = False) -> None:
    rows = _git("status", "--porcelain=v1").splitlines()
    if not allow_runtime:
        if rows:
            raise ProcessReadinessRepairError(f"worktree is not clean:{rows}")
        return
    allowed_roots = (
        EXPOSURE_JOURNAL_DIR.as_posix(),
        EXPOSURE_PATH.as_posix(),
        EXECUTION_MANIFEST_PATH.as_posix(),
        EXPOSURE_COMPLETION_PATH.as_posix(),
        EXPOSURE_FAILURE_PATH.as_posix(),
        SCIENCE_STARTED_PATH.as_posix(),
        SCIENCE_JOURNAL_DIR.as_posix(),
        SCIENCE_CARRIER_DIR.as_posix(),
        RESULT_PATH.as_posix(),
        SCIENCE_FAILURE_PATH.as_posix(),
    )
    unexpected = []
    for row in rows:
        candidate_text = row[3:].strip()
        candidate = ROOT / candidate_text
        if any(candidate_text.startswith(root) for root in allowed_roots):
            if candidate.name.startswith(".") and not (
                is_recognized_package_temporary(candidate)
            ):
                unexpected.append(row)
            continue
        unexpected.append(row)
    if unexpected:
        raise ProcessReadinessRepairError(
            f"unexpected worktree changes:{unexpected}"
        )
    for root in (
        ROOT / EXPOSURE_JOURNAL_DIR,
        ROOT / SCIENCE_JOURNAL_DIR,
        ROOT / SCIENCE_CARRIER_DIR,
    ):
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.name.startswith("."):
                if not is_recognized_package_temporary(path):
                    raise ProcessReadinessRepairError(
                        f"unrecognized runtime temporary:{path}"
                    )
                continue
            relative = path.relative_to(ROOT / PACKAGE_DIR)
            if (
                relative.parent
                == EXPOSURE_JOURNAL_DIR.relative_to(PACKAGE_DIR)
                and _EXPOSURE_RECORD.fullmatch(path.name)
            ):
                continue
            if (
                relative.parent
                == SCIENCE_JOURNAL_DIR.relative_to(PACKAGE_DIR)
                and _SCIENCE_RECORD.fullmatch(path.name)
            ):
                continue
            if str(relative.parent).startswith(
                str(SCIENCE_CARRIER_DIR.relative_to(PACKAGE_DIR))
            ) and (
                path.name.endswith(".json")
                or path.name in {"A.pkl.gz", "B.pkl.gz", "C.pkl.gz"}
            ):
                continue
            raise ProcessReadinessRepairError(
                f"unrecognized runtime file:{path}"
            )


def prior_file_bindings() -> list[dict[str, Any]]:
    paths = (
        previous.SOURCE_MANIFEST_PATH,
        previous.ARTIFACT_BINDING_PATH,
        previous.READINESS_PATH,
        Path(
            "docs/autogrowth/"
            "NATIVE_V2_PROCESS_RESILIENT_EXECUTION_RECLOSURE_RESULT_20260728.md"
        ),
    )
    return [require_committed_artifact(path) for path in paths]


def verify_runtime_inputs() -> dict[str, Any]:
    """One verifier shared by readiness, exposure, and outcome paths."""

    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", STARTING_HEAD, "HEAD"],
        cwd=ROOT,
        check=False,
    ).returncode != 0:
        raise ProcessReadinessRepairError(
            "required starting commit is not an ancestor"
        )
    previous_package = previous.verify_package_manifests()
    previous_readiness = previous.load_and_verify_readiness(committed=True)
    prior = prior_file_bindings()
    if (
        previous_readiness["cohort_digest"] != ACCEPTED_COHORT_DIGEST
        or previous_readiness["expanded_package_map_digest"]
        != EXPANDED_PACKAGE_MAP_DIGEST
        or previous_readiness["real_exposure_run"] is not False
        or previous_readiness["real_outcome_run"] is not False
        or previous_readiness["outcome_access"]
        != {"count": 0, "event_ids": []}
    ):
        raise ProcessReadinessRepairError(
            "previous process readiness identity changed"
        )
    stopped = previous.verify_stopped_alias_package_bytes()
    package_map = frozen.expanded_package_map()
    if digest(package_map) != EXPANDED_PACKAGE_MAP_DIGEST:
        raise ProcessReadinessRepairError("expanded package map changed")
    value = {
        "starting_head": STARTING_HEAD,
        "previous_package": previous_package,
        "previous_readiness": {
            "sha256": sha256_file(ROOT / previous.READINESS_PATH),
            "digest": previous_readiness["readiness_digest"],
        },
        "prior_files": prior,
        "prior_file_set_digest": digest(prior),
        "stopped_alias_package": stopped,
        "cohort_digest": ACCEPTED_COHORT_DIGEST,
        "expanded_package_map_digest": EXPANDED_PACKAGE_MAP_DIGEST,
        "arms": list(ARMS),
        "seed_count": SEED_COUNT,
        "unit_count": UNIT_COUNT,
        "row_count": ROW_COUNT,
        "minimum_target_opportunities": MIN_TARGET_OPPORTUNITIES,
        "minimum_qualifying_seeds": MIN_QUALIFYING_SEEDS,
        "outcome_access": {"count": 0, "event_ids": []},
    }
    value["runtime_input_digest"] = digest(value)
    return value


@dataclass(frozen=True)
class RuntimeDependencies:
    verify_inputs: Callable[[], Mapping[str, Any]]
    load_previous_readiness: Callable[[], Mapping[str, Any]]
    build_context: Callable[[], Mapping[str, Any]]
    verify_outer_manifest: Callable[[str], Mapping[str, Any]]
    load_ecology: Callable[[], Mapping[str, Any]]
    load_receipt: Callable[[], Mapping[str, Any]]
    expanded_package_map: Callable[[], Mapping[str, str]]
    registry_type: Any = V2LaboratoryRegistry


def production_runtime_dependencies() -> RuntimeDependencies:
    return RuntimeDependencies(
        verify_inputs=verify_runtime_inputs,
        load_previous_readiness=lambda: previous.load_and_verify_readiness(
            committed=True
        ),
        build_context=stopped_adapter.build_readiness_context,
        verify_outer_manifest=driver.verify_outer_manifest,
        load_ecology=lambda: driver._load_json(
            ROOT / driver.ECOLOGY_MANIFEST_PATH
        ),
        load_receipt=lambda: load_json(
            ROOT / stopped_adapter.PREFLIGHT_RECEIPT_PATH
        ),
        expanded_package_map=frozen.expanded_package_map,
    )


def build_real_exposure_runtime(
    dependencies: RuntimeDependencies | None = None,
) -> dict[str, Any]:
    deps = dependencies or production_runtime_dependencies()
    verified_inputs = copy.deepcopy(dict(deps.verify_inputs()))
    readiness = copy.deepcopy(dict(deps.load_previous_readiness()))
    context = dict(deps.build_context())
    identity = copy.deepcopy(dict(deps.verify_outer_manifest(
        "process-readiness-repair runtime"
    )))
    ecology = copy.deepcopy(dict(deps.load_ecology()))
    receipt = copy.deepcopy(dict(deps.load_receipt()))
    package_hashes = dict(deps.expanded_package_map())
    if digest(package_hashes) != EXPANDED_PACKAGE_MAP_DIGEST:
        raise ProcessReadinessRepairError("runtime package map changed")
    row_order = tuple(
        str(row["row_id"]) for row in driver.ecology_rows(ecology, "suffix")
    )
    registries = {}
    for arm in ARMS:
        payloads = {}
        rows = {}
        for ordinal in range(SEED_COUNT):
            organism_id = f"seed-{ordinal:02d}"
            payloads[organism_id] = context["restored"][
                (ordinal, arm)
            ].dumps()
            rows[organism_id] = driver._suffix_registered_rows(
                ecology, arm, ordinal
            )
        run_identity = digest({
            "experiment_id": driver.EXPERIMENT_ID,
            "phase": "preoutcome_exposure",
            "arm": arm,
            "outer_manifest_sha256": identity["outer_sha256"],
        })
        registry = deps.registry_type.freeze(
            payloads,
            exposure_rows=rows,
            row_order=row_order,
            run_identity=run_identity,
            package_hashes=package_hashes,
        )
        registries[arm] = {
            "registry": registry,
            "payloads": payloads,
            "rows": rows,
            "run_identity": run_identity,
        }
    return {
        **context,
        "verified_inputs": verified_inputs,
        "readiness": readiness,
        "identity": identity,
        "ecology": ecology,
        "receipt": receipt,
        "package_hashes": package_hashes,
        "row_order": row_order,
        "registries": registries,
    }


class RepairExposureUnitJournal(previous.ExposureUnitJournal):
    def append(
        self,
        kind: str,
        *,
        unit_index: int,
        unit_id: str,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        if kind not in {"PREPARED", "COMMITTED"}:
            raise ProcessReadinessRepairError(
                f"invalid exposure record:{kind}"
            )
        rows = self.records()
        unsigned = {
            "schema_version": "native_v2_exposure_unit_journal.v1",
            "record_index": len(rows),
            "previous_record_digest": (
                rows[-1]["record_digest"] if rows else "GENESIS"
            ),
            "kind": kind,
            "unit_index": int(unit_index),
            "unit_id": str(unit_id),
            "payload": copy.deepcopy(dict(payload)),
        }
        row = {**unsigned, "record_digest": digest(unsigned)}
        name = (
            f"{len(rows):06d}_{kind}_{int(unit_index):03d}_"
            f"{str(unit_id).replace('/', '_')}.json"
        )
        atomic_json(self.root / name, row)
        return row


def build_execution_manifest(
    runtime: Mapping[str, Any],
    exposure: Mapping[str, Any],
    exposure_sha256: str,
    *,
    launch_readiness: Mapping[str, Any],
) -> dict[str, Any]:
    if exposure["outcome_access"] != {"count": 0, "event_ids": []}:
        raise ProcessReadinessRepairError("exposure opened an outcome")
    value = {
        "schema_version": "native_v2_process_readiness_execution.v1",
        "package_id": PACKAGE_ID,
        "experiment_id": driver.EXPERIMENT_ID,
        "source_tree_identity": {
            "source_freeze_commit": runtime["identity"][
                "source_freeze_commit"
            ],
            "source_runtime_digest": runtime["identity"][
                "source_runtime_digest"
            ],
        },
        "experiment_package_identity": {
            "outer_manifest_sha256": runtime["identity"]["outer_sha256"],
            "expanded_laboratory_package_digest": digest(
                runtime["package_hashes"]
            ),
        },
        "repair_package": {
            "source_manifest_sha256": sha256_file(
                ROOT / SOURCE_MANIFEST_PATH
            ),
            "artifact_binding_sha256": sha256_file(
                ROOT / ARTIFACT_BINDING_PATH
            ),
            "launch_readiness_sha256": sha256_file(
                ROOT / LAUNCH_READINESS_PATH
            ),
            "launch_readiness_digest": launch_readiness[
                "launch_readiness_digest"
            ],
        },
        "previous_process_readiness": {
            "sha256": sha256_file(ROOT / previous.READINESS_PATH),
            "digest": runtime["readiness"]["readiness_digest"],
        },
        "exposure_artifact": {
            "path": EXPOSURE_PATH.as_posix(),
            "sha256": exposure_sha256,
            "digest": exposure["exposure_digest"],
        },
        "parity_digest": exposure["parity_digest"],
        "qualification_digest": exposure["qualification_digest"],
        "qualifying_seed_count": exposure["qualifying_seed_count"],
        "required_qualifying_seed_count": exposure[
            "required_qualifying_seed_count"
        ],
        "admitted": exposure["admitted"],
        "zero_outcome_read_result": copy.deepcopy(
            exposure["outcome_access"]
        ),
        "complete_snapshot_identity": copy.deepcopy(
            exposure["complete_snapshot_identity"]
        ),
        "global_preflight_receipt_digest": exposure[
            "global_preflight_receipt"
        ]["receipt_digest"],
    }
    value["execution_manifest_digest"] = digest(value)
    return value


def finalize_exact_artifacts(
    *,
    exposure: Mapping[str, Any],
    execution: Mapping[str, Any],
    restart_plan: Mapping[str, Any],
    interrupt: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    hook = interrupt or (lambda _stage: None)
    exposure_payload = pretty_json_bytes(exposure)
    execution_payload = pretty_json_bytes(execution)
    atomic_bytes(ROOT / EXPOSURE_PATH, exposure_payload)
    hook("after_exposure")
    atomic_bytes(ROOT / EXECUTION_MANIFEST_PATH, execution_payload)
    hook("after_execution")
    marker = {
        "schema_version": "native_v2_process_readiness_completion.v1",
        "package_id": PACKAGE_ID,
        "experiment_id": driver.EXPERIMENT_ID,
        "unit_count": UNIT_COUNT,
        "exposure_journal_chain_digest": restart_plan[
            "journal_chain_digest"
        ],
        "exposure_recomputation_count": restart_plan[
            "recomputation_count"
        ],
        "exposure": {
            "path": EXPOSURE_PATH.as_posix(),
            "sha256": sha256_bytes(exposure_payload),
            "digest": exposure["exposure_digest"],
        },
        "execution_manifest": {
            "path": EXECUTION_MANIFEST_PATH.as_posix(),
            "sha256": sha256_bytes(execution_payload),
            "digest": execution["execution_manifest_digest"],
        },
        "outcome_access": {"count": 0, "event_ids": []},
    }
    marker["completion_digest"] = digest(marker)
    atomic_json(ROOT / EXPOSURE_COMPLETION_PATH, marker)
    hook("after_completion")
    return {
        "exposure": copy.deepcopy(dict(exposure)),
        "execution_manifest": copy.deepcopy(dict(execution)),
        "completion": marker,
    }


def load_and_verify_launch_readiness(*, committed: bool) -> dict[str, Any]:
    if committed:
        require_committed_artifact(LAUNCH_READINESS_PATH)
    value = load_json(ROOT / LAUNCH_READINESS_PATH)
    verify_self_digest(
        value, "launch_readiness_digest", label="launch readiness"
    )
    if (
        value.get("cohort_digest") != ACCEPTED_COHORT_DIGEST
        or value.get("expanded_package_map_digest")
        != EXPANDED_PACKAGE_MAP_DIGEST
        or value.get("real_exposure_run") is not False
        or value.get("real_outcome_run") is not False
        or value.get("outcome_access")
        != {"count": 0, "event_ids": []}
    ):
        raise ProcessReadinessRepairError("launch readiness gate changed")
    return value


def run_exposure() -> dict[str, Any]:
    _require_clean_worktree(allow_runtime=True)
    if (ROOT / EXPOSURE_FAILURE_PATH).exists():
        raise ProcessReadinessRepairError("exposure has a terminal failure")
    verify_package_manifests()
    launch_readiness = load_and_verify_launch_readiness(committed=True)
    runtime = build_real_exposure_runtime()
    bindings = previous.production_unit_bindings(runtime)
    journal = RepairExposureUnitJournal(ROOT / EXPOSURE_JOURNAL_DIR)
    try:
        execution = previous.execute_resumable_units(
            bindings=bindings,
            journal=journal,
            compute_unit=lambda binding: previous.compute_production_unit(
                binding, runtime
            ),
        )
        exposure = previous.assemble_production_exposure(
            runtime, execution["unit_results"]
        )
        exposure_sha = sha256_bytes(pretty_json_bytes(exposure))
        execution_manifest = build_execution_manifest(
            runtime,
            exposure,
            exposure_sha,
            launch_readiness=launch_readiness,
        )
        return finalize_exact_artifacts(
            exposure=exposure,
            execution=execution_manifest,
            restart_plan=execution["restart_plan"],
        )
    except Exception as exc:
        record_failure(EXPOSURE_FAILURE_PATH, "run-exposure", exc)
        raise


def _validate_completion_identity(
    exposure: Mapping[str, Any],
    execution: Mapping[str, Any],
    completion: Mapping[str, Any],
) -> None:
    verify_self_digest(exposure, "exposure_digest", label="exposure")
    verify_self_digest(
        execution,
        "execution_manifest_digest",
        label="execution manifest",
    )
    verify_self_digest(
        completion, "completion_digest", label="exposure completion"
    )
    if (
        completion.get("schema_version")
        != "native_v2_process_readiness_completion.v1"
        or completion.get("package_id") != PACKAGE_ID
        or completion.get("experiment_id") != driver.EXPERIMENT_ID
        or completion.get("unit_count") != UNIT_COUNT
        or completion.get("outcome_access")
        != {"count": 0, "event_ids": []}
        or exposure.get("admitted") is not True
        or execution.get("admitted") is not True
        or exposure.get("outcome_access")
        != {"count": 0, "event_ids": []}
        or exposure.get("registry_package_hash")
        != EXPANDED_PACKAGE_MAP_DIGEST
    ):
        raise ProcessReadinessRepairError(
            "completed exposure identity/gate changed"
        )


def validate_exposure_journal_admission(
    *,
    runtime: Mapping[str, Any],
    launch_readiness: Mapping[str, Any],
    journal: RepairExposureUnitJournal,
    exposure_bytes: bytes,
    execution_bytes: bytes,
    completion: Mapping[str, Any],
    expected_unit_count: int = UNIT_COUNT,
    bindings_builder: Callable[
        [Mapping[str, Any]], Sequence[Mapping[str, Any]]
    ] = previous.production_unit_bindings,
    exposure_builder: Callable[
        [Mapping[str, Any], Sequence[Mapping[str, Any]]],
        Mapping[str, Any],
    ] = previous.assemble_production_exposure,
    execution_builder: Callable[..., Mapping[str, Any]] = (
        build_execution_manifest
    ),
) -> dict[str, Any]:
    bindings = tuple(bindings_builder(runtime))
    plan = journal.analyze(bindings)
    if (
        plan["committed_unit_count"] != expected_unit_count
        or plan["next_unit_index"] is not None
        or plan["dangling_prepared_unit_index"] is not None
        or plan["dangling_prepared_attempt_count"] != 0
        or plan["committed_unit_indices"]
        != list(range(expected_unit_count))
    ):
        raise ProcessReadinessRepairError(
            "exposure journal is not exactly the required committed units"
        )
    if (
        completion.get("unit_count") != plan["committed_unit_count"]
        or completion.get("exposure_journal_chain_digest")
        != plan["journal_chain_digest"]
        or completion.get("exposure_recomputation_count")
        != plan["recomputation_count"]
    ):
        raise ProcessReadinessRepairError(
            "completion/journal counts or chain changed"
        )
    records = journal.records()
    results = [
        row["payload"]["unit_result"]
        for row in records if row["kind"] == "COMMITTED"
    ]
    if len(results) != expected_unit_count:
        raise ProcessReadinessRepairError(
            "committed unit result coverage changed"
        )
    rebuilt_exposure = dict(exposure_builder(runtime, results))
    rebuilt_exposure_bytes = pretty_json_bytes(rebuilt_exposure)
    rebuilt_execution = dict(execution_builder(
        runtime,
        rebuilt_exposure,
        sha256_bytes(rebuilt_exposure_bytes),
        launch_readiness=launch_readiness,
    ))
    rebuilt_execution_bytes = pretty_json_bytes(rebuilt_execution)
    if rebuilt_exposure_bytes != exposure_bytes:
        raise ProcessReadinessRepairError(
            "committed exposure differs from journal reconstruction"
        )
    if rebuilt_execution_bytes != execution_bytes:
        raise ProcessReadinessRepairError(
            "committed execution differs from journal reconstruction"
        )
    return {
        "bindings": bindings,
        "plan": plan,
        "exposure": rebuilt_exposure,
        "execution_manifest": rebuilt_execution,
        "completion": copy.deepcopy(dict(completion)),
        "journal_record_count": len(records),
    }


def validate_completed_exposure(
    *,
    runtime_builder: Callable[[], Mapping[str, Any]] = (
        build_real_exposure_runtime
    ),
) -> dict[str, Any]:
    verify_package_manifests()
    launch_readiness = load_and_verify_launch_readiness(committed=True)
    for path in (
        EXPOSURE_PATH,
        EXECUTION_MANIFEST_PATH,
        EXPOSURE_COMPLETION_PATH,
    ):
        require_committed_artifact(path)
    exposure_bytes = (ROOT / EXPOSURE_PATH).read_bytes()
    execution_bytes = (ROOT / EXECUTION_MANIFEST_PATH).read_bytes()
    exposure = load_json(ROOT / EXPOSURE_PATH)
    execution = load_json(ROOT / EXECUTION_MANIFEST_PATH)
    completion = load_json(ROOT / EXPOSURE_COMPLETION_PATH)
    _validate_completion_identity(exposure, execution, completion)
    if (
        completion["exposure"]["sha256"] != sha256_bytes(exposure_bytes)
        or completion["exposure"]["digest"] != exposure["exposure_digest"]
        or completion["execution_manifest"]["sha256"]
        != sha256_bytes(execution_bytes)
        or completion["execution_manifest"]["digest"]
        != execution["execution_manifest_digest"]
    ):
        raise ProcessReadinessRepairError(
            "completion artifact byte binding changed"
        )
    runtime = dict(runtime_builder())
    admission = validate_exposure_journal_admission(
        runtime=runtime,
        launch_readiness=launch_readiness,
        journal=RepairExposureUnitJournal(ROOT / EXPOSURE_JOURNAL_DIR),
        exposure_bytes=exposure_bytes,
        execution_bytes=execution_bytes,
        completion=completion,
    )
    admission["runtime"] = runtime
    return admission


def science_started_value(
    completed: Mapping[str, Any],
) -> dict[str, Any]:
    value = {
        "schema_version": "native_v2_process_readiness_science_started.v1",
        "package_id": PACKAGE_ID,
        "experiment_id": driver.EXPERIMENT_ID,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "complete_suffix_consumed": True,
        "cohort_digest": ACCEPTED_COHORT_DIGEST,
        "expanded_package_map_digest": EXPANDED_PACKAGE_MAP_DIGEST,
        "exposure_digest": completed["exposure"]["exposure_digest"],
        "execution_manifest_digest": completed["execution_manifest"][
            "execution_manifest_digest"
        ],
        "exposure_completion_digest": completed["completion"][
            "completion_digest"
        ],
    }
    value["science_started_digest"] = digest(value)
    return value


def persist_science_started(
    path: Path, completed: Mapping[str, Any]
) -> dict[str, Any]:
    expected = science_started_value(completed)
    if path.exists():
        value = load_json(path)
        verify_self_digest(
            value, "science_started_digest", label="science started"
        )
        for key in (
            "schema_version",
            "package_id",
            "experiment_id",
            "complete_suffix_consumed",
            "cohort_digest",
            "expanded_package_map_digest",
            "exposure_digest",
            "execution_manifest_digest",
            "exposure_completion_digest",
        ):
            if value.get(key) != expected[key]:
                raise ProcessReadinessRepairError(
                    f"science-started marker changed:{key}"
                )
        return value
    atomic_json(path, expected)
    return expected


def _strict_partial_outcome_prefix(
    records: Sequence[Mapping[str, Any]],
    *,
    expected_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    row_ids = tuple(str(row["row_id"]) for row in expected_rows)
    if len(row_ids) != ROW_COUNT or len(set(row_ids)) != ROW_COUNT:
        raise ProcessReadinessRepairError(
            "canonical outcome plan lacks exact 16 unique rows"
        )
    expected_row_map = {str(row["row_id"]): row for row in expected_rows}
    cursor = 0
    event_ids: list[str] = []
    completed_seeds = []
    active_seed: int | None = None

    def failed_checkpoint(
        row: Mapping[str, Any], *, seed: int, row_count: int
    ) -> dict[str, Any] | None:
        if row["kind"] != "FAILED":
            return None
        if (
            int(row["seed_ordinal"]) != seed
            or row["payload"].get("outcome_access")
            != {"count": len(event_ids), "event_ids": event_ids}
            or cursor != len(records) - 1
        ):
            raise ProcessReadinessRepairError(
                "FAILED checkpoint sequence changed"
            )
        return {
            "event_ids": event_ids,
            "completed_seeds": completed_seeds,
            "active_seed": seed,
            "active_row_count": row_count,
            "failed": True,
            "record_count": len(records),
        }

    for seed in range(SEED_COUNT):
        if cursor == len(records):
            break
        prepared = records[cursor]
        if (
            prepared["kind"] != "PREPARED"
            or int(prepared["seed_ordinal"]) != seed
            or prepared["payload"].get("outcome_access")
            != {"count": len(event_ids), "event_ids": event_ids}
        ):
            raise ProcessReadinessRepairError(
                f"canonical PREPARED sequence changed:{seed}"
            )
        active_seed = seed
        cursor += 1
        row_count = 0
        for row_id in row_ids:
            for arm in ARMS:
                if cursor == len(records):
                    return {
                        "event_ids": event_ids,
                        "completed_seeds": completed_seeds,
                        "active_seed": active_seed,
                        "active_row_count": row_count,
                        "record_count": len(records),
                    }
                row = records[cursor]
                failure = failed_checkpoint(
                    row, seed=seed, row_count=row_count
                )
                if failure is not None:
                    return failure
                expected_event_id = f"seed-{seed:02d}:{row_id}:{arm}"
                expected_transition = str(
                    expected_row_map[row_id]["arms"][arm]["transition_id"]
                )
                if (
                    row["kind"] != "OUTCOME_ACCESSED"
                    or int(row["seed_ordinal"]) != seed
                    or row["payload"].get("event_id") != expected_event_id
                    or row["payload"].get("transition_id")
                    != expected_transition
                ):
                    raise ProcessReadinessRepairError(
                        "canonical outcome interaction identity/order changed"
                    )
                event_ids.append(expected_event_id)
                if row["payload"].get("next_guard_manifest") != {
                    "count": len(event_ids),
                    "event_ids": event_ids,
                }:
                    raise ProcessReadinessRepairError(
                        "canonical outcome counter changed"
                    )
                cursor += 1
            if cursor == len(records):
                return {
                    "event_ids": event_ids,
                    "completed_seeds": completed_seeds,
                    "active_seed": active_seed,
                    "active_row_count": row_count,
                    "record_count": len(records),
                }
            row_commit = records[cursor]
            failure = failed_checkpoint(
                row_commit, seed=seed, row_count=row_count
            )
            if failure is not None:
                return failure
            if (
                row_commit["kind"] != "TRI_ARM_ROW_COMMITTED"
                or int(row_commit["seed_ordinal"]) != seed
                or row_commit["payload"].get("row_id") != row_id
                or row_commit["payload"].get("outcome_access")
                != {"count": len(event_ids), "event_ids": event_ids}
            ):
                raise ProcessReadinessRepairError(
                    "canonical row checkpoint changed"
                )
            cursor += 1
            row_count += 1
        if cursor == len(records):
            return {
                "event_ids": event_ids,
                "completed_seeds": completed_seeds,
                "active_seed": active_seed,
                "active_row_count": row_count,
                "record_count": len(records),
            }
        final = records[cursor]
        failure = failed_checkpoint(
            final, seed=seed, row_count=row_count
        )
        if failure is not None:
            return failure
        if (
            final["kind"] != "COMMITTED"
            or int(final["seed_ordinal"]) != seed
            or final["payload"].get("outcome_access")
            != {"count": len(event_ids), "event_ids": event_ids}
        ):
            raise ProcessReadinessRepairError(
                "canonical seed checkpoint changed"
            )
        driver._validate_seed_journal_sequence(
            records, seed=seed, row_ids=row_ids
        )
        completed_seeds.append(seed)
        active_seed = None
        cursor += 1
    if cursor != len(records):
        raise ProcessReadinessRepairError(
            "foreign science journal suffix"
        )
    return {
        "event_ids": event_ids,
        "completed_seeds": completed_seeds,
        "active_seed": active_seed,
        "active_row_count": 0,
        "record_count": len(records),
    }


def outcome_accounting_from_journal(
    path: Path,
    *,
    expected_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    try:
        journal = driver.DurableHashJournal(path)
        records = journal._records()
        prefix = _strict_partial_outcome_prefix(
            records, expected_rows=expected_rows
        )
        event_ids = prefix["event_ids"]
        value = {
            "status": "known",
            "count": len(event_ids),
            "event_ids": event_ids,
            "canonical_prefix": prefix,
            "journal_record_count": len(records),
            "journal_chain_digest": digest(records),
            "last_valid_record_digest": (
                "GENESIS" if not records else records[-1]["record_hash"]
            ),
        }
    except Exception as exc:
        value = {
            "status": "unknown",
            "count": None,
            "event_ids": None,
            "canonical_prefix": None,
            "journal_record_count": None,
            "journal_chain_digest": None,
            "last_valid_record_digest": None,
            "validation_error_type": type(exc).__name__,
            "validation_error": str(exc),
        }
    value["accounting_digest"] = digest(value)
    return value


class RepairDurableHashJournal(driver.DurableHashJournal):
    def append(
        self, kind: str, *, seed: int, payload: Mapping[str, Any]
    ) -> dict[str, Any]:
        if self.fail_on_kind == kind:
            raise _INJECTED_HARNESS_FAILURE(f"durable_commit:{kind}")
        rows = self._records()
        unsigned = {
            "schema_version": _JOURNAL_SCHEMA,
            "index": len(rows),
            "previous_hash": (
                rows[-1]["record_hash"] if rows else "GENESIS"
            ),
            "kind": kind,
            "seed_ordinal": int(seed),
            "payload": copy.deepcopy(dict(payload)),
        }
        row = {**unsigned, "record_hash": driver.canonical_digest(unsigned)}
        atomic_json(self.root / f"{len(rows):06d}_{kind}.json", row)
        return row


class RepairFreshScientificJournal(driver.FreshScientificJournal):
    def __post_init__(self) -> None:
        self.base = RepairDurableHashJournal(
            self.root, fail_on_kind=self.fail_on_kind
        )

    def commit_row(
        self,
        seed: int,
        row_id: str,
        state: Mapping[str, Any],
        outcome_access: Mapping[str, Any],
    ) -> dict[str, Any]:
        scientific_row = self.adapter.completed_row(row_id)
        row_path = (
            self.carrier_root
            / f"seed-{int(seed):02d}"
            / "rows"
            / f"{row_id}.json"
        )
        atomic_json(row_path, scientific_row)
        payload = row_path.read_bytes()
        binding = {
            "path": driver._bound_path(row_path),
            "sha256": driver.sha256_bytes(payload),
            "size": len(payload),
            "scientific_row_digest": scientific_row[
                "scientific_row_digest"
            ],
        }
        self.row_bindings.append(binding)
        return self.base.commit_row(
            seed,
            row_id,
            {
                **copy.deepcopy(dict(state)),
                "scientific_row_binding": binding,
            },
            outcome_access,
        )

    def _persist_final_snapshots(
        self, seed: int
    ) -> dict[str, dict[str, Any]]:
        codec = driver.V2SnapshotCodec()
        result = {}
        for arm in ARMS:
            wrapper = self.adapter.staged_arms[arm]
            raw = codec.dumps(wrapper)
            compressed = driver.deterministic_gzip(raw)
            path = (
                self.carrier_root
                / f"seed-{int(seed):02d}"
                / "final_snapshots"
                / f"{arm}.pkl.gz"
            )
            atomic_bytes(path, compressed)
            restored = codec.loads(gzip.decompress(path.read_bytes()))
            identity = driver.post_event_semantic_identity(wrapper)
            observed = driver.post_event_semantic_identity(restored)
            if identity != observed:
                raise ProcessReadinessRepairError(
                    f"final snapshot restore mismatch:{seed}:{arm}"
                )
            result[arm] = {
                "path": driver._bound_path(path),
                "raw_sha256": driver.sha256_bytes(raw),
                "raw_size": len(raw),
                "compressed_sha256": driver.sha256_bytes(compressed),
                "compressed_size": len(compressed),
                "semantic_identity": identity,
                "semantic_identity_digest": driver.digest(identity),
            }
        return result

    def commit_seed(
        self,
        seed: int,
        state: Mapping[str, Any],
        outcome_access: Mapping[str, Any],
    ) -> dict[str, Any]:
        snapshots = self._persist_final_snapshots(seed)
        seed_result = self.adapter.seed_result(self.row_bindings)
        unsigned = {
            key: value
            for key, value in seed_result.items()
            if key != "seed_result_digest"
        }
        unsigned["final_snapshots"] = snapshots
        seed_result = {
            **unsigned,
            "seed_result_digest": driver.digest(unsigned),
        }
        path = (
            self.carrier_root
            / f"seed-{int(seed):02d}"
            / "seed_result.json"
        )
        atomic_json(path, seed_result)
        payload = path.read_bytes()
        binding = {
            "path": driver._bound_path(path),
            "sha256": driver.sha256_bytes(payload),
            "size": len(payload),
            "seed_result_digest": seed_result["seed_result_digest"],
            "final_snapshot_bindings": snapshots,
        }
        return self.base.commit_seed(
            seed,
            {
                **copy.deepcopy(dict(state)),
                "scientific_seed_binding": binding,
            },
            outcome_access,
        )


def execute_fresh_seed_atomically(
    *,
    seed_ordinal: int,
    live_arms: MutableMapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    adapter: Any,
    journal_root: Path,
    carrier_root: Path,
    environment: Any,
    preflight_receipt: Mapping[str, Any],
    snapshot_manifest: Mapping[str, Any],
    authorization: Mapping[str, Any],
) -> dict[str, Any]:
    driver.verify_bound_preflight_authorization(
        receipt=preflight_receipt,
        snapshot_manifest=snapshot_manifest,
        authorization=authorization,
    )
    journal = RepairFreshScientificJournal(
        journal_root, carrier_root, adapter
    )
    restored = journal.restored_outcome_guard()
    capability = driver.DurableOutcomeCapability(
        environment=environment,
        journal=journal,
        count=restored.count,
        event_ids=restored.event_ids,
    )
    result = driver.execute_seed_atomically(
        seed=seed_ordinal,
        live_arms=live_arms,
        rows=rows,
        adapter=adapter,
        journal=journal,
        guard=capability,
        preflight_receipt=preflight_receipt,
        snapshot_manifest=snapshot_manifest,
    )
    result["science_journal_chain_digest"] = digest(journal._records())
    return result


def science_restart_plan(
    journal: Any, ordinals: Sequence[int]
) -> dict[str, Any]:
    records = journal._records()
    if any(row["kind"] == "FAILED" for row in records):
        raise ProcessReadinessRepairError(
            "science journal contains FAILED record"
        )
    next_seed = journal.next_seed(tuple(ordinals))
    completed = [
        int(row["seed_ordinal"])
        for row in records if row["kind"] == "COMMITTED"
    ]
    expected = list(map(int, ordinals))[:len(completed)]
    if completed != expected:
        raise ProcessReadinessRepairError(
            "science committed seeds are not a contiguous prefix"
        )
    value = {
        "completed_ordinals": completed,
        "next_unfinished_seed": next_seed,
        "remaining_ordinals": (
            []
            if next_seed is None
            else list(map(int, ordinals))[len(completed):]
        ),
        "journal_chain_digest": digest(records),
    }
    value["restart_plan_digest"] = digest(value)
    return value


def run_science() -> dict[str, Any]:
    _require_clean_worktree(allow_runtime=True)
    if (ROOT / RESULT_PATH).exists():
        raise FileExistsError("canonical result already exists")
    if (ROOT / SCIENCE_FAILURE_PATH).exists():
        raise ProcessReadinessRepairError("science has a terminal failure")
    completed = validate_completed_exposure()
    started = persist_science_started(
        ROOT / SCIENCE_STARTED_PATH, completed
    )
    runtime = completed["runtime"]
    rows: Sequence[Mapping[str, Any]] | None = None
    try:
        environment_value = driver._load_json(
            ROOT / driver.ENVIRONMENT_MANIFEST_PATH
        )
        environment = driver.FrozenTruthfulEnvironment(environment_value)
        rows = driver._suffix_outcome_blind_rows(runtime["ecology"])
        seed_metadata = {
            int(item["ordinal"]): {
                "genome_seed": int(item["genome_seed"]),
                "targets": copy.deepcopy(item["targets"]),
            }
            for item in runtime["prefix"]["results"]
        }
        journal = RepairDurableHashJournal(ROOT / SCIENCE_JOURNAL_DIR)
        plan = science_restart_plan(journal, tuple(range(SEED_COUNT)))
        driver.committed_seed_results(
            journal,
            expected_ordinals=tuple(plan["completed_ordinals"]),
            expected_rows=rows,
            baseline_wrappers=runtime["restored"],
            expected_seed_metadata=seed_metadata,
            environment_manifest=environment_value,
        )
        authorization = completed["exposure"]["preflight_authorization"]
        for ordinal in plan["remaining_ordinals"]:
            live = {
                arm: runtime["restored"][(ordinal, arm)] for arm in ARMS
            }
            adapter = driver.FreshScienceAdapter(
                seed_ordinal=ordinal,
                genome_seed=seed_metadata[ordinal]["genome_seed"],
                targets=seed_metadata[ordinal]["targets"],
                identity_contract=runtime["runtime_manifest"]["metadata"][
                    "per_seed_identity_contracts"
                ][str(ordinal)],
            )
            execute_fresh_seed_atomically(
                seed_ordinal=ordinal,
                live_arms=live,
                rows=rows,
                adapter=adapter,
                journal_root=ROOT / SCIENCE_JOURNAL_DIR,
                carrier_root=ROOT / SCIENCE_CARRIER_DIR,
                environment=environment,
                preflight_receipt=runtime["receipt"],
                snapshot_manifest=runtime["runtime_manifest"],
                authorization=authorization,
            )
        final_journal = RepairDurableHashJournal(ROOT / SCIENCE_JOURNAL_DIR)
        final_plan = science_restart_plan(
            final_journal, tuple(range(SEED_COUNT))
        )
        if final_plan["next_unfinished_seed"] is not None:
            raise ProcessReadinessRepairError(
                "science ended before seed 31"
            )
        seed_results = driver.committed_seed_results(
            final_journal,
            expected_ordinals=tuple(range(SEED_COUNT)),
            expected_rows=rows,
            baseline_wrappers=runtime["restored"],
            expected_seed_metadata=seed_metadata,
            environment_manifest=environment_value,
        )
        adjudication = driver.adjudicate_committed_results(seed_results)
        accounting = outcome_accounting_from_journal(
            ROOT / SCIENCE_JOURNAL_DIR, expected_rows=rows
        )
        if accounting["status"] != "known":
            raise ProcessReadinessRepairError(
                "completed science outcome accounting is unknown"
            )
        value = {
            "schema_version": "native_v2_process_readiness_result.v1",
            "package_id": PACKAGE_ID,
            "experiment_id": driver.EXPERIMENT_ID,
            "science_started_digest": started[
                "science_started_digest"
            ],
            "expanded_package_map_digest": EXPANDED_PACKAGE_MAP_DIGEST,
            "exposure_digest": completed["exposure"]["exposure_digest"],
            "execution_manifest_digest": completed["execution_manifest"][
                "execution_manifest_digest"
            ],
            "all_32_committed": True,
            "restart_plan_at_entry": plan,
            "restart_plan_at_completion": final_plan,
            "seed_result_digests": [
                item["seed_result_digest"] for item in seed_results
            ],
            "recomputed_result_digests": [
                item["recomputed_result_digest"] for item in seed_results
            ],
            "adjudication": adjudication,
            "outcome_accounting": accounting,
            "journal_chain_digest": digest(final_journal._records()),
        }
        value["canonical_result_digest"] = digest(value)
        atomic_bytes(
            ROOT / RESULT_PATH,
            driver.deterministic_gzip(canonical_bytes(value)),
        )
        return value
    except Exception as exc:
        if rows is None:
            ecology = driver._load_json(ROOT / driver.ECOLOGY_MANIFEST_PATH)
            rows = driver._suffix_outcome_blind_rows(ecology)
        record_science_failure(exc, started, expected_rows=rows)
        raise


def record_failure(path: Path, command: str, exc: Exception) -> None:
    target = ROOT / path
    if target.exists():
        return
    value = {
        "schema_version": "native_v2_process_readiness_failure.v1",
        "package_id": PACKAGE_ID,
        "command": command,
        "exception_type": type(exc).__name__,
        "detail": str(exc),
        "parent_argv": list(getattr(sys, "orig_argv", sys.argv)),
        "process_id": os.getpid(),
    }
    value["failure_digest"] = digest(value)
    atomic_json(target, value)


def record_science_failure(
    exc: Exception,
    started: Mapping[str, Any],
    *,
    expected_rows: Sequence[Mapping[str, Any]],
) -> None:
    path = ROOT / SCIENCE_FAILURE_PATH
    if path.exists():
        return
    accounting = outcome_accounting_from_journal(
        ROOT / SCIENCE_JOURNAL_DIR, expected_rows=expected_rows
    )
    value = {
        "schema_version": "native_v2_process_readiness_science_failure.v1",
        "package_id": PACKAGE_ID,
        "command": "run-science",
        "exception_type": type(exc).__name__,
        "detail": str(exc),
        "science_started_digest": started["science_started_digest"],
        "complete_suffix_consumed": True,
        "outcome_accounting": accounting,
        "resume_authorized": False,
        "caught_program_failure_is_terminal": True,
        "parent_argv": list(getattr(sys, "orig_argv", sys.argv)),
        "process_id": os.getpid(),
    }
    value["failure_digest"] = digest(value)
    atomic_json(path, value)


def deterministic_environment(
    extra: Mapping[str, str] | None = None,
) -> dict[str, str]:
    value = {
        str(key): str(item)
        for key, item in sorted(DETERMINISTIC_ENV.items())
    }
    if extra:
        value.update({
            str(key): str(item) for key, item in sorted(extra.items())
        })
    return dict(sorted(value.items()))


def build_public_command(command: str) -> tuple[str, ...]:
    if command not in PUBLIC_CHILD_COMMANDS:
        raise ProcessReadinessRepairError(
            f"unknown service child command:{command}"
        )
    return (sys.executable, "-m", MODULE_PATH, command)


def service_attempt_root() -> Path:
    state = os.environ.get("XDG_STATE_HOME")
    base = Path(state) if state else Path.home() / ".local" / "state"
    return base / "hector-recon-v2-process-readiness-repair" / "attempts"


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
            "systemctl",
            "--user",
            "show",
            service_name,
            "--no-pager",
            *[f"--property={item}" for item in properties],
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ProcessReadinessRepairError(json.dumps({
            "detail": "service status is unavailable",
            "service_name": service_name,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }, sort_keys=True))
    values = {}
    for line in result.stdout.splitlines():
        key, separator, value = line.partition("=")
        if separator:
            values[key] = value
    if set(properties) - set(values):
        raise ProcessReadinessRepairError(
            f"incomplete service status:{service_name}"
        )
    return values


def _service_terminal(status: Mapping[str, str]) -> bool:
    return (
        status["SubState"] in {"exited", "dead", "failed"}
        and bool(status["ExecMainCode"])
    )


def _external_attempt_dirs(
    root: Path | None = None,
) -> tuple[Path, ...]:
    root = service_attempt_root() if root is None else root
    return () if not root.exists() else tuple(sorted(
        item for item in root.iterdir() if item.is_dir()
    ))


def _load_external_record(path: Path, digest_key: str) -> dict[str, Any]:
    value = load_json(path)
    verify_self_digest(value, digest_key, label=str(path))
    return value


def reject_concurrent_matching_run(
    command: str,
    *,
    attempt_root: Path | None = None,
    status_reader: Callable[[str], Mapping[str, str]] = _systemctl_show,
) -> None:
    for directory in _external_attempt_dirs(attempt_root):
        launch_path = directory / "launch.json"
        if not launch_path.is_file() or (directory / "final.json").exists():
            continue
        launch = _load_external_record(launch_path, "launch_digest")
        if launch.get("command") != command:
            continue
        status = status_reader(str(launch["service_name"]))
        if not _service_terminal(status):
            raise ProcessReadinessRepairError(
                f"concurrent matching service:{launch['attempt_id']}"
            )
        raise ProcessReadinessRepairError(
            "terminal matching service must be finalized before a new "
            f"attempt:{launch['attempt_id']}"
        )


def build_service_argv(
    *,
    command: str,
    service_name: str,
    stdout_path: Path,
    stderr_path: Path,
    environment: Mapping[str, str],
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
    values.extend(("--", *build_public_command(command)))
    return tuple(values)


def launch_service_attempt(
    command: str,
    *,
    canary_seconds: int | None = None,
) -> dict[str, Any]:
    if command not in PUBLIC_CHILD_COMMANDS:
        raise ProcessReadinessRepairError(f"invalid service command:{command}")
    if command == "service-canary":
        if canary_seconds is None or canary_seconds < 1:
            raise ProcessReadinessRepairError(
                "service canary duration is absent"
            )
        extra = {"RECON_SERVICE_CANARY_SECONDS": str(canary_seconds)}
    elif canary_seconds is not None:
        raise ProcessReadinessRepairError(
            "duration applies only to service canary"
        )
    else:
        extra = {}
    _require_clean_worktree()
    verify_package_manifests()
    readiness = load_and_verify_launch_readiness(committed=True)
    reject_concurrent_matching_run(command)
    attempt_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        + "-"
        + uuid.uuid4().hex
    )
    service_name = f"{SERVICE_PREFIX}-{command}-{attempt_id}"
    directory = service_attempt_root() / attempt_id
    directory.mkdir(parents=True, exist_ok=False)
    stdout_path = directory / "stdout.log"
    stderr_path = directory / "stderr.log"
    environment = deterministic_environment(extra)
    argv = build_service_argv(
        command=command,
        service_name=service_name,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        environment=environment,
    )
    launch = {
        "schema_version": "native_v2_service_attempt_launch.v1",
        "package_id": PACKAGE_ID,
        "attempt_id": attempt_id,
        "command": command,
        "service_name": service_name,
        "exact_head": _git("rev-parse", "HEAD"),
        "launch_readiness": {
            "path": LAUNCH_READINESS_PATH.as_posix(),
            "sha256": sha256_file(ROOT / LAUNCH_READINESS_PATH),
            "digest": readiness["launch_readiness_digest"],
        },
        "exact_python_argv": list(build_public_command(command)),
        "systemd_argv": list(argv),
        "environment": environment,
        "working_directory": str(ROOT),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "requested_at_utc": datetime.now(timezone.utc).isoformat(),
        "no_shell_transformation": True,
        "no_wall_clock_timeout": True,
        "lawful_restart_requires_new_attempt": True,
    }
    launch["launch_digest"] = digest(launch)
    atomic_json(directory / "launch.json", launch)
    result = subprocess.run(
        list(argv),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    dispatch = {
        "schema_version": "native_v2_service_attempt_dispatch.v1",
        "attempt_id": attempt_id,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "dispatched_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    dispatch["dispatch_digest"] = digest(dispatch)
    atomic_json(directory / "dispatch.json", dispatch)
    if result.returncode != 0:
        raise ProcessReadinessRepairError(
            f"service dispatch failed:{attempt_id}:{result.returncode}"
        )
    observed = None
    for _ in range(60):
        status = _systemctl_show(service_name)
        if status["ExecMainPID"] not in {"", "0"} or _service_terminal(status):
            observed = status
            break
        time.sleep(0.1)
    if observed is None:
        raise ProcessReadinessRepairError(
            f"service PID was not observed:{attempt_id}"
        )
    observation = {
        "schema_version": "native_v2_service_attempt_observation.v1",
        "attempt_id": attempt_id,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": observed,
    }
    observation["observation_digest"] = digest(observation)
    atomic_json(directory / "observation.json", observation)
    return {
        "attempt_id": attempt_id,
        "service_name": service_name,
        "process_id": int(observed["ExecMainPID"] or 0),
        "status": observed,
        "external_attempt_directory": str(directory),
        "launch_digest": launch["launch_digest"],
        "dispatch_digest": dispatch["dispatch_digest"],
    }


def poll_service_attempt(
    attempt_id: str,
    *,
    persist_canary_record: bool,
    attempt_root: Path | None = None,
    status_reader: Callable[[str], Mapping[str, str]] = _systemctl_show,
) -> dict[str, Any]:
    root = service_attempt_root() if attempt_root is None else attempt_root
    directory = root / str(attempt_id)
    existing_final = directory / "final.json"
    if existing_final.is_file():
        final = _load_external_record(existing_final, "final_digest")
        if persist_canary_record:
            if final.get("command") != "service-canary":
                raise ProcessReadinessRepairError(
                    "only a service canary may enter readiness"
                )
            _require_clean_worktree()
            atomic_json(ROOT / SERVICE_CANARY_RECORD_PATH, final)
        return final
    launch = _load_external_record(
        directory / "launch.json", "launch_digest"
    )
    dispatch = _load_external_record(
        directory / "dispatch.json", "dispatch_digest"
    )
    observation = _load_external_record(
        directory / "observation.json", "observation_digest"
    )
    status = dict(status_reader(str(launch["service_name"])))
    if not _service_terminal(status):
        return {
            "attempt_id": attempt_id,
            "terminal": False,
            "status": status,
        }
    stdout_path = Path(str(launch["stdout_path"]))
    stderr_path = Path(str(launch["stderr_path"]))
    if not stdout_path.is_file() or not stderr_path.is_file():
        raise ProcessReadinessRepairError(
            f"terminal service logs are absent:{attempt_id}"
        )
    code = status["ExecMainCode"]
    observed_pid = int(observation["status"]["ExecMainPID"] or 0)
    terminal_pid = int(status["ExecMainPID"] or 0)
    if observed_pid < 1 and terminal_pid < 1:
        raise ProcessReadinessRepairError(
            f"service process ID is absent:{attempt_id}"
        )
    if observed_pid > 0 and terminal_pid > 0 and observed_pid != terminal_pid:
        raise ProcessReadinessRepairError(
            f"service process ID changed:{attempt_id}"
        )
    final = {
        "schema_version": "native_v2_service_attempt_final.v1",
        "package_id": PACKAGE_ID,
        "attempt_id": attempt_id,
        "command": launch["command"],
        "service_name": launch["service_name"],
        "launch": launch,
        "dispatch": dispatch,
        "observation": observation,
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
        "finalized_at_utc": datetime.now(timezone.utc).isoformat(),
        "terminal": True,
    }
    if launch["command"] == "service-canary":
        child = json.loads(stdout_path.read_text(encoding="utf-8"))
        verify_self_digest(child, "canary_digest", label="service canary")
        if (
            child["argv"] != launch["exact_python_argv"]
            or child["working_directory"] != launch["working_directory"]
            or child["environment"] != launch["environment"]
        ):
            raise ProcessReadinessRepairError(
                "service canary child identity changed"
            )
        final["canary_child"] = child
    final["final_digest"] = digest(final)
    final_path = directory / "final.json"
    atomic_json(final_path, final)
    if persist_canary_record:
        if launch["command"] != "service-canary":
            raise ProcessReadinessRepairError(
                "only a service canary may enter readiness"
            )
        _require_clean_worktree()
        atomic_json(ROOT / SERVICE_CANARY_RECORD_PATH, final)
    return final


def service_canary_child() -> dict[str, Any]:
    seconds = int(os.environ.get("RECON_SERVICE_CANARY_SECONDS", "0"))
    if seconds < 1:
        raise ProcessReadinessRepairError(
            "service canary duration is invalid"
        )
    started_at = datetime.now(timezone.utc)
    monotonic_start = time.monotonic()
    time.sleep(seconds)
    elapsed = time.monotonic() - monotonic_start
    value = {
        "schema_version": "native_v2_service_canary_child.v1",
        "package_id": PACKAGE_ID,
        "process_id": os.getpid(),
        "parent_process_id": os.getppid(),
        "argv": list(getattr(sys, "orig_argv", sys.argv)),
        "working_directory": str(Path.cwd()),
        "environment": {
            key: os.environ.get(key)
            for key in deterministic_environment({
                "RECON_SERVICE_CANARY_SECONDS": str(seconds)
            })
        },
        "requested_seconds": seconds,
        "elapsed_seconds": elapsed,
        "started_at_utc": started_at.isoformat(),
        "ended_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    value["canary_digest"] = digest(value)
    return value


def data_free_runtime_call_canary(
    verifier: Callable[[], Mapping[str, Any]] = verify_runtime_inputs,
) -> dict[str, Any]:
    calls = {"verify": 0}

    def counted_verify() -> Mapping[str, Any]:
        calls["verify"] += 1
        return verifier()

    class FakeRegistry:
        @staticmethod
        def freeze(
            payloads: Mapping[str, bytes], **kwargs: Any
        ) -> Any:
            return type("Registry", (), {
                "registry_id": digest(sorted(payloads)),
                "tape_identity": digest(kwargs["row_order"]),
                "run_identity": kwargs["run_identity"],
            })()

    class FakeWrapper:
        def __init__(self, identity: str) -> None:
            self.identity = identity

        def dumps(self) -> bytes:
            return self.identity.encode()

    restored = {
        (ordinal, arm): FakeWrapper(f"{ordinal}:{arm}")
        for ordinal in range(SEED_COUNT) for arm in ARMS
    }
    dependencies = RuntimeDependencies(
        verify_inputs=counted_verify,
        load_previous_readiness=lambda: {"readiness_digest": "previous"},
        build_context=lambda: {
            "restored": restored,
            "prefix": {"results": []},
            "runtime_manifest": {"entries": []},
        },
        verify_outer_manifest=lambda _label: {
            "outer_sha256": "outer",
            "source_freeze_commit": "source",
            "source_runtime_digest": "runtime",
        },
        load_ecology=lambda: {
            "rows": [{
                "phase": "suffix",
                "row_id": f"row-{index:02d}",
                **{
                    f"{arm}_transition_id": f"{arm}:{index}"
                    for arm in ARMS
                },
            } for index in range(ROW_COUNT)],
            "transitions": [{
                "transition_id": f"{arm}:{index}",
                "predecessor_fen": (
                    "8/8/8/8/8/7K/5R2/7k w - - 0 1"
                ),
            } for arm in ARMS for index in range(ROW_COUNT)],
        },
        load_receipt=lambda: {"receipt_digest": "receipt"},
        expanded_package_map=frozen.expanded_package_map,
        registry_type=FakeRegistry,
    )
    runtime = build_real_exposure_runtime(dependencies)
    value = {
        "verification_call_count": calls["verify"],
        "registry_count": len(runtime["registries"]),
        "organism_count": sum(
            len(bundle["payloads"])
            for bundle in runtime["registries"].values()
        ),
        "outcome_access": {"count": 0, "event_ids": []},
    }
    value["call_canary_digest"] = digest(value)
    return value


def freeze_package_manifests(source_commit: str) -> dict[str, Any]:
    _require_clean_worktree()
    if _git("rev-parse", "HEAD") != source_commit:
        raise ProcessReadinessRepairError(
            "source freeze commit is not HEAD"
        )
    if (ROOT / SOURCE_MANIFEST_PATH).exists() or (
        ROOT / ARTIFACT_BINDING_PATH
    ).exists():
        raise FileExistsError("repair manifests already exist")
    inputs = verify_runtime_inputs()
    source = {
        "schema_version": "native_v2_process_readiness_source.v1",
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
        "deterministic_environment": deterministic_environment(),
        "runtime": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "working_directory": str(ROOT),
        },
        "frozen_inputs": inputs,
        "architecture": {
            "outer_process_repair_only": True,
            "prior_packages_immutable": True,
            "module_global_replacement": False,
            "large_driver_copy": False,
            "real_runtime_uses_preserved_byte_verification": True,
            "journal_admission_before_science_marker": True,
            "strict_partial_outcome_prefix": True,
            "unique_detached_service_attempts": True,
            "restart_recomputes_committed_units_for_comparison": True,
        },
    }
    source["source_manifest_digest"] = digest(source)
    atomic_json(ROOT / SOURCE_MANIFEST_PATH, source)
    binding = {
        "schema_version": "native_v2_process_readiness_binding.v1",
        "package_id": PACKAGE_ID,
        "source_manifest": {
            "path": SOURCE_MANIFEST_PATH.as_posix(),
            "sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
            "digest": source["source_manifest_digest"],
        },
        "frozen_inputs": inputs,
        "paths": {
            "launch_readiness": LAUNCH_READINESS_PATH.as_posix(),
            "service_canary_record": SERVICE_CANARY_RECORD_PATH.as_posix(),
            "readiness": READINESS_PATH.as_posix(),
            "exposure_journal": EXPOSURE_JOURNAL_DIR.as_posix(),
            "exposure": EXPOSURE_PATH.as_posix(),
            "execution": EXECUTION_MANIFEST_PATH.as_posix(),
            "completion": EXPOSURE_COMPLETION_PATH.as_posix(),
            "science_started": SCIENCE_STARTED_PATH.as_posix(),
            "science_journal": SCIENCE_JOURNAL_DIR.as_posix(),
            "science_carrier": SCIENCE_CARRIER_DIR.as_posix(),
            "result": RESULT_PATH.as_posix(),
        },
        "service_law": {
            "unique_attempt": True,
            "four_item_python_argv": True,
            "no_shell": True,
            "no_wall_timeout": True,
            "canary_duration_seconds": CANARY_DURATION_SECONDS,
        },
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
            raise ProcessReadinessRepairError(
                f"repair source changed:{relative}"
            )
    binding = load_json(ROOT / ARTIFACT_BINDING_PATH)
    binding_digest = verify_self_digest(
        binding, "artifact_binding_digest", label="artifact binding"
    )
    if (
        binding["source_manifest"]["sha256"]
        != sha256_file(ROOT / SOURCE_MANIFEST_PATH)
        or binding["source_manifest"]["digest"] != source_digest
        or canonical_bytes(binding["frozen_inputs"])
        != canonical_bytes(verify_runtime_inputs())
    ):
        raise ProcessReadinessRepairError(
            "repair source/artifact binding changed"
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
    }


def run_launch_readiness() -> dict[str, Any]:
    _require_clean_worktree()
    if (ROOT / LAUNCH_READINESS_PATH).exists() or (
        ROOT / LAUNCH_READINESS_FAILURE_PATH
    ).exists():
        raise FileExistsError("launch readiness already exists")
    require_committed_artifact(SOURCE_MANIFEST_PATH)
    require_committed_artifact(ARTIFACT_BINDING_PATH)
    started = time.perf_counter()
    try:
        package = verify_package_manifests()
        inputs = verify_runtime_inputs()
        call_canary = data_free_runtime_call_canary()
        if (
            call_canary["verification_call_count"] != 1
            or call_canary["registry_count"] != len(ARMS)
            or call_canary["organism_count"] != UNIT_COUNT
        ):
            raise ProcessReadinessRepairError(
                "runtime call-path canary failed"
            )
        value = {
            "schema_version": "native_v2_process_launch_readiness.v1",
            "package_id": PACKAGE_ID,
            "source_manifest": {
                "sha256": package["source_manifest_sha256"],
                "digest": package["source_manifest_digest"],
            },
            "artifact_binding": {
                "sha256": package["artifact_binding_sha256"],
                "digest": package["artifact_binding_digest"],
            },
            "runtime_input_digest": inputs["runtime_input_digest"],
            "runtime_call_path_canary": call_canary,
            "cohort_digest": ACCEPTED_COHORT_DIGEST,
            "expanded_package_map_digest": EXPANDED_PACKAGE_MAP_DIGEST,
            "verified_seed_count": SEED_COUNT,
            "verified_organism_count": UNIT_COUNT,
            "canary_duration_seconds": CANARY_DURATION_SECONDS,
            "real_exposure_run": False,
            "real_outcome_run": False,
            "outcome_access": {"count": 0, "event_ids": []},
            "elapsed_seconds": round(time.perf_counter() - started, 6),
        }
        value["launch_readiness_digest"] = digest(value)
        atomic_json(ROOT / LAUNCH_READINESS_PATH, value)
        return value
    except Exception as exc:
        record_failure(
            LAUNCH_READINESS_FAILURE_PATH, "verify-launch-readiness", exc
        )
        raise


def run_final_readiness() -> dict[str, Any]:
    _require_clean_worktree()
    if (ROOT / READINESS_PATH).exists() or (
        ROOT / READINESS_FAILURE_PATH
    ).exists():
        raise FileExistsError("final readiness already exists")
    try:
        package = verify_package_manifests()
        launch = load_and_verify_launch_readiness(committed=True)
        require_committed_artifact(SERVICE_CANARY_RECORD_PATH)
        service = load_json(ROOT / SERVICE_CANARY_RECORD_PATH)
        verify_self_digest(
            service, "final_digest", label="service canary record"
        )
        child = service.get("canary_child", {})
        if (
            service.get("command") != "service-canary"
            or service.get("terminal") is not True
            or service["terminal_status"]["result"] != "success"
            or service["terminal_status"]["exit_status"] != 0
            or service["terminal_status"]["runtime_max_usec"]
            not in {"infinity", "18446744073709551615"}
            or float(child.get("elapsed_seconds", 0))
            < CANARY_DURATION_SECONDS
            or child.get("requested_seconds") != CANARY_DURATION_SECONDS
            or service["launch"]["launch_readiness"]["sha256"]
            != sha256_file(ROOT / LAUNCH_READINESS_PATH)
        ):
            raise ProcessReadinessRepairError(
                "detached service canary gate failed"
            )
        inputs = verify_runtime_inputs()
        value = {
            "schema_version": "native_v2_process_readiness_final.v1",
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
                "sha256": sha256_file(ROOT / SERVICE_CANARY_RECORD_PATH),
                "digest": service["final_digest"],
                "attempt_id": service["attempt_id"],
                "process_id": service["process_id"],
                "elapsed_seconds": child["elapsed_seconds"],
            },
            "runtime_input_digest": inputs["runtime_input_digest"],
            "cohort_digest": ACCEPTED_COHORT_DIGEST,
            "expanded_package_map_digest": EXPANDED_PACKAGE_MAP_DIGEST,
            "verified_seed_count": SEED_COUNT,
            "verified_organism_count": UNIT_COUNT,
            "real_exposure_run": False,
            "real_outcome_run": False,
            "outcome_access": {"count": 0, "event_ids": []},
            "stop_before_exposure": True,
        }
        value["readiness_digest"] = digest(value)
        atomic_json(ROOT / READINESS_PATH, value)
        return value
    except Exception as exc:
        record_failure(
            READINESS_FAILURE_PATH, "verify-final-readiness", exc
        )
        raise


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
    poll.add_argument("--persist-canary-record", action="store_true")
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
        value = poll_service_attempt(
            args.attempt_id,
            persist_canary_record=args.persist_canary_record,
        )
    elif args.command == "run-exposure":
        value = run_exposure()
    elif args.command == "run-science":
        value = run_science()
    elif args.command == "service-canary":
        value = service_canary_child()
    else:  # pragma: no cover
        raise AssertionError(args.command)
    _print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
