import time

import pytest

from recon_lite_chess.experiments.m1_ranking_certificate import certificate


def test_favorable_ties_are_valid_and_unfavorable_ties_are_impossible():
    matrix = [[(0,), (0,)]]
    good = certificate([{'wins': [0, 1]}], matrix, deadline=time.monotonic()+10)
    bad = certificate([{'wins': [1, 0]}], matrix, deadline=time.monotonic()+10)
    assert good['perfect_fixed_weight_policy_exists']
    assert not bad['perfect_fixed_weight_policy_exists']
    assert bad['solver_independent_impossibility_witness']


def test_distinct_signatures_can_require_incompatible_weights():
    rows = [{'wins': [1, 0]}, {'wins': [0, 1]}]
    result = certificate(rows, [[(1,), (0,)], [(1,), (0,)]], deadline=time.monotonic()+10)
    assert not result['perfect_fixed_weight_policy_exists']
    witness = result['elementary_contradiction']
    assert sum(witness['minimum_margins']) > 0
    assert all(a == -b for a, b in zip(witness['delta'], witness['opposite_delta']))
    assert result['fitted_weights_discarded'] and 'weights' not in result


def test_added_context_conjunction_can_remove_the_conflict():
    rows = [{'wins': [1, 0]}, {'wins': [0, 1]}]
    result = certificate(rows, [[(1, 0), (0, 0)], [(1, 1), (0, 0)]], deadline=time.monotonic()+10)
    assert result['perfect_fixed_weight_policy_exists']


def test_multiple_winners_rejected_instead_of_overclaiming():
    with pytest.raises(ValueError, match='one winning'):
        certificate([{'wins': [1, 1]}], [[(0,), (1,)]], deadline=time.monotonic()+10)
