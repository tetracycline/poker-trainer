"""Reuse authentic B524 flop boundaries; resolve only unexported BTN barrel rivers for ranks104/105."""
import argparse, base64, json, subprocess, sys, tempfile
from copy import deepcopy
from pathlib import Path
from hu_b463_rank45_gate import RUST,SOLVER
from hu_b467_river_source_gate import compact,json_bytes,sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE,POOL,RANGES,proof
from hu_b568_caller_rivers import hand_cell
from hu_b637_rank57 import solve
from hu_checked_gto_boundary import load_original,prepare_job
from hu_sequential_cfr_reach import accepted,cardkey,game_reach

RUN=45118153398;HEAD='d1b22cd54e8c5391f2ee6d9411488923979ac797'
CASES={'6s5h4d':('6h',14792976867,'df887d5566b9f99505a5310b3e236205c6bfbd55b19013266fbf3e91071a442b'),
       '7d5c4c':('9c',14792312789,'8aeec8c25159cde3db0b15046bddee1bd1fa3f71b4b92851b25918879c392852'),
       '6d4c3h':('Kd',14793340092,'917c6f833fb3add6a982efa1bf6d788420433a990ba2448afeb10491cd3f24ea')}
TARGETS={'104':('ln-ipfr-r_model-1k916pi',75,2750,8650,3.045),'105':('ln-ipfr-r_model-1v72njh',50,2200,8925,3.932)}
ACT={'過':'x','下注 ½':'b50','下注 ¾':'b75'};DECK=[r+s for r in '23456789TJQKA' for s in 'cdhs']
def cards(s):return {s[i:i+2] for i in range(0,len(s),2)}

def boundary(flop,receipt,pipeline,ranges):
    turn,aid,digest=CASES[flop];archive=Path('data/solver_evidence')/f'NL2_B524_R8_{flop.upper()}_GTO.zip'
    name=f'B524-R8-{flop}-gto';meta=json.loads(receipt.read_bytes());assert meta['workflow_run']['head_repository_id']==1438346845
    pin={'name':name,'run':RUN,'head':HEAD,'sha256':digest};assert meta['id']==aid
    with tempfile.TemporaryDirectory() as tmp:
        d=Path(tmp);(d/f'{aid}.zip').symlink_to(archive.resolve());(d/f'{aid}.json').symlink_to(receipt.resolve())
        orig=load_original(d,aid,pin,'BTN_BB',flop,turn,'gto',pot=550,stack=9750,flop_line='b50 c',pipeline=pipeline,ranges=ranges)
    g=orig['source']['root'];old=orig['source']['subgame'];j=orig['job'];b=orig['public']
    assert ranges.SPOTS['BTN_BB']==dict(oop='BB',ip='BTN',oopc=[('BTNopen>BB','call')],ipc=[('BTNrfi','open')],pot=5.5,stack=97.5,pfr='ip',kind='SRP')
    assert cards(b[:6])==cards(flop) and b[6:]==turn and len(cards(b))==4
    assert (g['pot'],g['stack'],old['pot'],old['stack'])==(550,9750,1100,9475)
    assert j['turn_ip']=='50%,100%' and not any(n['line'].startswith(('b50 c/x b50 c/','b50 c/x b75 c/')) for n in old['nodes'])
    return orig

def parent_gate(orig,c):
    root=orig['source']['root'];b=orig['public'];f=root['flop'];route=c['routes'];known=cards(b)
    nodes={n['line']:n for n in root['nodes'] if len(n['board'])==6};a=nodes[''];response=nodes['b50']
    assert cards(a['board'])==cards(response['board'])==cards(f) and (a['player'],a['pot'],a['bets'])==(0,550,[0,0])
    assert (response['player'],response['pot'],response['bets'])==(1,825,[275,0])
    parent,=[n for n in root['nodes'] if (n['board'],n['line'])==(b,'b50 c/')]
    assert (parent['player'],parent['pot'],parent['bets'])==(0,1100,[275,275])
    strict=[accepted(a,root['hands'],'b50'),accepted(response,root['hands'],'c')]
    alive=[ss&{cardkey(h) for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4 and known.isdisjoint(cardkey(h))} for seat,ss in enumerate(strict)]
    heroes=sorted(h for h in alive[1] if hand_cell(''.join(h),b[:6])[0] in route['flop'] and hand_cell(''.join(h),b)[0] in route['turn'] and any(set(h).isdisjoint(v) for v in alive[0]))
    feasible={}
    for r in DECK:
        if r in known:continue
        for h in heroes:
            if r in h or hand_cell(''.join(h),b+r)[0] not in route['river']:continue
            opp=next((v for v in sorted(alive[0]) if r not in v and set(h).isdisjoint(v)),None)
            if opp:
                feasible[r]=dict(hero=''.join(h),opponent=''.join(opp));break
    rs=list(feasible);keep=rs if len(rs)<=16 else [rs[round(i*(len(rs)-1)/15)] for i in range(16)]
    return dict(flop= f,public_turn=b,root_accepted=[len(x) for x in strict],positive_boundary_by_seat=[len(x) for x in alive],
                compatible_displayed_hero_hands=len(heroes),candidate_river_count=len(rs),river_extracts=keep,static_witnesses={r:feasible[r] for r in keep})

