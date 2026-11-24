"""Solve shared SB three-bet checked rivers; independently gate ranks229 and230."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL, proof
from hu_b568_caller_rivers import hand_cell
from hu_b637_rank57 import solve
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, game_reach
from hu_trainer_route_gate import compatible

MODELS={229:"ln-3bp-3b_r_model-16dlc3j",230:"ln-3bp-3b_r_model-jaiium"}
LINE="x x/x x/"
CASES={
    "Qd8s3h":["2c","5s","7d","Tc"],
    "Kc9d4h":["2s","6c","8h","Td"],
    "Jc7d4s":["2h","5c","8d","Th"],
    "Qh9c5d":["2s","4h","7c","Td"],
    "Td8c5h":["2s","4d","7h","9c"],
    "8h6c3d":["2s","4h","5c","7d"],
}
TARGETS={"Qd8s3h":229,"Kc9d4h":229,"Qh9c5d":229,
         "Jc7d4s":230,"Td8c5h":230,"8h6c3d":230}
DECK=[r+s for r in "23456789TJQKA" for s in "cdhs"]
ACTION={"過":"x","下注 ⅓":"b33","下注 ½":"b50","下注 ¾":"b75"}


def public_cards(public):
    return {public[i:i+2] for i in range(0,len(public),2)}


def decisions(root,sub,turn,rivers,routes):
    sub.update(line0="x x",turn=turn,rivers=rivers)
    masks=game_reach(root,sub)[0]
    nodes=[n for n in sub["nodes"] if (n["line"],n["player"])==(LINE,0)]
    assert {n["board"][-2:] for n in nodes}==set(rivers)
    result={rank:{} for rank in MODELS}
    for node in nodes:
        assert (node["pot"],node["bets"])==(2100,[0,0])
        row=proof(root,sub,node,masks)
        public=node["board"]
        bits=base64.b64decode(row["compatible_action_mask_b64"],validate=True)
        hands=sub["hands"][0]
        for rank in MODELS:
            route=routes[str(rank)]
            selected=[]
            for i,(hole,mask) in enumerate(zip(hands,bits,strict=True)):
                if not mask:continue
                hand="".join(cardkey(hole))
                cells=[hand_cell(hand,public[:end])[0] for end in (6,8,10)]
                if any(key not in route[street] for street,key in zip(("flop","turn","river"),cells,strict=True)):
                    continue
                label=route["river"][cells[-1]]
                native=ACTION[label]
                if native not in node["acts"] or not mask&(1<<node["acts"].index(native)):
                    continue
                selected.append(hand)
            if selected:
                result[rank][public]=dict(hands=sorted(selected),b50=row["b50"],
                    strict_legal_combos=row["strict_legal_combos"],
                    compatible_hole_card_pairs=row["compatible_hole_card_pairs"])
    return result


def run(args):
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    if args.driver:
        assert args.driver.resolve()==solver/"postflop/pfdriver/target/release/pfdriver"
        assert subprocess.check_output(["git","-C",solver/"postflop/postflop-solver","rev-parse","HEAD"],text=True).strip()==RUST
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    import ranges
    pool_raw=(solver/"inputs/pool_stats.json").read_bytes()
    assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)["NL2"]
    routes=json.loads(args.routes.read_bytes())
    registry=json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())["records"]
    contracts=json.loads(Path("data/nl2_hu_verified_extensions.json").read_bytes())["trainer_route_contract"]["routes"]
    for rank,mid in MODELS.items():
        model=registry[mid]
        assert (model["frequency_rank"],model["solver_profile"],model["family"])==(rank,"SB3_BTN","3BP")
        assert abs(9000/2100/model["assumed_model_node_spr"]-1)<=.05
        assert routes[str(rank)]["model"]==mid and contracts[mid]["seat"]==0
    flop=args.flop
    job=pipeline.make_job("SB3_BTN","gto",flop,"result.json",iters=1900,target=.45,compress=True)
    job.update(flop_oop="50%",flop_ip="50%",
        extract=[dict(prefix=[],street=True)]+[
            dict(prefix=["x","x",turn],street=False,raw=True) for turn in CASES[flop]])
    assert (job["pot"],job["stack"],job["rake_rate"],job["rake_cap"])==(2100,9000,.05,1000)
    assert (job["oop"],job["ip"])==tuple(ranges.to_str(w) for w in ranges.ranges("SB3_BTN","gto"))
    root=solve(args.output/"flop",job,args.driver)
    assert (root["flop"],root["pot"],root["stack"])==(flop,2100,9000)
    assert 0<=root["info"]["gto_expl_pct"]<=.5 and not root["info"].get("lock_stats")
    oop,=[n for n in root["nodes"] if (n["line"],n["player"])==("",0)]
    ip,=[n for n in root["nodes"] if (n["line"],n["player"])==("x",1)]
    checks=[accepted(n,root["hands"],"x") for n in (oop,ip)]
    report=dict(batch=676,flop=flop,spot="SB3_BTN",acting_seat=0,line=LINE,
        root_sha256=sha(compact(root)),strict_flop_checks=[len(s) for s in checks],
        root_pot_bb=21,root_effective_stack_bb=90,restricted_flop_open_sizes_pct=[50],
        lock_scope="FROZEN_GTO_FLOP_TURN_RIVER_PARTIAL_NL2_MARGINALS",
        target_rank=TARGETS[flop],turns=[],selected={str(TARGETS[flop]):None})
    for turn in CASES[flop]:
        boundary,=[n for n in root["nodes"] if n["line"]=="x x/" and n["board"].endswith(turn)]
        assert (boundary["pot"],boundary["bets"])==(2100,[0,0])
        pub=boundary["board"]
        compatible_heroes={h for h in checks[0] if turn not in h
            and any(turn not in v and set(h).isdisjoint(v) for v in checks[1])}
        eligible={rank:{h for h in compatible_heroes
            if hand_cell("".join(h),pub[:6])[0] in routes[str(rank)]["flop"]
            and hand_cell("".join(h),pub)[0] in routes[str(rank)]["turn"]} for rank in MODELS}
        rivers=[r for r in DECK if r not in public_cards(pub) and any(
            r not in h and hand_cell("".join(h),pub+r)[0] in routes[str(rank)]["river"]
            for rank in MODELS for h in eligible[rank])]
        record=dict(turn=turn,eligible_by_rank={str(rank):len(hs) for rank,hs in eligible.items()},
                    legal_rivers=len(rivers),paired_policies=False,checks={str(rank):[] for rank in MODELS})
        report["turns"].append(record)
        if not rivers:continue
        original=pipeline.make_job("SB3_BTN","gto",flop,"result.json",iters=2400,target=.4,compress=False)
        original.update(pipeline.SUB)
        original.update(oop="",ip="",turn=turn,pot=2100,stack=9000,line0=["x","x","/"],root_no_bet=False,
            turn_oop="33%,50%,75%",turn_ip="33%,50%,75%",river_oop="33%,50%,75%,100%,a",river_ip="33%,50%,75%,100%,a",
            extract=[dict(prefix=[],street=True)]+[dict(prefix=["x","x",r],street=True) for r in rivers])
        for seat,key in enumerate(("oop_w","ip_w")):
            original[key]=[[h,w] for h,w in zip(root["hands"][seat],boundary["wr"][seat],strict=True) if w>1e-4]
        gto=solve(args.output/(turn+"-gto"),original,args.driver)
        assert (gto["pot"],gto["stack"],gto["flop"])==(2100,9000,flop)
        assert 0<=gto["info"]["gto_expl_pct"]<=.5 and not gto["info"].get("lock_stats")
        before=decisions(root,gto,turn,rivers,routes)
        if not any(before.values()):continue
        locked_job,meta=prepare_job(dict(source=dict(version="gto",root=root,manifest=dict(spot="SB3_BTN")),job=original),
                                    "exp_oop",pool,pipeline)
        locked_job["out"]="result.json"
        locked=solve(args.output/(turn+"-exp_oop"),locked_job,args.driver)
        assert (locked["pot"],locked["stack"],locked["flop"])==(2100,9000,flop)
        assert locked["hands"]==gto["hands"]
        assert 0<=locked["info"]["gto_expl_pct"]<=.5 and 0<=locked["info"]["hero_gap_pct"]<=.5
        applied=audit_patterns(locked,locked_job,dict(locks=meta),pool,hero_seat=0)
        assert applied and locked["info"].get("lock_stats")
        after=decisions(root,locked,turn,rivers,routes)
        record["paired_policies"]=True
        for rank,mid in MODELS.items():
            for public in sorted(before[rank].keys() & after[rank].keys()):
                gr,er=before[rank][public],after[rank][public]
                common=sorted(set(gr["hands"]) & set(er["hands"]))
                if not common:continue
                assert compatible(contracts[mid],dict(public_board=public,actual_exact_action_line=LINE,acting_seat=0))
                check=dict(board=public,hands=common,gto_b50=gr["b50"],locked_b50=er["b50"],
                    gto_strict_combos=gr["strict_legal_combos"],locked_strict_combos=er["strict_legal_combos"],
                    gto_compatible_pairs=gr["compatible_hole_card_pairs"],locked_compatible_pairs=er["compatible_hole_card_pairs"])
                record["checks"][str(rank)].append(check)
                if rank==TARGETS[flop] and report["selected"][str(rank)] is None:
                    report["selected"][str(rank)]=dict(turn=turn,**check)
        if all(report["selected"].values()):break
    (args.output/"proof.json").write_bytes(json_bytes(report))
    print(json.dumps(dict(flop=flop,valid_models=[rank for rank,value in report["selected"].items() if value])))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ("solver","output","routes"):cli.add_argument("--"+key,type=Path,required=True)
    cli.add_argument("--flop",choices=CASES,required=True)
    cli.add_argument("--driver",type=Path)
    run(cli.parse_args())
