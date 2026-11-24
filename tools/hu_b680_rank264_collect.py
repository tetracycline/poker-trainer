"""Download only successful workers from the fixed B677 source run."""
import argparse
import json
from pathlib import Path
import subprocess
import time

from hu_b467_river_source_gate import json_bytes,sha

REPO='tetracycline/poker-trainer'
FLOPS=('Jh7c3d','Ts6h2d','9d5c3h')


def api(path):
    for attempt in range(4):
        r=subprocess.run(['gh','api','repos/'+REPO+'/'+path],capture_output=True)
        if r.returncode==0:return r.stdout
        if attempt==3:raise RuntimeError(r.stderr.decode(errors='replace')[-800:])
        time.sleep(2*(attempt+1))


def main(a):
    run=json.loads(api('actions/runs/'+str(a.run)))
    assert run['head_sha']==a.head and run['repository']['id']==1438346845
    jobs=json.loads(api('actions/runs/'+str(a.run)+'/jobs?filter=latest&per_page=100'))['jobs']
    artifacts=json.loads(api('actions/runs/'+str(a.run)+'/artifacts?per_page=100'))['artifacts']
    a.output.mkdir(parents=True,exist_ok=True)
    records=[]
    for flop in FLOPS:
        job,=[j for j in jobs if j['name']=='solve ('+flop+')']
        assert (job['run_id'],job['head_sha'],job['status'],job['conclusion'])==(a.run,a.head,'completed','success')
        required={'Build the pinned native driver','Solve and independently replay the actual two-seat displayed route','Run actions/upload-artifact@v4'}
        assert required<={s['name']for s in job['steps']if s['status']=='completed' and s['conclusion']=='success'}
        artifact,=[r for r in artifacts if r['name']=='B677-R264-'+flop]
        assert not artifact['expired']
        assert (artifact['workflow_run']['id'],artifact['workflow_run']['head_sha'],artifact['workflow_run']['repository_id'])==(a.run,a.head,1438346845)
        assert artifact['digest'].startswith('sha256:') and len(artifact['digest'])==71
        receipt=json.loads(api('actions/artifacts/'+str(artifact['id'])))
        assert all(receipt[k]==artifact[k]for k in ('id','name','digest','workflow_run'))
        raw=api('actions/artifacts/'+str(artifact['id'])+'/zip')
        assert 'sha256:'+sha(raw)==artifact['digest']
        (a.output/f'{artifact["id"]}.zip').write_bytes(raw)
        (a.output/f'{artifact["id"]}.json').write_bytes(json_bytes(receipt))
        (a.output/f'job-{job["id"]}.json').write_bytes(json_bytes(job))
        records.append(dict(id=artifact['id'],name=artifact['name'],flop=flop,run=a.run,head=a.head,
            sha256=sha(raw),job_id=job['id'],job_name=job['name']))
    (a.output/'workers.json').write_bytes(json_bytes(records))
    print(json.dumps(dict(successful_source_jobs=len(records),source_run=a.run,source_head=a.head)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=int,required=True)
    p.add_argument('--head',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert a.run>0 and len(a.head)==40
    main(a)
