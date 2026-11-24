"""Recheck both original turn policies and the same limped BB/CO deal through each modeled river entry."""
import json
from functools import lru_cache
from pathlib import Path
from zipfile import ZipFile

from hu_b739_rank108 import ACTIONS, LINE, hand_cell
from hu_b745_rank108 import PINS, SOURCE
from hu_b714_rank255_rivers import DECK, cards
from hu_sequential_cfr_reach import accepted, cardkey
from hu_b467_river_source_gate import sha

@lru_cache(maxsize=65536)
def cell(h,public):
    return hand_cell(''.join(h),public)[0]


def policies(flop):
    batch,=[k for k,v in SOURCE.items() if flop in v[-1]]
    aid,digest=PINS[flop]
    path=Path('data/solver_evidence')/f'NL2_B{batch}_R108_{flop.upper()}.zip'
    assert sha(path.read_bytes())==digest
    with ZipFile(path) as files:
        read=lambda key:json.loads(files.read(key))
        raw=files.read('boundary/result.json')
        root=json.loads(raw)
        report=read('proof.json')
        assert sha(raw)==report['boundary_source_sha256']
        for row in report['turns']:
            turn=row['turn']
            games={};jobs={}
            for ver,key in [('gto','source_gto_sha256'),('exp_oop','source_nl2_sha256')]:
                if key not in row:continue
                raw=files.read(f'{turn}/{ver}/result.json')
                assert sha(raw)==row[key]
                games[ver]=json.loads(raw);jobs[ver]=read(f'{turn}/{ver}/job.json')
            yield turn,root,games,jobs,row


def physical(root,game,turn,route,child):
    fp={n['line']:n for n in root['nodes'] if len(n['board'])==6}
    tp={n['line']:n for n in game['nodes'] if len(n['board'])==8}
    lim,=[n for n in root['nodes'] if n['line']==LINE+'/' and n['board'].endswith(turn)]
    action=ACTIONS[child['label']]
    first=tp[LINE+'/'];facing=tp[LINE+'/'+action]
    public=first['board'];assert public==facing['board']==lim['board']
    assert (first['player'],first['pot'],first['bets'],facing['player'])==(0,1000,[0,0],1)
    bet={'x':0,'b33':330,'b50':500,'b75':750}[action]
    assert (facing['pot'],facing['bets'])==(1000+bet,[bet,0])
    bb=accepted(fp[''],root['hands'],'b50') & accepted(fp['b50 r'],root['hands'],'c') & accepted(first,game['hands'],action)
    co=accepted(fp['b50'],root['hands'],'r') & accepted(facing,game['hands'],'x' if action=='x' else 'c')
    wh=[{cardkey(h) for h,w in zip(root['hands'][i],lim['wr'][i],strict=True) if w>1e-4} for i in (0,1)]
    bb={h for h in bb&wh[0] if cards(public).isdisjoint(h) and cell(h,public[:6]) in route['flop'] and cell(h,public) in child['ingress']}
    co={v for v in co&wh[1] if cards(public).isdisjoint(v)}
    return {(h,v) for h in bb for v in co if set(h).isdisjoint(v)},public


def preflight(root,games,turn,route,child):
    rows={v:physical(root,g,turn,route,child)[0] for v,g in games.items()}
    board=next(n['board'] for n in games['gto']['nodes'] if n['line']==LINE+'/')
    common=rows['gto']&rows.get('exp_oop',set())
    opts={}
    for rv in DECK:
        if rv in cards(board):continue
        possible={h for h,v in common if rv not in h and rv not in v}
        hero={h for h in possible if cell(h,board+rv) in child['river']}
        if hero:opts[rv]={(h,v) for h,v in common if h in hero and rv not in v}
    return opts,dict(gto_bb=len({h for h,v in rows['gto']}),nl2_bb=len({h for h,v in rows.get('exp_oop',set())}),
        bb=len({h for h,v in common}),pairs=len(common),rivers=len(opts),river_bb=len({h for z in opts.values() for h,v in z}))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--routes',type=Path,required=True);args=p.parse_args()
    route=json.loads(args.routes.read_bytes())
    for flop in PINS:
        for turn,root,games,jobs,row in policies(flop):
            print(flop,turn,{r:preflight(root,games,turn,route,child)[1] for r,child in route['children'].items()},flush=True)
