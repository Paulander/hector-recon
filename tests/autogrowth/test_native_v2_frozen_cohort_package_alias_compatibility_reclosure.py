from __future__ import annotations

import copy
from functools import lru_cache
import hashlib
import inspect
from pathlib import Path
import sys

import chess
import pytest

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.learning import IntrinsicCreditConfig, IntrinsicCreditEngine
from recon_lite_chess.autogrowth import (
    native_v2_frozen_cohort_package_alias_compatibility_reclosure as closure,
)
from recon_lite_chess.autogrowth.native_authority_handover import (
    FrozenCompetenceProvenance,
    NativeR0Organism,
)
from recon_lite_chess.autogrowth.native_competence_envelope import (
    CompetenceEnvelopeConfig,
    SpecializationMode,
)
from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    R0_COMPETENCE_ID,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    ProspectiveV2IntegrityError,
    V2Mode,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2_lab import (
    RegisteredV2ExposureRow,
    V2LaboratoryRegistry,
)
from recon_lite_chess.autogrowth.native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
)
from recon_lite_chess.autogrowth.native_trace_competence_authority import (
    TraceNativeCompetenceOrganism,
    TraceNativeLearningConfig,
)


MATE_ONE = "8/8/8/8/8/7K/5R2/7k w - - 0 1"


def _after(board: chess.Board, move: chess.Move) -> chess.Board:
    successor = board.copy(stack=False)
    successor.push(move)
    return successor


@lru_cache(maxsize=1)
def _tiny_components() -> tuple[NativeReConKRKGraph, IntrinsicCreditEngine]:
    board = chess.Board(MATE_ONE)
    mate = next(
        move for move in board.legal_moves
        if _after(board, move).is_checkmate()
    )
    graph = NativeReConKRKGraph(config=NativeSingleGraphConfig(
        include_symmetries=False,
        max_ticks=80,
        indexed_scheduler=True,
        key_mode="canonical",
        shared_feature_atoms=True,
        shared_projection_atoms=True,
        include_grouped_cache_terminals=False,
        score_action_pattern_atoms=True,
        terminal_score_normalization="sqrt",
    ))
    graph.apply_intrinsic_td(
        board, mate, td_error=1.0, stage_diagnostic="synthetic_alias_canary"
    )
    graph.mature_existing_graph()
    graph.freeze_existing_parameters(reason="synthetic_alias_canary")
    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(min_grounding_evidence=3)
    )
    credit.register(R0_COMPETENCE_ID, mature=True)
    state = credit.states[R0_COMPETENCE_ID]
    state.slow_value = state.fast_value = 0.8
    state.terminal_evidence = 3
    state.causal_confirmations = 1
    state.grounding_level = 0
    return graph, credit


def _tiny_v2(ordinal: int) -> NativeProspectiveAuthorityV2:
    graph_template, credit_template = _tiny_components()
    graph = copy.deepcopy(graph_template)
    credit = copy.deepcopy(credit_template)
    r0 = NativeR0Organism(
        graph=graph,
        credit=credit,
        provenance=FrozenCompetenceProvenance.from_credit(
            credit, R0_COMPETENCE_ID
        ),
        frozen_triplet_ids=frozenset(graph.triplet_ids),
        source_manifest={
            "kind": "synthetic_alias_canary",
            "ordinal": ordinal,
        },
    )
    envelope_config = CompetenceEnvelopeConfig(selection_seed=9173 + ordinal)
    trace = TraceNativeCompetenceOrganism.empty(
        r0,
        envelope_config=envelope_config,
        learning_config=TraceNativeLearningConfig(
            lifecycle_connected=True,
            specialization_mode=SpecializationMode.LOCAL_CONTRAST,
            genome_seed=envelope_config.selection_seed,
        ),
    )
    wrapper = NativeProspectiveAuthorityV2.from_organism(
        trace, mode=V2Mode.PROSPECTIVE
    )
    wrapper.close_nomination()
    return wrapper


