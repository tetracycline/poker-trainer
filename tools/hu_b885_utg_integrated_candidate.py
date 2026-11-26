#!/usr/bin/env python3
"""B885: isolated integration of the B883 exact UTG price candidate.
Never writes a source archive, never invokes a solver, never moves a ref.
Run only in a disposable checkout; export a diff after both registry runtimes
and the full batch audit have passed. Historical certificates remain immutable.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from decimal import Decimal

D = Path("data")
STATUS = D / "nl2_hu_multiboard_status_current.json"
PARENT = "ln-opfr-t_model-19umlco"
TARGETS = {
    PARENT: (68, 7.25, "CERT-MULTIBOARD"),
    "ln-opfr-r_model-1puypid": (157, 2.6, "APPROX"),
    "ln-opfr-r_model-tl6ij8": (158, 4.151, "APPROX"),
    "ln-opfr-r_model-8w3cpr": (205, 7.25, "APPROX"),
}
PIN = D / "solver_evidence/reverified/rank68.json"
SHA = {
    "Jh9s4c": "88e20448d6f4c5636a063b3b3e78573f6bb14af4650c17b537de6b857671245e",
    "Ac8d3h": "827626b0c4f99471a63619af0a07c90bb4a46541043ab21565c88455337d5619",
    "As9d4c": "7b4b98e42a364b8188519976f0682bc7b973b468059896693fbe31b42fb6ffb5",
}
def read(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(p, old, new):
    s = p.read_text()
    assert s.count(old) == 1, (p, old)
    p.write_text(s.replace(old, new))
def run(*args): subprocess.run(args, check=True)
def main(out):
    out.mkdir(parents=True, exist_ok=True)
    assert not subprocess.check_output(["git", "status", "--porcelain"])
    before = read(STATUS)
    assert (before["CERT_MULTIBOARD"],before["APPROX"],before["EST"],before["TOTAL"]) == (158,234,0,392)
    original_pin = sha(PIN)
    original_boards = read(PIN)["boards"]
    assert {x["flop"]:x["source_sha256"] for x in original_boards} == SHA
    assert all((x["actual_spr"],x["model_assumed_spr"],x["relative_spr_error_pct"],x["acting_seat"],x["actual_exact_action_line"]) == (7.25,7,3.571429,0,"x b50 c/") for x in original_boards)
    run("python3","tools/hu_b838_approx_coverage_priority_audit.py")
    run("node","tools/hu_b883_utg_price_candidate.cjs",str(out/"b883"))
    model = Path("nl2_hu_model.js")
    model.write_bytes((out/"b883/nl2_hu_model.candidate.js").read_bytes())
    # Propagate explicit price into the existing rendered-route contract.
    replace(model, "const flopCallPct = priced ? Number(printed[2]) : s.flopCallPct;",
        "const flopCallPct = utgCall ? 50 : priced ? Number(printed[2]) : s.flopCallPct;")
    # Historical repair JSON stays original. Reconcile only the derived active
    # model-assumption fields of the three SHA-pinned rank68 boards.
    py = Path("tools/hu_apply_cert_extensions.py")
    replace(py, '        assert b["model_assumed_spr"] == model["assumed_model_node_spr"]',
'''        if mid == "ln-opfr-t_model-19umlco":
            historical = {"Jh9s4c":"88e20448d6f4c5636a063b3b3e78573f6bb14af4650c17b537de6b857671245e",
                          "Ac8d3h":"827626b0c4f99471a63619af0a07c90bb4a46541043ab21565c88455337d5619",
                          "As9d4c":"7b4b98e42a364b8188519976f0682bc7b973b468059896693fbe31b42fb6ffb5"}
            assert rank == 68 and model["assumed_model_node_spr"] == 7.25
            assert historical.get(b["flop"]) == b["source_sha256"]
            assert (b["actual_pot_bb"],b["actual_effective_stack_bb"],b["actual_spr"],
                    b["model_assumed_spr"],b["relative_spr_error_pct"],b["acting_seat"],
                    b["actual_exact_action_line"]) == (13,94.25,7.25,7,3.571429,0,"x b50 c/")
            b.update(historical_model_assumed_spr=7,historical_relative_spr_error_pct=3.571429,
                     model_assumed_spr=7.25,relative_spr_error_pct=0)
        assert b["model_assumed_spr"] == model["assumed_model_node_spr"]''')
    js = Path("nl2_cert_registry.js")
    replace(js, "  for (const [id,route] of Object.entries(manifest.trainer_route_contract?.routes || {})) {",
'''  const utgPrice = {
    'ln-opfr-t_model-19umlco':[68,1,'ln-opfr-f_vs_donk-1cci9ku','你過、對手下注、你跟|',['x b50 c',''],7.25],
    'ln-opfr-r_model-1puypid':[157,2,'ln-opfr-t_model-19umlco','你過、對手下注、你跟|你下注、對手跟|',['x b50 c','b75 c',''],2.6],
    'ln-opfr-r_model-tl6ij8':[158,2,'ln-opfr-t_model-19umlco','你過、對手下注、你跟|你下注、對手跟|',['x b50 c','b33 c',''],4.151],
    'ln-opfr-r_model-8w3cpr':[205,2,'ln-opfr-t_model-19umlco','你過、對手下注、你跟|你過、對手過|',['x b50 c','x x',''],7.25]
  };
  for (const id of Object.keys(utgPrice)) {
    if (!manifest.trainer_route_contract?.routes?.[id]) throw Error('Missing UTG exact route');
  }
  for (const [id,route] of Object.entries(manifest.trainer_route_contract?.routes || {})) {''')
    replace(js, "    if (route.priced_model_spr === undefined) {",
'''    if (utgPrice[id]) {
      const [rank,street,parent,history,streets,spr]=utgPrice[id];
      if (!model || model.model_id!==id || model.frequency_rank!==rank || model.street!==street ||
          model.source_model_id!==parent || model.solver_profile!=='UTG_CO' || model.family!=='SRP' ||
          model.abstract_action_history!==history || route.seat!==0 ||
          route.priced_model_spr!==spr || !Array.isArray(route.streets) ||
          route.streets.length!==streets.length || !streets.every((x,i)=>x===route.streets[i]))
        throw Error('Incorrect UTG exact route geometry');
      records[id]={...model,assumed_model_node_spr:spr};
      continue;
    }
    if (route.priced_model_spr === undefined) {''')
    replace(js, "    for (const b of e.boards) {",
'''    if (e.model_id==='ln-opfr-t_model-19umlco') {
      const original={
        Jh9s4c:'88e20448d6f4c5636a063b3b3e78573f6bb14af4650c17b537de6b857671245e',
        Ac8d3h:'827626b0c4f99471a63619af0a07c90bb4a46541043ab21565c88455337d5619',
        As9d4c:'7b4b98e42a364b8188519976f0682bc7b973b468059896693fbe31b42fb6ffb5'
      };
      if(e.rank!==68 || m.assumed_model_node_spr!==7.25 || e.boards.length!==3)
        throw Error('Invalid historical rank68 price reconciliation');
      e={...e,boards:e.boards.map(b=>{
        if(original[b.flop]!==b.source_sha256 || b.actual_pot_bb!==13 ||
           b.actual_effective_stack_bb!==94.25 || b.actual_spr!==7.25 ||
           b.model_assumed_spr!==7 || b.relative_spr_error_pct!==3.571429 ||
           b.acting_seat!==0 || b.actual_exact_action_line!=='x b50 c/')
          throw Error('Invalid historical rank68 source');
        return {...b,historical_model_assumed_spr:7,historical_relative_spr_error_pct:3.571429,
                model_assumed_spr:7.25,relative_spr_error_pct:0};
      })};
    }
    for (const b of e.boards) {''')
    run("node","--check",str(model))
    run("node","--check",str(js))
    run("python3","tools/hu_apply_cert_extensions.py","--out",str(STATUS))
    after = read(STATUS)
    assert sha(PIN) == original_pin
    assert set(before["records"]) == set(after["records"])
    assert (after["CERT_MULTIBOARD"],after["APPROX"],after["EST"],after["TOTAL"]) == (158,234,0,392)
    assert before["all_cert_lock_medium"] == after["all_cert_lock_medium"]
    assert before["exact_source_extensions"] == after["exact_source_extensions"]
    for mid, old in before["records"].items():
        new = after["records"][mid]
        if mid not in TARGETS:
            assert old == new, mid
            continue
        rank,spr,label=TARGETS[mid]
        assert (new["frequency_rank"],new["assumed_model_node_spr"],new["label"]) == (rank,spr,label)
        expected = json.loads(json.dumps(old))
        expected["assumed_model_node_spr"]=spr
        if mid==PARENT:
            for board in expected["certified_3_to_5_exact_flop_boards"]:
                assert SHA[board["flop"]] == board["source_sha256"]
                board.update(historical_model_assumed_spr=7,historical_relative_spr_error_pct=3.571429,
                             model_assumed_spr=7.25,relative_spr_error_pct=0)
        assert expected == new, mid
    frozen = read(D/"nl2_hu_multiboard_prerank.json")
    weights = {n["model_id"]:Decimal(str(n["estimated_NL2_hand_opportunity_fraction"])) for n in frozen["nodes"]}
    assert set(weights)==set(after["records"])
    total=sum(weights.values())
    cert=sum(weights[mid] for mid,m in after["records"].items() if m["label"]=="CERT-MULTIBOARD")
    coverage=round(100*cert/total,6)
    high=[mid for mid,m in after["records"].items() if m["label"]=="APPROX" and weights[mid]>=Decimal("0.002")]
    assert coverage==Decimal("84.700987") and len(high)==30
    run("node","tools/hu_extension_runtime_test.cjs",str(STATUS))
    run("bash","tools/hu_exact_batch_audit.sh",str(STATUS))
    # Compare production route manifest to the renderer, and independently
    # recompute the high-frequency boundary in the fixed candidate.
    manifest=read(D/"nl2_hu_verified_extensions.json")
    routes=manifest["trainer_route_contract"]["routes"]
    for mid,(_,spr,_) in TARGETS.items():
        assert routes[mid]["priced_model_spr"]==spr
        assert routes[mid]["streets"][0]=="x b50 c"
    candidate_routes=json.loads(subprocess.check_output(["node","tools/hu_b881_tail_price_routes.cjs"]))
    for a in candidate_routes:
        if a["rank"] in (157,158):
            assert (a["turn_facts"]["pot"],a["turn_facts"]["stack"])==(13,94.25)
            assert (a["pot"],a["stack"])==((32.5,84.5) if a["rank"]==157 else (21.66,89.92))
    allowed={str(model),str(py),str(js),str(STATUS),"data/nl2_hu_verified_extensions.json",
             "data/nl2_hu_model_history_crosswalk.json","data/nl2_hu_model_source_references.json"}
    changed=set(subprocess.check_output(["git","diff","--name-only"],text=True).splitlines())
    assert changed<=allowed and {str(model),str(py),str(js),str(STATUS)}<=changed,changed
    run("git","diff","--check")
    (out/"candidate.patch").write_bytes(subprocess.check_output(["git","diff","--binary"]))
    report=dict(schema="NL2_B885_ATOMIC_UTG_PRICE_CANDIDATE_V1",candidate_only=True,
        source_pin_sha256=original_pin,changed_files=sorted(changed),
        candidate_file_sha256={p:sha(Path(p)) for p in sorted(changed)},
        unchanged_records=388,cert=158,approx=234,coverage_pct=str(coverage),
        eligible_high_frequency=len(high),native_solves=0,new_cert=0,new_locks=0,new_medium=0,
        exact_price_routes=[a for a in candidate_routes if a["rank"] in (157,158)])
    (out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="exact_price_routes"},ensure_ascii=False))
if __name__=="__main__":main(Path(sys.argv[1]).resolve())
