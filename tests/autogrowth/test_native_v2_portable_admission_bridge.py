from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from recon_lite_chess.autogrowth import (
    native_v2_portable_admission_bridge as bridge,
)


BASE = Path(
    "reports/autogrowth/native_authority/v2_process_readiness_repair"
)


@pytest.fixture(scope="module")
def frozen_rows() -> tuple[dict, dict, dict, dict]:
    prepared = json.loads((
        BASE / "exposure_journal/000000_PREPARED_000_A_seed-00.json"
    ).read_text())
    committed = json.loads((
        BASE / "exposure_journal/000001_COMMITTED_000_A_seed-00.json"
    ).read_text())
    return (
        prepared,
        committed,
        prepared["payload"]["unit_binding"],
        committed["payload"]["unit_result"],
    )


def mutate_path(value: dict, pointer: str, replacement: object) -> dict:
    result = copy.deepcopy(value)
    parts = bridge.pointer_parts(pointer)
    current = result
    for part in parts[:-1]:
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    if isinstance(current, list):
        current[int(parts[-1])] = replacement
    else:
        current[parts[-1]] = replacement
    return result


def test_historical_files_are_restored_and_protected() -> None:
    assert bridge.verify_historical_inner_hashes() == {
        bridge.HISTORICAL_PROCESS_PATH.as_posix(): (
            bridge.HISTORICAL_PROCESS_SHA256
        ),
        bridge.HISTORICAL_TEST_PATH.as_posix(): bridge.HISTORICAL_TEST_SHA256,
    }
    protected = bridge.verify_protected_files()
    assert protected["file_count"] == 195
    assert protected["file_set_digest"] == bridge.PROTECTED_FILE_SET_DIGEST
    assert bridge.verify_zero_outcome_access()["count"] == 0


def test_public_surface_has_one_admission_and_no_outcome_command() -> None:
    source = Path(bridge.__file__).read_text()
    assert source.count('subparsers.add_parser("run-admission")') == 1
    assert 'add_parser("run-exposure")' not in source
    assert 'add_parser("run-science")' not in source
    assert "FrozenTruthfulEnvironment(" not in source
    assert "monkeypatch" not in source


def test_closed_classification_rejects_unknown_root(frozen_rows) -> None:
    binding = copy.deepcopy(frozen_rows[2])
    binding["unexpected"] = 1
    with pytest.raises(bridge.PortableAdmissionError, match="closed field roots"):
        bridge.classified_shape("unit_binding", binding)
    with pytest.raises(bridge.PortableAdmissionError, match="unclassified field"):
        bridge.classify_pointer("unit_binding", "/unexpected/value")


def test_source_snapshot_transport_is_static_frozen() -> None:
    for pointer in (
        "/source_snapshot_identity/entry/raw_sha256",
        "/source_snapshot_identity/entry/compressed_sha256",
        "/source_snapshot_identity/entry/semantic_identity_digest",
        "/source_snapshot_identity/entry_digest",
    ):
        assert bridge.classify_pointer("unit_binding", pointer) == bridge.STATIC_FROZEN
    assert bridge.classify_pointer(
        "unit_binding",
        "/source_snapshot_identity/entry/semantic_identity/continuation_digest",
    ) == bridge.SEMANTIC_EXACT


def test_pickle_transport_only_binding_difference_passes(frozen_rows) -> None:
    original = frozen_rows[2]
    changed = copy.deepcopy(original)
    changed["payload_sha256"] = "1" * 64
    changed["registry_identity"] = "2" * 64
    changed["unit_binding_digest"] = "3" * 64
    assert bridge.compare_portable_binding(original, changed) == bridge.digest(
        bridge.portable_projection(original, bridge.BINDING_TRANSPORT_PATHS)
    )


@pytest.mark.parametrize(
    ("pointer", "replacement"),
    [
        ("/arm", "B"),
        ("/seed_ordinal", 31),
        ("/organism_id", "seed-31"),
        ("/candidate_graph_continuation_digest", "4" * 64),
        ("/registry_tape_identity", "5" * 64),
        ("/registry_run_identity", "6" * 64),
        ("/expanded_package_map_digest", "7" * 64),
        ("/row_order/0", "changed-row"),
        ("/row_definitions/0/frame_id", "changed-frame"),
        (
            "/source_snapshot_identity/entry/semantic_identity/"
            "candidate_population_identity",
            "8" * 64,
        ),
        (
            "/source_snapshot_identity/entry/semantic_identity/"
            "continuation_digest",
            "9" * 64,
        ),
    ],
)
def test_portable_binding_rejects_semantic_association_changes(
    frozen_rows, pointer, replacement
) -> None:
    original = frozen_rows[2]
    with pytest.raises(bridge.PortableAdmissionError, match="portable unit binding"):
        bridge.compare_portable_binding(
            original, mutate_path(original, pointer, replacement)
        )


