"""Verify BTN river checks reached through the rendered low-flop call and middle-pair turn check."""
import argparse
import base64
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import EVIDENCE, json_bytes, sha
from hu_b483_locked_medium import POOL
from hu_b514_turn_stab import rates
from hu_b524_rank8_bb_leads import open_source
from hu_b542_rank8_original_turn import CODE as B542_CODE, HEAD, RUN, TURNS, hcls
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision, load_original, prepare_job, replay_native
from hu_multiboard_promote import texture
from hu_native_turn_result import replay, run_native
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey
from run10_common import classes

MID='ln-ipfr-r_model-nk1lkm'
LINE='b50 c/x x/x'
SOLVE_FLOP='7d5c4c'
REUSE_FLOP='6d4c3h'
SOLVE_CODE='B546_R70_7D5C4C_9C_ALL_RIVERS_'
RIVERS={'6s5h4d':['3c','4c'],SOLVE_FLOP:['Th','5s'],REUSE_FLOP:['7s','Tc']}
DATA=Path('data')


def current_texture(public):
    ranks,suits=public[::2],public[1::2]
    if max(Counter(suits).values())>=3:
        return 'mono'
    if len(set(ranks))<len(ranks):
        return 'paired'
    if 'A' in ranks:
        return 'A_high'
    if any(rank in ranks for rank in 'KQ'):
        return 'KQ_high'
    return 'mid_high' if any(rank in ranks for rank in 'JT') else 'low'


def playable_hands(src,row,route):
    assert 'b50' in row['source_actions'] and 'x' in row['source_actions']
    masks=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
    index=row['source_actions'].index('x')
    public=row['public_board']
    result={}
    for hole,mask in zip(src['subgame']['hands'][1],masks,strict=True):
        if not mask & (1<<index):
            continue
        hand=''.join(cardkey(hole))
        first,turn,river=hcls(hand,public[:6]),hcls(hand,public[:8]),classes(hand,public)[0]
        flop_row,turn_row,river_row=(current_texture(public[:n]) for n in (6,8,10))
        if (first in route[flop_row]['flop'] and turn in route[turn_row]['turn'] and
                river in route[river_row]['river'] and turn==river=='MID'):
            result[hand]=dict(hand=hand,flop=first,turn=turn,river=river,
                              flop_row=flop_row,turn_row=turn_row,river_row=river_row)
    return result


def additional_rivers(boundary):
    public=boundary['public']
    original=boundary['source']['subgame']['rivers']
    assert public=='4c5c7d9c' and original==['Th','5s']
    occupied={public[i:i+2] for i in range(0,len(public),2)}
    cards=[r+s for r in '23456789TJQKA' for s in 'cdhs' if r+s not in occupied and r+s not in original]
    assert len(cards)==46 and '3d' in cards
    return cards


def expanded_job(boundary,version,pool,pipeline):
    if version=='gto':
        job,locks=deepcopy(boundary['job']),[]
    else:
        job,locks=prepare_job(boundary,version,pool,pipeline)
    job['out']='turn.json'
    job['extract'] += [dict(prefix=['x','x',river],street=True) for river in additional_rivers(boundary)]
    return job,locks


