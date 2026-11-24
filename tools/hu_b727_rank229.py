"""Solve missing rank229 rivers for a verified rank82 boundary and two new SB three-bet flops."""
import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b568_caller_rivers import hand_cell
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b637_rank57 import solve
from hu_b676_checked_rivers import CASES as OLD_FLOPS, DECK, LINE, MODELS, public_cards
from hu_b681_rank229_extra import CASES as OTHER_FLOPS
from hu_checked_gto_boundary import load_original, prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, game_reach

SPOT = 'SB3_BTN'
MODEL = MODELS[229]
POT, STACK = 2100, 9000
MENU = '33%,50%,75%,100%'
OLD = 'KsQh4d'
ARTIFACT = 14599605695
PIN = dict(name='nl2-multiboard-B2-SB3_BTN-gto-KsQh4d', run=44666290556,
           head='91aaaf4661b62c114285a57f390fc6750e996471',
           sha256='0b6b5ddff20e0394c250171188d6f08cdb0e3d9194e5bb60ab4986cd9b41ffc9')
CASES = {OLD:['Tc'], 'KdQc5h':['2s','8d','Tc'], 'KhJc4s':['3d','8h','Ts']}


def parent(root, turn):
    n, = [n for n in root['nodes'] if n['line']=='x x/' and n['board'][6:]==turn]
    assert (n['pot'], n['bets'], n['player']) == (POT, [0,0], 0)
    return n


def available_rivers(root, turn, route, previous):
    p = parent(root, turn)
    board = p['board']
    known = public_cards(board)
    ranges = []
    for seat, line in enumerate(('', 'x')):
        node, = [n for n in root['nodes'] if n['line']==line and len(n['board'])==6]
        assert (node['player'],node['pot'],node['bets']) == (seat,POT,[0,0])
        action = accepted(node,root['hands'],'x')
        weighted = {cardkey(h) for h,w in zip(root['hands'][seat],p['wr'][seat],strict=True)
                    if w>1e-4 and known.isdisjoint(cardkey(h))}
        ranges.append(action & weighted)
    if previous:
        for seat,line in enumerate(('x x/', 'x x/x')):
            node, = [n for n in previous['nodes'] if (n['board'],n['line'],n['player'])==(board,line,seat)]
            ranges[seat] &= accepted(node,previous['hands'],'x')
    heroes = [h for h in sorted(ranges[0])
              if all(hand_cell(''.join(h),b)[0] in route[s] for s,b in [('flop',board[:6]),('turn',board)])
              and any(set(h).isdisjoint(v) for v in ranges[1])]
    # An old result with two exported rivers is retained as-is. Extend only the missing river cards.
    used = {n['board'][-2:] for n in previous['nodes'] if n['line']==LINE and n['player']==0} if previous else set()
    legal = [r for r in DECK if r not in known|used and any(r not in h
             and hand_cell(''.join(h),board+r)[0] in route['river']
             and any(r not in v and set(h).isdisjoint(v) for v in ranges[1]) for h in heroes)]
    selected = legal if len(legal)<=16 else [legal[round(i*(len(legal)-1)/15)] for i in range(16)]
    return dict(compatible_hero_hands=[''.join(h) for h in heroes],previous_rivers=sorted(used),
                legal_river_count=len(legal),river_extracts=selected)


def observations(root, sub, turn, rivers, route):
    sub.update(line0='x x',turn=turn,rivers=rivers)
    masks = game_reach(root,sub)[0]
    targets = [n for n in sub['nodes'] if (n['line'],n['player'])==(LINE,0)]
    assert len(targets)==len(rivers) and {n['board'][-2:] for n in targets}==set(rivers)
    out = {}
    for node in targets:
        board = node['board']
        assert (node['pot'],node['bets'],sub['stack']) == (POT,[0,0],STACK)
        reach = proof(root,sub,node,masks)
        bits = base64.b64decode(reach['compatible_action_mask_b64'],validate=True)
        check = 1 << node['acts'].index('x')
        shown = [''.join(cardkey(h)) for h,b in zip(sub['hands'][0],bits,strict=True) if b&check
                 and all(hand_cell(''.join(cardkey(h)),board[:n])[0] in route[s] for n,s in [(6,'flop'),(8,'turn'),(10,'river')])]
        out[board] = dict(reach=reach, displayed_check_hands=sorted(shown))
    return out


