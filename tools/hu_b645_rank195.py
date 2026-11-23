"""Verify BTN turn checks and bets after a checked-through flop in a BB three-bet pot."""
import io
import json
from zipfile import ZipFile

from hu_b467_river_source_gate import sha
from hu_b483_locked_medium import PIPELINE, RANGES
from hu_checked_stab_turns import TurnStudy, main


STUDY = TurnStudy(
    batch="B645", rank=195, model="ln-3bp-3c_t_model-1dv9vgr", filename="b645_bb_checked",
    template="STAGE2_B04_LOCAL_BB3_BTN_RAW.zip",
    template_sha="4748a1755bc2a3081680130972895a4a288c1a3b6129f986cbc1ff2a9861d2a7",
    spot="BB3_BTN", family="3BP", preflop_source="PINNED_POKER_SOLVER_PREFLOP_CFR",
    root_pot=2050, root_stack=9000, ip_bet_pct=50, root_branches=("x x",),
    label="BB 與 BTN 翻牌雙方過牌；轉河牌按 NL2 分街頻率鎖定 BB 回應",
    report_schema="NL2_HU_B645_ORIGINAL_LOCKED_MEDIUM_V1",
)


def original_template(raw):
    with ZipFile(io.BytesIO(raw)) as z:
        manifest_name, = [n for n in z.namelist() if n.endswith("/evidence/manifest.json")]
        m=json.loads(z.read(manifest_name))
        assert (m["source"],m["spot"],m["version"],m["failures"]) == ("tetracycline/poker-solver","BB3_BTN","gto",[])
        assert (m["source_pipeline_sha256"],m["source_ranges_sha256"]) == (PIPELINE,RANGES)
        case, = [c for c in m["cases"] if (c["flop"],c["turn"],c["line"]) == ("QsJh4d","7s","x x")]
        jobs=[]
        for suffix, digest in [("QsJh4d_extra_branch.json",case["flop_sha256"]),("QsJh4d_xx_7s.json",case["sub_sha256"])]:
            name, = [n for n in z.namelist() if n.endswith("/"+suffix)]
            assert sha(z.read(name)) == digest
            jobs.append(json.loads(z.read(name[:-5]+".job.json")))
    assert (jobs[0]["pot"],jobs[0]["stack"],jobs[1]["line0"]) == (2050,9000,["x","x","/"])
    return dict(root_job=jobs[0],subgame_job=jobs[1],manifest=dict(spot=m["spot"],solver_pin=PIPELINE,
                solver_ranges_sha256=RANGES,preflop_ranges=dict(source=STUDY.preflop_source,spot=m["spot"],
                source_preflop_tree_sha256=m["source_preflop_tree_sha256"])))


if __name__ == "__main__":
    main(STUDY,displayed_actions={"過":"x","下注 ⅓":"b33","下注 ½":"b50"},template_reader=original_template)
