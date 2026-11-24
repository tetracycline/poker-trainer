"""Three native CO/BB flops: independent rank92/93/94 turn-lead river gates.

Solve each flop root once and each eligible turn once per policy. Only river
nodes selected from the original root/UI before any turn solve are inspected.
A joint-reach zero or a GTO/NL2 UI disagreement never certifies a board.
"""
import argparse
import base64
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b568_caller_rivers import hand_cell
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b637_rank57 import solve
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, game_reach

CASES={
    '9d7h4c':['2d','5s','7s'],
    '8s6d2c':['3h','4d','6h'],
    '7c5d3h':['2s','6h','5s'],
}
MODELS={92:('ln-bb-r_model-1t7cwh6',33,1826,9112,4.818),
        93:('ln-bb-r_model-d919qu',50,2200,8925,3.932),
        94:('ln-bb-r_model-lf823j',75,2750,8650,3.045)}
WITNESSES={
    '9d7h4c':{92:('Tc9c','2d','3c'),93:('Jc9c','2d','3c'),94:('Jc9c','7s','2c')},
    '8s6d2c':{92:('Tc8c','3h','4c'),93:('Jc8c','3h','4c'),94:('Jc8c','6h','2d')},
    '7c5d3h':{92:('Td7d','2s','4c'),93:('Jd7d','2s','4c'),94:('Jd7d','5s','2c')},
}
SPOT='CO_BB';FLOP_LINE='x b50 c';ROOT_MENU='33%,50%,75%'
DECK=[r+s for r in '23456789TJQKA' for s in 'cdhs']
ACTION={'過':'x','下注 ⅓':'b33','下注 ½':'b50','下注 ¾':'b75'}
PROFILE=dict(oop='BB',ip='CO',oopc=[('COopen>BB','call')],ipc=[('COrfi','open')],pot=5.5,stack=97.5,pfr='ip',kind='SRP')


def cards(public):
    assert len(public)%2==0
    return {public[i:i+2] for i in range(0,len(public),2)}


def range_class(hand):
    a,b=sorted((hand[0],hand[2]),key='23456789TJQKA'.index,reverse=True)
    return a+b+('' if a==b else 's' if hand[1]==hand[3] else 'o')


def root_job(flop,pipeline):
    job=pipeline.make_job(SPOT,'gto',flop,'result.json',iters=2300,target=.45,compress=True)
    job.update(flop_oop=ROOT_MENU,flop_ip=ROOT_MENU,extract=[dict(prefix=[],street=True)]+[
        dict(prefix=['x','b50','c',t],street=False,raw=True) for t in CASES[flop]])
    return job


def static(flop,routes,pipeline,ranges):
    assert len({suit_isomorphism_class(f) for f in CASES})==len(CASES)==3
    assert ranges.SPOTS[SPOT]==PROFILE
    job=root_job(flop,pipeline)
    assert (job['pot'],job['stack'],job['rake_rate'],job['rake_cap'])==(550,9750,.05,1000)
    ws=ranges.ranges(SPOT,'gto')
    assert (job['oop'],job['ip'])==tuple(ranges.to_str(w) for w in ws)
    assert not job.get('locks') and job.get('hero') is None
    weights=[dict(zip(ranges.NAMES,w,strict=True)) for w in ws]
    assert all(weights[0][p]==0 for p in ('99','TT','JJ','QQ'))
    witness={}
    for rank,(mid,pct,pot,stack,spr) in MODELS.items():
        c=routes[str(rank)];line=FLOP_LINE+'/b'+str(pct)+' c/'
        assert (c['id'],c['rank'],c['spot'],c['actor'],c['source'],c['line'],c['pct'],c['root_pot'],c['root_stack'],
            c['turn_pot'],c['turn_stack'],c['river_pot'],c['river_stack'],c['spr'])==(
                mid,rank,SPOT,0,'ln-bb-t_model-cge9jz',line,pct,550,9750,1100,9475,pot,stack,spr)
        assert abs(stack/pot/spr-1)<=.05
        hero,turn,river=WITNESSES[flop][rank];villain='AcKh';public=flop+turn+river
        assert turn in CASES[flop] and len(cards(public+hero+villain))==9
        assert weights[0][range_class(hero)]==weights[1][range_class(villain)]==1
        cells=[hand_cell(hero,public[:n]) for n in (6,8,10)];route=c['routes']
        assert [x[1] for x in cells]==(['TPW']*3 if rank==92 else ['TPG']*3)
        assert all(x[0] in route[street] for x,street in zip(cells,('flop','turn','river'),strict=True))
        assert route['flop'][cells[0][0]]=='跟' and ACTION[route['turn'][cells[1][0]]]=='b'+str(pct)
        assert ACTION[route['river'][cells[2][0]]]=={92:'x',93:'b50',94:'b75'}[rank]
        witness[str(rank)]=dict(hero=hero,villain=villain,turn=turn,river=river,cells=cells,
            pinned_preflop_weights=[1.,1.],not_a_native_policy_witness=True)
    return job,witness


