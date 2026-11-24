"""Solve three rank150 third-pot flop branches using the trainer's displayed draw cells."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import hu_b703_rank29_highcards as limp
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b568_caller_rivers import hand_cell
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b637_rank57 import solve
from hu_b714_rank255_rivers import DECK, cards
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, game_reach
from hu_trainer_route_gate import compatible

MODEL='ln-iso-lmp_r_model-4ys53a'
LINE='x b33 c/x x/x'
CASES={
    '8s8h5s': [('2d','2s3s','4c'),('5h','2s3s','2c'),('Th','2s3s','2c'),('6c','2s3s','2c')],
    '9c9h6c': [('2d','2c3c','4d'),('6h','2c3c','2d'),('Ts','2c3c','2d'),('7h','2c3c','2d')],
    'Ts9s5h': [('7d','2s7s','3c'),('8h','2s8s','3c'),('Jc','2sJs','3c'),('9d','2s3s','2c')],
}
ROUTE='tools/hu_b724_rank150_routes.cjs'
PINS={ROUTE:'b8cd61436858474f68c51bf8d5e3425f1ae3894c',
      'tools/hu_b703_rank29_highcards.py':'1adbb4fe4bd2ad36643dd3e79bf5f41cd9580ac8',
      'tools/hu_b714_rank255_rivers.py':'8481a56d5a9ca431bcc69f028a973d5477b886fd',
      'tools/hu_b568_caller_rivers.py':'e69bda7fe46c3dd18a48dee1bb97f965ab2813f7',
      'tools/hu_b637_rank57.py':'86b795adbd8ff4e6e411a70cebf8b3db1efc4ff9',
      'tools/hu_b483_locked_medium.py':'018ac485d3fc115f125c777399d96ce38b0f5f04',
      'tools/hu_sequential_cfr_reach.py':'f26df926c088e5b4117bb911956cbc5031e2458d',
      'tools/hu_checked_gto_boundary.py':'219f46b0a259fa3e71f1225046ab5b12c44c28c6',
      'nl2_hu_model.js':'b4a308a0f65b707f43f41f0b354cec87c08d5af6',
      'nl2.js':'15aee97e53a156fe073c96a120638a8a3679958f',
      'tools/hu_trainer_route_contract.cjs':'3b10524228c357552bb3f1eac88e17f9b2459b32'}


def static_route(flop,route,manifest):
    out=[]
    for turn,hero,river in CASES[flop]:
        board=flop+turn+river
        villain=next(h for h in ('AdAc','KdKh','QhQd') if cards(h).isdisjoint(cards(hero+board)))
        assert len(cards(board+hero+villain))==9
        weights=[manifest['preflop_ranges'][key][limp.range_class(hand)] for key,hand in (('ip_169',hero),('oop_169',villain))]
        assert min(weights)>0
        cls=[hand_cell(hero,board[:n]) for n in (6,8,10)]
        assert cls[0][0] in route['flop'] and cls[1][0] in route['turn'] and route['river'][cls[2][0]]=='過'
        out.append(dict(turn=turn,river=river,hero=hero,villain=villain,classes=cls,preflop_weights=weights))
    return out


def parent_gate(root,turn,route):
    def node(line,seat):
        match,=[n for n in root['nodes'] if (n['line'],n['player'])==(line,seat)]
        return match
    check,bettor,caller=node('',0),node('x',1),node('x b33',0)
    assert (check['pot'],check['bets'],bettor['pot'],caller['bets'],caller['pot'])==(250,[0,0],250,[0,83],333)
    parent,=[n for n in root['nodes'] if n['line']=='x b33 c/' and n['board'].endswith(turn)]
    public=parent['board']
    assert (parent['player'],parent['pot'],parent['bets'])==(0,416,[83,83])
    assert cards(public[:6])==cards(root['flop']) and len(cards(public))==4
    live=[{cardkey(h) for h,w in zip(root['hands'][i],parent['wr'][i],strict=True)
        if w>1e-4 and cards(public).isdisjoint(cardkey(h))} for i in (0,1)]
    x=accepted(check,root['hands'],'x')
    c=accepted(caller,root['hands'],'c')
    b=accepted(bettor,root['hands'],'b33')
    foes=x&c&live[0]
    flop_hands={h for h in b&live[1] if hand_cell(''.join(h),public[:6])[0] in route['flop']}
    heroes={''.join(h) for h in flop_hands if hand_cell(''.join(h),public)[0] in route['turn']
        and any(set(h).isdisjoint(v) for v in foes)}
    eligible={}
    for river in DECK:
        if river in cards(public):
            continue
        kept=[h for h in sorted(heroes) if river not in cards(h) and route['river'].get(hand_cell(h,public+river)[0])=='過'
            and any(cards(public+river+h).isdisjoint(v) for v in foes)]
        if kept:
            eligible[river]=kept
    options=list(eligible)
    rivers=options if len(options)<=12 else [options[round(i*(len(options)-1)/11)] for i in range(12)]
    return parent,eligible,rivers,dict(raw_parent_sha256=sha(compact(parent)),public_board=public,
        oop_check=len(x),oop_call=len(c),ip_b33=len(b),oop_joint_check_call=len(foes),
        flop_displayed_draws=len(flop_hands),two_seat_flop_turn_ui=len(heroes),eligible_rivers=len(eligible))


def observations(root,sub,turn,rivers,eligible,route):
    sub.update(line0='x b33 c',turn=turn,rivers=rivers)
    nodes=[n for n in sub['nodes'] if (n['line'],n['player'])==(LINE,1)]
    assert len(nodes)==len(rivers) and {n['board'][-2:] for n in nodes}==set(rivers)
    masks=game_reach(root,sub)[0];rows={}
    for node in nodes:
        public=node['board']
        assert cards(public[:6])==cards(root['flop']) and public[6:8]==turn and len(cards(public))==5
        assert (node['pot'],node['bets'],sub['stack'])==(416,[0,0],9817)
        row=proof(root,sub,node,masks)
        bits=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
        hands={}
        for hand,mask in zip(sub['hands'][1],bits,strict=True):
            key=''.join(cardkey(hand))
            if not mask & (1<<node['acts'].index('x')) or key not in eligible[public[-2:]]:
                continue
            cells=[hand_cell(hand,public[:n]) for n in (6,8,10)]
            assert cells[0][0] in route['flop'] and cells[1][0] in route['turn'] and route['river'][cells[-1][0]]=='過'
            hands[key]=dict(classes=[c[1] for c in cells],displayed_suggestion='過',
                accepted_actions=[a for i,a in enumerate(node['acts']) if mask&(1<<i)])
        rows[public]=dict(reach=row,hands=hands)
    return rows


def run(args):
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
    assert len({suit_isomorphism_class(f) for f in CASES})==3
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
    report=dict(schema='NL2_B724_R150_THIRD_POT_DRAW_RIVERS_V1',rank=150,model_id=MODEL,
        actor=1,line=LINE,flop=args.flop,solver=limp.SOLVER,rust=limp.RUST,source_algorithm_blobs=PINS,
        source_worker_blob=limp.git_blob('tools/hu_b724_rank150_rivers.py'),template_archive_sha256=limp.TEMPLATE_SHA,
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


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for name in ('solver','output'):
        cli.add_argument('--'+name,type=Path,required=True)
    cli.add_argument('--flop',choices=CASES,required=True)
    cli.add_argument('--driver',type=Path)
    cli.add_argument('--preflight',action='store_true')
    run(cli.parse_args())
