"""B890: static candidate inventory from the already solved B563 dual roots.
Never invokes the native driver; exact physical common reach before the turn
does not establish a post-turn strategy or certify a board.
"""
import gzip,hashlib,itertools,json,math,re,subprocess,sys
from decimal import Decimal,ROUND_HALF_UP
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
from hu_b563_rank68_turn import NEW,TURNS,fresh,check_boundary,code_for
from hu_b881_utg_price_boundary import cards,DECK,one,count_pairs,witness
from hu_sequential_cfr_reach import accepted,cardkey
from hu_b568_caller_rivers import hand_cell

D=Path("data")
REG=D/"nl2_hu_multiboard_status_current.json"
RUN=45127617306
HEAD="d288704f9825c9fb055441302d841d323c316419"
PINS={"gto":"ae42b0f84772d198508181362bb772938a1a1ac77b27616204361dd5123b34bc",
      "exp_oop":"12ead48dcc86a2dcdb1558904bd8661a10a9a840bc84ef206c5c60b5c98f2510"}
LINE="x b50 c"
NEEDLES=["".join(p).lower().encode() for p in itertools.permutations([NEW[i:i+2] for i in range(0,6,2)])]
SIZES={157:(975,"b75"),158:(433,"b33")}

def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(p):return json.loads(p.read_bytes())
def git(*a):return subprocess.check_output(["git",*a],text=True).strip()
def sizes(menu):
    out=set()
    for t in str(menu).split(","):
        t=t.strip()
        if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?%",t):
            out.add(int((Decimal(t[:-1])*Decimal(1300)/100).quantize(Decimal("1"),rounding=ROUND_HALF_UP)))
    return out
def eligible(s,turn):
    check_boundary(s,NEW,turn)
    r=s["root"];j=s["root_job"];m=s["manifest"];sub=s["subgame"]
    assert r["flop"]==NEW and (r["pot"],r["stack"],j["rake_rate"],j["rake_cap"])==(650,9750,.05,1000)
    assert m["preflop_ranges"]["source"]=="PINNED_POKER_SOLVER_PREFLOP_CFR"
    assert 0<=r["info"]["gto_expl_pct"]<=.5
    if s["version"]=="gto":
        assert not j.get("locks") and j.get("hero") is None
    else:
        assert j["hero"]==0 and j["locks"] and r["info"]["lock_stats"] and 0<=r["info"]["hero_gap_pct"]<=.5
    if sub is None:return None
    assert 0<=sub["info"]["gto_expl_pct"]<=.5
    if s["version"]!="gto":assert 0<=sub["info"]["hero_gap_pct"]<=.5
    a,b,c=[one(r["nodes"],line,6) for line in ("","x","x b50")]
    p=one(r["nodes"],LINE+"/",8,turn)
    assert (p["player"],p["pot"],p["bets"])==(0,1300,[325,325])
    board=p["board"]
    assert cards(board[:6])==cards(NEW) and board[-2:]==turn
    allowed=[accepted(a,r["hands"],"x")&accepted(c,r["hands"],"c"),accepted(b,r["hands"],"b50")]
    sides=[allowed[i]&{cardkey(h) for h,w in zip(r["hands"][i],p["wr"][i],strict=True) if w>1e-4 and cards(board).isdisjoint(cardkey(h))} for i in (0,1)]
    return board,sides,s["subgame_job"]["turn_oop"]
