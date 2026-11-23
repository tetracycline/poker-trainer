"""Audit the available half-pot actions and measured opponent locks on every active named board."""
import argparse
import hashlib
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
    restricted_rows=[json.loads(restricted_path.read_bytes())] if restricted_path.exists() else []
    for filename in ('nl2_hu_b575_delayed_cbet.json', 'nl2_hu_b578_conditional_turns.json'):
        path=Path('data') / filename
        if path.exists():
            restricted_rows.extend(json.loads(path.read_bytes())['records'])
    restricted_by_key={(r['model_id'],r['public_board'],r['line'],r['seat']):r for r in restricted_rows}
    assert len(restricted_rows)==len(restricted_by_key)
    path=Path('data/nl2_hu_b583_frozen_rivers.json')
    river_rows=json.loads(path.read_bytes())['records'] if path.exists() else []
    rivers={(r['model_id'],r['public_board'],r['line'],r['seat']):r for r in river_rows}
    assert len(rivers)==len(river_rows)
    recovery_path=Path('data/nl2_hu_b587_raw_river_weights.json')
    if recovery_path.exists():
        recovered=json.loads(recovery_path.read_bytes())
        assert recovered['base_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
        for r in recovered['records']:
            target=rivers[r['model_id'],r['public_board'],r['line'],r['seat']]
            policies=target['policies']
            p=r['policy']
            i,=(i for i,old in enumerate(policies) if old['original']==p['original'])
            assert policies[i]['status']=='UNRESOLVED_ROUNDED_BOUNDARY' and p['status']=='VERIFIED'
            assert p['prior_unresolved_output_sha256']==policies[i]['output_sha256'] and p['original_node_count']>0
            assert all(e['max_abs']==0 and e['relative_sum']==0 for e in p['range_errors'])
            policies[i]=p
    barrel_rows={}
    for barrel_file in sorted(Path('data').glob('nl2_hu_b*_rank*_barrels.json')):
        report=json.loads(barrel_file.read_bytes())
        assert report['schema'] in ('NL2_HU_B590_SB_BB_BARREL_REPLIES_V1','NL2_HU_B609_BB_PROBE_RESPONSES_V1','NL2_HU_B628_3BP_TURN_BARREL_RESPONSES_V1')
        for barrel in report['records']:
            key=(barrel['model_id'],barrel['public_board'],barrel['line'],barrel['seat'],barrel['original']['run'],barrel['original']['source_sha256'])
            assert key not in barrel_rows
            barrel_rows[key]=barrel
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
            restricted=restricted_by_key.get((mid,row['public_board'],row['line'],row['seat']))
            if restricted:
                parent_ids={(p['version'],p['run'],p['sha256']) for p in [original,*policies]}
                locked_version='exp_ip' if row['seat'] else 'exp_oop'
                lock_id=restricted.get('original_locked_sha256') or restricted['policies'][locked_version]['parent']['source_sha256']
                lock_run=restricted.get('original_locked_run', restricted['source_run'])
                if (locked_version,lock_run,lock_id) in parent_ids and all(
                        (p.get('parent_version',v),p['parent']['artifact_run'],p['parent']['source_sha256']) in parent_ids
                        for v,p in restricted['policies'].items()):
                    conditional={}
                    for version,policy in restricted['policies'].items():
                        eligible=policy['half_pot']['eligible']
                        pairs=policy['half_pot_reply_pairs']
                        assert policy['original_half_pot_eligible']==0 and policy['legal_combos']>0
                        assert 0<=eligible<=policy['legal_combos']<=policy['compatible_pairs']
                        assert 0<=pairs<=policy['compatible_pairs'] and bool(pairs)==bool(eligible)
                        conditional[version]=dict(source_sha256=policy['source_sha256'],
                            archive_sha256=restricted['archive_sha256'], eligible_combos=eligible,
                            compatible_pairs=policy['compatible_pairs'], half_pot_reply_pairs=pairs,
                            nonpolarized_candidate=policy['half_pot']['candidate'])
                    row['restricted_turn_half_pot']=conditional
            river=rivers.get((mid,row['public_board'],row['line'],row['seat']))
            if river:
                assert (river['pot_bb'],river['stack_bb'])==(pot,stack)
                ids={(p['version'],p['run'],p['sha256']) for p in [original,*policies]}
                snapshots=[]
                for p in river['policies']:
                    src=p['original']
                    if (src['version'],src['run'],src['source_sha256']) not in ids:
                        continue
                    summary=dict(version=src['version'],run=src['run'],parent_sha256=src['source_sha256'],
                                 source_sha256=p['output_sha256'],status=p['status'])
                    if p['status']=='VERIFIED':
                        assert sum(h['compatible_pairs'] for h in p['hands'])==p['compatible_pairs']
                        assert sum(h['compatible_pairs'] for h in p['hands'] if h['accepted_mask']&2)==p['half_pot_pairs']
                        assert p['b50']['eligible']==sum(bool(h['accepted_mask']&2) for h in p['hands'])
                        summary.update(eligible_combos=p['b50']['eligible'],half_pot_pairs=p['half_pot_pairs'],
                                       nonpolarized_candidate=p['b50']['candidate'])
                    else:
                        assert p['status']=='UNRESOLVED_ROUNDED_BOUNDARY' and 'hands' not in p
                    snapshots.append(summary)
                if snapshots:
                    row['frozen_river_policies']=snapshots
            barrel=barrel_rows.get((mid,row['public_board'],row['line'],row['seat'],original['run'],original['sha256']))
            if barrel:
                baseline=barrel['gto']
                conditional=barrel['locked']
                assert (baseline['compatible_pairs'],baseline['legal_combos'],baseline['half_pot']['eligible'])==(
                    original['compatible_pairs'],original['legal_combos'],original['half_pot_eligible_combos'])
                assert (baseline['compatible_pairs'],baseline['legal_combos'])==(conditional['compatible_pairs'],conditional['legal_combos'])
                assert len(conditional['eligible_hand_frequencies'])==conditional['half_pot']['eligible']
                assert (barrel['pot_bb'],barrel['stack_bb'])==(pot,stack)
                if row['line']=='x x/':
                    rule, = barrel['rules']
                    if model['solver_profile'] in ('BTN_BB','CO3_BTN'):
                        field, n = 'vs_probe', 6093 if model['family']=='3BP' else 49952
                    else:
                        field, n = 'vs_delayed_cbet', 6843 if model['family']=='3BP' else 26780
                    assert (rule['table'],rule['size'],rule['n'],rule['applied_nodes'])==(field,'all',n,2)
                elif model['solver_profile'] in ('SB3_BTN','BB3_BTN'):
                    actions=baseline['actions']
                    assert row['line']=='b75 c/' and conditional['actions']==actions==original['actions']
                    expected=[('^b75 c/b50$','34-55%',3647)]
                    if 'b100' in actions:
                        expected.append(('^b75 c/b100$','81-110%',1175))
                    assert [(r['pattern'],r['size'],r['n']) for r in barrel['rules']]==expected
                    assert all(r['table']=='vs_turn_barrel_by_size' and r['applied_nodes']==1 for r in barrel['rules'])
                else:
                    assert len(barrel['rules'])==4
                assert all(r['n']>0 and r['applied_nodes']>0 for r in barrel['rules'])
                row['measured_barrel_reply_policy']=dict(source_sha256=barrel['output_sha256'],
                    eligible_combos=conditional['half_pot']['eligible'],nonpolarized_candidate=conditional['half_pot']['candidate'],
                    legal_combos=conditional['legal_combos'],compatible_pairs=conditional['compatible_pairs'])
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
