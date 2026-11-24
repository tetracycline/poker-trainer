"""Independently replay B684 rank103 native policies and stage named-board evidence only."""
import argparse
import base64
from copy import deepcopy
import io
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import hu_reverified_board_pair as pairs
from hu_b463_rank45_gate import SOLVER,RUST
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE,POOL,RANGES,proof
from hu_b514_turn_stab import rates
from hu_b536_sb_barrels import tx
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import prepare_job
from hu_multiboard_promote import texture
from hu_sequential_cfr_reach import accepted,cardkey,game_reach
from hu_trainer_route_gate import compatible
from hu_b687_collect import RUN,HEAD,FLOPS,authenticate,validate_run,validate_preflight
from verify_hu_multiboard_100bb import lock_scope

sys.path.insert(0,str(Path(__file__).resolve().parent/"lines_pipeline"))
from run10_common import hcls

MODEL="ln-3bp-3c_t_model-owdwy"
LINE="b33 c/x"
CASES={"Qs8h4d":["2c","5s","Tc","Ah"],"Jh8d3c":["2h","5s","9c","Qs"],"9c6c3h":["2d","4s","8d","Td"]}
CODE_PINS={"nl2_hu_model.js":"a98cb80d7762b464064874de39dcff6f4bf5707d",
           "nl2.js":"15aee97e53a156fe073c96a120638a8a3679958f"}
ACTIONS={"過":"x","下注 ⅓":"b33","下注 ½":"b50","下注 ¾":"b75"}


def replay_flop_route(root,turn,route):
    """Rebuild both native flop policies, turn blockers and playable UI classes."""
    opener,=(n for n in root["nodes"] if n["line"]=="")
    response,=(n for n in root["nodes"] if n["line"]=="b33")
    boundary,=(n for n in root["nodes"] if n["line"]=="b33 c/" and n["board"].endswith(turn))
    assert (boundary["player"],boundary["pot"],boundary["bets"])==(0,3404,[677,677])
    public=boundary["board"];cards={public[i:i+2] for i in range(0,len(public),2)}
    assert len(public)==8 and len(cards)==4
    assert cards-{turn}=={root["flop"][i:i+2] for i in (0,2,4)}
    alive=[{cardkey(h) for h,w in zip(root["hands"][s],boundary["wr"][s],strict=True)
            if w>1e-4 and cards.isdisjoint(cardkey(h))} for s in (0,1)]
    bet=accepted(opener,root["hands"],"b33");call=accepted(response,root["hands"],"c")
    villains=bet&alive[0];heroes=call&alive[1]
    parent_cells=route["routes"].get(tx(public[:6]),{}).get("parents",[])
    turn_cells=route["routes"].get(tx(public),{}).get("decisions",{})
    displayed={h for h in heroes if hcls("".join(h),public[:6]) in parent_cells
               and hcls("".join(h),public) in turn_cells}
    common=sorted("".join(h) for h in displayed if any(set(h).isdisjoint(v) for v in villains))
    return common,dict(public_board=public,root_oop_b33_accepted=len(bet),root_ip_call_accepted=len(call),
        legal_turn_villains=len(villains),legal_turn_heroes=len(heroes),displayed_parent_heroes=len(displayed),
        compatible_displayed_parent_heroes=len(common),root_turn_boundary_sha256=sha(compact(boundary)))


def expected_root(flop,pipeline):
    job=pipeline.make_job("BB3_BTN","gto",flop,"result.json",iters=2100,target=.45,compress=True)
    job.update(flop_oop="33%,50%,75%",flop_ip="33%,50%,75%",extract=[dict(prefix=[],street=True)]+[
        dict(prefix=["b33","c",t],street=False,raw=True) for t in CASES[flop]])
    return job


