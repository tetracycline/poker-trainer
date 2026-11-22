#!/usr/bin/env python3
"""B350: source-audited existing ORIGINAL 100bb UTG_CO full-menu Rust GTO,
then rank79 CO-IP b50 c/x turn-action 40/70 and SPR7. Frozen source order.
Never treat original GTO alone as an NL2 partially locked pair or CERT.
"""
import gzip,hashlib,json,pathlib
from hu_multiboard_promote import texture
D=pathlib.Path('data')
ROWS=[
 ('B233','4s4h2d',44894288118,'8s'),
 ('B234','7s5h3d',44894366667,'6c'),
 ('B235','KsQh4d',44894369547,'Tc'),
 ('B239','As9h2d',44895163541,'Kd'),
 ('B240','Js9h4d',44895186652,'Ts'),
 ('B241','As7h3d',44895340440,'Kd'),
 ('B243','QsJh4d',44900567417,'7s'),
 ('B245','KsJh4d',44900844857,'2h'),
]
MID='ln-ipc-t_model-1cla93g'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    v45=D/'nl2_hu_multiboard_status_v45_b345_rank71.json'
    s=json.loads(v45.read_text())
    assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(157,235,0,392)
    model=s['records'][MID]
    assert model['label']=='APPROX' and model['frequency_rank']==79
    assert model['solver_profile']=='UTG_CO' and model['street']==1
    assert model['assumed_model_node_spr']==7
    out=[]
    for batch,flop,run,turn in ROWS:
        nam=f'NL2_MULTIBOARD_{batch}_R30_{flop.upper()}_GTO'
        idx=D/f'solver_evidence/{nam}.index.json'
        gz=D/f'solver_evidence/{nam}.json.gz'
        x=json.loads(idx.read_text())
        raw=gzip.decompress(gz.read_bytes());data=json.loads(raw)
        assert x['run_id']==data['source_run_id']==run
        assert x['schema']=='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1'
        assert x['gto_cases']==x['verified_cases']==1 and x['locked_cases']==0
        assert x['gzip_sha256']==sha(gz) and x['source_sha256']==hashlib.sha256(raw).hexdigest()
        assert x['turn']==turn and x['original_parent_GTO_root_SHA256'] and x['original_parent_GTO_job_SHA256']
        assert not data['errors'] and len(data['artifacts'])==1
        art=data['artifacts'][0]
        assert (art['spot'],art['flop'],art['version'])==('UTG_CO',flop,'gto')
        assert not art['errors']
        matching=[c for c in art['cases'] if c['flop_line']=='b50 c' and c['turn']==turn]
        assert len(matching)==1
        c=matching[0]
        assert c['run_id']==run and c['gto_exploitability_pct']<=0.5
        assert (c['flop_root_pot_bb'],c['flop_root_stack_bb'])==(6.5,97.5)
        assert c['empirical_scope']=='PINNED_PREFLOP_CFR'
        assert len(c['source_sha256'])==64 and len(c['flop_source_sha256'])==64
        # Case source parser has ALL actor-correct node GTO strategies, not only target rank30.
        # CO is IP after calling original UTG flop b50. UTG check => CO to act.
        exact=[n for n in c['nodes'] if n['acting_seat']==1 and
             n['exact_node_line']=='b50 c/x' and len(n['public_board'])==8]
        legal=[n for n in exact if n['strictly_reachable_combos']>0 and abs(n['node_spr']-7)/7<=.05]
        out.append(dict(batch=batch,flop=flop,turn=turn,run_id=run,texture=texture(flop),
           original_source_index_sha256=sha(idx),original_source_archive_sha256=sha(gz),
           original_GTO_case_sha256=c['source_sha256'],
           original_flop_root_sha256=x['original_parent_GTO_root_SHA256'],
           original_flop_job_sha256=x['original_parent_GTO_job_SHA256'],
           original_gto_gap_pct=c['gto_exploitability_pct'],
           rank79_CO_IP_turn_actor_node_count=len(exact),
           rank79_CO_IP_turn_strict_SPR_40_70_combos=sum(n['strictly_reachable_combos'] for n in legal),
           rank79_CO_IP_turn_reachable_real_original_GTO=bool(legal),
           NO_real_rank79_NL2_actor_turn_lock_in_this_GTO_archive=True,
           current_rank79_remains_APPROX=True))
    assert len(out)==8
    positives=[x for x in out if x['rank79_CO_IP_turn_reachable_real_original_GTO']]
    distinct=sorted({x['texture'] for x in positives})
    result=dict(schema='NL2_HU_B350_R79_EIGHT_ORIGINAL_UTG_CO_FULL_ROOT_40_70_IP_TURN_SOURCE_SCAN_V1',
       V45_status_sha256=sha(v45),original_index_sha256s=[x['original_source_index_sha256'] for x in out],
       rank=79,model_id=MID,spot='UTG_CO',actor='CO_IP',exact_line='b50 c/x',model_spr=7.0,
       existing_B2_true_original_gto_plus_nl2_actor_paired_flop='Ks7h2d',
       original_gto_source_rows=out,
       source_proven_legal_original_gto_candidate_flops=[x['flop'] for x in positives],
       source_proven_legal_texture_classes=distinct,
       two_fresh_independent_real_NL2_CO_IP_partial_locks_STILL_NEEDED=True,
       original_full_flop_GTO_not_identical_to_exp_or_NL2_lock=True,
       no_observed_per_private_hand_conditional_villain_pool_rates=True,
       CURRENT_CERT=157,CURRENT_APPROX=235,CURRENT_EST=0,CURRENT_TOTAL=392,
       PR2_Draft_NEVER_MERGE=True)
    p=D/'nl2_hu_b350_rank79_8_original_utgco_gto_turn_legality.json'
    p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('PASS B350 8 original SHA verified GTO source roots; rank79 CO-IP strict turn eligible:',
          [(x['flop'],x['rank79_CO_IP_turn_strict_SPR_40_70_combos']) for x in out])
if __name__=='__main__':main()
