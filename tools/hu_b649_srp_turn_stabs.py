"""Solve in-position turn bets after the out-of-position flop bettor checks."""
import argparse
import gzip
import json
from pathlib import Path

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, sha
from hu_b590_rank3_barrels import main

SOURCES = {
    8: ("ln-ipfr-t_model-qcljc6", {
        "4d5h6s6h": (14792976867, "df887d5566b9f99505a5310b3e236205c6bfbd55b19013266fbf3e91071a442b"),
        "4c5c7d9c": (14792312789, "8aeec8c25159cde3db0b15046bddee1bd1fa3f71b4b92851b25918879c392852"),
        "3h4c6dKd": (14793340092, "917c6f833fb3add6a982efa1bf6d788420433a990ba2448afeb10491cd3f24ea"),
    }),
    12: ("ln-ipc-t_model-btptzw", {
        "2d7hKs9d": ("B486_44654973894_Ks7h2d_gto", "a3ad72199e526c0d7435da1245d7190ace7d3db8ed30bb98aada0412ba905041"),
        "2d9hAsKd": ("B486_44666285424_As9h2d_gto", "243d11045082459e6269385fded7c311fdf462233e3b06489290a3292606f864"),
        "3d7hAsKd": ("B486_44736420272_As7h3d_gto", "c3369bc3052b9c1111bbb8633f41751de3a1a2cb1a3c10004b9b1ff8a5d1dfad"),
        "3h8cKd5c": ("B486_45101236793_Kd8c3h_gto", "af167783b30fab7e9c0516f77e6d9d01344937012a8a6bb5f206dc272f275855"),
    }),
}


def sb_parent(board, pin, ranges):
    code=pin["archive_code"]
    assert code == f'B486_{board["source_run_id"]}_{board["flop"]}_gto'
    raw=Path(f"data/solver_evidence/NL2_{code}.json.gz").read_bytes()
    assert sha(raw)==pin["archive_sha256"]
    package=json.loads(gzip.decompress(raw))
    assert (package["schema"],package["solver"],package["rust"])==("NL2_B486_ORIGINAL_SB_BB_CFR_V1",SOLVER,RUST)
    source=package["source"]
    assert (source["run"],source["version"],source["manifest"]["spot"])==(pin["run"],"gto","SB_BB")
    root, sub=source["root"],source["subgame"]
    setup,job=source["root_job"],source["subgame_job"]
    assert sha(compact(root))==source["root_sha256"] and sha(compact(sub))==source["source_sha256"]==pin["source_sha256"]
    assert (setup["oop"],setup["ip"])==tuple(ranges.to_str(v) for v in ranges.ranges("SB_BB","gto"))
    assert (sub["line0"],sub["turn"],sub["flop"])==("b50 c",board["turn"],board["flop"])
    assert (root["pot"],root["stack"],sub["pot"],sub["stack"])==(600,9700,1200,9400)
    for output, native_job in ((root,setup),(sub,job)):
        assert not native_job.get("locks") and native_job.get("hero") is None
        assert (native_job["rake_rate"],native_job["rake_cap"])==(.05,1000)
        assert not output["info"].get("lock_stats") and 0<=output["info"]["gto_expl_pct"]<=.5
    parent,=(n for n in root["nodes"] if (n["board"],n["line"])==(board["public_board"],"b50 c/"))
    assert (parent["bets"],parent["pot"])==([300,300],1200)
    for seat, key in enumerate(("oop_w","ip_w")):
        assert job[key]==[[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4]
    return dict(source=source,job=job,identity=dict(source_sha256=source["source_sha256"],root_sha256=source["root_sha256"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--rank", type=int, choices=SOURCES, required=True)
    args, remaining = parser.parse_known_args()
    model,cases=SOURCES[args.rank]
    main(model_id=model,rank=args.rank,flop_line="b50 c",cases=cases,argv=remaining,
         repo_parent=sb_parent if args.rank==12 else None,schema="NL2_HU_B649_IP_BET_AFTER_FLOP_LEAD_V1")
