"""Authenticate checked-flop CO three-bet-pot turn and river decisions on five new low boards."""
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
PINS = DATA/'nl2_hu_b537_flops.json'
MODELS = {131: ('ln-3bp-3c_t_model-1oebhk7','x x/',0),
          244: ('ln-3bp-3c_r_model-knstxa','x x/b50 c/',825),
          261: ('ln-3bp-3c_r_model-7xkisp','x x/x x/',0)}
VERSIONS = ('gto','exp_oop')
RANGE_SHA = {'gto':'f64a116f62e62b8eb04e3d752bca6bc04513d5338d0295a0a65e0686aac49dbf',
             'exp_oop':'756ff4e3135a715d3f46777b8ee835b402238c5e78819952cbe4cc02ec98d652'}


def authenticate(downloads, flop, turn, runouts, version):
    src = original(downloads,flop,turn,version,batch='B537',spot='CO3_BTN',flop_line='x x',
        flop_policy='checkcheck',turn_policy='default',turn_extracts=('x b50 c','x b100 c','x x','b50 c','b100 c'),
        root_pot=1650,root_stack=9250,frozen_turns=list(runouts))
    meta,root,sub=src['manifest'],src['root'],src['subgame']
    assert (meta['solver_pin'],meta['solver_ranges_sha256'])==(PIPELINE,RANGES)
    assert meta['preflop_ranges']['full_sha256']=='787f719c752165262807f79b91daec81e1db86a83d557a4ea645ef2649f532c7'
    rootjob=src['root_job']
    assert sha(compact([rootjob['oop'],rootjob['ip']]))==RANGE_SHA[version]
    if sub is not None:
        parent,=(n for n in root['nodes'] if n['line']=='x x/' and n['board'].endswith(turn))
        assert parent['bets']==[0,0] and sub['rivers']==runouts[turn]
        job=src['subgame_job']
        assert (job['pot'],job['stack'],job['root_no_bet'])==(1650,9250,False)
        assert job['line0']==['x','x','/'] and (sub['pot'],sub['stack'])==(1650,9250)
        for seat,name in enumerate(('oop_w','ip_w')):
            assert job[name]==[[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
    return src


def exact_row(src, line, public, investment, masks):
    root, sub = src['root'], src['subgame']
    nodes=[n for n in sub['nodes'] if (n['line'],n['player'],n['board'])==(line,0,public)]
    if not nodes:
        return None,set()
    node,=nodes
    assert (node['pot'],node['bets'])==(1650+2*investment,[investment,investment])
    if investment:
        response,=(n for n in sub['nodes'] if (n['line'],n['board'])==('x x/b50',public[:8]))
        assert response['pot']==2475 and response['bets']==[825,0] and 'c' in response['acts']
    row=proof(root,sub,node,masks)
    mask=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
    hands={''.join(cardkey(h)) for h,a in zip(sub['hands'][0],mask,strict=True) if a}
    v=src['version']
    row.update(version=v,spot='CO3_BTN',family='3BP',flop=sub['flop'],turn=sub['turn'],
        source_run_id=src['run'],source_sha256=src['source_sha256'],archive_sha256=src['archive_sha256'],
        root_sha256=src['root_sha256'],gto_gap_pct=sub['info']['gto_expl_pct'],
        locked_hero_gap_pct=sub['info'].get('hero_gap_pct'),lock_scope=lock_scope(sub,src['manifest']['locks'],v),
        root_applied_rust_lock_nodes=sum(x['nodes'] for x in root['info'].get('lock_stats',{}).values()),
        subgame_applied_rust_lock_nodes=sum(x['nodes'] for x in sub['info'].get('lock_stats',{}).values()))
    return row,hands


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--downloads', required=True, type=Path)
    parser.add_argument('--run', required=True, type=int)
    args = parser.parse_args()
    assert args.run > 0
    routes = json.loads(subprocess.check_output(['node','tools/hu_b537_threebet_routes.cjs']))
    models = json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records']
    pins = json.loads(PINS.read_bytes())
    attempts=[]
    groups={r:dict(model_id=mid,rank=r,boards=[],pins=[]) for r,(mid,_,_) in MODELS.items()}
    records={r:[] for r in MODELS}
    for flop,runouts in pins.items():
        assert texture(flop)=='LOW'
        selected=set()
        for turn,rivers in runouts.items():
            outcome=dict(flop=flop,turn=turn,sources={},decisions=[])
            attempts.append(outcome)
            sources=[]
            for version in VERSIONS:
                file=args.downloads/f'NL2-B537-{flop}-{version}/trainer/evidence/{flop}-{version}.json'
                if not file.exists() or json.loads(file.read_bytes())['failures']:
                    outcome['sources'][version]='MISSING_COMPLETED_SOURCE'
                    continue
                source=authenticate(args.downloads,flop,turn,runouts,version)
                if source['subgame'] is None:
                    outcome['sources'][version]='NO_NATIVE_TURN'
                    continue
                gaps=[source[k]['info']['gto_expl_pct'] for k in ('root','subgame')]
                if version!='gto':
                    gaps.extend(source[k]['info']['hero_gap_pct'] for k in ('root','subgame'))
                outcome['sources'][version]=dict(gaps=gaps,source_sha256=source['source_sha256'])
                if all(0<=gap<=.5 for gap in gaps):
                    sources.append(source)
            if len(sources)!=2:
                continue
            g,e=sources
            rates=measured_rates(e)
            if not rates:
                continue
            archive=gzip.compress(compact(dict(run_id=args.run,solver=SOLVER,rust=RUST,source_arrays=sources)),mtime=0)
            code=f'B537_{flop.upper()}_{turn.upper()}'
            for src in sources:
                src.update(run=args.run,archive_code=code,archive_sha256=sha(archive))
            masks=[game_reach(s['root'],s['subgame'])[0] for s in sources]
            start,=(n['board'] for n in g['subgame']['nodes'] if (n['line'],n['player'])==('x x/',0))
            assert {start[i:i+2] for i in (0,2,4)}=={flop[i:i+2] for i in (0,2,4)} and start[6:]==turn
            for rank,(mid,line,investment) in MODELS.items():
                m=models[mid]
                assert m['frequency_rank']==rank and m['family']=='3BP' and m['solver_profile']=='CO3_BTN'
                columns=routes[str(rank)]
                for public in ([start] if m['street']==1 else [start+r for r in rivers]):
                    pair=[exact_row(s,line,public,investment,mask) for s,mask in zip(sources,masks,strict=True)]
                    (gr,gh),(er,eh)=pair
                    row=dict(rank=rank,public=public,selected=False)
                    outcome['decisions'].append(row)
                    if gr is None or er is None:
                        row['status']='NO_MATCHING_RUST_NODE'
                        continue
                    assert gr['source_actions']==er['source_actions']
                    shared=gh&eh
                    witness=[]
                    for h in sorted(shared):
                        types=[hcls(h,public[:6]),hcls(h,public[:8])]
                        if len(public)==10:
                            types.append(classes(h,public)[0])
                        if all(t in allowed for t,allowed in zip(types,columns,strict=True)):
                            witness.append(dict(hand=h,classes=types))
                    row.update(joint_source_pairs=[gr['compatible_hole_card_pairs'],er['compatible_hole_card_pairs']],
                               common_hands=len(shared),rendered_hands=len(witness))
                    if not witness or rank in selected:
                        continue
                    b,p=emit_board(m,g,e,public,line,'LOW')
                    assert p['common_legal_hero_combos']==len(shared) and b['actual_pot_bb']==(1650+2*investment)/100
                    p['shared_rendered_route_hands']=witness
                    b['nl2_locked_variants'][0].update(variant_label='翻牌至河牌分街 NL2 鎖頻',measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',
                        applied_street_rates=rates,pool_sha256=POOL,viewer_archive_code=p['viewer_archive_code'],viewer_sha256=p['viewer_sha256'])
                    selected.add(rank)
                    groups[rank]['boards'].append(b)
                    groups[rank]['pins'].append(p)
                    records[rank].append((gr,er))
                    (EVIDENCE/f'NL2_{code}.json.gz').write_bytes(archive)
                    row['selected']=True
    medium=dict(schema='NL2_HU_B537_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    for rank,group in groups.items():
        count=len(group['boards'])
        assert count==len({b['flop'] for b in group['boards']})<=5
        if count>=3:
            (EVIDENCE/'reverified'/f'rank{rank}.json').write_bytes(json_bytes(group))
            for gr,er in records[rank]:
                medium['gto_references'][source_key(group['model_id'],gr)]=gr
                medium['references'][source_key(group['model_id'],er)]=er
    (DATA/'nl2_hu_b537_locked_medium.json').write_bytes(json_bytes(medium))
    (DATA/'nl2_hu_b537_threebet_outcomes.json').write_bytes(json_bytes(dict(run=args.run,groups=groups,attempts=attempts)))


if __name__=='__main__':
    main()
