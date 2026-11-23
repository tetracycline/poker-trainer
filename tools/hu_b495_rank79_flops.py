"""Gate three fresh, distinct UTG-CO rank79 flops and two previously verified native board pairs."""
import argparse
import base64
import json
from pathlib import Path
import sys
import subprocess
from zipfile import ZipFile

from hu_apply_cert_extensions import verify_case
from hu_b467_river_source_gate import EVIDENCE, sha
from hu_b489_rank79_originals import EXTRA_SPOTS, LINE, MODEL, PIN, POOL, audit_node, pack, parse, read, save
from hu_board_reach_corrections import source_key, summarize
from hu_reverified_board_pair import emit_board


LOW_HALF_POT = {'9s7d4c':['8d','As','7s'], '8c6h3d':['8h','5h','2d'], '9c8d5h':['8s','7c','3d']}
CANDIDATES={"QcJh5s":["Th","5c","7d"], "QdJc3s":["7h","6c","8h"], "KhQs8d":["Qh","4s","3h"]}
TWO_TONE = {"KsQh4s":["5c","Kh","2h"], "QsJh4s":["2d","Qd","2s"], "KhQhJc":["Ks","6s","4s"]}
VERSIONS=("gto","exp_ip")
PRIOR=Path('data/nl2_hu_b489_rank79_attempts.json')
PRIOR_SHA='80e152bb59c293deca5d99df9a77254570e690227c95b2be25f083f3e8d3aea1'
REPORT=Path('data/nl2_hu_b495_rank79_flops.json')
REPAIR=EVIDENCE/'reverified/rank79.json'


def validate_choices(pipeline, batch="B495"):
    if batch == "B520":
        old = read(Path('data/nl2_hu_b503_rank79_flops.json'))
        assert old['candidates'] == TWO_TONE and len(old['model']['boards']) == 2
        for flop, turns in LOW_HALF_POT.items():
            assert flop not in TWO_TONE and flop not in CANDIDATES and len(set(flop[1::2])) == 3
            assert len(set(flop[::2])) == 3 and set(flop[::2]) <= set('23456789')
            assert pipeline.turns_for(flop) == turns
        return
    if batch == "B503":
        # Two-tone flops have a distinct flush-draw structure from the rainbow anchors.
        earlier = read(REPORT)
        assert earlier['candidates'] == CANDIDATES and len(earlier['model']['boards']) == 2
        assert all(row['compatible_hole_card_pairs'] == 0 for row in earlier['observations'].values()
                   if row['version'] == 'gto')
        for flop, turns in TWO_TONE.items():
            assert len(set(flop[1::2])) == 2 and len(set(flop[::2])) == 3
            assert flop not in earlier['candidates'] and turns == pipeline.turns_for(flop)
        return
    # Rank patterns from the complete 21 eligible archived native GTO subgames.
    prior_ranks={'442','753','883','A73','A92','J94','KQ6','KT4','KJ6','KQ5','KQ7','K72','KJ4','KQ3','KQ4','QJ6','QJ4','T95'}
    fresh=set()
    for flop,turns in CANDIDATES.items():
        ranks,suits=flop[::2],flop[1::2]
        assert len(set(suits))==3 and ranks[0] in 'KQ' and len(set(ranks))==3
        assert ranks not in prior_ranks and ranks not in fresh
        assert pipeline.turns_for(flop)==turns
        fresh.add(ranks)


def paired_proof(board,pin,rows,model):
    assert board['acting_seat']==1 and board['actual_exact_action_line']==LINE and board['exact_flop_action']=='b50 c'
    assert board['actual_pot_bb']==13 and board['actual_effective_stack_bb']==94.25 and board['actual_spr']==7.25
    for version,raw in zip(VERSIONS,rows,strict=True):
        count=pin['GTO_strict_combos' if version=='gto' else 'NL2_strict_combos']
        pairs=pin['GTO_compatible_hole_card_pairs' if version=='gto' else 'NL2_compatible_hole_card_pairs']
        raw_sha=pin['original_GTO_SHA256' if version=='gto' else 'actual_NL2_SHA256']
        signed=summarize(raw)
        assert (raw['version'],raw['public_board'],raw['line'],raw['acting_seat'],raw['source_sha256'])==(
            version,board['public_board'],LINE,1,raw_sha)
        assert signed['strictly_reachable_combos']==count>0 and signed['compatible_hole_card_pairs']==pairs>=count
        prefix='locked_' if version=='exp_ip' and 'locked_viewer_sha256' in pin else ''
        case,node=verify_case(pin[prefix+'viewer_archive_code'],pin[prefix+'viewer_sha256'],raw['source_run_id'],model,board,version,raw_sha,count)
        assert node['strictly_reachable_masks_b64']==raw['compatible_action_mask_b64']
        assert node['source_actions']==raw['source_actions'] and node['medium_50pct_strict_evidence']==raw['b50']
        if version=='exp_ip':
            assert raw['locked_hero_gap_pct']<=.5 and raw['root_applied_rust_lock_nodes']>0 and raw['subgame_applied_rust_lock_nodes']>0
            assert case['villain_lock_scope']['observed_marginal_source_nodes']>0


