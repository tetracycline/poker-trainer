"""Replay two archived UTG check-calls and the next frozen half-pot UTG–CO flop."""
import argparse
import base64
import gzip
import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from hu_b463_rank45_gate import RUST, SOLVER
from hu_b467_river_source_gate import EVIDENCE, compact, json_bytes, sha
from hu_b470_rank73_new_rivers import original
from hu_b483_locked_medium import POOL, RANGES, PIPELINE
from hu_b492_half_pot_leads import zip_payload
from hu_b518_rank220_native import measured_rates
from hu_b527_checked_barrels import COLUMNS, board_row, hcls
from hu_b538_utg_check_calls import RANGE_SHA, VERSIONS, LINE
from hu_b545_sb_half_pot import parent_entries
from hu_board_reach_corrections import source_key
from hu_checked_gto_boundary import audit_decision
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey, game_reach, compatible_node_reach

DATA=Path('data')
MODEL='ln-opfr-t_model-19umlco'
NEW='As9d4c'
PRIOR=DATA/'nl2_hu_b538_utg_check_calls.json'
PRIOR_RUN=45119866932
TURNS=('6c','Jc')


def code_for(version):
    return f'B563_R68_{NEW.upper()}_{version.upper()}'


def capture(solver, folder):
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
    for v in VERSIONS:
        m=folder/f'{NEW}-{v}.json'
        entries=parent_entries(solver,NEW,m)
        if v!='gto':
            entries[f'trainer/evidence/{NEW}-{v}.json']=entries.pop(f'trainer/evidence/{NEW}-gto.json')
        zip_payload(EVIDENCE/f'NL2_{code_for(v)}.zip',entries)


def check_boundary(source, flop, turn):
    root,sub,m=source['root'],source['subgame'],source['manifest']
    rj=source['root_job']
    assert sha(compact(root))==source['root_sha256']==m['file_flop_sha256']
    assert (m['spot'],m['pool_source_sha256'],m['solver_pin'],m['solver_ranges_sha256'])==('UTG_CO',POOL,PIPELINE,RANGES)
    assert m['flop_size_profile']=='utg-50-only' and m['allow_turn_lead'] and m['restricted_tree_assumption']
    assert (root['flop'],root['pot'],root['stack'],rj['flop_oop'],rj['flop_ip'])==(flop,650,9750,'50%','50%')
    assert sha(compact([rj['oop'],rj['ip']]))==RANGE_SHA[source['version']]
    if sub is None:
        return
    assert sha(compact(sub))==source['source_sha256']
    j=source['subgame_job']
    assert (sub['flop'],sub['turn'],sub['pot'],sub['stack'],sub['line0'])==(flop,turn,1300,9425,LINE)
    assert j['line0']==['x','b50','c','/'] and not j['root_no_bet']
    assert j['turn_ip']==j['turn_oop']=='50%,100%'
    parent,=(n for n in root['nodes'] if n['line']==LINE+'/' and n['board'].endswith(turn))
    assert (parent['bets'],parent['pot'])==([325,325],1300)
    for seat,key in enumerate(('oop_w','ip_w')):
        assert j[key]==[[h,w] for h,w in zip(root['hands'][seat],parent['wr'][seat],strict=True) if w>1e-4]
    for line,who,pot,bets,action in [('',0,650,[0,0],'x'),('x',1,650,[0,0],'b50'),('x b50',0,975,[0,325],'c')]:
        n,=(n for n in root['nodes'] if n['line']==line and len(n['board'])==6)
        assert (n['player'],n['pot'],n['bets'])==(who,pot,bets) and action in n['acts']


def previous(pin):
    code=pin['archive_code']
    packed=(EVIDENCE/f'NL2_{code}.json.gz').read_bytes()
    assert sha(packed)==pin['archive_sha256']
    d=json.loads(gzip.decompress(packed))
    assert d['run_id']==PRIOR_RUN
    pair=d['source_arrays']
    assert [s['version'] for s in pair]==list(VERSIONS)
    for s in pair:
        s.update(archive_code=code,archive_sha256=sha(packed),run=PRIOR_RUN)
    return pair


def fresh(folder, turn, run):
    pair=[]
    for v in VERSIONS:
        code=code_for(v)
        path=EVIDENCE/f'NL2_{code}.zip'
        base=folder/f'NL2-B563-{NEW}-{v}'
        if not base.exists():
            with ZipFile(path) as z:
                for name in z.namelist():
                    assert not Path(name).is_absolute() and '..' not in Path(name).parts
                z.extractall(base)
        s=original(folder,NEW,turn,v,batch='B563',spot='UTG_CO',flop_line=LINE,flop_policy='checked-b50only',
                   turn_policy='checkcheck',turn_extract='x x',root_pot=650,root_stack=9750,flop_profile='utg-50-only',frozen_turns=TURNS)
        s.update(archive_code=code,archive_sha256=sha(path.read_bytes()),run=run)
        pair.append(s)
    return pair


