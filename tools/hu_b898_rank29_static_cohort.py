"""B898: bounded, source-blind rank29 static eligibility inventory.
Only exact UI and pinned assumed ranges, never a solver call or a certification.
Conservatively exclude suit-isomorphic references in every retained source.
"""
import functools, gzip, io, itertools, json, re, subprocess, sys, zipfile
from pathlib import Path
import hu_b703_rank29_highcards as base
from hu_b582_rank29_reach import DECK, rendered
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b895_archive_r158 import coverage
from hu_b467_river_source_gate import sha

CARD_RUN = re.compile(rb"(?:[2-9tjqka][cdhs]){3}", re.I)
RANKS = "23456789TJQKA"
APP = {"nl2_hu_model.js":"cf3682f6c04f8dae054010c8e4e192dbed31be56","nl2.js":"15aee97e53a156fe073c96a120638a8a3679958f"}

def cards(s):
    return {s[i:i+2] for i in range(0,len(s),2)}

@functools.lru_cache(maxsize=None)
def iso(s):
    s="".join(s[i].upper()+s[i+1].lower() for i in (0,2,4))
    if len(cards(s))!=3:
        return None
    return suit_isomorphism_class(s)

def universe():
    # Fixed rank/texture space, no native outcomes; one canonical suit representative.
    groups={}
    for high in "AKQ":
        g={}
        for lo,mid in itertools.combinations(RANKS[:RANKS.index(high)],2):
            for suits in ("cch","chc","hcc"):
                flop="".join(r+s for r,s in zip((high,mid,lo),suits))
                g.setdefault(iso(flop),flop)
        groups[high]=g
    return groups

def inventory(keys):
    # A conservative exact-card mention blocks a candidate even in a different
    # profile. This may exclude unused boards but never licenses a duplicate.
    hits={}; files=0; members=0
    def note(raw,origin):
        for m in CARD_RUN.finditer(raw):
            k=iso(m.group().decode("ascii"))
            if k in keys:
                hits.setdefault(k,origin)
    def payload(raw,origin,depth=0):
        nonlocal members
        if origin.lower().endswith(".zip"):
            assert depth<5
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                for n in z.namelist():
                    if n.endswith("/"):continue
                    members+=1
                    note(n.encode(),origin+":"+n)
                    if n.lower().endswith((".json",".json.gz",".zip",".jsonl",".csv",".txt",".md",".py",".yml",".yaml")):
                        payload(z.read(n),origin+":"+n,depth+1)
        elif origin.lower().endswith(".gz"):
            note(gzip.decompress(raw),origin)
        else:
            note(raw,origin)
    paths=subprocess.check_output(["git","ls-files","data/solver_evidence","tools",".github/workflows","docs"],text=True).splitlines()
    for f in paths:
        p=Path(f)
        if p.name.startswith("hu_b898_") or "b898-boundary" in f or "B898_" in f:continue
        if not p.is_file():continue
        if p.suffix.lower() not in (".zip",".gz",".json",".jsonl",".csv",".txt",".md",".py",".yml",".yaml",".cjs",".js"):continue
        files+=1
        note(f.encode(),f)
        payload(p.read_bytes(),f)
    assert files>1000
    return hits,files,members

def witness(flop,manifest,route):
    r=manifest["preflop_ranges"]
    dead=cards(flop)
    hs=[a+b for a,b in itertools.combinations(DECK,2) if dead.isdisjoint(cards(a+b))]
    heroes=[h for h in hs if r["oop_169"][base.range_class(h)]>0 and rendered(h,flop,"flop",route)]
    villains=[h for h in hs if r["ip_169"][base.range_class(h)]>0]
    suit=next(s for s in "cdhs" if flop[1::2].count(s)==2)
    turns=[t for t in DECK if t[1]==suit and t not in dead]
    for t in turns:
        public=flop+t
        for h in heroes:
            if t in cards(h) or not rendered(h,public,"turn",route):continue
            used=cards(public+h)
            for river in DECK:
                if river in used or not rendered(h,public+river,"river",route):continue
                v=next((v for v in villains if cards(v).isdisjoint(used|{river})),None)
                if v:
                    assert len(cards(public+river+h+v))==9
                    old=base.RANGE_WITNESSES
                    try:
                        base.RANGE_WITNESSES={flop:(t,river,h,v)}
                        proof=base.static_witness(flop,manifest,route)
                    finally:
                        base.RANGE_WITNESSES=old
                    return dict(status="STATIC_POSITIVE_REQUIRES_FULL_HISTORICAL_DISPATCH_REVIEW", witness=proof,
                                all_suited_turns=turns, can_dispatch_native=False)
    return dict(status="NO_STATIC_WITNESS_ON_ANY_SUITED_TURN",all_suited_turns=turns,can_dispatch_native=False)

def main(out):
    cov=coverage()
    for f,h in APP.items():
        assert subprocess.check_output(["git","hash-object",f],text=True).strip()==h
    raw=Path(base.TEMPLATE).read_bytes()
    assert sha(raw)==base.TEMPLATE_SHA
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        m=json.loads(z.read("original-manifest.json"))
    route=json.loads(subprocess.check_output(["node","tools/hu_b703_rank29_routes.cjs"]))
    assert (route["model_id"],route["actor"],route["line"],route["spr"])==(base.MODEL,0,"b50 c/b75 c/",7.52)
    assert (route["root_pot"],route["root_stack"],route["turn_pot"],route["turn_stack"],route["river_pot"],route["river_stack"])==(250,9900,500,9775,1250,9400)
    groups=universe()
    keys=set().union(*(set(g) for g in groups.values()))
    hits,files,members=inventory(keys)
    # Freeze first four *unmentioned* canonical flops per A/K/Q high stratum.
    # All are selected before any hand evaluator is called.
    selected=[]
    for high,g in groups.items():
        selected.extend([f for k,f in g.items() if k not in hits][:4])
    assert len(selected)<=12 and len({iso(f) for f in selected})==len(selected)
    rows=[dict(flop=f,**witness(f,m,route)) for f in selected]
    excluded=[dict(flop=f,retained_source_or_code=hits[k]) for g in groups.values() for k,f in g.items() if k in hits]
    report=dict(schema="NL2_B898_RANK29_STATIC_COHORT_V1",rank=29,coverage=cov,
                estimated_per_hand_opportunity_pct=1.378548,
                universe_count=len(keys),retained_files_scanned=files,archive_members_scanned=members,
                conservative_excluded=excluded,selected_before_evaluation=selected,rows=rows,
                native_solves=0,cert_promotions=0,formal_lock_additions=0,formal_nonpolarized_additions=0,
                limitations="Bounded cohort only. Exact card mentions are over-inclusive. Missing expired untracked receipts not ruled out. Static range/UI witness is not a GTO or NL2 strategy. No root dispatched; require historical job/receipt review and source gate.")
    out.mkdir(parents=True,exist_ok=False)
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(dict(universe=len(keys),excluded=len(hits),selected=selected,
                          static_positive=[r["flop"] for r in rows if "witness" in r],
                          native_solves=0,cert_promotions=0)))

if __name__=="__main__":
    main(Path(sys.argv[1]))