def shared_pair_hands(board, pin, rows, model):
    # The rendered calling route includes good/weak top pair and middle/small pairs
    # on both K/Q-high and low flops. Identify one-pair witnesses in both native masks.
    pools = []
    for version, row in zip(VERSIONS, rows, strict=True):
        prefix = 'locked_' if version == 'exp_ip' and 'locked_viewer_archive_code' in pin else ''
        case, node = verify_case(pin[prefix+'viewer_archive_code'], pin[prefix+'viewer_sha256'],
                                 row['source_run_id'], model, board, version, row['source_sha256'], row['strict_legal_combos'])
        mask = base64.b64decode(node['strictly_reachable_masks_b64'], validate=True)
        pools.append({h for h, bits in zip(case['hands_by_seat'][1], mask, strict=True) if bits})
    common = pools[0] & pools[1]
    assert len(common) == pin['common_legal_hero_combos']
    ranks = set(board['flop'][::2])
    return sorted(h for h in common if len(set(h[::2])) == 2 and len(set(h[::2]) & ranks) == 1)


def prior_boards(model):
    assert sha(PRIOR.read_bytes())==PRIOR_SHA
    prior=read(PRIOR)
    group=prior['model']
    assert (group['model_id'],group['rank'],group['line'],group['actor'])==(MODEL,79,LINE,'CO_IP')
    assert {b['flop'] for b in group['boards']}=={'KsQh4d','QsJh4d'} and len(group['pins'])==len(group['boards'])==2
    proven=[]
    for b,pin in zip(group['boards'],group['pins'],strict=True):
        src=pin['archive_code'].removeprefix('GITHUB_ARTIFACT_')
        g=prior['originals'][src]
        assert read(Path('data/nl2_hu_b489_originals.json'))[src]['sha256']==pin['archive_sha256']==g['archive_sha256']
        e=prior['fresh'][f"{b['flop']} {b['turn']} exp_ip"]
        locked=EVIDENCE/('NL2_'+pin['locked_original_archive_code']+'.json.gz')
        assert sha(locked.read_bytes())==e['archive_sha256']==pin['locked_original_archive_sha256']
        paired_proof(b,pin,(g,e),model)
        proven.append((b,pin,g,e))
    return proven


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--batch',choices=('B495','B503','B520'),default='B495')
    p.add_argument('--artifacts',type=Path)
    p.add_argument('--solver',type=Path,required=True)
    p.add_argument('--run-id',type=int)
    p.add_argument('--head')
    p.add_argument('--preflight',action='store_true')
    args=p.parse_args()
    solver=args.solver.resolve()
    assert subprocess.check_output(['git','-C',str(solver),'rev-parse','HEAD'],text=True).strip()==PIN
    assert sha((solver/'inputs/pool_stats.json').read_bytes())==POOL
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline, ranges
    ranges.SPOTS.update(EXTRA_SPOTS)
    batch=args.batch
    candidates={'B495':CANDIDATES,'B503':TWO_TONE,'B520':LOW_HALF_POT}[batch]
    flop_profile='utg-50-only' if batch=='B520' else 'full'
    report=Path(f'data/nl2_hu_{batch.lower()}_rank79_flops.json')
    medium=Path(f'data/nl2_hu_{batch.lower()}_locked_medium.json')
    validate_choices(pipeline,batch)
    model=read(Path('data/nl2_hu_multiboard_status_current.json'))['records'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'],model['family'],model['assumed_model_node_spr'])==(79,'UTG_CO','SRP',7)
    accepted=prior_boards(model)
    if batch=='B520':
        for b,pin,g,e in accepted:
            witnesses=shared_pair_hands(b,pin,(g,e),model)
            assert witnesses
            pin['shared_one_pair_flop_hands']=witnesses
    if args.preflight:
        print('Verified both B489 board pairs, their exact hand masks and the three new solver flops.')
        return
    assert args.run_id and args.head and args.artifacts and not REPAIR.exists()
    infos={s['name']:s for s in read(args.artifacts/'list.json')['artifacts']}
    checked={};missing={};artifacts={}
    for flop,turns in candidates.items():
        native={}
        for version in VERSIONS:
            name=f'NL2-{batch}-{flop}-{version}'
            if name not in infos:
                missing[name]='NO_COMPLETED_SOURCE_ARTIFACT';continue
            info=infos[name];aid=info['id'];raw=args.artifacts/f'{aid}.zip';digest=sha(raw.read_bytes())
            assert info['digest']=='sha256:'+digest and (info['workflow_run']['id'],info['workflow_run']['head_sha'],info['workflow_run']['repository_id'])==(args.run_id,args.head,1438346845)
            artifacts[name]=dict(id=aid,sha256=digest,run=args.run_id,head=args.head)
            base=args.artifacts/name
            with ZipFile(raw) as z:z.extractall(base)
            evidence=base/'trainer/evidence';mf=evidence/f'{flop}-{version}.json'
            if not mf.is_file() or read(mf)['failures']:
                missing[name]=read(mf)['failures'] if mf.is_file() else 'NO_COMPLETED_NATIVE_MANIFEST';continue
            m=read(mf)
            assert sha((evidence/'pool_stats.json').read_bytes())==POOL and m['selected_lines']==['b50 c']
            assert sorted(c['turn'] for c in m['cases']+m['skipped'])==sorted(turns)
            if m['skipped']:missing[name]=m['skipped']
            for completed in m['cases']:
                turn=completed['turn']
                try:
                    sources=parse(base/'solver/postflop',evidence,mf,args.run_id,flop,version,solver,pipeline,ranges,True,expected_turns=turns,case_turn=turn,flop_profile=flop_profile)
                    source=sources[turn]
                except (AssertionError,KeyError,ValueError) as err:
                    missing[f'{name} {turn}']=f'REJECTED_NATIVE_SOURCE: {type(err).__name__} {err}'
                    continue
                source.update(artifact_id=aid,github_artifact_sha256=digest)
                pack(source,flop,turn,batch=batch)
                if batch=='B520':
                    sub=source['subgame']
                    node,=[n for n in sub['nodes'] if n['line']==LINE and len(n['board'])==8 and n['player']==1]
                    reply,=[n for n in sub['nodes'] if n['line']==LINE+' b50' and n['board']==node['board'] and n['player']==0]
                    assert 'b50' in node['acts'] and (reply['pot'],reply['bets'])==(1950,[0,650])
                row=audit_node(source)
                checked[f'{flop} {turn} {version}']=row
                native[turn,version]=(source,row)
        for turn in turns:
            if not all((turn,v) in native for v in VERSIONS):continue
            (g,gr),(e,er)=[native[turn,v] for v in VERSIONS]
            assert gr['public_board']==er['public_board']
            if not min(gr['compatible_hole_card_pairs'],er['compatible_hole_card_pairs']):continue
            b,pin=emit_board(model,g,e,gr['public_board'],LINE,'LOW' if batch=='B520' else 'KQ_HIGH',viewer_code=f'{batch}_R79_{flop.upper()}_{args.run_id}')
            assert b and pin
            paired_proof(b,pin,(gr,er),model)
            if batch=='B520':
                witnesses=shared_pair_hands(b,pin,(gr,er),model)
                if not witnesses:continue
                b['restricted_flop_size_profile']='UTG_CO_50PCT_ONLY'
                b['restricted_flop_bet_sizes_pct']=[50]
                b['nl2_locked_variants'][0]['variant_label']='翻牌限半池，轉牌可下注半池或滿池，依 NL2 分街邊際頻率局部鎖頻'
                pin['shared_one_pair_flop_hands']=witnesses
            accepted.append((b,pin,gr,er))
            break
    boards=[b for b,_,_,_ in accepted];pins=[p for _,p,_,_ in accepted]
    assert 2<=len(boards)==len({b['flop'] for b in boards})<=5
    group=dict(model_id=MODEL,rank=79,line=LINE,actor='CO_IP',spot='UTG_CO',boards=boards,pins=pins)
    save(report,dict(run=args.run_id,source_commit=args.head,originals=artifacts,prior_report_sha256=PRIOR_SHA,
                     candidates=candidates,first_positive_turn_per_flop_in_frozen_order=True,observations=checked,unavailable=missing,model=group))
    if len(boards)>=3:
        save(REPAIR,group)
        save(medium,dict(schema=f'NL2_HU_{batch}_ORIGINAL_LOCKED_MEDIUM_V1',rank=79,report_sha256=sha(report.read_bytes()),
                        gto_references={source_key(MODEL,g):g for _,_,g,e in accepted},
                        references={source_key(MODEL,e):dict(e,gto=g) for _,_,g,e in accepted}))
    print('Rank 79 verified distinct flop pairs:',len(boards))


if __name__=='__main__':main()
