"""Solve six original checked-flop, half-pot turn-call river studies.

Only exact three-street UI paths and two-seat native policy witnesses count.
Every actor lock is rebuilt from pinned measured NL2 street marginals, with
unknown-history assumptions labelled separately from observed private hands.
"""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys

from hu_b463_rank45_gate import RUST,SOLVER
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE,POOL,RANGES,proof
from hu_b568_caller_rivers import hand_cell
from hu_b637_rank57 import solve
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted,cardkey,game_reach

MODELS={76:"ln-opfr-r_model-1phsqr4",89:"ln-ipfr-r_model-bqgbuq"}
CASES={
  76:{"8c6h3d":["2s","4c","5h"],"7h5d2c":["3s","4h","6c"],"9d6d4c":["2h","3s","5c"]},
  89:{"Kd8c4h":["8s","4d","Kh"],"Qs7h3d":["7c","3s","Qh"],"Jc6d2s":["6h","2c","Jh"]},
}
SPOTS={
  76:dict(oop="SB",ip="BB",oopc=[("SBrfi","open")],ipc=[("SBopen>BB","call")],pot=6.,stack=97.,pfr="oop",kind="SRP"),
  89:dict(oop="BB",ip="BTN",oopc=[("BTNopen>BB","call")],ipc=[("BTNrfi","open")],pot=5.5,stack=97.5,pfr="ip",kind="SRP"),
}
DECK=[r+s for r in "23456789TJQKA" for s in "cdhs"]
ACTION={"過":"x","下注 ⅓":"b33","下注 ½":"b50","下注 ¾":"b75"}
ROOT_MENU="33%,50%,75%"


def public_cards(board):
    return {board[i:i+2] for i in range(0,len(board),2)}


def make_root(rank,flop,c,pipeline):
    job=pipeline.make_job(c["spot"],"gto",flop,"result.json",iters=2300,target=.45,compress=True)
    job.update(flop_oop=ROOT_MENU,flop_ip=ROOT_MENU,extract=[dict(prefix=[],street=True)]+[
        dict(prefix=["x","x",t],street=False,raw=True) for t in CASES[rank][flop]])
    return job


