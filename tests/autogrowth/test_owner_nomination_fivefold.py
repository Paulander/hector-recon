"""Recorder equivalence, partial evidence and fixed fivefold schedule."""
import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts/autogrowth'))
import run_owner_nomination as original
import run_owner_nomination_fivefold as lab
from test_owner_nomination_runner import small_source


def test_fivefold_phase_orders_preserve_original_first_prefix_and_exposures():
    for seed in lab.SEEDS:
        old_prefix, old_continuation = original.schedule(seed)
        prefix, continuation = lab.schedule(seed)
        assert prefix == old_prefix*5
        assert continuation == old_continuation[:128]*5 + old_continuation[128:]*5
        assert len(prefix) == 640 and len(continuation) == 1280
        assert sum(lab.ROWS[row][2] for row in continuation[:640]) == 560
        assert sum(lab.ROWS[row][2] for row in continuation[640:]) == 80
    assert 2*len(prefix) + 4*len(continuation) == lab.COUNTS['training'] == 6400
    assert 2*(2+2*20)*16 == lab.COUNTS['evaluation'] == 1344


def test_immutable_recorder_preserves_learning_and_formal_graph(tmp_path):
    actor = lab.AdaptiveOwnerDevelopment.from_actor(small_source(), state_coordinates=(0,1,2,3),
             development=lab.OwnerDevelopmentConfig(develop_every=8, min_support=2))
    left, right = copy.deepcopy(actor), copy.deepcopy(actor)
    order = list(range(16))
    first, _, old_eval = original.train_block(left, order, tmp_path/'old', 'same-start', do_evaluate=True)
    second, _, new_eval = lab.train_block(right, order, tmp_path/'new', 'same-start', do_evaluate=True)
    lab.same_state(first, second)
    assert old_eval == new_eval
    assert (tmp_path/'old/training.jsonl').read_bytes() == (tmp_path/'new/training.jsonl').read_bytes()
    assert len(list((tmp_path/'new/submitted').glob('*.json'))) == 16
    assert len(list((tmp_path/'new/credited').glob('*.json'))) == 16
    lab.verify_block(tmp_path/'new', order, 8, 'same-start')


def test_executed_action_survives_feedback_failure(tmp_path, monkeypatch):
    actor = small_source()
    def stop(_feedback):
        raise RuntimeError('interrupt after environment outcome')
    monkeypatch.setattr(actor, 'observe', stop)
    with pytest.raises(RuntimeError, match='interrupt after'):
        lab.train_block(actor, [0,1], tmp_path/'partial', 'start', do_evaluate=True)
    records = list((tmp_path/'partial/submitted').glob('*.json'))
    assert len(records) == 1
    record = json.loads(records[0].read_text())
    assert record['event'] == 8 and record['action'] in ('act-a','act-b')
    assert not list((tmp_path/'partial/credited').glob('*'))
    assert not (tmp_path/'partial/complete.json').exists()


def test_modified_immutable_record_and_duplicate_block_are_rejected(tmp_path):
    actor = small_source()
    restored, checkpoint, _ = lab.train_block(actor, [0,1], tmp_path/'block', 'start', do_evaluate=False)
    with pytest.raises(FileExistsError):
        lab.train_block(restored, [0], tmp_path/'block', checkpoint, do_evaluate=False)
    path = tmp_path/'block/submitted/000008.json'
    path.write_bytes(b'{}\n')
    with pytest.raises(AssertionError):
        lab.verify_block(tmp_path/'block', [0,1], 8, 'start')
