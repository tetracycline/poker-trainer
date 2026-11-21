#!/usr/bin/env python3
"""Create the source-proved 392-item NL2 training status registry.

CERT-MULTIBOARD = >=3 and <=5 named DIFFERENT authentic flop boards with:
same pot family, position, exact flop/turn action history, acting seat,
100bb preflop root ranges, converged GTO <=0.5%, legal sequential combo
reach and true SPR within 5% of the APPROX design's disclosed estimate.
CERT DOES NOT APPLY to the generic texture bucket beyond those boards.

EXP/locked NL2 must be paired to the *identical* source board and history;
unobserved player-pool conditional rates are imputed and documented.
All low-frequency nodes remain APPROX, irrespective of research examples.
"""
import argparse,base64,collections,gzip,hashlib,itertools,json,pathlib,re
RANKS='23456789TJQKA'
VERBS={'過':('x',),'跟':('c',),'加注':('r',),'下注':('b33','b50','b66','b75','b100'),
       '超池下注':('b150',),'全下':('a',),'加注全下':('a',)}
ORDER={'SB':0,'BB':1,'UTG':2,'HJ':3,'CO':4,'BTN':5}
PINS={44521980749:'01',44522421850:'02',44525865923:'03',
      44653774402:'04',44654973894:'05'}
FAM_ROOT={'BTN_BB':(5.5,97.5),'CO_BB':(5.5,97.5),
          'SB_BB':(6.0,97),'UTG_CO':(6.5,97.5),'BB3_BTN':(20.5,90),
          'SB3_BTN':(21.,90),'CO3_BTN':(16.5,92.5),
          'LMP_CO_BB':(2.5,99),'ISO_BTN_CO':(9.5,96)}
def hashsha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
    return h.hexdigest()
def load_gzip(p):
    return json.loads(gzip.decompress(p.read_bytes()))
def hero_seat(pre):
    pre=str(pre)
    got=re.search(r'你\s*(SB|BB|UTG|HJ|CO|BTN)\b',pre)
    names=re.findall(r'\b(SB|BB|UTG|HJ|CO|BTN)\b',pre)
    if not got:return None
    hero=got.group(1)
    others=[a for a in names if a!=hero]
    if not others:return None
    return 1 if ORDER[hero]>min(ORDER[a] for a in others) else 0

def tokenize(h):
    # An OOP player starts a new betting street with EMPTY action history.
    # This is not a missing decision; it is a bona fide solver "/" root.
    if not str(h).strip():return ('',)
    clauses=[]
    for z in str(h).split('、'):
        t=z.strip()
        if not t:continue
        if t.startswith('你'):v=t[1:]
        elif t.startswith('對手'):v=t[2:]
        else:return ()
        if v not in VERBS:return ()
        clauses.append(VERBS[v])
    if len(clauses)>10:return ()
    return tuple(' '.join(combo) for combo in itertools.product(*clauses))