def make_turn(root,turn,rivers,c,pipeline):
    parent,=(n for n in root["nodes"] if n["line"]=="x x/" and n["board"].endswith(turn))
    assert (parent["player"],parent["pot"],parent["bets"])==(0,c["pot"],[0,0])
    job=pipeline.make_job(c["spot"],"gto",root["flop"],"result.json",iters=2500,target=.4,rank=.4,compress=False)
    job.update(pipeline.SUB)
    job.update(oop="",ip="",pot=c["pot"],stack=c["stack"],turn=turn,line0=["x","x","/"],root_no_bet=False,
        turn_oop="33%,50%,75%,100%",turn_ip="33%,50%,75%,100%",
        river_oop="50%,75%,100%,a",river_ip="50%,75%,100%,a",
        extract=[dict(prefix=[],street=True)]+[
            dict(prefix=c["turn_line"].split()+[r],street=True) for r in rivers])
    for seat,key in enumerate(("oop_w","ip_w")):
        job[key]=[[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4]
    return job


def parent_candidates(root,turn,c):
    first,=(n for n in root["nodes"] if (n["line"],n["player"])==("",0))
    response,=(n for n in root["nodes"] if (n["line"],n["player"])==("x",1))
    boundary,=(n for n in root["nodes"] if n["line"]=="x x/" and n["board"].endswith(turn))
    assert all((n["board"],n["pot"],n["bets"])==(root["flop"],c["pot"],[0,0]) for n in (first,response))
    assert (boundary["player"],boundary["pot"],boundary["bets"])==(0,c["pot"],[0,0])
    public=boundary["board"];known=public_cards(public)
    assert len(known)==4 and known-{turn}==public_cards(root["flop"])
    native=[accepted(n,root["hands"],"x") for n in (first,response)]
    alive=[{cardkey(h) for h,w in zip(root["hands"][seat],boundary["wr"][seat],strict=True)
            if w>1e-4 and known.isdisjoint(cardkey(h))} for seat in (0,1)]
    check=[native[s]&alive[s] for s in (0,1)]
    actor=c["actor"];hero=check[actor];villain=check[1-actor];route=c["routes"]
    displayed={h for h in hero if hand_cell("".join(h),public[:6])[0] in route["flop"]
               and hand_cell("".join(h),public)[0] in route["turn"]}
    shared={h for h in displayed if any(set(h).isdisjoint(v) for v in villain)}
    eligible=[r for r in DECK if r not in known and any(
        r not in h and hand_cell("".join(h),public+r)[0] in route["river"]
        and any(r not in v and set(h).isdisjoint(v) for v in villain) for h in shared)]
    # Fix the exported river set before solving its turn/river strategies.
    rivers=eligible if len(eligible)<=16 else [eligible[round(i*(len(eligible)-1)/15)] for i in range(16)]
    assert len(rivers)==len(set(rivers))
    stats=dict(public_board=public,strict_flop_checks=[len(s) for s in native],
        positive_boundary_checks=[len(s) for s in check],displayed_parent_hands=len(displayed),
        compatible_displayed_parent_hands=len(shared),legal_river_candidates=len(eligible),river_extracts=rivers)
    return stats,rivers


def decisions(root,game,turn,rivers,c):
    game.update(line0="x x",turn=turn,rivers=rivers)
    masks=game_reach(root,game)[0];actor=c["actor"]
    targets=[n for n in game["nodes"] if (n["line"],n["player"])==(c["line"],actor)]
    assert {n["board"][-2:] for n in targets}==set(rivers)
    result={};route=c["routes"];bet=(c["pot"]*50+50)//100
    for node in targets:
        assert (node["pot"],node["bets"])==(c["river_pot"],[bet,bet])
        assert game["stack"]-max(node["bets"])==c["river_stack"]
        row=proof(root,game,node,masks);public=node["board"]
        bits=base64.b64decode(row["compatible_action_mask_b64"],validate=True);found={}
        for hole,mask in zip(game["hands"][actor],bits,strict=True):
            if not mask:continue
            hand="".join(cardkey(hole));cells=[hand_cell(hand,public[:n]) for n in (6,8,10)]
            if any(cell[0] not in route[street] for street,cell in zip(("flop","turn","river"),cells,strict=True)):continue
            label=route["river"][cells[-1][0]];action=ACTION[label]
            if action not in node["acts"] or not mask&(1<<node["acts"].index(action)):continue
            found[hand]=dict(classes=[cell[1] for cell in cells],displayed_suggestion=label,
                accepted_actions=[a for i,a in enumerate(node["acts"]) if mask&(1<<i)])
        result[public]=dict(hands=found,proof=row)
    return result


def run(args):
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    assert sha((solver/"postflop/py/pipeline.py").read_bytes())==PIPELINE
    assert sha((solver/"postflop/py/ranges.py").read_bytes())==RANGES
    if args.driver:
        assert args.driver.resolve()==solver/"postflop/pfdriver/target/release/pfdriver"
        assert subprocess.check_output(["git","-C",solver/"postflop/postflop-solver","rev-parse","HEAD"],text=True).strip()==RUST
    sys.path.insert(0,str(solver/"postflop/py"));import pipeline,ranges
    pool_raw=(solver/"inputs/pool_stats.json").read_bytes();assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)["NL2"];rank=args.rank;flop=args.flop
    assert flop in CASES[rank]
    route_raw=args.routes.read_bytes();c=json.loads(route_raw)[str(rank)]
    assert c["id"]==MODELS[rank] and c["turn_call_pct"]==50
    assert (c["spot"],c["actor"],c["pot"],c["stack"],c["river_pot"],c["river_stack"],c["line"])==(
        ("SB_BB",0,600,9700,1200,9400,"x x/x b50 c/") if rank==76 else
        ("BTN_BB",1,550,9750,1100,9475,"x x/b50 c/x"))
    assert abs(c["river_stack"]/c["river_pot"]/c["spr"]-1)<.001
    assert ranges.SPOTS[c["spot"]]==SPOTS[rank]
    job=make_root(rank,flop,c,pipeline)
    assert (job["pot"],job["stack"],job["rake_rate"],job["rake_cap"])==(c["pot"],c["stack"],.05,1000)
    assert (job["oop"],job["ip"])==tuple(ranges.to_str(w) for w in ranges.ranges(c["spot"],"gto"))
    assert not job.get("locks") and job.get("hero") is None
    root=solve(args.output/"flop",job,args.driver)
    assert (root["flop"],root["pot"],root["stack"])==(flop,c["pot"],c["stack"])
    assert 0<=root["info"]["gto_expl_pct"]<=.5 and not root["info"].get("lock_stats")
    report=dict(schema="NL2_B696_TURN_CALL_ORIGINAL_WORKER_V1",rank=rank,model_id=c["id"],spot=c["spot"],
        flop=flop,actor=c["actor"],line=c["line"],solver=SOLVER,rust=RUST,pipeline_sha256=PIPELINE,ranges_sha256=RANGES,
        pool_sha256=POOL,route_sha256=sha(route_raw),root_sha256=sha((args.output/"flop/result.json").read_bytes()),
        root_job_sha256=sha(compact(job)),root_pot=c["pot"],root_stack=c["stack"],
        river_pot=c["river_pot"],river_stack=c["river_stack"],restricted_flop_sizes_pct=[33,50,75],
        lock_scope="FROZEN_GTO_FLOP_TURN_RIVER_PARTIAL_NL2_MARGINALS",turns=[],selected=None,
        river_export_policy="UP_TO_16_EVENLY_SPACED_UI_LEGAL_CARDS_BEFORE_TURN_SOLVE",
        not_a_certification=True,no_observed_per_private_hand_NL2_frequencies=True)
    for turn in CASES[rank][flop]:
        stats,rivers=parent_candidates(root,turn,c)
        record=dict(turn=turn,parent_gate=stats,paired_policies=False,gto_boards=[],nl2_boards=[],common=[])
        report["turns"].append(record)
        if not rivers:continue
        original=make_turn(root,turn,rivers,c,pipeline)
        gto=solve(args.output/(turn+"-gto"),original,args.driver)
        assert (gto["flop"],gto["pot"],gto["stack"])==(flop,c["pot"],c["stack"])
        assert 0<=gto["info"]["gto_expl_pct"]<=.5 and not gto["info"].get("lock_stats")
        before=decisions(root,gto,turn,rivers,c)
        record.update(gto_source_sha256=sha((args.output/(turn+"-gto/result.json")).read_bytes()),
            gto_job_sha256=sha(compact(original)),gto_boards=[
                dict(public_board=b,displayed_hands=len(v["hands"]),reach=v["proof"]) for b,v in sorted(before.items())])
        if not any(v["hands"] for v in before.values()):continue
        version="exp_ip" if c["actor"] else "exp_oop"
        locked_job,rules=prepare_job(dict(source=dict(version="gto",root=root,manifest=dict(spot=c["spot"])),job=original),version,pool,pipeline)
        locked_job["out"]="result.json"
        locked=solve(args.output/(turn+"-"+version),locked_job,args.driver)
        assert (locked["flop"],locked["pot"],locked["stack"])==(flop,c["pot"],c["stack"])
        assert locked["hands"]==gto["hands"] and locked_job["hero"]==c["actor"]
        assert 0<=locked["info"]["gto_expl_pct"]<=.5 and 0<=locked["info"]["hero_gap_pct"]<=.5
        applied=audit_patterns(locked,locked_job,dict(locks=rules),pool,c["actor"])
        assert any(n>0 for pat,n in applied["driver_tree_nodes"].items() if pat in applied["marginal_targets"])
        after=decisions(root,locked,turn,rivers,c)
        record.update(paired_policies=True,nl2_source_sha256=sha((args.output/(turn+"-"+version)/"result.json").read_bytes()),
            nl2_job_sha256=sha(compact(locked_job)),measured_lock_application=applied,
            nl2_boards=[dict(public_board=b,displayed_hands=len(v["hands"]),reach=v["proof"]) for b,v in sorted(after.items())])
        for public in sorted(before.keys()&after.keys()):
            gh,eh=before[public]["hands"],after[public]["hands"];common=sorted(gh.keys()&eh.keys())
            if not common:continue
            match=dict(public_board=public,hands=common,gto_witnesses={h:gh[h] for h in common},nl2_witnesses={h:eh[h] for h in common},
                gto_b50=before[public]["proof"]["b50"],nl2_b50=after[public]["proof"]["b50"])
            record["common"].append(match)
            if report["selected"] is None:report["selected"]=dict(turn=turn,**match)
        if report["selected"] is not None:break
    report["positive_distinct_flops"]=int(report["selected"] is not None)
    (args.output/"rendered-routes.json").write_bytes(route_raw)
    (args.output/"proof.json").write_bytes(json_bytes(report))
    print(json.dumps(dict(rank=rank,flop=flop,positive=report["positive_distinct_flops"],
        nl2_locked_turns=sum(t["paired_policies"] for t in report["turns"]))))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for field in ("solver","routes","output"):cli.add_argument("--"+field,type=Path,required=True)
    cli.add_argument("--rank",type=int,choices=CASES,required=True);cli.add_argument("--flop",required=True)
    cli.add_argument("--driver",type=Path)
    run(cli.parse_args())

