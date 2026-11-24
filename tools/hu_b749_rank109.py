"""Solve six previously unexported 75% turn barrels on three preserved UTG checked-flop roots."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b568_caller_rivers import hand_cell
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b637_rank57 import solve
from hu_b667_rank109_monotone import LINE, MODEL, template_jobs, turn_job
from hu_b676_checked_rivers import public_cards
from hu_b696_turn_call_rivers import parent_candidates
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import cardkey, game_reach
from solve_hu_missing_branches import EXTRA_SPOTS

FLOPS={'8h6h2d':{'Ah':36,'Kh':39},'9c7c4d':{'Ac':36,'Kc':39},'Jh8h3d':{'Kh':20,'Ah':24}}
ARCHIVES={
    "8h6h2d": [
        "704389d80873be559495f96534054d0e708183c52765cd3c36850057a35f9242",
        "7cb7585ca322c9e7930ce2da25e0280d415496b82c9bf392d93a0fd32c79ad13",
        "3f3a635908513fdb3c125081166e62854c41d6333bccc5ff8bf9419479b08c07"
    ],
    "9c7c4d": [
        "05155fa76a4f60c73c302a8dd2be7b69a9c923fe86202ec29ad923134c168bca",
        "cad976ba9a2eb7fca85f95daaf12316c7f98490146e8c8b98cdc0a6673d23735",
        "c99d97bdbd335e6f8ea0e08253e8ed0eceea4fdb2b7b867b2e5fd8870b75b6c6"
    ],
    "Jh8h3d": [
        "7571c87abd7c094b8884644bbc3aee6f1ce5e28229d1b7d7b578be71bb23beab",
        "ef8cc2e1b34cd098cb8cd7ce1962240ab8c420d462a646cac43821e8247a760e",
        "c103c5c86da2bb0f318dc36b941a9057721cd9dc1e0f660311224fd5e20ffff4"
    ]
}
ROUTE='tools/hu_b619_utg_routes.cjs'
EVID=Path('data/solver_evidence')


def original(flop,template,ranges):
    spec,=[x for x in json.loads(Path('data/nl2_hu_b619_utg_inputs.json').read_bytes())['110'] if x['flop']==flop]
    name='NL2_B619_R110_'+flop.upper()+'.zip';path=EVID/name;archive_sha,root_sha,job_sha=ARCHIVES[flop]
    assert sha(path.read_bytes())==archive_sha==spec['archive_sha256']
    with ZipFile(path) as z:
        raw=z.read('root.json');jobraw=z.read('root.job.json');previous=json.loads(z.read('gto.job.json'))
    assert sha(raw)==root_sha and sha(jobraw)==job_sha
    job=json.loads(jobraw);root=json.loads(raw)
    assert job==dict(template['root_job'],flop=flop,out='result.json',flop_oop='50%',flop_ip='50%',
        extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',turn],street=False,raw=True) for turn in spec['root_turns']])
    assert (job['oop'],job['ip'])==tuple(ranges.to_str(w) for w in ranges.ranges('UTG_CO','gto'))
    assert (job['pot'],job['stack'],job['rake_rate'],job['rake_cap'])==(650,9750,.05,1000)
    assert not job.get('locks') and not root['info'].get('lock_stats') and 0<=root['info']['gto_expl_pct']<=.5
    assert previous['turn'] not in FLOPS[flop] and previous['turn_oop']=='50%'
    return root,dict(archive=name,archive_sha256=archive_sha,root_sha256=root_sha,root_job_sha256=job_sha,
        retained_flop_bet_menu='50%',previous_B619_subgame_turn=previous['turn'],previous_B619_subgame_turn_bet_menu=previous['turn_oop'])


def gate(root,turn,route):
    flop,=[n['board'] for n in root['nodes'] if n['line']=='']
    assert public_cards(flop)==public_cards(root['flop'])
    par,=[n for n in root['nodes'] if n['line']=='x x/' and n['board'][6:]==turn]
    assert par['board'][:6]==flop and par['bets']==[0,0] and par['pot']==650 and par['player']==0
    row,selected=parent_candidates(dict(root,flop=flop),turn,dict(pot=650,actor=0,routes=route))
    assert row['compatible_displayed_parent_hands']==FLOPS[root['flop']][turn] and selected
    return par,row,selected


def decision(root,game,turn,cards,route):
    game.update(line0='x x',turn=turn,rivers=cards)
    assert (game['pot'],game['stack'],game['flop'])==(650,9750,root['flop'])
    nodes=[n for n in game['nodes'] if n['line']==LINE]
    assert len(nodes)==len(cards) and {n['board'][8:] for n in nodes}==set(cards)
    masks=game_reach(root,game)[0];out={}
    for n in nodes:
        b=n['board']
        assert n['player']==0 and (n['pot'],n['bets'],game['stack']-max(n['bets']))==(1626,[488,488],9262)
        assert {'x','b50','b75'}<=set(n['acts'])
        row=proof(root,game,n,masks);bits=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
        index=1<<n['acts'].index('b75');shows=[]
        for h,mask in zip(game['hands'][0],bits,strict=True):
            if not mask&index:continue
            if all(hand_cell(h,b[:end])[0] in route[street] for end,street in ((6,'flop'),(8,'turn'),(10,'river'))):
                shows.append(''.join(cardkey(h)))
        out[b]=dict(reach=row,displayed_b75_hands=sorted(shows))
    return out


def run(a):
    solver=a.solver.resolve();flop=a.flop
    assert sys.version_info[:2]==(3,11) and subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    for p,pin in [('postflop/py/pipeline.py',PIPELINE),('postflop/py/ranges.py',RANGES),('inputs/pool_stats.json',POOL)]:
        assert sha((solver/p).read_bytes())==pin
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
    sys.path.insert(0,str(solver/'postflop/py'));import pipeline,ranges
    pipeline.SPOTS.update(EXTRA_SPOTS);ranges.SPOTS.update(EXTRA_SPOTS)
    pool=json.loads((solver/'inputs/pool_stats.json').read_bytes())['NL2']
    raw=subprocess.check_output(['node',ROUTE,'619']);route=json.loads(raw)['109']
    assert route['id']==MODEL and route['turn']==['mono:0'] and route['river']=={'mono:0':'下注 ¾'}
    model=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'],model['assumed_model_node_spr'])==(109,'UTG_CO',5.7)
    assert abs(9262/1626/model['assumed_model_node_spr']-1)<.05 and len({suit_isomorphism_class(f) for f in FLOPS})==3
    template=template_jobs();root,origin=original(flop,template,ranges)
    gates={t:gate(root,t,route) for t in FLOPS[flop]}
    if a.preflight:
        print(json.dumps(dict(flop=flop,previous=origin,turns={t:p[1] for t,p in gates.items()})));return
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);turns=[];selected=None
    def native(path,job):
        folder=out/path;game=solve(folder,job,None if (folder/'result.json').is_file() else a.driver)
        assert 0<=game['info']['gto_expl_pct']<=.5;return game
    for turn,(par,stats,cards) in gates.items():
        job=turn_job(template,root,par,cards)
        job.update(turn_oop='33%,50%,75%,100%',turn_ip='33%,50%,75%,100%',
            extract=[dict(prefix=[],street=True)]+[dict(prefix=['b75','c',r],street=False) for r in cards])
        assert not job['root_no_bet'] and not job.get('locks') and job.get('hero') is None
        g=native(turn+'-gto',job);assert not g['info'].get('lock_stats')
        row=dict(turn=turn,gate=stats,gto=decision(root,g,turn,cards,route),nl2={},common={});turns.append(row)
        if not any(v['displayed_b75_hands'] for v in row['gto'].values()):continue
        ej,rules=prepare_job(dict(source=dict(version='gto',root=root,manifest=dict(spot='UTG_CO')),job=job),'exp_oop',pool,pipeline)
        ej['out']='result.json';assert ej['hero']==0 and ej['locks']
        e=native(turn+'-exp_oop',ej);assert e['hands']==g['hands'] and 0<=e['info']['hero_gap_pct']<=.5
        app=audit_patterns(e,ej,dict(locks=rules),pool,0)
        assert any(v>0 for k,v in app['driver_tree_nodes'].items() if k in app['marginal_targets'])
        row['measured_lock_application']=app;row['nl2']=decision(root,e,turn,cards,route)
        for b,v in sorted(row['nl2'].items()):
            common=sorted(set(v['displayed_b75_hands'])&set(row['gto'][b]['displayed_b75_hands']))
            if common:
                row['common'][b]=common
                if selected is None:selected=dict(flop=flop,turn=turn,public_board=b,hands=common)
    assert len(turns)==2
    (out/'rendered-routes.json').write_bytes(raw)
    files={str(p.relative_to(out)):sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='proof.json'}
    locked=[(b,v['reach']) for t in turns for b,v in t['nl2'].items()];assert len(locked)==len({b for b,v in locked})
    joint=[r for b,r in locked if r['compatible_hole_card_pairs']>=r['strict_legal_combos']>0]
    assert all(r['b50'] is not None for r in joint)
    counts=dict(positive_distinct_flops=int(bool(selected)),native_locked_public_boards=len(locked),joint_halfpot_assessed=len(joint),
        nonpolarized_candidates=sum(r['b50']['candidate'] for r in joint))
    (out/'proof.json').write_bytes(json_bytes(dict(schema='NL2_B749_UTG_MONOTONE_TURN_VALUE_BET_V1',rank=109,model_id=MODEL,
        spot='UTG_CO',actor=0,line=LINE,flop=flop,original=origin,native_flop_solves=0,solver=SOLVER,rust=RUST,pool_sha256=POOL,
        range_sha256=RANGES,route_sha256=sha(raw),turn_bet_chips=488,river_pot=1626,river_stack=9262,model_spr=5.7,
        lock_scope='GTO checked flop with known half-pot-only flop menu. Turn/river opponent NL2 population marginals and provenance-labelled fallbacks.',
        turns=turns,selected=selected,native_files=files,**counts)))
    print(json.dumps(counts))

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ('solver','output'):cli.add_argument('--'+key,type=Path,required=True)
    cli.add_argument('--flop',choices=FLOPS,required=True);cli.add_argument('--driver',type=Path);cli.add_argument('--preflight',action='store_true')
    run(cli.parse_args())
