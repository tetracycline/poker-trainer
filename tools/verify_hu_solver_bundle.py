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

import re

def audit_pool_locks(data, subfile, ver):
    # An observed aggregate NL2 node frequency is not an observed combo range.
    if ver=='gto':return {'version':'GTO_NO_POOL_LOCK','villain_nodes':0,'matched_nodes':0,'coverage_pct':None}
    jobfile=subfile.with_suffix('.job.json')
    if not jobfile.is_file():raise ValueError('Missing source CFR job: '+str(jobfile))
    job=json.loads(jobfile.read_text())
    pats=[re.compile(x['pat']) for x in job.get('locks',[])]
    villain=0 if ver=='exp_ip' else 1
    valid=matched=0;unknown=[]
    for node in data['nodes']:
        if node['player']!=villain or len(node['acts'])<2:continue
        if not any(float(x)>1e-4 for x in node['w'][villain]):continue
        valid+=1
        if any(p.search(node['line']) for p in pats):matched+=1
        else:unknown.append({'board':node['board'],'line':node['line']})
    return {'version':'NL2_AGGREGATE_NODE_LOCKS_NOT_DIRECT_COMBO_OBSERVATIONS',
      'villain_nodes':valid,'matched_nodes':matched,'unmatched_nodes':valid-matched,
      'coverage_pct':round(100*matched/valid,2) if valid else None,
      'source_pattern_count':len(pats),'unmatched_examples':unknown[:25],
      'fully_locked_in_sample':bool(valid>0 and matched==valid),
      'interpretation':'Regex match is source coverage, not observed combo evidence; unmatched villain nodes remain unlocked.'}

def exact_medium_action_candidates(data, ver):
    # Eligible only on the exact public cards and action history, never on
    # every board with the same texture or a different family/SPR.
    hero=1 if ver=='exp_ip' else 0 if ver=='exp_oop' else None
    out=[]
    for node in data['nodes']:
        actor=node['player']
        if hero is not None and actor!=hero:continue
        acts=node['acts']
        if 'b50' not in acts:continue
        nh=len(data['hands'][actor])
        w=node['w'][actor];strategy=node['strat']
        if len(strategy)!=nh*len(acts):raise ValueError('CFR strategy dimensions invalid')
        bj=acts.index('b50');cnt=0;freq_sum=reach_sum=0.
        for h in range(nh):
            wt=float(w[h])
            if wt<=1e-4:continue
            q=[max(0,float(strategy[i*nh+h])) for i in range(len(acts))]
            t=sum(q)
            if t<=0:continue
            q=[v/t for v in q];reach_sum+=wt;freq_sum+=wt*q[bj]
            if q[bj]>=0.4-1e-7 and q[bj]>=0.7*max(q)-1e-7:cnt+=1
        if cnt:
            out.append({'board':node['board'],'exact_line':node['line'],'hero':hero,
              'actor':actor,'node_spr':round((data['stack']-max(node['bets']))/node['pot'],6),
              'eligible_combos':cnt,'reach_weighted_b50_pct':round(100*freq_sum/reach_sum,3) if reach_sum else 0})
    return out[:150]

def locked_response_gain(data,ver):
    if ver=='gto':return None
    a=data['info'].get('ev_exploit');b=data['info'].get('ev_gto_vs_pool')
    if not isinstance(a,list) or not isinstance(b,list) or len(a)!=2 or len(b)!=2:
        return None
    hero=1 if ver=='exp_ip' else 0
    return round((float(a[hero])-float(b[hero]))/100,5)

def verify_downloads(root,run_id):
    reach=importlib.import_module('hu_action_reach').audit
    results=[]
    errors=[]
    n_subgames=0
    skipped=0
    reach_combos=0
    near_mixed=0
    kinds=set()
    for ad in sorted(root.iterdir()):
        if not ad.is_dir() or not (ad.name.startswith('nl2-new-branches-') or
                                   ad.name.startswith('nl2-derived-') or
                                   (ad.name.startswith('nl2-stage2-') and '-verified-provenance' not in ad.name)):
            continue
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
                # GTO itself must converge to <=0.5%. The existing NL2
                # exploit driver optimizes a locked hero response to <=0.5%
                # but its preliminary equilibrium can stop at 1.5%;
                # those solves are evidence of a provisional pool response,
                # never eligible for CERT without the stricter first stage.
                gto_gap=data['info'].get('gto_expl_pct')
                hero_gap=data['info'].get('hero_gap_pct')
                if ver=='gto':
                    if gto_gap is None or float(gto_gap)>0.5:
                        raise ValueError('GTO CFR not converged to <=0.5%')
                else:
                    if gto_gap is None or float(gto_gap)>1.5 or hero_gap is None or float(hero_gap)>0.5:
                        raise ValueError('NL2 locked response exceeds the declared convergence gate')
                if case.get('combo_reach_report_sha256'):
                    cr=ad/case['combo_reach_report']
                    if not cr.exists() or checksum(cr)!=case['combo_reach_report_sha256']:
                        raise ValueError('Combo reach original sha256 mismatch')
                pool_support=audit_pool_locks(data,subfile,ver)
                med=exact_medium_action_candidates(data,ver)
                gain=locked_response_gain(data,ver)
                count=rp['summary']
                n_subgames+=1
                reach_combos+=count['combos_reachable']
                near_mixed+=count['near_mixed']
                kinds.add(spot)
                cases.append({'flop':case['flop'],'turn':case['turn'],'line':case['line'],
                  'parent_spr':case['turn_node_spr'],
                  'n_solver_nodes':len(data['nodes']),
                  'gto_gap_pct':data['info'].get('gto_expl_pct'),
                  'cert_converged':bool(rp['converged_for_cert']),
                  'solver_validated_for':'GTO_EXACT_BOARD_ONLY' if ver=='gto' else 'LOCKED_POOL_RESPONSE_PROVISIONAL_GTO_BASELINE',
                  'hero_gap_pct':data['info'].get('hero_gap_pct'),
                  'pool_lock_patterns':len(data['info'].get('lock_stats',{})),
                  'villain_pool_lock_coverage':pool_support,
                  'hero_gain_vs_locked_pool_bb':gain,
                  'medium50_exact_board_candidates':med,
                  'medium50_not_a_generic_MODEL_cert':True,
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
