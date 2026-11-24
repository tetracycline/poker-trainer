"""Solve the original Ts9h7c checked branch, using only its own two-seat reach and policies."""
import argparse
import json
from pathlib import Path

import hu_b789_rank230_seven_draws as parent
from hu_b467_river_source_gate import json_bytes
from hu_b580_rank27_rivers import suit_isomorphism_class

base,native=parent.base,parent.native
FLOP='Ts9h7c'
HERO_BY_TURN={'6s':'7sJs','5s':'7sJs','6h':'7hJh','5h':'7hJh'}
VILLAIN='3c3d'
NAME='tools/hu_b799_rank230_rainbow.py'
PARENT_BLOB='84f0186a2b0d96ab7f10ccf81fb7818b0a0db5ae'
PREVIOUS_FLOPS=(*parent.OLD,*parent.CASES)


def preflight(flop,route,ranges,pipeline):
    assert flop==FLOP and len({flop[i] for i in (1,3,5)})==3
    assert suit_isomorphism_class(flop) not in {suit_isomorphism_class(f) for f in PREVIOUS_FLOPS}
    oop,ip=ranges.ranges('SB3_BTN','gto')
    assert oop[ranges.NAMES.index('J7s')]==.41 and ip[ranges.NAMES.index('33')]==.41
    job=pipeline.make_job('SB3_BTN','gto',flop,'result.json',iters=2200,target=.4,compress=True)
    job.update(flop_oop='33%',flop_ip='33%',extract=[dict(prefix=[],street=True)]+[
        dict(prefix=['x','x',turn],street=False,raw=True) for turn in HERO_BY_TURN])
    assert (job['pot'],job['stack'],job['rake_rate'],job['rake_cap'])==(2100,9000,.05,1000)
    assert (job['oop'],job['ip'])==(ranges.to_str(oop),ranges.to_str(ip)) and not job.get('locks')
    examples={}
    for turn,hero in HERO_BY_TURN.items():
        assert hero[1]==hero[3]==turn[1] and len(native.public_cards(flop+turn+hero+VILLAIN))==8
        legal=[]
        for river in native.DECK:
            board=flop+turn+river
            if len(native.public_cards(board+hero+VILLAIN))!=9:continue
            if all(route[s].get(native.hand_cell(hero,board[:n])[0])=='過' for s,n in (('flop',6),('turn',8),('river',10))):
                legal.append(river)
        assert len(legal)==10 and '2c' in legal
        examples[turn]=dict(physical_sb=hero,physical_btn=VILLAIN,preflop_weights=[.41,.41],static_legal_rivers=legal)
    return job,examples


def run(args):
    assert base.blob(parent.WORKER)==PARENT_BLOB
    original_worker,original_cases,original_preflight=parent.WORKER,parent.CASES,parent.preflight
    try:
        parent.WORKER=NAME
        parent.CASES={FLOP:('7sJs',list(HERO_BY_TURN))}
        parent.preflight=preflight
        parent.run(args)
    finally:
        parent.WORKER,parent.CASES,parent.preflight=original_worker,original_cases,original_preflight
    if args.preflight or args.root_only:return
    out=args.output;file=out/'proof.json';d=json.loads(file.read_bytes());root=json.loads((out/'flop/result.json').read_bytes())
    route=json.loads((out/'rendered-routes.json').read_bytes())['230']
    assert d['origin']['flop']==FLOP and d['source_worker_blob']==base.blob(NAME)
    assert d['preregistered_turns']==list(HERO_BY_TURN) and d['origin']['root_solve_invocations']==1
    for r in d['turns']:
        turn=r['turn'];hero=HERO_BY_TURN[turn];edge=native.parent(root,turn)
        heroes,foes=base.root_hands(root,turn,route,edge)
        assert sorted(''.join(h) for h in heroes)==r['root_gate']['compatible_hero_hands']
        r['physical_sb_example']=hero;r['physical_btn_example']=VILLAIN
        r['physical_J7s_at_checked_boundary']=native.cardkey(hero) in heroes
        r['physical_33_at_checked_boundary']=native.cardkey(VILLAIN) in foes
        r['named_root_pair_joint']=r['physical_J7s_at_checked_boundary'] and r['physical_33_at_checked_boundary']
        if not r['root_gate']['compatible_hero_hands']:assert not r['policies'] and not r['preregistered_rivers']
        if r['common']:assert r['policies']['exp_oop']['measured_lock_application']
    d.update(schema='NL2_B799_R230_NEW_RAINBOW_ORIGINAL_V1',original_algorithm_worker_blob=PARENT_BLOB,
             source_flop_native_solves=1,prior_flop_inputs_used=False)
    file.write_bytes(json_bytes(d))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--flop',choices=[FLOP],default=FLOP);p.add_argument('--driver',type=Path)
    p.add_argument('--root-only',action='store_true');p.add_argument('--preflight',action='store_true')
    run(p.parse_args())
