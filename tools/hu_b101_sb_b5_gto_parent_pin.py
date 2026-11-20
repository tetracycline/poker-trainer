#!/usr/bin/env python3
"""B101: freeze byte-exact B5 SB_BB As7h3d GTO parent from prior verified
cancelled-run salvage. Rank43 needs one OOP river local lock, not new GTO.
No false claim of measured hole-card NL2 conditions or auto-CERT.
"""
import argparse,gzip,hashlib,json,pathlib
R=pathlib.Path("data")
INDEX=R/"solver_evidence/NL2_MULTIBOARD_B5_SBGAPS.index.json"
ARCH=R/"solver_evidence/NL2_MULTIBOARD_B5_SBGAPS.json.gz"
B54=R/"nl2_hu_b54_next14_sourceblind_gaps.json"
V23=R/"nl2_hu_multiboard_status_v23_b100_lmp_pair.json"
OUT=R/"nl2_hu_b101_sb_as7h3d_b5_gto_parent_pin.json"
DOC=pathlib.Path("docs/NL2_HU_B101_SB_AS7H3D_GTO_PARENT_PIN.md")
RUN=44736420272
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bufsha(b):return hashlib.sha256(b).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--artifact-root",required=True,type=pathlib.Path)
    args=parser.parse_args()
    i=json.loads(INDEX.read_text())
    raw=gzip.decompress(ARCH.read_bytes())
    verified=json.loads(raw)
    assert i['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
    assert i['batch']=='B5_SBGAPS' and i['run_id']==RUN
    assert i['verified_cases']>=50 and i['gto_cases']>=30
    assert i['excluded_unverified_job']=='SB_BB As7h3d exp_oop cancelled after 21-minute solve timeout'
    assert i['gzip_sha256']==sha(ARCH) and i['source_sha256']==bufsha(raw)
    assert verified['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert verified['source_run_id']==RUN and not verified['errors']
    gtos=[a for a in verified['artifacts'] if (a['spot'],a['version'],a['flop'])==('SB_BB','gto','As7h3d')]
    assert len(gtos)==1 and gtos[0]['cases'] and not gtos[0]['errors']
    case=[c for c in gtos[0]['cases'] if c['flop_line']=='b50 c' and c['turn']=='Kd']
    assert len(case)==1
    river=[n for n in case[0]['nodes'] if n['acting_seat']==0 and
           n['exact_node_line']=='b50 c/x x/' and n['strictly_reachable_combos']>0]
    assert river, 'Genuine GTO parent has no OOP river decision in requested line'
    root=args.artifact_root
    manifest=root/'evidence/SB_BB-gto-As7h3d.json'
    assert manifest.is_file()
    m=json.loads(manifest.read_text())
    assert m['schema']=='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1'
    assert (m['spot'],m['version'],m['flop'])==('SB_BB','gto','As7h3d')
    assert (m['root_pot_bb'],m['root_remaining_bb'])==(6.,97.)
    assert m['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
    assert not m['failures'] and m['no_generic_certification']
    source=root/'solver/postflop'/m['file_flop']
    job=source.with_suffix('.job.json')
    assert source.is_file() and job.is_file()
    assert sha(source)==m['file_flop_sha256']
    fr=json.loads(source.read_text());cfg=json.loads(job.read_text())
    assert (fr['flop'],fr['pot'],fr['stack'])==('As7h3d',600,9700)
    assert (cfg['pot'],cfg['stack'])==(600,9700)
    assert cfg.get('hero') is None and not cfg.get('locks')
    assert cfg['rake_rate']==.05 and cfg['rake_cap']==1000
    assert all(x in cfg.get('flop_oop','') for x in ('33%','50%','75%','100%'))
    assert all(x in cfg.get('flop_ip','') for x in ('33%','50%','75%','100%'))
    parent=[n for n in fr['nodes'] if n['line']=='b50 c/' and n['board'][-2:]=='Kd']
    assert len(parent)==1 and all(any(float(z)>1e-4 for z in ws) for ws in parent[0]['wr'])
    locked=json.loads(B54.read_text())
    row=next(x for x in locked['rows'] if x['rank']==43)
    assert row['model_id']=='ln-opfr-r_model-1e6gydx'
    assert row['missing_to_three_flops']==1
    assert row['matched_hero_side_NL2_lock_flops']==['As9h2d','Ks7h2d']
    assert row['model_spr']==7.833
    v23=json.loads(V23.read_text())
    assert (v23['CERT_MULTIBOARD'],v23['APPROX'])==(133,259)
    assert v23['records'][row['model_id']]['label']=='APPROX'
    res=dict(schema='NL2_HU_B101_SB_B5_AS7H3D_PINNED_PARENT_V1',
       status='PASS_SHA_PINNED_GTO_PARENT',
       original_B5_verified_run_id=RUN,original_B5_source_archive_sha256=sha(ARCH),
       original_GTO_manifest_sha256=sha(manifest),
       original_GTO_flop_sha256=sha(source),
       original_GTO_Rust_job_sha256=sha(job),
       original_GTO_file_relative_path=m['file_flop'],
       preflop_ranges_pinned_CFR_not_per_private_combo_observation=True,
       exact_root_pot_bb=6.,exact_root_stack_bb=97.,
       immutable_flop='As7h3d',immutable_turn='Kd',
       flop_line='b50 c',turn_line='x x',
       required_OOP_river_line='b50 c/x x/',
       GTO_positive_reach_OOP_river_nodes=len(river),
       parent_pot_bb=parent[0]['pot']/100,
       parent_effective_remaining_bb=(fr['stack']-max(parent[0]['bets']))/100,
       expected_model_rank=43,expected_model_id=row['model_id'],
       existing_exact_pair_flops=['As9h2d','Ks7h2d'],
       missing_third_flop='As7h3d',
       original_B5_EXP_OOP_cancelled_and_not_accepted=True,
       no_generic_texture_certification=True,
       no_new_CERT_until_Rust_and_actor_verification=True,
       current_CERT=133,current_APPROX=259,
       never_merge_PR2=True)
    OUT.write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B101 | SB_BB As7h3d B5 pinned actual GTO\n\n'+
       'Verified original GTO run 44736420272 and its original root/job/manifest SHA-256 pinned.\n'+
       'Previous EXP_OOP original job cancelled: it is not an authenticated lock.\n'+
       'GTO flop b50 c, turn Kd, turn x x, with positive OOP river actor source reach.\n'+
       'Rank43 already has As9h2d and Ks7h2d genuine GTO+NL2-OOP lock.\n'+
       'Next: solve only authentic turn/river NL2 OOP partial lock from this unchanged full GTO flop.\n'+
       'No generic texture advice or true conditional hole-card measurements. PR #2 Draft, never merge.\n')
    print(json.dumps(dict(PASS=True,rank=43,root_SHA=sha(source),root_job_SHA=sha(job),
        real_OOP_river_nodes=len(river),already_paired_flops=2,
        no_new_cert=True,CERT=133,APPROX=259),ensure_ascii=False))

if __name__=='__main__':main()
