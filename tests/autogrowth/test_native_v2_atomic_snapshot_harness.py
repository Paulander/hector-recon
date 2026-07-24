from __future__ import annotations

from pathlib import Path
import base64
import copy
import gzip
import json
import pickle
import subprocess
import sys

import pytest

from recon_lite_chess.autogrowth.native_single_graph_curriculum import (
    NativeSingleGraphConfig,
)
from recon_lite_chess.autogrowth.native_v2_atomic_snapshot_graph import (
    ImportStableOpaqueChessEcologyGraph,
)
from recon_lite_chess.autogrowth.native_v2_atomic_snapshot_harness import (
    ARMS,
    AtomicSnapshotIntegrityError,
    DurableHashJournal,
    InjectedHarnessFailure,
    NonResumableJournal,
    OutcomeAccessGuard,
    PickleSemanticCodec,
    SyntheticTriArmAdapter,
    atomic_json,
    canonical_digest,
    execute_seed_atomically,
    global_all_arm_preflight,
    persist_arm_snapshots_once,
    sha256_bytes,
    synthetic_arm_factory,
)


def _persist(
    root: Path,
    *,
    seeds: tuple[int, ...] = (0,),
    factory=synthetic_arm_factory,
) -> tuple[dict, PickleSemanticCodec]:
    codec = PickleSemanticCodec()
    manifest = persist_arm_snapshots_once(
        seed_ordinals=seeds,
        arm_factory=factory,
        package_root=root,
        codec=codec,
        experiment_id="synthetic-preflight",
        source_manifest_digest="synthetic-source-manifest",
    )
    return manifest, codec


def _rewrite_manifest(root: Path, manifest: dict) -> None:
    unsigned = {k: v for k, v in manifest.items() if k != "manifest_digest"}
    manifest["manifest_digest"] = canonical_digest(unsigned)
    atomic_json(root / "arm_snapshot_manifest.json", manifest, replace=True)


def _replace_entry_transport(
    root: Path,
    manifest: dict,
    index: int,
    value,
    codec: PickleSemanticCodec,
) -> None:
    entry = manifest["entries"][index]
    raw = codec.dumps(value)
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    (root / entry["path"]).write_bytes(compressed)
    entry.update({
        "raw_sha256": sha256_bytes(raw),
        "raw_size": len(raw),
        "compressed_sha256": sha256_bytes(compressed),
        "compressed_size": len(compressed),
        "compressed_reference_b64": base64.b64encode(compressed).decode("ascii"),
    })
    _rewrite_manifest(root, manifest)


def _preflight(
    root: Path,
    codec: PickleSemanticCodec,
    seeds: tuple[int, ...],
    guard: OutcomeAccessGuard | None = None,
):
    guard = guard or OutcomeAccessGuard()
    return global_all_arm_preflight(
        manifest_path=root / "arm_snapshot_manifest.json",
        package_root=root,
        receipt_path=root / "global_preflight_receipt.json",
        failure_path=root / "global_preflight_failure.json",
        codec=codec,
        guard=guard,
        required_seed_ordinals=seeds,
    )


def _execution_authority() -> tuple[dict, dict]:
    manifest = {"manifest_digest": "snapshot-manifest"}
    receipt = {
        "schema_version": "native_v2_global_preflight_receipt.v1",
        "manifest_digest": "snapshot-manifest",
        "coverage": {"complete": True},
        "outcome_access": {"count": 0, "event_ids": []},
    }
    receipt["receipt_digest"] = canonical_digest(receipt)
    return manifest, receipt


def test_byte_different_semantically_equal_pickles_pass(tmp_path: Path) -> None:
    def left_factory(seed: int):
        arms = synthetic_arm_factory(seed)
        for arm in arms.values():
            arm.layout = {"alpha": 1, "beta": 2}
        return arms

    def right_factory(seed: int):
        arms = synthetic_arm_factory(seed)
        for arm in arms.values():
            arm.layout = {"beta": 2, "alpha": 1}
        return arms

    left, codec = _persist(tmp_path / "left", factory=left_factory)
    right, _ = _persist(tmp_path / "right", factory=right_factory)
    assert [item["semantic_identity_digest"] for item in left["entries"]] == [
        item["semantic_identity_digest"] for item in right["entries"]
    ]
    assert [item["raw_sha256"] for item in left["entries"]] != [
        item["raw_sha256"] for item in right["entries"]
    ]
    left_receipt, _ = _preflight(tmp_path / "left", codec, (0,))
    right_receipt, _ = _preflight(tmp_path / "right", codec, (0,))
    assert left_receipt["coverage"]["artifact_count"] == 3
    assert right_receipt["coverage"]["artifact_count"] == 3


