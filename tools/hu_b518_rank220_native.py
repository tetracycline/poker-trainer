"""Verify the original CO river after a three-quarter-pot flop bet and a half-pot turn bet."""
import argparse
import gzip
import json
from pathlib import Path
from zipfile import ZipFile

from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import original
from hu_b483_locked_medium import POOL, proof
from hu_board_reach_corrections import source_key
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import game_reach
from verify_hu_multiboard_100bb import lock_scope

MODEL = 'ln-ipfr-r_model-nzfk3y'
FLOP_LINE, TURN_LINE = 'x b75 c', 'x b50 c'
LINE = FLOP_LINE+'/'+TURN_LINE+'/x'
VERSIONS = ('gto','exp_ip')
# First positive river in this frozen solver-deal order, at most one per new flop.
CASES = {
    'QdTd7c': ('9h', ('Tc','9c')),
    'Jh8h7d': ('6s', ('3s','Ks')),
    'AsKh6s': ('9c', ('3s','6d')),
    'KhJh9s': ('2c', ('Qh','5s')),
    'QsJc8s': ('7d', ('7s','Qc')),
}
HISTORICAL = (14529315586,14593317327,14593700327,14597269910,14597934573,14598482452)
PRIOR = Path('data/nl2_hu_b518_rank220_archived_reach.json')
RANGES = {'gto':'e140e5085bf28ef86962cf8783007566cb365b4f16e7ba4d01f7a63eba7a5e1f',
          'exp_ip':'0331f69c4212d328ec878523fd03f0d46b83948dbd0149310edde28bd3080d5b'}


def read(path):
    return json.loads(Path(path).read_bytes())


def archived_reach(directory):
    pins = read('data/nl2_hu_b498_rank138_artifacts.json')
    for run,group in read('data/nl2_hu_b485_original_artifacts.json').items():
        for item in group['artifacts']:
            pins.setdefault(str(item['id']),dict(item,run=int(run),head=group['trainer_commit']))
    evidence = []
    for aid in HISTORICAL:
        p = directory/f'{aid}.zip'
        pin = pins[str(aid)]
        assert sha(p.read_bytes()) == pin['sha256']
        with ZipFile(p) as archive:
            name, = (n for n in archive.namelist() if n.startswith(('evidence/','trainer/evidence/'))
                     and n.endswith('.json') and 'pool_stats' not in n)
            m = json.loads(archive.read(name))
            assert m['spot'] == 'CO_BB' and m['version'] in VERSIONS and not m.get('failures')
            for case in m['cases']:
                if case['line'] != FLOP_LINE:
                    continue
                raw_root = archive.read('solver/postflop/'+(m.get('file_flop') or case['flop_json']))
                raw = archive.read('solver/postflop/'+(case.get('source_path') or case['sub_json']))
                root,sub = json.loads(raw_root),json.loads(raw)
                assert sub['line0'] == FLOP_LINE and sub['turn'] == case['turn']
                assert 0 <= root['info']['gto_expl_pct'] <= .5 and 0 <= sub['info']['gto_expl_pct'] <= .5
                masks = game_reach(root,sub)[0]
                rows = {}
                for n in sub['nodes']:
                    if (n['line'],n['player']) in ((FLOP_LINE+'/',0),(LINE,1)):
                        r = proof(root,sub,n,masks)
                        rows[n['board']] = dict(line=n['line'],pairs=r['compatible_hole_card_pairs'],actor_combos=r['strict_legal_combos'])
                assert rows
                evidence.append(dict(artifact_id=aid,archive_sha256=pin['sha256'],run_id=pin['run'],head=pin['head'],
                                     version=m['version'],flop=root['flop'],turn=sub['turn'],root_sha256=sha(raw_root),
                                     subgame_sha256=sha(raw),nodes=rows))
    gtos = [r for r in evidence if r['version']=='gto']
    locked = [r for r in evidence if r['version']=='exp_ip']
    assert len(gtos)==5 and all(not n['pairs'] for r in gtos for n in r['nodes'].values())
    assert {r['flop'] for r in locked if any(n['pairs'] and n['line']==LINE for n in r['nodes'].values())}=={'As9h2d','8s8h3d'}
    assert all(r['flop'] not in CASES for r in evidence)
    return dict(rank=220,target_line=LINE,paired_historical_flops=0,archives=evidence)


