"""Preregistered runners for native prospective evidence authority."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import copy
from dataclasses import asdict, dataclass
import gzip
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import chess

from recon_lite import FrameContext, FrameKind

from .native_competence_envelope import AvailabilityState
from .native_prospective_evidence_authority import (
    CertificationMode,
    CertificationStatus,
    NativeProspectiveCompetenceOrganism,
    ProspectiveCellCertification,
    ProspectiveCertificationConfig,
    ProspectiveEvidenceAuthority,
    SyntheticGroundedReceipt,
    SyntheticReceiptIssuer,
    synthetic_prediction,
)
from .native_trace_competence_authority import TraceNativeCompetenceOrganism


SOURCE_COMMIT = "0df59c1c78ce2ecbcb15b906eb86de2c889811d8"
REGRESSION_ARTIFACT = Path(
    "reports/autogrowth/native_authority/"
    "native_terminal_trace_historical_regression.json.gz"
)
REGRESSION_ARTIFACT_SHA256 = (
    "eb60826db7269b1fb69cd2abe21d137bb1853503cd8177e69aeb36050a77ecf4"
)
PREREGISTRATION = Path(
    "docs/autogrowth/"
    "NATIVE_PROSPECTIVE_EVIDENCE_AUTHORITY_PREREGISTRATION_20260720.md"
)
FREEZE_MANIFEST = Path(
    "reports/autogrowth/native_authority/"
    "native_prospective_evidence_authority_freeze.json"
)
SYNTHETIC_OUTPUT = Path(
    "reports/autogrowth/native_authority/"
    "native_prospective_evidence_synthetic_canary.json"
)
KRK_OUTPUT = Path(
    "reports/autogrowth/native_authority/"
    "native_prospective_evidence_krk_diagnostic.json"
)
RUNNER_PATH = Path(__file__)


@dataclass(frozen=True)
class SyntheticStreamConfig:
    generator_seed: int = 2026072101
    prefix_positive: int = 16
    prefix_negative: int = 16
    suffix_events: int = 24
    spurious_dimensions: int = 6
    minimum_discovery_support: int = 4
    candidate_capacity: int = 192
    shuffle_shift: int = 1


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hash_file(path: str | Path) -> str:
    return _hash_bytes(Path(path).read_bytes())


def _hash_json(value: Any) -> str:
    return _hash_bytes(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8"))


def _write_json(path: str | Path, value: Any) -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite canonical artifact: {target}")
    payload = json.dumps(
        value, sort_keys=True, indent=2, allow_nan=False
    ).encode("utf-8")
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(target)
    return value


def generate_synthetic_stream(
    config: SyntheticStreamConfig | None = None,
) -> dict[str, Any]:
    cfg = config or SyntheticStreamConfig()
    issuer = SyntheticReceiptIssuer()
    spurious = tuple(f"s{index}" for index in range(cfg.spurious_dimensions))
    prefix: list[SyntheticGroundedReceipt] = []
    ordinal = 0
    for index in range(cfg.prefix_positive):
        rotating_noise = (f"n{index % 4}", f"n{(index + 1) % 4}")
        prefix.append(issuer.mint(
            event_ordinal=ordinal,
            active_signal_ids=("p0", "p1", *spurious, *rotating_noise),
            observed_outcome=True,
        ))
        ordinal += 1
    for index in range(cfg.prefix_negative):
        planted_half = "p0" if index % 2 == 0 else "p1"
        prefix.append(issuer.mint(
            event_ordinal=ordinal,
            active_signal_ids=(planted_half, f"n{index % 4}", f"x{index % 5}"),
            observed_outcome=False,
        ))
        ordinal += 1
    suffix: list[SyntheticGroundedReceipt] = []
    for index in range(cfg.suffix_events):
        outcome = index % 2 == 0
        if outcome:
            active_spurious = (
                spurious[index % len(spurious)],
                spurious[(index + 2) % len(spurious)],
            )
            signals = ("p0", "p1", *active_spurious, f"z{index % 3}")
        else:
            planted_half = "p0" if (index // 2) % 2 == 0 else "p1"
            signals = (planted_half, *spurious, f"z{index % 3}")
        suffix.append(issuer.mint(
            event_ordinal=ordinal,
            active_signal_ids=signals,
            observed_outcome=outcome,
        ))
        ordinal += 1
    return {
        "config": asdict(cfg),
        "prefix": prefix,
        "suffix": suffix,
        "issuer": issuer,
    }


def _receipt_manifest(receipt: SyntheticGroundedReceipt) -> dict[str, Any]:
    return {**receipt.unsigned_manifest(), "signature": receipt.signature}


def nominate_synthetic_candidates(
    prefix: Sequence[SyntheticGroundedReceipt],
    config: SyntheticStreamConfig,
) -> dict[str, ProspectiveCellCertification]:
    all_signals = sorted({
        signal for receipt in prefix for signal in receipt.active_signal_ids
    })
    candidates = []
    for members in itertools.combinations(all_signals, 2):
        matching = [
            receipt for receipt in prefix
            if set(members).issubset(receipt.active_signal_ids)
        ]
        successes = [item for item in matching if item.observed_outcome]
        failures = [item for item in matching if not item.observed_outcome]
        if len(successes) < config.minimum_discovery_support or failures:
            continue
        candidates.append((members, matching))
    candidates.sort(key=lambda row: row[0])
    candidates = candidates[: config.candidate_capacity]
    states = {}
    frontier = max(item.event_ordinal for item in prefix)
    for index, (members, matching) in enumerate(candidates):
        cell_id = f"synthetic_context_{index:04d}"
        proposal = matching[config.minimum_discovery_support - 1]
        states[cell_id] = ProspectiveCellCertification(
            cell_id=cell_id,
            members=tuple(members),
            polarity=AvailabilityState.AVAILABLE,
            lineage_parent_id=None,
            specialization_depth=0,
            birth_event_ordinal=proposal.event_ordinal,
            certification_frontier=frontier,
            proposal_receipt_ids=(proposal.event_id,),
            discovery_receipt_ids=tuple(item.event_id for item in matching),
            discovery_support=len(matching),
            discovery_successes=len(matching),
            discovery_failures=0,
            discovery_success_lower_bound=0.0,
            discovery_failure_lower_bound=0.0,
        )
    return states


def _synthetic_arm(
    name: str,
    mode: CertificationMode,
    states: Mapping[str, ProspectiveCellCertification],
    prefix: Sequence[SyntheticGroundedReceipt],
    suffix: Sequence[SyntheticGroundedReceipt],
    issuer: SyntheticReceiptIssuer,
    config: SyntheticStreamConfig,
) -> dict[str, Any]:
    authority = ProspectiveEvidenceAuthority(
        ProspectiveCertificationConfig(
            mode=mode,
            outcome_shuffle_shift=config.shuffle_shift,
        ),
        copy.deepcopy(dict(states)),
    )
    prefix_events = tuple(issuer.validate(item) for item in prefix)
    immediate_mature = ()
    if mode is CertificationMode.LEGACY_SAME_LEDGER:
        immediate_mature = authority.legacy_certify(prefix_events)
    immediate_manifest = copy.deepcopy(authority.to_manifest())
    virtual_before = copy.deepcopy(authority.to_manifest())
    virtual_prediction = authority.predict(
        trace_identity="synthetic:virtual:isolation",
        active_signal_ids=("p0", "p1"),
        policy_response=True,
        frame_kind=FrameKind.VIRTUAL,
    )
    virtual_isolation_exact = authority.to_manifest() == virtual_before
    prequential = []
    suffix_events = tuple(issuer.validate(item) for item in suffix)
    if mode is CertificationMode.PROSPECTIVE_OUTCOME_SHUFFLED:
        for receipt in suffix:
            prediction = synthetic_prediction(authority, receipt)
            prequential.append({
                "receipt_id": receipt.event_id,
                "classification": prediction.classification.to_manifest(),
            })
        emissions = authority.consume_frozen_shuffled_batch(suffix_events)
    else:
        emissions = []
        for receipt, event in zip(suffix, suffix_events, strict=True):
            prediction = synthetic_prediction(authority, receipt)
            prequential.append({
                "receipt_id": receipt.event_id,
                "classification": prediction.classification.to_manifest(),
            })
            emissions.append(authority.consume(event))
    final = authority.to_manifest()
    roundtrip = pickle_roundtrip_manifest(authority)
    mature_ids = tuple(sorted(
        cell.cell_id for cell in authority.cells.values()
        if cell.status is CertificationStatus.MATURE
    ))
    revoked_ids = tuple(sorted(
        cell.cell_id for cell in authority.cells.values()
        if cell.status is CertificationStatus.REVOKED
    ))
    planted_ids = tuple(sorted(
        cell.cell_id for cell in authority.cells.values()
        if cell.members == ("p0", "p1")
    ))
    spurious_ids = tuple(sorted(
        cell.cell_id for cell in authority.cells.values()
        if cell.members != ("p0", "p1")
    ))
    return {
        "name": name,
        "mode": mode.value,
        "immediate_mature_ids": list(immediate_mature),
        "immediate_mature_count": len(immediate_mature),
        "immediate_manifest": immediate_manifest,
        "prequential": prequential,
        "emissions": [item.to_manifest() for item in emissions],
        "final_manifest": final,
        "final_mature_ids": list(mature_ids),
        "final_revoked_ids": list(revoked_ids),
        "planted_candidate_ids": list(planted_ids),
        "planted_mature": bool(set(planted_ids).intersection(mature_ids)),
        "spurious_candidate_count": len(spurious_ids),
        "spurious_immediate_mature_count": len(
            set(spurious_ids).intersection(immediate_mature)
        ),
        "spurious_final_mature_count": len(
            set(spurious_ids).intersection(mature_ids)
        ),
        "serialization_exact": roundtrip == final,
        "virtual_prediction": virtual_prediction.to_manifest(),
        "virtual_isolation_exact": virtual_isolation_exact,
        "deficit_manifest": authority.deficit_manifest(),
    }


def pickle_roundtrip_manifest(authority: ProspectiveEvidenceAuthority) -> dict[str, Any]:
    import pickle
    restored = pickle.loads(
        pickle.dumps(authority, protocol=pickle.HIGHEST_PROTOCOL)
    )
    return restored.to_manifest()


def run_synthetic_canary(
    config: SyntheticStreamConfig | None = None,
    *,
    output: str | Path = SYNTHETIC_OUTPUT,
) -> dict[str, Any]:
    cfg = config or SyntheticStreamConfig()
    stream = generate_synthetic_stream(cfg)
    prefix = stream["prefix"]
    suffix = stream["suffix"]
    issuer = stream["issuer"]
    states = nominate_synthetic_candidates(prefix, cfg)
    if not any(cell.members == ("p0", "p1") for cell in states.values()):
        raise RuntimeError("planted persistent conjunction was not nominated")
    arms = {
        "prospective": _synthetic_arm(
            "prospective", CertificationMode.PROSPECTIVE,
            states, prefix, suffix, issuer, cfg,
        ),
        "legacy_same_ledger": _synthetic_arm(
            "legacy_same_ledger", CertificationMode.LEGACY_SAME_LEDGER,
            states, prefix, suffix, issuer, cfg,
        ),
        "prospective_shuffled": _synthetic_arm(
            "prospective_shuffled",
            CertificationMode.PROSPECTIVE_OUTCOME_SHUFFLED,
            states, prefix, suffix, issuer, cfg,
        ),
    }
    prospective = arms["prospective"]
    legacy = arms["legacy_same_ledger"]
    shuffled = arms["prospective_shuffled"]
    prospective_cells = prospective["final_manifest"]["cells"]
    gates = {
        "legacy_admits_spurious": legacy["spurious_immediate_mature_count"] > 0,
        "prospective_zero_immediate_maturity": (
            prospective["immediate_mature_count"] == 0
        ),
        "zero_pre_frontier_certification": all(
            not set(row["certification_receipt_ids"]).intersection(
                row["discovery_receipt_ids"]
            )
            for row in prospective_cells
        ),
        "zero_proposal_event_certification": all(
            not set(row["certification_receipt_ids"]).intersection(
                row["proposal_receipt_ids"]
            )
            for row in prospective_cells
        ),
        "planted_matures_prospectively": prospective["planted_mature"],
        "spurious_authority_closed": (
            prospective["spurious_final_mature_count"] == 0
        ),
        "prospective_exceeds_shuffled": (
            int(prospective["planted_mature"])
            > int(shuffled["planted_mature"])
        ),
        "serialization_exact": all(
            arm["serialization_exact"] for arm in arms.values()
        ),
        "no_virtual_certification": all(
            arm["final_manifest"]["audit"]["virtual_predictions"] == 0
            and arm["virtual_isolation_exact"]
            for arm in arms.values()
        ),
        "all_mature_lawful": all(
            row["prospective_successes"] >= 4
            and row["prospective_contradictions"] == 0
            for row in prospective_cells
            if row["status"] == CertificationStatus.MATURE.value
        ),
    }
    result = {
        "schema_version": "native_prospective_synthetic_canary.v1",
        "development_only": True,
        "generic_non_chess": True,
        "config": asdict(cfg),
        "stream_digest": _hash_json({
            "prefix": [_receipt_manifest(item) for item in prefix],
            "suffix": [_receipt_manifest(item) for item in suffix],
        }),
        "prefix_count": len(prefix),
        "suffix_count": len(suffix),
        "candidate_count": len(states),
        "candidate_digest": _hash_json([
            cell.to_manifest() for cell in states.values()
        ]),
        "arms": arms,
        "gates": gates,
        "passed": all(gates.values()),
        "stop_reason": (
            "synthetic_discriminator_passed"
            if all(gates.values()) else "synthetic_discriminator_failed"
        ),
    }
    return _write_json(output, result)


def _load_regression_result() -> dict[str, Any]:
    if _hash_file(REGRESSION_ARTIFACT) != REGRESSION_ARTIFACT_SHA256:
        raise RuntimeError("completed regression artifact changed")
    return json.load(gzip.open(REGRESSION_ARTIFACT, "rt"))


def _load_source(item: Mapping[str, Any]) -> TraceNativeCompetenceOrganism:
    path = Path(str(item["path"]))
    compressed = path.read_bytes()
    if _hash_bytes(compressed) != item["compressed_sha256"]:
        raise RuntimeError("source organism compressed hash mismatch")
    raw = gzip.decompress(compressed)
    if _hash_bytes(raw) != item["uncompressed_sha256"]:
        raise RuntimeError("source organism raw hash mismatch")
    organism = TraceNativeCompetenceOrganism.loads(raw)
    if organism.continuation_digest_v3() != item["continuation_v3_sha256"]:
        raise RuntimeError("source organism V3 mismatch")
    return organism


def _pattern_manifest(organism: TraceNativeCompetenceOrganism) -> list[dict[str, Any]]:
    rows = []
    for cell in sorted(
        organism.envelope.cells.values(), key=lambda item: item.cell_id
    ):
        rows.append({
            "cell_id": cell.cell_id,
            "members": list(cell.members),
            "polarity": None if cell.polarity is None else cell.polarity.value,
            "state": cell.state.name,
            "lineage_parent_id": cell.lineage_parent_id,
            "specialization_depth": cell.specialization_depth,
            "specialization_request_ordinal": cell.specialization_request_ordinal,
            "specialization_proposal_ordinal": cell.specialization_proposal_ordinal,
            "evidence_keys": list(cell.evidence_keys),
            "support": cell.support,
        })
    return rows


def build_freeze_manifest() -> dict[str, Any]:
    regression = _load_regression_result()
    local = sorted(
        (
            item["source_artifact"] for item in regression["organisms"]
            if item["arm"] == "local_contrast_specialization"
        ),
        key=lambda item: item["ordinal"],
    )
    if len(local) != 32:
        raise RuntimeError("expected all 32 local source organisms")
    pattern_rows = []
    for item in local:
        organism = _load_source(item)
        manifest = _pattern_manifest(organism)
        pattern_rows.append({
            "ordinal": item["ordinal"],
            "genome_seed": item["genome_seed"],
            "source_artifact": dict(item),
            "pattern_count": len(manifest),
            "pattern_digest": _hash_json(manifest),
            "depth_one_count": sum(
                row["specialization_depth"] == 1 for row in manifest
            ),
            "mature_depth_one_count": sum(
                row["specialization_depth"] == 1
                and row["state"] == "MATURE"
                for row in manifest
            ),
        })
    mature_children = sum(
        row["mature_depth_one_count"] for row in pattern_rows
    )
    if mature_children != 34:
        raise RuntimeError(
            f"historical specialization-child count changed: {mature_children}"
        )
    synthetic = generate_synthetic_stream()
    candidates = nominate_synthetic_candidates(
        synthetic["prefix"], SyntheticStreamConfig()
    )
    manifest = {
        "schema_version": "native_prospective_evidence_authority_freeze.v1",
        "source_commit": SOURCE_COMMIT,
        "development_only": True,
        "allowed_data": [
            "generic_synthetic_stream",
            "already_viewed_historical_regression_artifact",
            "frozen_local_contrast_source_organisms",
        ],
        "forbidden_data": [
            "fresh", "R1", "retired_65", "unopened_regression",
        ],
        "source_hashes": {
            str(RUNNER_PATH): _hash_file(RUNNER_PATH),
            "src/recon_lite_chess/autogrowth/native_prospective_evidence_authority.py":
                _hash_file(
                    "src/recon_lite_chess/autogrowth/"
                    "native_prospective_evidence_authority.py"
                ),
            str(PREREGISTRATION): _hash_file(PREREGISTRATION),
            "tests/autogrowth/test_native_prospective_evidence_authority.py":
                _hash_file(
                    "tests/autogrowth/"
                    "test_native_prospective_evidence_authority.py"
                ),
            str(REGRESSION_ARTIFACT): REGRESSION_ARTIFACT_SHA256,
        },
        "synthetic": {
            "config": asdict(SyntheticStreamConfig()),
            "prefix_count": len(synthetic["prefix"]),
            "suffix_count": len(synthetic["suffix"]),
            "stream_digest": _hash_json({
                "prefix": [
                    _receipt_manifest(item) for item in synthetic["prefix"]
                ],
                "suffix": [
                    _receipt_manifest(item) for item in synthetic["suffix"]
                ],
            }),
            "candidate_count": len(candidates),
            "candidate_digest": _hash_json([
                cell.to_manifest() for cell in candidates.values()
            ]),
        },
        "krk": {
            "regression_row_order_commitment": regression["row_order_commitment"],
            "reference_rows_digest": _hash_json(regression["reference_rows"]),
            "organisms": pattern_rows,
            "arms": [
                "prospective",
                "legacy_same_ledger",
                "prospective_outcome_shuffled",
            ],
        },
        "gates": {
            "synthetic": [
                "legacy_admits_spurious",
                "prospective_zero_immediate_maturity",
                "zero_pre_frontier_certification",
                "zero_proposal_event_certification",
                "planted_matures_prospectively",
                "spurious_authority_closed",
                "prospective_exceeds_shuffled",
                "serialization_exact",
                "no_virtual_certification",
                "all_mature_lawful",
            ],
            "krk": [
                "zero_pre_frontier_certification",
                "zero_same_event_proposal_certification",
                "zero_virtual_certification",
                "zero_maturity_below_four",
                "all_final_mature_lawful",
                "all_mature_contradictions_graph_revoked",
                "connected_nonzero_mature_competence",
                "connected_exceeds_shuffled_paired_coverage",
                "serialization_and_authority",
            ],
        },
        "stop_rule": (
            "close after synthetic and already-viewed retrospective diagnostic; "
            "no rescue, fresh data, R1, retired-65, tuning, or new mechanism"
        ),
    }
    return _write_json(FREEZE_MANIFEST, manifest)


def _metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts = {
        "tp": 0, "fp": 0, "positive_abstention": 0,
        "safe_abstention": 0, "refuted_positive": 0, "refuted_negative": 0,
    }
    for row in rows:
        state = row["classification"]["state"]
        actual = bool(row["actual_completion"])
        if state == AvailabilityState.AVAILABLE.value:
            counts["tp" if actual else "fp"] += 1
        elif state == AvailabilityState.REFUTED.value:
            counts["refuted_positive" if actual else "refuted_negative"] += 1
        else:
            counts["positive_abstention" if actual else "safe_abstention"] += 1
    return {
        **counts,
        "safe_narrow": counts["tp"] > 0 and counts["fp"] == 0,
        "deployable_tp": counts["tp"] if counts["fp"] == 0 else 0,
    }


def _evaluate_krk_organism(arg: Mapping[str, Any]) -> dict[str, Any]:
    source_item = arg["source_artifact"]
    reference_rows = arg["reference_rows"]
    source = _load_source(source_item)
    frontier = source._next_event_ordinal - 1
    prospective = NativeProspectiveCompetenceOrganism.from_frozen_patterns(
        source,
        config=ProspectiveCertificationConfig(CertificationMode.PROSPECTIVE),
        certification_frontier=frontier,
        reset_historical_authority=True,
    )
    legacy = NativeProspectiveCompetenceOrganism.from_frozen_patterns(
        source,
        config=ProspectiveCertificationConfig(
            CertificationMode.LEGACY_SAME_LEDGER
        ),
        certification_frontier=frontier,
        reset_historical_authority=False,
    )
    shuffled = NativeProspectiveCompetenceOrganism.from_frozen_patterns(
        source,
        config=ProspectiveCertificationConfig(
            CertificationMode.PROSPECTIVE_OUTCOME_SHUFFLED
        ),
        certification_frontier=frontier,
        reset_historical_authority=True,
    )
    pattern_digests = {
        name: _hash_json([
            {
                "cell_id": cell.cell_id,
                "members": list(cell.members),
                "polarity": cell.polarity.value,
                "lineage_parent_id": cell.lineage_parent_id,
                "specialization_depth": cell.specialization_depth,
            }
            for cell in sorted(
                organism.authority.cells.values(),
                key=lambda item: item.cell_id,
            )
        ])
        for name, organism in {
            "prospective": prospective,
            "legacy": legacy,
            "shuffled": shuffled,
        }.items()
    }
    if len(set(pattern_digests.values())) != 1:
        raise RuntimeError("identical-pattern arm contract failed")
    before = {
        "prospective": prospective.continuation_digest(),
        "legacy": legacy.continuation_digest(),
        "shuffled": shuffled.continuation_digest(),
    }
    immediate = {
        name: {
            "mature": sum(
                cell.status is CertificationStatus.MATURE
                for cell in organism.authority.cells.values()
            ),
            "provisional": sum(
                cell.status is CertificationStatus.PROVISIONAL
                for cell in organism.authority.cells.values()
            ),
            "revoked": sum(
                cell.status is CertificationStatus.REVOKED
                for cell in organism.authority.cells.values()
            ),
        }
        for name, organism in {
            "prospective": prospective,
            "legacy": legacy,
            "shuffled": shuffled,
        }.items()
    }
    terminal = prospective.base.completion_terminal()
    arm_rows = {"prospective": [], "legacy": [], "shuffled": []}
    shuffled_receipts = []
    parity_failures = []
    for reference in reference_rows:
        row_index = int(reference["row_index"])
        board = chess.Board(str(reference["fen"]))
        frame = FrameContext(
            f"trace-regression-real:{row_index}",
            FrameKind.REAL,
            values={"board": board},
        )
        actuation, trace = prospective.base.r0.emit_action_with_trace(frame)
        if actuation is None or trace is None:
            raise RuntimeError("R0 failed to emit viewed regression trace")
        actual_actuation = asdict(actuation)
        if actual_actuation != reference["actuation"]:
            parity_failures.append({
                "row_index": row_index, "field": "GraphActuation",
            })
        if list(trace.ordered_signal_identities) != reference[
            "ordered_signal_identities"
        ]:
            parity_failures.append({
                "row_index": row_index, "field": "ordered_signal_identities",
            })
        if trace.digest() != reference["trace_digest"]:
            parity_failures.append({
                "row_index": row_index, "field": "trace_digest",
            })
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(actuation.move_uci))
        if successor.is_checkmate() != bool(reference["actual_completion"]):
            parity_failures.append({
                "row_index": row_index, "field": "actual_completion",
            })
        predictions = {
            "prospective": prospective.predict_real_trace(trace),
            "legacy": legacy.predict_real_trace(trace),
            "shuffled": shuffled.predict_real_trace(trace),
        }
        trace_row = {
            "actuation": actual_actuation,
            "ordered_signal_identities": list(trace.ordered_signal_identities),
            "terminal_signals": [
                asdict(signal) for signal in trace.terminal_signals
            ],
            "trace_digest": trace.digest(),
        }
        receipt = terminal.mint(trace, board, successor)
        prospective_emission = prospective.observe_grounded(receipt)
        legacy_emission = legacy.observe_grounded(receipt)
        shuffled_receipts.append(receipt)
        for name, emission in {
            "prospective": prospective_emission,
            "legacy": legacy_emission,
        }.items():
            arm_rows[name].append({
                "row_index": row_index,
                "fen": reference["fen"],
                "actual_completion": reference["actual_completion"],
                "prediction": predictions[name].to_manifest(),
                "classification": predictions[name].classification.to_manifest(),
                "receipt": receipt.canonical_manifest(),
                "receipt_digest": receipt.digest(),
                **trace_row,
                "certification": emission.to_manifest(),
            })
        arm_rows["shuffled"].append({
            "row_index": row_index,
            "fen": reference["fen"],
            "actual_completion": reference["actual_completion"],
            "prediction": predictions["shuffled"].to_manifest(),
            "classification": predictions["shuffled"].classification.to_manifest(),
            "receipt": receipt.canonical_manifest(),
            "receipt_digest": receipt.digest(),
            **trace_row,
            "certification": None,
        })
        if len(shuffled_receipts) >= 2:
            target = shuffled_receipts[-2]
            source_receipt = shuffled_receipts[-1]
            emission = shuffled.observe_grounded_shuffled(
                target, source_receipt
            )
            arm_rows["shuffled"][-2]["certification"] = emission.to_manifest()
    if shuffled_receipts:
        emission = shuffled.observe_grounded_shuffled(
            shuffled_receipts[-1], shuffled_receipts[0]
        )
        arm_rows["shuffled"][-1]["certification"] = emission.to_manifest()

    final_rows = {}
    for name, organism in {
        "prospective": prospective,
        "legacy": legacy,
        "shuffled": shuffled,
    }.items():
        rows = []
        for reference in reference_rows:
            classification = organism.authority.classify(
                reference["ordered_signal_identities"],
                policy_response=True,
            )
            rows.append({
                "row_index": reference["row_index"],
                "actual_completion": reference["actual_completion"],
                "classification": classification.to_manifest(),
            })
        final_rows[name] = rows
    final_metrics = {
        name: _metrics(rows) for name, rows in final_rows.items()
    }
    prequential_metrics = {
        name: _metrics(rows) for name, rows in arm_rows.items()
    }
    dream_isolation = {}
    dream_board = chess.Board(str(reference_rows[0]["fen"]))
    for name, organism in {
        "prospective": prospective,
        "legacy": legacy,
        "shuffled": shuffled,
    }.items():
        dream_before = organism.continuation_digest()
        session = organism.dream_session()
        dream_result = session.request(FrameContext(
            f"prospective-diagnostic-virtual:{source_item['ordinal']}:{name}",
            FrameKind.VIRTUAL,
            values={"board": dream_board},
        ))
        session.close()
        dream_isolation[name] = {
            "before_digest": dream_before,
            "after_digest": organism.continuation_digest(),
            "exact": organism.continuation_digest() == dream_before,
            "certification_support_added": dream_result[
                "certification_support_added"
            ],
            "classification": dream_result[
                "classification"
            ].to_manifest(),
        }
    roundtrip = {}
    after = {}
    cell_rows = {}
    for name, organism in {
        "prospective": prospective,
        "legacy": legacy,
        "shuffled": shuffled,
    }.items():
        manifest = organism.continuation_manifest()
        restored = NativeProspectiveCompetenceOrganism.loads(organism.dumps())
        roundtrip[name] = restored.continuation_manifest() == manifest
        after[name] = organism.continuation_digest()
        cell_rows[name] = [
            cell.to_manifest() for cell in sorted(
                organism.authority.cells.values(),
                key=lambda item: item.cell_id,
            )
        ]
    authority_audits = {
        name: asdict(organism.authority.audit)
        for name, organism in {
            "prospective": prospective,
            "legacy": legacy,
            "shuffled": shuffled,
        }.items()
    }
    return {
        "ordinal": source_item["ordinal"],
        "genome_seed": source_item["genome_seed"],
        "source_artifact": dict(source_item),
        "frontier": frontier,
        "pattern_digest": next(iter(pattern_digests.values())),
        "pattern_digests_by_arm": pattern_digests,
        "parity_failures": parity_failures,
        "immediate": immediate,
        "prequential_rows": arm_rows,
        "prequential_metrics": prequential_metrics,
        "final_rows_same_tape_descriptive": final_rows,
        "final_metrics_same_tape_descriptive": final_metrics,
        "cell_rows": cell_rows,
        "authority_audits": authority_audits,
        "dream_isolation": dream_isolation,
        "before_digests": before,
        "after_digests": after,
        "serialization_exact": roundtrip,
    }


def _paired_coverage(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    wins = losses = ties = 0
    paired = []
    for row in rows:
        left = row["final_metrics_same_tape_descriptive"]["prospective"][
            "deployable_tp"
        ]
        right = row["final_metrics_same_tape_descriptive"]["shuffled"][
            "deployable_tp"
        ]
        if left > right:
            wins += 1
            outcome = "connected"
        elif left < right:
            losses += 1
            outcome = "shuffled"
        else:
            ties += 1
            outcome = "tie"
        paired.append({
            "ordinal": row["ordinal"],
            "prospective_deployable_tp": left,
            "shuffled_deployable_tp": right,
            "outcome": outcome,
        })
    return {
        "wins": wins, "losses": losses, "ties": ties, "rows": paired,
    }


def run_krk_diagnostic(
    *,
    output: str | Path = KRK_OUTPUT,
    max_workers: int = 4,
) -> dict[str, Any]:
    freeze = json.loads(FREEZE_MANIFEST.read_text())
    for path, digest in freeze["source_hashes"].items():
        if _hash_file(path) != digest:
            raise RuntimeError(f"frozen source changed: {path}")
    synthetic = json.loads(SYNTHETIC_OUTPUT.read_text())
    if not synthetic["passed"]:
        raise RuntimeError("synthetic discriminator did not authorize KRK diagnostic")
    regression = _load_regression_result()
    local = sorted(
        (
            item["source_artifact"] for item in regression["organisms"]
            if item["arm"] == "local_contrast_specialization"
        ),
        key=lambda item: item["ordinal"],
    )
    args = [
        {
            "source_artifact": item,
            "reference_rows": regression["reference_rows"],
        }
        for item in local
    ]
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        organisms = list(executor.map(_evaluate_krk_organism, args))
    organisms.sort(key=lambda item: item["ordinal"])
    paired = _paired_coverage(organisms)
    prospective_cells = [
        cell
        for organism in organisms
        for cell in organism["cell_rows"]["prospective"]
    ]
    shuffled_cells = [
        cell
        for organism in organisms
        for cell in organism["cell_rows"]["shuffled"]
    ]
    prospective_final_mature = [
        cell for cell in prospective_cells
        if cell["status"] == CertificationStatus.MATURE.value
    ]
    prospective_revoked = [
        cell for cell in prospective_cells
        if cell["status"] == CertificationStatus.REVOKED.value
    ]
    former_mature_children = sum(
        row["mature_depth_one_count"]
        for row in freeze["krk"]["organisms"]
    )
    surviving_children = sum(
        cell["status"] == CertificationStatus.MATURE.value
        and cell["specialization_depth"] == 1
        for cell in prospective_cells
    )
    gates = {
        "zero_pre_frontier_certification": all(
            not set(cell["certification_receipt_ids"]).intersection(
                cell["discovery_receipt_ids"]
            )
            for cell in prospective_cells + shuffled_cells
        ),
        "zero_same_event_proposal_certification": all(
            not set(cell["certification_receipt_ids"]).intersection(
                cell["proposal_receipt_ids"]
            )
            for cell in prospective_cells + shuffled_cells
        ),
        "zero_virtual_certification": all(
            organism["authority_audits"][arm]["virtual_predictions"] == 0
            for organism in organisms
            for arm in ("prospective", "legacy", "shuffled")
        ),
        "zero_maturity_below_four": all(
            all(
                transition["prospective_successes"] >= 4
                for transition in cell["transitions"]
                if transition["transition"] == "PROVISIONAL_TO_MATURE"
            )
            for cell in prospective_cells + shuffled_cells
        ),
        "all_final_mature_lawful": all(
            cell["prospective_successes"] >= 4
            and cell["prospective_contradictions"] == 0
            for cell in prospective_final_mature
        ),
        "all_mature_contradictions_graph_revoked": all(
            set(row["certification"]["revoked_cell_ids"])
            == set(row["certification"]["graph_local_revocation_ids"])
            for organism in organisms
            for row in organism["prequential_rows"]["prospective"]
            if row["certification"]["revoked_cell_ids"]
        ),
        "connected_nonzero_mature_competence": bool(prospective_final_mature),
        "connected_exceeds_shuffled_paired_coverage": (
            paired["wins"] > paired["losses"]
        ),
        "serialization_and_authority": all(
            not organism["parity_failures"]
            and all(organism["serialization_exact"].values())
            and all(
                row["exact"] and row["certification_support_added"] == 0
                for row in organism["dream_isolation"].values()
            )
            for organism in organisms
        ),
    }
    deficits = [
        cell["prospective_successes"]
        for cell in prospective_cells
        if cell["status"] == CertificationStatus.PROVISIONAL.value
    ]
    if not gates["connected_nonzero_mature_competence"]:
        stop_reason = "prospective_evidence_starvation"
    elif not gates["connected_exceeds_shuffled_paired_coverage"]:
        stop_reason = "prospective_certification_not_superior_to_shuffle"
    elif all(gates.values()):
        stop_reason = "prospective_evidence_authority_supported_on_viewed_development"
    else:
        stop_reason = "prospective_authority_or_lifecycle_gate_failed"
    result = {
        "schema_version": "native_prospective_evidence_krk_diagnostic.v1",
        "development_only": True,
        "retrospective_prospective_certification": True,
        "heldout_generalization_claim": False,
        "fresh_accessed": False,
        "r1_accessed": False,
        "retired_65_accessed": False,
        "unopened_pool_accessed": False,
        "source_commit": SOURCE_COMMIT,
        "freeze_manifest_sha256": _hash_file(FREEZE_MANIFEST),
        "synthetic_artifact_sha256": _hash_file(SYNTHETIC_OUTPUT),
        "organisms": organisms,
        "paired_correctly_certified_coverage": paired,
        "summary": {
            "prospective_final_mature_count": len(prospective_final_mature),
            "prospective_revoked_count": len(prospective_revoked),
            "former_mature_specialization_children": former_mature_children,
            "surviving_specialization_children": surviving_children,
            "depth_zero_survivors": sum(
                cell["specialization_depth"] == 0
                for cell in prospective_final_mature
            ),
            "depth_one_survivors": sum(
                cell["specialization_depth"] == 1
                for cell in prospective_final_mature
            ),
            "evidence_starvation_support_histogram": {
                str(value): deficits.count(value)
                for value in sorted(set(deficits))
            },
            "prequential_totals": {
                arm: {
                    key: sum(
                        organism["prequential_metrics"][arm][key]
                        for organism in organisms
                    )
                    for key in (
                        "tp", "fp", "positive_abstention", "safe_abstention",
                        "refuted_positive", "refuted_negative", "deployable_tp",
                    )
                }
                for arm in ("prospective", "legacy", "shuffled")
            },
            "final_same_tape_descriptive_totals": {
                arm: {
                    key: sum(
                        organism["final_metrics_same_tape_descriptive"][arm][key]
                        for organism in organisms
                    )
                    for key in (
                        "tp", "fp", "positive_abstention", "safe_abstention",
                        "refuted_positive", "refuted_negative", "deployable_tp",
                    )
                }
                for arm in ("prospective", "legacy", "shuffled")
            },
        },
        "gates": gates,
        "passed": all(gates.values()),
        "stop_reason": stop_reason,
    }
    return _write_json(output, result)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("freeze", "synthetic", "krk"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.action == "freeze":
        build_freeze_manifest()
    elif args.action == "synthetic":
        run_synthetic_canary()
    else:
        run_krk_diagnostic(max_workers=args.workers)


if __name__ == "__main__":
    main()
