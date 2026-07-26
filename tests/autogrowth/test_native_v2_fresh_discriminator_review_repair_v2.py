from __future__ import annotations

from pathlib import Path
import copy
import json
import pickle
import subprocess
import sys

import pytest

from recon_lite_chess.autogrowth import native_v2_fresh_discriminator_review_repair_v2 as fresh
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



def _engagement_seed(
    ordinal: int,
    *,
    c_break: bool = True,
    missing_clearing: int = 0,
) -> dict:
    mature = {"hypothesis": {"structural_state": fresh.StemCellState.MATURE.name}}
    clearing = {
        "contradiction_event_count": 2,
        "decision_bearing_contradiction_count": 1,
        "graph_clearing_count": 1 - missing_clearing,
        "missing_graph_clearing_count": missing_clearing,
        "selected_spurious_B_checked_count": 1,
        "all_required_graph_clearings_emitted": missing_clearing == 0,
        "events": [],
        "missing_events": [],
    }
    clearing["clearing_summary_digest"] = fresh.digest(clearing)
    value = {
        "seed_ordinal": ordinal,
        "genome_seed": 10_000 + ordinal,
        "initial_states": {"A": {}, "B": {"b": mature}, "C": {}},
        "immediate_authority_cell_ids": {"A": [], "B": ["b"], "C": []},
        "target_final_states": {
            "A": {
                "planted": {
                    "support": 4,
                    "contradictions": 0,
                    "prospectively_certified": True,
                },
                "selected_spurious": {"contradictions": 1},
            },
            "B": {"planted": None, "selected_spurious": None},
            "C": {
                "planted": {"contradictions": 4 if c_break else 3},
                "selected_spurious": None,
            },
        },
        "clearing_summary": clearing,
        "endpoints": {
            "A": {
                "false_deployment_authority": 0,
                "selected_spurious_attributable_false_authority": 0,
                "planted_authority_coverage": 1,
            },
            "B": {
                "false_deployment_authority": 1,
                "selected_spurious_attributable_false_authority": 1,
                "planted_authority_coverage": 1,
            },
            "C": {
                "false_deployment_authority": 0,
                "selected_spurious_attributable_false_authority": 0,
                "planted_authority_coverage": 0,
            },
        },
    }
    value["seed_result_digest"] = fresh.digest(value)
    return value


def test_complete_engagement_requires_24_C_association_breaks() -> None:
    twenty_three = [
        _engagement_seed(index, c_break=index < 23) for index in range(32)
    ]
    failed = fresh.adjudicate_committed_results(twenty_three)
    assert failed["engagement"]["C_planted_contradiction_dose_count"] == 23
    assert not failed["engagement"]["C_dose_passed"]
    assert not failed["both_primary_pass"]

    twenty_four = [
        _engagement_seed(index, c_break=index < 24) for index in range(32)
    ]
    passed = fresh.adjudicate_committed_results(twenty_four)
    assert passed["engagement"]["C_planted_contradiction_dose_count"] == 24
    assert passed["engagement"]["C_dose_passed"]
    assert passed["engagement"]["passed"]


def test_complete_engagement_fails_when_C_never_breaks() -> None:
    result = fresh.adjudicate_committed_results([
        _engagement_seed(index, c_break=False) for index in range(32)
    ])
    assert result["engagement"]["C_planted_contradiction_dose_count"] == 0
    assert not result["engagement"]["passed"]
    assert result["verdict"] == "mechanism_contrast_starvation"


def test_complete_engagement_checks_every_required_graph_clearing() -> None:
    values = [_engagement_seed(index) for index in range(32)]
    values[17] = _engagement_seed(17, missing_clearing=1)
    result = fresh.adjudicate_committed_results(values)
    assert result["engagement"]["missing_graph_clearing_count"] == 1
    assert not result["engagement"]["clearing_passed"]
    assert not result["both_primary_pass"]


