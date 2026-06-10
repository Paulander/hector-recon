# KRK Clean Retrain Retry1 Stage 6 Gap Inspection v1

## Decision

- status: `stage6_gap_explained_by_validation_profile_mismatch`
- retry1 Stage 6 learner quality issue: `False`
- overlay extraction issue: `False`
- current harness without profile bonus reproduces failure on protected overlay: `True`
- corrected profile bonus restores Stage 6 conversion: `True`
- promotion eval with corrected profile: `overlay_only`
- retry1 can replace protected stack: `False`
- Stage 7 remains quarantined: `True`
- Stage 8 remains blocked: `True`
- runtime behavior changed: `False`

## Finding

The retry1 Stage 6 failure was caused by a validation-profile mismatch. The historical Stage 6 training and stored passing validation artifact used:

```text
--stagnation-breaker-king-support-bonus 2.0
--early-stop-stable-suggestions 2
```

The initial retry1 guardrail rerun used `--use-profile-validation-defaults` but did not pass the explicit king-support bonus, so the validation ran with:

```text
stagnation_breaker_king_support_bonus = 0.0
```

That omission reproduces the same failure even on the existing protected Stage 6 overlay topology, so the failure is not unique to retry1.

## Evidence

Without the explicit king-support bonus:

| Topology | Mate | Max plies | Shadow |
| --- | ---: | ---: | ---: |
| retry1 Stage 6 overlay | 217/300 | 83/300 | 166 |
| historical protected overlay rerun with current harness | 217/300 | 83/300 | 166 |

With the explicit king-support bonus:

| Artifact | Mate | Max plies | Shadow | One-ply |
| --- | ---: | ---: | ---: | --- |
| retry1 Stage 6 overlay | 300/300 | 0/300 | 0 | failed, 217/300 optimal |
| retry1 Stage 5 overlay guardrail | 300/300 | 0/300 | 0 | failed, 144/300 improved |
| retry1 Stage 5 base control | 300/300 | 0/300 | 0 | failed, 144/300 improved |

Promotion evaluation with the corrected artifacts reports:

```text
promotion_status = overlay_only
failures = []
guardrail_control_debt = Stage 5 one-ply local reward debt
```

## Interpretation

The retry1 clean retrain is substantially better than the initial quarantine report suggested. Its Stage 6 overlay can reproduce the historical h40 conversion result when evaluated with the same profile-scoped king-support validation bonus used during training and historical validation.

The remaining blocker is not Stage 6 conversion. It is Stage 5 one-ply guardrail semantics: both the retry1 Stage 5 overlay guardrail and the retry1 Stage 5 base control convert 300/300 but fail local one-ply reward thresholds in the same way. That should be treated as base-control debt or a guardrail-definition issue, not Stage 6 overlay interference.

## Manifest Update

`reports/krk_stage6_overlay_compose_manifest_v0.md/json` now records replayable Stage 6/Stage 5 h40 validation commands with the explicit profile-scoped flags:

```text
--composition-profile handoff_composition_v1
--use-profile-validation-defaults
--stagnation-breaker-king-support-bonus 2.0
--early-stop-stable-suggestions 2
```

The promotion-eval command now includes the fresh Stage 5 base-control artifact so control debt is separated from true overlay regression.

## Next Step

Do not promote retry1 as a protected replacement yet. The next review should decide whether Stage 5 one-ply local reward debt should:

- block replacement despite identical/passing conversion,
- be treated as known base-control debt under current semantics,
- or trigger a narrow Stage 5 guardrail-definition review.

No Stage 7 repair, Stage 8 training, selector, or runtime behavior change is implied.
