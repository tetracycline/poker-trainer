"""B879: isolate and archive original rank114 flop CFR from two B876 cancelled jobs.

Not a certification. Run at most one native original root per independent 29-minute
job; the original B876 workers were cancelled during native work with no result
JSON in their artifacts. Original GTO-only roots never count as NL2-locked boards.
"""
import argparse,json,subprocess,sys
from pathlib import Path
from hu_b463_rank45_gate import SOLVER,RUST
from hu_b467_river_source_gate import json_bytes,compact,sha
from hu_b483_locked_medium import PIPELINE,POOL,RANGES
from hu_b481_rank27_limp_rivers import check_limp_source
from hu_b637_rank57 import solve
from hu_b876_rank114_new_originals import CASES,preflight as b876_preflight
import hu_b858_rank114_midhigh as base

FROZEN=Path("data/solver_evidence/partial/b876_r114_cancelled_receipts.json")
RANK=114
MODEL="ln-iso-lmp_r_model-asilzt"
PREVIOUS_ORIGINAL_HEAD="3e10f29814ec2872ad95185beadbf759e3b85c16"

def prepare(a):
    assert sys.version_info[:2]==(3,11)
    assert subprocess.check_output(["git","-C",a.solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    if a.driver:
        assert a.driver.resolve()==(a.solver/"postflop/pfdriver/target/release/pfdriver").resolve()
        assert subprocess.check_output(["git","-C",a.solver/"postflop/postflop-solver","rev-parse","HEAD"],text=True).strip()==RUST
    for path,digest in (("postflop/py/pipeline.py",PIPELINE),("postflop/py/ranges.py",RANGES),("inputs/pool_stats.json",POOL)):
        assert sha((a.solver/path).read_bytes())==digest
    b876_preflight()
    cancelled=json.loads(FROZEN.read_bytes())
    assert (cancelled["run"]["head_sha"],cancelled["run"]["conclusion"])==(PREVIOUS_ORIGINAL_HEAD,"cancelled")
    assert {x["flop"] for x in cancelled["workers"]}==set(CASES)
    old,=[x for x in cancelled["workers"] if x["flop"]==a.flop]
    assert old["job"]["conclusion"]=="cancelled"
    assert old["artifact"]["size_in_bytes"]<1500
    assert all(s["conclusion"]!="success" for s in old["job"]["steps"] if s["name"]=="Solve the missing river trees and replay both policies")
    s=json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())
    p=json.loads(Path("data/nl2_hu_b838_234_approx_frequency_priority.json").read_bytes())
    assert (s["CERT_MULTIBOARD"],s["APPROX"],s["EST"],s["TOTAL"])==(158,234,0,392)
    row,=[row for row in p["rows"] if row["rank"]==RANK]
    assert row["model_id"]==MODEL and row["passes_min_0_2_pct_frequency"] and s["records"][MODEL]["label"]=="APPROX"
    assert p["current_certified_opportunity_share_pct"]==84.700987
    sys.path.insert(0,str(a.solver/"postflop/py"))
    import pipeline,ranges
    src,template,manifest=base.original(a.receipts,pipeline,ranges)
    route_raw=subprocess.check_output(["node","tools/hu_b733_rank114_routes.cjs"])
    view=json.loads(route_raw)
    assert view["id"]==MODEL and view["turn_pct"]==66
    oldcases=base.CASES
    try:
        base.CASES=CASES
        witnesses=base.preflight(template,a.flop,view["routes"])
    finally:
        base.CASES=oldcases
    valid=[t for t in CASES[a.flop] if witnesses[t]]
    assert valid,"No legitimate original two-seat witness before solver"
    # Freeze a smaller original-root research iteration budget, but never
    # silently treat it as B876's full 2400-iteration source. <=0.5% gate
    # must still be met independently before any downstream paired NL2 proof.
    job=dict(template,flop=a.flop,out="result.json",iters=1600,target_pct=.45,
             extract=[dict(prefix=[],street=True)]+
                     [dict(prefix=["x","x",t],street=False,raw=True) for t in valid])
    check_limp_source(dict(manifest=manifest,root_job=job,subgame_job=None))
    assert (job["pot"],job["stack"],job["rake_rate"],job["rake_cap"])==(250,9900,.05,1000)
    assert job.get("hero") is None and not job.get("locks")
    return job,manifest,src,witnesses,valid,route_raw,old

def run(a):
    job,manifest,src,witnesses,valid,route,old=prepare(a)
    if a.preflight:
        print(json.dumps(dict(flop=a.flop,valid_turns=valid,previous_cancelled_job=old["job"]["id"],new_original_roots=0,cert=0)))
        return
    if a.driver:
        assert not a.output.exists() or not any(a.output.iterdir())
    else:
        assert (a.output/"root/result.json").is_file()
    a.output.mkdir(parents=True,exist_ok=True)
    raw=solve(a.output/"root",job,a.driver)
    canonical={raw["flop"][i:i+2] for i in (0,2,4)}
    assert canonical=={a.flop[i:i+2] for i in (0,2,4)}
    assert (raw["pot"],raw["stack"])==(250,9900)
    assert not raw["info"].get("lock_stats")
    assert raw["info"]["gto_expl_pct"]>=0
    extracted={n["board"][-2:] for n in raw["nodes"] if n["line"]=="x x/" and len(n["board"])==8}
    assert set(valid)==extracted
    report=dict(schema="NL2_B879_R114_SEPARATE_ORIGINAL_FLOP_CHECKPOINT_V1",
        rank=RANK,model=MODEL,flop=a.flop,source_cancelled_run=cancelled_id(old),
        cancelled_native_step="cancelled",original_complete_from_prior_job=False,
        root_job_sha256=sha((a.output/"root/job.json").read_bytes()),
        root_result_sha256=sha((a.output/"root/result.json").read_bytes()),
        source_pinned_solver=SOLVER,rust_sha=RUST,pipeline_sha256=PIPELINE,ranges_sha256=RANGES,pool_sha256=POOL,
        source_template_original_sha256=src["identity"]["root_job_sha256"],
        source_template_preflop_scope="ASSUMED_EXPLICIT_169CLASS_LMP",
        iteration_budget=1600,baseline_cancelled_iterations=2400,flop_menu=job["flop_oop"],
        gto_gap_pct=raw["info"]["gto_expl_pct"],passes_independent_gto_gap_gate=raw["info"]["gto_expl_pct"]<=.5,
        original_turn_boundary_exports=sorted(extracted),positive_static_two_seat_turns=valid,
        private_hand_NL2_marginals_observed=False,
        exact_actor_locked_turn_subgames=0,certifications_granted=0,
        requires_new_native_turn_plus_real_NL2_hero_lock_and_independent_physical_reach=True,
        report_scope="Original rank114 GTO flop only; restricted iteration budget, not B876-equivalent downstream NL2 certification")
    (a.output/"proof.json").write_bytes(json_bytes(report))
    print(json.dumps({k:report[k] for k in ("flop","gto_gap_pct","passes_independent_gto_gap_gate","original_turn_boundary_exports","certifications_granted")}))
def cancelled_id(old):
    return 45721122214
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("solver","receipts","output"):
        p.add_argument("--"+key,type=Path,required=True)
    p.add_argument("--flop",choices=CASES,required=True)
    p.add_argument("--driver",type=Path)
    p.add_argument("--preflight",action="store_true")
    run(p.parse_args())