def _clearing_record(
    cell_id: str,
    receipt_id: str,
    *,
    emitted: bool,
) -> dict:
    return {
        "production_classification": {"available_cell_ids": [cell_id]},
        "graph_authority_emission": {
            "contradiction_cell_ids": [cell_id],
            "graph_revocation_ids": [cell_id] if emitted else [],
        },
        "grounded_receipt": {"receipt_id": receipt_id},
    }


def test_multiple_contradictions_are_checked_individually() -> None:
    targets = {
        "planted": {"cell_id": "planted"},
        "selected_spurious": {"cell_id": "spurious"},
    }
    neutral = {
        "production_classification": {"available_cell_ids": []},
        "graph_authority_emission": {
            "contradiction_cell_ids": [],
            "graph_revocation_ids": [],
        },
        "grounded_receipt": {"receipt_id": "neutral"},
    }
    rows = (
        {
            "row_id": "one",
            "arms": {
                "A": _clearing_record("planted", "r1", emitted=True),
                "B": _clearing_record("spurious", "r2", emitted=True),
                "C": neutral,
            },
        },
        {
            "row_id": "two",
            "arms": {
                "A": neutral,
                "B": _clearing_record("spurious", "r3", emitted=False),
                "C": neutral,
            },
        },
    )
    result = fresh.summarize_clearing_events(rows, targets)
    assert result["decision_bearing_contradiction_count"] == 3
    assert result["graph_clearing_count"] == 2
    assert result["missing_graph_clearing_count"] == 1
    assert result["selected_spurious_B_checked_count"] == 2
    assert not result["all_required_graph_clearings_emitted"]


@pytest.mark.parametrize(
    ("committed_count", "next_seed"),
    ((1, 1), (16, 16), (32, None)),
)
def test_command_restart_plan_skips_only_committed_seeds(
    tmp_path: Path, committed_count: int, next_seed: int | None
) -> None:
    journal = fresh.DurableHashJournal(tmp_path / "journal")
    guard = {"count": 0, "event_ids": []}
    for seed in range(committed_count):
        journal.prepare_seed(seed, {}, guard)
        journal.commit_seed(seed, {}, guard)
    plan = fresh.restart_execution_plan(journal)
    assert plan["completed_ordinals"] == list(range(committed_count))
    assert plan["next_unfinished_seed"] == next_seed
    assert not set(plan["completed_ordinals"]).intersection(
        plan["remaining_ordinals"]
    )
    if next_seed is None:
        assert plan["remaining_ordinals"] == []
    else:
        assert plan["remaining_ordinals"][0] == next_seed


def test_seed_journal_requires_exact_rows_and_48_ordered_reads() -> None:
    row_ids = [f"row-{index:02d}" for index in range(16)]
    records = []
    previous = []
    records.append({
        "kind": "PREPARED",
        "seed_ordinal": 0,
        "payload": {"outcome_access": {"count": 0, "event_ids": []}},
    })
    count = 0
    event_ids = []
    for row_id in row_ids:
        for arm in fresh.ARMS:
            count += 1
            event_id = f"seed-00:{row_id}:{arm}"
            event_ids.append(event_id)
            records.append({
                "kind": "OUTCOME_ACCESSED",
                "seed_ordinal": 0,
                "payload": {
                    "event_id": event_id,
                    "next_guard_manifest": {
                        "count": count,
                        "event_ids": list(event_ids),
                    },
                },
            })
        records.append({
            "kind": "TRI_ARM_ROW_COMMITTED",
            "seed_ordinal": 0,
            "payload": {"row_id": row_id},
        })
    records.append({
        "kind": "COMMITTED",
        "seed_ordinal": 0,
        "payload": {"outcome_access": {"count": count, "event_ids": event_ids}},
    })
    commits, reads, _committed = fresh._validate_seed_journal_sequence(
        records, seed=0, row_ids=row_ids
    )
    assert len(commits) == 16
    assert len(reads) == 48

    reordered = copy.deepcopy(records)
    first = next(
        row for row in reordered if row["kind"] == "TRI_ARM_ROW_COMMITTED"
    )
    first["payload"]["row_id"] = row_ids[1]
    with pytest.raises(fresh.FreshScientificIntegrityError, match="row order"):
        fresh._validate_seed_journal_sequence(
            reordered, seed=0, row_ids=row_ids
        )



