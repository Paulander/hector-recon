"""Stable-import launcher for the frozen V2 canonical-contract cohort.

This outer wrapper does not implement contract verification.  It launches the
byte-frozen implementation through one literal fully qualified module path and
aggregates the three preregistered order results.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

from recon_lite_chess.autogrowth import (
    native_v2_frozen_cohort_canonical_contract_reclosure as frozen,
)


ROOT = frozen.ROOT
PACKAGE_ID = "native_v2_frozen_cohort_import_path_launcher_reclosure.v1"
WRAPPER_MODULE = (
    "recon_lite_chess.autogrowth."
    "native_v2_frozen_cohort_import_path_launcher_reclosure"
)
CHILD_MODULE = (
    "recon_lite_chess.autogrowth."
    "native_v2_frozen_cohort_canonical_contract_reclosure"
)
PACKAGE_DIR = Path(
    "reports/autogrowth/native_authority/"
    "v2_frozen_cohort_import_path_launcher_reclosure"
)
SOURCE_MANIFEST_PATH = PACKAGE_DIR / "source_manifest.json"
ARTIFACT_BINDING_PATH = PACKAGE_DIR / "artifact_binding_manifest.json"
RESULT_PATH = PACKAGE_DIR / "canonical_launcher_verification.json"
FAILURE_PATH = PACKAGE_DIR / "canonical_launcher_verification_failure.json"

STOPPED_SOURCE_COMMIT = "0859a4a1db53eb6221e3ac48e19d156896aa56c6"
STOPPED_MANIFEST_COMMIT = "7b41c9210aff57d0b8db2b5302754e68695836bb"
STOPPED_RESULT_COMMIT = "5016f776a0a698033ff7df9e3dfed4311b51fa3a"
STOPPED_FAILURE_SHA256 = (
    "c345a35666a95d603472a01b935cd2ec4cedb8581996c8684568fb29ae0ff9c6"
)
STOPPED_SOURCE_MANIFEST_SHA256 = (
    "4050a6598f54b50c05f7abe580cf122c27bcc56738e5bb9f515d858180730f62"
)
STOPPED_ARTIFACT_BINDING_SHA256 = (
    "f6f60742ebd5341eaa37d9704e8595d0d712754429ae824e2e6434d436968869"
)

FROZEN_FILE_HASHES = {
    "src/recon_lite_chess/autogrowth/"
    "native_v2_frozen_cohort_canonical_contract_reclosure.py": (
        "009660b6031d124fd85fa7dfb2f43e382ed5a1102d6f74fdf527f01c6e2de8b9"
    ),
    "tests/autogrowth/"
    "test_native_v2_frozen_cohort_canonical_contract_reclosure.py": (
        "83499c7f992f800cf31ff7a6ce19244eec79e41d38eca99504ae587400422be4"
    ),
    "reports/autogrowth/native_authority/"
    "v2_frozen_cohort_canonical_contract_reclosure/source_manifest.json": (
        STOPPED_SOURCE_MANIFEST_SHA256
    ),
    "reports/autogrowth/native_authority/"
    "v2_frozen_cohort_canonical_contract_reclosure/"
    "artifact_binding_manifest.json": STOPPED_ARTIFACT_BINDING_SHA256,
    "reports/autogrowth/native_authority/"
    "v2_frozen_cohort_canonical_contract_reclosure/"
    "canonical_contract_verification_failure.json": STOPPED_FAILURE_SHA256,
    "docs/autogrowth/"
    "NATIVE_V2_FROZEN_COHORT_CANONICAL_CONTRACT_RECLOSURE_RESULT_20260727.md": (
        "639c68c2779f02fd33d2a0e156ed9dbbaee112d23e3570fcbc2d558417db3741"
    ),
}

SOURCE_FILES = (
    "src/recon_lite_chess/autogrowth/"
    "native_v2_frozen_cohort_import_path_launcher_reclosure.py",
    "tests/autogrowth/"
    "test_native_v2_frozen_cohort_import_path_launcher_reclosure.py",
    "docs/autogrowth/"
    "NATIVE_V2_FROZEN_COHORT_IMPORT_PATH_LAUNCHER_RECLOSURE_"
    "PREREGISTRATION_20260727.md",
)

ORDER_NAMES = ("ascending", "descending", "even_then_odd")
DETERMINISTIC_ENV = copy.deepcopy(frozen.DETERMINISTIC_ENV)


class LauncherIntegrityError(RuntimeError):
    """A frozen launcher or cohort contract failed."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def _require_clean_worktree() -> None:
    if _git("status", "--porcelain=v1"):
        raise LauncherIntegrityError("launcher closure requires a clean worktree")


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite frozen artifact:{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        value, indent=2, sort_keys=True, allow_nan=False
    ).encode("utf-8") + b"\n"
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise LauncherIntegrityError(f"expected JSON object:{path}")
    return value