def test_pickle_transport_only_result_difference_passes(frozen_rows) -> None:
    original = frozen_rows[3]
    changed = copy.deepcopy(original)
    changed["unit_binding_digest"] = "1" * 64
    changed["scan_wrapper"]["registry_id"] = "2" * 64
    changed["scan_wrapper"]["payload_sha256"] = "3" * 64
    changed["unit_result_digest"] = "4" * 64
    assert bridge.compare_portable_unit_result(original, changed) == bridge.digest(
        bridge.portable_projection(original, bridge.RESULT_TRANSPORT_PATHS)
    )


@pytest.mark.parametrize(
    ("pointer", "replacement"),
    [
        ("/arm", "C"),
        ("/commitments/0/successor_fen", "8/8/8/8/8/8/8/K6k w - - 0 1"),
        ("/classifier_visible_projections/0/row_id", "changed-row"),
        (
            "/classifier_visible_projections/0/planted_activation",
            "__toggle_bool__",
        ),
        ("/target_counts/planted/distinct_opportunities", 99),
        ("/scan_wrapper/source_binding_identity", "1" * 64),
        ("/scan_wrapper/tape_identity", "2" * 64),
        ("/scan_wrapper/run_identity", "3" * 64),
        ("/scan_wrapper/scan_digest", "4" * 64),
        ("/scan_wrapper/scan/source_binding_identity", "5" * 64),
        ("/continuation_digest_after", "6" * 64),
        ("/candidate_graph_state_unchanged", False),
        ("/outcome_access/count", 1),
    ],
)
def test_portable_result_rejects_all_semantic_scan_changes(
    frozen_rows, pointer, replacement
) -> None:
    original = frozen_rows[3]
    if replacement == "__toggle_bool__":
        current = original["classifier_visible_projections"][0][
            "planted_activation"
        ]
        replacement = not current
    with pytest.raises(bridge.PortableAdmissionError, match="portable unit result"):
        bridge.compare_portable_unit_result(
            original, mutate_path(original, pointer, replacement)
        )


def test_complete_codec_identity_is_not_a_selected_summary(frozen_rows) -> None:
    identity = frozen_rows[2]["source_snapshot_identity"]["entry"][
        "semantic_identity"
    ]
    assert bridge.compare_complete_semantic_identity(
        identity, copy.deepcopy(identity), label="synthetic"
    ) == bridge.digest(identity)
    changed = copy.deepcopy(identity)
    changed["continuation_manifest"]["mode"] = "changed"
    with pytest.raises(bridge.PortableAdmissionError, match="complete semantic"):
        bridge.compare_complete_semantic_identity(identity, changed, label="synthetic")


def test_explicit_preoutcome_contract() -> None:
    clean = SimpleNamespace(
        pending_event=None,
        consumed_receipts={},
        consumed_tokens=set(),
        prospective_physical_fingerprints={},
        emissions={},
        event_transactions={},
    )
    assert bridge.require_preoutcome(clean)["outcome_access"] == bridge.ZERO_OUTCOME
    fields = (
        ("pending_event", object()),
        ("consumed_receipts", {"r": 1}),
        ("consumed_tokens", {"t"}),
        ("prospective_physical_fingerprints", {"f": "x"}),
        ("emissions", {"e": 1}),
        ("event_transactions", {"t": {"state": "CONSUMED"}}),
    )
    for field, bad in fields:
        candidate = copy.copy(clean)
        setattr(candidate, field, bad)
        with pytest.raises(bridge.PortableAdmissionError, match="pre-outcome"):
            bridge.require_preoutcome(candidate)


def test_registry_portable_projection_rejects_order_and_semantics(frozen_rows) -> None:
    exposure = json.loads((BASE / "preoutcome_exposure.json").read_text())
    registry = exposure["arms"]["A"]["registry"]
    transport = copy.deepcopy(registry)
    transport["registry_id"] = "1" * 64
    for index, item in enumerate(transport["organisms"]):
        item["payload_sha256"] = f"{index + 1:064x}"[-64:]
    assert bridge.portable_registry_manifest(registry) == (
        bridge.portable_registry_manifest(transport)
    )
    reordered = copy.deepcopy(registry)
    reordered["organisms"] = list(reversed(reordered["organisms"]))
    assert bridge.portable_registry_manifest(registry) != (
        bridge.portable_registry_manifest(reordered)
    )
    changed = copy.deepcopy(registry)
    changed["organisms"][0]["source_binding_identity"] = "2" * 64
    assert bridge.portable_registry_manifest(registry) != (
        bridge.portable_registry_manifest(changed)
    )


