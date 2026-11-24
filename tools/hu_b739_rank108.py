"""Extract omitted BB raise-call boundaries from three authentic limped GTO games."""
import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import EVIDENCE, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b481_rank27_limp_rivers import check_limp_source
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b568_caller_rivers import hand_cell
from hu_b637_rank57 import solve
from hu_b642_rank35 import CASES
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, game_reach

TURNS = {"2c2d4h": ("7s", "9h"), "3s3h2d": ("7c", "9d"), "4s4h2d": ("7c", "9h")}
LINE = "b50 r c"
MODEL = "ln-iso-lmp_t_model-1iwngt8"
ACTIONS = {"過": "x", "下注 ⅓": "b33", "下注 ½": "b50", "下注 ¾": "b75"}


def original(flop):
    code, digest, _ = CASES[flop]
    archive = EVIDENCE / f"NL2_{code}.zip"
    assert sha(archive.read_bytes()) == digest
    with ZipFile(archive) as z:
        raw, root_job, turn_job, m, receipt = [z.read(k) for k in (
            "original-flop.json", "original-flop.job.json", "original-subgame.job.json", "original-manifest.json", "provenance.json")]
    pin = json.loads(receipt)
    assert (sha(raw), sha(root_job), sha(turn_job)) == (pin["original_root_sha256"], pin["original_flop_job_sha256"], pin["original_job_sha256"])
    assert (pin["solver"], pin["rust"], pin["pool_sha256"], pin["version"]) == (SOLVER, RUST, POOL, "gto")
    root, rj, tj, manifest = map(json.loads, (raw, root_job, turn_job, m))
    assert (manifest["flop"], manifest["spot"], manifest["file_flop_sha256"], manifest["failures"]) == (flop, "LMP_CO_BB", sha(raw), [])
    check_limp_source(dict(manifest=manifest, root_job=rj, subgame_job=tj))
    assert not rj.get("locks") and not root["info"].get("lock_stats")
    assert (rj["pot"], rj["stack"], rj["flop_raise"], root["flop"]) == (250, 9900, "3x,a", flop)
    assert 0 <= root["info"]["gto_expl_pct"] <= .5
    return root, rj, tj, manifest, dict(archive=archive.name, archive_sha256=digest, **pin)


def preflight(root, route, turns):
    nodes = {n["line"]: n for n in root["nodes"] if len(n["board"]) == 6}
    first, facing, raised = (nodes[a] for a in ("", "b50", "b50 r"))
    assert [(n["player"], n["pot"], n["bets"]) for n in (first, facing, raised)] == [(0,250,[0,0]), (1,375,[125,0]), (0,750,[125,375])]
    bb = accepted(first, root["hands"], "b50") & accepted(raised, root["hands"], "c")
    co = accepted(facing, root["hands"], "r")
    results = {}
    for turn in turns:
        board = root["flop"] + turn
        assert not any(n["line"] == LINE+"/" and n["board"].endswith(turn) and "wr" in n for n in root["nodes"])
        live = sorted("".join(h) for h in bb if turn not in h and hand_cell("".join(h),board[:6])[0] in route["flop"]
                      and hand_cell("".join(h),board)[0] in route["turn"]
                      and any(turn not in v and set(h).isdisjoint(v) for v in co))
        assert live
        results[turn] = live
    return results


def inspect(root, sub, route, turn):
    sub.update(line0=LINE, turn=turn)
    node, = (n for n in sub["nodes"] if n["line"] == LINE+"/")
    assert node["player"] == 0 and node["pot"] == 1000 and node["bets"] == [0,0]
    assert {"x","b33","b50","b75"} <= set(node["acts"])
    row = proof(root, sub, node, game_reach(root, sub)[0])
    bits = base64.b64decode(row["compatible_action_mask_b64"],validate=True)
    hands = []
    for hole, allowed in zip(sub["hands"][0],bits,strict=True):
        ft = hand_cell(hole,node["board"][:6])[0]
        tt = hand_cell(hole,node["board"])[0]
        if ft in route["flop"] and tt in route["turn"] and allowed & (1 << node["acts"].index(ACTIONS[route["turn"][tt]])):
            hands.append("".join(cardkey(hole)))
    return dict(reach=row, displayed_hands=sorted(hands))


