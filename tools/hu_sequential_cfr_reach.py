#!/usr/bin/env python3
"""Independently filter every exact-board CFR combo through the full
flop -> turn -> river action ancestry. Only maximum-frequency action
or a >=40% and >=70%-of-max alternative is allowed at EACH prior decision.

This is sequential reachability under the *already solved* CFR policy, not
a fresh subgame optimization, and it certifies no generic texture MODEL.
"""
import argparse,base64,collections,gzip,hashlib,json,pathlib

TOL=1e-7
def cardkey(x):return tuple(sorted((x[:2],x[2:4])))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for z in iter(lambda:f.read(1024*1024),b''):h.update(z)
    return h.hexdigest()
def accepted(node,hands,action):
    who=node['player']; nh=len(hands[who])
    i=node['acts'].index(action)
    w=node['w'][who];strategies=node['strat'];out=set()
    if len(w)!=nh or len(strategies)!=nh*len(node['acts']):raise ValueError('Inconsistent source strategy dimensions')
    for h,cards in enumerate(hands[who]):
        if w[h]<=1e-4:continue
        v=[max(0.,float(strategies[k*nh+h])) for k in range(len(node['acts']))]
        den=sum(v)
        if den<=0:continue
        v=[p/den for p in v];best=max(range(len(v)),key=lambda k:v[k])
        if best==i or (v[i]>=0.4-TOL and v[i]>=0.7*v[best]-TOL):
            out.add(cardkey(cards))
    return out
def mask_at_node(n,hands):
    p=n['player'];nh=len(hands[p]);out=bytearray(nh)
    if len(n['w'][p])!=nh or len(n['strat'])!=nh*len(n['acts']):
        raise ValueError('Invalid actor strat dimension')
    for h,weight in enumerate(n['w'][p]):
        if weight<=1e-4:continue
        probabilities=[max(0.,float(n['strat'][i*nh+h])) for i in range(len(n['acts']))]
        den=sum(probabilities)
        if den<=0:continue
        probabilities=[v/den for v in probabilities]
        best=max(range(len(probabilities)),key=lambda i:probabilities[i])
        allowed=[best]+[i for i,pct in enumerate(probabilities)
            if i!=best and pct>=0.4-TOL and pct>=0.7*probabilities[best]-TOL]
        out[h]=sum(1<<i for i in allowed)
    return out
def game_reach(fr,sub):
    line0=sub['line0']
    flopboard=next(n['board'] for n in fr['nodes'] if len(n['board'])==6)
    flop_index={(n['line'],n['board']):n for n in fr['nodes'] if len(n['board'])==6}
    index={(n['line'],n['board']):n for n in sub['nodes']}
    cache={};nodes={};stats=collections.Counter()
    def qualifying(node,orig,action):
        k=(orig,node['line'],node['board'],node['player'],action)
        if k not in cache:
            cache[k]=accepted(node,fr['hands'] if orig=='flop' else sub['hands'],action)
        return cache[k]
    for n in sub['nodes']:
        board=n['board'];actor=n['player'];chunks=n['line'].split('/')
        if chunks[0]!=line0 or len(board) not in (8,10):
            raise ValueError('Unexpected source action/card lineage '+n['line']+' / '+board)
        initial=mask_at_node(n,sub['hands'])
        own=list(zip(sub['hands'][actor],initial))
        ancestors=[]
        flop_actions=line0.split()
        for i,required in enumerate(flop_actions):
            label=' '.join(flop_actions[:i])
            parent=flop_index.get((label,flopboard))
            if parent is None:raise ValueError('Missing exact flop parent '+label)
            if parent['player']==actor:ancestors.append((parent,'flop',required))
        turn_actions=chunks[1].split() if len(chunks)>1 else []
        for i,required in enumerate(turn_actions):
            label=line0+'/'+' '.join(turn_actions[:i])
            parent=index.get((label,board[:8]))
            if parent is None:raise ValueError('Missing turn parent '+label)
            if parent['player']==actor:ancestors.append((parent,'turn',required))
        if len(board)==10 and len(chunks)>2:
            river_actions=chunks[2].split()
            for i,required in enumerate(river_actions):
                label=line0+'/'+chunks[1]+'/'+' '.join(river_actions[:i])
                parent=index.get((label,board))
                if parent is None:raise ValueError('Missing river parent '+label)
                if parent['player']==actor:ancestors.append((parent,'river',required))
        eligible=None
        for parent,origin,required in ancestors:
            permitted=qualifying(parent,origin,required)
            eligible=permitted if eligible is None else eligible & permitted
        output=bytearray(initial)
        if eligible is not None:
            for i,(cards,_) in enumerate(own):
                if cardkey(cards) not in eligible:output[i]=0
        source_count=sum(bool(x) for x in initial)
        reached=sum(bool(x) for x in output)
        if reached>source_count:raise ValueError('Sequentially reached more hands than source')
        stats['nodes']+=1
        stats['source_actor_combo_nodes']+=source_count
        stats['sequential_actor_combo_nodes']+=reached
        stats['removed_by_parent_action_policy']+=source_count-reached
        nodes['|'.join((board,n['line'],str(actor)))]={'mask':base64.b64encode(output).decode('ascii'),
            'count':reached,'parent_actor_decisions':len(ancestors)}
    return nodes,stats

