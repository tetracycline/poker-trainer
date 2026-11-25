"""B832: two distinct, untested low-flop SB3_BTN J7s front-door draws.
Preflight checks exact rendered positions, sizing, actor and both ranges.
Only original CFR solves and jointly reachable GTO/NL2 turns may be evidence.
Never update certification from a proposed board or a zero-reach source.
"""
import argparse
import json
from pathlib import Path
import hu_b789_rank230_seven_draws as parent
from hu_b467_river_source_gate import json_bytes
from hu_b580_rank27_rivers import suit_isomorphism_class

WORKER = 'tools/hu_b832_rank230_eight_low.py'
PARENT_BLOB = '84f0186a2b0d96ab7f10ccf81fb7818b0a0db5ae'
CASES = {
    '8s7h2s': ('7sJs', ['4c', '5d']),
    '8s7h5s': ('7sJs', ['3d', '4c']),
}

def run(a):
    assert parent.base.blob(parent.WORKER) == PARENT_BLOB
    old_worker, old_cases, old_flops = parent.WORKER, parent.CASES, parent.OLD
    historical = (*old_flops, *old_cases,
        'Ts9h7c', '8s7s6d', '9h7h5h', 'Th7h5c',
        '8s7h6s', '9s7h5s', '9s7h4s', '8s7h4s',
        'Ts7h4s', 'Ts7h5s', '9s7h3s', '8s7h3s',
        'Ts7h2s', '9s7h2s', '9s7h6s', 'Ts7h3s')
    assert len({suit_isomorphism_class(f) for f in CASES}) == len(CASES)
    assert not ({suit_isomorphism_class(f) for f in CASES} &
                {suit_isomorphism_class(f) for f in historical})
    try:
        parent.WORKER, parent.CASES, parent.OLD = WORKER, CASES, historical
        parent.run(a)
    finally:
        parent.WORKER, parent.CASES, parent.OLD = old_worker, old_cases, old_flops
    if a.preflight or a.root_only:
        return
    path = a.output / 'proof.json'
    proof = json.loads(path.read_bytes())
    assert proof['origin']['root_solve_invocations'] == 1
    assert proof['source_worker_blob'] == parent.base.blob(WORKER)
    assert proof['preregistered_turns'] == CASES[a.flop][1]
    assert proof['positive_distinct_flops'] in (0, 1)
    assert len({t['turn'] for t in proof['turns']}) == len(proof['turns'])
    proof.update(schema='NL2_B832_R230_EIGHT_LOW_ORIGINAL_V1',
                 original_algorithm_worker_blob=PARENT_BLOB,
                 reused_native_flop_solve=False,
                 count_as_cert_only_after_independent_two_seat_replay=False)
    path.write_bytes(json_bytes(proof))

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for k in ('solver','output'):
        p.add_argument('--'+k, type=Path, required=True)
    p.add_argument('--flop', choices=CASES, required=True)
    p.add_argument('--driver', type=Path)
    p.add_argument('--root-only', action='store_true')
    p.add_argument('--preflight', action='store_true')
    run(p.parse_args())
