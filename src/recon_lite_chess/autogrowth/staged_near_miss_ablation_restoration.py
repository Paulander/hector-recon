"""TG28k staged near-miss and ablation restoration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from .persisted_staged_predecessor_pool import (
    PersistedStagedPredecessorPoolConfig,
    PersistedStagedPredecessorPoolResult,
    run_persisted_staged_predecessor_pool,
)


@dataclass(frozen=True)
class StagedNearMissAblationRestorationConfig:
    pool_config: PersistedStagedPredecessorPoolConfig = PersistedStagedPredecessorPoolConfig(
        staged_near_miss_count=2,
        near_miss_heldout_count=2,
        max_ablation_positions=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg28k_staged_near_miss_ablation_restoration_progress.json",
    )


@dataclass(frozen=True)
class StagedNearMissAblationRestorationResult:
    config: StagedNearMissAblationRestorationConfig
    pool_result: PersistedStagedPredecessorPoolResult

    def to_dict(self) -> dict[str, Any]:
        payload = self.pool_result.to_dict()
        decision = dict(payload["decision"])
        ablations = payload.get("ablation_results", {})
        restored = [name for name, row in ablations.items() if not row.get("skipped", False)]
        near_miss_pass = (
            decision["staged_near_miss_count"] > 0
            and decision["near_miss_false_positive_count"] == 0
        )
        ablation_pass = bool(restored) and _staged_actuator_ablation_collapses(ablations)
        checkpoint_pass = bool(
            decision["checkpoint_pass"]
            and near_miss_pass
            and ablation_pass
            and decision["foundation_m3_updates_during_training"] == 0
            and decision["foundation_m4_promotions_during_training"] == 0
        )
        decision.update(
            {
                "checkpoint_pass": checkpoint_pass,
                "checkpoint_interpretation": (
                    "staged_near_miss_and_ablation_restored"
                    if checkpoint_pass
                    else "staged_near_miss_or_ablation_not_restored"
                ),
                "tg28j_underlying_checkpoint_pass": payload["decision"]["checkpoint_pass"],
                "tg28j_underlying_checkpoint_interpretation": payload["decision"]["checkpoint_interpretation"],
                "restored_ablation_count": len(restored),
                "restored_ablation_names": restored,
                "staged_near_miss_false_positive_pass": near_miss_pass,
                "staged_actuator_ablation_collapse_pass": ablation_pass,
                "do_not_claim_broad_krk_competence": True,
            }
        )
        payload.update(
            {
                "schema_version": "krk_autogrowth_tg28k_staged_near_miss_ablation_restoration.v0",
                "checkpoint": "TG28k_staged_near_miss_ablation_restoration",
                "config": asdict(self.config),
                "underlying_tg28j_config": asdict(self.pool_result.config),
                "decision": decision,
            }
        )
        payload["purity_boundary"] = dict(payload["purity_boundary"]) | {
            "checkpoint": "TG28k",
            "staged_near_miss_pool": True,
            "ablations_restored": True,
            "near_miss_entries_used_as_provider": False,
        }
        return payload

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output

    def write_markdown(self, path: str | Path) -> Path:
        payload = self.to_dict()
        decision = payload["decision"]
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "\n".join(
                [
                    "# TG28k Staged Near-Miss + Ablation Restoration",
                    "",
                    f"- checkpoint_pass: `{decision['checkpoint_pass']}`",
                    f"- interpretation: `{decision['checkpoint_interpretation']}`",
                    f"- staged pool entries: `{decision['staged_pool_entry_count']}`",
                    f"- staged near-misses: `{decision['staged_near_miss_count']}`",
                    f"- near-miss false positives: `{decision['near_miss_false_positive_count']}`",
                    f"- restored ablations: `{decision['restored_ablation_count']}`",
                    f"- selected schedule: `{decision['selected_training_schedule']}`",
                    f"- staged any-reply successes: `{decision['staged_any_reply_success_count']}`",
                    f"- foundation M3/M4 deltas during training: `{decision['foundation_m3_updates_during_training']}` / `{decision['foundation_m4_promotions_during_training']}`",
                    "",
                    "Interpretation: this restores negative staged checks and bounded ablations on the persisted staged runway. It is not a broad KRK competence claim.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_staged_near_miss_ablation_restoration(
    *,
    config: StagedNearMissAblationRestorationConfig | None = None,
) -> StagedNearMissAblationRestorationResult:
    cfg = config or StagedNearMissAblationRestorationConfig()
    pool_result = run_persisted_staged_predecessor_pool(config=cfg.pool_config)
    return StagedNearMissAblationRestorationResult(config=cfg, pool_result=pool_result)


def _staged_actuator_ablation_collapses(ablations: dict[str, Any]) -> bool:
    actuator = ablations.get("mask_actuator_terminals", {})
    if actuator.get("skipped", False):
        return False
    staged = actuator.get("staged", {})
    return staged.get("selected_first_move_count") == 0
