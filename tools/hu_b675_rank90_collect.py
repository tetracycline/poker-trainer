"""Pin only the original B666 and completed preregistered B673 workers."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

REPO='tetracycline/poker-trainer'
RUN=45305698310
HEAD='b046a4583d38ef56db8e271fd329ab5116c55c8a'
EXPECTED={'B673-rank90-Ad9c5h':'Ad9c5h'}
JOB=138148881091
ARTIFACT=14881830088
DIGEST='daf8c8ba5e235fb57f6776f09e0413458c221d0b9f09bf08566ddab3ad886317'


def api(path):
    for attempt in range(4):
        result=subprocess.run(['gh','api','repos/'+REPO+'/'+path],capture_output=True)
        if result.returncode==0:
            return result.stdout
        if attempt==3:
            raise RuntimeError(result.stderr.decode(errors='replace')[-800:])
        time.sleep(2*(attempt+1))


def main(args):
    output=args.output
    output.mkdir(parents=True,exist_ok=True)
    workers=json.loads(args.workers.read_bytes())
    # Existing entries are immutable pins. Do not duplicate already collected new workers.
    old=[p for p in workers if p['run']!=RUN]
    assert len(old)==2 and {p['id'] for p in old}=={14865128989,14866363652}
    run=json.loads(api('actions/runs/'+str(RUN)))
    assert run['head_sha']==HEAD
    job=json.loads(api('actions/jobs/'+str(JOB)))
    assert (job['id'],job['run_id'],job['head_sha'],job['name'],job['status'],job['conclusion'])==(
        JOB,RUN,HEAD,'solve (Ad9c5h)','completed','success'), 'The pinned original Ad9c5h worker has not succeeded'
    required={'Build the pinned native solver','Solve only the new source and both actor strategies','Run actions/upload-artifact@v4'}
    assert required<={s['name'] for s in job['steps'] if s['status']=='completed' and s['conclusion']=='success'}
    artifacts=json.loads(api('actions/runs/'+str(RUN)+'/artifacts?per_page=100'))['artifacts']
    found={a['name']:a for a in artifacts if a['name'] in EXPECTED}
    assert set(found)==set(EXPECTED) and sum(a['name'] in EXPECTED for a in artifacts)==1
    workers=list(old)
    for name,flop in EXPECTED.items():
        a=found[name]
        assert not a['expired'] and (a['id'],a['digest'])==(ARTIFACT,'sha256:'+DIGEST)
        assert (a['workflow_run']['id'],a['workflow_run']['head_sha'],a['workflow_run']['repository_id'])==(RUN,HEAD,1438346845)
        workers.append(dict(id=a['id'],name=name,flop=flop,run=RUN,head=HEAD,sha256=a['digest'][7:]))
    for p in workers:
        raw=api('actions/artifacts/'+str(p['id']))
        receipt=json.loads(raw)
        assert (receipt['id'],receipt['name'],receipt['digest'],receipt['workflow_run']['id'],
                receipt['workflow_run']['head_sha'],receipt['workflow_run']['repository_id'])==(
            p['id'],p['name'],'sha256:'+p['sha256'],p['run'],p['head'],1438346845)
        archive=api('actions/artifacts/'+str(p['id'])+'/zip')
        assert hashlib.sha256(archive).hexdigest()==p['sha256']
        (output/(str(p['id'])+'.json')).write_bytes(raw)
        (output/(str(p['id'])+'.zip')).write_bytes(archive)
    args.workers.write_text(json.dumps(workers,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(authenticated_workers=len(workers),original_runs=sorted({p['run'] for p in workers}))))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--workers',type=Path,default=Path('data/nl2_hu_b673_rank90_workers.json'))
    main(parser.parse_args())
