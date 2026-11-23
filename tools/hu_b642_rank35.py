"""Verify the limped BB check after a half-pot flop lead and a checked-through turn."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import tempfile
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b481_rank27_limp_rivers import check_limp_source
from hu_b483_locked_medium import POOL, proof
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b617_rank58 import hcls, classes, texture
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision
from hu_native_river_witness_import import zip_entry
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey, game_reach

DATA = Path("data")
MODEL = "ln-iso-lmp_r_model-pjewx6"
LINE = "b50 c/x x/"
PATTERN = "^b50 c/x x/b(50|100)$"
CASES = {
    "2c2d4h": ("B500_LMP_CO_BB_2C2D4H_4C_GTO", "5887fdf1eefedc863b39ebe174fc1fd4b24bd97225ebd15dd820b70e91a869a2", "4c"),
    "3s3h2d": ("B492_LMP_CO_BB_3S3H2D_7D_GTO", "1f2347f93c576473108723c8ce76b08c179b5e225ff0b3b75539e5752b9c741e", "2s"),
    "4s4h2d": ("B492_LMP_CO_BB_4S4H2D_8S_GTO", "356d24c42e6a64aeeba51f484ffb9ceded184b95b560f3bc52d51492bfd8d911", "2s"),
    "5c5d2h": ("B500_LMP_CO_BB_5C5D2H_KC_GTO", "5262789c631959bde7be45dc0001866133b06aed464c8645633d1d1eefea4a30", "2c"),
}


def native(driver, folder, job):
    folder.mkdir(exist_ok=True, parents=True)
    (folder/"job.json").write_bytes(compact(job))
    subprocess.run([driver, "job.json"], cwd=folder, check=True)
    return (folder/job["out"]).read_bytes()


def eligible(source, route):
    root, sub = source["root"], source["subgame"]
    reach = game_reach(root, sub)[0]
    found = {}
    for node in sub["nodes"]:
        if (node["line"], node["player"]) != (LINE, 0):
            continue
        board = node["board"]
        assert (node["pot"], node["bets"]) == (500, [0, 0]) and "b50" in node["acts"]
        row = proof(root, sub, node, reach)
        mask = base64.b64decode(row["compatible_action_mask_b64"], validate=True)
        check = 1 << node["acts"].index("x")
        found[board] = {"".join(cardkey(h)) for h, bits in zip(sub["hands"][0], mask, strict=True)
                        if bits & check and hcls(h, board[:6]) in route[texture(board[:6])]["flop"]
                        and hcls(h, board[:8]) in route[texture(board[:8])]["turn"]
                        and classes(h, board)[0] in route[texture(board)]["river"]}
    return found


def solve(flop, pool, run, driver, work, out):
    parent_code, parent_sha, turn = CASES[flop]
    archive = EVIDENCE / f"NL2_{parent_code}.zip"
    assert sha(archive.read_bytes()) == parent_sha
    with ZipFile(archive) as z:
        root_bytes, rjob, sjob, manifest, pin = [z.read(n) for n in (
            "original-flop.json","original-flop.job.json","original-subgame.job.json",
            "original-manifest.json","provenance.json")]
    root = json.loads(root_bytes)
    root_job, turn_job, manifest, pin = map(json.loads, [rjob,sjob,manifest,pin])
    assert (pin["solver"],pin["rust"],pin["pool_sha256"],pin["version"]) == (SOLVER,RUST,POOL,"gto")
    assert (sha(root_bytes),sha(rjob),sha(sjob)) == (pin["original_root_sha256"],pin["original_flop_job_sha256"],pin["original_job_sha256"])
    assert manifest["file_flop_sha256"] == sha(root_bytes) and manifest["spot"] == "LMP_CO_BB" and not manifest["failures"]
    check_limp_source(dict(manifest=manifest,root_job=root_job,subgame_job=turn_job))
    assert not root_job.get("locks") and root_job["flop"] == flop
    if not any(n["line"]=="b50 c/" and n["board"].endswith(turn) and n.get("wr") for n in root["nodes"]):
        root_job = dict(root_job,out="root.json",extract=root_job["extract"]+[
            dict(prefix=["b50","c",turn],street=False,raw=True)])
        old=root
        root_bytes=native(driver,work/"flop",root_job)
        root=json.loads(root_bytes)
        by={(n["board"],n["line"],n["player"]):n for n in root["nodes"]}
        assert old["hands"]==root["hands"] and all(by[n["board"],n["line"],n["player"]]==n for n in old["nodes"])
    assert 0 <= root["info"]["gto_expl_pct"] <= .5 and not root["info"].get("lock_stats")
    boundary,=(n for n in root["nodes"] if n["line"]=="b50 c/" and n["board"].endswith(turn))
    assert boundary["pot"]==500 and boundary["bets"]==[125,125]
    public=boundary["board"]
    cards={public[i:i+2] for i in (0,2,4,6)}
    rivers=[r+s for r in "23456789TJQKA" for s in "cdhs" if r+s not in cards and texture(public+r+s)=="paired"]
    job=dict(turn_job,flop=flop,turn=turn,out="gto.json",extract=[dict(prefix=[],street=True)]+[
        dict(prefix=["x","x",r],street=True) for r in rivers])
    assert (job["line0"],job["pot"],job["stack"])==(["b50","c","/"],500,9775)
    for i,key in enumerate(("oop_w","ip_w")):
        job[key]=[[h,w] for h,w in zip(root["hands"][i],boundary["wr"][i],strict=True) if w>1e-4]
    rate=pool["HU_facing_bet"]["3"]["by_pot"]["limped"]
    assert rate["n"]==44882 and abs(sum(rate[k] for k in ("fold","call","raise"))-100)<.15
    rule=dict(pat=PATTERN,fold=rate["fold"]/100,**{"raise":rate["raise"]/100})
    lock_meta=dict(rule,n=rate["n"],source="NL2.HU_facing_bet[3].by_pot[limped]",scope="OBSERVED_LIMPED_RIVER_MARGINAL")
    lock_job=dict(job,hero=0,locks=[rule],iters=2500,target_pct=.35,rank_pct=.35,out="native.json")
    code="B642_R35_"+flop.upper()
    raw_gto=native(driver,work/"gto",job)
    raw_lock=native(driver,work/"locked",lock_job)
    root_sha=sha(compact(root))
    sources=[]
    for mode,body,locks in [("gto",raw_gto,[]),("exp_oop",raw_lock,[lock_meta])]:
        sub=json.loads(body)
        assert (sub["flop"],sub["pot"],sub["stack"])==(flop,500,9775)
        assert 0<=sub["info"]["gto_expl_pct"]<=.5
        if mode=="gto":
            assert not sub["info"].get("lock_stats")
        else:
            assert 0<=sub["info"]["hero_gap_pct"]<=.5
            measure=sub["info"]["lock_stats"]
            assert set(measure)=={PATTERN} and measure[PATTERN]["nodes"]>0
            for actual,target in [("fold","fold"),("agg","raise")]:
                assert abs(measure[PATTERN][actual]-rule[target])<.002
        sub.update(line0="b50 c",turn=turn,rivers=rivers)
        source=dict(version=mode,root=root,subgame=sub,run=run,source_sha256=sha(body),archive_code=code,
                    manifest=dict(spot="LMP_CO_BB",pot_family="LMP",locks=locks))
        if locks:
            source["manifest"].update(gto_parent_source_run_id=run,gto_parent_source_sha256=root_sha)
            source["verified_gto_parent"]=dict(run=run,sha256=root_sha)
        sources.append(source)
    route=json.loads(subprocess.check_output(["node","tools/hu_b642_rank35_routes.cjs"]))
    g,e=(eligible(source,route) for source in sources)
    common=sorted((b,sorted(g[b]&e[b])) for b in g if g[b]&e[b])
    result=dict(flop=flop,turn=turn,source_run=run,parent_archive=parent_code,
                original_artifact=pin["original_archive_id"],paired_rivers=len(common))
    out.mkdir(parents=True,exist_ok=True)
    if common:
        board,hands=common[0]
        bundle=EVIDENCE/f"NL2_{code}.zip"
        with ZipFile(bundle,"w") as z:
            for name,body in [("parent.json",json_bytes(dict(code=parent_code,sha256=parent_sha,artifact=pin["original_archive_id"]))),
                              ("root.job.json",compact(root_job)),("root.json",root_bytes),("gto.job.json",compact(job)),
                              ("gto.json",raw_gto),("native.job.json",compact(lock_job)),("native.json",raw_lock)]:
                zip_entry(z,name,body)
        for source in sources:source["archive_sha256"]=sha(bundle.read_bytes())
        model=json.loads((DATA/"nl2_hu_multiboard_status_current.json").read_bytes())["records"][MODEL]
        assert model["assumed_model_node_spr"]==19.55
        b,p=emit_board(model,*sources,board,LINE,texture(flop),viewer_code=code)
        assert b and p and p["common_legal_hero_combos"]>=len(hands)>0
        p.update(shared_rendered_checks=hands,original_flop_artifact=pin["original_archive_id"])
        lock=b["nl2_locked_variants"][0]
        lock.update(variant_label="CO 面對河牌下注的溜入底池實測回應",measurement_policy="LIMPED_RIVER_ALL_SIZES_MARGINAL",
                    applied_street_rates=[dict(street=3,token="b50|b100",n=rate["n"],nodes=measure[PATTERN]["nodes"],
                         fold_pct=100*measure[PATTERN]["fold"],raise_pct=100*measure[PATTERN]["agg"])],pool_sha256=POOL)
        rows=[audit_decision(s,board,LINE,0,root_sha) for s in sources]
        result.update(board=b,pin=p,rows=rows)
        for path in [bundle,EVIDENCE/f"NL2_MULTIBOARD_{code}.json.gz"]:
            (out/path.name).write_bytes(path.read_bytes())
    (out/"summary.json").write_bytes(json_bytes(result))


def collect(directory):
    group=dict(rank=35,model_id=MODEL,boards=[],pins=[])
    medium=dict(schema="NL2_HU_B642_ORIGINAL_LOCKED_MEDIUM_V1",references={},gto_references={})
    for flop in CASES:
        folder=directory / ("B642-"+flop)
        result=json.loads((folder/"summary.json").read_bytes())
        assert result["flop"]==flop
        if not result["paired_rivers"]:continue
        board,pin=result["board"],result["pin"]
        assert board["flop"]==flop and pin["shared_rendered_checks"] and board["strict_full_street_combo_reachable"]>0
        for name,expected in [(f'NL2_{pin["archive_code"]}.zip',pin["archive_sha256"]),
                              (f'NL2_MULTIBOARD_{pin["viewer_archive_code"]}.json.gz',pin["viewer_sha256"])]:
            raw=(folder/name).read_bytes()
            assert sha(raw)==expected
            (EVIDENCE/name).write_bytes(raw)
        group["boards"].append(board);group["pins"].append(pin)
        for key,row in zip(("gto_references","references"),result["rows"],strict=True):
            medium[key][source_key(MODEL,row)]=row
    assert len({suit_isomorphism_class(b["flop"]) for b in group["boards"]}) == len(group["boards"])
    if len(group["boards"])>=3:
        (EVIDENCE/"reverified/rank35.json").write_bytes(json_bytes(group))
        (DATA/"nl2_hu_b642_locked_medium.json").write_bytes(json_bytes(medium))
    elif group["boards"]:
        (DATA/"nl2_hu_b642_rank35_partial.json").write_bytes(json_bytes(dict(group=group,observations=medium)))
    print(len(group["boards"]), "distinct reachable rank35 flops")


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--collect",type=Path)
    cli.add_argument("--solver",type=Path)
    cli.add_argument("--run",type=int)
    cli.add_argument("--flop",choices=CASES)
    cli.add_argument("--output",type=Path)
    args=cli.parse_args()
    if args.collect:
        collect(args.collect)
    else:
        solver=args.solver.resolve()
        for folder,revision in [(solver,SOLVER),(solver/"postflop/postflop-solver",RUST)]:
            assert subprocess.check_output(["git","-C",folder,"rev-parse","HEAD"],text=True).strip()==revision
        pool_bytes=(solver/"inputs/pool_stats.json").read_bytes()
        assert sha(pool_bytes)==POOL and args.run>0
        with tempfile.TemporaryDirectory() as work:
            solve(args.flop,json.loads(pool_bytes)["NL2"],args.run,solver/"postflop/pfdriver/target/release/pfdriver",Path(work),args.output)