def expected_turn(root,turn,pipeline):
    parent,=(n for n in root["nodes"] if n["line"]=="b33 c/" and n["board"].endswith(turn))
    assert (parent["player"],parent["pot"],parent["bets"])==(0,3404,[677,677])
    job=pipeline.make_job("BB3_BTN","gto",root["flop"],"result.json",iters=2200,target=.4,rank=.4,compress=False)
    job.update(pipeline.SUB)
    job.update(oop="",ip="",pot=3404,stack=8323,turn=turn,line0=["b33","c","/"],root_no_bet=False,
        turn_oop="33%,50%,75%,100%",turn_ip="33%,50%,75%,100%",
        river_oop="50%,75%,100%,a",river_ip="50%,75%,100%,a",extract=[dict(prefix=[],street=True)])
    for seat,key in enumerate(("oop_w","ip_w")):
        job[key]=[[h,w] for h,w in zip(root["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4]
    return job


def observation(source,route):
    root,sub=source["root"],source["subgame"]
    node,=(n for n in sub["nodes"] if (n["line"],n["player"])==(LINE,1))
    assert (node["pot"],node["bets"])==(3404,[0,0])
    assert abs(8323/3404/route["spr"]-1)<.001
    row=proof(root,sub,node,game_reach(root,sub)[0])
    info=sub["info"]
    row.update(version=source["version"],spot="BB3_BTN",family="3BP",flop=sub["flop"],turn=sub["turn"],
        source_run_id=source["run"],source_sha256=source["source_sha256"],archive_sha256=source["archive_sha256"],
        root_sha256=source["root_sha256"],root_gto_stage_gap_pct=root["info"]["gto_expl_pct"],root_locked_hero_gap_pct=None,
        gto_gap_pct=info["gto_expl_pct"],locked_hero_gap_pct=info.get("hero_gap_pct"),
        lock_scope=lock_scope(sub,source["manifest"]["locks"],source["version"]),root_applied_rust_lock_nodes=0,
        subgame_applied_rust_lock_nodes=sum(v["nodes"] for v in info.get("lock_stats",{}).values()))
    public=node["board"]
    assert len(public)==8 and public[-2:]==sub["turn"]
    assert {public[i:i+2] for i in (0,2,4)}=={root["flop"][i:i+2] for i in (0,2,4)}
    parents=route["routes"].get(tx(public[:6]),{}).get("parents",[])
    decisions=route["routes"].get(tx(public),{}).get("decisions",{})
    masks=base64.b64decode(row["compatible_action_mask_b64"],validate=True)
    hands={}
    for i,(hand,bits) in enumerate(zip(sub["hands"][1],masks,strict=True)):
        if not bits:continue
        fc,tc=hcls(hand,public[:6]),hcls(hand,public)
        label=decisions.get(tc);action=ACTIONS.get(label)
        if fc not in parents or action not in node["acts"] or not bits&(1<<node["acts"].index(action)):continue
        frequencies=[max(0,node["strat"][k*len(masks)+i]) for k in range(len(node["acts"]))]
        total=sum(frequencies);assert total>0
        hands["".join(cardkey(hand))]=dict(flop_class=fc,turn_class=tc,displayed_suggestion=label,
            action_order=node["acts"],accepted_mask=bits,
            accepted_actions=[a for k,a in enumerate(node["acts"]) if bits&(1<<k)],
            strategy={a:round(v/total,7) for a,v in zip(node["acts"],frequencies,strict=True)})
    return row,hands


def verify_worker(pin,outer,pipeline,ranges,pool,route):
    with ZipFile(io.BytesIO(outer)) as z:
        assert len(z.namelist())==len(set(z.namelist()))
        claim=json.loads(z.read("proof.json"));flop=pin["flop"]
        assert (claim["schema"],claim["rank"],claim["model_id"],claim["flop"],claim["line"],claim["actor"])==(
            "NL2_B684_R103_ORIGINAL_WORKER_V1",103,MODEL,flop,LINE,1)
        assert (claim["solver"],claim["rust"],claim["pool_sha256"],claim["pot"],claim["stack"])==(SOLVER,RUST,POOL,3404,8323)
        assert (claim["pipeline_sha256"],claim["ranges_sha256"],claim["preflop_source"],claim["lock_scope"])==(
            PIPELINE,RANGES,"PINNED_POKER_SOLVER_PREFLOP_CFR","FROZEN_GTO_FLOP_TURN_RIVER_LOCK_ONLY")
        assert claim["route_sha256"]==sha(compact(route))
        assert claim["not_a_certification"] and claim["no_observed_per_hole_card_NL2_frequencies"]
        assert claim["restricted_flop_oop_sizes_pct"]==[33,50,75] and claim["restricted_flop_ip_sizes_pct"]==[33,50,75]
        raw=z.read("flop/result.json");root=json.loads(raw);job=expected_root(flop,pipeline)
        assert json.loads(z.read("flop/job.json"))==job
        assert claim["root_sha256"]==sha(raw) and claim["root_job_sha256"]==sha(compact(job))
        assert (root["flop"],root["pot"],root["stack"])==(flop,2050,9000)
        assert (job["oop"],job["ip"])==tuple(ranges.to_str(w) for w in ranges.ranges("BB3_BTN","gto"))
        assert not job.get("locks") and job.get("hero") is None
        assert (job["rake_rate"],job["rake_cap"])==(.05,1000)
        assert not root["info"].get("lock_stats") and 0<=root["info"]["gto_expl_pct"]<=.5
        for line,seat,pot,bets,action in [("",0,2050,[0,0],"b33"),("b33",1,2727,[677,0],"c")]:
            n,=(n for n in root["nodes"] if n["line"]==line)
            assert (n["player"],n["pot"],n["bets"])==(seat,pot,bets) and action in n["acts"]
        root_sha=sha(compact(root));archive_code="B687_R103_"+flop.upper()
        common_base=dict(root=root,run=pin["run"],root_sha256=root_sha,archive_code=archive_code,
            archive_sha256=sha(outer),manifest=dict(spot="BB3_BTN",pot_family="3BP",locks=[],
                preflop_ranges=dict(source="PINNED_POKER_SOLVER_PREFLOP_CFR",spot="BB3_BTN")))
        files={"flop/result.json","flop/job.json","proof.json"}
        tested=claim["turns"]
        assert tested and [r["turn"] for r in tested]==CASES[flop][:len(tested)]
        result=None;summary=[]
        for index,test in enumerate(tested):
            turn=test["turn"];parent_hands,parent_report=replay_flop_route(root,turn,route)
            assert test["flop_route_hands"]==len(parent_hands)
            if not parent_hands:
                assert test==dict(turn=turn,flop_route_hands=0,stage="FLOP_ROUTE_REJECTED",
                    gto_rendered_hands=0,paired=False,shared_hands=[])
                summary.append(dict(turn=turn,stage="FLOP_ROUTE_REJECTED",flop_route=parent_report,
                    gto_rendered=0,locked=False,shared=0,root_sha256=sha(raw)))
                continue
            assert "stage" not in test
            gjob=expected_turn(root,turn,pipeline)
            files.update((turn+"-gto/result.json",turn+"-gto/job.json"))
            grow=z.read(turn+"-gto/result.json");gsub=json.loads(grow)
            assert json.loads(z.read(turn+"-gto/job.json"))==gjob and sha(grow)==test["gto_sha256"]
            assert (gsub["flop"],gsub["pot"],gsub["stack"])==(flop,3404,8323)
            assert not gsub["info"].get("lock_stats") and 0<=gsub["info"]["gto_expl_pct"]<=.5
            gsub.update(line0="b33 c",turn=turn,rivers=[])
            g=dict(common_base,version="gto",subgame=gsub,source_sha256=sha(grow))
            gr,gh=observation(g,route)
            assert (test["public_board"],test["gto_rendered_hands"],test["gto_reach"],test["gto_b50"])==(
                gr["public_board"],len(gh),gr["strict_legal_combos"],gr["b50"])
            if not gh:
                assert not test["paired"] and not test["shared_hands"]
                summary.append(dict(turn=turn,stage="GTO_DISPLAY_REJECTED",flop_route=parent_report,
                    gto_rendered=0,locked=False,shared=0,gto_source_sha256=sha(grow),gto_job_sha256=sha(compact(gjob)),
                    gto_gap_pct=gsub["info"]["gto_expl_pct"],gto_strict_combos=gr["strict_legal_combos"],
                    gto_compatible_pairs=gr["compatible_hole_card_pairs"],gto_observation=gr))
                continue
            ejob,rules=prepare_job(dict(source=g,job=gjob),"exp_ip",pool,pipeline);ejob["out"]="result.json"
            files.update((turn+"-exp_ip/result.json",turn+"-exp_ip/job.json"))
            eraw=z.read(turn+"-exp_ip/result.json");esub=json.loads(eraw)
            assert json.loads(z.read(turn+"-exp_ip/job.json"))==ejob and sha(eraw)==test["nl2_sha256"]
            assert (esub["flop"],esub["pot"],esub["stack"])==(flop,3404,8323)
            assert ejob["hero"]==1 and ejob["locks"] and esub["info"]["lock_stats"]
            assert 0<=esub["info"]["gto_expl_pct"]<=.5 and 0<=esub["info"]["hero_gap_pct"]<=.5
            esub.update(line0="b33 c",turn=turn,rivers=[])
            manifest=dict(common_base["manifest"],locks=rules,gto_parent_source_run_id=pin["run"],gto_parent_source_sha256=root_sha)
            applied=audit_patterns(esub,ejob,manifest,pool,1)
            assert any(n>0 for pat,n in applied["driver_tree_nodes"].items() if pat in applied["marginal_targets"])
            e=dict(common_base,manifest=manifest,version="exp_ip",subgame=esub,source_sha256=sha(eraw),
                verified_gto_parent=dict(run=pin["run"],sha256=root_sha),
                measured_lock_application=applied,applied_rust_rates=esub["info"]["lock_stats"])
            er,eh=observation(e,route);common=sorted(gh.keys()&eh.keys())
            assert test["paired"] and test["shared_hands"]==common and test["measured_lock_application"]==applied
            assert (test["nl2_rendered_hands"],test["nl2_reach"],test["nl2_b50"])==(len(eh),er["strict_legal_combos"],er["b50"])
            for label,actual in (("gto_witnesses",gh),("nl2_witnesses",eh)):
                expected={h:{k:actual[h][k] for k in ("flop_class","turn_class","displayed_suggestion","accepted_actions")} for h in common}
                assert test[label]==expected
            summary.append(dict(turn=turn,stage="POSITIVE" if common else "NL2_DISPLAY_REJECTED" if not eh else "NO_COMMON_DISPLAYED_HANDS",
                flop_route=parent_report,gto_rendered=len(gh),nl2_rendered=len(eh),locked=True,shared=len(common),
                gto_source_sha256=sha(grow),nl2_source_sha256=sha(eraw),gto_job_sha256=sha(compact(gjob)),nl2_job_sha256=sha(compact(ejob)),
                gto_gap_pct=gsub["info"]["gto_expl_pct"],hero_gap_pct=esub["info"]["hero_gap_pct"],
                gto_observation=gr,nl2_observation=er,measured_lock_application=applied,applied_street_rates=rates(e)))
            if common:
                assert index==len(tested)-1
                result=(g,e,gr,er,gh,eh,common)
        assert claim["positive_distinct_flops"]==int(result is not None)
        assert result is not None or len(tested)==len(CASES[flop])
        assert {n for n in z.namelist() if not n.endswith("/") }==files
        return result,summary


def publish(args):
    assert (args.run,args.head)==(RUN,HEAD)
    assert args.output.resolve()!=Path.cwd().resolve(),"Use an isolated publication directory"
    assert not (args.output/"data").exists(),"Use a fresh output directory to exclude stale publications"
    for name,pin in CODE_PINS.items():
        assert subprocess.check_output(["git","hash-object",name],text=True).strip()==pin,(name,"price patch not active")
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==SOLVER
    py=solver/"postflop/py";assert sha((py/"pipeline.py").read_bytes())==PIPELINE and sha((py/"ranges.py").read_bytes())==RANGES
    sys.path.insert(0,str(py));import pipeline,ranges
    assert ranges.SPOTS["BB3_BTN"]==dict(oop="BB",ip="BTN",oopc=[("BTNopen>BB","3bet")],
        ipc=[("BTNrfi","open"),("BTNopen>BB3b","call")],pot=20.5,stack=90.0,pfr="oop",kind="3BP")
    pool_raw=(solver/"inputs/pool_stats.json").read_bytes();assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)["NL2"]
    route=json.loads(subprocess.check_output(["node","tools/hu_b684_rank103_routes.cjs"]))
    model=deepcopy(json.loads(Path("data/nl2_hu_multiboard_status_current.json").read_bytes())["records"][MODEL])
    assert (model["frequency_rank"],model["solver_profile"],model["family"],model["street"])==(103,"BB3_BTN","3BP",1)
    assert model["label"]=="APPROX"
    assert (model["source_model_id"],model["abstract_action_history"],model["assumed_model_node_spr"])==(
        route["source"],route["history"],route["spr"])
    contract=json.loads(Path("data/nl2_hu_verified_extensions.json").read_bytes())["trainer_route_contract"]["routes"][MODEL]
    assert (contract["seat"],contract["streets"],contract["priced_model_spr"])==(1,["b33 c","x"],route["spr"])
    inputs=json.loads(args.workers.read_bytes())
    assert len(inputs)==3 and {p["flop"] for p in inputs}==set(CASES)
    assert len({p["id"] for p in inputs})==3 and len({suit_isomorphism_class(p["flop"]) for p in inputs})==3
    assert len({p["job"] for p in inputs})==3 and {(p["run"],p["head"]) for p in inputs}=={(RUN,HEAD)}
    run_raw=(args.receipts/"run.json").read_bytes();source_run=json.loads(run_raw);validate_run(source_run)
    jobs_raw=(args.receipts/"jobs.json").read_bytes();jobs_response=json.loads(jobs_raw);jobs=jobs_response["jobs"]
    assert jobs_response["total_count"]==len(jobs)==4
    preflight,=(j for j in jobs if j["name"]=="routes-and-audit");validate_preflight(preflight)
    artifacts_raw=(args.receipts/"artifacts.json").read_bytes();artifacts_response=json.loads(artifacts_raw)
    artifacts=artifacts_response["artifacts"];assert artifacts_response["total_count"]==len(artifacts)==4
    assert {a["name"] for a in artifacts}=={"B684-verified-rank103-routes",*("B684-R103-"+f for f in FLOPS)}
    data=args.output/"data";evidence=data/"solver_evidence";evidence.mkdir(parents=True,exist_ok=True)
    provenance=evidence/"provenance"/"B687";provenance.mkdir(parents=True)
    for name,raw in (("run.json",run_raw),("jobs.json",jobs_raw),("artifacts.json",artifacts_raw)):
        (provenance/name).write_bytes(raw)
    pairs.EVIDENCE=evidence
    group=dict(rank=103,model_id=MODEL,boards=[],pins=[])
    medium=dict(schema="NL2_HU_B687_ORIGINAL_LOCKED_MEDIUM_V1",gto_references={},references={})
    reports=[]
    for pin in sorted(inputs,key=lambda p:list(CASES).index(p["flop"])):
        receipt_raw=(args.receipts/f'{pin["id"]}.json').read_bytes();receipt=json.loads(receipt_raw)
        job_raw=(args.receipts/f'job.{pin["job"]}.json').read_bytes();job=json.loads(job_raw)
        assert (sha(receipt_raw),sha(job_raw),sha(run_raw))==(
            pin["receipt_sha256"],pin["job_receipt_sha256"],pin["workflow_run_receipt_sha256"])
        listed,=(a for a in artifacts if a["id"]==pin["id"])
        assert job==next(j for j in jobs if j["id"]==pin["job"])
        authenticate(source_run,job,listed,pin);authenticate(source_run,job,receipt,pin)
        outer=(args.receipts/f'{pin["id"]}.zip').read_bytes()
        assert receipt["digest"]=="sha256:"+pin["sha256"] and sha(outer)==pin["sha256"]
        (provenance/f'{pin["id"]}.json').write_bytes(receipt_raw)
        (provenance/f'job.{pin["job"]}.json').write_bytes(job_raw)
        verified,attempts=verify_worker(pin,outer,pipeline,ranges,pool,route)
        archive_code="B687_R103_"+pin["flop"].upper()
        (evidence/("NL2_"+archive_code+".zip")).write_bytes(outer)
        report=dict(flop=pin["flop"],worker_id=pin["id"],worker_sha256=pin["sha256"],run=pin["run"],head=pin["head"],attempts=attempts,
                    positive=verified is not None,original_worker_archive_code=archive_code)
        reports.append(report)
        if verified is None:continue
        g,e,gr,er,gh,eh,common=verified;public=gr["public_board"]
        assert compatible(contract,dict(public_board=public,actual_exact_action_line=LINE,acting_seat=1))
        (evidence/("NL2_"+g["archive_code"]+".zip")).write_bytes(outer)
        board,pin2=pairs.emit_board(model,g,e,public,LINE,texture(pin["flop"]),viewer_code=g["archive_code"])
        assert board and pin2["GTO_compatible_hole_card_pairs"]>=pin2["GTO_strict_combos"]>0
        assert pin2["NL2_compatible_hole_card_pairs"]>=pin2["NL2_strict_combos"]>0
        assert pin2["common_legal_hero_combos"]>=len(common)>0
        board.update(source_run_role="ORIGINAL_GITHUB_ACTIONS_NATIVE_SOLVE",origin_solve_run_id=pin["run"],
            restricted_flop_oop_sizes_pct=[33,50,75],restricted_flop_ip_sizes_pct=[33,50,75])
        pin2.update(worker_artifact=pin["id"],worker_sha256=pin["sha256"],worker_head=pin["head"],
            source_run_role=board["source_run_role"],rendered_decision_hands=[
                dict(hand=h,flop_class=gh[h]["flop_class"],turn_class=gh[h]["turn_class"],
                    displayed_suggestion=gh[h]["displayed_suggestion"],gto=gh[h],nl2=eh[h]) for h in common])
        board["nl2_locked_variants"][0].update(pool_sha256=POOL,measurement_policy="STREET_SPECIFIC_POOL_MARGINALS",
            applied_street_rates=rates(e),origin_solve_run_id=pin["run"],source_run_role=board["source_run_role"],
            gto_parent_source_run_id=pin["run"],gto_parent_source_sha256=g["root_sha256"],
            viewer_archive_code=pin2["viewer_archive_code"],viewer_sha256=pin2["viewer_sha256"])
        group["boards"].append(board);group["pins"].append(pin2)
        for key,row in (("gto_references",gr),("references",er)):medium[key][source_key(MODEL,row)]=row
        report.update(public_board=public,shared_hands=len(common),half_pot_candidate=bool((er["b50"] or {}).get("candidate")))
    assert len({suit_isomorphism_class(b["flop"]) for b in group["boards"]})==len(group["boards"])
    destination=evidence/("reverified" if len(group["boards"])>=3 else "partial");destination.mkdir(exist_ok=True)
    (destination/("rank103.json" if len(group["boards"])>=3 else "B687_rank103.json")).write_bytes(json_bytes(group))
    medium_path=data/"nl2_hu_b687_locked_medium.json" if len(group["boards"])>=3 else destination/"B687_locked_medium.json"
    medium_path.write_bytes(json_bytes(medium))
    (data/"nl2_hu_b687_rank103_results.json").write_bytes(json_bytes(reports))
    (data/"nl2_hu_b687_rank103_workers.json").write_bytes(json_bytes(inputs))
    attempts=[a for r in reports for a in r["attempts"]]
    result=dict(schema="NL2_B687_R103_REPLAY_SUMMARY_V1",source_run=RUN,source_head=HEAD,
        source_run_receipt_sha256=sha(run_raw),root_flops=3,planned_turns=sum(map(len,CASES.values())),tested_turns=len(attempts),
        zero_flop_route_turns=sum(a["stage"]=="FLOP_ROUTE_REJECTED" for a in attempts),
        gto_turn_solves=sum("gto_observation" in a for a in attempts),
        gto_displayed_positive_turns=sum(a["gto_rendered"]>0 for a in attempts),
        nl2_locked_boards=sum(a["locked"] for a in attempts),
        nl2_displayed_positive_boards=sum(a.get("nl2_rendered",0)>0 for a in attempts),
        common_displayed_boards=sum(a["shared"]>0 for a in attempts),
        certifiable_distinct_flops=len(group["boards"]),cert_eligible=len(group["boards"])>=3,
        half_pot_assessed_gto_boards=sum("gto_observation" in a for a in attempts),
        half_pot_assessed_locked_boards=sum("nl2_observation" in a for a in attempts),
        half_pot_gto_candidates=sum(bool((a.get("gto_observation",{}).get("b50") or {}).get("candidate")) for a in attempts),
        half_pot_locked_candidates=sum(bool((a.get("nl2_observation",{}).get("b50") or {}).get("candidate")) for a in attempts),
        certified_board_half_pot_candidates=sum(r.get("half_pot_candidate",False) for r in reports),
        no_observed_per_hole_card_NL2_frequencies=True)
    (data/"nl2_hu_b687_rank103_summary.json").write_bytes(json_bytes(result))
    print(json.dumps(result))

if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for field in ("solver","receipts","workers","output"):cli.add_argument("--"+field,type=Path,required=True)
    cli.add_argument("--run",type=int,default=RUN);cli.add_argument("--head",default=HEAD)
    publish(cli.parse_args())
