# Native prospective evidence V2 scientific discriminator — integrity abort

Date: 2026-07-24

## Verdict

The bounded V2 prospective-evidence discriminator is closed as an
**instrument abort**. It produced no positive, negative, engagement, or causal
scientific result.

The outcome-blind gate passed and was frozen first. The canonical suffix then
failed hard on the exact error:

```text
ScientificIntegrityError:
preoutcome arm bytes changed before suffix:0:B
```

The package is not repaired or rerun.

## Frozen work that passed

- Protected V2.1 authority and registry sources remained byte-identical at
  `25945864fd998caf22ae12cbcb9bcb4779447337c0079f705640c63d2356f029`
  and
  `f3aee5cccf761af1cb6a5de94b886d5e758c0a07cb0f6d77b8898f662ca73b58`.
- The complete outer source/runtime identity was frozen before canonical
  discovery.
- The permanently retired two-seed process canary failed byte parity, so the
  preregistered serial fallback was used without relaxing equality.
- Native prefix discovery retained all 32 seeds. The exact planted candidate
  existed in 32/32; an eligible deterministic spurious target existed in
  29/32; both existed in 29/32.
- The registry-owned outcome-blind exposure pass completed after approximately
  8h21m. All three registries admitted; A/B/C row-level classifier-visible
  parity passed with zero failures; 29/32 seeds qualified against the required
  24/32, with eight distinct opportunities for each present target.
- That gate is frozen at commit `2a5ec3fe768dd4cae3d0087b093cb7bb490f41f9`.
  Its artifact SHA-256 is
  `087403387a7e3c10b7a7deb34f81de8a770d02db318e95760cc7f035de8dd2b5`
  and its internal digest is
  `d9bee547813c0c744984cf6b8dcc5166cdcc2a1e49d34a76c720bf9440a61390`.

These are engineering/admission facts only.

## Exact suffix failure and data access

The serial suffix reconstructed seed 0 arms and successfully matched the
pre-outcome byte hash for A. The frozen loop then executed all 16 arm-A suffix
events before checking B. B's reconstructed serialized SHA-256 did not equal
the byte hash frozen by the pre-outcome scan, and the fail-hard check raised
before B execution.

Consequently:

- 16 seed-0/A suffix outcomes were opened and consumed in process memory;
- no seed-0/B, seed-0/C, or later-seed outcome was opened;
- no complete seed result, event row, endpoint, or canonical gzip artifact was
  persisted;
- the runner did not persist the observed B hash or a field-level byte
  difference;
- the 16 opened events cannot lawfully be reconstructed by rerunning the seed.

This scope follows directly from the frozen execution order in
`_run_canonical_suffix_seed`: verify A, complete `_execute_suffix_arm(A)`,
verify B, then execute B. It is not an inference from scientific values.

## Scientific consequence

Mechanism engagement, `D_safe`, `D_signal`, sign tests, Holm adjustment, and
all causal interpretations are **not adjudicated**. The pre-outcome admission
pass cannot substitute for them. The experiment therefore says nothing about
whether prospective evidence is safer or more useful than legacy authority or
the truthful C control.

The exact machine-readable closure is
`reports/autogrowth/native_authority/v2_scientific_discriminator/suffix_integrity_abort.json`.
No `canonical_result.json.gz` exists.

## Boundary exposed

Two instrument boundaries are now explicit:

1. suffix reconstruction did not reproduce the pre-outcome serialized bytes
   for seed 0 arm B under the frozen serial process;
2. the runner verified each arm immediately before executing that arm, rather
   than verifying every seed/arm byte identity before opening the first
   outcome.

The first cause is deliberately not investigated or repaired in this closed
package. The second ordering allowed a partial stream to open before the later
arm mismatch was detected. Any future package requires a separately frozen
engineering reclosure that proves all arm identities before any outcome and
persists expected/observed hashes plus field-level mismatch evidence. It must
not reuse this scientific suffix as a confirmation stream.

## Validation provenance

Before execution:

- new focused/adversarial suite: 9 passed in 214.63 seconds;
- post-manifest ownership regression: 1 passed in 3.79 seconds;
- critical V2.1 subset: 5 passed in 625.91 seconds;
- exact adjacent suite: 54 passed in 651.29 seconds;
- the 1,013-test V2.1 certificate was carried forward because both protected
  hashes remained exact.

No KRK validation/regression/fresh pool, retired-65 successor, R1 stream, or
other prohibited data was opened.
