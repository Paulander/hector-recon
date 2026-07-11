# Run brief: balanced native intrinsic R0/R1

Date: 2026-07-11  
Branch: `codex/native-from-scratch-krk`

## Outcome

| Run/arm | R0 validation | R0 regression | R1 validation | R1 regression | R0 retained | Verdict |
|---|---:|---:|---:|---:|---:|---|
| First preregistration, random R0 | 6/8 | 8/8 | not run | not run | n/a | R0 gate failed |
| Correction, full intrinsic | 16/16 | 16/16 | 8/16 | 5/16 | 16/16 | causal partial R1; no promotion |
| Correction, no bootstrap | same snapshot | same snapshot | 0/16 | 0/16 | 16/16 | control flat |

The correction confirms that high-resolution edge/corner balancing fixes the R0 coverage problem and that mature-child bootstrap causally improves R1. It does not close R1.

## Frozen design

- Empty learned start: one root, zero learned edges/triplets/weights.
- R0: 48 train, 16 validation, 16 regression; six/two/two examples per four edges and four corners.
- R1: 48 train, 16 validation, 16 regression; balanced rook barriers, king-edge approaches, and four corners.
- All R0/R1 splits D4-orbit-disjoint; 40 observed R0 development positions and their orbits retired.
- Pool hash: `49a680bc4c91f91dc0c5f1d8b7f68c62e7dae8c75209d6e2470339d8f7935f12`.
- R0 cap 96, R1 cap 240, zero R0 replay, immediate joint-100% freeze.
- Full intrinsic versus no-bootstrap; same frozen R0 snapshot and legal-action schedule.
- Correct/forced moves used only for curriculum scheduling and measurement, never learner credit.

## Exact correction result

R0 stopped at epoch 8 after 384 episodes and 93.56 seconds. It scored 16/16 validation and 16/16 regression with zero null, illegal, stalemate, or rook-loss selections.

Full R1:

- 11,520 episodes; 939 distinct first actions; 2,493 unique action/reply exposures.
- 1,591 mature-child handoffs; 11,241 virtual-frame queries.
- 8/16 validation; 5/16 regression; 16/16 R0 retention.
- Peaked at 9/16 validation at epochs 180–220, ended 8/16 at 240.
- 0 formal-confirmation failures and 0 child-cache live mismatches.
- 10,909.73 seconds (~3h02m).

No-bootstrap:

- Same 11,520 episodes/actions/replies; zero child handoffs/virtual queries.
- 0/16 validation; 0/16 regression; 16/16 R0 retention.
- 0 formal-confirmation failures.
- 3,035.72 seconds (~50m36s).

Decision: `r0_pass=true`, `r1_pass=false`, `r1_causal_positive_vs_no_bootstrap=true`, `advance_to_r2=false`.

## Failure interpretation

Post-hoc chess audit found 19 full-arm held-out failures:

- 11 premature rook checks instead of a nearby quiet barrier placement;
- 8 wrong quiet rook offsets or king-approach squares.

The relevant sensor atoms are distinct. Balanced exposure removed gross orientation absence, but current shared-atom and hierarchy-edge weighting did not autonomously form a sufficiently selective conjunction/competition rule.

## Implementation/test updates

- Added balanced R1 strata and per-stratum held-out metrics.
- Added balanced R0 edge/corner strata after the preregistered R0 failure.
- Added D4 orbit isolation across train/validation/regression.
- Added explicit retired-development FEN input and manifest hash.
- Added reproducible preregistration scripts and CLI pool-mode flags.
- Focused changed-path suite: 11 passed in 32.84 seconds.
- Earlier focused suite before R0 correction: 10 passed in 31.53 seconds.
- Broad autogrowth run: 205 passed in 1,442.02 seconds, then manually interrupted in an unrelated long integration test; zero failures observed.
- Compile and `git diff --check` passed. Ruff could not be executed because the installed executable returned `Permission denied`.

## Artifacts

- `reports/autogrowth/native_from_scratch/r1_highres_balanced_seed_20260718_preregistration.json`
- `reports/autogrowth/native_from_scratch/r1_highres_balanced240_seed_20260718.json`
- `reports/autogrowth/native_from_scratch/r0_failed_seed_20260718_retired_fens.json`
- `reports/autogrowth/native_from_scratch/r0_r1_balanced_seed_20260719_preregistration.json`
- `reports/autogrowth/native_from_scratch/r0_r1_balanced96_240_seed_20260719_compact.json`

The full 23 MB artifact remains local at `reports/autogrowth/native_from_scratch/r0_r1_balanced96_240_seed_20260719.json`, SHA-256 `1a4a70ab17c0caf1c1a6cf878b5db3ab707bd02209a56e7bd8a7031fa08af5ed`. It is not intended for ordinary Git history.

## Next action

Do not rerun unchanged and do not advance to R2. First add resumable interval snapshots and parity-preserving acceleration, then implement outcome-driven self-grown composite proposals with matched-random controls and alternating structural/equilibration/consolidation epochs. Preregister fresh R1 pools after those mechanisms freeze.
