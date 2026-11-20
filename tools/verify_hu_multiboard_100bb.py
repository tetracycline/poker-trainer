#!/usr/bin/env python3
"""Independent NL2 100bb multiboard CFR source, pot, rake, action, SPR,
convergence, full-street per-combo frequency reach and locked-pool provenance
audit. Creates no generic GTO certification by itself.
"""
import argparse,base64,collections,hashlib,json,pathlib,re,sys
REPO_SPOTS={
'BTN_BB':('SRP',5.5,97.5),
'CO_BB':('SRP',5.5,97.5),
'SB_BB':('SRP',6.0,97.0),
'UTG_CO':('SRP',6.5,97.5),
'BB3_BTN':('3BP',20.5,90.0),
'SB3_BTN':('3BP',21.0,90.0),
'CO3_BTN':('3BP',16.5,92.5),
'ISO_BTN_CO':('ISO',9.5,96.0),
'LMP_CO_BB':('LMP',2.5,99.0)}
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for z in iter(lambda:f.read(1024*1024),b''):h.update(z)
    return h.hexdigest()
def strict_medium_evidence(n,raw,seq_mask):
    """Re-evaluate b50 relative-equity distribution ONLY after every past
    hero action was legal under max/near-mix and blockers.
    No empirical private-card NL2 frequencies are invented.
    """
    actions=n['acts']
    if 'b50' not in actions:return dict(eligible=0,preferred=0,candidate=False,status='NO_50PCT_ACTION')
    i=actions.index('b50');actor=n['player'];nh=len(raw['hands'][actor])
    if len(n['w'][actor])!=nh or len(n['eq'])!=nh or len(n['ev'])!=nh*len(actions):
        raise ValueError('Missing equity/EV/w source for strict medium-size proof')
    masks=base64.b64decode(seq_mask,validate=True)
    if len(masks)!=nh:raise ValueError('Sequential mask length changed')
    allhands=[];bet=[];p50=0
    for k,m in enumerate(masks):
        if not m or float(n['w'][actor][k])<=1e-4:continue
        equity=float(n['eq'][k]);weight=float(n['w'][actor][k])
        if not 0<=equity<=1.001:raise ValueError('Invalid source equity')
        allhands.append((equity,weight))
        if m & (1<<i):
            raw_ev=[float(n['ev'][j*nh+k]) for j in range(len(actions))]
            preferred=int(i==max(range(len(raw_ev)),key=lambda x:raw_ev[x]))
            p50+=preferred
            bet.append((equity,weight))
    if not bet:return dict(eligible=0,preferred=0,candidate=False,status='B50_UNREACHABLE_AFTER_PREVIOUS_STREET')
    total=sum(w for _,w in allhands);ordered=sorted(allhands)
    def quantile(frac):
        target=total*frac;acc=0
        for eq,w in ordered:
            acc+=w
            if acc>=target:return eq
        return ordered[-1][0]
    qlo,qhi=quantile(1/3),quantile(2/3)
    low=mid=high=0
    lw=mw=hw=0.
    for eq,w in bet:
        if eq<qlo:low+=1;lw+=w
        elif eq>qhi:high+=1;hw+=w
        else:mid+=1;mw+=w
    eligible=len(bet);fraction=mw/(lw+mw+hw)
    candidate=eligible>=20 and mid>=10 and fraction>=0.20 and (high>=5 or low>=5)
    return dict(eligible=eligible,preferred=p50,
        best_ev_b50_fraction_pct=round(100*p50/eligible,3),
        low_count=low,middle_count=mid,high_count=high,
        mid_reach_mass_fraction_pct=round(100*fraction,3),candidate=bool(candidate),
        status='EXACT_BOARD_STRICT_PATH_NONPOLARIZED_RESEARCH_CANDIDATE_NOT_GENERIC_BET_RECOMMENDATION')
