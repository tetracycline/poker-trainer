#!/usr/bin/env python3
"""B45 V3: existing genuine three-flop LMP rank28 after B42 source-blind cohort.

Preserve original V1 24/368 and supplemental V2 26/366 exactly; do not
upgrade any other rank. Named, restricted 50%-only game with assumed LMP
preflop ranges is NOT generic full-game GTO or observed NL2 private cards.
"""
import copy,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5

ROOT=pathlib.Path('data')
SRC=ROOT/'nl2_hu_multiboard_status_v2_tie.json'
B42=ROOT/'nl2_hu_b42_next6_sourceblind_gaps.json'
OUT=ROOT/'nl2_hu_multiboard_status_v3_rank28.json'
DOC=pathlib.Path('docs/NL2_HU_B45_RANK28_CERT.md')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    base=json.loads(SRC.read_text())
    b42=json.loads(B42.read_text())
    rank=json.loads((ROOT/'nl2_hu_multiboard_prerank.json').read_text())
    queue=json.loads((ROOT/'nl2_hu_stage2_queue.json').read_text())
    assert base['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V2_EQUAL_SCORE_TIE'
    assert base['CERT_MULTIBOARD']==26 and base['APPROX']==366 and base['TOTAL']==392
    assert b42['schema']=='NL2_HU_B42_SOURCE_BLIND_NEXT6_GAP_AUDIT_V1'
    assert b42['source_blind_preselection_ranks']==list(range(27,33))
    assert b42['fixed_rank_sha256']==digest(ROOT/'nl2_hu_multiboard_prerank.json')
    requested=[x for x in b42['rows'] if x['rank']==28]
    assert len(requested)==1 and requested[0]['meets_named_board_certification_evidence']
    rid=requested[0]['model_id']
    assert rid=='ln-iso-lmp_r_model-1siq45p'
    assert base['records'][rid]['label']=='APPROX'
    rn=next(dict(x) for x in rank['nodes'] if x['model_id']==rid)
    m=next(x for x in queue['records'] if x['model_id']==rid)
    assert rn['rank_by_empirically_grounded_frequency_proxy']==28 and not rn['high_frequency_priority']
    assert rn['family']==m['family']=='LMP' and rn['spot']==m['solver_profile']=='LMP_CO_BB'
    rn['preflop_text']=m['preflop_text']
    rn['abstract_action_history']=m['abstract_action_history']
    paths=[pathlib.Path(x) for x in base['source_evidence']['source_files']]
    assert len(paths)>=20 and all(x.is_file() for x in paths)
    exact,locks,meta=build_source_index(ROOT,paths)
    proven,err=candidates(rn,exact,locks,None)
    if err:raise ValueError(err)
    boards,gap=choose_3_5(proven)
    if gap:raise ValueError(gap)
    assert len(boards)==3 and len({x['flop'] for x in boards})==3
    assert set(x['flop'] for x in boards)==set(requested[0]['candidate_3_5_flops'])
    assert len({x['flop_texture'] for x in boards})>=2
    for b in boards:
        assert b['acting_seat']==0 and b['nl2_locked_variants']
        assert all(x['version']=='exp_oop' for x in b['nl2_locked_variants'])
        assert b['source_kind']=='ASSUMED_PREFLOP_RANGES' and b['assumed_preflop_ranges']
        assert b['strict_full_street_combo_reachable']>0
        assert b['genuine_gto_exploitability_pct']<=0.5 and b['relative_spr_error_pct']<=5
        assert b['actual_exact_action_line']=='b50 c/b50 c/'
        assert b['actual_spr']>0 and b['actual_pot_bb']>0 and len(b['source_sha256'])==64
    new=copy.deepcopy(base)
    record=new['records'][rid]
    record.update(label='CERT-MULTIBOARD',
        high_frequency_preregistered=True,
        original_top24_high_frequency_preregistered=False,
        b42_next6_preselected=True,
        b42_preselection_rank=28,
        assumed_LMP_169class_preflop_not_observed=True,
        restricted_LMP_50pct_source_scope=True,
        certified_3_to_5_exact_flop_boards=boards,
        proven_exact_board_count=len(boards),
        blocked_reason=None,
        source_credibility='GITHUB_ACTIONS_AUTHENTIC_CFR_SHA256_AND_FULL_STREET_COMBO_REACH')
    assert all(new['records'][key]==value for key,value in base['records'].items() if key!=rid)
    assert sum(r['label']=='CERT-MULTIBOARD' for r in new['records'].values())==27
    assert sum(r['label']=='APPROX' for r in new['records'].values())==365
    new['schema']='NL2_HU_392_MULTIBOARD_CERT_STATUS_V3_RANK28'
    new['CERT_MULTIBOARD']=27
    new['APPROX']=365
    new['original_v2_cert']=26
    new['original_v2_approx']=366
    new['original_top24_cert']=24
    new['original_top24_approx']=368
    new['original_top24_cutoff_unchanged']=True
    new['source_blind_next6_prereg_ranks']=list(range(27,33))
    new['added_cert_rank']=28
    new['added_cert_model_id']=rid
    new['supplementary_cert_count']=3
    new['parent_v2_sha256']=digest(SRC)
    new['source_blind_b42_sha256']=digest(B42)
    new['source_evidence']=meta
    new['named_board_only_no_generic_texture_GTO']=True
    new['no_real_per_private_combo_NL2_rates']=True
    OUT.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n')
    lines=['# B45 | Rank28 exact-board source-based certification','',
        '**V3 27 CERT / 365 APPROX**, original V2 26/366 and V1 24/368 unchanged.',
        'Rank28 was preregistered source-blind in B42 ranks27–32.',
        'Exactly 3 named flops with SHA-pinned GTO, matching OOP hero locks, legal combo reach and SPR.',
        '',
        '| Flop | Turn | Source GTO run | NL2 lock runs | Strict combos | Bet size evidence |',
        '| --- | --- | ---: | --- | ---: | --- |']
    for b in boards:
        lines.append('| '+b['flop']+' | '+b['turn']+' | '+str(b['source_run_id'])+
          ' | '+str([v['run_id'] for v in b['nl2_locked_variants']])+' | '+
          str(b['strict_full_street_combo_reachable'])+
          ' | '+('50% research candidate' if b['b50_nonpolarized_relative_equity_research_candidate'] else 'unsupported')+' |')
    lines+=['','**Hard limitations:** LMP source uses assumed 169-class preflop ranges and a RESTRICTED 50%-only flop game tree.',
        'This is neither unrestricted full-game GTO nor actual measured LMP private-card player behavior.',
        'One/two strict legal combos are thin evidence; preserve the per-board warning and source exact SHA.',
        'Never generalize named boards to all other textures, or recommend unsupported 50% bet sizes.',
        'Source pool NL2 action-rate marginals are not per-board/per-private-combo observations.',
        'PR #2 stays Draft/Open, never merge.','']
    DOC.write_text('\n'.join(lines))
    print(json.dumps({'schema':new['schema'],'CERT':27,'APPROX':365,
        'rank28_boards':[z['flop'] for z in boards],
        'low_strict_reach':[z['flop'] for z in boards if z['strict_full_street_combo_reachable']<10]},ensure_ascii=False))
if __name__=='__main__':main()
