#!/usr/bin/env python3
"""Audit why immutable B23 LMP GTO+hero-lock games did not certify rank 1.

No ranks, rules, thresholds, trees, source results, or classification changed.
Inspect all original source nodes with the existing 5% SPR, strict full
street combo reach and exact hero-side pairing policy.
"""
import collections,gzip,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from hu_multiboard_consolidate import discover
from hu_multiboard_promote import build_source_index,candidates,hero_seat,FAM_ROOT,texture

ROOT=pathlib.Path('data')
FLOPS=('4s4h2d','9s6h3d','KsQh4d','As7h3d','Jh9d6s')
BATCH='B23_LMP_NEXT'
MODEL_ID='ln-iso-lmp_t_model-19hfq8v'
TARGET='b50 c/'

def main():
    status=json.loads((ROOT/'nl2_hu_multiboard_status.json').read_text())
    rank=json.loads((ROOT/'nl2_hu_multiboard_prerank.json').read_text())
    queue=json.loads((ROOT/'nl2_hu_stage2_queue.json').read_text())
    assert status['TOTAL']==392 and status['CERT_MULTIBOARD']+status['APPROX']==392
    record=status['records'][MODEL_ID]
    assert record['label']=='APPROX' and record['frequency_rank']==1
    r=next(z for z in rank['nodes'] if z['model_id']==MODEL_ID)
    source_model=next(z for z in queue['records'] if z['model_id']==MODEL_ID)
    r=dict(r,preflop_text=source_model['preflop_text'],
        abstract_action_history=source_model['abstract_action_history'])
    spot=r['spot'];family=r['family'];street=int(r['street'])
    seat=hero_seat(r['preflop_text'])
    assert (spot,family,street,seat)==('LMP_CO_BB','LMP',1,0)
    rootpot,rootstack=FAM_ROOT[spot]
    ready,batches=discover(ROOT)
    assert batches[BATCH]['status']=='VERIFIED'
    by_gto,by_hero_lock,summary=build_source_index(ROOT,ready)
    ix=json.loads((ROOT/'solver_evidence'/('NL2_MULTIBOARD_'+BATCH+'.index.json')).read_text())
    z=gzip.decompress((ROOT/'solver_evidence'/('NL2_MULTIBOARD_'+BATCH+'.json.gz')).read_bytes())
    archive=json.loads(z)
    assert archive['source_run_id']==ix['run_id']==44764901527
    assert not archive['errors'] and len(archive['artifacts'])==4
    archive_cases=[]
    for art in archive['artifacts']:
        item=dict(flop=art['flop'],version=art['version'],artifact=art.get('artifact'),
            cfr_cases=len(art['cases']),excluded=art.get('excludes',[]),
            cases=[])
        for case in art['cases']:
            lines=collections.Counter(
                (n['exact_node_line'],n['acting_seat'],len(n['public_board']))
                for n in case['nodes'])
            matching=[n for n in case['nodes'] if n['exact_node_line']==TARGET
                    and n['acting_seat']==seat and len(n['public_board'])==8]
            item['cases'].append(dict(
                flop_line=case['flop_line'],turn=case['turn'],
                gto_gap=case.get('gto_exploitability_pct'),
                exact_target_node_count=len(matching),
                strict_target_combos=sum(int(n['strictly_reachable_combos']) for n in matching),
                target_nodes=[dict(board=n['public_board'],spr=n['node_spr'],
                    strict_combos=n['strictly_reachable_combos'],actor=n['acting_seat'],
                    line=n['exact_node_line']) for n in matching[:8]],
                available_lines=[dict(line=k[0],actor=k[1],board_cards=k[2],count=n)
                    for k,n in lines.most_common(14)]))
        archive_cases.append(item)
    verified=[]
    for flop in FLOPS:
        for key,values in by_gto.items():
            s,f,st,hero,line=key
            if (s,f,st,hero)!=(spot,family,street,seat) or line!=TARGET:continue
            for g,n,strict,origin in values:
                if g['flop']!=flop:continue
                spr_err=abs(n['spr']-r['approx_spr'])/max(1.,n['spr'])
                root_ok=abs(g['root_pot_bb']-rootpot)<1e-6 and abs(g['root_remaining_bb']-rootstack)<1e-6
                gap_ok=g.get('gto_gap_pct') is not None and g['gto_gap_pct']<=.5
                reach_ok=strict>0 and n['reachable']>0
                board_ok=len(n['board'])==8
                k=(spot,family,g['flop'],g['turn'],g['flop_line'],
                    n['board'],n['line'],seat)
                locks=[x for x in by_hero_lock.get(k,[]) if x['version']=='exp_oop']
                ok=root_ok and gap_ok and reach_ok and board_ok and spr_err<=.05 and bool(locks)
                reasons=[str(k) for k,v in {
                    'ROOT_POSITION_OR_STACK_MISMATCH':root_ok,
                    'GTO_GAP_HIGH':gap_ok,
                    'NO_STRICT_REACHABLE_COMBOS':reach_ok,
                    'WRONG_PUBLIC_BOARD_LENGTH':board_ok,
                    'SPR_OVER_5PCT':spr_err<=.05,
                    'NO_IDENTICAL_HERO_EXP_OOP_LOCK':bool(locks)
                }.items() if not v]
                verified.append(dict(flop=flop,turn=g['turn'],board=n['board'],
                    line=n['line'],source_run=g['run_id'],source_sha256=g['sha'],
                    source_kind=g['source_kind'],origin=origin,
                    root_ok=root_ok,gto_gap=g['gto_gap_pct'],
                    node_spr=n['spr'],model_spr=r['approx_spr'],
                    spr_error_pct=round(spr_err*100,4),strict_combo_count=strict,
                    source_reachable_combo_count=n['reachable'],locked_sources=[
                      dict(run=x['run_id'],sha=x['sha'],scope=x['scope']) for x in locks],
                    valid_gto_hero_lock_pair=ok,rejection_reasons=reasons))
    filtered,reason=candidates(r,by_gto,by_hero_lock,None)
    groups={}
    for f in FLOPS:
        matches=[x for x in verified if x['flop']==f]
        art=[x for x in archive_cases if x['flop']==f]
        groups[f]=dict(texture=texture(f),
            exact_gto_nodes_at_required_actor_and_history=len(matches),
            qualified_pair_nodes=sum(x['valid_gto_hero_lock_pair'] for x in matches),
            source_inspection=art,
            candidate_rows=[dict(turn=x['turn'],spr=x['node_spr'],
                legal_combo=x['strict_combo_count'],reject=x['rejection_reasons'])
                for x in matches])
    report=dict(schema='TASK_HYBRID_B24_LMP_RANK1_RAW_B23_STRICT_MISMATCH_V1',
        original_rules_unchanged=True,rank=1,model_id=MODEL_ID,
        source_batch_run=ix['run_id'],source_sha256=ix['source_sha256'],
        model_preflop_text=r['preflop_text'],
        abstract_action_history=r['abstract_action_history'],
        target_history=TARGET,hero_actor=seat,target_spr=r['approx_spr'],
        actual_prior_source_archive_count=len(ready),frozen_rank_top24=True,
        unchanged_classification=dict(cert=status['CERT_MULTIBOARD'],
            approx=status['APPROX'],status=record['label']),
        strict_candidate_count=len(filtered),source_refusal_reason=reason,
        qualifying_distinct_flops=sorted(set(x['flop'] for x in verified
                                              if x['valid_gto_hero_lock_pair'])),
        inspected=groups,matching_exact_gto_rows=verified,
        unsupported_cards_or_histories_must_not_be_relabelled=True)
    out=ROOT/'nl2_hu_rank1_B23_strict_source_mismatch.json'
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    lines=['# Rank 1 LMP original B23 source mismatch: strict no-CERT audit','',
      'Frozen 24-high-frequency model, no rule/tolerance/SPR revisions.',
      f'Current source-verified labels: {status["CERT_MULTIBOARD"]} CERT / {status["APPROX"]} APPROX.',
      f'Expected exact hero action line: \`{TARGET}\`, required SPR {r["approx_spr"]}.',
      'Only true independent GTO and same public board/line/actor hero-lock proof can count.','',
      '| flop | texture | matching GTO node rows | qualified exact hero lock pairs |',
      '| --- | --- | ---: | ---: |']
    for flop,x in groups.items():
        lines.append(f'| {flop} | {x["texture"]} | {x["exact_gto_nodes_at_required_actor_and_history"]} | {x["qualified_pair_nodes"]} |')
    lines.extend(['','## Original source cases',''])
    for a in archive_cases:
        lines.append(f'- {a["flop"]} / {a["version"]}: {a["cfr_cases"]} source cases; '
                     f'target nodes '+str(sum(x['exact_target_node_count'] for x in a['cases'])))
    lines.extend(['','This audit does not certify any extra abstract model.',''])
    (pathlib.Path('docs')/'NL2_HU_RANK1_B23_STRICT_SOURCE_MISMATCH.md').write_text('\n'.join(lines))
    print(json.dumps({'valid_flops':report['qualifying_distinct_flops'],
        'model_CERT':status['CERT_MULTIBOARD'],
        'raw_archive_games':sum(len(x['cases']) for x in archive_cases),
        'b23_flops':{f:{'gto':v['exact_gto_nodes_at_required_actor_and_history'],
                         'paired':v['qualified_pair_nodes']} for f,v in groups.items()}},
        ensure_ascii=False))
if __name__=='__main__':main()
