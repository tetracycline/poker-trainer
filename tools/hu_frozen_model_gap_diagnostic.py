#!/usr/bin/env python3
"""Exact source-only diagnostic for the two remaining top24 hard cases.
Reads immutable SHA-verified raw source archives through the registered
consolidation index. Never changes classification or creates a CERT.
"""
import collections,itertools,json,pathlib
from hu_multiboard_consolidate import discover
from hu_multiboard_promote import (
    build_source_index,candidates,FAM_ROOT,hero_seat,tokenize,
)

ROOT=pathlib.Path('data')
def target_lines(model):
    segments=model['abstract_action_history'].split('|')
    choices=[tokenize(s) for s in segments]
    if len(segments)!=int(model['street'])+1 or any(not x for x in choices):
        raise ValueError('Unparsable original model action history')
    return sorted(set('/'.join(a) for a in itertools.product(*choices)))

def audit(model,by_exact,by_locked):
    st=int(model['street']);spot=model['solver_profile'];family=model['family']
    seat=hero_seat(model['preflop_text'])
    rootpot,rootstack=FAM_ROOT[spot]
    actions=target_lines(model)
    summary=collections.Counter();detail=[]
    expected_hero_lock='exp_ip' if seat==1 else 'exp_oop'
    for key in actions:
        sources=by_exact.get((spot,family,st,seat,key),[])
        summary['source_rows_for_'+key]+=len(sources)
        for g,n,strict,origin in sources:
            node_spr=float(n['spr'])
            spr_error=abs(node_spr-float(model['approx_spr']))/max(1,node_spr)
            root_ok=abs(g['root_pot_bb']-rootpot)<=1e-6 and abs(g['root_remaining_bb']-rootstack)<=1e-6
            gap_ok=g.get('gto_gap_pct') is not None and g['gto_gap_pct']<=0.5
            spr_ok=spr_error<=0.05
            reach_ok=strict>=1 and n['reachable']>=1
            board_ok=len(n['board'])==(8 if st==1 else 10)
            pool_key=(spot,family,g['flop'],g['turn'],g['flop_line'],n['board'],n['line'],seat)
            lock_samples=[e for e in by_locked.get(pool_key,[]) if e['version']==expected_hero_lock]
            checks={'root_ok':root_ok,'gto_gap_ok':gap_ok,'spr_ok':spr_ok,
                    'strict_reach_ok':reach_ok,'board_len_ok':board_ok,'paired_hero_lock':bool(lock_samples)}
            for k,v in checks.items():summary[k+'_yes' if v else k+'_no']+=1
            summary['qualified_exact_gto_no_lock_needed']+=int(all([
                root_ok,gap_ok,spr_ok,reach_ok,board_ok]))
            if all([root_ok,gap_ok,spr_ok,reach_ok,board_ok,bool(lock_samples)]):
                summary['qualified_exact_gto_and_hero_lock']+=1
            if len(detail)<35:
                detail.append(dict(
                    flop=g['flop'],turn=g['turn'],line=n['line'],
                    public_board=n['board'],source_run=g['run_id'],
                    source_kind=g['source_kind'],origin=origin,
                    source_sha256=g['sha'],
                    gto_exploitability_pct=g['gto_gap_pct'],
                    node_spr=node_spr,spr_relative_error_pct=round(spr_error*100,4),
                    legal_combos=int(strict),locks=len(lock_samples),
                    gates=checks))
    broad=collections.Counter()
    for k,values in by_exact.items():
        spot_,family_,street_,seat_,line_=k
        if (spot_,family_,street_,seat_)==(spot,family,st,seat):
            broad[line_]+=len(values)
    m=dict(model)
    rows,reason=candidates(m,by_exact,by_locked,None)
    return dict(
        model_id=model['model_id'],spot=spot,family=family,street=st,hero_seat=seat,
        original_abstract_history=model['abstract_action_history'],
        original_estimated_spr=model['approx_spr'],requested_exact_lines=actions,
        exact_gto_candidate_rows=len(rows),refusal_reason=reason,
        by_gate=dict(summary),
        available_exact_lines_for_matching_spot_and_street=broad.most_common(45),
        source_examples=detail,
        not_a_CERT_upgrade=True)

def main():
    root=ROOT
    rank=json.loads((root/'nl2_hu_multiboard_prerank.json').read_text())
    queue=json.loads((root/'nl2_hu_stage2_queue.json').read_text())
    labels=json.loads((root/'nl2_hu_multiboard_status.json').read_text())
    byid={x['model_id']:x for x in queue['records']}
    ready,batches=discover(root)
    exact,locked,src=build_source_index(root,ready)
    cases=[]
    for row in rank['nodes']:
        if row['rank_by_empirically_grounded_frequency_proxy'] not in (1,24):continue
        m=dict(row)
        m.update({k:byid[row['model_id']][k] for k in ('preflop_text','abstract_action_history')})
        out=audit(m,exact,locked)
        out['current_label']=labels['records'][m['model_id']]['label']
        cases.append(out)
    if len(cases)!=2 or sorted(c['model_id'] for c in cases)!=sorted([
       next(x['model_id'] for x in rank['nodes'] if x['rank_by_empirically_grounded_frequency_proxy']==i)
       for i in (1,24)]):
        raise ValueError('Frozen top24 unexpected')
    report=dict(schema='TASK_HYBRID_FROZEN_1_AND_24_SOURCE_GAP_DIAG_V1',
        model_count=392,ranked_scope=[1,24],total_CERT=labels['CERT_MULTIBOARD'],
        source_files=[x.name for x in ready],source_index_batches=batches,
        no_gto_or_hero_lock_claim_from_diagnostic=True,cases=cases)
    target=pathlib.Path('data/nl2_hu_rank1_24_exact_source_diagnostic.json')
    target.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    for c in cases:
        print('RANK',c['original_abstract_history'],c['spot'],c['model_id'],
            'source target',c['requested_exact_lines'],
            'gates',c['by_gate'],'other exact lines',c['available_exact_lines_for_matching_spot_and_street'][:12])
    print('PASS source-only diagnostics',len(cases),'CERT unchanged',report['total_CERT'])
if __name__=='__main__':main()
