"""B856: two new rainbow mid-high LMP roots; strict same two-seat two-policy evidence, no old solve repeated."""
import argparse
import base64
import json
import itertools
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b481_rank27_limp_rivers import check_limp_source
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b568_caller_rivers import hand_cell
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b637_rank57 import solve
from hu_b676_checked_rivers import public_cards
from hu_b696_turn_call_rivers import parent_candidates
from hu_checked_gto_boundary import load_original, prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, game_reach

MODEL = 'ln-iso-lmp_r_model-asilzt'
SPOT, LINE = 'LMP_CO_BB', 'x x/x b66 c/'
OLD, ARTIFACT = '8s8h3d', 14600026283
PIN = dict(run=44666294821, head='e8f6e7dbce77676bf375a66b86db41742d896cd2',
           name='nl2-multiboard-B3-LMP_CO_BB-gto-8s8h3d',
           sha256='7583287177315c74022553f0b64dc91d39c95a9dee0f84329dd99b22564c273e')
CASES = {'Jh8d6c': ['2s','3s'], 'Th5d2c': ['3s','7s']}
EXCLUDED = (OLD, '7s7h4d', 'JcJh5d')
DECK = [r+s for r in '23456789TJQKA' for s in 'cdhs']


def original(receipts, pipeline, ranges):
    src = load_original(receipts, ARTIFACT, PIN, SPOT, OLD, '5s', 'gto',
                        pot=250, stack=9900, pipeline=pipeline, ranges=ranges)
    with ZipFile(receipts / f'{ARTIFACT}.zip') as z:
        m = json.loads(z.read('evidence/LMP_CO_BB-gto-8s8h3d.json'))
        raw = z.read('solver/postflop/' + m['file_flop'][:-5] + '.job.json')
    assert sha(raw) == src['identity']['root_job_sha256'] == 'bbed120f68c2e295febc4715fc2a8f987bf46d2d2802a7e410809fea66ca7907'
    assert src['identity']['root_sha256'] == 'c5861d2bbcc0361f095b13a8ed3e393785c48ec2a517cee1cafb7c52567ed61c'
    job = json.loads(raw)
    check_limp_source(dict(manifest=m,root_job=job,subgame_job=None))
    assert job['flop_oop'] == job['flop_ip'] == '33%,50%,75%,100%'
    assert src['job']['turn_ip'] == '50%,100%'
    assert all('b66' not in n['acts'] for n in src['source']['subgame']['nodes'] if n['line']=='x x/x')
    return src, job, m


def parent_gate(root, turn, route):
    flop, = [n['board'] for n in root['nodes'] if n['line']=='']
    assert len(flop)==6 and public_cards(flop)==public_cards(root['flop'])
    parent, = [n for n in root['nodes'] if n['line']=='x x/' and n['board'][6:]==turn]
    assert parent['board'][:6]==flop
    # Native flop order is suit-canonical, while the job retains the original order.
    return parent_candidates(dict(root,flop=flop),turn,dict(pot=250,actor=0,routes=route))