def boundary(root,turn):
    n,=[n for n in root['nodes'] if n['line']==FLOP_LINE+'/' and n['board'].endswith(turn)]
    assert (n['player'],n['pot'],n['bets'])==(0,1100,[275,275])
    assert len(n['board'])==8 and len(cards(n['board']))==4
    assert cards(n['board'][:6])==cards(root['flop']) and n['board'][6:]==turn
    return n


def gate(root,turn,routes):
    branch={}
    for line,seat,pot,bets in [('',0,550,[0,0]),('x',1,550,[0,0]),('x b50',0,825,[0,275])]:
        node,=[n for n in root['nodes'] if n['line']==line]
        assert (node['player'],node['pot'],node['bets'])==(seat,pot,bets)
        assert len(node['board'])==6 and cards(node['board'])==cards(root['flop'])
        branch[line]=node
    n=boundary(root,turn);public=n['board'];dead=cards(public)
    bbx=accepted(branch[''],root['hands'],'x');ipbet=accepted(branch['x'],root['hands'],'b50')
    bbc=accepted(branch['x b50'],root['hands'],'c')
    weighted=[{cardkey(h) for h,w in zip(root['hands'][s],n['wr'][s],strict=True)
               if w>1e-4 and dead.isdisjoint(cardkey(h))} for s in (0,1)]
    heroes=bbx&bbc&weighted[0];villains=ipbet&weighted[1]
    def blocker_counter(vs):return Counter(c for v in vs for c in v)
    def opponent_count(h,vs,counts):return len(vs)-counts[h[0]]-counts[h[1]]+int(h in vs)
    blockers=blocker_counter(villains)
    deals={h:opponent_count(h,villains,blockers) for h in heroes}
    joint=[h for h in sorted(heroes) if deals[h]>0]
    stats=dict(bb_check_accepted=len(bbx),bb_call_accepted=len(bbc),co_b50_accepted=len(ipbet),
        bb_check_call_intersection=len(bbx&bbc),hero_compatible_combos=len(joint),
        compatible_hole_card_pairs=sum(deals.values()),public_board=public,by_rank={})
    cache={h:tuple(hand_cell(''.join(h),public[:end])[0] for end in (6,8)) for h in joint}
    opponents_by_river={r:{v for v in villains if r not in v} for r in DECK if r not in dead}
    counts_by_river={r:blocker_counter(vs) for r,vs in opponents_by_river.items()}
    selected={}
    for rank in MODELS:
        route=routes[str(rank)]['routes']
        matches=[h for h in joint if cache[h][0] in route['flop'] and cache[h][1] in route['turn']]
        eligible=[];legal_counts={}
        for river,vs in opponents_by_river.items():
            count=sum(river not in h and opponent_count(h,vs,counts_by_river[river])>0 and
                hand_cell(''.join(h),public+river)[0] in route['river'] for h in matches)
            if count:eligible.append(river);legal_counts[river]=count
        picks=eligible if len(eligible)<=12 else [eligible[round(i*(len(eligible)-1)/11)] for i in range(12)]
        assert len(picks)==len(set(picks))<=12
        selected[str(rank)]=picks
        stats['by_rank'][str(rank)]=dict(flop_turn_rendered_hero_combos=len(matches),legal_river_count=len(eligible),
            eligible_river_compatible_displayed_hands=legal_counts,preregistered_extract_rivers=picks)
    return stats,selected


