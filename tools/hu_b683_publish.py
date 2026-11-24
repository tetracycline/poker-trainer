"""Record three authenticated B681 negatives and reference B679's prior partial.

This batch cannot promote a model. It neither recollects nor replays the old
B676 workers and does not emit global medium reports or reverified groups.
"""
import argparse
import contextlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from zipfile import ZipFile

import hu_b681_rank229_extra as worker
from hu_b683_collect import WORKERS, authenticate
from hu_b467_river_source_gate import json_bytes, sha
from hu_b483_locked_medium import PIPELINE, POOL, RANGES

PRIOR={
    "verification_batch":679,
    "partial_path":"data/solver_evidence/partial/rank229.json",
    "partial_group_sha256":"63a2c1dde2044ff39da99504e0c15e30106df4cc9e15bb4e88a62359c7c16021",
    "flop":"Kc9d4h","public_board":"4h9dKc8h3d",
    "source_run_id":45307442313,"worker_artifact":14880754286,
    "archive_sha256":"7220d620cec1b3f43b101bdcb410aaba6867d1cb4918fd7ae8969b03e45abbdf",
    "original_GTO_SHA256":"6a8451ac6e88bd0c94878a233e5e162cfde4adb798007dc98302bba60a8bb552",
    "actual_NL2_SHA256":"9d7d831dcf88a84dff949c970fc35cc779c0eadcf67b6ffc02a8b181e1ddd17f",
}


def replay(args):
    solver=args.solver.resolve()
    assert subprocess.check_output(["git","-C",solver,"rev-parse","HEAD"],text=True).strip()==worker.native.SOLVER
    py=solver/"postflop/py"
    assert sha((py/"pipeline.py").read_bytes())==PIPELINE
    assert sha((py/"ranges.py").read_bytes())==RANGES
    assert sha((solver/"inputs/pool_stats.json").read_bytes())==POOL
    sys.path.insert(0,str(py))
    routes_raw=args.routes.read_bytes();routes=json.loads(routes_raw)
    run=json.loads((args.receipts/"run.json").read_bytes())
    data=args.output/"data";partial=data/"solver_evidence/partial"
    partial.mkdir(parents=True,exist_ok=True)
    old=Path(PRIOR["partial_path"])
    if old.exists():
        group=json.loads(old.read_bytes())
        assert group["rank"]==229 and group["model_id"]==worker.native.MODELS[229]
        pin,=[p for p in group["pins"] if p["public_board"]==PRIOR["public_board"]]
        for key in ("flop","source_run_id","worker_artifact","archive_sha256","original_GTO_SHA256","actual_NL2_SHA256"):
            assert pin[key]==PRIOR[key]
    results=[];receipts=[]
    for pin in WORKERS:
        artifact=json.loads((args.receipts/(str(pin["id"])+".json")).read_bytes())
        job=json.loads((args.receipts/("job."+str(pin["job"])+".json")).read_bytes())
        authenticate(run,job,artifact,pin)
        archive=(args.receipts/(str(pin["id"])+".zip")).read_bytes()
        assert sha(archive)==pin["sha256"]
        receipts.append(dict(pin=pin,artifact=artifact,job=job))
        with TemporaryDirectory(prefix="b683-new-only-") as td:
            folder=Path(td)
            with ZipFile(io.BytesIO(archive)) as z:
                names=[n for n in z.namelist() if not n.endswith("/")]
                assert len(names)==len(set(names))
                for name in names:
                    path=PurePosixPath(name)
                    assert not path.is_absolute() and ".." not in path.parts
                    target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_bytes(z.read(name))
            original_proof=(folder/"proof.json").read_bytes()
            expected=json.loads(original_proof)
            assert json.loads((folder/"rendered-routes.json").read_bytes())==routes
            current=folder/"current-routes.json";current.write_bytes(routes_raw)
            with contextlib.redirect_stdout(io.StringIO()):
                worker.run(SimpleNamespace(solver=solver,flop=pin["flop"],output=folder,routes=current,driver=None))
            assert json.loads((folder/"proof.json").read_bytes())==expected
            assert (expected["batch"],expected["source_algorithm_batch"],expected["target_rank"],expected["flop"])==(
                681,676,229,pin["flop"])
            assert expected["selected"]=={"229":None}
            assert all(not t["paired_policies"] and not any(t["checks"].values()) for t in expected["turns"])
            required={"flop/job.json","flop/result.json","proof.json","rendered-routes.json"}
            for turn in expected["turns"]:
                if turn["legal_rivers"]:
                    required|={turn["turn"]+"-gto/"+name for name in ("job.json","result.json")}
            assert set(names)==required
            proof_name="b683_"+pin["flop"].upper()+"_proof.json"
            (partial/proof_name).write_bytes(original_proof)
            empty_flop=all(t["eligible_by_rank"]["229"]==0 for t in expected["turns"])
            results.append(dict(flop=pin["flop"],status="NEGATIVE",source_run=pin["run"],
                worker_artifact=pin["id"],worker_sha256=pin["sha256"],
                negative_cause="NO_STRICT_FLOP_UI_COMMON_HAND" if empty_flop else "NO_GTO_RIVER_HAND_MATCHES_RENDERED_ROUTE",
                gto_turn_subgames=sum(t["legal_rivers"]>0 for t in expected["turns"]),
                extracted_river_roots=sum(t["legal_rivers"] for t in expected["turns"]),
                proof_path="data/solver_evidence/partial/"+proof_name,proof_sha256=sha(original_proof),
                native_files_sha256={n:sha((folder/n).read_bytes()) for n in sorted(names) if n.endswith(("/job.json","/result.json"))},
                new_actor_locked_boards=0,new_half_pot_assessed=0))
    report=dict(schema="NL2_HU_B683_AUTHENTICATED_RANK229_NEGATIVES_V1",model_id=worker.native.MODELS[229],
        rank=229,previously_verified_partial=PRIOR,previous_source_replayed=False,records=results,
        new_positive_boards=0,new_negative_boards=3,prior_positive_boards=1,total_positive_flops=1,
        certification_eligible=False,live_registry_changed=False,
        new_actor_locked_boards=0,new_half_pot_assessed=0,new_nonpolarized_candidates=0)
    (data/"nl2_hu_b683_rank229_negatives.json").write_bytes(json_bytes(report))
    (partial/"b683_auth_receipt.json").write_bytes(json_bytes(dict(run=run,workers=receipts)))
    assert len(results)==3 and sum(r["gto_turn_subgames"] for r in results)==3
    print(json.dumps(dict(new_positive_boards=0,new_negative_boards=3,prior_positive_boards=1,
        new_actor_locked_boards=0,new_half_pot_assessed=0,certification_eligible=False)))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ("solver","receipts","output","routes"):cli.add_argument("--"+key,type=Path,required=True)
    replay(cli.parse_args())

