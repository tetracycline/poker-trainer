"""Compare SB's original turn strategy with measured BB replies to double and triple barrels."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import compact, sha
from hu_b483_locked_medium import POOL, proof
from hu_checked_gto_boundary import load_original
from hu_sequential_cfr_reach import game_reach
from solve_hu_missing_branches import EXTRA_SPOTS
from solve_hu_assumed_pots import RULES as ASSUMED_PROFILES

MODEL = "ln-opfr-t_model-1wej9w5"
CASES = {
    "4dThAsTd": (14529096110, "fc8e17ff2ba07578928a6467a4e7b73721cf05c5747b44b9d440a2b51d1cc39f"),
    "6s9dJh3c": (14628394918, "2e95b5b63a796934ed2d4e20c73a785d0d14b48b180c9baca47252127171b7b5"),
    "2d7hKs9d": (14593610543, "28f37cefb8d6adb25ed64f2b7d20098d4215fda32054f6a88b672aad0dc627b7"),
}


def reply_rules(pool, flop_line, pfr, family, actions, seat):
    rows = []
    if family == "LMP":
        assert flop_line in ("b50 c", "x x") and actions == ["x", "b50", "b100"]
        rate = pool["HU_facing_bet"]["2"]["by_pot"]["limped"]
        assert rate["n"] == 63420
        return [dict(pattern="^"+flop_line+"/b(50|100)$", table="HU_facing_bet[2].by_pot[limped]",
                     size="all", **rate)]
    table = pool["postflop_HU"][family + "_PFR_" + pfr.upper()]
    if seat and flop_line == "x x" and family=="3BP":
        if pfr=="oop":
            assert actions==["x","b50","b100"]
            obs=pool["HU_facing_bet"]["2"]["by_pot"]["3BP"]
            assert obs["n"]==53669
            return [dict(pattern="^x x/x b(50|100)$",table="HU_facing_bet[2].by_pot[3BP]",size="all",**obs)]
        assert pfr=="ip" and actions==["x","b33","b50","b75"]
        obs=table["vs_delayed_cbet"]
        assert obs["n"]==3776
        return [dict(pattern="^x x/x b(33|50|75)$",table="vs_delayed_cbet",size="all",**obs)]
    if seat and flop_line == "x x":
        assert family == "SRP" and pfr == "ip" and actions == ["x","b50","b100"]
        rate = table["vs_delayed_cbet"]
        assert rate["n"] == 32036
        return [dict(pattern="^x x/x b(50|100)$",table="vs_delayed_cbet",size="all",**rate)]
    if flop_line.startswith("x b"):
        assert family == "SRP" and pfr == "ip" and actions == ["x","b50","b100"]
        for action, interval, count in (("b50","34-55%",15700),("b100","81-110%",4480)):
            rate = table["vs_turn_barrel_by_size"][interval]
            assert rate["n"] == count
            rows.append(dict(pattern="^"+flop_line+"/x "+action+"$", table="vs_turn_barrel_by_size", size=interval, **rate))
        return rows
    if family == "3BP" and flop_line != "x x":
        assert pfr == "oop" and flop_line == "b75 c"
        assert actions in (["x","b50","a"], ["x","b50","b100","a"])
        for action, interval, count in (("b50","34-55%",3647), ("b100","81-110%",1175)):
            if action in actions:
                rate = table["vs_turn_barrel_by_size"][interval]
                assert rate["n"] == count
                rows.append(dict(pattern="^b75 c/"+action+"$", table="vs_turn_barrel_by_size", size=interval, **rate))
        return rows
    if flop_line=="x x":
        metric = "vs_probe" if pfr == "ip" else "vs_delayed_cbet"
        rate = table[metric]
        counts = {("SRP","ip"):49952, ("SRP","oop"):26780, ("3BP","oop"):6843, ("3BP","ip"):6093}
        assert rate["n"] == counts[family,pfr]
        return [dict(pattern="^x x/b(50|100)$",table=metric,size="all",**rate)]
    assert pfr == "oop"
    for street, prefix in (("turn", "^"+flop_line+"/"), ("river", "^"+flop_line+"/b(50|100) c/")):
        field = "vs_" + street + "_barrel_by_size"
        for action, interval in (("b50", "34-55%"), ("b100", "81-110%")):
            measure = table[field][interval]
            assert measure["n"] > 1000 and abs(sum(measure[k] for k in ("fold","call","raise"))-100) < .15
            rows.append(dict(pattern=prefix+action+"$", table=field, size=interval, **measure))
    return rows


def calculate(board, pin, originals, pool, archive, driver, verification_driver, pipeline, ranges, model, flop_line, repo_parent=None):
    public = board["public_board"]
    seat = board["acting_seat"]
    assert seat in (0, 1)
    turn_root = flop_line+"/"
    line = turn_root+("x" if seat else "")
    spot = model["solver_profile"]
    profile = ASSUMED_PROFILES[spot] if spot == "LMP_CO_BB" else ranges.SPOTS[spot]
    assert profile["kind"] in ("SRP", "3BP", "LMP") and profile["pfr"] in ("ip", "oop")
    pot, stack = round(100*profile["pot"]), round(100*profile["stack"])
    if repo_parent:
        parent=repo_parent(board,pin,ranges)
    else:
        aid=pin["archive_id"]
        receipt=json.loads((originals/f"{aid}.json").read_bytes())
        parent_pin=dict(name=receipt["name"],head=receipt["workflow_run"]["head_sha"],run=pin["run"],sha256=pin["archive_sha256"])
        parent=load_original(originals,aid,parent_pin,spot,board["flop"],board["turn"],"gto",pot=pot,stack=stack,
                             pipeline=pipeline,ranges=ranges,flop_line=flop_line)
    assert parent["identity"]["source_sha256"]==pin["source_sha256"]
    root,original=parent["source"]["root"],parent["source"]["subgame"]
    parent_job,root_sha=parent["job"],parent["identity"]["root_sha256"]
    assert (original["line0"], original["turn"], board["actual_exact_action_line"], board["acting_seat"]) == (flop_line, public[-2:], line, seat)
    bet_pct = 0 if flop_line=="x x" else int(next(token[1:] for token in flop_line.split() if token.startswith("b")))
    if seat and flop_line != "x x":
        assert parent_job["root_no_bet"] and model["solver_profile"] in ("BTN_BB","CO_BB")
        forced, = (n for n in original["nodes"] if (n["board"],n["line"],n["player"])==(public,turn_root,0))
        assert forced["acts"]==["x"]
    investment = (pot * bet_pct + 50) // 100
    assert (root["pot"], root["stack"], parent_job["pot"], parent_job["stack"]) == (pot, stack, pot+2*investment, stack-investment)
    assert (parent_job["rake_rate"], parent_job["rake_cap"], parent_job["line0"]) == (.05, 1000, [*flop_line.split(), "/"])
    assert not parent_job.get("locks") and parent_job.get("hero") is None and not original["info"].get("lock_stats")
    assert (original["pot"]/100, original["stack"]/100) == (board["actual_pot_bb"], board["actual_effective_stack_bb"])
    root_node, = (n for n in original["nodes"] if (n["board"],n["line"],n["player"]) == (public,line,seat))
    actions = root_node["acts"]
    assert actions == board["exact_node_actions"]
    rules = reply_rules(pool, flop_line, profile["pfr"], profile["kind"], actions, seat)
    job = dict(parent_job, hero=seat, iters=2500, target_pct=.35, rank_pct=.35, out="result.json",
               locks=[dict(pat=r["pattern"], fold=r["fold"]/100, **{"raise":r["raise"]/100}) for r in rules])
    key = public+"/result.json"
    if driver or verification_driver:
        with TemporaryDirectory() as tmp:
            Path(tmp,"job.json").write_bytes(compact(job))
            subprocess.run([(driver or verification_driver).resolve(), "job.json"], cwd=tmp, check=True)
            fresh = Path(tmp,"result.json").read_bytes()
        if driver:
            archive.writestr(key,fresh)
    payload = fresh if driver else archive.read(key)
    locked = json.loads(payload)
    if verification_driver:
        rebuilt = json.loads(fresh)
        assert all(rebuilt[k] == locked[k] for k in ("nodes","hands","pot","stack","flop"))
        for k in ("lock_stats","gto_expl_pct","hero_gap_pct"):
            assert rebuilt["info"][k] == locked["info"][k]
    assert all(locked[k]==original[k] for k in ("pot","stack","flop","hands"))
    locked.update(line0=original["line0"],turn=original["turn"],rivers=original["rivers"])
    assert 0<=locked["info"]["gto_expl_pct"]<=.35 and 0<=locked["info"]["hero_gap_pct"]<=.35
    stats = locked["info"]["lock_stats"]
    assert set(stats)=={r["pattern"] for r in rules}
    for r in rules:
        stat = stats[r["pattern"]]
        assert stat["nodes"] >= 1
        assert abs(stat["fold"]-r["fold"]/100)<.001 and abs(stat["agg"]-r["raise"]/100)<.001
        r["applied_nodes"] = stat["nodes"]
        r["applied_fold"] = stat["fold"]
        r["applied_raise"] = stat["agg"]

    def decision(game):
        node, = (n for n in game["nodes"] if (n["board"],n["line"],n["player"])==(public,line,seat))
        assert node["acts"] == actions and (profile["kind"] == "3BP" or actions == ["x","b50","b100"])
        masks=game_reach(root,game)[0]
        row=proof(root,game,node,masks)
        legal=base64.b64decode(row["compatible_action_mask_b64"],validate=True)
        medium_index=actions.index("b50")
        hands={h:round(node["strat"][medium_index*len(legal)+i],6)
               for i,(h,m) in enumerate(zip(game["hands"][seat],legal,strict=True)) if m & (1<<medium_index)}
        assert len(hands)==row["b50"]["eligible"] and row["compatible_hole_card_pairs"]>=row["strict_legal_combos"]>0
        return dict(legal_combos=row["strict_legal_combos"],compatible_pairs=row["compatible_hole_card_pairs"],
                    actions=node["acts"],half_pot=row["b50"],eligible_hand_frequencies=hands)

    before, after = decision(original), decision(locked)
    if seat == 1 and flop_line == "x x":
        assert parent_job["root_no_bet"] is False
        for game in (original, locked):
            opener, = (n for n in game["nodes"] if (n["board"],n["line"],n["player"])==(public,turn_root,0))
            assert opener["acts"][0]=="x" and len(opener["acts"])>1
    else:
        assert before["legal_combos"]==after["legal_combos"] and before["compatible_pairs"]==after["compatible_pairs"]
    assert before["half_pot"]["eligible"]==board["medium_50pct_eligible_combos"]
    assert before["half_pot"]["candidate"]==board["b50_nonpolarized_relative_equity_research_candidate"]
    return dict(rank=model["frequency_rank"],model_id=model["model_id"],public_board=public,line=line,seat=seat,pot_bb=original["pot"]/100,stack_bb=original["stack"]/100,
                original=pin,root_sha256=root_sha,job_sha256=sha(compact(job)),output_sha256=sha(payload),
                gto=before,locked=after,gto_gap_pct=locked["info"]["gto_expl_pct"],hero_gap_pct=locked["info"]["hero_gap_pct"],rules=rules)


def main(*, model_id=MODEL, rank=3, flop_line="b75 c", cases=CASES, argv=None, schema="NL2_HU_B590_SB_BB_BARREL_REPLIES_V1", repo_parent=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--solver",type=Path,required=True)
    p.add_argument("--originals",type=Path,required=True)
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    drivers=p.add_mutually_exclusive_group()
    drivers.add_argument("--driver",type=Path,help="Generate the frozen native outputs")
    drivers.add_argument("--verification-driver",type=Path,help="Independently solve all jobs and compare both players’ native arrays")
    a=p.parse_args(argv)
    assert subprocess.check_output(["git","-C",a.solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    sys.path.insert(0,str((a.solver/"postflop/py").resolve()))
    import pipeline
    import ranges
    ranges.SPOTS.update(EXTRA_SPOTS)
    pool_raw=(a.solver/"inputs/pool_stats.json").read_bytes()
    assert sha(pool_raw)==POOL
    model=json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())["records"][model_id]
    assert (model["frequency_rank"],model["label"])==(rank,"CERT-MULTIBOARD")
    records=[]
    boards={b["public_board"]:b for b in model["certified_3_to_5_exact_flop_boards"]}
    with ZipFile(a.archive,"w" if a.driver else "r",compression=ZIP_DEFLATED) as archive:
        for public,(aid,digest) in cases.items():
            b=boards[public]
            pin=dict(archive_sha256=digest,version="gto",run=b["source_run_id"],source_sha256=b["source_sha256"])
            pin["archive_code" if repo_parent else "archive_id"]=aid
            records.append(calculate(b,pin,a.originals,json.loads(pool_raw)["NL2"],archive,a.driver,a.verification_driver,pipeline,ranges,model,flop_line,repo_parent))
    report=dict(schema=schema,solver=SOLVER,rust=RUST,pool_sha256=POOL,
                archive_sha256=sha(a.archive.read_bytes()),records=records)
    a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")


if __name__=="__main__":
    main()
