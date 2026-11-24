"""Screen rank 46's three barrel children using B755's original paired turn strategies."""
import argparse
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile

from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b568_caller_rivers import hand_cell
from hu_b714_rank255_rivers import cards, DECK
import hu_b755_rank151 as original
from hu_sequential_cfr_reach import accepted, cardkey

RUN=45337049683
HEAD='26f8c0095103994c3078d778d141ca420f216907'
PINS={
    '7h6h4c':(14894716547,'c5ff73ce0cd8dcda8fce5ba5f301dd21954ac82896f635735aeccbc000eb760b'),
    '7h6d4s':(14894721279,'14b1019f010a403db8fdfa4942128f17e17d36b771118cac34670e4d97dd7589'),
    '7s5h3d':(14894831955,'721db42b6e5d6bf62527d02cb2d84eadb9923bae8fd2d99dc301c4906f5f88f6')
}
ACTIONS={199:'b33',200:'b50',201:'b75'}
ROUTES=Path(__file__).with_name('hu_b759_rank46_barrel_routes.cjs')


def load_pair(archive,entry):
    result={}
    turn=entry['turn']
    for mode,record in entry['policies'].items():
        path=turn+'-'+mode+'/'
        raw=archive.read(path+'result.json')
        job=archive.read(path+'job.json')
        assert sha(raw)==record['source_sha256'] and sha(job)==record['job_sha256']
        game=json.loads(raw);j=json.loads(job)
        assert (game['pot'],game['stack'],j['line0'],j['turn'])==(500,9775,['x','b50','c','/'],turn)
        assert game['info']['gto_expl_pct']<=.5
        if mode=='exp_ip':
            assert j['hero']==1 and j['locks'] and game['info']['hero_gap_pct']<=.5
            assert record['measured_lock_application']['marginal_targets']
        else:
            assert not j.get('locks') and not game['info'].get('lock_stats')
        result[mode]=game
    assert set(result)=={'gto','exp_ip'}
    return result


def check(parent,root_bb,root_co,game,mode,rank,route):
    turn_nodes={n['line']:n for n in game['nodes'] if len(n['board'])==8}
    line='x b50 c/'
    act=ACTIONS[rank]
    first,bettor,facing=[turn_nodes[k] for k in (line,line+'x',line+'x '+act)]
    assert first['board']==bettor['board']==facing['board']==parent['board']
    assert (first['player'],bettor['player'],facing['player'],first['pot'],bettor['pot'])==(0,1,0,500,500)
    amount=facing['bets'][1]
    assert (facing['bets'][0],facing['pot'],amount)==(0,500+amount,{199:165,200:250,201:375}[rank])
    pot=500+2*amount;stack=9775-amount
    assert abs(stack/pot/route['model_spr']-1)<=.05
    public=parent['board']
    live=[{cardkey(h) for h,w in zip(game['hands'][i],facing['w'][i],strict=True) if w>1e-4 and cards(public).isdisjoint(cardkey(h))} for i in (0,1)]
    bb=root_bb & live[0] & accepted(first,game['hands'],'x') & accepted(facing,game['hands'],'c')
    co=root_co & live[1] & accepted(bettor,game['hands'],act)
    actual={h for h in co if hand_cell(''.join(h),public[:6])[0] in route['flop'] and hand_cell(''.join(h),public)[0] in route['turn'] and any(set(h).isdisjoint(v) for v in bb)}
    river_line=line+'x '+act+' c/'
    extracted=[n['board'] for n in game['nodes'] if n['line']==river_line or n['line']==river_line+'x']
    return actual,bb,dict(mode=mode,turn_displayed_co_with_bb=len(actual),bb_check_call=len(bb),
                         sampled_river_nodes=extracted,native_river_pot=pot,native_river_stack=stack,native_river_spr=stack/pot)


