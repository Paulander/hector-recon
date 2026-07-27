from __future__ import annotations

import copy
from enum import Enum
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys

import pytest

from recon_lite_chess.autogrowth import (
    native_v2_frozen_cohort_execution_adapter_freeze as adapter,
)


class StringMode(str, Enum):
    PROSPECTIVE = "prospective"
    LEGACY = "legacy_same_ledger"


def _contract() -> dict:
    value = {
        "schema_version": "synthetic.contract.v1",
        "members": ("terminal-a", "terminal-b"),
        "mode": StringMode.PROSPECTIVE,
        "polarity": "POSITIVE",
        "candidate": "cell-1",
        "topology": {"root": "root-1", "legs": ("a", "b")},
        "initial_state": {"available": False},
    }
    return adapter.canonical.sign_contract(value)


def _json_contract() -> dict:
    return json.loads(json.dumps(_contract()))


def _manifest(expected: dict | None = None) -> dict:
    return {
        "schema_version": "synthetic.snapshot.v1",
        "metadata": {
            "per_seed_identity_contracts": {"0": expected or _json_contract()}
        },
        "entries": [],
        "manifest_digest": "synthetic-manifest",
    }


def _signed_exposure(*, admitted: bool = True) -> dict:
    value = {
        "schema_version": "synthetic.exposure.v1",
        "admitted": admitted,
        "outcome_access": {"count": 0, "event_ids": []},
    }
    value["exposure_digest"] = adapter.digest(value)
    return value


def _signed_execution(exposure: dict, expected: dict) -> dict:
    value = {
        "schema_version": "synthetic.execution.v1",
        "admitted": True,
        "exposure_artifact": {
            "digest": exposure["exposure_digest"],
            "sha256": expected["exposure_sha256"],
        },
        "prefix_manifest": {
            "sha256": expected["prefix_sha256"],
            "digest": expected["prefix_digest"],
        },
        "snapshot_manifest": {
            "sha256": expected["snapshot_sha256"],
            "digest": expected["snapshot_digest"],
        },
        "adapter_package": {
            "readiness_sha256": expected["readiness_sha256"],
            "readiness_digest": expected["readiness_digest"],
        },
    }
    value["execution_manifest_digest"] = adapter.digest(value)
    return value


def _admission_fixture() -> tuple[dict, dict, dict]:
    expected = {
        "exposure_digest": "filled-after-signing",
        "exposure_sha256": "exposure-sha",
        "prefix_sha256": "prefix-sha",
        "prefix_digest": "prefix-digest",
        "snapshot_sha256": "snapshot-sha",
        "snapshot_digest": "snapshot-digest",
        "readiness_sha256": "readiness-sha",
        "readiness_digest": "readiness-digest",
    }
    exposure = _signed_exposure()
    expected["exposure_digest"] = exposure["exposure_digest"]
    execution = _signed_execution(exposure, expected)
    return exposure, execution, expected


def _commit_seed(
    journal: adapter.driver.DurableHashJournal, seed: int
) -> None:
    zero = {"count": 0, "event_ids": []}
    journal.prepare_seed(seed, {"seed": seed}, zero)
    journal.commit_seed(seed, {"seed": seed, "complete": True}, zero)


def test_runtime_view_has_identical_canonical_bytes_and_digest() -> None:
    manifest = _manifest()
    source_before = copy.deepcopy(manifest)
    observed = _contract()
    assert manifest["metadata"]["per_seed_identity_contracts"]["0"] != observed
    runtime, proof = adapter.construct_runtime_contract_view(
        manifest, {"0": observed}
    )
    assert adapter.canonical_bytes(runtime) == adapter.canonical_bytes(manifest)
    assert adapter.digest(runtime) == adapter.digest(manifest)
    assert proof["source_before"] == proof["runtime_view"]
    assert proof["source_before"] == proof["source_after"]
    assert manifest == source_before
    assert runtime["metadata"]["per_seed_identity_contracts"]["0"] == observed


