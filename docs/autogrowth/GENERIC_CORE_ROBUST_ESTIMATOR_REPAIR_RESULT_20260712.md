# Generic-Core Robust Estimator Repair: Raw Development Result

Date: 2026-07-12. Track: generic-core development. Confirmation claim: none.
Builder and runner are the same agent.

## Frozen execution

The PI-authorized replacement contract was committed and pushed at `4ceb3b2`.
The calibrated estimator and initial runner were committed at `aaf700f`.

The first runner invocation failed at module import before entering `main`:
`ModuleNotFoundError: No module named 'scripts'`. It generated zero task rows
and wrote no artifact. The already-frozen two-function environment helper was
embedded verbatim, the failure was added to artifact metadata, calibration was
rerun, and the self-contained runner was committed at `1711306`. Only then was
the fresh seed range generated and executed once.

## Estimator calibration

Before the policy run:

- exact 7 × +1 / 1 × -1 streams retained mean +0.75 after 256, 1,024, and
  4,096 observations;
- mixed deterministic streams matched `math.fsum / count`;
- retained tail storage never exceeded 256;
- rare -1 exceptions survived repeated compression;
- graph edges matched the selected exact-mean or lower-tail statistic;
- the full generic library suite passed 43/43.

## Raw gates

| Measurement | Frozen requirement | Observed |
|---|---:|---:|
| Mean chooses refutable action | at least 19/20 | 20/20 |
| Lower-tail chooses consistent action | at least 19/20 | 20/20 |
| Lower-tail minimum exceeds mean minimum | at least 19/20 | 20/20 |
| Refutable exact mean within 0.10 of +0.75 | at least 19/20 | 20/20 |
| Graph/estimator mismatches | zero | zero |
| Matched configured budgets | 20/20 | 20/20 |

Across tasks, the mean arm's refutable estimate had:

- mean 0.750101, median 0.749931, range 0.742857–0.757040;
- 1,660–1,916 total observations;
- exactly 256 retained lower-tail sketch values.

The mean arm selected the refutable action throughout evaluation, producing
mean +0.75 and minimum -1.0. The lower-tail arm selected the consistent action,
producing mean and minimum +0.4.

Artifact:
`reports/autogrowth/generic_core/robust_estimator_repair_fresh_20260712.json`

- artifact SHA-256:
  `bf1424def72e946d69b8bd0965238639e609c235ba7b6584c4d2153a69ed1c9e`;
- source commit:
  `1711306ed438fc9de54cf813eccbed2352fcd5ba`;
- task-row SHA-256:
  `efa47f2ec97c91a4e155a23759c6f1427ada0e6ac897f43a87ab5cdf9141c34a`;
- return implementation SHA-256:
  `a6e14edb6fa47f8c865265234073bc3c52d6f888d5c9231a35af7c99648169c8`;
- graph-policy implementation SHA-256:
  `2d564513d205a29a3b63498384b0a4cffca1fef889369e4d82b371440445f8b0`;
- runner SHA-256:
  `737b6b5273e716539f7bc00f098b9088426abc808e7876028913d6ebc3eaea34`.

## Supported statement

On this fresh anonymous rare-refutation family, ReCoN graph action edges carried
the exact return statistic used for live choice. Exact streaming mean and
conservative lower-tail value produced the preregistered behavioral divergence
under matched online exploration and response streams. The earlier failed
comparison was correctly diagnosed as mean-estimator contamination.

## Limits

- This remains builder-run development evidence.
- The conservative tail sketch is lifetime exception memory, not an unbiased
  quantile reservoir or recent-window change detector.
- The environment is a one-state action bandit. It does not test contextual
  composition, temporal responsibility, options, multi-state dynamics, or
  transfer in the same learner.
- The action identities, episode boundaries, and scalar return remain
  environment interfaces.
- Passing this package does not independently confirm the earlier composition
  and delayed-policy packages.

## Next authorized boundary

The PI authorized proceeding to a genuine multi-state key-door integration if
this repair passed. That next package must be independently preregistered and
must combine the unchanged positive mechanisms without tuning them:

- multiple changing observations and learner-selected actions per episode;
- persistent responsibility to terminal-only valence;
- anonymous identity permutation;
- residual-grown graph topology with causal ablation;
- lower-tail exception memory;
- a mid-run dynamics change;
- retained old competence plus measurable adaptation.

It must not be described as KRK evidence or imagination/dreaming.
