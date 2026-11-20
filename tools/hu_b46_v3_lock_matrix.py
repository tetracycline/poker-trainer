#!/usr/bin/env python3
"""B46 independently audit every V3 CERT exact board: real NL2 pool-marginal
vs assumed/default vs unknown villain-node sources, and only exact-board
50% nonpolarized RESEARCH candidates. No generic bet-size recommendation.
"""
import hashlib,json,pathlib,collections
from hu_cert_lock_medium_coverage_matrix import create,write_md

ROOT=pathlib.Path('data')
SRC=ROOT/'nl2_hu_multiboard_status_v3_rank28.json'
V2=ROOT/'nl2_hu_multiboard_status_v2_tie.json'
OUT=ROOT/'nl2_hu_cert_lock_medium_matrix_v3.json'
MD=pathlib.Path('docs/NL2_HU_CERT_LOCK_MEDIUM_MATRIX_V3.md')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    src=json.loads(SRC.read_text())
    v2=json.loads(V2.read_text())
    assert src['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V3_RANK28'
    assert src['CERT_MULTIBOARD']==27 and src['APPROX']==365
    assert v2['CERT_MULTIBOARD']==26 and v2['APPROX']==366
    assert src['parent_v2_sha256']==sha(V2)
    result=create(src)
    assert result['CERT_MULTIBOARD']==27 and result['APPROX']==365 and result['model_count']==392
    assert len(result['models'])==27
    assert len(result['boards'])==101, 'B41 had 98 named boards; rank28 adds exactly three'
    a=result['strict_aggregate']
    assert a['named_board_proofs']==101
    assert a['b50_research_candidate_boards']>=39
    assert a['hero_lock_variants']>=109
    assert a['b50_research_candidate_boards']<=101
    assert all(b['hero_lock_proofs'] and b['strictly_reachable_combo_count']>0
               for b in result['boards'])
    for b in result['boards']:
        assert b['no_general_bet_size_recommendation']
        assert b['generic_handclass_texture_policy_is_not_GTO']
        assert b['b50_research_status'] in (
            'EXACT_BOARD_NONPOLARIZED_RESEARCH_CANDIDATE',
            'NOT_SUPPORTED_BY_CURRENT_EXACT_BOARD_EVIDENCE')
        if b['b50_research_status'].startswith('EXACT_BOARD'):
            assert b['b50_eligible_combo_count']>0
        for v in b['hero_lock_proofs']:
            cnt=v['source_node_counts']
            assert all(x is None for x in cnt.values()) or all(
                isinstance(x,int) and x>=0 for x in cnt.values()), 'unknown and measured cannot be conflated'
            assert v['node_rate_data_status'] in (
                'HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN',
                'MIXED_SOURCE_NL2_MARGINAL_PROXY')
            if v['node_rate_data_status'].startswith('HISTORICAL'):
                assert v['observed_fraction_of_source_nodes_pct'] is None
            assert len(v['source_sha256'])==64 and v['source_run_id']>0
    added=src['added_cert_model_id']
    rows=[b for b in result['boards'] if b['model_id']==added]
    assert len(rows)==3 and all(b['assumed_preflop_ranges'] for b in rows)
    assert all(b['original_source_kind']=='ASSUMED_PREFLOP_RANGES' for b in rows)
    assert sum(b['strictly_reachable_combo_count']<10 for b in rows)>=2
    result['schema']='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V3'
    result['source_v3_status_sha256']=sha(SRC)
    result['source_v2_unchanged_sha256']=sha(V2)
    result['frozen_Batch_E_run']=44732810327
    result['do_not_generalize_pooled_marginals_to_private_cards']=True
    result['LMP_restricted_single_50pct_flop_tree_not_unrestricted_GTO']=True
    result['never_merge_pr2']=True
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    MD.parent.mkdir(parents=True,exist_ok=True)
    MD.write_text(
      '# B46 | V3 all 27 CERT named-board NL2 locks and 50% research flags\n\n'
      'Original V1 (24/368) and V2 (26/366) retained unchanged. Current V3 27/365.\n'
      '**No generic hand-class texture becomes GTO. This is NOT investment/gambling performance validation.**\n'
      'Measured NL2 source data are pooled action-size marginals, never observed private-combo conditional actions.\n'
      'Assumed/default and unmatched opponent nodes are separately counted; historical unknown remains null.\n'
      'LMP has restricted 50%-only flop menu, assumed 169-class preflop ranges, and very thin strict reach on some boards.\n'
      'Nonpolarized 50% is a named-board RESEARCH candidate only, unsupported boards are NOT recommendations.\n\n'+
      write_md(result))
    print(json.dumps({'status':'PASS','CERT':27,'APPROX':365,
      'named_board_proofs':len(result['boards']),
      'b50_candidates':a['b50_research_candidate_boards'],
      'unsupported_50pct':len(result['boards'])-a['b50_research_candidate_boards'],
      'hero_lock_variants':a['hero_lock_variants'],
      'observed_marginal_pattern_nodes':a['observed_marginal_pattern_nodes'],
      'assumed_pattern_nodes':a['assumed_pattern_nodes'],
      'unmatched_opponent_nodes':a['unmatched_opponent_nodes']},ensure_ascii=False))

if __name__=='__main__':main()
