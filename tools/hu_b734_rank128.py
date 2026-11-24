"""Add the missing BB-response NL2 lock to an authenticated GTO source without a new GTO solve."""
import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b568_caller_rivers import hand_cell
from hu_b637_rank57 import solve
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import game_reach, cardkey

AID=14630030655
PIN=dict(name='nl2-multiboard-B5_SBGAPS-SB_BB-gto-KsQh4d',run=44736420272,head='e4bc0095a7cbfd75820c6d211bf0dacb255c5e3d',
         sha256='5ad798c2d3516b289acc7b23edb634293b632c150ddbbc2997912198dc498bac')
MODEL='ln-ipc-r_model-va4mgd'
LINE='b33 c/x b100 c/x'
ROUTES='tools/hu_b734_rank128_routes.cjs'


def original(receipts, ranges):
    artifact=json.loads((receipts/f'{AID}.json').read_bytes())
    workflow=artifact['workflow_run']
    assert (artifact['id'],artifact['name'],artifact['digest'],workflow['id'],workflow['head_sha'],workflow['repository_id'])==(AID,PIN['name'],'sha256:'+PIN['sha256'],PIN['run'],PIN['head'],1438346845)
    archive=receipts/f'{AID}.zip'
    assert sha(archive.read_bytes())==PIN['sha256']
    with ZipFile(archive) as z:
        pins={z.read(n).decode().strip() for n in z.namelist() if n.startswith('evidence/') and n.endswith('.txt')}
        assert {SOLVER,RUST}<=pins
        m=json.loads(z.read('evidence/SB_BB-gto-KsQh4d.json'))
        assert (m['schema'],m['spot'],m['flop'],m['version'],m['pot_family'],m['failures'],m['locks'])==(
            'NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1','SB_BB','KsQh4d','gto','SRP',[],[])
        assert (m['pool_source_sha256'],m['solver_pin'],m['solver_ranges_sha256'])==(POOL,PIPELINE,RANGES)
        assert m['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR' and m['preflop_ranges']['spot']=='SB_BB'
        case,=[c for c in m['cases'] if (c['line'],c['turn'])==('b33 c','Tc')]
        def extract(path,expected):
            result='solver/postflop/'+path
            raw=z.read(result);jraw=z.read(result[:-5]+'.job.json')
            assert sha(raw)==expected
            return json.loads(raw),json.loads(jraw),sha(jraw)
        root,rj,rjs=extract(m['file_flop'],m['file_flop_sha256']);sub,job,js=extract(case['source_path'],case['source_sha256'])
    assert (rj['oop'],rj['ip'])==tuple(ranges.to_str(w) for w in ranges.ranges('SB_BB','gto'))
    for game,j,pot,stack in [(root,rj,600,9700),(sub,job,996,9502)]:
        assert all((v['flop'],v['pot'],v['stack'])==('KsQh4d',pot,stack) for v in (game,j))
        assert (j['rake_rate'],j['rake_cap'])==(.05,1000) and not j.get('locks') and j.get('hero') is None
        assert 0<=game['info']['gto_expl_pct']<=.5 and not game['info'].get('lock_stats')
    p,=[n for n in root['nodes'] if (n['line'],n['board'])==('b33 c/','4dQhKsTc')]
    gate,=[n for n in root['nodes'] if n['line']=='b33']
    assert (p['player'],p['pot'],p['bets'],gate['player'],gate['pot'],gate['bets'])==(0,996,[198,198],1,798,[198,0])
    assert (sub['turn'],sub['line0'],job['turn'],job['line0'],job['root_no_bet'])==('Tc','b33 c','Tc',['b33','c','/'],False)
    for i,k in enumerate(('oop_w','ip_w')):
        assert job[k]==[[h,w] for h,w in zip(root['hands'][i],p['wr'][i],strict=True) if w>1e-4]
    source=dict(version='gto',root=root,subgame=sub,manifest=dict(spot='SB_BB',pot_family='SRP',locks=[]))
    return dict(source=source,job=job,identity=dict(artifact_id=AID,**PIN,root_sha256=m['file_flop_sha256'],
                root_job_sha256=rjs,original_gto_turn_source_sha256=case['source_sha256'],original_turn_job_sha256=js))


def inspect(root, sub, routes):
    sub.update(line0='b33 c',turn='Tc')
    masks=game_reach(root,sub)[0]
    rows={}
    for node in sub['nodes']:
        if (node['line'],node['player'])!=(LINE,1):continue
        board=node['board']
        assert board[:8]=='4dQhKsTc' and (node['pot'],node['bets'],sub['stack'])==(2988,[996,996],9502)
        assert abs((sub['stack']-996)/node['pot']/2.833-1)<.05
        reach=proof(root,sub,node,masks)
        action=1<<node['acts'].index('x')
        bits=base64.b64decode(reach['compatible_action_mask_b64'],validate=True)
        hands=[]
        for hole,mask in zip(sub['hands'][1],bits,strict=True):
            if not mask&action:continue
            hand=''.join(cardkey(hole))
            if all(hand_cell(hand,board[:end])[0] in routes[street] for street,end in [('flop',6),('turn',8),('river',10)]):
                hands.append(hand)
        rows[board]=dict(reach=reach,displayed_check_hands=sorted(hands))
    assert set(rows)=={'4dQhKsTc3h','4dQhKsTc4c'}
    return rows


def main(a):
    assert sys.version_info[:2]==(3,11)
    solver=a.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    native=solver/'postflop/py'
    assert sha((native/'pipeline.py').read_bytes())==PIPELINE and sha((native/'ranges.py').read_bytes())==RANGES
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
    sys.path.insert(0,str(native))
    import pipeline,ranges
    raw_pool=(solver/'inputs/pool_stats.json').read_bytes();assert sha(raw_pool)==POOL
    pool=json.loads(raw_pool)['NL2']
    model=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (model['frequency_rank'],model['label'],model['solver_profile'],model['assumed_model_node_spr'])==(128,'APPROX','SB_BB',2.833)
    raw_route=subprocess.check_output(['node',ROUTES]);route=json.loads(raw_route)
    assert route['model']==MODEL and route['river']=={'KQ_high:1':'過'}
    old=original(a.receipts,ranges)
    s=old['source'];root=s['root'];sub=s['subgame']
    assert (old['job']['pot'],old['job']['stack'],old['job']['turn_ip'],old['job']['river_ip'])==(996,9502,'50%,100%','50%,100%,a')
    before=inspect(root,sub,route)
    gate=before['4dQhKsTc3h']
    assert len(gate['displayed_check_hands'])==9 and gate['reach']['compatible_hole_card_pairs']==791
    assert not before['4dQhKsTc4c']['displayed_check_hands']
    if a.preflight:
        print(json.dumps(dict(flop='KsQh4d',pot=2988,stack=8506,shared_source_gto_hands=9,compatible_pairs=791)));return
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    job,rules=prepare_job(old,'exp_ip',pool,pipeline);job['out']='result.json'
    assert job['hero']==1 and job['locks']
    exp=solve(out/'exp_ip',job,a.driver)
    assert exp['hands']==sub['hands'] and exp['info']['lock_stats']
    assert 0<=exp['info']['hero_gap_pct']<=.5 and 0<=exp['info']['gto_expl_pct']<=.5
    measured=audit_patterns(exp,job,dict(locks=rules),pool,1)
    assert any(v>0 for k,v in measured['driver_tree_nodes'].items() if k in measured['marginal_targets'])
    after=inspect(root,exp,route)
    common={b:sorted(set(v['displayed_check_hands'])&set(after[b]['displayed_check_hands'])) for b,v in before.items()}
    reached=[v['reach'] for v in after.values() if v['reach']['compatible_hole_card_pairs']>=v['reach']['strict_legal_combos']>0]
    assert all(v['b50'] is not None for v in reached)
    counts=dict(positive_distinct_flops=int(any(common.values())),native_locked_public_boards=len(after),
                joint_halfpot_assessed=len(reached),nonpolarized_candidates=sum(bool(v['b50']['candidate']) for v in reached))
    report=dict(schema='NL2_B734_SB_BB_R128_ORIGINAL_GTO_PLUS_CONDITIONAL_NL2',rank=128,model=MODEL,flop='KsQh4d',turn='Tc',
                line=LINE,actor=1,existing_gto=old['identity'],source_gto_solves_repeated=0,source_flop_solves_repeated=0,
                solver=SOLVER,rust=RUST,pool_sha256=POOL,policy_scope='Authenticated SB versus BB GTO flop and turn; new BB response against observed SB marginal locks.',
                rendered_route_sha256=sha(raw_route),nl2_job_sha256=sha((out/'exp_ip/job.json').read_bytes()),
                nl2_source_sha256=sha((out/'exp_ip/result.json').read_bytes()),applied_measured_lock=measured,gto=before,nl2=after,
                same_displayed_hands_by_public_board=common,**counts)
    (out/'proof.json').write_bytes(json_bytes(report));(out/'rendered-routes.json').write_bytes(raw_route)
    print(json.dumps(counts))


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ('solver','receipts','output'):cli.add_argument('--'+key,type=Path,required=True)
    cli.add_argument('--driver',type=Path);cli.add_argument('--preflight',action='store_true')
    main(cli.parse_args())
