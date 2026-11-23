"""Conditional half-pot leads rooted in the original turn ranges, pot, stack and rake."""
import argparse
import gzip
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import EVIDENCE, compact, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b472_street_lock import POOL
from hu_b483_locked_medium import proof
from hu_reverified_board_pair import emit_board, source_case
from hu_sequential_cfr_reach import game_reach
from solve_hu_multiboard_100bb import make_fallbacks
from verify_hu_multiboard_100bb import lock_scope


INPUTS=Path("data/nl2_hu_b492_lead_inputs.json")
OUT=Path("data/nl2_hu_b492_half_pot_leads.json")
VERSIONS=("gto","exp_oop")
SCOPE="CONDITIONAL_TURN_SUBGAME_WITH_ORIGINAL_VERSION_FLOP_REACH_AND_HALF_POT_LEAD"


def read(path):
    return json.loads(path.read_bytes())


def write(path,data):
    path.write_bytes(compact(data)+b"\n")


def native_target(sub,target):
    found=[n for n in sub["nodes"] if (n["board"],n["line"],n["player"])==(target["public"],target["line"],target["seat"])]
    assert len(found)<=1
    return found[0] if found else None


def originals(directory,group,version):
    ref=group[version]
    path=directory/f"{ref['id']}.zip"
    assert sha(path.read_bytes())==ref["zip_sha256"]
    if (directory/f"{ref['id']}.json").exists():
        info=read(directory/f"{ref['id']}.json")
        assert (info["id"],info["digest"],info["workflow_run"]["id"],info["workflow_run"]["repository_id"])==(
            ref["id"],"sha256:"+ref["zip_sha256"],ref["run"],1438346845)
    flop,turn=group["flop"],group["turn"]
    with zipfile.ZipFile(path) as archive:
        pins={archive.read(n).decode().strip() for n in archive.namelist() if n.startswith("evidence/") and n.endswith(".txt")}
        assert {SOLVER,RUST} <= pins
        mf,=[n for n in archive.namelist() if n.startswith("evidence/") and n.endswith(".json")]
        manifest_raw=archive.read(mf)
        m=json.loads(manifest_raw)
        assert (m["spot"],m["version"])==(group["spot"],version) and not m["failures"]
        multi=m["schema"]=="NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1"
        assert multi or m["schema"]=="HU_MISSING_ACTION_HISTORY_CFR_V1"
        case,=[c for c in m["cases"] if c.get("source_sha256",c.get("sub_sha256"))==ref["source_sha256"]]
        assert (case["line"],case["turn"])==(group["targets"][0]["parent"],turn)
        rootpath="solver/postflop/"+(m["file_flop"] if multi else case["flop_json"])
        subpath="solver/postflop/"+(case["source_path"] if multi else case["sub_json"])
        rootraw,oldraw=archive.read(rootpath),archive.read(subpath)
        assert (sha(rootraw),sha(oldraw))==(ref["root_sha256"],ref["source_sha256"])
        rootjob=archive.read(rootpath.replace(".json",".job.json"))
        oldjob=archive.read(subpath.replace(".json",".job.json"))
    root,old,rj,job=map(json.loads,(rootraw,oldraw,rootjob,oldjob))
    assert (root["flop"],old["flop"],old["turn"],old["line0"])==(flop,flop,turn,case["line"])
    assert job["flop"]==flop and job["turn"]==turn and job["line0"]==case["line"].split()+["/"]
    assert (job["pot"],job["stack"],job["rake_rate"],job["rake_cap"])==(old["pot"],old["stack"],.05,1000)
    assert rj.get("hero")==job.get("hero")==({"gto":None,"exp_oop":0}[version])
    parent,=[n for n in root["nodes"] if n["line"]==case["line"]+"/" and n["board"][-2:]==turn]
    assert (old["pot"],old["stack"])==(parent["pot"],root["stack"]-parent["bets"][0])
    for seat,name in enumerate(("oop_w","ip_w")):
        assert job[name]==[[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat]) if w>1e-4]
    for target in group["targets"]:
        n=native_target(old,target)
        assert n is not None and n["acts"]==["x"] and n["player"]==0
        assert (old["stack"]-max(n["bets"]))*2>=n["pot"]
    raw_files={"original-flop.json":rootraw,"original-flop.job.json":rootjob,"original-subgame.json":oldraw,
               "original-subgame.job.json":oldjob,"original-manifest.json":manifest_raw}
    return root,old,job,raw_files


