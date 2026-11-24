"""Test the remaining JhTh8c original using B782's identical checked-branch and same-opponent gates."""
import argparse
import json
from pathlib import Path

import hu_b782_rank230_mid_pairs as base
from hu_b467_river_source_gate import json_bytes
from hu_b580_rank27_rivers import suit_isomorphism_class

FLOP='JhTh8c'
TURNS={'5c':13,'6d':13,'7s':13,'9c':13,'2d':13,'4s':7}
NAME='tools/hu_b785_rank230_jack_high.py'
PARENT_SHA='d93bef8fa8aca87dbf1838808128653a3ba24c79'
ROOT_SHA='6bd75273ce5b12bba8b1e74b493b547250a6bdc7173c8cee6738af2ddf801fc1'
ORIGINALS=('Th9h7c','Ts8s7h','Ts9s6h')
SOURCE_RUN=45348113146
SOURCE_HEAD='45ed3315f6998b86400899914ce63fa1cab8d647'


def run(a):
    assert a.flop==FLOP and base.blob(base.WORKER)==PARENT_SHA
    assert len({suit_isomorphism_class(f) for f in (FLOP,*ORIGINALS)})==4
    # These are the two previously successful prospective group members and the new original.
    # The B785 CLI only schedules the latter.
    base.SPEC={f:base.SPEC[f] for f in ORIGINALS[:2]}|{FLOP:(695,TURNS)}
    base.ROOTS={**base.ROOTS,FLOP:ROOT_SHA}
    base.WORKER=NAME
    base.run(a)
    if a.preflight:return
    p=a.output/'proof.json';d=json.loads(p.read_bytes())
    assert d['unchanged_original_nodes']==14 and d['origin']['root_result_sha256']==ROOT_SHA
    assert d['origin']['worker']['run']==45312594665 and d['origin']['worker']['id']==14882524997
    assert d['source_worker_blob']==base.blob(NAME) and d['preregistered_turns']==list(TURNS)
    d.update(schema='NL2_B785_R230_JH_TH_8C_ORIGINAL_EXTENDED_V1',source_parent_worker_blob=PARENT_SHA,
             earlier_distinct_flops=list(ORIGINALS),earlier_source_run=SOURCE_RUN,earlier_source_head=SOURCE_HEAD)
    p.write_bytes(json_bytes(d))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--flop',choices=[FLOP],default=FLOP);p.add_argument('--preflight',action='store_true');p.add_argument('--driver',type=Path)
    run(p.parse_args())
