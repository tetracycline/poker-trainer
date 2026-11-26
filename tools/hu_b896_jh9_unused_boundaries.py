"""B896: authenticate two previously untested exact-price turn boundaries on
the existing B538 Jh9s4c dual roots. No native invocation, no promotion.
A static witness is not a solved turn action or river certificate."""
import hashlib,itertools,json,math,subprocess,sys
from pathlib import Path
from zipfile import ZipFile
from hu_b538_utg_check_calls import authenticate, FLOPS
from hu_b881_utg_price_boundary import cards,DECK,one,count_pairs,witness
from hu_sequential_cfr_reach import accepted,cardkey
from hu_b568_caller_rivers import hand_cell
from hu_b483_locked_medium import PIPELINE,RANGES,POOL
import hu_b890_b563_static_gate as inventory

FLOP="Jh9s4c"
TURNS=("4h","Kd")
RUN=45119866932
HEAD="44f2b5752f3cf865227c409170499365c944e166"
PINS={"gto":(14793064321,"ba70074244bb43b8fd76084387fef33e3cdf841b75c4dcc6bbc66937d584de5d"),
      "exp_oop":(14793179237,"5725c0ac58a589fda92a264083b92399ea90f6184f510d1e94673b40b78f099a")}
REG=Path("data/nl2_hu_multiboard_status_current.json")
LINE="x b50 c"
SIZES={157:(975,"b75"),158:(433,"b33")}
def load(p):return json.loads(p.read_bytes())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def git(*a):return subprocess.check_output(["git",*a],text=True).strip()
def dump(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()

def validate_sources(inp):
    receipt=load(inp/"run.json")
    assert (receipt["id"],receipt["head_sha"],receipt["head_branch"],receipt["status"],receipt["conclusion"])==(RUN,HEAD,"fix/nl2-hu-lines-audit-20261118","completed","success")
    for mode,(ident,digest) in PINS.items():
        name=f"NL2-B538-{FLOP}-{mode}"
        meta=load(inp/(mode+".json"))
        assert (meta["id"],meta["name"],meta["digest"],meta["expired"])==(ident,name,"sha256:"+digest,False)
        assert (meta["workflow_run"]["id"],meta["workflow_run"]["head_sha"])==(RUN,HEAD)
        archive=inp/(mode+".zip")
        assert sha(archive.read_bytes())==digest
        dst=inp/name
        if not dst.exists():
            with ZipFile(archive) as z:
                assert all(not Path(n).is_absolute() and ".." not in Path(n).parts for n in z.namelist())
                z.extractall(dst)

def boundary(s,turn):
    root,j,m=s["root"],s["root_job"],s["manifest"]
    assert root["flop"]==FLOP and (root["pot"],root["stack"],j["rake_rate"],j["rake_cap"])==(650,9750,.05,1000)
    assert (m["spot"],m["solver_pin"],m["solver_ranges_sha256"],m["pool_source_sha256"])==("UTG_CO",PIPELINE,RANGES,POOL)
    assert m["preflop_ranges"]["source"]=="PINNED_POKER_SOLVER_PREFLOP_CFR"
    assert m["file_flop_sha256"]==s["root_sha256"]
    if s["subgame"] is None:return None
    sub=s["subgame"]
    assert (sub["pot"],sub["stack"],s["subgame_job"]["turn"],s["subgame_job"]["line0"])==(1300,9425,turn,["x","b50","c","/"])
    assert s["subgame_job"]["turn_oop"]==s["subgame_job"]["turn_ip"]=="50%,100%"
    if not all(0<=g["info"]["gto_expl_pct"]<=.5 for g in (root,sub)):return None
    if s["version"]=="gto":
        assert not j.get("locks") and j.get("hero") is None and not root["info"].get("lock_stats")
    else:
        assert j["hero"]==0 and j["locks"] and root["info"]["lock_stats"] and s["actual_flop_job_lock_coverage"]
        if not all(0<=g["info"]["hero_gap_pct"]<=.5 for g in (root,sub)):return None
    a,b,c=[one(root["nodes"],line,6) for line in ("","x","x b50")]
    assert [(n["player"],n["pot"],n["bets"]) for n in (a,b,c)]==[(0,650,[0,0]),(1,650,[0,0]),(0,975,[0,325])]
    p=one(root["nodes"],LINE+"/",8,turn)
    assert (p["player"],p["pot"],p["bets"])==(0,1300,[325,325])
    board=p["board"]
    assert cards(board[:6])==cards(FLOP) and board[-2:]==turn
    masks=[accepted(a,root["hands"],"x")&accepted(c,root["hands"],"c"),accepted(b,root["hands"],"b50")]
    sides=[masks[i]&{cardkey(h) for h,w in zip(root["hands"][i],p["wr"][i],strict=True) if w>1e-4 and cards(board).isdisjoint(cardkey(h))} for i in (0,1)]
    return board,sides

def main(inp,out):
    validate_sources(inp)
    before=REG.read_bytes();reg=json.loads(before)
    frozen=load(Path("data/nl2_hu_multiboard_prerank.json"))["nodes"]
    weights={n["model_id"]:n["estimated_NL2_hand_opportunity_fraction"] for n in frozen}
    assert len(weights)==392 and set(weights)==set(reg["records"])
    cert=[k for k,v in reg["records"].items() if v["label"]=="CERT-MULTIBOARD"]
    approx=[k for k,v in reg["records"].items() if v["label"]=="APPROX"]
    cov=round(100*math.fsum(weights[k] for k in cert)/math.fsum(weights.values()),6)
    assert (len(cert),len(approx),cov)==(158,234,84.700987)
    queue=sorted((dict(rank=reg["records"][k]["frequency_rank"],model=k,weight=weights[k]) for k in approx if weights[k]>=.002),key=lambda x:(-x["weight"],x["rank"]))
    assert len(queue)==30
    assert [x["rank"] for x in queue[-2:]]==[157,158]
    # Deliberately do not re-screen the Qc boundary already in B887, or the
    # known B538 nonconverged flops / three zero-NL2-reach 6c6d3h turns.
    historical=load(Path("data/nl2_hu_b538_utg_check_calls.json"))
    assert historical["run"]==RUN
    assert set(TURNS)<=set(FLOPS[FLOP]) and "Qc" not in TURNS
    for turn in TURNS:
        old,=[x for x in historical["attempts"] if (x["flop"],x["turn"])==(FLOP,turn)]
        assert old["nodes"] and any(x["status"]=="VERIFIED" for x in old["nodes"].values())
    routes=[r for r in json.loads(subprocess.check_output(["node","tools/hu_b881_tail_price_routes.cjs"])) if r["rank"] in SIZES]
    assert [r["rank"] for r in routes]==[157,158]
    for r in routes:
        rank=r["rank"];paid,_=SIZES[rank]
        assert r["id"] in approx and weights[r["id"]]>=.002 and r["profile"]=="UTG_CO"
        assert (r["root"]["pot"],r["root"]["stack"])==(6.5,97.5)
        assert (r["turn_facts"]["pot"],r["turn_facts"]["stack"])==(13,94.25)
        assert (r["pot"],r["stack"])==((1300+2*paid)/100,(9425-paid)/100)
        assert all(x["action"]=="跟" for x in r["flopIngress"])
        assert all(x["action"]==("下注 ¾" if rank==157 else "下注 ⅓") for x in r["turnIngress"])
    # Reuse the prior archive scanner, changing only the frozen target cards.
    inventory.NEW=FLOP;inventory.TURNS=TURNS
    inventory.NEEDLES=["".join(p).lower().encode() for p in itertools.permutations([FLOP[i:i+2] for i in range(0,6,2)])]
    hits=[];scanned=0
    for f in git("ls-files","data/solver_evidence").splitlines():
        if f.lower().endswith((".json",".json.gz",".zip")):
            inventory.scan(Path(f).read_bytes(),f,hits);scanned+=1
    assert scanned>1000
    # Named code leads must be reviewed before native dispatch; pin each file and
    # retain matching lines rather than treating missing compact index as proof.
    leads=git("grep","-il","-e",FLOP,"--",".github/workflows","tools","data/*inputs.json").splitlines()
    lead_inventory={f:{"blob":git("hash-object",f),"matching_lines":[{"line":i,"text":line[:2000]} for i,line in enumerate(Path(f).read_text().splitlines(),1) if FLOP.lower() in line.lower()]} for f in leads}
    rows=[]
    for turn in TURNS:
        pair=[authenticate(inp,FLOP,turn,v) for v in ("gto","exp_oop")]
        g,e=[boundary(s,turn) for s in pair]
        for r in routes:
            rank=r["rank"];paid,token=SIZES[rank]
            prior=[h for h in hits if (h["rank"],h["turn"])==(rank,turn)]
            rec=dict(rank=rank,model=r["id"],flop=FLOP,turn=turn,root_sha256=[s["root_sha256"] for s in pair],
                     prior_subgame_sha256=[s.get("source_sha256") for s in pair],target_paid_cents=paid,
                     target_pot_cents=1300+2*paid,target_stack_cents=9425-paid,raw_exact_hits=prior,can_dispatch_native=False)
            if g is None or e is None:
                rows.append(dict(rec,status="BLOCKED_MISSING_OR_UNCONVERGED_PARENT"));continue
            assert g[0]==e[0]
            board=g[0];hero=g[1][0]&e[1][0];opp=g[1][1]&e[1][1]
            fc={x["cell"] for x in r["flopIngress"]};tc={x["cell"] for x in r["turnIngress"]}
            rc={x["cell"] for x in r["river"] if x["action"]=="過"}
            assert fc and tc
            visible={h for h in hero if hand_cell("".join(h),board[:6])[0] in fc and hand_cell("".join(h),board)[0] in tc}
            candidates=[]
            for river in DECK:
                if river in cards(board):continue
                hs={h for h in visible if river not in h and hand_cell("".join(h),board+river)[0] in rc}
                vs={v for v in opp if river not in v}
                n=count_pairs(hs,vs)
                if n:candidates.append(dict(river=river,static_prior_pairs=n,witness=witness(hs,vs)))
            status="EXISTING_EXACT_JOB_REVIEW_ONLY" if prior else ("STATIC_POSITIVE_PENDING_CODE_LEAD_REVIEW" if candidates else "NO_STATIC_CHECK_WITNESS")
            rows.append(dict(rec,status=status,common_prior_physical_pairs=count_pairs(hero,opp),rendered_eligible_hero_combos=len(visible),static_check_river_candidates=candidates))
    rows.sort(key=lambda x:(-weights[x["model"]],x["rank"],x["turn"]))
    report=dict(schema="NL2_B896_JH9S4C_UNUSED_PRICED_BOUNDARIES_V1",registry_sha256=sha(before),CERT=len(cert),APPROX=len(approx),
                weighted_model_opportunity_coverage_pct=cov,high_frequency_queue=queue,source_run=RUN,source_head=HEAD,
                artifact_pins=PINS,retained_archives_scanned=scanned,named_code_leads=lead_inventory,rows=rows,
                native_solves=0,original_flop_solves_repeated=0,CERT_promotions=0,
                scope="Two new exact-price turn boundary preflights only; no solved turn or river strategy, no lock or b50 recommendation. No inference about expired untracked archives. Higher-frequency queue is retained, not declared exhausted by this study.")
    out.mkdir(parents=True,exist_ok=False)
    (out/"report.json").write_bytes(dump(report))
    assert REG.read_bytes()==before
    print(json.dumps([dict(rank=r["rank"],turn=r["turn"],status=r["status"],common_prior_pairs=r.get("common_prior_physical_pairs"),static_rivers=len(r.get("static_check_river_candidates",[])),duplicate_hits=len(r["raw_exact_hits"])) for r in rows]))
if __name__=="__main__":main(Path(sys.argv[1]),Path(sys.argv[2]))
