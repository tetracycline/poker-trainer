"""Replay archived UTG–CO half-pot flops, turn checks and independently priced river decisions."""
import argparse
import base64
import gzip
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b483_locked_medium import POOL
from hu_b489_rank79_originals import parse, PIN, EXTRA_SPOTS
from hu_b527_checked_barrels import COLUMNS, board_row, classes, hcls
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey, game_reach, compatible_node_reach

DATA = Path('data')
MODEL = 'ln-ipc-r_model-6ntgm7'
LINE = 'b50 c/x x/x'
BOARDS = {'8c6h3d':'3d6h8c5h6d', '9c8d5h':'5h8d9c3d2c', 'KsQh4d':'4dQhKsTc4c'}
OLD_GTO = '14703138852'


def load(flop, public, version, solver, pipeline, ranges):
    turn = public[6:8]
    historic = flop == 'KsQh4d'
    if historic and version == 'gto':
        pin = json.loads((DATA/'nl2_hu_b489_originals.json').read_bytes())[OLD_GTO]
        code = 'B554_R213_KSQH4D_GTO'
        path = EVIDENCE / f'NL2_{code}.zip'
        assert sha(path.read_bytes()) == pin['sha256']
        with ZipFile(path) as z, TemporaryDirectory() as temp:
            for name in z.namelist():
                assert not Path(name).is_absolute() and '..' not in Path(name).parts
            z.extractall(temp)
            base = Path(temp)
            manifest, = (base/'evidence').glob('*.json')
            source = parse(base/'solver/postflop', base/'evidence', manifest, pin['run'], flop, version,
                           solver, pipeline, ranges, False, case_turn=turn)[turn]
        source.update(archive_code=code, archive_sha256=pin['sha256'], artifact_id=int(OLD_GTO))
    else:
        previous = 'B489' if historic else 'B520'
        code = f'{previous}_R79_{flop.upper()}_{turn.upper()}_{version.upper()}'
        path = EVIDENCE / f'NL2_{code}.json.gz'
        raw = path.read_bytes()
        if historic:
            rows = json.loads((DATA/'nl2_hu_b489_rank79_attempts.json').read_bytes())['fresh']
        else:
            rows = json.loads((DATA/'nl2_hu_b520_rank79_flops.json').read_bytes())['observations']
        ref = rows[f'{flop} {turn} {version}']
        assert sha(raw) == ref['archive_sha256']
        source = json.loads(gzip.decompress(raw))
        assert (source['run'], source['artifact_id'], source['source_sha256']) == (ref['source_run_id'], ref['archive_id'], ref['source_sha256'])
        source.update(archive_code=code, archive_sha256=sha(raw))
    root, sub, m = source['root'], source['subgame'], source['manifest']
    assert sha(compact(root)) == m['file_flop_sha256'] and sha(compact(sub)) == source['source_sha256']
    assert (m['spot'], m['version'], m['pool_source_sha256'], m['flop_size_profile']) == ('UTG_CO', version, POOL, 'full' if historic else 'utg-50-only')
    assert (root['pot'],root['stack'],sub['pot'],sub['stack'],sub['turn'],sub['line0']) == (650,9750,1300,9425,turn,'b50 c')
    assert [source['root_job'][k] for k in ['oop','ip']] == [ranges.to_str(v) for v in ranges.ranges('UTG_CO',version)]
    for game in (root,sub):
        assert 0 <= game['info']['gto_expl_pct'] <= .5
        if version == 'gto':
            assert not game['info'].get('lock_stats')
        else:
            assert game['info']['lock_stats'] and 0 <= game['info']['hero_gap_pct'] <= .5
    return source


def get_node(game, board, line, seat):
    n, = (n for n in game['nodes'] if (n['board'],n['line'],n['player']) == (board,line,seat))
    return n


