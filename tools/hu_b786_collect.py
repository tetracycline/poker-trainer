"""Authenticate the B783 rank229 workers and their independently saved original roots."""
import argparse
import json
from pathlib import Path

from hu_b467_river_source_gate import json_bytes,sha
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt
from hu_b710_collect import api

RUN=45348606768
HEAD='6e9ed6e5213f171d810f13f4edb382b6853d7fdf'
WORKFLOW='.github/workflows/nl2-hu-b783-rank229-king-nines.yml'
WORKER='tools/hu_b783_rank229_king_nines.py'
BLOBS={WORKFLOW:'27e58961163816c579384c556e71f8edb42301f2',WORKER:'0a34b979baecba50757619304f0a724c432b8c87'}
JOBS={'Ks9d2h':138289171681,'Kc9h7d':138289171517,'Kh9s8d':138289171269}
STEPS=['Verify the two prior same-deal sources, restricted root menu and exact UI','Build the pinned native solver',
       'Solve the new original flop and record all check-through boundaries','Save the original root before any conditional turn solve',
       'Verify the original two-seat gate and replay completed conditional policies','Preserve the rank229 GTO and measured NL2 decisions']
PINS={'B783-R229-Kc9h7d': [14899641313, '393c1dbf71faa9231813e4f5efec1d55d72ef0d04a69bdcc4d59fa1c6293be3f'], 'B783-root-R229-Ks9d2h': [14899457096, 'c293b6e180e06f213abcde44c41bd2141dbe8ec6167e1750501ba06921ada65b'], 'B783-root-R229-Kc9h7d': [14899416803, 'a9ba63165339114d33df49eced3bb852afbf3a322924a4da515ef7938021b39e'], 'B783-R229-Kh9s8d': [14898798461, '780b197f800f0e52e6248be01b137dcf82ff689700d30050f0a8fe26f4a170b3'], 'B783-R229-Ks9d2h': [14898674403, '21f89a1d3c55da1cf22f3a1f8e22d177f21b25159be3766b2ea0cc8cc534ba70'], 'B783-root-R229-Kh9s8d': [14898518805, 'b1875f6feb0e36d5c8bc8dfdff3073562ea95a945efdcbd01089824da266cfb7']}


def validate(raw):
    run=run_receipt(raw['run'],RUN,HEAD,WORKFLOW)
    assert run['run_attempt']==1 and len(raw['jobs'])==3 and len(raw['artifacts'])==6
    jobs=[];arts=[]
    for f,jid in JOBS.items():
        j,=(j for j in raw['jobs'] if j['id']==jid)
        jobs.append(job_receipt(j,run,jid,'solve ('+f+')',STEPS))
        for prefix in ('B783-root-R229-','B783-R229-'):
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
