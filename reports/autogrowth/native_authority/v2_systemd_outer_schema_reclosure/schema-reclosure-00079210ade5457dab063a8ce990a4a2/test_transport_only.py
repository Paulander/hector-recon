from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = Path(
    "/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit"
)
COORDINATOR_PATH = PACKAGE_ROOT / "foreground_schema_reclosure_coordinator.py"
MANIFEST_PATH = PACKAGE_ROOT / "outer_manifest.json"


def load_coordinator():
    specification = importlib.util.spec_from_file_location(
        "native_v2_schema_reclosure_coordinator", COORDINATOR_PATH
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("coordinator cannot be loaded")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


coordinator = load_coordinator()
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


class SchemaReclosureTransportTests(unittest.TestCase):
    def test_child_result_exact_three_field_contract_passes(self):
        coordinator.verify_child_result_outcome_access(
            {
                "count": 0,
                "event_ids": [],
                "science_paths_absent": True,
            },
            label="test child",
        )

    def test_child_result_contract_rejects_every_shape_or_value_change(self):
        valid = {
            "count": 0,
            "event_ids": [],
            "science_paths_absent": True,
        }
        invalid = [
            {"count": 0, "event_ids": []},
            {**valid, "science_paths_absent": False},
            {**valid, "count": 1},
            {**valid, "count": False},
            {**valid, "event_ids": ["event-1"]},
            {**valid, "extra": None},
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                coordinator.verify_child_result_outcome_access(
                    value, label="test child"
                )

    def test_verifier_contract_remains_exactly_two_fields(self):
        coordinator.verify_transport_outcome_access(
            {"count": 0, "event_ids": []}, label="test verifier"
        )
        invalid = [
            {
                "count": 0,
                "event_ids": [],
                "science_paths_absent": True,
            },
            {"count": False, "event_ids": []},
            {"count": 0, "event_ids": ["event-1"]},
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                coordinator.verify_transport_outcome_access(
                    value, label="test verifier"
                )

    def test_stdout_loader_enforces_two_field_transport_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stdout.json"
            path.write_text(
                json.dumps({"outcome_access": {"count": 0, "event_ids": []}}),
                encoding="utf-8",
            )
            coordinator.load_successful_json_stdout(path, label="verifier")
            path.write_text(
                json.dumps(
                    {
                        "outcome_access": {
                            "count": 0,
                            "event_ids": [],
                            "science_paths_absent": True,
                        }
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(RuntimeError):
                coordinator.load_successful_json_stdout(path, label="verifier")

    def test_carried_slot_matches_commit_and_captured_records(self):
        value = coordinator.verify_carried_slot(REPOSITORY_ROOT, manifest)
        self.assertEqual(
            value["child_slot"], "portable-admission-01-e7dfd710b975"
        )
        self.assertEqual(value["historical_child_pid"], 282158)
        self.assertEqual(value["outcome_access"], {"count": 0, "event_ids": []})

    def test_carried_child_passes_full_child_directory_gates(self):
        value = coordinator.verify_child_directory(
            REPOSITORY_ROOT,
            manifest,
            "portable-admission-01-e7dfd710b975",
        )
        self.assertEqual(
            value["portable_cohort_digest"],
            "5f6de9695ee0da4a74d01b2f27d2f5b0e9abb2845e304f31d230c67b5477327b",
        )

    def test_carried_hash_change_fails(self):
        changed = copy.deepcopy(manifest)
        changed["carried_slot"]["file_sha256"]["result.json"] = "0" * 64
        with self.assertRaises(RuntimeError):
            coordinator.verify_carried_slot(REPOSITORY_ROOT, changed)

    def test_task_plan_never_runs_carried_child(self):
        plan = coordinator.frozen_task_plan(manifest)
        self.assertEqual(plan, manifest["task_plan"])
        self.assertEqual(plan[0]["task"], "slot-01-verifier")
        self.assertNotIn("slot-01-child", {row["task"] for row in plan})
        self.assertEqual(
            [row["task"] for row in plan],
            [
                "slot-01-verifier",
                "slot-02-child",
                "slot-02-verifier",
                "slot-03-child",
                "slot-03-verifier",
                "aggregate-verifier",
            ],
        )

    def test_future_attempts_are_absent(self):
        attempt_root = REPOSITORY_ROOT / manifest["child_attempt_root"]
        self.assertFalse(
            (attempt_root / "portable-admission-02-e7dfd710b975").exists()
        )
        self.assertFalse(
            (attempt_root / "portable-admission-03-e7dfd710b975").exists()
        )

    def test_outer_identities_and_service_are_new_and_unique(self):
        identities = [row["outer_execution_id"] for row in manifest["executions"]]
        self.assertEqual(len(identities), len(set(identities)))
        self.assertNotEqual(
            manifest["recovery_series_id"],
            "systemd-foreground-1107519c8a4448ed8e7bc134b8a68140",
        )
        self.assertNotEqual(
            manifest["systemd"]["unit_name"],
            "hector-recon-v2-admission-e697c46cf43a4129a54d24341be70e29.service",
        )

    def test_frozen_sources_and_science_absence_remain_exact(self):
        coordinator.verify_frozen_files(REPOSITORY_ROOT, manifest)
        coordinator.verify_protected_files(REPOSITORY_ROOT, manifest)
        coordinator.verify_science_absent(REPOSITORY_ROOT, manifest)

    def test_successor_record_root_is_absent_before_launch(self):
        self.assertFalse(Path(manifest["record_root"]).exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
