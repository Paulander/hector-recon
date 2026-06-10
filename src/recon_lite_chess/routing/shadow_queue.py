"""Offline prioritization for shadow stem candidates.

The queue is advisory only. It is meant to rank logged growth candidates for
review or later consolidation, not to create durable nodes during gameplay.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping


TRIGGER_PRIORITY = {
    "repeated_conversion_failure": 1,
    "reward_contract_mismatch": 2,
    "same_skill_loop_after_confirmation": 2,
    "successor_absent": 3,
    "handoff_gap": 3,
    "maintenance_needed_but_not_detected": 3,
    "high_score_conversion_failure": 4,
    "route_conflict": 5,
    "low_affordance_state": 6,
}


def _candidate_key(candidate: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(candidate.get("trigger", "unknown")),
        str(candidate.get("parent_skill", "unknown")),
        str(candidate.get("state_signature", "unknown")),
        str(candidate.get("observed_outcome", "unknown")),
    )


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            if not isinstance(payload, dict):
                raise ValueError(f"Expected JSON object in {path}:{line_no}")
            records.append(payload)
    return records


def _load_json_candidates(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected diagnostic JSON object in {path}")
    candidates = payload.get("shadow_candidates") or []
    if not isinstance(candidates, list):
        return []
    return [candidate for candidate in candidates if isinstance(candidate, dict)]


@dataclass
class ShadowStemQueueItem:
    candidate_id: str
    trigger: str
    parent_skill: str
    state_signature: str
    observed_outcome: str
    priority: int
    support: int = 1
    route_scores: dict[str, float] = field(default_factory=dict)
    packet_ids: list[str] = field(default_factory=list)
    promotion_status: str = "shadow"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ShadowStemQueue:
    schema_version: str = "shadow_stem_queue.v1"
    queue: list[ShadowStemQueueItem] = field(default_factory=list)
    trigger_counts: dict[str, int] = field(default_factory=dict)
    parent_skill_counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "queue": [item.to_dict() for item in self.queue],
            "trigger_counts": self.trigger_counts,
            "parent_skill_counts": self.parent_skill_counts,
        }


def build_shadow_stem_queue(candidates: Iterable[Mapping[str, Any]]) -> ShadowStemQueue:
    grouped: dict[tuple[str, str, str, str], ShadowStemQueueItem] = {}
    trigger_counts: Counter[str] = Counter()
    parent_counts: Counter[str] = Counter()

    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        trigger = str(candidate.get("trigger", "unknown"))
        parent_skill = str(candidate.get("parent_skill", "unknown"))
        state_signature = str(candidate.get("state_signature", "unknown"))
        observed_outcome = str(candidate.get("observed_outcome", "unknown"))
        priority = int(candidate.get("priority") or TRIGGER_PRIORITY.get(trigger, 99))
        trigger_counts[trigger] += 1
        parent_counts[parent_skill] += 1

        key = _candidate_key(candidate)
        item = grouped.get(key)
        if item is None:
            route_scores = {
                str(skill): float(score)
                for skill, score in (candidate.get("route_scores") or {}).items()
            }
            packet_id = candidate.get("packet_id")
            grouped[key] = ShadowStemQueueItem(
                candidate_id=str(candidate.get("candidate_id") or ".".join(key)),
                trigger=trigger,
                parent_skill=parent_skill,
                state_signature=state_signature,
                observed_outcome=observed_outcome,
                priority=priority,
                route_scores=route_scores,
                packet_ids=[str(packet_id)] if packet_id else [],
                promotion_status=str(candidate.get("promotion_status", "shadow")),
            )
            continue

        item.support += 1
        item.priority = min(item.priority, priority)
        packet_id = candidate.get("packet_id")
        if packet_id and str(packet_id) not in item.packet_ids:
            item.packet_ids.append(str(packet_id))

    queue = sorted(
        grouped.values(),
        key=lambda item: (
            item.priority,
            -item.support,
            item.parent_skill,
            item.state_signature,
            item.observed_outcome,
        ),
    )
    return ShadowStemQueue(
        queue=queue,
        trigger_counts={key: int(value) for key, value in trigger_counts.most_common()},
        parent_skill_counts={key: int(value) for key, value in parent_counts.most_common()},
    )


def build_shadow_stem_queue_from_files(paths: Iterable[Path]) -> ShadowStemQueue:
    candidates: list[dict[str, Any]] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.suffix == ".jsonl":
            candidates.extend(_load_jsonl(path))
        else:
            candidates.extend(_load_json_candidates(path))
    return build_shadow_stem_queue(candidates)
