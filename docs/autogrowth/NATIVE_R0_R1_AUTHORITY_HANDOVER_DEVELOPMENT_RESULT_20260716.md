# Native R0→R1 Authority Handover Development Result

Date: 2026-07-16. Status: bounded engineering/development result on previously touched rows. This is not a fresh KRK confirmation claim.

## Verdict

The authority closure succeeded, but actual-child availability failed. The serialized R0 graph can choose under formal graph authority and retains 32/32 known R0 rows, yet formal branch confirmation alone does not tell R1 whether R0 is competent on a hypothetical successor. On the retired evaluation row, R0 confirmed all 65 reply-local queries across all 19 candidate first actions. The parent therefore received the same positive child strength for every legal action, selected the same move as both controls, and converted 0/1.

The single binding boundary is `actual_child_availability`. Do not classify this as a failure of virtual frames, graph choice, all-replies composition, spawning, or retention.

## Provenance

- Authority closure commits: `a1ebe54` and `d8cb0d5`.
- Prior touched source artifact: `reports/autogrowth/native_from_scratch/r0_r1_balanced96_240_seed_20260719_compact.json`.
- Reconstructed source pool manifest: `49a680bc4c91f91dc0c5f1d8b7f68c62e7dae8c75209d6e2470339d8f7935f12` (exact match).
- Frozen trainer-free organism: `snapshots/autogrowth/native_authority/r0_organism.pkl` plus hash metadata.
- Build report: `reports/autogrowth/native_authority/r0_organism_build.json`.
- Canonical development artifact: `reports/autogrowth/native_authority/retired_r1_handover_development.json`.
- Organism SHA-256: `bb58b7d64bd3ab5b696713a7253555e051bd0e9fdef4637db7c27e7517495eaf`.
- Build-report SHA-256: `bf8fc1839d5cc195811fd6902270047925db5d92cf76ff18bc454d2d364195ca`.
- Development-artifact SHA-256: `efc63749f2f99b0e8b3a729b3bdf99b416639e40f682d730a5a709f7de79db4d`.
- R0 reproduction and extraction runtime: 287.02 s, including 16-row serialization parity.
- Three-arm bounded run runtime: 1,157.90 s.
- Fresh data touched: none. Final pool touched: none.
- Focused authority/frame/manifest validation passed.
- Full repository validation: 881 passed in 2,032.37 s; zero failures.
- Ruff was unavailable in this checkout (executable permission denied; module not installed).

## Gate table

| Development gate | Result | Observation |
|---|---:|---|
| 100% graph-owned real actions | Pass | 1.0 in all arms |
| Exactly one actuator | Pass | zero multiplicity failures |
| Zero host fallback | Pass | zero in all arms |
| Old selector/provider/priority tripwires | Pass | 0 / 0 / 0 calls |
| Zero planted/oracle responses | Pass | every response came from the serialized R0 graph |
| Zero persistent dream leakage | Pass | zero mutations; firewall canary rejected all persistent capabilities |
| Empty-to-grown R1 topology | Pass | one new trial triplet per arm, `ABSENT→TRIAL` |
| Exact R0 retention | Pass | 32/32 in every arm |
| Child-caused action changes | Fail | 0 paired discordances vs disconnected and shuffled |
| Full better than both controls | Fail | all arms 0/1 conversion |

## What happened

The frozen R0 policy is accurate when evaluated on its known Mate-in-1 manifold: its emitted action mates on all 32 retained validation/regression rows. But R0 currently has no local, outcome-calibrated abstention boundary. On hypothetical positions outside that manifold, some learned action branch still formally confirms. The child response then combines that permissive confirmation with one global mature value and one global confidence. Every candidate R1 leg appears equally available and equally valuable.

This is visible in chess terms on `3K4/k7/7R/8/8/8/8/8 w - - 0 1`. The graph chose `h6e6`. After each of Black’s three replies, R0 emitted a legal move, but none mated. The dream did not verify those moves by executing them—correctly, because dream verification would be an oracle-like self-certification path. The error is that R0 said “I respond” where it needed to say “I am competent here.”

The all-replies SCRIPT behaved correctly: it required every reply-local response. Its input was simply nonselective. The disconnected and shuffled controls therefore chose the same training and evaluation actions. Shuffling an all-positive, equal-valued multiset cannot create a causal difference.

## Authority change

The before/after ownership table is in `docs/architecture/native_r0_r1_authority_closure.md`. In brief, the old Python weighted sort and `_choose_with_child_priority` are fail-hard in the experimental path. FormalReConEngine now emits exactly one actuator through a semantic-free CHOICE primitive. Python executes that identity but never receives a score list or selects a winner. Actual R0 queries run on deep-isolated boards and one isolated frozen-graph clone per parent decision.

## Performance finding

Generic retrieval budgets of 2, 4, and 8 candidates per actuator reduced 32-row R0 retention to 71.875%, 84.375%, and 96.875%. The full graph-owned budget of 16 is required for 100% and was fixed for the canonical run. One 19-action/65-successor parent query took 349.05 s. A future replicated package needs graph-native scheduling optimization and per-row checkpoints, but may not lower R0 resolution or reintroduce host ranking.

## Bound next decision

Preserve this negative result. Do not rescue it in-package with another provider, selector, terminal, lifecycle rule, dose, dream verification, or mate predicate.

The next isolated architectural factor, if externally frozen, is a graph-native R0 competence-availability/abstention signal learned from real outcomes. It must distinguish “a branch formally responds” from “this mature child has grounded evidence that it succeeds from this local state.” Training may use actual executed success/failure and the central curriculum boundary, but not mate distance, correct moves, forced-mate labels, or virtual self-verification. Until that boundary is learned and causally selective, do not open fresh R1 or R2 data.
