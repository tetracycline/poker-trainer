"""B897: repair the never-executed B882 Jd9d3c preflight, not its two successful siblings.
Fixed flop and turns, no native outcomes used in selecting a static witness.
A witness is only an eligibility test; any native result is still a candidate.
"""
import argparse, gzip, itertools, json, subprocess
from pathlib import Path
from zipfile import ZipFile
import hu_b703_rank29_highcards as base
import hu_b882_rank29_new_twotone as prior
from hu_b582_rank29_reach import DECK, rendered
from hu_b467_river_source_gate import json_bytes
FLOP="Jd9d3c"
TURNS=("2d","4d","5d","7d")
HEAD="1cbe1de9d3c6fe806014083830ca2ce1e1762bfe"
APP={"nl2_hu_model.js":"cf3682f6c04f8dae054010c8e4e192dbed31be56","nl2.js":"15aee97e53a156fe073c96a120638a8a3679958f"}
def git(*args):
    return subprocess.check_output(["git",*args],text=True).strip()
def cards(s):
    return {s[i:i+2] for i in range(0,len(s),2)}
def read(p):
    return json.loads(Path(p).read_bytes())
def original_receipt(path):
    job=read(path)
    assert (job["id"],job["run_id"],job["head_sha"],job["name"],job["conclusion"])==(139691797892,45755111223,HEAD,"solve (Jd9d3c)","failure")
    steps={s["name"]:s["conclusion"] for s in job["steps"]}
    assert steps["Preflight distinct frozen rank29 textures, exact rendered sizes, original SHA and physical cards"]=="failure"
    assert steps["Solve original GTO and authentic matched NL2 partial lock, independent file replay"]=="skipped"
def inventory():
    # Check exact root jobs/results in retained evidence, independently of filename.
    needles=["".join(p).lower().encode() for p in itertools.permutations([FLOP[i:i+2] for i in (0,2,4)])]
    def visit(o):
        if isinstance(o,dict):
            f=o.get("flop")
            if isinstance(f,str) and cards(f)==cards(FLOP) and (o.get("pot"),o.get("stack"))==(250,9900):
                return True
            return any(visit(v) for v in o.values() if isinstance(v,(dict,list)))
        if isinstance(o,list):
            return any(visit(v) for v in o if isinstance(v,(dict,list)))
        return False
    def inspect(raw):
        if not any(n in raw.lower() for n in needles):return False
        return visit(json.loads(raw))
    hits=[]; scanned=0
    for f in git("ls-files","data/solver_evidence").splitlines():
        p=Path(f)
        if f.endswith(".zip"):
            scanned+=1
            with ZipFile(p) as z:
                for n in z.namelist():
                    if n.endswith(".json") and inspect(z.read(n)):hits.append(f+":"+n)
                    elif n.endswith(".json.gz") and inspect(gzip.decompress(z.read(n))):hits.append(f+":"+n)
        elif f.endswith(".json.gz"):
            scanned+=1
            if inspect(gzip.decompress(p.read_bytes())):hits.append(f)
        elif f.endswith(".json"):
            scanned+=1
            if inspect(p.read_bytes()):hits.append(f)
    assert scanned>1000
    print(json.dumps(dict(retained_archives_scanned=scanned,duplicate_root_hits=hits)))
    assert not hits,"Existing matching root must be reviewed, not re-solved"
    # After the failed preflight, any newly introduced dispatch mention needs review.
    changed=git("diff","--name-only",HEAD,"--",".github/workflows","tools").splitlines()
    leads=[f for f in changed if Path(f).is_file() and FLOP.lower() in Path(f).read_text(errors="replace").lower()]
    allowed={"tools/hu_b884_originals.py","tools/hu_b897_rank29_blocked_preflight.py",".github/workflows/nl2-hu-b897-rank29-blocked-preflight.yml"}
    assert not set(leads)-allowed,("Unreviewed later code leads",leads)
    return scanned
def choose(manifest,route):
    # Deterministic static enumeration, no solver access and no change to the frozen board/turns.
    ranks=manifest["preflop_ranges"]
    hs=[a+b for a,b in itertools.combinations(DECK,2) if cards(a+b).isdisjoint(cards(FLOP))]
    heroes=[h for h in hs if ranks["oop_169"][base.range_class(h)]>0 and rendered(h,FLOP,"flop",route)]
    villains=[h for h in hs if ranks["ip_169"][base.range_class(h)]>0]
    for turn in TURNS:
        for h in heroes:
            if turn in cards(h) or not rendered(h,FLOP+turn,"turn",route):continue
            for river in DECK:
                dead=cards(FLOP+turn+h)
                if river in dead or not rendered(h,FLOP+turn+river,"river",route):continue
                v=next((v for v in villains if cards(v).isdisjoint(dead|{river})),None)
                if v:return (turn,river,h,v)
    raise RuntimeError("NO_STATIC_RANGE_UI_WITNESS: no native dispatch")
def main(a):
    original_receipt(a.receipt)
    prior.preflight()
    assert tuple(prior.CASES[FLOP])==TURNS
    for p,h in APP.items():assert git("hash-object",p)==h
    with ZipFile(base.TEMPLATE) as z:manifest=json.loads(z.read("original-manifest.json"))
    route=json.loads(subprocess.check_output(["node","tools/hu_b703_rank29_routes.cjs"]))
    witness=choose(manifest,route)
    print(json.dumps(dict(flop=FLOP,fixed_turns=TURNS,static_witness=witness,prior_native_job="SKIPPED")))
    if a.preflight:inventory()
    old=(base.CASES,base.RANGE_WITNESSES,base.APP_PINS)
    try:
        base.CASES={FLOP:list(TURNS)}
        base.RANGE_WITNESSES={FLOP:witness}
        base.APP_PINS=APP
        base.run(a)
    finally:
        base.CASES,base.RANGE_WITNESSES,base.APP_PINS=old
    if not a.preflight:
        p=a.output/"proof.json"
        proof=read(p)
        proof.update(schema="NL2_B897_R29_B882_NEVER_EXECUTED_PREFLIGHT_REPAIR_V1",prior_failed_job=139691797892,prior_native_step="skipped",no_cert_promotion=True)
        p.write_bytes(json_bytes(proof))
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("solver","output","receipt"):p.add_argument("--"+k,type=Path,required=True)
    p.add_argument("--flop",choices=[FLOP],default=FLOP)
    p.add_argument("--driver",type=Path)
    p.add_argument("--preflight",action="store_true")
    main(p.parse_args())
