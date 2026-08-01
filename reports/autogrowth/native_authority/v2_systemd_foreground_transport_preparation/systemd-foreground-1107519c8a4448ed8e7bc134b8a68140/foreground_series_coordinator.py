#!/usr/bin/env python3
"""Foreground-only systemd coordinator for one frozen admission series.

This transport program imports no ReCoN module.  The systemd service owns this
process directly; it runs each frozen command synchronously and never retries.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Mapping, Sequence


ZERO_OUTCOME = {"count": 0, "event_ids": []}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def pretty_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.systemd-series.tmp")
    if temporary.exists():
        raise RuntimeError(f"ambiguous coordinator temporary:{temporary}")
    with temporary.open("xb") as handle:
        handle.write(pretty_bytes(value))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object:{path}")
    return value


def load_manifest(path: Path, expected_sha256: str) -> dict[str, Any]:
    if sha256_file(path) != expected_sha256:
        raise RuntimeError("outer manifest hash mismatch")
    manifest = load_json(path)
    if manifest["schema_version"] != "native_v2_systemd_foreground_series.v1":
        raise RuntimeError("outer manifest schema mismatch")
    coordinator = Path(manifest["coordinator"]["path"])
    if coordinator.resolve() != Path(__file__).resolve():
        raise RuntimeError("coordinator path mismatch")
    if sha256_file(coordinator) != manifest["coordinator"]["sha256"]:
        raise RuntimeError("coordinator hash mismatch")
    if str(Path(sys.executable).absolute()) != manifest["canonical_interpreter"]:
        raise RuntimeError(f"noncanonical interpreter:{sys.executable}")
    if Path.cwd().resolve() != Path(
        manifest["canonical_repository_root"]
    ).resolve():
        raise RuntimeError(f"noncanonical working directory:{Path.cwd()}")
    return manifest


def git(root: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ("git", *arguments), cwd=root, text=True, stderr=subprocess.STDOUT
    ).strip()


def git_bytes(root: Path, object_name: str) -> bytes:
    return subprocess.check_output(("git", "show", object_name), cwd=root)


def verify_prior_records(root: Path, manifest: Mapping[str, Any]) -> None:
    for preservation in manifest["preservation_refs"]:
        commit = preservation["commit"]
        if git(root, "rev-parse", commit) != commit:
            raise RuntimeError(f"preservation ref changed:{commit}")
        for path, expected in preservation["record_hashes"].items():
            observed = sha256_bytes(git_bytes(root, f"{commit}:{path}"))
            if observed != expected:
                raise RuntimeError(
                    f"preserved record changed:{commit}:{path}:{observed}"
                )


def verify_frozen_files(root: Path, manifest: Mapping[str, Any]) -> None:
    for relative, expected in manifest["frozen_files"].items():
        observed = sha256_file(root / relative)
        if observed != expected:
            raise RuntimeError(f"frozen file changed:{relative}:{observed}")


def verify_protected_files(root: Path, manifest: Mapping[str, Any]) -> None:
    specification = manifest["protected_files"]
    dependency_path = root / specification["dependency_manifest_path"]
    if sha256_file(dependency_path) != specification["dependency_manifest_sha256"]:
        raise RuntimeError("protected dependency manifest changed")
    dependencies = load_json(dependency_path)
    expected = dependencies["protected_files"]
    observed = {
        relative: sha256_file(root / relative)
        for relative in sorted(expected)
    }
    if observed != expected:
        raise RuntimeError("protected file map changed")
    if len(observed) != specification["count"]:
        raise RuntimeError("protected file count changed")
    if digest(observed) != specification["set_digest"]:
        raise RuntimeError("protected file-set digest changed")


def verify_module_paths(manifest: Mapping[str, Any]) -> None:
    for name, value in manifest["modules"].items():
        specification = importlib.util.find_spec(value["module"])
        if specification is None or specification.origin is None:
            raise RuntimeError(f"module cannot resolve:{name}")
        observed = str(Path(specification.origin).resolve())
        if observed != value["resolved_path"]:
            raise RuntimeError(
                f"module path changed:{name}:expected={value['resolved_path']}:"
                f"observed={observed}"
            )


def verify_science_absent(root: Path, manifest: Mapping[str, Any]) -> None:
    unexpected = [
        relative
        for relative in manifest["science_paths_required_absent"]
        if (root / relative).exists()
    ]
    if unexpected:
        raise RuntimeError(f"science path exists:{unexpected}")


def verify_no_bridge_temporaries(root: Path, manifest: Mapping[str, Any]) -> None:
    package = root / Path(manifest["child_attempt_root"]).parent
    temporaries = sorted(package.rglob("*.portable-admission.tmp"))
    if temporaries:
        raise RuntimeError(
            f"bridge temporary exists:{[str(path) for path in temporaries]}"
        )


def verify_attempts_absent(root: Path, manifest: Mapping[str, Any]) -> None:
    attempt_root = root / manifest["child_attempt_root"]
    existing = [
        entry["child_slot"]
        for entry in manifest["executions"]
        if (attempt_root / entry["child_slot"]).exists()
    ]
    if existing:
        raise RuntimeError(f"pre-existing child attempt directories:{existing}")


def verify_environment(manifest: Mapping[str, Any], *, service: bool) -> None:
    expected = dict(manifest["coordinator_environment"])
    for key, value in expected.items():
        if os.environ.get(key) != value:
            raise RuntimeError(
                f"coordinator environment mismatch:{key}:"
                f"expected={value}:observed={os.environ.get(key)}"
            )
    if service and not os.environ.get("INVOCATION_ID"):
        raise RuntimeError("systemd invocation identity is absent")


def parse_systemd_properties(output: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in output.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def verify_service_contract(manifest: Mapping[str, Any]) -> dict[str, Any]:
    unit = manifest["systemd"]["unit_name"]
    output = subprocess.check_output(
        (
            "systemctl",
            "--user",
            "show",
            unit,
            "--property=Id,Type,Restart,RuntimeMaxUSec,WorkingDirectory,MainPID,ActiveState,SubState",
            "--no-pager",
        ),
        text=True,
        stderr=subprocess.STDOUT,
    )
    values = parse_systemd_properties(output)
    required = {
        "Id": unit,
        "Type": "exec",
        "Restart": "no",
        "RuntimeMaxUSec": "infinity",
        "WorkingDirectory": manifest["canonical_repository_root"],
        "MainPID": str(os.getpid()),
    }
    for key, expected in required.items():
        if values.get(key) != expected:
            raise RuntimeError(
                f"systemd contract mismatch:{key}:"
                f"expected={expected}:observed={values.get(key)}"
            )
    if values.get("ActiveState") not in {"activating", "active"}:
        raise RuntimeError(
            f"systemd service not active:{values.get('ActiveState')}"
        )
    return values


def complete_preflight(
    manifest: Mapping[str, Any], *, require_service: bool
) -> dict[str, Any]:
    root = Path(manifest["canonical_repository_root"])
    verify_environment(manifest, service=require_service)
    head = git(root, "rev-parse", "HEAD")
    if head != manifest["frozen_child_package_commit"]:
        raise RuntimeError(f"frozen HEAD changed:{head}")
    status = git(root, "status", "--porcelain=v1", "--untracked-files=all")
    if status:
        raise RuntimeError(f"canonical worktree is not clean:{status}")
    verify_prior_records(root, manifest)
    verify_frozen_files(root, manifest)
    verify_protected_files(root, manifest)
    verify_module_paths(manifest)
    verify_science_absent(root, manifest)
    verify_attempts_absent(root, manifest)
    verify_no_bridge_temporaries(root, manifest)
    service_contract = (
        verify_service_contract(manifest) if require_service else None
    )
    return {
        "schema_version": "native_v2_systemd_foreground_preflight.v1",
        "recovery_series_id": manifest["recovery_series_id"],
        "head": head,
        "canonical_repository_root": str(root),
        "canonical_interpreter": sys.executable,
        "pythonpath": os.environ["PYTHONPATH"],
        "protected_file_count": manifest["protected_files"]["count"],
        "protected_file_set_digest": manifest["protected_files"]["set_digest"],
        "module_paths": {
            name: value["resolved_path"]
            for name, value in manifest["modules"].items()
        },
        "service_contract": service_contract,
        "outcome_access": dict(ZERO_OUTCOME),
    }


def verify_untracked_outputs(
    root: Path,
    manifest: Mapping[str, Any],
    completed_slots: Sequence[str],
) -> None:
    status = git(root, "status", "--porcelain=v1", "--untracked-files=all")
    if not status:
        if completed_slots:
            raise RuntimeError("completed child outputs are unexpectedly absent")
        return
    allowed_prefixes = tuple(
        f"{manifest['child_attempt_root']}/{slot}/"
        for slot in completed_slots
    )
    for line in status.splitlines():
        if not line.startswith("?? "):
            raise RuntimeError(f"tracked canonical state changed:{line}")
        relative = line[3:]
        if not relative.startswith(allowed_prefixes):
            raise RuntimeError(f"foreign untracked canonical path:{relative}")


def verify_after_task(
    root: Path,
    manifest: Mapping[str, Any],
    completed_slots: Sequence[str],
) -> None:
    if git(root, "rev-parse", "HEAD") != manifest["frozen_child_package_commit"]:
        raise RuntimeError("HEAD changed during series")
    verify_frozen_files(root, manifest)
    verify_protected_files(root, manifest)
    verify_science_absent(root, manifest)
    verify_no_bridge_temporaries(root, manifest)
    verify_untracked_outputs(root, manifest, completed_slots)


def task_paths(record_root: Path, task_name: str) -> dict[str, Path]:
    return {
        "launch": record_root / f"{task_name}_launch.json",
        "terminal": record_root / f"{task_name}_terminal.json",
        "stdout": record_root / f"{task_name}.stdout",
        "stderr": record_root / f"{task_name}.stderr",
    }


def run_command(
    *,
    command: Sequence[str],
    cwd: Path,
    environment: Mapping[str, str],
    record_root: Path,
    task_name: str,
    used_pids: set[int],
) -> dict[str, Any]:
    paths = task_paths(record_root, task_name)
    if any(path.exists() for path in paths.values()):
        raise RuntimeError(f"task record already exists:{task_name}")
    with paths["stdout"].open("xb") as stdout_handle, paths["stderr"].open(
        "xb"
    ) as stderr_handle:
        started_at = utc_now()
        started_monotonic = time.monotonic()
        process = subprocess.Popen(
            list(command),
            cwd=cwd,
            env=dict(environment),
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
        )
        if process.pid in used_pids:
            process.terminate()
            process.wait()
            raise RuntimeError(f"child PID reused:{process.pid}")
        used_pids.add(process.pid)
        launch = {
            "schema_version": "native_v2_systemd_foreground_task_launch.v1",
            "task_name": task_name,
            "command": list(command),
            "pid": process.pid,
            "cwd": str(cwd),
            "environment_digest": digest(dict(environment)),
            "started_at_utc": started_at,
        }
        launch["record_digest"] = digest(launch)
        atomic_write(paths["launch"], launch)
        returncode = process.wait()
    terminal = {
        "schema_version": "native_v2_systemd_foreground_task_terminal.v1",
        "task_name": task_name,
        "pid": process.pid,
        "returncode": returncode,
        "signal": -returncode if returncode < 0 else None,
        "started_at_utc": started_at,
        "ended_at_utc": utc_now(),
        "elapsed_seconds": time.monotonic() - started_monotonic,
        "stdout_path": str(paths["stdout"]),
        "stdout_size": paths["stdout"].stat().st_size,
        "stdout_sha256": sha256_file(paths["stdout"]),
        "stderr_path": str(paths["stderr"]),
        "stderr_size": paths["stderr"].stat().st_size,
        "stderr_sha256": sha256_file(paths["stderr"]),
        "launch_record_digest": launch["record_digest"],
    }
    terminal["record_digest"] = digest(terminal)
    atomic_write(paths["terminal"], terminal)
    return terminal


def verify_child_directory(
    root: Path,
    manifest: Mapping[str, Any],
    child_slot: str,
) -> dict[str, Any]:
    attempt = root / manifest["child_attempt_root"] / child_slot
    expected_names = {
        "00_started.json",
        "01_historical_journal_verified.json",
        "progress.json",
        "result.json",
    }
    if not attempt.is_dir():
        raise RuntimeError(f"child attempt directory absent:{child_slot}")
    actual_names = {path.name for path in attempt.iterdir()}
    if actual_names != expected_names:
        raise RuntimeError(
            f"child directory shape mismatch:{child_slot}:{sorted(actual_names)}"
        )
    progress = load_json(attempt / "progress.json")
    result = load_json(attempt / "result.json")
    if progress.get("completed_unit_count") != 96:
        raise RuntimeError(f"child progress incomplete:{child_slot}")
    fresh = result.get("fresh_verification", {})
    required_counts = {
        "complete_semantic_identity_count": 96,
        "portable_binding_count": 96,
        "portable_unit_result_count": 96,
        "mutation_count": 0,
    }
    for key, expected in required_counts.items():
        if fresh.get(key) != expected:
            raise RuntimeError(
                f"child result gate failed:{child_slot}:{key}:{fresh.get(key)}"
            )
    if len(result.get("historical_registries", {})) != 3:
        raise RuntimeError(f"historical registry count changed:{child_slot}")
    if result.get("outcome_access") != ZERO_OUTCOME:
        raise RuntimeError(f"child outcome access changed:{child_slot}")
    if result.get("protected_files") != {
        "file_count": manifest["protected_files"]["count"],
        "file_set_digest": manifest["protected_files"]["set_digest"],
    }:
        raise RuntimeError(f"child protected set changed:{child_slot}")
    return {
        "child_slot": child_slot,
        "files": {
            name: sha256_file(attempt / name) for name in sorted(expected_names)
        },
        "portable_cohort_digest": fresh["portable_cohort_digest"],
        "outcome_access": dict(ZERO_OUTCOME),
    }


def load_successful_json_stdout(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        raise RuntimeError(f"{label} stdout is not exact JSON") from error
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} stdout is not a JSON object")
    if value.get("outcome_access") != ZERO_OUTCOME:
        raise RuntimeError(f"{label} reported outcome access")
    return value


def series_terminal(
    manifest: Mapping[str, Any],
    *,
    classification: str,
    status: str,
    task_records: Sequence[Mapping[str, Any]],
    used_pids: set[int],
    error: BaseException | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema_version": "native_v2_systemd_foreground_series_terminal.v1",
        "recovery_series_id": manifest["recovery_series_id"],
        "systemd_unit": manifest["systemd"]["unit_name"],
        "status": status,
        "classification": classification,
        "task_count": len(task_records),
        "task_record_digests": [row["record_digest"] for row in task_records],
        "distinct_child_pids": sorted(used_pids),
        "outcome_access": dict(ZERO_OUTCOME),
        "ended_at_utc": utc_now(),
    }
    if error is not None:
        value.update(
            {
                "error_type": type(error).__name__,
                "error": str(error),
                "traceback_tail": traceback.format_exc().splitlines()[-20:],
            }
        )
    value["record_digest"] = digest(value)
    return value


def run_series(manifest_path: Path, manifest_sha256: str) -> int:
    manifest = load_manifest(manifest_path, manifest_sha256)
    root = Path(manifest["canonical_repository_root"])
    record_root = Path(manifest["record_root"])
    if record_root.exists():
        raise RuntimeError(f"series record root already exists:{record_root}")
    record_root.mkdir(parents=True, exist_ok=False)
    task_records: list[dict[str, Any]] = []
    used_pids: set[int] = set()
    completed_slots: list[str] = []
    interrupted: dict[str, Any] = {}

    def on_signal(signum: int, _frame: Any) -> None:
        interrupted.update(
            {
                "schema_version": "native_v2_systemd_foreground_interruption.v1",
                "recovery_series_id": manifest["recovery_series_id"],
                "signal": signum,
                "recorded_at_utc": utc_now(),
                "outcome_access": dict(ZERO_OUTCOME),
            }
        )
        interrupted["record_digest"] = digest(interrupted)
        path = record_root / "series_interrupted.json"
        if not path.exists():
            atomic_write(path, interrupted)
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)
    try:
        preflight = complete_preflight(manifest, require_service=True)
        preflight["record_digest"] = digest(preflight)
        atomic_write(record_root / "preflight.json", preflight)
        started = {
            "schema_version": "native_v2_systemd_foreground_series_started.v1",
            "recovery_series_id": manifest["recovery_series_id"],
            "systemd_unit": manifest["systemd"]["unit_name"],
            "coordinator_pid": os.getpid(),
            "systemd_invocation_id": os.environ["INVOCATION_ID"],
            "started_at_utc": utc_now(),
            "manifest_sha256": manifest_sha256,
            "outcome_access": dict(ZERO_OUTCOME),
        }
        started["record_digest"] = digest(started)
        atomic_write(record_root / "series_started.json", started)
        child_environment = dict(manifest["child_environment"])
        for entry in manifest["executions"]:
            child_name = f"slot-{entry['sequence']:02d}-child"
            child_terminal = run_command(
                command=entry["child_command"],
                cwd=root,
                environment=child_environment,
                record_root=record_root,
                task_name=child_name,
                used_pids=used_pids,
            )
            task_records.append(child_terminal)
            if child_terminal["returncode"] != 0:
                raise RuntimeError(f"child stopped nonzero:{entry['child_slot']}")
            completed_slots.append(entry["child_slot"])
            child_result = verify_child_directory(
                root, manifest, entry["child_slot"]
            )
            child_result["record_digest"] = digest(child_result)
            atomic_write(
                record_root / f"slot-{entry['sequence']:02d}-child-check.json",
                child_result,
            )
            verify_after_task(root, manifest, completed_slots)

            verifier_name = f"slot-{entry['sequence']:02d}-verifier"
            verifier_terminal = run_command(
                command=entry["verifier_command"],
                cwd=root,
                environment=child_environment,
                record_root=record_root,
                task_name=verifier_name,
                used_pids=used_pids,
            )
            task_records.append(verifier_terminal)
            if verifier_terminal["returncode"] != 0:
                raise RuntimeError(
                    f"verifier stopped nonzero:{entry['child_slot']}"
                )
            verifier_value = load_successful_json_stdout(
                task_paths(record_root, verifier_name)["stdout"],
                label=verifier_name,
            )
            if task_paths(record_root, verifier_name)["stderr"].stat().st_size:
                raise RuntimeError(f"verifier stderr is not empty:{verifier_name}")
            if verifier_value.get("attempt_id") != entry["child_slot"]:
                raise RuntimeError(f"verifier attempt identity changed:{verifier_name}")
            verify_after_task(root, manifest, completed_slots)

        aggregate_terminal = run_command(
            command=manifest["aggregate_command"],
            cwd=root,
            environment=child_environment,
            record_root=record_root,
            task_name="aggregate-verifier",
            used_pids=used_pids,
        )
        task_records.append(aggregate_terminal)
        if aggregate_terminal["returncode"] != 0:
            raise RuntimeError("aggregate verifier stopped nonzero")
        aggregate = load_successful_json_stdout(
            task_paths(record_root, "aggregate-verifier")["stdout"],
            label="aggregate-verifier",
        )
        if task_paths(record_root, "aggregate-verifier")["stderr"].stat().st_size:
            raise RuntimeError("aggregate verifier stderr is not empty")
        if aggregate.get("attempt_count") != 3:
            raise RuntimeError("aggregate attempt count changed")
        if len(aggregate.get("attempts", [])) != 3:
            raise RuntimeError("aggregate attempt identities changed")
        verify_after_task(root, manifest, completed_slots)
        terminal = series_terminal(
            manifest,
            classification=(
                "Canonical-path portable admission and exact historical "
                "reconstruction passed across three independently identified "
                "executions."
            ),
            status="passed",
            task_records=task_records,
            used_pids=used_pids,
        )
        atomic_write(record_root / "series_terminal.json", terminal)
        return 0
    except BaseException as error:
        terminal_path = record_root / "series_terminal.json"
        if not terminal_path.exists() and not isinstance(error, SystemExit):
            terminal = series_terminal(
                manifest,
                classification="terminal transport or admission stop",
                status="failed",
                task_records=task_records,
                used_pids=used_pids,
                error=error,
            )
            atomic_write(terminal_path, terminal)
        if isinstance(error, SystemExit):
            raise
        return 1


def read_only_status(manifest_path: Path, manifest_sha256: str) -> dict[str, Any]:
    manifest = load_manifest(manifest_path, manifest_sha256)
    record_root = Path(manifest["record_root"])
    records = {
        path.name: sha256_file(path)
        for path in sorted(record_root.glob("*.json"))
        if path.is_file()
    } if record_root.is_dir() else {}
    try:
        output = subprocess.check_output(
            (
                "systemctl",
                "--user",
                "show",
                manifest["systemd"]["unit_name"],
                "--property=Id,LoadState,ActiveState,SubState,Result,ExecMainCode,ExecMainStatus,MainPID,Type,Restart,RuntimeMaxUSec,WorkingDirectory",
                "--no-pager",
            ),
            text=True,
            stderr=subprocess.STDOUT,
        )
        service = parse_systemd_properties(output)
        service_error = None
    except subprocess.CalledProcessError as error:
        service = {}
        service_error = error.output.strip()
    return {
        "recovery_series_id": manifest["recovery_series_id"],
        "unit": manifest["systemd"]["unit_name"],
        "service": service,
        "service_error": service_error,
        "record_hashes": records,
        "terminal_record_present": (record_root / "series_terminal.json").is_file(),
    }


def finalize(manifest_path: Path, manifest_sha256: str) -> dict[str, Any]:
    manifest = load_manifest(manifest_path, manifest_sha256)
    record_root = Path(manifest["record_root"])
    finalization_path = record_root / "finalization.json"
    if finalization_path.exists():
        value = load_json(finalization_path)
        if value.get("record_digest") != digest(
            {key: item for key, item in value.items() if key != "record_digest"}
        ):
            raise RuntimeError("existing finalization digest mismatch")
        return value
    terminal_path = record_root / "series_terminal.json"
    interruption_path = record_root / "series_interrupted.json"
    if not terminal_path.exists() and not interruption_path.exists():
        raise RuntimeError("series has no terminal or interruption record")
    status = read_only_status(manifest_path, manifest_sha256)
    if status["service"].get("ActiveState") in {"active", "activating"}:
        raise RuntimeError("cannot finalize an active service")
    records = {
        path.name: sha256_file(path)
        for path in sorted(record_root.iterdir())
        if path.is_file()
    }
    value = {
        "schema_version": "native_v2_systemd_foreground_finalization.v1",
        "recovery_series_id": manifest["recovery_series_id"],
        "unit": manifest["systemd"]["unit_name"],
        "service": status["service"],
        "service_error": status["service_error"],
        "record_hashes": records,
        "finalized_at_utc": utc_now(),
        "outcome_access": dict(ZERO_OUTCOME),
    }
    value["record_digest"] = digest(value)
    atomic_write(finalization_path, value)
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight-only", "run-series", "status", "finalize"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--manifest", required=True)
        sub.add_argument("--manifest-sha256", required=True)
    arguments = parser.parse_args(argv)
    manifest_path = Path(arguments.manifest).resolve()
    if arguments.command == "preflight-only":
        manifest = load_manifest(manifest_path, arguments.manifest_sha256)
        value = complete_preflight(manifest, require_service=False)
        print(json.dumps(value, sort_keys=True, indent=2))
        return 0
    if arguments.command == "run-series":
        return run_series(manifest_path, arguments.manifest_sha256)
    if arguments.command == "status":
        value = read_only_status(manifest_path, arguments.manifest_sha256)
    elif arguments.command == "finalize":
        value = finalize(manifest_path, arguments.manifest_sha256)
    else:
        raise RuntimeError("unknown coordinator command")
    print(json.dumps(value, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