def test_stable_classified_projection_excludes_only_declared_transport(
    frozen_rows,
) -> None:
    original = frozen_rows[3]
    changed = copy.deepcopy(original)
    changed["unit_binding_digest"] = "1" * 64
    changed["scan_wrapper"]["registry_id"] = "2" * 64
    changed["scan_wrapper"]["payload_sha256"] = "3" * 64
    changed["unit_result_digest"] = "4" * 64
    assert bridge.compare_stable_classified_values(
        "unit_result", original, changed, label="transport-only"
    ) == bridge.digest(bridge.stable_classified_projection("unit_result", original))
    changed["scan_wrapper"]["scan_digest"] = "5" * 64
    with pytest.raises(bridge.PortableAdmissionError, match="stable classified"):
        bridge.compare_stable_classified_values(
            "unit_result", original, changed, label="semantic-change"
        )


def test_scan_wrapper_excludes_only_two_raw_derived_fields(frozen_rows) -> None:
    original = frozen_rows[3]["scan_wrapper"]
    changed = copy.deepcopy(original)
    changed["registry_id"] = "1" * 64
    changed["payload_sha256"] = "2" * 64
    assert bridge.portable_scan_wrapper(original) == bridge.portable_scan_wrapper(changed)
    changed["scan_digest"] = "3" * 64
    assert bridge.portable_scan_wrapper(original) != bridge.portable_scan_wrapper(changed)


def test_protected_map_and_artifact_bytes_fail_closed(tmp_path) -> None:
    observed = bridge.current_protected_hashes()
    bad = dict(observed)
    first = next(iter(bad))
    bad[first] = "0" * 64
    with pytest.raises(bridge.PortableAdmissionError, match="protected-file map"):
        bridge.verify_protected_files(bad)
    path = tmp_path / "artifact.json"
    path.write_bytes(b"preserved")
    old_root = bridge.ROOT
    # The helper accepts an absolute Path through pathlib's join semantics.
    with pytest.raises(bridge.PortableAdmissionError, match="artifact bytes"):
        bridge.require_exact_artifact_bytes(
            label="artifact", rebuilt=b"changed", preserved_path=path
        )
    assert old_root == bridge.ROOT


def test_classification_binds_all_known_raw_derived_paths(frozen_rows) -> None:
    binding = frozen_rows[2]
    result = frozen_rows[3]
    assert bridge.classify_pointer("unit_binding", "/payload_sha256") == (
        bridge.HISTORICAL_TRANSPORT
    )
    for pointer in ("/registry_identity", "/unit_binding_digest"):
        assert bridge.classify_pointer("unit_binding", pointer) == (
            bridge.DERIVED_FROM_HISTORICAL_TRANSPORT
        )
    assert bridge.classify_pointer(
        "unit_result", "/scan_wrapper/payload_sha256"
    ) == bridge.HISTORICAL_TRANSPORT
    for pointer in (
        "/unit_binding_digest",
        "/scan_wrapper/registry_id",
        "/unit_result_digest",
    ):
        assert bridge.classify_pointer("unit_result", pointer) == (
            bridge.DERIVED_FROM_HISTORICAL_TRANSPORT
        )
    assert bridge.classified_shape("unit_binding", binding)["leaf_count"] > 1000
    assert bridge.classified_shape("unit_result", result)["leaf_count"] > 1000


def test_journal_digest_and_chain_changes_are_rejected(tmp_path) -> None:
    root = tmp_path / "journal"
    journal = bridge.historical.RepairExposureUnitJournal(root)
    binding = {
        "schema_version": "test",
        "unit_index": 0,
        "unit_id": "A/seed-00",
        "unit_binding_digest": "b",
    }
    prepared = journal.prepare(binding, [])
    result = {"outcome_access": copy.deepcopy(bridge.ZERO_OUTCOME)}
    journal.commit(binding, prepared, result)
    assert journal.analyze([binding])["committed_unit_count"] == 1
    path = sorted(root.glob("*.json"))[1]
    row = json.loads(path.read_text())
    row["previous_record_digest"] = "changed"
    path.write_text(json.dumps(row))
    with pytest.raises(Exception, match="digest mismatch|chain/order"):
        journal.records()


def test_attempt_ids_and_commands_are_closed() -> None:
    assert len(bridge.ATTEMPT_IDS) == len(set(bridge.ATTEMPT_IDS)) == 3
    for ordinal, attempt_id in enumerate(bridge.ATTEMPT_IDS, start=1):
        assert f"-{ordinal:02d}-" in attempt_id
    with pytest.raises(bridge.PortableAdmissionError, match="not frozen"):
        bridge._attempt_dir("replacement-attempt")
