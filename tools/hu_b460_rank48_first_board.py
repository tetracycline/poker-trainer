#!/usr/bin/env python3
"""B460 rank48: independent, exact first-board BTN_BB b75 turn / BB OOP river proof.

No CERT promotion before three distinct *paired* authentic GTO and NL2 OOP boards.
No substitute for exact GTO raw results, and no generic texture extrapolation.
"""
import argparse,gzip,hashlib,json,pathlib,sys
MODEL="ln-bb-r_model-16s8tm3"
FLOP,TURN="9s6h3d","Ts"
SPOT="BTN_BB"
TARGET_LINE="x x/b75 c/"
TARGET_SPR=6.791
GTO_PIN="abe310c3aad02dd4a7c77fb2831801fd490cf51b"
RUST_PIN="9d1509fe5077d019825f833eed04b16d342dfda1"

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def load(path):return json.loads(path.read_text())
def locate(root,rel):
    candidates=[root/rel,root/"trainer"/rel]
    matches=[x for x in candidates if x.is_file()]
    if len(matches)!=1:raise ValueError("Expected one exact source: "+str(candidates))
    return matches[0]
def run_sources(download,ver,flop=FLOP,turn=TURN):
    root=download/ver
    mf=locate(root,f"evidence/BTN_BB-{flop}-{ver}.json")
    base="solver/postflop/out/BTN_BB/"+ver
    fp=locate(root,base+f"/{flop}_multiboard.json")
    fj=locate(root,base+f"/{flop}_multiboard.job.json")
    m=load(mf)
    assert (m["schema"],m["spot"],m["version"],m["flop"])==(
        "NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1",SPOT,ver,flop)
    assert m["flop_size_profile"]=="full" and not m["restricted_tree_assumption"]
    assert m["flop_line_policy"]=="checkcheck" and m["selected_lines"]==["x x"]
    assert m["turn_sizing_mode"]=="river-gaps" and "b75 c" in m["selected_turn_lines"]
    assert m["turns"]==[turn] and m["solved_cases"]==1 and not m["failures"] and not m["skipped"]
    assert m["file_flop_sha256"]==sha(fp)
    assert m["preflop_ranges"]["source"]=="PINNED_POKER_SOLVER_PREFLOP_CFR"
    assert m["root_pot_bb"]==5.5 and m["root_remaining_bb"]==97.5
    assert m["no_generic_certification"] is True
    c=next(x for x in m["cases"] if (x["line"],x["turn"])==("x x",turn))
    sub=locate(root,base+f"/{flop}_xx_{turn}.json")
    sj=locate(root,base+f"/{flop}_xx_{turn}.job.json")
    assert c["source_sha256"]==sha(sub)
    assert c["gto_gap_pct"] is not None and c["gto_gap_pct"]<=.5
    d,fr,job,subjob=load(sub),load(fp),load(fj),load(sj)
    assert (fr["flop"],fr["pot"],fr["stack"])==(flop,550,9750)
    assert (d["flop"],d["turn"],d["line0"])==(flop,turn,"x x")
    assert d["info"]["gto_expl_pct"]<=.5
    assert (subjob["turn_oop"],subjob["turn_ip"])==("33%,66%,75%","33%,66%,75%")
    assert abs(subjob["rake_rate"]-.05)<1e-8 and subjob["rake_cap"]==1000
    if ver=="gto":
        assert job.get("hero") is None and not job.get("locks")
        assert subjob.get("hero") is None and not subjob.get("locks")
    else:
        assert job.get("hero")==0 and job.get("locks")
        assert subjob.get("hero")==0 and subjob.get("locks")
        assert c["hero_gap_pct"] is not None and c["hero_gap_pct"]<=.5
        assert d["info"]["hero_gap_pct"]<=.5
        assert m.get("locks")
    pins=locate(root,"evidence/poker-solver-commit.txt"),locate(root,"evidence/upstream-engine-commit.txt")
    assert pins[0].read_text().strip()==GTO_PIN
    assert pins[1].read_text().strip()==RUST_PIN
    raw=dict(manifest=m,flop_root=fr,flop_job=job,turn_subgame=d,turn_job=subjob,
             manifest_sha256=sha(mf),root_sha256=sha(fp),
             root_job_sha256=sha(fj),subgame_sha256=sha(sub),turn_job_sha256=sha(sj))
    return raw
