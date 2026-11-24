"""Solve new turn and river continuations from three verified B687 flop roots."""
import argparse
import base64
import io
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import hu_b687_publish_rank103 as parent
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b568_caller_rivers import hand_cell
from hu_b637_rank57 import solve
from hu_b687_collect import authenticate, validate_preflight
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, game_reach
from hu_trainer_route_gate import compatible

MODEL = 'ln-3bp-3c_r_model-13bw264'
LINE = 'b33 c/x x/x'
PAIRED_TURN = {'Qs8h4d':'2c', 'Jh8d3c':'5s', '9c6c3h':'2d'}
CASES = {'Qs8h4d':['Ah','Tc','5s'], 'Jh8d3c':['Qs','9c'], '9c6c3h':['Td','8d','4s']}
DECK = [rank+suit for rank in '23456789TJQKA' for suit in 'cdhs']
EVIDENCE = Path('data/solver_evidence')
WORKERS = 'data/nl2_hu_b687_rank103_workers.json'
PINS = {
    WORKERS:'6eaaa70bb91688537e7b761a983f0710fec8645a',
    'tools/hu_b687_publish_rank103.py':'bbea922a2831a3f188c3c3511465ddb1191c5add',
    'tools/hu_b687_collect.py':'392d16713c97b7a945b07266bf87ce54608b04f1',
    'tools/hu_b684_rank103_routes.cjs':'52f4a2768516af9448ea8e9c023a92388006dd92',
    'tools/hu_b714_rank255_routes.cjs':'280774f9ff78d6373041d8c6039bb85b2b3453fc',
    'tools/hu_b568_caller_rivers.py':'e69bda7fe46c3dd18a48dee1bb97f965ab2813f7',
    'tools/hu_b637_rank57.py':'86b795adbd8ff4e6e411a70cebf8b3db1efc4ff9',
    'nl2_hu_model.js':'b4a308a0f65b707f43f41f0b354cec87c08d5af6',
    'nl2.js':'15aee97e53a156fe073c96a120638a8a3679958f',
    'tools/hu_trainer_route_contract.cjs':'3b10524228c357552bb3f1eac88e17f9b2459b32',
}


def cards(text):
    return {text[k:k+2] for k in range(0,len(text),2)}


def blob(path):
    return subprocess.check_output(['git','hash-object',str(path)],text=True).strip()


def routes():
    old = json.loads(subprocess.check_output(['node','tools/hu_b684_rank103_routes.cjs']))
    raw = subprocess.check_output(['node','tools/hu_b714_rank255_routes.cjs'])
    target = json.loads(raw)
    assert (target['id'],target['parent'],target['root'],target['root_fact']['spot']) == (
        MODEL,old['id'],old['source'],'BB3_BTN')
    assert target['actual'] == [34.04,83.23,2.445]
    contract = json.loads(Path('data/nl2_hu_verified_extensions.json').read_bytes())['trainer_route_contract']['routes'][MODEL]
    assert compatible(contract,dict(public_board='2d7hKs9d5s',actual_exact_action_line=LINE,acting_seat=1))
    return old,target,raw


def authenticated_parent(flop,pipeline,ranges,pool,previous_route):
    pin, = [p for p in json.loads(Path(WORKERS).read_bytes()) if p['flop']==flop]
    folder = EVIDENCE/'provenance/B687'
    run_raw = (folder/'run.json').read_bytes()
    job_raw = (folder/f'job.{pin["job"]}.json').read_bytes()
    receipt_raw = (folder/f'{pin["id"]}.json').read_bytes()
    assert (sha(run_raw),sha(job_raw),sha(receipt_raw)) == (
        pin['workflow_run_receipt_sha256'],pin['job_receipt_sha256'],pin['receipt_sha256'])
    run,job,receipt = map(json.loads,(run_raw,job_raw,receipt_raw))
    authenticate(run,job,receipt,pin)
    listed, = [a for a in json.loads((folder/'artifacts.json').read_bytes())['artifacts'] if a['id']==pin['id']]
    jobs=json.loads((folder/'jobs.json').read_bytes())['jobs']
    assert job==next(j for j in jobs if j['id']==pin['job'])
    validate_preflight(next(j for j in jobs if j['name']=='routes-and-audit'))
    authenticate(run,job,listed,pin)
    archive = (EVIDENCE/('NL2_B687_R103_'+flop.upper()+'.zip')).read_bytes()
    assert sha(archive)==pin['sha256']
    verified,_ = parent.verify_worker(pin,archive,pipeline,ranges,pool,previous_route)
    assert verified is not None
    g,e,_,_,gh,eh,_ = verified
    turn=PAIRED_TURN[flop]
    assert g['subgame']['turn']==e['subgame']['turn']==turn
    with ZipFile(io.BytesIO(archive)) as source:
        root_raw=source.read('flop/result.json')
        original_claim=json.loads(source.read('proof.json'))
        used_turns=[t['turn'] for t in original_claim['turns']]
        assert set(CASES[flop]).isdisjoint(used_turns)
        assert not any(name.startswith(t+'-') for name in source.namelist() for t in CASES[flop])
    assert sha(compact(g['root']))==sha(compact(e['root']))==g['root_sha256']
    for source in (g,e):
        assert all(len(n['board'])==8 for n in source['subgame']['nodes'])
    return pin,g,e,gh,eh,used_turns,sha(root_raw)


