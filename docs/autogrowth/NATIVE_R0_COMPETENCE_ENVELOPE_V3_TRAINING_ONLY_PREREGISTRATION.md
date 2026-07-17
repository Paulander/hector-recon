# Native R0 competence-envelope V3 training-only preregistration

Date: 2026-07-17
Status: frozen before execution
Authority prerequisite: deterministic closure commit `133ba03` passed

## Scope and immutable learning factors

V3 is the V2 learner rerun under the corrected deterministic runtime. It uses
the identical already-touched 64-frame tape, learner, member-choice genome,
thresholds, capacities, three structural rounds, and seeds. It has connected
and outcome-shuffled arms and a descriptive global baseline of `40/64 = 0.625`.

The runner imports V2 observation/reporting functions and the unchanged native
competence-envelope learner directly. Their frozen SHA-256 hashes are checked
before work begins:

- V2 runner module: `b2f499131b7628faa1211273c298070c693e94f767a59c9ae7510019e67e9341`
- learner module: `65dda4f09bc1181a6fe3780c27b56da4fc888a377ae3cfffe3c728e9d11d2a7b`

Do not access validation, regression, the 65 retired successors, R1, final, or
fresh data. Stop after the three-round lifecycle regardless of outcome.

## Deterministic admission

Generate a new 64-row reference by querying a freshly serialized/restored empty
competence wrapper under the corrected deterministic runtime. Persist all
reference rows and their digest. Replay the same frames through the real
observation path and require:

- exact complete `GraphActuation` and active-signal parity on all 64 frames;
- exactly 40 successes and 24 failures;
- 64 policy responses and 64 unique evidence identities;
- zero fabricated reward;
- exact persistent direct and wrapper state; and
- zero authority tripwire calls.

Every mismatch must persist its frame index, FEN, field, real value, and
reference value. Floating activation mismatches additionally persist exact
IEEE-754 bits. Admission may never collapse these data to one Boolean.

## Frozen arms

1. Connected: actual outcomes.
2. Outcome-shuffled: identical evidence with outcome responsibility permuted by
   seed `2026071602` and the V2-frozen permutation digest.

Both use unchanged `GraphNativeCompetenceEnvelope` defaults: support 4, Wilson
z `1.6448536269514722`, lower bound `0.55`, positive/refuted capacities `32/32`,
trial/proposal caps `192/192`, exactly three rounds, genome seed `2026071606`,
and retrieval budget 16.

## Bounded exhaustive diagnostic

After lifecycle, enumerate every eligible base-signal singleton, pair, and
triple. Do not persist every pattern. Persist instead:

- exact tested, support-qualified, and pure counts by arity;
- exact support, polarity, mixture, attempt, admission, rejection, and maturity
  histograms;
- a deterministic SHA-256 digest over every pure pattern record; and
- at most eight deterministic examples per arity.

The diagnostic is read-only and cannot feed either learner arm.

## Frozen verdict

Apply the first matching branch:

1. No pure support-qualified pattern exists: current representation/selectivity
   is insufficient.
2. Pure patterns exist but none were attempted: nomination/responsibility
   failure.
3. Pure patterns were attempted but none admitted: proposal
   admission/capacity failure.
4. Pure patterns were admitted but none matured: lifecycle/evidence-accounting
   defect.
5. Mature selective cells appear: native competence learning engaged; compare
   connected against outcome-shuffled and stop.

If V3 again finds pure patterns that the genome never nominates, the next
learning mechanism is residual-responsibility internal terminals—not more grace
or proposal throughput.

## Recorded architectural debt

`extract_active_competence_signals` currently reconstructs generic, label-blind
signals from the board, selected move, and graph maps instead of consuming the
actual frame-local terminal trace. This does not invalidate V3, but it means a
claim of fully self-contained native ReCoN remains premature. If V3 is
promising, graph-emitted internal-terminal provenance is the next authority
closure. This debt is recorded only; V3 does not alter it.