def expanded_source(boundary,version,pool,pipeline,args):
    code=SOLVE_CODE+version.upper()
    name='NL2_'+code+'.zip'
    directory=args.results/version
    if args.driver:
        job,locks=expanded_job(boundary,version,pool,pipeline)
        run_native(directory,args.driver,boundary,job,locks,args.run,version,name)
    path=directory/name
    if not path.is_file():
        return None,None
    source=replay(boundary,version,pool,pipeline,path,args.run,code,expanded_job)
    sub=source['subgame']
    old=boundary['source']['subgame']
    sub['rivers']=list(old['rivers'])+additional_rivers(boundary)
    assert set(sub['rivers'])=={n['board'][-2:] for n in sub['nodes'] if len(n['board'])==10}
    if version=='gto':
        nodes={(n['board'],n['line'],n['player']):n for n in sub['nodes']}
        assert all(nodes[(n['board'],n['line'],n['player'])]==n for n in old['nodes'])
    return source,path


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--solver',required=True,type=Path)
    ap.add_argument('--originals',required=True,type=Path)
    ap.add_argument('--results',required=True,type=Path)
    ap.add_argument('--run',required=True,type=int)
    ap.add_argument('--driver',type=Path)
    ap.add_argument('--reuse-run',type=int)
    args=ap.parse_args()
    solver=args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER and args.run>0
    if args.driver:
        assert args.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    import ranges
    poolraw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(poolraw)==POOL
    pool=json.loads(poolraw)['NL2']
    pins=json.loads((DATA/'nl2_hu_b542_rank8_originals.json').read_bytes())
    route=json.loads(subprocess.check_output(['node','tools/hu_b546_rank70_routes.cjs']))
    model=json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records'][MID]
    assert (model['frequency_rank'],model['street'],model['solver_profile'],model['assumed_model_node_spr'])==(70,2,'BTN_BB',8.364)
    group=dict(rank=70,model_id=MID,boards=[],pins=[])
    checks=dict(schema='NL2_HU_B546_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    report=[]
    for flop,turn in TURNS.items():
        if args.driver and flop!=SOLVE_FLOP:
            continue
        case=dict(flop=flop,turn=turn,rivers={})
        report.append(case)
        original={}
        for version in (('gto','exp_ip') if flop not in (SOLVE_FLOP,REUSE_FLOP) else ('gto',)):
            pin=pins[flop][version]
            aid=pin['id']
            item=json.loads((args.originals/f'{aid}.json').read_bytes())
            assert (item['name'],item['digest'])==(f'B524-R8-{flop}-{version}','sha256:'+pin['sha256'])
            table,_=open_source(args.originals,item,flop,version,RUN,HEAD,pool,pipeline,ranges)
            public,=(p for p in table if p.endswith(turn))
            original[version]=table[public][:2]
        g,gi=original['gto']
        public=g['subgame']['nodes'][0]['board'][:8]
        assert public.endswith(turn) and g['subgame']['rivers']==RIVERS[flop] and len(public)==8
        targets=RIVERS[flop]
        if flop in (SOLVE_FLOP,REUSE_FLOP):
            aid=gi['artifact_id']
            boundary=load_original(args.originals,aid,dict(name=f'B524-R8-{flop}-gto',run=RUN,head=HEAD,sha256=gi['artifact_sha256']),
                'BTN_BB',flop,turn,'gto',pot=550,stack=9750,flop_line='b50 c',pipeline=pipeline,ranges=ranges)
            assert boundary['public']==public
            if flop==SOLVE_FLOP:
                g,gpath=expanded_source(boundary,'gto',pool,pipeline,args)
                e,epath=expanded_source(boundary,'exp_ip',pool,pipeline,args)
                if args.driver:
                    return
                if not g or not e:
                    case['status']='MISSING_NEW_RIVER_EXTRACTION'
                    continue
                # The two archival rivers and the additional 46 cover every legal river.
                # 3d is the named new river subsequently verified from both fresh native jobs.
                targets=['3d']
                case['extracted_rivers']=g['subgame']['rivers']
                assert g['subgame']['rivers']==e['subgame']['rivers']
            else:
                name=f'NL2_{B542_CODE}.json.gz'
                local=EVIDENCE/name
                if not local.is_file() and args.reuse_run:
                    local=args.results/name
                if not local.is_file():
                    case['status']='MISSING_COMPLETED_CONDITIONAL_SOURCE'
                    continue
                native_run=args.reuse_run or json.loads((DATA/'nl2_hu_b542_rank8_results.json').read_bytes())['run']
                if (DATA/'nl2_hu_b542_rank8_results.json').is_file():
                    assert native_run==json.loads((DATA/'nl2_hu_b542_rank8_results.json').read_bytes())['run']
                assert native_run!=args.run and native_run>0
                e=replay_native(boundary,'exp_ip',pool,pipeline,local,native_run,B542_CODE)
            if not (0<=g['subgame']['info']['gto_expl_pct']<=.5 and
                    all(0<=e['subgame']['info'][k]<=.5 for k in ('gto_expl_pct','hero_gap_pct'))):
                case['status']='CONDITIONAL_OUTSIDE_CONVERGENCE_GATE'
                continue
            esha=gi['root_sha256']
        else:
            e,ei=original['exp_ip']
            esha=ei['root_sha256']
        gto_rows={}
        for river in targets:
            full=public+river
            gr=audit_decision(g,full,LINE,1,gi['root_sha256'])
            if gr and gr['compatible_hole_card_pairs'] and gr['b50']['eligible']:
                hands=playable_hands(g,gr,route)
                if hands:
                    gto_rows[full]=(gr,hands)
        for full,(gr,gh) in gto_rows.items():
            er=audit_decision(e,full,LINE,1,esha)
            eh=playable_hands(e,er,route) if er and er['compatible_hole_card_pairs'] else {}
            hs=[gh[h] for h in sorted(gh.keys() & eh.keys())]
            case['rivers'][full]=dict(gto_hands=len(gh),locked_hands=len(eh),shared_rendered_checks=hs)
            if case.get('selected') or not hs or not er['b50']['eligible']:
                continue
            board,pin=emit_board(model,g,e,full,LINE,texture(flop))
            assert (board['actual_pot_bb'],board['actual_effective_stack_bb'])==(11,94.75)
            assert all(r['strict_legal_combos']>0 and r['compatible_hole_card_pairs']>0 for r in (gr,er))
            pin.update(original_gto_archive=gi,shared_rendered_river_checks=hs)
            variant=board['nl2_locked_variants'][0]
            variant.update(pool_sha256=POOL,measurement_policy='STREET_SPECIFIC_POOL_MARGINALS')
            if flop in (SOLVE_FLOP,REUSE_FLOP):
                variant.update(variant_label='原始 GTO 翻牌範圍，轉河牌套用 NL2 分街鎖頻',
                    applied_street_rates=rates(e),gto_parent_source_run_id=RUN,gto_parent_source_sha256=gi['root_sha256'],
                    viewer_archive_code=pin.get('locked_viewer_archive_code',pin['viewer_archive_code']),viewer_sha256=pin.get('locked_viewer_sha256',pin['viewer_sha256']))
                pin['native_gto_parent']=gi
                if flop==SOLVE_FLOP:
                    for path in (gpath,epath):
                        shutil.copyfile(path,EVIDENCE/path.name)
                elif local!=EVIDENCE/name:
                    shutil.copyfile(local,EVIDENCE/name)
            else:
                pin['original_locked_archive']=ei
                variant.update(variant_label='BB 實測翻牌領打及轉河牌分街鎖頻',
                               viewer_archive_code=pin['viewer_archive_code'],viewer_sha256=pin['viewer_sha256'])
            for v,(_,identity) in original.items():
                shutil.copyfile(args.originals/f"{identity['artifact_id']}.zip",EVIDENCE/f"NL2_B524_R8_{flop.upper()}_{v.upper()}.zip")
            group['boards'].append(board)
            group['pins'].append(pin)
            checks['gto_references'][source_key(MID,gr)]=gr
            checks['references'][source_key(MID,er)]=er
            case['selected']=full
    count=len(group['boards'])
    assert count==len({b['flop'] for b in group['boards']})<=3
    if count==3:
        (EVIDENCE/'reverified/rank70.json').write_bytes(json_bytes(group))
        (DATA/'nl2_hu_b546_locked_medium.json').write_bytes(json_bytes(checks))
    (DATA/'nl2_hu_b546_rank70_results.json').write_bytes(json_bytes(dict(run=args.run,qualifying_distinct_flops=count,
        source_run=RUN,attempts=report,paired_boards=group)))


if __name__=='__main__':
    main()
