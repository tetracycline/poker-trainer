"""Authenticate each completed B758 worker and its separately preserved source root."""
import argparse
import json
from pathlib import Path
import re

from hu_b467_river_source_gate import json_bytes,sha
from hu_b710_collect import api
from hu_b738_collect import BRANCH,fields,artifact_receipt

RUN=45339357100
HEAD='0ff53f5eb30679e1150dd96fe3c2e7648d84f377'
WORKER='tools/hu_b758_rank75_monotone.py'
WORKFLOW='.github/workflows/nl2-hu-b758-rank75-monotone.yml'
WORKER_BLOB='44528fa0da5661425f7b259281eba4062c034747'
WORKFLOW_BLOB='ba30e44ef24af11dc9e8132170d2fb943957da42'
JOBS={'9h7h5h':138258993993,'9d8d6d':138258993861,'8c7c5c':138258993487}
STEPS=['Verify original CO donk and BTN call witnesses, monotone UI and both preflop ranges','Build the pinned native solver',
    'Extract the missing original boundaries or solve a new monotone full-size root','Preserve the completed original before conditional work',
    'Read the saved original and verify both policies at reachable turn decisions','Preserve the conditional jobs and original decisions']


def successes(job):
    return {s['name'] for s in job['steps'] if (s['status'],s['conclusion'])==('completed','success')}


def validate(raw):
    r=raw['run'];run=fields(r,'id head_sha head_branch path status conclusion run_attempt')
    run['repository']=fields(r['repository'],'id full_name')
    assert run['repository']==dict(id=1438346845,full_name='tetracycline/poker-trainer')
    assert (run['id'],run['head_sha'],run['head_branch'],run['path'],run['status'],run['run_attempt'])==(RUN,HEAD,BRANCH,WORKFLOW,'completed',1)
    assert run['conclusion'] in ('success','failure','timed_out','cancelled')
    assert len(raw['jobs'])==3
    jobs=[];arts=[];seen=set()
    for f,jid in JOBS.items():
        j,=[j for j in raw['jobs'] if j['id']==jid]
        v=fields(j,'id run_id head_sha run_attempt name status conclusion')
        v['steps']=[fields(x,'number name status conclusion') for x in j['steps']]
        assert (v['run_id'],v['head_sha'],v['run_attempt'],v['name'],v['status'])==(RUN,HEAD,1,f'solve ({f})','completed')
        assert v['conclusion'] in ('success','failure','timed_out','cancelled')
        passed=successes(v)
        if v['conclusion']=='success':assert set(STEPS)<=passed
        jobs.append(v)
        for prefix,step in [('B758-root-R75-',STEPS[3]),('B758-R75-',STEPS[5])]:
            name=prefix+f
            matches=[a for a in raw['artifacts'] if a['name']==name]
            if step in passed:assert len(matches)==1
            if not matches:continue
            a,=matches
            assert a['id'] not in seen and re.fullmatch(r'sha256:[0-9a-f]{64}',a['digest']) and a['size_in_bytes']>0
            seen.add(a['id']);arts.append(artifact_receipt(a,run,a['id'],name,a['digest'][7:]))
    assert len(arts)==len(raw['artifacts']) and (run['conclusion']=='success')==all(j['conclusion']=='success' for j in jobs)
    return dict(run=run,jobs=jobs,artifacts=arts)


def collect(out):
    out.mkdir(parents=True,exist_ok=True);endpoint=f'actions/runs/{RUN}'
    j=json.loads(api(endpoint+'/jobs?per_page=100'));a=json.loads(api(endpoint+'/artifacts?per_page=100'))
    assert j['total_count']==len(j['jobs']) and a['total_count']==len(a['artifacts'])
    auth=validate(dict(run=json.loads(api(endpoint)),jobs=j['jobs'],artifacts=a['artifacts']))
    (out/'receipt.json').write_bytes(json_bytes(auth))
    for row in auth['artifacts']:
        path=out/(str(row['id'])+'.zip')
        data=path.read_bytes() if path.is_file() else api(f"actions/artifacts/{row['id']}/zip")
        assert sha(data)==row['digest'][7:] and len(data)==row['size_in_bytes']
        path.write_bytes(data)


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--output',type=Path,required=True);collect(cli.parse_args().output)
