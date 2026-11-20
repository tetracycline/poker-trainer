#!/usr/bin/env python3
"""TASK-HYBRID B123. Promote ONLY preregistered B112 one-board gaps 41
and 69, from SHA-verified original GTO with genuine actor-IP NL2 locks.
No generic board/GTO claims; every CERT example is exact named public cards,
actual full-street action path, preflop 100bb, actor seat, SPR and strict reach.
"""
import copy,gzip,hashlib,json,pathlib
from hu_multiboard_promote import build_source_index,candidates,choose_3_5,hero_seat
from hu_cert_lock_medium_coverage_matrix import create,write_md

D=pathlib.Path('data')
BASE=D/'nl2_hu_multiboard_status_v26_b111_rank215_220.json'
QUEUE=D/'nl2_hu_b112_all_approx_frozen_frequency_gaps.json'
RANK=D/'nl2_hu_multiboard_prerank.json'
STAGE=D/'nl2_hu_stage2_queue.json'
OUT=D/'nl2_hu_multiboard_status_v27_b123_r41_69.json'
MATRIX=D/'nl2_hu_cert_lock_medium_matrix_v27_b123.json'
DOC=pathlib.Path('docs/NL2_HU_B123_V27_R41_69_REAL_CERT.md')
LOCKDOC=pathlib.Path('docs/NL2_HU_B123_V27_ALL_CERT_LOCK_MEDIUM.md')
SOURCES={
 'B121_CO_XX_XB50':D/'solver_evidence/NL2_MULTIBOARD_B121_CO_XX_XB50.json.gz',
 'B115_R69_BTN_B33XX':D/'solver_evidence/NL2_MULTIBOARD_B115_R69_BTN_B33XX.json.gz'
}
TARGETS=[
 dict(rank=41,model_id='ln-ipfr-t_model-sxr0qa',spot='CO_BB',street=1,
      line='x x/x',seat=1,flops={'8s8h3d','As9h2d','Js9h4d'},
      old_locked={'As9h2d','Js9h4d'},new_flop='8s8h3d',
      source='B121_CO_XX_XB50',source_version='exp_ip'),
 dict(rank=69,model_id='ln-ipfr-r_model-159a6z6',spot='BTN_BB',street=2,
      line='b33 c/x x/x',seat=1,flops={'8s8h3d','Jh9d6s','KsQh4d'},
      old_locked={'Jh9d6s','KsQh4d'},new_flop='8s8h3d',
      source='B115_R69_BTN_B33XX',source_version='exp_ip')
]
def read(path):return json.loads(path.read_text())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def validated_source(batch,path):
    ix=read(path.with_suffix('').with_suffix('.index.json'))
    raw=gzip.decompress(path.read_bytes())
    source=json.loads(raw)
    assert ix['batch']==batch and ix['generic_model_certification']==0
    assert ix['gzip_sha256']==digest(path)
    assert ix['source_sha256']==hashlib.sha256(raw).hexdigest()
    assert source['schema']=='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1'
    assert not source['errors'] and source['source_run_id']==ix['run_id']
    assert len(source['artifacts'])==ix['actual_spot_flop_version_jobs']
    assert sum(len(a['cases']) for a in source['artifacts'])==ix['verified_cases']
    assert sum(a['version']=='gto' for a in source['artifacts'])==ix['gto_cases']
    assert sum(a['version']!='gto' for a in source['artifacts'])==ix['locked_cases']
    return ix,source

def strict_hero(source,version,target):
    items=[n for a in source['artifacts'] if a['version']==version
           for c in a['cases'] if c['flop']==target['new_flop']
           for n in c['nodes'] if n['exact_node_line']==target['line']
           and n['acting_seat']==target['seat']
           and n['strictly_reachable_combos']>0]
    assert items, 'No real strictly reachable hero-side source for '+str(target['rank'])
    return items

