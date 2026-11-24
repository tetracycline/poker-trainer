"""Native BB3/BTN check-call turns, with strict root/UI diagnostics before solving.

The original root is 20.5bb/90bb. The 33% bet rounds to 677 chips,
so the turn root is 3404/8323. No worker result is a certificate.
"""
import argparse
import base64
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b536_sb_barrels import tx
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b637_rank57 import solve
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, game_reach

sys.path.insert(0,str(Path(__file__).resolve().parent/"lines_pipeline"))
from run10_common import hcls

MODEL="ln-3bp-3b_t_model-yap927"
FLOP_LINE="x b33 c"
LINE=FLOP_LINE+"/"
CASES={
    "Jc9h7d":["2s","3c","4h","6s"],
    "Ts8s6h":["2c","3h","4d","5c"],
    "9c7d5h":["2s","3c","4h","8s"],
}
ACTIONS={"過":"x","下注 ⅓":"b33","下注 ½":"b50","下注 ¾":"b75"}


def root_job(flop,pipeline):
    job=pipeline.make_job("BB3_BTN","gto",flop,"result.json",iters=2200,target=.4,compress=True)
    job.update(flop_oop="33%",flop_ip="33%",
        extract=[dict(prefix=[],street=True)]+[
            dict(prefix=["x","b33","c",turn],street=False,raw=True) for turn in CASES[flop]])
    return job