def turn_job(orig,config,gates):
    j=deepcopy(orig['job']);j.update(out='result.json',iters=2450,target_pct=.4,rank_pct=.4,compress=False,
       turn_oop='33%,50%,75%,100%',turn_ip='33%,50%,75%,100%',river_oop='50%,75%,100%,a',river_ip='50%,75%,100%,a',
       river_donk='50%,75%,100%',extract=[dict(prefix=[],street=True)])
    for k,c in config.items():
        for r in gates[k]['river_extracts']:
            j['extract'].extend([dict(prefix=['x','b'+str(c['pct']),'c',r],street=False),dict(prefix=['x','b'+str(c['pct']),'c',r,'x'],street=False)])
    return j

def observations(orig,game,config,gates):
    root=orig['source']['root'];pub=orig['public'];game.update(line0='b50 c',turn=pub[-2:]);masks=game_reach(root,game)[0];out={}
    for k,c in config.items():
        name=c['line'];rs=gates[k]['river_extracts'];idx=[n for n in game['nodes'] if (n['line'],n['player'])==(name,1)]
        assert {n['board'][-2:] for n in idx}==set(rs) and len(idx)==len(rs)
        records={};bet=1100*c['pct']//100
        for n in idx:
            b=n['board'];assert b[:8]==pub and (n['pot'],n['bets'])==(c['river_pot'],[bet,bet]) and game['stack']-bet==c['river_stack']
            first,=[p for p in game['nodes'] if (p['board'],p['line'],p['player'])==(b,name[:-1],0)]
            assert 'x' in first['acts'] and any(a.startswith('b') for a in first['acts'])
            row=proof(root,game,n,masks);mask=base64.b64decode(row['compatible_action_mask_b64'],validate=True);w={}
            for hand,ab in zip(game['hands'][1],mask,strict=True):
                if not ab:continue
                h=''.join(cardkey(hand));cs=[hand_cell(h,b[:length]) for length in (6,8,10)]
                if any(cc[0] not in c['routes'][street] for cc,street in zip(cs,('flop','turn','river'),strict=True)):continue
                label=c['routes']['river'][cs[-1][0]];act=ACT[label]
                if act in n['acts'] and ab & (1<<n['acts'].index(act)):w[h]=dict(classes=[v[1] for v in cs],displayed=label,accepted_mask=ab)
            records[b]=dict(hands=w,reach=row)
        out[k]=records
    return out

def safe_solve(folder,job,driver):
    return solve(folder,job,None if (folder/'result.json').is_file() else driver)

