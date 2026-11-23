"""Solve and replay river-only half-pot menus from original, printed prior-street strategies."""
import argparse
import base64
import gzip
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, sha
from hu_b483_locked_medium import POOL, proof
from hu_b561_river_boundary import one
from hu_sequential_cfr_reach import accepted, cardkey, game_reach, mask_at_node
from verify_hu_multiboard_100bb import strict_medium_evidence


DATA = Path("data")
ARCHIVE = DATA / "solver_evidence/NL2_B583_FROZEN_RIVERS.zip"
PINS = DATA / "nl2_hu_b583_frozen_river_inputs.json"
SAMPLE = {"n": 64272, "fold": 53.1, "call": 37.6, "raise": 9.3}
PATCH = Path("tools/hu_b561_river_root.patch")


def load_policy(pin, folder):
    digest=pin["source_sha256"]
    if "local_file" in pin:
        raw=(DATA/"solver_evidence"/pin["local_file"]).read_bytes()
        assert sha(raw)==pin["archive_sha256"]
        package=json.loads(gzip.decompress(raw))
        assert (package["solver"],package["rust"],package["pool_sha256"],package["run"])==(SOLVER,RUST,POOL,pin["run"])
        raw_turn=base64.b64decode(package["source_file_b64"],validate=True)
        raw_root=base64.b64decode(package["conditional_root_file_b64"],validate=True)
        assert sha(raw_root)==package["conditional_root_sha256"] and sha(raw_turn)==digest==package["source_sha256"]
        return json.loads(raw_root),json.loads(raw_turn),package["job"],sha(raw_root)
    archive=folder/f"{pin['archive_id']}.zip"
    assert sha(archive.read_bytes())==pin["archive_sha256"]
    receipt=json.loads(archive.with_suffix(".json").read_bytes())
    assert (receipt["id"],receipt["digest"],receipt["workflow_run"]["id"],receipt["workflow_run"]["repository_id"])==(
        pin["archive_id"],"sha256:"+pin["archive_sha256"],pin["run"],1438346845)
    with ZipFile(archive) as z:
        names=[f for f in z.namelist() if f.startswith(("evidence/","trainer/evidence/"))]
        assert {RUST,SOLVER}<={z.read(f).decode().strip() for f in names if f.endswith(".txt") and z.getinfo(f).file_size<200}
        mf,=(f for f in names if f.endswith(".json") and not f.endswith("pool_stats.json"))
        m=json.loads(z.read(mf))
        assert m["version"]==pin["version"] and not m["failures"]
        c,=(c for c in m["cases"] if c.get("source_sha256",c.get("sub_sha256"))==digest)
        if m["schema"]=="HU_MISSING_ACTION_HISTORY_CFR_V1":
            rp,rs,sp=c["flop_json"],c["flop_sha256"],c["sub_json"]
        else:
            assert m["schema"]=="NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1" and m["pool_source_sha256"]==POOL
            rp,rs,sp=m["file_flop"],m["file_flop_sha256"],c["source_path"]
        raw_root=z.read("solver/postflop/"+rp)
        raw_turn=z.read("solver/postflop/"+sp)
        assert sha(raw_root)==rs and sha(raw_turn)==digest
        return json.loads(raw_root),json.loads(raw_turn),json.loads(z.read("solver/postflop/"+sp[:-5]+".job.json")),rs


