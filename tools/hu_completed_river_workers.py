"""Authenticate completed native river workers and replay their negative evidence."""
import argparse
import json
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
from zipfile import ZipFile

from hu_b467_river_source_gate import compact, json_bytes, sha
import hu_b659_rank29_monotone
import hu_b664_rank57_bottom_pair

HEAD="19b59d0dc6342d7f51019d7796bc1e0b2525306c"


def verify(args):
    study = hu_b659_rank29_monotone if args.batch == 659 else hu_b664_rank57_bottom_pair
    run_id,rank = (45271606533,29) if args.batch == 659 else (45271606624,57)
    records=[]
    for flop in study.CASES:
        receipt=json.loads((args.originals/(flop+".json")).read_bytes())
        identity=receipt["workflow_run"]
        assert (identity["id"],identity["head_sha"],identity["repository_id"],receipt["name"]) == (
            run_id,HEAD,1438346845,f"B{args.batch}-R{rank}-"+flop)
        path=args.originals/(flop+".zip")
        assert receipt["digest"]=="sha256:"+sha(path.read_bytes())
        with ZipFile(path) as z, tempfile.TemporaryDirectory() as tmp:
            assert len(z.namelist())==len(set(z.namelist()))
            members={n for n in z.namelist() if not n.endswith("/")}
            assert {"proof.json","flop/job.json","flop/result.json"} <= members
            assert all(re.fullmatch(r"(?:proof.json|flop/(?:job|result).json|[2-9TJQKA][cdhs]-(?:gto|exp_oop)/(?:job|result).json)",n) for n in members)
            folder=Path(tmp)
            for name in members:
                dest=folder/name
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_bytes(z.read(name))
            proof=json.loads((folder/"proof.json").read_bytes())
            study.run(SimpleNamespace(solver=args.solver,flop=flop,output=folder,driver=None))
            assert json.loads((folder/"proof.json").read_bytes())==proof
            positives=[c for t in proof["turns"] for c in t["checks"]]
            assert not positives and all(not t["paired_policies"] for t in proof["turns"])
            expected={"proof.json","flop/job.json","flop/result.json"}
            if args.batch == 659:
                assert proof["eligible_flop_hands"]==0
            else:
                for turn in study.CASES[flop]:
                    expected.update(turn+"-gto/"+file for file in ("job.json","result.json"))
            assert members==expected
            turns={t["turn"]:sha(z.read(t["turn"]+"-gto/result.json")) for t in proof["turns"]} if args.batch==664 else {}
            root=json.loads((folder/"flop/result.json").read_bytes())
            assert 0<=root["info"]["gto_expl_pct"]<=.5
            records.append(dict(flop=flop,artifact_id=receipt["id"],artifact_sha256=sha(path.read_bytes()),
                source_run_id=run_id,source_head=HEAD,root_sha256=sha(compact(root)),
                root_gap_pct=root["info"]["gto_expl_pct"],proof_sha256=sha(z.read("proof.json")),
                original_turn_sources=turns,valid_distinct_flops=0,lock_solves=0,medium_assessments=0,
                checked_turns=[r["turn"] for r in proof["turns"]]))
    result=dict(rank=rank,status="APPROX",worker_run_id=run_id,worker_head=HEAD,
                valid_distinct_flops=0,records=records)
    args.out.write_bytes(json_bytes(result))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--batch",type=int,choices=(659,664),required=True)
    for key in ("solver","originals","out"):
        cli.add_argument("--"+key,type=Path,required=True)
    verify(cli.parse_args())
