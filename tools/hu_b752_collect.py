"""Authenticate the B751 rank224 Actions workers and original ZIP bytes."""
import argparse
import json
from pathlib import Path

from hu_b467_river_source_gate import json_bytes, sha
from hu_b710_collect import api
from hu_b738_collect import artifact_receipt, job_receipt, run_receipt

RUN=45335270712
HEAD='9186be07c135907548de06433d213cdf5e5f4ee4'
JOBS={"3s3h2d":138245762696,"4s4h2d":138245763072,"5c5d2h":138245763087}
PINS={"4s4h2d":[14892958334,"b2c90801bfb4bcc2615635661662c5210c138555e2720870e90e6c0787b6db4e"],"5c5d2h":[14892948362,"1c8e0b7fe1555f766fc88c3a8e5693e40057c54d689cf7717b5018539aee657b"],"3s3h2d":[14892903664,"d04b6ce68c7a58eb6a26b4ddab19aa269b6b3a29ef2006d90a8d9ec49e97d29e"]}
WORKFLOW='.github/workflows/nl2-hu-b751-rank224-rivers.yml'
FILES={WORKFLOW:'001e7d29ca18ff5ac33824459b4cafc9bafe9321','tools/hu_b751_rank224_rivers.py':'1557871aa43332ef0ab94afae517c610e3b5190f',
       'tools/hu_b751_parent_gate.py':'2a49f27f71aa4ed6dccbabee44b19434a7448ec8','tools/hu_b751_river_routes.cjs':'3da38f55c14c1547c4787926fdfd2f453008685d'}
STEPS=['Verify BB half-pot bet, CO call and river links, original range, both original policies and exact source jobs','Build the pinned native solver',
       'Extend the original turn extractions and verify all 18 old nodes per policy','Run actions/upload-artifact@v4']


def validate(raw):
    run=run_receipt(raw['run'],RUN,HEAD,WORKFLOW)
    assert len(raw['jobs'])==len(raw['artifacts'])==len(PINS)==3 and set(PINS)==set(JOBS)
    receipt=dict(run=run,jobs=[],artifacts=[])
    for flop,jid in JOBS.items():
        aid,digest=PINS[flop]
        job,=[v for v in raw['jobs'] if v['id']==jid];artifact,=[v for v in raw['artifacts'] if v['id']==aid]
        receipt['jobs'].append(job_receipt(job,run,jid,f'solve ({flop})',STEPS))
        receipt['artifacts'].append(artifact_receipt(artifact,run,aid,'B751-R224-'+flop,digest))
    return receipt


def collect(out):
    out.mkdir(exist_ok=True,parents=True)
    raw=dict(run=json.loads(api('actions/runs/'+str(RUN))),jobs=[json.loads(api('actions/jobs/'+str(jid))) for jid in JOBS.values()],
        artifacts=[json.loads(api('actions/artifacts/'+str(aid))) for aid,digest in PINS.values()])
    (out/'receipt.json').write_bytes(json_bytes(validate(raw)))
    for aid,digest in PINS.values():
        original=api('actions/artifacts/'+str(aid)+'/zip')
        assert sha(original)==digest
        (out/f'{aid}.zip').write_bytes(original)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    collect(p.parse_args().output)
