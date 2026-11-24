"""Replay the three preserved B713 worker ZIPs against their original B524 roots."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import hu_b713_btn_lead_rivers as native
from hu_b467_river_source_gate import json_bytes, sha
from hu_b710_publish import unpack_original

RUN=45325726082
HEAD='dfedf0e3e17a7da5f68583e250df3fa91de7b8ad'
REPO='tetracycline/poker-trainer'
BRANCH='fix/nl2-hu-lines-audit-20261118'
WORKFLOW='.github/workflows/nl2-hu-b713-btn-lead-rivers.yml'
ROUTE='tools/hu_b713_btn_lead_routes.cjs'
PINS={
    '6s5h4d':(14889043603,138214737134,'e70cb099aa77d8d50fb61ca4ccf137fff8198a2539256758057afcde6d7afb13'),
    '7d5c4c':(14889831091,138214736772,'ef69ab01baf742f847620a9ccc83f98bfd7a84413c74b1314957deacfa5429d9'),
    '6d4c3h':(14889023667,138214737160,'f9c6b6bc3c6f28d5bceacbe07cf683eec229bfd70bae1eded2cae41e34bfbbd3'),
}
BLOBS={
    "tools/hu_b713_btn_lead_rivers.py": "966c8247c6d5bc384aba3ba62351c1ec17aadb32",
    "tools/hu_b713_btn_lead_routes.cjs": "c74c7ec997694924fd5d67ba47aa799b52113023",
    ".github/workflows/nl2-hu-b713-btn-lead-rivers.yml": "0e385b992aae1faf01d09674bfd791a53f860045",
    "tools/hu_checked_gto_boundary.py": "219f46b0a259fa3e71f1225046ab5b12c44c28c6",
    "tools/hu_b637_rank57.py": "86b795adbd8ff4e6e411a70cebf8b3db1efc4ff9",
    "tools/hu_b483_locked_medium.py": "018ac485d3fc115f125c777399d96ce38b0f5f04",
    "tools/hu_sequential_cfr_reach.py": "f26df926c088e5b4117bb911956cbc5031e2458d",
    "tools/hu_b568_caller_rivers.py": "e69bda7fe46c3dd18a48dee1bb97f965ab2813f7",
    "tools/hu_b467_river_source_gate.py": "57d9eac04b074eb58e54ede0de384682fad35062",
    "tools/lines_pipeline/vclass.py": "512f315c14baa2eb1af908a9f3cbc1f68d57e533",
    "tools/lines_pipeline/common.py": "7338a5593f19dd878aba5cb21690bc9cf90365b3",
    "tools/verify_hu_multiboard_100bb.py": "df06b9480c0beef93165c46b13e71dd641f82177"
}
STEPS={'Authenticate immutable old artifact and actual compatible BTN and BB ranges','Compile pinned native engine',
    'Solve only missing turn and river policies and replay both model gates','Run actions/upload-artifact@v4'}


def receipts(raw):
    run=raw['run']
    assert (run['id'],run['head_sha'],run['head_branch'],run['path'],run['status'],run['conclusion'])==(
        RUN,HEAD,BRANCH,WORKFLOW,'completed','success')
    assert (run['repository']['id'],run['repository']['full_name'])==(1438346845,REPO)
    # Reconstruct only the identified GitHub API fields, including successful job steps.
    # An operational input may also contain expiring download URLs; none enter the evidence.
    selected={k:run[k] for k in ('id','head_sha','head_branch','path','status','conclusion','run_attempt')}
    selected['repository']={k:run['repository'][k] for k in ('id','full_name')}
    result=dict(run=selected,jobs=[],artifacts=[])
    assert len(raw['jobs'])==len(raw['artifacts'])==3
    for flop,(aid,jid,digest) in PINS.items():
        _,root_id,_=native.CASES[flop]
        job,=[j for j in raw['jobs'] if j['id']==jid]
        assert (job['id'],job['run_id'],job['run_attempt'],job['head_sha'],job['name'],job['status'],job['conclusion'])==(
            jid,RUN,run['run_attempt'],HEAD,f'resolve ({flop}, {root_id})','completed','success')
        assert STEPS<={s['name'] for s in job['steps'] if (s['status'],s['conclusion'])==('completed','success')}
        j={k:job[k] for k in ('id','run_id','run_attempt','head_sha','name','status','conclusion')}
        j['steps']=[{k:s[k] for k in ('name','number','status','conclusion')} for s in job['steps']]
        artifact,=[a for a in raw['artifacts'] if a['id']==aid]
        assert (artifact['name'],artifact['digest'],artifact['expired'])==('B713-BTN-'+flop,'sha256:'+digest,False)
        w=artifact['workflow_run']
        assert (w['id'],w['head_sha'],w['head_branch'],w['repository_id'],w['head_repository_id'])==(RUN,HEAD,BRANCH,1438346845,1438346845)
        a={k:artifact[k] for k in ('id','name','digest','size_in_bytes','created_at','expires_at','expired')}
        a['workflow_run']={k:w[k] for k in ('id','head_sha','head_branch','repository_id','head_repository_id')}
        result['jobs'].append(j)
        result['artifacts'].append(a)
    return result


def replay(args):
    assert sys.version_info[:2]==(3,11),'Use the source Python 3.11 runtime'
    for path,digest in BLOBS.items():
        assert subprocess.check_output(['git','hash-object',path],text=True).strip()==digest,path
    routes=subprocess.check_output(['node',ROUTE])
    auth=receipts(json.loads(args.receipts.read_bytes()))
    out=args.output.resolve()
    assert not out.exists() and Path('data').resolve() not in (out,*out.parents)
    out.mkdir(parents=True)
    evidence=out/'solver_evidence'
    evidence.mkdir()
    reports=[]
    decisions={k:[] for k in native.TARGETS}
    with TemporaryDirectory(prefix='b720-native-replay-') as tmp:
        temp=Path(tmp)
        for flop,(aid,jid,digest) in PINS.items():
            code='NL2_B713_BTN_'+flop.upper()+'.zip'
            source=args.archives/f'{aid}.zip'
            if not source.is_file():
                source=args.archives/code
            raw=source.read_bytes()
            assert sha(raw)==digest
            folder=temp/flop
            folder.mkdir()
            assert unpack_original(raw,folder)=={'gto/job.json','gto/result.json','rendered-routes.json','proof.json','original-flop-artifact.json'}
            assert (folder/'rendered-routes.json').read_bytes()==routes
            turn,old_id,old_sha=native.CASES[flop]
            old_receipt=(folder/'original-flop-artifact.json').read_bytes()
            (temp/f'{old_id}.json').write_bytes(old_receipt)
            original=(folder/'proof.json').read_bytes()
            report=json.loads(original)
            assert (report['schema'],report['source_run'],report['source_head'],report['flop'],report['turn'],report['spot'],report['actor'])==(
                'NL2_B713_FROZEN_B524_BTN_BARREL_RIVERS_V1',RUN,HEAD,flop,turn,'BTN_BB',1)
            assert (report['root_run'],report['root_head'],report['root_pin']['artifact_id'],report['root_pin']['artifact_sha256'])==(
                native.RUN,native.HEAD,old_id,old_sha)
            assert report['gto_job_sha256']==sha((folder/'gto/job.json').read_bytes())
            assert report['gto_source_sha256']==sha((folder/'gto/result.json').read_bytes())
            native.run(SimpleNamespace(solver=args.solver,flop=flop,routes=folder/'rendered-routes.json',receipts=temp,
                output=folder,run=RUN,head=HEAD,preflight=False,driver=None))
            assert (folder/'proof.json').read_bytes()==original
            assert (report['actor_lock_solved'],report['nl2_job_sha256'],report['nl2_source_sha256'],
                report['measured_lock_application'],report['flop_native_solves_repeated'])==(False,None,None,None,0)
            counts={}
            for rank,group in report['groups'].items():
                assert (group['positive_distinct_flops'],group['nl2_boards'],group['common'],group['selected'])==(0,[],[],None)
                for row in group['gto_boards']:
                    reached=row['reach']
                    assert (row['displayed_hands'],reached['strict_legal_combos'],reached['compatible_hole_card_pairs'],
                        reached['b50'],reached['status'])==(0,0,0,None,'ZERO_JOINT_REACH')
                    decisions[rank].append(row['public_board'])
                counts[rank]=len(group['gto_boards'])
            (evidence/code).write_bytes(raw)
            reports.append(dict(flop=flop,turn=turn,source_artifact=aid,source_job=jid,source_archive=code,
                archive_sha256=digest,original_proof_sha256=sha(original),original_root=report['root_pin'],
                gto_job_sha256=report['gto_job_sha256'],gto_source_sha256=report['gto_source_sha256'],zero_joint_decisions=counts))
    totals={r:len(rows) for r,rows in decisions.items()}
    public=set().union(*decisions.values())
    assert totals=={'104':32,'105':48} and len(public)==69
    summary=dict(schema='NL2_HU_B720_B713_RAW_NONREACHABLE_RIVERS_V1',source_run=RUN,source_head=HEAD,
        workers=reports,zero_joint_gto_nodes_by_rank=totals,zero_joint_gto_nodes=80,distinct_public_rivers=69,
        distinct_positive_flops_by_rank={'104':0,'105':0},gto_turn_subgames=3,actor_locked_boards=0,
        medium_assessed_boards=0,nonpolarized_candidates=0,cert_eligible_ranks=[],native_solves_repeated=0)
    (out/'nl2_hu_b720_source_receipts.json').write_bytes(json_bytes(auth))
    (out/'nl2_hu_b720_summary.json').write_bytes(json_bytes(summary))
    print(json.dumps(dict(source_run=RUN,zero_joint=80,unique_public=69,actor_locked=0,medium_assessed=0)))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--archives',type=Path,default=Path('data/solver_evidence'))
    cli.add_argument('--receipts',type=Path,default=Path('data/nl2_hu_b720_source_receipts.json'))
    for key in ('solver','output'):
        cli.add_argument('--'+key,type=Path,required=True)
    replay(cli.parse_args())