def test_two_distinct_starts_reaching_one_result_are_rejected() -> None:
    transitions = []
    for index in range(160):
        result_index = 0 if index in {0, 1} else index
        transitions.append({
            "transition_id": f"t-{index:03d}",
            "predecessor_fen": f"start-{index:03d}",
            "successor_fen": f"result-{result_index:03d}",
            "physical_transition_digest": f"transition-{index:03d}",
        })
    ecology = {"transitions": transitions}
    validation = {"physical_fingerprints": [
        f"stable-{index:03d}" for index in range(160)
    ]}
    excluded = {
        "excluded_all_position_fens": [],
        "excluded_transition_digests": [],
        "excluded_stable_interaction_ids": [],
        "superseded_overlap_comparison": {},
    }
    with pytest.raises(
        fresh.FreshScientificIntegrityError,
        match="reuses a board position",
    ):
        fresh.verify_physical_freshness(ecology, validation, excluded)


def _signed_exposure() -> dict:
    value = {
        "admitted": True,
        "outcome_access": {"count": 0, "event_ids": []},
        "qualifying_seed_count": 24,
        "parity_rows": [{"ordinal": 31, "arm": "C", "equal": True}],
        "prefix_candidate_verification": {"candidate": "exact"},
    }
    value["exposure_digest"] = fresh.digest(value)
    return value


def _signed_execution() -> dict:
    value = {"complete_snapshot_identity": "all-96", "admitted": True}
    value["execution_manifest_digest"] = fresh.digest(value)
    return value


@pytest.mark.parametrize(
    "changed_path",
    ("snapshot_31_C", "exposure_counts", "parity", "candidate_metadata"),
)
def test_immediate_preoutcome_reconstruction_rejects_changed_inputs(
    monkeypatch: pytest.MonkeyPatch,
    changed_path: str,
) -> None:
    exposure = _signed_exposure()
    execution = _signed_execution()
    rebuilt_exposure = copy.deepcopy(exposure)
    rebuilt_execution = copy.deepcopy(execution)
    if changed_path == "snapshot_31_C":
        rebuilt_execution["complete_snapshot_identity"] = "changed-31-C"
        rebuilt_execution["execution_manifest_digest"] = fresh.digest({
            key: value for key, value in rebuilt_execution.items()
            if key != "execution_manifest_digest"
        })
    elif changed_path == "exposure_counts":
        rebuilt_exposure["qualifying_seed_count"] = 23
    elif changed_path == "parity":
        rebuilt_exposure["parity_rows"][0]["equal"] = False
    else:
        rebuilt_exposure["prefix_candidate_verification"]["candidate"] = "changed"
    if changed_path != "snapshot_31_C":
        rebuilt_exposure["exposure_digest"] = fresh.digest({
            key: value for key, value in rebuilt_exposure.items()
            if key != "exposure_digest"
        })

    def fake_load(path: Path) -> dict:
        if path == fresh.ROOT / fresh.EXPOSURE_PATH:
            return copy.deepcopy(exposure)
        if path == fresh.ROOT / fresh.EXECUTION_MANIFEST_PATH:
            return copy.deepcopy(execution)
        if path == fresh.ROOT / fresh.ECOLOGY_MANIFEST_PATH:
            return {"ecology": "frozen"}
        raise AssertionError(path)

    monkeypatch.setattr(fresh, "verify_outer_manifest", lambda _phase: {"outer": "frozen"})
    monkeypatch.setattr(fresh, "_load_json", fake_load)
    monkeypatch.setattr(fresh, "_load_prefix_manifest", lambda: {"prefix": "frozen"})
    monkeypatch.setattr(fresh, "_validated_snapshot_manifest", lambda: {"manifest": "frozen"})
    monkeypatch.setattr(
        fresh,
        "global_all_arm_preflight",
        lambda **kwargs: ({"receipt": "zero-read"}, {"all": "96"}),
    )
    monkeypatch.setattr(
        fresh,
        "_reconstruct_exposure_value",
        lambda **kwargs: copy.deepcopy(rebuilt_exposure),
    )
    monkeypatch.setattr(
        fresh,
        "_build_execution_manifest",
        lambda **kwargs: copy.deepcopy(rebuilt_execution),
    )
    with pytest.raises(fresh.FreshScientificIntegrityError):
        fresh.reconstruct_admission_before_outcomes()


