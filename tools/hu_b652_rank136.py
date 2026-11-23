"""Verify BTN missed-draw river checks after an exact 75% flop c-bet and checked turn."""
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile, ZIP_DEFLATED

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b483_locked_medium import POOL, proof
from hu_b527_checked_barrels import board_row
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, game_reach

sys.path.insert(0,str(Path(__file__).resolve().parent/"lines_pipeline"))
from run10_common import classes,hcls

MODEL="ln-ipfr-r_model-mbe4f"
LINE="x b75 c/x x/x"
FLOPS={
    "Ah7d4c":"2s 3d 5h 6c 8s 9d Tc Jc Qs Ks",
    "Ac8h5d":"2s 3c 4h 6d 7s 9c Th Jd Qs Ks",
    "Ad9c6h":"2s 3c 4h 5d 7s 8c Th Jd Qs Ks",
    "As6c3h":"2d 4s 5h 7d 8c 9h Tc Js Qd Ks",
    "Ah8d4s":"2c 3d 5h 6s 7c 9d Tc Js Qd Ks",
    "Ac7h3d":"2s 4c 5h 6d 8s 9c Th Jd Qs Ks",
}


def root_job(flop,pipeline):
    turns=FLOPS[flop].split()
    job=pipeline.make_job("BTN_BB","gto",flop,"root.json",iters=1900,target=.45,compress=True,
        extract=[dict(prefix=[],street=True)]+[dict(prefix=["x","b75","c",t],street=False,raw=True) for t in turns])
    job.update(flop_oop="50%",flop_ip="75%")
    return job


