"""Re-prove the BB's checked-to-50%-bet/call path and its checked-through river."""
import argparse
import gzip
import json
from pathlib import Path
import zipfile

from hu_b463_rank45_gate import SOLVER,RUST
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import original
from hu_b483_locked_medium import proof
from hu_sequential_cfr_reach import game_reach

MODELS={14:('ln-bb-t_model-cge9jz','x b50 c/'),113:('ln-bb-r_model-123cy01','x b50 c/x x/')}
FROZEN=Path('data/nl2_hu_multiboard_status_v53_b465_rank218.json')
POOL='c2d7c8a6b0dd044a5e546256207a6e46f626b083ecb598b1e6d98bb928611c4a'
# The first pair is already complete. Each remaining full-menu GTO source needs only the independently locked BB solve.
CASES=(
    ('Js9h4d','Ts','JT_HIGH',14597934573,14597984483),
    ('Js9h3d','4s','JT_HIGH',14728659459,None),
    ('Js9s4s','8c','MONOTONE',14729431007,None),
    ('Td8h3c','2h','JT_HIGH',14757075648,None),
)
PINS={
    14597934573:(44666290556,'91aaaf4661b62c114285a57f390fc6750e996471','247c05663e8edd668a317d3104c33b0ab780ce26722923bc76dc3cff4fea04ec','6b5a75705f9586861ed4809f16078b5ad7e83b43775ce2cb6be482b7ee517e8a'),
    14597984483:(44666290556,'91aaaf4661b62c114285a57f390fc6750e996471','908762465dfa24c8958c0dc7b02e9ab6fb15dc39b8a0eb18d8a3a9fe42e7da0f','2a22a654472055c4a1aa69bcd0f535d90e2fa12df1b47d9d1821fc1a6ebdc0af'),
    14728659459:(44959135103,'65c3e91781c445b1b1dbeba0b045edb11f8bcd13','bbaff321c26035ec829b3678831557a87007356144f91919d9a1b374c32e43e2','a82833c54c3db65fde5a80f36bcd8203687a3465ab311342decd3962de21b133'),
    14729431007:(44960098050,'6998334fa022f137acf8644bf7786cf06d82ad83', '3c0cd00b9653960a59550e18f5c9c3bdce126c1ee6aa80a6d9f6dc5a42abeaf7','0b20619a3e1102cccbebf227862fe42e71765d515e08a9a8451f6b1c4abcef92'),
    14757075648:(45028060598,'c0dbaa5fb785616a82c6391c89a6fa0def661806','fe7f4d1f630e2203099e5dee6bd89b58483d6a1a200d9db410fa5546ca793258','a72a222688b46875594d854429c9fd02eb32b3cd39f0fd6a538b4f9c766ec718'),
}


