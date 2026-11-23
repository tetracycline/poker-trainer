"""Recover ranks 12/102 exclusively from actual SB b50, BB call and consecutive checks."""
import argparse
import gzip
import json
import subprocess
import zipfile
from pathlib import Path

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import original
from hu_reverified_board_pair import emit_board, source_case

ARTIFACTS=Path('data/nl2_hu_b486_sb_bb_original_artifacts.json')
MODELS={12:('ln-ipc-t_model-btptzw','b50 c/x'),102:('ln-ipc-r_model-1at1re2','b50 c/x x/x')}
FLOPS={'As9h2d':('Kd','HIGH'),'Ks7h2d':('9d','HIGH'),'As7h3d':('Kd','HIGH'),'Kd8c3h':('5c','HIGH'),
       'Js9h4d':('Ts','MID'),'8s8h3d':('5s','PAIRED')}
POOL='c2d7c8a6b0dd044a5e546256207a6e46f626b083ecb598b1e6d98bb928611c4a'


def checked_chips(root,sub,root_job,job,version):
    assert (root['pot'],root['stack'],root_job['pot'],root_job['stack'])==(600,9700,600,9700)
    assert root_job.get('hero')==job.get('hero')==(1 if version=='exp_ip' else None)
    assert (root_job['rake_rate'],job['rake_rate'],job['rake_cap'],root_job['rake_cap'])==(.05,.05,1000,1000)
    decision,=(n for n in root['nodes'] if n['line']=='' and len(n['board'])==6 and n['player']==0)
    response,=(n for n in root['nodes'] if n['line']=='b50' and len(n['board'])==6 and n['player']==1)
    assert 'b50' in decision['acts'] and 'c' in response['acts'] and response['bets'][0]==300
    assert (sub['pot'],sub['stack'],job['pot'],job['stack'],job['line0'])==(1200,9400,1200,9400,['b50','c','/'])


