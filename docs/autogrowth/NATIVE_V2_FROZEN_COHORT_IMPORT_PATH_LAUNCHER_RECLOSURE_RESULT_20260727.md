# V2 frozen-cohort import-path launcher reclosure — result

Date: 2026-07-27

## Verdict

Pass. The separately frozen wrapper launched the exact immutable child module
through its literal fully qualified import path in three fresh processes. All
three frozen seed orders completed. Every order verified all 32 candidate
contracts and all 96 A/B/C organisms with no candidate or graph mutation. The
cohort and per-seed contract digests were identical across orders. Exposure and
outcomes remained unopened.

This is an engineering closure of the launcher and prefix-to-snapshot identity
boundary. It is not an exposure result, causal result or KRK result.

## Frozen source and binding

- Starting commit:
  `5016f776a0a698033ff7df9e3dfed4311b51fa3a`.
- Launcher source freeze:
  `dfd486a57868309a04df263ce49717d89e37b583`.
- Launcher manifest freeze:
  `a54c42191944cac00018cf13e33e8500e0ab47e5`.
- Source-manifest SHA-256:
  `c296034ec4b7c9d7c1e5394bc41efc256b577422a108009ae1785d8d433e04d4`.
- Source-manifest canonical digest:
  `457a267d8aa2a3dda8341bd1ea73963276cc22ca9807a5e1a3d9eacf1aea92e0`.
- Artifact-binding SHA-256:
  `39165254df9f8a833058faff4681abe677eff4d04a8d6dfddbd41f8789347f50`.
- Artifact-binding canonical digest:
  `106748944c333d2a9dab449c2bc574db5352c401b04e4888d219e6e4f2ab49ea`.

The stopped source freeze `0859a4a`, manifest freeze `7b41c92`, stopped result
`5016f77`, and failure artifact SHA-256 `c345a35666a95d603472a01b935cd2ec4cedb8581996c8684568fb29ae0ff9c6`
remain unchanged. The earlier V2 runner, learner, graph, 32 prefix organisms,
96 snapshots, candidates, seeds and target selections remain byte-identical.

## Launcher identity

Fixed child module:

```text
recon_lite_chess.autogrowth.native_v2_frozen_cohort_canonical_contract_reclosure
```

Python executable:

```text
/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit/.venv/bin/python3
```

Working directory:

```text
/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit
```

Parent PID was `1077155`; child PIDs were `1077205`, `1081481`, and `1083186`.
Every stored child argument vector used the literal module above. The result
also stores the exact parent argument vector and deterministic environment.

## Checks and canonical execution

Focused launcher checks passed 8/8 in 14.07 seconds (16.48 seconds external
wall time). They used real processes for wrapper-as-`__main__`, child `--help`,
clean JSON output and a deliberate nonzero exit. They did not load an organism.
Manifest freezing completed in 6.35 seconds.

Canonical order results:

| Order | Wrapper runtime (s) | Child runtime (s) | Order-result digest |
|---|---:|---:|---|
| ascending | 1615.707323 | 1612.937810 | `a4d56f6629cf67647cee758a46159df22088821eecb4a62b2edbcb502fc94032` |
| descending | 1555.060834 | 1552.311337 | `6317754773acf390103e26d0d3581e4c594ec778007cf3c43fc02cbfd450f6cd` |
| even-then-odd | 1561.543797 | 1558.590748 | `3e74ffb7f11ef5fe449a37bc63f0e9814cb3cbe4cb5429db2b010849e4b01273` |

The canonical artifact's monotonic total was 4732.314753 seconds. The external
shell timer reported 4546.26 seconds; both readings are retained rather than
silently reconciling their clock difference.

## Gate results and hashes

- Fresh child processes: 3/3.
- Contracts: 32/32 per order.
- Organisms: 96/96 per order.
- Identical cohort digest:
  `a144fe94f4479c819756dfc44b22a2594e2b9df09367d571d39ab54007560bb8`.
- Per-seed contract-digest set:
  `62c940dada05d6073682caa6bc3150af18a1157bcc7fd62d291d01630962f223`.
- Candidate or graph mutations: 0.
- Exposure rows read: 0.
- Outcome reads: 0.
- Failure artifact: absent.
- Result artifact size: 79,565 bytes.
- Result artifact SHA-256:
  `92cf2e099a1f860deef4c90515f6b0617d7b95af521ab1c8604baecccd7202df`.
- Result canonical digest:
  `24a10043dce9894caac1db11dbb191011d92376e2e39b42f058bd53ff444e71c`.

## Interpretation and stop boundary

The old `__main__` launcher failure is closed by a stable import path without
modifying or rerunning the stopped package. The original raw-dictionary abort
remains reproducible, while the corrected canonical contract comparison now
passes the complete fixed cohort and is invariant to the three frozen seed
orders.

Discovery is already known to contain 32/32 planted targets and 30/32 selected
comparison targets. The evaluation suffix remains unopened, so any future
claim remains conditional on this fixed, outcome-blindly reused cohort and
ecology. This package stops before exposure for independent review.
