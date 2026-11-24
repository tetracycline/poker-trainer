"""Read-only replay of the named B705 locked turn policy; never runs a solver."""
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path
from zipfile import ZipFile

from hu_sequential_cfr_reach import accepted

RUN=45320372683
HEAD='610d867a828115e80285e5aebe49fc0059c788c3'
SOLVER='abe310c3aad02dd4a7c77fb2831801fd490cf51b'
PINS={'7h5d2c':(14887247264,'aa0df731ad3f1c02f5f6c5e040625dcdabb35395842a1b15ca0bcb02609b8347'),
      '8c6h3d':(14887396304,'4b2ef1bdbbcce854c7537e668fcd9e9fc8daa7bed7641876c9da14a765fa430d'),
      '9d6d4c':(14888170203,'74dbd57130ba0fd4ee0cbd188d5ef4b6e8351e429020fb3ca539de43e6dc0185')}
TRAINER_SOURCES={'tools/hu_sequential_cfr_reach.py':'f26df926c088e5b4117bb911956cbc5031e2458d',
                 'tools/solve_hu_multiboard_100bb.py':'c9085b34ffd2aa1dfc473949795cf54830a1372a',
                 'nl2_pool_rate_scope.js':'9b9297e59d59ea7bc3542fef47a3e4f5689d7df5'}
SOLVER_SOURCES={'postflop/pfdriver/src/main.rs':'815164ee87681002362bb02135e20042393b279e',
                'postflop/py/locks.py':'8ad28f0b01931cb8e189f91b9fb6313a02591027',
                'inputs/pool_stats.json':'9098b02cd9426b470ddcf22e1a4a48420bdaa262',
                'gto_check/pool_post.py':'fdce1b35f69d96edb0ebd39a5a83ce23d9d77c6a',
                'read_v1/engine.py':'9b0291b5b5def4c48a567ee283381fefd3c8af5e'}

def git_blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def sha(b):return hashlib.sha256(b).hexdigest()

def probability_rows(node,hands):
    who=node['player'];nh=len(hands[who]);acts=node['acts']
    assert len(node['strat'])==nh*len(acts)
    for i,w in enumerate(node['w'][who]):
        if w<=1e-4:continue
        v=[max(0.,node['strat'][j*nh+i]) for j in range(len(acts))];den=sum(v)
        if den>0:yield {a:x/den for a,x in zip(acts,v,strict=True)}

