"""Reproduce B718 from twelve original Actions artifact ZIPs (named ARTIFACT_ID.zip)."""
import argparse
import base64
import hashlib
import json
import subprocess
from pathlib import Path
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b481_rank27_limp_rivers import check_limp_source
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b568_caller_rivers import hand_cell
from hu_sequential_cfr_reach import accepted, cardkey, game_reach

LINE = "b33 c/x b50 c/x"
ACTIONS = {"過": "x", "下注 ¾": "b75"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def source_json(archive, name, expected=None):
    raw = archive.read(name)
    if expected is not None:
        assert sha(raw) == expected
    return json.loads(raw)


def replay(folder, pin, routes, profile):
    path = folder / (str(pin["artifact_id"]) + ".zip")
    assert sha(path.read_bytes()) == pin["sha256"]
    with ZipFile(path) as archive:
        files = archive.namelist()
        assert {archive.read(n).decode().strip() for n in files if n.startswith("evidence/") and n.endswith(".txt")} == {SOLVER, RUST}
        manifests = [n for n in files if n.startswith("evidence/") and n.endswith(".json")]
        if pin["result"] == "JOB_ONLY_NO_NATIVE_RESULT":
            assert not manifests and len(files) == 3 and sum(n.endswith(".job.json") for n in files) == 1
            return
        manifest_name, = manifests
        manifest = source_json(archive, manifest_name)
        assert (manifest["spot"], manifest["pot_family"], manifest["version"], manifest["flop"], manifest["failures"]) == ("LMP_CO_BB", "LMP", pin["version"], pin["flop"], [])
        assert (manifest["solver_pin"], manifest["solver_ranges_sha256"], manifest["pool_source_sha256"]) == (PIPELINE, RANGES, POOL)
        ranges = manifest["preflop_ranges"]
        assert ranges["source"] == profile["source"]
        case, = [c for c in manifest["cases"] if c["turn"] == pin["turn"] and c["line"] == "b33 c"]
        rootpath = "solver/postflop/" + manifest["file_flop"]
        subpath = "solver/postflop/" + case["source_path"]
        root = source_json(archive, rootpath, manifest["file_flop_sha256"])
        sub = source_json(archive, subpath, case["source_sha256"])
        rootjob = source_json(archive, rootpath.replace(".json", ".job.json"))
        subjob = source_json(archive, subpath.replace(".json", ".job.json"))
        check_limp_source(dict(manifest=manifest, root_job=rootjob, subgame_job=subjob))
        for seat in ("oop", "ip"):
            density = ranges[seat + "_169"]
            combos = lambda h: 6 if len(h)==2 else 4 if h.endswith("s") else 12
            assert sum(w > 0 for w in density.values()) == profile[seat + "_nonzero_classes"]
            assert abs(sum(combos(h)*w for h,w in density.items())/1326 - profile[seat + "_combo_weight_fraction"]) < 1e-12
        assert (root["pot"], root["stack"], sub["pot"], sub["stack"]) == (250, 9900, 416, 9817)
        for game, job in ((root, rootjob), (sub, subjob)):
            assert 0 <= game["info"]["gto_expl_pct"] <= .5
            assert job.get("hero") == (1 if pin["version"] == "exp_ip" else None)
            assert job.get("locks", []) == rootjob.get("locks", [])
            if pin["version"] == "exp_ip":
                assert 0 <= game["info"]["hero_gap_pct"] <= .5 and game["info"]["lock_stats"]
            else:
                assert not job.get("locks") and not game["info"].get("lock_stats")
        assert (subjob["line0"], subjob["root_no_bet"]) == (["b33", "c", "/"], False)
        opening, = [n for n in root["nodes"] if n["line"] == ""]
        facing, = [n for n in root["nodes"] if n["line"] == "b33"]
        parent, = [n for n in root["nodes"] if n["line"] == "b33 c/" and n["board"].endswith(pin["turn"])]
        assert (opening["player"], opening["pot"], opening["bets"]) == (0, 250, [0,0])
        assert (facing["player"], facing["pot"], facing["bets"]) == (1, 333, [83,0])
        assert (parent["player"], parent["pot"], parent["bets"]) == (0, 416, [83,83])
        board = parent["board"]
        public = {board[i:i+2] for i in range(0, len(board), 2)}
        enabled = [accepted(opening, root["hands"], "b33"), accepted(facing, root["hands"], "c")]
        for seat, key in enumerate(("oop_w", "ip_w")):
            weights = [[h,w] for h,w in zip(root["hands"][seat], parent["wr"][seat], strict=True) if w>1e-4]
            assert subjob[key] == weights
            enabled[seat] &= {cardkey(h) for h,_ in weights if public.isdisjoint(cardkey(h))}
        heroes = [h for h in enabled[1] if hand_cell("".join(h),board[:6])[0] in routes["flop"]
                  and hand_cell("".join(h),board)[0] in routes["turn"] and any(set(h).isdisjoint(v) for v in enabled[0])]
        assert len(heroes) == pin["boundary_compatible_ui_hero"]
        masks = game_reach(root, sub)[0]
        rivers = {n["board"]: n for n in sub["nodes"] if (n["line"], n["player"]) == (LINE, 1)}
        assert set(rivers) == set(pin["river"])
        for i, pub in enumerate(pin["river"]):
            node = rivers[pub]
            assert (node["pot"], node["bets"], sub["stack"] - max(node["bets"])) == (832,[208,208],9609)
            actual = proof(root, sub, node, masks)
            assert (masks[f"{pub}|{LINE}|1"]["count"], actual["strict_legal_combos"]) == (pin["actor_only"][i], pin["joint_hero"][i])
            bits = base64.b64decode(actual["compatible_action_mask_b64"], validate=True)
            displayed = []
            for h, allow in zip(sub["hands"][1], bits, strict=True):
                if not allow:
                    continue
                keys = [hand_cell(h,pub[:j])[0] for j in (6,8,10)]
                if any(k not in routes[st] for k,st in zip(keys, ("flop","turn","river"), strict=True)):
                    continue
                action = ACTIONS[routes["river"][keys[-1]]]
                if action in node["acts"] and allow & 1 << node["acts"].index(action):
                    displayed.append(h)
            assert len(displayed) == pin["displayed"][i]


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--zips", type=Path, required=True)
    cli.add_argument("--report", type=Path, default=Path("data/solver_evidence/partial/b718_limp_source_audit.json"))
    cli.add_argument("--routes-tool", type=Path, default=Path("tools/hu_b718_limp_routes.cjs"))
    args = cli.parse_args()
    report = json.loads(args.report.read_bytes())
    routes = json.loads(subprocess.check_output(["node",args.routes_tool]))
    assert routes["115"]["turn_pct"] == 33 and routes["116"]["turn_pct"] == 50
    assert routes["116"]["river"] == {"paired:0":"下注 ¾","paired:2":"過","paired:4":"過"}
    assert len(report["originals"]) == 12
    for pin in report["originals"]:
        replay(args.zips, pin, routes["116"], report["source_profile"])
    print("B718: 12 authentic archives, 5 GTO flops, 10 zero-joint GTO rivers, 2 locked rivers with zero displayed hands.")
