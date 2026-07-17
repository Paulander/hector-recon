# Deterministic native activation closure

Status: engineering-only, frozen after `dd5728d`. The V2 admission abort and
its canonical artifact remain immutable.

## Localized defect

Independent process-level localization found 57--59 mismatches among the 64
touched frames, depending on the compared processes. Every mismatch was
exclusively in `GraphActuation.activation`, below approximately `4e-16`.
Discrete actions, actuator identities, option identities, candidate counts,
formal tick counts, graph-ownership flags, fallback flags, and active competence
signal identities were exact.

Although this did not change the observed decisions, activation is
policy-critical. Near a tie, the same drift could change an action. Therefore
the contract remains bit-exact; it is not weakened with tolerances or rounding.

## Frozen repair

Every unordered policy-critical numerical reduction in the implicated native
path must:

1. identify each contribution;
2. sort by that identity;
3. collect the numerical contributions; and
4. combine them with `math.fsum`.

This applies to graph child activation, native terminal and composite evidence,
final native action strength, and anonymous choice sum/mean aggregation.
`PYTHONHASHSEED`, rounding, comparison tolerances, and removal of activation
from the parity contract are forbidden remedies.

## Canonical closure

The closure uses only the already-touched 64-event tape. Before any gates are
evaluated, the artifact must persist every field-level real-versus-restored-
wrapper mismatch, including IEEE-754 activation bits. It then requires:

- bit-exact complete `GraphActuation` and active-signal parity;
- all 64 discrete actions/options unchanged from the preserved authority
  addendum;
- exactly 40 completion successes and 24 failures, unchanged row by row;
- unchanged evidence identities;
- exact persistent organism identity; and
- zero fabricated reward.

If any discrete action, signal, evidence identity, or outcome changes, the
package stops. Otherwise it reruns only the bounded planted mature-envelope
authority regression, not the old long authority investigation.

The requested V3 run is not specified in the authorizing message. Passing this
closure therefore authorizes no inferred V3 design or execution; it stops for
the missing frozen V3 specification.

