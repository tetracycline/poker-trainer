#!/usr/bin/env python3
"""B107 SHA-pin original individually verified CO_BB Js9h4d GTO flop.

The ORIGINAL B2 overall run failed because of an unrelated SB3_BTN GTO job;
its authenticated CO_BB Js9h4d GTO artifact was independently admitted into
B2_PARTIAL. Never claim whole failed run validated, do not reuse failed job.
Predeclared source-blind rank215/220 share one missing actor-IP lock.
"""
import argparse,gzip,hashlib,json,pathlib
R=pathlib.Path('data')
IDX=R/'solver_evidence/NL2_MULTIBOARD_B2_PARTIAL.index.json'
ARCH=R/'solver_evidence/NL2_MULTIBOARD_B2_PARTIAL.json.gz'
B79=R/'nl2_hu_b79_next20_sourceblind_gaps.json'
B81=R/'nl2_hu_b81_next20_sourceblind_gaps.json'
V25=R/'nl2_hu_multiboard_status_v25_b106_rank135.json'
OUT=R/'nl2_hu_b107_co_js9h4d_b2_gto_parent_pin.json'
DOC=pathlib.Path('docs/NL2_HU_B107_CO_B2_JS9H4D_GTO_PARENT_PIN.md')
RUN=44666290556
SPOT='CO_BB';FLOP='Js9h4d';TURN='Ts'
FLOPLINE='x b33 c';TURNLINE='x b100 c'
TARGETS={215:'ln-ipfr-r_model-2h1iyv',220:'ln-ipfr-r_model-nzfk3y'}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(buf):return hashlib.sha256(buf).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--artifact-root',required=True,type=pathlib.Path)
    args=parser.parse_args()
    index=json.loads(IDX.read_text())
    raw=gzip.decompress(ARCH.read_bytes());verified=json.loads(raw)
    assert index['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert index['batch']=='B2_PARTIAL' and index['run_id']==RUN
    assert index['actual_spot_flop_version_jobs']==17
    assert index['gto_cases']>=40 and index['verified_cases']>=200
    assert 'SB3_BTN' in index['failed_source_job'] and 'excluded' in index['failed_source_job']
    assert index['gzip_sha256']==sha(ARCH) and index['source_sha256']==digest(raw)
    assert verified['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert verified['source_run_id']==RUN and not verified['errors']
    selected=[a for a in verified['artifacts'] if
              (a['spot'],a['version'],a['flop'])==(SPOT,'gto',FLOP)]
    assert len(selected)==1 and selected[0]['cases'] and not selected[0]['errors']
    cases=[x for x in selected[0]['cases'] if
           (x['flop_line'],x['turn'])==(FLOPLINE,TURN)]
    assert len(cases)==1
    actors=[n for n in cases[0]['nodes'] if n['acting_seat']==1 and
            n['exact_node_line']=='x b33 c/x b100 c/x' and n['strictly_reachable_combos']>0]
    assert actors, 'Original B2 GTO CO_BB has no exact actor-IP river node on preregistered path'
    artifact=args.artifact_root
    manifest=artifact/'evidence/CO_BB-gto-Js9h4d.json'
    assert manifest.is_file()
    source=json.loads(manifest.read_text())
    assert source['schema']=='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1'
    assert (source['spot'],source['version'],source['flop'])==(SPOT,'gto',FLOP)
    assert (source['root_pot_bb'],source['root_remaining_bb'])==(5.5,97.5)
    assert source['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
    assert source['no_generic_certification'] and not source['failures']
    flopfile=artifact/'solver/postflop'/source['file_flop']
    jobfile=flopfile.with_suffix('.job.json')
    assert flopfile.is_file() and jobfile.is_file()
    assert sha(flopfile)==source['file_flop_sha256']
    flop=json.loads(flopfile.read_text());job=json.loads(jobfile.read_text())
    assert (flop['flop'],flop['pot'],flop['stack'])==(FLOP,550,9750)
    assert (job['pot'],job['stack'])==(550,9750)
    assert job.get('hero') is None and not job.get('locks')
    assert job['rake_rate']==.05 and job['rake_cap']==1000
    assert all(v in job.get('flop_oop','') for v in ('33%','50%','75%','100%'))
    assert all(v in job.get('flop_ip','') for v in ('33%','50%','75%','100%'))
    roots=[n for n in flop['nodes'] if n['line']==FLOPLINE+'/' and n['board'][-2:]==TURN]
    assert len(roots)==1
    parent=roots[0]
    assert all(any(float(w)>1e-4 for w in ws) for ws in parent['wr'])
    rank=json.loads((R/'nl2_hu_multiboard_prerank.json').read_text())
    rank_sha=sha(R/'nl2_hu_multiboard_prerank.json')
    a=json.loads(B79.read_text());b=json.loads(B81.read_text())
    assert a['fixed_rank_sha256']==b['fixed_rank_sha256']==rank_sha
    assert a['source_blind_preselection_ranks']==list(range(196,216))
    assert b['source_blind_preselection_ranks']==list(range(216,236))
    v25=json.loads(V25.read_text())
    assert (v25['CERT_MULTIBOARD'],v25['APPROX'])==(135,257)
    summary={}
    for i,mid in TARGETS.items():
        cohort=a if i==215 else b
        row=next(x for x in cohort['rows'] if x['rank']==i)
        assert row['model_id']==mid and row['missing_to_three_flops']==1
        assert row['matched_hero_side_NL2_lock_flops']==['8s8h3d','As9h2d']
        assert row['matching_true_GTO_flops']==['8s8h3d','As9h2d','Js9h4d']
        assert row['model_spr']==3.145
        assert row['source_samples'][2]['GTO_run']==RUN
        assert row['source_samples'][2]['line']=='x b33 c/x b100 c/x'
        assert v25['records'][mid]['label']=='APPROX'
        summary[str(i)]=dict(model_id=mid,existing_two_locked_flops=['8s8h3d','As9h2d'],missing_GTO_only='Js9h4d')
    d=dict(schema='NL2_HU_B107_CO_B2_JS9H4D_GTO_PARENT_V1',
      result='PASS_INDIVIDUALLY_VERIFIED_B2_GTO_ARTIFACT',
      full_B2_workflow_failed_unrelated_job=True,
      B2_failed_SB3_BTN_GTO_job_explicitly_excluded=True,
      B2_PARTIAL_source_archive_SHA256=sha(ARCH),
      original_source_run_id=RUN,
      original_manifest_SHA256=sha(manifest),
      original_GTO_flop_SHA256=sha(flopfile),
      original_GTO_job_SHA256=sha(jobfile),
      original_GTO_flop_relative_path=source['file_flop'],
      original_full_flop_size_tree=True,
      source_root_pot_bb=5.5,source_root_stack_bb=97.5,
      source_preflop_CFR_pinned_not_observed_private_card=True,
      public_flop=FLOP,turn=TURN,
      flop_line=FLOPLINE,turn_line=TURNLINE,
      required_IP_river_line='x b33 c/x b100 c/x',
      original_GTO_positive_strict_IP_actor_node_count=len(actors),
      GTO_original_sequential_combo_sample=[n['strictly_reachable_combos'] for n in actors[:6]],
      original_parent_pot_bb=parent['pot']/100,
      original_parent_remaining_stack_bb=(flop['stack']-max(parent['bets']))/100,
      frozen_targets=[215,220],target_details=summary,
      new_model_CERT=0,
      certified_source_V25=[135,257],
      no_generic_texture_certification=True,
      no_observed_conditional_private_card_NL2_rates=True,
      never_merge=True)
    OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B107 | CO_BB Js9h4d original B2 *individually verified* GTO pin\n\n'+
      'The overall B2 Actions run 44666290556 failed because another SB3_BTN job failed; we use only the independently verified CO_BB GTO in B2_PARTIAL.\n'+
      'Original manifest, full flop and Rust job bytes independently SHA-pinned.\n'+
      'Flop x b33 c, Ts turn x b100 c, IP river check actor has positive legal combo reach.\n'+
      'Two preregistered ranks 215 and 220 need exactly the same third flop hero-IP lock.\n'+
      'Next: reuse the byte-identical real flop, solve only downstream Ts turn and river with partial NL2 IP lock.\n'+
      'Never claim B2 whole workflow passed, original flop was re-solved or exact private-card NL2 rates measured.\n'+
      'PR #2 Draft, never merge.\n')
    print(json.dumps(dict(PASS=True,ranks=[215,220],root_sha=d['original_GTO_flop_SHA256'],
      root_job_sha=d['original_GTO_job_SHA256'],true_IP_nodes=len(actors),
      source_B2_original_run=RUN,counts=[135,257]),ensure_ascii=False))

if __name__=='__main__':main()
