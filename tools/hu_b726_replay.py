"""Rebuild the three B722 source proofs and validate all named locked river nodes."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import hu_b722_rank264 as worker
from hu_b467_river_source_gate import json_bytes, sha
from hu_b483_locked_medium import proof
from hu_b710_publish import unpack_original
from hu_sequential_cfr_reach import game_reach

RUN=45327823847
HEAD='4e5bb6450f2d96abe4eea43a00ae2d159ca6a67e'
BRANCH='fix/nl2-hu-lines-audit-20261118'
WORKFLOW='.github/workflows/nl2-hu-b722-rank264-rivers.yml'
WORKER='tools/hu_b722_rank264.py'
BLOB='5612208f7778140da041c8caa69b6a301c1e9c4a'
PINS={
    'Js7s4d':(14890970661,138221552144,'052ff14b00c03cf6cd3dbfad913f470dda0b5428f1834ba15c0e2eebe24457ea'),
    'Ts7s3h':(14889634356,138221552268,'23454d5bf680a3875961fd46c6ffa8cabfb8d9b580f5a34f90ac243c98c80c9a'),
    'Jc9c5d':(14890896058,138221552238,'bffb2665a207ef063f1eb73a75179431f632dbd5cb34fa2b19133ab95a2d456b'),
}
STEPS={'Verify the pinned BB3 ranges, old two-seat checks and current rank264 UI','Build the pinned native solver',
       'Solve the unexported expanded river policies and replay without a native driver','Run actions/upload-artifact@v4'}


def read(path):
    return json.loads(path.read_bytes())


def fields(record, names):
    return {key:record[key] for key in names.split()}


def authenticate(api):
    raw=api['run']
    r=fields(raw,'id head_sha head_branch path status conclusion run_attempt')
    r['repository']=fields(raw['repository'],'id full_name')
    assert (r['id'],r['head_sha'],r['head_branch'],r['path'],r['status'],r['conclusion'])==(RUN,HEAD,BRANCH,WORKFLOW,'completed','success')
    assert r['repository']==dict(id=1438346845,full_name='tetracycline/poker-trainer')
    assert len(api['jobs'])==len(api['artifacts'])==3
    out=dict(run=r,jobs=[],artifacts=[])
    for flop,(aid,jid,digest) in PINS.items():
        j,=[v for v in api['jobs'] if v['id']==jid]
        assert (j['run_id'],j['head_sha'],j['run_attempt'],j['name'],j['status'],j['conclusion'])==(
            RUN,HEAD,r['run_attempt'],f'solve ({flop})','completed','success')
        assert STEPS<={v['name'] for v in j['steps'] if (v['status'],v['conclusion'])==('completed','success')}
        job=fields(j,'id run_id head_sha run_attempt name status conclusion')
        job['steps']=[fields(s,'number name status conclusion') for s in j['steps']]
        a,=[v for v in api['artifacts'] if v['id']==aid]
        assert (a['name'],a['digest'],a['expired'])==('B722-R264-'+flop,'sha256:'+digest,False)
        artifact=fields(a,'id name digest size_in_bytes created_at expires_at expired')
        artifact['workflow_run']=fields(a['workflow_run'],'id head_sha head_branch repository_id head_repository_id')
        assert artifact['workflow_run']==dict(id=RUN,head_sha=HEAD,head_branch=BRANCH,repository_id=1438346845,head_repository_id=1438346845)
        out['jobs'].append(job)
        out['artifacts'].append(artifact)
    return out


def verify_worker(folder,archive,pin,flop,solver):
    aid,jid,digest=pin
    assert sha(archive)==digest
    paths=unpack_original(archive,folder)
    raw=(folder/'proof.json').read_bytes()
    d=json.loads(raw)
    assert (d['schema'],d['source_run'],d['source_head'],d['source_worker_blob'],d['rank'],d['model_id'],d['line'],d['actor'],d['flop'])==(
        'NL2_HU_B722_BB3_R264_EXPANDED_RIVER_TREE_V1',RUN,HEAD,BLOB,264,worker.TARGET,worker.LINE,0,flop)
    assert paths==set(d['native_files'])|{'proof.json'}
    expected={'flop/job.json','flop/result.json','rendered-routes.json','proof.json'}
    for t in d['turns']:
        for suffix,present in (('gto',bool(t['gto'])),('exp_oop',t['actor_locked'])):
            if present:expected.update(t['turn']+'-'+suffix+'/'+n for n in ('job.json','result.json'))
    assert paths==expected and d['native_files']['rendered-routes.json']==d['route_sha256']
    assert all(sha((folder/p).read_bytes())==s for p,s in d['native_files'].items())
    worker.run(SimpleNamespace(solver=solver,flop=flop,output=folder,run=RUN,head=HEAD,driver=None,preflight=False))
    assert (folder/'proof.json').read_bytes()==raw
    assert all(sha((folder/p).read_bytes())==s for p,s in d['native_files'].items())
    assert d['selected'] is None and d['positive_distinct_flops']==0
    root=read(folder/'flop/result.json')
    turns=[]
    for t in d['turns']:
        turn=t['turn']
        assert not t['shared']
        record=dict(turn=turn,root_gate_compatible_mid_hands=t['parent_gate']['compatible_rendered_mid_hands'],
            root_weighted_checks_by_seat=t['parent_gate']['root_weighted_check_hands_by_seat'],actor_locked=t['actor_locked'])
        turns.append(record)
        if not t['actor_locked']:
            assert flop==worker.NEW and not t['gto'] and not t['nl2'] and record['root_weighted_checks_by_seat'][0]==0
            continue
        assert flop in worker.OLD and len(t['gto'])==len(t['nl2'])==12
        assert all(n['displayed_check_hands'] for n in t['gto'].values())
        assert all(not n['displayed_check_hands'] for n in t['nl2'].values())
        job=read(folder/(turn+'-exp_oop')/'job.json')
        sub=read(folder/(turn+'-exp_oop')/'result.json')
        assert job['hero']==0 and job['locks'] and sub['info']['lock_stats']
        assert (sub['pot'],sub['stack'])==(2050,9000)
        sub.update(line0='x x',turn=turn,rivers=t['parent_gate']['preregistered_rivers'])
        masks=game_reach(root,sub)[0]
        nodes={n['board']:n for n in sub['nodes'] if (n['line'],n['player'])==(worker.LINE,0)}
        assert nodes.keys()==t['nl2'].keys()
        named=[]
        for public,node in sorted(nodes.items()):
            o=proof(root,sub,node,masks)
            assert o==t['nl2'][public]['reach'] and (node['pot'],node['bets'])==(2050,[0,0])
            m=o['b50']
            if flop=='Js7s4d':assert o['strict_legal_combos']==o['compatible_hole_card_pairs']==0 and m is None
            else:assert o['compatible_hole_card_pairs']>=o['strict_legal_combos']>0 and m is not None and not m['candidate']
            named.append(dict(public_board=public,strict_hero_combos=o['strict_legal_combos'],
                compatible_hole_card_pairs=o['compatible_hole_card_pairs'],medium_assessed=m is not None,
                halfpot_eligible_combos=m['eligible'] if m else None,nonpolarized_candidate=m['candidate'] if m else None))
        measured=t['measured_lock_application']
        assert any(n>0 for p,n in measured['driver_tree_nodes'].items() if p in measured['marginal_targets'])
        record.update(gto_displayed_check_nodes=12,nl2_displayed_check_nodes=0,named_actor_locked_rivers=named,
            gto_job_sha256=t['gto_job_sha256'],gto_result_sha256=t['gto_result_sha256'],
            nl2_job_sha256=t['nl2_job_sha256'],nl2_result_sha256=t['nl2_result_sha256'],
            observed_pool_patterns_with_applied_nodes={p:n for p,n in measured['driver_tree_nodes'].items()
                if n>0 and p in measured['marginal_targets']})
    return dict(flop=flop,source_artifact=aid,source_job=jid,archive_sha256=digest,original_proof_sha256=sha(raw),
        root_origin=d['root_origin'],flop_bet_menu=d['flop_bet_menu'],turn_menu=d['turn_menu'],river_menu=d['river_menu'],
        named_positive_flops=0,turns=turns)


def main(args):
    assert sys.version_info[:2]==(3,11)
    assert subprocess.check_output(['git','hash-object',WORKER],text=True).strip()==BLOB
    auth=authenticate(read(args.receipts))
    stage=args.output.resolve()
    assert not stage.exists() and Path('data').resolve() not in (stage,*stage.parents)
    evidence=stage/'solver_evidence';evidence.mkdir(parents=True)
    workers=[]
    with TemporaryDirectory(prefix='b726-originals-') as tmp:
        for flop,pin in PINS.items():
            aid,jid,digest=pin
            name='NL2_B722_R264_'+flop.upper()+'.zip'
            path=args.archives/f'{aid}.zip'
            archive=(path if path.is_file() else args.archives/name).read_bytes()
            folder=Path(tmp)/flop;folder.mkdir()
            workers.append(dict(archive=name,**verify_worker(folder,archive,pin,flop,args.solver)))
            (evidence/name).write_bytes(archive)
    nodes=[p for w in workers for t in w['turns'] for p in t.get('named_actor_locked_rivers',[])]
    joint=[n for n in nodes if n['strict_hero_combos']>0]
    assert len(nodes)==len({r['public_board'] for r in nodes})==24
    assert len(joint)==sum(n['medium_assessed'] for n in nodes)==12 and not any(n['nonpolarized_candidate'] for n in nodes)
    summary=dict(schema='NL2_HU_B726_RANK264_MEASURED_LOCKED_RIVER_NEGATIVES_V1',rank=264,model_id=worker.TARGET,
        source_run=RUN,source_head=HEAD,workers=workers,positive_distinct_flops=0,source_flops=3,
        original_flop_roots_reused=2,new_flop_roots=1,actor_locked_turn_subgames=2,actor_locked_public_boards=len(nodes),
        zero_joint_locked_public_boards=12,positive_joint_locked_public_boards=len(joint),halfpot_assessed_public_boards=12,
        nonpolarized_candidates=0,cert_eligible_ranks=[],publisher_native_solves_repeated=0)
    (stage/'nl2_hu_b726_summary.json').write_bytes(json_bytes(summary))
    (stage/'nl2_hu_b726_source_receipts.json').write_bytes(json_bytes(auth))
    print(json.dumps({k:v for k,v in summary.items() if k!='workers'}))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--archives',type=Path,default=Path('data/solver_evidence'))
    cli.add_argument('--receipts',type=Path,default=Path('data/nl2_hu_b726_source_receipts.json'))
    for key in ('solver','output'):cli.add_argument('--'+key,type=Path,required=True)
    main(cli.parse_args())
