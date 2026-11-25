"""B877: two new distinct rank57 low-paired GTO+measured-NL2 original flops.

Rank57 is 2nd among 234 APPROX with 0.767868% estimated modeled per-hand
opportunity; certify only after independent SHA/source/SPR + two-seat
action-reach replay yields >=3 valid distinct public flops.
"""
import argparse,json,subprocess
from pathlib import Path
import hu_b664_rank57_bottom_pair as base
import hu_b637_rank57 as old
from hu_b467_river_source_gate import json_bytes
from hu_b580_rank27_rivers import suit_isomorphism_class

PARENT_BLOB="aa0eb696f992381e500a6683ed2e90b74f75e5fa"
CASES={
    "Kh5s5d":["2c","3h","7s"],
    "Ts6h6d":["3c","4s","8h"],
}
EXCLUDED=set(base.CASES)|set(old.CASES)|{"Ad6h6s","Kh8d8s"}

def preflight():
    assert subprocess.check_output(["git","hash-object",base.__file__],text=True).strip()==PARENT_BLOB
    assert base.CASES and set(base.CASES)=={"Kh4s4d","Qd3h3s","Js5h5c","9s4d4h"}
    assert (old.MODEL,old.LINE)==("ln-opfr-r_model-8ze7gv","x b50 c/b75 c/")
    fresh={suit_isomorphism_class(f) for f in CASES}
    previous={suit_isomorphism_class(f) for f in EXCLUDED}
    assert len(fresh)==len(CASES)==2 and not (fresh & previous)
    for flop,turns in CASES.items():
        cards=[flop[i:i+2] for i in (0,2,4)]
        assert len(set(cards))==3
        assert cards[1][0]==cards[2][0] and cards[0][0]!=cards[1][0]
        assert len(set(turns))==len(turns)==3
        assert all(len(t)==2 and t not in cards for t in turns)
    st=json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())
    pp=json.loads(Path("data/nl2_hu_b838_234_approx_frequency_priority.json").read_bytes())
    assert (st["CERT_MULTIBOARD"],st["APPROX"],st["EST"],st["TOTAL"])==(158,234,0,392)
    row,=[x for x in pp["rows"] if x["rank"]==57]
    assert row["passes_min_0_2_pct_frequency"] and row["model_id"]==old.MODEL
    assert st["records"][old.MODEL]["label"]=="APPROX"
    assert pp["current_certified_opportunity_share_pct"]==84.700987
    return sorted(EXCLUDED)

def run(a):
    excluded=preflight()
    if a.preflight:
        print(json.dumps(dict(rank=57,new_original_flops=sorted(CASES),excluded_prior_flops=excluded,cert_promotions=0)))
        return
    previous=base.CASES
    try:
        base.CASES=CASES
        base.run(a)
    finally:
        base.CASES=previous
    pf=a.output/"proof.json"
    proof=json.loads(pf.read_bytes())
    assert proof["rank"]==57 and proof["model_id"]==old.MODEL and proof["flop"]==a.flop
    assert (proof["line"],proof["actual_river_pot_bb"],proof["actual_river_effective_stack_bb"])==(old.LINE,30,85)
    assert len(proof["turns"])<=len(CASES[a.flop])
    assert proof["root_sha256"] and all(t["turn"] in CASES[a.flop] for t in proof["turns"])
    proof.update(schema="NL2_B877_R57_TWO_FRESH_LOW_PAIRED_ORIGINALS_V1",
       parent_worker_blob=PARENT_BLOB,
       preregistered_flops=sorted(CASES),
       historical_flops_excluded=excluded,
       genuine_original_flop=True,
       new_certifications=0,
       source_kind="PINNED_GTO_AND_REAL_ACTOR_OOP_PARTIAL_NL2_LOCK",
       unobserved_private_card_NL2_rates_never_inferred=True,
       independent_full_source_replay_required=True,
       only_named_board_exact_reach_can_be_certified=True)
    pf.write_bytes(json_bytes(proof))
    n=sum(len(t["checks"]) for t in proof["turns"])
    print(json.dumps(dict(rank=57,flop=a.flop,strict_joint_public_boards=n,cert_promotions=0)))
if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--solver",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    ap.add_argument("--driver",type=Path)
    ap.add_argument("--flop",choices=CASES,required=True)
    ap.add_argument("--preflight",action="store_true")
    run(ap.parse_args())
