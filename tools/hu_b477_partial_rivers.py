"""Replay the original river cases behind five remaining APPROX models."""
import argparse
import gzip
import json
from pathlib import Path

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, json_bytes, publish_bytes, sha
from hu_multiboard_promote import FAM_ROOT, hero_seat
from hu_sequential_cfr_reach import compatible_node_reach, game_reach
from verify_hu_multiboard_100bb import lock_scope, source_nodes

DATA = Path('data')
OUT = DATA/'nl2_hu_b477_raw_river_pairs.json'
QUEUE = DATA/'nl2_hu_stage2_queue.json'
PARENT_ID = 'ln-ipc-t_model-1cla93g'
# The UTG cases can only be reused on these same named parents already certified by B354.
SOURCES = [
    ('LMP_CO_BB','KsQh4d','Tc',44666294821,(116,),
     (14601426559,'144919b63c7609d4256109db43d81f60004bad04a1bb7398759d238edc70f454'),
     (14602013161,'d47283bedc85746aea26f7c30028ffc4e6c20578919ccbb913174e05c605242c')),
    ('LMP_CO_BB','8s8h3d','5s',44666294821,(200,),
     (14600026283,'7583287177315c74022553f0b64dc91d39c95a9dee0f84329dd99b22564c273e'),
     (14599769541,'c891339f9dfeb072f96562827956f59c6659623252f813ef2ebae4e190806cef')),
    ('SB3_BTN','KsQh4d','Tc',44666290556,(232,),
     (14599605695,'0b6b5ddff20e0394c250171188d6f08cdb0e3d9194e5bb60ab4986cd9b41ffc9'),
     (14599228790,'7a71071e69f43cfce3e94a1af04c60ab973c6d6b7d955fba97235c96d98e903e')),
    ('UTG_CO','Ks7h2d','9d',44654973894,(213,237),
     (14593222610,'7278ba34b2899846aba8269d54177a3dd4b7848a4d8afcc740bb1bdb732995ea'),
     (14593611061,'7f99f7223510e27d5dc53371b0db06ba9787a3e481eabf2dc0aca8fefa477a84')),
    ('UTG_CO','8s8h3d','5s',44971994483,(213,237),
     (14734625150,'54c3fec2359dee93337b22aff4ea28813584c9686c81f2df10ded1c2003888ec'),
     (14733689362,'6b33c24bbbc6f1f8d5db7b29607813ab90ce495a46a10e1e4dc93d2b9331bd91')),
    ('UTG_CO','Js9h4d','Ts',44971994483,(213,237),
     (14733963314,'9df129dbf97c76346091de7d7021e639a1071bf60fa26d9fcb6422c73d5277fa'),
     (14734635678,'90990cbb8a6756bb56b92624d74adab413da100682e6d1a318b8d5fb77002669')),
]
# Original root and river amounts are in hundredths of a big blind.
MODELS = {
    116: ('ln-iso-lmp_r_model-1c6f833','b33 c/x b50 c/x',1,832,9609),
    200: ('ln-iso-lmp_r_model-68efr6','x b50 c/x b50 c/x',1,1000,9525),
    232: ('ln-3bp-3b_r_model-19o21hu','x b33 c/x x/',0,3486,8307),
    213: ('ln-ipc-r_model-6ntgm7','b50 c/x x/x',1,1300,9425),
    237: ('ln-ipc-r_model-57gj58','b50 c/x b50 c/x',1,2600,8775),
}


def read(path):
    return json.loads(path.read_bytes())


