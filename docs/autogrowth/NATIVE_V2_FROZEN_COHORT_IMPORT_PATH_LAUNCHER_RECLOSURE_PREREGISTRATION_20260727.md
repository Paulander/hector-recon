# V2 frozen-cohort import-path launcher reclosure — preregistration

Date: 2026-07-27

Starting commit: `5016f776a0a698033ff7df9e3dfed4311b51fa3a`

## Purpose

This is a launcher-only engineering correction. The stopped canonical-contract
module, its tests, manifests, failure and result remain immutable. The only
change is a separately named outer wrapper that invokes the exact frozen
`verify-order` command through this literal fully qualified import path:

```text
recon_lite_chess.autogrowth.native_v2_frozen_cohort_canonical_contract_reclosure
```

The path may not be derived from the runtime module name, a callable, `runpy`,
stack inspection or the parent command.

## Bound stopped package

- source freeze: `0859a4a1db53eb6221e3ac48e19d156896aa56c6`;
- manifest freeze: `7b41c9210aff57d0b8db2b5302754e68695836bb`;
- stopped result: `5016f776a0a698033ff7df9e3dfed4311b51fa3a`;
- failure SHA-256:
  `c345a35666a95d603472a01b935cd2ec4cedb8581996c8684568fb29ae0ff9c6`.

The 32 prefix organisms, 96 A/B/C snapshots, 32 candidate contracts, seeds,
targets and all existing manifests remain byte-identical. Discovery, arm
construction, cloning, filtering, replacement, exposure and outcomes are out
of scope.

The reused cohort is already known to contain the planted target in 32/32 seeds
and the selected comparison target in 30/32. The suffix remains unopened. Any
later scientific claim is conditional on this fixed, outcome-blindly reused
cohort and ecology.

## Launcher contract

The wrapper constructs every child command as:

```text
<same Python> -m <literal frozen child module> verify-order --order <order>
```

It uses the repository root as working directory and the stopped package's
deterministic environment subset. Child stdout must be exactly one JSON object.
The wrapper records exact parent and child argument vectors, executable,
working directory, deterministic environment, process IDs, return codes,
stdout hashes, stderr, runtimes, per-order outputs and digests.

A nonzero child exit or malformed result writes the independent launcher
failure artifact and stops. A completed order is never rerun in this package.

## Pre-cohort checks

Focused tests must prove:

1. the exact literal child module appears in generated argument vectors;
2. `__main__` never appears there;
3. a real wrapper process running as `__main__` still emits the stable path;
4. `find_spec` resolves the path to the exact frozen source and hash;
5. the public child `--help` command succeeds in a real fresh process under the
   later interpreter, working directory and deterministic environment;
6. fresh process identity differs from the parent;
7. a real nonzero child preserves argv, order, return code, stdout and stderr;
8. successful machine-readable child output is one clean JSON object.

These checks do not load a frozen organism.

## Single cohort execution

After the new wrapper, tests, preregistration, source manifest and artifact
binding are frozen and pushed, execute each existing frozen order once:

1. ascending;
2. descending;
3. even ordinals followed by odd ordinals.

Each process must use the literal stable child module. Pass requires:

- 3/3 fresh processes complete and differ from the parent and each other;
- 32/32 stored contracts verify in every order;
- all 96 organisms verify in every order;
- identical cohort and per-seed contract digests across all orders;
- zero candidate or graph mutation;
- zero exposure rows and zero outcome reads;
- all earlier stopped-package suffix paths remain absent.

Any child or aggregate failure is terminal. Preserve it and stop without
rerunning, repairing, filtering, rebuilding or replacing anything.

## Delivery boundary

Run only the focused launcher tests and this single three-order comparison. Do
not run the full repository suite because all protected sources remain
byte-identical. Commit and push the source freeze, manifest freeze and final
result separately. Stop before exposure for independent review.
