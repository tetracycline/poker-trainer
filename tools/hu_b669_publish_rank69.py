"""Publish rank69 only after three independently authenticated rendered flop witnesses."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import hu_b655_rank69_checks as study
from hu_b655_publish_rank69 import verify, RUN as PRIOR_RUN, HEAD as PRIOR_HEAD
from hu_b669_rank69_checks import CASES
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b483_locked_medium import POOL
from hu_b514_turn_stab import rates
from hu_b550_rank69_originals import LINE, MID
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_board_reach_corrections import source_key
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solver", type=Path, required=True)
    parser.add_argument("--receipts", type=Path, required=True)
    parser.add_argument("--run", type=int, required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()
    assert args.run > 0
    assert subprocess.check_output(["git","-C",args.solver,"rev-parse","HEAD"],text=True).strip() == study.SOLVER
    pool_bytes = (args.solver/"inputs/pool_stats.json").read_bytes()
    assert sha(pool_bytes) == POOL
    pool = json.loads(pool_bytes)["NL2"]
    sys.path.insert(0,str((args.solver/"postflop/py").resolve()))
    import pipeline
    route = json.loads(subprocess.check_output(["node","tools/hu_b550_rank69_routes.cjs"]))
    study.CASES = dict(study.CASES, **CASES)
    data = Path("data")
    model = json.loads((data/"nl2_hu_multiboard_status_current.json").read_bytes())["records"][MID]
    receipts = []
    for path in args.receipts.glob("*.json"):
        receipt = json.loads(path.read_bytes())
        name = receipt.get("name", "")
        if name == "B655-R69-Th7h5c" or name.startswith("B669-R69-"):
            receipts.append(receipt)
    order = ["Th7h5c", *CASES]
    names = {r["name"] for r in receipts}
    expected = {"B655-R69-Th7h5c", *("B669-R69-"+f for f in CASES)}
    assert names <= expected and "B655-R69-Th7h5c" in names and len(names) == len(receipts)
    receipts.sort(key=lambda r:order.index(r["name"].split("-")[-1]))
    group = dict(rank=69,model_id=MID,boards=[],pins=[])
    medium = dict(schema="NL2_HU_B669_ORIGINAL_LOCKED_MEDIUM_V1",gto_references={},references={})
    attempts = []
    for receipt in receipts:
        name = receipt["name"]
        prior = name.startswith("B655-")
        run,head,batch = (PRIOR_RUN,PRIOR_HEAD,"B655") if prior else (args.run,args.head,"B669")
        workflow = receipt["workflow_run"]
        assert (workflow["repository_id"],workflow["id"],workflow["head_sha"]) == (1438346845,run,head)
        archive = args.receipts / f'{receipt["id"]}.zip'
        raw = archive.read_bytes()
        assert receipt["digest"] == "sha256:" + sha(raw)
        with ZipFile(archive) as z:
            claim = json.loads(z.read("proof.json"))
            flop = claim["flop"]
            assert claim["rank"] == 69 and claim["model_id"] == MID
            assert json.loads(z.read("flop/job.json")) == study.root_job(flop)
            root_raw = z.read("flop/result.json")
            assert sha(root_raw) == claim["root_sha256"]
            root = json.loads(root_raw)
            assert 0 <= root["info"]["gto_expl_pct"] <= .5 and not root["info"].get("lock_stats")
        positive = any(t["rivers"] for t in claim["turns"])
        attempts.append(dict(flop=flop,artifact_id=receipt["id"],artifact_sha256=sha(raw),
                             run=run,head=head,positive_rendered_witness=positive))
        if not positive:
            continue
        flop,public,code,raw,pair,rows,common = verify(archive,receipt,pipeline,pool,route,run,head,batch)
        if len(group["boards"]) == 5:
            continue
        source = data/"solver_evidence"
        (source/("NL2_"+code+".zip")).write_bytes(raw)
        board,pin = emit_board(model,pair["gto"],pair["exp_ip"],public,LINE,texture(flop),viewer_code=code)
        assert board and pin
        board.update(origin_solve_run_id=run,source_run_role="ORIGINAL_GITHUB_ACTIONS_NATIVE_SOLVE",
                     restricted_flop_bet_sizes_pct=[33],flop_sizing_assumption="One-third-pot flop menu for both positions")
        board["nl2_locked_variants"][0].update(
            variant_label="原始翻牌真解，轉河牌按 NL2 分街頻率鎖定 BB 回應",
            applied_street_rates=rates(pair["exp_ip"]),measurement_policy="STREET_SPECIFIC_POOL_MARGINALS",pool_sha256=POOL)
        pin.update(shared_rendered_checks=common,worker_artifact_id=receipt["id"],
                   worker_artifact_sha256=sha(raw),worker_head_sha=head)
        group["boards"].append(board)
        group["pins"].append(pin)
        for version,field in (("gto","gto_references"),("exp_ip","references")):
            medium[field][source_key(MID,rows[version])] = rows[version]
    assert len({suit_isomorphism_class(b["flop"]) for b in group["boards"]}) == len(group["boards"])
    report = dict(run=args.run,head=args.head,attempts=attempts,missing_worker_artifacts=sorted(expected-names),distinct_rendered_flops=len(group["boards"]))
    (data/"nl2_hu_b669_rank69_results.json").write_bytes(json_bytes(report))
    if len(group["boards"]) < 3:
        (data/"nl2_hu_b669_rank69_partial.json").write_bytes(json_bytes(dict(group=group,observations=medium)))
    else:
        (data/"solver_evidence/reverified/rank69.json").write_bytes(json_bytes(group))
        (data/"nl2_hu_b669_locked_medium.json").write_bytes(json_bytes(medium))
    print(len(group["boards"]),"independently replayed rendered flops")


if __name__ == "__main__":
    main()
