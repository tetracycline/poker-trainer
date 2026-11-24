"""Download only successful, SHA-authenticated B674 rank75 native workers."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

REPO="tetracycline/poker-trainer"
RUN=45307442376
HEAD="c7785b29f9fcfc1124e49689bdd80c3e89066f73"
PATH=".github/workflows/nl2-hu-b674-threebet-call-prices.yml"
FLOPS=("8h6d3c","7d7c3h","As9s4d")


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument("--output",type=Path,required=True)
    args=cli.parse_args();assert os.environ["GITHUB_REPOSITORY"]==REPO
    args.output.mkdir(parents=True,exist_ok=True)
    def get(resource,raw=False):
        # gh strips GitHub Authorization on signed artifact redirects to another host.
        # Authenticate metadata and SHA exactly as before; retry failed reads only.
        for attempt in range(4):
            response=subprocess.run(["gh","api","repos/"+REPO+"/"+resource],
                capture_output=True,timeout=90)
            if response.returncode==0:
                return response.stdout if raw else json.loads(response.stdout)
            if attempt==3:raise RuntimeError(response.stderr.decode(errors="replace")[-800:])
            time.sleep(2*(attempt+1))
    run=get(f"actions/runs/{RUN}")
    assert (run["id"],run["head_sha"],run["head_branch"],run["status"],run["conclusion"],run["path"])==(
        RUN,HEAD,"fix/nl2-hu-lines-audit-20261118","completed","success",PATH)
    artifacts=[];page=1
    while True:
        chunk=get(f"actions/runs/{RUN}/artifacts?per_page=100&page={page}")["artifacts"]
        artifacts.extend(chunk)
        if len(chunk)<100:break
        page+=1
    selected=[]
    for flop in FLOPS:
        artifact,=(a for a in artifacts if a["name"]=="B674-R75-"+flop)
        aid=artifact["id"];receipt=get(f"actions/artifacts/{aid}");wr=receipt["workflow_run"]
        assert not receipt["expired"] and receipt["name"]==artifact["name"] and receipt["digest"]==artifact["digest"]
        assert (wr["repository_id"],wr["id"],wr["head_sha"])==(1438346845,RUN,HEAD)
        raw=get(f"actions/artifacts/{aid}/zip",True);digest=hashlib.sha256(raw).hexdigest()
        assert receipt["digest"]=="sha256:"+digest
        (args.output/f"{aid}.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
        (args.output/f"{aid}.zip").write_bytes(raw)
        selected.append(dict(id=aid,name=receipt["name"],flop=flop,run=RUN,head=HEAD,sha256=digest))
    (args.output/"workers.json").write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(dict(source_run=RUN,source_head=HEAD,workers=len(selected))))

if __name__=="__main__":main()
