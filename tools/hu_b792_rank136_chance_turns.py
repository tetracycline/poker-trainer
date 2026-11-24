"""Continue three verified BTN/BB A-high flop strategies on unmatched weak-draw turns."""
import argparse
import base64
import json
from io import BytesIO
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b568_caller_rivers import hand_cell
from hu_b637_rank57 import solve
from hu_b652_rank136 import MODEL, LINE, SOLVER, RUST, read_route, root_job
from hu_b676_checked_rivers import DECK, public_cards
from hu_b766_rank75_chance_turns import blocked, reconstruct, weight_bytes, DRIVER_SOURCE
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, game_reach

TURNS={'Ad9c6h':('3s','2h'),'Ac8h5d':('Js','2h'),'Ah8d4s':('Qc','Jc')}
SOURCE='data/nl2_hu_b652_rank136_results.json'
SOURCE_HEAD='19b59d0dc6342d7f51019d7796bc1e0b2525306c'
CHILD='x b75 c/'
ROUTE='tools/hu_b652_rank136_routes.cjs'


def original(archive,flop,pipeline,ranges):
    record=json.loads(Path(SOURCE).read_bytes())
    assert (record['run'],record['head'],record['positive_flops'])==(45271606730,SOURCE_HEAD,0)
    pin,=(p for p in record['observations'] if p['flop']==flop)
    assert sha(archive.read_bytes())==pin['artifact_sha256']
    with ZipFile(archive) as outer, ZipFile(BytesIO(outer.read('source.zip'))) as inner:
        raw=inner.read('root.json'); root=json.loads(raw)
        assert sha(raw)==pin['original_root_sha256'] and root.get('flop')==flop
        assert inner.read('root.job.json')==compact(root_job(flop,pipeline))
        job=json.loads(inner.read('root.job.json'))
        assert inner.read('proof.json')==outer.read('proof.json')
        old=json.loads(inner.read('proof.json')); assert old['selected'] is None and old['run']==record['run']
    assert (root['pot'],root['stack'],job['rake_rate'],job['rake_cap'])==(550,9750,.05,1000)
    assert (job['oop'],job['ip'])==tuple(ranges.to_str(w) for w in ranges.ranges('BTN_BB','gto'))
    assert (job['flop_oop'],job['flop_ip'])==('50%','75%') and not job.get('locks')
    assert not root['info'].get('lock_stats') and 0<=root['info']['gto_expl_pct']<=.5
    observed={n['board'][6:]:n for n in root['nodes'] if n['line']==CHILD}
    assert len(observed)==10 and set(observed).isdisjoint(TURNS[flop])
    assert all((n['pot'],n['bets'],n['player'])==(1376,[413,413],0) for n in observed.values())
    masks={t:blocked(root['hands'],t) for t in (*observed,*TURNS[flop])};held={}
    for t,p in observed.items():
        w=reconstruct(root,observed,masks,[k for k in observed if k!=t],t)
        assert all(weight_bytes(a)==weight_bytes(b) for a,b in zip(w,p['wr'],strict=True))
        held[t]=[sha(weight_bytes(v)) for v in w]
    weights={t:reconstruct(root,observed,masks,list(observed),t) for t in TURNS[flop]}
    return root,weights,dict(**pin,source_run=record['run'],head=record['head'],job_sha256=sha(compact(job)),
                             held_out_seat_weight_sha256=held,original_solved_turns=[r['turn'] for r in old['turns']])