def replay(directory, spec, version, archive, models, parents):
    spot,flop,turn,run,ranks = spec[:5]
    artifact,expected = archive
    folder = directory/str(artifact)
    assert sha(folder.with_suffix('.zip').read_bytes()) == expected
    evidence = folder/'evidence'
    assert {f.read_text().strip() for f in evidence.glob('*.txt')} == {SOLVER,RUST}
    manifest, = evidence.glob('*.json')
    m = read(manifest)
    assert (m['spot'],m['version']) == (spot,version) and not m['failures']
    line = MODELS[ranks[0]][1].split('/')[0]
    case, = (c for c in m['cases'] if (c['line'],c['turn'])==(line,turn))
    base = folder/'solver/postflop'
    root_path = base/(m.get('file_flop') or case['flop_json'])
    sub_path = base/(case.get('source_path') or case['sub_json'])
    root_sha,sub_sha = sha(root_path.read_bytes()),sha(sub_path.read_bytes())
    assert (root_sha,sub_sha) == (m.get('file_flop_sha256') or case['flop_sha256'],case.get('source_sha256') or case['sub_sha256'])
    root,sub = read(root_path),read(sub_path)
    assert (root['flop'],sub['flop'],sub['line0'],sub['turn']) == (flop,flop,line,turn)
    assert (root['pot']/100,root['stack']/100) == FAM_ROOT[spot]
    root_job,sub_job = (read(p.with_suffix('.job.json')) for p in (root_path,sub_path))
    for game,job in [(root,root_job),(sub,sub_job)]:
        assert (job['pot'],job['stack'],job['rake_rate'],job['rake_cap']) == (game['pot'],game['stack'],.05,1000)
        assert 0 <= game['info']['gto_expl_pct'] <= .5
        assert job.get('hero') == (None if version=='gto' else MODELS[ranks[0]][2])
        assert bool(job.get('locks')) == (version != 'gto')
        if version!='gto':
            assert 0 <= game['info']['hero_gap_pct'] <= .5
    patterns = m.get('locks') or []
    if version!='gto' and not patterns:
        patterns = m['pool_lock_evidence'][flop]['source_patterns']
    if version!='gto':
        assert [p['pat'] for p in patterns] == [p['pat'] for p in sub_job['locks']]
    scope = lock_scope(sub,patterns,version)
    assert version=='gto' or scope['observed_marginal_source_nodes']>0
    if spot=='UTG_CO':
        parent=parents[flop]
        parent_lock, = (s for s in parent['nl2_locked_variants'] if s['version']=='exp_ip')
        assert (parent['turn'],parent['actual_exact_action_line'],parent['acting_seat']) == (turn,'b50 c/x',1)
        original=(parent['source_run_id'],parent['source_sha256']) if version=='gto' else (parent_lock['run_id'],parent_lock['sha256'])
        assert (run,sub_sha)==original
    masks = game_reach(root,sub)[0]
    reports,viewer_cases = {},{}
    for rank in ranks:
        mid,line,seat,pot,stack = MODELS[rank]
        model = models[mid]
        assert model['solver_profile']==spot and hero_seat(model['preflop_text'])==seat
        if spot=='UTG_CO':
            assert model['source_id']==PARENT_ID
        if model['source_action']=='bet':
            assert 'b'+str(round(100*model['source_action_assumed_size_pot']))+' c' in line.split('/')[1]
        else:
            assert model['source_action']=='check' and line.split('/')[1]=='x x'
        spr=stack/pot
        assert abs(spr-model['approx_spr'])/max(1,spr)<=.05
        boards={}
        qualified=[]
        for node in sub['nodes']:
            board=node['board']
            if (len(board),node['line'],node['player'])!=(10,line,seat):
                continue
            assert board[6:8]==turn and (node['pot'],sub['stack']-max(node['bets']))==(pot,stack)
            key='|'.join((board,line,str(seat)))
            actual=compatible_node_reach(root,sub,node,masks[key])
            boards[board]=dict(actor_only_combos=masks[key]['count'],compatible_hero_combos=actual['count'],
                               compatible_hole_card_pairs=actual['compatible_hole_card_pairs'])
            qualified.extend(source_nodes(dict(sub,nodes=[node]),{'nodes':{key:actual}}))
        assert len(boards)==2
        reports[rank]=dict(artifact_id=artifact,original_archive_sha256=expected,root_sha256=root_sha,
                           source_sha256=sub_sha,source_run_id=run,boards=boards,gto_gap_pct=sub['info']['gto_expl_pct'],
                           locked_hero_gap_pct=sub['info'].get('hero_gap_pct'),
                           pool_observed_marginal_source_nodes=scope['observed_marginal_source_nodes'])
        viewer_cases[rank]=dict(spot=spot,pot_family=model['family'],version=version,source_sha256=sub_sha,flop=flop,
                                turn=turn,flop_line=sub['line0'],hands_by_seat=sub['hands'],nodes=qualified,
                                gto_exploitability_pct=sub['info']['gto_expl_pct'], locked_hero_gap_pct=sub['info'].get('hero_gap_pct'),
                                villain_lock_scope=scope)
    return reports,viewer_cases


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--downloads',type=Path)
    parser.add_argument('--list-artifacts',action='store_true')
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    if args.list_artifacts:
        print(' '.join(str(archive[0]) for spec in SOURCES for archive in spec[5:]))
        return
    if args.downloads is None:
        parser.error('--downloads is required to replay original sources')
    models={m['model_id']:m for m in read(QUEUE)['records']}
    registry=read(DATA/'nl2_hu_multiboard_status_current.json')['records']
    parent=registry[PARENT_ID]
    assert parent['frequency_rank']==79 and parent['label']=='CERT-MULTIBOARD'
    parents={b['flop']:b for b in parent['certified_3_to_5_exact_flop_boards']}
    result={}
    for spec in SOURCES:
        spot,flop,turn,run,ranks,gto_zip,locked_zip=spec
        locked_version='exp_ip' if MODELS[ranks[0]][2] else 'exp_oop'
        gto,gcases=replay(args.downloads,spec,'gto',gto_zip,models,parents)
        locked,lcases=replay(args.downloads,spec,locked_version,locked_zip,models,parents)
        for rank in ranks:
            mid,line,seat,pot,stack=MODELS[rank]
            assert registry[mid]['frequency_rank']==rank
            entry=result.setdefault(rank,dict(rank=rank,model_id=mid,source_model_id=models[mid]['source_id'],
                                       exact_line=line,acting_seat=seat,pot_bb=pot/100,effective_stack_bb=stack/100,
                                       model_spr=models[mid]['approx_spr'],verified_paired_flops=[],flops={}))
            gv,lv=gto[rank],locked[rank]
            assert gv['boards'].keys()==lv['boards'].keys()
            rivers=sorted(b for b,g in gv['boards'].items() if min(g['compatible_hole_card_pairs'],lv['boards'][b]['compatible_hole_card_pairs'])>0)
            record=dict(turn=turn,gto=gv,locked=lv,locked_version=locked_version,positive_paired_rivers=rivers)
            entry['flops'][flop]=record
            if not rivers:
                continue
            entry['verified_paired_flops'].append(flop)
            path=DATA/'solver_evidence'/f'NL2_MULTIBOARD_R{rank}_{run}.json.gz'
            payload=dict(schema='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1',source_run_id=run,
                         original_archive_sha256_by_version={'gto':gto_zip[1],locked_version:locked_zip[1]},
                         no_generic_texture_certification=True,errors=[],artifacts=[dict(cases=[gcases[rank],lcases[rank]])])
            if args.verify:
                assert gzip.decompress(path.read_bytes())==compact(payload)
            else:
                path.write_bytes(gzip.compress(compact(payload),mtime=0))
            record['viewer_file'],record['viewer_sha256']=path.name,sha(path.read_bytes())
    report=dict(schema='NL2_HU_B477_ORIGINAL_RIVER_PAIR_AUDIT_V1',minimum_distinct_flops=3,models=result)
    publish_bytes(OUT,json_bytes(report),args.verify)
    print({rank:len(r['verified_paired_flops']) for rank,r in result.items()})


if __name__=='__main__':
    main()