def main(a):
    solver=a.solver.resolve()
    assert sys.version_info[:2]==(3,11)
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    native=solver/'postflop/py'
    assert sha((native/'pipeline.py').read_bytes())==PIPELINE and sha((native/'ranges.py').read_bytes())==RANGES
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
    sys.path.insert(0,str(native))
    import pipeline,ranges
    poolraw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(poolraw)==POOL
    pool=json.loads(poolraw)['NL2']
    reg=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (reg['frequency_rank'],reg['solver_profile'],reg['label'])==(229,SPOT,'APPROX') and abs(STACK/POT/reg['assumed_model_node_spr']-1)<.05
    prior=json.loads(Path('data/solver_evidence/partial/rank229.json').read_bytes())
    assert [b['flop'] for b in prior['boards']]==['Kc9d4h'] and prior['pins'][0]['rendered_decision_hands']
    assert len({suit_isomorphism_class(f) for f in [*CASES,*OLD_FLOPS,*OTHER_FLOPS]})==len(CASES)+len(OLD_FLOPS)+len(OTHER_FLOPS)
    raw=subprocess.check_output(['node','tools/hu_b676_checked_routes.cjs'])
    route=json.loads(raw)['229']
    assert route['model']==MODEL and route['river']==route['turn']=={'KQ_high:2':'過','mono:2':'過'}
    flop=a.flop
    old=None
    out=a.output.resolve()
    if flop==OLD:
        original=load_original(a.receipts,ARTIFACT,PIN,SPOT,OLD,'Tc','gto',pot=POT,stack=STACK,pipeline=pipeline,ranges=ranges)
        root=original['source']['root']
        old=original['source']['subgame']
        assert original['identity']['flop_oop_menu']==original['identity']['flop_ip_menu']==MENU
        gate=available_rivers(root,'Tc',route,old)
        assert gate['compatible_hero_hands']==sorted(['9c9h','9c9s']) and gate['previous_rivers']==['3h','4c'] and len(gate['river_extracts'])==16
        origin=original['identity']
    else:
        job=pipeline.make_job(SPOT,'gto',flop,'result.json',iters=2500,target=.45,compress=True)
        job.update(flop_oop=MENU,flop_ip=MENU,extract=[dict(prefix=[],street=True)]+[
            dict(prefix=['x','x',t],street=False,raw=True) for t in CASES[flop]])
        assert (job['pot'],job['stack'],job['rake_rate'],job['rake_cap'])==(POT,STACK,.05,1000)
        assert (job['oop'],job['ip'])==tuple(ranges.to_str(w) for w in ranges.ranges(SPOT,'gto'))
        assert '99:' in job['oop'] and 'AQs:' in job['ip']
        for turn in CASES[flop]:
            board=flop+turn+'6d'
            assert len(public_cards(board+'9c9sAsQs'))==9
            assert all(hand_cell('9c9s',board[:n])[0] in route[s] for n,s in ((6,'flop'),(8,'turn'),(10,'river')))
        root=None
        origin=dict(new_native_flop=True)
    if a.preflight:
        print(json.dumps(dict(flop=flop,source=origin,old_gate=gate if old else None)));return
    out.mkdir(exist_ok=True,parents=True)
    if root is None:root=solve(out/'flop',job,a.driver)
    assert (root['flop'],root['pot'],root['stack'])==(flop,POT,STACK) and not root['info'].get('lock_stats') and 0<=root['info']['gto_expl_pct']<=.5
    (out/'rendered-routes.json').write_bytes(raw)
    turns=[];chosen=None
    for t in CASES[flop]:
        gate=available_rivers(root,t,route,old);cards=gate['river_extracts']
        row=dict(turn=t,gate=gate,gto={},nl2={},common={});turns.append(row)
        if not cards:continue
        jj=pipeline.make_job(SPOT,'gto',flop,'result.json',iters=2400,target=.4,compress=False)
        jj.update(pipeline.SUB)
        jj.update(oop='',ip='',turn=t,pot=POT,stack=STACK,line0=['x','x','/'],root_no_bet=False,
                  turn_oop=MENU,turn_ip=MENU,river_oop=MENU+',a',river_ip=MENU+',a',
                  extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',c],street=True) for c in cards])
        for seat,k in enumerate(('oop_w','ip_w')):
            jj[k]=[[h,w] for h,w in zip(root['hands'][seat],parent(root,t)['wr'][seat],strict=True) if w>1e-4]
        g=solve(out/(t+'-gto'),jj,a.driver)
        assert 0<=g['info']['gto_expl_pct']<=.5 and not g['info'].get('lock_stats')
        row['gto']=observations(root,g,t,cards,route)
        if not any(v['displayed_check_hands'] for v in row['gto'].values()):continue
        source=dict(version='gto',root=root,manifest=dict(spot=SPOT,pot_family='3BP'))
        locked,metadata=prepare_job(dict(source=source,job=jj),'exp_oop',pool,pipeline)
        locked['out']='result.json';assert locked['hero']==0 and locked['locks']
        e=solve(out/(t+'-exp_oop'),locked,a.driver)
        assert e['hands']==g['hands'] and 0<=e['info']['gto_expl_pct']<=.5 and 0<=e['info']['hero_gap_pct']<=.5
        measures=audit_patterns(e,locked,dict(locks=metadata),pool,0)
        assert any(v>0 for k,v in measures['driver_tree_nodes'].items() if k in measures['marginal_targets'])
        row['measured_lock_application']=measures;row['nl2']=observations(root,e,t,cards,route)
        for b,v in sorted(row['gto'].items()):
            hands=sorted(set(v['displayed_check_hands'])&set(row['nl2'][b]['displayed_check_hands']))
            if hands:
                row['common'][b]=hands
                if chosen is None:chosen=dict(flop=flop,turn=t,public_board=b,hands=hands)
    locked_rows=[(b,v['reach']) for t in turns for b,v in t['nl2'].items()]
    assert len(locked_rows)==len({b for b,_ in locked_rows})
    reached=[r for _,r in locked_rows if r['compatible_hole_card_pairs']>=r['strict_legal_combos']>0]
    assert all(r['b50'] is not None for r in reached)
    summary=dict(positive_distinct_flops=int(bool(chosen)),native_locked_public_boards=len(locked_rows),
                 joint_halfpot_assessed=len(reached),nonpolarized_candidates=sum(bool(r['b50']['candidate']) for r in reached))
    files={str(p.relative_to(out)):sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='proof.json'}
    (out/'proof.json').write_bytes(json_bytes(dict(schema='NL2_B727_CHECKED_SB3_R229_V1',rank=229,model=MODEL,spot=SPOT,flop=flop,
        line=LINE,actor=0,source=origin,flop_solves_repeated=0,solver=SOLVER,rust=RUST,pool_sha256=POOL,route_sha256=sha(raw),
        policy_scope='GTO flop with actor OOP turn and river BR to opponent NL2 street marginals',turns=turns,selected=chosen,native_files=files,**summary)))
    print(json.dumps(summary))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ('solver','receipts','output'):cli.add_argument('--'+key,type=Path,required=True)
    cli.add_argument('--flop',choices=CASES,required=True);cli.add_argument('--driver',type=Path);cli.add_argument('--preflight',action='store_true')
    main(cli.parse_args())
