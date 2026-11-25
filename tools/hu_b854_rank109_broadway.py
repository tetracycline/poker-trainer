"""B854: fresh UTG monotone broadway roots, exact two-policy physical-pair gate.
No prior native jobs are rerun. Replay uses the saved arrays only.
"""
import argparse, itertools, json, subprocess, sys
from pathlib import Path
from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import PIPELINE, POOL, RANGES, proof
from hu_b568_caller_rivers import hand_cell
from hu_b580_rank27_rivers import suit_isomorphism_class
from hu_b637_rank57 import solve
from hu_b667_rank109_monotone import MODEL, LINE, template_jobs, turn_job
from hu_b696_turn_call_rivers import parent_candidates
from hu_checked_gto_boundary import prepare_job
from hu_sequential_cfr_reach import accepted, cardkey, game_reach
from solve_hu_missing_branches import EXTRA_SPOTS

CASES={'AcQcJc': ('4h','7s'), 'KdJdTd': ('3c','6h')}
OLD=('Ks8s3s','Qh7h2h','Ad8d4d','Jc6c2c','8h6h2d','9c7c4d','Jh8h3d','Td9h5c',
     'Jd7d3d','Th6h2h','Ts7s2s','Qd8d3d','Jc7c4c','8h6h2h')
DECK=[r+s for r in '23456789TJQKA' for s in 'cdhs']
def cards(board):return {board[i:i+2] for i in range(0,len(board),2)}
def h169(pair):
    a,b=sorted(pair,key=lambda c:'23456789TJQKA'.index(c[0]),reverse=True)
    return a[0]+b[0]+('' if a[0]==b[0] else 's' if a[1]==b[1] else 'o')
