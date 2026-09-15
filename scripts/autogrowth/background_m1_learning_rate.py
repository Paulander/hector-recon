"""One background-session experiment. No retry or automatic extension."""
from pathlib import Path
import json
import os
import resource
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
JOB=ROOT/'reports/autogrowth/runs/m1-learning-rate-job-20260909'
RUN=ROOT/'reports/autogrowth/runs/m1-learning-rate-seeds479-20260909'
PRIVATE=ROOT/'snapshots/autogrowth/m1-learning-rate-seeds479-20260909'
WALL=6600
RSS_LIMIT=6*1024**3
ADDRESS_LIMIT=2560*1024**2


def write(value):
    p=JOB/'status.json';t=p.with_suffix('.tmp')
    with t.open('w') as f:
        json.dump(value,f,indent=2);f.flush();os.fsync(f.fileno())
    t.replace(p)


def group_rss(pgid):
    total=0;members=0
    for p in Path('/proc').glob('[0-9]*/stat'):
        try:
            text=p.read_text();fields=text[text.rindex(')')+2:].split()
            if int(fields[2])==pgid:
                total+=int(fields[21])*os.sysconf('SC_PAGE_SIZE');members+=1
        except (OSError,ValueError,IndexError):pass
    return total,members


def proc_identity():
    # /proc is host-mounted while exec runs in a PID namespace. Never compare
    # namespace PIDs with host /proc process-group IDs for memory accounting.
    text=Path('/proc/self/stat').read_text()
    fields=text[text.rindex(')')+2:].split()
    return {'host_pid':int(text.split(' ',1)[0]),'host_pgid':int(fields[2]),
            'namespace_pid':os.getpid(),'namespace_pgid':os.getpgrp()}


def main():
    JOB.mkdir(parents=True,exist_ok=False)
    start=time.time();cpus=sorted(os.sched_getaffinity(0))[:3]
    if len(cpus)!=3:raise RuntimeError('three available CPUs required for declared budget')
    env=os.environ.copy()
    env.update(PYTHONHASHSEED='0',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    command=[sys.executable,'scripts/autogrowth/run_m1_learning_rate.py',
        '--pool','reports/autogrowth/runs/m1-coach-smoke-pool',
        '--reference','reports/autogrowth/development/M1_LONG_PLAY_20260907.json',
        '--private-source','snapshots/autogrowth/m1-long-play-seeds4-9',
        '--output',str(RUN),'--private',str(PRIVATE),'--seeds','4','7','9',
        '--episodes','6144','--evaluate-at','4608','5120','5632','6144',
        '--block','128','--workers','3','--wall-seconds','3000']
    def limits():
        os.sched_setaffinity(0,cpus)
        resource.setrlimit(resource.RLIMIT_AS,(ADDRESS_LIMIT,ADDRESS_LIMIT))
    def runner_limits():
        limits()
        (JOB/'runner-identity.json').write_text(json.dumps(proc_identity()))
    status={'status':'starting','supervisor_identity':proc_identity(),'started_utc_epoch':start,
        'hard_deadline_utc_epoch':start+WALL,'cpu_affinity':cpus,
        'max_workers':3,'aggregate_rss_limit_bytes':RSS_LIMIT,
        'per_process_address_limit_bytes':ADDRESS_LIMIT,'wall_seconds_per_arm':3000,
        'command':command,'retry_allowed':False,'run_directory':str(RUN),'private_directory':str(PRIVATE)}
    write(status)
    process=None;failure=None;peak=0
    try:
        with (JOB/'experiment.log').open('x') as log:
            process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,
                start_new_session=True,preexec_fn=runner_limits)
            identity=json.loads((JOB/'runner-identity.json').read_text())
            status.update(status='running',runner_identity=identity)
            while process.poll() is None:
                rss,members=group_rss(identity['host_pgid']);peak=max(peak,rss)
                status.update(rss_bytes=rss,peak_rss_bytes=peak,processes=members,checked_utc_epoch=time.time())
                write(status)
                if time.time()-start>=WALL:failure='whole-job wall limit'
                elif rss>RSS_LIMIT:failure='aggregate memory limit'
                elif list(RUN.glob('seed-*/learning_rate-*/arm-failure.json')):failure='an arm failed'
                elif (JOB/'STOP').exists():failure='requested stop'
                if failure:
                    os.killpg(process.pid,signal.SIGTERM)
                    try:process.wait(timeout=5)
                    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
                    break
                time.sleep(2)
        if process.returncode!=0 or failure:
            raise RuntimeError(failure or f'runner exit {process.returncode}')
        status.update(status='analyzing',peak_rss_bytes=peak);write(status)
        remaining=max(1,int(start+WALL-time.time()))
        subprocess.run([sys.executable,'scripts/autogrowth/summarize_m1_learning_rate.py'],
            cwd=ROOT,env=env,check=True,timeout=min(300,remaining),preexec_fn=limits)
        status.update(status='complete',completed_utc_epoch=time.time(),peak_rss_bytes=peak,
            report=str(ROOT/'reports/autogrowth/development/M1_LEARNING_RATE_20260909.json'))
        write(status)
    except BaseException as error:
        if process is not None and process.poll() is None:
            os.killpg(process.pid,signal.SIGKILL);process.wait()
        status.update(status='incomplete',error=str(error),completed_utc_epoch=time.time(),peak_rss_bytes=peak)
        write(status)
        raise

if __name__=='__main__':main()
