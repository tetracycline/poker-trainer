#!/usr/bin/env python3
"""Independent authenticity/lineage gate for ISO/LMP NL2 marginal-locked CFR.
Not a generic MODEL certificate. Unmatched actions remain unlocked.
"""
import argparse,collections,hashlib,json,pathlib

EXPECTED={'ISO_BTN_CO':(9.5,96.0,'SRP'),'LMP_CO_BB':(2.5,99.0,'limped')}
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
    return h.hexdigest()
def verify(root,solver):
    poolpath=solver/'inputs/pool_stats.json'
    pool=json.loads(poolpath.read_text())['NL2']['HU_facing_bet']
    out=[];errors=[]
    for artifact in sorted(root.iterdir()):
        if not artifact.is_dir() or not artifact.name.startswith('nl2-stage2-assumed-locked-'):continue
        try:
            manifests=list((artifact/'evidence').glob('*.json'))
            if len(manifests)!=1:raise ValueError('Expected exactly one provenance manifest')
            m=json.loads(manifests[0].read_text())
            spot=m['spot'];version=m['version']
            if spot not in EXPECTED or version not in ('exp_ip','exp_oop'):raise ValueError('Invalid spot/version')
            if spot not in artifact.name or version not in artifact.name:raise ValueError('Artifact identity mismatch')
            pot,stack,potgroup=EXPECTED[spot]
            if m['schema']!='HU_ASSUMED_NL2_AGGREGATE_LOCKED_CFR_V1' or not m['not_certified_generic_model']:
                raise ValueError('Missing explicit generic no-CERT gate')
            if len(m['oop_class_weights'])!=169 or len(m['ip_class_weights'])!=169:
                raise ValueError('Invalid 169 class preflop ranges')
            if abs(m['root_pot_bb']-pot)>1e-6 or abs(m['root_stack_bb']-stack)>1e-6:
                raise ValueError('Wrong pot/stack for frozen profile')
            if m['pool_sha256']!=sha(poolpath):raise ValueError('Measured pool source SHA mismatch')
            expected_stats=collections.Counter()
            for p in m['matched_aggregate_lock_patterns']:
                if p['n']<500 or p['scope']!='ACTUAL_AGGREGATE_NOT_HISTORY_OR_COMBO_CONDITIONAL':
                    raise ValueError('Untraceable pooled observation')
                st=p['street'];kind='facing_raise' if p['src'].endswith('bettor_vs_raise') else 'facing_bet'
                raw=pool[str(st)]['bettor_vs_raise' if kind=='facing_raise' else 'by_pot'][potgroup] if kind=='facing_bet' else pool[str(st)]['bettor_vs_raise']
                if raw['n']!=p['n'] or abs(raw['fold']/100-p['fold'])>1e-8 or abs(raw['raise']/100-p['raise_'])>1e-8:
                    raise ValueError('Incorrect aggregate NL2 source statistic for '+p['pat'])
                expected_stats[(st,kind)]+=1
            if len(expected_stats)!=6:raise ValueError('Not all pot/street sources accounted for')
            if m['failures']:raise ValueError('Solver error '+str(m['failures']))
            if not m['results']:raise ValueError('No successful multi-street solver result')
            flopfile=artifact/'solver/postflop/out'/spot/version/(m['flop']+'.json')
            fr=json.loads(flopfile.read_text())
            if fr['pot']!=round(100*pot) or fr['stack']!=round(100*stack):
                raise ValueError('Actual root CFR pot/stack mismatch')
            cases=[]
            for case in m['results']:
                rawfile=artifact/'solver/postflop'/case['subgame_path']
                if sha(rawfile)!=case['subgame_sha256']:raise ValueError('Raw CFR SHA mismatch')
                data=json.loads(rawfile.read_text())
                if (data.get('flop'),data.get('line0'),data.get('turn'))!=(case['flop'],case['line'],case['turn']):
                    raise ValueError('Flop/turn/actions do not match source')
                parent=next((n for n in fr['nodes'] if n['line']==case['line']+'/' and n['board'][-2:]==case['turn']),None)
                if parent is None:raise ValueError('No actual action-line parent')
                spr=(fr['stack']-max(parent['bets']))/parent['pot']
                if abs(spr-case['parent_spr'])>1e-5:raise ValueError('Parent SPR incorrect')
                info=data.get('info',{})
                if float(info.get('gto_expl_pct',float('inf')))>0.5 or float(info.get('hero_gap_pct',float('inf')))>0.5:
                    raise ValueError('Locked CFR convergence gate failed')
                if not case['matched_patterns']:raise ValueError('No NL2 frequency lock was applied in source subgame')
                river_nodes=0;reachable=0
                for node in data['nodes']:
                    if len(node['board'])==10:river_nodes+=1
                    h=data['hands'][node['player']]
                    if len(node['strat'])!=len(h)*len(node['acts']):raise ValueError('Malformed combo strat array')
                    if node['pot']<=0:raise ValueError('Invalid solver pot')
                    if (data['stack']-max(node['bets']))/node['pot']<0:raise ValueError('Invalid node SPR')
                    reachable+=sum(w>1e-4 for w in node['w'][node['player']])
                if river_nodes==0:raise ValueError('No real river CFR nodes')
                cases.append(dict(line=case['line'],turn=case['turn'],
                    exact_source_sha256=case['subgame_sha256'],
                    gto_expl_pct=info['gto_expl_pct'],hero_gap_pct=info['hero_gap_pct'],
                    observed_pattern_count=case['matched_patterns'],
                    river_nodes=river_nodes,reachable_combo_node_rows=reachable,
                    partial_lock_hero_gain_bb=case.get('partial_pool_locked_hero_gain_bb'),
                    source_scope='REAL_NL2_POT_AND_STREET_MARGINAL_ONLY_NOT_HISTORY_COMBO'))
            out.append(dict(spot=spot,version=version,root_spr=m['root_spr'],
                real_source_sample_patterns=len(m['matched_aggregate_lock_patterns']),
                proved_subgames=len(cases),cases=cases,
                generic_MODEL_CERT=0,exact_board_GTO_CERT=0,kind='EXPERIMENTAL_POOL_AGGREGATE_LOCKED'))
        except Exception as e:errors.append({'artifact':artifact.name,'reason':str(e)})
    return dict(schema='ISO_LMP_AGGREGATE_LOCKED_CFR_PROOF_V1',
        validated_artifacts=len(out),validated_subgames=sum(x['proved_subgames'] for x in out),
        actual_pool_frequency_scope='NL2 marginal by pot family and street, not exact history or combo',
        model_CERT=0,model_EST=0,errors=errors,artifacts=out)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--downloads',required=True,type=pathlib.Path)
    p.add_argument('--solver-root',required=True,type=pathlib.Path)
    p.add_argument('--out',required=True,type=pathlib.Path)
    a=p.parse_args()
    r=verify(a.downloads,a.solver_root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k!='artifacts'},ensure_ascii=False))
    if r['errors'] or r['validated_artifacts']!=4:raise SystemExit(1)
if __name__=='__main__':main()
