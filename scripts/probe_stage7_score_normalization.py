#!/usr/bin/env python3
"""Non-causal Stage 7 score-normalization probe.

This does not run the engine and does not change move selection. It replays the
arbitration artifact and asks whether bounded alternative arbitration semantics
would select already-observed converting providers:

* raw: current winner.
* adapter_role_priority: adapter-visible provider wins over unlicensed provider.
* forced_success_oracle: diagnostic upper bound from known forced-provider mates.

The oracle row is explicitly non-causal; it is present only to separate
calibration/ownership problems from missing-capacity problems.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _provider_choice(record: dict[str, Any], mode: str) -> dict[str, Any]:
    normal = record.get("normal_selected") if isinstance(record.get("normal_selected"), dict) else {}
    rows = [row for row in record.get("provider_arbitration") or [] if isinstance(row, dict)]
    if mode == "raw":
        return {
            "mode": mode,
            "selected_provider": normal.get("skill_id"),
            "selected_move": normal.get("move"),
            "selected_score": normal.get("score"),
            "source": "current_runtime",
            "known_outcome": None,
        }
    if mode == "adapter_role_priority":
        adapter_rows = [
            row for row in rows
            if row.get("adapter_fired_under_forced_provider")
            and isinstance(row.get("forced_best"), dict)
        ]
        if adapter_rows:
            best = max(
                adapter_rows,
                key=lambda row: float(
                    (row.get("forced_best") or {}).get("score", 0.0) or 0.0
                ),
            )
            return _row_choice(mode, best, "adapter_visible_role_priority")
        return _provider_choice(record, "raw")
    if mode == "forced_success_oracle":
        mate_rows = [
            row for row in rows
            if row.get("forced_known_outcome") == "mate"
            and isinstance(row.get("forced_best"), dict)
        ]
        if mate_rows:
            best = min(mate_rows, key=lambda row: int(row.get("forced_known_plies", 9999) or 9999))
            return _row_choice(mode, best, "diagnostic_oracle_not_causal")
        return _provider_choice(record, "raw")
    raise ValueError(f"unknown mode: {mode}")


def _row_choice(mode: str, row: dict[str, Any], source: str) -> dict[str, Any]:
    forced = row.get("forced_best") if isinstance(row.get("forced_best"), dict) else {}
    return {
        "mode": mode,
        "selected_provider": row.get("provider"),
        "selected_move": forced.get("move"),
        "selected_score": forced.get("score"),
        "source": source,
        "known_outcome": row.get("forced_known_outcome"),
        "known_plies": row.get("forced_known_plies"),
        "required_support_to_overtake_selected": row.get("required_support_to_overtake_selected"),
        "adapter_support_amount": row.get("adapter_support_amount"),
        "adapter_fired_under_forced_provider": row.get("adapter_fired_under_forced_provider"),
    }


def probe_stage7_score_normalization(
    *,
    arbitration_path: Path,
) -> dict[str, Any]:
    arbitration = _load_json(arbitration_path)
    records: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    modes = ("raw", "adapter_role_priority", "forced_success_oracle")
    for record in arbitration.get("records") or []:
        if not isinstance(record, dict):
            continue
        choices = {mode: _provider_choice(record, mode) for mode in modes}
        for mode, choice in choices.items():
            key = f"{mode}:{choice.get('selected_provider')}:{choice.get('known_outcome')}"
            counts[key] = counts.get(key, 0) + 1
        raw_provider = choices["raw"].get("selected_provider")
        records.append({
            "state_id": record.get("state_id"),
            "family_id": record.get("family_id"),
            "post_reply_fen": record.get("post_reply_fen"),
            "choices": choices,
            "adapter_role_changes_provider": choices["adapter_role_priority"].get("selected_provider")
            != raw_provider,
            "oracle_changes_provider": choices["forced_success_oracle"].get("selected_provider")
            != raw_provider,
        })

    adapter_role_mate = sum(
        1 for item in records
        if item["choices"]["adapter_role_priority"].get("known_outcome") == "mate"
    )
    oracle_mate = sum(
        1 for item in records
        if item["choices"]["forced_success_oracle"].get("known_outcome") == "mate"
    )
    if adapter_role_mate:
        status = "role_owned_score_normalization_sandbox_candidate"
        next_action = "sandbox_role_owned_arbitration_with_guardrails"
    elif oracle_mate:
        status = "visible_support_missing_for_some_forced_success_families"
        next_action = "derive_visible_support_for_oracle_success_families_before_calibration"
    else:
        status = "normalization_unlikely_to_solve_known_families"
        next_action = "consider_narrow_continuation_overlay_after_legal_first_probe"

    return {
        "schema_version": "stage7_score_normalization_probe.v1",
        "causal_status": "non_causal",
        "arbitration_source": str(arbitration_path),
        "record_count": len(records),
        "choice_counts": counts,
        "adapter_role_mate_count": adapter_role_mate,
        "oracle_mate_count": oracle_mate,
        "candidate_update": {
            "candidate_id": "cand.krk.box_shrink.score_normalized_role_arbitration.v1",
            "candidate_type": "score_normalization_probe",
            "status": status,
            "causal_status": "non_causal",
            "promotion_status": "proposed",
            "next_action": next_action,
            "hard_blocks": [
                "do_not_promote_stage7",
                "do_not_train_stage8",
                "do_not_make_oracle_choice_causal",
                "do_not_use_score_normalization_without_guardrails",
            ],
        },
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Stage 7 score normalization")
    parser.add_argument("--arbitration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = probe_stage7_score_normalization(arbitration_path=args.arbitration)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
