#!/usr/bin/env python3
"""B190 V34: only independently true GTO and actor-IP-locked exact named boards.

Promote rank199 and rank202 only if authentic B189 Rust children for both
B3 8s8h3d and 9s6h3d actually match original B175 GTO source/run/combo and
the existing KsQh4d GTO+NL2 hero lock on each model. Fail closed.
LMP preflop is assumed explicit 169class, NEVER observational NL2.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md

D=pathlib.Path('data')
V33=D/'nl2_hu_multiboard_status_v33_b179_rank138.json'
B175=D/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
RANKING=D/'nl2_hu_multiboard_prerank.json'
STAGE=D/'nl2_hu_stage2_queue.json'
B3=D/'solver_evidence/NL2_MULTIBOARD_B3.json.gz'
B3INDEX=D/'solver_evidence/NL2_MULTIBOARD_B3.index.json'
PINS={flop:D/('nl2_hu_b188_rank199_202_'+flop+'_B3_gto_pin.json')
 for flop in ('8s8h3d','9s6h3d')}
LOCK=D/'solver_evidence/NL2_MULTIBOARD_B189_R199_R202_B3_2FLOP_EXP_IP.json.gz'
OUT=D/'nl2_hu_multiboard_status_v34_b190_rank199_202.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v34_b190.json'
DOC=pathlib.Path('docs/NL2_HU_B190_V34_TWO_NEW_3FLOP_R199_R202_CERT.md')
MATDOC=pathlib.Path('docs/NL2_HU_B190_V34_ALL_569_NAMED_BOARD_LOCK_MEDIUM.md')
RANKS={199:'ln-iso-lmp_r_model-10l8t7i',202:'ln-iso-lmp_r_model-yh8124'}
FLOPS={'8s8h3d','9s6h3d','KsQh4d'}
LINE='x b33 c/x b50 c/x'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def frozen_evidence():
    v=load(V33);b=load(B175)
    assert v['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V33_B179_RANK138'
    assert (v['CERT_MULTIBOARD'],v['APPROX'],v['EST'],v['TOTAL'])==(145,247,0,392)
    assert len(v['records'])==392
    assert b['schema']=='NL2_HU_B175_V32_ALL_248_GENUINE_GTO_RUN_ACTOR_TURN_SHA_PROVENANCE_V1'
    assert b['v32_sha256']==v['B175_sourceblind_sha256'] or b['v32_sha256']==v['parent_v32_sha256']
    # Sourceblind 248 APPROX was frozen before B179 V33 changed rank138;
    # 199,202 must remain frozen APPROX with one real paired GTO+NL2 flop.
    for rank,mid in RANKS.items():
        assert v['records'][mid]['label']=='APPROX'
        row=next(q for q in b['rows'] if q['rank']==rank)
        assert row['model_id']==mid and row['hero_seat']==1
        assert row['distinct_GTO_plus_NL2_hero_flops']==['KsQh4d']
        assert set(row['distinct_real_GTO_flops'])==FLOPS
    ix=load(B3INDEX)
    assert (ix['run_id'],ix['batch'],ix['gto_cases'],ix['locked_cases'])==(44666294821,'B3',43,90)
    assert ix['gzip_sha256']==sha(B3)
    assert ix['source_sha256']==hashlib.sha256(gzip.decompress(B3.read_bytes())).hexdigest()
    for flop,path in PINS.items():
        q=load(path)
        assert q['schema']=='NL2_HU_B188_RANK199_202_B3_ORIGINAL_GTO_PARENT_PIN_V1'
        assert (q['source_run_id'],q['flop'],q['rank_targets'],q['hero_actor'])==(44666294821,flop,[199,202],1)
        assert q['original_GTO_flop_line']=='x b33 c' and q['target_turn_line']=='x b50 c'
        assert q['exact_river_line']==LINE
        assert q['original_B3_verified_archive_sha256']==sha(B3) and q['original_B3_index_sha256']==sha(B3INDEX)
        assert q['assumed_limped_preflop_169class_not_observed'] is True
        assert q['original_full_GTO_flop_not_recomputed'] is True
        for rank in RANKS:
            row=next(z for z in b['rows'] if z['rank']==rank)
            matched=[z for z in row['exact_authentic_gto_source_proofs']
                if z['flop']==flop and z['turn']==q['turn'] and z['source_run']==44666294821
                and z['source_sha']==q['original_GTO_case_SHA256']
                and z['exact_line']==LINE and z['actor']==1
                and z['strict_legal_combos']>0 and z['GTO_gap_pct']<=.5 and z['SPR_error_pct']<=5]
            assert matched and all(not z['true_NL2_actor_locked'] for z in matched)
    assert LOCK.is_file()
    lx=load(LOCK.with_suffix('').with_suffix('.index.json'))
    raw=gzip.decompress(LOCK.read_bytes())
    le=json.loads(raw)
    assert lx['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert (lx['batch'],lx['actual_spot_flop_version_jobs'],lx['verified_cases'],
       lx['gto_cases'],lx['locked_cases'])==('B189_R199_R202_B3_2FLOP_EXP_IP',2,2,0,2)
    assert lx['source_sha256']==hashlib.sha256(raw).hexdigest()
    assert lx['gzip_sha256']==sha(LOCK)
    assert lx['authentic_GTO_B3_run']==44666294821
    assert lx['exact_IP_line']==LINE and lx['actor_seat']==1
    assert lx['both_new_flops_positive_strict_hero_combo'] is True
    assert lx['strict_failure_reason'] is None and lx['immediate_CERT_upgrades']==0
    assert lx['generic_model_certification']==0
    assert le['source_run_id']==lx['run_id'] and not le['errors'] and len(le['artifacts'])==2
    names=lx['two_real_NL2_actor_IP_flop_sources']
    assert set(names)=={'8s8h3d','9s6h3d'}
    for flop,d in names.items():
        q=load(PINS[flop])
        assert d['strict_combos']>0 and d['nodes']>0
        assert d['GTO_source_run']==44666294821 and d['GTO_root_SHA256']==q['original_gto_root_sha256']
        assert d['GTO_job_SHA256']==q['original_gto_job_sha256']
        assert d['GTO_manifest_SHA256']==q['original_gto_manifest_sha256']
        assert d['original_assumed_169class_preflop_not_observed'] is True
    for case in le['artifacts']:
        assert case['version']=='exp_ip' and case['spot']=='LMP_CO_BB'
        assert case['flop'] in names and not case['errors'] and len(case['cases'])==1
        z=case['cases'][0]
        assert (z['flop_line'],z['turn'])==('x b33 c',load(PINS[case['flop']])['turn'])
        reachable=[n for n in z['nodes'] if
            n['exact_node_line']==LINE and n['acting_seat']==1 and n['strictly_reachable_combos']>0]
        assert reachable and sum(n['strictly_reachable_combos'] for n in reachable)==names[case['flop']]['strict_combos']
    return v,b,lx

def main():
    old,provenance,lx=frozen_evidence()
    files=[pathlib.Path(x) for x in old['source_evidence']['source_files']]
    assert all(p.is_file() for p in files) and len(files)==len(set(files))
    assert LOCK not in files
    files.append(LOCK)
    gto,locked,summary=build_source_index(D,files)
    ranks={x['rank_by_empirically_grounded_frequency_proxy']:x for x in load(RANKING)['nodes']}
    models={x['model_id']:x for x in load(STAGE)['records']}
    new=copy.deepcopy(old)
    proofboard={}
    for rank,mid in RANKS.items():
        model=models[mid]
        assert (model['solver_profile'],model['family'],model['street'])==('LMP_CO_BB','LMP',2)
        assert hero_seat(model['preflop_text'])==1
        pr=copy.deepcopy(ranks[rank])
        assert pr['model_id']==mid
        pr['preflop_text']=model['preflop_text']
        pr['abstract_action_history']=model['abstract_action_history']
        raw,why=candidates(pr,gto,locked,None)
        assert why is None,why
        selected,why=choose_3_5(raw)
        assert why is None,why
        assert len(selected)==3 and {z['flop'] for z in selected}==FLOPS
        assert len({z['flop_texture'] for z in selected})>=2
        for z in selected:
            assert z['actual_exact_action_line']==LINE and z['acting_seat']==1
            assert z['source_kind']=='ASSUMED_EXPLICIT_169CLASS'
            assert z['assumed_preflop_ranges'] is True
            assert z['strict_full_street_combo_reachable']>0 and z['exact_combo_reachable']>0
            assert z['genuine_gto_exploitability_pct']<=.5 and z['relative_spr_error_pct']<=5
            assert z['nl2_locked_variants'] and all(t['version']=='exp_ip' for t in z['nl2_locked_variants'])
            assert len(z['source_sha256'])==64
        for flop in ('8s8h3d','9s6h3d'):
            z=next(q for q in selected if q['flop']==flop)
            pin=load(PINS[flop])
            assert (z['source_run_id'],z['source_sha256'],z['turn'])==(
                44666294821,pin['original_GTO_case_SHA256'],pin['turn'])
            assert any(t['run_id']==lx['run_id'] for t in z['nl2_locked_variants'])
        oldthird=next(z for z in selected if z['flop']=='KsQh4d')
        assert oldthird['source_run_id']==44666294821
        assert any(t['run_id']!=lx['run_id'] for t in oldthird['nl2_locked_variants'])
        new['records'][mid].update(
            label='CERT-MULTIBOARD',high_frequency_preregistered=True,
            original_top24_high_frequency_preregistered=False,
            source_blind_expansion_rank=rank,
            prereg_cohort='B175_V32_FROZEN_TWO_MISSING_ORIGINAL_B3_TRUE_GTO_NL2_IP_FLOPS',
            certified_3_to_5_exact_flop_boards=selected,
            proven_exact_board_count=3,blocked_reason=None,
            source_credibility='B188_EXACT_ORIGINAL_B3_GTO_SHA_PLUS_B189_TRUE_IP_RUST_CHILD_2_FLOPS_PLUS_VERIFIED_KSQH4D_PRIOR_NL2')
        proofboard[str(rank)]=dict(model_id=mid,flops=sorted(FLOPS),
           new_hero_lock_run=lx['run_id'],original_gto_run=44666294821,actor='CO_IP')
    changed={k for k in old['records'] if old['records'][k]!=new['records'][k]}
    assert changed==set(RANKS.values())
    assert sum(v['label']=='CERT-MULTIBOARD' for v in new['records'].values())==147
    assert sum(v['label']=='APPROX' for v in new['records'].values())==245
    new.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V34_B190_RANK199_202',
       CERT_MULTIBOARD=147,APPROX=245,EST=0,TOTAL=392,
       parent_v33_sha256=sha(V33),
       source_evidence=summary,
       B175_sourceblind_sha256=sha(B175),
       B188_parent_pin_sha256s={flop:sha(p) for flop,p in PINS.items()},
       B189_verified_NL2_hero_IP_index_sha256=sha(LOCK.with_suffix('').with_suffix('.index.json')),
       source_blind_expansion_ranks=sorted(set(old['source_blind_expansion_ranks'])|set(RANKS)),
       supplementary_cert_count=old['supplementary_cert_count']+2,
       B190_rank199_202_three_real_GTO_NL2_pairing=proofboard,
       original_top24_cutoff_unchanged=True,
       no_generic_texture_GTO=True,no_observed_private_card_NL2_rates=True,
       PR2_remains_draft_never_merge=True)
    m=create(new)
    assert (m['CERT_MULTIBOARD'],m['APPROX'])==(147,245)
    assert len(m['models'])==147 and len(m['boards'])==569
    assert m['strict_aggregate']['named_board_proofs']==569
    assert m['strict_aggregate']['hero_lock_variants']>=661
    assert m['strict_aggregate']['b50_research_candidate_boards']>=132
    assert all(z['hero_lock_proofs'] and z['strictly_reachable_combo_count']>0 and
        z['no_general_bet_size_recommendation'] for z in m['boards'])
    OUT.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n')
    m.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V34_B190',
       parent_v34_status_sha256=sha(OUT),
       no_general_bet_size_advice=True,
       no_observed_private_card_conditionals=True,
       PR2_remains_draft_never_merge=True)
    MATRIX.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B190 V34: two independent 3-board CERT upgrades for rank199 and rank202\n\n'
      '**147 CERT-MULTIBOARD /245 APPROX /0 EST**, all **392** original models. '
      'Only rank199 and rank202 switched label. Each has exactly 3 genuinely '
      'solved GTO + hero-IP true NL2 locked flops: 8s8h3d/5s, 9s6h3d/Ts, '
      'KsQh4d/Tc; exact river line x b33 c/x b50 c/x; GTO <=0.5%, SPR error <=5%, '
      'all full-street legal combos >0. Original full-size GTO root run 44666294821, '
      'fresh B189 genuine Rust NL2 partial child on the two previously unpaired flops. '
      'LMP preflop assumed 169-class, NOT real NL2 preflop range observations. '
      'Pooled villain street/size NL2 frequencies are NOT measured private-hand conditionals. '
      '50%-pot nonpolar candidate applies only where exact-board proof exists, '
      'not arbitrary textures. 2475 HU links must remain connected. '
      'Draft PR #2, NEVER MERGE.\n')
    MATDOC.write_text('# B190 V34: all 569 original named boards with actor-lock provenance and medium50 research\n\n'+write_md(m))
    print(json.dumps(dict(PASS=True,CERT=147,APPROX=245,EST=0,
       source_run=lx['run_id'],upgraded_ranks=sorted(RANKS),
       true_GTO_NL2_named_boards=len(m['boards']),
       nl2_actor_lock_variants=m['strict_aggregate']['hero_lock_variants'],
       b50_nonpolar_exact_research=m['strict_aggregate']['b50_research_candidate_boards'],
       river_links_required=2475),ensure_ascii=False))
if __name__=='__main__':main()
