#!/usr/bin/env python3
"""B193 V35: upgrade only frozen rank201 with three genuine GTO+NL2 named flops.

Real original B3 GTO parent 44666294821, fresh B192 two Rust actor-IP
children x b33 c/x b100 c/x; original KsQh4d third flop paired to exact
NL2 actor-IP lock. ASSUMED 169-class limp preflop explicitly not observed.
No generic flop texture GTO or real private-card pool rate claims.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md

D=pathlib.Path('data')
V34=D/'nl2_hu_multiboard_status_v34_b190_rank199_202.json'
B175=D/'nl2_hu_b175_v32_248_exact_GTO_source_provenance.json'
RANK=D/'nl2_hu_multiboard_prerank.json'
STAGE=D/'nl2_hu_stage2_queue.json'
B3=D/'solver_evidence/NL2_MULTIBOARD_B3.json.gz'
B3I=D/'solver_evidence/NL2_MULTIBOARD_B3.index.json'
PINS={flop:D/('nl2_hu_b191_rank201_'+flop+'_B3_original_gto_pin.json')
 for flop in ('8s8h3d','9s6h3d')}
B192=D/'solver_evidence/NL2_MULTIBOARD_B192_R201_B3_2FLOP_EXP_IP.json.gz'
OUT=D/'nl2_hu_multiboard_status_v35_b193_rank201.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v35_b193.json'
DOC=pathlib.Path('docs/NL2_HU_B193_V35_RANK201_THREE_ORIGINAL_GTO_NL2_CERT.md')
MATDOC=pathlib.Path('docs/NL2_HU_B193_V35_ALL_572_NAMED_BOARD_LOCK_MEDIUM.md')
MID='ln-iso-lmp_r_model-qsgdjf'
FLOPS={'8s8h3d','9s6h3d','KsQh4d'}
LINE='x b33 c/x b100 c/x'

def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def freeze():
    old=load(V34);f=load(B175)
    assert old['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V34_B190_RANK199_202'
    assert (old['CERT_MULTIBOARD'],old['APPROX'],old['EST'],old['TOTAL'])==(147,245,0,392)
    assert len(old['records'])==392 and old['records'][MID]['label']=='APPROX'
    assert old['records']['ln-iso-lmp_r_model-10l8t7i']['label']=='CERT-MULTIBOARD'
    assert old['records']['ln-iso-lmp_r_model-yh8124']['label']=='CERT-MULTIBOARD'
    assert old['records']['ln-iso-lmp_r_model-vlgh2t']['label']=='APPROX'
    assert old['records']['ln-iso-lmp_r_model-wpg493']['label']=='APPROX'
    assert old['parent_v33_sha256']==sha(D/'nl2_hu_multiboard_status_v33_b179_rank138.json')
    assert old['B175_sourceblind_sha256']==sha(B175)
    row=next(x for x in f['rows'] if x['rank']==201)
    assert row['model_id']==MID and row['hero_seat']==1
    assert row['distinct_GTO_plus_NL2_hero_flops']==['KsQh4d']
    assert set(row['distinct_real_GTO_flops'])==FLOPS
    ix=load(B3I)
    assert (ix['batch'],ix['run_id'],ix['gto_cases'],ix['locked_cases'])==('B3',44666294821,43,90)
    assert ix['gzip_sha256']==sha(B3)
    assert ix['source_sha256']==hashlib.sha256(gzip.decompress(B3.read_bytes())).hexdigest()
    for flop,path in PINS.items():
        p=load(path)
        assert p['schema']=='NL2_HU_B191_RANK201_B3_ORIGINAL_XB33_XB100_GTO_PARENT_PIN_V1'
        assert (p['source_run_id'],p['target_rank'],p['model_id'])==(44666294821,201,MID)
        assert p['flop']==flop and p['spot']=='LMP_CO_BB' and p['actor']==1
        assert p['exact_river_line']==LINE and p['original_GTO_flop_line']=='x b33 c' and p['target_turn_line']=='x b100 c'
        assert p['minimum_strict_original_GTO_legal_IP_combos']>0
        assert p['original_assumed_preflop_169class_not_measured'] is True
        assert p['original_full_GTO_flop_not_recomputed'] is True
        assert p['original_B3_verified_archive_sha256']==sha(B3)
        assert p['original_B3_index_sha256']==sha(B3I)
        found=[x for x in row['exact_authentic_gto_source_proofs'] if
            x['flop']==flop and x['turn']==p['turn'] and x['source_run']==44666294821
            and x['source_sha']==p['original_GTO_case_SHA256'] and x['actor']==1
            and x['exact_line']==LINE and x['strict_legal_combos']>0 and
            x['GTO_gap_pct']<=.5 and x['SPR_error_pct']<=5]
        assert found and all(not x['true_NL2_actor_locked'] for x in found)
    assert B192.is_file()
    gz=B192.read_bytes()
    j=load(B192.with_suffix('').with_suffix('.index.json'))
    r=json.loads(gzip.decompress(gz))
    assert j['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert (j['batch'],j['actual_spot_flop_version_jobs'],j['verified_cases'],j['gto_cases'],j['locked_cases'])==(
        'B192_R201_B3_2FLOP_EXP_IP',2,2,0,2)
    assert j['source_sha256']==hashlib.sha256(gzip.decompress(gz)).hexdigest()
    assert j['gzip_sha256']==sha(B192)
    assert j['authentic_GTO_B3_run']==44666294821
    assert j['exact_IP_line']==LINE and j['actor_seat']==1
    assert j['both_new_flops_positive_strict_hero_combo'] is True and j['strict_failure_reason'] is None
    assert j['immediate_CERT_upgrades']==0 and j['generic_model_certification']==0
    assert r['source_run_id']==j['run_id'] and not r['errors'] and len(r['artifacts'])==2
    details=j['two_real_NL2_actor_IP_flop_sources']
    assert set(details)=={'8s8h3d','9s6h3d'}
    for flop,d in details.items():
        p=load(PINS[flop])
        assert d['GTO_source_run']==44666294821 and d['nodes']>0 and d['strict_combos']>0
        assert (d['GTO_root_SHA256'],d['GTO_job_SHA256'],d['GTO_manifest_SHA256'])==(
            p['original_gto_root_sha256'],p['original_gto_job_sha256'],p['original_gto_manifest_sha256'])
        assert d['original_assumed_169class_preflop_not_observed'] is True
    for a in r['artifacts']:
        assert (a['spot'],a['version'])==('LMP_CO_BB','exp_ip') and a['flop'] in details
        assert not a['errors'] and len(a['cases'])==1
        c=a['cases'][0]
        assert c['flop_line']=='x b33 c' and c['turn']==load(PINS[a['flop']])['turn']
        valid=[x for x in c['nodes'] if x['exact_node_line']==LINE and x['acting_seat']==1 and x['strictly_reachable_combos']>0]
        assert valid and sum(x['strictly_reachable_combos'] for x in valid)==details[a['flop']]['strict_combos']
    return old,j

def main():
    old,idx=freeze()
    sources=[pathlib.Path(x) for x in old['source_evidence']['source_files']]
    assert sources and len(sources)==len(set(sources)) and all(x.is_file() for x in sources)
    assert B192 not in sources
    sources.append(B192)
    gto,locked,meta=build_source_index(D,sources)
    rank=next(copy.deepcopy(x) for x in load(RANK)['nodes'] if x['rank_by_empirically_grounded_frequency_proxy']==201)
    model=next(x for x in load(STAGE)['records'] if x['model_id']==MID)
    assert rank['model_id']==MID and (model['solver_profile'],model['family'],model['street'])==('LMP_CO_BB','LMP',2)
    assert hero_seat(model['preflop_text'])==1
    rank['preflop_text']=model['preflop_text']
    rank['abstract_action_history']=model['abstract_action_history']
    cs,why=candidates(rank,gto,locked,None)
    assert why is None,why
    boards,why=choose_3_5(cs)
    assert why is None,why
    assert len(boards)==3 and {x['flop'] for x in boards}==FLOPS
    assert len({x['flop_texture'] for x in boards})>=2
    for b in boards:
        assert b['acting_seat']==1 and b['actual_exact_action_line']==LINE
        assert b['source_kind'].startswith('ASSUMED') and b['assumed_preflop_ranges'] is True
        assert b['strict_full_street_combo_reachable']>0 and b['exact_combo_reachable']>0
        assert b['genuine_gto_exploitability_pct']<=.5 and b['relative_spr_error_pct']<=5
        assert b['nl2_locked_variants'] and all(x['version']=='exp_ip' for x in b['nl2_locked_variants'])
        assert len(b['source_sha256'])==64
    for flop in ('8s8h3d','9s6h3d'):
        b=next(x for x in boards if x['flop']==flop)
        pin=load(PINS[flop])
        assert (b['source_run_id'],b['source_sha256'],b['turn'])==(44666294821,pin['original_GTO_case_SHA256'],pin['turn'])
        assert any(z['run_id']==idx['run_id'] for z in b['nl2_locked_variants'])
    third=next(x for x in boards if x['flop']=='KsQh4d')
    assert third['source_run_id']==44666294821 and any(x['run_id']!=idx['run_id'] for x in third['nl2_locked_variants'])
    out=copy.deepcopy(old)
    out['records'][MID].update(
        label='CERT-MULTIBOARD',high_frequency_preregistered=True,
        original_top24_high_frequency_preregistered=False,
        source_blind_expansion_rank=201,
        prereg_cohort='B175_V32_FROZEN_RANK201_TWO_MISSING_TRUE_GTO_PLUS_NL2_IP_B3_FLOPS',
        certified_3_to_5_exact_flop_boards=boards,
        proven_exact_board_count=3,blocked_reason=None,
        source_credibility='B191_ORIGINAL_B3_SHA_8S8H3D_9S6H3D_PLUS_B192_REAL_NL2_IP_RUST_PLUS_OFFICIAL_KSQH4D')
    assert {k for k in old['records'] if old['records'][k]!=out['records'][k]}=={MID}
    assert sum(v['label']=='CERT-MULTIBOARD' for v in out['records'].values())==148
    assert sum(v['label']=='APPROX' for v in out['records'].values())==244
    out.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V35_B193_RANK201',
       CERT_MULTIBOARD=148,APPROX=244,EST=0,TOTAL=392,
       parent_v34_sha256=sha(V34),source_evidence=meta,
       B175_sourceblind_sha256=sha(B175),
       B191_pin_SHA256s={flop:sha(p) for flop,p in PINS.items()},
       B192_true_NL2_CO_IP_source_index_SHA256=sha(B192.with_suffix('').with_suffix('.index.json')),
       source_blind_expansion_ranks=sorted(set(old['source_blind_expansion_ranks'])|{201}),
       supplementary_cert_count=old['supplementary_cert_count']+1,
       B193_rank201_three_original_GTO_NL2_named_flops=dict(
          rank=201,model_id=MID,flops=sorted(FLOPS),
          exact_line=LINE,actor='CO_IP',
          original_GTO_B3_run=44666294821,
          new_real_NL2_actor_IP_run=idx['run_id'],
          preflop_169class_ASSUMED_not_observed=True),
       original_top24_cutoff_unchanged=True,
       no_generic_texture_GTO=True,no_observed_private_card_NL2_rates=True,
       PR2_remains_draft_never_merge=True)
    m=create(out)
    assert (m['CERT_MULTIBOARD'],m['APPROX'])==(148,244)
    assert len(m['models'])==148 and len(m['boards'])==572
    assert m['strict_aggregate']['named_board_proofs']==572
    assert m['strict_aggregate']['hero_lock_variants']>=664
    assert m['strict_aggregate']['b50_research_candidate_boards']>=132
    assert all(x['hero_lock_proofs'] and x['strictly_reachable_combo_count']>0 and
       x['no_general_bet_size_recommendation'] for x in m['boards'])
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    m.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V35_B193',
       parent_v35_status_sha256=sha(OUT),
       no_general_bet_size_advice=True,
       no_observed_private_card_conditionals=True,
       PR2_remains_draft_never_merge=True)
    MATRIX.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B193 V35 rank201: exact B3 original GTO + NL2 actor-IP 3-flop CERT\n\n'
      '**148 CERT-MULTIBOARD /244 APPROX /0 EST** across all 392 original models. '
      'Only rank201 is promoted. Exactly 3 genuine public flops: 8s8h3d/5s, '
      '9s6h3d/Ts and KsQh4d/Tc, original B3 true 100bb GTO flop plus '
      'genuine correct-actor CO IP NL2 turn-river Rust locks; all strict '
      'full-street combo >0, original GTO exploitability <=0.5%, SPR error <=5%. '
      'Specific exact x b33 c/x b100 c/x river line only. '
      'Preflop 169-class LMP ranges are ASSUMED and not NL2 measurements. '
      'Pooled bet-size NL2 frequencies measured where available, defaults '
      'explicitly assumed where unavailable; no observed private-card '
      'conditional rates or generalized GTO/100% pot bet recommendation. '
      'Complete 572 named-board provenance and 2475 HU paths must pass Actions; '
      'PR #2 remains Draft, NEVER MERGE.\n')
    MATDOC.write_text('# B193 V35 all 572 named-board NL2 lock and medium-size provenance\n\n'+write_md(m))
    print(json.dumps(dict(PASS=True,CERT=148,APPROX=244,EST=0,
       newly_CERT_rank=201,boards=len(m['boards']),
       locks=m['strict_aggregate']['hero_lock_variants'],
       b50_exact_research=m['strict_aggregate']['b50_research_candidate_boards'],
       source_run=idx['run_id'],river_links_required=2475),ensure_ascii=False))
if __name__=='__main__':main()
