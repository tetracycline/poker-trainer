"""Test three new two-suited K94/K95 flop roots using the two verified 96s continuations."""
import argparse
import json
from pathlib import Path
import sys

import hu_b783_rank229_king_nines as parent
from hu_b467_river_source_gate import json_bytes,sha

WORKER='tools/hu_b788_rank229_two_suited.py'
BASE_WORKER='tools/hu_b783_rank229_king_nines.py'
BASE_BLOB='0a34b979baecba50757619304f0a724c432b8c87'
CASES={'Kd9h4h':['8d','7d','Td'],'Kd9h5h':['7d','8d','Td'],'Kd9d5h':['7h','8h','Th']}
PREVIOUS_K9FLOPS={
    'Kc9d4h','Kd9c5h','Ks9h3d','Ks9d2h','Kc9h7d','Kh9s8d',
    # These additional K9 boards were studied using other profiles.
    'Kd9d4c','Kd9d4d','Ks9s5s','Ks9h5d',
}
EVIDENCE=Path('data/solver_evidence')


def configuration(flop):
    assert parent.blob(BASE_WORKER)==BASE_BLOB
    current={parent.suit_isomorphism_class(f) for f in CASES}
    prior={parent.suit_isomorphism_class(f) for f in PREVIOUS_K9FLOPS|set(parent.CASES)}
    assert len(current)==len(CASES)==3 and current.isdisjoint(prior)
    one_suit, = (s for s in flop[1::2] if flop[1::2].count(s)==1)
    hero='6'+one_suit+'9'+one_suit
    assert hero in ('6d9d','6h9h') and flop[::2] in ('K94','K95')
    assert len(set(flop[1::2]))==2 and len(set(parent.public_cards(flop+hero)))==5
    assert all(t[1]==one_suit and len(parent.public_cards(flop+hero+t))==6 for t in CASES[flop])
    # Every new root is a different game. Existing complete interpretations remain pinned.
    group_path=EVIDENCE/'partial/b781_rank229.json'
    assert parent.blob(group_path)=='5d2d2fd7009fa3e9c0ef7514510ca87085b706e7'
    group=parent.read(group_path)
    old={b['flop']:b['public_board'] for b in group['boards']}
    assert old=={'Kc9d4h':'4h9dKc8h3d','Kd9c5h':'5h9cKd7d3c'}
    selected_parent = '4h9dKc8h3d' if hero=='6h9h' else '5h9cKd7d3c'
    return dict(flop=flop,hero=hero,prior_board_for_same_physical_sb=selected_parent,
                source_worker_blob=parent.blob(__file__),root_and_turn_algorithm_blob=BASE_BLOB,
                preregistered_turns=CASES[flop],suit_pattern=[flop[1::2].count(s) for s in flop[1::2]],
                original_two_positive_flops=old,restricted_flop_menu='50% both seats',
                preflop_spot='SB3_BTN',native_flop_price=[2100,9000])


def run(args):
    assert sys.version_info[:2]==(3,11)
    config=configuration(args.flop)
    old=parent.CASES
    if args.driver and not args.checkpoint_only and not args.preflight:
        assert parent.read(args.checkpoint/'selection.json')==config
    try:
        parent.CASES=CASES
        parent.run(args)
    finally:
        parent.CASES=old
    if args.preflight:
        print(json.dumps(config));return
    if args.checkpoint_only:
        assert parent.read(args.output/'checkpoint.json')['source_worker_blob']==BASE_BLOB
        (args.output/'selection.json').write_bytes(json_bytes(config));return
    path=args.output/'proof.json';proof=parent.read(path)
    assert proof['source_worker_blob']==BASE_BLOB and proof['original_flop_source']['source_worker_blob']==BASE_BLOB
    assert all(r['sb']==config['hero'] and r['true_source_range_weights'][0]>0 and r['true_source_range_weights'][1]>0
               for r in proof['static_witnesses'].values())
    previous,=(p for p in proof['previous_flop_witnesses'] if p['sb']==config['hero'])
    assert previous['public_board']==config['prior_board_for_same_physical_sb'] and previous['common_btn_hands']
    proof.update(schema='NL2_B788_R229_TWO_SUITED_ORIGINALS_V1',source_worker_blob=config['source_worker_blob'],
                 root_and_turn_algorithm_blob=BASE_BLOB,selection=config,
                 original_flop_root_reused=False,new_original_flop_root=True,
                 checkpoint_source_identity=sha(json_bytes(config)))
    for attempt in proof['turns']:
        if attempt['policies']:
            gate=attempt['root_gate']
            assert gate['hero']==config['hero'] and gate['hero_flop_check'] and gate['hero_positive_raw_range']
            assert gate['two_street_ui'] and gate['btn_disjoint_positive_checked_hands']
    path.write_bytes(json_bytes(proof))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('solver','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--flop',choices=CASES,required=True)
    p.add_argument('--second-archive',type=Path);p.add_argument('--driver',type=Path);p.add_argument('--checkpoint',type=Path)
    p.add_argument('--preflight',action='store_true');p.add_argument('--checkpoint-only',action='store_true')
    run(p.parse_args())
