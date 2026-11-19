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

def node_compact(node,raw):
    player=node['player']
    hands=raw['hands'][player]
    w=node['w'][player]
    f=node['strat'];act=node['acts'];nh=len(hands)
    if len(w)!=nh or len(f)!=nh*len(act):raise ValueError('Malformed per-combo source')
    masks=bytearray(nh)
    sums=[0.0]*len(act);total=0.0;live=mixed=0
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
        if max(kept)>7:raise ValueError('At most 8 source actions supported')
        masks[h]=sum(1<<i for i in kept)
        live+=1;mixed+=int(len(kept)>1)
        total+=weight
        for i,p in enumerate(prob):sums[i]+=weight*p
    return {'line':node['line'],'board':node['board'],'acting_seat':player,
       'actions':act,'pot_units':node['pot'],'bets_units':node['bets'],
       'remaining_stack_units':raw['stack']-max(node['bets']),
       'node_spr':round((raw['stack']-max(node['bets']))/node['pot'],6),
       'reachable_combos':live,'near_mixed_combos':mixed,
       'reach_weighted_action_pct':{a:round(100*s/total,3) if total else 0.
                                     for a,s in zip(act,sums)},
       'eligibility_encoding':'base64(uint8 per combo in hands[acting_seat], bit(i) for eligible action i, zero if absent)',
       'eligible_action_masks_b64':base64.b64encode(masks).decode('ascii'),
       'medium_50pct_eligible_combos':sum(bool(x&(1<<act.index('b50'))) for x in masks)
                                           if 'b50' in act else 0}

def build(root,proof):
    all_verified=set()
    for a in proof['artifacts']:
        for c in a['cases']:
            all_verified.add((a['artifact'],c['source_sha256'],c['flop'],c['line'],c['turn']))
    result=[]
    for ad in sorted(root.iterdir()):
        if not ad.is_dir() or not ad.name.startswith('nl2-stage2-'):continue
        ms=list((ad/'evidence').glob('*.json'))
        if len(ms)!=1:raise ValueError('Exactly one batch manifest required: '+ad.name)
        m=json.loads(ms[0].read_text())
        if m['failures']:raise ValueError('Source solver reported failure')
        versions=m['version']
        for c in m['cases']:
            if (ad.name,c['sub_sha256'],c['flop'],c['line'],c['turn']) not in all_verified:
                raise ValueError('No independently verified proof: '+ad.name+'/'+c['line'])
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
               'gto_gap_pct':gap,'hero_gap_pct':hero,'status':
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
