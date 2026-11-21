#!/usr/bin/env python3
"""CERT-MULTIBOARD per-board hero lock / medium-bet proof coverage gate.

No generic cell strategy is certified. Missing or imputed opponent frequencies
remain explicitly unobserved, not empirical NL2 hole-card action data.
"""
import argparse,collections,hashlib,json,pathlib

def audit(data):
    assert data['schema'] in ('NL2_HU_392_MULTIBOARD_CERT_STATUS_V1',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V2_EQUAL_SCORE_TIE',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V3_RANK28',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V4_BATCH50',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V5_BATCH55',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V6_RANK33',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V7_BATCH59',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V8_BATCH61',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V9_RANK40_B67',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V10_BATCH69',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V11_BATCH71',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V12_BATCH73',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V13_BATCH75',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V14_BATCH77',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V15_BATCH80',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V16_BATCH82',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V17_BATCH84',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V18_BATCH86',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V19_BATCH88',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V20_BATCH90',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V21_BATCH92',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V22_BATCH94',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V23_B100_LMP_PAIR',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V24_B103_RANK43',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V25_B106_RANK135',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V26_B111_RANK215_220',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V27_B123_R41_236',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V28_B133_RANK69',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V29_B142_RANK88',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V30_B145_RANK47',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V31_B150_RANK46',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V31_B161_RANK150',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V32_B168_RANK80',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V33_B179_RANK138',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V34_B190_RANK199_202',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V35_B193_RANK201',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V36_B196_RANK159',
                              'NL2_HU_392_MULTIBOARD_CERT_STATUS_V36_B201_RANK159')
    assert data['CERT_MULTIBOARD']+data['APPROX']==data['TOTAL']==392
    models={};tot=collections.Counter();source_set=set()
    for model_id,m in data['records'].items():
        if m['label']!='CERT-MULTIBOARD':continue
        boards=m['certified_3_to_5_exact_flop_boards']
        if not 3<=len(boards)<=5 or len({b['flop'] for b in boards})!=len(boards):
            raise ValueError('Invalid GTO board count in '+model_id)
        evidence=[]
        for x in boards:
            if x['acting_seat'] not in (0,1) or x['strict_full_street_combo_reachable']<=0:
                raise ValueError('No legally reachable hero combos for '+model_id)
            if x['genuine_gto_exploitability_pct']>.5 or x['relative_spr_error_pct']>5:
                raise ValueError('No proven GTO precision and SPR match in '+model_id)
            if len(x['source_sha256'])!=64 or not x['nl2_locked_variants']:
                raise ValueError('Missing exact GTO or paired node-locked response in '+model_id)
            wanted='exp_ip' if x['acting_seat']==1 else 'exp_oop'
            valid_locked=[]
            for v in x['nl2_locked_variants']:
                if v['version']!=wanted or len(v['sha256'])!=64 or not v['run_id']:
                    raise ValueError('Unmatched villain lock, or missing verified run')
                valid_locked.append({
                   'version':v['version'],
                   'run_id':v['run_id'],
                   'source_sha256':v['sha256'],
                   'scope':v['source_scope'],
                   'pool_coverage_pct':v.get('villain_observed_pattern_node_share_pct'),
                   'used_disclosed_default':bool(v.get('unknown_history_frequency_filled_with_default')),
                   'observed_marginal_source_nodes':v.get('observed_marginal_source_nodes'),
                   'assumed_default_source_nodes':v.get('assumed_default_source_nodes'),
                   'unlocked_source_nodes':v.get('unlocked_source_nodes'),
                   'hero_model_gain_bb':v.get('hero_model_gain_bb'),
                   'model_based_not_actual_winnings':True
                })
                tot['paired_hero_locked_source_variants']+=1
                if v.get('unknown_history_frequency_filled_with_default'):
                    tot['variants_with_assumed_defaults']+=1
                if (v.get('observed_marginal_source_nodes') or 0)>0:
                    tot['variants_with_measured_aggregate_marginals']+=1
                tot['source_nodes_from_measured_NL2_marginals']+=int(v.get('observed_marginal_source_nodes') or 0)
                tot['source_nodes_from_assumed_defaults']+=int(v.get('assumed_default_source_nodes') or 0)
                tot['source_villain_nodes_unmatched_unlocked']+=int(v.get('unlocked_source_nodes') or 0)
            medium=bool(x.get('b50_nonpolarized_relative_equity_research_candidate'))
            eligible=int(x.get('medium_50pct_eligible_combos') or 0)
            if medium and eligible<=0:raise ValueError('False b50 candidate with zero combos')
            tot['named_board_proofs']+=1
            tot['board_examples_with_b50_candidate' if medium else 'board_examples_without_nonpolarized_evidence']+=1
            tot['strictly_reachable_combo_rows']+=x['strict_full_street_combo_reachable']
            source_set.add((x['source_run_id'],x['source_sha256']))
            evidence.append(dict(
               flop=x['flop'],turn=x['turn'],exact_public_board=x['public_board'],
               exact_action_line=x['actual_exact_action_line'],
               original_pot_bb=x['actual_pot_bb'],
               actual_spr=x['actual_spr'],assumed_model_spr=x['model_assumed_spr'],
               source_run_id=x['source_run_id'],source_sha256=x['source_sha256'],
               gto_exploitability_pct=x['genuine_gto_exploitability_pct'],
               strictly_reachable_combo_rows=x['strict_full_street_combo_reachable'],
               paired_NL2_hero_lock=valid_locked,
               medium_50pct_eligible_combos=eligible,
               medium_nonpolarized_status='EXACT_BOARD_RESEARCH_CANDIDATE' if medium
                 else 'NOT_SUPPORTED_BY_CURRENT_CFR_EVIDENCE',
               no_global_bet_size_recommendation=True))
        tot['models_with_3_to_5_gto_and_hero_lock_source']+=1
        models[model_id]=dict(model_id=model_id,rank=m['frequency_rank'],
               source_spot=m['solver_profile'],source_family=m['family'],
               generic_handclass_texture_actions_still_approx=True,
               verified_named_board_count=len(evidence),
               boards=evidence)
    if len(models)!=data['CERT_MULTIBOARD']:
        raise ValueError('Not all certified models were audited')
    return {
        'schema':'NL2_HYBRID_CERT_NL2_LOCK_AND_MEDIUM_PROOF_V1',
        'cert_multiboard':len(models),'approx':data['APPROX'],'EST':0,'models_total':392,
        'distinct_source_gto_cases':len(source_set),'aggregate':dict(tot),
        'source_policy':'Only true exact board, betting history, root position, pot, SPR and max/near combo reach are supported.',
        'unknown_action_rates':'Observed marginal NL2 PFR cbet-size distribution and by-size fold/raise where available; unavailable conditional rates use disclosed assumed checked-to-bet45% and 35/35/20/10. Aggregates are not exact board-history private-combo frequencies.',
        'not_actual_NL2_earnings':True,
        'not_generalized_handclass_GTO':True,
        'models':models}
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=pathlib.Path,default=pathlib.Path('data/nl2_hu_multiboard_status.json'))
    p.add_argument('--out',type=pathlib.Path,default=pathlib.Path('data/nl2_hu_cert_lock_medium_audit.json'))
    args=p.parse_args()
    report=audit(json.loads(args.source.read_text()))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'cert':report['cert_multiboard'],'approx':report['approx'],
                      'source_cases':report['distinct_source_gto_cases'],
                      'aggregate':report['aggregate']},ensure_ascii=False))
if __name__=='__main__':main()