def run(a):
    solver=a.solver.resolve();assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    assert sha((solver/'postflop/py/pipeline.py').read_bytes())==PIPELINE and sha((solver/'postflop/py/ranges.py').read_bytes())==RANGES
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
    sys.path.insert(0,str(solver/'postflop/py'));import pipeline,ranges
    poolraw=(solver/'inputs/pool_stats.json').read_bytes();assert sha(poolraw)==POOL;pool=json.loads(poolraw)['NL2']
    turn,aid,_=CASES[a.flop];raw=a.routes.read_bytes();c=json.loads(raw);assert set(c)==set(TARGETS)
    for k,(mid,pct,pot,stack,spr) in TARGETS.items():
        r=c[k];assert (r['id'],r['pct'],r['river_pot'],r['river_stack'],r['spr'],r['actor'],r['spot'],r['line'])==(mid,pct,pot,stack,spr,1,'BTN_BB',f'b50 c/x b{pct} c/x')
        assert abs(stack/pot/spr-1)<=.05
    orig=boundary(a.flop,a.receipts/f'{aid}.json',pipeline,ranges);gates={k:parent_gate(orig,v) for k,v in c.items()};assert gates['105']['river_extracts']
    assert bool(gates['104']['river_extracts'])==(a.flop!='6d4c3h')
    brief={k:dict(hands=v['compatible_displayed_hero_hands'],rivers=len(v['river_extracts'])) for k,v in gates.items()}
    if a.preflight:print(json.dumps(dict(flop=a.flop,turn=turn,rank_preflight=brief)));return
    assert a.run>0 and len(a.head)==40 and all(ch in '0123456789abcdef' for ch in a.head)
    a.output.mkdir(exist_ok=True,parents=True);g=turn_job(orig,c,gates);source=orig['source'];before=safe_solve(a.output/'gto',g,a.driver)
    assert (before['flop'],before['pot'],before['stack'])==(a.flop,1100,9475) and 0<=before['info']['gto_expl_pct']<=.5 and not before['info'].get('lock_stats')
    initial=observations(orig,before,c,gates);paired=any(v['hands'] for group in initial.values() for v in group.values());after={k:{} for k in c};measured=None;nl2_job_sha=None;nl2_raw_sha=None
    if paired:
        lock,rules=prepare_job(dict(source=source,job=g),'exp_ip',pool,pipeline);lock['out']='result.json';assert lock['hero']==1
        exp=safe_solve(a.output/'exp_ip',lock,a.driver);assert all(exp[x]==before[x] for x in ('flop','pot','stack','hands'))
        assert 0<=exp['info']['gto_expl_pct']<=.5 and 0<=exp['info']['hero_gap_pct']<=.5 and exp['info']['lock_stats']
        measured=audit_patterns(exp,lock,dict(locks=rules),pool,1);assert any(v>0 for k,v in measured['driver_tree_nodes'].items() if k in measured['marginal_targets'])
        after=observations(orig,exp,c,gates);nl2_job_sha=sha(compact(lock));nl2_raw_sha=sha((a.output/'exp_ip/result.json').read_bytes())
    groups={}
    for k,v in initial.items():
        common=[]
        for board,entry in sorted(v.items()):
            if board in after[k]:
                other=after[k][board];hands=sorted(entry['hands'].keys()&other['hands'].keys())
                if hands:common.append(dict(public_board=board,hands=hands,gto_witnesses={h:entry['hands'][h] for h in hands},nl2_witnesses={h:other['hands'][h] for h in hands},gto_b50=entry['reach']['b50'],nl2_b50=other['reach']['b50']))
        def report(rows):return [dict(public_board=b,displayed_hands=len(x['hands']),reach=x['reach']) for b,x in sorted(rows.items())]
        groups[k]=dict(model_id=c[k]['id'],line=c[k]['line'],parent_gate=gates[k],gto_boards=report(v),nl2_boards=report(after[k]),common=common,selected=common[0] if common else None,positive_distinct_flops=int(bool(common)))
    report=dict(schema='NL2_B713_FROZEN_B524_BTN_BARREL_RIVERS_V1',source_run=a.run,source_head=a.head,spot='BTN_BB',actor=1,flop=a.flop,turn=turn,root_pin=orig['identity'],root_run=RUN,root_head=HEAD,
        solver=SOLVER,rust=RUST,pipeline_sha256=PIPELINE,ranges_sha256=RANGES,pool_sha256=POOL,route_sha256=sha(raw),flop_native_solves_repeated=0,
        gto_job_sha256=sha(compact(g)),gto_source_sha256=sha((a.output/'gto/result.json').read_bytes()),nl2_job_sha256=nl2_job_sha,nl2_source_sha256=nl2_raw_sha,
        actor_lock_solved=paired,measured_lock_application=measured,scope='Original B524 GTO flop frozen; new turn and river GTO plus actor-matched partial NL2 marginal locks. No empirical per-hole-card data.',groups=groups,not_a_certification=True)
    (a.output/'rendered-routes.json').write_bytes(raw);(a.output/'proof.json').write_bytes(json_bytes(report));print(json.dumps({k:v['positive_distinct_flops'] for k,v in groups.items()}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for f in ('solver','routes','receipts','output'):p.add_argument('--'+f,type=Path,required=True)
    p.add_argument('--flop',choices=CASES,required=True);p.add_argument('--driver',type=Path);p.add_argument('--preflight',action='store_true');p.add_argument('--run',type=int,default=0);p.add_argument('--head',default='');run(p.parse_args())
