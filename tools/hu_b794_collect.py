"""Authenticate the B792 Actions workers and their original native archives."""
import argparse
import json
from pathlib import Path

from hu_b467_river_source_gate import json_bytes,sha
from hu_b710_collect import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt

RUN=45351501007
HEAD='693a5d7cf92ba22c5f4e8da4f6ee29312c5779d3'
WORKFLOW='.github/workflows/nl2-hu-b792-rank136-turns.yml'
WORKER='tools/hu_b792_rank136_chance_turns.py'
JOBS={'Ac8h5d': 138298799539, 'Ad9c6h': 138298799141, 'Ah8d4s': 138298799781}
PINS={'Ac8h5d': [14900322317, '82dae00ffed0eb673730383819d91d28b5e16a8156d9a976c0b3c0ba58fdb21b'], 'Ad9c6h': [14900441815, '0f76b6693274890505b6f42fb5a2596b9fab21e082f2789071b1af6190dd7bed'], 'Ah8d4s': [14900951010, '63778af66077e76bbd6f9d90a98d49becf116c3d6a663363071d498f68f95d28']}
JOB_NAMES={'Ac8h5d': 'solve (Ac8h5d, 14864684107)', 'Ad9c6h': 'solve (Ad9c6h, 14863849825)', 'Ah8d4s': 'solve (Ah8d4s, 14866540680)'}
STEPS=['Authenticate the completed B652 original and validate ten held-out range pairs', 'Build the pinned native solver', 'Solve the unextracted conditional turns and verify exact two-seat decisions', 'Run actions/upload-artifact@v4']



def validate(raw):
    r=run_receipt(raw['run'],RUN,HEAD,WORKFLOW);out=dict(run=r,jobs=[],artifacts=[])
    assert len(raw['jobs'])==len(raw['artifacts'])==len(PINS)==3 and set(PINS)==set(JOBS)
    for flop,(aid,digest) in PINS.items():
        jid=JOBS[flop]
        j,=[j for j in raw['jobs'] if j['id']==jid];a,=[a for a in raw['artifacts'] if a['id']==aid]
        out['jobs'].append(job_receipt(j,r,jid,JOB_NAMES[flop],STEPS))
        out['artifacts'].append(artifact_receipt(a,r,aid,'B792-R136-'+flop,digest))
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

