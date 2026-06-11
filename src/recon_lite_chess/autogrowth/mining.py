"""Mechanical M4 candidate mining from KRK autogrowth traces."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from .features import validate_learner_record


_BEFORE_CLUSTER_FEATURES = (
    "black_king_nearest_edge_distance",
    "white_king_to_black_king_distance",
    "white_rook_to_black_king_distance",
    "white_king_to_rook_distance",
    "rook_attacked_by_black",
    "is_check",
)

_DELTA_CLUSTER_FEATURES = (
    "black_king_nearest_edge_distance",
    "black_reply_mobility",
    "white_king_to_black_king_distance",
    "white_rook_to_black_king_distance",
    "white_king_to_rook_distance",
    "rook_attacked_by_black",
    "is_check",
    "is_stalemate",
)


@dataclass(frozen=True)
class CandidateMiningConfig:
    min_support: int = 3
    max_candidates: int = 12
    source_trace_path: str = "reports/autogrowth/krk_autogrowth_m4_traces.json"


@dataclass(frozen=True)
class CandidateMiningResult:
    config: CandidateMiningConfig
    trace_schema_version: str
    trace_digest: str
    source_summary: dict[str, Any]
    candidates: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        validate_learner_record(self.candidates)
        return {
            "schema_version": "krk_autogrowth_m4_candidates.v0",
            "config": asdict(self.config),
            "trace_schema_version": self.trace_schema_version,
            "trace_digest": self.trace_digest,
            "source_summary": self.source_summary,
            "summary": {
                "candidate_count": len(self.candidates),
                "selected_candidate_key": self.candidates[0]["candidate_key"] if self.candidates else None,
                "behavior_change_applied": False,
                "candidate_spawned": False,
                "candidate_active_in_runtime": False,
                "ready_for_m5_sandbox": bool(self.candidates),
            },
            "candidates": self.candidates,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def load_trace_artifact(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def mine_triplet_candidates_from_artifact(
    path: str | Path,
    *,
    config: CandidateMiningConfig | None = None,
) -> CandidateMiningResult:
    trace_payload = load_trace_artifact(path)
    config = config or CandidateMiningConfig(source_trace_path=str(path))
    return mine_triplet_candidates_from_records(
        records=trace_payload["records"],
        trace_schema_version=str(trace_payload.get("schema_version", "unknown")),
        trace_digest=_digest_records(trace_payload["records"]),
        source_summary=dict(trace_payload.get("summary", {})),
        config=config,
    )


def mine_triplet_candidates_from_records(
    *,
    records: Iterable[dict[str, Any]],
    trace_schema_version: str,
    trace_digest: str,
    source_summary: dict[str, Any],
    config: CandidateMiningConfig,
) -> CandidateMiningResult:
    """Group trace triplets into candidate ReCoN topology records."""

    buckets: dict[str, dict[str, Any]] = {}
    for record in records:
        validate_learner_record(record)
        bucket_key = _bucket_key(record)
        bucket = buckets.setdefault(
            bucket_key,
            {
                "records": [],
                "local_scores": [],
                "terminal_rewards": [],
                "position_indices": set(),
                "trace_keys": [],
            },
        )
        local_score = _generic_local_score(record)
        terminal_reward = float(record.get("rollout_credit", {}).get("terminal_reward", 0.0))
        bucket["records"].append(record)
        bucket["local_scores"].append(local_score)
        bucket["terminal_rewards"].append(terminal_reward)
        bucket["position_indices"].add(int(record.get("position_index", -1)))
        if len(bucket["trace_keys"]) < 8:
            bucket["trace_keys"].append(str(record.get("trace_key", "")))

    candidates = [
        _candidate_from_bucket(index=index, key=key, bucket=bucket)
        for index, (key, bucket) in enumerate(sorted(buckets.items()))
        if len(bucket["records"]) >= int(config.min_support)
    ]
    candidates.sort(
        key=lambda candidate: (
            candidate["evidence"]["mean_candidate_credit"],
            candidate["evidence"]["support_count"],
            candidate["evidence"]["position_count"],
            candidate["candidate_key"],
        ),
        reverse=True,
    )
    candidates = candidates[: int(config.max_candidates)]
    for index, candidate in enumerate(candidates):
        candidate["rank"] = index + 1
        candidate["selected_for_m5"] = index == 0
        validate_learner_record(candidate)

    return CandidateMiningResult(
        config=config,
        trace_schema_version=trace_schema_version,
        trace_digest=trace_digest,
        source_summary=source_summary,
        candidates=candidates,
    )


def _digest_records(records: list[dict[str, Any]]) -> str:
    serialized = json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _bucket_key(record: dict[str, Any]) -> str:
    before = tuple(_feature_bin(record["before_features"][name]) for name in _BEFORE_CLUSTER_FEATURES)
    action = record["action"]
    action_schema = (
        int(action["piece_type"]),
        _signed_bucket(action["file_delta"]),
        _signed_bucket(action["rank_delta"]),
        _magnitude_bucket(action["file_delta"]),
        _magnitude_bucket(action["rank_delta"]),
        int(action["gives_check"]),
        int(action["is_capture"]),
    )
    delta = tuple(_delta_sign(record["progress_deltas"][name]) for name in _DELTA_CLUSTER_FEATURES)
    return json.dumps(
        {
            "before": before,
            "action": action_schema,
            "delta": delta,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _candidate_from_bucket(*, index: int, key: str, bucket: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = bucket["records"]
    prototype_before = _mean_features(record["before_features"] for record in records)
    prototype_delta = _mean_features(record["progress_deltas"] for record in records)
    prototype_after = _mean_features(record["after_features"] for record in records)
    first_action = records[0]["action"]
    local_scores = [float(score) for score in bucket["local_scores"]]
    terminal_rewards = [float(score) for score in bucket["terminal_rewards"]]
    mean_local = mean(local_scores) if local_scores else 0.0
    mean_terminal = mean(terminal_rewards) if terminal_rewards else 0.0
    mean_credit = mean_local + mean_terminal
    support_count = len(records)
    position_count = len(bucket["position_indices"])
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    return {
        "candidate_key": f"m4_triplet_{index:04d}_{digest}",
        "rank": 0,
        "selected_for_m5": False,
        "status": "m4_mined_not_spawned",
        "source_split": "train",
        "behavior_change_applied": False,
        "candidate_active_in_runtime": False,
        "recon_topology_plan": {
            "node_types": ["TERMINAL", "ACTION", "TERMINAL", "SCRIPT"],
            "relation_types": ["SUB", "SUR", "POR", "RET"],
            "spawn_count": 1,
            "spawned_now": False,
            "m3_update_count": 0,
            "m4_event_count": 0,
        },
        "before_cluster": {
            "feature_names": list(_BEFORE_CLUSTER_FEATURES),
            "prototype": {name: prototype_before[name] for name in _BEFORE_CLUSTER_FEATURES},
        },
        "action_schema": {
            "piece_type": int(first_action["piece_type"]),
            "file_delta_sign": _signed_bucket(first_action["file_delta"]),
            "rank_delta_sign": _signed_bucket(first_action["rank_delta"]),
            "file_delta_magnitude": _magnitude_bucket(first_action["file_delta"]),
            "rank_delta_magnitude": _magnitude_bucket(first_action["rank_delta"]),
            "gives_check": int(first_action["gives_check"]),
            "is_capture": int(first_action["is_capture"]),
        },
        "after_delta_cluster": {
            "feature_names": list(_DELTA_CLUSTER_FEATURES),
            "prototype": {name: prototype_delta[name] for name in _DELTA_CLUSTER_FEATURES},
        },
        "after_cluster": {
            "feature_names": sorted(prototype_after),
            "prototype": prototype_after,
        },
        "evidence": {
            "support_count": support_count,
            "position_count": position_count,
            "mean_generic_progress_credit": mean_local,
            "mean_terminal_reward": mean_terminal,
            "mean_candidate_credit": mean_credit,
            "positive_credit_count": sum(1 for score in local_scores if score > 0.0),
            "negative_credit_count": sum(1 for score in local_scores if score < 0.0),
            "example_trace_keys": list(bucket["trace_keys"]),
        },
    }


def _generic_local_score(record: dict[str, Any]) -> float:
    delta = record["progress_deltas"]
    repetition = record.get("repetition_context", {})
    score = 0.0
    score += -0.30 * float(delta["black_king_nearest_edge_distance"])
    score += -0.05 * float(delta["black_reply_mobility"])
    score += -0.04 * float(delta["white_king_to_black_king_distance"])
    score += -0.02 * float(delta["white_rook_to_black_king_distance"])
    score += -0.08 * float(delta["rook_attacked_by_black"])
    score += 0.10 * float(delta["is_check"])
    score += -1.00 * float(delta["is_stalemate"])
    score += -0.05 * float(repetition.get("position_seen_before", 0))
    score += -0.03 * float(repetition.get("white_action_seen_before", 0))
    return score


def _mean_features(items: Iterable[dict[str, float]]) -> dict[str, float]:
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for item in items:
        for key, value in item.items():
            totals[key] = totals.get(key, 0.0) + float(value)
            counts[key] = counts.get(key, 0) + 1
    return {key: totals[key] / counts[key] for key in sorted(totals)}


def _feature_bin(value: float) -> int:
    return max(-1, min(8, int(round(float(value)))))


def _delta_sign(value: float) -> int:
    value = float(value)
    if value > 0.0:
        return 1
    if value < 0.0:
        return -1
    return 0


def _signed_bucket(value: float) -> int:
    return _delta_sign(value)


def _magnitude_bucket(value: float) -> int:
    return min(3, abs(int(round(float(value)))))
