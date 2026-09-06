"""Control-law tests; answers used to test primitives are never learner inputs."""
import argparse
from dataclasses import asdict
import inspect
import json
import pickle
from pathlib import Path

import chess
import pytest

from recon_lite.graph import LinkType
from recon_lite_hector.benchmarks.terminal_attribution import (
    ARMS, AttributionDevelopment, make_plans,
)
from recon_lite_hector.learning.terminal_development import (
    Coordinate, DevelopmentConfig, TerminalDevelopment,
)
from recon_lite_chess.coach.interface import Feedback
from recon_lite_chess.coach.pools import prepare
from recon_lite_chess.coach.runner import source_identity
from recon_lite_chess.coach.terminal import SCHEMA
from recon_lite_chess.experiments import mate_one_attribution as experiment


class Port:
    schema = tuple(Coordinate(name, (False, True)) for name in ("x", "y", "action"))

    def __init__(self, x=False, y=False):
        self.values = (x, y)
        self.executed = None

    def bindings(self):
        assert inspect.currentframe().f_back.f_code.co_name == "_catalog"
        return ("a", "b")

    def measure(self, index, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_reader"
        return (*self.values, binding == "b")[index]

    def execute(self, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_actuator"
        assert self.executed is None
        self.executed = binding


def organisms(seed=1, episodes=64):
    mixed, atomic = make_plans(Port.schema, seed=seed, count=6, episodes=episodes)
    return {arm: AttributionDevelopment(Port.schema, seed=seed, arm=arm,
                                       mixed=mixed, atomic=atomic) for arm in ARMS}


def test_plans_are_production_grammar_without_outcomes_or_board_access():
    mixed, atomic = make_plans(SCHEMA, seed=5, count=80, episodes=128)
    assert (mixed, atomic) == make_plans(SCHEMA, seed=5, count=80, episodes=128)
    generator = TerminalDevelopment(seed="proposals:5",
                                    config=DevelopmentConfig(max_conditions=80))
    generator.schema = SCHEMA
    for event in range(1, 129):
        generator.completed = event
        generator._birth()
    assert [(p.operator, p.atoms, p.after_episode) for p in mixed] == [
        (c.operator, c.atoms, c.born) for c in generator.conditions.values()]
    assert len({(p.operator, p.atoms) for p in atomic}) == 80
    assert all(len(p.atoms) == 1 for p in atomic)
    assert any(len(p.atoms) > 1 for p in mixed)
    with pytest.raises(ValueError, match="unique atomic"):
        make_plans(SCHEMA, seed=5, count=96, episodes=128)
    with pytest.raises(ValueError, match="cannot reveal"):
        make_plans(SCHEMA, seed=5, count=80, episodes=1)


def test_identical_final_definitions_and_paired_exploration_despite_opposite_rewards():
    arms = organisms()
    assert not arms["online_random"].conditions
    assert len(arms["fixed_random"].conditions) == len(arms["atomic_only"].conditions) == 6
    for event in range(64):
        for arm, organism in arms.items():
            port = Port(bool(event % 2), bool(event % 3))
            action = organism.act(port, event_id=event, learn=True)
            assert action == port.executed
            organism.observe(Feedback(event, action, -1 if arm == "online_random" else 1))
            if arm == "online_random":
                assert len(organism.conditions) == sum(p.after_episode <= event + 1
                                                      for p in organism.plan)
        assert len({o.rng.getstate() for o in arms.values()}) == 1
    definitions = lambda o: [(c.operator, c.atoms) for c in o.conditions.values()]
    assert definitions(arms["online_random"]) == definitions(arms["fixed_random"])
    assert any(c.born > 0 for c in arms["online_random"].conditions.values())
    assert all(c.born == 0 for c in arms["fixed_random"].conditions.values())


def test_no_early_reveal_in_evaluation_and_no_reward_before_actual_action():
    organism = organisms()["online_random"]
    for event in range(5):
        organism.act(Port(), event_id=event, learn=False)
    assert organism.completed == 0 and not organism.conditions
    action = organism.act(Port(), event_id=0, learn=True)
    assert not organism.conditions and float(organism.bias) == 0
    organism.observe(Feedback(0, action, 1))
    assert organism.conditions


@pytest.mark.parametrize("arm", ARMS)
def test_pickle_continuation_and_pruning_disabled_in_every_arm(arm):
    organism = organisms()[arm]
    for event in range(10):
        action = organism.act(Port(), event_id=event, learn=True)
        organism.observe(Feedback(event, action, 1))
    restored = pickle.loads(pickle.dumps(organism))
    for event in range(10, 20):
        actions = [o.act(Port(True), event_id=event, learn=True) for o in (organism, restored)]
        assert actions[0] == actions[1]
        for o, action in zip((organism, restored), actions):
            o.observe(Feedback(event, action, -1))
        assert experiment.learned_digest(organism) == experiment.learned_digest(restored)
    before = list(restored.conditions)
    restored.completed = 10000
    for c in restored.conditions.values():
        c.weight.fast = c.weight.slow = 0
    restored._prune()
    assert list(restored.conditions) == before and restored.pruned == 0
    for cid, c in restored.conditions.items():
        for slot in range(restored.slots):
            assert restored.graph.edge_by_key[(f"gate:{slot}:{cid}", f"option:{slot}",
                                                LinkType.SUR)].w is c.weight


def test_training_loop_does_not_inspect_an_opaque_organism(monkeypatch):
    class Opaque:
        @property
        def graph(self):
            raise AssertionError("coach inspected graph")

        def act(self, sensor, *, event_id, learn):
            return "h1h8"

        def observe(self, feedback):
            assert set(asdict(feedback)) == {"event_id", "action", "reward"}
    def forbidden(*args):
        raise AssertionError("offline inspection during training")
    monkeypatch.setattr(experiment, "learned_digest", forbidden)
    fens = ("k7/8/1K6/8/8/8/8/7R w - - 0 1",)
    assert experiment.train_arm(Opaque(), fens, (0, 0), deadline=float("inf")) == {
        "attempts": 2, "real_moves": 2, "mates": 2}


@pytest.fixture
def pool(tmp_path):
    directory = tmp_path / "pool"
    prepare(directory, seed=43, train=8, validation=4, test=4)
    return directory


def args(pool, output, workers=1):
    return argparse.Namespace(pool=pool, output=output, episodes=6, conditions=4,
                              seeds=[1, 2], wall_seconds=90, workers=workers)


def test_end_to_end_only_real_actions_and_never_opens_final_test(pool, tmp_path, monkeypatch):
    original_read = Path.read_bytes
    def read_bytes(path):
        assert path.name != "test.txt"
        return original_read(path)
    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    pushes, original_push = [], chess.Board.push
    def push(board, move):
        pushes.append(move.uci())
        return original_push(board, move)
    monkeypatch.setattr(chess.Board, "push", push)
    output = tmp_path / "comparison"
    source = source_identity()
    result = experiment.run(args(pool, output))
    assert len(pushes) == 2 * 3 * (6 + 4)
    assert source_identity() == source
    assert result["status"] == "complete"
    manifest = json.loads((output / "manifest.json").read_text())
    assert not manifest["final_test_opened"]
    assert len(result["results"]) == 2
    for seed in result["results"]:
        assert {arm["training"]["attempts"] for arm in seed["arms"].values()} == {6}
        assert seed["arms"]["online_random"]["representation_digest"] == seed["arms"]["fixed_random"]["representation_digest"]
    with pytest.raises(FileExistsError):
        experiment.run(args(pool, output))


def test_parallel_and_serial_have_identical_behavior(pool, tmp_path):
    serial = experiment.run(args(pool, tmp_path / "serial", workers=1))
    parallel = experiment.run(args(pool, tmp_path / "parallel", workers=2))
    assert serial["comparisons"] == parallel["comparisons"]
    for a, b in zip(serial["results"], parallel["results"]):
        for arm in ARMS:
            a["arms"][arm].pop("seconds")
            b["arms"][arm].pop("seconds")
    assert serial["results"] == parallel["results"]


def test_timeout_retains_protocol_but_never_produces_comparison(pool, tmp_path, monkeypatch):
    def timeout(*args, **kwargs):
        raise TimeoutError("test budget")
    monkeypatch.setattr(experiment, "train_arm", timeout)
    output = tmp_path / "incomplete"
    with pytest.raises(TimeoutError):
        experiment.run(args(pool, output))
    assert (output / "manifest.json").exists()
    assert (output / "failure.json").exists()
    assert not (output / "summary.json").exists()


def test_overlap_and_duplicate_seed_guards(pool, tmp_path, monkeypatch):
    request = args(pool, tmp_path / "bad")
    request.seeds = [1, 1]
    with pytest.raises(ValueError, match="unique seeds"):
        experiment.run(request)
    request.seeds = [1]
    original = experiment.load_split
    monkeypatch.setattr(experiment, "load_split", lambda directory, split: original(directory, "train"))
    with pytest.raises(ValueError, match="overlap"):
        experiment.run(request)
    assert not request.output.exists()


def test_empty_pool_and_invalid_schedule_rejected_before_play(pool, tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="nonempty"):
        experiment.schedule_indices(0, 8, 1)
    with pytest.raises(ValueError, match="positive"):
        experiment.schedule_indices(8, 0, 1)
    monkeypatch.setattr(experiment, "load_split", lambda *args: ((), "empty"))
    request = args(pool, tmp_path / "empty")
    with pytest.raises(ValueError, match="nonempty"):
        experiment.run(request)
    assert not request.output.exists()
