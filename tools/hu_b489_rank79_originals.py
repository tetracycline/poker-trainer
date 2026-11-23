"""Recheck original UTG-CO 50%-call/check sources and independently solve missing CO-IP locks."""
import argparse
import gzip
import json
from pathlib import Path
import struct
import subprocess
import sys
import zipfile

from hu_b467_river_source_gate import EVIDENCE, compact, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIN, RUST, POOL, PIPELINE, RANGES, proof, encode
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import game_reach
from solve_hu_missing_branches import EXTRA_SPOTS
from solve_hu_multiboard_100bb import make_fallbacks
from verify_hu_multiboard_100bb import lock_scope


MODEL = "ln-ipc-t_model-1cla93g"
LINE = "b50 c/x"
FROZEN = Path("data/nl2_hu_multiboard_status_v53_b465_rank218.json")
PINS = json.loads(Path("data/nl2_hu_b489_originals.json").read_bytes())
OLD = Path("data/nl2_hu_b489_locked_medium.json")
REPORT = Path("data/nl2_hu_b489_rank79_attempts.json")
CANDIDATES = {"KsQh4d":["Tc"], "QsJh4d":["7s"], "KsQh3d":["Tc","7h","7s"]}
PAIR_RUN = 44971994483


def read(path):
    return json.loads(path.read_bytes())


def save(path,obj):
    path.write_bytes(encode(obj)+b"\n")


def audit_node(source):
    root,sub = source["root"],source["subgame"]
    n, = [n for n in sub["nodes"] if (n["line"],n["player"],len(n["board"])) == (LINE,1,8)]
    assert (n["pot"],sub["stack"]-max(n["bets"])) == (1300,9425)
    assert n["board"][6:] == sub["turn"]
    row = proof(root,sub,n,game_reach(root,sub)[0])
    m = source["manifest"]
    scope = lock_scope(sub,m["locks"],source["version"])
    scope.pop("matching_examples",None)
    scope.pop("caveat",None)
    return dict(row, source_run_id=source["run"],source_sha256=source["source_sha256"],
                archive_id=source.get("artifact_id"),archive_sha256=source["archive_sha256"],
                version=source["version"],flop=sub["flop"],turn=sub["turn"],spot="UTG_CO",family="SRP",
                root_sha256=m["file_flop_sha256"],gto_gap_pct=sub["info"]["gto_expl_pct"],
                locked_hero_gap_pct=sub["info"].get("hero_gap_pct"),lock_scope=scope,
                root_applied_rust_lock_nodes=sum(v["nodes"] for v in root["info"].get("lock_stats",{}).values()),
                subgame_applied_rust_lock_nodes=sum(v["nodes"] for v in sub["info"].get("lock_stats",{}).values()))


def pack(source, flop, turn, batch="B489"):
    code=f'{batch}_R79_{flop.upper()}_{turn.upper()}_{source["version"].upper()}'
    raw=gzip.compress(compact(source),mtime=0)
    raw=raw[:9]+bytes([255])+raw[10:]
    (EVIDENCE/f"NL2_{code}.json.gz").write_bytes(raw)
    source.update(archive_code=code,archive_sha256=sha(raw))


def native_size_weights(rules):
    # Rust deserializes sizing shares into f32. Python's sum changed in 3.12,
    # producing a binary64 ULP difference in a normalized share on some runners.
    return [dict(rule, sizes=[[size,struct.pack("!f",weight)] for size,weight in rule["sizes"]])
            if rule.get("sizes") is not None else rule for rule in rules]


