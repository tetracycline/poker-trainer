"""Replay three-bet-pot responses after a checked flop using the aggressor’s real position."""
import argparse
import gzip
import json
from pathlib import Path
from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import compact, sha
from hu_b537_threebet_checked import RANGE_SHA
from hu_b590_rank3_barrels import main

SOURCES = {
    131: ("ln-3bp-3c_t_model-1oebhk7", {
        "4c6s8h9d": ("B537_8H6S4C_9D", "7f66a1e3a3217a6b075ff0d124fdff12d349c89b84b5305a6b3a99cc1f796421"),
        "4h5d7cKc": ("B537_7C5D4H_KC", "d13a007472a01bdb4845b9d21eff9a5929a31a6819514c5c9c2d54ce1b86803c"),
        "4d7h8sQh": ("B537_8S7H4D_QH", "263e7ecf337f9a05bc7cd2d4dc297fc3bca284e863c5423da5727e8c43195b14"),
    }),
    82: ("ln-3bp-3b_t_model-6vpmec", {
        "4dQhKsTc": (14599605695, "0b6b5ddff20e0394c250171188d6f08cdb0e3d9194e5bb60ab4986cd9b41ffc9"),
        "2d7hKs9d": (14593123141, "a4f8ce62f6b0589e988939a4c6b020e2fba7d7d3dc7dd4c494d3583883e0fad5"),
        "3d7hAsKd": (14528582176, "174b88e1fd55c9e29f7473a35650dd4d6d7bb2225a84f920870bbbc4874b17d6"),
    }),
    120: ("ln-3bp-3b_t_model-n5cvfv", {
        "2d7hKs9d": (14593390837, "cd5c9cb6bedb3cc3bc72a3fc5053b950698ae8d150f1b57b2c8af2c657680311"),
        "4d8hAs8d": (14528551179, "fd980bcfd2418d4876fb68afdf5c442b11096ee397b00adec34fc9a878b228ac"),
        "2s7sKs9d": (14530206356, "a3af9124f71b333778007482b63c74a394dc49aed6d8324ec29ce764a19de87d"),
        "4dQhKsTc": (14592263783, "b2cb83c4641c7991b5aba9d76c199879073d72d49313ce960a1a921b1c5d93cc"),
    }),
}


def checked_co_parent(board, pin, ranges):
    code = pin["archive_code"]
    assert code == f'B537_{board["flop"].upper()}_{board["turn"].upper()}'
    raw = Path(f"data/solver_evidence/NL2_{code}.json.gz").read_bytes()
    assert sha(raw) == pin["archive_sha256"]
    package = json.loads(gzip.decompress(raw))
    assert (package["solver"], package["rust"], package["run_id"]) == (SOLVER, RUST, pin["run"])

    source, = (s for s in package["source_arrays"] if s["version"] == "gto")
    manifest, root, turn = source["manifest"], source["root"], source["subgame"]
    assert (manifest["spot"], manifest["version"], manifest["flop"], manifest["selected_lines"]) == (
        "CO3_BTN", "gto", board["flop"], ["x x"])
    assert not manifest["locks"] and not manifest["failures"]
    case, = (c for c in manifest["cases"] if (c["line"], c["turn"]) == ("x x", board["turn"]))
    assert sha(compact(root)) == source["root_sha256"] == manifest["file_flop_sha256"]
    assert sha(compact(turn)) == source["source_sha256"] == case["source_sha256"] == pin["source_sha256"]
    assert all(0 <= game["info"]["gto_expl_pct"] <= .5 for game in (root, turn))

    setup, job = source["root_job"], source["subgame_job"]
    assert sha(compact([setup["oop"], setup["ip"]])) == RANGE_SHA["gto"]
    assert all(not j.get("locks") and j.get("hero") is None for j in (setup, job))
    assert ranges.SPOTS["CO3_BTN"]["pfr"] == "ip" and (root["pot"], root["stack"]) == (1650, 9250)
    parent, = (n for n in root["nodes"] if (n["line"], n["board"]) == ("x x/", board["public_board"]))
    assert parent["bets"] == [0, 0] and parent["pot"] == 1650
    for seat, name in enumerate(("oop_w", "ip_w")):
        hands = zip(root["hands"][seat], parent["wr"][seat], strict=True)
        assert job[name] == [[hand, weight] for hand, weight in hands if weight > 1e-4]
    identity = {"root_sha256": source["root_sha256"], "source_sha256": source["source_sha256"]}
    return dict(source=source, job=job, identity=identity)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--rank", type=int, choices=SOURCES, required=True)
    args, remaining = parser.parse_known_args()
    model_id, cases = SOURCES[args.rank]
    main(model_id=model_id, rank=args.rank, flop_line="x x", cases=cases, argv=remaining,
         repo_parent=checked_co_parent if args.rank == 131 else None,
         schema="NL2_HU_B628_3BP_TURN_BARREL_RESPONSES_V1")
