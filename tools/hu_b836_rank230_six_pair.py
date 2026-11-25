"""B836: rank230 alternative positive-weight SB 96s middle-pair front-door draw.
Two distinct untested source flops; original solver only after frozen route preflight.
No automatic CERT publication. Frozen original and both-policy evidence required.
"""
import argparse
import json
from pathlib import Path
import subprocess
import hu_b789_rank230_seven_draws as parent
from hu_b467_river_source_gate import json_bytes,sha
from hu_b580_rank27_rivers import suit_isomorphism_class

WORKER='tools/hu_b836_rank230_six_pair.py'
PARENT_BLOB='84f0186a2b0d96ab7f10ccf81fb7818b0a0db5ae'
native=parent.native
PRIOR,PRIOR_SHA=parent.PRIOR,parent.PRIOR_SHA
CASES={'Ts6h3s':('6s9s',['2d','4c','5d']),
       '8s6h2s':('6s9s',['3d','4c','5d'])}
OLD=(*parent.OLD,*parent.CASES,'Ts9h7c','8s7s6d','9h7h5h','Th7h5c',
     '8s7h6s','9s7h5s','9s7h4s','8s7h4s','Ts7h4s','Ts7h5s','9s7h3s','8s7h3s',
     'Ts7h2s','9s7h2s','9s7h6s','Ts7h3s','8s7h2s','8s7h5s')

def preflight(flop,route,ranges,pipeline):
    hand,turns=parent.CASES[flop];villain='3c3d';suited=hand[1]
    assert hand[1]==hand[3] and hand[0]=='6' and hand[2]=='9'
    assert sum(flop[i]==suited for i in (1,3,5))==2 and any(flop[i]=='6' and flop[i+1]!=suited for i in (0,2,4))
    assert not ({suit_isomorphism_class(f) for f in CASES}&{suit_isomorphism_class(f) for f in OLD})
    assert len({suit_isomorphism_class(f) for f in CASES})==2
    assert sha(Path(PRIOR).read_bytes())==PRIOR_SHA
    group=json.loads(Path(PRIOR).read_bytes())
    assert [(p['flop'],p['rendered_decision_hands'][0]['hand']) for p in group['pins']]==[('Th9h7c','7hJh'),('Ts8s7h','7sJs')]
    oop,ip=ranges.ranges('SB3_BTN','gto')
    assert oop[ranges.NAMES.index('96s')]==.02 and ip[ranges.NAMES.index('33')]==.41
    job=pipeline.make_job('SB3_BTN','gto',flop,'result.json',iters=2200,target=.4,compress=True)
    job.update(flop_oop='33%',flop_ip='33%',extract=[dict(prefix=[],street=True)]+[
        dict(prefix=['x','x',turn],street=False,raw=True) for turn in turns])
    assert (job['pot'],job['stack'],job['rake_rate'],job['rake_cap'])==(2100,9000,.05,1000)
    assert (job['oop'],job['ip'])==(ranges.to_str(oop),ranges.to_str(ip)) and not job.get('locks')
    examples={}
    for turn in turns:
        legal=[]
        for river in native.DECK:
            pub=flop+turn+river
            if len(native.public_cards(pub+hand+villain))!=9:continue
            if all(route[s].get(native.hand_cell(hand,pub[:n])[0])=='過' for s,n in (('flop',6),('turn',8),('river',10))):
                legal.append(river)
        assert legal,(flop,turn)
        examples[turn]=dict(physical_sb=hand,physical_btn=villain,example_river=legal[0],legal_example_rivers=len(legal))
    return job,examples


def run(a):
    assert parent.base.blob(parent.WORKER)==PARENT_BLOB
    assert len({suit_isomorphism_class(f) for f in CASES})==2
    assert not ({suit_isomorphism_class(f) for f in CASES}&{suit_isomorphism_class(f) for f in OLD})
    # Only candidates with a physical, legal UI route for the frozen 96s hand
    # can be selected, deterministically in preregistered order, before native work.
    route=json.loads(subprocess.check_output(['node',parent.base.ROUTE]))['230']
    selected={}
    for flop,(hand,turns) in CASES.items():
        valid=[]
        for turn in turns:
            if any(len(native.public_cards(flop+turn+r+hand+'3c3d'))==9 and
                   all(route[s].get(native.hand_cell(hand,(flop+turn+r)[:n])[0])=='過'
                       for s,n in (('flop',6),('turn',8),('river',10)))
                   for r in native.DECK):
                valid.append(turn)
        selected[flop]=(hand,valid[:2])
    assert selected[a.flop][1],('no physical UI route; not a native job',a.flop)
    saved=parent.WORKER,parent.CASES,parent.OLD,parent.preflight
    try:
        parent.WORKER,parent.CASES,parent.OLD,parent.preflight=WORKER,selected,OLD,preflight
        parent.run(a)
    finally:
        parent.WORKER,parent.CASES,parent.OLD,parent.preflight=saved
    if a.preflight or a.root_only:return
    path=a.output/'proof.json'
    proof=json.loads(path.read_bytes())
    assert proof['origin']['root_solve_invocations']==1
    assert proof['source_worker_blob']==parent.base.blob(WORKER)
    assert proof['preregistered_turns']==selected[a.flop][1]
    for t in proof['turns']:
        t['physical_96s_at_checked_boundary']=t.pop('physical_J7s_at_checked_boundary')
    proof.update(schema='NL2_B836_R230_SIX_PAIR_ORIGINAL_V1',
                 original_algorithm_worker_blob=PARENT_BLOB,
                 preregistered_candidate_turns=CASES[a.flop][1],
                 sb_preflop_96s_weight=.02,
                 independent_two_seat_archive_required=True)
    path.write_bytes(json_bytes(proof))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--flop',choices=CASES,required=True)
    p.add_argument('--driver',type=Path)
    p.add_argument('--root-only',action='store_true')
    p.add_argument('--preflight',action='store_true')
    run(p.parse_args())
