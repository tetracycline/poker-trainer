"""B876: two genuinely new rank114 mid-high original flops; genuine GTO + NL2 actor lock.

Priority remains frozen B838. Exactly matched action history, 100bb root,
same-seat private card accessibility, full-street masks and original SHA
are inherited from authenticated B856. NO CERT until later independently
replayed original ZIPs show 3 distinct valid board pairs.
"""
import argparse
import json
import subprocess
from pathlib import Path

import hu_b856_rank114_midhigh as native
from hu_b467_river_source_gate import json_bytes
from hu_b580_rank27_rivers import suit_isomorphism_class

PARENT_BLOB="f62ed39c000dc8844a1a927ca1d45f5b135a8130"
MODEL="ln-iso-lmp_r_model-asilzt"
CASES={
    "Jh9d5c":["2s","3h"],
    "Ts8d4c":["3s","5h"],
}
PREVIOUS={
    "8s8h3d","7s7h4d","JcJh5d",
    "Jh8d6c","Th5d2c",
    "Jh6d3c","Th4d3c",
}

def preflight():
    assert subprocess.check_output(
        ["git","hash-object",native.__file__],text=True
    ).strip()==PARENT_BLOB
    assert native.MODEL==MODEL and native.LINE=="x x/x b66 c/"
    assert set(native.CASES)=={"Jh8d6c","Th5d2c"}
    assert set(native.EXCLUDED)<PREVIOUS
    assert len(CASES)==2
    fresh={suit_isomorphism_class(f) for f in CASES}
    prior={suit_isomorphism_class(f) for f in PREVIOUS}
    assert len(fresh)==2 and not fresh & prior
    for flop,turns in CASES.items():
        assert len(flop)==6 and len({flop[i:i+2] for i in (0,2,4)})==3
        assert len({flop[i+1] for i in (0,2,4)})==3
        assert 1<=len(turns)<=2 and len(set(turns))==len(turns)
        assert all(len(t)==2 and t not in {flop[i:i+2] for i in (0,2,4)}
                   for t in turns)
    from pathlib import Path
    s=json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())
    p=json.loads(Path("data/nl2_hu_b838_234_approx_frequency_priority.json").read_bytes())
    assert (s["CERT_MULTIBOARD"],s["APPROX"],s["EST"],s["TOTAL"])==(158,234,0,392)
    row,=[row for row in p["rows"] if row["rank"]==114]
    assert (row["model_id"],row["passes_min_0_2_pct_frequency"])==(MODEL,True)
    assert s["records"][MODEL]["label"]=="APPROX"
    assert p["current_certified_opportunity_share_pct"]==84.700987
    return {"excluded_historical_flops":sorted(PREVIOUS),"new_original_flops":sorted(CASES)}

def run(a):
    evidence=preflight()
    former=(native.CASES,native.EXCLUDED)
    try:
        native.CASES=CASES
        native.EXCLUDED=tuple(sorted(PREVIOUS))
        native.run(a)
    finally:
        native.CASES,native.EXCLUDED=former
    if a.preflight:
        return
    output=a.output/"proof.json"
    v=json.loads(output.read_bytes())
    assert v["rank"]==114 and v["model"]==MODEL and v["flop"]==a.flop
    assert (v["root_pot"],v["root_stack"],v["turn_bet"],v["river_pot"],v["river_stack"])==(250,9900,165,580,9735)
    assert v["positive_distinct_flops"] in (0,1)
    assert v["native_flop_solves_repeated"]==0 and len(v["turns"])<=len(CASES[a.flop])
    assert v["solver"]==native.SOLVER and v["rust"]==native.RUST
    assert v["route_sha256"] and v["native_files"]
    v.update(schema="NL2_B876_R114_TWO_FRESH_RAINBOW_ORIGINAL_GTO_NL2_V1",
       frozen_source_worker_blob=PARENT_BLOB,
       previously_tested_flops_excluded=evidence["excluded_historical_flops"],
       new_original_flops_preregistered=evidence["new_original_flops"],
       exact_model_priority_rank=114,
       independent_source_replay_required=True,
       no_generic_texture_certification=True,
       no_private_hand_NL2_empirical_data_claimed=True,
       certificate_promotions=0,
       original_root_reused=False)
    output.write_bytes(json_bytes(v))
    print(json.dumps(dict(rank=114,flop=a.flop,
      positive_distinct_flops=v["positive_distinct_flops"],
      native_locked_public_boards=v["native_locked_public_boards"],
      joint_halfpot_assessed=v["joint_halfpot_assessed"],
      nonpolarized_candidates=v["nonpolarized_candidates"],
      new_CERT=0)))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("solver","receipts","output"):
        p.add_argument("--"+key,type=Path,required=True)
    p.add_argument("--flop",choices=CASES,required=True)
    p.add_argument("--driver",type=Path)
    p.add_argument("--preflight",action="store_true")
    run(p.parse_args())
