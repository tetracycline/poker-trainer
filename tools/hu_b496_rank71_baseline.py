"""Reverify the two surviving LMP50 river examples and independently gate fresh native flops."""
import argparse
import json
from pathlib import Path
import subprocess
import zipfile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, EVIDENCE, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b472_street_lock import POOL
from hu_b481_rank27_limp_rivers import check_limp_source
from hu_b483_locked_medium import proof
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import game_reach
from verify_hu_multiboard_100bb import lock_scope

MODEL = 'ln-iso-lmp_r_model-vlgh2t'
SPOT = 'LMP_CO_BB'
LINE = 'b50 c/x b50 c/'
FRESH = ('3c3d4h', '5c5d2h', '2c2d4h')
OLD = {'4s4h2d':'2d4h4s8s5c', '7s5h3d':'3d5h7s6c7h'}
VERSIONS = ('gto', 'exp_oop')
LEADS = Path('data/nl2_hu_b492_lead_inputs.json')
REPORT = Path('data/nl2_hu_b496_rank71_baseline_attempts.json')


def unpack(raw, digest):
    assert sha(raw) == digest
    return json.loads(raw)


def read_source(package, ref, version, flop, historical):
    artifact, run, zip_sha = ref['id'], ref['run'], ref['zip_sha256']
    meta = json.loads((package/f'{artifact}.json').read_bytes())
    assert (meta['id'],meta['digest'],meta['workflow_run']['id'],meta['workflow_run']['repository_id']) == (
        artifact,'sha256:'+zip_sha,run,1438346845)
    zpath = package/f'{artifact}.zip'
    assert sha(zpath.read_bytes()) == zip_sha
    with zipfile.ZipFile(zpath) as archive:
        efiles = [n for n in archive.namelist() if n.startswith(('trainer/evidence/','evidence/'))]
        assert {SOLVER,RUST} <= {archive.read(n).decode().strip() for n in efiles if n.endswith('.txt')}
        mf, = (n for n in efiles if n.endswith('.json') and not n.endswith('/pool_stats.json'))
        m = json.loads(archive.read(mf))
        assert (m['schema'],m['spot'],m['version'],m['flop'],m['pot_family']) == (
            'NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1',SPOT,version,flop,'LMP')
        assert (m['flop_size_profile'],m['restricted_tree_assumption'],m['flop_action_sizes'],m['selected_lines']) == (
            'lmp-50-only',True,['50%'],['b50 c'])
        assert m['turn_subgame_sizing']=={'ip':'50%,100%','oop':'50%,100%'} and not m['failures']
        assert m['pool_source_sha256']==POOL and m['preflop_ranges']['source']=='ASSUMED_EXPLICIT_169CLASS'
        def getgame(name,digest):
            name = 'solver/postflop/'+name
            game = unpack(archive.read(name),digest)
            job = json.loads(archive.read(name.replace('.json','.job.json')))
            assert job.get('hero') == (None if version=='gto' else 0)
            return game,job
        root,rjob = getgame(m['file_flop'],m['file_flop_sha256'])
        assert root['flop']==flop and (root['pot'],root['stack'])==(250,9900)
        assert rjob['flop_oop']==rjob['flop_ip']=='50%'
        assert [r['pat'] for r in rjob.get('locks',[])]==[r['pat'] for r in m['locks']]
        check_limp_source(dict(manifest=m,root_job=rjob,subgame_job=None))
        root_decision,=(n for n in root['nodes'] if n['line']=='' and len(n['board'])==6 and n['player']==0)
        root_response,=(n for n in root['nodes'] if n['line']=='b50' and len(n['board'])==6 and n['player']==1)
        assert 'b50' in root_decision['acts'] and 'c' in root_response['acts'] and root_response['bets']==[125,0]
        if historical:
            assert ref['root_sha256']==m['file_flop_sha256']
        else:
            assert meta['name']==f'B496-original-{flop}-{version}'
            assert m['marginal_lock_matching']=='RUST_FIRST_MATCH_POOLED_FALLBACK_EXACT_STREET'
            assert len(m['turns'])==len(set(m['turns']))==2
            assert set(m['turns'])=={c['turn'] for c in m['cases']+m['skipped']}
        pool_raw=archive.read('trainer/evidence/pool_stats.json') if not historical else None
        pool=unpack(pool_raw,POOL)['NL2'] if pool_raw else None
        if pool and version=='exp_oop':
            audit_patterns(root,rjob,m,pool,hero_seat=0)
        sources={}
        for c in m['cases']:
            assert c['line']=='b50 c'
            if historical:
                assert c['source_sha256']==ref['source_sha256']
            sub,sjob=getgame(c['source_path'],c['source_sha256'])
            turn=c['turn']
            assert (sub['flop'],sub['line0'],sub['turn'],sub['pot'],sub['stack'])==(flop,'b50 c',turn,500,9775)
            assert sjob['line0']==['b50','c','/'] and sjob['turn']==turn
            assert (sjob['pot'],sjob['stack'],sjob['rake_rate'],sjob['rake_cap'])==(500,9775,.05,1000)
            assert sjob['turn_oop']==sjob['turn_ip']=='50%,100%' and not sjob.get('river_donk')
            assert [r['pat'] for r in sjob.get('locks',[])]==[r['pat'] for r in m['locks']]
            parent,=(n for n in root['nodes'] if n['line']=='b50 c/' and n['board'].endswith(turn))
            for seat, name in enumerate(('oop_w','ip_w')):
                assert sjob[name]==[[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
            check_limp_source(dict(manifest=m,root_job=rjob,subgame_job=sjob))
            if pool and version=='exp_oop':
                audit_patterns(sub,sjob,m,pool,hero_seat=0)
            sources[turn]=dict(root=root,subgame=sub,manifest=m,run=run,version=version,source_sha256=c['source_sha256'],
                archive_code=f'GHA_{artifact}',archive_sha256=zip_sha,provenance=dict(original_artifact_id=artifact,
                original_run=run,original_zip_sha256=zip_sha,original_root_sha256=m['file_flop_sha256'],
                original_source_sha256=c['source_sha256'],trainer_commit=meta['workflow_run']['head_sha'],
                original_manifest_sha256=sha(archive.read(mf)),original_flop_path=m['file_flop'],original_subgame_path=c['source_path']))
    return sources


def observations(source):
    root,sub=source['root'],source['subgame']
    result={}
    masks=game_reach(root,sub)[0]
    for node in sub['nodes']:
        if (node['line'],node['player'],len(node['board']))!=(LINE,0,10):
            continue
        public=node['board']
        assert node['acts']==['x'] and node['pot']==1000 and node['bets']==[250,250] and sub['stack']-max(node['bets'])==9525
        response,=(n for n in sub['nodes'] if (n['line'],n['player'],n['board'])==('b50 c/x b50',0,public[:8]))
        assert response['bets']==[0,250] and 'c' in response['acts']
        row=proof(root,sub,node,masks)
        row.update(flop=sub['flop'],turn=sub['turn'],spot=SPOT,family='LMP',source_run_id=source['run'],
                   source_sha256=source['source_sha256'],archive_sha256=source['archive_sha256'],version=source['version'],
                   root_sha256=source['provenance']['original_root_sha256'],gto_gap_pct=sub['info']['gto_expl_pct'],
                   locked_hero_gap_pct=sub['info'].get('hero_gap_pct'),original_archive_id=source['provenance']['original_artifact_id'],
                   lock_scope=lock_scope(sub,source['manifest']['locks'],source['version']))
        if source['version']!='gto':
            row.update(root_applied_rust_lock_nodes=sum(r['nodes'] for r in root['info'].get('lock_stats',{}).values()),
                       subgame_applied_rust_lock_nodes=sum(r['nodes'] for r in sub['info'].get('lock_stats',{}).values()))
        result[public]=row
    return result


def check_board(model, sources, flop, public):
    g,e=sources
    board,pin=emit_board(model,g,e,public,LINE,'LOW' if flop=='7s5h3d' else 'PAIRED')
    assert board and pin
    board.update(source_kind='ASSUMED_PREFLOP_RANGES',restricted_flop_size_profile='LMP_50PCT_ONLY',
                 river_tree_scope='ORIGINAL_RIVER_OOP_CHECK_ONLY')
    for tag,s in zip(('GTO','NL2'),sources,strict=True):
        pin[tag+'_archive_provenance']=s['provenance']
    view=EVIDENCE/f'NL2_MULTIBOARD_{pin["viewer_archive_code"]}.json.gz'
    raw=view.read_bytes()
    raw=raw[:9]+bytes([255])+raw[10:]
    view.write_bytes(raw)
    pin['viewer_sha256']=sha(raw)
    return board,pin


def qualified(source,row):
    info=source['root']['info']
    return (row['status']=='POSITIVE_JOINT_REACH' and 0<=info['gto_expl_pct']<=.5 and 0<=row['gto_gap_pct']<=.5 and
            (source['version']=='gto' or (0<=info['hero_gap_pct']<=.5 and 0<=row['locked_hero_gap_pct']<=.5 and
             row['lock_scope']['observed_marginal_source_nodes']>0)))


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--downloads',type=Path)
    cli.add_argument('--run',type=int)
    cli.add_argument('--historical-only',action='store_true')
    cli.add_argument('--list-originals',action='store_true')
    args=cli.parse_args()
    historical={g['flop']:g for g in json.loads(LEADS.read_bytes())['groups'].values() if g['spot']==SPOT and g['flop'] in OLD}
    if args.list_originals:
        print(*(g[v]['id'] for g in historical.values() for v in VERSIONS))
        return
    reg=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())
    model=reg['records'][MODEL]
    assert (model['label'],model['frequency_rank'],model['assumed_model_node_spr'])==('APPROX',71,9.916)
    previous={b['flop']:b for b in model['remaining_exact_board_evidence']}
    assert set(previous)==set(OLD)
    group=dict(rank=71,model_id=MODEL,actor='BB_OOP',line=LINE,spot=SPOT,boards=[],pins=[],
               trainer_scope=json.loads(subprocess.check_output(['node','tools/hu_b496_rank71_route.cjs'])))
    report=dict(rank=71,model_id=MODEL,run=args.run,scope='LMP50_ORIGINAL_RIVER_OOP_CHECK_ONLY',attempts={})
    refs={}
    if not args.historical_only:
        assert args.run>0
        members=json.loads((args.downloads/'run.json').read_bytes())['artifacts']
        fresh={r['name']:dict(id=r['id'],run=args.run,zip_sha256=r['digest'].removeprefix('sha256:')) for r in members}
    for flop in (*OLD, *(FRESH if not args.historical_only else ())):
        old=flop in OLD
        spec=historical.get(flop,{}) if old else {v:fresh.get(f'B496-original-{flop}-{v}') for v in VERSIONS}
        if any(not spec.get(v) for v in VERSIONS):
            report['attempts'][flop]=dict(status='MISSING_ORIGINAL_ARTIFACT');continue
        pair=[read_source(args.downloads,spec[v],v,flop,old) for v in VERSIONS]
        attempts=[]
        possible=[]
        for turn in sorted(set(pair[0])&set(pair[1])):
            sources=[s[turn] for s in pair]
            tables=[observations(s) for s in sources]
            for public in sorted(set(tables[0])|set(tables[1])):
                if old and public!=OLD[flop]:
                    continue
                rows=[t.get(public) for t in tables]
                attempts.append(dict(public_board=public, gto=rows[0], exp_oop=rows[1]))
                if all(r and qualified(s,r) for s,r in zip(sources,rows)):
                    possible.append((public,sources,rows))
        report['attempts'][flop]=dict(status='PAIRED_POSITIVE' if possible else 'NO_VERIFIED_PAIR',
                                     originals=spec if not old else {v:spec[v] for v in VERSIONS},tested_nodes=attempts)
        if old:
            assert len(possible)==1
        if not possible:
            continue
        public,sources,rows=possible[0]
        board,pin=check_board(model,sources,flop,public)
        assert pin['GTO_strict_combos']==rows[0]['strict_legal_combos'] and pin['NL2_strict_combos']==rows[1]['strict_legal_combos']
        assert pin['GTO_compatible_hole_card_pairs']==rows[0]['compatible_hole_card_pairs'] and pin['NL2_compatible_hole_card_pairs']==rows[1]['compatible_hole_card_pairs']
        if old:
            baseline=previous[flop]
            assert baseline['source_sha256']==sources[0]['source_sha256'] and baseline['strict_full_street_combo_reachable']==pin['GTO_strict_combos']
            prev,=(v for v in baseline['nl2_locked_variants'] if v['sha256']==sources[1]['source_sha256'])
            assert prev['strictly_reachable_combos']==pin['NL2_strict_combos']
            board['nl2_locked_variants']=[dict(board['nl2_locked_variants'][0],**prev)]
        else:
            # Retain the exact authenticated original ZIPs for future conditional solves and replay.
            for v in VERSIONS:
                artifact=spec[v]['id']
                target=EVIDENCE/f'B496_{artifact}.zip'
                target.write_bytes((args.downloads/f'{artifact}.zip').read_bytes())
            row=dict(rows[1],gto=rows[0])
            key=compact([MODEL,public,LINE,0,row['source_run_id'],row['source_sha256']]).decode()
            refs[key]=row
        group['boards'].append(board);group['pins'].append(pin)
    if args.historical_only:
        assert len(group['boards'])==2
        print('Original two-seat GTO and EXP verified for both legacy boards')
        return
    assert 2<=len(group['boards'])==len({b['flop'] for b in group['boards']})<=5
    report['verified_board_count']=len(group['boards'])
    report['eligible_for_restoration']=bool(refs)
    if refs:
        (EVIDENCE/'reverified/rank71.json').write_bytes(json_bytes(group))
        Path('data/nl2_hu_b496_locked_medium.json').write_bytes(compact(dict(
            schema='NL2_HU_B496_ORIGINAL_LOCKED_MEDIUM_V1',references=refs))+b'\n')
    REPORT.write_bytes(compact(report)+b'\n')
    print('rank71',len(group['boards']),'distinct dual-positive native baseline flops')


if __name__=='__main__':
    main()
