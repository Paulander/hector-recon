"""Portable handoff into the unchanged frozen native V2 outcome suffix.

This package changes no scientific factor.  It replaces only the obsolete
raw-serialization completed-exposure provider with an already demonstrated
portable semantic reconstruction, then executes the exact historical
``run_science`` code object in a private globals mapping.  The historical
module globals are never replaced.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import inspect
import json
import marshal
import os
import subprocess
import sys
import traceback
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, MutableMapping, Sequence

from . import native_v2_fresh_discriminator_review_repair_v2 as driver
from . import native_v2_portable_admission_bridge as portable
from . import native_v2_process_readiness_repair as historical
from . import native_v2_process_resilient_execution_reclosure as execution


ROOT = historical.ROOT
PYTHON_EXECUTABLE = Path(
    "/mnt/c/Users/oskar/Documents/Webpages playground/"
    "hector-recon-audit/.venv/bin/python3"
)
PACKAGE_ID = "native_v2_portable_outcome_successor.v1"
MODULE_PATH = (
    "recon_lite_chess.autogrowth.native_v2_portable_outcome_successor"
)
OUTCOME_ATTEMPT_ID = (
    "portable-outcome-03-19dbfa8e53bf4531bcb7d002cb4ef2f7"
)
SERVICE_UNIT = (
    "hector-recon-v2-outcome-03-19dbfa8e53bf4531bcb7d002cb4ef2f7.service"
)
PACKAGE_DIR = Path(
    "reports/autogrowth/native_authority/v2_portable_outcome_successor"
)
SOURCE_MANIFEST_PATH = PACKAGE_DIR / "source_manifest.json"
PACKAGE_MANIFEST_PATH = PACKAGE_DIR / "package_manifest.json"
PREOUTCOME_FAILURE_PATH = PACKAGE_DIR / "preoutcome_failure.json"
ATTEMPT_02_STDERR_PATH = PACKAGE_DIR / "preoutcome_attempt_02.stderr"
COMPLETION_PATH = PACKAGE_DIR / "completion.json"
PREREGISTRATION_PATH = Path(
    "docs/autogrowth/"
    "NATIVE_V2_PORTABLE_OUTCOME_SUCCESSOR_PREREGISTRATION_20260803.md"
)
TEST_PATH = Path(
    "tests/autogrowth/test_native_v2_portable_outcome_successor.py"
)
SELF_PATH = Path(
    "src/recon_lite_chess/autogrowth/"
    "native_v2_portable_outcome_successor.py"
)
SCHEMA_RECLOSURE_PACKAGE = Path(
    "reports/autogrowth/native_authority/"
    "v2_systemd_outer_schema_reclosure/"
    "schema-reclosure-00079210ade5457dab063a8ce990a4a2"
)
PORTABLE_AGGREGATE_PATH = (
    SCHEMA_RECLOSURE_PACKAGE / "series_records/aggregate-verifier.stdout"
)
PORTABLE_TERMINAL_PATH = (
    SCHEMA_RECLOSURE_PACKAGE / "series_records/series_terminal.json"
)
PORTABLE_FINALIZATION_PATH = (
    SCHEMA_RECLOSURE_PACKAGE / "series_records/finalization.json"
)
ZERO_OUTCOME = {"count": 0, "event_ids": []}
EXPECTED_AGGREGATE_DIGEST = (
    "a7bf36df7309f67da8d6c42ae700dd032413dcfa70390d47fba7e40c35eae733"
)
EXPECTED_PORTABLE_COHORT_DIGEST = (
    "5f6de9695ee0da4a74d01b2f27d2f5b0e9abb2845e304f31d230c67b5477327b"
)
EXPECTED_PROTECTED_FILE_COUNT = 195
EXPECTED_PROTECTED_FILE_SET_DIGEST = (
    "9082cf52f505d924590458c4dd2a7f365bbdec3494cdbbc3d974726e97cb4239"
)
EXPECTED_OUTCOME_COUNT = 1536
ARMS = tuple(historical.ARMS)
SEED_COUNT = historical.SEED_COUNT


class PortableOutcomeSuccessorError(RuntimeError):
    """The frozen portable handoff or outcome authority changed."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")


def pretty_json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PortableOutcomeSuccessorError(f"non-object JSON:{path}")
    return value


def verify_self_digest(
    value: Mapping[str, Any], field: str, *, label: str
) -> None:
    expected = value.get(field)
    observed = digest({key: item for key, item in value.items() if key != field})
    if expected != observed:
        raise PortableOutcomeSuccessorError(f"{label} digest changed")


def _git(*arguments: str) -> str:
    return subprocess.check_output(
        ("git", *arguments), cwd=ROOT, text=True
    ).strip()


def _require_committed_bytes(path: Path) -> None:
    try:
        committed = subprocess.check_output(
            ("git", "show", f"HEAD:{path.as_posix()}"), cwd=ROOT
        )
    except subprocess.CalledProcessError as exc:
        raise PortableOutcomeSuccessorError(
            f"package file is not committed:{path}"
        ) from exc
    if committed != (ROOT / path).read_bytes():
        raise PortableOutcomeSuccessorError(
            f"package file differs from HEAD:{path}"
        )


