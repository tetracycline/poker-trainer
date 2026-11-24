"""Check the earlier six B3 flop policies against rank150's actual third-pot draw route."""
import argparse
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile

import hu_b724_rank150_rivers as native
from hu_b467_river_source_gate import json_bytes,sha

PINS=[
  {
    "flop": "KsQh4d",
    "version": "exp_ip",
    "artifact": 14602013161,
    "job": 136056300480,
    "archive_sha256": "d47283bedc85746aea26f7c30028ffc4e6c20578919ccbb913174e05c605242c",
    "run": 44666294821,
    "head": "e8f6e7dbce77676bf375a66b86db41742d896cd2"
  },
  {
    "flop": "KsQh4d",
    "version": "gto",
    "artifact": 14601426559,
    "job": 136056300417,
    "archive_sha256": "144919b63c7609d4256109db43d81f60004bad04a1bb7398759d238edc70f454",
    "run": 44666294821,
    "head": "e8f6e7dbce77676bf375a66b86db41742d896cd2"
  },
  {
    "flop": "8s8h3d",
    "version": "gto",
    "artifact": 14600026283,
    "job": 136056300749,
    "archive_sha256": "7583287177315c74022553f0b64dc91d39c95a9dee0f84329dd99b22564c273e",
    "run": 44666294821,
    "head": "e8f6e7dbce77676bf375a66b86db41742d896cd2"
  },
  {
    "flop": "8s8h3d",
    "version": "exp_ip",
    "artifact": 14599769541,
    "job": 136056300105,
    "archive_sha256": "c891339f9dfeb072f96562827956f59c6659623252f813ef2ebae4e190806cef",
    "run": 44666294821,
    "head": "e8f6e7dbce77676bf375a66b86db41742d896cd2"
  },
  {
    "flop": "9s6h3d",
    "version": "exp_ip",
    "artifact": 14599454837,
    "job": 136056300465,
    "archive_sha256": "a9097cf51633aede964f0a9a83c591dc63a8a3e794aa0d430aa677dfee27cbce",
    "run": 44666294821,
    "head": "e8f6e7dbce77676bf375a66b86db41742d896cd2"
  },
  {
    "flop": "9s6h3d",
    "version": "gto",
    "artifact": 14599037935,
    "job": 136056300453,
    "archive_sha256": "f6d4d734bcb9d35f9c779e5b0d9853b23217bb1b44ef17b73ef35f4ef2fb0c11",
    "run": 44666294821,
    "head": "e8f6e7dbce77676bf375a66b86db41742d896cd2"
  }
]


def screen(directory):
    route=json.loads(subprocess.check_output(['node',native.ROUTE]))
    viewer=Path('data/solver_evidence/NL2_MULTIBOARD_B3.json.gz')
    index=json.loads(viewer.with_name('NL2_MULTIBOARD_B3.index.json').read_bytes())
    assert sha(viewer.read_bytes())==index['gzip_sha256']
    result=[]
    for pin in PINS:
        original=directory/f"{pin['artifact']}.zip"
        assert sha(original.read_bytes())==pin['archive_sha256']
        with ZipFile(original) as z:
            mf,=[n for n in z.namelist() if n.startswith('evidence/') and n.endswith('.json')]
            raw=z.read(mf);m=json.loads(raw)
            assert (m['spot'],m['version'],m['flop'],m['failures'])==('LMP_CO_BB',pin['version'],pin['flop'],[])
            rraw=z.read('solver/postflop/'+m['file_flop'])
            assert sha(rraw)==m['file_flop_sha256']
            r=json.loads(rraw);job_raw=z.read('solver/postflop/'+m['file_flop'].replace('.json','.job.json'))
            native.limp.check_limp_source(dict(manifest=m,root_job=json.loads(job_raw),subgame_job=None))
            assert (r['pot'],r['stack'])==(250,9900) and 0<=r['info']['gto_expl_pct']<=.5
            if pin['version']=='exp_ip':
                assert 0<=r['info']['hero_gap_pct']<=.5
            turns=[n['board'][-2:] for n in r['nodes'] if n['line']=='x b33 c/' and n.get('wr')]
            assert len(turns)==1
            parent,kept,rivers,report=native.parent_gate(r,turns[0],route)
            assert not kept and not rivers and report['flop_displayed_draws']==0
            result.append(dict(**pin,manifest_sha256=sha(raw),root_sha256=sha(rraw),root_job_sha256=sha(job_raw),
                original_turn_boundary=turns[0],original_gto_stage_gap_pct=r['info']['gto_expl_pct'],
                original_hero_gap_pct=r['info'].get('hero_gap_pct'),root_gate=report))
    return dict(schema='NL2_B731_HISTORICAL_RANK150_ROOT_REACH_SCREEN_V1',rank=150,model_id=native.MODEL,
        source_worker_blob=native.limp.git_blob('tools/hu_b724_rank150_rivers.py'),
        source_route_blob=native.limp.git_blob(native.ROUTE),originals=result,strict_displayed_flop_draws=0,
        positive_distinct_flops=0,additional_native_solves=0)


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--archives',required=True,type=Path)
    cli.add_argument('--out',required=True,type=Path);args=cli.parse_args()
    args.out.write_bytes(json_bytes(screen(args.archives)))
