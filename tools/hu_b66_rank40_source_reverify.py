#!/usr/bin/env python3
"""B66: reverify original immutable B52 SB_BB EXP_IP under *full-length*
focused action-prefix gate, independently proving actual hero-IP turn nodes.

Never promote rank40 from successful compilation alone. Verify exact source,
actor, SPR, public cards, strict reach and matched old GTO before eligibility.
"""
import gzip,hashlib,json,pathlib,sys
sys.path.insert(0,'tools')
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat

R=pathlib.Path('data')
RAW=R/'solver_evidence/NL2_MULTIBOARD_B66_SB_B100_IP.json'
GZ=R/'solver_evidence/NL2_MULTIBOARD_B66_SB_B100_IP.json.gz'
IX=R/'solver_evidence/NL2_MULTIBOARD_B66_SB_B100_IP.index.json'
OUT=R/'nl2_hu_b66_rank40_source_reverification.json'
DOC=pathlib.Path('docs/NL2_HU_B66_RANK40_SOURCE_REVERIFICATION.md')
V8=R/'nl2_hu_multiboard_status_v8_batch61.json'
B48=R/'nl2_hu_b48_next9_sourceblind_gaps.json'
MODEL='ln-ipc-t_model-188b2d5'
def sha(bytes_):return hashlib.sha256(bytes_).hexdigest()

