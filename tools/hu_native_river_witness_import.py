"""Publish sparse native river witnesses from B613 or B617 GitHub Actions artifacts."""
import argparse
import io
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import EVIDENCE, compact, sha, json_bytes
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL, proof
from hu_b514_turn_stab import rates
from hu_multiboard_promote import texture
from hu_b550_rank69_originals import published_actions
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import prepare_job
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import game_reach
from verify_hu_multiboard_100bb import lock_scope
import hu_b613_rank55_barrels as btn
import hu_b617_rank58 as sb

DATA=Path("data")


def zip_entry(z,name,body):
    entry=ZipInfo(name,date_time=(2026,1,1,0,0,0))
    entry.compress_type=ZIP_DEFLATED
    z.writestr(entry,body)


def authoritative_root(args,flop,z,report):
    if args.rank==55:
        old, job, _ = btn.original(args.originals,flop)
        added=True
    else:
        old,job,added = sb.flop_source(args.originals,flop)
    if added:
        assert json.loads(z.read("flop/job.json"))==job
        raw=z.read("flop/result.json")
        root=json.loads(raw)
    else:
        root=old;raw=compact(root)
    digest = sha(raw if args.rank==55 else compact(root))
    assert digest==report["root_sha256"] and root["hands"]==old["hands"]
    assert not root["info"].get("lock_stats") and 0<=root["info"]["gto_expl_pct"]<=.5
    nd={(n["board"],n["line"],n["player"]):n for n in root["nodes"]}
    assert all(nd[n["board"],n["line"],n["player"]]==n for n in old["nodes"])
    return root,raw,job