def gate(root,turn,weights):
    flop=root['flop'];board=flop+turn
    actions={n['line']:n for n in root['nodes'] if len(n['board'])==6}
    bb=accepted(actions[''],root['hands'],'x') & accepted(actions['x b75'],root['hands'],'c')
    btn=accepted(actions['x'],root['hands'],'b75')
    alive=[{cardkey(h) for h,w in zip(root['hands'][i],weights[i],strict=True) if w>1e-4} for i in (0,1)]
    bb &= alive[0];btn &= alive[1]
    holes=[h for h in sorted(btn) if hand_cell(''.join(h),flop)[0] in ('A_high:0','A_high:3','A_high:4')
           and hand_cell(''.join(h),board)[0]=='A_high:4' and any(set(h).isdisjoint(v) for v in bb)]
    possible={}
    for r in DECK:
        if r in public_cards(board):continue
        wanted=[h for h in holes if r not in h and hand_cell(''.join(h),board+r)[0]=='A_high:4'
                and any(r not in v and set(h).isdisjoint(v) for v in bb)]
        if wanted:possible[r]=[''.join(h) for h in wanted]
    # Favor the rivers retaining the largest original weak-draw sample, then interleave suits by card order.
    selected=sorted(possible,key=lambda r:(-len(possible[r]),DECK.index(r)))[:16]
    assert bb and holes and selected
    return bb,{r:possible[r] for r in selected}


