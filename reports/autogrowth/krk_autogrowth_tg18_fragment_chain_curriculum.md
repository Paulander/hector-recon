# TG18 Fragment-Chain Curriculum Summary

Artifact: `reports/autogrowth/krk_autogrowth_tg18_fragment_chain_curriculum.json`

Status: clean failure, rollback/quarantine.

TG18 tested the existing TG17/M16 fragment triplet-chain runway with three arms:

- protected baseline
- sham fragment-chain
- real fragment-chain autogrowth

Primary h40 result:

- baseline: 0/200 mates, 2,600 repetition events, 0 rook losses
- sham: 0/200 mates, identical to baseline on mate/repetition/safety
- real chain: 0/200 mates, 2,574 repetition events, 2 rook losses

Learning/chain signal:

- chain edges: 42
- training M3 updates: 16
- heldout M3 updates: 10
- heldout chain starts: 8
- heldout chain completions: 1
- after-terminal confirmations: 1
- M4 consolidation events: 0

Decision:

- `tg18_failed_cleanly`
- no candidate promotion
- candidate chain quarantined/pruned
- next recommended checkpoint: `TG19-LAG`

Interpretation:

TG18 showed a weak continuation signal by reducing repetition events, but it failed the safety gate because real chain behavior caused rook-loss regressions. Do not run longer over the same fragment-chain representation. The next isolated primitive to test should be LAG/temporal terminals for better activation precision and dead-loop detection, without direct move choice.