def original_checked_rivers(g,e,gh,eh,route):
    """Before any solve, retain deals with a shared checked-turn hand in both originals."""
    eligible=sorted(h for h in gh.keys()&eh.keys() if gh[h]['displayed_suggestion']==eh[h]['displayed_suggestion']=='過'
        and all('x' in pol[h]['accepted_actions'] for pol in (gh,eh)))
    villains=[]
    public=None
    for source in (g,e):
        root,sub=source['root'],source['subgame']
        lead,=(n for n in root['nodes'] if n['line']=='' and n['player']==0)
        check,=(n for n in sub['nodes'] if n['line']=='b33 c/' and n['player']==0)
        facing,=(n for n in sub['nodes'] if n['line']=='b33 c/x' and n['player']==1)
        assert (check['board'],check['pot'],check['bets'])==(facing['board'],3404,[0,0])
        public=check['board']
        live={cardkey(h) for h,w in zip(sub['hands'][0],facing['w'][0],strict=True) if w>1e-4 and cards(public).isdisjoint(cardkey(h))}
        villains.append(accepted(lead,root['hands'],'b33') & accepted(check,sub['hands'],'x') & live)
    found={}
    for river in DECK:
        if river in cards(public):continue
        possible=[]
        for h in eligible:
            if river in cards(h):continue
            cells=[hand_cell(h,(public+river)[:n])[0] for n in (6,8,10)]
            if cells[0] not in route['flop'] or cells[1] not in route['turn'] or route['river'].get(cells[2])!='過':continue
            dead=cards(public+river+h)
            if all(any(dead.isdisjoint(v) for v in policy) for policy in villains): possible.append(h)
        if possible:found[river]=possible
    return found


def new_parent_rivers(root,turn,route):
    """Use the immutable flop action policies and original raw turn weights."""
    lead,=(n for n in root['nodes'] if (n['line'],n['player'])==('',0))
    facing,=(n for n in root['nodes'] if (n['line'],n['player'])==('b33',1))
    boundary,=(n for n in root['nodes'] if n['line']=='b33 c/' and n['board'].endswith(turn))
    public=boundary['board']
    assert (boundary['player'],boundary['pot'],boundary['bets'])==(0,3404,[677,677])
    assert cards(public[:6])==cards(root['flop'])==cards(lead['board'])==cards(facing['board'])
    assert len(public)==8 and len(cards(public))==4
    live=[{cardkey(h) for h,w in zip(root['hands'][seat],boundary['wr'][seat],strict=True)
        if w>1e-4 and cards(public).isdisjoint(cardkey(h))} for seat in (0,1)]
    opponents=accepted(lead,root['hands'],'b33')&live[0]
    callers=accepted(facing,root['hands'],'c')&live[1]
    heroes=sorted(''.join(h) for h in callers if hand_cell(''.join(h),public[:6])[0] in route['flop']
        and hand_cell(''.join(h),public)[0] in route['turn'] and any(set(h).isdisjoint(v) for v in opponents))
    found={}
    for river in DECK:
        if river in cards(public):continue
        possible=[h for h in heroes if river not in cards(h) and route['river'].get(hand_cell(h,public+river)[0])=='過'
            and any(cards(public+river+h).isdisjoint(v) for v in opponents)]
        if possible:found[river]=possible
    return found,dict(raw_boundary_sha256=sha(compact(boundary)),public_board=public,
        strict_flop_bettors=len(opponents),strict_flop_callers=len(callers),two_seat_flop_turn_ui_heroes=len(heroes),
        legal_river_count=len(found))