def test_immediate_preoutcome_reconstruction_rejects_changed_prefix_before_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exposure = _signed_exposure()
    execution = _signed_execution()
    def fake_load(path: Path) -> dict:
        if path == fresh.ROOT / fresh.EXPOSURE_PATH:
            return copy.deepcopy(exposure)
        if path == fresh.ROOT / fresh.EXECUTION_MANIFEST_PATH:
            return copy.deepcopy(execution)
        raise AssertionError(path)
    monkeypatch.setattr(fresh, "verify_outer_manifest", lambda _phase: {})
    monkeypatch.setattr(fresh, "_load_json", fake_load)
    monkeypatch.setattr(
        fresh,
        "_load_prefix_manifest",
        lambda: (_ for _ in ()).throw(
            fresh.FreshScientificIntegrityError("prefix manifest digest mismatch")
        ),
    )
    with pytest.raises(fresh.FreshScientificIntegrityError, match="prefix manifest"):
        fresh.reconstruct_admission_before_outcomes()



class _FakeState:
    def __init__(
        self,
        cell_id: str,
        *,
        support: int = 0,
        successes: int = 0,
        contradictions: int = 0,
        certified: bool = False,
    ) -> None:
        self.cell_id = cell_id
        self.support = support
        self.successes = successes
        self.contradictions = contradictions
        self.prospectively_certified = certified

    def manifest(self) -> dict:
        return {
            "cell_id": self.cell_id,
            "support": self.support,
            "successes": self.successes,
            "contradictions": self.contradictions,
            "prospectively_certified": self.prospectively_certified,
            "hypothesis": {"structural_state": "TRIAL"},
        }


class _FakeEmission:
    def __init__(self, value: dict) -> None:
        self.value = copy.deepcopy(value)

    def manifest(self) -> dict:
        return copy.deepcopy(self.value)


class _FakeWrapper:
    def __init__(
        self,
        arm: str,
        continuation: str,
        ordinal: int,
        emissions: dict[str, dict] | None = None,
    ) -> None:
        self.arm = arm
        self._continuation = continuation
        self.next_expected_ordinal = ordinal
        self.states = {"p": _FakeState("p"), "s": _FakeState("s")}
        self.emissions = {
            key: _FakeEmission(value) for key, value in (emissions or {}).items()
        }

    def continuation_digest(self) -> str:
        return self._continuation


