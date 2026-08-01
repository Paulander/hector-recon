#!/usr/bin/env python3
"""Harmless foreground systemd-user-service canary with durable records."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence


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
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


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
    temporary = path.with_name(f".{path.name}.systemd-canary.tmp")
    if temporary.exists():
        raise RuntimeError(f"ambiguous canary temporary:{temporary}")
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
    canary = Path(manifest["canary"]["path"])
    if canary.resolve() != Path(__file__).resolve():
        raise RuntimeError("canary path mismatch")
    if sha256_file(canary) != manifest["canary"]["sha256"]:
        raise RuntimeError("canary hash mismatch")
    if str(Path(sys.executable).absolute()) != manifest["canonical_interpreter"]:
        raise RuntimeError("noncanonical canary interpreter")
    if Path.cwd().resolve() != Path(
        manifest["canonical_repository_root"]
    ).resolve():
        raise RuntimeError("noncanonical canary working directory")
    return manifest


def parse_properties(output: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in output.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def verify_service_contract(manifest: Mapping[str, Any]) -> dict[str, str]:
    unit = manifest["canary"]["unit_name"]
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
    values = parse_properties(output)
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
                f"canary service contract mismatch:{key}:"
                f"expected={expected}:observed={values.get(key)}"
            )
    if values.get("ActiveState") not in {"activating", "active"}:
        raise RuntimeError("canary service is not active")
    return values


def run_canary(manifest_path: Path, manifest_sha256: str) -> int:
    manifest = load_manifest(manifest_path, manifest_sha256)
    if not os.environ.get("INVOCATION_ID"):
        raise RuntimeError("systemd invocation identity is absent")
    for key, expected in manifest["canary_environment"].items():
        if os.environ.get(key) != expected:
            raise RuntimeError(f"canary environment mismatch:{key}")
    record_root = Path(manifest["canary"]["record_root"])
    if record_root.exists():
        raise RuntimeError("canary record root already exists")
    record_root.mkdir(parents=True, exist_ok=False)
    contract = verify_service_contract(manifest)
    duration = manifest["canary"]["duration_seconds"]
    if duration < 75:
        raise RuntimeError("canary duration is below 75 seconds")
    started_monotonic = time.monotonic()
    started = {
        "schema_version": "native_v2_systemd_canary_started.v1",
        "unit": manifest["canary"]["unit_name"],
        "pid": os.getpid(),
        "systemd_invocation_id": os.environ["INVOCATION_ID"],
        "started_at_utc": utc_now(),
        "duration_seconds": duration,
        "service_contract": contract,
        "manifest_sha256": manifest_sha256,
    }
    started["record_digest"] = digest(started)
    atomic_write(record_root / "started.json", started)
    time.sleep(duration)
    completed = {
        "schema_version": "native_v2_systemd_canary_completed.v1",
        "unit": manifest["canary"]["unit_name"],
        "pid": os.getpid(),
        "started_record_digest": started["record_digest"],
        "completed_at_utc": utc_now(),
        "elapsed_seconds": time.monotonic() - started_monotonic,
        "survived_launcher_return_boundary": True,
    }
    completed["record_digest"] = digest(completed)
    atomic_write(record_root / "completed.json", completed)
    return 0


def verify_record_digest(value: Mapping[str, Any]) -> None:
    expected = value.get("record_digest")
    observed = digest(
        {key: item for key, item in value.items() if key != "record_digest"}
    )
    if expected != observed:
        raise RuntimeError("canary record digest mismatch")


def verify_canary(manifest_path: Path, manifest_sha256: str) -> dict[str, Any]:
    manifest = load_manifest(manifest_path, manifest_sha256)
    record_root = Path(manifest["canary"]["record_root"])
    started = load_json(record_root / "started.json")
    completed = load_json(record_root / "completed.json")
    verify_record_digest(started)
    verify_record_digest(completed)
    if started["unit"] != manifest["canary"]["unit_name"]:
        raise RuntimeError("canary unit identity changed")
    if started["pid"] != completed["pid"]:
        raise RuntimeError("canary foreground PID changed")
    if completed["started_record_digest"] != started["record_digest"]:
        raise RuntimeError("canary record link changed")
    if completed["elapsed_seconds"] < 75:
        raise RuntimeError("canary did not exceed 75 seconds")
    if completed["survived_launcher_return_boundary"] is not True:
        raise RuntimeError("canary survival claim absent")
    return {
        "unit": manifest["canary"]["unit_name"],
        "pid": completed["pid"],
        "elapsed_seconds": completed["elapsed_seconds"],
        "started_sha256": sha256_file(record_root / "started.json"),
        "completed_sha256": sha256_file(record_root / "completed.json"),
        "survived_launcher_return_boundary": True,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "verify"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--manifest", required=True)
        sub.add_argument("--manifest-sha256", required=True)
    arguments = parser.parse_args(argv)
    manifest_path = Path(arguments.manifest).resolve()
    if arguments.command == "run":
        return run_canary(manifest_path, arguments.manifest_sha256)
    value = verify_canary(manifest_path, arguments.manifest_sha256)
    print(json.dumps(value, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