def science_code_digest(
    function: Callable[[], Mapping[str, Any]] = historical.run_science,
) -> str:
    return hashlib.sha256(marshal.dumps(function.__code__)).hexdigest()


def _source_paths() -> tuple[Path, ...]:
    paths = set(portable.protected_paths())
    paths.update((SELF_PATH, TEST_PATH, PREREGISTRATION_PATH))
    return tuple(sorted(paths, key=lambda item: item.as_posix()))


def _artifact_paths() -> tuple[Path, ...]:
    paths = {
        PORTABLE_AGGREGATE_PATH,
        PORTABLE_TERMINAL_PATH,
        PORTABLE_FINALIZATION_PATH,
        historical.EXPOSURE_PATH,
        historical.EXECUTION_MANIFEST_PATH,
        historical.EXPOSURE_COMPLETION_PATH,
        portable.SOURCE_MANIFEST_PATH,
        portable.CLASSIFICATION_MANIFEST_PATH,
        portable.DEPENDENCY_MANIFEST_PATH,
        PREOUTCOME_FAILURE_PATH,
        ATTEMPT_02_STDERR_PATH,
    }
    for attempt_id in portable.ATTEMPT_IDS:
        attempt = portable.ATTEMPT_ROOT / attempt_id
        paths.update(
            attempt / name
            for name in (
                "00_started.json",
                "01_historical_journal_verified.json",
                "progress.json",
                "result.json",
            )
        )
    for path in (ROOT / historical.EXPOSURE_JOURNAL_DIR).iterdir():
        if path.is_file():
            paths.add(path.relative_to(ROOT))
    return tuple(sorted(paths, key=lambda item: item.as_posix()))


def _output_paths() -> tuple[Path, ...]:
    return (
        historical.SCIENCE_STARTED_PATH,
        historical.SCIENCE_JOURNAL_DIR,
        historical.SCIENCE_CARRIER_DIR,
        historical.RESULT_PATH,
        historical.SCIENCE_FAILURE_PATH,
        PREOUTCOME_FAILURE_PATH,
        COMPLETION_PATH,
    )


def _materialized_input_spec() -> dict[str, Any]:
    adapter = historical.stopped_adapter
    return {
        "path": adapter.RAW_SNAPSHOT_MANIFEST_PATH.as_posix(),
        "size": adapter.RAW_SNAPSHOT_MANIFEST_SIZE,
        "sha256": adapter.RAW_SNAPSHOT_MANIFEST_SHA256,
        "compressed_path": adapter.COMPRESSED_SNAPSHOT_PATH.as_posix(),
        "compressed_sha256": adapter.COMPRESSED_SNAPSHOT_SHA256,
        "materialization": "exact decompression of frozen transport",
    }


def _worktree_rows() -> list[str]:
    return _git("status", "--porcelain=v1").splitlines()


def require_freeze_worktree() -> None:
    rows = _worktree_rows()
    if rows:
        raise PortableOutcomeSuccessorError(
            f"source-freeze worktree is not clean:{rows}"
        )


def require_runtime_worktree() -> None:
    allowed = tuple(path.as_posix() for path in _output_paths()) + (
        _materialized_input_spec()["path"],
    )
    unexpected = [
        row
        for row in _worktree_rows()
        if not any(row[3:].strip().startswith(prefix) for prefix in allowed)
    ]
    if unexpected:
        raise PortableOutcomeSuccessorError(
            f"unexpected runtime worktree paths:{unexpected}"
        )


def _service_child_command() -> list[str]:
    return [
        PYTHON_EXECUTABLE.as_posix(),
        "-m",
        MODULE_PATH,
        "run-science",
    ]


