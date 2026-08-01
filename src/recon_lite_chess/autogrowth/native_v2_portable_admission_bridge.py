"""Outcome-free portable admission for the frozen native V2 cohort.

This module is deliberately an outer verification bridge.  It leaves the
historically bound process-readiness package byte-identical, validates its
existing journal with its original validator, and then proves that a fresh
restore has the same complete semantic and outcome-blind behavior.  Historical
pickle hashes are reintroduced only after all 96 fresh comparisons pass, and
only to reconstruct the already committed registry and artifacts.

There is no exposure or outcome command in this package.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import traceback
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, MutableMapping, Sequence

from . import native_prospective_evidence_authority_v2_lab as laboratory
from . import native_v2_fresh_discriminator_review_repair_v2 as driver
from . import native_v2_process_readiness_repair as historical
from . import native_v2_process_resilient_execution_reclosure as execution


ROOT = historical.ROOT
PACKAGE_ID = "native_v2_portable_admission_bridge.v1"
MODULE_PATH = (
    "recon_lite_chess.autogrowth.native_v2_portable_admission_bridge"
)
STARTING_HEAD = "e7dfd710b9753b218cc8811f3ad59c85de350a34"
RESTORATION_COMMIT = "891748a"

PACKAGE_DIR = Path(
    "reports/autogrowth/native_authority/v2_portable_admission_bridge"
)
ATTEMPT_ROOT = PACKAGE_DIR / "attempts"
SOURCE_MANIFEST_PATH = PACKAGE_DIR / "source_manifest.json"
CLASSIFICATION_MANIFEST_PATH = PACKAGE_DIR / "field_classification.json"
DEPENDENCY_MANIFEST_PATH = PACKAGE_DIR / "artifact_dependency_manifest.json"

PREREGISTRATION_PATH = Path(
    "docs/autogrowth/"
    "NATIVE_V2_PORTABLE_ADMISSION_BRIDGE_PREREGISTRATION_20260801.md"
)
TEST_PATH = Path(
    "tests/autogrowth/test_native_v2_portable_admission_bridge.py"
)
SELF_PATH = Path(
    "src/recon_lite_chess/autogrowth/"
    "native_v2_portable_admission_bridge.py"
)

HISTORICAL_PROCESS_PATH = Path(
    "src/recon_lite_chess/autogrowth/"
    "native_v2_process_readiness_repair.py"
)
HISTORICAL_TEST_PATH = Path(
    "tests/autogrowth/test_native_v2_process_readiness_repair.py"
)
HISTORICAL_PROCESS_SHA256 = (
    "ae663e67ffad3dbdf8a7e988b5638181fa7a2c4398d3d46b7668cb80ee3d76a6"
)
HISTORICAL_TEST_SHA256 = (
    "fc3ea605cb8e49c0b3f20b359e3e181b2736d236b2f22f4b6c49946a9d4d2004"
)
PROTECTED_FILE_COUNT = 195
PROTECTED_FILE_SET_DIGEST = (
    "9082cf52f505d924590458c4dd2a7f365bbdec3494cdbbc3d974726e97cb4239"
)

STOP_REPORT_PATH = Path(
    "docs/autogrowth/"
    "NATIVE_V2_UNIT_BINDING_ADMISSION_RECLOSURE_STOP_20260801.md"
)
DIAGNOSTIC_PATH = historical.PACKAGE_DIR / (
    "unit_binding_admission_diagnostic.json"
)
PRESERVED_ATTEMPT_PATH = historical.PACKAGE_DIR / (
    "unit_binding_admission_attempts/20260731T202101435174689Z"
)

ATTEMPT_IDS = (
    "portable-admission-01-e7dfd710b975",
    "portable-admission-02-e7dfd710b975",
    "portable-admission-03-e7dfd710b975",
)
ZERO_OUTCOME = {"count": 0, "event_ids": []}

SEMANTIC_EXACT = "SEMANTIC_EXACT"
HISTORICAL_TRANSPORT = "HISTORICAL_TRANSPORT"
DERIVED_FROM_HISTORICAL_TRANSPORT = "DERIVED_FROM_HISTORICAL_TRANSPORT"
STATIC_FROZEN = "STATIC_FROZEN"
CLASSIFICATIONS = frozenset({
    SEMANTIC_EXACT,
    HISTORICAL_TRANSPORT,
    DERIVED_FROM_HISTORICAL_TRANSPORT,
    STATIC_FROZEN,
})

BINDING_TRANSPORT_PATHS = (
    "/payload_sha256",
    "/registry_identity",
    "/unit_binding_digest",
)
RESULT_TRANSPORT_PATHS = (
    "/unit_binding_digest",
    "/scan_wrapper/registry_id",
    "/scan_wrapper/payload_sha256",
    "/unit_result_digest",
)


class PortableAdmissionError(RuntimeError):
    """Fail-closed admission error."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def pretty_json_bytes(value: Mapping[str, Any]) -> bytes:
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


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PortableAdmissionError(f"expected JSON object:{path}")
    return value


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    """Write only bridge-owned output with an unambiguous atomic target."""

    resolved = path.resolve()
    package = (ROOT / PACKAGE_DIR).resolve()
    if package not in resolved.parents:
        raise PortableAdmissionError(f"bridge write escaped package:{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.portable-admission.tmp")
    if temporary.exists() or path.exists():
        raise PortableAdmissionError(f"bridge output already exists:{path}")
    payload = pretty_json_bytes(value)
    with temporary.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    _fsync_directory(path.parent)


def replace_progress(path: Path, value: Mapping[str, Any]) -> None:
    """Durably replace the one explicitly mutable progress record."""

    resolved = path.resolve()
    package = (ROOT / ATTEMPT_ROOT).resolve()
    if package not in resolved.parents:
        raise PortableAdmissionError("progress write escaped attempt root")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.portable-admission.tmp")
    if temporary.exists():
        raise PortableAdmissionError(f"ambiguous progress temporary:{temporary}")
    payload = pretty_json_bytes(value)
    with temporary.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    _fsync_directory(path.parent)


def _git(*args: str) -> str:
    return subprocess.check_output(
        ("git", *args), cwd=ROOT, text=True, stderr=subprocess.STDOUT
    ).strip()


def protected_paths() -> tuple[Path, ...]:
    journal = sorted((ROOT / historical.EXPOSURE_JOURNAL_DIR).glob("*.json"))
    relative_journal = tuple(path.relative_to(ROOT) for path in journal)
    return (
        historical.EXPOSURE_PATH,
        historical.EXECUTION_MANIFEST_PATH,
        historical.EXPOSURE_COMPLETION_PATH,
        *relative_journal,
    )


def current_protected_hashes() -> dict[str, str]:
    return {
        path.as_posix(): sha256_file(ROOT / path)
        for path in protected_paths()
    }