def parse(base,evidence,manifest,run,flop,version,solver,pipeline,ranges,fresh,*,expected_turns=None,case_turn=None):
    m=read(manifest)
    assert (m["spot"],m["pot_family"],m["flop"],m["version"]) == ("UTG_CO","SRP",flop,version)
    assert m["schema"]=="NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1" and not m["failures"]
    assert (m["solver_pin"],m["solver_ranges_sha256"],m["pool_source_sha256"])==(PIPELINE,RANGES,POOL)
    assert (m["root_pot_bb"],m["root_remaining_bb"],m["flop_action_sizes"]) == (6.5,97.5,["33%","50%","75%","100%"])
    assert m["preflop_ranges"]["source"]=="PINNED_POKER_SOLVER_PREFLOP_CFR" and m["preflop_ranges"]["spot"]=="UTG_CO"
    pin_name,=evidence.glob("*poker-solver*.txt")
    rust_name,=evidence.glob("*rust*.txt")
    assert pin_name.read_text().strip()==PIN and rust_name.read_text().strip()==RUST
    rootpath=base/m["file_flop"]
    assert sha(rootpath.read_bytes())==m["file_flop_sha256"]
    root,root_job=read(rootpath),read(rootpath.with_suffix(".job.json"))
    assert (root["flop"],root["pot"],root["stack"])==(flop,650,9750)
    assert root_job["flop_oop"]==root_job["flop_ip"]=="33%,50%,75%,100%"
    assert [root_job["oop"],root_job["ip"]]==[ranges.to_str(w) for w in ranges.ranges("UTG_CO",version)]
    lock_coverage={}
    if fresh:
        assert (m["marginal_lock_matching"],m["flop_line_policy"],m["selected_turn_lines"])==(
            "RUST_FIRST_MATCH_POOLED_FALLBACK_EXACT_STREET","oop-b50only",["x x"])
        assert m["turns"]==(CANDIDATES[flop] if expected_turns is None else expected_turns) and m["turn_sizing_mode"]=="default"
        pool=read(solver/"inputs/pool_stats.json")["NL2"]
        rules,_=make_fallbacks("UTG_CO",version,pool,pipeline.lock_list,flop,by_street=True)
        assert native_size_weights(root_job.get("locks",[]))==native_size_weights(json.loads(encode(rules)))
        if version!="gto":lock_coverage["root"]=audit_patterns(root,root_job,m,pool,hero_seat=1)
    assert 0<=root["info"]["gto_expl_pct"]<=.5
    if version=="exp_ip":assert root_job["hero"]==1 and 0<=root["info"]["hero_gap_pct"]<=.5
    else:assert version=="gto" and root_job.get("hero") is None and not root_job.get("locks")
    out={}
    for c in m["cases"]:
        if c["line"]!="b50 c" or (case_turn is not None and case_turn!=c["turn"]):continue
        turn=c["turn"]
        path=base/c["source_path"]
        assert sha(path.read_bytes())==c["source_sha256"]
        sub,job=read(path),read(path.with_suffix(".job.json"))
        assert (sub["flop"],sub["turn"],sub["line0"],sub["pot"],sub["stack"])==(flop,turn,"b50 c",1300,9425)
        for game,line,seat,action,bets in [(root,"",0,"b50",[0,0]),(root,"b50",1,"c",[325,0]),(sub,"b50 c/",0,"x",[0,0])]:
            node,=[n for n in game["nodes"] if n["line"]==line and n["player"]==seat]
            assert node["bets"]==bets and action in node["acts"]
        parent,=[n for n in root["nodes"] if n["line"]=="b50 c/" and n["board"][-2:]==turn]
        for seat,k in enumerate(("oop_w","ip_w")):
            assert job[k]==[[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat]) if w>1e-4]
        assert job["turn_oop"]==job["turn_ip"]=="50%,100%" and job["root_no_bet"] is False
        assert (job["rake_rate"],job["rake_cap"],job.get("hero"))==(.05,1000,root_job.get("hero"))
        assert job.get("locks",[])==root_job.get("locks",[])
        assert (c["gto_gap_pct"],c["hero_gap_pct"])==(sub["info"]["gto_expl_pct"],sub["info"].get("hero_gap_pct"))
        assert 0<=c["gto_gap_pct"]<=.5 and (version=="gto" or 0<=c["hero_gap_pct"]<=.5)
        source=dict(run=run,version=version,manifest=m,root=root,subgame=sub,source_sha256=c["source_sha256"],
                    root_job=root_job,subgame_job=job)
        if fresh and version=="exp_ip":
            source["measured_lock_application"]=dict(lock_coverage,subgame=audit_patterns(sub,job,m,pool,hero_seat=1))
        out[turn]=source
    return out