def freeze_package(source_commit: str) -> dict[str, Any]:
    require_freeze_worktree()
    if _git("rev-parse", "HEAD") != source_commit:
        raise PortableOutcomeSuccessorError("source commit is not HEAD")
    if (ROOT / SOURCE_MANIFEST_PATH).exists() or (
        ROOT / PACKAGE_MANIFEST_PATH
    ).exists():
        raise FileExistsError("portable outcome manifests already exist")
    aggregate = load_json(ROOT / PORTABLE_AGGREGATE_PATH)
    if aggregate.get("aggregate_digest") != EXPECTED_AGGREGATE_DIGEST:
        raise PortableOutcomeSuccessorError("portable aggregate changed")
    source = {
        "schema_version": "native_v2_portable_outcome_source.v1",
        "package_id": PACKAGE_ID,
        "source_commit": source_commit,
        "source_hashes": {
            path.as_posix(): sha256_file(ROOT / path)
            for path in _source_paths()
        },
        "historical_science_source_sha256": sha256_file(
            ROOT / Path(inspect.getsourcefile(historical.run_science) or "")
        ),
        "historical_science_code_digest": science_code_digest(),
        "protected_file_count": EXPECTED_PROTECTED_FILE_COUNT,
        "protected_file_set_digest": EXPECTED_PROTECTED_FILE_SET_DIGEST,
    }
    source["source_manifest_digest"] = digest(source)
    historical.atomic_json(ROOT / SOURCE_MANIFEST_PATH, source)
    package = {
        "schema_version": "native_v2_portable_outcome_package.v1",
        "package_id": PACKAGE_ID,
        "outcome_attempt_id": OUTCOME_ATTEMPT_ID,
        "service_unit": SERVICE_UNIT,
        "source_manifest": {
            "path": SOURCE_MANIFEST_PATH.as_posix(),
            "sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
            "digest": source["source_manifest_digest"],
        },
        "artifact_hashes": {
            path.as_posix(): sha256_file(ROOT / path)
            for path in _artifact_paths()
        },
        "portable_aggregate_digest": EXPECTED_AGGREGATE_DIGEST,
        "portable_cohort_digest": EXPECTED_PORTABLE_COHORT_DIGEST,
        "historical_science_code_digest": source[
            "historical_science_code_digest"
        ],
        "exact_child_command": _service_child_command(),
        "expected_complete_outcome_count": EXPECTED_OUTCOME_COUNT,
        "arms": list(ARMS),
        "seed_count": SEED_COUNT,
        "suffix_row_count": 16,
        "scientific_changes": [],
        "runtime_materialized_input": _materialized_input_spec(),
        "bypassed_obsolete_checks": [
            "recorded-child completed-exposure raw comparison",
            "historical run_science completed-exposure raw comparison",
        ],
    }
    package["package_manifest_digest"] = digest(package)
    historical.atomic_json(ROOT / PACKAGE_MANIFEST_PATH, package)
    return {
        "source_manifest_sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
        "source_manifest_digest": source["source_manifest_digest"],
        "package_manifest_sha256": sha256_file(ROOT / PACKAGE_MANIFEST_PATH),
        "package_manifest_digest": package["package_manifest_digest"],
        "exact_child_command": package["exact_child_command"],
        "outcome_access": copy.deepcopy(ZERO_OUTCOME),
    }


def verify_package_freeze() -> tuple[dict[str, Any], dict[str, Any]]:
    source = load_json(ROOT / SOURCE_MANIFEST_PATH)
    package = load_json(ROOT / PACKAGE_MANIFEST_PATH)
    verify_self_digest(source, "source_manifest_digest", label="source manifest")
    verify_self_digest(package, "package_manifest_digest", label="package manifest")
    for path in (SOURCE_MANIFEST_PATH, PACKAGE_MANIFEST_PATH):
        _require_committed_bytes(path)
    if package.get("source_manifest") != {
        "path": SOURCE_MANIFEST_PATH.as_posix(),
        "sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
        "digest": source["source_manifest_digest"],
    }:
        raise PortableOutcomeSuccessorError("source/package binding changed")
    for relative, expected in source["source_hashes"].items():
        if sha256_file(ROOT / Path(relative)) != expected:
            raise PortableOutcomeSuccessorError(f"frozen source changed:{relative}")
    for relative, expected in package["artifact_hashes"].items():
        if sha256_file(ROOT / Path(relative)) != expected:
            raise PortableOutcomeSuccessorError(
                f"frozen artifact changed:{relative}"
            )
    if (
        source.get("historical_science_code_digest") != science_code_digest()
        or package.get("historical_science_code_digest")
        != science_code_digest()
        or package.get("portable_aggregate_digest")
        != EXPECTED_AGGREGATE_DIGEST
        or package.get("portable_cohort_digest")
        != EXPECTED_PORTABLE_COHORT_DIGEST
        or package.get("exact_child_command") != _service_child_command()
        or package.get("runtime_materialized_input")
        != _materialized_input_spec()
    ):
        raise PortableOutcomeSuccessorError("frozen execution identity changed")
    return source, package


def verify_materialized_snapshot_manifest() -> dict[str, Any]:
    spec = _materialized_input_spec()
    raw = ROOT / spec["path"]
    compressed = ROOT / spec["compressed_path"]
    if (
        not raw.is_file()
        or raw.stat().st_size != spec["size"]
        or sha256_file(raw) != spec["sha256"]
        or not compressed.is_file()
        or sha256_file(compressed) != spec["compressed_sha256"]
    ):
        raise PortableOutcomeSuccessorError(
            "materialized frozen snapshot manifest changed or absent"
        )
    value = copy.deepcopy(spec)
    value["verified"] = True
    value["verification_digest"] = digest(value)
    return value