def test_semantic_drift_reports_precise_json_pointer(tmp_path: Path) -> None:
    manifest, codec = _persist(tmp_path)
    entry = manifest["entries"][0]
    value = codec.loads(gzip.decompress((tmp_path / entry["path"]).read_bytes()))
    value.source_state_identity = "foreign-state"
    _replace_entry_transport(tmp_path, manifest, 0, value, codec)
    guard = OutcomeAccessGuard()
    with pytest.raises(AtomicSnapshotIntegrityError, match="semantic drift"):
        _preflight(tmp_path, codec, (0,), guard)
    failure = json.loads((tmp_path / "global_preflight_failure.json").read_text())
    assert failure["classification"] == "semantic drift"
    paths = {row["path"] for row in failure["canonical_json_pointer_differences"]}
    assert "/source_state_identity" in paths
    assert failure["expected_continuation_digest"] != failure[
        "observed_continuation_digest"
    ]
    assert guard.count == 0


def test_restore_failure_is_classified_and_outcome_free(tmp_path: Path) -> None:
    manifest, codec = _persist(tmp_path)
    entry = manifest["entries"][0]
    raw = b"not-a-pickle"
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    (tmp_path / entry["path"]).write_bytes(compressed)
    entry.update({
        "raw_sha256": sha256_bytes(raw),
        "raw_size": len(raw),
        "compressed_sha256": sha256_bytes(compressed),
        "compressed_size": len(compressed),
        "compressed_reference_b64": base64.b64encode(compressed).decode("ascii"),
    })
    _rewrite_manifest(tmp_path, manifest)
    guard = OutcomeAccessGuard()
    with pytest.raises(AtomicSnapshotIntegrityError, match="restore failure"):
        _preflight(tmp_path, codec, (0,), guard)
    failure = json.loads((tmp_path / "global_preflight_failure.json").read_text())
    assert failure["classification"] == "restore failure"
    assert failure["observed_raw_sha256"] == sha256_bytes(raw)
    assert guard.count == 0


@pytest.mark.parametrize("entry_index", [0, 95])
def test_first_or_last_of_96_corruption_fails_before_outcomes(
    tmp_path: Path,
    entry_index: int,
) -> None:
    manifest, codec = _persist(tmp_path, seeds=tuple(range(32)))
    entry = manifest["entries"][entry_index]
    path = tmp_path / entry["path"]
    payload = bytearray(path.read_bytes())
    payload[-1] ^= 0x01
    path.write_bytes(payload)
    guard = OutcomeAccessGuard()
    with pytest.raises(AtomicSnapshotIntegrityError, match="transport corruption"):
        _preflight(tmp_path, codec, tuple(range(32)), guard)
    failure = json.loads((tmp_path / "global_preflight_failure.json").read_text())
    assert failure["seed_ordinal"] == entry["seed_ordinal"]
    assert failure["arm"] == entry["arm"]
    assert failure["first_differing_byte_offset"] == len(payload) - 1
    assert failure["observed_compressed_sha256"] == sha256_bytes(payload)
    assert failure["outcome_access"]["count"] == 0
    assert guard.count == 0


@pytest.mark.parametrize(
    ("field", "replacement", "pointer"),
    [
        ("candidate_population_identity", "foreign-candidate", "/candidate_population_identity"),
        ("topology_identity", "foreign-topology", "/topology_identity"),
        ("polarity", "NEGATIVE", "/polarity_manifest/cell"),
        ("source_organism_identity", "foreign-source", "/source_organism_identity"),
        ("source_state_identity", "foreign-state", "/source_state_identity"),
        ("mode", "legacy", "/mode"),
    ],
)
def test_candidate_topology_polarity_or_source_swap_fails(
    tmp_path: Path,
    field: str,
    replacement: str,
    pointer: str,
) -> None:
    manifest, codec = _persist(tmp_path)
    entry = manifest["entries"][0]
    value = codec.loads(gzip.decompress((tmp_path / entry["path"]).read_bytes()))
    setattr(value, field, replacement)
    _replace_entry_transport(tmp_path, manifest, 0, value, codec)
    with pytest.raises(AtomicSnapshotIntegrityError, match="semantic drift"):
        _preflight(tmp_path, codec, (0,))
    failure = json.loads((tmp_path / "global_preflight_failure.json").read_text())
    paths = {row["path"] for row in failure["canonical_json_pointer_differences"]}
    assert pointer in paths