def _reconstruction_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[object, list[dict], dict, dict, dict, dict]:
    row_ids = [f"row-{index:02d}" for index in range(16)]
    targets = {
        "planted": {"cell_id": "p"},
        "selected_spurious": {"cell_id": "s"},
    }
    baseline = {
        (0, arm): _FakeWrapper(arm, f"{arm}-continuation-00", 0)
        for arm in fresh.ARMS
    }
    final_emissions = {arm: {} for arm in fresh.ARMS}
    rows = []
    expected_rows = []
    environment_transitions = []
    row_bindings = []
    records = [{
        "kind": "PREPARED",
        "seed_ordinal": 0,
        "payload": {
            "outcome_access": {"count": 0, "event_ids": []},
        },
    }]
    event_ids = []
    count = 0
    for index, row_id in enumerate(row_ids):
        plan_arms = {}
        arm_records = {}
        for arm in fresh.ARMS:
            transition_id = f"transition:{row_id}:{arm}"
            predecessor = f"predecessor:{row_id}:{arm}"
            successor = f"successor:{row_id}:{arm}"
            plan_arms[arm] = {
                "transition_id": transition_id,
                "predecessor_fen": predecessor,
                "move_uci": f"move-{arm}",
            }
            environment_transitions.append({
                "transition_id": transition_id,
                "predecessor_fen": predecessor,
                "move_uci": f"move-{arm}",
                "successor_fen": successor,
                "outcome": False,
            })
            receipt_id = f"receipt:{row_id}:{arm}"
            emission = {
                "receipt_id": receipt_id,
                "matching_cell_ids": [],
                "supporting_cell_ids": [],
                "contradiction_cell_ids": [],
                "matured_cell_ids": [],
                "revoked_cell_ids": [],
                "graph_maturity_ids": [],
                "graph_revocation_ids": [],
            }
            final_emissions[arm][receipt_id] = emission
            record = {
                "arm": arm,
                "row_id": row_id,
                "visible_family": (
                    "suffix_spurious" if index < 8 else "suffix_planted"
                ),
                "transition_id": transition_id,
                "pre_outcome_continuation_digest": (
                    f"{arm}-continuation-{index:02d}"
                ),
                "post_event_continuation_digest": (
                    f"{arm}-continuation-{index + 1:02d}"
                ),
                "matching_cell_commitment": [],
                "production_classification": {"available_cell_ids": []},
                "production_formal_authority": False,
                "truthful_predecessor_fen": predecessor,
                "truthful_action_uci": f"move-{arm}",
                "truthful_successor_fen": successor,
                "truthful_outcome": False,
                "grounded_receipt": {"receipt_id": receipt_id},
                "graph_authority_emission": emission,
                "endpoint_increments": {
                    "false_deployment_authority": 0,
                    "selected_spurious_attributable_false_authority": 0,
                    "planted_authority_coverage": 0,
                },
            }
            record["result_record_digest"] = fresh.digest(record)
            arm_records[arm] = record
            count += 1
            event_id = f"seed-00:{row_id}:{arm}"
            event_ids.append(event_id)
            records.append({
                "kind": "OUTCOME_ACCESSED",
                "seed_ordinal": 0,
                "payload": {
                    "event_id": event_id,
                    "transition_id": transition_id,
                    "next_guard_manifest": {
                        "count": count,
                        "event_ids": list(event_ids),
                    },
                },
            })
        row = {
            "seed_ordinal": 0,
            "genome_seed": 12345,
            "row_id": row_id,
            "arms": arm_records,
        }
        row["scientific_row_digest"] = fresh.digest(row)
        rows.append(row)
        binding = {"path": f"row:{index}"}
        row_bindings.append(binding)
        records.append({
            "kind": "TRI_ARM_ROW_COMMITTED",
            "seed_ordinal": 0,
            "payload": {
                "row_id": row_id,
                "staged_state": {
                    **{
                        arm: {
                            "continuation_digest": (
                                f"{arm}-continuation-{index + 1:02d}"
                            ),
                            "suffix_topology_identity_digest": fresh.digest(
                                {"topology": arm}
                            ),
                        }
                        for arm in fresh.ARMS
                    },
                    "scientific_row_binding": binding,
                },
            },
        })
        expected_rows.append({
            "row_id": row_id,
            "visible_family": (
                "suffix_spurious" if index < 8 else "suffix_planted"
            ),
            "arms": plan_arms,
        })
    final_wrappers = {
        arm: _FakeWrapper(
            arm,
            f"{arm}-continuation-16",
            16,
            final_emissions[arm],
        )
        for arm in fresh.ARMS
    }
    initial_states = {
        arm: {
            cell_id: state.manifest()
            for cell_id, state in baseline[(0, arm)].states.items()
        }
        for arm in fresh.ARMS
    }
    final_cell_states = {
        arm: {
            cell_id: state.manifest()
            for cell_id, state in final_wrappers[arm].states.items()
        }
        for arm in fresh.ARMS
    }
    target_final_states = {
        arm: {
            "planted": final_cell_states[arm]["p"],
            "selected_spurious": final_cell_states[arm]["s"],
        }
        for arm in fresh.ARMS
    }
    endpoint_totals = {
        arm: {
            "false_deployment_authority": 0,
            "selected_spurious_attributable_false_authority": 0,
            "planted_authority_coverage": 0,
        }
        for arm in fresh.ARMS
    }
    seed_result = {
        "seed_ordinal": 0,
        "genome_seed": 12345,
        "targets": targets,
        "identity_contract_digest": "contract",
        "row_bindings": row_bindings,
        "endpoints": endpoint_totals,
        "clearing_summary": fresh.summarize_clearing_events(rows, targets),
        "initial_states": initial_states,
        "immediate_authority_cell_ids": {
            arm: [] for arm in fresh.ARMS
        },
        "target_final_states": target_final_states,
        "final_cell_states": final_cell_states,
        "final_event_ordinals": {arm: 16 for arm in fresh.ARMS},
        "final_emission_digests": {
            arm: fresh.digest(final_emissions[arm]) for arm in fresh.ARMS
        },
        "final_continuation_digests": {
            arm: f"{arm}-continuation-16" for arm in fresh.ARMS
        },
        "final_snapshots": {arm: {"arm": arm} for arm in fresh.ARMS},
    }
    seed_result["seed_result_digest"] = fresh.digest(seed_result)
    seed_binding = {
        "path": "seed-result",
        "seed_result_digest": seed_result["seed_result_digest"],
    }
    records.append({
        "kind": "COMMITTED",
        "seed_ordinal": 0,
        "payload": {
            "final_state": {
                **{
                    arm: {
                        "continuation_digest": f"{arm}-continuation-16",
                        "suffix_topology_identity_digest": fresh.digest(
                            {"topology": arm}
                        ),
                    }
                    for arm in fresh.ARMS
                },
                "scientific_seed_binding": seed_binding,
            },
            "outcome_access": {"count": count, "event_ids": event_ids},
        },
    })
    carrier = {"seed-result": seed_result}
    carrier.update({f"row:{index}": row for index, row in enumerate(rows)})

    class FakeJournal:
        def _records(self) -> list[dict]:
            return records

    monkeypatch.setattr(
        fresh,
        "_read_bound_json",
        lambda binding: copy.deepcopy(carrier[binding["path"]]),
    )
    monkeypatch.setattr(
        fresh,
        "_restore_final_snapshot",
        lambda snapshot: final_wrappers[snapshot["arm"]],
    )
    monkeypatch.setattr(
        fresh,
        "exact_arm_identity_contract",
        lambda _arms: {"contract_digest": "contract"},
    )
    monkeypatch.setattr(
        fresh,
        "suffix_topology_identity",
        lambda wrapper: {"topology": wrapper.arm},
    )
    environment = {"transitions": environment_transitions}
    metadata = {0: {"genome_seed": 12345, "targets": targets}}
    return FakeJournal(), expected_rows, baseline, metadata, environment, carrier


