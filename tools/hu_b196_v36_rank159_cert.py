#!/usr/bin/env python3
"""B196: fail-closed V36 rank159 ONLY, 3 genuinely locked named SB BB flops.

Original As7h3d B5 and Js9h4d B1 100bb GTO + genuine B195 Rust BB-IP
turn/river NL2 children. Third existing 9s6h3d genuine paired GTO+NL2.
No exact private-hand NL2 villain conditionals or generalized b100/b50 GTO.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md

D=pathlib.Path('data')
V35=D/'nl2_hu_multiboard_status_v35_b193_rank201.json'
B175=D/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
RANK=D/'nl2_hu_multiboard_prerank.json'
STAGE=D/'nl2_hu_stage2_queue.json'
PINS={flop:D/('nl2_hu_b194_rank159_'+flop+'_original_SB_BB_gto_pin.json')
 for flop in ('As7h3d','Js9h4d')}
LOCK=D/'solver_evidence/NL2_MULTIBOARD_B195_R159_SBBB_2FLOP_EXP_IP.json.gz'
OUT=D/'nl2_hu_multiboard_status_v36_b196_rank159.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v36_b196.json'
DOC=pathlib.Path('docs/NL2_HU_B196_V36_RANK159_THREE_SB_BB_GTO_NL2_CERT.md')
MATDOC=pathlib.Path('docs/NL2_HU_B196_V36_ALL_575_NAMED_BOARD_LOCK_MEDIUM.md')
MID='ln-ipc-r_model-vvxn9n'
FLOPS={'As7h3d','Js9h4d','9s6h3d'}
LINE='x b100 c/x x/x'

def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def freeze():
    old=load(V35);r=load(B175)
    assert old['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V35_B193_RANK201'
    assert (old['CERT_MULTIBOARD'],old['APPROX'],old['EST'],old['TOTAL'])==(148,244,0,392)
    assert old['records'][MID]['label']=='APPROX' and len(old['records'])==392
    assert old['records']['ln-iso-lmp_r_model-qsgdjf']['label']=='CERT-MULTIBOARD'
    assert old['records']['ln-iso-lmp_r_model-vlgh2t']['label']=='APPROX'
    assert old['records']['ln-iso-lmp_r_model-wpg493']['label']=='APPROX'
    assert r['schema']=='NL2_HU_B175_V32_ALL_248_GENUINE_GTO_RUN_ACTOR_TURN_SHA_PROVENANCE_V1'
    assert old['B175_sourceblind_sha256']==sha(B175)
    frozen=next(z for z in r['rows'] if z['rank']==159)
    assert frozen['model_id']==MID and frozen['hero_seat']==1
    assert frozen['distinct_GTO_plus_NL2_hero_flops']==['9s6h3d']
    assert {'As7h3d','Js9h4d','9s6h3d'}<=set(frozen['distinct_real_GTO_flops'])
    for flop,path in PINS.items():
        q=load(path)
        assert q['schema']=='NL2_HU_B194_RANK159_ORIGINAL_SB_BB_GTO_SOURCE_PIN_V1'
        assert (q['target_rank'],q['model_id'])==(159,MID)
        assert (q['spot'],q['flop'],q['acting_position'],q['acting_seat'])==('SB_BB',flop,'BB_IP',1)
        assert q['minimum_strict_original_actor_IP_combos']>0
        assert q['exact_river_line']==LINE
        assert q['original_parent_GTO_not_recomputed']
        assert q['preflop_source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
        assert q['true_NL2_BB_IP_child_NOT_YET_SOLVED']
        index=D/('solver_evidence/NL2_MULTIBOARD_'+q['source_batch']+'.index.json')
        arc=D/('solver_evidence/NL2_MULTIBOARD_'+q['source_batch']+'.json.gz')
        i=load(index)
        assert (i['batch'],i['run_id'])==(q['source_batch'],q['source_run_id'])
        assert q['original_archive_sha256']==i['gzip_sha256']==sha(arc)
        assert q['original_index_sha256']==sha(index)
        assert i['source_sha256']==hashlib.sha256(gzip.decompress(arc.read_bytes())).hexdigest()
        exact=[z for z in frozen['exact_authentic_gto_source_proofs'] if
          z['flop']==flop and z['turn']==q['turn'] and
          z['source_run']==q['source_run_id'] and z['source_sha']==q['original_case_sha256'] and
          z['exact_line']==LINE and z['actor']==1 and z['strict_legal_combos']>0 and
          z['GTO_gap_pct']<=.5 and z['SPR_error_pct']<=5]
        assert exact and all(not z['true_NL2_actor_locked'] for z in exact)
    assert LOCK.is_file()
    i=load(LOCK.with_suffix('').with_suffix('.index.json'))
    raw=gzip.decompress(LOCK.read_bytes())
    solve=json.loads(raw)
    assert i['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert (i['batch'],i['actual_spot_flop_version_jobs'],i['verified_cases'],i['gto_cases'],i['locked_cases'])==(
       'B195_R159_SBBB_2FLOP_EXP_IP',2,2,0,2)
    assert i['source_sha256']==hashlib.sha256(raw).hexdigest() and i['gzip_sha256']==sha(LOCK)
    assert i['exact_SB_BB_BB_IP_line']==LINE and i['actor_seat']==1
    assert i['both_new_flops_positive_strict_BB_IP_combos'] is True
    assert i['strict_failure_reason'] is None
    assert (i['immediate_CERT_upgrades'],i['generic_model_certification'])==(0,0)
    assert solve['source_run_id']==i['run_id'] and not solve['errors'] and len(solve['artifacts'])==2
    sources=i['real_B1_B5_GTO_pinned_flop_sources']
    assert set(sources)=={'As7h3d','Js9h4d'}
    for flop,item in sources.items():
        pin=load(PINS[flop])
        assert item['nodes']>0 and item['strict_combos']>0
        assert item['original_GTO_run']==pin['source_run_id']
        assert (item['original_GTO_root_sha256'],item['original_GTO_job_sha256'],item['original_GTO_manifest_sha256'])==(
            pin['original_gto_root_sha256'],pin['original_gto_job_sha256'],pin['original_gto_manifest_sha256'])
        assert item['original_SBBB_preflop_CFR_pinned_not_observed_NL2_private_hand']
    for a in solve['artifacts']:
        assert (a['spot'],a['version'])==('SB_BB','exp_ip') and not a['errors']
        assert a['flop'] in sources and len(a['cases'])==1
        z=a['cases'][0]
        assert (z['flop_line'],z['turn'])==('x b100 c',load(PINS[a['flop']])['turn'])
        legal=[n for n in z['nodes'] if n['exact_node_line']==LINE and
             n['acting_seat']==1 and n['strictly_reachable_combos']>0]
        assert legal and sum(n['strictly_reachable_combos'] for n in legal)==sources[a['flop']]['strict_combos']
    return old,i

def main():
    old,idx=freeze()
    files=[pathlib.Path(x) for x in old['source_evidence']['source_files']]
    assert files and len(files)==len(set(files)) and all(x.is_file() for x in files)
    assert LOCK not in files
    files.append(LOCK)
    gto,locked,summary=build_source_index(D,files)
    ranked={x['rank_by_empirically_grounded_frequency_proxy']:x for x in load(RANK)['nodes']}
    model=next(x for x in load(STAGE)['records'] if x['model_id']==MID)
    assert model['solver_profile']=='SB_BB' and model['family']=='SRP' and model['street']==2
    assert hero_seat(model['preflop_text'])==1
    item=copy.deepcopy(ranked[159])
    assert item['model_id']==MID
    item['preflop_text']=model['preflop_text']
    item['abstract_action_history']=model['abstract_action_history']
    candidates_all,why=candidates(item,gto,locked,None)
    assert why is None,why
    boards,why=choose_3_5(candidates_all)
    assert why is None,why
    assert len(boards)>=3 and {x['flop'] for x in boards}>=FLOPS
    assert len(boards)<=5 and len({x['flop_texture'] for x in boards})>=2
    selected=[next(x for x in boards if x['flop']==flop) for flop in ('As7h3d','Js9h4d','9s6h3d')]
    assert len(selected)==3
    for z in selected:
        assert z['acting_seat']==1 and z['actual_exact_action_line']==LINE
        assert z['strict_full_street_combo_reachable']>0 and z['exact_combo_reachable']>0
        assert z['genuine_gto_exploitability_pct']<=.5 and z['relative_spr_error_pct']<=5
        assert z['assumed_preflop_ranges'] is False
        assert z['nl2_locked_variants'] and all(a['version']=='exp_ip' for a in z['nl2_locked_variants'])
        assert len(z['source_sha256'])==64
    for flop in ('As7h3d','Js9h4d'):
        z=next(x for x in selected if x['flop']==flop)
        pin=load(PINS[flop])
        assert (z['source_run_id'],z['source_sha256'],z['turn'])==(
            pin['source_run_id'],pin['original_case_sha256'],pin['turn'])
        assert any(t['run_id']==idx['run_id'] for t in z['nl2_locked_variants'])
    third=next(x for x in selected if x['flop']=='9s6h3d')
    assert any(t['run_id']!=idx['run_id'] for t in third['nl2_locked_variants'])
    out=copy.deepcopy(old)
    out['records'][MID].update(
        label='CERT-MULTIBOARD',high_frequency_preregistered=True,
        original_top24_high_frequency_preregistered=False,
        source_blind_expansion_rank=159,
        prereg_cohort='B175_V32_FROZEN_SBBB_BBIP_TWO_MISSING_ORIGINAL_GTO_AND_TRUE_NL2_FLOPS',
        certified_3_to_5_exact_flop_boards=selected,
        proven_exact_board_count=3,blocked_reason=None,
        source_credibility='B194_B5_AS7H3D_AND_B1_JS9H4D_ORIGINAL_GTO_SHA_PLUS_B195_TRUE_BBIP_RUST_CHILD_PLUS_OFFICIAL_9S6H3D')
    assert {k for k in old['records'] if old['records'][k]!=out['records'][k]}=={MID}
    assert sum(z['label']=='CERT-MULTIBOARD' for z in out['records'].values())==149
    assert sum(z['label']=='APPROX' for z in out['records'].values())==243
    out.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V36_B196_RANK159',
        CERT_MULTIBOARD=149,APPROX=243,EST=0,TOTAL=392,
        parent_v35_sha256=sha(V35),
        source_evidence=summary,
        B175_sourceblind_sha256=sha(B175),
        B194_original_GTO_pin_SHA256s={k:sha(v) for k,v in PINS.items()},
        B195_real_NL2_BB_IP_index_SHA256=sha(LOCK.with_suffix('').with_suffix('.index.json')),
        source_blind_expansion_ranks=sorted(set(old['source_blind_expansion_ranks'])|{159}),
        supplementary_cert_count=old['supplementary_cert_count']+1,
        B196_rank159_three_true_GTO_NL2_SBBB_BBIP_flops=dict(
            rank=159,model_id=MID,flops=sorted(FLOPS),exact_line=LINE,actor='BB_IP',
            original_GTO_B1_B5_runs={'As7h3d':44736420272,'Js9h4d':44666285424},
            fresh_NL2_BB_IP_run=idx['run_id'],
            preflop_CFR_pinned_not_observed_private_hand=True),
        original_top24_cutoff_unchanged=True,no_generic_texture_GTO=True,
        no_observed_private_card_NL2_rates=True,
        PR2_remains_draft_never_merge=True)
    m=create(out)
    assert (m['CERT_MULTIBOARD'],m['APPROX'])==(149,243)
    assert len(m['models'])==149 and len(m['boards'])==575
    assert m['strict_aggregate']['named_board_proofs']==575
    assert m['strict_aggregate']['hero_lock_variants']>=664
    assert m['strict_aggregate']['b50_research_candidate_boards']>=132
    assert all(x['hero_lock_proofs'] and x['strictly_reachable_combo_count']>0 and
       x['no_general_bet_size_recommendation'] for x in m['boards'])
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    m.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V36_B196',
        parent_v36_status_sha256=sha(OUT),no_general_bet_size_advice=True,
        no_observed_private_card_conditionals=True,
        PR2_remains_draft_never_merge=True)
    MATRIX.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B196 V36 rank159: three true SB_BB BB IP GTO+NL2 named flops\n\n'
       '**149 CERT-MULTIBOARD /243 APPROX /0 EST** out of all 392 models. '
       'Only rank159 upgraded with exact true GTO and correct BB IP NL2 locked '
       'As7h3d/Kd, Js9h4d/Ts, 9s6h3d/Ts on river x b100 c/x x/x. '
       'Original GTO B5/B1 root+job+manifest full 100bb SHA-pinned. '
       'Original preflop solver CFR weights pinned, NOT measured private-card NL2 policy. '
       'All 3 flops strictly combo-reachable, GTO exploitability <=0.5%, SPR error <=5%. '
       'Measured pooled bet-size/street NL2 frequencies kept separate from explicit '
       'assumptions and UNKNOWN; NO observed villain hole-card conditional action rates. '
       '50%-pot nonpolarized label is only named-board research, not universal advice. '
       'Full 575 genuine board proofs and 2475/2475 HU paths must pass independent Actions. '
       'PR #2 stays Draft; NEVER MERGE.\n')
    MATDOC.write_text('# B196 V36: all 575 genuine named GTO/NL2 board lock and 50%-pot evidence\n\n'+write_md(m))
    print(json.dumps(dict(PASS=True,CERT=149,APPROX=243,EST=0,
       promoted_rank=159,true_named_boards=len(m['boards']),
       NL2_hero_lock_variants=m['strict_aggregate']['hero_lock_variants'],
       exact_50pot_research=m['strict_aggregate']['b50_research_candidate_boards'],
       new_real_BB_IP_source_run=idx['run_id'],river_links_required=2475),ensure_ascii=False))
if __name__=='__main__':main()
