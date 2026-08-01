# Frozen WSL user-service commands

Run these only from the normal WSL terminal with the current directory set to:

`/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit`

The harmless canary may be run for service-transport review. The real series
must not be run until separately authorized, and its canonical checkout must
first be clean at exact commit
`8479cbdd22ed06d09eea3bd051a2e0e8344063ec`.

## Harmless canary start

```bash
systemd-run --user --unit=hector-recon-v2-canary-2ec72b8bab3d4965a987e8b7433e19cc.service --service-type=exec --property=Restart=no --property=RuntimeMaxSec=infinity '--working-directory=/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit' '--property=StandardOutput=append:/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/systemd-foreground-1107519c8a4448ed8e7bc134b8a68140/canary_service.stdout' '--property=StandardError=append:/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/systemd-foreground-1107519c8a4448ed8e7bc134b8a68140/canary_service.stderr' --no-block --setenv=HOME=/home/banquo --setenv=LANG=C.UTF-8 --setenv=LC_ALL=C.UTF-8 --setenv=MKL_NUM_THREADS=1 --setenv=NUMEXPR_NUM_THREADS=1 --setenv=OMP_NUM_THREADS=1 --setenv=OPENBLAS_NUM_THREADS=1 --setenv=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin --setenv=PYTHONHASHSEED=0 --setenv=PYTHONNOUSERSITE=1 '--setenv=PYTHONPATH=/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit/src' --setenv=RECON_CANARY_UNIT=hector-recon-v2-canary-2ec72b8bab3d4965a987e8b7433e19cc.service --setenv=RECON_RECOVERY_SERIES_ID=systemd-foreground-1107519c8a4448ed8e7bc134b8a68140 --setenv=TZ=UTC '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit/.venv/bin/python3' '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/systemd-foreground-1107519c8a4448ed8e7bc134b8a68140/harmless_systemd_canary.py' run --manifest '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/systemd-foreground-1107519c8a4448ed8e7bc134b8a68140/outer_manifest.json' --manifest-sha256 2f9895f3a9a7c7b6aae99615b5739a2eb4fdab8efc7244a814e20e9d68aa0b28
```

## Harmless canary status

```bash
systemctl --user show hector-recon-v2-canary-2ec72b8bab3d4965a987e8b7433e19cc.service --property=Id,LoadState,ActiveState,SubState,Result,ExecMainCode,ExecMainStatus,MainPID,Type,Restart,RuntimeMaxUSec,WorkingDirectory --no-pager
```

## Harmless canary verification

Run after at least 80 seconds:

```bash
'/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit/.venv/bin/python3' '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/systemd-foreground-1107519c8a4448ed8e7bc134b8a68140/harmless_systemd_canary.py' verify --manifest '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/systemd-foreground-1107519c8a4448ed8e7bc134b8a68140/outer_manifest.json' --manifest-sha256 2f9895f3a9a7c7b6aae99615b5739a2eb4fdab8efc7244a814e20e9d68aa0b28
```

## Real series start — frozen but not authorized in this package

```bash
systemd-run --user --unit=hector-recon-v2-admission-e697c46cf43a4129a54d24341be70e29.service --service-type=exec --property=Restart=no --property=RuntimeMaxSec=infinity '--working-directory=/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit' '--property=StandardOutput=append:/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/systemd-foreground-1107519c8a4448ed8e7bc134b8a68140/series_service.stdout' '--property=StandardError=append:/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/systemd-foreground-1107519c8a4448ed8e7bc134b8a68140/series_service.stderr' --no-block --setenv=HOME=/home/banquo --setenv=LANG=C.UTF-8 --setenv=LC_ALL=C.UTF-8 --setenv=MKL_NUM_THREADS=1 --setenv=NUMEXPR_NUM_THREADS=1 --setenv=OMP_NUM_THREADS=1 --setenv=OPENBLAS_NUM_THREADS=1 --setenv=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin --setenv=PYTHONHASHSEED=0 --setenv=PYTHONNOUSERSITE=1 '--setenv=PYTHONPATH=/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit/src' --setenv=RECON_RECOVERY_SERIES_ID=systemd-foreground-1107519c8a4448ed8e7bc134b8a68140 --setenv=RECON_RECOVERY_UNIT=hector-recon-v2-admission-e697c46cf43a4129a54d24341be70e29.service --setenv=TZ=UTC '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit/.venv/bin/python3' '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/systemd-foreground-1107519c8a4448ed8e7bc134b8a68140/foreground_series_coordinator.py' run-series --manifest '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/systemd-foreground-1107519c8a4448ed8e7bc134b8a68140/outer_manifest.json' --manifest-sha256 2f9895f3a9a7c7b6aae99615b5739a2eb4fdab8efc7244a814e20e9d68aa0b28
```

## Real series read-only status

```bash
'/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit/.venv/bin/python3' '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/systemd-foreground-1107519c8a4448ed8e7bc134b8a68140/foreground_series_coordinator.py' status --manifest '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/systemd-foreground-1107519c8a4448ed8e7bc134b8a68140/outer_manifest.json' --manifest-sha256 2f9895f3a9a7c7b6aae99615b5739a2eb4fdab8efc7244a814e20e9d68aa0b28
```

## Real series finalization

Run only after the service is terminal. It records final state but cannot start
or resume work.

```bash
'/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit/.venv/bin/python3' '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/systemd-foreground-1107519c8a4448ed8e7bc134b8a68140/foreground_series_coordinator.py' finalize --manifest '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/systemd-foreground-1107519c8a4448ed8e7bc134b8a68140/outer_manifest.json' --manifest-sha256 2f9895f3a9a7c7b6aae99615b5739a2eb4fdab8efc7244a814e20e9d68aa0b28
```