def candidates(model,alllines,locked_by_key,strict,limit_spr=0.05):
    segments=model['abstract_action_history'].split('|')
    st=model['street']; seat=hero_seat(model['preflop_text'])
    if seat is None:return [],'NO_TRUSTED_ACTING_SEAT_IN_PREFLOP'
    if len(segments)!=st+1:return [],'INCOMPLETE_OR_EXTRA_STREET_HISTORY'
    fragments=[tokenize(s) for s in segments]
    if any(not f for f in fragments):return [],'UNPARSABLE_ACTION_SEQUENCE'
    possible=(a for a in itertools.product(*fragments))
    keys=set()
    for actions in possible:
        if st==1:
            target=actions[0]+'/'+actions[1]
        else:
            target=actions[0]+'/'+actions[1]+'/'+actions[2]
        keys.add(target)
    family=model['family'];spot=model['spot']
    rootpot,rootstack=FAM_ROOT[spot]
    selected=[]
    for key in keys:
        for g,n,proof,origin in alllines.get((spot,family,st,seat,key),()):
            if abs(g['root_pot_bb']-rootpot)>1e-6 or abs(g['root_remaining_bb']-rootstack)>1e-6:
                continue
            if g['gto_gap_pct'] is None or g['gto_gap_pct']>0.5:continue
            value=n['spr'];estimated=model['approx_spr']
            err=abs(value-estimated)/max(1.,value)
            if err>limit_spr:continue
            if proof<1 or n['reachable']<1:continue
            if st==1 and len(n['board'])!=8:continue
            if st==2 and len(n['board'])!=10:continue
            pool_key=(spot,family,g['flop'],g['turn'],g['flop_line'],n['board'],n['line'],seat)
            exp=locked_by_key.get(pool_key,[])
            variants=[]
            for sample in exp:
                cov=sample.get('pool_coverage')
                variants.append(dict(version=sample['version'],run_id=sample['run_id'],
                    sha256=sample['sha'],source_scope=sample['scope'],
                    villain_observed_pattern_node_share_pct=cov,
                    source_not_real_per_combo_observation=True,
                    unknown_history_frequency_filled_with_default=sample.get('unknown_defaults',False),
                    observed_marginal_source_nodes=sample.get('observed_marginal_nodes'),
                    assumed_default_source_nodes=sample.get('assumed_nodes'),
                    unlocked_source_nodes=sample.get('unlocked_nodes'),
                    hero_model_gain_bb=sample.get('hero_gain_bb')))
            # An exact model whose EXP actor isn't the hero may not borrow
            # the opponent's best action as the hero's recommendation.
            intended='exp_ip' if seat==1 else 'exp_oop'
            variants=[v for v in variants if v['version']==intended]
            selected.append(dict(flop=g['flop'],turn=g['turn'],public_board=n['board'],
                actual_exact_action_line=n['line'],acting_seat=seat,
                exact_flop_action=g['flop_line'],actual_pot_bb=n['pot_bb'],
                actual_effective_stack_bb=n['stack_bb'],actual_spr=value,
                model_assumed_spr=estimated,relative_spr_error_pct=round(100*err,4),
                genuine_gto_exploitability_pct=g['gto_gap_pct'],
                source_run_id=g['run_id'],source_sha256=g['sha'],
                source_kind=g['source_kind'],assumed_preflop_ranges=g['source_kind'].startswith('ASSUMED'),
                exact_combo_reachable=n['reachable'],strict_full_street_combo_reachable=proof,
                exact_node_actions=n['actions'],
                medium_50pct_eligible_combos=n.get('b50_eligible',0),
                b50_nonpolarized_relative_equity_research_candidate=bool(n.get('medium_candidate',False)),
                nl2_locked_variants=variants))
    unique={}
    for c in selected:
        k=(c['flop'],c['turn'],c['public_board'],c['actual_exact_action_line'])
        old=unique.get(k)
        if old is None or (
            len(c['nl2_locked_variants'])>len(old['nl2_locked_variants']),
            -c['relative_spr_error_pct'],c['strict_full_street_combo_reachable'])>(
            len(old['nl2_locked_variants']),-old['relative_spr_error_pct'],old['strict_full_street_combo_reachable']):
            unique[k]=c
    return list(unique.values()),None

def texture(flop):
    ranks=[flop[i] for i in (0,2,4)]
    suits=[flop[i] for i in (1,3,5)]
    if len(set(suits))==1:return 'MONOTONE'
    if len(set(ranks))<3:return 'PAIRED'
    r=max(RANKS.index(x) for x in ranks)
    if r==12:return 'ACE_HIGH'
    if r>=10:return 'KQ_HIGH'
    if r>=8:return 'JT_HIGH'
    return 'LOW'

def choose_3_5(rows):
    # SOURCE-DRIVEN: must represent distinct flops, >=2 textures and true
    # hero-side locked response for ALL selected example boards.
    by_flop=collections.defaultdict(list)
    for x in rows:
        by_flop[x['flop']].append(x)
    winners=[]
    for flop,items in by_flop.items():
        target=sorted(items,key=lambda c:(-int(bool(c['nl2_locked_variants'])),
            c['relative_spr_error_pct'],-c['strict_full_street_combo_reachable']))[0]
        if target['nl2_locked_variants']:winners.append(target)
    if len(winners)<3:return [],'NOT_ENOUGH_DISTINCT_AUTHENTIC_FLOPS_WITH_HERO_LOCKED_SOURCE'
    preferred=[]
    remaining=sorted(winners,key=lambda x:(x['relative_spr_error_pct'],
        -x['strict_full_street_combo_reachable'],x['flop']))
    while remaining and len(preferred)<5:
        seen={texture(z['flop']) for z in preferred}
        unseen=[x for x in remaining if texture(x['flop']) not in seen]
        x=(unseen or remaining)[0]
        x['flop_texture']=texture(x['flop'])
        preferred.append(x)
        remaining.remove(x)
    if len({x['flop_texture'] for x in preferred})<2:
        return [],'REPRESENTATIVE_BOARD_COVERAGE_LACKS_SECOND_TEXTURE'
    return preferred,None