def authenticate(directory, flop, version, turn, rivers):
    s = original(directory,flop,turn,version,batch='B518',spot='CO_BB',flop_line=FLOP_LINE,
                 flop_policy='checked-b75only',turn_policy='checked-b50only',turn_extract=TURN_LINE)
    m,root,fj = s['manifest'],s['root'],s['root_job']
    assert sha(compact([fj[k] for k in ('oop','ip')])) == RANGES[version]
    assert m['preflop_ranges']['full_sha256']=='787f719c752165262807f79b91daec81e1db86a83d557a4ea645ef2649f532c7'
    assert m['solver_pin']=='f0a173b3d9331c4ff8697359a838094f76babb35f16133e37bbd0bfb203b5253'
    assert m['solver_ranges_sha256']=='f2a302b483c79995ed90031b62e65a202ae7a1fdc8695f8940fe3e8291fb2bba'
    if s['subgame'] is None:
        return s
    sub,job = s['subgame'],s['subgame_job']
    parent, = (n for n in root['nodes'] if n['line']==FLOP_LINE+'/' and n['board'].endswith(turn))
    assert parent['bets']==[413,413] and parent['pot']==1376
    assert job['pot']==parent['pot'] and job['stack']==root['stack']-413==9337
    assert job['root_no_bet'] and job['line0']==[*FLOP_LINE.split(),'/']
    assert tuple(sub['rivers'])==rivers
    assert job['river_ip']==job['river_oop']=='50%,100%,a'
    for seat,key in enumerate(('oop_w','ip_w')):
        assert job[key]==[[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
    return s


def observe(source, river):
    root,sub = source['root'],source['subgame']
    target = [n for n in sub['nodes'] if n['line']==LINE and n['player']==1 and n['board'].endswith(river)]
    if not target:
        return None
    n, = target
    assert n['bets']==[688,688] and n['pot']==2752
    assert n['acts']==['x','b50','b100','a']
    child, = (c for c in sub['nodes'] if c['line']==LINE+' b50' and c['board']==n['board'] and c['player']==0)
    assert (child['pot'],child['bets'])==(4128,[688,2064])
    row = proof(root,sub,n,game_reach(root,sub)[0])
    v = source['version']
    scope = lock_scope(sub,source['manifest']['locks'],v)
    return dict(row,version=v,spot='CO_BB',family='SRP',flop=sub['flop'],turn=sub['turn'],
                source_run_id=source['run'],source_sha256=source['source_sha256'],archive_sha256=source['archive_sha256'],
                root_sha256=source['root_sha256'],gto_gap_pct=sub['info']['gto_expl_pct'],
                locked_hero_gap_pct=sub['info'].get('hero_gap_pct'),root_gto_stage_gap_pct=root['info']['gto_expl_pct'],
                root_locked_hero_gap_pct=root['info'].get('hero_gap_pct'),lock_scope=scope,
                root_applied_rust_lock_nodes=sum(x['nodes'] for x in root['info'].get('lock_stats',{}).values()),
                subgame_applied_rust_lock_nodes=sum(x['nodes'] for x in sub['info'].get('lock_stats',{}).values()))


def measured_rates(source):
    rates = []
    for stage,game,streets in (('actual_flop_job_lock_coverage','root',{1}), ('actual_turn_job_lock_coverage','subgame',{2,3})):
        for pattern,target in source[stage]['marginal_targets'].items():
            actual = source[game]['info']['lock_stats'].get(pattern)
            if target['street'] in streets and actual and actual['nodes']:
                token = 'r' if target['source'].endswith('bettor_vs_raise') else pattern.split(')?')[-1][:-1]
                rates.append(dict(street=target['street'],token=token,pattern=pattern,source=target['source'],n=target['n'],
                                  nodes=actual['nodes'],fold_pct=100*actual['fold'],raise_pct=100*actual['agg'],
                                  target_fold_pct=100*target['fold_target'],target_raise_pct=100*target['raise_target']))
    return rates


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--archives',type=Path)
    cli.add_argument('--downloads',type=Path)
    cli.add_argument('--run',type=int)
    args = cli.parse_args()
    if args.archives:
        assert not args.downloads
        result = archived_reach(args.archives)
        if PRIOR.exists():
            assert read(PRIOR)==result
        else:
            PRIOR.write_bytes(json_bytes(result))
        return
    assert args.downloads and args.run > 0
    model = read('data/nl2_hu_multiboard_status_current.json')['records'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'],model['family'],model['street'],model['assumed_model_node_spr'])==(220,'CO_BB','SRP',2,3.145)
    assert model['abstract_action_history']=='對手過、你下注、對手跟|對手過、你下注、對手跟|對手過'
    group = dict(rank=220,model_id=MODEL,boards=[],pins=[])
    report = dict(schema='NL2_HU_B518_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    attempts = []
    for flop,(turn,rivers) in CASES.items():
        row = dict(flop=flop,turn=turn,rivers=rivers,versions={},positive_pairs=[])
        attempts.append(row)
        sources = []
        for version in VERSIONS:
            manifest = args.downloads/f'NL2-B518-{flop}-{version}/trainer/evidence/{flop}-{version}.json'
            if not manifest.exists() or read(manifest).get('failures'):
                row['versions'][version] = 'MISSING_COMPLETED_ORIGINAL'
                continue
            s = authenticate(args.downloads,flop,version,turn,rivers)
            sources.append(s)
            row['versions'][version] = dict(root_sha256=s['root_sha256'],source_sha256=s['source_sha256'],
                                              gto_root_gap=s['root']['info']['gto_expl_pct'],cases=s['manifest']['cases'],
                                              skipped=s['manifest']['skipped'])
        if len(sources)!=2 or any(s['subgame'] is None for s in sources):
            row['status']='NO_PAIRED_TURN_SOURCE'
            continue
        g,e = sources
        assert g['manifest']['preflop_ranges']==e['manifest']['preflop_ranges']
        code=f'B518_R220_{flop.upper()}'
        blob=gzip.compress(compact(dict(run_id=args.run,flop=flop,turn=turn,source_arrays=sources)),mtime=0)
        digest=sha(blob)
        for s in sources:
            s.update(run=args.run,archive_code=code,archive_sha256=digest)
        row['archive_sha256']=digest
        rates=measured_rates(e)
        converged = all(0<=s[k]['info']['gto_expl_pct']<=.5 for s in sources for k in ('root','subgame'))
        converged &= all(0<=e[k]['info']['hero_gap_pct']<=.5 for k in ('root','subgame'))
        row['decisions']={}
        selected=None
        for river in rivers:
            pair = [observe(s,river) for s in sources]
            row['decisions'][river] = {s['version']:{k:o[k] for k in ('status','public_board','strict_legal_combos','compatible_hole_card_pairs')} if o else None
                                       for s,o in zip(sources,pair,strict=True)}
            if all(o and o['status']=='POSITIVE_JOINT_REACH' for o in pair):
                assert pair[0]['public_board']==pair[1]['public_board']
                row['positive_pairs'].append(river)
                if selected is None:
                    selected=pair
        if not converged or not {2,3}<=set(r['street'] for r in rates):
            row['status']='GAP_OR_MEASURED_LOCK_GATE'
            continue
        if not selected:
            row['status']='NO_PAIRED_POSITIVE_RIVER'
            continue
        gr,er=selected
        public=gr['public_board']
        assert er['lock_scope']['observed_marginal_source_nodes'] and er['subgame_applied_rust_lock_nodes']
        b,p=emit_board(model,g,e,public,LINE,texture(flop))
        assert (b['actual_pot_bb'],b['actual_effective_stack_bb'])==(27.52,86.49)
        assert (p['GTO_compatible_hole_card_pairs'],p['NL2_compatible_hole_card_pairs'])==(gr['compatible_hole_card_pairs'],er['compatible_hole_card_pairs'])
        b['nl2_locked_variants'][0].update(variant_label='原始翻牌至河牌 NL2 鎖頻',measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',
            pool_sha256=POOL,applied_street_rates=rates,viewer_archive_code=p['viewer_archive_code'],viewer_sha256=p['viewer_sha256'])
        (EVIDENCE/f'NL2_{code}.json.gz').write_bytes(blob)
        group['boards'].append(b)
        group['pins'].append(p)
        row.update(status='PAIRED_POSITIVE',selected=public)
        report['gto_references'][source_key(MODEL,gr)] = gr
        report['references'][source_key(MODEL,er)] = er
    count=len(group['boards'])
    assert len({b['flop'] for b in group['boards']})==count<=5
    if count>=3:
        (EVIDENCE/'reverified/rank220.json').write_bytes(json_bytes(group))
        Path('data/nl2_hu_b518_locked_medium.json').write_bytes(json_bytes(report))
    Path('data/nl2_hu_b518_rank220_attempts.json').write_bytes(json_bytes(dict(rank=220,model_id=MODEL,run_id=args.run,
        archived_reach_sha256=sha(PRIOR.read_bytes()),paired_flops=count,attempts=attempts)))


if __name__=='__main__':
    main()