def _resign_fake_seed_result(carrier: dict, records: list[dict] | None = None) -> None:
    seed_result = carrier["seed-result"]
    seed_result["seed_result_digest"] = fresh.digest({
        key: value for key, value in seed_result.items()
        if key != "seed_result_digest"
    })


def test_committed_reconstruction_accepts_exact_rows_and_final_graphs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    journal, rows, baseline, metadata, environment, _carrier = (
        _reconstruction_fixture(monkeypatch)
    )
    result = fresh.committed_seed_results(
        journal,
        expected_ordinals=(0,),
        expected_rows=rows,
        baseline_wrappers=baseline,
        expected_seed_metadata=metadata,
        environment_manifest=environment,
    )
    assert result[0]["reconstruction"]["row_count"] == 16
    assert result[0]["reconstruction"]["outcome_read_count"] == 48


@pytest.mark.parametrize(
    ("case", "message"),
    (
        ("endpoint", "endpoint summary"),
        ("target", "target_final_states summary"),
        ("continuation", "final_continuation_digests summary"),
    ),
)
def test_committed_reconstruction_rejects_changed_stored_summaries(
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    message: str,
) -> None:
    journal, rows, baseline, metadata, environment, carrier = (
        _reconstruction_fixture(monkeypatch)
    )
    seed_result = carrier["seed-result"]
    if case == "endpoint":
        seed_result["endpoints"]["A"]["false_deployment_authority"] = 1
    elif case == "target":
        seed_result["target_final_states"]["A"]["planted"]["support"] = 99
    else:
        seed_result["final_continuation_digests"]["A"] = "changed"
    _resign_fake_seed_result(carrier)
    # The fake journal binding tracks the newly signed record, as a real
    # internally re-signed carrier would.
    journal._records()[-1]["payload"]["final_state"][
        "scientific_seed_binding"
    ]["seed_result_digest"] = seed_result["seed_result_digest"]
    with pytest.raises(fresh.FreshScientificIntegrityError, match=message):
        fresh.committed_seed_results(
            journal,
            expected_ordinals=(0,),
            expected_rows=rows,
            baseline_wrappers=baseline,
            expected_seed_metadata=metadata,
            environment_manifest=environment,
        )


