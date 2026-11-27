"""B904: receipt-pinned, non-native screening of untested turns of six saved CO/BB roots."""
import argparse, json, os, subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from hu_b886_detached_price_candidate import api, git, sha, REPO, BRANCH
from hu_b895_archive_r158 import coverage
from hu_b710_publish import unpack_original
from hu_sequential_cfr_reach import accepted
import hu_b711_bb_lead_rivers as native
import hu_b766_rank75_chance_turns as chance

PARENT="9d925120a69a84ffd0bf78561cd407dd2f0e7917"
PINS={
 "9d7h4c":("B711","d4f480e69e5c4b83c683f86dd0d051d9a2b5fde44be4d874ab505841e953fbe9"),
 "8s6d2c":("B711","670f9d12a6e33b5df46b1475506b18a9c3946b9fdcbb461da0542f5ea6c30644"),
 "7c5d3h":("B711","51938d92c6f97346e824df1a9f0b896a8c682620f1e8d72ae36565f70f37be45"),
 "7h6h2c":("B844","790ef957e607ee6b5e78a770a58a1d98b4b15e5ce7d9a7acd918565be601b129"),
 "8h7h3c":("B844","026c6b4de189a1c29c56d3edc8a51bd6121850c8c62991af4cb41a55b33aeb34"),
 "9h8h2c":("B844","8cde6b16e3532fceeff9b2a74f18d3e7970cb9ac69562db0216f63401911f3c4"),
}
def read(p): return json.loads(Path(p).read_bytes())
def guard():
    h=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==h and git("rev-parse","HEAD^")==PARENT
    p=api("/pulls/2")
    assert p["state"]=="open" and p["draft"] and not p["merged"]
    assert (p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==(REPO,BRANCH,h)
    return coverage()
def screen(flop,out):
    cov=guard()
    batch,digest=PINS[flop]
    ev=Path("data/solver_evidence")
    archive=ev/("NL2_"+batch+"_CO_BB_"+flop.upper()+".zip")
    raw=archive.read_bytes();assert sha(raw)==digest
    if batch=="B711":
        rec,=[r for r in read("data/nl2_hu_b715_results.json") if r["flop"]==flop]
        assert rec["bytes_replayed"] and rec["source_run"]==45324358830
        assert rec["archive_sha256"]==digest and rec["archive"]==archive.name
    else:
        rec,=[r for r in read(ev/"partial/b845_b844_original_observations.json")["observations"] if r["flop"]==flop]
        assert rec["archive_sha256"]==digest and rec["archive"]==archive.name
        receipt=read("data/nl2_hu_b845_source_receipts.json")
        assert receipt["run"]["id"]==45535807925 and receipt["run"]["conclusion"]=="success"
        a,=[a for a in receipt["artifacts"] if a["id"]==rec["artifact"]]
        assert a["digest"]=="sha256:"+digest
        j,=[j for j in receipt["jobs"] if j["id"]==rec["job"]]
        assert j["status"]=="completed" and j["conclusion"]=="success"
    with TemporaryDirectory(prefix="b904-") as td:
        d=Path(td);names=unpack_original(raw,d)
        p=read(d/"proof.json")
        assert (p["flop"],p["spot"],p["actor"],p["flop_line"])==(flop,"CO_BB",0,"x b50 c")
        assert p["positive_distinct_flops_by_rank"]=={"92":0,"93":0,"94":0}
        assert p["actor_locked_turn_subgames"]==0
        assert set(p["native_file_sha256"])==names-{"proof.json"}
        assert all(sha((d/n).read_bytes())==v for n,v in p["native_file_sha256"].items())
        if batch=="B711":
            assert sha((d/"proof.json").read_bytes())==rec["proof_sha256"]
            assert p["root_source_sha256"]==rec["root_source_sha256"] and p["root_job_sha256"]==rec["root_job_sha256"]
        else:
            assert p==rec["proof"]
        root=read(d/"flop/result.json");job=read(d/"flop/job.json")
        assert sha((d/"flop/result.json").read_bytes())==p["root_source_sha256"]
        assert sha((d/"flop/job.json").read_bytes())==p["root_job_sha256"]
        assert (root["flop"],root["pot"],root["stack"],job["pot"],job["stack"])==(flop,550,9750,550,9750)
        assert job["flop_oop"]==job["flop_ip"]==native.ROOT_MENU and not job.get("locks")
        assert 0<=root["info"]["gto_expl_pct"]<=.5 and not root["info"].get("lock_stats")
        routes_raw=subprocess.check_output(["node","tools/hu_b711_bb_lead_routes.cjs"])
        assert routes_raw==(d/"rendered-routes.json").read_bytes(),"Rendered route changed: no silent reinterpretation"
        routes=json.loads(routes_raw)
        old=[r["turn"] for r in p["turns"]]
        assert len(old)==3 and len(set(old))==3
        observed={n["board"][-2:]:n for n in root["nodes"] if n["line"]=="x b50 c/"}
        assert set(observed)==set(old)
        for rec0 in p["turns"]:
            assert native.gate(root,rec0["turn"],routes)==(rec0["root_gate"],rec0["river_extracts_by_rank"])
        opening,=[n for n in root["nodes"] if n["line"]==""]
        ip,=[n for n in root["nodes"] if n["line"]=="x"]
        call,=[n for n in root["nodes"] if n["line"]=="x b50"]
        assert (opening["player"],ip["player"],call["player"])==(0,1,0)
        hero=accepted(opening,root["hands"],"x")&accepted(call,root["hands"],"c")
        villain=accepted(ip,root["hands"],"b50")
        new=[t for t in native.DECK if t not in native.cards(flop) and t not in old]
        assert len(new)==46
        result=dict(flop=flop,batch=batch,archive_sha256=digest,root_job_sha256=p["root_job_sha256"],root_source_sha256=p["root_source_sha256"],
                    strict_bb_check_call=len(hero),strict_co_halfpot=len(villain),prior_turns=old,untested_in_this_archive=new,
                    coverage=cov,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,leads=[],heldout=[],rows=[])
        if not hero or not villain:
            result["stage"]="NO_STRICT_ROOT_ACTION_ANY_TURN"
        else:
            masks={t:chance.blocked(root["hands"],t) for t in old+new}
            # Every value reconstructable without the held-out turn must agree bitwise.
            # Two blockers may cover both remaining observations; explicitly count those
            # missing values rather than pretending complete independent job replay.
            for t in old:
                checked=missing=0
                for s,hands in enumerate(root["hands"]):
                    for i in range(len(hands)):
                        actual=observed[t]["wr"][s][i]
                        if i in masks[t][s]:
                            assert chance.weight_bytes([actual])==chance.weight_bytes([0.0]);checked+=1;continue
                        values=[observed[a]["wr"][s][i] for a in old if a!=t and i not in masks[a][s]]
                        if not values:missing+=1;continue
                        assert all(chance.weight_bytes([v])==chance.weight_bytes([actual]) for v in values)
                        checked+=1
                result["heldout"].append(dict(turn=t,bitwise_checked=checked,unobservable_without_heldout=missing))
                # All three original observations together must fully reconstruct.
                w=chance.reconstruct(root,observed,masks,old,t)
                assert all(chance.weight_bytes(a)==chance.weight_bytes(b) for a,b in zip(w,observed[t]["wr"],strict=True))
            for t in new:
                w=chance.reconstruct(root,observed,masks,old,t)
                template=observed[old[0]]
                n=dict(template,board=template["board"][:6]+t,wr=w)
                synthetic=dict(root,nodes=[x for x in root["nodes"] if x["line"]!="x b50 c/"]+[n])
                stats,picks=native.gate(synthetic,t,routes)
                row=dict(turn=t,stats=stats,root_screen_river_picks=picks,
                         raw_seat_sha256=[sha(chance.weight_bytes(a)) for a in w])
                result["rows"].append(row)
                if any(picks.values()):result["leads"].append(dict(turn=t,rank_picks=picks))
            result["stage"]="ROOT_UI_PREFLIGHT_ONLY"
        result["scope"]="Six saved-root jobs in B904, per-artifact unseen turns only; leads are not historical dedup clearance, full held-out job replay, native solves, or same-deal GTO+NL2 evidence."
        out.mkdir(parents=True,exist_ok=False)
        (out/"screen.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
        print(json.dumps(dict(flop=flop,stage=result["stage"],strict_bb=len(hero),strict_co=len(villain),untested_turns=len(new),
            screened_turns=len(result["rows"]),leads=len(result["leads"]),rank_leads={k:sum(bool(x["rank_picks"][k]) for x in result["leads"]) for k in routes},coverage=cov)))
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--flop",required=True,choices=PINS)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();screen(a.flop,a.output.resolve())
