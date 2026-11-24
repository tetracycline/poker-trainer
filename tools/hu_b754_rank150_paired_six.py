"""Study two new paired flops with a six of the draw suit on the reachable rank150 river."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from zipfile import ZipFile

import hu_b724_rank150_rivers as original
import hu_b743_rank150_paired as checkpoint
from hu_b724_rank150_rivers import (
    LINE, MODEL, PIPELINE, POOL, RANGES, ROUTE, audit_patterns, cards, compact, compatible, json_bytes, limp,
    observations, prepare_job, sha, static_route, suit_isomorphism_class,
)

WORKER='tools/hu_b754_rank150_paired_six.py'
PRIOR_B743='194b86e1c2b8e7ac3cbd6af2f9daa67781aeb765'
PRIOR_GROUP='2ea284d590a1d381ca71c21c1bc32744a6cc1251'
PRIOR_T_ZIP='0dc1b2bae2ee0abef3f002a74feec0085600d6d8cf77e897253394394ff534b8'
PINS={**original.PINS,'nl2_hu_model.js':'b3dea42d0478e178aefda628e539ec7d95fbe6bd',
    'tools/hu_trainer_route_contract.cjs':'88f702e6d0a645e23b1f9359febfab658ec92f80',
    'tools/hu_b724_rank150_rivers.py':checkpoint.BASE,
    'tools/hu_b743_rank150_paired.py':PRIOR_B743}
CASES={
    '8d8c6d':[('2c','Ad5d','3h'),('2h','Ad4d','3c'),('3c','Ad5d','4h'),('4c','Ad3d','5h')],
    'JcJh6c':[('2h','Ac5c','3d'),('2d','Ac4c','3h'),('3h','Ac5c','4d'),('4h','Ac3c','5d')],
}
HISTORICAL=checkpoint.HISTORICAL|{'9h9d7h','TsTc6s','JdJh7d','7s7h4d','JcJh5d'}


def original_observations(evidence):
    prior=checkpoint.prior(Path('data/solver_evidence'))
    src=evidence/'partial/b747_rank150.json'
    assert limp.git_blob(src)==PRIOR_GROUP
    partial=json.loads(src.read_bytes())
    assert [p['flop'] for p in partial['pins']]==['9c9h6c','TsTc6s']
    target=partial['pins'][1]
    assert (target['public_board'],target['source_run_id'],target['archive_sha256'])==('6sTcTs2c3d',45333267578,PRIOR_T_ZIP)
    assert [p['hand'] for p in target['rendered_decision_hands']]==['4sAs','5sAs']
    for h in target['rendered_decision_hands']:
        assert h['displayed_suggestion']=='過' and all(h[v]['strategy']['x']==1 and h[v]['accepted_actions']==['x'] for v in ('nl2','gto'))
    archive=evidence/'NL2_B743_R150_TSTC6S.zip'
    assert sha(archive.read_bytes())==PRIOR_T_ZIP
    checked={}
    with ZipFile(archive) as z:
        proof=json.loads(z.read('proof.json'))
        assert proof['selected']==dict(turn='2c',public_board='6sTcTs2c3d')
        row,=[t for t in proof['turns'] if t['turn']=='2c']
        assert row['common']['6sTcTs2c3d']==['4sAs','5sAs']
        for version in ('gto','exp_ip'):
            raw=z.read('2c-'+version+'/result.json')
            assert sha(raw)==row['policies'][version]['source_sha256']
            sub=json.loads(raw)
            node,=[n for n in sub['nodes'] if n['line']=='x b33 c/x' and n['player']==1]
            hands=[original.cardkey(h) for h in sub['hands'][1]]
            freq=[]
            for h in ('4sAs','5sAs'):
                index=hands.index(original.cardkey(h))
                weights=[max(0,node['strat'][i*len(hands)+index]) for i in range(len(node['acts']))]
                assert original.cardkey(h) in original.accepted(node,sub['hands'],'x') and sum(weights)>0
                freq.append(round(weights[node['acts'].index('x')]/sum(weights),4))
            checked[version]=freq
    assert checked=={'gto':[.4784,.4325],'exp_ip':[.537,.9826]}
    return dict(previous=prior,paired_tens_group_blob=PRIOR_GROUP,paired_tens_zip_sha256=PRIOR_T_ZIP,
        paired_tens_checked_turn_frequency=checked,original_two_common_river_hands=['4sAs','5sAs'])


def parent_gate(root,turn,route):
    parent,eligible,_,diagnostic=original.parent_gate(root,turn,route)
    options=list(eligible)
    configured,=[f for f in CASES if cards(f)==cards(root['flop'])]
    draw_suit=configured[1]
    low=[r for r in options if r[0] in '34' and r[1]!=draw_suit]
    pair=[r for r in options if r not in low and r[0] in (turn[0],'6') and r[1]!=draw_suit]
    priority=(low+pair)[:12]
    rest=[r for r in options if r not in priority]
    slots=min(len(rest),12-len(priority))
    extra=rest[:1] if slots==1 else [rest[round(i*(len(rest)-1)/(slots-1))] for i in range(slots)]
    rivers=priority+extra
    assert len(rivers)==len(set(rivers))==min(12,len(options))
    return parent,eligible,rivers,dict(diagnostic,preregistered_river_rule='OFF_DRAW_SUIT_THREE_OR_FOUR_THEN_TURN_OR_SIX_PAIR_THEN_SPREAD',
        eligible_priority_rivers=priority)


def replay_or_solve(args,origin,solve):
    assert sys.version_info[:2]==(3,11)
    for p,digest in PINS.items():
        assert limp.git_blob(p)==digest,p
    solver=args.solver.resolve();py=solver/'postflop/py'
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==limp.SOLVER
    assert sha((py/'pipeline.py').read_bytes())==PIPELINE and sha((py/'ranges.py').read_bytes())==RANGES
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(pool_raw)==POOL and sha(Path(limp.TEMPLATE).read_bytes())==limp.TEMPLATE_SHA
    pool=json.loads(pool_raw)['NL2']
    if args.driver:
        assert args.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==limp.RUST
    sys.path.insert(0,str(py))
    import pipeline
    with ZipFile(limp.TEMPLATE) as z:
        root_template,turn_template,m=[json.loads(z.read(s)) for s in ('original-flop.job.json','original-turn.job.json','original-manifest.json')]
    limp.check_limp_source(dict(manifest=m,root_job=root_template,subgame_job=None))
    raw=subprocess.check_output(['node',ROUTE]);route=json.loads(raw)
    assert (route['model_id'],route['line'],route['actor'],route['native_price'])==(MODEL,LINE,1,[416,9817])
    assert abs((9817/416)/route['model_price'][2]-1)<.002
    contract=json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][MODEL]
    assert len({suit_isomorphism_class(f) for f in CASES})==2
    witness=static_route(args.flop,route,m)
    if args.preflight:
        print(json.dumps(dict(flop=args.flop,verified_deals=witness,assumed_preflop_ranges=True)))
        return
    out=args.output
    if args.driver:
        assert not out.exists() or not any(out.iterdir())
    else:
        assert (out/'proof.json').is_file()
    out.mkdir(exist_ok=True,parents=True)
    (out/'rendered-routes.json').write_bytes(raw)
    (out/'original-manifest.json').write_bytes(json_bytes(m))
    sizes='33%,50%,75%,100%'
    turns=[case[0] for case in CASES[args.flop]]
    root_job=dict(root_template,flop=args.flop,flop_oop=sizes,flop_ip=sizes,iters=2400,target_pct=.45,out='result.json',
        extract=[dict(prefix=[],street=True)] + [dict(prefix=prefix+[t],street=False,raw=True)
            for prefix in (['x','b33','c'], ['b33','c']) for t in turns])
    limp.check_limp_source(dict(manifest=m,root_job=root_job,subgame_job=None))
    root=solve(out/'flop',root_job,args.driver)
    assert cards(root['flop'])==cards(args.flop) and (root['pot'],root['stack'])==(250,9900)
    assert 0<=root['info']['gto_expl_pct']<=.5 and not root['info'].get('lock_stats')
    rank80_boundaries={}
    for turn in turns:
        boundary,=[n for n in root['nodes'] if n['line']=='b33 c/' and n['board'].endswith(turn)]
        assert cards(boundary['board'][:6])==cards(args.flop)
        assert (boundary['player'],boundary['pot'],boundary['bets'])==(0,416,[83,83])
        assert len(boundary['wr'])==2 and all(len(w)==len(h) for w,h in zip(boundary['wr'],root['hands'],strict=True))
        rank80_boundaries[turn]=sha(compact(boundary))
    report=dict(schema='NL2_B754_R150_PAIRED_SIX_SOURCE_V1',selection_origin=origin,original_flop_roots_per_worker=1,extra_flop_native_solves_in_continuation=0,rank=150,model_id=MODEL,
        actor=1,line=LINE,flop=args.flop,solver=limp.SOLVER,rust=limp.RUST,source_algorithm_blobs=PINS,
        source_worker_blob=limp.git_blob(WORKER),base_worker_blob=checkpoint.BASE,checkpoint_worker_blob=PRIOR_B743,template_archive_sha256=limp.TEMPLATE_SHA,
        route_sha256=sha(raw),pool_sha256=POOL,root_sha256=sha((out/'flop/result.json').read_bytes()),
        root_job_sha256=sha((out/'flop/job.json').read_bytes()),original_flop_bet_size_menu=sizes,
        root_price=[250,9900],turn_river_price=[416,9817],model_price=route['model_price'],
        actual_spr=round(9817/416,6),preflop_scope='PINNED_EXPLICIT_169_CLASS_ASSUMPTION',
        assumed_preflop_ranges=True,lock_scope='FROZEN_GTO_FLOP_WITH_MEASURED_PARTIAL_TURN_RIVER_NL2_MARGINALS',
        no_observed_per_private_hand_frequency=True,static_range_witnesses=witness,additional_original_b33_call_boundaries=rank80_boundaries,preregistered_flops=list(CASES),
        preregistered_turns=turns,turns=[],selected=None)
    for turn in turns:
        parent,eligible,rivers,diagnostic=parent_gate(root,turn,route)
        t=dict(turn=turn,root_gate=diagnostic,preregistered_rivers=rivers,policies={},common={})
        report['turns'].append(t)
        if not rivers:
            t['negative_reason']='ZERO_TWO_SEAT_FLOP_AND_THREE_STREET_UI_INTERSECTION'
            continue
        job=dict(turn_template,flop=args.flop,turn=turn,line0=['x','b33','c','/'],root_no_bet=False,
            flop_oop=sizes,flop_ip=sizes,turn_oop=sizes,turn_ip=sizes,river_oop='50%,75%,100%,a',river_ip='50%,75%,100%,a',
            pot=416,stack=9817,oop='',ip='',iters=2200,rank_pct=.45,target_pct=.45,compress=False,out='result.json',
            extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',r],street=True) for r in rivers])
        for i,key in enumerate(('oop_w','ip_w')):
            job[key]=[[h,w] for h,w in zip(root['hands'][i],parent['wr'][i],strict=True) if w>1e-4]
        assert job['oop_w'] and job['ip_w'] and (job['rake_rate'],job['rake_cap'])==(.05,1000)
        for version in ('gto','exp_ip'):
            if version=='gto':
                target,rules=job,[]
            else:
                target,rules=prepare_job(dict(source=dict(root=root,version='gto',manifest=m),job=job),'exp_ip',pool,pipeline)
                target['out']='result.json'
                assert target['hero']==1 and target['locks']
            local=out/(turn+'-'+version);game=solve(local,target,args.driver)
            assert cards(game['flop'])==cards(args.flop) and (game['pot'],game['stack'])==(416,9817)
            assert 0<=game['info']['gto_expl_pct']<=.5
            applied=None
            if version=='exp_ip':
                assert 0<=game['info']['hero_gap_pct']<=.5 and game['hands']==gto_hands
                applied=audit_patterns(game,target,dict(m,locks=rules),pool,1)
                assert any(n>0 for p,n in applied['driver_tree_nodes'].items() if p in applied['marginal_targets'])
            else:
                assert not game['info'].get('lock_stats')
                gto_hands=game['hands']
            boards=observations(root,game,turn,rivers,eligible,route)
            t['policies'][version]=dict(source_sha256=sha((local/'result.json').read_bytes()),
                job_sha256=sha((local/'job.json').read_bytes()),gto_gap_pct=game['info']['gto_expl_pct'],
                hero_gap_pct=game['info'].get('hero_gap_pct'),measured_lock_application=applied,boards=boards)
            if version=='gto' and not any(v['hands'] for v in boards.values()):
                t['negative_reason']='NO_GTO_RENDERED_RIVER_CHECK'
                break
        if 'exp_ip' in t['policies']:
            g,e=(t['policies'][v]['boards'] for v in ('gto','exp_ip'))
            for public in sorted(g):
                common=sorted(g[public]['hands'].keys() & e[public]['hands'].keys())
                if common:
                    assert compatible(contract,dict(public_board=public,actual_exact_action_line=LINE,acting_seat=1))
                    t['common'][public]=common
            if t['common']:
                report['selected']=dict(turn=turn,public_board=next(iter(t['common'])))
                break
            t['negative_reason']='NO_COMMON_GTO_AND_NL2_RENDERED_RIVER_CHECK'
    report['positive_distinct_flops']=int(report['selected'] is not None)
    report['native_file_sha256']={str(p.relative_to(out)):sha(p.read_bytes()) for p in sorted(out.rglob('*'))
        if p.is_file() and p.name!='proof.json'}
    (out/'proof.json').write_bytes(json_bytes(report))
    locked=[i['reach'] for t in report['turns'] for i in t['policies'].get('exp_ip',{}).get('boards',{}).values()]
    joint=[r for r in locked if r['strict_legal_combos']>0 and r['compatible_hole_card_pairs']>0 and r['b50'] is not None]
    print(json.dumps(dict(flop=args.flop,positive=report['positive_distinct_flops'],actor_locked_joint_boards=len(joint),
        half_pot_assessed=len(joint),nonpolarized_candidates=sum(r['b50']['candidate'] for r in joint))))

def run(args):
    origin=original_observations(args.prior_evidence)
    new={suit_isomorphism_class(f) for f in CASES}
    assert len(new)==2 and new.isdisjoint({suit_isomorphism_class(f) for f in HISTORICAL})
    original.CASES=CASES
    checkpoint.CASES=CASES
    checkpoint.WORKER=WORKER
    if args.checkpoint_only:
        replay_or_solve(SimpleNamespace(**(vars(args)|{'preflight':True})),origin,checkpoint.BASE_SOLVE)
        checkpoint.checkpoint_root(args)
        return
    reader=checkpoint.BASE_SOLVE
    if args.driver and not args.preflight:
        assert args.checkpoint
        reader=checkpoint.use_checkpoint(args.checkpoint)
    replay_or_solve(args,origin,reader)


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','output'):cli.add_argument('--'+k,required=True,type=Path)
    cli.add_argument('--flop',choices=CASES,required=True)
    cli.add_argument('--driver',type=Path)
    cli.add_argument('--checkpoint-only',action='store_true')
    cli.add_argument('--checkpoint',type=Path)
    cli.add_argument('--preflight',action='store_true')
    cli.add_argument('--prior-evidence',type=Path,default=Path('data/solver_evidence'))
    run(cli.parse_args())