def make_turn(root,t,weights,rivers,pipeline):
    job=pipeline.make_job('BTN_BB','gto',root['flop'],'result.json',iters=2100,target=.45,compress=False)
    job.update(pipeline.SUB)
    job.update(oop='',ip='',turn=t,pot=1376,stack=9337,line0=['x','b75','c','/'],root_no_bet=False,
               extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',r],street=True) for r in rivers])
    for i,key in enumerate(('oop_w','ip_w')):
        job[key]=[[h,w] for h,w in zip(root['hands'][i],weights[i],strict=True) if w>1e-4]
    return job


def observe(root,raw,t,rivers,bb):
    sub=dict(raw,line0='x b75 c',turn=t,rivers=list(rivers))
    masks=game_reach(root,sub)[0];hands=sub['hands']
    check,=(n for n in sub['nodes'] if n['line']==CHILD and n['player']==0)
    assert len(check['acts'])>1 and 'x' in check['acts']
    callers=bb & accepted(check,hands,'x')
    targets={n['board']:n for n in sub['nodes'] if n['line']==LINE and n['player']==1}
    assert {pub[-2:] for pub in targets}==set(rivers)
    checks={n['board']:n for n in sub['nodes'] if n['line']=='x b75 c/x x/' and n['player']==0}
    rows={};deals={}
    for pub,node in targets.items():
        assert (node['pot'],node['bets'])==(1376,[0,0]) and public_cards(pub[:6])==public_cards(root['flop'])
        row=proof(root,sub,node,masks);rows[pub]=row;bit=1<<node['acts'].index('x')
        valid=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
        legal={''.join(cardkey(h)) for h,m in zip(hands[1],valid,strict=True) if m&bit}
        villains=callers & accepted(checks[pub],hands,'x')
        villains&={cardkey(h) for h,w in zip(hands[0],node['w'][0],strict=True) if w>1e-4}
        qualified={}
        for h in sorted(legal & set(rivers[pub[-2:]])):
            occupied=public_cards(pub+h)
            foes=sorted(''.join(v) for v in villains if occupied.isdisjoint(v))
            if foes:qualified[h]=foes
        if qualified:deals[pub]=qualified
    return rows,deals


def run(a):
    assert sys.version_info[:2]==(3,11);solver=a.solver.resolve();n=solver/'postflop/py'
    git=lambda *c:subprocess.check_output(['git',*c],text=True).strip()
    assert git('-C',str(solver),'rev-parse','HEAD')==SOLVER
    assert git('hash-object',str(solver/'postflop/pfdriver/src/main.rs'))==DRIVER_SOURCE
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert git('-C',str(solver/'postflop/postflop-solver'),'rev-parse','HEAD')==RUST
    assert (sha((n/'pipeline.py').read_bytes()),sha((n/'ranges.py').read_bytes()))==(PIPELINE,RANGES)
    sys.path.insert(0,str(n));import pipeline,ranges
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(pool_raw)==POOL;pool=json.loads(pool_raw)['NL2']
    route=subprocess.check_output(['node',ROUTE]);render=json.loads(route)['136']
    assert render==dict(id=MODEL,flop=['A_high:0','A_high:3','A_high:4'],turn=['A_high:4'],river={'A_high:4':'過'})
    model=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'])==(136,'BTN_BB') and abs((9337/1376)/model['assumed_model_node_spr']-1)<.05
    root,weights,origin=original(a.archive,a.flop,pipeline,ranges)
    plans={t:gate(root,t,w) for t,w in weights.items()}
    if a.preflight:
        print(json.dumps({t:dict(btn=len(set(h for hs in rs.values() for h in hs)),bb=len(bb),rivers=len(rs)) for t,(bb,rs) in plans.items()}));return
    out=a.output
    if a.driver:assert not out.exists() or not any(out.iterdir())
    else:assert (out/'proof.json').exists()
    out.mkdir(parents=True,exist_ok=True)
    for name,raw in [('original-b652.zip',a.archive.read_bytes()),('rendered-routes.json',route)]:
        if a.driver:(out/name).write_bytes(raw)
        else:assert (out/name).read_bytes()==raw
    result=dict(rank=136,model_id=MODEL,flop=a.flop,line=LINE,actor=1,origin=origin,frozen_flop_menu=dict(bb='50%',btn='75%'),
                conditional_root_no_bet=False,original_flop_solves_repeated=0,measured_private_hand_frequencies=False,
                solver=SOLVER,rust=RUST,pool_sha256=POOL,route_sha256=sha(route),turns=[],selected=None,
                locked_public_boards=0,joint_halfpot_assessed=0,halfpot_candidates=0)
    for t,(bb,rivers) in plans.items():
        job=make_turn(root,t,weights[t],rivers,pipeline);policies={}
        turn=dict(turn=t,seat_weight_sha256=[sha(weight_bytes(row)) for row in weights[t]],river_gate=rivers,policies={},common={})
        result['turns'].append(turn)
        for mode in ('gto','exp_ip'):
            target=job;lock=None
            if mode=='exp_ip':
                target,rules=prepare_job(dict(source=dict(root=root,version='gto',manifest=dict(spot='BTN_BB')),job=job),mode,pool,pipeline)
                target['out']='result.json';assert target['hero']==1 and target['locks']
            folder=out/(t+'-'+mode);raw=solve(folder,target,a.driver)
            assert (raw['pot'],raw['stack'],raw['flop'])==(1376,9337,a.flop) and 0<=raw['info']['gto_expl_pct']<=.5
            if mode=='gto':assert not raw['info'].get('lock_stats') and not target.get('locks')
            else:
                assert 0<=raw['info']['hero_gap_pct']<=.5
                lock=audit_patterns(raw,target,dict(locks=rules),pool,1)
                assert any(v>0 for k,v in lock['driver_tree_nodes'].items() if k in lock['marginal_targets'])
            rows,deals=observe(root,raw,t,rivers,bb);policies[mode]=deals
            turn['policies'][mode]=dict(job_sha256=sha((folder/'job.json').read_bytes()),source_sha256=sha((folder/'result.json').read_bytes()),
                                        applied_lock=lock,boards=rows,common_deal_candidates=deals)
            if mode=='gto' and not deals:break
            if mode=='exp_ip':
                joint=[r for r in rows.values() if r['compatible_hole_card_pairs']>=r['strict_legal_combos']>0 and r['b50'] is not None]
                result['locked_public_boards']+=len(rows);result['joint_halfpot_assessed']+=len(joint)
                result['halfpot_candidates']+=sum(r['b50']['candidate'] for r in joint)
        for pub,gto in policies['gto'].items():
            locked=policies.get('exp_ip',{}).get(pub,{})
            same={h:sorted(set(v)&set(locked.get(h,[]))) for h,v in gto.items() if set(v)&set(locked.get(h,[]))}
            if same:turn['common'][pub]=same
        if turn['common']:
            pub=min(turn['common']);result['selected']=dict(public_board=pub,turn=t,btn_and_bb=turn['common'][pub]);break
    result['positive_distinct_flops']=int(result['selected'] is not None)
    (out/'proof.json').write_bytes(json_bytes(result))
    print(json.dumps({k:result[k] for k in ('flop','positive_distinct_flops','locked_public_boards','joint_halfpot_assessed','halfpot_candidates')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('archive','solver','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--flop',choices=TURNS,required=True);p.add_argument('--driver',type=Path)
    p.add_argument('--preflight',action='store_true');run(p.parse_args())
