from __future__ import annotations

from dataclasses import asdict
import hashlib

import chess
import pytest

from recon_lite import FrameContext, FrameKind
from recon_lite_chess.autogrowth.native_competence_envelope import (
    AvailabilityState, StemCellState,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_v2_science import (
    BASELINE_PACKAGE_MANIFEST,
    MIN_FAVORABLE_SEEDS,
    PROTECTED_HASHES,
    _arm_input,
    _classification_visible_projection,
    _rows,
    build_ecology_r0,
    candidate_identical_arms,
    exact_one_sided_sign_test,
    generate_c_permutation_manifest,
    generate_ecology_manifest,
    holm_adjust_two,
    policy_critical_package_hashes,
    run_discovery_seed,
    select_prefix_targets,
    sha256_file,
    sha256_json,
    validate_ecology_graph,
    verify_protected_boundary,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2, ProspectiveV2IntegrityError,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2_lab import (
    RegisteredV2ExposureRow, V2LaboratoryRegistry,
)


@pytest.fixture(scope="module")
def ecology():
    return generate_ecology_manifest()


@pytest.fixture(scope="module")
def discovery(ecology):
    return run_discovery_seed(
        {"ordinal": 0, "genome_seed": 1101}, ecology
    )


def test_protected_v21_boundary_is_exact():
    verify_protected_boundary()
    for relative, expected in PROTECTED_HASHES.items():
        assert sha256_file(relative) == expected
    package = policy_critical_package_hashes()
    assert sha256_json(package) == BASELINE_PACKAGE_MANIFEST


def test_ecology_is_legal_truthful_and_visibility_matched(ecology):
    validation = validate_ecology_graph(ecology)
    assert validation["row_count"] == 80
    assert validation["exact_visible_pair_count"] == 80
    for row in _rows(ecology, "prefix") + _rows(ecology, "suffix"):
        for arm in ("A", "C"):
            fen, expected = _arm_input(row, arm)
            board = chess.Board(fen)
            move = chess.Move.from_uci(row.move_uci)
            assert move in board.legal_moves
            board.push(move)
            assert board.is_checkmate() is expected


def test_c_permutation_is_truthful_and_preserves_marginals(ecology):
    manifest = generate_c_permutation_manifest(ecology)
    assert manifest["truthful_transitions"] is True
    assert manifest["label_shuffle"] is False
    assert manifest["outcome_marginals_preserved"] is True
    assert all(
        row["a_transition"]["outcome"] is not row["c_transition"]["outcome"]
        for row in manifest["rows"]
    )


def test_native_discovery_and_prefix_only_target_selection(ecology, discovery):
    wrapper = NativeProspectiveAuthorityV2.loads(discovery["payload"])
    assert wrapper.base.envelope.nomination_epoch.nomination_closed
    targets = select_prefix_targets(wrapper, ecology)
    assert targets == discovery["targets"]
    assert targets["selection_used_suffix"] is False
    assert targets["planted"] is not None
    assert targets["selected_spurious"] is not None
    assert targets["planted"]["pattern_digest"] == ecology["planted_pattern_digest"]
    assert targets["selected_spurious"]["pattern_digest"] in {
        row["pattern_digest"] for row in ecology["spurious_family"]
    }
    assert targets["selected_spurious"]["pattern_digest"] != targets["planted"]["pattern_digest"]


def test_candidate_identical_arms_have_only_frozen_authority_difference(discovery):
    wrapper = NativeProspectiveAuthorityV2.loads(discovery["payload"])
    arms = candidate_identical_arms(wrapper)
    assert not any(state.prospectively_certified for state in arms["A"].states.values())
    assert not any(state.prospectively_certified for state in arms["C"].states.values())
    for cell_id, state in arms["B"].states.items():
        assert state.prospectively_certified is (
            arms["B"].base.envelope.cells[cell_id].stem_cell.state.name
            == StemCellState.MATURE.name
        )


def test_a_b_c_classifier_visible_projection_is_exact(ecology, discovery):
    original = NativeProspectiveAuthorityV2.loads(discovery["payload"])
    arms = candidate_identical_arms(original)
    row = _rows(ecology, "suffix")[0]
    planted = discovery["targets"]["planted"]["cell_id"]
    spurious = discovery["targets"]["selected_spurious"]["cell_id"]
    projections = {}
    physical = {}
    for arm, wrapper in arms.items():
        fen, _ = _arm_input(row, arm)
        commitment = wrapper.probe_real_exposure(FrameContext(
            f"test:{arm}", FrameKind.REAL,
            values={"board": chess.Board(fen)},
        ))
        projection = _classification_visible_projection(
            wrapper, commitment,
            planted_cell_id=planted,
            spurious_cell_id=spurious,
            row_id=row.row_id,
        )
        projections[arm] = {
            key: value for key, value in projection.items()
            if key != "projection_digest"
        }
        physical[arm] = commitment.interaction_fingerprint
    assert projections["A"] == projections["B"] == projections["C"]
    assert physical["A"] == physical["B"]
    assert physical["C"] != physical["A"]


def test_truthful_receipt_drives_only_post_outcome_prospective_state(ecology, discovery):
    original = NativeProspectiveAuthorityV2.loads(discovery["payload"])
    wrapper = candidate_identical_arms(original)["A"]
    row = _rows(ecology, "suffix")[0]
    predecessor = chess.Board(row.a_fen)
    pending, trace = wrapper.open_real_event(FrameContext(
        "truthful-real-event", FrameKind.REAL, values={"board": predecessor}
    ))
    assert pending.pre_outcome_classification.state is AvailabilityState.UNKNOWN
    successor = predecessor.copy(stack=False)
    successor.push(chess.Move.from_uci(trace.actuation.move_uci))
    receipt = wrapper.mint_environment_receipt(
        pending_token=pending.pending_token,
        trace=trace,
        predecessor=predecessor,
        successor=successor,
    )
    assert receipt.observed_outcome is successor.is_checkmate()
    emission = wrapper.consume(receipt)
    assert set(emission.contradiction_cell_ids) == set(pending.matching_cell_ids)
    assert wrapper.pending_event is None


def test_exact_paired_inference_and_holm_are_seed_level():
    values = [1] * MIN_FAVORABLE_SEEDS + [0] * (32 - MIN_FAVORABLE_SEEDS)
    result = exact_one_sided_sign_test(values)
    assert result == {
        "wins": MIN_FAVORABLE_SEEDS,
        "losses": 0,
        "ties": 32 - MIN_FAVORABLE_SEEDS,
        "non_tied_effective_n": MIN_FAVORABLE_SEEDS,
        "one_sided_exact_p": 2 ** (-MIN_FAVORABLE_SEEDS),
    }
    adjusted = holm_adjust_two({"D_safe": result["one_sided_exact_p"], "D_signal": 0.02})
    assert adjusted["D_safe"] == 2 * result["one_sided_exact_p"]
    assert adjusted["D_signal"] == 0.02



def test_registry_scan_is_source_bound_and_raw_adjudication_fails_closed(ecology, discovery):
    original = NativeProspectiveAuthorityV2.loads(discovery["payload"])
    wrapper = candidate_identical_arms(original)["A"]
    payload = wrapper.dumps()
    row = _rows(ecology, "suffix")[0]
    registered = RegisteredV2ExposureRow(
        row_id=row.row_id,
        frame_id="focused-registry-row",
        predecessor_fen=row.a_fen,
    )
    package_hashes = {
        **policy_critical_package_hashes(),
        "focused_outer_manifest": hashlib.sha256(b"focused").hexdigest(),
    }
    registry = V2LaboratoryRegistry.freeze(
        {"seed-00": payload},
        exposure_rows={"seed-00": (registered,)},
        row_order=(row.row_id,),
        run_identity="focused-registry-run",
        package_hashes=package_hashes,
    )
    commitment = wrapper.probe_real_exposure(FrameContext(
        registered.frame_id, FrameKind.REAL,
        values={"board": chess.Board(registered.predecessor_fen)},
    ))
    scan = registry.scan(
        "seed-00", payload, (commitment,),
        tape_identity=registry.tape_identity,
        row_order=registry.row_order,
        run_identity=registry.run_identity,
        package_hashes=package_hashes,
    )
    assert scan["registry_id"] == registry.registry_id
    with pytest.raises(ProspectiveV2IntegrityError, match="exactly 32"):
        registry.adjudicate_cohort(
            (scan,), tape_identity=registry.tape_identity,
            row_order=registry.row_order,
            run_identity=registry.run_identity,
            package_hashes=package_hashes,
        )
    with pytest.raises(ProspectiveV2IntegrityError, match="raw-only"):
        registry.adjudicate_cohort(
            (scan["scan"],), tape_identity=registry.tape_identity,
            row_order=registry.row_order,
            run_identity=registry.run_identity,
            package_hashes=package_hashes,
        )
