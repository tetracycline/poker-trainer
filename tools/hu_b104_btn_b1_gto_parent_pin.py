#!/usr/bin/env python3
"""B104: pin independently verified original B1 BTN_BB As9h2d *full GTO*
flop to prepare one high-frequency rank135 exact hero-IP river-lock gap.

Never reuse an opponent-side EXP as hero-IP or label approximate texture GTO.
Original preflop weights are pinned CFR, NOT observed NL2 private-card actions.
"""
import argparse,gzip,hashlib,json,pathlib
R=pathlib.Path('data')
B1=R/'solver_evidence/NL2_MULTIBOARD_B1.json.gz'
IX=R/'solver_evidence/NL2_MULTIBOARD_B1.index.json'
B70=R/'nl2_hu_b70_next20_sourceblind_gaps.json'
V24=R/'nl2_hu_multiboard_status_v24_b103_rank43.json'
OUT=R/'nl2_hu_b104_btn_as9h2d_gto_parent_pin.json'
DOC=pathlib.Path('docs/NL2_HU_B104_BTN_B1_AS9H2D_GTO_PARENT_PIN.md')
RUN=44666285424
MODEL='ln-ipfr-r_model-3lq5u6'
FLOP='As9h2d';TURN='Kd';FLOPLINE='x b100 c';TURNLINE='x x'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--artifact-root',required=True,type=pathlib.Path)
    a=parser.parse_args()
    idx=json.loads(IX.read_text())
    raw=gzip.decompress(B1.read_bytes());b1=json.loads(raw)
    assert idx['batch']=='B1' and idx['run_id']==RUN and idx['verified_cases']>=100
    assert idx['actual_spot_flop_version_jobs']==18
    assert idx['source_sha256']==digest(raw) and idx['gzip_sha256']==sha(B1)
    assert b1['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert b1['source_run_id']==RUN and not b1['errors']
    originals=[x for x in b1['artifacts'] if
        (x['spot'],x['version'],x['flop'])==('BTN_BB','gto',FLOP)]
    assert len(originals)==1 and not originals[0]['errors']
    cases=[x for x in originals[0]['cases'] if
           (x['flop_line'],x['turn'])==(FLOPLINE,TURN)]
    assert len(cases)==1
    hero=[x for x in cases[0]['nodes'] if x['acting_seat']==1 and
          x['exact_node_line']=='x b100 c/x x/x' and x['strictly_reachable_combos']>0]
    assert hero, 'No true GTO IP river actor on predeclared decision line'
    root=a.artifact_root
    manifest=root/'evidence/BTN_BB-gto-As9h2d.json'
    assert manifest.is_file()
    meta=json.loads(manifest.read_text())
    assert meta['schema']=='NL2_MULTIBOARD_AUTHENTIC_SOURCE_V1'
    assert (meta['spot'],meta['version'],meta['flop'])==('BTN_BB','gto',FLOP)
    assert (meta['root_pot_bb'],meta['root_remaining_bb'])==(5.5,97.5)
    assert meta['preflop_ranges']['source']=='PINNED_POKER_SOLVER_PREFLOP_CFR'
    assert not meta['failures'] and meta['no_generic_certification'] is True
    file=root/'solver/postflop'/meta['file_flop'];jobfile=file.with_suffix('.job.json')
    assert file.is_file() and jobfile.is_file()
    assert meta['file_flop_sha256']==sha(file)
    fr=json.loads(file.read_text());job=json.loads(jobfile.read_text())
    assert (fr['flop'],fr['pot'],fr['stack'])==(FLOP,550,9750)
    assert (job['pot'],job['stack'])==(550,9750)
    assert job.get('hero') is None and not job.get('locks')
    assert job['rake_rate']==.05 and job['rake_cap']==1000
    assert all(x in job.get('flop_oop','') for x in ['33%','50%','75%','100%'])
    assert all(x in job.get('flop_ip','') for x in ['33%','50%','75%','100%'])
    parent=[n for n in fr['nodes'] if n['line']==FLOPLINE+'/' and n['board'][-2:]==TURN]
    assert len(parent)==1 and all(any(float(x)>1e-4 for x in w) for w in parent[0]['wr'])
    b70=json.loads(B70.read_text())
    assert b70['source_blind_preselection_ranks']==list(range(116,136))
    assert b70['fixed_rank_sha256']==sha(R/'nl2_hu_multiboard_prerank.json')
    rank=next(x for x in b70['rows'] if x['rank']==135)
    assert rank['model_id']==MODEL and rank['spot']=='BTN_BB' and rank['street']==2
    assert rank['missing_to_three_flops']==1
    assert rank['matched_hero_side_NL2_lock_flops']==['Jh9d6s','KsQh4d']
    assert 'As9h2d' in rank['matching_true_GTO_flops']
    assert rank['source_samples'][0]['GTO_run']==RUN
    v24=json.loads(V24.read_text())
    assert (v24['CERT_MULTIBOARD'],v24['APPROX'])==(134,258)
    assert v24['records'][MODEL]['label']=='APPROX'
    data=dict(schema='NL2_HU_B104_B1_BTN_AS9H2D_GTO_SHA_PARENT_V1',
        result='PASS_FULL_ORIGINAL_GTO_PIN',
        original_source_run_id=RUN,source_archive_sha256=sha(B1),
        original_GTO_manifest_sha256=sha(manifest),
        original_GTO_flop_root_sha256=sha(file),
        original_GTO_Rust_job_sha256=sha(jobfile),
        original_GTO_file_relative_path=meta['file_flop'],
        root_pot_bb=5.5,root_stack_bb=97.5,
        source_preflop_CFR_pinned_not_holecard_observed=True,
        original_root_full_flop_size_menu=True,
        preselected_rank=135,preselected_model_id=MODEL,
        target_public_flop=FLOP,target_turn=TURN,
        flop_line=FLOPLINE,turn_line=TURNLINE,
        required_IP_river_line='x b100 c/x x/x',
        original_source_GTO_IP_hero_river_nodes=len(hero),
        positive_strict_combo_counts=[z['strictly_reachable_combos'] for z in hero[:6]],
        original_parent_pot_bb=parent[0]['pot']/100,
        original_parent_remaining_stack_bb=(fr['stack']-max(parent[0]['bets']))/100,
        existing_hero_locked_flops=['Jh9d6s','KsQh4d'],
        missing_one_flop='As9h2d',
        new_cert=0,current_CERT=134,current_APPROX=258,
        no_generic_texture_GTO=True,
        no_empirically_observed_NL2_private_combo_frequencies=True,
        never_merge=True)
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B104 | Rank135 original B1 BTN_BB full GTO root SHA pin\n\n'+
       'Original run 44666285424, 100bb B1 As9h2d x-b100-call flop, Kd turn x-x, x river IP actor.\n'+
       'Original unmodified GTO full flop and job SHA pinned; no synthetic EXP source.\n'+
       'Rank135 already has two real hero-IP locked boards Jh9d6s and KsQh4d.\n'+
       'Next B105 may solve only downstream Kd turn x-x / river with NL2 partial IP lock.\n'+
       'Observed NL2 pool aggregate rate is NOT exact private-card behavior.\n'+
       'No CERT relabel until all real Rust and source gates pass. PR #2 remains Draft; never merge.\n')
    print(json.dumps(dict(PASS=True,rank=135,original_run=RUN,
       parent_root_sha=data['original_GTO_flop_root_sha256'],
       source_hero_river_nodes=len(hero),counts=[134,258]),ensure_ascii=False))

if __name__=='__main__':main()
