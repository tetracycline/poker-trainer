"""Authenticate all two B762 Actions workers and their original native archives."""
import argparse
import json
from pathlib import Path

from hu_b467_river_source_gate import json_bytes,sha
from hu_b710_collect import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt

RUN=45339909699
HEAD='e0b54459680cfe416fab7084849a591abeb23e70'
WORKFLOW='.github/workflows/nl2-hu-b762-rank199-rivers.yml'
JOBS={'2c':138260802757,'8d':138260803092}
PINS={'2c': [14894633872, '7afae1b51a0966d5727ed0f0a73504189cf77c2d4948b35fd8f52dcc9cf40048'],
 '8d': [14896015184, '9301daed1cf45b43cc36eb5893401b77b8985915ca90c9a63ac21a853f8d3c8e']}
FILES={WORKFLOW:'7217814a15c23c5f22a59b02902200a6718671d6','tools/hu_b762_rank199_rivers.py':'4549eb3e296258f6ee696e422fda1bf8454da1c4','tools/hu_b759_rank46_barrel_gates.py':'7871d309c6804b3259a1623589f65c43a4b36f47','tools/hu_b759_rank46_barrel_routes.cjs':'b294e53283fec0f349f1f2d33602f4e4f2230073'}
STEPS=['Authenticate both B755 turn policies and the shared CO and BB hands','Build the pinned native solver','Extract ten missing river decisions across the two turns and verify all original nodes','Run actions/upload-artifact@v4']


def validate(raw):
    r=run_receipt(raw['run'],RUN,HEAD,WORKFLOW);out=dict(run=r,jobs=[],artifacts=[])
    assert len(raw['jobs'])==len(raw['artifacts'])==len(PINS)==2 and set(PINS)==set(JOBS)
    for flop,(aid,digest) in PINS.items():
        jid=JOBS[flop]
        j,=[j for j in raw['jobs'] if j['id']==jid];a,=[a for a in raw['artifacts'] if a['id']==aid]
        out['jobs'].append(job_receipt(j,r,jid,'solve ('+flop+')',STEPS))
        out['artifacts'].append(artifact_receipt(a,r,aid,'B762-R199-7h6d4s-'+flop,digest))
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

