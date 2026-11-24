"""Authenticate all three B755 Actions workers and their original native archives."""
import argparse
import json
from pathlib import Path

from hu_b467_river_source_gate import json_bytes,sha
from hu_b710_collect import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt

RUN=45337049683
HEAD='26f8c0095103994c3078d778d141ca420f216907'
WORKFLOW='.github/workflows/nl2-hu-b755-rank151-rivers.yml'
JOBS={'7h6h4c':138251502448,'7h6d4s':138251502730,'7s5h3d':138251502776}
PINS={'7h6d4s': [14894721279, '14b1019f010a403db8fdfa4942128f17e17d36b771118cac34670e4d97dd7589'],
 '7h6h4c': [14894716547, 'c5ff73ce0cd8dcda8fce5ba5f301dd21954ac82896f635735aeccbc000eb760b'],
 '7s5h3d': [14894831955, '721db42b6e5d6bf62527d02cb2d84eadb9923bae8fd2d99dc301c4906f5f88f6']}
FILES={WORKFLOW:'2ace0c677d29d42853a83411b5302d083d681b30','tools/hu_b755_rank151.py':'4c34c46920de4cf70dfce48deff3ae413c00b718','tools/hu_b753_rank151_routes.cjs':'41b0e729d9d854285ebdaf0454346ef80add450f','tools/hu_b723_rank115_limp_rivers.py':'2d7b33a5386abcbed329e68a4a681054ad646693'}
STEPS=['Verify three-street CO check witnesses against the original BB and CO flop ranges','Build the pinned native solver','Compare all original flop nodes and solve eligible checked-through rivers','Run actions/upload-artifact@v4']


def validate(raw):
    r=run_receipt(raw['run'],RUN,HEAD,WORKFLOW);out=dict(run=r,jobs=[],artifacts=[])
    assert len(raw['jobs'])==len(raw['artifacts'])==len(PINS)==3 and set(PINS)==set(JOBS)
    for flop,(aid,digest) in PINS.items():
        jid=JOBS[flop]
        j,=[j for j in raw['jobs'] if j['id']==jid];a,=[a for a in raw['artifacts'] if a['id']==aid]
        out['jobs'].append(job_receipt(j,r,jid,'solve ('+flop+')',STEPS))
        out['artifacts'].append(artifact_receipt(a,r,aid,'B755-R151-'+flop,digest))
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

