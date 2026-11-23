"""Solve fresh two-tone BB flop leads using the original 100bb four-size game and ranges."""
import argparse
from pathlib import Path
import json

from hu_b546_rank70_conditional import current_texture
from hu_b613_rank55_barrels import CASES, original, process

FLOPS=("7s6c4c","8h6d5d","8s5h3h","9d7h5h","6s4h2h")
TEMPLATE="7d5c4c"
ARTIFACT=CASES[TEMPLATE][0]


def source_job(originals,flop):
    assert flop in FLOPS
    _, base, _=original(originals,TEMPLATE)
    assert base["flop_oop"]==base["flop_ip"]=="33%,50%,75%,100%"
    assert base["pot"]==550 and base["stack"]==9750 and not base.get("locks")
    assert len({tuple(sorted(f[::2])) for f in (*FLOPS,*CASES)})==len(FLOPS)+len(CASES)
    turns=[a+s for a in "A" for s in "cdhs" if current_texture(flop+a+s)=="A_high"]
    requests=[dict(prefix=[],street=True)]+[dict(prefix=["b50","c",t],street=False,raw=True) for t in turns]
    return dict(base,flop=flop,out="result.json",extract=requests),turns


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ["solver","originals","output"]:
        parser.add_argument("--"+name,type=Path,required=True)
    parser.add_argument("--run",type=int,required=True)
    parser.add_argument("--flop",choices=FLOPS,required=True)
    parser.add_argument("--driver",type=Path)
    args=parser.parse_args(); assert args.run>0
    report=process(args,source_job(args.originals,args.flop),ARTIFACT)
    report["batch"]=624
    report["preflop_template"]=TEMPLATE
    (args.output/"proof.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