def preparation(group,version,job,pipeline,pool):
    changed=deepcopy(job)
    turn_lead=any(len(t["public"])==8 for t in group["targets"])
    river_lead=any(len(t["public"])==10 for t in group["targets"])
    if turn_lead:
        assert changed["root_no_bet"]
        changed.update(root_no_bet=False,turn_oop="50%")
    if river_lead:
        assert not changed.get("river_donk")
        changed["river_donk"]="50%"
    changed["out"]="conditional.json"
    changed["target_pct"]=min(changed["target_pct"],.45)
    changed["iters"]=max(changed["iters"],2000)
    rules,meta=make_fallbacks(group["spot"],version,pool,pipeline.lock_list,group["flop"],by_street=True)
    if version=="exp_oop":
        assert changed["hero"]==0 and rules
        changed.update(locks=json.loads(compact(rules)),rank_pct=.45)
    else:
        assert not rules and not changed.get("locks") and changed.get("hero") is None
    metadata=[dict(pat=r["pat"],source=r.get("src"),scope=r.get("scope","PINNED_MEASURED_NL2_SOURCE"),
                   n=r.get("n"),**({"street":r["street"]} if "street" in r else {})) for r in meta]
    assert [r["pat"] for r in metadata]==[r["pat"] for r in changed.get("locks",[])]
    return changed,metadata


def code_for(key,version):
    return f"B492_{key.upper()}_{version.upper()}"


def zip_payload(path,entries):
    with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,data in sorted(entries.items()):
            info=zipfile.ZipInfo(name)
            info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,data)


def original_files(group,version,files):
    return dict(original_run_id=group[version]["run"],original_archive_id=group[version]["id"],
                original_archive_sha256=group[version]["zip_sha256"],original_source_sha256=group[version]["source_sha256"],
                original_root_sha256=group[version]["root_sha256"],original_job_sha256=sha(files["original-subgame.job.json"]),
                original_flop_job_sha256=sha(files["original-flop.job.json"]))


def solve(args,key,group,version,pipeline,pool):
    directory=args.work.resolve()
    directory.mkdir(exist_ok=True,parents=True)
    _,_,oldjob,files=originals(args.originals,group,version)
    job,meta=preparation(group,version,oldjob,pipeline,pool)
    jobraw=compact(job)
    (directory/"conditional.job.json").write_bytes(jobraw)
    result=dict(run_id=args.run_id,group=key,version=version,scope=SCOPE,solver=SOLVER,rust=RUST,pool_sha256=POOL,
                **original_files(group,version,files))
    try:
        subprocess.run([str(args.driver.resolve()),"conditional.job.json"],cwd=directory,check=True,timeout=300)
    except (subprocess.TimeoutExpired,subprocess.CalledProcessError) as e:
        result.update(status="UNAVAILABLE",reason=type(e).__name__)
        write(directory/"outcome.json",result)
        return
    raw=(directory/"conditional.json").read_bytes()
    envelope=dict(result,solver_output_sha256=sha(raw),conditional_job_sha256=sha(jobraw))
    files.update({"conditional.job.json":jobraw,"conditional.json":raw,"provenance.json":compact(envelope),
                  "street-lock-metadata.json":compact(meta)})
    pack=directory/f"NL2_{code_for(key,version)}.zip"
    zip_payload(pack,files)
    write(directory/"outcome.json",dict(envelope,status="SOLVED",archive=pack.name,archive_sha256=sha(pack.read_bytes())))


