"""B888: one genuinely new priced UTG lead continuation from the two B538 roots.
No original flop solve, no certificate writes. The two modes retain their own
original parent distributions. Success requires independent later cross-policy
intersection of identical physical deals and full audit.
"""
import argparse,base64,gzip,hashlib,itertools,json,math,re,subprocess,sys
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from decimal import Decimal, ROUND_HALF_UP
from hu_b538_utg_check_calls import authenticate
from hu_b881_utg_price_boundary import live, cards, DECK
from hu_b568_caller_rivers import hand_cell
from hu_b463_rank45_gate import SOLVER,RUST
from hu_b483_locked_medium import PIPELINE,RANGES,POOL,proof
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b637_rank57 import solve
from hu_sequential_cfr_reach import accepted,cardkey,game_reach

P=Path("data/nl2_hu_b888_r158_raw_dedup.json")
REG=Path("data/nl2_hu_multiboard_status_current.json")
FLOP="Ac8d3h";TURN="Qc";LINE="x b50 c";RIVER_LINE=LINE+"/b33 c/"
MODEL="ln-opfr-r_model-tl6ij8"
def sha(raw):return hashlib.sha256(raw).hexdigest()
def dump(x):return (json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode()
def load(p):return json.loads(p.read_bytes())
def git(*a):return subprocess.check_output(["git",*a],text=True).strip()
def target_flop(v):
    return isinstance(v,str) and len(v)==6 and cards(v)==cards(FLOP)
def chip_sizes(menu):
    out=set()
    for t in str(menu).split(","):
        t=t.strip()
        if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?%",t):
            out.add(int((Decimal(t[:-1])*Decimal(1300)/100).quantize(Decimal("1"),rounding=ROUND_HALF_UP)))
    return out
NEEDLES=[("".join(p)).lower().encode() for p in itertools.permutations([FLOP[:2],FLOP[2:4],FLOP[4:]])]
def scan_json(raw,path,hits):
    low=raw.lower()
    if not any(n in low for n in NEEDLES):return
    obj=json.loads(raw)
    def rec(x):
        if isinstance(x,dict):
            if target_flop(x.get("flop")) and x.get("turn")==TURN and x.get("pot")==1300 and x.get("stack")==9425:
                line=x.get("line0")
                if (line in (LINE,["x","b50","c","/"])) and 433 in chip_sizes(x.get("turn_oop","")):
                    hits.append(dict(path=path,kind="EXACT_EXISTING_JOB",job_sha256=sha(dump(x))))
                for n in x.get("nodes",[]):
                    if isinstance(n,dict) and n.get("line")==RIVER_LINE and n.get("pot")==2166 and n.get("player")==0:
                        hits.append(dict(path=path,kind="EXACT_EXISTING_RIVER_NODE",board=n.get("board")))
            for v in x.values():
                if isinstance(v,(list,dict)):rec(v)
        elif isinstance(x,list):
            for v in x:
                if isinstance(v,(list,dict)):rec(v)
    rec(obj)
def scan_archive(raw,path,hits,depth=0):
    assert depth<=4,"unexpected nested archive depth"
    if raw[:2]==b"\x1f\x8b":
        scan_archive(gzip.decompress(raw),path+"!gzip",hits,depth+1)
    elif raw[:4]==b"PK\x03\x04":
        with ZipFile(BytesIO(raw)) as z:
            for n in sorted(z.namelist()):
                if n.lower().endswith((".json",".json.gz",".zip")):
                    scan_archive(z.read(n),path+"!"+n,hits,depth+1)
    elif path.lower().endswith(".json") or raw.lstrip()[:1] in (b"{",b"["):
        scan_json(raw,path,hits)
def preflight(a):
    p=load(P)
    assert (p["rank"],p["model"],p["flop"],p["turn"])==(158,MODEL,FLOP,TURN)
    reg=load(REG);rank=load(Path("data/nl2_hu_multiboard_prerank.json"))
    w={n["model_id"]:n["estimated_NL2_hand_opportunity_fraction"] for n in rank["nodes"]}
    cov=round(100*math.fsum(w[k] for k,v in reg["records"].items() if v["label"]=="CERT-MULTIBOARD")/math.fsum(w.values()),6)
    assert (reg["CERT_MULTIBOARD"],reg["APPROX"],cov)==(158,234,84.700987) and reg["records"][MODEL]["label"]=="APPROX"
    assert w[MODEL]>=.002
    r=a.input/"b887.zip";assert sha(r.read_bytes())==p["b887"]["sha256"]
    with ZipFile(r) as z:
        old=json.loads(z.read("report.json"));route_list=json.loads(z.read("current-index/routes.json"))
    assert old["registry_sha256"]==sha(REG.read_bytes())
    row,=[x for x in old["rows"] if (x["rank"],x["flop"],x["turn"])==(158,FLOP,TURN)]
    assert row["status"]=="STATIC_POSITIVE_PENDING_RAW_JOB_DEDUP" and len(row["candidate_rivers"])==27
    assert row["historical_raw_filename_leads"]==p["historical_raw_leads"] and row["historical_code_and_manifest_leads"]==p["historical_code_leads"]
    assert row["common_prior_physical_pairs"]==658 and row["rendered_eligible_hero_combos"]==19
    route,=[x for x in route_list if x["rank"]==158]
    assert (route["pot"],route["stack"])==(21.66,89.92)
    # Verify current geometry independently, not merely the previous artifact.
    current=json.loads(subprocess.check_output(["node","tools/hu_b874_tail_routes.cjs"]))
    assert route==next(x for x in current if x["rank"]==158)
    assert git("rev-parse",p["b887"]["head"]+":"+str(REG))==git("rev-parse","HEAD:"+str(REG))
    # The previous named raw inventory has only the source archive and two
    # byte-identical viewer aliases. B563's actual fresh root was As9d4c.
    assert sha(Path(p["historical_raw_leads"][1]).read_bytes())==sha(Path(p["historical_raw_leads"][2]).read_bytes())
    for f in p["historical_code_leads"]:
        assert git("rev-parse","HEAD:"+f)==git("rev-parse",p["b887"]["head"]+":"+f)
    # Scan every retained tracked archive (including generic filenames and
    # compressed/nested raw job documents). Unknown parse failures stop dispatch.
    hits=[];scanned=0
    for f in git("ls-files","data/solver_evidence").splitlines():
        if f.lower().endswith((".json",".json.gz",".zip")):
            scan_archive(Path(f).read_bytes(),f,hits);scanned+=1
    assert scanned>1000
    if hits:raise ValueError("Prior exact job or result found; no native invocation: "+json.dumps(hits[:20]))
    # Check latest named workflow/tool leads as well as original raw ZIPs.
    leads=git("grep","-il","-e",FLOP,"--",".github/workflows","tools","data/*inputs.json").splitlines()
    assert set(leads)-set(p["historical_code_leads"])<={"tools/hu_b888_r158_exact_third.py",".github/workflows/nl2-hu-b888-r158-exact-third.yml"}
    a.output.mkdir(parents=True,exist_ok=True)
    rivers=[x["river"] for x in sorted(row["candidate_rivers"],key=lambda x:(-x["static_prior_pairs"],DECK.index(x["river"])))[:8]]
    assert len(set(rivers))==8
    sources={}
    for pin in p["sources"]:
        v=pin["version"];zpath=a.input/(pin["name"]+".zip")
        assert sha(zpath.read_bytes())==pin["sha256"]
        dst=a.input/pin["name"]
        if not dst.exists():
            with ZipFile(zpath) as z:
                assert all(not Path(n).is_absolute() and ".." not in Path(n).parts for n in z.namelist())
                z.extractall(dst)
        with ZipFile(zpath) as z:
            names=[n for n in z.namelist() if n.endswith(".job.json")]
            assert len(names)==4
            for n in names:
                j=json.loads(z.read(n));t=j.get("turn")
                expected=pin["turn_jobs"][t] if t else [pin["root_job"],pin["root_result"]]
                assert [sha(z.read(n)),sha(z.read(n.replace(".job.json",".json")))]==expected
                if t:
                    assert (j["pot"],j["stack"],j["line0"],j["turn_oop"])==(1300,9425,["x","b50","c","/"],"50%,100%")
                    assert 433 not in chip_sizes(j["turn_oop"])
        s=authenticate(a.input,FLOP,TURN,v)
        assert s["root_sha256"]==pin["root_result"] and s["source_sha256"]==pin["turn_jobs"][TURN][1]
        live(s,FLOP)
        sources[v]=s
    assert [sources[v]["root_sha256"] for v in ("gto","exp_oop")]==row["root_sha256"]
    assert [sources[v]["source_sha256"] for v in ("gto","exp_oop")]==row["prior_subgame_sha256"]
    plan=dict(schema="NL2_B888_EXACT_THIRD_FROZEN_PLAN_V1",rank=158,flop=FLOP,turn=TURN,source_run=p["source_run"],
        source_root_sha256=row["root_sha256"],source_previous_turn_sha256=row["prior_subgame_sha256"],
        source_artifacts=p["sources"],target_paid_cents=433,target_pot=2166,target_stack=8992,
        existing_menu="50%,100%",new_menu=p["new_turn_menu"],rivers=rivers,retained_archives_scanned=scanned,
        exact_duplicates=[],code_leads=leads,registry_sha256=sha(REG.read_bytes()),coverage_pct=cov,
        dedup_scope="Retained tracked raw job/results plus named original completed ZIPs and code leads. No claim about unavailable expired untracked artifacts.",
        original_flop_solves_repeated=0,certifications_granted=0)
    return sources[a.mode],route,plan
def eligible(root,sub,n,route,mask):
    public=n["board"];turn=public[:8]
    turn_root,=[x for x in sub["nodes"] if x["line"]==LINE+"/" and x["board"]==turn and x["player"]==0]
    face,=[x for x in sub["nodes"] if x["line"]==LINE+"/b33" and x["board"]==turn and x["player"]==1]
    assert (turn_root["pot"],turn_root["bets"],face["pot"],face["bets"])==(1300,[0,0],1733,[433,0])
    # Opponent must take the exact flop stab and then the exact 433-cent call,
    # on this same physical deal, not simply have nonzero abstract reach.
    ip,=[x for x in root["nodes"] if x["line"]=="x" and len(x["board"])==6 and x["player"]==1]
    foes=accepted(ip,root["hands"],"b50") & accepted(face,sub["hands"],"c")
    foes &= {cardkey(h) for h,w in zip(sub["hands"][1],n["w"][1],strict=True) if w>1e-4 and cards(public).isdisjoint(cardkey(h))}
    flop_cells={x["cell"] for x in route["flopIngress"]};turn_cells={x["cell"] for x in route["turnIngress"]}
    river_cells={x["cell"] for x in route["river"] if x["action"]=="過"}
    bit=1<<n["acts"].index("x")
    good={}
    for h,bits in zip(sub["hands"][0],base64.b64decode(mask,validate=True),strict=True):
        h=cardkey(h)
        if not bits&bit or not cards(public).isdisjoint(h):continue
        hs="".join(h)
        if hand_cell(hs,public[:6])[0] not in flop_cells or hand_cell(hs,turn)[0] not in turn_cells or hand_cell(hs,public)[0] not in river_cells:continue
        vs=sorted("".join(v) for v in foes if set(h).isdisjoint(v))
        if vs:good[hs]=vs
    return good
def run(a):
    s,route,plan=preflight(a)
    solver=a.solver.resolve()
    assert git("-C",str(solver),"rev-parse","HEAD")==SOLVER
    for path,digest in (("postflop/py/pipeline.py",PIPELINE),("postflop/py/ranges.py",RANGES),("inputs/pool_stats.json",POOL)):
        assert sha((solver/path).read_bytes())==digest
    if a.driver:
        assert a.driver.resolve()==solver/"postflop/pfdriver/target/release/pfdriver"
        assert git("-C",str(solver/"postflop/postflop-solver"),"rev-parse","HEAD")==RUST
    pool=load(solver/"inputs/pool_stats.json")["NL2"]
    job=deepcopy(s["subgame_job"])
    assert job["turn_oop"]=="50%,100%" and job["turn_ip"]=="50%,100%"
    # Only change the OOP decision menu, preserve the two source-specific
    # ranges, rake, IP menu and original measured/assumed lock distinction.
    job.update(turn_oop=plan["new_menu"],out="result.json",iters=2000,target_pct=.45,
        extract=[dict(prefix=[],street=True)]+[dict(prefix=["b33","c",r],street=True) for r in plan["rivers"]])
    assert chip_sizes(job["turn_oop"])=={433,650,1300}
    if a.mode=="exp_oop":job["rank_pct"]=.45
    if a.preflight:
        print(json.dumps(plan));return
    if a.driver:
        assert not (a.output/"native/job.json").exists()
        (a.output/"plan.json").write_bytes(dump(plan))
    else:assert (a.output/"plan.json").read_bytes()==dump(plan)
    sub=solve(a.output/"native",job,a.driver)
    assert (sub["flop"],sub["pot"],sub["stack"])==(FLOP,1300,9425)
    assert 0<=sub["info"]["gto_expl_pct"]<=.5
    if a.mode=="exp_oop":
        assert job["hero"]==0 and 0<=sub["info"]["hero_gap_pct"]<=.5
        lock=audit_patterns(sub,job,s["manifest"],pool,0)
        token=r"^(?:[^/]*/){1}(?:[^/]+ )?b33$"
        assert lock["first_pattern_visible_nodes"].get(token,0)>0 and lock["driver_tree_nodes"].get(token,0)>0
        assert lock["marginal_targets"][token]["source"]=="NL2.HU_facing_bet[2].by_size[≤33%]"
    else:
        assert not job.get("locks") and not sub["info"].get("lock_stats");lock=None
    sub.update(line0=LINE,turn=TURN,rivers=plan["rivers"])
    masks=game_reach(s["root"],sub)[0];rows={}
    targets=[n for n in sub["nodes"] if n["line"]==RIVER_LINE and n["player"]==0 and len(n["board"])==10]
    assert {n["board"][-2:] for n in targets}==set(plan["rivers"])
    for n in targets:
        assert (n["pot"],n["bets"],9425-max(n["bets"]))==(2166,[433,433],8992)
        assert "b50" in n["acts"] and "x" in n["acts"]
        obs=proof(s["root"],sub,n,masks)
        obs["rendered_exact_deals"]=eligible(s["root"],sub,n,route,obs["compatible_action_mask_b64"])
        rows[n["board"]]=obs
    result=dict(schema="NL2_B888_R158_EXACT_THIRD_NATIVE_POLICY_V1",rank=158,mode=a.mode,flop=FLOP,turn=TURN,
        original_root_sha256=s["root_sha256"],previous_turn_sha256=s["source_sha256"],plan_sha256=sha(dump(plan)),
        job_sha256=sha((a.output/"native/job.json").read_bytes()),result_sha256=sha((a.output/"native/result.json").read_bytes()),
        pool_sha256=POOL,solver=SOLVER,rust=RUST,info=sub["info"],measured_partial_lock=lock,rows=rows,
        private_card_empirical_frequencies=False,original_flop_solves_repeated=0,CERT_promotions=0,
        scope="One flop, one source-specific conditional turn menu, candidate river policies. Intersect the same physical hero AND villain deal across the two independent policy artifacts before any named-board acceptance; not a CERT.")
    raw=dump(result);file=a.output/"proof.json"
    if a.driver:file.write_bytes(raw)
    else:assert file.read_bytes()==raw
    print(json.dumps(dict(mode=a.mode,river_nodes=len(rows),rendered_positive=sum(bool(x["rendered_exact_deals"]) for x in rows.values()),CERT_promotions=0)))
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("input","solver","output"):p.add_argument("--"+k,type=Path,required=True)
    p.add_argument("--mode",choices=("gto","exp_oop"),required=True)
    p.add_argument("--driver",type=Path);p.add_argument("--preflight",action="store_true")
    run(p.parse_args())
