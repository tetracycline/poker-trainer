"""Download and authenticate the completed B743 checkpoints and native decisions."""
import argparse
import json
from pathlib import Path

from hu_b467_river_source_gate import json_bytes, sha
from hu_b710_collect import api
from hu_b747_rank150_replay import RUN, PINS, authenticate


def fields(obj,keys):
    return {k:obj[k] for k in keys.split()}


def receipt(run,jobs,artifacts):
    core=fields(run,'id head_sha head_branch path status conclusion run_attempt')
    core['repository']=fields(run['repository'],'id full_name')
    job_rows=[];artifact_rows=[]
    for f,pin in PINS.items():
        j,=[j for j in jobs if j['id']==pin['job']]
        item=fields(j,'id run_id head_sha name status conclusion run_attempt')
        item['steps']=[fields(step,'name number status conclusion') for step in j['steps']]
        job_rows.append(item)
        for key in ('original','checkpoint'):
            a,=[a for a in artifacts if a['id']==pin[key][0]]
            item=fields(a,'id name digest size_in_bytes expired')
            item['workflow_run']=fields(a['workflow_run'],'id head_sha head_branch head_repository_id repository_id')
            artifact_rows.append(item)
    auth=dict(run=core,jobs=job_rows,artifacts=artifact_rows)
    authenticate(auth)
    return auth


def collect(directory):
    directory.mkdir(parents=True,exist_ok=True)
    assert not any(directory.iterdir())
    prefix='actions/runs/'+str(RUN)
    run=json.loads(api(prefix))
    jobs=json.loads(api(prefix+'/jobs?per_page=100'))
    artifacts=json.loads(api(prefix+'/artifacts?per_page=100'))
    assert jobs['total_count']==3 and artifacts['total_count']==6
    auth=receipt(run,jobs['jobs'],artifacts['artifacts'])
    (directory/'receipt.json').write_bytes(json_bytes(auth))
    for row in auth['artifacts']:
        ident=row['id']
        raw=api(f'actions/artifacts/{ident}/zip')
        assert len(raw)==row['size_in_bytes'] and 'sha256:'+sha(raw)==row['digest']
        (directory/f'{ident}.zip').write_bytes(raw)


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--output',type=Path,required=True)
    collect(cli.parse_args().output)
