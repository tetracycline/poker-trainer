"""Replay B681's fourteen original nodes and check its sole Kd9c5h SB hand on three unextracted diamond turns."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b568_caller_rivers import hand_cell
from hu_b676_checked_rivers import DECK,LINE,MODELS,public_cards
from hu_b727_rank229 import observations,prepare_job,audit_patterns,solve,accepted,cardkey,SOLVER,RUST,POOL,PIPELINE,RANGES
from hu_trainer_route_gate import compatible

FLOP='Kd9c5h'
HERO='6d9d'
TURNS={'8d':(133,18),'7d':(133,18),'Td':(126,21)}
MODE='exp_oop'
MODEL=MODELS[229]
ROUTE='tools/hu_b676_checked_routes.cjs'
RUN=45308387321
HEAD='47d7bbeb4f40c73113830a72f299f2aabb1ad7aa'
ARTIFACT=14882375723
DIGEST='0b8ca55055abb9eec56204cb86f38239256cefb95fdefbf6d50dfa825e57779f'
EV=Path('data/solver_evidence')

def read(p):
    return json.loads(p.read_bytes())

def source(archive,ranges):
    auth=read(EV/'partial/b683_auth_receipt.json')
    pin,=[w for w in auth['workers'] if w['pin']['flop']==FLOP]
    assert (auth['run']['id'],auth['run']['head_sha'],auth['run']['conclusion'])==(RUN,HEAD,'success')
    assert (pin['artifact']['id'],pin['artifact']['digest'],pin['job']['id'],pin['job']['conclusion'])==(ARTIFACT,'sha256:'+DIGEST,138157708558,'success')
    assert sha(archive.read_bytes())==DIGEST
    with ZipFile(archive) as z:
        data=lambda k:json.loads(z.read(k))
        proof=data('proof.json');assert proof==read(EV/'partial/b683_KD9C5H_proof.json')
        root=data('flop/result.json');job=data('flop/job.json');template=data('2s-gto/job.json')
        record,=[x for x in read(Path('data/nl2_hu_b683_rank229_negatives.json'))['records'] if x['flop']==FLOP]
        assert record['worker_sha256']==DIGEST and sha(compact(root))==proof['root_sha256']
        assert all(sha(z.read(k))==v for k,v in record['native_files_sha256'].items())
        origin=dict(run=RUN,head=HEAD,artifact=ARTIFACT,job=pin['job']['id'],archive_sha256=DIGEST,original_flop_sha256=sha(z.read('flop/result.json')),canonical_original_flop_sha256=proof['root_sha256'],
                    original_flop_job_sha256=sha(z.read('flop/job.json')),original_turn_template_sha256=sha(z.read('2s-gto/job.json')))
    assert (root['flop'],root['pot'],root['stack'],len(root['nodes']))==(FLOP,2100,9000,14)
    assert not root['info'].get('lock_stats') and 0<=root['info']['gto_expl_pct']<=.5
    assert (job['flop_oop'],job['flop_ip'],job['rake_rate'],job['rake_cap'])==('50%','50%',.05,1000)
    assert (job['oop'],job['ip'])==tuple(ranges.to_str(w) for w in ranges.ranges('SB3_BTN','gto'))
    assert (template['turn_oop'],template['turn_ip'],template['root_no_bet'],template['pot'],template['stack'])==('33%,50%,75%','33%,50%,75%',False,2100,9000)
    assert template['line0']==['x','x','/'] and not template.get('locks') and not job.get('locks')
    extra=[dict(prefix=['x','x',t],street=False,raw=True) for t in TURNS]
    assert not any(a['prefix']==b['prefix'] for a in extra for b in job['extract'])
    return root,dict(job,extract=job['extract']+extra),template,origin

def gates(root,turn,route,boundary=None):
    nodes={n['line']:n for n in root['nodes'] if len(n['board'])==6};board=nodes['']['board']+turn
    assert public_cards(board[:6])==public_cards(FLOP)
    sb,btn=[accepted(nodes[k],root['hands'],'x') for k in ('','x')]
    assert {''.join(h) for h in sb}=={HERO}
    btn={h for h in btn if public_cards(board+HERO).isdisjoint(h)}
    assert all(hand_cell(HERO,board[:cut])[0] in route[key] for cut,key in [(6,'flop'),(8,'turn')])
    if boundary:
        assert (boundary['board'],boundary['line'],boundary['player'],boundary['pot'],boundary['bets'])==(board,'x x/',0,2100,[0,0])
        live=[{cardkey(h) for h,w in zip(root['hands'][i],boundary['wr'][i],strict=True) if w>1e-4} for i in (0,1)]
        if not sb&live[0]:return [],set()
        btn&=live[1]
    rivers=[r for r in DECK if r not in public_cards(board+HERO) and route['river'].get(hand_cell(HERO,board+r)[0])=='過' and any(r not in h for h in btn)]
    return rivers,btn

def compare(old,new):
    assert all(old[k]==new[k] for k in ('flop','pot','stack','hands'))
    assert not new['info'].get('lock_stats') and 0<=new['info']['gto_expl_pct']<=.5
    identity=lambda n:(n['board'],n['line'],n['player'])
    nodes={identity(n):n for n in new['nodes']}
    assert len(nodes)==len(new['nodes'])==len(old['nodes'])+len(TURNS)
    for n in old['nodes']:assert nodes.pop(identity(n))==n
    assert all(n['line']=='x x/' and len(n['wr'])==2 for n in nodes.values())
    bounds={n['board'][6:]:n for n in nodes.values()};assert set(bounds)==set(TURNS)
    return bounds

def decisions(root,game,t,rivers,route,opponents):
    rows=observations(root,game,t,rivers,route)
    turns={n['line']:n for n in game['nodes'] if len(n['board'])==8}
    foes=opponents&accepted(turns['x x/x'],game['hands'],'x')
    found={}
    for n in game['nodes']:
        public=n['board']
        if n['line']!=LINE or n['player']!=0:continue
        acts=rows[public]['displayed_check_hands']
        assert set(acts)<={HERO}
        if HERO not in acts:continue
        active={cardkey(h) for h,w in zip(game['hands'][1],n['w'][1],strict=True) if w>1e-4}
        held=public_cards(public+HERO);eligible=sorted(''.join(v) for v in foes&active if held.isdisjoint(v))
        if eligible:found[public]=eligible
    return rows,found

def run(a):
    solver=a.solver.resolve();py=solver/'postflop/py'
    git=lambda repo:subprocess.check_output(['git','-C',repo,'rev-parse','HEAD'],text=True).strip()
    assert sys.version_info[:2]==(3,11) and git(solver)==SOLVER
    if a.driver:assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver' and git(solver/'postflop/postflop-solver')==RUST
    assert (sha((py/'pipeline.py').read_bytes()),sha((py/'ranges.py').read_bytes()))==(PIPELINE,RANGES)
    poolraw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(poolraw)==POOL
    sys.path.insert(0,str(py));import pipeline,ranges
    pool=json.loads(poolraw)['NL2'];route_raw=subprocess.check_output(['node',ROUTE]);route=json.loads(route_raw)['229']
    model=read(Path('data/nl2_hu_multiboard_status_current.json'))['records'][MODEL]
    contract=read(Path('data/nl2_hu_verified_extensions.json'))['trainer_route_contract']['routes'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'],contract['seat'],contract['streets'])==(229,'SB3_BTN',0,['x x','x x',''])
    assert abs(90/21/model['assumed_model_node_spr']-1)<=.05
    old,job,template,origin=source(a.archive,ranges)
    static={}
    for t,expected in TURNS.items():
        cards,foes=gates(old,t,route);assert (len(foes),len(cards))==expected
        static[t]=dict(compatible_btn_hands=len(foes),rivers=cards)
    if a.preflight:print(json.dumps(dict(flop=FLOP,hero=HERO,original=origin,prequalified=static)));return
    out=a.output
    if a.driver:assert not out.exists() or not any(out.iterdir())
    else:assert (out/'proof.json').is_file()
    out.mkdir(parents=True,exist_ok=True)
    for name,raw in [('rendered-routes.json',route_raw),('original-b681.zip',a.archive.read_bytes())]:
        if a.driver:(out/name).write_bytes(raw)
        else:assert (out/name).read_bytes()==raw
    result=solve(out/'flop',job,a.driver);bounds=compare(old,result)
    report=dict(schema='NL2_B780_SB3_R229_ORIGINAL_DIAMOND_TURNS_V1',rank=229,model_id=MODEL,flop=FLOP,actor=0,line=LINE,hero=HERO,
                source=origin,solver=SOLVER,rust=RUST,pool_sha256=POOL,route_sha256=sha(route_raw),original_nodes_unchanged=len(old['nodes']),
                original_nodes_sha256=sha(compact(old['nodes'])),frozen_original_flop_menu='50% only, both seats',
                root_job_sha256=sha((out/'flop/job.json').read_bytes()),root_sha256=sha((out/'flop/result.json').read_bytes()),
                new_raw_boundary_sha256={t:sha(compact(n)) for t,n in bounds.items()},observed_private_hand_frequencies=False,
                turns=[],selected=None,locked_public_boards=0,joint_halfpot_assessed=0,halfpot_candidates=0)
    for t in TURNS:
        parent=bounds[t];cards,btn=gates(result,t,route,parent)
        entry=dict(turn=t,river_cards=cards,compatible_btn_hands=len(btn),policies={},common={})
        report['turns'].append(entry)
        if not cards:continue
        gto=dict(template,turn=t,extract=[dict(prefix=[],street=True)]+[dict(prefix=['x','x',r],street=True) for r in cards])
        for i,key in enumerate(('oop_w','ip_w')):gto[key]=[[h,w] for h,w in zip(result['hands'][i],parent['wr'][i],strict=True) if w>1e-4]
        paired={}
        for mode in ('gto',MODE):
            target=gto;applied=None
            if mode==MODE:
                target,rules=prepare_job(dict(source=dict(root=result,version='gto',manifest=dict(spot='SB3_BTN')),job=gto),MODE,pool,pipeline)
                target['out']='result.json';assert target['hero']==0 and target['locks']
            d=out/(t+'-'+mode);sub=solve(d,target,a.driver)
            assert (sub['flop'],sub['pot'],sub['stack'])==(FLOP,2100,9000) and 0<=sub['info']['gto_expl_pct']<=.5
            if mode==MODE:
                assert 0<=sub['info']['hero_gap_pct']<=.5
                applied=audit_patterns(sub,target,dict(locks=rules),pool,0)
                assert any(n>0 for k,n in applied['driver_tree_nodes'].items() if k in applied['marginal_targets'])
            else:assert not target.get('locks') and not sub['info'].get('lock_stats')
            rows,found=decisions(result,sub,t,cards,route,btn)
            paired[mode]=found
            entry['policies'][mode]=dict(job_sha256=sha((d/'job.json').read_bytes()),source_sha256=sha((d/'result.json').read_bytes()),
                applied_lock=applied,boards=rows,compatible_btn_by_public_board=found)
            if mode=='gto' and not found:break
            if mode==MODE:
                locked=[v['reach'] for v in rows.values()]
                joint=[r for r in locked if r['compatible_hole_card_pairs']>=r['strict_legal_combos']>0 and 'b50' in r['source_actions'] and r['b50'] is not None]
                report['locked_public_boards']+=len(locked);report['joint_halfpot_assessed']+=len(joint)
                report['halfpot_candidates']+=sum(bool(r['b50']['candidate']) for r in joint)
        if MODE in paired:
            for pub,foes in paired['gto'].items():
                common=sorted(set(foes)&set(paired[MODE].get(pub,[])))
                if common:
                    assert compatible(contract,dict(public_board=pub,actual_exact_action_line=LINE,acting_seat=0))
                    entry['common'][pub]=dict(sb=HERO,btn_hands=common)
            if entry['common']:
                report['selected']=dict(turn=t,public_board=min(entry['common']),**entry['common'][min(entry['common'])]);break
    report['positive_distinct_flops']=int(report['selected'] is not None)
    (out/'proof.json').write_bytes(json_bytes(report));print(json.dumps({k:report[k] for k in ('selected','positive_distinct_flops','locked_public_boards','joint_halfpot_assessed','halfpot_candidates')}))

if __name__=='__main__':
    c=argparse.ArgumentParser(description=__doc__)
    for name in ('solver','archive','output'):c.add_argument('--'+name,type=Path,required=True)
    c.add_argument('--preflight',action='store_true');c.add_argument('--driver',type=Path);run(c.parse_args())
