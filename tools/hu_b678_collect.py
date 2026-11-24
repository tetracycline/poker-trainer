"""Download only successful, SHA-authenticated B674 rank75 native workers."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import urllib.request

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
        req=urllib.request.Request("https://api.github.com/repos/"+REPO+"/"+resource,headers={
            "Authorization":"Bearer "+os.environ["GH_TOKEN"],"Accept":"application/vnd.github+json",
            "X-GitHub-Api-Version":"2022-11-28","User-Agent":"nl2-b678-original-worker-audit"})
        with urllib.request.urlopen(req,timeout=90) as response:body=response.read()
        return body if raw else json.loads(body)
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