def source_nodes(d,seq):
    out=[]
    for n in d['nodes']:
        k='|'.join((n['board'],n['line'],str(n['player'])))
        strict=seq['nodes'].get(k)
        if strict is None:raise ValueError('No sequential mask for '+k)
        reach=sum(w>1e-4 for w in n['w'][n['player']])
        if reach==0 or strict['count']==0:continue
        spr=(d['stack']-max(n['bets']))/n['pot']
        if spr<0:raise ValueError('Negative SPR')
        medium=strict_medium_evidence(n,d,strict['mask'])

        actor=n['player'];hands=d['hands'][actor];nh=len(hands)
        actions=n['acts'];strictmask=base64.b64decode(strict['mask'],validate=True)
        if len(strictmask)!=nh or len(n['ev'])!=len(actions)*nh or len(n['strat'])!=len(actions)*nh:
            raise ValueError('Missing original CFR EV/strategy dimensions')
        bestlegal=bytearray([255]*nh);bestunrestricted=bytearray([255]*nh)
        weighted=[0.]*len(actions);total=0.
        for k,m in enumerate(strictmask):
            if not m:continue
            prob=[max(0.,float(n['strat'][z*nh+k])) for z in range(len(actions))]
            den=sum(prob)
            if den<=0:raise ValueError('Reachable actor with zero strategy sum')
            prob=[z/den for z in prob]
            ev=[float(n['ev'][z*nh+k]) for z in range(len(actions))]
            permitted=[z for z in range(len(actions)) if m&(1<<z)]
            if not permitted:raise ValueError('Reachable hand but no permissible action')
            bestlegal[k]=max(permitted,key=lambda z:ev[z])
            bestunrestricted[k]=max(range(len(actions)),key=lambda z:ev[z])
            weight=float(n['w'][actor][k]);total+=weight
            for z,pct in enumerate(prob):weighted[z]+=weight*pct
        per_action={act:round(100*weighted[i]/total,3) if total else 0
                    for i,act in enumerate(actions)}
        out.append(dict(public_board=n['board'],exact_node_line=n['line'],
          acting_seat=n['player'],pot_bb=n['pot']/100,
          remaining_bb=(d['stack']-max(n['bets']))/100,
          node_spr=round(spr,6),source_reachable_combos=reach,
          strictly_reachable_combos=strict['count'],
          strictly_reachable_masks_b64=strict['mask'],
          source_actions=n['acts'],
          action_frequency_weighted_pct=per_action,
          strict_legal_best_ev_action_indices_b64=base64.b64encode(bestlegal).decode('ascii'),
          strict_unconstrained_best_ev_action_indices_b64=base64.b64encode(bestunrestricted).decode('ascii'),
          best_ev_scope='CONDITIONAL_RUST_CFR_ACTION_EV_WITHIN_ACTUAL_EXACT_POT_AND_BOARD',
          medium_50pct_eligible_combos=medium['eligible'],
          b50_nonpolarized_relative_equity_research_candidate=medium['candidate'],
          medium_50pct_strict_evidence=medium))
    return out
