#!/usr/bin/env python3
"""Verify an archived action-history GitHub Actions run, without re-solving.

Every authentic CFR subgame is verified against its own manifest SHA-256,
range/stack/pot lineage and independently reconstructed per-combo reach.
No result can be counted as a certified NL2 webpage cell until a separate
position+bet-history+SPR+board+combo-link crosswalk is proved.
"""
import argparse
import hashlib
import importlib
import json
import pathlib

def checksum(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
    return h.hexdigest()

def verify_downloads(root,run_id):
    reach=importlib.import_module('hu_action_reach').audit
    results=[]
    errors=[]
    n_subgames=0
    skipped=0
    reach_combos=0
    near_mixed=0
    kinds=set()
    for ad in sorted(root.glob('nl2-new-branches-*')):
        manifests=list((ad/'evidence').glob('*.json'))
        if len(manifests)!=1:
            errors.append({'artifact':ad.name,'reason':'Expected exactly one solver manifest'})
            continue
        m=json.loads(manifests[0].read_text())
        if m.get('failures') or m.get('failed_flops'):
            errors.append({'artifact':ad.name,'reason':'Original solver reported failures'})
        spot,ver=m['spot'],m['version']
        if spot not in ad.name or ver not in ad.name:
            errors.append({'artifact':ad.name,'reason':'Artifact name vs manifest profile mismatch'})
            continue
        cases=[]
        for case in m['cases']:
            try:
                base=ad/'solver/postflop'
                flopfile=base/case['flop_json']
                subfile=base/case['sub_json']
                if checksum(flopfile)!=case['flop_sha256'] or checksum(subfile)!=case['sub_sha256']:
                    raise ValueError('Manifest CFR SHA-256 mismatch')
                fr=json.loads(flopfile.read_text())
                data=json.loads(subfile.read_text())
                if data.get('flop')!=case['flop'] or data.get('turn')!=case['turn'] or data.get('line0')!=case['line']:
                    raise ValueError('Wrong flop/turn/history on river CFR')
                parent=next((x for x in fr['nodes'] if x['line']==case['line']+'/'
                              and x['board'][-2:]==case['turn']),None)
                if parent is None:raise ValueError('Missing exact parent action history')
                if abs(case['turn_node_spr']-
                    (fr['stack']-max(parent['bets']))/parent['pot'])>1e-5:
                    raise ValueError('Source node SPR mismatch')
                for n in data['nodes']:
                    k=n['line']+'|'+n['board']
                    if k not in case['node_spr_by_exact_line_and_board']:
                        raise ValueError('Missing recorded node SPR '+k)
                    observed=(data['stack']-max(n['bets']))/n['pot']
                    expected=case['node_spr_by_exact_line_and_board'][k]
                    if expected is None or abs(expected-observed)>1e-5:
                        raise ValueError('Turn/river node SPR mismatch '+k)
                rp=reach(data,str(subfile),case['sub_sha256'],str(run_id))
                count=rp['summary']
                n_subgames+=1
                reach_combos+=count['combos_reachable']
                near_mixed+=count['near_mixed']
                kinds.add(spot)
                cases.append({'flop':case['flop'],'turn':case['turn'],'line':case['line'],
                  'parent_spr':case['turn_node_spr'],
                  'n_solver_nodes':len(data['nodes']),
                  'gto_gap_pct':data['info'].get('gto_expl_pct'),
                  'hero_gap_pct':data['info'].get('hero_gap_pct'),
                  'pool_lock_patterns':len(data['info'].get('lock_stats',{})),
                  'source_sha256':case['sub_sha256'],
                  'reach_summary':count,
                  'certified_nl2_cells':0})
            except Exception as exc:
                errors.append({'artifact':ad.name,'case':case.get('line'), 'reason':str(exc)})
        skipped+=len(m.get('skipped_unreachable',[]))
        results.append(dict(artifact=ad.name,spot=spot,version=ver,
              solved_cases=len(cases),skipped_unreachable=m.get('skipped_unreachable',[]),
              cases=cases))
    report=dict(schema='NL2_HU_SOLVER_ARCHIVE_AUDIT_V1',
       run_id=run_id,artifact_count=len(results),profiles=sorted(kinds),
       solved_subgames=n_subgames,skipped_unreachable=skipped,
       raw_reachable_hand_combos=reach_combos,near_mixed_combo_nodes=near_mixed,
       certified_new_nl2_river_cells=0,estimated_new_nl2_river_cells=0,
       mapping_status='BLOCKED: needs verified NL2 exact action, pot, ranges, SPR and board lineage',
       errors=errors,artifacts=results)
    if not results:errors.append({'reason':'No artifact downloads found'})
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--downloads',type=pathlib.Path,required=True)
    p.add_argument('--run-id',type=int,required=True)
    p.add_argument('--out',type=pathlib.Path,required=True)
    a=p.parse_args()
    report=verify_downloads(a.downloads,a.run_id)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('artifacts','errors')},ensure_ascii=False))
    if report['errors']:
        print(json.dumps(report['errors'],ensure_ascii=False))
        raise SystemExit(1)
if __name__=='__main__':main()
