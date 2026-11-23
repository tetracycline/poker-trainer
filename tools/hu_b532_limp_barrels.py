"""Replay BB's half-pot limped lead and exact turn barrels against the visible trainer routes."""
import argparse
import base64
import gzip
import json
from pathlib import Path
import subprocess
import sys

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import original
from hu_b481_rank27_limp_rivers import check_limp_source
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b518_rank220_native import measured_rates
from hu_board_reach_corrections import source_key
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import game_reach, cardkey
from verify_hu_multiboard_100bb import lock_scope

sys.path.insert(0, str(Path(__file__).resolve().parent/'lines_pipeline'))
from run10_common import classes, hcls

DATA = Path('data')
PINS = DATA/'nl2_hu_b532_flops.json'
MODELS = {27: ('ln-iso-lmp_r_model-1aov4pd', 33), 29: ('ln-iso-lmp_r_model-gifggm', 75)}
VERSIONS = ('gto','exp_oop')
TEXTURES = {'MONOTONE':'mono','LOW':'low','KQ_HIGH':'KQ_high'}


def authenticate(downloads, flop, turn, runouts, version):
    src = original(downloads, flop, turn, version, batch='B532', spot='LMP_CO_BB',
        flop_line='b50 c', flop_policy='oop-b50only', turn_policy='default',
        turn_extracts=('b33 c','b50 c','b75 c','b100 c'), root_pot=250, root_stack=9900,
        turn_mode='33-50-75-100', turn_menu='33%,50%,75%,100%', preflop_source='ASSUMED_EXPLICIT_169CLASS',
        flop_profile='lmp-50-only', frozen_turns=list(runouts))
    check_limp_source(src)
    meta, root, game = src['manifest'], src['root'], src['subgame']
    assert (meta['solver_pin'],meta['solver_ranges_sha256']) == (PIPELINE,RANGES)
    facing, = (n for n in root['nodes'] if n['line']=='b50' and len(n['board'])==6)
    assert (facing['player'],facing['bets'],facing['pot']) == (1,[125,0],375) and 'c' in facing['acts']
    if game is not None:
        parent, = (n for n in root['nodes'] if n['line']=='b50 c/' and n['board'].endswith(turn))
        assert parent['bets']==[125,125] and game['rivers']==runouts[turn]
        job = src['subgame_job']
        assert (job['pot'],job['stack'],job['root_no_bet'])==(500,9775,False)
        assert job['line0']==['b50','c','/'] and (game['pot'],game['stack'])==(500,9775)
        for seat, name in enumerate(('oop_w','ip_w')):
            assert job[name]==[[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
    return src


def river_row(src, line, river, investment):
    root, sub = src['root'], src['subgame']
    nodes = [n for n in sub['nodes'] if n['line']==line and n['player']==0 and n['board'].endswith(river)]
    if not nodes:
        return None, set()
    node, = nodes
    assert node['pot']==500+2*investment and node['bets']==[investment,investment]
    turn_bet, = (n for n in sub['nodes'] if n['board']==node['board'][:8] and n['line']==line.removesuffix(' c/'))
    assert (turn_bet['pot'],turn_bet['bets'],turn_bet['player'])==(500+investment,[investment,0],1)
    assert 'c' in turn_bet['acts']
    row = proof(root,sub,node,game_reach(root,sub)[0])
    mask = base64.b64decode(row['compatible_action_mask_b64'],validate=True)
    hands = {''.join(cardkey(h)) for h,allowed in zip(sub['hands'][0],mask,strict=True) if allowed}
    v = src['version']
    row.update(version=v,spot='LMP_CO_BB',family='LMP',flop=sub['flop'],turn=sub['turn'],
        source_run_id=src['run'],source_sha256=src['source_sha256'],archive_sha256=src['archive_sha256'],
        root_sha256=src['root_sha256'],gto_gap_pct=sub['info']['gto_expl_pct'],
        locked_hero_gap_pct=sub['info'].get('hero_gap_pct'),lock_scope=lock_scope(sub,src['manifest']['locks'],v),
        root_applied_rust_lock_nodes=sum(x['nodes'] for x in root['info'].get('lock_stats',{}).values()),
        subgame_applied_rust_lock_nodes=sum(x['nodes'] for x in sub['info'].get('lock_stats',{}).values()))
    return row, hands


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--downloads', required=True, type=Path)
    parser.add_argument('--run', required=True, type=int)
    args = parser.parse_args()
    assert args.run > 0
    routes = json.loads(subprocess.check_output(['node','tools/hu_b532_limp_routes.cjs']))
    models = json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records']
    pins = json.loads(PINS.read_bytes())
    attempts = []
    medium = dict(schema='NL2_HU_B532_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    counts = {}
    for tag, flops in pins.items():
        rank = int(tag)
        mid,pct = MODELS[rank]
        m = models[mid]
        assert (m['frequency_rank'],m['family'],m['solver_profile'],m['street'])==(rank,'LMP','LMP_CO_BB',2)
        group = dict(model_id=mid,rank=rank,boards=[],pins=[])
        observations = []
        line = f'b50 c/b{pct} c/'
        for flop,runouts in flops.items():
            columns = routes[tag][TEXTURES[texture(flop)]]
            report = dict(rank=rank,flop=flop,selected=None,runouts={})
            attempts.append(report)
            for turn,rivers in runouts.items():
                outcome = dict(gaps={},rivers={})
                report['runouts'][turn] = outcome
                sources = []
                for v in VERSIONS:
                    file=args.downloads/f'NL2-B532-{flop}-{v}/trainer/evidence/{flop}-{v}.json'
                    if not file.exists() or json.loads(file.read_bytes())['failures']:
                        continue
                    src=authenticate(args.downloads,flop,turn,runouts,v)
                    if src['subgame'] is None:
                        continue
                    gaps=[src[g]['info']['gto_expl_pct'] for g in ('root','subgame')]
                    if v!='gto':
                        gaps.extend(src[g]['info']['hero_gap_pct'] for g in ('root','subgame'))
                    outcome['gaps'][v]=gaps
                    if all(0<=value<=.5 for value in gaps):
                        sources.append(src)
                if len(sources)!=2:
                    outcome['status']='NO_CONVERGED_SOURCE_PAIR'
                    continue
                g,e=sources
                assert g['manifest']['preflop_ranges']==e['manifest']['preflop_ranges']
                rates=measured_rates(e)
                if not rates:
                    outcome['status']='NO_MEASURED_NATIVE_LOCK'
                    continue
                raw=gzip.compress(compact(dict(run_id=args.run,solver=SOLVER,rust=RUST,source_arrays=sources)),mtime=0)
                code=f'B532_R{rank}_{flop.upper()}_{turn.upper()}'
                for src in sources:
                    src.update(run=args.run,archive_sha256=sha(raw),archive_code=code)
                for river in rivers:
                    (gr,gh),(er,eh)=[river_row(s,line,river,500*pct//100) for s in sources]
                    if not gr or not er:
                        outcome['rivers'][river]={'status':'NATIVE_TARGET_ABSENT'}
                        continue
                    public=gr['public_board']
                    assert public==er['public_board'] and gr['source_actions']==er['source_actions']
                    witness=[]
                    for hand in sorted(gh & eh):
                        categories=(hcls(hand,public[:6]),hcls(hand,public[:8]),classes(hand,public)[0])
                        if all(c in eligible for c,eligible in zip(categories,columns,strict=True)):
                            witness.append(dict(cards=hand,classes=list(categories)))
                    outcome['rivers'][river]=dict(joint_gto=gr['compatible_hole_card_pairs'],joint_lock=er['compatible_hole_card_pairs'],
                        common_hands=len(gh & eh),rendered_hands=len(witness))
                    if not witness or report['selected']:
                        continue
                    board,pin=emit_board(m,g,e,public,line,texture(flop))
                    assert pin['common_legal_hero_combos']==len(gh & eh)
                    pin.update(rendered_route_witnesses=witness,restricted_flop_sizes_pct=[50],assumed_limp_preflop=True)
                    board['nl2_locked_variants'][0].update(variant_label='限半池翻牌・分街 NL2 鎖頻',measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',
                        applied_street_rates=rates,pool_sha256=POOL,viewer_archive_code=pin['viewer_archive_code'],viewer_sha256=pin['viewer_sha256'])
                    (EVIDENCE/f'NL2_{code}.json.gz').write_bytes(raw)
                    group['boards'].append(board)
                    group['pins'].append(pin)
                    observations.append((gr,er))
                    report['selected']=public
        counts[tag]=len(group['boards'])
        assert len(group['boards'])==len({b['flop'] for b in group['boards']})<=5
        if counts[tag]>=3:
            (EVIDENCE/'reverified'/f'rank{rank}.json').write_bytes(json_bytes(group))
            for gr,er in observations:
                medium['gto_references'][source_key(mid,gr)]=gr
                medium['references'][source_key(mid,er)]=er
        (DATA/f'nl2_hu_b532_rank{rank}_pairs.json').write_bytes(json_bytes(group))
    (DATA/'nl2_hu_b532_rendered_barrels.json').write_bytes(json_bytes(dict(run=args.run,qualifying_flops=counts,attempts=attempts)))
    (DATA/'nl2_hu_b532_locked_medium.json').write_bytes(json_bytes(medium))


if __name__=='__main__':
    main()