def witness_policies(source,row,routes):
    sub=source['subgame'];b=row['public_board']
    n,=(n for n in sub['nodes'] if (n['board'],n['line'],n['player'])==(b,LINE+'/',0))
    assert n['acts']==row['source_actions'] and n['pot']==1300 and n['bets']==[0,0] and {'x','b50','b100'}<=set(n['acts'])
    all_hands=sub['hands'][0]
    masks=base64.b64decode(row['compatible_action_mask_b64'],validate=True)
    out={}
    for i,(hole,mask) in enumerate(zip(all_hands,masks,strict=True)):
        if not mask:
            continue
        h=''.join(cardkey(hole));fc,tc=hcls(h,b[:6]),hcls(h,b)
        if fc not in COLUMNS or tc not in COLUMNS:
            continue
        fk=f'{board_row(b[:6])}:{COLUMNS.index(fc)}';tk=f'{board_row(b)}:{COLUMNS.index(tc)}'
        if fk not in routes['flop'] or tk not in routes['turn']:
            continue
        acts=n['acts'];weights=[max(0.,n['strat'][j*len(all_hands)+i]) for j in range(len(acts))]
        total=sum(weights)
        assert total>0
        out[h]=dict(hand=h,flop_class=fc,turn_class=tc,flop_texture=board_row(b[:6]),turn_texture=board_row(b),
                    displayed_suggestion=routes['turn'][tk],native=dict(action_order=acts,accepted_mask=mask,
                    accepted_actions=[a for j,a in enumerate(acts) if mask & (1<<j)],
                    strategy={a:round(w/total,7) for a,w in zip(acts,weights,strict=True)}))
    return out


def opponent(e,b,pool):
    sub=e['subgame'];rules=e['manifest']['locks'];masks=game_reach(e['root'],sub)[0];details=[]
    for game,job,line in [(e['root'],e['root_job'],'x'),(sub,e['subgame_job'],LINE+'/b50'),
                          (sub,e['subgame_job'],LINE+'/b100'),(sub,e['subgame_job'],LINE+'/x')]:
        assert job['hero']==0
        r=next(r for r in rules if re.search(r['pat'],line))
        rule=next(r for r in job['locks'] if re.search(r['pat'],line))
        assert rule['pat']==r['pat']
        n,=(n for n in game['nodes'] if n['line']==line and n['board']==(b if game is sub else b[:6]))
        assert n['player']==1 and len(n['acts'])>=2
        stat=game['info']['lock_stats'][r['pat']]
        obs=dict(line=line,scope=r['scope'],source=r['source'],pattern=r['pat'],n=r['n'],applied_nodes=stat['nodes'],
                 native_rule=rule,applied_pattern_fold=stat['fold'],applied_pattern_aggressive=stat['agg'])
        if line=='x':
            counted=pool['postflop_HU']['SRP_float_bet_when_pfr_checks_oop']
            assert r['source']=='SRP_float_bet_when_pfr_checks_oop' and r['n']==counted['n'] and rule['bet']==counted['pct']/100
        else:
            obs['compatible_hole_card_pairs']=compatible_node_reach(e['root'],sub,n,masks[f'{b}|{line}|1'])['compatible_hole_card_pairs']
            if line.endswith('b50') or line.endswith('b100'):
                size=650 if line.endswith('b50') else 1300
                bucket='34-55%' if size==650 else '81-110%'
                counted=pool['HU_facing_bet']['2']['by_size'][bucket]
                assert (n['pot'],n['bets'])==(1300+size,[size,0])
                assert r['source']==f'NL2.HU_facing_bet[2].by_size[{bucket}]' and r['n']==counted['n']
                assert (rule['fold'],rule['raise'])==(counted['fold']/100,counted['raise']/100)
            else:
                assert r['n']==0 and r['scope']=='ASSUMED_HISTORY_RATE_OR_SIZE' and rule['bet']==.45
        details.append(obs)
    assert details[0]['applied_nodes']>0
    return details


