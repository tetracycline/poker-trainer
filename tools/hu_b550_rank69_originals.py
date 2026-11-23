"""Export previously unrequested BB third-pot calls and verify named rank69 rivers from native policy pairs."""
import argparse
import base64
import gzip
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER,RUST
from hu_b467_river_source_gate import EVIDENCE,compact,json_bytes,sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL
from hu_b514_turn_stab import rates
from hu_b536_sb_barrels import tx
from hu_b542_rank8_original_turn import HEAD,RUN,hcls
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision,lock_metadata
from hu_reverified_board_pair import emit_board
from hu_multiboard_promote import texture
from hu_sequential_cfr_reach import accepted,cardkey
from solve_hu_multiboard_100bb import make_fallbacks
from run10_common import classes

DATA=Path('data')
MID='ln-ipfr-r_model-159a6z6'
LINE='b33 c/x x/x'
NEW='8c6d5s'
PINS={'5h4h3s':(14792264343,'63bbcdaa03624c3c37e3e3de35bdcb6ae1c50b12116d1423c5de5d2c34f36d58'),
      '6s5h4d':(14792976867,'df887d5566b9f99505a5310b3e236205c6bfbd55b19013266fbf3e91071a442b')}
TURNS={'5h4h3s':('2d','7s','Jd'),'6s5h4d':('2s','8c','Js'),NEW:('2h','7h','Jh')}
# Three cards per root. The extractions are the only original-game change on the two full-menu flops.
RIVERS=('2c','3d','4s','5d','6h','7c','8h','9s','Td','Jh')


def source_job(args,flop):
    template=flop if flop in PINS else '6s5h4d'
    aid,digest=PINS[template]
    folder=args.originals
    meta=json.loads((folder/f'{aid}.json').read_bytes())
    assert (meta['id'],meta['name'],meta['digest'])==(aid,f'B524-R8-{template}-gto','sha256:'+digest)
    assert (meta['workflow_run']['id'],meta['workflow_run']['head_sha'],meta['workflow_run']['repository_id'])==(RUN,HEAD,1438346845)
    archived=folder/f'{aid}.zip'
    assert sha(archived.read_bytes())==digest
    with ZipFile(archived) as z:
        m=json.loads(z.read(f'trainer/evidence/{template}-gto.json'))
        path='solver/postflop/'+m['file_flop']
        raw=z.read(path);original=json.loads(raw);job=json.loads(z.read(path[:-5]+'.job.json'))
    assert (m['spot'],m['version'],m['flop'],m['failures'],sha(raw))==('BTN_BB','gto',template,[],m['file_flop_sha256'])
    assert not job.get('locks') and job.get('hero') is None and job['compress']
    assert job['flop_oop']==job['flop_ip']=='33%,50%,75%,100%' and (job['pot'],job['stack'])==(550,9750)
    if flop==NEW:
        original=None
        job.update(flop=flop,flop_oop='33%',flop_ip='33%',extract=[dict(prefix=[],street=True)])
    job['out']='result.json'
    job['extract']+=[dict(prefix=['b33','c',turn],street=False,raw=True) for turn in TURNS[flop]]
    return job,original


def execute(driver,folder,job):
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'job.json').write_bytes(compact(job))
    subprocess.run([str(driver.resolve()),'job.json'],cwd=folder,timeout=1050,check=True)
    return (folder/'result.json').read_bytes()


