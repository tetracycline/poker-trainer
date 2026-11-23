"""Gate three fresh, distinct UTG-CO rank79 flops and two previously verified native board pairs."""
import argparse
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


CANDIDATES={"QcJh5s":["Th","5c","7d"], "QdJc3s":["7h","6c","8h"], "KhQs8d":["Qh","4s","3h"]}
VERSIONS=("gto","exp_ip")
PRIOR=Path('data/nl2_hu_b489_rank79_attempts.json')
PRIOR_SHA='80e152bb59c293deca5d99df9a77254570e690227c95b2be25f083f3e8d3aea1'
REPORT=Path('data/nl2_hu_b495_rank79_flops.json')
MEDIUM=Path('data/nl2_hu_b495_locked_medium.json')
REPAIR=EVIDENCE/'reverified/rank79.json'


def validate_choices(pipeline):
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
    validate_choices(pipeline)
    model=read(Path('data/nl2_hu_multiboard_status_current.json'))['records'][MODEL]
    assert (model['frequency_rank'],model['solver_profile'],model['family'],model['assumed_model_node_spr'])==(79,'UTG_CO','SRP',7)
    accepted=prior_boards(model)
    if args.preflight:
        print('Verified both B489 board pairs, their exact hand masks and the three new solver flops.')
        return
    assert args.run_id and args.head and args.artifacts and not REPAIR.exists()
    infos={s['name']:s for s in read(args.artifacts/'list.json')['artifacts']}
    checked={};missing={};artifacts={}
    for flop,turns in CANDIDATES.items():
        native={}
        for version in VERSIONS:
            name=f'NL2-B495-{flop}-{version}'
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
                    sources=parse(base/'solver/postflop',evidence,mf,args.run_id,flop,version,solver,pipeline,ranges,True,expected_turns=turns,case_turn=turn)
                    source=sources[turn]
                except (AssertionError,KeyError,ValueError) as err:
                    missing[f'{name} {turn}']=f'REJECTED_NATIVE_SOURCE: {type(err).__name__} {err}'
                    continue
                source.update(artifact_id=aid,github_artifact_sha256=digest)
                pack(source,flop,turn,batch='B495')
                row=audit_node(source)
                checked[f'{flop} {turn} {version}']=row
                native[turn,version]=(source,row)
        for turn in turns:
            if not all((turn,v) in native for v in VERSIONS):continue
            (g,gr),(e,er)=[native[turn,v] for v in VERSIONS]
            assert gr['public_board']==er['public_board']
            if not min(gr['compatible_hole_card_pairs'],er['compatible_hole_card_pairs']):continue
            b,pin=emit_board(model,g,e,gr['public_board'],LINE,'KQ_HIGH',viewer_code=f'B495_R79_{flop.upper()}_{args.run_id}')
            assert b and pin
            paired_proof(b,pin,(gr,er),model)
            accepted.append((b,pin,gr,er))
            break
    boards=[b for b,_,_,_ in accepted];pins=[p for _,p,_,_ in accepted]
    assert 2<=len(boards)==len({b['flop'] for b in boards})<=5
    group=dict(model_id=MODEL,rank=79,line=LINE,actor='CO_IP',spot='UTG_CO',boards=boards,pins=pins)
    save(REPORT,dict(run=args.run_id,source_commit=args.head,originals=artifacts,prior_report_sha256=PRIOR_SHA,
                     candidates=CANDIDATES,first_positive_turn_per_flop_in_frozen_order=True,observations=checked,unavailable=missing,model=group))
    if len(boards)>=3:
        save(REPAIR,group)
        save(MEDIUM,dict(schema='NL2_HU_B495_ORIGINAL_LOCKED_MEDIUM_V1',rank=79,report_sha256=sha(REPORT.read_bytes()),
                        gto_references={source_key(MODEL,g):g for _,_,g,e in accepted},
                        references={source_key(MODEL,e):dict(e,gto=g) for _,_,g,e in accepted}))
    print('Rank 79 verified distinct flop pairs:',len(boards))


if __name__=='__main__':main()
