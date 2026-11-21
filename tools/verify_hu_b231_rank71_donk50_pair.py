#!/usr/bin/env python3
"""Fail-closed independent B231 original parent/full-river-donk50 GTO vs partial NL2 lock auditor.
No generic model CERT, no observed hole-card conditional NL2 rate is inferred.
"""
import argparse,base64,gzip,hashlib,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from hu_sequential_cfr_reach import game_reach
ROOT=pathlib.Path(__file__).resolve().parents[1]
D=ROOT/'data'
RUN=44884042851
B231_BOARD='9s8h4d';B231_TURN='Ah';LINE='b50 c/x b50 c/'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for z in iter(lambda:f.read(1048576),b''):h.update(z)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--parent',required=True,type=pathlib.Path)
    ap.add_argument('--new',required=True,type=pathlib.Path)
    args=ap.parse_args()
    parent=args.parent.resolve();fresh=args.new.resolve()
    pinpath=D/'nl2_hu_b216_rank71_lmp_9s8h4d_gto_parent_pin.json'
    pin=json.loads(pinpath.read_text())
    assert pin['source_run_id']==RUN and pin['source_gto_job_id'] is None
    assert (pin['spot'],pin['flop'],pin['turn'])==('LMP_CO_BB',B231_BOARD,B231_TURN)
    assert pin['observed_preflop_ranges'] is False and pin['assumed_limped_169class'] is True
    assert (pin['target_exact_actor_OOP_river_nodes'],pin['target_exact_actor_OOP_strict_combos'])==(0,0)
    mf=parent/'evidence/LMP_CO_BB-gto-9s8h4d.json'
    rawroot=parent/'solver/postflop/out/LMP_CO_BB/gto/9s8h4d_multiboard.json'
    rootjob=rawroot.with_suffix('.job.json')
    for f,digest in [(mf,pin['original_gto_manifest_sha256']),
                     (rawroot,pin['original_gto_root_sha256']),
                     (rootjob,pin['original_gto_job_sha256'])]:
        assert f.exists() and sha(f)==digest, f'Original GTO SHA mismatch: {f}'
    m0=json.loads(mf.read_text());fr=json.loads(rawroot.read_text());j0=json.loads(rootjob.read_text())
    assert m0['version']=='gto' and m0['spot']=='LMP_CO_BB' and m0['flop']==B231_BOARD
    assert m0['preflop_ranges']['source']=='ASSUMED_EXPLICIT_169CLASS'
    assert (fr['pot'],fr['stack'])==(250,9900)
    assert j0['pot']==250 and j0['stack']==9900 and j0.get('hero') is None
    reportfile=fresh/'evidence/LMP_CO_BB-exp_oop-9s8h4d-donk50.json'
    assert reportfile.is_file()
    report=json.loads(reportfile.read_text())
    assert report['schema']=='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1'
    assert (report['spot'],report['flop'],report['version'])==('LMP_CO_BB',B231_BOARD,'exp_oop')
    assert (report['selected_lines'],report['selected_turn_lines'],report['turns'])==(['b50 c'],['x b50 c'],[B231_TURN])
    assert report['gto_parent_source_run_id']==RUN
    assert report['new_river_donk_menu']=='50%'
    assert report['new_river_donk_tree_not_original_full_flop_tree'] is True
    assert report['parent_B216_legacy_zero_actor_combos'] is True
    assert report['original_B231_parent_pin_sha256']==sha(pinpath)
    assert report['flop_root_jobfile_sha256']==pin['original_gto_job_sha256']
    assert report['gto_parent_source_sha256']==pin['original_gto_root_sha256']
    assert report['gto_parent_source_manifest_sha256']==pin['original_gto_manifest_sha256']
    assert report['preflop_ranges']==m0['preflop_ranges']
    assert report['no_generic_certification'] and not report['failures'] and report['solved_cases']==1
    assert report['new_genuine_unlocked_GTO_child'] is not None and len(report['cases'])==1
    assert report['locks'] and report['not_observed_exact_NL2_hero_EV'] is True
    base=fresh/'solver/postflop'
    output={}
    for v in ('gto','exp_oop'):
        src=base/'out/LMP_CO_BB'/v/'9s8h4d_b50c_Ah.json'
        job=src.with_suffix('.job.json')
        assert src.is_file() and job.is_file()
        j=json.loads(job.read_text());raw=json.loads(src.read_text())
        assert j['river_donk']=='50%' and j['pot']>0 and j['stack']>0
        assert j['rake_rate']==0.05 and j['rake_cap']==1000
        if v=='gto':
            assert j.get('hero') is None and not j.get('locks')
            prev=report['new_genuine_unlocked_GTO_child']
            assert prev['subgame_sha256']==sha(src) and prev['job_sha256']==sha(job)
            assert raw['info'].get('gto_expl_pct') is not None
            assert float(raw['info']['gto_expl_pct'])<=0.5
        else:
            assert j['hero']==0 and j.get('locks')
            assert report['cases'][0]['source_sha256']==sha(src)
            assert report['cases'][0]['exp_jobfile_sha256']==sha(job)
        assert raw['line0']=='b50 c' and raw['turn']==B231_TURN
        assert any(len(n['board'])==8 for n in raw['nodes'])
        assert any(len(n['board'])==10 for n in raw['nodes'])
        seq,stats=game_reach(fr,raw)
        found=[]
        for n in raw['nodes']:
            if n['line']!=LINE or n['player']!=0 or len(n['board'])!=10:continue
            key='|'.join((n['board'],n['line'],'0'))
            q=seq[key]
            if q['count']<=0:continue
            pot=n['pot'];stack=raw['stack']-max(n['bets'])
            assert pot>0 and stack>=0
            spr=stack/pot
            spr_error=100*abs(spr-9.916)/9.916
            found.append(dict(public_board=n['board'],strict_combos=q['count'],
                actual_spr=round(spr,5),spr_error_pct=round(spr_error,4),
                allowed_action_names=n['acts']))
        valid=[z for z in found if z['spr_error_pct']<=5]
        output[v]=dict(raw_sha256=sha(src),job_sha256=sha(job),
            original_rust_source_nodes=len(raw['nodes']),river_target_positive_actor_nodes=len(found),
            river_target_strict_combos=sum(z['strict_combos'] for z in found),
            exact_spr_matched_nodes=len(valid),exact_spr_matched_strict_combos=sum(z['strict_combos'] for z in valid),
            strict_nodes=valid,reach_stats=dict(stats),
            gto_exploitability_pct=raw['info'].get('gto_expl_pct'),
            hero_gap_pct=raw['info'].get('hero_gap_pct'))
    # A new pair counts only if BOTH original Rust subgames have strictly
    # reachable correct-actor, exact-line and model-SPR-matched combos.
    paired=all(output[v]['exact_spr_matched_strict_combos']>0 for v in ('gto','exp_oop'))
    # Keep raw authentic GTO/EXP evidence *separate* and immutable.
    archive=D/'solver_evidence'
    archive.mkdir(parents=True,exist_ok=True)
    for v in ('gto','exp_oop'):
        p=base/'out/LMP_CO_BB'/v/'9s8h4d_b50c_Ah.json'
        blob=gzip.compress(p.read_bytes(),compresslevel=9,mtime=0)
        name=f'NL2_MULTIBOARD_B231_R71_9S8H4D_DONK50_{v.upper()}.json.gz'
        destination=archive/name
        destination.write_bytes(blob)
        output[v]['archive_path']=str(destination.relative_to(ROOT))
        output[v]['gzip_sha256']=sha(destination)
    idx=dict(schema='NL2_MULTIBOARD_B231_EXACT_SHA_GTO_PLUS_PARTIAL_NL2_DONK50_V1',
        upstream_original_B216_run_id=RUN,
        b231_current_run_id=int(__import__('os').environ['GITHUB_RUN_ID']),
        original_parent_pin_sha256=sha(pinpath),
        original_GTO_parent_root_sha256=pin['original_gto_root_sha256'],
        spot='LMP_CO_BB',rank=71,flop=B231_BOARD,turn=B231_TURN,
        target_line=LINE,actor_OOP=0,new_river_donk='50%',
        full_100bb_original_flop_GTO_not_reoptimized=True,
        original_169class_LMP_preflop_assumed_not_observed=True,
        observed_NL2_private_card_conditional_rates=False,
        matched_restricted_river_tree_new_not_original_full_tree=True,
        true_original_Rust_subgames=2,
        paired_exact_line_actor_SPR_reach=paired,records=output,
        research_nonpolar50_generalization=False,
        automatic_generic_model_CERT_upgrades=0,
        V38_CERT_MULTIBOARD=151,V38_APPROX=241,V38_EST=0,
        PR2_Draft_NEVER_MERGE=True)
    idxfile=archive/'NL2_MULTIBOARD_B231_R71_9S8H4D_DONK50_PAIR.index.json'
    idxfile.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n')
    doc=ROOT/'docs/NL2_HU_B231_R71_ACTUAL_RIVER_DONK50_EXACT_SOURCE.md'
    doc.write_text('# B231 rank71 exact board, new permitted river-donk50 subgame\n\n'
        'Original full-flop LMP 100bb GTO root from B216 run 44884042851 SHA pinned. '
        'The original target OOP river action was missing because the turn/river tree '
        'had no 50%-pot river donk. This separate experiment permits exactly one 50%-pot '
        'river donk, while retaining the original GTO flop state byte-identical.\n\n'
        'Unrestricted opponent GTO turn/river and separately pooled-NL2-marginal-locked '
        'turn/river were recomputed in genuine pinned Rust; this does NOT reoptimize '
        'earlier streets or prove a fully game-tree GTO flop under the expanded river menu. '
        'Limped preflop 169-class ranges remain assumed, not measured.\n\n'
        f"Exact actor-OOP river match (GTO/EXP): {output['gto']['exact_spr_matched_strict_combos']}/"
        f"{output['exp_oop']['exact_spr_matched_strict_combos']} combos; paired={paired}. "
        'Never substitute unknown hole-card NL2 frequencies with pooled marginals.\n\n'
        'PR#2 remains Draft, NEVER MERGE. V38 remains 151 CERT/241 APPROX/0 EST '
        'pending an independent three-board promotion gate and original/tree comparability.\n')
    print('B231 source independent verified',json.dumps(dict(paired=paired,
        gto=output['gto']['exact_spr_matched_strict_combos'],
        nl2=output['exp_oop']['exact_spr_matched_strict_combos'])))
if __name__=='__main__':
    main()
