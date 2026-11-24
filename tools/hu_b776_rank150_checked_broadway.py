"""Solve the missing exp_ip policy for B765's existing TdTc3d/2c GTO turn and twelve rivers."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import hu_b724_rank150_rivers as native
import hu_b765_rank150_low_flanks as deals
import hu_b768_collect as receipts
from hu_b467_river_source_gate import compact,json_bytes,sha

FLOP,TURN='TdTc3d','2c'
HERO='JdKd'
WORKER='tools/hu_b776_rank150_checked_broadway.py'
ORIGINAL='B765_R150_TDTC3D'
CHECKPOINT='B765_ROOT_R150_TDTC3D'
SOURCE_ID=14896358683
SOURCE_SHA='0b271e142cae8c318ab8231b256421c530f4cccbaf54ca47bb18f2fdff575142'
CHECK_ID=14897400744
CHECK_SHA='fc4ce4bc078629ed912175c628ad09284fe42c4250790d4485af9a19f54d9fc1'
JOB_SHA='dca3ea5d7912ceb2a9ebf81bd1c95d03f21f9dfd2170c0631b7cd15609d79079'
RESULT_SHA='54dbdbad8975f4020e3aaa8c7961c26f16ffbff16fe2f817ecff121962f41c1f'
PAIRS={'2h':13,'2s':13,'3h':13,'3s':13,'4h':9,'5s':10,'6s':11,'8h':13,'9s':11,'Jh':0,'Qh':11,'Ks':0}


def original():
    evidence=Path('data/solver_evidence')
    receipt=Path('data/nl2_hu_b768_source_receipts.json')
    assert native.limp.git_blob(receipt)=='61f96b80c99c2fe5c23ee3a1b9e6882fbd73f559'
    auth=receipts.validate(json.loads(receipt.read_bytes()))
    for name,code,identity,digest in [('B765-R150-',ORIGINAL,SOURCE_ID,SOURCE_SHA),('B765-root-R150-',CHECKPOINT,CHECK_ID,CHECK_SHA)]:
        match,=[a for a in auth['artifacts'] if a['name']==name+FLOP]
        assert (match['id'],match['digest'])==(identity,'sha256:'+digest)
        path=evidence/('NL2_'+code+'.zip')
        assert len(path.read_bytes())==match['size_in_bytes'] and sha(path.read_bytes())==digest
    with ZipFile(evidence/('NL2_'+ORIGINAL+'.zip')) as z, ZipFile(evidence/('NL2_'+CHECKPOINT+'.zip')) as cp:
        claim=json.loads(z.read('proof.json'));pin=json.loads(cp.read('checkpoint.json'))
        assert (claim['flop'],claim['selected'],claim['source_worker_blob'])==(FLOP,None,receipts.WORKER_BLOB)
        files={name:z.read(name) for name in ('rendered-routes.json','original-manifest.json','flop/job.json','flop/result.json',TURN+'-gto/job.json',TURN+'-gto/result.json')}
        assert all(sha(raw)==claim['native_file_sha256'][name] for name,raw in files.items())
        assert all(files[name]==cp.read(name) for name in ('flop/job.json','flop/result.json'))
        assert sha(files['flop/result.json'])==pin['original_root_sha256'] and sha(files['flop/job.json'])==pin['original_root_job_sha256']
        assert tuple(sha(files[TURN+'-gto/'+n+'.json']) for n in ('job','result'))==(JOB_SHA,RESULT_SHA)
        record,=[t for t in claim['turns'] if t['turn']==TURN]
        assert set(record['policies'])=={'gto'} and not any(TURN+'-exp_ip/' in n for n in z.namelist())
        assert record['policies']['gto']['source_sha256']==RESULT_SHA and record['preregistered_rivers']==list(PAIRS)
        assert all(not b['hands'] for b in record['policies']['gto']['boards'].values())
    origin=dict(source_run=receipts.RUN,source_head=receipts.HEAD,source_job=receipts.JOBS[FLOP],source_artifact=SOURCE_ID,
                source_sha256=SOURCE_SHA,root_checkpoint_artifact=CHECK_ID,root_checkpoint_sha256=CHECK_SHA,
                gto_turn_job_sha256=JOB_SHA,gto_turn_sha256=RESULT_SHA,root_job_sha256=pin['original_root_job_sha256'],
                root_sha256=pin['original_root_sha256'])
    return files,record,origin


def displayed(root,game,rivers,eligible,route,first=None):
    boards=native.observations(root,game,TURN,rivers,eligible,route)
    pairs={}
    for public,data in boards.items():
        co,bb=deals.hand_pairs(root,game,TURN,public)
        witness={(''.join(h),''.join(v)) for h in co if ''.join(h) in data['hands'] for v in bb if set(h).isdisjoint(v)}
        if first is not None:
            witness &= first[public]
        hands={h for h,_ in witness}
        data['hands']={h:data['hands'][h] for h in sorted(hands)}
        data['compatible_bb_per_co']={h:sorted(v for c,v in witness if c==h) for h in sorted(hands)}
        pairs[public]=witness
    return boards,pairs


def run(args):
    solver=args.solver.resolve();assert sys.version_info[:2]==(3,11)
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==native.limp.SOLVER
    for path,pin in {**deals.base.PINS,deals.WORKER:receipts.WORKER_BLOB}.items():
        assert native.limp.git_blob(path)==pin,path
    if args.driver:
        assert args.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==native.limp.RUST
    py=solver/'postflop/py';sys.path.insert(0,str(py));import pipeline
    pool_bytes=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(pool_bytes)==native.POOL and sha((py/'pipeline.py').read_bytes())==native.PIPELINE and sha((py/'ranges.py').read_bytes())==native.RANGES
    pool=json.loads(pool_bytes)['NL2'];files,record,origin=original()
    raw_route=subprocess.check_output(['node',native.ROUTE]);assert raw_route==files['rendered-routes.json']
    route=json.loads(raw_route);assert (route['model_id'],route['line'],route['actor'],route['native_price'])==(native.MODEL,native.LINE,1,[416,9817])
    manifest=json.loads(files['original-manifest.json']);rootjob=json.loads(files['flop/job.json']);root=json.loads(files['flop/result.json'])
    native.limp.check_limp_source(dict(manifest=manifest,root_job=rootjob,subgame_job=None))
    parent,eligible,_,gate=native.parent_gate(root,TURN,route);rivers=record['preregistered_rivers']
    gj=json.loads(files[TURN+'-gto/job.json']);game=json.loads(files[TURN+'-gto/result.json'])
    assert 0<=game['info']['gto_expl_pct']<=.5 and not game['info'].get('lock_stats')
    assert (gj['flop'],gj['turn'],gj['line0'],gj['root_no_bet'],gj['pot'],gj['stack'])==(FLOP,TURN,['x','b33','c','/'],False,416,9817)
    assert gj['extract']==[dict(prefix=[],street=True)]+[dict(prefix=['x','x',r],street=True) for r in rivers]
    for i,k in enumerate(('oop_w','ip_w')):
        assert gj[k]==[[h,w] for h,w in zip(root['hands'][i],parent['wr'][i],strict=True) if w>1e-4]
    gto,gto_deals=displayed(root,game,rivers,eligible,route)
    assert {p[-2:]:len(v) for p,v in gto_deals.items()}==PAIRS
    assert {h for vs in gto_deals.values() for h,v in vs}=={HERO}
    assert all(gto[p]['reach']==b['reach'] for p,b in record['policies']['gto']['boards'].items())
    target,rules=native.prepare_job(dict(source=dict(root=root,version='gto',manifest=manifest),job=gj),'exp_ip',pool,pipeline)
    target['out']='result.json';assert target['hero']==1 and target['locks']
    if args.preflight:
        print(json.dumps(dict(named_gto_rivers=len(gto),gto_rivers_with_compatible_co_bb=sum(bool(v) for v in gto_deals.values()),
                              co=HERO,gto_job=JOB_SHA,new_nl2_job=sha(compact(target)))))
        return
    out=args.output
    if args.driver:assert not out.exists() or not any(out.iterdir())
    out.mkdir(parents=True,exist_ok=True)
    for path,raw in files.items():
        dest=out/path;dest.parent.mkdir(parents=True,exist_ok=True)
        if not args.driver:assert dest.read_bytes()==raw
        else:dest.write_bytes(raw)
    folder=out/(TURN+'-exp_ip')
    locked=native.solve(folder,target,args.driver)
    assert (folder/'job.json').read_bytes()==compact(target)
    assert locked['hands']==game['hands'] and (locked['pot'],locked['stack'])==(416,9817)
    assert 0<=locked['info']['gto_expl_pct']<=.5 and 0<=locked['info']['hero_gap_pct']<=.5
    application=native.audit_patterns(locked,target,dict(manifest,locks=rules),pool,1)
    assert any(v>0 for k,v in application['driver_tree_nodes'].items() if k in application['marginal_targets'])
    nl2,both=displayed(root,locked,rivers,eligible,route,gto_deals)
    common={p:sorted({h for h,v in vs}) for p,vs in sorted(both.items()) if vs}
    joint=[b['reach'] for b in nl2.values() if b['reach']['compatible_hole_card_pairs']>0 and b['reach']['strict_legal_combos']>0 and b['reach']['b50'] is not None]
    proof=dict(schema='NL2_B776_EXACT_GTO_TURN_MISSING_EXP_IP_V1',rank=150,model_id=native.MODEL,flop=FLOP,turn=TURN,actor=1,line=native.LINE,
               source_worker_blob=native.limp.git_blob(WORKER),source=origin,solver=native.limp.SOLVER,rust=native.limp.RUST,pool_sha256=native.POOL,
               root_gate=gate,preregistered_rivers=rivers,original_flop_cfr_repeated=0,original_gto_turn_cfr_repeated=0,new_locked_turn_subgames=1,
               gto=dict(source_sha256=RESULT_SHA,job_sha256=JOB_SHA,boards=gto),
               exp_ip=dict(source_sha256=sha((folder/'result.json').read_bytes()),job_sha256=sha(compact(target)),measured_lock_application=application,boards=nl2),
               common=common,selected=dict(turn=TURN,public_board=next(iter(common))) if common else None,
               assumed_preflop_ranges=True,lock_scope='FROZEN_GTO_FLOP_WITH_MEASURED_PARTIAL_TURN_RIVER_NL2_MARGINALS',
               no_observed_per_private_hand_frequency=True,locked_named_boards=len(nl2),joint_halfpot_assessed=len(joint),
               nonpolarized_candidates=sum(r['b50']['candidate'] for r in joint))
    proof['native_file_sha256']={p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='proof.json'}
    (out/'proof.json').write_bytes(json_bytes(proof))
    print(json.dumps({k:proof[k] for k in ('selected','locked_named_boards','joint_halfpot_assessed','nonpolarized_candidates')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('solver','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--preflight',action='store_true');p.add_argument('--driver',type=Path)
    run(p.parse_args())
