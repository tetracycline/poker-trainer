#!/usr/bin/env python3
"""Cross-check ALL CERT named-board UI rows against the source-verified
24/392 model registry and the measured/assumed/unknown node-lock ledger.

Fails closed: no invented opponent private-card behavior; b50 is research
evidence on a named exact runout only, not a training-wide bet policy.
"""
import collections, hashlib, json, pathlib

DATA=pathlib.Path('data')
REG=DATA/'nl2_hu_multiboard_status.json'
MATRIX=DATA/'nl2_hu_cert_lock_medium_matrix.json'
OUT=DATA/'nl2_hu_cert_ui_completeness_gate.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    s=json.loads(REG.read_text())
    m=json.loads(MATRIX.read_text())
    assert s['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V1'
    assert s['TOTAL']==392 and s['CERT_MULTIBOARD']==24 and s['APPROX']==368
    assert m['schema']=='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V1'
    assert m['CERT_MULTIBOARD']==24 and m['APPROX']==368
    assert len(s['records'])==392 and len(m['models'])==24
    cert={key:value for key,value in s['records'].items() if value['label']=='CERT-MULTIBOARD'}
    approx={key:value for key,value in s['records'].items() if value['label']=='APPROX'}
    assert len(cert)==24 and len(approx)==368
    assert {v['frequency_rank'] for v in cert.values()}==set(range(1,25))
    if any(v['high_frequency_preregistered'] for v in approx.values()):
        raise ValueError('Frozen top 24 includes an unproven APPROX row')
    expected={};scope=collections.Counter();low_reach=[];source_runs=set()
    for model_id,model in cert.items():
        boards=model['certified_3_to_5_exact_flop_boards']
        assert 3<=len(boards)<=5 and len({x['flop'] for x in boards})==len(boards)
        assert model_id in m['models'] and m['models'][model_id]['example_count']==len(boards)
        for b in boards:
            key=(model_id,b['flop'],b['turn'],b['public_board'],b['actual_exact_action_line'])
            if key in expected:raise ValueError('Duplicated named board '+str(key))
            expected[key]=b
            assert b['strict_full_street_combo_reachable']>=1
            assert b['genuine_gto_exploitability_pct']<=.5
            assert b['relative_spr_error_pct']<=5
            assert len(b['source_sha256'])==64
            assert b['nl2_locked_variants'] and all(len(v['sha256'])==64 for v in b['nl2_locked_variants'])
            if b['strict_full_street_combo_reachable']<10:
                low_reach.append(dict(model_id=model_id,flop=b['flop'],
                   turn=b['turn'],combos=b['strict_full_street_combo_reachable']))
            source_runs.add(b['source_run_id'])
            for lock in b['nl2_locked_variants']:
                source_runs.add(lock['run_id'])
            scope['named_board_rows']+=1
            scope['hero_lock_sources']+=len(b['nl2_locked_variants'])
            scope['b50_research_candidates']+=int(b['b50_nonpolarized_relative_equity_research_candidate'])
            scope['assumed_preflop_named_boards']+=int(b['assumed_preflop_ranges'])
    actual={}
    for b in m['boards']:
        key=(b['model_id'],b['flop'],b['turn'],b['exact_public_board'],b['exact_action_line'])
        if key in actual:raise ValueError('Duplicate UI matrix row '+str(key))
        actual[key]=b
        if key not in expected:raise ValueError('Matrix certifies unknown exact board '+str(key))
        src=expected[key]
        if b['GTO_sha256']!=src['source_sha256'] or b['GTO_run_id']!=src['source_run_id']:
            raise ValueError('UI crosswalk exact GTO source differs '+str(key))
        if b['strictly_reachable_combo_count']!=src['strict_full_street_combo_reachable']:
            raise ValueError('UI crossed an actual combo reach mismatch '+str(key))
        if len(b['hero_lock_proofs'])!=len(src['nl2_locked_variants']):
            raise ValueError('Lock evidence dropped a run '+str(key))
        observed_set={(x['version'],x['run_id'],x['sha256']) for x in src['nl2_locked_variants']}
        shown_set={(x['version'],x['source_run_id'],x['source_sha256']) for x in b['hero_lock_proofs']}
        if observed_set!=shown_set:raise ValueError('Wrong lock run or digest in UI '+str(key))
        for lock in b['hero_lock_proofs']:
            if 'TURN_ONLY' in lock['source_scope'] and lock['lock_scope']!='DOWNSTREAM_TURN_RIVER_ONLY':
                raise ValueError('Downstream-only lock falsely labeled whole flop')
            counts=lock['source_node_counts']
            if any(x is None for x in counts.values()):
                if not all(x is None for x in counts.values()):
                    raise ValueError('Partially unknown source counts are misleading')
                scope['unknown_legacy_lock_variants']+=1
            elif any(x<0 for x in counts.values()):
                raise ValueError('Negative node provenance')
        if (b['b50_research_status']=='EXACT_BOARD_NONPOLARIZED_RESEARCH_CANDIDATE') != bool(src['b50_nonpolarized_relative_equity_research_candidate']):
            raise ValueError('Wrong nonpolarized b50 label')
        if b['b50_research_status'].startswith('EXACT_BOARD') and b['b50_eligible_combo_count']<=0:
            raise ValueError('Unreachable 50pct recommendation')
        if b['generic_handclass_texture_policy_is_not_GTO'] is not True:
            raise ValueError('Generic texture GTO falsely marked')
    if set(expected)!=set(actual):
        raise ValueError('At least one CERT named board lacks a viewable provenance row')
    ag=m['strict_aggregate']
    assert scope['named_board_rows']==ag['named_board_proofs']>=88
    assert scope['hero_lock_sources']==ag['hero_lock_variants']>=96
    assert scope['b50_research_candidates']==ag['b50_research_candidate_boards']>=35
    report=dict(schema='TASK_HYBRID_B27_FULL_CERT_UI_GUARD_V1',
      parent_registry_sha256=sha(REG),parent_provenance_matrix_sha256=sha(MATRIX),
      cert_models=24,approx_models=368,est_models=0,
      named_board_coverage=f"{len(actual)}/{len(expected)}",
      node_lock_source_coverage=f"{scope['hero_lock_sources']}/{scope['hero_lock_sources']}",
      b50_nonpolarized_research_candidate_boards=scope['b50_research_candidates'],
      b50_evidence_not_supported=scope['named_board_rows']-scope['b50_research_candidates'],
      source_runs=len(source_runs),low_reach_under10_combo_examples=low_reach,
      counts=dict(scope),all_24_preregistered_top_ranked_models_certified=True,
      all_cert_boards_have_exact_source_and_hero_lock=True,
      b50_never_generalized_beyond_named_public_board=True,
      observed_NL2_marginal_does_not_mean_conditional_hand_data=True,
      assumed_169_LMP_starting_ranges_are_not_empirical_NL2=True,
      downstream_partial_lock_is_not_full_flop_lock=True,
      draft_PR_never_merge=True)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('PASS B27 true per-board gate',json.dumps({
        'CERT':report['cert_models'],'APPROX':report['approx_models'],
        'boards':len(actual),'hero_lock_sources':scope['hero_lock_sources'],
        'b50_research':scope['b50_research_candidates'],
        'unsupported_b50':report['b50_evidence_not_supported'],
        'low_reach':len(low_reach)},ensure_ascii=False))
if __name__=='__main__':main()