def preflight(template, flop, route, pinned_ranges):
    # B854 failed before invoking any native job: this manifest records provenance,
    # not oop_169/ip_169 dictionaries. Use the exact serialized native input.
    p=template['manifest']['preflop_ranges']
    assert p['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
    job=template['root_job']
    assert (job['oop'],job['ip'])==pinned_ranges
    def weights(s):
        rows=[x.split(':') for x in s.split(',') if x]
        assert rows and all(len(row)==2 for row in rows)
        values={k:float(v) for k,v in rows}
        assert len(values)==len(rows) and all(0<v<=1 for v in values.values())
        return values
    oop,ip=map(weights,pinned_ranges)
    assert suit_isomorphism_class(flop) not in {suit_isomorphism_class(x) for x in OLD}
    out={}
    for t in CASES[flop]:
        dead=cards(flop+t)
        pairs=[tuple(sorted(h)) for h in itertools.combinations([c for c in DECK if c not in dead],2)]
        hero=[h for h in pairs if oop.get(h169(h),0)>0
              and hand_cell(''.join(h),flop)[0] in route['flop']
              and hand_cell(''.join(h),flop+t)[0] in route['turn']]
        opp=[v for v in pairs if ip.get(h169(v),0)>0]
        witness=None
        for h in hero:
            for r in DECK:
                if r in dead or r in h or route['river'].get(hand_cell(''.join(h),flop+t+r)[0])!='下注 ¾':continue
                v=next((v for v in opp if r not in v and set(h).isdisjoint(v)),None)
                if v:
                    witness=dict(hero=h,opponent=v,river=r);break
            if witness:break
        out[t]=witness
    return out

def observe(root, sub, turn, rivers, route):
    sub.update(line0='x x',turn=turn,rivers=rivers)
    assert (sub['flop'],sub['pot'],sub['stack'])==(root['flop'],650,9750)
    def one(nodes,line):return next(n for n in nodes if n['line']==line)
    rootnodes=[n for n in root['nodes'] if len(n['board'])==6]
    a,b=one(rootnodes,''),one(rootnodes,'x')
    assert (a['player'],b['player'],a['pot'],b['pot'],a['bets'],b['bets'])==(0,1,650,650,[0,0],[0,0])
    prior=[accepted(a,root['hands'],'x'),accepted(b,root['hands'],'x')]
    tnodes=[n for n in sub['nodes'] if len(n['board'])==8]
    a,b=one(tnodes,'x x/'),one(tnodes,'x x/b75')
    assert (a['player'],b['player'],a['pot'],b['pot'],a['bets'],b['bets'])==(0,1,650,1138,[0,0],[488,0])
    prior[0]&=accepted(a,sub['hands'],'b75');prior[1]&=accepted(b,sub['hands'],'c')
    masks=game_reach(root,sub)[0];out={}
    for n in sub['nodes']:
        if n['line']!=LINE:continue
        board=n['board'];dead=cards(board)
        assert len(dead)==5 and board[6:8]==turn and (n['player'],n['pot'],n['bets'])==(0,1626,[488,488])
        assert 'b50' in n['acts'] and 'b75' in n['acts']
        live=[{cardkey(h) for h,w in zip(sub['hands'][i],n['w'][i],strict=True)
               if w>1e-4 and dead.isdisjoint(cardkey(h))}&prior[i] for i in (0,1)]
        shown={h for h in live[0]&accepted(n,sub['hands'],'b75')
               if hand_cell(''.join(h),board[:6])[0] in route['flop']
               and hand_cell(''.join(h),board[:8])[0] in route['turn']
               and route['river'].get(hand_cell(''.join(h),board)[0])=='下注 ¾'}
        out[board]=dict(reach=proof(root,sub,n,masks),hero=sorted(live[0]),opp=sorted(live[1]),shown=sorted(shown))
    assert {b[-2:] for b in out}==set(rivers)
    return out

def witness(hero,opp):
    for h in sorted(hero):
        for v in sorted(opp):
            if set(h).isdisjoint(v):return [h,v]
    return None
def common(g,e,display=False):
    key='shown' if display else 'hero'
    return witness(set(g[key])&set(e[key]),set(g['opp'])&set(e['opp']))
def run(a):
    solver=a.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    for path,pin in [('postflop/py/pipeline.py',PIPELINE),('postflop/py/ranges.py',RANGES),('inputs/pool_stats.json',POOL)]:
        assert sha((solver/path).read_bytes())==pin
    if a.driver:
        assert a.driver.resolve()==solver/'postflop/pfdriver/target/release/pfdriver'
        assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
    sys.path.insert(0,str(solver/'postflop/py'));import pipeline,ranges
    pipeline.SPOTS.update(EXTRA_SPOTS);ranges.SPOTS.update(EXTRA_SPOTS)
    pool=json.loads((solver/'inputs/pool_stats.json').read_bytes())['NL2']
    route_raw=subprocess.check_output(['node','tools/hu_b619_utg_routes.cjs','619'])
    route=json.loads(route_raw)['109']
    assert route['id']==MODEL and route['turn']==['mono:0'] and route['river']=={'mono:0':'下注 ¾'}
    reg=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert (reg['frequency_rank'],reg['solver_profile'],reg['assumed_model_node_spr'],reg['label'])==(109,'UTG_CO',5.7,'APPROX')
    assert abs(9262/1626/5.7-1)<.05
    template=template_jobs();flop=a.flop
    pinned_ranges=tuple(ranges.to_str(w) for w in ranges.ranges('UTG_CO','gto'))
    pre=preflight(template,flop,route,pinned_ranges)
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    report=dict(schema='NL2_B854_R109_NEW_BROADWAY_MONOTONE_TWO_SEAT_V1',rank=109,flop=flop,
      model_id=MODEL,actor=0,spot='UTG_CO',line=LINE,solver=SOLVER,rust=RUST,pool_sha256=POOL,
      route_sha256=sha(route_raw),preflight=pre,turns=[],selected=None,native_flop_solves=0,
      locked_public_boards=0,joint_halfpot_assessed=0,nonpolarized_candidates=0)
    def native(folder,job):
        p=out/folder
        result=solve(p,job,None if (p/'result.json').exists() else a.driver)
        assert 0<=result['info']['gto_expl_pct']<=.5
        return result
    valid=[t for t in CASES[flop] if pre[t]]
    if valid:
        job=dict(template['root_job'],flop=flop,out='result.json',extract=[dict(prefix=[],street=True)]+[
            dict(prefix=['x','x',t],street=False,raw=True) for t in valid])
        assert (job['oop'],job['ip'])==tuple(ranges.to_str(w) for w in ranges.ranges('UTG_CO','gto'))
        assert (job['pot'],job['stack'],job['rake_rate'],job['rake_cap'])==(650,9750,.05,1000)
        assert not job.get('locks') and job.get('hero') is None
        root=native('flop',job);assert not root['info'].get('lock_stats')
        report['native_flop_solves']=1
        public=next(n['board'] for n in root['nodes'] if n['line']=='')
        assert cards(public)==cards(flop)
        for t in valid:
            gate,rivers=parent_candidates(dict(root,flop=public),t,dict(pot=650,actor=0,routes=route))
            item=dict(turn=t,parent_gate=gate,gto={},nl2={},common_displayed_pairs={},common_prior_pairs={})
            report['turns'].append(item)
            if not rivers:continue
            p=next(n for n in root['nodes'] if n['line']=='x x/' and n['board'].endswith(t))
            gj=turn_job(template,root,p,rivers)
            gj.update(turn_oop='33%,50%,75%,100%',turn_ip='33%,50%,75%,100%',
                extract=[dict(prefix=[],street=True)]+[dict(prefix=['b75','c',r],street=False) for r in rivers])
            g=native(t+'-gto',gj);assert not g['info'].get('lock_stats')
            item['gto']=observe(root,g,t,rivers,route)
            if not any(witness(x['shown'],x['opp']) for x in item['gto'].values()):continue
            ej,rules=prepare_job(dict(source=dict(version='gto',root=root,manifest=dict(spot='UTG_CO',pot_family='SRP')),job=gj),'exp_oop',pool,pipeline)
            ej['out']='result.json';assert ej['hero']==0 and ej['locks']
            e=native(t+'-exp_oop',ej);assert e['hands']==g['hands'] and 0<=e['info']['hero_gap_pct']<=.5
            app=audit_patterns(e,ej,dict(locks=rules),pool,0)
            assert any(v>0 for k,v in app['driver_tree_nodes'].items() if k in app['marginal_targets'])
            item['measured_lock_application']=app;item['nl2']=observe(root,e,t,rivers,route)
            for b,after in sorted(item['nl2'].items()):
                before=item['gto'][b];report['locked_public_boards']+=1
                both=common(before,after)
                if both:
                    assert all(x['reach']['compatible_hole_card_pairs']>0 and x['reach']['b50'] is not None for x in (before,after))
                    item['common_prior_pairs'][b]=both;report['joint_halfpot_assessed']+=1
                    report['nonpolarized_candidates']+=int(after['reach']['b50']['candidate'])
                visible=common(before,after,True)
                if visible:
                    item['common_displayed_pairs'][b]=visible
                    if report['selected'] is None:report['selected']=dict(board=b,turn=t,physical_pair=visible)
    report['positive_distinct_flops']=int(report['selected'] is not None)
    report['native_files']={str(p.relative_to(out)):sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='proof.json'}
    (out/'proof.json').write_bytes(json_bytes(report))
    print(json.dumps({k:report[k] for k in ('flop','native_flop_solves','positive_distinct_flops','locked_public_boards','joint_halfpot_assessed','nonpolarized_candidates')}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--solver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--driver',type=Path);p.add_argument('--flop',choices=CASES,required=True);run(p.parse_args())
