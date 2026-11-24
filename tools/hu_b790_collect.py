"""Authenticate the B788 rank229 workers and their independently saved original roots."""
import argparse
import json
from pathlib import Path

from hu_b467_river_source_gate import json_bytes,sha
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt
from hu_b710_collect import api

RUN=45350106474
HEAD='d95c5bc9650de53edf4b169df23a490989f703bd'
WORKFLOW='.github/workflows/nl2-hu-b788-rank229-two-suited.yml'
WORKER='tools/hu_b788_rank229_two_suited.py'
BLOBS={WORKFLOW:'30cc6260873559273a078f62d81be6475381c6ac',WORKER:'04f771903296cf84ce74813bb3380a9d21a45d73'}
JOBS={'Kd9h4h':138294133201,'Kd9h5h':138294132751,'Kd9d5h':138294133070}
STEPS=['Verify the two prior same-deal sources, restricted root menu and exact UI','Build the pinned native solver',
       'Solve the new original flop and record all check-through boundaries','Save the original two-suited root and selection before conditional work',
       'Verify the original two-seat gate and replay completed conditional policies','Preserve the rank229 GTO and measured NL2 decisions']
PINS={'B788-root-R229-Kd9h4h': [14900146337, '94d9004d2d385a8e6e3564e132f35da6925a463e24d6694587b8656619f53e2c'], 'B788-R229-Kd9d5h': [14900141456, 'e1462a92f55847e1f1298fd21342b9cd17aa9b8a1c00f1efcf2f0c694240801d'], 'B788-R229-Kd9h5h': [14899917125, '14c53d57061609d49f11ad1c49c4d52a7beb14bb2f82e1fd7b5da094d32ace36'], 'B788-R229-Kd9h4h': [14899917076, '99eca797862da35c8d6db4258336b7a424edcdc372d4a4faf5960e49a72eabb4'], 'B788-root-R229-Kd9d5h': [14899474253, '4ffa83c47293a4bc6e2246905d8f9be7a13bb8779704fe3ebb3dfa442db86550'], 'B788-root-R229-Kd9h5h': [14899384465, 'df44983852d82f38857642f69b617acc249f1b1d14e863e7a775324dc07b39bd']}


def validate(raw):
    run=run_receipt(raw['run'],RUN,HEAD,WORKFLOW)
    assert run['run_attempt']==1 and len(raw['jobs'])==3 and len(raw['artifacts'])==6
    jobs=[];arts=[]
    for f,jid in JOBS.items():
        j,=(j for j in raw['jobs'] if j['id']==jid)
        jobs.append(job_receipt(j,run,jid,'solve ('+f+')',STEPS))
        for prefix in ('B788-root-R229-','B788-R229-'):
            name=prefix+f
            a,=(a for a in raw['artifacts'] if a['name']==name)
            aid,digest=PINS[name]
            arts.append(artifact_receipt(a,run,aid,name,digest))
    return dict(run=run,jobs=jobs,artifacts=arts)


def collect(out):
    out.mkdir(exist_ok=True,parents=True);path='actions/runs/'+str(RUN)
    jobs=json.loads(api(path+'/jobs?per_page=100'));arts=json.loads(api(path+'/artifacts?per_page=100'))
    assert jobs['total_count']==3 and arts['total_count']==6
    receipt=validate(dict(run=json.loads(api(path)),jobs=jobs['jobs'],artifacts=arts['artifacts']))
    (out/'receipt.json').write_bytes(json_bytes(receipt))
    for row in receipt['artifacts']:
        p=out/(str(row['id'])+'.zip')
        raw=p.read_bytes() if p.exists() else api('actions/artifacts/'+str(row['id'])+'/zip')
        assert sha(raw)==row['digest'][7:] and len(raw)==row['size_in_bytes']
        p.write_bytes(raw)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);collect(p.parse_args().output)