def _verify_self_digest(
    value: Mapping[str, Any], field: str, *, label: str
) -> str:
    expected = value.get(field)
    observed = digest({key: item for key, item in value.items() if key != field})
    if expected != observed:
        raise LauncherIntegrityError(
            f"{label} digest mismatch:expected={expected}:observed={observed}"
        )
    return observed


def frozen_child_source_path() -> Path:
    specification = importlib.util.find_spec(CHILD_MODULE)
    if specification is None or specification.origin is None:
        raise LauncherIntegrityError(f"child module cannot be resolved:{CHILD_MODULE}")
    observed = Path(specification.origin).resolve()
    expected = Path(frozen.__file__).resolve()
    if observed != expected:
        raise LauncherIntegrityError(
            f"child module source mismatch:expected={expected}:observed={observed}"
        )
    return observed


def build_child_argv(order_name: str) -> tuple[str, ...]:
    if order_name not in ORDER_NAMES:
        raise LauncherIntegrityError(f"unknown frozen order:{order_name}")
    return (
        sys.executable,
        "-m",
        CHILD_MODULE,
        "verify-order",
        "--order",
        order_name,
    )


def build_child_help_argv() -> tuple[str, ...]:
    return (sys.executable, "-m", CHILD_MODULE, "--help")


def deterministic_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(DETERMINISTIC_ENV)
    return environment


