"""Solve new third-pot BB leads for BTN's checked-down rank69 river decision."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b483_locked_medium import POOL, proof
from hu_b550_rank69_originals import LINE, MID, published_actions, turn_job, tx
from hu_b613_rank55_barrels import native
from hu_sequential_cfr_reach import accepted, game_reach

CASES = {
    "Ts9h6c": ["2d","3c","4h","7s","Jd"],
    "Jh8c7d": ["2s","3h","4c","9d","Tc"],
    "Th7h5c": ["2d","3s","4c","8h","Jc"],
    "JdTc8s": ["2c","3d","4h","7s","9d"],
    "8d7c4h": ["2s","3d","5h","9c","Ts"],
}
TEMPLATE = "NL2_B613_R55_7D5C4C.zip"
TEMPLATE_SHA = "afdf2d2f10164167506d93b57f053463bcbf135f5e0ef0dade64bc75401e39bf"


def root_job(flop):
    path = EVIDENCE/TEMPLATE
    assert sha(path.read_bytes()) == TEMPLATE_SHA
    with ZipFile(path) as z:
        source = json.loads(z.read("worker.json"))
        job = json.loads(z.read("flop/job.json"))
    assert (source["run"],source["original_artifact"],source["solver"],source["rust"]) == (45177383424,14792312789,SOLVER,RUST)
    assert (job["pot"],job["stack"],job["rake_rate"],job["rake_cap"]) == (550,9750,.05,1000)
    assert not job.get("locks") and job.get("hero") is None
    extracts = [dict(prefix=[],street=True)] + [dict(prefix=["b33","c",t],street=False,raw=True) for t in CASES[flop]]
    return dict(job,flop=flop,flop_oop="33%",flop_ip="33%",out="result.json",extract=extracts)


def screen(args):
    solver = args.solver.resolve()
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
    route=json.loads(subprocess.check_output(["node","tools/hu_b550_rank69_routes.cjs"]))
    flop=args.flop
    job=root_job(flop)
    assert (job["oop"],job["ip"])==tuple(ranges.to_str(v) for v in ranges.ranges("BTN_BB","gto"))
    raw=native(args.output/"flop",job,None if args.existing_root else args.driver)
    root=json.loads(raw)
    assert (root["flop"],root["pot"],root["stack"])==(flop,550,9750) and 0<=root["info"]["gto_expl_pct"]<=.5
    assert not root["info"].get("lock_stats")
    open_node,=(n for n in root["nodes"] if n["line"]=="")
    response,=(n for n in root["nodes"] if n["line"]=="b33")
    leads=accepted(open_node,root["hands"],"b33")
    calls=accepted(response,root["hands"],"c")
    report=dict(rank=69,model_id=MID,flop=flop,root_sha256=sha(raw),strict_flop_leads=len(leads),strict_flop_calls=len(calls),turns=[])
    for t in CASES[flop]:
        if not any(set(h).isdisjoint(v) for h in leads if t not in h for v in calls if t not in v):
            report["turns"].append(dict(turn=t,reason="NO_DISJOINT_FLOP_LEAD_AND_CALL",rivers=[]))
            continue
        policies=[]
        for version in ("gto","exp_ip"):
            j,locks,rivers,public=turn_job(root,flop,t,version,pool,pipeline)
            result=native(args.output/(t+"-"+version),j,args.driver)
            sub=json.loads(result)
            assert (sub["pot"],sub["stack"],sub["flop"])==(914,9568,flop) and 0<=sub["info"]["gto_expl_pct"]<=.5
            if version=="exp_ip":
                assert 0<=sub["info"]["hero_gap_pct"]<=.5 and bool(sub["info"]["lock_stats"])
            else:
                assert not sub["info"].get("lock_stats")
            sub.update(line0="b33 c",turn=t,rivers=rivers)
            masks=game_reach(root,sub)[0]
            targets={n["board"]:n for n in sub["nodes"] if (n["line"],n["player"])==(LINE,1)}
            assert set(targets)=={public+r for r in rivers}
            choices={}
            for b,n in targets.items():
                assert (n["pot"],n["bets"])==(914,[0,0])
                row=proof(root,sub,n,masks)
                hands=published_actions(dict(subgame=sub),row,route)
                if hands:
                    choices[b]=(set(hands),row["b50"])
            policies.append(choices)
            if not choices:
                break
        matches=[]
        if len(policies)==2:
            original,locked=policies
            for b in sorted(original.keys() & locked.keys()):
                common=sorted(original[b][0] & locked[b][0])
                if common:
                    matches.append(dict(public_board=b,hands=common,locked_medium=locked[b][1]))
        report["turns"].append(dict(turn=t,policies_checked=len(policies),rivers=matches))
        if matches:
            break
    (args.output/"proof.json").write_bytes(json_bytes(report))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--solver",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--flop",choices=CASES,required=True)
    p.add_argument("--driver",type=Path)
    p.add_argument("--existing-root",action="store_true")
    screen(p.parse_args())