def create_pair(args,flop,reg,receipt,route,solver,pool):
    aid=receipt["id"]
    info=receipt["workflow_run"]
    assert info["repository_id"]==1438346845 and info["id"]==args.run
    assert info["head_branch"]=="fix/nl2-hu-lines-audit-20261118"
    assert receipt["name"]==f"B{args.batch}-R{args.rank}-{flop}"
    work=args.archives/f"{aid}.zip"
    assert receipt["digest"]=="sha256:"+sha(work.read_bytes())

    with ZipFile(work) as z:
        report=json.loads(z.read("proof.json"))
        assert (report["rank"],report["model_id"],report["run"],report["flop"])==(args.rank,args.model,args.run,flop)
        root, rawroot, rootjob = authoritative_root(args,flop,z,report)
        choice=next((t for t in report["turns"] if t["checks"]),None)
        if not choice:return None
        turn=choice["turn"];check=choice["checks"][0];public=check["board"]
        root_sha=sha(compact(root))
        spot=reg["solver_profile"]
        if args.rank==55:
            gto,rivers,boundary=btn.turn_job(root,turn,solver)
            spec=dict(source=dict(version="gto",root=root,manifest=dict(spot=spot)),job=gto)
            exp,locks=prepare_job(spec,args.version,pool,solver);exp["out"]="result.json"
            native_pot=2200;paid=550;line0="b50 c"
        else:
            gto,exp,locks,rivers,boundary=sb.make_turn(root,turn,solver,pool,route)
            native_pot=1992;paid=396;line0="x b50 c"
        assert public[:8]==boundary and public[-2:] in rivers
        games={};rows={};hands={}
        payload=io.BytesIO()
        with ZipFile(payload,"w") as selected:
            zip_entry(selected,"worker.json",json_bytes(dict(id=aid,sha256=receipt["digest"],head=info["head_sha"],
                     run=args.run,original_artifact=report["original_artifact"],solver=SOLVER,rust=RUST,pool_sha256=POOL)))
            zip_entry(selected,"flop/job.json",compact(rootjob))
            zip_entry(selected,"flop/result.json",rawroot)
            for v,j,m in [("gto",gto,[]),(args.version,exp,locks)]:
                stem=turn+"-"+v
                jraw=z.read(stem+"/job.json");assert json.loads(jraw)==json.loads(compact(j))
                raw=z.read(stem+"/result.json");sub=json.loads(raw)
                zip_entry(selected,stem+"/job.json",jraw);zip_entry(selected,stem+"/result.json",raw)
                assert (sub["pot"],sub["stack"],sub["flop"])==(j["pot"],j["stack"],flop)
                sub.update(turn=turn,rivers=rivers,line0=line0)
                manifest=dict(spot=spot,pot_family="SRP",locks=m)
                src=dict(root=root,subgame=sub,version=v,run=args.run,source_sha256=sha(raw),manifest=manifest)
                if v==args.version:
                    manifest.update(gto_parent_source_run_id=args.run,gto_parent_source_sha256=root_sha)
                    src.update(verified_gto_parent=dict(run=args.run,sha256=root_sha),
                               measured_lock_application=audit_patterns(sub,j,manifest,pool,args.seat),
                               applied_rust_rates=sub["info"]["lock_stats"])
                node,=(n for n in sub["nodes"] if (n["board"],n["line"],n["player"])==(public,args.line,args.seat))
                assert (node["pot"],node["bets"])==(native_pot,[paid,paid])
                row=proof(root,sub,node,game_reach(root,sub)[0])
                hands[v]=set(published_actions(src,row,route) if args.rank==55 else sb.matching_hands(sub,node,row,route))
                row.update(version=v,spot=spot,family="SRP",flop=flop,turn=turn,source_run_id=args.run,
                           source_sha256=sha(raw),root_sha256=root_sha,gto_gap_pct=sub["info"]["gto_expl_pct"],
                           locked_hero_gap_pct=sub["info"].get("hero_gap_pct"),lock_scope=lock_scope(sub,m,v),
                           root_applied_rust_lock_nodes=0,subgame_applied_rust_lock_nodes=sum(r["nodes"] for r in sub["info"].get("lock_stats",{}).values()))
                games[v]=src;rows[v]=row
        shared=sorted(hands["gto"] & hands[args.version])
        assert shared and shared==check["hands"] and rows[args.version]["b50"]==check["locked_half_pot"]
        code=f"B{args.batch}_R{args.rank}_{flop.upper()}"
        archive=payload.getvalue();digest=sha(archive)
        for v in games:
            games[v].update(archive_code=code,archive_sha256=digest);rows[v]["archive_sha256"]=digest
        b,p=emit_board(reg,games["gto"],games[args.version],public,args.line,texture(flop),viewer_code=code)
        p.update(shared_rendered_checks=shared,worker_artifact=aid,worker_sha256=receipt["digest"][7:],
                 original_flop_artifact=report["original_artifact"])
        b["nl2_locked_variants"][0].update(variant_label="原始 GTO 翻牌策略及 NL2 轉、河牌玩家池節點鎖",applied_street_rates=rates(games[args.version]),
            measurement_policy="STREET_SPECIFIC_POOL_MARGINALS",pool_sha256=POOL,gto_parent_source_run_id=args.run,
            gto_parent_source_sha256=root_sha,viewer_archive_code=p["viewer_archive_code"],viewer_sha256=p["viewer_sha256"])
        (EVIDENCE/("NL2_"+code+".zip")).write_bytes(archive)
        return b,p,rows


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    for name in ["originals","archives","solver"]:cli.add_argument("--"+name,type=Path,required=True)
    cli.add_argument("--batch",type=int,choices=(613,617),required=True)
    cli.add_argument("--run",type=int,required=True)
    args=cli.parse_args()
    if args.batch==613:
        args.rank,args.model,args.version,args.seat,args.line=55,btn.MODEL,"exp_ip",1,btn.LINE
        cases=btn.CASES;route_js="tools/hu_b613_rank55_routes.cjs"
    else:
        args.rank,args.model,args.version,args.seat,args.line=58,sb.MODEL,"exp_oop",0,sb.LINE
        cases=sb.CASES;route_js="tools/hu_b617_sb_routes.cjs"
    assert subprocess.check_output(["git","-C",args.solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    sys.path.insert(0,str((args.solver/"postflop/py").resolve()))
    import pipeline
    bytepool=(args.solver/"inputs/pool_stats.json").read_bytes();assert sha(bytepool)==POOL
    pool=json.loads(bytepool)["NL2"]
    reg=json.loads((DATA/"nl2_hu_multiboard_status_current.json").read_bytes())["records"][args.model]
    route=json.loads(subprocess.check_output(["node",route_js]))
    if args.rank==58:route=route["58"]
    receipts={d["name"]:d for d in (json.loads(f.read_bytes()) for f in args.archives.glob("*.json"))}
    group=dict(rank=args.rank,model_id=args.model,boards=[],pins=[])
    report=dict(schema=f"NL2_HU_B{args.batch}_ORIGINAL_LOCKED_MEDIUM_V1",references={},gto_references={})
    for flop in cases:
        receipt=receipts.get(f"B{args.batch}-R{args.rank}-{flop}")
        if receipt is None:continue
        result=create_pair(args,flop,reg,receipt,route,pipeline,pool)
        if result is None:continue
        b,p,rows=result
        group["boards"].append(b);group["pins"].append(p)
        for v,key in [("gto","gto_references"),(args.version,"references")]:
            row=rows[v];report[key][source_key(args.model,row)]=row
    partial=DATA/f"nl2_hu_b{args.batch}_rank{args.rank}_partial.json"
    if partial.exists():
        previous=json.loads(partial.read_bytes())
        assert previous["group"]["rank"]==args.rank and previous["group"]["model_id"]==args.model
        saved={b["flop"]:(b,p) for b,p in zip(previous["group"]["boards"],previous["group"]["pins"],strict=True)}
        for board,pin in zip(group["boards"],group["pins"],strict=True):
            existing=saved.setdefault(board["flop"],(board,pin))
            assert existing==(board,pin)
        group["boards"]=[b for b,_ in saved.values()]
        group["pins"]=[p for _,p in saved.values()]
        for key in ("references","gto_references"):
            for identity,obs in previous["observations"][key].items():
                assert report[key].setdefault(identity,obs)==obs
    count=len(group["boards"])
    print(f"{count} distinct positive named flops from {len(receipts)} worker artifacts")
    if not count:return
    if count>=3:
        (EVIDENCE/f"reverified/rank{args.rank}.json").write_bytes(json_bytes(group))
        (DATA/f"nl2_hu_b{args.batch}_locked_medium.json").write_bytes(json_bytes(report))
    else:
        partial.write_bytes(json_bytes(dict(group=group,observations=report)))


if __name__=="__main__":
    main()
