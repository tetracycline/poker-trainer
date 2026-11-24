"""Read rank 46's six immutable strategy archives and replay rank 151's exact display route."""
import argparse
import base64
import hashlib
import json
import subprocess
from pathlib import Path
from zipfile import ZipFile

from hu_b568_caller_rivers import hand_cell
from hu_sequential_cfr_reach import accepted, cardkey, compatible_node_reach, game_reach

PINS = [{'digest': '7583287177315c74022553f0b64dc91d39c95a9dee0f84329dd99b22564c273e',
  'id': 14600026283,
  'name': 'nl2-multiboard-B3-LMP_CO_BB-gto-8s8h3d',
  'run': 44666294821},
 {'digest': 'c891339f9dfeb072f96562827956f59c6659623252f813ef2ebae4e190806cef',
  'id': 14599769541,
  'name': 'nl2-multiboard-B3-LMP_CO_BB-exp_ip-8s8h3d',
  'run': 44666294821},
 {'digest': 'f6d4d734bcb9d35f9c779e5b0d9853b23217bb1b44ef17b73ef35f4ef2fb0c11',
  'id': 14599037935,
  'name': 'nl2-multiboard-B3-LMP_CO_BB-gto-9s6h3d',
  'run': 44666294821},
 {'digest': 'f435c405bf069d666bf3b08e51e1a731e560b912e14ea6b97e7d5eca38d45ffb',
  'id': 14699135035,
  'name': 'nl2-multiboard-B210_R46_B3-LMP_CO_BB-exp_ip-9s6h3d',
  'run': 44882669727},
 {'digest': 'a9c69fec0313802717caaf2f046632020e9b523d67f88aa373a09c6d627cb809',
  'id': 14721557248,
  'name': 'nl2-multiboard-B286_R46_LMP_7S7H2D-LMP_CO_BB-gto-7s7h2d',
  'run': 44939456600},
 {'digest': '5923efb3b2eb93ef4380a3f73ed15fa90529ea022e63b256d8e184e33af6b9d0',
  'id': 14724203804,
  'name': 'nl2-multiboard-B288_R46_7S7H2D-LMP_CO_BB-exp_ip-7s7h2d',
  'run': 44947726457}]
LINE = 'x b50 c/x x/x'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def archived(directory, pin):
    path = directory / f"{pin['id']}.zip"
    assert digest(path.read_bytes()) == pin['digest'], path
    with ZipFile(path) as archive:
        manifest_path, = [n for n in archive.namelist() if n.startswith('evidence/') and n.endswith('.json')]
        manifest = json.loads(archive.read(manifest_path))
        base = 'solver/postflop/'
        root_path = base + manifest['file_flop']
        root_bytes = archive.read(root_path) if root_path in archive.namelist() else None
        case, = [c for c in manifest['cases'] if c['line'] == 'x b50 c']
        sub_path = base + case['source_path']
        sub_bytes = archive.read(sub_path)
        job_bytes = archive.read(sub_path.removesuffix('.json') + '.job.json')
        assert digest(sub_bytes) == case['source_sha256']
        assert (manifest['spot'], manifest['n_NL2_hands']) == ('LMP_CO_BB', 2334487)
        assert pin['name'].endswith(f"-{manifest['spot']}-{manifest['version']}-{manifest['flop']}")
        sub = json.loads(sub_bytes)
        job = json.loads(job_bytes)
        assert (job['line0'], sub['line0'], sub['pot'], sub['stack']) == (['x','b50','c','/'], 'x b50 c', 500, 9775)
        if manifest['version'] == 'exp_ip':
            assert job['hero'] == 1 and job['locks'] and manifest['locks']
        else:
            assert manifest['version'] == 'gto' and not job.get('locks') and sub['info']['gto_expl_pct'] <= 0.5
        return manifest, root_bytes, sub, digest(job_bytes), case['source_sha256']


