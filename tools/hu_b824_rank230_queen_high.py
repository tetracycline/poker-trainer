"""B824: two previously untested non-isomorphic SB3_BTN queen-high seven-pair front-door-draw flops.
The pinned rank230 worker first checks the exact rendered J7s route, then
solves a single original per board and tests two registered checked turns.
No registry changes without independent artifact replay and full audit.
"""
import argparse
import json
from pathlib import Path
import hu_b789_rank230_seven_draws as parent
from hu_b467_river_source_gate import json_bytes
from hu_b580_rank27_rivers import suit_isomorphism_class

WORKER='tools/hu_b824_rank230_queen_high.py'
PARENT_BLOB='84f0186a2b0d96ab7f10ccf81fb7818b0a0db5ae'
CASES={'QsTs7h':('7sJs',['4c','5d']),
       'Qs9s7h':('7sJs',['4c','5d'])}

def run(a):
    assert parent.base.blob(parent.WORKER)==PARENT_BLOB
    old_worker,old_cases,old_flops=parent.WORKER,parent.CASES,parent.OLD
    prior=(*old_flops,*old_cases,'Ts9h7c','8s7s6d','9h7h5h','Th7h5c','8s7h6s','9s7h5s','9s7h4s','8s7h4s','Ts7h4s','Ts7h5s','9s7h3s','8s7h3s')
    assert not ({suit_isomorphism_class(f) for f in CASES}&{suit_isomorphism_class(f) for f in prior})
    try:
        parent.WORKER=WORKER
        parent.CASES=CASES
        parent.OLD=prior
        parent.run(a)
    finally:
        parent.WORKER,parent.CASES,parent.OLD=old_worker,old_cases,old_flops
    if a.preflight or a.root_only:return
    file=a.output/'proof.json'
    proof=json.loads(file.read_bytes())
    assert proof['origin']['root_solve_invocations']==1
    assert proof['source_worker_blob']==parent.base.blob(WORKER)
    assert proof['preregistered_turns']==CASES[a.flop][1]
    proof.update(schema='NL2_B824_R230_SEVEN_THREE_ORIGINAL_V1',
                 original_algorithm_worker_blob=PARENT_BLOB,
                 prior_flop_inputs_used=False)
    file.write_bytes(json_bytes(proof))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--flop',choices=CASES,required=True)
    p.add_argument('--driver',type=Path)
    p.add_argument('--root-only',action='store_true')
    p.add_argument('--preflight',action='store_true')
    run(p.parse_args())