def archived_fresh(directory, run):
    pins=read(Path("data/nl2_hu_b489_replay_sources.json"))
    assert len(pins)==4 and {pin["run"] for pin in pins.values()}=={run}
    for id,pin in pins.items():
        info=read(directory/f"{id}.json")
        assert (info["id"],info["name"],info["digest"],info["workflow_run"]["id"],info["workflow_run"]["head_sha"],
                info["workflow_run"]["repository_id"])==(int(id),pin["name"],"sha256:"+pin["sha256"],run,pin["commit"],1438346845)
        path=directory/f"{id}.zip"
        assert sha(path.read_bytes())==pin["sha256"]
        with zipfile.ZipFile(path) as raw:
            raw.extractall(directory/pin["name"])
    return pins


def other_archived_turns():
    results={}
    recorded=sorted(p for name in ("NL2_B473_R146_*","NL2_B476_UTG_*","NL2_B479_R146_*")
                    for p in EVIDENCE.glob(name+".json.gz"))
    assert len(recorded)==7
    for path in recorded:
        packed=json.loads(gzip.decompress(path.read_bytes()))
        source=(packed.get("source_arrays") or packed["sources"])[0]
        assert (packed["solver"],packed["rust"],source["version"])==(PIN,RUST,"gto")
        branch=source["branches"]["b50 c"] if "branches" in source else source
        root,sub=source["root"],branch["subgame"]
        assert sha(compact(root))==source["root_sha256"]
        assert sha(compact(sub))==branch["source_sha256"]
        node,=[n for n in sub["nodes"] if (n["line"],n["player"],len(n["board"]))==(LINE,1,8)]
        exact=proof(root,sub,node,game_reach(root,sub)[0])
        results[packed["flop"]]=dict(run=packed["run_id"],archive_sha256=sha(path.read_bytes()),
           root_sha256=source["root_sha256"],subgame_sha256=branch["source_sha256"],public_board=node["board"],
           strict_combos=exact["strict_legal_combos"],compatible_deals=exact["compatible_hole_card_pairs"])
    return results


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--originals",type=Path)
    p.add_argument("--fresh",type=Path)
    p.add_argument("--run-id",type=int)
    p.add_argument("--solver",type=Path)
    p.add_argument("--list-artifacts",action="store_true")
    p.add_argument("--write-prior",action="store_true")
    p.add_argument("--archived-fresh",action="store_true",help="Recheck the four completed B489 artifacts by ID, digest and run")
    args=p.parse_args()
    if args.list_artifacts:
        print(" ".join(PINS));return
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",str(solver),"rev-parse","HEAD"],text=True).strip()==PIN
    assert sha((solver/"inputs/pool_stats.json").read_bytes())==POOL
    sys.path.insert(0,str(solver/"postflop/py"))
    import pipeline
    import ranges
    ranges.SPOTS.update(EXTRA_SPOTS)
    model=read(FROZEN)["records"][MODEL]
    assert (model["frequency_rank"],model["family"],model["solver_profile"],model["assumed_model_node_spr"])==(79,"SRP","UTG_CO",7)
    original_rows, paired_sources, old_claims, refs, equilibrium = {}, {}, {}, {}, {}
    for art,a in PINS.items():
        file=args.originals/f"{art}.zip"; meta=read(args.originals/f"{art}.json")
        assert (meta["name"],meta["id"],meta["digest"],meta["workflow_run"]["id"],meta["workflow_run"]["head_sha"]) == (
            a["name"],int(art),"sha256:"+a["sha256"],a["run"],a["commit"])
        assert sha(file.read_bytes())==a["sha256"]
        folder=args.originals/art
        evidence=folder/"evidence"
        manifest,=evidence.glob("*.json")
        sources=parse(folder/"solver/postflop",evidence,manifest,a["run"],a["flop"],a["version"],solver,pipeline,ranges,False)
        for turn,source in sources.items():
            source.update(artifact_id=int(art),archive_code=f"GITHUB_ARTIFACT_{art}",archive_sha256=a["sha256"])
            row=audit_node(source)
            original_rows[art]=row
            if a["run"]==PAIR_RUN:
                old_claims.setdefault(a["flop"],{})[a["version"]]=row
            if a["flop"] in CANDIDATES and a["version"]=="gto":
                assert row["compatible_hole_card_pairs"]>0
                paired_sources[a["flop"],turn,"gto"]=source
    for b in model["certified_3_to_5_exact_flop_boards"]:
        if b["source_run_id"]!=PAIR_RUN:continue
        g=old_claims[b["flop"]]["gto"]
        assert (g["source_sha256"],g["public_board"],g["line"],g["acting_seat"])==(b["source_sha256"],b["public_board"],LINE,1)
        prefix=[MODEL,b["public_board"],LINE,1,PAIR_RUN]
        equilibrium[encode(prefix+[g["source_sha256"]]).decode()]=g
        for locked in b["nl2_locked_variants"]:
            e=old_claims[b["flop"]]["exp_ip"]
            assert (e["source_sha256"],e["version"],e["source_run_id"])==(locked["sha256"],locked["version"],locked["run_id"])
            refs[encode(prefix+[e["source_sha256"]]).decode()]=dict(e,gto=g)
    assert len(refs)==len(equilibrium)==2
    baseline=dict(schema="NL2_HU_B489_ORIGINAL_LOCKED_MEDIUM_V1",registry=FROZEN.name,registry_sha256=sha(FROZEN.read_bytes()),
                  poker_solver_pin=PIN,rust_engine_pin=RUST,pool_sha256=POOL,original_artifacts_sha256=sha(Path("data/nl2_hu_b489_originals.json").read_bytes()),
                  totals={"gto_zero":sum(not r["strict_legal_combos"] for r in equilibrium.values()),"lock_positive":sum(bool(r["strict_legal_combos"]) for r in refs.values())},
                  gto_references=equilibrium,references=refs)
    if args.write_prior:save(OLD,baseline)
    else:assert OLD.read_bytes()==encode(baseline)+b"\n"
    if args.fresh is None:return
    assert args.run_id
    used_pins=archived_fresh(args.fresh,args.run_id) if args.archived_fresh else None
    fresh_rows,missing,boards,pins={},{},[],[]
    for flop,turns in CANDIDATES.items():
        for ver in (("gto","exp_ip") if flop=="KsQh3d" else ("exp_ip",)):
            folder=args.fresh/f"NL2-B489-{flop}-{ver}"
            evidence=folder/"trainer/evidence"; manifest=evidence/f"{flop}-{ver}.json"
            if not manifest.is_file() or read(manifest)["failures"]:
                missing[flop+" "+ver]="MISSING_OR_FAILED_ORIGINAL";continue
            sources=parse(folder/"solver/postflop",evidence,manifest,args.run_id,flop,ver,solver,pipeline,ranges,True)
            if not sources:missing[flop+" "+ver]=read(manifest)["skipped"]
            for turn,source in sources.items():
                if used_pins:
                    artifact,=([int(id),pin] for id,pin in used_pins.items() if pin["name"]==folder.name)
                    source.update(artifact_id=artifact[0],github_artifact_sha256=artifact[1]["sha256"])
                pack(source,flop,turn)
                fresh_rows[flop+" "+turn+" "+ver]=audit_node(source)
                paired_sources[flop,turn,ver]=source
        for turn in turns:
            g,e=(paired_sources.get((flop,turn,v)) for v in ("gto","exp_ip"))
            if not g or not e:continue
            node=audit_node(g); nl2=audit_node(e)
            if not min(node["compatible_hole_card_pairs"],nl2["compatible_hole_card_pairs"]):continue
            public=node["public_board"];assert nl2["public_board"]==public
            b,pin=emit_board(model,g,e,public,LINE,"KQ_HIGH")
            assert b and pin
            boards.append(b);pins.append(pin);break
    assert len(boards)==len({b["flop"] for b in boards})
    group=dict(rank=79,model_id=MODEL,spot="UTG_CO",actor="CO_IP",line=LINE,boards=boards,pins=pins)
    if len(boards)>=3:
        d=EVIDENCE/"reverified";d.mkdir(exist_ok=True)
        save(d/"rank79.json",group)
    save(REPORT,dict(fresh_original_artifacts=used_pins,other_archived_turns=other_archived_turns(),originals=original_rows,fresh=fresh_rows,unavailable=missing,model=group))
    print("Rank 79 original paired named flops:",len(boards))


if __name__=="__main__":
    main()
