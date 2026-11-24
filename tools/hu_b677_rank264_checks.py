"""Solve three new BB three-bet checked-down middle-pair river sources.

The historical A-high rank264 example and KQ-high rank150 example are not
playable in the current trainer. Neither is counted toward these new sources.
"""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys

from hu_b463_rank45_gate import RUST,SOLVER
from hu_b467_river_source_gate import EVIDENCE,compact,json_bytes,sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL,proof
from hu_b568_caller_rivers import hand_cell
from hu_b637_rank57 import solve
from hu_b645_rank195 import STUDY,original_template
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted,cardkey,game_reach
from hu_trainer_route_gate import compatible

MODEL='ln-3bp-3b_r_model-rlw959'
LINE='x x/x x/'
CASES={'Jh7c3d':['2s','4h','5d'],'Ts6h2d':['3c','4s','5h'],'9d5c3h':['2s','4d','6c']}
DECK=[r+s for r in '23456789TJQKA' for s in 'cdhs']


def decisions(root,sub,turn,rivers,route):
    sub.update(line0='x x',turn=turn,rivers=rivers)
    masks=game_reach(root,sub)[0]
    nodes=[n for n in sub['nodes'] if (n['line'],n['player'])==(LINE,0)]
    assert {n['board'][-2:] for n in nodes}==set(rivers)
    results={}
    for node in nodes:
        assert (node['pot'],node['bets'])==(2050,[0,0])
        row=proof(root,sub,node,masks)
        bits=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
        check=1<<node['acts'].index('x')
        hands=[]
        for hole,allowed in zip(sub['hands'][0],bits,strict=True):
            if not allowed&check:continue
            hand=''.join(cardkey(hole))
            if all(hand_cell(hand,node['board'][:size])[0] in route[street]
                   for street,size in [('flop',6),('turn',8),('river',10)]):hands.append(hand)
        if hands:results[node['board']]=(set(hands),row['b50'])
    return results


def run(args):
    solver=args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    if args.driver:
        assert args.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline,ranges
    raw_pool=(solver/'inputs/pool_stats.json').read_bytes();assert sha(raw_pool)==POOL
    pool=json.loads(raw_pool)['NL2']
    route=json.loads(subprocess.check_output(['node','tools/hu_b677_rank264_routes.cjs']))
    registry=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())
    model=registry['records'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'])==(264,'BB3_BTN')
    assert abs(9000/2050/model['assumed_model_node_spr']-1)<=.05
    contract=json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][MODEL]
    raw=(EVIDENCE/STUDY.template).read_bytes();assert sha(raw)==STUDY.template_sha
    template=original_template(raw)
    flop=args.flop
    job=dict(template['root_job'],flop=flop,out='result.json',target_pct=.45,iters=2500,
        extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',t],street=False,raw=True) for t in CASES[flop]])
    assert (job['oop'],job['ip'])==tuple(ranges.to_str(v)for v in ranges.ranges('BB3_BTN','gto'))
    assert (job['pot'],job['stack'],job['flop_oop'],job['flop_ip'])==(2050,9000,'33%,50%,75%','33%,50%,75%')
    root=solve(args.output/'flop',job,args.driver)
    assert (root['flop'],root['pot'],root['stack'])==(flop,2050,9000)
    assert not root['info'].get('lock_stats') and 0<=root['info']['gto_expl_pct']<=.5
    opener,=[n for n in root['nodes']if n['line']=='']
    response,=[n for n in root['nodes']if n['line']=='x']
    assert (opener['player'],response['player'])==(0,1)
    own=accepted(opener,root['hands'],'x');opponent=accepted(response,root['hands'],'x')
    tested=[]
    manifest=dict(template['manifest'],spot='BB3_BTN',pot_family='3BP',locks=[])
    for turn in CASES[flop]:
        parent,=[n for n in root['nodes']if n['line']=='x x/' and n['board'].endswith(turn)]
        assert (parent['pot'],parent['bets'])==(2050,[0,0])
        public=parent['board'];cards={public[i:i+2]for i in range(0,8,2)}
        eligible=[h for h in own if turn not in h and hand_cell(''.join(h),public[:6])[0]in route['flop']
            and hand_cell(''.join(h),public)[0]in route['turn'] and any(turn not in v and set(h).isdisjoint(v)for v in opponent)]
        rivers=[r for r in DECK if r not in cards and any(r not in h and hand_cell(''.join(h),public+r)[0]in route['river']for h in eligible)]
        record=dict(turn=turn,eligible_turn_hands=len(eligible),legal_rivers=len(rivers),paired_policies=False,checks=[])
        tested.append(record)
        if not rivers:continue
        original=dict(template['subgame_job'],flop=flop,turn=turn,out='result.json',pot=2050,stack=9000,
            line0=['x','x','/'],root_no_bet=False,turn_oop='33%,50%,75%',turn_ip='33%,50%,75%',
            river_oop='50%,75%,100%,a',river_ip='50%,75%,100%,a',target_pct=.4,iters=2200,
            extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',r],street=True)for r in rivers])
        for seat,key in enumerate(('oop_w','ip_w')):
            original[key]=[[h,w]for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True)if w>1e-4]
        gto=solve(args.output/(turn+'-gto'),original,args.driver)
        assert (gto['flop'],gto['pot'],gto['stack'])==(flop,2050,9000)
        assert not gto['info'].get('lock_stats') and 0<=gto['info']['gto_expl_pct']<=.5
        before=decisions(root,gto,turn,rivers,route)
        if not before:continue
        locked_job,rules=prepare_job(dict(source=dict(version='gto',root=root,manifest=manifest),job=original),'exp_oop',pool,pipeline)
        locked_job['out']='result.json'
        locked=solve(args.output/(turn+'-exp_oop'),locked_job,args.driver)
        assert (locked['flop'],locked['pot'],locked['stack'])==(flop,2050,9000)
        assert 0<=locked['info']['gto_expl_pct']<=.5 and 0<=locked['info']['hero_gap_pct']<=.5
        audit_patterns(locked,locked_job,dict(manifest,locks=rules),pool,0)
        after=decisions(root,locked,turn,rivers,route)
        record['paired_policies']=True
        for board in sorted(before.keys()&after.keys()):
            common=sorted(before[board][0]&after[board][0])
            if common:
                assert compatible(contract,dict(public_board=board,actual_exact_action_line=LINE,acting_seat=0))
                record['checks'].append(dict(board=board,hands=common,gto_b50=before[board][1],locked_b50=after[board][1]))
        if record['checks']:break
    result=dict(rank=264,model_id=MODEL,flop=flop,line=LINE,root_sha256=sha(compact(root)),
        actual_river_pot_bb=20.5,actual_river_effective_stack_bb=90,turns=tested)
    (args.output/'proof.json').write_bytes(json_bytes(result))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for name in ('solver','output'):cli.add_argument('--'+name,type=Path,required=True)
    cli.add_argument('--flop',choices=CASES,required=True)
    cli.add_argument('--driver',type=Path)
    run(cli.parse_args())
