"""Extend authenticated half-pot flop leads to ace turns and independently gate the rank 55 river check."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL, proof
from hu_b542_rank8_original_turn import HEAD, RUN
from hu_b546_rank70_conditional import current_texture
from hu_b550_rank69_originals import execute, published_actions
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import game_reach

MODEL = "ln-ipfr-r_model-1mcb4lz"
LINE = "b50 c/b50 c/x"
CASES = {
    "7d5c4c": (14792312789, "8aeec8c25159cde3db0b15046bddee1bd1fa3f71b4b92851b25918879c392852"),
    "6d4c3h": (14793340092, "917c6f833fb3add6a982efa1bf6d788420433a990ba2448afeb10491cd3f24ea"),
    "6s5h4d": (14792976867, "df887d5566b9f99505a5310b3e236205c6bfbd55b19013266fbf3e91071a442b"),
}
TURNS = ["As", "Ah", "Ac", "Ad"]
RIVERS = [r+s for r in "23456789TJQK" for s in "cdhs"]


def original(folder, flop):
    aid, digest = CASES[flop]
    meta = json.loads((folder/f"{aid}.json").read_bytes())
    info = meta["workflow_run"]
    assert (meta["id"], info["id"], info["head_sha"], info["repository_id"]) == (aid, RUN, HEAD, 1438346845)
    assert (meta["name"], meta["digest"]) == (f"B524-R8-{flop}-gto", "sha256:"+digest)
    archive = folder/f"{aid}.zip"
    assert sha(archive.read_bytes()) == digest
    with ZipFile(archive) as z:
        m = json.loads(z.read(f"trainer/evidence/{flop}-gto.json"))
        assert (m["flop"], m["spot"], m["version"], m["failures"]) == (flop,"BTN_BB","gto",[])
        path = "solver/postflop/" + m["file_flop"]
        raw = z.read(path)
        assert sha(raw) == m["file_flop_sha256"]
        job = json.loads(z.read(path[:-5]+".job.json"))
    root = json.loads(raw)
    turns = [t for t in TURNS if current_texture(flop+t) == "A_high"]
    job.update(out="result.json", extract=job["extract"]+
               [dict(prefix=["b50","c",t], street=False, raw=True) for t in turns])
    return root, job, turns


def native(folder, job, driver):
    if driver:
        return execute(driver, folder, job)
    assert json.loads((folder/"job.json").read_bytes()) == json.loads(compact(job))
    return (folder/"result.json").read_bytes()


def turn_job(root, turn, pipeline):
    parent, = (n for n in root["nodes"] if n["line"] == "b50 c/" and n["board"].endswith(turn))
    assert (parent["pot"],parent["bets"]) == (1100,[275,275])
    flop, public = root["flop"],parent["board"]
    known = set(public[i:i+2] for i in range(0,8,2))
    rivers = [r for r in RIVERS if r not in known and current_texture(public+r) == "A_high"]
    job = pipeline.make_job("BTN_BB","gto",flop,"result.json",compress=False,target=.4,rank=.4,iters=2000)
    job.update(pipeline.SUB)
    job.update(oop="",ip="",turn=turn,pot=1100,stack=9475,line0=["b50","c","/"],root_no_bet=False,
               extract=[dict(prefix=[],street=True)] + [dict(prefix=["b50","c",r],street=True) for r in rivers])
    for actor, key in enumerate(["oop_w","ip_w"]):
        job[key] = [[h,w] for h,w in zip(root["hands"][actor],parent["wr"][actor],strict=True) if w>1e-4]
    return job, rivers, public


def process(args):
    solver = args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    if args.driver:
        assert args.driver.resolve() == solver/"postflop/pfdriver/target/release/pfdriver"
        assert subprocess.check_output(["git","-C",solver/"postflop/postflop-solver","rev-parse","HEAD"],text=True).strip()==RUST
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    pool_raw = (solver/"inputs/pool_stats.json").read_bytes()
    assert sha(pool_raw) == POOL
    pool = json.loads(pool_raw)["NL2"]
    route = json.loads(subprocess.check_output(["node","tools/hu_b613_rank55_routes.cjs"]))
    old, job, turns = original(args.originals,args.flop)
    root_raw = native(args.output/"flop",job,args.driver)
    root = json.loads(root_raw)
    assert (root["flop"],root["hands"],root["pot"],root["stack"]) == (args.flop,old["hands"],550,9750)
    assert 0<=root["info"]["gto_expl_pct"]<=.5 and not root["info"].get("lock_stats")
    nodes = {(n["board"],n["line"],n["player"]):n for n in root["nodes"]}
    # Appended exports leave the original native strategy and all historical boundaries intact.
    assert all(nodes[(n["board"],n["line"],n["player"])] == n for n in old["nodes"])
    root_sha = sha(compact(root))
    results = []
    for turn in turns:
        gto, rivers, public = turn_job(root,turn,pipeline)
        parent = dict(source=dict(version="gto",root=root,manifest=dict(spot="BTN_BB")),job=gto)
        exploit, locks = prepare_job(parent,"exp_ip",pool,pipeline)
        exploit["out"]="result.json"
        shared = {}
        checks = []
        for version, spec, rules in [("gto",gto,[]),("exp_ip",exploit,locks)]:
            raw = native(args.output/(turn+"-"+version),spec,args.driver)
            sub = json.loads(raw)
            assert (sub["pot"],sub["stack"],sub["flop"]) == (1100,9475,args.flop)
            assert 0<=sub["info"]["gto_expl_pct"]<=.5
            sub.update(turn=turn,rivers=rivers,line0="b50 c")
            manifest=dict(spot="BTN_BB",pot_family="SRP",locks=rules)
            source=dict(root=root,subgame=sub,manifest=manifest,version=version,run=args.run,source_sha256=sha(raw))
            if version=="exp_ip":
                assert 0<=sub["info"]["hero_gap_pct"]<=.5
                manifest.update(gto_parent_source_run_id=args.run,gto_parent_source_sha256=root_sha)
                source.update(verified_gto_parent=dict(run=args.run,sha256=root_sha),
                              measured_lock_application=audit_patterns(sub,spec,manifest,pool,1),
                              applied_rust_rates=sub["info"]["lock_stats"])
            else:
                assert not sub["info"].get("lock_stats")
            masks = game_reach(root,sub)[0]
            river_nodes = {n["board"]:n for n in sub["nodes"] if (n["line"],n["player"])==(LINE,1)}
            assert set(river_nodes)=={public+r for r in rivers}
            for river in rivers:
                board = public+river
                node = river_nodes[board]
                assert (node["pot"],node["bets"])==(2200,[550,550])
                row = proof(root,sub,node,masks)
                hands = published_actions(source,row,route)
                if version=="gto":
                    shared[board] = hands
                else:
                    same = sorted(shared.get(board,{}).keys() & hands.keys())
                    if same:
                        assert abs(((9475-550)/2200)/4.083-1)<=.05
                        checks.append(dict(board=board,hands=same,locked_half_pot=row["b50"]))
        results.append(dict(turn=turn,checks=checks))
        if checks:break
    return dict(rank=55,model_id=MODEL,flop=args.flop,run=args.run,root_sha256=sha(root_raw),
                original_artifact=CASES[args.flop][0],original_nodes_reproduced=len(old["nodes"]),turns=results)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--solver",type=Path,required=True)
    p.add_argument("--originals",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--flop",choices=CASES,required=True)
    p.add_argument("--run",type=int,required=True)
    p.add_argument("--driver",type=Path)
    args=p.parse_args()
    assert args.run>0
    report=process(args)
    (args.output/"proof.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
