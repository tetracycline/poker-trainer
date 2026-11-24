"""Add three new T-high two-suit SB check-call flops with unchanged B689 source gates."""
import argparse
import hashlib
import json
from pathlib import Path

import hu_b689_rank84 as native
from hu_b467_river_source_gate import json_bytes
from hu_b580_rank27_rivers import suit_isomorphism_class

CASES={
    'Td9d5c':['2h','3s','4c','6h'],
    'Th9h7c':['2s','3d','4c','6s'],
    'Ts8s7h':['2c','3d','4h','6c'],
}
SOURCE_BLOBS={
    'tools/hu_b689_rank84.py':'ab2e677593a0f81e19164f2a97ec768cc97f82fc',
    'tools/hu_b689_rank84_routes.cjs':'c90250c610c3388e854458895296872113554b91',
}
EARLIER_SB_FLOPS=('Qs8h3d','Qh9c4s','Kd7s2h')


def run(args):
    for name,expected in SOURCE_BLOBS.items():
        raw=Path(name).read_bytes()
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==expected
    old_cases=native.CASES
    all_flops=[*EARLIER_SB_FLOPS,*old_cases,*CASES]
    assert len(all_flops)==len({suit_isomorphism_class(flop)for flop in all_flops})
    for flop,turns in CASES.items():
        assert flop[0]=='T'and sorted(flop[1::2].count(suit)for suit in set(flop[1::2]))==[1,2]
        for turn in turns:
            public=flop+turn
            assert len({public[index:index+2]for index in range(0,8,2)})==4
            assert native.tx(public)=='mid_high'
    try:
        native.CASES=CASES
        native.run(args)
    finally:
        native.CASES=old_cases
    path=args.output/'proof.json'
    report=json.loads(path.read_bytes())
    assert report['schema']=='NL2_B689_R84_ORIGINAL_WORKER_V1'
    assert report['root_gate_threshold']=='MAX_FREQUENCY_OR_GE40PCT_AND_GE70PCT_OF_MAX_UNCHANGED'
    report.update(schema='NL2_B697_R84_ORIGINAL_WORKER_V1',source_algorithm_batch=689,new_source_batch=697,
        source_algorithm_blobs=SOURCE_BLOBS,preregistered_new_flops=list(CASES),
        prior_positive_source=dict(flop='Ts9s6h',turn='2c',run_id=45312594665,artifact_id=14883039797),
        original_prior_flop_replayed=False)
    path.write_bytes(json_bytes(report))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ('solver','output','routes'):cli.add_argument('--'+key,type=Path,required=True)
    cli.add_argument('--flop',choices=CASES,required=True)
    cli.add_argument('--driver',type=Path)
    run(cli.parse_args())