def main(args):
    assert sys.version_info[:2] == (3,11)
    solver = args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip() == SOLVER
    native = solver/"postflop/py"
    assert sha((native/"pipeline.py").read_bytes()) == PIPELINE and sha((native/"ranges.py").read_bytes()) == RANGES
    if args.driver:
        assert args.driver.resolve() == solver/"postflop/pfdriver/target/release/pfdriver"
        assert subprocess.check_output(["git","-C",solver/"postflop/postflop-solver","rev-parse","HEAD"],text=True).strip() == RUST
    sys.path.insert(0,str(native))
    import pipeline
    raw_pool = (solver/"inputs/pool_stats.json").read_bytes()
    assert sha(raw_pool) == POOL
    pool = json.loads(raw_pool)["NL2"]
    route_bytes = args.routes.read_bytes()
    route = json.loads(route_bytes)
    assert (route["model"],route["flop_bet_pct"],route["raise_to_multiple"],route["actual_spr"]) == (MODEL,50,3,9.525)
    old,rj,tj,m,identity = original(args.flop)
    turns = TURNS[args.flop]
    upper = preflight(old,route,turns)
    if args.preflight:
        print(json.dumps({t:len(v) for t,v in upper.items()}))
        return
    out = args.output
    new_job = dict(rj,out="result.json",extract=rj["extract"] + [dict(prefix=["b50","r","c",t],street=False,raw=True) for t in turns])
    root = solve(out/"boundary",new_job,args.driver)
    assert root["hands"] == old["hands"] and root["info"]["gto_iters"] == old["info"]["gto_iters"]
    assert 0 <= root["info"]["gto_expl_pct"] <= .5 and not root["info"].get("lock_stats")
    lookup = {(n["line"],n["board"],n["player"]):n for n in root["nodes"]}
    assert all(n == lookup[(n["line"],n["board"],n["player"])] for n in old["nodes"])
    rows = []
    for turn in turns:
        boundary, = (n for n in root["nodes"] if n["line"] == LINE+"/" and n["board"].endswith(turn))
        assert (boundary["pot"],boundary["bets"],boundary["player"]) == (1000,[375,375],0)
        weights = {key:[[h,w] for h,w in zip(root["hands"][seat],boundary["wr"][seat],strict=True) if w>1e-4]
                   for seat,key in enumerate(("oop_w","ip_w"))}
        job = dict(tj)
        job.update(weights, pot=1000,stack=9525,turn=turn,line0=["b50","r","c","/"],root_no_bet=False,turn_oop="33%,50%,75%,100%",
                   turn_ip="33%,50%,75%,100%",river_oop="50%,100%,a",river_ip="50%,100%,a",out="result.json",
                   target_pct=.45,rank_pct=.45,iters=2200,extract=[dict(prefix=[],street=True)])
        gto = solve(out/turn/"gto",job,args.driver)
        assert gto["stack"] == 9525 and gto["pot"] == 1000 and not gto["info"].get("lock_stats") and 0 <= gto["info"]["gto_expl_pct"] <= .5
        before = inspect(root,gto,route,turn)
        item = dict(turn=turn,source_gto_sha256=sha((out/turn/"gto/result.json").read_bytes()),gto=before)
        if before["displayed_hands"]:
            lock,rules = prepare_job(dict(source=dict(root=root,manifest=m,version="gto"),job=job),"exp_oop",pool,pipeline)
            lock["out"] = "result.json"
            result = solve(out/turn/"exp_oop",lock,args.driver)
            assert result["info"]["lock_stats"] and result["hands"]==gto["hands"] and 0 <= result["info"]["hero_gap_pct"] <= .5 and 0 <= result["info"]["gto_expl_pct"] <= .5
            measured = audit_patterns(result,lock,dict(locks=rules),pool,0)
            assert any(v>0 for k,v in measured["driver_tree_nodes"].items() if k in measured["marginal_targets"])
            after = inspect(root,result,route,turn)
            item.update(nl2=after,measured_lock=measured,source_nl2_sha256=sha((out/turn/"exp_oop/result.json").read_bytes()),
                        shared_displayed_hands=sorted(set(before["displayed_hands"]) & set(after["displayed_hands"])))
        rows.append(item)
    summary = dict(positive_distinct_flops=int(any(x.get("shared_displayed_hands") for x in rows)),
                   native_locked_public_boards=sum("nl2" in x for x in rows),
                   joint_halfpot_assessed=sum(x["nl2"]["reach"]["b50"] is not None for x in rows if "nl2" in x),
                   nonpolarized_candidates=sum(bool((x["nl2"]["reach"]["b50"] or {}).get("candidate")) for x in rows if "nl2" in x))
    report = dict(schema="NL2_B739_LIMP_BB_B50_R3_CALL_TURN_SOURCE",rank=108,model=MODEL,flop=args.flop,
                  line=LINE,actual_pot=1000,actual_stack=9525,actual_spr=9.525,rendered_model_spr=route["registry_spr"],
                  source_only=True,original=identity,old_nodes_reproduced=len(old["nodes"]),original_job_extra_extracts=len(turns),
                  rendered_route_sha256=sha(route_bytes),upstream_legal_hands=upper,
                  boundary_source_sha256=sha((out/"boundary/result.json").read_bytes()),turns=rows,**summary)
    (out/"proof.json").write_bytes(json_bytes(report))
    (out/"routes.json").write_bytes(route_bytes)
    print(json.dumps(summary))


if __name__ == "__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--flop",choices=TURNS,required=True)
    for field in ("solver","output","routes"):
        cli.add_argument("--"+field,type=Path,required=True)
    cli.add_argument("--driver",type=Path)
    cli.add_argument("--preflight",action="store_true")
    main(cli.parse_args())
