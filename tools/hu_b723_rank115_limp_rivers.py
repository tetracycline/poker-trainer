"""Resolve CO's one-third-pot turn stab using four saved BB half-pot flop roots."""
import argparse
import base64
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b481_rank27_limp_rivers import check_limp_source
from hu_b483_locked_medium import PIPELINE, RANGES, POOL, proof
from hu_b568_caller_rivers import hand_cell
from hu_b637_rank57 import solve
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, game_reach

EVIDENCE = Path("data/solver_evidence")
B492 = ("NL2_B492_LMP_CO_BB_7S5H3D_6C_GTO.zip", "069e51390d9fa1407edb741ec7767323f4de4ee90dfcb9deeec65de57ee5d2ae")
B580 = ("NL2_B580_R27_LMP.zip", "d4b98b4351012d78aa62f3cd31b75228d4f7a35725584d86f633552fbf28369a")
CASES = {"7s5h3d":("6c",1,4), "7h6d4s":("9d",11,12), "7h6c4h":("9s",10,12), "7h6h4c":("8s",9,6)}
LINE = "b50 c/x b33 c/x"
MID = "ln-iso-lmp_r_model-17dzvwx"

def load_root(flop):
    archive, digest = B492 if flop == "7s5h3d" else B580
    path = EVIDENCE / archive
    assert sha(path.read_bytes()) == digest
    with ZipFile(path) as z:
        take = lambda n: json.loads(z.read(n))
        manifest = take("original-manifest.json")
        if flop == "7s5h3d":
            root_name, job_name, sub_name = "original-flop.json", "original-flop.job.json", "original-subgame.job.json"
            origin = take("provenance.json")
            assert (origin["solver"],origin["rust"]) == (SOLVER,RUST)
            assert (origin["original_run_id"],origin["original_archive_id"]) == (44769773770,14648360341)
            assert sha(z.read(root_name)) == origin["original_root_sha256"] == manifest["file_flop_sha256"]
            assert sha(z.read(job_name)) == origin["original_flop_job_sha256"]
            source_run, source_kind = origin["original_run_id"], "GITHUB_ACTIONS_ORIGINAL"
        else:
            origin = take("source-provenance.json")
            assert (origin["poker_solver"],origin["rust"]) == (SOLVER,RUST)
            root_name = flop + "/root.json"
            job_name = "original-flop.job.json" if flop == "7h6d4s" else flop + "/root.job.json"
            sub_name = "original-turn.job.json"
            for name in (root_name,job_name,sub_name):
                assert sha(z.read(name)) == origin["source_files"][name]
            source_run = origin["original_run"] if flop == "7h6d4s" else None
            source_kind = "GITHUB_ACTIONS_ORIGINAL" if source_run else "PRIOR_PINNED_LOCAL_RUST_VERIFIED_AND_ARCHIVED_ON_GITHUB"
        root, rootjob, template = take(root_name), take(job_name), take(sub_name)
        assert manifest["preflop_ranges"]["source"] == "ASSUMED_EXPLICIT_169CLASS"
        check_limp_source(dict(manifest=manifest,root_job=rootjob,subgame_job=None))
        assert (root["flop"],rootjob["flop"],root["pot"],root["stack"]) == (flop,flop,250,9900)
        assert rootjob["flop_oop"] == "50%" and not rootjob.get("locks") and not root["info"].get("lock_stats")
        assert 0 <= root["info"]["gto_expl_pct"] <= .5
        return root, template, dict(archive=archive,archive_sha256=digest,flop_menu="50%",root_sha256=sha(z.read(root_name)),
            root_job_sha256=sha(z.read(job_name)),template_sha256=sha(z.read(sub_name)),source_solve_run=source_run,scope=source_kind)


