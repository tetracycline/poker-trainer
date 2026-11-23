"""Replay two completed rank8 source pairs and lock one additional GTO turn without changing its flop range."""
import argparse
import base64
import json
from pathlib import Path
import shutil
import subprocess
import sys

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import EVIDENCE, json_bytes, sha
from hu_b483_locked_medium import POOL
from hu_b514_turn_stab import rates
from hu_b524_rank8_bb_leads import MID, LINE, open_source
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision, load_original, replay_native, solve_native
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey

sys.path.insert(0,str(Path(__file__).resolve().parent/'lines_pipeline'))
from run10_common import hcls

RUN=45118153398
HEAD='d1b22cd54e8c5391f2ee6d9411488923979ac797'
TARGET='6d4c3h'
TURNS={'6s5h4d':'6h','7d5c4c':'9c',TARGET:'Kd'}
CODE='B542_R8_6D4C3H_KD_EXP_IP'
DATA=Path('data')


def witnesses(source, row, route):
    public=row['public_board']
    assert row['source_actions']==['x','b50','b100']
    masks=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
    result={}
    for hole,mask in zip(source['subgame']['hands'][1],masks,strict=True):
        if not mask:
            continue
        hand=''.join(cardkey(hole))
        flop_class,turn_class=hcls(hand,public[:6]),hcls(hand,public)
        action=route['turn'].get(turn_class)
        if flop_class in route['flop'] and action and mask & (1<<row['source_actions'].index(action)):
            result[hand]=dict(hand=hand,flop_class=flop_class,turn_class=turn_class,turn_action=action)
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--solver',required=True,type=Path)
    ap.add_argument('--originals',required=True,type=Path)
    ap.add_argument('--results',required=True,type=Path)
    ap.add_argument('--run',required=True,type=int)
    ap.add_argument('--driver',type=Path)
    args=ap.parse_args()
    solver=args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER and args.run>0
    if args.driver:
        assert args.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)['NL2']
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    import ranges

    route=json.loads(subprocess.check_output(['node','tools/hu_b542_rank8_turn_routes.cjs']))
    pins=json.loads((DATA/'nl2_hu_b542_rank8_originals.json').read_bytes())
    model=json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records'][MID]
    assert (model['frequency_rank'],model['street'],model['solver_profile'],model['assumed_model_node_spr'])==(8,1,'BTN_BB',8.364)
    group=dict(rank=8,model_id=MID,boards=[],pins=[])
    checks=dict(schema='NL2_B542_NATIVE_PAIRED_TURN_VERSION_V1',references={},gto_references={})
    attempts=[]
    name=f'NL2_{CODE}.json.gz'
    for flop,turn in TURNS.items():
        if args.driver and flop!=TARGET:
            continue
        public=None
        sources={}
        rows={}
        originals={}
        candidates={}
        for version,info in pins[flop].items():
            aid=info['id']
            meta=json.loads((args.originals/f'{aid}.json').read_bytes())
            assert (meta['name'],meta['digest'])==(f'B524-R8-{flop}-{version}','sha256:'+info['sha256'])
            candidates[version],_=open_source(args.originals,meta,flop,version,RUN,HEAD,pool,pipeline,ranges)
            pub,=(p for p in candidates[version] if p.endswith(turn))
            assert not public or public==pub
            public=pub
            sources[version],originals[version],rows[version]=candidates[version][public]
        if flop==TARGET:
            gi=originals['gto']
            boundary=load_original(args.originals,gi['artifact_id'],dict(name=f'B524-R8-{flop}-gto',
                run=RUN,head=HEAD,sha256=gi['artifact_sha256']),'BTN_BB',flop,turn,'gto',pot=550,stack=9750,
                flop_line='b50 c',pipeline=pipeline,ranges=ranges)
            assert witnesses(sources['gto'],rows['gto'],route)
            if args.driver:
                out=solve_native(boundary,'exp_ip',pool,pipeline,args.results,args.driver,args.run,CODE)
            else:
                out=args.results/name
            if not out.is_file():
                attempts.append(dict(flop=flop,turn=turn,status='NO_CONDITIONAL_SOURCE'))
                continue
            e=replay_native(boundary,'exp_ip',pool,pipeline,out,args.run,CODE)
            if args.driver:
                return
            info=e['subgame']['info']
            if not all(0<=info[k]<=.5 for k in ('gto_expl_pct','hero_gap_pct')):
                attempts.append(dict(flop=flop,turn=turn,status='OUTSIDE_CONDITIONAL_CONVERGENCE_GATE'))
                continue
            er=audit_decision(e,public,LINE,1,gi['root_sha256'])
            assert er and er['subgame_applied_rust_lock_nodes']>0
            sources['exp_ip'],rows['exp_ip']=e,er
        g,e=(sources[v] for v in ('gto','exp_ip'))
        gr,er=(rows[v] for v in ('gto','exp_ip'))
        gh,eh=(witnesses(sources[v],rows[v],route) for v in ('gto','exp_ip'))
        shared=[gh[h] for h in sorted(gh.keys() & eh.keys())]
        attempts.append(dict(flop=flop,public=public,rendered_shared_hands=shared,
                             gto_joint_pairs=gr['compatible_hole_card_pairs'],locked_joint_pairs=er['compatible_hole_card_pairs']))
        if not shared:
            continue
        assert all(row['b50'] and row['b50']['eligible']>0 for row in (gr,er))
        board,pin=emit_board(model,g,e,public,LINE,texture(flop))
        assert (board['actual_pot_bb'],board['actual_effective_stack_bb'])==(11,94.75)
        assert all(row['strict_legal_combos']>0 and row['compatible_hole_card_pairs']>0 for row in (gr,er))
        for v,ident in originals.items():
            shutil.copyfile(args.originals/f"{ident['artifact_id']}.zip",EVIDENCE/f"NL2_B524_R8_{flop.upper()}_{v.upper()}.zip")
        pin.update(original_gto_archive=originals['gto'],shared_rendered_action_hands=shared)
        variant=board['nl2_locked_variants'][0]
        variant.update(pool_sha256=POOL,measurement_policy='STREET_SPECIFIC_POOL_MARGINALS')
        if flop==TARGET:
            pin['native_gto_parent']=originals['gto']
            variant.update(variant_label='原始 GTO 翻牌領打範圍，轉河牌套用 NL2 分街鎖頻',
                applied_street_rates=rates(e),gto_parent_source_run_id=RUN,gto_parent_source_sha256=originals['gto']['root_sha256'],
                viewer_archive_code=pin['locked_viewer_archive_code'],viewer_sha256=pin['locked_viewer_sha256'])
            shutil.copyfile(out,EVIDENCE/name)
        else:
            pin['original_locked_archive']=originals['exp_ip']
            variant.update(variant_label='BB 翻牌領打採用實測單加注底池頻率，轉河牌使用分街鎖頻',
                           viewer_archive_code=pin['viewer_archive_code'],viewer_sha256=pin['viewer_sha256'])
        group['boards'].append(board)
        group['pins'].append(pin)
        checks['gto_references'][source_key(MID,gr)]=gr
        checks['references'][source_key(MID,er)]=er
    count=len(group['boards'])
    assert len({b['flop'] for b in group['boards']})==count<=3
    if count==3:
        (EVIDENCE/'reverified/rank8.json').write_bytes(json_bytes(group))
        (DATA/'nl2_hu_b542_locked_medium.json').write_bytes(json_bytes(checks))
    (DATA/'nl2_hu_b542_rank8_results.json').write_bytes(json_bytes(dict(run=args.run,qualifying_distinct_flops=count,
        source_run=RUN,attempts=attempts,paired_boards=group)))


if __name__=='__main__':
    main()
