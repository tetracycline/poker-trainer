"""Reproduce each B792 source, both players' actual decisions, and measured half-pot coverage."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import hu_b792_rank136_chance_turns as native
import hu_b794_collect as receipt
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b710_publish import unpack_original
from hu_b747_rank150_replay import materialize
from hu_sequential_cfr_reach import accepted,cardkey


def read(path):
    return json.loads(path.read_bytes())


def independent_deals(root,game,public,weights,route):
    """Use the same physical BTN and BB across both streets and all checked decisions."""
    f,turn,river=(public[:i] for i in (6,8,10))
    flop={n['line']:n for n in root['nodes'] if n['board']==f}
    turns={n['line']:n for n in game['nodes'] if n['board']==turn}
    rivers={n['line']:n for n in game['nodes'] if n['board']==river}
    assert [flop[k]['player'] for k in ('','x','x b75')]==[0,1,0]
    assert [turns[k]['player'] for k in (native.CHILD,native.CHILD+'x')]==[0,1]
    assert [rivers[k]['player'] for k in ('x b75 c/x x/',native.LINE)]==[0,1]
    live=[]
    for seat in (0,1):
        start={cardkey(h) for h,w in zip(root['hands'][seat],weights[seat],strict=True) if w>1.e-4}
        last={cardkey(h) for h,w in zip(game['hands'][seat],rivers[native.LINE]['w'][seat],strict=True)
              if w>1.e-4 and native.public_cards(public).isdisjoint(cardkey(h))}
        live.append(start&last)
    bb=live[0]&accepted(flop[''],root['hands'],'x')&accepted(flop['x b75'],root['hands'],'c')
    bb&=accepted(turns[native.CHILD],game['hands'],'x')&accepted(rivers['x b75 c/x x/'],game['hands'],'x')
    btn=live[1]&accepted(flop['x'],root['hands'],'b75')&accepted(turns[native.CHILD+'x'],game['hands'],'x')
    btn&=accepted(rivers[native.LINE],game['hands'],'x')
    found={}
    for cards in sorted(btn):
        h=''.join(cards)
        if not all(native.hand_cell(h,public[:n])[0] in route[k] for n,k in ((6,'flop'),(8,'turn'),(10,'river'))):continue
        foes=sorted(''.join(v) for v in bb if set(cards).isdisjoint(v))
        if foes:found[h]=foes
    return found


def authenticate_archive(folder,frozen,archive,flop,solver,route_raw):
    names=unpack_original(archive,folder)
    proof_raw=(folder/'proof.json').read_bytes()
    claim=json.loads(proof_raw)
    assert (claim['rank'],claim['model_id'],claim['actor'],claim['line'],claim['flop'])==(136,native.MODEL,1,native.LINE,flop)
    assert (folder/'rendered-routes.json').read_bytes()==route_raw
    expected={'proof.json','original-b652.zip','rendered-routes.json'}
    for turn in claim['turns']:
        for mode,pol in turn['policies'].items():
            for filename,key in (('job','job_sha256'),('result','source_sha256')):
                path=f'{turn["turn"]}-{mode}/{filename}.json';expected.add(path)
                assert sha((folder/path).read_bytes())==pol[key]
    assert names==expected
    assert sha((folder/'original-b652.zip').read_bytes())==claim['origin']['artifact_sha256']
    subprocess.run([sys.executable,str(frozen/receipt.WORKER),'--flop',flop,'--solver',str(solver),
                    '--archive',str(folder/'original-b652.zip'),'--output',str(folder)],cwd=frozen,check=True)
    assert (folder/'proof.json').read_bytes()==proof_raw
    assert len(claim['origin']['held_out_seat_weight_sha256'])==10 and claim['original_flop_solves_repeated']==0
    return claim


def inspect(folder,flop,claim,route,pipeline,ranges):
    root,weights,original=native.original(folder/'original-b652.zip',flop,pipeline,ranges)
    assert original==claim['origin'];eligible={};counts=[0,0,0];total_turn_jobs=0
    for turn in claim['turns']:
        t=turn['turn'];totals={};total_turn_jobs+=len(turn['policies'])
        for mode,pol in turn['policies'].items():
            game=read(folder/(t+'-'+mode)/'result.json')
            windows={pub:independent_deals(root,game,pub,weights[t],route) for pub in pol['boards']}
            totals[mode]={p:d for p,d in windows.items() if d}
            assert totals[mode]==pol['common_deal_candidates']
            if mode=='exp_ip':
                assert pol['applied_lock'] and any(n>0 for k,n in pol['applied_lock']['driver_tree_nodes'].items() if k in pol['applied_lock']['marginal_targets'])
                rows=list(pol['boards'].values());half=[r for r in rows if r['compatible_hole_card_pairs']>=r['strict_legal_combos']>0 and 'b50' in r['source_actions'] and r['b50'] is not None]
                counts[0]+=len(rows);counts[1]+=len(half);counts[2]+=sum(r['b50']['candidate'] for r in half)
        matched={}
        for pub,gh in totals['gto'].items():
            lock=totals.get('exp_ip',{}).get(pub,{})
            common={h:sorted(set(bb)&set(lock.get(h,[]))) for h,bb in gh.items() if set(bb)&set(lock.get(h,[]))}
            if common:matched[pub]=common
        assert matched==turn['common']
        if matched:eligible[t]=matched
    keys=('locked_public_boards','joint_halfpot_assessed','halfpot_candidates')
    assert counts==[claim[k] for k in keys]
    output=dict(flop=flop,original=original,conditional_native_jobs=total_turn_jobs,selected=claim['selected'],
                inspected_turns=[t['turn'] for t in claim['turns']],**dict(zip(keys,counts,strict=True)))
    if eligible:
        t,=eligible;public=min(eligible[t]);assert claim['selected']==dict(turn=t,public_board=public,btn_and_bb=eligible[t][public])
    else:assert claim['selected'] is None
    assert claim['positive_distinct_flops']==len(eligible)
    return output


def publish(a):
    solver=a.solver.resolve();assert sys.version_info[:2]==(3,11)
    sys.path.insert(0,str(solver/'postflop/py'));import pipeline,ranges
    pin=read(a.archives/'receipt.json');auth=receipt.validate(pin)
    assert (a.archives/'receipt.json').read_bytes()==json_bytes(auth)
    registry=Path('data/nl2_hu_multiboard_status_current.json');prior=registry.read_bytes()
    route_raw=subprocess.check_output(['node',native.ROUTE]);route=json.loads(route_raw)['136']
    model=json.loads(prior)['records'][native.MODEL]
    assert (model['frequency_rank'],model['solver_profile'])==(136,'BTN_BB')
    old,=[b for b in model.get('remaining_exact_board_evidence',[]) if b['flop']=='KsQh4d']
    assert old['actual_exact_action_line']==native.LINE and old['public_board']=='4dQhKsTc4c'
    assert {native.hand_cell('2d3h',old['public_board'][:i])[0].split(':')[0] for i in (6,8,10)}=={'KQ_high','paired'}
    out=a.output.resolve();assert not out.exists() and not out.is_relative_to(Path('data').resolve())
    evidence=out/'solver_evidence';partial=evidence/'partial';partial.mkdir(parents=True)
    results=[]
    with TemporaryDirectory(prefix='b794-') as tmp:
        directory=Path(tmp);frozen=directory/'frozen';materialize(receipt.HEAD,frozen)
        assert route_raw==subprocess.check_output(['node',native.ROUTE],cwd=frozen)
        for f,jid in receipt.JOBS.items():
            meta,=(v for v in auth['artifacts'] if v['name']=='B792-R136-'+f)
            raw=(a.archives/(str(meta['id'])+'.zip')).read_bytes()
            assert sha(raw)==meta['digest'][7:] and len(raw)==meta['size_in_bytes']
            (evidence/('NL2_B792_R136_'+f.upper()+'.zip')).write_bytes(raw)
            folder=directory/f;claim=authenticate_archive(folder,frozen,raw,f,solver,route_raw)
            worker=inspect(folder,f,claim,route,pipeline,ranges)
            worker.update(original_job_id=jid,worker_artifact=meta['id'],archive_sha256=sha(raw),proof_sha256=sha((folder/'proof.json').read_bytes()))
            results.append(worker)
    selected={w['flop']:w['selected'] for w in results if w['selected']}
    result=dict(rank=136,model_id=native.MODEL,source_head=receipt.HEAD,source_run=receipt.RUN,
                checked_distinct_flops=len(results),positive_distinct_flops=len(selected),
                selected_by_flop=selected,cert_eligible_ranks=[136] if len(selected)>=3 else [],
                legacy_ksqh4d=dict(public_board=old['public_board'],actual_line=old['actual_exact_action_line'],
                                   present_rendered_flop_texture='KQ_high',required_flop_texture='A_high',included_in_distinct_flops=False),
                original_flop_native_solves_repeated=0,conditional_native_jobs=sum(w['conditional_native_jobs'] for w in results),
                workers=results)
    for k in ('locked_public_boards','joint_halfpot_assessed','halfpot_candidates'):result[k]=sum(w[k] for w in results)
    (out/'nl2_hu_b794_results.json').write_bytes(json_bytes(result))
    (out/'nl2_hu_b794_source_manifest.json').write_bytes(json_bytes(auth))
    assert registry.read_bytes()==prior
    print(json.dumps({k:v for k,v in result.items() if k not in ('legacy_ksqh4d','workers','selected_by_flop')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('archives','output','solver'):p.add_argument('--'+k,type=Path,required=True)
    publish(p.parse_args())
