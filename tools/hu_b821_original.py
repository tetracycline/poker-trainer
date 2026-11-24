"""B821: permanently archive B820 rank264 missing-river ancestry gate, zero native solves."""
import argparse,json,subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from hu_b805_original import api
from hu_b738_collect import run_receipt,job_receipt,artifact_receipt
from hu_b710_publish import unpack_original
from hu_b467_river_source_gate import json_bytes,sha
import hu_b820_rank264_missing_rivers as worker
RUN=45495202512
HEAD='8a15545733c7565eb3c6d5c7dad21eeaafd35beb'
WF='.github/workflows/nl2-hu-b820-rank264-missing-rivers.yml'
WORKER='tools/hu_b820_rank264_missing_rivers.py'
AID=14967528605
DIGEST='636e441ee1ea3547953961207429638ce4bf637aa3d472db4d8c7a2842ebcc6a'
JOB=138803719974
def collect(folder):
    folder.mkdir(parents=True,exist_ok=False)
    ep='actions/runs/'+str(RUN)
    run=run_receipt(json.loads(api(ep)),RUN,HEAD,WF)
    assert run['run_attempt']==1
    j=json.loads(api(ep+'/jobs?per_page=100'))
    a=json.loads(api(ep+'/artifacts?per_page=100'))
    assert j['total_count']==a['total_count']==1
    job=job_receipt(j['jobs'][0],run,JOB,'original-reach',['Authenticate both original policies and independently compare actual physical common turn hands','Run actions/upload-artifact@v4'])
    artifact=artifact_receipt(a['artifacts'][0],run,AID,'B820-rank264-unexported-river-gate',DIGEST)
    pins={}
    for path in (WF,WORKER):
        pin=json.loads(api('contents/'+path+'?ref='+HEAD))['sha']
        assert subprocess.check_output(['git','hash-object',path],text=True).strip()==pin
        pins[path]=pin
    raw=api('actions/artifacts/'+str(AID)+'/zip')
    assert sha(raw)==DIGEST and len(raw)==artifact['size_in_bytes']
    (folder/'original.zip').write_bytes(raw)
    (folder/'receipt.json').write_bytes(json_bytes(dict(run=run,job=job,artifact=artifact,blobs=pins)))
def replay(a):
    stage=a.output.resolve()
    assert not stage.exists() and not stage.is_relative_to(Path('data').resolve())
    ev=stage/'solver_evidence';partial=ev/'partial';partial.mkdir(parents=True)
    before=Path('data/nl2_hu_multiboard_status_current.json').read_bytes()
    receipt=json.loads((a.archives/'receipt.json').read_bytes())
    assert receipt['run']['head_sha']==HEAD and receipt['job']['id']==JOB and receipt['artifact']['id']==AID
    raw=(a.archives/'original.zip').read_bytes();assert sha(raw)==DIGEST
    with TemporaryDirectory(prefix='b821-') as d:
        d=Path(d);original=d/'original';original.mkdir()
        assert unpack_original(raw,original)=={'b820-23.json'}
        claim=json.loads((original/'b820-23.json').read_bytes())
        worker.run(d/'replay.json')
        actual=json.loads((d/'replay.json').read_bytes())
        assert actual==claim and actual['eligible_turns']==actual['original_flop_solves']==actual['conditional_solves']==0 and actual['not_a_certificate']
        assert len(actual['checked_turns'])==2
        assert all(x['common_rendered_hero']==0 and not x['new_rivers'] for x in actual['checked_turns'])
        result=dict(rank=264,source_run=RUN,source_head=HEAD,original_flop_solves=0,checked_new_river_ancestries=2,eligible_turns=0,positive_distinct_flops=0,cert_eligible_ranks=[],locked_public_boards=0,joint_halfpot_assessed=0,halfpot_candidates=0,unchanged_registry_sha256=sha(before),source_artifacts=[AID])
        (partial/'b821_rank264_missing_river_ancestry.json').write_bytes(json_bytes(dict(result=result,proof=actual,archive='NL2_B820_R264_UNEXPORTED_RIVERS.zip',sha256=DIGEST)))
        (stage/'nl2_hu_b821_results.json').write_bytes(json_bytes(result))
        (stage/'nl2_hu_b821_source_receipts.json').write_bytes(json_bytes(receipt))
        (ev/'NL2_B820_R264_UNEXPORTED_RIVERS.zip').write_bytes(raw)
    assert before==Path('data/nl2_hu_multiboard_status_current.json').read_bytes()
    print(json.dumps(result))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--archives',type=Path,required=True)
    p.add_argument('--output',type=Path)
    p.add_argument('--collect',action='store_true')
    a=p.parse_args()
    if a.collect:collect(a.archives)
    else:replay(a)