def main():
    source=json.loads(RAW.read_text())
    v8=json.loads(V8.read_text())
    b48=json.loads(B48.read_text())
    assert v8['CERT_MULTIBOARD']==56 and v8['APPROX']==336
    assert v8['records'][MODEL]['label']=='APPROX'
    prereg=next(x for x in b48['rows'] if x['rank']==40)
    assert prereg['model_id']==MODEL and prereg['missing_to_three_flops']==1
    assert source['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert source['source_run_id']==44809135555
    scope=dict(schema='NL2_HU_B66_B52_SB_B100_IP_REVERIFICATION_V1',
       original_github_run_id=44809135555,
       selected_original_artifact='nl2-multiboard-B52_TWO_IP_LOCKS-SB_BB-exp_ip-9s6h3d',
       original_B52_verification_was_failure=True,
       focused_prefix_gate_corrected_for_3_tokens=True,
       previous_B62_CO_BB_valid_only_snapshot_untouched=True,
       previous_B64_CO_BB_rank41_exclusion_untouched=True,
       current_cert=56,current_approx=336,
       preselected_rank=40,model_id=MODEL,
       source_verification_errors=source['errors'],
       authentic_source_verifier_pass=False,
       verified_archive_index_sha256=None,
       actual_actor_IP_exact_nodes=[],
       matching_real_GTO_and_hero_lock_flops=[],
       expected_rank40_exact_line='x b100 c/x',
       eligible_for_separate_cert_version=False,
       no_automatic_model_label_upgrade=True,
       per_private_combo_NL2_rates_not_observed=True,
       PR2_remains_draft_never_merge=True)
    issues=[]
    if source['errors']:
        issues.append('STRICT_ORIGINAL_SOLVER_SOURCE_REJECTED')
    else:
        arts=source.get('artifacts',[])
        if len(arts)!=1 or any(not z.get('cases') or z.get('errors') for z in arts):
            issues.append('NOT_EXACTLY_ONE_VALID_SOLVER_ARTIFACT')
        elif (arts[0]['spot'],arts[0]['flop'],arts[0]['version'])!=('SB_BB','9s6h3d','exp_ip'):
            issues.append('MISMATCHED_IMMUTABLE_ORIGINAL_ARTIFACT')
        elif not all(c['flop_line']=='x b100 c' for c in arts[0]['cases']):
            issues.append('ACTUAL_FLOP_LINE_NOT_X_B100_CALL')
        elif source['exact_board_gto_sources']!=0 or source['imputed_pool_locked_sources']<1:
            issues.append('INCORRECT_GTO_VS_PARTIAL_LOCK_SOURCE')
        else:
            scope['authentic_source_verifier_pass']=True
            origin=arts[0]
            acting=[dict(flop=c['flop'],turn=c['turn'],board=n['public_board'],
                    exact_line=n['exact_node_line'],actor=n['acting_seat'],
                    strictly_reachable_combos=n['strictly_reachable_combos'])
                    for c in origin['cases'] for n in c['nodes']
                    if n['acting_seat']==1 and n['strictly_reachable_combos']>0]
            scope['actual_actor_IP_exact_nodes']=acting[:30]
            bytes_=RAW.read_bytes()
            zipped=gzip.compress(bytes_,compresslevel=9,mtime=0)
            GZ.write_bytes(zipped)
            index=dict(schema='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1',
                batch='B66_SB_B100_IP',run_id=44809135555,
                actual_spot_flop_version_jobs=1,
                verified_cases=source['new_authentic_board_cases'],
                gto_cases=source['exact_board_gto_sources'],
                locked_cases=source['imputed_pool_locked_sources'],
                source_sha256=sha(bytes_),gzip_sha256=sha(zipped),
                generic_model_certification=0,
                originally_rejected_due_to_full_prefix_verification_bug=True,
                corrected_prefix_required=['x','b100','c'],
                original_B52_artifact_unmodified=True,
                old_B62_and_B64_results_unchanged=True,
                no_automatic_GENERIC_CERT=True)
            IX.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
            scope['verified_archive_index_sha256']=sha(IX.read_bytes())
            rank=json.loads((R/'nl2_hu_multiboard_prerank.json').read_text())
            queue=json.loads((R/'nl2_hu_stage2_queue.json').read_text())
            r=next(dict(x) for x in rank['nodes'] if x['model_id']==MODEL)
            m=next(x for x in queue['records'] if x['model_id']==MODEL)
            r['preflop_text']=m['preflop_text']
            r['abstract_action_history']=m['abstract_action_history']
            assert r['rank_by_empirically_grounded_frequency_proxy']==40
            assert hero_seat(r['preflop_text'])==1
            original=[pathlib.Path(z) for z in v8['source_evidence']['source_files']]
            assert GZ not in original and all(z.is_file() for z in original)
            exact,lock,meta=build_source_index(R,original+[GZ])
            refs,reason=candidates(r,exact,lock,None)
            boards,gap=choose_3_5(refs) if reason is None else ([],reason)
            scope['matching_real_GTO_and_hero_lock_flops']=[
                dict(flop=x['flop'],turn=x['turn'],line=x['actual_exact_action_line'],
                actor=x['acting_seat'],gto_run=x['source_run_id'],
                hero_lock_run_ids=[v['run_id'] for v in x['nl2_locked_variants']],
                legal_combo_count=x['strict_full_street_combo_reachable'])
                for x in boards]
            if gap:
                issues.append('STILL_NOT_CERTIFIABLE:'+str(gap))
            elif len(boards)<3:
                issues.append('STILL_LESS_THAN_THREE_MATCHED_REAL_FLOPS')
            elif not any(x['flop']=='9s6h3d' and x['acting_seat']==1 and
                      any(v['run_id']==44809135555 for v in x['nl2_locked_variants'])
                      for x in boards):
                issues.append('VERIFIED_SOURCE_NOT_APPLICABLE_TO_GTO_RANK40_HERO')
            else:
                scope['eligible_for_separate_cert_version']=True
    scope['remaining_gate_issues']=issues
    scope['status']='ELIGIBLE_FOR_NEW_VERSION' if scope['eligible_for_separate_cert_version'] else 'SAFE_SOURCE_EXCLUSION'
    OUT.write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B66 | Rank40 genuine exact SB_BB source validation\n\n'+
      'Original B52 Rust solver artifact immutable, original B52 group failed verification.\n'+
      'Corrected strictly full focused flop action prefix x-b100-call (3 tokens, not 2).\n'+
      'Source verified: '+str(scope['authentic_source_verifier_pass'])+
      '; separate rank40 certification eligible: '+str(scope['eligible_for_separate_cert_version'])+'.\n'+
      'Matched independently pinned GTO and actor-IP hero lock boards: '+
      str(scope['matching_real_GTO_and_hero_lock_flops'])+'.\n'+
      'Residual gate issues: '+str(issues)+'.\n'+
      'Original V8 56 CERT / 336 APPROX unchanged until a separately verified version.\n'+
      'Rank41 B64 rejection and previous B62 valid CO_BB archive are untouched.\n'+
      'No fabricated private-combo player behavior, no generic GTO, never merge Draft PR #2.\n')
    print(json.dumps({k:scope[k] for k in (
        'status','authentic_source_verifier_pass','eligible_for_separate_cert_version',
        'matching_real_GTO_and_hero_lock_flops','remaining_gate_issues','current_cert','current_approx')},ensure_ascii=False))

if __name__=='__main__':main()
