# Native V2 Outcome Execution — Instrument Stop

Date: 2026-07-29

Source commit:
`e02423739fbd27809a6b6c820aa85e59898fe728`

Science service attempt:
`20260729T154354756091Z-04d8f7e03f144963a272919e64c7f221`

## Verdict

**INSTRUMENT FAILURE BEFORE SCIENCE START.**

This is not a mechanism pass, valid scientific negative, or engagement
failure. The frozen science child stopped while reconstructing the committed
exposure journal for admission, before it created the science-start marker or
outcome environment.

The exact exception was:

```text
ProcessResilienceError: changed or foreign PREPARED unit:0
```

It arose in `validate_completed_exposure()` through
`validate_exposure_journal_admission()` and `ExposureUnitJournal.analyze()`.
Per the frozen stop rule, the attempt was not repaired or relaunched.

## Preserved boundary

- Service start: `2026-07-29 17:43:54 CEST`
- Service end: `2026-07-29 21:31:19 CEST`
- Exit status: `1`; signal: none
- Terminal result: `exit-code`
- Standard-error bytes: `2059`
- Standard-error SHA-256:
  `3b9ed489f1d9c78f6a875f6cfee74e7eae2db83e50e91b66f17962781074ab95`
- Final service-record SHA-256:
  `89817fd49af81df63427816512d91900d9f4c537ca7bf890dc758a45bbba3b46`
- Final service-record digest:
  `72760a7456ad311c8f043a1a12599b75c3a98f726f811556b20bceab873dc233`
- Cleanup adjudication digest:
  `4ef49df23cd33d4530ba3f56fdad8128226a9489be796aa044ab220abab57dc8`
- Cleanup succeeded and the retained service unit is absent.

No `science_started.json`, science journal, carrier, canonical result,
science-failure artifact, or outcome-result binding was created. The failure
preceded outcome-environment construction, and no outcome was read or consumed.

Consequently, engagement gates, A/B/C endpoints, per-seed comparisons,
wins/losses/ties, effective sample sizes, corrected probabilities,
contradiction/revocation counts, and all scientific pass/fail gates are **not
evaluated**.

Only the finalized service record was added to the repository. Partial
scientific state was not inspected. The external standard-error log remains
bound by its exact size and SHA-256 in that record.