def historical(directory,artifact,flop,turn,version):
    run,trainer_commit,archive_sha,case_sha=PINS[artifact]
    zip_path=directory/f'{artifact}.zip'
    assert sha(zip_path.read_bytes())==archive_sha
    api=json.loads((directory/f'{artifact}.json').read_bytes())
    assert (api['id'],api['digest'],api['workflow_run']['id'],api['workflow_run']['head_sha'])==(artifact,'sha256:'+archive_sha,run,trainer_commit)
    with zipfile.ZipFile(zip_path) as z:
        names=z.namelist()
        assert {z.read(p).decode().strip() for p in names if p.startswith('evidence/') and p.endswith('.txt')}=={SOLVER,RUST}
        manifest_name,=(p for p in names if p.startswith('evidence/') and p.endswith('.json'))
        m=json.loads(z.read(manifest_name))
        assert (m['schema'],m['spot'],m['version'],m['flop'],m['pot_family'])==('NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1','CO_BB',version,flop,'SRP')
        assert not m['failures'] and m['flop_action_sizes']==['33%','50%','75%','100%'] and m['pool_source_sha256']==POOL
        assert (m['root_pot_bb'],m['root_remaining_bb'])==(5.5,97.5)
        assert m['preflop_ranges']['spot']=='CO_BB' and m['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
        case,=(c for c in m['cases'] if (c['line'],c['turn'])==('x b50 c',turn))
        games=[]
        for path,digest in [(m['file_flop'],m['file_flop_sha256']),(case['source_path'],case_sha)]:
            full='solver/postflop/'+path
            raw=z.read(full)
            assert sha(raw)==digest
            game=json.loads(raw)
            job=json.loads(z.read(full.removesuffix('.json')+'.job.json'))
            assert (game['flop'],job['flop'],job['pot'],job['stack'],job['rake_rate'],job['rake_cap'])==(flop,flop,game['pot'],game['stack'],.05,1000)
            assert (job.get('hero'),bool(job.get('locks')))==((None,False) if version=='gto' else (0,True))
            assert [r['pat'] for r in job.get('locks',[])]==[r['pat'] for r in m['locks']]
            assert 0<=game['info']['gto_expl_pct']<=.5
            if version!='gto':assert 0<=game['info']['hero_gap_pct']<=.5
            games.append((game,job))
    (root,rj),(sub,sj)=games
    assert (root['pot'],root['stack'],rj['flop_oop'],rj['flop_ip'])==(550,9750,'33%,50%,75%,100%','33%,50%,75%,100%')
    assert (sub['pot'],sub['stack'],sub['turn'],sub['line0'],sj['line0'])==(1100,9475,turn,'x b50 c',['x','b50','c','/'])
    assert sj['turn_oop']==sj['turn_ip']=='50%,100%'
    assert (case['source_sha256'],case['gto_gap_pct'],case['hero_gap_pct'])==(case_sha,sub['info']['gto_expl_pct'],sub['info'].get('hero_gap_pct'))
    return dict(version=version,manifest=m,root=root,root_sha256=m['file_flop_sha256'],root_job=rj,
                subgame=sub,source_sha256=case_sha,subgame_job=sj,run=run,origin_id=artifact,
                origin_zip_sha256=archive_sha,trainer_commit=trainer_commit)


def store_source(source,flop):
    code=f"B487_{flop.upper()}_{source['version'].upper()}"
    path=EVIDENCE/f'NL2_{code}.json.gz'
    packed=gzip.compress(compact(source),mtime=0)
    path.write_bytes(packed[:9]+bytes([255])+packed[10:])
    source.update(archive_code=code,archive_sha256=sha(path.read_bytes()))


def target_nodes(s,line,seat=0):
    sub=s['subgame']
    if sub is None:return {}
    root=s['root']
    masks=game_reach(root,sub)[0]
    nodes={}
    for n in sub['nodes']:
        if (n['line'],n['player'])!=(line,seat):continue
        assert n['pot']==1100 and sub['stack']-max(n['bets'])==9475
        exact=proof(root,sub,n,masks)
        nodes[n['board']]=dict(legal_combos=exact['strict_legal_combos'],legal_deals=exact['compatible_hole_card_pairs'],b50=exact['b50'])
    return nodes


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--originals',type=Path)
    p.add_argument('--fresh',type=Path)
    p.add_argument('--run-id',type=int)
    p.add_argument('--list-artifacts',action='store_true')
    p.add_argument('--preflight',action='store_true')
    args=p.parse_args()
    if args.list_artifacts:
        print(' '.join(map(str,PINS)));return
    records=json.loads(FROZEN.read_bytes())['records']
    groups={}
    audit={}
    for rank,(mid,line) in MODELS.items():
        m=records[mid]
        assert (m['frequency_rank'],m['solver_profile'],m['assumed_model_node_spr'])==(rank,'CO_BB',8.364)
        assert all((b['actual_exact_action_line'],b['acting_seat'],b['actual_pot_bb'],b['actual_effective_stack_bb'])==(line,0,11,94.75) for b in m['certified_3_to_5_exact_flop_boards'])
        groups[rank]=dict(model_id=mid,rank=rank,spot='CO_BB',actor='BB_OOP',line=line,boards=[],pins=[])
        audit[rank]={}
    assert records[MODELS[113][0]]['source_model_id']==MODELS[14][0]
    for flop,turn,texture,gid,eid in CASES:
        g=historical(args.originals,gid,flop,turn,'gto')
        if eid:
            e=historical(args.originals,eid,flop,turn,'exp_oop')
        elif args.preflight or not (args.fresh/f'NL2-B487-{flop}-exp_oop'/'trainer/evidence'/f'{flop}-exp_oop.json').is_file():
            e=None
        else:
            e=original(args.fresh,flop,turn,'exp_oop',batch='B487',spot='CO_BB',flop_line='x b50 c',
                       flop_policy='checked-b50only',turn_policy='checkcheck',turn_extract='x x',root_pot=550,root_stack=9750)
            e['run']=args.run_id
            assert e['run']>0 and all(0<=e['root']['info'][k]<=.5 for k in ('hero_gap_pct','gto_expl_pct'))
            if e['subgame'] is not None:
                assert all(0<=e['subgame']['info'][k]<=.5 for k in ('hero_gap_pct','gto_expl_pct'))
        if e:
            for k in ('solver_pin','solver_ranges_sha256','preflop_ranges','pool_source_sha256'):
                assert g['manifest'][k]==e['manifest'][k]
        if not args.preflight:
            for source in [g]+([e] if e else []):
                store_source(source,flop)
        for rank,(mid,line) in MODELS.items():
            gs=target_nodes(g,line);es=target_nodes(e,line) if e else {}
            common=sorted(k for k in gs.keys()&es.keys() if gs[k]['legal_deals'] and es[k]['legal_deals'])
            old=next((b['public_board'] for b in records[mid]['certified_3_to_5_exact_flop_boards'] if b['flop']==flop),None)
            # Keep a previously published river if it is reverified; otherwise use the first shared positive public board.
            chosen=old if old in common else next(iter(common),None)
            audit[rank][flop]=dict(turn=turn,gto_run=g['run'],gto_sha256=g['source_sha256'],gto=gs,
                                   locked_run=e['run'] if e else None,locked_sha256=e['source_sha256'] if e else None,
                                   locked=es,selected=chosen)
            if chosen and not args.preflight:
                from hu_reverified_board_pair import emit_board
                board,pin=emit_board(records[mid],g,e,chosen,line,texture)
                assert board is not None and pin is not None
                groups[rank]['boards'].append(board);groups[rank]['pins'].append(pin)
            if args.preflight:print(rank,flop,{b:v['legal_combos'] for b,v in gs.items()},chosen)
    if args.preflight:return
    parent_set={b['flop'] for b in groups[14]['boards']}
    assert all(b['flop'] in parent_set for b in groups[113]['boards'])
    for rank,group in groups.items():
        flops={b['flop'] for b in group['boards']}
        assert len(flops)==len(group['boards'])==len(group['pins'])
        if len(flops)>=3:
            dest=EVIDENCE/'reverified';dest.mkdir(exist_ok=True)
            (dest/f'rank{rank}.json').write_bytes(json_bytes(group))
    Path('data/nl2_hu_b487_cobb_reach.json').write_bytes(json_bytes(dict(raw_boards=audit,models=groups)))
    print({rank:len(g['boards']) for rank,g in groups.items()})


if __name__=='__main__':
    main()