@pytest.fixture(scope="module")
def synthetic_registry_fixture() -> dict:
    board = chess.Board(MATE_ONE)
    row_order = ("synthetic-row-0",)
    wrappers = {}
    payloads = {}
    exposure_rows = {}
    commitments = {}
    for ordinal in range(32):
        organism_id = f"organism-{ordinal:02d}"
        wrapper = NativeProspectiveAuthorityV2.loads(
            _tiny_v2(ordinal).dumps()
        )
        row = RegisteredV2ExposureRow(
            row_id=row_order[0],
            frame_id=f"synthetic-alias-canary:{organism_id}:row-0",
            predecessor_fen=board.fen(),
        )
        commitment = wrapper.probe_real_exposure(FrameContext(
            row.frame_id,
            FrameKind.REAL,
            values={"board": board},
        ))
        wrappers[organism_id] = wrapper
        payloads[organism_id] = wrapper.dumps()
        exposure_rows[organism_id] = (row,)
        commitments[organism_id] = (commitment,)
    return {
        "wrappers": wrappers,
        "payloads": payloads,
        "exposure_rows": exposure_rows,
        "row_order": row_order,
        "commitments": commitments,
        "run_identity": "synthetic-package-alias-canary.v1",
    }


def _freeze_registry(fixture: dict, package_map: dict) -> V2LaboratoryRegistry:
    return V2LaboratoryRegistry.freeze(
        fixture["payloads"],
        exposure_rows=fixture["exposure_rows"],
        row_order=fixture["row_order"],
        run_identity=fixture["run_identity"],
        package_hashes=package_map,
    )


def test_diagnosis_has_exactly_13_absent_three_way_equal_aliases() -> None:
    value = closure.diagnose_original_package_map()
    assert value["alias_count"] == 13
    assert value["all_original_aliases_absent"]
    assert value["all_path_file_alias_digests_equal"]
    assert len(value["rows"]) == 13
    for row in value["rows"]:
        assert not row["alias_present"]
        assert (
            row["runtime_digest"]
            == row["file_digest"]
            == row["expected_alias_digest"]
        )
        assert row["runtime_key"] == "runtime:" + row["declared_path"]


def test_expansion_retains_complete_original_map_and_adds_only_aliases() -> None:
    original = closure.driver.laboratory_package_hashes()
    expanded = closure.derive_expanded_package_map(original)
    aliases = closure.declared_alias_paths()
    assert set(expanded) == set(original) | set(aliases)
    assert all(expanded[key] == value for key, value in original.items())
    assert closure.expanded_package_map_manifest(expanded)[
        "complete_original_map_retained"
    ]


@pytest.mark.parametrize(
    "alias", sorted(closure.laboratory.POLICY_CRITICAL_SOURCE_PATHS)
)
@pytest.mark.parametrize("operation", ("remove", "change"))
def test_removing_or_changing_any_alias_fails(
    alias: str, operation: str
) -> None:
    expanded = closure.expanded_package_map()
    if operation == "remove":
        expanded.pop(alias)
    else:
        expanded[alias] = "0" * 64
    with pytest.raises(closure.CompatibilityClosureError):
        closure.validate_expanded_package_map(expanded)


def test_wrong_declared_path_fails() -> None:
    wrong = closure.declared_alias_paths()
    wrong["hector_m5_structure"] = wrong["hector_pack_template"]
    with pytest.raises(
        closure.CompatibilityClosureError,
        match="declared alias-to-path",
    ):
        closure.derive_expanded_package_map(
            closure.driver.laboratory_package_hashes(),
            declared_paths=wrong,
        )


def test_extra_manually_authored_alias_fails() -> None:
    expanded = closure.expanded_package_map()
    expanded["manual_alias"] = "0" * 64
    with pytest.raises(
        closure.CompatibilityClosureError, match="key coverage"
    ):
        closure.validate_expanded_package_map(expanded)


def test_production_expanded_map_creates_real_registry(
    synthetic_registry_fixture: dict,
) -> None:
    package_map = closure.expanded_package_map()
    registry = _freeze_registry(synthetic_registry_fixture, package_map)
    assert isinstance(registry, V2LaboratoryRegistry)
    assert tuple(registry.package_hashes) == tuple(sorted(package_map.items()))
    assert len(registry.organisms) == 32
    assert len(registry.exposure_rows) == 32


