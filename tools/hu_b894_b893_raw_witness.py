"""B894: independent two-seat raw action witness for completed B893. No solves."""
import hashlib,json,sys,zipfile,math
from pathlib import Path
from hu_b892_independent_raw_witness import accepted,key,cards,node
from hu_b563_rank68_turn import fresh,check_boundary
from hu_b890_b563_static_gate import PINS,RUN
from hu_b893_r158_b563_exact_third import MODEL,FLOP,TURN,LINE,RIVER_LINE
from hu_b568_caller_rivers import hand_cell
import subprocess

def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def main():
    folder=Path(sys.argv[1])
    pin=read(Path("data/nl2_hu_b894_b893_replay_pins.json"))
    reg=read(Path("data/nl2_hu_multiboard_status_current.json"))
    w={n["model_id"]:n["estimated_NL2_hand_opportunity_fraction"] for n in read(Path("data/nl2_hu_multiboard_prerank.json"))["nodes"]}
    assert set(w)==set(reg["records"]) and len(w)==392
    cert=[k for k,v in reg["records"].items() if v["label"]=="CERT-MULTIBOARD"]
    approx=[k for k,v in reg["records"].items() if v["label"]=="APPROX"]
    cov=round(100*math.fsum(w[k] for k in cert)/math.fsum(w.values()),6)
    assert MODEL in approx and w[MODEL]>=.002 and cov<90
    route,=[x for x in json.loads(subprocess.check_output(["node","tools/hu_b881_tail_price_routes.cjs"])) if x["rank"]==158]
    assert (route["profile"],route["pot"],route["stack"])==("UTG_CO",21.66,89.92)
    fc={x["cell"] for x in route["flopIngress"]};tc={x["cell"] for x in route["turnIngress"]}
    rc={x["cell"] for x in route["river"] if x["action"]=="過"}
    sources=fresh(folder/"original",TURN,RUN)
    modes={};metadata={}
    for source in sources:
        mode=source["version"];p=pin["artifacts"][mode]
        archive=folder/(mode+".zip")
        assert sha(archive.read_bytes())==p["sha256"]
        assert source["archive_sha256"]==PINS[mode]
        check_boundary(source,FLOP,TURN)
        r=source["root"];rj=source["root_job"]
        with zipfile.ZipFile(archive) as z:
            sraw=z.read("b893-source/native/result.json");jraw=z.read("b893-source/native/job.json")
            s=json.loads(sraw);j=json.loads(jraw);pr=json.loads(z.read("b893-source/proof.json"))
            planraw=z.read("b893-source/plan.json");plan=json.loads(planraw)
        assert pr["mode"]==mode and pr["rank"]==158
        assert (pr["original_root_sha256"],pr["previous_turn_sha256"])==(source["root_sha256"],source["source_sha256"])
        assert (pr["job_sha256"],pr["result_sha256"],pr["plan_sha256"])==(sha(jraw),sha(sraw),sha(planraw))
        assert (r["flop"],r["pot"],r["stack"],s["flop"],s["pot"],s["stack"])==(FLOP,650,9750,FLOP,1300,9425)
        assert (j["turn"],j["line0"],j["turn_oop"],j["rake_rate"],j["rake_cap"])==(TURN,["x","b50","c","/"],"33.333333%,50%,100%",.05,1000)
        for g in (r,s):assert 0<=g["info"]["gto_expl_pct"]<=.5
        if mode=="exp_oop":
            assert j["hero"]==rj["hero"]==0 and j["locks"] and rj["locks"]
            assert 0<=r["info"]["hero_gap_pct"]<=.5 and 0<=s["info"]["hero_gap_pct"]<=.5
            assert pr["measured_partial_lock"] and not pr["private_card_empirical_frequencies"]
        else:assert not j.get("locks") and not rj.get("locks") and not s["info"].get("lock_stats")
        f,=[n["board"] for n in r["nodes"] if n["line"]=="" and len(n["board"])==6 and n["player"]==0]
        assert cards(f)==cards(FLOP);t=f+TURN
        a=node(r,"",f,0,650,[0,0]);b=node(r,"x",f,1,650,[0,0]);c=node(r,"x b50",f,0,975,[0,325])
        parent=node(r,LINE+"/",t,0,1300,[325,325])
        u=node(s,LINE+"/",t,0,1300,[0,0]);v=node(s,LINE+"/b33",t,1,1733,[433,0])
        for seat,k in enumerate(("oop_w","ip_w")):
            assert j[k]==[[h,w] for h,w in zip(r["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4]
        hero=accepted(r,a,"x")&accepted(r,c,"c")&accepted(s,u,"b33")
        foe=accepted(r,b,"b50")&accepted(s,v,"c")
        modes[mode]={}
        assert len(pr["rows"])==8 and {board[-2:] for board in pr["rows"]}==set(plan["rivers"])
        for board,row in pr["rows"].items():
            assert board.startswith(t) and len(cards(board))==5
            n=node(s,RIVER_LINE,board,0,2166,[433,433])
            assert "b50" in n["acts"] and row["public_board"]==board and row["acting_seat"]==0 and row["line"]==RIVER_LINE
            hs={h for h in hero&accepted(s,n,"x") if cards(h).isdisjoint(cards(board))}
            vs={key(h) for h,w in zip(s["hands"][1],n["w"][1],strict=True) if w>1e-4 and cards(h).isdisjoint(cards(board))}&foe
            expected={(h,o) for h in hs for o in vs if cards(h).isdisjoint(cards(o)) and hand_cell(h,f)[0] in fc and hand_cell(h,t)[0] in tc and hand_cell(h,board)[0] in rc}
            claimed={(key(h),key(o)) for h,opps in row["rendered_exact_deals"].items() for o in opps}
            assert expected==claimed, (mode,board,len(expected),len(claimed))
            modes[mode][board]=(expected,row["b50"])
        metadata[mode]=dict(artifact=p["id"],archive_sha256=p["sha256"],original_archive_sha256=source["archive_sha256"],root_sha256=source["root_sha256"],previous_turn_sha256=source["source_sha256"],job_sha256=sha(jraw),result_sha256=sha(sraw),plan_sha256=sha(planraw))
    assert set(modes["gto"])==set(modes["exp_oop"])
    rows=[]
    for b in sorted(modes["gto"]):
        g,gm=modes["gto"][b];e,em=modes["exp_oop"][b];shared=g&e
        rows.append(dict(board=b,gto_pairs=len(g),nl2_pairs=len(e),shared_pairs=len(shared),shared_hero_combos=len({h for h,o in shared}),shared_deals=sorted(shared),gto_b50_raw_evidence=gm,nl2_b50_raw_evidence=em))
    result=dict(schema="B894_B893_INDEPENDENT_WITNESS_V1",rank=158,model=MODEL,source_run=pin["native_run"],sources=metadata,rows=rows,cert=len(cert),approx=len(approx),coverage_pct=cov,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,scope="Exact one-flop candidate only. Both-seat physical deal intersection, not a certificate or recommendation; b50 evidence remains exact-node research.")
    print(json.dumps(result,sort_keys=True,indent=2))
if __name__=="__main__":main()
