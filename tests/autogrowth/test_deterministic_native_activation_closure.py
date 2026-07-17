from __future__ import annotations

from dataclasses import asdict
import json
import os
import pickle
import struct
import subprocess
import sys

import chess
import pytest

from recon_lite import Graph, LinkType, Node, NodeType

from recon_lite_chess.autogrowth.native_authority_lab import (
    NativeAuthorityLabConfig,
    load_retired_r0_build,
)
from recon_lite_chess.autogrowth.native_competence_envelope import (
    GraphNativeCompetenceEnvelope,
    NativeR0CompetenceOrganism,
    extract_active_competence_signals,
)


class ReverseIterableSet(set[str]):
    """Set whose deliberately noncanonical iterator exposes order coupling."""

    def __iter__(self):
        return iter(reversed(sorted(set.__iter__(self))))


@pytest.fixture(scope="module")
def build():
    return load_retired_r0_build(NativeAuthorityLabConfig())


def _activation_bits(value: float) -> str:
    return struct.pack("!d", float(value)).hex()


def _manifest(organism, fen: str) -> dict[str, object]:
    board = chess.Board(fen)
    actuation = organism.emit_action(board)
    assert actuation is not None
    signals = extract_active_competence_signals(organism, board, actuation)
    return {
        "actuation": asdict(actuation),
        "activation_bits": _activation_bits(actuation.activation),
        "signals": list(signals),
    }


def test_graph_reduction_is_bit_exact_under_reversed_edge_insertion() -> None:
    graph = Graph()
    graph.add_node(Node("root", NodeType.SCRIPT))
    values = {
        "a": (1.0e16, 1.0),
        "b": (1.0, 1.0),
        "c": (-1.0e16, 1.0),
        "d": (0.125, 1.0),
    }
    for identity in values:
        graph.add_node(Node(identity, NodeType.TERMINAL))
    for identity, (activation, weight) in values.items():
        graph.add_edge("root", identity, LinkType.SUB)
        graph.get_edge("root", identity, LinkType.SUB).w = weight
        graph.nodes[identity].activation.value = activation
    forward = graph.compute_z_sur("root")
    graph.edges.reverse()
    reverse = graph.compute_z_sur("root")
    assert _activation_bits(forward) == _activation_bits(reverse)


def test_native_actuation_is_bit_exact_under_reversed_set_and_edge_order(
    build,
) -> None:
    fen = build.pools.r0_train[0]
    baseline = _manifest(build.organism, fen)
    varied = pickle.loads(pickle.dumps(build.organism))
    varied.graph.graph.edges.reverse()
    varied.graph.triplet_nodes = {
        triplet_id: ReverseIterableSet(node_ids)
        for triplet_id, node_ids in reversed(
            tuple(varied.graph.triplet_nodes.items())
        )
    }
    assert _manifest(varied, fen) == baseline


def test_pickle_round_trips_preserve_complete_actuation_and_signals(build) -> None:
    fens = tuple(build.pools.r0_train[:3])
    baseline = [_manifest(build.organism, fen) for fen in fens]
    wrapper = NativeR0CompetenceOrganism(
        build.organism, GraphNativeCompetenceEnvelope()
    )
    for _round in range(3):
        wrapper = NativeR0CompetenceOrganism.loads(wrapper.dumps())
        assert [_manifest(wrapper.r0, fen) for fen in fens] == baseline


def test_three_python_hash_seeds_preserve_bit_exact_actuation_and_signals(
    build, tmp_path,
) -> None:
    payload_path = tmp_path / "organism.pkl"
    payload_path.write_bytes(NativeR0CompetenceOrganism(
        build.organism, GraphNativeCompetenceEnvelope()
    ).dumps())
    fens = tuple(build.pools.r0_train[:3])
    code = """
import json, struct, sys
from dataclasses import asdict
import chess
from recon_lite_chess.autogrowth.native_competence_envelope import (
    NativeR0CompetenceOrganism, extract_active_competence_signals,
)
wrapper = NativeR0CompetenceOrganism.loads(open(sys.argv[1], 'rb').read())
rows = []
for fen in json.loads(sys.argv[2]):
    board = chess.Board(fen)
    actuation = wrapper.r0.emit_action(board)
    signals = extract_active_competence_signals(wrapper.r0, board, actuation)
    rows.append({
        'actuation': asdict(actuation),
        'activation_bits': struct.pack('!d', actuation.activation).hex(),
        'signals': list(signals),
    })
print(json.dumps(rows, sort_keys=True, separators=(',', ':')))
"""
    outputs = []
    for hash_seed in ("1", "17", "313"):
        env = os.environ.copy()
        env["PYTHONHASHSEED"] = hash_seed
        outputs.append(subprocess.check_output(
            [sys.executable, "-c", code, str(payload_path), json.dumps(fens)],
            env=env,
            text=True,
        ).strip())
    assert outputs[0] == outputs[1] == outputs[2]
