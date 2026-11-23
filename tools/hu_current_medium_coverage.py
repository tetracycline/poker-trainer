"""Audit the available half-pot actions and measured opponent locks on every active named board."""
import argparse
from collections import Counter
import json
from pathlib import Path

from hu_apply_cert_extensions import verify_case
from hu_medium_policy_usage import medium_usage, comparison_counts
from hu_board_reach_corrections import read_replays, source_key, summarize


def decision(model, board, lock, pins, sources):
    version = lock['version'] if lock else 'gto'
    run, digest = ((lock['run_id'],lock['sha256']) if lock else (board['source_run_id'],board['source_sha256']))
    key = dict(public_board=board['public_board'], line=board['actual_exact_action_line'],
               acting_seat=board['acting_seat'], source_run_id=run, source_sha256=digest)
    raw = sources.get(source_key(model['model_id'],key))
    if raw is not None:
        summary = summarize(raw)
        assert raw['status']=='POSITIVE_JOINT_REACH' and raw['version']==version
        actions = raw['source_actions']
        combos, pairs = raw['strict_legal_combos'],raw['compatible_hole_card_pairs']
        eligible = summary['medium_50pct_eligible_combos']
        candidate = summary['b50_nonpolarized_relative_equity_research_candidate']
    else:
        pin, = [p for p in pins if p['public_board']==board['public_board'] and p['original_GTO_SHA256']==board['source_sha256']]
        prefix = 'locked_' if lock and 'locked_viewer_archive_code' in pin else ''
        side = 'NL2' if lock else 'GTO'
        assert not lock or pin['actual_NL2_SHA256']==digest
        combos,pairs=pin[side+'_strict_combos'], pin[side+'_compatible_hole_card_pairs']
        _, node = verify_case(pin[prefix+'viewer_archive_code'],pin[prefix+'viewer_sha256'],run,model,board,version,digest,combos)
        actions=node['source_actions']
        eligible=node['medium_50pct_eligible_combos']
        candidate=node['b50_nonpolarized_relative_equity_research_candidate']
    assert pairs>=combos>0 and 0<=eligible<=combos
    assert 'b50' in actions or (eligible==0 and not candidate)
    published = lock or board
    assert (eligible,candidate)==(published['medium_50pct_eligible_combos'],published['b50_nonpolarized_relative_equity_research_candidate'])
    result=dict(version=version,run=run,sha256=digest,actions=actions,legal_combos=combos,
                compatible_pairs=pairs,half_pot_eligible_combos=eligible,nonpolarized_candidate=candidate)
    if raw and 'short_stack_all_in' in raw:
        all_in = raw['short_stack_all_in']
        assert (all_in['version'], all_in['action'], all_in['pot_chips'], all_in['all_in_chips']) == (
            version, 'a', round(board['actual_pot_bb']*100), round(board['actual_effective_stack_bb']*100))
        assert actions == ['x','a'] and all_in['compatible_pairs'] == pairs and all_in['eligible_combos'] <= combos
        result['short_stack_all_in'] = all_in
    if lock:
        assert version==('exp_ip' if board['acting_seat'] else 'exp_oop')
        result.update(measured_nodes=lock['observed_marginal_source_nodes'],
                      assumed_nodes=lock['assumed_default_source_nodes'],unmatched_nodes=lock['unlocked_source_nodes'])
    return result