def boundary(root, template, flop, route):
    turn, num_hands, num_rivers = CASES[flop]
    parent, = [n for n in root["nodes"] if n["line"] == "b50 c/" and n["board"].endswith(turn)]
    public = parent["board"]
    cards = {public[i:i+2] for i in range(0,8,2)}
    assert len(cards) == 4 and cards-{turn} == {flop[i:i+2] for i in (0,2,4)}
    assert (parent["player"],parent["pot"],parent["bets"]) == (0,500,[125,125])
    nodes = {n["line"]:n for n in root["nodes"] if n["board"] == public[:6]}
    assert (nodes[""]["player"],nodes[""]["pot"],nodes[""]["bets"]) == (0,250,[0,0])
    assert (nodes["b50"]["player"],nodes["b50"]["pot"],nodes["b50"]["bets"]) == (1,375,[125,0])
    enabled = [accepted(nodes[""],root["hands"],"b50"),accepted(nodes["b50"],root["hands"],"c")]
    job = dict(template, flop=flop, turn=turn, out="result.json", iters=2450, target_pct=.4, rank_pct=.4, compress=False,
               turn_oop="33%,50%,75%,100%", turn_ip="33%,50%,75%,100%", river_oop="50%,75%,100%,a",river_ip="50%,75%,100%,a",
               river_donk="50%,75%,100%", extract=[dict(prefix=[],street=True)])
    assert (job["pot"],job["stack"],job["line0"],job["root_no_bet"],job.get("hero")) == (500,9775,["b50","c","/"],False,None)
    assert not job.get("locks")
    for seat, key in enumerate(("oop_w","ip_w")):
        job[key] = [[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4]
        enabled[seat] &= {cardkey(h) for h,_ in job[key] if cards.isdisjoint(cardkey(h))}
    heroes = sorted(h for h in enabled[1] if hand_cell("".join(h),public[:6])[0] in route["flop"]
                    and hand_cell("".join(h),public)[0] in route["turn"] and any(set(h).isdisjoint(o) for o in enabled[0]))
    rivers = {}
    for rank,suit in product("23456789TJQKA","cdhs"):
        river = rank+suit
        if river in cards:continue
        for h in heroes:
            if river in h or hand_cell("".join(h),public+river)[0] not in route["river"]:continue
            opp = next((o for o in sorted(enabled[0]) if river not in o and set(h).isdisjoint(o)),None)
            if opp:
                rivers[river] = ["".join(h),"".join(opp)]
                break
    assert (len(heroes),len(rivers)) == (num_hands,num_rivers)
    for river in rivers:
        for end in ([],["x"]):
            job["extract"].append(dict(prefix=["x","b33","c",river,*end],street=False))
    return job, public, rivers, len(heroes)


def observe(root, game, public, rivers, route):
    game.update(line0="b50 c",turn=public[-2:])
    masks = game_reach(root,game)[0]
    nodes = {(n["line"],n["board"]):n for n in game["nodes"]}
    result = {}
    for card in rivers:
        board=public+card
        bb = nodes[LINE[:-1],board]
        co = nodes[LINE,board]
        assert (bb["player"],co["player"],co["pot"],co["bets"],game["stack"]-165) == (0,1,830,[165,165],9610)
        assert "x" in bb["acts"] and any(x.startswith("b") for x in bb["acts"])
        row=proof(root,game,co,masks)
        bits=base64.b64decode(row["compatible_action_mask_b64"],validate=True)
        check=1 << co["acts"].index("x")
        hands=[]
        for h,v in zip(game["hands"][1],bits,strict=True):
            if v&check and all(hand_cell(h,board[:cut])[0] in route[street] for cut,street in ((6,"flop"),(8,"turn"),(10,"river"))):
                hands.append("".join(cardkey(h)))
        result[board]=dict(reach=row,displayed_hands=sorted(hands))
    return result


def run(args):
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip() == SOLVER
    for path,pin in (("postflop/py/pipeline.py",PIPELINE),("postflop/py/ranges.py",RANGES),("inputs/pool_stats.json",POOL)):
        assert sha((solver/path).read_bytes())==pin
    if args.driver:
        assert args.driver.resolve()==solver/"postflop/pfdriver/target/release/pfdriver"
        assert subprocess.check_output(["git","-C",solver/"postflop/postflop-solver","rev-parse","HEAD"],text=True).strip()==RUST
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    pool=json.loads((solver/"inputs/pool_stats.json").read_bytes())["NL2"]
    route=json.loads(args.routes.read_bytes())["115"]
    assert (route["id"],route["turn_pct"],route["turn"],route["river"]) == (MID,33,{"low:1":"下注 ⅓"},{"low:1":"過"})
    assert abs((9610/830)/route["model_spr"]-1) <= .05
    root,template,source=load_root(args.flop)
    job,public,rivers,nh=boundary(root,template,args.flop,route)
    print(json.dumps(dict(flop=args.flop,public=public,compatible_root_ui_hands=nh,eligible_rivers=len(rivers))))
    if args.preflight:return
    assert args.run>0 and len(args.head)==40
    def continuation(version,j):
        folder=args.output/version
        game=solve(folder,j,None if (folder/"result.json").is_file() else args.driver)
        assert (game["flop"],game["pot"],game["stack"]) == (args.flop,500,9775)
        assert 0<=game["info"]["gto_expl_pct"]<=.5
        return game,dict(job_sha256=sha((folder/"job.json").read_bytes()),result_sha256=sha((folder/"result.json").read_bytes()))
    g,gpin=continuation("gto",job)
    assert not g["info"].get("lock_stats")
    before=observe(root,g,public,rivers,route)
    after,epin,application,common={},None,None,{}
    if any(row["displayed_hands"] for row in before.values()):
        lock,rules=prepare_job(dict(source=dict(version="gto",root=root,manifest=dict(spot="LMP_CO_BB")),job=job),"exp_ip",pool,pipeline)
        lock["out"]="result.json"
        assert lock["hero"]==1
        e,epin=continuation("exp_ip",lock)
        assert e["hands"]==g["hands"] and 0<=e["info"]["hero_gap_pct"]<=.5 and e["info"]["lock_stats"]
        application=audit_patterns(e,lock,dict(locks=rules),pool,1)
        assert any(v>0 for k,v in application["driver_tree_nodes"].items() if k in application["marginal_targets"])
        after=observe(root,e,public,rivers,route)
        common={b:sorted(set(before[b]["displayed_hands"]) & set(after[b]["displayed_hands"])) for b in before}
    report=dict(schema="NL2_B723_R115_FROZEN_HALF_POT_FLOP_IP_STAB_V1",run=args.run,head=args.head,rank=115,model=MID,actor=1,
                line=LINE,flop=args.flop,turn=public[-2:],source=source,source_scope="Original restricted half-pot BB flop. Explicit assumed LMP 169-class ranges. NL2 observed street marginals apply to BB, with explicit assumed fallback patterns.",
                gto_source=gpin,nl2_source=epin,model_spr=route["model_spr"],actual_spr=9610/830,solver=SOLVER,rust=RUST,pool=POOL,
                selected_rivers=rivers,boundary_hands=nh,route_sha256=sha(args.routes.read_bytes()),gto=before,nl2=after,common=common,
                positive_flops=int(any(common.values())),actor_locked=epin is not None,lock_application=application,
                medium_scope="For each original GTO/locked node inspect reach.b50, including the original positive compatible hand count.")
    (args.output/"proof.json").write_bytes(json_bytes(report))
    (args.output/"rendered-routes.json").write_bytes(args.routes.read_bytes())

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("solver","routes","output"):parser.add_argument("--"+key,type=Path,required=True)
    parser.add_argument("--driver",type=Path)
    parser.add_argument("--flop",choices=CASES,required=True)
    parser.add_argument("--run",type=int,default=0)
    parser.add_argument("--head",default="")
    parser.add_argument("--preflight",action="store_true")
    run(parser.parse_args())