def jobs(root,parent,rivers,pipeline,pool):
    assert (root["pot"],root["stack"],parent["pot"],parent["bets"])==(550,9750,1376,[413,413])
    job=pipeline.make_job("BTN_BB","gto",root["flop"],"gto.json",iters=2000,target=.45,rank=.45,compress=False)
    job.update(pipeline.SUB)
    job.update(oop="",ip="",pot=1376,stack=9337,line0=["x","b75","c","/"],turn=parent["board"][-2:],
               root_no_bet=True,extract=[dict(prefix=[],street=True)]+[dict(prefix=["x","x",r],street=True) for r in rivers])
    for seat,k in enumerate(("oop_w","ip_w")):
        job[k]=[[hand,w] for hand,w in zip(root["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4]
    lock,meta=prepare_job(dict(source=dict(root=root,version="gto",manifest=dict(spot="BTN_BB")),job=job),"exp_ip",pool,pipeline)
    return job,lock,meta


def candidates(root,parent,allowed):
    """Use only original flop actions and structural trainer cells to order rivers."""
    flop,public=root["flop"],parent["board"]
    source,=(n for n in root["nodes"] if n["line"]=="x" and len(n["board"])==6)
    flop_hands=accepted(source,root["hands"],"b75")
    holes=[h for h in flop_hands if hcls("".join(h),flop) in allowed and hcls("".join(h),public)=="WDRAW"
           and not set(h)&{public[i:i+2] for i in range(0,8,2)}]
    count=[]
    for r in (v+s for v in "23456789TJQKA" for s in "cdhs"):
        if r in public or board_row(public+r)!="A_high":continue
        n=sum(r not in h and classes("".join(h),public+r)[0]=="WDRAW" for h in holes)
        if n:count.append((-n,r))
    return len(holes),[r for _,r in sorted(count)[:8]]


def replay_hands(root,sub,turn,rivers,route):
    sub.update(line0="x b75 c",turn=turn,rivers=rivers)
    masks=game_reach(root,sub)[0]
    results={}
    nodes=[n for n in sub["nodes"] if n["line"]==LINE and n["player"]==1]
    assert {n["board"][-2:] for n in nodes}==set(rivers)
    for n in nodes:
        board=n["board"]
        assert n["pot"]==1376 and n["bets"]==[0,0] and {"x","b50"}<=set(n["acts"])
        row=proof(root,sub,n,masks)
        legal=base64.b64decode(row["compatible_action_mask_b64"],validate=True)
        choice=1<<n["acts"].index("x")
        hands=set()
        for hand,bits in zip(sub["hands"][1],legal,strict=True):
            if not bits&choice:continue
            fc,tc,rc=hcls(hand,board[:6]),hcls(hand,board[:8]),classes(hand,board)[0]
            if fc in route[0] and tc==rc=="WDRAW" and all(board_row(board[:k])=="A_high" for k in (6,8,10)):
                hands.add("".join(cardkey(hand)))
        if hands:results[board]=(hands,row)
    return results


def native(folder,job,driver,threads):
    name=job["out"][:-5]+".job.json"
    (folder/name).write_bytes(compact(job))
    subprocess.run([str(driver),name],cwd=folder,check=True,env=dict(os.environ,RAYON_NUM_THREADS=str(threads)))
    result=json.loads((folder/job["out"]).read_bytes())
    assert 0<=result["info"]["gto_expl_pct"]<=.45
    if job.get("hero") is not None:assert 0<=result["info"]["hero_gap_pct"]<=.45 and result["info"]["lock_stats"]
    else:assert not result["info"].get("lock_stats")
    return result


def read_route():
    view=json.loads(subprocess.check_output(["node","tools/hu_b652_rank136_routes.cjs"]))["136"]
    assert view["id"]==MODEL and view["flop"]==["A_high:0","A_high:3","A_high:4"]
    assert view["turn"]==["A_high:4"] and view["river"]=={"A_high:4":"過"}
    return ({"TPG","DRAW","WDRAW"},"WDRAW","WDRAW")


def run(args):
    solver=args.solver.resolve()
    for path, revision in ((solver, SOLVER), (solver / "postflop/postflop-solver", RUST)):
        assert subprocess.check_output(["git", "-C", path, "rev-parse", "HEAD"], text=True).strip() == revision
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    driver=solver/"postflop/pfdriver/target/release/pfdriver"
    pool_raw=(solver/"inputs/pool_stats.json").read_bytes()
    assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)["NL2"]
    route=read_route()
    output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    setup=root_job(args.flop,pipeline)
    root=native(output,setup,driver,2)
    options=[]
    for t in FLOPS[args.flop].split():
        parent,=(n for n in root["nodes"] if n["line"]=="x b75 c/" and n["board"].endswith(t))
        size,rivers=candidates(root,parent,route[0])
        if size and rivers:options.append((-size,t,rivers,parent))
    report=dict(rank=136,model_id=MODEL,flop=args.flop,run=args.run,turns=[],selected=None)
    for _,turn,rivers,parent in sorted(options):
        a,b,meta=jobs(root,parent,rivers,pipeline,pool)
        policies=[]
        for job in (a,b):
            game=native(output,job,driver,1)
            policies.append(replay_hands(root,game,turn,rivers,route))
            if not policies[-1]:break
        matches=[]
        if len(policies)==2:
            g,l=policies
            for public in sorted(g.keys()&l.keys()):
                hands=sorted(g[public][0]&l[public][0])
                if hands:matches.append(dict(board=public,hands=hands,compatible_pairs=[g[public][1]["compatible_hole_card_pairs"],l[public][1]["compatible_hole_card_pairs"]],locked_half_pot=l[public][1]["b50"]))
        report["turns"].append(dict(turn=turn,checked_rivers=rivers,shared_rivers=len(matches)))
        if matches:
            report["selected"]=dict(turn=turn,rivers=rivers,**matches[0])
            break
    (output/"proof.json").write_bytes(json_bytes(report))
    with ZipFile(output/"source.zip","w",compression=ZIP_DEFLATED) as z:
        files=["root.job.json","root.json","proof.json"]
        if report["selected"]:files.extend(["gto.job.json","gto.json","native.job.json","native.json"])
        for f in files:z.write(output/f,f)
    print(args.flop, "shared hands",len((report["selected"] or {}).get("hands",[])))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--solver",type=Path,required=True)
    cli.add_argument("--flop",choices=FLOPS,required=True)
    cli.add_argument("--run",type=int,required=True)
    cli.add_argument("--output",type=Path,required=True)
    args=cli.parse_args()
    assert args.run>0
    run(args)
