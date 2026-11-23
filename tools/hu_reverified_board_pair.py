"""Export a named GTO/hero-lock pair after independent, two-seat reach replay."""
import base64
import gzip

from hu_b467_river_source_gate import EVIDENCE, compact, sha
from hu_sequential_cfr_reach import cardkey, compatible_node_reach, game_reach
from verify_hu_multiboard_100bb import lock_scope, locked_model_gain, source_nodes


def source_case(model, source, public, line, seat):
    root,sub,m = source['root'],source['subgame'],source['manifest']
    if sub is None:
        return None
    version=source['version']
    assert m['spot']==model['solver_profile'] and m['pot_family']==model['family']
    assert version=='gto' or version==('exp_ip' if seat else 'exp_oop')
    assert 0<=sub['info']['gto_expl_pct']<=.5 and 0<=root['info']['gto_expl_pct']<=.5
    if version!='gto':
        assert 0<=sub['info']['hero_gap_pct']<=.5 and 0<=root['info']['hero_gap_pct']<=.5
    matches=[n for n in sub['nodes'] if (n['board'],n['line'],n['player'])==(public,line,seat)]
    if not matches:return None
    node,=matches
    key='|'.join((public,line,str(seat)))
    reach=compatible_node_reach(root,sub,node,game_reach(root,sub)[0][key])
    if not reach['compatible_hole_card_pairs'] or not reach['count']:return None
    derived,=source_nodes(dict(sub,nodes=[node]),{'nodes':{key:reach}})
    assert abs(derived['node_spr']/model['assumed_model_node_spr']-1)<=.05
    mask=base64.b64decode(reach['mask'],validate=True)
    hands={cardkey(h) for h,actions in zip(sub['hands'][seat],mask,strict=True) if actions}
    assert len(hands)==reach['count']==derived['strictly_reachable_combos']
    scope=lock_scope(sub,m['locks'],version)
    if version!='gto':assert scope['observed_marginal_source_nodes']>0
    c=dict(spot=m['spot'],pot_family=m['pot_family'],version=version,source_sha256=source['source_sha256'],
           flop=sub['flop'],turn=sub['turn'],flop_line=sub['line0'],hands_by_seat=sub['hands'],nodes=[derived],
           gto_exploitability_pct=sub['info']['gto_expl_pct'],locked_hero_gap_pct=sub['info'].get('hero_gap_pct'),
           villain_lock_scope=scope)
    return c,hands,reach['compatible_hole_card_pairs']


def emit_board(model,gto,lock,public_board,line,texture):
    """Return (board, pin) on success or (None, None) when either original lacks a compatible deal."""
    seat=int(lock['version']=='exp_ip')
    assert gto['version']=='gto' and lock['version'] in ('exp_ip','exp_oop')
    both=[source_case(model,s,public_board,line,seat) for s in (gto,lock)]
    if any(c is None for c in both):return None,None
    (g,gh,gpairs),(e,eh,epairs)=both
    n,en=g['nodes'][0],e['nodes'][0]
    assert all(g[k]==e[k] for k in ('spot','pot_family','flop','turn','flop_line'))
    assert all(n[k]==en[k] for k in ('public_board','exact_node_line','acting_seat','pot_bb','remaining_bb','node_spr'))
    run,locked_run=gto['run'],lock['run']
    rank=model['frequency_rank'];flop=g['flop']
    def publish(source,cases):
        code=f'REVERIFIED_R{rank}_{source["run"]}_{flop}'
        bundle=dict(schema='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1',source_run_id=source['run'],
                    original_archive_sha256=source['archive_sha256'],errors=[],no_generic_texture_certification=True,artifacts=[dict(cases=cases)])
        blob=gzip.compress(compact(bundle),mtime=0)
        (EVIDENCE/f'NL2_MULTIBOARD_{code}.json.gz').write_bytes(blob)
        return code,sha(blob)
    code,digest=publish(gto,[g,e] if run==locked_run else [g])
    scope=e['villain_lock_scope']
    variant=dict(version=e['version'],run_id=locked_run,sha256=e['source_sha256'],source_scope='PARTIALLY_LOCKED_NL2_MARGINAL_PROXY',
                 observed_marginal_source_nodes=scope['observed_marginal_source_nodes'],assumed_default_source_nodes=scope['imputed_assumption_nodes'],
                 unlocked_source_nodes=scope['unmatched_nodes'],unknown_history_frequency_filled_with_default=bool(scope['imputed_assumption_nodes']),
                 source_not_real_per_combo_observation=True,villain_observed_pattern_node_share_pct=scope['coverage_pct'],
                 true_hero_gap_pct=e['locked_hero_gap_pct'],hero_model_gain_bb=locked_model_gain(lock['subgame'],e['version']),
                 medium_50pct_eligible_combos=en['medium_50pct_eligible_combos'],
                 b50_nonpolarized_relative_equity_research_candidate=en['b50_nonpolarized_relative_equity_research_candidate'])
    assumed=model['family'] in ('LMP','ISO')
    spr=model['assumed_model_node_spr']
    board=dict(flop=flop,turn=g['turn'],public_board=public_board,actual_exact_action_line=line,acting_seat=seat,
               exact_flop_action=g['flop_line'],actual_pot_bb=n['pot_bb'],actual_effective_stack_bb=n['remaining_bb'],actual_spr=n['node_spr'],
               model_assumed_spr=spr,relative_spr_error_pct=round(100*abs(n['node_spr']/spr-1),6),
               genuine_gto_exploitability_pct=g['gto_exploitability_pct'],source_run_id=run,source_sha256=g['source_sha256'],
               source_kind='ASSUMED_PREFLOP_RANGES' if assumed else 'PINNED_PREFLOP_CFR',assumed_preflop_ranges=assumed,
               exact_combo_reachable=n['source_reachable_combos'],strict_full_street_combo_reachable=len(gh),exact_node_actions=n['source_actions'],
               medium_50pct_eligible_combos=n['medium_50pct_eligible_combos'],b50_nonpolarized_relative_equity_research_candidate=n['b50_nonpolarized_relative_equity_research_candidate'],
               nl2_locked_variants=[variant],flop_texture=texture)
    pin=dict(flop=flop,turn=g['turn'],public_board=public_board,source_run_id=run,archive_code=gto['archive_code'],
             archive_sha256=gto['archive_sha256'],viewer_archive_code=code,viewer_sha256=digest,
             original_GTO_SHA256=g['source_sha256'],actual_NL2_SHA256=e['source_sha256'],actual_spr=n['node_spr'],
             GTO_strict_combos=len(gh),NL2_strict_combos=len(eh),GTO_compatible_hole_card_pairs=gpairs,
             NL2_compatible_hole_card_pairs=epairs,common_legal_hero_combos=len(gh&eh),pool_observed_marginal_lock_nodes=scope['observed_marginal_source_nodes'],
             pool_assumed_lock_nodes=scope['imputed_assumption_nodes'],pool_unlocked_nodes=scope['unmatched_nodes'],
             medium50_exact_research_candidate=n['b50_nonpolarized_relative_equity_research_candidate'],
             locked_original_archive_code=lock['archive_code'],locked_original_archive_sha256=lock['archive_sha256'])
    if len(public_board)==10:board['river']=pin['river']=public_board[-2:]
    if run!=locked_run:
        lc,ls=publish(lock,[e]);pin.update(locked_viewer_archive_code=lc,locked_viewer_sha256=ls,locked_source_run_id=locked_run)
    return board,pin
