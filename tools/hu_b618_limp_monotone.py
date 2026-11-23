"""Solve rank29 on new monotone flops using its authored half-pot / three-quarter-pot route."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b481_rank27_limp_rivers import check_limp_source
from hu_b483_locked_medium import POOL
from hu_b582_rank29_reach import candidates, cards, verified_masks
from hu_checked_gto_boundary import prepare_job

FLOPS = ('Ks7s3s','Qh8h4h','Jc7c3c','Kd9d4d','Qs6s2s')
ORIGINAL = 'NL2_B580_R27_LMP.zip'
ORIGINAL_SHA = 'd4b98b4351012d78aa62f3cd31b75228d4f7a35725584d86f633552fbf28369a'


def execute(driver, folder, job, threads):
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'job.json').write_bytes(compact(job))
    subprocess.run([str(driver),'job.json'],cwd=folder,check=True,
                   env=dict(os.environ,RAYON_NUM_THREADS=str(threads)))
    return json.loads((folder/job['out']).read_bytes())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--flop',required=True,choices=FLOPS)
    parser.add_argument('--solver',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    solver=args.solver.resolve()
    for repo,commit in [(solver,SOLVER),(solver/'postflop/postflop-solver',RUST)]:
        assert subprocess.check_output(['git','-C',repo,'rev-parse','HEAD'],text=True).strip()==commit
    driver=solver/'postflop/pfdriver/target/release/pfdriver'
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    poolraw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(poolraw)==POOL
    pool=json.loads(poolraw)['NL2']
    original=EVIDENCE/ORIGINAL
    assert sha(original.read_bytes())==ORIGINAL_SHA
    with ZipFile(original) as z:
        root_job,child_job,manifest=[json.loads(z.read(n)) for n in ('original-flop.job.json','original-turn.job.json','original-manifest.json')]
    flop=args.flop
    turns=['2h','3d','4c','5h','8c','Tc','Qd','Ah']
    turns=[t for t in turns if t not in cards(flop)]
    root_job=dict(root_job,flop=flop,out='root.json',extract=[dict(prefix=[],street=True)]+
                  [dict(prefix=['b50','c',t],street=False,raw=True) for t in turns])
    check_limp_source(dict(manifest=manifest,root_job=root_job,subgame_job=None))
    root=execute(driver,args.out/'root',root_job,2)
    assert (root['flop'],root['pot'],root['stack'])==(flop,250,9900)
    assert 0<=root['info']['gto_expl_pct']<=.5 and not root['info'].get('lock_stats')
    route=json.loads(subprocess.check_output(['node','tools/hu_b582_rank29_route.cjs']))
    eligible,targets=candidates(root,route)
    report=dict(flop=flop,solver=SOLVER,rust=RUST,root_sha256=sha((args.out/'root/root.json').read_bytes()),
                root_eligible=eligible, eligible_turns=[t for _,t,_,_ in targets],turns=[],positive=[])
    for _,turn,n,choices in targets[:3]:
        rivers=[r for _,r,_ in choices]
        gto=dict(child_job,flop=flop,turn=turn,out='gto.json',turn_oop='75%',turn_ip='50%,100%',
                 river_oop='50%,75%,100%,a',river_ip='50%,75%,100%,a',target_pct=.45,iters=2000,
                 extract=[dict(prefix=[],street=True)]+[dict(prefix=['b75','c',r],street=True) for r in rivers])
        for seat,key in enumerate(('oop_w','ip_w')):
            gto[key]=[[h,w] for h,w in zip(root['hands'][seat],n['wr'][seat],strict=True) if w>1e-4]
        locked,meta=prepare_job(dict(source=dict(version='gto',root=root,manifest=manifest),job=gto),'exp_oop',pool,pipeline)
        policies=[]
        result=dict(turn=turn,rivers=rivers,gto_hands={},locked_hands={})
        for version,job in [('gto',gto),('exp_oop',locked)]:
            sub=execute(driver,args.out/turn/version,job,1)
            assert (sub['flop'],sub['pot'],sub['stack'])==(flop,500,9775)
            assert 0<=sub['info']['gto_expl_pct']<=.5
            if version=='exp_oop':
                assert 0<=sub['info']['hero_gap_pct']<=.5
                audit_patterns(sub,job,dict(manifest,locks=meta),pool,hero_seat=0)
            else:
                assert not sub['info'].get('lock_stats')
            sub.update(line0='b50 c',turn=turn)
            seen={r:sorted(allowed.intersection(verified_masks(root,sub,0,n['board']+r))) for _,r,allowed in choices}
            result['gto_hands' if version=='gto' else 'locked_hands']=seen
            policies.append(seen)
            if not any(seen.values()):
                break
        report['turns'].append(result)
        if len(policies)==2:
            for r in rivers:
                common=sorted(set(policies[0][r]).intersection(policies[1][r]))
                if common:report['positive'].append(dict(public_board=n['board']+r,shared_hands=common))
        if report['positive']:
            break
    (args.out/'result.json').write_bytes(json_bytes(report))
    print(f"{flop}: {len(report['positive'])} positive named rivers")


if __name__=='__main__':
    main()
