"""Extract the missing rank150 branch from B733's verified 7s7h4d root and test its four suited 65 hands."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

import hu_b724_rank150_rivers as native
import hu_b736_publish as prior
import hu_b754_rank150_paired_six as base
import hu_b765_rank150_low_flanks as deals
from hu_b467_river_source_gate import compact, json_bytes, sha

FLOP = '7s7h4d'
TURNS = ('5c', '6d', '2h')
HANDS = {'5'+s+'6'+s for s in 'cdhs'}
WORKER = 'tools/hu_b770_rank150_straight_draw.py'
OLD_JOB_SHA = 'edf8e61decf0dd9ac1885b41658bc1175ae5f62a9399e9b2047231809bfc3995'
OLD_ROOT_SHA = 'fd2caa812ded75f7fa9b0c0b9cedaabdd6b117fe6c3e97a57f122c5fa7122434'
SIZE = '33%,50%,75%,100%'


def original():
    auth = prior.authentication(json.loads(Path('data/nl2_hu_b736_source_receipts.json').read_bytes()))
    artifact_id, digest = prior.ARTIFACTS[FLOP]
    assert any(a['id'] == artifact_id and a['digest'] == 'sha256:'+digest for a in auth['artifacts'])
    archive = Path('data/solver_evidence/NL2_B733_R114_7S7H4D.zip')
    assert sha(archive.read_bytes()) == digest
    with ZipFile(archive) as z:
        proof = json.loads(z.read('proof.json'))
        raw_job, raw_result = [z.read(name) for name in ('flop/job.json','flop/result.json')]
        assert proof['flop'] == FLOP and proof['spot'] == 'LMP_CO_BB'
        assert (sha(raw_job),sha(raw_result)) == (OLD_JOB_SHA,OLD_ROOT_SHA)
        assert all(sha(z.read(p)) == digest for p,digest in proof['native_files'].items())
    job, root = json.loads(raw_job), json.loads(raw_result)
    assert len(root['nodes']) == 37 and not any(n['line']=='x b33 c/' for n in root['nodes'])
    assert job['flop_oop'] == job['flop_ip'] == SIZE and (job['pot'],job['stack']) == (250,9900)
    identity = dict(archive=archive.name,archive_sha256=digest,source_run=prior.RUN,source_head=prior.HEAD,
                    artifact_id=artifact_id,job_id=prior.JOBS[FLOP],original_root_sha256=OLD_ROOT_SHA,original_root_job_sha256=OLD_JOB_SHA)
    return job,root,identity


def screen(root, route):
    nodes = {n['line']:n for n in root['nodes'] if len(n['board'])==6}
    def accepted(line, action):
        return native.accepted(nodes[line],root['hands'],action)
    bb = accepted('','x') & accepted('x b33','c')
    co = accepted('x','b33')
    named = {''.join(h) for h in co if native.hand_cell(''.join(h),FLOP)[0] in route['flop']}
    assert named == HANDS and native.cardkey('AcAd') in bb
    assert (len(co),len(bb)) == (404,187)
    observations = {}
    for turn in TURNS:
        examples = {}
        for h in sorted(HANDS):
            if turn in native.cards(h) or native.hand_cell(h,FLOP+turn)[0] not in route['turn']:
                continue
            valid = [r for r in native.DECK if len(native.cards(FLOP+turn+r+h+'AcAd'))==9
                     and route['river'].get(native.hand_cell(h,FLOP+turn+r)[0])=='過']
            if valid:
                examples[h] = dict(compatible_bb='AcAd',turn_class=native.hand_cell(h,FLOP+turn)[0],river_examples=valid)
        assert examples
        observations[turn] = examples
    return observations


def verify_root(original_root, augmented):
    assert augmented['hands']==original_root['hands'] and augmented['info']['gto_iters']==original_root['info']['gto_iters']
    assert augmented['info']['gto_expl_pct']==original_root['info']['gto_expl_pct'] and not augmented['info'].get('lock_stats')
    indexed = {(n['line'],n['board'],n['player']):n for n in augmented['nodes']}
    assert len(indexed)==len(augmented['nodes'])==len(original_root['nodes'])+len(TURNS)
    assert all(indexed[n['line'],n['board'],n['player']]==n for n in original_root['nodes'])
    boundaries = {}
    for turn in TURNS:
        n, = [n for n in augmented['nodes'] if n['line']=='x b33 c/' and n['board'].endswith(turn)]
        assert (n['player'],n['pot'],n['bets']) == (0,416,[83,83])
        assert all(len(w)==len(h) and max(w)>0 for w,h in zip(n['wr'],augmented['hands'],strict=True))
        boundaries[turn] = sha(compact(n))
    return boundaries


def observed(root,game,turn,rivers,eligible,route,first):
    rows = native.observations(root,game,turn,rivers,eligible,route)
    policy = {}
    for public,row in rows.items():
        co,bb = deals.hand_pairs(root,game,turn,public)
        pairs = {(''.join(h),''.join(v)) for h in co if ''.join(h) in HANDS and ''.join(h) in row['hands']
                 for v in bb if set(h).isdisjoint(v)}
        if first is not None:
            pairs &= first[public]
        shared = {h for h,v in pairs}
        row['hands'] = {h:row['hands'][h] for h in sorted(shared)}
        row['compatible_bb_per_co'] = {h:sorted(v for hero,v in pairs if hero==h) for h in sorted(shared)}
        policy[public] = pairs
    return rows,policy


def turn_record(root, turn, route, template, manifest, pool, pipeline, out, driver):
    parent, eligible, rivers, diagnostic = native.parent_gate(root,turn,route)
    assert all(set(hs)<=HANDS for hs in eligible.values())
    record = dict(turn=turn,root_gate=diagnostic,preregistered_rivers=rivers,policies={},common={})
    if not rivers:
        record['negative_reason'] = 'ZERO_TWO_SEAT_FLOP_AND_THREE_STREET_UI_INTERSECTION'
        return record
    job = dict(template,flop=FLOP,turn=turn,line0=['x','b33','c','/'],root_no_bet=False,
               flop_oop=SIZE,flop_ip=SIZE,turn_oop=SIZE,turn_ip=SIZE,river_oop='50%,75%,100%,a',river_ip='50%,75%,100%,a',
               pot=416,stack=9817,oop='',ip='',iters=2200,rank_pct=.45,target_pct=.45,compress=False,out='result.json',
               extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',r],street=True) for r in rivers])
    for i,key in enumerate(('oop_w','ip_w')):
        job[key]=[[h,w] for h,w in zip(root['hands'][i],parent['wr'][i],strict=True) if w>1e-4]
    assert job['oop_w'] and job['ip_w'] and (job['rake_rate'],job['rake_cap'])==(.05,1000)
    first = None
    for version in ('gto','exp_ip'):
        target,rules = (job,[]) if version=='gto' else native.prepare_job(dict(source=dict(root=root,version='gto',manifest=manifest),job=job),'exp_ip',pool,pipeline)
        target['out'] = 'result.json'
        folder = out/(turn+'-'+version)
        game = native.solve(folder,target,driver)
        assert (folder/'job.json').read_bytes()==compact(target)
        assert native.cards(game['flop'])==native.cards(FLOP) and (game['pot'],game['stack'])==(416,9817)
        assert 0<=game['info']['gto_expl_pct']<=.5
        application = None
        if version=='exp_ip':
            assert target['hero']==1 and target['locks'] and game['hands']==gto_hands and 0<=game['info']['hero_gap_pct']<=.5
            application=native.audit_patterns(game,target,dict(manifest,locks=rules),pool,1)
            assert any(v>0 for k,v in application['driver_tree_nodes'].items() if k in application['marginal_targets'])
        else:
            assert not game['info'].get('lock_stats')
            gto_hands=game['hands']
        boards,match=observed(root,game,turn,rivers,eligible,route,first)
        record['policies'][version]=dict(source_sha256=sha((folder/'result.json').read_bytes()),job_sha256=sha(compact(target)),
                measured_lock_application=application,gto_gap_pct=game['info']['gto_expl_pct'],hero_gap_pct=game['info'].get('hero_gap_pct'),boards=boards)
        if version=='gto':
            first=match
            if not any(first.values()):
                record['negative_reason']='NO_GTO_SAME_CO_BB_RENDERED_RIVER_CHECK'
                break
        else:
            record['common']={p:sorted({h for h,_ in values}) for p,values in match.items() if values}
            if not record['common']:
                record['negative_reason']='NO_COMMON_CO_AND_BB_IN_GTO_AND_NL2'
    return record


def run(a):
    solver=a.solver.resolve()
    assert sys.version_info[:2]==(3,11) and subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==native.limp.SOLVER
    for path,digest in {**base.PINS,deals.WORKER:'3b528ee6849904817131e67063c7beb9aae8792f'}.items():
        assert native.limp.git_blob(path)==digest,path
    py=solver/'postflop/py';assert sha((py/'pipeline.py').read_bytes())==native.PIPELINE and sha((py/'ranges.py').read_bytes())==native.RANGES
    sys.path.insert(0,str(py))
    import pipeline
    raw_pool=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(raw_pool)==native.POOL and sha(Path(native.limp.TEMPLATE).read_bytes())==native.limp.TEMPLATE_SHA
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==native.limp.RUST
    pool=json.loads(raw_pool)['NL2']
    with ZipFile(native.limp.TEMPLATE) as z:
        manifest,template=[json.loads(z.read(p)) for p in ('original-manifest.json','original-turn.job.json')]
    original_job,old,origin=original()
    native.limp.check_limp_source(dict(manifest=manifest,root_job=original_job,subgame_job=None))
    routes=subprocess.check_output(['node',native.ROUTE]);route=json.loads(routes)
    assert (route['model_id'],route['line'],route['actor'],route['native_price'])==(native.MODEL,native.LINE,1,[416,9817])
    assert abs(9817/416/route['model_price'][2]-1)<.002
    screen_result=screen(old,route)
    if a.preflight:
        print(json.dumps({t:{h:len(row['river_examples']) for h,row in hands.items()} for t,hands in screen_result.items()}))
        return
    out=a.output
    if a.driver:
        assert not out.exists() or not any(out.iterdir())
    out.mkdir(parents=True,exist_ok=True)
    expanded=dict(original_job,extract=original_job['extract']+[dict(prefix=['x','b33','c',t],street=False,raw=True) for t in TURNS])
    if a.checkpoint:
        assert a.driver and not a.checkpoint_only
        shutil.copytree(a.checkpoint/'flop',out/'flop')
    root=native.solve(out/'flop',expanded,a.driver if a.checkpoint_only else None)
    assert (out/'flop/job.json').read_bytes()==compact(expanded)
    verified=verify_root(old,root)
    checkpoint=dict(source=origin,worker_blob=native.limp.git_blob(WORKER),old_nodes_identical=len(old['nodes']),
                    added_raw_boundaries=verified,expanded_job_sha256=sha(compact(expanded)),expanded_result_sha256=sha((out/'flop/result.json').read_bytes()))
    if a.checkpoint_only:
        (out/'checkpoint.json').write_bytes(json_bytes(checkpoint))
        return
    if a.driver:
        assert a.checkpoint and (a.checkpoint/'checkpoint.json').read_bytes()==json_bytes(checkpoint)
    (out/'checkpoint.json').write_bytes(json_bytes(checkpoint));(out/'rendered-routes.json').write_bytes(routes)
    (out/'original-manifest.json').write_bytes(json_bytes(manifest))
    report=dict(schema='NL2_B770_ORIGINAL_56S_RANK150_RIVER_SOURCE_V1',rank=150,model_id=native.MODEL,
                actor=1,line=native.LINE,flop=FLOP,origin=origin,original_flops_new=0,original_root_reexports=1,
                new_raw_turn_boundaries=list(TURNS),flop_solves_repeated_for_continuation=0,checkpoint=checkpoint,
                source_worker_blob=native.limp.git_blob(WORKER),solver=native.limp.SOLVER,rust=native.limp.RUST,pool_sha256=native.POOL,
                root_price=[250,9900],turn_river_price=[416,9817],route_sha256=sha(routes),prior_exact_flop_ui_deals=screen_result,
                assumed_preflop_ranges=True,lock_scope='FROZEN_GTO_FLOP_WITH_MEASURED_PARTIAL_TURN_RIVER_NL2_MARGINALS',
                no_observed_per_private_hand_frequency=True,selected=None,turns=[])
    for turn in TURNS:
        t=turn_record(root,turn,route,template,manifest,pool,pipeline,out,a.driver)
        report['turns'].append(t)
        if t['common']:
            report['selected']=dict(turn=turn,public_board=sorted(t['common'])[0])
            break
    report['positive_distinct_flops']=int(bool(report['selected']))
    report['native_file_sha256']={p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='proof.json'}
    (out/'proof.json').write_bytes(json_bytes(report))
    print(json.dumps({'flop':FLOP,'selected':report['selected'],'identical_original_nodes':len(old['nodes'])}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('solver','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--preflight',action='store_true');p.add_argument('--driver',type=Path)
    p.add_argument('--checkpoint-only',action='store_true');p.add_argument('--checkpoint',type=Path)
    run(p.parse_args())
