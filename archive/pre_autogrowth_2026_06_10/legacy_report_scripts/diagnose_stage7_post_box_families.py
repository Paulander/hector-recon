#!/usr/bin/env python3
"""Stage 7 post-box-shrink family-split continuation diagnosis.

This consumes the replay-free Stage 7 diagnosis plus bounded forced-provider
probe artifacts and turns the four unique failed post-reply families into
explicit non-causal StructuralCandidate-style records.

The output is a planning/diagnosis artifact only. It does not compile adapters,
train weights, promote Stage 7, or alter runtime routing.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _state_suffix(state_id: str) -> str:
    return state_id.removeprefix("state.")


def _terms_from_audit(audit: dict[str, Any] | None, key: str) -> set[str]:
    if not isinstance(audit, dict):
        return set()
    values = audit.get(key)
    if not isinstance(values, list):
        return set()
    return {str(item) for item in values}


def _all_terms_from_probe(probe: dict[str, Any] | None) -> dict[str, list[str]]:
    audit = probe.get("move_shape_audit") if isinstance(probe, dict) else None
    return {
        "current_terms": sorted(_terms_from_audit(audit, "current_terms")),
        "move_shape_terms": sorted(_terms_from_audit(audit, "move_shape_terms")),
        "post_move_terms": sorted(_terms_from_audit(audit, "post_move_terms")),
        "worst_reply_terms": sorted(_terms_from_audit(audit, "worst_reply_terms")),
    }


def _records_by_state(probe: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for record in probe.get("records") or []:
        if isinstance(record, dict) and record.get("state_id"):
            records[str(record["state_id"])] = record
    return records


def _playout_results_by_provider(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_provider: dict[str, dict[str, Any]] = {}
    for item in record.get("playout_probes") or []:
        if not isinstance(item, dict):
            continue
        provider = str(item.get("provider") or "")
        if not provider:
            continue
        by_provider[provider] = {
            "result": item.get("result"),
            "plies": item.get("plies"),
            "first_move": item.get("first_move"),
            "horizon": item.get("horizon"),
            "forced_successor_available": item.get("forced_successor_available"),
        }
    return by_provider


def _first_move_probes_by_provider(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_provider: dict[str, dict[str, Any]] = {}
    for item in record.get("first_move_probes") or []:
        if isinstance(item, dict) and item.get("provider"):
            by_provider[str(item["provider"])] = item
    return by_provider


def _merged_forced_provider_results(
    *,
    state_id: str,
    h40_record: dict[str, Any] | None,
    h80_record: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    providers = set()
    h40_results = _playout_results_by_provider(h40_record or {})
    h80_results = _playout_results_by_provider(h80_record or {})
    providers.update(h40_results)
    providers.update(h80_results)
    first_moves = _first_move_probes_by_provider(h40_record or {})
    merged: dict[str, dict[str, Any]] = {}
    for provider in sorted(providers):
        result = dict(h40_results.get(provider) or {})
        if provider in h80_results:
            h80 = h80_results[provider]
            if result.get("result") != "mate":
                result.update({
                    "h80_result": h80.get("result"),
                    "h80_plies": h80.get("plies"),
                    "h80_first_move": h80.get("first_move"),
                })
        if provider in first_moves:
            result["first_move_probe"] = {
                "move": first_moves[provider].get("move"),
                "forced_successor_available": first_moves[provider].get(
                    "forced_successor_available"
                ),
                "legal": first_moves[provider].get("legal"),
                "confidence": first_moves[provider].get("confidence"),
                **_all_terms_from_probe(first_moves[provider]),
            }
        merged[provider] = result
    return merged


def _diagnosis_for_family(results: dict[str, dict[str, Any]]) -> tuple[str, str | None]:
    mating = [
        (provider, payload)
        for provider, payload in results.items()
        if payload.get("result") == "mate" or payload.get("h80_result") == "mate"
    ]
    if mating:
        best = min(
            mating,
            key=lambda item: int(
                item[1].get("plies")
                if item[1].get("result") == "mate"
                else item[1].get("h80_plies")
                or 999
            ),
        )
        return "existing_provider_can_convert_if_family_role_selects_it", best[0]
    if results and all(
        payload.get("result") == "max_plies" or payload.get("h80_result") == "max_plies"
        for payload in results.values()
    ):
        return "unresolved_by_existing_forced_providers_at_h80", None
    return "needs_deeper_probe", None


def _candidate_for_family(
    *,
    state_id: str,
    diagnosis: str,
    provider: str | None,
) -> dict[str, Any]:
    suffix = _state_suffix(state_id)
    if diagnosis == "existing_provider_can_convert_if_family_role_selects_it" and provider:
        provider_name = provider.removeprefix("krk.").replace(".", "_")
        return {
            "candidate_id": f"cand.krk.box_shrink.family_{suffix}.{provider_name}_adapter.v1",
            "candidate_type": "family_specific_support_adapter",
            "target_skill": "krk.box_shrink",
            "target_provider": provider,
            "candidate_role": f"krk.post_box_family_{suffix}_{provider_name}",
            "status": "sandbox_ready_if_terms_separate",
            "diagnosis": diagnosis,
            "causal_status": "non_causal",
            "promotion_status": "proposed",
            "next_action": "derive_visible_family_terms_before_compiling_adapter",
        }
    return {
        "candidate_id": f"cand.krk.box_shrink.family_{suffix}.unresolved_continuation.v1",
        "candidate_type": "unresolved_continuation_probe",
        "target_skill": "krk.box_shrink",
        "target_provider": None,
        "candidate_role": f"krk.post_box_family_{suffix}_unresolved_continuation",
        "status": "needs_legal_first_or_longer_horizon_sweep",
        "diagnosis": diagnosis,
        "causal_status": "non_causal",
        "promotion_status": "proposed",
        "next_action": "run_targeted_legal_first_and_longer_horizon_sweep",
    }


def _provider_term_splits(families: list[dict[str, Any]], provider: str) -> dict[str, Any]:
    success_sets: dict[str, list[set[str]]] = defaultdict(list)
    fail_sets: dict[str, list[set[str]]] = defaultdict(list)
    for family in families:
        result = family.get("forced_provider_results", {}).get(provider)
        if not isinstance(result, dict):
            continue
        first = result.get("first_move_probe") if isinstance(result.get("first_move_probe"), dict) else {}
        bucket = success_sets if result.get("result") == "mate" else fail_sets
        for key in ("current_terms", "move_shape_terms", "post_move_terms", "worst_reply_terms"):
            bucket[key].append(set(first.get(key) or []))

    def common(values: list[set[str]]) -> set[str]:
        if not values:
            return set()
        acc = set(values[0])
        for value in values[1:]:
            acc &= value
        return acc

    output: dict[str, Any] = {}
    for key in ("current_terms", "move_shape_terms", "post_move_terms", "worst_reply_terms"):
        success_common = common(success_sets.get(key, []))
        fail_common = common(fail_sets.get(key, []))
        output[key] = {
            "success_common": sorted(success_common),
            "failure_common": sorted(fail_common),
            "success_common_minus_failure_common": sorted(success_common - fail_common),
        }
    return output


def _legal_first_summary(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(record, dict):
        return None
    counts = Counter()
    mating_moves: list[dict[str, Any]] = []
    tested_moves = 0
    for item in record.get("legal_first_probes") or []:
        if not isinstance(item, dict):
            continue
        tested_moves += 1
        result = str(item.get("result") or "unknown")
        horizon = str(item.get("horizon") or "unknown")
        counts[f"h{horizon}:{result}"] += 1
        if result == "mate":
            mating_moves.append({
                "move": item.get("move"),
                "horizon": item.get("horizon"),
                "plies": item.get("plies"),
                "move_shape_audit": item.get("move_shape_audit"),
            })
    if tested_moves == 0:
        return None
    return {
        "tested_move_count": tested_moves,
        "outcome_counts": dict(counts),
        "mating_moves": mating_moves,
        "any_mate": bool(mating_moves),
    }


def diagnose_families(
    *,
    diagnosis_path: Path,
    forced_h40_path: Path,
    unresolved_h80_path: Path | None = None,
    adapter_smoke_path: Path | None = None,
    unresolved_legal_first_path: Path | None = None,
) -> dict[str, Any]:
    diagnosis = _load_json(diagnosis_path)
    h40 = _load_json(forced_h40_path)
    h80 = _load_json(unresolved_h80_path)
    adapter_smoke = _load_json(adapter_smoke_path)
    legal_first = _load_json(unresolved_legal_first_path)
    h40_by_state = _records_by_state(h40)
    h80_by_state = _records_by_state(h80)
    legal_first_by_state = _records_by_state(legal_first)

    families: list[dict[str, Any]] = []
    for state in diagnosis.get("unique_failed_post_reply_states") or []:
        if not isinstance(state, dict):
            continue
        # The bounded probe uses state IDs, so match by FEN through the h40 record.
        matched_state_id = None
        for candidate_id, record in h40_by_state.items():
            if record.get("post_reply_fen") == state.get("post_reply_fen"):
                matched_state_id = candidate_id
                break
        if not matched_state_id:
            continue
        forced_results = _merged_forced_provider_results(
            state_id=matched_state_id,
            h40_record=h40_by_state.get(matched_state_id),
            h80_record=h80_by_state.get(matched_state_id),
        )
        family_diagnosis, provider = _diagnosis_for_family(forced_results)
        legal_summary = _legal_first_summary(legal_first_by_state.get(matched_state_id))
        first_probe = next(iter(_first_move_probes_by_provider(h40_by_state[matched_state_id]).values()), {})
        visible_terms = _all_terms_from_probe(first_probe)
        families.append({
            "family_id": f"stage7.post_box.family_{_state_suffix(matched_state_id)}",
            "state_id": matched_state_id,
            "post_reply_fen": state.get("post_reply_fen"),
            "selected_successor": state.get("selected_successor"),
            "selected_move": state.get("selected_move"),
            "conversion_result": state.get("conversion_result"),
            "failure_classes": list(state.get("failure_classes") or []),
            "visible_terms": visible_terms,
            "forced_provider_results": forced_results,
            "diagnosis": family_diagnosis,
            "best_forced_provider": provider,
            "legal_first_summary": legal_summary,
            "candidate": _candidate_for_family(
                state_id=matched_state_id,
                diagnosis=family_diagnosis,
                provider=provider,
            ),
        })

    provider_splits = {
        provider: _provider_term_splits(families, provider)
        for provider in (
            "krk.drive_to_edge",
            "krk.fence_established",
            "krk.stage0_basin",
            "krk.edge_trap_close",
        )
    }
    family_diagnosis_counts = Counter(family["diagnosis"] for family in families)
    candidate_updates = [family["candidate"] for family in families]
    overbroad_adapter_status = None
    if adapter_smoke:
        adapter_fire_count = int(adapter_smoke.get("adapter_fire_count", 0) or 0)
        adapter_by_outcome = dict(adapter_smoke.get("adapter_supported_provider_by_outcome", {}) or {})
        if adapter_fire_count and not any(key.endswith(":mate") for key in adapter_by_outcome):
            overbroad_adapter_status = {
                "candidate_id": "cand.krk.box_shrink_to_drive_repair.visible_provider_support.v1",
                "status": "overbroad_adapter_candidate",
                "diagnosis": [
                    "role_contract_fires_but_supported_provider_outcome_max_plies",
                    "needs_family_specific_terms",
                ],
                "adapter_fire_count": adapter_fire_count,
                "adapter_supported_provider_by_outcome": adapter_by_outcome,
                "next_action": "do_not_run_m3_on_current_broad_adapter",
                "causal_status": "non_causal",
            }

    return {
        "schema_version": "stage7_post_box_family_diagnosis.v1",
        "causal_status": "non_causal",
        "stage7_status": "local_valid_composition_quarantined",
        "diagnosis_source": str(diagnosis_path),
        "forced_h40_source": str(forced_h40_path),
        "unresolved_h80_source": str(unresolved_h80_path) if unresolved_h80_path else None,
        "adapter_smoke_source": str(adapter_smoke_path) if adapter_smoke_path else None,
        "unresolved_legal_first_source": (
            str(unresolved_legal_first_path) if unresolved_legal_first_path else None
        ),
        "family_count": len(families),
        "family_diagnosis_counts": dict(family_diagnosis_counts),
        "families": families,
        "provider_term_splits": provider_splits,
        "candidate_updates": candidate_updates,
        "overbroad_adapter_status": overbroad_adapter_status,
        "recommended_next_actions": [
            "compile_no_broad_stage7_repair",
            "derive_narrow_family_terms_for_forced-success_families",
            "run_targeted_legal_first_longer_horizon_for_unresolved_families",
            "do_not_train_stage8",
            "do_not_promote_stage7",
            "do_not_run_m3_on_current_broad_drive_adapter",
        ],
    }


def _write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Stage 7 Post-Box Family Diagnosis",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Stage 7 status: `{payload['stage7_status']}`",
        f"Families: `{payload['family_count']}`",
        "",
        "## Family Counts",
        "",
    ]
    for key, value in sorted(payload.get("family_diagnosis_counts", {}).items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Families", ""])
    for family in payload.get("families") or []:
        lines.append(f"### {family['family_id']}")
        lines.append("")
        lines.append(f"- State: `{family['state_id']}`")
        lines.append(f"- FEN: `{family['post_reply_fen']}`")
        lines.append(f"- Diagnosis: `{family['diagnosis']}`")
        lines.append(f"- Best forced provider: `{family.get('best_forced_provider')}`")
        candidate = family.get("candidate", {})
        lines.append(f"- Candidate: `{candidate.get('candidate_id')}`")
        lines.append(f"- Candidate status: `{candidate.get('status')}`")
        lines.append("")
    if payload.get("overbroad_adapter_status"):
        status = payload["overbroad_adapter_status"]
        lines.extend([
            "## Adapter Status",
            "",
            f"- Candidate: `{status['candidate_id']}`",
            f"- Status: `{status['status']}`",
            f"- Adapter fires: `{status['adapter_fire_count']}`",
            f"- Next action: `{status['next_action']}`",
            "",
        ])
    lines.extend(["## Recommended Next Actions", ""])
    for item in payload.get("recommended_next_actions") or []:
        lines.append(f"- `{item}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose Stage 7 post-box families")
    parser.add_argument("--diagnosis", type=Path, required=True)
    parser.add_argument("--forced-h40", type=Path, required=True)
    parser.add_argument("--unresolved-h80", type=Path, default=None)
    parser.add_argument("--adapter-smoke", type=Path, default=None)
    parser.add_argument("--unresolved-legal-first", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = diagnose_families(
        diagnosis_path=args.diagnosis,
        forced_h40_path=args.forced_h40,
        unresolved_h80_path=args.unresolved_h80,
        adapter_smoke_path=args.adapter_smoke,
        unresolved_legal_first_path=args.unresolved_legal_first,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        _write_markdown(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
