#!/usr/bin/env python3
"""B277 V41: source-blind authentic GTO+actor NL2 paired proof deficit ranking
for ALL 238 remaining APPROX model IDs. Original frozen B258 ranks immutable.
Only V41 certified model IDs are removed, never re-rate by prospective GTO.
Optional B274-276 original GTO source is counted ONLY with committed SHA-
verified Rust proof and never treated as NL2 actor locked on GTO alone.
"""
import collections,csv,gzip,hashlib,json,pathlib
from hu_cert_lock_medium_audit import audit

D=pathlib.Path('data');DOC=pathlib.Path('docs')
STATUS=D/'nl2_hu_multiboard_status_v41_b271_rank61.json'
FROZEN=D/'nl2_hu_b258_v39_240_approx_frequency_sourceblind_queue.json'
OUT=D/'nl2_hu_b277_v41_238_approx_true_sourceblind_queue.json'
CSV=D/'nl2_hu_b277_v41_238_approx_true_sourceblind_queue.csv'
MD=DOC/'NL2_HU_B277_V41_238_APPROX_FROZEN_AUTHENTIC_GTO_NL2_PRIORITY.md'
RESEARCH=[
    ('B274',44936238647,'KsJh4d'),
    ('B275',44936370769,'8s7h5d'),
    ('B276',44936829955,'9s6h3d'),
]
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def future_source_status(batch,run,flop):
    pinpath=D/f'nl2_hu_{batch.lower()}_rank71_lmp_{flop}_gto_parent_pin.json'
    indexpath=D/f'solver_evidence/NL2_MULTIBOARD_{batch}_R71_{flop.upper()}_GTO.index.json'
    rawpath=D/f'solver_evidence/NL2_MULTIBOARD_{batch}_R71_{flop.upper()}_GTO.json.gz'
    report=dict(batch=batch,original_GTO_source_run_id=run,flop=flop,
        source_status='NOT_YET_COMMITTED_AND_SHA_VERIFIED_AT_CHECKOUT',
        original_GTO_actor_OOP_river_strict_combos=None,
        actual_NL2_actor_locked_source_present=False,
        counts_as_third_certified_flop=False,cert_upgrade=0)
    if not any(p.is_file() for p in (pinpath,indexpath,rawpath)):
        return report
    # Missing any one of three authentic pinned artifacts fails closed.
    if not all(p.is_file() for p in (pinpath,indexpath,rawpath)):
        report['source_status']='PARTIAL_COMMITTED_ARTIFACT_FAILCLOSED'
        return report
    pin,idx=load(pinpath),load(indexpath)
    assert (pin['source_run_id'],idx['run_id'])==(run,run)
    assert (pin['spot'],pin['flop'],pin['flop_line'],pin['turn_line'])==(
        'LMP_CO_BB',flop,'b50 c','x b50 c')
    assert (pin['target_rank'],pin['model_id'])==(71,'ln-iso-lmp_r_model-vlgh2t')
    assert pin['assumed_limped_169class'] is True and pin['observed_preflop_ranges'] is False
    assert pin['direct_nl2_lock_source_present'] is False
    assert (idx['gto_cases'],idx['locked_cases'],idx['verified_cases'])==(1,0,1)
    assert (idx['original_parent_GTO_root_SHA256'],idx['original_parent_GTO_job_SHA256'],
        idx['original_parent_GTO_manifest_SHA256'])==(
        pin['original_gto_root_sha256'],pin['original_gto_job_sha256'],pin['original_gto_manifest_sha256'])
    assert idx['source_sha256']==hashlib.sha256(gzip.decompress(rawpath.read_bytes())).hexdigest()
    assert idx['gzip_sha256']==sha(rawpath)
    combos=pin['target_exact_actor_OOP_strict_combos']
    assert idx['exact_target_actor_OOP_strict_combos']==combos
    assert combos>=0 and idx['no_generic_model_certification'] is True and idx['immediate_CERT_upgrades']==0
    report.update(source_status='ORIGINAL_GTO_SHA_VERIFIED_ONLY_NEEDS_REAL_NL2_ACTOR_LOCK'
        if combos>0 else 'ORIGINAL_GTO_SHA_VERIFIED_ZERO_STRICT_ACTOR_FAILCLOSED',
        original_GTO_actor_OOP_river_strict_combos=combos,
        source_sha256=idx['source_sha256'],root_sha256=pin['original_gto_root_sha256'])
    return report