def unpack(directory,key,group,version,original_dir,pipeline,pool,run):
    result_path=directory/"outcome.json"
    if not result_path.exists():
        return None,"NO_COMPLETED_ORIGINAL_SOLVER_OUTPUT"
    result=read(result_path)
    assert (result["run_id"],result["group"],result["version"],result["scope"],result["solver"],result["rust"],result["pool_sha256"])==(
        run,key,version,SCOPE,SOLVER,RUST,POOL)
    if result["status"]=="UNAVAILABLE":
        return None,result["reason"]
    assert result["status"]=="SOLVED"
    root,old,oldjob,files=originals(original_dir,group,version)
    job,metadata=preparation(group,version,oldjob,pipeline,pool)
    pack=directory/result["archive"]
    code=code_for(key,version)
    assert pack.name==f"NL2_{code}.zip" and sha(pack.read_bytes())==result["archive_sha256"]
    with zipfile.ZipFile(pack) as z:
        assert all(z.read(f)==data for f,data in files.items())
        assert json.loads(z.read("provenance.json"))=={k:v for k,v in result.items() if k not in ("status","archive","archive_sha256")}
        assert all(result[k]==v for k,v in original_files(group,version,files).items())
        assert z.read("conditional.job.json")==compact(job) and sha(compact(job))==result["conditional_job_sha256"]
        assert z.read("street-lock-metadata.json")==compact(metadata)
        raw=z.read("conditional.json")
        assert sha(raw)==result["solver_output_sha256"]
    dest=EVIDENCE/pack.name
    shutil.copyfile(pack,dest)
    sub=json.loads(raw)
    assert (sub["hands"],sub["flop"],sub["pot"],sub["stack"])==(old["hands"],old["flop"],old["pot"],old["stack"])
    sub.update(line0=old["line0"],turn=group["turn"])
    manifest=dict(spot=group["spot"],pot_family=group["family"],locks=metadata)
    details=dict(original_files(group,version,files),raw_path=dest.as_posix(),raw_sha256=result["archive_sha256"],
                 conditional_job_sha256=result["conditional_job_sha256"],gto_gap_pct=sub["info"]["gto_expl_pct"],
                 locked_hero_gap_pct=sub["info"].get("hero_gap_pct"),turn_root_changes=job["root_no_bet"]!=oldjob["root_no_bet"],
                 river_donk=job.get("river_donk"),frozen_root_applied_lock_nodes=sum(s["nodes"] for s in root["info"].get("lock_stats",{}).values()))
    if version=="exp_oop":
        stats=sub["info"]["lock_stats"]
        if stats:
            details["checked_lock_patterns"]=audit_patterns(sub,job,manifest,pool)
        details["applied_rust_rates"]={k:dict(nodes=s["nodes"],actual_fold=s["fold"],actual_aggression=s["agg"]) for k,s in stats.items()}
    return dict(root=root,subgame=sub,version=version,run=run,source_sha256=sha(raw),manifest=manifest,
                archive_code=code,archive_sha256=result["archive_sha256"],old=old,details=details),None


def check_target(source,target):
    node=native_target(source["subgame"],target)
    old=native_target(source["old"],target)
    t=target["line"]
    row=dict(source_run_id=source["run"],source_sha256=source["source_sha256"],source_actions=node["acts"] if node else [],
             public_board=target["public"],line=t,acting_seat=target["seat"],version=source["version"],**source["details"])
    if not node or "b50" not in node["acts"]:
        return dict(row,status="UNAVAILABLE",reason="RUST_MENU_MISSING_EXACT_B50_EDGE")
    sub=source["subgame"]
    assert (node["pot"],node["bets"])==(old["pot"],old["bets"]) and node["player"]==0
    child_line=t+("" if t.endswith("/") else " ")+"b50"
    child,=[n for n in sub["nodes"] if (n["board"],n["line"],n["player"])==(target["public"],child_line,1)]
    bet=child["pot"]-node["pot"]
    assert abs(2*bet-node["pot"])<=1 and child["bets"][0]-node["bets"][0]==bet
    row.update(lead_chips=bet,pot_chips=node["pot"],remaining_chips=sub["stack"]-max(node["bets"]))
    if len(target["public"])==10:
        turnboard=target["public"][:8]
        prior,=[n for n in sub["nodes"] if (n["line"],n["board"],n["player"])==(target["parent"]+"/x b50",turnboard,0)]
        assert "c" in prior["acts"] and node["bets"][0]==node["bets"][1]
        row["turn_call_propagation"]=dict(parent=prior["line"],caller=0,call_amount=prior["bets"][1]-prior["bets"][0],
                                          resulting_matched_bets=node["bets"],turn_public_board=turnboard)
    if not 0<=row["gto_gap_pct"]<=.5 or (source["version"]=="exp_oop" and not 0<=row["locked_hero_gap_pct"]<=.5):
        return dict(row,status="UNAVAILABLE",reason="SOLVER_CONVERGENCE_THRESHOLD")
    scope=lock_scope(sub,source["manifest"]["locks"],source["version"])
    if source["version"]=="exp_oop" and (not row["applied_rust_rates"] or not scope["observed_marginal_source_nodes"]):
        return dict(row,status="UNAVAILABLE",reason="NO_APPLIED_MEASURED_CONDITIONAL_LOCK")
    row["villain_lock_scope"]=scope
    row.update(proof(source["root"],sub,node,game_reach(source["root"],sub)[0]))
    return row