def scan_json(raw,path,hits):
    low=raw.lower()
    if not any(n in low for n in NEEDLES):return
    obj=json.loads(raw)
    def rec(x):
        if isinstance(x,dict):
            f=x.get("flop")
            turn=x.get("turn")
            if isinstance(f,str) and len(f)==6 and cards(f)==cards(NEW) and turn in TURNS and (x.get("pot"),x.get("stack"))==(1300,9425):
                if x.get("line0") in (LINE,["x","b50","c","/"]):
                    for rank,(paid,token) in SIZES.items():
                        if paid in sizes(x.get("turn_oop","")):
                            hits.append(dict(rank=rank,turn=turn,kind="EXACT_JOB_MENU",path=path))
            b=x.get("board")
            if isinstance(b,str) and len(b)==10 and cards(b[:6])==cards(NEW) and b[6:8] in TURNS and x.get("player")==0:
                for rank,(paid,token) in SIZES.items():
                    if x.get("line")==LINE+"/"+token+" c/" and x.get("pot")==1300+2*paid:
                        hits.append(dict(rank=rank,turn=b[6:8],kind="EXACT_EXISTING_RIVER_NODE",board=b,path=path))
            for v in x.values():
                if isinstance(v,(list,dict)):rec(v)
        elif isinstance(x,list):
            for v in x:
                if isinstance(v,(list,dict)):rec(v)
    rec(obj)
def scan(raw,path,hits,depth=0):
    assert depth<=4
    if raw[:2]==b"\x1f\x8b":
        scan(gzip.decompress(raw),path+"!gzip",hits,depth+1)
    elif raw[:4]==b"PK\x03\x04":
        with ZipFile(BytesIO(raw)) as z:
            for n in sorted(z.namelist()):
                if n.lower().endswith((".json",".json.gz",".zip")):scan(z.read(n),path+"!"+n,hits,depth+1)
    elif path.lower().endswith(".json") or raw.lstrip()[:1] in (b"{",b"["):
        scan_json(raw,path,hits)
