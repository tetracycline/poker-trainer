"""Authenticate all three B749 Actions workers and their original native archives."""
import argparse
import json
from pathlib import Path

from hu_b467_river_source_gate import json_bytes,sha
from hu_b710_collect import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt

RUN=45334735286
HEAD='b95813f3ff884f3550366aa8aa6203cafd268147'
WORKFLOW='.github/workflows/nl2-hu-b749-rank109-turns.yml'
JOBS={'Jh8h3d':138244033129,'9c7c4d':138244033257,'8h6h2d':138244033397}
PINS={"9c7c4d":[14894130266,"61d5818a827580a335fb1c5b738e92cbe5f5da8553d28741735a16ab38dff48f"],"8h6h2d":[14893107062,"714855b288725b8a425a54fcb90175916fcfb72baf2f7f9acf8b80427b7cb673"],"Jh8h3d":[14892982552,"2a2a872ed105ff5089329924e7639f7c012c69732b2d66407d85941df2824f5a"]}
FILES={WORKFLOW:'a483b4c0884446b83c3b8bb8f0fa55de1600b782','tools/hu_b749_rank109.py':'941c031e7c431b63eccb48feb5e27e5ee8c01ab7','tools/hu_b619_utg_routes.cjs':'146d958d6d981cd101ab6aae556e462a8b800d74'}
STEPS=['Check preserved UTG flop ranges and three-suited turn routes','Compile the pinned native solver',
       'Solve both missing turn barrels on the original flop and replay both policies','Run actions/upload-artifact@v4']


def validate(raw):
    r=run_receipt(raw['run'],RUN,HEAD,WORKFLOW);out=dict(run=r,jobs=[],artifacts=[])
    assert len(raw['jobs'])==len(raw['artifacts'])==len(PINS)==3 and set(PINS)==set(JOBS)
    for flop,(aid,digest) in PINS.items():
        jid=JOBS[flop]
        j,=[j for j in raw['jobs'] if j['id']==jid];a,=[a for a in raw['artifacts'] if a['id']==aid]
        out['jobs'].append(job_receipt(j,r,jid,'solve ('+flop+')',STEPS))
        out['artifacts'].append(artifact_receipt(a,r,aid,'B749-R109-'+flop,digest))
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

