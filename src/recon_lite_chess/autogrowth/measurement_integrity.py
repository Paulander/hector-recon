"""Domain-independent measurement invariants for counterfactual evaluations."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from math import sqrt
from statistics import NormalDist
from typing import Any, Iterable, Mapping, Sequence


RETIRED_DEVELOPMENT_ROW_IDS = frozenset(range(600, 728))

_ROW_FIELDS = (
    "success_by_row",
    "endpoint_by_row",
    "trace_digest_by_row",
    "active_composite_ids_by_row",
    "predicate_evaluated_ids_by_row",
)
_RUNNER_FIELDS = (
    "black_reply_policy",
    "seed",
    "seed_schedule",
    "judge_version",
    "fence_check_timing",
    "tick_budget",
    "tie_break",
    "deterministic_row_order",
)
_SOURCE_FIELDS = ("split", "sha256", "row_ids")


@dataclass(frozen=True)
class CounterfactualSnapshot:
    """Deep snapshot of mutable runtime and graph state.

    Restoring deliberately replaces population *items*. Callers must retain stable
    composite IDs and reacquire the live item after every restore.
    """

    runtime_state: Mapping[str, Any]
    node_state: Mapping[str, Mapping[str, Any]]
    edge_state: Sequence[Mapping[str, Any]]

    @classmethod
    def capture(cls, runtime: Any) -> "CounterfactualSnapshot":
        runtime_state = {
            name: deepcopy(value)
            for name, value in vars(runtime).items()
            if name not in {"cfg", "native_graph"}
        }
        graph = runtime.native_graph.graph
        node_state = {
            str(node_id): {
                "state": deepcopy(node.state),
                "activation": deepcopy(node.activation),
                "tick_entered": int(node.tick_entered),
                "meta": deepcopy(node.meta),
            }
            for node_id, node in graph.nodes.items()
        }
        edge_state = tuple(
            {"w": deepcopy(edge.w), "meta": deepcopy(edge.meta)}
            for edge in graph.edges
        )
        return cls(runtime_state=runtime_state, node_state=node_state, edge_state=edge_state)

    def restore(self, runtime: Any) -> None:
        for name, saved in self.runtime_state.items():
            current = getattr(runtime, name, None)
            if isinstance(current, dict) and isinstance(saved, Mapping):
                current.clear()
                current.update(deepcopy(saved))
            elif isinstance(current, list) and isinstance(saved, list):
                current[:] = deepcopy(saved)
            elif isinstance(current, set) and isinstance(saved, set):
                current.clear()
                current.update(deepcopy(saved))
            else:
                setattr(runtime, name, deepcopy(saved))

        graph = runtime.native_graph.graph
        if len(graph.edges) != len(self.edge_state):
            raise RuntimeError("graph edge topology changed during counterfactual evaluation")
        for node_id, saved in self.node_state.items():
            if node_id not in graph.nodes:
                raise RuntimeError(f"graph node disappeared during counterfactual evaluation: {node_id}")
            node = graph.nodes[node_id]
            node.state = deepcopy(saved["state"])
            node.activation = deepcopy(saved["activation"])
            node.tick_entered = int(saved["tick_entered"])
            node.meta.clear()
            node.meta.update(deepcopy(saved["meta"]))
        for edge, saved in zip(graph.edges, self.edge_state, strict=True):
            edge.w = deepcopy(saved["w"])
            edge.meta.clear()
            edge.meta.update(deepcopy(saved["meta"]))


def live_population_item(runtime: Any, composite_id: str) -> dict[str, Any]:
    """Return the current population item; never accept a captured item object."""

    try:
        item = runtime.population[str(composite_id)]
    except KeyError as exc:
        raise KeyError(f"counterfactual target is not live: {composite_id}") from exc
    if not isinstance(item, dict):
        raise TypeError(f"population item must be mutable dict: {composite_id}")
    return item


def apply_live_routing_weight(runtime: Any, composite_id: str, requested: float) -> dict[str, float]:
    item = live_population_item(runtime, composite_id)
    item["routing_weight_override"] = float(requested)
    observed = float(live_population_item(runtime, composite_id)["routing_weight_override"])
    if observed != float(requested):
        raise AssertionError(f"live routing weight mismatch: requested={requested}, observed={observed}")
    return {
        "requested_routing_weight": float(requested),
        "observed_routing_weight": observed,
    }


def counterfactual_plan(arm: str, doses: Iterable[float]) -> tuple[dict[str, Any], ...]:
    arm = str(arm).upper()
    off = {"intervention": "off", "dose_multiplier": None}
    if arm == "G":
        return (off, {"intervention": "on", "dose_multiplier": None})
    if arm == "L":
        clean = tuple(float(dose) for dose in doses if float(dose) > 0)
        if not clean:
            clean = (1.0,)
        return (off, *({"intervention": "on", "dose_multiplier": dose} for dose in clean))
    raise ValueError(f"unknown counterfactual arm: {arm}")


def paired_binary_outcomes(
    left: Sequence[bool],
    right: Sequence[bool],
    *,
    confidence: float = 0.95,
    noninferiority_margin: float = 0.0,
) -> dict[str, Any]:
    """Paired Wilson sign interval, scaled to the all-row net difference.

    The Wilson interval is calculated for P(left wins | discordant), transformed
    to a signed discordance effect, and multiplied by discordants / all pairs.
    """

    if len(left) != len(right):
        raise ValueError("paired outcomes must have equal length")
    total = len(left)
    favorable = sum(1 for a, b in zip(left, right, strict=True) if a and not b)
    unfavorable = sum(1 for a, b in zip(left, right, strict=True) if not a and b)
    discordants = favorable + unfavorable
    difference = (favorable - unfavorable) / max(1, total)
    if discordants == 0:
        ci_low = ci_high = 0.0
    else:
        z = NormalDist().inv_cdf(1.0 - (1.0 - float(confidence)) / 2.0)
        p = favorable / discordants
        denominator = 1.0 + z * z / discordants
        center = (p + z * z / (2.0 * discordants)) / denominator
        radius = z * sqrt((p * (1.0 - p) / discordants) + z * z / (4.0 * discordants**2)) / denominator
        scale = discordants / max(1, total)
        ci_low = (2.0 * max(0.0, center - radius) - 1.0) * scale
        ci_high = (2.0 * min(1.0, center + radius) - 1.0) * scale
    margin = float(noninferiority_margin)
    return {
        "method": "paired Wilson sign interval scaled by discordant fraction",
        "confidence": float(confidence),
        "paired_row_count": total,
        "favorable": favorable,
        "unfavorable": unfavorable,
        "discordant_count": discordants,
        "difference": difference,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "noninferiority_margin": margin,
        "noninferior": ci_low >= -margin,
        "superior": ci_low > 0.0,
    }


def holm_adjusted_pvalues(p_values: Sequence[float], *, alpha: float = 0.05) -> list[dict[str, Any]]:
    """Return Holm step-down adjusted p-values in the original order."""

    m = len(p_values)
    ordered = sorted(enumerate(float(p) for p in p_values), key=lambda row: (row[1], row[0]))
    result: list[dict[str, Any] | None] = [None] * m
    running = 0.0
    still_rejecting = True
    for rank, (index, p_value) in enumerate(ordered, start=1):
        adjusted = min(1.0, max(running, (m - rank + 1) * p_value))
        running = adjusted
        threshold = float(alpha) / (m - rank + 1)
        rejected = bool(still_rejecting and p_value <= threshold)
        if not rejected:
            still_rejecting = False
        result[index] = {
            "index": index,
            "rank": rank,
            "raw_p": p_value,
            "adjusted_p": adjusted,
            "holm_threshold": threshold,
            "rejected": rejected,
        }
    return [row for row in result if row is not None]


def validate_split_ids(
    discovery_train_ids: Iterable[int],
    confirmation_validation_ids: Iterable[int],
    final_test_ids: Iterable[int],
) -> dict[str, Any]:
    train = set(map(int, discovery_train_ids))
    validation = set(map(int, confirmation_validation_ids))
    final = set(map(int, final_test_ids))
    overlaps = {
        "train_validation": sorted(train & validation),
        "train_final": sorted(train & final),
        "validation_final": sorted(validation & final),
    }
    if any(overlaps.values()):
        raise ValueError(f"measurement split overlap: {overlaps}")
    retired = sorted(final & RETIRED_DEVELOPMENT_ROW_IDS)
    if retired:
        raise ValueError(f"retired development rows cannot be final test: {retired}")
    return {
        "disjoint": True,
        "train_row_ids": sorted(train),
        "validation_row_ids": sorted(validation),
        "final_test_row_ids": sorted(final),
        "retired_development_row_ids": sorted(RETIRED_DEVELOPMENT_ROW_IDS),
    }


def assert_final_test_untouched(
    *,
    final_test_ids: Iterable[int],
    adaptive_row_ids: Mapping[str, Iterable[int]],
) -> None:
    final = set(map(int, final_test_ids))
    leaks = {
        str(path): sorted(final & set(map(int, row_ids)))
        for path, row_ids in adaptive_row_ids.items()
        if final & set(map(int, row_ids))
    }
    if leaks:
        raise ValueError(f"final-test rows reached adaptive paths: {leaks}")


def assert_complete_arm_record(record: Mapping[str, Any]) -> None:
    for field in _ROW_FIELDS:
        if field not in record:
            raise ValueError(f"missing arm provenance field: {field}")
    if "runner_config" not in record:
        raise ValueError("missing arm provenance field: runner_config")
    for field in _RUNNER_FIELDS:
        if field not in record["runner_config"]:
            raise ValueError(f"missing runner_config field: {field}")
    if "source_manifest" not in record:
        raise ValueError("missing arm provenance field: source_manifest")
    for field in _SOURCE_FIELDS:
        if field not in record["source_manifest"]:
            raise ValueError(f"missing source_manifest field: {field}")
    expected = set(map(str, record["source_manifest"]["row_ids"]))
    for field in _ROW_FIELDS:
        if set(map(str, record[field])) != expected:
            raise ValueError(f"{field} does not cover the exact source row IDs")


def assert_noop_parity(full: Mapping[str, Any], noop: Mapping[str, Any]) -> dict[str, Any]:
    assert_complete_arm_record(full)
    assert_complete_arm_record(noop)
    for field in (*_ROW_FIELDS, "action_by_row", "runner_config", "source_manifest"):
        if full.get(field) != noop.get(field):
            raise AssertionError(f"no-op parity mismatch: {field}")
    row_ids = list(map(str, full["source_manifest"]["row_ids"]))
    paired = paired_binary_outcomes(
        [bool(full["success_by_row"][row_id]) for row_id in row_ids],
        [bool(noop["success_by_row"][row_id]) for row_id in row_ids],
    )
    return {"passed": paired["difference"] == 0.0, "paired": paired}


def validate_analysis_population(
    *,
    predeclared_row_ids: Iterable[int],
    analyzed_row_ids: Iterable[int],
    static_eligible_row_ids: Iterable[int],
    off_nonfiring_by_row: Mapping[int, bool],
    on_nonfiring_by_row: Mapping[int, bool],
) -> None:
    predeclared = set(map(int, predeclared_row_ids))
    analyzed = set(map(int, analyzed_row_ids))
    eligible = set(map(int, static_eligible_row_ids))
    if analyzed != predeclared:
        raise ValueError("analysis must evaluate the full predeclared pool")
    if not eligible <= predeclared:
        raise ValueError("static eligible subset must be defined inside the predeclared pool")
    for row_id in sorted(predeclared - eligible):
        if bool(off_nonfiring_by_row.get(row_id)) != bool(on_nonfiring_by_row.get(row_id)):
            raise ValueError(f"non-firing parity failed for row {row_id}")

