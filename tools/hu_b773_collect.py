"""Authenticate the B771 Actions workers and their original native archives."""
import argparse
import json
from pathlib import Path

from hu_b467_river_source_gate import json_bytes,sha
from hu_b710_collect import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt

RUN=45341697139
HEAD='28a793f7df724892631de6f516fe78e4b07fb879'
WORKFLOW='.github/workflows/nl2-hu-b771-rank199-third-flop.yml'
JOBS={'7h6c4h':138266616373}
PINS={'7h6c4h':[14897186929,'85f3a52680e963c94538e568d13bfd27d48e6ba26726c7e5042e85ed70b1c7ba']}
FILES={WORKFLOW:'a0f94748bf443de583b8c3ec46ff92bf2630a9c6','tools/hu_b771_rank199_third_flop.py':'c6ec1d4a7e115ba351dedb8ea7a21b5af51bc1ad','tools/hu_b767_rank199_new_turns.py':'24abe7561da53016a4806a562bbf279e2bf17be6','tools/hu_b759_rank46_barrel_gates.py':'7871d309c6804b3259a1623589f65c43a4b36f47','tools/hu_b759_rank46_barrel_routes.cjs':'b294e53283fec0f349f1f2d33602f4e4f2230073','tools/hu_b764_rank199_partial.py':'91f6dd10c00491777ec5d9761bcbd85ddd7e253f','tools/hu_b769_rank199_partial.py':'b4520b3e60be841b1f7174acbeac028e373a5b39'}
STEPS=['Authenticate the original 15 flop nodes and four distinct turn routes','Build the pinned native solver','Verify four new boundaries and stop after the first shared native policy deal','Run actions/upload-artifact@v4']


def validate(raw):
    r=run_receipt(raw['run'],RUN,HEAD,WORKFLOW);out=dict(run=r,jobs=[],artifacts=[])
    assert len(raw['jobs'])==len(raw['artifacts'])==len(PINS)==1 and set(PINS)==set(JOBS)
    for flop,(aid,digest) in PINS.items():
        jid=JOBS[flop]
        j,=[j for j in raw['jobs'] if j['id']==jid];a,=[a for a in raw['artifacts'] if a['id']==aid]
        out['jobs'].append(job_receipt(j,r,jid,'solve',STEPS))
        out['artifacts'].append(artifact_receipt(a,r,aid,'B771-R199-'+flop,digest))
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

