"""B833: genuinely new monotone rank75 QJo gutshot source candidates.
Both original preflop actors, exact b33/c size, and the displayed three-street
route are validated before any native solve. Positive certification requires
subsequent original-artifact replay and a distinct three-flop proof.
"""
import argparse
import json
from pathlib import Path
import hu_b830_rank75_new_monotone as parent
from hu_b467_river_source_gate import json_bytes
from hu_b580_rank27_rivers import suit_isomorphism_class

WORKER='tools/hu_b833_rank75_new_monotone.py'
PARENT_BLOB='6a0da607f95ed6327bf2dec80e3b50093063a13a'
CASES={
    '9d8d2d':['3d','4d','5d'],
    'Td8d6d':['2d','3d','5d'],
}

def run(a):
    assert parent.checked.blob(parent.WORKER)==PARENT_BLOB
    old_worker,old_cases,old_flops=parent.WORKER,parent.CASES,parent.OLD
    prior=set(old_flops)|set(old_cases)
    assert len({suit_isomorphism_class(f) for f in CASES})==len(CASES)
    assert not ({suit_isomorphism_class(f) for f in CASES} &
                {suit_isomorphism_class(f) for f in prior})
    try:
        parent.WORKER,parent.CASES,parent.OLD=WORKER,CASES,prior
        parent.run(a)
    finally:
        parent.WORKER,parent.CASES,parent.OLD=old_worker,old_cases,old_flops
    if a.preflight or a.checkpoint_only:return
    out=a.output/'proof.json'
    proof=json.loads(out.read_bytes())
    assert proof['origin']['worker_blob']==parent.checked.blob(WORKER)
    assert proof['new_flop_solve_invocations']==1
    assert proof['flop']==a.flop and proof['preregistered_turns']==CASES[a.flop]
    assert proof['locked_public_boards']>=0 and proof['joint_halfpot_assessed']>=0
    proof.update(schema='NL2_B833_R75_NEW_MONO_GUTSHOT_V1',
                 original_algorithm_worker_blob=PARENT_BLOB,
                 old_source_reused_as_cert=False,
                 only_exact_public_boards_can_become_cert=True)
    out.write_bytes(json_bytes(proof))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--flop',choices=CASES,required=True)
    p.add_argument('--driver',type=Path);p.add_argument('--checkpoint',type=Path)
    p.add_argument('--checkpoint-only',action='store_true');p.add_argument('--preflight',action='store_true')
    run(p.parse_args())