def test_swapped_arm_artifact_fails_semantically(tmp_path: Path) -> None:
    manifest, codec = _persist(tmp_path)
    first, second = manifest["entries"][0], manifest["entries"][1]
    for key in (
        "path", "raw_sha256", "raw_size", "compressed_sha256",
        "compressed_size", "compressed_reference_b64",
    ):
        first[key], second[key] = second[key], first[key]
    _rewrite_manifest(tmp_path, manifest)
    with pytest.raises(AtomicSnapshotIntegrityError, match="semantic drift"):
        _preflight(tmp_path, codec, (0,))


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "foreign"])
def test_missing_duplicate_or_foreign_member_fails(
    tmp_path: Path,
    mutation: str,
) -> None:
    manifest, codec = _persist(tmp_path)
    if mutation == "missing":
        manifest["entries"].pop()
    elif mutation == "duplicate":
        manifest["entries"].append(copy.deepcopy(manifest["entries"][0]))
    else:
        manifest["entries"][0]["seed_ordinal"] = 99
    _rewrite_manifest(tmp_path, manifest)
    guard = OutcomeAccessGuard()
    with pytest.raises(AtomicSnapshotIntegrityError):
        _preflight(tmp_path, codec, (0,), guard)
    assert guard.count == 0


@pytest.mark.parametrize("field", ["seed_ordinals", "arms", "codec_identity"])
def test_manifest_header_or_codec_swap_fails_before_outcomes(
    tmp_path: Path,
    field: str,
) -> None:
    manifest, codec = _persist(tmp_path)
    manifest[field] = {
        "seed_ordinals": [0, 1],
        "arms": ["B", "A", "C"],
        "codec_identity": "foreign-codec",
    }[field]
    _rewrite_manifest(tmp_path, manifest)
    guard = OutcomeAccessGuard()
    with pytest.raises(AtomicSnapshotIntegrityError, match="semantic drift"):
        _preflight(tmp_path, codec, (0,), guard)
    failure = json.loads((tmp_path / "global_preflight_failure.json").read_text())
    paths = {row["path"] for row in failure["canonical_json_pointer_differences"]}
    assert f"/{field}" in paths or any(
        path.startswith(f"/{field}/") for path in paths
    )
    assert guard.count == 0


def test_forensic_transport_reference_tamper_fails_before_restore(
    tmp_path: Path,
) -> None:
    manifest, codec = _persist(tmp_path)
    entry = manifest["entries"][0]
    reference = bytearray(base64.b64decode(entry["compressed_reference_b64"]))
    reference[-1] ^= 0x01
    entry["compressed_reference_b64"] = base64.b64encode(reference).decode("ascii")
    _rewrite_manifest(tmp_path, manifest)
    with pytest.raises(AtomicSnapshotIntegrityError, match="transport corruption"):
        _preflight(tmp_path, codec, (0,))
    failure = json.loads((tmp_path / "global_preflight_failure.json").read_text())
    assert failure["detail"] == "forensic transport reference differs from manifest"
    assert failure["observed_compressed_sha256"] == sha256_bytes(reference)


def test_semantic_identity_digest_tamper_fails_before_acceptance(
    tmp_path: Path,
) -> None:
    manifest, codec = _persist(tmp_path)
    manifest["entries"][0]["semantic_identity_digest"] = "0" * 64
    _rewrite_manifest(tmp_path, manifest)
    with pytest.raises(AtomicSnapshotIntegrityError, match="semantic drift"):
        _preflight(tmp_path, codec, (0,))
    failure = json.loads((tmp_path / "global_preflight_failure.json").read_text())
    assert failure["canonical_json_pointer_differences"][0]["path"] == (
        "/semantic_identity_digest"
    )


def test_complete_96_preflight_receipt_has_zero_outcomes(tmp_path: Path) -> None:
    _, codec = _persist(tmp_path, seeds=tuple(range(32)))
    guard = OutcomeAccessGuard()
    receipt, restored = _preflight(tmp_path, codec, tuple(range(32)), guard)
    assert receipt["coverage"] == {
        "seed_count": 32,
        "arm_count": 3,
        "artifact_count": 96,
        "complete": True,
    }
    assert len(restored) == 96
    assert receipt["outcome_access"] == {"count": 0, "event_ids": []}
    assert guard.count == 0


@pytest.mark.parametrize("stage", ["open", "mint", "consume", "invariant"])
@pytest.mark.parametrize("arm", ARMS)
def test_failure_at_any_arm_stage_cannot_advance_live_state(
    tmp_path: Path,
    stage: str,
    arm: str,
) -> None:
    live = synthetic_arm_factory(0)
    adapter = SyntheticTriArmAdapter(fail_stage=stage, fail_arm=arm)
    before = {key: value.semantic_manifest() for key, value in live.items()}
    manifest, receipt = _execution_authority()
    guard = OutcomeAccessGuard()
    journal = DurableHashJournal(tmp_path / "journal")
    with pytest.raises(InjectedHarnessFailure, match=stage):
        execute_seed_atomically(
            seed=0, live_arms=live,
            rows=({"row_id": "row-0", "outcomes": {a: True for a in ARMS}},),
            adapter=adapter, journal=journal, guard=guard,
            preflight_receipt=receipt, snapshot_manifest=manifest,
        )
    assert {key: value.semantic_manifest() for key, value in live.items()} == before
    with pytest.raises(NonResumableJournal):
        journal.next_seed((0, 1))


