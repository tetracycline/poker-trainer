"""B845: independently replay and preserve completed B844 raw artifacts, no native rerun."""
import argparse, json, subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from hu_b805_original import api
from hu_b738_collect import run_receipt, job_receipt, artifact_receipt
from hu_b710_publish import unpack_original
from hu_b467_river_source_gate import json_bytes, sha
import hu_b844_bb_two_tone as worker

RUN=45535807925
HEAD='3adcd4ccbf81e2f7946f7ddbb9ea88436ecd2a4f'
WF='.github/workflows/nl2-hu-b844-co-bb-two-tone.yml'
PINS=[
 ('7h6h2c',138941981103,14987535334,'790ef957e607ee6b5e78a770a58a1d98b4b15e5ce7d9a7acd918565be601b129'),
 ('8h7h3c',138941981525,14986942830,'026c6b4de189a1c29c56d3edc8a51bd6121850c8c62991af4cb41a55b33aeb34'),
 ('9h8h2c',138941981395,14986593813,'8cde6b16e3532fceeff9b2a74f18d3e7970cb9ac69562db0216f63401911f3c4')]
STEPS=['Freeze actual UI routes and verify pinned CO-BB ranges and exact prices','Build the pinned native solver','Solve one original flop and the reachable multi-size GTO and actor-lock continuations','Run actions/upload-artifact@v4']

def read(path): return json.loads(path.read_bytes())

def collect(folder):
    folder.mkdir(parents=True,exist_ok=False)
    ep='actions/runs/'+str(RUN)
    run=run_receipt(json.loads(api(ep)),RUN,HEAD,WF)
    assert run['run_attempt']==1
    js=json.loads(api(ep+'/jobs?per_page=100'))
    ars=json.loads(api(ep+'/artifacts?per_page=100'))
    assert js['total_count']==ars['total_count']==len(PINS)
    receipt=dict(run=run,jobs=[],artifacts=[],blobs={})
    for path in (WF,'tools/hu_b844_bb_two_tone.py','tools/hu_b711_bb_lead_rivers.py','tools/hu_b711_bb_lead_routes.cjs'):
        pin=json.loads(api('contents/'+path+'?ref='+HEAD))['sha']
        assert subprocess.check_output(['git','hash-object',path],text=True).strip()==pin
        receipt['blobs'][path]=pin
    for flop,jid,aid,digest in PINS:
        j,=[x for x in js['jobs'] if x['id']==jid]
        receipt['jobs'].append(job_receipt(j,run,jid,'solve ('+flop+')',STEPS))
        a,=[x for x in ars['artifacts'] if x['id']==aid]
        a=artifact_receipt(a,run,aid,'B844-CO-BB-'+flop,digest)
        raw=api('actions/artifacts/'+str(aid)+'/zip')
        assert sha(raw)==digest and len(raw)==a['size_in_bytes']
        (folder/(str(aid)+'.zip')).write_bytes(raw)
        receipt['artifacts'].append(a)
    (folder/'receipt.json').write_bytes(json_bytes(receipt))

def replay(a):
    stage=a.output.resolve()
    assert not stage.exists() and not stage.is_relative_to(Path('data').resolve())
    ev=stage/'solver_evidence'; partial=ev/'partial';partial.mkdir(parents=True)
    registry=Path('data/nl2_hu_multiboard_status_current.json');before=registry.read_bytes()
    status=json.loads(before)
    assert (status['CERT_MULTIBOARD'],status['APPROX'],status['TOTAL'])==(158,234,392)
    rec=read(a.archives/'receipt.json')
    assert (rec['run']['id'],rec['run']['head_sha'])==(RUN,HEAD)
    observations=[]
    with TemporaryDirectory(prefix='b845-') as tmp:
        for flop,jid,aid,digest in PINS:
            raw=(a.archives/(str(aid)+'.zip')).read_bytes()
            assert sha(raw)==digest and any(x['id']==aid and x['digest']=='sha256:'+digest for x in rec['artifacts'])
            dest=Path(tmp)/str(aid);dest.mkdir()
            names=unpack_original(raw,dest)
            hashes={n:sha((dest/n).read_bytes()) for n in sorted(names)}
            claim=read(dest/'proof.json')
            worker.run(SimpleNamespace(solver=a.solver,output=dest,routes=dest/'rendered-routes.json',flop=flop,driver=None,preflight=False))
            actual=read(dest/'proof.json')
            assert actual==claim and actual['flop']==flop
            assert actual['positive_distinct_flops_by_rank']=={'92':0,'93':0,'94':0}
            assert actual['actor_locked_turn_subgames']==0
            assert actual['unique_locked_public_boards']==actual['unique_medium_assessed_public_boards']==actual['unique_nonpolarized_candidate_public_boards']==0
            assert all(not any(t['common_by_rank'].values()) and not t['actor_locked'] for t in actual['turns'])
            assert all(sha((dest/n).read_bytes())==h for n,h in hashes.items())
            name='NL2_B844_CO_BB_'+flop.upper()+'.zip'
            (ev/name).write_bytes(raw)
            observations.append(dict(flop=flop,job=jid,artifact=aid,archive=name,archive_sha256=digest,native_file_sha256=hashes,proof=actual))
    result=dict(source_run=RUN,source_artifacts=[o['artifact'] for o in observations],
        positive_distinct_flops_by_rank={'92':0,'93':0,'94':0},cert_eligible_ranks=[],native_repeated=0,
        locked_public_boards=0,joint_halfpot_assessed=0,halfpot_candidates=0,
        unchanged_registry_sha256=sha(before),
        root_count=len(observations),gto_turn_subgames=sum(o['proof']['gto_turn_subgames'] for o in observations),
        model_node_opportunity_coverage_pct=84.700987)
    (stage/'nl2_hu_b845_source_receipts.json').write_bytes(json_bytes(rec))
    (stage/'nl2_hu_b845_results.json').write_bytes(json_bytes(result))
    (partial/'b845_b844_original_observations.json').write_bytes(json_bytes(dict(result=result,observations=observations)))
    assert before==registry.read_bytes()
    print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archives',type=Path,required=True)
    p.add_argument('--solver',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--collect',action='store_true')
    a=p.parse_args()
    if a.collect:collect(a.archives)
    else:replay(a)
