"""Pair one new full-menu solve with the two independently verified rank146 originals."""
import argparse
import gzip
import json
from pathlib import Path

from hu_b467_river_source_gate import EVIDENCE, NoLegalRiver, compact, export_board, extract, json_bytes, sha
from hu_b470_rank73_new_rivers import original
from hu_b471_rank146_prior import ID, LINE, OUT as PRIOR
from hu_b463_rank45_gate import SOLVER, RUST

FLOP, TURN = 'KhQd5c','9s'
MODEL_SPR = 7.25


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--downloads',type=Path,required=True)
    parser.add_argument('--run-id',type=int,required=True)
    args = parser.parse_args()
    assert args.run_id > 0
    checkpoint = json.loads(PRIOR.read_bytes())
    assert (checkpoint['rank'],checkpoint['model_id'],checkpoint['line']) == (146,ID,LINE)
    assert [b['flop'] for b in checkpoint['boards']] == ['KsQh4d','QsJh4d']
    for b,p in zip(checkpoint['boards'],checkpoint['pins']):
        for code,digest in [(p['viewer_archive_code'],p['viewer_sha256']),(p['locked_viewer_archive_code'],p['locked_viewer_sha256'])]:
            assert sha((EVIDENCE / f'NL2_MULTIBOARD_{code}.json.gz').read_bytes()) == digest
        assert (b['actual_pot_bb'],b['actual_effective_stack_bb'],b['actual_exact_action_line']) == (13,94.25,LINE)
        assert p['GTO_compatible_hole_card_pairs']>0 and p['NL2_compatible_hole_card_pairs']>0
    missing = [ver for ver in ('gto','exp_oop') if not
               (args.downloads/f'NL2-B473-{FLOP}-{ver}'/'trainer/evidence'/f'{FLOP}-{ver}.json').is_file()]
    if missing:
        report = dict(rank=146,model_id=ID,flop=FLOP,turn=TURN,line=LINE,missing_originals=missing,
                      distinct_paired_flops=2,prior_gate_sha256=sha(PRIOR.read_bytes()))
        Path('data/nl2_hu_b473_rank146_new_flop.json').write_bytes(json_bytes(report))
        print('rank146 2/3, missing original source',missing)
        return
    new = [original(args.downloads,FLOP,TURN,ver,batch='B473',spot='UTG_CO',flop_line='b50 c',
                    flop_policy='oop-b50only',turn_policy='checkcheck',turn_extract='x x',root_pot=650,root_stack=9750)
           for ver in ('gto','exp_oop')]
    gto,exp=new
    for key in ('preflop_ranges','solver_pin','pool_source_sha256'):
        assert gto['manifest'][key] == exp['manifest'][key]
    code='B473_R146_KHQD5C'
    encoded = gzip.compress(compact(dict(run_id=args.run_id,solver=SOLVER,rust=RUST,
                                         flop=FLOP,turn=TURN,source_arrays=new)),mtime=0)
    (EVIDENCE / f'NL2_{code}.json.gz').write_bytes(encoded)
    pin=dict(flop=FLOP,turn=TURN,source_run_id=args.run_id,archive_code=code)
    result=dict(rank=146,model_id=ID,flop=FLOP,turn=TURN,line=LINE,archive_sha256=sha(encoded),
                prior_gate_sha256=sha(PRIOR.read_bytes()),compatible_deals_by_river={},prior_distinct_flops=2)
    public=None
    if all(s['subgame'] is not None for s in new):
        for source in new:
            for game in (source['root'],source['subgame']):
                assert 0 <= game['info']['gto_expl_pct'] <= .5
                if source['version']=='exp_oop': assert 0 <= game['info']['hero_gap_pct'] <= .5
        def river_cards(s):
            return {n['board'] for n in s['subgame']['nodes'] if len(n['board'])==10 and n['line']==LINE and n['player']==0}
        for board in sorted(river_cards(gto) & river_cards(exp)):
            counts={}
            for s in new:
                try:
                    _, count, _ = extract(s,LINE,MODEL_SPR,pin,board)
                except NoLegalRiver:
                    count=0
                counts[s['version']]=count
            result['compatible_deals_by_river'][board]=counts
            if public is None and min(counts.values())>0:
                public=board
    if public is not None:
        parent=dict(public_board=public[:8],source_kind='PINNED_PREFLOP_CFR',assumed_preflop_ranges=False,flop_texture='HIGH')
        b,p=export_board(pin,parent,new,146,LINE,MODEL_SPR,False,archive_digest=sha(encoded),public_board=public)
        assert (b['actual_pot_bb'],b['actual_effective_stack_bb'])==(13,94.25)
        ext=dict(rank=146,model_id=ID,actor='UTG_OOP',spot='UTG_CO',line=LINE,
                 boards=checkpoint['boards']+[b],pins=checkpoint['pins']+[p])
        (EVIDENCE/'extensions').mkdir(exist_ok=True)
        (EVIDENCE/'extensions/rank146.json').write_bytes(json_bytes(ext))
    result.update(selected_public_board=public,distinct_paired_flops=2+int(public is not None))
    Path('data/nl2_hu_b473_rank146_new_flop.json').write_bytes(json_bytes(result))
    print(f"rank146 {result['distinct_paired_flops']}/3 paired flops")


if __name__=='__main__':
    main()
