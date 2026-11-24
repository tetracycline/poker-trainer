"""Replay B724's additional BB-b33/CO-call flop boundaries for the rank80 CO river."""
import argparse
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile

import hu_b724_rank150_rivers as source
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b671_rank80 import MODEL, LINE, DECK, cards
from hu_b568_caller_rivers import hand_cell
from hu_sequential_cfr_reach import accepted, cardkey

RUN=45329555043
HEAD="7dd111dc5e4d9860a867893e912981c95062349a"
ROUTE="tools/hu_b671_rank80_routes.cjs"
PINS={"8s8h5s":[14892117865,138227163340,"719239bca0a11a71ffb711ad1b5c16714ee0a5bac323b723d927c0a17948bd3b"],"9c9h6c":[14891728442,138227163492,"9410fbd73365fafacf681007f7bb425b747d317ae26a2eea15bee27c2c4df289"],"Ts9s5h":[14891519205,138227163611,"36a1bbfb5b27d78dd7e52787d35a4e7adfda18cbd0595f5150ef8c03a5bd021f"]}
SOURCE_BLOB="854dfd8cc37fb3bcfb7481573a74bb78c3419120"
ROUTE_BLOB="8e21d8d28f3ba5107b733848d6a6776da2d43f62"


def load_source(flop,archives):
    aid,jobid,digest=PINS[flop]
    path=archives/f"{aid}.zip"
    if not path.exists():
        path=archives/("NL2_B724_R150_"+flop.upper()+".zip")
    assert sha(path.read_bytes())==digest
    with ZipFile(path) as z:
        proof=json.loads(z.read("proof.json"))
        job=json.loads(z.read("flop/job.json"))
        root=json.loads(z.read("flop/result.json"))
        manifest=json.loads(z.read("original-manifest.json"))
        assert (proof["flop"],proof["rank"],proof["source_worker_blob"],proof["source_algorithm_blobs"]) == (flop,150,SOURCE_BLOB,source.PINS)
        assert sha(z.read("flop/result.json"))==proof["root_sha256"] and sha(z.read("flop/job.json"))==proof["root_job_sha256"]
        assert (root["flop"],root["pot"],root["stack"])==(flop,250,9900)
        assert (source.limp.TEMPLATE_SHA,sha(Path(source.limp.TEMPLATE).read_bytes()))==(proof["template_archive_sha256"],proof["template_archive_sha256"])
        with ZipFile(source.limp.TEMPLATE) as template:
            orig=json.loads(template.read("original-manifest.json"))
            assert manifest==orig
            template_job=json.loads(template.read("original-flop.job.json"))
            turn_template=json.loads(template.read("original-turn.job.json"))
        turns=[r[0] for r in source.CASES[flop]]
        sizes="33%,50%,75%,100%"
        expected=dict(template_job,flop=flop,flop_oop=sizes,flop_ip=sizes,iters=2400,target_pct=.45,out="result.json",
                      extract=[dict(prefix=[],street=True)]+[dict(prefix=prefix+[t],street=False,raw=True) for prefix in (["x","b33","c"],["b33","c"]) for t in turns])
        assert job==expected and not job.get("locks") and not root["info"].get("lock_stats") and 0<=root["info"]["gto_expl_pct"]<=.5
        source.limp.check_limp_source(dict(manifest=manifest,root_job=job,subgame_job=None))
        return root,turn_template,manifest,dict(run=RUN,head=HEAD,artifact=aid,job=jobid,zip_sha256=digest,root_sha256=proof["root_sha256"],
            root_job_sha256=proof["root_job_sha256"],boundaries=proof["additional_original_b33_call_boundaries"])


