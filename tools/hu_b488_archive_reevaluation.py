"""Rebuild the named river decisions of four models from their original GTO and opponent-lock jobs."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import zipfile

from hu_b483_locked_medium import ARCHIVES, PIN, POOL, RUNS, digest, encode
from hu_b485_locked_medium import ORIGINS, legacy_rules, read_game, replay
from hu_b467_river_source_gate import EVIDENCE, json_bytes
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from solve_hu_missing_branches import EXTRA_SPOTS

FROZEN=Path('data/nl2_hu_multiboard_status_v53_b465_rank218.json')
MODELS={
    85:('ln-bb-r_model-1e6bpc','x b50 c/x x/',0),
    112:('ln-ipfr-r_model-9eqgjz','x x/x x/x',1),
    177:('ln-3bp-3b_r_model-1mh38ma','b75 c/x x/',0),
    256:('ln-3bp-3c_r_model-cfardb','b33 c/x x/x',1),
}
# Freeze the public runouts before replay. Preserve previously verified named rivers where available.
SELECTION=(
    (85,'8s8h3d','3d8h8s5s4s',14592317474,14592238442),
    (85,'KsQh4d','4dQhKsTc3h',14591903053,14593036851),
    (85,'Js9h4d','4d9hJsTsAh',14591863023,14592556513),
    (112,'KsQh4d','4dQhKsTc3h',14600212926,14601061377),
    (112,'As9h2d','2d9hAsKd6s',14599607198,14599634225),
    (112,'Jh9d6s','6s9dJh3cJd',14628385508,14626854645),
    (177,'Ks7h2d','2d7hKs9d5s',14593390837,14592524168),
    (177,'KsQh4d','4dQhKsTc3h',14592263783,14593625078),
    (177,'Js9h4d','4d9hJsTs9c',14592627989,14592977981),
    (256,'Ks7h2d','2d7hKs9d5s',14593390837,14592064422),
    (256,'KsQh4d','4dQhKsTc3h',14592263783,14593171704),
    (256,'Ks7s2s','2s7sKs9d4d',14530206356,14530400782),
)


def origins():
    catalog={}
    for run,obj in ORIGINS.items():
        for a in obj['artifacts']:
            catalog[a['id']]=(int(run),obj['trainer_commit'],a)
    for name,(artifact,sha) in ARCHIVES.items():
        run,head=next((r,h) for r,(n,h) in RUNS.items() if f'-B{n}-' in name)
        catalog[artifact]=(run,head,dict(id=artifact,name=name,sha256=sha))
    return {i:catalog[i] for row in SELECTION for i in row[-2:]}


def original(directory,catalog,artifact,version,model,b,solver,pipeline,ranges,pool):
    run,head,origin=catalog[artifact]
    info=json.loads((directory/f'{run}.json').read_bytes())
    api,=(a for a in (info['artifacts'] if isinstance(info,dict) else info) if a['id']==artifact)
    wf=api['workflow_run']
    assert (api['name'],api['digest'],wf['id'],wf['head_sha'],wf['repository_id'],wf['head_branch'])==(
        origin['name'],'sha256:'+origin['sha256'],run,head,1438346845,'fix/nl2-hu-lines-audit-20261118')
    file=directory/f'{artifact}.zip'
    assert digest(file.read_bytes())==origin['sha256']
    with zipfile.ZipFile(file) as z:
        mf,=(k for k in z.namelist() if k.startswith('evidence/') and k.endswith('.json'))
        m=json.loads(z.read(mf))
        assert (m['spot'],m['version'])==(model['solver_profile'],version)
        case,=(c for c in m['cases'] if (m.get('flop',c.get('flop')),c['turn'],c['line'])==
               (b['flop'],b['turn'],b['exact_flop_action']))
        sh=case.get('sub_sha256') or case['source_sha256']
        rootsha=m.get('file_flop_sha256') or case['flop_sha256']
        rp=m.get('file_flop') or case['flop_json']
        sp=case.get('source_path') or case['sub_json']
        root,rj=read_game(z,rp,rootsha)
        sub,sj=read_game(z,sp,sh)
        for game in (root,sub):
            assert 0<=game['info']['gto_expl_pct']<=.5
            if version!='gto':assert 0<=game['info']['hero_gap_pct']<=.5
        n,=(n for n in sub['nodes'] if (n['board'],n['line'],n['player'])==(b['public_board'],b['actual_exact_action_line'],b['acting_seat']))
        assert (n['pot']/100,(sub['stack']-max(n['bets']))/100)==(b['actual_pot_bb'],b['actual_effective_stack_bb'])
        # B485 independently verifies Git/Rust pins, genuine preflop range strings, full root-to-turn
        # hand weights, each real lock and sample, both jobs' rake and original compatible masks.
        direct=replay(z,origin,run,{sh:{sh:(model,dict(b,exact_node_actions=n['acts']),version)}},solver,pipeline,ranges,pool)[sh]
        assert direct['strict_legal_combos']>0 and direct['compatible_hole_card_pairs']>0
        if 'locks' in m:
            metadata=m['locks']
        else:
            _,meta=legacy_rules(pipeline,m['spot'],version,b['flop'],m.get('flop_bet_sizes'))
            metadata=[dict(r,source=r['src']) for r in meta]
        def job_sha(rel):
            return digest(z.read('solver/postflop/'+rel.replace('.json','.job.json')))
        evidence=dict(original_artifact_id=artifact,original_zip_sha256=origin['sha256'],original_run=run,trainer_commit=head,
                      original_manifest_sha256=digest(z.read(mf)),original_root_sha256=rootsha,original_source_sha256=sh,
                      original_flop_job_sha256=job_sha(rp),original_turn_job_sha256=job_sha(sp),
                      root_GTO_stage_gap_pct=root['info']['gto_expl_pct'],root_locked_hero_gap_pct=root['info'].get('hero_gap_pct'))
    return dict(run=run,version=version,source_sha256=sh,root=root,subgame=sub,
                manifest=dict(spot=m['spot'],pot_family=model['family'],locks=metadata),
                archive_code=f'GHA_{artifact}',archive_sha256=origin['sha256'],provenance=evidence),direct


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--downloads',type=Path)
    parser.add_argument('--solver',type=Path)
    parser.add_argument('--list-artifacts',action='store_true')
    parser.add_argument('--list-runs',action='store_true')
    args=parser.parse_args()
    catalog=origins()
    if args.list_artifacts or args.list_runs:
        print(' '.join(map(str,sorted(catalog if args.list_artifacts else {r for r,_,_ in catalog.values()}))))
        return
    solver=args.solver.resolve()
    assert subprocess.check_output(['git','-C',str(solver),'rev-parse','HEAD'],text=True).strip()==PIN
    poolfile=(solver/'inputs/pool_stats.json').read_bytes()
    assert digest(poolfile)==POOL
    pool=json.loads(poolfile)['NL2']
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    import ranges
    ranges.SPOTS.update(EXTRA_SPOTS)
    records=json.loads(FROZEN.read_bytes())['records']
    groups={rank:dict(rank=rank,model_id=mid,boards=[],pins=[]) for rank,(mid,_,_) in MODELS.items()}
    for rank,flop,public,gid,eid in SELECTION:
        mid,line,seat=MODELS[rank]
        model=records[mid]
        assert model['frequency_rank']==rank
        pots={(b['actual_pot_bb'],b['actual_effective_stack_bb']) for b in model['certified_3_to_5_exact_flop_boards']
              if (b['actual_exact_action_line'],b['acting_seat'])==(line,seat)}
        (pot,stack),=pots
        b=dict(flop=flop,turn=public[6:8],public_board=public,actual_exact_action_line=line,exact_flop_action=line.split('/')[0],
               acting_seat=seat,actual_pot_bb=pot,actual_effective_stack_bb=stack)
        g,gr=original(args.downloads,catalog,gid,'gto',model,b,solver,pipeline,ranges,pool)
        e,er=original(args.downloads,catalog,eid,'exp_ip' if seat else 'exp_oop',model,b,solver,pipeline,ranges,pool)
        assert g['run']==e['run']
        board,pin=emit_board(model,g,e,public,line,texture(flop))
        assert board and pin
        for k,w,source in [('GTO',gr,g),('NL2',er,e)]:
            assert pin[f'{k}_strict_combos']==w['strict_legal_combos']
            assert pin[f'{k}_compatible_hole_card_pairs']==w['compatible_hole_card_pairs']
            pin[k+'_archive_provenance']=source['provenance']
        # Both source versions share this run. Canonicalize gzip's OS byte across Python/zlib builds.
        view=EVIDENCE/f"NL2_MULTIBOARD_{pin['viewer_archive_code']}.json.gz"
        blob=view.read_bytes()
        blob=blob[:9]+bytes([255])+blob[10:]
        view.write_bytes(blob);pin['viewer_sha256']=digest(blob)
        groups[rank]['boards'].append(board);groups[rank]['pins'].append(pin)
    output=EVIDENCE/'reverified'
    output.mkdir(exist_ok=True)
    for rank,group in groups.items():
        assert len(group['boards'])==len({b['flop'] for b in group['boards']})==3
        (output/f'rank{rank}.json').write_bytes(json_bytes(group))
        print(rank,[(b['public_board'],p['GTO_strict_combos'],p['NL2_strict_combos']) for b,p in zip(group['boards'],group['pins'])])


if __name__=='__main__':
    main()
