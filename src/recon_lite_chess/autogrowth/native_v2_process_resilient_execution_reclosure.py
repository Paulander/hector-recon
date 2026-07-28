"""Process-resilient outer execution for the frozen native V2 cohort.

This module does not change the learner, graph, laboratory registry, cohort,
ecology, thresholds, or statistical rules.  It adds durable unit boundaries
around the already-frozen outcome-blind exposure and correct outer
bookkeeping around the already-frozen outcome journal.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import time
from typing import Any, Callable, Mapping, MutableMapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind

from . import (
    native_v2_fresh_discriminator_review_repair_v2 as driver,
)
from . import (
    native_v2_frozen_cohort_package_alias_compatibility_reclosure as frozen,
)
from . import (
    native_v2_frozen_cohort_execution_adapter_freeze as stopped_adapter,
)
from .native_prospective_evidence_authority_v2_lab import (
    V2LaboratoryRegistry,
)


ROOT = driver.ROOT
PACKAGE_ID = "native_v2_process_resilient_execution_reclosure.v1"
MODULE_PATH = (
    "recon_lite_chess.autogrowth."
    "native_v2_process_resilient_execution_reclosure"
)
STARTING_HEAD = "8baab926a214260eada65765db3383c8033a2716"
ACCEPTED_COHORT_DIGEST = (
    "a144fe94f4479c819756dfc44b22a2594e2b9df09367d571d39ab54007560bb8"
)
EXPANDED_PACKAGE_MAP_DIGEST = (
    "2334cce42845479e8d1a642876d088b96ad18c5d1b55c9b31e7cfaa0549f048d"
)
STOP_REPORT_PATH = Path(
    "docs/autogrowth/"
    "NATIVE_V2_FROZEN_COHORT_PACKAGE_ALIAS_COMPATIBILITY_"
    "EXPOSURE_PROCESS_STOP_20260728.md"
)
STOP_REPORT_SHA256 = (
    "0c93579404128e973756c99dea9749d12ad1e4f07e1ce63c4dcea730e929e59a"
)

PACKAGE_DIR = Path(
    "reports/autogrowth/native_authority/"
    "v2_process_resilient_execution_reclosure"
)
SOURCE_MANIFEST_PATH = PACKAGE_DIR / "source_manifest.json"
ARTIFACT_BINDING_PATH = PACKAGE_DIR / "artifact_binding_manifest.json"
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
    "native_v2_process_resilient_execution_reclosure.py",
    "tests/autogrowth/"
    "test_native_v2_process_resilient_execution_reclosure.py",
    "docs/autogrowth/"
    "NATIVE_V2_PROCESS_RESILIENT_EXECUTION_RECLOSURE_"
    "PREREGISTRATION_20260728.md",
)
PUBLIC_COMMANDS = (
    "verify-readiness",
    "run-exposure",
    "run-science",
    "supervisor-canary",
)
DETERMINISTIC_ENV = copy.deepcopy(frozen.DETERMINISTIC_ENV)
ARMS = tuple(driver.ARMS)
SEED_COUNT = int(driver.SEED_COUNT)
ROW_COUNT = 16
UNIT_COUNT = len(ARMS) * SEED_COUNT
MIN_QUALIFYING_SEEDS = int(driver.MIN_QUALIFYING_SEEDS)
MIN_TARGET_OPPORTUNITIES = int(driver.MIN_TARGET_OPPORTUNITIES)


class ProcessResilienceError(RuntimeError):
    """A frozen identity or durable process boundary changed."""


class SupervisorUnavailable(ProcessResilienceError):
    """The required user-level systemd service manager is unavailable."""


class InjectedProcessInterruption(RuntimeError):
    """Synthetic-only interruption used by focused tests."""


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


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            value.update(chunk)
    return value.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProcessResilienceError(f"expected JSON object:{path}")
    return value


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    _atomic_bytes(path, pretty_json_bytes(value))


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True
    ).strip()


def _require_clean_worktree(*, allow_runtime: bool = False) -> None:
    rows = _git("status", "--porcelain=v1").splitlines()
    if not allow_runtime:
        if rows:
            raise ProcessResilienceError(f"worktree is not clean:{rows}")
        return
    allowed = (
        EXPOSURE_JOURNAL_DIR.as_posix(),
        EXPOSURE_PATH.as_posix(),
        EXECUTION_MANIFEST_PATH.as_posix(),
        EXPOSURE_COMPLETION_PATH.as_posix(),
        SCIENCE_STARTED_PATH.as_posix(),
        SCIENCE_JOURNAL_DIR.as_posix(),
        SCIENCE_CARRIER_DIR.as_posix(),
        RESULT_PATH.as_posix(),
        EXPOSURE_FAILURE_PATH.as_posix(),
        SCIENCE_FAILURE_PATH.as_posix(),
    )
    unexpected = [
        row
        for row in rows
        if not any(row[3:].strip().startswith(prefix) for prefix in allowed)
    ]
    if unexpected:
        raise ProcessResilienceError(
            f"unexpected worktree changes:{unexpected}"
        )


def _require_starting_ancestor() -> None:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", STARTING_HEAD, "HEAD"],
        cwd=ROOT,
        check=False,
    )
    if result.returncode != 0:
        raise ProcessResilienceError("starting commit is not an ancestor")


def require_committed_artifact(relative: Path) -> dict[str, Any]:
    path = ROOT / relative
    if not path.is_file():
        raise ProcessResilienceError(f"required artifact is absent:{relative}")
    committed = subprocess.run(
        ["git", "cat-file", "-e", f"HEAD:{relative.as_posix()}"],
        cwd=ROOT,
        check=False,
    )
    if committed.returncode != 0:
        raise ProcessResilienceError(
            f"required artifact is not committed:{relative}"
        )
    head_bytes = subprocess.check_output(
        ["git", "show", f"HEAD:{relative.as_posix()}"], cwd=ROOT
    )
    current = path.read_bytes()
    if current != head_bytes:
        raise ProcessResilienceError(
            f"required artifact differs from HEAD:{relative}"
        )
    return {
        "path": relative.as_posix(),
        "size": len(current),
        "sha256": sha256_bytes(current),
    }


def verify_self_digest(
    value: Mapping[str, Any], key: str, *, label: str
) -> str:
    unsigned = {name: item for name, item in value.items() if name != key}
    observed = digest(unsigned)
    if value.get(key) != observed:
        raise ProcessResilienceError(f"{label} self-digest mismatch")
    return observed


def build_public_command(command: str) -> tuple[str, ...]:
    if command not in PUBLIC_COMMANDS:
        raise ProcessResilienceError(f"unknown public command:{command}")
    return (sys.executable, "-m", MODULE_PATH, command)


def unit_plan(
    *,
    arms: Sequence[str] = ARMS,
    seed_count: int = SEED_COUNT,
) -> tuple[dict[str, Any], ...]:
    rows = []
    index = 0
    for arm in arms:
        for ordinal in range(seed_count):
            rows.append({
                "unit_index": index,
                "arm": str(arm),
                "seed_ordinal": int(ordinal),
                "unit_id": f"{arm}/seed-{ordinal:02d}",
            })
            index += 1
    return tuple(rows)


def preserved_input_identity() -> dict[str, Any]:
    alias_files = (
        frozen.SOURCE_MANIFEST_PATH,
        frozen.ARTIFACT_BINDING_PATH,
        frozen.READINESS_PATH,
    )
    rows = [require_committed_artifact(path) for path in alias_files]
    rows.append(require_committed_artifact(STOP_REPORT_PATH))
    value = {
        "starting_commit": STARTING_HEAD,
        "stopped_alias_package": rows,
        "stopped_alias_package_dir": frozen.PACKAGE_DIR.as_posix(),
        "stopped_exposure_artifact_absent": not (
            ROOT / frozen.EXPOSURE_PATH
        ).exists(),
        "stopped_execution_manifest_absent": not (
            ROOT / frozen.EXECUTION_MANIFEST_PATH
        ).exists(),
        "stopped_failure_artifact_absent": not (
            ROOT / frozen.EXPOSURE_FAILURE_PATH
        ).exists(),
        "stopped_science_started": False,
        "stopped_science_journal_absent": not (
            ROOT / frozen.SCIENCE_JOURNAL_DIR
        ).exists(),
        "stopped_result_absent": not (ROOT / frozen.RESULT_PATH).exists(),
    }
    if rows[-1]["sha256"] != STOP_REPORT_SHA256:
        raise ProcessResilienceError("terminal process-stop report changed")
    if not all(
        value[key]
        for key in (
            "stopped_exposure_artifact_absent",
            "stopped_execution_manifest_absent",
            "stopped_failure_artifact_absent",
            "stopped_science_journal_absent",
            "stopped_result_absent",
        )
    ):
        raise ProcessResilienceError("stopped package gained a runtime output")
    value["identity_digest"] = digest(value)
    return value


def verify_frozen_inputs() -> dict[str, Any]:
    _require_starting_ancestor()
    preserved = preserved_input_identity()
    alias_package = frozen.verify_package_manifests()
    readiness = frozen.load_and_verify_readiness(committed=True)
    if (
        readiness["cohort_digest"] != ACCEPTED_COHORT_DIGEST
        or readiness["expanded_package_map"]["expanded_map_digest"]
        != EXPANDED_PACKAGE_MAP_DIGEST
        or readiness["verified_seed_count"] != SEED_COUNT
        or readiness["verified_organism_count"] != UNIT_COUNT
    ):
        raise ProcessResilienceError("stopped readiness identity changed")
    package_map = frozen.expanded_package_map()
    if digest(package_map) != EXPANDED_PACKAGE_MAP_DIGEST:
        raise ProcessResilienceError("expanded package map changed")
    value = {
        "preserved_inputs": preserved,
        "alias_package": alias_package,
        "alias_readiness": {
            "sha256": sha256_file(ROOT / frozen.READINESS_PATH),
            "digest": readiness["readiness_digest"],
            "cohort_digest": readiness["cohort_digest"],
            "expanded_package_map_digest": readiness[
                "expanded_package_map"
            ]["expanded_map_digest"],
            "verified_seed_count": readiness["verified_seed_count"],
            "verified_organism_count": readiness[
                "verified_organism_count"
            ],
        },
        "scientific_constants": {
            "arms": list(ARMS),
            "seed_count": SEED_COUNT,
            "unit_count": UNIT_COUNT,
            "row_count": ROW_COUNT,
            "minimum_target_opportunities": MIN_TARGET_OPPORTUNITIES,
            "minimum_qualifying_seeds": MIN_QUALIFYING_SEEDS,
            "minimum_favorable_seeds": int(driver.MIN_FAVORABLE_SEEDS),
            "primary_alpha": float(driver.PRIMARY_ALPHA),
            "bootstrap_replicates": int(driver.BOOTSTRAP_REPLICATES),
        },
        "unit_plan": list(unit_plan()),
        "unit_plan_digest": digest(unit_plan()),
    }
    value["frozen_input_digest"] = digest(value)
    return value


@dataclass
class ExposureUnitJournal:
    root: Path

    def records(self) -> list[dict[str, Any]]:
        if not self.root.exists():
            return []
        paths = sorted(self.root.glob("*.json"))
        rows = []
        previous = "GENESIS"
        for index, path in enumerate(paths):
            row = _load_json(path)
            unsigned = {
                key: value
                for key, value in row.items()
                if key != "record_digest"
            }
            if row.get("record_digest") != digest(unsigned):
                raise ProcessResilienceError(
                    f"exposure journal record digest mismatch:{path.name}"
                )
            if (
                int(row.get("record_index", -1)) != index
                or row.get("previous_record_digest") != previous
            ):
                raise ProcessResilienceError(
                    f"exposure journal chain/order mismatch:{path.name}"
                )
            expected_prefix = f"{index:06d}_{row.get('kind')}_"
            if not path.name.startswith(expected_prefix):
                raise ProcessResilienceError(
                    f"exposure journal filename mismatch:{path.name}"
                )
            previous = str(row["record_digest"])
            rows.append(row)
        return rows

    def append(
        self,
        kind: str,
        *,
        unit_index: int,
        unit_id: str,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        if kind not in {"PREPARED", "COMMITTED"}:
            raise ProcessResilienceError(f"invalid exposure record:{kind}")
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
        _atomic_json(self.root / name, row)
        return row

    def analyze(
        self, bindings: Sequence[Mapping[str, Any]]
    ) -> dict[str, Any]:
        expected = tuple(copy.deepcopy(dict(item)) for item in bindings)
        records = self.records()
        cursor = 0
        committed = []
        prepared_attempts: dict[int, list[dict[str, Any]]] = {}
        for unit_index, binding in enumerate(expected):
            attempts = []
            while (
                cursor < len(records)
                and records[cursor]["kind"] == "PREPARED"
                and int(records[cursor]["unit_index"]) == unit_index
            ):
                row = records[cursor]
                payload = row["payload"]
                attempt = len(attempts) + 1
                if (
                    row["unit_id"] != binding["unit_id"]
                    or payload.get("unit_binding") != binding
                    or int(payload.get("attempt", -1)) != attempt
                    or int(payload.get("recomputation_count", -1))
                    != attempt - 1
                    or payload.get("recomputes_prepared_record_digest")
                    != (
                        None
                        if not attempts
                        else attempts[-1]["record_digest"]
                    )
                    or payload.get("outcome_access")
                    != {"count": 0, "event_ids": []}
                ):
                    raise ProcessResilienceError(
                        f"changed or foreign PREPARED unit:{unit_index}"
                    )
                attempts.append(row)
                cursor += 1
            if not attempts:
                if cursor != len(records):
                    raise ProcessResilienceError(
                        f"exposure journal gap/reorder:{unit_index}"
                    )
                return self._plan(
                    records, committed, prepared_attempts, unit_index, None
                )
            prepared_attempts[unit_index] = attempts
            if cursor == len(records):
                return self._plan(
                    records, committed, prepared_attempts, unit_index, attempts
                )
            row = records[cursor]
            if (
                row["kind"] != "COMMITTED"
                or int(row["unit_index"]) != unit_index
                or row["unit_id"] != binding["unit_id"]
            ):
                raise ProcessResilienceError(
                    f"exposure journal changed order:{unit_index}"
                )
            payload = row["payload"]
            result = payload.get("unit_result")
            if (
                payload.get("unit_binding_digest")
                != binding["unit_binding_digest"]
                or payload.get("prepared_record_digest")
                != attempts[-1]["record_digest"]
                or not isinstance(result, Mapping)
                or payload.get("unit_result_digest") != digest(result)
                or result.get("outcome_access")
                != {"count": 0, "event_ids": []}
            ):
                raise ProcessResilienceError(
                    f"changed COMMITTED unit:{unit_index}"
                )
            committed.append(row)
            cursor += 1
        if cursor != len(records):
            raise ProcessResilienceError("foreign exposure journal suffix")
        return self._plan(
            records, committed, prepared_attempts, None, None
        )

    @staticmethod
    def _plan(
        records: Sequence[Mapping[str, Any]],
        committed: Sequence[Mapping[str, Any]],
        attempts: Mapping[int, Sequence[Mapping[str, Any]]],
        next_index: int | None,
        dangling: Sequence[Mapping[str, Any]] | None,
    ) -> dict[str, Any]:
        value = {
            "record_count": len(records),
            "committed_unit_indices": [
                int(item["unit_index"]) for item in committed
            ],
            "committed_unit_count": len(committed),
            "next_unit_index": next_index,
            "dangling_prepared_unit_index": (
                None if dangling is None else next_index
            ),
            "dangling_prepared_attempt_count": (
                0 if dangling is None else len(dangling)
            ),
            "recomputation_count": sum(
                max(0, len(items) - 1) for items in attempts.values()
            ),
            "journal_chain_digest": digest(records),
            "last_record_digest": (
                "GENESIS" if not records else records[-1]["record_digest"]
            ),
        }
        value["restart_plan_digest"] = digest(value)
        return value

    def prepare(
        self,
        binding: Mapping[str, Any],
        existing_attempts: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        attempt = len(existing_attempts) + 1
        return self.append(
            "PREPARED",
            unit_index=int(binding["unit_index"]),
            unit_id=str(binding["unit_id"]),
            payload={
                "unit_binding": copy.deepcopy(dict(binding)),
                "attempt": attempt,
                "recomputation_count": attempt - 1,
                "recomputes_prepared_record_digest": (
                    None
                    if not existing_attempts
                    else existing_attempts[-1]["record_digest"]
                ),
                "outcome_access": {"count": 0, "event_ids": []},
            },
        )

    def commit(
        self,
        binding: Mapping[str, Any],
        prepared: Mapping[str, Any],
        result: Mapping[str, Any],
    ) -> dict[str, Any]:
        if result.get("outcome_access") != {"count": 0, "event_ids": []}:
            raise ProcessResilienceError("exposure unit opened an outcome")
        return self.append(
            "COMMITTED",
            unit_index=int(binding["unit_index"]),
            unit_id=str(binding["unit_id"]),
            payload={
                "unit_binding_digest": binding["unit_binding_digest"],
                "prepared_record_digest": prepared["record_digest"],
                "unit_result": copy.deepcopy(dict(result)),
                "unit_result_digest": digest(result),
            },
        )


def execute_resumable_units(
    *,
    bindings: Sequence[Mapping[str, Any]],
    journal: ExposureUnitJournal,
    compute_unit: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    interrupt: Callable[[str, int], None] | None = None,
) -> dict[str, Any]:
    hook = interrupt or (lambda _stage, _index: None)
    plan = journal.analyze(bindings)
    committed_by_index = {
        int(row["unit_index"]): row for row in journal.records()
        if row["kind"] == "COMMITTED"
    }
    for index in plan["committed_unit_indices"]:
        expected = compute_unit(bindings[index])
        stored = committed_by_index[index]["payload"]["unit_result"]
        if canonical_bytes(expected) != canonical_bytes(stored):
            raise ProcessResilienceError(
                f"committed exposure unit changed:{index}"
            )
    next_index = plan["next_unit_index"]
    while next_index is not None:
        binding = bindings[next_index]
        current = journal.analyze(bindings)
        attempts = [
            row for row in journal.records()
            if row["kind"] == "PREPARED"
            and int(row["unit_index"]) == next_index
        ]
        hook("before_unit", next_index)
        prepared = journal.prepare(binding, attempts)
        hook("after_prepared", next_index)
        result = compute_unit(binding)
        hook("after_unit", next_index)
        journal.commit(binding, prepared, result)
        hook("after_committed", next_index)
        current = journal.analyze(bindings)
        next_index = current["next_unit_index"]
    final = journal.analyze(bindings)
    if final["committed_unit_count"] != len(bindings):
        raise ProcessResilienceError("exposure units ended incomplete")
    results = [
        row["payload"]["unit_result"]
        for row in journal.records() if row["kind"] == "COMMITTED"
    ]
    if len(results) != len(bindings):
        raise ProcessResilienceError("committed exposure coverage changed")
    return {"restart_plan": final, "unit_results": results}


def finalize_exact_artifacts(
    *,
    exposure: Mapping[str, Any],
    build_execution: Callable[[Mapping[str, Any], str], Mapping[str, Any]],
    exposure_path: Path,
    execution_path: Path,
    completion_path: Path,
    completion_extra: Mapping[str, Any],
    interrupt: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    hook = interrupt or (lambda _stage: None)
    exposure_payload = pretty_json_bytes(exposure)
    exposure_sha = sha256_bytes(exposure_payload)
    execution = build_execution(exposure, exposure_sha)
    execution_payload = pretty_json_bytes(execution)
    execution_sha = sha256_bytes(execution_payload)

    for path, expected, label in (
        (exposure_path, exposure_payload, "exposure"),
        (execution_path, execution_payload, "execution"),
    ):
        if path.exists() and path.read_bytes() != expected:
            raise ProcessResilienceError(
                f"divergent pre-existing {label} artifact"
            )

    if not exposure_path.exists():
        _atomic_bytes(exposure_path, exposure_payload)
    hook("after_exposure")
    if not execution_path.exists():
        _atomic_bytes(execution_path, execution_payload)
    hook("after_execution")

    marker = {
        "schema_version": "native_v2_exposure_completion.v1",
        "package_id": PACKAGE_ID,
        "exposure": {
            "path": exposure_path.as_posix(),
            "sha256": exposure_sha,
            "digest": exposure["exposure_digest"],
        },
        "execution_manifest": {
            "path": execution_path.as_posix(),
            "sha256": execution_sha,
            "digest": execution["execution_manifest_digest"],
        },
        **copy.deepcopy(dict(completion_extra)),
    }
    marker["completion_digest"] = digest(marker)
    marker_payload = pretty_json_bytes(marker)
    if completion_path.exists():
        if completion_path.read_bytes() != marker_payload:
            raise ProcessResilienceError(
                "divergent exposure completion marker"
            )
    else:
        _atomic_bytes(completion_path, marker_payload)
    hook("after_completion")
    return {
        "exposure": copy.deepcopy(dict(exposure)),
        "execution_manifest": copy.deepcopy(dict(execution)),
        "completion": marker,
    }


def _snapshot_entry(
    manifest: Mapping[str, Any], ordinal: int, arm: str
) -> Mapping[str, Any]:
    matches = [
        item for item in manifest["entries"]
        if int(item["seed_ordinal"]) == ordinal and str(item["arm"]) == arm
    ]
    if len(matches) != 1:
        raise ProcessResilienceError(
            f"snapshot entry missing or duplicated:{arm}:{ordinal}"
        )
    return matches[0]


def build_real_exposure_runtime() -> dict[str, Any]:
    frozen.verify_package_manifests()
    readiness = frozen.load_and_verify_readiness(committed=True)
    context = stopped_adapter.build_readiness_context()
    identity = driver.verify_outer_manifest(
        "process-resilient exposure runtime"
    )
    ecology = driver._load_json(ROOT / driver.ECOLOGY_MANIFEST_PATH)
    receipt = _load_json(ROOT / stopped_adapter.PREFLIGHT_RECEIPT_PATH)
    package_hashes = frozen.expanded_package_map()
    if digest(package_hashes) != EXPANDED_PACKAGE_MAP_DIGEST:
        raise ProcessResilienceError("expanded package map changed")
    row_order = tuple(
        str(row["row_id"]) for row in driver.ecology_rows(ecology, "suffix")
    )
    registries = {}
    for arm in ARMS:
        payloads = {}
        rows = {}
        for ordinal in range(SEED_COUNT):
            organism_id = f"seed-{ordinal:02d}"
            payloads[organism_id] = context["restored"][(ordinal, arm)].dumps()
            rows[organism_id] = driver._suffix_registered_rows(
                ecology, arm, ordinal
            )
        run_identity = digest({
            "experiment_id": driver.EXPERIMENT_ID,
            "phase": "preoutcome_exposure",
            "arm": arm,
            "outer_manifest_sha256": identity["outer_sha256"],
        })
        registry = V2LaboratoryRegistry.freeze(
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
        "readiness": readiness,
        "identity": identity,
        "ecology": ecology,
        "receipt": receipt,
        "package_hashes": package_hashes,
        "row_order": row_order,
        "registries": registries,
    }


def production_unit_bindings(
    runtime: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    bindings = []
    map_digest = digest(runtime["package_hashes"])
    for item in unit_plan():
        arm = str(item["arm"])
        ordinal = int(item["seed_ordinal"])
        organism_id = f"seed-{ordinal:02d}"
        wrapper = runtime["restored"][(ordinal, arm)]
        registry = runtime["registries"][arm]["registry"]
        rows = runtime["registries"][arm]["rows"][organism_id]
        snapshot = copy.deepcopy(dict(_snapshot_entry(
            runtime["runtime_manifest"], ordinal, arm
        )))
        value = {
            "schema_version": "native_v2_exposure_unit_binding.v1",
            **copy.deepcopy(dict(item)),
            "organism_id": organism_id,
            "source_snapshot_identity": {
                "entry": snapshot,
                "entry_digest": digest(snapshot),
            },
            "candidate_graph_continuation_digest": (
                wrapper.continuation_digest()
            ),
            "payload_sha256": sha256_bytes(
                runtime["registries"][arm]["payloads"][organism_id]
            ),
            "registry_identity": registry.registry_id,
            "registry_tape_identity": registry.tape_identity,
            "registry_run_identity": registry.run_identity,
            "expanded_package_map_digest": map_digest,
            "row_order": list(runtime["row_order"]),
            "row_order_digest": digest(runtime["row_order"]),
            "row_definitions": [row.manifest() for row in rows],
            "row_definition_digest": digest([
                row.manifest() for row in rows
            ]),
            "outcome_access": {"count": 0, "event_ids": []},
        }
        value["unit_binding_digest"] = digest(value)
        bindings.append(value)
    return tuple(bindings)


def compute_production_unit(
    binding: Mapping[str, Any],
    runtime: Mapping[str, Any],
) -> dict[str, Any]:
    arm = str(binding["arm"])
    ordinal = int(binding["seed_ordinal"])
    organism_id = str(binding["organism_id"])
    wrapper = runtime["restored"][(ordinal, arm)]
    registry_bundle = runtime["registries"][arm]
    registry = registry_bundle["registry"]
    rows = registry_bundle["rows"][organism_id]
    payload = registry_bundle["payloads"][organism_id]
    targets = runtime["prefix"]["results"][ordinal]["targets"]
    before = wrapper.continuation_digest()
    commitments = []
    projections = []
    for source_row, registered in zip(
        driver.ecology_rows(runtime["ecology"], "suffix"),
        rows,
        strict=True,
    ):
        commitment = wrapper.probe_real_exposure(FrameContext(
            registered.frame_id,
            FrameKind.REAL,
            values={"board": chess.Board(registered.predecessor_fen)},
        ))
        commitments.append(commitment)
        projections.append(driver.classification_visible_projection(
            wrapper,
            commitment,
            commitment.trace,
            planted_cell_id=driver.target_cell_id(targets, "planted"),
            spurious_cell_id=driver.target_cell_id(
                targets, "selected_spurious"
            ),
            row_id=str(source_row["row_id"]),
        ))
    after = wrapper.continuation_digest()
    if after != before:
        raise ProcessResilienceError(
            f"exposure changed organism:{arm}:{ordinal}"
        )
    scan_wrapper = registry.scan(
        organism_id,
        payload,
        commitments,
        tape_identity=registry.tape_identity,
        row_order=runtime["row_order"],
        run_identity=registry.run_identity,
        package_hashes=runtime["package_hashes"],
    )
    value = {
        "schema_version": "native_v2_exposure_unit_result.v1",
        "unit_index": int(binding["unit_index"]),
        "unit_id": str(binding["unit_id"]),
        "arm": arm,
        "seed_ordinal": ordinal,
        "organism_id": organism_id,
        "unit_binding_digest": binding["unit_binding_digest"],
        "commitments": [item.manifest() for item in commitments],
        "classifier_visible_projections": projections,
        "scan_wrapper": scan_wrapper,
        "target_counts": driver._target_counts_from_scan(
            scan_wrapper["scan"], targets
        ),
        "continuation_digest_before": before,
        "continuation_digest_after": after,
        "candidate_graph_state_unchanged": True,
        "outcome_access": {"count": 0, "event_ids": []},
    }
    value["unit_result_digest"] = digest(value)
    return value


def assemble_production_exposure(
    runtime: Mapping[str, Any],
    unit_results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if len(unit_results) != UNIT_COUNT:
        raise ProcessResilienceError("exposure unit coverage is incomplete")
    by_key = {
        (str(item["arm"]), int(item["seed_ordinal"])): item
        for item in unit_results
    }
    if len(by_key) != UNIT_COUNT:
        raise ProcessResilienceError("duplicate exposure unit")
    prefix_verification = driver._verify_prefix_snapshot_metadata(
        runtime["prefix"], runtime["runtime_manifest"], runtime["restored"]
    )
    arms_result = {}
    projections: dict[int, dict[str, list[dict[str, Any]]]] = {
        ordinal: {} for ordinal in range(SEED_COUNT)
    }
    target_counts: dict[int, dict[str, dict[str, Any]]] = {
        ordinal: {} for ordinal in range(SEED_COUNT)
    }
    for arm in ARMS:
        registry = runtime["registries"][arm]["registry"]
        scans = []
        per_seed = []
        for ordinal in range(SEED_COUNT):
            unit = by_key[(arm, ordinal)]
            scan = unit["scan_wrapper"]
            scans.append(scan)
            projections[ordinal][arm] = copy.deepcopy(
                unit["classifier_visible_projections"]
            )
            target_counts[ordinal][arm] = copy.deepcopy(
                unit["target_counts"]
            )
            per_seed.append({
                "ordinal": ordinal,
                "organism_id": unit["organism_id"],
                "continuation_digest": unit[
                    "continuation_digest_before"
                ],
                "target_counts": copy.deepcopy(unit["target_counts"]),
                "scan_wrapper_digest": digest(scan),
                "projection_digests": [
                    item["projection_digest"]
                    for item in unit["classifier_visible_projections"]
                ],
            })
        adjudication = registry.adjudicate_cohort(
            scans,
            tape_identity=registry.tape_identity,
            row_order=runtime["row_order"],
            run_identity=registry.run_identity,
            package_hashes=runtime["package_hashes"],
        )
        arms_result[arm] = {
            "registry": driver._registry_manifest(registry),
            "registry_adjudication": adjudication,
            "per_seed": per_seed,
            "scan_wrapper_set_digest": digest(scans),
        }
    parity_rows = []
    for ordinal in range(SEED_COUNT):
        for row_index, row_id in enumerate(runtime["row_order"]):
            values = {
                arm: projections[ordinal][arm][row_index] for arm in ARMS
            }
            comparable = {
                arm: {
                    key: item for key, item in value.items()
                    if key != "projection_digest"
                }
                for arm, value in values.items()
            }
            if not (comparable["A"] == comparable["B"] == comparable["C"]):
                raise ProcessResilienceError(
                    f"A/B/C exposure parity failure:{ordinal}:{row_id}"
                )
            parity_rows.append({
                "ordinal": ordinal,
                "row_id": row_id,
                "equal": True,
                "projection_digests": {
                    arm: values[arm]["projection_digest"] for arm in ARMS
                },
            })
    qualifications = []
    for ordinal in range(SEED_COUNT):
        qualified = all(
            target_counts[ordinal][arm][name]["distinct_opportunities"]
            >= MIN_TARGET_OPPORTUNITIES
            for arm in ARMS
            for name in ("planted", "selected_spurious")
        )
        qualifications.append({"ordinal": ordinal, "qualified": qualified})
    qualifying = sum(item["qualified"] for item in qualifications)
    registry_hash = digest(runtime["package_hashes"])
    authorization = {
        "schema_version": (
            "native_v2_review_repair_v2_preflight_authorization.v1"
        ),
        "experiment_id": driver.EXPERIMENT_ID,
        "registry_package_hash": registry_hash,
        "expected_global_preflight": {
            "receipt_digest": runtime["receipt"]["receipt_digest"],
            "snapshot_manifest_digest": runtime["runtime_manifest"][
                "manifest_digest"
            ],
            "registry_package_hash": registry_hash,
        },
        "complete_96_required": True,
        "outcome_access_at_freeze": {"count": 0, "event_ids": []},
    }
    authorization["authorization_digest"] = digest(authorization)
    driver.verify_bound_preflight_authorization(
        receipt=runtime["receipt"],
        snapshot_manifest=runtime["runtime_manifest"],
        authorization=authorization,
    )
    value = {
        "schema_version": (
            "native_v2_review_repair_v2_preoutcome_exposure.v1"
        ),
        "experiment_id": driver.EXPERIMENT_ID,
        "outer_manifest_sha256": runtime["identity"]["outer_sha256"],
        "snapshot_manifest_digest": runtime["runtime_manifest"][
            "manifest_digest"
        ],
        "complete_snapshot_identity": driver._complete_snapshot_identity(
            runtime["runtime_manifest"], runtime["restored"]
        ),
        "prefix_candidate_verification": prefix_verification,
        "global_preflight_receipt": copy.deepcopy(runtime["receipt"]),
        "preflight_authorization": authorization,
        "registry_package_hash": registry_hash,
        "arms": arms_result,
        "parity_rows": parity_rows,
        "parity_row_count": len(parity_rows),
        "parity_digest": digest(parity_rows),
        "per_seed_qualification": qualifications,
        "qualification_digest": digest(qualifications),
        "qualifying_seed_count": qualifying,
        "required_qualifying_seed_count": MIN_QUALIFYING_SEEDS,
        "admitted": qualifying >= MIN_QUALIFYING_SEEDS,
        "stop_reason": (
            None
            if qualifying >= MIN_QUALIFYING_SEEDS
            else "prospective_evidence_starvation"
        ),
        "outcome_access": {"count": 0, "event_ids": []},
    }
    value["exposure_digest"] = digest(value)
    return value


def build_execution_manifest(
    runtime: Mapping[str, Any],
    exposure: Mapping[str, Any],
    exposure_sha256: str,
) -> dict[str, Any]:
    if exposure["outcome_access"] != {"count": 0, "event_ids": []}:
        raise ProcessResilienceError("exposure opened an outcome")
    value = {
        "schema_version": (
            "native_v2_process_resilient_execution_manifest.v1"
        ),
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
        "process_resilience_package": {
            "source_manifest_sha256": sha256_file(
                ROOT / SOURCE_MANIFEST_PATH
            ),
            "artifact_binding_sha256": sha256_file(
                ROOT / ARTIFACT_BINDING_PATH
            ),
            "readiness_sha256": sha256_file(ROOT / READINESS_PATH),
            "readiness_digest": runtime["process_readiness"][
                "readiness_digest"
            ],
        },
        "stopped_alias_readiness": {
            "sha256": sha256_file(ROOT / frozen.READINESS_PATH),
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


def run_exposure() -> dict[str, Any]:
    _require_clean_worktree(allow_runtime=True)
    if (ROOT / EXPOSURE_FAILURE_PATH).exists():
        raise ProcessResilienceError("exposure has a terminal failure")
    verify_package_manifests()
    process_readiness = load_and_verify_readiness(committed=True)
    runtime = build_real_exposure_runtime()
    runtime["process_readiness"] = process_readiness
    bindings = production_unit_bindings(runtime)
    journal = ExposureUnitJournal(ROOT / EXPOSURE_JOURNAL_DIR)
    try:
        execution = execute_resumable_units(
            bindings=bindings,
            journal=journal,
            compute_unit=lambda binding: compute_production_unit(
                binding, runtime
            ),
        )
        exposure = assemble_production_exposure(
            runtime, execution["unit_results"]
        )
        completed = finalize_exact_artifacts(
            exposure=exposure,
            build_execution=lambda value, sha: build_execution_manifest(
                runtime, value, sha
            ),
            exposure_path=ROOT / EXPOSURE_PATH,
            execution_path=ROOT / EXECUTION_MANIFEST_PATH,
            completion_path=ROOT / EXPOSURE_COMPLETION_PATH,
            completion_extra={
                "unit_count": UNIT_COUNT,
                "exposure_journal_chain_digest": execution[
                    "restart_plan"
                ]["journal_chain_digest"],
                "exposure_recomputation_count": execution[
                    "restart_plan"
                ]["recomputation_count"],
                "outcome_access": {"count": 0, "event_ids": []},
            },
        )
        return completed
    except Exception as exc:
        record_failure(EXPOSURE_FAILURE_PATH, "run-exposure", exc)
        raise


def validate_completed_exposure() -> dict[str, Any]:
    verify_package_manifests()
    require_committed_artifact(EXPOSURE_PATH)
    require_committed_artifact(EXECUTION_MANIFEST_PATH)
    require_committed_artifact(EXPOSURE_COMPLETION_PATH)
    exposure = _load_json(ROOT / EXPOSURE_PATH)
    execution = _load_json(ROOT / EXECUTION_MANIFEST_PATH)
    completion = _load_json(ROOT / EXPOSURE_COMPLETION_PATH)
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
        exposure.get("admitted") is not True
        or execution.get("admitted") is not True
        or exposure.get("outcome_access")
        != {"count": 0, "event_ids": []}
        or completion.get("outcome_access")
        != {"count": 0, "event_ids": []}
        or exposure.get("registry_package_hash")
        != EXPANDED_PACKAGE_MAP_DIGEST
    ):
        raise ProcessResilienceError("completed exposure gate changed")
    for path, row in (
        (ROOT / EXPOSURE_PATH, completion["exposure"]),
        (
            ROOT / EXECUTION_MANIFEST_PATH,
            completion["execution_manifest"],
        ),
    ):
        if (
            sha256_file(path) != row["sha256"]
            or _load_json(path).get(
                "exposure_digest"
                if path == ROOT / EXPOSURE_PATH
                else "execution_manifest_digest"
            )
            != row["digest"]
        ):
            raise ProcessResilienceError("completion file binding changed")
    return {
        "exposure": exposure,
        "execution_manifest": execution,
        "completion": completion,
    }


def science_started_value(
    completed: Mapping[str, Any],
) -> dict[str, Any]:
    value = {
        "schema_version": "native_v2_science_started.v1",
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
    if path.exists():
        value = _load_json(path)
        verify_self_digest(
            value, "science_started_digest", label="science started"
        )
        for key, expected in (
            ("package_id", PACKAGE_ID),
            ("experiment_id", driver.EXPERIMENT_ID),
            ("complete_suffix_consumed", True),
            (
                "exposure_digest",
                completed["exposure"]["exposure_digest"],
            ),
            (
                "execution_manifest_digest",
                completed["execution_manifest"][
                    "execution_manifest_digest"
                ],
            ),
        ):
            if value.get(key) != expected:
                raise ProcessResilienceError(
                    "science-started marker changed"
                )
        return value
    value = science_started_value(completed)
    _atomic_json(path, value)
    return value


def outcome_accounting_from_journal(path: Path) -> dict[str, Any]:
    try:
        journal = driver.DurableHashJournal(path)
        records = journal._records()
        event_ids: list[str] = []
        for row in records:
            payload = row["payload"]
            if row["kind"] == "OUTCOME_ACCESSED":
                event_id = str(payload["event_id"])
                expected_ids = [*event_ids, event_id]
                expected = {
                    "count": len(expected_ids),
                    "event_ids": expected_ids,
                }
                if payload.get("next_guard_manifest") != expected:
                    raise ProcessResilienceError(
                        "journal outcome sequence changed"
                    )
                event_ids = expected_ids
            elif row["kind"] in {
                "PREPARED", "TRI_ARM_ROW_COMMITTED", "COMMITTED", "FAILED"
            }:
                manifest = payload.get("outcome_access")
                if manifest is not None and manifest != {
                    "count": len(event_ids),
                    "event_ids": event_ids,
                }:
                    raise ProcessResilienceError(
                        "journal outcome checkpoint changed"
                    )
            else:
                raise ProcessResilienceError(
                    f"unknown science journal record:{row['kind']}"
                )
        value = {
            "status": "known",
            "count": len(event_ids),
            "event_ids": event_ids,
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
            "journal_record_count": None,
            "journal_chain_digest": None,
            "last_valid_record_digest": None,
            "validation_error_type": type(exc).__name__,
            "validation_error": str(exc),
        }
    value["accounting_digest"] = digest(value)
    return value


def science_restart_plan(
    journal: Any, ordinals: Sequence[int]
) -> dict[str, Any]:
    records = journal._records()
    if any(row["kind"] == "FAILED" for row in records):
        raise ProcessResilienceError("science journal contains FAILED record")
    next_seed = journal.next_seed(tuple(ordinals))
    completed = [
        int(row["seed_ordinal"])
        for row in records if row["kind"] == "COMMITTED"
    ]
    expected = list(map(int, ordinals))[:len(completed)]
    if completed != expected:
        raise ProcessResilienceError(
            "science committed seeds are not a contiguous prefix"
        )
    value = {
        "completed_ordinals": completed,
        "next_unfinished_seed": next_seed,
        "remaining_ordinals": (
            [] if next_seed is None
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
        raise ProcessResilienceError("science has a terminal failure")
    completed = validate_completed_exposure()
    # The marker is deliberately written before constructing the environment.
    started = persist_science_started(ROOT / SCIENCE_STARTED_PATH, completed)
    try:
        runtime = build_real_exposure_runtime()
        runtime["process_readiness"] = load_and_verify_readiness(
            committed=True
        )
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
        journal = driver.DurableHashJournal(ROOT / SCIENCE_JOURNAL_DIR)
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
            live: MutableMapping[str, Any] = {
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
            driver.execute_fresh_seed_atomically(
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
        final_journal = driver.DurableHashJournal(ROOT / SCIENCE_JOURNAL_DIR)
        final_plan = science_restart_plan(
            final_journal, tuple(range(SEED_COUNT))
        )
        if final_plan["next_unfinished_seed"] is not None:
            raise ProcessResilienceError("science ended before seed 31")
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
            ROOT / SCIENCE_JOURNAL_DIR
        )
        if accounting["status"] != "known":
            raise ProcessResilienceError(
                "completed science outcome accounting is unknown"
            )
        value = {
            "schema_version": "native_v2_process_resilient_result.v1",
            "package_id": PACKAGE_ID,
            "experiment_id": driver.EXPERIMENT_ID,
            "science_started_digest": started["science_started_digest"],
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
        driver._atomic_bytes(
            ROOT / RESULT_PATH,
            driver.deterministic_gzip(canonical_bytes(value)),
        )
        return value
    except Exception as exc:
        record_science_failure(exc, started)
        raise


def record_failure(path: Path, command: str, exc: Exception) -> None:
    if (ROOT / path).exists():
        return
    value = {
        "schema_version": "native_v2_process_resilient_failure.v1",
        "package_id": PACKAGE_ID,
        "command": command,
        "exception_type": type(exc).__name__,
        "detail": str(exc),
        "parent_argv": list(getattr(sys, "orig_argv", sys.argv)),
        "process_id": os.getpid(),
    }
    value["failure_digest"] = digest(value)
    _atomic_json(ROOT / path, value)


def record_science_failure(
    exc: Exception, started: Mapping[str, Any]
) -> None:
    path = ROOT / SCIENCE_FAILURE_PATH
    if path.exists():
        return
    value = build_science_failure(
        exc,
        started,
        journal_path=ROOT / SCIENCE_JOURNAL_DIR,
    )
    _atomic_json(path, value)


def build_science_failure(
    exc: Exception,
    started: Mapping[str, Any],
    *,
    journal_path: Path,
) -> dict[str, Any]:
    accounting = outcome_accounting_from_journal(journal_path)
    value = {
        "schema_version": "native_v2_process_resilient_science_failure.v1",
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
    return value


def deterministic_environment() -> dict[str, str]:
    return {
        str(key): str(value)
        for key, value in sorted(DETERMINISTIC_ENV.items())
    }


def supervisor_log_root() -> Path:
    state = os.environ.get("XDG_STATE_HOME")
    base = Path(state) if state else Path.home() / ".local" / "state"
    return base / "hector-recon-v2-process-resilient"


def build_systemd_argv(
    command: str,
    *,
    service_name: str,
    stdout_path: Path,
    stderr_path: Path,
    wait: bool,
) -> tuple[str, ...]:
    python_argv = build_public_command(command)
    values = [
        "systemd-run",
        "--user",
        f"--unit={service_name}",
        "--property=Type=exec",
        f"--property=WorkingDirectory={ROOT}",
        f"--property=StandardOutput=append:{stdout_path}",
        f"--property=StandardError=append:{stderr_path}",
    ]
    if wait:
        values.append("--wait")
    values.extend(
        f"--setenv={key}={value}"
        for key, value in deterministic_environment().items()
    )
    values.extend(("--", *python_argv))
    return tuple(values)


def manual_persistent_commands(command: str) -> dict[str, str]:
    environment = " ".join(
        f"{key}={shlex.quote(value)}"
        for key, value in deterministic_environment().items()
    )
    return {
        "working_directory": f"cd {shlex.quote(str(ROOT))}",
        "command": (
            f"env {environment} "
            + shlex.join(build_public_command(command))
        ),
    }


def _systemd_available() -> tuple[bool, dict[str, Any]]:
    result = subprocess.run(
        ["systemctl", "--user", "is-system-running"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    status = result.stdout.strip()
    available = result.returncode in {0, 1} and status in {
        "running", "degraded", "starting"
    }
    return available, {
        "argv": ["systemctl", "--user", "is-system-running"],
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "status": status,
    }


def supervisor_canary_child() -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    value = {
        "schema_version": "native_v2_supervisor_canary_child.v1",
        "process_id": os.getpid(),
        "parent_process_id": os.getppid(),
        "argv": list(getattr(sys, "orig_argv", sys.argv)),
        "working_directory": str(Path.cwd()),
        "environment": {
            key: os.environ.get(key)
            for key in deterministic_environment()
        },
        "started_at_utc": started,
        "ended_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    value["canary_digest"] = digest(value)
    return value


def run_supervised_canary(
    *,
    log_root: Path | None = None,
) -> dict[str, Any]:
    available, check = _systemd_available()
    if not available:
        raise SupervisorUnavailable(json.dumps({
            "detail": "user-level systemd is unavailable",
            "systemd_check": check,
            "manual_run_exposure": manual_persistent_commands(
                "run-exposure"
            ),
            "manual_run_science": manual_persistent_commands("run-science"),
        }, sort_keys=True))
    root = supervisor_log_root() if log_root is None else Path(log_root)
    root.mkdir(parents=True, exist_ok=True)
    stamp = f"{int(time.time() * 1_000_000)}-{os.getpid()}"
    service_name = f"recon-v2-resilience-canary-{stamp}"
    stdout_path = root / f"{service_name}.stdout.log"
    stderr_path = root / f"{service_name}.stderr.log"
    argv = build_systemd_argv(
        "supervisor-canary",
        service_name=service_name,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        wait=True,
    )
    launched_at = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(
        list(argv),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    ended_at = datetime.now(timezone.utc).isoformat()
    if result.returncode != 0:
        raise SupervisorUnavailable(json.dumps({
            "detail": "harmless systemd canary failed",
            "argv": list(argv),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "manual_run_exposure": manual_persistent_commands(
                "run-exposure"
            ),
            "manual_run_science": manual_persistent_commands("run-science"),
        }, sort_keys=True))
    if not stdout_path.is_file() or not stderr_path.is_file():
        raise ProcessResilienceError("supervisor canary logs are absent")
    child_stdout = stdout_path.read_text(encoding="utf-8")
    if not child_stdout.strip():
        raise ProcessResilienceError("supervisor canary stdout is empty")
    try:
        child = json.loads(child_stdout)
    except json.JSONDecodeError as exc:
        raise ProcessResilienceError(
            "supervisor canary stdout is not one JSON document"
        ) from exc
    verify_self_digest(child, "canary_digest", label="supervisor canary")
    if (
        child["argv"] != list(build_public_command("supervisor-canary"))
        or child["working_directory"] != str(ROOT)
        or child["environment"] != deterministic_environment()
    ):
        raise ProcessResilienceError(
            "supervised child argv/environment/cwd changed"
        )
    value = {
        "available": True,
        "service_name": service_name,
        "process_id": child["process_id"],
        "start_timestamp_utc": launched_at,
        "end_timestamp_utc": ended_at,
        "exact_python_argv": list(
            build_public_command("supervisor-canary")
        ),
        "systemd_argv": list(argv),
        "working_directory": str(ROOT),
        "environment": deterministic_environment(),
        "exit_status": result.returncode,
        "signal": None,
        "launcher_stdout": result.stdout,
        "launcher_stderr": result.stderr,
        "stdout_log": {
            "path": str(stdout_path),
            "sha256": sha256_file(stdout_path),
            "size": stdout_path.stat().st_size,
        },
        "stderr_log": {
            "path": str(stderr_path),
            "sha256": sha256_file(stderr_path),
            "size": stderr_path.stat().st_size,
        },
        "child": child,
        "no_wall_clock_timeout": True,
        "no_shell_transformation": True,
    }
    value["supervisor_canary_digest"] = digest(value)
    return value


def data_free_resumption_canary(root: Path) -> dict[str, Any]:
    bindings = []
    for item in unit_plan(arms=("A", "B"), seed_count=2):
        value = {
            "schema_version": "synthetic_unit_binding.v1",
            **item,
            "outcome_access": {"count": 0, "event_ids": []},
        }
        value["unit_binding_digest"] = digest(value)
        bindings.append(value)

    def compute(binding: Mapping[str, Any]) -> dict[str, Any]:
        value = {
            "schema_version": "synthetic_unit_result.v1",
            "unit_index": binding["unit_index"],
            "unit_id": binding["unit_id"],
            "unit_binding_digest": binding["unit_binding_digest"],
            "value": int(binding["unit_index"]) ** 2,
            "outcome_access": {"count": 0, "event_ids": []},
        }
        value["unit_result_digest"] = digest(value)
        return value

    interrupted = {"done": False}

    def interrupt(stage: str, index: int) -> None:
        if stage == "after_prepared" and index == 1 and not interrupted["done"]:
            interrupted["done"] = True
            raise InjectedProcessInterruption("readiness canary")

    journal = ExposureUnitJournal(root)
    try:
        execute_resumable_units(
            bindings=bindings,
            journal=journal,
            compute_unit=compute,
            interrupt=interrupt,
        )
    except InjectedProcessInterruption:
        pass
    resumed = execute_resumable_units(
        bindings=bindings,
        journal=journal,
        compute_unit=compute,
    )
    value = {
        "unit_count": len(bindings),
        "committed_unit_count": resumed["restart_plan"][
            "committed_unit_count"
        ],
        "recomputation_count": resumed["restart_plan"][
            "recomputation_count"
        ],
        "outcome_access": {"count": 0, "event_ids": []},
        "journal_chain_digest": resumed["restart_plan"][
            "journal_chain_digest"
        ],
    }
    value["canary_digest"] = digest(value)
    return value


def new_output_paths() -> tuple[Path, ...]:
    return (
        SOURCE_MANIFEST_PATH,
        ARTIFACT_BINDING_PATH,
        READINESS_PATH,
        READINESS_FAILURE_PATH,
        EXPOSURE_JOURNAL_DIR,
        EXPOSURE_PATH,
        EXECUTION_MANIFEST_PATH,
        EXPOSURE_COMPLETION_PATH,
        EXPOSURE_FAILURE_PATH,
        SCIENCE_STARTED_PATH,
        SCIENCE_JOURNAL_DIR,
        SCIENCE_CARRIER_DIR,
        RESULT_PATH,
        SCIENCE_FAILURE_PATH,
    )


def freeze_package_manifests(source_commit: str) -> dict[str, Any]:
    _require_clean_worktree()
    if _git("rev-parse", "HEAD") != source_commit:
        raise ProcessResilienceError("source freeze commit is not HEAD")
    if (ROOT / SOURCE_MANIFEST_PATH).exists() or (
        ROOT / ARTIFACT_BINDING_PATH
    ).exists():
        raise FileExistsError("process-resilience manifests already exist")
    fixed = verify_frozen_inputs()
    source = {
        "schema_version": "native_v2_process_resilience_source.v1",
        "package_id": PACKAGE_ID,
        "source_freeze_commit": source_commit,
        "source_hashes": {
            relative: sha256_file(ROOT / relative)
            for relative in SOURCE_FILES
        },
        "module_path": MODULE_PATH,
        "public_commands": {
            command: list(build_public_command(command))
            for command in PUBLIC_COMMANDS
        },
        "deterministic_environment": deterministic_environment(),
        "runtime": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "working_directory": str(ROOT),
        },
        "frozen_inputs": fixed,
        "architecture": {
            "outer_process_resilience_only": True,
            "protected_sources_unchanged": True,
            "module_global_replacement": False,
            "exposure_units": UNIT_COUNT,
            "outcomes_inaccessible_during_exposure": True,
            "science_started_before_environment": True,
            "failure_counts_derived_from_journal": True,
            "systemd_user_service_required": True,
            "no_managed_long_command_fallback": True,
        },
    }
    source["source_manifest_digest"] = digest(source)
    _atomic_json(ROOT / SOURCE_MANIFEST_PATH, source)
    binding = {
        "schema_version": "native_v2_process_resilience_binding.v1",
        "package_id": PACKAGE_ID,
        "source_manifest": {
            "path": SOURCE_MANIFEST_PATH.as_posix(),
            "sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
            "digest": source["source_manifest_digest"],
        },
        "frozen_inputs": fixed,
        "output_paths": {
            "readiness": READINESS_PATH.as_posix(),
            "readiness_failure": READINESS_FAILURE_PATH.as_posix(),
            "exposure_journal": EXPOSURE_JOURNAL_DIR.as_posix(),
            "exposure": EXPOSURE_PATH.as_posix(),
            "execution_manifest": EXECUTION_MANIFEST_PATH.as_posix(),
            "exposure_completion": EXPOSURE_COMPLETION_PATH.as_posix(),
            "exposure_failure": EXPOSURE_FAILURE_PATH.as_posix(),
            "science_started": SCIENCE_STARTED_PATH.as_posix(),
            "science_journal": SCIENCE_JOURNAL_DIR.as_posix(),
            "science_carrier": SCIENCE_CARRIER_DIR.as_posix(),
            "result": RESULT_PATH.as_posix(),
            "science_failure": SCIENCE_FAILURE_PATH.as_posix(),
        },
        "host_launch": {
            "run_exposure_python_argv": list(
                build_public_command("run-exposure")
            ),
            "run_science_python_argv": list(
                build_public_command("run-science")
            ),
            "environment": deterministic_environment(),
            "working_directory": str(ROOT),
            "stdout_stderr_outside_worktree": True,
            "no_wall_clock_timeout": True,
            "no_shell_transformation": True,
        },
        "scientific_constants": fixed["scientific_constants"],
    }
    binding["artifact_binding_digest"] = digest(binding)
    _atomic_json(ROOT / ARTIFACT_BINDING_PATH, binding)
    return {
        "source_manifest_sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
        "source_manifest_digest": source["source_manifest_digest"],
        "artifact_binding_sha256": sha256_file(
            ROOT / ARTIFACT_BINDING_PATH
        ),
        "artifact_binding_digest": binding["artifact_binding_digest"],
    }


def verify_package_manifests() -> dict[str, Any]:
    source = _load_json(ROOT / SOURCE_MANIFEST_PATH)
    source_digest = verify_self_digest(
        source, "source_manifest_digest", label="source manifest"
    )
    for relative, expected in source["source_hashes"].items():
        if sha256_file(ROOT / relative) != expected:
            raise ProcessResilienceError(f"source changed:{relative}")
    binding = _load_json(ROOT / ARTIFACT_BINDING_PATH)
    binding_digest = verify_self_digest(
        binding, "artifact_binding_digest", label="artifact binding"
    )
    if (
        binding["source_manifest"]["sha256"]
        != sha256_file(ROOT / SOURCE_MANIFEST_PATH)
        or binding["source_manifest"]["digest"] != source_digest
        or canonical_bytes(binding["frozen_inputs"])
        != canonical_bytes(verify_frozen_inputs())
    ):
        raise ProcessResilienceError("source/artifact binding changed")
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


def load_and_verify_readiness(*, committed: bool) -> dict[str, Any]:
    if committed:
        require_committed_artifact(READINESS_PATH)
    value = _load_json(ROOT / READINESS_PATH)
    verify_self_digest(value, "readiness_digest", label="readiness")
    if (
        value.get("cohort_digest") != ACCEPTED_COHORT_DIGEST
        or value.get("expanded_package_map_digest")
        != EXPANDED_PACKAGE_MAP_DIGEST
        or value.get("real_exposure_run") is not False
        or value.get("outcome_access")
        != {"count": 0, "event_ids": []}
        or value.get("supervisor_canary", {}).get("available") is not True
    ):
        raise ProcessResilienceError("readiness gate changed")
    return value


def run_readiness() -> dict[str, Any]:
    _require_clean_worktree()
    if (ROOT / READINESS_PATH).exists() or (
        ROOT / READINESS_FAILURE_PATH
    ).exists():
        raise FileExistsError("process-resilience readiness already exists")
    require_committed_artifact(SOURCE_MANIFEST_PATH)
    require_committed_artifact(ARTIFACT_BINDING_PATH)
    started = time.perf_counter()
    try:
        package = verify_package_manifests()
        fixed = verify_frozen_inputs()
        canary_root = supervisor_log_root() / "readiness"
        supervisor = run_supervised_canary(log_root=canary_root)
        journal_canary = data_free_resumption_canary(
            Path("/tmp")
            / f"recon-v2-resilience-readiness-{os.getpid()}"
        )
        value = {
            "schema_version": "native_v2_process_resilience_readiness.v1",
            "package_id": PACKAGE_ID,
            "source_manifest": {
                "sha256": package["source_manifest_sha256"],
                "digest": package["source_manifest_digest"],
            },
            "artifact_binding": {
                "sha256": package["artifact_binding_sha256"],
                "digest": package["artifact_binding_digest"],
            },
            "public_command": list(
                build_public_command("verify-readiness")
            ),
            "working_directory": str(ROOT),
            "python_executable": sys.executable,
            "cohort_digest": ACCEPTED_COHORT_DIGEST,
            "expanded_package_map_digest": EXPANDED_PACKAGE_MAP_DIGEST,
            "verified_seed_count": SEED_COUNT,
            "verified_organism_count": UNIT_COUNT,
            "unit_plan_digest": fixed["unit_plan_digest"],
            "supervisor_canary": supervisor,
            "resumption_canary": journal_canary,
            "manual_persistent_commands": {
                command: manual_persistent_commands(command)
                for command in ("run-exposure", "run-science")
            },
            "real_exposure_run": False,
            "real_outcome_run": False,
            "outcome_access": {"count": 0, "event_ids": []},
            "protected_source_changes": 0,
            "module_global_replacement_count": 0,
            "elapsed_seconds": round(time.perf_counter() - started, 6),
        }
        value["readiness_digest"] = digest(value)
        _atomic_json(ROOT / READINESS_PATH, value)
        return value
    except Exception as exc:
        record_failure(READINESS_FAILURE_PATH, "verify-readiness", exc)
        raise


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
    commands.add_parser("supervisor-canary")
    args = parser.parse_args(argv)
    if args.command == "freeze-manifests":
        value = freeze_package_manifests(args.source_commit)
    elif args.command == "verify-readiness":
        value = run_readiness()
    elif args.command == "run-exposure":
        value = run_exposure()
    elif args.command == "run-science":
        value = run_science()
    elif args.command == "supervisor-canary":
        value = supervisor_canary_child()
    else:  # pragma: no cover
        raise AssertionError(args.command)
    _print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
