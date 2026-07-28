"""Data-free package-alias compatibility closure for the frozen V2 cohort.

This outer package preserves every prior runner and artifact.  It derives the
laboratory registry's stable alias keys from the registry's own declared
alias-to-path table, while retaining the complete frozen path-keyed map.
Readiness constructs registries only and stops before the first exposure probe.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import inspect
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import textwrap
import time
from typing import Any, Callable, Mapping, MutableMapping, Sequence

import chess
from recon_lite import FrameContext, FrameKind

from recon_lite_chess.autogrowth import (
    native_prospective_evidence_authority_v2_lab as laboratory,
)
from recon_lite_chess.autogrowth import (
    native_v2_fresh_discriminator_review_repair_v2 as driver,
)
from recon_lite_chess.autogrowth import (
    native_v2_frozen_cohort_execution_adapter_freeze as stopped_adapter,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2_lab import (
    V2LaboratoryRegistry,
)


ROOT = driver.ROOT
PACKAGE_ID = "native_v2_frozen_cohort_package_alias_compatibility_reclosure.v1"
MODULE_PATH = (
    "recon_lite_chess.autogrowth."
    "native_v2_frozen_cohort_package_alias_compatibility_reclosure"
)
STARTING_HEAD = "b9e3b9392d91da4db495e79fc97f3820e31654af"
ACCEPTED_COHORT_DIGEST = (
    "a144fe94f4479c819756dfc44b22a2594e2b9df09367d571d39ab54007560bb8"
)
STOPPED_EXPOSURE_FAILURE_SHA256 = (
    "1e7713a5ef3b33e46d61fa7525e95f430126996b48477f96bbc5ee871886ab9f"
)
STOPPED_EXPOSURE_FAILURE_DIGEST = (
    "e76be5210359e1dc5a3aed02d18bd081a1f2e6555a64af519af3763d8936a110"
)

PACKAGE_DIR = Path(
    "reports/autogrowth/native_authority/"
    "v2_frozen_cohort_package_alias_compatibility_reclosure"
)
SOURCE_MANIFEST_PATH = PACKAGE_DIR / "source_manifest.json"
ARTIFACT_BINDING_PATH = PACKAGE_DIR / "artifact_binding_manifest.json"
READINESS_PATH = PACKAGE_DIR / "readiness.json"
READINESS_FAILURE_PATH = PACKAGE_DIR / "readiness_failure.json"
EXPOSURE_PATH = PACKAGE_DIR / "preoutcome_exposure.json"
EXPOSURE_FAILURE_PATH = PACKAGE_DIR / "exposure_failure.json"
EXECUTION_MANIFEST_PATH = PACKAGE_DIR / "execution_manifest.json"
SCIENCE_JOURNAL_DIR = PACKAGE_DIR / "science_journal"
SCIENCE_CARRIER_DIR = PACKAGE_DIR / "science_carrier"
RESULT_PATH = PACKAGE_DIR / "canonical_result.json.gz"
SCIENCE_FAILURE_PATH = PACKAGE_DIR / "science_failure.json"

SOURCE_FILES = (
    "src/recon_lite_chess/autogrowth/"
    "native_v2_frozen_cohort_package_alias_compatibility_reclosure.py",
    "tests/autogrowth/"
    "test_native_v2_frozen_cohort_package_alias_compatibility_reclosure.py",
    "docs/autogrowth/"
    "NATIVE_V2_FROZEN_COHORT_PACKAGE_ALIAS_COMPATIBILITY_RECLOSURE_"
    "PREREGISTRATION_20260727.md",
)

DETERMINISTIC_ENV = copy.deepcopy(stopped_adapter.DETERMINISTIC_ENV)
PUBLIC_COMMANDS = ("verify-readiness", "run-exposure", "run-science")

# Exact aliases used by the mechanically copied frozen reconstruction.
ARMS = driver.ARMS
EXPERIMENT_ID = driver.EXPERIMENT_ID
FreshScientificIntegrityError = driver.FreshScientificIntegrityError
MIN_QUALIFYING_SEEDS = driver.MIN_QUALIFYING_SEEDS
MIN_TARGET_OPPORTUNITIES = driver.MIN_TARGET_OPPORTUNITIES
OutcomeAccessGuard = driver.OutcomeAccessGuard
SEED_COUNT = driver.SEED_COUNT
_complete_snapshot_identity = driver._complete_snapshot_identity
_registry_manifest = driver._registry_manifest
_suffix_registered_rows = driver._suffix_registered_rows
_target_counts_from_scan = driver._target_counts_from_scan
_verify_prefix_snapshot_metadata = driver._verify_prefix_snapshot_metadata
classification_visible_projection = driver.classification_visible_projection
digest = driver.digest
ecology_rows = driver.ecology_rows
target_cell_id = driver.target_cell_id
verify_bound_preflight_authorization = driver.verify_bound_preflight_authorization


class CompatibilityClosureError(RuntimeError):
    """The compatibility package or one of its frozen inputs changed."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CompatibilityClosureError(f"expected JSON object:{path}")
    return value


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


def _git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def _require_clean_worktree() -> None:
    if _git("status", "--porcelain=v1"):
        raise CompatibilityClosureError(
            "compatibility command requires a clean worktree"
        )


def _require_commit(commit: str) -> None:
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
        raise CompatibilityClosureError(
            f"required commit is not an ancestor:{commit}"
        )


