# Research evidence index — 2026-11-13

See the [research handoff](RESEARCH_HANDOFF_20261113.md) for findings, limits
and the chess preparation order. Paths below are host locations, outside the
published Git tree unless noted. This index checks source identities and
selected reports/manifests; it does not replace the preserved readbacks or
reauthenticate bulk payloads. No historical packet was copied or modified.

## Hector-Recon chess

The chess repository is [Paulander/hector-recon](https://github.com/Paulander/hector-recon);
on this host its original checkout is `/Users/banquo/Documents/ChatGPT/Hector-Recon/source`.
Paths in this section are relative to `/Users/banquo/Documents/ChatGPT/Hector-Recon`
unless absolute.

| Evidence | Source authority and custody |
| --- | --- |
| Published native M1 | Pre-handoff `main` and tag `m1-native-replicated-2026-09-28` both resolved on GitHub to [`989cfb7e3f826ab71c05c590deacda259d72da2d`](https://github.com/Paulander/hector-recon/commit/989cfb7e3f826ab71c05c590deacda259d72da2d); learner implementation [`b0bc0c6fe26eba5bd3a0985403ca5a7b5a0b0130`](https://github.com/Paulander/hector-recon/commit/b0bc0c6fe26eba5bd3a0985403ca5a7b5a0b0130). [Tracked ledger](evidence/native_m1_replication_20260928.json) pins the recovery archive at `native-selective-m1-recovery-20260927/evidence/recovery_archive_data/native-selective-m1-recovery-20260927.tar.gz`, SHA-256 `06f3e29ecfb138a10034a4da3495cf1d5d1471bfc9dfda72d1c8fb808e9d781c`; adjacent `SHA256SUMS.txt` and `ARCHIVE_VERIFICATION.json`. The archive still depends on earlier packages including `native-selective-m1-readiness-20260925`. |
| Sparse discovery | Local `codex/sparse-terminal-discovery` at `f942b93af15f4b527bd4d289a3a2d2f54ffff796`, checkout `sparse-terminal-discovery-20261021-code/`. Protocol and design in its `docs/`. Reports and checksum lists: `sparse-terminal-discovery-20261021-evidence/REPORT.md` with `m1-pilot-901/SHA256SUMS.txt`; `sparse-terminal-discovery-alpha-continuation-20261024/` and `sparse-terminal-discovery-alpha-replication-20261024/`, each with `REPORT.md` and `SHA256SUMS.txt`. |
| Completed modular pilot | `m2-modular-pilot-fixture-repair-execution-20261010/`: `REPORT.md`, `FINAL_LEDGER.json`, `ARCHIVE_READBACK.json` and `seal/SHA256SUMS`. Archive `seal/m2-modular-pilot-fixture-repair-execution-20261010.tar.gz`: SHA-256 `28da1cc6546a7cd9feea1579772be5aae32242661176a9b169f06866fe8dc3da`; native snapshot `seal/NATIVE_SOURCE.tar.gz`: `ec81864653441281bd6f7338efe8157ae443ab4ca3cb664d666e9c9bbeef4f06`. The earlier `m2-modular-learning-pilot-execution-20261010/REPORT.md` records the unlaunched predecessor, a separate packet. |
| Fixed512, partial | `m2-modular-512-verification-recovery-20261021-saved-closure/`: `REPORT.md`, `FINAL_PARTIAL_LEDGER.json`, `CURRENT_SOURCE_READBACK.json`, `FINAL_DELIVERY_READBACK.json`. `CHECKSUMS.json` SHA-256 `a614d14ebec3f540ece5760fcf4f76efa59421d7bdcabd7eb38a0d3d6843873d` covers the **saved handoff packet**, with no complete archive seal or semantic V. The partial ledger lists the retained payload roots below. |

The pilot's `SOURCE_REUSE_INITIAL.json` names
`m2-modular-learning-pilot-execution-20261010-code/` as the qualified source
root. Its Git HEAD is unborn. The identical 77-file `source` maps in the
completed packet's `DECLARATION_frozen.json` and `DECLARATION_plastic.json`
match all 77 current files at that root. Compared with the published baseline,
25 of those paths are new and three differ: `formal_engine.py`,
`context_decision.py` and `terminal_development.py`. This checks the declared
slice; the seal binds the larger native snapshot. It does not qualify any
port or make the later continuation directory authoritative by its branch
name. The older `m2-modular-512-continuation-engineering-20261011-code/` also
has an unborn HEAD.

The fixed512 payload remains in
`/Volumes/T7/ReCoN-Archives/active-scientific-executions/m2-modular-512-verification-recovery-20261021/`,
`t7-scientific-control/m2-modular-512-verification-recovery-20261021/` and
`m2-modular-512-verification-recovery-20261021/`. Start from the saved
`CURRENT_SOURCE_READBACK.json`, the actual invocation and its source pins,
and the immutable producer capsules rather than either draft checkout.

## ReCoN Active Vision

Canonical repository: `/Users/banquo/Documents/ChatGPT/ReCoN-Active-Vision`.
The separate worktree `/Users/banquo/Documents/ChatGPT/Hector-Recon/learned-owner-selection-worktree`
is part of that repository, on `codex/learned-owner-selection-v1` at
`ac10ad1d9a43ce6971c65b45addc78d65bb628b3` at this handoff. Its provenance
records identify the pinned vendor and source inputs. Earlier child-practice
and supplied-handover findings are indexed in that repo's `STATUS.md` and
`results/`, including `learned_reacquisition_report_v1.txt` and
`learned_stabilizer_report_v1.txt`. Keep vision results and code in that repo.

Packet paths below are relative to `/Volumes/T7/ReCoN-Archives/ReCoN-Active-Vision`.
Read each `REPORT.md` with `CLOSURE.json`. These are the closure's canonical
JSON manifest SHA-256 values (sorted compact JSON, not the pretty-printed file
bytes). Each closure gives the recorded backup location.

| Packet | Status and manifest SHA-256 |
| --- | --- |
| `learned-owner-selection-v1/execution` | Verified parent study; joint criterion missed. `e84d9228dbe09269bf6f7af6d57a57ab0dd4d325d4f0143fe20719fd9c411906` |
| `learned-owner-selection-collapse-audit-v1` | Completed saved-data credit/margin audit. Manifest is the closure's `evidence` map. `e492d53e6013dc5d1bcfc9d2fc64962974a584cf101ed65d5de5475447149797` |
| `learned-owner-skill-coefficients-v1-evaluation-recovery` | Verified evaluation of the original actors; joint criterion missed. Original evaluation stop retained in `learned-owner-skill-coefficients-v1`. `17c255f22d0d58485b070679e1b87da4bd9bd638c956dc63603b408e4f7a836d` |
| `matched-first-loss-v1-20261112T214211Z-run` | Verified bundled diagnostic; schedule missed criterion. `152b420142bf75d42f7126c91c53a028a231f27ae717ead874a0deef6269e47d` |
| `matched-recovery-component-v1-20261113T090100Z-run` | Completed and independently verified component diagnostic. `d458936c3ed3cf5ce53579627d5755bddd44e171ca31a09a425e8c4c213a72a4` |
| `saved-loss-and-release-decision-audit-v1-20261113T092814Z` | Completed saved-data diagnosis. `7fd7fe49cf4ecd4c0c77eaad4b08f77aa2e99532d91d280af61fea7734127192` |
| `retinal-reader-lease-value-v1-prepared-20261113T101623Z` | Sealed preparation only, including `source/PROTOCOL.md`. Separately authorized fresh execution was ongoing at handoff. `8832aea2cc37a3c782d6608a136c040d67f4aba3f3790df581b877756826ea5f` |

The November architecture review remains in
`/Users/banquo/Documents/ChatGPT/Hector-Recon/architecture-continuity-review-20261111/`
with `REVIEW_BRIEF.txt` and `SOURCES.json`. It traces what the earlier
experiments established about terminal boundaries, ownership and development.
