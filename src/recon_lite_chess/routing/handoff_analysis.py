"""Aggregate ReCoN handoff diagnostics into non-causal failure motifs.

The analyzer consumes JSON emitted by ``scripts/test_krk_landmark_progress.py``
and optional shadow-candidate JSONL files. It does not influence runtime
routing; it turns trace records into compact summaries for deciding the next
training or topology-growth experiment.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


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


def _counter_dict(counter: Counter) -> dict[str, int]:
    return {str(key): int(value) for key, value in counter.most_common()}


def _phase_status_key(packet: Mapping[str, Any]) -> str:
    return f"{packet.get('phase', 'unknown')}:{packet.get('status', 'unknown')}"


def _packet_key(packet: Mapping[str, Any]) -> tuple[str, str, str]:
    evidence = packet.get("evidence_terms") if isinstance(packet.get("evidence_terms"), dict) else {}
    return (
        str(packet.get("from_skill") or "unknown"),
        str(packet.get("phase") or "unknown"),
        str(evidence.get("fen") or ""),
    )


def _handoff_context_key(packet: Mapping[str, Any]) -> tuple[str, str]:
    evidence = packet.get("evidence_terms") if isinstance(packet.get("evidence_terms"), dict) else {}
    return (
        str(packet.get("from_skill") or "unknown"),
        str(evidence.get("fen") or ""),
    )


def _add_counter_values(counter: Counter, payload: Mapping[str, Any] | None) -> None:
    if not isinstance(payload, Mapping):
        return
    for key, value in payload.items():
        counter[str(key)] += int(value or 0)


@dataclass
class HandoffAnalysis:
    """Compact aggregate of one or more handoff diagnostic outputs."""

    schema_version: str = "handoff_analysis.v1"
    source_files: list[str] = field(default_factory=list)
    total_evaluated: int = 0
    no_move: int = 0
    one_ply_status_counts: dict[str, int] = field(default_factory=dict)
    conversion_status_counts: dict[str, int] = field(default_factory=dict)
    playout_counts: dict[str, int] = field(default_factory=dict)
    packet_phase_status_counts: dict[str, int] = field(default_factory=dict)
    post_reply_failure_count: int = 0
    successor_selected_skill_counts: dict[str, int] = field(default_factory=dict)
    failed_successor_skill_counts: dict[str, int] = field(default_factory=dict)
    failure_class_counts: dict[str, int] = field(default_factory=dict)
    selected_successor_outcome_counts: dict[str, int] = field(default_factory=dict)
    failure_class_by_successor_counts: dict[str, int] = field(default_factory=dict)
    contract_mismatch_count: int = 0
    contract_mismatch_by_successor_counts: dict[str, int] = field(default_factory=dict)
    visible_eligible_successor_counts: dict[str, int] = field(default_factory=dict)
    handoff_gap_count: int = 0
    route_conflict_count: int = 0
    shadow_trigger_counts: dict[str, int] = field(default_factory=dict)
    shadow_parent_skill_counts: dict[str, int] = field(default_factory=dict)
    top_failure_motifs: list[dict[str, Any]] = field(default_factory=list)
    recommended_next_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        lines = [
            "# KRK Handoff Analysis",
            "",
            f"- Sources: {len(self.source_files)}",
            f"- Total evaluated: {self.total_evaluated}",
            f"- No move: {self.no_move}",
            f"- One-ply statuses: {self.one_ply_status_counts}",
            f"- Conversion statuses: {self.conversion_status_counts}",
            f"- Playouts: {self.playout_counts}",
            f"- Handoff gaps: {self.handoff_gap_count}",
            f"- Route conflicts: {self.route_conflict_count}",
            "",
            "## Successor Skills",
            "",
        ]
        if self.successor_selected_skill_counts:
            for skill, count in self.successor_selected_skill_counts.items():
                lines.append(f"- `{skill}` selected {count} times")
        else:
            lines.append("- No successor skill evidence found.")

        lines.extend(["", "## Failure Motifs", ""])
        if self.failure_class_counts:
            lines.append("Failure classes:")
            for cls, count in self.failure_class_counts.items():
                lines.append(f"- `{cls}`: {count}")
            lines.append("")
        if self.top_failure_motifs:
            for motif in self.top_failure_motifs:
                lines.append(
                    "- "
                    f"`{motif['from_skill']}` via `{motif['successor_skill']}` "
                    f"resulted in `{motif['outcome']}` "
                    f"(count={motif['count']}, gap={motif['handoff_gap']}, "
                    f"conflict={motif['route_conflict']})"
                )
        else:
            lines.append("- No failed post-reply or conversion motifs found.")

        if self.selected_successor_outcome_counts:
            lines.extend(["", "Selected successor by outcome:"])
            for key, count in self.selected_successor_outcome_counts.items():
                lines.append(f"- `{key}`: {count}")

        if self.contract_mismatch_count:
            lines.extend(["", "Contract mismatches:"])
            lines.append(f"- Total selected despite contract mismatch: {self.contract_mismatch_count}")
            for skill, count in self.contract_mismatch_by_successor_counts.items():
                lines.append(f"- `{skill}`: {count}")

        if self.visible_eligible_successor_counts:
            lines.extend(["", "Visible eligible successors:"])
            for skill, count in self.visible_eligible_successor_counts.items():
                lines.append(f"- `{skill}`: {count}")

        lines.extend(["", "## Shadow Candidates", ""])
        if self.shadow_trigger_counts:
            for trigger, count in self.shadow_trigger_counts.items():
                lines.append(f"- `{trigger}`: {count}")
        else:
            lines.append("- No shadow candidates found.")

        lines.extend(["", "## Recommended Next Actions", ""])
        for action in self.recommended_next_actions:
            lines.append(f"- {action}")
        return "\n".join(lines) + "\n"


def analyze_handoff_records(
    diagnostics: Iterable[Mapping[str, Any]],
    *,
    source_files: Iterable[str] = (),
    shadow_candidates: Iterable[Mapping[str, Any]] = (),
) -> HandoffAnalysis:
    one_ply = Counter()
    conversion = Counter()
    playouts = Counter()
    packet_phase_status = Counter()
    successor_selected = Counter()
    failed_successor = Counter()
    failure_classes = Counter()
    selected_successor_outcomes = Counter()
    failure_class_by_successor = Counter()
    contract_mismatch_by_successor = Counter()
    visible_eligible_successors = Counter()
    shadow_triggers = Counter()
    shadow_parent_skills = Counter()
    motifs: Counter[tuple[str, str, str, bool, bool]] = Counter()

    total = 0
    no_move = 0
    post_reply_failures = 0
    handoff_gaps = 0
    route_conflicts = 0
    embedded_shadows: list[Mapping[str, Any]] = []

    for diag in diagnostics:
        total += int(diag.get("total", 0) or 0)
        no_move += int(diag.get("no_move", 0) or 0)
        if isinstance(diag.get("one_ply_status_counts"), Mapping):
            _add_counter_values(one_ply, diag.get("one_ply_status_counts"))
        else:
            one_ply[str(diag.get("one_ply_status", "not_checked"))] += int(diag.get("total", 1) or 1)
        if isinstance(diag.get("conversion_status_counts"), Mapping):
            _add_counter_values(conversion, diag.get("conversion_status_counts"))
        else:
            raw_playouts = diag.get("playouts") or {}
            playout_total = sum(int(value or 0) for value in raw_playouts.values())
            if playout_total:
                conversion["passed"] += int(raw_playouts.get("mate", 0) or 0)
                conversion["failed"] += max(0, playout_total - int(raw_playouts.get("mate", 0) or 0))
            else:
                conversion[str(diag.get("conversion_status", "not_checked"))] += int(diag.get("total", 1) or 1)
        for key, value in (diag.get("playouts") or {}).items():
            playouts[str(key)] += int(value or 0)

        raw_shadows = diag.get("shadow_candidates") or []
        if isinstance(raw_shadows, list):
            embedded_shadows.extend(
                candidate for candidate in raw_shadows if isinstance(candidate, Mapping)
            )

        packets = diag.get("handoff_packets") or []
        if not isinstance(packets, list):
            continue
        post_reply_context: dict[tuple[str, str], Mapping[str, Any]] = {}
        for packet in packets:
            if not isinstance(packet, Mapping):
                continue
            packet_phase_status[_phase_status_key(packet)] += 1

            evidence = packet.get("evidence_terms")
            if not isinstance(evidence, Mapping):
                continue
            successor = evidence.get("successor_selected_skill")
            phase = packet.get("phase")
            status = packet.get("status")
            outcome = str(packet.get("observed_outcome") or evidence.get("playout_result") or "unknown")
            context_key = _handoff_context_key(packet)
            if phase == "post_opponent_reply":
                post_reply_context[context_key] = evidence
                if successor:
                    successor_selected[str(successor)] += 1
                for failure_class in evidence.get("failure_classes", []) or []:
                    failure_classes[str(failure_class)] += 1
                    if successor:
                        failure_class_by_successor[f"{successor}:{failure_class}"] += 1
                visible_eligible = evidence.get("visible_eligible_successors")
                if isinstance(visible_eligible, Mapping):
                    for skill in visible_eligible:
                        visible_eligible_successors[str(skill)] += 1
                if successor:
                    selected_successor_outcomes[f"{successor}:{outcome}"] += 1
                if evidence.get("selected_despite_contract_mismatch"):
                    contract_mismatch_by_successor[str(successor or "unknown")] += 1
            context = post_reply_context.get(context_key, {})
            successor_for_packet = successor or context.get("successor_selected_skill")
            handoff_gap = bool(evidence.get("handoff_gap", context.get("handoff_gap", False)))
            route_conflict = bool(evidence.get("route_conflict", context.get("route_conflict", False)))
            handoff_gaps += int(bool(evidence.get("handoff_gap")))
            route_conflicts += int(bool(evidence.get("route_conflict")))

            if phase == "post_opponent_reply" and status == "failed":
                post_reply_failures += 1
                failed_successor[str(successor_for_packet or "unknown")] += 1
            if phase == "playout_summary" and status == "failed":
                motifs[(
                    str(packet.get("from_skill") or "unknown"),
                    str(successor_for_packet or "unknown"),
                    outcome,
                    handoff_gap,
                    route_conflict,
                )] += 1

    for candidate in [*embedded_shadows, *list(shadow_candidates)]:
        if not isinstance(candidate, Mapping):
            continue
        shadow_triggers[str(candidate.get("trigger", "unknown"))] += 1
        shadow_parent_skills[str(candidate.get("parent_skill", "unknown"))] += 1

    top_motifs = [
        {
            "from_skill": from_skill,
            "successor_skill": successor,
            "outcome": outcome,
            "handoff_gap": handoff_gap,
            "route_conflict": route_conflict,
            "count": count,
        }
        for (from_skill, successor, outcome, handoff_gap, route_conflict), count in motifs.most_common(10)
    ]

    recommendations = _recommend_actions(
        conversion=conversion,
        handoff_gaps=handoff_gaps,
        route_conflicts=route_conflicts,
        failed_successor=failed_successor,
        shadow_triggers=shadow_triggers,
    )

    return HandoffAnalysis(
        source_files=list(source_files),
        total_evaluated=total,
        no_move=no_move,
        one_ply_status_counts=_counter_dict(one_ply),
        conversion_status_counts=_counter_dict(conversion),
        playout_counts=_counter_dict(playouts),
        packet_phase_status_counts=_counter_dict(packet_phase_status),
        post_reply_failure_count=post_reply_failures,
        successor_selected_skill_counts=_counter_dict(successor_selected),
        failed_successor_skill_counts=_counter_dict(failed_successor),
        failure_class_counts=_counter_dict(failure_classes),
        selected_successor_outcome_counts=_counter_dict(selected_successor_outcomes),
        failure_class_by_successor_counts=_counter_dict(failure_class_by_successor),
        contract_mismatch_count=sum(contract_mismatch_by_successor.values()),
        contract_mismatch_by_successor_counts=_counter_dict(contract_mismatch_by_successor),
        visible_eligible_successor_counts=_counter_dict(visible_eligible_successors),
        handoff_gap_count=handoff_gaps,
        route_conflict_count=route_conflicts,
        shadow_trigger_counts=_counter_dict(shadow_triggers),
        shadow_parent_skill_counts=_counter_dict(shadow_parent_skills),
        top_failure_motifs=top_motifs,
        recommended_next_actions=recommendations,
    )


def _recommend_actions(
    *,
    conversion: Counter,
    handoff_gaps: int,
    route_conflicts: int,
    failed_successor: Counter,
    shadow_triggers: Counter,
) -> list[str]:
    actions: list[str] = []
    if conversion.get("failed", 0) > 0:
        actions.append(
            "Keep local one-ply skills separate from conversion. Focus the next experiment on post-reply continuation."
        )
    if handoff_gaps > 0:
        actions.append(
            "Inspect low-affordance post-reply states and consider a shadow stem for a dedicated continuation skill."
        )
    if route_conflicts > 0:
        actions.append(
            "Compare competing successor skills in route-conflict states before changing scoring or topology."
        )
    if failed_successor:
        skill, _ = failed_successor.most_common(1)[0]
        actions.append(
            f"Prioritize diagnostics for successor `{skill}` because it appears in failed post-reply handoffs."
        )
    if shadow_triggers:
        trigger, _ = shadow_triggers.most_common(1)[0]
        actions.append(
            f"Use `{trigger}` as the first shadow-growth queue filter; do not create durable nodes yet."
        )
    if not actions:
        actions.append("No handoff bottleneck found in these diagnostics; run a larger conversion sample.")
    return actions


def analyze_handoff_files(
    paths: Iterable[Path],
    *,
    shadow_paths: Iterable[Path] = (),
) -> HandoffAnalysis:
    path_list = [Path(path) for path in paths]
    diagnostics = [_load_json(path) for path in path_list]
    shadows: list[dict[str, Any]] = []
    for path in shadow_paths:
        shadows.extend(_load_jsonl(Path(path)))
    return analyze_handoff_records(
        diagnostics,
        source_files=[str(path) for path in path_list],
        shadow_candidates=shadows,
    )
