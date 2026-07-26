from __future__ import annotations

from pathlib import Path
import copy
import json
import pickle
import subprocess
import sys

import pytest

from recon_lite_chess.autogrowth import native_v2_fresh_discriminator as fresh
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import V2Mode
from recon_lite_chess.autogrowth.native_v2_atomic_snapshot_graph import (
    ImportStableOpaqueChessEcologyGraph,
)
from recon_lite_chess.autogrowth.native_single_graph_curriculum import (
    NativeSingleGraphConfig,
)


def _signed(value: dict, field: str) -> dict:
    value[field] = fresh.digest(value)
    return value


def test_logical_ecology_keeps_frozen_doses_and_order() -> None:
    rows = fresh.logical_specs()
    assert len(rows) == 80
    assert sum(row["phase"] == "prefix" and row["a_outcome"] for row in rows) == 32
    assert sum(row["phase"] == "prefix" and not row["a_outcome"] for row in rows) == 32
    assert sum(row["visible_family"] == "suffix_spurious" for row in rows) == 8
    assert sum(row["visible_family"] == "suffix_planted" for row in rows) == 8


def test_arm_mode_contract_uses_enum_values() -> None:
    source = Path(fresh.__file__).read_text()
    assert '"A": V2Mode.PROSPECTIVE.value' in source
    assert '"B": V2Mode.LEGACY.value' in source
    assert '"C": V2Mode.PROSPECTIVE.value' in source
    assert V2Mode.LEGACY.value != V2Mode.PROSPECTIVE.value


def test_bound_preflight_requires_exact_receipt_and_coverage() -> None:
    manifest = {"manifest_digest": "manifest", "experiment_id": "test-experiment"}
    receipt = {
        "schema_version": "test",
        "manifest_digest": "manifest",
        "coverage": {"seed_count": 2, "arm_count": 3, "artifact_count": 6, "complete": True},
        "verification_rows": [
            {"seed_ordinal": seed, "arm": arm}
            for seed in (0, 1) for arm in fresh.ARMS
        ],
        "outcome_access": {"count": 0, "event_ids": []},
    }
    receipt["receipt_digest"] = fresh.canonical_digest(receipt)
    authorization = {
        "experiment_id": "test-experiment",
        "registry_package_hash": "registry",
        "expected_global_preflight": {
            "receipt_digest": receipt["receipt_digest"],
            "snapshot_manifest_digest": "manifest",
            "registry_package_hash": "registry",
        },
    }
    authorization["authorization_digest"] = fresh.digest(authorization)
    fresh.verify_bound_preflight_authorization(
        receipt=receipt,
        snapshot_manifest=manifest,
        authorization=authorization,
        expected_experiment_id="test-experiment",
        expected_seed_ordinals=(0, 1),
    )
    wrong = copy.deepcopy(authorization)
    wrong["expected_global_preflight"]["receipt_digest"] = "0" * 64
    wrong["authorization_digest"] = fresh.digest({
        key: value for key, value in wrong.items() if key != "authorization_digest"
    })
    with pytest.raises(fresh.FreshScientificIntegrityError, match="exact binding"):
        fresh.verify_bound_preflight_authorization(
            receipt=receipt,
            snapshot_manifest=manifest,
            authorization=wrong,
            expected_experiment_id="test-experiment",
            expected_seed_ordinals=(0, 1),
        )


def test_truthful_environment_requires_unforgeable_runner_capability() -> None:
    old = json.loads((fresh.ROOT / fresh.OLD_PACKAGE_DIR / "ecology_manifest.json").read_text())
    row = old["rows"][0]
    transition = fresh.transition_manifest(row["a_fen"], row["move_uci"])
    transition = {"transition_id": "one", **transition}
    manifest = {
        "schema_version": "test-environment.v1",
        "experiment_id": "test",
        "ecology_digest": "test",
        "outcome_capability_required": True,
        "completion_terminal_identity": "mate",
        "transition_count": 1,
        "transitions": [transition],
    }
    manifest["environment_digest"] = fresh.digest(manifest)
    environment = fresh.FrozenTruthfulEnvironment(manifest)
    assert set(environment.outcome_blind("one")) == {
        "transition_id", "predecessor_fen", "move_uci"
    }
    with pytest.raises(fresh.OutcomeCapabilityError):
        environment._execute(object(), "one", transition["move_uci"])


def test_import_stable_graph_restores_in_fresh_process(tmp_path: Path) -> None:
    graph = ImportStableOpaqueChessEcologyGraph(
        config=NativeSingleGraphConfig(max_ticks=1)
    )
    payload = tmp_path / "graph.pkl"
    payload.write_bytes(pickle.dumps(graph, protocol=pickle.HIGHEST_PROTOCOL))
    code = (
        "import pickle,sys; x=pickle.load(open(sys.argv[1],'rb')); "
        "print(type(x).__module__ + ':' + type(x).__name__)"
    )
    observed = subprocess.run(
        [sys.executable, "-c", code, str(payload)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert observed == (
        "recon_lite_chess.autogrowth.native_v2_atomic_snapshot_graph:"
        "ImportStableOpaqueChessEcologyGraph"
    )


def test_bound_path_supports_isolated_transaction_directories(tmp_path: Path) -> None:
    path = tmp_path / "carrier.json"
    assert fresh._bound_path(path) == path.resolve().as_posix()
    assert fresh._resolve_bound_path(fresh._bound_path(path)) == path.resolve()


def test_protected_boundary_is_byte_exact() -> None:
    observed = fresh.verify_protected_boundary()
    assert observed
    assert all(len(value) == 64 for value in observed.values())


def test_future_commands_are_separate_from_design_freeze() -> None:
    source = Path(fresh.__file__).read_text()
    freeze_body = source.split("def freeze_predata_design", 1)[1].split(
        "def _registry_manifest", 1
    )[0]
    assert "run_canonical_discovery" not in freeze_body
    assert "execute_fresh_seed_atomically" not in freeze_body
    assert "_assert_predata_outputs_absent()" in freeze_body


def test_canary_machine_evidence_if_present() -> None:
    path = fresh.ROOT / fresh.TOY_CANARY_PATH
    if not path.exists():
        pytest.skip("retired canary is executed after source-focused tests")
    value = json.loads(path.read_text())
    unsigned = {key: item for key, item in value.items() if key != "canary_digest"}
    assert value["canary_digest"] == fresh.digest(unsigned)
    assert value["snapshot_artifact_count"] == 96
    assert value["first_corruption"]["rejected"]
    assert value["last_corruption"]["rejected"]
    assert len(value["stage_failures"]) == 17
    assert all(item["live_state_byte_identical"] for item in value["stage_failures"])
    assert value["success_transaction"]["journal_only_reconstruction_byte_identical"]
    assert value["fresh_process_restoration"]["passed"]
    assert value["outcome_access_law"]["passed"]


def test_no_fresh_outputs_exist_before_source_freeze() -> None:
    if (fresh.ROOT / fresh.OUTER_MANIFEST_PATH).exists():
        pytest.skip("pre-data design already frozen")
    fresh._assert_predata_outputs_absent()
