from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path

import pytest

from recon_lite_chess.autogrowth import (
    native_v2_portable_outcome_successor as successor,
)


def test_private_provider_executes_identical_code_without_global_replacement() -> None:
    sentinel = {"completed": True}

    def original_provider():
        raise AssertionError("obsolete provider ran")

    namespace = {"validate_completed_exposure": original_provider}
    exec(
        "def science():\n"
        "    return {'value': validate_completed_exposure()}\n",
        namespace,
    )
    science = namespace["science"]
    before = science.__globals__["validate_completed_exposure"]
    result = successor.execute_unchanged_science_suffix(
        sentinel, science_function=science
    )
    assert result == {"value": sentinel}
    assert science.__globals__["validate_completed_exposure"] is before


def test_historical_science_code_object_is_reused() -> None:
    source = inspect.getsource(successor.execute_unchanged_science_suffix)
    assert "types.FunctionType" in source
    assert "science_function.__code__" in source
    assert "historical.run_science()" not in source


def test_launcher_freeze_differs_only_by_absolute_child_path() -> None:
    package, proof = successor._portable_launcher_package()
    assert package["artifact_binding"]["frozen_inputs"][
        "child_source_path"
    ] == proof["recorded_value"]
    assert proof["runtime_value"] != proof["recorded_value"]
    assert proof["all_other_fields_exact"] is True


def test_launcher_portable_check_rejects_non_path_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launcher = successor.historical.stopped_adapter.launcher
    observed = launcher.verify_frozen_inputs()
    observed["target_counts"] = {"planted": 31, "selected_comparison": 30}
    monkeypatch.setattr(launcher, "verify_frozen_inputs", lambda: observed)
    with pytest.raises(
        successor.PortableOutcomeSuccessorError,
        match="changed beyond checkout path",
    ):
        successor._portable_launcher_package()


def test_readiness_path_provider_is_private() -> None:
    source = inspect.getsource(successor._portable_readiness_context)
    assert source.count("types.FunctionType") == 2
    assert "adapter.verify_frozen_inputs.__globals__" in source
    assert "adapter.build_readiness_context.__globals__" in source


