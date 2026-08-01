#!/usr/bin/env python3
"""Detached transport controller for one frozen canonical-path recovery series."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any


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


def atomic_write(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.outer-recovery.tmp")
    if temporary.exists():
        raise RuntimeError(f"ambiguous outer temporary:{temporary}")
    payload = pretty_bytes(value)
    with temporary.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def load_manifest(path: Path, expected_sha256: str) -> dict[str, Any]:
    if sha256_file(path) != expected_sha256:
        raise RuntimeError("outer recovery manifest hash mismatch")
    value = json.loads(path.read_text(encoding="utf-8"))
    controller = Path(value["controller"]["path"])
    if controller.resolve() != Path(__file__).resolve():
        raise RuntimeError("outer controller path mismatch")
    if sha256_file(controller) != value["controller"]["sha256"]:
        raise RuntimeError("outer controller hash mismatch")
    if str(Path(sys.executable).absolute()) != value["canonical_interpreter"]:
        raise RuntimeError(
            f"noncanonical interpreter:{sys.executable}"
        )
    root = Path(value["canonical_repository_root"])
    if Path.cwd().resolve() != root.resolve():
        raise RuntimeError(f"noncanonical cwd:{Path.cwd().resolve()}")
    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=root, text=True
    ).strip()
    if head != value["frozen_child_package_commit"]:
        raise RuntimeError(f"frozen HEAD changed:{head}")
    return value


def execution_entry(
    manifest: dict[str, Any], outer_execution_id: str
) -> tuple[int, dict[str, Any]]:
    matches = [
        (index, entry)
        for index, entry in enumerate(manifest["executions"])
        if entry["outer_execution_id"] == outer_execution_id
    ]
    if len(matches) != 1:
        raise RuntimeError("unknown or ambiguous outer execution ID")
    return matches[0]


def execution_dir(manifest_path: Path, outer_execution_id: str) -> Path:
    return manifest_path.parent / "executions" / outer_execution_id


def task_paths(base: Path, task: str) -> dict[str, Path]:
    return {
        "launch": base / f"{task}_launch.json",
        "terminal": base / f"{task}_terminal.json",
        "stdout": base / f"{task}.stdout",
        "stderr": base / f"{task}.stderr",
        "supervisor_stdout": base / f"{task}_supervisor.stdout",
        "supervisor_stderr": base / f"{task}_supervisor.stderr",
        "supervisor_launch": base / f"{task}_supervisor_launch.json",
        "supervisor_failure": base / f"{task}_supervisor_failure.json",
    }


def require_terminal_success(base: Path, task: str) -> dict[str, Any]:
    paths = task_paths(base, task)
    if paths["supervisor_failure"].exists():
        raise RuntimeError(f"prior {task} supervisor failed")
    if not paths["terminal"].is_file():
        raise RuntimeError(f"prior {task} has no terminal record")
    value = json.loads(paths["terminal"].read_text(encoding="utf-8"))
    if value["returncode"] != 0 or value["signal"] is not None:
        raise RuntimeError(f"prior {task} did not succeed")
    return value


def child_attempt_dir(manifest: dict[str, Any], child_slot: str) -> Path:
    return (
        Path(manifest["canonical_repository_root"])
        / "reports/autogrowth/native_authority/v2_portable_admission_bridge"
        / "attempts"
        / child_slot
    )


def validate_sequential_gate(
    manifest_path: Path,
    manifest: dict[str, Any],
    index: int,
    entry: dict[str, Any],
    task: str,
) -> None:
    if task == "child":
        if index:
            previous = manifest["executions"][index - 1]
            previous_dir = execution_dir(
                manifest_path, previous["outer_execution_id"]
            )
            require_terminal_success(previous_dir, "verifier")
        attempt = child_attempt_dir(manifest, entry["child_slot"])
        if attempt.exists():
            raise RuntimeError(f"pre-existing child attempt directory:{attempt}")
    elif task == "verifier":
        current = execution_dir(manifest_path, entry["outer_execution_id"])
        require_terminal_success(current, "child")
        attempt = child_attempt_dir(manifest, entry["child_slot"])
        names = sorted(path.name for path in attempt.iterdir())
        expected = sorted(
            [
                "00_started.json",
                "01_historical_journal_verified.json",
                "progress.json",
                "result.json",
            ]
        )
        if names != expected:
            raise RuntimeError(f"passing child directory shape mismatch:{names}")
    else:
        raise RuntimeError(f"unknown execution task:{task}")


def command_for(
    manifest: dict[str, Any], entry: dict[str, Any], task: str
) -> list[str]:
    if task == "child":
        return list(entry["child_command"])
    if task == "verifier":
        return list(entry["verifier_command"])
    raise RuntimeError(f"unknown execution task:{task}")


def launch_supervisor(
    manifest_path: Path,
    manifest_sha256: str,
    outer_execution_id: str,
    task: str,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path, manifest_sha256)
    index, entry = execution_entry(manifest, outer_execution_id)
    base = execution_dir(manifest_path, outer_execution_id)
    if task == "child":
        base.mkdir(parents=True, exist_ok=False)
    elif not base.is_dir():
        raise RuntimeError("outer execution directory is absent")
    validate_sequential_gate(manifest_path, manifest, index, entry, task)
    paths = task_paths(base, task)
    if any(path.exists() for path in paths.values()):
        raise RuntimeError(f"outer {task} records already exist")
    supervisor_command = [
        manifest["canonical_interpreter"],
        str(Path(__file__).resolve()),
        "supervise",
        "--manifest",
        str(manifest_path),
        "--manifest-sha256",
        manifest_sha256,
        "--outer-execution-id",
        outer_execution_id,
        "--task",
        task,
    ]
    environment = dict(manifest["deterministic_environment"])
    with paths["supervisor_stdout"].open("xb") as stdout_handle, paths[
        "supervisor_stderr"
    ].open("xb") as stderr_handle:
        process = subprocess.Popen(
            supervisor_command,
            cwd=manifest["canonical_repository_root"],
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
            start_new_session=True,
        )
    record = {
        "schema_version": "native_v2_outer_supervisor_launch.v1",
        "recovery_series_id": manifest["recovery_series_id"],
        "outer_execution_id": outer_execution_id,
        "child_slot": entry["child_slot"],
        "task": task,
        "supervisor_pid": process.pid,
        "supervisor_command": supervisor_command,
        "start_new_session": True,
        "started_at_utc": utc_now(),
        "manifest_sha256": manifest_sha256,
        "controller_sha256": manifest["controller"]["sha256"],
    }
    record["record_digest"] = sha256_bytes(canonical_bytes(record))
    atomic_write(paths["supervisor_launch"], record)
    return record


def supervise(
    manifest_path: Path,
    manifest_sha256: str,
    outer_execution_id: str,
    task: str,
) -> int:
    base: Path | None = None
    try:
        manifest = load_manifest(manifest_path, manifest_sha256)
        index, entry = execution_entry(manifest, outer_execution_id)
        base = execution_dir(manifest_path, outer_execution_id)
        validate_sequential_gate(manifest_path, manifest, index, entry, task)
        paths = task_paths(base, task)
        command = command_for(manifest, entry, task)
        environment = dict(manifest["deterministic_environment"])
        with paths["stdout"].open("xb") as stdout_handle, paths[
            "stderr"
        ].open("xb") as stderr_handle:
            started_at = utc_now()
            process = subprocess.Popen(
                command,
                cwd=manifest["canonical_repository_root"],
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout_handle,
                stderr=stderr_handle,
                start_new_session=True,
            )
            launch = {
                "schema_version": "native_v2_outer_task_launch.v1",
                "recovery_series_id": manifest["recovery_series_id"],
                "outer_execution_id": outer_execution_id,
                "child_slot": entry["child_slot"],
                "task": task,
                "pid": process.pid,
                "session_id": os.getsid(process.pid),
                "command": command,
                "cwd": manifest["canonical_repository_root"],
                "environment": environment,
                "environment_digest": sha256_bytes(canonical_bytes(environment)),
                "manifest_sha256": manifest_sha256,
                "controller_sha256": manifest["controller"]["sha256"],
                "start_new_session": True,
                "started_at_utc": started_at,
            }
            launch["record_digest"] = sha256_bytes(canonical_bytes(launch))
            atomic_write(paths["launch"], launch)
            returncode = process.wait()
        terminal = {
            "schema_version": "native_v2_outer_task_terminal.v1",
            "recovery_series_id": manifest["recovery_series_id"],
            "outer_execution_id": outer_execution_id,
            "child_slot": entry["child_slot"],
            "task": task,
            "pid": process.pid,
            "returncode": returncode,
            "signal": -returncode if returncode < 0 else None,
            "started_at_utc": started_at,
            "ended_at_utc": utc_now(),
            "stdout_size": paths["stdout"].stat().st_size,
            "stdout_sha256": sha256_file(paths["stdout"]),
            "stderr_size": paths["stderr"].stat().st_size,
            "stderr_sha256": sha256_file(paths["stderr"]),
            "manifest_sha256": manifest_sha256,
            "launch_record_digest": launch["record_digest"],
        }
        if task == "child":
            attempt = child_attempt_dir(manifest, entry["child_slot"])
            terminal["child_attempt_files"] = {
                path.name: sha256_file(path)
                for path in sorted(attempt.glob("*"))
                if path.is_file()
            } if attempt.is_dir() else {}
        terminal["record_digest"] = sha256_bytes(canonical_bytes(terminal))
        atomic_write(paths["terminal"], terminal)
        return 0
    except BaseException as error:
        if base is not None:
            failure_path = task_paths(base, task)["supervisor_failure"]
            if not failure_path.exists():
                failure = {
                    "schema_version": "native_v2_outer_supervisor_failure.v1",
                    "outer_execution_id": outer_execution_id,
                    "task": task,
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "ended_at_utc": utc_now(),
                }
                failure["record_digest"] = sha256_bytes(canonical_bytes(failure))
                atomic_write(failure_path, failure)
        raise


def launch_aggregate(manifest_path: Path, manifest_sha256: str) -> dict[str, Any]:
    manifest = load_manifest(manifest_path, manifest_sha256)
    for entry in manifest["executions"]:
        base = execution_dir(manifest_path, entry["outer_execution_id"])
        require_terminal_success(base, "verifier")
    base = manifest_path.parent / "aggregate"
    base.mkdir(exist_ok=False)
    paths = task_paths(base, "aggregate")
    supervisor_command = [
        manifest["canonical_interpreter"],
        str(Path(__file__).resolve()),
        "supervise-aggregate",
        "--manifest",
        str(manifest_path),
        "--manifest-sha256",
        manifest_sha256,
    ]
    environment = dict(manifest["deterministic_environment"])
    with paths["supervisor_stdout"].open("xb") as stdout_handle, paths[
        "supervisor_stderr"
    ].open("xb") as stderr_handle:
        process = subprocess.Popen(
            supervisor_command,
            cwd=manifest["canonical_repository_root"],
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
            start_new_session=True,
        )
    record = {
        "schema_version": "native_v2_outer_supervisor_launch.v1",
        "recovery_series_id": manifest["recovery_series_id"],
        "task": "aggregate",
        "supervisor_pid": process.pid,
        "supervisor_command": supervisor_command,
        "start_new_session": True,
        "started_at_utc": utc_now(),
        "manifest_sha256": manifest_sha256,
        "controller_sha256": manifest["controller"]["sha256"],
    }
    record["record_digest"] = sha256_bytes(canonical_bytes(record))
    atomic_write(paths["supervisor_launch"], record)
    return record


def supervise_aggregate(manifest_path: Path, manifest_sha256: str) -> int:
    manifest = load_manifest(manifest_path, manifest_sha256)
    base = manifest_path.parent / "aggregate"
    paths = task_paths(base, "aggregate")
    try:
        for entry in manifest["executions"]:
            require_terminal_success(
                execution_dir(manifest_path, entry["outer_execution_id"]),
                "verifier",
            )
        command = list(manifest["aggregate_command"])
        environment = dict(manifest["deterministic_environment"])
        with paths["stdout"].open("xb") as stdout_handle, paths[
            "stderr"
        ].open("xb") as stderr_handle:
            started_at = utc_now()
            process = subprocess.Popen(
                command,
                cwd=manifest["canonical_repository_root"],
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout_handle,
                stderr=stderr_handle,
                start_new_session=True,
            )
            launch = {
                "schema_version": "native_v2_outer_task_launch.v1",
                "recovery_series_id": manifest["recovery_series_id"],
                "task": "aggregate",
                "pid": process.pid,
                "session_id": os.getsid(process.pid),
                "command": command,
                "cwd": manifest["canonical_repository_root"],
                "environment": environment,
                "environment_digest": sha256_bytes(canonical_bytes(environment)),
                "manifest_sha256": manifest_sha256,
                "controller_sha256": manifest["controller"]["sha256"],
                "start_new_session": True,
                "started_at_utc": started_at,
            }
            launch["record_digest"] = sha256_bytes(canonical_bytes(launch))
            atomic_write(paths["launch"], launch)
            returncode = process.wait()
        terminal = {
            "schema_version": "native_v2_outer_task_terminal.v1",
            "recovery_series_id": manifest["recovery_series_id"],
            "task": "aggregate",
            "pid": process.pid,
            "returncode": returncode,
            "signal": -returncode if returncode < 0 else None,
            "started_at_utc": started_at,
            "ended_at_utc": utc_now(),
            "stdout_size": paths["stdout"].stat().st_size,
            "stdout_sha256": sha256_file(paths["stdout"]),
            "stderr_size": paths["stderr"].stat().st_size,
            "stderr_sha256": sha256_file(paths["stderr"]),
            "manifest_sha256": manifest_sha256,
            "launch_record_digest": launch["record_digest"],
        }
        terminal["record_digest"] = sha256_bytes(canonical_bytes(terminal))
        atomic_write(paths["terminal"], terminal)
        return 0
    except BaseException as error:
        failure_path = paths["supervisor_failure"]
        if not failure_path.exists():
            failure = {
                "schema_version": "native_v2_outer_supervisor_failure.v1",
                "task": "aggregate",
                "error_type": type(error).__name__,
                "error": str(error),
                "ended_at_utc": utc_now(),
            }
            failure["record_digest"] = sha256_bytes(canonical_bytes(failure))
            atomic_write(failure_path, failure)
        raise


def status(
    manifest_path: Path,
    manifest_sha256: str,
    task: str,
    outer_execution_id: str | None,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path, manifest_sha256)
    if task == "aggregate":
        base = manifest_path.parent / "aggregate"
    else:
        if outer_execution_id is None:
            raise RuntimeError("outer execution ID is required")
        execution_entry(manifest, outer_execution_id)
        base = execution_dir(manifest_path, outer_execution_id)
    paths = task_paths(base, task)
    value: dict[str, Any] = {
        "task": task,
        "outer_execution_id": outer_execution_id,
        "terminal": paths["terminal"].exists(),
        "supervisor_failure": paths["supervisor_failure"].exists(),
    }
    if paths["launch"].exists():
        launch = json.loads(paths["launch"].read_text(encoding="utf-8"))
        value["pid"] = launch["pid"]
        try:
            os.kill(launch["pid"], 0)
            value["process_present"] = True
        except ProcessLookupError:
            value["process_present"] = False
        value["started_at_utc"] = launch["started_at_utc"]
    if paths["terminal"].exists():
        value["terminal_record"] = json.loads(
            paths["terminal"].read_text(encoding="utf-8")
        )
    if paths["supervisor_failure"].exists():
        value["supervisor_failure_record"] = json.loads(
            paths["supervisor_failure"].read_text(encoding="utf-8")
        )
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("launch-child", "launch-verifier"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--manifest", required=True)
        sub.add_argument("--manifest-sha256", required=True)
        sub.add_argument("--outer-execution-id", required=True)
    supervise_parser = subparsers.add_parser("supervise")
    supervise_parser.add_argument("--manifest", required=True)
    supervise_parser.add_argument("--manifest-sha256", required=True)
    supervise_parser.add_argument("--outer-execution-id", required=True)
    supervise_parser.add_argument("--task", required=True, choices=("child", "verifier"))
    aggregate = subparsers.add_parser("launch-aggregate")
    aggregate.add_argument("--manifest", required=True)
    aggregate.add_argument("--manifest-sha256", required=True)
    supervise_aggregate_parser = subparsers.add_parser("supervise-aggregate")
    supervise_aggregate_parser.add_argument("--manifest", required=True)
    supervise_aggregate_parser.add_argument("--manifest-sha256", required=True)
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--manifest", required=True)
    status_parser.add_argument("--manifest-sha256", required=True)
    status_parser.add_argument("--task", required=True, choices=("child", "verifier", "aggregate"))
    status_parser.add_argument("--outer-execution-id")
    arguments = parser.parse_args()
    manifest_path = Path(arguments.manifest).resolve()
    if arguments.command == "launch-child":
        value = launch_supervisor(
            manifest_path,
            arguments.manifest_sha256,
            arguments.outer_execution_id,
            "child",
        )
    elif arguments.command == "launch-verifier":
        value = launch_supervisor(
            manifest_path,
            arguments.manifest_sha256,
            arguments.outer_execution_id,
            "verifier",
        )
    elif arguments.command == "supervise":
        return supervise(
            manifest_path,
            arguments.manifest_sha256,
            arguments.outer_execution_id,
            arguments.task,
        )
    elif arguments.command == "launch-aggregate":
        value = launch_aggregate(manifest_path, arguments.manifest_sha256)
    elif arguments.command == "supervise-aggregate":
        return supervise_aggregate(manifest_path, arguments.manifest_sha256)
    elif arguments.command == "status":
        value = status(
            manifest_path,
            arguments.manifest_sha256,
            arguments.task,
            arguments.outer_execution_id,
        )
    else:
        raise RuntimeError("unknown controller command")
    print(json.dumps(value, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