def main():
    base=read(BASE);frozen=read(QUEUE)
    assert base['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V26_B111_RANK215_220'
    assert (base['CERT_MULTIBOARD'],base['APPROX'],base.get('EST',0),base['TOTAL'])==(137,255,0,392)
    assert base['independently_verified_completed_batches']['B4_MICRO']['status']=='VERIFIED'
    assert base['independently_verified_completed_batches']['B4_MICRO']['run_id']==44732810327
    assert frozen['schema']=='NL2_HU_B112_V26_ALL_APPROX_SOURCE_BLIND_FREQUENCY_AUDIT_V1'
    assert frozen['candidate_count']==255
    assert frozen['one_board_short_ranks']==[41,69,71,88,236,313]
    assert frozen['parent_V26_sha256']==digest(BASE)
    assert frozen['frozen_rank_sha256']==digest(RANK)
    idx={};proof={}
    for batch,path in SOURCES.items():
        assert path.is_file() and path.with_suffix('').with_suffix('.index.json').is_file()
        idx[batch],proof[batch]=validated_source(batch,path)
    b121=idx['B121_CO_XX_XB50']
    assert (b121['run_id'],b121['gto_cases'],b121['locked_cases'])==(44838577146,0,1)
    assert b121['original_gto_parent_run']==44836834970
    assert b121['original_GTO_flop_NOT_recomputed'] is True
    assert b121['exact_actor_IP_turn_nodes']>0 and b121['strict_failure_reason'] is None
    b115=idx['B115_R69_BTN_B33XX']
    assert (b115['run_id'],b115['gto_cases'],b115['locked_cases'])==(44837218223,1,1)
    for t in TARGETS:strict_hero(proof[t['source']],t['source_version'],t)
    ranks=read(RANK)['nodes']
    stage=read(STAGE)['records']
    sourcefiles=[pathlib.Path(s) for s in base['source_evidence']['source_files']]
    assert all(x.is_file() for x in sourcefiles)
    for batch in ('B113_UTG_B75_XB50','B114_R41_CO_XX'):
        arch=D/('solver_evidence/NL2_MULTIBOARD_'+batch+'.json.gz')
        if arch.is_file():
            old,_=validated_source(batch,arch)
            assert old['immediate_CERT_upgrades']==0
            sourcefiles.append(arch)
    sourcefiles+=list(SOURCES.values())
    assert len(sourcefiles)==len(set(sourcefiles))
    authentic_gto,real_locked,meta=build_source_index(D,sourcefiles)
    out=copy.deepcopy(base)
    new_cert=[]
    for t in TARGETS:
        fid=t['model_id']
        fr=next(z for z in frozen['rows'] if z['rank']==t['rank'])
        assert fr['model_id']==fid and fr['missing_real_hero_flops_to_3']==1
        assert set(fr['hero_locked_flops'])==t['old_locked']
        assert t['new_flop'] not in t['old_locked']
        node=next(copy.deepcopy(x) for x in ranks
            if x['rank_by_empirically_grounded_frequency_proxy']==t['rank'])
        model=next(x for x in stage if x['model_id']==fid)
        assert node['model_id']==fid and model['model_id']==fid
        assert (model['solver_profile'],model['street'])==(t['spot'],t['street'])
        assert model['family']=='SRP'
        assert hero_seat(model['preflop_text'])==t['seat']
        node['preflop_text']=model['preflop_text']
        node['abstract_action_history']=model['abstract_action_history']
        choices,reason=candidates(node,authentic_gto,real_locked,None)
        assert reason is None,(t['rank'],reason)
        picked,reason=choose_3_5(choices)
        assert reason is None,(t['rank'],reason)
        assert len(picked)==3 and {z['flop'] for z in picked}==t['flops']
        assert len({z['flop_texture'] for z in picked})>=2
        for z in picked:
            assert z['acting_seat']==t['seat'] and z['actual_exact_action_line']==t['line']
            assert z['strict_full_street_combo_reachable']>0
            assert z['relative_spr_error_pct']<=5 and z['genuine_gto_exploitability_pct']<=.5
            assert not z['assumed_preflop_ranges']
            assert any(q['version']==t['source_version'] for q in z['nl2_locked_variants'])
        newly=next(z for z in picked if z['flop']==t['new_flop'])
        assert any(q['version']==t['source_version'] and q['run_id']==idx[t['source']]['run_id']
                   for q in newly['nl2_locked_variants'])
        assert base['records'][fid]['label']=='APPROX'
        out['records'][fid].update(label='CERT-MULTIBOARD',
            high_frequency_preregistered=True,
            original_top24_high_frequency_preregistered=False,
            source_blind_expansion_rank=t['rank'],
            prereg_cohort='B112_FROZEN_SIX_ONE_BOARD_SHORT',
            certified_3_to_5_exact_flop_boards=picked,
            proven_exact_board_count=3,blocked_reason=None,
            source_credibility='PINNED_ORIGINAL_GTO_PLUS_AUTHENTIC_HERO_IP_NL2_RUST_LOCK')
        new_cert.append(dict(rank=t['rank'],model_id=fid,
            board_flops=sorted(t['flops']),run_id=idx[t['source']]['run_id']))
    changed={k for k in base['records'] if base['records'][k]!=out['records'][k]}
    assert changed=={t['model_id'] for t in TARGETS}
    assert sum(x['label']=='CERT-MULTIBOARD' for x in out['records'].values())==139
    assert sum(x['label']=='APPROX' for x in out['records'].values())==253
    assert all(x['label'] in ('CERT-MULTIBOARD','APPROX') for x in out['records'].values())
    out.update(schema='NL2_HU_392_MULTIBOARD_CERT_STATUS_V27_B123_R41_69',
        CERT_MULTIBOARD=139,APPROX=253,EST=0,
        original_v26_cert=137,original_v26_approx=255,
        source_evidence=meta,source_blind_expansion_ranks=[41,69],
        supplementary_cert_count=115,parent_v26_sha256=digest(BASE),
        B112_frozen_gap_sha256=digest(QUEUE),
        B115_source_index_sha256=digest(SOURCES['B115_R69_BTN_B33XX'].with_suffix('').with_suffix('.index.json')),
        B121_source_index_sha256=digest(SOURCES['B121_CO_XX_XB50'].with_suffix('').with_suffix('.index.json')),
        b123_true_rank_proofs=new_cert,
        original_top24_cutoff_unchanged=True,
        no_generic_texture_GTO=True,no_observed_private_card_NL2_rates=True,
        PR2_remains_draft_never_merge=True)
    for batch,ix in idx.items():
        out['independently_verified_completed_batches'][batch]={
            'status':'VERIFIED','run_id':ix['run_id'],
            'authentic_jobs':ix['actual_spot_flop_version_jobs'],
            'gto_cases':ix['gto_cases'],'locked_cases':ix['locked_cases'],
            'new_subgames':ix['verified_cases'],'gzip_sha256':ix['gzip_sha256'],
            'no_generic_texture_GTO':True}
    matrix=create(out)
    assert (matrix['CERT_MULTIBOARD'],matrix['APPROX'])==(139,253)
    assert len(matrix['models'])==139
    assert len(matrix['boards'])==545 and matrix['strict_aggregate']['named_board_proofs']==545
    assert all(z['hero_lock_proofs'] and z['strictly_reachable_combo_count']>0
               and z['no_general_bet_size_recommendation'] for z in matrix['boards'])
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    matrix.update(schema='NL2_CERT_PER_NAMED_BOARD_LOCK_AND_MEDIUM_PROVENANCE_V27_B123',
        parent_v27_status_sha256=digest(OUT),
        no_general_bet_size_advice=True,
        no_observed_private_card_conditionals=True,
        PR2_remains_draft_never_merge=True)
    MATRIX.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
    DOC.write_text('# B123 V27 genuine 3-board GTO + actor-IP lock promotion\n\n'
        '**139 CERT-MULTIBOARD / 253 APPROX / 0 EST** from unchanged 392 nodes.\n\n'
        'rank 41: CO_BB turn x x/x, exact flops 8s8h3d, As9h2d, Js9h4d. '
        'New source B121 actor-IP Rust turn-only, original GTO flop SHA pinned, run 44838577146.\n\n'
        'rank 69: BTN_BB river b33 c/x x/x, exact flops 8s8h3d, Jh9d6s, KsQh4d. '
        'New source B115 exact GTO + actor-IP Rust run 44837218223.\n\n'
        'No generic GTO inference to other flop textures, no observed '
        'NL2 per-private-card conditional rates. Failed B113 rank236 and '
        'B114 full-tree EXP-IP rank41 paths remain negative evidence. '
        'Batch E VERIFIED (44732810327). Original 2,475/2,475 river routing preserved.\n'
        'Draft PR #2: NEVER MERGE.\n')
    LOCKDOC.write_text('# B123 V27 per-board node-lock/50pct research flags\n\n'+write_md(matrix))
    print(json.dumps({'PASS':True,'CERT':139,'APPROX':253,'EST':0,
        'ranks':[41,69],'named_boards':len(matrix['boards']),
        'node_lock_variants':matrix['strict_aggregate']['hero_lock_variants'],
        'b50_candidate_boards':matrix['strict_aggregate']['b50_research_candidate_boards'],
        'source_runs':[44838577146,44837218223]}))

if __name__=='__main__':
    main()
