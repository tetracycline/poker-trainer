"""Check SB's three-quarter-pot turn lead and river barrel on named paired boards."""
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b483_locked_medium import POOL, proof
from hu_b546_rank70_conditional import current_texture
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import cardkey, game_reach

sys.path.insert(0, str(Path(__file__).resolve().parent / "lines_pipeline"))
from run10_common import classes, hcls

LINE = "x b50 c/b75 c/"
MODEL = "ln-opfr-r_model-8ze7gv"
CASES = {
    "TdTs4h": (565, "b46753b38c693b952771f79db076130ec2c296100d69c4045b77af3d3776a099", ["5d","6c","Jc","Qd","Ks","Ah","3s"]),
    "QcQd4s": (565, "76cdb6ec787ccd9286ceb095381b68f2e71e36da1151d42604364312d09c6a61", ["2s","7d","Js","Kd","Ac","6h","8c"]),
    "JdJh3c": (565, "7a8d37dcb8c915eea9eb9d885c9e1c2243da30baa75e17872de269f7801cd67d", ["5h","Ks","6c","Qd","Ad","7s","8c"]),
    "TcTh3s": (574, "faf27c4bbb7813e23d8ad8a0a47e1d28a83e38793d22230c1e48d8ab1510999e", ["5c","8h","Js","Qh","Kd","Ah","7d"]),
}


def solve(folder, job, driver):
    folder.mkdir(exist_ok=True, parents=True)
    job_file, output = folder / "job.json", folder / "result.json"
    if driver:
        job_file.write_bytes(compact(job))
        subprocess.run([driver.resolve(), "job.json"], cwd=folder, check=True, env=dict(os.environ, RAYON_NUM_THREADS="2"))
    assert json.loads(job_file.read_bytes()) == json.loads(compact(job))
    return json.loads(output.read_bytes())


def root_job(flop):
    batch, digest, turns = CASES[flop]
    archive = EVIDENCE / f"NL2_B{batch}_R18_{flop.upper()}.zip"
    assert sha(archive.read_bytes()) == digest
    with ZipFile(archive) as z:
        evidence = json.loads(z.read(f"trainer/evidence/{flop}-gto.json"))
        assert (evidence["spot"], evidence["version"], evidence["failures"]) == ("SB_BB", "gto", [])
        name, = [n for n in z.namelist() if n.endswith("_multiboard.json")]
        root_raw = z.read(name)
        assert sha(root_raw) == evidence["file_flop_sha256"]
        original = json.loads(root_raw)
        job = json.loads(z.read(name[:-5]+".job.json"))
    extracts = [dict(prefix=["x","b50","c",t], raw=True, street=False) for t in turns]
    return original, dict(job, out="result.json", extract=job["extract"]+extracts)


def turn_jobs(root, turn, pipeline, pool):
    parent, = [n for n in root["nodes"] if n["line"] == "x b50 c/" and n["board"].endswith(turn)]
    assert (parent["pot"], parent["bets"]) == (1200,[300,300])
    board = parent["board"]
    known = {board[i:i+2] for i in range(0,8,2)}
    rivers = [r+s for r in "23456789TJQKA" for s in "cdhs" if r+s not in known and current_texture(board+r+s) == "paired"]
    job = pipeline.make_job("SB_BB","gto",root["flop"],"result.json",target=.4,rank=.4,iters=2300,compress=False)
    job.update(pipeline.SUB)
    job.update(oop="",ip="",line0=["x","b50","c","/"],turn=turn,turn_oop="75%",river_oop="50%,75%,100%",
               pot=1200,stack=9400,root_no_bet=False,extract=[dict(prefix=[],street=True)]+[
                   dict(prefix=["b75","c",r],street=False) for r in rivers])
    for seat, key in enumerate(("oop_w","ip_w")):
        job[key]=[[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4]
    lock, rules = prepare_job(dict(source=dict(version="gto",root=root,manifest=dict(spot="SB_BB")),job=job),"exp_oop",pool,pipeline)
    lock["out"]="result.json"
    return job, lock, rules, rivers


def hands_for(root, sub, turn, rivers, route):
    sub.update(line0="x b50 c",turn=turn,rivers=rivers)
    masks=game_reach(root,sub)[0]
    targets = [n for n in sub["nodes"] if (n["line"],n["player"]) == (LINE,0)]
    assert {n["board"][-2:] for n in targets} == set(rivers)
    matches={}
    for node in targets:
        b=node["board"]
        assert (node["pot"],node["bets"])==(3000,[900,900])
        assert abs((9400-900)/3000/2.733-1) <= .05
        row=proof(root,sub,node,masks)
        mask=base64.b64decode(row["compatible_action_mask_b64"],validate=True)
        i=node["acts"].index("b75")
        shared=set()
        for hand,bits in zip(sub["hands"][0],mask,strict=True):
            if bits & (1<<i) and hcls(hand,b[:6]) in route[current_texture(b[:6])]["flop"] and hcls(hand,b[:8]) in route[current_texture(b[:8])]["turn"] and route[current_texture(b)]["river"].get(classes(hand,b)[0])=="下注 ¾":
                shared.add("".join(cardkey(hand)))
        if shared:
            matches[b] = (shared,row)
    return matches


def run(args):
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    if args.driver:
        assert args.driver.resolve()==solver/"postflop/pfdriver/target/release/pfdriver"
        assert subprocess.check_output(["git","-C",solver/"postflop/postflop-solver","rev-parse","HEAD"],text=True).strip()==RUST
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    pool_raw=(solver/"inputs/pool_stats.json").read_bytes()
    assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)["NL2"]
    route=json.loads(subprocess.check_output(["node","tools/hu_b617_sb_routes.cjs"]))["57"]
    old,job=root_job(args.flop)
    root=solve(args.output/"flop",job,None if args.existing_root else args.driver)
    assert root["hands"]==old["hands"] and 0<=root["info"]["gto_expl_pct"]<=.5
    nodes={(n["board"],n["line"],n["player"]):n for n in root["nodes"]}
    assert all(nodes[n["board"],n["line"],n["player"]]==n for n in old["nodes"])
    tested=[]
    for t in CASES[args.flop][2]:
        g,e,_,rivers=turn_jobs(root,t,pipeline,pool)
        pair=[]
        for version,j in [("gto",g),("exp_oop",e)]:
            sub=solve(args.output/(t+"-"+version),j,args.driver)
            assert (sub["pot"],sub["stack"],sub["flop"])==(1200,9400,args.flop)
            assert 0 <= sub["info"]["gto_expl_pct"]<=.5
            if version=="exp_oop":
                assert 0<=sub["info"]["hero_gap_pct"]<=.5 and sub["info"]["lock_stats"]
            else:
                assert not sub["info"].get("lock_stats")
            pair.append(hands_for(root,sub,t,rivers,route))
            if not pair[0]:
                break
        matches=[]
        if len(pair)==2:
            gto,locked=pair
            for b in sorted(gto.keys() & locked.keys()):
                hands=sorted(gto[b][0] & locked[b][0])
                if hands:
                    matches.append(dict(board=b,hands=hands,locked_half_pot=locked[b][1]["b50"]))
        tested.append(dict(turn=t,positive_rivers=matches))
        if matches:
            break
    result=dict(rank=57,model_id=MODEL,flop=args.flop,root_sha256=sha(compact(root)),turns=tested)
    (args.output/"proof.json").write_bytes(json_bytes(result))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--solver",type=Path,required=True)
    p.add_argument("--flop",choices=CASES,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--driver",type=Path)
    p.add_argument("--existing-root",action="store_true")
    run(p.parse_args())
