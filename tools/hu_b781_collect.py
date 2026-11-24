"""Authenticate the B780 Actions workers and their original native archives."""
import argparse
import json
from pathlib import Path

from hu_b467_river_source_gate import json_bytes,sha
from hu_b710_collect import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt

RUN=45347370837
HEAD='23e07c1640b6cfcfc2d0b10f76130957f6ee273a'
WORKFLOW='.github/workflows/nl2-hu-b780-rank229-suited-turns.yml'
JOBS={'Kd9c5h':138285091670}
PINS={'Kd9c5h':[14898088914,'ac6df1b860419ff379293362d43081f30f392fce6723e182212c29e252db47d1']}
FILES={WORKFLOW:'9d0ea81a28bfddfd6dd72d403253fb052caae244','tools/hu_b780_rank229_suited_turns.py':'93f44e4cd2332304833bc0095abcc82f6744350d','tools/hu_b727_rank229.py':'601385f1ead29779ca5bf30f40237f13abba2c43','tools/hu_b676_checked_routes.cjs':'522ea33d7326c38a7493507cbde96b5df4a6f3f7'}
STEPS=['Authenticate the B681 root and three previously unextracted diamond turns','Build the pinned native solver','Reproduce all original nodes and test paired GTO and measured opponent policies','Run actions/upload-artifact@v4']


def validate(raw):
    r=run_receipt(raw['run'],RUN,HEAD,WORKFLOW);out=dict(run=r,jobs=[],artifacts=[])
    assert len(raw['jobs'])==len(raw['artifacts'])==len(PINS)==1 and set(PINS)==set(JOBS)
    for flop,(aid,digest) in PINS.items():
        jid=JOBS[flop]
        j,=[j for j in raw['jobs'] if j['id']==jid];a,=[a for a in raw['artifacts'] if a['id']==aid]
        out['jobs'].append(job_receipt(j,r,jid,'solve',STEPS))
        out['artifacts'].append(artifact_receipt(a,r,aid,'B780-R229-'+flop,digest))
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

