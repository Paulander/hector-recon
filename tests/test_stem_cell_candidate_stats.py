from recon_lite_chess.autogrowth import validate_learner_record
from recon_lite_hector.nodes.stem_cell import StemCellState, StemCellTerminal


def _trial_cell() -> StemCellTerminal:
    cell = StemCellTerminal("candidate_stats_test")
    cell.state = StemCellState.TRIAL
    cell.xp = cell.XP_SOLIDIFY
    cell.trial_node_id = "TRIAL_candidate_stats_test"
    cell.trial_parent_id = "local_parent"
    return cell


def test_positive_correlation_alone_cannot_mature_candidate() -> None:
    cell = _trial_cell()
    cell.record_candidate_request("local_parent")
    cell.record_candidate_activation("local_parent")
    cell.mark_confirmed(1)
    cell.record_candidate_correlation("positive")

    should_change, state = cell.check_solidification()

    assert should_change is False
    assert state == "needs_intervention"
    assert cell.candidate_survival_decision() == "needs_intervention"


def test_causal_intervention_is_required_for_maturity() -> None:
    cell = _trial_cell()
    cell.record_candidate_request("local_parent")
    cell.record_candidate_activation("local_parent")
    cell.mark_confirmed(2)
    cell.record_candidate_intervention("positive", cycle=2)

    should_change, state = cell.check_solidification()

    assert should_change is True
    assert state == "mature"
    assert cell.candidate_can_mature() is True


def test_negative_relevant_candidate_becomes_suppressor_instead_of_prune() -> None:
    cell = _trial_cell()
    cell.xp = 40
    cell.record_candidate_request("local_parent")
    cell.record_candidate_activation("local_parent")
    cell.mark_confirmed(3)
    cell.mark_sibling_contrast(1.0, suppressed_sibling="candidate_action_leg")
    cell.record_candidate_intervention("negative", cycle=3)

    should_change, state = cell.check_solidification()

    assert should_change is False
    assert state == "suppress"
    assert cell.state == StemCellState.TRIAL
    assert cell.candidate_stats.survival_stats.quarantine_reason == "local_suppressor_candidate"
    assert cell.candidate_stats.survival_stats.suppressed_sibling == "candidate_action_leg"


def test_candidate_stats_roundtrip_and_firewall() -> None:
    cell = _trial_cell()
    cell.record_candidate_request("local_parent")
    cell.record_candidate_activation("local_parent")
    cell.mark_confirmed(4)
    cell.mark_sibling_contrast(0.8, suppressed_sibling="candidate_action_leg")
    cell.record_candidate_intervention("negative", cycle=4)

    restored = StemCellTerminal.from_dict(cell.to_dict())

    assert restored.candidate_stats.relevance_stats.request_exposures == 1
    assert restored.candidate_stats.relevance_stats.activation_count == 1
    assert restored.candidate_stats.relevance_stats.confirm_count == 1
    assert restored.candidate_stats.credit_stats.negative_intervention == 1
    assert restored.candidate_stats.survival_stats.last_confirm_cycle == 4
    validate_learner_record(restored.candidate_stats.to_dict())
