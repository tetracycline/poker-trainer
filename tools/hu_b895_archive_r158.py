#!/usr/bin/env python3
"""B895: permanently retain two audited rank158 source families; no native solves or ref update."""
import base64, hashlib, io, json, os, sys, zipfile
from decimal import Decimal
from collections import Counter
from pathlib import Path
from hu_b886_detached_price_candidate import api, git, sha, REPO, BRANCH
BASE="e5ac84d6eb4207aa2b3f7e4b391e19632f7161b9"
REG="data/nl2_hu_multiboard_status_current.json"
WEIGHTS="data/nl2_hu_multiboard_prerank.json"
PREFIX="data/solver_evidence/b895_rank158/"
RUNS={
45853648334:BASE,45853648200:BASE,
45834355813:"908800f2eddec39e31cd64dfd414ef46dfe164a5",45834355794:"908800f2eddec39e31cd64dfd414ef46dfe164a5",
45843986179:"be434c0e0a9b63906823060b09f5987190b007f5",45843986029:"be434c0e0a9b63906823060b09f5987190b007f5",
45815112958:"cceffee7e13448a102a06d42a063c0ee5b6bc9de",45815112802:"cceffee7e13448a102a06d42a063c0ee5b6bc9de",
45833752310:"0e9ff66cbcb33e43bf9496427ec7717675ce5869",45833752230:"0e9ff66cbcb33e43bf9496427ec7717675ce5869"}
ARTS={
"b894-replay.zip":(15135311156,"35e3275397b9b7ba6d4f59874cc5dabbb24e4576af6194ccd24d159f29d73459",45853648334),
"b892-witness.zip":(15124695980,"d6f6aa5ba35807c7affec131d3376f0cb55fc10d6ad74956e65129a8e70d8099",45834355813),
"b889-replay.zip":(15123531822,"2bf200640cfeb6cfa7816ce17c87198451d1066fa6e6a5cfa55d555a0dec577a",45833752310),
"b890-static.zip":(15125015449,"c5cf666d392fa0b33d5a7f2c0e6beb0e331e2d025460ea34db08c6466e562fa6",45833752230),
"b888-gto.zip":(15114867243,"a43e4a0900781a16706c2355501649c521aa4109b6c98db4026df4808e0073d6",45815112958),
"b888-exp_oop.zip":(15115576330,"48193c80ea7af8744c38a773454d6d6db47490a20b34647713afd0b086b291ac",45815112958),
"original-ac8-gto.zip":(14793708366,"f2ed6bb2438d3b7c4fb84d6e3195a5798504e3e0e6f0228ba2518c918f75f1ae",None),
"original-ac8-exp_oop.zip":(14793159254,"400b10c2f45130e018fd93f0eb6e8341189525086ce981b88fcdfce22da3eb87",None)}
def dump(p,obj):
    p.write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")
def read(p): return json.loads(Path(p).read_bytes())
def guard():
    parent=os.environ["GITHUB_SHA"]
    assert os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_REF"]=="refs/heads/"+BRANCH
    assert git("rev-parse","HEAD")==parent and git("rev-parse","HEAD^")==BASE
    p=api("/pulls/2")
    assert p["state"]=="open" and p["draft"] and not p["merged"]
    assert (p["head"]["repo"]["full_name"],p["head"]["ref"],p["head"]["sha"])==(REPO,BRANCH,parent)
    return parent
def coverage():
    assert git("hash-object",REG)=="59d02d3c7b5ed05515ec94bc1753300264598346"
    assert git("hash-object",WEIGHTS)=="7519db4affc935040f07d455e090ce9d3bc07138"
    reg=read(REG)["records"]
    w={n["model_id"]:Decimal(str(n["estimated_NL2_hand_opportunity_fraction"])) for n in read(WEIGHTS)["nodes"]}
    assert set(w)==set(reg) and len(w)==392
    assert Counter(v["label"] for v in reg.values())=={"CERT-MULTIBOARD":158,"APPROX":234}
    assert reg["ln-opfr-r_model-tl6ij8"]["label"]=="APPROX"
    cov=round(100*sum(w[k] for k,v in reg.items() if v["label"]=="CERT-MULTIBOARD")/sum(w.values()),6)
    high=sum(v["label"]=="APPROX" and w[k]>=Decimal("0.002") for k,v in reg.items())
    assert cov==Decimal("84.700987") and high==30
    return {"cert":158,"approx":234,"coverage_pct":str(cov),"high_approx":high}
