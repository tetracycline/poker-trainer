"""Replay both seats at a limped turn after BB checks, CO bets half pot and BB calls."""
import argparse
import json
from pathlib import Path

from hu_b467_river_source_gate import EVIDENCE, json_bytes
from hu_b496_rank71_baseline import read_source
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board, source_case

MODEL = 'ln-iso-lmp_t_model-10v4wiz'
LINE = 'x b50 c/'
FLOPS = {'3c3d4h': ('Qh','7h'), '7s5h3d': ('6c','7h'), '8s8h3d': ('5s','8d')}
VERSIONS = ('gto','exp_oop')


def inspect(source):
    root,sub=source['root'],source['subgame']
    node,=(n for n in sub['nodes'] if n['line']==LINE and n['player']==0 and len(n['board'])==8)
    public=node['board']
    reply,=(n for n in sub['nodes'] if (n['board'],n['player'],n['line'])==(public,1,LINE+'b50'))
    assert 'x' in node['acts'] and 'b50' in node['acts'] and node['pot']==500
    assert (reply['pot'],reply['bets'])==(750,[250,0])
    row=audit_decision(source,public,LINE,0,source['provenance']['original_root_sha256'])
    assert row is not None
    if row['status']=='POSITIVE_JOINT_REACH':assert row['b50'] is not None
    gaps=[root['info']['gto_expl_pct'],sub['info']['gto_expl_pct']]
    if source['version']=='exp_oop':
        gaps += [root['info']['hero_gap_pct'],sub['info']['hero_gap_pct']]
        assert row['root_applied_rust_lock_nodes']>0 and row['subgame_applied_rust_lock_nodes']>0
        assert row['lock_scope']['observed_marginal_source_nodes']>0
    return row,all(0<=gap<=.5 for gap in gaps)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('downloads',type=Path)
    parser.add_argument('--run',required=True,type=int)
    parser.add_argument('--head',required=True)
    args=parser.parse_args()
    registry=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())
    model=registry['records'][MODEL]
    assert (model['frequency_rank'],model['street'],model['solver_profile'],model['assumed_model_node_spr'])==(13,1,'LMP_CO_BB',19.3)
    infos={row['name']:row for row in json.loads((args.downloads/'run.json').read_bytes())['artifacts']}
    group=dict(model_id=MODEL,rank=13,boards=[],pins=[])
    medium=dict(schema='NL2_HU_B510_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    attempts={}
    for flop,turns in FLOPS.items():
        pair={}
        observations=attempts[flop]={}
        for version in VERSIONS:
            name=f'B510-original-{flop}-{version}'
            if name not in infos:
                observations[version]='MISSING_COMPLETED_SOLVER_ARTIFACT'
                continue
            item=infos[name]
            meta=json.loads((args.downloads/f"{item['id']}.json").read_bytes())
            assert (meta['workflow_run']['head_sha'],meta['name'],meta['digest'])==(args.head,name,item['digest'])
            pin=dict(id=item['id'],run=args.run,zip_sha256=item['digest'].removeprefix('sha256:'))
            pair[version]=read_source(args.downloads,pin,version,flop,False,flop_line='x b50 c',batch='B510')
            for s in pair[version].values():
                assert s['manifest']['turns']==list(turns)
        for turn in turns:
            if any(turn not in pair.get(v,{}) for v in VERSIONS):
                observations[turn]='NO_COMPLETED_SOURCE_PAIR'
                continue
            g,e=(pair[v][turn] for v in VERSIONS)
            gr,good_g=inspect(g)
            er,good_e=inspect(e)
            assert gr['public_board']==er['public_board'] and gr['source_actions']==er['source_actions']
            public=gr['public_board']
            obs=observations[turn]=dict(public_board=public,gto=gr,exp_oop=er)
            if not good_g or not good_e or min(gr['compatible_hole_card_pairs'],er['compatible_hole_card_pairs'])==0:
                continue
            _,gh,_=source_case(model,g,public,LINE,0)
            _,eh,_=source_case(model,e,public,LINE,0)
            obs['common_legal_bb_hands']=len(gh & eh)
            if not obs['common_legal_bb_hands']:continue
            board,pin=emit_board(model,g,e,public,LINE,texture(flop))
            assert board['actual_spr']==19.55 and pin['common_legal_hero_combos']==obs['common_legal_bb_hands']
            board['nl2_locked_variants'][0]['variant_label']='翻牌下注限半池，轉牌可領打半池或滿池，依 NL2 分街邊際頻率局部鎖頻'
            board['restricted_flop_bet_sizes_pct']=[50]
            board['turn_root_allows_lead']=True
            pin.update(gto_archive_provenance=g['provenance'],locked_archive_provenance=e['provenance'])
            group['boards'].append(board)
            group['pins'].append(pin)
            medium['references'][source_key(MODEL,er)]=er
            medium['gto_references'][source_key(MODEL,gr)]=gr
            break
    count=len(group['boards'])
    assert count==len({b['flop'] for b in group['boards']})<=3
    Path('data/nl2_hu_b510_rank13_attempts.json').write_bytes(json_bytes(dict(rank=13,model_id=MODEL,run=args.run,
        head=args.head,line=LINE,restricted_flop_bet_sizes_pct=[50],turn_leads_pct=[50,100],
        attempts=attempts,verified_flops=count,model=group)))
    if count==3:
        (EVIDENCE/'reverified/rank13.json').write_bytes(json_bytes(group))
        Path('data/nl2_hu_b510_locked_medium.json').write_bytes(json_bytes(medium))
    print(f'Rank 13: {count} verified distinct flop pairs')


if __name__=='__main__':
    main()
