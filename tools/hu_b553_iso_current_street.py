"""Rebuild rank124/125 source sets using the actual flop/turn cells and their native action masks."""
import argparse
import base64
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

from hu_b463_rank45_gate import SOLVER
from hu_b467_river_source_gate import EVIDENCE,json_bytes,sha
from hu_b483_locked_medium import POOL
from hu_b514_turn_stab import rates
from hu_b536_sb_barrels import tx
from hu_b539_iso_boundaries import MODELS,load_boundary,hcls
from hu_board_reach_corrections import source_key
from hu_apply_cert_extensions import update_references
from hu_checked_gto_boundary import audit_decision,replay_native
from hu_multiboard_promote import texture
from hu_reverified_board_pair import emit_board
from hu_sequential_cfr_reach import cardkey

DATA=Path('data')
RUN=45120208827
HEAD='972be701de6e00e72e55b01e99d95d6234106aee'


def matched_hands(source,row,flop_classes,turn_actions):
    public=row['public_board']
    actions=row['source_actions']
    result={}
    for hole,mask in zip(source['subgame']['hands'][1],base64.b64decode(row['compatible_action_mask_b64'],validate=True),strict=True):
        if not mask:continue
        hand=''.join(cardkey(hole))
        first,current=hcls(hand,public[:6]),hcls(hand,public)
        action=turn_actions.get(current)
        if first in flop_classes and action in actions and mask & (1<<actions.index(action)):
            result[hand]=dict(hand=hand,flop_class=first,turn_class=current,turn_action=action,
                              flop_texture=tx(public[:6]),turn_texture=tx(public))
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archives',required=True,type=Path)
    ap.add_argument('--downloads',required=True,type=Path)
    ap.add_argument('--solver',required=True,type=Path)
    args=ap.parse_args()
    solver=args.solver.resolve()
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==SOLVER
    sys.path.insert(0,str(solver/'postflop/py'))
    import pipeline
    poolbytes=(solver/'inputs/pool_stats.json').read_bytes()
    assert sha(poolbytes)==POOL
    pool=json.loads(poolbytes)['NL2']
    positions=json.loads((DATA/'nl2_hu_b539_flops.json').read_bytes())
    pins=json.loads((DATA/'nl2_hu_b553_iso_archives.json').read_bytes())
    old=json.loads((DATA/'nl2_hu_b539_iso_results.json').read_bytes())['groups']
    models=json.loads((DATA/'nl2_hu_multiboard_status_current.json').read_bytes())['records']
    route=json.loads(subprocess.check_output(['node','tools/hu_b553_iso_rendered.cjs']))
    groups={r:dict(rank=r,model_id=x[0],boards=[],pins=[]) for r,x in MODELS.items()}
    medium=dict(schema='NL2_HU_B553_ORIGINAL_LOCKED_MEDIUM_V1',gto_references={},references={})
    ledger=[]
    assert positions.keys()==pins.keys()
    for flop,turns in positions.items():
        p=pins[flop];aid=p['id'];name=f'NL2-B539-{flop}-gto'
        meta=json.loads((args.archives/f'{aid}.json').read_bytes())
        assert (meta['id'],meta['name'],meta['digest'])==(aid,name,'sha256:'+p['sha256'])
        assert (meta['workflow_run']['id'],meta['workflow_run']['head_sha'],meta['workflow_run']['repository_id'])==(RUN,HEAD,1438346845)
        archive=args.archives/f'{aid}.zip';assert sha(archive.read_bytes())==p['sha256']
        base=args.downloads/name
        with ZipFile(archive) as z:
            for member in z.namelist():
                assert not Path(member).is_absolute() and '..' not in Path(member).parts
            z.extractall(base)
        for rank,(mid,pct) in MODELS.items():
            model=models[mid];assert model['frequency_rank']==rank
            prefs=route[str(rank)]
            group=groups[rank]
            for turn in turns:
                observation=dict(rank=rank,flop=flop,turn=turn)
                ledger.append(observation)
                loaded=load_boundary(args.downloads,flop,turn,turns,pct,RUN)
                if not loaded:
                    observation['status']='NO_NATIVE_TURN';continue
                boundary,raw=loaded;g=boundary['source'];public=boundary['public']
                first,last=tx(public[:6]),tx(public)
                observation.update(public=public,flop_texture=first,turn_texture=last)
                if first not in prefs or last not in prefs:
                    observation['status']='NO_RENDERED_ACTUAL_STREET_ROW';continue
                if not all(0<=g[k]['info']['gto_expl_pct']<=.5 for k in ('root','subgame')):
                    observation['status']='GTO_OUTSIDE_CONVERGENCE';continue
                rootsha=boundary['identity']['root_sha256'];line=f'x b{pct} c/x'
                gr=audit_decision(g,public,line,1,rootsha)
                assert gr
                gh=matched_hands(g,gr,prefs[first]['flop'],prefs[last]['actions'])
                observation['gto_rendered_action_hands']=len(gh)
                if not gh:
                    observation['status']='NO_RENDERED_GTO_ACTION';continue
                code=f'B539_R{rank}_{flop.upper()}_{turn.upper()}_EXP_IP'
                path=base/'trainer/native'/f'NL2_{code}.json.gz'
                if not path.is_file():
                    observation['status']='NO_COMPLETED_LOCK';continue
                e=replay_native(boundary,'exp_ip',pool,pipeline,path,RUN,code)
                if not all(0<=e['subgame']['info'][k]<=.5 for k in ('gto_expl_pct','hero_gap_pct')):
                    observation['status']='LOCK_OUTSIDE_CONVERGENCE';continue
                er=audit_decision(e,public,line,1,rootsha)
                assert er
                eh=matched_hands(e,er,prefs[first]['flop'],prefs[last]['actions'])
                shared=[gh[h] for h in sorted(gh.keys()&eh.keys())]
                observation.update(gto_pairs=gr['compatible_hole_card_pairs'],locked_pairs=er['compatible_hole_card_pairs'],
                                   locked_rendered_action_hands=len(eh),joint_rendered_action_hands=len(shared))
                if not shared:
                    observation['status']='NO_SHARED_RENDERED_ACTION';continue
                observation['status']='REACHED'
                if any(b['flop']==flop for b in group['boards']):continue
                assert all(r['b50'] is not None for r in (gr,er))
                board,pin=emit_board(model,g,e,public,line,texture(flop),viewer_code=f'B553_R{rank}_{flop.upper()}_{turn.upper()}')
                pin.update(rendered_source_hands=shared,native_gto_parent=boundary['identity'],original_github_artifact=p)
                board['nl2_locked_variants'][0].update(variant_label='原始翻牌 GTO 範圍・轉河牌 NL2 分街鎖頻',
                    gto_parent_source_run_id=RUN,gto_parent_source_sha256=rootsha,pool_sha256=POOL,
                    measurement_policy='STREET_SPECIFIC_POOL_MARGINALS',applied_street_rates=rates(e),
                    viewer_archive_code=pin['viewer_archive_code'],viewer_sha256=pin['viewer_sha256'])
                (EVIDENCE/f"NL2_{g['archive_code']}.json.gz").write_bytes(raw)
                shutil.copyfile(path,EVIDENCE/path.name)
                group['boards'].append(board);group['pins'].append(pin)
                medium['gto_references'][source_key(mid,gr)]=gr;medium['references'][source_key(mid,er)]=er
    # Raw CFR rows from B539 remain historical evidence. The live medium registry only
    # accepts rows from an active three-flop model, and must never rediscover retired pins.
    previous=DATA/'nl2_hu_b539_locked_medium.json'
    historical=DATA/'nl2_hu_b539_historical_rendered_references.json'
    if previous.exists():
        original_rows=previous.read_bytes()
        assert sha(original_rows)=='8cffdeb45112c52c086a3176687981d45b93c14b67f6482c35105cbd681b80c6'
        if historical.exists():assert historical.read_bytes()==original_rows
        previous.replace(historical)
    assert sha(historical.read_bytes())=='8cffdeb45112c52c086a3176687981d45b93c14b67f6482c35105cbd681b80c6'
    active=dict(schema=medium['schema'],gto_references={},references={})
    crosspath=DATA/'nl2_hu_model_history_crosswalk.json'
    refpath=DATA/'nl2_hu_model_source_references.json'
    crosswalk=json.loads(crosspath.read_bytes());refs=json.loads(refpath.read_bytes())
    for rank,group in groups.items():
        target=EVIDENCE/'reverified'/f'rank{rank}.json'
        count=len(group['boards']);assert count==len({b['flop'] for b in group['boards']})<=5
        if target.exists():
            current=json.loads(target.read_bytes())
            assert current in (old[str(rank)],group), 'Unrecognized independent publication for this rank'
        mid=group['model_id']
        if count>=3:
            target.write_bytes(json_bytes(group))
            for key in ('references','gto_references'):
                active[key].update({k:v for k,v in medium[key].items() if json.loads(k)[0]==mid})
        else:
            if target.exists():target.unlink()
            if len(old[str(rank)]['boards'])>=3:
                model=dict(models[mid],certified_3_to_5_exact_flop_boards=group['boards'])
                update_references(model,crosswalk,refs)
                crosswalk['records'][mid]['board_specific_certification_status']='APPROX'
                for entry in refs['items'][mid]['references']:
                    entry['reference_status']='REVERIFIED_SINGLE_NAMED_BOARD_GTO'
                refs['items'][mid]['note']=f'{count} named flop(s) have a jointly playable rendered action. Three distinct flops are required for CERT-MULTIBOARD.'
    crosspath.write_bytes(json_bytes(crosswalk))
    refpath.write_bytes(json_bytes(refs))
    (DATA/'nl2_hu_b553_iso_results.json').write_bytes(json_bytes(dict(source_run=RUN,attempts=ledger,groups=groups,source_proofs=medium)))
    (DATA/'nl2_hu_b553_locked_medium.json').write_bytes(json_bytes(active))


if __name__=='__main__':
    main()