def assess(root,sub,turn,rivers,allowed,route):
    sub.update(line0='b33 c',turn=turn,rivers=rivers)
    masks=game_reach(root,sub)[0]
    nodes=[n for n in sub['nodes'] if n['line']==LINE and n['player']==1]
    assert {n['board'][-2:] for n in nodes}==set(rivers) and len(nodes)==len(rivers)
    result={}
    for node in nodes:
        public=node['board']
        assert cards(public[:6])==cards(root['flop']) and public[6:8]==turn and len(cards(public))==5
        assert (node['pot'],node['bets'],sub['stack'])==(3404,[0,0],8323)
        row=proof(root,sub,node,masks)
        bits=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
        hand_proof={}
        for h,mask in zip(sub['hands'][1],bits,strict=True):
            key=''.join(cardkey(h))
            if key not in allowed[public[-2:]] or not mask & (1<<node['acts'].index('x')):continue
            cells=[hand_cell(h,public[:n]) for n in (6,8,10)]
            assert cells[0][0] in route['flop'] and cells[1][0] in route['turn'] and route['river'][cells[2][0]]=='過'
            hand_proof[key]=dict(classes=[c[1] for c in cells],displayed_suggestion='過',accepted_actions=[a for i,a in enumerate(node['acts']) if mask&(1<<i)])
        result[public]=dict(reach=row,hands=hand_proof)
    return result