def screen(root, sub, route):
    flop, = {node['board'] for node in root['nodes'] if len(node['board']) == 6}
    prefix = {n['line']: n for n in root['nodes'] if n['board'] == flop}
    assert [prefix[k]['player'] for k in ('', 'x','x b50')] == [0,1,0]
    bb = accepted(prefix[''], root['hands'], 'x') & accepted(prefix['x b50'], root['hands'], 'c')
    co = accepted(prefix['x'], root['hands'], 'b50')
    primary = [h for h in co if hand_cell(''.join(h), flop)[0] in route['flop']]
    blockers = [h for h in primary if any(set(h).isdisjoint(v) for v in bb)]
    masks, _ = game_reach(root, sub)
    rows = []
    for n in sub['nodes']:
        if n['line'] != LINE:
            continue
        board = n['board']
        assert (n['player'], n['pot'], n['bets']) == (1,500,[0,0])
        assert n['acts'].count('x') == 1 and len(board) == 10
        key = f"{board}|{LINE}|1"
        exact = compatible_node_reach(root, sub, n, masks[key])
        counts = dict(flop=0,turn=0,river=0,displayed_check=0)
        accepted_hands = set()
        for hand, bits in zip(sub['hands'][1], base64.b64decode(exact['mask'],validate=True), strict=True):
            if not bits:
                continue
            for street, length in [('flop',6),('turn',8),('river',10)]:
                cell, _ = hand_cell(hand, board[:length])
                if cell not in route[street]:
                    break
                counts[street] += 1
            else:
                assert route['river'][cell] == '過'
                if bits & (1 << n['acts'].index('x')):
                    counts['displayed_check'] += 1
                    accepted_hands.add(''.join(cardkey(hand)))
        rows.append(dict(board=board, strict_co=exact['count'], compatible_bb=exact['compatible_opponent_combos'],
                         compatible_pairs=exact['compatible_hole_card_pairs'], sequential_displayed_co=counts,
                         displayed_hands=sorted(accepted_hands)))
    assert sorted(row['board'][-2:] for row in rows)==sorted(sub['rivers']) and len(rows)==2
    return dict(flop_bb_check_and_call=len(bb),flop_co_b50=len(co),flop_displayed_b50=len(primary),
                flop_displayed_with_compatible_bb=len(blockers),rivers=rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--originals',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    route=json.loads(subprocess.check_output(['node',str(Path(__file__).with_name('hu_b753_rank151_routes.cjs'))]))
    status=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records']
    parent=status[route['turn_source']]
    assert parent['label']=='CERT-MULTIBOARD' and route['line']==LINE
    evidence={r['flop']:r for r in parent['certified_3_to_5_exact_flop_boards']}
    sources=[]
    roots={}
    for pin in PINS:
        manifest, raw, sub, job_sha, sub_sha=archived(args.originals,pin)
        flop=manifest['flop']
        root_sha=manifest['file_flop_sha256']
        if raw is not None:
            assert digest(raw)==root_sha
            roots[root_sha]=json.loads(raw)
        sources.append((pin,manifest,sub,job_sha,sub_sha))
    boards={}
    for pin,manifest,sub,job_sha,sub_sha in sources:
        flop=manifest['flop']
        mode=manifest['version']
        parent_board=evidence[flop]
        assert (parent_board['turn'],parent_board['actual_spr'])==(sub['turn'],19.55)
        if mode=='gto':
            assert (parent_board['source_run_id'],parent_board['source_sha256'])==(pin['run'],sub_sha)
        else:
            assert any((v['version'],v['run_id'],v['sha256'])==(mode,pin['run'],sub_sha) for v in parent_board['nl2_locked_variants'])
        root=roots[manifest['file_flop_sha256']]
        assert (root['flop'],root['pot'],root['stack'])==(flop,250,9900)
        outcome=screen(root,sub,route)
        boards.setdefault(flop,{})[mode]=dict(pin,root_sha256=manifest['file_flop_sha256'],turn=sub['turn'],
                                               job_sha256=job_sha,subgame_sha256=sub_sha,**outcome)
    for by_mode in boards.values():
        gto={row['board']:row for row in by_mode['gto']['rivers']}
        nl2={row['board']:row for row in by_mode['exp_ip']['rivers']}
        assert set(gto)==set(nl2) and len(gto)==2
        by_mode['common_displayed_co_by_board']={b:sorted(set(gto[b]['displayed_hands']) & set(nl2[b]['displayed_hands'])) for b in gto}
        assert not any(by_mode['common_displayed_co_by_board'].values())
        assert by_mode['gto']['flop_displayed_with_compatible_bb']==0
    out=dict(rank=151,actual_render=route,boards=boards,imported_policy_river_nodes=12,
             distinct_actual_rivers=6,source_actor_locked_turns_replayed=3,rank151_positive_flops=0,
             new_native_solves=0,new_actor_locks=0,rank151_eligible_locked_halfpot_assessments=0)
    args.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':
    main()
