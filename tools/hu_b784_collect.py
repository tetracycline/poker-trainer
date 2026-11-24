"""Authenticate B782's three checked-branch source jobs and their original native solutions."""
import argparse
import json
from pathlib import Path
import re

from hu_b467_river_source_gate import json_bytes,sha
from hu_b710_collect import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt

RUN=45348113146
HEAD='45ed3315f6998b86400899914ce63fa1cab8d647'
JOBS={'Th9h7c':138287535579,'Ts8s7h':138287535510,'Ts9s6h':138287535166}
WORKFLOW='.github/workflows/nl2-hu-b782-rank230-mid-pairs.yml'
WORKER='tools/hu_b782_rank230_mid_pairs.py'
PINS={WORKER:'d93bef8fa8aca87dbf1838808128653a3ba24c79',WORKFLOW:'bb6cbf43d342d2a2675f3960afbe3abb99d14814'}
STEPS=['Verify the genuine SB3_BTN thirty-three-percent root and both checked seats','Build the pinned native driver',
       'Re-export the checked ranges, match every original node and verify the new native turns','Preserve the matched root and genuine conditional jobs']
SOURCES={'B782-R230-'+flop:'B782_R230_'+flop.upper() for flop in JOBS}


def validate(raw):
    run=run_receipt(raw['run'],RUN,HEAD,WORKFLOW)
    assert len(raw['jobs'])==len(raw['artifacts'])==3
    result=dict(run=run,jobs=[],artifacts=[])
    for flop,jid in JOBS.items():
        j,=[j for j in raw['jobs'] if j['id']==jid]
        result['jobs'].append(job_receipt(j,run,jid,'solve ('+flop+')',STEPS))
        name='B782-R230-'+flop
        a,=[a for a in raw['artifacts'] if a['name']==name]
        assert a['size_in_bytes']>0 and re.fullmatch('sha256:[a-f0-9]{64}',a['digest'])
        result['artifacts'].append(artifact_receipt(a,run,a['id'],name,a['digest'][7:]))
    assert len({a['id'] for a in result['artifacts']})==3
    return result


def collect(out):
    out.mkdir(parents=True,exist_ok=True);endpoint=f'actions/runs/{RUN}'
    jobs=json.loads(api(endpoint+'/jobs?per_page=100'));artifacts=json.loads(api(endpoint+'/artifacts?per_page=100'))
    assert (jobs['total_count'],artifacts['total_count'])==(3,3)
    receipt=validate(dict(run=json.loads(api(endpoint)),jobs=jobs['jobs'],artifacts=artifacts['artifacts']))
    (out/'receipt.json').write_bytes(json_bytes(receipt))
    for a in receipt['artifacts']:
        target=out/f"{a['id']}.zip"
        data=target.read_bytes() if target.exists() else api(f"actions/artifacts/{a['id']}/zip")
        assert len(data)==a['size_in_bytes'] and sha(data)==a['digest'][7:]
        target.write_bytes(data)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    collect(p.parse_args().output)
