"""B864: authenticate completed B862/B863 screens, replay without native, stage immutable receipts."""
import json,sys,subprocess
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from collections import Counter
from hu_b859_limp_boundaries import api
from hu_b467_river_source_gate import sha,json_bytes
from hu_b861_rank128_originals import main as replay128
from hu_b863_rank136_boundaries import main as replay136

BRANCH='fix/nl2-hu-lines-audit-20261118'
PINS=[
 dict(tag='b862_rank128',rank=128,run=45649536120,audit=45649536010,head='277af71312b8e84c6b9e976b4bd374cbbb096a5e',job=139329931206,artifact=15039542398,size=19489,digest='a2367e3938f38226559a798f8d3d3d2671562017ea13bbe507c41f23480d4512',name='B861-rank128-original-source-screen',workflow='.github/workflows/nl2-hu-b861-rank128-originals.yml',script='tools/hu_b861_rank128_originals.py'),
 dict(tag='b863_rank136',rank=136,run=45649707333,audit=45649707383,head='a38b45def0f24ca1750059838196221796c4e40c',job=139330545433,artifact=15038124406,size=29144,digest='c4a864eb9f5d3d38f7eb1f92673bbb056582c3a1482db65188a724569c8ecb6b',name='B863-rank136-unused-chance-boundaries',workflow='.github/workflows/nl2-hu-b863-rank136-boundaries.yml',script='tools/hu_b863_rank136_boundaries.py')]
def read(p):return json.loads(api(p))
def authenticated(p):
    run=read(f"actions/runs/{p['run']}");audit=read(f"actions/runs/{p['audit']}");job=read(f"actions/jobs/{p['job']}");meta=read(f"actions/artifacts/{p['artifact']}")
    assert (run['id'],run['head_sha'],run['head_branch'],run['status'],run['conclusion'],run['path'])==(p['run'],p['head'],BRANCH,'completed','success',p['workflow'])
    assert (audit['head_sha'],audit['status'],audit['conclusion'],audit['name'])==(p['head'],'completed','success','NL2 full batch audit')
    assert (job['run_id'],job['head_sha'],job['status'],job['conclusion'])==(p['run'],p['head'],'completed','success')
    assert (meta['id'],meta['name'],meta['digest'],meta['size_in_bytes'],meta['expired'])==(p['artifact'],p['name'],'sha256:'+p['digest'],p['size'],False)
    assert (meta['workflow_run']['id'],meta['workflow_run']['head_sha'])==(p['run'],p['head'])
    raw=api(f"actions/artifacts/{p['artifact']}/zip")
    assert len(raw)==p['size'] and sha(raw)==p['digest']
    with ZipFile(BytesIO(raw)) as z:
        assert z.testzip() is None
        files={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
    return raw,files,dict(run=run,audit=audit,job=job,artifact=meta)
def main(stage,solver):
    assert not stage.exists()
    partial=stage/'solver_evidence'/'partial';partial.mkdir(parents=True)
    summaries=[]
    for p,replay in zip(PINS,(replay128,replay136),strict=True):
        for path in (p['workflow'],p['script']):
            assert subprocess.check_output(['git','hash-object',path],text=True).strip()==read(f"contents/{path}?ref={p['head']}")['sha']
        raw,files,receipts=authenticated(p)
        temp=stage.parent/('replay-'+p['tag']);replay(temp,solver)
        assert set(files)=={x.name for x in temp.iterdir()}
        for n in ('report.json','rendered-routes.json'):
            assert files[n]==(temp/n).read_bytes(),n
        r=json.loads(files['report.json']);assert r['rank']==p['rank']
        assert all(r[k]==0 for k in ('native_solves','cert_promotions','locked_public_boards','joint_halfpot_assessed','nonpolarized_candidates'))
        if p['rank']==128:
            rows=[x for f in r['source_flops'] for x in f['rows']]
            counts=Counter(x['status'] for x in rows)
            assert len(r['source_flops'])==6 and counts=={'NO_DISPLAYED_BOUNDARY_WITNESS':5,'EXCLUDED_PREVIOUS_B735_BOUNDARY':1}
            assert not any(x.get('exact_gto_river_nodes') for x in rows)
            evidence=dict(boundary_status=dict(counts))
        else:
            leads={f['flop']:sum(bool(x['river_boundary_witnesses']) for x in f['rows']) for f in r['flops']}
            assert all(len(f['rows'])==39 for f in r['flops']) and leads=={'Ac7h3d':21,'Ah7d4c':21,'As6c3h':18}
            evidence=dict(unseen_boundaries=117,leads=leads)
        (partial/(p['tag']+'_report.json')).write_bytes(files['report.json'])
        (partial/(p['tag']+'_receipts.json')).write_bytes(json_bytes(receipts))
        (partial.parent/('NL2_B864_'+p['tag']+'_SCREEN.zip')).write_bytes(raw)
        summaries.append(dict(**p,report_and_route_replay_byte_equal=True,member_sha256={n:sha(v) for n,v in files.items()},**evidence))
    summary=dict(schema='NL2_B864_AUTHENTIC_BOUNDARY_ARCHIVE_V1',sources=summaries,cert_promotions=0,native_solves=0,locked_public_boards=0,joint_halfpot_assessed=0,nonpolarized_candidates=0,scope='Rank128 exported boundaries only; rank136 reconstructed GTO chance inputs, not solved turn or river or joint reach.')
    (stage/'nl2_hu_b864_results.json').write_bytes(json_bytes(summary));print(json.dumps(summary))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
