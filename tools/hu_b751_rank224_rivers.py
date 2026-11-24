"""Export rank224 river decisions without recomputing the original limped flop."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys

import hu_b739_rank108 as native
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b637_rank57 import solve
from hu_b714_rank255_rivers import cards
from hu_b745_rank108 import PINS, SOURCE, receipt
from hu_b751_parent_gate import cell, policies, preflight
from hu_trainer_route_gate import compatible

CASES = {'3s3h2d': ('7c', 5, 806, 29), '4s4h2d': ('7c', 4, 560, 29), '5c5d2h': ('6d', 1, 150, 31)}
MODEL = 'ln-iso-lmp_r_model-1wo1hx8'
LINE = 'b50 r c/b50 c/'


def load(path):
    return json.loads(Path(path).read_bytes())


def originals(flop, pipeline, pool):
    turn = CASES[flop][0]
    batch, = [b for b, s in SOURCE.items() if flop in s[-1]]
    receipt(load('data/nl2_hu_b'+str(742 if batch==739 else 745)+'_source_receipts.json'), batch)
    group = load('data/solver_evidence/reverified/rank108.json')
    pin, = [p for p in group['pins'] if p['flop']==flop]
    aid, digest = PINS[flop]
    assert (pin['archive_sha256'],pin['worker_artifact'],pin['original_job_id'],pin['worker_head'],pin['turn']) == (
        digest,aid,SOURCE[batch][-1][flop],SOURCE[batch][1],turn)
    assert group['model_id']==native.MODEL and group['rank']==108
    found, = [x for x in policies(flop) if x[0]==turn]
    _,root,games,jobs,row=found
    assert (row['source_gto_sha256'],row['source_nl2_sha256'])==(pin['original_GTO_SHA256'],pin['actual_NL2_SHA256'])
    root_boundary, = [n for n in root['nodes'] if n['line']==native.LINE+'/' and n['board'].endswith(turn)]
    assert (root['pot'],root['stack'],root['flop'],root_boundary['pot'],root_boundary['bets'])==(250,9900,flop,1000,[375,375])
    assert not root['info'].get('lock_stats') and 0<=root['info']['gto_expl_pct']<=.5
    gj=jobs['gto']
    assert (gj['pot'],gj['stack'],gj['line0'],gj['root_no_bet'],gj['extract'])==(1000,9525,['b50','r','c','/'],False,[dict(prefix=[],street=True)])
    assert (gj['turn_oop'],gj['turn_ip'],gj['river_oop'],gj['river_ip'])==('33%,50%,75%,100%','33%,50%,75%,100%','50%,100%,a','50%,100%,a')
    for seat,key in enumerate(('oop_w','ip_w')):
        assert gj[key]==[[h,w] for h,w in zip(root['hands'][seat],root_boundary['wr'][seat],strict=True) if w>1e-4]
    lock,rules=native.prepare_job(dict(source=dict(root=root,version='gto',manifest=dict(spot='LMP_CO_BB')),job=gj),'exp_oop',pool,pipeline)
    lock['out']='result.json'
    assert jobs['exp_oop']==lock and lock['hero']==0
    for ver, game in games.items():
        assert len(game['nodes'])==18 and all(n['board']==root_boundary['board'] for n in game['nodes'])
        assert 0<=game['info']['gto_expl_pct']<=.5 and game['hands']==games['gto']['hands']
        if ver=='exp_oop':
            applied=native.audit_patterns(game,lock,dict(locks=rules),pool,0)
            assert applied==row['measured_lock'] and 0<=game['info']['hero_gap_pct']<=.5
        else:assert not game['info'].get('lock_stats')
    return root,games,jobs,rules,pin


def observe(root,game,turn,rivers,allowed,child,contract):
    game.update(line0=native.LINE,turn=turn,rivers=rivers)
    masks=native.game_reach(root,game)[0]
    river_nodes=[n for n in game['nodes'] if len(n['board'])==10]
    assert len(river_nodes)==len(rivers) and {n['board'][-2:] for n in river_nodes}==set(rivers)
    rows={};surviving={}
    for node in river_nodes:
        public=node['board'];rv=public[-2:]
        assert (node['line'],node['player'],node['pot'],node['bets'])==(LINE,0,2000,[500,500])
        assert public[6:8]==turn and cards(public[:6])==cards(root['flop']) and len(cards(public))==5
        assert compatible(contract,dict(public_board=public,actual_exact_action_line=LINE,acting_seat=0))
        p=native.proof(root,game,node,masks)
        mask=base64.b64decode(p['compatible_action_mask_b64'],validate=True)
        by_hand={native.cardkey(h):b for h,b in zip(game['hands'][0],mask,strict=True) if b}
        villains={native.cardkey(h) for h,w in zip(game['hands'][1],node['w'][1],strict=True) if w>1e-4}
        accepted=set()
        for bb,co in allowed[rv]:
            wanted=native.ACTIONS[child['river'][cell(bb,public)]]
            if co in villains and wanted in node['acts'] and by_hand.get(bb,0)&(1<<node['acts'].index(wanted)):
                accepted.add((bb,co))
        surviving[public]=accepted
        rows[public]=dict(reach=p,displayed_hands=sorted({''.join(bb) for bb,co in accepted}),
                          displayed_compatible_pairs=len(accepted))
    return rows,surviving


def run(a):
    assert sys.version_info[:2]==(3,11)
    solver=a.solver.resolve();py=solver/'postflop/py'
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==native.SOLVER
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==native.RUST
    poolraw=(solver/'inputs/pool_stats.json').read_bytes()
    assert (sha(poolraw),sha((py/'pipeline.py').read_bytes()),sha((py/'ranges.py').read_bytes()))==(native.POOL,native.PIPELINE,native.RANGES)
    sys.path.insert(0,str(py));import pipeline
    pool=json.loads(poolraw)['NL2']
    route_raw=a.routes.read_bytes();route=json.loads(route_raw);child=route['children']['224']
    assert (route['parent'],child['model'],child['label'],child['price'])==(native.MODEL,MODEL,'下注 ½',4.513)
    model=load('data/nl2_hu_multiboard_status_current.json')['records'][MODEL]
    contract=load('data/nl2_hu_verified_extensions.json')['trainer_route_contract']['routes'][MODEL]
    assert (model['frequency_rank'],model['source_model_id'],model['solver_profile'])==(224,native.MODEL,'LMP_CO_BB')
    assert (contract['seat'],contract['streets'],contract['priced_model_spr'])==(0,['b50 r c','b50 c',''],4.513)
    assert abs((9025/2000)/model['assumed_model_node_spr']-1)<.001
    root,games,jobs,rules,pin=originals(a.flop,pipeline,pool)
    turn,bb,pairs,eligible=CASES[a.flop]
    allowed,gate=preflight(root,games,turn,route,child)
    assert (gate['bb'],gate['pairs'],gate['rivers'])==(bb,pairs,eligible)
    all_rivers=list(allowed);rivers=[all_rivers[round(i*(len(all_rivers)-1)/11)] for i in range(12)]
    assert len(set(rivers))==12
    gate.update(preregistered_rivers=rivers,example_private_deal={rv:[''.join(v) for v in min(allowed[rv])] for rv in rivers})
    if a.preflight:
        print(json.dumps(dict(flop=a.flop,turn=turn,gate=gate)));return
    out=a.output
    if a.driver:assert not out.exists() or not any(out.iterdir())
    else:assert (out/'proof.json').is_file()
    out.mkdir(parents=True,exist_ok=True)
    (out/'rendered-routes.json').write_bytes(route_raw)
    policies_out={};kept={};common={}
    for ver in ('gto','exp_oop'):
        old=games[ver]
        job=dict(jobs[ver],extract=jobs[ver]['extract']+[dict(prefix=['b50','c',rv],street=False,raw=True) for rv in rivers])
        folder=out/(turn+'-'+ver)
        new=solve(folder,job,a.driver)
        for k in ('flop','pot','stack','hands'):assert old[k]==new[k]
        original_nodes=[n for n in new['nodes'] if len(n['board'])==8]
        assert original_nodes==old['nodes'] and len(original_nodes)==18
        assert 0<=new['info']['gto_expl_pct']<=.5
        measured=None
        if ver=='exp_oop':
            assert 0<=new['info']['hero_gap_pct']<=.5
            measured=native.audit_patterns(new,job,dict(locks=rules),pool,0)
            assert measured==native.audit_patterns(old,jobs[ver],dict(locks=rules),pool,0)
            assert any(v>0 for k,v in measured['driver_tree_nodes'].items() if k in measured['marginal_targets'])
        else:assert not new['info'].get('lock_stats')
        rows,deals=observe(root,new,turn,rivers,allowed,child,contract)
        policies_out[ver]=dict(original_18_node_sha256=sha(compact(original_nodes)),source_sha256=sha((folder/'result.json').read_bytes()),
            job_sha256=sha((folder/'job.json').read_bytes()),boards=rows,measured_lock_application=measured)
        kept[ver]=deals
        if ver=='gto' and not any(deals.values()):break
    if 'exp_oop' in kept:
        for board,op in kept['gto'].items():
            both=op & kept['exp_oop'][board]
            if both:
                common[board]=dict(hands=sorted({''.join(h) for h,v in both}),private_pairs=len(both),
                    example_opponent_per_hand={''.join(h):min(''.join(v) for b,v in both if b==h) for h in sorted({b for b,v in both})})
    obs=[r['reach'] for r in policies_out.get('exp_oop',{}).get('boards',{}).values()]
    counts=dict(native_locked_public_boards=len(obs),joint_halfpot_assessed=sum(r['b50'] is not None for r in obs),
        nonpolarized_candidates=sum(bool((r['b50'] or {}).get('candidate')) for r in obs),positive_distinct_flops=int(bool(common)))
    obj=dict(schema='NL2_B751_RANK224_EXTENDED_ORIGINAL_TURN_EXPORT_V1',rank=224,model_id=MODEL,actor=0,line=LINE,
        flop=a.flop,turn=turn,source_parent=pin,source_root_sha256=sha(compact(root)),route_sha256=sha(route_raw),parent_gate=gate,
        original_flop_solves_repeated=0,solver=native.SOLVER,rust=native.RUST,pool_sha256=native.POOL,pipeline_sha256=native.PIPELINE,
        ranges_sha256=native.RANGES,lock_scope='Observed pool-marginal CO response locks; BB policy and a frozen original GTO flop.',
        no_observed_per_private_hand_frequency=True,policies=policies_out,common=common,selected_public_board=min(common,default=None),**counts)
    (out/'proof.json').write_bytes(json_bytes(obj))
    print(json.dumps(dict(flop=a.flop,turn=turn,matched_original_nodes=18,**counts)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--flop',choices=CASES,required=True)
    for path in ('solver','routes','output'):parser.add_argument('--'+path,type=Path,required=True)
    parser.add_argument('--driver',type=Path)
    parser.add_argument('--preflight',action='store_true')
    run(parser.parse_args())
