"""B882: three independent high-frequency rank29 two-tone originals.

All 3 board candidates and turns are frozen before new solve outcomes.
No CERT promotion without subsequent independently replayed authentic GTO
plus same-actor measured NL2 lock and strict two-seat/combo route proof.
"""
import argparse
import json
import subprocess
from pathlib import Path

import hu_b703_rank29_highcards as base
import hu_b717_rank29_low_connected as low
import hu_b839_rank29_new_monotone as mono
import hu_b659_rank29_monotone as first
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b467_river_source_gate import json_bytes

PARENT_BLOB = "1adbb4fe4bd2ad36643dd3e79bf5f41cd9580ac8"
MODEL = "ln-iso-lmp_r_model-gifggm"
WORKER = "tools/hu_b882_rank29_new_twotone.py"
CASES = {
    "Jd9d3c": ["2d", "4d", "5d", "7d"],
    "Qh8h4s": ["2h", "3h", "5h", "7h"],
    "KcTc6h": ["2c", "3c", "4c", "7c"],
}
WITNESSES = {
    "Jd9d3c": ("2d", "6s", "JcQh", "AdAh"),
    "Qh8h4s": ("2h", "6d", "QcKh", "AdAc"),
    "KcTc6h": ("2c", "9s", "KdQh", "AdAh"),
}
CURRENT_UI = {
    "nl2_hu_model.js": "b3dea42d0478e178aefda628e539ec7d95fbe6bd",
    "nl2.js": "15aee97e53a156fe073c96a120638a8a3679958f",
}

def preflight():
    assert subprocess.check_output(["git","hash-object",base.__file__],text=True).strip() == PARENT_BLOB
    assert base.MODEL == MODEL
    reg=json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())
    pr=json.loads(Path("data/nl2_hu_b838_234_approx_frequency_priority.json").read_bytes())
    assert (reg["CERT_MULTIBOARD"],reg["APPROX"],reg["EST"],reg["TOTAL"]) == (158,234,0,392)
    item, = [x for x in pr["rows"] if x["rank"] == 29]
    assert item["model_id"] == MODEL and item["passes_min_0_2_pct_frequency"]
    assert reg["records"][MODEL]["label"] == "APPROX"
    assert pr["current_certified_opportunity_share_pct"] == 84.700987
    missing=json.loads(Path("data/nl2_hu_b871_current_234_source_gap_rescreen.json").read_bytes())
    n, = [x for x in missing["models"] if x["rank"] == 29]
    assert (n["model_id"],n["preliminary_new_flops_needed"]) == (MODEL,3)
    old=set(first.CASES)|set(base.CASES)|set(low.CASES)|set(mono.CASES)
    old |= {x["flop"] for x in json.loads(Path("data/nl2_hu_b582_rank29_reach.json").read_bytes())["flops"]}
    new={suit_isomorphism_class(f) for f in CASES}
    assert len(new) == len(CASES) == 3
    assert not new & {suit_isomorphism_class(f) for f in old}
    assert set(CASES) == set(WITNESSES)
    for flop,turns in CASES.items():
        cards={flop[i:i+2] for i in (0,2,4)}
        assert len(cards)==3 and len({c[1] for c in cards})==2
        assert len(turns)==len(set(turns))==4
        suit=max({s for s in "cdhs"},key=lambda s:sum(c[1]==s for c in cards))
        assert sum(c[1]==suit for c in cards)==2
        assert all(t not in cards and t[1]==suit for t in turns)
        turn,river,hero,villain=WITNESSES[flop]
        allcards=[flop[i:i+2] for i in (0,2,4)]+[turn,river,hero[:2],hero[2:],villain[:2],villain[2:]]
        assert len(allcards)==9 and len(set(allcards))==9 and turn in turns
    return old

def run(a):
    old=preflight()
    prev=(base.CASES,base.RANGE_WITNESSES,base.APP_PINS)
    try:
        base.CASES=CASES
        base.RANGE_WITNESSES=WITNESSES
        base.APP_PINS=CURRENT_UI
        base.run(a)
    finally:
        base.CASES,base.RANGE_WITNESSES,base.APP_PINS=prev
    if a.preflight:
        print(json.dumps(dict(rank=29,frozen_flops=list(CASES),archived_rank29_flops=len(old),
                              true_solves_this_preflight=0,promotions=0)))
        return
    proofpath=a.output/"proof.json"
    proof=json.loads(proofpath.read_bytes())
    assert (proof["rank"],proof["model_id"],proof["flop"],proof["line"],proof["actor"]) == (29,MODEL,a.flop,"b50 c/b75 c/",0)
    assert len(proof["turns"])<=len(CASES[a.flop])
    assert proof["root_sha256"] and proof["original_root_solves"] if "original_root_solves" in proof else proof["root_sha256"]
    pairs=sum(len(row.get("checks",[])) for row in proof["turns"])
    proof.update(schema="NL2_B882_R29_THREE_FROZEN_TWOTONE_ORIGINALS_V1",
                 pinned_base_worker_blob=PARENT_BLOB,
                 currently_pinned_UI_blobs=CURRENT_UI,
                 independently_preregistered_flops=list(CASES),
                 historic_rank29_flops_excluded=sorted(old),
                 true_river_pair_candidate_count=pairs,
                 self_certified=False,
                 source_subject_to_independent_SHA_SPR_actor_combos_and_NL2_lock_gate=True,
                 no_unobserved_private_hand_NL2_frequencies_claimed=True)
    proofpath.write_bytes(json_bytes(proof))
    print(json.dumps(dict(rank=29,flop=a.flop,paired_public_river_candidates=pairs,CERT_upgrades=0)))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("solver","output"):p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--driver",type=Path)
    p.add_argument("--flop",choices=CASES,required=True)
    p.add_argument("--preflight",action="store_true")
    run(p.parse_args())