def main():
    status=load(STATUS);frozen=load(FROZEN)
    assert status['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V41_B271_RANK61'
    assert (status['CERT_MULTIBOARD'],status['APPROX'],status['EST'],status['TOTAL'])==(154,238,0,392)
    assert status['no_generic_texture_GTO'] and status['no_observed_private_card_NL2_rates']
    assert frozen['schema']=='NL2_HU_B258_V39_240_APPROX_FROZEN_REAL_SOURCEBLIND_PRIORITY_V1'
    assert (frozen['CERT_MULTIBOARD'],frozen['APPROX'],frozen['EST'],frozen['TOTAL'])==(152,240,0,392)
    assert len(frozen['all_240_approx_source_gaps'])==240
    by_model={z['model_id']:z for z in frozen['all_240_approx_source_gaps']}
    assert len(by_model)==240
    removed={mid for mid in by_model if status['records'][mid]['label']=='CERT-MULTIBOARD'}
    assert removed=={'ln-iso-lmp_r_model-wpg493','ln-ipfr-t_model-qpx6tn'}
    records=[v for v in status['records'].values() if v['label']=='APPROX']
    assert len(records)==238
    rows=[];counts=collections.Counter()
    for v in records:
        mid=v['model_id']
        assert mid in by_model,mid
        z=dict(by_model[mid])
        assert (z['rank'],z['model_id'])==(v['frequency_rank'],mid)
        assert z['genuine_paired_flop_count']<3
        assert z['minimum_remaining_new_exact_flop_actor_lock_pairs']==3-z['genuine_paired_flop_count']
        assert z['historical_source_audit_SHA256']==frozen['original_B175_provenance_sha256']
        z['latest_status_label']='APPROX'
        z['snapshot_limit']='ORIGINAL_B175_HISTORICAL_PAIRED_PROOFS_ONLY'
        z['no_fresh_GTO_ONLY_PROMOTED_AS_NL2_PAIR']=True
        rows.append(z);counts[z['priority_cohort']]+=1
    rows.sort(key=lambda z:(z['minimum_remaining_new_exact_flop_actor_lock_pairs'],
       -z['frozen_frequency_proxy'],z['rank']))
    assert len(rows)==238 and all(z['minimum_remaining_new_exact_flop_actor_lock_pairs']>=1 for z in rows)
    assert len({z['model_id'] for z in rows})==238
    assert [z['rank'] for z in rows if z['minimum_remaining_new_exact_flop_actor_lock_pairs']==1]==[71]
    assert rows[0]['rank']==71
    assert status['records']['ln-iso-lmp_r_model-vlgh2t']['label']=='APPROX'
    assert status['records']['ln-iso-lmp_r_model-wpg493']['label']=='CERT-MULTIBOARD'
    assert status['records']['ln-ipfr-t_model-qpx6tn']['label']=='CERT-MULTIBOARD'
    assert status['records']['ln-opfr-t_model-1hmsxaw']['label']=='CERT-MULTIBOARD'
    assert sum(counts.values())==238
    proofs=[future_source_status(batch,run,flop) for batch,run,flop in RESEARCH]
    a=audit(status)
    assert (a['cert_multiboard'],a['approx'],a['EST'])==(154,238,0)
    assert (a['aggregate']['named_board_proofs'],a['aggregate']['paired_hero_locked_source_variants'],
        a['aggregate']['board_examples_with_b50_candidate'])==(590,682,134)
    assert a['not_generalized_handclass_GTO'] and a['not_actual_NL2_earnings']
    out=dict(schema='NL2_HU_B277_V41_238_APPROX_SOURCEBLIND_TRUE_GTO_ACTOR_LOCK_GAP_V1',
        V41_status_sha256=sha(STATUS),parent_B258_V39_snapshot_sha256=sha(FROZEN),
        CERT_MULTIBOARD=154,APPROX=238,EST=0,TOTAL=392,
        original_frozen_provenance_reused_without_frequency_reoptimization=True,
        removed_from_240_approx_because_verified_V41_certified=sorted(removed),
        historical_only_one_flop_short_rank=71,
        one_flop_short=[z for z in rows if z['minimum_remaining_new_exact_flop_actor_lock_pairs']==1],
        all_238_approx_source_gaps=rows,cohort_counts=dict(counts),
        ranked_nearest_3_board_candidates=[dict(rank=z['rank'],model_id=z['model_id'],
            missing=z['minimum_remaining_new_exact_flop_actor_lock_pairs'],
            frozen_frequency_proxy=z['frozen_frequency_proxy']) for z in rows[:40]],
        current_rank71_preregistered_original_GTO_artifact_audit=proofs,
        no_actual_NL2_hero_lock_source_inferred_from_GTO_only=True,
        no_new_GTO_source_claim_without_SHA=True,no_generic_texture_GTO=True,
        no_measured_private_card_NL2_frequency_fabrication=True,
        existing_named_certified_boards=590,existing_hero_lock_variants=682,
        exact_board_nonpolarized_b50_research_only=134,
        PR2_Draft_NEVER_MERGE=True)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    fields=['rank','model_id','spot','family','hero_seat','frozen_frequency_proxy',
      'genuine_paired_flop_count','minimum_remaining_new_exact_flop_actor_lock_pairs',
      'priority_cohort','source_history']
    with CSV.open('w',encoding='utf8',newline='') as fp:
        writer=csv.DictWriter(fp,fieldnames=fields,extrasaction='ignore')
        writer.writeheader();writer.writerows(rows)
    docs=['# B277: V41 exact original GTO+NL2 actor lock deficit (238 APPROX)',
        '','**154 CERT / 238 APPROX / 0 EST**. Full 590 real named-board source / 682 hero lock variants and 134 exact-board b50 candidates retained.',
        'Rank 71 is the only historical **one-third-flop and matching-actor-NL2-lock short** spot.',
        'Rank313 and rank61 were genuinely promoted in V40/V41 and were removed, without rewriting frozen B175/B258 priorities.',
        'Original preflop LMP 169-class distribution remains ASSUMED. The snapshot is conservative: historical GTO+NL2 source pairs are a floor only.',
        'New GTO-only boards B274-B276 are never counted as paired NL2 source, and no canceled/partial solver source is treated as verified.',
        '','## Preregistered rank71 original Rust source status at checkout','']
    for z in proofs:docs.append(f"- {z['batch']} {z['flop']}: {z['source_status']} — strict hero OOP river combos: {z['original_GTO_actor_OOP_river_strict_combos']}")
    docs+=['','## Missing true paired flop count and frozen rank priority','',
       '| Frozen rank | CO/BB spot | Paired genuine flop count | Distinct paired flops still required | Frozen estimated opportunity |',
       '|---:|---|---:|---:|---:|']
    for z in rows[:55]:
        docs.append(f"|{z['rank']}|{z['spot']}|{z['genuine_paired_flop_count']}|"
          f"{z['minimum_remaining_new_exact_flop_actor_lock_pairs']}|{z['frozen_frequency_proxy']:.8f}|")
    docs+=['','No CERT upgraded in B277. Unknown NL2 source frequency is neither measured nor zero. '
      'New original-GTO-only proof requires genuine source-matched Rust NL2 actor lock, '
      'exact public board, strict legal combos and SPR before any 3-board certification. '
      'All 590 actor lock/medium source audits and HU 2475/2475 must PASS. '
      'PR#2 remains Draft, NEVER MERGE.']
    MD.write_text('\n'.join(docs)+'\n')
    print('PASS B277',json.dumps(dict(CERT=154,APPROX=238,one_flop_short_rank=71,
       remaining_cohorts=dict(counts),preregistered_sources=proofs),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
