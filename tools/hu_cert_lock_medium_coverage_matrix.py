#!/usr/bin/env python3
"""Evidence-only per-CERT named-board hero lock provenance / medium-size matrix.

Requires verified registry, preserving UNKNOWN vs measured vs assumed.
A frozen source's pooled NL2 marginal is *not* the conditional private-card
policy of a particular villain on this board. This script changes no CERT.
"""
import collections,json,pathlib
from hu_cert_lock_medium_audit import audit

ROOT=pathlib.Path('data')
OUT=ROOT/'nl2_hu_cert_lock_medium_matrix.json'
MD=pathlib.Path('docs/NL2_HU_CERT_LOCK_MEDIUM_MATRIX.md')

def to_integer_or_unknown(value):
    if value is None:return None
    value=int(value)
    if value<0:raise ValueError('Negative opponent node provenance')
    return value

def create(status):
    ref=audit(status)
    rows=[];counter=collections.Counter();models={}
    certified=sorted((z for z in status['records'].values()
        if z['label']=='CERT-MULTIBOARD'),key=lambda x:x['frequency_rank'])
    for node in certified:
        model_id=node['model_id']
        board_rows=[]
        for sample in node['certified_3_to_5_exact_flop_boards']:
            locks=[]
            for x in sample['nl2_locked_variants']:
                counts=dict(
                   observed_marginal=to_integer_or_unknown(x.get('observed_marginal_source_nodes')),
                   assumed_default=to_integer_or_unknown(x.get('assumed_default_source_nodes')),
                   unmatched_unlocked=to_integer_or_unknown(x.get('unlocked_source_nodes')))
                if all(v is None for v in counts.values()):
                    kind='HISTORICAL_POOL_MARGINAL_SOURCE_COUNTS_UNKNOWN'
                    share=None
                else:
                    if any(v is None for v in counts.values()):
                        raise ValueError('Partially missing lock source counts '+model_id)
                    denom=sum(counts.values())
                    share=round(100*counts['observed_marginal']/denom,3) if denom else None
                    kind='MIXED_SOURCE_NL2_MARGINAL_PROXY'
                    counter['observed_marginal_pattern_nodes']+=counts['observed_marginal']
                    counter['assumed_pattern_nodes']+=counts['assumed_default']
                    counter['unmatched_opponent_nodes']+=counts['unmatched_unlocked']
                source_scope=x['source_scope']
                if 'TURN_ONLY' in source_scope:
                    lock_scope='DOWNSTREAM_TURN_RIVER_ONLY'
                    counter['turn_river_only_locks']+=1
                else:
                    lock_scope='PARTIALLY_LOCKED_SOURCE'
                entry=dict(
                    version=x['version'],source_scope=source_scope,lock_scope=lock_scope,
                    source_run_id=x['run_id'],source_sha256=x['sha256'],
                    aggregate_NL2_pool_coverage_pct=x.get('villain_observed_pattern_node_share_pct'),
                    source_node_counts=counts,
                    observed_fraction_of_source_nodes_pct=share,
                    node_rate_data_status=kind,
                    any_disclosed_default=bool(x.get('unknown_history_frequency_filled_with_default')),
                    EV_is_model_estimate_not_real_winnings=True,
                    hero_model_gain_bb=x.get('hero_model_gain_bb'))
                locks.append(entry)
                counter['hero_lock_variants']+=1
                counter['lock_variants_with_default_flag']+=int(entry['any_disclosed_default'])
            medium=bool(sample.get('b50_nonpolarized_relative_equity_research_candidate'))
            eligible=int(sample.get('medium_50pct_eligible_combos') or 0)
            if medium and eligible<=0:
                raise ValueError('Unreachable medium-size action improperly labeled on '+model_id)
            line=dict(model_id=model_id,rank=node['frequency_rank'],
                pot_family=node['family'],spot=node['solver_profile'],street=node['street'],
                flop=sample['flop'],turn=sample['turn'],
                exact_public_board=sample['public_board'],
                exact_action_line=sample['actual_exact_action_line'],
                actor_seat=sample['acting_seat'],actual_spr=sample['actual_spr'],
                estimated_model_spr=node['assumed_model_node_spr'],
                spr_relative_error_pct=sample['relative_spr_error_pct'],
                genuine_GTO_exploitability_pct=sample['genuine_gto_exploitability_pct'],
                strictly_reachable_combo_count=sample['strict_full_street_combo_reachable'],
                GTO_run_id=sample['source_run_id'],GTO_sha256=sample['source_sha256'],
                original_source_kind=sample['source_kind'],
                assumed_preflop_ranges=bool(sample['assumed_preflop_ranges']),
                hero_lock_proofs=locks,
                b50_eligible_combo_count=eligible,
                b50_research_status=('EXACT_BOARD_NONPOLARIZED_RESEARCH_CANDIDATE' if medium
                    else 'NOT_SUPPORTED_BY_CURRENT_EXACT_BOARD_EVIDENCE'),
                generic_handclass_texture_policy_is_not_GTO=True,
                no_general_bet_size_recommendation=True)
            if not locks or sample['strict_full_street_combo_reachable']<=0:
                raise ValueError('Missing already certified raw source for '+model_id)
            board_rows.append(line);rows.append(line)
            counter['named_board_proofs']+=1
            counter['b50_research_candidate_boards']+=int(medium)
        if not 3<=len(board_rows)<=5:
            raise ValueError('Current CERT no longer has 3–5 representative named boards')
        models[model_id]=dict(rank=node['frequency_rank'],source_spot=node['solver_profile'],
            example_count=len(board_rows),
            medium_research_examples=sum(x['b50_research_status'].startswith('EXACT_BOARD') for x in board_rows),
            with_only_downstream_locked_proofs=sum(
                any(x['lock_scope']=='DOWNSTREAM_TURN_RIVER_ONLY' for x in y['hero_lock_proofs'])
                for y in board_rows))
    if not(counter['named_board_proofs']==ref['aggregate']['named_board_proofs']
           and counter['hero_lock_variants']==ref['aggregate']['paired_hero_locked_source_variants']
           and counter['b50_research_candidate_boards']==ref['aggregate']['board_examples_with_b50_candidate']
           and counter['observed_marginal_pattern_nodes']==ref['aggregate']['source_nodes_from_measured_NL2_marginals']
           and counter['assumed_pattern_nodes']==ref['aggregate']['source_nodes_from_assumed_defaults']
           and counter['unmatched_opponent_nodes']==ref['aggregate']['source_villain_nodes_unmatched_unlocked']):
        raise ValueError('Per-board matrix does not match independently audited CERT aggregates')
    if len(models)!=status['CERT_MULTIBOARD']:
        raise ValueError('All CERT models must be represented')
    return dict(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V1',
        model_count=392,CERT_MULTIBOARD=status['CERT_MULTIBOARD'],
        APPROX=status['APPROX'],EST=0,
        strict_aggregate=dict(counter),models=models,boards=rows,
        policy=dict(
            observed='Observed aggregate NL2 frequencies by street/bet-size only, NOT board-specific conditional or private-card villain decisions',
            assumed='If no measured applicable rate, preserve ASSUMED flags; do not treat as observed',
            unknown='Historical sources may lack per-node observed/assumed denominators, encode null not zero',
            nonpolarized='50% pot label is exact named-board research only, NOT all textures or general hand classes',
            scope='GTO parent plus genuine downstream turn/river partial lock is NOT whole-flop NL2-lock GTO',
            outcome='No realized NL2 win rate or external EV validation implied'))

