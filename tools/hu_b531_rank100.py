"""Check both original CO/BB policies and the rendered middle-pair route on distinct flops."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys

from hu_b467_river_source_gate import EVIDENCE, json_bytes, sha
from hu_b483_locked_medium import POOL
from hu_b496_rank71_baseline import qualified, read_source
from hu_b510_rank13_checked_stab import FLOPS as HISTORICAL
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board, source_case

sys.path.insert(0,str(Path(__file__).resolve().parent/'lines_pipeline'))
from run10_common import classes, hcls

MID = 'ln-iso-lmp_r_model-1hgiamg'
LINE = 'x b50 c/x x/'
DATA = Path('data')
FLOPS = {
    '6c4h2d': ('3h','Kc'), 'As7d4c': ('3h','Ts'), 'Th7c4d': ('3c','8h'),
    'Jc8d3h': ('Ts','2h'), '9c6d3s': ('Js','Th'),
}


def paired_texture(public):
    return len(set(public[::2])) < len(public)//2 and max(Counter(public[1::2]).values()) < 3


def assess(sources, model, public):
    g,e = sources
    observed = [audit_decision(s,public,LINE,0,s['provenance']['original_root_sha256']) for s in sources]
    audit = dict(public_board=public)
    if not all(o and qualified(s,o) for s,o in zip(sources,observed)):
        audit['status'] = 'NO_QUALIFYING_NATIVE_PAIR'
        return None,audit
    shared = source_case(model,g,public,LINE,0)[1] & source_case(model,e,public,LINE,0)[1]
    audit['common_legal_hands'] = len(shared)
    if any(paired_texture(public[:k]) for k in (6,8,10)):
        audit['status'] = 'NO_RENDERED_PAIRED_ROW'
        return None,audit
    hands = [''.join(h) for h in sorted(shared)]
    audit['middle_pair_route_witnesses'] = [h for h in hands if hcls(h,public[:6]) == hcls(h,public[:8]) == 'MID' and classes(h,public) == ['MID']]
    if not audit['middle_pair_route_witnesses']:
        audit['status'] = 'NO_COMMON_MIDDLE_PAIR_HAND'
        return None,audit
    audit['status'] = 'VERIFIED'
    return observed,audit


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('downloads', type=Path)
    cli.add_argument('--run', type=int, required=True)
    cli.add_argument('--head', required=True)
    cli.add_argument('--historical',action='store_true')
    args = cli.parse_args()
    subprocess.run(['node','tools/hu_b531_rank100_routes.cjs'],check=True)
    historical=args.historical
    batch='B510' if historical else 'B531'
    model=json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records'][MID]
    assert (model['frequency_rank'],model['solver_profile'],model['family'],model['assumed_model_node_spr'])==(100,'LMP_CO_BB','LMP',19.3)
    manifests=json.loads((args.downloads/'run.json').read_bytes())['artifacts']
    catalog={m['name']:m for m in manifests}
    medium=dict(schema='NL2_HU_B531_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    group=dict(rank=100,model_id=MID,boards=[],pins=[])
    attempts=[]
    for flop,turns in (HISTORICAL if historical else FLOPS).items():
        row=dict(flop=flop,archives={},rivers=[],selected=None)
        attempts.append(row)
        pairs=[]
        for v in ('gto','exp_oop'):
            item=catalog.get(f'{batch}-original-{flop}-{v}')
            if not item:
                row['archives'][v]=dict(status='MISSING_ORIGINAL')
                continue
            aid=item['id']
            meta=json.loads((args.downloads/f'{aid}.json').read_bytes())
            assert (meta['name'],meta['digest'],meta['workflow_run']['head_sha'],meta['workflow_run']['id']) == (item['name'],item['digest'],args.head,args.run)
            pin=dict(id=aid,run=args.run,zip_sha256=item['digest'].removeprefix('sha256:'))
            row['archives'][v]=pin
            sources=read_source(args.downloads,pin,v,flop,False,flop_line='x b50 c',batch=batch)
            assert all(s['manifest']['turns']==list(turns) for s in sources.values())
            pairs.append(sources)
        if len(pairs)!=2:
            continue
        for turn in turns:
            if not all(turn in pair for pair in pairs):
                continue
            g,e=[pair[turn] for pair in pairs]
            assert g['subgame']['rivers']==e['subgame']['rivers']
            for river in g['subgame']['rivers']:
                public = next((n['board'] for n in g['subgame']['nodes'] if (n['line'],n['player'],n['board'][-2:])==(LINE,0,river)),None)
                if public is None:
                    continue
                proof,audit = assess((g,e),model,public)
                row['rivers'].append(audit)
                if not proof or row['selected']:
                    continue
                assert not historical
                gr,er=proof
                b,p=emit_board(model,g,e,public,LINE,texture(flop))
                assert (b['actual_pot_bb'],b['actual_effective_stack_bb'],b['acting_seat'])==(5,97.75,0)
                assert p['common_legal_hero_combos']==audit['common_legal_hands']
                b.update(restricted_flop_bet_sizes_pct=[50],turn_root_allows_lead=True)
                b['nl2_locked_variants'][0].update(measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',pool_sha256=POOL,
                    variant_label='翻牌限半池，轉牌可領打半池或滿池，翻牌至河牌依 NL2 分街邊際頻率局部鎖頻')
                p.update(gto_archive_provenance=g['provenance'],locked_archive_provenance=e['provenance'],rendered_middle_pair_hands=audit['middle_pair_route_witnesses'])
                for s in (g,e):
                    src=args.downloads/f"{s['provenance']['original_artifact_id']}.zip"
                    shutil.copyfile(src,EVIDENCE/f"NL2_B531_R100_{flop.upper()}_{s['version'].upper()}.zip")
                medium['gto_references'][source_key(MID,gr)]=gr
                medium['references'][source_key(MID,er)]=er
                group['boards'].append(b)
                group['pins'].append(p)
                row['selected']=public
    count=len(group['boards'])
    assert count==len({b['flop'] for b in group['boards']})<=5
    if count>=3:
        (EVIDENCE/'reverified/rank100.json').write_bytes(json_bytes(group))
        (DATA/'nl2_hu_b531_locked_medium.json').write_bytes(json_bytes(medium))
    if historical:
        assert len(attempts)==3 and all(row['rivers'] for row in attempts) and count==0
        assert all(any(case.get('common_legal_hands',0)>0 for case in row['rivers']) for row in attempts)
    output=DATA/('nl2_hu_b531_rank100_historical.json' if historical else 'nl2_hu_b531_rank100_attempts.json')
    output.write_bytes(json_bytes(dict(rank=100,model_id=MID,run=args.run,head=args.head,verified_flops=count,attempts=attempts,model=group)))


if __name__=='__main__':
    main()
