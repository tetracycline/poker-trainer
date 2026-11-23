"""Reproduce checked-flop IP bets and the observed NL2 three-bet-pot turn replies."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile

from hu_b467_river_source_gate import compact, sha
from hu_b590_rank3_barrels import main
from hu_b607_checked_3bet_turns import STUDY

SOURCES = {
    156: ("ln-3bp-3c_t_model-1v9gtc3", {
        "4dQhKsTc": (14599605695, "0b6b5ddff20e0394c250171188d6f08cdb0e3d9194e5bb60ab4986cd9b41ffc9"),
        "2d7hKs9d": (14593123141, "a4f8ce62f6b0589e988939a4c6b020e2fba7d7d3dc7dd4c494d3583883e0fad5"),
        "3d7hAsKd": (14528582176, "174b88e1fd55c9e29f7473a35650dd4d6d7bb2225a84f920870bbbc4874b17d6"),
    }),
    198: ("ln-3bp-3b_t_model-wsml7c", {
        "6cTsJc2h": ("B607_R198_JCTS6C", "93740bac58cb066eddaf42d5c7895274589d24b30edfd7bbcbac94ba59b7b2cc"),
        "5dTcJd2h": ("B607_R198_JDTC5D", "4c0644ff36c07a1396305999cdc59c4d7786899cd83fb4db1c5af0a2ef5b8f8a"),
        "7hTdJh3s": ("B607_R198_JHTD7H", "766f3fd6cb37c6e4fb763e949fae703776b5e8c636225c704fe19441eaab415b"),
        "6d9cTd2h": ("B607_R198_TD9C6D", "522fe86493f358ed5de2390d6b9543649b9b2f4d4e0a80db45bf41a43603b62d"),
        "4h9sTh3s": ("B607_R198_TH9S4H", "d1b4cc5617c67d91e24aefd832949d66c36a2bb87fe06a9420f345bfff81827c"),
    }),
}


def checked_parent(board, pin, ranges):
    flop, turn, public = board["flop"], board["turn"], board["public_board"]
    code = STUDY.archive_code(flop)
    assert (pin["archive_code"], pin["run"]) == (code, 45176012281)
    path = Path("data/solver_evidence") / f"NL2_{code}.zip"
    inputs = json.loads(Path("data/nl2_hu_b607_checked_3bet_inputs.json").read_bytes())
    definition, = (r for r in inputs if (r["flop"], r["turn"]) == (flop, turn))
    assert sha(path.read_bytes()) == definition["sha256"] == pin["archive_sha256"]
    with ZipFile(path) as archive:
        root_job = json.loads(archive.read("root.job.json"))
        root = json.loads(archive.read("root.json"))
        job = json.loads(archive.read("gto.job.json"))
        raw = archive.read("gto.json")
    subgame = json.loads(raw)
    assert sha(raw) == pin["source_sha256"]
    assert (root_job["oop"],root_job["ip"]) == tuple(ranges.to_str(v) for v in ranges.ranges(STUDY.spot, "gto"))
    assert root_job["flop_oop"] == root_job["flop_ip"] == "50%"
    for native, setup in ((root,root_job),(subgame,job)):
        assert (native["flop"],native["pot"],native["stack"]) == (flop,1650,9250)
        assert (setup["flop"],setup["pot"],setup["stack"]) == (flop,1650,9250)
        assert (setup["rake_rate"],setup["rake_cap"])==(.05,1000)
        assert not setup.get("locks") and setup.get("hero") is None
        assert not native["info"].get("lock_stats") and 0<=native["info"]["gto_expl_pct"]<=.5
    assert (job["turn"],job["line0"],job["root_no_bet"]) == (turn,["x","x","/"],False)
    assert job["turn_oop"] == job["turn_ip"] == "33%,50%,75%"
    parent, = (n for n in root["nodes"] if (n["board"],n["line"]) == (public,"x x/"))
    assert (parent["bets"],parent["pot"]) == ([0,0],1650)
    for seat, key in enumerate(("oop_w","ip_w")):
        assert job[key] == [[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4]
    subgame.update(line0="x x",turn=turn,rivers=[])
    return dict(source=dict(root=root,subgame=subgame),job=job,
                identity=dict(source_sha256=sha(raw),root_sha256=sha(compact(root))))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--rank", type=int, choices=SOURCES, required=True)
    args, remaining = parser.parse_known_args()
    model, cases = SOURCES[args.rank]
    main(model_id=model, rank=args.rank, flop_line="x x", cases=cases, argv=remaining,
         repo_parent=checked_parent if args.rank==198 else None, schema="NL2_HU_B646_IP_CHECKED_THREEBET_V1")
