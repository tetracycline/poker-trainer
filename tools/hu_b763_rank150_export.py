"""Authenticate and replay B760's sixteen additional rank150 river extractions."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import hu_b760_rank150_rivers as worker
import hu_b756_rank150 as previous
from hu_b467_river_source_gate import json_bytes,sha
from hu_b710_publish import unpack_original
from hu_b738_collect import artifact_receipt,job_receipt,run_receipt

RUN=45339742939
HEAD='2866c4a21d742bf6c6407146510f52349fc86e43'
JOB=138260253534
ARTIFACT=14895188746
DIGEST='a1834ecef09c08256bb1ef845f6d950ac54314feeffc4291709f3d92aa8f2e58'
WORKFLOW='.github/workflows/nl2-hu-b760-rank150-new-rivers.yml'
SOURCE='tools/hu_b760_rank150_rivers.py'
PINS={WORKFLOW:'35188a6f83ecb117f2cca0e3b1e735a3552f28e1',SOURCE:'1480d68ea05eeae56b86f3f4d3f2bff9cd0c0256'}
STEPS=['Replay the original paired-turn jobs and preregister the new physical BB and CO deals','Compile the pinned native solver',
       'Export new rivers and verify all 210 original nodes per policy and both seats','Run actions/upload-artifact@v4']
CODE='B760_R150_TS9S5H_9D'
MODEL=worker.native.MODEL


def auth(raw):
    r=run_receipt(raw['run'],RUN,HEAD,WORKFLOW)
    j,=raw['jobs'];a,=raw['artifacts']
    return dict(run=r,jobs=[job_receipt(j,r,JOB,'solve',STEPS)],artifacts=[artifact_receipt(a,r,ARTIFACT,'B760-R150-Ts9s5h-9d',DIGEST)])


def collect(out):
    from hu_b710_collect import api
    out.mkdir(parents=True,exist_ok=True);base=f'actions/runs/{RUN}'
    receipts=auth(dict(run=json.loads(api(base)),jobs=json.loads(api(base+'/jobs?per_page=100'))['jobs'],
        artifacts=json.loads(api(base+'/artifacts?per_page=100'))['artifacts']))
    (out/'receipt.json').write_bytes(json_bytes(receipts))
    raw=api(f'actions/artifacts/{ARTIFACT}/zip')
    assert sha(raw)==DIGEST and len(raw)==receipts['artifacts'][0]['size_in_bytes']
    (out/f'{ARTIFACT}.zip').write_bytes(raw)


def publish(a):
    assert sys.version_info[:2]==(3,11)
    for path,pin in PINS.items():
        assert subprocess.check_output(['git','rev-parse',HEAD+':'+path],text=True).strip()==pin
        assert subprocess.check_output(['git','hash-object',path],text=True).strip()==pin
    solver=a.solver.resolve();sys.path.insert(0,str(solver/'postflop/py'));import pipeline
    poolraw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(poolraw)==worker.native.POOL
    pool=json.loads(poolraw)['NL2']
    reg=Path('data/nl2_hu_multiboard_status_current.json');before=reg.read_bytes();model=json.loads(before)['records'][MODEL]
    assert (model['frequency_rank'],model['assumed_model_node_spr'])==(150,23.558)
    ev=Path('data/solver_evidence');current=subprocess.check_output(['node',worker.native.ROUTE])
    out=a.output.resolve();assert not out.exists() and not out.is_relative_to(Path('data').resolve());dest=out/'solver_evidence';dest.mkdir(parents=True)
    receipt=auth(worker.read(a.receipts));previous.write(out/'nl2_hu_b763_source_receipts.json',receipt)
    raw=a.archive.read_bytes();assert len(raw)==receipt['artifacts'][0]['size_in_bytes'] and sha(raw)==DIGEST
    (dest/('NL2_'+CODE+'.zip')).write_bytes(raw)
    with TemporaryDirectory(prefix='b763-') as td:
        temp=Path(td);prior=temp/'prior';prior.mkdir()
        group,medium=previous.previous(prior,solver,model,pipeline,pool,current)
        assert group==worker.read(ev/'partial/b756_rank150.json') and medium==worker.read(ev/'partial/b756_rank150_locked_medium.json')
        folder=temp/'B760';names=unpack_original(raw,folder);proof=(folder/'proof.json').read_bytes();d=json.loads(proof)
        assert (folder/'rendered-routes.json').read_bytes()==current and d['source']['root_result_sha256']==worker.ROOT_SHA
        assert names=={'proof.json','rendered-routes.json'}|{worker.TURN+'-'+v+'/'+k for v in d['policies'] for k in ('job.json','result.json')}
        worker.run(SimpleNamespace(solver=solver,output=folder,preflight=False,driver=None))
        assert proof==(folder/'proof.json').read_bytes()
        assert d['common']=={} and d['selected_public_board'] is None and d['positive_distinct_flops']==0
        assert set(d['policies'])=={'gto'} and (d['locked_named_boards'],d['joint_halfpot_assessed'],d['nonpolarized_candidates'])==(0,0,0)
        pol=d['policies']['gto'];observed=pol['boards']
        assert len(observed)==16 and set(d['new_rivers'])==set(worker.RIVERS) and not (set(d['new_rivers'])&set(d['original_rivers']))
        assert set(pol['eligible_deal_counts'])==set(observed) and not any(pol['eligible_deal_counts'].values())
        display={p:sorted(r['hands']) for p,r in observed.items() if r['hands']}
        assert display=={'5h9sTs9dAc':['8cJh','8dJh'],'5h9sTs9dAd':['8cJh','8dJh']}
        assert set(d['preflight']['same_both_policy_hero_hands'])=={'JcQh','JdQh'}
        assert all(set(h).isdisjoint(d['preflight']['same_both_policy_hero_hands']) for h in display.values())
    n=len(group['boards']);assert n==len(group['pins'])==2
    summary=dict(schema='NL2_B763_ORIGINAL_RANK150_UNEXPORTED_RIVERS_V1',rank=150,model_id=MODEL,source_run=RUN,source_head=HEAD,artifact_id=ARTIFACT,
        job_id=JOB,archive_sha256=DIGEST,proof_sha256=sha(proof),original_b724_source=d['source'],old_nodes_verified_per_policy=210,
        gto_ui_compatible_new_rivers=sum(v>0 for v in d['policies']['gto']['eligible_deal_counts'].values()),selected_public_board=d['selected_public_board'],
        positive_distinct_flops=n,new_positive_named_boards=0,cert_eligible_ranks=[],
        gto_positive_joint_reach=sum(r['reach']['strict_legal_combos']>0 for r in observed.values()),gto_displayed_without_locked_turn_compatibility=display,
        common_gto_and_locked_turn_hands=d['preflight']['same_both_policy_hero_hands'],published_prior_positive_group='data/solver_evidence/partial/b756_rank150.json',
        **{k:d[k] for k in ('locked_named_boards','joint_halfpot_assessed','nonpolarized_candidates')})
    previous.write(out/'nl2_hu_b763_results.json',summary)
    assert reg.read_bytes()==before
    print(json.dumps(summary))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    c=sub.add_parser('collect');c.add_argument('--output',type=Path,required=True)
    s=sub.add_parser('publish')
    for k in ('solver','output','receipts','archive'):s.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();collect(a.output) if a.mode=='collect' else publish(a)
