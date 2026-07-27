from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys

from recon_lite_chess.autogrowth import (
    native_v2_frozen_cohort_import_path_launcher_reclosure as launcher,
)


def test_child_argv_uses_literal_stable_module_path() -> None:
    argv = launcher.build_child_argv("ascending")
    assert argv == (
        sys.executable,
        "-m",
        launcher.CHILD_MODULE,
        "verify-order",
        "--order",
        "ascending",
    )
    assert launcher.CHILD_MODULE in argv
    assert "__main__" not in argv


def test_child_module_resolves_to_exact_frozen_source() -> None:
    specification = importlib.util.find_spec(launcher.CHILD_MODULE)
    assert specification is not None
    assert specification.origin is not None
    assert Path(specification.origin).resolve() == launcher.frozen_child_source_path()
    assert launcher.sha256_file(launcher.frozen_child_source_path()) == (
        launcher.FROZEN_FILE_HASHES[
            "src/recon_lite_chess/autogrowth/"
            "native_v2_frozen_cohort_canonical_contract_reclosure.py"
        ]
    )


def test_parent_running_as_main_still_emits_stable_child_argv() -> None:
    argv = (
        sys.executable,
        "-m",
        launcher.WRAPPER_MODULE,
        "probe-child-argv",
        "--order",
        "ascending",
    )
    child = launcher.execute_child(argv, order_name="probe")
    assert child["returncode"] == 0
    assert child["process_id"] != os.getpid()
    value = launcher.parse_clean_json_stdout(child)
    assert value["parent_runtime_module_name"] == "__main__"
    assert value["child_argv"] == list(launcher.build_child_argv("ascending"))
    assert "__main__" not in value["child_argv"]


def test_real_fresh_child_public_help_resolves_without_loading_cohort() -> None:
    argv = launcher.build_child_help_argv()
    child = launcher.execute_child(argv, order_name="help")
    assert child["argv"] == list(argv)
    assert child["returncode"] == 0
    assert child["process_id"] != os.getpid()
    assert "usage:" in child["stdout"]
    assert child["stderr"] == ""


def test_nonzero_child_exit_preserves_exact_process_record() -> None:
    argv = (
        sys.executable,
        "-m",
        launcher.CHILD_MODULE,
        "verify-order",
        "--order",
        "not-a-frozen-order",
    )
    child = launcher.execute_child(argv, order_name="invalid-order")
    assert child["argv"] == list(argv)
    assert child["order_name"] == "invalid-order"
    assert child["returncode"] != 0
    assert child["stdout"] == ""
    assert "invalid choice" in child["stderr"]


def test_successful_child_stdout_is_one_clean_json_value() -> None:
    argv = (
        sys.executable,
        "-m",
        launcher.WRAPPER_MODULE,
        "probe-child-argv",
        "--order",
        "descending",
    )
    child = launcher.execute_child(argv, order_name="json-probe")
    assert child["returncode"] == 0
    value = launcher.parse_clean_json_stdout(child)
    assert json.loads(child["stdout"]) == value
    assert value["child_argv"] == list(launcher.build_child_argv("descending"))


def test_frozen_inputs_and_stopped_failure_remain_exact() -> None:
    fixed = launcher.verify_frozen_inputs()
    assert fixed["child_module"] == launcher.CHILD_MODULE
    assert fixed["target_counts"] == {
        "planted": 32,
        "selected_comparison": 30,
    }
    assert fixed["outcome_reads"] == 0
    assert fixed["exposure_rows_read"] == 0
    old_failure = (
        launcher.ROOT
        / "reports/autogrowth/native_authority/"
        "v2_frozen_cohort_canonical_contract_reclosure/"
        "canonical_contract_verification_failure.json"
    )
    assert launcher.sha256_file(old_failure) == launcher.STOPPED_FAILURE_SHA256


def test_wrapper_source_has_no_runtime_import_path_derivation() -> None:
    source = Path(launcher.__file__).read_text(encoding="utf-8")
    assert "CHILD_MODULE = (" in source
    assert '"native_v2_frozen_cohort_canonical_contract_reclosure"' in source
    assert "runpy" not in source
    assert "inspect.stack" not in source
    assert "__module__" not in source
    assert "-m\",\n        __name__" not in source
    assert set(launcher.ORDER_NAMES) == {
        "ascending",
        "descending",
        "even_then_odd",
    }