def attach_view(row,code):
    path=EVIDENCE/f"NL2_MULTIBOARD_{code}.json.gz"
    row.update(viewer_path=path.as_posix(),viewer_sha256=sha(path.read_bytes()))


def record(group,target,sources,missing,model,run):
    public,line,seat=target["public"],target["line"],target["seat"]
    orig,other=group["gto"],group["exp_oop"]
    old,=[b for b in model["certified_3_to_5_exact_flop_boards"] if b["public_board"]==public and b["actual_exact_action_line"]==line and b["acting_seat"]==seat]
    assert (old["source_sha256"],old["source_run_id"])==(orig["source_sha256"],orig["run"])
    assert any((l["run_id"],l["sha256"],l["version"])==(other["run"],other["source_sha256"],"exp_oop") for l in old["nl2_locked_variants"])
    row=dict(model_id=model["model_id"],rank=target["rank"],public_board=public,line=line,seat=seat,flop=group["flop"],
             turn=group["turn"],original_gto_run=orig["run"],original_gto_sha256=orig["source_sha256"],
             original_lock_run=other["run"],original_lock_sha256=other["source_sha256"],scope=SCOPE,source_run_id=run,
             board=None,pin=None,unavailable_versions=dict(missing))
    for ver in VERSIONS:
        if ver not in sources:
            row[ver]=None
            continue
        try:
            result=check_target(sources[ver],target)
            result.update(spot=group["spot"],family=group["family"],flop=group["flop"],turn=group["turn"])
            row[ver]=result
        except (AssertionError,KeyError,ValueError) as error:
            row["unavailable_versions"][ver]=f"TARGET_SOURCE_VERIFICATION_FAILED: {type(error).__name__} {error}"
            row[ver]=None
    outcomes=[row[v]["status"] if row[v] else "UNAVAILABLE" for v in VERSIONS]
    code=f'B492_R{target["rank"]}_{group["flop"].upper()}_{public[6:].upper()}_{run}'
    if all(v=="POSITIVE_JOINT_REACH" for v in outcomes):
        try:
            b,p=emit_board(model,sources["gto"],sources["exp_oop"],public,line,old["flop_texture"],viewer_code=code)
            assert b and p
            b["source_kind"]=SCOPE
            b["half_pot_conditional_comparison"]=True
            p["half_pot_conditional_comparison"]=True
            for version in VERSIONS:
                attach_view(row[version],code)
            row.update(status="BOTH_POSITIVE",board=b,pin=p)
        except (AssertionError,KeyError,ValueError) as err:
            row["status"]="UNAVAILABLE"
            row["unavailable_versions"]["pair"]=f"PAIR_VIEWER_VERIFICATION_FAILED: {type(err).__name__} {err}"
    else:
        row["status"]="UNAVAILABLE" if "UNAVAILABLE" in outcomes else "ZERO_JOINT_REACH"
        # Retain positive native output if the other version is missing or has zero reach.
        for version in VERSIONS:
            if not row[version] or row[version]["status"]!="POSITIVE_JOINT_REACH":
                continue
            source=sources[version]
            try:
                case=source_case(model,source,public,line,seat)
                assert case is not None
                code_one=code+"_"+version.upper()
                bundle=dict(schema="NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1",source_run_id=run,
                            original_archive_sha256=source["archive_sha256"],errors=[],no_generic_texture_certification=True,
                            artifacts=[dict(cases=[case[0]])])
                path=EVIDENCE/f"NL2_MULTIBOARD_{code_one}.json.gz"
                path.write_bytes(gzip.compress(compact(bundle),mtime=0))
                attach_view(row[version],code_one)
            except (AssertionError,KeyError,ValueError) as err:
                row["unavailable_versions"][version]=f"VIEWER_VERIFICATION_FAILED: {type(err).__name__} {err}"
    return row


