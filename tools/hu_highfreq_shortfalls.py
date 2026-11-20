#!/usr/bin/env python3
"""Frozen top24 exact-board evidence shortfall report, no new hypotheses.

Uses only independent true Rust CFR sources already committed. Lists
why each still-APPROX top24 model does not have three distinctive matched
GTO plus hero-side NL2 locked flops, and actionable board targets.
"""
import collections,json,pathlib,sys
from hu_multiboard_promote import candidates,build_source_index,hero_seat,texture

CANDIDATE_FLOPS={
 'LMP_CO_BB':('As7h3d','Jh9d6s','4s4h2d'),
 'SB_BB':('KsQh4d','9s6h3d','As7h3d','Jh9d6s'),
 'BTN_BB':('As7h3d','Jh9d6s','8s8h3d','KsQh4d'),
 'CO_BB':('As7h3d','KsQh4d','9s6h3d'),
 'SB3_BTN':('As7h3d','Jh9d6s','9s6h3d')
}
def main():
    root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'data')
    out=pathlib.Path(sys.argv[2] if len(sys.argv)>2 else 'data/nl2_hu_highfreq_shortfalls.json')
    rank=json.loads((root/'nl2_hu_multiboard_prerank.json').read_text())
    queue=json.loads((root/'nl2_hu_stage2_queue.json').read_text())
    status=json.loads((root/'nl2_hu_multiboard_status.json').read_text())
    by_id={x['model_id']:x for x in queue['records']}
    proof=[root/'solver_evidence'/('NL2_MULTIBOARD_'+x+'.json.gz') for x in ('B1','B2_PARTIAL','B2_REPAIRED_GTO','B3','B4_MICRO','B5_SBGAPS','B6_REMAIN','B7_RIVER','B8_LOCK','B9_LMP_FAST','B10_RIVER_EXP','B11_RIVER_FAST','B12_LOCK_FAST','B13_LMP_B50','B14_FOCUS_EXP','B15_GTO_PARENT_EXP','B16_GTO_PARENT_TWO','B17_RIVER_PINNED','B18_RIVERPAIR','B19_LMP50_RESTRICTED','B20_B66_GTO','B22_B66_EXP','B23_LMP_NEXT','B25_LMP_TEXTURES','B26_LMP_NONPAIRED','B29_OFFICIAL_RELOCK','B32_BTN_RELOCK','B33_BTN_XB50_XX','B36_BTN_RELOCK','B37_BTN_XB50_XX','B38_BTN_IP_XX')]
    proof=[p for p in proof if p.is_file()]
    exact,locked,summ=build_source_index(root,proof)
    result=[]
    for r in rank['nodes']:
        if not r['high_frequency_priority']:continue
        m=by_id[r['model_id']]
        r.update({'preflop_text':m['preflop_text'],
                  'abstract_action_history':m['abstract_action_history']})
        refs,reason=candidates(r,exact,locked,None)
        all_flops=collections.defaultdict(list)
        for c in refs:all_flops[c['flop']].append(c)
        with_lock={f:a for f,a in all_flops.items() if any(x['nl2_locked_variants'] for x in a)}
        without_lock={f:a for f,a in all_flops.items() if not any(x['nl2_locked_variants'] for x in a)}
        ref_score={
          'rank':r['rank_by_empirically_grounded_frequency_proxy'],
          'id':r['model_id'],'family':r['family'],'spot':r['spot'],'street':r['street'],
          'original_model_spr':r['approx_spr'],
          'current_label':status['records'][r['model_id']]['label'],
          'exact_matching_flops':sorted(all_flops),
          'flops_with_hero_lock':sorted(with_lock),
          'flops_without_hero_lock':sorted(without_lock),
          'distinct_matching_gto_flop_count':len(all_flops),
          'distinct_gto_plus_hero_lock_count':len(with_lock),
          'missing_required_flops':max(0,3-len(with_lock)),
          'texture_labels_seen':sorted({texture(x) for x in with_lock}),
          'recorded_line_examples':[
              {'flop':f,'source_run_id':a[0]['source_run_id'],
               'node_spr':a[0]['actual_spr'],
               'line':a[0]['actual_exact_action_line'],
               'lock_count':len(a[0]['nl2_locked_variants'])}
              for f,a in list(all_flops.items())[:6]],
          'upcoming_preregistered_board_examples':[
              x for x in CANDIDATE_FLOPS.get(r['spot'],())
              if x not in all_flops][:4],
          'unproven_until_gto_and_hero_lock_solved':True,
          'no_source_match_reason':reason
        }
        result.append(ref_score)
    assert len(result)==24
    topmissing=[x for x in result if x['current_label']=='APPROX']
    target_spots=collections.Counter(x['spot'] for x in topmissing)
    result.sort(key=lambda x:x['rank'])
    data={
     'schema':'NL2_TOP24_FROZEN_MULTIBOARD_SHORTFALLS_V1',
     'top24':24,'certified_from_source':24-len(topmissing),
     'still_approx':len(topmissing),
     'new_source_batches':[p.name for p in proof],
     'sources':summ,
     'missing_by_spot':dict(target_spots),
     'recommendation':'Solve a few new exact flops ONLY where action history, actual SPR, actor, sequential legal combos, and hero-side NL2 lock can be matched; never grant CERT from texture alone.',
     'ranking_locked':True,
     'rows':result
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'top24':24,'certified':24-len(topmissing),
                      'pending':len(topmissing),'by_spot':dict(target_spots),
                      'closest':sorted(topmissing,key=lambda x:(x['missing_required_flops'],x['rank']))[:6]},ensure_ascii=False))
if __name__=='__main__':main()