def turn_job(root,turn,picks,pipeline):
    parent=boundary(root,turn)
    job=pipeline.make_job(SPOT,'gto',root['flop'],'result.json',iters=2500,target=.4,rank=.4,compress=False)
    job.update(pipeline.SUB);job.update(oop='',ip='',pot=1100,stack=9475,turn=turn,line0=['x','b50','c','/'],
        root_no_bet=False,turn_oop='33%,50%,75%,100%',turn_ip='33%,50%,75%,100%',
        river_oop='50%,75%,100%,a',river_ip='50%,75%,100%,a',extract=[dict(prefix=[],street=True)])
    for rank,(_,pct,*_) in MODELS.items():
        job['extract'].extend(dict(prefix=['b'+str(pct),'c',r],street=False) for r in picks[str(rank)])
    for seat,key in enumerate(('oop_w','ip_w')):
        job[key]=[[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
        assert job[key]
    return job


def decisions(root,sub,turn,picks,routes):
    sub.update(line0=FLOP_LINE,turn=turn,rivers=sorted({r for group in picks.values() for r in group}))
    masks=game_reach(root,sub)[0];out={}
    for rank,(_,pct,pot,stack,_) in MODELS.items():
        c=routes[str(rank)];route=c['routes'];line=c['line'];bet=(1100*pct+50)//100
        nodes=[n for n in sub['nodes'] if (n['line'],n['player'])==(line,0)];rows={}
        assert len(nodes)==len(picks[str(rank)]) and {n['board'][-2:] for n in nodes}==set(picks[str(rank)])
        for node in nodes:
            public=node['board'];assert len(public)==10 and len(cards(public))==5
            assert cards(public[:6])==cards(root['flop']) and public[6:8]==turn
            assert (node['pot'],node['bets'],sub['stack']-max(node['bets']))==(pot,[bet,bet],stack)
            row=proof(root,sub,node,masks);found={}
            action_masks=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
            for i,(hole,mask) in enumerate(zip(sub['hands'][0],action_masks,strict=True)):
                if not mask:continue
                hand=''.join(cardkey(hole));cells=[hand_cell(hand,public[:n]) for n in (6,8,10)]
                if any(cell[0] not in route[street] for cell,street in zip(cells,('flop','turn','river'),strict=True)):continue
                assert ACTION[route['turn'][cells[1][0]]]=='b'+str(pct)
                label=route['river'][cells[-1][0]];action=ACTION[label]
                if action not in node['acts'] or not mask&(1<<node['acts'].index(action)):continue
                weights=[max(0,node['strat'][k*len(action_masks)+i]) for k in range(len(node['acts']))];total=sum(weights);assert total>0
                found[hand]=dict(flop_class=cells[0][1],turn_class=cells[1][1],river_class=cells[2][1],displayed_suggestion=label,
                    action_order=node['acts'],accepted_mask=mask,accepted_actions=[a for j,a in enumerate(node['acts']) if mask&(1<<j)],
                    strategy={a:round(w/total,7) for a,w in zip(node['acts'],weights,strict=True)})
            assert bool(row['b50'] is not None)==bool(row['strict_legal_combos'])
            rows[public]=dict(reach=row,displayed_hands=found)
        out[str(rank)]=rows
    return out


def run(args):
    assert sys.version_info[:2]==(3,11),'Use source Python3.11 for exact expected job bytes'
    solver=args.solver.resolve();py=solver/'postflop/py'
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    assert sha((py/'pipeline.py').read_bytes())==PIPELINE and sha((py/'ranges.py').read_bytes())==RANGES
    if args.driver:
        assert args.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
    sys.path.insert(0,str(py));import pipeline,ranges
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)['NL2'];route_raw=args.routes.read_bytes();routes=json.loads(route_raw)
    assert route_raw==subprocess.check_output(['node','tools/hu_b711_bb_lead_routes.cjs'])
    job,witness=static(args.flop,routes,pipeline,ranges)
    if args.preflight:
        print(json.dumps(dict(flop=args.flop,spot=SPOT,root_job_sha256=sha(compact(job)),static_witnesses=witness,no_native_solve=True)))
        return
    out=args.output;existing=out/'proof.json'
    if args.driver:assert not out.exists() or not any(out.iterdir()),'Do not rerun a completed native source directory'
    else:assert existing.is_file(),'Replay needs the completed original source proof'
    out.mkdir(parents=True,exist_ok=True);(out/'rendered-routes.json').write_bytes(route_raw)
    root=solve(out/'flop',job,args.driver)
    assert (root['flop'],root['pot'],root['stack'])==(args.flop,550,9750)
    assert 0<=root['info']['gto_expl_pct']<=.5 and not root['info'].get('lock_stats')
    report=dict(schema='NL2_B711_CO_BB_MULTI_SIZE_NATIVE_SOURCE_V1',spot=SPOT,actor=0,flop=args.flop,solver=SOLVER,rust=RUST,
        pipeline_sha256=PIPELINE,ranges_sha256=RANGES,pool_sha256=POOL,route_sha256=sha(route_raw),
        source_worker_blob=subprocess.check_output(['git','hash-object','tools/hu_b711_bb_lead_rivers.py'],text=True).strip(),
        source_route_blob=subprocess.check_output(['git','hash-object','tools/hu_b711_bb_lead_routes.cjs'],text=True).strip(),
        root_job_sha256=sha((out/'flop/job.json').read_bytes()),root_source_sha256=sha((out/'flop/result.json').read_bytes()),
        root_gap_pct=root['info']['gto_expl_pct'],preflop_range_source='PINNED_POKER_SOLVER_PREFLOP_CFR',root_menu=ROOT_MENU,
        turn_menu='33%,50%,75%,100%',river_menu='50%,75%,100%,a',flop_line=FLOP_LINE,root_pot=550,root_stack=9750,
        turn_pot=1100,turn_stack=9475,static_range_witnesses=witness,preregistered_flops=list(CASES),preregistered_turns=CASES[args.flop],
        river_selection='UP_TO_12_EVENLY_SPACED_TWO_SEAT_ROOT_AND_THREE_STREET_UI_ELIGIBLE_CARDS_PER_RANK_BEFORE_ANY_TURN_SOLVE',
        lock_scope='FROZEN_GTO_FLOP_TURN_RIVER_PARTIAL_NL2_MARGINALS',no_observed_per_private_hand_NL2_frequencies=True,
        not_a_certification=True,turns=[],selected_by_rank={str(rank):None for rank in MODELS})
    counts={str(r):dict(gto_river_decisions=0,locked_river_decisions=0,positive_joint_locked_decisions=0,
        medium_assessments=0,nonpolarized_candidates=0,shared_displayed_decisions=0) for r in MODELS}
    all_locked=set();all_joint=set();all_medium=set();all_candidates=set();all_common=set();gto_turns=locked_turns=0
    # Freeze all three turn/river selections from the original root, before the first continuation is solved.
    plans={t:gate(root,t,routes) for t in CASES[args.flop]}
    for turn,(diagnostic,picks) in plans.items():
        rec=dict(turn=turn,root_gate=diagnostic,river_extracts_by_rank=picks,gto_solved=False,actor_locked=False,
            gto={},nl2={},common_by_rank={str(rank):[] for rank in MODELS},negative_stage='ZERO_ROOT_JOINT_UI_RIVERS')
        report['turns'].append(rec)
        if not any(picks.values()):continue
        original=turn_job(root,turn,picks,pipeline);gto=solve(out/(turn+'-gto'),original,args.driver)
        assert (gto['flop'],gto['pot'],gto['stack'])==(args.flop,1100,9475)
        assert 0<=gto['info']['gto_expl_pct']<=.5 and not gto['info'].get('lock_stats')
        before=decisions(root,gto,turn,picks,routes);gto_turns+=1
        rec.update(gto_solved=True,gto=before,gto_source_sha256=sha((out/(turn+'-gto')/'result.json').read_bytes()),
            gto_job_sha256=sha((out/(turn+'-gto')/'job.json').read_bytes()),gto_gap_pct=gto['info']['gto_expl_pct'],
            negative_stage='ZERO_GTO_RENDERED_ACTION_WITNESSES')
        for rank,rows in before.items():counts[rank]['gto_river_decisions']+=len(rows)
        if not any(item['displayed_hands'] for rows in before.values() for item in rows.values()):continue
        locked_job,rules=prepare_job(dict(source=dict(version='gto',root=root,manifest=dict(spot=SPOT)),job=original),'exp_oop',pool,pipeline)
        locked_job['out']='result.json';assert locked_job['hero']==0 and locked_job['locks']
        locked=solve(out/(turn+'-exp_oop'),locked_job,args.driver)
        assert (locked['flop'],locked['pot'],locked['stack'])==(args.flop,1100,9475) and locked['hands']==gto['hands']
        assert 0<=locked['info']['gto_expl_pct']<=.5 and 0<=locked['info']['hero_gap_pct']<=.5
        measured=audit_patterns(locked,locked_job,dict(locks=rules),pool,0)
        assert any(n>0 for pat,n in measured['driver_tree_nodes'].items() if pat in measured['marginal_targets'])
        after=decisions(root,locked,turn,picks,routes);locked_turns+=1
        rec.update(actor_locked=True,nl2=after,nl2_source_sha256=sha((out/(turn+'-exp_oop')/'result.json').read_bytes()),
            nl2_job_sha256=sha((out/(turn+'-exp_oop')/'job.json').read_bytes()),
            locked_hero_gap_pct=locked['info']['hero_gap_pct'],measured_lock_application=measured,
            negative_stage='ZERO_COMMON_GTO_NL2_RENDERED_HAND')
        for rank,rows in after.items():
            assert set(rows)==set(before[rank]);ct=counts[rank]
            for public,obs in sorted(rows.items()):
                row=obs['reach'];ct['locked_river_decisions']+=1;all_locked.add(public)
                if row['strict_legal_combos']:
                    assert row['compatible_hole_card_pairs']>=row['strict_legal_combos']>0 and row['b50'] is not None
                    ct['positive_joint_locked_decisions']+=1;ct['medium_assessments']+=1
                    all_joint.add(public);all_medium.add(public)
                    if row['b50']['candidate']:ct['nonpolarized_candidates']+=1;all_candidates.add(public)
                g=before[rank][public]['displayed_hands'];e=obs['displayed_hands'];common=sorted(g.keys()&e.keys())
                if not common:continue
                assert all(g[h]['displayed_suggestion']==e[h]['displayed_suggestion'] for h in common)
                rec['common_by_rank'][rank].append(dict(public_board=public,shared_hands=common))
                if report['selected_by_rank'][rank] is None:report['selected_by_rank'][rank]=dict(turn=turn,public_board=public,shared_hands=common)
                all_common.add(public);ct['shared_displayed_decisions']+=1
        if any(rec['common_by_rank'].values()):rec['negative_stage']=None
    report.update(counts_by_rank=counts,positive_distinct_flops_by_rank={r:int(v is not None) for r,v in report['selected_by_rank'].items()},
        native_flop_solves=1,gto_turn_subgames=gto_turns,actor_locked_turn_subgames=locked_turns,
        locked_river_decisions=sum(c['locked_river_decisions'] for c in counts.values()),unique_locked_public_boards=len(all_locked),
        positive_joint_locked_decisions=sum(c['positive_joint_locked_decisions'] for c in counts.values()),unique_positive_joint_locked_public_boards=len(all_joint),
        medium_assessments=sum(c['medium_assessments'] for c in counts.values()),unique_medium_assessed_public_boards=len(all_medium),
        unique_nonpolarized_candidate_public_boards=len(all_candidates),unique_common_displayed_public_boards=len(all_common))
    report['native_file_sha256']={str(p.relative_to(out)):sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p!=existing}
    existing.write_bytes(json_bytes(report))
    print(json.dumps({k:report[k] for k in ('flop','positive_distinct_flops_by_rank','gto_turn_subgames','actor_locked_turn_subgames',
        'locked_river_decisions','unique_locked_public_boards','medium_assessments','unique_medium_assessed_public_boards','unique_nonpolarized_candidate_public_boards')}))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for field in ('solver','output','routes'):cli.add_argument('--'+field,type=Path,required=True)
    cli.add_argument('--flop',choices=CASES,required=True);cli.add_argument('--driver',type=Path);cli.add_argument('--preflight',action='store_true')
    run(cli.parse_args())