def run(a):
    assert subprocess.check_output(['git','-C',a.solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    for names,base in [(TRAINER_SOURCES,Path.cwd()),(SOLVER_SOURCES,a.solver)]:
        for path,blob in names.items():assert git_blob((base/path).read_bytes())==blob,path
    pool=json.loads((a.solver/'inputs/pool_stats.json').read_bytes())['NL2']['postflop_HU']
    assert pool['SRP_turn_stab_ip_after_pfr_checks']=={'n':38412,'pct':34.5}
    assert pool['SRP_probe']=={'n':133319,'pct':37.5}
    assert pool['SRP_float_bet_when_pfr_checks_oop']=={'n':108612,'pct':40.0}
    rows=[];all_zero=0
    for flop,(aid,digest) in PINS.items():
        paths=[p for p in [a.archives/f'{aid}.zip',a.archives/f'NL2_B705_R76_{flop.upper()}.zip'] if p.is_file()]
        assert len(paths)==1 and sha(paths[0].read_bytes())==digest
        with ZipFile(paths[0]) as z:
            proof=json.loads(z.read('proof.json'));origin=proof['root_origin']
            assert (proof['rank'],proof['spot'],proof['actor'],proof['flop'],proof['line'])==(76,'SB_BB',0,flop,'x x/x b50 c/')
            assert (origin['resume_run'],origin['resume_head'],proof['flop_native_solves_repeated'])==(RUN,HEAD,0)
            root=json.loads(z.read('flop/result.json'));assert sha(z.read('flop/result.json'))==origin['original_root_result_sha256']
            assert (root['flop'],root['pot'],root['stack'])==(flop,600,9700)
            f={n['line']:n for n in root['nodes'] if len(n['board'])==6}
            base=[accepted(f[''],root['hands'],'x'),accepted(f['x'],root['hands'],'x')]
            for t in proof['turns']:
                if not t['paired_policies']:continue
                turn=t['turn'];paired={}
                assert t['parent_gate']['compatible_displayed_parent_hands']>0
                for version in ['gto','exp_oop']:
                    g=version=='gto';pref='gto' if g else 'nl2';prefix=f'{turn}-{version}/'
                    jr=z.read(prefix+'job.json');rr=z.read(prefix+'result.json')
                    assert sha(jr)==t[pref+'_job_sha256'] and sha(rr)==t[pref+'_source_sha256']
                    job=json.loads(jr);sub=json.loads(rr);stats=sub['info'].get('lock_stats')
                    assert 0<=sub['info']['gto_expl_pct']<=.5 and (not stats)==g
                    if not g:
                        assert job['hero']==0 and 0<=sub['info']['hero_gap_pct']<=.5
                        matched=next(r for r in job['locks'] if re.search(r['pat'],'x x/x'))
                        assert matched=={'pat':'.*/x$','bet':.45,'sizes':[[33,.35],[50,.35],[75,.2],[100,.1]]}
                        assert stats['.*/x$']['nodes']>0 and abs(stats['.*/x$']['agg']-.45)<.001
                    tree={n['line']:n for n in sub['nodes'] if len(n['board'])==8}
                    opp=tree['x x/x'];assert (opp['player'],opp['acts'])==(1,['x','b33','b50','b75','b100'])
                    probs=list(probability_rows(opp,sub['hands']));seat0=set(base[0]);seat1=set(base[1]);step=[]
                    for line,act,seat in [('x x/','x',0),('x x/x','b50',1),('x x/x b50','c',0)]:
                        n=tree[line];assert n['player']==seat
                        handset=accepted(n,sub['hands'],act);keep=seat1 if seat else seat0;keep.intersection_update(handset)
                        step.append({'action':act,'seat':seat,'accepted_at_node':len(handset),'after_own_prior_actions':len(keep)})
                    if not g:
                        assert all(v['b33']==v['b50'] and v['b50']<.4 for v in probs)
                        assert not seat1 and step[1]['accepted_at_node']==0
                        observations=t['nl2_boards'];assert len(observations)==16
                        assert all(x['reach']['strict_legal_combos']==0 and x['reach']['compatible_hole_card_pairs']==0 and x['displayed_hands']==0 for x in observations)
                        all_zero+=len(observations)
                    paired[version]=dict(job_sha256=sha(jr),result_sha256=sha(rr),steps=step,
                            opponent_weight_positive_hands=len(probs),max_opponent_b50_probability=max((v['b50'] for v in probs),default=None),
                            river_rows=len(t[pref+'_boards']),river_rows_with_displayed_hands=sum(x['displayed_hands']>0 for x in t[pref+'_boards']))
                rows.append(dict(flop=flop,turn=turn,artifact_id=aid,archive_sha256=digest,policies=paired))
    assert len(rows)==7 and all_zero==112
    assert sum(x['policies']['exp_oop']['steps'][0]['accepted_at_node']==0 for x in rows)==6
    assert all(x['policies']['gto']['steps'][1]['accepted_at_node']>0 for x in rows)
    assert next(x for x in rows if (x['flop'],x['turn'])==('9d6d4c','5c'))['policies']['exp_oop']['steps'][2]['after_own_prior_actions']==64
    result=dict(schema='NL2_R76_B705_ORIGINAL_SIZE_GATE_DIAGNOSIS_V1',source_run=RUN,source_head=HEAD,solver=SOLVER,
        trainer_source_git_blobs=TRAINER_SOURCES,solver_source_git_blobs=SOLVER_SOURCES,paired_turns=rows,zero_locked_river_nodes=all_zero,
        model='ln-opfr-r_model-1phsqr4',required_line='x x/x b50 c/',scope='B705 fixed four-size menu and disclosed fallback only',
        matched_rule={'pattern':'.*/x$','n':0,'bet':.45,'per_betting_hand_size_fractions':[[33,.35],[50,.35],[75,.2],[100,.1]],'empirical_private_hand_evidence':False},
        conclusion='With this exact rule/menu b50 equals b33 for every reached hand and is below 40%. b33 precedes b50 under first-maximum tie selection. No board change can admit b50 under the unchanged locked policy and strict gate. This says nothing about actual NL2 players never betting half-pot.',
        nearby_pool_scopes={'SRP_turn_stab_ip_after_pfr_checks':'34.5% of 38,412 after calling the flop c-bet (different history; no size split)',
        'SRP_probe':'37.5% of 133,319: OOP caller against IP PFR (different seats; no size split)',
        'SRP_float_bet_when_pfr_checks_oop':'40.0% of 108,612: flop, not turn; no size split',
        'gto_check/pool_post.py, read_v1/engine.py':'SRP source filters exclude the SB opener'},
        original_flops_repeated=0,new_solves=0,new_node_locked_boards=0,new_medium_assessed_boards=0,certification_changes=0)
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archives',type=Path,required=True);p.add_argument('--solver',type=Path,required=True);run(p.parse_args())