def check_prices(s, p):
    root, sub = s['root'],s['subgame']
    for game,public,line,actor,bets,pot,action in [
        (root,p[:6],'',0,[0,0],650,'b50'), (root,p[:6],'b50',1,[325,0],975,'c'),
        (root,p[:8],'b50 c/',0,[325,325],1300,'x'), (sub,p[:8],'b50 c/',0,[0,0],1300,'x'),
        (sub,p[:8],'b50 c/x',1,[0,0],1300,'x'), (sub,p,'b50 c/x x/',0,[0,0],1300,'x'),
        (sub,p,LINE,1,[0,0],1300,'b50'), (sub,p,LINE+' b50',0,[0,650],1950,'c')]:
        n = get_node(game,public,line,actor)
        assert (n['bets'],n['pot']) == (bets,pot) and action in n['acts']
    parent = get_node(root,p[:8],'b50 c/',0)
    for seat,k in enumerate(('oop_w','ip_w')):
        assert s['subgame_job'][k] == [[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]


def hands(s, row, route):
    p = row['public_board']
    sub = s['subgame']
    node = get_node(sub,p,LINE,1)
    masks = base64.b64decode(row['compatible_action_mask_b64'],validate=True)
    deal = sub['hands'][1]
    out = {}
    for i,(hole,mask) in enumerate(zip(deal,masks,strict=True)):
        if not mask:
            continue
        hand = ''.join(cardkey(hole))
        group = (hcls(hand,p[:6]),hcls(hand,p[:8]),classes(hand,p)[0])
        if any(t not in COLUMNS for t in group):
            continue
        keys = [f'{board_row(p[:n])}:{COLUMNS.index(t)}' for t,n in zip(group,(6,8,10),strict=True)]
        if any(k not in route[street] for k,street in zip(keys,('flop','turn','river'),strict=True)):
            continue
        acts = node['acts']
        prob = [max(0.,node['strat'][j*len(deal)+i]) for j in range(len(acts))]
        total = sum(prob)
        assert total > 0
        policy = dict(accepted_mask=mask,action_order=acts,accepted_actions=[a for j,a in enumerate(acts) if mask & (1<<j)],
                      strategy={a:round(x/total,7) for a,x in zip(acts,prob,strict=True)})
        out[hand] = dict(hand=hand,flop_class=group[0],turn_class=group[1],river_class=group[2],
            flop_texture=board_row(p[:6]),turn_texture=board_row(p[:8]),river_texture=board_row(p),
            displayed_suggestion=route['river'][keys[2]],native=policy)
    return out


def opponent_rates(src,public,pool):
    root,sub = src['root'],src['subgame']
    masks = game_reach(root,sub)[0]
    found=[]
    for game,job,board,line,street in [(root,src['root_job'],public[:6],'',1),
            (sub,src['subgame_job'],public[:8],'b50 c/',2),(sub,src['subgame_job'],public,'b50 c/x x/',3),
            (sub,src['subgame_job'],public,LINE+' b50',3)]:
        n=get_node(game,board,line,0)
        first=next(r for r in src['manifest']['locks'] if re.search(r['pat'],line))
        rule=next(r for r in job['locks'] if re.search(r['pat'],line))
        assert job['hero']==1 and first['pat']==rule['pat']
        stat=game['info']['lock_stats'][rule['pat']]
        assert stat['nodes']>0
        if street==1:
            bucket=re.fullmatch(r'cbet_by_texture_SRP\[(.+)\]',first['source'])[1]
            measured=pool['cbet_by_texture_SRP'][bucket]
            assert first['n']==measured['n'] and rule['bet']==measured['cbet']/100
        elif street==2:
            measured=pool['postflop_HU']['SRP_PFR_OOP']['turn_barrel']
            assert first['source']=='SRP_PFR_OOP.turn_barrel' and first['n']==measured['n'] and rule['bet']==measured['pct']/100
        elif line.endswith('b50'):
            measured=pool['HU_facing_bet']['3']['by_size']['34-55%']
            assert first['source']=='NL2.HU_facing_bet[3].by_size[34-55%]' and first['n']==measured['n']
            assert rule['fold']==measured['fold']/100 and rule['raise']==measured['raise']/100
        else:
            assert first['scope']=='ASSUMED_HISTORY_RATE_OR_SIZE' and first['n']==0 and rule['bet']==.45
        rec=dict(street=street,token='b50' if line.endswith('b50') else 'history',line=line,source=first['source'],scope=first['scope'],
            n=first['n'],nodes=stat['nodes'],pattern=first['pat'],opportunity='FACING_BET' if line.endswith('b50') else 'FIRST_TO_ACT',
            native_rule=rule,pattern_aggregate_fold_pct=100*stat['fold'],pattern_aggregate_aggressive_pct=100*stat['agg'])
        if game is sub:
            reach=compatible_node_reach(root,sub,n,masks[f'{board}|{line}|0'])
            rec['compatible_hole_card_pairs']=reach['compatible_hole_card_pairs']
            if not reach['compatible_hole_card_pairs']:
                rec['status']='RULE_APPLIED_IN_TREE_NO_COMPATIBLE_DEAL_AT_THIS_NODE'
        if line.endswith('b50'):
            rec.update(target_fold_pct=100*rule['fold'],target_raise_pct=100*rule['raise'],fold_pct=100*stat['fold'],raise_pct=100*stat['agg'])
        else:
            rec.update(target_bet_pct=100*rule['bet'],bet_pct=100*stat['agg'])
        found.append(rec)
    return found


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--solver',type=Path,required=True)
    args=ap.parse_args()
    solver=args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==PIN
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline, ranges
    ranges.SPOTS.update(EXTRA_SPOTS)
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)['NL2']
    route=json.loads(subprocess.check_output(['node','tools/hu_b554_rank213_route.cjs']))
    model=json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    group=dict(rank=213,model_id=MODEL,boards=[],pins=[])
    medium=dict(schema='NL2_HU_B554_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    for flop,p in BOARDS.items():
        g,e=[load(flop,p,v,solver,pipeline,ranges) for v in ('gto','exp_ip')]
        sets=[]
        for s in (g,e):
            check_prices(s,p)
            row=audit_decision(s,p,LINE,1,s['manifest']['file_flop_sha256'])
            assert row['compatible_hole_card_pairs']>=row['strict_legal_combos']>0
            sets.append(hands(s,row,route))
            medium['gto_references' if s is g else 'references'][source_key(MODEL,row)]=row
        shared=[]
        for h in sorted(sets[0].keys() & sets[1].keys()):
            a,b=sets[0][h],sets[1][h]
            info={k:v for k,v in a.items() if k!='native'}
            assert info=={k:v for k,v in b.items() if k!='native'}
            shared.append(dict(info,gto=a['native'],nl2=b['native']))
        assert shared
        agreement={k:sum(all(w['displayed_suggestion'] in w[v]['accepted_actions'] for v in versions) for w in shared)
                   for k,versions in [('gto',['gto']),('nl2',['nl2']),('both',['gto','nl2'])]}
        board,pin=emit_board(model,g,e,p,LINE,texture(flop))
        pin.update(rendered_decision_hands=shared,hands_accepting_displayed_suggestion=agreement,
                   original_gto_artifact_id=g['artifact_id'],original_locked_artifact_id=e['artifact_id'])
        board['flop_size_profile']=g['manifest']['flop_size_profile']
        if g['manifest']['restricted_tree_assumption']:
            board.update(restricted_flop_size_profile='UTG_CO_50PCT_ONLY', restricted_flop_bet_sizes_pct=[50])
        board['flop_bet_sizes_pct']=[int(v.rstrip('%')) for v in g['manifest']['flop_action_sizes']]
        board['nl2_locked_variants'][0].update(variant_label='UTG 翻轉牌實測鎖、河牌首動 45% 假設',pool_sha256=POOL,measurement_policy='MEASURED_UTG_FLOP_AND_TURN_ASSUMED_CHECKED_THROUGH_RIVER_ROOT',
            applied_street_rates=opponent_rates(e,p,pool),viewer_archive_code=pin.get('locked_viewer_archive_code',pin['viewer_archive_code']),
            viewer_sha256=pin.get('locked_viewer_sha256',pin['viewer_sha256']))
        group['boards'].append(board)
        group['pins'].append(pin)
    assert len({b['flop'] for b in group['boards']})==3
    (EVIDENCE/'reverified/rank213.json').write_bytes(json_bytes(group))
    (DATA/'nl2_hu_b554_locked_medium.json').write_bytes(json_bytes(medium))


if __name__=='__main__':
    main()
