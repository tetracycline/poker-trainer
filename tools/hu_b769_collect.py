"""Authenticate all three B767 Actions workers and their original native archives."""
import argparse
import json
from pathlib import Path

from hu_b467_river_source_gate import json_bytes,sha
from hu_b710_collect import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt

RUN=45340862830
HEAD='6a91dc4efd5434d1e05abce4021e9ccc3e541348'
WORKFLOW='.github/workflows/nl2-hu-b767-rank199-new-turns.yml'
JOBS={'7s5h3d-Qd':138263931400,'7h6h4c-Qc':138263931699,'7s5h3d-9c':138263931740}
PINS={'7h6h4c-Qc': [14895319115, 'adfaa92abee93177ef4d0edf65e1655fda9004481b257eafb7ee7345723391e7'],
 '7s5h3d-9c': [14896101177, '49aea6de00249d7a58cd03a47124b6dca272f8a51e36f1eeb8b95f101396fc83'],
 '7s5h3d-Qd': [14895584238, 'c03469274967a37422be72cbeee7d80cec983dc079e7df1c35f8aa1679513e25']}
FILES={WORKFLOW:'89cafa3f5e59124cdfea149b3286bda094ff5013','tools/hu_b767_rank199_new_turns.py':'24abe7561da53016a4806a562bbf279e2bf17be6','tools/hu_b759_rank46_barrel_gates.py':'7871d309c6804b3259a1623589f65c43a4b36f47','tools/hu_b759_rank46_barrel_routes.cjs':'b294e53283fec0f349f1f2d33602f4e4f2230073'}
STEPS=['Authenticate the frozen flop, both original boundary ranges and eligible private deals','Build the pinned native solver','Solve the new turn and its eligible rivers with the measured lock after positive GTO reach','Run actions/upload-artifact@v4']


def validate(raw):
    r=run_receipt(raw['run'],RUN,HEAD,WORKFLOW);out=dict(run=r,jobs=[],artifacts=[])
    assert len(raw['jobs'])==len(raw['artifacts'])==len(PINS)==3 and set(PINS)==set(JOBS)
    for flop,(aid,digest) in PINS.items():
        jid=JOBS[flop]
        j,=[j for j in raw['jobs'] if j['id']==jid];a,=[a for a in raw['artifacts'] if a['id']==aid]
        out['jobs'].append(job_receipt(j,r,jid,'solve ('+flop.replace('-',', ')+')',STEPS))
        out['artifacts'].append(artifact_receipt(a,r,aid,'B767-R199-'+flop,digest))
    return out


def collect(out):
    out.mkdir(parents=True,exist_ok=True)
    r=dict(run=json.loads(api('actions/runs/'+str(RUN))),
        jobs=[json.loads(api('actions/jobs/'+str(i))) for i in JOBS.values()],
        artifacts=[json.loads(api('actions/artifacts/'+str(i))) for i,digest in PINS.values()])
    (out/'receipt.json').write_bytes(json_bytes(validate(r)))
    for ident,digest in PINS.values():
        raw=api('actions/artifacts/'+str(ident)+'/zip');assert sha(raw)==digest
        (out/(str(ident)+'.zip')).write_bytes(raw)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    collect(p.parse_args().output)

