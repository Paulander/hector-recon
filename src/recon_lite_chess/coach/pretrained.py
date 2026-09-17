"""Load the exact reviewed M1 actor; never deserialize an arbitrary checkpoint.

The bundled pickle is trusted code/data, authenticated against a code-pinned
SHA256 before decompression or unpickling. This is not a general safe-pickle API.
Each call returns an independent, still-plastic actor. It does not install a
finisher service, modify reward, freeze weights or change exploration settings.
"""
import gzip
import hashlib
from importlib.resources import files
import json
import pickle
import sys

ARTIFACT_SHA256 = "52c226628e5f8d09520c82a0b24dcb2e88ecf4e81ebb1746850df852a16000ff"


def _verified_payload(payload):
    if hashlib.sha256(payload).hexdigest() != ARTIFACT_SHA256:
        raise ValueError("bundled M1 artifact failed its pinned SHA256 check")
    return payload


def pretrained_m1_manifest():
    """Return the artifact provenance; evaluation receipts are test-only data."""
    path = files("recon_lite_chess").joinpath("checkpoints/selective_m1_seed61.json")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("artifact_sha256") != ARTIFACT_SHA256:
        raise ValueError("M1 manifest does not identify the approved artifact")
    return manifest


def load_pretrained_m1():
    """Return seed61/event2048 with the original weights, topology and RNG state.

    Python 3.12 is the validated serialization/runtime version. Other versions
    require explicit migration/parity tests rather than an implicit downgrade.
    For inference, call ``act(..., learn=False)`` through ChessFeaturePort.
    """
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("the promoted M1 artifact is validated on Python 3.12")
    from .selective import SelectiveMateOneOrganism
    path = files("recon_lite_chess").joinpath("checkpoints/selective_m1_seed61.pkl.gz")
    actor = pickle.loads(gzip.decompress(_verified_payload(path.read_bytes())))
    if type(actor) is not SelectiveMateOneOrganism or actor.completed != 2048:
        raise ValueError("unexpected bundled M1 actor identity")
    if actor.pending or actor.owner_pending is not None:
        raise ValueError("M1 artifact contains unresolved credit")
    actor.validate_ownership()
    actor.graph.validate_formal_pairs()
    return actor
