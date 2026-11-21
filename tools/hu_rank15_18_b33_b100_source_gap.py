#!/usr/bin/env python3
"""Immutable source-only audit of high-frequency NL2 river ranks 15/18.
No CERT promotion; examine strict b33-c / b100-c per-combo sources and paired hero lock.
"""
import collections,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from hu_multiboard_consolidate import discover
from hu_multiboard_promote import build_source_index,candidates,hero_seat

ROOT=pathlib.Path('data')
TARGET='b33 c/b100 c/'
def main():
    reg=json.loads((ROOT/'nl2_hu_multiboard_status.json').read_text())
    rank=json.loads((ROOT/'nl2_hu_multiboard_prerank.json').read_text())
    queue=json.loads((ROOT/'nl2_hu_stage2_queue.json').read_text())
    byid={v['model_id']:v for v in queue['records']}
    selection=[v for v in rank['nodes'] if v['rank_by_empirically_grounded_frequency_proxy'] in (15,18)]
    assert len(selection)==2 and reg['TOTAL']==392
    ready,bat=discover(ROOT)
    exact,locked,summary=build_source_index(ROOT,ready)
    records=[]
    for q in selection:
        model=byid[q['model_id']]
        row=dict(q)
        row.update({k:model[k] for k in ('preflop_text','abstract_action_history')})
        spot=row['spot'];family=row['family'];street=row['street'];seat=hero_seat(row['preflop_text'])
        assert spot=='SB_BB' and family=='SRP' and street==2 and seat==0
        assert row['abstract_action_history']=='你下注、對手跟|你下注、對手跟|'
        keys=('SB_BB','SRP',2,0,TARGET)
        available=exact.get(keys,[])
        entries=[]
        flops=collections.defaultdict(lambda:{'gto_nodes':0,'strict_eligible_nodes':0,
            'matching_locked_nodes':0,'strict_combos':0,'root_spr':set(),'source_runs':set()})
        for g,n,strict,origin in available:
            err=abs(n['spr']-row['approx_spr'])/max(1,n['spr'])
            pool_key=(spot,family,g['flop'],g['turn'],g['flop_line'],n['board'],n['line'],seat)
            paired=[x for x in locked.get(pool_key,[]) if x['version']=='exp_oop']
            legal=bool(strict>0 and n['reachable']>0 and err<=.05 and g['gto_gap_pct'] is not None and g['gto_gap_pct']<=.5)
            agg=flops[g['flop']]
            agg['gto_nodes']+=1
            agg['strict_eligible_nodes']+=int(legal)
            agg['matching_locked_nodes']+=int(legal and bool(paired))
            agg['strict_combos']+=int(strict) if legal else 0
            agg['root_spr'].add(round(n['spr'],5))
            agg['source_runs'].add(g['run_id'])
            entries.append(dict(flop=g['flop'],turn=g['turn'],line=n['line'],board=n['board'],
                gto_run=g['run_id'],gto_sha256=g['sha'],source_kind=g['source_kind'],
                actual_spr=round(n['spr'],5),target_spr=row['approx_spr'],
                spr_error_pct=round(err*100,4),gto_gap_pct=g['gto_gap_pct'],
                strict_combo_count=int(strict),actor_reachable_combos=int(n['reachable']),
                valid_gto_for_exact_model=legal,paired_exp_oop_count=len(paired),
                lock_source_runs=[x['run_id'] for x in paired],
                lock_source_scopes=[x['scope'] for x in paired],
                origin=origin))
        possible,reason=candidates(row,exact,locked,None)
        result=dict(rank=q['rank_by_empirically_grounded_frequency_proxy'],id=row['model_id'],
            current_label=reg['records'][row['model_id']]['label'],
            exact_target=TARGET,hero=seat,spot=spot,source_count=len(entries),
            valid_gto_plus_any_lock_count=sum(x['valid_gto_for_exact_model'] and x['paired_exp_oop_count']>0 for x in entries),
            by_flop=[dict(flop=f,**{k:sorted(v) if isinstance(v,set) else v for k,v in z.items()})
                for f,z in sorted(flops.items())],
            all_matches=sorted(entries,key=lambda x:(-int(x['valid_gto_for_exact_model']),-x['strict_combo_count'],x['flop'],x['turn'])),
            candidate_count=len(possible),no_exact_match_reason=reason)
        records.append(result)
    assert len(records)==2
    s=dict(schema='TASK_HYBRID_RANK15_18_STRICT_B33_B100_LINEAGE_V1',
        from_verified_cert_count=reg['CERT_MULTIBOARD'],
        source_archives=[p.name for p in ready],
        registry_unchanged=True,does_not_certify_new_models=True,
        pair_gate='matching source family, acting hero, exact turn+river line, named flop/turn/river, 5% SPR, <=0.5% GTO gap and positive max/near combo reach',
        records=records)
    dest=ROOT/'nl2_hu_rank15_18_b33_b100_source_gap.json'
    dest.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
    for r in records:
        print('RANK',r['rank'],'exact-source-rows',r['source_count'],'candidate count',r['candidate_count'])
        print('FLOPS',r['by_flop'])
    print('PASS source-only exact 15/18 lineage audit (no label changes)')
if __name__=='__main__':main()