def main(out,receipt_path):
    out.mkdir(parents=True,exist_ok=False)
    receipt=load(receipt_path)
    assert (receipt["id"],receipt["head_sha"],receipt["head_branch"],receipt["status"],receipt["conclusion"])==(RUN,HEAD,"fix/nl2-hu-lines-audit-20261118","completed","success")
    before=REG.read_bytes();reg=json.loads(before)
    nodes=load(D/"nl2_hu_multiboard_prerank.json")["nodes"]
    weights={n["model_id"]:n["estimated_NL2_hand_opportunity_fraction"] for n in nodes}
    assert set(weights)==set(reg["records"]) and len(weights)==392
    cert=[k for k,v in reg["records"].items() if v["label"]=="CERT-MULTIBOARD"]
    approx=[k for k,v in reg["records"].items() if v["label"]=="APPROX"]
    coverage=round(100*math.fsum(weights[k] for k in cert)/math.fsum(weights.values()),6)
    assert (len(cert),len(approx),coverage)==(158,234,84.700987)
    for mode,digest in PINS.items():
        p=D/"solver_evidence"/("NL2_"+code_for(mode)+".zip")
        assert sha(p.read_bytes())==digest
    routes=[r for r in json.loads(subprocess.check_output(["node","tools/hu_b881_tail_price_routes.cjs"])) if r["rank"] in SIZES]
    assert [r["rank"] for r in routes]==[157,158]
    priority={r["rank"]:r for r in load(D/"nl2_hu_b838_234_approx_frequency_priority.json")["rows"]}
    for r in routes:
        assert priority[r["rank"]]["model_id"]==r["id"] and r["id"] in approx and weights[r["id"]]>=.002
        assert r["profile"]=="UTG_CO" and r["root"]["pot"]==6.5 and r["root"]["stack"]==97.5
        assert r["turn_facts"] is not None and r["turn_facts"]["root"]==r["root"]
        assert (r["turn_facts"]["pot"],r["turn_facts"]["stack"])==(13,94.25)
        paid,token=SIZES[r["rank"]]
        assert (r["pot"],r["stack"])==((1300+2*paid)/100,(9425-paid)/100)
    hits=[];scanned=0
    for f in git("ls-files","data/solver_evidence").splitlines():
        if f.lower().endswith((".json",".json.gz",".zip")):
            scan(Path(f).read_bytes(),f,hits);scanned+=1
    assert scanned>1000
    leads=git("grep","-il","-e",NEW,"--",".github/workflows","tools","data/*inputs.json").splitlines()
    rows=[]
    for turn in TURNS:
        pair=fresh(out/"raw",turn,RUN)
        assert [s["version"] for s in pair]==["gto","exp_oop"]
        assert all(s["archive_sha256"]==PINS[s["version"]] for s in pair)
        bounds=[eligible(s,turn) for s in pair]
        for r in routes:
            rank=r["rank"];paid,token=SIZES[rank]
            prior=[h for h in hits if (h["rank"],h["turn"])==(rank,turn)]
            rec=dict(rank=rank,model=r["id"],flop=NEW,turn=turn,source_run=RUN,
                     root_sha256=[s["root_sha256"] for s in pair],
                     prior_subgame_sha256=[s.get("source_sha256") for s in pair],
                     target_paid_cents=paid,target_river_pot_cents=1300+2*paid,
                     target_stack_cents=9425-paid,raw_exact_hits=prior,can_dispatch_native=False)
            if any(x is None for x in bounds):
                rows.append(dict(rec,status="BLOCKED_MISSING_ARCHIVED_TURN_PARENT"));continue
            g,e=bounds
            assert g[0]==e[0]
            board=g[0];hero=g[1][0]&e[1][0];opp=g[1][1]&e[1][1]
            fc={x["cell"] for x in r["flopIngress"]};tc={x["cell"] for x in r["turnIngress"]}
            rc={x["cell"] for x in r["river"] if x["action"]=="過"}
            assert fc and tc
            assert all(x["action"]=="跟" for x in r["flopIngress"])
            assert all(x["action"]==("下注 ¾" if rank==157 else "下注 ⅓") for x in r["turnIngress"])
            visible={h for h in hero if hand_cell("".join(h),board[:6])[0] in fc and hand_cell("".join(h),board)[0] in tc}
            candidates=[]
            for river in DECK:
                if river in cards(board):continue
                hs={h for h in visible if river not in h and hand_cell("".join(h),board+river)[0] in rc}
                vs={v for v in opp if river not in v}
                n=count_pairs(hs,vs)
                if n:candidates.append(dict(river=river,static_prior_pairs=n,witness=witness(hs,vs)))
            menu_present=any(paid in sizes(x[2]) for x in bounds)
            status=("NO_STATIC_CHECK_WITNESS" if not candidates else
                    "EXISTING_JOB_OR_MENU_REVIEW_ONLY" if prior or menu_present else
                    "STATIC_POSITIVE_PENDING_FULL_CODE_LEAD_REVIEW")
            rows.append(dict(rec,status=status,original_menus=[g[2],e[2]],common_prior_physical_pairs=count_pairs(hero,opp),
                             rendered_eligible_hero_combos=len(visible),static_check_river_candidates=candidates))
    rows.sort(key=lambda x:(x["rank"],x["turn"]))
    report=dict(schema="NL2_B890_R157_R158_ARCHIVED_B563_STATIC_GATE_V1",registry_sha256=sha(before),
                CERT=len(cert),APPROX=len(approx),weighted_model_opportunity_coverage_pct=coverage,
                source_run=RUN,source_head=HEAD,source_archive_sha256=PINS,retained_archives_scanned=scanned,
                named_code_leads=leads,rows=rows,original_flop_solves_repeated=0,native_solves=0,CERT_promotions=0,
                scope="Existing original dual-policy flop boundary, same physical deals. River check-class candidate only; no solved turn lead or post-turn intersection. Raw inventory is retained archive scope only, not expired external artifacts. Do not dispatch from this report alone.")
    (out/"report.json").write_text(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    assert REG.read_bytes()==before
    print(json.dumps([{k:v for k,v in r.items() if k not in ("static_check_river_candidates","raw_exact_hits")} | {"static_rivers":len(r.get("static_check_river_candidates",[])),"raw_hits":len(r["raw_exact_hits"])} for r in rows],ensure_ascii=False))
if __name__=="__main__":main(Path(sys.argv[1]),Path(sys.argv[2]))