def build_source_index(root,extra):
    # The on-disk authentic source compact files were independently SHA and
    # node/pot validated by previous Actions. Exclude local offline unverified
    # experimental shards from CERT-MULTIBOARD.
    source=[
        root/'nl2_hu_exact_boards.json.gz',
        root/'nl2_hu_exact_boards_b04.json.gz',
        root/'nl2_hu_exact_boards_b05.json.gz'
    ]
    games=[];official=[]
    for path in source:
        d=load_gzip(path)
        assert d['schema']=='HU_NL2_EXACT_BOARD_CFR_V1' and d['generic_model_upgrades']==0
        games.extend(d['subgames'])
    if len(games)!=644:raise ValueError('Official immutable CFR index expected 644 true subgames')
    by_exact=collections.defaultdict(list)
    by_locked=collections.defaultdict(list)
    strict={}
    for bid in ('01','02','03','04','05'):
        path=root/f'nl2_hu_sequential_reach_official_b{bid}.json.gz'
        if not path.exists():raise ValueError('Missing independently verified sequential reach '+str(path))
        d=load_gzip(path)
        if d['schema']!='HU_NL2_SEQUENTIAL_REACH_OVERLAY_V1' or d['generic_model_CERT']!=0:
            raise ValueError('Invalid sequential source proof')
        strict.update(d['subgames_by_source_sha256'])
    for game in games:
        g=dict(spot=game['spot'],family=game['pot_family'],version=game['version'],
            flop=game['flop'],turn=game['turn'],flop_line=game['flop_line'],
            root_pot_bb=game['flop_root_pot_bb'],root_remaining_bb=game['flop_root_stack_bb'],
            run_id=game['source_run_id'],sha=game['source_sha256'],
            gto_gap_pct=game['gto_gap_pct'],source_kind='PINNED_PREFLOP_CFR_OFFICIAL')
        proof=strict.get(g['sha'],{}).get('nodes',{})
        for n in game['nodes']:
            seat=n['acting_seat'];key=(n['board'],n['line'],str(seat))
            seq=proof.get('|'.join(key),{})
            rows=int(seq.get('count',0))
            if game['version']=='gto':
                st=1 if len(n['board'])==8 else 2 if len(n['board'])==10 else None
                if st is None:continue
                nn=dict(board=n['board'],line=n['line'],seat=seat,spr=n['node_spr'],
                    pot_bb=n['pot_units']/100,stack_bb=n['remaining_stack_units']/100,
                    reachable=n['reachable_combos'],actions=n['actions'],
                    b50_eligible=n.get('medium_50pct_eligible_combos',0),
                    medium_candidate=(n.get('b50_relative_equity_mix') or {}).get('nonpolarized_medium_bet_candidate',False))
                by_exact[(g['spot'],g['family'],st,seat,n['line'])].append((g,nn,rows,'official'))
            else:
                key=(g['spot'],g['family'],g['flop'],g['turn'],g['flop_line'],n['board'],n['line'],seat)
                cov=(game.get('nl2_pool_lock_coverage') or {}).get('coverage_pct')
                by_locked[key].append(dict(version=g['version'],run_id=g['run_id'],sha=g['sha'],
                     pool_coverage=cov,scope='PARTIAL_NL2_OBSERVED_AGGREGATE_LOCK',
                     unknown_defaults=False,hero_gain_bb=game.get('hero_gain_vs_locked_pool_bb')))
    new_count=0
    for path in extra:
        source=load_gzip(path) if path.suffix=='.gz' else json.loads(path.read_text())
        if source['schema']!='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1' or source['errors']:
            raise ValueError('New CFR source not independently verified: '+str(path))
        for artifact in source['artifacts']:
            for sample in artifact['cases']:
                new_count+=1
                g=dict(spot=sample['spot'],family=sample['pot_family'],version=sample['version'],
                    flop=sample['flop'],turn=sample['turn'],flop_line=sample['flop_line'],
                    root_pot_bb=sample['flop_root_pot_bb'],root_remaining_bb=sample['flop_root_stack_bb'],
                    run_id=sample['run_id'],sha=sample['source_sha256'],
                    gto_gap_pct=sample['gto_exploitability_pct'],source_kind=sample['empirical_scope'])
                for n in sample['nodes']:
                    seat=n['acting_seat'];line=n['exact_node_line'];board=n['public_board']
                    if g['version']=='gto':
                        st=1 if len(board)==8 else 2 if len(board)==10 else None
                        if st is None:continue
                        nn=dict(board=board,line=line,seat=seat,spr=n['node_spr'],
                            pot_bb=n['pot_bb'],stack_bb=n['remaining_bb'],
                            reachable=n['source_reachable_combos'],
                            actions=n['source_actions'],
                            b50_eligible=n.get('medium_50pct_eligible_combos',0),
                            medium_candidate=n.get('b50_nonpolarized_relative_equity_research_candidate',False))
                        by_exact[(g['spot'],g['family'],st,seat,line)].append(
                             (g,nn,n['strictly_reachable_combos'],'new-github-actions'))
                    else:
                        key=(g['spot'],g['family'],g['flop'],g['turn'],g['flop_line'],board,line,seat)
                        matched=sample.get('villain_lock_scope') or {}
                        # Count real *marginal* source coverage separately from
                        # assumed rates and unobserved action-history nodes.
                        by_locked[key].append(dict(version=g['version'],run_id=g['run_id'],sha=g['sha'],
                          pool_coverage=sample.get('lock_coverage_pct'),
                          scope=sample['certified_scope'],
                          unknown_defaults=int(matched.get('imputed_assumption_nodes',0))>0,
                          observed_marginal_nodes=int(matched.get('observed_marginal_source_nodes',0)),
                          assumed_nodes=int(matched.get('imputed_assumption_nodes',0)),
                          unlocked_nodes=int(matched.get('unmatched_nodes',0)),
                          hero_gain_bb=sample.get('hero_model_gain_bb')))
    return by_exact,by_locked,dict(official_subgames=len(games),new_subgames=new_count,source_files=[str(x) for x in extra])