def verify_protected_files(
    expected: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    observed = current_protected_hashes()
    observed_digest = digest(observed)
    if (
        len(observed) != PROTECTED_FILE_COUNT
        or observed_digest != PROTECTED_FILE_SET_DIGEST
    ):
        raise PortableAdmissionError(
            "historical protected exposure set changed"
        )
    if expected is not None and dict(expected) != observed:
        raise PortableAdmissionError("frozen protected-file map changed")
    return {
        "file_count": len(observed),
        "file_set_digest": observed_digest,
        "file_hashes": observed,
    }


def _science_paths() -> tuple[Path, ...]:
    return (
        historical.SCIENCE_STARTED_PATH,
        historical.SCIENCE_JOURNAL_DIR,
        historical.SCIENCE_CARRIER_DIR,
        historical.RESULT_PATH,
        historical.SCIENCE_FAILURE_PATH,
    )


def verify_zero_outcome_access() -> dict[str, Any]:
    present = [path.as_posix() for path in _science_paths() if (ROOT / path).exists()]
    if present:
        raise PortableAdmissionError(f"outcome-stage path exists:{present}")
    exposure = load_json(ROOT / historical.EXPOSURE_PATH)
    completion = load_json(ROOT / historical.EXPOSURE_COMPLETION_PATH)
    if (
        exposure.get("outcome_access") != ZERO_OUTCOME
        or completion.get("outcome_access") != ZERO_OUTCOME
    ):
        raise PortableAdmissionError("historical exposure reports outcome access")
    return {
        "count": 0,
        "event_ids": [],
        "science_paths_absent": True,
    }


def verify_historical_inner_hashes() -> dict[str, str]:
    observed = {
        HISTORICAL_PROCESS_PATH.as_posix(): sha256_file(
            ROOT / HISTORICAL_PROCESS_PATH
        ),
        HISTORICAL_TEST_PATH.as_posix(): sha256_file(ROOT / HISTORICAL_TEST_PATH),
    }
    expected = {
        HISTORICAL_PROCESS_PATH.as_posix(): HISTORICAL_PROCESS_SHA256,
        HISTORICAL_TEST_PATH.as_posix(): HISTORICAL_TEST_SHA256,
    }
    if observed != expected:
        raise PortableAdmissionError("historically bound inner package changed")
    return observed


def _pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _pointer_unescape(value: str) -> str:
    return value.replace("~1", "/").replace("~0", "~")


def pointer_parts(pointer: str) -> tuple[str, ...]:
    if pointer == "":
        return ()
    if not pointer.startswith("/"):
        raise PortableAdmissionError(f"invalid JSON pointer:{pointer}")
    return tuple(_pointer_unescape(item) for item in pointer[1:].split("/"))


def pointer_from_parts(parts: Sequence[str]) -> str:
    return "" if not parts else "/" + "/".join(_pointer_escape(item) for item in parts)


def leaf_pointers(value: Any, prefix: tuple[str, ...] = ()) -> Iterator[str]:
    if isinstance(value, Mapping):
        if not value:
            yield pointer_from_parts(prefix)
            return
        for key in sorted(value, key=str):
            yield from leaf_pointers(value[key], prefix + (str(key),))
        return
    if isinstance(value, (list, tuple)):
        if not value:
            yield pointer_from_parts(prefix)
            return
        for index, item in enumerate(value):
            yield from leaf_pointers(item, prefix + (str(index),))
        return
    yield pointer_from_parts(prefix)


_DYNAMIC_KEY_PREFIXES = (
    "seed-", "cell-", "node-", "edge-", "stem-", "option-",
    "candidate-", "opaque_", "opaque-", "request:", "terminal:",
    "script:", "leg:", "authority:", "evidence:", "event:",
)


def normalized_pointer(pointer: str) -> str:
    normalized = []
    for item in pointer_parts(pointer):
        if item.isdigit():
            normalized.append("*")
        elif (
            len(item) >= 32
            or ":" in item
            or item.startswith(_DYNAMIC_KEY_PREFIXES)
            or re.fullmatch(r"[0-9a-f]{16,}", item)
        ):
            normalized.append("{key}")
        else:
            normalized.append(item)
    return pointer_from_parts(normalized)


def _roots(**items: str) -> dict[str, str]:
    if set(items.values()) - CLASSIFICATIONS:
        raise AssertionError("invalid field classification")
    return dict(items)


ROOT_CLASSIFICATIONS: dict[str, dict[str, str]] = {
    "unit_binding": _roots(
        schema_version=STATIC_FROZEN,
        unit_index=SEMANTIC_EXACT,
        unit_id=SEMANTIC_EXACT,
        arm=SEMANTIC_EXACT,
        seed_ordinal=SEMANTIC_EXACT,
        organism_id=SEMANTIC_EXACT,
        source_snapshot_identity=SEMANTIC_EXACT,
        candidate_graph_continuation_digest=SEMANTIC_EXACT,
        payload_sha256=HISTORICAL_TRANSPORT,
        registry_identity=DERIVED_FROM_HISTORICAL_TRANSPORT,
        registry_tape_identity=SEMANTIC_EXACT,
        registry_run_identity=STATIC_FROZEN,
        expanded_package_map_digest=STATIC_FROZEN,
        row_order=STATIC_FROZEN,
        row_order_digest=STATIC_FROZEN,
        row_definitions=STATIC_FROZEN,
        row_definition_digest=STATIC_FROZEN,
        outcome_access=SEMANTIC_EXACT,
        unit_binding_digest=DERIVED_FROM_HISTORICAL_TRANSPORT,
    ),
    "unit_result": _roots(
        schema_version=STATIC_FROZEN,
        unit_index=SEMANTIC_EXACT,
        unit_id=SEMANTIC_EXACT,
        arm=SEMANTIC_EXACT,
        seed_ordinal=SEMANTIC_EXACT,
        organism_id=SEMANTIC_EXACT,
        unit_binding_digest=DERIVED_FROM_HISTORICAL_TRANSPORT,
        commitments=SEMANTIC_EXACT,
        classifier_visible_projections=SEMANTIC_EXACT,
        scan_wrapper=SEMANTIC_EXACT,
        target_counts=SEMANTIC_EXACT,
        continuation_digest_before=SEMANTIC_EXACT,
        continuation_digest_after=SEMANTIC_EXACT,
        candidate_graph_state_unchanged=SEMANTIC_EXACT,
        outcome_access=SEMANTIC_EXACT,
        unit_result_digest=DERIVED_FROM_HISTORICAL_TRANSPORT,
    ),
    "scan_wrapper": _roots(
        schema_version=STATIC_FROZEN,
        registry_id=DERIVED_FROM_HISTORICAL_TRANSPORT,
        organism_id=SEMANTIC_EXACT,
        tape_identity=SEMANTIC_EXACT,
        row_order=STATIC_FROZEN,
        run_identity=STATIC_FROZEN,
        package_hashes=STATIC_FROZEN,
        payload_sha256=HISTORICAL_TRANSPORT,
        continuation_digest=SEMANTIC_EXACT,
        experimental_identity_digest=SEMANTIC_EXACT,
        candidate_population_identity=SEMANTIC_EXACT,
        source_binding_identity=SEMANTIC_EXACT,
        scan_digest=SEMANTIC_EXACT,
        scan=SEMANTIC_EXACT,
    ),
    "registry_entry": _roots(
        organism_id=SEMANTIC_EXACT,
        payload_sha256=HISTORICAL_TRANSPORT,
        continuation_digest=SEMANTIC_EXACT,
        experimental_identity_digest=SEMANTIC_EXACT,
        candidate_population_identity=SEMANTIC_EXACT,
        source_binding_identity=SEMANTIC_EXACT,
    ),
    "registry_manifest": _roots(
        schema_version=STATIC_FROZEN,
        registry_id=DERIVED_FROM_HISTORICAL_TRANSPORT,
        tape_identity=SEMANTIC_EXACT,
        row_order=STATIC_FROZEN,
        run_identity=STATIC_FROZEN,
        package_hashes=STATIC_FROZEN,
        organisms=SEMANTIC_EXACT,
        exposure_rows=STATIC_FROZEN,
    ),
    "per_seed_summary": _roots(
        ordinal=SEMANTIC_EXACT,
        organism_id=SEMANTIC_EXACT,
        continuation_digest=SEMANTIC_EXACT,
        target_counts=SEMANTIC_EXACT,
        scan_wrapper_digest=DERIVED_FROM_HISTORICAL_TRANSPORT,
        projection_digests=SEMANTIC_EXACT,
    ),
    "per_arm_summary": _roots(
        registry=SEMANTIC_EXACT,
        registry_adjudication=SEMANTIC_EXACT,
        per_seed=SEMANTIC_EXACT,
        scan_wrapper_set_digest=DERIVED_FROM_HISTORICAL_TRANSPORT,
    ),
    "exposure_artifact": _roots(
        schema_version=STATIC_FROZEN,
        experiment_id=STATIC_FROZEN,
        outer_manifest_sha256=STATIC_FROZEN,
        snapshot_manifest_digest=STATIC_FROZEN,
        complete_snapshot_identity=STATIC_FROZEN,
        prefix_candidate_verification=SEMANTIC_EXACT,
        global_preflight_receipt=STATIC_FROZEN,
        preflight_authorization=STATIC_FROZEN,
        registry_package_hash=STATIC_FROZEN,
        arms=SEMANTIC_EXACT,
        parity_rows=SEMANTIC_EXACT,
        parity_row_count=SEMANTIC_EXACT,
        parity_digest=SEMANTIC_EXACT,
        per_seed_qualification=SEMANTIC_EXACT,
        qualification_digest=SEMANTIC_EXACT,
        qualifying_seed_count=SEMANTIC_EXACT,
        required_qualifying_seed_count=STATIC_FROZEN,
        admitted=SEMANTIC_EXACT,
        stop_reason=SEMANTIC_EXACT,
        outcome_access=SEMANTIC_EXACT,
        exposure_digest=DERIVED_FROM_HISTORICAL_TRANSPORT,
    ),
    "execution_manifest": _roots(
        schema_version=STATIC_FROZEN,
        package_id=STATIC_FROZEN,
        experiment_id=STATIC_FROZEN,
        source_tree_identity=STATIC_FROZEN,
        experiment_package_identity=STATIC_FROZEN,
        repair_package=STATIC_FROZEN,
        previous_process_readiness=STATIC_FROZEN,
        exposure_artifact=DERIVED_FROM_HISTORICAL_TRANSPORT,
        parity_digest=SEMANTIC_EXACT,
        qualification_digest=SEMANTIC_EXACT,
        qualifying_seed_count=SEMANTIC_EXACT,
        required_qualifying_seed_count=STATIC_FROZEN,
        admitted=SEMANTIC_EXACT,
        zero_outcome_read_result=SEMANTIC_EXACT,
        complete_snapshot_identity=STATIC_FROZEN,
        global_preflight_receipt_digest=STATIC_FROZEN,
        execution_manifest_digest=DERIVED_FROM_HISTORICAL_TRANSPORT,
    ),
    "completion_marker": _roots(
        schema_version=STATIC_FROZEN,
        package_id=STATIC_FROZEN,
        experiment_id=STATIC_FROZEN,
        unit_count=STATIC_FROZEN,
        exposure_journal_chain_digest=DERIVED_FROM_HISTORICAL_TRANSPORT,
        exposure_recomputation_count=DERIVED_FROM_HISTORICAL_TRANSPORT,
        exposure=DERIVED_FROM_HISTORICAL_TRANSPORT,
        execution_manifest=DERIVED_FROM_HISTORICAL_TRANSPORT,
        outcome_access=SEMANTIC_EXACT,
        completion_digest=DERIVED_FROM_HISTORICAL_TRANSPORT,
    ),
    "journal_prepared": _roots(
        schema_version=STATIC_FROZEN,
        record_index=DERIVED_FROM_HISTORICAL_TRANSPORT,
        previous_record_digest=DERIVED_FROM_HISTORICAL_TRANSPORT,
        kind=STATIC_FROZEN,
        unit_index=SEMANTIC_EXACT,
        unit_id=SEMANTIC_EXACT,
        payload=SEMANTIC_EXACT,
        record_digest=DERIVED_FROM_HISTORICAL_TRANSPORT,
    ),
    "journal_committed": _roots(
        schema_version=STATIC_FROZEN,
        record_index=DERIVED_FROM_HISTORICAL_TRANSPORT,
        previous_record_digest=DERIVED_FROM_HISTORICAL_TRANSPORT,
        kind=STATIC_FROZEN,
        unit_index=SEMANTIC_EXACT,
        unit_id=SEMANTIC_EXACT,
        payload=SEMANTIC_EXACT,
        record_digest=DERIVED_FROM_HISTORICAL_TRANSPORT,
    ),
}


_SOURCE_SNAPSHOT_STATIC_FIELDS = frozenset({
    "path", "raw_sha256", "raw_size", "compressed_sha256",
    "compressed_size", "semantic_identity_digest",
})


def classify_pointer(kind: str, pointer: str) -> str:
    parts = pointer_parts(pointer)
    if not parts:
        raise PortableAdmissionError(f"empty field pointer:{kind}")
    roots = ROOT_CLASSIFICATIONS.get(kind)
    if roots is None or parts[0] not in roots:
        raise PortableAdmissionError(f"unclassified field:{kind}:{pointer}")

    if kind == "unit_binding" and parts[:2] == ("source_snapshot_identity", "entry_digest"):
        return STATIC_FROZEN
    if (
        kind == "unit_binding"
        and len(parts) >= 3
        and parts[:2] == ("source_snapshot_identity", "entry")
        and parts[2] in _SOURCE_SNAPSHOT_STATIC_FIELDS
    ):
        return STATIC_FROZEN
    if kind == "unit_result" and parts[0] == "scan_wrapper" and len(parts) > 1:
        return classify_pointer("scan_wrapper", pointer_from_parts(parts[1:]))
    if kind == "registry_manifest" and parts[0] == "organisms" and len(parts) > 2:
        return classify_pointer("registry_entry", pointer_from_parts(parts[2:]))
    if kind == "per_arm_summary" and parts[0] == "registry" and len(parts) > 1:
        return classify_pointer("registry_manifest", pointer_from_parts(parts[1:]))
    if kind == "per_arm_summary" and parts[0] == "per_seed" and len(parts) > 2:
        return classify_pointer("per_seed_summary", pointer_from_parts(parts[2:]))
    if kind == "exposure_artifact" and parts[0] == "arms" and len(parts) > 2:
        return classify_pointer("per_arm_summary", pointer_from_parts(parts[2:]))
    if kind == "journal_prepared" and parts[:2] == ("payload", "unit_binding") and len(parts) > 2:
        return classify_pointer("unit_binding", pointer_from_parts(parts[2:]))
    if kind == "journal_prepared" and parts[:2] == ("payload", "recomputes_prepared_record_digest"):
        return DERIVED_FROM_HISTORICAL_TRANSPORT
    if kind == "journal_committed" and parts[:2] == ("payload", "unit_result") and len(parts) > 2:
        return classify_pointer("unit_result", pointer_from_parts(parts[2:]))
    if kind == "journal_committed" and len(parts) == 2 and parts[0] == "payload" and parts[1] in {
        "prepared_record_digest", "unit_binding_digest", "unit_result_digest"
    }:
        return DERIVED_FROM_HISTORICAL_TRANSPORT
    return roots[parts[0]]


def classified_shape(kind: str, value: Mapping[str, Any]) -> dict[str, Any]:
    expected_roots = set(ROOT_CLASSIFICATIONS[kind])
    if set(value) != expected_roots:
        raise PortableAdmissionError(
            f"closed field roots changed:{kind}:"
            f"missing={sorted(expected_roots - set(value))}:"
            f"extra={sorted(set(value) - expected_roots)}"
        )
    rows = []
    templates: dict[str, str] = {}
    for pointer in leaf_pointers(value):
        classification = classify_pointer(kind, pointer)
        rows.append((pointer, classification))
        template = normalized_pointer(pointer)
        previous_class = templates.get(template)
        if previous_class is not None and previous_class != classification:
            raise PortableAdmissionError(
                f"normalized pointer has conflicting classes:"
                f"{kind}:{template}"
            )
        templates[template] = classification
    counts = Counter(classification for _, classification in rows)
    return {
        "leaf_count": len(rows),
        "class_counts": dict(sorted(counts.items())),
        "concrete_pointer_classification_digest": digest(rows),
        "templates": templates,
    }


def _classification_objects() -> Iterator[tuple[str, str, Mapping[str, Any]]]:
    journal = historical.RepairExposureUnitJournal(
        ROOT / historical.EXPOSURE_JOURNAL_DIR
    )
    for row in journal.records():
        index = int(row["unit_index"])
        if row["kind"] == "PREPARED":
            binding = row["payload"]["unit_binding"]
            yield f"journal-prepared:{row['record_index']}", "journal_prepared", row
            yield f"unit-binding:{index}", "unit_binding", binding
        elif row["kind"] == "COMMITTED":
            result = row["payload"]["unit_result"]
            yield f"journal-committed:{row['record_index']}", "journal_committed", row
            yield f"unit-result:{index}", "unit_result", result
            yield f"scan-wrapper:{index}", "scan_wrapper", result["scan_wrapper"]
        else:
            raise PortableAdmissionError("foreign historical journal kind")
    exposure = load_json(ROOT / historical.EXPOSURE_PATH)
    for arm in execution.ARMS:
        summary = exposure["arms"][arm]
        yield f"registry:{arm}", "registry_manifest", summary["registry"]
        for index, entry in enumerate(summary["registry"]["organisms"]):
            yield f"registry-entry:{arm}:{index}", "registry_entry", entry
        for index, item in enumerate(summary["per_seed"]):
            yield f"per-seed:{arm}:{index}", "per_seed_summary", item
        yield f"per-arm:{arm}", "per_arm_summary", summary
    yield "exposure", "exposure_artifact", exposure
    yield "execution", "execution_manifest", load_json(
        ROOT / historical.EXECUTION_MANIFEST_PATH
    )
    yield "completion", "completion_marker", load_json(
        ROOT / historical.EXPOSURE_COMPLETION_PATH
    )


def build_classification_manifest() -> dict[str, Any]:
    instances: dict[str, Any] = {}
    templates: dict[str, dict[str, str]] = defaultdict(dict)
    for object_id, kind, value in _classification_objects():
        if object_id in instances:
            raise PortableAdmissionError(f"duplicate classification object:{object_id}")
        shape = classified_shape(kind, value)
        for pointer, classification in shape.pop("templates").items():
            previous_class = templates[kind].get(pointer)
            if previous_class is not None and previous_class != classification:
                raise PortableAdmissionError(
                    f"multiply classified pointer:{kind}:{pointer}"
                )
            templates[kind][pointer] = classification
        instances[object_id] = {"kind": kind, **shape}
    schemas = {}
    for kind in sorted(ROOT_CLASSIFICATIONS):
        rows = [
            {"pointer": pointer, "classification": classification}
            for pointer, classification in sorted(templates[kind].items())
        ]
        if not rows:
            raise PortableAdmissionError(f"classification schema unused:{kind}")
        schemas[kind] = {
            "top_level_fields": copy.deepcopy(ROOT_CLASSIFICATIONS[kind]),
            "expanded_pointer_templates": rows,
            "template_count": len(rows),
            "template_digest": digest(rows),
        }
    value = {
        "schema_version": "native_v2_portable_field_classification.v1",
        "package_id": PACKAGE_ID,
        "classifications": sorted(CLASSIFICATIONS),
        "no_catch_all": True,
        "fresh_schema_aliases": {
            "fresh_unit_binding": "unit_binding",
            "fresh_unit_result": "unit_result",
            "fresh_registry_entry": "registry_entry",
            "fresh_registry_manifest": "registry_manifest",
            "fresh_scan_wrapper": "scan_wrapper",
            "fresh_per_seed_summary": "per_seed_summary",
            "fresh_per_arm_summary": "per_arm_summary",
            "fresh_exposure_artifact": "exposure_artifact",
            "fresh_execution_manifest": "execution_manifest",
            "fresh_completion_marker": "completion_marker",
        },
        "portable_unit_result_exclusions": list(RESULT_TRANSPORT_PATHS),
        "portable_unit_binding_exclusions": list(BINDING_TRANSPORT_PATHS),
        "schemas": schemas,
        "instances": instances,
        "instance_count": len(instances),
        "known_raw_derived_closure": {
            "unit_binding": list(BINDING_TRANSPORT_PATHS),
            "registry_entry": ["/payload_sha256"],
            "registry": ["/registry_id"],
            "scan_wrapper": ["/registry_id", "/payload_sha256"],
            "unit_result": list(RESULT_TRANSPORT_PATHS),
            "journal_and_summaries": [
                "record_digest", "previous_record_digest",
                "prepared_record_digest", "unit_binding_digest",
                "unit_result_digest", "scan_wrapper_digest",
                "scan_wrapper_set_digest",
            ],
            "artifacts": [
                "emitted registry raw fields", "exposure bytes/digest",
                "execution exposure binding/digest",
                "completion bindings/digest",
            ],
        },
    }
    value["classification_manifest_digest"] = digest(value)
    return value


def verify_self_digest(value: Mapping[str, Any], field: str) -> None:
    unsigned = {key: item for key, item in value.items() if key != field}
    if value.get(field) != digest(unsigned):
        raise PortableAdmissionError(f"self digest mismatch:{field}")


def validate_classified_object(
    manifest: Mapping[str, Any],
    object_id: str,
    kind: str,
    value: Mapping[str, Any],
) -> dict[str, Any]:
    instance = manifest["instances"].get(object_id)
    if not isinstance(instance, Mapping) or instance.get("kind") != kind:
        raise PortableAdmissionError(f"missing classified instance:{object_id}")
    shape = classified_shape(kind, value)
    templates = shape.pop("templates")
    frozen_schema = manifest["schemas"][kind]
    frozen_templates = {
        item["pointer"]: item["classification"]
        for item in frozen_schema["expanded_pointer_templates"]
    }
    for pointer, classification in templates.items():
        if frozen_templates.get(pointer) != classification:
            raise PortableAdmissionError(
                f"unclassified or multiply classified field:{object_id}:{pointer}"
            )
    expected = {
        key: instance[key]
        for key in (
            "kind", "leaf_count", "class_counts",
            "concrete_pointer_classification_digest",
        )
    }
    observed = {"kind": kind, **shape}
    if observed != expected:
        raise PortableAdmissionError(f"classified shape changed:{object_id}")
    return observed


def value_at_pointer(value: Any, pointer: str) -> Any:
    current = value
    for part in pointer_parts(pointer):
        if isinstance(current, Mapping):
            if part not in current:
                raise PortableAdmissionError(f"missing classified pointer:{pointer}")
            current = current[part]
        elif isinstance(current, (list, tuple)):
            try:
                current = current[int(part)]
            except (ValueError, IndexError) as exc:
                raise PortableAdmissionError(
                    f"invalid classified array pointer:{pointer}"
                ) from exc
        else:
            raise PortableAdmissionError(f"invalid classified pointer:{pointer}")
    return current


def stable_classified_projection(
    kind: str, value: Mapping[str, Any]
) -> list[dict[str, Any]]:
    classified_shape(kind, value)
    rows = []
    for pointer in leaf_pointers(value):
        classification = classify_pointer(kind, pointer)
        if classification in {SEMANTIC_EXACT, STATIC_FROZEN}:
            rows.append({
                "pointer": pointer,
                "classification": classification,
                "value": copy.deepcopy(value_at_pointer(value, pointer)),
            })
    return rows


def compare_stable_classified_values(
    kind: str, historical_value: Mapping[str, Any],
    fresh_value: Mapping[str, Any], *, label: str
) -> str:
    left = stable_classified_projection(kind, historical_value)
    right = stable_classified_projection(kind, fresh_value)
    if canonical_bytes(left) != canonical_bytes(right):
        raise PortableAdmissionError(
            f"stable classified value changed:{kind}:{label}"
        )
    return digest(left)


def _remove_pointer(value: MutableMapping[str, Any], pointer: str) -> None:
    parts = pointer_parts(pointer)
    current: Any = value
    for part in parts[:-1]:
        if not isinstance(current, MutableMapping) or part not in current:
            raise PortableAdmissionError(f"missing transport path:{pointer}")
        current = current[part]
    if not isinstance(current, MutableMapping) or parts[-1] not in current:
        raise PortableAdmissionError(f"missing transport path:{pointer}")
    del current[parts[-1]]


def portable_projection(
    value: Mapping[str, Any], exclusions: Sequence[str]
) -> dict[str, Any]:
    result = copy.deepcopy(dict(value))
    for pointer in exclusions:
        _remove_pointer(result, pointer)
    return result


def compare_portable_binding(
    historical_binding: Mapping[str, Any], fresh_binding: Mapping[str, Any]
) -> str:
    left = portable_projection(historical_binding, BINDING_TRANSPORT_PATHS)
    right = portable_projection(fresh_binding, BINDING_TRANSPORT_PATHS)
    if canonical_bytes(left) != canonical_bytes(right):
        raise PortableAdmissionError(
            f"portable unit binding changed:{historical_binding.get('unit_id')}"
        )
    return digest(left)


def compare_portable_unit_result(
    historical_result: Mapping[str, Any], fresh_result: Mapping[str, Any]
) -> str:
    left = portable_projection(historical_result, RESULT_TRANSPORT_PATHS)
    right = portable_projection(fresh_result, RESULT_TRANSPORT_PATHS)
    if canonical_bytes(left) != canonical_bytes(right):
        raise PortableAdmissionError(
            f"portable unit result changed:{historical_result.get('unit_id')}"
        )
    return digest(left)


def compare_complete_semantic_identity(
    expected: Mapping[str, Any], observed: Mapping[str, Any], *, label: str
) -> str:
    """Compare the canonical bytes of the complete existing codec identity."""

    if canonical_bytes(expected) != canonical_bytes(observed):
        raise PortableAdmissionError(f"complete semantic identity changed:{label}")
    return digest(expected)


def require_exact_artifact_bytes(
    *, label: str, rebuilt: bytes, preserved_path: Path
) -> str:
    preserved = (ROOT / preserved_path).read_bytes()
    if rebuilt != preserved:
        raise PortableAdmissionError(f"historical {label} bytes changed")
    return sha256_bytes(rebuilt)


def portable_scan_wrapper(value: Mapping[str, Any]) -> dict[str, Any]:
    return portable_projection(
        value, ("/registry_id", "/payload_sha256")
    )


def portable_registry_manifest(value: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(dict(value))
    _remove_pointer(result, "/registry_id")
    organisms = result.get("organisms")
    if not isinstance(organisms, list):
        raise PortableAdmissionError("registry organisms malformed")
    for entry in organisms:
        if not isinstance(entry, MutableMapping) or "payload_sha256" not in entry:
            raise PortableAdmissionError("registry transport entry malformed")
        del entry["payload_sha256"]
    return result


def require_preoutcome(wrapper: Any) -> dict[str, Any]:
    transactions = getattr(wrapper, "event_transactions", None)
    if not isinstance(transactions, Mapping):
        raise PortableAdmissionError("organism event transactions malformed")
    consumed_transactions = sorted(
        str(token) for token, row in transactions.items()
        if isinstance(row, Mapping) and row.get("state") == "CONSUMED"
    )
    conditions = {
        "pending_event_none": getattr(wrapper, "pending_event", object()) is None,
        "consumed_receipts_empty": not bool(getattr(wrapper, "consumed_receipts", None)),
        "consumed_tokens_empty": not bool(getattr(wrapper, "consumed_tokens", None)),
        "prospective_physical_fingerprints_empty": not bool(
            getattr(wrapper, "prospective_physical_fingerprints", None)
        ),
        "emissions_empty": not bool(getattr(wrapper, "emissions", None)),
        "consumed_event_transactions": consumed_transactions,
        "outcome_access": copy.deepcopy(ZERO_OUTCOME),
    }
    if not all(
        value is True
        for key, value in conditions.items()
        if key.endswith("_none") or key.endswith("_empty")
    ) or consumed_transactions:
        raise PortableAdmissionError("organism is not explicitly pre-outcome")
    return conditions


@dataclass(frozen=True)
class HistoricalJournalState:
    plan: Mapping[str, Any]
    prepared_paths: tuple[Path, ...]
    committed_paths: tuple[Path, ...]


def validate_historical_journal() -> HistoricalJournalState:
    journal = historical.RepairExposureUnitJournal(
        ROOT / historical.EXPOSURE_JOURNAL_DIR
    )
    records = journal.records()
    if len(records) != 192:
        raise PortableAdmissionError("historical journal record count changed")
    prepared_by_index: dict[int, list[dict[str, Any]]] = defaultdict(list)
    committed_by_index: dict[int, list[dict[str, Any]]] = defaultdict(list)
    prepared_paths: dict[int, Path] = {}
    committed_paths: dict[int, Path] = {}
    paths = sorted((ROOT / historical.EXPOSURE_JOURNAL_DIR).glob("*.json"))
    for path, row in zip(paths, records, strict=True):
        index = int(row["unit_index"])
        if row["kind"] == "PREPARED":
            prepared_by_index[index].append(row)
            prepared_paths.setdefault(index, path.relative_to(ROOT))
        elif row["kind"] == "COMMITTED":
            committed_by_index[index].append(row)
            committed_paths.setdefault(index, path.relative_to(ROOT))
        else:
            raise PortableAdmissionError("foreign historical journal record")
    if set(prepared_by_index) != set(range(96)) or set(committed_by_index) != set(range(96)):
        raise PortableAdmissionError("historical journal unit coverage changed")
    bindings = []
    for index in range(96):
        attempts = prepared_by_index[index]
        first = attempts[0]["payload"]["unit_binding"]
        if any(
            canonical_bytes(row["payload"]["unit_binding"])
            != canonical_bytes(first)
            for row in attempts[1:]
        ):
            raise PortableAdmissionError(
                f"historical PREPARED bindings disagree:{index}"
            )
        bindings.append(first)
        committed = committed_by_index[index]
        if len(committed) != 1:
            raise PortableAdmissionError(f"historical COMMITTED count changed:{index}")
        row = committed[0]
        payload = row["payload"]
        result = payload.get("unit_result")
        if (
            row["unit_id"] != first["unit_id"]
            or payload.get("unit_binding_digest") != first["unit_binding_digest"]
            or payload.get("prepared_record_digest") != attempts[-1]["record_digest"]
            or not isinstance(result, Mapping)
            or payload.get("unit_result_digest") != digest(result)
            or result.get("unit_result_digest") != digest({
                key: value for key, value in result.items()
                if key != "unit_result_digest"
            })
            or result.get("outcome_access") != ZERO_OUTCOME
        ):
            raise PortableAdmissionError(f"historical COMMITTED changed:{index}")
    # This is intentionally the restored, historically bound validator.
    plan = journal.analyze(tuple(bindings))
    completion = load_json(ROOT / historical.EXPOSURE_COMPLETION_PATH)
    if (
        plan.get("committed_unit_count") != 96
        or plan.get("next_unit_index") is not None
        or plan.get("dangling_prepared_unit_index") is not None
        or plan.get("journal_chain_digest")
        != completion.get("exposure_journal_chain_digest")
        or plan.get("recomputation_count")
        != completion.get("exposure_recomputation_count")
    ):
        raise PortableAdmissionError("historical journal/completion changed")
    del records, bindings, prepared_by_index, committed_by_index
    return HistoricalJournalState(
        plan=copy.deepcopy(plan),
        prepared_paths=tuple(prepared_paths[index] for index in range(96)),
        committed_paths=tuple(committed_paths[index] for index in range(96)),
    )


def _historical_unit(
    state: HistoricalJournalState, index: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    prepared = load_json(ROOT / state.prepared_paths[index])
    committed = load_json(ROOT / state.committed_paths[index])
    return (
        prepared["payload"]["unit_binding"],
        committed["payload"]["unit_result"],
    )


def _registry_entry_by_id(registry: Any, organism_id: str) -> Any:
    matches = [
        item for item in registry.organisms if item.organism_id == organism_id
    ]
    if len(matches) != 1:
        raise PortableAdmissionError(
            f"fresh registry organism association changed:{organism_id}"
        )
    return matches[0]


def reconstruct_historical_registry(
    fresh_registry: Any,
    historical_payload_hashes: Mapping[str, str],
) -> Any:
    if set(historical_payload_hashes) != {
        item.organism_id for item in fresh_registry.organisms
    }:
        raise PortableAdmissionError("historical payload/organism coverage changed")
    entries = tuple(
        laboratory.RegisteredV2Organism(
            organism_id=item.organism_id,
            payload_sha256=str(historical_payload_hashes[item.organism_id]),
            continuation_digest=item.continuation_digest,
            experimental_identity_digest=item.experimental_identity_digest,
            candidate_population_identity=item.candidate_population_identity,
            source_binding_identity=item.source_binding_identity,
        )
        for item in fresh_registry.organisms
    )
    if len({item.payload_sha256 for item in entries}) != len(entries):
        raise PortableAdmissionError("historical payload hashes are not unique")
    if len({item.continuation_digest for item in entries}) != len(entries):
        raise PortableAdmissionError("historical continuations are not unique")
    tape_manifest = {
        "row_order": list(fresh_registry.row_order),
        "organisms": {
            organism_id: [row.manifest() for row in rows]
            for organism_id, rows in fresh_registry.exposure_rows
        },
    }
    tape_identity = laboratory._sha(tape_manifest)
    if tape_identity != fresh_registry.tape_identity:
        raise PortableAdmissionError("historical registry tape identity changed")
    unsigned = {
        "schema_version": laboratory.LAB_REGISTRY_SCHEMA_VERSION,
        "tape_identity": tape_identity,
        "tape_manifest": tape_manifest,
        "run_identity": fresh_registry.run_identity,
        "package_hashes": [list(item) for item in fresh_registry.package_hashes],
        "organisms": [item.manifest() for item in entries],
    }
    return laboratory.V2LaboratoryRegistry(
        schema_version=laboratory.LAB_REGISTRY_SCHEMA_VERSION,
        registry_id=laboratory._sha(unsigned),
        tape_identity=tape_identity,
        row_order=tuple(fresh_registry.row_order),
        run_identity=fresh_registry.run_identity,
        package_hashes=tuple(fresh_registry.package_hashes),
        organisms=entries,
        exposure_rows=tuple(fresh_registry.exposure_rows),
    )


def reconstruct_completion_marker(
    exposure: Mapping[str, Any],
    execution_manifest: Mapping[str, Any],
    journal_plan: Mapping[str, Any],
) -> dict[str, Any]:
    exposure_payload = historical.pretty_json_bytes(exposure)
    execution_payload = historical.pretty_json_bytes(execution_manifest)
    marker = {
        "schema_version": "native_v2_process_readiness_completion.v1",
        "package_id": historical.PACKAGE_ID,
        "experiment_id": driver.EXPERIMENT_ID,
        "unit_count": historical.UNIT_COUNT,
        "exposure_journal_chain_digest": journal_plan["journal_chain_digest"],
        "exposure_recomputation_count": journal_plan["recomputation_count"],
        "exposure": {
            "path": historical.EXPOSURE_PATH.as_posix(),
            "sha256": sha256_bytes(exposure_payload),
            "digest": exposure["exposure_digest"],
        },
        "execution_manifest": {
            "path": historical.EXECUTION_MANIFEST_PATH.as_posix(),
            "sha256": sha256_bytes(execution_payload),
            "digest": execution_manifest["execution_manifest_digest"],
        },
        "outcome_access": copy.deepcopy(ZERO_OUTCOME),
    }
    marker["completion_digest"] = digest(marker)
    return marker


def _historical_identity_files() -> tuple[Path, ...]:
    paths = [STOP_REPORT_PATH, DIAGNOSTIC_PATH]
    paths.extend(sorted((ROOT / PRESERVED_ATTEMPT_PATH).glob("*.json")))
    return tuple(
        path if not path.is_absolute() else path.relative_to(ROOT)
        for path in paths
    )


def _source_dependency_paths() -> tuple[Path, ...]:
    tracked = _git("ls-files", "src", "pyproject.toml", "uv.lock").splitlines()
    values = [Path(item) for item in tracked if item.endswith(".py") or item in {"pyproject.toml", "uv.lock"}]
    values.extend((TEST_PATH, PREREGISTRATION_PATH))
    return tuple(sorted(set(values), key=lambda item: item.as_posix()))


def build_source_manifest(source_commit: str) -> dict[str, Any]:
    paths = _source_dependency_paths()
    hashes = {path.as_posix(): sha256_file(ROOT / path) for path in paths}
    if SELF_PATH.as_posix() not in hashes or TEST_PATH.as_posix() not in hashes:
        raise PortableAdmissionError("bridge source/test absent from source closure")
    value = {
        "schema_version": "native_v2_portable_admission_source.v1",
        "package_id": PACKAGE_ID,
        "module_path": MODULE_PATH,
        "source_commit": source_commit,
        "complete_runtime_source_tree": True,
        "source_hashes": hashes,
        "source_file_count": len(hashes),
        "historical_inner_hashes": verify_historical_inner_hashes(),
        "runtime": {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "working_directory": str(ROOT),
        },
        "commands": {
            "admission": "run-admission",
            "read_only_attempt_verifier": "verify-attempt",
            "read_only_aggregate_verifier": "verify-aggregate",
            "outcome_or_science_commands": [],
        },
    }
    value["source_manifest_digest"] = digest(value)
    return value


def build_dependency_manifest(
    source_manifest: Mapping[str, Any],
    classification_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    protected = verify_protected_files()
    historical_files = {
        path.as_posix(): sha256_file(ROOT / path)
        for path in _historical_identity_files()
    }
    commands = [
        [
            ".venv/bin/python3", "-m", MODULE_PATH, "run-admission",
            "--attempt-id", attempt_id,
        ]
        for attempt_id in ATTEMPT_IDS
    ]
    value = {
        "schema_version": "native_v2_portable_admission_dependencies.v1",
        "package_id": PACKAGE_ID,
        "source_manifest": {
            "path": SOURCE_MANIFEST_PATH.as_posix(),
            "sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
            "digest": source_manifest["source_manifest_digest"],
        },
        "classification_manifest": {
            "path": CLASSIFICATION_MANIFEST_PATH.as_posix(),
            "sha256": sha256_file(ROOT / CLASSIFICATION_MANIFEST_PATH),
            "digest": classification_manifest["classification_manifest_digest"],
        },
        "historical_inner_hashes": verify_historical_inner_hashes(),
        "historical_identity_files": historical_files,
        "protected_files": protected["file_hashes"],
        "protected_file_count": protected["file_count"],
        "protected_file_set_digest": protected["file_set_digest"],
        "historical_artifacts": {
            "journal": historical.EXPOSURE_JOURNAL_DIR.as_posix(),
            "exposure": historical.EXPOSURE_PATH.as_posix(),
            "execution": historical.EXECUTION_MANIFEST_PATH.as_posix(),
            "completion": historical.EXPOSURE_COMPLETION_PATH.as_posix(),
        },
        "attempt_ids": list(ATTEMPT_IDS),
        "exact_process_commands": commands,
        "process_count": 3,
        "gates": {
            "historical_units": 96,
            "complete_semantic_identities": 96,
            "portable_bindings": 96,
            "portable_unit_results": 96,
            "historical_registry_count": 3,
            "exact_artifact_count": 3,
            "protected_file_count": PROTECTED_FILE_COUNT,
            "mutation_count": 0,
            "outcome_access_count": 0,
            "three_process_results_identical": True,
        },
        "prohibitions": [
            "exposure execution", "outcome environment", "science execution",
            "R1", "retired-65", "historical regression", "held-out learning",
            "fresh learning", "learner growth", "production launcher wiring",
        ],
        "success_classification": (
            "Portable admission and exact historical reconstruction passed."
        ),
    }
    value["artifact_dependency_manifest_digest"] = digest(value)
    return value


def freeze_package(source_commit: str) -> dict[str, Any]:
    if (ROOT / SOURCE_MANIFEST_PATH).exists() or (ROOT / CLASSIFICATION_MANIFEST_PATH).exists() or (ROOT / DEPENDENCY_MANIFEST_PATH).exists():
        raise PortableAdmissionError("portable admission package already frozen")
    verify_historical_inner_hashes()
    verify_protected_files()
    verify_zero_outcome_access()
    classification = build_classification_manifest()
    atomic_json(ROOT / CLASSIFICATION_MANIFEST_PATH, classification)
    source = build_source_manifest(source_commit)
    atomic_json(ROOT / SOURCE_MANIFEST_PATH, source)
    dependencies = build_dependency_manifest(source, classification)
    atomic_json(ROOT / DEPENDENCY_MANIFEST_PATH, dependencies)
    return {
        "source_manifest_sha256": sha256_file(ROOT / SOURCE_MANIFEST_PATH),
        "source_manifest_digest": source["source_manifest_digest"],
        "classification_manifest_sha256": sha256_file(
            ROOT / CLASSIFICATION_MANIFEST_PATH
        ),
        "classification_manifest_digest": classification[
            "classification_manifest_digest"
        ],
        "artifact_dependency_manifest_sha256": sha256_file(
            ROOT / DEPENDENCY_MANIFEST_PATH
        ),
        "artifact_dependency_manifest_digest": dependencies[
            "artifact_dependency_manifest_digest"
        ],
    }


def _require_committed_bytes(path: Path) -> None:
    try:
        committed = subprocess.check_output(
            ("git", "show", f"HEAD:{path.as_posix()}"), cwd=ROOT
        )
    except subprocess.CalledProcessError as exc:
        raise PortableAdmissionError(f"frozen file is not committed:{path}") from exc
    if committed != (ROOT / path).read_bytes():
        raise PortableAdmissionError(f"frozen file differs from HEAD:{path}")


def verify_package_freeze() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source = load_json(ROOT / SOURCE_MANIFEST_PATH)
    classification = load_json(ROOT / CLASSIFICATION_MANIFEST_PATH)
    dependencies = load_json(ROOT / DEPENDENCY_MANIFEST_PATH)
    verify_self_digest(source, "source_manifest_digest")
    verify_self_digest(classification, "classification_manifest_digest")
    verify_self_digest(dependencies, "artifact_dependency_manifest_digest")
    for path in (
        SOURCE_MANIFEST_PATH, CLASSIFICATION_MANIFEST_PATH,
        DEPENDENCY_MANIFEST_PATH,
    ):
        _require_committed_bytes(path)
    for relative, expected in source["source_hashes"].items():
        if sha256_file(ROOT / Path(relative)) != expected:
            raise PortableAdmissionError(f"frozen source changed:{relative}")
    if source["historical_inner_hashes"] != verify_historical_inner_hashes():
        raise PortableAdmissionError("historical inner source binding changed")
    if dependencies["historical_identity_files"] != {
        path.as_posix(): sha256_file(ROOT / path)
        for path in _historical_identity_files()
    }:
        raise PortableAdmissionError("preserved stop evidence changed")
    verify_protected_files(dependencies["protected_files"])
    verify_zero_outcome_access()
    if (
        dependencies["source_manifest"]["sha256"]
        != sha256_file(ROOT / SOURCE_MANIFEST_PATH)
        or dependencies["classification_manifest"]["sha256"]
        != sha256_file(ROOT / CLASSIFICATION_MANIFEST_PATH)
    ):
        raise PortableAdmissionError("bridge manifest binding changed")
    return source, classification, dependencies


def _attempt_record(stage: str, value: Mapping[str, Any]) -> dict[str, Any]:
    record = {
        "schema_version": "native_v2_portable_admission_attempt_record.v1",
        "package_id": PACKAGE_ID,
        "stage": stage,
        **copy.deepcopy(dict(value)),
    }
    record["record_digest"] = digest(record)
    return record


def _attempt_dir(attempt_id: str) -> Path:
    if attempt_id not in ATTEMPT_IDS:
        raise PortableAdmissionError(f"attempt is not frozen:{attempt_id}")
    return ROOT / ATTEMPT_ROOT / attempt_id


def _load_attempt_record(path: Path) -> dict[str, Any]:
    value = load_json(path)
    verify_self_digest(value, "record_digest")
    if value.get("package_id") != PACKAGE_ID:
        raise PortableAdmissionError(f"foreign attempt record:{path}")
    return value


def _portable_registry_and_scan_checks(
    *,
    runtime: Mapping[str, Any],
    exposure: Mapping[str, Any],
    historical_payloads: Mapping[str, Mapping[str, str]],
    stored_results: Sequence[Mapping[str, Any]],
    fresh_results: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    by_key_stored = {
        (str(row["arm"]), int(row["seed_ordinal"])): row
        for row in stored_results
    }
    by_key_fresh = {
        (str(row["arm"]), int(row["seed_ordinal"])): row
        for row in fresh_results
    }
    registries = {}
    checks = {}
    for arm in execution.ARMS:
        fresh_registry = runtime["registries"][arm]["registry"]
        reconstructed = reconstruct_historical_registry(
            fresh_registry, historical_payloads[arm]
        )
        historical_manifest = driver._registry_manifest(reconstructed)
        preserved_manifest = exposure["arms"][arm]["registry"]
        if canonical_bytes(historical_manifest) != canonical_bytes(preserved_manifest):
            raise PortableAdmissionError(
                f"historical registry manifest changed:{arm}"
            )
        fresh_manifest = driver._registry_manifest(fresh_registry)
        if canonical_bytes(portable_registry_manifest(fresh_manifest)) != canonical_bytes(
            portable_registry_manifest(historical_manifest)
        ):
            raise PortableAdmissionError(f"portable registry changed:{arm}")
        wrappers = []
        for ordinal in range(execution.SEED_COUNT):
            stored = by_key_stored[(arm, ordinal)]["scan_wrapper"]
            fresh = by_key_fresh[(arm, ordinal)]["scan_wrapper"]
            organism_id = f"seed-{ordinal:02d}"
            if (
                stored["payload_sha256"] != historical_payloads[arm][organism_id]
                or stored["registry_id"] != reconstructed.registry_id
                or canonical_bytes(portable_scan_wrapper(stored))
                != canonical_bytes(portable_scan_wrapper(fresh))
            ):
                raise PortableAdmissionError(
                    f"historical/fresh scan association changed:{arm}:{ordinal}"
                )
            wrappers.append(stored)
        adjudication = reconstructed.adjudicate_cohort(
            wrappers,
            tape_identity=reconstructed.tape_identity,
            row_order=runtime["row_order"],
            run_identity=reconstructed.run_identity,
            package_hashes=runtime["package_hashes"],
        )
        if adjudication != exposure["arms"][arm]["registry_adjudication"]:
            raise PortableAdmissionError(
                f"historical registry adjudication changed:{arm}"
            )
        registries[arm] = reconstructed
        checks[arm] = {
            "historical_registry_id": reconstructed.registry_id,
            "fresh_registry_id": fresh_registry.registry_id,
            "registry_manifest_digest": digest(historical_manifest),
            "portable_registry_digest": digest(
                portable_registry_manifest(historical_manifest)
            ),
            "stored_wrapper_count": len(wrappers),
            "adjudication": copy.deepcopy(adjudication),
        }
    return registries, checks


def _build_historical_runtime(
    runtime: Mapping[str, Any], registries: Mapping[str, Any]
) -> dict[str, Any]:
    result = dict(runtime)
    result["registries"] = {
        arm: {**dict(runtime["registries"][arm]), "registry": registries[arm]}
        for arm in execution.ARMS
    }
    return result


def run_admission(attempt_id: str) -> dict[str, Any]:
    started = time.monotonic()
    attempt_dir = _attempt_dir(attempt_id)
    if attempt_dir.exists():
        raise PortableAdmissionError(f"attempt already exists:{attempt_id}")
    attempt_dir.mkdir(parents=True, exist_ok=False)
    try:
        source, classification, dependencies = verify_package_freeze()
        expected_command = [
            ".venv/bin/python3", "-m", MODULE_PATH, "run-admission",
            "--attempt-id", attempt_id,
        ]
        index = ATTEMPT_IDS.index(attempt_id)
        if dependencies["exact_process_commands"][index] != expected_command:
            raise PortableAdmissionError("literal admission command changed")
        if Path(sys.executable).resolve() != (ROOT / ".venv/bin/python3").resolve():
            raise PortableAdmissionError("admission interpreter changed")
        started_record = _attempt_record("started", {
            "attempt_id": attempt_id,
            "process_id": os.getpid(),
            "argv": list(sys.argv),
            "literal_frozen_command": expected_command,
            "source_manifest_digest": source["source_manifest_digest"],
            "classification_manifest_digest": classification[
                "classification_manifest_digest"
            ],
            "dependency_manifest_digest": dependencies[
                "artifact_dependency_manifest_digest"
            ],
            "protected_file_set_digest": PROTECTED_FILE_SET_DIGEST,
            "outcome_access": copy.deepcopy(ZERO_OUTCOME),
        })
        atomic_json(attempt_dir / "00_started.json", started_record)

        historical_state = validate_historical_journal()
        historical_record = _attempt_record("historical_journal_verified", {
            "attempt_id": attempt_id,
            "historical_unit_count": 96,
            "journal_record_count": 192,
            "journal_chain_digest": historical_state.plan[
                "journal_chain_digest"
            ],
            "recomputation_count": historical_state.plan[
                "recomputation_count"
            ],
            "outcome_access": copy.deepcopy(ZERO_OUTCOME),
        })
        atomic_json(attempt_dir / "01_historical_journal_verified.json", historical_record)

        runtime = historical.build_real_exposure_runtime()
        fresh_bindings = tuple(execution.production_unit_bindings(runtime))
        if len(fresh_bindings) != 96:
            raise PortableAdmissionError("fresh unit binding coverage changed")
        codec = driver.V2SnapshotCodec()
        exposure = load_json(ROOT / historical.EXPOSURE_PATH)
        stored_results: list[dict[str, Any]] = []
        fresh_results: list[dict[str, Any]] = []
        historical_payloads: dict[str, dict[str, str]] = {
            arm: {} for arm in execution.ARMS
        }
        semantic_rows = []
        progress_path = attempt_dir / "progress.json"

        for index, fresh_binding in enumerate(fresh_bindings):
            historical_binding, stored_result = _historical_unit(
                historical_state, index
            )
            validate_classified_object(
                classification, f"unit-binding:{index}", "unit_binding",
                historical_binding,
            )
            validate_classified_object(
                classification, f"unit-result:{index}", "unit_result",
                stored_result,
            )
            validate_classified_object(
                classification, f"scan-wrapper:{index}", "scan_wrapper",
                stored_result["scan_wrapper"],
            )
            validate_classified_object(
                classification, f"unit-binding:{index}", "unit_binding",
                fresh_binding,
            )
            portable_binding_digest = compare_portable_binding(
                historical_binding, fresh_binding
            )
            arm = str(fresh_binding["arm"])
            ordinal = int(fresh_binding["seed_ordinal"])
            organism_id = str(fresh_binding["organism_id"])
            if (
                int(fresh_binding["unit_index"]) != index
                or fresh_binding["unit_id"] != f"{arm}/seed-{ordinal:02d}"
                or organism_id != f"seed-{ordinal:02d}"
            ):
                raise PortableAdmissionError(
                    f"fresh unit association changed:{index}"
                )
            wrapper = runtime["restored"][(ordinal, arm)]
            preoutcome = require_preoutcome(wrapper)
            complete_semantic = codec.semantic_identity(wrapper)
            source_entry = historical_binding["source_snapshot_identity"]["entry"]
            compare_complete_semantic_identity(
                source_entry["semantic_identity"],
                complete_semantic,
                label=f"{arm}:{ordinal}",
            )
            if source_entry["semantic_identity_digest"] != digest(complete_semantic):
                raise PortableAdmissionError(
                    f"source snapshot semantic digest changed:{arm}:{ordinal}"
                )
            fresh_registry = runtime["registries"][arm]["registry"]
            fresh_entry = _registry_entry_by_id(fresh_registry, organism_id)
            preserved_entry = exposure["arms"][arm]["registry"]["organisms"][ordinal]
            if (
                fresh_entry.organism_id != organism_id
                or fresh_entry.continuation_digest
                != complete_semantic["continuation_digest"]
                or fresh_entry.experimental_identity_digest
                != complete_semantic["experiment_identity"]
                or fresh_entry.candidate_population_identity
                != complete_semantic["candidate_population_identity"]
                or fresh_entry.source_binding_identity
                != stored_result["scan_wrapper"]["source_binding_identity"]
                or fresh_entry.source_binding_identity
                != preserved_entry["source_binding_identity"]
            ):
                raise PortableAdmissionError(
                    f"external semantic/source binding changed:{arm}:{ordinal}"
                )
            before_identity = codec.semantic_identity(wrapper)
            fresh_result = execution.compute_production_unit(fresh_binding, runtime)
            after_identity = codec.semantic_identity(wrapper)
            if canonical_bytes(before_identity) != canonical_bytes(after_identity):
                raise PortableAdmissionError(
                    f"fresh scan mutated complete organism:{arm}:{ordinal}"
                )
            validate_classified_object(
                classification, f"unit-result:{index}", "unit_result",
                fresh_result,
            )
            validate_classified_object(
                classification, f"scan-wrapper:{index}", "scan_wrapper",
                fresh_result["scan_wrapper"],
            )
            portable_result_digest = compare_portable_unit_result(
                stored_result, fresh_result
            )
            historical_payload = str(historical_binding["payload_sha256"])
            if historical_payload != stored_result["scan_wrapper"]["payload_sha256"]:
                raise PortableAdmissionError(
                    f"historical payload association changed:{arm}:{ordinal}"
                )
            historical_payloads[arm][organism_id] = historical_payload
            stored_results.append(copy.deepcopy(stored_result))
            fresh_results.append(fresh_result)
            row = {
                "unit_index": index,
                "unit_id": fresh_binding["unit_id"],
                "arm": arm,
                "seed_ordinal": ordinal,
                "organism_id": organism_id,
                "complete_semantic_identity_digest": digest(complete_semantic),
                "preoutcome_state_digest": digest(preoutcome),
                "portable_binding_digest": portable_binding_digest,
                "portable_unit_result_digest": portable_result_digest,
                "fresh_scan_digest": fresh_result["scan_wrapper"]["scan_digest"],
                "continuation_digest": fresh_result[
                    "continuation_digest_before"
                ],
                "candidate_graph_state_unchanged": True,
                "outcome_access": copy.deepcopy(ZERO_OUTCOME),
            }
            row["row_digest"] = digest(row)
            semantic_rows.append(row)
            replace_progress(progress_path, _attempt_record("fresh_units", {
                "attempt_id": attempt_id,
                "completed_unit_count": index + 1,
                "last_unit_id": fresh_binding["unit_id"],
                "completed_row_digest": digest(semantic_rows),
                "outcome_access": copy.deepcopy(ZERO_OUTCOME),
            }))

        # Build and classify the wholly fresh summary before any historical
        # transport value is inserted into a reconstructed registry.
        fresh_exposure = execution.assemble_production_exposure(
            runtime, fresh_results
        )
        launch_readiness = historical.load_and_verify_launch_readiness(
            committed=True
        )
        fresh_exposure_bytes = historical.pretty_json_bytes(fresh_exposure)
        fresh_execution = historical.build_execution_manifest(
            runtime,
            fresh_exposure,
            sha256_bytes(fresh_exposure_bytes),
            launch_readiness=launch_readiness,
        )
        fresh_completion = reconstruct_completion_marker(
            fresh_exposure, fresh_execution, historical_state.plan
        )
        preserved_execution = load_json(
            ROOT / historical.EXECUTION_MANIFEST_PATH
        )
        preserved_completion = load_json(
            ROOT / historical.EXPOSURE_COMPLETION_PATH
        )
        fresh_object_checks = {}
        for object_id, kind, preserved_value, fresh_value in (
            ("exposure", "exposure_artifact", exposure, fresh_exposure),
            ("execution", "execution_manifest", preserved_execution, fresh_execution),
            ("completion", "completion_marker", preserved_completion, fresh_completion),
        ):
            validate_classified_object(
                classification, object_id, kind, fresh_value
            )
            fresh_object_checks[object_id] = compare_stable_classified_values(
                kind, preserved_value, fresh_value, label=object_id
            )
        for arm in execution.ARMS:
            preserved_arm = exposure["arms"][arm]
            fresh_arm = fresh_exposure["arms"][arm]
            validate_classified_object(
                classification, f"per-arm:{arm}", "per_arm_summary", fresh_arm
            )
            fresh_object_checks[f"per-arm:{arm}"] = (
                compare_stable_classified_values(
                    "per_arm_summary", preserved_arm, fresh_arm,
                    label=f"per-arm:{arm}",
                )
            )
            validate_classified_object(
                classification, f"registry:{arm}", "registry_manifest",
                fresh_arm["registry"],
            )
            compare_stable_classified_values(
                "registry_manifest", preserved_arm["registry"],
                fresh_arm["registry"], label=f"registry:{arm}",
            )
            for ordinal in range(execution.SEED_COUNT):
                validate_classified_object(
                    classification, f"registry-entry:{arm}:{ordinal}",
                    "registry_entry", fresh_arm["registry"]["organisms"][ordinal],
                )
                validate_classified_object(
                    classification, f"per-seed:{arm}:{ordinal}",
                    "per_seed_summary", fresh_arm["per_seed"][ordinal],
                )

        # Historical byte-derived values are first inserted only after all 96
        # complete semantic, binding, scan and result comparisons have passed.
        historical_registries, registry_checks = (
            _portable_registry_and_scan_checks(
                runtime=runtime,
                exposure=exposure,
                historical_payloads=historical_payloads,
                stored_results=stored_results,
                fresh_results=fresh_results,
            )
        )
        historical_runtime = _build_historical_runtime(
            runtime, historical_registries
        )
        rebuilt_exposure = execution.assemble_production_exposure(
            historical_runtime, stored_results
        )
        rebuilt_exposure_bytes = historical.pretty_json_bytes(rebuilt_exposure)
        exposure_sha256 = require_exact_artifact_bytes(
            label="exposure",
            rebuilt=rebuilt_exposure_bytes,
            preserved_path=historical.EXPOSURE_PATH,
        )
        rebuilt_execution = historical.build_execution_manifest(
            historical_runtime,
            rebuilt_exposure,
            sha256_bytes(rebuilt_exposure_bytes),
            launch_readiness=launch_readiness,
        )
        rebuilt_execution_bytes = historical.pretty_json_bytes(rebuilt_execution)
        execution_sha256 = require_exact_artifact_bytes(
            label="execution",
            rebuilt=rebuilt_execution_bytes,
            preserved_path=historical.EXECUTION_MANIFEST_PATH,
        )
        rebuilt_completion = reconstruct_completion_marker(
            rebuilt_exposure, rebuilt_execution, historical_state.plan
        )
        rebuilt_completion_bytes = historical.pretty_json_bytes(
            rebuilt_completion
        )
        completion_sha256 = require_exact_artifact_bytes(
            label="completion",
            rebuilt=rebuilt_completion_bytes,
            preserved_path=historical.EXPOSURE_COMPLETION_PATH,
        )
        protected = verify_protected_files(dependencies["protected_files"])
        outcome = verify_zero_outcome_access()
        result = _attempt_record("passed", {
            "attempt_id": attempt_id,
            "process_id": os.getpid(),
            "classification": (
                "Portable admission and exact historical reconstruction passed."
            ),
            "historical_journal": {
                "unit_count": 96,
                "record_count": 192,
                "journal_chain_digest": historical_state.plan[
                    "journal_chain_digest"
                ],
                "recomputation_count": historical_state.plan[
                    "recomputation_count"
                ],
            },
            "fresh_verification": {
                "complete_semantic_identity_count": len(semantic_rows),
                "portable_binding_count": len(semantic_rows),
                "portable_unit_result_count": len(semantic_rows),
                "portable_cohort_digest": digest(semantic_rows),
                "unit_rows": semantic_rows,
                "fresh_summary_classification_digests": fresh_object_checks,
                "mutation_count": 0,
            },
            "historical_registries": registry_checks,
            "exact_artifacts": {
                "exposure_sha256": exposure_sha256,
                "exposure_digest": rebuilt_exposure["exposure_digest"],
                "execution_sha256": execution_sha256,
                "execution_digest": rebuilt_execution[
                    "execution_manifest_digest"
                ],
                "completion_sha256": completion_sha256,
                "completion_digest": rebuilt_completion[
                    "completion_digest"
                ],
            },
            "protected_files": {
                "file_count": protected["file_count"],
                "file_set_digest": protected["file_set_digest"],
            },
            "outcome_access": outcome,
            "elapsed_seconds": time.monotonic() - started,
        })
        atomic_json(attempt_dir / "result.json", result)
        return result
    except Exception as exc:
        failure = _attempt_record("failed", {
            "attempt_id": attempt_id,
            "process_id": os.getpid(),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback_tail": traceback.format_exc().splitlines()[-20:],
            "outcome_access": copy.deepcopy(ZERO_OUTCOME),
            "elapsed_seconds": time.monotonic() - started,
        })
        failure_path = attempt_dir / "failure.json"
        if not failure_path.exists():
            atomic_json(failure_path, failure)
        raise


def verify_attempt(attempt_id: str) -> dict[str, Any]:
    _, _, dependencies = verify_package_freeze()
    attempt_dir = _attempt_dir(attempt_id)
    result_path = attempt_dir / "result.json"
    if not result_path.exists() or (attempt_dir / "failure.json").exists():
        raise PortableAdmissionError(f"attempt is not a passing result:{attempt_id}")
    allowed = {
        "00_started.json", "01_historical_journal_verified.json",
        "progress.json", "result.json",
    }
    actual = {path.name for path in attempt_dir.iterdir() if path.is_file()}
    if actual != allowed:
        raise PortableAdmissionError(
            f"attempt file set changed:{attempt_id}:{sorted(actual)}"
        )
    started = _load_attempt_record(attempt_dir / "00_started.json")
    historical_record = _load_attempt_record(
        attempt_dir / "01_historical_journal_verified.json"
    )
    progress = _load_attempt_record(attempt_dir / "progress.json")
    result = _load_attempt_record(result_path)
    if (
        any(row.get("attempt_id") != attempt_id for row in (
            started, historical_record, progress, result
        ))
        or result.get("stage") != "passed"
        or result.get("classification")
        != "Portable admission and exact historical reconstruction passed."
        or result["fresh_verification"]["complete_semantic_identity_count"] != 96
        or result["fresh_verification"]["portable_binding_count"] != 96
        or result["fresh_verification"]["portable_unit_result_count"] != 96
        or progress.get("completed_unit_count") != 96
        or len(result.get("historical_registries", {})) != 3
        or result.get("protected_files") != {
            "file_count": PROTECTED_FILE_COUNT,
            "file_set_digest": PROTECTED_FILE_SET_DIGEST,
        }
        or result.get("outcome_access") != {
            "count": 0, "event_ids": [], "science_paths_absent": True
        }
    ):
        raise PortableAdmissionError(f"attempt gate failed:{attempt_id}")
    expected_index = ATTEMPT_IDS.index(attempt_id)
    if dependencies["exact_process_commands"][expected_index][-1] != attempt_id:
        raise PortableAdmissionError("attempt/command association changed")
    return {
        "attempt_id": attempt_id,
        "result_sha256": sha256_file(result_path),
        "result_digest": result["record_digest"],
        "portable_cohort_digest": result["fresh_verification"][
            "portable_cohort_digest"
        ],
        "historical_registry_ids": {
            arm: value["historical_registry_id"]
            for arm, value in result["historical_registries"].items()
        },
        "exact_artifacts": copy.deepcopy(result["exact_artifacts"]),
        "outcome_access": copy.deepcopy(ZERO_OUTCOME),
    }


def verify_aggregate() -> dict[str, Any]:
    rows = [verify_attempt(attempt_id) for attempt_id in ATTEMPT_IDS]
    fields = (
        "portable_cohort_digest", "historical_registry_ids", "exact_artifacts"
    )
    if len({row["attempt_id"] for row in rows}) != 3:
        raise PortableAdmissionError("three admission attempt identities changed")
    result_process_ids = {
        _load_attempt_record(_attempt_dir(row["attempt_id"]) / "result.json")[
            "process_id"
        ]
        for row in rows
    }
    if len(result_process_ids) != 3:
        raise PortableAdmissionError("admissions did not use three fresh processes")
    for field in fields:
        if len({canonical_bytes(row[field]) for row in rows}) != 1:
            raise PortableAdmissionError(
                f"three admission processes disagree:{field}"
            )
    value = {
        "schema_version": "native_v2_portable_admission_aggregate.v1",
        "package_id": PACKAGE_ID,
        "classification": (
            "Portable admission and exact historical reconstruction passed."
        ),
        "attempt_count": 3,
        "attempts": rows,
        "portable_cohort_digest": rows[0]["portable_cohort_digest"],
        "historical_registry_ids": rows[0]["historical_registry_ids"],
        "exact_artifacts": rows[0]["exact_artifacts"],
        "protected_file_count": PROTECTED_FILE_COUNT,
        "protected_file_set_digest": PROTECTED_FILE_SET_DIGEST,
        "mutation_count": 0,
        "outcome_access": copy.deepcopy(ZERO_OUTCOME),
    }
    value["aggregate_digest"] = digest(value)
    return value


def _print(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, sort_keys=True, indent=2))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    freeze = subparsers.add_parser("freeze-package")
    freeze.add_argument("--source-commit", required=True)
    run = subparsers.add_parser("run-admission")
    run.add_argument("--attempt-id", required=True, choices=ATTEMPT_IDS)
    verify = subparsers.add_parser("verify-attempt")
    verify.add_argument("--attempt-id", required=True, choices=ATTEMPT_IDS)
    subparsers.add_parser("verify-aggregate")
    arguments = parser.parse_args(argv)
    if arguments.command == "freeze-package":
        _print(freeze_package(arguments.source_commit))
    elif arguments.command == "run-admission":
        _print(run_admission(arguments.attempt_id))
    elif arguments.command == "verify-attempt":
        _print(verify_attempt(arguments.attempt_id))
    elif arguments.command == "verify-aggregate":
        _print(verify_aggregate())
    else:  # pragma: no cover - argparse makes this unreachable.
        raise PortableAdmissionError("unknown bridge command")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

