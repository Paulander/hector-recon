#!/usr/bin/env python3
"""Transport-only tests; no frozen child, verifier, or aggregate is run."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(
    "/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit"
)
PACKAGE = Path(
    "/mnt/c/Users/oskar/Documents/Webpages playground/"
    "hector-recon-v2-systemd-series/"
    "systemd-foreground-1107519c8a4448ed8e7bc134b8a68140"
)
MANIFEST_PATH = PACKAGE / "outer_manifest.json"
LAUNCH_CONTRACT_PATH = PACKAGE / "launch_contract.json"
COORDINATOR_PATH = PACKAGE / "foreground_series_coordinator.py"
CANARY_PATH = PACKAGE / "harmless_systemd_canary.py"


def load_module(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


coordinator = load_module("systemd_foreground_coordinator", COORDINATOR_PATH)
canary = load_module("systemd_foreground_canary", CANARY_PATH)


class TransportPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.contract = json.loads(
            LAUNCH_CONTRACT_PATH.read_text(encoding="utf-8")
        )

    def test_transport_sources_import_no_recon_package(self) -> None:
        for path in (COORDINATOR_PATH, CANARY_PATH):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imported = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.append(node.module)
            self.assertFalse(
                [name for name in imported if name.startswith("recon_lite")]
            )

    def test_new_global_identities_are_unique_and_closed_series_is_not_reused(self) -> None:
        outer_ids = [
            row["outer_execution_id"] for row in self.manifest["executions"]
        ]
        self.assertEqual(len(outer_ids), 3)
        self.assertEqual(len(set(outer_ids)), 3)
        self.assertNotIn(
            self.manifest["recovery_series_id"],
            self.manifest["closed_series_ids"],
        )
        self.assertEqual(
            [row["child_slot"] for row in self.manifest["executions"]],
            [
                "portable-admission-01-e7dfd710b975",
                "portable-admission-02-e7dfd710b975",
                "portable-admission-03-e7dfd710b975",
            ],
        )

    def test_launch_contract_binds_manifest_and_transport_hashes(self) -> None:
        manifest_sha = hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
        self.assertEqual(self.contract["outer_manifest_sha256"], manifest_sha)
        self.assertEqual(
            self.contract["coordinator_sha256"],
            hashlib.sha256(COORDINATOR_PATH.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            self.contract["canary_sha256"],
            hashlib.sha256(CANARY_PATH.read_bytes()).hexdigest(),
        )

    def test_systemd_start_commands_are_foreground_service_ownership(self) -> None:
        for name, script, subcommand in (
            ("canary_start", CANARY_PATH, "run"),
            ("real_start", COORDINATOR_PATH, "run-series"),
        ):
            command = self.contract["exact_commands"][name]
            self.assertEqual(command[0:2], ["systemd-run", "--user"])
            self.assertNotIn("--scope", command)
            self.assertIn("--service-type=exec", command)
            self.assertIn("--property=Restart=no", command)
            self.assertIn("--property=RuntimeMaxSec=infinity", command)
            self.assertIn("--no-block", command)
            self.assertIn(str(script), command)
            self.assertIn(subcommand, command)
            self.assertNotIn("sh", command)
            self.assertNotIn("bash", command)
            self.assertNotIn("nohup", command)

    def test_status_and_finalization_commands_cannot_start_work(self) -> None:
        commands = self.contract["exact_commands"]
        self.assertEqual(commands["real_status"][2], "status")
        self.assertEqual(commands["real_finalize"][2], "finalize")
        self.assertEqual(commands["canary_verify"][2], "verify")
        for name in ("real_status", "real_finalize", "canary_verify"):
            self.assertNotIn("run-series", commands[name])
            self.assertNotIn("run-admission", commands[name])

    def test_static_real_preflight_dependencies_match_without_running_child(self) -> None:
        coordinator.verify_prior_records(ROOT, self.manifest)
        coordinator.verify_frozen_files(ROOT, self.manifest)
        coordinator.verify_protected_files(ROOT, self.manifest)
        coordinator.verify_module_paths(self.manifest)
        coordinator.verify_science_absent(ROOT, self.manifest)
        coordinator.verify_attempts_absent(ROOT, self.manifest)
        coordinator.verify_no_bridge_temporaries(ROOT, self.manifest)
        self.assertEqual(self.manifest["outcome_access"], coordinator.ZERO_OUTCOME)

    def test_synchronous_command_records_exact_exit_and_logs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            used: set[int] = set()
            terminal = coordinator.run_command(
                command=(
                    sys.executable,
                    "-c",
                    "import sys; print('transport-ok'); print('note', file=sys.stderr)",
                ),
                cwd=root,
                environment=dict(os.environ),
                record_root=root,
                task_name="synthetic-pass",
                used_pids=used,
            )
            self.assertEqual(terminal["returncode"], 0)
            self.assertIsNone(terminal["signal"])
            self.assertEqual((root / "synthetic-pass.stdout").read_text(), "transport-ok\n")
            self.assertEqual((root / "synthetic-pass.stderr").read_text(), "note\n")
            self.assertEqual(len(used), 1)

    def test_nonzero_synthetic_command_is_recorded_without_retry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            terminal = coordinator.run_command(
                command=(sys.executable, "-c", "raise SystemExit(7)"),
                cwd=root,
                environment=dict(os.environ),
                record_root=root,
                task_name="synthetic-stop",
                used_pids=set(),
            )
            self.assertEqual(terminal["returncode"], 7)
            self.assertEqual(
                sorted(path.name for path in root.iterdir()),
                [
                    "synthetic-stop.stderr",
                    "synthetic-stop.stdout",
                    "synthetic-stop_launch.json",
                    "synthetic-stop_terminal.json",
                ],
            )

    def test_atomic_record_write_fails_on_ambiguous_temporary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "record.json"
            temporary = path.with_name(f".{path.name}.systemd-series.tmp")
            temporary.write_text("occupied", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "ambiguous"):
                coordinator.atomic_write(path, {"value": 1})
            self.assertFalse(path.exists())

    def test_canary_contract_is_harmless_and_long_enough(self) -> None:
        self.assertGreaterEqual(self.manifest["canary"]["duration_seconds"], 75)
        self.assertNotIn("run-admission", CANARY_PATH.read_text(encoding="utf-8"))
        value = {"field": "value"}
        value["record_digest"] = canary.digest(value)
        canary.verify_record_digest(value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