def _portable_launcher_package() -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify the old launcher while normalizing only its checkout path.

    The launcher artifact embedded the absolute path of its child module even
    though the same child bytes and every other frozen input are portable.
    The three-process admission already established the complete organism and
    unit semantics.  This verifier retains every old launcher check and permits
    exactly that one absolute-path representation difference.
    """

    launcher = historical.stopped_adapter.launcher
    source = launcher._load_json(ROOT / launcher.SOURCE_MANIFEST_PATH)
    source_digest = launcher._verify_self_digest(
        source, "source_manifest_digest", label="launcher source manifest"
    )
    for relative, expected in source["source_hashes"].items():
        observed = launcher.sha256_file(ROOT / relative)
        if observed != expected:
            raise PortableOutcomeSuccessorError(
                f"launcher source changed:{relative}:{observed}"
            )
    launcher._verify_commit(str(source["source_freeze_commit"]))
    binding = launcher._load_json(ROOT / launcher.ARTIFACT_BINDING_PATH)
    binding_digest = launcher._verify_self_digest(
        binding, "artifact_binding_digest", label="launcher artifact binding"
    )
    if (
        binding["source_manifest"]["sha256"]
        != launcher.sha256_file(ROOT / launcher.SOURCE_MANIFEST_PATH)
        or binding["source_manifest"]["digest"] != source_digest
        or binding["launcher_contract"]["child_module"]
        != launcher.CHILD_MODULE
    ):
        raise PortableOutcomeSuccessorError(
            "launcher source/artifact binding changed"
        )

    observed_fixed = launcher.verify_frozen_inputs()
    expected_fixed = binding["frozen_inputs"]
    current_child = str(launcher.frozen_child_source_path())
    if observed_fixed.get("child_source_path") != current_child:
        raise PortableOutcomeSuccessorError(
            "launcher child source resolution changed"
        )
    normalized = copy.deepcopy(observed_fixed)
    normalized["child_source_path"] = expected_fixed.get(
        "child_source_path"
    )
    if canonical_bytes(normalized) != canonical_bytes(expected_fixed):
        raise PortableOutcomeSuccessorError(
            "launcher frozen input changed beyond checkout path"
        )
    proof = {
        "normalized_field": "child_source_path",
        "recorded_value": expected_fixed["child_source_path"],
        "runtime_value": observed_fixed["child_source_path"],
        "child_source_sha256": observed_fixed["child_source_sha256"],
        "all_other_fields_exact": True,
    }
    proof["proof_digest"] = digest(proof)
    package = {
        "source_manifest_sha256": launcher.sha256_file(
            ROOT / launcher.SOURCE_MANIFEST_PATH
        ),
        "source_manifest_digest": source_digest,
        "artifact_binding_sha256": launcher.sha256_file(
            ROOT / launcher.ARTIFACT_BINDING_PATH
        ),
        "artifact_binding_digest": binding_digest,
        "artifact_binding": binding,
    }
    return package, proof


def _portable_readiness_context() -> tuple[dict[str, Any], dict[str, Any]]:
    """Run the existing context builder with one private path-normalized input."""

    adapter = historical.stopped_adapter
    launcher_package, proof = _portable_launcher_package()
    original_launcher = adapter.verify_frozen_inputs.__globals__.get("launcher")
    verify_globals: MutableMapping[str, Any] = dict(
        adapter.verify_frozen_inputs.__globals__
    )
    verify_globals["launcher"] = types.SimpleNamespace(
        verify_package_manifests=lambda: launcher_package
    )
    private_verify = types.FunctionType(
        adapter.verify_frozen_inputs.__code__,
        verify_globals,
        name=adapter.verify_frozen_inputs.__name__,
        argdefs=adapter.verify_frozen_inputs.__defaults__,
        closure=adapter.verify_frozen_inputs.__closure__,
    )
    private_verify.__kwdefaults__ = adapter.verify_frozen_inputs.__kwdefaults__

    original_provider = adapter.build_readiness_context.__globals__.get(
        "verify_frozen_inputs"
    )
    context_globals: MutableMapping[str, Any] = dict(
        adapter.build_readiness_context.__globals__
    )
    context_globals["verify_frozen_inputs"] = private_verify
    private_context = types.FunctionType(
        adapter.build_readiness_context.__code__,
        context_globals,
        name=adapter.build_readiness_context.__name__,
        argdefs=adapter.build_readiness_context.__defaults__,
        closure=adapter.build_readiness_context.__closure__,
    )
    private_context.__kwdefaults__ = adapter.build_readiness_context.__kwdefaults__
    value = dict(private_context())
    if (
        adapter.verify_frozen_inputs.__globals__.get("launcher")
        is not original_launcher
        or adapter.build_readiness_context.__globals__.get(
            "verify_frozen_inputs"
        )
        is not original_provider
    ):
        raise PortableOutcomeSuccessorError(
            "historical readiness module globals changed"
        )
    return value, proof


def _build_portable_runtime() -> tuple[dict[str, Any], dict[str, Any]]:
    snapshot_proof = verify_materialized_snapshot_manifest()
    dependencies = historical.production_runtime_dependencies()
    proof: dict[str, Any] = {}

    def build_context() -> Mapping[str, Any]:
        context, observed = _portable_readiness_context()
        proof.update(observed)
        return context

    portable_dependencies = historical.RuntimeDependencies(
        verify_inputs=dependencies.verify_inputs,
        load_previous_readiness=dependencies.load_previous_readiness,
        build_context=build_context,
        verify_outer_manifest=dependencies.verify_outer_manifest,
        load_ecology=dependencies.load_ecology,
        load_receipt=dependencies.load_receipt,
        expanded_package_map=dependencies.expanded_package_map,
        registry_type=dependencies.registry_type,
    )
    runtime = historical.build_real_exposure_runtime(portable_dependencies)
    if not proof.get("all_other_fields_exact"):
        raise PortableOutcomeSuccessorError(
            "portable launcher proof was not consumed"
        )
    proof["materialized_snapshot_manifest"] = snapshot_proof
    return runtime, proof


def verify_service_context() -> dict[str, Any]:
    expected_executable = PYTHON_EXECUTABLE.resolve()
    if Path(sys.executable).resolve() != expected_executable:
        raise PortableOutcomeSuccessorError("Python interpreter changed")
    if Path.cwd().resolve() != ROOT.resolve():
        raise PortableOutcomeSuccessorError("working directory changed")
    if os.environ.get("PYTHONHASHSEED") != "0":
        raise PortableOutcomeSuccessorError("PYTHONHASHSEED is not frozen")
    if os.environ.get("RECON_PORTABLE_OUTCOME_ATTEMPT_ID") != OUTCOME_ATTEMPT_ID:
        raise PortableOutcomeSuccessorError("outcome attempt identity changed")
    if os.environ.get("RECON_PORTABLE_OUTCOME_UNIT") != SERVICE_UNIT:
        raise PortableOutcomeSuccessorError("outcome service identity changed")
    invocation_id = os.environ.get("INVOCATION_ID")
    if not invocation_id:
        raise PortableOutcomeSuccessorError("user-service invocation is absent")
    argv = list(getattr(sys, "orig_argv", sys.argv))
    if argv != _service_child_command():
        raise PortableOutcomeSuccessorError("service child command changed")
    return {
        "attempt_id": OUTCOME_ATTEMPT_ID,
        "service_unit": SERVICE_UNIT,
        "systemd_invocation_id": invocation_id,
        "process_id": os.getpid(),
        "parent_process_id": os.getppid(),
        "executable": Path(sys.executable).resolve().as_posix(),
        "working_directory": Path.cwd().resolve().as_posix(),
        "argv": argv,
    }


def _portable_reference() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    aggregate = load_json(ROOT / PORTABLE_AGGREGATE_PATH)
    if (
        aggregate.get("aggregate_digest") != EXPECTED_AGGREGATE_DIGEST
        or digest({
            key: item
            for key, item in aggregate.items()
            if key != "aggregate_digest"
        }) != EXPECTED_AGGREGATE_DIGEST
        or aggregate.get("attempt_count") != 3
        or aggregate.get("portable_cohort_digest")
        != EXPECTED_PORTABLE_COHORT_DIGEST
        or aggregate.get("protected_file_count")
        != EXPECTED_PROTECTED_FILE_COUNT
        or aggregate.get("protected_file_set_digest")
        != EXPECTED_PROTECTED_FILE_SET_DIGEST
        or aggregate.get("mutation_count") != 0
        or aggregate.get("outcome_access") != ZERO_OUTCOME
    ):
        raise PortableOutcomeSuccessorError("portable aggregate gate changed")
    attempt_rows: list[list[dict[str, Any]]] = []
    for summary in aggregate["attempts"]:
        attempt_id = str(summary["attempt_id"])
        result_path = portable.ATTEMPT_ROOT / attempt_id / "result.json"
        result = load_json(ROOT / result_path)
        portable.verify_self_digest(result, "record_digest")
        if (
            sha256_file(ROOT / result_path) != summary["result_sha256"]
            or result.get("record_digest") != summary["result_digest"]
            or result.get("outcome_access")
            != {"count": 0, "event_ids": [], "science_paths_absent": True}
            or result["fresh_verification"]["mutation_count"] != 0
            or result["fresh_verification"]["portable_cohort_digest"]
            != EXPECTED_PORTABLE_COHORT_DIGEST
        ):
            raise PortableOutcomeSuccessorError(
                f"portable attempt changed:{attempt_id}"
            )
        rows = copy.deepcopy(result["fresh_verification"]["unit_rows"])
        if len(rows) != len(ARMS) * SEED_COUNT:
            raise PortableOutcomeSuccessorError(
                f"portable attempt coverage changed:{attempt_id}"
            )
        attempt_rows.append(rows)
    if any(
        canonical_bytes(rows) != canonical_bytes(attempt_rows[0])
        for rows in attempt_rows[1:]
    ):
        raise PortableOutcomeSuccessorError(
            "portable attempts disagree on semantic unit rows"
        )
    return aggregate, attempt_rows[0]


def _registry_entry_by_id(registry: Any, organism_id: str) -> Any:
    matches = [
        entry
        for entry in registry.entries
        if entry.organism_id == organism_id
    ]
    if len(matches) != 1:
        raise PortableOutcomeSuccessorError(
            f"registry organism coverage changed:{organism_id}"
        )
    return matches[0]


def _verify_live_mapping(
    *,
    runtime: Mapping[str, Any],
    historical_state: portable.HistoricalJournalState,
    reference_rows: Sequence[Mapping[str, Any]],
    classification: Mapping[str, Any],
) -> dict[str, Any]:
    bindings = tuple(execution.production_unit_bindings(runtime))
    if len(bindings) != len(ARMS) * SEED_COUNT:
        raise PortableOutcomeSuccessorError("live binding coverage changed")
    codec = driver.V2SnapshotCodec()
    exposure = load_json(ROOT / historical.EXPOSURE_PATH)
    stored_results: list[dict[str, Any]] = []
    historical_payloads: dict[str, dict[str, str]] = {
        arm: {} for arm in ARMS
    }
    mapping_rows = []
    for index, fresh_binding in enumerate(bindings):
        historical_binding, stored_result = portable._historical_unit(
            historical_state, index
        )
        portable.validate_classified_object(
            classification,
            f"unit-binding:{index}",
            "unit_binding",
            historical_binding,
        )
        portable.validate_classified_object(
            classification,
            f"unit-binding:{index}",
            "unit_binding",
            fresh_binding,
        )
        binding_digest = portable.compare_portable_binding(
            historical_binding, fresh_binding
        )
        arm = str(fresh_binding["arm"])
        ordinal = int(fresh_binding["seed_ordinal"])
        organism_id = str(fresh_binding["organism_id"])
        if (
            int(fresh_binding["unit_index"]) != index
            or fresh_binding["unit_id"] != f"{arm}/seed-{ordinal:02d}"
            or organism_id != f"seed-{ordinal:02d}"
            or (ordinal, arm) not in runtime["restored"]
        ):
            raise PortableOutcomeSuccessorError(
                f"live unit association changed:{index}"
            )
        wrapper = runtime["restored"][(ordinal, arm)]
        before = codec.semantic_identity(wrapper)
        preoutcome = portable.require_preoutcome(wrapper)
        source_entry = historical_binding["source_snapshot_identity"]["entry"]
        portable.compare_complete_semantic_identity(
            source_entry["semantic_identity"], before,
            label=f"{arm}:{ordinal}",
        )
        if source_entry["semantic_identity_digest"] != digest(before):
            raise PortableOutcomeSuccessorError(
                f"snapshot semantic digest changed:{arm}:{ordinal}"
            )
        registry = runtime["registries"][arm]["registry"]
        entry = _registry_entry_by_id(registry, organism_id)
        preserved_entry = exposure["arms"][arm]["registry"]["organisms"][
            ordinal
        ]
        if (
            entry.continuation_digest != before["continuation_digest"]
            or entry.experimental_identity_digest
            != before["experiment_identity"]
            or entry.candidate_population_identity
            != before["candidate_population_identity"]
            or entry.source_binding_identity
            != stored_result["scan_wrapper"]["source_binding_identity"]
            or entry.source_binding_identity
            != preserved_entry["source_binding_identity"]
        ):
            raise PortableOutcomeSuccessorError(
                f"live source/organism identity changed:{arm}:{ordinal}"
            )
        reference = reference_rows[index]
        checks = {
            "unit_index": index,
            "unit_id": fresh_binding["unit_id"],
            "arm": arm,
            "seed_ordinal": ordinal,
            "organism_id": organism_id,
            "complete_semantic_identity_digest": digest(before),
            "preoutcome_state_digest": digest(preoutcome),
            "portable_binding_digest": binding_digest,
            "continuation_digest": before["continuation_digest"],
        }
        for field, value in checks.items():
            if reference.get(field) != value:
                raise PortableOutcomeSuccessorError(
                    f"live/reference semantic mismatch:{index}:{field}"
                )
        if codec.semantic_identity(wrapper) != before:
            raise PortableOutcomeSuccessorError(
                f"identity check mutated wrapper:{arm}:{ordinal}"
            )
        mapping_rows.append(checks)
        historical_payloads[arm][organism_id] = str(
            historical_binding["payload_sha256"]
        )
        stored_results.append(copy.deepcopy(stored_result))
    if set(runtime["restored"]) != {
        (ordinal, arm)
        for ordinal in range(SEED_COUNT)
        for arm in ARMS
    }:
        raise PortableOutcomeSuccessorError("restored mapping key set changed")
    return {
        "bindings": bindings,
        "stored_results": stored_results,
        "historical_payloads": historical_payloads,
        "mapping_rows": mapping_rows,
        "mapping_digest": digest(mapping_rows),
    }


def _reconstruct_completed(
    *,
    runtime: Mapping[str, Any],
    historical_state: portable.HistoricalJournalState,
    mapping: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    preserved_exposure = load_json(ROOT / historical.EXPOSURE_PATH)
    registries: dict[str, Any] = {}
    registry_rows = {}
    by_key = {
        (str(row["arm"]), int(row["seed_ordinal"])): row
        for row in mapping["stored_results"]
    }
    for arm in ARMS:
        fresh_registry = runtime["registries"][arm]["registry"]
        reconstructed = portable.reconstruct_historical_registry(
            fresh_registry, mapping["historical_payloads"][arm]
        )
        historical_manifest = driver._registry_manifest(reconstructed)
        preserved_manifest = preserved_exposure["arms"][arm]["registry"]
        if canonical_bytes(historical_manifest) != canonical_bytes(
            preserved_manifest
        ):
            raise PortableOutcomeSuccessorError(
                f"historical registry reconstruction changed:{arm}"
            )
        if canonical_bytes(
            portable.portable_registry_manifest(
                driver._registry_manifest(fresh_registry)
            )
        ) != canonical_bytes(
            portable.portable_registry_manifest(historical_manifest)
        ):
            raise PortableOutcomeSuccessorError(
                f"portable registry changed:{arm}"
            )
        wrappers = [
            by_key[(arm, ordinal)]["scan_wrapper"]
            for ordinal in range(SEED_COUNT)
        ]
        adjudication = reconstructed.adjudicate_cohort(
            wrappers,
            tape_identity=reconstructed.tape_identity,
            row_order=runtime["row_order"],
            run_identity=reconstructed.run_identity,
            package_hashes=runtime["package_hashes"],
        )
        if adjudication != preserved_exposure["arms"][arm][
            "registry_adjudication"
        ]:
            raise PortableOutcomeSuccessorError(
                f"historical registry adjudication changed:{arm}"
            )
        registries[arm] = reconstructed
        registry_rows[arm] = {
            "registry_id": reconstructed.registry_id,
            "manifest_digest": digest(historical_manifest),
            "wrapper_count": len(wrappers),
            "adjudication_digest": digest(adjudication),
        }
    historical_runtime = portable._build_historical_runtime(
        runtime, registries
    )
    if historical_runtime["restored"] is not runtime["restored"]:
        raise PortableOutcomeSuccessorError(
            "live restored mapping was not handed through directly"
        )
    rebuilt_exposure = execution.assemble_production_exposure(
        historical_runtime, mapping["stored_results"]
    )
    exposure_bytes = historical.pretty_json_bytes(rebuilt_exposure)
    exposure_sha256 = portable.require_exact_artifact_bytes(
        label="exposure",
        rebuilt=exposure_bytes,
        preserved_path=historical.EXPOSURE_PATH,
    )
    launch_readiness = historical.load_and_verify_launch_readiness(
        committed=True
    )
    rebuilt_execution = historical.build_execution_manifest(
        historical_runtime,
        rebuilt_exposure,
        historical.sha256_bytes(exposure_bytes),
        launch_readiness=launch_readiness,
    )
    execution_bytes = historical.pretty_json_bytes(rebuilt_execution)
    execution_sha256 = portable.require_exact_artifact_bytes(
        label="execution",
        rebuilt=execution_bytes,
        preserved_path=historical.EXECUTION_MANIFEST_PATH,
    )
    rebuilt_completion = portable.reconstruct_completion_marker(
        rebuilt_exposure, rebuilt_execution, historical_state.plan
    )
    completion_bytes = historical.pretty_json_bytes(rebuilt_completion)
    completion_sha256 = portable.require_exact_artifact_bytes(
        label="completion",
        rebuilt=completion_bytes,
        preserved_path=historical.EXPOSURE_COMPLETION_PATH,
    )
    historical._validate_completion_identity(
        rebuilt_exposure, rebuilt_execution, rebuilt_completion
    )
    completed = {
        "runtime": historical_runtime,
        "exposure": rebuilt_exposure,
        "execution_manifest": rebuilt_execution,
        "completion": rebuilt_completion,
    }
    audit = {
        "verified_organism_count": len(runtime["restored"]),
        "portable_binding_count": len(mapping["bindings"]),
        "mapping_digest": mapping["mapping_digest"],
        "registry_rows": registry_rows,
        "exposure_sha256": exposure_sha256,
        "exposure_digest": rebuilt_exposure["exposure_digest"],
        "execution_sha256": execution_sha256,
        "execution_digest": rebuilt_execution["execution_manifest_digest"],
        "completion_sha256": completion_sha256,
        "completion_digest": rebuilt_completion["completion_digest"],
        "restored_mapping_direct": True,
        "outcome_access": copy.deepcopy(ZERO_OUTCOME),
    }
    audit["handoff_digest"] = digest(audit)
    return completed, audit


def build_portable_completed() -> tuple[dict[str, Any], dict[str, Any]]:
    source, package = verify_package_freeze()
    aggregate, reference_rows = _portable_reference()
    started = (ROOT / historical.SCIENCE_STARTED_PATH).exists()
    if not started:
        observed = portable.verify_aggregate()
        if observed["aggregate_digest"] != EXPECTED_AGGREGATE_DIGEST:
            raise PortableOutcomeSuccessorError(
                "live portable aggregate changed before science"
            )
        if portable.verify_zero_outcome_access() != {
            "count": 0,
            "event_ids": [],
            "science_paths_absent": True,
        }:
            raise PortableOutcomeSuccessorError(
                "outcome state changed before science"
            )
    historical_state = portable.validate_historical_journal()
    runtime, launcher_path_proof = _build_portable_runtime()
    classification = load_json(ROOT / portable.CLASSIFICATION_MANIFEST_PATH)
    mapping = _verify_live_mapping(
        runtime=runtime,
        historical_state=historical_state,
        reference_rows=reference_rows,
        classification=classification,
    )
    completed, audit = _reconstruct_completed(
        runtime=runtime,
        historical_state=historical_state,
        mapping=mapping,
    )
    audit.update({
        "source_manifest_digest": source["source_manifest_digest"],
        "package_manifest_digest": package["package_manifest_digest"],
        "portable_aggregate_digest": aggregate["aggregate_digest"],
        "portable_cohort_digest": aggregate["portable_cohort_digest"],
        "historical_science_code_digest": science_code_digest(),
        "launcher_path_proof": launcher_path_proof,
    })
    audit["handoff_digest"] = digest(
        {key: item for key, item in audit.items() if key != "handoff_digest"}
    )
    return completed, audit


def execute_unchanged_science_suffix(
    completed: Mapping[str, Any],
    *,
    science_function: Callable[[], Mapping[str, Any]] = historical.run_science,
) -> dict[str, Any]:
    original_provider = science_function.__globals__.get(
        "validate_completed_exposure"
    )
    private_globals: MutableMapping[str, Any] = dict(
        science_function.__globals__
    )

    def verified_completed_provider() -> Mapping[str, Any]:
        return completed

    private_globals["validate_completed_exposure"] = (
        verified_completed_provider
    )
    delegated = types.FunctionType(
        science_function.__code__,
        private_globals,
        name=science_function.__name__,
        argdefs=science_function.__defaults__,
        closure=science_function.__closure__,
    )
    delegated.__kwdefaults__ = science_function.__kwdefaults__
    if delegated.__code__ is not science_function.__code__:
        raise PortableOutcomeSuccessorError(
            "historical science code object was not preserved"
        )
    try:
        result = dict(delegated())
    finally:
        if science_function.__globals__.get(
            "validate_completed_exposure"
        ) is not original_provider:
            raise PortableOutcomeSuccessorError(
                "historical module global provider changed"
            )
    return result


def _load_existing_result() -> dict[str, Any]:
    payload = gzip.decompress((ROOT / historical.RESULT_PATH).read_bytes())
    value = json.loads(payload.decode("ascii"))
    if not isinstance(value, dict):
        raise PortableOutcomeSuccessorError("canonical result is not an object")
    if value.get("canonical_result_digest") != digest({
        key: item
        for key, item in value.items()
        if key != "canonical_result_digest"
    }):
        raise PortableOutcomeSuccessorError("canonical result digest changed")
    return value


def _completion_record(
    *,
    service: Mapping[str, Any],
    handoff: Mapping[str, Any],
    result: Mapping[str, Any],
    reconstructed_after_interruption: bool,
) -> dict[str, Any]:
    accounting = result.get("outcome_accounting")
    if (
        result.get("all_32_committed") is not True
        or not isinstance(accounting, dict)
        or accounting.get("status") != "known"
        or accounting.get("count") != EXPECTED_OUTCOME_COUNT
    ):
        raise PortableOutcomeSuccessorError(
            "canonical outcome completion gate changed"
        )
    value = {
        "schema_version": "native_v2_portable_outcome_completion.v1",
        "package_id": PACKAGE_ID,
        "outcome_attempt_id": OUTCOME_ATTEMPT_ID,
        "service": copy.deepcopy(dict(service)),
        "handoff": copy.deepcopy(dict(handoff)),
        "historical_result": {
            "path": historical.RESULT_PATH.as_posix(),
            "sha256": sha256_file(ROOT / historical.RESULT_PATH),
            "digest": result["canonical_result_digest"],
        },
        "outcome_accounting": copy.deepcopy(accounting),
        "all_32_committed": True,
        "reconstructed_after_interruption": reconstructed_after_interruption,
    }
    value["completion_digest"] = digest(value)
    return value


def _record_preoutcome_failure(exc: Exception) -> None:
    if (ROOT / historical.SCIENCE_STARTED_PATH).exists():
        return
    if (ROOT / PREOUTCOME_FAILURE_PATH).exists():
        return
    value = {
        "schema_version": "native_v2_portable_outcome_preoutcome_failure.v1",
        "package_id": PACKAGE_ID,
        "outcome_attempt_id": OUTCOME_ATTEMPT_ID,
        "exception_type": type(exc).__name__,
        "detail": str(exc),
        "traceback_tail": traceback.format_exc().splitlines()[-20:],
        "outcome_access": copy.deepcopy(ZERO_OUTCOME),
    }
    value["failure_digest"] = digest(value)
    historical.atomic_json(ROOT / PREOUTCOME_FAILURE_PATH, value)


def run_science() -> dict[str, Any]:
    require_runtime_worktree()
    service = verify_service_context()
    verify_package_freeze()
    if (ROOT / COMPLETION_PATH).exists():
        raise FileExistsError("portable outcome completion already exists")
    if (ROOT / historical.SCIENCE_FAILURE_PATH).exists():
        raise PortableOutcomeSuccessorError(
            "historical science has a terminal failure"
        )
    try:
        completed, handoff = build_portable_completed()
    except Exception as exc:
        _record_preoutcome_failure(exc)
        raise
    if (ROOT / historical.RESULT_PATH).exists():
        result = _load_existing_result()
        reconstructed = True
    else:
        result = execute_unchanged_science_suffix(completed)
        reconstructed = False
    completion = _completion_record(
        service=service,
        handoff=handoff,
        result=result,
        reconstructed_after_interruption=reconstructed,
    )
    historical.atomic_json(ROOT / COMPLETION_PATH, completion)
    return completion


def _print(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, sort_keys=True, indent=2))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    freeze = commands.add_parser("freeze")
    freeze.add_argument("--source-commit", required=True)
    commands.add_parser("verify-package")
    commands.add_parser("run-science")
    args = parser.parse_args(argv)
    if args.command == "freeze":
        value = freeze_package(args.source_commit)
    elif args.command == "verify-package":
        source, package = verify_package_freeze()
        value = {
            "source_manifest_digest": source["source_manifest_digest"],
            "package_manifest_digest": package["package_manifest_digest"],
            "historical_science_code_digest": science_code_digest(),
            "outcome_access": copy.deepcopy(ZERO_OUTCOME),
        }
    else:
        value = run_science()
    _print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
