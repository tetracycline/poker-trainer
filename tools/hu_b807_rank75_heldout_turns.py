"""B807: four held-out rank75 chance turns, no repeated native flop solve.

Keep the exact B766 reconstruction and native gates. Exclude every rank/suit
orbit tested by B758 or B766. Only advance real new GTO/locked turn evidence.
"""
import argparse
import json
from pathlib import Path
import hu_b766_rank75_chance_turns as parent
from hu_b467_river_source_gate import json_bytes

WORKER='tools/hu_b807_rank75_heldout_turns.py'
PARENT_BLOB='2624730b49abd405db6aa82b2f87c5e8bf728c64'
PRIOR_RESULT_BLOB='aa38e566cbcbffb5a6da35a8a898aebaa9f37846'
TURNS=('4c','5c','4d','5d')

def run(a):
    assert parent.checked.blob(parent.__file__)==PARENT_BLOB
    assert parent.checked.blob('data/nl2_hu_b772_results.json')==PRIOR_RESULT_BLOB
    old=parent.TURNS
    assert old==('2d','7d','9h','Ac')
    orbit=lambda t:(t[0],t[1]=='d')
    assert len({orbit(t) for t in (*old,*parent.ORIGINAL_TURNS,*TURNS)})==12
    parent.TURNS=TURNS
    try:
        parent.run(a)
    finally:
        parent.TURNS=old
    if a.preflight:return
    path=a.output/'proof.json'
    proof=json.loads(path.read_bytes())
    assert proof['source_worker_blob']==PARENT_BLOB
    assert [r['turn'] for r in proof['turns']]==list(TURNS[:len(proof['turns'])])
    locked=[r for r in proof['turns'] if 'exp_ip' in r]
    assert all(r['measured_lock_application'] for r in locked)
    proof.update(schema='NL2_B807_R75_HELDOUT_CONDITIONAL_TURNS_V1',
                 source_worker_blob=parent.checked.blob(WORKER),
                 original_algorithm_worker_blob=PARENT_BLOB,
                 prior_result_blob=PRIOR_RESULT_BLOB,
                 new_flop_solve_invocations=0,
                 previously_tested_turns=list(parent.ORIGINAL_TURNS)+list(old),
                 preregistered_turns=list(TURNS),
                 locked_public_boards=len(locked))
    path.write_bytes(json_bytes(proof))

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--solver',type=Path,required=True)
    cli.add_argument('--rust-source',type=Path)
    cli.add_argument('--evidence',type=Path,default=Path('data/solver_evidence'))
    cli.add_argument('--output',type=Path,required=True)
    cli.add_argument('--driver',type=Path)
    cli.add_argument('--preflight',action='store_true')
    run(cli.parse_args())
