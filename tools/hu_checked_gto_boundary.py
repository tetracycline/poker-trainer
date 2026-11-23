"""Verify original checked flop boundaries and solve independently locked continuations."""
import base64
from copy import deepcopy
import gzip
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import compact, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b480_rank1_street_locks import packed
from hu_b483_locked_medium import POOL, PIPELINE, RANGES, proof
from hu_b485_locked_medium import legacy_rules
from hu_sequential_cfr_reach import game_reach
from solve_hu_multiboard_100bb import make_fallbacks
from verify_hu_multiboard_100bb import lock_scope


def lock_metadata(rows):
    return [dict(pat=r['pat'],source=r['src'],scope=r.get('scope','PINNED_MEASURED_NL2_SOURCE'),n=r['n'],
                 **({'street':r['street']} if 'street' in r else {})) for r in rows]


def load_original(folder, aid, pin, spot, flop, turn, version, *, pot, stack, pipeline, ranges, flop_line="x x"):
    info=json.loads((folder/f'{aid}.json').read_bytes())
    assert (info['id'],info['name'],info['digest'],info['workflow_run']['id'],info['workflow_run']['head_sha'],info['workflow_run']['repository_id'])==(
        aid,pin['name'],'sha256:'+pin['sha256'],pin['run'],pin['head'],1438346845)
    archive=folder/f'{aid}.zip'
    assert sha(archive.read_bytes())==pin['sha256']
    with ZipFile(archive) as z:
        files=[n for n in z.namelist() if n.startswith(('evidence/','trainer/evidence/'))]
        assert {SOLVER,RUST}<={z.read(n).decode().strip() for n in files if n.endswith('.txt')}
        mf,=[n for n in files if n.endswith('.json') and not n.endswith('pool_stats.json')]
        m=json.loads(z.read(mf))
        assert (m['spot'],m['version'],m['failures'])==(spot,version,[])
        c,=[c for c in m['cases'] if c['turn']==turn and c['line']==flop_line and (m.get('flop') or c['flop'])==flop]
        if m['schema']=='HU_MISSING_ACTION_HISTORY_CFR_V1':
            assert (m['source_pipeline_sha256'],m['source_ranges_sha256'],m['source_preflop_tree_sha256'])==(
                PIPELINE,RANGES,'d4ca8e0c7d53deb6af337bfef8ff0c125205c1d3ef912267d8b40efc2fe7c100')
            rp,rs,sp,ss=c['flop_json'],c['flop_sha256'],c['sub_json'],c['sub_sha256']
            measured=m.get('pool_lock_evidence',{}).get(flop,{}).get('source_patterns')
            expected,metadata=legacy_rules(pipeline,spot,version,flop,m.get('flop_bet_sizes'))
            if measured is None:
                # Older archives omit the report. Both native jobs must still match every reconstructed numerical rule below.
                measured = metadata
            for observed,reconstructed,native in zip(measured,metadata,expected,strict=True):
                assert all(observed[k]==value for k,value in reconstructed.items())
                assert set(observed)-set(reconstructed)<={'fold','raise_'}
                for key,action in (('fold','fold'),('raise_','raise')):
                    if key in observed:assert observed[key]==native[action]
            patterns=lock_metadata(measured)
        else:
            assert (m['schema'],m['pool_source_sha256'],m['solver_pin'],m['solver_ranges_sha256'],m['flop'])==(
                'NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1',POOL,PIPELINE,RANGES,flop)
            assert m['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
            rp,rs,sp,ss=m['file_flop'],m['file_flop_sha256'],c['source_path'],c['source_sha256']
            patterns=m['locks'];expected=None
        def extract(path,digest):
            f='solver/postflop/'+path;raw=z.read(f);job=z.read(f[:-5]+'.job.json')
            assert sha(raw)==digest
            return json.loads(raw),json.loads(job),sha(job)
        root,rj,rjs=extract(rp,rs);sub,j,js=extract(sp,ss)
    assert all((source['flop'],source['pot'],source['stack'])==(flop,pot,stack) for source in (root,rj))
    assert sub['turn']==j['turn']==turn and sub['line0']==flop_line and j['line0']==flop_line.split()+['/']
    assert (rj['oop'],rj['ip'])==tuple(ranges.to_str(weights) for weights in ranges.ranges(spot,version))
    hero={'gto':None,'exp_oop':0,'exp_ip':1}[version]
    for job in (rj,j):
        assert job.get('hero')==hero and (job['rake_rate'],job['rake_cap'])==(.05,1000)
        assert [r['pat'] for r in job.get('locks',[])]==[r['pat'] for r in patterns]
    assert rj.get('locks',[])==j.get('locks',[]) and bool(j.get('locks'))==(hero is not None)
    if expected is not None:assert j.get('locks',[])==json.loads(compact(expected))
    parent,=[n for n in root['nodes'] if n['line']==flop_line+'/' and n['board'][-2:]==turn]
    bet_pct, raise_multiple = {"x x": (0, 1), "x b33 c": (33, 1), "x b50 c": (50, 1), "x b75 c": (75, 1), "x b100 c": (100, 1), "x b75 r c": (75, 3), "b50 c": (50, 1), "b75 c": (75, 1), "b100 c": (100, 1)}[flop_line]
    bet = (pot * bet_pct + 50) // 100
    investment = bet * raise_multiple
    if bet:
        ip_bet = flop_line.startswith("x ")
        facing_line = ("x " if ip_bet else "") + f"b{bet_pct}"
        facing, = (n for n in root["nodes"] if len(n["board"]) == 6 and n["line"] == facing_line)
        assert (facing["pot"], facing["bets"]) == (pot + bet, [0, bet] if ip_bet else [bet, 0])
    if raise_multiple > 1:
        raised, = (n for n in root["nodes"] if len(n["board"]) == 6 and n["line"] == f"x b{bet_pct} r")
        assert (raised["pot"], raised["bets"]) == (pot + investment + bet, [investment, bet])
    assert parent['bets'] == [investment, investment] and len(parent['board']) == 8
    boundary = (pot + 2 * investment, stack - investment)
    assert (parent['pot'], stack - max(parent['bets'])) == boundary
    assert all((source['flop'], source['pot'], source['stack']) == (flop, *boundary) for source in (sub, j))
    for seat,name in enumerate(('oop_w','ip_w')):
        assert j[name]==[[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
    assert j['root_no_bet'] == (flop_line in ('x b33 c', 'x b50 c', 'x b75 c', 'x b100 c'))
    for game in (root,sub):
        assert 0<=game['info']['gto_expl_pct']<=.5
        if hero is not None:assert 0<=game['info']['hero_gap_pct']<=.5 and game['info']['lock_stats']
    src=dict(run=pin['run'],version=version,root=root,subgame=sub,source_sha256=ss,archive_code=f'GHA_{aid}',archive_sha256=pin['sha256'],
             manifest=dict(spot=spot,pot_family=ranges.SPOTS[spot]['kind'],locks=patterns))
    identity=dict(artifact_id=aid,artifact_run=pin['run'],artifact_sha256=pin['sha256'],head=pin['head'],root_sha256=rs,
                  source_sha256=ss,root_job_sha256=rjs,turn_job_sha256=js,flop_oop_menu=rj['flop_oop'],flop_ip_menu=rj['flop_ip'])
    return dict(source=src,job=j,identity=identity,public=parent['board'])


def prepare_job(original,version,pool,pipeline):
    source=original['source']
    assert source['version']=='gto' and not original['job'].get('locks') and not source['root']['info'].get('lock_stats')
    rule_rows,meta=make_fallbacks(source['manifest']['spot'],version,pool,pipeline.lock_list,source['root']['flop'],by_street=True)
    out=deepcopy(original['job']);hero={'exp_oop':0,'exp_ip':1}[version]
    out.update(hero=hero,locks=json.loads(compact(rule_rows)),rank_pct=.45,target_pct=.45,iters=max(2000,out['iters']),out='native.json')
    return out,lock_metadata(meta)


def solve_native(original,version,pool,pipeline,directory,driver,run,code):
    directory.mkdir(parents=True,exist_ok=True)
    job,meta=prepare_job(original,version,pool,pipeline);jraw=compact(job);(directory/'native.job.json').write_bytes(jraw)
    subprocess.run([str(driver.resolve()),'native.job.json'],cwd=directory,timeout=360,check=True)
    raw=(directory/'native.json').read_bytes()
    dest=directory/f'NL2_{code}.json.gz'
    packed(dest,dict(schema='NL2_HU_FROZEN_GTO_FLOP_CONDITIONAL_NATIVE_LOCK_V1',solver=SOLVER,rust=RUST,pool_sha256=POOL,
                     run=run,version=version,scope='FROZEN_GTO_FLOP_TURN_RIVER_LOCK_ONLY',original=original['identity'],
                     source_sha256=sha(raw),job_sha256=sha(jraw),job=job,locks=meta,source_file_b64=base64.b64encode(raw).decode()))
    return dest


def replay_native(original,version,pool,pipeline,path,run,code):
    blob=path.read_bytes();locked=json.loads(gzip.decompress(blob));job,meta=prepare_job(original,version,pool,pipeline)
    assert (locked['schema'],locked['solver'],locked['rust'],locked['pool_sha256'],locked['version'],locked['run'],locked['original'])==(
        'NL2_HU_FROZEN_GTO_FLOP_CONDITIONAL_NATIVE_LOCK_V1',SOLVER,RUST,POOL,version,run,original['identity'])
    assert locked['job']==job and locked['locks']==meta and locked['job_sha256']==sha(compact(job))
    raw=base64.b64decode(locked['source_file_b64'],validate=True);assert sha(raw)==locked['source_sha256']
    sub=json.loads(raw);g=original['source'];parent=original['identity']
    old=g['subgame'];assert all(sub[k]==old[k] for k in ('flop','pot','stack','hands'))
    assert job['line0'] == [*old['line0'].split(), '/']
    sub.update(line0=old['line0'],turn=old['turn'],rivers=old['rivers'])
    manifest=dict(g['manifest'],locks=meta,gto_parent_source_run_id=g['run'],gto_parent_source_sha256=parent['root_sha256'])
    assert parent['root_sha256']==sha(compact(g['root'])) and job['hero']==(version=='exp_ip')
    assert sub['info']['lock_stats']
    coverage=audit_patterns(sub,job,manifest,pool,hero_seat=job['hero'])
    return dict(version=version,run=run,source_sha256=sha(raw),root=g['root'],subgame=sub,manifest=manifest,
                verified_gto_parent=dict(run=g['run'],sha256=parent['root_sha256']),archive_code=code,archive_sha256=sha(blob),
                measured_lock_application=coverage,applied_rust_rates=sub['info']['lock_stats'])


def audit_decision(source, public, line, seat, root_sha):
    root,sub=source['root'],source['subgame'];v=source['version'];m=source['manifest']
    target=[n for n in sub['nodes'] if (n['board'],n['line'],n['player'])==(public,line,seat)]
    if not target:return None
    node,=target
    assert node['bets']==[0,0] and node['pot']==sub['pot']
    obs=proof(root,sub,node,game_reach(root,sub)[0]);scope=lock_scope(sub,m['locks'],v)
    obs.update(version=v,spot=m['spot'],family=m['pot_family'],flop=sub['flop'],turn=sub['turn'],source_run_id=source['run'],
               source_sha256=source['source_sha256'],archive_sha256=source['archive_sha256'],root_sha256=root_sha,
               gto_gap_pct=sub['info']['gto_expl_pct'],locked_hero_gap_pct=sub['info'].get('hero_gap_pct'),
               root_gto_stage_gap_pct=root['info']['gto_expl_pct'],root_locked_hero_gap_pct=root['info'].get('hero_gap_pct'),lock_scope=scope,
               root_applied_rust_lock_nodes=sum(s['nodes'] for s in root['info'].get('lock_stats',{}).values()),
               subgame_applied_rust_lock_nodes=sum(s['nodes'] for s in sub['info'].get('lock_stats',{}).values()))
    return obs