def test_portable_reference_requires_three_exact_rows(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    aggregate = {
        "attempt_count": 3,
        "attempts": [],
        "portable_cohort_digest": successor.EXPECTED_PORTABLE_COHORT_DIGEST,
        "protected_file_count": successor.EXPECTED_PROTECTED_FILE_COUNT,
        "protected_file_set_digest": (
            successor.EXPECTED_PROTECTED_FILE_SET_DIGEST
        ),
        "mutation_count": 0,
        "outcome_access": {"count": 0, "event_ids": []},
    }
    for index in range(3):
        attempt = tmp_path / f"attempt-{index}"
        attempt.mkdir()
        result = {
            "record_digest": "",
            "outcome_access": {
                "count": 0,
                "event_ids": [],
                "science_paths_absent": True,
            },
            "fresh_verification": {
                "mutation_count": 0,
                "portable_cohort_digest": (
                    successor.EXPECTED_PORTABLE_COHORT_DIGEST
                ),
                "unit_rows": [{"unit_id": "A/seed-00"}],
            },
        }
        result["record_digest"] = successor.digest(
            {key: value for key, value in result.items() if key != "record_digest"}
        )
        path = attempt / "result.json"
        path.write_text(json.dumps(result), encoding="utf-8")
        aggregate["attempts"].append({
            "attempt_id": attempt.name,
            "result_sha256": successor.sha256_file(path),
            "result_digest": result["record_digest"],
        })
    aggregate["aggregate_digest"] = successor.digest(aggregate)
    aggregate_path = tmp_path / "aggregate.json"
    aggregate_path.write_text(json.dumps(aggregate), encoding="utf-8")
    monkeypatch.setattr(successor, "ROOT", tmp_path)
    monkeypatch.setattr(
        successor, "PORTABLE_AGGREGATE_PATH", Path("aggregate.json")
    )
    monkeypatch.setattr(
        successor.portable, "ATTEMPT_ROOT", Path(".")
    )
    monkeypatch.setattr(
        successor.portable, "verify_self_digest",
        lambda value, field: None,
    )
    monkeypatch.setattr(successor, "ARMS", ("A",))
    monkeypatch.setattr(successor, "SEED_COUNT", 1)
    monkeypatch.setattr(
        successor,
        "EXPECTED_AGGREGATE_DIGEST",
        aggregate["aggregate_digest"],
    )
    _, rows = successor._portable_reference()
    assert rows == [{"unit_id": "A/seed-00"}]
    changed = json.loads((tmp_path / "attempt-2/result.json").read_text())
    changed["fresh_verification"]["unit_rows"][0]["unit_id"] = "changed"
    changed["record_digest"] = successor.digest(
        {
            key: value
            for key, value in changed.items()
            if key != "record_digest"
        }
    )
    (tmp_path / "attempt-2/result.json").write_text(
        json.dumps(changed), encoding="utf-8"
    )
    aggregate["attempts"][2]["result_sha256"] = successor.sha256_file(
        tmp_path / "attempt-2/result.json"
    )
    aggregate["attempts"][2]["result_digest"] = changed["record_digest"]
    aggregate["aggregate_digest"] = successor.digest(
        {key: value for key, value in aggregate.items() if key != "aggregate_digest"}
    )
    monkeypatch.setattr(
        successor,
        "EXPECTED_AGGREGATE_DIGEST",
        aggregate["aggregate_digest"],
    )
    aggregate_path.write_text(json.dumps(aggregate), encoding="utf-8")
    with pytest.raises(successor.PortableOutcomeSuccessorError):
        successor._portable_reference()


def test_completion_requires_all_32_and_exact_outcome_count(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(successor, "ROOT", tmp_path)
    monkeypatch.setattr(successor.historical, "RESULT_PATH", Path("result.gz"))
    (tmp_path / "result.gz").write_bytes(b"result")
    result = {
        "all_32_committed": True,
        "canonical_result_digest": "result-digest",
        "outcome_accounting": {
            "status": "known",
            "count": successor.EXPECTED_OUTCOME_COUNT,
        },
    }
    value = successor._completion_record(
        service={"attempt": "service"},
        handoff={"handoff_digest": "handoff"},
        result=result,
        reconstructed_after_interruption=False,
    )
    assert value["all_32_committed"] is True
    changed = copy.deepcopy(result)
    changed["outcome_accounting"]["count"] -= 1
    with pytest.raises(successor.PortableOutcomeSuccessorError):
        successor._completion_record(
            service={}, handoff={}, result=changed,
            reconstructed_after_interruption=False,
        )


def test_runtime_worktree_allows_only_declared_output_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allowed = successor.historical.SCIENCE_JOURNAL_DIR / "journal.jsonl"
    monkeypatch.setattr(
        successor, "_worktree_rows", lambda: [f"?? {allowed.as_posix()}"]
    )
    successor.require_runtime_worktree()
    materialized = successor._materialized_input_spec()["path"]
    monkeypatch.setattr(
        successor, "_worktree_rows", lambda: [f"?? {materialized}"]
    )
    successor.require_runtime_worktree()
    monkeypatch.setattr(
        successor, "_worktree_rows", lambda: ["?? unrelated.txt"]
    )
    with pytest.raises(successor.PortableOutcomeSuccessorError):
        successor.require_runtime_worktree()


def test_materialized_snapshot_requires_exact_frozen_bytes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    adapter = successor.historical.stopped_adapter
    raw = b"exact raw snapshot"
    compressed = b"exact frozen transport"
    monkeypatch.setattr(successor, "ROOT", tmp_path)
    monkeypatch.setattr(adapter, "RAW_SNAPSHOT_MANIFEST_PATH", Path("raw.json"))
    monkeypatch.setattr(adapter, "COMPRESSED_SNAPSHOT_PATH", Path("raw.json.gz"))
    monkeypatch.setattr(adapter, "RAW_SNAPSHOT_MANIFEST_SIZE", len(raw))
    monkeypatch.setattr(
        adapter,
        "RAW_SNAPSHOT_MANIFEST_SHA256",
        successor.hashlib.sha256(raw).hexdigest(),
    )
    monkeypatch.setattr(
        adapter,
        "COMPRESSED_SNAPSHOT_SHA256",
        successor.hashlib.sha256(compressed).hexdigest(),
    )
    (tmp_path / "raw.json").write_bytes(raw)
    (tmp_path / "raw.json.gz").write_bytes(compressed)
    assert successor.verify_materialized_snapshot_manifest()["verified"] is True
    (tmp_path / "raw.json").write_bytes(b"changed raw snapshot")
    with pytest.raises(
        successor.PortableOutcomeSuccessorError,
        match="changed or absent",
    ):
        successor.verify_materialized_snapshot_manifest()


def test_service_context_fails_without_user_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(successor.Path, "cwd", lambda: successor.ROOT)
    monkeypatch.setenv("PYTHONHASHSEED", "0")
    monkeypatch.setenv(
        "RECON_PORTABLE_OUTCOME_ATTEMPT_ID", successor.OUTCOME_ATTEMPT_ID
    )
    monkeypatch.setenv("RECON_PORTABLE_OUTCOME_UNIT", successor.SERVICE_UNIT)
    monkeypatch.delenv("INVOCATION_ID", raising=False)
    monkeypatch.setattr(
        successor.sys, "executable", str(successor.PYTHON_EXECUTABLE)
    )
    with pytest.raises(
        successor.PortableOutcomeSuccessorError,
        match="user-service invocation",
    ):
        successor.verify_service_context()


def test_service_context_requires_literal_child_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(successor.Path, "cwd", lambda: successor.ROOT)
    monkeypatch.setattr(
        successor.sys, "executable", str(successor.PYTHON_EXECUTABLE)
    )
    monkeypatch.setenv("PYTHONHASHSEED", "0")
    monkeypatch.setenv(
        "RECON_PORTABLE_OUTCOME_ATTEMPT_ID", successor.OUTCOME_ATTEMPT_ID
    )
    monkeypatch.setenv("RECON_PORTABLE_OUTCOME_UNIT", successor.SERVICE_UNIT)
    monkeypatch.setenv("INVOCATION_ID", "invocation")
    monkeypatch.setattr(successor.sys, "orig_argv", ["wrong"])
    with pytest.raises(
        successor.PortableOutcomeSuccessorError,
        match="service child command",
    ):
        successor.verify_service_context()
    monkeypatch.setattr(
        successor.sys, "orig_argv", successor._service_child_command()
    )
    assert successor.verify_service_context()["argv"] == (
        successor._service_child_command()
    )


def test_source_contains_no_launcher_or_scientific_reimplementation() -> None:
    source = inspect.getsource(successor)
    assert "systemd-run" not in source
    assert "launch-service" not in source
    assert "execute_fresh_seed_atomically(" not in source
    assert "adjudicate_committed_results(" not in source