def boundary(spec, pin, directory):
    root,sub,job,root_sha=load_policy(pin,directory)
    board,line,actor=spec["public_board"],spec["line"],spec["seat"]
    flop_line,turn_line,river_prefix=line.split("/")
    assert river_prefix==("x" if actor else "") and job["line0"]==[*flop_line.split(),"/"]
    assert (job["rake_rate"],job["rake_cap"])==(.05,1000)
    if "local_file" in pin:
        sub.update(line0=flop_line,turn=board[6:8])
    assert sub["line0"]==flop_line and sub["turn"]==board[6:8]
    if pin["version"]=="gto":
        assert 0<=sub["info"]["gto_expl_pct"]<=.5
    else:
        assert job["hero"]==actor and 0<=sub["info"]["hero_gap_pct"]<=.5 and sub["info"]["lock_stats"]
    original=one(sub,board,line)
    assert original["player"]==actor and original["pot"]==round(100*spec["pot_bb"])
    assert sub["stack"]-max(original["bets"])==round(100*spec["stack_bb"])
    baseline=proof(root,sub,original,game_reach(root,sub)[0])
    assert baseline["strict_legal_combos"]>0 and baseline["b50"]["eligible"]==0
    weights=[dict(job[k]) for k in ("oop_w","ip_w")]
    valid=[set(map(cardkey,hands)) for hands in sub["hands"]]
    # The turn job already contains the flop action weights. Its last printed
    # strategy on each subsequent action supplies the conditional river ranges.
    for game,public,prefix,actions in ((root,board[:6],"",flop_line.split()),
            (sub,board[:8],flop_line+"/",turn_line.split()),
            (sub,board,flop_line+"/"+turn_line+"/",river_prefix.split())):
        for i,action in enumerate(actions):
            n=one(game,public,prefix+" ".join(actions[:i]))
            seat=n["player"]
            valid[seat]&=accepted(n,game["hands"],action)
            if game is sub:
                hands=sub["hands"][seat]
                offset=len(hands)*n["acts"].index(action)
                for j,h in enumerate(hands):
                    weights[seat][h]*=n["strat"][offset+j]
    for seat in (0,1):
        valid[seat]&={cardkey(h) for h,w in zip(sub["hands"][seat],original["w"][seat],strict=True) if w>1e-4}
    ranges=[[(h,w) for h,w in seat.items() if w>0 and board[-2:] not in cardkey(h)] for seat in weights]
    reply=line+(" b50" if actor else "b50")
    new_job=dict(flop=board[:6],turn=board[6:8],river=board[8:],pot=original["pot"],
            stack=round(100*spec["stack_bb"]),rake_rate=.05,rake_cap=1000,oop_w=ranges[0],ip_w=ranges[1],
            line0=[*flop_line.split(),"/",*turn_line.split(),"/"],flop_oop="",flop_ip="",flop_raise="",
            turn_oop="",turn_ip="",turn_raise="",river_oop="" if actor else "50%",
            river_ip="50%" if actor else "50%,100%,a",river_raise="a",iters=3000,target_pct=.1,
            extract=[dict(prefix=[],street=True,raw=True)],out="river.json")
    if pin["version"]!="gto":
        new_job.update(hero=actor,rank_pct=.1,locks=[dict(pat="^"+reply+"$",fold=SAMPLE["fold"]/100,
                                                         **{"raise":SAMPLE["raise"]/100})])
    return new_job,dict(root_sha=root_sha,parent_gto_phase_gap_pct=sub["info"]["gto_expl_pct"],
        parent_locked_hero_gap_pct=sub["info"].get("hero_gap_pct"),original=original,baseline=baseline,
        hands=sub["hands"],valid=valid,reply=reply)


