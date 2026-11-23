"""Replay the exact priced SB river route and intersect both original strategies with its trainer cells."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b518_rank220_native import measured_rates
from hu_b467_river_source_gate import EVIDENCE, json_bytes, sha
from hu_b483_locked_medium import POOL
from hu_b519_sb_barrels import HISTORY, MODELS, observations, pin_from_metadata
from hu_b514_turn_stab import rates
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import load_original, replay_native
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board, source_case

DATA = Path('data')
B519 = 45112310600
FRESH = {
    15: ('AhJh4s','As8s5h','AdQd6s','AcTc3d','Ah9d3c'),
    16: ('KsJs6h','Qh9h4d','Kh8d5h','JdTd4c','Qc8c3h'),
}
PARENTS = {'Jh8s5d':(14790353462,'4s'), 'QsTc5h':(14790391845,'3h'), 'Ks9h5d':(14789444503,'7s')}
ARCHIVES = {'AsTh4d':14789244161,'As9h2d':14790081899,'Js9h4d':14790321775}
PREFERRED = {'9s6h3d':'3d6h9sTs7c','KsQh4d':'4dQhKsTc4c','Ks7h2d':'2d7hKs9d5s'}
COLUMNS = {'TPG':0,'TPW':1,'MID':2,'DRAW':3,'WDRAW':4}


def tx(public):
    ranks, suits = public[::2], public[1::2]
    if max(Counter(suits).values()) >= 3:
        return 'mono'
    if len(set(ranks)) < len(ranks):
        return 'paired'
    if 'A' in ranks:
        return 'A_high'
    if any(c in ranks for c in 'KQ'):
        return 'KQ_high'
    return 'mid_high' if any(c in ranks for c in 'JT') else 'low'


def witnesses(hands, public, allowed, hcls, classes):
    kept = []
    for cards in sorted(hands):
        hand = ''.join(cards)
        cells = [tx(public[:s])+':'+str(COLUMNS.get(c,-1)) for s,c in
                 ((6,hcls(hand,public[:6])),(8,hcls(hand,public[:8])),(10,classes(hand,public)[0]))]
        if cells[0] in allowed[0] and cells[1] in allowed[1] and cells[2] in allowed[1]:
            kept.append(dict(hand=hand, flop_cell=cells[0], turn_cell=cells[1], river_cell=cells[2]))
    return kept


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--originals',type=Path,required=True)
    parser.add_argument('--solver',type=Path,required=True)
    parser.add_argument('--run',type=int,required=True)
    parser.add_argument('--head',required=True)
    args = parser.parse_args()
    solver = args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    raw=(solver/'inputs/pool_stats.json').read_bytes()
    assert args.run>0 and sha(raw)==POOL
    pool=json.loads(raw)['NL2']
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    import ranges
    pins=json.loads((DATA/'nl2_hu_b519_artifacts.json').read_bytes())
    pins.update(json.loads((DATA/'nl2_hu_b536_completed_artifacts.json').read_bytes()))

    def original(rank,aid,flop,turn,version):
        return load_original(args.originals,aid,pins[str(aid)],'SB_BB',flop,turn,version,pot=600,stack=9700,
                             flop_line=MODELS[rank][1],pipeline=pipeline,ranges=ranges)

    sys.path.insert(0,str(Path(__file__).resolve().parent/'lines_pipeline'))
    from run10_common import hcls, classes
    allowed=json.loads(subprocess.check_output(['node','tools/hu_b536_sb_route_cells.cjs'],text=True))
    models=json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records']
    metadata={m['name']:m for m in (json.loads(p.read_bytes()) for p in args.originals.glob('*.json'))}
    attempts, groups, bindings=[],{},{}
    locked=dict(schema='NL2_HU_B536_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})

    def evaluate(rank,flop,turn,gto,lock):
        mid,flop_line,pot,stack=MODELS[rank]
        model=models[mid]
        line=flop_line+'/b50 c/'
        group=groups.setdefault(rank,dict(rank=rank,model_id=mid,boards=[],pins=[]))
        row=dict(rank=rank,flop=flop,turn=turn,rivers={},selected=None)
        attempts.append(row)
        versions=[]
        for src in (gto,lock):
            source=src['source']
            if source['subgame'] is None or not all(0<=x<=.5 for x in
                  [source['subgame']['info']['gto_expl_pct'],source['subgame']['info'].get('hero_gap_pct') or 0]):
                row['status']='NATIVE_SOURCE_OUTSIDE_GATE'
                return
            versions.append(observations(source,flop_line,pot,stack,src['identity']['root_sha256']))
        g,e=gto['source'],lock['source']
        priority=PREFERRED.get(flop)
        for public in sorted(versions[0].keys()&versions[1].keys(),key=lambda x:(x!=priority,x)):
            gr,er=[o[public] for o in versions]
            evidence=dict(gto_pairs=gr['compatible_hole_card_pairs'],lock_pairs=er['compatible_hole_card_pairs'])
            row['rivers'][public]=evidence
            if min(evidence.values())<1:
                continue
            original_hands, fitted_hands=[source_case(model,s,public,line,0)[1] for s in (g,e)]
            shared=original_hands&fitted_hands
            passed=witnesses(shared,public,allowed[str(rank)],hcls,classes)
            evidence.update(shared_hands=len(shared),rendered_hands=passed)
            if not passed or row['selected'] or any(b['flop']==flop for b in group['boards']):
                continue
            b,p=emit_board(model,g,e,public,line,texture(flop))
            assert p['common_legal_hero_combos']==len(shared)
            p['rendered_route_hands']=passed
            p['original_gto_archive']=gto['identity']
            p['locked_parent_or_archive']=lock['identity']
            v=b['nl2_locked_variants'][0]
            if 'verified_gto_parent' in e:
                v.update(variant_label='原始 GTO 翻牌，轉河分街 NL2 鎖頻',pool_sha256=POOL,
                         measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=rates(e),
                         gto_parent_source_run_id=g['run'],gto_parent_source_sha256=gto['identity']['root_sha256'])
            if 'actual_turn_job_lock_coverage' in e:
                v.update(variant_label='完整翻牌與轉河牌局部 NL2 鎖頻',pool_sha256=POOL,
                         measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=measured_rates(e))
            v.update(viewer_archive_code=p.get('locked_viewer_archive_code',p['viewer_archive_code']),
                     viewer_sha256=p.get('locked_viewer_sha256',p['viewer_sha256']))
            group['boards'].append(b);group['pins'].append(p)
            bindings.setdefault(rank,[]).append((gr,er))
            row['selected']=public
        row['status']='RENDERED_WITNESS' if row['selected'] else 'NO_ADDITIONAL_RENDERED_WITNESS'

    legacy=args.originals/'14529402679.zip'
    assert sha(legacy.read_bytes())==pins['14529402679']['sha256']
    with ZipFile(legacy) as z:
        name,=(n for n in z.namelist() if n.startswith('evidence/') and n.endswith('.json'))
        old,=(c for c in json.loads(z.read(name))['cases'] if (c['flop'],c['turn'],c['line'])==('AsTh4d','4s','b75 c'))
        root=z.read('solver/postflop/'+old['flop_json'])
        assert sha(root)==old['flop_sha256']
        gap=json.loads(root)['info']['gto_expl_pct']
        assert gap>.5
        attempts.append(dict(rank=15,flop='AsTh4d',turn='4s',status='LOCKED_ROOT_GTO_STAGE_OUTSIDE_GATE',root_gap_pct=gap))
    for rank, entries in HISTORY.items():
        for flop,turn,gid,eid in entries:
            g=original(rank,gid,flop,turn,'gto')
            if eid:
                e=original(rank,eid,flop,turn,'exp_oop')
            else:
                aid=ARCHIVES[flop]
                pkg=args.originals/f'{aid}.zip'
                assert sha(pkg.read_bytes())==pins[str(aid)]['sha256']
                code=f'B519_R15_{flop.upper()}_EXP_OOP'
                dest=EVIDENCE/f'NL2_{code}.json.gz'
                with ZipFile(pkg) as z:
                    dest.write_bytes(z.read(dest.name))
                e=dict(identity=g['identity'],source=replay_native(g,'exp_oop',pool,pipeline,dest,B519,code))
            evaluate(rank,flop,turn,g,e)
    for flop,(aid,turn) in PARENTS.items():
        g=original(16,aid,flop,turn,'gto')
        source=g['source']; mid,line,pot,stack=MODELS[16]
        gr=observations(source,line,pot,stack,g['identity']['root_sha256'])
        screening={}
        for public,row in gr.items():
            hands=source_case(models[mid],source,public,line+'/b50 c/',0)[1] if row['compatible_hole_card_pairs'] else set()
            screening[public]=witnesses(hands,public,allowed['16'],hcls,classes)
        assert not any(screening.values())
        attempts.append(dict(rank=16,flop=flop,status='NO_RENDERED_HAND_IN_COMPLETED_GTO',rivers=screening))
    for rank, flops in FRESH.items():
        line=MODELS[rank][1]
        for flop in flops:
            turns=pipeline.turns_for(flop,3)
            by_turn={t:{} for t in turns}
            for version in ('gto','exp_oop'):
                name=f'NL2-B536-{flop}-{version}'
                m=metadata.get(name)
                if not m:continue
                pin=pin_from_metadata(m)
                assert pin['run']==args.run and pin['head']==args.head
                aid=m['id']; pins[str(aid)]=pin
                pkg=args.originals/f'{aid}.zip'
                assert sha(pkg.read_bytes())==pin['sha256']
                with ZipFile(pkg) as z:
                    mf=f'trainer/evidence/{flop}-{version}.json'
                    if mf not in z.namelist():continue
                    manifest=json.loads(z.read(mf))
                    if manifest['failures'] or not manifest['cases']:continue
                    assert (manifest['selected_lines'],manifest['turns'],manifest['marginal_lock_matching'])==([line],turns,'RUST_FIRST_MATCH_POOLED_FALLBACK_EXACT_STREET')
                    assert manifest['flop_size_profile']=='full'
                    for case in manifest['cases']:
                        turn=case['turn']
                        files=(manifest['file_flop'],case['source_path'])
                        native=[json.loads(z.read('solver/postflop/'+f)) for f in files]
                        if any(game['info']['gto_expl_pct']>.5 or (version=='exp_oop' and game['info']['hero_gap_pct']>.5) for game in native):continue
                        src=original(rank,aid,flop,turn,version)
                        if version=='exp_oop':
                            for st, f, game in zip(('actual_flop_job_lock_coverage','actual_turn_job_lock_coverage'),files,native,strict=True):
                                job=json.loads(z.read('solver/postflop/'+f[:-5]+'.job.json'))
                                src['source'][st]=audit_patterns(game,job,manifest,pool,hero_seat=0)
                        by_turn[turn][version]=src
            for turn,pair in by_turn.items():
                if len(pair)==2:evaluate(rank,flop,turn,pair['gto'],pair['exp_oop'])
                else:attempts.append(dict(rank=rank,flop=flop,turn=turn,status='NO_COMPLETED_CONVERGED_PAIR'))
    # Keep all positive partials reproducible under their actual solver identity.
    for group in groups.values():
        for pin in group['pins']:
            for key in ('original_gto_archive','locked_parent_or_archive'):
                aid=pin[key]['artifact_id']
                name=f'NL2_B536_ORIGINAL_{aid}.zip'
                shutil.copyfile(args.originals/f'{aid}.zip',EVIDENCE/name)
    for rank,group in groups.items():
        assert len(group['boards'])==len({b['flop'] for b in group['boards']})
        if len(group['boards'])<3:continue
        (EVIDENCE/f'reverified/rank{rank}.json').write_bytes(json_bytes(group))
        for gr,er in bindings[rank]:
            locked['references'][source_key(group['model_id'],er)]=er
            locked['gto_references'][source_key(group['model_id'],gr)]=gr
    counts={k:len(v['boards']) for k,v in groups.items()}
    (DATA/'nl2_hu_b536_sb_barrel_outcomes.json').write_bytes(json_bytes(dict(run=args.run,counts=counts,verified_pairs=groups,attempts=attempts)))
    (DATA/'nl2_hu_b536_locked_medium.json').write_bytes(json_bytes(locked))


if __name__=='__main__':
    main()