def turn_job(template, root, turn, cards):
    parent, = [n for n in root['nodes'] if n['line']=='x x/' and n['board'][6:]==turn]
    assert (parent['pot'],parent['bets'],parent['player'])==(250,[0,0],0)
    job = dict(template,flop=root['flop'],turn=turn,out='result.json',iters=2400,target_pct=.4,rank_pct=.4,
               root_no_bet=False,turn_oop='33%,50%,75%,100%',turn_ip='33%,66%,100%',
               river_oop='50%,75%,100%,a',river_ip='50%,75%,100%,a',river_donk='50%,75%,100%',
               extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','b66','c',r],street=False) for r in cards])
    assert (job['pot'],job['stack'],job['line0'])==(250,9900,['x','x','/'])
    for seat,key in enumerate(('oop_w','ip_w')):
        job[key]=[[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
    assert not job.get('locks') and job.get('hero') is None
    return job


def preflight(template, flop, route):
    # Exact native LMP assumptions (not observed per-private-hand pool data).
    def weights(seat):
        return {k:float(v) for k,v in (x.split(':') for x in template[seat].split(','))}
    def h169(pair):
        a,b=sorted(pair,key=lambda x:'23456789TJQKA'.index(x[0]),reverse=True)
        return a[0]+b[0]+('' if a[0]==b[0] else 's' if a[1]==b[1] else 'o')
    oop,ip=weights('oop'),weights('ip')
    evidence={}
    for turn in CASES[flop]:
        known=public_cards(flop+turn)
        combos=list(itertools.combinations([c for c in DECK if c not in known],2))
        heroes=[h for h in combos if oop.get(h169(h),0)>0 and
                hand_cell(''.join(h),flop)[0] in route['flop'] and
                hand_cell(''.join(h),flop+turn)[0] in route['turn']]
        opponents=[v for v in combos if ip.get(h169(v),0)>0]
        pair=None
        for hero in heroes:
            for river in DECK:
                if river in known or river in hero or hand_cell(''.join(hero),flop+turn+river)[0] not in route['river']:
                    continue
                villain=next((v for v in opponents if river not in v and set(v).isdisjoint(hero)),None)
                if villain:
                    pair=dict(hero=hero,villain=villain,river=river)
                    break
            if pair:break
        evidence[turn]=pair
    return evidence

def same_pair(hero,opp):
    for h in sorted(hero):
        for v in sorted(opp):
            if set(h).isdisjoint(v):return [h,v]
    return None

def observations(root, game, turn, cards, route):
    game.update(line0='x x',turn=turn,rivers=cards)
    assert (game['flop'],game['pot'],game['stack'])==(root['flop'],250,9900)
    facing, = [n for n in game['nodes'] if n['line']=='x x/x b66']
    assert (facing['player'],facing['bets'],facing['pot'])==(0,[0,165],415)
    masks = game_reach(root,game)[0]
    f0,f1=(next(n for n in root['nodes'] if n['line']==line and len(n['board'])==6) for line in ('','x'))
    t0,t1,t2=(next(n for n in game['nodes'] if n['line']==line and len(n['board'])==8) for line in ('x x/','x x/x','x x/x b66'))
    assert (f0['player'],f1['player'],t0['player'],t1['player'],t2['player'])==(0,1,0,1,0)
    assert (t0['pot'],t1['pot'],t2['pot'])==(250,250,415)
    prior=[accepted(f0,root['hands'],'x') & accepted(t0,game['hands'],'x') & accepted(t2,game['hands'],'c'),
           accepted(f1,root['hands'],'x') & accepted(t1,game['hands'],'b66')]
    rows = {}
    for node in game['nodes']:
        if node['line']!=LINE:continue
        board = node['board']
        assert node['player']==0 and node['bets']==[165,165] and node['pot']==580
        assert game['stack']-max(node['bets'])==9735 and {'x','b50'}<=set(node['acts'])
        assert public_cards(board[:6])==public_cards(root['flop']) and board[6:8]==turn
        reach = proof(root,game,node,masks)
        bits = base64.b64decode(reach['compatible_action_mask_b64'],validate=True)
        check = 1 << node['acts'].index('x')
        show = sorted(''.join(cardkey(h)) for h,v in zip(game['hands'][0],bits,strict=True) if v&check
                      and all(hand_cell(h,board[:n])[0] in route[s] for n,s in ((6,'flop'),(8,'turn'),(10,'river'))))
        dead=public_cards(board)
        live=[{cardkey(h) for h,w in zip(game['hands'][seat],node['w'][seat],strict=True)
               if w>1e-4 and dead.isdisjoint(cardkey(h))}&prior[seat] for seat in (0,1)]
        shown={cardkey(h) for h in show}&live[0]&accepted(node,game['hands'],'x')
        rows[board]=dict(reach=reach,displayed_check_hands=sorted(shown),
                         prior_hero=sorted(live[0]),prior_villain=sorted(live[1]))
    assert len(rows)==len(cards) and {b[-2:] for b in rows}==set(cards)
    return rows


def run(a):
    solver=a.solver.resolve()
    assert sys.version_info[:2]==(3,11)
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    for p,pin in [('postflop/py/pipeline.py',PIPELINE),('postflop/py/ranges.py',RANGES),('inputs/pool_stats.json',POOL)]:
        assert sha((solver/p).read_bytes())==pin
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline,ranges
    pool=json.loads((solver/'inputs/pool_stats.json').read_bytes())['NL2']
    raw=subprocess.check_output(['node','tools/hu_b733_rank114_routes.cjs'])
    view=json.loads(raw);route=view['routes'];flop=a.flop
    reg=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (reg['frequency_rank'],reg['solver_profile'],reg['source_model_id'])==(114,SPOT,view['facing'])
    assert view['id']==MODEL and view['turn_pct']==66 and abs(9735/580/view['model_spr']-1)<.05
    assert len({suit_isomorphism_class(f) for f in CASES})==2
    assert not {suit_isomorphism_class(f) for f in CASES}&{suit_isomorphism_class(f) for f in EXCLUDED}
    src,root_template,manifest=original(a.receipts,pipeline,ranges)
    old=src['source']['root']
    observed,_=parent_gate(old,'5s',route)
    assert (observed['compatible_displayed_parent_hands'],observed['legal_river_candidates'])==(144,35)
    static=preflight(root_template,flop,route)
    valid=[t for t in CASES[flop] if static[t]]
    assert valid, 'No legal native-input UI witness; no native solve dispatched'
    if a.preflight:
        print(json.dumps(dict(flop=flop,checked_original=observed,turn_price_chips=165,static=static)));return
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    def native(path,job):
        folder=out/path
        game=solve(folder,job,None if (folder/'result.json').exists() else a.driver)
        assert 0<=game['info']['gto_expl_pct']<=.5
        return game
    job=dict(root_template,flop=flop,out='result.json',iters=2400,target_pct=.45,
             extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',t],street=False,raw=True) for t in valid])
    check_limp_source(dict(manifest=manifest,root_job=job,subgame_job=None))
    root=native('flop',job)
    assert (root['flop'],root['pot'],root['stack'])==(flop,250,9900) and not root['info'].get('lock_stats')
    turns=[];selected=None
    for t in valid:
        stats,cards=parent_gate(root,t,route)
        row=dict(turn=t,gate=stats,gto={},nl2={},common={},common_prior={});turns.append(row)
        if not cards:continue
        job=turn_job(src['job'],root,t,cards)
        g=native(t+'-gto',job)
        assert not g['info'].get('lock_stats')
        row['gto']=observations(root,g,t,cards,route)
        if not any(same_pair(x['displayed_check_hands'],x['prior_villain']) for x in row['gto'].values()):continue
        source=dict(version='gto',root=root,manifest=dict(spot=SPOT,pot_family='LMP'))
        lock,rules=prepare_job(dict(source=source,job=job),'exp_oop',pool,pipeline)
        lock['out']='result.json'
        assert lock['hero']==0 and lock['locks']
        e=native(t+'-exp_oop',lock)
        assert e['hands']==g['hands'] and 0<=e['info']['hero_gap_pct']<=.5
        application=audit_patterns(e,lock,dict(locks=rules),pool,0)
        assert any(v>0 for k,v in application['driver_tree_nodes'].items() if k in application['marginal_targets'])
        row['measured_lock_application']=application;row['nl2']=observations(root,e,t,cards,route)
        for b,after in sorted(row['nl2'].items()):
            before=row['gto'][b]
            opponent=set(before['prior_villain'])&set(after['prior_villain'])
            common=same_pair(set(before['displayed_check_hands'])&set(after['displayed_check_hands']),opponent)
            prior=same_pair(set(before['prior_hero'])&set(after['prior_hero']),opponent)
            if prior:
                assert all(x['reach']['compatible_hole_card_pairs']>0 and x['reach']['b50'] is not None for x in (before,after))
                row['common_prior'][b]=prior
            if common:
                assert prior is not None
                row['common'][b]=common
                if selected is None:selected=dict(flop=flop,turn=t,public_board=b,physical_pair=common)
        if selected:break
    rows=[(b,v['reach']) for t in turns for b,v in t['nl2'].items()]
    assert len(rows)==len({b for b,r in rows})
    reached=[t['nl2'][b]['reach'] for t in turns for b in t['common_prior']]
    counts=dict(positive_distinct_flops=int(bool(selected)),native_locked_public_boards=len(rows),
                joint_halfpot_assessed=len(reached),nonpolarized_candidates=sum(r['b50']['candidate'] for r in reached))
    (out/'rendered-routes.json').write_bytes(raw)
    files={str(p.relative_to(out)):sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='proof.json'}
    (out/'proof.json').write_bytes(json_bytes(dict(schema='NL2_B856_R114_NEW_MIDHIGH_TWO_SEAT_V1',rank=114,model=MODEL,
        spot=SPOT,actor=0,line=LINE,flop=flop,source_template=src['identity'],reused_native_flop=False,static_witnesses=static,
        native_flop_solves_repeated=0,solver=SOLVER,rust=RUST,range_sha256=RANGES,pool_sha256=POOL,route_sha256=sha(raw),
        root_pot=250,root_stack=9900,turn_bet=165,river_pot=580,river_stack=9735,model_spr=view['model_spr'],
        preflop_scope='Explicit assumed LMP 169-class ranges',lock_scope='Frozen GTO flop. CO turn/river street marginals with documented fallbacks, no observed private-combo rates.',
        turn_ip_menu='33%,66%,100%',
        turns=turns,selected=selected,native_files=files,**counts)))
    print(json.dumps(counts))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('solver','receipts','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--flop',required=True,choices=CASES);p.add_argument('--driver',type=Path);p.add_argument('--preflight',action='store_true')
    run(p.parse_args())