def compatible_node_reach(flop_root, subgame, node, actor_reach):
    """Restrict an actor mask to deals where both players could take every prior action."""
    board = node["board"]
    actor = node["player"]
    opponent = 1 - actor
    public = {board[i:i+2] for i in range(0, len(board), 2)}
    streets = node["line"].split("/")
    if len(streets) != len(board) // 2 - 2 or streets[0] != subgame["line0"]:
        raise ValueError("Source board and action history disagree")
    hands = subgame["hands"]
    if len(node["w"][opponent]) != len(hands[opponent]):
        raise ValueError("Opponent source weight dimension mismatch")
    villains = {cardkey(hand) for hand, weight in zip(hands[opponent], node["w"][opponent])
                if weight > 1e-4 and public.isdisjoint(cardkey(hand))}
    for street, history in enumerate(streets):
        game = flop_root if street == 0 else subgame
        street_board = board[:6 + 2 * street]
        parents = {n["line"]: n for n in game["nodes"] if n["board"] == street_board}
        actions = history.split()
        for i, action in enumerate(actions):
            prefix = "/".join(streets[:street] + [" ".join(actions[:i])])
            parent = parents[prefix]
            if parent["player"] == opponent:
                villains &= accepted(parent, game["hands"], action)

    mask = bytearray(base64.b64decode(actor_reach["mask"], validate=True))
    if len(mask) != len(hands[actor]) or sum(map(bool, mask)) != actor_reach["count"]:
        raise ValueError("Actor sequential mask dimension/count mismatch")

    def blocker_counts(combos):
        return collections.Counter(card for combo in combos for card in combo)

    def disjoint_count(hand, combos, counts):
        first, second = hand
        return len(combos) - counts[first] - counts[second] + (hand in combos)

    villain_counts = blocker_counts(villains)
    heroes = set()
    pairs = 0
    for i, hole in enumerate(hands[actor]):
        if not mask[i]:
            continue
        hand = cardkey(hole)
        compatible = disjoint_count(hand, villains, villain_counts) if public.isdisjoint(hand) else 0
        if compatible:
            heroes.add(hand)
            pairs += compatible
        else:
            mask[i] = 0
    if len(heroes) != sum(map(bool, mask)):
        raise ValueError("Duplicate private hands in source")
    hero_counts = blocker_counts(heroes)
    opponent_count = sum(disjoint_count(hand, heroes, hero_counts) > 0 for hand in villains)
    return dict(actor_reach, mask=base64.b64encode(mask).decode(), count=len(heroes),
                compatible_opponent_combos=opponent_count, compatible_hole_card_pairs=pairs)

def compile_batch(downloads,proof):
    validated={(art['artifact'],c['source_sha256']) for art in proof['artifacts'] for c in art['cases']}
    out={};tot=collections.Counter();artifact_count=0
    for ad in sorted(downloads.iterdir()):
        if not ad.is_dir() or not ad.name.startswith('nl2-stage2-') or '-verified-provenance' in ad.name:continue
        ms=list((ad/'evidence').glob('*.json'))
        if len(ms)!=1:raise ValueError('Missing unique source manifest '+ad.name)
        m=json.loads(ms[0].read_text())
        if m['failures']:raise ValueError('Source solver failed '+ad.name)
        artifact_count+=1
        for c in m['cases']:
            if (ad.name,c['sub_sha256']) not in validated:
                raise ValueError('No independent source proof for '+ad.name)
            root=ad/'solver/postflop'
            fp=root/c['flop_json'];sub=root/c['sub_json']
            if sha(fp)!=c['flop_sha256'] or sha(sub)!=c['sub_sha256']:
                raise ValueError('SHA mismatch of original CFR data')
            fr=json.loads(fp.read_text());raw=json.loads(sub.read_text())
            if raw.get('line0')!=c['line'] or raw.get('turn')!=c['turn']:
                raise ValueError('No exact source line/board')
            nodes,stats=game_reach(fr,raw)
            if c['sub_sha256'] in out:raise ValueError('Duplicate source SHA within batch')
            out[c['sub_sha256']]={'source_run_id':proof['run_id'],'spot':m['spot'],'version':m['version'],
              'flop':c['flop'],'turn':c['turn'],'source_sha256':c['sub_sha256'],
              'status':'EXACT_BOARD_SEQUENTIAL_COMBO_GATE_ONLY_NOT_NEW_GTO_SOLVE',
              'nodes':nodes,'stats':dict(stats)}
            tot.update(stats);tot['source_subgames']+=1
    if artifact_count!=proof['artifact_count'] or tot['source_subgames']!=proof['solved_subgames']:
        raise ValueError('Artifact or subgame count does not reconcile')
    return {'schema':'HU_NL2_SEQUENTIAL_REACH_OVERLAY_V1',
      'source_proof_run_id':proof['run_id'],
      'generic_model_CERT':0,
      'rules':'Only highest-frequency action; second action allowed when f>=40% and >=70% of highest. Intersect all actor-specific prior actions on exact flop/turn/river plus card blockers. EV is not re-solved.',
      'aggregate_stats':dict(tot),
      'subgames_by_source_sha256':out}
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--downloads',type=pathlib.Path,required=True)
    p.add_argument('--proof',type=pathlib.Path,required=True)
    p.add_argument('--out',type=pathlib.Path,required=True)
    a=p.parse_args()
    source=json.loads(a.proof.read_text())
    if source['errors']:raise ValueError('Independently verified archive proof failed')
    data=compile_batch(a.downloads,source)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n').encode()
    a.out.write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))
    assert gzip.decompress(a.out.read_bytes())==raw
    print(json.dumps({'source_run':source['run_id'],'stats':data['aggregate_stats'],
      'source_cases':len(data['subgames_by_source_sha256']),
      'compressed_bytes':a.out.stat().st_size},ensure_ascii=False))
if __name__=='__main__':main()