def write_md(out):
    lines=['# Exact NL2 CERT source: node-lock coverage and 50% pot research status',
     '', 'Draft PR #2. Never merge from this report.',
     'Every row below is a **named true public board** with a solver run/SHA.',
     'Opponent action rates refer only to **observed NL2 pool marginals**, not per-board/private-hand conditional behavior.',
     'Unknown historical per-node source counts remain unknown; defaults and unmatched villain nodes are separately counted.',
     '50% pot is a research candidate on the named runout, not a universal bet size recommendation.',
     '',
     f"Verified: {out['CERT_MULTIBOARD']} CERT / {out['APPROX']} APPROX; {len(out['boards'])} named boards.",
     '',
     '| rank | model | named board proof | GTO run | lock run(s) | measured / assumed / unlocked nodes | 50% pot |',
     '| ---: | --- | --- | ---: | --- | --- | --- |']
    for b in sorted(out['boards'],key=lambda x:(x['rank'],x['flop'],x['turn'])):
        lk=b['hero_lock_proofs'];n=lk[0]['source_node_counts']
        measured='unknown' if n['observed_marginal'] is None else (
            str(n['observed_marginal'])+'/'+str(n['assumed_default'])+'/'+str(n['unmatched_unlocked']))
        status=('candidate' if b['b50_research_status'].startswith('EXACT_BOARD') else 'unproven')
        lockruns=','.join(str(x['source_run_id']) for x in lk)
        lines.append(f"| {b['rank']} | {b['model_id']} | {b['flop']} {b['turn']} | {b['GTO_run_id']} | {lockruns} | {measured} | {status} |")
    lines.extend(['','No CERT from generic texture mapping or unsupported downstream action lines.',''])
    return '\n'.join(lines)

def main():
    source=json.loads((ROOT/'nl2_hu_multiboard_status.json').read_text())
    result=create(source)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    MD.parent.mkdir(parents=True,exist_ok=True)
    MD.write_text(write_md(result))
    print(json.dumps(dict(CERT=result['CERT_MULTIBOARD'],APPROX=result['APPROX'],
          boards=len(result['boards']),aggregate=result['strict_aggregate']),ensure_ascii=False))
if __name__=='__main__':main()
