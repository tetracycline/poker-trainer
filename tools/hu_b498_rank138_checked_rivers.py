"""Reverify three checked CO vs BB rivers from the original solver jobs, ranges and two-seat masks."""
import argparse
import json
from pathlib import Path
import zipfile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b483_locked_medium import POOL, proof
from hu_board_reach_corrections import source_key
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import game_reach
from verify_hu_multiboard_100bb import lock_scope

MID = 'ln-ipfr-r_model-hqu5je'
LINE = 'x x/x x/x'
PINS = Path('data/nl2_hu_b498_rank138_artifacts.json')
OUTPUT = EVIDENCE / 'reverified/rank138.json'
REPORT = Path('data/nl2_hu_b498_locked_medium.json')
SELECTION = (
    ('Js9h4d','4d9hJsTsAh',14597934573,14693877001),
    ('8s8h3d','3d8h8s5s4s',14593700327,14694335674),
    ('As9h2d','2d9hAsKd6s',14597269910,14598482452),
)


def read_source(folder, artifact, ref, flop, public, version):
    archive=folder/f'{artifact}.zip'
    assert sha(archive.read_bytes())==ref['sha256']
    with zipfile.ZipFile(archive) as z:
        name,=[n for n in z.namelist() if n.startswith('evidence/') and n.endswith('.json')]
        pins={z.read(n).decode().strip() for n in z.namelist() if n.startswith('evidence/') and n.endswith('.txt')}
        assert {SOLVER,RUST} <= pins
        m=json.loads(z.read(name))
        assert (m['spot'],m['version'],m['failures'])==('CO_BB',version,[])
        case,=[c for c in m['cases'] if c['turn']==public[6:8] and c['line']=='x x']
        legacy=m['schema']=='HU_MISSING_ACTION_HISTORY_CFR_V1'
        if legacy:
            assert version=='gto' and m['selected_flops']==[flop]
            assert m['source_preflop_tree_sha256']=='d4ca8e0c7d53deb6af337bfef8ff0c125205c1d3ef912267d8b40efc2fe7c100'
            rp,rsha,sp,ssha=case['flop_json'],case['flop_sha256'],case['sub_json'],case['sub_sha256']
        else:
            assert (m['schema'],m['pool_source_sha256'],m['pot_family'],m['flop'])==('NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1',POOL,'SRP',flop)
            assert m['preflop_ranges']['source'] in ('PINNED_POKER_SOLVER_PREFLOP_CFR','PINNED_LEGACY_OFFICIAL_GTO_FLOP_WEIGHTS')
            rp,rsha,sp,ssha=m['file_flop'],m['file_flop_sha256'],case['source_path'],case['source_sha256']
        def game(rel,digest):
            prefix='solver/postflop/'+rel
            raw=z.read(prefix);jb=z.read(prefix[:-5]+'.job.json')
            assert sha(raw)==digest
            return json.loads(raw),json.loads(jb),sha(jb)
        root,rj,rjobsha=game(rp,rsha);sub,j,jsha=game(sp,ssha)
    assert (root['flop'],sub['turn'],sub['line0'],j['line0'])==(flop,public[6:8],'x x',['x','x','/'])
    assert all((job['pot'],job['stack'],job['rake_rate'],job['rake_cap'])==(550,9750,.05,1000) for job in (rj,j))
    parent,=[n for n in root['nodes'] if n['line']=='x x/' and n['board']==public[:8]]
    for seat,side in enumerate(('oop_w','ip_w')):
        assert j[side]==[[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
    patterns=m.get('locks',[])
    assert j.get('hero')==(1 if version=='exp_ip' else None)
    assert [x['pat'] for x in patterns]==[x['pat'] for x in j.get('locks',[])]
    manifest=dict(spot='CO_BB',pot_family='SRP',locks=patterns)
    if 'gto_parent_source_run_id' in m:
        assert m['gto_parent_source_sha256']==rsha and rj.get('hero') is None
        manifest.update(gto_parent_source_run_id=m['gto_parent_source_run_id'],gto_parent_source_sha256=rsha)
    else:
        assert rj.get('hero')==j.get('hero') and rj.get('locks',[])==j.get('locks',[])
    node,=[n for n in sub['nodes'] if (n['board'],n['line'],n['player'])==(public,LINE,1)]
    assert node['pot']==550 and node['bets']==[0,0]
    row=proof(root,sub,node,game_reach(root,sub)[0])
    row.update(source_run_id=ref['run'],source_sha256=ssha,archive_sha256=ref['sha256'],source_archive=ref['name'],
               spot='CO_BB',family='SRP',flop=flop,turn=sub['turn'],version=version,public_board=public,line=LINE,acting_seat=1,
               source_actions=node['acts'],root_sha256=rsha,gto_gap_pct=sub['info']['gto_expl_pct'],
               locked_hero_gap_pct=sub['info'].get('hero_gap_pct'),root_gto_stage_gap_pct=root['info']['gto_expl_pct'],
               root_applied_rust_lock_nodes=sum(x['nodes'] for x in root['info'].get('lock_stats',{}).values()),
               subgame_applied_rust_lock_nodes=sum(x['nodes'] for x in sub['info'].get('lock_stats',{}).values()))
    assert row['status']=='POSITIVE_JOINT_REACH' and row['compatible_hole_card_pairs']>=row['strict_legal_combos']>0
    if version=='exp_ip':
        scope=lock_scope(sub,patterns,version)
        assert scope['observed_marginal_source_nodes']>0 and row['subgame_applied_rust_lock_nodes']>0
    source=dict(run=ref['run'],version=version,source_sha256=ssha,root=root,subgame=sub,manifest=manifest,
                archive_code=f'GHA_{artifact}',archive_sha256=ref['sha256'])
    provenance=dict(artifact=artifact,artifact_sha256=ref['sha256'],root_sha256=rsha,flop_job_sha256=rjobsha,
                    turn_job_sha256=jsha,source_sha256=ssha,run=ref['run'],head=ref['head'])
    return source,row,provenance


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('downloads',type=Path)
    args=cli.parse_args()
    refs=json.loads(PINS.read_bytes())
    reg=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes());model=reg['records'][MID]
    assert (model['frequency_rank'],model['solver_profile'],model['family'],model['street'])==(138,'CO_BB','SRP',2)
    group=dict(rank=138,model_id=MID,boards=[],pins=[])
    report=dict(schema='NL2_HU_B498_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    for flop,public,gid,eid in SELECTION:
        g,gr,gp=read_source(args.downloads,gid,refs[str(gid)],flop,public,'gto')
        e,er,ep=read_source(args.downloads,eid,refs[str(eid)],flop,public,'exp_ip')
        assert gr['source_actions']==er['source_actions']
        if 'gto_parent_source_run_id' in e['manifest']:
            assert e['root']==g['root'] and ep['root_sha256']==gp['root_sha256']
            e['verified_gto_parent']=dict(run=g['run'],sha256=gp['root_sha256'])
        board,pin=emit_board(model,g,e,public,LINE,texture(flop))
        assert pin['GTO_strict_combos']==gr['strict_legal_combos'] and pin['NL2_strict_combos']==er['strict_legal_combos']
        pin.update(original_gto_archive=gp,original_lock_archive=ep)
        if e.get('verified_gto_parent'):
            board['nl2_locked_variants'][0]['variant_label']='原始 GTO 翻牌範圍，轉河牌 NL2 局部鎖頻'
        if flop=='8s8h3d':pin['historical_restricted_flop_game_tree']=True
        for code,field in [('viewer_archive_code','viewer_sha256'),('locked_viewer_archive_code','locked_viewer_sha256')]:
            if code not in pin:continue
            viewer=EVIDENCE/f"NL2_MULTIBOARD_{pin[code]}.json.gz"
            blob=viewer.read_bytes();blob=blob[:9]+bytes([255])+blob[10:]
            viewer.write_bytes(blob);pin[field]=sha(blob)
        group['boards'].append(board);group['pins'].append(pin)
        report['references'][source_key(MID,er)]=er
        report['gto_references'][source_key(MID,gr)]=gr
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_bytes(json_bytes(group));REPORT.write_bytes(json_bytes(report))
    print('Three independently reachable CO checked rivers verified')


if __name__=='__main__':
    main()
