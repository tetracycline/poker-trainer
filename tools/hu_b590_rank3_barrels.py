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

MODEL = "ln-opfr-t_model-1wej9w5"
CASES = {
    "4dThAsTd": (14529096110, "fc8e17ff2ba07578928a6467a4e7b73721cf05c5747b44b9d440a2b51d1cc39f"),
    "6s9dJh3c": (14628394918, "2e95b5b63a796934ed2d4e20c73a785d0d14b48b180c9baca47252127171b7b5"),
    "2d7hKs9d": (14593610543, "28f37cefb8d6adb25ed64f2b7d20098d4215fda32054f6a88b672aad0dc627b7"),
}


def reply_rules(pool, flop_line):
    rows = []
    table = pool["postflop_HU"]["SRP_PFR_OOP"]
    for street, prefix in (("turn", "^"+flop_line+"/"), ("river", "^"+flop_line+"/b(50|100) c/")):
        field = "vs_" + street + "_barrel_by_size"
        for action, interval in (("b50", "34-55%"), ("b100", "81-110%")):
            measure = table[field][interval]
            assert measure["n"] > 1000 and abs(sum(measure[k] for k in ("fold","call","raise"))-100) < .15
            rows.append(dict(pattern=prefix+action+"$", table=field, size=interval, **measure))
    return rows


def calculate(board, pin, originals, pool, archive, driver, verification_driver, pipeline, ranges, model, flop_line):
    public = board["public_board"]
    line = flop_line+"/"
    aid=pin["archive_id"]
    receipt=json.loads((originals/f"{aid}.json").read_bytes())
    parent_pin=dict(name=receipt["name"],head=receipt["workflow_run"]["head_sha"],run=pin["run"],sha256=pin["archive_sha256"])
    parent=load_original(originals,aid,parent_pin,"SB_BB",board["flop"],board["turn"],"gto",pot=600,stack=9700,
                         pipeline=pipeline,ranges=ranges,flop_line=flop_line)
    assert parent["identity"]["source_sha256"]==pin["source_sha256"]
    root,original=parent["source"]["root"],parent["source"]["subgame"]
    parent_job,root_sha=parent["job"],parent["identity"]["root_sha256"]
    assert (original["line0"], original["turn"], board["actual_exact_action_line"], board["acting_seat"]) == (flop_line, public[-2:], line, 0)
    investment={"b100 c":600, "b75 c":450, "b50 c":300}[flop_line]
    assert (root["pot"], root["stack"], parent_job["pot"], parent_job["stack"]) == (600, 9700, 600+2*investment, 9700-investment)
    assert (parent_job["rake_rate"], parent_job["rake_cap"], parent_job["line0"]) == (.05, 1000, [*flop_line.split(), "/"])
    assert not parent_job.get("locks") and parent_job.get("hero") is None and not original["info"].get("lock_stats")
    assert (original["pot"]/100, original["stack"]/100) == (board["actual_pot_bb"], board["actual_effective_stack_bb"])
    rules = reply_rules(pool, flop_line)
    job = dict(parent_job, hero=0, iters=2500, target_pct=.35, rank_pct=.35, out="result.json",
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
        node, = (n for n in game["nodes"] if (n["board"],n["line"],n["player"])==(public,line,0))
        assert node["acts"] == ["x","b50","b100"]
        masks=game_reach(root,game)[0]
        row=proof(root,game,node,masks)
        legal=base64.b64decode(row["compatible_action_mask_b64"],validate=True)
        hands={h:round(node["strat"][len(legal)+i],6) for i,(h,m) in enumerate(zip(game["hands"][0],legal,strict=True)) if m & 2}
        assert len(hands)==row["b50"]["eligible"] and row["compatible_hole_card_pairs"]>=row["strict_legal_combos"]>0
        return dict(legal_combos=row["strict_legal_combos"],compatible_pairs=row["compatible_hole_card_pairs"],
                    actions=node["acts"],half_pot=row["b50"],eligible_hand_frequencies=hands)

    before, after = decision(original), decision(locked)
    assert before["legal_combos"]==after["legal_combos"] and before["compatible_pairs"]==after["compatible_pairs"]
    assert before["half_pot"]["eligible"]==board["medium_50pct_eligible_combos"]
    assert before["half_pot"]["candidate"]==board["b50_nonpolarized_relative_equity_research_candidate"]
    return dict(rank=model["frequency_rank"],model_id=model["model_id"],public_board=public,line=line,seat=0,pot_bb=original["pot"]/100,stack_bb=original["stack"]/100,
                original=pin,root_sha256=root_sha,job_sha256=sha(compact(job)),output_sha256=sha(payload),
                gto=before,locked=after,gto_gap_pct=locked["info"]["gto_expl_pct"],hero_gap_pct=locked["info"]["hero_gap_pct"],rules=rules)


def main(*, model_id=MODEL, rank=3, flop_line="b75 c", cases=CASES):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--solver",type=Path,required=True)
    p.add_argument("--originals",type=Path,required=True)
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    drivers=p.add_mutually_exclusive_group()
    drivers.add_argument("--driver",type=Path,help="Generate the frozen native outputs")
    drivers.add_argument("--verification-driver",type=Path,help="Independently solve all jobs and compare both players’ native arrays")
    a=p.parse_args()
    assert subprocess.check_output(["git","-C",a.solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    sys.path.insert(0,str((a.solver/"postflop/py").resolve()))
    import pipeline
    import ranges
    pool_raw=(a.solver/"inputs/pool_stats.json").read_bytes()
    assert sha(pool_raw)==POOL
    model=json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())["records"][model_id]
    assert (model["frequency_rank"],model["label"])==(rank,"CERT-MULTIBOARD")
    records=[]
    boards={b["public_board"]:b for b in model["certified_3_to_5_exact_flop_boards"]}
    with ZipFile(a.archive,"w" if a.driver else "r",compression=ZIP_DEFLATED) as archive:
        for public,(aid,digest) in cases.items():
            b=boards[public]
            pin=dict(archive_id=aid,archive_sha256=digest,version="gto",run=b["source_run_id"],source_sha256=b["source_sha256"])
            records.append(calculate(b,pin,a.originals,json.loads(pool_raw)["NL2"],archive,a.driver,a.verification_driver,pipeline,ranges,model,flop_line))
    report=dict(schema="NL2_HU_B590_SB_BB_BARREL_REPLIES_V1",solver=SOLVER,rust=RUST,pool_sha256=POOL,
                archive_sha256=sha(a.archive.read_bytes()),records=records)
    a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")


if __name__=="__main__":
    main()
