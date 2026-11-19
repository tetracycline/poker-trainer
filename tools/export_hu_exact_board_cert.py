#!/usr/bin/env python3
"""Export honest exact-board CFR references for NL2.

Only source nodes from a converged *GTO* solver with independently checked
source SHA/pot/action-line are labeled CERT_EXACT_BOARD. Pool-locked responses
are EXPERIMENTAL_LOCKED when the equilibrium stage was less precise.
A representative texture does not certify a generic six-texture MODEL node.
"""
import argparse,base64,hashlib,json,pathlib

def digest(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for buf in iter(lambda:f.read(1024*1024),b''):h.update(buf)
    return h.hexdigest()

def node_compact(node, raw):
    """Compact and fully auditable per-combo actions and relative action EVs."""
    import math,statistics
    player=node['player'];hands=raw['hands'][player]
    w=node['w'][player];f=node['strat'];act=node['acts'];nh=len(hands)
    e=node.get('ev',[]);qeq=node.get('eq',[])
    if len(w)!=nh or len(f)!=nh*len(act) or len(e)!=nh*len(act) or len(qeq)!=nh:
        raise ValueError('Malformed combo/strategy/action EV dimensions')
    if len(act)>8:raise ValueError('At most 8 source actions supported')
    masks=bytearray(nh);best_ev=bytearray([255]*nh)
    sums=[0.]*len(act);total=0.;live=mixed=0
    weights=[];b50_candidates=[]
    ev_gaps=[]
    b50_idx=act.index('b50') if 'b50' in act else None
    for h in range(nh):
        weight=float(w[h])
        if weight<=1e-4:continue
        prob=[max(0.,float(f[j*nh+h])) for j in range(len(act))]
        t=sum(prob)
        if t<=0:continue
        prob=[v/t for v in prob]
        highest=max(range(len(prob)),key=lambda i:prob[i])
        kept=[highest]+[i for i,p in enumerate(prob) if i!=highest and
               p>=0.4-1e-7 and p>=0.7*prob[highest]-1e-7]
        masks[h]=sum(1<<i for i in kept)
        live+=1;mixed+=int(len(kept)>1);total+=weight
        for i,p in enumerate(prob):sums[i]+=weight*p
        # Action EV is in the solver's original 1/100 bb units. Record the
        # maximum for the same actual board and opponent, never a generic pool.
        values=[float(e[j*nh+h]) for j in range(len(act))]
        if any(not math.isfinite(x) for x in values):
            raise ValueError('Nonfinite action EV')
        ranked=sorted(range(len(values)),key=lambda i:(values[i],prob[i]),reverse=True)
        best_ev[h]=ranked[0]
        if len(values)>1:ev_gaps.append((values[ranked[0]]-values[ranked[1]])/100.)
        eq=float(qeq[h])
        if not math.isfinite(eq) or eq<0 or eq>1.001:
            raise ValueError('Invalid relative equity of actual combo')
        weights.append((eq,weight))
        if b50_idx is not None and b50_idx in kept:
            b50_candidates.append((eq,weight,h,highest,values[b50_idx]))
    low=middle=high=0
    lowmass=midmass=highmass=0.
    if weights and b50_idx is not None:
        sorted_w=sorted(weights)
        def weighted_quantile(frac):
            target=total*frac;acc=0.
            for eq,weight in sorted_w:
                acc+=weight
                if acc>=target:return eq
            return sorted_w[-1][0]
        first,second=weighted_quantile(1/3),weighted_quantile(2/3)
        for eq,weight,h,highest,ev50 in b50_candidates:
            if eq<first:low+=1;lowmass+=weight
            elif eq>second:high+=1;highmass+=weight
            else:middle+=1;midmass+=weight
    b50mass=lowmass+midmass+highmass
    merged=bool(len(b50_candidates)>=20 and middle>=10
                and midmass>=b50mass*0.2 and (high>=5 or low>=5))
    return {'line':node['line'],'board':node['board'],'acting_seat':player,
       'actions':act,'pot_units':node['pot'],'bets_units':node['bets'],
       'remaining_stack_units':raw['stack']-max(node['bets']),
       'node_spr':round((raw['stack']-max(node['bets']))/node['pot'],6),
       'reachable_combos':live,'near_mixed_combos':mixed,
       'reach_weighted_action_pct':{a:round(100*x/total,3) if total else 0.
                                     for a,x in zip(act,sums)},
       'eligibility_encoding':'base64 uint8 bitmask in exact hands[acting_seat] order; highest always kept; second iff f>=40% and >=70%*fmax; absent zero',
       'eligible_action_masks_b64':base64.b64encode(masks).decode('ascii'),
       'best_ev_action_indices_b64':base64.b64encode(best_ev).decode('ascii'),
       'best_ev_encoding':'base64 uint8 index into original actions in exact hands[acting_seat] order, 255 if unreachable; conditional solver EV, not universal NL2 recommendation',
       'median_best_vs_next_ev_gap_bb':round(statistics.median(ev_gaps),5) if ev_gaps else None,
       'medium_50pct_eligible_combos':len(b50_candidates),
       'b50_relative_equity_mix':None if b50_idx is None else {
           'low_count':low,'middle_count':middle,'high_count':high,
           'middle_eligible_weight_share_pct':round(100*midmass/b50mass,2) if b50mass else 0.,
           'definition':'Relative to current spot reach-weighted equity terciles, not fixed hand classes',
           'nonpolarized_medium_bet_candidate':merged,
           'candidate_threshold':'b50 eligible >=20 combos; middle equity >=10 combos and >=20% of b50 reach mass; low or high tail >=5 combos',
           'status':'SOURCE_ONLY_NOT_GENERALIZABLE_TO_TEXTURE_OR_ANOTHER_SPR'
       }}

def build(root,proof):
    all_verified={}
    for a in proof['artifacts']:
        for c in a['cases']:
            all_verified[(a['artifact'],c['source_sha256'],c['flop'],c['line'],c['turn'])]=c
    result=[]
    for ad in sorted(root.iterdir()):
        if not ad.is_dir() or not ad.name.startswith('nl2-stage2-') or '-verified-provenance' in ad.name:continue
        ms=list((ad/'evidence').glob('*.json'))
        if len(ms)!=1:raise ValueError('Exactly one batch manifest required: '+ad.name)
        m=json.loads(ms[0].read_text())
        if m['failures']:raise ValueError('Source solver reported failure')
        versions=m['version']
        for c in m['cases']:
            key=(ad.name,c['sub_sha256'],c['flop'],c['line'],c['turn'])
            if key not in all_verified:
                raise ValueError('No independently verified proof: '+ad.name+'/'+c['line'])
            verified=all_verified[key]
            rawfile=ad/'solver/postflop'/c['sub_json']
            if digest(rawfile)!=c['sub_sha256']:raise ValueError('Solver SHA mismatch')
            raw=json.loads(rawfile.read_text())
            gap=raw['info'].get('gto_expl_pct')
            hero=raw['info'].get('hero_gap_pct')
            cert=versions=='gto' and isinstance(gap,(int,float)) and gap<=0.5
            if versions=='gto' and not cert:raise ValueError('Unconverged GTO')
            nodes=[node_compact(n,raw) for n in raw['nodes']]
            # Preserve unaltered two-seat combo order; source never enters
            # another pot type or SPR; board is explicit for every node.
            result.append({'source_run_id':proof['run_id'],'spot':m['spot'],
               'pot_family': '3BP' if '3' in m['spot'] else 'SRP',
               'version':versions,'flop':raw['flop'],'turn':raw.get('turn'),
               'flop_line':raw.get('line0'),'flop_root_pot_bb':c['root_pot_bb'],
               'flop_root_stack_bb':c['root_stack_bb'],
               'turn_spr':c['turn_node_spr'],'source_sha256':c['sub_sha256'],
               'gto_gap_pct':gap,'hero_gap_pct':hero,
               'nl2_pool_lock_coverage':verified.get('villain_pool_lock_coverage'),
               'hero_gain_vs_locked_pool_bb':verified.get('hero_gain_vs_locked_pool_bb'),
               'lock_frequency_proof_incomplete':not bool((verified.get('villain_pool_lock_coverage') or {}).get('fully_locked_in_sample')),
               'status':
                  'CERT_EXACT_BOARD_GTO' if cert else 'EXPERIMENTAL_POOL_LOCKED',
               'hands_by_seat':raw['hands'],'nodes':nodes})
    return {'schema':'HU_NL2_EXACT_BOARD_CFR_V1',
       'rules':'For every reached combo, only the highest-probability action survives; a second action survives iff f>=40% and >=70% of the largest. Zero reach means no action. Never generalize exact-board certificates across textures or SPR.',
       'generic_model_upgrades':0,'exact_subgame_count':len(result),
       'source_proof_run_id':proof['run_id'],'subgames':result}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--downloads',type=pathlib.Path,required=True)
    p.add_argument('--proof',type=pathlib.Path,required=True)
    p.add_argument('--out',type=pathlib.Path,required=True)
    a=p.parse_args()
    proof=json.loads(a.proof.read_text())
    if proof['errors']:raise SystemExit('Independent proof failed')
    report=build(a.downloads,proof)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps({'schema':report['schema'],'subgames':report['exact_subgame_count'],
        'exact_board_gto':sum(x['status']=='CERT_EXACT_BOARD_GTO' for x in report['subgames']),
        'model_upgrades':report['generic_model_upgrades'],'bytes':a.out.stat().st_size}))
if __name__=='__main__':main()