def lock_scope(d,patterns,version):
    if version=='gto':
        return dict(villain_decision_nodes=0,pattern_matched_nodes=0,
            observed_marginal_source_nodes=0,imputed_assumption_nodes=0,
            unmatched_nodes=0,coverage_pct=None,all_villain_nodes_locked=False)
    villain=1 if version=='exp_oop' else 0
    candidates=[]
    for n in d['nodes']:
        if n['player']!=villain or len(n['acts'])<2:continue
        if not any(float(w)>1e-4 for w in n['w'][villain]):continue
        candidates.append(n)
    observed=imputed=matched=0
    samples=[]
    for n in candidates:
        hits=[item for item in patterns if re.search(item['pat'],n['line'])]
        if not hits:continue
        matched+=1
        # A coarse empirical marginal is NOT a direct conditional observation
        # of this exact bet-size, board, SPR and prior action history.
        first=hits[0]
        scope=first.get('scope','PINNED_MEASURED_NL2_SOURCE')
        if scope.startswith('ASSUMED') or first.get('n',0)<500:
            imputed+=1
        else:observed+=1
        if len(samples)<12:
            samples.append(dict(line=n['line'],board=n['board'],
                first_pattern=first['pat'],source=first.get('source'),
                source_observed_count=first.get('n'),scope=scope))
    total=len(candidates)
    return dict(villain_decision_nodes=total,pattern_matched_nodes=matched,
        observed_marginal_source_nodes=observed,imputed_assumption_nodes=imputed,
        unmatched_nodes=total-matched,
        coverage_pct=round(100*matched/total,3) if total else None,
        all_villain_nodes_locked=bool(total and matched==total),
        matching_examples=samples,
        caveat='Regex/source bucket matching does not prove the Rust driver locked every combo nor its conditional opponent behavior.')

def locked_model_gain(d,version):
    if version=='gto':return None
    info=d.get('info',{})
    before=info.get('ev_gto_vs_pool');after=info.get('ev_exploit')
    seat=1 if version=='exp_ip' else 0
    if isinstance(before,list) and isinstance(after,list) and len(before)==len(after)==2:
        return round((float(after[seat])-float(before[seat]))/100,5)
    return None