def turn_job(root,flop,turn,version,pool,pipeline):
    parent,=(n for n in root['nodes'] if n['line']=='b33 c/' and n['board'].endswith(turn))
    assert parent['bets']==[182,182] and parent['pot']==914
    public=parent['board']
    rivers=[r for r in RIVERS if r not in (public[i:i+2] for i in (0,2,4,6)) and tx(public+r) in ('low','mid_high')]
    rows,meta=make_fallbacks('BTN_BB',version,pool,pipeline.lock_list,flop,by_street=True)
    job=pipeline.make_job('BTN_BB',version,flop,'result.json',compress=False,target=.45,rank=.45,iters=2000,locks=rows)
    job.update(pipeline.SUB)
    job.update(oop='',ip='',turn=turn,pot=914,stack=9568,line0=['b33','c','/'],root_no_bet=False,
               extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',r],street=True) for r in rivers])
    for seat,key in enumerate(('oop_w','ip_w')):
        job[key]=[[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
    return job,lock_metadata(meta),rivers,public


def published_actions(source,row,route):
    public=row['public_board']
    if 'x' not in row['source_actions'] or not row['compatible_hole_card_pairs']:
        return {}
    idx=row['source_actions'].index('x')
    masks=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
    result={}
    for h,bits in zip(source['subgame']['hands'][1],masks,strict=True):
        if bits & (1<<idx):
            hand=''.join(cardkey(h))
            cells=[(tx(public[:n]),hcls(hand,public[:n]) if n<10 else classes(hand,public)[0]) for n in (6,8,10)]
            if all(c in route[t][key] for (t,c),key in zip(cells,('flop','turn','river'),strict=True)):
                result[hand]=dict(hand=hand,flop=cells[0],turn=cells[1],river=cells[2])
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('originals','solver','results'):ap.add_argument('--'+n,type=Path,required=True)
    ap.add_argument('--driver',type=Path)
    ap.add_argument('--flop',choices=TURNS)
    ap.add_argument('--run',type=int,required=True)
    args=ap.parse_args()
    solver=args.solver.resolve()
    assert args.run>0 and subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    if args.driver:
        assert args.flop and args.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    import ranges
    poolbytes=(solver/'inputs/pool_stats.json').read_bytes();assert sha(poolbytes)==POOL
    pool=json.loads(poolbytes)['NL2']
    route=json.loads(subprocess.check_output(['node','tools/hu_b550_rank69_routes.cjs']))
    model=json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records'][MID]
    assert (model['frequency_rank'],model['solver_profile'],model['assumed_model_node_spr'])==(69,'BTN_BB',10.436)
    group=dict(rank=69,model_id=MID,boards=[],pins=[])
    report=dict(schema='NL2_HU_B550_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    records=[]
    for flop in ([args.flop] if args.flop else TURNS):
        rootjob,old=source_job(args,flop)
        assert (rootjob['oop'],rootjob['ip'])==tuple(ranges.to_str(w) for w in ranges.ranges('BTN_BB','gto'))
        folder=args.results/flop
        case=dict(flop=flop,restricted_flop_sizes=([33] if flop==NEW else None),turns=[],selected=None)
        records.append(case)
        if args.driver:
            execute(args.driver,folder,rootjob)
        elif not (folder/'completed.txt').is_file() or not (folder/'result.json').is_file():
            case['status']='ROOT_UNAVAILABLE';continue
        assert json.loads((folder/'job.json').read_bytes())==rootjob
        root_raw=(folder/'result.json').read_bytes();root=json.loads(root_raw);rsha=sha(compact(root))
        case['native_root_sha256']=sha(root_raw)
        if not args.driver:
            assert (folder/'completed.txt').read_text().strip()==sha(root_raw)
        assert (root['flop'],root['pot'],root['stack'])==(flop,550,9750) and not root['info'].get('lock_stats')
        if old is not None:
            nodes={(n['board'],n['line'],n['player']):n for n in root['nodes']}
            assert all(nodes[(n['board'],n['line'],n['player'])]==n for n in old['nodes'])
            case['bit_identical_original_nodes']=len(old['nodes'])
        if not 0<=root['info']['gto_expl_pct']<=.5:
            case['status']='GTO_ROOT_OUTSIDE_CONVERGENCE'
            if args.driver:(folder/'completed.txt').write_text(sha(root_raw)+'\n')
            continue
        first,=(n for n in root['nodes'] if not n['line'])
        facing,=(n for n in root['nodes'] if n['line']=='b33')
        assert facing['bets']==[182,0]
        leads=accepted(first,root['hands'],'b33');calls=accepted(facing,root['hands'],'c')
        for turn in TURNS[flop]:
            pair={};paths={};rec=dict(turn=turn,river_checks={});case['turns'].append(rec)
            for version in ('gto','exp_ip'):
                job,locks,rivers,public=turn_job(root,flop,turn,version,pool,pipeline)
                oop={cardkey(h) for h,w in job['oop_w'] if turn not in cardkey(h)} & leads
                ip={cardkey(h) for h,w in job['ip_w'] if turn not in cardkey(h)} & calls
                if not any(set(h).isdisjoint(v) for h in ip for v in oop):
                    rec['status']='NO_JOINT_FLOP_CALL';break
                dest=folder/(turn+'-'+version)
                if args.driver:
                    execute(args.driver,dest,job)
                if not (dest/'result.json').is_file():
                    rec['status']='SUBGAME_UNAVAILABLE';break
                assert json.loads((dest/'job.json').read_bytes())==json.loads(compact(job))
                raw=(dest/'result.json').read_bytes();sub=json.loads(raw);info=sub['info']
                if not 0<=info['gto_expl_pct']<=.5 or (version=='exp_ip' and not 0<=info['hero_gap_pct']<=.5):
                    rec['status']='SUBGAME_OUTSIDE_CONVERGENCE';break
                sub.update(line0='b33 c',turn=turn,rivers=rivers)
                manifest=dict(spot='BTN_BB',pot_family='SRP',locks=locks)
                source=dict(root=root,subgame=sub,manifest=manifest,version=version,run=args.run,source_sha256=sha(raw))
                if version=='exp_ip':
                    parent=dict(run=args.run,sha256=rsha)
                    manifest.update(gto_parent_source_run_id=args.run,gto_parent_source_sha256=rsha)
                    source.update(verified_gto_parent=parent,measured_lock_application=audit_patterns(sub,job,manifest,pool,1),applied_rust_rates=info['lock_stats'])
                else:
                    assert not info.get('lock_stats')
                pair[version]=source;paths[version]=dest
            if args.driver or len(pair)!=2 or case['selected']:continue
            g,e=pair['gto'],pair['exp_ip']
            code=f'B550_R69_{flop.upper()}_{turn.upper()}'
            payload=gzip.compress(compact(dict(root_job=rootjob,root=root,native_root_file_b64=base64.b64encode(root_raw).decode(),run=args.run,solver=SOLVER,rust=RUST,pool_sha256=POOL,
                sources={v:dict(job=json.loads((d/'job.json').read_bytes()),source_file_b64=base64.b64encode((d/'result.json').read_bytes()).decode()) for v,d in paths.items()})),mtime=0)
            for s in (g,e):s.update(archive_code=code,archive_sha256=sha(payload))
            for river in rivers:
                full=public+river
                gr,er=(audit_decision(s,full,LINE,1,rsha) for s in (g,e))
                if not gr or not er:continue
                gh,eh=(published_actions(s,r,route) for s,r in ((g,gr),(e,er)))
                shared=[gh[h] for h in sorted(gh.keys()&eh.keys())]
                rec['river_checks'][full]=len(shared)
                if not shared or not all(r['b50'] and r['b50']['eligible'] for r in (gr,er)):continue
                board,pin=emit_board(model,g,e,full,LINE,texture(flop))
                pin.update(shared_rendered_checks=shared,flop_size_profile=rootjob['flop_oop'],original_full_menu_artifact=PINS.get(flop))
                board['nl2_locked_variants'][0].update(variant_label='原始 GTO 翻牌範圍，轉河牌套用 NL2 分街鎖頻',
                    applied_street_rates=rates(e),measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',pool_sha256=POOL,
                    gto_parent_source_run_id=args.run,gto_parent_source_sha256=rsha,viewer_archive_code=pin['viewer_archive_code'],viewer_sha256=pin['viewer_sha256'])
                if flop==NEW:board['flop_sizing_assumption']='One-third-pot flop menu for both positions'
                (EVIDENCE/f'NL2_{code}.json.gz').write_bytes(payload)
                group['boards'].append(board);group['pins'].append(pin)
                report['gto_references'][source_key(MID,gr)]=gr;report['references'][source_key(MID,er)]=er
                case['selected']=full
                break
        if args.driver:(folder/'completed.txt').write_text(sha(root_raw)+'\n')
    if args.driver:return
    count=len(group['boards'])
    assert count==len({b['flop'] for b in group['boards']})<=3
    if count==3:
        (EVIDENCE/'reverified/rank69.json').write_bytes(json_bytes(group))
        (DATA/'nl2_hu_b550_locked_medium.json').write_bytes(json_bytes(report))
    (DATA/'nl2_hu_b550_rank69_results.json').write_bytes(json_bytes(dict(run=args.run,count=count,records=records,paired=group)))


if __name__=='__main__':
    main()