def materialize(args,inputs,pipeline,pool):
    freeze=inputs["freeze"]
    historical=json.loads(subprocess.check_output(["git","show",freeze+":data/nl2_hu_multiboard_status_current.json"]))
    results=[]
    for key,g in inputs["groups"].items():
        sources,missing={},{}
        for ver in VERSIONS:
            folder=args.work/f"B492-source-{key}-{ver}"
            try:
                source,reason=unpack(folder,key,g,ver,args.originals,pipeline,pool,args.run_id)
            except (AssertionError,KeyError,ValueError,FileNotFoundError,zipfile.BadZipFile) as err:
                source=None
                reason=f"SOURCE_VERIFICATION_FAILED: {type(err).__name__} {err}"
            if source is None:missing[ver]=reason
            else:sources[ver]=source
        for t in g["targets"]:
            results.append(record(g,t,sources,missing,historical["records"][t["model"]],args.run_id))
    short=inputs["under_half_pot_stack"]
    for s in short:
        m=historical["records"][s["model"]]
        b,=[b for b in m["certified_3_to_5_exact_flop_boards"] if (b["public_board"],b["actual_exact_action_line"])==(s["board"],s["line"])]
        assert b["actual_spr"]==s["spr"]<.5 and 2*b["actual_effective_stack_bb"]<b["actual_pot_bb"]
    assert len(results)==17 and len(short)==7
    write(OUT,dict(schema="NL2_HU_B492_CONDITIONAL_HALF_POT_LEADS_V1",source_run_id=args.run_id,freeze=freeze,
                   poker_solver_pin=SOLVER,rust_pin=RUST,pool_sha256=POOL,inputs_sha256=sha(INPUTS.read_bytes()),
                   records=results,under_half_pot_stack=short))
    print({s:sum(r["status"]==s for r in results) for s in ("BOTH_POSITIVE","ZERO_JOINT_REACH","UNAVAILABLE")})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--group")
    p.add_argument("--version",choices=VERSIONS)
    p.add_argument("--solver",type=Path)
    p.add_argument("--originals",type=Path)
    p.add_argument("--work",type=Path)
    p.add_argument("--run-id",type=int)
    p.add_argument("--driver",type=Path)
    p.add_argument("--list-artifacts",action="store_true")
    p.add_argument("--assemble",action="store_true")
    p.add_argument("--preflight",action="store_true")
    p.add_argument("--verify-published",action="store_true")
    args=p.parse_args()
    inputs=read(INPUTS)
    groups=inputs["groups"]
    if args.list_artifacts:
        chosen=[groups[args.group]] if args.group else groups.values()
        print(" ".join(str(i) for i in sorted({g[v]["id"] for g in chosen for v in VERSIONS})))
        return
    if args.verify_published:
        d=read(OUT)
        assert d["inputs_sha256"]==sha(INPUTS.read_bytes()) and len(d["records"])==17
        for r in d["records"]:
            for ver in VERSIONS:
                s=r[ver]
                if s and s.get("raw_path"):assert sha(Path(s["raw_path"]).read_bytes())==s["raw_sha256"]
                if s and s.get("viewer_path"):assert sha(Path(s["viewer_path"]).read_bytes())==s["viewer_sha256"]
            if r["status"]=="BOTH_POSITIVE":
                assert all(r[v]["compatible_hole_card_pairs"]>0 and "b50" in r[v]["source_actions"] for v in VERSIONS)
                assert r["board"] and r["pin"]
            else:assert r["board"] is None and r["pin"] is None
        return
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",str(solver),"rev-parse","HEAD"],text=True).strip()==SOLVER
    assert sha((solver/"inputs/pool_stats.json").read_bytes())==POOL
    pool=read(solver/"inputs/pool_stats.json")["NL2"]
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    if args.preflight:
        count=0
        for g in groups.values():
            for v in VERSIONS:
                _,_,job,_=originals(args.originals,g,v)
                preparation(g,v,job,pipeline,pool)
                count+=1
        print(f"{count} original solver jobs verified")
        return
    assert args.run_id and args.run_id>0
    if args.assemble:
        materialize(args,inputs,pipeline,pool)
    else:
        assert args.driver and args.group and args.version
        driver=args.driver.resolve()
        assert driver == solver/"postflop/pfdriver/target/release/pfdriver"
        engine=solver/"postflop/postflop-solver"
        assert subprocess.check_output(["git","-C",str(engine),"rev-parse","HEAD"],text=True).strip()==RUST
        solve(args,args.group,groups[args.group],args.version,pipeline,pool)


if __name__=="__main__":
    main()
