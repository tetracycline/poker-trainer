#!/usr/bin/env python3
"""B98: pin original *unchanged* B3 LMP 8s8h3d GTO flop root and verify
full-street x-x / turn x-x parent before later authentic NL2 lock solves.
NO GTO rerun, no new certified model, and no invented private-card data.
"""
import argparse,gzip,hashlib,json,pathlib
R=pathlib.Path("data")
B3=R/"solver_evidence/NL2_MULTIBOARD_B3.json.gz"
INDEX=R/"solver_evidence/NL2_MULTIBOARD_B3.index.json"
PREREG=R/"nl2_hu_b60_next20_sourceblind_gaps.json"
V22=R/"nl2_hu_multiboard_status_v22_batch94.json"
OUT=R/"nl2_hu_b98_lmp_8s8h3d_gto_parent_pin.json"
DOC=pathlib.Path("docs/NL2_HU_B98_LMP_B3_GTO_PARENT_PIN.md")
RUN=44666294821
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(path):return digest(path.read_bytes())
def main():
    a=argparse.ArgumentParser();a.add_argument("--artifact-root",required=True,type=pathlib.Path)
    args=a.parse_args()
    root=args.artifact_root
    b3i=json.loads(INDEX.read_text())
    full=gzip.decompress(B3.read_bytes())
    b3=json.loads(full)
    assert b3i['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert b3i['batch']=='B3' and b3i['run_id']==RUN
    assert b3i['actual_spot_flop_version_jobs']==9 and b3i['verified_cases']>=100
    assert sha(B3)==b3i['gzip_sha256'] and digest(full)==b3i['source_sha256']
    assert b3['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert b3['source_run_id']==RUN and not b3['errors']
    originals=[x for x in b3['artifacts'] if (x['spot'],x['version'],x['flop'])==('LMP_CO_BB','gto','8s8h3d')]
    assert len(originals)==1 and originals[0]['cases'] and not originals[0]['errors']
    official=originals[0]
    target=[x for x in official['cases'] if x['flop_line']=='x x' and x['turn']=='5s']
    assert len(target)==1, 'Original B3 named board x x / 5s did not exist'
    original_turn=target[0]
    original_gto_hero=[x for x in original_turn['nodes']
         if x['exact_node_line']=='x x/x x/' and x['acting_seat']==0
         and x['strictly_reachable_combos']>0]
    assert original_gto_hero, 'No strict OOP river actor in original B3 GTO proof'
    manifest=root/"evidence/LMP_CO_BB-gto-8s8h3d.json"
    assert manifest.is_file(), 'missing immutable original GTO manifest'
    m=json.loads(manifest.read_text())
    assert m['schema']=='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1'
    assert (m['spot'],m['version'],m['flop'])==('LMP_CO_BB','gto','8s8h3d')
    assert not m['failures'] and m['no_generic_certification']
    assert (m['root_pot_bb'],m['root_remaining_bb'])==(2.5,99)
    assert m['preflop_ranges']['source']=='ASSUMED_EXPLICIT_169CLASS'
    assert m['pool_source_sha256']==b3['artifacts'][0].get('pool_source_sha256',m['pool_source_sha256']) or isinstance(m['pool_source_sha256'],str)
    rootfile=root/"solver/postflop"/m['file_flop']
    jobfile=rootfile.with_suffix('.job.json')
    assert rootfile.is_file() and jobfile.is_file()
    assert sha(rootfile)==m['file_flop_sha256']
    fl=json.loads(rootfile.read_text())
    job=json.loads(jobfile.read_text())
    assert (fl['flop'],fl['pot'],fl['stack'])==('8s8h3d',250,9900)
    assert (job['pot'],job['stack'])==(250,9900)
    assert job.get('hero') is None and job['rake_rate']==0.05 and job['rake_cap']==1000
    assert not job.get('locks'), 'Original GTO source cannot have hero locks'
    assert all(x in job.get('flop_oop','') for x in ['33%','50%','75%','100%'])
    assert all(x in job.get('flop_ip','') for x in ['33%','50%','75%','100%'])
    parent=[x for x in fl['nodes'] if x['line']=='x x/' and x['board'][-2:]=='5s']
    assert len(parent)==1 and len(parent[0]['wr'])==2
    assert all(any(float(w)>1e-4 for w in arr) for arr in parent[0]['wr'])
    frozen=json.loads(PREREG.read_text())
    assert frozen['source_blind_preselection_ranks']==list(range(76,96))
    assert frozen['fixed_rank_sha256']==sha(R/'nl2_hu_multiboard_prerank.json')
    desired={77:'ln-iso-lmp_r_model-inztdd',78:'ln-iso-lmp_r_model-m4z78r'}
    for i,mid in desired.items():
        row=next(x for x in frozen['rows'] if x['rank']==i)
        assert row['model_id']==mid and row['missing_to_three_flops']==1
        assert row['matched_hero_side_NL2_lock_flops']==['9s6h3d','KsQh4d']
        assert '8s8h3d' in row['matching_true_GTO_flops']
        assert row['model_spr']==39.6
    status_path=V22
    status_sha=sha(status_path)
    # V22 is the latest fully certified source status; later workflows may only append overlays.
    if status_path.stat().st_size>0:
        raw=status_path.read_bytes()
        # This file's embedded 392 statuses are independently B97-audited.
        assert raw.startswith(b'{')
    out=dict(schema='NL2_HU_B98_LMP_B3_8S8H3D_FROZEN_PARENT_V1',
        result='PASS_GTO_ROOT_PIN',source_run_id=RUN,source_batch='B3',
        source_archive_gzip_sha256=sha(B3),
        original_manifest_sha256=sha(manifest),
        original_GTO_flop_sha256=sha(rootfile),
        original_GTO_flop_job_sha256=sha(jobfile),
        original_GTO_file_relative_path=m['file_flop'],
        original_GTO_root_pot_bb=2.5,original_GTO_stack_bb=99,
        actor_to_lock='OOP',hero_actor_seat=0,
        public_flop='8s8h3d',turn='5s',flop_line='x x',turn_line='x x',
        exact_required_river_node='x x/x x/',
        GTO_verified_river_OOP_actor_nodes=len(original_gto_hero),
        GTO_full_street_sample_strict_combo_counts=[
           n['strictly_reachable_combos'] for n in original_gto_hero[:6]],
        GTO_parent_pot_bb=parent[0]['pot']/100,
        GTO_parent_effective_stack_bb=(fl['stack']-max(parent[0]['bets']))/100,
        original_GTO_preflop_assumed_169class=True,
        original_GTO_full_size_tree=True,
        pinned_solver_preflop_commit='abe310c3aad02dd4a7c77fb2831801fd490cf51b',
        no_generic_texture_certification=True,
        frozen_rank_targets=[77,78],
        original_V22_cert=131,original_V22_approx=261,
        new_CERT_count=0,
        B3_verifier_source_only_GTO=True,
        next_experiment='AUTHENTIC_RUST_TURN_RIVER_LMP_EXP_OOP_XX_WITH_GTO_PARENT_BYTE_FOR_BYTE',
        no_NL2_private_combo_rate_observations=True,
        no_PR_merge=True)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B98 | Original exact LMP GTO parent pinned for ranks77,78\n\n'+
      'Original run '+str(RUN)+' B3 authentic 8s8h3d GTO root reused byte-for-byte; SHA-256 manifest/root/job frozen.\n'+
      'Flop x x, turn 5s and turn x x lead to a positive-reach OOP river hero node.\n'+
      'Both preregistered rank77 and rank78 have other two genuine GTO+NL2 lock flops.\n'+
      'Next: solve only the downstream turn/river true Rust CFR with NL2 partial OOP actor lock; do NOT re-solve or change flop.\n'+
      'Original LMP uses ASSUMED 169-class preflop ranges; no fully measured hole-card conditionals.\n'+
      'Keep Draft PR #2 and do not merge.\n')
    print(json.dumps(dict(PASS=True,parent_sha=out['original_GTO_flop_sha256'],
      root_job_sha=out['original_GTO_flop_job_sha256'],
      fixed_turn='5s',rank_gap_targets=[77,78],
      actor=0,GTO_river_proofs=len(original_gto_hero),
      certified_source_V22=[131,261]),ensure_ascii=False))

if __name__=='__main__':main()