def one_root(flop,path,route):
    aid,digest=PINS[flop];assert sha(path.read_bytes())==digest
    with ZipFile(path) as z:
        root=json.loads(z.read('flop/result.json'));claim=json.loads(z.read('proof.json'))
        frozen,_,_,pin,_=original.source(flop)
        bounds=original.compare_extraction(frozen,root,original.CASES[flop])
        assert claim['source']==pin and sha(z.read('flop/result.json'))==claim['root_sha256']
        fs={n['line']:n for n in root['nodes'] if len(n['board'])==6}
        assert set(fs['x']['acts'])=={'x','b50'}
        root_bb=accepted(fs[''],root['hands'],'x')&accepted(fs['x b50'],root['hands'],'c')
        root_co=accepted(fs['x'],root['hands'],'b50')
        out=[]
        for entry in claim['turns']:
            t=entry['turn'];parent=bounds[t];public=parent['board'];games=load_pair(z,entry)
            live=[{cardkey(h) for h,w in zip(root['hands'][i],parent['wr'][i],strict=True) if w>1e-4} for i in (0,1)]
            for rank,act in ACTIONS.items():
                cfg=route[str(rank)]
                policies=[check(parent,root_bb&live[0],root_co&live[1],games[m],m,rank,cfg) for m in ('gto','exp_ip')]
                (gh,gv,gr),(eh,ev,er)=policies
                both=gv&ev
                heroes={h for h in gh&eh if any(set(h).isdisjoint(v) for v in both)}
                rivers={}
                for r in DECK:
                    if r in cards(public):
                        continue
                    actual={}
                    for h in sorted(heroes):
                        cell=hand_cell(''.join(h),public+r)[0]
                        if r in h or cell not in cfg['river']:continue
                        opponent=next((v for v in sorted(both) if set(h).isdisjoint(v) and r not in v),None)
                        if opponent:
                            actual[''.join(h)]=''.join(opponent)
                    if actual:rivers[r]=actual
                out.append(dict(rank=rank,turn=t,root_boundary_sha256=sha(compact(parent)),prefix='x b50 c/x '+act+' c',
                    policies=[gr,er],same_co_and_bb_before_river=len(heroes),eligible_rivers=rivers,
                    full_river_policy_verified=False))
    return dict(flop=flop,artifact_id=aid,archive_sha256=digest,screened=out)


def main():
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument('--archives',type=Path,default=Path('data/solver_evidence'));args.add_argument('--output',type=Path,required=True)
    a=args.parse_args()
    route=json.loads(subprocess.check_output(['node',str(ROUTES)]))
    status=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records']
    for rank in ACTIONS:
        model=status[route[str(rank)]['model_id']]
        assert (model['frequency_rank'],model['assumed_model_node_spr'])==(rank,route[str(rank)]['model_spr'])
    check83=json.loads(subprocess.check_output(['node','tools/hu_rank83_ingress_price_audit.cjs']))
    prices={str(x['flop_bet_pct']):x['actual_spr'] for x in check83['ingress']}
    assert set(prices)=={'50','75','100'} and not any(x['passes_current_spr_gate'] for x in check83['ingress'])
    workers=[]
    for f,(aid,d) in PINS.items():
        path=a.archives/(str(aid)+'.zip')
        if not path.exists():path=a.archives/('NL2_B755_R151_'+f.upper()+'.zip')
        workers.append(one_root(f,path,route))
    eligible={rank:[(w['flop'],t['turn'],len(t['eligible_rivers'])) for w in workers for t in w['screened'] if t['rank']==rank and t['eligible_rivers']] for rank in ACTIONS}
    assert eligible=={199:[('7h6d4s','2c',4),('7h6d4s','8d',6)],200:[],201:[]}
    assert all(not e['sampled_river_nodes'] for w in workers for t in w['screened'] for e in t['policies'])
    historical={}
    for rank,filename in [(199,'nl2_hu_multiboard_status_v34_b190_rank199_202.json'),(201,'nl2_hu_multiboard_status_v35_b193_rank201.json')]:
        p=Path('data')/filename;old=json.loads(p.read_bytes())['records'][route[str(rank)]['model_id']]
        actual=[dict(flop=b['flop'],turn=b['turn'],line=b['actual_exact_action_line'],run=b['source_run_id']) for b in old['certified_3_to_5_exact_flop_boards']]
        assert len(actual)==3 and all(b['line'].split('/')[0]=='x b33 c' for b in actual)
        historical[rank]=dict(path=str(p),sha256=sha(p.read_bytes()),cases=actual,required_flop_line='x b50 c')
    for filename in ('nl2_hu_b384_rank200_two_new_true_source_strict_pairs.json','nl2_hu_b422_rank200_three_gto_first.json','nl2_hu_b432_rank200_two_missing_gto_flops.json'):
        p=Path('data')/filename;o=json.loads(p.read_bytes())
        positive=o.get('distinct_new_flops_with_true_positive_pairs',o.get('positive_distinct_flops_by_model',{}).get('200'))
        assert positive==[]
        historical.setdefault(200,[]).append(dict(path=str(p),sha256=sha(p.read_bytes()),original_recorded_positive_flops=positive))
    out=dict(source_run=RUN,source_head=HEAD,rank83=dict(actual_ingress_count=len(check83['ingress']),prices_by_flop_bet_percent=prices,
        source_hero_examples=check83['non_allin_example_count'],affected_ranks=[m['rank'] for m in check83['affected_models']],eligible_native_prices=0),
        actual_render=route,workers=workers,historical_originals=historical,eligible_flop_turns_by_rank=eligible,frozen_flop_menu='50% only',
        new_solves=0,new_locks=0,medium_assessments=0,certified_flops_added=0)
    a.output.write_bytes(json_bytes(out))
    print(json.dumps(eligible))


if __name__=='__main__':
    main()