def turn_job(root,turn,pipeline):
    parent,=[n for n in root["nodes"] if n["line"]==LINE and n["board"].endswith(turn)]
    assert (parent["player"],parent["pot"],parent["bets"])==(0,3404,[677,677])
    job=pipeline.make_job("BB3_BTN","gto",root["flop"],"result.json",iters=2300,target=.4,rank=.4,compress=False)
    job.update(pipeline.SUB)
    job.update(oop="",ip="",pot=3404,stack=8323,turn=turn,line0=["x","b33","c","/"],root_no_bet=False,
        turn_oop="33%,50%,75%,100%",turn_ip="33%,50%,75%,100%",
        river_oop="50%,75%,100%,a",river_ip="50%,75%,100%,a",extract=[dict(prefix=[],street=True)])
    for seat,key in enumerate(("oop_w","ip_w")):
        job[key]=[[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4]
    return job


def root_gate(root,turn,route):
    first,=[n for n in root["nodes"] if n["line"]==""]
    bet,=[n for n in root["nodes"] if n["line"]=="x"]
    call,=[n for n in root["nodes"] if n["line"]=="x b33"]
    assert (first["player"],first["pot"],first["bets"])==(0,2050,[0,0])
    assert (bet["player"],bet["pot"],bet["bets"])==(1,2050,[0,0])
    assert (call["player"],call["pot"],call["bets"])==(0,2727,[0,677])
    checks=accepted(first,root["hands"],"x")
    bets=accepted(bet,root["hands"],"b33")
    calls=accepted(call,root["hands"],"c")
    parent,=[n for n in root["nodes"] if n["line"]==LINE and n["board"].endswith(turn)]
    public=parent["board"]
    dead={public[i:i+2] for i in range(0,8,2)}
    weighted=[{cardkey(h) for h,w in zip(root["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4}
        for seat in (0,1)]
    actors={h for h in checks&calls&weighted[0] if dead.isdisjoint(h)}
    opponents={h for h in bets&weighted[1] if dead.isdisjoint(h)}
    pairs={h:sum(set(h).isdisjoint(v) for v in opponents) for h in actors}
    joint={h for h,n in pairs.items() if n}
    flop_ui=route["routes"].get(tx(public[:6]),{}).get("parents",[])
    turn_ui=route["routes"].get(tx(public),{}).get("decisions",{})
    matching={h for h in joint if hcls("".join(h),public[:6]) in flop_ui and hcls("".join(h),public) in turn_ui}
    return dict(oop_check_combos=len(checks),oop_call_combos=len(calls),ip_b33_combos=len(bets),
        oop_check_call_intersection=len(checks&calls),turn_compatible_hero_combos=len(joint),
        turn_compatible_pairs=sum(pairs.values()),rendered_mid_hero_combos=len(matching),
        rendered_mid_hands=sorted("".join(h) for h in matching))


def decision(root,game,turn,route):
    game.update(line0=FLOP_LINE,turn=turn,rivers=[])
    node,=[n for n in game["nodes"] if (n["line"],n["player"])==(LINE,0)]
    assert (node["pot"],node["bets"])==(3404,[0,0])
    row=proof(root,game,node,game_reach(root,game)[0])
    masks=base64.b64decode(row["compatible_action_mask_b64"],validate=True)
    public=node["board"]
    flop_ui=route["routes"].get(tx(public[:6]),{}).get("parents",[])
    turn_ui=route["routes"].get(tx(public),{}).get("decisions",{})
    diagnostic=dict(strict_hero_combos=row["strict_legal_combos"],
        compatible_pairs=row["compatible_hole_card_pairs"],flop_ui_combos=0,turn_ui_combos=0,
        displayed_action_combos=0,flop_classes={},turn_classes={})
    fclasses=Counter();tclasses=Counter();eligible={}
    for i,(hole,bits) in enumerate(zip(game["hands"][0],masks,strict=True)):
        if not bits:continue
        fc,tc=hcls(hole,public[:6]),hcls(hole,public)
        fclasses[fc]+=1;tclasses[tc]+=1
        if fc not in flop_ui:continue
        diagnostic["flop_ui_combos"]+=1
        label=turn_ui.get(tc)
        if label is None:continue
        diagnostic["turn_ui_combos"]+=1
        action=ACTIONS[label]
        if action not in node["acts"] or not bits&(1<<node["acts"].index(action)):continue
        diagnostic["displayed_action_combos"]+=1
        weights=[max(0,node["strat"][a*len(masks)+i]) for a in range(len(node["acts"]))]
        total=sum(weights);assert total>0
        eligible["".join(cardkey(hole))]=dict(flop_class=fc,turn_class=tc,displayed_suggestion=label,
            action_order=node["acts"],accepted_mask=bits,
            accepted_actions=[a for k,a in enumerate(node["acts"]) if bits&(1<<k)],
            strategy={a:round(w/total,7) for a,w in zip(node["acts"],weights,strict=True)})
    diagnostic["flop_classes"]=dict(fclasses);diagnostic["turn_classes"]=dict(tclasses)
    return row,eligible,diagnostic


def run(args):
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    assert sha((solver/"postflop/py/pipeline.py").read_bytes())==PIPELINE
    assert sha((solver/"postflop/py/ranges.py").read_bytes())==RANGES
    if args.driver:
        assert args.driver.resolve()==solver/"postflop/pfdriver/target/release/pfdriver"
        assert subprocess.check_output(["git","-C",solver/"postflop/postflop-solver","rev-parse","HEAD"],text=True).strip()==RUST
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline,ranges
    pool_raw=(solver/"inputs/pool_stats.json").read_bytes();assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)["NL2"]
    route=json.loads(args.routes.read_bytes())
    assert (route["rank"],route["id"],route["line"],route["spot"],route["seat"])==(121,MODEL,LINE,"BB3_BTN",0)
    assert (route["root_pot"],route["root_stack"],route["flop_bet"],route["turn_pot"],route["turn_stack"])==(2050,9000,677,3404,8323)
    assert abs(8323/3404/route["spr"]-1)<.001
    assert len({suit_isomorphism_class(f) for f in CASES})==3
    job=root_job(args.flop,pipeline)
    assert (job["pot"],job["stack"],job["rake_rate"],job["rake_cap"])==(2050,9000,.05,1000)
    assert (job["oop"],job["ip"])==tuple(ranges.to_str(w) for w in ranges.ranges("BB3_BTN","gto"))
    root=solve(args.output/"flop",job,args.driver)
    assert (root["flop"],root["pot"],root["stack"])==(args.flop,2050,9000)
    assert 0<=root["info"]["gto_expl_pct"]<=.5 and not root["info"].get("lock_stats")
    attempts=[]
    for turn in CASES[args.flop]:
        gate=root_gate(root,turn,route)
        record=dict(turn=turn,root_gate=gate,gto_solved=False,paired=False,shared_hands=[],
            negative_stage="ROOT_TWO_SEAT_UI_INTERSECTION_ZERO")
        attempts.append(record)
        if not gate["rendered_mid_hero_combos"]:continue
        gto_job=turn_job(root,turn,pipeline)
        gto=solve(args.output/(turn+"-gto"),gto_job,args.driver)
        assert (gto["flop"],gto["pot"],gto["stack"])==(args.flop,3404,8323)
        assert 0<=gto["info"]["gto_expl_pct"]<=.5 and not gto["info"].get("lock_stats")
        before,gh,gd=decision(root,gto,turn,route)
        record.update(gto_solved=True,public_board=before["public_board"],
            gto_sha256=sha((args.output/(turn+"-gto")/"result.json").read_bytes()),
            gto_diagnostic=gd,gto_rendered_hands=len(gh),gto_reach=before["strict_legal_combos"],
            gto_compatible_pairs=before["compatible_hole_card_pairs"],gto_b50=before["b50"],
            negative_stage="GTO_TURN_RENDERED_ACTION_INTERSECTION_ZERO")
        if not gh:continue
        locked_job,rules=prepare_job(dict(source=dict(version="gto",root=root,manifest=dict(spot="BB3_BTN")),job=gto_job),
            "exp_oop",pool,pipeline)
        locked_job["out"]="result.json"
        locked=solve(args.output/(turn+"-exp_oop"),locked_job,args.driver)
        assert (locked["flop"],locked["pot"],locked["stack"])==(args.flop,3404,8323)
        assert locked["hands"]==gto["hands"]
        assert 0<=locked["info"]["gto_expl_pct"]<=.5 and 0<=locked["info"]["hero_gap_pct"]<=.5
        measured=audit_patterns(locked,locked_job,dict(locks=rules),pool,hero_seat=0)
        assert measured and locked["info"].get("lock_stats")
        after,eh,ed=decision(root,locked,turn,route)
        common=sorted(gh.keys()&eh.keys())
        for hand in common:
            for key in ("flop_class","turn_class","displayed_suggestion"):assert gh[hand][key]==eh[hand][key]
        record.update(paired=True,nl2_sha256=sha((args.output/(turn+"-exp_oop")/"result.json").read_bytes()),
            nl2_diagnostic=ed,nl2_rendered_hands=len(eh),nl2_reach=after["strict_legal_combos"],
            nl2_compatible_pairs=after["compatible_hole_card_pairs"],nl2_b50=after["b50"],
            measured_lock_application=measured,shared_hands=common,
            gto_witnesses={h:gh[h] for h in common},nl2_witnesses={h:eh[h] for h in common},
            negative_stage=None if common else "GTO_NL2_RENDERED_HAND_INTERSECTION_ZERO")
        if common:break
    report=dict(schema="NL2_B686_R121_ORIGINAL_WORKER_V1",rank=121,model_id=MODEL,flop=args.flop,line=LINE,
        root_sha256=sha((args.output/"flop/result.json").read_bytes()),root_job_sha256=sha(compact(job)),
        solver=SOLVER,rust=RUST,pipeline_sha256=PIPELINE,ranges_sha256=RANGES,pool_sha256=POOL,
        root_pot=2050,root_stack=9000,pot=3404,stack=8323,actor=0,
        restricted_flop_oop_sizes_pct=[33],restricted_flop_ip_sizes_pct=[33],
        pricing_scope="PINNED_B674_EXPLICIT_33_PERCENT_CHECK_CALL_MODEL",
        lock_scope="FROZEN_GTO_FLOP_TURN_RIVER_PARTIAL_NL2_MARGINALS",
        rendered_routes_sha256=sha(args.routes.read_bytes()),positive_distinct_flops=int(any(r["shared_hands"] for r in attempts)),
        turns=attempts,not_a_certification=True,no_observed_per_hole_card_NL2_frequencies=True)
    (args.output/"proof.json").write_bytes(json_bytes(report))
    (args.output/"rendered-routes.json").write_bytes(args.routes.read_bytes())
    print(json.dumps(dict(flop=args.flop,positive_distinct_flops=report["positive_distinct_flops"],
        gto_turns=sum(r["gto_solved"] for r in attempts),locked_turns=sum(r["paired"] for r in attempts))))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ("solver","output","routes"):cli.add_argument("--"+key,type=Path,required=True)
    cli.add_argument("--flop",choices=CASES,required=True)
    cli.add_argument("--driver",type=Path)
    run(cli.parse_args())

