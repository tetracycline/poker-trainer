"""Solve the rendered SB turn lead and river check from four authenticated SB/BB roots."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import compact, sha
from hu_b483_locked_medium import POOL, proof
from hu_b546_rank70_conditional import current_texture as texture
from hu_b613_rank55_barrels import native
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import cardkey, game_reach

sys.path.insert(0,str(Path(__file__).resolve().parent/"lines_pipeline"))
from run10_common import hcls, classes

CASES=json.loads(Path("data/nl2_hu_b617_rank58_sources.json").read_bytes())
LINE="x b50 c/b33 c/"
MODEL="ln-opfr-r_model-aumml6"


def flop_source(folder, flop):
    pin=CASES[flop]
    aid=pin["artifact_id"]
    meta=json.loads((folder/f"{aid}.json").read_bytes())
    info=meta["workflow_run"]
    assert (meta["id"],meta["name"],info["id"],info["head_sha"],info["repository_id"])==(aid,pin["name"],pin["run"],pin["head"],1438346845)
    archive=folder/f"{aid}.zip"
    assert meta["digest"]=="sha256:"+pin["sha256"] and sha(archive.read_bytes())==pin["sha256"]
    with ZipFile(archive) as z:
        mf,=(p for p in z.namelist() if p.startswith(("evidence/","trainer/evidence/")) and p.endswith(".json") and not p.endswith("pool_stats.json"))
        m=json.loads(z.read(mf))
        assert m["spot"]=="SB_BB" and m["version"]=="gto" and not m["failures"]
        member=pin["root_member"]
        raw=z.read(member)
        old=json.loads(raw)
        job=json.loads(z.read(member[:-5]+".job.json"))
        if "file_flop_sha256" in m:
            assert m["file_flop_sha256"]==sha(raw)
        else:
            hashes={c["flop_sha256"] for c in m["cases"] if c["flop"]==flop}
            assert hashes=={sha(raw)}
    assert not job.get("locks") and (job["flop"],job["pot"],job["stack"],job["rake_rate"],job["rake_cap"])==(flop,600,9700,.05,1000)
    assert 0<=old["info"]["gto_expl_pct"]<=.5
    extra=[]
    for t in pin["turns"]:
        if not any(n["line"]=="x b50 c/" and n["board"].endswith(t) and n.get("wr") for n in old["nodes"]):
            extra.append(dict(prefix=["x","b50","c",t],street=False,raw=True))
    return old,dict(job,out="result.json",extract=job["extract"]+extra),bool(extra)


def make_turn(root, turn, pipeline, pool, route):
    public,=(n for n in root["nodes"] if n["line"]=="x b50 c/" and n["board"].endswith(turn))
    q=public["board"]; assert (public["pot"],public["bets"])==(1200,[300,300])
    known={q[i:i+2] for i in range(0,8,2)}
    rivers=[r+s for r in "23456789TJQKA" for s in "cdhs" if r+s not in known and route[texture(q+r+s)]["river"]]
    job=pipeline.make_job("SB_BB","gto",root["flop"],"result.json",target=.4,rank=.4,iters=2300,compress=False)
    job.update(pipeline.SUB)
    job.update(oop="",ip="",line0=["x","b50","c","/"],turn=turn,turn_oop="33%,50%,100%",river_oop="50%,75%,100%",pot=1200,stack=9400,root_no_bet=False,
               extract=[dict(prefix=[],street=True)]+[dict(prefix=["b33","c",r],street=True) for r in rivers])
    for seat,key in enumerate(("oop_w","ip_w")):
        job[key]=[[h,w] for h,w in zip(root["hands"][seat],public["wr"][seat],strict=True) if w>1e-4]
    base=dict(source=dict(version="gto",root=root,manifest=dict(spot="SB_BB")),job=job)
    exp,meta=prepare_job(base,"exp_oop",pool,pipeline)
    exp["out"]="result.json"
    return job,exp,meta,rivers,q


def matching_hands(sub, node, row, route):
    b=node["board"]; idx=node["acts"].index("x"); mask=base64.b64decode(row["compatible_action_mask_b64"],validate=True)
    selected=[]
    for h,bits in zip(sub["hands"][0],mask,strict=True):
        if bits & (1<<idx) and hcls(h,b[:6]) in route[texture(b[:6])]["flop"] and hcls(h,b[:8]) in route[texture(b[:8])]["turn"] and route[texture(b)]["river"].get(classes(h,b)[0])=="過":
            selected.append("".join(cardkey(h)))
    return set(selected)


def process(args):
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    if args.driver:
        assert args.driver.resolve()==solver/"postflop/pfdriver/target/release/pfdriver"
        assert subprocess.check_output(["git","-C",solver/"postflop/postflop-solver","rev-parse","HEAD"],text=True).strip()==RUST
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    pool_bytes=(solver/"inputs/pool_stats.json").read_bytes();assert sha(pool_bytes)==POOL
    pool=json.loads(pool_bytes)["NL2"]
    route=json.loads(subprocess.check_output(["node","tools/hu_b617_sb_routes.cjs"]))["58"]
    old,j,extra=flop_source(args.originals,args.flop)
    root=json.loads(native(args.output/"flop",j,args.driver)) if extra else old
    assert root["hands"]==old["hands"] and 0<=root["info"]["gto_expl_pct"]<=.5
    nodes={(n["board"],n["line"],n["player"]):n for n in root["nodes"]}
    assert all(nodes[n["board"],n["line"],n["player"]]==n for n in old["nodes"])
    result=[]
    for turn in CASES[args.flop]["turns"]:
        g,e,meta,rivers,public=make_turn(root,turn,pipeline,pool,route)
        choices={};checks=[]
        for version,job in [("gto",g),("exp_oop",e)]:
            raw=native(args.output/(turn+"-"+version),job,args.driver)
            sub=json.loads(raw)
            assert (sub["pot"],sub["stack"],sub["flop"])==(1200,9400,args.flop)
            assert 0<=sub["info"]["gto_expl_pct"]<=.5
            if version=="exp_oop":assert 0<=sub["info"]["hero_gap_pct"]<=.5 and sub["info"]["lock_stats"]
            else:assert not sub["info"].get("lock_stats")
            sub.update(line0="x b50 c",turn=turn,rivers=rivers)
            masks=game_reach(root,sub)[0]
            targets={n["board"]:n for n in sub["nodes"] if (n["line"],n["player"])==(LINE,0)}
            assert set(targets)=={public+r for r in rivers}
            for b,node in targets.items():
                assert (node["pot"],node["bets"])==(1992,[396,396]) and abs(((9400-396)/1992)/4.35-1)<=.05
                row=proof(root,sub,node,masks)
                hands=matching_hands(sub,node,row,route)
                if version=="gto":choices[b]=hands
                elif hands & choices[b]:checks.append(dict(board=b,hands=sorted(hands & choices[b]),locked_half_pot=row["b50"]))
        result.append(dict(turn=turn,checks=checks))
        if checks:break
    return dict(rank=58,model_id=MODEL,flop=args.flop,run=args.run,original_artifact=CASES[args.flop]["artifact_id"],
                original_nodes_reproduced=len(old["nodes"]),root_sha256=sha(compact(root)),turns=result)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name in ["solver","originals","output"]:p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--run",type=int,required=True)
    p.add_argument("--flop",choices=CASES,required=True)
    p.add_argument("--driver",type=Path)
    args=p.parse_args();assert args.run>0
    (args.output/"proof.json").parent.mkdir(parents=True,exist_ok=True)
    (args.output/"proof.json").write_text(json.dumps(process(args),sort_keys=True,indent=2)+"\n")
