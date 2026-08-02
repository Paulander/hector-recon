# Frozen schema-reclosure service commands

Run from the ordinary WSL terminal with the current directory set to:

`/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit`

Before launch, HEAD must be exact commit
`8479cbdd22ed06d09eea3bd051a2e0e8344063ec`; the only untracked canonical
files may be the four immutable carried slot-01 files. Slots 02 and 03 must be
absent. Never run the start command more than once.

## Start

```bash
systemd-run --user --unit=hector-recon-v2-schema-6a8e100e71b846b98715e72fb378c75e.service --service-type=exec --property=Restart=no --property=RuntimeMaxSec=infinity '--working-directory=/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit' '--property=StandardOutput=append:/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/schema-reclosure-00079210ade5457dab063a8ce990a4a2/series_service.stdout' '--property=StandardError=append:/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/schema-reclosure-00079210ade5457dab063a8ce990a4a2/series_service.stderr' --no-block --setenv=HOME=/home/banquo --setenv=LANG=C.UTF-8 --setenv=LC_ALL=C.UTF-8 --setenv=MKL_NUM_THREADS=1 --setenv=NUMEXPR_NUM_THREADS=1 --setenv=OMP_NUM_THREADS=1 --setenv=OPENBLAS_NUM_THREADS=1 --setenv=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin --setenv=PYTHONHASHSEED=0 --setenv=PYTHONNOUSERSITE=1 '--setenv=PYTHONPATH=/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit/src' --setenv=RECON_RECOVERY_SERIES_ID=schema-reclosure-00079210ade5457dab063a8ce990a4a2 --setenv=RECON_RECOVERY_UNIT=hector-recon-v2-schema-6a8e100e71b846b98715e72fb378c75e.service --setenv=TZ=UTC '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit/.venv/bin/python3' '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/schema-reclosure-00079210ade5457dab063a8ce990a4a2/foreground_schema_reclosure_coordinator.py' run-series --manifest '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/schema-reclosure-00079210ade5457dab063a8ce990a4a2/outer_manifest.json' --manifest-sha256 643443467633a67943546c5d89a68f3948a6781324467ca0225ba87857ab4aea
```

## Read-only status

```bash
'/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit/.venv/bin/python3' '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/schema-reclosure-00079210ade5457dab063a8ce990a4a2/foreground_schema_reclosure_coordinator.py' status --manifest '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/schema-reclosure-00079210ade5457dab063a8ce990a4a2/outer_manifest.json' --manifest-sha256 643443467633a67943546c5d89a68f3948a6781324467ca0225ba87857ab4aea
```

## Finalize after terminal state

```bash
'/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-audit/.venv/bin/python3' '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/schema-reclosure-00079210ade5457dab063a8ce990a4a2/foreground_schema_reclosure_coordinator.py' finalize --manifest '/mnt/c/Users/oskar/Documents/Webpages playground/hector-recon-v2-systemd-series/schema-reclosure-00079210ade5457dab063a8ce990a4a2/outer_manifest.json' --manifest-sha256 643443467633a67943546c5d89a68f3948a6781324467ca0225ba87857ab4aea
```