def archived(folder, meta):
    path=folder/f'{meta["id"]}.zip'
    assert sha(path.read_bytes())==meta['sha256']
    with zipfile.ZipFile(path) as z:
        mf,=(n for n in z.namelist() if n.startswith('evidence/') and n.endswith('.json'))
        m=json.loads(z.read(mf))
        legacy=m['schema']=='HU_MISSING_ACTION_HISTORY_CFR_V1'
        keys=('poker-solver-commit','upstream-engine-commit') if legacy else ('poker-solver-pinned-SHA','rust-engine-pin-SHA')
        assert [z.read('evidence/'+k+'.txt').decode().strip() for k in keys]==[SOLVER,RUST]
        flop=m['selected_flops'][0] if legacy else m['flop']
        ver=m['version']
        assert m['spot']=='SB_BB' and ver in ('gto','exp_ip') and flop in meta['name']
        assert not m['failures']
        c,=(c for c in m['cases'] if c['line']=='b50 c' and c['turn']==FLOPS[flop][0])
        if legacy:
            assert m['source_preflop_tree_sha256']=='d4ca8e0c7d53deb6af337bfef8ff0c125205c1d3ef912267d8b40efc2fe7c100'
            rp,rs,sp,ss=c['flop_json'],c['flop_sha256'],c['sub_json'],c['sub_sha256']
            patterns=[dict(pat=r['pat'],n=r['n'],source=r['src']) for r in m['pool_lock_evidence'][flop]['source_patterns']]
        else:
            assert m['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR' and m['pool_source_sha256']==POOL
            rp,rs,sp,ss=m['file_flop'],m['file_flop_sha256'],c['source_path'],c['source_sha256']
            patterns=m['locks']
        def files(name,digest):
            raw=z.read('solver/postflop/'+name)
            assert sha(raw)==digest
            return json.loads(raw),json.loads(z.read('solver/postflop/'+name[:-5]+'.job.json'))
        root,rjob=files(rp,rs);sub,sjob=files(sp,ss)
    assert (sub['flop'],sub['turn'],sub['line0'])==(flop,c['turn'],'b50 c')
    checked_chips(root,sub,rjob,sjob,ver)
    assert [r['pat'] for r in patterns]==[r['pat'] for r in rjob.get('locks',[])]==[r['pat'] for r in sjob.get('locks',[])]
    assert (sub['info']['gto_expl_pct'],sub['info'].get('hero_gap_pct'))==(
        c['sub_gto_expl_pct'] if legacy else c['gto_gap_pct'],c['sub_hero_gap_pct'] if legacy else c['hero_gap_pct'])
    return dict(run=meta['run'],version=ver,source_sha256=ss,root_sha256=rs,root=root,subgame=sub,
                root_job=rjob,subgame_job=sjob,original_manifest=m,manifest=dict(spot='SB_BB',pot_family='SRP',locks=patterns),
                original_artifact=meta)


def persist(source):
    sub=source['subgame'];m=source['manifest'];flop=source['root']['flop']
    code=f'B486_{source["run"]}_{flop}_{source["version"]}'
    blob=gzip.compress(compact(dict(schema='NL2_B486_ORIGINAL_SB_BB_CFR_V1',solver=SOLVER,rust=RUST,source=source)),mtime=0)
    (EVIDENCE/f'NL2_{code}.json.gz').write_bytes(blob)
    return dict(source,archive_code=code,archive_sha256=sha(blob))


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument('--originals',required=True,type=Path)
    cli.add_argument('--new-solves',type=Path)
    cli.add_argument('--run',type=int)
    args=cli.parse_args()
    registry=json.loads(Path('data/nl2_hu_multiboard_status_v53_b465_rank218.json').read_bytes())
    routes=json.loads(subprocess.check_output(['node','tools/hu_b486_sb_trainer_routes.cjs']))
    groups={rank:dict(rank=rank,model_id=mid,line=line,actor='BB_IP',spot='SB_BB',trainer_scope=routes[mid],boards=[],pins=[])
            for rank,(mid,line) in MODELS.items()}
    packages={}
    for meta in json.loads(ARTIFACTS.read_bytes()):
        s=archived(args.originals,meta)
        packages.setdefault(s['subgame']['flop'],{})[s['version']]=s
    unavailable={}
    if args.new_solves:
        assert args.run and args.run>0
        for flop,version in (('As7h3d','exp_ip'),('Kd8c3h','gto'),('Kd8c3h','exp_ip')):
            mf=args.new_solves/f'NL2-B486-{flop}-{version}/trainer/evidence/{flop}-{version}.json'
            if not mf.exists() or json.loads(mf.read_bytes())['failures']:
                unavailable[flop,version]='MISSING_OR_FAILED_ORIGINAL';continue
            s=original(args.new_solves,flop,FLOPS[flop][0],version,batch='B486',spot='SB_BB',flop_line='b50 c',
                       flop_policy='oop-b50only',turn_policy='checkcheck',turn_extract='x x',root_pot=600,root_stack=9700)
            if s['subgame'] is not None:
                checked_chips(s['root'],s['subgame'],s['root_job'],s['subgame_job'],version)
                assert all('50%' in s['subgame_job'][k].split(',') for k in ('turn_ip','river_ip'))
            packages.setdefault(flop,{})[version]=dict(s,run=args.run)
    evidence={}
    for flop,pair in packages.items():
        versions={v:persist(s) for v,s in pair.items()}
        for rank,(mid,line) in MODELS.items():
            model=registry['records'][mid]
            assert (model['frequency_rank'],model['solver_profile'],model['assumed_model_node_spr'])==(rank,'SB_BB',7.583)
            expected_length=8 if rank==12 else 10
            publics=sorted({n['board'] for s in pair.values() if s['subgame'] is not None for n in s['subgame']['nodes']
                            if n['line']==line and n['player']==1 and len(n['board'])==expected_length})
            trials={}
            for board in publics:
                trials[board]={}
                for v,s in versions.items():
                    if s['subgame'] is None:
                        trials[board][v]=dict(status='NO_LEGAL_TURN_SUBGAME');continue
                    if any(not (0<=game['info']['gto_expl_pct']<=.5) or
                           (v!='gto' and not (0<=game['info']['hero_gap_pct']<=.5)) for game in (s['root'],s['subgame'])):
                        trials[board][v]=dict(status='GAP_ABOVE_THRESHOLD');continue
                    info=source_case(model,s,board,line,1)
                    trials[board][v]=dict(status='VERIFIED' if info else 'NO_COMPATIBLE_DEAL_FOR_THIS_LINE',
                                         strict_hero_combos=len(info[1]) if info else 0,compatible_deals=info[2] if info else 0)
            for board in publics:
                if all(trials[board].get(v,{}).get('compatible_deals',0)>0 for v in ('gto','exp_ip')):
                    b,p=emit_board(model,versions['gto'],versions['exp_ip'],board,line,FLOPS[flop][1])
                    assert (b['actual_pot_bb'],b['actual_effective_stack_bb'])==(12,94)
                    groups[rank]['boards'].append(b);groups[rank]['pins'].append(p)
                    break
            evidence.setdefault(rank,{})[flop]=dict(sources={v:{k:s[k] for k in ('archive_code','archive_sha256','run','source_sha256')} for v,s in versions.items()},publics=trials)
    for rank,group in groups.items():
        boards=group['boards']
        if 3<=len(boards)<=5 and len({b['flop'] for b in boards})==len(boards):
            dest=EVIDENCE/'reverified';dest.mkdir(exist_ok=True)
            (dest/f'rank{rank}.json').write_bytes(json_bytes(group))
    Path('data/nl2_hu_b486_sb_checked_originals.json').write_bytes(json_bytes(dict(models=groups,attempts=evidence,unavailable=[dict(flop=f,version=v,reason=r) for (f,v),r in unavailable.items()])))
    print({rank:len(g['boards']) for rank,g in groups.items()})


if __name__=='__main__':main()