def verify(root,source_pin,run_id):
    sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
    from hu_sequential_cfr_reach import game_reach
    src=source_pin.resolve()
    expected_pool=sha(src/'inputs/pool_stats.json')
    reports=[]
    rejects=[]
    accum=collections.Counter()
    for ad in sorted(root.iterdir()):
        if not ad.is_dir() or not (ad.name.startswith('nl2-stage3-') or ad.name.startswith('nl2-multiboard-')):
            continue
        manifest=list((ad/'evidence').glob('*.json'))
        if len(manifest)!=1:
            rejects.append(dict(artifact=ad.name,reason='Expected one actual solver manifest'))
            continue
        m=json.loads(manifest[0].read_text())
        info=dict(artifact=ad.name,spot=m['spot'],version=m['version'],flop=m['flop'],cases=[],
            excludes=m.get('skipped',[]),errors=m.get('failures',[]))
        try:
            if m['schema']!='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1' or m['no_generic_certification'] is not True:
                raise ValueError('Not a genuine auditable multi-board solver record')
            if m['spot'] not in REPO_SPOTS or m['version'] not in ('gto','exp_ip','exp_oop'):
                raise ValueError('Unexpected source profile or version')
            if m.get('turn_sizing_mode','default') not in ('default','river-gaps','exact-b66-only'):
                raise ValueError('Unregistered turn subgame size menu')
            permitted_flop_lines={'oop-b33only':'b33 c','oop-b50only':'b50 c','oop-b75only':'b75 c'}
            policy=m.get('flop_line_policy','all')
            if policy in permitted_flop_lines:
                if m.get('selected_lines')!=[permitted_flop_lines[policy]]:
                    raise ValueError('Focused flop policy not identical to source action line')
            if m.get('turn_line_policy','default') not in ('default','b100only'):
                raise ValueError('Unregistered focused turn continuation')
            fam,pot,stack=REPO_SPOTS[m['spot']]
            if m['pot_family']!=fam or abs(m['root_pot_bb']-pot)>1e-6 or abs(m['root_remaining_bb']-stack)>1e-6:
                raise ValueError('Root pot/SPR assumption mismatch')
            if abs(m['root_spr']-stack/pot)>1e-4:
                raise ValueError('Root SPR mismatch')
            if m['pool_source_sha256']!=expected_pool:
                raise ValueError('NL2 statistical pool source hash mismatch')
            if m['spot'] in ('ISO_BTN_CO','LMP_CO_BB'):
                r=m['preflop_ranges']
                if r['source']!='ASSUMED_EXPLICIT_169CLASS':
                    raise ValueError('Assumed pool mislabeled empirical')
                for seat in ('oop_169','ip_169'):
                    if len(r[seat])!=169 or any(not 0<=float(x)<=1 for x in r[seat].values()) or not sum(r[seat].values()):
                        raise ValueError('Frozen assumed 169 class range invalid')
            else:
                if m['preflop_ranges']['source']!='PINNED_POKER_SOLVER_PREFLOP_CFR':
                    raise ValueError('Known SRP/3BP profile without real preflop CFR')
                if m['preflop_ranges']['full_sha256']!=sha(src/'v8_build/build/pf_data.json'):
                    raise ValueError('Preflop combo weights underlying file changed')
            if m['failures'] or m['solved_cases']!=len(m['cases']) or not m['cases']:
                raise ValueError('Original solver source incomplete')
            base=ad/'solver/postflop'
            flopfile=base/m['file_flop']
            if sha(flopfile)!=m['file_flop_sha256']:
                raise ValueError('Raw flop source sha256 mismatch')
            jobfile=flopfile.with_suffix('.job.json')
            if not jobfile.is_file():raise ValueError('Missing authentic Rust driver flop config')
            j=json.loads(jobfile.read_text());fr=json.loads(flopfile.read_text())
            if fr.get('flop')!=m['flop'] or fr['pot']!=round(100*pot) or fr['stack']!=round(100*stack):
                raise ValueError('Authentic flop model does not match assumed 100bb pot')
            if j['pot']!=round(100*pot) or j['stack']!=round(100*stack):
                raise ValueError('Rust job actual pot/stack inconsistent')
            if m.get('flop_line_policy') in permitted_flop_lines:
                actual_flop_extract=[e.get('prefix',[]) for e in j.get('extract',[]) if e.get('prefix',[])]
                expected_flop=permitted_flop_lines[m['flop_line_policy']].split()
                if m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK':
                    # The previously verified GTO flop solves a larger action
                    # set; the new EXP proof solves ONLY the declared downstream
                    # continuation. The GTO parent must contain our requested line.
                    if not any(p[:2]==expected_flop for p in actual_flop_extract):
                        raise ValueError('Exact requested line absent from pinned GTO flop parent')
                elif not actual_flop_extract or not all(p[:2]==expected_flop for p in actual_flop_extract):
                    raise ValueError('Actual flop job has unexpected or missing focused action extraction')
            if abs(j['rake_rate']-0.05)>1e-8 or j['rake_cap']!=1000:
                raise ValueError('Unstated rake vs expected NL2 5% max10bb')
            fp=m.get('flop_size_profile','full')
            if fp=='lmp-50-only':
                if m['spot']!='LMP_CO_BB' or m.get('flop_line_policy')!='oop-b50only':
                    raise ValueError('LMP restricted flop tree mismatched declared exact b50 c')
                if j.get('flop_oop')!='50%' or j.get('flop_ip')!='50%' or m.get('flop_action_sizes')!=['50%']:
                    raise ValueError('False 50pct restricted-game claim vs actual Rust menu')
                if m.get('restricted_tree_assumption') is not True:
                    raise ValueError('Missing restricted-tree warning on solver source')
            elif fp=='full':
                if not all(x in j.get('flop_oop','') for x in ('33%','50%','75%','100%')):
                    raise ValueError('Missing actual OOP lead sizes')
                if not all(x in j.get('flop_ip','') for x in ('33%','50%','75%','100%')):
                    raise ValueError('Missing actual IP bet sizes')
            else: raise ValueError('Unknown flop size proof profile')
            if m['version']=='gto' and j.get('hero') is not None:
                raise ValueError('GTO job unexpectedly locks a hero')
            partial_gto_parent=m.get('flop_parent_mode')=='PINNED_GTO_FLOP_PARENT_TURN_ONLY_LOCK'
            if partial_gto_parent:
                if m['version']=='gto' or j.get('hero') is not None or j.get('locks'):
                    raise ValueError('Copied GTO flop root mislabeled as locked flop')
                if m.get('flop_root_jobfile_sha256')!=sha(jobfile):
                    raise ValueError('Pinned GTO root Rust job SHA changed')
                if m.get('gto_parent_source_sha256')!=sha(flopfile):
                    raise ValueError('Pinned GTO parent raw flop SHA changed')
                if int(m.get('gto_parent_source_run_id',0))<=0:
                    raise ValueError('Missing immutable original GTO run ID')
                if m.get('turn_line_policy')!='b100only':
                    raise ValueError('Partial GTO parent lock requires fixed turn continuation')
            else:
                if m['version']!='gto' and j.get('hero')!=(1 if m['version']=='exp_ip' else 0):
                    raise ValueError('Locked hero seat is wrong')
                if m['version']!='gto' and not j.get('locks'):
                    raise ValueError('Pool locked variant has no lock patterns')
            for c in m['cases']:
                rawfile=base/c['source_path']
                if sha(rawfile)!=c['source_sha256']:
                    raise ValueError('Subgame SHA mismatch '+c['source_path'])
                if m.get('turn_line_policy')=='b100only':
                    if m.get('selected_turn_lines')!=['b100 c']:
                        raise ValueError('Requested turn line not declared exactly')
                    subjobfile=rawfile.with_suffix('.job.json')
                    if not subjobfile.is_file():
                        raise ValueError('Missing true focused turn Rust job config')
                    subjob=json.loads(subjobfile.read_text())
                    sub_extract=[e.get('prefix',[]) for e in subjob.get('extract',[]) if e.get('prefix',[])]
                    if not sub_extract or not all(p[:2]==['b100','c'] for p in sub_extract):
                        raise ValueError('Actual Rust extracted turn line mismatches b100 c')
                if m.get('turn_sizing_mode')=='river-gaps':
                    real_job=rawfile.with_suffix('.job.json')
                    if not real_job.exists():raise ValueError('No exact turn-river solver config')
                    j2=json.loads(real_job.read_text())
                    if j2.get('turn_oop')!='33%,66%,75%' or j2.get('turn_ip')!='33%,66%,75%':
                        raise ValueError('Actual solved turn sizes differ from predeclared river-gaps menu')
                if m.get('turn_sizing_mode')=='exact-b66-only':
                    if m['spot']!='SB_BB' or m['version']!='gto' or m.get('selected_lines')!=['x x'] or m.get('selected_turn_lines')!=['b66 c']:
                        raise ValueError('Exact 66% source requires predeclared SB_BB x-x GTO')
                    exact_job=rawfile.with_suffix('.job.json')
                    if not exact_job.is_file():raise ValueError('Missing exact b66 Rust turn job')
                    cfg=json.loads(exact_job.read_text())
                    if cfg.get('turn_oop')!='66%' or cfg.get('turn_ip')!='66%':
                        raise ValueError('Actual Rust menu not exclusive 66%, may merge with 75')
                    ex=[z.get('prefix',[]) for z in cfg.get('extract',[]) if z.get('prefix',[])]
                    if not ex or not all(z[:2]==['b66','c'] for z in ex):
                        raise ValueError('Exact b66 river extraction missing')
                if partial_gto_parent:
                    actual_subjob=rawfile.with_suffix('.job.json')
                    if not actual_subjob.is_file():raise ValueError('No genuine downstream Rust EXP job')
                    sj=json.loads(actual_subjob.read_text())
                    hero=1 if m['version']=='exp_ip' else 0
                    if sj.get('hero')!=hero or not sj.get('locks'):
                        raise ValueError('Turn-only lock lacks correct hero/real subgame locks')
                    if abs(sj.get('rake_rate',-1)-0.05)>1e-8 or sj.get('rake_cap')!=1000:
                        raise ValueError('Turn-only true Rust job rake differs from NL2')
                d=json.loads(rawfile.read_text())
                if m.get('turn_sizing_mode')=='exact-b66-only':
                    if not any(n['line']=='x x/' and 'b66' in n.get('acts',[]) for n in d['nodes']):
                        raise ValueError('Actual Rust root lacks distinct b66 action')
                    if not any(n['line']=='x x/b66 c/' and len(n['board'])==10 for n in d['nodes']):
                        raise ValueError('Actual Rust river lacks exact b66 call branch')
                if d['flop']!=m['flop'] or d['turn']!=c['turn'] or d['line0']!=c['line']:
                    raise ValueError('Wrong flop-to-turn lineage')
                parent=next((n for n in fr['nodes'] if n['line']==c['line']+'/' and n['board'][-2:]==c['turn']),None)
                if parent is None:raise ValueError('No exact flop parent '+c['line'])
                pp=parent['pot']/100;rem=(fr['stack']-max(parent['bets']))/100
                if abs(pp-c['flop_parent_pot_bb'])>1e-5 or abs(rem-c['flop_parent_effective_remaining_bb'])>1e-5 or abs(rem/pp-c['real_flop_parent_spr'])>1e-5:
                    raise ValueError('Parent authentic SPR inconsistent')
                gg=d['info'].get('gto_expl_pct')
                hh=d['info'].get('hero_gap_pct')
                if gg is None or gg>0.5:
                    raise ValueError('GTO equilibrium gap >0.5% '+str(gg))
                if m['version']!='gto' and (hh is None or hh>0.5):
                    raise ValueError('Locked hero gap >0.5% '+str(hh))
                if c['true_river_nodes']!=sum(len(n['board'])==10 for n in d['nodes']):
                    raise ValueError('Declared river CFR node count wrong')
                sequential,proof=game_reach(fr,d)
                if not proof['sequential_actor_combo_nodes']:
                    # Real CFR solved the game, but this branch is impossible
                    # under the user-mandated max/near action policy.
                    # Never publish an unreachable exact-board GTO example.
                    info['excludes'].append(dict(line=c['line'],turn=c['turn'],
                        source_sha256=c['source_sha256'],
                        reason='SOLVED_CFR_BUT_ALL_COMBOS_UNREACHABLE_AFTER_STRICT_MULTISTREET_POLICY'))
                    accum['authentic_cfr_cases_excluded_by_reachability']+=1
                    continue
                nodes=source_nodes(d,dict(nodes=sequential))
                locked=lock_scope(d,m['locks'],m['version'])
                gain=locked_model_gain(d,m['version'])
                if not nodes:
                    info['excludes'].append(dict(line=c['line'],turn=c['turn'],
                        source_sha256=c['source_sha256'],
                        reason='SOLVED_CFR_BUT_NO_STRICT_ACTOR_COMBOS'))
                    accum['authentic_cfr_cases_excluded_by_reachability']+=1
                    continue
                source=dict(run_id=run_id,artifact=ad.name,
                  pot_family=fam,spot=m['spot'],version=m['version'],flop=m['flop'],
                  turn=c['turn'],flop_line=c['line'],flop_root_pot_bb=pot,
                  flop_root_stack_bb=stack,flop_source_sha256=m['file_flop_sha256'],
                  root_spr=m['root_spr'],turn_spr=c['real_flop_parent_spr'],
                  source_sha256=c['source_sha256'],gto_exploitability_pct=gg,
                  locked_hero_gap_pct=hh,flop_size_menu=['33%','50%','75%','100%'],
                  NL2_pool_source_sha256=expected_pool,
                  lock_patterns=m['locks'] if m['version']!='gto' else [],
                  lock_coverage_pct=locked['coverage_pct'],
                  villain_lock_scope=locked,
                  hero_model_gain_bb=gain,
                  rust_source_lock_stats=d['info'].get('lock_stats',{}),
                  medium50_strict_eligible_total=sum(n['medium_50pct_eligible_combos'] for n in nodes),
                  medium50_strict_merged_research_nodes=sum(bool(n['b50_nonpolarized_relative_equity_research_candidate']) for n in nodes),
                  assumed_missing_rate_policy=m['unknown_action_frequency_policy'],
                  empirical_scope=('ASSUMED_PREFLOP_RANGES' if fam in ('ISO','LMP') else 'PINNED_PREFLOP_CFR'),
                  certified_scope=('EXACT_BOARD_ONLY_GTO' if m['version']=='gto'
                      else 'TURN_ONLY_NL2_MARGINAL_LOCK_FROM_PINNED_GTO_FLOP_PARENT'
                      if partial_gto_parent else 'PARTIALLY_LOCKED_NL2_MARGINAL_PROXY'),
                  hands_by_seat=d['hands'],
                  strict_combo_path_summary=dict(proof),nodes=nodes)
                info['cases'].append(source)
                accum['verified_cases']+=1
                accum['gto' if m['version']=='gto' else 'pool_locked_experimental']+=1
                accum['sequential_actor_combo_nodes']+=proof['sequential_actor_combo_nodes']
                accum['individually_proved_nodes']+=len(nodes)
                accum['medium50_strict_eligible_combo_nodes']+=sum(n['medium_50pct_eligible_combos'] for n in nodes)
                accum['medium50_strict_research_candidate_nodes']+=sum(bool(n['b50_nonpolarized_relative_equity_research_candidate']) for n in nodes)
                accum['vil_observed_marginal_lock_match_nodes']+=locked['observed_marginal_source_nodes']
                accum['vil_assumed_default_lock_match_nodes']+=locked['imputed_assumption_nodes']
                accum['vil_unlocked_nodes']+=locked['unmatched_nodes']
        except Exception as exc:
            info['errors'].append(str(exc))
            rejects.append(dict(artifact=ad.name,reason=str(exc)))
        reports.append(info)
    if not reports:rejects.append(dict(reason='No authentic multi-board artifacts found'))
    return dict(schema='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1',
      source_run_id=run_id,actual_NL2_stake_hands=2334487,
      source_poker_solver_pin='abe310c3aad02dd4a7c77fb2831801fd490cf51b',
      authentic_rust_engine_pin='9d1509fe5077d019825f833eed04b16d342dfda1',
      no_generic_texture_certification=True,
      new_authentic_board_cases=accum['verified_cases'],
      exact_board_gto_sources=accum['gto'],
      imputed_pool_locked_sources=accum['pool_locked_experimental'],
      verified_source_nodes=accum['individually_proved_nodes'],
      strictly_reachable_combo_nodes=accum['sequential_actor_combo_nodes'],
      medium50_strict_eligible_combo_nodes=accum['medium50_strict_eligible_combo_nodes'],
      medium50_strict_nonpolarized_research_candidate_nodes=accum['medium50_strict_research_candidate_nodes'],
      villain_nodes_with_measured_NL2_marginal_lock_source=accum['vil_observed_marginal_lock_match_nodes'],
      villain_nodes_matched_assumed_default=accum['vil_assumed_default_lock_match_nodes'],
      villain_nodes_unlocked=accum['vil_unlocked_nodes'],
      errors=rejects,artifacts=reports)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--downloads',required=True,type=pathlib.Path)
    p.add_argument('--solver-root',required=True,type=pathlib.Path)
    p.add_argument('--run-id',type=int,required=True)
    p.add_argument('--out',required=True,type=pathlib.Path)
    a=p.parse_args()
    d=verify(a.downloads,a.solver_root,a.run_id)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in d.items() if k not in ('artifacts','errors')},ensure_ascii=False))
    if d['errors'] or d['new_authentic_board_cases']<1:raise SystemExit(1)
if __name__=='__main__':main()