def execute_child(
    argv: Sequence[str], *, order_name: str | None = None
) -> dict[str, Any]:
    exact_argv = tuple(str(item) for item in argv)
    started = time.perf_counter()
    process = subprocess.Popen(
        exact_argv,
        cwd=ROOT,
        env=deterministic_environment(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    process_id = process.pid
    stdout, stderr = process.communicate()
    return {
        "argv": list(exact_argv),
        "order_name": order_name,
        "process_id": process_id,
        "returncode": int(process.returncode),
        "stdout": stdout,
        "stderr": stderr,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }


def parse_clean_json_stdout(child: Mapping[str, Any]) -> dict[str, Any]:
    stdout = child.get("stdout")
    if not isinstance(stdout, str):
        raise LauncherIntegrityError("child stdout is not text")
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise LauncherIntegrityError(
            f"child stdout is not one clean JSON value:{exc}"
        ) from exc
    if not isinstance(value, dict):
        raise LauncherIntegrityError("child stdout JSON is not an object")
    return value


def _verify_commit(commit: str) -> None:
    subprocess.run(
        ("git", "cat-file", "-e", f"{commit}^{{commit}}"),
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if subprocess.run(
        ("git", "merge-base", "--is-ancestor", commit, "HEAD"),
        cwd=ROOT,
        check=False,
    ).returncode != 0:
        raise LauncherIntegrityError(f"frozen commit is not an ancestor:{commit}")


def verify_frozen_inputs() -> dict[str, Any]:
    for commit in (
        STOPPED_SOURCE_COMMIT,
        STOPPED_MANIFEST_COMMIT,
        STOPPED_RESULT_COMMIT,
    ):
        _verify_commit(commit)
    observed_hashes = {}
    for relative, expected in FROZEN_FILE_HASHES.items():
        observed = sha256_file(ROOT / relative)
        observed_hashes[relative] = observed
        if observed != expected:
            raise LauncherIntegrityError(
                f"frozen file changed:{relative}:expected={expected}:observed={observed}"
            )
    child_source = frozen_child_source_path()
    if sha256_file(child_source) != FROZEN_FILE_HASHES[
        "src/recon_lite_chess/autogrowth/"
        "native_v2_frozen_cohort_canonical_contract_reclosure.py"
    ]:
        raise LauncherIntegrityError("resolved child source hash mismatch")
    stopped_package = frozen._verify_frozen_package_manifests()
    static = frozen.verify_static_bindings()
    artifact = stopped_package["artifact_binding"]
    if (
        len(artifact.get("prefix_organisms", ())) != 32
        or len(artifact.get("snapshots", ())) != 96
        or len(artifact.get("contracts", ())) != 32
        or static["target_counts"]
        != {"planted": 32, "selected_comparison": 30}
    ):
        raise LauncherIntegrityError("frozen cohort cardinality changed")
    if any((ROOT / path).exists() for path in frozen.STOPPED_OUTPUT_PATHS):
        raise LauncherIntegrityError("stopped package suffix is no longer unopened")
    return {
        "frozen_file_hashes": observed_hashes,
        "child_module": CHILD_MODULE,
        "child_source_path": str(child_source),
        "child_source_sha256": sha256_file(child_source),
        "stopped_source_manifest_sha256": stopped_package[
            "source_manifest_sha256"
        ],
        "stopped_source_manifest_digest": stopped_package[
            "source_manifest_digest"
        ],
        "stopped_artifact_binding_sha256": stopped_package[
            "artifact_binding_sha256"
        ],
        "stopped_artifact_binding_digest": stopped_package[
            "artifact_binding_digest"
        ],
        "prefix_organism_set_digest": artifact["prefix_organism_set_digest"],
        "snapshot_set_digest": artifact["snapshot_set_digest"],
        "contract_set_digest": artifact["contract_set_digest"],
        "target_counts": copy.deepcopy(static["target_counts"]),
        "outcome_reads": 0,
        "exposure_rows_read": 0,
    }


def freeze_package_manifests(source_commit: str) -> dict[str, Any]:
    _require_clean_worktree()
    if _git("rev-parse", "HEAD") != source_commit:
        raise LauncherIntegrityError("source freeze commit is not HEAD")
    if (ROOT / SOURCE_MANIFEST_PATH).exists() or (
        ROOT / ARTIFACT_BINDING_PATH
    ).exists():
        raise FileExistsError("launcher manifests already exist")
    fixed = verify_frozen_inputs()
    source_hashes = {
        relative: sha256_file(ROOT / relative) for relative in SOURCE_FILES
    }
    source = {
        "schema_version": "native_v2_import_path_launcher_source_manifest.v1",
        "package_id": PACKAGE_ID,
        "source_freeze_commit": source_commit,
        "source_hashes": source_hashes,
        "fixed_child_module": CHILD_MODULE,
        "fixed_child_source_path": fixed["child_source_path"],
        "fixed_child_source_sha256": fixed["child_source_sha256"],
        "deterministic_environment": copy.deepcopy(DETERMINISTIC_ENV),
        "runtime": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "working_directory": str(ROOT),
        },
        "preservation": {
            "stopped_package_byte_identical": True,
            "frozen_cohort_byte_identical": True,
            "launcher_only_correction": True,
            "evaluation_suffix_unopened": True,
        },
    }
    source["source_manifest_digest"] = digest(source)
    _atomic_json(ROOT / SOURCE_MANIFEST_PATH, source)

    binding = {
        "schema_version": "native_v2_import_path_launcher_artifact_binding.v1",
        "package_id": PACKAGE_ID,
        "bound_commits": {
            "stopped_source": STOPPED_SOURCE_COMMIT,
            "stopped_manifests": STOPPED_MANIFEST_COMMIT,
            "stopped_result": STOPPED_RESULT_COMMIT,
        },
        "source_manifest": {
            "path": SOURCE_MANIFEST_PATH.as_posix(),
            "sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
            "digest": source["source_manifest_digest"],
        },
        "frozen_inputs": fixed,
        "launcher_contract": {
            "wrapper_module": WRAPPER_MODULE,
            "child_module": CHILD_MODULE,
            "python_executable": sys.executable,
            "working_directory": str(ROOT),
            "orders": list(ORDER_NAMES),
            "deterministic_environment": copy.deepcopy(DETERMINISTIC_ENV),
        },
        "disclosures": {
            "planted_target_count_known": 32,
            "selected_comparison_target_count_known": 30,
            "fixed_outcome_blindly_reused_cohort": True,
            "evaluation_suffix_unopened": True,
            "future_claim_conditional_on_fixed_cohort_and_ecology": True,
            "prior_instrument_stops_remain_valid": True,
        },
    }
    binding["artifact_binding_digest"] = digest(binding)
    _atomic_json(ROOT / ARTIFACT_BINDING_PATH, binding)
    return {
        "source_manifest_path": SOURCE_MANIFEST_PATH.as_posix(),
        "source_manifest_sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
        "source_manifest_digest": source["source_manifest_digest"],
        "artifact_binding_path": ARTIFACT_BINDING_PATH.as_posix(),
        "artifact_binding_sha256": sha256_file(ROOT / ARTIFACT_BINDING_PATH),
        "artifact_binding_digest": binding["artifact_binding_digest"],
    }


def verify_package_manifests() -> dict[str, Any]:
    source = _load_json(ROOT / SOURCE_MANIFEST_PATH)
    source_digest = _verify_self_digest(
        source, "source_manifest_digest", label="launcher source manifest"
    )
    for relative, expected in source["source_hashes"].items():
        observed = sha256_file(ROOT / relative)
        if observed != expected:
            raise LauncherIntegrityError(
                f"launcher source changed:{relative}:{observed}"
            )
    _verify_commit(str(source["source_freeze_commit"]))
    binding = _load_json(ROOT / ARTIFACT_BINDING_PATH)
    binding_digest = _verify_self_digest(
        binding, "artifact_binding_digest", label="launcher artifact binding"
    )
    if (
        binding["source_manifest"]["sha256"]
        != sha256_file(ROOT / SOURCE_MANIFEST_PATH)
        or binding["source_manifest"]["digest"] != source_digest
        or binding["launcher_contract"]["child_module"] != CHILD_MODULE
    ):
        raise LauncherIntegrityError("launcher source/artifact binding mismatch")
    fixed = verify_frozen_inputs()
    if canonical_bytes(binding["frozen_inputs"]) != canonical_bytes(fixed):
        raise LauncherIntegrityError("frozen input binding mismatch")
    return {
        "source_manifest_sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
        "source_manifest_digest": source_digest,
        "artifact_binding_sha256": sha256_file(ROOT / ARTIFACT_BINDING_PATH),
        "artifact_binding_digest": binding_digest,
        "artifact_binding": binding,
    }


def _child_summary(child: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "argv": copy.deepcopy(child["argv"]),
        "order_name": child["order_name"],
        "process_id": int(child["process_id"]),
        "returncode": int(child["returncode"]),
        "elapsed_seconds": child["elapsed_seconds"],
        "stdout_size": len(str(child["stdout"]).encode("utf-8")),
        "stdout_sha256": hashlib.sha256(
            str(child["stdout"]).encode("utf-8")
        ).hexdigest(),
        "stderr": str(child["stderr"]),
    }


def _write_failure(
    *,
    reason: str,
    child: Mapping[str, Any] | None,
    completed: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    failure = {
        "schema_version": "native_v2_import_path_launcher_failure.v1",
        "package_id": PACKAGE_ID,
        "reason": reason,
        "parent_argv": list(getattr(sys, "orig_argv", sys.argv)),
        "parent_process_id": os.getpid(),
        "fixed_child_module": CHILD_MODULE,
        "python_executable": sys.executable,
        "working_directory": str(ROOT),
        "deterministic_environment": copy.deepcopy(DETERMINISTIC_ENV),
        "failed_child": copy.deepcopy(dict(child)) if child is not None else None,
        "completed_orders": copy.deepcopy(list(completed)),
        "outcome_reads": 0,
        "exposure_rows_read": 0,
    }
    failure["failure_digest"] = digest(failure)
    _atomic_json(ROOT / FAILURE_PATH, failure)
    return failure


def _validate_order_result(
    value: Mapping[str, Any], child: Mapping[str, Any], order_name: str
) -> dict[int, str]:
    if (
        value.get("schema_version")
        != "native_v2_canonical_contract_order_result.v1"
        or value.get("package_id") != frozen.PACKAGE_ID
        or value.get("order_name") != order_name
        or value.get("evaluation_order") != list(frozen.ORDER_MAP[order_name])
        or value.get("process_id") != child["process_id"]
        or value.get("verified_seed_count") != 32
        or value.get("verified_organism_count") != 96
    ):
        raise LauncherIntegrityError(f"child result identity failed:{order_name}")
    core = value.get("core")
    if not isinstance(core, dict):
        raise LauncherIntegrityError(f"child core missing:{order_name}")
    seed_rows = core.get("seed_rows")
    if not isinstance(seed_rows, list) or len(seed_rows) != 32:
        raise LauncherIntegrityError(f"child seed rows incomplete:{order_name}")
    if (
        core.get("outcome_access") != {"count": 0, "event_ids": []}
        or core.get("exposure_rows_read") != 0
        or any(core.get("stopped_output_paths_present", {}).values())
        or not all(row.get("no_candidate_or_graph_mutation") for row in seed_rows)
    ):
        raise LauncherIntegrityError(f"child safety gate failed:{order_name}")
    observed_result_digest = digest(
        {key: item for key, item in value.items() if key != "order_result_digest"}
    )
    if value.get("order_result_digest") != observed_result_digest:
        raise LauncherIntegrityError(f"child result digest failed:{order_name}")
    return {int(row["seed_ordinal"]): str(row["contract_digest"]) for row in seed_rows}


def run_verification() -> dict[str, Any]:
    _require_clean_worktree()
    if (ROOT / RESULT_PATH).exists() or (ROOT / FAILURE_PATH).exists():
        raise FileExistsError("launcher result path already exists")
    package = verify_package_manifests()
    started = time.perf_counter()
    completed: list[dict[str, Any]] = []
    parsed_results: list[dict[str, Any]] = []
    contract_maps: list[dict[int, str]] = []
    for order_name in ORDER_NAMES:
        child = execute_child(build_child_argv(order_name), order_name=order_name)
        if child["returncode"] != 0:
            _write_failure(
                reason=f"child process failed:{order_name}",
                child=child,
                completed=completed,
            )
            raise LauncherIntegrityError(f"child process failed:{order_name}")
        try:
            parsed = parse_clean_json_stdout(child)
            contract_map = _validate_order_result(parsed, child, order_name)
        except Exception as exc:
            _write_failure(
                reason=f"child result invalid:{order_name}:{type(exc).__name__}:{exc}",
                child=child,
                completed=completed,
            )
            raise
        summary = _child_summary(child)
        completed.append({"child": summary, "result": parsed})
        parsed_results.append(parsed)
        contract_maps.append(contract_map)

    process_ids = [int(item["process_id"]) for item in parsed_results]
    cohort_digests = {str(item["cohort_digest"]) for item in parsed_results}
    contract_map_bytes = {canonical_bytes(item) for item in contract_maps}
    try:
        if (
            len(set(process_ids)) != 3
            or os.getpid() in process_ids
            or len(cohort_digests) != 1
            or len(contract_map_bytes) != 1
        ):
            raise LauncherIntegrityError("cross-order identity gate failed")
    except Exception as exc:
        _write_failure(
            reason=f"aggregate result invalid:{type(exc).__name__}:{exc}",
            child=None,
            completed=completed,
        )
        raise

    per_seed_contract_digests = [
        {"seed_ordinal": ordinal, "contract_digest": contract_maps[0][ordinal]}
        for ordinal in range(32)
    ]
    result = {
        "schema_version": "native_v2_import_path_launcher_result.v1",
        "package_id": PACKAGE_ID,
        "source_manifest": {
            "sha256": package["source_manifest_sha256"],
            "digest": package["source_manifest_digest"],
        },
        "artifact_binding": {
            "sha256": package["artifact_binding_sha256"],
            "digest": package["artifact_binding_digest"],
        },
        "parent_argv": list(getattr(sys, "orig_argv", sys.argv)),
        "parent_process_id": os.getpid(),
        "fixed_child_module": CHILD_MODULE,
        "python_executable": sys.executable,
        "working_directory": str(ROOT),
        "deterministic_environment": copy.deepcopy(DETERMINISTIC_ENV),
        "orders": completed,
        "child_process_ids": process_ids,
        "fresh_process_count": 3,
        "verified_seed_count_per_order": 32,
        "verified_organism_count_per_order": 96,
        "identical_cohort_digest": next(iter(cohort_digests)),
        "per_seed_contract_digests": per_seed_contract_digests,
        "per_seed_contract_digest_set": digest(per_seed_contract_digests),
        "all_orders_identical": True,
        "candidate_or_graph_mutation_count": 0,
        "exposure_rows_read": 0,
        "outcome_access": {"count": 0, "event_ids": []},
        "evaluation_suffix_unopened": True,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }
    result["result_digest"] = digest(result)
    _atomic_json(ROOT / RESULT_PATH, result)
    return result


def _print(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    freeze = commands.add_parser("freeze-manifests")
    freeze.add_argument("--source-commit", required=True)
    probe = commands.add_parser("probe-child-argv")
    probe.add_argument("--order", choices=ORDER_NAMES, required=True)
    commands.add_parser("run-verification")
    args = parser.parse_args(argv)
    if args.command == "freeze-manifests":
        value = freeze_package_manifests(args.source_commit)
    elif args.command == "probe-child-argv":
        value = {
            "parent_runtime_module_name": __name__,
            "parent_process_id": os.getpid(),
            "child_argv": list(build_child_argv(args.order)),
        }
    elif args.command == "run-verification":
        value = run_verification()
    else:  # pragma: no cover
        raise AssertionError(args.command)
    _print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
