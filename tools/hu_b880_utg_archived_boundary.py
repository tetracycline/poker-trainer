"""B880: rank157/158 new priced continuation preflight from B538 archived dual roots.
No native solver invocation, no promotion. Static witnesses stop at the turn boundary;
a possible river class is NOT a solved river policy or a shared post-turn reach proof.
"""
import collections,gzip,hashlib,json,subprocess,sys
from pathlib import Path
from hu_b568_caller_rivers import hand_cell
from hu_sequential_cfr_reach import accepted,cardkey
from hu_b463_rank45_gate import SOLVER
from hu_b483_locked_medium import POOL,RANGES,PIPELINE

D=Path("data")
PINS={
    "Jh9s4c":"716e87c13e000aa3d8593bce99ba4a87157d8e57fd05e672589547d8c9ce6a93",
    "Ac8d3h":"9269f5375b5c465cb1d9f37f7b0a5f31c296a365dc97ab87bf71690bfdc47d20",
}
RUN=45119866932
LINE="x b50 c"
DECK=[r+s for r in "23456789TJQKA" for s in "cdhs"]
def load(p):return json.loads(p.read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
def cards(board):return {board[i:i+2] for i in range(0,len(board),2)}
def one(nodes,line,boardlen,turn=None):
    n,=[n for n in nodes if n["line"]==line and len(n["board"])==boardlen and (turn is None or n["board"].endswith(turn))]
    return n
def live(s,flop):
    r=s["root"];j=s["root_job"];m=s["manifest"]
    assert r["flop"]==flop and (r["pot"],r["stack"])==(650,9750)
    assert (m["spot"],m["solver_pin"],m["solver_ranges_sha256"],m["pool_source_sha256"])==("UTG_CO",PIPELINE,RANGES,POOL)
    assert m["preflop_ranges"]["source"]=="PINNED_POKER_SOLVER_PREFLOP_CFR"
    assert (j["pot"],j["stack"],j["rake_rate"],j["rake_cap"])==(650,9750,.05,1000)
    assert m["file_flop_sha256"]==s["root_sha256"]
    assert 0<=r["info"]["gto_expl_pct"]<=.5
    if s["version"]=="gto":
        assert not j.get("locks") and j.get("hero") is None and not r["info"].get("lock_stats")
    else:
        assert j["hero"]==0 and j["locks"] and r["info"]["lock_stats"]
        assert 0<=r["info"]["hero_gap_pct"]<=.5
        assert s["actual_flop_job_lock_coverage"]
    a,b,c=[one(r["nodes"],line,6) for line in ("","x","x b50")]
    assert [(n["player"],n["pot"],n["bets"]) for n in (a,b,c)]==[(0,650,[0,0]),(1,650,[0,0]),(0,975,[0,325])]
    p=one(r["nodes"],LINE+"/",8,"Qc")
    assert (p["player"],p["pot"],p["bets"])==(0,1300,[325,325])
    board=p["board"]
    assert cards(board[:6])==cards(flop)
    allowed=[accepted(a,r["hands"],"x")&accepted(c,r["hands"],"c"),accepted(b,r["hands"],"b50")]
    eligible=[]
    for i in (0,1):
        eligible.append(allowed[i]&{cardkey(h) for h,w in zip(r["hands"][i],p["wr"][i],strict=True) if w>1e-4 and cards(board).isdisjoint(cardkey(h))})
    old=s["subgame_job"]
    assert old["turn"]=="Qc" and old["pot"]==1300 and old["stack"]==9425 and old["line0"]==["x","b50","c","/"]
    return board,eligible,old["turn_oop"],s["root_sha256"],s["source_sha256"]

def count_pairs(heroes,opponents):
    counts=collections.Counter(c for h in opponents for c in h)
    return sum(len(opponents)-counts[h[0]]-counts[h[1]]+int(h in opponents) for h in heroes)
def witness(hs,vs):
    for h in sorted(hs):
        for v in sorted(vs):
            if set(h).isdisjoint(v):return [list(h),list(v)]
    return None

def main(out):
    receipt=load(Path(sys.argv[2]))
    assert (receipt["id"],receipt["head_sha"],receipt["status"],receipt["conclusion"])==(RUN,"44f2b5752f3cf865227c409170499365c944e166","completed","success")
    reg=load(D/"nl2_hu_multiboard_status_current.json")
    rank=load(D/"nl2_hu_multiboard_prerank.json")
    pri=load(D/"nl2_hu_b838_234_approx_frequency_priority.json")
    assert (reg["CERT_MULTIBOARD"],reg["APPROX"],reg["EST"],reg["TOTAL"])==(158,234,0,392)
    from math import fsum
    weight={n["model_id"]:n["estimated_NL2_hand_opportunity_fraction"] for n in rank["nodes"]}
    coverage=round(100*fsum(weight[k] for k,v in reg["records"].items() if v["label"]=="CERT-MULTIBOARD")/fsum(weight.values()),6)
    assert coverage==84.700987
    routes=json.loads(subprocess.check_output(["node","tools/hu_b874_tail_routes.cjs"]))
    routes=[r for r in routes if r["rank"] in (157,158)]
    assert [r["rank"] for r in routes]==[157,158]
    tail=load(D/"nl2_hu_b874_tail_index_inventory.json")
    assert all(x["exact_actor_line_index_entries"]==0 for x in tail["models"] if x["rank"] in (157,158))
    results=[]
    for flop,digest in PINS.items():
        p=D/"solver_evidence"/f"NL2_B538_{flop.upper()}_QC_{RUN}.json.gz"
        raw=p.read_bytes();assert sha(raw)==digest
        source=json.loads(gzip.decompress(raw));assert source["run_id"]==RUN
        sources={s["version"]:s for s in source["source_arrays"]}
        assert set(sources)=={"gto","exp_oop"}
        g,e=[live(sources[v],flop) for v in ("gto","exp_oop")]
        assert g[0]==e[0]
        board=g[0];hero=g[1][0]&e[1][0];opp=g[1][1]&e[1][1]
        for route in routes:
            r=route["rank"]
            row,=[x for x in pri["rows"] if x["rank"]==r]
            assert row["passes_min_0_2_pct_frequency"] and row["model_id"]==route["id"]
            assert reg["records"][route["id"]]["label"]=="APPROX"
            assert route["profile"]=="UTG_CO" and route["root"]["pot"]==6.5 and route["root"]["stack"]==97.5
            assert route["flopIngressStatus"]=="RENDERED_PRIMARY_LINKS" and all(x["action"]=="跟" for x in route["flopIngress"])
            turn_action="下注 ¾" if r==157 else "下注 ⅓"
            # Fractional one-third (not 33%) is required by the exact price.
            paid=975 if r==157 else 433
            assert abs((1300+2*paid)/100-route["pot"])<=.011 and abs((9425-paid)/100-route["stack"])<=.011
            target_pct="75%" if r==157 else "33.333333%"
            assert all(x["action"]==turn_action for x in route["turnIngress"])
            flop_cells={x["cell"] for x in route["flopIngress"]};turn_cells={x["cell"] for x in route["turnIngress"]}
            river_cells={x["cell"]:x["action"] for x in route["river"]}
            visible={h for h in hero if hand_cell("".join(h),board[:6])[0] in flop_cells and hand_cell("".join(h),board)[0] in turn_cells}
            candidates=[]
            for river in DECK:
                if river in cards(board):continue
                public=board+river
                hs={h for h in visible if river not in h and hand_cell("".join(h),public)[0] in river_cells}
                vs={v for v in opp if river not in v}
                pairs=count_pairs(hs,vs)
                if pairs:
                    candidates.append(dict(river=river,static_prior_pairs=pairs,witness=witness(hs,vs)))
            # The original B538 subgame only studied check-check. A missing
            # compact-index entry cannot alone prove a size was never solved.
            menus=[g[2],e[2]]
            menu_present=any(any(abs(float(t.strip().rstrip("%"))-(75 if r==157 else 100/3))<.01 for t in m.split(",") if t.strip().rstrip("%").replace(".","",1).isdigit()) for m in menus)
            results.append(dict(rank=r,model=route["id"],flop=flop,turn=board[-2:],archive_sha256=digest,original_run=RUN,root_sha256=[g[3],e[3]],prior_subgame_sha256=[g[4],e[4]],old_turn_oop_menus=menus,target_turn_size=target_pct,original_menu_already_included_target=menu_present,expected_pot_cents=1300+2*paid,expected_stack_cents=9425-paid,common_prior_physical_pairs=count_pairs(hero,opp),rendered_eligible_hero_combos=len(visible),static_river_candidates=candidates,certifications_granted=0))
    results.sort(key=lambda x:(x["rank"],x["flop"]))
    out.mkdir(parents=True,exist_ok=True)
    report=dict(schema="NL2_B880_R157_R158_ORIGINAL_DUAL_ROOT_STATIC_PREFLIGHT_V1",CERT=158,APPROX=234,weighted_model_opportunity_coverage_pct=coverage,original_root_solves=0,new_native_solves=0,certifications_granted=0,scope="Common exact two-seat flop policy and possible future river texture only; no turn or river solved policy, no 50% candidate, no private-card empirical NL2 frequency. Further archive-wide dedup and native price/policy verification required.",rows=results)
    (out/"report.json").write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print(json.dumps([{k:x[k] for k in ("rank","flop","common_prior_physical_pairs","rendered_eligible_hero_combos","original_menu_already_included_target")} | {"static_rivers":len(x["static_river_candidates"])} for x in results]))
if __name__=="__main__":main(Path(sys.argv[1]))