def coverage(registry):
    _, locked, gto, _ = read_replays()
    alternatives={}
    for path in sorted(Path('data').glob('nl2_hu_b*_half_pot_leads.json')):
        report=json.loads(path.read_bytes())
        for row in report['records']:
            key=(row['model_id'],row['public_board'],row['line'],row['seat'],row['original_gto_run'],row['original_gto_sha256'])
            assert key not in alternatives
            alternatives[key]=row
    frozen_path=Path('data/nl2_hu_b561_frozen_river.json')
    frozen=json.loads(frozen_path.read_bytes()) if frozen_path.exists() else None
    restricted_path=Path('data/nl2_hu_b573_restricted_turn.json')
    restricted=json.loads(restricted_path.read_bytes()) if restricted_path.exists() else None
    boards=[]
    for model in sorted(registry['records'].values(),key=lambda m:m['frequency_rank']):
        if model['label']!='CERT-MULTIBOARD':
            continue
        mid=model['model_id']
        pins=registry['exact_source_extensions'].get(mid,[])
        for board in model['certified_3_to_5_exact_flop_boards']:
            original=decision(model,board,None,pins,gto)
            policies=[decision(model,board,lock,pins,locked) for lock in board['nl2_locked_variants']]
            assert any(p['measured_nodes']>0 for p in policies)
            pot,stack=board['actual_pot_bb'],board['actual_effective_stack_bb']
            row=dict(rank=model['frequency_rank'],model_id=mid,public_board=board['public_board'],
                     line=board['actual_exact_action_line'],seat=board['acting_seat'],pot_bb=pot,stack_bb=stack,
                     gto=original,opponent_locks=policies)
            alt=None
            if 'b50' in original['actions']:
                row['half_pot_status']='NATIVE_ACTION'
            elif stack<pot/2:
                assert 'a' in original['actions']
                row['half_pot_status']='EXCEEDS_EFFECTIVE_STACK'
            else:
                alt=alternatives.get((mid,row['public_board'],row['line'],row['seat'],original['run'],original['sha256']))
                if alt and (alt['original_lock_run'],alt['original_lock_sha256']) in {(p['run'],p['sha256']) for p in policies}:
                    row['half_pot_status']='CONDITIONAL_'+alt['status']
                    row['conditional_run']=alt['source_run_id']
                    if frozen and (frozen['model_id'],frozen['public_board'],frozen['line'],frozen['seat'])==(mid,row['public_board'],row['line'],row['seat']):
                        assert frozen['schema']=='NL2_HU_B561_FROZEN_RIVER_V1'
                        assert frozen['full_turn_alternative_run']==alt['source_run_id'] and frozen['full_turn_status']==alt['status']=='ZERO_JOINT_REACH'
                        assert (frozen['original_run'],frozen['pot_bb'],frozen['stack_bb'])==(original['run'],pot,stack)
                        refs=frozen['policies']
                        assert refs['gto']['original']['original_source_sha256']==original['sha256']
                        lock,=(p for p in policies if p['sha256']==refs['exp_oop']['original']['original_source_sha256'] and p['run']==frozen['original_run'])
                        for policy,baseline in [(refs['gto'],original),(refs['exp_oop'],lock)]:
                            assert (policy['strict_legal_combos'],policy['compatible_pairs'])==(baseline['legal_combos'],baseline['compatible_pairs'])
                            assert policy['actions']==['x','b50'] and 0<policy['half_pot_pairs']<=policy['compatible_pairs']
                            assert 0<policy['b50']['eligible']<=policy['strict_legal_combos'] and not policy['b50']['candidate']
                        row['full_turn_half_pot_status']=row['half_pot_status']
                        row['half_pot_status']='CONDITIONAL_FROZEN_RIVER_BOTH_POSITIVE'
                        row['frozen_river_run']=frozen['run']
                    if alt['status']=='BOTH_POSITIVE':
                        assert all(alt[v]['compatible_hole_card_pairs']>=alt[v]['strict_legal_combos']>0 and
                                   'b50' in alt[v]['source_actions'] for v in ('gto','exp_oop'))
                else:
                    row['half_pot_status']='NO_MATCHING_CONDITIONAL_SOURCE'
            if restricted and (mid,row['public_board'],row['line'],row['seat']) == (
                    restricted['model_id'], restricted['public_board'], restricted['line'], restricted['seat']):
                parent_ids={(p['version'],p['run'],p['sha256']) for p in [original,*policies]}
                if all((v,restricted['source_run'],p['parent']['source_sha256']) in parent_ids
                       for v,p in restricted['policies'].items()):
                    assert all(p['original_half_pot_eligible']==0 and p['half_pot_reply_pairs']>0
                               for p in restricted['policies'].values())
                    row['restricted_turn_half_pot']={v:dict(source_sha256=p['source_sha256'],
                        archive_sha256=restricted['archive_sha256'], eligible_combos=p['half_pot']['eligible'],
                        nonpolarized_candidate=p['half_pot']['candidate']) for v,p in restricted['policies'].items()}
            row['medium_policy_usage']=medium_usage(row, alt, frozen)
            boards.append(row)
    totals=dict(Counter(r['half_pot_status'] for r in boards))
    assert len(boards)==registry['all_cert_lock_medium']['named_board_proofs']
    return dict(certified_models=registry['CERT_MULTIBOARD'],named_boards=len(boards),half_pot_status=totals,
                medium_action_eligible=comparison_counts(boards,'eligible_policy_comparison'),
                nonpolarized_candidate=comparison_counts(boards,'nonpolarized_policy_comparison'),boards=boards)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    current=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())
    report=coverage(current)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='boards'}))
