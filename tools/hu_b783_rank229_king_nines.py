"""Test the two witnessed 96s check-through routes on three independent K9 flops."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import hu_b727_rank229 as base
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b568_caller_rivers import hand_cell
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b676_checked_rivers import DECK, LINE, public_cards
from hu_trainer_route_gate import compatible

CASES = {
    'Ks9d2h': ['8s','7s','8h','7h'],
    'Kc9h7d': ['8c','5c','8d','5d'],
    'Kh9s8d': ['7h','5h','7d','5d'],
}
ROUTE = 'tools/hu_b676_checked_routes.cjs'
PRIOR = [
    ('NL2_B676_SB3_KC9D4H.zip','7220d620cec1b3f43b101bdcb410aaba6867d1cb4918fd7ae8969b03e45abbdf','Kc9d4h','8h','4h9dKc8h3d','6h9h'),
    ('NL2_B780_R229_KD9C5H.zip','ac6df1b860419ff379293362d43081f30f392fce6723e182212c29e252db47d1','Kd9c5h','7d','5h9cKd7d3c','6d9d'),
]
WORKER = 'tools/hu_b783_rank229_king_nines.py'
ALG = {'tools/hu_b676_checked_rivers.py':'aee288ad582bd2ce7f47fb4f1e4c50165d88a23c','tools/hu_b727_rank229.py':'601385f1ead29779ca5bf30f40237f13abba2c43',
       ROUTE:'522ea33d7326c38a7493507cbde96b5df4a6f3f7'}


def blob(path):
    return subprocess.check_output(['git','hash-object',str(path)],text=True).strip()


def read(p):
    return json.loads(p.read_bytes())


def raw_ranges(root,turn):
    parent = base.parent(root,turn)
    assert public_cards(parent['board'][:6]) == public_cards(root['flop']) and parent['board'][6:] == turn
    assert len(parent['wr']) == 2
    return parent,[{base.cardkey(h) for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4}
                  for seat in (0,1)]


def flop_gate(root,turn,hero,route):
    first, = (n for n in root['nodes'] if n['line']=='')
    after, = (n for n in root['nodes'] if n['line']=='x')
    for n,seat in ((first,0),(after,1)):
        assert (n['player'],n['pot'],n['bets']) == (seat,2100,[0,0])
        assert public_cards(n['board'])==public_cards(root['flop'])
    parent,live=raw_ranges(root,turn)
    sb=base.accepted(first,root['hands'],'x');btn=base.accepted(after,root['hands'],'x')
    hero_key=base.cardkey(hero)
    board=parent['board']
    assert len(public_cards(board+hero))==6
    foes={v for v in btn&live[1] if public_cards(board+hero).isdisjoint(v)}
    ui=all(hand_cell(hero,board[:n])[0] in route[k] for n,k in ((6,'flop'),(8,'turn')))
    river_cards = [r for r in DECK if r not in public_cards(board+hero) and route['river'].get(hand_cell(hero,board+r)[0])=='過'
                   and any(r not in v for v in foes)] if hero_key in sb & live[0] and ui else []
    gate=dict(hero=hero,raw_parent_sha256=sha(compact(parent)),flop_sb_check_combos=len(sb),flop_btn_check_combos=len(btn),
              hero_flop_check=hero_key in sb,hero_positive_raw_range=hero_key in live[0],two_street_ui=ui,
              btn_disjoint_positive_checked_hands=sorted(''.join(v) for v in foes),eligible_rivers=river_cards)
    return parent,foes,gate


def outcomes(root,game,turn,rivers,hero,foes,route):
    rows=base.observations(root,game,turn,rivers,route)
    tn,=(n for n in game['nodes'] if n['line']=='x x/x' and n['player']==1)
    assert len(tn['board'])==8 and tn['board'][6:]==turn
    same_foes=foes & base.accepted(tn,game['hands'],'x')
    by_board={}
    for node in game['nodes']:
        if (node['line'],node['player'])!=(LINE,0):continue
        public=node['board'];row=rows[public]
        assert public_cards(public[:6])==public_cards(root['flop']) and public[6:8]==turn
        if hero not in row['displayed_check_hands']:continue
        active={base.cardkey(h) for h,w in zip(game['hands'][1],node['w'][1],strict=True) if w>1e-4}
        compatible_btn=sorted(''.join(h) for h in same_foes&active if public_cards(public+hero).isdisjoint(h))
        if compatible_btn:
            assert row['reach']['strict_legal_combos']>0 and row['reach']['compatible_hole_card_pairs']>0
            by_board[public]=compatible_btn
    return rows,by_board


def check_donors(args,route,ranges):
    root_template=turn_template=None
    prior_evidence=[]
    for name,digest,flop,turn,public,hero in PRIOR:
        path=args.second_archive if name==PRIOR[1][0] and args.second_archive else Path('data/solver_evidence')/name
        assert sha(path.read_bytes())==digest
        with ZipFile(path) as z:
            get=lambda p:json.loads(z.read(p))
            root=get('flop/result.json');rj=get('flop/job.json')
            tj=get(turn+'-gto/job.json');claim=get('proof.json')
            assert root['flop']==flop and (root['pot'],root['stack'])==(2100,9000)
            assert 0<=root['info']['gto_expl_pct']<=.5 and not root['info'].get('lock_stats')
            assert rj['flop_oop']==rj['flop_ip']=='50%'
            assert (rj['oop'],rj['ip'])==tuple(ranges.to_str(w) for w in ranges.ranges('SB3_BTN','gto'))
            assert tj['turn_oop']==tj['turn_ip']=='33%,50%,75%' and tj['river_oop']==tj['river_ip']=='33%,50%,75%,100%,a'
            assert tj['line0']==['x','x','/'] and not tj['root_no_bet']
            rj={k:v for k,v in rj.items() if k not in ('flop','extract')}
            template={k:v for k,v in tj.items() if k not in ('flop','turn','extract','oop_w','ip_w')}
            if root_template is None:root_template,turn_template=rj,template
            else:assert root_template==rj and turn_template==template
            parent,foes,gate=flop_gate(root,turn,hero,route)
            assert public[-2:] in gate['eligible_rivers']
            sets=[]
            for mode in ('gto','exp_oop'):
                game=get(turn+'-'+mode+'/result.json')
                # Restrict this already-solved native game to one returned river decision.
                # The complete original before-river history is retained for strict replay.
                chosen=dict(game,nodes=[n for n in game['nodes'] if len(n['board'])==8 or n['board']==public])
                rows,hands=outcomes(root,chosen,turn,[public[-2:]],hero,foes,route)
                sets.append(set(hands[public]))
            common=sorted(set.intersection(*sets));assert common
            if name==PRIOR[1][0]:assert claim['selected']==dict(turn=turn,public_board=public,sb=hero,btn_hands=common)
            else:assert claim['selected']['229']['board']==public and claim['selected']['229']['hands']==[hero]
        prior_evidence.append(dict(archive=name,sha256=digest,flop=flop,turn=turn,public_board=public,sb=hero,common_btn_hands=common))
    return root_template,turn_template,prior_evidence


def run(a):
    assert sys.version_info[:2]==(3,11) and all(blob(p)==s for p,s in ALG.items())
    solver=a.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==base.SOLVER
    for p,digest in [('postflop/py/pipeline.py',base.PIPELINE),('postflop/py/ranges.py',base.RANGES),('inputs/pool_stats.json',base.POOL)]:
        assert sha((solver/p).read_bytes())==digest
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==base.RUST
    sys.path.insert(0,str(solver/'postflop/py'));import pipeline,ranges
    pool=read(solver/'inputs/pool_stats.json')['NL2']
    route_raw=subprocess.check_output(['node',ROUTE]);route=json.loads(route_raw)['229']
    assert route['model']==base.MODEL and route['turn']==route['river']=={'KQ_high:2':'過','mono:2':'過'}
    model=read(Path('data/nl2_hu_multiboard_status_current.json'))['records'][base.MODEL]
    contract=read(Path('data/nl2_hu_verified_extensions.json'))['trainer_route_contract']['routes'][base.MODEL]
    assert (model['frequency_rank'],model['solver_profile'],contract['seat'],contract['streets'])==(229,'SB3_BTN',0,['x x','x x',''])
    assert abs(9000/2100/model['assumed_model_node_spr']-1)<.001
    old_flops=set(base.OLD_FLOPS)|set(base.OTHER_FLOPS)|set(base.CASES)
    assert len({suit_isomorphism_class(f) for f in CASES})==len(CASES)
    assert not ({suit_isomorphism_class(f) for f in CASES}&{suit_isomorphism_class(f) for f in old_flops})
    root_template,turn_template,donors=check_donors(a,route,ranges)
    flop=a.flop;turns=CASES[flop]
    weights=[dict(zip(ranges.NAMES,ws,strict=True)) for ws in ranges.ranges('SB3_BTN','gto')]
    assert weights[0]['96s']>0 and weights[1]['AQs']>0
    static={}
    for t in turns:
        h='6'+t[1]+'9'+t[1]
        assert len(public_cards(flop+t+h))==6 and t[1] in flop[1::2]
        foes=['A'+s+'Q'+s for s in 'cdhs' if public_cards('A'+s+'Q'+s).isdisjoint(public_cards(flop+t+h))]
        r,bb=next((r,b) for r in DECK for b in foes if r not in public_cards(flop+t+h+b)
                  and all(hand_cell(h,(flop+t+r)[:n])[0] in route[key] for n,key in ((6,'flop'),(8,'turn'),(10,'river'))))
        static[t]=dict(sb=h,btn=bb,river=r,true_source_range_weights=[weights[0]['96s'],weights[1]['AQs']],new_policy_pending=True)
    if a.preflight:
        print(json.dumps(dict(flop=flop,previous=donors,new_full_ui_and_preflop_witnesses=static)));return
    out=a.output.resolve()
    if a.driver:assert not out.exists() or not any(out.iterdir())
    elif not a.checkpoint_only:assert (out/'proof.json').is_file()
    root_job=dict(root_template,flop=flop,extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',t],street=False,raw=True) for t in turns])
    def load_or_solve(folder,job,driver):
        result=base.solve(folder,job,driver)
        assert (folder/'job.json').read_bytes()==compact(job)
        return result
    if a.checkpoint_only:
        assert a.driver
        result=load_or_solve(out/'flop',root_job,a.driver)
    else:
        if a.driver:
            assert a.checkpoint and read(a.checkpoint/'checkpoint.json')['root_job_sha256']==sha(compact(root_job))
            (out/'flop').mkdir(parents=True)
            for k in ('job.json','result.json'):(out/'flop'/k).write_bytes((a.checkpoint/'flop'/k).read_bytes())
        result=load_or_solve(out/'flop',root_job,None)
    assert (result['flop'],result['pot'],result['stack'])==(flop,2100,9000)
    assert not result['info'].get('lock_stats') and 0<=result['info']['gto_expl_pct']<=.5
    assert {n['board'][6:] for n in result['nodes'] if n['line']=='x x/'}==set(turns)
    identity=dict(flop=flop,root_job_sha256=sha(compact(root_job)),root_result_sha256=sha((out/'flop/result.json').read_bytes()),
                  root_nodes_sha256=sha(compact(result['nodes'])),source_worker_blob=blob(__file__))
    if a.checkpoint_only:(out/'checkpoint.json').write_bytes(json_bytes(identity));return
    if a.driver:assert read(a.checkpoint/'checkpoint.json')==identity
    report=dict(schema='NL2_B783_RANK229_NEW_96S_ROOTS_V1',rank=229,model_id=base.MODEL,flop=flop,actor=0,line=LINE,
                spot='SB3_BTN',price=[2100,9000],solver=base.SOLVER,rust=base.RUST,pool_sha256=base.POOL,
                original_flop_source=identity,source_worker_blob=blob(__file__),previous_flop_witnesses=donors,
                new_original_flops=1,original_flop_repeated=0,
                flop_sizes='50% only for both seats, matching the two original check-through games',
                turn_sizes='33%,50%,75%',route_sha256=sha(route_raw),static_witnesses=static,
                turns=[],selected=None,locked_public_boards=0,joint_halfpot_assessed=0,halfpot_candidates=0)
    (out/'rendered-routes.json').write_bytes(route_raw)
    for t in turns:
        hero=static[t]['sb'];parent,foes,gate=flop_gate(result,t,hero,route)
        entry=dict(turn=t,hero=hero,root_gate=gate,policies={},common={});report['turns'].append(entry)
        rivers=gate['eligible_rivers']
        if not rivers:continue
        job=dict(turn_template,flop=flop,turn=t,extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',r],street=True) for r in rivers])
        for i,k in enumerate(('oop_w','ip_w')):job[k]=[[h,w] for h,w in zip(result['hands'][i],parent['wr'][i],strict=True) if w>1e-4]
        found={}
        for mode in ('gto','exp_oop'):
            target=job;applied=None
            if mode=='exp_oop':
                target,rules=base.prepare_job(dict(source=dict(root=result,version='gto',manifest=dict(spot='SB3_BTN')),job=job),mode,pool,pipeline)
                target['out']='result.json'
            folder=out/(t+'-'+mode);game=load_or_solve(folder,target,a.driver)
            assert (game['flop'],game['pot'],game['stack'])==(flop,2100,9000) and 0<=game['info']['gto_expl_pct']<=.5
            if mode=='gto':assert not game['info'].get('lock_stats')
            else:
                assert target['hero']==0 and 0<=game['info']['hero_gap_pct']<=.5
                applied=base.audit_patterns(game,target,dict(locks=rules),pool,0)
                assert any(n>0 for k,n in applied['driver_tree_nodes'].items() if k in applied['marginal_targets'])
            rows,found[mode]=outcomes(result,game,t,rivers,hero,foes,route)
            entry['policies'][mode]=dict(job_sha256=sha(compact(target)),source_sha256=sha((folder/'result.json').read_bytes()),boards=rows,
                                        compatible_btn_by_public_board=found[mode],applied_lock=applied)
            if mode=='gto' and not found[mode]:break
            if mode=='exp_oop':
                stats=[r['reach'] for r in rows.values()]
                joint=[r for r in stats if r['compatible_hole_card_pairs']>=r['strict_legal_combos']>0 and 'b50' in r['source_actions'] and r['b50'] is not None]
                report['locked_public_boards']+=len(stats);report['joint_halfpot_assessed']+=len(joint)
                report['halfpot_candidates']+=sum(r['b50']['candidate'] for r in joint)
        if 'exp_oop' in found:
            for public,btn in found['gto'].items():
                common=sorted(set(btn)&set(found['exp_oop'].get(public,[])))
                if common:
                    assert compatible(contract,dict(public_board=public,actual_exact_action_line=LINE,acting_seat=0))
                    entry['common'][public]=dict(sb=hero,btn_hands=common)
        if entry['common']:
            public=min(entry['common']);report['selected']=dict(turn=t,public_board=public,**entry['common'][public]);break
    report['positive_distinct_flops']=int(report['selected'] is not None)
    report['native_file_sha256']={p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='proof.json'}
    (out/'proof.json').write_bytes(json_bytes(report))
    print(json.dumps({k:report[k] for k in ('flop','selected','locked_public_boards','joint_halfpot_assessed','halfpot_candidates')}))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for n in ('solver','output'):cli.add_argument('--'+n,type=Path,required=True)
    cli.add_argument('--flop',choices=CASES,required=True);cli.add_argument('--second-archive',type=Path)
    cli.add_argument('--preflight',action='store_true');cli.add_argument('--checkpoint-only',action='store_true')
    cli.add_argument('--checkpoint',type=Path);cli.add_argument('--driver',type=Path)
    run(cli.parse_args())
