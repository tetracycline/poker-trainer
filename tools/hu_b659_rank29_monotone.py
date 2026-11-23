"""Solve a BB half-pot lead and consecutive three-quarter barrels on monotone flops."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b481_rank27_limp_rivers import check_limp_source
from hu_b483_locked_medium import POOL, proof
from hu_b582_rank29_reach import DECK, LINE, cards, rendered
from hu_b637_rank57 import solve
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, game_reach
from hu_trainer_route_gate import compatible

MODEL = "ln-iso-lmp_r_model-gifggm"
CASES = {
    "8s5s2s": ["3h","4c","6h","7c","9d","Th","Qd","Ac"],
    "7h4h2h": ["3d","5c","6d","8c","9s","Ts","Qd","Ac"],
    "9d6d3d": ["2c","4s","5c","7h","8c","Ts","Qh","As"],
    "As8s3s": ["2h","4c","5h","6d","7c","9d","Th","Qc"],
}


def eligible_by_river(parent, route, flop_hands, callers):
    public = parent["board"]
    turn = public[-2:]
    survivors = [h for h in flop_hands if turn not in cards(h) and rendered(h,public,"turn",route)]
    legal = {}
    for river in DECK:
        if river in cards(public):
            continue
        hands = {h for h in survivors if river not in cards(h) and rendered(h,public+river,"river",route)
                 and any(set(v).isdisjoint(cards(h)|{turn,river}) for v in callers)}
        if hands:
            legal[river] = hands
    return legal


def played(root, sub, turn, legal):
    sub.update(line0="b50 c", turn=turn, rivers=list(legal))
    masks = game_reach(root,sub)[0]
    positive = {}
    targets = [node for node in sub["nodes"] if (node["line"],node["player"]) == (LINE,0)]
    assert {n["board"][-2:] for n in targets} == set(legal)
    for node in targets:
        public = node["board"]
        assert (node["pot"],node["bets"]) == (1250,[375,375])
        row = proof(root,sub,node,masks)
        bits = base64.b64decode(row["compatible_action_mask_b64"],validate=True)
        action = 1 << node["acts"].index("b75")
        hands = {"".join(cardkey(h)) for h,m in zip(sub["hands"][0],bits,strict=True) if m & action}
        common = sorted(hands & legal[public[-2:]])
        if common:
            positive[public] = (common,row["b50"])
    return positive


def run(args):
    solver = args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip() == SOLVER
    if args.driver:
        assert args.driver.resolve() == solver/"postflop/pfdriver/target/release/pfdriver"
        assert subprocess.check_output(["git","-C",solver/"postflop/postflop-solver","rev-parse","HEAD"],text=True).strip() == RUST
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    raw = (solver/"inputs/pool_stats.json").read_bytes()
    assert sha(raw)==POOL
    pool = json.loads(raw)["NL2"]
    template = EVIDENCE/"NL2_B580_R27_LMP.zip"
    assert sha(template.read_bytes()) == "d4b98b4351012d78aa62f3cd31b75228d4f7a35725584d86f633552fbf28369a"
    with ZipFile(template) as z:
        root_job,turn_job,manifest = [json.loads(z.read(n)) for n in ("original-flop.job.json","original-turn.job.json","original-manifest.json")]
    route = json.loads(subprocess.check_output(["node","tools/hu_b582_rank29_route.cjs"]))
    assert route["river"] == {"mono:0":"下注 ¾"}
    contract = json.loads(Path("data/nl2_hu_verified_extensions.json").read_bytes())["trainer_route_contract"]["routes"][MODEL]
    flop = args.flop
    turns = CASES[flop]
    root_job.update(flop=flop,out="result.json",extract=[dict(prefix=[],street=True)]+[
        dict(prefix=["b50","c",t],street=False,raw=True) for t in turns])
    check_limp_source(dict(manifest=manifest,root_job=root_job,subgame_job=None))
    root = solve(args.output/"flop",root_job,args.driver)
    assert (root["flop"],root["pot"],root["stack"])==(flop,250,9900)
    assert 0 <= root["info"]["gto_expl_pct"] <= .5 and not root["info"].get("lock_stats")
    lead, = [n for n in root["nodes"] if n["line"]==""]
    call, = [n for n in root["nodes"] if n["line"]=="b50"]
    assert (lead["player"],lead["pot"],call["player"],call["pot"])==(0,250,1,375)
    public = lead["board"]
    heroes = ["".join(h) for h in accepted(lead,root["hands"],"b50") if rendered("".join(h),public,"flop",route)]
    callers = accepted(call,root["hands"],"c")
    tested = []
    for turn in turns:
        parent, = [n for n in root["nodes"] if n["line"]=="b50 c/" and n["board"]==public+turn]
        assert (parent["pot"],parent["bets"]) == (500,[125,125])
        legal = eligible_by_river(parent,route,heroes,callers)
        record = dict(turn=turn,legal_rivers=len(legal),paired_policies=False,checks=[])
        tested.append(record)
        if not legal:
            continue
        job = dict(turn_job,flop=flop,turn=turn,out="result.json",turn_oop="75%",turn_ip="50%,100%",
                   river_oop="50%,75%,100%,a",river_ip="50%,75%,100%,a",target_pct=.45,iters=2000,
                   extract=[dict(prefix=[],street=True)]+[dict(prefix=["b75","c",r],street=False) for r in legal])
        for seat,k in enumerate(("oop_w","ip_w")):
            job[k] = [[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4]
        gto = solve(args.output/(turn+"-gto"),job,args.driver)
        assert (gto["flop"],gto["pot"],gto["stack"])==(flop,500,9775)
        assert 0 <= gto["info"]["gto_expl_pct"] <= .5 and not gto["info"].get("lock_stats")
        original = played(root,gto,turn,legal)
        if not original:
            continue
        locked_job,rules = prepare_job(dict(source=dict(version="gto",root=root,manifest=manifest),job=job),"exp_oop",pool,pipeline)
        locked_job["out"] = "result.json"
        locked = solve(args.output/(turn+"-exp_oop"),locked_job,args.driver)
        assert (locked["flop"],locked["pot"],locked["stack"]) == (flop,500,9775)
        assert 0<=locked["info"]["gto_expl_pct"]<=.5 and 0<=locked["info"]["hero_gap_pct"]<=.5
        audit_patterns(locked,locked_job,dict(manifest,locks=rules),pool,0)
        paired = played(root,locked,turn,legal)
        record["paired_policies"] = True
        for board in sorted(original.keys() & paired.keys()):
            hands = sorted(set(original[board][0]) & set(paired[board][0]))
            if hands:
                assert compatible(contract,dict(public_board=board,actual_exact_action_line=LINE,acting_seat=0))
                record["checks"].append(dict(board=board,hands=hands,gto_b50=original[board][1],locked_b50=paired[board][1]))
        if record["checks"]:
            break
    report = dict(rank=29,model_id=MODEL,flop=flop,root_sha256=sha(compact(root)),line=LINE,
                  actual_river_spr=7.52,eligible_flop_hands=len(heroes),turns=tested)
    (args.output/"proof.json").write_bytes(json_bytes(report))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("solver","output"):
        parser.add_argument("--"+name,type=Path,required=True)
    parser.add_argument("--driver",type=Path)
    parser.add_argument("--flop",choices=CASES,required=True)
    run(parser.parse_args())
