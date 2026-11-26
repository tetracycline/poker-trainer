"""B887: after B886's audited geometry repair, replay original dual roots.
No native invocation, no promotions, no registry writes. A new sized continuation
is not authorized by an absent compact-index row: retain historical raw leads.
"""
import hashlib,json,subprocess,sys
from pathlib import Path

D=Path("data")
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(["git",*args],text=True)
def main(out,receipt):
    out.mkdir(parents=True,exist_ok=False)
    registry=D/"nl2_hu_multiboard_status_current.json"
    before=sha(registry)
    subprocess.run([sys.executable,"tools/hu_b881_utg_price_boundary.py",str(out/"boundary"),str(receipt)],check=True)
    boundary=load(out/"boundary/report.json")
    subprocess.run([sys.executable,"tools/hu_b874_tail_inventory.py",str(out/"current-index")],check=True)
    current=load(out/"current-index/report.json")
    assert current["registry_sha256"]==before
    assert boundary["weighted_model_opportunity_coverage_pct"]==current["weighted_model_opportunity_coverage_pct"]==84.700987
    indexed={x["rank"]:x for x in current["models"]}
    assert len(boundary["rows"])==4
    # The historical third flop was already negative at the earlier UTG check-call
    # boundary on all three extracted turns. Do not rerun it or extrapolate that
    # result to other roots, sizes or turns.
    oldpath=D/"nl2_hu_b538_utg_check_calls.json"
    old=load(oldpath)
    assert old["run"]==45119866932
    negatives=[x for x in old["attempts"] if x["flop"]=="6c6d3h"]
    assert {x["turn"] for x in negatives}=={"6s","5d","4s"}
    assert all(x["nodes"] and all(y["nl2_pairs"]==0 and y["status"]=="ZERO_JOINT_REACH" for y in x["nodes"].values()) for x in negatives)
    paths=git("ls-files","data/solver_evidence").splitlines()
    rows=[]
    for x in boundary["rows"]:
        assert x["price_gate_passed"],x["price_comparison"]
        assert x["original_run"]==45119866932 and x["certifications_granted"]==0
        leads=[p for p in paths if x["flop"].lower() in p.lower() and p.lower().endswith((".zip",".json.gz",".json"))]
        # Report references by filename and exact indexed entries separately. Neither
        # an empty filename search nor index absence establishes global uniqueness.
        hits=[s for s in indexed[x["rank"]]["sources"] if s["flop"]==x["flop"] and s["turn"]==x["turn"]]
        history=git("grep","-il","-e",x["flop"],"--",".github/workflows","tools","data/*inputs.json").splitlines()
        candidates=x["static_river_candidates"]
        rows.append(dict(rank=x["rank"],flop=x["flop"],turn=x["turn"],target_turn_size=x["target_turn_size"],
          root_sha256=x["root_sha256"],prior_subgame_sha256=x["prior_subgame_sha256"],archive_sha256=x["archive_sha256"],
          price_comparison=x["price_comparison"],common_prior_physical_pairs=x["common_prior_physical_pairs"],
          rendered_eligible_hero_combos=x["rendered_eligible_hero_combos"],candidate_rivers=candidates,
          original_menu_already_included_target=x["original_menu_already_included_target"],
          historical_raw_filename_leads=leads,historical_code_and_manifest_leads=history,
          current_exact_index_hits=hits,status=("NO_STATIC_WITNESS" if not candidates else
          "EXISTING_MENU_REVIEW_ONLY" if x["original_menu_already_included_target"] else "STATIC_POSITIVE_PENDING_RAW_JOB_DEDUP"),
          can_dispatch_native=False,certifications_granted=0))
    assert sha(registry)==before
    payload=dict(schema="NL2_B887_CORRECTED_UTG_BOUNDARY_DEDUP_PREFLIGHT_V1",
        registry_sha256=before,source_receipt_sha256=sha(receipt),historical_B538_report_sha256=sha(oldpath),
        current_index_sha256=sha(out/"current-index/report.json"),CERT=boundary["CERT"],APPROX=boundary["APPROX"],
        weighted_model_opportunity_coverage_pct=boundary["weighted_model_opportunity_coverage_pct"],
        rows=rows,third_flop_prior_negative_not_rerun=negatives,native_solves=0,CERT_promotions=0,
        scope="Same exact two-seat prior boundary after corrected price; river candidates are static only. Raw-job identity and complete same-actor post-turn GTO/NL2 reach remain required. No private-card empirical NL2 or half-pot claim.")
    (out/"report.json").write_text(json.dumps(payload,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps([dict(rank=r["rank"],flop=r["flop"],status=r["status"],candidates=len(r["candidate_rivers"]),raw_leads=len(r["historical_raw_filename_leads"])) for r in rows]))
if __name__=="__main__":main(Path(sys.argv[1]),Path(sys.argv[2]))
