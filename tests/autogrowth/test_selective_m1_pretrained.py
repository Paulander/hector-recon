"""Artifact identity, plasticity, legacy compatibility and full M1 parity."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import pickle

import pytest

from recon_lite import Graph, LinkType, Node, NodeType
from recon_lite_chess.coach.exercise import play_mate_one
from recon_lite_chess.coach.pretrained import (
    _verified_payload, load_pretrained_m1, pretrained_m1_manifest,
)


def test_tampered_artifact_rejected_before_deserialization():
    with pytest.raises(ValueError, match="SHA256"):
        _verified_payload(b"untrusted pickle or changed weights")


def test_actor_returns_independent_plastic_graphs_with_exact_weight_aliases():
    actor, other = load_pretrained_m1(), load_pretrained_m1()
    assert len(actor.conditions) == 12 and actor.completed == 2048
    assert actor.conditions == other.conditions
    assert not actor.reclosure_enabled and not actor.development_config.split_enabled
    for cid, condition in actor.conditions.items():
        assert condition is not other.conditions[cid]
        for slot in range(actor.slots):
            edge = actor.graph.get_edge(f"gate:{slot}:{cid}", f"option:{slot}", LinkType.SUR)
            assert edge.w is condition.weight
    old_weights = {cid: float(c.weight) for cid, c in actor.conditions.items()}
    row = play_mate_one(actor, "k7/8/1K6/8/8/8/8/7R w - - 0 1",
                        event_id=2048, learn=True)
    assert row.real_moves == 1 and actor.completed == 2049 and not actor.pending
    assert other.completed == 2048
    assert {cid: float(c.weight) for cid, c in other.conditions.items()} == old_weights
    assert {cid: float(c.weight) for cid, c in actor.conditions.items()} != old_weights


def test_promoted_checkpoint_replays_all_1512_original_actions_without_learning():
    """Reproduction, not a new fresh evaluation or independent replication."""
    manifest = pretrained_m1_manifest()
    rows = []
    for name, expected_sha in (
        ("m1_validated_receipts.json.gz", manifest["validation_panel_sha256"]),
        ("m1_scope_completion_receipts.json.gz",
         manifest["scope_completion"]["validation_panel_sha256"]),
    ):
        payload = (Path(__file__).parent / "data" / "selective_m1" / name).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == expected_sha
        rows.extend(json.loads(gzip.decompress(payload)))
    assert len(rows) == len({row["fen"] for row in rows}) == 1512
    actor = load_pretrained_m1()
    before = copy.deepcopy(actor.conditions)
    rngs = {key: value.getstate() for key, value in vars(actor).items()
            if hasattr(value, "getstate")}
    for event, expected in enumerate(rows):
        actual = play_mate_one(actor, expected["fen"], event_id=event, learn=False)
        assert actual.action == expected["action"], (expected, actual)
        assert actual.reward == 1 and actual.reason == "checkmate"
        assert actual.real_moves == 1
    assert actor.completed == 2048 and actor.conditions == before
    assert rngs == {key: value.getstate() for key, value in vars(actor).items()
                    if hasattr(value, "getstate")}
