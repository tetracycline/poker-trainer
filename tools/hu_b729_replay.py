"""Replay the four immutable B723 Actions archives at the CO river check decision."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import hu_b723_rank115_limp_rivers as native
from hu_b467_river_source_gate import json_bytes, sha
from hu_b710_publish import unpack_original

RUN = 45329019172
HEAD = "b9ec29c2cf989f38631fd1b966470bdfef06953d"
BRANCH = "fix/nl2-hu-lines-audit-20261118"
WORKFLOW = ".github/workflows/nl2-hu-b723-rank115-limp-rivers.yml"
ROUTE = "tools/hu_b718_limp_routes.cjs"
WORKER = "tools/hu_b723_rank115_limp_rivers.py"
PINS = {"7h6d4s":[14891391162,138225387226,"625d03b64625d9d5ae62092ba16674539582d20444eac11e6d628b8172acbab5"],"7h6c4h":[14890867735,138225387609,"7024079625212774430041025b48a2aa7f58cad8c71ce03592ae355a053be077"],"7h6h4c":[14890364090,138225387641,"74bce94fd8a6d9e6900366161d7560ee484a09c9fd8d1f8ec4abd52a1525ce1d"],"7s5h3d":[14890034768,138225387565,"7631013dbd1a85859a1a0bf1485c2fa167d10f3ed5b9d457338273d98e3f4a4f"]}
BLOBS = {WORKER:"2d7b33a5386abcbed329e68a4a681054ad646693", WORKFLOW:"9c781b3122f7d2d643b28a4918cfb561d1d82ad3", ROUTE:"7091b40ce80d8273752e4ea2b0b0c6ab98df9c0f",
    "tools/hu_b637_rank57.py":"86b795adbd8ff4e6e411a70cebf8b3db1efc4ff9","tools/hu_checked_gto_boundary.py":"219f46b0a259fa3e71f1225046ab5b12c44c28c6",
    "tools/hu_b483_locked_medium.py":"018ac485d3fc115f125c777399d96ce38b0f5f04","tools/hu_sequential_cfr_reach.py":"f26df926c088e5b4117bb911956cbc5031e2458d",
    "tools/hu_b568_caller_rivers.py":"e69bda7fe46c3dd18a48dee1bb97f965ab2813f7","tools/hu_b470_rank73_new_rivers.py":"39336981ae910b385744a2b0aaea237397babb38"}
STEPS = {"Authenticate saved flop strategy, both ranges and exact CO route","Build pinned Rust driver","Solve missing continuation and replay original strategies","Run actions/upload-artifact@v4"}


def authenticate(receipts):
    run = receipts["run"]
    attempt = run["run_attempt"]
    assert (run["id"],run["head_sha"],run["head_branch"],run["path"],run["status"],run["conclusion"]) == (RUN,HEAD,BRANCH,WORKFLOW,"completed","success")
    assert run["repository"] == {"id":1438346845,"full_name":"tetracycline/poker-trainer"}
    assert len(receipts["jobs"]) == len(receipts["artifacts"]) == len(PINS) == 4
    for flop,(aid,jid,digest) in PINS.items():
        job, = [j for j in receipts["jobs"] if j["id"]==jid]
        assert (job["run_id"],job["head_sha"],job["run_attempt"],job["name"],job["status"],job["conclusion"]) == (RUN,HEAD,attempt,f"solve ({flop})","completed","success")
        assert STEPS <= {s["name"] for s in job["steps"] if s["conclusion"]=="success" and s["status"]=="completed"}
        artifact, = [a for a in receipts["artifacts"] if a["id"] == aid]
        assert (artifact["name"],artifact["digest"],artifact["expired"]) == ("B723-R115-"+flop,"sha256:"+digest,False)
        w=artifact["workflow_run"]
        assert (w["id"],w["head_sha"],w["head_branch"],w["head_repository_id"],w["repository_id"]) == (RUN,HEAD,BRANCH,1438346845,1438346845)


def ancestor_counts(folder,flop,report,routes):
    from hu_sequential_cfr_reach import accepted, cardkey
    from hu_b568_caller_rivers import hand_cell
    root,_,_=native.load_root(flop)
    turn=json.loads((folder/"gto/result.json").read_bytes())
    public=next(iter(report["gto"]))[:8]
    root_nodes={n["line"]:n for n in root["nodes"] if n["board"]==public[:6]}
    turn_nodes={n["line"]:n for n in turn["nodes"] if n["board"]==public}
    parent,=[n for n in root["nodes"] if n["line"]=="b50 c/" and n["board"]==public]
    weights=[{cardkey(h) for h,w in zip(root["hands"][seat],parent["wr"][seat],strict=True) if w>1e-4} for seat in (0,1)]
    bb=accepted(root_nodes[""],root["hands"],"b50") & weights[0]
    co=accepted(root_nodes["b50"],root["hands"],"c") & weights[1]
    bbcheck=bb & accepted(turn_nodes["b50 c/"],turn["hands"],"x")
    bbcall=bbcheck & accepted(turn_nodes["b50 c/x b33"],turn["hands"],"c")
    cobet=co & accepted(turn_nodes["b50 c/x"],turn["hands"],"b33")
    visible={h for h in cobet if hand_cell("".join(h),public[:6])[0] in routes["flop"] and hand_cell("".join(h),public)[0] in routes["turn"]}
    assert not bbcall and visible
    return dict(bb_flop_b50=len(bb),bb_flop_b50_turn_x=len(bbcheck),bb_flop_b50_turn_x_then_call=len(bbcall),
                co_flop_call=len(co),co_flop_call_turn_b33=len(cobet),co_b33_with_displayed_flop_and_turn=len(visible))


def replay_one(solver, raw, temporary, routes, flop, pin):
    aid,jid,digest=pin
    assert sha(raw)==digest
    folder=temporary/flop
    folder.mkdir()
    files=unpack_original(raw,folder)
    original=(folder/"proof.json").read_bytes()
    report=json.loads(original)
    assert (report["rank"],report["model"],report["actor"],report["line"],report["run"],report["head"],report["flop"])==(115,native.MID,1,native.LINE,RUN,HEAD,flop)
    assert (folder/"rendered-routes.json").read_bytes()==routes
    expected={"proof.json","rendered-routes.json","gto/job.json","gto/result.json"}
    if report["actor_locked"]:
        expected |= {"exp_ip/job.json","exp_ip/result.json"}
    assert files == expected
    native.run(SimpleNamespace(solver=solver,output=folder,driver=None,flop=flop,routes=folder/"rendered-routes.json",head=HEAD,run=RUN,preflight=False))
    assert original == (folder/"proof.json").read_bytes()
    source={"flop":flop,"turn":report["turn"],"source_job":jid,"artifact_id":aid,"archive_sha256":digest,"original_root":report["source"],
        "gto_source":report["gto_source"],"nl2_source":report["nl2_source"],"proof_sha256":sha(original),"actor_locked":report["actor_locked"],
        "gto_and_lock_common":{b:h for b,h in report["common"].items() if h},"nodes":{}}
    for board,gto in sorted(report["gto"].items()):
        variants={"gto":gto}
        if report["actor_locked"]:
            variants["exp_ip"] = report["nl2"][board]
            common = sorted(set(gto["displayed_hands"]) & set(variants["exp_ip"]["displayed_hands"]))
            assert report["common"][board] == common
        observed={}
        for v,record in variants.items():
            o=record["reach"];medium=o["b50"];nh=o["strict_legal_combos"]
            assert (o["public_board"],o["acting_seat"],o["line"])==(board,1,native.LINE)
            assert o["compatible_hole_card_pairs"]>=nh>=len(record["displayed_hands"])
            assert (medium is not None)==(nh>0) and all(h for h in record["displayed_hands"])
            observed[v]=dict(joint_hero=nh,compatible_pairs=o["compatible_hole_card_pairs"],displayed=record["displayed_hands"],
                             medium_assessed=medium is not None,b50_eligible=medium["eligible"] if medium else None,
                             nonpolarized_candidate=medium["candidate"] if medium else None)
        source["nodes"][board]=observed
    assert bool(source["gto_and_lock_common"])==bool(report["positive_flops"])
    source["gto_ancestor_counts"]=ancestor_counts(folder,flop,report,json.loads(routes)["115"])
    return source


def main(args):
    assert sys.version_info[:2] == (3,11)
    for path,expected in BLOBS.items():
        assert subprocess.check_output(["git","hash-object",path],text=True).strip()==expected,path
    routes=subprocess.check_output(["node",ROUTE])
    receipts=json.loads(args.receipts.read_bytes());authenticate(receipts)
    output=args.output.resolve()
    assert not output.exists() and Path("data").resolve() not in (output,*output.parents)
    evidence=output/"solver_evidence";evidence.mkdir(parents=True)
    results=[]
    with TemporaryDirectory(prefix="b729-") as tmp:
        for flop,pin in sorted(PINS.items()):
            name="NL2_B723_R115_"+flop.upper()+".zip"
            path=args.archives/(str(pin[0])+".zip")
            raw=(path if path.is_file() else args.archives/name).read_bytes()
            source=replay_one(args.solver,raw,Path(tmp),routes,flop,pin)
            (evidence/name).write_bytes(raw);source["archive"]=name;results.append(source)
    all_boards=[(b,node) for r in results for b,node in r["nodes"].items()]
    assert len(all_boards)==len({b for b,n in all_boards})==34
    counts=Counter()
    for _,node in all_boards:
        for v,d in node.items():
            counts[v+"_public_boards"]+=1
            counts[v+"_joint_positive"]+=int(d["joint_hero"]>0)
            counts[v+"_displayed_positive"]+=int(bool(d["displayed"]))
            counts[v+"_medium_assessed"]+=int(d["medium_assessed"])
            counts[v+"_nonpolarized_candidates"]+=int(bool(d["nonpolarized_candidate"]))
    assert counts["gto_joint_positive"]==0 and counts["exp_ip_public_boards"]==0
    positive=[r["flop"] for r in results if r["gto_and_lock_common"]]
    totals=dict(positive_distinct_flops=positive,cert_eligible_ranks=[115] if len(positive)>=3 else [],
                source_run=RUN,source_head=HEAD,rank=115,model=native.MID,source_flops=4,frozen_flop_native_solves_repeated=0,
                actor_locked_turn_subgames=sum(r["actor_locked"] for r in results),actor_locked_public_boards=counts["exp_ip_public_boards"],
                medium_assessed_public_boards=counts["exp_ip_medium_assessed"],locked_nonpolarized_candidates=counts["exp_ip_nonpolarized_candidates"],
                observations=counts)
    (output/"nl2_hu_b729_summary.json").write_bytes(json_bytes(dict(schema="NL2_HU_B729_RANK115_NAMED_RIVER_SOURCE_REPLAY_V1",**totals,workers=results)))
    (output/"nl2_hu_b729_source_receipts.json").write_bytes(json_bytes(receipts))
    print(json.dumps(totals))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archives",type=Path,default=Path("data/solver_evidence"))
    p.add_argument("--receipts",type=Path,default=Path("data/nl2_hu_b729_source_receipts.json"))
    for name in ("output","solver"):p.add_argument("--"+name,type=Path,required=True)
    main(p.parse_args())