@pytest.mark.parametrize(
    "kind", ["PREPARED", "TRI_ARM_ROW_COMMITTED", "COMMITTED"]
)
def test_durable_commit_failure_is_all_or_none(
    tmp_path: Path,
    kind: str,
) -> None:
    live = synthetic_arm_factory(0)
    before = {key: value.semantic_manifest() for key, value in live.items()}
    manifest, receipt = _execution_authority()
    journal = DurableHashJournal(tmp_path / "journal", fail_on_kind=kind)
    with pytest.raises(InjectedHarnessFailure, match="durable_commit"):
        execute_seed_atomically(
            seed=0, live_arms=live,
            rows=({"row_id": "row-0", "outcomes": {a: True for a in ARMS}},),
            adapter=SyntheticTriArmAdapter(), journal=journal,
            guard=OutcomeAccessGuard(), preflight_receipt=receipt,
            snapshot_manifest=manifest,
        )
    assert {key: value.semantic_manifest() for key, value in live.items()} == before


def test_dangling_prepared_is_permanently_nonresumable(tmp_path: Path) -> None:
    journal = DurableHashJournal(tmp_path / "journal")
    journal.prepare_seed(
        0, {"state": "initial"}, {"count": 0, "event_ids": []}
    )
    with pytest.raises(NonResumableJournal, match="dangling PREPARED"):
        journal.next_seed((0, 1))


def test_committed_seed_resumes_only_at_next_seed(tmp_path: Path) -> None:
    live = synthetic_arm_factory(0)
    manifest, receipt = _execution_authority()
    journal = DurableHashJournal(tmp_path / "journal")
    result = execute_seed_atomically(
        seed=0, live_arms=live,
        rows=(
            {"row_id": "row-0", "outcomes": {a: True for a in ARMS}},
            {"row_id": "row-1", "outcomes": {a: False for a in ARMS}},
        ),
        adapter=SyntheticTriArmAdapter(), journal=journal,
        guard=OutcomeAccessGuard(), preflight_receipt=receipt,
        snapshot_manifest=manifest,
    )
    assert result["journal_next_seed"] == 1
    assert journal.next_seed((0, 1)) == 1
    assert journal.restored_outcome_guard().manifest() == result["outcome_access"]
    assert {arm.value for arm in live.values()} == {0}
    kinds = [row["kind"] for row in journal._records()]
    assert kinds == [
        "PREPARED", "TRI_ARM_ROW_COMMITTED",
        "TRI_ARM_ROW_COMMITTED", "COMMITTED",
    ]


def test_import_stable_graph_instance_restores_in_fresh_process(
    tmp_path: Path,
) -> None:
    graph = ImportStableOpaqueChessEcologyGraph(
        config=NativeSingleGraphConfig(max_ticks=1)
    )
    payload_path = tmp_path / "stable_graph.pkl"
    payload = pickle.dumps(graph, protocol=pickle.HIGHEST_PROTOCOL)
    payload_path.write_bytes(payload)
    assert b"native_v2_atomic_snapshot_graph" in payload
    code = (
        "import pickle,sys; "
        "x=pickle.load(open(sys.argv[1],'rb')); "
        "print(type(x).__module__ + ':' + type(x).__name__)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code, str(payload_path)],
        check=True, capture_output=True, text=True,
    )
    assert completed.stdout.strip() == (
        "recon_lite_chess.autogrowth.native_v2_atomic_snapshot_graph:"
        "ImportStableOpaqueChessEcologyGraph"
    )


def test_snapshot_factory_called_once_per_seed(tmp_path: Path) -> None:
    calls: list[int] = []

    def factory(seed: int):
        calls.append(seed)
        return synthetic_arm_factory(seed)

    persist_arm_snapshots_once(
        seed_ordinals=(0, 1, 2), arm_factory=factory,
        package_root=tmp_path, codec=PickleSemanticCodec(),
        experiment_id="once", source_manifest_digest="source",
    )
    assert calls == [0, 1, 2]


def test_journal_rejects_skipped_seed(tmp_path: Path) -> None:
    journal = DurableHashJournal(tmp_path / "journal")
    with pytest.raises(AtomicSnapshotIntegrityError, match="expected seed 0"):
        journal.prepare_seed(
            1, {"state": "skipped"}, {"count": 0, "event_ids": []}
        )