def promote(rank,queue,root,proof_files):
    models={x['model_id']:x for x in queue['records']}
    by_exact,by_lock,source_summary=build_source_index(root,proof_files)
    statuses={}
    error_counts=collections.Counter()
    selected_count=0
    for r in rank['nodes']:
        m=models[r['model_id']]
        assert r['model_id']==m['model_id']
        assert m['family']==r['family'] and m['solver_profile']==r['spot']
        r['preflop_text']=m['preflop_text']
        r['abstract_action_history']=m['abstract_action_history']
        c,status=candidates(r,by_exact,by_lock,None)
        examples,reason=choose_3_5(c) if r['high_frequency_priority'] and status is None else ([],status)
        if not r['high_frequency_priority']:
            reason='LOWER_FREQUENCY_BELOW_PREREGISTERED_TOP24_CUTOFF'
        if examples:
            selected_count+=1
        else:error_counts[reason or 'UNKNOWN_INSUFFICIENT_PROOF']+=1
        record=dict(model_id=m['model_id'],source_model_id=m['source_id'],
            label='CERT-MULTIBOARD' if examples else 'APPROX',
            must_not_extrapolate_to_all_texture_cards=True,
            model_frequencies_are_not_observed_combo_counts=True,
            frequency_rank=r['rank_by_empirically_grounded_frequency_proxy'],
            estimated_nl2_occurrence_opportunity_frac=r['estimated_NL2_hand_opportunity_fraction'],
            high_frequency_preregistered=r['high_frequency_priority'],
            family=m['family'],solver_profile=m['solver_profile'],street=m['street'],
            preflop_text=m['preflop_text'],abstract_action_history=m['abstract_action_history'],
            assumed_model_node_spr=m['approx_spr'],
            certified_3_to_5_exact_flop_boards=examples,
            proven_exact_board_count=len(examples),blocked_reason=None if examples else reason,
            source_credibility='GITHUB_ACTIONS_AUTHENTIC_CFR_SHA256_AND_FULL_STREET_COMBO_REACH')
        statuses[m['model_id']]=record
    if len(statuses)!=392 or rank['summary']['high_frequency_priority']!=24:
        raise ValueError('Prereg 392 MODEL ranking changed without reapproval')
    counters=collections.Counter(x['label'] for x in statuses.values())
    assert counters['CERT-MULTIBOARD']+counters['APPROX']==392
    return dict(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V1',
       CERT_MULTIBOARD=counters['CERT-MULTIBOARD'],APPROX=counters['APPROX'],
       TOTAL=392,top_N_rank_cutoff=24,
       exact_board_min=3,exact_board_max=5,
       spr_relative_tolerance=0.05,
       selection_outcome_independent=True,
       unchanged_100pct_river_navigation=True,
       sample_model_limits='CERT-MULTIBOARD attests ONLY named board runouts/acting player, source bet lines and exact source SPR; generic hand-class texture decision remains APPROX outside these.',
       nl2_aggregate_frequency_assumptions=rank['disclosed_assumptions'],
       source_evidence=source_summary,
       nonupgrade_reasons=dict(error_counts),
       records=statuses)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--rank',required=True,type=pathlib.Path)
    p.add_argument('--queue',required=True,type=pathlib.Path)
    p.add_argument('--root',required=True,type=pathlib.Path)
    p.add_argument('--new-proof',type=pathlib.Path,nargs='*',default=[])
    p.add_argument('--out',required=True,type=pathlib.Path)
    a=p.parse_args()
    d=promote(json.loads(a.rank.read_text()),json.loads(a.queue.read_text()),a.root,a.new_proof)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'CERT_MULTIBOARD':d['CERT_MULTIBOARD'],'APPROX':d['APPROX'],
        'top24':d['top_N_rank_cutoff'],'sources':d['source_evidence'],'reasons':d['nonupgrade_reasons']},ensure_ascii=False))
if __name__=='__main__':main()
