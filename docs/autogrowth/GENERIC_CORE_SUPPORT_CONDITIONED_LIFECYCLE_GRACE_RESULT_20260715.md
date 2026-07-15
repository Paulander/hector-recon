# Generic-Core Support-Conditioned Lifecycle Grace Result

Date: 2026-07-15. Status: canonical package complete and closed. This is a
generic-core mechanism experiment, not native KRK evidence and not transfer
authorization.

## Provenance and integrity

The preregistration was committed at `22f8c27`, the validated implementation at
`8a71e73`, and the exact admission manifest at `94c7706`. The same live process
paused before phase 1, verified the manifest bytes from HEAD, and resumed. The
first twenty candidates, seeds 20262401--20262420, all admitted; no later seed in
the capped 20262401--20262440 pool was touched.

Canonical compressed artifact:
`reports/autogrowth/generic_core/support_conditioned_lifecycle_grace_20260715.json.gz`.

- Uncompressed SHA-256:
  `96fa1cfaf62c92fee1d9a316927ad67a743a50f167f952ff73bdeceeced6b1e3`
- Compressed SHA-256:
  `5f062809538c9aaac0d2c197ff564132385d912d9997e20d88aed2aa331ee271`
- Admission SHA-256:
  `2e281f18c6da612939dc49996c9a0a2a67d88f52bf584a0fc477acb4c7af29b9`
- Task-row SHA-256:
  `087efd8169f8076db6a63f7121bcd89b9cafdd20f6237cdbb88b9cc043439f13`

All 20 cells passed the measurement/integrity gate. Exact/full-scan support,
graph identity/firewall, terminal backend, right-censor, RNG/event/row budget,
clone, final-return, and role-blind audit checks had zero failures. The fixed
reference stability gate passed. Pre-fresh validation was 48 focused tests plus
one retired full-horizon five-arm smoke. The pre-fresh full repository suite
passed 868 tests in 2,136.77 seconds; the post-result suite passed the same 868
tests in 2,105.55 seconds.

## Preregistered verdict

| Gate | Verdict | Canonical observation |
|---|---:|---|
| Measurement/integrity | **Pass** | 20/20 invariant cells; zero integrity failures |
| More life vs two-review | **Pass** | Conditioned minimum support higher in 18/20; median +12.5 |
| Conditioned evidence | **Fail** | All four reached support 32 in 9/20, required 16/20; deaths 2/80 |
| Conditioned maturation | **Fail** | All four matured with positive rent in 8/20, required 16/20 |
| Self-regulation vs fixed-six | **Fail** | Evidence/maturation tied, but occupancy only 1.46% lower and blocks/displacements lower in 4/20 |
| Behavior | **Fail** | Median old/new 0.923/0.692; only 4/20 mastered both |
| Stability | **Pass** | Fixed reference median old/new 1.0/1.0; 16/20 mastered both |
| Priority | **Not identified** | 908 unequal opportunities among 74,220; descriptive only |

`support_conditioned_self_regulation` is false, `behavioral_readiness` is false,
and `native_transfer_authorized` is constitutionally false.

## Arm comparison

| Exact-directed lifecycle | All four support 32 | All four mature + positive rent | Median weakest support | Targets supported | Unsupported deaths | Right-censored targets | Median old/new | Both >=0.85 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Two reviews | 1/20 | 1/20 | 14.5 | 61/80 | 19 | 0 | 0.966 / 0.651 | 1/20 |
| Fixed six | 9/20 | 8/20 | 29 | 69/80 | 1 | 10 | 0.879 / 0.692 | 4/20 |
| Conditioned six | 9/20 | 8/20 | 29 | 69/80 | 2 | 9 | 0.923 / 0.692 | 4/20 |

The fixed and conditioned arms had median live-trial occupancies 3.203 and 3.156.
Conditioned had fewer challenger blocks and fewer displaced eligible proposals in
only 4/20 paired tasks. Their paired median weakest-support and behavior
differences were both zero.

## Interpretation

The positive result is narrow but real: the two-review lifecycle was prematurely
killing potentially useful structures. Giving trials up to six reviews raised
individual target support from 61/80 to 69/80, reduced unsupported deaths from
19 to 1--2, and raised all-four maturation from 1/20 to 8/20.

The proposed self-regulation mechanism did not earn a stronger claim. Fixed-six
and conditioned-six produced the same task-level support, maturation, median
weakest support, and new behavior. The progress/request conjunction saved almost
no capacity and did not reliably reduce challenger blocking or proposal
displacement. Under the preregistered strongest null, the gain is explained by
**more life**, not useful support-conditioned control.

The tail matters but does not rescue the result. Of the eleven conditioned tasks
that failed the all-four support gate, nine missing targets ended right-censored
with 3--5 reviews and two ended through conditioned no-progress/budget
transitions. The fixed arm showed ten censors and one budget death. These late
births are legitimate failures under the frozen horizon and explain why 69/80
individual targets still yielded only 9/20 complete target sets. They also show
that conditioned grace failed its intended capacity-release function; they do
not authorize extending the horizon or adding throughput post hoc.

## Bound next decision

Close support-conditioned lifecycle grace at the frozen six-review dose. Do not
extend life, increase exploration/proposal throughput, tune the progress window,
or open native KRK on this result. Before another fresh experiment, an external
audit should use this artifact to adjudicate the late-birth/challenger-blocking
tail and choose one isolated factor. The current package does not preregister
that choice.

Internal terminals remain a valid architectural primitive, and virtual-frame
handover canary v2 remains a causally tested planted engineering mechanism. This
negative self-regulation result does not invalidate either architecture, but it
does mean neither is yet an autonomous learned KRK handover. Native R1/R2 remain
closed and unchanged.