def test_manifest_file_stays_byte_identical(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    payload = json.dumps(_manifest(), indent=2, sort_keys=True).encode() + b"\n"
    path.write_bytes(payload)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    loaded = json.loads(path.read_text())
    adapter.construct_runtime_contract_view(loaded, {"0": _contract()})
    after = hashlib.sha256(path.read_bytes()).hexdigest()
    assert before == after
    assert path.read_bytes() == payload


def test_semantic_change_rejected_before_runtime_view() -> None:
    manifest = _manifest()
    changed = _contract()
    changed["members"] = ("terminal-a", "changed-terminal")
    changed = adapter.canonical.sign_contract(changed)
    source_before = copy.deepcopy(manifest)
    with pytest.raises(adapter.canonical.CanonicalContractMismatch):
        adapter.construct_runtime_contract_view(manifest, {"0": changed})
    assert manifest == source_before


def test_stopped_raw_mismatch_reproduces_then_runtime_raw_check_passes() -> None:
    expected = _json_contract()
    observed = _contract()
    with pytest.raises(
        adapter.driver.FreshScientificIntegrityError,
        match="snapshot candidate contract mismatch:0",
    ):
        adapter.canonical.legacy_raw_contract_check(
            expected, observed, seed_ordinal=0
        )
    runtime, _ = adapter.construct_runtime_contract_view(
        _manifest(expected), {"0": observed}
    )
    assert runtime["metadata"]["per_seed_identity_contracts"]["0"] == observed
    adapter.canonical.legacy_raw_contract_check(
        runtime["metadata"]["per_seed_identity_contracts"]["0"],
        observed,
        seed_ordinal=0,
    )


def test_runtime_view_does_not_replace_module_globals() -> None:
    bindings = adapter.capture_critical_bindings()
    adapter.construct_runtime_contract_view(_manifest(), {"0": _contract()})
    unchanged = adapter.require_bindings_unchanged(bindings)
    assert "driver._verify_prefix_snapshot_metadata" in unchanged
    assert "canonical.compare_complete_contracts" in unchanged


def test_semantic_set_digest_uses_complete_per_seed_identity() -> None:
    identities = {
        arm: {"arm": arm, "state": [arm]} for arm in adapter.driver.ARMS
    }
    assert adapter.semantic_identity_set_digest(identities) == adapter.digest({
        arm: identities[arm] for arm in adapter.driver.ARMS
    })


def test_public_commands_use_literal_fully_qualified_path() -> None:
    for command in adapter.PUBLIC_COMMANDS:
        argv = adapter.build_public_command(command)
        assert argv == (sys.executable, "-m", adapter.ADAPTER_MODULE, command)
        assert "__main__" not in argv
    source = Path(adapter.__file__).read_text(encoding="utf-8")
    assert "runpy" not in source
    assert "monkeypatch" not in source
    assert "__module__" not in source
    assert "inspect.stack" not in source


def test_public_help_and_readiness_help_execute_in_fresh_processes() -> None:
    help_process = adapter.execute_public_process(adapter.build_help_command())
    assert help_process["returncode"] == 0
    assert help_process["process_id"] != os.getpid()
    assert "verify-readiness" in help_process["stdout"]
    readiness_help = adapter.execute_public_process(
        (*adapter.build_public_command("verify-readiness"), "--help")
    )
    assert readiness_help["returncode"] == 0
    assert readiness_help["process_id"] not in {
        os.getpid(), help_process["process_id"]
    }
    assert readiness_help["stderr"] == ""


def test_old_package_output_identity_is_stable() -> None:
    before = adapter._old_output_identity()
    after = adapter._old_output_identity()
    assert before == after
    rows = {row["path"]: row for row in before["rows"]}
    assert rows[adapter.launcher.RESULT_PATH.as_posix()]["exists"] is True
    assert rows[adapter.canonical.FAILURE_PATH.as_posix()]["exists"] is True


def test_exposure_gate_rejects_any_outcome_access() -> None:
    adapter.require_zero_outcomes(
        {"outcome_access": {"count": 0, "event_ids": []}}, label="synthetic"
    )
    with pytest.raises(adapter.AdapterIntegrityError, match="opened an outcome"):
        adapter.require_zero_outcomes(
            {"outcome_access": {"count": 1, "event_ids": ["event"]}},
            label="synthetic",
        )
    source = inspect.getsource(adapter.run_exposure)
    assert "FrozenTruthfulEnvironment" not in source
    assert "run_science" not in source


def test_science_cannot_begin_without_admitted_exposure() -> None:
    exposure, _, expected = _admission_fixture()
    exposure = _signed_exposure(admitted=False)
    expected["exposure_digest"] = exposure["exposure_digest"]
    execution = _signed_execution(exposure, expected)
    with pytest.raises(adapter.AdapterIntegrityError, match="not admitted"):
        adapter.validate_admission_values(
            exposure=exposure, execution=execution, expected=expected
        )


def test_two_seed_journal_resumes_at_next_unfinished_seed(tmp_path: Path) -> None:
    journal = adapter.driver.DurableHashJournal(tmp_path / "journal")
    _commit_seed(journal, 0)
    plan = adapter.restart_plan(journal, (0, 1))
    assert plan["completed_ordinals"] == [0]
    assert plan["next_unfinished_seed"] == 1
    assert plan["remaining_ordinals"] == [1]


def test_all_complete_journal_reconstructs_without_replay(tmp_path: Path) -> None:
    journal = adapter.driver.DurableHashJournal(tmp_path / "journal")
    _commit_seed(journal, 0)
    _commit_seed(journal, 1)
    executions = []
    result = adapter.execute_remaining_or_reconstruct(
        journal=journal,
        seed_ordinals=(0, 1),
        execute_seed=lambda seed: executions.append(seed),
        reconstruct_summary=lambda seeds: {"seeds": list(seeds)},
    )
    assert executions == []
    assert result["executed_ordinals"] == []
    assert result["summary"] == {"seeds": [0, 1]}


@pytest.mark.parametrize(
    "kind",
    ("exposure", "snapshot", "prefix", "execution"),
)
def test_changed_bound_identity_stops_before_outcome(kind: str) -> None:
    exposure, execution, expected = _admission_fixture()
    if kind == "exposure":
        exposure["extra"] = "changed"
        exposure["exposure_digest"] = adapter.digest({
            key: value for key, value in exposure.items()
            if key != "exposure_digest"
        })
    elif kind == "snapshot":
        execution["snapshot_manifest"]["sha256"] = "changed"
        execution["execution_manifest_digest"] = adapter.digest({
            key: value for key, value in execution.items()
            if key != "execution_manifest_digest"
        })
    elif kind == "prefix":
        execution["prefix_manifest"]["digest"] = "changed"
        execution["execution_manifest_digest"] = adapter.digest({
            key: value for key, value in execution.items()
            if key != "execution_manifest_digest"
        })
    elif kind == "execution":
        execution["adapter_package"]["readiness_digest"] = "changed"
        execution["execution_manifest_digest"] = adapter.digest({
            key: value for key, value in execution.items()
            if key != "execution_manifest_digest"
        })
    with pytest.raises(adapter.AdapterIntegrityError):
        adapter.validate_admission_values(
            exposure=exposure, execution=execution, expected=expected
        )
    assert exposure["outcome_access"] == {"count": 0, "event_ids": []}


def test_frozen_input_bindings_and_old_paths_remain_exact() -> None:
    fixed = adapter.verify_frozen_inputs()
    assert fixed["passing_launcher_result"]["cohort_digest"] == (
        adapter.ACCEPTED_COHORT_DIGEST
    )
    assert fixed["transport_checks"] == {
        "prefix_manifest_sha256": adapter.PREFIX_MANIFEST_SHA256,
        "raw_snapshot_size": adapter.RAW_SNAPSHOT_MANIFEST_SIZE,
        "raw_snapshot_sha256": adapter.RAW_SNAPSHOT_MANIFEST_SHA256,
        "compressed_snapshot_sha256": adapter.COMPRESSED_SNAPSHOT_SHA256,
        "preflight_receipt_sha256": adapter.PREFLIGHT_RECEIPT_SHA256,
    }
    assert fixed["target_counts"] == {
        "planted": 32,
        "selected_comparison": 30,
    }
    assert fixed["exposure_rows_read"] == 0
    assert fixed["outcome_reads"] == 0