def gate(root,turn,route):
    node,=[n for n in root["nodes"] if n["line"]=="b33 c/" and n["board"].endswith(turn)]
    public=node["board"]
    assert cards(public[:6])==cards(root["flop"]) and len(cards(public))==4
    assert (node["player"],node["pot"],node["bets"])==(0,416,[83,83])
    opening,=[n for n in root["nodes"] if n["line"]=="" and n["board"]==public[:6]]
    facing,=[n for n in root["nodes"] if n["line"]=="b33" and n["board"]==public[:6]]
    assert (opening["player"],opening["pot"],opening["bets"])==(0,250,[0,0])
    assert (facing["player"],facing["pot"],facing["bets"])==(1,333,[83,0])
    alive=[{cardkey(h) for h,w in zip(root["hands"][seat],node["wr"][seat],strict=True) if w>1e-4 and cards(public).isdisjoint(cardkey(h))} for seat in (0,1)]
    bb=accepted(opening,root["hands"],"b33") & alive[0]
    co=accepted(facing,root["hands"],"c") & alive[1]
    flop=[h for h in co if hand_cell("".join(h),public[:6])[0] in route["flop"]]
    both=[h for h in sorted(flop) if hand_cell("".join(h),public)[0] in route["turn"] and any(set(h).isdisjoint(v) for v in bb)]
    eligible={}
    for river in DECK:
        if river in cards(public):continue
        for h in both:
            if river in h:continue
            displayed=route["river"].get(hand_cell("".join(h),public+river)[0])
            v=next((v for v in sorted(bb) if river not in v and set(h).isdisjoint(v)),None)
            if displayed and v:
                eligible[river]=dict(co="".join(h),bb="".join(v),displayed=displayed)
                break
    options=list(eligible)
    selected=options if len(options)<=12 else [options[round(i*(len(options)-1)/11)] for i in range(12)]
    info=dict(turn=turn,public=public,boundary_sha256=sha(compact(node)),bb_strict_b33=len(bb),co_strict_call=len(co),flop_ui=len(flop),
              two_seat_turn_ui=len(both),feasible_rivers=len(eligible),river_witnesses={r:eligible[r] for r in selected})
    return node,info


def run(flop,archives,routes):
    root,template,manifest,source_pin=load_source(flop,archives)
    rows=[]
    for turn,_,_ in source.CASES[flop]:
        _,row=gate(root,turn,routes)
        assert row["boundary_sha256"]==source_pin["boundaries"][turn]
        rows.append(row)
    opening,=[n for n in root["nodes"] if n["line"]=="" and len(n["board"])==6]
    index=opening["acts"].index("b33"); nh=len(root["hands"][0]); probabilities=[]
    for i,w in enumerate(opening["w"][0]):
        if w<=1e-4:continue
        freq=[max(0.,float(opening["strat"][a*nh+i])) for a in range(len(opening["acts"]))]
        if sum(freq)>0:probabilities.append(freq[index]/sum(freq))
    return dict(flop=flop,pin=source_pin,root_actions=opening["acts"],bb_initial_accepted_b33=len(accepted(opening,root["hands"],"b33")),
                highest_reached_bb_b33_frequency=max(probabilities),turns=rows,root_only=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archives",type=Path,default=Path("data/solver_evidence"))
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--flop",choices=list(source.CASES))
    a=p.parse_args()
    assert subprocess.check_output(["git","hash-object",ROUTE],text=True).strip()==ROUTE_BLOB
    assert subprocess.check_output(["git","hash-object","tools/hu_b724_rank150_rivers.py"],text=True).strip()==SOURCE_BLOB
    route=json.loads(subprocess.check_output(["node",ROUTE]))
    registry=json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())
    model=registry["records"][MODEL]
    assert (model["frequency_rank"],model["solver_profile"],model["abstract_action_history"])==(80,"LMP_CO_BB","對手下注、你跟|對手過、你過|對手過")
    assert abs(9817/416/model["assumed_model_node_spr"]-1)<.05
    rows=[run(f,a.archives,route) for f in ([a.flop] if a.flop else source.CASES)]
    out=dict(schema="NL2_B732_R80_B724_ORIGINAL_BOUNDARIES_V1",rank=80,model=MODEL,line=LINE,actor=1,source_run=RUN,source_head=HEAD,
             source_workflow=".github/workflows/nl2-hu-b724-rank150-rivers.yml",root_price=[250,9900],turn_river_price=[416,9817],route_sha256=sha(compact(route)),flops=rows,
             preflop_scope="Original assumed LMP 169-class weights. Both solver preflop ranges and reached private hands are checked.",
             reached_turns=sum(bool(v["river_witnesses"]) for w in rows for v in w["turns"]),new_native_subgames=0,original_flops_reused=len(rows),new_actor_locked_public_boards=0,half_pot_assessed_public_boards=0,
             scope="Flop boundary and UI preflight only. River candidates require independent continuation GTO and actor-matched NL2 policies.")
    a.output.write_bytes(json_bytes(out))
    print(json.dumps({w["flop"]:[(v["turn"],v["two_seat_turn_ui"],v["feasible_rivers"]) for v in w["turns"]] for w in rows}))