def _path_bytes_in_head(relative: Path) -> bytes:
    completed = subprocess.run(
        ("git", "show", f"HEAD:{relative.as_posix()}"),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise CompatibilityClosureError(
            f"required artifact is not committed:{relative}"
        )
    return completed.stdout


def require_committed_artifact(relative: Path) -> dict[str, Any]:
    payload = (ROOT / relative).read_bytes()
    if payload != _path_bytes_in_head(relative):
        raise CompatibilityClosureError(
            f"working artifact differs from HEAD:{relative}"
        )
    return {
        "path": relative.as_posix(),
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def verify_self_digest(
    value: Mapping[str, Any], field: str, *, label: str
) -> str:
    unsigned = {key: item for key, item in value.items() if key != field}
    observed = digest(unsigned)
    if value.get(field) != observed:
        raise CompatibilityClosureError(f"{label} self-digest changed")
    return observed


def build_public_command(command: str) -> tuple[str, ...]:
    if command not in PUBLIC_COMMANDS:
        raise CompatibilityClosureError(f"unknown public command:{command}")
    return (sys.executable, "-m", MODULE_PATH, command)


def declared_alias_paths(
    supplied: Mapping[str, str] | None = None,
) -> dict[str, str]:
    declared = dict(
        laboratory.POLICY_CRITICAL_SOURCE_PATHS
        if supplied is None else supplied
    )
    canonical = dict(laboratory.POLICY_CRITICAL_SOURCE_PATHS)
    if declared != canonical:
        raise CompatibilityClosureError(
            "declared alias-to-path mapping differs from registry"
        )
    if len(declared) != 13:
        raise CompatibilityClosureError(
            f"registry alias count changed:{len(declared)}"
        )
    return declared


def diagnose_original_package_map(
    original: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    path_map = dict(
        driver.laboratory_package_hashes()
        if original is None else original
    )
    declared = declared_alias_paths()
    expected_aliases = laboratory.policy_critical_package_hashes(ROOT)
    if set(expected_aliases) != set(declared):
        raise CompatibilityClosureError(
            "registry expected-alias coverage changed"
        )
    rows = []
    for alias, relative in sorted(declared.items()):
        runtime_key = "runtime:" + relative
        if runtime_key not in path_map:
            raise CompatibilityClosureError(
                f"original map lacks declared runtime path:{runtime_key}"
            )
        file_digest = sha256_file(ROOT / relative)
        runtime_digest = path_map[runtime_key]
        expected_digest = expected_aliases[alias]
        if not runtime_digest == file_digest == expected_digest:
            raise CompatibilityClosureError(
                f"alias/path/file digest mismatch:{alias}"
            )
        rows.append({
            "alias": alias,
            "declared_path": relative,
            "runtime_key": runtime_key,
            "alias_present": alias in path_map,
            "runtime_digest": runtime_digest,
            "file_digest": file_digest,
            "expected_alias_digest": expected_digest,
        })
    if any(row["alias_present"] for row in rows):
        raise CompatibilityClosureError(
            "original path-keyed map unexpectedly contains registry aliases"
        )
    value = {
        "alias_count": len(rows),
        "all_original_aliases_absent": True,
        "all_path_file_alias_digests_equal": True,
        "original_key_count": len(path_map),
        "original_map_digest": digest(path_map),
        "rows": rows,
    }
    value["diagnostic_digest"] = digest(value)
    return value


def derive_expanded_package_map(
    original: Mapping[str, str],
    *,
    declared_paths: Mapping[str, str] | None = None,
) -> dict[str, str]:
    declared = declared_alias_paths(declared_paths)
    diagnosis = diagnose_original_package_map(original)
    expanded = dict(original)
    rows = {row["alias"]: row for row in diagnosis["rows"]}
    for alias, relative in sorted(declared.items()):
        row = rows[alias]
        if row["declared_path"] != relative:
            raise CompatibilityClosureError(
                f"alias mapped to wrong declared path:{alias}"
            )
        expanded[alias] = str(row["runtime_digest"])
    return validate_expanded_package_map(expanded, original=original)


def validate_expanded_package_map(
    supplied: Mapping[str, str],
    *,
    original: Mapping[str, str] | None = None,
) -> dict[str, str]:
    original_map = dict(
        driver.laboratory_package_hashes()
        if original is None else original
    )
    diagnosis = diagnose_original_package_map(original_map)
    aliases = declared_alias_paths()
    expected_keys = set(original_map) | set(aliases)
    supplied_keys = set(supplied)
    if supplied_keys != expected_keys:
        missing = sorted(expected_keys - supplied_keys)
        extra = sorted(supplied_keys - expected_keys)
        raise CompatibilityClosureError(
            f"expanded package-map key coverage changed:"
            f"missing={missing}:extra={extra}"
        )
    for key, expected in original_map.items():
        if supplied.get(key) != expected:
            raise CompatibilityClosureError(
                f"original path-keyed entry changed:{key}"
            )
    rows = {row["alias"]: row for row in diagnosis["rows"]}
    for alias in sorted(aliases):
        expected = rows[alias]["runtime_digest"]
        if supplied.get(alias) != expected:
            raise CompatibilityClosureError(
                f"registry alias digest changed:{alias}"
            )
    return {key: str(supplied[key]) for key in sorted(supplied)}


def expanded_package_map() -> dict[str, str]:
    original = driver.laboratory_package_hashes()
    return derive_expanded_package_map(original)


def expanded_package_map_manifest(
    package_map: Mapping[str, str],
) -> dict[str, Any]:
    validated = validate_expanded_package_map(package_map)
    aliases = declared_alias_paths()
    original = driver.laboratory_package_hashes()
    value = {
        "original_key_count": len(original),
        "expanded_key_count": len(validated),
        "alias_count": len(aliases),
        "original_map_digest": digest(original),
        "expanded_map_digest": digest(validated),
        "aliases": {
            alias: {
                "declared_path": aliases[alias],
                "runtime_key": "runtime:" + aliases[alias],
                "digest": validated[alias],
            }
            for alias in sorted(aliases)
        },
        "complete_original_map_retained": all(
            validated.get(key) == item for key, item in original.items()
        ),
    }
    value["manifest_digest"] = digest(value)
    return value


def reconstruct_exposure_value_with_expanded_map(
    *,
    identity: Mapping[str, Any],
    prefix: Mapping[str, Any],
    ecology: Mapping[str, Any],
    manifest: Mapping[str, Any],
    receipt: Mapping[str, Any],
    restored: Mapping[tuple[int, str], NativeProspectiveAuthorityV2],
    guard: OutcomeAccessGuard,
    package_hashes: Mapping[str, str],
) -> dict[str, Any]:
    prefix_verification = _verify_prefix_snapshot_metadata(
        prefix, manifest, restored
    )
    package_hashes = validate_expanded_package_map(package_hashes)
    registry_package_hash = digest(package_hashes)
    row_order = tuple(row["row_id"] for row in ecology_rows(ecology, "suffix"))
    projections: dict[int, dict[str, list[dict[str, Any]]]] = {
        ordinal: {} for ordinal in range(SEED_COUNT)
    }
    arms_result = {}
    target_counts: dict[int, dict[str, dict[str, Any]]] = {
        ordinal: {} for ordinal in range(SEED_COUNT)
    }
    for arm in ARMS:
        payloads = {}
        exposure_rows = {}
        for ordinal in range(SEED_COUNT):
            organism_id = f"seed-{ordinal:02d}"
            payloads[organism_id] = restored[(ordinal, arm)].dumps()
            exposure_rows[organism_id] = _suffix_registered_rows(
                ecology, arm, ordinal
            )
        run_identity = digest({
            "experiment_id": EXPERIMENT_ID,
            "phase": "preoutcome_exposure",
            "arm": arm,
            "outer_manifest_sha256": identity["outer_sha256"],
        })
        registry = V2LaboratoryRegistry.freeze(
            payloads,
            exposure_rows=exposure_rows,
            row_order=row_order,
            run_identity=run_identity,
            package_hashes=package_hashes,
        )
        scan_wrappers = []
        per_seed = []
        for ordinal in range(SEED_COUNT):
            organism_id = f"seed-{ordinal:02d}"
            wrapper = restored[(ordinal, arm)]
            targets = prefix["results"][ordinal]["targets"]
            before = wrapper.continuation_digest()
            commitments = []
            visible = []
            for row, registered in zip(
                ecology_rows(ecology, "suffix"),
                exposure_rows[organism_id],
                strict=True,
            ):
                commitment = wrapper.probe_real_exposure(FrameContext(
                    registered.frame_id,
                    FrameKind.REAL,
                    values={"board": chess.Board(registered.predecessor_fen)},
                ))
                commitments.append(commitment)
                visible.append(classification_visible_projection(
                    wrapper,
                    commitment,
                    commitment.trace,
                    planted_cell_id=target_cell_id(targets, "planted"),
                    spurious_cell_id=target_cell_id(targets, "selected_spurious"),
                    row_id=str(row["row_id"]),
                ))
            if wrapper.continuation_digest() != before:
                raise FreshScientificIntegrityError("exposure changed restored snapshot")
            scan_wrapper = registry.scan(
                organism_id,
                payloads[organism_id],
                commitments,
                tape_identity=registry.tape_identity,
                row_order=row_order,
                run_identity=run_identity,
                package_hashes=package_hashes,
            )
            scan_wrappers.append(scan_wrapper)
            counts = _target_counts_from_scan(scan_wrapper["scan"], targets)
            target_counts[ordinal][arm] = counts
            projections[ordinal][arm] = visible
            per_seed.append({
                "ordinal": ordinal,
                "organism_id": organism_id,
                "continuation_digest": before,
                "target_counts": counts,
                "scan_wrapper_digest": digest(scan_wrapper),
                "projection_digests": [
                    item["projection_digest"] for item in visible
                ],
            })
        adjudication = registry.adjudicate_cohort(
            scan_wrappers,
            tape_identity=registry.tape_identity,
            row_order=row_order,
            run_identity=run_identity,
            package_hashes=package_hashes,
        )
        arms_result[arm] = {
            "registry": _registry_manifest(registry),
            "registry_adjudication": adjudication,
            "per_seed": per_seed,
            "scan_wrapper_set_digest": digest(scan_wrappers),
        }
    parity_rows = []
    for ordinal in range(SEED_COUNT):
        for row_index, row_id in enumerate(row_order):
            values = {
                arm: projections[ordinal][arm][row_index] for arm in ARMS
            }
            comparable = {
                arm: {
                    key: item for key, item in value.items()
                    if key != "projection_digest"
                }
                for arm, value in values.items()
            }
            if not (comparable["A"] == comparable["B"] == comparable["C"]):
                raise FreshScientificIntegrityError(
                    f"control_exposure_parity_failure:{ordinal}:{row_id}"
                )
            parity_rows.append({
                "ordinal": ordinal,
                "row_id": row_id,
                "equal": True,
                "projection_digests": {
                    arm: values[arm]["projection_digest"] for arm in ARMS
                },
            })
    per_seed_qualification = []
    for ordinal in range(SEED_COUNT):
        qualified = all(
            target_counts[ordinal][arm][name]["distinct_opportunities"]
            >= MIN_TARGET_OPPORTUNITIES
            for arm in ARMS
            for name in ("planted", "selected_spurious")
        )
        per_seed_qualification.append({
            "ordinal": ordinal,
            "qualified": qualified,
        })
    qualifying = sum(item["qualified"] for item in per_seed_qualification)
    authorization = {
        "schema_version": "native_v2_review_repair_v2_preflight_authorization.v1",
        "experiment_id": EXPERIMENT_ID,
        "registry_package_hash": registry_package_hash,
        "expected_global_preflight": {
            "receipt_digest": receipt["receipt_digest"],
            "snapshot_manifest_digest": manifest["manifest_digest"],
            "registry_package_hash": registry_package_hash,
        },
        "complete_96_required": True,
        "outcome_access_at_freeze": guard.manifest(),
    }
    authorization["authorization_digest"] = digest(authorization)
    verify_bound_preflight_authorization(
        receipt=receipt,
        snapshot_manifest=manifest,
        authorization=authorization,
    )
    value = {
        "schema_version": "native_v2_review_repair_v2_preoutcome_exposure.v1",
        "experiment_id": EXPERIMENT_ID,
        "outer_manifest_sha256": identity["outer_sha256"],
        "snapshot_manifest_digest": manifest["manifest_digest"],
        "complete_snapshot_identity": _complete_snapshot_identity(
            manifest, restored
        ),
        "prefix_candidate_verification": prefix_verification,
        "global_preflight_receipt": copy.deepcopy(dict(receipt)),
        "preflight_authorization": authorization,
        "registry_package_hash": registry_package_hash,
        "arms": arms_result,
        "parity_rows": parity_rows,
        "parity_row_count": len(parity_rows),
        "parity_digest": digest(parity_rows),
        "per_seed_qualification": per_seed_qualification,
        "qualification_digest": digest(per_seed_qualification),
        "qualifying_seed_count": qualifying,
        "required_qualifying_seed_count": MIN_QUALIFYING_SEEDS,
        "admitted": qualifying >= MIN_QUALIFYING_SEEDS,
        "stop_reason": (
            None if qualifying >= MIN_QUALIFYING_SEEDS
            else "prospective_evidence_starvation"
        ),
        "outcome_access": guard.manifest(),
    }
    value["exposure_digest"] = digest(value)
    return value


def _package_acquisition_statement(
    function: Callable[..., Any],
) -> tuple[ast.FunctionDef, ast.stmt]:
    parsed = ast.parse(textwrap.dedent(inspect.getsource(function)))
    node = parsed.body[0]
    if not isinstance(node, ast.FunctionDef):
        raise CompatibilityClosureError("reconstruction is not a function")
    matches = [
        statement
        for statement in node.body
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == "package_hashes"
        )
    ]
    if len(matches) != 1:
        raise CompatibilityClosureError(
            "reconstruction package acquisition is not unique"
        )
    return node, matches[0]


def _normalized_reconstruction_ast(
    function: Callable[..., Any], *, compatibility: bool
) -> tuple[str, str]:
    node, acquisition = _package_acquisition_statement(function)
    node = copy.deepcopy(node)
    node.name = "_reconstruct_exposure_value"
    node.body = [
        statement
        for statement in node.body
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == "package_hashes"
        )
    ]
    if compatibility:
        index = next(
            (
                position
                for position, item in enumerate(node.args.kwonlyargs)
                if item.arg == "package_hashes"
            ),
            None,
        )
        if index is None:
            raise CompatibilityClosureError(
                "compatibility reconstruction lacks explicit package map"
            )
        del node.args.kwonlyargs[index]
        del node.args.kw_defaults[index]
    elif any(
        item.arg == "package_hashes" for item in node.args.kwonlyargs
    ):
        raise CompatibilityClosureError(
            "frozen reconstruction unexpectedly accepts a package map"
        )
    return (
        ast.dump(node, annotate_fields=True, include_attributes=False),
        ast.dump(acquisition, annotate_fields=True, include_attributes=False),
    )


def reconstruction_ast_comparison() -> dict[str, Any]:
    frozen_tree, frozen_acquisition = _normalized_reconstruction_ast(
        driver._reconstruct_exposure_value, compatibility=False
    )
    bounded_tree, bounded_acquisition = _normalized_reconstruction_ast(
        reconstruct_exposure_value_with_expanded_map, compatibility=True
    )
    if frozen_tree != bounded_tree:
        raise CompatibilityClosureError(
            "bounded reconstruction differs beyond package-map acquisition"
        )
    if "laboratory_package_hashes" not in frozen_acquisition:
        raise CompatibilityClosureError(
            "frozen reconstruction acquisition changed"
        )
    if "validate_expanded_package_map" not in bounded_acquisition:
        raise CompatibilityClosureError(
            "bounded reconstruction does not validate explicit package map"
        )
    value = {
        "normalized_equal": True,
        "frozen_function": (
            driver._reconstruct_exposure_value.__module__
            + "."
            + driver._reconstruct_exposure_value.__name__
        ),
        "bounded_function": (
            reconstruct_exposure_value_with_expanded_map.__module__
            + "."
            + reconstruct_exposure_value_with_expanded_map.__name__
        ),
        "normalized_ast_digest": hashlib.sha256(
            frozen_tree.encode("utf-8")
        ).hexdigest(),
        "frozen_acquisition_ast": frozen_acquisition,
        "bounded_acquisition_ast": bounded_acquisition,
    }
    value["comparison_digest"] = digest(value)
    return value


CRITICAL_BINDINGS = {
    "driver": (
        "_reconstruct_exposure_value",
        "_registry_manifest",
        "_suffix_registered_rows",
        "_verify_prefix_snapshot_metadata",
        "laboratory_package_hashes",
        "execute_fresh_seed_atomically",
        "committed_seed_results",
        "adjudicate_committed_results",
    ),
    "laboratory": (
        "POLICY_CRITICAL_SOURCE_PATHS",
        "policy_critical_package_hashes",
        "V2LaboratoryRegistry",
    ),
    "stopped_adapter": (
        "build_readiness_context",
        "run_exposure",
        "run_science",
        "SOURCE_MANIFEST_PATH",
        "ARTIFACT_BINDING_PATH",
        "READINESS_PATH",
        "EXPOSURE_FAILURE_PATH",
    ),
}


def capture_critical_bindings() -> dict[tuple[str, str], Any]:
    modules = {
        "driver": driver,
        "laboratory": laboratory,
        "stopped_adapter": stopped_adapter,
    }
    return {
        (module_name, name): getattr(modules[module_name], name)
        for module_name, names in CRITICAL_BINDINGS.items()
        for name in names
    }


def require_bindings_unchanged(
    before: Mapping[tuple[str, str], Any],
) -> list[str]:
    after = capture_critical_bindings()
    changed = [
        f"{module_name}.{name}"
        for (module_name, name), value in before.items()
        if after[(module_name, name)] is not value
    ]
    if changed:
        raise CompatibilityClosureError(
            f"module-global replacement detected:{changed}"
        )
    return [
        f"{module_name}.{name}"
        for module_name, name in sorted(before)
    ]


def _path_identity(relative: Path) -> dict[str, Any]:
    path = ROOT / relative
    if not path.exists():
        return {
            "path": relative.as_posix(),
            "exists": False,
            "size": None,
            "sha256": None,
        }
    if not path.is_file():
        raise CompatibilityClosureError(
            f"preserved artifact is not a file:{relative}"
        )
    return {
        "path": relative.as_posix(),
        "exists": True,
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def preserved_adapter_identity() -> dict[str, Any]:
    paths = (
        stopped_adapter.SOURCE_MANIFEST_PATH,
        stopped_adapter.ARTIFACT_BINDING_PATH,
        stopped_adapter.READINESS_PATH,
        stopped_adapter.EXPOSURE_FAILURE_PATH,
    )
    rows = [_path_identity(path) for path in paths]
    failure = next(
        row
        for row in rows
        if row["path"] == stopped_adapter.EXPOSURE_FAILURE_PATH.as_posix()
    )
    if (
        failure["sha256"] != STOPPED_EXPOSURE_FAILURE_SHA256
        or not failure["exists"]
    ):
        raise CompatibilityClosureError(
            "stopped exposure failure artifact changed"
        )
    failure_value = _load_json(
        ROOT / stopped_adapter.EXPOSURE_FAILURE_PATH
    )
    verify_self_digest(
        failure_value,
        "failure_digest",
        label="stopped exposure failure",
    )
    if (
        failure_value.get("failure_digest")
        != STOPPED_EXPOSURE_FAILURE_DIGEST
        or failure_value.get("outcome_access")
        != {"count": 0, "event_ids": []}
    ):
        raise CompatibilityClosureError(
            "stopped exposure failure content changed"
        )
    return {"rows": rows, "digest": digest(rows)}


def new_output_paths() -> tuple[Path, ...]:
    return (
        SOURCE_MANIFEST_PATH,
        ARTIFACT_BINDING_PATH,
        READINESS_PATH,
        READINESS_FAILURE_PATH,
        EXPOSURE_PATH,
        EXPOSURE_FAILURE_PATH,
        EXECUTION_MANIFEST_PATH,
        SCIENCE_JOURNAL_DIR,
        SCIENCE_CARRIER_DIR,
        RESULT_PATH,
        SCIENCE_FAILURE_PATH,
    )


def verify_frozen_inputs() -> dict[str, Any]:
    _require_commit(STARTING_HEAD)
    stopped_package = stopped_adapter.verify_package_manifests()
    stopped_identity = preserved_adapter_identity()
    diagnosis = diagnose_original_package_map()
    expanded = expanded_package_map()
    map_manifest = expanded_package_map_manifest(expanded)
    ast_comparison = reconstruction_ast_comparison()
    fixed = stopped_adapter.verify_frozen_inputs()
    if (
        fixed["passing_launcher_result"]["cohort_digest"]
        != ACCEPTED_COHORT_DIGEST
    ):
        raise CompatibilityClosureError("accepted cohort digest changed")
    return {
        "starting_head": STARTING_HEAD,
        "accepted_cohort_digest": ACCEPTED_COHORT_DIGEST,
        "stopped_adapter_package": stopped_package,
        "stopped_adapter_identity": stopped_identity,
        "stopped_exposure_failure": {
            "path": stopped_adapter.EXPOSURE_FAILURE_PATH.as_posix(),
            "sha256": STOPPED_EXPOSURE_FAILURE_SHA256,
            "failure_digest": STOPPED_EXPOSURE_FAILURE_DIGEST,
        },
        "frozen_cohort_transport": copy.deepcopy(
            fixed["transport_checks"]
        ),
        "prefix_manifest_digest": fixed["prefix_manifest_digest"],
        "preflight_receipt_digest": fixed["preflight_receipt_digest"],
        "target_counts": copy.deepcopy(fixed["target_counts"]),
        "alias_diagnosis": diagnosis,
        "expanded_package_map": map_manifest,
        "expanded_package_entries": expanded,
        "bounded_reconstruction_ast": ast_comparison,
        "outcome_access": {"count": 0, "event_ids": []},
    }


def construct_registry_manifests_without_scanning(
    *,
    restored: Mapping[tuple[int, str], NativeProspectiveAuthorityV2],
    ecology: Mapping[str, Any],
    identity: Mapping[str, Any],
    package_hashes: Mapping[str, str],
) -> dict[str, Any]:
    validated = validate_expanded_package_map(package_hashes)
    map_digest = digest(validated)
    before_semantic = stopped_adapter._semantic_set(restored)
    bindings_before = capture_critical_bindings()
    stopped_before = preserved_adapter_identity()
    row_order = tuple(
        row["row_id"] for row in ecology_rows(ecology, "suffix")
    )
    registries = {}
    payload_count = 0
    registered_row_count = 0
    for arm in ARMS:
        payloads = {}
        exposure_rows = {}
        for ordinal in range(SEED_COUNT):
            organism_id = f"seed-{ordinal:02d}"
            payloads[organism_id] = restored[(ordinal, arm)].dumps()
            exposure_rows[organism_id] = _suffix_registered_rows(
                ecology, arm, ordinal
            )
        run_identity = digest({
            "experiment_id": EXPERIMENT_ID,
            "phase": "preoutcome_exposure",
            "arm": arm,
            "outer_manifest_sha256": identity["outer_sha256"],
        })
        registry = V2LaboratoryRegistry.freeze(
            payloads,
            exposure_rows=exposure_rows,
            row_order=row_order,
            run_identity=run_identity,
            package_hashes=validated,
        )
        if tuple(registry.package_hashes) != tuple(sorted(validated.items())):
            raise CompatibilityClosureError(
                f"registry package map changed:{arm}"
            )
        manifest = _registry_manifest(registry)
        registries[arm] = {
            "manifest": manifest,
            "manifest_digest": digest(manifest),
            "organism_count": len(registry.organisms),
            "registered_row_count": sum(
                len(rows) for _organism_id, rows in registry.exposure_rows
            ),
            "package_map_digest": digest(dict(registry.package_hashes)),
        }
        payload_count += len(payloads)
        registered_row_count += registries[arm]["registered_row_count"]
    after_semantic = stopped_adapter._semantic_set(restored)
    if before_semantic != after_semantic:
        raise CompatibilityClosureError(
            "registry construction changed candidate or graph state"
        )
    unchanged_bindings = require_bindings_unchanged(bindings_before)
    stopped_after = preserved_adapter_identity()
    if stopped_before != stopped_after:
        raise CompatibilityClosureError(
            "stopped adapter package changed during readiness"
        )
    if any(
        item["package_map_digest"] != map_digest
        or item["organism_count"] != 32
        for item in registries.values()
    ):
        raise CompatibilityClosureError(
            "real registry coverage or package map changed"
        )
    value = {
        "registry_count": len(registries),
        "payload_count": payload_count,
        "registered_row_count": registered_row_count,
        "row_order": list(row_order),
        "row_order_digest": digest(row_order),
        "expanded_package_map_digest": map_digest,
        "registries": registries,
        "semantic_state_before_digest": digest(before_semantic),
        "semantic_state_after_digest": digest(after_semantic),
        "candidate_or_graph_mutation_count": 0,
        "module_global_replacement_count": 0,
        "unchanged_module_global_bindings": unchanged_bindings,
        "stopped_adapter_identity_before": stopped_before,
        "stopped_adapter_identity_after": stopped_after,
        "registry_scan_count": 0,
        "cohort_aggregation_count": 0,
        "organism_exposure_probe_count": 0,
        "outcome_access": {"count": 0, "event_ids": []},
        "stopped_before_first_organism_exposure_probe": True,
    }
    value["registry_closure_digest"] = digest(value)
    return value


def build_execution_manifest(
    *,
    identity: Mapping[str, Any],
    prefix: Mapping[str, Any],
    ecology: Mapping[str, Any],
    manifest: Mapping[str, Any],
    exposure: Mapping[str, Any],
    readiness: Mapping[str, Any],
    package_hashes: Mapping[str, str],
    exposure_path: Path = EXPOSURE_PATH,
) -> dict[str, Any]:
    validated = validate_expanded_package_map(package_hashes)
    if exposure.get("outcome_access") != {"count": 0, "event_ids": []}:
        raise CompatibilityClosureError("exposure opened an outcome")
    if exposure.get("registry_package_hash") != digest(validated):
        raise CompatibilityClosureError(
            "exposure used a different expanded package map"
        )
    value = {
        "schema_version": (
            "native_v2_package_alias_compatibility_execution_manifest.v1"
        ),
        "package_id": PACKAGE_ID,
        "experiment_id": EXPERIMENT_ID,
        "source_tree_identity": {
            "source_freeze_commit": identity["source_freeze_commit"],
            "source_runtime_digest": identity["source_runtime_digest"],
        },
        "experiment_package_identity": {
            "outer_manifest_sha256": identity["outer_sha256"],
            "expanded_laboratory_package_digest": digest(validated),
            "expanded_package_map_manifest": (
                expanded_package_map_manifest(validated)
            ),
        },
        "compatibility_package": {
            "source_manifest_sha256": sha256_file(
                ROOT / SOURCE_MANIFEST_PATH
            ),
            "artifact_binding_sha256": sha256_file(
                ROOT / ARTIFACT_BINDING_PATH
            ),
            "readiness_sha256": sha256_file(ROOT / READINESS_PATH),
            "readiness_digest": readiness["readiness_digest"],
        },
        "seed_manifest": {
            "sha256": sha256_file(ROOT / driver.SEED_MANIFEST_PATH),
            "digest": driver._load_json(
                ROOT / driver.SEED_MANIFEST_PATH
            )["seed_manifest_digest"],
        },
        "ecology_manifest": {
            "sha256": sha256_file(ROOT / driver.ECOLOGY_MANIFEST_PATH),
            "digest": ecology["ecology_digest"],
        },
        "prefix_manifest": {
            "sha256": sha256_file(ROOT / driver.PREFIX_MANIFEST_PATH),
            "digest": prefix["prefix_manifest_digest"],
            "candidate_manifest_digest": driver._candidate_manifest_digest(
                prefix
            ),
        },
        "snapshot_manifest": {
            "sha256": sha256_file(
                ROOT / stopped_adapter.RAW_SNAPSHOT_MANIFEST_PATH
            ),
            "digest": manifest["manifest_digest"],
            "entry_set_digest": digest(manifest["entries"]),
            "artifact_count": len(manifest["entries"]),
        },
        "exposure_artifact": {
            "path": exposure_path.as_posix(),
            "sha256": sha256_file(ROOT / exposure_path),
            "digest": exposure["exposure_digest"],
        },
        "parity_digest": exposure["parity_digest"],
        "qualification_digest": exposure["qualification_digest"],
        "qualifying_seed_count": exposure["qualifying_seed_count"],
        "required_qualifying_seed_count": exposure[
            "required_qualifying_seed_count"
        ],
        "admitted": exposure["admitted"],
        "zero_outcome_read_result": copy.deepcopy(
            exposure["outcome_access"]
        ),
        "complete_snapshot_identity": copy.deepcopy(
            exposure["complete_snapshot_identity"]
        ),
        "global_preflight_receipt_digest": exposure[
            "global_preflight_receipt"
        ]["receipt_digest"],
    }
    value["execution_manifest_digest"] = digest(value)
    return value


def load_and_verify_readiness(*, committed: bool) -> dict[str, Any]:
    if committed:
        require_committed_artifact(READINESS_PATH)
    value = _load_json(ROOT / READINESS_PATH)
    verify_self_digest(value, "readiness_digest", label="readiness")
    if (
        value.get("cohort_digest") != ACCEPTED_COHORT_DIGEST
        or value.get("verified_seed_count") != 32
        or value.get("verified_organism_count") != 96
        or value.get("registry_count") != 3
        or value.get("registry_payload_count") != 96
        or value.get("registry_scan_count") != 0
        or value.get("organism_exposure_probe_count") != 0
        or value.get("candidate_or_graph_mutation_count") != 0
        or value.get("outcome_access")
        != {"count": 0, "event_ids": []}
    ):
        raise CompatibilityClosureError("readiness gate changed")
    return value


def run_exposure() -> dict[str, Any]:
    _require_clean_worktree()
    if any((ROOT / path).exists() for path in (
        EXPOSURE_PATH, EXECUTION_MANIFEST_PATH, EXPOSURE_FAILURE_PATH
    )):
        raise FileExistsError("compatibility exposure output already exists")
    try:
        verify_package_manifests()
        readiness = load_and_verify_readiness(committed=True)
        context = stopped_adapter.build_readiness_context()
        identity = driver.verify_outer_manifest(
            "package-alias compatibility exposure"
        )
        ecology = driver._load_json(ROOT / driver.ECOLOGY_MANIFEST_PATH)
        receipt = _load_json(ROOT / stopped_adapter.PREFLIGHT_RECEIPT_PATH)
        guard = OutcomeAccessGuard()
        package_hashes = expanded_package_map()
        exposure = reconstruct_exposure_value_with_expanded_map(
            identity=identity,
            prefix=context["prefix"],
            ecology=ecology,
            manifest=context["runtime_manifest"],
            receipt=receipt,
            restored=context["restored"],
            guard=guard,
            package_hashes=package_hashes,
        )
        if exposure["outcome_access"] != {"count": 0, "event_ids": []}:
            raise CompatibilityClosureError("compatibility exposure read outcome")
        _atomic_json(ROOT / EXPOSURE_PATH, exposure)
        execution = build_execution_manifest(
            identity=identity,
            prefix=context["prefix"],
            ecology=ecology,
            manifest=context["runtime_manifest"],
            exposure=exposure,
            readiness=readiness,
            package_hashes=package_hashes,
        )
        _atomic_json(ROOT / EXECUTION_MANIFEST_PATH, execution)
        return exposure
    except Exception as exc:
        record_failure(EXPOSURE_FAILURE_PATH, "run-exposure", exc)
        raise


def reconstruct_compatibility_admission() -> dict[str, Any]:
    verify_package_manifests()
    readiness = load_and_verify_readiness(committed=True)
    require_committed_artifact(EXPOSURE_PATH)
    require_committed_artifact(EXECUTION_MANIFEST_PATH)
    exposure = _load_json(ROOT / EXPOSURE_PATH)
    execution = _load_json(ROOT / EXECUTION_MANIFEST_PATH)
    verify_self_digest(exposure, "exposure_digest", label="exposure")
    verify_self_digest(
        execution,
        "execution_manifest_digest",
        label="execution manifest",
    )
    if (
        exposure.get("admitted") is not True
        or execution.get("admitted") is not True
    ):
        raise CompatibilityClosureError("frozen exposure is not admitted")
    package_hashes = expanded_package_map()
    if (
        exposure.get("registry_package_hash") != digest(package_hashes)
        or execution.get("experiment_package_identity", {}).get(
            "expanded_laboratory_package_digest"
        )
        != digest(package_hashes)
    ):
        raise CompatibilityClosureError(
            "admission used a different expanded package map"
        )
    context = stopped_adapter.build_readiness_context()
    identity = driver.verify_outer_manifest(
        "package-alias compatibility immediate pre-outcome"
    )
    ecology = driver._load_json(ROOT / driver.ECOLOGY_MANIFEST_PATH)
    receipt = _load_json(ROOT / stopped_adapter.PREFLIGHT_RECEIPT_PATH)
    guard = OutcomeAccessGuard()
    reconstructed = reconstruct_exposure_value_with_expanded_map(
        identity=identity,
        prefix=context["prefix"],
        ecology=ecology,
        manifest=context["runtime_manifest"],
        receipt=receipt,
        restored=context["restored"],
        guard=guard,
        package_hashes=package_hashes,
    )
    if canonical_bytes(reconstructed) != canonical_bytes(exposure):
        raise CompatibilityClosureError(
            "current cohort differs from frozen compatibility exposure"
        )
    rebuilt = build_execution_manifest(
        identity=identity,
        prefix=context["prefix"],
        ecology=ecology,
        manifest=context["runtime_manifest"],
        exposure=exposure,
        readiness=readiness,
        package_hashes=package_hashes,
    )
    if canonical_bytes(rebuilt) != canonical_bytes(execution):
        raise CompatibilityClosureError(
            "current cohort differs from compatibility execution manifest"
        )
    if reconstructed["outcome_access"] != {"count": 0, "event_ids": []}:
        raise CompatibilityClosureError(
            "immediate reconstruction read an outcome"
        )
    return {
        "readiness": readiness,
        "identity": identity,
        "ecology": ecology,
        "receipt": receipt,
        "authorization": reconstructed["preflight_authorization"],
        "exposure": reconstructed,
        "execution_manifest": execution,
        "package_hashes": package_hashes,
        **context,
    }


def _science_worktree_is_clean_enough() -> None:
    rows = _git("status", "--porcelain=v1").splitlines()
    allowed = (
        SCIENCE_JOURNAL_DIR.as_posix(),
        SCIENCE_CARRIER_DIR.as_posix(),
    )
    unexpected = [
        row
        for row in rows
        if not any(row[3:].strip().startswith(prefix) for prefix in allowed)
    ]
    if unexpected:
        raise CompatibilityClosureError(
            f"unexpected worktree changes before science:{unexpected}"
        )


def run_science() -> dict[str, Any]:
    _science_worktree_is_clean_enough()
    if (ROOT / RESULT_PATH).exists():
        raise FileExistsError("compatibility canonical result already exists")
    try:
        context = reconstruct_compatibility_admission()
        prefix = context["prefix"]
        runtime_manifest = context["runtime_manifest"]
        restored = context["restored"]
        ecology = context["ecology"]
        environment_value = driver._load_json(
            ROOT / driver.ENVIRONMENT_MANIFEST_PATH
        )
        environment = driver.FrozenTruthfulEnvironment(environment_value)
        rows = driver._suffix_outcome_blind_rows(ecology)
        seed_metadata = {
            int(item["ordinal"]): {
                "genome_seed": int(item["genome_seed"]),
                "targets": copy.deepcopy(item["targets"]),
            }
            for item in prefix["results"]
        }
        journal = driver.DurableHashJournal(ROOT / SCIENCE_JOURNAL_DIR)
        entry_plan = stopped_adapter.restart_plan(
            journal, tuple(range(SEED_COUNT))
        )
        completed = driver.committed_seed_results(
            journal,
            expected_ordinals=tuple(entry_plan["completed_ordinals"]),
            expected_rows=rows,
            baseline_wrappers=restored,
            expected_seed_metadata=seed_metadata,
            environment_manifest=environment_value,
        )
        if len(completed) != len(entry_plan["completed_ordinals"]):
            raise CompatibilityClosureError(
                "completed seed verification mismatch"
            )
        for ordinal in entry_plan["remaining_ordinals"]:
            live: MutableMapping[str, Any] = {
                arm: restored[(ordinal, arm)] for arm in ARMS
            }
            adapter = driver.FreshScienceAdapter(
                seed_ordinal=ordinal,
                genome_seed=seed_metadata[ordinal]["genome_seed"],
                targets=seed_metadata[ordinal]["targets"],
                identity_contract=runtime_manifest["metadata"][
                    "per_seed_identity_contracts"
                ][str(ordinal)],
            )
            driver.execute_fresh_seed_atomically(
                seed_ordinal=ordinal,
                live_arms=live,
                rows=rows,
                adapter=adapter,
                journal_root=ROOT / SCIENCE_JOURNAL_DIR,
                carrier_root=ROOT / SCIENCE_CARRIER_DIR,
                environment=environment,
                preflight_receipt=context["receipt"],
                snapshot_manifest=runtime_manifest,
                authorization=context["authorization"],
            )
        final_journal = driver.DurableHashJournal(ROOT / SCIENCE_JOURNAL_DIR)
        final_plan = stopped_adapter.restart_plan(
            final_journal, tuple(range(SEED_COUNT))
        )
        if final_plan["next_unfinished_seed"] is not None:
            raise CompatibilityClosureError(
                "canonical science ended before seed 31"
            )
        seed_results = driver.committed_seed_results(
            final_journal,
            expected_ordinals=tuple(range(SEED_COUNT)),
            expected_rows=rows,
            baseline_wrappers=restored,
            expected_seed_metadata=seed_metadata,
            environment_manifest=environment_value,
        )
        adjudication = driver.adjudicate_committed_results(seed_results)
        value = {
            "schema_version": (
                "native_v2_package_alias_compatibility_result.v1"
            ),
            "package_id": PACKAGE_ID,
            "experiment_id": EXPERIMENT_ID,
            "expanded_package_map_digest": digest(
                context["package_hashes"]
            ),
            "exposure_digest": context["exposure"]["exposure_digest"],
            "execution_manifest_digest": context["execution_manifest"][
                "execution_manifest_digest"
            ],
            "all_32_committed": True,
            "restart_plan_at_entry": entry_plan,
            "restart_plan_at_completion": final_plan,
            "seed_result_digests": [
                item["seed_result_digest"] for item in seed_results
            ],
            "recomputed_result_digests": [
                item["recomputed_result_digest"] for item in seed_results
            ],
            "adjudication": adjudication,
            "journal_chain_digest": digest(final_journal._records()),
        }
        value["canonical_result_digest"] = digest(value)
        driver._atomic_bytes(
            ROOT / RESULT_PATH,
            driver.deterministic_gzip(canonical_bytes(value)),
        )
        return value
    except Exception as exc:
        record_failure(SCIENCE_FAILURE_PATH, "run-science", exc)
        raise


def freeze_package_manifests(source_commit: str) -> dict[str, Any]:
    _require_clean_worktree()
    if _git("rev-parse", "HEAD") != source_commit:
        raise CompatibilityClosureError("source freeze commit is not HEAD")
    if (ROOT / SOURCE_MANIFEST_PATH).exists() or (
        ROOT / ARTIFACT_BINDING_PATH
    ).exists():
        raise FileExistsError("compatibility manifests already exist")
    fixed = verify_frozen_inputs()
    source_hashes = {
        relative: sha256_file(ROOT / relative) for relative in SOURCE_FILES
    }
    source = {
        "schema_version": (
            "native_v2_package_alias_compatibility_source_manifest.v1"
        ),
        "package_id": PACKAGE_ID,
        "source_freeze_commit": source_commit,
        "source_hashes": source_hashes,
        "module_paths": {
            "compatibility": MODULE_PATH,
            "stopped_adapter": stopped_adapter.ADAPTER_MODULE,
            "driver": stopped_adapter.DRIVER_MODULE,
            "laboratory_registry": laboratory.__name__,
        },
        "public_commands": {
            command: list(build_public_command(command))
            for command in PUBLIC_COMMANDS
        },
        "deterministic_environment": copy.deepcopy(DETERMINISTIC_ENV),
        "runtime": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "working_directory": str(ROOT),
        },
        "alias_diagnosis": copy.deepcopy(fixed["alias_diagnosis"]),
        "expanded_package_map": copy.deepcopy(
            fixed["expanded_package_map"]
        ),
        "bounded_reconstruction_ast": copy.deepcopy(
            fixed["bounded_reconstruction_ast"]
        ),
        "preservation": {
            "outer_compatibility_only": True,
            "no_module_global_replacement": True,
            "stopped_adapter_byte_identical": True,
            "old_failure_preserved": True,
            "real_registry_scan_not_run": True,
            "real_exposure_not_run": True,
            "real_outcomes_not_read": True,
        },
    }
    source["source_manifest_digest"] = digest(source)
    _atomic_json(ROOT / SOURCE_MANIFEST_PATH, source)
    binding = {
        "schema_version": (
            "native_v2_package_alias_compatibility_artifact_binding.v1"
        ),
        "package_id": PACKAGE_ID,
        "source_manifest": {
            "path": SOURCE_MANIFEST_PATH.as_posix(),
            "sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
            "digest": source["source_manifest_digest"],
        },
        "frozen_inputs": fixed,
        "output_paths": {
            "readiness": READINESS_PATH.as_posix(),
            "readiness_failure": READINESS_FAILURE_PATH.as_posix(),
            "exposure": EXPOSURE_PATH.as_posix(),
            "exposure_failure": EXPOSURE_FAILURE_PATH.as_posix(),
            "execution_manifest": EXECUTION_MANIFEST_PATH.as_posix(),
            "science_journal": SCIENCE_JOURNAL_DIR.as_posix(),
            "science_carrier": SCIENCE_CARRIER_DIR.as_posix(),
            "result": RESULT_PATH.as_posix(),
            "science_failure": SCIENCE_FAILURE_PATH.as_posix(),
        },
        "scientific_constants": {
            "seed_count": SEED_COUNT,
            "arms": list(ARMS),
            "suffix_rows": 16,
            "minimum_target_opportunities": MIN_TARGET_OPPORTUNITIES,
            "minimum_qualifying_seeds": MIN_QUALIFYING_SEEDS,
            "minimum_favorable_seeds": driver.MIN_FAVORABLE_SEEDS,
            "holm_test_count": 2,
            "all_32_paired": True,
        },
        "map_law": {
            "original_map_retained": True,
            "aliases_derived_from_registry_declaration": True,
            "declared_alias_count": 13,
            "expanded_map_digest": fixed["expanded_package_map"][
                "expanded_map_digest"
            ],
            "same_map_for_registry_scan_aggregation_execution_and_rebuild": True,
        },
        "stop_boundary": {
            "readiness_only_in_this_package": True,
            "real_registries_created": True,
            "real_registry_scans_forbidden": True,
            "organism_exposure_probes_forbidden": True,
            "exposure_command_frozen_not_run": True,
            "science_command_frozen_not_run": True,
        },
    }
    binding["artifact_binding_digest"] = digest(binding)
    _atomic_json(ROOT / ARTIFACT_BINDING_PATH, binding)
    return {
        "source_manifest_path": SOURCE_MANIFEST_PATH.as_posix(),
        "source_manifest_sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
        "source_manifest_digest": source["source_manifest_digest"],
        "artifact_binding_path": ARTIFACT_BINDING_PATH.as_posix(),
        "artifact_binding_sha256": sha256_file(
            ROOT / ARTIFACT_BINDING_PATH
        ),
        "artifact_binding_digest": binding["artifact_binding_digest"],
    }


def verify_package_manifests() -> dict[str, Any]:
    source = _load_json(ROOT / SOURCE_MANIFEST_PATH)
    source_digest = verify_self_digest(
        source,
        "source_manifest_digest",
        label="compatibility source manifest",
    )
    for relative, expected in source["source_hashes"].items():
        observed = sha256_file(ROOT / relative)
        if observed != expected:
            raise CompatibilityClosureError(
                f"compatibility source changed:{relative}:{observed}"
            )
    _require_commit(str(source["source_freeze_commit"]))
    binding = _load_json(ROOT / ARTIFACT_BINDING_PATH)
    binding_digest = verify_self_digest(
        binding,
        "artifact_binding_digest",
        label="compatibility artifact binding",
    )
    if (
        binding["source_manifest"]["sha256"]
        != sha256_file(ROOT / SOURCE_MANIFEST_PATH)
        or binding["source_manifest"]["digest"] != source_digest
    ):
        raise CompatibilityClosureError(
            "compatibility source/artifact binding mismatch"
        )
    fixed = verify_frozen_inputs()
    if canonical_bytes(fixed) != canonical_bytes(binding["frozen_inputs"]):
        raise CompatibilityClosureError(
            "compatibility frozen-input binding mismatch"
        )
    return {
        "source_manifest_sha256": sha256_file(
            ROOT / SOURCE_MANIFEST_PATH
        ),
        "source_manifest_digest": source_digest,
        "artifact_binding_sha256": sha256_file(
            ROOT / ARTIFACT_BINDING_PATH
        ),
        "artifact_binding_digest": binding_digest,
    }


def record_failure(path: Path, command: str, exc: Exception) -> None:
    if (ROOT / path).exists():
        return
    value = {
        "schema_version": (
            "native_v2_package_alias_compatibility_failure.v1"
        ),
        "package_id": PACKAGE_ID,
        "command": command,
        "exception_type": type(exc).__name__,
        "detail": str(exc),
        "parent_argv": list(getattr(sys, "orig_argv", sys.argv)),
        "process_id": os.getpid(),
        "registry_scan_count": 0 if command == "verify-readiness" else None,
        "organism_exposure_probe_count": (
            0 if command == "verify-readiness" else None
        ),
        "outcome_access": {"count": 0, "event_ids": []},
    }
    value["failure_digest"] = digest(value)
    _atomic_json(ROOT / path, value)


def readiness_value(
    *,
    context: Mapping[str, Any],
    registries: Mapping[str, Any],
    package: Mapping[str, Any],
    started: float,
) -> dict[str, Any]:
    summary = context["summary"]
    value = {
        "schema_version": (
            "native_v2_package_alias_compatibility_readiness.v1"
        ),
        "package_id": PACKAGE_ID,
        "source_manifest": {
            "sha256": package["source_manifest_sha256"],
            "digest": package["source_manifest_digest"],
        },
        "artifact_binding": {
            "sha256": package["artifact_binding_sha256"],
            "digest": package["artifact_binding_digest"],
        },
        "public_command": list(build_public_command("verify-readiness")),
        "actual_parent_argv": list(getattr(sys, "orig_argv", sys.argv)),
        "process_id": os.getpid(),
        "python_executable": sys.executable,
        "working_directory": str(ROOT),
        "deterministic_environment": copy.deepcopy(DETERMINISTIC_ENV),
        "verified_seed_count": summary["verified_seed_count"],
        "verified_organism_count": summary["verified_organism_count"],
        "cohort_digest": summary["cohort_digest"],
        "candidate_contract_rows": copy.deepcopy(
            summary["runtime_view_proof"]["contract_rows"]
        ),
        "candidate_contract_row_set_digest": summary[
            "runtime_view_proof"
        ]["contract_row_set_digest"],
        "runtime_view_identity": {
            "source_before": copy.deepcopy(
                summary["runtime_view_proof"]["source_before"]
            ),
            "runtime_view": copy.deepcopy(
                summary["runtime_view_proof"]["runtime_view"]
            ),
            "source_after": copy.deepcopy(
                summary["runtime_view_proof"]["source_after"]
            ),
        },
        "base_semantic_state_before_digest": summary[
            "semantic_state_before_digest"
        ],
        "base_semantic_state_after_digest": summary[
            "semantic_state_after_digest"
        ],
        "registry_count": registries["registry_count"],
        "registry_payload_count": registries["payload_count"],
        "registered_row_definition_count": registries[
            "registered_row_count"
        ],
        "registry_row_order": copy.deepcopy(registries["row_order"]),
        "registry_row_order_digest": registries["row_order_digest"],
        "expanded_package_map": expanded_package_map_manifest(
            expanded_package_map()
        ),
        "real_registry_closure": copy.deepcopy(registries),
        "registry_scan_count": 0,
        "cohort_aggregation_count": 0,
        "organism_exposure_probe_count": 0,
        "candidate_or_graph_mutation_count": 0,
        "module_global_replacement_count": 0,
        "outcome_access": {"count": 0, "event_ids": []},
        "stopped_before_first_organism_exposure_probe": True,
        "evaluation_suffix_unopened": True,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }
    value["readiness_digest"] = digest(value)
    return value


def run_readiness() -> dict[str, Any]:
    _require_clean_worktree()
    if (ROOT / READINESS_PATH).exists() or (
        ROOT / READINESS_FAILURE_PATH
    ).exists():
        raise FileExistsError("compatibility readiness output already exists")
    require_committed_artifact(SOURCE_MANIFEST_PATH)
    require_committed_artifact(ARTIFACT_BINDING_PATH)
    started = time.perf_counter()
    try:
        package = verify_package_manifests()
        context = stopped_adapter.build_readiness_context()
        summary = context["summary"]
        if (
            summary["cohort_digest"] != ACCEPTED_COHORT_DIGEST
            or summary["verified_seed_count"] != 32
            or summary["verified_organism_count"] != 96
            or summary["candidate_or_graph_mutation_count"] != 0
            or summary["outcome_access"]
            != {"count": 0, "event_ids": []}
        ):
            raise CompatibilityClosureError(
                "retained cohort readiness gate changed"
            )
        identity = driver.verify_outer_manifest(
            "package-alias compatibility readiness"
        )
        ecology = driver._load_json(ROOT / driver.ECOLOGY_MANIFEST_PATH)
        registries = construct_registry_manifests_without_scanning(
            restored=context["restored"],
            ecology=ecology,
            identity=identity,
            package_hashes=expanded_package_map(),
        )
        value = readiness_value(
            context=context,
            registries=registries,
            package=package,
            started=started,
        )
        _atomic_json(ROOT / READINESS_PATH, value)
        return value
    except Exception as exc:
        record_failure(READINESS_FAILURE_PATH, "verify-readiness", exc)
        raise


def _print(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    freeze = commands.add_parser("freeze-manifests")
    freeze.add_argument("--source-commit", required=True)
    commands.add_parser("verify-readiness")
    commands.add_parser("run-exposure")
    commands.add_parser("run-science")
    args = parser.parse_args(argv)
    if args.command == "freeze-manifests":
        value = freeze_package_manifests(args.source_commit)
    elif args.command == "verify-readiness":
        value = run_readiness()
    elif args.command == "run-exposure":
        value = run_exposure()
    elif args.command == "run-science":
        value = run_science()
    else:  # pragma: no cover
        raise AssertionError(args.command)
    _print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
