"""Publish SB/BB check-call / check-check river hands on priced native 33%-flop sources."""
import argparse
import base64
import gzip
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b514_turn_stab import rates
from hu_b527_checked_barrels import board_row, COLUMNS
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b619_utg_rivers import reproduce
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import prepare_job
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey, game_reach
from hu_trainer_route_gate import compatible
from run10_common import hcls, classes
from verify_hu_multiboard_100bb import lock_scope

MODEL = "ln-opfr-r_model-1ixkq7a"
LINE = "x b33 c/x x/"
RANK = 90
DATA = Path("data")
HISTORIC = {
    "As9h2d": "b1a8e88fd871a2e0e9f8f43f068ed5187df9fc51511a09de93bd663bac2fca8d",
    "As7h3d": "b22c76c1e20f29d34096a197d1e50e3a5e03843bfe43554f6bcb02a9890a1aff",
}


def make_root(pipeline, flop, turns):
    j=pipeline.make_job("SB_BB","gto",flop,"root.json",iters=2000,target=.45,compress=True,
        extract=[dict(prefix=[],street=True)]+[dict(prefix=["x","b33","c",t],raw=True,street=False) for t in turns])
    j.update(flop_oop="33%",flop_ip="33%")
    return j


def make_turn(pipeline, root, turn, rivers):
    parent,=(n for n in root["nodes"] if n["line"]=="x b33 c/" and n["board"].endswith(turn))
    assert parent["pot"]==996 and parent["bets"]==[198,198]
    j=pipeline.make_job("SB_BB","gto",root["flop"],"gto.json",iters=2200,target=.4,rank=.4,compress=False)
    j.update(pipeline.SUB)
    j.update(oop="",ip="",line0=["x","b33","c","/"],turn=turn,pot=996,stack=9502,root_no_bet=True,
        turn_oop="33%,50%,75%",turn_ip="33%,50%,75%",river_oop="50%,75%,100%",river_ip="50%,75%,100%",
        extract=[dict(prefix=[],street=True)]+[dict(prefix=["x","x",r],street=True) for r in rivers])
    for seat,key in enumerate(("oop_w","ip_w")):
        j[key]=[[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4]
    return j


def sources(spec, pipeline, pool, ranges, run, driver, cache):
    flop,turn=spec["flop"],spec["turn"]
    code="B666_R90_"+flop.upper()
    archive=EVIDENCE/("NL2_"+code+".zip")
    assert sha(archive.read_bytes())==spec["archive_sha256"]
    with ZipFile(archive) as z:
        raw={n:z.read(n) for n in z.namelist()}
    assert set(raw)=={n+ext for n in ("root","gto","native") for ext in (".json",".job.json")}
    root=json.loads(raw["root.json"])
    rj=json.loads(raw["root.job.json"])
    if flop in HISTORIC:
        parent=EVIDENCE/("NL2_B666_R90_"+flop.upper()+"_PARENT.zip")
        assert sha(parent.read_bytes())==HISTORIC[flop]
        with ZipFile(parent)as z:
            names=[n for n in z.namelist() if "evidence/"in n]
            assert {SOLVER,RUST}<={z.read(n).decode().strip() for n in names if n.endswith(".txt")}
            m=json.loads(z.read(next(n for n in names if n.endswith(".json") and not n.endswith("pool_stats.json"))))
            assert (m["version"],m["spot"],m["failures"])==("gto","SB_BB",[])
            name="solver/postflop/"+m["file_flop"]
            assert sha(z.read(name))==m["file_flop_sha256"] and z.read(name)==raw["root.json"]
            expected=json.loads(z.read(name.replace(".json",".job.json")))
            expected["out"]="root.json"
            assert rj==expected
    else:
        assert rj==make_root(pipeline,flop,spec["root_turns"])
        if driver:reproduce(rj,root,driver,cache)
    assert (rj["oop"],rj["ip"])==tuple(ranges.to_str(w) for w in ranges.ranges("SB_BB","gto"))
    assert (root["pot"],root["stack"],root["flop"])==(600,9700,flop)
    assert not root["info"].get("lock_stats") and 0<=root["info"]["gto_expl_pct"]<=.5
    root_sha=sha(compact(root))
    root_nodes={n["line"]:n for n in root["nodes"] if len(n["board"])==6}
    for line,seat,action,bets,pot in [("",0,"x",[0,0],600),("x",1,"b33",[0,0],600),("x b33",0,"c",[0,198],798)]:
        n=root_nodes[line]
        assert (n["player"],n["bets"],n["pot"])==(seat,bets,pot) and action in n["acts"]
    j=make_turn(pipeline,root,turn,spec["river_extracts"])
    g=dict(root=root,run=run,version="gto",root_sha256=root_sha,archive_code=code,archive_sha256=spec["archive_sha256"],
        manifest=dict(spot="SB_BB",pot_family="SRP",locks=[],preflop_ranges=dict(source="PINNED_POKER_SOLVER_PREFLOP_CFR",spot="SB_BB")))
    lock,rules=prepare_job(dict(source=g,job=j),"exp_oop",pool,pipeline)
    lock["out"]="native.json"
    e=dict(g,version="exp_oop",verified_gto_parent=dict(run=run,sha256=root_sha),
        manifest=dict(g["manifest"],locks=rules,gto_parent_source_run_id=run,gto_parent_source_sha256=root_sha))
    for source,mode,job in [(g,"gto",j),(e,"native",lock)]:
        assert json.loads(raw[mode+".job.json"])==job
        sub=json.loads(raw[mode+".json"])
        if driver:reproduce(job,sub,driver,cache)
        assert (sub["pot"],sub["stack"],sub["flop"])==(996,9502,flop) and 0<=sub["info"]["gto_expl_pct"]<=.5
        sub.update(line0="x b33 c",turn=turn,rivers=spec["river_extracts"])
        source.update(subgame=sub,source_sha256=sha(raw[mode+".json"]))
    assert not g["subgame"]["info"].get("lock_stats")
    assert 0<=e["subgame"]["info"]["hero_gap_pct"]<=.5
    e.update(applied_rust_rates=e["subgame"]["info"]["lock_stats"],
        measured_lock_application=audit_patterns(e["subgame"],lock,e["manifest"],pool,hero_seat=0))
    return g,e


def decision(source, public, route):
    root,sub=source["root"],source["subgame"]
    n,=(n for n in sub["nodes"] if n["board"]==public and n["line"]==LINE and n["player"]==0)
    assert (n["pot"],n["bets"])==(996,[0,0]) and abs(9502/996/9.5-1)<.05
    row=proof(root,sub,n,game_reach(root,sub)[0])
    info=sub["info"]
    row.update(version=source["version"],spot="SB_BB",family="SRP",flop=sub["flop"],turn=sub["turn"],
        source_run_id=source["run"],source_sha256=source["source_sha256"],archive_sha256=source["archive_sha256"],
        root_sha256=source["root_sha256"],root_gto_stage_gap_pct=root["info"]["gto_expl_pct"],root_locked_hero_gap_pct=None,
        gto_gap_pct=info["gto_expl_pct"],locked_hero_gap_pct=info.get("hero_gap_pct"),
        lock_scope=lock_scope(sub,source["manifest"]["locks"],source["version"]),root_applied_rust_lock_nodes=0,
        subgame_applied_rust_lock_nodes=sum(v["nodes"] for v in info.get("lock_stats",{}).values()))
    found={}
    masks=base64.b64decode(row["compatible_action_mask_b64"],validate=True)
    actions=n["acts"]
    for i,(hand,bits) in enumerate(zip(sub["hands"][0],masks,strict=True)):
        labels=[hcls(hand,public[:6]),hcls(hand,public[:8]),classes(hand,public)[0]]
        if not bits or any(x not in COLUMNS for x in labels):continue
        fc,tc,rc=labels
        label=route[board_row(public)]["river"].get(rc)
        action={"過":"x","下注 ½":"b50","下注 ¾":"b75"}.get(label)
        if (fc not in route[board_row(public[:6])]["flop"] or tc not in route[board_row(public[:8])]["turn"] or
            action not in actions or not bits&(1<<actions.index(action))):continue
        weights=[max(0,n["strat"][a*len(masks)+i]) for a in range(len(actions))]
        total=sum(weights); assert total>0
        found["".join(cardkey(hand))]=(labels,label,dict(action_order=actions,accepted_mask=bits,
            accepted_actions=[a for k,a in enumerate(actions) if bits&(1<<k)],strategy={a:round(w/total,7) for a,w in zip(actions,weights,strict=True)}))
    return row,found


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--solver",type=Path,required=True)
    cli.add_argument("--run",type=int,default=0)
    cli.add_argument("--reproduce-flop")
    cli.add_argument("--out",type=Path,required=True)
    a=cli.parse_args()
    assert subprocess.check_output(["git","-C",a.solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    py=a.solver/"postflop/py"
    assert sha((py/"pipeline.py").read_bytes())==PIPELINE and sha((py/"ranges.py").read_bytes())==RANGES
    sys.path.insert(0,str(py.resolve()))
    import pipeline,ranges
    poolraw=(a.solver/"inputs/pool_stats.json").read_bytes();assert sha(poolraw)==POOL
    pool=json.loads(poolraw)["NL2"]
    route=json.loads(subprocess.check_output(["node","tools/hu_b666_rank90_route.cjs"]))
    model=json.loads((DATA/"nl2_hu_multiboard_status_current.json").read_bytes())["records"][MODEL]
    entries=json.loads((DATA/"nl2_hu_b666_rank90_inputs.json").read_bytes())
    assert 3<=len(entries)<=5 and len({suit_isomorphism_class(x["flop"]) for x in entries})==len(entries)
    contract=json.loads((DATA/"nl2_hu_verified_extensions.json").read_bytes())["trainer_route_contract"]["routes"][MODEL]
    prior=EVIDENCE/"reverified/rank90.json"
    published=json.loads(prior.read_bytes())["pins"] if a.run and prior.exists() else []
    oldruns={(p["flop"],p["archive_sha256"]):p["source_run_id"] for p in published}
    group=dict(rank=RANK,model_id=MODEL,boards=[],pins=[])
    medium=dict(schema="NL2_HU_B666_ORIGINAL_LOCKED_MEDIUM_V1",references={},gto_references={})
    report=[];cache={}
    driver=a.solver/"postflop/pfdriver/target/release/pfdriver" if a.reproduce_flop else None
    for spec in entries:
        if a.reproduce_flop and spec["flop"]!=a.reproduce_flop:continue
        run=oldruns.get((spec["flop"],spec["archive_sha256"]),a.run)
        pair=sources(spec,pipeline,pool,ranges,run,driver,cache)
        public=next(n["board"] for n in pair[0]["subgame"]["nodes"] if n["line"]==LINE and n["board"].endswith(spec["river"]))
        assert compatible(contract,dict(public_board=public,actual_exact_action_line=LINE,acting_seat=0))
        observed=[decision(s,public,route) for s in pair]
        rows,hands=zip(*observed,strict=True)
        common=[]
        for h in sorted(hands[0].keys()&hands[1].keys()):
            labels,label,gpol=hands[0][h];assert hands[1][h][:2]==hands[0][h][:2]
            common.append(dict(hand=h,flop_class=labels[0],turn_class=labels[1],river_class=labels[2],
                displayed_suggestion=label,gto=gpol,nl2=hands[1][h][2]))
        assert common
        report.append(dict(rank=RANK,flop=spec["flop"],public_board=public,shared_hands=len(common),
            compatible_pairs=[r["compatible_hole_card_pairs"] for r in rows],locked_half_pot_candidate=rows[1]["b50"]["candidate"]))
        if a.run:
            g,e=pair
            b,p=emit_board(model,g,e,public,LINE,texture(spec["flop"]),viewer_code="B666_R90_"+spec["flop"].upper())
            b.update(source_run_role="VERIFICATION_OF_LOCAL_NATIVE_RESULTS",origin_solve_run_id=None,
                restricted_flop_bet_sizes_pct=[33] if spec["flop"] not in HISTORIC else None,flop_bet_size_menu=spec["flop_menu"])
            p.update(rendered_decision_hands=common,source_run_role=b["source_run_role"],exact_root_sizing=spec["root_sizing"])
            b["nl2_locked_variants"][0].update(source_run_role=b["source_run_role"],origin_solve_run_id=None,pool_sha256=POOL,
                measurement_policy="STREET_SPECIFIC_POOL_MARGINALS",applied_street_rates=rates(e),
                gto_parent_source_run_id=run,gto_parent_source_sha256=g["root_sha256"],
                viewer_archive_code=p["viewer_archive_code"],viewer_sha256=p["viewer_sha256"])
            group["boards"].append(b);group["pins"].append(p)
            for key,row in zip(("gto_references","references"),rows,strict=True):medium[key][source_key(MODEL,row)]=row
    if a.run:
        assert len(group["boards"])==len(entries)
        prior.write_bytes(json_bytes(group))
        (DATA/"nl2_hu_b666_locked_medium.json").write_bytes(json_bytes(medium))
    a.out.write_bytes(json_bytes(report))


if __name__=="__main__":main()