def test_committed_reconstruction_rejects_duplicate_missing_or_reordered_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    journal, rows, baseline, metadata, environment, carrier = (
        _reconstruction_fixture(monkeypatch)
    )
    seed_result = carrier["seed-result"]
    seed_result["row_bindings"][1] = copy.deepcopy(seed_result["row_bindings"][0])
    _resign_fake_seed_result(carrier)
    journal._records()[-1]["payload"]["final_state"][
        "scientific_seed_binding"
    ]["seed_result_digest"] = seed_result["seed_result_digest"]
    with pytest.raises(fresh.FreshScientificIntegrityError):
        fresh.committed_seed_results(
            journal,
            expected_ordinals=(0,),
            expected_rows=rows,
            baseline_wrappers=baseline,
            expected_seed_metadata=metadata,
            environment_manifest=environment,
        )


def test_committed_reconstruction_rejects_final_graph_row_disagreement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    journal, rows, baseline, metadata, environment, _carrier = (
        _reconstruction_fixture(monkeypatch)
    )
    original_restore = fresh._restore_final_snapshot
    def changed_restore(snapshot: dict) -> _FakeWrapper:
        wrapper = original_restore(snapshot)
        if snapshot["arm"] == "A":
            wrapper._continuation = "A-different-final-continuation"
        return wrapper
    monkeypatch.setattr(fresh, "_restore_final_snapshot", changed_restore)
    with pytest.raises(
        fresh.FreshScientificIntegrityError,
        match="row/snapshot continuation",
    ):
        fresh.committed_seed_results(
            journal,
            expected_ordinals=(0,),
            expected_rows=rows,
            baseline_wrappers=baseline,
            expected_seed_metadata=metadata,
            environment_manifest=environment,
        )


def test_committed_reconstruction_rejects_journal_transition_disagreement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    journal, rows, baseline, metadata, environment, _carrier = (
        _reconstruction_fixture(monkeypatch)
    )
    outcome_record = next(
        record
        for record in journal._records()
        if record["kind"] == "OUTCOME_ACCESSED"
    )
    outcome_record["payload"]["transition_id"] = "foreign-transition"
    with pytest.raises(
        fresh.FreshScientificIntegrityError,
        match="journal/row transition mismatch",
    ):
        fresh.committed_seed_results(
            journal,
            expected_ordinals=(0,),
            expected_rows=rows,
            baseline_wrappers=baseline,
            expected_seed_metadata=metadata,
            environment_manifest=environment,
        )
