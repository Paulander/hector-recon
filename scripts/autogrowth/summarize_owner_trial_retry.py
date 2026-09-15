"""Read-only trial summary with explicit recovered-work and timing scope."""
import argparse
import json
from pathlib import Path
from summarize_owner_trial_learning import summarize
from run_owner_nomination import write_once, encoded


def report(path):
    root=Path(path);raw=json.loads((root/'result.json').read_text())
    value=summarize(root)
    value['recovery']=raw['recovery']
    value['elapsed_seconds_scope']=raw['elapsed_seconds_scope']
    value['max_rss_scope']='Maximum observed start/training/frozen-verification unit RSS; excludes initialization/final report assembly.'
    return value


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run');p.add_argument('--output',required=True)
    args=p.parse_args();write_once(Path(args.output),encoded(report(args.run)))
