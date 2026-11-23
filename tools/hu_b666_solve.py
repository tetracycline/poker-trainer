"""Solve and package exact rank90 flop, turn and actor-locked continuations."""
import argparse
import json
from pathlib import Path
import os
import subprocess
import sys
from zipfile import ZipFile,ZIP_DEFLATED

from hu_b467_river_source_gate import compact,sha,json_bytes
from hu_b527_checked_barrels import board_row
from hu_b666_rank90 import SOLVER,RUST,POOL,HISTORIC,make_root,make_turn,decision
from hu_checked_gto_boundary import prepare_job

TURNS={"As9h2d":["Kd"],"As7h3d":["Kd"],"Ac8h3d":["Kh","6s"],"Ah7d4c":["Ks","9h"]}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--solver",type=Path,required=True)
    p.add_argument("--flop",choices=TURNS,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    solver=a.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    assert subprocess.check_output(["git","-C",solver/"postflop/postflop-solver","rev-parse","HEAD"],text=True).strip()==RUST
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    rawpool=(solver/"inputs/pool_stats.json").read_bytes();assert sha(rawpool)==POOL
    pool=json.loads(rawpool)["NL2"]
    driver=solver/"postflop/pfdriver/target/release/pfdriver"
    route=json.loads(subprocess.check_output(["node","tools/hu_b666_rank90_route.cjs"]))
    rootpath=a.output/"root";rootpath.mkdir(parents=True,exist_ok=True)
    flop,turns=a.flop,TURNS[a.flop]
    def solve(job,folder,name):
        folder.mkdir(parents=True,exist_ok=True)
        (folder/(name+".job.json")).write_bytes(compact(job))
        subprocess.run([driver,str((folder/(name+".job.json")).resolve())],cwd=folder,check=True,env=dict(os.environ,RAYON_NUM_THREADS="1"))
        return (folder/job["out"]).read_bytes()
    if flop in HISTORIC:
        path=Path("data/solver_evidence")/("NL2_B666_R90_"+flop.upper()+"_PARENT.zip")
        assert sha(path.read_bytes())==HISTORIC[flop]
        with ZipFile(path)as z:
            mf=next(n for n in z.namelist() if "evidence/"in n and n.endswith(".json") and not n.endswith("pool_stats.json"))
            m=json.loads(z.read(mf));member="solver/postflop/"+m["file_flop"]
            rootraw=z.read(member);rootjob=json.loads(z.read(member.replace(".json",".job.json")))
            assert sha(rootraw)==m["file_flop_sha256"]
            rootjob["out"]="root.json"
        (rootpath/"root.job.json").write_bytes(compact(rootjob))
        (rootpath/"root.json").write_bytes(rootraw)
    else:
        rootjob=make_root(pipeline,flop,turns)
        rootraw=solve(rootjob,rootpath,"root")
    root=json.loads(rootraw);rootsha=sha(compact(root))
    assert 0<=root["info"]["gto_expl_pct"]<=.5
    attempts=[];selected=None
    for turn in turns:
        parent,=(n for n in root["nodes"] if n["line"]=="x b33 c/" and n["board"].endswith(turn))
        public=parent["board"]
        known={public[i:i+2] for i in range(0,8,2)}
        rivers=[r+s for r in "23456789TJQKA" for s in "cdhs" if r+s not in known and board_row(public+r+s) in ("low","A_high","mono")]
        g=make_turn(pipeline,root,turn,rivers)
        e,rules=prepare_job(dict(source=dict(version="gto",root=root,manifest=dict(spot="SB_BB")),job=g),"exp_oop",pool,pipeline)
        e["out"]="native.json"
        folder=a.output/turn
        gr,er=solve(g,folder,"gto"),solve(e,folder,"native")
        sources=[]
        for version,raw in [("gto",gr),("exp_oop",er)]:
            sub=json.loads(raw);sub.update(line0="x b33 c",turn=turn,rivers=rivers)
            sources.append(dict(root=root,subgame=sub,run=1,version=version,source_sha256=sha(raw),root_sha256=rootsha,archive_sha256="0"*64,
                                manifest=dict(spot="SB_BB",pot_family="SRP",locks=[] if version=="gto" else rules)))
        for river in rivers:
            b=public+river
            rows=[decision(s,b,route) for s in sources]
            common=sorted(rows[0][1].keys() & rows[1][1].keys())
            attempts.append(dict(public_board=b,shared_hands=len(common)))
            if common:
                selected=dict(flop=flop,turn=turn,river=river,root_turns=turns,river_extracts=rivers,
                    root_sizing={k:v for k,v in rootjob.items() if k.startswith(("flop_","turn_","river_"))},
                    flop_menu=rootjob["flop_ip"],shared_hands=len(common))
                with ZipFile(a.output/("NL2_B666_R90_"+flop.upper()+".zip"),"w",ZIP_DEFLATED)as z:
                    for name,body in [("root.json",rootraw),("root.job.json",compact(rootjob)),("gto.json",gr),("gto.job.json",compact(g)),("native.json",er),("native.job.json",compact(e))]:
                        z.writestr(name,body)
                selected["archive_sha256"]=sha((a.output/("NL2_B666_R90_"+flop.upper()+".zip")).read_bytes())
                break
        if selected:break
    (a.output/"selected.json").write_bytes(json_bytes(selected))
    (a.output/"attempts.json").write_bytes(json_bytes(attempts))
    print(json.dumps(selected))

if __name__=="__main__":main()