def test_data_free_create_scan_and_cohort_use_same_map(
    synthetic_registry_fixture: dict,
) -> None:
    package_map = closure.expanded_package_map()
    registry = _freeze_registry(synthetic_registry_fixture, package_map)
    scans = [
        registry.scan(
            organism_id,
            synthetic_registry_fixture["payloads"][organism_id],
            synthetic_registry_fixture["commitments"][organism_id],
            tape_identity=registry.tape_identity,
            row_order=synthetic_registry_fixture["row_order"],
            run_identity=synthetic_registry_fixture["run_identity"],
            package_hashes=package_map,
        )
        for organism_id in sorted(synthetic_registry_fixture["payloads"])
    ]
    adjudication = registry.adjudicate_cohort(
        scans,
        tape_identity=registry.tape_identity,
        row_order=synthetic_registry_fixture["row_order"],
        run_identity=synthetic_registry_fixture["run_identity"],
        package_hashes=package_map,
    )
    assert all(scan["registry_id"] == registry.registry_id for scan in scans)
    assert adjudication["organism_count"] == 32
    assert all(scan["scan"]["outcome_fields_read"] == 0 for scan in scans)
    assert dict(registry.package_hashes) == package_map


def test_old_map_reproduces_preserved_alias_failure(
    synthetic_registry_fixture: dict,
) -> None:
    old_map = closure.driver.laboratory_package_hashes()
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="hector_m5_structure",
    ):
        _freeze_registry(synthetic_registry_fixture, old_map)


def test_bounded_reconstruction_differs_only_in_map_acquisition() -> None:
    value = closure.reconstruction_ast_comparison()
    assert value["normalized_equal"]
    assert "laboratory_package_hashes" in value["frozen_acquisition_ast"]
    assert (
        "validate_expanded_package_map"
        in value["bounded_acquisition_ast"]
    )


def test_compatibility_operations_do_not_replace_module_globals(
    synthetic_registry_fixture: dict,
) -> None:
    before = closure.capture_critical_bindings()
    package_map = closure.expanded_package_map()
    registry = _freeze_registry(synthetic_registry_fixture, package_map)
    organism_id = sorted(synthetic_registry_fixture["payloads"])[0]
    registry.scan(
        organism_id,
        synthetic_registry_fixture["payloads"][organism_id],
        synthetic_registry_fixture["commitments"][organism_id],
        tape_identity=registry.tape_identity,
        row_order=synthetic_registry_fixture["row_order"],
        run_identity=synthetic_registry_fixture["run_identity"],
        package_hashes=package_map,
    )
    unchanged = closure.require_bindings_unchanged(before)
    assert "driver._reconstruct_exposure_value" in unchanged
    assert "stopped_adapter.run_exposure" in unchanged


def test_new_namespace_and_output_paths_are_disjoint() -> None:
    assert closure.PACKAGE_DIR != closure.stopped_adapter.PACKAGE_DIR
    assert closure.PACKAGE_ID != closure.stopped_adapter.PACKAGE_ID
    assert closure.EXPOSURE_PATH != closure.stopped_adapter.EXPOSURE_PATH
    assert closure.RESULT_PATH != closure.stopped_adapter.RESULT_PATH
    for command in closure.PUBLIC_COMMANDS:
        assert closure.build_public_command(command) == (
            sys.executable, "-m", closure.MODULE_PATH, command
        )


def test_readiness_stops_before_probe_or_scan() -> None:
    source = inspect.getsource(closure.run_readiness)
    registry_source = inspect.getsource(
        closure.construct_registry_manifests_without_scanning
    )
    combined = source + registry_source
    assert "probe_real_exposure" not in combined
    assert ".scan(" not in combined
    assert ".adjudicate_cohort(" not in combined
    assert "run_exposure()" not in source


def test_stopped_failure_and_adapter_package_remain_exact() -> None:
    identity = closure.preserved_adapter_identity()
    rows = {row["path"]: row for row in identity["rows"]}
    failure = rows[
        closure.stopped_adapter.EXPOSURE_FAILURE_PATH.as_posix()
    ]
    assert failure["sha256"] == closure.STOPPED_EXPOSURE_FAILURE_SHA256
    assert closure.sha256_file(
        closure.ROOT / closure.stopped_adapter.SOURCE_MANIFEST_PATH
    ) == "0f0c9daedb0cf667d147c41f63af7dccb0eb9593423f34f14fd9b236e4340b75"


def test_source_has_no_global_replacement_or_dynamic_loading() -> None:
    source = Path(closure.__file__).read_text(encoding="utf-8")
    assert "runpy" not in source
    assert "monkeypatch" not in source
    assert "setattr(driver" not in source
    assert "setattr(laboratory" not in source
    assert "exec(" not in source
    assert "eval(" not in source
