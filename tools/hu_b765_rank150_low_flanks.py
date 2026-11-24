"""Check matched A-low suited draw histories on two original paired-three limped flops."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile

import hu_b754_rank150_paired_six as base
import hu_b724_rank150_rivers as native
from hu_b467_river_source_gate import json_bytes,sha

WORKER='tools/hu_b765_rank150_low_flanks.py'
BASE_WORKER='tools/hu_b754_rank150_paired_six.py'
BASE_BLOB='fc49ca7aff86b3432f389921bb74190fffff94d3'
CASES={'9s9h3s':[('2d','As5s','2h'),('2h','As5s','3c'),('4d','As5s','4c')],
       'TdTc3d':[('2c','Ad5d','2h'),('2h','Ad4d','3c'),('4c','Ad5d','4h')]}
ANCHORS={'9s9h3s':{'5sAs'},'TdTc3d':{'4dAd','5dAd'}}
HISTORICAL=base.HISTORICAL|set(base.CASES)
OLD={'9s9h3s':('NL2_B724_R150_9C9H6C.zip','6c9c9h2d2h',{'5cAc':{'4hKh'}}),
     'TdTc3d':('NL2_B743_R150_TSTC6S.zip','6sTcTs2c3d',{'4sAs':{'AcAd','AcAh','JdKd','JdKh','JhKd','JhKh'},
                                                      '5sAs':{'AcAd','AcAh','JdKd','JdKh','JhKd','JhKh'}})}
OLD_READER=base.observations


def hand_pairs(root,game,turn,public):
    """Use the same BB through its flop check-call, turn check and river check."""
    r={n['line']:n for n in root['nodes'] if len(n['board'])==6}
    p,=[n for n in root['nodes'] if n['line']=='x b33 c/' and n['board'].endswith(turn)]
    assert p['board']==public[:8]
    tn={n['line']:n for n in game['nodes'] if n['board']==public[:8]}
    rn={n['line']:n for n in game['nodes'] if n['board']==public}
    final=rn[native.LINE];assert final['player']==1 and final['pot']==416 and final['bets']==[0,0]
    bb=native.accepted(r[''],root['hands'],'x')&native.accepted(r['x b33'],root['hands'],'c')&native.accepted(tn['x b33 c/'],game['hands'],'x')&native.accepted(rn['x b33 c/x x/'],game['hands'],'x')
    co=native.accepted(r['x'],root['hands'],'b33')&native.accepted(tn['x b33 c/x'],game['hands'],'x')&native.accepted(final,game['hands'],'x')
    live=[{native.cardkey(h) for h,w in zip(root['hands'][i],p['wr'][i],strict=True) if w>1e-4 and native.cards(public).isdisjoint(native.cardkey(h))} for i in (0,1)]
    weighted={native.cardkey(h) for h,w in zip(game['hands'][0],final['w'][0],strict=True) if w>1e-4}
    return co&live[1],bb&live[0]&weighted


def original_pairs(flop,evidence):
    name,public,expected=OLD[flop];raw=(evidence/name).read_bytes()
    with ZipFile(evidence/name) as z:
        proof=json.loads(z.read('proof.json'));target=proof['selected'];turn=target['turn'];assert target['public_board']==public
        root=json.loads(z.read('flop/result.json'))
        record,=[r for r in proof['turns'] if r['turn']==turn]
        assert record['common'][public]==sorted(expected)
        verified={}
        for ver in ('gto','exp_ip'):
            game_raw=z.read(turn+'-'+ver+'/result.json')
            assert sha(game_raw)==record['policies'][ver]['source_sha256']
            co,bb=hand_pairs(root,json.loads(game_raw),turn,public)
            verified[ver]={(''.join(h),''.join(v)) for h in co if ''.join(h) in expected for v in bb if set(h).isdisjoint(v)}
        jointly=verified['gto']&verified['exp_ip']
        assert jointly=={(h,v) for h,vs in expected.items() for v in vs}
    return dict(source_flop=proof['flop'],public_board=public,archive=name,archive_sha256=sha(raw),
        original_two_policy_deals=sorted([list(v) for v in jointly]))


def static(flop,route,manifest):
    opp={'9s9h3s':'4hKh','TdTc3d':'JhKh'}[flop]
    out=[]
    for turn,hero,river in CASES[flop]:
        public=flop+turn+river
        assert len(native.cards(public+hero+opp))==9
        cells=[native.hand_cell(hero,public[:n]) for n in (6,8,10)]
        assert cells[0][0] in route['flop'] and cells[1][0] in route['turn'] and route['river'][cells[2][0]]=='過'
        weights=[manifest['preflop_ranges'][key][base.limp.range_class(h)] for key,h in [('ip_169',hero),('oop_169',opp)]]
        assert min(weights)>0
        out.append(dict(turn=turn,river=river,hero=hero,villain=opp,classes=cells,preflop_weights=weights))
    return out


def parent_gate(root,turn,route):
    boundary,earlier,_,diagnostic=native.parent_gate(root,turn,route)
    flop,=[f for f in CASES if native.cards(f)==native.cards(root['flop'])]
    targets=ANCHORS[flop]
    eligible={r:sorted(set(hands)&targets) for r,hands in earlier.items() if targets.intersection(hands)}
    priority=[r for r in eligible if r[0] in (turn[0],'3') and r[1]!=flop[1]]
    rest=[r for r in eligible if r not in priority];slots=min(len(rest),12-len(priority));assert slots>=0
    extra=rest[:1] if slots==1 else [rest[round(i*(len(rest)-1)/(slots-1))] for i in range(slots)]
    rivers=priority+extra
    assert len(rivers)==len(set(rivers))==min(12,len(eligible))
    diagnostic.update(preregistered_hero_hands=sorted(targets),eligible_named_hand_rivers=len(eligible),
        named_heroes_in_root_and_ui=sorted({h for rows in eligible.values() for h in rows}),
        river_sampling='TURN_OR_THREE_PAIR_OFF_DRAW_SUIT_THEN_EVEN_SPREAD')
    return boundary,eligible,rivers,diagnostic


def run(args):
    assert base.limp.git_blob(BASE_WORKER)==BASE_BLOB
    assert len({base.suit_isomorphism_class(f) for f in CASES})==2
    previous=base.original_observations(args.prior_evidence)
    prior_deals=original_pairs(args.flop,args.prior_evidence)
    accept={}
    def observed(root,sub,turn,rivers,eligible,route):
        rows=OLD_READER(root,sub,turn,rivers,eligible,route)
        locked=bool(sub['info'].get('lock_stats'));seen=accept.setdefault(turn,{})
        for public,item in rows.items():
            co,bb=hand_pairs(root,sub,turn,public)
            present={''.join(h):{''.join(v) for v in bb if set(h).isdisjoint(v)} for h in co if ''.join(h) in item['hands']}
            if not locked:seen[public]=present
            else:
                assert public in seen
                present={h:vs&seen[public].get(h,set()) for h,vs in present.items()}
            keep={h:vs for h,vs in present.items() if vs}
            item['hands']={h:item['hands'][h] for h in sorted(keep)}
            item['private_opponent_witnesses']={h:dict(first=min(vs),count=len(vs)) for h,vs in sorted(keep.items())}
        return rows
    base.WORKER=WORKER;base.CASES=CASES;base.HISTORICAL=HISTORICAL;base.static_route=static;base.parent_gate=parent_gate;base.observations=observed
    base.run(args)
    if args.preflight or args.checkpoint_only:return
    path=args.output/'proof.json';claim=json.loads(path.read_bytes())
    assert claim['source_worker_blob']==base.limp.git_blob(WORKER) and claim['selection_origin']==previous
    claim.update(schema='NL2_B765_R150_PAIRED_LOW_FLANK_ORIGINAL_V1',source_worker_parent_blob=BASE_BLOB,
        original_identical_two_policy_deals=prior_deals,named_hero_preregistration=sorted(ANCHORS[args.flop]),
        observed_same_opponent_per_common_hand=True)
    for t in claim['turns']:
        if not t['preregistered_rivers']:t['negative_reason']='NO_PREREGISTERED_NAMED_CO_CLOSES_FLOP_WITH_COMPATIBLE_BB_AND_CURRENT_UI'
        for public,hands in t['common'].items():
            assert all(h in ANCHORS[args.flop] and t['policies']['exp_ip']['boards'][public]['private_opponent_witnesses'][h]['count']>0 for h in hands)
    path.write_bytes(json_bytes(claim))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('solver','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--prior-evidence',type=Path,default=Path('data/solver_evidence'));p.add_argument('--flop',choices=CASES,required=True)
    p.add_argument('--driver',type=Path);p.add_argument('--checkpoint',type=Path);p.add_argument('--checkpoint-only',action='store_true')
    p.add_argument('--preflight',action='store_true');run(p.parse_args())
