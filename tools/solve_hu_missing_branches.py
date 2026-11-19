#!/usr/bin/env python3
"""Solve genuinely missing HU flop-to-turn-to-river histories.

This is a raw CFR continuation, not an NL2 decision publisher. Do not assume
the sample flop is the same as any displayed texture bucket, or copy across
positions/pot histories. Preserve original board, pot, bet sizes, reach and hash.
"""
import argparse
import hashlib
import gzip
import importlib
import json
import os
import pathlib
import sys
import time
import traceback

BRANCHES = {
    # Root FLOP exact action lines in a 100bb HU game. Subgame ranges are
    # inherited from the actual weighted parent combos, not the UI MODEL.
    "BTN_BB": ("x x", "x b33 c", "x b75 c", "x b33 r c", "x b75 r c"),
    "CO_BB":  ("x x", "x b33 c", "x b75 c", "x b33 r c", "x b75 r c"),
    "UTG_BB": ("x x", "x b33 c", "x b75 c", "x b33 r c", "x b75 r c"),
    "HJ_BB":  ("x x", "x b33 c", "x b75 c", "x b33 r c", "x b75 r c"),
    "SB_BB":  ("x x", "b33 c", "b75 c", "b33 r c", "b75 r c"),
    "SB3_BTN": ("x x", "b33 c", "b75 c", "b33 r c", "b75 r c"),
    "BB3_BTN": ("x x", "b33 c", "b75 c", "b33 r c", "b75 r c"),
    "UTG_CO": ("x x", "b33 c", "b75 c", "b33 r c", "b75 r c"),
    "CO3_BTN": ("x x", "x b33 c", "x b75 c", "x b33 r c", "x b75 r c"),
}
# Verified against poker-solver/preflop/pfsolve.py's exact 100bb abstract tree:
# RFI UTG/CO 2.5; first IP 3bet 3x (7.5); dead SB+BB=1.5.
# Both player action-chain ranges come from the actual preflop CFR output.
EXTRA_SPOTS = {
    "UTG_CO": dict(oop="UTG",ip="CO",
        oopc=[("UTGrfi","open")],ipc=[("UTGopen>CO","call")],
        pot=6.5,stack=97.5,pfr="oop",kind="SRP"),
    "CO3_BTN": dict(oop="CO",ip="BTN",
        oopc=[("COrfi","open"),("COopen>BTN3b","call")],
        ipc=[("COopen>BTN","3bet")],
        pot=16.5,stack=92.5,pfr="ip",kind="3BP"),
}
def digest(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--solver-root',required=True,type=pathlib.Path)
    p.add_argument('--spot',choices=BRANCHES,required=True)
    p.add_argument('--start',type=int,default=0)
    p.add_argument('--count',type=int,default=1)
    p.add_argument('--turn-count',type=int,default=1)
    p.add_argument('--version',choices=['gto','exp_ip','exp_oop'],default='gto')
    p.add_argument('--manifest',type=pathlib.Path,required=True)
    a=p.parse_args()
    if a.start<0 or not 1<=a.count<=2 or not 1<=a.turn_count<=3:
        p.error('start >= 0; count 1..2; turn-count 1..3')
    pf=a.solver_root.resolve()/'postflop'
    if not (pf/'pfdriver/target/release/pfdriver').is_file():
        raise SystemExit('BLOCKED: real Rust CFR engine has not been built')
    sys.path.insert(0,str(pf/'py'))
    pipeline=importlib.import_module('pipeline')
    job=importlib.import_module('job')
    ranges=importlib.import_module('ranges')
    for profile,config in EXTRA_SPOTS.items():
        for node,action in config['oopc']+config['ipc']:
            if node not in ranges.ACTS or action not in ranges.ACTS[node]:
                raise SystemExit('INVALID_PREFLOP_CFR_RANGE: '+profile+' '+node+' '+action)
        ranges.SPOTS[profile]=config
        pipeline.NFLOP[profile]=8
        pipeline.OFFS[profile]=0.31 if profile=='UTG_CO' else 0.69
    sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
    reach_audit=importlib.import_module('hu_action_reach').audit
    flops=pipeline.flops_for(a.spot)[a.start:a.start+a.count]
    if not flops:raise SystemExit('No selected flops')
    out=pf/'out'/a.spot/a.version
    out.mkdir(parents=True,exist_ok=True)
    manifest={
      'schema':'HU_MISSING_ACTION_HISTORY_CFR_V1',
      'spot':a.spot,'version':a.version,
      'start':a.start,'count':a.count,
      'branches':BRANCHES[a.spot],
      'selected_flops':flops,
      'turn_count':a.turn_count,
      'source':'tetracycline/poker-solver',
      'source_pipeline_sha256':digest(pf/'py/pipeline.py'),
      'source_ranges_sha256':digest(pf/'py/ranges.py'),
      'source_preflop_tree_sha256':digest(a.solver_root.resolve()/'preflop/pfsolve.py'),
      'derived_spot_profile':EXTRA_SPOTS.get(a.spot),
      'solver_output_is_not_nl2_certification':True,
      'cases':[],'failures':[],'skipped_unreachable':[],
    }
    for flop in flops:
        t0=time.monotonic()
        turns=pipeline.turns_for(flop)[:a.turn_count]
        lines=BRANCHES[a.spot]
        fpath=out/f'{flop}_extra_branch.json'
        # Extract actual combo reach at each exact line; source GTO/locked ranges,
        # not guessed class reach or blanket continuation probability.
        extracts=[dict(prefix=[],street=True)] + [
          dict(prefix=line.split()+[turn],street=False,raw=True)
          for line in lines for turn in turns]
        locks,_=pipeline.lock_list(a.spot,a.version,flop)
        j=job.make_job(a.spot,a.version,flop,str(fpath)+'.tmp',
          extract=extracts,locks=locks,compress=True,target=0.5,rank=1.5)
        jpath=out/f'{flop}_extra_branch.job.json'
        try:
            log=job.run(j,str(jpath))
            os.rename(str(fpath)+'.tmp',fpath)
            fr=json.loads(fpath.read_text())
            fr['info']['log']=log
            fr['turns']=turns
            fpath.write_text(json.dumps(fr,separators=(',',':')))
            for line in lines:
                for turn in turns:
                    node=next((n for n in fr['nodes']
                        if n['line']==line+'/' and n['board'][-2:]==turn),None)
                    wr=node.get('wr') if node else None
                    if not wr or len(wr)!=2 or any(
                      sum(float(w) for w in side if float(w)>1e-4)<=0 for side in wr):
                        manifest['skipped_unreachable'].append(
                          {'flop':flop,'line':line,'turn':turn,'reason':'NO_TWO_SIDED_COMBO_REACH'})
                        continue
                    # solve_sub generates the turn/river tree with exact pot, stacks,
                    # per-combo reach from this parent branch and sampled river cards.
                    pipeline.solve_sub(a.spot,a.version,flop,fr,line,turn)
                    key=f"{flop}_{line.replace(' ','')}_{turn}"
                    sub=out/f'{key}.json'
                    if not sub.is_file():
                        raise RuntimeError('missing authentic turn/river CFR file: '+str(sub))
                    src=json.loads(sub.read_text())
                    mem={}
                    for n in src.get('nodes',[]):
                        bb=int(src['stack'])-max(n.get('bets',[0,0]))
                        mem[n['line']+'|'+n['board']]=None if n['pot']<=0 else round(max(bb,0)/n['pot'],5)
                    rproof=reach_audit(src,str(sub.relative_to(pf)),digest(sub),
                        os.environ.get('GITHUB_RUN_ID'))
                    rpath=a.manifest.parent / (
                        f"combo-reach-{a.spot}-{a.version}-{flop}-{line.replace(' ','')}-{turn}.json.gz")
                    rpath.parent.mkdir(parents=True,exist_ok=True)
                    with gzip.open(rpath,'wt',encoding='utf8') as h:
                        json.dump(rproof,h,ensure_ascii=False,separators=(',',':'))
                    manifest['cases'].append({
                       'flop':flop,'line':line,'turn':turn,
                       'combo_reach_report':str(rpath),
                       'combo_reach_report_sha256':digest(rpath),
                       'combo_reach_summary':rproof['summary'],
                       'combo_reach_converged_for_cert':rproof['converged_for_cert'],
                       'root_pot_bb':fr['pot']/100,'root_stack_bb':fr['stack']/100,
                       'turn_node_pot_bb':node['pot']/100,
                       'turn_node_stack_bb':(fr['stack']-max(node['bets']))/100,
                       'turn_node_spr':round((fr['stack']-max(node['bets']))/node['pot'],5),
                       'flop_json':str(fpath.relative_to(pf)),
                       'flop_sha256':digest(fpath),
                       'sub_json':str(sub.relative_to(pf)),'sub_sha256':digest(sub),
                       'sub_gto_expl_pct':src['info'].get('gto_expl_pct'),
                       'sub_hero_gap_pct':src['info'].get('hero_gap_pct'),
                       'node_spr_by_exact_line_and_board':mem,
                       'status':'AUTHENTIC_CFR_NEEDS_UI_LINEAGE_PROOF'})
        except Exception as ex:
            manifest['failures'].append({'flop':flop,'reason':str(ex),
                                         'trace':traceback.format_exc()[-1200:]})
        manifest.setdefault('seconds_by_flop',{})[flop]=round(time.monotonic()-t0,2)
    manifest['cases_solved']=len(manifest['cases'])
    manifest['failed_flops']=len(manifest['failures'])
    a.manifest.parent.mkdir(parents=True,exist_ok=True)
    a.manifest.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'spot':a.spot,'version':a.version,
        'cases_solved':manifest['cases_solved'],
        'skipped_unreachable':len(manifest['skipped_unreachable']),
        'failed_flops':len(manifest['failures'])}))
    if manifest['failures']:raise SystemExit(1)
if __name__=='__main__':main()
