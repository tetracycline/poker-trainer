"""Authenticate the two original GTO and downstream NL2 OOP archive pairs for rank146."""
import argparse
import hashlib
import json
from pathlib import Path

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import export_board, json_bytes, publish_bytes

OUT = Path('data/nl2_hu_b471_rank146_original_pairs.json')
ARCHIVES = (
    ('KsQh4d','Tc',44894369547,44895095589,14703138852,14703731534,
     '6e2a963e65f65bac7cd7eae1985dcb230fe7d37625eb318cfeadf06f1f6b24cb','e7b79cf1337a300b4ca7da2ef99ebe0c684885ac56667198fff95345eb528e3a'),
    ('QsJh4d','7s',44900567417,44900938891,14706190808,14705753667,
     '18e28d53d3511b0467aed8f0c43625758bfebd0997c4f3d47822c63ef187ed76','0b5ffb09f17535d3b961be1a00ad5965f31845a30d388f3b821b1d83f9cfcdab'),
)
ID = 'ln-opfr-r_model-19h8rla'
LINE = 'b50 c/x x/'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def checked(input_root, spec, verify):
    flop,turn,gto_run,exp_run,ga,ea,gzip_sha,ezip_sha=spec
    inputs=[input_root/f'r30-{i}' for i in (ga,ea)]
    manifests=[]
    for folder, expected in zip(inputs,(gzip_sha,ezip_sha)):
        assert digest(folder.with_suffix('.zip'))==expected
        evidence=folder/'evidence'
        assert (evidence/'poker-solver-pin.txt').read_text().strip()==SOLVER
        assert (evidence/'rust-engine-pin.txt').read_text().strip()==RUST
        manifest,=evidence.glob('*.json')
        manifests.append(manifest)
    gm,em=map(read,manifests)
    assert (gm['spot'],gm['version'],gm['flop'],gm['root_pot_bb'],gm['root_remaining_bb'])==('UTG_CO','gto',flop,6.5,97.5)
    assert gm['flop_size_profile']=='full' and gm['flop_action_sizes']==['33%','50%','75%','100%']
    assert gm['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR' and not gm['failures']
    assert (em['spot'],em['version'],em['flop'],em['turn'],em['flop_line'])==('UTG_CO','exp_oop',flop,turn,'b50 c')
    assert em['original_GTO_source_run_id']==gto_run and em['original_GTO_manifest_sha256']==digest(manifests[0])
    assert em['original_GTO_flop_unchanged'] and em['partially_locked_turn_river_only'] and not em['failures']
    pf=inputs[0]/'solver/postflop'
    root_file=pf/gm['file_flop']
    assert digest(root_file)==em['original_GTO_flop_root_sha256']==gm['file_flop_sha256']
    assert digest(root_file.with_suffix('.job.json'))==em['original_GTO_job_sha256']
    root=read(root_file)
    gc,=(c for c in gm['cases'] if (c['line'],c['turn'])==('b50 c',turn))
    ec,=em['cases']
    sources=[]
    for version,folder,rel,claim in [('gto',inputs[0],gc['source_path'],gc),('exp_oop',inputs[1],ec['original_Rust_exp_subgame_path'],ec)]:
        p=folder/'solver/postflop'/rel
        assert digest(p)==claim['source_sha256']
        game,job=read(p),read(p.with_suffix('.job.json'))
        assert (game['line0'],game['flop'],game['turn'])==('b50 c',flop,turn)
        assert game['info']['gto_expl_pct']<=.5 and (job['rake_rate'],job['rake_cap'])==(.05,1000)
        if version=='exp_oop':
            assert digest(p.with_suffix('.job.json'))==ec['original_exp_job_sha256']
            assert job['hero']==0 and job['locks'] and em['locks'] and game['info']['hero_gap_pct']<=.5
        else:
            assert job.get('hero') is None and not job.get('locks')
        sources.append(dict(version=version,root=root,subgame=game,source_sha256=digest(p),
                            manifest=dict(spot='UTG_CO',pot_family='SRP',locks=em['locks'] if version=='exp_oop' else [])))
    pin=dict(flop=flop,turn=turn,source_run_id=gto_run,NL2_run_id=exp_run,NL2_archive_sha256=ezip_sha,
             archive_code=f'GITHUB_ARTIFACT_{ga}')
    board=dict(public_board=next(n['board'] for n in sources[0]['subgame']['nodes'] if len(n['board'])==8),
               source_kind='PINNED_PREFLOP_CFR',assumed_preflop_ranges=False,flop_texture='HIGH')
    b,p=export_board(pin,board,sources,146,LINE,7.25,verify,archive_digest=gzip_sha)
    assert (b['actual_pot_bb'],b['actual_effective_stack_bb'])==(13,94.25)
    b['nl2_locked_variants'][0]['source_scope']='PARTIAL_TURN_RIVER_NL2_FROM_ORIGINAL_GTO_FLOP'
    return b,p


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--downloads',type=Path,required=True)
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    pairs=[checked(args.downloads,s,args.verify) for s in ARCHIVES]
    publish_bytes(OUT,json_bytes(dict(rank=146,model_id=ID,spot='UTG_CO',actor='UTG_OOP',line=LINE,
                  downstream_lock_scope='ORIGINAL_GTO_FLOP_WITH_SEPARATE_NL2_TURN_RIVER',boards=[b for b,p in pairs],
                  pins=[p for b,p in pairs],minimum_missing_distinct_flops=1)),args.verify)


if __name__=='__main__':
    main()