def run(args):
    assert sys.version_info[:2]==(3,11)
    for path,digest in PINS.items():assert blob(path)==digest,path
    solver=args.solver.resolve();py=solver/'postflop/py'
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==parent.SOLVER
    assert sha((py/'pipeline.py').read_bytes())==PIPELINE and sha((py/'ranges.py').read_bytes())==RANGES
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(pool_raw)==POOL
    sys.path.insert(0,str(py));import pipeline,ranges
    pool=json.loads(pool_raw)['NL2']
    if args.driver:
        assert args.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==parent.RUST
    old,route,route_raw=routes();flop=args.flop
    pin,g,e,gh,eh,used_turns,root_sha=authenticated_parent(flop,pipeline,ranges,pool,old)
    old_rivers=original_checked_rivers(g,e,gh,eh,route)
    assert not old_rivers, 'The published turn now has a genuine checked continuation: review it before spending new CFR'
    planned=[]
    for turn in CASES[flop]:
        allowed,gate=new_parent_rivers(g['root'],turn,route)
        options=list(allowed)
        rivers=options if len(options)<=16 else [options[round(i*(len(options)-1)/15)] for i in range(16)]
        planned.append((turn,allowed,gate,rivers))
    if args.preflight:
        print(json.dumps(dict(flop=flop,authenticated_root_sha256=root_sha,original_turns_skipped=used_turns,
            original_paired_turn_check_rivers=0,new_boundaries=[dict(turn=t,**gate) for t,_,gate,_ in planned])))
        return
    output=args.output.resolve()
    if args.driver:assert not output.exists() or not any(output.iterdir())
    else:assert (output/'proof.json').is_file()
    output.mkdir(parents=True,exist_ok=True)
    report=dict(schema='NL2_B714_R255_RIVER_CONTINUATION_V1',rank=255,model_id=MODEL,flop=flop,
        line=LINE,actor=1,pot=3404,stack=8323,actual_spr=round(8323/3404,6),parent_pin=pin,
        root_sha256=root_sha,canonical_root_sha256=g['root_sha256'],flop_native_solves_repeated=0,
        source_worker_blob=blob('tools/hu_b714_rank255_rivers.py'),source_algorithm_blobs=PINS,
        original_turns_skipped=used_turns,original_paired_turn_zero_shared_check=True,
        original_paired_turn_sha256={s['version']:s['source_sha256'] for s in (g,e)},
        preregistered_new_turns=CASES[flop],route_sha256=sha(route_raw),pool_sha256=POOL,
        solver=parent.SOLVER,rust=parent.RUST,restricted_flop_sizes_pct=[33,50,75],
        turn_menu_pct=[33,50,75,100],river_menu='50%,75%,100%,a',
        scope='FROZEN_GTO_FLOP_TURN_RIVER_PARTIAL_NL2_MARGINALS',
        assumed_default_sources_separate=True,observed_per_private_hand_NL2=False,turns=[],selected=None)
    (output/'rank255-routes.json').write_bytes(route_raw)
    for turn,allowed,gate,rivers in planned:
        record=dict(turn=turn,root_gate=gate,preregistered_rivers=rivers,policies={},common={})
        report['turns'].append(record)
        if not rivers:
            record['negative_reason']='NO_TWO_SEAT_FLOP_ANCESTRY_AND_PLAYABLE_RIVER';continue
        gjob=parent.expected_turn(g['root'],turn,pipeline)
        assert gjob['extract']==[dict(prefix=[],street=True)]
        gjob['extract'] += [dict(prefix=['x','x',r],street=True) for r in rivers]
        for version in ('gto','exp_ip'):
            if version=='gto':job,metadata=gjob,[]
            else:
                job,metadata=prepare_job(dict(source=g,job=gjob),'exp_ip',pool,pipeline)
                job['out']='result.json'
            folder=output/(turn+'-'+version)
            game=solve(folder,job,args.driver)
            assert (game['flop'],game['pot'],game['stack'])==(flop,3404,8323)
            assert 0<=game['info']['gto_expl_pct']<=.5
            applied=None
            if version=='exp_ip':
                assert 0<=game['info']['hero_gap_pct']<=.5 and job['hero']==1 and game['hands']==gto_hands
                applied=audit_patterns(game,job,dict(locks=metadata),pool,1)
                assert any(n>0 for p,n in applied['driver_tree_nodes'].items() if p in applied['marginal_targets'])
            else:
                assert not game['info'].get('lock_stats');gto_hands=game['hands']
            observed=assess(g['root'],game,turn,rivers,allowed,route)
            record['policies'][version]=dict(source_sha256=sha((folder/'result.json').read_bytes()),
                job_sha256=sha((folder/'job.json').read_bytes()),gto_gap_pct=game['info']['gto_expl_pct'],
                hero_gap_pct=game['info'].get('hero_gap_pct'),measured_lock_application=applied,boards=observed)
            if version=='gto' and not any(item['hands'] for item in observed.values()):
                record['negative_reason']='NO_GTO_RIVER_HAND_MATCHES_RENDERED_CHECK';break
        if 'exp_ip' in record['policies']:
            before=record['policies']['gto']['boards'];after=record['policies']['exp_ip']['boards']
            for public in sorted(before):
                common=sorted(before[public]['hands'].keys()&after[public]['hands'].keys())
                if common:record['common'][public]=common
            if record['common']:
                report['selected']=dict(turn=turn,public_board=next(iter(record['common'])));break
            record['negative_reason']='NO_COMMON_GTO_AND_NL2_RENDERED_RIVER_CHECK'
    report['positive_distinct_flops']=int(report['selected'] is not None)
    report['native_file_sha256']={str(p.relative_to(output)):sha(p.read_bytes()) for p in sorted(output.rglob('*')) if p.is_file() and p.name!='proof.json'}
    (output/'proof.json').write_bytes(json_bytes(report))
    locked=[b for r in report['turns'] for b in r['policies'].get('exp_ip',{}).get('boards',{}).values()]
    joint=[b for b in locked if b['reach']['strict_legal_combos']>0 and b['reach']['b50'] is not None]
    print(json.dumps(dict(flop=flop,positive=report['positive_distinct_flops'],
        common_rivers=sum(len(r['common']) for r in report['turns']),actor_locked_reachable_rivers=len(joint),
        gto_turn_jobs=sum('gto' in r['policies'] for r in report['turns']),
        actor_lock_turn_jobs=sum('exp_ip' in r['policies'] for r in report['turns']),
        half_pot_assessed=len(joint),nonpolarized_candidates=sum(b['reach']['b50']['candidate'] for b in joint))))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for name in ('solver','output'):cli.add_argument('--'+name,type=Path,required=True)
    cli.add_argument('--preflight',action='store_true')
    cli.add_argument('--driver',type=Path)
    cli.add_argument('--flop',choices=CASES,required=True)
    run(cli.parse_args())