def evaluate(pair, flop, turn, routes, model, pool):
    for s in pair:
        check_boundary(s,flop,turn)
    if any(s['subgame'] is None for s in pair):
        return None,dict(status='MISSING_PRICED_PARENT')
    for s in pair:
        for g in (s['root'],s['subgame']):
            if not 0<=g['info']['gto_expl_pct']<=.5 or (s['version']!='gto' and not 0<=g['info']['hero_gap_pct']<=.5):
                return None,dict(status='OUTSIDE_CONVERGENCE')
    g,e=pair
    public,=(n['board'] for n in g['subgame']['nodes'] if n['line']==LINE+'/')
    rows=[audit_decision(s,public,LINE+'/',0,s['root_sha256']) for s in pair]
    gs,es=[witness_policies(s,row,routes) for s,row in zip(pair,rows,strict=True)]
    shared=[]
    for h in sorted(gs.keys() & es.keys()):
        info={k:v for k,v in gs[h].items() if k!='native'}
        assert info=={k:v for k,v in es[h].items() if k!='native'}
        shared.append(dict(info,gto=gs[h]['native'],nl2=es[h]['native']))
    detail=dict(public_board=public, GTO_compatible_hole_card_pairs=rows[0]['compatible_hole_card_pairs'],
                NL2_compatible_hole_card_pairs=rows[1]['compatible_hole_card_pairs'],shared_rendered_decision_hands=len(shared))
    if not shared:
        return None,dict(status='NO_SHARED_REACHED_HAND',**detail)
    rates=opponent(e,public,pool)
    if not any(r['compatible_hole_card_pairs'] and r['applied_nodes'] for r in rates[1:3]):
        return None,dict(status='NO_REACHABLE_SIZED_RESPONSE',**detail)
    return (rows,shared,rates),dict(status='VERIFIED',**detail)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--solver', required=True, type=Path)
    ap.add_argument('--capture',type=Path,help='Capture the two complete, already solved native manifests')
    ap.add_argument('--run',type=int,help='Actions run authenticating the new source archives')
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    solver=args.solver.resolve()
    pool_raw=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(pool_raw)==POOL
    pool=json.loads(pool_raw)['NL2']
    frozen=json.loads((DATA/'nl2_hu_b563_frozen_flop.json').read_bytes())
    assert (frozen['flop'],frozen['turns'],frozen['flop_action'])==(NEW,list(TURNS),LINE)
    if args.capture:
        assert not args.run
        capture(solver,args.capture)
    historical=json.loads(PRIOR.read_bytes())
    old=historical['models']['68']
    assert historical['run']==PRIOR_RUN and {b['flop'] for b in old['boards']}=={'Jh9s4c','Ac8d3h'}
    old_pins={pin['flop']:pin for pin in old['pins']}
    group=dict(rank=68,model_id=MODEL,boards=[],pins=[])
    medium=dict(schema='NL2_HU_B563_ORIGINAL_LOCKED_MEDIUM_V1',references={},gto_references={})
    model=json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records'][MODEL]
    assert model['assumed_model_node_spr']==7 and model['frequency_rank']==68
    routes=json.loads(subprocess.check_output(['node','tools/hu_b563_rank68_route.cjs']))
    attempts=[]
    with TemporaryDirectory() as temp:
        for flop,turns in [(b['flop'],[b['turn']]) for b in old['boards']]+[(NEW,TURNS)]:
            selected=False
            for turn in turns:
                is_new=flop==NEW
                pair=fresh(Path(temp),turn,args.run) if is_new else previous(old_pins[flop])
                proof,obs=evaluate(pair,flop,turn,routes,model,pool)
                record=dict(flop=flop,turn=turn,archive_sha256={s['version']:s['archive_sha256'] for s in pair},**obs)
                attempts.append(record)
                if proof is None:
                    assert is_new
                    continue
                rows,shared,response=proof
                if not is_new:
                    assert obs['public_board']==old_pins[flop]['public_board']
                    assert set(old_pins[flop]['shared_rendered_route_hands'])=={w['hand'] for w in shared}
                if selected:
                    continue
                record['selected']=True
                selected=True
                if not args.run:
                    continue
                g,e=pair
                board,pin=emit_board(model,g,e,obs['public_board'],LINE+'/',texture(flop),viewer_code=f'B563_R68_{flop.upper()}_{turn.upper()}')
                pin.update(rendered_decision_hands=shared,shared_rendered_route_hands=[w['hand'] for w in shared],
                    hands_accepting_displayed_suggestion={k:sum(all(w['displayed_suggestion'] in w[v]['accepted_actions'] for v in vv) for w in shared)
                        for k,vv in [('gto',['gto']),('nl2',['nl2']),('both',['gto','nl2'])]},
                    first_applicable_opponent_rules=response,source_run_role='AUTHENTICATED_LOCAL_ARCHIVE_IMPORT' if is_new else 'ORIGINAL_B538_WORKER')
                board.update(restricted_flop_size_profile='UTG_CO_50PCT_ONLY',restricted_flop_bet_sizes_pct=[50],turn_root_allows_lead=True)
                variant=board['nl2_locked_variants'][0]
                variant.update(measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',pool_sha256=POOL,applied_street_rates=measured_rates(e),
                               viewer_archive_code=pin['viewer_archive_code'],viewer_sha256=pin['viewer_sha256'],
                               turn_checked_to_bet_assumption={'bet':.45,'applied_subgame_nodes':response[3]['applied_nodes']},
                               variant_label='翻牌限半池，轉牌可下注半池或滿池，依 NL2 分街頻率鎖頻')
                group['boards'].append(board);group['pins'].append(pin)
                for ref,row in zip(('gto_references','references'),rows,strict=True):
                    medium[ref][source_key(MODEL,row)]=row
    if args.run and len(group['boards'])>=3:
        assert len({b['flop'] for b in group['boards']})==len(group['boards'])==3
        (EVIDENCE/'reverified/rank68.json').write_bytes(json_bytes(group))
        (DATA/'nl2_hu_b563_locked_medium.json').write_bytes(json_bytes(medium))
    args.out.write_bytes(json_bytes(dict(schema='NL2_HU_B563_CHECKED_HALF_POT_TURN_V1',source_import_run=args.run,
        selection='FIRST_ELIGIBLE_FROZEN_TURN', attempts=attempts,
        distinct_flops=sum(a.get('selected',False) for a in attempts))))


if __name__=='__main__':
    main()