def target_nodes(fr,sub,seq):
    out=[]
    for n in sub["nodes"]:
        if n["line"]!=TARGET_LINE or n["player"]!=0 or len(n["board"])!=10:continue
        spr=(sub["stack"]-max(n["bets"]))/n["pot"]
        if abs(spr-TARGET_SPR)/TARGET_SPR>.05:continue
        key="|".join((n["board"],n["line"],str(n["player"])))
        q=seq[key]
        out.append(dict(board=n["board"],line=n["line"],acting_seat=n["player"],
            actual_spr=round(spr,6),strict_combos=q["count"],
            raw_source_actor_combos=sum(float(w)>1e-4 for w in n["w"][0]),
            source_actions=n["acts"],source_node=n,strict_mask=q["mask"]))
    return out
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--downloads",required=True,type=pathlib.Path)
    a.add_argument("--run-id",required=True,type=int)
    args=a.parse_args()
    root=pathlib.Path.cwd(); data=root/"data"
    sys.path.insert(0,str((root/"tools").resolve()))
    from hu_sequential_cfr_reach import game_reach
    from verify_hu_multiboard_100bb import strict_medium_evidence,lock_scope,locked_model_gain
    g=run_sources(args.downloads,"gto")
    e=run_sources(args.downloads,"exp_oop")
    gr,gs=g["flop_root"],g["turn_subgame"]
    er,es=e["flop_root"],e["turn_subgame"]
    gm,gstats=game_reach(gr,gs)
    em,estats=game_reach(er,es)
    gn=target_nodes(gr,gs,gm)
    en=target_nodes(er,es,em)
    glist=[];elist=[]
    for n in gn:
        src=n.pop("source_node");mask=n.pop("strict_mask")
        medium=strict_medium_evidence(src,gs,mask) if n["strict_combos"]>0 else dict(eligible=0,candidate=False,status="UNREACHABLE")
        n["b50_medium_eligible_combos"]=medium["eligible"]
        n["b50_nonpolarized_research_candidate"]=medium["candidate"]
        glist.append(n)
    for n in en:
        n.pop("source_node");n.pop("strict_mask")
        elist.append(n)
    lk=lock_scope(es,e["manifest"]["locks"],"exp_oop")
    assert lk["pattern_matched_nodes"]>0
    assert (g["manifest"]["root_pot_bb"],e["manifest"]["root_pot_bb"])==(5.5,5.5)
    st=load(data/"nl2_hu_multiboard_status_v51_b453_rank32.json")
    assert (st["CERT_MULTIBOARD"],st["APPROX"],st["EST"],st["TOTAL"])==(164,228,0,392)
    model=st["records"][MODEL]
    assert model["label"]=="APPROX" and model["frequency_rank"]==48
    assert model["solver_profile"]==SPOT and model["street"]==2
    assert abs(model["assumed_model_node_spr"]-TARGET_SPR)<1e-6
    positive_gto={n["board"] for n in glist if n["strict_combos"]>0}
    positive_exp={n["board"] for n in elist if n["strict_combos"]>0}
    paired=sorted(positive_gto&positive_exp)
    payload=dict(schema="NL2_B460_R48_BTN_BB_B75_RIVER_FIRST_EXACT_BOARD_V1",
        model_id=MODEL,frequency_rank=48,flop=FLOP,turn=TURN,spot=SPOT,
        target_exact_river_line=TARGET_LINE,target_spr=TARGET_SPR,acting_seat=0,
        verified_original_gto_run_id=args.run_id,verified_exp_oop_run_id=args.run_id,
        original_gto_sha256=g["subgame_sha256"],actual_NL2_OOP_sha256=e["subgame_sha256"],
        root_source_sha256s=dict(gto=g["root_sha256"],exp_oop=e["root_sha256"]),
        original_gto_gap_pct=g["turn_subgame"]["info"]["gto_expl_pct"],
        exp_oop_hero_gap_pct=e["turn_subgame"]["info"]["hero_gap_pct"],
        GTO_nodes=glist,NL2_OOP_nodes=elist,
        original_gto_positive_nodes=len(positive_gto),
        NL2_OOP_positive_nodes=len(positive_exp),
        exact_paired_positive_river_nodes=len(paired),paired_public_boards=paired,
        new_distinct_real_flops=1,
        cannot_certify_without_three_distinct_paired_flops=True,
        original_flop_menu_full=True,turn_menu="33%,66%,75%",
        b75_exact_action_must_exist_not_relabelled=True,
        observed_pool_marginal_lock_nodes=lk["observed_marginal_source_nodes"],
        assumed_pool_lock_nodes=lk["imputed_assumption_nodes"],
        unmatched_unlocked_pool_nodes=lk["unmatched_nodes"],
        no_NL2_private_hand_action_frequencies=True,
        hero_model_gain_bb=locked_model_gain(es,"exp_oop"),
        strict_reach_policy="40PCT_ABSOLUTE_AND_70PCT_OF_MAX_FREQUENCY",
        no_generic_texture_certification=True,
        preserved_baseline=(164,228,0),CERT_MULTIBOARD=164,APPROX=228,EST=0,
        PR2_Draft_NEVER_MERGE=True)
    proof=data/"nl2_hu_b460_rank48_first_exact_b75_evidence.json"
    proof.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
    arc=dict(schema="NL2_B460_R48_AUTHENTIC_GTO_AND_NL2_OOP_SOURCE_V1",
             solver_pin=GTO_PIN,rust_pin=RUST_PIN,gto=g,exp_oop=e)
    raw=json.dumps(arc,ensure_ascii=False,separators=(",",":")).encode()
    gz=data/"solver_evidence/NL2_B460_R48_BTN_BB_9S6H3D_B75.json.gz"
    gz.parent.mkdir(parents=True,exist_ok=True)
    gz.write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))
    index=dict(schema="NL2_B460_R48_SOURCE_INDEX_V1",run_id=args.run_id,
       raw_archive_sha256=sha(gz),proof_sha256=sha(proof),
       GTO_source_sha256=g["subgame_sha256"],NL2_OOP_source_sha256=e["subgame_sha256"],
       positive_paired_river_nodes=len(paired),not_certified_yet=True)
    gz.with_suffix("").with_suffix(".index.json").write_text(json.dumps(index,indent=2)+"\n")
    doc=root/"docs/NL2_HU_B460_R48_FIRST_EXACT_B75.md"
    doc.write_text("# B460 rank48: first authentic BTN_BB x-x / b75-call river board\n\n"
      "Full original 100bb GTO and real NL2-OOP Rust solve from independent jobs; "
      "frozen flop 9s6h3d, turn Ts. Source hashes, actual sizes, 5% rake, "
      "acting seat, strict 40/70 multi-street reach, and partial pool-marginal "
      "locks are checked against raw artifacts. Medium 50% bet evidence, if "
      "eligible, is only a named-board research candidate.\n\n"
      f"Actual positive paired river nodes: {len(paired)}. "
      "One board never proves a 3–5-board CERT; the model stays APPROX. "
      "Counts: 164 CERT / 228 APPROX / 0 EST. PR2 stays Draft.\n")
    print(json.dumps(dict(run=args.run_id,model_rank=48,paired=len(paired),
        gto_nodes=len(glist),exp_nodes=len(elist),cert=164,approx=228,est=0)))
if __name__=="__main__":main()