def prepare(out):
    parent=guard(); c=coverage()
    assert not git("status","--porcelain")
    root=Path(PREFIX); assert not root.exists(); root.mkdir(parents=True)
    out.mkdir(parents=True,exist_ok=True)
    runs={}
    for id,head in RUNS.items():
        r=api("/actions/runs/"+str(id))
        assert (r["head_sha"],r["head_branch"],r["status"],r["conclusion"])==(head,BRANCH,"completed","success"),id
        runs[str(id)]=r
    meta={}
    for name,(id,digest,run) in ARTS.items():
        a=api("/actions/artifacts/"+str(id))
        assert not a["expired"] and a["digest"]=="sha256:"+digest
        if run is not None: assert a["workflow_run"]["id"]==run and a["workflow_run"]["head_sha"]==RUNS[run]
        else:
            r=api("/actions/runs/"+str(a["workflow_run"]["id"]))
            assert (r["status"],r["conclusion"],r["head_sha"])==("completed","success",a["workflow_run"]["head_sha"])
            runs[str(r["id"])]=r
        raw=api("/actions/artifacts/"+str(id)+"/zip",raw=True)
        assert sha(raw)==digest
        with zipfile.ZipFile(io.BytesIO(raw)) as z: assert z.testzip() is None
        (root/name).write_bytes(raw);meta[name]=a
    accepted=read("data/nl2_hu_b895_accepted_r158_witness.json")
    with zipfile.ZipFile(root/"b894-replay.zip") as z:
        witness=json.loads(z.read("report-23.json"))
        for mode in ("gto","exp_oop"):
            raw=z.read(mode+".zip")
            pins=read("data/nl2_hu_b894_b893_replay_pins.json")["artifacts"][mode]
            assert sha(raw)==pins["sha256"]
            (root/("b893-"+mode+".zip")).write_bytes(raw)
    assert witness["rank"]==158 and witness["coverage_pct"]==84.700987
    assert all(witness[k]==0 for k in ("cert_promotions","formal_lock_additions","formal_nonpolarized_additions"))
    keys=("board","gto_pairs","nl2_pairs","shared_pairs","shared_hero_combos")
    assert [{k:r[k] for k in keys} for r in witness["rows"]]==accepted["rows"]
    def cards(s): return {s[i:i+2] for i in range(0,len(s),2)}
    for row in witness["rows"]:
        assert len(row["shared_deals"])==row["shared_pairs"]
        assert len({h for h,o in row["shared_deals"]})==row["shared_hero_combos"]
        assert len(cards(row["board"]))==5
        for h,o in row["shared_deals"]:
            assert len(cards(h))==len(cards(o))==2 and len(cards(h)|cards(o)|cards(row["board"]))==9
    dump(root/"b894-witness.json",witness)
    old=read("data/nl2_hu_b892_r158_raw_witness_candidate.json")
    assert old["rank"]==158 and sum(r["shared_rendered_pairs"] for r in old["rows"])==19
    dump(root/"receipts.json",{"runs":runs,"artifacts":meta,"scope":"two positive distinct flop candidates only"})
    files={str(p):sha(p.read_bytes()) for p in sorted(root.iterdir())}
    dump(out/"prepared.json",dict(c,parent=parent,files=files,native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0))
def upload(out):
    parent=guard(); coverage(); p=read(out/"prepared.json")
    assert p["parent"]==parent and p["native_solves"]==p["cert_promotions"]==0
    assert not git("diff","--name-only")
    entries=[]
    for path,h in p["files"].items():
        assert path.startswith(PREFIX)
        b=Path(path).read_bytes();assert sha(b)==h
        expected=hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()
        actual=api("/git/blobs",{"content":base64.b64encode(b).decode(),"encoding":"base64"})["sha"]
        assert actual==expected
        entries.append({"path":path,"mode":"100644","type":"blob","sha":actual})
    tree=api("/git/trees",{"base_tree":api("/git/commits/"+parent)["tree"]["sha"],"tree":entries})["sha"]
    c=api("/git/commits",{"message":"B895 archive two independently audited rank158 native source families; no CERT promotion","tree":tree,"parents":[parent]})
    assert c["tree"]["sha"]==tree and [x["sha"] for x in c["parents"]]==[parent]
    receipt=dict(p,candidate_commit=c["sha"],candidate_tree=tree,expected_sha=parent,ref_updated=False,candidate_only=True,full_audit_completed=True,blobs=entries)
    dump(out/"detached-candidate.json",receipt);print(json.dumps(receipt,indent=2))
if __name__=="__main__":
    {"prepare":prepare,"upload":upload}[sys.argv[1]](Path(sys.argv[2]).resolve())