def replay(spec, pin, job, source, raw_job, raw):
    assert json.loads(raw_job)==json.loads(compact(job))
    g=json.loads(raw)
    board,actor=spec["public_board"],spec["seat"]
    n=one(g,board,spec["line"])
    reply=one(g,board,source["reply"])
    assert n["acts"] in (["x","b50"],["x","b50","a"])
    assert (n["player"],n["pot"],n["bets"])==(actor,job["pot"],[0,0])
    bet=(n["pot"]+1)//2
    assert (reply["pot"],reply["bets"],reply["player"])==(n["pot"]+bet,[0,bet] if actor else [bet,0],1-actor)
    assert reply["acts"]==["f","c","a"]
    if actor:
        forced=one(g,board,spec["line"][:-1])
        assert forced["acts"]==["x"]
    valid=[]
    errors=[]
    for seat in (0,1):
        m=dict(zip(g["hands"][seat],n["w"][seat],strict=True))
        orig=source["original"]["w"][seat]
        diffs=[abs(m.get(h,0)-v) for h,v in zip(source["hands"][seat],orig,strict=True)]
        error=dict(max_abs=max(diffs),relative_sum=sum(diffs)/sum(orig))
        # The original exporter rounds each per-hand strategy. Do not apply
        # comparison evidence when its reconstructed range misses either gate.
        errors.append(error)
        valid.append(source["valid"][seat]&{cardkey(h) for h,w in m.items() if w>1e-4})
    if any(err["max_abs"]>=.005 or err["relative_sum"]>=.0001 for err in errors):
        return dict(status="UNRESOLVED_ROUNDED_BOUNDARY",original=pin,root_sha256=source["root_sha"],
                    input_sha256=sha(raw_job),output_sha256=sha(raw),range_errors=errors)
    mask=mask_at_node(n,g["hands"])
    counts=0;half=0;rows=[]
    for i,h in enumerate(g["hands"][actor]):
        cards=cardkey(h)
        pairs=sum(set(cards).isdisjoint(v) for v in valid[1-actor]) if cards in valid[actor] else 0
        if not pairs:
            mask[i]=0
            continue
        assert mask[i]>0
        counts+=pairs
        if mask[i]&2:half+=pairs
        rows.append(dict(hand=h,b50=n["strat"][len(mask)+i],accepted_mask=mask[i],compatible_pairs=pairs))
    baseline=source["baseline"]
    assert (len(rows),counts)==(baseline["strict_legal_combos"],baseline["compatible_hole_card_pairs"])
    medium=strict_medium_evidence(n,g,base64.b64encode(mask).decode())
    assert medium["eligible"]==sum(bool(r["accepted_mask"]&2) for r in rows) and bool(half)==bool(medium["eligible"])
    info=g["info"]
    assert 0<=info["gto_expl_pct"]<=.1
    result=dict(status="VERIFIED",original=pin,root_sha256=source["root_sha"],input_sha256=sha(raw_job),output_sha256=sha(raw),
        parent_gto_phase_gap_pct=source["parent_gto_phase_gap_pct"],
        parent_locked_hero_gap_pct=source["parent_locked_hero_gap_pct"],gto_gap_pct=info["gto_expl_pct"],actions=n["acts"],original_actions=baseline["source_actions"],original_b50=baseline["b50"],
        range_errors=errors,legal_combos=len(rows),compatible_pairs=counts,half_pot_pairs=half,b50=medium,hands=rows)
    if pin["version"]!="gto":
        pattern=job["locks"][0]["pat"]
        assert set(info["lock_stats"])=={pattern} and 0<=info["hero_gap_pct"]<=.1
        rate=info["lock_stats"][pattern]
        assert rate["nodes"]==1 and abs(rate["fold"]-.531)<1e-5 and abs(rate["agg"]-.093)<1e-5
        result.update(locked_hero_gap_pct=info["hero_gap_pct"],applied_reply=rate)
    else:
        assert not info.get("lock_stats")
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--solver",type=Path,required=True)
    p.add_argument("--originals",type=Path,required=True)
    p.add_argument("--driver",type=Path)
    p.add_argument("--outputs",type=Path)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    assert not args.driver or args.outputs
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    pool=(solver/"inputs/pool_stats.json").read_bytes()
    assert sha(pool)==POOL and json.loads(pool)["NL2"]["HU_facing_bet"]["3"]["by_size"]["34-55%"]==SAMPLE
    registry=json.loads((DATA/"nl2_hu_multiboard_status_current.json").read_bytes())["records"]
    records=[]
    for spec in json.loads(PINS.read_bytes()):
        model=registry[spec["model_id"]]
        assert model["label"]=="CERT-MULTIBOARD" and model["frequency_rank"]==spec["rank"]
        board,=(b for b in model["certified_3_to_5_exact_flop_boards"] if b["public_board"]==spec["public_board"])
        assert (board["actual_exact_action_line"],board["acting_seat"],board["actual_pot_bb"],board["actual_effective_stack_bb"])==(
            spec["line"],spec["seat"],spec["pot_bb"],spec["stack_bb"])
        ids={("gto",board["source_run_id"],board["source_sha256"])}
        ids.update((l["version"],l["run_id"],l["sha256"]) for l in board["nl2_locked_variants"])
        policies=[]
        for pin in spec["sources"]:
            assert (pin["version"],pin["run"],pin["source_sha256"]) in ids
            stem=f"r{spec['rank']}_{pin['source_sha256'][:12]}"
            job,src=boundary(spec,pin,args.originals)
            if args.driver:
                folder=args.outputs/stem
                folder.mkdir(parents=True,exist_ok=True)
                raw_job=compact(job)
                (folder/"river.job.json").write_bytes(raw_job)
                subprocess.run([args.driver.resolve(),"river.job.json"],cwd=folder,check=True)
                raw=(folder/"river.json").read_bytes()
            else:
                with ZipFile(ARCHIVE) as z:
                    raw_job=z.read(stem+"/river.job.json")
                    raw=z.read(stem+"/river.json")
            policies.append(replay(spec,pin,job,src,raw_job,raw))
        records.append(dict({k:v for k,v in spec.items() if k!="sources"},policies=policies))
    args.out.write_text(json.dumps(dict(schema="NL2_HU_B583_ORIGINAL_POLICY_FROZEN_RIVERS_V1",
        solver=SOLVER,rust=RUST,driver_patch_sha256=sha(PATCH.read_bytes()),pool_sha256=POOL,
        response_source="NL2.HU_facing_bet[3].by_size[34-55%]",response=SAMPLE,records=records),
        sort_keys=True,indent=2)+"\n")


if __name__=="__main__":
    main()
